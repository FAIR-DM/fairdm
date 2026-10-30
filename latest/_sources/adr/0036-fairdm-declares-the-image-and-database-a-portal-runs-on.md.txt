# ADR 0036 — FairDM declares the image and database a portal runs on

**Status:** accepted

## Decision

FairDM records, in its `pyproject.toml`, the base image version and the PostGIS version it is
tested on:

```toml
[tool.fairdm.platform]
image = "1.0.0"
postgis = "17-3.5"
```

`image` is a version of the base images ([ADR 0034](0034-portals-build-on-the-published-base-images.md)).
`postgis` is a tag of the `postgis/postgis` image. A portal runs on the versions declared by the
FairDM it installs, read at the release or commit it pins: its tests, its production image and its
database. When a portal moves to a newer FairDM, its image and its database move in the same
change.

FairDM's `Test suite` and `Image` workflows read the PostGIS tag from the table, so it is the
database FairDM is actually tested against. `image` is raised in the pull request that follows an
image release.

## Why

A portal that chose its own image and database could drift from what FairDM was tested on, and
find out only when something broke in production. With the versions in FairDM itself, choosing a
FairDM version chooses the rest, and a tool can read them from a portal's lock file with nothing
for the portal to keep in step.

The table lives in `pyproject.toml` because that file exists at every release and every commit a
portal can pin, and any workflow can read it with Python's standard library.

## Revisit if

Portals need to run on a database or image FairDM was not tested on, or FairDM is installed in a
way that leaves no `pyproject.toml` to read at the pinned version.
