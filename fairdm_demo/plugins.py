"""Example plugins demonstrating inheritance and reusability patterns.

This module shows how portal developers can:
1. Inherit from framework base classes (BaseOverviewPlugin, BaseEditPlugin, BaseDeletePlugin)
2. Customize behavior by overriding methods
3. Use polymorphic visibility checks
4. Register plugins for custom models

These examples serve as living documentation for plugin development patterns.
"""

from django.utils.translation import gettext_lazy as _

from fairdm import plugins
from fairdm.contrib.plugins import Plugin
from fairdm.core.plugins import BaseDeletePlugin, BaseEditPlugin, BaseOverviewPlugin
from fairdm.core.project.forms import ProjectForm
from fairdm.core.project.models import Project
from fairdm.core.sample.forms import SampleForm
from fairdm.core.sample.models import Sample

# =============================================================================
# Example 1: Basic Inheritance from Framework Base Classes
# =============================================================================


@plugins.register(Project)
class ProjectOverview(BaseOverviewPlugin):
    """Project overview inheriting standard behavior from framework.

    This demonstrates:
    - Inheriting menu configuration from BaseOverviewPlugin
    - Inheriting template resolution hierarchy
    - Adding custom context data via method override
    """

    # Menu configuration inherited from BaseOverviewPlugin
    # (label="Overview", icon="eye", order=0)

    def get_context_data(self, **kwargs):
        """Add project-specific context: datasets, samples, contributors."""
        context = super().get_context_data(**kwargs)

        # Add related objects to context
        context["datasets"] = self.object.datasets.all()
        context["samples"] = self.object.samples.all()
        context["contributors"] = self.object.contributors.all()

        return context


@plugins.register(Project)
class ProjectEdit(BaseEditPlugin):
    """Project edit form inheriting standard form handling.

    This demonstrates:
    - Setting form_class for edit functionality
    - Overriding menu configuration to customize appearance
    - Setting explicit permissions
    """

    form_class = ProjectForm

    # Customize menu (override default from BaseEditPlugin)
    menu = {"label": _("Edit Project"), "icon": "pencil-square", "order": 10}

    # Set explicit permission (required for editing projects)
    permission = "fairdm_demo.change_project"


@plugins.register(Project)
class ProjectDelete(BaseDeletePlugin):
    """Project deletion with confirmation.

    This demonstrates:
    - Inheriting deletion confirmation behavior
    - Customizing success URL after deletion
    - High order value to position tab at the end
    """

    # Menu inherited from BaseDeletePlugin, but reposition it
    menu = {"label": _("Delete"), "icon": "trash", "order": 1000}

    permission = "fairdm_demo.delete_project"

    def get_success_url(self):
        """Redirect to project list after deletion."""
        from django.urls import reverse

        return reverse("fairdm:project-list")


# =============================================================================
# Example 2: Custom Plugin Without Inheritance
# =============================================================================


@plugins.register(Sample)
class SampleOverview(Plugin):
    """Sample overview demonstrating custom plugin without base class.

    This shows that you can create plugins from scratch without inheriting
    from framework base classes if you need full control.
    """

    from django.views.generic import TemplateView

    # Must inherit from a Django CBV
    __bases__ = (Plugin, TemplateView)

    menu = {"label": _("Overview"), "icon": "eye", "order": 0}

    def get_context_data(self, **kwargs):
        """Add sample-specific context."""
        context = super().get_context_data(**kwargs)

        context["measurements"] = self.object.measurements.all()
        context["location"] = getattr(self.object, "location", None)

        return context


@plugins.register(Sample)
class SampleEdit(BaseEditPlugin):
    """Sample edit form."""

    form_class = SampleForm
    menu = {"label": _("Edit"), "icon": "pencil", "order": 10}
    permission = "fairdm_demo.change_sample"


# =============================================================================
# Example 3: Polymorphic Visibility with Check Functions
# =============================================================================


@plugins.register(Sample)
class LocationDetailsPlugin(Plugin):
    """Plugin that only appears for samples with locations.

    This demonstrates:
    - Using a custom check function for conditional visibility
    - The plugin tab only appears when the condition is met
    """

    from django.views.generic import TemplateView

    __bases__ = (Plugin, TemplateView)

    menu = {"label": _("Location Details"), "icon": "geo-alt", "order": 50}

    # Custom visibility check: only show if sample has a location
    @staticmethod
    def check(request, obj):
        """Only visible for samples with assigned locations."""
        return obj and hasattr(obj, "location") and obj.location is not None

    template_name = "fairdm_demo/plugins/location_details.html"

    def get_context_data(self, **kwargs):
        """Add location and coordinates to context."""
        context = super().get_context_data(**kwargs)

        if self.object.location:
            context["location"] = self.object.location
            context["coordinates"] = {
                "lat": self.object.location.latitude,
                "lon": self.object.location.longitude,
            }

        return context


# =============================================================================
# Example 4: Using is_instance_of for Polymorphic Models
# =============================================================================

# Note: This example assumes Sample has polymorphic subclasses like RockSample, WaterSample
# Uncomment if those models exist in your demo app:

# @plugins.register(Sample)
# class RockAnalysisPlugin(Plugin, TemplateView):
#     """Plugin only visible for RockSample instances.
#
#     This demonstrates:
#     - Using is_instance_of() helper for polymorphic filtering
#     - Plugin won't appear for WaterSample or other Sample subtypes
#     """
#
#     from .models import RockSample
#
#     check = is_instance_of(RockSample)  # Only visible for RockSample
#     menu = {"label": _("Rock Analysis"), "icon": "gem", "order": 30}
#     template_name = "fairdm_demo/plugins/rock_analysis.html"


# =============================================================================
# Example 5: Location Model Plugins (COMMENTED OUT - Location model not in demo)
# =============================================================================


# @plugins.register(Location)
# class LocationOverview(BaseOverviewPlugin):
#     """Location overview with map display."""
#
#     menu = {"label": _("Map"), "icon": "map", "order": 0}
#
#     def get_context_data(self, **kwargs):
#         """Add map configuration to context."""
#         context = super().get_context_data(**kwargs)
#
#         # Add coordinates for map rendering
#         context["map_center"] = {
#             "lat": self.object.latitude,
#             "lon": self.object.longitude,
#         }
#         context["zoom_level"] = 12
#
#         # Add samples at this location
#         context["samples"] = self.object.samples.all()
#
#         return context


# @plugins.register(Location)
# class LocationEdit(BaseEditPlugin):
#     """Location edit form."""
#
#     form_class = LocationForm
#     menu = {"label": _("Edit Location"), "icon": "pencil", "order": 10}
#     permission = "fairdm_demo.change_location"


# =============================================================================
# Notes for Portal Developers
# =============================================================================

# 1. **Import base classes from framework:**
#    from fairdm.core.plugins import BaseOverviewPlugin, BaseEditPlugin, BaseDeletePlugin
#
# 2. **Register plugins with decorator:**
#    @plugins.register(YourModel)
#
# 3. **Inherit from base + Django CBV:**
#    class YourPlugin(BaseOverviewPlugin):  # or (Plugin, TemplateView)
#
# 4. **Set menu configuration:**
#    menu = {"label": "...", "icon": "...", "order": 0}
#
# 5. **Override methods as needed:**
#    - get_context_data() for custom context
#    - get_success_url() for redirects after forms
#    - has_permission() for custom auth logic
#
# 6. **Use check attribute for conditional visibility:**
#    check = is_instance_of(SpecificSubclass)
#    # or
#    @staticmethod
#    def check(request, obj):
#        return obj.some_condition
#
# 7. **Templates follow hierarchy:**
#    - Explicit: template_name = "my/template.html"
#    - Auto-resolved: {app}/{model}/plugins/{plugin_name}.html
#                   → {app}/plugins/{plugin_name}.html
#                   → plugins/{plugin_name}.html
#                   → plugins/base.html (fallback)
