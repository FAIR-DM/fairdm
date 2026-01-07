## Feature Specification: Production-Ready Configuration via fairdm.conf

**Feature Branch**: `003-fairdm-setup`
**Created**: 2026-01-02 (renamed from 002-production-config-fairdm-conf on 2026-01-07)
**Status**: Draft
**Input**: User description: "Goal: Deliver a clear, opinionated production configuration story using the fairdm.conf package. Scope: Define responsibilities and boundaries of fairdm.conf, provide patterns for safe settings overrides, and support PostgreSQL, Redis, container-based deployment, and pluggable addons without brittle coupling. Why now: A stable, production-ready configuration baseline is critical for existing and future portals to rely on FairDM with confidence."

## Clarifications

### Session 2026-01-02

- Q: When a portal starts and backing services for cache/broker/background jobs (e.g., `REDIS_URL`) are missing/unreachable, what should the baseline do? → A: Fail fast in production and staging; degrade with a prominent warning in development.
- Q: Where should the development and staging overrides live (as the primary, supported pattern)? → A: Separate environment profile modules for `development` and `staging` that import the production baseline and then override.
- Q: For project-specific overrides (branding, feature flags, extra apps), where should portal teams put them? → A: In the portal’s settings module (e.g., `config/settings.py`) immediately after calling `fairdm.setup(...)`.
- Q: When required configuration is missing/invalid at startup, should the error message include all detected problems or stop at the first one? → A: Report all missing/invalid items in a single startup error.
- Q: If an addon listed in `fairdm.setup(addons=[...])` is misconfigured (e.g., missing `__fdm_setup_module__` or its setup module can’t be imported), what should happen? → A: Fail fast in `production`/`staging`, but warn and skip in `development`.

### Session 2026-01-02 (Architecture Clarification)

- Q: How should the configuration architecture work? → A: Keep `fairdm/conf/settings/*` as the production baseline; `setup()` orchestrates loading them based on profile. The existing settings directory contains production-ready modular settings. Individual modules target specific production requirements (caching, media/static, database, etc.). No separate base.py/production.py files are needed.
- Q: What should the development environment override file be named? → A: `local.py` (follows common Django convention for "local development").
- Q: How should the settings/* modules be organized? → A: Consolidate into ~8-12 focused modules aligned with production concerns (database, cache, security, static/media, email, logging, apps/middleware, celery, auth). Rearrange, edit, and consolidate current settings modules within this directory for long-term maintainability.
- Q: How should addon configuration be loaded? → A: Addons provide a setup module (e.g., `addon/conf.py`); `setup()` imports and executes it after loading base settings.
- Q: How should validation errors be reported? → A: Collect all errors during validation, then raise single `ImproperlyConfigured` exception with all issues listed.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Stand up a production-ready portal (Priority: P1)

A portal maintainer wants to bring a new FairDM-based portal into production using the recommended configuration layer so that they can rely on a clear, documented baseline for database, cache, background jobs, and static/media handling without writing their own configuration from scratch.

**Why this priority**: This is the primary value of the configuration feature: enabling teams to deploy a reliable production portal quickly and consistently.

**Independent Test**: A maintainer can follow the configuration documentation to stand up a fresh production environment for a reference portal using the provided configuration layer and environment variables only, without editing core configuration code.

**Acceptance Scenarios**:

1. **Given** a clean project using the configuration layer, **when** a maintainer provides production environment values for database, cache, static/media, and background processing, **then** the portal starts successfully in a production profile without additional configuration code changes.
2. **Given** a misconfigured or missing required environment value, **when** the portal starts, **then** the maintainer sees a clear, actionable error message that identifies what needs to be fixed.

---

### User Story 2 - Customise project-specific overrides safely (Priority: P1)

A portal developer wants to adjust settings for their specific project (for example, enabling an extra add-on, changing branding, or toggling a feature flag) without editing the core configuration baseline so that upgrades remain straightforward and conflicts are minimised.

**Why this priority**: Without a safe override pattern, each portal risks diverging from the baseline in incompatible ways, making upgrades and support difficult.

**Independent Test**: A developer can introduce project-specific overrides following the documented pattern (for example, an override module and environment variables) and confirm that changes apply correctly while the baseline remains intact and upgradeable.

**Acceptance Scenarios**:

1. **Given** a project using the baseline configuration, **when** a developer adds overrides in the documented location and format, **then** those overrides take effect without modifying the baseline configuration files.
2. **Given** a future update to the baseline configuration, **when** the project upgrades to a new FairDM version, **then** the project-specific overrides still apply and no manual rework of the baseline configuration is required.

---

### User Story 3 - Integrate addons without fragile settings coupling (Priority: P2)

An addon author wants to publish a reusable addon that integrates with the configuration layer so that portal teams can enable and configure it consistently without hand-editing multiple settings or risking configuration drift.

**Why this priority**: Addons extend the platform; if their configuration is ad hoc, portal deployments become fragile and difficult to support.

**Independent Test**: An addon can declare its configuration needs in a way that fits into the baseline pattern, and a portal maintainer can enable or disable the addon following a documented set of steps.

**Acceptance Scenarios**:

1. **Given** an addon that follows the documented configuration pattern, **when** a maintainer enables it using the recommended configuration entry points, **then** the addon is active with sensible defaults and clearly documented environment options.
2. **Given** the same addon, **when** a maintainer decides to disable it following the documented steps, **then** the portal remains stable and no orphaned or conflicting configuration remains.

---

### Edge Cases

- Environments where only some backing services (for example, cache or background workers) are available initially; in development the configuration should degrade with prominent warnings, while production/staging should fail fast.
- Mismatched or partial environment configuration across multiple environments (development, staging, production) that could otherwise lead to surprises when promoting a portal.
- Addons that require additional services (for example, extra message queues or storage) and need a clear way to express those requirements within the configuration model.
- Migration from an older, ad hoc configuration into the opinionated configuration layer while keeping existing portals online.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The platform MUST provide a single, clearly documented configuration entry point that represents the recommended production baseline for FairDM portals.
- **FR-002**: The configuration layer MUST define and document which responsibilities it owns (for example, core settings for database, cache, background jobs, static/media handling, and URLs) versus which remain project-specific.
- **FR-003**: The configuration layer MUST support configuration for a production-grade relational database engine as a first-class, documented target, including connection parameters and recommended defaults.
- **FR-004**: The configuration layer MUST support configuration for a production-grade network cache service as a first-class, documented target, including connection parameters and recommended defaults.
- **FR-005**: The configuration layer MUST provide a concrete, opinionated pattern for background task processing (including queue, broker, and result backend) that is sufficient to run a full production stack out of the box, while allowing advanced teams to replace this stack via their own configuration at their own responsibility.
- **FR-006**: The configuration layer MUST support environment-driven configuration for all production-critical values (such as database, cache, storage, secrets, and debug flags) so that portals can be deployed in containers or traditional environments without editing configuration code.
- **FR-007**: The platform MUST provide a documented override pattern that allows project teams to extend or override baseline configuration safely without modifying the baseline configuration code. The primary supported pattern is: call `fairdm.setup(...)` first in the portal settings module (e.g., `config/settings.py`), then place project-owned overrides immediately after that call.
- **FR-008**: The configuration layer MUST support multiple environments (for example, development, staging, production) using a primary pattern in which each environment has its own profile module that imports a shared production-ready baseline and then overrides specific values as needed, selected via a clear environment indicator (for example, a dedicated configuration environment variable).
- **FR-009**: The configuration documentation MUST include a reference deployment story that demonstrates container-based deployment driven entirely by environment variables.
- **FR-010**: The configuration layer MUST provide a structured way for addons to declare their configuration needs (for example, required settings and environment variables) so that portal teams can enable and configure addons without editing multiple unrelated files. Misconfigured addons MUST fail fast in `production`/`staging`, and MUST warn and be skipped in `development`.
- **FR-011**: The configuration documentation MUST describe how addon configuration interacts with the baseline and override patterns to minimise brittle coupling.
- **FR-012**: The configuration layer MUST surface clear, human-readable error messages when required configuration values are missing, invalid, or inconsistent across environments. In particular, the baseline MUST fail fast in `production` and `staging` when required backing services are missing/unreachable, and MUST degrade with prominent warnings in `development`. When failing fast, errors SHOULD report all detected missing/invalid items in a single startup error message.
- **FR-013**: The platform MUST recommend environment variables as the primary, canonical baseline mechanism for providing secrets (such as credentials and tokens) to the configuration layer, in a way that keeps these values out of source control and remains practical for common hosting environments.

### Key Entities *(include if feature involves data)*

- **Configuration Baseline**: The set of recommended default configuration values and responsibilities that define what it means for a FairDM portal to be “production-ready”.
- **Environment Profile**: A logical grouping of configuration values for a specific environment (for example, development, staging, production), derived from the baseline and environment-specific inputs.
- **Override Layer**: The project-controlled configuration additions or adjustments that sit on top of the baseline (for example, project branding, feature flags, addon choices) and are explicitly separated from the baseline for upgrade safety.
- **Addon Configuration Block**: The subset of configuration that an addon needs to declare (for example, additional settings and environment-driven values) so that it can be enabled, tuned, or disabled in a consistent way across portals.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new portal team following the documentation can bring a reference portal from “no configuration” to a functional production environment within one working day using only the configuration layer and environment variables.
- **SC-002**: At least 80% of new FairDM portals created after this feature is adopted use the opinionated configuration layer without custom ad hoc configuration structures.
- **SC-003**: Portal maintainers report that they can adjust project-specific settings (including enabling or disabling addons) without editing the baseline configuration code in at least 90% of common scenarios.
- **SC-004**: Configuration-related production incidents (for example, misconfigured backing services or missing secrets) are reduced by at least 50% for portals that adopt the new configuration baseline, compared to historical patterns.
- **SC-005**: Addon authors can document their configuration needs using the shared pattern, and at least one reference addon successfully demonstrates enabling and disabling via the configuration layer without manual file edits beyond the documented entry points.

## Assumptions

- Portal teams are comfortable working with environment variables and simple environment-specific configuration files, even if they do not write application code regularly.
- Most production deployments will use a relational database and a network cache service provided by well-established, production-grade technologies.
- Some portals will deploy in containers and others on managed platforms or virtual machines; the configuration layer must not assume a single hosting model.
- Future changes to the configuration layer will maintain backwards-compatible entry points so that early adopters remain on a stable upgrade path.
