# Configuration Checks

FairDM uses Django's check framework to validate production-readiness of your portal configuration. This replaces the old runtime logging system with explicit, on-demand validation.

## Running Checks

### Development Mode

```bash
python manage.py check
```

This runs all registered checks, including FairDM's configuration checks. Errors will prevent the application from starting, while warnings are informational.

### Production Deployment Checks

```bash
python manage.py check --deploy
```

The `--deploy` flag runs additional checks specifically for production environments, including:

- Database configuration (PostgreSQL required)
- Cache backend (Redis/Memcached required)
- SECRET_KEY security
- ALLOWED_HOSTS configuration
- DEBUG mode (must be False)
- SSL/HTTPS settings
- Cookie security
- Celery configuration

**Recommendation:** Run this command during deployment to catch configuration issues early.

## Check Categories

### Database Checks (fairdm.E100-E199)

#### E100: DATABASES['default'] Not Configured

**Error:** No default database configured.
**Fix:** Set the `DATABASE_URL` environment variable.

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

#### E101: SQLite Not Recommended for Production

**Error:** Using SQLite in production environment.
**Fix:** Switch to PostgreSQL by setting `DATABASE_URL`.

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

### Cache Checks (fairdm.E200-E299)

#### E200: Development Cache Backend in Production

**Error:** Using LocMemCache or DummyCache in production.
**Fix:** Set `CACHE_URL` to Redis or Memcached.

```bash
CACHE_URL=redis://localhost:6379/1
```

### Security Checks (fairdm.E001, E003-E005)

#### E001: SECRET_KEY Not Set

**Error:** SECRET_KEY is empty or missing.
**Fix:** Set `SECRET_KEY` environment variable (50+ characters recommended).

```bash
SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
```

**Note:** Django also provides security.W009 for SECRET_KEY length and quality checks.

#### E003: ALLOWED_HOSTS Empty

**Error:** ALLOWED_HOSTS list is empty.
**Fix:** Set `DJANGO_ALLOWED_HOSTS` with comma-separated domain names.

```bash
DJANGO_ALLOWED_HOSTS=example.com,www.example.com
```

#### E004: ALLOWED_HOSTS Contains Wildcard

**Error:** ALLOWED_HOSTS contains '*' wildcard.
**Fix:** Specify explicit domain names.

```bash
DJANGO_ALLOWED_HOSTS=example.com,www.example.com
```

#### E005: DEBUG Enabled in Production

**Error:** DEBUG is set to True.
**Fix:** Set `DJANGO_DEBUG=False` in production.

```bash
DJANGO_DEBUG=False
```

**Note:** Django also provides security.W018 for DEBUG checks. For cookie security (SESSION_COOKIE_SECURE and CSRF_COOKIE_SECURE), Django provides security.W012 and security.W016 respectively.

### Celery Checks (fairdm.E300-E399)

#### E300: CELERY_BROKER_URL Not Configured

**Error:** Celery broker URL is missing.
**Fix:** Set `CELERY_BROKER_URL` environment variable.

```bash
CELERY_BROKER_URL=redis://localhost:6379/0
```

#### E301: CELERY_TASK_ALWAYS_EAGER True

**Error:** Celery tasks run synchronously (CELERY_TASK_ALWAYS_EAGER=True).
**Fix:** Set `CELERY_TASK_ALWAYS_EAGER=False` for async task processing.

```bash
CELERY_TASK_ALWAYS_EAGER=False
```

## Integration with CI/CD

Add the check command to your deployment pipeline:

### GitHub Actions Example

```yaml
- name: Run Django Checks
  run: |
    poetry run python manage.py check --deploy
  env:
    DJANGO_SETTINGS_MODULE: config.production
```

### GitLab CI Example

```yaml
test:checks:
  stage: test
  script:
    - poetry run python manage.py check --deploy
  variables:
    DJANGO_SETTINGS_MODULE: config.production
```

### Docker Example

```dockerfile
RUN python manage.py check --deploy
```

## Filtering Checks

### Run Specific Tag

```bash
# Only database checks
python manage.py check --tag database

# Only security checks
python manage.py check --tag security

# Only cache checks
python manage.py check --tag caches

# Only deploy checks
python manage.py check --tag deploy
```

### Combine Tags

```bash
# Security and database checks
python manage.py check --tag security --tag database
```

## Silencing Checks

To silence specific checks, add them to `SILENCED_SYSTEM_CHECKS` in your settings:

```python
SILENCED_SYSTEM_CHECKS = [
    'security.W004',  # Silence HSTS warning
    'security.W008',  # Silence HTTPS redirect warning
]
```

**Warning:** Only silence checks if you understand the security implications.

## Migration from Legacy System

The old `validate_services()` function is deprecated and will be removed in a future version. Update your deployment processes:

**Old (deprecated):**

```python
from fairdm.conf.checks import validate_services
validate_services('production', settings_dict)
```

**New (recommended):**

```bash
python manage.py check --deploy
```

The new system provides:

- ✅ Consistent Django integration
- ✅ Better error reporting
- ✅ Tag-based filtering
- ✅ CI/CD friendly
- ✅ Explicit validation (no runtime noise)

## Troubleshooting

### Check Command Exits with Error Code 1

This is expected when errors are found. Fix the reported issues before deploying.

### Check Command Shows Warnings But Succeeds

Warnings don't prevent deployment but should be addressed for production environments.

### Cannot Import fairdm.conf.checks

Ensure checks are imported in `fairdm/apps.py`:

```python
from fairdm.conf import checks as conf_checks  # noqa: F401
```

This import is required in the `ready()` method to register checks with Django's check framework.
