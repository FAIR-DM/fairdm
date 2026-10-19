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
#     DJANGO_ENV=production DJANGO_SETTINGS_MODULE=config.settings
# COPY entrypoint.sh /usr/local/bin/fairdm-entrypoint; mkdir /docker-entrypoint.d
# WORKDIR /app; USER fairdm; EXPOSE 8000
ENTRYPOINT ["fairdm-entrypoint"]
CMD ["web"]

FROM runtime AS development
USER root
# build-essential, libpq-dev, git
ENV DJANGO_ENV=development
USER fairdm
```

`DJANGO_ENV` and `DJANGO_SETTINGS_MODULE` are set in the image because a portal's `manage.py`
defaults to development, and the worker never reads `manage.py` at all. A portal whose settings
module is not `config.settings` sets it in its own Dockerfile or environment.

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
          for step in "$start_dir"/*; do
            [ -f "$step" ] || continue
            if [ -x "$step" ]; then "$step"; else echo "skipping $step: not executable" >&2; fi
          done
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
ARG FAIRDM_VERSION
FROM ${FAIRDM_IMAGE}:${FAIRDM_VERSION}-dev AS build
COPY --chown=fairdm:fairdm pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev --no-install-project
COPY --chown=fairdm:fairdm . .
RUN uv sync --locked --no-dev --no-editable

FROM ${FAIRDM_IMAGE}:${FAIRDM_VERSION}
COPY --from=build /opt/venv /opt/venv
COPY --chown=fairdm:fairdm . /app
```

It installs no system package (SC-001). `FAIRDM_VERSION` has no default: no release has images
yet, and the guide tells a portal to write its own FairDM version there. CI sets both arguments to
point at the images just built. `README.md` is copied because hatchling reads it, and the guide
says a portal whose build backend does not can leave it out.

FairDM's demo builds with this file only once the demo's settings stop overriding the
environment's compression settings. `config/settings.py:9-10` sets `COMPRESS_ENABLED = True` and
`COMPRESS_OFFLINE = False` after `fairdm.setup()`, a leftover from the first commit in 2025 that
predates the environment profiles. With it, `compress` in the start sequence refuses to run. Both
lines go, so production compresses offline (`fairdm/conf/settings/static_media.py:42`) and
development does not compress (`fairdm/conf/development.py:81`).

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
3. one `docker run --rm --network host --user root -v "$PWD:/app" -v "$HOME/.cache/uv:/root/.cache/uv"`
   with `-e POSTGRES_HOST -e POSTGRES_PORT -e POSTGRES_USER -e POSTGRES_PASSWORD -e POSTGRES_DB
   -e DJANGO_VERSION`, running `sh -c "uv sync --locked && uv pip install django~=$DJANGO_VERSION.0
   && <version check> && pytest --cov=fairdm --cov-report=xml"`. The uv cache directory is kept
   between runs with `actions/cache`, keyed on `uv.lock`, so dependencies are not downloaded and
   the git dependencies not cloned on every run

The job name, the matrix and the Codecov step stay, so the required check keeps its name.

### P6. `.github/workflows/image.yml`

Research R10. One job, `Image`, `runs-on: ubuntu-latest`, `permissions: contents: read,
packages: write`, with a PostGIS service on 5432.

1. Build `runtime` and `development` from `docker/Dockerfile` (load, cached).
2. Build `docker/portal.Dockerfile` with `FAIRDM_IMAGE` and `FAIRDM_VERSION` pointing at them.
3. Run `docker/smoke-test.sh <portal image>`.
4. Only on a `refs/tags/v*` ref: log in with `GITHUB_TOKEN` and run `docker/publish.sh
   ${GITHUB_REF_NAME#v}`.

`docker/publish.sh <version> [<repository>]` (default `ghcr.io/fair-dm/fairdm`) handles both
tags, `<version>` and `<version>-dev`, one at a time: a tag that already exists is left alone, and
a missing one is pushed. A published tag is therefore never moved (FR-013), and a run that failed
after pushing one tag is completed by running again, rather than refused forever. Existence is
read with `docker buildx imagetools inspect`, and only a not-found answer counts as absent: an
authentication or network error stops the script before anything is pushed. Nothing is pushed if
any earlier step fails, because the script runs last (FR-014).

The job has `concurrency: image-${{ github.ref }}` with `cancel-in-progress: false`, so two runs on
the same tag never check and push at the same time.

Triggers: `pull_request`, `push` to `main`, `release: published`, `workflow_dispatch`. Any `v*` tag
ref publishes, including a tag pushed by hand. Only people with write access can push one.

**v0.1.0 gets no images.** A dispatch on a tag runs the workflow and the Dockerfile as they were at
that tag, and v0.1.0 has neither. The first images are published by the first release that
carries this feature. SC-003 is shown on that release, not before the merge.

### P7. `docker/smoke-test.sh`

Research R8, plus what only the image's contents can show: `libpq.so.5` and `uv` are present in
the runtime image, `import fairdm` fails in the runtime image itself, and `gcc` and `git` are
present in the development image. Takes the runtime, development and portal image names. Uses `docker run` against the job's PostGIS service
through the host network. Each check prints one line, and the script exits non-zero on the first
failure. The settings the demo needs in production mode come from the environment the script
sets: a throwaway secret key, allowed hosts, the database, and whatever else the production
configuration checks require. Production redirects HTTP to HTTPS
(`fairdm/conf/settings/security.py:36`), so requests send `X-Forwarded-Proto: https`, as a proxy in
front of a portal would. The implementer reads them from `fairdm/conf/` and
`config/production.py` and lists them in the guide, since a portal needs the same.

### P8. Documentation

- `docs/portal-development/production.md` is rewritten as the guide to deploying a portal on the
  images: the two images and their tags, which image version goes with which FairDM version and
  what a portal pinned to a commit between releases uses (FR-019), the example Dockerfile by
  `literalinclude` of `docker/portal.Dockerfile`, start steps, the worker, the port and the
  environment variables, and the development image in a portal's own compose file (FR-018). The
  description of `compose/production/django` goes.
- Contributor pages that describe the compose stack or the GDAL install in CI
  (`docs/contributing/before_you_start.md`, `docs/contributing/testing/index.md`,
  `docs/portal-development/getting_started.md`, `AGENTS.md`, which still calls the compose stack
  broken at line 26) are brought up to date.
- The guide's release note says images appear only when Tag Release runs with `RELEASE_TOKEN`,
  since a release created with `GITHUB_TOKEN` starts no other workflow.
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

### P10. Removing django-compressor (decisions D11)

- `pyproject.toml`: drop `django-compressor` and `django-libsass` from the dependencies and from
  deptry's DEP002 list, then `uv lock`.
- `fairdm/conf/settings/apps.py`: drop `compressor` from the installed apps and the `("compress",)`
  entry from the setup-tools production list.
- `fairdm/conf/settings/static_media.py`: drop `COMPRESS_ROOT`, `COMPRESS_URL`, the
  `CompressorFinder`, `COMPRESS_ENABLED`, `COMPRESS_OFFLINE`, `COMPRESS_FILTERS` and
  `COMPRESS_PRECOMPILERS`, and the module docstring's mention of compressor.
- `fairdm/conf/development.py` and `tests/settings.py`: drop their `COMPRESS_*` lines.
- `fairdm/templates/pages/spectacular.html`: drop `compress` from its `{% load %}`.
- `fairdm/contrib/theme/README.md`: the snippet that compresses the theme stylesheet goes.
- The entrypoint, its tests, the smoke test, the guide and `CONTEXT.md` drop the step.
- Changelog: a Removed entry, with what a portal that used `{% compress %}` has to do.

The SCSS files under `demo/static/scss/` and the Bootstrap-era theme pages
(`docs/portal-development/theme.md`, `theme-migration.md`) are already stale and are not touched.

### P11. Image releases of their own (decisions D2, D17)

Changed during the build at the maintainer's request. The images are versioned separately from
FairDM and released from the Actions tab:

- `.github/workflows/image-release.yml`: `workflow_dispatch` with a `bump` input, on `main` only.
  Jobs: `Version` (`docker/next-version.sh`), `Check` (calls `image.yml`), `Publish` (rebuild from
  cache, `docker/publish.sh`, then `gh release create image-v<version>`). Only `Publish` has
  `contents: write` and `packages: write`.
- `.github/workflows/image.yml`: builds and smoke-tests only, callable with a `version` input. The
  release trigger and the publish job go.
- `docker/next-version.sh BUMP`: next version from the `image-v*` tags, tested in
  `tests/test_docker/test_next_version.py`.
- `docker/portal.Dockerfile`'s build argument is `FAIRDM_IMAGE_VERSION`.
- The guide's version section, the contributor page's release section, ADR 0034 and the
  changelog describe image versions.

