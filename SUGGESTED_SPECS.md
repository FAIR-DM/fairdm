# Suggested FairDM Feature Specifications

This file lists candidate feature specs to bootstrap the Speckit-driven workflow for FairDM. Each item is a proposed **feature specification** that can be turned into a dedicated `specs/[###-feature-name]/` tree.

Priorities:

- **P1** – Should be tackled early to stabilise the framework and support production portals.
- **P2** – Important but can follow once P1 items are underway.
- **P3** – Nice-to-have or longer-term.

---

## P1 – Documentation & Onboarding

### SPEC-001: FairDM Documentation Baseline

**Goal**: Establish a coherent documentation baseline aligned with the constitution, covering portal admins, contributors, and developers.

**Scope**:

- Clarify the high-level vision, FAIR-first philosophy, and core architecture (linking to the constitution).
- Ensure the four major doc sections (portal-administration, user-guide, portal-development, contributing) are discoverable, up to date, and cross-linked.
- Provide a minimal but complete “Getting Started” flow for:
  - Spinning up the demo portal (Docker / local dev).
  - Creating a first custom Sample/Measurement model.
  - Registering it and seeing it in the UI/API.

**Why now**: Documentation is essential for future contributors and for stabilising expectations before deep API changes.

---

## P1 – Production Configuration & Setup

### SPEC-002: Production-Ready Django Configuration via `fairdm.conf`

**Goal**: Deliver a clear, opinionated production configuration story using the `fairdm.conf` package.

**Scope**:

- Define the intended responsibilities and boundaries of `fairdm.conf` (settings, URLs, environment handling, celery, static/media config, etc.).
- Provide a documented pattern for projects to extend/override core settings safely (e.g., `dev_overrides.py`, local settings, env vars).
- Make sure the configuration supports:
  - PostgreSQL + Redis as first-class production targets.
  - Container-based deployment (Docker/Docker Compose) with environment-driven settings.
  - Pluggable addons without brittle settings coupling.

**Why now**: A stable, production-ready configuration baseline is critical for existing and future portals to rely on FairDM with confidence.

### SPEC-003: `fairdm.setup` Command & Project Scaffolding

**Goal**: Provide a robust `fairdm.setup` (or equivalent management command/CLI) that scaffolds a new FairDM-based portal with best-practice defaults.

**Scope**:

- Define the UX for creating a new portal (questions asked, defaults, optional flags).
- Generate a project layout wired to `fairdm.conf`, including:
  - Settings module referencing FairDM defaults.
  - URL configuration that plugs in core FairDM URLs.
  - Example Sample/Measurement app skeleton.
- Ensure generated projects:
  - Are 12-factor friendly (env-based secrets, no hard-coded credentials).
  - Ship with basic Docker/Docker Compose configuration.
  - Include pointers to docs and the constitution.

**Why now**: A good setup experience is a key adoption lever and ensures early portals share consistent, supportable structure.

---

## P1 – Sample / Measurement Registration

### SPEC-004: Stabilise Sample & Measurement Registration System

**Goal**: Define and stabilise the contract for registering Sample/Measurement models via `fairdm.registry`.

**Scope**:

- Document and, if necessary, refine the public API of the registry (`register`, `SampleConfig`, `MeasurementConfig`, metadata classes, factories).
- Clearly specify what the registry auto-generates:
  - Forms, tables, filters, serializers.
  - Import/export resources.
  - Minimal admin integration.
- Define how users override behaviour (custom forms/tables/serializers, custom views) without forking core code.
- Ensure the registration system is robustly tested and versioned, with clear migration guidance if signatures change.

**Why now**: This is the heart of domain modeling in FairDM; stabilising it early prevents churn for all downstream portals.

---

## P1 – Plugin System

### SPEC-005: Stabilise Pluggable Detail View & Plugin Registry

**Goal**: Finalise the plugin architecture around `fairdm.plugins` and the pluggable detail views for core models.

**Scope**:

- Define the contract for `FairDMPlugin`, `PluginConfig`, `PluginMenuItem`, and `plugins.register`.
- Clarify supported plugin categories (EXPLORE, ACTIONS, MANAGEMENT) and how they map to menus and URLs.
- Specify how plugins declare:
  - Target models.
  - Permissions checks.
  - Menu entries and icons.
  - Templates and media.
- Provide guidance and examples (e.g., fairdm-discussions-style addon) as canonical patterns.
- Ensure the system degrades gracefully if no plugins are installed.

**Why now**: Plugins are the primary extension mechanism for advanced features; getting this right avoids fragmentation and brittle customizations.

---

## P2 – FAIR Metadata, Privacy & Access Control

### SPEC-006: FAIR Metadata Baseline & Validation

**Goal**: Codify the minimum FAIR metadata set required at each core level (Project, Dataset, Sample, Measurement, Contributor, Organization) and how it is enforced.

**Scope**:

- Enumerate required vs recommended fields per entity.
- Define validation rules and UX patterns for missing or incomplete FAIR-critical metadata.
- Specify machine-readable exports (e.g., JSON, JSON-LD, DataCite-like structures) derived from these fields.

**Why now**: Aligns implementation with the constitution’s “FAIR as non-negotiable” stance and gives portal developers clear targets.

### SPEC-007: Privacy & Access Control Baseline

**Goal**: Provide a clear, opinionated baseline for handling sensitive research data in FairDM portals.

**Scope**:

- Describe how object-level permissions (e.g., via django-guardian) integrate with the core models.
- Define roles (viewer, editor, manager) and their default permissions, including for plugins.
- Clarify how public vs restricted datasets are represented in the model and UI.

**Why now**: Many research datasets are sensitive; a clear story on privacy is critical for adoption.

---

## P2 – Admin & Import/Export

### SPEC-008: Admin Experience & Core Data Management

**Goal**: Provide a consistent, usable admin experience for managing core entities.

**Scope**:

- Define minimal `ModelAdmin` patterns for core models and registry-registered models.
- Clarify when and how custom admin configuration is recommended.

**Why now**: Admin is the main control surface for many portals; it must be coherent and predictable.

### SPEC-009: Import/Export Framework Integration

**Goal**: Standardise how FairDM portals perform CSV/Excel/JSON imports and exports for core and registered models.

**Scope**:

- Decide on, and document, the preferred package(s) (e.g., django-import-export or a custom lightweight layer).
- Define default import/export resources for registered models and how to override them.

**Why now**: Data onboarding and bulk operations are central to real-world usage.

---

## P2 – API & Programmatic Access

### SPEC-010: Standardised REST API for Core & Registered Models

**Goal**: Establish a consistent REST API surface for the core data model and registry-registered Sample/Measurement models.

**Scope**:

- Define DRF viewsets/routers conventions and URL patterns.
- Clarify authentication/authorization behaviour for API endpoints.
- Ensure FAIR metadata is exposed and searchable.

**Why now**: APIs are critical for interoperability and automation across systems.

---

## P3 – Frontend UX & Theming

### SPEC-011: Core UI Patterns & Theming

**Goal**: Define the core UI patterns and theming model for FairDM-powered portals.

**Scope**:

- Document canonical list/detail views, navigation patterns, and Bootstrap 5/Cotton components.
- Clarify how portals can override templates while remaining on the upgrade path.

**Why later**: Important, but can evolve after core registration, plugins, and configuration are stable.

---

## P3 – Addon Ecosystem

### SPEC-012: Addon Guidelines & Reference Addons

**Goal**: Provide guidance and examples for building addons (e.g., fairdm-discussions) that integrate cleanly with the core.

**Scope**:

- Define what qualifies as an addon vs core feature.
- Document best practices for URL namespaces, settings, migrations, and UI integration.
- Use one or two reference addons as worked examples.

**Why later**: Depends on having a stable core plugin and registry story in place.
