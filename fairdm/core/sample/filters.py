"""Sample filtering and search functionality.

This module provides FilterSet classes for filtering Sample models with support for:
- Status filtering
- Dataset filtering
- Polymorphic type filtering
- Generic search across multiple fields
- Cross-relationship filtering (descriptions, dates)
- Reusable SampleFilterMixin for custom filters
"""

import django_filters
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from fairdm.core.sample.models import Sample


class SampleFilterMixin:
    """Mixin providing common filter configurations for Sample models.

    This mixin provides pre-configured filters for common Sample fields that can be
    reused across custom sample type filters. It includes:
    - Status filtering (multiple choice)
    - Dataset filtering
    - Polymorphic type filtering
    - Generic search (name, local_id, uuid)
    - Description content filtering (cross-relationship)
    - Date range filtering (cross-relationship)

    Usage:
        class MyCustomSampleFilter(SampleFilterMixin, django_filters.FilterSet):
            # Add custom filters here
            custom_field = django_filters.CharFilter(...)

            class Meta(SampleFilterMixin.Meta):
                model = MyCustomSample
                fields = SampleFilterMixin.Meta.fields + ['custom_field']
    """

    image = django_filters.BooleanFilter(
        field_name="images",
        lookup_expr="isnull",
        exclude=True,
        label=_("Has image"),
    )

    def __init__(self, *args, **kwargs):
        """Initialise the filter and widen the dataset choices.

        On the mixin rather than on `SampleFilter` alone, because this is the published
        extension point: a portal's own filter inherits `Meta.fields`, and with it a
        "dataset" choice field whose choices come from the model's default manager.
        That manager is privacy-first, so without this a portal developer's filter
        would reject every private dataset - which is every dataset until someone
        publishes it.
        """
        super().__init__(*args, **kwargs)

        from fairdm.core.models import Dataset

        if "dataset" in self.filters:
            self.filters["dataset"].queryset = Dataset.all_objects.all()

    class Meta:
        """Meta configuration for SampleFilterMixin."""

        model = Sample
        fields = ["status", "dataset", "polymorphic_ctype"]  # Only actual model fields


class SampleFilter(SampleFilterMixin, django_filters.FilterSet):
    """FilterSet for Sample model with comprehensive filtering capabilities.

    Provides filters for:
    - status: Filter by sample availability status
    - dataset: Filter by parent dataset
    - polymorphic_ctype: Filter by sample type (RockSample, WaterSample, etc.)
    - search: Generic search across name, local_id, and uuid
    - description: Search in associated description text
    - date_after/date_before: Filter by associated date ranges

    Example:
        # In a view
        filterset = SampleFilter(request.GET, queryset=Sample.objects.all())
        if filterset.is_valid():
            filtered_samples = filterset.qs
    """

    # Status filter - filter by concept relationship
    status = django_filters.ModelChoiceFilter(
        field_name="status",
        label=_("Status"),
        queryset=None,  # Will be set dynamically in __init__
        empty_label=_("Any status"),
    )

    # Dataset filter - allow filtering by parent dataset
    dataset = django_filters.ModelChoiceFilter(
        field_name="dataset",
        label=_("Dataset"),
        queryset=None,  # Will be set dynamically in __init__
        empty_label=_("Any dataset"),
    )

    # Polymorphic type filter - filter by content type (sample subclass)
    polymorphic_ctype = django_filters.ModelChoiceFilter(
        field_name="polymorphic_ctype",
        label=_("Sample Type"),
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
        field_name="descriptions__text",
        lookup_expr="icontains",
        label=_("Description contains"),
    )

    # Date range filters - cross-relationship filtering
    date_after = django_filters.DateFilter(
        field_name="dates__date",
        lookup_expr="gte",
        label=_("Date after"),
    )

    date_before = django_filters.DateFilter(
        field_name="dates__date",
        lookup_expr="lte",
        label=_("Date before"),
    )

    def __init__(self, *args, **kwargs):
        """Initialize the filter and set dynamic querysets."""
        super().__init__(*args, **kwargs)
        # Import here to avoid circular imports and app registry issues
        from django.contrib.contenttypes.models import ContentType
        from research_vocabs.models import Concept

        # The dataset choices are set by `SampleFilterMixin.__init__` above.

        # Set polymorphic content type queryset
        self.filters["polymorphic_ctype"].queryset = ContentType.objects.filter(
            app_label__in=["fairdm_core", "fairdm_demo"]
        )

        # Set status queryset (all Concepts from SampleStatus vocabulary)
        from fairdm.core.choices import SampleStatus

        self.filters["status"].queryset = Concept.objects.filter(
            vocabulary__name=SampleStatus._meta.name
        )

    def filter_search(self, queryset, name, value):
        """Filter by generic search across name, local_id, and uuid fields.

        Args:
            queryset: The queryset to filter
            name: The filter name (unused)
            value: The search term

        Returns:
            Filtered queryset matching name, local_id, or uuid
        """
        if not value:
            return queryset

        return queryset.filter(
            Q(name__icontains=value)
            | Q(local_id__icontains=value)
            | Q(uuid__icontains=value)
        )

    class Meta(SampleFilterMixin.Meta):
        """Meta configuration for SampleFilter."""

        model = Sample
        fields = [*SampleFilterMixin.Meta.fields, "date_after", "date_before"]
