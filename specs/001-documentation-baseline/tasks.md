---

description: "Task list for FairDM documentation baseline feature"

---

# Tasks: FairDM Documentation Baseline

**Input**: Design documents from `/specs/001-documentation-baseline/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Automated tests are not required for this feature. Validation is via manual walkthroughs of the documented user journeys and verification against the success criteria in spec.md.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Ensure the documentation toolchain and local environment are ready to implement the documentation baseline.

- [ ] T001 Confirm local documentation environment and Sphinx configuration using fairdm-docs for docs/conf.py
- [ ] T002 Run a baseline documentation build to capture current warnings and errors for docs/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish a clear, role-focused top-level documentation structure and navigation that all user stories depend on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T003 Review existing role-based sections and toctrees to understand current structure and gaps in docs/index.md, docs/admin-guide/index.md, docs/contributor-guide/index.md, docs/developer-guide/index.md, docs/contributing/index.md
- [ ] T004 [P] Update the main documentation entry point to prominently surface admin-guide, contributor-guide, developer-guide, and contributing sections with short role-focused descriptions in docs/index.md
- [ ] T005 [P] Ensure each role section has a clear landing page stating purpose and target audience (create or update) in docs/admin-guide/index.md, docs/contributor-guide/index.md, docs/developer-guide/index.md, docs/contributing/index.md
- [ ] T006 [P] Add an explicit reference and link to the FairDM constitution in the high-level overview section of docs/about/about.md and align messaging with .specify/memory/constitution.md

**Checkpoint**: Foundation ready — role-based sections and navigation are in place and discoverable from the main entry point.

---

## Phase 3: User Story 1 - New Developer Onboards Quickly (Priority: P1) 🎯 MVP

**Goal**: A new developer can use the documentation alone to bring up a demo portal, define a minimal Sample/Measurement model, register it, and verify it in the UI and via programmatic access.

**Independent Test**: A developer with general web development experience but no prior FairDM knowledge can complete the full Getting Started journey in one sitting, starting from the main docs entry point and ending with a working demo portal and visible Sample/Measurement model.

### Implementation for User Story 1

- [ ] T007 [US1] Refine the high-level "What is FairDM" and FAIR-first overview to highlight developer evaluation goals and link to the constitution in docs/about/about.md
- [ ] T008 [P] [US1] Ensure the developer-focused entry point describes the scope of the developer guide and links clearly from the main index in docs/developer-guide/index.md and docs/index.md
- [ ] T009 [P] [US1] Design and document a single, opinionated Getting Started flow outline (steps, prerequisites, expected outcome) in docs/developer-guide/getting_started.md
- [ ] T010 [US1] Flesh out the Getting Started flow with concrete narrative steps for running the demo portal locally (without hard-coding specific tooling beyond what quickstart.md allows) in docs/developer-guide/getting_started.md
- [ ] T011 [US1] Extend the Getting Started flow to include defining a minimal custom Sample model and a related Measurement model (conceptual description tied to existing demo configuration) in docs/developer-guide/getting_started.md
- [ ] T012 [US1] Document how to register the new Sample/Measurement models with the FairDM registry and verify that they appear in the portal UI in docs/developer-guide/getting_started.md
- [ ] T013 [US1] Add a section to the Getting Started flow showing how to confirm the new model via a programmatic access path (e.g., documented endpoint or shell snippet) in docs/developer-guide/getting_started.md
- [ ] T014 [P] [US1] Cross-link from any existing developer-facing onboarding pages (e.g., docs/developer-guide/before_you_start.md and docs/developer-guide/project_directory.md) to the single canonical Getting Started journey in docs/developer-guide/getting_started.md
- [ ] T015 [US1] Validate the full developer journey manually against the acceptance scenarios and success criterion SC-001, noting any gaps for follow-up, using docs/index.md and docs/developer-guide/getting_started.md

**Checkpoint**: User Story 1 is complete when a new developer can follow the documented journey end-to-end without external guidance and reach a working demo portal with a visible Sample/Measurement model and programmatic access.

---

## Phase 4: User Story 2 - Portal Administrator Understands Their Responsibilities (Priority: P2)

**Goal**: A portal administrator can, using only the admin-focused docs, understand their role, key concepts, and perform core administrative tasks in a demo portal.

**Independent Test**: An administrator can navigate from the main docs entry point to the admin-guide, understand core entities and responsibilities, and carry out at least three core admin tasks (including adjusting dataset access) using only the documentation.

### Implementation for User Story 2

- [ ] T016 [US2] Update the admin-guide landing page to describe the portal administrator role, responsibilities, and relationship to core entities (Projects, Datasets, Samples, Measurements, Contributors) in docs/admin-guide/index.md
- [ ] T017 [P] [US2] Add or refine a concise overview of core entities suitable for admins, reusing or cross-linking to conceptual material from docs/developer-guide/core_data_model.md in docs/admin-guide/index.md
- [ ] T018 [P] [US2] Create or update a focused guide for managing users, roles, and permissions, including at least one dataset-level access control example, in docs/admin-guide/managing_users_and_permissions.md
- [ ] T019 [US2] Add an end-to-end walkthrough for adjusting access to a dataset in a demo portal, linked from the admin-guide landing page, in docs/admin-guide/adjusting_dataset_access.md
- [ ] T020 [P] [US2] Ensure clear navigation from the main docs entry point and from the high-level roles description to the admin-guide landing page in docs/index.md and docs/about/roles.md
- [ ] T021 [US2] Manually validate the admin journey against the acceptance scenarios and success criterion SC-002 using docs/admin-guide/index.md, docs/admin-guide/managing_users_and_permissions.md, and docs/admin-guide/adjusting_dataset_access.md

**Checkpoint**: User Story 2 is complete when an administrator can understand their responsibilities and perform documented admin tasks in a demo portal using only the admin-guide.

---

## Phase 5: User Story 3 - Contributor Learns How to Contribute Data (Priority: P3)

**Goal**: A contributor can, using only the contributor-guide, understand how to access a FairDM portal, locate relevant datasets, and add or edit data in a FAIR-aligned way.

**Independent Test**: A contributor with portal access can locate an existing dataset, understand key fields, and add or edit entries while following documented metadata practices, without needing developer assistance.

### Implementation for User Story 3

- [ ] T022 [US3] Update the contributor-guide landing page to clearly describe the contributor role, high-level workflow, and connection to FAIR metadata practices in docs/contributor-guide/index.md
- [ ] T023 [P] [US3] Create or refine guidance on understanding core dataset and record fields from a contributor perspective, building on existing explanations in docs/contributor-guide/core_data_model.md
- [ ] T024 [P] [US3] Extend or rewrite the contributor Getting Started page to walk through locating an existing dataset, reviewing field meanings, and safely editing an existing record in docs/contributor-guide/getting_started.md
- [ ] T025 [US3] Add a step-by-step guide for adding a new Sample and associated Measurements in the UI, including highlighting required vs optional metadata fields for one concrete workflow, in docs/contributor-guide/getting_started.md
- [ ] T026 [P] [US3] Introduce a short metadata best-practices page or section (e.g., required vs optional, controlled vocabularies, provenance hints) linked from the contributor-guide landing page in docs/contributor-guide/metadata_practices.md
- [ ] T027 [US3] Manually validate the contributor journey against the acceptance scenarios and success criterion SC-003 using docs/contributor-guide/index.md and docs/contributor-guide/getting_started.md

**Checkpoint**: User Story 3 is complete when contributors can reliably add and edit data in a demo portal while following documented metadata guidelines.

---

## Phase 6: User Story 4 - Framework Contributor Knows How to Contribute Safely (Priority: P3)

**Goal**: A framework contributor can, using only the contributing documentation, set up a local FairDM development environment, run the core quality gates (tests, typing, linting, docs build), and understand how to propose changes in a way that aligns with the constitution.

**Independent Test**: A developer with general Python and Django experience, but no prior involvement with FairDM, can follow the contributing docs to clone the repository, install dependencies, run the tests and documentation build, and identify the basic contribution workflow without external guidance.

### Implementation for User Story 4

- [ ] T028 [US4] Update the framework contributor landing information to clearly describe the framework contributor role, expectations, and how it differs from portal contributors in docs/contributing/index.md
- [ ] T029 [P] [US4] Ensure docs/contributing/before_you_start.md and docs/contributing/django_dev.md together provide a step-by-step guide for setting up a FairDM development environment (clone repository, install dependencies, run tests and docs build)
- [ ] T030 [P] [US4] Document the core quality gates (tests, type checking, linting, documentation build) and how to run them locally, consolidating or extending guidance in docs/contributing/django_dev.md and docs/contributing/frontend_dev.md
- [ ] T031 [P] [US4] Update docs/contributing/contribution_framework.md to explain the contribution workflow (issues, discussions, pull requests) and explicitly reference the FairDM constitution for design decisions
- [ ] T032 [US4] Manually validate that a new framework contributor can follow the contributing docs (index, before_you_start.md, django_dev.md, contribution_framework.md) to set up a development environment, run the core quality gates, and understand how to propose a change without external guidance

**Checkpoint**: User Story 4 is complete when a new framework contributor can confidently set up a development environment, run the agreed quality gates, and understand the basic contribution workflow using only the contributing documentation.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Tighten cross-links, edge-case handling, and high-level guidance that spans multiple user stories.

- [ ] T033 [P] Add contextual navigation and "You are here" framing on deep documentation pages most likely to be landed on from search (e.g., docs/more/* and role-specific subpages) to address edge-case navigation
- [ ] T034 [P] Add or update a short "Reporting documentation issues" section that explains how users can report discrepancies or gaps, linked from docs/index.md and docs/about/reviewing_content.md
- [ ] T035 Consolidate and verify cross-links between role guides and core concept pages (e.g., Projects, Datasets, Samples, Measurements) across docs/about/, docs/contributor-guide/, docs/developer-guide/, and docs/admin-guide/
- [ ] T036 Run a final documentation build and skim for obvious structural issues, broken navigation, and inconsistencies against FR-001–FR-007, FR-006’s tooling-agnostic requirement, and SC-001–SC-004 for docs/
- [ ] T037 [P] Update or add a brief "What changed" or release-notes style summary for this documentation baseline feature, grouped under a section keyed to this baseline or the relevant FairDM release, so existing users can discover updated workflows, in docs/about/reviewing_content.md or a new docs/more/whats_new.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately.
- **Foundational (Phase 2)**: Depends on completion of Phase 1 — blocks all user story phases.
- **User Story Phases (3–6)**: Each depends on completion of Phase 2, but US2, US3, and US4 do not depend on US1 and can be developed in parallel once foundational work is done.
- **Polish (Phase 7)**: Depends on completion of all user stories targeted for this feature (at minimum US1 as the MVP, and optionally US2, US3, and US4).

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2 and serves as the MVP; other stories do not strictly depend on it but benefit from its established Getting Started patterns.
- **User Story 2 (P2)**: Can start after Phase 2; may cross-link to conceptual material created or refined during US1 but remains independently testable using admin-focused pages.
- **User Story 3 (P3)**: Can start after Phase 2; may cross-link to the same conceptual material but remains independently testable using contributor-focused pages.
- **User Story 4 (P3)**: Can start after Phase 2; may cross-link to conceptual and governance material but remains independently testable using the contributing documentation.

### Within Each User Story

- For each story, complete landing-page clarity tasks before deep how-to guides.
- Within deep guides (e.g., getting_started pages), structure and outline should be agreed before filling in detailed steps.
- Cross-linking and final narrative polish should happen after core content is in place.

### Parallel Opportunities

- After Phase 1, foundational tasks T004, T005, and T006 can be executed in parallel since they affect different files.
- Once foundational navigation is stable, User Story 1, 2, and 3 implementation tasks can be split across team members:
  - US1 tasks in docs/about/about.md and docs/developer-guide/*
  - US2 tasks in docs/admin-guide/* and shared index/roles pages
  - US3 tasks in docs/contributor-guide/* and related metadata guidance pages
- Within US1, T008, T009, and T014 can be worked on in parallel as they affect different developer-guide files.
- Within US2, T017, T018, and T020 can proceed in parallel since they target distinct admin and roles pages.
- Within US3, T023, T024, and T026 can proceed in parallel as they focus on different contributor-guide files.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational (ensure clear role-based navigation and constitution reference).
3. Complete Phase 3: User Story 1 (developer Getting Started journey).
4. **STOP and VALIDATE**: Have a new or unfamiliar developer follow the Getting Started flow and confirm SC-001 can plausibly be met.
5. If successful, publish or share the updated docs as the Documentation Baseline MVP.

### Incremental Delivery

1. Deliver the MVP by completing Phases 1–3.
2. Add User Story 2 (Phase 4) to strengthen admin-focused guidance; validate against SC-002.
3. Add User Story 3 (Phase 5) to provide contributor-focused guidance; validate against SC-003.
4. Add User Story 4 (Phase 6) to provide framework-contributor-focused guidance.
5. Apply Phase 7 (Polish) to improve navigation, edge cases, and communication of changes.

### Parallel Team Strategy

With multiple contributors:

- One person can focus on foundational navigation and constitution linkage (Phases 1–2).
- Another can implement US1 (developer Getting Started) in Phase 3.
- Additional contributors can handle US2 and US3 (Phases 4–5) and US4 (Phase 6) in parallel once foundational structure is stable.
- A final pass (Phase 7) can be owned by a maintainer to unify tone, ensure cross-links are consistent, and verify alignment with the FairDM constitution and spec.md.
