"""
Example plugins for Project model using the new model-centric system.
"""

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from fairdm import plugins
from fairdm.contrib.generic.plugins import (
    DescriptionsPlugin,
    KeyDatesPlugin,
    KeywordsPlugin,
)
from fairdm.contrib.plugins import Plugin
from fairdm.core.plugins import OverviewPlugin
from fairdm.views import FairDMDeleteView, FairDMTemplateView, FairDMUpdateView

from ..dataset.views import DatasetListView
from .forms import ProjectForm
from .models import Project, ProjectDate, ProjectDescription, PublicDatasetsProtect


class Attributes(Plugin, FairDMUpdateView):
    """The project's own attributes: name, status, visibility, owner, plus its identifiers and
    dates. An additional view belonging to :class:`Overview` rather than a registration of its
    own, so the navigation strip carries one entry for the whole collection (013 plan P1).

    Supersedes the standalone ``project-update`` route and ``ProjectConfigure``, which duplicated
    part of the same surface with its own, separate navigation entry.
    """

    url_path = "attributes"
    page_title = _("Attributes")
    model = Project
    form_class = ProjectForm

    def get_success_url(self):
        return self.base_object.get_absolute_url()


class Delete(Plugin, FairDMDeleteView):
    """The project's own deletion page, confirmed by typing its name.

    An additional view belonging to :class:`Overview`, per :class:`Attributes` above. Supersedes
    the standalone ``project-delete`` route.
    """

    url_path = "delete"
    page_title = _("Delete project")
    model = Project
    require_confirmation = True
    success_url = reverse_lazy("project-list")

    def get_confirmation_value(self):
        return self.base_object.name

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except PublicDatasetsProtect as e:
            context = self.get_context_data(
                object=self.base_object, protected_datasets=e.datasets
            )
            return self.render_to_response(context)


@plugins.register(Project, label=_("Overview"), icon="view", order=0)
class Overview(OverviewPlugin):
    """The project's own page: its registered overview, and the root of its collection.

    Restores what the 2026-08-11 registry rework dropped by accident (013 plan P1): before that,
    ``Overview`` was one of nine registrations against ``Project`` and the project's own page
    carried a working navigation entry. Declaring no ``url_path`` of its own keeps it the root of
    the record's include, the same convention the contributor pages already use.
    """

    url_path = None
    template_name = "project/project_detail.html"
    extra_views = [Attributes, Delete]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # ``project_detail.html`` predates the registration and still refers to ``project``, the
        # name Django's ``SingleObjectMixin`` added automatically for the standalone detail view
        # this replaces. This view is a ``TemplateView`` and does not add it on its own.
        context["project"] = self.base_object
        return context


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
