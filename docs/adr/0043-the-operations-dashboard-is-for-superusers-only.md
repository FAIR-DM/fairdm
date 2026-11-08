# ADR 0043 — The operations dashboard is for superusers only

**Status:** accepted

## Decision

Every portal ships Django Control Room's dashboard with its Redis, cache and Celery panels, inside
the administration interface. FairDM sets `REQUIRE_SUPERUSER` in each control-room package's own
settings, so only active superusers can open the dashboard or any panel. The Redis panel is left
read-only. The URL panel's request testing and the agent interface are off. The URL and signal
panels are development dependencies, never runtime ones.

## Why

The administration interface admits holders of a rights-carrying portal role as well as staff.
Those people curate records and manage contributors. The panels reach the portal's
infrastructure instead: the cache panel can change and clear entries, and the Celery panel shows
the arguments each task was called with, which can hold personal data. They stay with the accounts
that already control everything else in the portal.

The dashboard finds panels from the packages installed in the environment, not from the apps a
portal turns on. A panel package installed in production but not turned on still appears in the
administration index with a link that fails, so the URL and signal panels, which describe the code
rather than the running portal, are kept out of production installs altogether.

## Revisit if

Portals need operators who are not superusers, or the package registers panels from
`INSTALLED_APPS` rather than from installed distributions.
