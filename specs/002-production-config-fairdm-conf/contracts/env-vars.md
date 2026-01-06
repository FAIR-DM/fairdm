# Contract: Environment Variables (fairdm.conf)

**Feature**: specs/002-production-config-fairdm-conf/spec.md  
**Date**: 2026-01-02

This contract defines the supported environment variables for configuring a FairDM portal via `fairdm.conf`.

**Source of truth**: `fairdm/conf/environment.py` (django-environ `Env(...)` schema)

## Required in production

These must be set for a secure and functional production deployment:

- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`

At least one database configuration strategy:

- `DATABASE_URL` (preferred when available), OR
- `POSTGRES_HOST` + `POSTGRES_PORT` + `POSTGRES_DB` + `POSTGRES_USER` + `POSTGRES_PASSWORD`

Cache/broker:

- `REDIS_URL`

## Commonly configured

- `DJANGO_SITE_DOMAIN`
- `DJANGO_SITE_NAME`
- `DJANGO_TIME_ZONE`
- `DJANGO_SECURE` and `DJANGO_SECURE_HSTS_SECONDS`
- Email settings: `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_BACKEND`

## Development / local convenience

- `DJANGO_DEBUG`
- `SHOW_DEBUG_TOOLBAR`
- `USE_DOCKER`

## Notes

- Secrets are provided via environment variables only.
- For local dev, defaults may exist to reduce friction, but production documentation should treat security-critical values as required.
