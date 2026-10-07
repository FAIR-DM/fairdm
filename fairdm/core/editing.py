"""The pages that edit a record, written once and registered on every record type.

A project, a dataset, a sample and a measurement are edited through the same pages, each a plugin
registered on all four models. A sample or measurement type a portal registers gets them with no
further work. The pages are reached from the Manage menu, never from the tabs.
"""

import inspect
from collections import Counter
from typing import ClassVar

from django.forms import modelform_factory
from django.http import Http404
from django.urls import reverse
from django.utils.functional import Promise
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from meta.views import MetadataMixin
from mvp.views import MVPFormView

from fairdm.contrib.contributors.access import RecordAccess
from fairdm.contrib.generic.forms import KeywordForm
from fairdm.contrib.plugins import Plugin
from fairdm.contrib.plugins import registry as plugin_registry
from fairdm.contrib.plugins import reverse as plugin_reverse
from fairdm.contrib.plugins.access import can_open, has_perm
from fairdm.contrib.plugins.mixins import RecordOwnPageBackFallbackMixin
from fairdm.core.dataset.forms import DatasetForm
from fairdm.core.dataset.models import Dataset, DatasetDescription
from fairdm.core.descriptions import VocabularyDescriptionsForm
from fairdm.core.measurement.models import Measurement, MeasurementDescription
from fairdm.core.project.forms import ProjectForm
from fairdm.core.project.models import (
    Project,
    ProjectDescription,
    PublicDatasetsProtect,
)
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
from fairdm.utils.choices import Visibility
from fairdm.views import FairDMDeleteView, FairDMUpdateView


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

    @staticmethod
    def name_of(record):
        """Name a record as a person does: a measurement by its name, else its portal ID.

        Args:
            record: A project, dataset, sample or measurement, of any registered type.

        Returns:
            The name to show for the record.
        """
        if RecordAccess(record).model is Measurement:
            return record.name or str(record.uuid)
        return str(record)

    @property
    def record_name(self):
        """The page's record, named by :meth:`name_of`."""
        return self.name_of(self.base_object)

    @staticmethod
    def without_form_tag(form):
        """Strip a form's crispy helper of the tag and buttons, which the page draws itself.

        A form element nested in another ends the outer one early, leaving the page's Save
        buttons outside any form.

        Args:
            form: A form that may carry a crispy ``helper``.

        Returns:
            The same form.
        """
        helper = getattr(form, "helper", None)
        if helper is not None:
            helper.form_tag = False
            helper.inputs = []
        return form

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
        return self.without_form_tag(form)


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
class EditKeywords(RecordEditingPage, FairDMUpdateView):
    """Edit the record's keywords: one field per vocabulary the portal configures for its kind.

    A record type with no vocabulary configured gets the free-text keywords alone.
    """

    name = "keywords"
    access = "change"
    menu_label = _("Keywords")
    menu_icon = "keywords"
    page_title = _("Keywords")  # type: ignore[assignment]
    form_class = KeywordForm

    def get_form(self, form_class=None):
        """Drop the form tag and buttons the page draws itself."""
        return self.without_form_tag(super().get_form(form_class))


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


@plugin_registry.register(Project, Dataset, Sample, Measurement, menu=False)
class DeleteRecord(RecordEditingPage, RecordOwnPageBackFallbackMixin, FairDMDeleteView):
    """Delete the record, confirmed by typing its name, or its portal ID when it has no name.

    A project and a dataset say what goes with them as counts by record type, because listing
    every row would run to thousands of lines. A sample and a measurement list the rows that go
    with them. A record that cannot be deleted says what stops it and offers no way to confirm.
    The measurements that stop a deletion and that the viewer may not see are counted in the
    ``protected_unlisted`` context entry and never named.
    """

    name = "delete"
    access = "delete"
    menu_label = _("Delete")
    menu_icon = "delete"
    page_title = _("Delete")  # type: ignore[assignment]
    template_name = "editing/delete_record.html"
    require_confirmation = True
    show_related_objects = True

    def get_confirmation_value(self):
        """Ask the person to type the record's name."""
        return self.record_name

    def _collect_deletion_data(self):
        """Cache the collector's walk for the life of the request."""
        # The walk loads every row that goes with the record, and the protection check and the
        # counts both need it.
        if not hasattr(self, "deletion_data"):
            self.deletion_data = super()._collect_deletion_data()
        return self.deletion_data

    def get_success_message(self, cleaned_data):
        """Tell the person which record was deleted."""
        return gettext("Deleted %(name)s.") % {"name": self.record_name}

    def get_success_url(self):
        """Lead to the dataset a sample or measurement belonged to, else to a list page.

        Read before the record goes. A person who may not open the dataset is led to the dataset
        list instead.
        """
        record = self.base_object
        model = RecordAccess(record).model
        if model in {Sample, Measurement}:
            dataset = record.dataset
            if can_open(self.overview_for(dataset), self.request, dataset):
                return dataset.get_absolute_url()
            return reverse("dataset-list")
        return reverse("dataset-list" if model is Dataset else "project-list")

    def get_context_data(self, **kwargs):
        """Add what stops the deletion, named only as far as the viewer may see, and the counts."""
        context = super().get_context_data(**kwargs)
        record = self.base_object
        model = RecordAccess(record).model
        context["protected_unlisted"] = 0
        if model is Project:
            public = list(record.datasets.filter(visibility=Visibility.PUBLIC))
            if public:
                context["protected_objects"] = public
        if context["protected_objects"]:
            context["is_protected"] = True
            context["form"] = None
            listed, unlisted = self.split_protected(context["protected_objects"])
            context["protected_objects"] = listed
            context["protected_unlisted"] = unlisted
        elif model in {Project, Dataset}:
            context["related_objects"] = self.related_objects_summary()
        return context

    def split_protected(self, protected):
        """Separate what stops the deletion into what the viewer may see and a count of the rest.

        A measurement can sit in a dataset the viewer holds no level on, so it is named only when
        the viewer may see it, and then by :meth:`RecordEditingPage.name_of`.

        Args:
            protected: The objects that stop the deletion.

        Returns:
            The objects to name, and how many measurements were left out.
        """
        measurements = [item for item in protected if isinstance(item, Measurement)]
        others = [item for item in protected if not isinstance(item, Measurement)]
        seen = set(
            Measurement.objects.visible_to(self.request.user)
            .filter(pk__in=[item.pk for item in measurements])
            .values_list("pk", flat=True)
        )
        shown = [self.name_of(item) for item in measurements if item.pk in seen]
        return others + shown, len(measurements) - len(seen)

    def related_objects_summary(self):
        """Count what a project or dataset takes with it, by record type and concrete class.

        Returns:
            A list of ``(label, lines, 0)`` groups, one each for datasets, samples and
            measurements that have instances.
        """
        # Sample and Measurement are multi-table inherited, so the collector reports one row as
        # two entries. Skipping the bare base class avoids counting it twice.
        related_map, _protected = self._collect_deletion_data()
        counts = {Dataset: Counter(), Sample: Counter(), Measurement: Counter()}
        for instances in related_map.values():
            for instance in instances:
                concrete = type(instance)
                if concrete in {Sample, Measurement}:
                    continue
                for base, found in counts.items():
                    if isinstance(instance, base):
                        found[concrete] += 1
        groups = []
        for base, label in (
            (Dataset, _("Datasets")),
            (Sample, _("Samples")),
            (Measurement, _("Measurements")),
        ):
            if not counts[base]:
                continue
            lines = [
                f"{concrete._meta.verbose_name_plural.title()} ({count})"
                for concrete, count in sorted(
                    counts[base].items(),
                    key=lambda item: item[0]._meta.verbose_name_plural,
                )
            ]
            groups.append((label, lines, 0))
        return groups

    def form_valid(self, form):
        """Draw the page again in its protected state when a public dataset blocks the deletion."""
        try:
            return super().form_valid(form)
        except PublicDatasetsProtect:
            return self.render_to_response(
                self.get_context_data(object=self.base_object)
            )


MENU_PAGES = (
    EditDetails,
    EditDescriptions,
    EditKeywords,
    EditKeyDates,
    EditIdentifiers,
    DeleteRecord,
)


def manage_menu(request, record):
    """List the editing pages the viewer may use on a record, in the order the menu shows them.

    Args:
        request: The current request.
        record: A project, dataset, sample or measurement, of any registered type.

    Returns:
        One entry per page the viewer may open, each with a ``label``, an ``icon``, a ``url`` and
        ``destructive``, which marks the entry that deletes the record.
    """
    return [
        {
            "label": page.menu_label,
            "icon": page.menu_icon,
            "url": plugin_reverse(record, page.get_name()),
            "destructive": page.access == "delete",
        }
        for page in MENU_PAGES
        if page.may_be_used_by(request, record)
    ]
