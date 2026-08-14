# Configuration Checks

FairDM validates portal configuration through Django's check framework — there is no second,
FairDM-specific validation path (FR-018).

## Production-critical checks run automatically at boot

Whenever the settings in force are the production baseline, `FairDMConfig.ready()` — the first
point in Django's boot sequence where the check framework has a populated app registry to run
against — runs a fixed, production-critical subset of checks and refuses to start if any of them
fails. Every failure is reported together, in one error, rather than stopping at the first
(FR-013, SC-003):

- a production-grade database is configured (`fairdm.E100`, `E101`, `E102`)
- a shared cache backend is configured (`fairdm.E200`)
- `SECRET_KEY` is set and not an insecure or published value (`fairdm.E001`)
- `ALLOWED_HOSTS` is non-empty and not wildcarded (`fairdm.E003`, `E004`)
- `DEBUG` is `False` (`fairdm.E005`)

Celery is deliberately **not** in this subset — a portal may legitimately run without a
background worker, and blocking a boot on that would make the guard something operators route
around.

Which environments those are is decided the same way the override layers are: by which module was
found. FairDM ships one non-production override module, `development`, and that is the one
environment where nothing in this subset runs and nothing about it is logged (FR-014, SC-004). A
portal missing the same configuration starts normally there, using the development-only fallbacks in
`fairdm/conf/development.py`.

Every other value of `DJANGO_ENV` runs on the production baseline — a typo, a case variant such as
`Production`, an empty string, or a `staging` name your own portal supplies a module for — so every
other value is checked against production standards. Set `DJANGO_ENV` to exactly `development` to opt
out; nothing else does.

## Running the full check set on demand

The subset above is only ever run automatically in production. The full check set — including
Celery and everything Django itself contributes — is always available on demand and assesses
against production standards regardless of the current resolved environment (FR-015):

```bash
python manage.py check --deploy
```

```bash
python manage.py check
```

Plain `check` (no `--deploy`) runs every check *not* tagged as a deployment check — FairDM's
configuration checks are all deployment checks, so use `--deploy` to see them.

**Recommendation:** run `check --deploy` in CI and again during deployment, in addition to (not
instead of) the automatic production boot guard — the guard only fires once a process has
actually started, while a CI run catches a misconfiguration before anything ships.

## Check Categories

### Database Checks (fairdm.E100-E199)

#### E100: DATABASES['default'] Not Configured

**Error:** No default database configured at all.
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

#### E102: DATABASES['default'] Configured but Unusable

**Error:** `DATABASE_URL` is present but syntactically malformed — it parses to a database
configuration with an engine but no database name (for example `postgresql://` with nothing
after the scheme). This is distinct from E100: the value is present, just unusable.
**Fix:** Set `DATABASE_URL` to a complete PostgreSQL connection string.

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

### Cache Checks (fairdm.E200-E299)

#### E200: Cache Backend Not Shared

**Error:** The default cache is absent, empty, or a per-process backend — locmem, dummy,
filebased, or anything else outside the shared-backend allowlist (Redis, Memcached).
**Fix:** Set `REDIS_URL` to a Redis instance. This is the variable the cache settings module
reads — `CACHE_URL` is not consulted.

```bash
REDIS_URL=redis://localhost:6379/1
```

### Security Checks (fairdm.E001, E003-E005)

#### E001: SECRET_KEY Not Set or Insecure

**Error:** SECRET_KEY is empty or missing, it carries the `django-insecure-` prefix that
marks a published development key — including FairDM's own shipped fallback — or it is shorter
than 50 characters.
**Fix:** Set `DJANGO_SECRET_KEY` to a private, randomly generated value of 50 characters or more.

```bash
DJANGO_SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
```

**Note:** Django also provides security.W009 for the same condition, but only as a *Warning* —
FairDM's own check exists specifically so this can block a boot.

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

**Note:** Django also provides security.W018 for DEBUG checks. For cookie security
(SESSION_COOKIE_SECURE and CSRF_COOKIE_SECURE), Django provides security.W012 and security.W016
respectively.

### Celery Checks (fairdm.E300-E399)

Not part of the production-critical subset — see above. Only reported by `check --deploy`.

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
    DJANGO_SETTINGS_MODULE: config.settings
    DJANGO_ENV: production
```

### GitLab CI Example

```yaml
test:checks:
  stage: test
  script:
    - poetry run python manage.py check --deploy
  variables:
    DJANGO_SETTINGS_MODULE: config.settings
    DJANGO_ENV: production
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

# Only the production-critical subset FairDMConfig.ready() runs at boot
python manage.py check --deploy --tag production_critical
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

**Warning:** Only silence checks if you understand the security implications. A check in the
production-critical subset still runs at boot even if silenced from `check --deploy`'s output —
silencing hides it from the report, not from `FairDMConfig.ready()`.

## Troubleshooting

### The Portal Refuses to Start in Production

This is the intended behaviour when a production-critical check fails (FR-013). The raised error
lists every failing check by id — fix the configuration each one names and restart.

If this happens on a machine you consider a development box, check `DJANGO_ENV` first: only the exact
value `development` stands the guard down, so `Development` or an unset-then-emptied variable is
treated as a production deployment (FR-014).

### Check Command Exits with Error Code 1

This is expected when errors are found. Fix the reported issues before deploying.

### Check Command Shows Warnings But Succeeds

Warnings don't prevent deployment but should be addressed for production environments.

### Cannot Import fairdm.conf.checks

Ensure checks are imported in `fairdm/apps.py`, at module level rather than inside `ready()`, so
the full set registers regardless of the resolved environment:

```python
from fairdm.conf import checks as conf_checks  # noqa: F401
```
