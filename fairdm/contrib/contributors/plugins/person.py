"""The Projects and Datasets list tabs, each one plugin on every page that carries it.

Prototype for specification 023: Datasets is registered on a project, a person and an
organization, and Projects on a person and an organization.
"""

from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from fairdm import plugins
from fairdm.contrib.plugins import Plugin
from fairdm.contrib.plugins.mixins import PrivateRecordNotFoundMixin
from fairdm.core.dataset.models import Dataset
from fairdm.core.dataset.views import DatasetListView
from fairdm.core.project.models import Project
from fairdm.core.project.plugins import project_is_visible
from fairdm.core.project.views import ProjectListView
from fairdm.core.utils import get_objects_for_user
from fairdm.utils.choices import Visibility

from ..models import Contributor


def record_is_visible(request, obj):
    """Open the tab for whoever may open the record's overview."""
    if isinstance(obj, Project):
        return project_is_visible(request, obj)
    return True


@plugins.register(Contributor, label=_("Projects"), icon="project", order=10)
class Projects(Plugin, ProjectListView):
    """List the public projects a person or an organization is credited on."""

    page_title = _("Projects")

    def show_create_action(self, user):
        """Offer no way to create a project from a contributor's page."""
        return False

    def get_queryset(self, *args, **kwargs):
        """Limit to the contributor's public projects, for every viewer."""
        self.queryset = self.base_object.get_public_projects()
        return super().get_queryset()

    def get_lookup_kwargs(self) -> dict:
        """Return no lookup kwargs, as the queryset is already scoped to the record."""
        return {}


@plugins.register(Project, Contributor, label=_("Datasets"), icon="dataset", order=20)
class Datasets(PrivateRecordNotFoundMixin, Plugin, DatasetListView):
    """List a record's datasets: a project's own, or those a contributor is credited on."""

    page_title = _("Datasets")
    check = staticmethod(record_is_visible)

    def get_queryset(self, *args, **kwargs):
        """Limit to the record's datasets that this viewer may be shown."""
        record = self.base_object
        if not isinstance(record, Project):
            # A contributor's page names public datasets only, for every viewer.
            self.queryset = record.get_public_datasets()
            return super().get_queryset()
        datasets = Dataset.all_objects.filter(project=record)
        user = self.request.user
        allowed = Q(visibility=Visibility.PUBLIC)
        if user.is_authenticated:
            if user.has_perm("dataset.view_dataset"):
                self.queryset = datasets
                return super().get_queryset()
            mine = get_objects_for_user(
                user,
                ["dataset.view_dataset", "dataset.change_dataset"],
                datasets,
                any_perm=True,
                accept_global_perms=False,
            )
            allowed |= Q(pk__in=mine.values("pk"))
        self.queryset = datasets.filter(allowed)
        return super().get_queryset()

    def get_lookup_kwargs(self) -> dict:
        """Return no lookup kwargs, as the queryset is already scoped to the record."""
        return {}

    def show_create_action(self, user):
        """Offer adding a dataset only on a project, as the tab did before."""
        return isinstance(self.base_object, Project) and user.is_authenticated
