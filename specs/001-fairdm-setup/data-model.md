# Configuration Schema & Data Model

## Architecture Overview

FairDM provides a production-ready configuration baseline through modular settings files in `fairdm/conf/settings/*`. The `fairdm.setup()` function orchestrates loading these settings modules and applying environment-specific overlays based on the `DJANGO_ENV` environment variable.

**Loading Flow**:
```
1. fairdm.setup() called from portal's settings.py
2. Load all settings/* modules (8-12 files) → Production Baseline
3. Detect DJANGO_ENV (defaults to "production")
4. Apply environment overlay:
   - DJANGO_ENV="local" → Apply local.py overrides
   - DJANGO_ENV="staging" → Apply staging.py overrides
   - DJANGO_ENV="production" → No overlay (use baseline as-is)
5. Load addon setup modules (if addons specified)
6. Validate configuration with aggregated error collection
7. Inject all settings into caller's globals
```

## Settings Modules Structure (Production Baseline)

The `fairdm/conf/settings/*` directory contains 8-12 focused modules that define production-ready defaults. These modules ARE the production configuration, not inherited or imported—they are loaded directly via `django-split-settings.include()`.

### Core Settings Modules

#### 1. `apps.py` - Application Configuration
*   **Responsibility**: Define Django apps and middleware stack.
*   **Key Settings**:
    *   `INSTALLED_APPS`: Core Django apps + FairDM apps (`fairdm.core`, `fairdm.registry`, etc.)
    *   `MIDDLEWARE`: Security, Session, Common, CSRF, Auth, Messages, Clickjacking
    *   `ROOT_URLCONF`: Portal's URL configuration
    *   `WSGI_APPLICATION`: WSGI application entry point

#### 2. `database.py` - Database Configuration
*   **Responsibility**: PostgreSQL configuration for production.
*   **Key Settings**:
    *   `DATABASES`: PostgreSQL connection from `DATABASE_URL` env var (required)
    *   `ATOMIC_REQUESTS`: `True` (transaction per request)
    *   `CONN_MAX_AGE`: Persistent connections (default: 60s)
*   **Behavior**: Fails fast if `DATABASE_URL` not set in production/staging.

#### 3. `cache.py` - Cache Configuration
*   **Responsibility**: Redis cache configuration for production.
*   **Key Settings**:
    *   `CACHES`: Redis backend from `REDIS_URL` env var (required)
    *   Named caches: `default`, `select2`, `vocabularies`
*   **Behavior**: Fails fast if `REDIS_URL` not set in production/staging.

#### 4. `security.py` - Security Settings
*   **Responsibility**: Production security hardening.
*   **Key Settings**:
    *   `DEBUG`: `False`
    *   `ALLOWED_HOSTS`: From `DJANGO_ALLOWED_HOSTS` env var (required)
    *   `SECURE_SSL_REDIRECT`: `True`
    *   `SECURE_HSTS_SECONDS`: `31536000` (1 year)
    *   `SESSION_COOKIE_SECURE`: `True`
    *   `CSRF_COOKIE_SECURE`: `True`
    *   `SECRET_KEY`: From `DJANGO_SECRET_KEY` env var (required)

#### 5. `static_media.py` - Static & Media Files
*   **Responsibility**: Static/media file serving (WhiteNoise, cloud storage).
*   **Key Settings**:
    *   `STATIC_ROOT`, `STATIC_URL`
    *   `MEDIA_ROOT`, `MEDIA_URL`
    *   `STORAGES`: WhiteNoise for static, local/S3/Azure/GCS for media
    *   `STATICFILES_FINDERS`: FileSystemFinder, AppDirectoriesFinder

#### 6. `celery.py` - Background Tasks
*   **Responsibility**: Celery configuration for async tasks.
*   **Key Settings**:
    *   `CELERY_BROKER_URL`: From `REDIS_URL` or `CELERY_BROKER_URL` env var
    *   `CELERY_RESULT_BACKEND`: Redis backend
    *   `CELERY_TASK_ALWAYS_EAGER`: `False` (use workers in production)

#### 7. `auth.py` - Authentication
*   **Responsibility**: Authentication backends and password validation.
*   **Key Settings**:
    *   `AUTHENTICATION_BACKENDS`: ModelBackend, ObjectPermissionBackend
    *   `AUTH_PASSWORD_VALIDATORS`: Length, common passwords, numeric, similarity checks

#### 8. `logging.py` - Logging Configuration
*   **Responsibility**: Production logging (Sentry, file handlers).
*   **Key Settings**:
    *   Sentry SDK integration (if `SENTRY_DSN` set)
    *   Log handlers for errors, warnings
    *   Format strings for structured logging

#### 9. `email.py` - Email Backend
*   **Responsibility**: Email configuration for production.
*   **Key Settings**:
    *   `EMAIL_BACKEND`: SMTP or service-specific backend
    *   SMTP credentials from env vars

### Additional Modules (as needed)
*   `templates.py`: Template engine configuration
*   `i18n.py`: Internationalization settings
*   `performance.py`: Performance optimizations

## Environment Override Files

Environment-specific configurations overlay the production baseline WITHOUT inheritance or imports. These are thin files that modify specific settings for local development or staging environments.

### `local.py` - Development Environment
*   **Purpose**: Override production settings for local development.
*   **Applied When**: `DJANGO_ENV=local` (or `development`)
*   **Key Overrides**:
    *   `DEBUG`: `True`
    *   `ALLOWED_HOSTS`: `['*']` or `['localhost', '127.0.0.1']`
    *   `DATABASES`: Fallback to SQLite if `DATABASE_URL` not set (with warning)
    *   `CACHES`: Fallback to `LocMemCache` if `REDIS_URL` not set (with warning)
    *   `EMAIL_BACKEND`: `django.core.mail.backends.console.EmailBackend`
    *   `SECURE_SSL_REDIRECT`: `False`
    *   `SESSION_COOKIE_SECURE`: `False`
    *   `CSRF_COOKIE_SECURE`: `False`
*   **Behavior**: Degrades gracefully with warnings when backing services unavailable.

### `staging.py` - Staging Environment
*   **Purpose**: Override production settings for staging/QA environments.
*   **Applied When**: `DJANGO_ENV=staging`
*   **Key Overrides**:
    *   Enhanced logging for debugging
    *   Optional: Relaxed rate limits for testing
    *   Optional: Test payment processors
*   **Behavior**: Fails fast like production (requires DB, cache, etc.).

## Addon Contract

Addons are Python packages that integrate with FairDM configuration via a discovery mechanism.

### Protocol

1.  **Discovery**: 
    *   Addon package must be installed in the environment
    *   Addon must be listed in `fairdm.setup(addons=['addon_name'])`

2.  **Entry Point**: 
    *   Addon must define `__fdm_setup_module__` in its top-level `__init__.py`
    *   Points to a setup module path (e.g., `'my_addon.conf'` or `'my_addon.setup'`)

3.  **Setup Module Structure**: 
    *   The module pointed to by `__fdm_setup_module__` is imported and executed during `fairdm.setup()`
    *   Setup module can modify globals directly or return a dictionary of settings
    *   Common pattern:
        ```python
        # my_addon/setup.py
        
        def setup(globals_dict):
            """Called by fairdm.setup() with caller's globals."""
            globals_dict['INSTALLED_APPS'].extend([
                'my_addon.app1',
                'my_addon.app2',
            ])
            globals_dict['MIDDLEWARE'].insert(3, 'my_addon.middleware.CustomMiddleware')
            globals_dict['MY_ADDON_SETTING'] = 'value'
        ```

4.  **Loading Behavior**:
    *   **Production/Staging**: If addon setup module fails to import or raises error, `fairdm.setup()` collects error and raises `ImproperlyConfigured` with all errors at end
    *   **Local/Development**: If addon setup module fails, log warning and skip addon (continue with other addons)

5.  **URL Integration** (optional):
    *   If addon provides `<addon>.urls` module, it can be auto-discovered
    *   Portal's URL configuration can include via `addon_urls` list provided by `fairdm.setup()`

### Example Addon Structure

```
my_fairdm_addon/
  __init__.py              # Defines __fdm_setup_module__ = 'my_fairdm_addon.setup'
  setup.py                 # Provides setup(globals) function
  apps.py
  models.py
  urls.py                  # Optional URL patterns
  ...
```

## Validation Logic & Error Aggregation

The `fairdm/conf/checks.py` module provides validation logic that respects the environment and collects all errors before raising.

### Validation Flow

1.  **Triggered by**: `fairdm.setup()` after loading settings and addons
2.  **Collects**: All configuration errors into a list
3.  **Reports**: Single `ImproperlyConfigured` exception with formatted message containing all errors

### Fail-Fast Checks (Production/Staging)

When `DJANGO_ENV` is `production` or `staging`, the following are REQUIRED and raise errors if missing:

*   **Database Configuration**:
    *   Check: `DATABASE_URL` environment variable set?
    *   Fail: Raise error "DATABASE_URL is required in production/staging"
    
*   **Cache Configuration**:
    *   Check: `REDIS_URL` environment variable set?
    *   Fail: Raise error "REDIS_URL is required in production/staging"
    
*   **Secret Key**:
    *   Check: `DJANGO_SECRET_KEY` environment variable set?
    *   Fail: Raise error "DJANGO_SECRET_KEY is required"
    
*   **Allowed Hosts**:
    *   Check: `DJANGO_ALLOWED_HOSTS` environment variable set?
    *   Fail: Raise error "DJANGO_ALLOWED_HOSTS is required in production/staging"

*   **Addon Setup Modules**:
    *   Check: All specified addons have valid `__fdm_setup_module__`?
    *   Check: All addon setup modules import successfully?
    *   Fail: Raise error "Addon 'addon_name' failed to load: [error details]"

### Graceful Degradation (Local/Development)

When `DJANGO_ENV` is `local` or `development`, missing backing services degrade gracefully:

*   **Database Missing**:
    *   Check: `DATABASE_URL` environment variable set?
    *   Degrade: Log warning "DATABASE_URL not set, using SQLite fallback"
    *   Action: Set `DATABASES['default']` to SQLite backend
    
*   **Cache Missing**:
    *   Check: `REDIS_URL` environment variable set?
    *   Degrade: Log warning "REDIS_URL not set, using LocMemCache fallback"
    *   Action: Set `CACHES['default']` to `LocMemCache` backend
    
*   **Addon Failures**:
    *   Check: Addon setup module importable and executable?
    *   Degrade: Log warning "Addon 'addon_name' failed to load, skipping: [error details]"
    *   Action: Skip addon, continue with remaining configuration

### Error Message Format

When multiple errors are collected, they are formatted as:

```
Configuration errors detected:
  1. DATABASE_URL is required in production/staging
  2. REDIS_URL is required in production/staging
  3. Addon 'my_addon' failed to load: ModuleNotFoundError: No module named 'my_addon.setup'

Fix these configuration issues and try again.
```

This aggregated approach ensures developers see ALL configuration problems at once, not one at a time.

## Environment Variables Schema

See `contracts/env-vars.md` for the complete reference of supported environment variables.

### Required for All Environments
*   `DJANGO_SECRET_KEY`: Django secret key (must be unique per portal)

### Required for Production/Staging
*   `DATABASE_URL`: PostgreSQL connection string
*   `REDIS_URL`: Redis connection string  
*   `DJANGO_ALLOWED_HOSTS`: Comma-separated list of allowed hostnames

### Optional (with fallbacks)
*   `DJANGO_ENV`: Environment name (`production`, `staging`, `local`/`development`) - defaults to `production`
*   `SENTRY_DSN`: Sentry error tracking DSN
*   `DJANGO_DEBUG`: Override DEBUG setting (use with caution)
*   `EMAIL_*`: Email backend configuration
*   `AWS_*`: S3 storage configuration

## Settings Override Pattern for Portals

Portals call `fairdm.setup()` in their `config/settings.py` and can apply overrides after:

```python
# config/settings.py
import fairdm

# Load FairDM baseline + environment overlay
fairdm.setup(
    apps=['my_portal_app'],
    addons=['fairdm_addon_discussions'],
)

# Portal-specific overrides
SITE_NAME = "My Research Portal"
SITE_DESCRIPTION = "Domain-specific data portal"

# Advanced: Override specific settings if needed
INSTALLED_APPS += ['my_custom_app']
MIDDLEWARE.insert(0, 'my_portal.middleware.CustomMiddleware')
```

**Note**: Overrides should be minimal. Most configuration should be via environment variables, not code changes.
