# FairDM Framework Specifications

This document contains feature specifications for the FairDM framework. Specifications are ordered by implementation priority: critical foundational specs first (those that affect others), followed by specifications for core built-in functionality, then workflow and governance specs, and finally additional enhancement specs.

**Status Key:**

- ✅ **Implemented** - Feature is complete and in production
- 🔄 **In Progress** - Currently being implemented
- 📋 **Planned** - Specified and ready for implementation
- 💡 **Proposed** - Idea stage, requires further analysis

---

## ✅ Critical Foundation (Implemented)

### FS-001 - Documentation Infrastructure & Conventions

**Status:** ✅ Implemented (spec-001)
**Test Coverage:** ~40% | **Documentation:** ~95%

Define how documentation is authored, validated, and kept synchronized with governance and feature implementations. Establish the documentation information architecture distinguishing user guides, developer documentation, and governance materials. Define cross-linking strategies between governance documents and technical documentation. Establish a feature documentation checklist specifying what documentation must be updated when features ship. Define how specifications are referenced from documentation to enable traceability. Establish validation criteria including build processes, link checking, failure conditions, and minimum quality expectations. Ensure contributors can locate appropriate documentation locations, follow consistent checklists when shipping features, and execute repeatable documentation validation.

### FS-002 - Testing Infrastructure & Conventions

**Status:** 🔄 In Progress (spec-002)
**Test Coverage:** ~30% | **Documentation:** ~60%

Define the testing strategy, test organization layers, and foundational test fixtures supporting feature validation. Establish test layer taxonomy (unit, integration, contract) and their organizational structure. Define naming conventions for test files and test functions. Establish minimal fixture datasets covering common workflows including data import, review submission, administrative approval, and export operations. Define testing patterns for schema mapping validation and round-trip data integrity. Ensure feature specifications can reference standard test layers and fixture locations unambiguously, minimal happy-path integration tests exist covering end-to-end workflows, and testing conventions provide clear guidance on test naming, organization, and required assertions.

### FS-003 - CI/CD Pipeline & Automation

**Status:** 💡 Proposed
**Test Coverage:** N/A | **Documentation:** ~20%

Define continuous integration and deployment automation including pull request checks, main branch integration, and scheduled or on-demand operations. Establish test execution strategies determining which test suites run in different contexts. Define coverage collection and reporting expectations. Establish build and deployment automation sequences. Define environment-specific configurations for different deployment targets. Establish failure notification and handling procedures. Ensure contributors understand what automated checks will run on their contributions, CI failures provide actionable diagnostic information, and deployment to staging and production environments follows documented, auditable procedures.

### FS-004 - Production Configuration System (fairdm.conf)

**Status:** 🔄 In Progress (spec-003)
**Test Coverage:** ~20% | **Documentation:** ~50%

Define production-ready configuration system using fairdm.conf package. Establish responsibilities and boundaries of configuration layer. Provide patterns for safe settings overrides distinguishing production baseline from environment-specific profiles (development, staging). Support PostgreSQL, Redis, container-based deployment, and pluggable addons without brittle coupling. Define fail-fast behavior for missing required services in production/staging with graceful degradation in development. Ensure portal teams can deploy production-ready instances following clear configuration patterns and customize project-specific settings without diverging from upgradeable baseline.

### FS-005 - Sample & Measurement Registration System

**Status:** 🔄 In Progress (spec-004)
**Test Coverage:** ~70% | **Documentation:** ~75%

Define the core registry system enabling researchers to register custom Sample and Measurement models through configuration rather than code. Establish registration API accepting model classes with ModelConfiguration objects specifying list_fields, detail_fields, filter_fields, and metadata. Define auto-generation behavior for Forms, Tables, FilterSets, Serializers, and Import/Export resources when custom implementations not provided. Specify discovery API for retrieving registered models programmatically. Establish validation requirements ensuring registered models inherit from polymorphic base classes. Ensure researchers with basic Python skills can register domain-specific models and have fully functional portal interfaces (list, detail, create, edit, delete) without writing views or templates.

---

## ✅ Core Built-In Functionality (Implemented)

### FS-006 - Core Data Model (Project, Dataset, Sample, Measurement)

**Status:** ✅ Implemented (built-in)
**Test Coverage:** ~80% | **Documentation:** ~85%

Define the four-level hierarchical data model foundational to all FairDM portals. Establish Project as top-level organizational container with collaborator, funding, and metadata support. Define Dataset as DataCite-aligned publication unit with literature references and access control. Specify Sample as polymorphic base supporting IGSN identifiers, spatial data, and hierarchical relationships. Define Measurement as polymorphic observation base linking to samples with extensible schema support. Ensure all models include standard metadata fields (contributors, descriptions, dates, identifiers), generic relations for flexible associations, and object-level permission integration. Establish clear parent-child relationships (Project → Dataset → Sample → Measurement) with cascade behaviors.

### FS-007 - Plugin System

**Status:** ✅ Implemented (built-in)
**Test Coverage:** ~55% | **Documentation:** ~70%

Define plugin system allowing extensions to register custom panels, actions, and functionality for core models without modifying framework code. Establish plugin registration API with decorators linking plugins to specific model classes. Specify plugin configuration including category (explore, actions, management), permissions, icons, and URL patterns. Define plugin view base classes providing consistent context and permission checking. Support plugin discovery allowing dynamic extension of detail views with custom tabs and functionality. Ensure plugins can access model instances, request context, and user permissions while maintaining security boundaries and consistent UI patterns.

### FS-008 - Contributors & Identity Management

**Status:** ✅ Implemented (built-in)
**Test Coverage:** ~75% | **Documentation:** ~80%

Define contributor system supporting both Person (individual researchers) and Organization entities with polymorphic Contributor base. Establish identity integration with ORCID for persons and ROR for organizations including API data fetching and profile synchronization. Define Contribution model as ordered, role-based linkage between contributors and content objects (projects, datasets, samples, measurements) using CRediT taxonomy. Specify automatic permission management where contributions grant object-level access and removal cleans up permissions. Support organization membership, affiliation hierarchies, and multi-language profiles. Ensure contributors can be imported from external identifiers (ORCID, ROR), roles track specific contributions (conceptualization, data curation, investigation), and contributor profiles include persistent identifiers for FAIR compliance.

### FS-009 - Authentication & Object-Level Permissions

**Status:** ✅ Implemented (built-in)
**Test Coverage:** ~85% | **Documentation:** ~90%

Define authentication system integrating django-allauth for social auth, email verification, and account management with django-guardian for object-level permissions. Establish authentication backends supporting ModelBackend, allauth, and ObjectPermissionBackend. Define group-based roles (Portal Admin, Database Admin, Site Content, Literature Manager, Reviewer) with distinct permission scopes. Specify object-level permission patterns for Project, Dataset, Sample, and Measurement models including view, change, delete, add_contributor, modify_contributor, modify_metadata, and import permissions. Establish permission inheritance where project/dataset contributors automatically receive object permissions. Ensure permission checks enforce visibility restrictions (private, restricted, public), superusers bypass all checks, and permission grants/revocations trigger proper cleanup and audit trails.

### FS-010 - Spatial Data & Location Management

**Status:** ✅ Implemented (built-in)
**Test Coverage:** ~65% | **Documentation:** ~60%

Define spatial data support using GeoDjango and PostGIS for point-based sample locations. Establish Point model with geometry fields, elevation, coordinate system tracking, and methods. Specify GeoJSON serialization for API endpoints with spatial filtering and distance-based queries. Define integration with Sample model through generic foreign key allowing any sample type to associate with point locations. Support bounding box calculations for datasets, spatial indexing for performance, and map-based visualizations. Ensure spatial queries support distance filters, geographic aggregations, and proper coordinate reference system handling with SRID 4326 (WGS84) as standard.

### FS-011 - Import/Export Framework

**Status:** ✅ Implemented (built-in)
**Test Coverage:** ~70% | **Documentation:** ~70%

Define import/export system using django-import-export for bulk data operations. Establish Resource classes for Sample and Measurement models with field mappings, validation, and transformation logic. Specify CSV, Excel, and JSON format support with configurable column mapping. Define validation reporting showing row-level errors with field-specific messages. Support dry-run preview mode allowing validation without persistence. Establish natural key resolution for foreign key relationships (e.g., sample_id instead of database ID). Ensure import operations provide detailed feedback on successes and failures, export includes all configured fields with proper formatting, and large datasets handle efficiently through chunking and streaming.

### FS-012 - Activity Stream & Audit Logging

**Status:** ✅ Implemented (built-in)
**Test Coverage:** ~60% | **Documentation:** ~65%

Define activity tracking system using django-activity-stream for user actions and content changes. Establish automatic activity recording for create, update, delete, and publish actions on core models (Project, Dataset, Sample, Measurement, Person, Organization). Specify Action model storing actor, verb, action_object, target, and timestamp with generic foreign keys for flexible associations. Define activity stream views providing chronological feeds of actions filtered by actor, object, or verb. Support follow/unfollow functionality allowing users to track specific objects or other users. Ensure activity records are immutable, queryable by multiple dimensions (who did what to which object when), and displayable in user-friendly format with natural language timestamps and icon representations.

---

## 📋 Workflow & Governance (Planned)

### FS-013 - Role Hierarchy & Permission Matrix

**Status:** 📋 Planned

Define roles and permissions ensuring review and curation capabilities do not confer publication or approval authority. Restrict publication approval to designated administrative roles with tightly controlled assignment. Define the minimal role set and permission matrix mapping roles to capabilities. Establish who can grant or revoke role assignments. Define testable authorization rules and audit requirements. Ensure for each protected action the specification defines required permissions and denial behavior, and includes concrete authorization scenarios covering reviewer and administrator boundaries.

### FS-014 - Curation Review Workflow

**Status:** 📋 Planned

Define the scientific review workflow where domain experts curate and assess datasets for accuracy and completeness. Establish workflow states including submission, active review, revision requests, and approval for publication consideration. Define state transitions and authorized actors including reviewers and dataset contributors. Specify artifacts produced at each stage including review comments, quality assessments, and metadata corrections. Establish rejection and revision iteration patterns. Ensure every workflow transition has clearly defined triggering actions, required permissions, inputs, outputs, and audit events, and the workflow enforces that curation review completion is prerequisite to publication approval.

### FS-015 - Publication Approval Workflow

**Status:** 📋 Planned

Define the administrative publication approval workflow controlling dataset transition from private to public visibility. Establish workflow states including pending approval, change requests, approval, publication, and rejection. Define state transitions restricted to administrative roles. Specify required administrative checks including provenance verification, metadata quality assessment, and export validation. Define the final publication action making data publicly accessible. Ensure publication approval is strictly separated from curation review permissions, every approval action is audited with timestamp and rationale, and rejected datasets can be returned to curation with specific feedback.

### FS-016 - Provenance & Attribution Model

**Status:** 📋 Planned

Define canonical data structures and attribution rules for publication metadata, scientific authors, portal users, and editorial approvers. Establish entity relationships for DOI and citation metadata, original scientific authors, portal users (reviewers and curators), and editorial approvers with action timestamps. Define attribution rules for data exports and public display. Establish audit and event requirements for editorial actions. Ensure given a dataset, the system can unambiguously identify original authors, curators, and editorial approvers, and provenance fields required at publication time are explicitly enumerated.

### FS-017 - Review Submission Package Requirements

**Status:** 📋 Planned

Define submission completeness requirements when reviewers submit datasets for publication approval consideration. Establish minimum provenance requirements including scientific authors, DOI, and citation information. Define required metadata fields including abstract, methods, and quality assessments. Establish data completeness requirements including minimum measurements, coordinates, and mandatory fields. Define validation rules executed at submission time. Ensure required fields and artifacts are explicitly enumerated with validation rules, incomplete submissions are blocked with actionable error messages, and test coverage addresses missing or invalid submission elements.

### FS-018 - Publication Pipeline & Release Process

**Status:** 📋 Planned

Define the publication process and artifacts for transitioning approved datasets to public visibility. Establish the publication trigger action and required preconditions. Define artifacts produced including public export files and metadata records. Establish automated process steps including export generation, file distribution, and index updates. Define any manual steps and responsible actors. Establish rollback strategies for publication failures. Ensure the publication pipeline is fully enumerated with clear responsibilities, publication operations are atomic (all steps succeed or all roll back), and every publication action is audited.

### FS-019 - Publish-Time Completeness Gates

**Status:** 📋 Planned

Define completeness requirements that must be satisfied before publication approval. Establish provenance completeness requirements. Define minimum metadata requirements including abstract, license, and contributor information. Establish identifier requirements for DOI, ORCID, and ROR where available. Ensure required fields and artifacts are explicitly enumerated with validation rules, and validation failures are categorized into actionable error categories.

### FS-020 - Post-Publication Immutability & Amendment Workflow

**Status:** 📋 Planned

Define what data becomes immutable after publication and how corrections or new versions are managed. Establish immutability boundaries specifying which fields or objects become locked. Define amendment and versioning models distinguishing new versions from patches and tracking lineage. Establish how DOI and public artifacts are updated or superseded. Ensure the specification defines clear rules preventing silent post-publication mutations, and defines an auditable amendment workflow.

### FS-021 - Audit Trail for Editorial Actions

**Status:** 📋 Planned

Define event logging requirements for administrative and editorial actions including approvals, rejections, revision requests, permission changes, role assignments, and dataset visibility state transitions. Establish event schema capturing actor, action, timestamp, affected object, and before/after state where applicable. Define retention policies and access rules for audit data. Establish how audit data is presented to administrators. Ensure every privileged action has a corresponding required audit event, and audit records are immutable and queryable by object and actor.

### FS-022 - Automated Checks vs Manual Overrides

**Status:** 📋 Planned

Define which validations are automated, which can be overridden, and how overrides are tracked. Establish which checks are hard gates versus soft warnings. Define override permissions and required audit trails. Establish how override rationale is captured and stored. Ensure every override is attributable to a specific actor, timestamped, and visible in audit logs.

---

## 📋 API & Interoperability (Planned)

### FS-023 - Public API Harvesting Contract

**Status:** 📋 Planned

Define minimum REST API endpoints and field stability guarantees required for data harvesting. Establish required endpoints with request and response structures. Define pagination strategies. Establish field stability guarantees and versioning. Define error response contracts. Ensure a harvesting client can be implemented based solely on the specification.

### FS-024 - API Authorization Rules

**Status:** 📋 Planned

Define authorization levels distinguishing public, authenticated, reviewer-restricted, and administrator-restricted access. Establish authorization rules for each endpoint or resource type. Define authentication token or session requirements where applicable. Establish expected error responses for unauthorized or forbidden requests. Ensure for each endpoint the specification defines allowed roles and denial behavior.

### FS-025 - API Versioning & Deprecation Policy

**Status:** 📋 Planned

Define compatibility guarantees and deprecation procedures for the public API. Establish versioning scheme selecting from URL path versioning, header-based versioning, or media type versioning. Define backward-compatibility rules. Establish deprecation communication requirements and timelines. Ensure API consumers can determine when field or endpoint changes are breaking versus non-breaking.

---

## 💡 Additional Enhancements (Proposed)

### FS-029 - Data Visualization Framework

**Status:** 💡 Proposed

Define framework for generating interactive data visualizations for measurements and sample collections. Establish charting library integration (e.g., Chart.js, Plotly) with server-side data aggregation. Specify visualization types for common data patterns (time series, scatter plots, histograms, heatmaps). Define configuration patterns allowing portal developers to register custom visualizations for domain-specific measurement types. Support export of visualizations as static images or interactive HTML. Ensure visualizations update dynamically with data filters and provide drill-down capabilities to underlying records.

### FS-030 - Internationalization & Localization

**Status:** 💡 Proposed

Define comprehensive i18n/l10n strategy supporting multi-language portals and translatable content. Establish translation workflow for UI strings, documentation, and user-generated content. Specify django-parler integration for translatable model fields with per-field language fallbacks. Define translation contribution process and quality assurance procedures. Support right-to-left languages, locale-specific date/number formatting, and timezone handling. Ensure portal interfaces can be fully translated while preserving technical functionality and FAIR metadata can include multilingual descriptions and keywords.
