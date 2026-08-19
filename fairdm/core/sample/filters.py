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
from fairdm.core.vocabularies import FairDMSampleStatus


class SampleFilterMixin(django_filters.FilterSet):
    """Reusable base carrying the filters every Sample type inherits.

    A `django_filters.FilterSet` subclass, not a plain mixin: django-filter's
    metaclass only collects declared filters from the class body and from bases
    that carry `declared_filters`, which a plain Python class never does (D-008).
    `Meta` deliberately has no `model` - that is what lets this class exist
    without a concrete model to generate implicit filters from, the same shape
    `fairdm.core.filters.BaseListFilter` already uses for projects and datasets.
    Setting `model = Sample` here would make the metaclass generate a full,
    unused Sample filter set every time this class (or any subclass) is defined.

    `Meta.fields` stays as a convenience list a subclass's own `Meta` (which does
    carry a `model`) can extend, matching the existing usage in
    `fairdm_demo.filters.RockSampleFilter` and `WaterSampleFilter`.

    Usage:
        class MyCustomSampleFilter(SampleFilterMixin, django_filters.FilterSet):
            # Add custom filters here
            custom_field = django_filters.CharFilter(...)

            class Meta(SampleFilterMixin.Meta):
                model = MyCustomSample
                fields = SampleFilterMixin.Meta.fields + ['custom_field']
    """

    image = django_filters.BooleanFilter(
        method="filter_has_image",
        label=_("Has image"),
    )

    def filter_has_image(self, queryset, name, value):
        """Narrow to samples that do, or do not, carry an image.

        `image` is a `FileField`, and Django writes an empty string for "no
        file attached" even where `null=True` allows the column to hold NULL
        (`lookup_expr="isnull"`, the pattern `BaseListFilter.image` uses, never
        matches an unset `FileField` for this reason). Both representations
        count as "no image" here so the filter narrows correctly regardless of
        which one is on a given row.
        """
        if value is None:
            return queryset
        no_image = Q(image="") | Q(image__isnull=True)
        return queryset.exclude(no_image) if value else queryset.filter(no_image)

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
        """Field names a subclass's own `model`-bearing `Meta` may extend.

        No `model` here - see the class docstring. Without one, django-filter's
        `get_filters()` returns only `declared_filters` (`image`) for this class
        itself, and `fields` is inert until a subclass provides both.
        """

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

    # Status filter - `status` is a `ConceptField`, which stores the concept's name as a plain
    # string, not a foreign key (F7). A `ModelChoiceFilter` compares against `Concept` instances
    # and never matches, so this uses the same `ChoiceFilter`-over-vocabulary pattern
    # `ProjectFilter.status` (`fairdm/core/project/filters.py`) already uses.
    status = django_filters.ChoiceFilter(
        field_name="status",
        label=_("Status"),
        choices=FairDMSampleStatus().choices,
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

        # The dataset choices are set by `SampleFilterMixin.__init__` above.

        # Set polymorphic content type queryset
        self.filters["polymorphic_ctype"].queryset = ContentType.objects.filter(
            app_label__in=["fairdm_core", "fairdm_demo"]
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
