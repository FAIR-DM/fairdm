# Create a Plugin

This guide walks you through creating plugins in the FairDM Framework. Plugins are modular, reusable views that extend model detail pages with custom functionality.

## Overview

**What is a Plugin?**
A plugin is a Django class-based view (CBV) combined with the `Plugin` mixin that provides:
- Automatic URL routing under model detail pages
- Tab-based navigation (optional)
- Permission-based access control
- Template resolution hierarchy
- Breadcrumb navigation
- Static asset management

**Key Benefits:**
- ✅ No manual URL configuration required
- ✅ Automatic integration into model detail pages
- ✅ Reusable across multiple models
- ✅ Inheritable for creating base plugins in packages
- ✅ Polymorphic visibility with `check` functions

---

## Quick Start

### 1. Create a `plugins.py` Module

In any Django app, create a file named `plugins.py`:

```text
myapp/
├── templates/
│   └── plugins/
│       └── sample/
│           └── analysis.html
├── __init__.py
├── apps.py
├── models.py
├── plugins.py   ← define plugins here
```

### 2. Import Required Components

```python
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView, UpdateView

from fairdm import plugins
from fairdm.contrib.plugins import Plugin
from .models import Sample
from .forms import SampleAnalysisForm
```

### 3. Define and Register a Basic Plugin

```python
@plugins.register(Sample)
class AnalysisPlugin(Plugin, TemplateView):
    """Display analysis results for a sample."""
    
    # Tab configuration (required for tab visibility)
    menu = {
        "label": _("Analysis"),
        "icon": "chart-bar",
        "order": 20,
    }
    
    template_name = "plugins/sample/analysis.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Access the sample instance via self.object
        context["analysis_data"] = self.object.get_analysis()
        return context
```

### 4. Create a Template

Templates follow a hierarchical resolution pattern. Create your template at:
`templates/plugins/sample/analysis.html`

```html
{% extends "plugins/base.html" %}

{% block plugin_content %}
<div class="card">
    <div class="card-header">
        <h3>Analysis Results for {{ object.name }}</h3>
    </div>
    <div class="card-body">
        <p>Analysis data: {{ analysis_data }}</p>
    </div>
</div>
{% endblock %}
```

---

## Plugin Configuration

### Menu Configuration

The `menu` dict controls tab appearance and ordering:

```python
menu = {
    "label": _("My Plugin"),  # Required: Display text
    "icon": "chart-line",     # Optional: Icon name
    "order": 50,              # Optional: Sort position (default 0)
}
```

**To hide a plugin from tabs** (accessible only via direct URL):
```python
menu = None  # or omit the menu attribute
```

### Tab Ordering

Tabs are sorted by `order` value, then alphabetically by label:
- Lower numbers appear first
- Suggested ranges:
  - **0-99**: Overview and primary content
  - **100-499**: Edit/management functions  
  - **500-699**: Secondary content (descriptions, metadata)
  - **700-899**: Actions (export, import)
  - **900+**: Dangerous actions (delete)

### Permission-Based Access

Require specific permissions for plugin access:

```python
@plugins.register(Sample)
class EditPlugin(Plugin, UpdateView):
    menu = {"label": _("Edit"), "icon": "pencil", "order": 100}
    permission = "myapp.change_sample"  # Django permission string
    form_class = SampleForm
    
    # Users without this permission:
    # 1. Won't see the "Edit" tab
    # 2. Get 403 Forbidden on direct URL access
```

### Polymorphic Visibility

Show plugins only for specific model subtypes:

```python
from fairdm.contrib.plugins import is_instance_of

@plugins.register(Sample)
class RockAnalysisPlugin(Plugin, TemplateView):
    check = is_instance_of(RockSample)  # Only visible for RockSample
    menu = {"label": _("Geochemistry"), "order": 30}
```

Custom visibility checks:

```python
def has_location(request, obj):
    """Show plugin only if sample has a location."""
    return obj and hasattr(obj, "location") and obj.location is not None

@plugins.register(Sample)
class LocationPlugin(Plugin, TemplateView):
    check = has_location
    menu = {"label": _("Location"), "order": 40}
```

---

## Common Plugin Patterns

### 1. Overview Plugin (Read-Only View)

```python
from fairdm.core.plugins import BaseOverviewPlugin

@plugins.register(Sample)
class SampleOverview(BaseOverviewPlugin):
    # Inherits: menu = {"label": "Overview", "icon": "eye", "order": 0}
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["measurements"] = self.object.measurements.all()
        context["recent_activity"] = self.get_recent_activity()
        return context
```

### 2. Edit Plugin (Form-Based)

```python
from fairdm.core.plugins import BaseEditPlugin

@plugins.register(Sample)
class SampleEdit(BaseEditPlugin):
    menu = {"label": _("Edit"), "icon": "pencil", "order": 100}
    form_class = SampleForm
    permission = "samples.change_sample"
    
    def get_success_url(self):
        return self.object.get_absolute_url()
```

### 3. Delete Plugin

```python
from fairdm.core.plugins import BaseDeletePlugin

@plugins.register(Sample)
class SampleDelete(BaseDeletePlugin):
    menu = {"label": _("Delete"), "icon": "trash", "order": 900}
    permission = "samples.delete_sample"
    
    def get_success_url(self):
        from django.urls import reverse
        return reverse("sample-list")
```

### 4. List View Plugin (Related Objects)

```python
from fairdm.core.measurement.views import MeasurementListView

@plugins.register(Sample)
class SampleMeasurements(Plugin, MeasurementListView):
    menu = {"label": _("Measurements"), "icon": "table", "order": 25}
    template_name = "plugins/list_view.html"
    
    def get_queryset(self):
        return self.object.measurements.all()
```

### 5. Action Plugin (Export, Download, etc.)

```python
from django.http import HttpResponse

@plugins.register(Sample)
class ExportCSV(Plugin):
    menu = {"label": _("Export CSV"), "icon": "download", "order": 700}
    
    def get(self, request, *args, **kwargs):
        sample = self.object
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{sample.name}.csv"'
        
        # Generate CSV content
        writer = csv.writer(response)
        writer.writerow(["Field", "Value"])
        writer.writerow(["Name", sample.name])
        # ... add more data
        
        return response
```

---

## Advanced Features

### Plugin Groups

Wrap multiple plugins under a shared URL namespace and single tab:

```python
from fairdm.contrib.plugins import PluginGroup

class MetadataView(Plugin, TemplateView):
    menu = {"label": "View", "icon": "eye", "order": 10}
    template_name = "plugins/metadata/view.html"

class MetadataEdit(Plugin, UpdateView):
    menu = {"label": "Edit", "icon": "pencil", "order": 20}
    form_class = MetadataForm

@plugins.register(Sample)
class MetadataGroup(PluginGroup):
    plugins = [MetadataView, MetadataEdit]
    menu = {"label": "Metadata", "icon": "database", "order": 50}
    url_prefix = "metadata"  # URLs: .../metadata/view/, .../metadata/edit/
```

**Result:**
- Single "Metadata" tab in navigation
- URLs namespaced under "metadata/"
- Clicking tab navigates to first plugin (MetadataView)

### Custom URL Paths

Override auto-generated URL paths:

```python
@plugins.register(Sample)
class AnalysisPlugin(Plugin, TemplateView):
    url_path = "analyse"  # Instead of auto-generated "analysis-plugin"
    menu = {"label": "Analysis", "order": 20}
```

URL becomes: `/samples/<uuid>/analyse/` instead of `/samples/<uuid>/analysis-plugin/`

### Template Resolution Hierarchy

Plugins automatically search for templates in this order:

1. Explicit `template_name` if set
2. `plugins/{model_name}/{plugin_name}.html` (model-specific)
3. `plugins/{parent_model_name}/{plugin_name}.html` (polymorphic models)
4. `plugins/{plugin_name}.html` (plugin default)
5. `plugins/base.html` (framework fallback)

**Example:** For `AnalysisPlugin` registered with `Sample`:
- `plugins/sample/analysis-plugin.html`
- `plugins/analysis-plugin.html`
- `plugins/base.html`

This allows model-specific customization without code changes.

### Static Assets (CSS/JavaScript)

Include plugin-specific assets using Django's Media class:

```python
@plugins.register(Sample)
class ChartPlugin(Plugin, TemplateView):
    menu = {"label": "Charts", "icon": "chart", "order": 40}
    
    class Media:
        css = {
            "all": ("plugins/charts/styles.css",),
        }
        js = (
            "https://cdn.jsdelivr.net/npm/chart.js",
            "plugins/charts/init.js",
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["chart_data"] = self.object.get_chart_data()
        return context
```

**In your template:**
```html
{% extends "plugins/base.html" %}

{% block extra_head %}
    {{ plugin_media.css }}
{% endblock %}

{% block plugin_content %}
    <canvas id="myChart"></canvas>
{% endblock %}

{% block extra_js %}
    {{ plugin_media.js }}
{% endblock %}
```

---

## Creating Reusable Plugins

### Base Plugin Classes for Distribution

Create base plugins that others can inherit:

```python
# In your package: mypackage/plugins.py
from fairdm.contrib.plugins import Plugin
from django.views.generic import TemplateView

class GeologyAnalysisPlugin(Plugin, TemplateView):
    """Reusable geology analysis plugin."""
    menu = {"label": "Geology", "icon": "gem", "order": 30}
    template_name = "geology/analysis.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["geology_data"] = self.analyze_geology(self.object)
        return context
    
    def analyze_geology(self, sample):
        """Override this method to customize analysis."""
        return {}
```

### Portal Developer Inheritance

Users of your package can inherit and customize:

```python
# In portal project: myportal/plugins.py
from mypackage.plugins import GeologyAnalysisPlugin
from fairdm import plugins
from .models import Sample

@plugins.register(Sample)
class CustomGeologyPlugin(GeologyAnalysisPlugin):
    # Inherit menu, template, base behavior
    # Customize analysis logic
    def analyze_geology(self, sample):
        # Portal-specific geology analysis
        return {
            "custom_metric": sample.calculate_custom_metric(),
            "local_data": sample.get_local_geology_data(),
        }
```

---

## Context Variables

Plugins automatically receive these context variables:

- **`object`**: The model instance (Project, Dataset, Sample, etc.)
- **`tabs`**: List of Tab objects for this model
- **`breadcrumbs`**: Breadcrumb navigation chain
- **`plugin_media`**: CSS/JS assets (if Media class defined)
- **`view`**: The plugin view instance

### Accessing the Model Instance

```python
def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    
    # Access the model instance
    sample = self.object  # or context["object"]
    
    # Add custom data
    context["measurements"] = sample.measurements.all()
    context["location"] = sample.location
    
    return context
```

---

## Template Guidelines

### Extend the Base Template

```html
{% extends "plugins/base.html" %}

{% block plugin_content %}
    <!-- Your content here -->
{% endblock %}
```

### Available Template Blocks

- `plugin_content`: Main content area (recommended)
- `extra_head`: Additional <head> content (CSS links, etc.)
- `extra_js`: Additional JavaScript at page bottom
- `breadcrumbs`: Override breadcrumb navigation

### Use Framework Components

```html
{% load cotton %}

<c-card>
    <c-card-header>
        <h3>{{ object.name }}</h3>
    </c-card-header>
    <c-card-body>
        <p>Your content here...</p>
    </c-card-body>
</c-card>
```

---

## Registering for Multiple Models

Register a plugin with multiple models:

```python
@plugins.register(Sample, Measurement)
class ExportPlugin(Plugin):
    menu = {"label": "Export", "icon": "download", "order": 700}
    
    def get(self, request, *args, **kwargs):
        obj = self.object
        # Works for both Sample and Measurement
        return self.generate_export(obj)
```

---

## Django System Checks

The plugin system includes validation checks:

**E001**: Plugin missing required attributes (e.g., inherits neither Plugin nor Django CBV)
**E002**: Duplicate plugin names for the same model
**E003**: URL path conflicts between plugins
**E004**: Invalid `template_name` (file doesn't exist)
**E005**: PluginGroup with empty `plugins` list
**E006**: PluginGroup contains invalid plugin classes
**E007**: URL prefix conflicts between plugin groups
**W001**: Invalid permission string (permission doesn't exist)
**W002**: Menu configuration missing required keys
**W003**: URL path contains invalid characters

Run checks:
```bash
poetry run python manage.py check
```

---

## Migration from Old Plugin API

If you have plugins using the old API (`@plugin.register('model.Model', category=...)`), update them:

**Old API:**
```python
@plugin.register('sample.Sample', category=plugins.EXPLORE)
class Analysis(BasePlugin, TemplateView):
    menu_item = MenuLink(name="Analysis", icon="chart")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sample = self.base_object
        return context
```

**New API:**
```python
@plugins.register(Sample)
class Analysis(Plugin, TemplateView):
    menu = {"label": "Analysis", "icon": "chart", "order": 20}
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sample = self.object
        return context
```

**Key Changes:**
- ✅ Use model class instead of string: `Sample` not `'sample.Sample'`
- ✅ Import from `fairdm.contrib.plugins` not `fairdm.plugins`
- ✅ Inherit `Plugin` mixin, not `BasePlugin`
- ✅ Use `menu` dict, not `menu_item = MenuLink(...)`
- ✅ Access instance via `self.object`, not `self.base_object`
- ✅ Order tabs with `menu["order"]`, not categories
- ✅ No `category` parameter needed

---

## Examples

### Complete Plugin Example

```python
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from fairdm import plugins
from fairdm.contrib.plugins import Plugin, is_instance_of
from .models import Sample, RockSample

@plugins.register(Sample)
class GeochemistryPlugin(Plugin, TemplateView):
    """Display geochemical analysis for rock samples."""
    
    # Only show for RockSample instances
    check = is_instance_of(RockSample)
    
    # Tab configuration
    menu = {
        "label": _("Geochemistry"),
        "icon": "atom",
        "order": 35,
    }
    
    # Require permission
    permission = "samples.view_geochemistry"
    
    # Template
    template_name = "plugins/sample/geochemistry.html"
    
    # Static assets
    class Media:
        css = {"all": ("plugins/geochemistry/style.css",)}
        js = ("plugins/geochemistry/charts.js",)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get the rock sample
        rock = self.object
        
        # Add analysis data
        context["elements"] = rock.get_element_concentrations()
        context["isotopes"] = rock.get_isotope_ratios()
        context["minerals"] = rock.get_mineral_composition()
        
        return context
```

---

## Best Practices

1. ✅ **Always inherit from both `Plugin` and a Django CBV**
   ```python
   class MyPlugin(Plugin, TemplateView):  # Correct
   ```

2. ✅ **Use `self.object` to access the model instance**
   ```python
   sample = self.object  # Correct
   ```

3. ✅ **Set appropriate `order` values for logical tab ordering**
   ```python
   menu = {"label": "Overview", "order": 0}  # First tab
   menu = {"label": "Edit", "order": 100}    # Middle tab
   menu = {"label": "Delete", "order": 900}  # Last tab
   ```

4. ✅ **Use permission strings for access control**
   ```python
   permission = "myapp.change_sample"
   ```

5. ✅ **Create model-specific templates for customization**
   ```
   templates/plugins/sample/my-plugin.html
   templates/plugins/measurement/my-plugin.html
   ```

6. ✅ **Use Media class for static assets, not inline `<style>` or `<script>`**
   ```python
   class Media:
       css = {"all": ("myapp/plugin.css",)}
       js = ("myapp/plugin.js",)
   ```

7. ✅ **Test plugins with Django system checks**
   ```bash
   poetry run python manage.py check
   ```

---

## Troubleshooting

**Plugin doesn't appear as tab:**
- Check that `menu` is set (not `None`)
- Verify user has required `permission`
- Check that `check` function returns `True`

**403 Forbidden when accessing plugin:**
- Verify `permission` attribute is correct
- Ensure user has the required permission
- Check object-level permissions (django-guardian)

**Template not found:**
- Check `template_name` is correct
- Verify template exists in search path
- Use absolute path or rely on hierarchical resolution

**URL conflict:**
- Run `python manage.py check` for error E003
- Set unique `url_path` for each plugin
- Use PluginGroups to namespace related plugins

**Assets not loading:**
- Run `python manage.py collectstatic`
- Check static file paths in Media class
- Verify STATIC_URL in settings

---

## Further Reading

- [Plugin System Architecture](../../specs/008-plugin-system/plan.md)
- [Quick Start Examples](../../specs/008-plugin-system/quickstart.md)
- [Demo App Plugins](../../fairdm_demo/plugins.py) - Working examples

Plugins are automatically discovered from any `plugins.py` file in installed Django apps. Ensure your app is in `INSTALLED_APPS` for plugins to be loaded.

## Summary

- Use `@plugin.register('model.name', category=plugins.CATEGORY)` for registration
- Create explicit `MenuLink` instances for menu configuration
- Access the related object via `self.base_object`
- Choose appropriate base classes: `Explore`, `Action`, or `Management`
- Wrap template content with `<c-plugin>` components
- Use FairDM components for consistent UI design
- **Always use separate CSS/JS files with the `Media` inner class** - never inline styles or scripts
