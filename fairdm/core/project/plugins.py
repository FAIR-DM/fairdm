"""
Example plugins for ProjectDetailPage using the new view-centric system.
"""

from django.views.generic import TemplateView

from fairdm.core.plugins import (
    OverviewPlugin,
)
from fairdm.plugins import ACTIONS, FairDMPlugin, PluginMenuItem, register_plugin

from .views import ProjectDetailPage


@register_plugin(ProjectDetailPage)
class Overview(OverviewPlugin):
    """Basic project overview plugin."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.base_object  # type: ignore[attr-defined]

        context.update(
            {
                "project": project,
                "dataset_count": (getattr(project, "datasets", None) and project.datasets.count()) or 0,
            }
        )

        return context


@register_plugin(ProjectDetailPage)
class Export(FairDMPlugin, TemplateView):
    """Export project data plugin."""

    category = ACTIONS
    menu_item = PluginMenuItem(name="Export", icon="download")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.base_object  # type: ignore[attr-defined]

        context.update(
            {
                "project": project,
                "export_formats": ["JSON", "CSV", "XML"],
            }
        )

        return context


@register_plugin(ProjectDetailPage)
class Settings(FairDMPlugin, TemplateView):
    """Project settings management plugin."""

    category = ACTIONS
    menu_item = PluginMenuItem(name="Settings", icon="gear")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.base_object  # type: ignore[attr-defined]

        context.update(
            {
                "project": project,
                "can_edit": self.request.user.has_perm("change_project", project),
            }
        )

        return context
