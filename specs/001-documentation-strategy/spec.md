# Feature Specification: FairDM Documentation Strategy

**Feature Branch**: `001-documentation-strategy`
**Created**: 2025-12-30 (merged with 003-docs-infrastructure on 2026-01-07)
**Completed**: 2026-01-07
**Status**: Complete (MVP Delivered - Phase 7 Deferred)
**Input**: This specification merges two related features:

1. "Establish a coherent documentation baseline aligned with the constitution, covering portal admins, contributors, and developers. Clarify the high-level vision, FAIR-first philosophy, and core architecture. Ensure the four major doc sections (portal-administration, user-guide, portal-development, contributing) are discoverable, up to date, and cross-linked. Provide a minimal but complete Getting Started flow for spinning up the demo portal, creating a first custom Sample/Measurement model, and registering it so that it is visible in the UI and via the API."
2. "Create a feature spec defining how documentation is authored, validated, and kept in sync with the constitution and features. The spec should define the Sphinx information architecture: where new docs live (user guides vs dev docs vs governance docs), where governance materials live (constitution + references) and how they are cross-linked, the 'feature docs checklist' that lists what docs must be updated when a feature ships, how specs are referenced from docs so readers can trace behavior back to a spec, what 'docs are valid' means including build steps and link checks and failure conditions and minimum expectations, and any migration or conformance work needed to bring existing docs into the conventions."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Contributor Finds Where to Add Documentation (Priority: P1)

A framework contributor implementing a new feature needs to know exactly where to add documentation for different aspects of the feature (developer setup, admin configuration, portal user usage).

**Why this priority**: Without clear guidance on documentation location, contributors will skip documentation or place it incorrectly, leading to fragmented and undiscoverable docs. This is the foundation for all other documentation requirements.

**Independent Test**: Can be fully tested by asking a contributor "where do I document X?" and they can answer correctly using the documented information architecture. Delivers value by making documentation contribution predictable and consistent.

**Acceptance Scenarios**:

1. **Given** a contributor is adding a new admin feature, **When** they consult the documentation guidelines, **Then** they can determine it belongs in `docs/portal-administration/` and find the appropriate subdirectory or file to update
2. **Given** a contributor is documenting a new model configuration option, **When** they reference the information architecture, **Then** they know to add it to `docs/portal-development/model_configuration.md` or related file
3. **Given** a contributor is adding a governance principle, **When** they consult the guidelines, **Then** they know the constitution lives at `.specify/memory/constitution.md` and understand the amendment process

---

### User Story 2 - Contributor Uses Feature Documentation Checklist (Priority: P2)

A framework contributor completing a feature uses a structured checklist to ensure all required documentation updates are completed before the feature can be considered done.

**Why this priority**: Systematic documentation coverage prevents gaps and ensures FAIR principles and constitution requirements are met. This operationalizes P1's information architecture into a repeatable process.

**Independent Test**: Can be tested by having a contributor complete a feature checklist and verifying all relevant documentation sections are updated. Delivers value by making documentation completeness explicit and verifiable.

**Acceptance Scenarios**:

1. **Given** a contributor has implemented a new core model, **When** they consult the feature documentation checklist, **Then** they see explicit items for updating developer guide (model definition), User Guide (how to use), and admin guide (permissions/management)
2. **Given** a feature adds new configuration options, **When** checking the documentation checklist, **Then** the contributor is prompted to update the configuration reference and provide examples
3. **Given** a feature changes existing behavior, **When** using the checklist, **Then** the contributor is reminded to update migration guides and mark any breaking changes

---

### User Story 3 - Reader Traces Documentation to Specification (Priority: P3)

A portal developer reading documentation can follow links to the original feature specification to understand the rationale, full requirements, and design decisions behind a documented feature.

**Why this priority**: Traceability improves documentation quality and helps developers understand "why" not just "how". This supports long-term maintainability and governance compliance tracking.

**Independent Test**: Can be tested by following a docs-to-spec link and verifying the spec contains the rationale for the documented behavior. Delivers value by making design decisions transparent and auditable.

**Acceptance Scenarios**:

1. **Given** a reader is viewing documentation about the registration API, **When** they encounter a link to the specification, **Then** they can navigate to the corresponding spec file in `specs/###-feature-name/`
2. **Given** a spec introduces a new feature, **When** documentation is written for it, **Then** the documentation includes a reference back to the spec with appropriate context
3. **Given** a constitution principle is referenced in documentation, **When** the reader clicks the link, **Then** they are taken to the specific section in `.specify/memory/constitution.md`

---

### User Story 4 - Documentation Validation Passes (Priority: P1)

An automated documentation validation process checks that documentation builds successfully, links are valid, required sections exist, and constitution principles are followed.

**Why this priority**: Broken documentation is almost as bad as missing documentation. Automated validation catches issues before they reach users and enforces quality standards.

**Independent Test**: Can be tested by running the validation suite on both passing and intentionally broken documentation. Delivers value by making documentation quality measurable and enforceable.

**Acceptance Scenarios**:

1. **Given** documentation contains broken internal links, **When** validation runs, **Then** the build fails with specific error messages listing each broken link
2. **Given** a new feature is merged without updating required documentation sections, **When** validation checks run, **Then** the missing documentation is flagged in the feature docs checklist validation
3. **Given** documentation builds successfully with all links valid, **When** validation completes, **Then** the build passes and generates a validation report confirming compliance
4. **Given** documentation formatting violates Sphinx or MyST standards, **When** the build runs, **Then** warnings are surfaced and treated as errors in CI

---

### User Story 5 - Existing Documentation Brought Into Compliance (Priority: P2)

A migration process identifies and remediates non-conforming documentation, bringing existing docs into alignment with the new information architecture and quality standards.

**Why this priority**: Legacy documentation needs to be updated to match new conventions. This is lower priority than establishing the standards but necessary for long-term consistency.

**Independent Test**: Can be tested by running a conformance audit that identifies specific non-conforming files and tracking their remediation. Delivers value by ensuring all documentation follows the same standards.

**Acceptance Scenarios**:

1. **Given** existing documentation lacks spec cross-references, **When** a conformance audit runs, **Then** it produces a list of files needing spec links with guidance on how to add them
2. **Given** documentation files are misplaced in the directory structure, **When** migration tooling runs, **Then** it suggests or executes moves to align with the information architecture
3. **Given** documentation has inconsistent heading styles or formatting, **When** conformance checks run, **Then** violations are flagged with suggested fixes

---

### Edge Cases

- What happens when a user lands directly on a deep documentation page (via search) without context? The documentation MUST provide navigation and framing so they can easily discover where they are and how to get back to the main structure.
- How does the system handle documentation updates that significantly change recommended workflows? Change logs, "What's new" sections, or upgrade notes SHOULD guide existing users to updated practices.
- How are discrepancies between actual portal behaviour and documentation handled? There MUST be an obvious way for users to report documentation issues or gaps.
- What happens when a feature spans multiple documentation sections (e.g., developer + admin + contributor)? [RESOLVED: Feature documentation checklist (FR-011) prompts authors to update all relevant sections; spec authors decide which sections to update based on information architecture guidance]
- How do we handle deprecated features that still need documentation? [RESOLVED: Use standard MyST `:::{{deprecated}}` admonition per FR-021; include version deprecated and migration path]
- What if a feature is experimental and documentation should be marked as such? [RESOLVED: Use standard MyST `:::{{warning}} Experimental` admonition per FR-021; clearly communicate stability expectations]
- How do we maintain versioned documentation for different FairDM releases? [DEFERRED: Multi-version hosting explicitly out of scope for this feature; will be addressed if/when FairDM reaches stable 1.0 release with backward compatibility requirements]
- What happens when specs are updated after initial documentation is written? [RESOLVED: Spec authors are responsible for updating related documentation when specs change; normal PR review process ensures alignment; this spec defines WHERE to place documentation]
- How do we handle external links that become stale over time? [RESOLVED: External links checked but treated as warnings requiring manual review, not hard failures]
- What happens when the constitution is amended and documentation needs to be updated to reflect new principles or governance changes? [RESOLVED: Constitution amendment owner triggers documentation review and ensures alignment before amendment is considered complete per FR-020]

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The documentation MUST present a clear high-level overview of FairDM's purpose, FAIR-first philosophy, and core architecture, including an explicit link to the FairDM constitution for deeper governance and principles.
- **FR-002**: The documentation MUST have clearly separated and discoverable sections for portal administrators, Portal Users, portal developers, and Framework Contributors.
- **FR-003**: The main documentation entry point MUST provide obvious navigation to the four key sections: portal-administration, user-guide, portal-development, and contributing.
- **FR-004**: There MUST be a single, linear Getting Started guide for Portal Developers that describes how to bring up a demo portal, define a simple Sample/Measurement model, register it, and confirm it appears in both the UI and via a documented programmatic access path.
- **FR-005**: The documentation MUST describe, in non-implementation terms, the responsibilities and typical workflows of portal administrators and Portal Users, emphasising FAIR-compliant metadata practices.
- **FR-006**: The documentation MUST avoid prescribing specific tooling commands or environment details beyond what is necessary to describe user journeys; concrete commands and stack details SHOULD be deferred to implementation-oriented quickstarts or developer appendices.
- **FR-007**: Documentation pages MUST be internally cross-linked so that users can move between role-specific guides, concept explanations (e.g., Projects, Datasets, Samples, Measurements), and the Getting Started flow without dead ends.
- **FR-008**: Documentation MUST be organized into four primary sections: portal-development (Portal Developers), portal-administration (Portal Administrators), user-guide (Portal Users), and contributing (Framework Contributors), each with a clear index and purpose statement; this top-level structure is immutable and future specs MUST be able to rely on these section names and locations without concern for structural changes
- **FR-008a**: Within each primary documentation section, subdirectories MAY be added as needed to organize content; the information architecture guide MUST provide clear guidance on when to create new subdirectories vs adding to existing files
- **FR-009**: Governance materials (constitution, principles, governance process) MUST reside in `.specify/memory/` and be cross-referenced from documentation using stable links; this location is immutable
- **FR-010**: Feature specifications MUST reside in `specs/###-feature-name/` directories with spec.md, plan.md, tasks.md, and checklists/ subdirectory; this location is immutable
- **FR-011**: Documentation MUST include a feature documentation checklist template at `.specify/templates/feature-docs-checklist.md` that lists all documentation sections requiring updates when features change
- **FR-012**: Documentation pages MUST be able to reference specifications using a consistent linking pattern (e.g., `[spec](../../specs/003-docs-infrastructure/spec.md)` or custom MyST role)
- **FR-013**: Documentation MUST reference constitution sections using stable anchor links (e.g., `[Constitution: FAIR-First](.specify/memory/constitution.md#i-fair-first-research-portals)`)
- **FR-014**: Documentation validation MUST include Sphinx build checks (errors and warnings treated as failures), internal link checking (hard failure), external link checking (warning only, requires manual review), and MyST syntax validation; internal link failures and build errors MUST hard-block PR merges with no bypass mechanism
- **FR-015**: Documentation validation MUST verify that feature documentation checklists exist for each merged feature and are marked complete; missing or incomplete checklists MUST prevent PR merge
- **FR-016**: Documentation MUST define minimum expectations including: no broken links, all code examples syntactically valid, all images have alt text, all sections have proper heading hierarchy
- **FR-017**: A documentation conformance audit MUST identify existing documentation that does not meet the information architecture or quality standards
- **FR-018**: Feature documentation checklist MUST be integrated into the Speckit workflow (triggered after tasks are complete or as part of `/speckit.finalize`)
- **FR-019**: Documentation MUST include guidance on when to create new files vs update existing pages; new files SHOULD be created when: (a) content represents a standalone concept requiring dedicated treatment, OR (b) content describes a separate user journey or workflow, OR (c) adding content to an existing page would exceed approximately 500 words of new material (loose guideline, not strict threshold); the information architecture guide MUST provide examples of each scenario
- **FR-020**: When the constitution is amended, the person proposing or approving the amendment MUST trigger a documentation review to identify affected documentation sections and either update them directly or create tracked issues for section owners to address; constitution amendments MUST NOT be considered complete until documentation alignment is verified
- **FR-021**: Documentation MUST use standard MyST admonitions to mark feature lifecycle status: `:::{{deprecated}}` for deprecated features (with version deprecated and alternative if applicable), `:::{{warning}} Experimental` for experimental/unstable features, and `:::{{note}}` for features in maintenance mode; the information architecture guide MUST provide examples and conventions for each lifecycle status

### Non-Functional Requirements

- **NFR-001**: Documentation MUST be reasonably accessible and usable on common desktop and mobile devices, with navigation elements and primary content remaining readable without requiring horizontal scrolling at typical viewport widths.
- **NFR-002**: Documentation navigation MUST remain responsive; key landing pages (main index, role-specific indexes, and primary getting-started guides) SHOULD render and become interactive within a few seconds on a typical developer laptop when built locally.
- **NFR-003**: Documentation MUST be structured to allow future internationalisation (e.g., user-facing strings and examples SHOULD avoid hard-coded locale assumptions where possible, and content SHOULD avoid mixing multiple languages in a single page except where explicitly illustrative).
- **NFR-004**: Documentation SHOULD follow basic accessibility best practices consistent with the Bootstrap-based UI (e.g., meaningful headings, descriptive link text, and avoidance of color-only distinctions in diagrams or screenshots where feasible).

### Key Entities *(include if feature involves data)*

- **Documentation Section**: Represents a logical grouping of pages targeted at a specific audience (e.g., portal administrators, contributors, developers, framework contributors). Key attributes include purpose, target audience, and primary entry points.
- **User Role**: Represents the type of user consuming the documentation (developer, portal administrator, contributor, framework contributor). Key attributes include primary goals, typical tasks, and required level of technical knowledge.
- **Information Architecture**: Hierarchical structure defining where documentation lives (sections, subsections, files) and the purpose of each area
- **Feature Documentation Checklist**: Template listing documentation sections to update for different feature types (new models, new UI components, configuration changes, etc.)
- **Spec Cross-Reference**: Link from documentation to specification files with context about what aspect of the spec the docs cover
- **Constitution Cross-Reference**: Link from documentation to specific constitutional principles with explanation of how feature aligns
- **Validation Report**: Output from documentation validation including build status, link check results, checklist completeness, and quality metrics
- **Conformance Audit**: Analysis of existing documentation identifying non-conforming files with specific issues and remediation steps

### Assumptions & Dependencies

- It is assumed that a basic, runnable FairDM demo portal environment exists that can be started by following high-level instructions (e.g., using a standard local or containerised setup), without prescribing specific tools in this specification.
- It is assumed that the documentation is delivered through an existing documentation system capable of organising pages into sections, providing navigation, and supporting cross-links between topics.
- The feature depends on at least one maintained reference portal configuration that reflects the documented workflows closely enough for users to follow them successfully.
- **Assumption 1**: FairDM will continue using Sphinx with MyST (Markdown) parser for documentation; if this changes, the entire documentation infrastructure will need revision
- **Assumption 2**: Feature specifications will continue to live in the `specs/` directory using the Speckit format; information architecture depends on this structure
- **Assumption 3**: The constitution will remain the single source of truth for governance and will continue to reside in `.specify/memory/constitution.md`
- **Assumption 4**: CI/CD infrastructure exists or will be implemented to run documentation validation automatically on pull requests
- **Assumption 5**: Framework Contributors have basic familiarity with Markdown and can learn MyST syntax; no specialized documentation tooling expertise is required
- **Assumption 6**: Documentation versioning will follow the FairDM release versioning scheme; multi-version documentation hosting will be addressed in a future feature if needed
- **Assumption 7**: External link checking will use a reasonable grace period (e.g., warn but don't fail on temporary outages) to avoid false positives in CI
- **Assumption 8**: Spec authors are responsible for updating documentation related to their specs; this documentation strategy provides the information architecture (WHERE to place docs), and the normal PR review process ensures documentation quality and alignment

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users landing directly on any major documentation page (defined as the main documentation index, role-specific landing pages, and primary getting-started guides in each section) can reach the main documentation entry point or an appropriate role-specific landing page in no more than two clicks.
- **SC-002**: Framework Contributors can answer "where do I document X?" in under 30 seconds by consulting the information architecture guide (measured by observing 5 representative Framework Contributors with varying experience levels completing common documentation placement tasks)
- **SC-003**: 95% of new features include completed feature documentation checklists before being marked done
- **SC-004**: Documentation builds succeed without errors or warnings in CI/CD pipeline on every commit
- **SC-005**: Link validation catches 100% of broken internal links before documentation is published
- **SC-006**: Feature documentation includes traceable links to specifications in at least 80% of feature-related pages within 6 months
- **SC-007**: Conformance audit identifies and remediates 100% of misplaced documentation files within the information architecture within 3 months
- **SC-008**: Zero documentation PRs are merged without passing validation checks (100% enforcement with no exceptions or bypass mechanism)
- **SC-009**: Documentation contribution time decreases by 40% due to clear guidelines and checklists (measured against average time for features 001-002 documentation updates; tracked via PR timestamps from feature completion to docs PR merge)

### Validation Approach

Success criteria are validated through manual walkthroughs documented in the tasks.md validation tasks from the original specifications, plus automated validation checks in CI/CD.

## Scope

### In Scope

- Defining immutable top-level information architecture: four primary documentation sections (portal-development, portal-administration, user-guide, contributing), governance materials location (.specify/memory/), and feature specifications location (specs/)
- Establishing guidelines for when and how to create subdirectories within the four primary documentation sections
- Creating feature documentation checklist template with guidance for different feature types
- Establishing spec-to-docs and constitution-to-docs cross-reference patterns
- Implementing documentation validation including build checks, link validation, and checklist verification
- Defining documentation quality standards and minimum expectations
- Creating conformance audit process to identify non-conforming existing documentation
- Documenting the documentation contribution process and guidelines
- Integrating documentation checklist into Speckit workflow
- Providing a complete Getting Started flow for new developers
- Clarifying high-level vision, FAIR-first philosophy, and core architecture

### Out of Scope

- Multi-version documentation hosting (e.g., separate docs for v1.0, v2.0) - deferred to future feature
- Automated documentation generation from code (docstrings to docs) - may be considered separately
- Translation and internationalization of documentation - deferred to future feature
- Search engine optimization or analytics for documentation site - not a priority for initial implementation
- Custom Sphinx extensions beyond existing configuration - use standard MyST and Sphinx features
- Automated spec-to-docs synchronization (beyond manual checklist) - too complex for initial version
- Documentation style guide beyond structural requirements - rely on existing Sphinx/MyST conventions
- API reference documentation generation - covered separately by existing autodoc setup

## Dependencies

- **Sphinx**: Documentation is built using Sphinx; version specified in pyproject.toml must support MyST parser
- **MyST Parser**: Markdown support in Sphinx; configuration in conf.py must be compatible
- **Existing .specify/ structure**: Documentation references constitution and specs which must remain in their current locations
- **Speckit workflow**: Feature documentation checklist integrates with existing Speckit commands (specify, plan, tasks, finalize)
- **CI/CD Pipeline**: Documentation validation must run in CI; requires CI configuration (GitHub Actions or equivalent)
- **pydata-sphinx-theme**: Current theme configuration in conf.py; changes to theme might affect documentation structure
- **Git repository structure**: Documentation assumes specs/ and .specify/ directories exist at repository root

## Risks

- **Risk 1**: Contributors may ignore or bypass documentation checklist if not enforced - **Mitigation**: Integrate checklist validation into CI so PRs can't merge without passing
- **Risk 2**: External links may break frequently causing false CI failures - **Mitigation**: Treat external link failures as warnings requiring manual review rather than hard blocks; maintain exclude list for known problematic domains
- **Risk 3**: Existing documentation may be too extensive to remediate quickly - **Mitigation**: Prioritize high-traffic pages and new feature documentation; create migration plan with phases
- **Risk 4**: Spec cross-references may become stale if specs are updated - **Mitigation**: Include spec version or date in cross-references; add validation to check spec existence
- **Risk 5**: Information architecture may not scale as documentation grows - **Mitigation**: Design with clear hierarchy and allow for subdirectories; plan for periodic architecture reviews
- **Risk 6**: Documentation validation may become too strict and slow down development - **Mitigation**: Make validation levels configurable (errors vs warnings); allow temporary exceptions with tracking

## Terminology *(reference)*

**Note**: Documentation sections have both human-readable display names (used in prose and navigation) and directory paths (used in file system and links). The table below shows both.

**Important**: The term "contributor" is ambiguous and should NOT be used alone in specifications. Always use the fully qualified term: "Framework Contributor" for people contributing to FairDM codebase, or "Portal User" for people contributing data to portals. Similarly, use "Portal Developer" (not "developer" or "portal builder") when referring to people building portals with FairDM.

| Term | Definition | Canonical Location |
| ---- | ---------- | ------------------ |
| **Overview** | High-level conceptual documentation section explaining FairDM's purpose, FAIR-first philosophy, core architecture, and contributor model | `docs/overview/` |
| **User Guide** | Documentation section for portal users (people who add/edit data in portals); display name for the user-facing documentation | `docs/user-guide/` |
| **Admin Guide** | Documentation section for portal administrators who manage users, permissions, and metadata quality; display name for administrator-facing documentation | `docs/portal-administration/` |
| **Developer Guide** | Documentation section for Portal Developers (people building new FairDM-powered portals); display name for portal developer documentation | `docs/portal-development/` |
| **Contributing Guide** | Documentation section for Framework Contributors; display name for framework contribution documentation | `docs/contributing/` |
| **Portal User** | Person who adds or edits research data, samples, measurements, and metadata in a FairDM portal | See User Guide |
| **Portal Administrator** | Person who has access to the Django admin site (is_staff=True) and manages portal configuration, users, and permissions | See Admin Guide |
| **Portal Developer** | Person who builds new research data portals using the FairDM framework; primary audience for the Developer Guide | See Developer Guide |
| **Framework Contributor** | Person who contributes to the FairDM framework codebase itself (code, docs, tests) | See Contributing Guide |
| **Information Architecture** | The hierarchical structure defining where documentation lives (sections, subsections, files) and the purpose of each area; establishes the immutable top-level structure and guidelines for subdirectory creation | Defined in this spec |
| **Feature Documentation Checklist** | Template listing documentation sections that require updates for different feature types (new models, UI components, configuration changes, etc.); integrated into Speckit workflow | `.specify/templates/feature-docs-checklist.md` |
| **Spec Cross-Reference** | Link from documentation to specification files providing context about what aspect of the spec the documentation covers; enables traceability from docs to requirements | Pattern: `[spec](../../specs/###-feature-name/spec.md)` |
| **Constitution Cross-Reference** | Link from documentation to specific constitutional principles explaining how a feature aligns with governance requirements | Pattern: `[Constitution: Topic](.specify/memory/constitution.md#anchor)` |
| **Validation Report** | Output from automated documentation validation including build status, link check results, checklist completeness, and quality metrics; generated by CI/CD pipeline | Generated by validation tools |
| **Conformance Audit** | Analysis process that identifies existing documentation not meeting information architecture or quality standards, with specific issues and remediation steps | Process defined in FR-017 |

## Clarifications

### Session 2025-12-30

- Q: What is the baseline developer profile for the Getting Started journey and SC-001? → A: Developers comfortable with Python OOP and basic Django, ideally having completed the official Django tutorials.
- Q: How should the duplicated SC-001 measurable outcomes be handled? → A: Consolidate into a single SC-001 that uses the clarified developer profile and removes overlapping wording.
- Q: Should framework contributors be covered as an explicit audience in this specification? → A: Yes, add a dedicated user story for framework contributors aligned with the contributing documentation.

### Session 2026-01-06

- Q: When documentation validation fails in CI (e.g., broken links, missing checklist items), what should happen to the pull request? → A: Hard block - PR cannot be merged under any circumstances until validation passes
- Q: External links in documentation can fail temporarily (site downtime) or permanently (moved/deleted content). How should the validation system handle external link failures? → A: Check external links but treat failures as warnings; require manual review

### Session 2026-01-07

- Q: User Stories 1-5 describe outcomes requiring actual documentation content (Getting Started guides, admin guides, User Guides). Should these implementation-focused stories remain in this strategy/infrastructure spec? → A: Delete User Stories 1-5 entirely; they are out of scope for this spec
- Q: The spec requires "unchanging directory structure" but also mentions future extensibility. What level of immutability is required for the documentation directory structure? → A: Core structure immutable (4 main sections + .specify/ + specs/), but subdirectories within sections can be added as needed
- Q: FR-019 requires guidance on when to create new documentation files vs adding to existing files, but no criteria are defined. What thresholds should determine file creation? → A: New file when topic >500 words (loose guideline) OR standalone concept OR separate user journey
- Q: When the constitution is amended, how should affected documentation be updated? Who is responsible for triggering and coordinating documentation reviews? → A: Constitution owner triggers docs review
- Q: What happens when specs are updated after initial documentation is written? How is documentation kept aligned with evolving specs? → A: Spec authors responsible for documentation; PR review by maintainers
- Q: The spec uses both "Admin Guide" and "portal-administration" interchangeably. Are these synonyms or is there a distinction between display names and directory paths? → A: "Admin Guide" is the display name/human-readable term; "portal-administration" is the directory path; terminology should clarify this distinction
- Q: The word "contributor" is used ambiguously throughout - sometimes meaning Framework Contributors (who contribute code), other times Portal Users (who contribute data). How should this be clarified? → A: Always specify contributor type
- Q: Several technical terms from Key Entities (Information Architecture, Feature Documentation Checklist, Spec Cross-Reference, etc.) are not defined in Terminology. Should these be added? → A: Add technical terms to terminology
- Q: The spec uses "developers", "portal developers", and "portal builders" inconsistently when referring to people building portals with FairDM. What term should be used consistently? → A: Use "Portal Developer" consistently
- Q: Edge cases mention deprecated and experimental features but don't define how to mark them in documentation. What convention should be used? → A: Standard admonitions for lifecycle

## Open Questions

[None - all aspects of the feature are well-defined based on existing Sphinx structure and Speckit conventions. Reasonable defaults have been chosen where specifics were not provided.]
