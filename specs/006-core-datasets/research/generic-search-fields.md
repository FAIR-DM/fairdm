# Research: Generic Search Field Set

**Feature**: 006-core-datasets
**Task**: T013
**Purpose**: Define searchable field set for generic dataset search functionality

---

## Requirements Analysis

### User Search Scenarios

1. **By Name**: "Geological Survey 2024"
2. **By UUID**: Quick lookup for technical users
3. **By Keywords**: Discovery through metadata
4. **By Description**: Find by methodology or content
5. **By Related Fields**: Project name, contributor name

---

## Recommended Searchable Fields

### Primary Fields (Direct Model)

| Field | Type | Weight | Rationale |
|-------|------|--------|-----------|
| **name** | CharField | High | Most common search term |
| **uuid** | UUIDField | High | Technical lookup, exact match |
| **description** | TextField | Medium | Content discovery |
| **keywords** | ArrayField | High | Metadata tags for discovery |

### Related Fields (Cross-Model)

| Field | Type | Weight | Rationale |
|-------|------|--------|-----------|
| **descriptions__description** | TextField | Medium | Detailed methodology/abstract |
| **project__name** | CharField | Medium | Filter by project context |
| **contributors__name** | CharField | Low | Author/creator search |

---

## Implementation

### Django Filter SearchFilter

```python
from django_filters import FilterSet, CharFilter

class DatasetFilter(FilterSet):
    """
    Filter for Dataset model with generic search.

    Generic search searches across:
    - Dataset name
    - Dataset UUID (partial match)
    - Dataset keywords
    - Dataset descriptions (all types)
    - Project name
    """
    search = CharFilter(method='filter_search', label=_('Search'))

    def filter_search(self, queryset, name, value):
        """
        Generic search across multiple fields.

        Uses OR logic - matches if ANY field contains search term.
        Case-insensitive search with partial matching.

        Performance: Requires database indexes on searched fields.
        See indexing strategy in research/cross-relationship-indexes.md
        """
        if not value:
            return queryset

        from django.db.models import Q

        return queryset.filter(
            Q(name__icontains=value) |
            Q(uuid__icontains=value) |
            Q(description__icontains=value) |
            Q(keywords__icontains=value) |
            Q(descriptions__description__icontains=value) |
            Q(project__name__icontains=value)
        ).distinct()

    class Meta:
        model = Dataset
        fields = ['search', ...]
```

### Admin Search Fields

```python
class DatasetAdmin(admin.ModelAdmin):
    """Admin for Dataset model."""
    search_fields = [
        'name',
        'uuid',
        'description',
        'keywords',
        'descriptions__description',
        'project__name',
    ]
```

**Django Admin automatically**:

- Uses `icontains` for text fields
- Uses `iexact` for UUID (case-insensitive exact match recommended)
- Combines with OR logic
- Adds DISTINCT clause

---

## Performance Considerations

### Database Indexes Required

```python
class Dataset(BaseModel):
    name = models.CharField(
        max_length=300,
        db_index=True,  # ← Index for name search
    )

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,  # ← Already indexed (unique constraint)
    )

    keywords = ArrayField(
        models.CharField(max_length=100),
        blank=True,
        default=list,
        # PostgreSQL GIN index for array contains
    )

    class Meta:
        indexes = [
            models.Index(fields=['name']),  # For name search
            GinIndex(fields=['keywords']),  # For keyword search (PostgreSQL)
            # Cross-relationship indexes
            models.Index(fields=['project', 'name']),  # For project filtering + search
        ]


class DatasetDescription(models.Model):
    description = models.TextField()

    class Meta:
        indexes = [
            # Full-text search index (PostgreSQL)
            GinIndex(
                fields=['description'],
                name='dataset_desc_fts_idx',
                opclasses=['gin_trgm_ops']  # Trigram index for LIKE queries
            ),
        ]
```

### Query Optimization

```python
# Prefetch related data to avoid N+1 queries
def get_queryset(self):
    return Dataset.objects.all().select_related(
        'project'
    ).prefetch_related(
        'descriptions',
        'contributors'
    )
```

---

## Search Behavior

### Case Sensitivity

**Recommendation**: Case-insensitive (`icontains`)

**Rationale**:

- Users don't remember exact casing
- Scientific terms may have various capitalizations
- More user-friendly

```python
# Case-insensitive
Q(name__icontains='geological')  # Matches "Geological", "geological", "GEOLOGICAL"

# Case-sensitive (NOT recommended)
Q(name__contains='geological')  # Only matches exact case
```

### Partial Matching

**Recommendation**: Allow partial matches

**Rationale**:

- Users may only know part of the name
- Enables discovery through fragments
- Standard search engine behavior

```python
# Partial match
Q(name__icontains='geo')  # Matches "Geological Survey", "Geothermal", "Geography"

# Exact match (NOT for generic search)
Q(name__iexact='Geological Survey')  # Only matches exact name
```

### Word Order

**Current**: Order-independent (OR logic with `icontains`)

**Future Enhancement**: Full-text search with ranking

```python
# Current: Matches if ANY word appears
filter_search('geological survey')  # Matches "Survey of Geological Sites"

# Future: PostgreSQL full-text search with ranking
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank

queryset.annotate(
    search=SearchVector('name', 'description', 'keywords'),
    rank=SearchRank('search', SearchQuery(value))
).filter(search=SearchQuery(value)).order_by('-rank')
```

---

## User Interface

### Search Input

```html
<form method="get" class="mb-4">
    <div class="input-group input-group-lg">
        <input type="text"
               name="search"
               class="form-control"
               placeholder="Search datasets by name, keywords, or description"
               value="{{ filter.form.search.value|default:'' }}"
               aria-label="Search datasets">
        <button class="btn btn-primary" type="submit">
            <i class="bi bi-search"></i> Search
        </button>
    </div>
    <small class="form-text text-muted">
        Search across dataset names, UUIDs, keywords, descriptions, and project names
    </small>
</form>
```

### Search Results

```html
{% if filter.form.search.value %}
    <div class="alert alert-info">
        <strong>{{ object_list.count }}</strong> dataset(s) found for
        <strong>"{{ filter.form.search.value }}"</strong>
        {% if filter.form.search.value %}
            <a href="?" class="btn btn-sm btn-outline-secondary ms-2">Clear search</a>
        {% endif %}
    </div>
{% endif %}

{% if not object_list %}
    <div class="alert alert-warning">
        <h5>No datasets found</h5>
        <p>Try adjusting your search terms or filters.</p>
        <ul>
            <li>Check spelling</li>
            <li>Use fewer or different keywords</li>
            <li>Remove filters to broaden results</li>
        </ul>
    </div>
{% endif %}
```

---

## Highlighting Search Terms

### Template Filter

```python
# fairdm/templatetags/search_tags.py

from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe
import re

register = template.Library()


@register.filter
def highlight_search(text, search_term):
    """
    Highlight search term in text.

    Usage: {{ dataset.name|highlight_search:search_term }}
    """
    if not search_term or not text:
        return text

    # Escape special regex characters
    pattern = re.escape(search_term)

    # Case-insensitive replacement
    highlighted = re.sub(
        f'({pattern})',
        r'<mark>\1</mark>',
        text,
        flags=re.IGNORECASE
    )

    return mark_safe(highlighted)
```

### Template Usage

```html
{% load search_tags %}

<h5 class="card-title">
    {{ dataset.name|highlight_search:search_term }}
</h5>
<p class="card-text">
    {{ dataset.description|truncatewords:20|highlight_search:search_term }}
</p>
```

---

## Advanced Features (Future)

### 1. Search Suggestions

```python
def get_search_suggestions(query, limit=5):
    """
    Get dataset name suggestions based on partial query.

    For autocomplete functionality.
    """
    return Dataset.objects.filter(
        name__istartswith=query
    ).values_list('name', flat=True)[:limit]
```

### 2. Recent Searches

```python
# Store in session
def save_recent_search(request, query):
    """Save search query to recent searches."""
    recent = request.session.get('recent_searches', [])
    if query and query not in recent:
        recent.insert(0, query)
        request.session['recent_searches'] = recent[:10]  # Keep last 10
```

### 3. Search Analytics

```python
class DatasetSearch(models.Model):
    """Track search queries for analytics."""
    query = models.CharField(max_length=255)
    results_count = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
```

---

## Testing

### Search Behavior Tests

```python
@pytest.mark.django_db
def test_search_by_name():
    """Search finds datasets by name."""
    DatasetFactory(name="Geological Survey 2024")
    DatasetFactory(name="Climate Data")

    filterset = DatasetFilter({'search': 'geological'})
    assert filterset.qs.count() == 1


@pytest.mark.django_db
def test_search_case_insensitive():
    """Search is case-insensitive."""
    DatasetFactory(name="Geological Survey")

    filterset = DatasetFilter({'search': 'GEOLOGICAL'})
    assert filterset.qs.count() == 1


@pytest.mark.django_db
def test_search_partial_match():
    """Search matches partial words."""
    DatasetFactory(name="Geological Survey 2024")

    filterset = DatasetFilter({'search': 'geo'})
    assert filterset.qs.count() == 1


@pytest.mark.django_db
def test_search_by_uuid():
    """Search finds datasets by UUID."""
    dataset = DatasetFactory()
    uuid_str = str(dataset.uuid)[:8]  # First 8 chars

    filterset = DatasetFilter({'search': uuid_str})
    assert dataset in filterset.qs


@pytest.mark.django_db
def test_search_by_keywords():
    """Search finds datasets by keywords."""
    DatasetFactory(keywords=['geology', 'minerals'])
    DatasetFactory(keywords=['climate', 'temperature'])

    filterset = DatasetFilter({'search': 'geology'})
    assert filterset.qs.count() == 1


@pytest.mark.django_db
def test_search_by_description():
    """Search finds datasets by description text."""
    dataset = DatasetFactory(description="This dataset contains geological samples")
    DatasetFactory(description="Climate data")

    filterset = DatasetFilter({'search': 'geological'})
    assert dataset in filterset.qs


@pytest.mark.django_db
def test_search_across_related_descriptions():
    """Search finds datasets by DatasetDescription text."""
    dataset = DatasetFactory()
    dataset.descriptions.create(
        description_type="Methods",
        description="X-ray fluorescence methodology"
    )

    filterset = DatasetFilter({'search': 'fluorescence'})
    assert dataset in filterset.qs


@pytest.mark.django_db
def test_search_by_project_name():
    """Search finds datasets by project name."""
    project = ProjectFactory(name="Arctic Research")
    dataset = DatasetFactory(project=project)
    DatasetFactory()  # Different project

    filterset = DatasetFilter({'search': 'arctic'})
    assert filterset.qs.count() == 1
    assert dataset in filterset.qs


@pytest.mark.django_db
def test_search_distinct_results():
    """Search returns distinct results (no duplicates)."""
    dataset = DatasetFactory(name="Geological Survey")
    dataset.descriptions.create(
        description_type="Abstract",
        description="Geological data collection"
    )
    dataset.descriptions.create(
        description_type="Methods",
        description="Geological sampling methodology"
    )

    # Matches name AND two descriptions - should return dataset once
    filterset = DatasetFilter({'search': 'geological'})
    assert filterset.qs.count() == 1


@pytest.mark.django_db
def test_empty_search_returns_all():
    """Empty search returns all datasets."""
    DatasetFactory.create_batch(5)

    filterset = DatasetFilter({'search': ''})
    assert filterset.qs.count() == 5
```

---

## Documentation

### User Guide

> **Generic Search**
>
> The search box allows you to find datasets by:
>
> - **Name**: Full or partial dataset name
> - **UUID**: Dataset identifier (useful for technical lookups)
> - **Keywords**: Metadata tags assigned to datasets
> - **Description**: Main description or detailed methodology/abstract
> - **Project**: Name of the project containing the dataset
>
> **Tips**:
>
> - Search is case-insensitive ("Geological" = "geological")
> - Partial matches work ("geo" finds "Geological Survey")
> - Searches across all fields simultaneously
> - Results show all datasets matching ANY searched field

### Developer Guide

> **Search Implementation**
>
> Generic search uses Django ORM Q objects to perform OR queries across multiple fields:
>
> ```python
> queryset.filter(
>     Q(name__icontains=value) |
>     Q(uuid__icontains=value) |
>     Q(keywords__icontains=value) |
>     Q(descriptions__description__icontains=value) |
>     Q(project__name__icontains=value)
> ).distinct()
> ```
>
> **Performance Optimization**:
>
> - Requires database indexes on frequently searched fields
> - Use `select_related()` for project lookups
> - Use `prefetch_related()` for descriptions
> - Apply `.distinct()` to avoid duplicate results from JOINs

---

## Decision Summary

✅ **Primary Fields**: name, uuid, description, keywords
✅ **Related Fields**: descriptions__description, project__name
✅ **Search Type**: Case-insensitive, partial match (`icontains`)
✅ **Logic**: OR (match if ANY field contains term)
✅ **Performance**: Database indexes required on searched fields
✅ **Results**: Distinct (no duplicates)
✅ **Admin Integration**: Same search fields used in admin
✅ **Future**: Full-text search with ranking for PostgreSQL
