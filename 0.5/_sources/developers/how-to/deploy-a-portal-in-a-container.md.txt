# How to deploy a portal in a container

A portal runs in a container built on the base images FairDM publishes. You follow this guide to build your portal's production image, start it against a PostGIS database and a Redis server, and check the configuration before you put it in front of people.

## Before you start

You need:

- Docker.
- A portal repository with a `pyproject.toml` and a `uv.lock` that lock FairDM among the dependencies.
- A PostGIS database and a Redis server that the container can reach.
- A reverse proxy or load balancer that ends TLS and sets the `X-Forwarded-Proto` header.

## Steps

1. Find the image version and the PostGIS tag your FairDM declares. Open `pyproject.toml` in the FairDM repository at the release or commit your portal pins and read the `[tool.fairdm.platform]` table.

   ```toml
   [tool.fairdm.platform]
   image = "1.0.0"
   postgis = "17-3.5"
   ```

   Use the image version in the next steps, and run your database from the `postgis/postgis` image with that tag. When you move your portal to a newer FairDM, move the image and the database in the same change.

2. Copy this Dockerfile to the root of your portal's repository. It installs your locked dependencies on the development image, which has a compiler and git, then copies them and your code onto the runtime image.

   ```{literalinclude} ../../../docker/portal.Dockerfile
   :language: dockerfile
   ```

   The Dockerfile copies `README.md` because the `hatchling` build backend reads it. Leave it out if your build backend does not.

3. Add a `.dockerignore` next to the Dockerfile. The Dockerfile copies your whole repository into the image, and anyone who can pull the image can read every file in it.

   ```text
   .env
   stack*.env
   .git
   .venv
   media/
   ```

4. Build the image with the version from step 1.

   ```bash
   docker build --build-arg FAIRDM_IMAGE_VERSION=1.0.0 -t my-portal .
   ```

5. Write the portal's configuration to a file outside the repository, such as `/etc/my-portal/portal.env`, with one variable on each line.

   ```text
   DJANGO_SECRET_KEY=<at least 50 random characters>
   DJANGO_SITE_DOMAIN=portal.example.org
   POSTGRES_HOST=<database host>
   POSTGRES_DB=<database name>
   POSTGRES_USER=<database user>
   POSTGRES_PASSWORD=<database password>
   REDIS_URL=redis://<redis host>:6379/0
   BACKUP_PUBLIC_KEY=<the armoured public key on one line, with \n in place of each line break>
   ```

   [Container images](../reference/container-images.md#variables-a-production-portal-needs) lists the variables the production checks require, and [Settings](../reference/settings.md#environment-variables) describes each one.

   The portal refuses to start in production without `BACKUP_PUBLIC_KEY`. [How to back up a portal](back-up-a-portal.md#encrypt-the-backups) shows how to create the key pair and write it on one line.

6. Start the portal, with a volume at the directory it writes backups to.

   ```bash
   docker run --rm --publish 8000:8000 --env-file /etc/my-portal/portal.env \
     --volume my-portal-backups:/var/lib/fairdm/backups my-portal
   ```

7. Point your proxy at port 8000 of the container. The portal redirects plain HTTP to HTTPS and trusts `X-Forwarded-Proto` for the original scheme. A request that reaches the container without the header gets a redirect and not a page.

8. Run the deployment checks against the same configuration.

   ```bash
   docker run --rm --env-file /etc/my-portal/portal.env my-portal python manage.py check --deploy
   ```

## Run the worker and the scheduler

Backups run as scheduled tasks, so the portal needs a Celery worker and Celery beat, the process that sends the tasks on their schedule. Start both from the same image and environment file, with the same volume at the backup directory. Run one beat for each portal: a second beat sends every task twice.

```yaml
services:
  worker:
    image: my-portal
    env_file: /etc/my-portal/portal.env
    command: worker --loglevel INFO
    volumes:
      - backups:/var/lib/fairdm/backups
  beat:
    image: my-portal
    env_file: /etc/my-portal/portal.env
    command: beat --loglevel INFO
    volumes:
      - backups:/var/lib/fairdm/backups

volumes:
  backups:
    name: my-portal-backups
    external: true
```

The volume is the `my-portal-backups` volume of step 6, which Docker created when the web container started, so Compose uses it and does not create a second one. The web, worker and beat containers share it (add it to the web service too, as in step 6) so that `manage.py backup` run in any of them writes where the others look. With media on S3, backups go to the bucket and the volume holds nothing. A worker still builds the media archive on its own local disk before it uploads it, so give it free disk of about twice the size of the media. See [How to back up a portal](back-up-a-portal.md).

## The result

The container applies the database migrations, collects the static files and starts gunicorn on port 8000. If a step fails, the container exits with that step's status and names what is missing. The log lines of the start sequence are in [Container images](../reference/container-images.md#start-sequence).

`check --deploy` exits with `0` when every check passes and `1` when it finds an error. It reports `fairdm.W601` until you tell the portal how many proxies stand in front of it. See [How to count API callers behind a proxy](count-api-callers-behind-a-proxy.md). Each check and its fix is in [Configuration checks](../../administrators/reference/configuration-checks.md).

The container serves static files but not `/media/`. Uploaded files are written to `/app/media` inside the container and are lost when it is replaced. Mount a volume at that path and have your proxy serve it, or set the `S3_*` variables to store media in S3. See [`STORAGES`](../reference/settings.md#storages).

To change the port, set `PORT`, as [Container images](../reference/container-images.md#environment-variables-the-entrypoint-reads) describes. To run work of your own before the server starts, see [How to add a start step to a container](add-a-start-step-to-a-container.md). To run a background worker, see [How to run a background worker in a container](run-a-background-worker-in-a-container.md). Why the images have a version of their own is in [How the container images are versioned](../explanation/how-the-container-images-are-versioned.md).
