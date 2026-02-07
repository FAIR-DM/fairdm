# Contract: Dataset Filters

**Feature**: 004-core-datasets
**Purpose**: Define the public interface for DatasetFilter with generic search and cross-relationship filters
**Input**: [data-model.md](../data-model.md), [plan.md](../plan.md)

## DatasetFilter Interface

### Class Definition

```python
class DatasetFilter(BaseListFilter):
    """
    FilterSet for Dataset model with comprehensive filtering capabilities.

    Features:
        - Generic search across multiple fields (name, uuid, keywords)
        - Cross-relationship filters for descriptions and dates
        - Standard filters for project, license, visibility
        - AND logic for filter combinations (django-filter default)

    Performance:
        Cross-relationship filters require database indexes on:
        - DatasetDescription.description_type
        - DatasetDate.date_type

    Usage:
        # In views
        filterset = DatasetFilter(request.GET, queryset=Dataset.objects.all())
        filtered_datasets = filterset.qs

        # With tables
        table = DatasetTable(filterset.qs)
    """
```

### Filter Fields

```python
# Generic search field (matches across multiple fields)
search = django_filters.CharFilter(
    method='filter_search',
    label=_('Search'),
    help_text=_('Search by dataset name, UUID, or keywords'),
)

# Project filter
project = django_filters.ModelChoiceFilter(
    queryset=Project.objects.all(),
    label=_('Project'),
    help_text=_('Filter datasets by project'),
)

# License filter
license = django_filters.CharFilter(
    field_name='license__name',
    lookup_expr='iexact',
    label=_('License'),
    help_text=_('Filter by license name (exact match)'),
)

# Visibility filter
visibility = django_filters.ChoiceFilter(
    choices=Visibility.choices,
    label=_('Visibility'),
    help_text=_('Filter by access control level'),
)

# Cross-relationship filter for descriptions
description = django_filters.CharFilter(
    field_name='descriptions__description',
    lookup_expr='icontains',
    label=_('Description'),
    help_text=_('Search within dataset descriptions'),
    distinct=True,  # Prevent duplicate results from joins
)

# Cross-relationship filter for dates by type
date_type = django_filters.ChoiceFilter(
    field_name='dates__date_type',
    choices=[],  # Populated in __init__ from vocabulary
    label=_('Date Type'),
    help_text=_('Filter by specific date types (e.g., Collected, Published)'),
    distinct=True,
)
```

### Meta Configuration

```python
class Meta:
    model = Dataset
    fields = {
        'search': [],  # Custom method filter
        'project': ['exact'],
        'license': ['exact'],
        'visibility': ['exact'],
        'description': ['icontains'],
        'date_type': ['exact'],
    }
```

### Custom Filter Methods

```python
def filter_search(self, queryset, name, value):
    """
    Generic search across multiple fields.

    Args:
        queryset: Base QuerySet to filter
        name: Field name (ignored for generic search)
        value: Search term

    Returns:
        Filtered QuerySet matching search term in any searchable field

    Searchable Fields:
        - name: Dataset name (ILIKE match)
        - uuid: Short UUID (exact or partial match)
        - keywords__name: Tag names (ILIKE match)

    Performance Note:
        Uses ILIKE queries which can be slow on large datasets.
        Consider full-text search for production at scale.
    """
    if not value:
        return queryset

    return queryset.filter(
        Q(name__icontains=value) |
        Q(uuid__icontains=value) |
        Q(keywords__name__icontains=value)
    ).distinct()
```

### Constructor

```python
def __init__(self, *args, **kwargs):
    """
    Initialize filter with dynamic date type choices from vocabulary.

    Populates date_type filter choices from FairDMDates vocabulary
    to ensure filter matches available date types in the system.
    """
    super().__init__(*args, **kwargs)

    # Populate date_type choices from vocabulary
    date_types = FairDMDates.from_collection("Dataset")
    self.filters['date_type'].extra['choices'] = [
        (concept.label, concept.label) for concept in date_types
    ]
```

---

## Filter Combination Logic

### AND Logic (Default)

All filters are combined with AND logic by django-filter:

```python
# Multiple filters applied together
filtered = DatasetFilter({
    'project': project_id,
    'visibility': 'PUBLIC',
    'license': 'CC BY 4.0',
}, queryset=Dataset.objects.all())

# Equivalent SQL:
# WHERE project_id = ? AND visibility = ? AND license = ?
```

### OR Logic (Custom Method)

For OR combinations, use custom filter methods:

```python
def filter_multi_field_search(self, queryset, name, value):
    """Example OR filter."""
    return queryset.filter(
        Q(field1=value) | Q(field2=value) | Q(field3=value)
    )
```

---

## Cross-Relationship Filter Performance

### Database Indexes Required

```python
# In DatasetDescription model
class Meta:
    indexes = [
        models.Index(fields=['description_type']),
    ]

# In DatasetDate model
class Meta:
    indexes = [
        models.Index(fields=['date_type']),
    ]
```

### Query Performance

**Without indexes**:
```sql
-- Full table scan on descriptions
SELECT * FROM dataset
JOIN dataset_description ON ...
WHERE dataset_description.description ILIKE '%term%';
```

**With indexes**:
```sql
-- Index seek on date_type
SELECT * FROM dataset
JOIN dataset_date ON ...
WHERE dataset_date.date_type = 'Collected';
-- Uses index on date_type
```

### Performance Testing

```python
def test_cross_relationship_filter_performance(self):
    """Cross-relationship filters perform adequately with indexes."""
    # Create 1000 datasets with dates
    for i in range(1000):
        dataset = DatasetFactory()
        DatasetDateFactory(related=dataset, date_type='Collected')

    # Measure query time
    with assertQueryTime(max_seconds=1.0):
        filterset = DatasetFilter({
            'date_type': 'Collected'
        }, queryset=Dataset.objects.all())
        list(filterset.qs)  # Force query execution
```

---

## Testing Contracts

### Filter Field Tests

```python
def test_project_filter(self):
    """Project filter shows only datasets from selected project."""
    project1 = ProjectFactory()
    project2 = ProjectFactory()
    DatasetFactory(project=project1, count=3)
    DatasetFactory(project=project2, count=2)

    filterset = DatasetFilter({'project': project1.id})
    assert filterset.qs.count() == 3

def test_license_filter(self):
    """License filter matches by exact license name."""
    cc_by = License.objects.get(name="CC BY 4.0")
    mit = License.objects.get(name="MIT")
    DatasetFactory(license=cc_by, count=5)
    DatasetFactory(license=mit, count=3)

    filterset = DatasetFilter({'license': 'CC BY 4.0'})
    assert filterset.qs.count() == 5

def test_visibility_filter(self):
    """Visibility filter shows datasets with selected visibility."""
    DatasetFactory(visibility=Visibility.PUBLIC, count=4)
    DatasetFactory(visibility=Visibility.PRIVATE, count=2)

    filterset = DatasetFilter({'visibility': Visibility.PUBLIC})
    assert filterset.qs.count() == 4
```

### Generic Search Tests

```python
def test_generic_search_by_name(self):
    """Generic search matches dataset names."""
    DatasetFactory(name="Rock Collection Alpha")
    DatasetFactory(name="Water Samples Beta")
    DatasetFactory(name="Rock Collection Gamma")

    filterset = DatasetFilter({'search': 'rock'})
    assert filterset.qs.count() == 2

def test_generic_search_by_uuid(self):
    """Generic search matches UUIDs."""
    dataset = DatasetFactory(uuid="d123abc")
    DatasetFactory()  # Other dataset

    filterset = DatasetFilter({'search': '123abc'})
    assert filterset.qs.count() == 1
    assert filterset.qs.first() == dataset

def test_generic_search_by_keyword(self):
    """Generic search matches keywords."""
    dataset1 = DatasetFactory()
    dataset1.keywords.add("geology")
    dataset2 = DatasetFactory()
    dataset2.keywords.add("biology")

    filterset = DatasetFilter({'search': 'geology'})
    assert filterset.qs.count() == 1
    assert filterset.qs.first() == dataset1
```

### Cross-Relationship Filter Tests

```python
def test_description_filter(self):
    """Description filter searches across dataset descriptions."""
    dataset1 = DatasetFactory()
    DatasetDescription.objects.create(
        related=dataset1,
        description_type='Abstract',
        description='Contains uranium samples'
    )
    dataset2 = DatasetFactory()
    DatasetDescription.objects.create(
        related=dataset2,
        description_type='Abstract',
        description='Contains iron samples'
    )

    filterset = DatasetFilter({'description': 'uranium'})
    assert filterset.qs.count() == 1
    assert filterset.qs.first() == dataset1

def test_date_type_filter(self):
    """Date type filter shows datasets with specific date types."""
    dataset1 = DatasetFactory()
    DatasetDate.objects.create(
        related=dataset1,
        date_type='Collected',
        date='2024-01-15'
    )
    dataset2 = DatasetFactory()
    DatasetDate.objects.create(
        related=dataset2,
        date_type='Published',
        date='2024-02-20'
    )

    filterset = DatasetFilter({'date_type': 'Collected'})
    assert filterset.qs.count() == 1
    assert filterset.qs.first() == dataset1
```

### Filter Combination Tests

```python
def test_multiple_filters_combine_with_and(self):
    """Multiple filters combine with AND logic."""
    project = ProjectFactory()
    DatasetFactory(
        project=project,
        visibility=Visibility.PUBLIC,
        license=License.objects.get(name="CC BY 4.0"),
        count=2
    )
    DatasetFactory(project=project, visibility=Visibility.PRIVATE)  # Wrong visibility
    DatasetFactory(visibility=Visibility.PUBLIC)  # Wrong project

    filterset = DatasetFilter({
        'project': project.id,
        'visibility': Visibility.PUBLIC,
    })
    assert filterset.qs.count() == 2
```

### Performance Tests

```python
def test_cross_relationship_performance_with_large_dataset(self):
    """Cross-relationship filters perform well with 1000+ datasets."""
    # Create 1000 datasets with descriptions
    for i in range(1000):
        dataset = DatasetFactory()
        DatasetDescriptionFactory(related=dataset)

    # Measure queries
    with assertNumQueries(max_queries=5):
        filterset = DatasetFilter({
            'description': 'sample'
        }, queryset=Dataset.objects.all())
        list(filterset.qs[:10])  # Paginated results
```

---

## Usage Examples

### In Views

```python
from django.views.generic import ListView

class DatasetListView(ListView):
    model = Dataset
    filterset_class = DatasetFilter

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filterset = DatasetFilter(
            self.request.GET,
            queryset=queryset
        )
        return self.filterset.qs
```

### With django-tables2

```python
from django_tables2 import SingleTableView

class DatasetTableView(SingleTableView):
    model = Dataset
    table_class = DatasetTable
    filterset_class = DatasetFilter

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filterset = self.filterset_class(
            self.request.GET,
            queryset=queryset
        )
        return self.filterset.qs
```

### In Templates

```django
<form method="get">
    {{ filter.form.as_p }}
    <button type="submit">Filter</button>
</form>

<table>
    {% for dataset in filter.qs %}
        <tr><td>{{ dataset.name }}</td></tr>
    {% endfor %}
</table>
```

---

## Migration Path

### Phase 1: Add Basic Filters (Non-Breaking)

```python
# Add project, license, visibility filters
class DatasetFilter(BaseListFilter):
    project = django_filters.ModelChoiceFilter(...)
    license = django_filters.CharFilter(...)
    visibility = django_filters.ChoiceFilter(...)
```

### Phase 2: Add Generic Search (Feature Addition)

```python
# Add search field with custom method
search = django_filters.CharFilter(method='filter_search', ...)
```

### Phase 3: Add Cross-Relationship Filters (Feature Addition + Indexes)

```python
# Add description and date_type filters
description = django_filters.CharFilter(...)
date_type = django_filters.ChoiceFilter(...)

# Add database indexes for performance
# Requires migration: AddIndex to DatasetDescription and DatasetDate
```

**Impact**: All changes are backwards compatible. Existing code continues to work. New filters are optional.
