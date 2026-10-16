# ADR 0035 — FairDM does not compress static files

**Status:** accepted

## Decision

FairDM does not depend on django-compressor or django-libsass, and its settings carry no
compression configuration. Static files are collected with `collectstatic` and served by
WhiteNoise. A portal that wants `{% compress %}` installs django-compressor itself, adds it to
`INSTALLED_APPS`, and adds `python manage.py compress` to its own start steps.

## Why

No template in FairDM, its demo, the django-mvp packages or the deployed GHFDB portal used
`{% compress %}`. With offline compression on in production, `manage.py compress` stops with an
error when it finds no such tag, so a start sequence that ran it could never succeed. django-libsass
was installed only as compressor's SCSS precompiler. Keeping two dependencies and a start step
that do nothing, or fail, costs every portal and helps none.

## Revisit if

FairDM's own templates need bundling or minification that WhiteNoise and the django-mvp
stylesheets do not provide.
