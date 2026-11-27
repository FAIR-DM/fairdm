# How to run a background worker in a container

Some of a portal's work runs in the background, outside the web request. You run a Celery worker from the same image as the web container, so both run the same code and read the same configuration.

## Before you start

You have a [production image for your portal](deploy-a-portal-in-a-container.md) and a Redis server. Your portal's `config` package exposes the Celery application, so the worker can find it. FairDM provides the application as `fairdm.conf.celery.app`.

```python
# config/__init__.py
from fairdm.conf.celery import app as celery_app

__all__ = ("celery_app",)
```

## Steps

1. Start a container from the same image with the command `worker`. Give it the same environment file as the web container.

   ```bash
   docker run --rm --env-file /etc/my-portal/portal.env my-portal worker --loglevel INFO
   ```

   Everything after `worker` goes to Celery.

2. If your Celery application is not in the `config` package, set `CELERY_APP` to the module that holds it.

   ```bash
   docker run --rm --env-file /etc/my-portal/portal.env --env CELERY_APP=my_portal.celery my-portal worker
   ```

3. With Docker Compose, give the worker its own service. It uses the same image and environment file as the web service.

   ```yaml
   services:
     worker:
       image: my-portal
       env_file: /etc/my-portal/portal.env
       command: worker --loglevel INFO
   ```

## The result

The worker connects to the broker at `REDIS_URL` and runs the tasks the web container sends. It runs none of the web container's start sequence, so it does not migrate the database, collect static files or run your start steps. Start it after the web container has migrated the database.

The worker needs the same variables as the web container, because it reads the same settings. [Container images](../reference/container-images.md#commands) describes the `worker` command. The settings that shape the worker, such as the time limits and the broker, are in [Settings](../reference/settings.md#background-tasks). Without a worker, tasks wait in the broker and nothing runs them.
