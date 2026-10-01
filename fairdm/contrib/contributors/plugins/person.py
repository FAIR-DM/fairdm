"""Plugins for contributor pages: overview, projects, datasets, statistics and network."""

from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from django.utils.translation import gettext as _

from fairdm import plugins
from fairdm.contrib.plugins import Plugin
from fairdm.core.dataset.views import DatasetListView
from fairdm.core.plugins import OverviewPlugin
from fairdm.core.project.views import ProjectListView
from fairdm.views.base import FairDMTemplateView

from ..models import Contributor
from .overview import ContributorOverviewMixin


@plugins.register(Contributor, label=_("Overview"), icon="overview", order=0)
class Overview(ContributorOverviewMixin, OverviewPlugin):
    """The overview page of a person or an organization."""

    url_path = None

    def get_template_names(self):
        """Draw the person or the organization page."""
        if self.base_object.is_organization:
            return ["contributors/overview/organization.html"]
        return ["contributors/overview/person.html"]

    def get_context_data(self, **kwargs):
        """Add everything the person or organization page draws."""
        context = super().get_context_data(**kwargs)
        if self.base_object.is_organization:
            context.update(self.get_organization_context())
        else:
            context.update(self.get_person_context())
        return context


@plugins.register(Contributor, label=_("Projects"), icon="project", order=100)
class ContributorProjects(Plugin, ProjectListView):
    """List the projects a contributor is credited on."""

    page_title = _("Projects")

    def get_queryset(self, *args, **kwargs):
        """Limit to this contributor's projects."""
        return self.base_object.projects.all()

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
        return self.base_object.datasets.all()

    def get_page_title(self):
        """Title the page "My Datasets" on the user's own profile."""
        if self.request.user == self.base_object:
            return _("My Datasets")
        return super().get_page_title()


@plugins.register(Contributor, label=_("Statistics"), icon="statistics", order=300)
class Statistics(Plugin, FairDMTemplateView):
    """Show the contributor's contribution counts."""

    page_title = _("Statistics")

    def get_context_data(self, **kwargs):
        """Add the total number of contributions and the counts by type."""
        context = super().get_context_data(**kwargs)

        contributions_by_type = {}
        for entry in self.base_object.contributions.values("content_type").annotate(
            count=Count("id")
        ):
            content_type = ContentType.objects.get(pk=entry["content_type"])
            model_class = content_type.model_class()
            if model_class:
                contributions_by_type[model_class._meta.verbose_name_plural] = entry[
                    "count"
                ]

        context.update(
            {
                "total_contributions": self.base_object.contributions.count(),
                "contributions_by_type": contributions_by_type,
            }
        )

        return context


@plugins.register(Contributor, label=_("Network"), icon="people", order=400)
class Network(Plugin, FairDMTemplateView):
    """Show the contributor's frequent collaborators."""

    page_title = _("Network")
    model = Contributor
