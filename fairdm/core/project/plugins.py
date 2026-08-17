"""
Example plugins for Project model using the new model-centric system.
"""

from django.utils.translation import gettext_lazy as _

from fairdm import plugins
from fairdm.contrib.generic.plugins import (
    DescriptionsPlugin,
    KeyDatesPlugin,
    KeywordsPlugin,
)
from fairdm.contrib.plugins import Plugin
from fairdm.views import FairDMTemplateView, FairDMUpdateView

from ..dataset.views import DatasetListView
from .models import Project, ProjectDate, ProjectDescription


@plugins.register(Project, order=100)
class DatasetList(Plugin, DatasetListView):
    """Plugin for listing datasets associated with a project."""

    page_title = _("Datasets")

    def get_queryset(self, *args, **kwargs):
        """Filter datasets to only those belonging to this project."""
        return self.base_object.datasets.all()

    def get_lookup_kwargs(self) -> dict:
        return {}


@plugins.register(Project, label=_("Export"), order=200)
class ProjectExportView(Plugin, FairDMTemplateView):
    """Export project data plugin."""

    page_title = _("Export Project Data")
    page_icon = "export"


@plugins.register(Project, label=_("Configure"), icon="settings", order=300)
class ProjectConfigure(Plugin, FairDMUpdateView):
    """Project settings management plugin."""

    page_title = _("Configure project")
    permission = "project.change_project"
    model = Project
    fields = ["name", "visibility", "owner"]


class Descriptions(DescriptionsPlugin):
    """Plugin for managing project descriptions using inline formsets."""

    model = Project
    inline_model = ProjectDescription


class Keywords(KeywordsPlugin):
    """Plugin for managing project keywords."""

    model = Project


class KeyDates(KeyDatesPlugin):
    """Plugin for managing project key dates using inline formsets."""

    # InlineFormSetView configuration
    model = Project
    inline_model = ProjectDate
