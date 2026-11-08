# Research: an operations control room in the administration interface

Read against `origin/main` at `0b194ab0` and the published packages at these versions:
dj-control-room 1.8.1, dj-control-room-base 1.6.0, dj-redis-panel 0.10.0, dj-cache-panel 0.6.0,
dj-celery-panel 0.6.0, dj-urls-panel 0.5.0, dj-signals-panel 0.6.0.

## Planning notes

### Use Django Control Room

**Adopted.** It covers the three services every portal runs. It is MIT licensed and declares
support for Django 6.0 and Python 3.9 and later. Its only new dependency is the panel packages
themselves (each needs Django and `dj-control-room-base`, the Redis panel needs `redis`, which
FairDM already installs, and the URL panel needs `requests`). It is self-hosted, and it makes no
request to any outside service except the URL panel's test feature, which FairDM turns off
(below). The project is young (first release February 2026) and mostly the work of one
maintainer. Each panel is a separate small package, so a panel that stops being maintained can be
removed on its own.

## Assumptions checked

- **All six packages declare Django 6.0 support.** Read from their published metadata
  (`Framework :: Django :: 6.0`). The suite run in the first task confirms that they import and
  their pages render under FairDM.
- **The panels render inside FairDM's administration site.** Every panel builds its page context
  from `django.contrib.admin.site.each_context()`. FairDM replaces the default site with
  `CustomAdminSite` through `FairDMAdminSite.default_site`, so `admin.site` is FairDM's own site and
  its header and portal name appear on the panel pages.
- **The panels' admin sidebar entries follow the same permission check as their pages.**
  `BasePanelAdmin.has_module_permission` and `has_view_permission` call the panel's own permission
  check, so an account refused a panel is not shown its entry in the administration index.

## Findings that shape the plan

1. **Each panel reads its own access settings.** `PanelConfig` merges, in order: built-in defaults,
   the panel's own defaults, an override the hub may apply, and the project's
   `DJ_<PANEL>_SETTINGS` dict. The hub's `DJ_CONTROL_ROOM_SETTINGS` governs only the hub's own
   pages. Superuser-only access therefore needs `REQUIRE_SUPERUSER: True` in seven dicts:
   `DJ_CONTROL_ROOM_SETTINGS`, `DJ_CONTROL_ROOM_BASE_SETTINGS` (the base package registers an
   admin entry of its own) and one per panel.
2. **The permission check also requires staff.** `_check_permission` refuses any account without
   `is_staff` before it looks at `is_superuser`. A superuser made by `createsuperuser` is staff, so
   this holds in practice. A superuser with `is_staff` cleared is refused, which is stricter than
   the spec and acceptable. The documentation says so.
3. **FairDM's administration site admits more than staff.** `CustomAdminSite.has_permission` admits
   holders of a rights-carrying portal role who are not staff. The panels' own check refuses them
   (finding 2), so the dashboard does not rely on the site's check.
4. **Panel URLs must sit under `ADMIN_URL`, ahead of `admin.site.urls`.** The admin's catch-all
   would otherwise answer them. FairDM mounts the admin in `fairdm/contrib/admin/urls.py`, which is
   the place for them.
5. **The Redis panel needs its instance named.** It reads `INSTANCES` from
   `DJ_REDIS_PANEL_SETTINGS` and has no default. FairDM points it at `REDIS_URL`. Key editing,
   deletion and expiry changes are per-instance features that default to off, and FairDM leaves
   them off (FR-014).
6. **The URL panel's test feature sends real HTTP requests.** With `ENABLE_TESTING` on (its
   default) it sends a request to an address a user enters, with a blocklist for private ranges.
   That is a request leaving the portal, so FairDM sets `ENABLE_TESTING: False` (FR-013).
7. **The AI-agent interface is off by default** (`MCP_ENABLED: False`) and answers 404. FairDM sets
   nothing for it.
8. **The Celery panel reads from `celery.current_app`** and inspects workers over the broker. With
   no worker it reports none. FairDM's Celery app is configured in `fairdm/conf/celery.py`.
9. **Development-only apps follow an existing pattern.** `fairdm/conf/development.py` appends apps
   to `INSTALLED_APPS` when `DJANGO_ENV=development`. The URL and signal panels are installed
   packages in every portal and added to `INSTALLED_APPS` only there. Their URL routes are mounted
   only when the app is installed (`django.apps.apps.is_installed`), so production answers 404.
10. **The hub discovers panels through entry points and lists official panels that are not
    installed** as cards with an install guide. A production dashboard may therefore show the URL
    and signal panels as available to install. That card opens nothing in the portal, which is
    what FR-011 asks.
11. **A portal's settings win by assignment.** FairDM's settings are applied by `setup()`, and a
    portal's settings module assigns its own values afterwards, as for every other FairDM setting
    (FR-008).

## What already exists

| Piece | Where the search stopped |
|---|---|
| Dashboard, panels, permission checks, sidebar entries | A maintained package: Django Control Room |
| Superuser-only rule | The package's `REQUIRE_SUPERUSER` setting. Nothing new |
| Read-only Redis | The package's per-instance features, left at their default. Nothing new |
| Development-only apps | This repo: the pattern in `fairdm/conf/development.py` |
| Mounting routes under the admin address | This repo: `fairdm/contrib/admin/urls.py` and `ADMIN_URL` |
| Settings documentation | This repo: `docs/developers/reference/settings.md` |
| Tests for the admin's permission split | This repo: the factories and fixtures used by the existing admin tests |
