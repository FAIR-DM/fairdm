# Configuration Guide

FairDM provides a flexible, environment-aware configuration system built on top of Django's settings. This guide explains how to configure your portal for development and production.

## Overview

The configuration system is designed around these principles:

- **One entry point**: a portal's settings module obtains its entire Django configuration from a single `fairdm.setup()` call.
- **Production by default**: `DJANGO_ENV` defaults to `production`, and the baseline it composes is FairDM's production-grade configuration — not a development-friendly one that happens to also work in production.
- **Layered overrides**: everything that varies by environment is expressed as an override module layered on top of the baseline, in a declared order.
- **No allowlist**: an override module is found by existence, not by name-matching a fixed list of permitted environments.

## Quick Start

In your portal's settings module — recommended at `config/settings.py`:

```python
import fairdm

fairdm.setup()
```

That's it. FairDM loads its production-grade defaults, and layers in whatever override modules exist for the resolved environment.

## The `DJANGO_ENV` Variable

The resolved environment is taken literally from `DJANGO_ENV`:

```bash
export DJANGO_ENV=production   # the default when unset
export DJANGO_ENV=development
```

There is no allowlist. Any value is valid — including a typo, or an environment name only your portal knows about. If nothing ships an override module for that name, `setup()` silently falls back to the production baseline: the safe direction, and one a developer notices immediately because the portal behaves as if in production.

FairDM itself ships exactly one override module: `development`. There is no `staging` profile — a portal that wants one supplies its own override module, through the same mechanism as any other environment name.

## The Five Layers

`fairdm.setup()` composes settings in five layers. Each layer applies over the one before it, so a later layer's value for the same setting wins:

1. **The baseline** — FairDM's production-grade defaults, organised under `fairdm/conf/settings/`, one module per concern.
2. **FairDM's own override module** for the resolved environment, if it ships one (only `development.py` today).
3. **Addon settings** — settings contributed by any addon named in `fairdm.setup(addons=[...])`.
4. **The portal's own override module** for the resolved environment, resolved beside the portal's settings module (see below).
5. **Assignment after the `setup()` call**, in the portal's own settings module. This is the only way to override a setting FairDM owns — `setup()` does not accept settings as keyword arguments.

```python
# config/settings.py
import fairdm

fairdm.setup(
    apps=["my_portal_app"],
    addons=["fairdm_discussions"],
)

# Layer 5 — assignment after the call, always wins
TIME_ZONE = "Europe/London"

INSTALLED_APPS = INSTALLED_APPS + ["my_other_app"]
LOGGING["loggers"]["my_app"] = {"handlers": ["console"], "level": "INFO"}
```

### The portal's own override module

A portal supplies its own layer-4 override by adding a module named after the environment, **beside its settings module** — for the recommended layout that's `config/<environment>.py`:

```
config/
├── settings.py       # calls fairdm.setup()
├── development.py    # applied when DJANGO_ENV=development
└── production.py     # applied when DJANGO_ENV=production
```

```python
# config/production.py — applied as layer 4, before assignments in settings.py
#
# Do not call fairdm.setup() here — this module runs inside the caller's
# already-in-progress setup() call, sharing its scope.

LANGUAGES = [
    ("en", "English"),
    ("de", "German"),
]
```

The lookup is anchored to the settings module's own directory, not to a hardcoded `config/` path — a portal laid out differently (for instance, a settings module living in a package named after the project, as `django-admin startproject` produces) still gets its override module found. The documentation and the recommended project structure always use `config/`, because that's what new portals should use; the mechanism itself does not require it.

If your settings module has no resolvable file on disk (for example, one generated at runtime or imported from an archive), this layer is skipped with a warning rather than failing.

If FairDM and the portal both ship an override module for the same resolved environment, both apply — FairDM's first, the portal's second, so the portal's values win on any setting both name.

## Environment Files

`fairdm.setup()` reads environment files in this order, before composing any settings layer:

1. `stack.env` — read first, respecting variables already set in the process environment.
2. `stack.<environment>.env` — read next, also respecting variables already set.
3. An explicit `env_file=` argument, if given — read last, and **does** overwrite variables already set, including by the two files above.

```python
fairdm.setup(env_file="/path/to/custom.env")
```

## Overriding a FairDM Default

Assignment after the `setup()` call is the only supported way to override a setting FairDM owns:

```python
import fairdm

fairdm.setup()

# Scalars
TIME_ZONE = "Europe/London"

# Lists — extend, don't replace, unless you mean to
INSTALLED_APPS = INSTALLED_APPS + ["my_portal_app"]

# Dicts
LOGGING["loggers"]["my_app"] = {"handlers": ["console"], "level": "DEBUG"}
```

`fairdm.setup()` does not accept settings as keyword arguments — passing one raises `TypeError`.

## Addon Integration

Addons are FairDM extensions that provide additional functionality. They inject settings, apps, and middleware as layer 3, before the portal's own override module and before any post-call assignment — so a portal can always override what an addon set.

### Using Addons

```python
import fairdm

fairdm.setup(
    addons=[
        "fairdm_discussions",
        "fairdm_publications",
    ]
)
```

### Creating an Addon

To make your package a FairDM addon:

1. Create a setup module (e.g. `my_addon/fdm_setup.py`):

```python
# my_addon/fdm_setup.py

INSTALLED_APPS = INSTALLED_APPS + ["my_addon"]  # noqa: F821
MIDDLEWARE = MIDDLEWARE + ["my_addon.middleware.MyMiddleware"]  # noqa: F821

MY_ADDON_SETTING = "value"
```

2. Register the setup module in your package's `__init__.py`:

```python
# my_addon/__init__.py

__fdm_setup_module__ = "my_addon.fdm_setup"
```

3. Enable it in the portal:

```python
fairdm.setup(addons=["my_addon"])
```

An addon that cannot be loaded prevents startup in production, naming the addon; in any other environment it logs a warning and is skipped.

## Refusing to Start in Production

When the resolved environment is `production`, FairDM runs its production-critical configuration checks and prevents startup if any fails — reporting every failure in one message, not just the first. In any other environment these checks do not run and nothing is emitted about them.

The full check set stays available on demand, and always assesses configuration against production standards regardless of the current environment:

```bash
python manage.py check --deploy
```

See {doc}`/portal-administration/configuration-checks` for the check catalogue and what each one requires.

## Interrogating the Resolved Configuration

Because a layer that finds no override module is skipped silently, FairDM provides a way to ask what actually happened: which layers were considered, which were found, and — for a given setting — which layer produced its final value. Consult {doc}`/portal-administration/configuration-checks` for the current command and its output format.

## Troubleshooting

### "SECRET_KEY is not set or is empty"

```bash
export DJANGO_SECRET_KEY="$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')"
```

### "DATABASES['default'] is not configured"

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/dbname"
```

Or rely on the development fallback:

```bash
export DJANGO_ENV=development  # falls back to SQLite
```

### "ALLOWED_HOSTS is empty"

```bash
export DJANGO_ALLOWED_HOSTS="example.com,www.example.com"
```

### My override module isn't being applied

- Check the file is named exactly after the resolved environment: `DJANGO_ENV=development` looks for `development.py`, not `dev.py` or `Development.py` — the lookup is literal, not normalised.
- Check the file sits directly beside your settings module, not in a subdirectory.
- Check `DJANGO_ENV` is actually set to what you expect: `python -c "import os; print(os.environ.get('DJANGO_ENV', 'production'))"`.

## Examples

### Minimal Development Setup

```python
# config/settings.py
import fairdm

fairdm.setup()
```

```bash
export DJANGO_ENV=development
```

### Production Setup

```bash
# stack.production.env
DJANGO_SECRET_KEY="your-secret-key"
DJANGO_ALLOWED_HOSTS="example.com"
DJANGO_SITE_DOMAIN="example.com"
DJANGO_SITE_NAME="My Portal"
DATABASE_URL="postgresql://user:pass@localhost/dbname"
REDIS_URL="redis://localhost:6379/0"
```

```python
# config/settings.py
import fairdm

fairdm.setup()
```

### Portal with Customisation

```python
# config/settings.py
import fairdm

fairdm.setup(
    addons=["fairdm_discussions"],
)

INSTALLED_APPS = INSTALLED_APPS + [
    "my_samples",
    "my_measurements",
]

TEMPLATES[0]["DIRS"].insert(0, BASE_DIR / "templates")
```

```python
# config/production.py — layer 4, applied before the assignments above
LANGUAGES = [("en", "English"), ("de", "German")]
```

## See Also

- {doc}`/portal-administration/configuration-checks` - production-critical checks and the deployment check command
- {doc}`/developer-guide/production` - Docker deployment guide
- {doc}`/developer-guide/setting_up` - Initial portal setup
- {doc}`/contributing/testing` - Testing your configuration
