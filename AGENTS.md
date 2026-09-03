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
- **Lint:** `poetry run pre-commit run --all-files` — this is the gate CI enforces.
  Raw `poetry run ruff check .` covers a wider file set and is not the gate.
- **Format:** `poetry run invoke format`
- **Type-check:** `poetry run pre-commit run --hook-stage manual mypy`. Staged manually
  rather than on every commit: the package currently reports 214 errors across 44 files,
  so making it blocking would hold every pull request red until a dedicated typing pass.
- **Build:** `poetry build`

Development tooling comes from the `mvp-shared[dev,test]` bundle pinned in `pyproject.toml`,
so `poetry run <tool>` and the pre-commit hooks always agree on versions.

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

Required status checks (exact names, as they report on a pull request):

- `call-build / Code Quality`
- `call-build / Security Scan`
- `call-build / Build Package`
- `call-tests / Test Python 3.13, Django 5.1`
- `call-tests / Test Python 3.13, Django 5.2`

CI calls the shared family workflows in `django-mvp/shared`, pinned to `v0.4.1`, from
`.github/workflows/build.yml` and `.github/workflows/tests.yml`. Releases run through
`prepare-release.yml` → `tag-release.yml` → `publish.yml`.

## Development workflow

Feature work follows a spec-driven process: spec → plan → tasks → implement → review → PR, with a
`specs/NNN-slug/` directory per feature. `specs/` holds the specs written so far and stays as the
record of what was built and why.

Project standards and the quality bar live in `CONSTITUTION.md`.
