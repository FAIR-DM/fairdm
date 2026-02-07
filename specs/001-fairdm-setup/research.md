# Research: Django Check Framework Integration

**Date**: 2026-01-20
**Purpose**: Research Django's system check framework patterns for migrating FairDM configuration validation.

## Django Check Framework Overview

Django's system check framework allows applications to register validation checks that run when:

- `python manage.py check` is explicitly called
- `python manage.py check --deploy` is called for production-critical checks
- Other management commands run (can be disabled per-command)

### Key Benefits for FairDM

1. **No runtime noise**: Checks don't run during normal development (`runserver`, `migrate`, etc.)
2. **Explicit validation**: Portal maintainers run checks when they want to validate configuration
3. **Standard Django pattern**: Uses Django's built-in infrastructure, not custom logic
4. **Severity levels**: ERROR, WARNING, INFO for appropriate feedback
5. **Tagging system**: Built-in tags (security, database, caching) + custom tags
6. **Deploy mode**: Production-critical checks only run with `--deploy` flag

## Check Function Structure

### Basic Pattern

```python
from django.core.checks import Error, Warning, Info, register, Tags

@register(Tags.security, deploy=True)
def check_secret_key(app_configs, **kwargs):
    """Validate SECRET_KEY configuration."""
    from django.conf import settings

    errors = []

    secret_key = getattr(settings, 'SECRET_KEY', '')

    if not secret_key:
        errors.append(
            Error(
                'SECRET_KEY is not set.',
                hint='Set DJANGO_SECRET_KEY environment variable.',
                id='fairdm.E001',
            )
        )
    elif len(secret_key) < 50:
        errors.append(
            Warning(
                f'SECRET_KEY is too short ({len(secret_key)} characters).',
                hint='Recommended: 50+ characters for production.',
                id='fairdm.W001',
            )
        )

    return errors
```

### Key Components

1. **Decorator**: `@register(tags, deploy=True/False)`
   - `tags`: Django's built-in tags or custom tags
   - `deploy=True`: Only runs with `--deploy` flag
   - Can use multiple tags: `@register(Tags.security, Tags.database)`

2. **Function Signature**: `def check_name(app_configs, **kwargs)`
   - `app_configs`: List of app configs being checked (can be None)
   - `**kwargs`: Additional arguments (future extensibility)
   - Must return list of CheckMessage instances

3. **Check Messages**:
   - `Error`: Critical issues that prevent proper operation
   - `Warning`: Issues that should be addressed but aren't critical
   - `Info`: Informational messages
   - `Debug`: Debug-level information (rarely used)

4. **Message Attributes**:
   - `msg`: The error message (required)
   - `hint`: Suggested resolution (optional but recommended)
   - `obj`: Object related to the error (optional)
   - `id`: Unique identifier like `'fairdm.E001'` (required)

## Built-in Tags

Django provides several built-in tags in `django.core.checks.Tags`:

- `Tags.admin`: Admin-related checks
- `Tags.caches`: Cache configuration checks
- `Tags.compatibility`: Compatibility checks
- `Tags.database`: Database configuration checks
- `Tags.models`: Model definition checks
- `Tags.security`: Security-related checks
- `Tags.signals`: Signal-related checks
- `Tags.templates`: Template configuration checks
- `Tags.urls`: URL configuration checks

## Custom Tags

For FairDM, we'll use a custom `deploy` tag for production-critical checks:

```python
# In fairdm/conf/checks.py
class DeployTags:
    deploy = 'deploy'
```

Usage:

```python
@register(Tags.security, DeployTags.deploy)
def check_something(app_configs, **kwargs):
    # ...
```

## Registration in AppConfig

Checks should be registered in the app's `ready()` method:

```python
# In fairdm/conf/apps.py
from django.apps import AppConfig

class FairdmConfConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "fairdm.conf"
    verbose_name = "FairDM Configuration"

    def ready(self):
        # Import checks module to register checks
        from . import checks  # noqa: F401
```

The import causes the `@register` decorators to execute, registering the checks.

## Mapping Current Validations to Checks

### Current validate_services() Logic

The existing `validate_services()` function performs these validations:

1. **Database validation**
   - Check if DATABASE['default'] is configured
   - Warn if using SQLite in production-like environments

2. **Cache validation**
   - Check if cache backend is locmem or dummy
   - Warn about unsuitable cache backends

3. **SECRET_KEY validation**
   - Check if SECRET_KEY is set
   - Check if SECRET_KEY contains 'insecure'
   - Check SECRET_KEY length

4. **ALLOWED_HOSTS validation**
   - Check if ALLOWED_HOSTS is empty in production
   - Check if ALLOWED_HOSTS contains wildcard

5. **DEBUG mode validation**
   - Check if DEBUG is True in production

6. **HTTPS/SSL validation**
   - Check SECURE_SSL_REDIRECT
   - Check SESSION_COOKIE_SECURE
   - Check CSRF_COOKIE_SECURE

7. **Celery broker validation**
   - Check if CELERY_BROKER_URL is set
   - Check if CELERY_TASK_ALWAYS_EAGER is True

### Proposed Check Functions

| Current Validation | New Check Function | Severity | Tags | Deploy? |
|-------------------|-------------------|----------|------|---------|
| Database configured | `check_database_configured` | ERROR | database | ✅ |
| SQLite in production | `check_database_production_ready` | ERROR | database | ✅ |
| Cache backend configured | `check_cache_backend` | ERROR | caches | ✅ |
| SECRET_KEY set | `check_secret_key_exists` | ERROR | security | ✅ |
| SECRET_KEY 'insecure' | `check_secret_key_production` | ERROR | security | ✅ |
| SECRET_KEY length | `check_secret_key_strength` | WARNING | security | ✅ |
| ALLOWED_HOSTS empty | `check_allowed_hosts_configured` | ERROR | security | ✅ |
| ALLOWED_HOSTS wildcard | `check_allowed_hosts_secure` | ERROR | security | ✅ |
| DEBUG True | `check_debug_false` | ERROR | security | ✅ |
| SSL redirect | `check_ssl_redirect` | WARNING | security | ✅ |
| Cookie secure flags | `check_cookie_security` | ERROR | security | ✅ |
| Celery broker URL | `check_celery_broker` | ERROR | custom:celery | ✅ |
| Celery always eager | `check_celery_async` | ERROR | custom:celery | ✅ |

### Severity Level Decisions

**ERROR** (production-critical):

- Database not configured or SQLite
- Cache backend unsuitable (locmem/dummy)
- SECRET_KEY missing or insecure
- ALLOWED_HOSTS empty or wildcard
- DEBUG=True
- Cookie security flags disabled
- Celery broker missing or synchronous mode

**WARNING** (recommendations):

- SECRET_KEY too short
- SSL redirect not enabled (suggestion, not requirement)

**INFO** (informational):

- None currently (could add best-practice hints)

## Testing Strategy

### Unit Tests for Check Functions

```python
# tests/integration/conf/test_checks.py
import pytest
from django.core.checks import Error, Warning
from django.test import override_settings

from fairdm.conf.checks import check_secret_key


class TestSecretKeyCheck:
    @override_settings(SECRET_KEY='')
    def test_missing_secret_key_returns_error(self):
        """Check returns ERROR when SECRET_KEY is not set."""
        errors = check_secret_key(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert errors[0].id == 'fairdm.E001'
        assert 'SECRET_KEY is not set' in errors[0].msg

    @override_settings(SECRET_KEY='short')
    def test_short_secret_key_returns_warning(self):
        """Check returns WARNING when SECRET_KEY is too short."""
        errors = check_secret_key(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Warning)
        assert errors[0].id == 'fairdm.W001'

    @override_settings(SECRET_KEY='a' * 50)
    def test_valid_secret_key_returns_empty(self):
        """Check returns empty list when SECRET_KEY is valid."""
        errors = check_secret_key(app_configs=None)

        assert errors == []
```

### Integration Tests

```python
from django.core.management import call_command
from django.core.management.base import SystemCheckError
from django.test import override_settings
import pytest


class TestCheckCommandIntegration:
    @override_settings(SECRET_KEY='')
    def test_check_deploy_fails_with_missing_secret_key(self):
        """Running check --deploy fails when SECRET_KEY is missing."""
        with pytest.raises(SystemCheckError) as exc_info:
            call_command('check', deploy=True)

        assert 'fairdm.E001' in str(exc_info.value)

    @override_settings(SECRET_KEY='a' * 50)
    def test_check_deploy_passes_with_valid_config(self, settings):
        """Running check --deploy succeeds with valid configuration."""
        # Set up valid production configuration
        settings.DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': 'test_db'
            }
        }
        settings.CACHES = {
            'default': {
                'BACKEND': 'django_redis.cache.RedisCache',
                'LOCATION': 'redis://localhost:6379/1'
            }
        }
        settings.ALLOWED_HOSTS = ['example.com']
        settings.DEBUG = False

        # Should not raise
        call_command('check', deploy=True)
```

### Test Coverage Requirements

1. **Each check function** must have:
   - Test for the error/warning condition
   - Test for the passing condition
   - Test for edge cases (if applicable)

2. **Integration tests** must verify:
   - Checks are registered and callable
   - `--deploy` flag correctly filters checks
   - Multiple errors are reported together
   - Error IDs are unique and consistent

3. **Coverage targets**:
   - 100% coverage of check logic (critical path)
   - All error messages have associated tests
   - All hints have associated tests

## Backwards Compatibility Analysis

### Current Callers of validate_services()

```bash
# Search results show:
fairdm/conf/setup.py:156:    validate_services(env_profile, caller_globals)
```

Only one caller: `fairdm/conf/setup.py` in the `setup()` function.

### Current Callers of validate_addon_module()

```bash
# Search results show:
fairdm/conf/addons.py:75:    if not validate_addon_module(addon_name, setup_module_path, env_profile):
```

Only one caller: `fairdm/conf/addons.py` in the `load_addon()` function.

### Migration Impact

**Breaking changes**: None for external users

- `validate_services()` and `validate_addon_module()` are internal functions
- Not documented as public API
- Only called from within fairdm.conf package

**Internal changes needed**:

1. Remove `validate_services()` call from `fairdm/conf/setup.py`
2. Remove `validate_addon_module()` call from `fairdm/conf/addons.py`
3. Convert addon validation to check function
4. Update tests that may be calling these functions directly

### Test Impact

Need to search for test usages:

```python
# Likely test files to update:
# - tests/integration/conf/test_setup.py
# - tests/integration/conf/test_addons.py
# - Any tests that mock or call validate_services()
```

## Implementation Checklist

### Phase 1: Create Check Functions

- [ ] Create custom `DeployTags` class
- [ ] Implement database check functions
- [ ] Implement cache check functions
- [ ] Implement security check functions (SECRET_KEY, ALLOWED_HOSTS, DEBUG)
- [ ] Implement HTTPS/SSL check functions
- [ ] Implement Celery check functions
- [ ] Implement addon validation check function

### Phase 2: Register Checks

- [ ] Update `FairdmConfConfig.ready()` to import checks module
- [ ] Verify checks are registered with correct tags
- [ ] Test `python manage.py check` shows non-deploy checks
- [ ] Test `python manage.py check --deploy` shows all checks

### Phase 3: Remove Old Code

- [ ] Remove `validate_services()` function from checks.py
- [ ] Remove `validate_services()` call from setup.py
- [ ] Remove `validate_addon_module()` function from checks.py
- [ ] Remove `validate_addon_module()` call from addons.py
- [ ] Update any imports

### Phase 4: Update Tests

- [ ] Write unit tests for each check function
- [ ] Write integration tests for check command
- [ ] Update existing tests that called old functions
- [ ] Verify test coverage maintained or improved

### Phase 5: Documentation

- [ ] Create portal-administration/configuration-checks.md
- [ ] Document how to run checks
- [ ] Document what each check validates
- [ ] Document how to resolve common issues
- [ ] Add to deployment checklist

## Decision: Check Registration Pattern

**Decision**: Use `@register` decorator at function definition + import in `AppConfig.ready()`

**Rationale**:

- Standard Django pattern
- Keeps check definitions close to their implementation
- Avoids manual registration boilerplate
- Easy to understand and maintain

**Alternative considered and rejected**: Manual registration in `ready()` method

- More verbose
- Separation between definition and registration
- Harder to maintain

## Decision: Environment Awareness

**Decision**: Checks are NOT environment-aware; they validate production readiness

**Rationale**:

- Checks assess "is this configuration production-ready?" not "does this match my environment?"
- Using `--deploy` flag makes intent explicit
- Simpler check logic (no environment branching)
- Consistent validation rules regardless of where portal runs

**What this means**:

- Running `python manage.py check` in development with SQLite: no warnings
- Running `python manage.py check --deploy` in development with SQLite: ERROR
- Developer must explicitly opt into production validation

## Error ID Naming Convention

**Pattern**: `fairdm.<severity><number>`

Where:

- `severity`: E (Error), W (Warning), I (Info)
- `number`: Sequential within severity (001, 002, 003, ...)

**Examples**:

- `fairdm.E001`: SECRET_KEY not set
- `fairdm.E002`: Database not configured
- `fairdm.W001`: SECRET_KEY too short
- `fairdm.W002`: SSL redirect not enabled

**Reservation**:

- E001-E099: Reserved for security checks
- E100-E199: Reserved for database checks
- E200-E299: Reserved for cache checks
- E300-E399: Reserved for Celery checks
- W001-W099: Reserved for security warnings
- W100-W199: Reserved for optimization hints

## Next Steps

1. Implement check functions in `fairdm/conf/checks.py`
2. Update `fairdm/conf/apps.py` to register checks
3. Remove old validation code
4. Write tests
5. Update documentation
