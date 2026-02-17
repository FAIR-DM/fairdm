# Data Model: Core Measurement Enhancement

**Feature**: 006-core-measurements | **Date**: February 16, 2026

## Entity Overview

This feature does NOT add new database models. It enhances the existing Measurement model and its metadata models with correct vocabularies, custom querysets, permissions, forms, filters, and admin configuration — mirroring what Feature 005 delivered for Samples.

## Existing Models (to be enhanced)

### Measurement (BasePolymorphicModel)

```
┌─────────────────────────────────────────────┐
│ Measurement (fairdm.core.measurement)       │
├─────────────────────────────────────────────┤
│ PK: id (auto)                               │
│ FK: dataset → Dataset (CASCADE)             │
│ FK: sample → Sample (PROTECT)               │
│ FK: polymorphic_ctype → ContentType         │
│    uuid: ShortUUIDField (prefix="m")        │
│    name: CharField (from BaseModel)         │
│    image: ImageField (from BaseModel)       │
│    keywords: M2M→Concept (from BaseModel)   │
│    tags: TaggableManager (from BaseModel)   │
│    options: JSONField (from BaseModel)       │
│    added: DateTimeField (auto)              │
│    modified: DateTimeField (auto)           │
│    contributors: GenericRelation            │
├─────────────────────────────────────────────┤
│ VOCABULARY FIXES:                           │
│    CONTRIBUTOR_ROLES = from_collection("Measurement") ✓ │
│    DESCRIPTION_TYPES = from_collection("Measurement") ← FIX │
│    DATE_TYPES = from_collection("Measurement") ← FIX │
├─────────────────────────────────────────────┤
│ MANAGER CHANGE:                             │
│    objects = PolymorphicManager              │
│      .from_queryset(MeasurementQuerySet)()  │
├─────────────────────────────────────────────┤
│ Methods:                                    │
│    get_value() → value ± uncertainty        │
│    print_value() → human-readable string    │
│    get_absolute_url() → /measurements/{uuid}/ ← FIX │
│    clean() → prevent base instantiation     │
│    type_of → classproperty → Measurement    │
│    get_template_name() → template list      │
├─────────────────────────────────────────────┤
│ Meta:                                       │
│    ordering = ["-modified"]                 │
│    permissions = CORE_PERMISSIONS + import  │
│    default_related_name = "measurements"    │
└─────────────────────────────────────────────┘
```

### MeasurementDescription (AbstractDescription)

```
┌──────────────────────────────────────────────┐
│ MeasurementDescription                       │
├──────────────────────────────────────────────┤
│ FK: related → Measurement (CASCADE)          │
│    type: CharField (choices from vocabulary) │
│    value: TextField                          │
├──────────────────────────────────────────────┤
│ VOCABULARY FIX:                              │
│    from_collection("Sample")                 │
│    → from_collection("Measurement")          │
├──────────────────────────────────────────────┤
│ Constraint: unique(related, type)            │
└──────────────────────────────────────────────┘
```

### MeasurementDate (AbstractDate)

```
┌──────────────────────────────────────────────┐
│ MeasurementDate                              │
├──────────────────────────────────────────────┤
│ FK: related → Measurement (CASCADE)          │
│    type: CharField (choices from vocabulary) │
│    value: PartialDateField                   │
├──────────────────────────────────────────────┤
│ VOCABULARY FIX:                              │
│    from_collection("Sample")                 │
│    → from_collection("Measurement")          │
├──────────────────────────────────────────────┤
│ Constraint: unique(related, type)            │
└──────────────────────────────────────────────┘
```

### MeasurementIdentifier (AbstractIdentifier)

```
┌──────────────────────────────────────────────┐
│ MeasurementIdentifier                        │
├──────────────────────────────────────────────┤
│ FK: related → Measurement (CASCADE)          │
│    type: CharField (choices from vocabulary) │
│    value: CharField (unique, indexed)        │
├──────────────────────────────────────────────┤
│ No changes needed — already uses             │
│ FairDMIdentifiers() (correct)                │
└──────────────────────────────────────────────┘
```

## New Components (code-only, no migrations)

### MeasurementQuerySet

```
MeasurementQuerySet(PolymorphicQuerySet)
├── with_related()
│   ├── select_related("dataset", "sample", "sample__dataset")
│   └── prefetch_related("contributors", "contributors__contributor", "contributors__roles")
├── with_metadata()
│   └── prefetch_related("descriptions", "dates", "identifiers")
└── (no hierarchy methods — measurements don't have parent/child relationships)
```

### MeasurementPermissionBackend

```
MeasurementPermissionBackend(ObjectPermissionBackend)
└── has_perm(user, perm, obj)
    ├── Check direct measurement permission (guardian)
    └── Fallback: map to dataset permission
        ├── view_measurement → view_dataset
        ├── change_measurement → change_dataset
        ├── delete_measurement → delete_dataset
        ├── add_measurement → change_dataset
        └── import_data → import_data
```

### BaseMeasurementConfiguration

```
BaseMeasurementConfiguration(ModelConfiguration)
├── fields = ["name", "dataset", "sample", "image"]
├── table_fields = ["name", "dataset", "sample", "added", "modified"]
├── form_fields = ["name", "dataset", "sample", "image"]
├── filterset_fields = ["dataset", "sample"]
└── serializer_fields = ["id", "uuid", "name", "dataset", "sample", "added", "modified"]
```

## Relationships

```
Project ──1:N──→ Dataset ──1:N──→ Measurement
                     │                  │
                     └──1:N──→ Sample ←─┘ (FK, PROTECT)
                                        │
                                        ├── MeasurementDescription (CASCADE)
                                        ├── MeasurementDate (CASCADE)
                                        ├── MeasurementIdentifier (CASCADE)
                                        └── Contribution (GenericRelation)
```

**Key constraint**: `Measurement.sample` must be a sample that is included in `Measurement.dataset`. This is enforced via form-level queryset filtering, not database-level constraint.

## Sample Selection Workflow

```
1. User creates/manages Dataset A
2. User adds samples to Dataset A:
   a. Create new sample directly in Dataset A
   b. OR add reference to existing sample from Dataset B
3. User creates measurement in Dataset A:
   - Sample field shows only samples included in Dataset A
   - Measurement.dataset = Dataset A (auto-set from context)
   - Measurement.sample = selected sample from Dataset A's pool
```
