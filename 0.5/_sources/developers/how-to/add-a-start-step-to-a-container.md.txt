# How to add a start step to a container

A portal often has work to do before its server starts, such as clearing expired sessions or loading reference data. You add a start step to run that work on every start of the web container, after the database is migrated and the static files are collected.

## Before you start

You have a [production image for your portal](deploy-a-portal-in-a-container.md), built from the portal Dockerfile.

## Steps

1. Write the step as an executable file. It can be a shell script or a Python script with a `#!/usr/bin/env python` first line. This one removes expired sessions.

   ```sh
   #!/bin/sh
   set -eu
   python manage.py clearsessions
   ```

2. Save it in your portal's repository as `docker-entrypoint.d/10-clear-sessions`. The steps run in the order of their file names, so prefix the names with numbers to choose the order.

3. Add one line to your portal's Dockerfile, after the `COPY` that puts your code in `/app`.

   ```dockerfile
   COPY --chmod=755 docker-entrypoint.d/ /docker-entrypoint.d/
   ```

   `--chmod=755` makes the file executable.

4. Rebuild the image and start the container.

   ```bash
   docker build --build-arg FAIRDM_IMAGE_VERSION=1.0.0 -t my-portal .
   docker run --rm --publish 8000:8000 --env-file /etc/my-portal/portal.env my-portal
   ```

## The result

The step runs on every start of the `web` command, after `migrate` and `collectstatic` and before gunicorn. It runs as the user `fairdm` in `/app` with the container's environment, and it can use `python manage.py` because the database has been migrated. Write it so it is safe to run again, because it runs on every start.

A step that exits with a non-zero status stops the start. The container exits with that status and the server does not start, as it does when `migrate` fails. A file that is not executable is skipped, and the container's log names it.

```text
skipping /docker-entrypoint.d/10-clear-sessions: not executable
```

The `worker` command and any other command run no start steps.

To try a step without rebuilding the image, mount a directory of steps when you run it.

```bash
docker run ... --volume "$PWD/docker-entrypoint.d:/docker-entrypoint.d:ro" my-portal
```

The container runs as user id 1000, so the mounted directory and its files must be readable by that user. A directory it cannot read counts as empty, and no step runs. To read the steps from another directory, set `FAIRDM_START_DIR`. All the rules for steps are in [Container images](../reference/container-images.md#start-steps).
