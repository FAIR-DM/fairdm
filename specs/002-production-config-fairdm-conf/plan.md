# Implementation Plan: Production-Ready Configuration via fairdm.conf

**Branch**: `001-production-config-fairdm-conf` | **Date**: 2026-01-02 | **Spec**: [specs/001-production-config-fairdm-conf/spec.md](specs/001-production-config-fairdm-conf/spec.md)
**Input**: Feature specification from `specs/001-production-config-fairdm-conf/spec.md` 

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This plan implements a robust, opinionated configuration system for FairDM portals using `django-split-settings` and `django-environ`. The core goal is to provide a "production-first" baseline through modular settings that portals load via `fairdm.setup()`, ensuring consistency and security while allowing for safe, project-specific overrides.

Key architectural decisions include:
- **Modular Production Baseline**: `fairdm/conf/settings/*` contains 8-12 focused modules (database, cache, security, static/media, email, logging, apps/middleware, celery, auth) representing production-ready defaults.
- **Orchestrated Loading**: `fairdm.setup()` uses `django-split-settings` to load all settings modules, then applies environment-specific overrides based on `DJANGO_ENV`.
- **Environment Overrides**: `local.py` (development) and `staging.py` provide environment-specific adjustments on top of the production baseline.
- **Fail-Fast vs. Degrade**: Production/Staging fail immediately on missing backing services (Redis, DB) or misconfigured addons. Development degrades gracefully with warnings.
- **Explicit Setup**: Portals initialize configuration via a `fairdm.setup()` call in their `settings.py`, followed by project-specific overrides.
- **Aggregated Error Reporting**: Startup checks collect all configuration errors and report them in a single `ImproperlyConfigured` exception.

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: 
- `django` (^5.1.3)
- `django-environ` (^0.10.0)
- `django-split-settings` (^1.2.0)
- `django-redis` (^5.2.0)
- `celery` (^5.4.0)
- `whitenoise` (^6.4.0)
**Storage**: PostgreSQL (primary), Redis (cache/broker)
**Testing**: `pytest` (via `pytest-django`)
**Target Platform**: Containerized (Docker) Linux environments
**Project Type**: Django Framework (Library/Package)
**Performance Goals**: Zero runtime overhead after startup. Fast fail-fast checks (<1s).
**Constraints**: Must support 12-factor app principles (config in env vars). Must not break existing Django settings patterns.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1. **Explicit Configuration**: The `fairdm.setup()` function ensures configuration is explicit, not magical. Settings modules are loaded explicitly via `include()`.
2. **Environment Parity**: Environment overrides (local.py, staging.py) build on top of the production baseline to enforce parity.
3. **Fail-Fast**: The requirement to fail fast in production aligns with robust operations. Aggregated error reporting ensures all issues are visible.
4. **Separation of Concerns**: Framework production baseline lives in `fairdm/conf/settings/*`, environment overrides in `fairdm/conf/{local,staging}.py`, project config in `config/settings.py`.

## Project Structure

### Documentation (this feature)

```
specs/002-production-config-fairdm-conf/
 plan.md              # This file
 research.md          # Phase 0 output
 data-model.md        # Phase 1 output (N/A for this feature, but we'll use for config schema)
 quickstart.md        # Phase 1 output
 contracts/           # Phase 1 output (API contracts for setup() and addons)
 tasks.md             # Phase 2 output
``n
### Source Code (repository root)

```
fairdm/
  conf/
    __init__.py          # Exports setup()
    setup.py             # Main orchestration: loads settings/*, applies env overrides, loads addons
    environment.py       # env var handling and typing (django-environ setup)
    local.py             # Development environment overrides
    staging.py           # Staging environment overrides
    checks.py            # Validation logic (fail-fast/degrade, aggregated errors)
    settings/
      __init__.py        # Empty or minimal
      apps.py            # INSTALLED_APPS, MIDDLEWARE
      auth.py            # Authentication backends, password validators
      cache.py           # Cache configuration (Redis for production)
      celery.py          # Celery/background task configuration
      database.py        # Database configuration (PostgreSQL for production)
      email.py           # Email backend configuration
      logging.py         # Logging configuration
      security.py        # Security settings (HTTPS, cookies, HSTS, etc.)
      static_media.py    # Static/media file handling (WhiteNoise, S3, etc.)
      # Additional modules as needed (max ~8-12 total)
```

**Structure Decision**: The existing `fairdm/conf/settings/*` directory (currently ~25 files) will be consolidated into 8-12 focused modules. Each module targets a specific production concern. The `setup()` function orchestrates loading these modules via `django-split-settings.include()`, then applies environment-specific overrides from `local.py` or `staging.py` based on the `DJANGO_ENV` environment variable.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

N/A - No violations anticipated.
