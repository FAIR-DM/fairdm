# Implementation Plan: Core Dataset App Cleanup & Enhancement

**Branch**: `006-core-datasets` | **Date**: 2026-01-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/006-core-datasets/spec.md`

**Note**: This plan was created by the `/speckit.plan` command.

## Summary

This feature focuses on cleaning up and enhancing the `fairdm.core.dataset` app to ensure robust FAIR data compliance, comprehensive testing coverage, and excellent portal usability. The work encompasses model validation, optimized QuerySet methods, user-context-aware forms, advanced filtering, and enhanced Django admin interface. Client-side integration (list views, detail views, APIs) is explicitly out of scope and deferred to future specifications.

**Primary Requirements**:

- Enforce FAIR metadata principles at the model level with validation
- Provide optimized QuerySet methods to prevent N+1 query problems
- Implement permission-aware forms with proper user context filtering
- Enable comprehensive filtering by project, license, visibility, and dates
- Enhance admin interface with search, bulk operations, and inline metadata editing
- Achieve 90%+ meaningful test coverage with proper test organization

**Technical Approach** (from research phase below):

- Django models with custom validators for FAIR metadata types
- Custom QuerySet manager with prefetch optimization methods
- ModelForm with request context for permission-based queryset filtering
- django-filter FilterSet with multiple field types and search integration
- Django admin with Select2 widgets, inline editors, and bulk actions
- factory-boy factories for test data generation
- pytest with pytest-django for comprehensive unit and integration testing

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: Django 5.1.3, django-tables2, django-filter, django-select2, django-guardian, licensing, shortuuid, factory-boy, pytest, pytest-django
**Storage**: PostgreSQL (primary), with Django ORM support for other SQL databases
**Testing**: pytest, pytest-django, factory-boy for fixtures, coverage.py for coverage analysis
**Target Platform**: Linux server (production), cross-platform development (macOS, Linux, Windows)
**Project Type**: Django web application (monolithic framework)
**Performance Goals**:

- Dataset CRUD operations complete within 2 seconds
- 100-dataset list view with filters loads in under 1 second
- QuerySet optimization reduces database queries by 80%+ for related data loading
**Constraints**:
- Must maintain backward compatibility with existing Dataset instances
- Must integrate with django-guardian for object-level permissions
- Must support FAIR metadata vocabularies (FairDMDescriptions, FairDMDates, FairDMIdentifiers, FairDMRoles)
- Must not break existing views/templates (they're out of scope but shouldn't be broken)
**Scale/Scope**:
- Single Django app (`fairdm.core.dataset`) with 8 files to enhance
- ~1500 lines of existing code to review and improve
- 52 functional requirements to address
- Estimated 20-30 test files across unit and integration layers

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: FAIR-First Research Portals

✅ **PASS**: This feature directly strengthens FAIR compliance by:

- Enforcing required metadata at the model level (descriptions, dates, identifiers, contributors)
- Providing stable identifiers (ShortUUID) for external referencing
- Supporting visibility controls to enable public read access when appropriate
- Ensuring metadata is accessible through proper model relationships
- No violations detected

### Principle II: Domain-Driven, Declarative Modeling

✅ **PASS**: This feature enhances declarative modeling:

- Dataset model and related models (DatasetDescription, DatasetDate, DatasetIdentifier) remain explicit Django models
- Uses vocabulary-based validation (FairDMDescriptions, FairDMDates, FairDMIdentifiers)
- Forms, filters, and admin are declarative configurations, not ad-hoc runtime logic
- No new runtime structures; all enhancements are model-level or configuration-level
- No violations detected

### Principle III: Configuration Over Custom Plumbing

✅ **PASS**: This feature follows configuration-first approach:

- Admin enhancements use Django's declarative admin configuration (list_display, fieldsets, inlines)
- Forms use ModelForm with declarative field definitions
- Filters use django-filter FilterSet with declarative fields
- QuerySet methods provide reusable query optimization without view-level logic
- No custom plumbing or boilerplate duplication introduced
- No violations detected

### Principle IV: Opinionated, Production-Grade Defaults

✅ **PASS**: This feature maintains production-grade defaults:

- Uses Django admin (existing default)
- Uses django-tables2, django-filter, django-select2 (existing stack)
- Uses PostgreSQL-compatible Django ORM (no database-specific code)
- Uses Bootstrap 5 widgets (Select2) for enhanced UX
- Tests use pytest/pytest-django (existing testing stack)
- No new dependencies or stack changes introduced
- No violations detected

### Principle V: Test-First Quality & Sustainability

✅ **PASS**: This feature enforces test-first discipline:

- FR-046 through FR-052 mandate comprehensive testing requirements
- Tests must be written before implementation (Red → Green → Refactor)
- Unit tests for models, QuerySets, forms, filters (tests/unit/core/)
- Integration tests for admin interface (tests/integration/core/)
- factory-boy factories for test data generation
- Test organization follows spec 002 test layer taxonomy
- Meaningful test quality emphasized over coverage percentages
- No violations detected

### Principle VI: Documentation Critical

✅ **PASS**: This feature maintains documentation standards:

- Functional requirements (FR-001 through FR-052) document expected behavior
- Edge cases clearly identified for implementation decisions
- Success criteria provide measurable outcomes
- Plan includes technical context and structure decisions
- Documentation will be updated in implementation phase
- No violations detected

### Principle VII: Living Demo & Reference Implementation

✅ **PASS**: This feature requires demo app updates:

- Demo app updates are **mandatory** per this principle
- `fairdm_demo` should demonstrate dataset model best practices
- Demo app factories should show proper Dataset factory usage
- Docstrings in demo should link to dataset documentation
- Implementation phase must update demo app in same PR as core changes
- No violations detected

**Overall Constitution Compliance**: ✅ **PASS** - No violations detected. Feature aligns with all constitutional principles.

## Project Structure

### Documentation (this feature)

```text
specs/006-core-datasets/
├── spec.md              # Feature specification (completed)
├── plan.md              # This file (current step)
├── research.md          # Phase 0: Research findings (to be created)
├── data-model.md        # Phase 1: Data model design (to be created)
├── quickstart.md        # Phase 1: Quick start guide (to be created)
├── contracts/           # Phase 1: API contracts (to be created)
│   ├── models.py        # Model interface contracts
│   ├── querysets.py     # QuerySet method contracts
│   ├── forms.py         # Form interface contracts
│   └── filters.py       # Filter interface contracts
├── tasks.md             # Phase 2: Implementation tasks (via /speckit.tasks)
└── checklists/
    └── requirements.md  # Requirements quality checklist (completed)
```

### Source Code (existing Django app structure)

```text
fairdm/core/dataset/
├── __init__.py          # Package initialization, exports
├── models.py            # Dataset, DatasetDescription, DatasetDate, DatasetIdentifier, DatasetQuerySet
├── admin.py             # DatasetAdmin, DescriptionInline, DateInline
├── forms.py             # DatasetForm with user context
├── filters.py           # DatasetFilter with multiple filter fields
├── views.py             # DatasetCreateView, DatasetListView, DatasetDetailView (out of scope)
├── urls.py              # URL routing (out of scope)
├── apps.py              # Django app configuration
├── plugins.py           # Plugin integration (out of scope)
└── templates/           # Dataset templates (out of scope)

fairdm/core/
├── abstract.py          # AbstractDescription, AbstractDate, AbstractIdentifier (base classes)
├── base.py              # BaseModel (parent class for Dataset)
├── filters.py           # BaseListFilter (parent class for DatasetFilter)
├── vocabularies.py      # FairDMDescriptions, FairDMDates, FairDMIdentifiers, FairDMRoles
└── utils.py             # CORE_PERMISSIONS and other utilities

fairdm/factories/        # Centralized factory exports (to be updated)
└── __init__.py          # Re-exports DatasetFactory for downstream use

fairdm/core/factories.py # Factory definitions (to be created/updated)
└── DatasetFactory       # factory-boy DjangoModelFactory for Dataset model

tests/unit/core/
└── test_dataset_*.py    # Unit tests for Dataset model, QuerySet, forms, filters

tests/integration/core/
└── test_dataset_admin.py # Integration tests for admin interface

fairdm_demo/             # Demo app updates (mandatory per Principle VII)
├── models.py            # Example Dataset subclass or usage patterns
├── config.py            # Dataset registration configuration example
└── factories.py         # Demo factory examples showing Dataset factory usage
```

**Structure Decision**: This feature works within the existing Django app structure (`fairdm.core.dataset`). No new apps or major structural changes are required. The work focuses on enhancing existing files (models.py, admin.py, forms.py, filters.py) and adding comprehensive tests following the established test layer taxonomy from spec 002-testing-strategy.

Key structural principles:

- **Locality**: Model enhancements stay in models.py, admin enhancements in admin.py, etc.
- **Test organization**: Tests mirror source structure in tests/unit/core/ and tests/integration/core/
- **Factory location**: Factories declared in fairdm/core/factories.py, re-exported via fairdm/factories.py
- **Demo app**: Updates mandatory to demonstrate new patterns and maintain executable documentation

## Complexity Tracking

**No violations** - This feature aligns with all constitutional principles without requiring any justified deviations. The Complexity Tracking table is empty.

---

## Phase 0: Research & Clarification

**Objective**: Resolve all "NEEDS CLARIFICATION" markers from Technical Context and identify technology/pattern choices.

### Research Tasks

All items in Technical Context are already clarified based on existing FairDM codebase:

1. ✅ **Language/Version**: Python 3.13 (confirmed in pyproject.toml)
2. ✅ **Primary Dependencies**: Django 5.1.3, django-filter, django-tables2, django-select2, licensing (confirmed in pyproject.toml)
3. ✅ **Storage**: PostgreSQL primary via Django ORM (confirmed in existing infrastructure)
4. ✅ **Testing**: pytest, pytest-django, factory-boy (confirmed in spec 002-testing-strategy)
5. ✅ **Performance Goals**: Documented in spec.md Success Criteria
6. ✅ **Constraints**: Documented in Technical Context above

### Technology/Pattern Decisions

#### Decision 1: Model Validation Strategy

**Decision**: Use Django model field validators and vocabulary-based validation

**Rationale**:

- FairDM already uses vocabulary pattern (FairDMDescriptions, FairDMDates, FairDMIdentifiers)
- Field validators provide immediate feedback before database save
- Vocabulary validation ensures metadata type consistency
- Existing pattern in AbstractDescription, AbstractDate, AbstractIdentifier base classes

**Alternatives Considered**:

- Custom clean() methods: Less reusable, harder to test individually
- Database constraints: Less flexible, harder to provide helpful error messages
- Form-only validation: Doesn't protect against programmatic saves

**Implementation Notes**:

- Add validators to DatasetDescription.description_type, DatasetDate.date_type, DatasetIdentifier.identifier_type
- Validation errors should reference vocabulary concept URIs for clarity

#### Decision 2: Privacy-First QuerySet with Optional Optimization

**Decision**: Default QuerySet excludes PRIVATE datasets; provide explicit methods for optimization and private access

**Rationale**:

- Constitutional requirement for privacy by default
- Prevents accidental exposure of private datasets in public views
- Optimization methods (with_related, with_contributors) are optional based on actual usage patterns
- Django's prefetch_related() is idiomatic and well-tested

**Alternatives Considered**:

- get_visible() returning only PUBLIC: Too restrictive, doesn't handle INTERNAL visibility
- No default filtering: Dangerous, could expose private data accidentally
- View-level filtering: Duplicate logic, error-prone

**Implementation Notes**:

- Default manager excludes datasets with visibility=PRIVATE
- Provide get_all() or with_private() for explicit private dataset access
- Keep optional prefetch methods: with_related(), with_contributors() (SHOULD not MUST)
- Consider adding prefetch for related_literature based on usage patterns
- Document query count expectations and privacy behavior in tests

#### Decision 3: Form Permission Filtering with Base Class Pattern

**Decision**: Filter querysets in form `__init__()` using request.user context; consider moving pattern to base form class

**Rationale**:

- Already implemented in DatasetForm for project field
- Keeps permission logic close to form definition
- Supports both authenticated and anonymous users
- Pattern is widely applicable across FairDM forms
- Flexible for future permission complexity

**Alternatives Considered**:

- View-level queryset filtering: Duplicate logic across views
- Middleware filtering: Too global, affects all forms
- Guardian integration at form level: Overkill for simple permission checks

**Implementation Notes**:

- Accept optional request parameter in `__init__()`
- Filter project queryset to user.projects.all() for authenticated users
- Consider public project filtering for anonymous users
- Add clear docstring explaining request parameter usage
- Research moving pattern to base form class if applicable to multiple forms
- All help_text must use gettext_lazy() for internationalization
- Help text should be form-specific, not copied from model

#### Decision 4: Filter Implementation with Cross-Relationship Support

**Decision**: Extend django-filter BaseListFilter with generic search and cross-relationship filters

**Rationale**:

- BaseListFilter provides consistent interface across FairDM
- django-filter handles filter combinations automatically (AND logic by default)
- Generic search field improves UX over individual text filters
- Cross-relationship filters (descriptions, dates) enable metadata filtering
- Already used in existing DatasetFilter

**Alternatives Considered**:

- Individual text field filters: Verbose, poor UX
- Custom filter implementation: Reinvents django-filter functionality
- URL parameter parsing: Error-prone, no form rendering
- JavaScript-based filtering: Requires API, out of scope

**Implementation Notes**:

- Add fields: project (ChoiceFilter), visibility (ChoiceFilter), license (exact match)
- Remove: added/modified date range filters (not helpful per clarification)
- Add: Generic search field matching across multiple CharField/TextField fields
- Add: Cross-relationship filters for descriptions and dataset dates
- Research performance implications of cross-relationship filters
- Consider database indexing for frequently filtered relationships
- Test filter combinations (AND logic handled by django-filter)

#### Decision 5: Admin Bulk Actions (Limited)

**Decision**: Provide bulk metadata export only; NO bulk visibility changes

**Rationale**:

- Bulk visibility changes are too dangerous - could accidentally expose private datasets
- Portal administrators may not fully understand implications
- Data protection is constitutional requirement
- Bulk metadata export is safe and useful

**Alternatives Considered**:

- Bulk visibility changes with confirmation: Still too risky
- No bulk operations at all: Reduces admin productivity for safe operations
- JavaScript-based bulk operations: Requires API, out of scope

**Implementation Notes**:

- Add admin actions: export_metadata (JSON, DataCite format)
- Do NOT implement: make_public, make_private, make_internal
- Use queryset.update() for safe bulk operations only
- Provide message feedback for export operations
- Respect object-level permissions for all bulk actions
- Document rationale for no bulk visibility changes

#### Decision 6: Test Data Factory Pattern

**Decision**: Use factory-boy DjangoModelFactory with sensible defaults

**Rationale**:

- Mandated by spec 002-testing-strategy
- factory-boy is industry standard for Django test data
- Supports SubFactory for related objects
- Enables downstream portal reuse

**Alternatives Considered**:

- Manual test data creation: Too verbose, hard to maintain
- Django fixtures (JSON/YAML): Brittle, hard to customize
- pytest fixtures only: Not reusable in non-pytest contexts

**Implementation Notes**:

- Create DatasetFactory in fairdm/core/factories.py
- Re-export from fairdm/factories.py for downstream use
- Include SubFactory for project, license (if applicable)
- Support all fields with sensible defaults (Faker where appropriate)
- Document factory in docstring with usage examples

#### Decision 7: License Default Configuration

**Decision**: Hard-code CC BY 4.0 as default license instead of using settings

**Rationale**:

- CC BY 4.0 is FairDM's recommended default per clarification
- Hard-coding provides predictable behavior across portals
- Settings-based approach adds unnecessary configuration complexity
- Portals can still override via form/view logic if needed

**Alternatives Considered**:

- Settings-based default: Requires configuration, less predictable
- No default: Poor UX, users must always select

**Implementation Notes**:

- Set default in DatasetForm to License.objects.filter(name="CC BY 4.0").first()
- Document default in form help_text using gettext_lazy()
- Test that default applies correctly on form instantiation

#### Decision 8: DOI via Identifier Model

**Decision**: Support DOI through DatasetIdentifier model with identifier_type='DOI'

**Rationale**:

- Consistent with FAIR metadata pattern (identifiers as related objects)
- Allows multiple identifiers of different types (DOI, Handle, ARK, etc.)
- Reference field should be reserved for actual literature items/publications
- Cleaner separation of concerns

**Alternatives Considered**:

- OneToOne reference field: Confuses DOI with publication metadata
- Direct DOI field on Dataset: Doesn't scale to multiple identifier types

**Implementation Notes**:

- Use existing DatasetIdentifier model with identifier_type='DOI'
- Validate identifier_type against FairDMIdentifiers vocabulary
- Reference field remains for linking to LiteratureItem (dataset publication)
- Form should provide easy DOI entry (consider separate field that creates identifier)

#### Decision 9: Literature Relationships with DataCite Types

**Decision**: Create intermediate model for Dataset-Literature relationships with DataCite relationship types

**Rationale**:

- DataCite provides standardized relationship vocabulary
- Enables rich metadata about how datasets relate to publications
- Supports future DataCite metadata export
- Aligns with FAIR interoperability principles

**Alternatives Considered**:

- Simple ManyToMany: Loses relationship type information
- JSON field with types: Not queryable, harder to validate

**Implementation Notes**:

- Create DatasetLiteratureRelation intermediate model
- Include relationship_type field with DataCite choices (IsCitedBy, Cites, IsSupplementTo, IsSupplementedBy, IsReferencedBy, References, IsDocumentedBy, Documents)
- Research complete DataCite RelationType vocabulary during implementation
- Provide through= parameter on related_literature ManyToMany field
- Document DataCite relationship types in model docstring

#### Decision 10: Dynamic Inline Form Limits

**Decision**: Calculate inline form max_num based on vocabulary size dynamically

**Rationale**:

- Vocabularies may be extended post-deployment
- Hard-coded limits (6) may be insufficient or excessive
- Dynamic calculation ensures forms match available choices
- Improves maintainability and extensibility

**Alternatives Considered**:

- Hard-coded max_num: Breaks when vocabularies extended
- No limit: Poor UX with too many empty forms

**Implementation Notes**:

- For DescriptionInline: max_num = len(Dataset.DESCRIPTION_TYPES)
- For DateInline: max_num = len(Dataset.DATE_TYPES)
- Consider using ModelAdmin.get_formset() to dynamically set max_num
- Test that forms adapt when vocabularies change

#### Decision 11: Autocomplete Widget Strategy

**Decision**: Use Django admin built-in autocomplete where possible; explicit Select2 only when needed

**Rationale**:

- Django admin 3.2+ includes autocomplete functionality
- Built-in autocomplete is simpler and better maintained
- Explicit Select2 only needed for custom queryset filtering
- Consistent with Django best practices

**Alternatives Considered**:

- Always use Select2: Unnecessary dependency
- Always use built-in: May not support all use cases

**Implementation Notes**:

- Use autocomplete_fields in ModelAdmin for ForeignKey/ManyToMany
- Fall back to Select2Widget only if per-dataset queryset filtering needed
- Apply autocomplete consistently across all applicable fields per clarification
- Document widget choices in admin class docstrings

#### Decision 12: Role-Based Permissions

**Decision**: Map FairDM roles to Django permissions using Dataset.CONTRIBUTOR_ROLES

**Rationale**:

- Consistent with spec 005-core-projects approach
- FairDM roles provide domain-specific permission modeling
- Django permissions provide enforcement mechanism
- Guardian enables object-level permission checks

**Alternatives Considered**:

- Direct permission assignment: Bypasses role abstraction
- Group-based only: Less flexible for object-level control

**Implementation Notes**:

- Define Dataset.CONTRIBUTOR_ROLES vocabulary (e.g., DatasetViewer, DatasetEditor, DatasetManager)
- Map roles to permissions: Viewer→view_dataset, Editor→view/add/change, Manager→all
- Use Guardian for object-level permission assignment
- Document role-permission mapping in models.py
- Test permission enforcement at object level

### Edge Case Resolutions

The spec identifies 15 edge cases requiring decisions. Based on research and user clarifications:

1. **Orphaned datasets on project deletion**
   - **Resolution**: Use PROTECT behavior (CLARIFIED)
   - **Rationale**: Prevents accidental data loss; projects with datasets cannot be deleted until datasets are reassigned or removed
   - **Implementation**: Change on_delete=models.CASCADE to models.PROTECT; orphaned datasets (project=null) are permitted but not encouraged

2. **Duplicate dataset names**
   - **Resolution**: Allow duplicates (no unique constraint)
   - **Rationale**: Multiple datasets may legitimately share names across different projects; UUID provides uniqueness
   - **Implementation**: No code change needed, document in model docstring

3. **Visibility inheritance from project**
   - **Resolution**: No automatic inheritance (deferred to future spec)
   - **Rationale**: Dataset visibility is independent business decision; automatic changes could surprise users
   - **Implementation**: Document as manual administrator task, consider future signal/automation

4. **License changes after publication**
   - **Resolution**: Allow changes but add warning if DOI exists
   - **Rationale**: License corrections may be necessary; legal requirements vary by institution
   - **Implementation**: Check for DOI in DatasetIdentifier with identifier_type='DOI'; add admin warning message; document in form help_text using gettext_lazy()

5. **Related literature deletion behavior**
   - **Resolution**: Keep SET_NULL for reference, CASCADE for ManyToMany
   - **Rationale**: Primary DOI reference should survive literature item deletion; related literature is secondary
   - **Implementation**: Document behavior in model docstring

6. **Empty datasets (no samples/measurements)**
   - **Resolution**: Allow but flag in admin list_display
   - **Rationale**: Datasets may be created before data collection; preview/planning phase is valid
   - **Implementation**: Add has_data property, display in admin with icon/color

7. **Contributor role validation**
   - **Resolution**: Add validator to ensure role in CONTRIBUTOR_ROLES vocabulary
   - **Rationale**: Consistent with FAIR metadata requirements
   - **Implementation**: Add validator to Contribution model (may be in contrib app)

8. **Date type validation**
   - **Resolution**: Add validator to DatasetDate.date_type
   - **Rationale**: Ensures controlled vocabulary compliance
   - **Implementation**: Validator checks against DATE_TYPES vocabulary

9. **Description type validation**
   - **Resolution**: Add validator to DatasetDescription.description_type
   - **Rationale**: Ensures controlled vocabulary compliance
   - **Implementation**: Validator checks against DESCRIPTION_TYPES vocabulary

10. **UUID collision handling**
    - **Resolution**: Rely on ShortUUID uniqueness + database constraint
    - **Rationale**: Collision probability is astronomically low; database will raise IntegrityError if occurs
    - **Implementation**: No special handling needed, document in model docstring

11. **Image aspect ratio** (NEW)
    - **Resolution**: Research and define optimal aspect ratio for responsive layouts
    - **Rationale**: Images used in cards and HTML meta tags need consistent sizing
    - **Implementation**: Research Bootstrap card image best practices, test across viewports, document recommended ratio (e.g., 16:9, 4:3, or 1:1)

12. **Cross-relationship filter performance** (NEW)
    - **Resolution**: Implement with indexing; measure performance in tests
    - **Rationale**: Filtering by descriptions/dates requires joins; performance critical for usability
    - **Implementation**: Add database indexes to description_type and date_type fields, write performance tests with large datasets

13. **Dynamic inline form limits** (NEW)
    - **Resolution**: Calculate max_num from vocabulary size (Decision 10)
    - **Rationale**: Vocabularies may be extended; forms should adapt automatically
    - **Implementation**: Use get_formset() to set max_num dynamically based on len(VOCABULARY)

14. **Generic search field scope** (NEW)
    - **Resolution**: Define searchable field set; exclude large text fields
    - **Rationale**: Balance between comprehensive search and performance
    - **Implementation**: Include: name, uuid, keyword names; exclude: descriptions (too large, use separate filter)

15. **Literature relationship types** (NEW)
    - **Resolution**: Implement DatasetLiteratureRelation with DataCite types (Decision 9)
    - **Rationale**: Standardized vocabulary, FAIR interoperability
    - **Implementation**: Research DataCite RelationType vocabulary, implement intermediate model, validate relationship_type

### Research Complete

All clarifications resolved. 12 technology/pattern decisions documented with rationale. 15 edge cases resolved with implementation guidance. Ready for Phase 1: Data Model & Contracts.

---

## Phase 1: Data Model & Contract Design

**Objective**: Document data structures, validation rules, and component interfaces reflecting all clarifications.

### Data Model Enhancements

See [data-model.md](data-model.md) (to be created) for detailed entity definitions, field specifications, relationships, and validation rules.

**Summary of model changes**:

1. **Dataset model**:
   - **CHANGE**: project.on_delete from CASCADE to PROTECT (prevents accidental deletion)
   - **CHANGE**: Default manager excludes PRIVATE datasets (privacy-first)
   - Add field validators for name (required, max_length)
   - Document visibility choices and PRIVATE default
   - Add/enhance docstrings for all fields
   - Document orphaned dataset behavior (project=null permitted)

2. **DatasetQuerySet**:
   - **NEW**: Default excludes datasets with visibility=PRIVATE
   - **NEW**: get_all() or with_private() method for explicit private access
   - Document existing methods: with_related(), with_contributors() (now optional SHOULD not MUST)
   - Ensure proper prefetch optimization
   - Add privacy-first behavior tests
   - Add tests for query count

3. **DatasetLiteratureRelation** (NEW intermediate model):
   - **CREATE**: Intermediate model for Dataset.related_literature ManyToMany
   - Fields: dataset (ForeignKey), literature_item (ForeignKey), relationship_type (CharField with DataCite choices)
   - Choices: IsCitedBy, Cites, IsSupplementTo, IsSupplementedBy, IsReferencedBy, References, IsDocumentedBy, Documents
   - Research complete DataCite RelationType vocabulary
   - Validate relationship_type against vocabulary

4. **DatasetDescription, DatasetDate, DatasetIdentifier**:
   - Add vocabulary validation to type fields
   - Document available vocabulary choices
   - Enhance error messages with vocabulary URIs
   - **DOI support**: via DatasetIdentifier with identifier_type='DOI', not reference field

5. **DatasetForm**:
   - **CHANGE**: Default license to CC BY 4.0 (hard-coded, not settings-based)
   - **CHANGE**: All help_text must use gettext_lazy() for i18n
   - **CHANGE**: Help_text should be form-specific, not copied from model
   - **CHANGE**: Apply autocomplete to ALL applicable fields (not just project)
   - Document request parameter usage
   - Add field validators
   - Consider DOI entry field that creates DatasetIdentifier
   - Research moving request pattern to base form class

6. **DatasetFilter**:
   - **REMOVE**: added/modified date range filters (not helpful)
   - **ADD**: Generic search field matching across name, uuid, keywords
   - **ADD**: Cross-relationship filter for descriptions (research performance)
   - **ADD**: Cross-relationship filter for dataset dates
   - Add project filter (ChoiceFilter)
   - Add visibility filter (ChoiceFilter)
   - Keep license filter (exact match)
   - Document AND logic (django-filter default)
   - Add performance tests for cross-relationship filters

7. **DatasetAdmin**:
   - **REMOVE**: Bulk visibility change actions (too dangerous)
   - **ADD**: Bulk metadata export action (safe)
   - **CHANGE**: Use Django autocomplete_fields where possible instead of explicit Select2
   - **CHANGE**: Dynamic inline limits based on vocabulary size (get_formset)
   - **CHANGE**: Research and implement improved fieldset organization
   - Add has_data to list_display
   - Add project, license, visibility to list_filter
   - Document readonly fields (uuid, timestamps)
   - Add license change warning if DOI exists

### API Contracts

See [contracts/](contracts/) directory (to be created) for detailed interface specifications.

**Contracts to define**:

1. **models.py**: Dataset model interface
   - Public methods and properties
   - Field types and constraints
   - Related model interfaces (DatasetDescription, DatasetDate, DatasetIdentifier, DatasetLiteratureRelation)
   - Privacy-first queryset behavior
   - PROTECT behavior for project deletion

2. **querysets.py**: DatasetQuerySet interface
   - Method signatures: get_all(), with_private(), with_related(), with_contributors()
   - Return types and query optimization guarantees
   - Privacy-first default behavior
   - Query count expectations for optimization methods

3. **forms.py**: DatasetForm interface
   - Field definitions with autocomplete on all applicable fields
   - Validation rules
   - Request context handling
   - License default (CC BY 4.0)
   - gettext_lazy() usage for help_text
   - DOI entry field specification

4. **filters.py**: DatasetFilter interface
   - Filter field types (project, license, visibility)
   - Generic search field specification
   - Cross-relationship filters (descriptions, dates)
   - Performance expectations
   - AND logic combination behavior

5. **admin.py**: DatasetAdmin interface
   - Search, filter, and display configurations
   - Dynamic inline formset limits
   - Bulk action specifications (export only, no visibility changes)
   - Autocomplete field configurations
   - License change warning logic

6. **intermediate_models.py**: DatasetLiteratureRelation interface
   - Field definitions
   - DataCite relationship type choices
   - Validation rules

### Quick Start Guide

See [quickstart.md](quickstart.md) (to be created) for developer onboarding.

**Quick start topics**:

1. Creating a dataset programmatically (respecting privacy-first defaults)
2. Using DatasetForm in views with request context
3. Applying DatasetFilter with generic search and cross-relationship filters
4. Customizing DatasetAdmin with dynamic inlines
5. Writing tests with DatasetFactory
6. Working with DatasetLiteratureRelation for literature links
7. Understanding privacy-first queryset behavior
8. Adding DOI via DatasetIdentifier
9. Role-based permissions with FairDM roles
10. Common patterns and gotchas (PROTECT behavior, orphaned datasets, etc.)

### Demo App Updates

**Mandatory updates** per Principle VII:

1. **fairdm_demo/models.py**:
   - Add example usage of DatasetLiteratureRelation intermediate model
   - Document privacy-first queryset usage patterns
   - Show proper DOI identifier creation
   - Document best practices in docstrings linking to relevant docs

2. **fairdm_demo/config.py** (or admin.py):
   - Show DatasetAdmin customization with dynamic inline limits
   - Demonstrate autocomplete configuration
   - Show bulk export action implementation
   - Document fieldset organization best practices

3. **fairdm_demo/factories.py**:
   - Show DatasetFactory usage with CC BY 4.0 default
   - Demonstrate SubFactory for project, license
   - Show creation of related DatasetIdentifier for DOI
   - Show creation of DatasetLiteratureRelation examples
   - Link to documentation in docstrings

4. **fairdm_demo/forms.py**:
   - Show DatasetForm customization with request context
   - Demonstrate gettext_lazy() usage for help_text
   - Show DOI entry field implementation
   - Document base form pattern if implemented

5. **fairdm_demo/filters.py**:
   - Show generic search field implementation
   - Demonstrate cross-relationship filters
   - Document performance considerations

### Phase 1 Deliverables

- [ ] data-model.md created with updated entity definitions reflecting all clarifications
- [ ] contracts/ directory with 6 interface specification files
- [ ] quickstart.md with comprehensive developer onboarding (10 topics)
- [ ] Demo app updated in 5 files with examples and docstrings
- [ ] All clarifications from Session 2026-01-15 incorporated
- [ ] 12 technology decisions documented and validated
- [ ] 15 edge cases resolved with implementation guidance

**Phase 1 complete. Ready for Phase 2 (tasks.md via /speckit.tasks).**
