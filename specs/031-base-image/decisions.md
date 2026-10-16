# Decisions: publish a FairDM base image that portals build their containers on

Questions the specification settled, with the reasoning that is too long for the specification
itself. Each says what would reopen it.

## D1. The images do not contain FairDM

A portal installs FairDM through its own lock file. The GHFDB portal pins FairDM, fairdm-geo and
fairdm-discussions to git commits through `[tool.uv.sources]`. If the image installed FairDM, its
copy would either be replaced by the portal's on every build, or would fight it. Leaving FairDM out
makes the image a statement about FairDM's system requirements only, which is the part every
portal currently repeats.

**Reopen if** FairDM is published to a package index and portals stop pinning it from git.

## D2. Tags follow releases, not commits

The maintainer's choice, given at agreement: once GitHub releases run (#525), portals pin FairDM to
a release, and the image should carry the same number. A portal then moves FairDM and its image
with one decision.

No tag moves once published, and there is no `latest`. The image last published as
`ghcr.io/fair-dm/fairdm:latest` stopped being updated when its repository was archived. Portals
building on it broke without warning, because a moving tag gives no signal when it stops moving.

**Reopen if** releases stay rare enough that portals keep needing unreleased commits.

## D3. A production portal uses both images

Portals install FairDM and its addons from git, and some of their dependencies compile. Installing
them needs git and build tools, which have no place in a production container. The development
image carries them, so it serves as the stage where a portal installs its dependencies, as well as
the local development image. The runtime image carries only what FairDM needs to run.

## D4. The start sequence is the one portals run today

The GHFDB portal starts with migrate, collectstatic, compress, then gunicorn. The setup pipeline
configured through `django-setup-tools` lists different steps (`preload`, `sync_site_id`) and is
never called (#193). Choosing between the two belongs to #193. The image takes the sequence that
is known to run a portal in production.

**Reopen when** #193 settles the sequence.

## D5. amd64 only

The deployed portal and the people developing on FairDM today all run on amd64. Building for arm64
doubles the build and is not needed by anyone yet.

**Reopen when** a portal or a contributor needs arm64.
