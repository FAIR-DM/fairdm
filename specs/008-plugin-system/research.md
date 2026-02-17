# Research: Plugin System for Model Extensibility

**Feature**: 008-plugin-system  
**Date**: 2026-02-17

---

## 1. Plugin as Django View Mixin

### Decision
`Plugin` is a **mixin class** (not a standalone base view) that is always paired with a Django CBV such as `TemplateView`, `UpdateView`, `ListView`, `DeleteView`, `FormView`, or `InlineFormSetView`.

### Rationale
- Django's CBV ecosystem is mature and well-understood; reimplementing view dispatch, form handling, etc. inside a monolithic Plugin base class would duplicate Django.
- Mixin composition gives developers full access to Django's view API while the Plugin mixin adds only plugin-specific behavior (tab configuration, template resolution, context enrichment, permission gating).
- The existing codebase already uses this pattern (`FairDMPlugin` mixin + Django view), proving it works in practice. The redesign retains the pattern but simplifies the mixin API.
- Users can compose with *any* Django CBV (including contrib views and third-party views like `InlineFormSetView` from django-extra-views).

### Alternatives Considered
1. **Plugin as standalone View subclass** — Rejected because it forces a single inheritance path and prevents easy composition with Django's view hierarchy.
2. **Plugin as function-based view wrapper** — Rejected because FairDM is heavily CBV-oriented and FBVs don't support the mixin/inheritance customization patterns the spec requires.

---

## 2. URL Generation Strategy — `get_urls()` Classmethod

### Decision
Each `Plugin` class implements a `get_urls()` classmethod that returns a list of `django.urls.URLPattern` objects. `PluginGroup.get_urls()` iterates its constituent plugins and wraps their URLs under a common prefix. The registry collects all patterns per model via `get_urls_for_model(model)`.

### Rationale
- User explicitly suggested this pattern: "implementing a `get_urls` classmethod on the base Plugin class" and "PluginGroup's `get_urls` loops over constituent plugin classes."
- This mirrors Django's `ModelAdmin.get_urls()` pattern, which is well-known to Django developers.
- Decentralized URL generation lets each plugin own its routing, making plugins self-contained and distributable.
- The registry serves as an aggregator — it collects URL patterns from all registered plugins for a given model and returns them as a single includable list.

### Alternatives Considered
1. **Centralized URL generation in the registry** — Rejected because it couples URL knowledge to the registry rather than the plugin, reducing encapsulation.
2. **URL generation in a per-model orchestrator view (current `PluggableView`)** — Rejected per user guidance: "do not rely too heavily on existing implementation." The orchestrator pattern mixes concerns (URL generation + view dispatch + menu management).

---

## 3. Removing the Orchestrator View (`PluggableView`)

### Decision
Eliminate the dynamically-created per-model `PluggableView` class. Each plugin IS its own view and generates its own URL patterns. The registry replaces the orchestrator's responsibilities (plugin tracking, URL aggregation, tab collection).

### Rationale
- The current `PluggableView` is complex: it dynamically creates a subclass per model, acts as both a view dispatch point and URL generator, and mixes in `FairDMBaseMixin` + `RelatedObjectMixin` — making it hard to test, debug, and extend.
- With `get_urls()` on each plugin, there's no need for a central view class to generate URLs.
- Tab/menu data can be collected by the registry (or a template tag) rather than stored on a view class.
- The user's guidance to "come up with the best API possible rather than trying to fit in with existing code" supports this simplification.

### What Replaces It
| Current `PluggableView` Responsibility | New Owner |
|----------------------------------------|-----------|
| Store list of registered plugins per model | `PluginRegistry._registry` |
| Generate URL patterns | `Plugin.get_urls()` / `PluginGroup.get_urls()` |
| Build flex_menu Menu instances | `PluginRegistry.get_tabs_for_model()` + template tag |
| Template resolution | `Plugin.get_template_names()` (on the mixin) |
| Provide model instance via `RelatedObjectMixin` | `PluginMixin` incorporates object fetching |
| Dynamic view class creation | Not needed — registry maps model → plugin list |

---

## 4. Menu / Tab System

### Decision
Replace the three-category `flex_menu.Menu` system with a flat list of `Tab` dataclasses. Plugins with a `menu` dict attribute appear as tabs. Tab ordering is controlled by `menu["order"]`. Plugins with `menu = None` are accessible only by direct URL.

### Rationale
- Spec clarification explicitly removed categories: "No categories — any plugin registered with a Menu simply appears as a tab in the tab list."
- The `flex_menu` library adds unnecessary indirection for what is a simple ordered tab list.
- A single `menu` dict is cleaner than separate attributes and doesn't pollute the class namespace.
- `menu = None` (or any falsey value) makes it explicit when a plugin has no tab.
- User stated: "we should have a single attr called menu which required a dict... we don't pollute class namespace and we can set menu = Falsey to disable creating a tab."
- A `Tab` dataclass (label, icon, url, order, is_active) is sufficient for template rendering.
- The registry (or a template tag) collects tabs from all plugins for a model, sorts by `menu["order"]`, and passes them to the template.

### Tab Data Flow
```
Plugin.menu dict attribute
  → PluginRegistry collects all menu-having plugins for model
  → Builds list[Tab] sorted by menu["order"]
  → Template tag {% get_plugin_tabs %} or context processor passes to template
  → Bootstrap 5 nav-tabs renders tabs
```

### Alternatives Considered
1. **Keep flex_menu** — Rejected because it introduces an external dependency for a simple flat list and its three-menu structure conflicts with the no-categories decision.
2. **Django template inclusion tags per plugin** — Rejected because it scatters tab rendering logic across plugins instead of centralizing it.
3. **Inner Menu class** — Rejected in favor of simpler single dict attribute.
4. **Separate menu_label, menu_icon, menu_order attributes** — Rejected because it pollutes class namespace; single `menu` dict is cleaner.

---

## 5. Template Resolution Hierarchy

### Decision
`Plugin.get_template_names()` returns a list of template paths in this resolution order:

1. `{app_label}/{model_name}/plugins/{plugin_name}.html` — Most specific (model-specific override)
2. `{base_model_name}/plugins/{plugin_name}.html` — Polymorphic parent fallback
3. `plugins/{plugin_name}.html` — Generic plugin template
4. Plugin class's `template_name` attribute if explicitly set
5. `plugins/base.html` — Framework-provided fallback

### Rationale
- Mirrors the current resolution logic in `PluggableView.get_template_names()` but moves it to the plugin class where it belongs.
- Supports polymorphic models: a `RockSample` plugin can fall back to `Sample`'s template.
- The explicit `template_name` attribute allows developers to skip the hierarchy entirely if desired (standard Django pattern).
- The framework fallback (`plugins/base.html`) ensures plugins always render something, even without custom templates (FR-030).

### Alternatives Considered
1. **Configuration-only template paths** — Rejected because it loses the automatic resolution that reduces developer effort.
2. **Template resolution via registry** — Rejected because it separates rendering concerns from the view class, which is unintuitive in Django.

---

## 6. Model Instance Access

### Decision
The `Plugin` mixin provides a `get_object()` method that fetches the model instance from the URL kwargs (using UUID). The instance is available as `self.object` in the view and `{{ object }}` in templates. Related hierarchy objects (parent project, dataset) are available via standard model relationships.

### Rationale
- Django's `SingleObjectMixin` already provides `get_object()`. For plugins that extend `DetailView`-style views, this is automatic.
- For plugins that extend `TemplateView` (no built-in `get_object()`), the `Plugin` mixin injects the object fetching behavior.
- The current `RelatedObjectMixin.base_object` pattern is renamed to `object` for consistency with Django conventions.

### Implementation Detail
```python
class Plugin:
    model = None  # Set by registry during registration
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_object(self):
        if not hasattr(self, '_object'):
            self._object = get_object_or_404(
                self.model, **{self.slug_field: self.kwargs[self.slug_url_kwarg]}
            )
        return self._object
    
    @property
    def object(self):
        return self.get_object()
```

---

## 7. Permission Checking Strategy

### Decision
Two-tier permission checking: model-level (Django `auth`) AND object-level (django-guardian). Permissions are checked in `Plugin.dispatch()` before the view processes the request. Failed checks return 403 for direct URL access and hide the tab for tab rendering.

### Rationale
- Spec clarification (Q6): "Both model-level and object-level permissions."
- Checking in `dispatch()` is the standard Django pattern (per `PermissionRequiredMixin`).
- Tab visibility filtering happens separately in `PluginRegistry.get_tabs_for_model()` — it calls `plugin.has_permission(request, obj)` for each plugin and excludes those that fail.

### Implementation
```python
class Plugin:
    permission = None  # e.g., "myapp.change_sample"
    
    def has_permission(self, request, obj=None):
        if self.permission is None:
            return True
        # Model-level check
        if not request.user.has_perm(self.permission):
            return False
        # Object-level check (django-guardian)
        if obj is not None and not request.user.has_perm(self.permission, obj):
            return False
        return True
    
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if not self.has_permission(request, obj):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
```

### PluginGroup Permissions
- Group-level `permission` is checked first. If it fails, no wrapped plugins are accessible.
- Individual plugin permissions are checked in addition to the group-level permission.

---

## 8. PluginGroup Design

### Decision
`PluginGroup` is a non-view class that composes multiple `Plugin` classes. It provides:
- A single `Menu` entry (single tab)
- A `url_prefix` that prefixes all wrapped plugin URLs
- A `get_urls()` classmethod that loops over constituent plugins
- A concept of a "default plugin" (first in the list) whose URL is used for the tab link

### Rationale
- User described the PluginGroup composition pattern explicitly in the spec clarification.
- The default plugin concept is necessary because the tab must link to *something* — it links to the first plugin in the group.
- URL prefixing provides clean namespacing: `/samples/123/metadata/view/`, `/samples/123/metadata/edit/`.

### Implementation
```python
class PluginGroup:
    plugins = []      # List of Plugin classes
    url_prefix = ""   # Common URL prefix
    permission = None # Group-level permission
    
    class Menu:
        label = ""
        icon = ""
        order = 0
    
    @classmethod
    def get_urls(cls):
        patterns = []
        for plugin_cls in cls.plugins:
            for pattern in plugin_cls.get_urls():
                prefixed = path(f"{cls.url_prefix}/{pattern.pattern}", 
                               pattern.callback, 
                               name=pattern.name)
                patterns.append(prefixed)
        return patterns
    
    @classmethod
    def get_default_url_name(cls):
        """URL name for the tab link — first plugin's URL."""
        return cls.plugins[0].get_url_name()
```

### Alternatives Considered
1. **PluginGroup as a view** — Rejected because the group itself doesn't render anything; it's a composition container.
2. **Automatic CRUD PluginGroup** — Deferred as a convenience class; base PluginGroup is sufficient for composition.

---

## 9. Startup Validation via Django System Checks

### Decision
Use Django's `System Check Framework` to validate plugin configurations at startup. Register checks in the app's `AppConfig.ready()` method.

### Rationale
- Django system checks run at `manage.py check`, `manage.py runserver`, and in CI pipelines — exactly when you want to catch configuration errors.
- The check framework provides standardized error/warning levels (Error, Warning, Info) with structured IDs.
- This is the idiomatic Django approach (used by Django's own admin, auth, and contenttypes apps).

### Checks to Implement
| Check ID | Description |
|----------|-------------|
| `plugins.E001` | Plugin class missing required attributes |
| `plugins.E002` | Duplicate plugin name on same model |
| `plugins.E003` | URL path conflict between plugins on same model |
| `plugins.E004` | Plugin registered for non-existent model |
| `plugins.E005` | PluginGroup contains invalid/missing plugin classes |
| `plugins.E006` | URL path conflict within PluginGroup |
| `plugins.E007` | Plugin registered both standalone and in PluginGroup for same model |
| `plugins.W001` | Plugin permission string references non-existent permission |
| `plugins.W002` | Plugin template path not found (informational) |

---

## 10. Error Isolation

### Decision
Since each plugin IS a separate Django view with its own URL, error isolation is *naturally achieved* at the URL level. One plugin's template error results in a 500 on that plugin's URL only, not on other plugin pages.

For tab rendering (where tabs are links, not embedded content), tab list generation uses try/except to gracefully handle any plugin that raises during tab data collection.

### Rationale
- The spec clarified: "each tab navigates to that plugin's dedicated view URL (standard Django view pattern, not embedded content)."
- This means different plugins are different HTTP requests — one failing doesn't affect others.
- The only shared rendering surface is the tab list itself, which is a simple list of links generated from static data (Menu config + URL reversal).

---

## 11. Static Asset Management

### Decision
Use Django's standard `Media` inner class pattern on Plugin classes for static CSS/JS.

### Rationale
- Django already provides the `Media` class mechanism for forms and widgets — it's well-documented and automatic.
- Plugin templates can use `{{ plugin_media.css }}` and `{{ plugin_media.js }}` to include plugin-specific assets.
- This is how the current system works and it's the right pattern.

### Example
```python
class ChartPlugin(Plugin, TemplateView):
    class Media:
        css = {"all": ("plugins/chart/style.css",)}
        js = ("plugins/chart/chart.js",)
```

---

## 12. Base Model Registration with Visibility Checks

### Decision
Plugins register only against base models (Project, Dataset, Sample, Measurement, Contributor), not polymorphic subclasses. A `check` callable controls visibility for specific model types.

### Rationale
- Simpler registry: tracks only 4-5 base models instead of N polymorphic subclasses
- Easier to reason about: all Sample plugins in one place
- More flexible: `check` callable can handle complex logic beyond single-class matching
- Consistent with Django admin: registers on base models, uses filtering for customization
- User stated: "I don't think it makes sense to register plugins against specific subclasses... much simpler and easier to track if we only allow registering against the base models"

### Pattern
```python
from fairdm import plugins

@plugins.register(Sample)  # Base model, not RockSample
class AnalysisPlugin(Plugin, TemplateView):
    check = is_instance_of(RockSample)  # Helper function
    menu = {"label": "Analysis", "icon": "chart-bar", "order": 10}
```

### Helper Functions
The framework provides visibility helper functions:

```python
def is_instance_of(*model_classes):
    """Check if obj is an instance of any specified model class."""
    def check(request, obj):
        if obj is None:
            return True  # Model-level access
        return isinstance(obj, model_classes)
    return check

# Usage:
check = is_instance_of(RockSample, SoilSample)
```

Alternatively, use lambdas for simple checks:
```python
check = lambda request, obj: isinstance(obj, RockSample)
```

### Tab Filtering
Visibility checks are evaluated during tab collection:
```python
for plugin in registry.get_plugins_for_model(Sample):
    if plugin.check and not plugin.check(request, obj):
        continue  # Skip this plugin for this instance
    # ... permission check, then add to tabs
```

---

## 13. Backward Compatibility

### Decision
Backward compatibility is **NOT** a requirement (per user guidance). The new API will be a complete replacement of the existing plugin system.

### Migration Path
- Existing `FairDMPlugin` mixin → rename/refactor to new `Plugin` mixin
- Existing `PluginMenuItem` / `PluginConfig` → replace with `menu` dict attribute
- Existing old API → replace with `@plugins.register(BaseModel)` (on base models only)
- Registration on polymorphic subclasses → replace with `check = is_instance_of(Subclass)`
- Existing `PluggableView` → remove entirely; registry handles URL aggregation
- Existing category constants (EXPLORE, ACTIONS, MANAGEMENT) → remove
- Existing `flex_menu.Menu` instances on views → remove; replaced by Tab dataclass

### Rationale
User stated: "Backwards compatibility is not a requirement. Come up with the best API possible rather than trying to fit in with existing code."
