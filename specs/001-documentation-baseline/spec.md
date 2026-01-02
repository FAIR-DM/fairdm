# Feature Specification: FairDM Documentation Baseline

**Feature Branch**: `001-documentation-baseline`  
**Created**: 2025-12-30  
**Status**: Draft  
**Input**: User description: "Establish a coherent documentation baseline aligned with the constitution, covering portal admins, contributors, and developers. Clarify the high-level vision, FAIR-first philosophy, and core architecture. Ensure the four major doc sections (admin-guide, contributor-guide, developer-guide, contributing) are discoverable, up to date, and cross-linked. Provide a minimal but complete Getting Started flow for spinning up the demo portal, creating a first custom Sample/Measurement model, and registering it so that it is visible in the UI and via the API."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - New Developer Onboards Quickly (Priority: P1)

A new developer wants to evaluate FairDM and set up a small prototype portal for their research group. They should be able to read a high-level overview, follow a single "Getting Started" path to run a demo portal locally, define one simple Sample/Measurement model, register it, and see it in the portal UI and via a programmatic endpoint.

**Why this priority**: This journey is the primary entry point for adoption: if new developers cannot quickly understand and trial FairDM, they are unlikely to build portals on top of it.

**Independent Test**: A developer who is comfortable with Python object-oriented programming and has basic familiarity with Django (ideally having completed the official Django tutorials), but no prior FairDM experience, can, using only the documentation, complete the prototype journey end-to-end in one sitting without external guidance.

**Acceptance Scenarios**:

1. **Given** a new developer who knows where the documentation is, **When** they follow the Getting Started guide, **Then** they successfully start a local demo portal and access it through a browser.
2. **Given** the same developer, **When** they follow the documented steps to define and register a minimal Sample/Measurement model, **Then** the new model appears in the portal UI and is retrievable via a documented programmatic endpoint.

---

### User Story 2 - Portal Administrator Understands Their Responsibilities (Priority: P2)

A portal administrator (often a data manager with limited development experience) wants to understand what FairDM can do, how the core data model works, and what tasks they are responsible for (e.g., managing users, permissions, and core metadata) without reading developer-focused material.

**Why this priority**: Administrators shape day-to-day data quality, FAIR compliance, and user trust; they need clear, concise guidance tailored to their role.

**Independent Test**: An administrator can navigate the admin-facing documentation section, understand the core concepts and responsibilities, and perform key administrative tasks in a demo portal using only the documentation.

**Acceptance Scenarios**:

1. **Given** a portal administrator, **When** they open the admin-guide section from the main documentation entry point, **Then** they find an overview that explains their role, core entities (Projects, Datasets, Samples, Measurements, Contributors), and links to specific how-to guides.
2. **Given** this admin-guide, **When** they follow the steps for managing users and permissions, **Then** they can successfully adjust access to a dataset in a demo portal as described in the docs.

---

### User Story 3 - Contributor Learns How to Contribute Data (Priority: P3)

A data contributor (e.g., researcher) wants to know how to log in, understand the basic structure of a FairDM portal, and add or edit data in a way that aligns with FAIR principles without needing to understand implementation details.

**Why this priority**: Contributors are the primary source of data; clear guidance for them directly improves data quality and FAIR compliance.

**Independent Test**: A contributor can, using only the contributor-guide, understand how to access a FairDM-powered portal, locate relevant projects/datasets, and add or edit entries while following recommended metadata practices.

**Acceptance Scenarios**:

1. **Given** a contributor with access to a demo portal, **When** they follow the contributor-guide, **Then** they can successfully locate an existing dataset and understand the meaning of key fields before editing.
2. **Given** the same contributor, **When** they follow the documented steps for adding a new Sample and associated Measurements, **Then** they can complete the process using the UI and understand which metadata is required for FAIR compliance.

---

### User Story 4 - Framework Contributor Knows How to Contribute Safely (Priority: P3)

A developer who wants to contribute to the FairDM framework itself (code, documentation, or examples) needs clear, role-appropriate guidance on how to set up a development environment, follow the project’s quality gates, and submit changes in a way that aligns with the constitution.

**Why this priority**: Framework contributors extend and maintain the core that other portals rely on. Clear contributor-facing documentation reduces friction for new contributors while protecting project quality and constitutional alignment.

**Independent Test**: A developer with general Python and Django experience, but no prior involvement with FairDM, can locate the contributing documentation, set up a working development environment, run the test suite and docs build, and identify how to propose a change (e.g., via pull request) without external guidance.

**Acceptance Scenarios**:

1. **Given** a developer interested in contributing to FairDM, **When** they navigate from the main documentation entry point to the contributing section, **Then** they find an overview that explains contributor roles, expectations (tests, typing, documentation), and links to setup instructions.
2. **Given** that same developer, **When** they follow the contributing guide, **Then** they can set up a local development environment, run the relevant test and documentation commands, and understand the basic workflow for submitting a contribution (issues, discussions, or pull requests) in a way that references the FairDM constitution.

---

### User Story 5 - Reader Understands FairDM Overview and Contributors (Priority: P2)

A new reader (often a prospective portal administrator, developer, or institutional stakeholder) wants to understand, at a glance, what FairDM is for, how it relates to FAIR principles, what its core features and data model look like, and why contributors are explicitly modeled and recorded.

**Why this priority**: The Overview pages are the first contact point for many evaluators and non-technical stakeholders. If they cannot quickly understand FairDM's purpose, scope, and treatment of contributors, they may not trust or adopt the framework.

**Independent Test**: A new reader with no prior FairDM knowledge, but general familiarity with research data management, can read the Overview and related core concept pages and then accurately explain (in their own words) FairDM's purpose, its core entities (Projects, Datasets, Samples, Measurements, Contributors, Organizations), and why contributor information is recorded and surfaced in portals.

**Acceptance Scenarios**:

1. **Given** a new reader landing on the main documentation entry point, **When** they follow links to the Overview section, **Then** they can find clear explanations of FairDM's introduction, background, goals, core features, high-level core data model, and contributor tracking without needing to read developer- or admin-focused guides, and can describe what a contributor is in FairDM portals, what counts as a contribution (data, metadata, curation, code, documentation, etc.), and why contributors are recorded (attribution, provenance, FAIR/reproducibility).
2. **Given** a reader who has read the Overview and Contributors sections, **When** they later browse a FairDM portal (demo or production), **Then** they can recognise where contributor information appears in the UI (e.g., on project, dataset, sample, or measurement pages) and understand its purpose.

---

### Edge Cases

- What happens when a user lands directly on a deep documentation page (via search) without context? The documentation MUST provide navigation and framing so they can easily discover where they are and how to get back to the main structure.
- How does the system handle documentation updates that significantly change recommended workflows? Change logs, “What’s new” sections, or upgrade notes SHOULD guide existing users to updated practices.
- How are discrepancies between actual portal behaviour and documentation handled? There MUST be an obvious way for users to report documentation issues or gaps.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The documentation MUST present a clear high-level overview of FairDM’s purpose, FAIR-first philosophy, and core architecture, including an explicit link to the FairDM constitution for deeper governance and principles.
- **FR-002**: The documentation MUST have clearly separated and discoverable sections for portal administrators, contributors, developers, and FairDM framework contributors.
- **FR-003**: The main documentation entry point MUST provide obvious navigation to the four key sections: admin-guide, contributor-guide, developer-guide, and contributing.
- **FR-004**: There MUST be a single, linear Getting Started guide for developers that describes how to bring up a demo portal, define a simple Sample/Measurement model, register it, and confirm it appears in both the UI and via a documented programmatic access path.
- **FR-005**: The documentation MUST describe, in non-implementation terms, the responsibilities and typical workflows of portal administrators and contributors, emphasising FAIR-compliant metadata practices.
- **FR-006**: The documentation MUST avoid prescribing specific tooling commands or environment details beyond what is necessary to describe user journeys; concrete commands and stack details SHOULD be deferred to implementation-oriented quickstarts or developer appendices.
- **FR-007**: Documentation pages MUST be internally cross-linked so that users can move between role-specific guides, concept explanations (e.g., Projects, Datasets, Samples, Measurements), and the Getting Started flow without dead ends.

### Non-Functional Requirements

- **NFR-001**: Documentation MUST be reasonably accessible and usable on common desktop and mobile devices, with navigation elements and primary content remaining readable without requiring horizontal scrolling at typical viewport widths.
- **NFR-002**: Documentation navigation MUST remain responsive; key landing pages (main index, role-specific indexes, and primary getting-started guides) SHOULD render and become interactive within a few seconds on a typical developer laptop when built locally.
- **NFR-003**: Documentation MUST be structured to allow future internationalisation (e.g., user-facing strings and examples SHOULD avoid hard-coded locale assumptions where possible, and content SHOULD avoid mixing multiple languages in a single page except where explicitly illustrative).
- **NFR-004**: Documentation SHOULD follow basic accessibility best practices consistent with the Bootstrap-based UI (e.g., meaningful headings, descriptive link text, and avoidance of color-only distinctions in diagrams or screenshots where feasible).

### Key Entities *(include if feature involves data)*

- **Documentation Section**: Represents a logical grouping of pages targeted at a specific audience (e.g., portal administrators, contributors, developers, framework contributors). Key attributes include purpose, target audience, and primary entry points.
- **User Role**: Represents the type of user consuming the documentation (developer, portal administrator, contributor, framework contributor). Key attributes include primary goals, typical tasks, and required level of technical knowledge.

### Assumptions & Dependencies

- It is assumed that a basic, runnable FairDM demo portal environment exists that can be started by following high-level instructions (e.g., using a standard local or containerised setup), without prescribing specific tools in this specification.
- It is assumed that the documentation is delivered through an existing documentation system capable of organising pages into sections, providing navigation, and supporting cross-links between topics.
- The feature depends on at least one maintained reference portal configuration that reflects the documented workflows closely enough for users to follow them successfully.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users landing directly on any major documentation page (defined as the main documentation index, role-specific landing pages, and primary getting-started guides in each section) can reach the main documentation entry point or an appropriate role-specific landing page in no more than two clicks.

### Validation Approach

Success criteria are validated through manual walkthroughs documented in the tasks.md validation tasks (T015, T021, T027, T032, T041). Each validation task specifies the user story acceptance scenarios to verify.

## Terminology *(reference)*

| Term | Definition | Canonical Location |
|------|------------|--------------------|
| **Overview** | High-level conceptual documentation section explaining FairDM's purpose, FAIR-first philosophy, core architecture, and contributor model | `docs/overview/` |
| **Contributor Guide** | Documentation section for portal contributors (people who add/edit data in portals) | `docs/contributor-guide/` |
| **User Guide** | (Obsolete) Former name for Contributor Guide | N/A |
| **About** | (Obsolete) Former name for Overview section | N/A |
| **Portal Contributor** | Person who adds or edits research data, samples, measurements, and metadata in a FairDM portal | See Contributor Guide |
| **Framework Contributor** | Person who contributes to the FairDM framework codebase itself (code, docs, tests) | See Contributing Guide |
| **Admin Guide** | Documentation section for portal administrators who manage users, permissions, and metadata quality | `docs/admin-guide/` |
| **Developer Guide** | Documentation section for developers building new FairDM portals | `docs/developer-guide/` |
| **Contributing Guide** | Documentation section for framework contributors | `docs/contributing/` |

## Clarifications

### Session 2025-12-30

- Q: What is the baseline developer profile for the Getting Started journey and SC-001? → A: Developers comfortable with Python OOP and basic Django, ideally having completed the official Django tutorials.
- Q: How should the duplicated SC-001 measurable outcomes be handled? → A: Consolidate into a single SC-001 that uses the clarified developer profile and removes overlapping wording.
- Q: Should framework contributors be covered as an explicit audience in this specification? → A: Yes, add a dedicated user story for framework contributors aligned with the contributing documentation.
