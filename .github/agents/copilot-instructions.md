# fairdm Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-05-28

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
- Python 3.11+, Django 5.x + django-allauth (authentication, social login, email verification), django-guardian (object-level permissions), django-polymorphic (Contributor hierarchy), django-invitations (invitation-only signup support), django-lifecycle (model hooks), rapidfuzz (fuzzy name matching) (010-profile-claiming)
- PostgreSQL (primary), SQLite (dev/test) (010-profile-claiming)
- Python 3.11+ + Django 5.1.3+, djangorestframework, drf-spectacular[sidecar], dj-rest-auth, django-rest-polymorphic, drf-orjson-renderer, drf-schema-adapter (compatibility risk — see R7), django-parler-rest, django-cors-headers, djangorestframework-guardian (011-restful-api)
- PostgreSQL (existing) (011-restful-api)
- Python 3.11+ + Django 5.1.3+, djangorestframework, drf-spectacular[sidecar], dj-rest-auth, drf-orjson-renderer, django-cors-headers, djangorestframework-guardian (011-restful-api)
- Python 3.12, Django 5.x + djangorestframework, drf-spectacular, django-flex-menus (`flex_menu`), djangorestframework-guardian (011-restful-api)
- PostgreSQL (primary); SQLite (dev/tests) (011-restful-api)
- Python 3.13 (per active virtualenv) + Django, django-mvp, django-meta (`MetadataMixin`), django-filter (`FilterView`), django-tables2 (`MVPTableViewMixin`), pytest, pytest-django (012-base-views-docs)
- PostgreSQL (test DB via pytest-django) (012-base-views-docs)
- Python 3.13 + Django 5.x, django-guardian (object permissions), django-filter (ProjectFilter), FairDM base views (`FairDMListView`, `FairDMCreateView`, `FairDMUpdateView`, `FairDMDeleteView`), crispy-forms (existing forms) (013-project-crud-views)
- PostgreSQL (primary); SQLite (test/dev) (013-project-crud-views)
- Python 3.12+, Django 5.x + django-guardian (object-level permissions), django-filter (`DatasetFilter`), django-select2 (autocomplete widgets), django-addanother, licensing (License model) (014-dataset-crud-views)
- PostgreSQL (production), SQLite (dev/test) (014-dataset-crud-views)
- Python 3.13, Django 5.x + easy-thumbnails =2.10,<3.0 (already installed); Pillow (transitive via easy-thumbnails); django-mvp (Bootstrap 5 UI) (015-image-field-spec)
- `FileSystemStorage` (local dev), S3-compatible (production) � both already configured (015-image-field-spec)

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
- 015-image-field-spec: Added Python 3.13, Django 5.x + easy-thumbnails =2.10,<3.0 (already installed); Pillow (transitive via easy-thumbnails); django-mvp (Bootstrap 5 UI)
- 014-dataset-crud-views: Added Python 3.12+, Django 5.x + django-guardian (object-level permissions), django-filter (`DatasetFilter`), django-select2 (autocomplete widgets), django-addanother, licensing (License model)
- 013-project-crud-views: Added Python 3.13 + Django 5.x, django-guardian (object permissions), django-filter (ProjectFilter), FairDM base views (`FairDMListView`, `FairDMCreateView`, `FairDMUpdateView`, `FairDMDeleteView`), crispy-forms (existing forms)


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
