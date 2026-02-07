# Feature Specification: FairDM Registry System

**Feature Branch**: `002-fairdm-registry`
**Created**: 2026-01-07
**Status**: Draft
**Input**: User description: "Core Purpose: The registry system is the central mechanism that transforms FairDM's philosophy of 'configuration over code' into reality..."

## Clarifications

### Session 2026-01-08

- Q: When and how deeply should the registry validate field names specified in configuration (fields, table_fields, form_fields, filterset_fields)? → A: Validate field existence and type compatibility at registration time, defer data validation to runtime
- Q: When should the registry generate and cache auto-generated components (Forms, Tables, FilterSets, etc.)? → A: Generate and cache all components at registration time (balanced startup cost, zero runtime overhead)
- Q: What fields should be included by default when users don't specify field lists? → A: Include all user-defined fields, exclude auto-generated fields (id, created_at, updated_at, polymorphic_ctype)
- Q: How should form submission errors be displayed to users? → A: Use django-crispy-forms default behavior
- Q: Should the registry limit or warn about the number of columns in table list_fields? → A: No limit or warnings, let developers manage

### Session 2026-01-12

- Q: Should this feature specification be limited to the registry API and component generation only, deferring all UI integration (views, templates, URL routing) to future feature specs? → A: Registry API + Component Generation Only - Registry provides register(), auto-generates classes (Form, Table, FilterSet, Resource, Serializer, ModelAdmin), stores in RegistryEntry, provides introspection API. NO views, templates, or URL patterns. Future specs handle UI integration.
- Q: How should acceptance criteria be reformulated for this API-only scope? → A: API Introspection & Class Availability - Test that registry methods return correct objects, generated classes have expected attributes, configuration is accessible programmatically
- Q: Which user stories should be retained, removed, or significantly refactored for the API-only scope? → A: Keep US1 (Registration) + US6 (Programmatic Access) - Core registration mechanics + introspection API. Remove US2-US5 entirely.
- Q: Which component types should the registry still auto-generate for an API-only feature? → A: All 6 component types - Keep Form, Table, FilterSet, Resource, Serializer, ModelAdmin generation as originally specified
- Q: What should fairdm_demo demonstrate for this API-only registry feature? → A: Registration Examples + API Tests - Update fairdm_demo with registration.py showing various registration patterns, test files demonstrating how to introspect registry and verify component generation, docstrings linking to docs
- Q: Should the registry provide one-step component access (`registry.get_table(Model)`) or two-step (`config = registry.get_for_model(Model)` then `config.get_table_class()`)? → A: Two-step API - Better separation of concerns, config object is reusable, matches existing implementation. Registry returns config, config provides component access methods.
- Q: What field configuration pattern should ModelConfiguration support (single fields list, component-specific lists, or nested config objects)? → A: Parent `fields` with optional custom class overrides - Simple configs use single `fields` list (all components inherit). Advanced users provide custom Form/Table/FilterSet classes directly. No intermediate nested config layer (FormConfig, TableConfig) needed.
- Q: When should component classes be generated (eager at registration or lazy on first access)? → A: Lazy generation with caching - Components generated on first property access (`config.form`, `config.table`, etc.), cached via `@cached_property`. Balances startup time with runtime performance. Configuration still validated at registration time.
- Q: What level of detail should the spec provide for nested config classes like FormConfig, TableConfig? → A: Not needed - Removed from spec. Simple configs use `fields` attribute, advanced users provide custom classes directly (form_class, table_class, etc.). No intermediate config layer.
- Q: What should happen when the same model is registered twice? → A: Raise DuplicateRegistrationError - First registration attempt succeeds, second raises clear error with model name and original registration location. Prevents silent bugs from import ordering issues.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Register a Sample Model with Minimal Configuration (Priority: P1)

A researcher with basic Python skills has created a custom `RockSample` model and wants to register it with the FairDM registry so that component classes (Form, Table, FilterSet, Resource) are automatically generated and accessible via the registry API.

**Why this priority**: This is the most fundamental use case—if researchers can't easily register their models with minimal configuration and access generated components, the entire registry system fails its core purpose.

**Independent Test**: Can be fully tested by creating a simple model class, registering it with field list configuration, and verifying via Python API that all component classes are generated, stored in the registry, and have the expected structure.

**Acceptance Scenarios**:

1. **Given** a researcher has defined a custom Sample model with standard fields (name, description, location), **When** they register it using `@register` decorator with `fields` specified, **Then** the registry successfully registers the model without raising errors
2. **Given** a Sample model registered with `fields = ['name', 'location']`, **When** a developer calls `config = registry.get_for_model(RockSample)` and then accesses `config.table`, **Then** the property returns a django-tables2.Table class with columns for 'name' and 'location'
3. **Given** a registered Sample model, **When** a developer calls `config = registry.get_for_model(RockSample)` and then accesses `config.form`, **Then** the property returns a ModelForm class including all fields from `fields` with appropriate widgets
4. **Given** a registered Sample model, **When** a developer calls `registry.get_for_model(RockSample)`, **Then** the method returns a ModelConfiguration instance with access to all component generation methods

---

### User Story 2 - Discover and Query Registered Models Programmatically (Priority: P1)

A portal developer wants to programmatically access all registered Sample models and their generated components to build advanced portal features (e.g., unified search interfaces, dynamic navigation menus).

**Why this priority**: This enables the registry to be a true central API for portal development. Developers need to introspect registered models, access their configurations, and retrieve generated components without hardcoding model names.

**Independent Test**: Can be tested by registering multiple Sample models with different configurations, then calling registry introspection methods and verifying all models are returned with correct metadata and component references.

**Acceptance Scenarios**:

1. **Given** three different Sample models (RockSample, WaterSample, SoilSample) registered with the registry, **When** a developer accesses `registry.samples` property, **Then** it returns a list of all three registered Sample model classes
2. **Given** a registered Sample model, **When** a developer calls `registry.get_for_model(RockSample)`, **Then** the method returns the ModelConfiguration instance with accessible `fields` attribute and component generation methods
3. **Given** multiple registered Sample models, **When** a developer iterates over `registry.samples`, **Then** each iteration yields a model class that can be passed to `registry.get_for_model()` to access its configuration
4. **Given** a registered Sample model with custom `table_class` override, **When** a developer accesses `config.table`, **Then** the property returns the user-provided custom Table class, not an auto-generated one
5. **Given** registry contains both Sample and Measurement models, **When** a developer accesses `registry.measurements` property, **Then** only Measurement subclasses are returned, not Sample models

---

### Edge Cases

- **What happens when a user registers a model without specifying any field lists?** The system uses sensible defaults: all user-defined fields are included, while auto-generated fields (`id`, `created_at`, `updated_at`, `polymorphic_ctype`) are excluded. This ensures discoverability of user-created fields without cluttering interfaces with technical metadata.
- **How does the system handle registration conflicts?** If the same model is registered twice, the system MUST raise a `DuplicateRegistrationError` with the model name and location of the original registration. This prevents silent bugs from import ordering issues.
- **What happens if a user specifies a field in `list_fields` that doesn't exist on the model?** The system should validate field names at registration time and raise a clear `InvalidFieldError` with suggestions for valid field names.
- **What happens if a custom Form class conflicts with auto-generated field lists?** The custom Form takes precedence, and the registry should not attempt to override user-provided classes. However, it should validate that the custom Form inherits from ModelForm and is compatible with the model.
- **How does filtering work across relationships?** If `filter_fields` includes a foreign key field like `project__name`, the auto-generated FilterSet should create appropriate nested filters using Django's double-underscore syntax.
- **How does the registry handle polymorphic relationships?** Since FairDM uses django-polymorphic for Sample/Measurement inheritance, the registry should automatically detect polymorphic models using `Model.__subclasses__()` and the introspection API should correctly categorize models as Sample or Measurement subclasses.
- **What happens when a model uses translatable fields (django-parler)?** The registry should detect translatable fields and include them in generated components, with the understanding that language switching will be handled by future UI integration specs.
- **How are component generation errors reported?** All component generation should happen at registration time (during `AppConfig.ready()`), so configuration errors surface immediately during application startup with clear error messages including model name, field name, and suggested fixes.
- **What happens if a user provides invalid custom component classes?** The registry should validate that custom classes inherit from the expected base classes (e.g., custom Table must inherit from `django_tables2.Table`) and raise clear errors at registration time.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The registry MUST provide a `register(model, config_class)` method that accepts a Sample or Measurement model class and an optional configuration class
- **FR-002**: The registry MUST validate that registered models inherit from `fairdm.core.Sample` or `fairdm.core.Measurement` polymorphic base classes
- **FR-003**: When `fields` is not specified in the configuration, the registry MUST use a default field list that includes all user-defined model fields while excluding: `id`, `polymorphic_ctype`, `polymorphic_ctype_id`, fields ending with `_ptr` or `_ptr_id` (multi-table inheritance), fields with `auto_now=True`, `auto_now_add=True`, or `editable=False`
- **FR-004**: The registry MUST auto-generate a `ModelForm` (on first access to `config.form` property) for any registered model that does not provide a custom `form_class`, including only fields specified in `fields` attribute
- **FR-005**: The registry MUST auto-generate a `django_tables2.Table` (on first access to `config.table` property) for any registered model that does not provide a custom `table_class`, with columns for all fields in `fields` attribute
- **FR-006**: The registry MUST auto-generate a `django_filters.FilterSet` (on first access to `config.filterset` property) for any registered model that does not provide a custom `filterset_class`, with filters for all fields in `fields` attribute using appropriate filter types based on field types (CharField → CharFilter, DateField → DateFromToRangeFilter, ForeignKey → ModelChoiceFilter)
- **FR-007**: The registry MUST auto-generate a REST API `ModelSerializer` (on first access to `config.serializer` property) for any registered model that does not provide a custom `serializer_class`, including fields from `fields` attribute and using nested serializers for ForeignKey relationships
- **FR-008**: The registry MUST auto-generate an `import_export.Resource` (on first access to `config.resource` property) for any registered model that does not provide a custom `resource_class`, supporting CSV import/export for fields in `fields` attribute
- **FR-009**: The registry MUST auto-generate a Django Admin `ModelAdmin` class (on first access to `config.admin` property) for any registered model that does not provide a custom `admin_class`
- **FR-010**: The registry MUST provide a `samples` property that returns a list of all registered Sample model classes
- **FR-011**: The registry MUST provide a `measurements` property that returns a list of all registered Measurement model classes
- **FR-012**: The registry MUST validate field names at registration time by checking (1) field existence on the model, (2) relationship path validity for double-underscore notation (e.g., `project__title`), and (3) type compatibility with the usage context (e.g., filterable/sortable field types). The registry must raise clear validation errors indicating the invalid field name and suggesting valid alternatives.
- **FR-013**: The registry MUST raise a `DuplicateRegistrationError` with model name and original registration location if the same model is registered more than once
- **FR-014**: The registry MUST allow users to override any auto-generated component (Form, Table, FilterSet, Serializer, Resource, ModelAdmin) by providing their own class in the configuration
- **FR-015**: Auto-generated import/export Resource classes MUST support natural keys for ForeignKey relationships via `use_natural_foreign_keys=True`
- **FR-016**: The registry MUST handle polymorphic querysets correctly by detecting polymorphic models using `Model.__subclasses__()` and providing introspection methods that correctly categorize Sample vs Measurement subclasses
- **FR-017**: Auto-generated Forms MUST use appropriate widgets for common field types (DateInput for dates, FileInput for files, Select for ForeignKey/Choice fields)
- **FR-018**: Auto-generated Forms MUST integrate with django-crispy-forms for Bootstrap 5 styling and layout via `FormHelper`
- **FR-019**: Auto-generated Tables MUST use django-tables2 Bootstrap 5 templates via `template_name = 'django_tables2/bootstrap5.html'`
- **FR-020**: Auto-generated FilterSets MUST integrate with django-crispy-forms for consistent filter panel styling
- **FR-021**: The registry MUST validate configuration at registration time but generate components lazily on first access (e.g., first call to `config.get_form_class()`), caching generated classes for subsequent access to ensure zero runtime overhead after first use
- **FR-022**: The registry MUST provide a `get_for_model(model)` method that accepts either a model class or string "app_label.model_name" and returns the ModelConfiguration instance for that model
- **FR-023**: ModelConfiguration instances MUST provide component access properties: `form`, `table`, `filterset`, `resource`, `serializer`, `admin` (implemented as `@cached_property`) that return the appropriate component class (custom or auto-generated)

### Non-Functional Requirements

- **NFR-001**: Configuration validation at registration time MUST complete within 10ms per registered model on typical development hardware (to ensure application startup remains fast even with 20+ registered models). Component generation on first access MUST complete within 50ms per component type.
- **NFR-002**: All auto-generated components MUST have zero additional overhead during component class instantiation (no lazy generation, metaclass inspection, or dynamic class creation at runtime)

### Key Entities *(include if feature involves data)*

- **Registry**: The central singleton object that stores all registered models and their configurations. Accessed via `@register` decorator for registration. Provides `get_for_model(model)` method to retrieve ModelConfiguration instances and `samples`/`measurements` properties to list registered models.
- **ModelConfiguration**: A user-defined class (decorated with `@register`) that specifies how a model should be configured for component generation. Contains `model` attribute (required), `fields` attribute (list of field names for all components), and optional custom class overrides (`form_class`, `table_class`, `filterset_class`, `resource_class`, `serializer_class`, `admin_class`).
- **Registered Model**: A Sample or Measurement model class that has been explicitly registered with the registry, along with its associated Configuration Class. The registry stores the model class, configuration object, and references to all auto-generated or custom components.
- **Auto-Generated Component**: A Form, Table, FilterSet, Serializer, Resource, or ModelAdmin class that the registry creates dynamically based on a model's configuration when the user does not provide a custom class. All auto-generated components are created eagerly at registration time (not lazily on first use) and cached in the registry for zero-overhead reuse. This ensures all configuration errors surface during application startup rather than at runtime.

- **Field List**: A list of model field names specified in the `fields` attribute of ModelConfiguration (e.g., `fields = ['name', 'date_collected', 'location']`) that determines which fields are used by all auto-generated components (tables, forms, filters, serializers, import/export resources). Field names can use Django's double-underscore syntax for related fields (e.g., `project__title`).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can register a new Sample model with FairDM and access its auto-generated Form, Table, FilterSet, Serializer, Resource, and ModelAdmin classes via registry accessor methods in under 10 minutes
- **SC-002**: The registry supports at least 90% of common component generation use cases through configuration alone, without requiring custom Form/Table/FilterSet classes
- **SC-003**: All auto-generated components use consistent configuration patterns and Bootstrap 5 styling classes
- **SC-004**: Developers can query the registry API to discover registered models via `registry.samples`/`registry.measurements` properties and access their configurations via `registry.get_for_model(Model)`
- **SC-005**: Users registering models with only `model` and `fields` specified get sensible, functional defaults for all components (forms, tables, filters all use the same field list)
- **SC-006**: Advanced users can progressively override individual auto-generated components (e.g., just the Table) without needing to reimplement other components (FilterSet, Form, etc.)
- **SC-007**: The registry correctly handles polymorphic model hierarchies, distinguishing between Sample and Measurement subclasses via `samples` and `measurements` properties
- **SC-008**: Generated components are cached at startup, ensuring zero runtime generation overhead and immediate error detection
- **SC-009**: The demo app demonstrates registration of at least 3 custom Sample types and 2 Measurement types with working component generation and introspection tests
