# Container images

This page describes the two base images FairDM publishes for portals, the tags they are published under, what the images contain, the variables and commands they understand, the start sequence, and the record of the image and database versions that FairDM declares. It does not give the steps to build or run a portal, which are in [How to deploy a portal in a container](../how-to/deploy-a-portal-in-a-container.md), or the reasons behind the versioning, which are in [How the container images are versioned](../explanation/how-the-container-images-are-versioned.md).

## The images

Both images are built from `docker/Dockerfile` in the FairDM repository. Neither contains FairDM or any portal code. A portal installs its own locked dependencies, FairDM among them.

| | Runtime image | Development image |
| --- | --- | --- |
| Dockerfile target | `runtime` | `development` |
| Registry name | `ghcr.io/fair-dm/fairdm:<image version>` | `ghcr.io/fair-dm/fairdm:<image version>-dev` |
| Built from | `python:3.13-slim` | The runtime image |
| Added system packages | `gdal-bin`, `libpq5`, `postgresql-client-17` | `build-essential`, `libpq-dev`, `git` |
| `DJANGO_ENV` | `production` | `development` |
| Used for | Running a portal | Installing a portal's dependencies, and running a portal on your own machine |

Both images are published for `linux/amd64`. GDAL, GEOS and PROJ come with `gdal-bin` and are found without `GDAL_LIBRARY_PATH` or `GEOS_LIBRARY_PATH`.

`<image version>` is a three-part version such as `1.0.0`. It is the version of the images and not of FairDM. There is no `latest` tag, and a published tag is never replaced. A release is also recorded as the Git tag and GitHub release `image-v<image version>`.

## What is in an image

| Item | Value |
| --- | --- |
| Working directory | `/app` |
| Python environment | `/opt/venv`, first on `PATH` |
| User | `fairdm`, user id 1000, group id 1000 |
| Directories created | `/app/static`, `/app/media`, `/opt/venv`, `/docker-entrypoint.d` and `/var/lib/fairdm/backups`, all owned by `fairdm` |
| Package manager | uv 0.11, copied from `ghcr.io/astral-sh/uv:0.11` |
| Exposed port | `8000` |
| Entrypoint | `fairdm-entrypoint` |
| Default command | `web` |

The images carry these OCI labels: `org.opencontainers.image.title`, `description`, `source`, `licenses` (`MIT`) and `version`. The `version` label takes the `VERSION` build argument, which defaults to `dev`.

## Environment variables the image sets

| Variable | Value | Notes |
| --- | --- | --- |
| `DJANGO_ENV` | `production` in the runtime image, `development` in the development image | See [DJANGO_ENV](settings.md#django_env) |
| `DJANGO_SETTINGS_MODULE` | `config.settings` | Set another value in a portal whose settings module is elsewhere |
| `PORT` | `8000` | gunicorn listens on `0.0.0.0:$PORT` |
| `BACKUP_DIR` | `/var/lib/fairdm/backups` | Where a portal with local media writes its backups. See [BACKUP_DIR](settings.md#backup_dir) |
| `UV_PROJECT_ENVIRONMENT` | `/opt/venv` | Keeps the environment outside `/app`, so a source tree mounted at `/app` never hides it |
| `UV_LINK_MODE` | `copy` | |
| `UV_PYTHON_DOWNLOADS` | `never` | uv uses the image's Python |
| `PATH` | `/opt/venv/bin:$PATH` | |
| `PYTHONUNBUFFERED` | `1` | |
| `PYTHONDONTWRITEBYTECODE` | `1` | |

## Environment variables the entrypoint reads

| Variable | Default | What it does |
| --- | --- | --- |
| `FAIRDM_START_DIR` | `/docker-entrypoint.d` | The directory the `web` command takes [start steps](#start-steps) from |
| `WSGI_APP` | `config.wsgi:application` | The WSGI application gunicorn serves |
| `CELERY_APP` | `config` | The application the `worker` command runs. Celery finds the Celery instance in that module. |
| `PORT` | `8000` | Read by gunicorn for its address |

## Variables a production portal needs

The `web` command starts the portal on the production baseline, so [the production checks](../../administrators/reference/configuration-checks.md) apply. These variables are the ones the checks require. Each is described in [Settings](settings.md#environment-variables).

| Variable | Required | Notes |
| --- | --- | --- |
| [`DJANGO_SECRET_KEY`](settings.md#django_secret_key) | Yes | At least 50 characters, with no default |
| [`DJANGO_SITE_DOMAIN`](settings.md#django_site_domain) | Yes, or `DJANGO_ALLOWED_HOSTS` | Added to `ALLOWED_HOSTS` |
| [`DJANGO_ALLOWED_HOSTS`](settings.md#django_allowed_hosts) | No | A comma-separated list of further hosts |
| [`POSTGRES_HOST`](settings.md#postgres_host), [`POSTGRES_DB`](settings.md#postgres_db), [`POSTGRES_USER`](settings.md#postgres_user), [`POSTGRES_PASSWORD`](settings.md#postgres_password) | Yes, or `DATABASE_URL` | [`POSTGRES_PORT`](settings.md#postgres_port) defaults to `5432` |
| [`DATABASE_URL`](settings.md#database_url) | Yes, or the `POSTGRES_*` variables | |
| [`REDIS_URL`](settings.md#redis_url) | Yes | The cache and the Celery broker |

## Commands

The first argument of `docker run` after the image name selects what the container does.

| Command | What it runs |
| --- | --- |
| `web` (the default) | The [start sequence](#start-sequence), ending in gunicorn |
| `worker [arguments]` | `celery --app $CELERY_APP worker` with the arguments you give. It runs no migration and no start step. |
| Anything else | The command as given, with no start sequence. `python manage.py shell` and a Compose `command:` line work without a wrapper. |

## Start sequence

The `web` command runs these steps in this order. It stops at the first one that fails and exits with that step's status, and gunicorn does not start.

1. `python manage.py migrate --noinput`
2. `python manage.py collectstatic --noinput`
3. Each [start step](#start-steps), one at a time
4. `gunicorn $WSGI_APP`, started with `exec`

Static files are collected when the container starts, so settings that arrive through the environment apply to them.

## Start steps

A start step is a file in the start directory, `/docker-entrypoint.d` unless `FAIRDM_START_DIR` names another.

| Rule | Behaviour |
| --- | --- |
| Which files | Every regular file in the directory |
| Order | The order of the file names. Prefix the names with numbers to choose it. |
| A file that is not executable | Skipped, with `skipping <path>: not executable` on standard error |
| A missing or empty directory | The sequence runs with no start steps |
| A step that exits with a non-zero status | The start stops with that status |
| User, directory and environment | The user `fairdm`, in `/app`, with the container's environment |
| A directory the `fairdm` user cannot read | Treated as empty, so no step runs |

The `worker` command and any other command run no start steps. [How to add a start step to a container](../how-to/add-a-start-step-to-a-container.md) shows how to add one.

## Portal image build arguments

`docker/portal.Dockerfile` builds a portal's production image on the base images. A portal copies the file into its own repository.

| Build argument | Default | What it does |
| --- | --- | --- |
| `FAIRDM_IMAGE` | `ghcr.io/fair-dm/fairdm` | The registry name of the base images |
| `FAIRDM_IMAGE_VERSION` | None | The image version to build on. The build fails without it. |

The build installs the locked dependencies with `uv sync --locked --no-dev` on the development image, then copies the environment and the portal's code onto the runtime image. It needs a `pyproject.toml`, a `uv.lock` and a `README.md` in the portal's root.

## `[tool.fairdm.platform]`

FairDM records the image and the database it is tested on in its `pyproject.toml`:

```toml
[tool.fairdm.platform]
image = "1.0.0"
postgis = "17-3.5"
```

| Key | Type | What it holds |
| --- | --- | --- |
| `image` | `str` | The image version FairDM is tested on, a version of the images described on this page |
| `postgis` | `str` | The tag of the `postgis/postgis` image FairDM is tested against |

A portal reads the table at the FairDM release or commit it pins and uses the image version and the PostGIS tag that it declares. FairDM's own workflows read `postgis` from the table.
