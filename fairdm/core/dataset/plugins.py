"""Registered pages for a dataset: overview, update, descriptions and delete."""

from collections import Counter

from django.conf import settings
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
from fairdm.core.measurement.models import Measurement
from fairdm.core.plugins import OverviewPlugin
from fairdm.core.related_records import DatasetDateInline, DatasetIdentifierInline
from fairdm.core.sample.models import Sample
from fairdm.utils.choices import Visibility
from fairdm.views import FairDMDeleteView, FairDMUpdateView

from .forms import DatasetForm
from .models import Dataset, DatasetDate, DatasetDescription

DATASET_SETTINGS = getattr(settings, "FAIRDM_DATASET", {})


def dataset_is_visible(request, obj):
    """Return whether the request's user may view a dataset.

    A public dataset is always visible, a private one only with ``dataset.view_dataset``.
    The plugin lookup reads through ``Dataset.all_objects`` so a private dataset's owner can
    still open it, which is why this check is needed. It is set as ``Overview.check``.

    Args:
        request: The current request.
        obj: The dataset, or ``None`` when no record has been resolved.

    Returns:
        True when the page may be shown.
    """
    if obj is None:
        return True
    if obj.visibility == Visibility.PUBLIC:
        return True
    return has_perm(request, "dataset.view_dataset", obj)


def visible_to_holder_of(permission):
    """Build a page check that also admits a holder of one record-level permission.

    Like :func:`dataset_is_visible`, except a private dataset also stays visible to a user
    holding ``permission`` on it. ``Update`` needs this because its own permission is
    ``change_dataset``, and creating a dataset grants the right to view it together with the
    right to edit it, so a record-level grant of the page's own permission is already evidence
    of legitimate access.

    Args:
        permission: The permission to accept at record level.

    Returns:
        A ``check(request, obj)`` callable.
    """

    def check(request, obj):
        if dataset_is_visible(request, obj):
            return True
        if obj is None:
            return False
        return request.user.has_perm(permission, obj)

    return check


class DatasetDatesInline(DatasetDateInline):
    """Row set for the dataset's dates, refusing a collection end before its start."""

    formset = date_ordering_formset(
        DatasetDate.START_TYPE,
        DatasetDate.END_TYPE,
        _(
            "The dataset's collection end date (%(end)s) cannot be before its "
            "collection start date (%(start)s)."
        ),
    )


class Update(PrivateRecordNotFoundMixin, Plugin, FairDMUpdateView):
    """Edit the dataset's attributes, identifiers and collection dates.

    An additional view of :class:`Overview`, so the navigation strip carries one entry for the
    whole collection.
    """

    url_path = "update"
    # An additional view inherits its owner's `check` but never its `permission`, so one that
    # states none is open to everyone, anonymous included (#279). Each page states both itself.
    permission = "dataset.change_dataset"
    check = staticmethod(visible_to_holder_of("dataset.change_dataset"))
    page_title = _("Update dataset")
    model = Dataset
    form_class = DatasetForm
    template_name = "dataset/plugins/update.html"
    inlines = [DatasetIdentifierInline, DatasetDatesInline]

    crud_views = {
        "list": "dataset-list",
        "update": "dataset:overview-update",
        "delete": "dataset:overview-delete",
    }
    show_list_action = True

    def show_delete_action(self, user):
        """Offer the delete link only to a user who holds the permission ``Delete`` requires."""
        return has_perm(self.request, Delete.permission, self.base_object)

    def get_form_kwargs(self):
        """Pass the request so the project field offers only the researcher's own projects."""
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_success_url(self):
        """Return to the dataset's own page."""
        return self.base_object.get_absolute_url()


class Descriptions(PrivateRecordNotFoundMixin, Plugin, MetadataMixin, MVPFormView):
    """Edit the dataset's descriptions, one area per concept in ``DatasetDescription.VOCABULARY``.

    An additional view of :class:`Overview`, built on :class:`VocabularyDescriptionsForm`.
    """

    permission = "dataset.change_dataset"
    check = staticmethod(dataset_is_visible)
    page_title = _("Descriptions")
    model = Dataset
    form_class = VocabularyDescriptionsForm
    # A plain form view derives no template from a model, so Django raises if this is unset.
    template_name = "form_view.html"

    def get_form_kwargs(self):
        """Pass the description model and the dataset to the form."""
        kwargs = super().get_form_kwargs()
        kwargs["related_model"] = DatasetDescription
        kwargs["instance"] = self.base_object
        return kwargs

    def form_valid(self, form):
        """Save the descriptions before redirecting."""
        form.save()
        return super().form_valid(form)

    def get_success_url(self):
        """Return to the dataset's own page."""
        return self.base_object.get_absolute_url()


class Delete(
    PrivateRecordNotFoundMixin, RecordOwnPageBackFallbackMixin, Plugin, FairDMDeleteView
):
    """Delete the dataset, confirmed by typing its name, with a preview of what goes with it.

    An additional view of :class:`Overview`. Unlike the project deletion page it has no
    protected-object guard, because a dataset's visibility never blocks its own deletion.
    """

    url_path = "delete"
    permission = "dataset.delete_dataset"
    check = staticmethod(visible_to_holder_of("dataset.delete_dataset"))
    page_title = _("Delete dataset")
    model = Dataset
    require_confirmation = True
    show_related_objects = True
    success_url = reverse_lazy("dataset-list")

    def get_confirmation_value(self):
        """Ask the user to type the dataset's name."""
        return self.base_object.name

    def _collect_deletion_data(self):
        """Cache the collector's walk for the life of the request."""
        # The walk loads every sample and measurement, and both `is_protected` and
        # `related_objects_summary` need it.
        if not hasattr(self, "deletion_data"):
            self.deletion_data = super()._collect_deletion_data()
        return self.deletion_data

    def get_context_data(self, **kwargs):
        """Replace the cascade preview with a count of samples and measurements.

        Everything else the collector reports is deleted with the dataset but never listed,
        as it would run to thousands of lines. A protected object keeps the shell's own preview,
        because ``protected_objects`` names what blocks deletion, not what it would remove.
        """
        context = super().get_context_data(**kwargs)
        if self.show_related_objects and not context["is_protected"]:
            context["related_objects"] = self.related_objects_summary()
        return context

    def related_objects_summary(self):
        """Count the samples and measurements a deletion removes, by concrete class.

        Returns:
            A list of ``(label, lines, 0)`` groups, one each for samples and measurements
            that have instances.
        """
        # Sample and Measurement are multi-table inherited, so `Collector` reports one row as two
        # entries. Skipping the bare base class avoids counting it twice.
        related_map, _protected = self._collect_deletion_data()
        sample_counts = Counter()
        measurement_counts = Counter()
        for instances in related_map.values():
            for instance in instances:
                concrete = type(instance)
                if concrete is Sample or concrete is Measurement:
                    continue
                if isinstance(instance, Sample):
                    sample_counts[concrete] += 1
                elif isinstance(instance, Measurement):
                    measurement_counts[concrete] += 1

        groups = []
        for label, counts in (
            (_("Samples"), sample_counts),
            (_("Measurements"), measurement_counts),
        ):
            if not counts:
                continue
            lines = [
                f"{concrete._meta.verbose_name_plural.title()} ({count})"
                for concrete, count in sorted(
                    counts.items(), key=lambda item: item[0]._meta.verbose_name_plural
                )
            ]
            groups.append((label, lines, 0))
        return groups


@plugins.register(Dataset, label=_("Overview"), icon="view", order=0)
class Overview(PrivateRecordNotFoundMixin, CRUDDirectoryMixin, OverviewPlugin):
    """The dataset's own page and the root of its collection.

    Its ``extra_views`` are :class:`Update`, :class:`Delete` and :class:`Descriptions`, and
    ``directory`` names the action links they need. The shared detail shell draws ``update``
    and ``delete`` as buttons, and ``dataset_detail.html`` draws ``descriptions`` itself.
    """

    url_path = None
    model = Dataset
    check = staticmethod(dataset_is_visible)
    template_name = "dataset/dataset_detail.html"
    extra_views = [Update, Delete, Descriptions]

    directory = ["update", "delete", "descriptions"]
    crud_views = {
        "update": "dataset:overview-update",
        "delete": "dataset:overview-delete",
        "descriptions": "dataset:overview-descriptions",
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
        """Add the dataset under the ``dataset`` key the template expects."""
        context = super().get_context_data(**kwargs)
        context["dataset"] = self.base_object
        return context
