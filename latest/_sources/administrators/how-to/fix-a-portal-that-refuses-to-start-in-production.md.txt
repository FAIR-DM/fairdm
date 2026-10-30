# How to fix a portal that refuses to start in production

A portal on the production configuration stops at start-up when a production-critical check fails, and it lists every failing check in one message. Each section below is headed by what you see, gives the cause in one sentence and then the fix.

Wherever a fix sets an environment variable, set it in the portal's process environment, or in a `stack.env` or `stack.production.env` file in the portal's base directory, and restart the portal. The order in which FairDM reads these files is in [Configuration](../../developers/reference/configuration.md).

## The portal stops with "FairDM production configuration is invalid"

A production-critical check failed, so the guard stopped the portal before it served a request. The message lists each failing check by id.

Look up each id in [Configuration checks](../reference/configuration-checks.md), apply its fix and restart. The sections below cover the common ones. Every management command stops with the same message while the fault remains, `check --deploy` included.

## The portal stops on a machine you treat as a development machine

Only a `DJANGO_ENV` of exactly `development` stands the guard down, so `Development`, an empty value or a typo is treated as production.

Set `DJANGO_ENV=development` exactly. When the variable is unset, the environment is `production`. Do not set it to `development` on a portal that serves real users.

## The message names fairdm.E001, or says the secret key is not set, insecure or short

The secret key is empty, carries the `django-insecure-` prefix or has fewer than 50 characters.

Set `DJANGO_SECRET_KEY` to a random value of 50 or more characters.

```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

## The message names fairdm.E100, E101 or E102, or says the database has no name

The database settings are empty, point at an engine other than PostGIS, or carry no database name.

Set `DATABASE_URL` to a complete PostgreSQL connection string. FairDM opens it with the PostGIS backend whatever the scheme says. Alternatively set `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST` and `POSTGRES_PORT`.

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

The database needs the PostGIS extension, and the server needs the GDAL, GEOS and PROJ libraries.

## The message names fairdm.E003 or fairdm.E004, or says the allowed hosts list is empty or has a wildcard

`ALLOWED_HOSTS` holds no host, or it holds `*`.

Set `DJANGO_SITE_DOMAIN`, or set `DJANGO_ALLOWED_HOSTS` to a comma-separated list of host names. Remove `*` from both.

```bash
DJANGO_ALLOWED_HOSTS=example.com,www.example.com
```

## The message names fairdm.E005, or says debug is on

`DEBUG` is `True`.

Set `DJANGO_DEBUG=False`, or remove the variable, and remove any `DEBUG = True` in your settings.

## The message names fairdm.E200, or says the cache is not shared

The `default` cache is a per-process backend, or `REDIS_URL` is unset.

Set `REDIS_URL` to a running Redis instance. The cache settings read no other variable.

```bash
REDIS_URL=redis://localhost:6379/1
```

## The message names fairdm.E500, or says a role is missing from the database

One of the four portal roles is not in the database, so everyone in it has lost their rights.

Run `python manage.py migrate`. The command is allowed to run while a role is missing, and it installs the roles. Do not delete or rename a role in the administration interface. The portal refuses both.

## The message names fairdm.E501, or says development accounts are present

A person holds the email address of a development account, and those accounts share a published password.

Delete the accounts the message names. Only a superuser can delete a person. If the portal really is a development portal, set `DJANGO_ENV=development` instead.

## The message says "FairDM configuration is invalid" and names fairdm.E400

`PARLER_LANGUAGES` names a language code that `LANGUAGES` does not include. This stops the portal in every environment, not only in production.

Add the missing codes to `LANGUAGES`, or remove them from `PARLER_LANGUAGES` and `PARLER_DEFAULT_LANGUAGE_CODE`.

## The message names an addon and says its setup module could not be found or raised an error

A package listed in `fairdm.setup(addons=[...])` is not installed, names a setup module that does not exist, or fails while its settings apply. Where `DJANGO_ENV` is `production`, this stops the portal.

Install the addon package in the portal's environment, or correct the module its `__fdm_setup_module__` names, or fix the error the message quotes. In any other environment the addon is skipped with a warning.

## What to do next

Run the checks again once the portal starts, because the start-up guard covers only the production-critical subset. See [How to run the configuration checks](run-the-configuration-checks.md). The reason for the guard is in [How FairDM configures a portal](../../explanation/how-fairdm-configures-a-portal.md).
