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

## D4. The start sequence is the one portals run today, without compression

The GHFDB portal starts with migrate, collectstatic, compress, then gunicorn. The setup pipeline
configured through `django-setup-tools` lists different steps (`preload`, `sync_site_id`) and is
never called (#193). Choosing between the two belongs to #193. The image takes the sequence that
is known to run a portal in production.

**Reopen when** #193 settles the sequence.

## D5. amd64 only

The deployed portal and the people developing on FairDM today all run on amd64. Building for arm64
doubles the build and is not needed by anyone yet.

**Reopen when** a portal or a contributor needs arm64.

## D6. v0.1.0 gets no images

A workflow run on a tag uses the workflow and the Dockerfile at that tag, and v0.1.0 has neither.
Building v0.1.0's images from a later tree would label an image with a release it was not built
from. The first images are published by the first release that carries this feature, so the
example Dockerfile carries no default version.

**Reopen if** a portal needs an image for v0.1.0 before the next release.

## D7. Publishing completes a partial set instead of refusing it

The design review found that refusing to publish when either tag exists leaves a release with one
image for good if the second push fails. Publishing pushes only the tags that are missing and
leaves existing ones alone, which keeps every published tag fixed and lets a rerun finish the
pair. A concurrency group stops two runs on the same tag from racing.

## D8. The demo stops overriding its environment's compression settings

`config/settings.py` set `COMPRESS_ENABLED = True` and `COMPRESS_OFFLINE = False` after
`fairdm.setup()`, from the repository's first commit. With them the start sequence's `compress`
refuses to run, so the example Dockerfile could not build a working demo. Both lines go and the
framework's per-environment values apply.

## D9. Design review watch items

From the design review, carried into the briefs rather than re-planned:

- name each environment variable passed to `docker run`; docker does not expand `POSTGRES_*`
- requests in the smoke test send `X-Forwarded-Proto: https`
- `docker buildx imagetools inspect` exits non-zero on errors as well as on absence
- the runtime image's `COPY --chown` makes portal code writable by the server; FR-004 does not
  require otherwise, so it stays as planned
- the matrix's Python version no longer selects Python inside the image; it stays at 3.13, which
  the image provides

## D10. The smoke test asks the container for its own pages

**Decision.** `docker/smoke-test.sh` requests `/` with `docker exec` and Python's standard library,
inside the portal container, and passes the database and Redis hosts in by environment variable.
It publishes no port.

**Why.** Docker Desktop does not give containers the host's network, and a CI runner does. A
request made from inside works the same on both, and the image already has Python. Only the
database and Redis hosts differ between the two places, so those are the script's only
network inputs.

**Revisit if.** A check needs to reach the container from outside, for instance through a proxy.

## D11. FairDM stops depending on django-compressor

The `compress` step failed on the demo with `No 'compress' template tags found in templates`. No
template in FairDM, the demo, the django-mvp packages or the GHFDB portal uses `{% compress %}`, and
`COMPRESS_OFFLINE` is on in production, so the step could never succeed. Asked during the build,
the maintainer decided to remove django-compressor and the `compress` step. django-libsass goes
with it, because its only use was as compressor's SCSS precompiler. The start sequence is migrate,
collectstatic, the portal's steps, then gunicorn. This amends FR-005 and adds FR-020, approved by
the maintainer in the session on 2026-10-16.

**Reopen if** a portal needs offline compression back, in which case it belongs to that portal.

## D12. The smoke test copies its start step into the container

**Decision.** `docker/smoke-test.sh` creates the web container, copies the start step into
`/docker-entrypoint.d` with `docker cp`, then starts it. It does not bind-mount the step.

**Why.** Docker Desktop with `docker.exe` receives an empty directory when a WSL path is bind-mounted
by `docker run --volume`, so the step never ran locally. Copying works the same on Docker Desktop
and on a CI runner. The step logs a line to stderr, the same stream as gunicorn, so the script can
compare their order in the container log.

**Revisit if.** The script only ever runs on Linux runners and a mount reads more simply.

## D13. In the compose stack the worker waits for the web service to be healthy

**Decision.** `django` has a healthcheck that requests the home page, and `celeryworker` depends on it
being healthy. Both still run `uv sync --locked`, as the plan says.

**Why.** Both services mount the same `venv` volume. Started together, the two installs raced: the web
service failed with "failed to remove directory /opt/venv: Permission denied" and the worker started
without a `celery` executable. With the worker waiting, its `uv sync` finds the environment complete
and returns at once.

**Revisit if.** The development image ships an environment of its own, which would make the first
`uv sync` unnecessary.

## D14. publish.sh asks about both tags before it pushes either

**Decision.** `docker/publish.sh VERSION [REPOSITORY]` runs `docker buildx imagetools inspect` on
`<version>` and `<version>-dev` first, and only then tags and pushes whichever is missing. The local
images come from `RUNTIME_IMAGE` and `DEVELOPMENT_IMAGE` (defaults `fairdm-base:ci` and
`fairdm-base:ci-dev`, the names image.yml builds), the docker command from `DOCKER`.

**Why.** Plan P6 says an authentication or network error stops the script before anything is
pushed. Checking and pushing one tag at a time would push the first tag and then stop on an error
asking about the second. Environment variables for the image names keep the argument list the plan
gives, and match how smoke-test.sh takes `DOCKER`.

**Revisit if.** A third image joins the release, which would make a loop over images worth its lines.

## D15. The demo portal is built with the engine's own builder

**Decision.** In image.yml the runtime and development images are built with
`docker/build-push-action` (container builder, GitHub Actions cache, `load: true`), and the portal
with `docker buildx build --builder default --load`.

**Why.** The portal Dockerfile starts `FROM fairdm-base:ci-dev`, an image that exists only in the
engine's image store. A container builder cannot see that store: a probe with `FROM fairdm-dev:ci`
failed with "pull access denied", and the engine's builder built it. The portal build needs no cache.

**Revisit if.** The runner's builder is not named `default`, which the first run on a runner shows,
or the images are pushed to a registry before the portal is built.

## D16. publish.sh has tests, and they sit in tests/test_docker

**Decision.** `tests/test_docker/test_publish.py` runs the script with a stand-in `docker` command
and checks which pushes it makes: both tags, one tag, none, and none when the registry cannot be
asked. The brief's scope list names no test directory.

**Why.** Skipping a published tag and pushing nothing on an error are the script's contract, and a
registry run in the brief's evidence shows them once. The tests keep showing them. The directory
is declared in `[tool.forge.conformance] non-mirror-paths`.

**Revisit if.** The reviewer would rather the script's evidence stay a one-time run.
