# Implementation Plan: Core Measurement Model Enhancement

**Branch**: `006-core-measurements` | **Date**: February 16, 2026 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/006-core-measurements/spec.md`

## Summary

Enhance the existing `fairdm.core.measurement` app to match the architecture and quality level of `fairdm.core.sample` (Feature 005). This includes fixing vocabulary bugs, adding custom querysets, permissions, rich admin/forms/filters, and reusable base classes — all mirroring the established patterns from the sample app. No new database models are added; all changes are code-only with no migrations required.

## Technical Context

**Language/Version**: Python 3.11+ (Django 4.2+)
**Primary Dependencies**: django-polymorphic 3.1+, django-guardian 2.4+, django-filter 23.0+, django-crispy-forms 2.0+, django-select2, django-tables2 2.5+, research-vocabs
**Storage**: PostgreSQL (via Django ORM, no direct SQL)
**Testing**: pytest + pytest-django with factory-boy
**Target Platform**: Linux server (Docker), development on Windows
**Project Type**: Django app within FairDM framework
**Performance Goals**: Measurement list with 1000+ mixed polymorphic types loads <1s; QuerySet optimization reduces queries by 80%+
**Constraints**: No new database tables; no migrations (code-only changes); placeholder view only (full detail deferred); client-side views out of scope
**Scale/Scope**: ~10 files modified/created in core, ~8 test files, ~3 demo app updates

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. FAIR-First** | ✅ PASS | Fixes vocabulary bugs that break FAIR metadata compliance. Measurement-specific vocabularies for descriptions, dates, and roles ensure proper metadata categorization. |
| **II. Domain-Driven Declarative** | ✅ PASS | Uses declarative registration via registry. BaseMeasurementConfiguration provides declarative field specs. No ad-hoc runtime structures. |
| **III. Config Over Plumbing** | ✅ PASS | Registry auto-generates forms, tables, filters, admin. Portal devs configure fields, not plumbing. MeasurementFormMixin/FilterMixin reduce boilerplate. |
| **IV. Opinionated Defaults** | ✅ PASS | Provides sensible defaults for all auto-generated components. BaseMeasurementConfiguration defines standard field sets. Admin works out-of-the-box with polymorphic support. |
| **V. Test-First Quality** | ✅ PASS | Comprehensive test suite planned (8 test files mirroring source structure). Tests written before implementation per TDD discipline. |
| **VI. Documentation Critical** | ✅ PASS | Demo app updated as living documentation. Quickstart.md provides developer migration guide. Docstrings required on all new classes. |
| **VII. Living Demo** | ✅ PASS | Demo app gains measurement child admins and BaseMeasurementConfiguration usage. Demo measurement models demonstrate correct patterns. |

**Gate Result**: ✅ ALL PASS — No violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/006-core-measurements/
├── plan.md              # This file
├── research.md          # Phase 0 output — decision log & technology research
├── data-model.md        # Phase 1 output — entity descriptions & relationships
├── quickstart.md        # Phase 1 output — developer migration guide
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
fairdm/core/measurement/
├── __init__.py          # (no changes)
├── apps.py              # (no changes)
├── models.py            # FIX: vocabularies, manager, get_absolute_url
├── admin.py             # REWRITE: polymorphic parent+child admin with inlines
├── forms.py             # REWRITE: MeasurementFormMixin + MeasurementForm
├── filters.py           # REWRITE: MeasurementFilterMixin + MeasurementFilter
├── plugins.py           # FIX: inline model references
├── managers.py          # NEW: MeasurementQuerySet
├── permissions.py       # NEW: MeasurementPermissionBackend
├── config.py            # NEW: BaseMeasurementConfiguration
├── views.py             # (no changes)
└── urls.py              # (no changes)

fairdm/core/
└── admin.py             # MODIFY: remove old measurement admin classes

fairdm_demo/
├── admin.py             # MODIFY: add measurement child admins
└── config.py            # MODIFY: use BaseMeasurementConfiguration

tests/test_core/test_measurement/
├── __init__.py          # (exists)
├── conftest.py          # NEW: shared fixtures
├── test_models.py       # NEW: model creation, polymorphism, vocabularies
├── test_admin.py        # NEW: admin search, filters, inlines, polymorphic
├── test_forms.py        # NEW: validation, widgets, sample filtering
├── test_filters.py      # NEW: filter fields, search, cross-relationship
├── test_permissions.py  # NEW: permission backend, dataset inheritance
├── test_registry.py     # NEW: registry integration for measurement subtypes
└── test_integration.py  # ENHANCE: expand existing integration tests
```

**Structure Decision**: Follows existing Django app structure within `fairdm/core/measurement/`. Test structure mirrors source per constitution requirement. No new apps or packages created.

## Complexity Tracking

No constitution violations — table not needed.

## Implementation Phases

### Phase 1: Foundation — Models, Manager, Permissions (User Stories 1, 2, 7)

**Goal**: Fix model-level bugs and add core infrastructure that all other components depend on.

**Dependencies**: None — this is the foundation layer.

#### Tasks

**T001**: Fix vocabulary references in `models.py`

- Change `MeasurementDescription.VOCABULARY` from `from_collection("Sample")` to `from_collection("Measurement")`
- Change `MeasurementDate.VOCABULARY` from `from_collection("Sample")` to `from_collection("Measurement")`
- Vocabulary choices are provided at form level, validated at model level via `clean()` methods
- **No migration needed** — Abstract* base classes do not set database-level choices
- **Test**: Verify vocabulary choices match Measurement collection; model `clean()` rejects invalid types

**T002**: Create placeholder view and fix `get_absolute_url()` in `models.py` + `views.py` + `urls.py`

- Change `get_absolute_url()` from `return self.sample.get_absolute_url()` to `return reverse("measurement:overview", kwargs={"uuid": self.uuid})`
- Create placeholder `MeasurementDetailView(DetailView)` in `views.py`:
  - Use `template_name = "measurement/detail.html"`
  - MUST return HTTP 200 with measurement.name, measurement.uuid, dataset link, sample link, "Coming soon" message
- Register URL pattern `/measurements/<uuid>/` to route to placeholder view
- Create `templates/measurement/detail.html` with above content
- **Test**: Verify URL pattern returns `/measurements/{uuid}/` with HTTP 200; templates using `get_absolute_url()` don't break

**T003**: Create `managers.py` — MeasurementQuerySet

- Mirror `SampleQuerySet` pattern from `sample/managers.py`
- `with_related()`: `select_related("dataset", "sample", "sample__dataset")` + `prefetch_related("contributors", ...)`
- `with_metadata()`: `prefetch_related("descriptions", "dates", "identifiers")`
- Update `Measurement.objects` to use `PolymorphicManager.from_queryset(MeasurementQuerySet)()`
- **Test**: Query count assertions for with_related/with_metadata

**T004**: Create `permissions.py` — MeasurementPermissionBackend

- Mirror `SamplePermissionBackend` from `sample/permissions.py`
- Map measurement permissions to dataset permissions
- Register in `AUTHENTICATION_BACKENDS` (or document for portal developers)
- **Test**: Verify permission inheritance from dataset

**T005**: Fix `plugins.py` inline model references

- Change `inline_model = SampleDescription` → `MeasurementDescription`
- Change `inline_model = SampleDate` → `MeasurementDate`
- Fix docstrings referencing "dataset" context
- **Test**: Verify plugins use correct inline models

### Phase 2: Admin Interface (User Story 3)

**Goal**: Full polymorphic admin with correct vocabularies and inlines.

**Dependencies**: Phase 1 (vocabulary fixes, models working correctly)

#### Tasks

**T006**: Create measurement-specific admin inlines in `measurement/admin.py`

- `MeasurementDescriptionInline(admin.StackedInline)` — model=MeasurementDescription
- `MeasurementDateInline(admin.StackedInline)` — model=MeasurementDate
- `MeasurementIdentifierInline(admin.StackedInline)` — model=MeasurementIdentifier
- `MeasurementContributionInline(GenericTabularInline)` — model=Contribution
- Mirror inline configuration from `SampleDescriptionInline`, etc.

**T007**: Create NEW `MeasurementChildAdmin(PolymorphicChildModelAdmin)` in `measurement/admin.py`

- Mirror `SampleChildAdmin` from `sample/admin.py`
- `base_fieldsets` (tuple) with name, dataset, sample, uuid, timestamps
- `list_display`, `list_filter`, `search_fields`, `readonly_fields`, `autocomplete_fields`
- Include all 4 inlines from T006
- Custom `measurement_type()` display method
- This is a NEW class separate from the basic MeasurementAdmin in core/admin.py
- **Test**: Admin renders, search works, filters work, inlines save

**T008**: Create `MeasurementParentAdmin(PolymorphicParentModelAdmin)` in `measurement/admin.py`

- Mirror `SampleParentAdmin` from `sample/admin.py`
- Register with `@admin.register(Measurement)`
- `get_child_models()` returns `registry.measurements`
- Include `PolymorphicChildModelFilter` in list_filter
- **Test**: Type selection interface works, routing to child admin works

**T009**: Remove old basic measurement admin classes from `fairdm/core/admin.py`

- Remove the basic `MeasurementParentAdmin` class
- Remove the basic `MeasurementAdmin(PolymorphicChildModelAdmin)` class that existed before this feature
- These are being replaced by the new comprehensive admin classes created in T007/T008
- Remove related imports
- Keep `DescriptionInline` and `DateInline` if used elsewhere (for Dataset)
- **Test**: No import errors, admin still works

**T010**: Add measurement child admins to `fairdm_demo/admin.py`

- Create `ExampleMeasurementAdmin(MeasurementChildAdmin)` with demo-specific base_fieldsets
- Create `XRFMeasurementAdmin(MeasurementChildAdmin)` with element/concentration fields
- Create `ICP_MS_MeasurementAdmin(MeasurementChildAdmin)` with isotope/concentration fields
- **Test**: Demo measurement admin renders correctly for all 3 types

### Phase 3: Forms (User Story 4)

**Goal**: Rich measurement forms with autocomplete, dataset-scoped sample selection, and reusable mixin.

**Dependencies**: Phase 1 (models, permissions)

#### Tasks

**T011**: Create `MeasurementFormMixin` in `measurement/forms.py`

- Mirror `SampleFormMixin` from `sample/forms.py`
- Pop `request` from kwargs
- Configure `dataset` field: `ModelSelect2Widget`, guardian-filtered queryset
- Configure `sample` field: `ModelSelect2Widget`, filtered to samples in the selected dataset
- Create `FormHelper(form_tag=False)`
- **Test**: Mixin configures widgets correctly, sample queryset filtered by dataset

**T012**: Rewrite `MeasurementForm` in `measurement/forms.py`

- Inherit from `MeasurementFormMixin, forms.ModelForm`
- Use `fields` (not `exclude`) — include name, dataset, sample, image, tags
- Configure proper widgets and help_text with `gettext_lazy()`
- `clean()` prevents base Measurement instantiation
- **Test**: Form validates correctly, rejects base type, handles cross-dataset samples

### Phase 4: Filters (User Story 5)

**Goal**: Rich filtering with search, type selection, and cross-relationship queries.

**Dependencies**: Phase 1 (models, manager)

#### Tasks

**T013**: Create `MeasurementFilterMixin` in `measurement/filters.py`

- Mirror `SampleFilterMixin` from `sample/filters.py`
- `Meta.fields = ["dataset", "sample", "polymorphic_ctype"]`

**T014**: Rewrite `MeasurementFilter` in `measurement/filters.py`

- Inherit from `MeasurementFilterMixin, django_filters.FilterSet`
- `dataset` — ModelChoiceFilter with dynamic queryset
- `sample` — ModelChoiceFilter with dynamic queryset
- `polymorphic_ctype` — ModelChoiceFilter for measurement type
- `search` — CharFilter with custom method searching name + UUID
- `description` — CharFilter on `descriptions__text` (cross-relationship)
- `date_after`/`date_before` — DateFilter on `dates__date`
- Dynamic queryset initialization in `__init__`
- **Test**: Each filter works individually and in combination

### Phase 5: Configuration & Registry (User Stories 1, 6)

**Goal**: Base configuration class and demo app integration.

**Dependencies**: Phase 1-4 (all components exist)

#### Tasks

**T015**: Create `BaseMeasurementConfiguration` in `measurement/config.py`

- Mirror `BaseSampleConfiguration` from `sample/config.py`
- Define standard `fields`, `table_fields`, `form_fields`, `filterset_fields`, `serializer_fields`
- **Test**: Configuration creates valid auto-generated components

**T016**: Update `fairdm_demo/config.py` to use `BaseMeasurementConfiguration`

- Change demo measurement configs to inherit from `BaseMeasurementConfiguration` instead of `ModelConfiguration`
- Verify registry auto-generates correct components
- **Test**: Demo measurement models work with new base configuration

### Phase 6: Tests & Integration (User Stories 7, 8 + overarching)

**Goal**: Comprehensive test suite and end-to-end verification.

**Dependencies**: All previous phases

#### Tasks

**T017**: Create test fixtures in `conftest.py`

- Factory fixtures for Measurement, MeasurementDescription, MeasurementDate, MeasurementIdentifier
- Dataset and Sample fixtures for cross-relationship testing
- User fixtures with guardian permissions

**T018**: Write `test_models.py`

- Model creation and polymorphism
- Vocabulary validation (correct collections used)
- Cross-dataset sample linking
- `get_value()` and `print_value()` methods
- `clean()` prevents base instantiation
- `get_absolute_url()` returns correct pattern
- CASCADE/PROTECT behavior

**T019**: Write `test_admin.py`

- Parent admin type selection interface
- Child admin rendering with inlines
- Search by name/UUID
- Filter by dataset, sample, type
- Vocabulary correctness in inlines

**T020**: Write `test_forms.py`

- Form validation (valid/invalid data)
- Sample queryset filtered by dataset
- MeasurementFormMixin widget configuration
- Request context handling
- Base type rejection

**T021**: Write `test_filters.py`

- Individual filter fields
- Combined filters
- Search across name/UUID
- Cross-relationship filters (descriptions, dates)
- Polymorphic type filter

**T022**: Write `test_permissions.py`

- Direct measurement permissions
- Permission inheritance from dataset
- Cross-dataset permission boundaries
- Anonymous user handling

**T023**: Write `test_registry.py`

- Registration of polymorphic measurement types
- Auto-generated form/filter/table/admin
- BaseMeasurementConfiguration integration
- Admin inheritance validation

**T024**: Enhance `test_integration.py`

- End-to-end CRUD workflow
- Cross-dataset measurement-sample linking
- Permission-gated operations
- QuerySet optimization verification

### Phase 7: Documentation (Constitution Principle VI compliance)

**Goal**: Update all relevant documentation to reflect measurement app enhancements and maintain living documentation per Constitution Principle VII.

**Dependencies**: Phase 1-6 (implementation complete for accurate documentation)

#### Tasks

**T025**: Update overview documentation — `docs/overview/`

- Create or update `docs/overview/data-model.rst` to include measurement model architecture
- Document measurement-sample-dataset relationship flows with diagrams
- Explain polymorphic measurement pattern and how it mirrors sample pattern
- Document cross-dataset linking workflow and provenance tracking
- Add measurement lifecycle diagrams (creation → metadata → analysis workflow)
- **Test**: Docs build without errors, cross-references resolve

**T026**: Create measurement development guide — `docs/portal-development/measurements.rst`

- How to define custom measurement types (step-by-step with XRF example)
- Registration with registry using `BaseMeasurementConfiguration`
- Creating custom admin classes inheriting from `MeasurementChildAdmin`
- Custom form/filter development using mixins
- QuerySet optimization patterns with `with_related()` and `with_metadata()`
- Permission configuration and dataset inheritance
- **Test**: Code examples in docs execute successfully

**T027**: Update registry documentation — `docs/portal-development/registry.rst`

- Add measurement-specific registration examples
- Document `BaseMeasurementConfiguration` field options
- Explain polymorphic admin validation rules for measurements
- Add troubleshooting section for common measurement registration issues
- **Test**: Examples match current registry API

**T028**: Create measurement admin guide — `docs/portal-administration/measurements-admin.rst`

- How to use polymorphic admin type selection interface
- Managing measurement metadata (descriptions, dates, identifiers, contributors)
- Bulk operations and filtering strategies
- Vocabulary management for measurement types
- Troubleshooting common admin issues
- **Test**: Screenshots/examples reflect actual admin interface

**T029**: Update API documentation (if REST API exposed)

- Document measurement endpoints structure
- Explain polymorphic type handling in API responses
- Document filtering query parameters
- Add measurement API usage examples
- **Test**: API examples return expected responses

**T030**: Update deployment/upgrade guide

- Document vocabulary validation approach (code-only, no migrations)
- Provide data audit checklist for existing portals
- Explain breaking changes and backward compatibility
- Deployment troubleshooting section
- **Test**: Deployment steps validated on test environment

**T031**: Add inline code documentation (docstrings)

- Comprehensive docstrings for `MeasurementQuerySet` methods
- `MeasurementFormMixin` and `MeasurementFilterMixin` usage docs
- `MeasurementChildAdmin` and `MeasurementParentAdmin` configuration guide
- `BaseMeasurementConfiguration` field options
- Link docstrings to relevant documentation sections
- **Test**: Sphinx autodoc generates complete API reference

## Task Dependency Graph

```
T001 (vocab fix) ─────┐
T002 (URL fix) ────────┤
T003 (queryset) ───────┼──→ T006-T010 (admin) ──→ T010 (demo admin)
T004 (permissions) ────┤                          T016 (demo config)
T005 (plugins fix) ────┘
                       │
                       ├──→ T011-T012 (forms)
                       │
                       ├──→ T013-T014 (filters)
                       │
                       └──→ T015 (config) ──→ T016 (demo config)

T017-T024 (tests) run alongside each phase per TDD discipline

T025-T031 (docs) run after implementation complete (phases 1-6)
```

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Invalid vocabulary data fails validation | Low (pre-production) | Medium | Data audit required before deployment; existing invalid types fail on save |
| ContributionInline is broken (model commented out) | Medium | Low | Create dedicated MeasurementContributionInline; don't depend on contrib inline |
| Registry validation rejects new admin pattern | Low | Medium | Admin inheritance validation already exists in config.py for measurements |
| Sample-dataset membership enforcement not yet implemented | Medium | Medium | Form-level filtering is sufficient; database constraint can be added later |
| URL pattern for measurement detail view 404s | Expected | Low | Intentional — detail view deferred to future feature |

## Migration Checklist

- ⚠️ **No migrations needed for this feature**
- Vocabulary changes are code-only (form-level choices, model-level validation)
- Manager changes are code-only (no schema impact)
- Permission backend registration documented but not auto-configured
- Abstract* base classes do not set database-level choices by design

## Summary

**Feature**: 006-core-measurements — Core Measurement Model Enhancement
**Phases**: 7 | **Tasks**: 31 | **Status**: Ready for implementation

### Phase Breakdown

| Phase | Focus | Tasks | Dependencies |
|-------|-------|-------|--------------|
| 1 | Foundation — models, manager, permissions | T001–T005 | None |
| 2 | Admin — polymorphic parent/child, inlines | T006–T010 | Phase 1 |
| 3 | Forms — mixin, autocomplete, dataset-scoped samples | T011–T012 | Phase 1 |
| 4 | Filters — search, type, cross-relationship | T013–T014 | Phase 1 |
| 5 | Configuration & registry integration | T015–T016 | Phase 1-4 |
| 6 | Tests & integration verification | T017–T024 | Ongoing (TDD) |
| 7 | Documentation — overview, guides, API reference | T025–T031 | Phase 1-6 complete |

### Key Deliverables

**Code** (10 modified + 3 new files):

- 3 new files: `managers.py`, `permissions.py`, `config.py`
- 6 modified core files: `models.py`, `admin.py`, `forms.py`, `filters.py`, `plugins.py`, `core/admin.py`
- 2 demo app updates: `admin.py`, `config.py`
- 8 comprehensive test files

**Documentation** (7 tasks):

- Overview documentation with flows and relationships
- Portal development guide for custom measurements
- Admin guide for portal administrators
- API reference documentation
- Migration/upgrade guide
- Inline docstrings with Sphinx autodoc

### Success Criteria

✅ All 7 Constitution principles pass
✅ Mirrors `fairdm.core.sample` architecture completely
✅ Fixes 4 critical bugs (vocabularies, plugins, form, URL)
✅ 80%+ query reduction with optimization methods
✅ Comprehensive test coverage across 8 test files
✅ Complete documentation per Principle VI
✅ Demo app as living documentation per Principle VII

**Next**: Run `/speckit.tasks` to generate detailed task breakdown with acceptance criteria.
