# Research: publish a FairDM base image that portals build their containers on

Investigated against `origin/main` at `a4a93b71` (v0.1.0). Citations into installed packages are
to the resolved virtual environment of this branch, `.venv/lib/python3.13/site-packages/`.

## Planning notes

### Tag the images by release, once #525 runs

**Adopted.** #525 merged as #532, and v0.1.0 was released on 2026-10-16 by the Prepare Release →
Tag Release flow. Tag Release creates the release with `RELEASE_TOKEN`, a personal access token,
so the `release: published` event reaches other workflows (GitHub suppresses that event only for
releases created with `GITHUB_TOKEN`). The image workflow publishes on that event, tagged
`<version>` and `<version>-dev`, where `<version>` is the release tag without its `v`. v0.1.0
was released before this feature and gets no images: a run on its tag would use the tree of that
tag, which has no image definition. The first images come with the first release that carries
this feature.

## What the code and the environment already give

- **The development image definition.** `compose/django/Dockerfile` installs `gdal-bin` and `git`
  on `python:3.13-slim`, copies uv in, and keeps the environment at `/opt/venv`. #509 proved it
  runs FairDM against PostGIS under `docker compose up`. The new definition starts from it.
- **GDAL is found without a library path.** Django looks the libraries up with
  `ctypes.util.find_library` (`django/contrib/gis/gdal/libgdal.py:5`, `:59`), which on Debian
  reads the `ldconfig` cache and matches the versioned `libgdal.so.N`. Debian's `gdal-bin` pulls
  in libgdal, GEOS and PROJ. Only the `-dev` packages carry the unversioned `.so` symlink, and the
  runtime does not need it.
- **gunicorn and Celery are FairDM dependencies** (`pyproject.toml`: `gunicorn>=23,<27`,
  `celery>=5.6.2,<6`), so any portal's lock file installs them. The image does not.
- **gunicorn binds to `0.0.0.0:$PORT` when `PORT` is set** (`gunicorn/config.py:670-671`), and
  reads extra options from `GUNICORN_CMD_ARGS` (`gunicorn/config.py:87-88`). The port and the
  worker count need no option of the image's own.
- **Celery reads its application from `CELERY_APP`** (`celery/bin/celery.py:59` declares
  `envvar='APP'`, and `:227` sets `auto_envvar_prefix="CELERY"`). FairDM's demo, and any portal laid
  out like it, exposes the app from `config/__init__.py` (`from fairdm.conf.celery import app as
  celery_app`), so the default is `config`.
- **Static files.** `STATIC_ROOT` is `BASE_DIR / "static"` and `COMPRESS_OFFLINE` is on
  (`fairdm/conf/settings/static_media.py:18`, `:42`), so `compress` has to run before serving, and
  `/app/static` has to be writable by the server's user. WhiteNoise serves the result
  (`fairdm/conf/settings/apps.py:114`).
- **The release token is visible to this repository** (`RELEASE_TOKEN` in its organisation
  secrets), and v0.1.0's Tag Release run succeeded.
- **The image name already exists.** `ghcr.io/fair-dm/fairdm` is public and holds two tags,
  `latest` and `2025.1`, from the archived `FAIR-DM/docker` repository. The package is linked to
  that repository, so this repository's workflows cannot push to it until the package grants this
  repository write access. That is a package setting only an organisation owner can change. The
  pull-request checks build and test without pushing and are not affected.
- **The demo portal installs without the dev group.** `config/settings.py` installs neither
  fairdm-discussions nor fairdm-docs, so the demo builds with `uv sync --no-dev`, the way a portal's
  production image would.

## Decisions

### R1. One Dockerfile, two targets

`docker/Dockerfile` has a `runtime` stage on `python:3.13-slim` and a `development` stage built
`FROM runtime`, adding `build-essential`, `libpq-dev` and `git`. The development image is then
everything the runtime image is, plus the tools (FR-009), with the same Python, the same paths and
the same user, so a virtual environment built in one runs in the other. Published as
`ghcr.io/fair-dm/fairdm:<version>` and `ghcr.io/fair-dm/fairdm:<version>-dev`, following the
`python:3.13` and `python:3.13-slim` convention of one repository with variant suffixes.

Alternatives: `ghcr.io/osgeo/gdal` images ship GDAL and their own Python, which is Ubuntu's 3.12
and not FairDM's 3.13. Building GDAL from source is slower and gains nothing over Debian's
packages.

### R2. Runtime packages

`gdal-bin` (libgdal, GEOS, PROJ) and `libpq5`. psycopg2-binary bundles its own libpq, but a
portal that installs psycopg or psycopg2 from source needs the system one at runtime, and the spec
lists it (FR-002).

### R3. User and paths

A `fairdm` user and group with uid and gid 1000, home `/home/fairdm`. `WORKDIR /app`, owned by
`fairdm`, with `/app/static` and `/app/media` created and owned by it. The environment is
`/opt/venv`, owned by `fairdm`, set with `UV_PROJECT_ENVIRONMENT=/opt/venv` and put first on
`PATH`, so `python` and `gunicorn` are the portal's. `UV_LINK_MODE=copy`,
`UV_PYTHON_DOWNLOADS=never` (uv uses the image's Python, never a downloaded one),
`PYTHONUNBUFFERED=1`, `PYTHONDONTWRITEBYTECODE=1`, `PORT=8000`. uv is copied from
`ghcr.io/astral-sh/uv`, pinned to a minor version.

### R4. The start sequence is a shell entrypoint

`docker/entrypoint.sh`, installed as `/usr/local/bin/fairdm-entrypoint` and set as `ENTRYPOINT`,
with `CMD ["web"]`.

- `web`: `python manage.py migrate --noinput`, `collectstatic --noinput`, `compress`, then every
  executable file in `/docker-entrypoint.d/` in name order, then `exec gunicorn "$WSGI_APP"`. The
  default `WSGI_APP` is `config.wsgi:application`.
- `worker`: `exec celery worker`, with the application from `CELERY_APP` (default `config`). It
  runs none of the web steps.
- Anything else is run as given with `exec "$@"`, the convention of the official images, so
  `docker run … python manage.py shell` and Compose `command:` lines work unchanged.

`set -eu` makes any failing step stop the start with its exit status (FR-005, FR-008).
`/docker-entrypoint.d/` follows the official nginx image, where the same directory holds the
image's start hooks. A portal adds a step with `COPY --chmod=755 start.d/ /docker-entrypoint.d/`.
Its steps run after FairDM's, so a later release's default steps change under it without the
portal changing (US2 AS 3).

The directory can be moved with `FAIRDM_START_DIR`, which is how the tests point it at a temporary
directory. No other behaviour depends on it.

Not adopted: `django-setup-tools`, configured in `fairdm/conf/settings/apps.py:254-282` and never
called (#193). Its lists differ from the sequence portals run, and its `on_initial` list includes
`createsuperuser`, which prompts. Settling that is #193's (decisions D4).

### R5. FairDM's compose stack builds the development target and syncs at start

The development image holds no dependencies (FR-003), so the stack keeps them in a named volume
on `/opt/venv` and runs `uv sync --locked` before the server starts. The first start installs
everything and later starts find nothing to do. A portal's own compose file does exactly the
same with `image: ghcr.io/fair-dm/fairdm:<version>-dev` and no Dockerfile (US3 AS 3), and the
guide shows both. FairDM's stack uses `build:` with `target: development` instead of `image:`,
because it has to run the definition on the branch, not a published one (FR-011).

`compose/django/Dockerfile` and the `compose/` directory go.

### R6. The example portal Dockerfile is a real file, built in CI

`docker/portal.Dockerfile` is the complete production Dockerfile the guide shows, included into
the page with `literalinclude` so the guide cannot drift from it. It takes the image name and
version as build arguments with published defaults. CI builds FairDM's own demo portal with it,
on the images just built from the branch, and runs the checks in R8 against that container. This
is what proves SC-001 and SC-005: the example installs no system package and starts from an
empty database.

### R7. Tests of the entrypoint run in the suite, without Docker

`tests/test_docker/test_entrypoint.py` runs `docker/entrypoint.sh` with `subprocess`, with a `PATH`
holding stand-in `python`, `gunicorn` and `celery` scripts that record their arguments, and
`FAIRDM_START_DIR` pointing at a temporary directory. It asserts the order of the steps, that a
failing step stops the start and the server never runs, the worker mode, and that any other
command runs as given. These are the behaviours a specification decides, and they run in seconds
on every pull request. `tests/test_docker/` is declared in `[tool.forge.conformance]
non-mirror-paths`, because its subject is a shell script.

### R8. What only a built image can show is checked in CI by a script

`docker/smoke-test.sh` runs against the built demo portal image and a PostGIS service:

- the container starts, migrates, collects and compresses, and `/` answers with a 200
- `PORT=8123` makes it answer on 8123
- the server process is not uid 0
- `python -c "from django.contrib.gis import gdal, geos; …"` succeeds with no library path set
- the `worker` command starts Celery and runs no migration
- with the database unreachable, the container exits non-zero and nothing ever answers on the port
- a step mounted into `/docker-entrypoint.d/` ran after migrations and before the server

### R9. Every pull request runs the suite inside the development image

`test-suite.yml` builds the `development` target from the branch with `docker/build-push-action`
(`load: true`, `push: false`, layers cached in the GitHub Actions cache), then runs
`uv sync --locked` and `pytest` in it with the checkout mounted at `/app` and the PostGIS service
reached through the host network. The required check keeps its name. The step that installed
GDAL on the runner goes. Running as root inside the job's container lets the mounted checkout,
which the runner's user owns, receive `coverage.xml`.

### R10. A new image workflow builds, checks and publishes

`.github/workflows/image.yml` runs on every pull request, on pushes to `main`, on
`release: published`, and by hand. One job builds both targets and the demo portal, runs
`docker/smoke-test.sh`, and only then, and only when the ref is a `v*` tag, logs in to the
registry with `GITHUB_TOKEN` (`packages: write`) and pushes whichever of the two tags does not
exist yet, leaving any that does untouched (FR-013, plan P6). A failure anywhere before the
push publishes nothing (FR-014). Images are built for `linux/amd64` only (FR-015).

The check is named `Image`. Making it required on the ruleset is a tightening that follows once
the check has reported on `main`.

## What already exists

| New piece | Where the search stopped |
|---|---|
| Image definition | this repo: `compose/django/Dockerfile`, extended into `docker/Dockerfile` |
| Choosing the port | gunicorn: `PORT` (`gunicorn/config.py:670`) |
| Worker count and other server options | gunicorn: `GUNICORN_CMD_ARGS` (`gunicorn/config.py:87`) |
| Choosing the Celery app | Celery: `CELERY_APP` (`celery/bin/celery.py:59`, `:227`) |
| Start hooks directory | convention of the official nginx image, `/docker-entrypoint.d/`; no package |
| Start sequence script | new code: `docker/entrypoint.sh`, about 40 lines |
| Finding GDAL | Django: `find_library` in `django/contrib/gis/gdal/libgdal.py`; nothing needed |
| Building and pushing images in CI | `docker/setup-buildx-action`, `docker/build-push-action`, `docker/login-action` |
| Image smoke checks | new code: `docker/smoke-test.sh` |
| Entrypoint tests | new code: `tests/test_docker/test_entrypoint.py` |
| Example portal Dockerfile | new file: `docker/portal.Dockerfile`, which is also the guide's example |
| Image workflow | new file: `.github/workflows/image.yml` |
| Publishing without moving a tag | new code: `docker/publish.sh`, using `docker buildx imagetools` |
