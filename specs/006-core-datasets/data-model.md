# Data Model: Core Dataset App

**Feature**: 006-core-datasets
**Created**: 2026-01-15
**Input**: [spec.md](spec.md), [plan.md](plan.md)

## Overview

This document defines the detailed data structures, field specifications, relationships, and validation rules for the Dataset app enhancement. All changes reflect the clarifications from Session 2026-01-15 including PROTECT behavior, privacy-first defaults, DataCite standards, and dynamic configurations.

## Entity Definitions

### Dataset

**Purpose**: Core model representing a collection of samples, measurements, and metadata in the FairDM hierarchy.

**Inheritance**: Extends `fairdm.core.base.BaseModel`

**Fields**:

| Field | Type | Constraints | Default | Description |
|-------|------|-------------|---------|-------------|
| `uuid` | ShortUUIDField | unique, editable=False, prefix="d" | auto-generated | Stable external identifier |
| `name` | CharField | required, max_length=200 | - | Human-readable dataset name |
| `visibility` | IntegerField | choices=Visibility | PRIVATE | Access control level (PUBLIC, INTERNAL, PRIVATE) |
| `image` | ImageField | optional | - | Visual identification image for cards and meta tags |
| `project` | ForeignKey | optional, on_delete=PROTECT | null | Associated project (PROTECT prevents deletion) |
| `reference` | OneToOneField | optional, on_delete=SET_NULL | null | Data publication/literature item |
| `related_literature` | ManyToManyField | through=DatasetLiteratureRelation | - | Related literature with relationship types |
| `license` | LicenseField | optional | CC BY 4.0 | Dataset license |
| `added` | DateTimeField | auto_now_add | current timestamp | Creation timestamp (audit trail) |
| `modified` | DateTimeField | auto_now | current timestamp | Last modification timestamp (audit trail) |
| `keywords` | ManyToManyField | optional | - | Taggit tags for categorization |

**Relationships**:

- **Project**: ForeignKey to `project.Project` with `on_delete=PROTECT` (prevents accidental dataset loss when project deleted)
- **Contributors**: GenericRelation to `contributors.Contribution` (many-to-many through content types)
- **Descriptions**: Reverse relation from `DatasetDescription` (one-to-many)
- **Dates**: Reverse relation from `DatasetDate` (one-to-many)
- **Identifiers**: Reverse relation from `DatasetIdentifier` (one-to-many)
- **Related Literature**: ManyToManyField to `literature.LiteratureItem` through `DatasetLiteratureRelation`
- **Samples**: Reverse relation from sample models (one-to-many)
- **Measurements**: Reverse relation from measurement models (one-to-many)

**Validation**:

- `name` MUST be non-empty (required field)
- `name` max_length=200
- `visibility` MUST be one of: PUBLIC, INTERNAL, PRIVATE
- Orphaned datasets (`project=null`) are permitted but not encouraged

**Properties**:

- `has_data` (cached_property): Boolean indicating if dataset has any samples or measurements
- `bbox` (cached_property): Geographic bounding box for dataset

**Permissions**:

- `view_dataset`: View dataset details
- `add_dataset`: Create new datasets
- `change_dataset`: Edit existing datasets
- `delete_dataset`: Delete datasets
- `import_data`: Import data into datasets

**Meta**:

- `verbose_name`: "dataset"
- `verbose_name_plural`: "datasets"
- `default_related_name`: "datasets"
- `ordering`: ["modified"]

**Manager**: `DatasetQuerySet.as_manager()` (custom QuerySet with privacy-first default)

**Behavior Notes**:

- **PROTECT behavior**: Projects with attached datasets cannot be deleted. Users must reassign or delete datasets first.
- **Orphaned datasets**: Datasets with `project=null` are valid (edge case for project restructuring) but not encouraged.
- **UUID collision**: Relies on ShortUUID uniqueness + database unique constraint. Collision probability is astronomically low.
- **Empty datasets**: Datasets without samples/measurements are valid (planning phase) but flagged via `has_data` property.
- **Image aspect ratio**: TBD based on research (T012, T014). Should work well in card displays and HTML meta tags.

---

### DatasetQuerySet

**Purpose**: Custom QuerySet manager providing privacy-first defaults and optimized query methods.

**Methods**:

| Method | Return Type | Parameters | Description |
|--------|-------------|------------|-------------|
| `get_all()` or `with_private()` | QuerySet | - | Returns ALL datasets including PRIVATE ones (explicit opt-in) |
| `with_related()` | QuerySet | - | Prefetches project and contributors (SHOULD, not MUST) |
| `with_contributors()` | QuerySet | - | Prefetches only contributors (SHOULD, not MUST) |

**Default Behavior**:

- **Privacy-first**: Default manager excludes datasets with `visibility=PRIVATE`
- Users MUST explicitly call `get_all()` or `with_private()` to access private datasets
- This prevents accidental exposure of private data in public views

**Query Optimization**:

- `with_related()`: Reduces queries by ~80% when loading datasets with project and contributor data
- `with_contributors()`: Optimizes contributor-only queries
- Methods are suggestions (SHOULD) based on usage patterns, not hard requirements (MUST)

**Query Count Expectations**:

- Without optimization: N+1 queries (1 for datasets, 1 per dataset for related data)
- With `with_related()`: 2-3 queries total (1 for datasets, 1-2 for prefetch)

---

### DatasetLiteratureRelation

**Purpose**: Intermediate model for Dataset-to-LiteratureItem relationships specifying DataCite relationship types.

**Inheritance**: Extends `django.db.models.Model`

**Fields**:

| Field | Type | Constraints | Default | Description |
|-------|------|-------------|---------|-------------|
| `dataset` | ForeignKey | required, on_delete=CASCADE | - | Dataset in relationship |
| `literature_item` | ForeignKey | required, on_delete=CASCADE | - | Literature item in relationship |
| `relationship_type` | CharField | required, max_length=50, choices=DATACITE_TYPES | - | DataCite relationship type |

**DataCite Relationship Types** (from DataCite RelationType vocabulary):

- `IsCitedBy`: Dataset is cited by the literature item
- `Cites`: Dataset cites the literature item
- `IsSupplementTo`: Dataset supplements the literature item
- `IsSupplementedBy`: Dataset is supplemented by the literature item
- `IsReferencedBy`: Dataset is referenced by the literature item
- `References`: Dataset references the literature item
- `IsDocumentedBy`: Dataset is documented by the literature item
- `Documents`: Dataset documents the literature item

**Validation**:

- `relationship_type` MUST be one of the DataCite types
- Validate against DataCite RelationType vocabulary (research complete list in T011)

**Usage**:

```python
# Creating a relationship
DatasetLiteratureRelation.objects.create(
    dataset=my_dataset,
    literature_item=paper,
    relationship_type='IsCitedBy'
)

# Querying
dataset.related_literature.through.objects.filter(
    relationship_type='IsCitedBy'
)
```

**Meta**:

- `verbose_name`: "dataset literature relation"
- `verbose_name_plural`: "dataset literature relations"
- `unique_together`: [["dataset", "literature_item", "relationship_type"]]

---

### DatasetDescription

**Purpose**: Stores typed descriptions for datasets using controlled FAIR vocabulary.

**Inheritance**: Extends `fairdm.core.abstract.AbstractDescription`

**Fields** (from AbstractDescription):

| Field | Type | Constraints | Default | Description |
|-------|------|-------------|---------|-------------|
| `related` | ForeignKey | required, on_delete=CASCADE | - | Dataset this description belongs to |
| `description_type` | CharField | required, choices=VOCABULARY | - | Type from FairDMDescriptions vocabulary |
| `description` | TextField | required | - | Description text content |

**Vocabulary**: `FairDMDescriptions.from_collection("Dataset")`

**Validation**:

- `description_type` MUST validate against `DESCRIPTION_TYPES` vocabulary
- Validation errors should reference vocabulary concept URIs for clarity

**Common Description Types** (from FairDMDescriptions):

- Abstract
- Methods
- Technical Info
- Rights
- Other

---

### DatasetDate

**Purpose**: Stores typed dates for datasets using controlled FAIR vocabulary.

**Inheritance**: Extends `fairdm.core.abstract.AbstractDate`

**Fields** (from AbstractDate):

| Field | Type | Constraints | Default | Description |
|-------|------|-------------|---------|-------------|
| `related` | ForeignKey | required, on_delete=CASCADE | - | Dataset this date belongs to |
| `date_type` | CharField | required, choices=VOCABULARY | - | Type from FairDMDates vocabulary |
| `date` | DateField | required | - | Date value |

**Vocabulary**: `FairDMDates.from_collection("Dataset")`

**Validation**:

- `date_type` MUST validate against `DATE_TYPES` vocabulary
- Validation errors should reference vocabulary concept URIs for clarity

**Common Date Types** (from FairDMDates):

- Collected
- Created
- Issued
- Submitted
- Accepted
- Available
- Copyrighted
- Updated

---

### DatasetIdentifier

**Purpose**: Stores typed identifiers for datasets using controlled FAIR vocabulary.

**Inheritance**: Extends `fairdm.core.abstract.AbstractIdentifier`

**Fields** (from AbstractIdentifier):

| Field | Type | Constraints | Default | Description |
|-------|------|-------------|---------|-------------|
| `related` | ForeignKey | required, on_delete=CASCADE | - | Dataset this identifier belongs to |
| `identifier_type` | CharField | required, choices=VOCABULARY | - | Type from FairDMIdentifiers vocabulary |
| `identifier` | CharField | required, max_length=255 | - | Identifier value |

**Vocabulary**: `FairDMIdentifiers()`

**Validation**:

- `identifier_type` MUST validate against `IDENTIFIER_TYPES` vocabulary
- Validation errors should reference vocabulary concept URIs for clarity

**DOI Support**:

- DOI identifiers use `identifier_type='DOI'`
- The `reference` field on Dataset is for linking to literature items/publications, NOT for DOI storage
- This separation maintains clean data modeling and supports multiple identifier types

**Common Identifier Types** (from FairDMIdentifiers):

- DOI
- Handle
- ARK
- URL
- URN

---

## Relationships Diagram

```
┌─────────────────┐
│     Project     │
│                 │
└────────┬────────┘
         │ PROTECT (prevents project deletion if datasets exist)
         │
         ▼
┌─────────────────┐                  ┌──────────────────────┐
│     Dataset     │◄─────────────────┤  DatasetDescription  │
│                 │  one-to-many     │                      │
│                 │                  └──────────────────────┘
│                 │◄─────────────────┤    DatasetDate       │
│                 │  one-to-many     └──────────────────────┘
│                 │◄─────────────────┤  DatasetIdentifier   │
│                 │  one-to-many     └──────────────────────┘
│                 │
│                 │◄─────────────────┤    Contribution      │
│                 │  GenericRelation └──────────────────────┘
│                 │
└────────┬────────┘
         │
         │ many-to-many (through DatasetLiteratureRelation)
         │
         ▼
┌─────────────────┐                  ┌──────────────────────────────┐
│ LiteratureItem  │◄─────────────────┤ DatasetLiteratureRelation    │
│                 │                  │   - dataset (FK)              │
└─────────────────┘                  │   - literature_item (FK)      │
                                     │   - relationship_type         │
                                     │     (DataCite types)          │
                                     └──────────────────────────────┘
```

---

## Database Indexes

**Performance-Critical Indexes**:

1. **DatasetDescription.description_type**: Required for cross-relationship filter performance (T122)
2. **DatasetDate.date_type**: Required for cross-relationship filter performance (T123)
3. **Dataset.visibility**: Default queryset filters on this field frequently
4. **Dataset.project_id**: Foreign key lookups common in filtering

**Index Strategy**:

- Add indexes after measuring actual query patterns in tests
- Balance query performance vs. write performance
- Monitor index usage in production via database analytics

---

## Data Migration Considerations

**Breaking Changes**:

1. **PROTECT behavior** (T042): Changing `project.on_delete` from CASCADE to PROTECT
   - **Impact**: Projects with datasets can no longer be deleted
   - **Migration**: No data migration needed; behavior change only
   - **Rollback**: Can revert to CASCADE if needed

2. **Privacy-first default** (T138): Changing default QuerySet to exclude PRIVATE
   - **Impact**: Existing views using `Dataset.objects.all()` will exclude private datasets
   - **Migration**: No data migration; code update needed in views
   - **Fix**: Use `Dataset.objects.get_all()` or `.with_private()` where private datasets needed

**Non-Breaking Changes**:

1. **DatasetLiteratureRelation** (T037): New intermediate model
   - **Impact**: Converts simple ManyToMany to through model
   - **Migration**: Django creates bridge table; existing relationships preserved
   - **Rollback**: Can remove through= parameter to revert

2. **Vocabulary validation** (T039-T041): Adding validators to type fields
   - **Impact**: New datasets must use valid vocabulary types
   - **Migration**: Validate existing data matches vocabulary or provide data cleanup
   - **Rollback**: Remove validators to revert

**Migration Order**:

1. Add DatasetLiteratureRelation model
2. Update Dataset.related_literature through= parameter
3. Add vocabulary validators to Description/Date/Identifier models
4. Change Dataset.project on_delete to PROTECT
5. Add database indexes for description_type and date_type

---

## Test Data Considerations

**Factory Defaults** (DatasetFactory):

- `name`: Faker-generated dataset name
- `visibility`: PRIVATE (matches default)
- `license`: CC BY 4.0 (matches default)
- `project`: SubFactory(ProjectFactory) - creates associated project
- `image`: Optional - can use Faker image for tests

**Related Factories**:

- `DatasetDescriptionFactory`: SubFactory(DatasetFactory), valid description_type
- `DatasetDateFactory`: SubFactory(DatasetFactory), valid date_type
- `DatasetIdentifierFactory`: SubFactory(DatasetFactory), valid identifier_type, DOI format
- `DatasetLiteratureRelationFactory`: SubFactory for both dataset and literature_item

**Test Scenarios**:

- Empty datasets (no samples/measurements)
- Orphaned datasets (project=null)
- Private/internal/public visibility combinations
- With/without DOI identifiers
- Various license types
- Multiple descriptions/dates/identifiers

---

## Edge Case Documentation

**Documented in plan.md Edge Case Resolutions section**:

1. **Orphaned datasets**: project=null permitted
2. **Duplicate names**: No unique constraint
3. **Visibility inheritance**: No automatic inheritance
4. **License changes**: Warning if DOI exists
5. **Literature deletion**: SET_NULL for reference, CASCADE for ManyToMany
6. **Empty datasets**: Allowed, flagged via has_data
7. **Contributor roles**: Validated against CONTRIBUTOR_ROLES
8. **Date types**: Validated against DATE_TYPES
9. **Description types**: Validated against DESCRIPTION_TYPES
10. **UUID collision**: Database constraint handles
11. **Image aspect ratio**: Research in T012, T014
12. **Filter performance**: Indexes in T122, T123
13. **Dynamic inlines**: get_formset() in T072, T073
14. **Generic search**: Defined scope in T116, T124
15. **Literature types**: DataCite vocabulary in T011

See [plan.md](plan.md) Edge Case Resolutions for detailed implementation guidance.
