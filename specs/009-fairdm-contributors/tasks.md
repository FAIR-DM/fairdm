# Tasks: FairDM Contributors System

**Input**: Design documents from `/specs/009-fairdm-contributors/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api-contracts.md, quickstart.md

**Tests**: Tests are included per the framework's test-first requirement (Constitution Principle V)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project environment verification and dependency setup

- [ ] T001 Verify Python 3.11+ and Poetry environment
- [ ] T002 Verify all dependencies from pyproject.toml are installed (django-polymorphic, django-lifecycle, django-guardian, etc.)
- [ ] T003 [P] Run Django system checks to verify configuration: `poetry run python manage.py check`
- [ ] T004 [P] Verify Celery + Redis infrastructure is running for background tasks
- [ ] T005 Verify test framework (pytest + pytest-django) configuration

**Checkpoint - Setup Complete**: `poetry run python manage.py check` returns exit code 0

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Migration Planning & Data Safety

- [ ] T006 Create migration 0011_add_partial_dates.py to add start_date/end_date PartialDateField columns to OrganizationMember model
- [ ] T007 Create migration 0012_rename_to_affiliation.py to rename OrganizationMember model → Affiliation and update table name
- [ ] T008 Create migration 0013_update_related_names.py to update related_name from "organization_members" → "affiliations"

### Test Fixtures & Framework

- [ ] T009 [P] Create test fixtures in tests/test_contrib/test_contributors/conftest.py (person_factory, org_factory, affiliation_factory, contribution_factory, identifier_factory)
- [ ] T010 [P] Create TransformTestMixin in tests/test_contrib/test_contributors/ for transform round-trip testing

### System Validation

- [ ] T011 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` - MUST pass before proceeding
- [ ] T012 ⚠️ CRITICAL: Run migration tests: `poetry run pytest tests/test_contrib/test_contributors/test_migrations.py -v` - MUST pass before proceeding

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Contributor Data Models (Priority: P1) 🎯 MVP

**Goal**: Provide complete, metadata-rich Person and Organization models with validation, computed properties, and lifecycle hooks

**Independent Test**: Create Person (claimed and unclaimed) and Organization instances, verify field validation, test polymorphic queries, verify model methods

### Tests for User Story 1 (Red → Green → Refactor)

- [ ] T013 [P] [US1] Write test_person_claimed_unclaimed_semantics in tests/test_contrib/test_contributors/test_models.py (MUST FAIL before T032)
- [ ] T014 [P] [US1] Write test_organization_creation_and_validation in tests/test_contrib/test_contributors/test_models.py (MUST FAIL before T033)
- [ ] T015 [P] [US1] Write test_affiliation_unique_constraints in tests/test_contrib/test_contributors/test_models.py (MUST FAIL before T034)
- [ ] T016 [P] [US1] Write test_contribution_gfk_relationships in tests/test_contrib/test_contributors/test_models.py (MUST FAIL before T035)
- [ ] T017 [P] [US1] Write test_contributor_identifier_uniqueness in tests/test_contrib/test_contributors/test_models.py (MUST FAIL before T036)

### Core Model Updates for User Story 1

- [ ] T018 [P] [US1] Update Contributor model in fairdm/contrib/contributors/models.py: Add privacy_settings JSONField, get_visible_fields(viewer) method
- [ ] T019 [P] [US1] Update Person model in fairdm/contrib/contributors/models.py: Add is_claimed property, fix save() name population, fix clean() email validation
- [ ] T020 [P] [US1] Update Organization model in fairdm/contrib/contributors/models.py: Add manage_organization permission to Meta, fix from_ror() classmethod bug
- [ ] T021 [US1] Rename OrganizationMember → Affiliation in fairdm/contrib/contributors/models.py: Add type field security state machine, add PartialDateField start_date/end_date, add is_primary field
- [ ] T022 [US1] Update Contribution model in fairdm/contrib/contributors/models.py: Review and fix lifecycle hooks, verify add_to() classmethod
- [ ] T023 [US1] Update ContributorIdentifier model in fairdm/contrib/contributors/models.py: Change AFTER_CREATE hook to dispatch async Celery task instead of synchronous API call

### Manager & Queryset Methods for User Story 1

- [ ] T024 [US1] Update UserManager in fairdm/contrib/contributors/managers.py: Add create_unclaimed(first_name, last_name, **extra_fields) method
- [ ] T025 [US1] Update PersonalContributorsManager in fairdm/contrib/contributors/managers.py: Add claimed() and unclaimed() queryset methods
- [ ] T026 [US1] Complete stub methods in ContributionManager in fairdm/contrib/contributors/managers.py: for_entity(), by_contributor(), by_role()

### Validation & Utilities for User Story 1

- [ ] T027 [P] [US1] Update validators in fairdm/contrib/contributors/validators.py: Ensure ORCID and ROR format validators are complete
- [ ] T028 [P] [US1] Review and complete utility functions in fairdm/contrib/contributors/utils/helpers.py: get_contributor_avatar(), current_user_has_role(), update_or_create_contribution()

### Admin Integration for User Story 1

- [ ] T029 [US1] Update PersonAdmin in fairdm/contrib/contributors/admin.py: Add is_claimed list filter, add privacy_settings readonly field
- [ ] T030 [US1] Update OrganizationAdmin in fairdm/contrib/contributors/admin.py: Add AffiliationInline (rename from OrganizationMemberInline)
- [ ] T031 [US1] Create AffiliationAdmin in fairdm/contrib/contributors/admin.py: Register Affiliation model with list_display for type field state

### System Validation for User Story 1

- [ ] T032 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` - MUST pass before proceeding
- [ ] T033 ⚠️ CRITICAL: Run User Story 1 tests: `poetry run pytest tests/test_contrib/test_contributors/test_models.py -v` - ALL tests MUST pass

**Checkpoint**: User Story 1 complete - Core models, managers, validators, admin working and tested

---

## Phase 4: User Story 2 - External Identifier Integration (Priority: P2)

**Goal**: Automatic ORCID/ROR synchronization via async Celery tasks with proper error handling and rate limiting

**Independent Test**: Provide ORCID/ROR identifier, verify async task dispatches, mock external APIs, verify metadata updates

### Tests for User Story 2

- [X] T034 [P] [US2] Write test_orcid_sync_task in tests/test_contrib/test_contributors/test_tasks.py with mocked ORCID API (MUST FAIL before T045)
- [X] T035 [P] [US2] Write test_ror_sync_task in tests/test_contrib/test_contributors/test_tasks.py with mocked ROR API (MUST FAIL before T046)
- [X] T036 [P] [US2] Write test_periodic_refresh_all in tests/test_contrib/test_contributors/test_tasks.py (MUST FAIL before T047)
- [X] T037 [P] [US2] Write test_sync_error_handling in tests/test_contrib/test_contributors/test_tasks.py for API failures (MUST FAIL before T048)

### Implementation for User Story 2

- [X] T038 [P] [US2] Create tasks.py in fairdm/contrib/contributors/: Define sync_contributor_identifier(identifier_pk) Celery task
- [X] T039 [P] [US2] Add refresh_all_contributors() Celery beat task to fairdm/contrib/contributors/tasks.py
- [X] T040 [P] [US2] Add detect_duplicate_contributors() Celery task to fairdm/contrib/contributors/tasks.py
- [X] T041 [US2] Update ContributorIdentifier AFTER_CREATE hook in fairdm/contrib/contributors/models.py to call sync_contributor_identifier.delay() via transaction.on_commit()
- [ ] T042 [US2] Update Person.from_orcid() classmethod in fairdm/contrib/contributors/models.py to use async task for sync
- [ ] T043 [US2] Update Organization.from_ror() classmethod in fairdm/contrib/contributors/models.py to use async task for sync

### System Validation for User Story 2

- [X] T044 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` - MUST pass before proceeding
- [X] T045 ⚠️ CRITICAL: Run User Story 2 tests: `poetry run pytest tests/test_contrib/test_contributors/test_tasks.py -v` - ALL tests MUST pass

**Checkpoint**: User Story 2 complete - ORCID/ROR sync working asynchronously with error handling

---

## Phase 5: User Story 3 - Person Profile Management via Admin (Priority: P3)

**Goal**: Unified admin interface for Person (auth + contributor) with claim status filtering and inline affiliations

**Independent Test**: Create/edit Person via admin, verify claimed/unclaimed filtering, verify inline affiliation management

### Tests for User Story 3

- [X] T046 [P] [US3] Write test_person_admin_changelist_loads in tests/test_contrib/test_contributors/test_admin.py (MUST FAIL before T052)
- [X] T047 [P] [US3] Write test_person_admin_claim_filter in tests/test_contrib/test_contributors/test_admin.py (MUST FAIL before T053)
- [X] T048 [P] [US3] Write test_person_admin_inline_affiliations in tests/test_contrib/test_contributors/test_admin.py (MUST FAIL before T054)

### Implementation for User Story 3

- [X] T049 [US3] Update PersonAdmin in fairdm/contrib/contributors/admin.py: Add "Claimed Status" filter, add inline for Affiliation
- [X] T050 [US3] Add ClaimedStatusFilter to fairdm/contrib/contributors/admin.py for claimed/unclaimed Person filtering
- [X] T051 [US3] Update PersonAdmin fieldsets in fairdm/contrib/contributors/admin.py: Group auth fields and profile fields clearly

### System Validation for User Story 3

- [X] T052 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` - MUST pass before proceeding
- [X] T053 ⚠️ CRITICAL: Run User Story 3 tests: `poetry run pytest tests/test_contrib/test_contributors/test_admin.py::test_person* -v` - ALL tests MUST pass

**Checkpoint**: User Story 3 complete - Person admin interface unified and functional

---

## Phase 6: User Story 3b - Organization Management via Admin (Priority: P3)

**Goal**: Dedicated Organization admin with inline membership, sub-organization listing, and ROR sync trigger

**Independent Test**: Create/edit Organization via admin, manage members inline, verify parent-child org relationships

### Tests for User Story 3b

- [X] T054 [P] [US3b] Write test_organization_admin_changelist_loads in tests/test_contrib/test_contributors/test_admin.py (MUST FAIL before T059)
- [X] T055 [P] [US3b] Write test_organization_admin_inline_members in tests/test_contrib/test_contributors/test_admin.py (MUST FAIL before T060)
- [X] T056 [P] [US3b] Write test_organization_admin_ror_sync_button in tests/test_contrib/test_contributors/test_admin.py (MUST FAIL before T061)

### Implementation for User Story 3b

- [X] T057 [US3b] Update OrganizationAdmin in fairdm/contrib/contributors/admin.py: Add inline for members (via Affiliation), add inline for sub-organizations
- [X] T058 [US3b] Add "Sync from ROR" admin action to OrganizationAdmin in fairdm/contrib/contributors/admin.py

### System Validation for User Story 3b

- [X] T059 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` - MUST pass before proceeding
- [X] T060 ⚠️ CRITICAL: Run User Story 3b tests: `poetry run pytest tests/test_contrib/test_contributors/test_admin.py::test_organization* -v` - ALL tests MUST pass

**Checkpoint**: User Story 3b complete - Organization admin interface fully functional

---

## Phase 7: User Story 3c - Organization Ownership by Authenticated Users (Priority: P3)

**Goal**: Organization ownership via django-guardian manage_organization permission with transfer capability

**Independent Test**: Assign organization owner, verify owner can edit org and manage members, verify non-owners cannot, verify transfer

### Tests for User Story 3c

- [X] T061 [P] [US3c] Write test_assign_organization_owner in tests/test_contrib/test_contributors/test_permissions.py (MUST FAIL before T067)
- [X] T062 [P] [US3c] Write test_owner_can_edit_organization in tests/test_contrib/test_contributors/test_permissions.py (MUST FAIL before T068)
- [X] T063 [P] [US3c] Write test_non_owner_cannot_edit in tests/test_contrib/test_contributors/test_permissions.py (MUST FAIL before T069)
- [X] T064 [P] [US3c] Write test_transfer_ownership in tests/test_contrib/test_contributors/test_permissions.py (MUST FAIL before T070)
- [X] T065 [P] [US3c] Write test_admin_override_access in tests/test_contrib/test_contributors/test_permissions.py (MUST FAIL before T071)

### Implementation for User Story 3c

- [ ] T066 [US3c] Add lifecycle hook to Affiliation model in fairdm/contrib/contributors/models.py: When type changes to/from OWNER (3), sync manage_organization permission
- [ ] T067 [US3c] Create organization ownership view in fairdm/contrib/contributors/views/organization.py: transfer_ownership(request, org_pk, new_owner_pk)
- [ ] T068 [US3c] Add permission check decorators to organization edit views in fairdm/contrib/contributors/views/organization.py
- [ ] T069 [US3c] Update Organization admin in fairdm/contrib/contributors/admin.py: Add "Transfer Ownership" action

### System Validation for User Story 3c

- [ ] T070 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` - MUST pass before proceeding
- [ ] T071 ⚠️ CRITICAL: Run User Story 3c tests: `poetry run pytest tests/test_contrib/test_contributors/test_permissions.py -v` - ALL tests MUST pass

**Checkpoint**: User Story 3c complete - Organization ownership working with guardian integration

---

## Phase 8: User Story 4 - Contributor Roles and Affiliations (Priority: P4)

**Goal**: Multi-role contribution tracking with time-bound affiliation history and PartialDateField precision

**Independent Test**: Assign multiple roles to contributor on project/dataset, record affiliation changes with dates, query historical affiliations

### Tests for User Story 4

- [ ] T072 [P] [US4] Write test_multiple_roles_per_contribution in tests/test_contrib/test_contributors/test_models.py (MUST FAIL before T078)
- [ ] T073 [P] [US4] Write test_affiliation_time_bounds in tests/test_contrib/test_contributors/test_models.py (MUST FAIL before T079)
- [ ] T074 [P] [US4] Write test_partial_date_precision in tests/test_contrib/test_contributors/test_models.py (MUST FAIL before T080)
- [ ] T075 [P] [US4] Write test_primary_affiliation_constraint in tests/test_contrib/test_contributors/test_models.py (MUST FAIL before T081)

### Implementation for User Story 4

- [ ] T076 [US4] Verify Contribution.roles ConceptManyToManyField in fairdm/contrib/contributors/models.py uses FairDMRoles vocabulary
- [ ] T077 [US4] Implement Affiliation.save() override in fairdm/contrib/contributors/models.py: Enforce only one is_primary=True per person
- [ ] T078 [US4] Add Person.current_affiliations() method in fairdm/contrib/contributors/models.py: Returns affiliations with end_date=NULL
- [ ] T079 [US4] Add Person.primary_affiliation() property in fairdm/contrib/contributors/models.py: Returns is_primary=True affiliation

### System Validation for User Story 4

- [ ] T080 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` - MUST pass before proceeding
- [ ] T081 ⚠️ CRITICAL: Run User Story 4 tests: `poetry run pytest tests/test_contrib/test_contributors/test_models.py::test_*affiliation* tests/test_contrib/test_contributors/test_models.py::test_*role* -v` - ALL tests MUST pass

**Checkpoint**: User Story 4 complete - Roles and time-bound affiliations working correctly

---

## Phase 9: User Story 5 - Metadata Export and Interoperability (Priority: P5)

**Goal**: TransformRegistry with built-in DataCite/Schema.org/CSL-JSON/ORCID/ROR transforms plus extensible API

**Independent Test**: Export Person/Organization to each format, verify schema compliance, create custom transform, import from external format

### Tests for User Story 5

- [ ] T082 [P] [US5] Write test_datacite_export_person in tests/test_contrib/test_contributors/test_transforms.py using TransformTestMixin (MUST FAIL before T092)
- [ ] T083 [P] [US5] Write test_schema_org_export_organization in tests/test_contrib/test_contributors/test_transforms.py (MUST FAIL before T093)
- [ ] T084 [P] [US5] Write test_csl_json_export in tests/test_contrib/test_contributors/test_transforms.py (MUST FAIL before T094)
- [ ] T085 [P] [US5] Write test_orcid_round_trip in tests/test_contrib/test_contributors/test_transforms.py (MUST FAIL before T095)
- [ ] T086 [P] [US5] Write test_ror_round_trip in tests/test_contrib/test_contributors/test_transforms.py (MUST FAIL before T096)
- [ ] T087 [P] [US5] Write test_transform_registry_registration in tests/test_contrib/test_contributors/test_transforms.py (MUST FAIL before T097)
- [ ] T088 [P] [US5] Write test_custom_transform_creation in tests/test_contrib/test_contributors/test_transforms.py (MUST FAIL before T098)

### Implementation for User Story 5

- [ ] T089 [P] [US5] Create TransformRegistry singleton in fairdm/contrib/contributors/utils/transforms.py with @register decorator
- [ ] T090 [P] [US5] Create BaseTransform abstract class in fairdm/contrib/contributors/utils/transforms.py with to_format() and from_format() methods
- [ ] T091 [US5] Implement DataCiteTransform in fairdm/contrib/contributors/utils/transforms.py: Bidirectional Person/Organization ↔ DataCite JSON
- [ ] T092 [US5] Implement SchemaOrgTransform in fairdm/contrib/contributors/utils/transforms.py: Bidirectional Person/Organization ↔ Schema.org JSON-LD
- [ ] T093 [US5] Implement CSLJSONTransform in fairdm/contrib/contributors/utils/transforms.py: Person → CSL-JSON (for citations)
- [ ] T094 [US5] Implement ORCIDTransform in fairdm/contrib/contributors/utils/transforms.py: Bidirectional Person ↔ ORCID API JSON
- [ ] T095 [US5] Implement RORTransform in fairdm/contrib/contributors/utils/transforms.py: Bidirectional Organization ↔ ROR API JSON
- [ ] T096 [US5] Add to_datacite() / to_schema_org() / to_csl_json() methods to Contributor model in fairdm/contrib/contributors/models.py that delegate to registry
- [ ] T097 [US5] Update Person.from_orcid() and Organization.from_ror() in fairdm/contrib/contributors/models.py to use ORCIDTransform/RORTransform

### System Validation for User Story 5

- [ ] T098 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` - MUST pass before proceeding
- [ ] T099 ⚠️ CRITICAL: Run User Story 5 tests: `poetry run pytest tests/test_contrib/test_contributors/test_transforms.py -v` - ALL tests MUST pass

**Checkpoint**: User Story 5 complete - Transform system working with all formats and extensible

---

## Phase 10: User Story 6 - Query Utilities and Custom Managers (Priority: P6)

**Goal**: Advanced queryset methods for search, filtering, bulk operations, and duplicate detection

**Independent Test**: Use manager methods for common queries, verify query efficiency, test duplicate detection utility

### Tests for User Story 6

- [ ] T100 [P] [US6] Write test_claimed_unclaimed_querysets in tests/test_contrib/test_contributors/test_managers.py (MUST FAIL before T106)
- [ ] T101 [P] [US6] Write test_contribution_by_role in tests/test_contrib/test_contributors/test_managers.py (MUST FAIL before T107)
- [ ] T102 [P] [US6] Write test_contribution_for_entity in tests/test_contrib/test_contributors/test_managers.py (MUST FAIL before T108)
- [ ] T103 [P] [US6] Write test_duplicate_detection in tests/test_contrib/test_contributors/test_models.py (MUST FAIL before T109)

### Implementation for User Story 6

- [ ] T104 [US6] Implement PersonalContributorsManager.claimed() in fairdm/contrib/contributors/managers.py: Filter email IS NOT NULL AND is_active=True
- [ ] T105 [US6] Implement PersonalContributorsManager.unclaimed() in fairdm/contrib/contributors/managers.py: Filter email IS NULL OR is_active=False
- [ ] T106 [US6] Implement ContributionManager.by_role(role_name) in fairdm/contrib/contributors/managers.py: Filter by roles__name
- [ ] T107 [US6] Implement ContributionManager.for_entity(obj) in fairdm/contrib/contributors/managers.py: Filter by content_type + object_id
- [ ] T108 [US6] Implement detect_duplicate_contributors() utility in fairdm/contrib/contributors/utils/helpers.py: Fuzzy name matching with threshold

### System Validation for User Story 6

- [ ] T109 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` - MUST pass before proceeding
- [ ] T110 ⚠️ CRITICAL: Run User Story 6 tests: `poetry run pytest tests/test_contrib/test_contributors/test_managers.py -v` - ALL tests MUST pass

**Checkpoint**: User Story 6 complete - All query utilities working efficiently

---

## Phase 11: Privacy Controls (Cross-Cutting)

**Goal**: Privacy-aware field visibility based on viewer and claim status

**Independent Test**: Set privacy levels, verify visible fields for different viewer types

### Tests for Privacy

- [ ] T111 [P] Write test_privacy_unclaimed_person in tests/test_contrib/test_contributors/test_privacy.py (MUST FAIL before T115)
- [ ] T112 [P] Write test_privacy_claimed_person in tests/test_contrib/test_contributors/test_privacy.py (MUST FAIL before T116)
- [ ] T113 [P] Write test_get_visible_fields_anonymous in tests/test_contrib/test_contributors/test_privacy.py (MUST FAIL before T117)
- [ ] T114 [P] Write test_get_visible_fields_authenticated in tests/test_contrib/test_contributors/test_privacy.py (MUST FAIL before T118)

### Implementation for Privacy

- [ ] T115 Implement Contributor.get_visible_fields(viewer) in fairdm/contrib/contributors/models.py: Return field dict based on privacy_settings and viewer
- [ ] T116 Add default privacy settings in Person.save() in fairdm/contrib/contributors/models.py: Unclaimed=all public, claimed=email private
- [ ] T117 Update contributor detail views in fairdm/contrib/contributors/views/ to use get_visible_fields()

### System Validation for Privacy

- [ ] T118 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` - MUST pass before proceeding
- [ ] T119 ⚠️ CRITICAL: Run privacy tests: `poetry run pytest tests/test_contrib/test_contributors/test_privacy.py -v` - ALL tests MUST pass

**Checkpoint**: Privacy controls complete and tested

---

## Phase 12: Template Tags & Frontend Integration (Cross-Cutting)

**Goal**: Template tags for contributor filtering and display

**Independent Test**: Use template tags in test templates, verify output

### Tests for Template Tags

- [ ] T120 [P] Write test_by_role_filter in tests/test_contrib/test_contributors/test_templatetags.py (MUST FAIL before T123)
- [ ] T121 [P] Write test_has_role_filter in tests/test_contrib/test_contributors/test_templatetags.py (MUST FAIL before T124)

### Implementation for Template Tags

- [ ] T122 Implement by_role template filter in fairdm/contrib/contributors/templatetags/contributor_tags.py
- [ ] T123 Implement has_role template filter in fairdm/contrib/contributors/templatetags/contributor_tags.py

### System Validation for Template Tags

- [ ] T124 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` - MUST pass before proceeding
- [ ] T125 ⚠️ CRITICAL: Run template tag tests: `poetry run pytest tests/test_contrib/test_contributors/test_templatetags.py -v` - ALL tests MUST pass

**Checkpoint**: Template tags complete and tested

---

## Phase 13: Demo App Updates (Constitution Principle VII)

**Goal**: Update fairdm_demo to demonstrate all new features

**Independent Test**: Run demo app tests, verify demo models use Affiliation, verify admin views work

### Tests for Demo App

- [ ] T126 [P] Write test_demo_person_creation in fairdm_demo/tests/test_contributors.py (MUST FAIL before T130)
- [ ] T127 [P] Write test_demo_organization_ownership in fairdm_demo/tests/test_contributors.py (MUST FAIL before T131)
- [ ] T128 [P] Write test_demo_affiliation_workflow in fairdm_demo/tests/test_contributors.py (MUST FAIL before T132)
- [ ] T129 [P] Write test_demo_admin_views_load in fairdm_demo/tests/test_contributors.py (MUST FAIL before T133)

### Implementation for Demo App

- [ ] T130 Update fairdm_demo/models.py: Replace OrganizationMember with Affiliation usage examples
- [ ] T131 Update fairdm_demo/factories.py: Add AffiliationFactory, update PersonFactory with claimed/unclaimed examples
- [ ] T132 Add example transform usage to fairdm_demo/models.py or README.md
- [ ] T133 Add example privacy control usage to fairdm_demo/models.py

### System Validation for Demo App

- [ ] T134 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` - MUST pass before proceeding
- [ ] T135 ⚠️ CRITICAL: Run demo app tests: `poetry run pytest fairdm_demo/tests/test_contributors.py -v` - ALL tests MUST pass

**Checkpoint**: Demo app updated and all demo tests passing

---

## Phase 14: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup and verification before completion

- [ ] T136 [P] Update developer documentation in specs/009-fairdm-contributors/quickstart.md with final usage examples
- [ ] T137 [P] Update API contracts in specs/009-fairdm-contributors/contracts/api-contracts.md with any signature changes
- [ ] T138 Code review and refactoring: Remove debug print statements, add docstrings to all public methods
- [ ] T139 Verify all 5 identified bugs from plan.md are fixed (from_ror classmethod, clean() validation, sync timing, etc.)
- [ ] T140 Run quickstart.md validation: Execute all code examples from quickstart.md to ensure they work
- [ ] T141 Performance verification: Test contributor lookup with 10,000+ records meets < 200ms requirement (SC-007)
- [ ] T142 ORCID/ROR sync performance: Verify sync completes < 5s per identifier (SC-002, SC-003)

### Schema Validation

- [ ] T143 [P] Write test_datacite_schema_validation in tests/test_contrib/test_contributors/test_transforms.py: Use official DataCite JSON schema validator to verify exports
- [ ] T144 [P] Write test_schema_org_validation in tests/test_contrib/test_contributors/test_transforms.py: Use schema.org validator or JSON-LD processor to verify exports
- [ ] T145 Add DataCite JSON schema validation in fairdm/contrib/contributors/transforms/datacite.py: Validate export() output against official schema
- [ ] T146 Add Schema.org validation utility in fairdm/contrib/contributors/transforms/schemaorg.py: Validate JSON-LD structure

### Documentation Updates (Constitution Principle VI)

- [ ] T147 Create docs/portal-development/contributors.md: Comprehensive developer guide covering Person model (AUTH_USER_MODEL, claimed/unclaimed semantics, privacy settings), Organization model (ROR sync, ownership via manage_organization), Affiliation model (type field state machine, PartialDateField), Contribution model (roles, GFK relationships), and manager methods (claimed()/unclaimed(), by_role(), for_entity())
- [ ] T148 Add TransformRegistry API documentation to docs/portal-development/contributors.md: Document BaseTransform interface, bidirectional transform creation, built-in adapters (DataCite, Schema.org, CSL-JSON, ORCID, ROR), and example custom transformer implementation
- [ ] T149 Add privacy controls section to docs/portal-development/contributors.md: Document privacy_settings JSONField structure, get_visible_fields() method, default privacy behavior for claimed vs unclaimed profiles
- [ ] T150 Add claiming data model section to docs/portal-development/contributors.md: Document is_claimed property, claimed()/unclaimed() managers, create_unclaimed() method, and note that claiming flows are implemented in Feature 010
- [ ] T151 Create docs/portal-administration/managing_contributors.md: Admin guide covering Person admin interface (unified auth + contributor fields), Organization admin (inline memberships, ownership transfer), Affiliation verification workflow (type field PENDING→MEMBER→ADMIN→OWNER), and ORCID/ROR sync troubleshooting
- [ ] T152 Update docs/portal-development/index.md toctree: Add contributors.md to "Defining models" section before using_the_registry
- [ ] T153 Update docs/portal-administration/index.md toctree: Add managing_contributors.md to main toctree after managing_users_and_permissions
- [ ] T154 Add inline code examples to all new documentation: Every API method, manager, and configuration option MUST have a working code example
- [ ] T155 Add migration guide to docs/portal-development/contributors.md: Document AUTH_USER_MODEL change implications for existing portals, OrganizationMembership→Affiliation migration path, and settings.py updates required

### Final System Validation

- [ ] T156 ⚠️ CRITICAL: Run full Django system checks: `poetry run python manage.py check --deploy` - MUST pass
- [ ] T157 ⚠️ CRITICAL: Run contributor-specific tests: `poetry run pytest tests/test_contrib/test_contributors/ fairdm_demo/tests/test_contributors.py -v --cov=fairdm/contrib/contributors` - ALL tests MUST pass with >90% coverage
- [ ] T158 ⚠️ CRITICAL: Verify all documentation pages render correctly: Build Sphinx docs locally and verify no warnings or broken links for new contributor documentation pages
- [ ] T159 ⚠️ CRITICAL: Run ENTIRE project test suite: `poetry run pytest -v` - ALL tests across the entire project MUST pass. This ensures the contributors feature has not broken any existing functionality elsewhere in FairDM. DO NOT mark this task complete unless the full test suite passes with ZERO failures.

**Checkpoint**: Feature complete - all user stories implemented, tested, documented, and verified against entire project test suite

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-10)**: All depend on Foundational phase completion
  - US1 (Phase 3): Foundation for all other stories
  - US2 (Phase 4): Can start after US1 complete (depends on models)
  - US3/3b/3c (Phases 5-7): Can start after US1 complete (depends on models)
  - US4 (Phase 8): Can start after US1 complete (depends on Affiliation model)
  - US5 (Phase 9): Can start after US1 complete (depends on models)
  - US6 (Phase 10): Can start after US1 complete (depends on models and managers)
- **Privacy (Phase 11)**: Depends on US1 (models)
- **Template Tags (Phase 12)**: Depends on US4 (roles)
- **Demo App (Phase 13)**: Depends on all user stories complete
- **Polish (Phase 14)**: Depends on all previous phases

### User Story Dependencies

- **User Story 1 (P1)**: MUST complete before all other stories - provides foundation models
- **User Story 2 (P2)**: Can start after US1 - No dependencies on other stories
- **User Story 3 (P3)**: Can start after US1 - No dependencies on other stories
- **User Story 3b (P3)**: Can start after US1 - No dependencies on other stories
- **User Story 3c (P3)**: Can start after US1 - Depends on Affiliation from US1
- **User Story 4 (P4)**: Can start after US1 - Depends on models from US1
- **User Story 5 (P5)**: Can start after US1 - No dependencies on other stories
- **User Story 6 (P6)**: Can start after US1 - Depends on managers from US1

### Within Each User Story

- Tests MUST be written and FAIL before implementation (Red → Green → Refactor)
- Models before managers
- Managers before admin/views
- Core implementation before system checks
- System checks MUST pass before tests
- Tests MUST pass before moving to next story

### Parallel Opportunities

- **Setup tasks** marked [P] can run in parallel
- **Foundational migrations** T006-T008 can be written in parallel (but must run sequentially)
- **Foundational test fixtures** T009-T010 can run in parallel
- **Within each user story**: All test-writing tasks marked [P] can run in parallel
- **After US1 complete**: US2, US3, US3b, US4, US5, US6 can be worked on in parallel by different team members
- **Privacy and Template Tags**: Can be worked on in parallel after US1 complete

---

## Parallel Example: User Story 1

```bash
# Launch all test-writing tasks for User Story 1 together:
Task T013: "Write test_person_claimed_unclaimed_semantics in tests/test_contrib/test_contributors/test_models.py"
Task T014: "Write test_organization_creation_and_validation in tests/test_contrib/test_contributors/test_models.py"
Task T015: "Write test_affiliation_unique_constraints in tests/test_contrib/test_contributors/test_models.py"
Task T016: "Write test_contribution_gfk_relationships in tests/test_contrib/test_contributors/test_models.py"
Task T017: "Write test_contributor_identifier_uniqueness in tests/test_contrib/test_contributors/test_models.py"

# Then launch all model update tasks together:
Task T018: "Update Contributor model privacy_settings"
Task T019: "Update Person model is_claimed property"
Task T020: "Update Organization model manage_organization permission"
# (T021-T023 must wait until migrations are applied)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3/3b/3c → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently → Deploy/Demo
6. Add User Story 5 → Test independently → Deploy/Demo
7. Add User Story 6 → Test independently → Deploy/Demo
8. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (Phase 1-2)
2. Once Foundational is done and US1 is complete:
   - Developer A: User Story 2 (ORCID/ROR sync)
   - Developer B: User Story 3/3b/3c (Admin interfaces)
   - Developer C: User Story 5 (Transforms)
   - Developer D: User Story 4 + 6 (Roles + Queries)
3. Stories complete and integrate independently
4. All converge for Phase 13-14 (Demo + Polish)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- ⚠️ CRITICAL tasks are system checks and test runs - MUST pass before proceeding
- Verify tests fail before implementing (Red → Green → Refactor)
- Run `poetry run python manage.py check` after each phase
- Run phase-specific tests after implementation, before moving to next phase
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Feature 010 scope: All claiming flows (ORCID intercept, email, token, merge) are deferred - only data model support in Feature 009
