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
- 006-core-measurements: Added Python 3.11+ (Django 4.2+) + django-polymorphic 3.1+, django-guardian 2.4+, django-filter 23.0+, django-crispy-forms 2.0+, django-select2, django-tables2 2.5+, research-vocabs
- 002-fairdm-registry: Added Python 3.13+ + Django 5.1+, django-tables2 2.7+, django-filter 24.3+, django-crispy-forms 2.3+, crispy-bootstrap5 2025.6+, djangorestframework 3.15+, django-import-export 4.0+, django-polymorphic 4.1+
- 002-fairdm-registry: Added Python 3.13+ + Django 5.1+, django-tables2 2.7+, django-filter 24.3+, django-crispy-forms 2.3+, crispy-bootstrap5 2025.6+, djangorestframework 3.15+, django-import-export 4.0+, django-polymorphic 4.1+


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
