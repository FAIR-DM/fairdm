# Feature Specification: FairDM Contributors System

**Feature Branch**: `009-fairdm-contributors`
**Created**: 2026-02-18
**Status**: Draft
**Input**: User description: "The contributors app serves as the human infrastructure layer of FairDM portals, managing people and organizations who participate in research data creation, curation, and sharing. This feature focuses on developer-facing aspects: data models, managers, utilities, and templatetags for attribution, identity persistence, and community building."

## Clarifications

### Session 2026-02-18

- Q: Are Affiliation and OrganizationMembership two separate records, or is active membership derived from an open-ended Affiliation? → A: Single **Affiliation** model; active membership is an Affiliation with no end date. `OrganizationMembership` is removed as a separate entity. **Critical constraint**: production databases already use `OrganizationMembership`, so data migrations from `OrganizationMembership` to `Affiliation` must be explicitly planned and safely executed without data loss.
- Q: What is the coupling strategy between Person and the auth User model? → A: **Person IS the auth User model** (`AUTH_USER_MODEL = "contributors.Person"`). Person extends `AbstractUser` directly — there is no separate User model. An "unclaimed" person (added for data provenance by someone else) is distinguished by having `email = NULL` and no usable password, meaning they cannot log in. A claimed person has a valid email and credentials.
- Q: What access-control mechanism enforces Organization ownership privileges? → A: **`django-guardian` object-level permissions** on the Organization instance (e.g. a `manage_organization` permission), consistent with how Projects and Datasets handle object-level access in FairDM.
- Q: What triggers ORCID/ROR synchronization? → A: **On-save for initial population** (fires when an ORCID/ROR identifier is first set or changed) plus a **periodic background task via Celery** for routine refresh of existing profiles.
- Q: What happens when an organization has no owner assigned — who can manage it? → A: **Portal admins only** — an ownerless organization is managed exclusively by Django staff/superusers until an admin explicitly grants `manage_organization` to a person. No automatic promotion of members occurs.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Core Contributor Data Models (Priority: P1)

As a developer, I have access to predefined, metadata-rich Person and Organization models with essential fields so that I can capture comprehensive contributor information and link it to research outputs (projects, datasets, samples, measurements) without writing custom models.

**Why this priority**: These built-in models are the foundation of the contributors system. Every portal needs to track people and organizations, and having these models ready to use immediately enables contributor tracking from day one.

**Independent Test**: Can be fully tested by creating Person and Organization instances with various field combinations, querying them, and verifying field validation. Delivers immediate value by enabling basic contributor tracking without any model development work.

**Acceptance Scenarios**:

1. **Given** I am setting up a new portal, **When** I use the built-in Person model to create records with standard fields (name, email, affiliation, ORCID), **Then** I can create and save person records with proper field validation
2. **Given** the Person model has privacy controls, **When** I set privacy levels on sensitive fields (email, phone), **Then** public views exclude these fields while authenticated views include them
3. **Given** I need to track organizations, **When** I use the built-in Organization model with name, location, ROR identifier, and parent organization fields, **Then** I can model institutional hierarchies without custom development
4. **Given** I have contributors in the system, **When** I link them to Projects/Datasets/Samples/Measurements using built-in relationship fields, **Then** I can query all contributions for a given person or organization
5. **Given** I have Person and Organization instances, **When** I retrieve contributor information, **Then** I get proper string representations suitable for citations and display

---

### User Story 2 - External Identifier Integration (Priority: P2)

As a developer, automatic synchronization with ORCID (for persons) and ROR (for organizations) registries happens transparently so that contributor profiles remain current and authoritative without me needing to manage it myself.

**Why this priority**: This is critical for FAIR compliance and prevents attribution confusion. It ensures that contributor identities are globally unique and verifiable.

**Independent Test**: Can be fully tested by providing an ORCID/ROR identifier and verifying that the system fetches and updates contributor metadata automatically. Delivers immediate value by maintaining accurate, up-to-date contributor information.

**Acceptance Scenarios**:

1. **Given** I have a Person with an ORCID identifier, **When** I trigger a sync operation, **Then** the system fetches current name, affiliation, and other public metadata from ORCID
2. **Given** I have an Organization with a ROR identifier, **When** I trigger a sync operation, **Then** the system fetches current organization name, location, and parent institution from ROR
3. **Given** I am creating a new Person, **When** I provide only an ORCID identifier, **Then** the system auto-populates name and affiliation fields from ORCID
4. **Given** external data has changed, **When** I schedule periodic sync operations, **Then** contributor profiles automatically update with current information
5. **Given** an external sync fails, **When** I check the contributor record, **Then** I see the last successful sync timestamp and any error messages

---

### User Story 3 - Person Profile Management via Admin (Priority: P3)

As a portal admin, a unified admin interface lets me manage the Person record — which serves as both the contributor profile and the auth account — in one place, so I never have to context-switch to maintain complete and consistent contributor records.

**Why this priority**: Without unified management, admins must navigate multiple admin sections to maintain a single contributor's information, which leads to inconsistencies and missed updates. A unified interface is essential for maintaining data integrity.

**Independent Test**: Can be fully tested by creating, editing, and deleting Person profiles through the admin interface and verifying that corresponding user account fields are updated atomically. Delivers value by eliminating the dual-screen management problem immediately.

**Acceptance Scenarios**:

1. **Given** I am a portal admin, **When** I open a Person record in the admin, **Then** I see both auth account fields (email, account status, last login) and contributor profile fields (ORCID, biography, affiliations) unified in a single view — because Person is the auth model
2. **Given** I am a portal admin, **When** I create a new Person with no email address, **Then** the record is saved as unclaimed (cannot log in) and is available for attribution purposes only
3. **Given** I have an unclaimed profile with ORCID identifier, **When** the data model is queried, **Then** the system provides the data structure needed for future claiming flows (see Feature 010) to match and link accounts based on ORCID
4. **Given** a user claims a profile, **When** they access their profile, **Then** they can edit permitted fields (bio, photo, preferences) while admin-controlled fields remain read-only
5. **Given** I am a portal admin, **When** I filter contributors by claim status, **Then** I can quickly identify unclaimed profiles that need follow-up
6. **Given** I edit account-level fields for a Person, **When** I save, **Then** both the User model and Person model are updated atomically with no partial-save failure states

---

### User Story 3b - Organization Management via Admin (Priority: P3)

As a portal admin, a dedicated admin interface lets me create, edit, and manage Organizations — including their profile details, membership, sub-organizations, and external identifiers — so that the portal always has an accurate and up-to-date picture of the institutions represented in the research community.

**Why this priority**: Organizations are first-class entities in FairDM and need the same quality of admin tooling as Person profiles. Without it, admins cannot maintain institutional records or review organizational membership.

**Independent Test**: Can be fully tested by performing full CRUD operations on Organizations through the admin, managing memberships inline, and verifying that parent-child organizational relationships are correctly enforced. Delivers value by giving admins complete control over institutional records.

**Acceptance Scenarios**:

1. **Given** I am a portal admin, **When** I open an Organization record, **Then** I see all profile fields (name, ROR, location, logo, URL, type) and an inline list of current members with their roles
2. **Given** I am a portal admin, **When** I create a new Organization, **Then** I can optionally link it to a parent organization to model institutional hierarchy
3. **Given** I am a portal admin, **When** I add or remove members from an Organization, **Then** those changes are reflected immediately in all affiliation records
4. **Given** I am a portal admin, **When** I trigger a ROR sync for an Organization, **Then** the profile fields are updated from the ROR registry and the last-synced timestamp is recorded
5. **Given** I am a portal admin, **When** I search for organizations by name or ROR identifier, **Then** I quickly find the target record without scrolling through a full list

---

### User Story 3c - Organization Ownership by Authenticated Users (Priority: P3)

As an authenticated user, I can own an Organization so that I have the authority to manage its profile and membership without requiring portal admin intervention for every change.

**Why this priority**: Admin-only management of organizations creates a bottleneck. Delegating ownership to trusted users enables community self-governance and reduces the admin workload while preserving accountability.

**Independent Test**: Can be fully tested by assigning an owner to an organization, verifying the owner can edit the org profile and manage memberships, verifying non-owners and unauthenticated users cannot, and verifying portal admins retain override access. Delivers value by enabling decentralized organizational self-management.

**Acceptance Scenarios**:

1. **Given** I am the owner of an Organization, **When** I access the organization management interface, **Then** I can edit the organization's profile (name, logo, URL, description) without requiring admin intervention
2. **Given** I am the owner of an Organization, **When** I manage memberships, **Then** I can invite, approve, or remove members and assign their roles within the organization
3. **Given** I am a regular authenticated user (non-owner), **When** I view an Organization, **Then** I can see the public profile but cannot edit it or manage memberships
4. **Given** I am the owner and I wish to transfer ownership, **When** I assign a new owner from existing members, **Then** the previous owner loses ownership privileges and the new owner gains them
5. **Given** I am a portal admin, **When** I manage any Organization, **Then** I retain full access regardless of who the designated owner is

---

### User Story 4 - Contributor Roles and Affiliations (Priority: P4)

As a developer, built-in support for multiple roles and time-bound affiliations lets me accurately represent each contributor's involvement and institutional history without writing custom relationship models.

**Why this priority**: Essential for proper academic attribution and credit. Contributors often have multiple roles (PI, data collector, analyst) and affiliations change over time.

**Independent Test**: Can be fully tested by assigning multiple roles to contributors on different projects/datasets, recording affiliation changes with dates, and querying contribution history. Delivers value by capturing the full context of contributions.

**Acceptance Scenarios**:

1. **Given** I have a contributor on a project, **When** I assign them roles (Principal Investigator, Data Collector, Analyst), **Then** these roles are stored with the project-contributor relationship
2. **Given** a contributor changes institutions, **When** I record their new affiliation with start/end dates, **Then** historical affiliations are preserved with accurate time ranges
3. **Given** I need to display dataset contributors, **When** I query the dataset, **Then** I get all contributors with their role-specific contributions at the time of the dataset
4. **Given** I have contributors with multiple affiliations, **When** I generate citations, **Then** the system includes the relevant affiliation for that specific contribution
5. **Given** I want to track organizational membership, **When** I link a Person to multiple Organizations with roles, **Then** I can query all members of an organization and their roles

---

### User Story 5 - Metadata Export and Interoperability (Priority: P5)

As a developer, built-in DataCite and Schema.org exports work out of the box so my portal is immediately FAIR-compliant, and I have access to a well-documented public API for creating bidirectional transformations to import from and export to additional external formats.

**Why this priority**: Critical for FAIR compliance (Interoperable, Reusable). Built-in formats enable immediate integration with scholarly infrastructure, while the extensible bidirectional API allows portals to exchange contributor data with domain-specific systems, institutional repositories, and external data sources.

**Independent Test**: Can be fully tested by creating contributors with various attributes, verifying built-in export functions produce valid DataCite and Schema.org JSON-LD, creating a custom transformer for a new format, and importing contributor data from external sources. Delivers value by making contributor information harvestable in standard formats and enabling data exchange with external systems.

**Acceptance Scenarios**:

1. **Given** I have a contributor with complete metadata, **When** I export to DataCite format, **Then** I get valid DataCite Creator/Contributor XML with name, identifier, and affiliation
2. **Given** I have an organization, **When** I export to Schema.org format, **Then** I get valid JSON-LD with type Organization including location and identifier
3. **Given** I have dataset contributors, **When** I generate dataset metadata, **Then** contributor information is properly embedded in the dataset's DataCite metadata
4. **Given** external systems harvest my portal, **When** they request contributor metadata, **Then** they receive structured data with persistent identifiers
5. **Given** I need to generate citations, **When** I use the citation utility, **Then** I get properly formatted citations following standard academic styles (APA, Chicago, etc.)
6. **Given** I need to support a custom metadata format, **When** I use the transformation API to define a new transformer, **Then** I can export contributor data in my custom format using the same interface as built-in formats
7. **Given** I have contributor data in a custom external format, **When** I use the transformation API to import the data, **Then** Person and Organization records are created with properly mapped fields

---

### User Story 6 - Query Utilities and Custom Managers (Priority: P6)

As a developer, I have access to custom model managers and utility functions so that I can efficiently query contributors, filter by various criteria, and build new features without writing repetitive queryset code.

**Why this priority**: Improves developer productivity and maintainability. Provides consistent, well-tested patterns for common contributor-related operations that all addons and extensions can rely on.

**Independent Test**: Can be fully tested by using manager methods to query contributors with various filters, performing bulk operations, and verifying query efficiency. Delivers value by reducing development time for contributor features.

**Acceptance Scenarios**:

1. **Given** I need to find contributors with specific expertise, **When** I use the search utility with keywords, **Then** I get relevant contributors ranked by match quality
2. **Given** I want to find active contributors, **When** I use a manager method to filter by recent activity, **Then** I get contributors who have made contributions within a specified timeframe
3. **Given** I need to display organization members, **When** I query an organization's contributors, **Then** I get an optimized queryset with prefetched relationships
4. **Given** I want to identify potential duplicate profiles, **When** I use the duplicate detection utility, **Then** I get groups of contributors with similar names/identifiers
5. **Given** I need to perform bulk operations, **When** I use manager methods for batch updates, **Then** operations are executed efficiently with minimal database queries

---

### Edge Cases

- What happens when a Person has multiple ORCID identifiers or conflicting ORCID data?
- How does the system handle ORCID/ROR API failures or rate limiting during sync operations?
- What happens when a claimed profile is deleted by the user but their contributions still need attribution?
- How are contributors handled when they have special characters or non-Latin scripts in their names?
- What happens when an organization's ROR identifier changes or the organization is merged with another?
- How does the system prevent duplicate profiles when multiple admins create contributors with similar information?
- What happens when privacy settings conflict with FAIR metadata requirements (e.g., public dataset requiring contributor emails)?
- What happens if the data migration from `OrganizationMembership` to `Affiliation` fails partway through — how is the partial state detected and rolled back?
- **[Resolved]** An organization with no `manage_organization` permission holder is managed exclusively by portal admins (Django staff/superusers); no member auto-promotion occurs. Admin must explicitly grant `manage_organization` to establish an owner.
- What happens when an organization owner's account is deactivated or deleted?
- How does the system handle a Person profile where the linked User account is deleted?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a built-in **Person** model that extends the Django auth user model, serving as both the contributor profile and the authentication account in a single model
- **FR-001a**: A Person with `email = NULL` and no usable password MUST be treated as an unclaimed/provenance-only record that cannot log in; a Person with a valid email and credentials is a fully active account
- **FR-002**: System MUST provide built-in Organization model with fields for name, location (geographic), ROR identifier, logo, URL, parent organization, and organization type
- **FR-003**: System MUST support many-to-many relationships between Person and Organization via a single **Affiliation** model with role and time period tracking; active membership is represented by an Affiliation with no end date
- **FR-003a**: System MUST provide a data migration that safely moves all existing `OrganizationMembership` records into `Affiliation` records without data loss before `OrganizationMembership` is removed
- **FR-004**: System MUST support linking contributors to Projects, Datasets, Samples, and Measurements with role specification
- **FR-005**: System MUST trigger an ORCID sync automatically when an ORCID identifier is first set or changed on a Person record; additionally, a periodic Celery background task MUST refresh all Person records that have an ORCID identifier
- **FR-006**: System MUST trigger a ROR sync automatically when a ROR identifier is first set or changed on an Organization record; additionally, a periodic Celery background task MUST refresh all Organization records that have a ROR identifier
- **FR-007**: System MUST distinguish between claimed Person records (valid email + credentials, can log in) and unclaimed Person records (NULL email, no usable password, provenance-only) via a computed `is_claimed` property and `claimed()`/`unclaimed()` manager queryset methods
- **FR-008**: *Deferred to [Feature 010: Profile Claiming & Account Linking](../010-profile-claiming/spec.md).* The data model MUST be designed to support future claiming flows (ORCID match, email match, token-based, post-signup merge) but no claiming flow UI, adapters (except the existing ORCID adapter bug fix), or merge logic is implemented in this feature.
- **FR-009**: System MUST enforce privacy controls on sensitive fields (email, phone) based on user preferences and claim status
- **FR-010**: System MUST track affiliation history with start and end dates for each Person-Organization relationship
- **FR-010a**: System MUST provide a unified admin interface for the Person model that exposes both auth account fields and contributor profile fields in a single view — no separate User admin is required since Person IS the auth model
- **FR-010c**: System MUST provide a dedicated Organization admin interface with inline membership management and inline sub-organization listing
- **FR-010d**: System MUST support assigning Organization ownership by granting a designated Person the `manage_organization` object-level permission on that Organization instance via `django-guardian`
- **FR-010e**: A Person holding the `manage_organization` object-level permission MUST be able to edit the organization profile and manage memberships without requiring Django admin or staff privileges
- **FR-010f**: Organization ownership MUST be transferable by the current owner by revoking their own `manage_organization` permission and granting it to any existing member
- **FR-010g**: Portal admins (Django staff/superuser) MUST retain full management access to all Organizations regardless of `manage_organization` permission assignment
- **FR-010h**: An Organization with no Person holding `manage_organization` MUST remain fully accessible to portal admins only; no automatic promotion of existing members to owner status may occur — ownership must be explicitly granted by a portal admin
- **FR-011**: System MUST export contributor metadata in DataCite XML/JSON format
- **FR-012**: System MUST export contributor metadata in Schema.org JSON-LD format
- **FR-012a**: System MUST provide a well-documented public API for developers to create custom bidirectional metadata transformations (import and export) for additional formats
- **FR-012b**: System MUST support importing contributor data from external sources using the transformation API with proper field mapping and validation
- **FR-013**: System MUST provide custom model managers with methods for common queries (active contributors, recent activity, search by expertise)
- **FR-014**: System MUST provide utility functions for duplicate detection based on names and identifiers
- **FR-016**: System MUST support multiple roles per contributor per research output (e.g., PI, Data Collector, Analyst)
- **FR-017**: System MUST track last sync timestamp and sync status for external identifier integrations
- **FR-018**: System MUST provide contribution aggregation showing all research outputs by a given contributor
- **FR-019**: System MUST generate properly formatted citations including contributor names and affiliations
- **FR-020**: System MUST handle internationalization for contributor names with non-Latin scripts

### Key Entities

- **Person**: The central model for both individual contributors and authenticated users. Person extends the auth user model directly — there is no separate User table. A Person created by an admin for provenance purposes (unclaimed) has `email = NULL` and no usable password, preventing login. A Person with a valid email and credentials is a fully active, claimed account. Key attributes include name variants, ORCID identifier, biography, photo, privacy settings, and sync metadata.

- **Organization**: Represents an institution or research organization with identifying information (name, ROR), location, branding (logo), and hierarchical relationships (parent organization). Key attributes include organization type, URL, and contact information.

- **Contribution**: Junction entity linking contributors (Person or Organization) to research outputs (Project, Dataset, Sample, Measurement) with role specification and time context. Tracks the "who did what" relationship.

- **Affiliation**: Time-bound relationship between Person and Organization capturing institutional membership with role, start date, and end date. Enables historical affiliation tracking. The `type` field (0=PENDING, 1=MEMBER, 2=ADMIN, 3=OWNER) tracks verification status and authorization level.

**Organization Ownership**: Organization ownership is implemented via the `manage_organization` object-level permission (django-guardian) synchronized with `Affiliation.type=OWNER`. When a Person's Affiliation type changes to/from OWNER (3), a lifecycle hook automatically grants/revokes the `manage_organization` permission. This is not a separate model but a permission relationship enforced through the Affiliation model's state machine.

## Dependencies & Assumptions

### External Dependencies

- **ORCID API**: System depends on ORCID public API for fetching person metadata. Assumes API is publicly accessible and returns data in documented JSON format.
- **ROR API**: System depends on ROR registry API for fetching organization metadata. Assumes API is publicly accessible and returns data in documented JSON format.
- **django-guardian**: Organization ownership privileges rely on `django-guardian` object-level permissions, consistent with Project and Dataset access control.
- **Celery + Redis**: Periodic ORCID/ROR profile refresh relies on Celery beat tasks and a Redis broker, consistent with FairDM's recommended background task infrastructure.
- **Schema.org Vocabulary**: System must use Schema.org Person and Organization types for structured data.

### Assumptions

- Person IS the auth user model (`AUTH_USER_MODEL = "contributors.Person"`); there is no separate User table to link or synchronise
- An unclaimed Person is identified by `email = NULL`; no additional claim-status field is required
- Developers can immediately use the built-in Person and Organization models without custom model development
- ORCID and ROR identifiers, when provided, are valid and correctly formatted
- Contributor names using non-Latin scripts can be represented in Unicode (UTF-8)
- The portal has authentication system in place for user account management (claimed profiles)
- Geographic location data is available in standardized format (coordinates, country codes)
- Existing production `OrganizationMembership` records must be fully preserved (no data loss) during migration to the unified `Affiliation` model

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developers can start using built-in Person and Organization models for contributor tracking immediately without any setup time
- **SC-002**: System successfully synchronizes with ORCID registry for 95% of valid ORCID identifiers within 5 seconds
- **SC-003**: System successfully synchronizes with ROR registry for 95% of valid ROR identifiers within 5 seconds
- **SC-004**: Exported DataCite and Schema.org metadata passes validation with 100% compliance to schemas
- **SC-005**: Duplicate detection utility identifies 90% of true duplicates while producing less than 5% false positives
- **SC-006**: Developers write at least 60% less code for common contributor queries by using the provided managers compared to manual queryset construction
- **SC-007**: Portal can handle 10,000+ contributor records with contributor lookup completing in under 200ms
- **SC-008**: Privacy-controlled fields are correctly excluded from public views in 100% of cases
- **SC-009**: Generated citations match standard academic formats (APA, Chicago) with 99% accuracy
