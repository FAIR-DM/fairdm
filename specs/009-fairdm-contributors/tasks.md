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

- [X] T001 Verify Python 3.11+ and Poetry environment
- [X] T002 Verify all dependencies from pyproject.toml are installed (django-polymorphic, django-lifecycle, django-guardian, etc.)
- [X] T003 [P] Run Django system checks to verify configuration: `poetry run python manage.py check`
- [X] T004 [P] Verify Celery + Redis infrastructure is running for background tasks
- [X] T005 Verify test framework (pytest + pytest-django) configuration

**Checkpoint - Setup Complete**: `poetry run python manage.py check` returns exit code 0

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Migration Planning & Data Safety

- [X] T006 Create migration 0011_add_partial_dates.py to add start_date/end_date PartialDateField columns to OrganizationMember model
- [X] T007 Create migration 0012_rename_to_affiliation.py to rename OrganizationMember model → Affiliation and update table name
- [X] T008 Create migration 0013_update_related_names.py to update related_name from "organization_members" → "affiliations"
- [X] T008a Create migration 0014_add_is_claimed_field.py to add is_claimed BooleanField to Person model (nullable for migration)
- [X] T008b Create data migration 0015_set_is_claimed.py to set is_claimed=True for existing users with email NOT NULL, is_claimed=False for others
- [X] T008c Create migration 0016_make_is_claimed_non_nullable.py to alter is_claimed field to default=False, non-nullable

### Test Fixtures & Framework

- [X] T009 [P] Create test fixtures in tests/test_contrib/test_contributors/conftest.py (person_factory, org_factory, affiliation_factory, contribution_factory, identifier_factory)
- [X] T010 [P] Create TransformTestMixin in tests/test_contrib/test_contributors/ for transform round-trip testing

### System Validation

- [X] T011 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` - MUST pass before proceeding
- [X] T012 ⚠️ CRITICAL: Run migration tests: `poetry run pytest tests/test_contrib/test_contributors/test_migrations.py -v` - MUST pass before proceeding

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Contributor Data Models (Priority: P1) 🎯 MVP

**Goal**: Provide complete, metadata-rich Person and Organization models with validation, is_claimed BooleanField state tracking (Ghost/Invited/Claimed/Banned), and lifecycle hooks

**Independent Test**: Create Person in all states (Ghost, Invited, Claimed, Banned), verify is_claimed field updates, verify Organization instances, test polymorphic queries, verify model methods

### Tests for User Story 1 (Red → Green → Refactor)

- [X] T013 [P] [US1] Write test_person_state_transitions in tests/test_contrib/test_contributors/test_models.py to verify Ghost→Invited→Claimed→Banned state machine (MUST FAIL before T032)
- [X] T014 [P] [US1] Write test_organization_creation_and_validation in tests/test_contrib/test_contributors/test_models.py (MUST FAIL before T033)
- [X] T015 [P] [US1] Write test_affiliation_unique_constraints in tests/test_contrib/test_contributors/test_models.py (MUST FAIL before T034)
- [X] T016 [P] [US1] Write test_contribution_gfk_relationships in tests/test_contrib/test_contributors/test_models.py (MUST FAIL before T035)
- [X] T017 [P] [US1] Write test_contributor_identifier_uniqueness in tests/test_contrib/test_contributors/test_models.py (MUST FAIL before T036)

### Core Model Updates for User Story 1

- [X] T018 [P] [US1] Update Contributor model in fairdm/contrib/contributors/models.py: Add privacy_settings JSONField, get_visible_fields(viewer) method
- [X] T019 [P] [US1] Update Person model in fairdm/contrib/contributors/models.py: Add is_claimed BooleanField (migrated in T008a-c), fix save() name population, fix clean() email validation and claimed-state email protection
- [X] T020 [P] [US1] Update Organization model in fairdm/contrib/contributors/models.py: Add manage_organization permission to Meta, fix from_ror() classmethod bug
- [X] T021 [US1] Rename OrganizationMember → Affiliation in fairdm/contrib/contributors/models.py: Add type field security state machine, add PartialDateField start_date/end_date, add is_primary field
- [X] T022 [US1] Update Contribution model in fairdm/contrib/contributors/models.py: Review and fix lifecycle hooks, verify add_to() classmethod
- [X] T023 [US1] Update ContributorIdentifier model in fairdm/contrib/contributors/models.py: Change AFTER_CREATE hook to dispatch async Celery task instead of synchronous API call

### Manager & Queryset Methods for User Story 1

- [X] T024 [US1] Create PersonQuerySet in fairdm/contrib/contributors/managers.py: Add real(), claimed(), unclaimed(), ghost(), invited() methods
- [X] T025 [US1] Unify managers in fairdm/contrib/contributors/managers.py: Merge PersonalContributorsManager into UserManager using .from_queryset(PersonQuerySet) pattern
- [X] T025a [US1] Update Person model in fairdm/contrib/contributors/models.py: Remove contributors = PersonalContributorsManager() line, keep only objects = UserManager()
- [X] T025b [US1] Update UserManager.create_unclaimed() in fairdm/contrib/contributors/managers.py: Set is_claimed=False, is_active=True, email=NULL (creates Ghost state)
- [X] T026 [US1] Complete stub methods in ContributionManager in fairdm/contrib/contributors/managers.py: for_entity(), by_contributor(), by_role()

### Validation & Utilities for User Story 1

- [X] T027 [P] [US1] Update validators in fairdm/contrib/contributors/validators.py: Ensure ORCID and ROR format validators are complete
- [X] T027a [P] [US1] Write test_person_name_internationalization in tests/test_contrib/test_contributors/test_models.py: Test Person name handling with non-Latin scripts (Chinese, Arabic, Cyrillic) for FR-020 compliance (MUST FAIL before T019)
- [X] T028 [P] [US1] Review and complete utility functions in fairdm/contrib/contributors/utils/helpers.py: get_contributor_avatar(), current_user_has_role(), update_or_create_contribution()

### Admin Integration for User Story 1

- [X] T029 [US1] Update PersonAdmin in fairdm/contrib/contributors/admin.py: Add is_claimed list filter, add privacy_settings readonly field
- [X] T030 [US1] Update OrganizationAdmin in fairdm/contrib/contributors/admin.py: Add AffiliationInline (rename from OrganizationMemberInline)
- [X] T031 [US1] Create AffiliationAdmin in fairdm/contrib/contributors/admin.py: Register Affiliation model with list_display for type field state

### System Validation for User Story 1

- [X] T032 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` - MUST pass before proceeding
- [X] T033 ⚠️ CRITICAL: Run User Story 1 tests: `poetry run pytest tests/test_contrib/test_contributors/test_models.py -v` - ALL tests MUST pass

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
- [X] T042 [US2] Update Person.from_orcid() classmethod in fairdm/contrib/contributors/models.py to use async task for sync
- [X] T043 [US2] Update Organization.from_ror() classmethod in fairdm/contrib/contributors/models.py to use async task for sync

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

**Goal**: Organization ownership via derived `manage_organization` permission using custom auth backend (no guardian rows)

**Independent Test**: Assign organization owner, verify owner can edit org and manage members, verify non-owners cannot, verify transfer

### Tests for User Story 3c

- [X] T061 [P] [US3c] Write test_assign_organization_owner in tests/test_contrib/test_contributors/test_permissions.py (MUST FAIL before T067)
- [X] T062 [P] [US3c] Write test_owner_can_edit_organization in tests/test_contrib/test_contributors/test_permissions.py (MUST FAIL before T068)
- [X] T063 [P] [US3c] Write test_non_owner_cannot_edit in tests/test_contrib/test_contributors/test_permissions.py (MUST FAIL before T069)
- [X] T064 [P] [US3c] Write test_transfer_ownership in tests/test_contrib/test_contributors/test_permissions.py (MUST FAIL before T070)
- [X] T065 [P] [US3c] Write test_admin_override_access in tests/test_contrib/test_contributors/test_permissions.py (MUST FAIL before T071)

### Implementation for User Story 3c

- [X] ~~T066 [US3c] Add lifecycle hook to Affiliation model in fairdm/contrib/contributors/models.py: When type changes to/from OWNER (3), sync manage_organization permission~~ **SUPERSEDED** by derived permission approach (T066a-T066c)
- [X] T066a [US3c] Create OrganizationPermissionBackend in fairdm/contrib/contributors/permissions.py: Derive manage_organization from OWNER Affiliation query
- [X] T066b [US3c] Register OrganizationPermissionBackend in fairdm/conf/settings/auth.py AUTHENTICATION_BACKENDS
- [X] T066c [US3c] Remove lifecycle hooks from Affiliation model + remove manage_organization from Organization.Meta.permissions + create cleanup migration
- [X] T067 [US3c] Create organization ownership view in fairdm/contrib/contributors/views/organization.py: transfer_ownership(request, org_pk, new_owner_pk)
- [X] T068 [US3c] Add permission check decorators to organization edit views in fairdm/contrib/contributors/views/organization.py
- [X] T069 [US3c] Update Organization admin in fairdm/contrib/contributors/admin.py: Add "Transfer Ownership" action

### System Validation for User Story 3c

- [X] T070 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` - MUST pass before proceeding
- [X] T071 ⚠️ CRITICAL: Run User Story 3c tests: `poetry run pytest tests/test_contrib/test_contributors/test_permissions.py -v` - ALL tests MUST pass

**Checkpoint**: User Story 3c complete - Organization ownership working with derived permission backend (no guardian permission rows)

---

## Phase 8: User Story 4 - Contributor Roles and Affiliations (Priority: P4)

**Goal**: Multi-role contribution tracking with time-bound affiliation history and PartialDateField precision

**Independent Test**: Assign multiple roles to contributor on project/dataset, record affiliation changes with dates, query historical affiliations

### Tests for User Story 4

- [X] T072 [P] [US4] Write test_multiple_roles_per_contribution in tests/test_contrib/test_contributors/test_models.py (MUST FAIL before T077)
- [X] T073 [P] [US4] Write test_affiliation_time_bounds in tests/test_contrib/test_contributors/test_models.py (MUST FAIL before T078)
- [X] T074 [P] [US4] Write test_partial_date_precision in tests/test_contrib/test_contributors/test_models.py (MUST FAIL before T079)
- [X] T075 [P] [US4] Write test_primary_affiliation_constraint in tests/test_contrib/test_contributors/test_models.py (MUST FAIL before T080)
- [X] T075a [P] [US4] Write test_affiliation_queryset_methods in tests/test_contrib/test_contributors/test_managers.py: Test primary(), current(), past() methods (MUST FAIL before T079)

### Implementation for User Story 4

- [X] T076 [US4] Verify Contribution.roles ConceptManyToManyField in fairdm/contrib/contributors/models.py uses FairDMRoles vocabulary
- [X] T077 [US4] Implement Affiliation.save() override in fairdm/contrib/contributors/models.py: Enforce only one is_primary=True per person
- [X] T078 [US4] Create AffiliationQuerySet in fairdm/contrib/contributors/managers.py: Add primary(), current(), past() methods for querying affiliations
- [X] T079 [US4] Create AffiliationManager in fairdm/contrib/contributors/managers.py: Use .from_queryset(AffiliationQuerySet) pattern to expose queryset methods
- [X] T079a [US4] Update Affiliation model in fairdm/contrib/contributors/models.py: Add objects = AffiliationManager() to enable Person.affiliations.primary(), .current() usage

### System Validation for User Story 4

- [X] T080 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` - MUST pass before proceeding
- [X] T081 ⚠️ CRITICAL: Run User Story 4 tests: `poetry run pytest tests/test_contrib/test_contributors/test_models.py::test_*affiliation* tests/test_contrib/test_contributors/test_models.py::test_*role* tests/test_contrib/test_contributors/test_managers.py::test_affiliation_queryset_methods -v` - ALL tests MUST pass

**Checkpoint**: User Story 4 complete - Roles and time-bound affiliations working correctly with queryset-based affiliation queries (Person.affiliations.primary(), Person.affiliations.current())

---

## Phase 9: User Story 5 - Metadata Export and Interoperability (Priority: P5)

**Goal**: TransformRegistry with built-in DataCite/Schema.org/CSL-JSON/ORCID/ROR transforms plus extensible API

**Independent Test**: Export Person/Organization to each format, verify schema compliance, create custom transform, import from external format

### Tests for User Story 5

- [X] T082 [P] [US5] Write test_datacite_export_person in tests/test_contrib/test_contributors/test_transforms.py using TransformTestMixin (MUST FAIL before T092)
- [X] T083 [P] [US5] Write test_schema_org_export_organization in tests/test_contrib/test_contributors/test_transforms.py (MUST FAIL before T093)
- [X] T084 [P] [US5] Write test_csl_json_export in tests/test_contrib/test_contributors/test_transforms.py (MUST FAIL before T094)
- [X] T085 [P] [US5] Write test_orcid_round_trip in tests/test_contrib/test_contributors/test_transforms.py (MUST FAIL before T095)
- [X] T086 [P] [US5] Write test_ror_round_trip in tests/test_contrib/test_contributors/test_transforms.py (MUST FAIL before T096)
- [X] T087 [P] [US5] Write test_transform_registry_registration in tests/test_contrib/test_contributors/test_transforms.py (MUST FAIL before T097)
- [X] T088 [P] [US5] Write test_custom_transform_creation in tests/test_contrib/test_contributors/test_transforms.py (MUST FAIL before T098)

### Implementation for User Story 5

- [X] T089 [P] [US5] Create TransformRegistry singleton in fairdm/contrib/contributors/utils/transforms.py with @register decorator
- [X] T090 [P] [US5] Create BaseTransform abstract class in fairdm/contrib/contributors/utils/transforms.py with to_format() and from_format() methods
- [X] T091 [US5] Implement DataCiteTransform in fairdm/contrib/contributors/utils/transforms.py: Bidirectional Person/Organization ↔ DataCite JSON
- [X] T092 [US5] Implement SchemaOrgTransform in fairdm/contrib/contributors/utils/transforms.py: Bidirectional Person/Organization ↔ Schema.org JSON-LD
- [X] T093 [US5] Implement CSLJSONTransform in fairdm/contrib/contributors/utils/transforms.py: Person → CSL-JSON (for citations)
- [X] T094 [US5] Implement ORCIDTransform in fairdm/contrib/contributors/utils/transforms.py: Bidirectional Person ↔ ORCID API JSON
- [X] T095 [US5] Implement RORTransform in fairdm/contrib/contributors/utils/transforms.py: Bidirectional Organization ↔ ROR API JSON
- [X] T096 [US5] Add to_datacite() / to_schema_org() / to_csl_json() methods to Contributor model in fairdm/contrib/contributors/models.py that delegate to registry
- [X] T097 [US5] Update Person.from_orcid() and Organization.from_ror() in fairdm/contrib/contributors/models.py to use ORCIDTransform/RORTransform

### System Validation for User Story 5

- [X] T098 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` - MUST pass before proceeding
- [X] T099 ⚠️ CRITICAL: Run User Story 5 tests: `poetry run pytest tests/test_contrib/test_contributors/test_transforms.py -v` - ALL tests MUST pass

**Checkpoint**: User Story 5 complete - Transform system working with all formats and extensible

---

## Phase 10: User Story 6 - Query Utilities and Custom Managers (Priority: P6)

**Goal**: Advanced queryset methods for search, filtering, bulk operations, and duplicate detection

**Independent Test**: Use manager methods for common queries, verify query efficiency, test duplicate detection utility

### Tests for User Story 6

- [X] T100 [P] [US6] Write test_claimed_unclaimed_querysets in tests/test_contrib/test_contributors/test_managers.py (MUST FAIL before T106)
- [X] T101 [P] [US6] Write test_contribution_by_role in tests/test_contrib/test_contributors/test_managers.py (MUST FAIL before T107)
- [X] T102 [P] [US6] Write test_contribution_for_entity in tests/test_contrib/test_contributors/test_managers.py (MUST FAIL before T108)
- [X] T103 [P] [US6] Write test_duplicate_detection in tests/test_contrib/test_contributors/test_managers.py (MUST FAIL before T109)

### Implementation for User Story 6

- [X] T104 [US6] Implement PersonQuerySet.claimed() in fairdm/contrib/contributors/managers.py: Filter is_claimed=True
- [X] T105 [US6] Implement PersonQuerySet.unclaimed() in fairdm/contrib/contributors/managers.py: Filter is_claimed=False
- [X] T105a [US6] Implement PersonQuerySet.ghost() in fairdm/contrib/contributors/managers.py: Filter is_claimed=False, email__isnull=True
- [X] T105b [US6] Implement PersonQuerySet.invited() in fairdm/contrib/contributors/managers.py: Filter is_claimed=False, email__isnull=False
- [X] T105c [US6] Implement PersonQuerySet.real() in fairdm/contrib/contributors/managers.py: Exclude is_superuser=True and email="AnonymousUser" (safe for portal queries)
- [X] T106 [US6] Implement ContributionManager.by_role(role_name) in fairdm/contrib/contributors/managers.py: Filter by roles__name
- [X] T107 [US6] Implement ContributionManager.for_entity(obj) in fairdm/contrib/contributors/managers.py: Filter by content_type + object_id
- [X] T108 [US6] Implement detect_duplicate_contributors() utility in fairdm/contrib/contributors/utils/helpers.py: Fuzzy name matching with threshold
- [X] T108a [US6] Update all call sites from Person.contributors.* to Person.objects.real().* (grep for Person.contributors and update)

### System Validation for User Story 6

- [X] T109 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` - MUST pass before proceeding
- [X] T110 ⚠️ CRITICAL: Run User Story 6 tests: `poetry run pytest tests/test_contrib/test_contributors/test_managers.py -v` - ALL tests MUST pass

**Checkpoint**: User Story 6 complete - All query utilities working efficiently

---

## Phase 11: Privacy Controls (Cross-Cutting)

**Goal**: Privacy-aware field visibility based on viewer and claim status

**Independent Test**: Set privacy levels, verify visible fields for different viewer types

### Tests for Privacy

- [X] T111 [P] Write test_privacy_unclaimed_person in tests/test_contrib/test_contributors/test_privacy.py (MUST FAIL before T115)
- [X] T112 [P] Write test_privacy_claimed_person in tests/test_contrib/test_contributors/test_privacy.py (MUST FAIL before T116)
- [X] T113 [P] Write test_get_visible_fields_anonymous in tests/test_contrib/test_contributors/test_privacy.py (MUST FAIL before T117)
- [X] T114 [P] Write test_get_visible_fields_authenticated in tests/test_contrib/test_contributors/test_privacy.py (MUST FAIL before T118)

### Implementation for Privacy

- [X] T115 Implement Contributor.get_visible_fields(viewer) in fairdm/contrib/contributors/models.py: Return field dict based on privacy_settings and viewer
- [X] T116 Add default privacy settings in Person.save() in fairdm/contrib/contributors/models.py: Unclaimed=all public, claimed=email private
- [X] T117 Update contributor detail views in fairdm/contrib/contributors/views/ to use get_visible_fields()

### System Validation for Privacy

- [X] T118 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` - MUST pass before proceeding
- [X] T119 ⚠️ CRITICAL: Run privacy tests: `poetry run pytest tests/test_contrib/test_contributors/test_privacy.py -v` - ALL tests MUST pass

**Checkpoint**: Privacy controls complete and tested

---

## Phase 12: Template Tags & Frontend Integration (Cross-Cutting)

**Goal**: Template tags for contributor filtering and display

**Independent Test**: Use template tags in test templates, verify output

### Tests for Template Tags

- [X] T120 [P] Write test_by_role_filter in tests/test_contrib/test_contributors/test_templatetags.py (MUST FAIL before T123)
- [X] T121 [P] Write test_has_role_filter in tests/test_contrib/test_contributors/test_templatetags.py (MUST FAIL before T124)

### Implementation for Template Tags

- [X] T122 Implement by_role template filter in fairdm/contrib/contributors/templatetags/contributor_tags.py
- [X] T123 Implement has_role template filter in fairdm/contrib/contributors/templatetags/contributor_tags.py

### System Validation for Template Tags

- [X] T124 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` - MUST pass before proceeding
- [X] T125 ⚠️ CRITICAL: Run template tag tests: `poetry run pytest tests/test_contrib/test_contributors/test_templatetags.py -v` - ALL tests MUST pass

**Checkpoint**: Template tags complete and tested

---

## Phase 13: Demo App Updates (Constitution Principle VII)

**Goal**: Update fairdm_demo to demonstrate all new features

**Independent Test**: Run demo app tests, verify demo models use Affiliation, verify admin views work

### Tests for Demo App

- [X] T126 [P] Write test_demo_person_creation in fairdm_demo/tests/test_contributors.py (MUST FAIL before T130)
- [X] T127 [P] Write test_demo_organization_ownership in fairdm_demo/tests/test_contributors.py (MUST FAIL before T131)
- [X] T128 [P] Write test_demo_affiliation_workflow in fairdm_demo/tests/test_contributors.py (MUST FAIL before T132)
- [X] T129 [P] Write test_demo_admin_views_load in fairdm_demo/tests/test_contributors.py (MUST FAIL before T133)

### Implementation for Demo App

- [X] T130 Update fairdm_demo/models.py: Replace OrganizationMember with Affiliation usage examples
- [X] T131 Update fairdm_demo/factories.py: Add AffiliationFactory, update PersonFactory with claimed/unclaimed examples
- [X] T132 Add example transform usage to fairdm_demo/models.py or README.md
- [X] T133 Add example privacy control usage to fairdm_demo/models.py

### System Validation for Demo App

- [X] T134 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` - MUST pass before proceeding
- [X] T135 ⚠️ CRITICAL: Run demo app tests: `poetry run pytest fairdm_demo/tests/test_contributors.py -v` - ALL tests MUST pass

**Checkpoint**: Demo app updated and all demo tests passing

---

## Phase 14: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup and verification before completion

- [X] T136 [P] Update developer documentation in specs/009-fairdm-contributors/quickstart.md with final usage examples
- [X] T137 [P] Update API contracts in specs/009-fairdm-contributors/contracts/api-contracts.md with any signature changes
- [X] T138 Code review and refactoring: Remove debug print statements, add docstrings to all public methods
- [X] T139 Verify all 5 identified bugs from plan.md are fixed (from_ror classmethod, clean() validation, sync timing, etc.)
- [X] T140 Run quickstart.md validation: Execute all code examples from quickstart.md to ensure they work
- [X] T141 Performance verification: Test contributor lookup with 10,000+ records meets < 200ms requirement (SC-007)
- [X] T142 ORCID/ROR sync performance: Verify sync completes < 5s per identifier (SC-002, SC-003)

### Schema Validation

- [X] T143 [P] Write test_datacite_schema_validation in tests/test_contrib/test_contributors/test_transforms.py: Use official DataCite JSON schema validator to verify exports
- [X] T144 [P] Write test_schema_org_validation in tests/test_contrib/test_contributors/test_transforms.py: Use schema.org validator or JSON-LD processor to verify exports
- [X] T145 Add DataCite JSON schema validation in fairdm/contrib/contributors/transforms/datacite.py: Validate export() output against official schema
- [X] T146 Add Schema.org validation utility in fairdm/contrib/contributors/transforms/schemaorg.py: Validate JSON-LD structure

### Documentation Updates (Constitution Principle VI)

- [X] T147 Create docs/portal-development/contributors.md: Comprehensive developer guide covering Person model (AUTH_USER_MODEL, is_claimed BooleanField, Ghost/Invited/Claimed/Banned state machine, privacy settings), unified manager approach (Person.objects.real() for portal queries, objects.claimed()/unclaimed()/ghost()/invited()), Organization model (ROR sync, ownership via manage_organization), Affiliation model (type field state machine, PartialDateField), Contribution model (roles, GFK relationships), and STRONG recommendation that portal developers maintain separate superuser and Person accounts
- [X] T148 Add TransformRegistry API documentation to docs/portal-development/contributors.md: Document BaseTransform interface, bidirectional transform creation, built-in adapters (DataCite, Schema.org, CSL-JSON, ORCID, ROR), and example custom transformer implementation
- [X] T149 Add privacy controls section to docs/portal-development/contributors.md: Document privacy_settings JSONField structure, get_visible_fields() method, default privacy behavior for claimed vs unclaimed profiles
- [X] T150 Add claiming data model section to docs/portal-development/contributors.md: Document is_claimed BooleanField, state machine (Ghost→Invited→Claimed→Banned), queryset methods (claimed()/unclaimed()/ghost()/invited()), create_unclaimed() method, and note that claiming flows are implemented in Feature 010
- [X] T151 Create docs/portal-administration/managing_contributors.md: Admin guide covering Person admin interface (unified auth + contributor fields), Organization admin (inline memberships, ownership transfer), Affiliation verification workflow (type field PENDING→MEMBER→ADMIN→OWNER), and ORCID/ROR sync troubleshooting
- [X] T152 Update docs/portal-development/index.md toctree: Add contributors.md to "Defining models" section before using_the_registry
- [X] T153 Update docs/portal-administration/index.md toctree: Add managing_contributors.md to main toctree after managing_users_and_permissions
- [X] T154 Add inline code examples to all new documentation: Every API method, manager, and configuration option MUST have a working code example
- [X] T155 Add migration guide to docs/portal-development/contributors.md: Document AUTH_USER_MODEL change implications for existing portals, OrganizationMembership→Affiliation migration path, and settings.py updates required

### Final System Validation

- [X] T156 ⚠️ CRITICAL: Run full Django system checks: `poetry run python manage.py check --deploy` - MUST pass
- [X] T157 ⚠️ CRITICAL: Run contributor-specific tests: `poetry run pytest tests/test_contrib/test_contributors/ fairdm_demo/tests/test_contributors.py -v --cov=fairdm/contrib/contributors` - ALL tests MUST pass with >90% coverage
- [X] T158 ⚠️ CRITICAL: Verify all documentation pages render correctly: Build Sphinx docs locally and verify no warnings or broken links for new contributor documentation pages
- [X] T159 ⚠️ CRITICAL: Run ENTIRE project test suite: `poetry run pytest -v` - ALL tests across the entire project MUST pass. This ensures the contributors feature has not broken any existing functionality elsewhere in FairDM. DO NOT mark this task complete unless the full test suite passes with ZERO failures.

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
- **Foundational migrations** T006-T008c can be written in parallel (but must run sequentially - T006→T007→T008→T008a→T008b→T008c)
- **Foundational test fixtures** T009-T010 can run in parallel
- **Within each user story**: All test-writing tasks marked [P] can run in parallel
- **After US1 complete**: US2, US3, US3b, US4, US5, US6 can be worked on in parallel by different team members
- **Privacy and Template Tags**: Can be worked on in parallel after US1 complete
- **Manager unification (US6)**: T104-T105c (queryset methods) can be implemented in parallel, then T025-T025b (unification) combines them, then T108a (call site updates) last

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
Task T019: "Add is_claimed BooleanField to Person model"
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

### Key Architectural Decisions (from research.md)

- **is_claimed BooleanField** (D3): Explicit ownership tracking. State machine: Ghost (email=NULL, is_claimed=False, is_active=True) → Invited (email present, is_claimed=False, is_active=True) → Claimed (is_claimed=True, is_active=True) → Banned (is_claimed=True, is_active=False). Ghosts and Invited have is_active=True to enable invitation/password reset flows.
- **Manager Unification** (D8): Merge PersonalContributorsManager into UserManager using .from_queryset(PersonQuerySet). Single manager with Person.objects.real() to exclude superusers/AnonymousUser. Portal developers MUST maintain separate superuser and Person accounts.
- **Affiliation Queries** (D3 update): Person.primary_affiliation() and Person.current_affiliations() removed - use Person.affiliations.primary() and Person.affiliations.current() queryset methods on Affiliation model instead. Keeps affiliation logic on the Affiliation model where it belongs.
- **No Property Aliases**: given/family property aliases removed from Person - transformers will handle first_name/last_name access patterns as needed.
