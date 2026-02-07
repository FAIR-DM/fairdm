# Feature Specification: Core Sample Model Enhancement

**Feature Branch**: `007-core-samples`
**Created**: January 16, 2026
**Status**: Draft
**Input**: User description: "Feature 007-core-samples will focus on cleaning up and enhancing the fairdm.core.sample app. We will go through models, modelmanagers, forms, filters and admin, making sure to identify feature holes, testing requirements and enhancements that support fair data and portal useability. Client side integration (e.g. list views, detail views, api, etc) are out of scope for this feature and will be deferred to later specs. The Sample model is intended to reflect the IGSN (International Generic Sample Number) metadata schema as closely as possible. Note however that the IGSN metadata is currently being redesigned as part of an ongoing project which we will need to monitor. For now, we will keep the Sample model simple but functional. We can update it in future releases to address updated IGSN metadata. IMPORTANT: The Sample model is a base polymorphic model from which ALL FairDM samples are derived. This means it integrates tightly with the FairDM registry system. Also, we should focus on providing basic mixin for forms, filters, etc, that provide core Sample-related functionality, from which developers of specific samples types can mixin to their own form classes. e.g. class SampleForm(): ... class RockSampleForm(SampleForm): ..."

## Clarifications

### Session 2026-01-16

- Q: Should there be a detailed "Dataset Creator Manages Sample Lifecycle" user story? → A: No, this is beyond scope. Focus on model, forms, filters, and admin as in Feature 006 (datasets).
- Q: Should User Story 2 refer to "portal administrator" or "portal developer"? → A: Portal developer (not administrator) defines custom sample types.
- Q: Does User Story 2 overlap with Feature 004 (registry system)? → A: Yes, need to ensure we're not duplicating work from the registry spec and properly reference/build upon it.
- Q: Is User Story 3 complex enough to require research? → A: Yes, sample relationships can be very complex in some cases and will require research into proper implementation patterns.
- Q: How important is the base form/filter inheritance? → A: Very important for proper integration - developers must inherit from correct base forms/filters to get all basic functionality defined in the core app.

## User Scenarios & Testing

### User Story 1 - Sample Model Polymorphism & Registry Integration (Priority: P1)

As a portal developer using FairDM, I want the Sample model to support polymorphic inheritance and seamlessly integrate with the FairDM registry (Feature 004) so that I can define domain-specific sample types that automatically get forms, filters, tables, and admin interfaces without duplicating registry functionality.

**Why this priority**: Polymorphic sample support and registry integration are fundamental to FairDM's extensibility model. This must work correctly or the framework cannot support different research domains.

**Independent Test**: Can be fully tested by defining custom sample models inheriting from Sample, registering them via Feature 004 registry patterns, and verifying polymorphic queries and auto-generated components work correctly. Success is demonstrated when custom sample types integrate seamlessly without manual form/filter/admin creation.

**Acceptance Scenarios**:

1. **Given** I define a new sample type inheriting from Sample (e.g., RockSample with mineral_type field), **When** I register it using Feature 004 registry patterns, **Then** the registry auto-generates appropriate forms, filters, tables, and admin interfaces.
2. **Given** I have multiple sample types registered (RockSample, WaterSample), **When** I query Sample.objects.all(), **Then** I receive polymorphic results including both base Sample instances and typed subclass instances.
3. **Given** I have a custom sample type with additional fields, **When** I create instances via the auto-generated form, **Then** both base Sample fields and custom fields are properly handled.
4. **Given** I register a custom sample without providing custom form/filter classes, **When** the registry auto-generates defaults, **Then** the generated components work correctly for CRUD operations.
5. **Given** I have polymorphic sample types in the database, **When** I access admin interface, **Then** each sample type displays with its appropriate admin configuration.

---

### User Story 2 - Enhanced Sample Admin Interface (Priority: P1)

As a portal administrator, I want a comprehensive Django admin interface for samples that provides search, filtering, inline metadata editing, and proper handling of polymorphic sample types so that I can efficiently manage samples and their metadata without writing custom code.

**Why this priority**: Admin interface is the primary tool for portal administrators to manage sample data. A well-designed admin directly impacts operational efficiency.

**Independent Test**: Can be fully tested by accessing the admin interface, performing searches, applying filters, editing samples with inline metadata, and working with different polymorphic sample types. Success is demonstrated when all admin operations work correctly and efficiently for both base Sample and custom sample types.

**Acceptance Scenarios**:

1. **Given** I am in the sample admin list view, **When** I search by sample name, local_id, or UUID, **Then** matching samples appear in results.
2. **Given** I am viewing a sample in the admin, **When** I add a description inline without saving the sample, **Then** the description form appears and allows data entry.
3. **Given** I am editing a sample, **When** I use the dataset field Select2 widget, **Then** I can search and select datasets with autocomplete.
4. **Given** I am viewing the sample admin list, **When** I apply filters for dataset, status, or location, **Then** the list updates to show only matching samples.
5. **Given** I am editing a sample with relationships, **When** I use the relationship inline, **Then** I can add/remove sample relationships efficiently.
6. **Given** I have multiple polymorphic sample types, **When** I view the admin list, **Then** each sample displays with its appropriate type identifier.

---

### User Story 3 - Robust Sample Forms with Dataset Context (Priority: P2)

As a developer implementing sample creation/edit views, I want sample forms that automatically filter querysets based on dataset context, provide clear help text, use appropriate widgets, handle polymorphic types, and provide base mixins for custom sample forms so that users have an intuitive data entry experience and I can reuse common functionality.

**Why this priority**: Forms are the primary user interface for sample creation and editing. Quality forms with reusable mixins directly impact user experience and developer productivity.

**Independent Test**: Can be fully tested by instantiating forms for different sample types with various dataset contexts, rendering them, and submitting valid/invalid data. Success is demonstrated when forms properly filter choices, handle polymorphic types, display help text, and validate correctly.

**Acceptance Scenarios**:

1. **Given** an authenticated user with access to specific datasets creates a sample, **When** the form renders, **Then** the dataset field shows only accessible datasets as choices.
2. **Given** a developer creates a custom sample form, **When** the form inherits from SampleFormMixin, **Then** common sample fields (dataset, status, location) are pre-configured with appropriate widgets.
3. **Given** a user fills the sample form with name and dataset, **When** the form is submitted, **Then** validation passes and the sample is created with correct polymorphic type.
4. **Given** a user fills the sample form with an invalid location format, **When** the form is submitted, **Then** validation fails with a clear error message about location format requirements.
5. **Given** a user is editing an existing sample, **When** the form renders, **Then** all current field values including polymorphic-specific fields are pre-populated correctly.
6. **Given** a form is rendered for a new sample, **When** no status is selected, **Then** the default status (e.g., "available") is pre-selected.

---

### User Story 4 - Advanced Sample Filtering & Search (Priority: P2)

As a portal user browsing samples, I want to filter samples by dataset, status, location, date ranges, polymorphic type, and search by name/local_id/keywords so that I can quickly find relevant samples without browsing through all results, with base filter mixins available for custom sample type filters.

**Why this priority**: Effective filtering is essential for usability as sample collections grow. Base filter mixins reduce developer effort for custom sample types.

**Independent Test**: Can be fully tested by creating samples of various types with different attributes and applying different filter combinations. Success is demonstrated when filters correctly narrow results, handle polymorphic types, combine logically, and mixins provide reusable functionality.

**Acceptance Scenarios**:

1. **Given** multiple samples exist with different statuses, **When** I filter by a specific status, **Then** only samples with that status appear in results.
2. **Given** samples exist across multiple datasets, **When** I filter by a specific dataset, **Then** only samples from that dataset appear in results.
3. **Given** samples have location data, **When** I filter by a bounding box or radius, **Then** only samples within that geographic area appear in results.
4. **Given** samples of different polymorphic types exist, **When** I filter by sample type (e.g., RockSample), **Then** only samples of that specific type appear in results.
5. **Given** I search for a keyword that appears in sample names or local_ids, **When** the filter is applied, **Then** all samples with that keyword appear in results.
6. **Given** I apply multiple filters (dataset AND status), **When** the filters are applied together, **Then** only samples matching ALL criteria appear in results.
7. **Given** I am developing a custom sample type filter, **When** I inherit from SampleFilterMixin, **Then** I have pre-configured filters for common sample fields.

---

### User Story 5 - Sample Relationships & Provenance (Priority: P3)

As a researcher, I want to define typed relationships between samples (parent-child, derived-from, split-from) to track sample provenance and hierarchies, so that I can maintain accurate records of sample processing and sub-sampling for scientific reproducibility.

**Why this priority**: Sample provenance and relationships are critical for scientific reproducibility, but basic sample CRUD should work before relationships are fully implemented. This feature requires research into complex relationship patterns.

**Independent Test**: Can be fully tested by creating parent samples, establishing various relationship types to child samples, and querying relationships bidirectionally. Success is demonstrated when relationships are correctly stored, queried efficiently, and prevent invalid circular references.

**Acceptance Scenarios**:

1. **Given** I have an existing sample (parent), **When** I create a new sample as a child with relationship type "derived-from", **Then** the typed relationship is recorded and queryable.
2. **Given** I have related samples, **When** I view the parent sample, **Then** I see all child samples listed with their relationship types.
3. **Given** I have a child sample, **When** I view its details, **Then** I can navigate to its parent sample with the relationship type displayed.
4. **Given** I have sample hierarchies, **When** I query for all descendants of a parent, **Then** I receive the complete tree of related samples efficiently.
5. **Given** I attempt to create a circular relationship, **When** the relationship is validated, **Then** the system prevents the circular reference with a clear error message.

---

### User Story 6 - Optimized Sample QuerySets (Priority: P3)

As a developer building sample views, I want optimized QuerySet methods that prefetch related data, handle polymorphic queries efficiently, and provide common query patterns so that my views perform well even with large sample collections of mixed types.

**Why this priority**: QuerySet optimization prevents N+1 query problems and improves performance. While important, it can be added after core CRUD operations work.

**Independent Test**: Can be fully tested by executing QuerySet methods with Django Debug Toolbar or query logging enabled. Success is demonstrated when complex polymorphic queries execute efficiently with minimal database hits.

**Acceptance Scenarios**:

1. **Given** 1000 samples of mixed polymorphic types exist with datasets and contributors, **When** I call `Sample.objects.with_related().all()`, **Then** all data loads with minimal database queries (optimized for polymorphic types).
2. **Given** I need sample metadata and relationships, **When** I call `Sample.objects.with_metadata()`, **Then** descriptions, dates, identifiers, and contributors are prefetched without additional queries per sample.
3. **Given** I query polymorphic samples, **When** I use `.select_subclasses()`, **Then** the correct subclass instances are returned with their type-specific fields.
4. **Given** I chain multiple QuerySet methods, **When** I call `Sample.objects.with_related().filter(status='available')`, **Then** both optimizations and filters apply correctly and efficiently.

---

### Edge Cases

- **Dataset deletion with samples**: Should samples be deleted when their dataset is deleted (CASCADE) or should deletion be prevented (PROTECT)? Current spec uses CASCADE - verify this is intentional for sample lifecycle.
- **Duplicate local_id values**: Should local_id be unique within a dataset, globally unique, or allowed to have duplicates? Current code allows duplicates as local_id is dataset-creator specific.
- **Sample status transitions**: Status transitions are unrestricted - samples CAN transition from "destroyed" back to "available" or any other status. No state machine validation required.
- **Polymorphic type changes**: Base Sample entries ARE NOT ALLOWED - only subclass instances (RockSample, WaterSample, etc.) can be created. Type conversion between subclasses is deferred to future feature (would require data migration with loss warnings).
- **Location data validation**: Deferred to future location feature. Basic foreign key to fairdm_location.Point is sufficient for this feature.
- **Sample relationship cycles**: Circular relationship prevention implementation is deferred due to complexity. Basic direct-cycle prevention required, but deep traversal depth limits require further research.
- **IGSN identifier validation**: Should IGSN identifiers be validated against format rules? Should live API validation be attempted?
- **Empty samples**: Can samples exist without any measurements? When should this be flagged or prevented?
- **Polymorphic queryset performance**: With many sample types, polymorphic queries may hit performance issues. Research optimization strategies.
- **Sample image requirements**: Should sample images have specific aspect ratios or size limits? Consider responsive display requirements.
- **Cross-relationship filter performance**: Filtering by descriptions and dates requires joins. Research performance implications for large sample sets.
- **Generic search field scope**: Which fields should generic search match against? Define searchable field set considering performance.
- **Mixin inheritance order**: For forms/filters inheriting from mixins, what's the correct MRO (Method Resolution Order)? Document proper inheritance patterns.
- **Registry override patterns**: When should developers provide custom forms/filters vs. relying on auto-generation? Define decision criteria.

## Requirements

### Functional Requirements

#### Model & Data Integrity

- **FR-001**: Sample model MUST inherit from BasePolymorphicModel to support domain-specific sample types via django-polymorphic. Direct instantiation of base Sample model MUST be prevented - only polymorphic subclass instances (RockSample, WaterSample, etc.) can be created. Forms and admin MUST enforce this constraint.
- **FR-002**: Sample model MUST include unique UUID identifier with 's' prefix for stable internal referencing using ShortUUID.
- **FR-003**: Sample model MUST support local_id field for dataset-creator specified identifiers (duplicates allowed across datasets).
- **FR-004**: Sample model MUST include status field using controlled vocabulary from FairDMSampleStatus (e.g., available, in_use, stored, destroyed, unknown). Sample model SHOULD include material field to specify primary material/substance (e.g., rock, water, soil, sediment, tissue, air) using controlled vocabulary where available.
- **FR-005**: Sample model MUST support foreign key relationship to Dataset with CASCADE delete behavior (samples deleted when parent dataset deleted).
- **FR-006**: Sample model MUST support optional location field linking to spatial point data (fairdm_location.Point).
- **FR-007**: Sample metadata models (SampleDescription, SampleDate, SampleIdentifier) MUST use concrete ForeignKey relationships to Sample for query performance and type safety. Only contributors MUST use GenericRelation (Contribution) for polymorphic contributor support across all core models.
- **FR-008**: SampleRelation model MUST support typed relationships between samples using controlled vocabulary for relationship types (parent-child, derived-from, split-from, etc.).
- **FR-009**: SampleRelation model MUST support bidirectional queries (parent→children, child→parent) efficiently.
- **FR-010**: SampleRelation model MUST prevent circular relationships through validation.
- **FR-011**: Sample model MUST support keywords from controlled vocabularies and free-text tags for categorization.
- **FR-012**: Sample model MUST include timestamps (added, modified) for audit trail purposes.
- **FR-013**: Sample model MUST support optional image field for visual documentation.
- **FR-014**: SampleDescription model MUST validate description_type against DESCRIPTION_TYPES vocabulary from FairDMDescriptions.
- **FR-015**: SampleDate model MUST validate date_type against DATE_TYPES vocabulary from FairDMDates.
- **FR-016**: SampleIdentifier model MUST validate identifier_type against IDENTIFIER_TYPES vocabulary from FairDMIdentifiers, including IGSN type with format validation (IGSN Handle pattern: 10273/[A-Z0-9]{9,}, e.g., 10273/ABCD123456789).
- **FR-017**: Sample model MUST align with IGSN metadata schema for core fields (name, type, location, material) to support future IGSN integration.

As a researcher, I need to define relationships between samples (parent-child, derived-from, split-from) to track sample provenance and hierarchies, so that I can maintain accurate records of sample processing and sub-sampling.

**Why this priority**: Sample provenance and relationships are critical for scientific reproducibility, but the system can function with basic samples before relationships are fully implemented.

**Independent Test**: Can be tested by creating a parent sample, splitting it into child samples, and verifying the relationship is bidirectional (parent lists children, child references parent).

**Acceptance Scenarios**:

1. **Given** I have an existing sample (parent), **When** I create a new sample as a child of the parent, **Then** the parent-child relationship is recorded and queryable
2. **Given** I have related samples, **When** I view the parent sample, **Then** I see all child samples listed with their relationship types
3. **Given** I have a child sample, **When** I view its details, **Then** I can navigate to its parent sample
4. **Given** I have complex sample hierarchies, **When** I query for all descendants of a parent, **Then** I receive the complete tree of related samples

---

### User Story 4 - Dataset Creator Adds Rich Sample Metadata (Priority: P2)

As a dataset creator, I need to attach multiple descriptions, dates, identifiers, and contributor records to samples, with limited administrator oversight that includes audit trails and protections against inappropriate modifications, so that samples are properly documented and support FAIR data principles while maintaining data integrity.

**Why this priority**: Rich metadata is essential for FAIR compliance and discoverability, but basic sample CRUD operations should work before all metadata types are fully integrated. Administrator access must be controlled similar to User Story 1.

**Independent Test**: Can be tested by:

1. Dataset creator adding multiple metadata types to samples
2. Administrator attempting to modify metadata on published samples and verifying audit trail
3. Verifying all metadata is displayed and searchable
4. Confirming checks prevent administrators from editing data they shouldn't

**Acceptance Scenarios**:

1. **Given** I am a dataset creator editing a sample, **When** I add multiple descriptions with different types (abstract, methods), **Then** each description is stored with its type, my user ID, and timestamp
2. **Given** I am a dataset creator editing a sample, **When** I add key dates (collection_date, analysis_date), **Then** dates are stored and can be used for filtering and timeline views
3. **Given** I am an administrator, **When** I attempt to modify existing sample metadata on a published sample, **Then** the system records an audit log entry with my user ID, timestamp, changed fields, and requires a justification note
4. **Given** I am registering a sample, **When** I add an IGSN identifier, **Then** the identifier is validated, stored, and displayed with appropriate formatting and external links
5. **Given** I am documenting a sample, **When** I add contributors with roles (collector, analyst), **Then** contributors are linked to the sample with their specific roles preserved and proper attribution

---

### User Story 5 - Developer Reuses Sample Form/Filter Components (Priority: P3)

As a portal developer, I need base form and filter mixins that provide common sample functionality (dataset selection, status filtering, location handling), so that I can quickly create custom forms and filters for my sample types without reimplementing common patterns.

**Why this priority**: Developer experience improvements that reduce boilerplate code. The system can function without these mixins, but they significantly improve development speed and consistency.

**Independent Test**: Can be tested by creating a custom sample form that inherits from SampleFormMixin, verifying that common fields (dataset, status, location) are pre-configured with appropriate widgets and validation.

**Acceptance Scenarios**:

1. **Given** I am creating a custom sample form, **When** I inherit from SampleFormMixin, **Then** common sample fields have appropriate form widgets (e.g., dataset as autocomplete, status as select)
2. **Given** I am creating a custom filter, **When** I inherit from SampleFilterMixin, **Then** I have pre-configured filters for status, date ranges, and location
3. **Given** I create a custom sample admin, **When** I inherit from SampleAdmin, **Then** I have standard inlines for descriptions, dates, identifiers, contributors, and relationships
4. **Given** I use sample mixins, **When** I add my own fields/filters, **Then** they integrate seamlessly with the inherited base functionality

---

### Edge Cases

- What happens when a sample's dataset is deleted? (CASCADE delete removes samples, or PROTECT prevents deletion)
- How does the system handle duplicate local_id values within the same dataset? (Allow duplicates as local_id is dataset-creator specific)
- What happens when a sample has circular relationships (child is also parent)? (Validation should prevent this)
- How are polymorphic queries handled when a custom sample type is deleted from code but records exist in database? (Polymorphic system should gracefully degrade to base Sample)
- What happens when IGSN identifier is added but external IGSN system is unavailable? (Identifier stored locally, validation warning shown)
- How are sample permissions inherited from parent datasets? (Object-level permissions should cascade from dataset to samples)
- What happens when location data includes altitude/depth information? (Support z-coordinate in location model)

## Requirements

### Functional Requirements

#### QuerySet Methods

- **FR-018**: Sample model default manager MUST use SampleQuerySet to make custom methods available on Sample.objects.
- **FR-019**: SampleQuerySet MUST provide manager methods that optimize performance for common cross-table queries (prefetching related models, metadata, and relationships to prevent N+1 query problems).
- **FR-020**: SampleQuerySet MUST provide manager methods that enable efficient traversal of sample hierarchies and relationships.
- **FR-021**: QuerySet optimization methods MUST reduce database queries by at least 80% compared to naive ORM usage when loading samples with related data.
- **FR-022**: QuerySet methods MUST be chainable and composable with standard Django QuerySet operations (filter, exclude, etc.).

#### Forms

- **FR-023**: SampleForm MUST include fields for name, dataset, status, location, local_id with appropriate widgets.
- **FR-024**: SampleForm MUST use Select2Widget or django-autocomplete-light with autocomplete for ALL applicable fields (ForeignKey, ManyToMany) for improved UX.
- **FR-025**: SampleForm MUST support "add another" functionality on dataset field allowing inline dataset selection.
- **FR-026**: SampleForm MUST filter dataset queryset appropriately based on user context.
- **FR-027**: SampleForm MUST default status field to appropriate default value (e.g., "available").
- **FR-028**: SampleForm MUST provide clear, helpful help_text for all fields wrapped in gettext_lazy() for internationalization. Help text SHOULD be form-specific.
- **FR-029**: SampleForm MUST accept optional `request` parameter in `__init__` to access user context for queryset filtering.
- **FR-030**: SampleForm MUST properly handle both creation and update scenarios for base Sample and polymorphic types.
- **FR-031**: Forms SHOULD provide SampleFormMixin with pre-configured widgets for common sample fields (dataset, status, location) for reuse in custom sample type forms.

#### Filters

- **FR-032**: SampleFilter MUST extend django_filters.FilterSet providing consistent filtering interface.
- **FR-033**: SampleFilter MUST support filtering by status (exact match or multiple choice).
- **FR-034**: SampleFilter MUST support filtering by dataset (exact match or choice).
- **FR-035**: SampleFilter MUST support filtering by polymorphic sample type.
- **FR-036**: SampleFilter MUST support filtering by description content via cross-relationship filter.
- **FR-037**: SampleFilter MUST support filtering by sample date types via cross-relationship filter.
- **FR-038**: SampleFilter MUST provide generic search field that matches across name, local_id, uuid rather than individual text filters for improved user experience.
- **FR-039**: Filters SHOULD provide SampleFilterMixin with common sample filter configurations for reuse in custom sample type filters.

#### Admin Interface

- **FR-040**: SampleAdmin MUST be registered with Django admin site and handle polymorphic sample types correctly.
- **FR-041**: SampleAdmin MUST provide search by name, local_id, and UUID for quick sample location.
- **FR-042**: SampleAdmin MUST provide list_display showing name, dataset, status, polymorphic type, added, and modified dates.
- **FR-043**: SampleAdmin MUST provide list_filter for dataset, status, polymorphic type, and location.
- **FR-044**: SampleAdmin MUST include inline editors for SampleDescription, SampleDate, SampleIdentifier, and SampleRelation.
- **FR-045**: SampleAdmin SHOULD leverage Django admin's built-in autocomplete functionality for ForeignKey and ManyToMany fields.
- **FR-046**: SampleAdmin MUST organize fields into logical fieldsets with clear, descriptive names.
- **FR-047**: SampleAdmin MUST make UUID and timestamps readonly to prevent accidental modification.
- **FR-048**: SampleAdmin MUST dynamically calculate inline form limits based on available description types, date types, and identifier types from vocabularies.
- **FR-049**: SampleAdmin MUST properly handle polymorphic sample types in list and detail views.

#### Registry Integration Requirements

- **FR-050**: Sample model MUST integrate with FairDM registry system (Feature 004) for auto-generation of forms, filters, tables without duplicating Feature 004 functionality.
- **FR-051**: Sample registration MUST leverage existing registry patterns and configuration classes from Feature 004.
- **FR-052**: Registry MUST support polymorphic sample types with type-specific field configurations.
- **FR-053**: Registry MUST auto-generate ModelForm when custom form not provided, using configured fields.
- **FR-054**: Registry MUST auto-generate FilterSet when custom filter not provided, using configured filterset_fields.
- **FR-055**: Registry MUST auto-generate django-tables2 Table when custom table not provided, using configured table_fields.
- **FR-056**: Registry SHOULD generate minimal ModelAdmin when custom admin not provided.
- **FR-057**: SampleFormMixin and SampleFilterMixin MUST be designed to work with registry-generated forms/filters.

#### Permissions

- **FR-058**: Sample model MUST define custom permissions for data operations: view_sample, add_sample, change_sample, delete_sample, import_data.
- **FR-059**: Sample permissions MUST integrate with django-guardian for object-level permission enforcement.
- **FR-060**: Sample permissions MUST inherit from parent dataset permissions by default.

#### Testing Requirements

- **FR-061**: Sample model MUST have unit tests for: model creation, polymorphic behavior, validation rules, field constraints, relationship handling, and property calculations.
- **FR-062**: SampleQuerySet methods MUST have unit tests for: polymorphic queries, with_related(), with_metadata(), by_relationship(), get_descendants(), and query chaining.
- **FR-063**: SampleForm MUST have unit tests for: form validation, polymorphic type handling, queryset filtering, default values, field widgets, request context handling, and gettext_lazy wrapping.
- **FR-064**: SampleFormMixin MUST have unit tests verifying proper widget configuration and field setup for common sample fields.
- **FR-065**: SampleFilter MUST have unit tests for: each filter field, polymorphic type filtering, cross-relationship filters (descriptions, dates), generic search functionality, and edge cases.
- **FR-066**: SampleFilterMixin MUST have unit tests verifying filter configuration and integration with custom sample type filters.
- **FR-067**: SampleAdmin MUST have integration tests for: search, filters, polymorphic type handling, inline editing, dynamic inline limits, and widget functionality.
- **FR-068**: All tests MUST use factory-boy factories from fairdm.factories for test data generation.
- **FR-069**: Test organization MUST mirror source code structure in tests/test_core/test_sample/ as documented in Architecture & Stack Constraints > Testing & Tooling, with unit and integration tests living together in flat structure.
- **FR-070**: Tests MUST verify registry integration works correctly for polymorphic sample types without duplicating Feature 004 test coverage.
- **FR-071**: Sample status transitions MUST be unrestricted - any status can change to any other status without validation (e.g., "destroyed" can become "available"). This edge case MUST have explicit test coverage.

### Key Entities

- **Sample**: Physical or digital specimen/artifact; core polymorphic base with UUID, name, dataset reference, status, location, optional image. Metadata accessed via reverse relations (descriptions, dates, identifiers). Contributors via GenericRelation.
- **SampleDescription**: Typed free-text descriptions with concrete ForeignKey to Sample using controlled vocabulary.
- **SampleDate**: Typed dates linked to sample using controlled vocabulary.
- **SampleIdentifier**: External identifiers (IGSN, DOI) linked to sample with validation.
- **SampleRelation**: Typed relationships between samples supporting provenance tracking with circular reference prevention.
- **SampleQuerySet**: Custom QuerySet providing optimized query methods for polymorphic sample retrieval.
- **SampleForm**: ModelForm for sample creation/editing with dataset context awareness.
- **SampleFormMixin**: Reusable mixin providing common sample form functionality for custom sample types.
- **SampleFilter**: FilterSet for sample searching and filtering including polymorphic type and cross-relationship filters.
- **SampleFilterMixin**: Reusable mixin providing common sample filter functionality for custom sample types.
- **SampleAdmin**: Django admin configuration for sample management interface with polymorphic type handling and dynamic inline forms.
- **Dataset**: Parent container for samples providing context and permissions boundary.
- **Location**: Spatial point data for sample collection sites.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Portal developers can define and register custom polymorphic sample types in under 30 minutes (model definition + registration).
- **SC-002**: Sample CRUD operations complete with proper validation and error messages within 2 seconds for typical use cases.
- **SC-003**: Sample list view with 1000+ samples of mixed polymorphic types and filters applied loads in under 1 second with optimized querysets.
- **SC-004**: Sample model achieves 90%+ test coverage with meaningful tests of critical paths and edge cases including polymorphic behavior.
- **SC-005**: Sample forms provide clear validation feedback with user-friendly error messages for all invalid inputs.
- **SC-006**: Sample admin interface allows administrators to search, filter, and edit samples of any polymorphic type without writing custom code.
- **SC-007**: SampleQuerySet optimization reduces database queries by 80%+ compared to naive ORM usage when loading samples with related data.
- **SC-008**: Sample filter combinations work correctly in 100% of test cases without unexpected results for polymorphic queries.
- **SC-009**: Custom sample type developers report 60% less boilerplate code using provided mixins compared to manual implementation.
- **SC-010**: Registry integration generates functional forms/filters/admin for 95% of custom sample types without requiring custom overrides.

## Assumptions

### Technical Assumptions

- **A-001**: Django-polymorphic is already installed and configured in the framework.
- **A-002**: Django-guardian is already installed and configured for object-level permissions.
- **A-003**: Research-vocabs package is available for controlled vocabulary support.
- **A-004**: ShortUUID package is available for generating unique identifiers.
- **A-005**: Location model (fairdm_location.Point) exists and supports spatial queries.
- **A-006**: FairDM registry system (Feature 004) is already implemented and functional.
- **A-007**: BasePolymorphicModel, AbstractDescription, AbstractDate, AbstractIdentifier abstracts already exist.
- **A-008**: Dataset model (Feature 006) is complete and functional.

### Scope Assumptions

- **A-009**: Client-side views (list views, detail views) are out of scope and handled in future features.
- **A-010**: REST API integration is out of scope for this feature.
- **A-011**: Sample import/export functionality beyond basic admin is out of scope.
- **A-012**: Advanced spatial queries (GIS analysis) are out of scope; basic location filtering is sufficient.
- **A-013**: Workflow management (sample routing, approval processes) is out of scope.

### Standards Assumptions

- **A-014**: IGSN metadata schema version 1.0 is current; redesign project status will be monitored but not blocking.
- **A-015**: IGSN identifier validation can be performed via regex pattern matching; live API validation is optional.
- **A-016**: DataCite identifier types are sufficient for external identifier support.

## Dependencies

### Internal Dependencies

- **D-001**: FairDM registry system must be functional and tested (Feature 004) - CRITICAL: Polymorphic sample integration builds directly on Feature 004 patterns.
- **D-002**: Dataset model must be complete with permissions system (Feature 006).
- **D-003**: Contributor models (Person, Organization) and Contribution through-model with GenericRelation support must exist.
- **D-004**: Location models must be available (fairdm_location app).
- **D-005**: Research vocabularies for sample status, description types, date types, identifier types, relationship types must be defined.

### External Dependencies

- **D-006**: Django-polymorphic package (v3.1+)
- **D-007**: Django-guardian package (v2.4+)
- **D-008**: Research-vocabs package (custom FairDM package)
- **D-009**: ShortUUID package (v1.0+)
- **D-010**: Django-crispy-forms package (v2.0+)
- **D-011**: Django-filter package (v23.0+)
- **D-012**: Django-tables2 package (v2.5+)

## Out of Scope

### Explicitly Excluded

- **OS-001**: Sample list views and detail views (deferred to client-side integration feature).
- **OS-002**: REST API endpoints for samples (deferred to API feature).
- **OS-003**: Sample import/export wizards beyond basic admin functionality.
- **OS-004**: Advanced GIS integration and spatial analysis beyond basic location filtering.
- **OS-005**: Sample workflow management and approval processes.
- **OS-006**: Integration with external IGSN registration system (identifier storage only).
- **OS-007**: Real-time collaboration features for sample editing.
- **OS-008**: Sample barcode/QR code generation and scanning.
- **OS-009**: Integration with laboratory information management systems (LIMS).
- **OS-010**: Administrator audit trail and justification system for published samples (deferred to governance feature).

### Future Considerations

- **FC-001**: Monitor IGSN metadata schema redesign project for future updates.
- **FC-002**: Advanced sample relationship types require research - consider composite, aliquot, section types based on domain requirements.
- **FC-003**: Evaluate integration with IGSN API for automated registration when schema stabilizes.
- **FC-004**: Consider sample chain-of-custody tracking in future workflow features.
- **FC-005**: Evaluate support for 3D sample models and multi-dimensional data in future releases.
- **FC-006**: Consider administrator audit trail system in future governance/compliance feature.
- **FC-007**: Location coordinate reference system specification, altitude/depth handling, and advanced spatial validation deferred to future location feature.
- **FC-008**: Location-based filtering (bounding box, radius queries) deferred until fairdm_location provides comprehensive geo query capabilities.
- **FC-009**: Sample type conversion between polymorphic subclasses (e.g., RockSample → WaterSample) with data loss warnings deferred to future feature.
- **FC-010**: Deep circular relationship detection beyond direct cycles (A→B→C→A) and configurable traversal depth limits deferred due to complexity.

## Technical Notes

### Polymorphic Model Considerations

The Sample model uses django-polymorphic as a base, which has specific implications:

1. **Queryset behavior**: Sample.objects.all() returns polymorphic instances (typed subclasses) by default
2. **Inheritance order**: PolymorphicModel must be listed first in inheritance chain
3. **Proxy models**: Subclasses should be concrete models, not proxy models
4. **Type identification**: Each instance has access to .type_of property for identifying its class

### Registry Integration Pattern

Custom sample types integrate via registration pattern:

```python
# Example registration (illustrative only)
@register
class RockSampleConfig(ModelConfiguration):
    model = RockSample
    fields = ["name", "dataset", "status", "mineral_type", "hardness"]
```

The registry auto-generates:

- ModelForm with specified fields
- FilterSet with appropriate filter types
- Table with column definitions
- Basic ModelAdmin with inlines

### Form/Filter Mixin Strategy

Base mixins should provide:

**SampleFormMixin**:

- Pre-configured field ordering
- Widget selection for common fields
- Initial value handling for dataset/status
- Request-based filtering for dataset queryset

**SampleFilterMixin**:

- Status multi-select filter
- Dataset filter
- Date range filters
- Search filter for name/local_id/uuid

**SampleAdmin**:

- Standard inline configuration
- Common list_display, list_filter, search_fields
- Fieldset organization
- Read-only field configuration
- Audit trail integration for administrator edits on published samples
- Delete protection for published samples

### Sample Relationship Complexity (Deferred - Requires Research)

Sample relationships are complex and require a more thoughtful solution. This feature implements basic direct circular prevention only.

**Deferred to future feature**:

1. **Deep circular detection**: Detecting cycles beyond A→B→A (e.g., A→B→C→A)
2. **Traversal depth limits**: Configurable depth for relationship graph traversal
3. **Complex patterns**: Composite samples, aliquots, sections, splits
4. **Performance optimization**: Evaluate django-treebeard or django-mppt for hierarchical queries

**This feature scope**:

- Basic typed relationships (parent-child, derived-from, split-from)
- Direct circular prevention (A→B, B→A blocked)
- Bidirectional queries (parent→children, child→parents)
- Self-reference prevention

### Testing Strategy

This feature requires comprehensive testing coverage:

1. **Model tests**: Field validation, relationships, polymorphic behavior, manager methods
2. **Form tests**: Field rendering, validation, custom widget behavior, request integration
3. **Filter tests**: Queryset filtering, search, date ranges, location filtering
4. **Admin tests**: Inline display, field configuration, permissions
5. **Registry tests**: Auto-generation of forms/filters/tables/admin, custom overrides
6. **Integration tests**: Sample lifecycle, relationship creation, metadata addition, permission inheritance

### Migration Considerations

- Existing Sample model has established fields; changes should be additive where possible
- New fields should have sensible defaults or allow null=True to avoid migration issues
- Relationship model (SampleRelation) already exists; may need additional relationship types
- Consider data migration for existing samples to populate new required metadata fields
