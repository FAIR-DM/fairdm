# How to develop a portal on the development image

The development image runs your portal on your own machine with no Dockerfile of your own. You mount your code from the checkout and keep your dependencies in a volume, so an edit to a Python file reloads the server.

## Before you start

You need Docker with Compose, and a portal repository with a `pyproject.toml` and a `uv.lock`. Your portal's `config` package sets up Django, so the settings module is `config.settings`, and it exposes the Celery application as [How to run a background worker in a container](run-a-background-worker-in-a-container.md) shows.

## Steps

1. Find the image version and the PostGIS tag your FairDM declares in the `[tool.fairdm.platform]` table. [Container images](../reference/container-images.md#toolfairdmplatform) describes where to read it.

2. Save this as `docker-compose.yml` in your portal's repository. Write the image version in place of `<image version>`, and the PostGIS tag in place of `17-3.5` if it differs.

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

3. Start the stack.

   ```bash
   docker compose up
   ```

4. If you work on Linux and your user id is not 1000, add `user: "<your id>:<your group id>"` to the `django` service. The containers run as user id 1000, and the user needs to write to your checkout.

## The result

The first start installs your locked dependencies into the `venv` volume. The portal then answers on <http://localhost:8000>. An edit to a Python file reloads the server.

The development image sets `DJANGO_ENV=development`, so the portal runs with FairDM's development settings. Those settings show Django's debug pages, so the compose file publishes the port on your own machine only. Redis is set, so the portal uses a real cache and the worker runs tasks in the background. Email is printed to the console. [Settings](../reference/settings.md) gives each setting's development value.

The worker waits for the web container to be healthy, so the two never install into the volume at once. To change the settings the portal runs with, see [How to override a FairDM setting](override-a-fairdm-setting.md). What the image contains is in [Container images](../reference/container-images.md).
