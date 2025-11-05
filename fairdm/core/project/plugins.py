"""
Example plugins for ProjectDetailPage using the new view-centric system.
"""

from django.views.generic import TemplateView

from fairdm.plugins import ACTIONS, EXPLORE, MANAGEMENT, register_plugin

from .views import ProjectDetailPage


@register_plugin(ProjectDetailPage)
class Overview(TemplateView):
    """Basic project overview plugin."""

    category = EXPLORE
    menu_item = {"name": "Overview", "icon": "fa-solid fa-eye"}
    template_name = "project/plugins/overview.html"

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
class ProjectExportPlugin(TemplateView):
    """Export project data plugin."""

    category = ACTIONS
    menu_item = {"name": "Export", "icon": "fa-solid fa-download"}
    template_name = "project/plugins/export.html"

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
class ProjectSettingsPlugin(TemplateView):
    """Project settings management plugin."""

    category = MANAGEMENT
    menu_item = {"name": "Settings", "icon": "fa-solid fa-cog"}
    template_name = "project/plugins/settings.html"

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
