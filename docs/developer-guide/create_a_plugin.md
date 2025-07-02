# Create a plugin

This guide walks you through creating a plugin in the FairDM Framework. Plugins are modular views that integrate seamlessly into the portal via registration, automatic routing, and a consistent UI system using fairdm components.

## 1. Create a plugins.py module

In any **Django app** that is discoverable by Django, create a file named `plugins.py`.

Your app directory should now look something like this:

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

## 2. Define the plugin class

Inside `plugins.py`, define new view class just like you would with a normal Django class-based view. Be sure
to also inherit from `GenericPlugin` to gain access to the plugin system. You will also need to register your
plugin using the `@plugins.register` decorator. Doing so will automatically add the plugin to the appropriate menus in 
the UI and handle all required URL routing.

```python
from django.views.generic import TemplateView
from fairdm.plugins import GenericPlugin

class MyPlugin(GenericPlugin, TemplateView): 
    template_name = "myapp/myplugin.html" 
    name = "My Plugin" 
    menu = "Tools" # default = "Explore"
    icon = "fa fa-cog" # Optional
```

The attributes `name`, `menu`, and `icon` are specific to the `GenericPlugin` class. They define where the plugin will
appear in the sidebar menu and how it will be displayed.

- `name`: The name of the plugin as it will appear in the menu. Also used to generate the URL for the plugin.
- `menu`: The menu under which the plugin will be listed. If not specified, defaults to "Explore". If set to False, the 
plugin will not be listed in the menu.
- `icon`: The icon to be displayed next to the plugin name in the menu.
- `sidebar_primary`: A dictionary of configuration values for the primary sidebar (left).
- `sidebar_secondary`: A dictionary of configuration values for the secondary sidebar (right).

## 3. Register the plugin

For the plugin to be shown in the portal, you need to register it. This is done using the `@plugins.register` decorator. 
The decorator takes a list of model types ("project", "dataset", "sample", or "contributor") that the plugin will be 
associated with. Once properly registered, the plugin will then be available for those models in the portal.

```python
from django.views.generic import TemplateView
from fairdm.plugins import GenericPlugin
from fairdm import plugins # NEW: decorator for registration

@plugins.register(to=["dataset"]) # New: register the plugin (this will register for the dataset detail page only) 
class MyPlugin(GenericPlugin, TemplateView): 
    template_name = "myapp/myplugin.html" 
    name = "My Plugin" # name shown in the menu
    menu = "Tools" # default = "Explore"
    icon = "fa fa-cog" # Optional
```


## 4. Add some context

Next, add some context to your plugin that will be passed to the template. You can do this by overriding the `get_context_data` method.
This method is called when the plugin is rendered, and it allows you to add any additional context variables you need.
In your context data, you will already have access to the underlying base object (e.g., `dataset`, `project`, or `sample`) via
context["base_object"] or context["dataset"] (if you have registered it to dataset). You will also have access to the
related class (e.g., `Dataset`, `Project`, or `Sample`) via context["related_class"].

`related_class` and `related_object` are also available as methods on the plugin class itself.

```python

@plugins.register(to=["dataset"])
class DatasetSummary(GenericPlugin, TemplateView): 
    template_name = "myapp/summary.html" 
    name = "Summary" 
    menu = "Data Summary" 
    
    def get_context_data(self, **kwargs): 
        context = super().get_context_data(**kwargs) 
        dataset = self.base_object # Access the related dataset 
        Dataset = self.related_class # Access the related class (Dataset)
        # add any additional context variables you need
        context["summary"] = generate_summary_for(dataset) # Custom function to generate summary  
        return context
```

## 5. Create a template for your plugin

Now, create a template for your plugin. This template will be rendered when the plugin is accessed in the portal. The 
location of the template should match the `template_name` attribute you specified in your plugin class.

In your template, create a `<c-plugin>` wrapper around your content. This ensures that the plugin is styled correctly 
and fits into the overall design of the portal.

```html
<c-plugin> 
    <h2>{{ dataset.name }}</h2> 
    <p>This dataset contains {{ summary.record_count }} records.</p>
</c-plugin>
```

:::{note}
**Important:** Do not use `{% extends %}` in your plugin templates. The base layout will be injected automatically by the plugin system.
:::
:::{tip}
Use the FairDM component library to ensure consistency in design with other aspects of the portal. 
See the [component documentation](../components/components.md) for available components.
:::

## Summary

- Define your plugin class in `plugins.py` and register it with `@plugins.register`.
- Gain access to the related model instance via `self.base_object`.
- Do **not** use `{% extends %}` in templates—wrap content with `<c-plugin>`.
- Use fairdm components for consistent UI design.
