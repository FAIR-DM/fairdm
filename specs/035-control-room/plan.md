# Implementation Plan: An operations control room in the administration interface

**Branch**: `035-control-room` | **Date**: 2026-11-08 | **Spec**: [spec.md](spec.md) |
**Research**: [research.md](research.md)

## Summary

FairDM depends on Django Control Room with its Redis, cache and Celery panels. The URL and signal
panels go in FairDM's own development dependency group and are turned on by the development
settings wherever they are installed. A new
baseline settings module, `fairdm/conf/settings/control_room.py`, installs the hub and the three
operational panels and writes each package's settings dict with `REQUIRE_SUPERUSER: True`. It
points the Redis panel at `REDIS_URL` with editing left off, and turns off the URL panel's test
requests. `fairdm/conf/development.py` adds the URL and signal panels. `fairdm/contrib/admin/urls.py`
mounts every installed panel's routes under `ADMIN_URL`, ahead of the admin's own routes. The
documentation gains an administrators' how-to for the dashboard, a developers' how-to for
changing who can open it or removing it, and settings reference entries.

## Technical Context

**Language/Version**: Python 3.13, Django 6.0
**Primary Dependencies**: new runtime: `dj-control-room[redis,cache,celery]` (pulls in
`dj-control-room-base` and the three panels). New development group: `dj-urls-panel`,
`dj-signals-panel`. Present: `redis`, `celery`, `django-redis`.
**Storage**: the packages ship placeholder models for their admin entries and migrations of their
own. FairDM adds no model and no migration.
**Testing**: pytest through the shared development container
(`~/.openclaw/devserver/fairdm-shared-test.sh <worktree> suite`)

## Constitution Check

- **Article VII, dependency discipline.** One new runtime dependency, justified in
  [research.md](research.md): it is the whole feature, and nothing in the stack does it. The
  packages are named only in settings strings, so they join the existing deptry ignore list for
  packages referenced that way.
- **Article XIV, production-grade defaults.** Superuser-only access, read-only Redis, no
  outbound requests and the agent interface off are the defaults. The feature needs no
  configuration to work.
- **Core versus addon.** The constitution leaves advanced dashboards to addons. This one is about
  running the portal, not its data, serves G16, and is placed in core by the maintainer's
  decision. Recorded in [decisions.md](decisions.md).
- Every public name is documented in the story that adds it. Line length 88. No leading-underscore
  names.

## Design

### Settings (US1)

`fairdm/conf/settings/control_room.py`, added to `settings_modules` in `fairdm/conf/setup.py`
after `settings/celery.py`:

- Appends to `INSTALLED_APPS`, in the order the package requires: `dj_control_room_base`,
  `dj_redis_panel`, `dj_cache_panel`, `dj_celery_panel`, `dj_control_room`. The hub comes after
  its panels.
- Writes these dicts, each with `"REQUIRE_SUPERUSER": True`:
  - `DJ_CONTROL_ROOM_SETTINGS`
  - `DJ_CONTROL_ROOM_BASE_SETTINGS`
  - `DJ_REDIS_PANEL_SETTINGS`, which also has
    `"INSTANCES": {"default": {"url": <REDIS_URL or the unconfigured placeholder>}}`, the same
    location the cache uses. No `features` key, so editing, deleting and expiry changes stay at
    their default of off.
  - `DJ_CACHE_PANEL_SETTINGS`
  - `DJ_CELERY_PANEL_SETTINGS`
  - `DJ_URLS_PANEL_SETTINGS`, which also has `"ENABLE_TESTING": False`
  - `DJ_SIGNALS_PANEL_SETTINGS`
- The URL and signal dicts are written in the baseline even though their apps are installed only
  in development. A dict for an app that is not installed is never read, and keeping all seven in
  one module keeps the access rule in one place.
- Nothing sets `MCP_ENABLED`.

`fairdm/conf/development.py`: inserts each of `dj_urls_panel` and `dj_signals_panel` into
`INSTALLED_APPS` immediately before `dj_control_room` when `importlib.util.find_spec` finds it,
the pattern already used for `django_browser_reload`. They are never runtime dependencies: the hub
discovers panels from installed distributions' entry points, not from `INSTALLED_APPS`, and lists
an installed, unmounted panel in the admin sidebar with a link that fails.

A portal overrides any of these by assigning its own value after `setup()`, as for every other
setting. A portal removes the dashboard by removing the five or seven app names from
`INSTALLED_APPS`.

### Routes (US1, US2)

`fairdm/contrib/admin/urls.py`: before the admin's own pattern, for each of
`dj_redis_panel`, `dj_cache_panel`, `dj_celery_panel`, `dj_urls_panel`, `dj_signals_panel` and
`dj_control_room` that `django.apps.apps.is_installed()` reports, a pattern
`f"{ADMIN_URL}<prefix>/"` including that app's `urls` module, with the prefix the package
documents (`dj-redis-panel`, …, `dj-control-room`). An app that is not installed gets no pattern,
so production answers 404 for the URL and signal panels (FR-011) and a portal that removes the
hub loses its routes with it (FR-009). One loop over a tuple of `(app label, prefix, urls module)`;
no helper module.

### What is not built

- No view, template, model, permission check or theme adapter of FairDM's own.
- No change to `CustomAdminSite`: the panels' own permission check refuses everyone the spec
  refuses, independently of the site's check (research finding 3).

### Tests (US1)

`tests/test_conf/test_settings/test_control_room.py` and
`tests/test_contrib/test_admin/test_control_room.py`:

- Settings: each of the seven dicts has `REQUIRE_SUPERUSER` true; the Redis instance URL equals
  the cache location; no Redis `features`; `ENABLE_TESTING` false; no `MCP_ENABLED` true; a
  portal module that assigns its own `DJ_REDIS_PANEL_SETTINGS` after `setup()` keeps its value.
- Access, through the test client, on the dashboard and every panel's index route: a superuser
  gets 200; a staff non-superuser and a holder of each rights-carrying portal role get 403; an
  anonymous visitor is redirected to the admin sign-in. The admin index shows a superuser the
  control-room entries and shows the others none.
- Under another `ADMIN_URL`, the dashboard reverses and answers under it.
- With Redis unreachable (a URL pointing at a closed port) the Redis and cache panel pages answer
  200, and the Celery panel answers 200 with no worker.
- The agent interface answers 404.
- A settings module without the five apps boots and the admin index answers 200, with no
  dashboard route.

### Tests (US2)

- Development settings install the two panels before the hub; production (`DJANGO_ENV=qa`)
  settings do not.
- With development settings a superuser opens both panels and a staff non-superuser gets 403.
- With the apps absent, both panel addresses answer 404 (built with an override of
  `INSTALLED_APPS` and a fresh URL conf).

### Documentation

- `docs/administrators/how-to/check-the-portals-services-in-the-control-room.md` (US1): what the
  dashboard shows, who can open it, and that the Redis panel is read-only. Linked from
  `docs/administrators/index.md`.
- `docs/developers/how-to/change-who-can-open-the-control-room.md` (US1): changing access through
  the package settings, turning on Redis editing, removing the dashboard, and what turning on the
  agent interface exposes. Linked from `docs/developers/index.md`. US2 adds a section on the
  development-only panels.
- `docs/developers/reference/settings.md`: one entry per new setting, in a new "Operations
  dashboard" section.
- `docs/explanation/the-technology-stack.md`: one line for Django Control Room.
- `CHANGELOG.md` under `[Unreleased]`.

## Risks

- **The hub lists every installed panel.** Any panel package a portal installs appears on its
  dashboard. The documentation says so.
- **A young dependency.** Pinned with a lower bound at the current release and an upper bound at
  the next major. A panel that breaks is removed on its own.
- **The panels' templates extend the stock admin.** FairDM's admin is the stock admin with its own
  `base_site.html`, so they render inside it. Rendering is checked through the test client and at
  the walkthrough.
