# Research: Core Measurement Model Enhancement

**Feature**: 006-core-measurements | **Date**: February 16, 2026

## Decision Log

### D1: Vocabulary Validation Strategy

- **Decision**: Vocabulary changes do NOT create database migrations. CharField choices are not enforced at the database level. Validation happens at the model level via `clean()` and `save()` methods.
- **Rationale**: FairDM's `Abstract*` base classes (AbstractDescription, AbstractDate) intentionally do not set `choices` on CharField to avoid schema migrations. Vocabulary enforcement is handled at form rendering (via `from_collection()`) and model validation (via `.clean()` method). This allows vocabulary updates without database changes.
- **Implementation**: Change `VOCABULARY = from_collection("Sample")` to `from_collection("Measurement")` in code only. Existing records with invalid types will fail validation on next save — requires data audit before deployment.
- **Alternatives considered**: (A) Database-level choices enforcement — rejected because it requires migrations for vocabulary updates and violates FairDM design pattern. (B) No validation — rejected because it allows data integrity issues.

### D2: Measurement `get_absolute_url()` Strategy

- **Decision**: Return `/measurements/{uuid}/` URL pattern even though detail view is deferred
- **Rationale**: URL patterns should be defined early to prevent broken references in templates, admin, and API responses. Views can return 404 until implemented.
- **Alternatives considered**: (A) Return `sample.get_absolute_url()` as current — rejected because it's semantically wrong and creates confusion about which entity is being linked.

### D3: Sample Selection for Measurements

- **Decision**: Filtered queryset limited to samples included in the measurement's dataset. Users first add samples to dataset, then create measurements.
- **Rationale**: This enforces a clean workflow: dataset membership is a prerequisite for measurement creation. It prevents orphaned cross-references and aligns with dataset-scoped permissions.
- **Alternatives considered**: (A) Show all accessible samples — rejected because it bypasses dataset membership requirements. (B) Two-step wizard — rejected as over-engineered for current needs.

### D4: Polymorphic Admin Architecture

- **Decision**: Mirror Sample app pattern — `MeasurementParentAdmin(PolymorphicParentModelAdmin)` + `MeasurementChildAdmin(PolymorphicChildModelAdmin)` with registry-based child discovery
- **Rationale**: Consistency with Sample app ensures predictable developer experience. The pattern is proven and already partially implemented in `fairdm/core/admin.py`.
- **Alternatives considered**: (A) Separate admin per type — rejected because it loses the unified list view. (B) Single admin — rejected because it can't show subclass-specific fields.

### D5: QuerySet Prefetch Strategy

- **Decision**: Balanced prefetching — `with_related()` for direct relationships (sample, dataset, contributors), `with_metadata()` for metadata models (descriptions, dates, identifiers). Deep nesting left to views.
- **Rationale**: Covers the most common access patterns without over-fetching. Views that need `sample.dataset` or `contributor.person.organization` can chain additional `select_related()`.
- **Alternatives considered**: (A) Aggressive prefetch — rejected because it loads data many views don't need. (C) Minimal prefetch — rejected because it doesn't prevent the most common N+1 queries.

## Technology Research

### Polymorphic Admin — django-polymorphic

The `PolymorphicParentModelAdmin` / `PolymorphicChildModelAdmin` pattern from `django-polymorphic` is already used successfully for Sample. Key implementation notes:

- **`base_fieldsets`** must be a **tuple** (not list) so polymorphic admin can append subclass fields
- **`get_child_models()`** on the parent admin returns registered models dynamically from `registry.measurements`
- **`PolymorphicChildModelFilter`** enables list filtering by subtype
- Child admins set `base_model = Measurement` to enable routing
- Registry validation already enforces admin inheritance via `_validate_admin_inheritance()` in `config.py`

### Permission Backend — django-guardian

The `SamplePermissionBackend` pattern maps sample-level permissions to parent dataset permissions. The measurement equivalent should:

1. Check direct measurement permission via guardian
2. Fall back to dataset permission mapping:
   - `measurement.view_measurement` → `dataset.view_dataset`
   - `measurement.change_measurement` → `dataset.change_dataset`
   - `measurement.delete_measurement` → `dataset.delete_dataset`
   - `measurement.add_measurement` → `dataset.change_dataset`
   - `measurement.import_data` → `dataset.import_data`

### Form Widgets — django-autocomplete-light / django-select2

The `SampleFormMixin` pattern uses:

- `ModelSelect2Widget` for FK fields (dataset, location)
- `AddAnotherWidgetWrapper` for dataset field
- Guardian-based queryset filtering for dataset choices
- `crispy_forms.helper.FormHelper` with `form_tag = False`

The measurement form should mirror this, adding:

- Sample field filtered to dataset's samples
- Dataset field with guardian permissions

### FilterSet Pattern — django-filter

The `SampleFilter` pattern includes:

- `SampleFilterMixin` with base `Meta.fields`
- Dynamic queryset initialization in `__init__`
- Cross-relationship filters (e.g., `descriptions__text`, `dates__date`)
- Custom search method spanning multiple fields
- `polymorphic_ctype` filter for type selection

## Component Mapping: Sample → Measurement

| Sample Component | File | Measurement Equivalent | Status |
|---|---|---|---|
| `SampleQuerySet` | `sample/managers.py` | `MeasurementQuerySet` | **CREATE** |
| `SampleFormMixin` | `sample/forms.py` | `MeasurementFormMixin` | **CREATE** |
| `SampleForm` | `sample/forms.py` | `MeasurementForm` | **REWRITE** |
| `SampleFilterMixin` | `sample/filters.py` | `MeasurementFilterMixin` | **CREATE** |
| `SampleFilter` | `sample/filters.py` | `MeasurementFilter` | **REWRITE** |
| `SampleChildAdmin` | `sample/admin.py` | `MeasurementChildAdmin` | **MOVE+ENHANCE** (from `core/admin.py`) |
| `SampleParentAdmin` | `sample/admin.py` | `MeasurementParentAdmin` | **MOVE+ENHANCE** (from `core/admin.py`) |
| `SamplePermissionBackend` | `sample/permissions.py` | `MeasurementPermissionBackend` | **CREATE** |
| `BaseSampleConfiguration` | `sample/config.py` | `BaseMeasurementConfiguration` | **CREATE** |
| 5 inlines | `sample/admin.py` | 4 inlines (no SampleRelation equivalent) | **CREATE** |
| `SampleDescription.VOCABULARY` | `sample/models.py` | `MeasurementDescription.VOCABULARY` | **FIX** |
| `SampleDate.VOCABULARY` | `sample/models.py` | `MeasurementDate.VOCABULARY` | **FIX** |

## Files to Create

1. `fairdm/core/measurement/managers.py` — MeasurementQuerySet
2. `fairdm/core/measurement/permissions.py` — MeasurementPermissionBackend
3. `fairdm/core/measurement/config.py` — BaseMeasurementConfiguration
4. `docs/portal-development/measurements.rst` — Custom measurement development guide
5. `docs/portal-administration/measurements-admin.rst` — Admin user guide
6. `docs/overview/measurements-data-model.rst` or update existing data model docs — Architecture and flows

## Files to Modify

1. `fairdm/core/measurement/models.py` — Fix vocabularies, add custom manager
2. `fairdm/core/measurement/admin.py` — Full polymorphic admin with inlines
3. `fairdm/core/measurement/forms.py` — Rewrite with mixin pattern
4. `fairdm/core/measurement/filters.py` — Rewrite with rich filtering
5. `fairdm/core/measurement/plugins.py` — Fix inline model references
6. `fairdm/core/admin.py` — Remove old measurement admin classes (moved to measurement/admin.py)
7. `fairdm_demo/admin.py` — Add measurement child admins for demo models
8. `fairdm_demo/config.py` — Update to use BaseMeasurementConfiguration
9. `docs/portal-development/registry.rst` — Add measurement registration examples
10. `docs/overview/data-model.rst` (or similar) — Add measurement architecture section

## Test Files to Create

Following test structure mirroring source (`tests/test_core/test_measurement/`):

1. `conftest.py` — Fixtures using factory-boy
2. `test_models.py` — Model creation, polymorphism, validation, vocabularies
3. `test_admin.py` — Admin search, filters, inlines, polymorphic handling
4. `test_forms.py` — Form validation, widgets, sample filtering
5. `test_filters.py` — Filter fields, search, cross-relationship queries
6. `test_permissions.py` — Permission backend, dataset inheritance
7. `test_integration.py` — End-to-end CRUD, cross-dataset linking
8. `test_registry.py` — Registry integration for measurement subtypes

## Migration Considerations

### No Database Migrations Required

All changes in this feature are code-only with no database schema modifications:

**Vocabulary Changes** (Code-only):

- Changing `MeasurementDescription.VOCABULARY` and `MeasurementDate.VOCABULARY` from `from_collection("Sample")` to `from_collection("Measurement")`
- **No migration generated** — `Abstract*` base classes (AbstractDescription, AbstractDate) do not set database-level `choices` on CharField
- Validation happens at model level via `.clean()` methods, not at database level
- Existing records with invalid vocabulary types will fail validation on next save (data audit required)

**Manager Changes** (Code-only):

- Adding `objects = PolymorphicManager.from_queryset(MeasurementQuerySet)()` does NOT require migration
- Managers are not stored in database schema

**All Other Changes** (Code-only):

- Forms, filters, admin classes, permissions, config classes — all application layer only
- No new fields, no schema alterations, no database constraints added

**Deployment Note**: Run data audit before deploying to ensure existing measurements have valid vocabulary types.
