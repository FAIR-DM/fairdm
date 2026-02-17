# Changelog

All notable changes to the FairDM project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

#### Plugin System for Model Extensibility (Feature 008)

- **Declarative Plugin Registration**: Simple decorator-based registration system
  - `@plugins.register(Model)` decorator for registering plugins with model classes
  - Multiple model registration: `@plugins.register(Sample, Measurement)`
  - Global registry singleton for centralized plugin management
  - Auto-discovery of plugins.py modules in Django apps

- **Plugin Mixin Architecture**: Composable plugin behavior with Django CBVs
  - `Plugin` mixin combines with any Django class-based view (TemplateView, UpdateView, DeleteView, etc.)
  - Automatic URL routing under model detail pages (e.g., `/samples/<uuid>/plugin-name/`)
  - Built-in permission checking (model-level and object-level via django-guardian)
  - Automatic object access via `self.object` (standard Django CBV pattern)

- **Tab-Based Navigation**: Automatic tab generation from menu configuration
  - `menu = {"label": "...", "icon": "...", "order": 0}` dict-based configuration
  - Tabs sorted by `order` then `label` for predictable layout
  - Permission-filtered tabs (users only see tabs they can access)
  - Active tab detection for current plugin
  - Cotton component: `<c-plugin-tabs />`for rendering tab UI

- **Hierarchical Template Resolution**: Automatic template discovery  
  - Model-specific templates: `plugins/{model_name}/{plugin_name}.html`
  - Polymorphic model support: `plugins/{parent_model_name}/{plugin_name}.html`
  - Plugin default: `plugins/{plugin_name}.html`
  - Framework fallback: `plugins/base.html`
  - Explicit override via `template_name` attribute

- **Plugin Groups**: Namespace multiple plugins under shared URL prefix and single tab
  - `PluginGroup` composition class wraps related plugins
  - Shared URL namespace (e.g., `/samples/<uuid>/metadata/view/`, `.../metadata/edit/`)
  - Single tab entry linking to default (first) plugin
  - Group-level permission checking

- **Permission System Integration**: Two-tier permission checking
  - Model-level permissions: `permission = "app.change_model"` attribute
  - Object-level permissions: django-guardian integration in `has_permission()`
  - Visibility filtering: `check` function for polymorphic/conditional visibility
  - Helper: `is_instance_of(ModelClass)` for polymorphic filtering
  - Automatic 403 Forbidden on unauthorized access

- **Custom URL Patterns**: Override auto-generated URLs
  - `url_path` attribute for custom URL segments
  - `name` attribute for custom URL naming
  - Auto-generated slugified names from class name if not set
  - URL conflict detection via system checks

- **Reusable Plugin Base Classes**: Framework provides inheritablePlugin bases
  - `BaseOverviewPlugin`: Read-only overview with standard menu config
  - `BaseEditPlugin`: Form-based editing with permission checking
  - `BaseDeletePlugin`: Delete confirmation with success URL handling
  - Generic plugins: `KeywordsPlugin`, `DescriptionsPlugin`, `KeyDatesPlugin`
  - Portal developers inherit and customize for domain-specific behavior

- **Static Asset Management**: Django Media class integration
  - Declare CSS/JS dependencies via `class Media:` inner class
  - Automatic inclusion in template context as `plugin_media`
  - Support for both local files and CDN URLs
  - Template blocks: `{% block extra_head %}{{ plugin_media.css }}{% endblock %}`

- **Django System Checks**: Comprehensive validation (E001-E007, W001-W003)
  - **E001**: Missing required attributes (Plugin mixin or Django CBV)
  - **E002**: Duplicate plugin names for the same model
  - **E003**: URL path conflicts between plugins
  - **E004**: Invalid `template_name` (file doesn't exist)
  - **E005**: PluginGroup with empty `plugins` list
  - **E006**: PluginGroup contains invalid plugin classes
  - **E007**: URL prefix conflicts between plugin groups
  - **W001**: Invalid permission string (permission doesn't exist)
  - **W002**: Menu configuration missing required keys
  - **W003**: URL path contains invalid characters

- **Automatic Context & Breadcrumbs**: Plugins receive rich context automatically
  - `object`: Model instance (Project, Dataset, Sample, Measurement, etc.)
  - `tabs`: List of Tab objects for current model
  - `breadcrumbs`: Auto-generated navigation chain
  - `plugin_media`: Static assets if Media class defined
  - `view`: Plugin view instance for template access

- **Documentation & Examples**: Comprehensive guides for all user types
  - Developer guide: Creating plugins, inheritance patterns, advanced features
  - Portal admin guide: Managing plugins, permissions, troubleshooting
  - Demo app examples: 10+ working plugin implementations in `fairdm_demo/plugins.py`
  - Quickstart guide: Step-by-step plugin creation workflow
  - API documentation: Complete docstrings with usage examples

- **Testing Infrastructure**: Full test coverage for plugin system
  - 67 passing tests covering all 8 user stories
  - Unit tests: Plugin registration, tab generation, template resolution, permissions
  - Integration tests: URL routing, permission filtering, PluginGroups, context injection
  - System check tests: All error/warning validations
  - Demo app tests: Real-world plugin examples

### Changed

#### Plugin API Migration (Feature 008)

- **New Plugin API**: Simplified registration and configuration
  - **Before**: `@plugin.register('model.Model', category=plugins.EXPLORE)` with string-based registration
  - **After**: `@plugins.register(Model)` with direct model class reference
  - **Before**: `BasePlugin` base class with `menu_item = MenuLink(...)`
  - **After**: `Plugin` mixin with `menu = {"label": "...", "icon": "...", "order": 0}`
  - **Before**: `self.base_object` for instance access
  - **After**: `self.object` (standard Django CBV pattern)
  - **Before**: Category-based grouping (EXPLORE, ACTIONS, MANAGEMENT)
  - **After**: Order-based sorting with `menu["order"]` value
  
- **URL patterns**: No changes required - URLs auto-generated from plugin registration

- **Templates**: Hierarchical resolution now searches multiple paths automatically

- **Permissions**: Permission checking now integrated into Plugin.dispatch() with guardian support

### Migration Guide

#### Upgrading Plugins to New API

**Step 1: Update imports**
```python
# Before
from fairdm.plugins import plugin, MenuLink, BasePlugin

# After
from fairdm import plugins
from fairdm.contrib.plugins import Plugin
```

**Step 2: Update registration decorator**
```python
# Before
@plugin.register('sample.Sample', category=plugins.EXPLORE)

# After
from .models import Sample
@plugins.register(Sample)
```

**Step 3: Update class definition**
```python
# Before
class MyPlugin(BasePlugin, TemplateView):
    menu_item = MenuLink(name="My Plugin", icon="chart")

# After
class MyPlugin(Plugin, TemplateView):
    menu = {"label": "My Plugin", "icon": "chart", "order": 20}
```

**Step 4: Update object access**
```python
# Before
def get_context_data(self, **kwargs):
    sample = self.base_object

# After
def get_context_data(self, **kwargs):
    sample = self.object
```

**Step 5: Run system checks**
```bash
poetry run python manage.py check
```

#### Configuration Checks System (Spec 003)

- **Polymorphic Sample Model**: Flexible sample inheritance with automatic type detection
  - Base `Sample` model with core fields (name, local_id, dataset, location, status, UUID)
  - Polymorphic QuerySet with automatic downcasting to subclass types
  - Support for custom Sample types via model inheritance
  - Integration with django-polymorphic for efficient polymorphic queries

- **Sample Metadata System**: Rich metadata support through related models
  - `SampleDescription`: Multiple descriptions per sample (abstract, methods, other types)
  - `SampleDate`: Temporal metadata with PartialDate support (collected, available, created types)
  - `SampleIdentifier`: Persistent identifiers (IGSN, barcodes, custom types)
  - `SampleContribution`: Track contributors with roles (collector, analyst, owner)
  - Generic relations for flexible metadata attachment

- **Sample Relationships & Provenance**: Track sample hierarchies and processing history
  - `SampleRelation`: Bidirectional relationships between samples
  - Common relationship types: child_of, derived-from, split-from, replicate-of
  - Validation prevents self-reference and direct circular relationships
  - Convenience methods: `get_children()`, `get_parents()`, `get_descendants(depth)`
  - Support for complex multi-level hierarchies

- **Optimized QuerySet Methods**: Performance-focused query patterns
  - `with_related()`: Prefetch dataset, location, contributors, and nested project
  - `with_metadata()`: Prefetch descriptions, dates, identifiers in bulk
  - `by_relationship()`: Filter samples by relationship type and related sample
  - `get_descendants()`: Iterative BFS traversal with depth limiting
  - Performance: <10 queries for 1000 samples, 80%+ query reduction

- **Forms & Filters**: Reusable mixins for Sample CRUD operations
  - `SampleFormMixin`: Standard form configuration with dataset filtering
  - `SampleFilterMixin`: Common filters for name, local_id, dataset, status, type
  - Permission-aware dataset queryset filtering
  - Crispy-forms integration for consistent UI
  - Bootstrap 5 compatible widgets

- **Admin Interface**: Comprehensive Django admin integration
  - Polymorphic parent/child admin for type selection
  - Inline editing for descriptions, dates, identifiers, relationships, contributors
  - Search by name, local_id, UUID
  - Filters by dataset, status, polymorphic type
  - List display with key fields and sample type column

- **Registry Integration**: Automatic component generation
  - Auto-generate ModelForm, FilterSet, Table, and ModelAdmin for custom Sample types
  - Configuration via `ModelConfiguration` class with `@register` decorator
  - Override auto-generated classes with custom implementations as needed
  - Field-level configuration for forms, filters, tables, and serializers

- **Testing Infrastructure**: Comprehensive test coverage
  - Unit tests for models, forms, filters, admin, registry integration
  - Integration tests for polymorphic queries, relationships, permissions
  - Performance tests for query optimization (marked with @pytest.mark.slow)
  - Factory support via fairdm_demo models (RockSample, WaterSample)
  - 99 passing tests across all sample functionality

- **Documentation**: Complete guides for developers and administrators
  - Developer guide: Custom sample types, field patterns, validation, QuerySet optimization
  - Forms & Filters guide: Mixins, customization, testing patterns
  - Admin guide: Managing samples, metadata, relationships, bulk operations
  - Quickstart guide: Step-by-step custom sample creation with working examples
  - API documentation with usage examples in all QuerySet methods

#### Configuration Checks System (Spec 003)

- **Django Check Framework Integration**: Migrated configuration validation from runtime logging to Django's check framework
  - 8 production-readiness checks for database, cache, security, and Celery configuration
  - Custom `DeployTags` class with 'deploy' tag for production-specific checks
  - Error IDs: fairdm.E001, E003-E005, E100-E101, E200, E300-E301
  - `python manage.py check --deploy` command for explicit production validation
  - Tag-based filtering (--tag security, --tag database, --tag caches, --tag deploy)
  - CI/CD friendly with proper exit codes and clear error messages
  - Comprehensive documentation in `docs/portal-administration/configuration-checks.md`
  - **Note**: Removed duplicate checks that Django already provides:
    - SECRET_KEY 'insecure' check (use Django's security.W009)
    - SECRET_KEY length check (use Django's security.W009)
    - SECURE_SSL_REDIRECT check (use Django's security.W008)
    - SESSION_COOKIE_SECURE check (use Django's security.W012)
    - CSRF_COOKIE_SECURE check (use Django's security.W016)

### Changed

#### Configuration Validation Improvements (Spec 003)

- **Removed runtime validation noise**: Configuration validation no longer runs automatically during setup
  - Development workflow is cleaner without constant warning messages
  - Validation is now explicit via `manage.py check` command
  - Production deployments should run `python manage.py check --deploy` in CI/CD pipelines

### Deprecated

#### Legacy Configuration Functions (Spec 003)

- **validate_services()**: Deprecated in favor of Django check framework
  - Function still exists but emits DeprecationWarning
  - Will be removed in a future version
  - Use `python manage.py check --deploy` instead
  - See migration guide in `docs/portal-administration/configuration-checks.md`

#### Core Dataset Models & CRUD Operations (Spec 006)

- **Dataset Model Enhancements**: Comprehensive FAIR-compliant dataset model
  - Enhanced docstrings with image guidelines (16:9 aspect ratio recommended)
  - Role-based permission mapping (Viewer/Editor/Manager → Django permissions)
  - ROLE_PERMISSIONS class attribute for permission management
  - Integration with django-guardian for object-level access control
  - Image field with upload directory and aspect ratio guidance
  - Support for orphaned datasets (project=null permitted)
  - PROTECT behavior on project deletion to prevent accidental data loss

- **DatasetQuerySet & Manager**: Privacy-first data access patterns
  - Default manager excludes PRIVATE datasets automatically
  - `with_private()` method for explicit private dataset access
  - `get_visible()` method returns only PUBLIC datasets
  - `with_related()` optimization (86% query reduction: 21→3 queries)
  - `with_contributors()` lighter optimization for contributor data
  - Method chaining support (combine filters efficiently)
  - Comprehensive docstrings with performance expectations

- **DatasetFilter**: Advanced filtering for list views and APIs
  - Generic search across name, UUID, keywords with Q objects
  - License exact match filtering (ModelChoiceFilter)
  - Project filtering with dynamic user context
  - Visibility filtering (PUBLIC/INTERNAL/PRIVATE)
  - Cross-relationship filters (description_type, date_type)
  - Database indexes for filter performance (10-20x improvement)
  - Comprehensive module docstring with best practices

- **DatasetForm**: User-friendly forms with smart defaults
  - Dynamic project queryset based on user permissions
  - CC BY 4.0 license pre-selected by default (FAIR compliance)
  - Crispy Forms integration with Bootstrap 5 layouts
  - Optional inline contributor management
  - Field ordering optimized for user workflow
  - Help text with documentation links

- **DatasetAdmin**: Powerful admin interface
  - List view with name, project, license, visibility, date added
  - Search across name, UUID, keywords, description text
  - Filtering by project, license, visibility, date added
  - Inline editing for descriptions, dates, identifiers, literature relations
  - Dynamic contributor limit based on vocabulary (max 5 per role)
  - Horizontal filter for contributor management
  - Bulk actions for common operations

- **DatasetLiteratureRelation**: Link datasets with publications
  - Intermediate model with DataCite relationship types
  - Choices: IsDocumentedBy, IsCitedBy, IsSupplementTo, IsDerivedFrom, etc.
  - Bidirectional relationships (dataset ↔ literature)
  - Vocabulary validation for relationship_type field
  - Comprehensive docstring with usage examples

- **Database Migrations**: Performance and structure updates
  - Migration 0008: Indexes for DatasetDescription.type and DatasetDate.type
  - PROTECT on_delete behavior for Dataset.project
  - DatasetLiteratureRelation intermediate model
  - Vocabulary validation for relationship types

#### Testing Infrastructure (Spec 006)

- **Comprehensive Test Suite**: 80+ tests across 8 test files
  - test_models.py: Dataset CRUD, validation, relationships (30+ tests)
  - test_filter.py: All filter types, performance, combinations (30+ tests)
  - test_queryset.py: Privacy-first, optimizations, chaining (25+ tests)
  - test_form.py: Form rendering, validation, user context (15+ tests)
  - test_admin.py: Admin interface, inlines, search/filter (20+ tests)
  - test_description.py: DatasetDescription vocabulary validation
  - test_date.py: DatasetDate vocabulary validation
  - test_identifier.py: DatasetIdentifier creation and DOI support
  - test_literature_relation.py: DataCite relationship types

- **Factory Examples**: Comprehensive test data generation patterns
  - DatasetFactory with CC BY 4.0 default license
  - DOI creation examples via DatasetIdentifier
  - Literature relation examples with DataCite types
  - Complete metadata example combining all patterns
  - Best practices documentation in fairdm_demo/factories.py

#### Demo App Updates (Spec 006)

- **QuerySet Optimization Examples**: 6 complete patterns in fairdm_demo/models.py
  - Privacy-first default usage with permission checks
  - with_related() optimization (86% query reduction)
  - with_contributors() lighter optimization
  - Method chaining examples
  - Performance monitoring with Django Debug Toolbar
  - Custom QuerySet pattern for custom models

- **Filter Examples**: 4 complete classes in fairdm_demo/filters.py
  - Generic search pattern across multiple fields
  - Cross-relationship filtering with indexes
  - ModelChoiceFilter with dynamic querysets
  - 10 best practices sections with rationale

- **Factory Examples**: 7 complete examples in fairdm_demo/factories.py
  - Basic Sample/Measurement factories
  - Dataset with default CC BY 4.0 license
  - DOI creation via DatasetIdentifier
  - Literature relations with DataCite types
  - Complete dataset with all metadata types

#### Documentation (Spec 006)

- **Research Documents**: Technical decisions and rationale
  - Image aspect ratio research (16:9 recommendation, Bootstrap cards, Open Graph)
  - DataCite RelationType vocabulary analysis
  - Performance optimization strategies

- **Model Docstrings**: Comprehensive documentation in code
  - Image Guidelines section with aspect ratio specifications
  - Role-Based Permissions section with permission mapping
  - Usage examples for has_perm() checks
  - Integration with django-guardian

#### Project Admin Interface Enhancements

- **Advanced Search Capabilities**: Enhanced ProjectAdmin with comprehensive search functionality
  - Search projects by name, UUID, and owner organization
  - Fast full-text search across multiple fields for quick project discovery
  - Support for partial name matching and exact UUID lookups

- **Smart Filtering System**: Added powerful filter options for project management
  - Filter by project status (Concept/Active/Completed)
  - Filter by visibility (Public/Private)
  - Filter by date added (Today, Past 7 days, This month, This year)
  - Combine multiple filters for precise project queries

- **Organized Form Layout**: Improved admin form with collapsible fieldsets
  - Basic Information section (always visible)
  - Access & Visibility section (collapsible)
  - Organization section with keywords (collapsible)
  - Metadata section for funding JSON (collapsible)
  - Cleaner, more focused editing experience

- **Inline Metadata Editing**: Edit related project data without leaving the page
  - ProjectDescription inline for adding multiple description types
  - ProjectDate inline for managing project dates
  - ProjectIdentifier inline for external identifiers (DOI, grant numbers)

- **Bulk Operations**: Efficient management of multiple projects at once
  - Bulk status changes (Mark as Concept/Active/Completed)
  - Bulk export as JSON for data portability
  - Bulk export as DataCite JSON for DOI registration
  - User feedback messages confirming operation success

- **Internationalization**: Full i18n support for admin interface
  - All user-facing strings wrapped with gettext_lazy
  - Ready for translation to multiple languages
  - Consistent terminology across admin interface

#### Registry System Enhancements

- **Registry Introspection API**: New properties `registry.samples`, `registry.measurements`, and `registry.models` for programmatic discovery of registered models
  - Enables dynamic iteration over all registered Sample subclasses
  - Provides access to all registered Measurement subclasses
  - Allows retrieval of all registered models (Samples + Measurements combined)
  - Supports filtering and programmatic model discovery workflows

#### Performance & Scalability

- **Performance Benchmarks**: Comprehensive test suite validating registry performance requirements
  - Single model registration: <10ms per model (actual: ~4 microseconds)
  - Component generation: <50ms per component type on first access (actual: ~100 microseconds)
  - Cached access: <1ms for dictionary lookup operations (actual: <1 microsecond)
  - Scalability: Support for 20+ registered models without noticeable startup delay
- **Cached Property Optimization**: Efficient caching of auto-generated components (forms, tables, filters, etc.)

#### Type Safety & Developer Experience

- **Comprehensive Type Hints**: Full mypy compatibility across all registry modules
  - Added type annotations for all method parameters and return types
  - Improved IDE support and static analysis capabilities
  - Enhanced developer experience with better autocomplete and error detection
- **Contract Compliance Testing**: Protocol verification ensuring implementation matches specifications
  - Validates FairDMRegistry Protocol compliance
  - Verifies ModelConfiguration Protocol adherence
  - Tests registration API compatibility and type safety

#### Configuration System Improvements

- **Enhanced ModelConfiguration**: Improved dataclass field inheritance handling
  - Fixed model attribute inheritance from class to instance level
  - Better support for declarative model registration patterns
  - Improved validation and error reporting for configuration issues

### Fixed

- **Model Registration**: Fixed dataclass field inheritance issue where class-level `model` attributes weren't properly inherited by instances
- **Demo App Registration**: Corrected `@register` decorator usage in demo configuration files
- **Test Compatibility**: Resolved Django model name conflicts in test suite for better test isolation

### Technical Details

#### API Additions

```python
# New introspection properties
registry.samples         # Iterator[Type[Sample]] - all registered Sample subclasses
registry.measurements    # Iterator[Type[Measurement]] - all registered Measurement subclasses
registry.models         # Iterator[Type[Model]] - all registered models combined

# Enhanced performance characteristics
# - Registration: 4μs per model (well under 10ms requirement)
# - Component generation: 100μs per component (well under 50ms requirement)
# - Cached access: <1μs per lookup (well under 1ms requirement)
```

#### Performance Metrics

- **Registration Performance**: Average 4 microseconds per model registration
- **Component Generation**: Average 100 microseconds for form/table/filter generation
- **Cached Access**: Sub-microsecond performance for repeated component access
- **Startup Performance**: <500ms for 25+ registered models
- **Memory Efficiency**: <1KB registry overhead per registered model

#### Type Safety

- Full mypy compliance across `fairdm.registry.*` modules
- Comprehensive Protocol definitions for public APIs
- Enhanced IDE support with complete type annotations

#### Test Coverage

- **Core Features**: 61.8% coverage on completed functionality
- **Introspection API**: 100% test coverage with 12 comprehensive test cases
- **Performance Testing**: 7 benchmark tests validating all performance requirements
- **Contract Compliance**: 4 Protocol verification tests ensuring API compatibility

### Breaking Changes

None - All changes are backward compatible additions to the existing API.

### Migration Guide

No migration required. New introspection properties are additive features that don't affect existing code.

#### Using New Introspection Features

```python
from fairdm.registry import registry

# Iterate over all registered Sample models
for sample_model in registry.samples:
    print(f"Sample: {sample_model.__name__}")

# Access all registered Measurement models
for measurement_model in registry.measurements:
    print(f"Measurement: {measurement_model.__name__}")

# Get all registered models (Samples + Measurements)
all_models = list(registry.models)
print(f"Total registered models: {len(all_models)}")
```

### Development

- Enhanced development experience with comprehensive type hints and better error messages
- Improved testing infrastructure with performance benchmarks and contract validation
- Better documentation of registry patterns and API usage examples

---

*This changelog documents registry system enhancements delivered in the 002-fairdm-registry feature branch.*
