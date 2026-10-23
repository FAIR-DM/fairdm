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

## Choose the image version

The images have a version of their own, separate from FairDM's. They change far less often than
FairDM does: only when the Python version, the system libraries, uv or the start sequence changes.
Each image release is published as two tags. For image version `1.0.0`:

| Image | Tag |
| --- | --- |
| Runtime image | `ghcr.io/fair-dm/fairdm:1.0.0` |
| Development image | `ghcr.io/fair-dm/fairdm:1.0.0-dev` |

The version says what kind of change a release is:

- a new **major** version changes something a portal may have to adapt to, such as the Python
  version, the paths, the user or the start command
- a new **minor** version adds something, such as a system library
- a new **patch** version changes nothing a portal relies on, such as a rebuild that picks up
  security updates

The releases and their changes are listed on the repository's
[releases page](https://github.com/FAIR-DM/fairdm/releases), as `image-v<version>`.

Use the image version declared by the FairDM your portal installs. FairDM records it in its
`pyproject.toml`, with the PostGIS version it is tested against:

```toml
[tool.fairdm.platform]
image = "1.0.0"
postgis = "17-3.5"
```

Read the table at the release or commit your portal pins. When you move your portal to a newer
FairDM, move its image and its database to the versions that FairDM declares in the same change.

There is no `latest` tag, so a portal's image changes only when its Dockerfile does. FairDM's
image release workflow never replaces a published tag. A portal that needs an image that cannot
change at all writes the digest the registry shows into its `FROM` lines by hand.

## Build the images from a FairDM checkout

From the root of a FairDM checkout:

```bash
docker build -f docker/Dockerfile --target runtime -t fairdm-base:local .
docker build -f docker/Dockerfile --target development -t fairdm-base:local-dev .
```

Use these names in place of the published images in the next section by passing
`--build-arg FAIRDM_IMAGE=fairdm-base --build-arg FAIRDM_IMAGE_VERSION=local`.

## Build your portal's production image

Copy the Dockerfile below to your portal's repository. It installs your locked dependencies on the
development image, then copies them and your code onto the runtime image. It installs no system
package.

```{literalinclude} ../../docker/portal.Dockerfile
:language: dockerfile
```

`FAIRDM_IMAGE_VERSION` has no default. Write the image version your portal builds on there, as
[Choose the image version](#choose-the-image-version) explains:

```bash
docker build --build-arg FAIRDM_IMAGE_VERSION=1.0.0 -t my-portal .
```

Your repository needs a `pyproject.toml` and a `uv.lock`. The Dockerfile copies `README.md` because
the `hatchling` build backend reads it, so a portal whose build backend does not can leave it out.

### Keep secrets out of the image

The Dockerfile copies your whole repository into the image, and anyone who can pull the image can
read every file in it. Production secrets come from the container's environment when it starts,
never from a file in the repository. Add a `.dockerignore` next to the Dockerfile so that
environment files and local state stay out of the build:

```text
.env
stack*.env
.git
.venv
media/
```

## Start the portal

The image's default command is `web`. It runs these steps, in this order, and stops at the first one
that fails, exiting with that step's status without starting the server:

1. `python manage.py migrate --noinput`
2. `python manage.py collectstatic --noinput`
3. Your [start steps](#add-your-own-start-steps), if you have any
4. `gunicorn config.wsgi:application`

Static files are collected when the container starts, not when it is built, so settings that
arrive through the environment apply to them.

Run it against a PostGIS database and a Redis server, with the configuration in a file kept
outside the repository, so the secrets stay out of the image and out of your shell history:

```bash
docker run --rm --publish 8000:8000 --env-file /etc/my-portal/portal.env my-portal
```

`portal.env` holds one variable per line:

```text
DJANGO_SECRET_KEY=<at least 50 random characters>
DJANGO_SITE_DOMAIN=portal.example.org
POSTGRES_HOST=<database host>
POSTGRES_DB=<database name>
POSTGRES_USER=<database user>
POSTGRES_PASSWORD=<database password>
REDIS_URL=redis://<redis host>:6379/0
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
| `WSGI_APP` | The WSGI application gunicorn serves. Defaults to `config.wsgi:application`. |

Without them the container refuses to start, naming what is missing. See
[Configuration checks](../administrators/reference/configuration-checks.md) for the full list of checks
and `python manage.py check --deploy` to run them before you deploy.

Production redirects plain HTTP to HTTPS and trusts the `X-Forwarded-Proto` header for the
original scheme. Put the portal behind a proxy that terminates TLS and sets that header. A request
that reaches the container without it gets a redirect and not a page.

### Change the port

The server listens on port 8000. Set `PORT` to change it, with no rebuild:

```bash
docker run --env PORT=8123 --publish 8123:8123 ... my-portal
```

## Add your own start steps

A portal often has work of its own to do before the server starts: loading reference data,
clearing expired sessions, warming a cache. Put each piece of work in an executable file in
`/docker-entrypoint.d/`. The `web` command runs the files there after `collectstatic` and before
`gunicorn`, one at a time, in name order. Prefix the names with numbers to choose the order.

A step is any executable: a shell script, or a Python script with a `#!/usr/bin/env python` first
line. It runs as the user `fairdm` in `/app`, with the container's environment, and it can use
`python manage.py` because the database has already been migrated. This one removes expired
sessions:

```sh
#!/bin/sh
set -eu
python manage.py clearsessions
```

Save it in your portal's repository as `docker-entrypoint.d/10-clear-sessions` and add one line to
your portal's Dockerfile, after the `COPY` that puts your code in `/app`:

```dockerfile
COPY --chmod=755 docker-entrypoint.d/ /docker-entrypoint.d/
```

`--chmod=755` is what makes the file executable. A file that is not executable is skipped, and the
container's log has a line naming it:

```text
skipping /docker-entrypoint.d/10-clear-sessions: not executable
```

A step that exits with a non-zero status stops the start. The container exits with that status and
the server never starts, the same as for `migrate`. To try a step without rebuilding the image,
mount a directory of steps when you run it:

```bash
docker run ... --volume "$PWD/docker-entrypoint.d:/docker-entrypoint.d:ro" my-portal
```

The server runs as the `fairdm` user, uid 1000, so the mounted directory and its files have to be
readable by that user. A directory only its owner can read is treated as empty, and no step runs.

Set `FAIRDM_START_DIR` to read the steps from another directory. If the directory is missing or
empty, the container runs the sequence above and nothing more. The `worker` command and any
other command run no start steps.

## Start a background worker

The same image starts a Celery worker when its command is `worker`. It runs none of the steps
above, start steps included.

```bash
docker run ... my-portal worker --loglevel INFO
```

Arguments after `worker` go to Celery. The worker runs the application in `config`, which is where
a portal laid out like the demo exposes it. Set `CELERY_APP` for another. It needs the same
environment variables as the web container.

## Run any other command

Anything else is run as given, so `docker run ... my-portal python manage.py shell` and a Compose
`command:` line work without a wrapper.

## Develop your portal on the development image

The development image also runs your portal on your own machine, with no Dockerfile of your own.
Your code is mounted from the checkout and your dependencies are installed into a volume, so an
edit to a Python file reloads the server. Save this as `docker-compose.yml` in your portal's
repository:

```yaml
services:
  postgres:
    image: postgis/postgis:17-3.5
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: fairdm
    volumes:
      - postgres:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      retries: 20

  redis:
    image: redis:7

  django: &django
    image: ghcr.io/fair-dm/fairdm:<image version>-dev
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      POSTGRES_HOST: postgres
      POSTGRES_DB: fairdm
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      REDIS_URL: redis://redis:6379/0
    volumes:
      - .:/app
      - venv:/opt/venv
    ports:
      - "127.0.0.1:8000:8000"
    command: sh -c "uv sync --locked && python manage.py migrate && python manage.py runserver 0.0.0.0:8000"
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/')"]
      interval: 5s
      timeout: 10s
      retries: 240

  celeryworker:
    <<: *django
    ports: []
    healthcheck:
      disable: true
    depends_on:
      django:
        condition: service_healthy
    command: sh -c "uv sync --locked && celery --app config worker --loglevel INFO"

volumes:
  postgres: {}
  venv: {}
```

Write the image version your portal builds on in place of `<image version>`, and the `postgis` tag
from the same table in place of `17-3.5` if it differs. Then run `docker compose up`. The first start installs your locked dependencies into the `venv` volume, and the portal
answers on <http://localhost:8000> once it has. The development image sets `DJANGO_ENV=development`,
so the portal runs with its development settings. Those settings show Django's debug pages, so the
port is published on your own machine only.

The worker waits for the web container to be healthy, so the two never install into the volume at
once. On Linux, the containers run as user id 1000. If yours has another id, add `user:
"<your id>:<your group id>"` to the `django` service so it can write to your checkout.

## Validate before you deploy

Run Django's deployment checks against the same configuration:

```bash
python manage.py check --deploy
```

The command exits with `0` when every check passes and `1` when it finds errors. Include it in your
CI pipeline to catch configuration problems before a deployment. For the checks and how to fix each
one, see [Configuration checks](../administrators/reference/configuration-checks.md).
