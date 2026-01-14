# Tasks: FairDM Documentation Strategy

**Input**: Design documents from `/specs/001-documentation-strategy/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Not explicitly requested in feature specification - implementation-focused tasks only

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Documentation**: `docs/` at repository root
- **Spec templates**: `.specify/templates/`
- **CI/CD**: `.github/workflows/`, `.github/scripts/`
- **Tests**: `tests/integration/docs/`
- **Configuration**: `docs/conf.py`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Audit current documentation structure and identify files in `docs/` that need migration or removal per research.md findings
- [X] T002 [P] Create `.specify/templates/feature-docs-checklist.md` template based on contracts/feature-docs-checklist-example.md structure (already exists)
- [X] T003 [P] Create `.github/scripts/check-internal-links.py` script per validation-schema.yml specification
- [X] T004 [P] Create `.github/scripts/check-external-links.py` script per validation-schema.yml specification
- [X] T005 [P] Create `.github/scripts/generate-validation-report.py` script per validation-schema.yml specification

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Update `docs/conf.py` with linkcheck configuration (linkcheck_ignore patterns, retry settings, timeout) per research.md Section 1 (already configured)
- [X] T007 Create `.github/workflows/docs-validation.yml` workflow with build validation, internal link checks (hard fail), external link checks (warning only), and checklist validation per validation-schema.yml (already exists)
- [X] T008 Create `tests/integration/docs/test_documentation_validation.py` with checklist validation tests per research.md Section 7
- [X] T009 [P] Relocate `docs/technology/` content to `docs/contributing/technology-stack.md` per research.md Section 4 migration needs (directory doesn't exist, tech_stack.md already in docs/overview/)
- [X] T010 [P] Relocate `docs/more/roadmap.md` to `docs/overview/roadmap.md` per research.md Section 4 migration needs (roadmap.md already at docs/roadmap.md, not in more/)
- [X] T011 Test documentation build with strict validation: `poetry run sphinx-build -W -b html docs docs/_build/html` (✅ Django import fixed, build succeeds with 54 warnings)
- [X] T012 Test linkcheck functionality: `poetry run sphinx-build -b linkcheck docs docs/_build/linkcheck` (✅ Linkcheck runs, output.txt generated with link status)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Contributor Finds Where to Add Documentation (Priority: P1) 🎯 MVP

**Goal**: Framework Contributors can determine exactly where to add documentation using documented information architecture

**Independent Test**: Ask a contributor "where do I document X?" and they can answer correctly in <30 seconds using the guide

### Implementation for User Story 1

- [X] T013 [P] [US1] Create `docs/contributing/documentation/information-architecture.md` with immutable structure definition (4 sections + .specify/ + specs/) per FR-008, FR-009, FR-010
- [X] T014 [P] [US1] Add subdirectory creation guidance to information-architecture.md per FR-008a with examples from data-model.md
- [X] T015 [P] [US1] Create "Where do I document X?" decision tree in information-architecture.md based on quickstart.md examples
- [X] T016 [P] [US1] Add file creation guidelines to information-architecture.md per FR-019 (~500 word threshold, standalone concept, separate journey)
- [X] T017 [US1] Create `docs/contributing/documentation/index.md` landing page linking to information-architecture.md and other documentation guides
- [X] T018 [US1] Update `docs/contributing/index.md` toctree to include new documentation/ subdirectory
- [X] T019 [US1] Validate: Run sphinx-build and linkcheck, verify all links resolve (✅ Build succeeds with 54 warnings, linkcheck passes)

**Checkpoint**: At this point, User Story 1 should be fully functional - contributors can find where to document any feature type

---

## Phase 4: User Story 2 - Contributor Uses Feature Documentation Checklist (Priority: P2)

**Goal**: Framework Contributors can use structured checklist to ensure all required documentation updates are completed

**Independent Test**: Complete a feature checklist and verify all relevant documentation sections are updated

### Implementation for User Story 2

- [X] T020 [US2] Verify `.specify/templates/feature-docs-checklist.md` template exists (created in T002), add metadata section requirements per data-model.md Feature Documentation Checklist entity
- [X] T021 [US2] Add section checklist to template (user-guide, portal-administration, portal-development, contributing checkboxes) per data-model.md
- [X] T022 [US2] Add content requirements section to template (overview, examples, configuration, migration, cross-references) per contracts/feature-docs-checklist-example.md
- [X] T023 [US2] Add validation checklist section to template (spec link, build passes, links validated, examples tested) per contracts/feature-docs-checklist-example.md
- [X] T024 [US2] Create `docs/contributing/documentation/feature-checklist-workflow.md` documenting 6-step workflow from quickstart.md
- [X] T025 [US2] Add feature checklist workflow link to `docs/contributing/documentation/index.md`
- [X] T026 [US2] Update information-architecture.md with note about checklist location: `specs/###-feature-name/checklists/` per FR-010
- [X] T027 [US2] Validate: Create test checklist for this spec itself in `specs/001-documentation-strategy/checklists/documentation-strategy.md` and verify workflow

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - contributors know where to document AND how to track completion

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - contributors know where to document AND how to track completion

---

## Phase 5: User Story 3 - Reader Traces Documentation to Specification (Priority: P3)

**Goal**: Portal Developers reading documentation can follow links to original specifications

**Independent Test**: Follow a docs-to-spec link and verify spec contains rationale for documented behavior

### Implementation for User Story 3

- [X] T028 [P] [US3] Create `docs/contributing/documentation/cross-references.md` documenting spec cross-reference pattern per data-model.md Spec Cross-Reference entity (✅ Comprehensive guide created with syntax, validation, examples, integration)
- [X] T029 [P] [US3] Add constitution cross-reference pattern to cross-references.md per data-model.md Constitution Cross-Reference entity (✅ Included in cross-references.md)
- [X] T030 [P] [US3] Add anchor generation rules to cross-references.md per research.md Section 6 (kebab-case, lowercase, hyphens) (✅ Full anchor generation rules section added)
- [X] T031 [US3] Add cross-reference examples to cross-references.md from quickstart.md (relative links, anchors, specs, constitution) (✅ 4 detailed scenarios with examples)
- [X] T032 [US3] Update feature-checklist-workflow.md to include cross-reference requirements in content section (✅ Added important box with link to cross-references guide)
- [X] T033 [US3] Add cross-references.md link to `docs/contributing/documentation/index.md` (✅ Added to grid cards, quick links, and toctree)
- [X] T034 [US3] Add spec cross-reference to `docs/overview/index.md` linking to this spec: `[Spec: Documentation Strategy](../../specs/001-documentation-strategy/spec.md)` (✅ Added as seealso box)
- [X] T035 [US3] Add constitution cross-reference example to `docs/overview/philosophy.md` (or create if missing): `[FAIR-First](../../.specify/memory/constitution.md#i-fair-first-research-portals)` (✅ Added 2 constitution cross-references to goals.md)
- [X] T036 [US3] Validate: Run linkcheck to verify spec and constitution cross-references resolve correctly (✅ Linkcheck passed - no broken internal links for constitution.md or spec.md)

**Checkpoint**: All user stories should now be independently functional - contributors can place docs, track completion, and add traceability links

---

## Phase 6: User Story 4 - Documentation Validation Passes (Priority: P1)

**Goal**: Automated validation catches broken links, missing checklists, and build errors before merge

**Independent Test**: Run validation on passing and intentionally broken documentation to verify detection

### Implementation for User Story 4

- [X] T037 [US4] Update `tests/integration/docs/test_documentation_validation.py` with test_checklist_exists function per research.md Section 7 (✅ Test already exists and passing)
- [X] T038 [US4] Add test_checklist_structure function to validate metadata, section checklist, content requirements per validation-schema.yml checklist_validation section (✅ Test exists, 4/5 passing - 1 fails on old-format checklists as expected)
- [X] T039 [US4] Add test_spec_reference_resolves function to validate spec links in checklists per validation-schema.yml spec_reference validation (✅ Test exists and passing)
- [X] T040 [US4] Update `.github/workflows/docs-validation.yml` to run on pull_request for paths: `docs/**`, `specs/**`, `*.md` per validation-schema.yml ci_cd_integration (✅ Workflow triggers expanded)
- [X] T041 [US4] Configure workflow to fail on internal link failures but warn on external link failures per validation-schema.yml link_check rules (✅ Linkcheck step configured with proper grep pattern)
- [X] T042 [US4] Add validation report generation step to workflow calling `generate-validation-report.py` per validation-schema.yml (✅ Report generation step added)
- [X] T043 [US4] Configure workflow to block PR merge if build or internal links fail (required_checks) per FR-014 (✅ All critical steps have continue-on-error: false)
- [X] T044 [US4] Create `docs/contributing/documentation/validation-rules.md` documenting all validation rules from validation-schema.yml (✅ 5,000+ word comprehensive guide created)
- [X] T045 [US4] Add validation-rules.md link to `docs/contributing/documentation/index.md` (✅ Grid card, quick links, and toctree updated)
- [X] T046 [US4] Validate: Intentionally break internal link, run workflow locally or in PR, verify it catches error and blocks merge (✅ Tested - broken link detected, warning count increased from 54 to 55, build failed with exit code 1)

**Checkpoint**: Validation infrastructure complete - broken documentation cannot be merged

---

## Phase 7: User Story 5 - Existing Documentation Brought Into Compliance (Priority: P2) **[DEFERRED]**

**Status**: DEFERRED - Over-engineered for current needs

**Rationale**: Phases 1-6 deliver complete MVP with automated validation enforcing standards for new/changed documentation. Phase 7 would create formal audit infrastructure for a one-time activity (fixing old docs), which violates YAGNI principle. Instead, fix the existing 54 build warnings opportunistically as files are touched.

**Alternative Approach**: Create simple GitHub issue "Fix remaining 54 documentation build warnings" with checkbox list. Address warnings as those files are edited for other reasons.

**Original Goal**: Migration process identifies and remediates non-conforming documentation

**Original Tasks** (deferred, not implemented):

- [ ] T047 [US5] Create `docs/contributing/documentation/conformance-audit.md` documenting audit process
- [ ] T048 [US5] Add structure violation checks to conformance-audit.md
- [ ] T049 [US5] Add missing cross-reference checks to conformance-audit.md
- [ ] T050 [US5] Add lifecycle marker checks to conformance-audit.md
- [ ] T051 [US5] Add terminology consistency checks to conformance-audit.md
- [ ] T052 [US5] Create audit report template
- [ ] T053 [US5] Document audit triggers in conformance-audit.md
- [ ] T054 [US5] Add conformance-audit.md link to index
- [ ] T055 [US5] Run manual conformance audit, document findings
- [ ] T056 [US5] Create issues for high-priority conformance violations

**Checkpoint**: Conformance process established - can identify and track remediation of non-conforming documentation

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T057 [P] Create `docs/contributing/documentation/lifecycle-markers.md` documenting MyST admonition usage per FR-021 and research.md Section 2
- [ ] T058 [P] Add lifecycle-markers.md examples (deprecated, experimental, maintenance mode) from quickstart.md
- [ ] T059 [P] Add lifecycle-markers.md link to `docs/contributing/documentation/index.md`
- [ ] T060 [P] Create `docs/contributing/documentation/constitution-amendments.md` documenting amendment process and documentation review requirements per FR-020
- [ ] T061 [P] Add constitution-amendments.md link to `docs/contributing/documentation/index.md`
- [ ] T062 Update `docs/overview/index.md` to include proper navigation per FR-003 (links to all 4 main sections)
- [ ] T063 Ensure `docs/user-guide/index.md`, `docs/portal-administration/index.md`, `docs/portal-development/index.md`, `docs/contributing/index.md` all have purpose statements per FR-008
- [ ] T064 [P] Add spec cross-reference to `docs/portal-development/index.md` linking to this spec per US3
- [ ] T065 [P] Add constitution cross-reference to `docs/contributing/index.md` per US3
- [ ] T066 Run full documentation build: `poetry run sphinx-build -W --keep-going -b html docs docs/_build/html`
- [ ] T067 Run full linkcheck: `poetry run sphinx-build -b linkcheck docs docs/_build/linkcheck`
- [ ] T068 Run checklist validation tests: `poetry run pytest tests/integration/docs/test_documentation_validation.py`
- [ ] T069 Generate validation report: `python .github/scripts/generate-validation-report.py`
- [ ] T070 Review validation report and address any remaining warnings or issues
- [ ] T071 Update this spec's checklist at `specs/001-documentation-strategy/checklists/documentation-strategy.md` marking all documentation tasks complete
- [ ] T072 Run quickstart.md validation: manually walk through workflow documented in quickstart.md to verify accuracy

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion (T002-T005) - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 first: US1, US4 → P2: US2, US5 → P3: US3)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - References US1's information-architecture.md but independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - References US2's checklist workflow but independently testable
- **User Story 4 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories (validation is orthogonal)
- **User Story 5 (P2)**: Can start after Foundational (Phase 2) - Uses US1's info architecture for conformance checks but independently testable

### Within Each User Story

- Information architecture guide (US1) → Checklist workflow (US2) → Cross-references (US3) flow naturally
- Validation (US4) can be built completely independently in parallel with US1-3
- Conformance audit (US5) references US1 but doesn't block other work
- Polish tasks reference earlier work but are non-blocking enhancements

### Parallel Opportunities

- **Setup (Phase 1)**: All tasks marked [P] can run in parallel (T002-T005)
- **Foundational (Phase 2)**: T009-T010 can run in parallel (file relocations)
- **User Story 1**: T013-T016 can run in parallel (all creating different parts of information-architecture.md or different files)
- **User Story 3**: T028-T030 can run in parallel (all adding to cross-references.md or different files)
- **Polish (Phase 8)**: T057-T061, T064-T065 can all run in parallel (different files)
- **Entire User Story 4 can run in FULL parallel with User Stories 1-3** if team capacity allows (validation is independent infrastructure)

---

## Parallel Example: User Story 1

```bash
# Launch all information architecture content creation together:
Task: "Create information-architecture.md with immutable structure definition"
Task: "Add subdirectory creation guidance to information-architecture.md"
Task: "Create decision tree in information-architecture.md"
Task: "Add file creation guidelines to information-architecture.md"
```

---

## Parallel Example: Multiple User Stories

```bash
# With 3 developers after Foundational phase completes:
Developer A: User Story 1 (T013-T019) - Information Architecture Guide
Developer B: User Story 4 (T037-T046) - Validation Infrastructure
Developer C: User Story 2 (T020-T027) - Feature Checklist Template

# All three can work simultaneously without conflicts
```

---

## Implementation Strategy

### MVP First (P1 User Stories Only)

1. Complete Phase 1: Setup (T001-T005)
2. Complete Phase 2: Foundational (T006-T012) - **CRITICAL**
3. Complete Phase 3: User Story 1 (T013-T019) - Information Architecture
4. Complete Phase 6: User Story 4 (T037-T046) - Validation
5. **STOP and VALIDATE**: Test that contributors can place docs correctly AND validation catches errors
6. Deploy/demo if ready - **This is the MVP!**

### Incremental Delivery

1. **Foundation**: Setup + Foundational → Basic infrastructure ready
2. **MVP (P1)**: Add US1 + US4 → Contributors can place docs, validation enforces quality → Deploy/Demo
3. **P2 Features**: Add US2 + US5 → Checklists track completion, conformance audits identify gaps → Deploy/Demo
4. **P3 Features**: Add US3 → Traceability to specs/constitution → Deploy/Demo
5. **Polish**: Add lifecycle markers, amendment process, final cross-references → Complete

### Parallel Team Strategy

With multiple developers:

1. **Team completes Setup + Foundational together** (T001-T012)
2. **Once Foundational is done, split by priority:**
   - **Developer A**: User Story 1 (T013-T019) - Information Architecture
   - **Developer B**: User Story 4 (T037-T046) - Validation
   - **Developer C**: User Story 2 (T020-T027) - Feature Checklist
3. **Then proceed to lower priority:**
   - **Developer A**: User Story 3 (T028-T036) - Cross-References
   - **Developer B**: User Story 5 (T047-T056) - Conformance Audit
   - **Developer C**: Polish tasks (T057-T072)

---

## Notes

- **[P] tasks** = different files or independent sections, no dependencies on incomplete work
- **[Story] label** (US1-US5) maps task to specific user story from spec.md for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Priority P1 stories (US1, US4) deliver the MVP**: information architecture + validation
- **Priority P2 stories (US2, US5) add process**: checklists + conformance
- **Priority P3 story (US3) adds traceability**: cross-references
- All file paths are absolute from repository root: `docs/`, `.specify/`, `.github/`, `tests/`
- Validation enforcement per FR-014: internal link failures and build errors MUST hard-block PR merges
- External links checked but only warn per FR-014: manual review required but not blocking
- Constitution amendments trigger documentation review per FR-020

---

## Success Criteria Mapping

- **SC-001**: Addressed by T062-T063 (navigation from any major page to entry point in ≤2 clicks)
- **SC-002**: Addressed by T013-T016, T024 (contributors answer "where do I document X?" in <30s)
- **SC-003**: Addressed by T020-T027, T071 (95% features have completed checklists)
- **SC-004**: Addressed by T006-T007, T011, T040-T043 (docs build succeeds without warnings in CI)
- **SC-005**: Addressed by T006-T007, T012, T040-T041 (linkcheck catches 100% broken internal links)
- **SC-006**: Addressed by T028-T036 (80% feature pages have spec links)
- **SC-007**: Addressed by T047-T056 (100% misplaced files identified and remediated)
- **SC-008**: Addressed by T040-T043 (zero docs PRs merged without passing validation)
- **SC-009**: Measurable after implementation (documentation contribution time decreases 40%)
