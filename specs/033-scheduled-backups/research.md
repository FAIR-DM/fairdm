# Research: scheduled, encrypted backups of the database and media

Investigated against main at 8265846d, with django-dbbackup 5.3.1, django-celery-beat 2.9.0 and
django-storages 1.14.6 as locked.

## Planning notes

### Ship the schedules as django-celery-beat entries

**Adopted.** `CELERY_BEAT_SCHEDULER` is already the database scheduler and django-celery-beat
registers its models on the admin site FairDM swaps in (`fairdm.contrib.admin.sites.CustomAdminSite`
is the default site, so `admin.site.register` in django-celery-beat lands there). Its periodic-task
changelist already has enable, disable and "Run selected tasks" actions, so changing, disabling and
running a backup at once need no FairDM screen. FairDM creates the two `PeriodicTask` rows, each on
a `CrontabSchedule` of minute 0, hour 3, day of week 0, in `TIME_ZONE`, from a `post_migrate`
receiver, creating a task only when none of its name exists. The database scheduler notices changes
made in the admin through its `PeriodicTasks.changed` marker, so a change takes effect without a
restart.

### Encrypt by default

**Adopted**, with GPG public-key encryption, which django-dbbackup supports through python-gnupg.
The details are below.

## Findings that change the plan

### FairDM's existing backup settings stop every backup

django-dbbackup 5 removed `DBBACKUP_STORAGE` and `DBBACKUP_STORAGE_OPTIONS`, and raises
`RuntimeError` whenever either is set (`dbbackup/settings.py:6-11`), so today every `dbbackup` and
`mediabackup` run fails. It now reads the `dbbackup` alias of `STORAGES`. The plan replaces both
settings with `STORAGES["dbbackup"]`, and the settings reference loses the two entries that
describe them. A portal that sets either name itself must move to `STORAGES["dbbackup"]`, and the
changelog says so. The design depends on 5.3 throughout, so 5.3 becomes the dependency's floor.

django-dbbackup reads all of its settings once, when `dbbackup.settings` is imported
(`settings.py:20-38`), and `Storage.__init__` applies `STORAGE_OPTIONS` over any options passed in
(`storage.py:65-67`). `override_settings` therefore does not reach it: tests patch the attributes
of `dbbackup.settings` directly.

### A media backup walks the whole media storage

`mediabackup` archives every file in the default storage. With backups in the media bucket under a
prefix, as FR-016 asks, each media backup would contain every earlier backup, and its size would
grow without bound. Locally this cannot happen with FairDM's settings: `MEDIA_ROOT` is
`BASE_DIR / "media"` and the backup directory is `BASE_DIR / "backups"` or `/var/lib/fairdm/backups`,
so only the shared-bucket case needs handling. FairDM's media backup must skip the backup prefix
when the backups share the media bucket. This
is done with a subclass of django-dbbackup's `mediabackup` command that overrides
`_explore_storage` and filters out the backup prefix. FairDM runs that subclass. It does not replace
the `mediabackup` command, so a portal that calls it directly keeps upstream behaviour.

### The time limits on tasks would kill every backup

`CELERY_TASK_TIME_LIMIT` is five minutes and `CELERY_TASK_SOFT_TIME_LIMIT` one minute, for every
task. A media archive of a real portal takes longer than a minute. The two backup tasks carry their
own limits: a soft limit of 5 h 50 min and a hard limit of 6 h.

### The server name changes with every container

django-dbbackup writes the host name into each file name. A container's host name changes on every
deployment. Cleanup does not filter by server name unless asked, so retention still counts every
file. File names are still easier to read with one stable name, so `DBBACKUP_HOSTNAME` is set from
`BACKUP_SERVER_NAME`, with `fairdm` as the default.

### Native dump format, and PostGIS

The connector django-dbbackup picks for the PostGIS engine, `PgDumpGisConnector`, writes plain SQL
and restores it with `psql`. `PgDumpBinaryConnector` writes PostgreSQL's custom format and restores
it with `pg_restore --single-transaction --clean --if-exists`. A custom-format dump carries
`CREATE EXTENSION postgis`, so it restores into an empty database. FairDM sets that connector for
the default database through `DBBACKUP_CONNECTORS`.

`dbrestore` decrypts the file before it runs `pg_restore`, so a wrong private key fails before the
database is touched. `dbbackup --clean` cleans up only after the new backup is written, so a failed
backup removes nothing. Both are tested rather than assumed.

### Encryption

- **Packages.** `python-gnupg` is a new dependency, and the `gnupg` Debian package goes into the
  runtime image. Debian 13 ships gnupg 2.4.7.
- **The key.** `BACKUP_PUBLIC_KEY` holds an ASCII-armoured public key. It is an environment variable
  rather than a mounted file, because every hosting choice has environment variables and not every
  one mounts files. Docker Compose accepts a quoted multi-line value.
- **The recipient.** django-dbbackup reads `DBBACKUP_GPG_RECIPIENT` when it is imported and passes
  it to `gnupg.GPG()` with the default home. FairDM's backup function imports the key into a keyring
  of its own (`GNUPGHOME` set for the duration of the call, under `DBBACKUP_TMP_DIR`), takes the
  fingerprint that gpg reports, and hands it to django-dbbackup as the recipient for that call. The
  portal configures only the key.
- **Trust.** The keyring holds only the one key the portal supplied, so it is always trusted. In
  5.3.1 the settings module assigns `GPG_ALWAYS_TRUST` and then overwrites it with
  `DBBACKUP_GPG_RECIPIENT` (`settings.py:29-30`), which FairDM never sets. The setting
  `DBBACKUP_GPG_ALWAYS_TRUST` therefore has no effect, and trust is off when the file is encrypted
  (`utils.py:192`). A key just imported into a fresh keyring has unknown trust, and gpg refuses it as
  a recipient. FairDM's backup function sets `dbbackup.settings.GPG_ALWAYS_TRUST = True` alongside
  the recipient for the call, and restores both afterwards.
- **A private key is refused.** A secret-key block also imports as a key that can encrypt. The check
  treats any secret key material in `BACKUP_PUBLIC_KEY` as unusable (`fairdm.E701`), so the portal
  never holds the key that decrypts its own backups.
- **Line breaks.** `BACKUP_PUBLIC_KEY` is read with `multiline=True`, so a value written with `\n`
  escapes on one line works as well as a quoted multi-line value.
- **Restoring.** Decryption uses gpg's default keyring. The developer imports the private key into
  the one-off container that runs the restore. The portal never holds it.
- **The production check.** FairDM imports `BACKUP_PUBLIC_KEY` into a temporary keyring and checks
  for a key that can encrypt. With no key it reports `fairdm.E700`, and with a key that cannot be
  used it reports `fairdm.E701`. Both are tagged `production_critical` and registered as deploy
  checks, like `fairdm.E001`, so `FairDMConfig.ready()` refuses to boot on them.
- **Development.** With no key, backups are written unencrypted.

### The warning about backups on the database's machine

`fairdm.W700` warns when the backup storage is a `FileSystemStorage`. It is not a deploy check. The
web start runs `migrate`, which runs the non-deploy checks and prints their warnings, so the warning
appears at every start. It is reported only when the resolved environment is production, and it
can be silenced through `SILENCED_SYSTEM_CHECKS`.

### Storage selection

| Media | Backups go to |
|---|---|
| local | `FileSystemStorage` at `BACKUP_DIR`. The default is `BASE_DIR / "backups"`, and the runtime image sets `/var/lib/fairdm/backups`, which it creates owned by `fairdm` |
| S3 | `S3Boto3Storage` with `location="backups"`, in the media bucket, or in `BACKUP_S3_BUCKET_NAME` when that is set |

The development stack gets a `backups` named volume. Retention is `BACKUP_KEEP`, which defaults to
4 and sets both `DBBACKUP_CLEANUP_KEEP` and `DBBACKUP_CLEANUP_KEEP_MEDIA`.

### Running the scheduler

The runtime image's start script gains a `beat` mode, `celery --app $CELERY_APP beat`, beside
`worker`. Beat reads the scheduler from settings. The development stack gets a `celerybeat` service,
and the deployment guide shows beat as a service of its own. One beat per portal is required, and
the guide says so.

### PostgreSQL client tools

FairDM's stack runs `postgis/postgis:17-3.5` (`[tool.fairdm] postgis` in `pyproject.toml`). Debian
13, which `python:3.13-slim` is built on, ships `postgresql-client-17` (17.11), and it goes into the
runtime image. The tests run in the development image, which inherits it, so the backup round trip
is tested where it will run, and CI's development-image build carries it with no change to the
workflow.

## What already exists

- Scheduling, the admin screens, enabling, disabling and "run now": **an installed package**,
  django-celery-beat. No new code.
- Dumping, restoring, archiving media, retention, listing backups, GPG: **an installed package**,
  django-dbbackup. No new code.
- S3 storage: **an installed package**, django-storages, the same backend media already uses.
- Production refusal and warnings: **this repo**, `fairdm/conf/checks.py`, `DeployTags`, and the
  aggregation in `fairdm/apps.py`.
- Seeding rows after migrate: **Django**, the `post_migrate` signal, as `fairdm/portal_roles.py`
  already does for the portal roles.
- Importing a key and reading its fingerprint: **an installed package** once added, python-gnupg.
- Skipping the backup prefix in a media archive: **new code**, a `_explore_storage` override on a
  subclass of django-dbbackup's media backup command. Upstream offers no exclusion option.
- Inspecting the key and handing its keyring, recipient and trust to django-dbbackup for one call:
  **new code**, one class in `fairdm/backups/keys.py`, used by both the check and the backup
  function.
- Two Celery tasks and a `backup` management command that call it: **new code**, thin.
- The `beat` start mode and the `celerybeat` service: **new code**, beside the existing `worker`
  mode and `celeryworker` service.
