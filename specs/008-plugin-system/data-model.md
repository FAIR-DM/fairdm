# Data Model: Plugin System for Model Extensibility

**Feature**: 008-plugin-system  
**Date**: 2026-02-17

---

## Overview

The plugin system does not define database models (no Django ORM entities). It is a **runtime registration and composition system** that operates entirely in memory. The "data model" here describes the Python classes, their attributes, relationships, and lifecycle.

---

## Entity Definitions

### 1. Plugin (Mixin Class)

**Module**: `fairdm.contrib.plugins.base`  
**Type**: Python mixin class (no database table)  
**Purpose**: Adds plugin behavior to any Django class-based view

#### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | Auto from class name | Unique identifier per model (slugified) |
| `url_path` | `str` | Auto from `name` | URL path segment for this plugin |
| `template_name` | `str` | `""` (uses resolution) | Explicit template path override |
| `permission` | `str \| None` | `None` | Required permission string (e.g., `"myapp.change_sample"`) |
| `check` | `Callable[[HttpRequest, Model \| None], bool] \| None` | `None` | Visibility check for model type filtering |
| `model` | `type[Model] \| None` | `None` | Set by registry during registration (base model only) |
| `menu` | `dict \| None` | `None` | Tab configuration dict with keys: `label` (str), `icon` (str, optional), `order` (int, default 0). If None/falsey, no tab is created. |

#### Inner Classes

##### `Media` (optional, standard Django)
Controls static asset inclusion.

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `css` | `dict` | `{}` | CSS files by media type |
| `js` | `tuple` | `()` | JavaScript file paths |

#### Key Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `get_name` | `@classmethod -> str` | Returns the plugin name (slugified class name if not set) |
| `get_url_path` | `@classmethod -> str` | Returns URL path segment |
| `get_urls` | `@classmethod -> list[URLPattern]` | Generates URL pattern(s) for this plugin |
| `get_template_names` | `() -> list[str]` | Hierarchical template resolution |
| `get_object` | `() -> Model` | Fetches model instance from URL kwargs |
| `has_permission` | `(request, obj=None) -> bool` | Two-tier permission check |
| `get_context_data` | `(**kwargs) -> dict` | Adds object, tabs, breadcrumbs, media |
| `get_breadcrumbs` | `() -> list[dict]` | Auto-generates breadcrumb chain |
| `dispatch` | `(request, *args, **kwargs) -> HttpResponse` | Permission-gated dispatch |

#### Lifecycle

```
1. Developer defines Plugin subclass (paired with Django CBV)
2. @plugins.register(Model) registers class with registry
3. Registry validates: name uniqueness, URL conflicts, permissions
4. At URL include time: Plugin.get_urls() generates URL patterns
5. At request time: dispatch() → permission check → view logic → render
```

#### Validation Rules

- `name` must be unique per base model (same name allowed across different base models)
- `url_path` must be unique per base model (same path allowed across different base models)
- `permission` string, if set, should reference an existing Django permission
- When paired with a Django CBV, the Plugin mixin must appear first in MRO
- `check` callable, if set, must accept `(request, obj)` and return bool
- Plugins should only register on base models (Project, Dataset, Sample, Measurement, Contributor), not polymorphic subclasses

---

### 2. PluginGroup (Composition Container)

**Module**: `fairdm.contrib.plugins.group`  
**Type**: Python class (no database table, not a view)  
**Purpose**: Wraps multiple Plugin classes into a single feature unit with shared URL namespace

#### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `plugins` | `list[type[Plugin]]` | `[]` | Ordered list of wrapped plugin classes |
| `url_prefix` | `str` | Auto from class name | Common URL prefix for all wrapped plugins |
| `permission` | `str \| None` | `None` | Group-level permission (checked before individual plugin perms) |
| `name` | `str` | Auto from class name | Group identifier |
| `menu` | `dict \| None` | `None` | Tab configuration dict with keys: `label` (str), `icon` (str, optional), `order` (int, default 0). Required for tab visibility. |

#### Key Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `get_urls` | `@classmethod -> list[URLPattern]` | Iterates plugins, prefixes each URL pattern |
| `get_default_plugin` | `@classmethod -> type[Plugin]` | Returns first plugin (tab link target) |
| `get_default_url_name` | `@classmethod -> str` | Returns URL name of default plugin |

#### Lifecycle

```
1. Developer defines individual Plugin classes (can omit Menu — group provides it)
2. Developer defines PluginGroup with plugins list and Menu
3. @plugins.register(Model) registers the group
4. Registry validates: group-level and individual plugin constraints
5. PluginGroup.get_urls() generates prefixed URL patterns for all wrapped plugins
6. Tab rendering uses group's Menu, linking to default plugin's URL
```

#### Validation Rules

- `plugins` list must not be empty
- All entries in `plugins` must be Plugin subclasses
- No URL path conflicts within the group's plugins
- Individual plugins in the group must not also be registered standalone for the same model
- Group `name` follows same uniqueness rules as Plugin `name`

---

### 3. Tab (Data Transfer Object)

**Module**: `fairdm.contrib.plugins.menu`  
**Type**: Python dataclass (no database table)  
**Purpose**: Represents a single tab entry for template rendering

#### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `label` | `str` | — | Display text |
| `icon` | `str` | `""` | Icon identifier |
| `url` | `str` | — | Resolved URL for the tab link |
| `order` | `int` | `0` | Sort position |
| `is_active` | `bool` | `False` | Whether this tab is the current page |

#### Construction
Tabs are built by `PluginRegistry.get_tabs_for_model()` from registered plugins/groups that have a `Menu` inner class, filtered by the current user's permissions.

---

### 4. PluginRegistry (Singleton)

**Module**: `fairdm.contrib.plugins.registry`  
**Type**: Python class (singleton instance)  
**Purpose**: Central registry tracking model → plugin/group associations

#### Internal State

| Attribute | Type | Description |
|-----------|------|-------------|
| `_registry` | `dict[type[Model], list[type[Plugin \| PluginGroup]]]` | Maps models to their registered plugins/groups |

#### Key Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `register` | `(*models) -> Callable` | Decorator for registering plugins/groups |
| `get_plugins_for_model` | `(model) -> list` | All plugins/groups for a model |
| `get_urls_for_model` | `(model) -> list[URLPattern]` | Aggregated URL patterns |
| `get_tabs_for_model` | `(model, request, obj) -> list[Tab]` | Permission-filtered, sorted tabs |
| `is_registered` | `(plugin, model) -> bool` | Check if plugin is registered for model |

#### Global Instances

```python
registry = PluginRegistry()       # Singleton
# In fairdm/__init__.py - exports from fairdm.contrib.plugins.registry
# Users do: from fairdm import plugins; @plugins.register(...)
register = registry.register  # Convenience alias
```

---

## Helper Functions

### Visibility Check Helpers

**Module**: `fairdm.contrib.plugins.visibility`

The framework provides helper functions for common visibility check patterns:

#### `is_instance_of(*model_classes)`

```python
def is_instance_of(*model_classes: type[Model]) -> Callable[[HttpRequest, Model | None], bool]:
    """Returns a check function that passes if obj is an instance of any model_class."""
    def check(request, obj):
        if obj is None:
            return True  # Allow model-level access
        return isinstance(obj, model_classes)
    return check
```

**Usage**:
```python
# Single model type
check = is_instance_of(RockSample)

# Multiple model types
check = is_instance_of(RockSample, SoilSample, WaterSample)
```

#### Custom Check Functions

For complex logic, define custom callables:
```python
def check_is_published(request, obj):
    """Only show for published samples."""
    if obj is None:
        return True
    return getattr(obj, 'status', None) == 'published'

class AnalysisPlugin(Plugin, TemplateView):
    check = check_is_published
    ...
```

Or use lambdas for simple checks:
```python
class AnalysisPlugin(Plugin, TemplateView):
    check = lambda request, obj: isinstance(obj, RockSample) and obj.status == 'published'
    ...
```

---

## Entity Relationships

```
PluginRegistry (1) ─────manages────── (N) Plugin/PluginGroup
      │                                        │
      │ maps: Model → [Plugin|PluginGroup]     │
      │                                        │
      ├── get_urls_for_model() ──calls──► Plugin.get_urls()
      │                                  PluginGroup.get_urls()
      │                                        │
      └── get_tabs_for_model() ──reads──► Plugin.Menu / PluginGroup.Menu
                                               │
                                          produces
                                               │
                                          list[Tab]
                                               │
                                          rendered by
                                               │
                                          Template (nav-tabs)

PluginGroup (1) ─────wraps────── (N) Plugin
      │
      ├── url_prefix → prepended to each Plugin's url_path
      ├── Menu → single Tab entry
      └── get_urls() → loop Plugin.get_urls() + prefix
```

---

## State Transitions

The plugin system is stateless at runtime — there are no state machines or transitions. The key lifecycle phases are:

| Phase | Trigger | Actions |
|-------|---------|---------|
| **Registration** | `@plugins.register(Model)` at import time | Plugin added to registry, validation deferred |
| **Validation** | `AppConfig.ready()` / `manage.py check` | System checks validate all registrations |
| **URL Generation** | `include()` in urlpatterns | `get_urls()` called on each plugin/group |
| **Tab Collection** | Template tag / context processor | `get_tabs_for_model()` builds Tab list |
| **Request Dispatch** | HTTP request to plugin URL | `dispatch()` → permission check → view render |

---

## Composition Patterns

### Pattern A: Simple Plugin (Single View)

```python
from fairdm import plugins
from fairdm.contrib.plugins import is_instance_of

@plugins.register(Sample)  # Base model
class AnalysisPlugin(Plugin, TemplateView):
    check = is_instance_of(RockSample)  # Only for RockSample instances
    template_name = "plugins/analysis.html"
    menu = {
        "label": "Analysis",
        "icon": "chart-bar",
        "order": 10,
    }
```

**URL produced**: `samples/<uuid>/analysis/`  
**Tab**: "Analysis" with chart-bar icon at position 10 (only visible on RockSample detail pages)

### Pattern B: PluginGroup (Multi-View Feature)

```python
from fairdm import plugins

class GeospatialView(Plugin, DetailView):
    template_name = "geospatial/view.html"

class GeospatialEdit(Plugin, UpdateView):
    form_class = GeospatialForm
    permission = "myapp.change_geospatial"

@plugins.register(Sample)  # Base model
class GeospatialGroup(PluginGroup):
    check = is_instance_of(RockSample, WaterSample)  # Multiple model types
    plugins = [GeospatialView, GeospatialEdit]
    url_prefix = "geospatial"
    menu = {
        "label": "Geospatial",
        "icon": "map",
        "order": 15,
    }
```

**URLs produced**:
- `samples/<uuid>/geospatial/geospatial-view/`
- `samples/<uuid>/geospatial/geospatial-edit/`

**Tab**: "Geospatial" with map icon, links to first plugin (view)

### Pattern C: Plugin Without Tab (Direct URL Only)

```python
from fairdm import plugins

@plugins.register(Sample)  # All Sample types
class DeletePlugin(Plugin, DeleteView):
    permission = "myapp.delete_sample"
    success_url = "/"
    menu = None  # No tab, direct URL only
```

**URL produced**: `samples/<uuid>/delete/`  
**Tab**: None (menu is None)  
**Visibility**: All Sample instances (no `check` filter)

### Pattern D: Reusable Plugin (Third-Party)

```python
# In a published package
class KeywordPlugin(Plugin, UpdateView):
    form_class = None  # Set by subclass or auto-generated
    menu = {
        "label": "Keywords",
        "icon": "tags",
        "order": 50,
    }

# In a portal developer's code
@register_plugin(Sample)  # Base model
class RockKeywords(KeywordPlugin):
    check = is_instance_of(RockSample)
    form_class = RockKeywordForm
```
