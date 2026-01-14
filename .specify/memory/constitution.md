<!--
Sync Impact Report
- Version change: 1.2.0 → 1.3.0
- Modified principles: None
- Added sections:
	- Principle VII: "Living Demo & Reference Implementation" - New principle establishing fairdm_demo as a maintained reference application that demonstrates current best practices, stays synchronized with framework changes, and serves as executable documentation with docstrings linking to relevant documentation.
- Removed sections: None
- Templates requiring updates (✓ updated / ⚠ pending):
	- ✓ .specify/templates/plan-template.md (Constitution Check should consider demo app updates)
	- ✓ .specify/templates/spec-template.md (Compatible - specs should note demo app impact)
	- ✓ .specify/templates/tasks-template.md (Compatible - tasks should include demo app updates when relevant)
	- ⚠ .github/instructions/copilot.instructions.md (Should reference Principle VII for demo app maintenance)
	- ⚠ docs/ (Documentation should reference demo app as working examples)
- Follow-up TODOs:
	- Add docstrings to fairdm_demo models, views, and configuration linking to documentation
	- Ensure demo app migrations stay current with core model changes
	- Create CI check to verify demo app stays functional with framework changes
	- Document demo app architecture and purpose in contributing guide
-->

# FairDM Constitution

## Core Principles

### I. FAIR-First Research Portals

FairDM exists to make it easy to build research data portals that embody the FAIR principles: Findable, Accessible, Interoperable, and Reusable.

- Every feature MUST be evaluated on how it improves or, at minimum, does not weaken FAIR characteristics of data, metadata, and APIs.
- Portals built on FairDM MUST expose rich, discoverable metadata (projects, datasets, samples, measurements, contributors) through both the UI and machine-readable endpoints.
- Persistent and stable identifiers (e.g., DOIs, IGSNs, ORCID, ROR, internal stable IDs) SHOULD be first-class in data models and views wherever appropriate.
- Public read access, when enabled, MUST not depend on custom client code; users and machines MUST be able to discover and access information via documented web endpoints.
- FAIR compliance is a NON-NEGOTIABLE goal of the framework: a minimally configured portal MUST be able to meet FAIR expectations using core functionality and recommended practices.

### II. Domain-Driven, Declarative Modeling

FairDM is a framework, not a single portal. Its core obligation is to let research communities declaratively define domain-specific schemas while sharing a common, stable backbone.

- The core models (Project, Dataset, Sample, Measurement, Contributor, Organization and related entities) provide the canonical backbone and MUST remain stable, versioned, and well-documented.
- Domain-specific data structures MUST be expressed as explicit Django models that extend FairDM base classes, using declarative fields and validators rather than ad-hoc runtime structures.
- Schema declarations MUST be the primary source of truth; auto-generated forms, tables, filters, serializers, and APIs MUST derive from registered models and configuration, not from hand-wired view logic.
- Extensions (e.g., custom measurement types, research-specific fields, vocabularies) MUST be expressed as reusable, documented modules so they can be adopted by multiple portals where appropriate.

### III. Configuration Over Custom Plumbing

Portal developers should focus on modeling their domain and configuring behavior, not recreating web plumbing, routing, or boilerplate frontend code.

- The registry and registration APIs are the primary extension points; new models, views, tables, APIs, and plugins SHOULD be added by registration and configuration, not by copying core implementation.
- When the framework can safely infer defaults (forms, tables, filters, serializers, import/export resources, basic admin integration), it MUST do so, allowing developers to override only when necessary.
- New features to the framework MUST prefer declarative, documented configuration (e.g., settings, registries, plugin metadata) over one-off hard-coded behaviors.
- User-facing portals SHOULD be functional without custom templates or JavaScript; HTMX, Alpine.js, and bespoke UI code are used to enhance, not to gate, core functionality.

### IV. Opinionated, Production-Grade Defaults

FairDM provides a coherent, modern stack so that a new portal is deployable, maintainable, and reproducible with minimal choices.

- The primary backend MUST remain Django-based, using the recommended ecosystem (e.g., django-tables2, django-filter, django-guardian, django-allauth, Celery, DRF where applicable) unless a governance-approved RFC justifies change.
- Default deployment targets MUST be container-friendly and reproducible (e.g., Docker, docker-compose, 12-factor-style configuration via environment variables).
- The default database for production deployments SHOULD be PostgreSQL; alternative databases MAY be supported where they do not break guarantees of the core data model.
- The default UI MUST be a responsive, accessible Bootstrap 5-based interface with small progressive enhancements (HTMX, Alpine.js) rather than a heavy, bespoke SPA.
- Any new core feature MUST ship with sensible defaults (configuration, UI, permissions) so that a fresh project can enable it with minimal effort.

In the near term (while FairDM is primarily used by its original author), stability of core behavior through tests and documentation is the top priority; feature velocity and advanced capabilities SHOULD be delivered primarily through addons.

### V. Test-First Quality & Sustainability (NON-NEGOTIABLE)

FairDM is intended for long-lived research infrastructure. All behavior changes MUST be driven by tests written first, and code, documentation, and community processes must reflect that responsibility.

**Test-First Discipline**:

- Tests MUST be written and observed failing before implementation work begins (Red → Green → Refactor).
- All new or changed Python behavior MUST have pytest coverage.
- Django integration behavior MUST have pytest-django coverage with appropriate test database strategies.
- Cotton component tests MUST use `django_cotton.render_component()` with pytest-django's `rf` fixture (NOT Template() or render_to_string).
- User-visible/UI behavior MUST have pytest-playwright coverage when the change affects rendered output, interactions, or accessibility.
- Pull requests MUST NOT be merged with failing tests, or without new/updated tests for behavior changes.
- The only acceptable exception is a docs-only change (no runtime behavior impact).

**Code Quality & Tooling**:

- Type hints, static analysis, and style rules (e.g., Ruff, mypy) are REQUIRED for core framework code except where explicitly exempted in project-wide configuration.
- Test organization MUST follow the documented test layer taxonomy (unit, integration, contract) and naming conventions.
- **Test quality over coverage targets**: Coverage metrics are a guide, not a goal. Tests MUST be:
  - **Meaningful**: Verify behavior and critical functionality, not just syntactical presence
  - **Maintainable**: Easy to update when underlying code changes
  - **Reliable**: Consistently pass or fail based on actual code correctness
- Coverage tools SHOULD be used to identify untested code paths, but high coverage percentages alone do NOT guarantee quality.
- New features SHOULD aim for thorough test coverage of critical paths and edge cases; reviewers MUST assess test quality and completeness, not just coverage numbers.

**Documentation & Community**:

- Documentation (developer, admin, and User Guides) MUST be updated alongside new features or breaking changes so that research teams with modest technical skills can remain productive.
- Accessibility, internationalisation readiness, and usability SHOULD be considered non-optional; regressions in these areas MUST be treated as bugs.
- Community contributions MUST respect this constitution and the published User Guidelines; maintainers MUST clearly communicate rationale for accepting or rejecting proposals with reference to these principles.
- Privacy and protection of sensitive research data MUST be treated as first-class concerns: portals MUST be able to restrict access appropriately and MUST NOT require public exposure of data to use core features.

### VI. Documentation Critical

Documentation is part of the framework surface area and MUST be treated with the same rigor as code.

- Every public setting, template block, Cotton component, and public API MUST be documented with at least one minimal usage example.
- Any change to public behavior MUST include a documentation update in the same pull request.
- Examples in documentation MUST be kept working and reflect the current recommended usage.
- Documentation MUST describe expected behavior in testable terms (inputs, outputs, and constraints).
- Breaking changes MUST include migration guides that provide concrete, step-by-step instructions for users upgrading from previous versions.
- Documentation MUST be versioned alongside code releases so users can reference docs appropriate to their deployed version.

### VII. Living Demo & Reference Implementation

FairDM maintains a reference application (`fairdm_demo`) that serves as executable documentation, a testing ground for new features, and a model for portal developers.

- The demo app MUST remain functional and up-to-date with the current framework version at all times.
- When core models, APIs, or recommended patterns change, the demo app MUST be updated in the same pull request to reflect those changes.
- Demo app code (models, views, configuration, filters, tables, options) SHOULD include comprehensive docstrings that explain the purpose, usage, and rationale for each component.
- Docstrings in demo app code SHOULD link to relevant sections of the documentation using clear references (e.g., "See documentation: [Topic Name](path/to/docs/topic.md)") where applicable.
- The demo app SHOULD demonstrate current best practices for:
  - Model registration and configuration
  - Custom Sample and Measurement types
  - Integration with django-tables2, django-filter, and other framework components
  - Permission handling and object-level access control
  - Import/export configuration
  - Plugin development and integration
- The demo app MAY include examples that go beyond minimal usage to illustrate advanced patterns, but MUST maintain simplicity and clarity as its primary goals.
- CI/CD pipelines MUST verify that the demo app remains functional (models migrate cleanly, basic pages render, no import errors) as part of the standard test suite.
- Documentation SHOULD reference the demo app as working examples where appropriate, creating a bi-directional link between narrative documentation and executable code.

**Rationale**: The demo app serves triple duty as (1) a smoke test that framework changes work in a realistic context, (2) a learning resource for new portal developers, and (3) a forcing function to ensure patterns recommended in documentation are actually usable. By treating it as a first-class artifact with constitutional protection, we ensure it doesn't drift out of sync and become misleading or broken.

## Architecture & Stack Constraints

This section defines the non-negotiable architectural boundaries and technology choices that keep FairDM coherent and maintainable.

- **Language & Runtime**: FairDM core MUST be implemented in Python and target currently supported CPython versions as defined in the project documentation and pyproject configuration.
- **Web Framework**: Django is the foundational web framework. Alternatives MAY be evaluated experimentally but MUST NOT replace Django for the core without a major-version governance decision and migration strategy.
- **Data Storage**:
  - The core data model MUST be relational and map to a SQL database; PostgreSQL is the reference implementation.
  - Migrations for core models MUST be maintained in the framework codebase; user-defined models follow normal Django migration workflows.
- **Asynchronous Work**: Long-running or high-volume operations (e.g., imports, exports, heavy analysis) SHOULD be executed using Celery or a governance-approved equivalent, with clear task monitoring guidance.
- **API Layer**: When REST or programmatic access is enabled, Django REST Framework (or a governance-approved successor) SHOULD be used, and generated APIs MUST honor FAIR metadata and permission rules.
- **Frontend**:
  - Server-rendered templates with Bootstrap 5, Cotton components, and small HTMX/Alpine.js enhancements are the default.
  - Alternative frontends MAY be added as optional integrations but MUST NOT break or remove the server-rendered baseline.
- **Configuration & Settings**:
  - Environment-based configuration (e.g., django-environ) is REQUIRED for secrets and deployment-specific settings.
  - Project scaffolding MUST favor patterns that are 12-factor compatible and reproducible via containerization.
- **Testing & Tooling**:
  - pytest and pytest-django are the canonical testing stack.
  - Test organization MUST follow the documented test layer taxonomy (unit: `tests/unit/{app}/test_{module}.py`, integration: `tests/integration/{app}/test_{module}.py`, contract: `tests/contract/{app}/test_{module}.py`).
  - Fixture factories MUST use pytest fixtures and/or factory-boy for reusable test data.
  - Integration tests MUST use transaction rollback for test isolation; test database MUST be created once per session.
  - Cotton component tests MUST use `django_cotton.render_component()` with pytest-django fixtures.
  - UI/interaction tests MUST use pytest-playwright for user-visible behavior validation.
  - Coverage measurement SHOULD use coverage.py to identify untested code paths; coverage is a guide to find gaps, not a gate to merge.
    - Static analysis and formatting tooling (e.g., Ruff, mypy, djlint) as defined in pyproject.toml MUST be used for core development.
- **Core MUST include**:
  - The canonical data model backbone (Project, Dataset, Sample, Measurement, Contributor, Organization and closely related entities).
  - Facilities to collect, validate, and store the metadata required for FAIR-compliant portals.
  - Basic CRUD and editing flows for core entities, including permissions-aware creation, update, and deletion.
  - Basic browsing, search, and download/access flows for data and metadata, respecting privacy and authorization constraints.
  - Basic analytics and activity indicators that help administrators understand core usage and health (e.g., counts, simple trends), when they can be implemented generically.

- **Addons SHOULD provide** (examples, non-exhaustive):
  - Advanced or domain-specific analytics, dashboards, and reporting.
  - Community or collaboration features (e.g., discussions, comments) similar to fairdm-discussions and other pluggable apps.
  - Deep integrations with external systems (e.g., discipline-specific repositories, bespoke visualization tools) that are not universally required.
  - Highly specialized or domain-specific UI workflows that go beyond the generic portal patterns.

Core MAY offer lightweight hooks and extension points to support these addons but SHOULD avoid embedding domain-specific behavior that can live more appropriately in separate packages.

## Development Workflow & Quality Gates

This section governs how new capabilities are proposed, designed, and implemented within the FairDM project, including how the Speckit-based specification files are used.

- **Specification First**:
  - Non-trivial changes MUST start with a feature specification (spec.md) that articulates user stories, priorities, and measurable success criteria in business and research terms.
  - User stories MUST be independently testable slices of value and ordered by priority (P1, P2, P3, …).
- **Planning & Constitution Check**:
  - Each feature MUST include an implementation plan (plan.md) that records technical context, chosen architecture, and project structure.
  - The “Constitution Check” section in plan.md MUST explicitly note how the design aligns with the Core Principles and record any intentional violations in the “Complexity Tracking” table with justification.
- **Task Breakdown**:
  - Tasks (tasks.md) MUST be grouped by user story and structured so that each story can be implemented and tested independently where feasible.
  - Shared foundational work (infrastructure, core models) MUST be captured as explicit blocking tasks before story-specific implementation.
- **Test-First Discipline**:
  - Tests MUST be written and observed failing before implementation work begins (Red → Green → Refactor) as defined in Principle V.
  - Contract/integration tests SHOULD be written before or alongside implementation for critical user journeys.
  - No change MAY be merged that causes the agreed test suite for the touched areas to fail.
  - Pull requests without appropriate test coverage for behavior changes MUST NOT be merged (except docs-only changes).
- **Documentation Critical**:
  - Developer, admin, and contributor documentation MUST be updated when behavior, configuration, or workflows change in user-visible ways, as defined in Principle VI.
  - Public APIs, settings, template blocks, and Cotton components MUST include usage examples.
  - Breaking changes MUST include migration guides.
  - Speckit templates (plan-template, spec-template, tasks-template, checklist-template, command templates when present) MUST remain consistent with this constitution; any divergence MUST be corrected as part of the change.

## Governance

The constitution defines how FairDM is evolved and how compliance is enforced.

- **Governance & Scope**:
  - This constitution supersedes ad-hoc practices when they conflict.
  - It applies to the core FairDM framework and any official demo or reference projects maintained in this repository (including `fairdm_demo`).
  - At present, final authority for constitutional changes and major core decisions rests with the original author as BDFL (Benevolent Dictator For Life), while explicitly preparing for a future, broader governance model.
- **Amendments & Versioning**:
  - Amendments MUST be made via pull request that clearly states the intended change, rationale, and expected impact on existing portals and contributors.
  - Constitution versions MUST follow semantic versioning:
    - **MAJOR**: Backward-incompatible governance or principle changes, or removal/redefinition of existing principles.
    - **MINOR**: Addition of new principles or sections, or substantial expansion of existing guidance.
    - **PATCH**: Clarifications, non-semantic wording changes, and typo fixes.
  - Any change to this document MUST update the version, Last Amended date, and Sync Impact Report at the top of the file.
  - The FairDM core package itself SHOULD follow semantic versioning. Occasional breaking changes to the core API and data model are permitted, but MUST be clearly versioned, documented, and accompanied by migration guidance; as adoption grows, the threshold for such changes SHOULD become increasingly strict and MAY lead to formal LTS policies.
- **Compliance & Review**:
  - Code review for core changes MUST consider alignment with the Core Principles, Architecture & Stack Constraints, and Workflow rules defined here.
  - When violations are accepted (e.g., for pragmatic reasons), they MUST be documented in the relevant plan.md “Complexity Tracking” section and, where long-lived, reflected in a future constitutional amendment.
  - Runtime guidance for contributors and AI agents (e.g., .github/instructions/copilot.instructions.md and related files) MUST be kept consistent with this constitution.
- **Transparency & Community Input**:
  - Proposed constitutional changes SHOULD be discussed openly (e.g., via issues or discussions) before being merged.
  - Maintainers SHOULD provide clear, written rationale when accepting or rejecting significant changes with explicit reference to this document.
  - As additional maintainers and institutional stakeholders join the project, a more formal governance structure (e.g., a small core team or steering group with an RFC process) SHOULD be established and documented as an amendment to this section.

**Version**: 1.3.0 | **Ratified**: 2025-12-30 | **Last Amended**: 2026-01-08
