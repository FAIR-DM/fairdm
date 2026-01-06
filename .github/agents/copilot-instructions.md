# fairdm Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-12-30

## Active Technologies
- Python 3.10+ (current dev environment Python 3.11) + Django, Sphinx (via `fairdm-docs`), MyST Markdown, `pydata-sphinx-theme`, `sphinx-design`, Bootstrap 5, Context7 for library docs (001-documentation-baseline)
- N/A for this feature (documentation only; code and data models already exist in core FairDM) (001-documentation-baseline)
- Python 3.13 (001-production-config-fairdm-conf)
- PostgreSQL (primary), Redis (cache/broker) (001-production-config-fairdm-conf)

- Documentation tooling in Python (version as defined by the `fairdm-docs` package and project-wide tooling); content itself is language-agnostic. + `fairdm-docs` (Sphinx-based tooling and setup utilities), Sphinx, `pydata-sphinx-theme`, existing FairDM documentation sources under `docs/`. (001-documentation-baseline)

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
- 001-production-config-fairdm-conf: Added Python 3.13
- 001-production-config-fairdm-conf: Added Python 3.13
- 001-documentation-baseline: Added Python 3.10+ (current dev environment Python 3.11) + Django, Sphinx (via `fairdm-docs`), MyST Markdown, `pydata-sphinx-theme`, `sphinx-design`, Bootstrap 5, Context7 for library docs


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
