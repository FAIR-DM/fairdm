# Configuration Checks Quickstart

**Purpose**: Guide for portal administrators on validating FairDM configuration before deployment.

## Overview

FairDM includes built-in configuration checks that validate your portal's readiness for production deployment. These checks verify that critical settings (database, cache, security, background tasks) are properly configured.

## Running Configuration Checks

### Basic Check

Run basic configuration validation:

```bash
python manage.py check
```

This runs standard Django checks plus any FairDM-specific checks that don't require the `--deploy` flag.

### Deployment Check

Run comprehensive production-readiness validation before deploying:

```bash
python manage.py check --deploy
```

This runs ALL checks, including production-critical validations that assess whether your configuration meets production standards.

**When to use `--deploy`:**

- Before deploying to staging or production
- As part of your CI/CD pipeline
- When troubleshooting production configuration issues
- Before upgrading FairDM to a new version

## Understanding Check Output

### Success

When all checks pass:

```
System check identified no issues (0 silenced).
```

### Errors

Critical issues that must be fixed:

```
System check identified some issues:

ERRORS:
fairdm.E001: SECRET_KEY is not set.
 HINT: Set DJANGO_SECRET_KEY environment variable.

fairdm.E100: DATABASES['default'] is not configured.
 HINT: Set DATABASE_URL environment variable.
```

### Warnings

Recommended improvements:

```
WARNINGS:
fairdm.W001: SECRET_KEY is too short (20 characters).
 HINT: Recommended: 50+ characters for production.
```

## Common Issues & Resolutions

### SECRET_KEY Issues

**Error**: `fairdm.E001: SECRET_KEY is not set`

**Resolution**:

```bash
# Generate a secure secret key
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# Set it as an environment variable
export DJANGO_SECRET_KEY='<generated-key>'
```

**Warning**: `fairdm.W001: SECRET_KEY is too short`

**Resolution**: Generate a longer secret key (50+ characters recommended).

---

### Database Issues

**Error**: `fairdm.E100: DATABASES['default'] is not configured`

**Resolution**:

```bash
# Set database URL
export DATABASE_URL='postgresql://user:pass@localhost:5432/dbname'
```

**Error**: `fairdm.E101: SQLite is not recommended for production`

**Resolution**: Configure PostgreSQL for production:

```bash
export DATABASE_URL='postgresql://user:pass@host:5432/dbname'
```

---

### Cache Issues

**Error**: `fairdm.E200: Cache backend 'locmem' is not suitable for production`

**Resolution**:

```bash
# Configure Redis cache
export REDIS_URL='redis://localhost:6379/0'
```

---

### Security Issues

**Error**: `fairdm.E002: ALLOWED_HOSTS is empty`

**Resolution**:

```bash
# Set allowed hosts for production
export DJANGO_ALLOWED_HOSTS='example.com,www.example.com'
```

**Error**: `fairdm.E003: ALLOWED_HOSTS contains '*' (wildcard)`

**Resolution**: Specify explicit domain names instead of wildcard.

**Error**: `fairdm.E004: DEBUG is True`

**Resolution**:

```bash
export DJANGO_DEBUG=False
```

**Error**: `fairdm.E010: SESSION_COOKIE_SECURE must be True in production`

**Resolution**: Ensure HTTPS is configured and the setting is enabled.

---

### Celery Issues

**Error**: `fairdm.E300: CELERY_BROKER_URL is not set`

**Resolution**:

```bash
# Use Redis as broker (or RabbitMQ)
export REDIS_URL='redis://localhost:6379/0'
```

**Error**: `fairdm.E301: CELERY_TASK_ALWAYS_EAGER is True`

**Resolution**: This setting makes tasks run synchronously (for testing only). Remove or set to False for production.

---

## Integration with CI/CD

### GitLab CI Example

```yaml
test:
  script:
    - python manage.py check --deploy
    - pytest
```

### GitHub Actions Example

```yaml
- name: Run configuration checks
  run: python manage.py check --deploy

- name: Run tests
  run: pytest
```

### Pre-deployment Checklist

1. ✅ Run `python manage.py check --deploy` locally
2. ✅ Resolve all ERRORs
3. ✅ Review and address WARNINGs
4. ✅ Commit configuration changes
5. ✅ Verify checks pass in CI/CD pipeline
6. ✅ Deploy

## Troubleshooting

### Checks Don't Run

**Issue**: Running `check` command shows no FairDM checks

**Possible causes**:

1. FairDM app not in INSTALLED_APPS
2. App configuration not loaded properly
3. Checks module not imported

**Diagnosis**:

```python
# In Django shell
from django.apps import apps
config = apps.get_app_config('fairdm_conf')
print(config)  # Should show FairdmConfConfig
```

### False Positives

**Issue**: Checks report errors for settings that are correctly configured

**Possible causes**:

1. Environment variables not loaded
2. Settings override not applied
3. Check logic needs updating

**Diagnosis**:

```python
# In Django shell
from django.conf import settings
print(settings.SECRET_KEY)  # Verify actual setting value
print(settings.DATABASES)
```

### Silent Failures

**Issue**: Configuration is wrong but checks don't catch it

**Action**: File a bug report with:

- The incorrect configuration
- Expected check behavior
- Actual check behavior
- Steps to reproduce

## Additional Resources

- [Django System Check Framework](https://docs.djangoproject.com/en/stable/topics/checks/)
- [FairDM Configuration Guide](../portal-development/configuration.md)
- [Deployment Checklist](deployment-checklist.md)
- [Environment Variables Reference](environment-variables.md)

## Summary

- Use `python manage.py check` for basic validation
- Use `python manage.py check --deploy` before deployment
- Fix all ERRORs before deploying
- Review and address WARNINGs
- Integrate checks into CI/CD pipeline
- Run checks as part of regular maintenance
