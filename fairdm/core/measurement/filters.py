"""Measurement filtering and search functionality (T013, T014 - Phase 7).

This module provides FilterSet classes for filtering Measurement models with support for:
- Dataset filtering
- Sample filtering
- Polymorphic type filtering
- Generic search across multiple fields
- Cross-relationship filtering (descriptions, dates)
- Reusable MeasurementFilterMixin for custom filters
"""

import django_filters
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from fairdm.core.measurement.models import Measurement


class MeasurementFilterMixin(django_filters.FilterSet):
    """Reusable base carrying the filters every Measurement type inherits.

    A `django_filters.FilterSet` subclass, not a plain mixin: django-filter's
    metaclass only collects declared filters from the class body and from bases
    that carry `declared_filters`, which a plain Python class never does (matches
    `SampleFilterMixin`, D-008). `Meta` deliberately has no `model` - that is what
    lets this class exist without a concrete model to generate implicit filters
    from. Setting `model = Measurement` here would make the metaclass generate a
    full, unused Measurement filter set every time this class (or any subclass)
    is defined.

    `Meta.fields` stays as a convenience list naming only actual model fields, that
    a subclass's own `Meta` (which does carry a `model`) can extend - the same shape
    `SampleFilterMixin.Meta` uses.

    Provides filters for:
    - dataset: Filter by parent dataset
    - sample: Filter by associated sample
    - polymorphic_ctype: Filter by measurement type (XRFMeasurement, ICP_MS_Measurement, etc.)
    - search: Generic search across name and uuid
    - description: Search in associated description text
    - date_after/date_before: Filter by associated date ranges

    See Also:
        - Developer Guide: docs/portal-development/measurements.md#step-4-custom-forms-and-filters
        - Filtering Documentation: docs/portal-development/forms-and-filters/

    Usage:
        class MyCustomMeasurementFilter(MeasurementFilterMixin, django_filters.FilterSet):
            # Add custom filters here
            custom_field = django_filters.CharFilter(...)

            class Meta(MeasurementFilterMixin.Meta):
                model = MyCustomMeasurement
                fields = MeasurementFilterMixin.Meta.fields + ['custom_field']
    """

    # Dataset filter - allow filtering by parent dataset
    dataset = django_filters.ModelChoiceFilter(
        field_name="dataset",
        label=_("Dataset"),
        queryset=None,  # Will be set dynamically in __init__
        empty_label=_("Any dataset"),
    )

    # Sample filter - allow filtering by associated sample
    sample = django_filters.ModelChoiceFilter(
        field_name="sample",
        label=_("Sample"),
        queryset=None,  # Will be set dynamically in __init__
        empty_label=_("Any sample"),
    )

    # Polymorphic type filter - filter by content type (measurement subclass)
    polymorphic_ctype = django_filters.ModelChoiceFilter(
        field_name="polymorphic_ctype",
        label=_("Measurement Type"),
        queryset=None,  # Will be set dynamically in __init__
        empty_label=_("Any type"),
    )

    # Generic search filter - searches across multiple fields
    search = django_filters.CharFilter(
        method="filter_search",
        label=_("Search"),
    )

    # Description filter - cross-relationship search
    description = django_filters.CharFilter(
        field_name="descriptions__value",
        lookup_expr="icontains",
        label=_("Description contains"),
    )

    # Date range filters - cross-relationship filtering
    date_after = django_filters.DateFilter(
        field_name="dates__value",
        lookup_expr="gte",
        label=_("Date after"),
    )

    date_before = django_filters.DateFilter(
        field_name="dates__value",
        lookup_expr="lte",
        label=_("Date before"),
    )

    def filter_search(self, queryset, name, value):
        """Filter by generic search across name and uuid fields.

        Args:
            queryset: The queryset to filter
            name: The filter name (unused)
            value: The search term

        Returns:
            Filtered queryset matching name or uuid
        """
        if not value:
            return queryset

        return queryset.filter(Q(name__icontains=value) | Q(uuid__icontains=value))

    def __init__(self, *args, **kwargs):
        """Initialise the filter and set the dynamic querysets.

        On the mixin rather than on `MeasurementFilter` alone, because this is the
        published extension point: a portal's own filter inherits this behaviour
        directly, including a "dataset" choice field whose choices come from the
        model's default manager. That manager is privacy-first, so without this a
        portal developer's filter would reject every private dataset - which is
        every dataset until someone publishes it.
        """
        super().__init__(*args, **kwargs)

        from django.contrib.contenttypes.models import ContentType

        from fairdm.core.models import Dataset
        from fairdm.core.sample.models import Sample

        if "dataset" in self.filters:
            self.filters["dataset"].queryset = Dataset.all_objects.all()

        if "sample" in self.filters:
            self.filters["sample"].queryset = Sample.objects.all()

        if "polymorphic_ctype" in self.filters:
            self.filters["polymorphic_ctype"].queryset = ContentType.objects.filter(
                app_label__in=["fairdm_core", "fairdm_demo"]
            )

    class Meta:
        """Field names a subclass's own `model`-bearing `Meta` may extend.

        No `model` here - see the class docstring.
        """

        fields = ["dataset", "sample", "polymorphic_ctype"]  # Only actual model fields


class MeasurementFilter(MeasurementFilterMixin, django_filters.FilterSet):
    """FilterSet for Measurement model with comprehensive filtering capabilities.

    Every filter is inherited from `MeasurementFilterMixin`; this class only
    supplies the concrete `model`.

    Example:
        # In a view
        filterset = MeasurementFilter(request.GET, queryset=Measurement.objects.all())
        if filterset.is_valid():
            filtered_measurements = filterset.qs
    """

    class Meta(MeasurementFilterMixin.Meta):
        """Meta configuration for MeasurementFilter."""

        model = Measurement
        fields = [*MeasurementFilterMixin.Meta.fields, "date_after", "date_before"]
