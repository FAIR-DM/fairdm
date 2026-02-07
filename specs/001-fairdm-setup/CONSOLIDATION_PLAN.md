# Settings Consolidation Plan

**Task**: T001 - Audit existing settings files and create consolidation mapping
**Date**: 2026-01-05
**Feature**: specs/002-production-config-fairdm-conf

## Current State

**Existing Files** (25 files, ~1,350 total lines):
- `apps.py` (97 lines) - INSTALLED_APPS
- `general.py` (135 lines) - MIDDLEWARE, TEMPLATES, core Django settings
- `authentication.py` (75 lines) - Auth backends, password validators, allauth config
- `database.py` (42 lines) - Database configuration
- `cache.py` (66 lines) - Cache backends (Redis/LocMem)
- `security.py` (48 lines) - Security settings (HTTPS, cookies, HSTS)
- `file_storage.py` (76 lines) - Static/media file configuration
- `celery.py` (35 lines) - Celery configuration
- `logging.py` (77 lines) - Logging and Sentry
- `email.py` (31 lines) - Email backend
- `icons.py` (178 lines) - Icon configuration (easy-icons)
- `markdown.py` (162 lines) - Markdown editor configuration
- `theme_options.py` (93 lines) - Theme/UI configuration
- `page_config.py` (48 lines) - Page-level settings
- `fairdm.py` (42 lines) - FairDM-specific settings
- `language.py` (15 lines) - i18n settings
- `seo.py` (14 lines) - SEO/meta tags
- `configuration.py` (14 lines) - django-solo configuration
- `thumbnailer.py` (23 lines) - Easy-thumbnails configuration
- `invitations.py` (11 lines) - django-invitations
- `flex_menu.py` (10 lines) - Menu configuration
- `activity_streams.py` (5 lines) - Activity stream settings
- `import_export.py` (4 lines) - Import/export settings
- `webpack.py` (0 lines) - Empty
- `admin.py` (0 lines) - Empty

## Target State (8-12 focused modules)

### Core Modules (Must Have)

#### 1. `apps.py` - Application Stack (~150 lines)
**Sources**: Current `apps.py` + `general.py` (MIDDLEWARE, TEMPLATES)
**Responsibility**: INSTALLED_APPS, MIDDLEWARE, TEMPLATES, ROOT_URLCONF, WSGI_APPLICATION
**Content**:
- INSTALLED_APPS list (keep as-is from current apps.py)
- MIDDLEWARE stack (from general.py)
- TEMPLATES configuration (from general.py)
- ROOT_URLCONF, WSGI_APPLICATION (from general.py)

#### 2. `database.py` - Database Configuration (~50 lines)
**Sources**: Current `database.py`
**Responsibility**: PostgreSQL/SQLite configuration with env vars
**Content**:
- DATABASES configuration (PostgreSQL from DATABASE_URL)
- ATOMIC_REQUESTS, CONN_MAX_AGE
- Database backup settings (DBBACKUP_*)
**Production**: Requires DATABASE_URL, fails fast if missing

#### 3. `cache.py` - Cache Configuration (~70 lines)
**Sources**: Current `cache.py`
**Responsibility**: Redis/LocMem cache backends
**Content**:
- CACHES (default, select2, vocabularies)
- SELECT2_CACHE_BACKEND, SELECT2_THEME
- COLLECTFASTA_CACHE, VOCABULARY_DEFAULT_CACHE
**Production**: Requires REDIS_URL, fails fast if missing

#### 4. `security.py` - Security Settings (~80 lines)
**Sources**: Current `security.py` + `general.py` (SECRET_KEY, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS)
**Responsibility**: Production security hardening
**Content**:
- DEBUG = False
- SECRET_KEY (from env, required)
- ALLOWED_HOSTS (from env, required)
- CSRF_TRUSTED_ORIGINS
- SECURE_SSL_REDIRECT, SECURE_HSTS_*
- SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE
- SESSION_COOKIE_HTTPONLY, CSRF_COOKIE_HTTPONLY
- SECURE_BROWSER_XSS_FILTER, X_FRAME_OPTIONS
**Production**: Requires DJANGO_SECRET_KEY, DJANGO_ALLOWED_HOSTS

#### 5. `static_media.py` - Static & Media Files (~100 lines)
**Sources**: Current `file_storage.py`
**Responsibility**: WhiteNoise, static/media storage, thumbnails
**Content**:
- STATIC_ROOT, STATIC_URL, STATICFILES_DIRS, STATICFILES_FINDERS
- MEDIA_ROOT, MEDIA_URL
- STORAGES (WhiteNoise for static, local/S3 for media)
- THUMBNAIL_* settings (easy-thumbnails)
- WhiteNoise configuration

#### 6. `celery.py` - Background Tasks (~40 lines)
**Sources**: Current `celery.py`
**Responsibility**: Celery broker/backend configuration
**Content**:
- CELERY_BROKER_URL (from REDIS_URL or env)
- CELERY_RESULT_BACKEND
- CELERY_TASK_ALWAYS_EAGER, CELERY_TASK_EAGER_PROPAGATES
**Production**: Requires REDIS_URL

#### 7. `auth.py` - Authentication (~100 lines)
**Sources**: Current `authentication.py`
**Responsibility**: Auth backends, password validation, allauth
**Content**:
- AUTH_USER_MODEL
- AUTHENTICATION_BACKENDS (ModelBackend, allauth, guardian)
- AUTH_PASSWORD_VALIDATORS
- PASSWORD_HASHERS
- LOGIN_URL, LOGIN_REDIRECT_URL
- ACCOUNT_* (django-allauth settings)
**Keep**: Most allauth settings (they're production-ready)

#### 8. `logging.py` - Logging (~80 lines)
**Sources**: Current `logging.py`
**Responsibility**: Production logging and Sentry
**Content**:
- Sentry SDK initialization (if SENTRY_DSN set)
- LOGGING configuration (handlers, formatters, loggers)
**Production**: Sentry optional but recommended

#### 9. `email.py` - Email Backend (~40 lines)
**Sources**: Current `email.py`
**Responsibility**: Email configuration
**Content**:
- EMAIL_BACKEND
- EMAIL_HOST, EMAIL_PORT, EMAIL_USE_TLS
- DEFAULT_FROM_EMAIL
**Production**: Requires SMTP credentials if using email

### Optional/Addon-Specific Modules (Keep Separate)

These settings are addon/library-specific and should remain as separate files that are conditionally included:

#### 10. `fairdm_addons.py` - FairDM-Specific Add-ons (~250 lines)
**Sources**: `icons.py`, `markdown.py`, `theme_options.py`, `page_config.py`, `fairdm.py`
**Responsibility**: FairDM framework add-on configurations
**Rationale**: These are highly specific to FairDM extras (icons, markdown, themes) and not core Django
**Content**:
- EASY_ICONS_* (icon configuration)
- MARTOR_* (markdown editor)
- CRISPY_*, DJANGO_TABLES2_* (UI frameworks)
- PAGE_CONFIG_* (page settings)
- FAIRDM_* (framework-specific)

#### Keep as separate files (to be loaded conditionally):
- `language.py` (15 lines) - i18n settings (LANGUAGES, LANGUAGE_CODE, USE_I18N, LOCALE_PATHS)
- `seo.py` (14 lines) - django-meta SEO settings
- `configuration.py` (14 lines) - django-solo, waffle flags
- `invitations.py` (11 lines) - django-invitations
- `flex_menu.py` (10 lines) - django-flex-menus
- `activity_streams.py` (5 lines) - django-activity-stream
- `import_export.py` (4 lines) - django-import-export

#### Delete (empty or obsolete):
- `webpack.py` (0 lines)
- `admin.py` (0 lines)

## Consolidation Actions

### Phase 1: Create Core Modules (T003-T011)
1. **T003**: Consolidate `apps.py` - merge current apps.py + general.py (MIDDLEWARE, TEMPLATES)
2. **T004**: Keep `database.py` mostly as-is, ensure env var usage
3. **T005**: Keep `cache.py` mostly as-is, ensure fail-fast logic
4. **T006**: Consolidate `security.py` - merge security.py + general.py (SECRET_KEY, ALLOWED_HOSTS)
5. **T007**: Rename `file_storage.py` → `static_media.py`, clean up
6. **T008**: Keep `celery.py` as-is
7. **T009**: Rename `authentication.py` → `auth.py`, clean up
8. **T010**: Keep `logging.py` mostly as-is
9. **T011**: Keep `email.py` as-is

### Phase 2: Create Add-on Module (Optional)
10. Create `fairdm_addons.py` by merging:
    - icons.py
    - markdown.py
    - theme_options.py
    - page_config.py
    - fairdm.py

### Phase 3: Archive/Keep Small Files
- Move to `fairdm/conf/settings/optional/`:
  - language.py
  - seo.py
  - configuration.py
  - invitations.py
  - flex_menu.py
  - activity_streams.py
  - import_export.py

### Phase 4: Cleanup (T012)
- Delete webpack.py (empty)
- Delete admin.py (empty)
- Archive old general.py after consolidation

## Loading Order in setup.py

```python
# Core modules (always loaded in production)
include('settings/apps.py')
include('settings/database.py')
include('settings/cache.py')
include('settings/security.py')
include('settings/static_media.py')
include('settings/celery.py')
include('settings/auth.py')
include('settings/logging.py')
include('settings/email.py')

# FairDM add-ons (framework-specific)
include('settings/fairdm_addons.py')

# Optional modules (conditionally loaded based on what's enabled)
if some_condition:
    include('settings/optional/language.py')
    include('settings/optional/seo.py')
    # etc.
```

## Validation Needs

Each core module that requires env vars should handle them gracefully:

**Production/Staging**: Fail fast if env vars missing
**Local/Development**: Degrade gracefully with warnings and fallbacks

Modules needing validation:
- `database.py`: DATABASE_URL required in prod, SQLite fallback in local
- `cache.py`: REDIS_URL required in prod, LocMemCache fallback in local
- `security.py`: SECRET_KEY, ALLOWED_HOSTS required in prod
- `celery.py`: REDIS_URL required in prod
- `email.py`: EMAIL_* required if email features enabled

## Estimated Consolidation Effort

- **High Effort** (merge + refactor): apps.py, security.py, fairdm_addons.py
- **Medium Effort** (rename + cleanup): static_media.py, auth.py
- **Low Effort** (keep as-is): database.py, cache.py, celery.py, logging.py, email.py

**Total Estimated Time**: 4-6 hours for all consolidation tasks

## Success Criteria

✅ 8-12 focused modules in `fairdm/conf/settings/`
✅ Each module has clear, single responsibility
✅ All env var dependencies documented
✅ No duplication across modules
✅ Loading order is deterministic
✅ Optional/addon settings isolated
✅ Empty files deleted
