"""
Example plugins for Project model using the new model-centric system.
"""

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from meta.views import MetadataMixin
from mvp.views import MVPFormView
from mvp.views.inline import InlinesMixin

from fairdm import plugins
from fairdm.contrib.plugins import Plugin
from fairdm.contrib.plugins.access import has_perm
from fairdm.core.descriptions import VocabularyDescriptionsForm
from fairdm.core.formsets import date_ordering_formset
from fairdm.core.plugins import OverviewPlugin
from fairdm.core.related_records import ProjectDateInline, ProjectIdentifierInline
from fairdm.utils.choices import Visibility
from fairdm.views import FairDMDeleteView, FairDMTemplateView, FairDMUpdateView

from ..dataset.views import DatasetListView
from .forms import ProjectForm
from .models import Project, ProjectDate, ProjectDescription, PublicDatasetsProtect


def project_is_visible(request, obj):
    """Whether ``request``'s user may view ``obj`` — a public project always, a private one only
    with ``project.view_project``.

    A registered page resolves its record through machinery that deliberately reads past
    filtered managers (``fairdm.contrib.plugins.base.Plugin.get_base_object``), on the assumption
    the page gates itself. ``Project`` has no privacy-filtered default manager either, so without
    this check a private project would be readable by anyone holding its address (013 plan P1).
    Set as :class:`Overview`'s ``check`` rather than reimplemented per page: an additional view
    inherits its owner's ``check``, so :class:`Attributes` and :class:`Delete` are covered too.
    """
    if obj is None:
        return True
    if obj.visibility == Visibility.PUBLIC:
        return True
    return has_perm(request, "project.view_project", obj)


class ProjectDatesInline(ProjectDateInline):
    """The project's own dates, ordered ``Start`` before ``End`` (013 plan P3). The rule is
    parameterised on :attr:`ProjectDate.START_TYPE`/``END_TYPE`` rather than the literals, and
    stated here rather than in ``related_records.py`` because it is this page's own choice of
    which shared declaration to combine with which shared rule — a dataset's dates page pairs
    the same base with its own, differently-typed pair (plan P6)."""

    formset = date_ordering_formset(
        ProjectDate.START_TYPE,
        ProjectDate.END_TYPE,
        _(
            "The project's end date (%(end)s) cannot be before its start date (%(start)s)."
        ),
    )


class Attributes(Plugin, InlinesMixin, FairDMUpdateView):
    """The project's own attributes: name, status, visibility, owner, plus its identifiers and
    dates. An additional view belonging to :class:`Overview` rather than a registration of its
    own, so the navigation strip carries one entry for the whole collection (013 plan P1).

    Supersedes the standalone ``project-update`` route and ``ProjectConfigure``, which duplicated
    part of the same surface with its own, separate navigation entry.
    """

    url_path = "attributes"
    # An additional view inherits its owner's `check` but never its `permission`
    # (fairdm/contrib/plugins/access.py `can_open`), so one that states none is open to
    # everyone, anonymous included (issue #279). Every page here writes its own.
    permission = "project.change_project"
    page_title = _("Attributes")
    model = Project
    form_class = ProjectForm
    inlines = [ProjectIdentifierInline, ProjectDatesInline]

    def get_success_url(self):
        return self.base_object.get_absolute_url()


class Delete(Plugin, FairDMDeleteView):
    """The project's own deletion page, confirmed by typing its name.

    An additional view belonging to :class:`Overview`, per :class:`Attributes` above. Supersedes
    the standalone ``project-delete`` route.
    """

    url_path = "delete"
    permission = "project.delete_project"
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
    check = staticmethod(project_is_visible)
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


@plugins.register(Project, label=_("Descriptions"), icon="description", order=300)
class Descriptions(Plugin, MetadataMixin, MVPFormView):
    """The project's own descriptions: one editable area per concept in
    ``ProjectDescription.VOCABULARY``, generated by :class:`VocabularyDescriptionsForm`.

    A registration of its own rather than an additional view, matching Dataset and Sample (013
    plan P2) — unlike :class:`Attributes` and :class:`Delete`, whose owner is :class:`Overview`.
    The generic ``fairdm.contrib.generic.plugins.DescriptionsPlugin`` is neither used nor
    repaired here: it offers add/remove rows rather than the fixed set of labelled areas this
    page requires, and it is broken where it is registered (issue #280).
    """

    permission = "project.change_project"
    page_title = _("Descriptions")
    model = Project
    form_class = VocabularyDescriptionsForm
    # Set explicitly even though it is also the inherited fallback. A plain form view derives no
    # template from a model the way Attributes' update view does, so leaving template_name unset
    # makes Django raise before the fallback is ever reached.
    template_name = "form_view.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["related_model"] = ProjectDescription
        kwargs["instance"] = self.base_object
        return kwargs

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_success_url(self):
        return self.base_object.get_absolute_url()
