# How to back up a portal

A portal backs up its database and its media every week without any configuration. You change when a backup runs, switch one off, run one at once, or write one from the command line.

## Before you start

- The portal runs a Celery worker and Celery beat, the process that sends scheduled tasks. A portal started from the compose files in the FairDM repository runs the worker. Start beat with `celery --app fairdm.conf.celery beat --loglevel INFO`, from the same image and environment as the worker. Without beat, the tasks below exist but nothing sends them.
- You can sign in to the admin as a superuser.

## What runs by default

Migrating the portal creates two periodic tasks. You see them in the admin under **Periodic tasks**.

| Task | Does |
| --- | --- |
| Back up the database | Writes a dump of the database in PostgreSQL's custom format |
| Back up the media | Writes a compressed archive of the media files |

Each runs on Sunday at 03:00 in the portal's [`TIME_ZONE`](../reference/settings.md#time_zone). The backups go to the directory in [`BACKUP_DIR`](../reference/settings.md#backup_dir), `/var/lib/fairdm/backups` in the container images. After each backup the oldest beyond [`BACKUP_KEEP`](../reference/settings.md#backup_keep) are removed, four of each kind by default.

```{warning}
Mount a volume at the backup directory. Without one, the backups are lost when the container is replaced.
```

FairDM creates a task only when it is missing. A schedule you change, or a task you switch off, stays as you left it after the next migration.

## Steps

1. Change when a backup runs. Open the task in the admin under **Periodic tasks**, choose another crontab schedule or add one, and save. Celery beat picks the change up without a restart.

2. Switch a backup off. Untick **Enabled** on the task and save. Delete the task and the next migration creates it again with the default schedule, so untick it instead.

3. Run a backup at once. In the **Periodic tasks** list, tick the task, choose **Run selected tasks** and apply it. A worker runs the backup.

4. Write a backup from the command line, in a running container.

   ```bash
   docker exec my-portal-web python manage.py backup
   ```

   Add `--database-only` or `--media-only` to write one of the two. See [`backup`](../reference/management-commands.md#backup).

5. Keep more or fewer backups. Set `BACKUP_KEEP` in the environment to the number of backups of each kind to keep.

## If your portal sets its own backup storage

django-dbbackup 5 no longer reads `DBBACKUP_STORAGE` and `DBBACKUP_STORAGE_OPTIONS`, and refuses to start when either is set. Move the choice to `STORAGES["dbbackup"]` in your settings.

```python
STORAGES["dbbackup"] = {
    "BACKEND": "django.core.files.storage.FileSystemStorage",
    "OPTIONS": {"location": "/mnt/backups"},
}
```
