# Implementation Plan: publish a FairDM base image that portals build their containers on

**Branch**: `031-base-image` | **Date**: 2026-10-16 | **Spec**: [spec.md](spec.md)

**Input**: [spec.md](spec.md), [research.md](research.md), [decisions.md](decisions.md),
[planning-notes.md](planning-notes.md)

## Summary

One Dockerfile, `docker/Dockerfile`, with a `runtime` target and a `development` target built on
it. A shell entrypoint runs the start sequence, the portal's own start steps, a Celery worker, or
any other command. The example portal Dockerfile the deployment guide shows is a real file, and CI
builds FairDM's demo portal with it and checks the result. The test suite runs inside the
development image on every pull request. A new image workflow publishes both images on each
release under its version, and never moves a published tag.

## Technical context

- Python 3.13 on `python:3.13-slim` (Debian trixie), Debian's `gdal-bin` and `libpq5`, uv copied
  from `ghcr.io/astral-sh/uv`
- No new Python dependency. gunicorn and Celery are already FairDM dependencies
- CI actions: `docker/setup-buildx-action`, `docker/build-push-action`, `docker/login-action`
- Registry: `ghcr.io/fair-dm/fairdm`, amd64

## Constitution check

- **Article I.** The entrypoint's behaviour is tested first in the suite (research R7). What only
  a built image shows is checked by a script in CI (R8). Nothing pins wording.
- **Articles II and III.** One Dockerfile, one entrypoint script, and no option of the image's own
  where gunicorn or Celery already reads one from the environment (research, "What already
  exists").
- **Articles VI and XVI.** The deployment guide is rewritten in this pull request, and its example
  Dockerfile is the file CI builds.
- **Article VII.** No new runtime dependency.
- **Article XIV.** The deployment target becomes a published, reproducible container.

## Design

### P1. `docker/Dockerfile`

Research R1 to R3. Outline:

```dockerfile
FROM python:3.13-slim AS runtime
# gdal-bin, libpq5; fairdm user 1000; /app, /app/static, /app/media, /opt/venv owned by fairdm
# uv from ghcr.io/astral-sh/uv:<minor>; ENV UV_PROJECT_ENVIRONMENT=/opt/venv PATH=/opt/venv/bin:$PATH
#     UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PORT=8000
# COPY entrypoint.sh /usr/local/bin/fairdm-entrypoint; mkdir /docker-entrypoint.d
# WORKDIR /app; USER fairdm; EXPOSE 8000
ENTRYPOINT ["fairdm-entrypoint"]
CMD ["web"]

FROM runtime AS development
USER root
# build-essential, libpq-dev, git
USER fairdm
```

The build context is the repository root, and the Dockerfile copies only `docker/entrypoint.sh`.
OCI labels: `org.opencontainers.image.source` set to the repository URL, plus title, description,
licence and, from a build argument, version.

### P2. `docker/entrypoint.sh`

Research R4. POSIX `sh` with `set -eu`:

```sh
start_dir="${FAIRDM_START_DIR:-/docker-entrypoint.d}"
case "${1:-web}" in
  web)    python manage.py migrate --noinput
          python manage.py collectstatic --noinput
          python manage.py compress
          for step in "$start_dir"/*; do [ -f "$step" ] && [ -x "$step" ] && "$step"; done
          exec gunicorn "${WSGI_APP:-config.wsgi:application}" ;;
  worker) shift; exec celery --app "${CELERY_APP:-config}" worker "$@" ;;
  *)      exec "$@" ;;
esac
```

A step file that is not executable is skipped with a line on stderr naming it, so a missing
`--chmod` shows up in the log rather than as a silent no-op. A glob that matches nothing is
handled by the `-f` test.

### P3. `docker/portal.Dockerfile`, the example a portal copies

Research R6.

```dockerfile
ARG FAIRDM_IMAGE=ghcr.io/fair-dm/fairdm
ARG FAIRDM_VERSION=0.1.0
FROM ${FAIRDM_IMAGE}:${FAIRDM_VERSION}-dev AS build
COPY --chown=fairdm:fairdm pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev --no-install-project
COPY --chown=fairdm:fairdm . .
RUN uv sync --locked --no-dev --no-editable

FROM ${FAIRDM_IMAGE}:${FAIRDM_VERSION}
COPY --from=build /opt/venv /opt/venv
COPY --chown=fairdm:fairdm . /app
```

It installs no system package (SC-001). `FAIRDM_VERSION`'s default is the latest release, and
release preparation does not bump it: the guide tells a portal to set it to its own FairDM
version. CI overrides both arguments to point at the images just built.

### P4. FairDM's compose stack

Research R5. `django` and `celeryworker` build `docker/Dockerfile` with `target: development`,
mount the checkout at `/app` and a named volume `venv` at `/opt/venv`, and run:

- django: `sh -c "uv sync --locked && python manage.py migrate && python manage.py runserver 0.0.0.0:8000"`
- celeryworker: `sh -c "uv sync --locked && celery --app fairdm.conf.celery worker --loglevel INFO"`

Both run through the entrypoint's pass-through branch. `compose/django/Dockerfile` is deleted.

### P5. The test suite in the development image

Research R9. In `test-suite.yml`, replace "Install GDAL, GEOS and PROJ", "Install uv", "Sync
dependencies", "Pin Django version" and "Run tests" with:

1. `docker/setup-buildx-action`
2. `docker/build-push-action` with `target: development`, `load: true`, `push: false`,
   `tags: fairdm-dev:ci`, `cache-from/to: type=gha,scope=development`
3. one `docker run --rm --network host --user root -v "$PWD:/app" -e POSTGRES_* -e DJANGO_VERSION
   fairdm-dev:ci sh -c "uv sync --locked && uv pip install django~=$DJANGO_VERSION.0 && <version
   check> && pytest --cov=fairdm --cov-report=xml"`, with `UV_NO_SYNC=1` for any `uv run` after
   the pin, as today

The job name, the matrix and the Codecov step stay, so the required check keeps its name.

### P6. `.github/workflows/image.yml`

Research R10. One job, `Image`, `runs-on: ubuntu-latest`, `permissions: contents: read,
packages: write`, with a PostGIS service on 5432.

1. Build `runtime` and `development` from `docker/Dockerfile` (load, cached).
2. Build `docker/portal.Dockerfile` with `FAIRDM_IMAGE` and `FAIRDM_VERSION` pointing at them.
3. Run `docker/smoke-test.sh <portal image>`.
4. Only on a `refs/tags/v*` ref: compute `version=${GITHUB_REF_NAME#v}`, check with
   `docker buildx imagetools inspect` that neither `ghcr.io/fair-dm/fairdm:$version` nor
   `:$version-dev` exists (exit 1 if one does), log in with `GITHUB_TOKEN`, tag and push both.

Triggers: `pull_request`, `push` to `main`, `release: published`, `workflow_dispatch`. A dispatch
on a release tag publishes that release's images, which is how v0.1.0 gets them.

### P7. `docker/smoke-test.sh`

Research R8. Takes the portal image name. Uses `docker run` against the job's PostGIS service
through the host network. Each check prints one line, and the script exits non-zero on the first
failure. The settings the demo needs in production mode come from the environment the script
sets: a throwaway secret key, allowed hosts, the database, and whatever else the production
configuration checks require. The implementer reads them from `fairdm/conf/` and
`config/production.py` and lists them in the guide, since a portal needs the same.

### P8. Documentation

- `docs/portal-development/production.md` is rewritten as the guide to deploying a portal on the
  images: the two images and their tags, which image version goes with which FairDM version and
  what a portal pinned to a commit between releases uses (FR-019), the example Dockerfile by
  `literalinclude` of `docker/portal.Dockerfile`, start steps, the worker, the port and the
  environment variables, and the development image in a portal's own compose file (FR-018). The
  description of `compose/production/django` goes.
- Contributor pages that mention `compose/django/Dockerfile` or describe the compose stack
  (`docs/contributing/before_you_start.md`, `docs/contributing/testing/index.md`,
  `docs/portal-development/getting_started.md`, `AGENTS.md`) are brought up to date.
- `CONTEXT.md` gains *base image*, *runtime image*, *development image* and *start sequence*, as
  the spec's key entities define them.
- The changelog gets one Added entry.

### P9. Publishing access

The package `ghcr.io/fair-dm/fairdm` is linked to the archived `FAIR-DM/docker` repository
(research). Before the first push, an organisation owner grants this repository write access in
the package's settings, and decides what happens to its old `latest` and `2025.1` tags. Nothing
in this plan depends on it until a release is published. It is raised at the merge gate.

## Story order

US1 first: it carries the Dockerfile, the entrypoint and the example, which every other story
builds on. Then US2 (start steps), US3 (compose), US5 (the checks on pull requests) and US4
(publishing), each from the previous story's accepted commit. US4 comes last because it extends
the workflow US5 creates.

## Risks

- **Debian package names drift between releases.** `gdal-bin` and `libpq5` are stable names, and
  the pull-request build catches a change the day the base image moves.
- **The suite inside a container is slower to start.** The cached image build adds about a minute
  to the test job. The suite itself is unchanged.
- **The development image runs as `fairdm`.** On a Linux host whose user is not uid 1000, a mounted
  checkout may not be writable from inside. The guide says so, and that `user:` in the compose file
  changes it.
