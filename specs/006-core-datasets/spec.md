# Feature Specification: Core Dataset App Cleanup & Enhancement

**Feature Branch**: `006-core-datasets`
**Created**: 2026-01-15
**Status**: Draft
**Input**: User description: "Focus on cleaning up and enhancing the fairdm.core.dataset app. We will go through models, modelmanagers, forms, filters and admin, making sure to identify feature holes, testing requirements and enhancements that support fair data and portal useability. Client side integration (e.g. list views, detail views, api, etc) are out of scope for this feature and will be deferred to later specs."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dataset Model Validation & FAIR Compliance (Priority: P1)

As a portal developer using FairDM, I want the Dataset model to enforce FAIR data principles through validation and provide comprehensive metadata fields so that all datasets created in my portal inherently support findability, accessibility, interoperability, and reusability without additional implementation.

**Why this priority**: FAIR compliance is a core FairDM principle and foundational to all dataset operations. Without proper model-level enforcement, data quality cannot be guaranteed.

**Independent Test**: Can be fully tested by creating Dataset instances with various metadata combinations and verifying validation rules work correctly. Success is demonstrated when required FAIR metadata is enforced and optional metadata is properly handled.

**Acceptance Scenarios**:

1. **Given** a user creates a dataset without a name, **When** the dataset is saved, **Then** validation prevents creation with a clear error message.
2. **Given** a user creates a dataset with all required FAIR metadata fields populated, **When** the dataset is saved, **Then** the dataset persists successfully with all metadata intact.
3. **Given** a dataset exists with contributors, dates, descriptions, and identifiers, **When** the dataset is queried, **Then** all related metadata is accessible via proper relationships.
4. **Given** a user sets dataset visibility to PRIVATE, **When** QuerySet method `get_visible()` is called, **Then** the dataset is excluded from results.
5. **Given** a dataset has a DOI identifier, **When** the dataset metadata is accessed, **Then** the DOI is properly formatted and accessible.

---

### User Story 2 - Enhanced Dataset Admin Interface (Priority: P1)

As a portal administrator, I want a comprehensive Django admin interface for datasets that provides search, filtering, bulk operations, inline metadata editing, and clear visibility controls so that I can efficiently manage datasets and their metadata without writing custom code.

**Why this priority**: Admin interface is the primary tool for portal administrators to manage data. A well-designed admin directly impacts operational efficiency.

**Independent Test**: Can be fully tested by accessing the admin interface, performing searches, applying filters, editing datasets with inline metadata, and executing bulk operations. Success is demonstrated when all admin operations work correctly and efficiently.

**Acceptance Scenarios**:

1. **Given** I am in the dataset admin list view, **When** I search by dataset name or UUID, **Then** matching datasets appear in results.
2. **Given** I am viewing a dataset in the admin, **When** I add a description inline without saving the dataset, **Then** the description form appears and allows data entry.
3. **Given** I have multiple datasets selected in the admin list, **When** I execute a bulk action to change visibility, **Then** all selected datasets update their visibility status.
4. **Given** I am editing a dataset, **When** I use the project field Select2 widget, **Then** I can search and select projects with autocomplete.
5. **Given** I am viewing the dataset admin list, **When** I apply filters for project or license, **Then** the list updates to show only matching datasets.
6. **Given** I am editing a dataset with related literature, **When** I use the ManyToMany widget, **Then** I can add/remove literature items efficiently.

---

### User Story 3 - Robust Dataset Forms with User Context (Priority: P2)

As a developer implementing dataset creation/edit views, I want dataset forms that automatically filter querysets based on user permissions, provide clear help text, use appropriate widgets, and handle optional fields gracefully so that users have an intuitive data entry experience.

**Why this priority**: Forms are the primary user interface for dataset creation and editing. Quality forms directly impact user experience and data quality.

**Independent Test**: Can be fully tested by instantiating forms with different user contexts, rendering them, and submitting valid/invalid data. Success is demonstrated when forms properly filter choices, display help text, and validate correctly.

**Acceptance Scenarios**:

1. **Given** an authenticated user with access to 3 projects creates a dataset, **When** the form renders, **Then** the project field shows only those 3 projects as choices.
2. **Given** a form is rendered for a new dataset, **When** no license is selected, **Then** the default license (CC BY 4.0) is pre-selected.
3. **Given** a user fills the dataset form with a name and project, **When** the form is submitted, **Then** validation passes and the dataset is created.
4. **Given** a user fills the dataset form with an invalid DOI format, **When** the form is submitted, **Then** validation fails with a clear error message about DOI format requirements.
5. **Given** a user is editing an existing dataset, **When** the form renders, **Then** all current field values are pre-populated correctly.
6. **Given** a user without authentication accesses the form, **When** the form renders, **Then** the project queryset is empty or shows only public projects.

---

### User Story 4 - Advanced Dataset Filtering & Search (Priority: P2)

As a portal user browsing datasets, I want to filter datasets by project, license, visibility, date ranges, and search by name/keywords so that I can quickly find relevant datasets without browsing through all results.

**Why this priority**: Effective filtering is essential for usability as dataset collections grow. Poor filtering forces users to manually scan results.

**Independent Test**: Can be fully tested by creating datasets with various attributes and applying different filter combinations. Success is demonstrated when filters correctly narrow results and combine logically.

**Acceptance Scenarios**:

1. **Given** multiple datasets exist with different licenses, **When** I filter by a specific license, **Then** only datasets with that license appear in results.
2. **Given** datasets exist across multiple projects, **When** I filter by a specific project, **Then** only datasets from that project appear in results.
3. **Given** datasets have different visibility settings, **When** I filter by PUBLIC visibility, **Then** only public datasets appear in results.
4. **Given** datasets were created on different dates, **When** I filter by a date range, **Then** only datasets added within that range appear in results.
5. **Given** I search for a keyword that appears in dataset names, **When** the filter is applied, **Then** all datasets with that keyword in the name appear in results.
6. **Given** I apply multiple filters (project AND license), **When** the filters are applied together, **Then** only datasets matching ALL criteria appear in results.

---

### User Story 5 - Optimized Dataset QuerySets (Priority: P3)

As a developer building dataset views, I want optimized QuerySet methods that prefetch related data, filter by visibility, and handle common queries efficiently so that my views perform well even with large dataset collections.

**Why this priority**: QuerySet optimization prevents N+1 query problems and improves performance. While important, it can be added after core CRUD operations work.

**Independent Test**: Can be fully tested by executing QuerySet methods with Django Debug Toolbar or query logging enabled. Success is demonstrated when complex queries execute efficiently with minimal database hits.

**Acceptance Scenarios**:

1. **Given** 100 datasets exist with projects and contributors, **When** I call `Dataset.objects.with_related().all()`, **Then** all data loads with 3 or fewer database queries total (1 for datasets, 1-2 for prefetch).
2. **Given** datasets have different visibility settings, **When** I call `Dataset.objects.get_visible()`, **Then** only PUBLIC datasets are returned.
3. **Given** I need dataset contributor information, **When** I call `Dataset.objects.with_contributors()`, **Then** contributor data is prefetched without additional queries per dataset.
4. **Given** I chain multiple QuerySet methods, **When** I call `Dataset.objects.with_related().get_visible()`, **Then** both filters apply correctly and efficiently.

---

### Edge Cases

- **Project deletion with datasets**: ✅ **RESOLVED** - Use PROTECT behavior. Projects with attached datasets cannot be deleted. Orphaned datasets (project=null) are permitted but not encouraged.
- **Duplicate dataset names**: Should dataset names be unique within a project, globally unique, or allowed to have duplicates? Current code allows duplicates - is this intentional?
- **Visibility inheritance**: When a project becomes private, should all its datasets automatically become private? Current code does not enforce this.
- **License changes after publication**: Can a dataset license be changed after it has a DOI/is published? Current code allows this - should it be prevented or warned?
- **Related literature deletion**: What happens when a literature item referenced by datasets is deleted? Need consistent CASCADE/SET_NULL behavior across reference field and related_literature ManyToMany.
- **Empty datasets**: Can a dataset exist with no samples or measurements? Current code allows this via `has_data` property - when should empty datasets be prevented/flagged?
- **Contributor role validation**: Are dataset contributor roles properly validated against the CONTRIBUTOR_ROLES vocabulary? Current code doesn't explicitly validate.
- **Date type validation**: Are dataset date types properly validated against the DATE_TYPES vocabulary? Current code doesn't explicitly validate.
- **Metadata description types**: Are description types validated against DESCRIPTION_TYPES vocabulary? Need explicit validation.
- **UUID collision**: While extremely unlikely with ShortUUID, what happens if a UUID collision occurs? Current code may fail silently on unique constraint.
- **Image aspect ratio**: ✅ **RESOLVED** - Research and define optimal aspect ratio for dataset images that works well in card displays and HTML meta tags. Consider responsive design requirements.
- **Cross-relationship filter performance**: ✅ **NEW** - Filtering by descriptions and dataset dates requires joins across relationships. Research performance implications for large datasets and consider indexing strategies.
- **Dynamic inline form limits**: ✅ **NEW** - Inline forms must dynamically adjust based on vocabulary size. What happens if vocabulary is extended after deployment? How do existing forms adapt?
- **Generic search field scope**: ✅ **NEW** - Which fields should the generic search match against? Need to define searchable field set and consider performance with ILIKE queries on large datasets.
- **Literature relationship types**: ✅ **NEW** - Research DataCite relationship type standards and determine which types are most relevant for dataset-to-literature relationships. Design intermediate model schema.

## Clarifications

### Session 2026-01-15

- Q: Should datasets be deleted when their project is deleted (CASCADE)? → A: No, use PROTECT behavior. Projects with datasets cannot be deleted. Orphaned datasets (project=null) are permitted but not encouraged.
- Q: What should the default license be? → A: CC BY 4.0 (Creative Commons Attribution 4.0 International)
- Q: How should DOI be supported? → A: Via DatasetIdentifier model with identifier_type='DOI', not via reference field. The reference field is for linking to literature items/dataset publications.
- Q: Should literature relationships be simple ManyToMany? → A: No, use intermediate model with relationship types following DataCite standards (IsCitedBy, Cites, IsSupplementTo, etc.)
- Q: Are timestamps for sorting or auditing? → A: Primarily for auditing, not necessarily for sorting.
- Q: What image requirements exist? → A: Define aspect ratio suitable for card displays and HTML meta tags. Research optimal ratio for responsive layouts.
- Q: Should default queryset include private datasets? → A: No, privacy-first. Default should exclude PRIVATE datasets. Provide explicit get_all() or with_private() method when private datasets are needed.
- Q: Are with_related() and with_contributors() hard requirements? → A: No, they are suggestions (SHOULD not MUST). Plan based on actual usage patterns.
- Q: Should autocomplete only apply to project field? → A: No, use Select2/autocomplete on ALL applicable fields (ForeignKey, ManyToMany) for consistent UX.
- Q: Should help text be internationalized? → A: Yes, wrap in gettext_lazy(). Help text should be form-specific, not just copied from model.
- Q: Where should request parameter pattern live? → A: Consider moving to base form class if widely applicable across forms.
- Q: Should filters include added/modified date ranges? → A: No, not particularly helpful. Focus on other filters.
- Q: Should filters have individual text field filters? → A: No, implement generic search field that matches across multiple CharField/TextField fields.
- Q: Should filters support description and date filtering? → A: Yes, via cross-relationship filters. Research performance implications.
- Q: Does Django admin have built-in autocomplete? → A: Yes, leverage built-in functionality unless custom queryset filtering requires explicit configuration.
- Q: What fieldset names should be used? → A: Research and propose improved names beyond placeholders.
- Q: Should admin have bulk visibility change actions? → A: No, too dangerous - could accidentally expose private datasets. Bulk metadata export is acceptable.
- Q: Should inline forms have hard-coded limits? → A: No, dynamically calculate based on vocabulary size (description types, date types).
- Q: How should permissions be structured? → A: Role-based using FairDM roles (Dataset.CONTRIBUTOR_ROLES). Map roles to permissions and use django-guardian for object-level enforcement.

## Requirements *(mandatory)*

### Functional Requirements

#### Model & Data Integrity

- **FR-001**: Dataset model MUST enforce that `name` field is required and non-empty (max 200 characters recommended).
- **FR-002**: Dataset model MUST support all FAIR metadata through related models: descriptions (DatasetDescription), dates (DatasetDate), identifiers (DatasetIdentifier), and contributors (Contribution).
- **FR-003**: Dataset model MUST provide a unique, stable identifier via ShortUUID with prefix "d" for external referencing.
- **FR-004**: Dataset model MUST support visibility control (PUBLIC, INTERNAL, PRIVATE) with default of PRIVATE for data protection.
- **FR-005**: Dataset model MUST support optional project association with PROTECT delete behavior to prevent accidental dataset deletion when projects are deleted. Projects with attached datasets cannot be deleted until datasets are reassigned or removed. Orphaned datasets (project=null) are permitted.
- **FR-006**: Dataset model MUST support optional license via LicenseField with default of CC BY 4.0 (Creative Commons Attribution 4.0 International).
- **FR-007**: Dataset model MUST support DOI via DatasetIdentifier model with identifier_type='DOI' for unique external identification of published datasets.
- **FR-008**: Dataset model MUST support ManyToMany relationship to related literature with intermediate model specifying relationship types following DataCite standards (e.g., IsCitedBy, Cites, IsSupplementTo, IsSupplementedBy).
- **FR-009**: DatasetDescription model MUST validate description_type against DESCRIPTION_TYPES vocabulary from FairDMDescriptions.
- **FR-010**: DatasetDate model MUST validate date_type against DATE_TYPES vocabulary from FairDMDates.
- **FR-011**: DatasetIdentifier model MUST validate identifier_type against IDENTIFIER_TYPES vocabulary from FairDMIdentifiers.
- **FR-012**: Dataset model MUST include timestamps (added, modified) primarily for audit trail purposes.
- **FR-013**: Dataset model MUST support keyword tagging for search and categorization.
- **FR-014**: Dataset model MUST support optional image field for visual identification with defined aspect ratio suitable for card displays and HTML meta tags (research optimal ratio for responsive card layouts).

#### QuerySet Methods

- **FR-015**: Dataset model default manager MUST exclude PRIVATE datasets by default (privacy-first approach). DatasetQuerySet SHOULD provide `get_all()` or `with_private()` method to explicitly include private datasets when needed.
- **FR-016**: DatasetQuerySet SHOULD provide `with_related()` method that prefetches project and contributors for optimization (not mandatory, but recommended based on actual usage patterns).
- **FR-017**: DatasetQuerySet SHOULD provide `with_contributors()` method that prefetches only contributors for optimization (not mandatory, but recommended based on actual usage patterns).
- **FR-018**: Dataset model default manager MUST use DatasetQuerySet to make custom methods available on Dataset.objects.

#### Forms

- **FR-019**: DatasetForm MUST include fields for name, image, project, license, and DOI with appropriate widgets.
- **FR-020**: DatasetForm MUST use Select2Widget or django-autocomplete-light with autocomplete for ALL applicable fields (ForeignKey, ManyToMany) for improved UX, not just project selection.
- **FR-021**: DatasetForm MUST support "add another" functionality on project field allowing inline project creation.
- **FR-022**: DatasetForm MUST filter project queryset to show only projects the authenticated user has access to.
- **FR-023**: DatasetForm MUST default license field to CC BY 4.0 (Creative Commons Attribution 4.0 International).
- **FR-024**: DatasetForm MUST provide clear, helpful help_text for all fields wrapped in gettext_lazy() for internationalization. Help text SHOULD be form-specific, not just copied from model field help_text.
- **FR-025**: DatasetForm MUST accept optional `request` parameter in `__init__` to access user context for queryset filtering. Consider moving this pattern to base form class if widely applicable.
- **FR-026**: DatasetForm MUST properly handle both creation and update scenarios.

#### Filters

- **FR-027**: DatasetFilter MUST extend BaseListFilter providing consistent filtering interface.
- **FR-028**: DatasetFilter MUST support filtering by license (exact match).
- **FR-029**: DatasetFilter MUST support filtering by project (exact match or choice).
- **FR-030**: DatasetFilter MUST support filtering by visibility level.
- **FR-031**: DatasetFilter MUST support filtering by description content via cross-relationship filter (research feasibility and performance implications).
- **FR-032**: DatasetFilter MUST support filtering by dataset date types via cross-relationship filter (e.g., filter by publication date, collection date).
- **FR-033**: DatasetFilter SHOULD use generic search field that matches across multiple CharField/TextField fields rather than individual text filters for each field.
- **FR-034**: DatasetFilter relies on django-filter's default AND logic for combining multiple filters (explicit specification not required).

#### Admin Interface

- **FR-035**: DatasetAdmin MUST provide search by name and UUID for quick dataset location.
- **FR-036**: DatasetAdmin MUST provide list_display showing name, added, and modified dates.
- **FR-037**: DatasetAdmin MUST provide list_filter for project, license, visibility, and date ranges.
- **FR-038**: DatasetAdmin MUST include inline editors for DatasetDescription and DatasetDate.
- **FR-039**: DatasetAdmin SHOULD leverage Django admin's built-in autocomplete functionality for ForeignKey and ManyToMany fields unless custom queryset filtering per-dataset requires explicit Select2Widget configuration.
- **FR-040**: DatasetAdmin MUST organize fields into logical fieldsets with clear, descriptive names (research and propose improved fieldset organization beyond placeholder names).
- **FR-041**: DatasetAdmin MUST NOT provide bulk visibility change actions to prevent accidental exposure of private datasets. Bulk export metadata operations are acceptable.
- **FR-042**: DatasetAdmin MUST make UUID and timestamps readonly to prevent accidental modification.
- **FR-043**: DatasetAdmin MUST dynamically calculate inline form limits based on available description types and date types from vocabularies rather than hard-coded maximums. Inline forms should match the number of available type choices.

#### Permissions

- **FR-044**: Dataset model MUST define custom permissions for FAIR data operations: view_dataset, add_dataset, change_dataset, delete_dataset, import_data.
- **FR-045**: Dataset permissions MUST be role-based using FairDM roles (Dataset.CONTRIBUTOR_ROLES). Permissions MUST map to roles (e.g., DatasetViewer, DatasetEditor, DatasetManager) and integrate with django-guardian for object-level permission enforcement.

#### Testing Requirements

- **FR-046**: Dataset model MUST have unit tests for: model creation, validation rules, field constraints, method behaviors, and property calculations.
- **FR-047**: DatasetQuerySet methods MUST have unit tests for: privacy-first default behavior, get_all()/with_private() methods, with_related(), with_contributors(), and query chaining.
- **FR-048**: DatasetForm MUST have unit tests for: form validation, queryset filtering, default values, field widgets, request context handling, and gettext_lazy wrapping.
- **FR-049**: DatasetFilter MUST have unit tests for: each filter field, cross-relationship filters (descriptions, dates), generic search functionality, and edge cases.
- **FR-050**: DatasetAdmin MUST have integration tests for: search, filters, inline editing, dynamic inline limits, and widget functionality.
- **FR-051**: All tests MUST use factory-boy factories from fairdm.factories for test data generation.
- **FR-052**: Test organization MUST follow the testing strategy: unit tests in tests/unit/core/, integration tests in tests/integration/core/.

### Key Entities

- **Dataset**: Core model representing a collection of samples, measurements, and metadata in the FairDM hierarchy.
- **DatasetDescription**: Related model storing typed descriptions for datasets using controlled vocabulary.
- **DatasetDate**: Related model storing typed dates for datasets using controlled vocabulary.
- **DatasetIdentifier**: Related model storing typed identifiers (DOI, etc.) for datasets using controlled vocabulary.
- **DatasetLiteratureRelation**: Intermediate model for Dataset-to-LiteratureItem relationships specifying DataCite relationship types (to be created).
- **DatasetQuerySet**: Custom QuerySet providing optimized query methods for dataset retrieval with privacy-first default.
- **DatasetForm**: ModelForm for dataset creation/editing with user context awareness and internationalized help text.
- **DatasetFilter**: FilterSet for dataset searching and filtering including cross-relationship filters.
- **DatasetAdmin**: Django admin configuration for dataset management interface with dynamic inline forms.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All dataset CRUD operations complete with proper validation and error messages within 2 seconds for typical use cases.
- **SC-002**: Dataset list view with 100 datasets and filters applied loads in under 1 second with optimized querysets.
- **SC-003**: Dataset model achieves 90%+ test coverage with meaningful tests of critical paths and edge cases.
- **SC-004**: Dataset forms provide clear validation feedback with user-friendly error messages for all invalid inputs.
- **SC-005**: Dataset admin interface allows administrators to search, filter, and edit datasets without writing custom code.
- **SC-006**: DatasetQuerySet optimization reduces database queries by 80%+ compared to naive ORM usage when loading datasets with related data.
- **SC-007**: All mandatory FAIR metadata fields are enforceable at the model level preventing incomplete dataset creation.
- **SC-008**: Dataset filter combinations work correctly in 100% of test cases without unexpected results.
