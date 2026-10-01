"""Plugins for contributor pages: the projects and datasets a contributor is credited on."""

from django.utils.translation import gettext_lazy as _

from fairdm import plugins
from fairdm.contrib.plugins import Plugin
from fairdm.core.dataset.views import DatasetListView
from fairdm.core.project.views import ProjectListView

from ..models import Contributor


@plugins.register(Contributor, label=_("Projects"), icon="project", order=100)
class ContributorProjects(Plugin, ProjectListView):
    """List the projects a contributor is credited on."""

    page_title = _("Projects")

    def get_queryset(self, *args, **kwargs):
        """Limit to this contributor's projects."""
        return self.base_object.get_public_projects()

    def get_page_title(self):
        """Title the page "My Projects" on the user's own profile."""
        if self.request.user == self.base_object:
            return _("My Projects")
        return super().get_page_title()


@plugins.register(Contributor, label=_("Datasets"), icon="dataset", order=200)
class ContributorDatasets(Plugin, DatasetListView):
    """List the datasets a contributor is credited on."""

    page_title = _("Datasets")

    def get_queryset(self, *args, **kwargs):
        """Limit to this contributor's datasets."""
        return self.base_object.get_public_datasets()

    def get_page_title(self):
        """Title the page "My Datasets" on the user's own profile."""
        if self.request.user == self.base_object:
            return _("My Datasets")
        return super().get_page_title()
