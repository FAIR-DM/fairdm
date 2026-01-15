# Contract: Dataset QuerySet

**Feature**: 006-core-datasets
**Purpose**: Define the public interface for DatasetQuerySet manager with privacy-first defaults
**Input**: [data-model.md](../data-model.md)

## DatasetQuerySet Interface

### Class Definition

```python
class DatasetQuerySet(models.QuerySet):
    """
    Custom QuerySet for Dataset model with privacy-first defaults and optimized query methods.

    Privacy-First Design:
        The default manager behavior excludes datasets with visibility=PRIVATE.
        This prevents accidental exposure of private datasets in public views.

        To access private datasets, use:
        - get_all() or with_private(): Returns all datasets including private ones

    Query Optimization:
        Optional optimization methods reduce N+1 query problems:
        - with_related(): Prefetches project and contributors
        - with_contributors(): Prefetches only contributors

        These are suggestions (SHOULD) based on usage patterns, not requirements (MUST).
    """
```

### Methods

#### Default Behavior (Privacy-First)

```python
def all(self) -> QuerySet["Dataset"]:
    """
    Return all NON-PRIVATE datasets (privacy-first default).

    Returns:
        QuerySet excluding datasets with visibility=PRIVATE

    Note:
        This overrides the default QuerySet.all() to implement privacy-first design.
        To access private datasets, use get_all() or with_private().

    Examples:
        # Returns only PUBLIC and INTERNAL datasets
        Dataset.objects.all()

        # To get truly all datasets
        Dataset.objects.get_all()
    """
    return self.exclude(visibility=Visibility.PRIVATE)
```

#### Explicit Private Access

```python
def get_all(self) -> QuerySet["Dataset"]:
    """
    Return ALL datasets including PRIVATE ones (explicit opt-in).

    Returns:
        QuerySet including all datasets regardless of visibility

    Note:
        This method provides explicit access to private datasets.
        Views that need private datasets must explicitly call this method.

    Examples:
        # Get all datasets including private
        all_datasets = Dataset.objects.get_all()

        # Filter private datasets
        private_datasets = Dataset.objects.get_all().filter(
            visibility=Visibility.PRIVATE
        )
    """
    # Call super().all() to get truly all records
    return super().all()

# OR alternative naming:

def with_private(self) -> QuerySet["Dataset"]:
    """
    Return ALL datasets including PRIVATE ones (explicit opt-in).

    Alternative naming to get_all(). Choose one approach and document.

    Returns:
        QuerySet including all datasets regardless of visibility
    """
    return super().all()
```

#### Query Optimization Methods (Optional - SHOULD not MUST)

```python
def with_related(self) -> QuerySet["Dataset"]:
    """
    Prefetch related project and contributors for optimized access.

    Returns:
        QuerySet with prefetched project and contributors

    Performance:
        Reduces queries from N+1 to 2-3 total:
        - 1 query for datasets
        - 1-2 queries for prefetch (project, contributors)

    Note:
        This is a SHOULD method (optional) based on actual usage patterns.
        Only use when views/templates access project and contributor data.

    Examples:
        # Optimized query for list view with project info
        datasets = Dataset.objects.with_related().filter(
            visibility=Visibility.PUBLIC
        )

        # Access without additional queries
        for dataset in datasets:
            print(dataset.project.name)  # No additional query
            print(dataset.contributors.count())  # No additional query
    """
    return self.prefetch_related(
        "project",
        "contributors",
    )
```

```python
def with_contributors(self) -> QuerySet["Dataset"]:
    """
    Prefetch only contributors for optimized access.

    Returns:
        QuerySet with prefetched contributors

    Performance:
        Reduces queries from N+1 to 2 total:
        - 1 query for datasets
        - 1 query for contributors

    Note:
        This is a SHOULD method (optional) based on actual usage patterns.
        Use when views/templates only need contributor data, not project.

    Examples:
        # Optimized query for contributor list
        datasets = Dataset.objects.with_contributors()

        # Access without additional queries
        for dataset in datasets:
            for contributor in dataset.contributors.all():  # No additional query
                print(contributor.name)
    """
    return self.prefetch_related("contributors")
```

### Manager Configuration

```python
class Dataset(BaseModel):
    # ...
    objects = DatasetQuerySet.as_manager()  # Custom manager with privacy-first default
```

---

## Query Count Expectations

### Without Optimization

```python
# N+1 query problem
datasets = Dataset.objects.all()
for dataset in datasets:
    print(dataset.project.name)        # +1 query per dataset
    print(dataset.contributors.count())  # +1 query per dataset

# Total: 1 + N + N = 2N + 1 queries for N datasets
```

### With Optimization

```python
# Optimized query
datasets = Dataset.objects.with_related().all()
for dataset in datasets:
    print(dataset.project.name)        # No additional query
    print(dataset.contributors.count())  # No additional query

# Total: 1 + 1 + 1 = 3 queries regardless of N
```

### Query Reduction

- **Without optimization**: 2N + 1 queries (for N=100: 201 queries)
- **With optimization**: 3 queries (for N=100: 3 queries)
- **Reduction**: ~98% for large datasets (meets SC-006 requirement of 80%+)

---

## Chaining Behavior

### Method Chaining

```python
# Methods can be chained
datasets = (
    Dataset.objects
    .get_all()           # Include private datasets
    .with_related()      # Prefetch project and contributors
    .filter(project=my_project)
    .order_by('-modified')
)
```

### Privacy-First + Optimization

```python
# Default excludes private, optimizes queries
public_datasets = Dataset.objects.with_related().all()

# Explicit include private, optimizes queries
all_datasets = Dataset.objects.get_all().with_related()
```

### Filter Preservation

```python
# Privacy-first applied after filters
recent_public = Dataset.objects.filter(
    modified__gte=last_week
).all()  # Excludes private from filtered results

# Explicit private access after filters
recent_all = Dataset.objects.filter(
    modified__gte=last_week
).get_all()  # Includes private in filtered results
```

---

## Testing Contracts

### Privacy-First Default Tests

```python
def test_default_excludes_private(self):
    """Dataset.objects.all() excludes PRIVATE datasets."""
    Dataset.objects.create(name="Private", visibility=Visibility.PRIVATE)
    Dataset.objects.create(name="Public", visibility=Visibility.PUBLIC)

    assert Dataset.objects.all().count() == 1
    assert Dataset.objects.all().first().name == "Public"

def test_get_all_includes_private(self):
    """Dataset.objects.get_all() includes PRIVATE datasets."""
    Dataset.objects.create(name="Private", visibility=Visibility.PRIVATE)
    Dataset.objects.create(name="Public", visibility=Visibility.PUBLIC)

    assert Dataset.objects.get_all().count() == 2
```

### Query Optimization Tests

```python
def test_with_related_reduces_queries(self):
    """with_related() reduces queries by 80%+ (SC-006)."""
    # Create 100 datasets with projects and contributors
    for i in range(100):
        dataset = DatasetFactory()
        ContributorFactory(dataset=dataset, count=3)

    # Measure queries without optimization
    with assertNumQueries(201):  # 1 + 100 + 100
        datasets = Dataset.objects.all()
        for dataset in datasets:
            _ = dataset.project.name
            _ = dataset.contributors.count()

    # Measure queries with optimization
    with assertNumQueries(3):  # 1 + 1 + 1
        datasets = Dataset.objects.with_related().all()
        for dataset in datasets:
            _ = dataset.project.name
            _ = dataset.contributors.count()

def test_with_contributors_prefetches_contributors(self):
    """with_contributors() prefetches only contributors."""
    dataset = DatasetFactory()
    ContributorFactory(dataset=dataset, count=5)

    with assertNumQueries(2):  # 1 for dataset, 1 for contributors
        datasets = Dataset.objects.with_contributors().all()
        for dataset in datasets:
            _ = list(dataset.contributors.all())
```

### Chaining Tests

```python
def test_chaining_privacy_and_optimization(self):
    """Privacy-first and optimization methods chain correctly."""
    DatasetFactory(visibility=Visibility.PRIVATE)
    DatasetFactory(visibility=Visibility.PUBLIC)

    # get_all() + with_related()
    datasets = Dataset.objects.get_all().with_related()
    assert datasets.count() == 2

    # all() (privacy-first) + with_related()
    datasets = Dataset.objects.all().with_related()
    assert datasets.count() == 1
```

---

## Implementation Notes

### Manager Setup

The QuerySet must be registered as a manager on the Dataset model:

```python
class Dataset(BaseModel):
    objects = DatasetQuerySet.as_manager()
```

This makes custom methods available on `Dataset.objects`:
- `Dataset.objects.all()` → privacy-first default
- `Dataset.objects.get_all()` → explicit private access
- `Dataset.objects.with_related()` → query optimization

### Privacy-First Implementation Options

**Option 1: Override all()** (Recommended)
```python
def all(self):
    return self.exclude(visibility=Visibility.PRIVATE)

def get_all(self):
    return super().all()
```

**Option 2: Custom Manager with get_queryset()**
```python
class DatasetManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().exclude(visibility=Visibility.PRIVATE)

class Dataset(BaseModel):
    objects = DatasetManager.from_queryset(DatasetQuerySet)()
    all_objects = DatasetQuerySet.as_manager()  # For private access
```

Choose Option 1 for consistency with clarifications.

### Documentation Requirements

All methods MUST document:
1. Privacy behavior (includes/excludes private)
2. Query count expectations
3. Usage examples
4. Performance characteristics

---

## Migration Path

### Phase 1: Implement Methods (Non-Breaking)

Add new methods without changing default behavior:

```python
def with_related(self):
    ...

def with_contributors(self):
    ...
```

### Phase 2: Add Privacy-First Default (Breaking Change)

Change default behavior to exclude private:

```python
def all(self):
    return self.exclude(visibility=Visibility.PRIVATE)

def get_all(self):
    return super().all()
```

**Impact**: Views using `Dataset.objects.all()` will exclude private datasets

**Migration**: Update views that need private datasets to use `get_all()`

### Rollback

Revert `all()` override to restore original behavior:

```python
# Remove override, default .all() returns all records
```
