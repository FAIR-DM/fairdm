# Roadmap — FairDM

**Date:** 2026-08-12

This document was designed against [GOALS.md](../GOALS.md). See also [CONTEXT.md](../CONTEXT.md) for domain terminology and [memory/constitution.md](../memory/constitution.md) for project standards.

The first thirteen items are already built. They are carried here so the sequence reads whole, from an empty repository to where the framework stands today.

## Versioning

Releases are gated on how important a goal is, not on how many features have landed.

| Version | What it means |
|---------|---------------|
| `0.0.x` | Building toward the Essential goals. Pre-viable, expect churn, install from a git pin rather than an index. |
| `0.1.0` | Every Essential goal delivered. The minimum usable release and the first publish. |
| `0.1.x` → `0.x` | The Expected goals, at whatever granularity the work takes. Patch releases are fixes. |
| `1.0.0` | Every Expected goal delivered. The complete, dependable release. |
| `1.x` | Stable line. Fixes and additive features only. |
| `2.0` | The next major, where breaking changes go. |

Two rules follow from that table. A goal is not one minor release: some take several, and one release can move two goals at once. Once `1.0` ships, a breaking change never goes out on the `1.x` line and waits for the next major instead.

Aspirational goals may be developed against v2 or v1 as required.

## Already delivered

The framework these items describe is working code. Each one is carried at the version it was built at, and each carries a verification tag until a later pass confirms the code meets the goal it claims.

### R1 — Portal configuration in a single call

*Delivered · advances G7*

A portal declares its apps and addons in one call and receives a complete settings baseline. The baseline is production-grade in every environment, and each environment is an override layered over it in a declared order, selected by name and found by whether it exists. FairDM ships an override for development only, and a portal supplies its own for anything else. In production, configuration that would leave the portal unsafe stops it starting rather than surfacing as a runtime failure.

Serves G7.

### R2 — Model registry and generated components

*Delivered · advances G2*

Registering a model with a configuration class produces its form, table, filter set, serializer, import and export resource, and admin entry without any of those being written by hand. A portal author describes fields and grouping, and the components follow.

Serves G2.

### R3 — Projects

*Delivered · advances G1*

The outermost container of the core model, with descriptions, dates, identifiers, funding, status and keywords, and a fixed schema that portals consume rather than extend.

Serves G1.

### R4 — Datasets

*Delivered · advances G1*

The unit of citation and distribution, carrying its own descriptions, dates, identifiers, licence, keywords and related literature, with visibility held independently of its project.

Serves G1.

### R5 — Samples

*Delivered · advances G1*

The polymorphic base every sample type inherits from, so a portal defines its own specimen types and the framework treats them uniformly.

Serves G1.

### R6 — Measurements

*Delivered · advances G1*

The polymorphic base for results and observations recorded against a sample, including the case where a measurement belongs to a different dataset than the sample it describes.

Serves G1.

### R7 — The default portal interface

*Delivered · needs verification · advances G5*

Every page a portal serves inherits a shared application shell with navigation, menus, icons and component templates already in place, so a new portal has a working interface before anyone writes a template.

Serves G5.

### R8 — The plugin system

*Delivered · advances G3*

Views attach to core records as tabs and panels through a registry, so an addon adds pages to an existing record type without the framework being edited. Addon packages announce their own settings and URLs and are picked up at startup.

Serves G3.

### R9 — Contributors and contributions

*Delivered · needs verification · advances G4*

People and organisations are one polymorphic family, credited against records through contribution entries that carry roles drawn from a controlled vocabulary. A person is also the portal account, so credit and identity are the same record.

Serves G4.

### R10 — Profile claiming

*Delivered · needs verification · advances G4, G15*

A person credited on a record before they ever visited the portal can take ownership of that profile by signing in with an external identity, instead of a duplicate account being created alongside the credit.

Serves G4 and G15.

### R11 — The machine-readable API

*Delivered · needs verification · advances G10*

Projects, datasets, contributors and every registered sample and measurement type are reachable over a versioned HTTP API with authentication, pagination, filtering, ordering and generated interactive documentation.

Serves G10.

### R12 — Editing projects and datasets in the portal

*Delivered · needs verification · advances G6*

Projects and datasets can be created, read, updated and deleted through the portal itself, without the Django admin and without a portal author writing those views.

The project half is verified: a project can be listed, created, edited — its own fields, its dates and its identifiers together, its descriptions on their own page — and deleted, each page reachable from the project itself and refused to anyone who may not open it. The dataset half is not yet verified, so the tag stands.

Serves G6.

### R13 — Identifier synchronisation

*Delivered · needs verification · advances G15*

An ORCID or ROR identifier recorded against a person or organisation is resolved against the issuing registry in the background, so the local record is populated from the authoritative source rather than retyped.

Serves G15.

## Essential goals: v0.1.0

Everything needed to reach a minimum usable release.

### R14 — Access rules hold on every surface

*feature · advances G8, G12*

Visibility is decided per record and is enforced in some places and not others. A private dataset is readable by anyone who has its address, and the collection tables that list samples and measurements across the portal show rows belonging to private datasets. Until one rule governs every surface, no portal can hold embargoed data, and every capability built on top of visibility inherits the same hole. This comes first because it is the only item on the roadmap whose absence loses a research group its data.

**Deliverables:**

- One access rule per record type, applied by every page, table, feed and API endpoint that can return that record.
- Sample and measurement access derived from the dataset they belong to, consistently across the portal and the API.
- Non-disclosure on refusal, so an address does not confirm that a private record exists.
- A regression test per surface that a private record is not returned to a viewer without rights to it.
- The documentation for portal administrators states what private means and where it applies.

Serves G8 and G12. Out of scope: roles and their default permissions, which are R15.

### R15 — Portal roles ship with the framework

*feature · advances G8*

Running a portal is currently a bespoke setup. No roles or default permissions ship, so an administrator has to invent them, and someone who creates a dataset through the portal is not granted anything over it and cannot edit it afterwards. The framework should arrive with the roles a research portal actually needs and grant them at the moments that matter.

**Deliverables:**

- A defined set of portal roles with the permissions each one holds, installed with the framework rather than assembled per portal.
- Creating a record grants its creator the rights to manage it.
- Project and dataset membership grants rights over the records beneath it.
- Administrators can assign and revoke roles through the portal.
- Documentation for administrators listing each role and what it can do.

Serves G8. Out of scope: enforcement of visibility, which is R14.

### R16 — Every core record type can be created and edited in the portal

*multi-feature · advances G6, G2*

Registering a sample or measurement type produces its components but not its pages. Samples have no create, list or delete pages at all, and a measurement has only a placeholder. A portal author who registers a domain model still cannot let a researcher enter data through the portal, which leaves the Django admin as the only route and defeats the point of registration.

**Deliverables:**

- Every registered sample and measurement type gets list, detail, create, edit and delete pages from its registration alone.
- Those pages are reachable from the record they belong to, so a dataset leads to its samples and a sample to its measurements.
- Creating a measurement carries its sample and dataset context rather than asking the user to restate it.
- Access rules from R14 and R15 apply to the generated pages.
- The developer documentation shows what registration produces and how a portal overrides one page without taking over the rest.

Serves G6 and G2. Out of scope: bulk entry through file import, which is R21.

### R17 — Records can be found, sorted and filtered

*feature · advances G9*

Filtering is generated from a registered model and works. Search is not: it matches a typed phrase against a handful of fields as plain substrings, with no ranking and no index behind it, so it degrades as soon as a portal holds real data. Sorting is inconsistent between one list and the next. A portal whose records cannot be found is a portal nobody uses, and this becomes visible the moment R16 gives every registered type a list of its own.

**Deliverables:**

- Search across the core record types that tolerates partial words and returns the closest matches first.
- Sorting on every list, on the columns a reader would expect to sort by.
- Filters generated from a registered model's own fields, on its own list pages.
- Indexes that keep search and filtering usable as a portal grows, with a stated expectation of what "usable" means.
- The same search, sort and filter available through the API.
- Only records the viewer may see are returned, under the rule from R14.

Serves G9. Out of scope: searching across portals, which is R29.

### R18 — Plugins attach to any registered model

*feature · advances G3*

Extension points are fixed in advance rather than derived from what is registered, so a model a portal or an addon defines has nowhere to attach. A record type gains plugin pages only when someone edits a URL configuration by hand, which an addon cannot do.

Measurements were previously named here as the live example. That was wrong: a measurement is a component of the sample page rather than a record with a page of its own, so it has no attachment point by design. The five plugins registered against it have been removed, and registering a plugin incorrectly now fails at registration rather than doing nothing.

**Deliverables:**

- Attachment points follow from a model being registered, including models defined by a portal or an addon.
- A startup report lists every registered plugin and where it attached, so an addon author can see the result. A registration against a record with no mounted attachment point is reported as such — this cannot be caught at registration, because no URL configuration exists when the decorator runs.

Serves G3. Out of scope: removing the code that this defect left stranded, which is R20.

### R19 — Contributions can be managed on every core record

*feature · advances G4*

A contribution can be recorded against any record in the core model, but the pages for adding, editing and removing contributions exist only on projects. Datasets, samples and measurements can be credited in principle and not in practice, and a dataset is the unit that gets cited, so this is the gap that matters most.

**Deliverables:**

- Contribution management on projects, datasets, samples and measurements alike.
- Roles offered per record type, drawn from the vocabulary appropriate to that type.
- Ordering of contributors on a record is under the research team's control, because it determines how the record is cited.
- Editing and removing an existing contribution, not only adding one.
- Access rules from R14 and R15 govern who may change credit on a record.

Serves G4. Out of scope: sending credit to an external publisher, which belongs to a publication addon.

### R20 — Retire the code that never runs

*feature · advances G3, G18*

Several modules are shipped but unreachable: the import and export views, the geographic location helpers that import modules which do not exist, a second component-generation system that nothing calls, a second declarative configuration system with one remaining consumer, and a data manager whose surrounding documentation still describes it as active. Their presence is worse than their absence, because each one reads as a working feature to anyone extending the framework, and one of them has already misled its own tests. The core cannot stay small while it carries a second version of itself.

**Deliverables:**

- Each unreachable module is either wired up and covered by tests or deleted.
- One component-generation path and one configuration path remain, with the alternatives gone.
- Documentation and docstrings that describe removed or inert behaviour are corrected in the same change.
- Nothing in the package imports a module that does not exist.
- Anything deferred rather than removed is recorded as an issue with a reason.

Serves G3 and G18. Out of scope: the import and export feature itself, which is R21 and decides whether those views are worth wiring or replacing.

## Expected goals: v1.0.0

The capabilities a complete, dependable version of the framework is expected to have.

### R21 — Tabular data goes in and comes back out

*multi-feature · advances G11*

Import and export is written but nobody can reach it. The pages are not routed, one of the templates does not exist, and the work runs in the request rather than in the background. A research group's existing data arrives as spreadsheets, so this is the capability that decides whether a portal can be populated at all.

**Deliverables:**

- Import and export are reachable from the dataset they belong to.
- An exported file re-imports into the same dataset and produces the same records.
- Large imports run in the background and report progress and failures per row.
- A dataset exports as one archive covering its samples, measurements and metadata.
- Import validates before it writes, and reports what it would reject.

Serves G11. Out of scope: import across several related tables in one pass, which follows once single-table import is dependable.

### R22 — A dataset moves from working to visible through a checked process

*feature · advances G13*

Visibility is a switch anyone with rights can flip. There is no point at which a dataset is checked for completeness before the rest of the portal sees it, which is what a portal administrator is being asked to guarantee.

**Deliverables:**

- Defined states for a dataset from working through review to visible, with the transitions between them.
- Completeness requirements checked at the transition, reported as what is missing.
- A review step that a nominated role performs, with the outcome recorded against the dataset.
- The dataset's history of state changes is visible to the people responsible for it.

Serves G13. Out of scope: submitting to an external publisher, which belongs to an addon.

### R23 — Datasets carry versions

*multi-feature · advances G19*

A dataset that has been cited keeps changing, and nothing records what it looked like when the citation was made. Comparable repositories treat a version as the thing that gets cited, so a reader can retrieve the exact state a paper referred to. Without it, a citation to a dataset stops referring to anything specific.

**Deliverables:**

- A published dataset that changes produces a new version rather than overwriting the old one.
- Earlier versions stay retrievable and are marked as superseded.
- A dataset's version history is visible on the record, with what changed between versions.
- Citation of a dataset resolves to a specific version.
- Versions are reachable through the API alongside the current state.

Serves G19. Out of scope: minting a separate identifier per version with an external agency, which belongs to a publication addon.

### R24 — Dataset metadata is complete enough to hand to a publisher

*feature · advances G14*

The record model carries most of what a publisher needs, but the publication-shaped output of a dataset refers to fields the dataset does not have and omits the identifier entirely, so it renders mostly empty. An addon that submits a dataset for formal publication cannot work until the metadata a dataset exposes is both complete and correct.

**Deliverables:**

- A published dataset exposes its metadata in the shape a publisher expects, with every required element populated from real fields.
- Missing required metadata is reported against the dataset before it reaches an addon.
- The mapping is covered by tests that fail when a field is renamed or removed.
- The developer documentation states what an addon can rely on.

Serves G14. Out of scope: minting identifiers or talking to a registration agency.

### R25 — Records are machine-readable where machines look

*feature · advances G10*

The API is the deliberate machine route, but discovery services do not use it. Comparable repositories publish structured metadata in the page itself and offer a listing that a crawler can walk. Without those, a portal's records stay invisible to dataset search engines however good its API is, and findable is the first thing FAIR asks for.

**Deliverables:**

- Structured metadata embedded in project, dataset, sample and measurement pages in the format dataset search engines consume.
- A crawlable listing of the portal's public records.
- Only public records appear in either, under the rule from R14.
- The documentation for administrators explains what is exposed and how to verify it.

Serves G10. Out of scope: harvesting protocols for portal-to-portal exchange, which is R29.

### R26 — A research group can deploy the shipped stack

*feature · advances G16*

The deployment story does not run. The container stack builds from a directory that is not in the repository, points at an environment file that is not there, and the production configuration described in the documentation does not exist. A group with no operations staff has nothing to follow.

**Deliverables:**

- A container stack in the repository that builds and runs as documented.
- A production configuration covering the web, database, cache, background worker and storage services.
- Backups, upgrades and log access documented as routine operations.
- A first-run path from empty to a portal with an administrator account.
- The deployment documentation matches what the repository ships, verified by following it.

Serves G16. Out of scope: hosting choices and managed services, which are the deploying group's decision.

### R27 — Installing a schema package is all a portal needs

*feature · advances G17, G18*

A community can package a domain schema today, but the receiving portal has to name it in configuration for anything to happen, and the contract an addon is written against is described in prose rather than checked. Adoption across communities depends on installation being uneventful.

**Deliverables:**

- An installed schema package is discovered without the portal listing it by hand.
- A stated contract for what an addon may rely on, with a startup check that reports violations.
- A reference schema package, kept working by the framework's own tests.
- Documentation covering authoring, publishing and installing a schema package.

Serves G17 and G18. Out of scope: a registry or index of published schemas.

### R28 — Identifiers stay meaningful

*resolve · advances G15*

Identifiers are recorded against people and organisations and resolved for two schemes. Samples and datasets accept identifiers with no validation, so a mistyped one is stored as readily as a real one, and nothing distinguishes them later.

**Deliverables:**

- Identifiers are validated against their scheme when entered, in the portal and the API.
- Sample and dataset identifiers resolve to their registry from the record page.
- An invalid or unresolvable identifier is reported to the person who entered it.

Serves G15. Out of scope: minting new identifiers, which requires an agreement with an issuing agency.

## Aspirational goals: v2.0

Genuine wants whose absence never makes the framework incomplete.

### R29 — Portals exchange data with one another

*multi-feature · advances G20*

One portal can find and reuse records held by another, through the harvesting protocols the research data community already runs, rather than by manual export and re-import.

Serves G20.

### R30 — A portal supports its research community

*multi-feature · advances G21*

Discussion, news and collaboration around the data, so a portal is somewhere a research community works rather than only a place its data is stored.

Serves G21.

### R31 — Contributors work in their own language

*feature · advances G22*

Translation is prepared for throughout the framework and no translation exists: there are no message catalogues, the configured translation path points at a directory that is not there, and there is no way for a visitor to change language. Regional conventions for dates and numbers follow the same gap.

Serves G22.
