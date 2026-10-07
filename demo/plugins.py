"""Example plugins demonstrating inheritance and reusability patterns.

This module shows how portal developers can:
1. Inherit from the framework's base class for an overview (OverviewPlugin)
2. Customize behavior by overriding methods
3. Use polymorphic visibility checks
4. Register plugins for custom models

These examples serve as living documentation for plugin development patterns. Editing and
deleting a project, dataset, sample or measurement needs no plugin of your own: the shared pages
in fairdm.core.editing are registered on every record type.

### Example 1: Basic Inheritance from Framework Base Classes

```python
@plugins.register(Project)
class ProjectOverview(OverviewPlugin):
    '''Project overview inheriting standard behavior from framework.

    This demonstrates:
    - Inheriting menu configuration from OverviewPlugin
    - Inheriting template resolution hierarchy
    - Adding custom context data via method override
    '''

    # Menu configuration inherited from OverviewPlugin
    # (label="Overview", icon="eye", order=0)

    def get_context_data(self, **kwargs):
        '''Add project-specific context: datasets, samples, contributors.'''
        context = super().get_context_data(**kwargs)

        # Add related objects to context
        context["datasets"] = self.object.datasets.all()
        context["samples"] = self.object.samples.all()
        context["contributors"] = self.object.contributors.all()

        return context
```

### Example 2: Custom Plugin Without Inheritance

```python
@plugins.register(Sample)
class SampleOverview(Plugin):
    '''Sample overview demonstrating custom plugin without base class.

    This shows that you can create plugins from scratch without inheriting
    from framework base classes if you need full control.
    '''

    from django.views.generic import TemplateView

    # Must inherit from a Django CBV
    __bases__ = (Plugin, TemplateView)

    menu = {"label": _("Overview"), "icon": "eye", "order": 0}

    def get_context_data(self, **kwargs):
        '''Add sample-specific context.'''
        context = super().get_context_data(**kwargs)

        context["measurements"] = self.object.measurements.all()
        context["location"] = getattr(self.object, "location", None)

        return context
```

### Example 3: Polymorphic Visibility with Check Functions

```python
@plugins.register(Sample)
class LocationDetailsPlugin(Plugin):
    '''Plugin that only appears for samples with locations.

    This demonstrates:
    - Using a custom check function for conditional visibility
    - The plugin tab only appears when the condition is met
    '''

    from django.views.generic import TemplateView

    __bases__ = (Plugin, TemplateView)

    menu = {"label": _("Location Details"), "icon": "geo-alt", "order": 50}

    # Custom visibility check: only show if sample has a location
    @staticmethod
    def check(request, obj):
        '''Only visible for samples with assigned locations.'''
        return obj and hasattr(obj, "location") and obj.location is not None

    template_name = "demo/plugins/location_details.html"

    def get_context_data(self, **kwargs):
        '''Add location and coordinates to context.'''
        context = super().get_context_data(**kwargs)

        if self.object.location:
            context["location"] = self.object.location
            context["coordinates"] = {
                "lat": self.object.location.latitude,
                "lon": self.object.location.longitude,
            }

        return context
```

### Example 4: Using is_instance_of for Polymorphic Models

```python
@plugins.register(Sample)
class RockAnalysisPlugin(Plugin, TemplateView):
    '''Plugin only visible for RockSample instances.

    This demonstrates:
    - Using is_instance_of() helper for polymorphic filtering
    - Plugin won't appear for WaterSample or other Sample subtypes
    '''

    from .models import RockSample

    check = is_instance_of(RockSample)  # Only visible for RockSample
    menu = {"label": _("Rock Analysis"), "icon": "gem", "order": 30}
    template_name = "demo/plugins/rock_analysis.html"
```

### Example 5: Location Model Plugins (requires a Location model)

```python
@plugins.register(Location)
class LocationOverview(OverviewPlugin):
    '''Location overview with map display.'''

    menu = {"label": _("Map"), "icon": "map", "order": 0}

    def get_context_data(self, **kwargs):
        '''Add map configuration to context.'''
        context = super().get_context_data(**kwargs)

        # Add coordinates for map rendering
        context["map_center"] = {
            "lat": self.object.latitude,
            "lon": self.object.longitude,
        }
        context["zoom_level"] = 12

        # Add samples at this location
        context["samples"] = self.object.samples.all()

        return context
```

## Notes for Portal Developers

1. **Import base classes from framework:**
   from fairdm.core.plugins import OverviewPlugin

2. **Register plugins with decorator:**
   @plugins.register(YourModel)

3. **Inherit from base + Django CBV:**
   class YourPlugin(OverviewPlugin):  # or (Plugin, TemplateView)

4. **Set menu configuration:**
   menu = {"label": "...", "icon": "...", "order": 0}

5. **Override methods as needed:**
   - get_context_data() for custom context
   - get_success_url() for redirects after forms
   - has_permission() for custom auth logic

6. **Use check attribute for conditional visibility:**
   check = is_instance_of(SpecificSubclass)
   # or
   @staticmethod
   def check(request, obj):
       return obj.some_condition

7. **Templates follow hierarchy:**
   - Explicit: template_name = "my/template.html"
   - Auto-resolved: {app}/{model}/plugins/{plugin_name}.html
                  → {app}/plugins/{plugin_name}.html
                  → plugins/{plugin_name}.html
                  → plugins/base.html (fallback)
"""
