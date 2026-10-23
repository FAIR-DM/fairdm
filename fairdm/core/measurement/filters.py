"""Filter sets for measurements, including the reusable ``MeasurementFilterMixin``."""

import django_filters
from django import forms
from django.utils.translation import gettext_lazy as _
from mvp.filters import SearchFilter
from partial_date import PartialDate

from fairdm.contrib.autocomplete.fields import (
    DatasetMultipleChoiceField,
    SampleMultipleChoiceField,
)
from fairdm.contrib.autocomplete.filters import RecordMultipleFilter
from fairdm.core.measurement.models import Measurement


class PartialDateFilterField(forms.CharField):
    """A ``CharField`` that validates its value as a year, a year and month, or a full date.

    It uses ``PartialDate``'s own parser rather than a second regex that could drift from it. A
    plain ``CharFilter`` let any string through, and the request failed later with an unhandled
    ``ValidationError`` when the queryset was evaluated.
    """

    def to_python(self, value):
        """Raise a ``ValidationError`` unless the value is ``YYYY``, ``YYYY-MM`` or ``YYYY-MM-DD``."""
        value = super().to_python(value)
        if value:
            PartialDate.parseDate(value)
        return value


class PartialDateFilter(django_filters.CharFilter):
    """A ``CharFilter`` whose form field validates a partial date string before it reaches the ORM."""

    field_class = PartialDateFilterField


class MeasurementFilterMixin(django_filters.FilterSet):
    """Reusable base carrying the filters every measurement type inherits.

    A ``FilterSet`` subclass rather than a plain mixin, because django-filter only collects
    declared filters from bases that carry ``declared_filters``. ``Meta`` deliberately has no
    ``model``, or the metaclass would generate a full, unused Measurement filter set whenever this
    class or a subclass is defined. ``Meta.fields`` names only actual model fields, which a
    subclass's own ``Meta`` can extend. See docs/developers/how-to/add-a-measurement-type.md.

    The dataset and sample filters are ``RecordMultipleFilter`` objects at public scope, so a
    visitor and a signed-in researcher are offered the same public records.

    Args:
        *args: Positional arguments passed to ``FilterSet``.
        **kwargs: Keyword arguments passed to ``FilterSet``.

    Attributes:
        dataset: Filter by parent dataset.
        sample: Filter by associated sample.
        polymorphic_ctype: Filter by measurement type.
        q: Search across name and uuid.
        description: Search in the description text.
        date_after: Filter to dates on or after a partial date.
        date_before: Filter to dates on or before a partial date.

    Example:
        ```python
        class MyMeasurementFilter(MeasurementFilterMixin, django_filters.FilterSet):
            class Meta(MeasurementFilterMixin.Meta):
                model = MyMeasurement
                fields = MeasurementFilterMixin.Meta.fields + ["date_after"]
        ```
    """

    dataset = RecordMultipleFilter(DatasetMultipleChoiceField, field_name="dataset")

    sample = RecordMultipleFilter(SampleMultipleChoiceField, field_name="sample")

    polymorphic_ctype = django_filters.ModelChoiceFilter(
        field_name="polymorphic_ctype",
        label=_("Measurement Type"),
        queryset=None,
        empty_label=_("Any type"),
    )

    q = SearchFilter(fields=["name", "uuid"], label=_("Search"))

    description = django_filters.CharFilter(
        field_name="descriptions__value",
        lookup_expr="icontains",
        label=_("Description contains"),
    )

    # `MeasurementDate.value` is a PartialDateField, which refuses the `datetime.date` a
    # `DateFilter` cleans to. `PartialDateFilter` validates against the model field's own parser.
    date_after = PartialDateFilter(
        field_name="dates__value",
        lookup_expr="gte",
        label=_("Date after"),
    )

    date_before = PartialDateFilter(
        field_name="dates__value",
        lookup_expr="lte",
        label=_("Date before"),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        from django.contrib.contenttypes.models import ContentType

        from fairdm.registry import registry

        if "polymorphic_ctype" in self.filters:
            registered_content_types = ContentType.objects.get_for_models(
                *registry.measurements
            ).values()
            self.filters["polymorphic_ctype"].queryset = ContentType.objects.filter(
                pk__in=[ct.pk for ct in registered_content_types]
            )

    class Meta:
        fields = ["dataset", "sample", "polymorphic_ctype"]


class MeasurementFilter(MeasurementFilterMixin, django_filters.FilterSet):
    """Filter set for ``Measurement``. Every filter comes from ``MeasurementFilterMixin``."""

    class Meta(MeasurementFilterMixin.Meta):
        model = Measurement
        fields = [*MeasurementFilterMixin.Meta.fields, "date_after", "date_before"]
