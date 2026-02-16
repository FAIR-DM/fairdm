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


class MeasurementFilterMixin:
    """Mixin providing common filter configurations for Measurement models.

    This mixin provides pre-configured filters for common Measurement fields that can be
    reused across custom measurement type filters. It includes:
    - Dataset filtering
    - Sample filtering
    - Polymorphic type filtering
    - Generic search (name, uuid)
    - Description content filtering (cross-relationship)
    - Date range filtering (cross-relationship)

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

    class Meta:
        """Meta configuration for MeasurementFilterMixin."""

        model = Measurement
        fields = ["dataset", "sample", "polymorphic_ctype"]  # Only actual model fields


class MeasurementFilter(MeasurementFilterMixin, django_filters.FilterSet):
    """FilterSet for Measurement model with comprehensive filtering capabilities.

    Provides filters for:
    - dataset: Filter by parent dataset
    - sample: Filter by associated sample
    - polymorphic_ctype: Filter by measurement type (XRFMeasurement, ICP_MS_Measurement, etc.)
    - search: Generic search across name and uuid
    - description: Search in associated description text
    - date_after/date_before: Filter by associated date ranges

    Example:
        # In a view
        filterset = MeasurementFilter(request.GET, queryset=Measurement.objects.all())
        if filterset.is_valid():
            filtered_measurements = filterset.qs
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

    def __init__(self, *args, **kwargs):
        """Initialize the filter and set dynamic querysets."""
        super().__init__(*args, **kwargs)
        # Import here to avoid circular imports and app registry issues
        from django.contrib.contenttypes.models import ContentType

        from fairdm.core.models import Dataset
        from fairdm.core.sample.models import Sample

        # Set dataset queryset
        self.filters["dataset"].queryset = Dataset.objects.all()

        # Set sample queryset
        self.filters["sample"].queryset = Sample.objects.all()

        # Set polymorphic content type queryset
        self.filters["polymorphic_ctype"].queryset = ContentType.objects.filter(
            app_label__in=["fairdm_core", "fairdm_demo"]
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

    class Meta(MeasurementFilterMixin.Meta):
        """Meta configuration for MeasurementFilter."""

        model = Measurement
        fields = [*MeasurementFilterMixin.Meta.fields, "date_after", "date_before"]
