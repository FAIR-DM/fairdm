# Feature Specification: FairDM Registry System

**Feature Branch**: `004-fairdm-registry`  
**Created**: 2026-01-07  
**Status**: Draft  
**Input**: User description: "Core Purpose: The registry system is the central mechanism that transforms FairDM's philosophy of 'configuration over code' into reality..."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Register a Sample Model with Minimal Configuration (Priority: P1)

A researcher with basic Python skills has created a custom `RockSample` model and wants to make it available in the portal without writing any views, forms, or templates.

**Why this priority**: This is the most fundamental use case—if researchers can't easily register their models with minimal effort, the entire registry system fails its core purpose.

**Independent Test**: Can be fully tested by creating a simple model class, registering it with just field lists, and verifying that list views, detail views, and basic forms are automatically generated and functional.

**Acceptance Scenarios**:

1. **Given** a researcher has defined a custom Sample model with standard fields (name, description, location), **When** they register the model with only `list_fields` and `detail_fields` specified, **Then** the system generates a working list view with a table, detail view with all fields displayed, and create/edit forms
2. **Given** a registered Sample model, **When** a user navigates to the samples list page, **Then** they see a paginated, sortable table showing all specified list fields
3. **Given** a registered Sample model, **When** a user clicks on a sample in the list, **Then** they see a detail page displaying all specified detail fields with appropriate formatting
4. **Given** a registered Sample model with auto-generated forms, **When** a user with appropriate permissions creates a new sample, **Then** the form includes all editable fields with appropriate widgets and validation

---

### User Story 2 - Filter and Search Registered Models (Priority: P1)

A portal user needs to find specific samples among hundreds of records by filtering on key attributes (e.g., collection date, location, rock type).

**Why this priority**: Search and filtering are essential for usability once data volumes grow beyond a few dozen records. Without this, the portal becomes unusable for real research workflows.

**Independent Test**: Can be tested by registering a model with `filter_fields` specified, populating the database with test data, and verifying that filter widgets appear and correctly narrow results.

**Acceptance Scenarios**:

1. **Given** a Sample model registered with `filter_fields = ['name', 'date_collected', 'location']`, **When** the user views the sample list page, **Then** filter widgets for each specified field appear in a sidebar or panel
2. **Given** available filter widgets, **When** the user enters a partial name match, **Then** the table updates to show only matching samples without full page reload
3. **Given** available filter widgets, **When** the user applies multiple filters (e.g., date range AND location), **Then** the results show only records matching all criteria
4. **Given** applied filters, **When** the user clears filters, **Then** the full unfiltered list is restored

---

### User Story 3 - Import and Export Data (Priority: P2)

A researcher needs to bulk-import 100 sample records from a CSV file provided by a collaborator, and later export their own dataset for sharing.

**Why this priority**: Bulk data operations are critical for real-world workflows but are not needed for initial portal setup. This is a high-value convenience feature that prevents manual data entry.

**Independent Test**: Can be tested by registering a model, uploading a CSV with valid data, verifying records are created, then exporting and verifying the exported file matches the import format.

**Acceptance Scenarios**:

1. **Given** a registered Sample model, **When** a user with edit permissions visits the sample list page, **Then** they see "Import" and "Export" action buttons
2. **Given** the import interface, **When** a user uploads a valid CSV file with columns matching model fields, **Then** all records are created successfully and a summary is displayed
3. **Given** the import interface, **When** a user uploads a CSV with errors (e.g., missing required fields, invalid values), **Then** the system displays specific error messages for each row and does not create invalid records
4. **Given** a filtered sample list, **When** a user clicks "Export", **Then** a CSV file downloads containing only the filtered records with all `list_fields` included

---

### User Story 4 - Customize Auto-Generated Components (Priority: P2)

An intermediate user wants to override the default table layout to add custom columns (e.g., calculated fields, status badges) without losing the benefits of auto-generated filtering and pagination.

**Why this priority**: This enables progressive complexity—users can start simple and incrementally customize as their needs evolve, without rebuilding everything from scratch.

**Independent Test**: Can be tested by registering a model with a custom Table class that adds a computed column, then verifying the custom column appears alongside auto-generated columns and all standard features (sorting, pagination) still work.

**Acceptance Scenarios**:

1. **Given** a Sample model registered with a custom `Table` class that adds a "Status" column, **When** the user views the sample list, **Then** the custom column appears with other columns and displays correct computed values
2. **Given** a custom Table class, **When** the user sorts or filters the list, **Then** the custom column values update correctly
3. **Given** a Sample model registered with a custom `Form` class with field dependencies, **When** the user fills the form, **Then** dependent fields show/hide based on custom logic
4. **Given** a custom FilterSet with a multi-select filter, **When** the user selects multiple options, **Then** results match any of the selected values (OR logic)

---

### User Story 5 - Access Registered Models via REST API (Priority: P3)

An external tool needs to query sample data programmatically via JSON API endpoints for automated analysis pipelines.

**Why this priority**: API access is essential for interoperability and automation, but portal-internal functionality should work first. This is a lower priority for initial MVP but critical for FAIR compliance.

**Independent Test**: Can be tested by enabling the API app, registering a model with API enabled, and making GET/POST/PATCH requests to verify CRUD operations work and return valid JSON.

**Acceptance Scenarios**:

1. **Given** a Sample model registered with `api_enabled=True`, **When** the API module is enabled in settings, **Then** REST endpoints are auto-generated at `/api/samples/`
2. **Given** available API endpoints, **When** an authenticated client sends a GET request to `/api/samples/`, **Then** it receives a paginated JSON response with all samples matching their permissions
3. **Given** API endpoints, **When** a client sends a POST request with valid JSON data, **Then** a new sample is created and the response includes the created resource with its ID
4. **Given** API endpoints with nested relationships, **When** a client requests a sample detail, **Then** related objects (e.g., measurements) are included as nested serialized data or hyperlinks

---

### User Story 6 - Discover and Query Registered Models Programmatically (Priority: P3)

A portal developer wants to build a unified search page that queries all registered Sample types across the portal (e.g., RockSample, WaterSample, SoilSample) in one interface.

**Why this priority**: This enables advanced portal features like cross-model search, but basic per-model functionality should work first.

**Independent Test**: Can be tested by registering multiple Sample models, then calling registry methods like `registry.get_registered_samples()` and verifying all models are returned with their configuration metadata.

**Acceptance Scenarios**:

1. **Given** three different Sample models registered with the registry, **When** a developer calls `registry.get_registered_samples()`, **Then** the method returns a list of all registered Sample models with their configuration objects
2. **Given** registry introspection methods, **When** a developer retrieves a model's configuration, **Then** they can access `list_fields`, `filter_fields`, `detail_fields`, and custom classes (Form, Table, FilterSet) programmatically
3. **Given** multiple registered Sample types, **When** a unified search page queries all types using registry-provided metadata, **Then** results from all types are displayed in a consistent format
4. **Given** registry-provided metadata, **When** a developer wants to dynamically generate a menu of all Sample types, **Then** they can iterate registered models and create links without hardcoding model names

---

### Edge Cases

- **What happens when a user registers a model without specifying any field lists?** The system should use sensible defaults (e.g., all model fields except auto-generated ones like `id`, `created_at`) or raise a clear error requiring at least `list_fields`.
- **How does the system handle registration conflicts?** If the same model is registered twice, the system should raise a clear error indicating the duplicate registration and the original registration location.
- **What happens if a user specifies a field in `list_fields` that doesn't exist on the model?** The system should validate field names at registration time and raise a clear error with suggestions for valid field names.
- **How are permissions enforced on auto-generated views?** All auto-generated views should integrate with django-guardian to check object-level permissions before displaying or modifying data.
- **What happens when a user tries to import data with foreign key references?** The import system should support natural keys or ID-based references and provide clear error messages when references cannot be resolved.
- **How does the registry handle polymorphic relationships?** Since FairDM uses django-polymorphic for Sample/Measurement inheritance, the registry should automatically detect polymorphic models and generate appropriate querysets that fetch the correct subclass instances.
- **What happens if a custom Form class conflicts with auto-generated field lists?** The custom Form takes precedence, and the registry should not attempt to override user-provided classes. However, it should validate that the custom Form is compatible with the model.
- **How does filtering work across relationships?** If `filter_fields` includes a foreign key field like `project__name`, the auto-generated FilterSet should create appropriate nested filters using Django's double-underscore syntax.
- **What happens when export/import involves file fields or image fields?** The export should include file paths or URLs, and import should support uploading files separately or referencing existing media paths.
- **How does the registry handle multi-language content (django-parler)?** If a model uses translatable fields, the auto-generated forms and tables should support language switching and display content in the user's current language.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The registry MUST provide a `register(model, config_class)` method that accepts a Sample or Measurement model class and an optional configuration class
- **FR-002**: The registry MUST validate that registered models inherit from `fairdm.core.Sample` or `fairdm.core.Measurement` polymorphic base classes
- **FR-003**: The registry MUST auto-generate a `ModelForm` for any registered model that does not provide a custom Form class, including only fields specified in `list_fields` or `detail_fields`
- **FR-004**: The registry MUST auto-generate a `django_tables2.Table` for any registered model that does not provide a custom Table class, with columns for all `list_fields` plus a detail link column
- **FR-005**: The registry MUST auto-generate a `django_filters.FilterSet` for any registered model that does not provide a custom FilterSet class, with filters for all `filter_fields` using appropriate filter types based on field types (CharField → CharFilter, DateField → DateFromToRangeFilter, ForeignKey → ModelChoiceFilter)
- **FR-006**: The registry MUST auto-generate a REST API `ModelSerializer` for any registered model when the API module is enabled, including fields from `list_fields` and `detail_fields` and using nested serializers for ForeignKey relationships
- **FR-007**: The registry MUST auto-generate an `import_export.Resource` for any registered model that does not provide a custom Resource class, supporting CSV import/export for fields in `list_fields` and `detail_fields`
- **FR-008**: The registry MUST provide a method to retrieve all registered Sample models and their configuration objects (e.g., `get_registered_samples()`)
- **FR-009**: The registry MUST provide a method to retrieve all registered Measurement models and their configuration objects (e.g., `get_registered_measurements()`)
- **FR-010**: The registry MUST raise a clear validation error at registration time if a specified field in `list_fields`, `detail_fields`, or `filter_fields` does not exist on the model
- **FR-011**: The registry MUST raise a clear error if the same model is registered more than once
- **FR-012**: The registry MUST integrate auto-generated views with django-guardian to enforce object-level permissions (view, change, delete) based on Project/Dataset ownership
- **FR-013**: Auto-generated list views MUST support server-side pagination with configurable page size (default 25 records per page)
- **FR-014**: Auto-generated list views MUST support server-side sorting on all `list_fields` columns
- **FR-015**: Auto-generated detail views MUST display all `detail_fields` in a structured layout with appropriate field rendering (dates formatted, URLs as links, images displayed inline)
- **FR-016**: Auto-generated forms MUST include Django's built-in validation and display field-specific error messages
- **FR-017**: Auto-generated forms MUST use appropriate widgets for common field types (DateInput for dates, FileInput for files, Select for ForeignKey/Choice fields)
- **FR-018**: The registry MUST allow users to override any auto-generated component (Form, Table, FilterSet, Serializer, Resource) by providing their own class in the configuration
- **FR-019**: The registry MUST generate Django Admin `ModelAdmin` classes for all registered models, integrating with django-admin with minimal styling
- **FR-020**: Auto-generated import/export functionality MUST validate data before creating records and provide detailed error reports for invalid rows
- **FR-021**: Auto-generated import/export functionality MUST support natural keys for ForeignKey relationships
- **FR-022**: The registry MUST support configuration of card display fields for Project/Dataset models, allowing users to specify which fields appear on card layouts
- **FR-023**: The registry MUST enforce that required metadata fields (title, description, authority, citations) are included in detail views and forms
- **FR-024**: Auto-generated API endpoints MUST support filtering, pagination, and sorting via query parameters (e.g., `?name__icontains=rock&page=2&ordering=-date_collected`)
- **FR-025**: Auto-generated API endpoints MUST return proper HTTP status codes (200 OK, 201 Created, 400 Bad Request, 403 Forbidden, 404 Not Found) based on operation outcome and permissions
- **FR-026**: The registry MUST handle polymorphic querysets correctly, ensuring that list views display the correct subclass instances with their specific fields
- **FR-027**: Auto-generated forms MUST integrate with django-crispy-forms for Bootstrap 5 styling and layout
- **FR-028**: Auto-generated tables MUST use django-tables2 Bootstrap 5 templates for consistent styling
- **FR-029**: Auto-generated filters MUST integrate with django-crispy-forms for consistent filter panel styling
- **FR-030**: The registry MUST support HTMX integration for auto-generated list views, enabling filter updates without full page reloads

### Key Entities *(include if feature involves data)*

- **Registry**: The central singleton object that stores all registered models and their configurations. Provides methods to register models, retrieve registered models, and access their auto-generated components.
- **Configuration Class**: A user-defined class (or auto-generated default) that specifies how a model should be displayed and interacted with. Contains attributes like `list_fields`, `detail_fields`, `filter_fields`, `card_fields`, and references to custom classes (Form, Table, FilterSet, Serializer, Resource).
- **Registered Model**: A Sample or Measurement model class that has been explicitly registered with the registry, along with its associated Configuration Class. The registry stores the model class, configuration object, and references to all auto-generated or custom components.
- **Auto-Generated Component**: A Form, Table, FilterSet, Serializer, Resource, or ModelAdmin class that the registry creates dynamically based on a model's configuration when the user does not provide a custom class. These components are created at registration time and cached for reuse.
- **Field List**: A list of model field names specified in the configuration (e.g., `list_fields = ['name', 'date_collected', 'location']`) that determines which fields appear in a particular context (list views, detail views, filters, forms, exports). Field names can use Django's double-underscore syntax for related fields (e.g., `project__title`).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A researcher with basic Python knowledge can register a new Sample model and have a fully functional portal interface (list, detail, create, edit, delete) in under 10 minutes without writing any view code
- **SC-002**: The registry supports at least 90% of common portal use cases through configuration alone, without requiring custom Form/Table/FilterSet classes
- **SC-003**: All registered models follow consistent UI patterns—users familiar with one model's interface can immediately understand how to interact with any other registered model
- **SC-004**: API endpoints for registered models support all standard REST operations (GET, POST, PATCH, DELETE) with consistent URL patterns and JSON response formats
- **SC-005**: Portal administrators can import 1000+ sample records from CSV in under 5 minutes with clear validation feedback for any errors
- **SC-006**: Developers can query the registry to dynamically generate portal features (e.g., unified search, navigation menus) without hardcoding model names
- **SC-007**: Users registering models with only `list_fields` and `detail_fields` specified get sensible, functional defaults for all other components (forms use all editable fields, filters include common searchable fields)
- **SC-008**: Advanced users can progressively override individual auto-generated components (e.g., just the Table) without needing to reimplement other components (FilterSet, Form, etc.)
- **SC-009**: Auto-generated forms integrate seamlessly with Bootstrap 5 styling and match the portal's design system without additional CSS
- **SC-010**: All auto-generated views enforce object-level permissions, preventing unauthorized access or modifications across 100% of registered models
