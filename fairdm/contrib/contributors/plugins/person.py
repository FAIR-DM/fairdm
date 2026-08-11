from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from django.utils.translation import gettext as _

from fairdm import plugins
from fairdm.contrib.plugins import Plugin
from fairdm.core.dataset.views import DatasetListView
from fairdm.core.plugins import OverviewPlugin
from fairdm.core.project.views import ProjectListView
from fairdm.views.base import FairDMTemplateView

from ..models import Contributor, Person


@plugins.register(Contributor, label=_("About"), icon="overview", order=0)
class Overview(OverviewPlugin):
    """Overview plugin for Contributor detail pages (Person and Organization)."""

    url_path = None

    def get_context_data(self, **kwargs):
        """Add contribution counts and ORCID identifier to the context."""
        context = super().get_context_data(**kwargs)
        context["contributions_by_type"] = self.get_contribution_counts()
        context["object"] = self.object

        # Add ORCID identifier if available (for Person objects)
        if isinstance(self.object, Person):
            orcid = self.object.identifiers.filter(type="ORCID").first()
            context["orcid_identifier"] = orcid

        return context

    def get_contribution_counts(self):
        """
        Calculate contribution counts by content type.

        Returns:
            dict: Mapping of model verbose names to contribution counts
                  (e.g., {"Projects": 5, "Datasets": 3})
        """
        contributions_by_type = self.object.contributions.values("content_type").annotate(count=Count("id"))
        result = {}
        for entry in contributions_by_type:
            content_type = ContentType.objects.get(pk=entry["content_type"])
            model_class = content_type.model_class()
            if model_class:
                verbose_name = model_class._meta.verbose_name_plural
                if verbose_name:
                    model_verbose_name = str(verbose_name).title()
                    result[model_verbose_name] = entry["count"]
        return result


@plugins.register(Contributor, label=_("Projects"), icon="project", order=100)
class ContributorProjects(Plugin, ProjectListView):
    """Projects plugin for Contributor model - shows all projects a contributor is associated with."""

    page_title = _("Projects")

    def get_queryset(self, *args, **kwargs):
        """Filter projects to only those associated with this contributor."""
        return self.object.projects.all()

    def get_page_title(self):
        if self.request.user == self.object:
            return _("My Projects")
        return super().get_page_title()


@plugins.register(Contributor, label=_("Datasets"), icon="dataset", order=200)
class ContributorDatasets(Plugin, DatasetListView):
    """Datasets plugin for Contributor model - shows all datasets a contributor is associated with."""

    def get_queryset(self, *args, **kwargs):
        """Filter datasets to only those associated with this contributor."""
        return self.object.datasets.all()

    def get_page_title(self):
        if self.request.user == self.object:
            return _("My Datasets")
        return super().get_page_title()


@plugins.register(Contributor, label=_("Statistics"), icon="statistics", order=300)
class Statistics(Plugin, FairDMTemplateView):
    """Plugin showing detailed contribution statistics."""

    page_title = _("Statistics")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get contribution counts by type
        contributions_by_type = {}
        for entry in self.object.contributions.values("content_type").annotate(count=Count("id")):
            content_type = ContentType.objects.get(pk=entry["content_type"])
            model_class = content_type.model_class()
            if model_class:
                contributions_by_type[model_class._meta.verbose_name_plural] = entry["count"]

        context.update(
            {
                "total_contributions": self.object.contributions.count(),
                "contributions_by_type": contributions_by_type,
            }
        )

        return context


@plugins.register(Contributor, label=_("Network"), icon="people", order=400)
class Network(Plugin, FairDMTemplateView):
    """Plugin showing frequent collaborators."""

    page_title = _("Network")
    model = Contributor
