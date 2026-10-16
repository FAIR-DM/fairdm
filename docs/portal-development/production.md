# How to deploy a portal in a container

FairDM provides two base images for portals to build their containers on. This guide builds a
portal's production image on them, starts it against a PostGIS database, and starts a background
worker from the same image.

## The two images

Both images are built from `docker/Dockerfile`. Neither contains FairDM or any portal code: your
portal's locked dependencies decide which FairDM it runs.

| Image | Target | Holds | Used for |
| --- | --- | --- | --- |
| Runtime image | `runtime` | Python 3.13, uv, the PostgreSQL client library, GDAL, GEOS and PROJ, a non-root `fairdm` user, and the start sequence | Running your portal in production |
| Development image | `development` | Everything in the runtime image, plus git and the tools that build Python packages which compile | Installing your portal's dependencies |

In both images your portal lives in `/app`, its virtual environment in `/opt/venv`, and the server
runs as the user `fairdm` (uid 1000). GeoDjango finds GDAL, GEOS and PROJ without
`GDAL_LIBRARY_PATH` or `GEOS_LIBRARY_PATH` being set.

Both images are published as `ghcr.io/fair-dm/fairdm:<version>` and
`ghcr.io/fair-dm/fairdm:<version>-dev`.

## Build the images from a FairDM checkout

From the root of a FairDM checkout:

```bash
docker build -f docker/Dockerfile --target runtime -t fairdm-base:local .
docker build -f docker/Dockerfile --target development -t fairdm-base:local-dev .
```

Use these names in place of the published images in the next section by passing
`--build-arg FAIRDM_IMAGE=fairdm-base --build-arg FAIRDM_VERSION=local`.

## Build your portal's production image

Copy the Dockerfile below to your portal's repository. It installs your locked dependencies on the
development image, then copies them and your code onto the runtime image. It installs no system
package.

```{literalinclude} ../../docker/portal.Dockerfile
:language: dockerfile
```

`FAIRDM_VERSION` has no default. Write the FairDM release your portal depends on there:

```bash
docker build --build-arg FAIRDM_VERSION=<release> -t my-portal .
```

Your repository needs a `pyproject.toml` and a `uv.lock`. The Dockerfile copies `README.md` because
the `hatchling` build backend reads it, so a portal whose build backend does not can leave it out.

## Start the portal

The image's default command is `web`. It runs these steps, in this order, and stops at the first one
that fails, exiting with that step's status without starting the server:

1. `python manage.py migrate --noinput`
2. `python manage.py collectstatic --noinput`
3. `python manage.py compress`
4. `gunicorn config.wsgi:application`

Static files are collected and compressed when the container starts, not when it is built, so
settings that arrive through the environment apply to them.

```{note}
`compress` stops with an error when no template in the portal uses the `{% compress %}` tag. A
portal that compresses nothing therefore does not start.
```

Run it against a PostGIS database and a Redis server:

```bash
docker run --rm --publish 8000:8000 \
    --env DJANGO_SECRET_KEY=<at least 50 random characters> \
    --env DJANGO_SITE_DOMAIN=portal.example.org \
    --env POSTGRES_HOST=<database host> \
    --env POSTGRES_DB=<database name> \
    --env POSTGRES_USER=<database user> \
    --env POSTGRES_PASSWORD=<database password> \
    --env REDIS_URL=redis://<redis host>:6379/0 \
    my-portal
```

### Environment variables

The image sets `DJANGO_ENV=production` and `DJANGO_SETTINGS_MODULE=config.settings`. A portal whose
settings module is somewhere else sets `DJANGO_SETTINGS_MODULE` in its own Dockerfile or
environment. These variables are the ones a production portal needs:

| Variable | Meaning |
| --- | --- |
| `DJANGO_SECRET_KEY` | The secret key, at least 50 characters. There is no default. |
| `DJANGO_SITE_DOMAIN` | The domain the portal answers on. It is added to `ALLOWED_HOSTS`. Set `DJANGO_ALLOWED_HOSTS` to a comma-separated list for more. |
| `POSTGRES_HOST`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | The PostGIS database. `POSTGRES_PORT` defaults to 5432. Alternatively set `DATABASE_URL`. |
| `REDIS_URL` | The Redis server used for the cache and as the Celery broker. |

Without them the container refuses to start, naming what is missing. See
[Configuration checks](../portal-administration/configuration-checks.md) for the full list of checks
and `python manage.py check --deploy` to run them before you deploy.

Production redirects plain HTTP to HTTPS and trusts the `X-Forwarded-Proto` header for the
original scheme. Put the portal behind a proxy that terminates TLS and sets that header. A request
that reaches the container without it gets a redirect and not a page.

### Change the port

The server listens on port 8000. Set `PORT` to change it, with no rebuild:

```bash
docker run --env PORT=8123 --publish 8123:8123 ... my-portal
```

## Start a background worker

The same image starts a Celery worker when its command is `worker`. It runs none of the steps above.

```bash
docker run ... my-portal worker --loglevel INFO
```

Arguments after `worker` go to Celery. The worker runs the application in `config`, which is where
a portal laid out like the demo exposes it. Set `CELERY_APP` for another. It needs the same
environment variables as the web container.

## Run any other command

Anything else is run as given, so `docker run ... my-portal python manage.py shell` and a Compose
`command:` line work without a wrapper.

## Validate before you deploy

Run Django's deployment checks against the same configuration:

```bash
python manage.py check --deploy
```

The command exits with `0` when every check passes and `1` when it finds errors. Include it in your
CI pipeline to catch configuration problems before a deployment. For the checks and how to fix each
one, see [Configuration checks](../portal-administration/configuration-checks.md).
