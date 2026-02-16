"""
FairDM Demo Portal - Filter Examples

This module demonstrates best practices for creating filters in FairDM portals,
including:

1. **Generic Search**: Search across multiple fields simultaneously
2. **Cross-Relationship Filters**: Filter by related model fields
3. **Choice Filters**: Dropdown filtering for categorical data
4. **Performance Optimization**: Database indexes for efficient queries
5. **Filter Combinations**: AND logic when multiple filters applied

These examples follow the patterns established in fairdm.core.dataset.filters
and can be adapted for custom Sample and Measurement models.

## Quick Reference

**Generic Search Filter**:
```python
import django_filters
from django.db.models import Q


class MyFilter(BaseListFilter):
    search = django_filters.CharFilter(
        method="filter_search",
        label="Search",
        help_text="Search across multiple fields",
    )

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(name__icontains=value) | Q(uuid__icontains=value)
        ).distinct()
```

**Cross-Relationship Filter**:
```python
description_type = django_filters.CharFilter(
    field_name="descriptions__description_type",
    lookup_expr="exact",
    label="Description Type",
    distinct=True,  # Prevent duplicate results
)
```

**Performance Considerations**:
- Add database indexes to frequently filtered fields (especially type fields)
- Use distinct=True on cross-relationship filters to prevent duplicates
- Test with large datasets (10k+ records) to ensure acceptable query times
- Expected query time: <10ms for most filter combinations

## Related Documentation

- **Filter Guide**: `docs/portal-development/filters/creating-filters.md`
- **Dataset Filter Reference**: `fairdm/core/dataset/filters.py`
- **Performance Guide**: `docs/portal-development/filters/performance.md`

## Integration with FairDM Registry

Filters work seamlessly with the FairDM registry system. You can specify
custom filter classes in your model configuration:

```python
from fairdm.registry import register, ModelConfiguration


@register
class MySampleConfig(ModelConfiguration):
    model = MySample
    filterset_class = MySampleFilter  # Custom filter class
    filter_fields = ["name", "location", "date"]
```

See `docs/portal-development/registry/configuration.md` for details.
"""

import django_filters
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from fairdm.core.sample.filters import SampleFilter, SampleFilterMixin
from fairdm_demo.models import RockSample, WaterSample

from .models import CustomSample

# ============================================================================
# Example 1: Basic Filter (Registry Auto-Generated Pattern)
# ============================================================================


class CustomSampleFilter(SampleFilter):
    """
    Basic filter for CustomSample showing registry auto-generation pattern.

    This is the simplest filter configuration - just specify the model and
    fields. The registry will auto-generate this if you don't provide a
    custom filterset_class.

    Usage in Registry:
        ```python
        @register
        class CustomSampleConfig(ModelConfiguration):
            model = CustomSample
            filter_fields = ["name", "char_field", "date_field"]
            # No filterset_class needed - registry auto-generates
        ```
    """

    class Meta:
        model = CustomSample
        fields = [
            "name",
            "char_field",
            "text_field",
            "integer_field",
            "big_integer_field",
            "positive_integer_field",
            "positive_small_integer_field",
            "small_integer_field",
            "boolean_field",
            "date_field",
            "date_time_field",
            "time_field",
            "decimal_field",
            "float_field",
        ]


# ============================================================================
# Example 2: Filter with Generic Search (Recommended Pattern)
# ============================================================================


# Commented out example - uncomment and adapt
# class RockSampleFilter(SampleFilter):
class RockSampleFilterExample(SampleFilter):
    """
    Example filter demonstrating generic search across multiple fields.

    This filter shows how to:
    1. Add a generic search field that searches multiple model fields
    2. Use Q objects for OR logic within the search
    3. Use distinct() to prevent duplicate results from joins
    4. Combine search with other filters

    Pattern Usage:
    Copy this pattern when you want users to be able to search across
    multiple fields at once without needing separate filter inputs for
    each field.

    Performance Notes:
    - Search uses icontains lookup (case-insensitive)
    - Index the fields being searched for better performance
    - Use distinct() when searching across related fields
    """

    search = django_filters.CharFilter(
        method="filter_search",
        label="Search",
        help_text="Search across sample name, UUID, location, and rock type",
    )

    # Standard filters
    rock_type = django_filters.CharFilter(
        field_name="rock_type",
        lookup_expr="icontains",
        label="Rock Type",
        help_text="Filter by rock type (e.g., granite, basalt)",
    )

    # Example date range filter
    collection_date_from = django_filters.DateFilter(
        field_name="collection_date",
        lookup_expr="gte",
        label="Collection Date From",
        help_text="Show samples collected on or after this date",
    )

    collection_date_to = django_filters.DateFilter(
        field_name="collection_date",
        lookup_expr="lte",
        label="Collection Date To",
        help_text="Show samples collected on or before this date",
    )

    class Meta:
        # model = RockSample
        model = CustomSample  # Replace with your model
        fields = []  # Leave empty when defining custom filters above

    def filter_search(self, queryset, name, value):
        """
        Generic search method across multiple fields.

        Searches the following fields (case-insensitive):
        - name: Sample name
        - uuid: Sample UUID
        - rock_type: Rock classification
        - location: Collection location (if exists)

        Args:
            queryset: The queryset to filter
            name: The filter name (unused)
            value: The search term

        Returns:
            Filtered queryset matching search term in any field
        """
        if not value:
            return queryset

        return queryset.filter(
            Q(name__icontains=value)
            | Q(uuid__icontains=value)
            | Q(char_field__icontains=value)  # Replace with actual field names
            # Q(rock_type__icontains=value) |
            # Q(location__icontains=value)
        ).distinct()


# ============================================================================
# Example 3: Filter with Cross-Relationship Filtering
# ============================================================================


# Commented out example - uncomment and adapt
# class XRFMeasurementFilter(BaseListFilter):
class XRFMeasurementFilterExample(SampleFilter):
    """
    Example filter demonstrating cross-relationship filtering.

    This filter shows how to:
    1. Filter by fields in related models (descriptions, dates, etc.)
    2. Use distinct=True to prevent duplicate results from joins
    3. Combine cross-relationship filters with standard filters
    4. Add database indexes for performance

    Pattern Usage:
    Use this pattern when you need to filter by attributes of related
    objects (e.g., "find all samples with ABSTRACT descriptions").

    Performance Considerations:
    - Add database indexes to the related model's type fields
    - Use select_related/prefetch_related in views for efficiency
    - Test with large datasets to ensure acceptable query times

    Database Indexes Required:
    ```python
    class XRFMeasurement(Measurement):
        class Meta:
            indexes = [
                models.Index(fields=["type"], name="xrf_type_idx"),
            ]
    ```
    """

    # Generic search
    search = django_filters.CharFilter(
        method="filter_search",
        label="Search",
        help_text="Search across measurement name and UUID",
    )

    # Cross-relationship filter - filter by description type
    # description_type = django_filters.CharFilter(
    #     field_name="descriptions__description_type",
    #     lookup_expr="exact",
    #     label="Description Type",
    #     help_text="Filter by description type (e.g., ABSTRACT, METHODS)",
    #     distinct=True  # IMPORTANT: Prevents duplicate results from join
    # )

    # Cross-relationship filter - filter by date type
    # date_type = django_filters.CharFilter(
    #     field_name="dates__date_type",
    #     lookup_expr="exact",
    #     label="Date Type",
    #     help_text="Filter by date type (e.g., COLLECTED, ANALYZED)",
    #     distinct=True  # IMPORTANT: Prevents duplicate results from join
    # )

    # Standard choice filter
    # analysis_type = django_filters.ChoiceFilter(
    #     field_name="analysis_type",
    #     choices=[
    #         ("XRF", "X-Ray Fluorescence"),
    #         ("ICP-MS", "ICP Mass Spectrometry"),
    #         ("SEM", "Scanning Electron Microscopy"),
    #     ],
    #     label="Analysis Type",
    #     help_text="Filter by type of analysis performed",
    #     empty_label="All types"
    # )

    class Meta:
        # model = XRFMeasurement
        model = CustomSample  # Replace with your model
        fields = []

    def filter_search(self, queryset, name, value):
        """Generic search across name and UUID."""
        if not value:
            return queryset

        return queryset.filter(Q(name__icontains=value) | Q(uuid__icontains=value)).distinct()


# ============================================================================
# Example 4: Filter with Multiple Choice Fields and Ordering
# ============================================================================


# Commented out example - uncomment and adapt
# class DatasetFilter(BaseListFilter):
class DatasetFilterExample(SampleFilter):
    """
    Example filter demonstrating advanced filtering patterns.

    This filter shows how to:
    1. Use ModelChoiceFilter for ForeignKey relationships
    2. Use ChoiceFilter for enum/choice fields
    3. Add ordering support
    4. Combine all filter types

    Pattern Usage:
    Use this pattern for complex models with many relationship types
    and categorical data that needs filtering.
    """

    search = django_filters.CharFilter(
        method="filter_search",
        label="Search",
        help_text="Search across multiple fields",
    )

    # Example: Filter by related project
    # project = django_filters.ModelChoiceFilter(
    #     queryset=Project.objects.all(),
    #     label="Project",
    #     help_text="Filter by associated project",
    #     empty_label="All projects"
    # )

    # Example: Filter by visibility level
    # visibility = django_filters.ChoiceFilter(
    #     field_name="visibility",
    #     choices=[
    #         ("PUBLIC", "Public"),
    #         ("INTERNAL", "Internal"),
    #         ("PRIVATE", "Private"),
    #     ],
    #     label="Visibility",
    #     help_text="Filter by visibility level",
    #     empty_label="All levels"
    # )

    # Example: Ordering support
    # ordering = django_filters.OrderingFilter(
    #     fields=(
    #         ("name", "name"),
    #         ("added", "added"),
    #         ("modified", "modified"),
    #     ),
    #     field_labels={
    #         "name": "Name",
    #         "added": "Date Added",
    #         "modified": "Last Modified",
    #     },
    #     label="Order by"
    # )

    class Meta:
        # model = Dataset
        model = CustomSample  # Replace with your model
        fields = []

    def filter_search(self, queryset, name, value):
        """Generic search implementation."""
        if not value:
            return queryset

        return queryset.filter(Q(name__icontains=value) | Q(uuid__icontains=value)).distinct()


# ============================================================================
# Best Practices Summary
# ============================================================================

"""
## Filter Best Practices for FairDM Portals

### 1. Generic Search Pattern
- Use a single search field that searches multiple model fields
- Use Q objects with OR logic for comprehensive search
- Use distinct() to prevent duplicate results
- Make search case-insensitive with icontains lookup
- Document which fields are searched in help_text

### 2. Cross-Relationship Filters
- Use field_name with double underscore for related fields
- Always add distinct=True to prevent duplicate results
- Add database indexes to frequently filtered type fields
- Document performance characteristics in docstrings
- Test with large datasets (10k+ records)

### 3. Choice Filters
- Use ChoiceFilter for enum/choice fields
- Use ModelChoiceFilter for ForeignKey fields
- Always provide empty_label for optional filters
- Add helpful help_text explaining the options
- Consider using Select2 widget for large choice lists

### 4. Date Range Filters
- Create separate _from and _to filters for ranges
- Use gte and lte lookups for inclusive ranges
- Use DateFilter widget with HTML5 date input
- Provide clear labels distinguishing from/to
- Consider DateFromToRangeFilter for combined widget

### 5. Performance Optimization
- Add database indexes to frequently filtered fields
- Use select_related() in views for ForeignKey filters
- Use prefetch_related() for ManyToMany filters
- Test query performance with Django Debug Toolbar
- Aim for <10ms query times on 10k+ records

### 6. Filter Combinations
- All filters use AND logic by default
- Each additional filter narrows the result set
- Document expected behavior in class docstring
- Test all common filter combinations
- Ensure filters work correctly when empty

### 7. User Experience
- Provide helpful help_text for each filter
- Use clear, descriptive labels
- Group related filters logically
- Consider default ordering
- Add placeholders where appropriate

### 8. Testing
After creating filters, test:
1. Each individual filter works correctly
2. Filters combine with AND logic
3. Empty filters don't error
4. Cross-relationship filters use distinct()
5. Query performance is acceptable
6. Form renders without errors
7. Help text is clear and accurate

See: `tests/unit/core/dataset/test_filter.py` for comprehensive filter tests.

### 9. Database Indexes for Performance
When using cross-relationship filters, add indexes to improve performance:

```python
class MyModel(models.Model):
    type = models.CharField(max_length=50)

    class Meta:
        indexes = [
            models.Index(fields=["type"], name="mymodel_type_idx"),
        ]
```

After adding indexes, run:
```bash
poetry run python manage.py makemigrations
poetry run python manage.py migrate
```

### 10. Registry Integration
The registry can auto-generate filters from filter_fields configuration:

```python
@register
class MySampleConfig(ModelConfiguration):
    model = MySample
    filter_fields = ["name", "date", "location"]
    # Registry creates basic filter with these fields
```

For advanced filters (search, cross-relationship), provide custom filterset_class:

```python
@register
class MySampleConfig(ModelConfiguration):
    model = MySample
    filterset_class = MySampleFilter  # Your custom filter
```
"""


# =============================================================================
# Sample Filters
# =============================================================================


class RockSampleFilter(SampleFilterMixin, django_filters.FilterSet):
    """FilterSet for RockSample model with geological filtering capabilities.

    Extends SampleFilterMixin to provide both common sample filters and
    rock-specific filters including:
    - All common filters from SampleFilterMixin (status, dataset, search, etc.)
    - rock_type: Filter by geological rock type (igneous, sedimentary, metamorphic)
    - mineral_content: Search in mineral composition text
    - grain_size: Filter by grain size category

    Example:
        # In a view
        filterset = RockSampleFilter(
            request.GET,
            queryset=RockSample.objects.all()
        )
        filtered_rocks = filterset.qs
    """

    # Rock type filter - choice field
    rock_type = django_filters.ChoiceFilter(
        field_name="rock_type",
        label=_("Rock Type"),
        choices=[
            ("", _("Any rock type")),
            ("igneous", _("Igneous")),
            ("sedimentary", _("Sedimentary")),
            ("metamorphic", _("Metamorphic")),
        ],
        empty_label=None,  # We provide custom empty option
    )

    # Mineral content search
    mineral_content = django_filters.CharFilter(
        field_name="mineral_content",
        lookup_expr="icontains",
        label=_("Mineral Content"),
    )

    # Grain size filter
    grain_size = django_filters.ChoiceFilter(
        field_name="grain_size",
        label=_("Grain Size"),
        choices=[
            ("", _("Any grain size")),
            ("fine", _("Fine")),
            ("medium", _("Medium")),
            ("coarse", _("Coarse")),
        ],
        empty_label=None,
    )

    class Meta(SampleFilterMixin.Meta):
        """Meta configuration for RockSampleFilter."""

        model = RockSample
        fields = [
            *SampleFilterMixin.Meta.fields,
            "rock_type",
            "mineral_content",
            "grain_size",
        ]


class WaterSampleFilter(SampleFilterMixin, django_filters.FilterSet):
    """FilterSet for WaterSample model with water quality filtering capabilities.

    Extends SampleFilterMixin to provide both common sample filters and
    water-specific filters including:
    - All common filters from SampleFilterMixin (status, dataset, search, etc.)
    - source_type: Filter by water source type (river, lake, groundwater, etc.)
    - ph_level: Range filter for pH values
    - temperature: Range filter for temperature measurements
    - dissolved_oxygen: Range filter for DO levels

    Example:
        # In a view
        filterset = WaterSampleFilter(
            request.GET,
            queryset=WaterSample.objects.all()
        )
        filtered_water = filterset.qs
    """

    # Source type filter (using actual field name: water_source)
    water_source = django_filters.CharFilter(
        field_name="water_source",
        lookup_expr="icontains",
        label=_("Water Source"),
    )

    # pH level range filters
    ph_min = django_filters.NumberFilter(
        field_name="ph_level",
        lookup_expr="gte",
        label=_("pH minimum"),
    )

    ph_max = django_filters.NumberFilter(
        field_name="ph_level",
        lookup_expr="lte",
        label=_("pH maximum"),
    )

    # Temperature range filters
    temp_min = django_filters.NumberFilter(
        field_name="temperature_celsius",
        lookup_expr="gte",
        label=_("Temperature min (°C)"),
    )

    temp_max = django_filters.NumberFilter(
        field_name="temperature_celsius",
        lookup_expr="lte",
        label=_("Temperature max (°C)"),
    )

    # Dissolved oxygen range filters
    do_min = django_filters.NumberFilter(
        field_name="dissolved_oxygen_mg_l",
        lookup_expr="gte",
        label=_("DO minimum (mg/L)"),
    )

    do_max = django_filters.NumberFilter(
        field_name="dissolved_oxygen_mg_l",
        lookup_expr="lte",
        label=_("DO maximum (mg/L)"),
    )

    class Meta(SampleFilterMixin.Meta):
        """Meta configuration for WaterSampleFilter."""

        model = WaterSample
        fields = [
            *SampleFilterMixin.Meta.fields,
            "water_source",
            "ph_min",
            "ph_max",
            "temp_min",
            "temp_max",
            "do_min",
            "do_max",
        ]
