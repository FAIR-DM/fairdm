"""Row-set declarations for the related records that carry a ``type``/``value`` pair.

Covers the models built on ``AbstractDate`` and ``AbstractIdentifier``
(``fairdm/core/abstract.py``), each edited as a row set on its record's key dates or identifiers page.
"""

from django.utils.translation import gettext_lazy as _
from mvp.views.inline import InlineFormSet

from .dataset.models import DatasetDate, DatasetIdentifier
from .forms import ConceptSelectField
from .formsets import date_ordering_formset
from .measurement.models import MeasurementDate, MeasurementIdentifier
from .project.models import ProjectDate, ProjectIdentifier
from .sample.models import SampleDate, SampleIdentifier


class RelatedRecordInline(InlineFormSet):
    """Row set with one row per existing ``type``/``value`` pair and no blank extras.

    A subclass names only its ``model``.
    """

    # A tuple, not a list: BaseInlineFormSet appends the parent key to a list in place,
    # leaking rows between the subclasses that share it.
    fields = ("type", "value")
    extra = 0

    def get_factory_kwargs(self):
        """Cap the row set at one row per type the collection offers, and draw types as a drop-down."""
        kwargs = super().get_factory_kwargs()
        kwargs["field_classes"] = {"type": ConceptSelectField}
        kwargs["max_num"] = len(self.model.get_type_concepts())
        kwargs["validate_max"] = True
        return kwargs


class ProjectDateInline(RelatedRecordInline):
    """Row set for a project's dates."""

    model = ProjectDate


class ProjectIdentifierInline(RelatedRecordInline):
    """Row set for a project's identifiers."""

    model = ProjectIdentifier


class DatasetDateInline(RelatedRecordInline):
    """Row set for a dataset's dates."""

    model = DatasetDate


class DatasetIdentifierInline(RelatedRecordInline):
    """Row set for a dataset's identifiers."""

    model = DatasetIdentifier


class SampleDateInline(RelatedRecordInline):
    """Row set for a sample's dates."""

    model = SampleDate


class SampleIdentifierInline(RelatedRecordInline):
    """Row set for a sample's identifiers."""

    model = SampleIdentifier


class MeasurementDateInline(RelatedRecordInline):
    """Row set for a measurement's dates."""

    model = MeasurementDate


class MeasurementIdentifierInline(RelatedRecordInline):
    """Row set for a measurement's identifiers."""

    model = MeasurementIdentifier


class ProjectDatesInline(ProjectDateInline):
    """Row set for the project's dates, refusing an end before its start."""

    formset = date_ordering_formset(
        ProjectDate.START_TYPE,
        ProjectDate.END_TYPE,
        _(
            "The project's end date (%(end)s) cannot be before its start date (%(start)s)."
        ),
    )


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
