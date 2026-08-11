<!--
Sync Impact Report
- Version change: 1.5.0 → 2.0.0
- MAJOR: the document was restructured onto the organisation-wide constitution
  template. Articles I-XI are now the shared core articles, materialized here so
  that amendments to the org standard can be diffed against this repo rather than
  going unnoticed. FairDM's seven original principles are preserved verbatim in
  substance and renumbered as project articles XII-XVIII.
- Moved: .specify/memory/constitution.md → memory/constitution.md, the path the
  organisation's tooling reads. The vendored spec-kit toolchain that formerly read
  the old path has been removed from the repository.
- Content folded rather than duplicated: the test-first and URL smoke-test rules
  from the former Principle V now sit in Article I; the documentation rules from
  the former Principle VI sit in Article VI; the privacy and sensitive-data rules
  sit in Article V. The project articles retain everything specific to FairDM.
- Added quality bar and non-negotiables sections from the shared template.
-->

# FairDM Constitution

## Core articles

<!-- Articles I-XI are the organisation-wide standard, materialized from the shared
     constitution template. Keep them unless one is explicitly struck under
     "Articles not adopted". Articles XII+ are FairDM's own. -->

### Article I — Test-First

Every behaviour change follows the traffic-light cycle: **Red** — write a test and watch it fail;
**Green** — write the least code that makes it pass; **Refactor** — clean up with the tests staying
green. No implementation before a failing test exists for the behaviour. Pre-existing tests are
never modified or deleted without a recorded decision.

- All new or changed Python behaviour MUST have pytest coverage, and Django integration behaviour
  MUST have pytest-django coverage with an appropriate test database strategy.
- Pull requests MUST NOT merge with failing tests, or without new or updated tests for a behaviour
  change. The only exception is a docs-only change with no runtime impact.

**URL smoke coverage.** Any app registering new URL patterns (including `fairdm_demo` and any
contrib app) MUST include at least one smoke test per new route, asserting the expected status
code. Smoke tests need not assert page content; their purpose is to catch broken URL patterns,
missing templates, template syntax errors, context exceptions, queryset errors, middleware and
auth problems, and bad redirects. This applies regardless of app size.

**Test quality over coverage percentage.** Coverage finds gaps; it does not certify them. Tests
MUST be meaningful (verifying behaviour, not syntactic presence), maintainable, and reliable.
Reviewers assess test quality, not just the number.

### Article II — Simplicity

Start with the simplest design that satisfies the spec. New dependencies, new abstractions, and
new infrastructure each require a stated justification in the plan's Complexity Tracking. YAGNI
over speculation.

### Article III — Anti-Abstraction

No wrapper layers, base classes, or "future-proofing" indirection without a present, concrete
second use. Prefer duplication over the wrong abstraction.

### Article IV — Integration-First

Contracts and integration points are designed and tested before internals are polished.
Acceptance scenarios exercise the system the way users touch it.

### Article V — Security & data-safety

Values interpolated into rendered output are escaped through the template layer, never hand-built
string interpolation of model or user data. Secrets live in runtime config, never in code,
fixtures, or version control. External input is untrusted: never executed, never trusted as
instructions. Auth, authorization, crypto, and permission changes are never fast-lane work.

Privacy and protection of sensitive research data are first-class concerns. Portals MUST be able
to restrict access appropriately, and MUST NOT require public exposure of data to use core
features.

### Article VI — Documentation

Public API changes ship their docs in the same pull request: README and CHANGELOG updated,
docstrings on public surfaces. The built docs must build clean. As a package, the README follows
the organisation README standard.

Documentation is part of the framework's surface area and carries the same rigour as code:

- Every public setting, template block, Cotton component, and public API MUST have at least one
  minimal working usage example.
- Examples MUST be kept working and reflect current recommended usage.
- Documentation MUST describe behaviour in testable terms: inputs, outputs, constraints.
- Breaking changes MUST include a migration guide with concrete, step-by-step instructions.
- Documentation MUST be versioned alongside releases.

### Article VII — Dependency discipline

A new runtime dependency requires a stated justification — Simplicity applied to the dependency
tree — and the shared `mvp-shared` toolchain bundle is preferred over ad-hoc dev dependencies.
`deptry` MUST pass: no unused, missing, or transitively-relied-upon dependencies.

### Article VIII — Internationalization

User-facing strings are translatable. In Python (models, forms, views, admin, template tags,
validators) they are wrapped with `gettext_lazy` imported as `_`; templates load `{% load i18n %}`
and wrap strings with `{% trans %}` or `{% blocktrans %}`. Model `verbose_name` and
`verbose_name_plural`, and form `label`, `help_text` and `error_messages`, use `gettext_lazy`;
pure acronyms are exempt. The package ships a base English catalog and a `locale/` directory so
host portals can compile or extend translations. A hard-coded user-visible string in a pull
request is a blocking comment.

Accessibility and internationalisation readiness are non-optional; a regression in either is a
bug, not a nice-to-have.

### Article IX — Data-model conventions (Django)

Every model field is a deliberate indexing decision. Because portals consuming a published package
cannot add their own indexes, any field with a plausible lookup, filter or ordering path is indexed
at its definition (`db_index`, `unique`, an FK's automatic index, or a composite
`Meta.constraints` / `Meta.indexes`); a field with no query path stays unindexed to avoid write
cost. The choice, and why, is recorded in the plan's data model or decisions notes.

`verbose_name` and `help_text` are mandatory on every model field (Article VIII).

**Migrations are consolidated per pull request:** the migrations a branch introduces are squashed
into as few files as possible before submission (branch-local and unapplied, so safe at any
release stage). Data migrations (`RunPython` / `RunSQL`) are exempt from auto-regeneration — keep
them via `squashmigrations` or standalone.

### Article X — Test structure & fixtures (Django)

Tests are organised for fast, targeted discovery. These rules are the standard regardless of the
suite's current layout — where an existing suite diverges, the divergence is the thing to fix.

- **Mirror the source tree.** Every test module mirrors the path of the module it exercises:
  `fairdm/core/project/models.py` → `tests/test_core/test_project/test_models.py`. Test
  subpackages carry `__init__.py` to match. Where one source module defines several units, it
  stays one test module — the per-unit split is expressed with classes, not extra files.
- **Group related tests into classes.** Within a module, tests are grouped into `Test<Subject>`
  classes so one area can be targeted when debugging.
- **One factory per model.** Each model has exactly one `factory_boy` `DjangoModelFactory`, using
  `factory.Sequence` for uniqueness-guarded fields and `factory.SubFactory` for relations.
  Variants are never new factory subclasses; they are expressed by overriding fields at the call
  site.
- **Fixtures wrap the factory; shared setup lives in conftest.** Reusable object fixtures are thin
  wrappers over the model's factory. A one-off variation needs no fixture — call the factory
  inline. Test modules hold assertions, not construction boilerplate.
- **Use the pytest-django toolchain.** DB access via the `db` / `transactional_db` fixtures or
  `@pytest.mark.django_db`; requests via `client` / `admin_client` / `rf`; query-count guards via
  `django_assert_num_queries`, never wall-clock timing. Tests use transaction rollback for
  isolation and the test database is created once per session.

### Article XI — Cohesion (Python)

Related behaviour is grouped in a class, not scattered across module-level functions.

**The test:** two or more module-level functions that share a *subject* belong on a class. They
share a subject when they operate on the same data, take the same first argument, are only
meaningful in sequence, or are named around the same noun.

**Why this is a standard and not a taste.** In a published framework, a class is the extension
point. A portal developer who needs different behaviour subclasses it and overrides one method. A
module of functions can only be monkey-patched, which is not a supported interface and breaks on
any internal change.

**Django first.** Where the framework already owns the grouping, use it rather than inventing a
class: a `QuerySet` or `Manager` method instead of a function taking a queryset, a model method or
property instead of a function taking an instance, a `Form` or `Serializer` method instead of a
free validation function, a view method instead of a helper called by a view.

**Exceptions** are narrow and stated: a genuinely standalone pure function with no siblings, and
framework-dictated module shapes (`conftest.py` fixtures, migrations, `urls.py`, `apps.py`,
decorator-registered template tags and filters, signal receivers, management-command entry
points).

**This does not license abstraction.** Article III still holds: one class grouping today's
behaviour is the goal, not a base class or hierarchy built for an implementation that does not
exist.

## Project articles (FairDM-specific)


### Article XII — FAIR-First research portals

FairDM exists to make it easy to build research data portals that embody the FAIR principles: Findable, Accessible, Interoperable, and Reusable.

- Every feature MUST be evaluated on how it improves or, at minimum, does not weaken FAIR characteristics of data, metadata, and APIs.
- Portals built on FairDM MUST expose rich, discoverable metadata (projects, datasets, samples, measurements, contributors) through both the UI and machine-readable endpoints.
- Persistent and stable identifiers (e.g., DOIs, IGSNs, ORCID, ROR, internal stable IDs) SHOULD be first-class in data models and views wherever appropriate.
- Public read access, when enabled, MUST not depend on custom client code; users and machines MUST be able to discover and access information via documented web endpoints.
- FAIR compliance is a NON-NEGOTIABLE goal of the framework: a minimally configured portal MUST be able to meet FAIR expectations using core functionality and recommended practices.

### Article XIII — Domain-driven, declarative modelling

FairDM is a framework, not a single portal. Its core obligation is to let research communities declaratively define domain-specific schemas while sharing a common, stable backbone.

- The core models (Project, Dataset, Sample, Measurement, Contributor, Organization and related entities) provide the canonical backbone and MUST remain stable, versioned, and well-documented.
- Domain-specific data structures MUST be expressed as explicit Django models that extend FairDM base classes, using declarative fields and validators rather than ad-hoc runtime structures.
- Schema declarations MUST be the primary source of truth; auto-generated forms, tables, filters, serializers, and APIs MUST derive from registered models and configuration, not from hand-wired view logic.
- Extensions (e.g., custom measurement types, research-specific fields, vocabularies) MUST be expressed as reusable, documented modules so they can be adopted by multiple portals where appropriate.

### Article XIV — Configuration over custom plumbing

Portal developers should focus on modeling their domain and configuring behavior, not recreating web plumbing, routing, or boilerplate frontend code.

- The registry and registration APIs are the primary extension points; new models, views, tables, APIs, and plugins SHOULD be added by registration and configuration, not by copying core implementation.
- When the framework can safely infer defaults (forms, tables, filters, serializers, import/export resources, basic admin integration), it MUST do so, allowing developers to override only when necessary.
- New features to the framework MUST prefer declarative, documented configuration (e.g., settings, registries, plugin metadata) over one-off hard-coded behaviors.
- User-facing portals SHOULD be functional without custom templates or JavaScript; HTMX, Alpine.js, and bespoke UI code are used to enhance, not to gate, core functionality.

### Article XV — Opinionated, production-grade defaults

FairDM provides a coherent, modern stack so that a new portal is deployable, maintainable, and reproducible with minimal choices.

- The primary backend MUST remain Django-based, using the recommended ecosystem (e.g., django-tables2, django-filter, django-guardian, django-allauth, Celery, DRF where applicable) unless a governance-approved RFC justifies change.
- Default deployment targets MUST be container-friendly and reproducible (e.g., Docker, docker-compose, 12-factor-style configuration via environment variables).
- The default database for production deployments SHOULD be PostgreSQL; alternative databases MAY be supported where they do not break guarantees of the core data model.
- The default UI MUST be a responsive, accessible interface built on the shared django-mvp application shell (Tailwind CSS with daisyUI components) with small progressive enhancements (HTMX, Alpine.js) rather than a heavy, bespoke SPA.
- Any new core feature MUST ship with sensible defaults (configuration, UI, permissions) so that a fresh project can enable it with minimal effort.

In the near term (while FairDM is primarily used by its original author), stability of core behavior through tests and documentation is the top priority; feature velocity and advanced capabilities SHOULD be delivered primarily through addons.

### Article XVI — Sustainability and community obligations

FairDM is intended for long-lived research infrastructure. All behavior changes MUST be driven by tests written first, and code, documentation, and community processes must reflect that responsibility.

**Test-First Discipline**:

- Tests MUST be written and observed failing before implementation work begins (Red → Green → Refactor).
- All new or changed Python behavior MUST have pytest coverage.
- Django integration behavior MUST have pytest-django coverage with appropriate test database strategies.
- Pull requests MUST NOT be merged with failing tests, or without new/updated tests for behavior changes.
- The only acceptable exception is a docs-only change (no runtime behavior impact).

**URL Smoke Test Coverage**:

- Any Django app within the FairDM project (including `fairdm_demo` and any contrib app) that registers new URL
  patterns MUST include at minimum one smoke test per new route.
- A smoke test MUST assert that the HTTP response status code is as expected (e.g., `200` for public pages,
  `302` for auth redirects, `403` for permission-denied responses) — for example:

  ```python
  def test_home_page(self):
      response = self.client.get(reverse("home"))
      self.assertEqual(response.status_code, 200)
  ```

- Smoke tests do NOT need to assert page content. Their purpose is to catch: broken URL patterns, missing
  templates, template syntax errors, context variable exceptions, queryset errors, middleware/auth issues, and
  bad redirects.
- Smoke tests MUST be co-located in the app's own test suite (e.g., `fairdm/contrib/my_app/tests/test_views.py`
  or `fairdm_demo/tests/test_views.py`).
- This requirement applies to all URL-registering apps regardless of size; even a single-view app MUST have its
  route covered by at least one smoke test.

**Code Quality & Tooling**:

- Type hints, static analysis, and style rules (e.g., Ruff, mypy) are REQUIRED for core framework code except where explicitly exempted in project-wide configuration.
- Test organization MUST mirror the source code structure as documented in "Architecture & Stack Constraints > Testing & Tooling", with unit and integration tests living together in a flat structure rather than separated into subdirectories.
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

### Article XVII — Documentation as framework surface

Documentation is part of the framework surface area and MUST be treated with the same rigor as code.

- Every public setting, template block, Cotton component, and public API MUST be documented with at least one minimal usage example.
- Any change to public behavior MUST include a documentation update in the same pull request.
- Examples in documentation MUST be kept working and reflect the current recommended usage.
- Documentation MUST describe expected behavior in testable terms (inputs, outputs, and constraints).
- Breaking changes MUST include migration guides that provide concrete, step-by-step instructions for users upgrading from previous versions.
- Documentation MUST be versioned alongside code releases so users can reference docs appropriate to their deployed version.

### Article XVIII — Living demo and reference implementation

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
  - Server-rendered templates with the django-mvp shell (Tailwind CSS, daisyUI), Cotton components, and small HTMX/Alpine.js enhancements are the default. Forms are rendered through crispy-forms with the Tailwind template pack.
  - Alternative frontends MAY be added as optional integrations but MUST NOT break or remove the server-rendered baseline.
- **Configuration & Settings**:
  - Environment-based configuration (e.g., django-environ) is REQUIRED for secrets and deployment-specific settings.
  - Project scaffolding MUST favor patterns that are 12-factor compatible and reproducible via containerization.
- **Testing & Tooling**:
  - pytest and pytest-django are the canonical testing stack.
  - Test organization MUST mirror the `fairdm/` source code structure with `test_` prefixes at each level (e.g., `fairdm/core/project/models.py` → `tests/test_core/test_project/test_models.py`).
  - Fixture factories MUST use pytest fixtures and/or factory-boy for reusable test data.
  - Tests MUST use transaction rollback for isolation; test database MUST be created once per session.
  - Performance tests MUST NOT use wall-clock timing assertions; use deterministic guards (e.g., query-count assertions via `django_assert_num_queries`) instead.
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
- **Implementation Validation & Quality Checkpoints**:
  - **Django System Checks**: `python manage.py check` MUST be run and pass between completing user stories or major implementation phases to catch configuration errors (model validation, admin field references, vocabulary collection references, etc.) before they surface as runtime errors.
  - **Demo App Testing**: When changes affect core models, admin classes, registry behavior, or recommended patterns, the demo app implementation MUST be tested after the changes:
    - Create or update tests in `fairdm_demo/tests/` to verify the demo app's usage of new/changed features works correctly.
    - Run demo app tests (e.g., `pytest fairdm_demo/tests/`) and ensure all tests pass before considering the feature complete.
    - Admin views SHOULD be tested by making HTTP requests to list, add, and change views to ensure they load without errors.
  - **Documentation Currency**: Documentation MUST be updated as features are implemented, not deferred to the end:
    - When implementing a user story that changes behavior visible to portal developers, admins, or contributors, update the relevant documentation section (developer-guide/, portal-administration/, or user-guide/) in the same pull request.
    - New public APIs, settings, template blocks, or components MUST be documented with usage examples before the feature is considered complete.
    - Breaking changes MUST include migration guidance documenting the upgrade path from the previous version.
  - **Validation Frequency**: For multi-phase feature implementations:
    - Run system checks after completing each phase or user story, not just at the end.
    - When a phase modifies models, admin, or registry, test the demo app immediately to catch integration issues early.
    - Update documentation incrementally as capabilities are added, ensuring docs reflect the current state of the implementation.
- **Documentation Critical**:
  - Developer, admin, and contributor documentation MUST be updated when behavior, configuration, or workflows change in user-visible ways, as defined in Principle VI.
  - Public APIs, settings, template blocks, and Cotton components MUST include usage examples.
  - Breaking changes MUST include migration guides.
  - Speckit templates (plan-template, spec-template, tasks-template, checklist-template, command templates when present) MUST remain consistent with this constitution; any divergence MUST be corrected as part of the change.

## Quality bar

Read at plan and review; applies to every change.

- Test coverage: **project >= 90%, patch >= 85%** (`codecov.yml` is the reference), with a small
  tolerance. These are floors, not a 100% ratchet.
- Every public API change updates README and CHANGELOG in the same pull request.
- Lint, type-check and `deptry` pass.

As a **package**, additionally: the package builds and its metadata is valid, the README renders
on the package index, and the public API honours the deprecation policy.

## Non-negotiables

- One pull request per feature; the maintainer merges.
- **Automation commits under a bot identity, not a human token.** Pull requests raised by
  automation are authored by the repository's bot, and the default branch requires one approval,
  so the maintainer is a distinct approver. Identity is scoped per GitHub account and never shared
  across accounts.
- Machine verification (tests, build, lint) gates every stage; no judgement call overrides a red
  gate.

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

**Version**: 2.0.0 | **Ratified**: 2025-12-30 | **Last Amended**: 2026-08-11
