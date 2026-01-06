# Tasks: Documentation Infrastructure

**Input**: Design documents from `/specs/003-docs-infrastructure/`
**Prerequisites**: plan.md, spec.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and documentation structure verification

- [X] T001 Verify existing Sphinx configuration in docs/conf.py is compatible with planned changes
- [X] T002 [P] Create checklists directory structure in .specify/templates/
- [X] T003 [P] Create validation scripts directory in .specify/scripts/powershell/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core documentation infrastructure that MUST be complete before ANY user story implementation

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create feature documentation checklist template at .specify/templates/feature-docs-checklist.md
- [X] T005 Document information architecture decision criteria in docs/contributing/documentation-standards.md
- [X] T006 [P] Add sphinx.ext.linkcheck configuration to docs/conf.py
- [X] T007 [P] Configure linkcheck to treat internal link failures as hard errors in docs/conf.py
- [X] T008 Configure linkcheck to treat external link failures as warnings in docs/conf.py
- [X] T009 Add MyST extension configuration for cross-references in docs/conf.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Contributor Finds Where to Add Documentation (Priority: P1) 🎯 MVP

**Goal**: Create clear information architecture documentation that tells contributors exactly where to add different types of documentation

**Independent Test**: Ask a contributor "where do I document X?" and they can answer correctly in under 30 seconds by consulting docs/contributing/documentation-standards.md

### Implementation for User Story 1

- [X] T010 [P] [US1] Create information architecture table in docs/contributing/documentation-standards.md showing four sections
- [X] T011 [P] [US1] Document developer-guide section purpose and example pages in docs/contributing/documentation-standards.md
- [X] T012 [P] [US1] Document admin-guide section purpose and example pages in docs/contributing/documentation-standards.md
- [X] T013 [P] [US1] Document contributor-guide section purpose and example pages in docs/contributing/documentation-standards.md
- [X] T014 [P] [US1] Document contributing section purpose and example pages in docs/contributing/documentation-standards.md
- [X] T015 [US1] Add decision criteria for choosing between sections in docs/contributing/documentation-standards.md
- [X] T016 [US1] Document governance materials location (.specify/memory/) in docs/contributing/documentation-standards.md
- [X] T017 [US1] Document specifications location (specs/) in docs/contributing/documentation-standards.md
- [X] T018 [US1] Add examples of "where does X go" decisions in docs/contributing/documentation-standards.md
- [X] T019 [US1] Update docs/contributing/index.md to reference documentation-standards.md
- [X] T020 [US1] Add section on when to create new page vs update existing in docs/contributing/documentation-standards.md

**Checkpoint**: Contributors can now find where to place documentation by reading documentation-standards.md

---

## Phase 4: User Story 2 - Contributor Uses Feature Documentation Checklist (Priority: P2)

**Goal**: Provide structured checklist template that ensures all required documentation is updated when shipping features

**Independent Test**: Complete a feature checklist for a sample feature and verify all relevant documentation sections are identified

### Implementation for User Story 2

- [X] T021 [P] [US2] Define checklist structure with feature types in .specify/templates/feature-docs-checklist.md
- [X] T022 [P] [US2] Add checklist section for new core models in .specify/templates/feature-docs-checklist.md
- [X] T023 [P] [US2] Add checklist section for new UI components in .specify/templates/feature-docs-checklist.md
- [X] T024 [P] [US2] Add checklist section for configuration changes in .specify/templates/feature-docs-checklist.md
- [X] T025 [P] [US2] Add checklist section for breaking changes in .specify/templates/feature-docs-checklist.md
- [X] T026 [US2] Document how to use the checklist in .specify/templates/feature-docs-checklist.md header
- [X] T027 [US2] Add examples of completed checklists in .specify/templates/feature-docs-checklist.md
- [X] T028 [US2] Reference checklist template from docs/contributing/documentation-standards.md
- [X] T029 [US2] Add guidance on when checklist is required in docs/contributing/documentation-standards.md
- [X] T030 [US2] Create sample completed checklist for this feature in specs/003-docs-infrastructure/checklists/documentation.md

**Checkpoint**: Contributors can copy and complete feature documentation checklists using the template

---

## Phase 5: User Story 3 - Reader Traces Documentation to Specification (Priority: P3)

**Goal**: Enable readers to follow links from documentation to specs and constitution for context and rationale

**Independent Test**: Follow a docs-to-spec link and verify the spec contains the expected rationale

### Implementation for User Story 3

- [X] T031 [P] [US3] Document spec cross-reference pattern in docs/contributing/documentation-standards.md
- [X] T032 [P] [US3] Document constitution cross-reference pattern in docs/contributing/documentation-standards.md
- [X] T033 [P] [US3] Add examples of spec cross-references with context in docs/contributing/documentation-standards.md
- [X] T034 [P] [US3] Add examples of constitution cross-references in docs/contributing/documentation-standards.md
- [X] T035 [US3] Update developer-guide/documentation.md to explain cross-reference patterns
- [X] T036 [US3] Add cross-reference from docs/index.md to constitution in .specify/memory/constitution.md
- [X] T037 [US3] Add cross-reference from docs/developer-guide/index.md to relevant specs
- [X] T038 [US3] Document stable anchor naming conventions for constitution sections in docs/contributing/documentation-standards.md
- [X] T039 [US3] Create examples showing how specs should link back to constitution principles in docs/contributing/documentation-standards.md

**Checkpoint**: Readers can trace documentation to specifications and constitution using consistent link patterns

---

## Phase 6: User Story 4 - Documentation Validation Passes (Priority: P1) 🎯 CRITICAL

**Goal**: Automated validation catches documentation errors before they reach users

**Independent Test**: Run validation on both passing and intentionally broken documentation; verify failures provide actionable errors

### Implementation for User Story 4

- [X] T040 [P] [US4] Create validate-docs.ps1 script in .specify/scripts/powershell/
- [X] T041 [P] [US4] Add Sphinx build check with -W flag in validate-docs.ps1
- [X] T042 [P] [US4] Add linkcheck execution for internal links in validate-docs.ps1
- [X] T043 [P] [US4] Add linkcheck execution for external links (warnings only) in validate-docs.ps1
- [X] T044 [US4] Create Python validator for checklist completeness in .specify/scripts/powershell/validate-checklists.py (must verify: all items marked [x], each item specifies target section and required content, checklist status progresses from not-started → in-progress → completed per plan.md Entity 2 validation rules)
- [X] T045 [US4] Add checklist validator to validate-docs.ps1 script
- [X] T046 [US4] Create GitHub Actions workflow at .github/workflows/docs-validation.yml
- [X] T047 [US4] Configure CI to run validate-docs.ps1 on PR events in .github/workflows/docs-validation.yml
- [X] T048 [US4] Configure CI to hard-block on internal link failures in .github/workflows/docs-validation.yml
- [X] T049 [US4] Configure CI to warn (not block) on external link failures in .github/workflows/docs-validation.yml
- [X] T050 [US4] Add validation status badge to docs/index.md
- [X] T051 [US4] Document validation process in docs/contributing/documentation-standards.md
- [X] T052 [US4] Add local validation instructions in docs/contributing/documentation-standards.md
- [X] T053 [US4] Define minimum quality expectations in docs/contributing/documentation-standards.md
- [X] T054 [US4] Create test documentation files with known errors for validation testing in tests/test_docs/
- [X] T055 [US4] Verify validation catches internal link errors using test files in tests/test_docs/ (verified via linkcheck output - internal link errors detected)
- [X] T056 [US4] Verify validation warns on external link errors using test files in tests/test_docs/ (verified via linkcheck output - external links warn, don't fail build)

**Checkpoint**: Documentation validation runs automatically in CI and hard-blocks PRs with internal errors

---

## Phase 7: User Story 5 - Existing Documentation Brought Into Compliance (Priority: P2)

**Goal**: Identify and remediate non-conforming existing documentation

**Independent Test**: Run conformance audit and track remediation of identified issues

### Implementation for User Story 5

- [X] T057 [P] [US5] Create conformance audit script in .specify/scripts/powershell/audit-docs.ps1
- [X] T058 [P] [US5] Add checker for missing spec cross-references in audit-docs.ps1
- [X] T059 [P] [US5] Add checker for misplaced files in directory structure in audit-docs.ps1
- [X] T060 [P] [US5] Add checker for missing alt text on images in audit-docs.ps1
- [X] T061 [P] [US5] Add checker for heading hierarchy violations in audit-docs.ps1
- [X] T062 [US5] Generate audit report with file paths and specific issues in audit-docs.ps1 (output format: JSON with schema fields per plan.md Entity 6: audit_date, pages_scanned_count, non_conforming_pages[], issues_by_category{}, remediation_steps[], priority per issue)
- [X] T063 [US5] Add remediation suggestions to audit report output in audit-docs.ps1
- [X] T064 [US5] Document how to run conformance audit in docs/contributing/documentation-standards.md
- [X] T065 [US5] Run initial conformance audit and generate baseline report
- [ ] T066 [US5] Prioritize high-traffic pages for remediation in audit report
- [X] T067 [US5] Create migration plan with phases for remediating existing docs in specs/003-docs-infrastructure/migration-plan.md
- [ ] T068 [US5] Add missing spec cross-references to high-priority pages identified in audit
- [ ] T069 [US5] Fix misplaced documentation files identified in audit
- [ ] T070 [US5] Add alt text to images identified in audit

**Checkpoint**: Conformance audit can identify non-conforming documentation and track remediation progress

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final integration

- [X] T071 [P] Add MyST syntax examples to docs/contributing/documentation-standards.md
- [X] T072 [P] Document common documentation patterns in docs/contributing/documentation-standards.md
- [X] T073 [P] Add troubleshooting section for validation errors in docs/contributing/documentation-standards.md
- [X] T074 [P] Create developer-guide/documentation.md summarizing documentation workflow
- [X] T075 Update docs/developer-guide/index.md to include link to documentation.md
- [X] T076 Add FAQ section to docs/contributing/documentation-standards.md
- [X] T077 Document how to handle deprecated features in documentation in docs/contributing/documentation-standards.md
- [X] T078 Document how to mark experimental features in documentation in docs/contributing/documentation-standards.md
- [X] T079 Run full documentation build and verify all pages render correctly (build succeeded with 51 warnings - warnings documented in audit baseline)
- [X] T080 Run complete validation suite and verify all checks pass (linkcheck completed - 11 external broken links found, documented in migration plan)
- [X] T081 Create this feature's documentation checklist in specs/003-docs-infrastructure/checklists/documentation.md and mark complete
- [X] T082 Update constitution cross-references if any constitutional principles were referenced

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3, P1)**: Depends on Foundational completion - Must complete first (highest priority)
- **User Story 4 (Phase 6, P1)**: Can start after Foundational, should complete early (critical validation)
- **User Story 2 (Phase 4, P2)**: Can start after US1 completion (references IA document)
- **User Story 5 (Phase 7, P2)**: Depends on US1 and US4 completion (needs IA and validation tools)
- **User Story 3 (Phase 5, P3)**: Can start after US1 completion (references IA document)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories
- **User Story 4 (P1)**: Can start after Foundational - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 (references documentation-standards.md created in US1)
- **User Story 3 (P3)**: Depends on US1 (references documentation-standards.md created in US1)
- **User Story 5 (P2)**: Depends on US1 (needs IA to audit against) and US4 (uses validation tools)

### Within Each User Story

- Setup and Foundational tasks must complete before user stories
- Tasks marked [P] within a phase can run in parallel
- User Story 1 MUST complete before User Story 2, 3, or 5 (they depend on documentation-standards.md)
- User Story 4 can run in parallel with User Story 1

### Parallel Opportunities

**Phase 1 (Setup)**: T002 and T003 can run in parallel

**Phase 2 (Foundational)**: T006-T009 can run in parallel after T004-T005 complete

**User Story 1**: T010-T014 (section documentation) can all run in parallel; then T015-T020 sequentially

**User Story 2**: T021-T025 (checklist sections) can all run in parallel; then T026-T030 sequentially

**User Story 3**: T031-T034 (documentation patterns) can all run in parallel; then T035-T039 sequentially

**User Story 4**: T040-T043 (script components) can all run in parallel; validation testing (T054-T056) can run in parallel

**User Story 5**: T057-T061 (audit checkers) can all run in parallel; remediation tasks (T068-T070) can run in parallel

**Polish Phase**: T071-T074 can all run in parallel

---

## Parallel Example: User Story 1

```bash
# These tasks can all run simultaneously:
git checkout -b task/T010-ia-table
git checkout -b task/T011-developer-guide-docs
git checkout -b task/T012-admin-guide-docs
git checkout -b task/T013-contributor-guide-docs
git checkout -b task/T014-contributing-docs

# Each creates different sections in docs/contributing/documentation-standards.md
# Merge all branches, then proceed with sequential tasks T015-T020
```

---

## Implementation Strategy

### Minimum Viable Product (MVP)

**MVP Scope**: User Story 1 + User Story 4 (Foundation)

This delivers the core value:

1. Contributors know where to document (US1)
2. Documentation is automatically validated (US4)

**Why this MVP**: These two stories provide immediate value - clear guidance and quality enforcement. Other stories build on this foundation.

**MVP Tasks**: T001-T009 (Setup + Foundational) + T010-T020 (US1) + T040-T056 (US4) = 56 tasks

### Incremental Delivery

After MVP, deliver in priority order:

1. **User Story 2** (Checklists) - Operationalizes the IA from US1
2. **User Story 5** (Conformance) - Brings existing docs into compliance
3. **User Story 3** (Traceability) - Adds spec cross-references
4. **Polish** - Final improvements

### Testing Strategy

- Validation testing is built into User Story 4 (T054-T056)
- Each user story has independent test criteria in its acceptance scenarios
- Manual testing: Follow quickstart guide and verify contributor workflow
- Conformance audit serves as integration test for all stories

---

## Total Tasks: 82

- Setup: 3 tasks
- Foundational: 6 tasks (BLOCKING)
- User Story 1: 11 tasks
- User Story 2: 10 tasks
- User Story 3: 9 tasks
- User Story 4: 17 tasks
- User Story 5: 14 tasks
- Polish: 12 tasks

**Estimated Complexity**:

- Simple tasks (file creation, documentation): ~60% (49 tasks)
- Medium tasks (script writing, validation logic): ~30% (25 tasks)
- Complex tasks (CI integration, audit tooling): ~10% (8 tasks)
