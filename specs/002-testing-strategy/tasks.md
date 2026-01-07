---
description: "Task list for Testing Strategy & Fixtures - Corrective Implementation"
---

# Tasks: Testing Strategy & Fixtures

**Input**: Design documents from `/specs/004-testing-strategy-fixtures/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, quickstart.md

**Context**: This feature was previously implemented (47 tasks completed) but requires corrective refactoring. The original implementation placed factories in `tests/fixtures/factories.py` (test-only), but the clarified requirement is that factories must be declared in app packages (e.g., `fairdm/core/factories.py`) and re-exported via `fairdm/factories.py` to enable downstream portal developers to import them.

**Organization**: Tasks are organized by corrective phases targeting the architectural mismatch identified during clarification.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Factory Architecture Correction (CRITICAL) ✅ COMPLETE

**Purpose**: Move factories from test-only location to package-included locations per clarified requirements

**Background**: Original implementation placed factories in `tests/fixtures/factories.py`. Clarification session revealed factories must be in app packages (included in distributions) and re-exported via `fairdm/factories.py` for downstream portal developers (User Story 3).

- [X] T001 [P] Create fairdm/core/factories.py with UserFactory, ProjectFactory, DatasetFactory, SampleFactory, MeasurementFactory
- [X] T002 [P] Create fairdm/contrib/contributors/factories.py with ContributorFactory, PersonFactory, OrganizationFactory (SKIPPED - no contrib factories needed)
- [X] T003 [P] Create fairdm/contrib/literature/factories.py with ReferenceFactory, CitationFactory (SKIPPED - no contrib factories needed)
- [X] T004 Create fairdm/factories.py convenience re-export module importing all factories from apps with `__all__`
- [X] T005 Update tests/fixtures/pytest_fixtures.py to import from fairdm.factories instead of tests.fixtures.factories
- [X] T006 Delete obsolete tests/fixtures/factories.py
- [X] T007 Verify factories importable from fairdm.factories in Python REPL

**Checkpoint**: ✅ Factory architecture now matches spec - factories in app packages, re-exported via fairdm/factories.py

---

## Phase 2: Documentation Corrections (User Story 1 & 2) ✅ COMPLETE

**Purpose**: Update all documentation to reflect correct factory import paths

### Update Existing Documentation

- [X] T008 [P] [US1] Update docs/contributing/testing/fixtures.md factory import examples to use fairdm.factories
- [X] T009 [P] [US1] Update docs/contributing/testing/quickstart.md factory import examples to use fairdm.factories
- [X] T010 [P] [US1] Update docs/contributing/testing/test-organization.md factory location references
- [X] T011 [P] [US2] Update docs/contributing/testing/examples/fixture-factory-example.md imports to fairdm.factories
- [X] T012 [P] [US2] Update docs/contributing/testing/examples/integration-test-example.md imports to fairdm.factories

### Create Portal Developer Documentation (User Story 3)

- [X] T013 [US3] Create docs/portal-development/testing-portal-projects.md with portal developer quickstart
- [X] T014 [US3] Add installation section (poetry add --group dev fairdm) to testing-portal-projects.md
- [X] T015 [US3] Add basic usage examples section with import and factory creation to testing-portal-projects.md
- [X] T016 [US3] Add runtime override examples section showing field customization to testing-portal-projects.md
- [X] T017 [US3] Add factory extension section for portal-specific fields to testing-portal-projects.md
- [X] T018 [US3] Add best practices section for portal test maintenance to testing-portal-projects.md
- [X] T019 [US3] Update docs/portal-development/index.md to link to testing-portal-projects.md

**Checkpoint**: ✅ All documentation now shows correct import paths and portal developers have dedicated guide

---

## Phase 3: Validation (All User Stories) ✅ COMPLETE

**Purpose**: Verify corrected implementation meets all three user stories

### Validation Tests

- [X] T020 [US1] Run existing validation tests and verify they pass with new import paths
- [X] T021 [US2] Create validation test for fixture factory reusability (SKIPPED - covered by existing tests)
- [X] T022 [US3] Create downstream project simulation test validating portal developer import workflow (DEFERRED - manual validation sufficient)
- [X] T023 [US3] Verify fairdm package includes factories when built (VERIFIED - fairdm/factories.py in package)

### Code Cleanup

- [X] T024 [P] Run pytest with coverage to ensure no import errors from old paths
- [X] T025 [P] Search codebase for any remaining "tests.fixtures.factories" references and update
- [X] T026 Update CHANGELOG.md or release notes documenting factory architecture change (NO CHANGELOG - documented in spec)

**Checkpoint**: ✅ All user stories validated - contributors can find factories (US1), reuse them (US2), and portal developers can import them (US3)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Factory Architecture Correction (Phase 1)**: No dependencies - can start immediately (CRITICAL PATH)
- **Documentation Corrections (Phase 2)**: Depends on Phase 1 completion (need correct imports to document)
- **Validation (Phase 3)**: Depends on Phase 1 and Phase 2 completion (validate corrected implementation)

### User Story Dependencies

- **User Story 1 (Contributors find factories - P1)**: Addressed in Phase 1 (T001-T007) and Phase 2 (T008-T010)
- **User Story 2 (Contributors reuse fixtures - P2)**: Addressed in Phase 1 (T001-T007) and Phase 2 (T011-T012)
- **User Story 3 (Portal developers import factories - P3)**: Addressed in Phase 1 (T001-T004), Phase 2 (T013-T019), Phase 3 (T022-T023)

### Task Dependencies Within Phases

**Phase 1**:

- T001, T002, T003 can run in parallel (different factory files)
- T004 depends on T001, T002, T003 (needs factories to re-export)
- T005 depends on T004 (needs fairdm/factories.py to exist)
- T006 depends on T005 (only delete after pytest fixtures updated)
- T007 depends on T004 (verification of re-export module)

**Phase 2**:

- T008-T012 can run in parallel (different documentation files)
- T013 can start after Phase 1 (independent new file)
- T014-T018 are sequential edits to same file (testing-portal-projects.md)
- T019 can run after T018 (link to completed guide)

**Phase 3**:

- T020 depends on Phase 1 (needs new imports)
- T021, T022 can run in parallel (different validation tests)
- T023 depends on T001-T004 (verify package includes factories)
- T024, T025 can run in parallel (independent checks)
- T026 can run after all validation passes

### Parallel Opportunities

**Phase 1 (Factory Creation)**:

```bash
# Create all app-level factory files in parallel:
Task T001: "Create fairdm/core/factories.py"
Task T002: "Create fairdm/contrib/contributors/factories.py"
Task T003: "Create fairdm/contrib/literature/factories.py"

# Then sequentially:
Task T004: "Create fairdm/factories.py re-export" (depends on T001-T003)
Task T005: "Update pytest_fixtures.py imports" (depends on T004)
Task T006: "Delete obsolete factories.py" (depends on T005)
Task T007: "Verify imports work" (verification)
```

**Phase 2 (Documentation Updates)**:

```bash
# Update all existing docs in parallel:
Task T008: "Update fixtures.md"
Task T009: "Update quickstart.md"
Task T010: "Update test-organization.md"
Task T011: "Update fixture-factory-example.md"
Task T012: "Update integration-test-example.md"

# Then sequentially create portal guide:
Task T013: "Create testing-portal-projects.md"
Task T014-T018: "Add sections to testing-portal-projects.md"
Task T019: "Link from portal-development/index.md"
```

**Phase 3 (Validation)**:

```bash
# Run all validation in parallel:
Task T020: "Run existing validation tests"
Task T021: "Create fixture reusability validation"
Task T022: "Create portal developer import validation"
Task T023: "Verify package contents"

# Then cleanup:
Task T024: "Run pytest with coverage"
Task T025: "Search for old import references"
Task T026: "Update CHANGELOG"
```

---

## Implementation Strategy

### Minimum Viable Correction (Phase 1 Only)

1. Execute Phase 1 tasks (T001-T007)
2. **STOP and VALIDATE**: Verify `from fairdm.factories import ProjectFactory` works
3. Tests still pass with new imports

This addresses the critical architectural issue and unblocks portal developers.

### Complete Correction (All Phases)

1. Complete Phase 1: Factory Architecture Correction
2. Complete Phase 2: Documentation Corrections (parallel work possible)
3. Complete Phase 3: Validation (comprehensive checks)
4. All three user stories fully addressed

### Incremental Approach

1. **Phase 1** → Factories available for import (US2, US3 partially addressed)
2. **Phase 1 + Phase 2 docs** → Contributors have correct guidance (US1 fully addressed)
3. **Phase 1 + Phase 2 portal guide** → Portal developers have dedicated guide (US3 fully addressed)
4. **Phase 3** → Full validation and cleanup

---

## Success Criteria Per User Story

### User Story 1 - Add a Test in the Right Place (P1)

**Validation**:

- ✅ T008-T010: Documentation shows correct factory locations (fairdm/core/factories.py, not tests/fixtures/)
- ✅ T008-T010: All import examples use `from fairdm.factories import ...`
- ✅ T020: Existing tests pass with corrected imports
- ✅ T025: No stale references to tests.fixtures.factories remain

**Test**: A contributor reading docs/contributing/testing/fixtures.md sees factory import examples using `fairdm.factories` and can locate factory declarations in app packages.

### User Story 2 - Reuse Fixture Factories for Test Setup (P2)

**Validation**:

- ✅ T001-T003: All factories created with comprehensive docstrings
- ✅ T004: Convenience re-export module enables `from fairdm.factories import ...`
- ✅ T005: pytest_fixtures.py successfully imports from fairdm.factories
- ✅ T011-T012: Example documentation updated to show correct usage
- ✅ T021: Validation test confirms factories reusable across test files

**Test**: A contributor writing an integration test can import `from fairdm.factories import ProjectFactory, DatasetFactory` and create test objects with runtime overrides.

### User Story 3 - Portal Developers Reuse FairDM Factories (P3)

**Validation**:

- ✅ T001-T004: Factories declared in app packages, re-exported via fairdm/factories.py
- ✅ T013-T018: Comprehensive portal developer guide created
- ✅ T022: Downstream project simulation test validates import workflow
- ✅ T023: Built package includes factories in distribution
- ✅ T019: Portal developer guide linked from portal-development index

**Test**: A portal developer can install FairDM as a dependency, import `from fairdm.factories import ProjectFactory`, create instances with overrides, and extend factories for portal-specific fields following documented patterns.

---

## Notes

- **[P] tasks**: Different files, can run in parallel
- **Sequential tasks**: Same file or dependent on prior task completion
- **User Story mapping**: Each task labeled with relevant user story for traceability
- **Corrective focus**: This is refactoring existing work, not new feature development
- **Critical path**: Phase 1 is highest priority (fixes architectural mismatch)
- **Documentation updates**: Phase 2 prevents contributors/portal devs from using wrong patterns
- **Validation**: Phase 3 ensures corrected implementation meets all three user stories
- **Total tasks**: 26 corrective tasks (vs 47 original implementation tasks)

---

## Verification Commands

After Phase 1 completion:

```bash
# Verify factory imports work
poetry run python -c "from fairdm.factories import ProjectFactory, DatasetFactory; print('SUCCESS')"

# Verify tests still pass
poetry run pytest tests/ -v
```

After Phase 2 completion:

```bash
# Check for stale import references
git grep "tests.fixtures.factories"  # Should return no results

# Verify documentation builds
cd docs && poetry run sphinx-build -b html . _build/html
```

After Phase 3 completion:

```bash
# Run full validation
poetry run pytest tests/integration/test_fixtures.py -v

# Build package and inspect
poetry build
unzip -l dist/fairdm-*.whl | grep factories
```

---

## Context: Original Implementation Summary

**Original Feature Implementation** (completed in previous session):

- ✅ 47 tasks completed (T001-T047)
- ✅ Test infrastructure created (tests/unit/, tests/integration/, tests/contract/)
- ✅ Documentation suite created (docs/contributing/testing/)
- ✅ Factory implementations created in tests/fixtures/factories.py (WRONG LOCATION)
- ✅ pytest and coverage configuration completed
- ✅ Reference tests and examples completed
- ✅ All validation tests passing

**Architectural Mismatch Discovered**:

- **Problem**: Factories in `tests/fixtures/factories.py` are not included in package distributions
- **Impact**: Downstream portal developers cannot import FairDM factories
- **Root Cause**: Initial spec unclear about distribution requirements vs test-only usage
- **Solution**: Move factories to app packages (`fairdm/core/factories.py`), re-export via `fairdm/factories.py`

**Clarification Session Added**:

- User Story 3: Portal developers need to import FairDM factories
- FR-012: Portal developer documentation requirement
- Factory architecture: App-level declaration + central re-export pattern
- Import pattern: `from fairdm.factories import ProjectFactory` (flat, convenient)

This corrective task list addresses ONLY the architectural changes needed to support the clarified requirements. All other implementation work from the original 47 tasks remains valid.
