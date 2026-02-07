# Implementation Plan: Configuration Checks Refactoring

**Branch**: `001-fairdm-setup` | **Date**: 2026-01-20 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-fairdm-setup/spec.md`

**Note**: This plan focuses on refactoring the configuration validation system to use Django's check framework instead of runtime logging.

## Summary

**Primary Requirement**: Migrate configuration validation from runtime logging (which creates noise during normal development) to Django's check framework, allowing explicit validation via `python manage.py check --deploy`.

**Technical Approach**:

- Replace `validate_services()` function with individual Django system check functions
- Use Django's built-in tags (security, database, caching) plus custom `deploy` tag
- Checks assess production readiness regardless of environment (not environment-aware)
- Register checks in `FairdmConfConfig.ready()` method
- Production-critical checks use ERROR severity with `deploy` tag
- Development hints use WARNING/INFO severity without `deploy` tag

## Technical Context

**Language/Version**: Python 3.13 (current), 3.11+ supported
**Primary Dependencies**: Django 5.1, django-environ (for environment variable parsing)
**Storage**: PostgreSQL (production), SQLite (development)
**Testing**: pytest, pytest-django
**Target Platform**: Linux server (production), Windows/macOS/Linux (development)
**Project Type**: Django web application
**Performance Goals**: Check execution < 1 second for typical configurations
**Constraints**: Must not slow down normal development workflow (runserver, migrations)
**Scale/Scope**: ~10 individual check functions covering database, cache, secrets, security, celery

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ **Principle I: FAIR-First Research Portals**

- **Status**: Not applicable - infrastructure change
- **Rationale**: Configuration checks improve deployment reliability but don't directly affect FAIR compliance

### ✅ **Principle II: Domain-Driven, Declarative Modeling**

- **Status**: Compliant
- **Rationale**: No data model changes; this is pure infrastructure refactoring

### ✅ **Principle III: Configuration Over Custom Plumbing**

- **Status**: Compliant
- **Rationale**: Uses Django's built-in check framework (standard Django pattern) instead of custom validation logic

### ✅ **Principle IV: Opinionated, Production-Grade Defaults**

- **Status**: Compliant
- **Rationale**: Aligns with Django best practices for production deployment validation

### ✅ **Principle V: Test-First Quality & Sustainability (NON-NEGOTIABLE)**

- **Status**: Requires tests
- **Action**: Must write tests that verify:
  - Check functions are registered
  - Checks return appropriate severity and messages
  - `--deploy` flag correctly filters checks
  - All existing validation coverage is maintained

### ✅ **Principle VI: Documentation Critical**

- **Status**: Requires documentation update
- **Action**: Update portal-administration documentation to explain:
  - How to run configuration checks
  - When to use `--deploy` flag
  - What each check validates
  - How to resolve common issues

### ✅ **Principle VII: Living Demo & Reference Implementation**

- **Status**: Not applicable - no demo app changes needed
- **Rationale**: Demo app uses fairdm.setup() which will continue to work; checks are framework-level

## Project Structure

### Documentation (this feature)

```text
specs/001-fairdm-setup/
├── plan.md              # This file
├── spec.md              # Feature specification (already exists)
├── research.md          # Django check framework patterns (to be created)
└── tasks.md             # Task breakdown (created by /speckit.tasks)
```

### Source Code (repository root)

```text
fairdm/
├── conf/
│   ├── apps.py          # Register checks in FairdmConfConfig.ready()
│   ├── checks.py        # Convert from validate_services() to check functions
│   ├── setup.py         # Remove validate_services() call
│   └── addons.py        # Convert validate_addon_module to check function
└── ...

tests/
├── integration/
│   └── conf/
│       └── test_checks.py  # Test check registration and behavior
└── ...

docs/
└── portal-administration/
    └── configuration-checks.md  # New: How to validate configuration
```

**Structure Decision**: This is a refactoring within the existing `fairdm.conf` package. No new modules or packages needed. Changes are localized to:

1. `fairdm/conf/checks.py` - convert validation logic to check functions
2. `fairdm/conf/apps.py` - register checks in ready() method
3. `fairdm/conf/setup.py` - remove validate_services() call
4. Tests and documentation

## Complexity Tracking

> **No violations** - this refactoring aligns with Django best practices and constitution principles.

---

## Phase 0: Research & Pattern Discovery

### Research Questions

1. **Django Check Framework Best Practices**
   - How to structure check functions (signature, return values)
   - How to use built-in vs custom tags
   - How to make checks work with `--deploy` flag
   - Error message formatting conventions
   - Registration patterns in AppConfig.ready()

2. **Migration Strategy**
   - How to ensure all existing validation coverage is preserved
   - How to map current validation logic to appropriate severity levels
   - Testing strategy for check functions

3. **Backwards Compatibility**
   - Does removing validate_services() break any tests or external code?
   - Are there other callers of validate_services() besides setup.py?

### Research Deliverable

`research.md` containing:

- Django check framework patterns and examples
- Mapping of current validations to check functions
- Decision on severity levels for each check
- Testing approach for check functions

---

## Phase 1: Design & Contracts

### Design Deliverables

**No data-model.md needed** - this is pure infrastructure refactoring with no data model changes.

**No contracts/ needed** - no API changes, internal implementation only.

**quickstart.md** - Brief guide for:

- Running `python manage.py check --deploy` before deployment
- Interpreting check messages
- Common configuration fixes

### Implementation Design

#### Check Functions Structure

```python
# fairdm/conf/checks.py

from django.core.checks import Error, Warning, Info, Tags, register

# Custom tag for deploy checks
class DeployTags:
    deploy = 'deploy'

@register(Tags.database, DeployTags.deploy)
def check_database_config(app_configs, **kwargs):
    """Validate database configuration for production readiness."""
    errors = []
    # Check logic here
    return errors

@register(Tags.security, DeployTags.deploy)
def check_secret_key(app_configs, **kwargs):
    """Validate SECRET_KEY configuration."""
    errors = []
    # Check logic here
    return errors

# ... more check functions
```

#### Check Categories

1. **Database Checks** (Tags.database, deploy)
   - Database configured (not empty)
   - Not using SQLite in production contexts

2. **Cache Checks** (Tags.caching, deploy)
   - Cache backend configured
   - Not using locmem/dummy cache

3. **Security Checks** (Tags.security, deploy)
   - SECRET_KEY present and strong
   - ALLOWED_HOSTS configured (not empty, not wildcard)
   - DEBUG is False (for production readiness)
   - HTTPS settings (SECURE_SSL_REDIRECT, SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE)

4. **Celery Checks** (custom 'celery' tag, deploy)
   - CELERY_BROKER_URL configured
   - CELERY_TASK_ALWAYS_EAGER is False (for production readiness)

5. **Development Hints** (no deploy tag, WARNING/INFO level)
   - Suggestions for SSL redirect
   - Other optional improvements

---

## Post-Phase 1: Agent Context Update

After Phase 1 design is complete, run:

```powershell
.\.specify\scripts\powershell\update-agent-context.ps1 -AgentType copilot
```

This will update `.github/instructions/copilot.instructions.md` with any new patterns or technologies introduced by this feature (Django check framework patterns, check registration, etc.).

---

## Next Steps

1. **Phase 0 (Research)**: Agent will research Django check framework patterns and create `research.md`
2. **Phase 1 (Design)**: Agent will create `quickstart.md` with usage guide
3. **Update Agent Context**: Run update script to capture patterns
4. **Phase 2 (Tasks)**: Run `/speckit.tasks` to generate task breakdown
5. **Implementation**: Execute tasks, following test-first discipline

---

## Success Criteria

- ✅ No warnings/errors during normal `python manage.py runserver`
- ✅ Running `python manage.py check --deploy` shows all production readiness issues
- ✅ All existing validation logic is preserved
- ✅ Test coverage maintained or improved
- ✅ Documentation explains how to use configuration checks
- ✅ `validate_services()` function removed from codebase
- ✅ Checks registered in `FairdmConfConfig.ready()`
