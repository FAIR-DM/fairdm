# Research: FairDM Documentation Baseline

## Decisions

### D1. Documentation Stack
- **Decision**: Use the existing `fairdm-docs` package (Sphinx + `pydata-sphinx-theme` tooling) as the documentation stack for this feature.
- **Rationale**: `fairdm-docs` is already tailored for FairDM, encapsulates Sphinx configuration, and standardises the look and feel using `pydata-sphinx-theme`. Reusing it keeps the documentation aligned with other FairDM projects and reduces maintenance overhead.
- **Alternatives considered**:
  - **Vanilla Sphinx setup**: More manual configuration and duplication of effort; rejected because `fairdm-docs` already provides the needed scaffolding and conventions.
  - **MkDocs or other static site generators**: Would diverge from the existing documentation tooling and require rethinking theme, navigation, and build pipelines; rejected for now to maintain consistency and focus.

### D2. Documentation Structure & Roles
- **Decision**: Keep the existing top-level structure (admin-guide, contributor-guide, developer-guide, contributing) and refine content and cross-links rather than introducing new top-level sections.
- **Rationale**: The current structure already maps well to the key user roles identified in the specification. Improving clarity, navigation, and getting-started flows within this structure is less disruptive and easier to adopt.
- **Alternatives considered**:
  - **Flattened single guide**: A single monolithic guide would simplify structure but make it harder to target content to specific roles; rejected to preserve role-focused guidance.
  - **More granular top-level sections**: Risk of overwhelming users and fragmenting content; better handled as subsections and toctrees within the existing areas.

### D3. Getting Started Journey
- **Decision**: Provide one opinionated, linear Getting Started journey for new developers that reuses an existing demo portal configuration and focuses on:
  1. Running the portal locally.
  2. Defining a minimal Sample/Measurement model.
  3. Registering it and verifying visibility in the UI and via programmatic access.
- **Rationale**: A single, end-to-end journey is easier to maintain and communicate than multiple variants. It matches the specification’s requirement for an independently testable P1 user story.
- **Alternatives considered**:
  - **Multiple parallel getting-started tracks** (e.g., Docker-first vs local-venv): Deferred to future features; they add complexity and documentation branching that is not necessary for the first baseline.

### D4. Implementation-Agnostic Specification, Implementation-Specific Quickstarts
- **Decision**: Keep the feature specification and high-level docs implementation-agnostic, while allowing developer-oriented quickstarts and how-to pages to mention concrete tools (e.g., exact commands for `fairdm-docs` and Sphinx).
- **Rationale**: This respects the Speckit specification guidelines and the FairDM constitution’s emphasis on configuration over hard-coded tooling, while still giving developers actionable guidance where appropriate.
- **Alternatives considered**:
  - **Embedding specific commands into the spec**: Rejected as it mixes design intent with implementation detail and would make future tooling changes harder.

## Unknowns / Clarifications

At this time, there are no open NEEDS CLARIFICATION items for this feature. All requirements are focused on user journeys and documentation structure rather than specific tooling contracts.

If future requirements introduce additional delivery channels (e.g., PDF exports, versioned docs per FairDM release), a follow-up research phase will be needed to evaluate Sphinx extensions or other tooling.
