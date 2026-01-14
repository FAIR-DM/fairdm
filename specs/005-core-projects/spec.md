# Feature Specification: Core Projects MVP

**Feature Branch**: `005-core-projects`  
**Created**: January 14, 2026  
**Status**: Draft  
**Input**: User description: "Focus on the role of Projects within FairDM, targeting code within the fairdm.core.project app. Polish the Project model, ensure i18n compliance, create forms with proper help text and error handling, set up admin interface, configure filtering for portal users."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create and Configure Project (Priority: P1)

A research team lead or project manager wants to create a new project record to establish the organizational container for their research initiative. They need to provide basic identification (name, description) and context (status, visibility, ownership) to make the project findable and properly attributed.

**Why this priority**: This is the foundational capability - without the ability to create projects with core metadata, no other project features can be utilized. This represents the minimum viable functionality.

**Independent Test**: Can be fully tested by navigating to the project creation interface, filling in required fields (name, status, visibility), and successfully saving a new project record that appears in the project list and detail views.

**Acceptance Scenarios**:

1. **Given** I am a logged-in user with project creation permissions, **When** I navigate to the "Create Project" page and submit the form with required fields (name, status, visibility), **Then** a new project is created with a unique identifier and I am redirected to the project detail page.

2. **Given** I am creating a project, **When** I leave the name field empty and submit, **Then** I see a clear error message indicating that the project name is required.

3. **Given** I am creating a project, **When** I provide a name that exactly matches an existing project owned by the same organization, **Then** I see a warning about potential duplication but am still allowed to create the project.

4. **Given** I am editing an existing project, **When** I change the visibility from "Private" to "Public", **Then** the project becomes visible to non-authenticated users in the project list.

5. **Given** I am creating a project, **When** I select "Concept" as the status, **Then** the status is saved correctly and displayed in the project detail view and list views.

---

### User Story 2 - Add Rich Descriptive Metadata (Priority: P1)

A researcher wants to add detailed contextual information about their project including multiple description types (abstract, methods, significance), date milestones (start date, end date, data collection periods), and identifiers (DOI, grant numbers) to make the project FAIR-compliant and discoverable.

**Why this priority**: Rich metadata is essential for FAIR principles (Findable, Accessible, Interoperable, Reusable). Without this, projects lack the context needed for discovery, citation, and reuse. This is core to FairDM's value proposition.

**Independent Test**: Can be fully tested by creating a project, then adding multiple descriptions with different types (Abstract, Methods), adding date ranges (project start/end), and adding external identifiers (DOI, grant number), then verifying all metadata displays correctly on the project detail page.

**Acceptance Scenarios**:

1. **Given** I have created a project, **When** I add a description with type "Abstract" and save, **Then** the abstract appears in the project detail view under a clearly labeled "Abstract" section.

2. **Given** I have a project with one description, **When** I add a second description with type "Methods", **Then** both descriptions are displayed independently with their respective type labels.

3. **Given** I am adding project dates, **When** I add a start date (type: "Project Start") and end date (type: "Project End"), **Then** the project timeline is displayed correctly showing duration and current phase.

4. **Given** I am adding project identifiers, **When** I add a DOI identifier, **Then** the DOI is displayed as a clickable link in the project detail view and included in metadata exports.

5. **Given** I am editing project descriptions, **When** I delete an existing description, **Then** it is removed from the project detail view and the change is persisted.

---

### User Story 3 - Manage Project Team and Contributors (Priority: P2)

A project lead wants to associate contributors (individual researchers, organizations, institutions) with the project and assign them appropriate roles (Principal Investigator, Co-Investigator, Data Manager, etc.) to properly attribute work and manage permissions.

**Why this priority**: Proper attribution is critical for academic research and FAIR principles. However, basic project creation and metadata can function without a full contributor system, making this P2 rather than P1.

**Independent Test**: Can be fully tested by creating a project, adding multiple contributors with different roles, verifying their display in the project team section, and confirming that contributor information appears in metadata exports and citation formats.

**Acceptance Scenarios**:

1. **Given** I have a project, **When** I add a contributor with role "Principal Investigator", **Then** they appear in the project team list with their role clearly identified.

2. **Given** I have a project with multiple contributors, **When** I view the project detail page, **Then** contributors are displayed in a logical order (by role hierarchy or alphabetically) with their names, roles, and affiliations.

3. **Given** I am adding a contributor, **When** I select a person who is already registered in the system, **Then** their existing profile information (name, affiliation, ORCID) is automatically linked rather than duplicated.

4. **Given** I have contributor roles assigned, **When** I change a contributor's role from "Co-Investigator" to "Data Manager", **Then** the change is reflected immediately in all views displaying that contributor.

5. **Given** I am a project contributor, **When** I view the project detail page, **Then** I can see all other contributors and their roles (subject to privacy settings).

---

### User Story 4 - Organize Projects with Keywords and Tags (Priority: P2)

A researcher wants to categorize their project using controlled vocabulary keywords (from discipline-specific ontologies) and free-form tags to improve discoverability through filtering and search.

**Why this priority**: Keywords and tags significantly enhance findability but are not strictly required for a minimal viable project record. They can be added after initial project creation.

**Independent Test**: Can be fully tested by creating a project, adding both controlled keywords from a configured vocabulary and custom tags, then using the project filter interface to find projects by those keywords/tags.

**Acceptance Scenarios**:

1. **Given** I am editing a project, **When** I add keywords from a controlled vocabulary using an autocomplete widget, **Then** the selected keywords are saved and displayed as clickable filter links on the project detail page.

2. **Given** I am editing a project, **When** I add custom free-form tags, **Then** the tags are saved and displayed distinctly from controlled keywords.

3. **Given** I am browsing projects, **When** I click on a keyword or tag, **Then** I am taken to a filtered list showing all projects with that keyword/tag.

4. **Given** I am using the project filter interface, **When** I select multiple keywords, **Then** I see only projects that match all selected keywords (AND logic by default).

5. **Given** I have projects with keywords, **When** I export project metadata, **Then** keywords are included in machine-readable formats using standardized vocabulary URIs.

---

### User Story 5 - Configure Admin Interface for Project Management (Priority: P3)

A portal administrator wants a comprehensive Django admin interface for managing projects including bulk operations, advanced filtering, inline editing of related metadata (descriptions, dates, identifiers), and data quality validation.

**Why this priority**: Admin interface improvements enhance administrative efficiency but are not required for end-user functionality. Portal users interact through the public interface, not the admin.

**Independent Test**: Can be fully tested by logging into the Django admin, navigating to the Projects section, performing CRUD operations, using filters and search, editing inline descriptions/dates, and verifying data quality checks.

**Acceptance Scenarios**:

1. **Given** I am an admin user, **When** I access the Projects admin, **Then** I can search projects by name, UUID, or owner organization.

2. **Given** I am viewing the project list in admin, **When** I use the status filter, **Then** I see only projects matching the selected status.

3. **Given** I am editing a project in admin, **When** I add/edit descriptions, dates, and identifiers inline without leaving the project edit page, **Then** all changes are saved correctly.

4. **Given** I am viewing a project in admin, **When** the project is missing required metadata (e.g., no abstract, no start date), **Then** I see clear warnings or indicators highlighting the gaps.

5. **Given** I select multiple projects in the admin list, **When** I perform a bulk action (e.g., "Export as JSON", "Change status"), **Then** the action applies to all selected projects correctly.

---

### User Story 6 - Filter and Search Projects (Priority: P2)

A portal user wants to find relevant projects by filtering on status, owner organization, keywords, contributors, and other criteria, with an intuitive interface that shows how many projects match before applying filters.

**Why this priority**: Filtering is essential for discoverability in portals with many projects, but basic list views can function without advanced filtering initially.

**Independent Test**: Can be fully tested by navigating to the project list view, applying various filters (status, owner, keywords), verifying result counts update dynamically, and confirming filtered results match the criteria.

**Acceptance Scenarios**:

1. **Given** I am viewing the project list, **When** I select a status filter (e.g., "In Progress"), **Then** only projects with that status are displayed and the result count updates.

2. **Given** I am using multiple filters, **When** I select both a status and an owner organization, **Then** only projects matching both criteria are shown.

3. **Given** I have applied filters, **When** I clear all filters, **Then** the full project list is restored.

4. **Given** I am filtering by keywords, **When** I select a keyword from the autocomplete widget, **Then** only projects tagged with that keyword appear.

5. **Given** I am viewing filtered results, **When** I sort by name or date modified, **Then** the filtered results are sorted correctly without losing the filter state.

---

### Edge Cases

- What happens when a project name contains special characters or is extremely long (>255 characters)?
- How does the system handle a project with no owner organization (orphaned projects)?
- What happens when a user tries to add the same description type multiple times (e.g., two "Abstract" descriptions)?
- How does the system handle date inconsistencies (e.g., end date before start date)?
- What happens when a contributor is removed from the system but is still associated with projects?
- How does the system handle visibility changes when a project has public datasets but is changed to private status?
- What happens when attempting to create identical external identifiers (e.g., same DOI) for different projects?
- How are internationalized characters in project names and descriptions handled in search and filtering?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow authenticated users with appropriate permissions to create new project records with required fields (name, status, visibility).

- **FR-002**: System MUST generate a unique, short, human-readable identifier (UUID with prefix) for each project upon creation.

- **FR-003**: System MUST support multiple description types (Abstract, Methods, Significance, etc.) for each project, each stored as a separate related record.

- **FR-004**: System MUST allow users to add multiple date records to projects with typed date categories (Project Start, Project End, Data Collection Start, Data Collection End).

- **FR-005**: System MUST allow users to add multiple external identifiers to projects with identifier types from a controlled vocabulary (DOI, Grant Number, Proposal ID, etc.).

- **FR-006**: System MUST support project status tracking through a controlled vocabulary with at least these states: Concept, Planning, Active, On Hold, Complete, Cancelled.

- **FR-007**: System MUST support project visibility levels including at minimum: Private (only team members), Organization (anyone in owning organization), Public (anyone).

- **FR-008**: System MUST associate projects with an owning organization and optionally multiple contributing organizations.

- **FR-009**: System MUST allow users to associate contributors (people and organizations) with projects and assign roles from a controlled vocabulary (Principal Investigator, Co-Investigator, Data Manager, etc.).

- **FR-010**: System MUST support both controlled vocabulary keywords and free-form tags for project categorization.

- **FR-011**: System MUST provide form validation with clear, user-friendly error messages in the user's selected language.

- **FR-012**: System MUST provide contextual help text for all form fields explaining what information is expected and why it matters.

- **FR-013**: System MUST display projects in a list view with pagination, sorting by name, status, and modification date.

- **FR-014**: System MUST display project details in a dedicated detail view showing all metadata, descriptions, dates, identifiers, contributors, and related datasets.

- **FR-015**: System MUST provide filtering capabilities for the project list including filters for status, owner, keywords, contributors, and visibility.

- **FR-016**: System MUST support full-text search across project names, descriptions, and keywords.

- **FR-017**: System MUST provide a comprehensive admin interface for project management including search, filtering, inline editing of related metadata, and bulk operations.

- **FR-018**: System MUST enforce object-level permissions allowing project owners and contributors with appropriate roles to edit project metadata while restricting access to others.

- **FR-019**: System MUST ensure all user-facing strings (field labels, help text, error messages, UI text) use Django's internationalization (i18n) framework for translation support.

- **FR-020**: System MUST validate date ranges to ensure end dates are not before start dates, displaying appropriate warnings when inconsistencies are detected.

- **FR-021**: System MUST prevent deletion of projects that have associated datasets unless explicitly forced by an administrator.

- **FR-022**: System MUST maintain audit trails showing when projects were created, modified, and by whom.

- **FR-023**: System MUST export project metadata in machine-readable formats (JSON-LD, DataCite JSON) including all descriptions, dates, identifiers, and contributor information.

- **FR-024**: System MUST display project funding information when available, supporting structured funding data (funder, grant number, amount, period).

- **FR-025**: System MUST optimize database queries for project lists using select_related and prefetch_related to minimize query count.

### Key Entities

- **Project**: The top-level organizational container representing a research initiative. Core attributes include unique identifier (UUID), name, status, visibility, owner organization, funding information, and timestamps (created, modified). Related to: Organization (owner), Contributors (team members), Descriptions (multiple types), Dates (timeline), Identifiers (external IDs), Keywords (controlled vocabulary), Tags (free-form), Datasets (child records).

- **Project Description**: Typed descriptions providing context about the project. Attributes include description type (from controlled vocabulary), text content, and ordering for display. Relationship: Many-to-one with Project.

- **Project Date**: Typed date records marking project milestones and phases. Attributes include date type (from controlled vocabulary), date value, and optional end date for ranges. Relationship: Many-to-one with Project.

- **Project Identifier**: External identifiers for project discovery and citation. Attributes include identifier type (DOI, Grant Number, etc.), identifier value, and optional URL. Relationship: Many-to-one with Project.

- **Project Contributor**: Association between projects and people/organizations with role information. Attributes include contributor reference, role type (from controlled vocabulary), and order/prominence. Relationship: Many-to-one with Project, generic foreign key to Person or Organization.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can create a complete project record (name, status, visibility, owner, at least one description) in under 3 minutes from a blank form.

- **SC-002**: Project list pages load with pagination showing 50 projects in under 1 second for datasets up to 10,000 projects.

- **SC-003**: All form validation errors are displayed inline with clear, actionable messages indicating what needs to be corrected.

- **SC-004**: Filtering the project list by any single criterion (status, owner, keyword) returns results in under 500ms for datasets up to 10,000 projects.

- **SC-005**: 100% of user-facing strings (field labels, help text, error messages, buttons) are wrapped in Django translation functions and translatable.

- **SC-006**: Admin users can search for projects by name or UUID and receive results in under 300ms.

- **SC-007**: The project detail view displays all associated metadata (descriptions, dates, identifiers, contributors) in a single page load with no more than 5 database queries.

- **SC-008**: Users can add up to 10 contributors to a project with role assignments in under 2 minutes using an autocomplete interface.

- **SC-009**: Project metadata exports (JSON-LD, DataCite) include all required fields for external repository submission (DataCite, Zenodo, etc.) without manual editing.

- **SC-010**: The admin interface supports bulk status changes for up to 100 projects simultaneously completing in under 5 seconds.
