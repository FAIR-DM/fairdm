# How to back up a portal

A portal backs up its database and its media every week without any configuration. You change when a backup runs, switch one off, run one at once, or write one from the command line.

## Before you start

- The portal runs a Celery worker and Celery beat, the process that sends scheduled tasks. A portal started from the compose files in the FairDM repository runs the worker. Start beat with `celery --app fairdm.conf.celery beat --loglevel INFO`, from the same image and environment as the worker. Without beat, the tasks below exist but nothing sends them.
- You can sign in to the admin as a superuser.

## What runs by default

Migrating the portal creates two periodic tasks. You see them in the admin under **Periodic tasks**.

| Task | Does |
| --- | --- |
| Back up the database (`fairdm.backups.tasks.backup_database`) | Writes a dump of the database in PostgreSQL's custom format |
| Back up the media (`fairdm.backups.tasks.backup_media`) | Writes a compressed archive of the media files |

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

## Encrypt the backups

A production portal encrypts every backup to a public key, and refuses to start without one (see [`fairdm.E700`](../../administrators/reference/configuration-checks.md#fairdm-e700-no-backup-public-key-is-set) and [`fairdm.E701`](../../administrators/reference/configuration-checks.md#fairdm-e701-the-backup-public-key-cannot-be-used)). The portal holds only the public key, so a stolen backup is unreadable and the server cannot decrypt its own backups. A development portal with no key writes unencrypted backups.

1. Create a key pair on your own computer, not on the portal's server.

   ```bash
   gpg --quick-generate-key "My Portal Backups <backups@example.org>" rsa4096 encr never
   ```

   Give the key a passphrase when gpg asks.

2. Export the public key.

   ```bash
   gpg --armor --export backups@example.org
   ```

3. Set `BACKUP_PUBLIC_KEY` in the portal's environment to the whole output, from `-----BEGIN PGP PUBLIC KEY BLOCK-----` to `-----END PGP PUBLIC KEY BLOCK-----`. In an env file the value may span several lines inside quotes.

4. Keep the private key off the portal. Export it with `gpg --armor --export-secret-keys backups@example.org`, store it in a password manager or on an offline medium, and keep a copy apart from the backups. Whoever loses the private key cannot read any backup made with the public key. The portal refuses a private key in `BACKUP_PUBLIC_KEY`.

5. Check it. `python manage.py check --deploy` reports no `fairdm.E700` or `fairdm.E701`, and the next backup file ends in `.gpg`.

The images FairDM publishes carry `gpg`. A custom image needs the `gnupg` package.

## Run a backup from your own code

`run_backup` writes one backup, the same one the task and the command write. It takes `"database"` or `"media"` and raises when the backup fails.

```python
from fairdm.backups.run import run_backup

run_backup("database")
```

The two tasks, `backup_database` and `backup_media`, call it and carry their own time limits of 5 hours 50 minutes soft and 6 hours hard, in place of the one minute and five minutes every other task has.

## If your portal sets its own backup storage

django-dbbackup 5 no longer reads the two storage settings of the 4.x series, and refuses to start when either is set. Move the choice to `STORAGES["dbbackup"]` in your settings.

```python
STORAGES["dbbackup"] = {
    "BACKEND": "django.core.files.storage.FileSystemStorage",
    "OPTIONS": {"location": "/mnt/backups"},
}
```
