"""The pages that edit a record, written once and registered on every record type.

A project, a dataset, a sample and a measurement are edited through the same pages, each a plugin
registered on all four models. A sample or measurement type a portal registers gets them with no
further work. The pages are reached from the Manage menu, never from the tabs.
"""

import inspect
from typing import ClassVar

from django.forms import modelform_factory
from django.http import Http404
from django.utils.functional import Promise
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from meta.views import MetadataMixin
from mvp.views import MVPFormView

from fairdm.contrib.contributors.access import RecordAccess
from fairdm.contrib.plugins import Plugin
from fairdm.contrib.plugins import registry as plugin_registry
from fairdm.contrib.plugins import reverse as plugin_reverse
from fairdm.contrib.plugins.access import can_open, has_perm
from fairdm.core.dataset.forms import DatasetForm
from fairdm.core.dataset.models import Dataset, DatasetDescription
from fairdm.core.descriptions import VocabularyDescriptionsForm
from fairdm.core.measurement.models import Measurement, MeasurementDescription
from fairdm.core.project.forms import ProjectForm
from fairdm.core.project.models import Project, ProjectDescription
from fairdm.core.related_records import (
    DatasetDatesInline,
    DatasetIdentifierInline,
    MeasurementDateInline,
    MeasurementIdentifierInline,
    ProjectDatesInline,
    ProjectIdentifierInline,
    SampleDateInline,
    SampleIdentifierInline,
)
from fairdm.core.sample.models import Sample, SampleDescription
from fairdm.registry import registry
from fairdm.views import FairDMUpdateView


class RecordEditingPage(Plugin):
    """What every editing page shares: who may open it and where it leads afterwards.

    A page names its right in ``access``. The rule that reads it lives here, because one page is
    registered on four record types and a plugin has one ``permission`` attribute, not four.

    A request is answered in this order, on every request, so a save is refused as a view is:

    1. A viewer who may neither see the record nor holds the right on it gets a 404, as for a
       record that does not exist.
    2. A visitor who may see the record and may not use the page is sent to sign in.
    3. A signed-in person who may see the record and may not use the page gets a 403.

    Attributes:
        access: ``"change"`` for the pages that edit the record, ``"delete"`` for the one that
            removes it.
        menu_label: The page's entry in the Manage menu.
        menu_icon: The icon beside that entry.
    """

    OPEN: ClassVar[str] = "open"
    MISSING: ClassVar[str] = "missing"
    REFUSED: ClassVar[str] = "refused"

    PERMISSIONS: ClassVar[dict[str, dict[type, str]]] = {
        "change": {
            Project: "project.change_project",
            Dataset: "dataset.change_dataset",
            Sample: "sample.change_sample",
            Measurement: "measurement.change_measurement",
        },
        "delete": {
            Project: "project.delete_project",
            Dataset: "dataset.delete_dataset",
            Sample: "sample.delete_sample",
            Measurement: "measurement.delete_measurement",
        },
    }

    access: ClassVar[str] = "change"
    menu_label: ClassVar[str | Promise] = ""
    menu_icon: ClassVar[str] = "edit"

    @classmethod
    def permission_for(cls, record):
        """Name the permission that opens this page on a record.

        Args:
            record: A project, dataset, sample or measurement, of any registered type.

        Returns:
            The permission, with its app label.
        """
        return cls.PERMISSIONS[cls.access][RecordAccess(record).model]

    @staticmethod
    def overview_for(record):
        """Find the overview page of the record's kind, whose check decides who may see it.

        Resolved when asked, because the record modules import this module.

        Args:
            record: A project, dataset, sample or measurement, of any registered type.

        Returns:
            The overview plugin class.
        """
        from fairdm.core.dataset.plugins import Overview as DatasetOverview
        from fairdm.core.measurement.plugins import Overview as MeasurementOverview
        from fairdm.core.project.plugins import Overview as ProjectOverview
        from fairdm.core.sample.plugins import Overview as SampleOverview

        return {
            Project: ProjectOverview,
            Dataset: DatasetOverview,
            Sample: SampleOverview,
            Measurement: MeasurementOverview,
        }[RecordAccess(record).model]

    @classmethod
    def verdict(cls, request, record):
        """Decide what the viewer is told when they ask for this page on a record.

        Args:
            request: The current request.
            record: The record the page belongs to.

        Returns:
            ``OPEN`` when the page may run, ``MISSING`` when the viewer is to be told the record
            does not exist, ``REFUSED`` when they may see the record and may not use the page.
        """
        permission = cls.permission_for(record)
        may_see = can_open(cls.overview_for(record), request, record)
        if not may_see and not request.user.has_perm(permission, record):
            return cls.MISSING
        return cls.OPEN if has_perm(request, permission, record) else cls.REFUSED

    @classmethod
    def may_be_used_by(cls, request, record):
        """Say whether the page would open for the viewer, for the Manage menu.

        Args:
            request: The current request.
            record: The record the page belongs to.

        Returns:
            True when the page would run.
        """
        return cls.verdict(request, record) == cls.OPEN

    def dispatch(self, request, *args, **kwargs):
        """Answer 404 for a record the viewer may not see, before any other refusal."""
        record = self.base_object
        if record is None or self.verdict(request, record) == self.MISSING:
            kind = (
                RecordAccess(record).kind if record is not None else gettext("record")
            )
            raise Http404(
                gettext("No %(kind)s matches the given query.") % {"kind": kind}
            )
        return super().dispatch(request, *args, **kwargs)

    def has_permission(self):
        """Open the page for whoever ``verdict`` admits, so the save is checked as the view is."""
        return self.may_be_used_by(self.request, self.base_object)

    def get_object(self, queryset=None):
        """Edit the record the address names, so no page depends on a ``model`` attribute."""
        return self.base_object

    @property
    def record_name(self):
        """The record as a person names it: a measurement by its name, else its portal ID."""
        record = self.base_object
        if RecordAccess(record).model is Measurement:
            return record.name or str(record.uuid)
        return str(record)

    def get_success_message(self, cleaned_data):
        """Tell the person which record was saved."""
        return gettext("Saved %(name)s.") % {"name": self.record_name}

    def get_success_url(self):
        """Return to the record's own page."""
        return self.base_object.get_absolute_url()


@plugin_registry.register(Project, Dataset, Sample, Measurement, menu=False)
class EditDetails(RecordEditingPage, FairDMUpdateView):
    """Edit the record's own fields.

    A sample or measurement is edited with the form its registered type creates records with, less
    the fields that would move it to another dataset or sample. Dates and identifiers have pages
    of their own.
    """

    name = "edit"
    access = "change"
    menu_label = _("Edit details")
    menu_icon = "edit"
    page_title = _("Edit details")  # type: ignore[assignment]

    def get_form_class(self):
        """Choose the record's form by its kind, and by its registered type for a sample or measurement."""
        record = self.base_object
        core = RecordAccess(record).model
        if core is Project:
            return ProjectForm
        if core is Dataset:
            return DatasetForm
        model = type(record)
        if registry.is_registered(model):
            return registry.get_for_model(model).get_form_class()
        return modelform_factory(model, fields=("name", "image"))

    def get_form_kwargs(self):
        """Pass the request to a form whose constructor asks for it."""
        kwargs = super().get_form_kwargs()
        if "request" in inspect.signature(self.get_form_class()).parameters:
            kwargs["request"] = self.request
        return kwargs

    def get_form(self, form_class=None):
        """Drop the fields that move a record and the form tag and buttons the page draws itself."""
        form = super().get_form(form_class)
        if RecordAccess(self.base_object).model in {Sample, Measurement}:
            for name in ("dataset", "sample"):
                form.fields.pop(name, None)
        helper = getattr(form, "helper", None)
        if helper is not None:
            helper.form_tag = False
            helper.inputs = []
        return form


@plugin_registry.register(Project, Dataset, Sample, Measurement, menu=False)
class EditDescriptions(RecordEditingPage, MetadataMixin, MVPFormView):
    """Edit the record's descriptions, one area per type its vocabulary offers."""

    name = "descriptions"
    access = "change"
    menu_label = _("Edit descriptions")
    menu_icon = "description"
    page_title = _("Descriptions")  # type: ignore[assignment]
    form_class = VocabularyDescriptionsForm
    # A plain form view derives no template from a model, so Django raises if this is unset.
    template_name = "form_view.html"

    DESCRIPTIONS: ClassVar[dict[type, type]] = {
        Project: ProjectDescription,
        Dataset: DatasetDescription,
        Sample: SampleDescription,
        Measurement: MeasurementDescription,
    }

    def get_form_kwargs(self):
        """Pass the description model and the record to the form."""
        kwargs = super().get_form_kwargs()
        kwargs["related_model"] = self.DESCRIPTIONS[
            RecordAccess(self.base_object).model
        ]
        kwargs["instance"] = self.base_object
        return kwargs

    def form_valid(self, form):
        """Save the descriptions before redirecting."""
        form.save()
        return super().form_valid(form)


@plugin_registry.register(Project, Dataset, Sample, Measurement, menu=False)
class EditKeyDates(RecordEditingPage, FairDMUpdateView):
    """Edit the record's dates, one row per date type its vocabulary offers.

    A project and a dataset refuse an end that falls before the start.
    """

    name = "key-dates"
    access = "change"
    menu_label = _("Key dates")
    menu_icon = "date"
    page_title = _("Key dates")  # type: ignore[assignment]
    fields = ()

    INLINES: ClassVar[dict[type, list]] = {
        Project: [ProjectDatesInline],
        Dataset: [DatasetDatesInline],
        Sample: [SampleDateInline],
        Measurement: [MeasurementDateInline],
    }

    def get_inlines(self):
        """List the row set of this kind of record's dates."""
        return list(self.INLINES[RecordAccess(self.base_object).model])


@plugin_registry.register(Project, Dataset, Sample, Measurement, menu=False)
class EditIdentifiers(RecordEditingPage, FairDMUpdateView):
    """Edit the record's identifiers, one row per identifier type its vocabulary offers.

    The identifier the portal gives the record is its ``uuid``, which is not a row here.
    """

    name = "identifiers"
    access = "change"
    menu_label = _("Identifiers")
    menu_icon = "identifier"
    page_title = _("Identifiers")  # type: ignore[assignment]
    fields = ()

    INLINES: ClassVar[dict[type, list]] = {
        Project: [ProjectIdentifierInline],
        Dataset: [DatasetIdentifierInline],
        Sample: [SampleIdentifierInline],
        Measurement: [MeasurementIdentifierInline],
    }

    def get_inlines(self):
        """List the row set of this kind of record's identifiers."""
        return list(self.INLINES[RecordAccess(self.base_object).model])


MENU_PAGES = (EditDetails, EditDescriptions, EditKeyDates, EditIdentifiers)


def manage_menu(request, record):
    """List the editing pages the viewer may use on a record, in the order the menu shows them.

    Args:
        request: The current request.
        record: A project, dataset, sample or measurement, of any registered type.

    Returns:
        One entry per page the viewer may open, each with a ``label``, an ``icon`` and a ``url``.
    """
    return [
        {
            "label": page.menu_label,
            "icon": page.menu_icon,
            "url": plugin_reverse(record, page.get_name()),
        }
        for page in MENU_PAGES
        if page.may_be_used_by(request, record)
    ]
