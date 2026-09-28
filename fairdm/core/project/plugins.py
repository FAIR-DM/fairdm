"""Registered pages for a project: overview, update, descriptions, delete, datasets and export."""

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from meta.views import MetadataMixin
from mvp.views import MVPFormView
from mvp.views.detail import CRUDDirectoryMixin

from fairdm import plugins
from fairdm.contrib.plugins import Plugin
from fairdm.contrib.plugins.access import has_perm
from fairdm.contrib.plugins.mixins import (
    PrivateRecordNotFoundMixin,
    RecordOwnPageBackFallbackMixin,
)
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
    """Return whether the request's user may view a project.

    A public project is always visible, a private one only with ``project.view_project``.
    A registered page resolves its record past filtered managers and relies on the page to gate
    itself, so without this check a private project would be readable by anyone holding its
    address. It is set as ``Overview.check``.

    An additional view does not inherit this rule (the owner is read from ``plugin_class``, which
    exists only on the view instance, while ``has_permission`` passes the class). ``Update``,
    ``Delete`` and ``Descriptions`` therefore each state a visibility rule of their own (#284).

    Args:
        request: The current request.
        obj: The project, or ``None`` when no record has been resolved.

    Returns:
        True when the page may be shown.
    """
    if obj is None:
        return True
    if obj.visibility == Visibility.PUBLIC:
        return True
    return has_perm(request, "project.view_project", obj)


def visible_to_holder_of(permission):
    """Build a page check that also admits a holder of one record-level permission.

    Like :func:`project_is_visible`, except a private project also stays visible to a user
    holding ``permission`` on it. ``Update`` and ``Delete`` need this because their own
    permissions are ``change_project`` and ``delete_project``, and creating a project grants the
    right to view it together with the right to edit it, so a record-level grant of the page's own
    permission is already evidence of legitimate access.

    A user holding ``permission`` only at the model level still finds no grant here and is
    refused, because ``has_perm`` with an object consults only the object-level backend.

    Args:
        permission: The permission to accept at record level.

    Returns:
        A ``check(request, obj)`` callable.
    """

    def check(request, obj):
        if project_is_visible(request, obj):
            return True
        if obj is None:
            return False
        return request.user.has_perm(permission, obj)

    return check


class ProjectDatesInline(ProjectDateInline):
    """Row set for the project's dates, refusing an end before its start."""

    formset = date_ordering_formset(
        ProjectDate.START_TYPE,
        ProjectDate.END_TYPE,
        _(
            "The project's end date (%(end)s) cannot be before its start date (%(start)s)."
        ),
    )


class Update(PrivateRecordNotFoundMixin, Plugin, FairDMUpdateView):
    """Edit the project's name, status, visibility, owner, identifiers and dates.

    An additional view of :class:`Overview`, so the navigation strip carries one entry for the
    whole collection.
    """

    url_path = "update"
    # An additional view inherits its owner's `check` but never its `permission`, so one that
    # states none is open to everyone, anonymous included (#279). Each page states both itself.
    permission = "project.change_project"
    check = staticmethod(visible_to_holder_of("project.change_project"))
    page_title = _("Update project")
    model = Project
    form_class = ProjectForm
    inlines = [ProjectIdentifierInline, ProjectDatesInline]

    crud_views = {
        "list": "project-list",
        "update": "project:overview-update",
        "delete": "project:overview-delete",
    }
    show_list_action = True

    def show_delete_action(self, user):
        """Offer the delete link only to a user who holds the permission ``Delete`` requires."""
        return has_perm(self.request, Delete.permission, self.base_object)

    def get_success_url(self):
        """Return to the project's own page."""
        return self.base_object.get_absolute_url()


class Delete(
    PrivateRecordNotFoundMixin, RecordOwnPageBackFallbackMixin, Plugin, FairDMDeleteView
):
    """Delete the project, confirmed by typing its name.

    An additional view of :class:`Overview`.
    """

    url_path = "delete"
    permission = "project.delete_project"
    check = staticmethod(visible_to_holder_of("project.delete_project"))
    page_title = _("Delete project")
    model = Project
    require_confirmation = True
    success_url = reverse_lazy("project-list")

    def get_confirmation_value(self):
        """Ask the user to type the project's name."""
        return self.base_object.name

    def get_context_data(self, **kwargs):
        """Report the project's public datasets as the objects protecting it from deletion."""
        # Set after `super()`, because passing these as keyword arguments would be overwritten.
        context = super().get_context_data(**kwargs)
        public_datasets = self.base_object.datasets.filter(visibility=Visibility.PUBLIC)
        if public_datasets.exists():
            context["is_protected"] = True
            context["protected_objects"] = list(public_datasets)
            # `cotton/form/index.html` renders any `form` in context, which would duplicate the
            # confirmation input the `is_protected` branch already withholds.
            context["form"] = None
        return context

    def form_valid(self, form):
        """Re-render the page when a public dataset blocks the deletion."""
        try:
            return super().form_valid(form)
        except PublicDatasetsProtect:
            return self.render_to_response(
                self.get_context_data(object=self.base_object)
            )


class Descriptions(PrivateRecordNotFoundMixin, Plugin, MetadataMixin, MVPFormView):
    """Edit the project's descriptions, one area per concept in ``ProjectDescription.VOCABULARY``.

    An additional view of :class:`Overview`, built on :class:`VocabularyDescriptionsForm`. The
    generic ``DescriptionsPlugin`` is not used because it offers add and remove rows rather than a
    fixed set of labelled areas, and it is broken where it is registered (#280).
    """

    permission = "project.change_project"
    # `change_project` is granted model-wide, so without this check a holder of the model-level
    # right could read and rewrite the descriptions of a private project.
    check = staticmethod(project_is_visible)
    page_title = _("Descriptions")
    model = Project
    form_class = VocabularyDescriptionsForm
    # A plain form view derives no template from a model, so Django raises if this is unset.
    template_name = "form_view.html"

    def get_form_kwargs(self):
        """Pass the description model and the project to the form."""
        kwargs = super().get_form_kwargs()
        kwargs["related_model"] = ProjectDescription
        kwargs["instance"] = self.base_object
        return kwargs

    def form_valid(self, form):
        """Save the descriptions before redirecting."""
        form.save()
        return super().form_valid(form)

    def get_success_url(self):
        """Return to the project's own page."""
        return self.base_object.get_absolute_url()


@plugins.register(Project, label=_("Overview"), icon="view", order=0)
class Overview(PrivateRecordNotFoundMixin, CRUDDirectoryMixin, OverviewPlugin):
    """The project's own page and the root of its collection.

    Its ``extra_views`` are :class:`Update`, :class:`Delete` and :class:`Descriptions`, and
    ``directory`` names the action links they need. The shared detail shell draws ``update`` and
    ``delete`` as buttons, and ``project_detail.html`` draws ``descriptions`` itself.

    ``PrivateRecordNotFoundMixin`` makes a private project answer a stranger with a 404, since a
    403 or a sign-in redirect would confirm the record exists.
    """

    url_path = None
    model = Project
    check = staticmethod(project_is_visible)
    template_name = "project/project_detail.html"
    extra_views = [Update, Delete, Descriptions]

    directory = ["update", "delete", "descriptions"]
    crud_views = {
        "update": "project:overview-update",
        "delete": "project:overview-delete",
        "descriptions": "project:overview-descriptions",
    }

    def show_update_action(self, user):
        """Show the edit action to a user who may open the update page."""
        return has_perm(self.request, Update.permission, self.base_object)

    def show_delete_action(self, user):
        """Show the delete action to a user who may open the delete page."""
        return has_perm(self.request, Delete.permission, self.base_object)

    def show_descriptions_action(self, user):
        """Show the descriptions action to a user who may open the descriptions page."""
        return has_perm(self.request, Descriptions.permission, self.base_object)

    def get_context_data(self, **kwargs):
        """Add the project under the ``project`` key the template expects."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.base_object
        return context


@plugins.register(Project, order=100)
class DatasetList(Plugin, DatasetListView):
    """List the datasets that belong to the project."""

    page_title = _("Datasets")

    def get_queryset(self, *args, **kwargs):
        """Limit to the project's datasets."""
        return self.base_object.datasets.all()

    def get_lookup_kwargs(self) -> dict:
        """Return no lookup kwargs, as the queryset is already scoped to the project."""
        return {}


@plugins.register(Project, label=_("Export"), order=200)
class ProjectExportView(Plugin, FairDMTemplateView):
    """Page for exporting the project's data."""

    page_title = _("Export Project Data")
    page_icon = "export"
