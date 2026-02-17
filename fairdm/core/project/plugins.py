"""
Example plugins for Project model using the new model-centric system.
"""

from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from fairdm import plugins
from fairdm.contrib.generic.plugins import (
    DescriptionsPlugin,
    KeyDatesPlugin,
    KeywordsPlugin,
)
from fairdm.contrib.plugins import Plugin
from fairdm.core.plugins import (
    BaseDeletePlugin,
    EditPlugin,
    OverviewPlugin,
)
from fairdm.utils.utils import user_guide

from ..dataset.views import DatasetListView
from .forms import ProjectForm
from .models import Project, ProjectDate, ProjectDescription

# ============ EXPLORE PLUGINS =================


@plugins.register(Project)
class Overview(OverviewPlugin):
    """Basic project overview plugin."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object

        context.update(
            {
                "project": project,
                "dataset_count": (getattr(project, "datasets", None) and project.datasets.count()) or 0,
            }
        )

        return context


@plugins.register(Project)
class Datasets(Plugin, DatasetListView):
    """Plugin for listing datasets associated with a project."""

    menu = {"label": _("Datasets"), "icon": "dataset", "order": 20}
    template_name = "plugins/list_view.html"

    def get_queryset(self, *args, **kwargs):
        """Filter datasets to only those belonging to this project."""
        return self.object.datasets.all()


# ============ ACTION PLUGINS =================


@plugins.register(Project)
class Export(Plugin, TemplateView):
    """Export project data plugin."""

    menu = {"label": _("Export"), "icon": "export", "order": 600}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object

        context.update(
            {
                "project": project,
                "export_formats": ["JSON", "CSV", "XML"],
            }
        )

        return context


@plugins.register(Project)
class Settings(Plugin, TemplateView):
    """Project settings management plugin."""

    menu = {"label": _("Settings"), "icon": "settings", "order": 700}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object

        context.update(
            {
                "project": project,
                "can_edit": self.request.user.has_perm("change_project", project),
            }
        )

        return context


# ============ MANAGEMENT PLUGINS =================


@plugins.register(Project)
class Edit(EditPlugin):
    """Plugin for editing basic project information."""

    title = _("Basic Information")
    model = Project
    form_class = ProjectForm
    fields = ["image", "name", "visibility", "status"]
    about = _(
        "Edit basic information about your project, including its name, visibility, and current status. "
        "These fields help others understand your project and control who can access it."
    )
    learn_more = user_guide("project/edit")


@plugins.register(Project)
class Delete(BaseDeletePlugin):
    """Plugin for deleting a project."""

    menu = {"label": _("Delete"), "icon": "delete", "order": 900}

    # Page configuration
    about = _(
        "Deleting a project is a permanent action that removes it from the system. "
        "Please see the documentation by clicking the link below to understand what happens when a project is deleted."
    )
    learn_more = user_guide("project/delete")


@plugins.register(Project)
class Descriptions(DescriptionsPlugin):
    """Plugin for managing project descriptions using inline formsets."""

    menu = {"label": _("Descriptions"), "icon": "description", "order": 510}
    about = _(
        "Provide key details about your project, including its name and key descriptions. "
        "This information is essential for conveying the project's purpose and scope, "
        "helping users quickly understand its relevance."
    )
    learn_more = user_guide("project/descriptions")
    model = Project
    inline_model = ProjectDescription


@plugins.register(Project)
class Keywords(KeywordsPlugin):
    """Plugin for managing project keywords."""

    menu = {"label": _("Keywords"), "icon": "keywords", "order": 520}

    # Page configuration
    about = _(
        "Keywords enhance your project's visibility in search engines and catalogs by summarizing its content. "
        "They help others quickly evaluate its relevance without reading the full documentation."
    )
    learn_more = user_guide("project/keywords")

    # UpdateView configuration
    model = Project


@plugins.register(Project)
class KeyDates(KeyDatesPlugin):
    """Plugin for managing project key dates using inline formsets."""

    menu = {"label": _("Key Dates"), "icon": "date", "order": 530}

    # Page configuration
    about = _(
        "Entering key dates helps track important milestones and timelines, supporting effective "
        "project management and giving others insight into the project's history and progress."
    )
    learn_more = user_guide("project/key-dates")

    # InlineFormSetView configuration
    model = Project
    inline_model = ProjectDate
