# Feature Specification: Portal configuration via `fairdm.setup()`

**Feature Branch**: `001-fairdm-setup`

**Created**: 2026-01-02 (renamed from `002-production-config-fairdm-conf` on 2026-01-07; rewritten 2026-08-13)

**Status**: Draft

**Serves**: G7 — *Development and production settings stay out of a portal's way while remaining configurable where it matters*. Roadmap item R1.

**Input**: A FairDM portal should obtain its entire Django settings baseline from one call. FairDM
owns a single set of production-grade defaults; every environment is expressed as an override
layered on top of them in a declared order, selected by an environment variable. A portal that is
misconfigured for production must refuse to start rather than degrade quietly, and a developer must
be able to ask the system which layer produced any given setting.

## Clarifications

### Session 2026-08-13 (retrospective audit)

- Q: Which environment profiles does FairDM support? → A: Production and development only. Staging is removed as a shipped profile; `staging` survives only as an environment name a portal may supply its own override file for.
- Q: How is an environment's override file selected? → A: By existence, not by an allowlist. `setup()` looks for a module named after the resolved environment; if there is none, nothing is applied and the baseline stands.
- Q: What happens when `DJANGO_ENV` names an environment nothing ships a file for, including a typo? → A: The production baseline applies unchanged. Falling back to the strictest configuration is the safe direction, and the resulting behaviour is immediately visible to a developer.
- Q: Where does a portal put its own environment overrides? → A: In a module named after the environment, beside the portal's settings module. The recommended project structure places that at `config/<environment>.py`, and the documentation always presents that structure, but the lookup is anchored to the settings module so a portal laid out differently still works.
- Q: Do configuration checks belong to this feature? → A: Yes. The January 2026 decision to stop running them on every start was right about the symptom and wrong about the remedy: they were noise in development, where they have nothing useful to say. Production-critical checks run automatically in production and stop the boot; everything else stays on demand.
- Q: What replaces `validate_services()`? → A: Nothing — it is deleted outright, with its tests and its documented migration path. Its role is covered by the check framework.
- Q: Does the container deployment story belong to this feature? → A: No. It is roadmap R26, which already describes the same gap.
- Q: How much of the addon system does this feature own? → A: Only where addon settings sit in the precedence order and what happens when an addon is broken. What an addon may rely on, how it is discovered and how it is packaged belong to R27.
- Q: Should a portal be able to override a FairDM setting through a `setup()` keyword argument? → A: No. Assignment after the call is the single supported mechanism, so the precedence order has one tail rather than two.
- Q: May the baseline supply a working default for a security-critical value? → A: No. A portal that omits one must fail, not inherit a value published in FairDM's own source.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Obtain a complete settings baseline from one call (Priority: P1)

A portal maintainer creates a settings module, calls `fairdm.setup()`, and has a complete, working
Django configuration — database, cache, background tasks, static and media handling, authentication,
email, logging, security headers and the REST API — without writing or copying any of it.

**Why this priority**: Everything else in this feature is a qualification of this sentence. Without
it there is no configuration layer, only a library of settings a portal has to assemble.

**Independent Test**: A settings module whose entire content is an import and a `setup()` call
produces a Django configuration that passes `manage.py check` and starts a server.

**Acceptance Scenarios**:

1. **Given** a portal whose settings module calls `fairdm.setup()` and nothing else, **when** Django loads settings, **then** every setting FairDM owns is present and no `ImproperlyConfigured` is raised for a value FairDM is responsible for.
2. **Given** the same portal, **when** a maintainer reads `fairdm/conf/settings/`, **then** each module covers one named concern and states in its own docstring what it owns.
3. **Given** a portal that passes `apps=[...]`, **when** Django resolves a template or static file that exists in both the portal and FairDM, **then** the portal's file is served.

---

### User Story 2 - Vary configuration by environment through layered overrides (Priority: P1)

A portal runs the same code in development and in production, and the difference between them is
expressed entirely as override modules layered over a single production baseline, selected by one
environment variable.

**Why this priority**: This is the mechanism the whole feature rests on, and the one most likely to
be got subtly wrong. It has to be a declared order that can be tested, not an emergent one.

**Independent Test**: Setting the environment variable and resolving settings twice, once per
environment, yields two configurations that differ only where the corresponding override module says
they differ.

**Acceptance Scenarios**:

1. **Given** `DJANGO_ENV` is unset, **when** settings resolve, **then** the production baseline applies.
2. **Given** `DJANGO_ENV=development`, **when** settings resolve, **then** FairDM's development overrides apply on top of the baseline and every setting neither the baseline nor that module names is unchanged.
3. **Given** `DJANGO_ENV` names an environment for which neither FairDM nor the portal ships a module, **when** settings resolve, **then** the production baseline applies unchanged and no error is raised.
4. **Given** a portal supplying its own module for the resolved environment, **when** settings resolve, **then** its values win over FairDM's module for the same environment and lose to assignments made after the `setup()` call.
5. **Given** a portal laid out with its settings module somewhere other than `config/`, **when** it places an override module beside that settings module, **then** the override is found.

---

### User Story 3 - A misconfigured production portal refuses to start (Priority: P1)

A maintainer deploying to production learns about missing or unsafe configuration when the portal
fails to start, in one message listing everything that is wrong — not from a runtime failure weeks
later, and not from a quiet fallback to a development-grade service.

**Why this priority**: The baseline claims to be production-safe. Nothing else in this feature makes
that claim true; this story does. It is also the story that closes the two silent degradations the
audit found.

**Independent Test**: Resolving settings in production with a production-critical variable removed
raises a startup error naming every missing item, while the same omission in development is silent.

**Acceptance Scenarios**:

1. **Given** `DJANGO_ENV=production` and no database configuration, **when** the portal starts, **then** it fails with an error naming the missing configuration.
2. **Given** `DJANGO_ENV=production` and several production-critical values missing at once, **when** the portal starts, **then** the error names all of them, not the first.
3. **Given** `DJANGO_ENV=development` with the same values missing, **when** the portal starts, **then** it starts, no configuration check is emitted, and development-grade fallbacks apply.
4. **Given** any environment, **when** a maintainer runs the deployment check on demand, **then** the full check set reports against production standards regardless of the current environment.

---

### User Story 4 - See which layer produced a setting (Priority: P2)

A developer debugging unexpected behaviour asks the portal what its configuration resolved to and
which layer set each value, instead of reading four files and reasoning about precedence.

**Why this priority**: A layered system that silently skips absent files is only safe if it can be
interrogated. This is what makes the layering supportable rather than mysterious, and the
information already exists at the moment `setup()` runs.

**Independent Test**: A command reports the layers considered, which were found, and for a given
setting the layer that last wrote it.

**Acceptance Scenarios**:

1. **Given** any portal, **when** the developer asks for the resolved configuration, **then** every layer is listed in application order and marked found or absent.
2. **Given** a setting written by more than one layer, **when** the developer asks about it, **then** the layer that produced the final value is named.
3. **Given** an environment for which no override module exists, **when** the developer asks for the resolved configuration, **then** the absent layer is reported as absent rather than omitted.

---

### User Story 5 - Override any FairDM default without editing FairDM (Priority: P2)

A portal changes any setting FairDM owns — branding, feature flags, a third-party package's
configuration — through the documented mechanism, and an upgrade to a later FairDM version does not
disturb it.

**Why this priority**: Without this the baseline is a fork magnet. It is P2 rather than P1 only
because the mechanism falls out of the ordering established in User Story 2.

**Independent Test**: A portal overrides a representative setting from each FairDM settings module
and the values survive settings resolution.

**Acceptance Scenarios**:

1. **Given** a portal that assigns a setting after the `setup()` call, **when** settings resolve, **then** the portal's value stands regardless of which FairDM module set it.
2. **Given** a setting FairDM composes from several inputs, **when** a portal overrides it by name, **then** no special-case handling in the entry point is required for it to take effect.

---

### User Story 6 - An addon contributes settings at a defined point (Priority: P3)

An addon named in the `setup()` call contributes its own settings, and a portal can always override
what the addon set.

**Why this priority**: An addon is one of the layers, so leaving it undefined would make the
precedence order incomplete. It is P3 because only its position in the order and its failure
behaviour belong here — the addon contract itself is R27.

**Independent Test**: An addon's settings apply, and a portal override of the same setting wins.

**Acceptance Scenarios**:

1. **Given** a portal naming an addon, **when** settings resolve, **then** the addon's settings apply after FairDM's environment override and before the portal's.
2. **Given** an addon that cannot be loaded, **when** the environment is production, **then** the portal fails to start and names the addon.
3. **Given** the same addon, **when** the environment is not production, **then** a warning is emitted, the addon is skipped, and the portal starts.

---

### Edge Cases

- `DJANGO_ENV` set to an empty string, or to an environment name that differs only in case from a shipped one.
- A portal shipping an override module for an environment FairDM also ships one for, so both layers apply in the same resolution.
- A portal whose settings module is not on disk in the usual way — imported from a zip, or generated — so the anchor for the portal override cannot be resolved.
- A production-critical value present but syntactically unusable, as distinct from absent.
- An addon whose settings module loads but raises partway through, leaving settings half-applied.

## Requirements *(mandatory)*

### Functional Requirements

**The baseline**

- **FR-001**: The platform MUST provide a single public entry point that a portal calls once from its settings module to obtain a complete Django settings baseline.
- **FR-002**: The baseline MUST be organised into modules under `fairdm/conf/settings/`, each covering one named concern and documenting in its own docstring what it owns and what it leaves to a portal. The order in which they are applied MUST be declared and deterministic.
- **FR-003**: Every value in the baseline MUST be the recommended production value. The baseline MUST NOT branch on the resolved environment; environment-varying behaviour belongs in override modules.
- **FR-004**: The baseline MUST NOT supply a working default for any security-critical value, including the secret key, the allowed hosts, the site domain and any administrative password. A portal that omits one MUST fail rather than inherit a value published in FairDM's source.
- **FR-005**: Apps a portal declares in the entry point call MUST be registered so that the portal's templates and static files take precedence over FairDM's when both define the same path.
- **FR-006**: All deployment-varying values MUST be settable from the environment. The entry point MUST document which environment files it reads and in what order, so that a portal can predict where a value came from.

**The layering**

- **FR-007**: The resolved environment MUST be taken from a single environment variable, defaulting to production when it is unset.
- **FR-008**: Settings MUST be applied in this order, later layers overriding earlier ones: the baseline; FairDM's override module for the resolved environment; settings contributed by addons; the portal's override module for the resolved environment; assignments made in the portal's settings module after the entry point call.
- **FR-009**: FairDM MUST ship an override module for development and MUST NOT ship one for any other environment.
- **FR-010**: An override module MUST be selected by existence rather than from a fixed list of permitted environments. When no module exists for a layer, that layer MUST be skipped without error.
- **FR-011**: The portal's override module MUST be resolved beside the portal's settings module, so that the mechanism does not depend on any directory name.
- **FR-012**: Assignment after the entry point call MUST be the only supported mechanism for a portal to override a setting outside its environment module. The entry point MUST NOT accept settings as keyword arguments.

**Refusing to start**

- **FR-013**: When the resolved environment is production, the entry point MUST run the production-critical configuration checks and MUST prevent startup if any fails, reporting every failure in a single error rather than stopping at the first.
- **FR-014**: In any other environment the entry point MUST NOT run configuration checks and MUST emit nothing about them.
- **FR-015**: The full check set MUST remain available on demand through Django's deployment check command, and MUST assess configuration against production standards regardless of the current environment.
- **FR-016**: Configuration checks MUST be implemented as Django system checks with appropriate severity, tagged so that production-critical checks participate in the deployment check run.
- **FR-017**: The production-critical subset MUST cover, at minimum: a production-grade database is configured; a shared cache is configured; the secret key is not a published or otherwise insecure value; allowed hosts are set; debug is off.
- **FR-018**: The platform MUST NOT retain a second configuration-validation path alongside the check framework.

**Interrogating the result**

- **FR-019**: The platform MUST provide a command that reports the layers considered for the current environment, in application order, each marked found or absent.
- **FR-020**: That command MUST report, for a named setting, its resolved value and the layer that produced it.

**Addons**

- **FR-021**: Settings contributed by an addon named in the entry point call MUST be applied at the position given in FR-008, so that a portal can always override an addon.
- **FR-022**: An addon that cannot be loaded MUST prevent startup in production, naming the addon; in any other environment it MUST emit a warning, be skipped, and allow startup to continue.

**Documentation**

- **FR-023**: The configuration contract MUST be documented on a single page covering the entry point, every layer in FR-008, the environment variable, the environment files, the check behaviour and the interrogation command.
- **FR-024**: That documentation MUST present the recommended project structure and use it in every example, while stating that the portal override module is resolved beside the settings module.

### Key Entities

- **Baseline**: FairDM's complete set of production-grade settings, organised by concern, applied to every portal in every environment before anything else.
- **Override module**: A module named after an environment, contributed by FairDM or by a portal, applied over the baseline when the resolved environment matches its name and it exists.
- **Resolved environment**: The name taken from the environment variable, which selects which override modules are looked for. Not an allowlist — any name is valid, and one nothing ships a module for resolves to the baseline.
- **Production-critical check**: A configuration check whose failure means a portal must not start in production, as distinct from a recommendation reported only on demand.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A portal whose settings module contains only the entry point call reaches a running development server with no other configuration written.
- **SC-002**: Resolving settings for production and for development produces configurations that differ only in the settings named by the development override module, verified by a test that compares the two resolutions.
- **SC-003**: Removing any single production-critical value and resolving settings in production fails to start, and the error names every missing or unsafe value in that resolution rather than the first one found.
- **SC-004**: Resolving settings in development with the same values absent starts successfully and emits no configuration-check output.
- **SC-005**: For every setting FairDM sets, the interrogation command names the layer that produced its resolved value.
- **SC-006**: No value shipped in FairDM's source allows a portal to start in production with a publicly-known secret, an unrestricted host list, or debug enabled.
- **SC-007**: A maintainer configuring a new portal for both environments can do so from the single documentation page without reading FairDM's source.

## Out of Scope

- **Container deployment.** A working container stack, its build and its environment file are roadmap R26. This feature says how configuration reaches a portal, not how the portal is shipped.
- **The addon contract.** What an addon may rely on, how it is discovered and how it is packaged are roadmap R27. This feature defines only where an addon's settings sit and what a broken addon does.
- **A staging profile.** FairDM ships no staging override module. A portal that wants one supplies its own, through the same mechanism as any other environment.
- **Adoption and incident-rate outcomes.** The previous version of this spec carried four success criteria measured in adoption percentages and production-incident reductions. Nothing in this repository can observe them.

## Assumptions

- Portal teams are comfortable setting environment variables and editing a small Python module, without necessarily writing application code.
- Production deployments use a relational database and a shared cache service; the development fallbacks exist so that a developer can start without either.
- Portals are deployed by more than one means, so the configuration layer assumes no particular hosting model.
- The entry point's signature stays backwards-compatible for portals already calling it, except where this specification removes an argument deliberately.
