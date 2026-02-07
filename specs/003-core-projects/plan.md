# Implementation Plan: Core Projects MVP

**Branch**: `003-core-projects` | **Date**: January 14, 2026 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-core-projects/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Polish the `fairdm.core.project` app to MVP state with focus on: (1) model refinements including i18n compliance and DataCite funding schema, (2) streamlined creation forms with role-based permissions, (3) comprehensive admin interface with inline editing, (4) advanced filtering and search capabilities, (5) proper validation and error handling. Technical approach includes leveraging existing django-tables2, django-filter, django-guardian infrastructure while ensuring consistent use of Cotton components for UI and maintaining test-first discipline per constitution.

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: Django 5.1.3, django-guardian, django-tables2, django-filter, django-crispy-forms, crispy-bootstrap5, django-cotton, django-import-export, Django REST Framework
**Storage**: PostgreSQL (primary), supports SQLite for development
**Testing**: pytest, pytest-django, pytest-playwright (for UI tests), factory-boy (fixtures)
**Target Platform**: Linux server (Docker/docker-compose deployable), 12-factor configuration via django-environ
**Project Type**: Django web application (server-rendered templates with Bootstrap 5 + HTMX + Alpine.js enhancements)
**Performance Goals**:

- Project list load <1s for 10k projects (50 per page)
- Single filter operation <500ms for 10k projects
- Admin search <300ms
- Detail view <5 database queries via select_related/prefetch_related
**Constraints**:
- Must maintain backward compatibility with existing Project model migrations
- Must use Cotton components for UI consistency
- All user-facing strings must use Django i18n (_() wrapper)
- Tests must follow established taxonomy (unit/integration/contract)
**Scale/Scope**:
- Existing Project model with ~10 fields, 3 related models (ProjectDescription, ProjectDate, ProjectIdentifier)
- ~15 files to modify across models, forms, admin, filters, views, templates
- 25 functional requirements to implement
- 6 user stories with 31 acceptance scenarios

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: FAIR-First Research Portals ✅

- **Alignment**: Feature directly enhances FAIR compliance by improving Project metadata collection (descriptions, dates, identifiers following DataCite schema), searchability, and machine-readable exports (JSON-LD, DataCite JSON).
- **Persistent Identifiers**: FR-002 ensures unique UUID generation, FR-005 adds external identifier support (DOI, grant numbers).
- **Public Access**: FR-007 defines visibility levels supporting public discovery without custom client code.
- **Verdict**: PASS - Feature strengthens FAIR characteristics across all dimensions.

### Principle II: Domain-Driven, Declarative Modeling ✅

- **Alignment**: Work focuses on existing core Project model (part of canonical backbone), with related models (ProjectDescription, ProjectDate, ProjectIdentifier) following declarative patterns.
- **Schema Declaration**: Uses standard Django model fields, no runtime ad-hoc structures. Related models use controlled vocabularies for types.
- **Registry Integration**: Project model already registered; improvements maintain registration-based approach.
- **Verdict**: PASS - Adheres to declarative modeling principles, strengthens core backbone.

### Principle III: Configuration Over Custom Plumbing ✅

- **Alignment**: Leverages django-tables2, django-filter, django-crispy-forms for auto-generated tables/filters/forms. Admin improvements use inline formsets and standard Django patterns.
- **Defaults**: Auto-generates sensible defaults where possible (e.g., filter fields from model, table columns from list_fields).
- **No Custom Routing**: Uses existing URL patterns and view infrastructure.
- **Verdict**: PASS - Exemplifies configuration-over-code philosophy.

### Principle IV: Opinionated, Production-Grade Defaults ✅

- **Stack Compliance**: Uses Django 5.1.3, django-guardian for permissions, django-tables2/filter for UI, Bootstrap 5 + Cotton components, HTMX enhancements.
- **Deployment**: Changes are Docker-compatible, use django-environ for configuration.
- **Database**: Works with PostgreSQL (and SQLite for dev).
- **UI**: Server-rendered templates with Cotton components, no SPA requirements.
- **Verdict**: PASS - Fully aligned with mandated stack and deployment patterns.

### Principle V: Test-First Quality & Sustainability ✅

- **Test-First Commitment**: Plan includes explicit test requirements for each user story. Tests will be written before implementation (Red → Green → Refactor).
- **Coverage Strategy**:
  - Unit tests for model methods, form validation, filter logic
  - Integration tests for view workflows, permission checks, database queries
  - Contract tests (pytest-playwright) for UI interactions, form submissions, filtering
- **Quality Over Quantity**: Tests focus on critical paths (CRUD operations, permission enforcement, data validation) and edge cases (date conflicts, duplicate descriptions, orphaned projects).
- **Cotton Component Tests**: Will use `django_cotton.render_component()` with pytest-django fixtures as mandated.
- **Verdict**: PASS - Committed to test-first discipline and comprehensive coverage strategy.

### Principle VI: Documentation Critical ✅

- **Documentation Plan**:
  - Update developer guide with Project model patterns, permission model, DataCite funding schema
  - Update admin guide with new admin features and bulk operations
  - Update contributor guide with project creation workflow, metadata best practices
  - Add inline code examples for form usage, filter configuration, admin customization
- **Docstrings**: All new/modified classes and methods will include comprehensive docstrings
- **API Documentation**: Update any affected API endpoint documentation
- **Verdict**: PASS - Documentation updates planned alongside implementation.

### Principle VII: Living Demo & Reference Implementation ✅

- **Demo App Impact**: fairdm_demo already includes example Project usage. Changes will require:
  - Update demo factories to use DataCite funding schema
  - Add examples of role-based permission patterns
  - Demonstrate streamlined creation workflow
  - Show proper i18n string wrapping
- **Docstring Links**: Demo code will link to relevant documentation sections
- **Synchronization**: Demo app updates will be included in same PR as framework changes
- **Verdict**: PASS - Demo app maintenance explicitly planned.

### Architecture & Stack Constraints ✅

- **Python/Django**: Core Django app modification, no alternative frameworks
- **Database**: PostgreSQL-compatible migrations, standard Django ORM
- **Testing**: pytest + pytest-django + pytest-playwright
- **Frontend**: Bootstrap 5 + Cotton + HTMX, no SPA
- **Configuration**: Environment-based via django-environ
- **Verdict**: PASS - No architectural constraints violated.

### Development Workflow & Quality Gates ✅

- **Specification First**: spec.md complete with user stories, requirements, success criteria
- **Planning**: This plan.md documents technical context and alignment
- **Constitution Check**: This section validates alignment (currently in progress)
- **Next**: Phase 0 research will resolve any technical unknowns, Phase 1 will create contracts
- **Verdict**: PASS - Following prescribed workflow.

**OVERALL GATE STATUS: ✅ PASS** - All constitutional principles aligned, no violations, ready for Phase 0 research.

## Project Structure

### Documentation (this feature)

```text
specs/003-core-projects/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
fairdm/core/project/
├── __init__.py
├── admin.py             # Enhanced admin with inlines, filters, bulk actions
├── apps.py
├── filters.py           # ProjectFilter with keyword/tag/contributor filters
├── forms.py             # Streamlined ProjectForm for creation
├── models.py            # Project, ProjectDescription, ProjectDate, ProjectIdentifier
├── options.py           # ModelConfiguration for registry (if needed)
├── plugins.py           # Project detail page plugins (if any)
├── receivers.py         # Signal handlers (if any)
├── serializers.py       # DRF serializers for API (if enabled)
├── tables.py            # django-tables2 ProjectTable
├── urls.py              # URL routing for CRUD views
├── views.py             # CRUD views with permission checks
└── migrations/          # Database migrations (existing + new)

fairdm/core/project/templates/project/
├── project_list.html    # List view with filters and tables
├── project_detail.html  # Detail view with tabbed metadata
├── project_form.html    # Create/edit form (streamlined)
└── components/          # Cotton components
    ├── project_card.html
    ├── project_metadata.html
    └── project_filters.html

fairdm_demo/
├── models.py            # Demo Project examples (update funding schema)
├── factories.py         # Factory fixtures (update for DataCite)
└── tests/               # Demo-specific tests

tests/
├── unit/
│   └── core/
│       └── project/
│           ├── test_models.py        # Model validation, uniqueness constraints
│           ├── test_forms.py         # Form validation, date checks
│           ├── test_filters.py       # Filter logic
│           └── test_permissions.py   # Role-based permission logic
├── integration/
│   └── core/
│       └── project/
│           ├── test_views.py         # CRUD workflows, redirects
│           ├── test_admin.py         # Admin operations, inline editing
│           └── test_queries.py       # Query optimization, prefetch
└── contract/
    └── core/
        └── project/
            ├── test_creation.py      # E2E project creation flow
            ├── test_metadata.py      # Add descriptions/dates/identifiers
            ├── test_filtering.py     # Filter UI interactions
            └── test_permissions.py   # Permission-based access control
```

**Structure Decision**: Django app structure (Option 2 adapted). FairDM uses a modular Django app architecture where `fairdm/core/project/` contains the complete app implementation. Tests follow the established taxonomy (unit/integration/contract) with pytest-django. Templates use Cotton components for consistency. Demo app provides working examples with proper docstrings linking to documentation.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**No violations recorded** - All constitutional principles are aligned with this feature implementation.
