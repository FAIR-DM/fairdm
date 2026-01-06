# Quickstart: Production-Ready Configuration via fairdm.conf

**Feature**: specs/002-production-config-fairdm-conf/spec.md  
**Date**: 2026-01-02

This quickstart is for portal developers who want a production-ready baseline without managing a large settings surface.

## 1) Create your project settings module

In your project’s settings file (e.g. `config/settings.py`), call `fairdm.setup(...)` first:

```python
import fairdm

fairdm.setup(
    apps=[
        "my_portal_app",  # your domain app(s)
    ],
    addons=[
        # optional addons by package name
        # "fairdm_discussions",
    ],
)

# Project-owned overrides (minimal, optional)
# e.g. site copy/branding
SITE_NAME = "My Portal"
```

## 2) Select environment with `DJANGO_ENV`

Set `DJANGO_ENV` to one of:

- `production`
- `staging`
- `development`

FairDM selects the environment profile inside `fairdm.setup()`.

## 3) Provide environment variables (secrets via env vars only)

Create environment files or set env vars via your hosting platform.

Typical pattern:

- `stack.env` (shared defaults)
- `stack.development.env` (development-only overrides)

At minimum, production should provide:

- `DJANGO_SECRET_KEY`
- database connection (e.g., `DATABASE_URL` or component database vars)
- cache/broker connection (e.g., `REDIS_URL`)
- `DJANGO_ALLOWED_HOSTS`

See `contracts/env-vars.md` for the current reference list.

## 4) Run the portal

- Web server: `gunicorn config.wsgi` (or equivalent)
- Background workers (if enabled by baseline): run the configured Celery worker and scheduler processes

## 5) Enable an addon

Add the addon package to your environment and include it in `fairdm.setup(addons=[...])`.

Addons should:

- expose a settings setup module via `__fdm_setup_module__`
- optionally provide a `<addon>.urls` module for automatic URL inclusion

See `contracts/python-api.md` for the addon contract.
