# Implementation Plan: Core Sample Model Enhancement

**Branch**: `007-core-samples` | **Date**: 2026-01-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/007-core-samples/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Cleanup and enhancement of the `fairdm.core.sample` app focusing on models, model managers, forms, filters, and admin interfaces. The Sample model is a polymorphic base class (via django-polymorphic) that integrates with the FairDM registry system (Feature 004) and aligns with IGSN metadata schema. Developers can create domain-specific sample types that automatically get forms, filters, tables, and admin interfaces through registry registration. Provides base mixins (SampleFormMixin, SampleFilterMixin) for reusable sample functionality. Includes typed sample relationships for provenance tracking.

## Technical Context

**Language/Version**: Python 3.11 (per project pyproject.toml)
**Primary Dependencies**:

- Django 5.x (web framework)
- django-polymorphic 3.1+ (polymorphic model support)
- django-guardian 2.4+ (object-level permissions)
- django-crispy-forms 2.0+ (form layouts)
- django-filter 23.0+ (filtering)
- django-tables2 2.5+ (table rendering)
- research-vocabs (FairDM controlled vocabularies)
- shortuuid 1.0+ (unique identifiers)

**Storage**: PostgreSQL (primary target, Django ORM migrations)
**Testing**: pytest + pytest-django (flat test structure mirroring source code as per Architecture & Stack Constraints > Testing & Tooling)
**Target Platform**: Linux server (containerized deployment, Django WSGI application)
**Project Type**: Django app within monolithic FairDM framework
**Performance Goals**:

- Sample CRUD operations < 2 seconds
- List queries with 1000+ polymorphic samples < 1 second with optimized querysets
- Polymorphic queries < 200ms for paginated results

**Constraints**:

- Must not duplicate Feature 004 (registry system) functionality
- Must integrate with Feature 006 (datasets) - samples belong to datasets
- IGSN metadata schema compliance (v1.0, monitor redesign project)
- Polymorphic model inheritance patterns (django-polymorphic)
- Client-side views/API out of scope (deferred to future features)

**Scale/Scope**:

- Support 100,000+ sample records with mixed polymorphic types
- Handle deep sample relationship hierarchies (5+ levels)
- Admin interface manages 500+ samples per dataset
- Multiple custom sample types per portal

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: FAIR-First Research Portals ✅

- Sample model aligns with IGSN metadata schema for FAIR compliance
- Supports persistent identifiers (UUID, IGSN)
- Concrete ForeignKey relationships for rich metadata (descriptions, dates, identifiers) - 2-4x faster queries
- GenericRelation for contributors to support polymorphic contributor model across core objects
- Object-level permissions via django-guardian
- Status: **COMPLIANT**

### Principle II: Domain-Driven, Declarative Modeling ✅

- Sample is polymorphic base model extending core FairDM backbone
- Domain-specific sample types expressed as explicit Django models
- Registry integration provides declarative configuration (Feature 004)
- Mixins (SampleFormMixin, SampleFilterMixin) provide reusable patterns
- Status: **COMPLIANT**

### Principle III: Configuration Over Custom Plumbing ✅

- Registry auto-generates forms, filters, tables, admin from model configuration
- Developers register models, not rewrite plumbing
- Base mixins reduce boilerplate for custom sample types
- Status: **COMPLIANT**

### Principle IV: Opinionated, Production-Grade Defaults ✅

- Uses Django ecosystem (django-polymorphic, django-guardian, django-filter, django-tables2)
- Bootstrap 5 UI with HTMX/Alpine.js enhancements (out of scope for this feature, but admin follows patterns)
- Sensible defaults (status values, UUID generation, polymorphic queries)
- Status: **COMPLIANT**

### Principle V: Test-First Quality & Sustainability ✅

- Comprehensive test requirements (FR-061 through FR-070)
- Test-first discipline for all model/form/filter/admin behavior
- Test organization mirrors source code structure (flat, no layer subdirectories) as per Architecture & Stack Constraints > Testing & Tooling
- Factory-boy for test data generation
- Per-method query-count assertions for database performance
- See [fairdm-testing skill](../../.github/skills/fairdm-testing/SKILL.md) for pytest conventions and patterns
- Status: **COMPLIANT** - Tests must be written before implementation

### Principle VI: Documentation Critical ✅

- All public forms, filters, admin configurations must be documented
- Mixins require usage examples
- Migration guides for any breaking changes to Sample model
- See [fairdm-documentation skill](../../.github/skills/fairdm-documentation/SKILL.md) for MyST Markdown syntax, audience guidelines, and citation requirements
- Status: **COMPLIANT** - Documentation updates required with code changes

### Principle VII: Living Demo & Reference Implementation ✅

- `fairdm_demo` must be updated with sample registration examples
- Demo app must show polymorphic sample types in action
- Docstrings linking to documentation required
- Status: **COMPLIANT** - Demo app updates REQUIRED in same PR

**Overall Gate Status**: ✅ **PASS** - No constitutional violations. Feature aligns with all core principles.

## Project Structure

### Documentation (this feature)

```text
specs/007-core-samples/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output - sample relationships research
├── data-model.md        # Phase 1 output - Sample model, relationships, metadata
├── quickstart.md        # Phase 1 output - Developer guide for custom sample types
├── contracts/           # Phase 1 output - N/A (admin/forms, not API contracts)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
fairdm/
└── core/
    ├── models/
    │   ├── sample.py              # Enhanced Sample model with polymorphic support
    │   ├── sample_metadata.py     # SampleDescription, SampleDate, SampleIdentifier
    │   └── sample_relation.py     # SampleRelation for provenance
    ├── managers/
    │   └── sample.py              # SampleQuerySet with optimizations
    ├── forms/
    │   ├── sample.py              # SampleForm, SampleFormMixin
    │   └── sample_metadata.py     # Inline forms for descriptions/dates/identifiers
    ├── filters/
    │   └── sample.py              # SampleFilter, SampleFilterMixin
    ├── admin/
    │   └── sample.py              # SampleAdmin with polymorphic support
    └── migrations/
        └── 00XX_enhance_sample_*.py

fairdm_demo/
├── models.py                      # Example polymorphic sample types (RockSample, WaterSample)
├── config.py                      # Sample registration with registry
├── forms.py                       # Example custom forms using SampleFormMixin
├── filters.py                     # Example custom filters using SampleFilterMixin
└── admin.py                       # Example custom admin for sample types

tests/
└── test_core/
    └── test_sample/
        ├── test_models.py              # Sample model, queryset, polymorphic behavior
        ├── test_forms.py               # SampleFormMixin, auto-generated forms
        ├── test_filters.py             # SampleFilterMixin, auto-generated filters
        ├── test_admin.py               # SampleAdmin integration tests
        ├── test_registry.py            # Sample registration and auto-generation
        ├── test_relationships.py       # Dataset relationships, polymorphic queries
        └── test_crud.py                # End-to-end CRUD flows
```

**Structure Decision**: Django app enhancement within existing `fairdm/core/` structure. This is core framework functionality, not a new app. Demo app (`fairdm_demo/`) updated to demonstrate polymorphic sample usage and registration patterns.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**No violations detected** - This table intentionally left empty.
