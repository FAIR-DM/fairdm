# fairdm Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-12-30

## Active Technologies
- Python 3.10+ (current dev environment Python 3.11) + Django, Sphinx (via `fairdm-docs`), MyST Markdown, `pydata-sphinx-theme`, `sphinx-design`, Bootstrap 5, Context7 for library docs
- Python 3.13 (001-production-config-fairdm-conf)
- PostgreSQL (primary), Redis (cache/broker) (001-production-config-fairdm-conf)
- Python 3.11+ + pytest, pytest-django, factory-boy, coverage.py, pytest-playwright (004-testing-strategy-fixtures)
- Test database (PostgreSQL in test mode) with transaction rollback per test, session-level DB creation (004-testing-strategy-fixtures)
- Python 3.13+ + Django 5.1+, django-tables2 2.7+, django-filter 24.3+, django-crispy-forms 2.3+, crispy-bootstrap5 2025.6+, djangorestframework 3.15+, django-import-export 4.0+, django-polymorphic 4.1+ (002-fairdm-registry)
- PostgreSQL (primary), SQLite (development/testing) (002-fairdm-registry)
- Python 3.11+ (Django 4.2+) + django-polymorphic 3.1+, django-guardian 2.4+, django-filter 23.0+, django-crispy-forms 2.0+, django-select2, django-tables2 2.5+, research-vocabs (006-core-measurements)
- PostgreSQL (via Django ORM, no direct SQL) (006-core-measurements)
- Python 3.13, Django 5.x + Django CBVs, django-guardian (object-level perms), django-polymorphic (model inheritance), django-extra-views (InlineFormSetView) (008-plugin-system)
- N/A (no database tables — runtime registration system) (008-plugin-system)
- [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION] + [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION] (009-fairdm-contributors)
- [if applicable, e.g., PostgreSQL, CoreData, files or N/A] (009-fairdm-contributors)
- Python 3.11+ + Django 5.x, django-polymorphic, django-lifecycle, django-guardian, django-allauth, django-countries, Celery, requests, easy-thumbnails, shortuuid, django-ordered-model, research-vocabs, django-import-export, django-autocomplete-light, django-select2 (009-fairdm-contributors)
- PostgreSQL (production), SQLite (development/testing) (009-fairdm-contributors)

- Documentation tooling in Python (version as defined by the `fairdm-docs` package and project-wide tooling); content itself is language-agnostic. + `fairdm-docs` (Sphinx-based tooling and setup utilities), Sphinx, `pydata-sphinx-theme`, existing FairDM documentation sources under `docs/`.

## Project Structure

```text
backend/
frontend/
tests/
```

## Commands

cd src; pytest; ruff check .

## Code Style

Documentation tooling in Python (version as defined by the `fairdm-docs` package and project-wide tooling); content itself is language-agnostic.: Follow standard conventions

## Recent Changes
- 009-fairdm-contributors: Added Python 3.11+ + Django 5.x, django-polymorphic, django-lifecycle, django-guardian, django-allauth, django-countries, Celery, requests, easy-thumbnails, shortuuid, django-ordered-model, research-vocabs, django-import-export, django-autocomplete-light, django-select2
- 009-fairdm-contributors: Added [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION] + [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]
- 008-plugin-system: Added Python 3.13, Django 5.x + Django CBVs, django-guardian (object-level perms), django-polymorphic (model inheritance), django-extra-views (InlineFormSetView)


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
