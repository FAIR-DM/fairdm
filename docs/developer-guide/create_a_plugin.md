# Create a Plugin

This guide walks you through creating a plugin in the FairDM Framework. Plugins are modular views that integrate seamlessly into the portal via registration, automatic routing, and a consistent UI system.

## 1. Plugin Types

FairDM supports three types of plugins:

- **Explore**: Analytical and exploratory views (data visualization, statistics, etc.)
- **Actions**: Operations that perform actions (export, import, transformation, etc.)  
- **Management**: Form-based views for managing object data and settings

## 2. Create a plugins.py module

In any **Django app** that is discoverable by Django, create a file named `plugins.py`.

Your app directory should look like this:

```text
myapp/
├── templates/
│   └── myapp/
│       └── myplugin.html
├── __init__.py
├── apps.py
├── plugins.py   ← define your plugin here
├── ...
```

## 3. Import Required Components

```python
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from fairdm import plugins  # For category constants
from fairdm.plugins import plugin, MenuLink, BasePlugin
```

## 4. Define and Register Your Plugin

Use the `@plugin.register()` decorator to register plugins with explicit model strings and category constants:

### Explore Plugin Example

```python
@plugin.register('dataset.Dataset', category=plugins.EXPLORE)
class DatasetAnalysis(BasePlugin, TemplateView):
    menu_item = MenuLink(name=_("Analysis"), icon="chart-bar")
    template_name = "myapp/analysis.html"
    title = _("Dataset Analysis")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dataset = self.base_object
        context["stats"] = self.calculate_stats(dataset)
        return context
    
    def calculate_stats(self, dataset):
        # Your analysis logic here
        return {"record_count": dataset.samples.count()}
```

### Action Plugin Example

```python
@plugin.register('sample.Sample', category=plugins.ACTIONS)
class ExportSample(BasePlugin):
    menu_item = MenuLink(name=_("Export CSV"), icon="download")
    title = _("Export Sample Data")
    
    def get(self, request, *args, **kwargs):
        sample = self.base_object
        # Generate CSV export
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{sample.name}.csv"'
        # Add your export logic here
        return response
```

### Management Plugin Example

```python
@plugin.register('project.Project', category=plugins.MANAGEMENT)  
class ProjectSettings(plugins.Management):
    menu_item = MenuLink(name=_("Settings"), icon="gear")
    form_class = ProjectSettingsForm
    title = _("Project Settings")
    
    def get_object(self):
        return self.base_object
```

## 5. Plugin Configuration

### Required Attributes

- **menu_item**: A `MenuLink` instance defining how the plugin appears in menus
  - Set to `None` to hide the plugin from menus
- **title**: The page title for the plugin view

### Optional Attributes

- **path**: Custom URL path (auto-generated from class name if not provided)
- **template_name**: Custom template path
- **sections**: Layout configuration for sidebars and headers
- **check**: Permission check function or boolean

### MenuLink Configuration

```python
menu_item = MenuLink(
    name=_("My Plugin"),           # Display name in menu
    icon="chart-line",            # Icon name (FontAwesome)
    check=my_permission_function  # Optional permission check
)
```

### Adding CSS and JavaScript

:::{important}
**Always create CSS and JavaScript in separate files.** Do not use inline `<style>` or `<script>` tags in plugin templates.
:::

Use Django's `Media` inner class to declare static assets:

```python
@plugin.register('dataset.Dataset', category=plugins.EXPLORE)
class DatasetAnalysis(BasePlugin, TemplateView):
    menu_item = MenuLink(name=_("Analysis"), icon="chart-bar")
    template_name = "myapp/analysis.html"
    title = _("Dataset Analysis")
    
    class Media:
        css = {
            'all': ('myapp/css/analysis.css',)
        }
        js = ('myapp/js/charts.js', 'myapp/js/analysis.js')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stats"] = self.calculate_stats(self.base_object)
        return context
```

**File Structure:**
```text
myapp/
├── static/
│   └── myapp/
│       ├── css/
│       │   └── analysis.css
│       └── js/
│           ├── charts.js
│           └── analysis.js
├── templates/
│   └── myapp/
│       └── analysis.html
└── plugins.py
```

**Benefits:**
- Proper caching and minification in production
- Better code organization and reusability
- Automatic asset collection via `collectstatic`
- Easier debugging and maintenance

## 6. Plugin Base Classes

Choose the appropriate base class for your plugin type:

- **`plugins.Explore`**: For analytical/exploratory views
- **`plugins.Action`**: For action-based operations  
- **`plugins.Management`**: For form-based management views

All inherit from `BasePlugin` and provide type-specific defaults.

## 7. Accessing the Base Object

In your plugin, access the related model instance via `self.base_object`:

```python
def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    
    # Access the object this plugin is attached to
    dataset = self.base_object  # Will be Dataset, Project, Sample, etc.
    
    # Add your custom context
    context["sample_count"] = dataset.samples.count()
    return context
```

## 8. Create a Template

Create a template for your plugin that matches the `template_name` attribute. Wrap your content in a `<c-plugin>` component for consistent styling:

```html
<c-plugin>
    <h2>{{ dataset.name }}</h2>
    <p>This dataset contains {{ stats.record_count }} samples.</p>
    
    <!-- Use FairDM components for consistency -->
    <c-card>
        <c-card-header>Analysis Results</c-card-header>
        <c-card-body>
            <p>Your analysis content here...</p>
        </c-card-body>
    </c-card>
</c-plugin>
```

:::{note}
**Important:** Do not use `{% extends %}` in plugin templates. The base layout is injected automatically by the plugin system.
:::

:::{tip}
Use the FairDM component library for consistent UI design. See the [component documentation](../components/components.md) for available components.
:::

## 9. Model Registration Strings

Use these model strings when registering plugins:

- `'project.Project'` - For project-level plugins
- `'dataset.Dataset'` - For dataset-level plugins  
- `'sample.Sample'` - For sample-level plugins
- `'measurement.Measurement'` - For measurement-level plugins

## 10. Plugin Discovery

Plugins are automatically discovered from any `plugins.py` file in installed Django apps. Ensure your app is in `INSTALLED_APPS` for plugins to be loaded.

## Summary

- Use `@plugin.register('model.name', category=plugins.CATEGORY)` for registration
- Create explicit `MenuLink` instances for menu configuration
- Access the related object via `self.base_object`
- Choose appropriate base classes: `Explore`, `Action`, or `Management`
- Wrap template content with `<c-plugin>` components
- Use FairDM components for consistent UI design
- **Always use separate CSS/JS files with the `Media` inner class** - never inline styles or scripts
