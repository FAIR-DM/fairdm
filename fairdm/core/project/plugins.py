"""
Example plugins for Project model using the new model-centric system.
"""

from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _
from meta.views import MetadataMixin
from mvp.views import MVPFormView
from mvp.views.detail import CRUDDirectoryMixin
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
    Set as :class:`Overview`'s ``check``, which is what guards the project's own page.

    It does **not** carry to :class:`Attributes` or :class:`Delete` on a real request, despite the
    inheritance ``can_open`` describes: the owner is read from ``plugin_class``, which ``get_urls``
    binds through ``as_view()`` and which therefore exists only on the view instance, while
    ``has_permission`` passes the class. Those two pages are guarded by their own ``permission``
    alone. Reported as issue #284; not repaired here because making the predicate apply to pages
    that already require ``change_project``/``delete_project`` is a decision about how editing
    rights and visibility compose, which belongs with the plugin access work in #279.
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

    # FR-045 — this page offers the deletion page. The shared form shell already carries the slot
    # and fills it from get_delete_url(); all this page supplies is where the three routes it
    # reverses actually live, since the interface layer's defaults name the standalone
    # `project-update`/`project-delete` routes this feature retires.
    crud_views = {
        "list": "project-list",
        "update": "project:overview-attributes",
        "delete": "project:overview-delete",
    }
    show_list_action = True

    def show_delete_action(self, user):
        """Offered on the right ``Delete`` itself requires, not on the one that opened this page:
        a user may hold ``change_project`` without ``delete_project``, and a link they cannot
        follow is worse than no link."""
        return has_perm(self.request, Delete.permission, self.base_object)

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

    def get_back_url(self) -> str:
        """The confirmation page's own "Go Back" falls back to the project itself rather than
        the project list (013 plan FR-044, US-5 T069/T070): ``MVPDeleteView``'s own fallback is
        ``resolve_crud_url("list")``, which ``Delete`` never shows (it carries no ``list``
        entry in its ``directory``), so the shell rendered the control as a destination-less
        button. From a project's own deletion page, "back" means back to the record being
        considered for deletion, not the collection everyone reaches it through. The ``?back``
        query-string override above this in the MRO is preserved unchanged.
        """
        candidate = self.request.GET.get("back")
        if candidate and url_has_allowed_host_and_scheme(
            url=candidate,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return candidate
        return self.base_object.get_absolute_url()

    def get_context_data(self, **kwargs):
        """Populate the shell's own ``is_protected``/``protected_objects`` contract with the
        project's public datasets, evaluated fresh on every call so the refusal holds whether
        the page has just been opened or a submission was just refused (013 plan P4).

        Runs after ``super().get_context_data()`` rather than passing these through keyword
        arguments, which :class:`FairDMDeleteView`'s own assignment would overwrite.
        """
        context = super().get_context_data(**kwargs)
        public_datasets = self.base_object.datasets.filter(visibility=Visibility.PUBLIC)
        if public_datasets.exists():
            context["is_protected"] = True
            context["protected_objects"] = list(public_datasets)
            # The shell's own confirmation field is withheld by `delete_view.html`'s
            # `is_protected` branch, but the raw form is rendered unconditionally by
            # `cotton/form/index.html` whenever a `form` is in context — a second,
            # duplicate confirmation input the shell's contract has no way to suppress.
            # Clearing it here is confined to this page's own context, not the shell.
            context["form"] = None
        return context

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except PublicDatasetsProtect:
            return self.render_to_response(
                self.get_context_data(object=self.base_object)
            )


@plugins.register(Project, label=_("Overview"), icon="view", order=0)
class Overview(CRUDDirectoryMixin, OverviewPlugin):
    """The project's own page: its registered overview, and the root of its collection.

    Restores what the 2026-08-11 registry rework dropped by accident (013 plan P1): before that,
    ``Overview`` was one of nine registrations against ``Project`` and the project's own page
    carried a working navigation entry. Declaring no ``url_path`` of its own keeps it the root of
    the record's include, the same convention the contributor pages already use.

    Mixes in the interface layer's own action-link mechanism (013 plan P5, US-5) rather than a
    hand-rolled one: ``directory`` names the two actions this page's extra views need an entry
    for (``update`` and ``delete``, drawn by the shared ``detail_view.html`` shell as its "Edit"
    and "Delete" buttons), and ``crud_views`` reverses each to :class:`Attributes`' and
    :class:`Delete`'s own registered names — the default ``{model_name}-update``/``-delete``
    shape resolves to the standalone routes this feature retires.
    """

    url_path = None
    model = Project
    check = staticmethod(project_is_visible)
    template_name = "project/project_detail.html"
    extra_views = [Attributes, Delete]

    directory = ["update", "delete"]
    crud_views = {
        "update": "project:overview-attributes",
        "delete": "project:overview-delete",
    }

    def show_update_action(self, user):
        return has_perm(self.request, Attributes.permission, self.base_object)

    def show_delete_action(self, user):
        return has_perm(self.request, Delete.permission, self.base_object)

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
    # Stated here as well as on Overview. A registration of its own takes no predicate from any
    # other page, and `change_project` alone is not a visibility rule: `has_perm` grants it
    # model-wide, so without this a holder of the model-level right reads and rewrites the
    # descriptions of a private project the project's own page refuses them.
    check = staticmethod(project_is_visible)
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
