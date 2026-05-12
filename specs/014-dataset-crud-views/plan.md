# Implementation Plan: Dataset CRUD Views

**Branch**: `014-dataset-crud-views` | **Date**: 2026-05-12 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/014-dataset-crud-views/spec.md`

## Summary

Complete the Dataset CRUD surface by adding `DatasetUpdateView` and `DatasetDeleteView`, refactoring `DatasetCreateView` to use a new `DatasetCreateForm` (restricting fields to `name`, `project`, `license`), and wiring all four URLs. `DatasetForm` remains the full form used by the update view and as the base for `DatasetCreateForm`. Both the create and update views pass `request` to `DatasetForm` to filter the project dropdown to the user's accessible projects. The `visibility` field is intentionally excluded from all forms and is managed via a future publish/unpublish workflow. Deletion is guarded by the existing name-confirmation mechanism (`require_confirmation = True`) and a `django-guardian` object-level permission check. All four patterns mirror the already-implemented Project CRUD pattern exactly.

## Technical Context

**Language/Version**: Python 3.12+, Django 5.x  
**Primary Dependencies**: django-guardian (object-level permissions), django-filter (`DatasetFilter`), django-select2 (autocomplete widgets), django-addanother, licensing (License model)  
**Storage**: PostgreSQL (production), SQLite (dev/test)  
**Testing**: pytest, pytest-django  
**Target Platform**: Linux server (Django web app)  
**Project Type**: Django web application — framework extension  
**Performance Goals**: N/A (CRUD forms, not high-throughput)  
**Constraints**: No new migrations; all changes are view/form/URL layer only. No changes to the Dataset model or DatasetFilter.  
**Scale/Scope**: 4 URL patterns, 2 new view classes, 1 new form class, 1 modified view, 1 modified form module, 1 modified URL module.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. FAIR-First | ✅ Pass | Dataset visibility remains first-class; public-only list view enforces FAIR discoverability. Editing fields do not weaken FAIR characteristics. |
| II. Domain-Driven Modeling | ✅ Pass | No model changes. `DatasetCreateForm` is a declarative subclass of `DatasetForm`; no ad-hoc runtime logic. |
| III. Configuration Over Plumbing | ✅ Pass | Views mirror the established Project CRUD pattern; no novel plumbing invented. |
| IV. Production-Grade Defaults | ✅ Pass | Uses `django-guardian` for object-level permissions (project standard). Bootstrap 5 UI baseline unchanged. |
| V. Test-First Quality | ✅ Pass | URL smoke tests MUST be added for all four routes. Behavior tests for permission denial, form validation, and redirect targets. |
| VI. Documentation Critical | ⚠ Note | No public API changes. Internal docstrings required on new view classes per codebase convention. No doc-site updates needed for this phase. |
| VII. Living Demo | ✅ Pass | No changes to `fairdm_demo` required (Dataset views are core, not demo-specific). |

**Constitution Check — Post-Design**: No violations. No entry required in Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/014-dataset-crud-views/
├── plan.md              ← this file
├── research.md          ← Phase 0 output
├── data-model.md        ← Phase 1 output
├── quickstart.md        ← Phase 1 output
└── tasks.md             ← Phase 2 output (/speckit.tasks)
```

### Source Code (affected files only)

```text
fairdm/core/dataset/
├── forms.py             ← ADD DatasetCreateForm; no changes to DatasetForm
├── views.py             ← MODIFY DatasetCreateView (form_class, remove get_initial);
│                           ADD DatasetUpdateView, DatasetDeleteView
└── urls.py              ← ADD dataset-update, dataset-delete URL patterns

tests/test_core/test_dataset/
└── test_views.py        ← ADD smoke tests + behaviour tests for all four views
```

## Complexity Tracking

*No constitution violations.*
