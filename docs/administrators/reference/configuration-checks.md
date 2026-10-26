# Configuration checks

This page lists every configuration check FairDM adds to Django's check framework. Each entry gives the check's id, its severity, its tags, what it reports and how to fix it. It does not explain why the portal refuses to start in production, which is in [How FairDM configures a portal](../../explanation/how-fairdm-configures-a-portal.md), and it does not list the checks Django itself provides.

## Tags

Every check carries the tags shown in its entry. You pass a tag to `manage.py check --tag` to run only the checks that carry it.

| Tag | Meaning |
|---|---|
| `database` | The database settings. |
| `caches` | The cache settings. |
| `security` | Secrets, hosts, debug mode and cookies. |
| `translation` | The language settings. |
| `models` | The portal's registered sample and measurement types. |
| `deploy` | A FairDM check that runs only with `--deploy`. |
| `production_critical` | A check that also runs at start-up when the settings in force are the production baseline. A failing one stops the portal from starting. |

A check registered as a deployment check runs only when you pass `--deploy`. A check without that registration runs on plain `manage.py check`, at `runserver` and at `migrate`.

## Summary

| Id | Severity | Stops a production start | Runs without `--deploy` |
|---|---|---|---|
| `fairdm.E001` | Error | Yes | No |
| `fairdm.E003` | Error | Yes | No |
| `fairdm.E004` | Error | Yes | No |
| `fairdm.E005` | Error | Yes | No |
| `fairdm.E006` | Error | No | Yes |
| `fairdm.E100` | Error | Yes | No |
| `fairdm.E101` | Error | Yes | No |
| `fairdm.E102` | Error | Yes | No |
| `fairdm.E200` | Error | Yes | No |
| `fairdm.E300` | Error | No | No |
| `fairdm.E301` | Error | No | No |
| `fairdm.E400` | Error | Yes, in every environment | Yes |
| `fairdm.E500` | Error | Yes | No |
| `fairdm.E501` | Error | Yes | No |
| `fairdm.E700` | Error | Yes | No |
| `fairdm.E701` | Error | Yes | No |
| `fairdm.E600` | Error | No | Yes |
| `fairdm.W601` | Warning | No | No |

## fairdm.E001: the secret key is empty, insecure or too short

- **Severity**: Error.
- **Tags**: `security`, `deploy`, `production_critical`.
- **Reports**: One of three conditions.
  - `SECRET_KEY` is empty.
  - `SECRET_KEY` starts with `django-insecure-`, the prefix of a published development key. FairDM's own development fallback carries it.
  - `SECRET_KEY` is shorter than 50 characters.
- **Fix**: Set `DJANGO_SECRET_KEY` to a private, randomly generated value of 50 characters or more.

```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

## fairdm.E003: the allowed hosts list is empty

- **Severity**: Error.
- **Tags**: `security`, `deploy`, `production_critical`.
- **Reports**: `ALLOWED_HOSTS` is empty. FairDM builds it from `DJANGO_SITE_DOMAIN` and `DJANGO_ALLOWED_HOSTS`, so the check fires when both are unset.
- **Fix**: Set `DJANGO_SITE_DOMAIN`, or set `DJANGO_ALLOWED_HOSTS` to a comma-separated list of host names.

```bash
DJANGO_ALLOWED_HOSTS=example.com,www.example.com
```

## fairdm.E004: the allowed hosts list contains a wildcard

- **Severity**: Error.
- **Tags**: `security`, `deploy`, `production_critical`.
- **Reports**: `ALLOWED_HOSTS` contains `*`.
- **Fix**: Name each host. Remove `*` from `DJANGO_ALLOWED_HOSTS` and from any assignment in your settings.

## fairdm.E005: debug mode is on

- **Severity**: Error.
- **Tags**: `security`, `deploy`, `production_critical`.
- **Reports**: `DEBUG` is `True`.
- **Fix**: Set `DJANGO_DEBUG=False`, or remove the variable. The default is `False`.

## fairdm.E006: a cookie name has a prefix the browser will not accept

- **Severity**: Error.
- **Tags**: `security`. This is not a deployment check.
- **Reports**: `CSRF_COOKIE_NAME`, `SESSION_COOKIE_NAME` or `LANGUAGE_COOKIE_NAME` starts with `__Secure-` or `__Host-` while its own `*_COOKIE_SECURE` setting is `False`. A browser discards such a cookie, so every sign-in post fails with "CSRF verification failed. Request aborted." The check reports one error for each cookie.
- **Fix**: Set the matching `*_COOKIE_SECURE` setting to `True`, or remove the prefix from the cookie name for an environment served over plain HTTP.

```python
CSRF_COOKIE_NAME = "csrftoken"
SESSION_COOKIE_NAME = "sessionid"
```

## fairdm.E100: no default database is configured

- **Severity**: Error.
- **Tags**: `database`, `deploy`, `production_critical`.
- **Reports**: `DATABASES["default"]` is missing or empty. FairDM's baseline always fills it, so this appears only when your own settings remove or empty it.
- **Fix**: Leave `DATABASES` to FairDM and set `DATABASE_URL`.

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

## fairdm.E101: the database is not PostgreSQL with PostGIS

- **Severity**: Error.
- **Tags**: `database`, `deploy`, `production_critical`.
- **Reports**: The `ENGINE` of `DATABASES["default"]` is not `django.contrib.gis.db.backends.postgis`.
- **Fix**: Leave `DATABASES` to FairDM and set `DATABASE_URL`. FairDM opens it with the PostGIS backend whatever scheme it names. A portal that sets `DATABASES` itself sets `ENGINE` to the PostGIS backend. The database needs the PostGIS extension, and the server needs the GDAL, GEOS and PROJ libraries.

## fairdm.E102: the database has no name

- **Severity**: Error.
- **Tags**: `database`, `deploy`, `production_critical`.
- **Reports**: `DATABASES["default"]` has no `NAME`. This is what an unset or malformed `DATABASE_URL` leaves, for example `postgresql://` with nothing after the scheme.
- **Fix**: Set `DATABASE_URL` to a complete PostgreSQL connection string, or set `POSTGRES_DB` with `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST` and `POSTGRES_PORT`.

## fairdm.E200: the cache is not shared

- **Severity**: Error.
- **Tags**: `caches`, `deploy`, `production_critical`.
- **Reports**: The `default` cache is not one of these backends, or it is the placeholder FairDM uses when `REDIS_URL` is unset.
  - `django_redis.cache.RedisCache`
  - `django.core.cache.backends.memcached.PyMemcacheCache`
  - `django.core.cache.backends.memcached.PyLibMCCache`
- **Fix**: Set `REDIS_URL` to a Redis instance. The cache settings read no other variable.

```bash
REDIS_URL=redis://localhost:6379/1
```

## fairdm.E300: no Celery broker is configured

- **Severity**: Error.
- **Tags**: `deploy`. Not part of the start-up guard.
- **Reports**: `CELERY_BROKER_URL` is empty. FairDM fills it from `REDIS_URL`.
- **Fix**: Set `REDIS_URL`.

## fairdm.E301: Celery tasks run in the web process

- **Severity**: Error.
- **Tags**: `deploy`. Not part of the start-up guard.
- **Reports**: `CELERY_TASK_ALWAYS_EAGER` is `True`, so background tasks run synchronously. FairDM sets it to `True` itself when `DJANGO_ENV` is `development` and `REDIS_URL` is unset.
- **Fix**: Remove the assignment in your settings that sets it to `True`. For a development portal, set `REDIS_URL` to run tasks on a worker.

## fairdm.E400: the language settings disagree

- **Severity**: Error.
- **Tags**: `translation`. This is not a deployment check.
- **Reports**: `PARLER_LANGUAGES` names a language code that `LANGUAGES` does not include. A code such as `fr-ca` is accepted when `LANGUAGES` has `fr`. The `code` under the `default` key and `PARLER_DEFAULT_LANGUAGE_CODE` are checked too. The same rule runs when the settings load and again when the portal's models load, in every environment, so the portal stops before any command runs.
- **Fix**: Add the missing codes to `LANGUAGES`, or remove them from `PARLER_LANGUAGES` and `PARLER_DEFAULT_LANGUAGE_CODE`.

## fairdm.E500: a portal role is missing

- **Severity**: Error.
- **Tags**: `deploy`, `production_critical`.
- **Reports**: One or more of the four shipped roles is not in the database: Portal Administrator, Data Curator, Community Manager, Developer. The message names each missing role. The check stands down while `migrate` runs, and it reports nothing when the group table cannot be read.
- **Fix**: Run `python manage.py migrate`, which installs the roles.

## fairdm.E501: development accounts exist outside development

- **Severity**: Error.
- **Tags**: `deploy`, `production_critical`.
- **Reports**: A person holds one of the email addresses of FairDM's development accounts, which share a published password. The check stands down when `DJANGO_ENV` is `development`. The addresses are:
  - `portal.administrator@example.com`
  - `data.curator@example.com`
  - `community.manager@example.com`
  - `portal.developer@example.com`
  - `regular.user@example.com`
  - `staff.user@example.com`
  - `super.user@example.com`
  - `admin.user@example.com`
  - `member.user@example.com`
  - `former-admin.user@example.com`
  - `community-manager.user@example.com`
  - `data-curator.user@example.com`
- **Fix**: Remove the accounts the message names. If the portal is a development portal, set `DJANGO_ENV=development`.

## fairdm.E600: a registered type cannot be created through the API

- **Severity**: Error.
- **Tags**: `models`. This is not a deployment check.
- **Reports**: The API serializer of a registered sample or measurement type has no writable field for a field the model requires. A field is required when it is editable, has no default and may be neither blank nor null. A field the serializer marks read-only counts as left out. The message names the type and the field, and no record of the type can be created through the API.
- **Fix**: Add the field to `serializer_fields` or `fields` in the type's registration, or to the serializer the registration names. See [Model configuration](../../developers/reference/model-configuration.md).

## fairdm.W601: the number of proxies in front of the API is not set

- **Severity**: Warning.
- **Tags**: `security`, `deploy`. This check never stops the portal from starting.
- **Reports**: `REST_FRAMEWORK` has no `NUM_PROXIES` key. The API then takes a caller's address from the `X-Forwarded-For` header, which the caller writes. Any value you set silences the warning, `0` and `None` included.
- **Fix**: Set the number of proxies between the visitor and the portal, or `0` when there is none. See [How to count API callers behind a proxy](../../developers/how-to/count-api-callers-behind-a-proxy.md).

```python
REST_FRAMEWORK["NUM_PROXIES"] = 1
```

## fairdm.E700: no backup public key is set

- **Severity**: Error.
- **Tags**: `security`, `deploy`, `production_critical`.
- **Reports**: `BACKUP_PUBLIC_KEY` is empty. A production portal does not write unencrypted backups, so it does not start.
- **Fix**: Set `BACKUP_PUBLIC_KEY` to an armoured OpenPGP public key. See [How to back up a portal](../../developers/how-to/back-up-a-portal.md#encrypt-the-backups).

## fairdm.E701: the backup public key cannot be used

- **Severity**: Error.
- **Tags**: `security`, `deploy`, `production_critical`.
- **Reports**: One of these. `BACKUP_PUBLIC_KEY` is not an armoured public key. The key cannot encrypt, as with a key that only signs. The value holds a private key, which the portal refuses so that it never holds the key that decrypts its backups. Or `gpg` is not installed, as in a custom image without `gnupg`.
- **Fix**: Export the public key with `gpg --armor --export`, and set `BACKUP_PUBLIC_KEY` to its text. Remove a private key from the environment. In a custom image, install `gnupg`.

## What you can do with the checks

- Run them. See [How to run the configuration checks](../how-to/run-the-configuration-checks.md).
- Hide one from the report. See [How to silence a configuration check](../how-to/silence-a-configuration-check.md).
- Fix a portal that stops at start-up. See [How to fix a portal that refuses to start in production](../how-to/fix-a-portal-that-refuses-to-start-in-production.md).
