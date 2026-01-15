# Research: Cross-Relationship Filter Indexing

**Feature**: 006-core-datasets
**Task**: T018
**Purpose**: Document indexing strategies for performant cross-relationship filtering

---

## Problem Statement

Generic search and filters query across relationships:

```python
# Filter by DatasetDescription text (crosses dataset → descriptions relationship)
Q(descriptions__description__icontains=value)

# Filter by Project name (crosses dataset → project relationship)
Q(project__name__icontains=value)

# Filter by date type (crosses dataset → dates relationship)
Q(dates__date_type=value)
```

**Performance Issues**:

- JOIN operations across tables
- LIKE queries (`icontains`) can't use standard B-tree indexes efficiently
- Multiple filter conditions compound the problem
- N+1 query problems with prefetch

---

## Indexing Strategies

### 1. Foreign Key Indexes (Built-in)

```python
class Dataset(BaseModel):
    project = models.ForeignKey(
        Project,
        on_delete=models.PROTECT,
        # Django automatically creates index on project_id column
    )
```

**Performance**: ✅ Excellent for exact FK lookups
**Use Case**: `filter(project=project_instance)`, `filter(project_id=5)`
**Cost**: Low (automatic)

---

### 2. Composite Indexes for JOIN + Filter

```python
class Dataset(BaseModel):
    class Meta:
        indexes = [
            # Optimize: filter(project=X, name__icontains=Y)
            models.Index(fields=['project', 'name']),

            # Optimize: filter(project=X, visibility=Y)
            models.Index(fields=['project', 'visibility']),

            # Optimize: filter(visibility=X, added__gte=Y)
            models.Index(fields=['visibility', 'added']),
        ]
```

**Performance**: ✅ Excellent for combined filters
**Use Case**: Common filter combinations
**Cost**: Medium (storage overhead per index)

---

### 3. Trigram Indexes for Text Search (PostgreSQL)

```python
from django.contrib.postgres.indexes import GinIndex

class DatasetDescription(models.Model):
    description = models.TextField()

    class Meta:
        indexes = [
            GinIndex(
                fields=['description'],
                name='dataset_desc_trgm_idx',
                opclasses=['gin_trgm_ops']  # Trigram operator class
            ),
        ]
```

**Requires**: `CREATE EXTENSION pg_trgm;` in PostgreSQL

**Performance**: ✅ Very good for `LIKE`/`icontains` queries
**Use Case**: `descriptions__description__icontains='methodology'`
**Cost**: High (storage overhead, slower writes)

**Migration**:

```python
from django.contrib.postgres.operations import TrigramExtension

class Migration:
    operations = [
        TrigramExtension(),  # Enable pg_trgm extension
        migrations.AddIndex(...),
    ]
```

---

### 4. GIN Index for Array Fields (PostgreSQL)

```python
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex

class Dataset(BaseModel):
    keywords = ArrayField(
        models.CharField(max_length=100),
        blank=True,
        default=list,
    )

    class Meta:
        indexes = [
            GinIndex(fields=['keywords']),  # For array containment queries
        ]
```

**Performance**: ✅ Excellent for array containment (`@>`, `contains`)
**Use Case**: `filter(keywords__contains=['geology'])`, `filter(keywords__overlap=['geology', 'minerals'])`
**Cost**: Medium (storage overhead)

---

### 5. Covering Indexes (INCLUDE clause - PostgreSQL 11+)

```python
class DatasetDescription(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    description_type = models.CharField(max_length=50)
    description = models.TextField()

    class Meta:
        indexes = [
            # Index on (dataset, description_type) INCLUDE (description)
            # Allows index-only scans without touching table
            models.Index(
                fields=['dataset', 'description_type'],
                name='dataset_desc_covering_idx',
                include=['description'],  # Extra columns in index
            ),
        ]
```

**Performance**: ✅ Excellent (index-only scans)
**Use Case**: Queries that filter by indexed columns and retrieve included columns
**Cost**: High (storage overhead - stores description text in index)

**Note**: Only worth it for frequently accessed columns

---

### 6. Partial Indexes (Filtered Indexes)

```python
class Dataset(BaseModel):
    class Meta:
        indexes = [
            # Only index PUBLIC datasets (most common query)
            models.Index(
                fields=['visibility', 'added'],
                name='dataset_public_idx',
                condition=models.Q(visibility='PUBLIC')
            ),
        ]
```

**Performance**: ✅ Excellent for common subset queries
**Use Case**: `filter(visibility='PUBLIC')` - the most common dataset query
**Cost**: Low (smaller index size, only indexes subset)

---

## Recommended Index Strategy

### Dataset Model

```python
from django.contrib.postgres.indexes import GinIndex

class Dataset(BaseModel):
    class Meta:
        indexes = [
            # Basic indexes
            models.Index(fields=['name']),  # For name search
            models.Index(fields=['added']),  # For ordering by date

            # Composite indexes for common filters
            models.Index(fields=['project', 'visibility']),  # Project + access control
            models.Index(fields=['visibility', 'added']),    # Public datasets by date

            # Partial index for PUBLIC datasets (most common)
            models.Index(
                fields=['added'],
                name='dataset_public_recent_idx',
                condition=models.Q(visibility='PUBLIC')
            ),

            # GIN index for keywords array
            GinIndex(fields=['keywords']),
        ]
```

### DatasetDescription Model

```python
from django.contrib.postgres.indexes import GinIndex

class DatasetDescription(models.Model):
    class Meta:
        indexes = [
            # Foreign key + filter combo
            models.Index(fields=['dataset', 'description_type']),

            # Trigram index for text search
            GinIndex(
                fields=['description'],
                name='dataset_desc_search_idx',
                opclasses=['gin_trgm_ops']
            ),
        ]
```

### DatasetDate Model

```python
class DatasetDate(models.Model):
    class Meta:
        indexes = [
            # Foreign key + filter combo
            models.Index(fields=['dataset', 'date_type']),

            # Date range queries
            models.Index(fields=['date', 'date_type']),
        ]
```

### DatasetIdentifier Model

```python
class DatasetIdentifier(models.Model):
    class Meta:
        indexes = [
            # Foreign key + filter combo
            models.Index(fields=['dataset', 'identifier_type']),

            # Lookup by identifier value
            models.Index(fields=['identifier']),
        ]
```

---

## QuerySet Optimization

### Prefetch Related Data

```python
class DatasetQuerySet(models.QuerySet):
    def with_related(self):
        """Prefetch commonly accessed related data."""
        return self.select_related(
            'project',
            'license',
        ).prefetch_related(
            'descriptions',
            'dates',
            'identifiers',
            'contributors',
        )
```

**Performance**: ✅ Eliminates N+1 queries
**Use Case**: List views that display related data
**Cost**: None (reduces total queries)

### Annotate for Filtering

```python
from django.db.models import Exists, OuterRef

class DatasetQuerySet(models.QuerySet):
    def with_has_data(self):
        """Annotate whether dataset has samples or measurements."""
        return self.annotate(
            has_data=Exists(
                Sample.objects.filter(dataset=OuterRef('pk'))
            ) | Exists(
                Measurement.objects.filter(dataset=OuterRef('pk'))
            )
        )
```

**Performance**: ✅ Good (single query with subquery)
**Use Case**: Filtering/displaying datasets with data
**Cost**: None (avoids separate queries per dataset)

---

## Benchmarking

### Test Query Performance

```python
from django.db import connection
from django.test.utils import CaptureQueriesContext

# Benchmark filter performance
with CaptureQueriesContext(connection) as context:
    datasets = Dataset.objects.filter(
        descriptions__description__icontains='methodology'
    ).distinct()[:20]
    list(datasets)  # Force query execution

print(f"Queries: {len(context.captured_queries)}")
for query in context.captured_queries:
    print(f"Time: {query['time']}s")
    print(f"SQL: {query['sql'][:200]}")
```

### EXPLAIN ANALYZE

```python
queryset = Dataset.objects.filter(
    descriptions__description__icontains='methodology'
).distinct()

print(queryset.explain(analyze=True, verbose=True))
```

**Look for**:

- **Seq Scan** (bad) vs **Index Scan** (good)
- **Nested Loop** joins (can be slow)
- High **execution time** or **rows scanned**

---

## Migration Strategy

### Phase 1: Essential Indexes (Day 1)

```python
class Migration:
    operations = [
        # Enable trigram extension
        TrigramExtension(),

        # Basic performance indexes
        migrations.AddIndex(
            model_name='dataset',
            index=models.Index(fields=['name'], name='dataset_name_idx'),
        ),
        migrations.AddIndex(
            model_name='dataset',
            index=GinIndex(fields=['keywords'], name='dataset_keywords_idx'),
        ),

        # Cross-relationship indexes
        migrations.AddIndex(
            model_name='datasetdescription',
            index=models.Index(fields=['dataset', 'description_type']),
        ),
    ]
```

### Phase 2: Optimize Hot Paths (After Monitoring)

```python
class Migration:
    operations = [
        # Add trigram index after confirming search usage
        migrations.AddIndex(
            model_name='datasetdescription',
            index=GinIndex(
                fields=['description'],
                name='dataset_desc_trgm_idx',
                opclasses=['gin_trgm_ops']
            ),
        ),

        # Add partial index for PUBLIC datasets
        migrations.AddIndex(
            model_name='dataset',
            index=models.Index(
                fields=['added'],
                name='dataset_public_idx',
                condition=models.Q(visibility='PUBLIC')
            ),
        ),
    ]
```

### Phase 3: Advanced Optimization (Production Monitoring)

```python
class Migration:
    operations = [
        # Add covering index if query logs show benefit
        migrations.AddIndex(
            model_name='datasetdescription',
            index=models.Index(
                fields=['dataset', 'description_type'],
                name='dataset_desc_covering_idx',
                include=['description']
            ),
        ),
    ]
```

---

## Monitoring & Maintenance

### Query Monitoring

```python
# settings.py (development)
LOGGING = {
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',  # Log all SQL queries
        },
    },
}
```

### Slow Query Log (PostgreSQL)

```sql
-- postgresql.conf
log_min_duration_statement = 1000  -- Log queries > 1 second
```

### Index Usage Stats

```sql
-- Check index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- Find unused indexes
SELECT
    schemaname,
    tablename,
    indexname
FROM pg_stat_user_indexes
WHERE idx_scan = 0
AND indexname NOT LIKE '%_pkey';
```

---

## Testing

### Performance Tests

```python
import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

@pytest.mark.django_db
def test_search_query_count():
    """Generic search should use efficient queries."""
    # Create test data
    DatasetFactory.create_batch(10)

    with CaptureQueriesContext(connection) as context:
        filterset = DatasetFilter({'search': 'dataset'})
        list(filterset.qs[:10])

    # Should be 1-2 queries (select + maybe count)
    assert len(context.captured_queries) <= 2


@pytest.mark.django_db
def test_cross_relationship_filter_performance():
    """Cross-relationship filters should perform well."""
    project = ProjectFactory()
    for i in range(100):
        dataset = DatasetFactory(project=project)
        dataset.descriptions.create(
            description_type="Methods",
            description=f"Methodology {i}"
        )

    with CaptureQueriesContext(connection) as context:
        filterset = DatasetFilter({
            'project': project.id,
            'description': 'Methodology'
        })
        list(filterset.qs[:20])

    # Should be efficient (1-3 queries)
    assert len(context.captured_queries) <= 3
```

---

## Decision Summary

✅ **Foreign Key Indexes**: Automatic for ForeignKey fields
✅ **Composite Indexes**: For common filter combinations (project + visibility, visibility + date)
✅ **Trigram Indexes**: For text search (`icontains`) on description fields
✅ **GIN Indexes**: For array containment queries (keywords)
✅ **Partial Indexes**: For PUBLIC datasets (most common subset)
✅ **Prefetch/Select Related**: Eliminate N+1 queries in querysets
✅ **Phased Rollout**: Essential indexes first, optimize based on monitoring
✅ **Monitoring**: Track slow queries and index usage in production
