# Configuration Guide

FairDM provides a flexible, environment-aware configuration system built on top of Django's settings. This guide explains how to configure your portal for different deployment scenarios.

## Overview

The configuration system is designed around these principles:

- **Production by default**: Settings start from a secure production baseline
- **Environment-specific overrides**: Development and staging can override production settings
- **Project customization**: Portals can safely override framework settings
- **Addon integration**: Third-party addons inject their settings cleanly

## Quick Start

In your portal's main `settings.py`:

```python
import fairdm

fairdm.setup()
```

That's it! FairDM will load the appropriate configuration based on your environment.

## Environment Profiles

FairDM supports three environment profiles, selected via the `DJANGO_ENV` environment variable:

### Production (default)

```bash
export DJANGO_ENV=production
```

**Characteristics**:
- Strict validation (fail-fast)
- Requires PostgreSQL database
- Requires Redis cache
- Enforces HTTPS security
- Requires strong SECRET_KEY
- DEBUG disabled

**Use for**: Production deployments, public-facing portals

### Staging

```bash
export DJANGO_ENV=staging
```

**Characteristics**:
- Production-like validation
- Enhanced DEBUG-level logging
- Optional Sentry error tracking
- Same security requirements as production

**Use for**: Pre-production testing, QA environments

### Development

```bash
export DJANGO_ENV=development
```

**Characteristics**:
- Graceful degradation (warns instead of failing)
- SQLite fallback if no DATABASE_URL
- LocMemCache fallback if no Redis
- Eager Celery (no broker needed)
- Console email backend
- DEBUG enabled
- Relaxed security settings

**Use for**: Local development, testing

## Configuration Structure

FairDM's configuration is organized into focused modules:

```
fairdm/conf/
├── __init__.py              # Package exports
├── setup.py                 # Main setup() function
├── environment.py           # Environment variable handling
├── checks.py                # Configuration validation
├── addons.py                # Addon discovery and loading
├── development.py           # Development overrides
├── staging.py               # Staging overrides
└── settings/                # Production baseline (10 modules)
    ├── apps.py              # INSTALLED_APPS, MIDDLEWARE, TEMPLATES
    ├── auth.py              # Authentication backends
    ├── cache.py             # Redis/LocMemCache/DummyCache
    ├── celery.py            # Background task processing
    ├── database.py          # PostgreSQL/SQLite configuration
    ├── email.py             # Email backend
    ├── logging.py           # Logging and Sentry
    ├── security.py          # SECRET_KEY, ALLOWED_HOSTS, HTTPS
    ├── static_media.py      # Static/media with WhiteNoise, S3
    └── addons.py            # Third-party library configurations
```

## Loading Order

When you call `fairdm.setup()`, settings are loaded in this order:

1. **Environment detection**: Reads `DJANGO_ENV` (defaults to `production`)
2. **Environment variables**: Loads `.env` files if present
3. **Production baseline**: Loads all modules from `settings/` directory
4. **Environment overrides**: Loads `development.py` or `staging.py` if applicable
5. **Addon configurations**: Loads addon setup modules
6. **Project overrides**: Applies `**overrides` passed to `setup()`
7. **Validation**: Runs configuration checks

Later settings override earlier ones.

## Environment Variables

### Required (Production/Staging)

```bash
# Security
DJANGO_SECRET_KEY="your-secret-key-minimum-50-characters-long"
DJANGO_ALLOWED_HOSTS="example.com,www.example.com"

# Site identification
DJANGO_SITE_DOMAIN="example.com"
DJANGO_SITE_NAME="My Research Portal"

# Database
DATABASE_URL="postgresql://user:password@localhost:5432/dbname"

# Cache
REDIS_URL="redis://localhost:6379/0"

# Email (if sending emails)
EMAIL_HOST="smtp.example.com"
EMAIL_PORT="587"
EMAIL_HOST_USER="noreply@example.com"
EMAIL_HOST_PASSWORD="your-email-password"
```

### Optional

```bash
# Static files (S3/CloudFront)
AWS_ACCESS_KEY_ID="your-access-key"
AWS_SECRET_ACCESS_KEY="your-secret-key"
AWS_STORAGE_BUCKET_NAME="your-bucket"
AWS_S3_CUSTOM_DOMAIN="cdn.example.com"

# Error tracking
SENTRY_DSN="your-sentry-dsn"

# Media storage (if using S3)
AWS_MEDIA_BUCKET_NAME="your-media-bucket"
```

### Environment File Loading

FairDM loads environment files in this order (later files override earlier ones):

1. `stack.env` (base configuration)
2. `stack.{profile}.env` (e.g., `stack.production.env`, `stack.development.env`)
3. Custom file specified via `env_file` parameter

Example:

```python
fairdm.setup(env_file="/path/to/custom.env")
```

## Project Customization

### Using **overrides

Pass settings as keyword arguments to `setup()`:

```python
import fairdm

fairdm.setup(
    TIME_ZONE="Europe/London",
    LANGUAGE_CODE="en-gb",
    CUSTOM_SETTING="value",
)
```

### Post-setup Assignments

Modify settings after calling `setup()`:

```python
import fairdm

fairdm.setup()

# Add portal-specific apps
INSTALLED_APPS = INSTALLED_APPS + [
    "my_portal_app",
    "my_other_app",
]

# Customize logging
LOGGING["loggers"]["my_app"] = {
    "handlers": ["console", "file"],
    "level": "INFO",
}

# Override specific settings
TIME_ZONE = "America/New_York"
```

### Which Method to Use?

- **`**overrides`**: For simple scalar values (strings, booleans, numbers)
- **Post-setup assignments**: For complex modifications (extending lists, updating dicts)

## Addon Integration

Addons are FairDM extensions that provide additional functionality. They inject settings, apps, and middleware automatically.

### Using Addons

```python
import fairdm

fairdm.setup(
    addons=[
        "fairdm_discussions",    # Community discussions
        "fairdm_publications",   # Research publications
    ]
)
```

### Creating an Addon

To make your package a FairDM addon:

1. Create a setup module (e.g., `my_addon/fdm_setup.py`):

```python
# my_addon/fdm_setup.py

# Add your app to INSTALLED_APPS
INSTALLED_APPS = INSTALLED_APPS + ["my_addon"]  # noqa: F821

# Add middleware
MIDDLEWARE = MIDDLEWARE + ["my_addon.middleware.MyMiddleware"]  # noqa: F821

# Add custom settings
MY_ADDON_SETTING = "value"
```

2. Register the setup module in your package's `__init__.py`:

```python
# my_addon/__init__.py

__fdm_setup_module__ = "my_addon.fdm_setup"
```

3. Install and enable in portal:

```python
fairdm.setup(addons=["my_addon"])
```

### Addon Validation

- **Production/Staging**: Addons must load successfully (fail-fast)
- **Development**: Failed addons log warnings but don't stop startup

## Configuration Validation

FairDM validates your configuration on startup. Validation behavior depends on environment:

### Production/Staging (Fail-Fast)

Startup fails if:
- `SECRET_KEY` missing or too short (< 50 characters)
- `ALLOWED_HOSTS` empty or contains wildcards
- `DEBUG = True` (security risk)
- Database not configured or unreachable
- Cache backend is not production-grade (not Redis/Memcached)
- HTTPS security settings disabled
- Required addons fail to load

### Development (Graceful Degradation)

Logs warnings but continues if:
- `SECRET_KEY` is short (>= 8 characters acceptable)
- `DATABASE_URL` not set → falls back to SQLite
- `REDIS_URL` not set → falls back to LocMemCache
- Celery broker not configured → uses eager mode (synchronous)
- Email backend not configured → uses console backend
- Addons fail to load → skips and continues

## Troubleshooting

### Common Issues

#### "SECRET_KEY is required"

**Solution**: Set `DJANGO_SECRET_KEY` in your environment:

```bash
export DJANGO_SECRET_KEY="$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')"
```

#### "Database not configured"

**Solution**: Set `DATABASE_URL`:

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/dbname"
```

Or for development, rely on SQLite fallback:

```bash
export DJANGO_ENV=development  # Uses SQLite automatically
```

#### "Cache backend not suitable for production"

**Solution**: Set `REDIS_URL`:

```bash
export REDIS_URL="redis://localhost:6379/0"
```

#### "ALLOWED_HOSTS cannot be empty"

**Solution**: Set `DJANGO_ALLOWED_HOSTS`:

```bash
export DJANGO_ALLOWED_HOSTS="example.com,www.example.com"
```

For development:

```bash
export DJANGO_ENV=development  # Allows "*" automatically
```

### Debugging Configuration

#### View Loaded Settings

```python
# In Django shell or management command
from django.conf import settings

print(settings.DATABASES)
print(settings.INSTALLED_APPS)
```

#### Enable Debug Logging

```bash
export DJANGO_LOG_LEVEL=DEBUG
```

#### Check Environment Profile

```python
import os
print(os.environ.get("DJANGO_ENV", "production"))
```

## Best Practices

### Security

1. **Never commit secrets**: Use environment variables or `.env` files (gitignored)
2. **Use strong SECRET_KEY**: Minimum 50 characters, cryptographically random
3. **Enable HTTPS**: Always use `SESSION_COOKIE_SECURE=True` and `CSRF_COOKIE_SECURE=True` in production
4. **Restrict ALLOWED_HOSTS**: Never use wildcards in production

### Performance

1. **Use Redis**: Always use Redis cache in production (not LocMemCache)
2. **Use PostgreSQL**: SQLite is only for development
3. **Enable WhiteNoise**: For efficient static file serving
4. **Use CDN**: Configure S3/CloudFront for static/media files in production

### Maintainability

1. **Use environment files**: Keep `stack.env` and `stack.production.env` in version control (without secrets)
2. **Document overrides**: Comment why you override framework defaults
3. **Test environments**: Test staging configuration before production
4. **Use addons wisely**: Only enable addons you need

## Examples

### Minimal Development Setup

```python
# settings.py
import fairdm

fairdm.setup()  # That's it! Uses SQLite, LocMemCache, etc.
```

### Production Setup

```bash
# .env or stack.production.env
DJANGO_ENV=production
DJANGO_SECRET_KEY="your-secret-key"
DJANGO_ALLOWED_HOSTS="example.com"
DJANGO_SITE_DOMAIN="example.com"
DJANGO_SITE_NAME="My Portal"
DATABASE_URL="postgresql://user:pass@localhost/dbname"
REDIS_URL="redis://localhost:6379/0"
```

```python
# settings.py
import fairdm

fairdm.setup()
```

### Portal with Customization

```python
# settings.py
import fairdm

fairdm.setup(
    addons=["fairdm_discussions"],
    TIME_ZONE="Europe/London",
)

# Add portal apps
INSTALLED_APPS = INSTALLED_APPS + [
    "my_samples",
    "my_measurements",
]

# Customize templates
TEMPLATES[0]["DIRS"].insert(0, BASE_DIR / "templates")
```

## See Also

- {doc}`/developer-guide/production` - Docker deployment guide
- {doc}`/developer-guide/setting_up` - Initial portal setup
- {doc}`/contributing/testing` - Testing your configuration
