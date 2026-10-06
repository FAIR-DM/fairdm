"""Filter sets for measurements, including the reusable ``MeasurementFilterMixin``."""

import django_filters
from django import forms
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from partial_date import PartialDate

from fairdm.contrib.contributors.choices import ContributionLevel
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
    subclass's own ``Meta`` can extend. See docs/portal-development/measurements.md.

    The dataset choices are the datasets the requesting user may change, or the privacy-first
    default manager's datasets when there is no authenticated user. ``Dataset.all_objects`` is
    never offered unconditionally, as it would list every private dataset.

    Args:
        *args: Positional arguments passed to ``FilterSet``.
        **kwargs: Keyword arguments passed to ``FilterSet``.

    Attributes:
        dataset: Filter by parent dataset.
        sample: Filter by associated sample.
        polymorphic_ctype: Filter by measurement type.
        search: Search across name and uuid.
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

    dataset = django_filters.ModelChoiceFilter(
        field_name="dataset",
        label=_("Dataset"),
        queryset=None,
        empty_label=_("Any dataset"),
    )

    sample = django_filters.ModelChoiceFilter(
        field_name="sample",
        label=_("Sample"),
        queryset=None,
        empty_label=_("Any sample"),
    )

    polymorphic_ctype = django_filters.ModelChoiceFilter(
        field_name="polymorphic_ctype",
        label=_("Measurement Type"),
        queryset=None,
        empty_label=_("Any type"),
    )

    search = django_filters.CharFilter(
        method="filter_search",
        label=_("Search"),
    )

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

    def filter_search(self, queryset, name, value):
        """Filter by a search term matching the name or uuid.

        Args:
            queryset: The queryset to filter.
            name: The filter name (unused).
            value: The search term.

        Returns:
            The queryset matching the name or uuid, unchanged when there is no term.
        """
        if not value:
            return queryset

        return queryset.filter(Q(name__icontains=value) | Q(uuid__icontains=value))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        from django.contrib.contenttypes.models import ContentType

        from fairdm.core.models import Dataset
        from fairdm.core.sample.models import Sample
        from fairdm.registry import registry

        if "dataset" in self.filters:
            if (
                self.request
                and hasattr(self.request, "user")
                and self.request.user is not None
                and self.request.user.is_authenticated
            ):
                self.filters["dataset"].queryset = Dataset.all_objects.accessible_to(
                    self.request.user, ContributionLevel.EDIT
                )
            else:
                self.filters["dataset"].queryset = Dataset.objects.all()

        if "sample" in self.filters:
            self.filters["sample"].queryset = Sample.objects.all()

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
