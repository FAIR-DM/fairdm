# ADR 0034 — Portals build on the base images FairDM publishes

**Status:** accepted

## Decision

FairDM publishes two container images to `ghcr.io/fair-dm/fairdm` from `docker/Dockerfile`:

- the runtime image, tagged with the image version (`1.0.0`)
- the development image, tagged with the same version and `-dev` (`1.0.0-dev`)

Neither image contains FairDM or any portal code. A portal installs its own locked dependencies,
FairDM included, on the development image and runs on the runtime image. The runtime image
starts a portal with `docker/entrypoint.sh`. The default `web` command applies migrations,
collects static files, runs the executable files in `/docker-entrypoint.d/` in name order, then
starts gunicorn. `worker` starts Celery.

The images have a semantic version of their own, separate from FairDM's. A maintainer releases a
new version with the Image Release workflow, started from the Actions tab with a patch, minor or
major bump. It publishes both tags and creates an `image-v<version>` tag and GitHub release. A
published tag is never moved and there is no `latest` tag. A release that stopped part way is
completed by running the workflow again, which pushes only the tags that are missing. FairDM's
changelog says when a FairDM release needs a newer image.

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

The images change only when the Python version, the system libraries, uv or the start sequence
changes, which is a few times a year, while FairDM releases far more often. Tagging them by FairDM
release would publish the same image again under every new number, and an image could only pick
up security updates when FairDM happened to release. A version of their own means a new tag only
when the image changes, and a patch release for security updates at any time. It also leaves a
portal that pins FairDM to a commit free to use the newest image.

No tag moves because the image FairDM once published as `latest` from a separate repository
stopped being updated when that repository was archived, and a portal built on it broke with no
warning.

## Revisit if

FairDM's system requirements start changing with most of its releases, which would make a
separate version a second number to keep in step, or FairDM is published to a package index and
portals stop pinning it from git.
