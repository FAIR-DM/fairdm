# Tasks: Core Sample Model Enhancement

**Feature**: 007-core-samples | **Branch**: 007-core-samples
**Input**: Design documents from `/specs/007-core-samples/`
**Prerequisites**: ✅ plan.md, ✅ spec.md, ✅ research.md, ✅ data-model.md, ✅ quickstart.md

**Tests**: Test tasks are included per Constitution Principle V (test-first discipline) and Feature 007 test requirements.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `- [ ] [ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Implementation Strategy

**MVP Scope**: User Story 1 (Polymorphism & Registry) + User Story 2 (Admin Interface)

- These P1 stories deliver core polymorphic sample functionality with basic CRUD via admin
- Forms, filters, and advanced features follow incrementally

**Test-First**: All test tasks MUST be completed before their corresponding implementation tasks

**Demo App Updates**: Per Constitution Principle VII, demo app updates happen alongside feature implementation

---

## Phase 1: Setup & Project Structure

**Purpose**: Branch setup, dependency verification, and structural preparation

- [ ] T001 Create feature branch `007-core-samples` from main
- [ ] T002 Verify django-polymorphic 3.1+ installed in poetry environment
- [ ] T003 [P] Verify research-vocabs package available with controlled vocabularies
- [ ] T004 [P] Verify shortuuid 1.0+ installed for UUID generation
- [ ] T005 Review Feature 004 (registry) and Feature 006 (datasets) implementation for integration patterns

---

## Phase 2: Foundational Models & Infrastructure (BLOCKING)

**Purpose**: Core Sample model and SampleRelation model MUST exist before any user story work

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Create SampleQuerySet manager in fairdm/core/sample/managers.py
- [X] T007 Enhance Sample model in fairdm/core/sample/models.py with polymorphic base, UUID field, IGSN fields (sample_type, material), image field, django-taggit keywords/tags fields, ManyToMany 'related' field with symmetrical=False through SampleRelation, convenience methods get_all_relationships() and get_related_samples(), SampleQuerySet manager (note: metadata models use concrete FK, only contributors uses GenericRelation)
- [X] T008 [P] Create SampleRelation model in fairdm/core/sample/models.py with source/target FKs, relationship_type, circular validation in clean()
- [X] T009 [P] Create SampleDescription model in fairdm/core/models/sample_description.py extending AbstractDescription
- [X] T010 [P] Create SampleDate model in fairdm/core/models/sample_date.py extending AbstractDate
- [X] T011 [P] Create SampleIdentifier model in fairdm/core/models/sample_identifier.py extending AbstractIdentifier with IGSN validation
- [ ] T012 Generate and apply migrations for Sample, SampleRelation, and metadata models
- [X] T013 Update fairdm/core/sample/**init**.py to export new models

**Checkpoint**: Sample model foundation complete - user story implementation can now proceed

**Note on T012**: Migration generation blocked by unrelated AttributeError in dataset models ('PrefetchBase' object has no setter). This appears to be a pre-existing issue. The code changes for Phase 2 are complete and ready for migration once the dataset issue is resolved.

---

## Phase 3: User Story 1 - Polymorphism & Registry Integration (Priority: P1) 🎯 MVP

**Goal**: Enable polymorphic sample types that seamlessly integrate with Feature 004 registry system for auto-generated forms, filters, tables, and admin

**Independent Test**: Define custom RockSample/WaterSample models, register them, verify polymorphic queries return correct subclass instances, and verify auto-generated components work

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T014 [P] [US1] Unit test for SampleQuerySet.with_related() in tests/unit/core/models/test_sample_queryset.py
- [ ] T015 [P] [US1] Unit test for SampleQuerySet.with_metadata() in tests/unit/core/models/test_sample_queryset.py
- [ ] T016 [P] [US1] Unit test for polymorphic Sample query returning correct subclass instances in tests/unit/core/models/test_sample_polymorphic.py
- [ ] T017 [P] [US1] Integration test for custom sample type registration via Feature 004 registry in tests/integration/registry/test_sample_registration.py
- [ ] T018 [US1] Integration test for auto-generated form/filter/table for custom sample type in tests/integration/registry/test_sample_components.py

### Implementation for User Story 1

- [ ] T019 [P] [US1] Implement SampleQuerySet.with_related() prefetching dataset, location, contributors in fairdm/core/managers/sample.py
- [ ] T020 [P] [US1] Implement SampleQuerySet.with_metadata() prefetching descriptions, dates, identifiers in fairdm/core/managers/sample.py
- [ ] T021 [US1] Implement SampleQuerySet.by_relationship() filtering by relationship type in fairdm/core/managers/sample.py
- [ ] T022 [US1] Add registry integration hooks to Sample model for auto-component generation in fairdm/core/models/sample.py
- [ ] T023 [US1] Verify polymorphic queries work correctly (Sample.objects.all() returns subclass instances)
- [ ] T024 [P] [US1] Create RockSample demo model in fairdm_demo/models.py with mineral_type, hardness, grain_size fields
- [ ] T025 [P] [US1] Create WaterSample demo model in fairdm_demo/models.py with ph_level, temperature, dissolved_oxygen fields
- [ ] T026 [US1] Generate and apply migrations for demo sample types
- [ ] T027 [US1] Register RockSample in fairdm_demo/config.py using Feature 004 registry patterns with fields configuration
- [ ] T028 [US1] Register WaterSample in fairdm_demo/config.py using Feature 004 registry patterns with fields configuration
- [ ] T029 [US1] Verify auto-generated forms for RockSample/WaterSample handle both base and custom fields correctly
- [ ] T030 [US1] Update fairdm_demo/factories.py with RockSampleFactory and WaterSampleFactory for testing

**Checkpoint**: Polymorphic samples with registry integration fully functional

---

## Phase 4: User Story 2 - Enhanced Admin Interface (Priority: P1) 🎯 MVP

**Goal**: Comprehensive Django admin for samples with search, filtering, inline metadata editing, and polymorphic type handling

**Independent Test**: Access admin, search by name/local_id/uuid, apply filters (dataset, status), edit sample with inline descriptions/dates/identifiers, verify polymorphic types display correctly

### Tests for User Story 2

- [ ] T031 [P] [US2] Admin integration test for sample search functionality in tests/integration/admin/test_sample_admin_search.py
- [ ] T032 [P] [US2] Admin integration test for sample filtering (dataset, status, location) in tests/integration/admin/test_sample_admin_filters.py
- [ ] T033 [US2] Admin integration test for inline metadata editing (descriptions, dates, identifiers) in tests/integration/admin/test_sample_admin_inlines.py

### Implementation for User Story 2

- [ ] T034 [US2] Create SampleAdmin base class in fairdm/core/admin/sample.py with search_fields (name, local_id, uuid)
- [ ] T035 [US2] Add list_filter configuration to SampleAdmin (dataset, status, polymorphic_ctype) in fairdm/core/admin/sample.py
- [ ] T036 [US2] Add list_display configuration showing name, local_id, dataset, status, sample_type, added in fairdm/core/admin/sample.py
- [ ] T037 [P] [US2] Create DescriptionInline for SampleDescription in fairdm/core/admin/sample.py with tabular format
- [ ] T038 [P] [US2] Create DateInline for SampleDate in fairdm/core/admin/sample.py with tabular format
- [ ] T039 [P] [US2] Create IdentifierInline for SampleIdentifier in fairdm/core/admin/sample.py with tabular format
- [ ] T040 [P] [US2] Create RelationshipInline for SampleRelation in fairdm/core/admin/sample.py with autocomplete foreign keys
- [ ] T041 [US2] Add inlines to SampleAdmin (descriptions, dates, identifiers, relationships) with max_num limits dynamically calculated from vocabulary sizes (FR-048)
- [ ] T042 [US2] Configure autocomplete_fields for dataset and location in SampleAdmin
- [ ] T043 [US2] Add polymorphic type column display in admin list view
- [ ] T044 [US2] Register SampleAdmin with admin.site.register() in fairdm/core/admin/**init**.py
- [ ] T045 [P] [US2] Create RockSampleAdmin extending SampleAdmin in fairdm_demo/admin.py
- [ ] T046 [P] [US2] Create WaterSampleAdmin extending SampleAdmin in fairdm_demo/admin.py
- [ ] T047 [US2] Register RockSampleAdmin and WaterSampleAdmin in fairdm_demo/admin.py

**Checkpoint**: Admin interface complete with full CRUD, search, filtering, and inline editing

---

## Phase 5: User Story 3 - Robust Forms with Dataset Context (Priority: P2)

**Goal**: Sample forms that filter querysets by dataset context, provide clear help text, use appropriate widgets, handle polymorphic types, with reusable SampleFormMixin

**Independent Test**: Instantiate SampleForm with dataset context, render form, verify dataset field shows only accessible datasets, submit valid/invalid data, verify validation messages

### Tests for User Story 3

- [ ] T048 [P] [US3] Unit test for SampleForm field configuration in tests/unit/core/forms/test_sample_form.py
- [ ] T049 [P] [US3] Unit test for SampleFormMixin providing base field widgets in tests/unit/core/forms/test_sample_form_mixin.py
- [ ] T050 [US3] Integration test for form rendering with dataset context filtering in tests/integration/forms/test_sample_form_context.py
- [ ] T051 [US3] Integration test for form validation (required fields, location format) in tests/integration/forms/test_sample_form_validation.py

### Implementation for User Story 3

- [ ] T052 [US3] Create SampleFormMixin in fairdm/core/forms/sample.py with base widgets (dataset autocomplete, status select, location widget)
- [ ] T053 [US3] Create SampleForm extending ModelForm and SampleFormMixin in fairdm/core/forms/sample.py
- [ ] T054 [US3] Implement **init** method accepting request parameter for dataset filtering in SampleForm
- [ ] T055 [US3] Configure crispy-forms layout for SampleForm with fieldsets (Identification, Location, Status, Metadata) in fairdm/core/forms/sample.py
- [ ] T056 [US3] Add field help_text for all Sample fields (name, local_id, dataset, status, location, sample_type, material)
- [ ] T057 [US3] Implement clean_location() validation for coordinate format in SampleForm
- [ ] T058 [US3] Set default value for status field ("available") in SampleForm
- [ ] T058.5 [US3] Implement "add another" popup functionality for dataset field using django-addanother in SampleForm (FR-025)
- [ ] T059 [P] [US3] Create RockSampleForm extending SampleForm in fairdm_demo/forms.py with custom fields (mineral_type, hardness, grain_size)
- [ ] T060 [P] [US3] Create WaterSampleForm extending SampleForm in fairdm_demo/forms.py with custom fields (ph_level, temperature, dissolved_oxygen)
- [ ] T061 [US3] Update RockSample registry configuration to use RockSampleForm in fairdm_demo/config.py
- [ ] T062 [US3] Update WaterSample registry configuration to use WaterSampleForm in fairdm_demo/config.py

**Checkpoint**: Forms with dataset context filtering, validation, and reusable mixins complete

---

## Phase 6: User Story 4 - Advanced Filtering & Search (Priority: P2)

**Goal**: Filter samples by dataset, status, location, date ranges, polymorphic type, and search by name/local_id/keywords with reusable SampleFilterMixin

**Independent Test**: Create samples with various attributes, apply different filter combinations (dataset AND status, location radius, polymorphic type), verify results correctly narrowed

### Tests for User Story 4

- [ ] T063 [P] [US4] Unit test for SampleFilter field configuration in tests/unit/core/filters/test_sample_filter.py
- [ ] T064 [P] [US4] Unit test for SampleFilterMixin providing base filters in tests/unit/core/filters/test_sample_filter_mixin.py
- [ ] T065 [US4] Integration test for filtering by dataset, status, location in tests/integration/filters/test_sample_filter_combinations.py
- [ ] T066 [US4] Integration test for polymorphic type filtering in tests/integration/filters/test_sample_filter_polymorphic.py
- [ ] T067 [US4] Integration test for generic search across name and local_id in tests/integration/filters/test_sample_filter_search.py

### Implementation for User Story 4

- [ ] T068 [US4] Create SampleFilterMixin in fairdm/core/filters/sample.py with base filters (status, dataset, location)
- [ ] T069 [US4] Create SampleFilter extending FilterSet and SampleFilterMixin in fairdm/core/filters/sample.py
- [ ] T070 [US4] Add status filter with MultipleChoiceFilter using FairDMSampleStatus vocabulary in SampleFilter
- [ ] T071 [US4] Add dataset filter with ModelChoiceFilter using autocomplete widget in SampleFilter
- [ ] T072 [US4] Add date_range filter with DateFromToRangeFilter for added field in SampleFilter
- [ ] T073 [US4] Add polymorphic_ctype filter for filtering by sample type in SampleFilter
- [ ] T074 [US4] Add generic search filter (SearchFilter) matching name, local_id in SampleFilter
- [ ] T075 [US4] Implement cross-relationship filters for description content and date types in SampleFilter (FR-036, FR-037)
- [ ] T076 [P] [US4] Create RockSampleFilter extending SampleFilter in fairdm_demo/filters.py with custom filters (mineral_type, hardness range, grain_size)
- [ ] T077 [P] [US4] Create WaterSampleFilter extending SampleFilter in fairdm_demo/filters.py with custom filters (ph_level range, temperature range)
- [ ] T078 [US4] Update RockSample registry configuration to use RockSampleFilter in fairdm_demo/config.py
- [ ] T079 [US4] Update WaterSample registry configuration to use WaterSampleFilter in fairdm_demo/config.py

**Checkpoint**: Filtering system with mixins and polymorphic type support complete

---

## Phase 7: User Story 5 - Sample Relationships & Provenance (Priority: P3)

**Goal**: Define typed relationships between samples (parent-child, derived-from, split-from) to track sample provenance and hierarchies

**Independent Test**: Create parent sample, establish relationships to child samples with different types, query relationships bidirectionally, attempt circular relationship and verify prevention

### Tests for User Story 5

- [ ] T080 [P] [US5] Unit test for SampleRelation.clean() preventing self-reference in tests/unit/core/models/test_sample_relation.py
- [ ] T081 [P] [US5] Unit test for SampleRelation.clean() preventing direct circular relationships in tests/unit/core/models/test_sample_relation.py
- [ ] T082 [US5] Unit test for SampleRelation.clean() detecting deep circular chains in tests/unit/core/models/test_sample_relation.py
- [ ] T083 [US5] Integration test for creating sample relationships with different types in tests/integration/core/test_sample_relationships.py
- [ ] T084 [US5] Integration test for bidirectional relationship queries (parent→children, child→parents) in tests/integration/core/test_sample_relationships.py
- [ ] T084.5 [P] [US5] Unit test for Sample.get_all_relationships() returning all SampleRelation objects in tests/unit/core/models/test_sample_methods.py
- [ ] T084.6 [P] [US5] Unit test for Sample.get_related_samples() with optional relationship_type filter in tests/unit/core/models/test_sample_methods.py
- [ ] T085 [US5] Integration test for SampleQuerySet.get_descendants() recursive traversal in tests/integration/core/test_sample_descendants.py

### Implementation for User Story 5

- [ ] T086 [US5] Enhance SampleRelation.clean() to prevent self-references in fairdm/core/models/sample_relation.py
- [ ] T087 [US5] Enhance SampleRelation.clean() to detect direct circular relationships in fairdm/core/models/sample_relation.py
- [ ] T088 [US5] Implement deep circular chain detection in SampleRelation.clean() using graph traversal in fairdm/core/models/sample_relation.py
- [ ] T089 [US5] Implement SampleQuerySet.get_descendants() with iterative BFS for hierarchy traversal in fairdm/core/managers/sample.py
- [ ] T090 [US5] Add max_depth parameter support to get_descendants() in fairdm/core/managers/sample.py
- [ ] T091 [US5] Add get_ancestors() method to SampleQuerySet for reverse hierarchy traversal in fairdm/core/managers/sample.py
- [ ] T092 [US5] Update RelationshipInline in SampleAdmin to prevent circular relationships at form level in fairdm/core/admin/sample.py
- [ ] T093 [P] [US5] Add sample relationship examples to demo app using RockSample hierarchy in fairdm_demo/factories.py
- [ ] T094 [P] [US5] Add sample relationship usage examples to quickstart.md documentation

**Checkpoint**: Sample relationships with circular prevention and hierarchy traversal complete

---

## Phase 8: User Story 6 - Optimized QuerySets (Priority: P3)

**Goal**: Optimized QuerySet methods that prefetch related data, handle polymorphic queries efficiently, and provide common query patterns

**Independent Test**: Execute QuerySet methods with Django Debug Toolbar enabled, verify minimal database hits (<10 queries for 1000 samples with relationships)

### Tests for User Story 6

- [ ] T095 [P] [US6] Performance test for Sample.objects.with_related().all() with 1000+ samples in tests/performance/test_sample_queryset_performance.py
- [ ] T096 [P] [US6] Performance test for Sample.objects.with_metadata().all() with 1000+ samples in tests/performance/test_sample_queryset_performance.py
- [ ] T097 [US6] Performance test for polymorphic query with select_subclasses() in tests/performance/test_sample_polymorphic_performance.py
- [ ] T098 [US6] Performance test for chained QuerySet methods (with_related + filter) in tests/performance/test_sample_queryset_chaining.py

### Implementation for User Story 6

- [ ] T099 [US6] Optimize with_related() to use select_related for polymorphic base class in fairdm/core/managers/sample.py
- [ ] T100 [US6] Optimize with_metadata() to use prefetch_related for concrete FK metadata models in fairdm/core/managers/sample.py
- [ ] T101 [US6] Add select_subclasses() support to with_related() for polymorphic type fields in fairdm/core/managers/sample.py
- [ ] T102 [US6] Implement queryset chaining tests ensuring optimizations persist through filters in fairdm/core/managers/sample.py
- [ ] T103 [US6] Add Django Debug Toolbar configuration to demo app for query profiling in fairdm_demo/settings.py (if not present)
- [ ] T104 [US6] Document QuerySet optimization patterns in developer guide docs/portal-development/optimization.md

**Checkpoint**: QuerySet optimization complete with performance verification

---

## Phase 9: Demo App Updates & Documentation (Cross-Cutting)

**Purpose**: Update demo app per Constitution Principle VII and create comprehensive documentation

**Note**: Demo app *code* (models, forms, admin) was implemented in earlier phases alongside feature development. This phase focuses on *documentation* (docstrings, README, guides) to ensure accuracy after all implementation changes are complete.

- [ ] T105 [P] Add comprehensive docstrings to RockSample model linking to docs/portal-development/models/custom-samples.md in fairdm_demo/models.py
- [ ] T106 [P] Add comprehensive docstrings to WaterSample model linking to docs/portal-development/models/custom-samples.md in fairdm_demo/models.py
- [ ] T107 [P] Add docstrings to RockSampleFactory explaining usage patterns in fairdm_demo/factories.py
- [ ] T108 [P] Add docstrings to WaterSampleFactory explaining usage patterns in fairdm_demo/factories.py
- [ ] T109 [P] Update fairdm_demo/README.md with sample registration examples and usage instructions
- [ ] T110 Create developer guide page docs/portal-development/models/custom-samples.md documenting custom sample type creation
- [ ] T111 [P] Create developer guide page docs/portal-development/forms/sample-forms.md documenting SampleFormMixin usage
- [ ] T112 [P] Create developer guide page docs/portal-development/filters/sample-filters.md documenting SampleFilterMixin usage
- [ ] T113 [P] Create developer guide page docs/portal-development/admin/sample-admin.md documenting SampleAdmin customization
- [ ] T114 Update quickstart.md with IGSN metadata schema alignment notes in specs/007-core-samples/quickstart.md
- [ ] T115 Update main documentation index docs/index.md with links to sample model documentation
- [ ] T116 [P] Add sample management tutorial to docs/user-guide/samples/managing-samples.md
- [ ] T117 [P] Add sample relationships tutorial to docs/user-guide/samples/sample-relationships.md

**Checkpoint**: Demo app and documentation complete per constitution requirements

---

## Phase 10: Testing, Validation & Polish

**Purpose**: Comprehensive testing, edge case validation, and final polish before merge

- [ ] T118 Run full test suite with pytest and verify all tests pass: `poetry run pytest`
- [ ] T119 Run test coverage analysis and verify >90% coverage for new code: `poetry run pytest --cov=fairdm.core`
- [ ] T120 [P] Run mypy type checking on new code: `poetry run mypy fairdm/core/models/sample.py fairdm/core/forms/sample.py`
- [ ] T121 [P] Run ruff linting on all modified files: `poetry run ruff check fairdm/core/ fairdm_demo/`
- [ ] T122 [P] Run djlint on template files (if any templates added): `poetry run djlint fairdm/templates/`
- [ ] T123 Validate migrations apply cleanly to fresh database: `poetry run python manage.py migrate --check`
- [ ] T124 Test admin interface manually with test data (create, edit, delete samples, inline editing)
- [ ] T125 Test polymorphic queries manually in Django shell (Sample.objects.all() returns correct types)
- [ ] T126 Test sample relationships manually (create parent-child, verify circular prevention)
- [ ] T127 [P] Test form rendering and validation with ChromeDevTools MCP (if forms have templates)
- [ ] T128 [P] Test filter combinations with 1000+ samples for performance validation
- [ ] T129 Review and address all edge cases documented in spec.md (duplicate local_id, status transitions, location validation, etc.)
- [ ] T130 Update CHANGELOG.md with Feature 007 changes following Keep a Changelog format
- [ ] T131 Create pull request with comprehensive description linking to spec, testing evidence, and demo app examples

**Checkpoint**: Feature complete, tested, documented, and ready for review

---

## Task Summary

**Total Tasks**: 133

**Tasks by Phase**:

- Setup: 5 tasks (T001-T005)
- Foundational: 8 tasks (T006-T013)
- US1 Polymorphism & Registry: 17 tasks (T014-T030)
- US2 Admin Interface: 17 tasks (T031-T047)
- US3 Forms with Mixins: 15 tasks (T048-T062)
- US4 Filtering & Search: 17 tasks (T063-T079)
- US5 Relationships & Provenance: 17 tasks (T080-T094) — includes 2 new tasks for convenience methods
- US6 Optimized QuerySets: 10 tasks (T095-T104)
- Demo App & Documentation: 13 tasks (T105-T117)
- Testing & Polish: 14 tasks (T118-T131)

**Parallel Opportunities**:

- Phase 1 Setup: T003-T004 (2 parallel)
- Phase 2 Foundational: T008-T011 (4 parallel)
- US1: T014-T015, T019-T020, T024-T025 (multiple batches)
- US2: T031-T032, T037-T040, T045-T046 (multiple batches)
- US3: T048-T049, T059-T060 (multiple batches)
- US4: T063-T064, T076-T077 (multiple batches)
- US5: T080-T081, T084.5-T084.6, T093-T094 (multiple batches)
- US6: T095-T096 (parallel)
- Documentation: T105-T108, T110-T113, T116-T117 (multiple batches)
- Polish: T120-T122, T127-T128 (multiple batches)

**Independent Test Criteria by User Story**:

- **US1**: Define custom sample types (RockSample, WaterSample), register with Feature 004, verify polymorphic queries return correct types, verify auto-generated components work
- **US2**: Access admin, search by name/uuid, filter by dataset/status, edit with inline metadata, verify polymorphic types display correctly
- **US3**: Instantiate forms with dataset context, render and verify field filtering, submit valid/invalid data, verify validation
- **US4**: Create samples with various attributes, apply filter combinations, verify results correctly narrowed
- **US5**: Create parent sample, establish typed relationships, query bidirectionally, attempt circular reference and verify prevention
- **US6**: Execute QuerySet methods with query logging, verify <10 queries for 1000 samples with relationships

**MVP Scope**: User Story 1 (T014-T030) + User Story 2 (T031-T047)

- Delivers core polymorphic sample functionality with registry integration
- Provides admin interface for basic CRUD operations
- Enables portal developers to define custom sample types immediately
- Estimated: 34 tasks for MVP

**Dependencies**:

```
Phase 1 (Setup) → Phase 2 (Foundational) → [All User Stories can proceed in parallel]

Within User Stories:
- US1 tests → US1 implementation
- US2 depends on US1 (needs Sample model with polymorphic support)
- US3 tests → US3 implementation
- US4 tests → US4 implementation (can start after US2 complete for admin testing)
- US5 depends on Phase 2 (needs SampleRelation model)
- US6 depends on US1 (optimizes QuerySet from US1)
- Phase 9 (Demo/Docs) can proceed in parallel with US3-US6
- Phase 10 (Testing) requires all previous phases complete
```

**Format Validation**: ✅ All tasks follow checklist format with sequential IDs, [P] parallel markers, [US#] story tags, and exact file paths
