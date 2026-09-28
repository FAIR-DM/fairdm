"""Filter sets for the demo models, with examples of common filter patterns.

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

## Best Practices

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
uv run python manage.py makemigrations
uv run python manage.py migrate
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

import django_filters
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from demo.models import RockSample, WaterSample
from fairdm.core.sample.filters import SampleFilter, SampleFilterMixin

from .models import CustomSample


class CustomSampleFilter(SampleFilter):
    """Basic filter for CustomSample showing registry auto-generation pattern.

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


class RockSampleFilterExample(SampleFilter):
    """Example filter demonstrating generic search across multiple fields.

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

    rock_type = django_filters.CharFilter(
        field_name="rock_type",
        lookup_expr="icontains",
        label="Rock Type",
        help_text="Filter by rock type (e.g., granite, basalt)",
    )

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
        model = CustomSample
        fields = []

    def filter_search(self, queryset, name, value):
        """Search several fields at once.

        Matches the term case-insensitively against `name`, `uuid` and `char_field`.

        Args:
            queryset: The queryset to filter.
            name: The filter name (unused).
            value: The search term.

        Returns:
            The queryset restricted to rows matching the term in any field.
        """
        if not value:
            return queryset

        return queryset.filter(
            Q(name__icontains=value)
            | Q(uuid__icontains=value)
            | Q(char_field__icontains=value)
        ).distinct()


class XRFMeasurementFilterExample(SampleFilter):
    """Example filter for models that are filtered through related objects.

    It declares a generic search and uses `distinct()` so joins do not duplicate
    rows. The module docstring shows the cross-relationship filter to add for
    attributes of related objects (e.g., "find all samples with ABSTRACT
    descriptions").

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

    search = django_filters.CharFilter(
        method="filter_search",
        label="Search",
        help_text="Search across measurement name and UUID",
    )

    class Meta:
        model = CustomSample
        fields = []

    def filter_search(self, queryset, name, value):
        """Generic search across name and UUID."""
        if not value:
            return queryset

        return queryset.filter(
            Q(name__icontains=value) | Q(uuid__icontains=value)
        ).distinct()


class DatasetFilterExample(SampleFilter):
    """Example filter for complex models with many relationships.

    It declares a generic search. Add `ModelChoiceFilter` for foreign keys,
    `ChoiceFilter` for choice fields and `OrderingFilter` for sorting as the
    model needs them.
    """

    search = django_filters.CharFilter(
        method="filter_search",
        label="Search",
        help_text="Search across multiple fields",
    )

    class Meta:
        model = CustomSample
        fields = []

    def filter_search(self, queryset, name, value):
        """Generic search implementation."""
        if not value:
            return queryset

        return queryset.filter(
            Q(name__icontains=value) | Q(uuid__icontains=value)
        ).distinct()


class RockSampleFilter(SampleFilterMixin, django_filters.FilterSet):
    """FilterSet for RockSample model with geological filtering capabilities.

    Extends SampleFilterMixin to provide both common sample filters and
    rock-specific filters including:
    - All common filters from SampleFilterMixin (status, dataset, search, etc.)
    - rock_type: Filter by geological rock type (igneous, sedimentary, metamorphic)
    - mineral_content: Search in mineral composition text
    - grain_size: Filter by grain size category

    Attributes:
        rock_type: Choice filter on the rock type.
        mineral_content: Case-insensitive search of the mineral composition text.
        grain_size: Choice filter on the grain size category.

    Example:
        # In a view
        filterset = RockSampleFilter(
            request.GET,
            queryset=RockSample.objects.all()
        )
        filtered_rocks = filterset.qs
    """

    rock_type = django_filters.ChoiceFilter(
        field_name="rock_type",
        label=_("Rock Type"),
        choices=[
            ("", _("Any rock type")),
            ("igneous", _("Igneous")),
            ("sedimentary", _("Sedimentary")),
            ("metamorphic", _("Metamorphic")),
        ],
        empty_label=None,
    )

    mineral_content = django_filters.CharFilter(
        field_name="mineral_content",
        lookup_expr="icontains",
        label=_("Mineral Content"),
    )

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

    Attributes:
        water_source: Case-insensitive search of the water source.
        ph_min: Lower bound on the pH level.
        ph_max: Upper bound on the pH level.
        temp_min: Lower bound on the temperature in degrees Celsius.
        temp_max: Upper bound on the temperature in degrees Celsius.
        do_min: Lower bound on dissolved oxygen in mg/L.
        do_max: Upper bound on dissolved oxygen in mg/L.

    Example:
        # In a view
        filterset = WaterSampleFilter(
            request.GET,
            queryset=WaterSample.objects.all()
        )
        filtered_water = filterset.qs
    """

    water_source = django_filters.CharFilter(
        field_name="water_source",
        lookup_expr="icontains",
        label=_("Water Source"),
    )

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
