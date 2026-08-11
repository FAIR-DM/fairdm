# AGENTS.md — Agent Configuration for FairDM

<!-- Thin index only. Details live in the pointed-to files. -->

FairDM is a Django framework for building FAIR research data portals. Research teams declare
domain-specific sample and measurement models, register them, and get a working portal without
writing views, URL routing, or frontend code. The package ships the core backbone (projects,
datasets, samples, measurements, contributors) plus a demo application in `fairdm_demo`.

## Stack & commands

- **Stack:** Python 3.13, Django 5.1+, Poetry-managed, PostgreSQL in production
- **Install:** `poetry install --with dev,test,docs`
- **Test:** `poetry run pytest` (or `poetry run invoke test` for coverage)
- **Lint:** `poetry run ruff check .`
- **Format:** `poetry run invoke format`
- **All checks:** `poetry run invoke pre-push`
- **Type-check:** none — mypy is configured but disabled in CI and pre-commit
- **Build:** `poetry build`

The `docker-compose.yml` local development environment is not currently working and is not part
of any verification path.

## Agent skills

### Issue tracker

GitHub Issues via the `gh` CLI. External PRs are not a triage surface. See `docs/agents/issue-tracker.md`.

### Triage labels

Six canonical triage labels plus the feature-lifecycle set. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout — `CONTEXT.md` at the root, `docs/adr/` for architectural decisions. See `docs/agents/domain.md`.

### CI checks

Required status checks the pipeline reads (exact names):
`Lint & Format`, `Type Check`, `Test (Python 3.13, Django 5.1)`, `CI Success`.

CI is repo-native and defined in `.github/workflows/ci.yml`.

## Development workflow

Feature work follows a spec-driven process: spec → plan → tasks → implement → review → PR, with a
`specs/NNN-slug/` directory per feature. The toolchain is vendored in `.specify/`.

Project standards and the quality bar live in `memory/constitution.md`.
