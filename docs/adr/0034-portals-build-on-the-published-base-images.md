# ADR 0034 — Portals build on the base images FairDM publishes

**Status:** accepted

## Decision

FairDM publishes two container images to `ghcr.io/fair-dm/fairdm` from `docker/Dockerfile`:

- the runtime image, tagged with the release version without its `v` (`0.2.0`)
- the development image, tagged with the same version and `-dev` (`0.2.0-dev`)

Neither image contains FairDM or any portal code. A portal installs its own locked dependencies,
FairDM included, on the development image and runs on the runtime image. The runtime image
starts a portal with `docker/entrypoint.sh`. The default `web` command applies migrations,
collects static files, runs the executable files in `/docker-entrypoint.d/` in name order, then
starts gunicorn. `worker` starts Celery.

Images are published only for releases. A published tag is never moved and there is no `latest`
tag. A release whose publishing stopped part way is completed by running the image workflow
again, which pushes only the tags that are missing.

## Why

FairDM's system requirements, PostGIS and the GDAL, GEOS and PROJ libraries since ADR 0031, are
needed wherever Django starts. Each portal used to write its own image, and found out about a
new requirement only when something broke. The GHFDB portal's production image still installed
no GDAL after FairDM started needing it. The requirements now change in the same pull request as
the code that needs them, and FairDM's own suite runs in the development image, so a change that
breaks the image fails at review.

The images carry no FairDM because portals pin FairDM and its addons in their own lock files,
often to git sources. An image that installed FairDM would either be overwritten by the portal's
copy or conflict with it.

Tags follow releases so that moving a portal's FairDM version and moving its image are the same
decision. The image FairDM once published as `latest` from a separate repository stopped being
updated when that repository was archived, and a portal built on it broke with no warning.

## Revisit if

Portals need images for commits between releases, or FairDM is published to a package index and
portals stop pinning it from git.
