# Implementation Plan: Scheduled, encrypted backups of the database and media

**Branch**: `033-scheduled-backups` | **Date**: 2026-10-26 | **Spec**: [spec.md](spec.md) |
**Research**: [research.md](research.md)

## Summary

A new app, `fairdm.backups`, holds two Celery tasks, the function they share, a media backup
command subclass that skips the backup location, a `backup` management command, and the
`post_migrate` receiver that creates the two default periodic tasks. The settings move from the
removed `DBBACKUP_STORAGE*` names to `STORAGES["dbbackup"]`, chosen from the media storage. The
checks module gains `fairdm.E700`, `fairdm.E701` and `fairdm.W700`. The images gain
`postgresql-client-17`, `gnupg` and a backup directory, and the start script gains a `beat` mode. The
development stack gains a beat service and a backups volume. Documentation covers configuring,
taking, restoring and checking backups.

## Technical Context

**Language/Version**: Python 3.13, Django 6.0
**Primary Dependencies**: django-dbbackup 5.3 (present, and its floor becomes `>=5.3,<6`), django-celery-beat 2.9 (present),
django-storages (present), **python-gnupg (new)**
**Storage**: PostGIS 17. Backups go to a local directory or an S3 prefix
**Testing**: pytest, run in the development image built from the branch, against the PostGIS
service. The round trip needs `pg_dump`, `pg_restore` and `gpg` in that image, so the image change
comes first (Group 1)
**Target Platform**: the FairDM runtime and development images (Debian 13)
**Constraints**: the backup tasks override the global 1 min / 5 min task limits

## Constitution Check

- **Article I (Testing)**: every acceptance scenario becomes a test, except those that only
  docs can satisfy (US2 1–4), which are exercised by the documented commands under test as far as a
  test can go: list, decrypt, restore into an empty database. US1 AS 17 and 18 and SC-003 (a change
  in the admin takes effect without a restart) are django-celery-beat's database scheduler, and
  are not tested again here.
- **Article II/III (Simplicity, anti-abstraction)**: no storage abstraction of FairDM's own. The
  one subclass exists because upstream offers no exclusion.
- **Article V (Security & data safety)**: the private key never reaches the portal. Retention is
  confined to the backup location. Encryption is refused-or-on in production.
- **Article VII (Dependencies)**: python-gnupg is justified. django-dbbackup's encryption imports
  it. `deptry` stays green.
- **Article XIII/XIV (Configuration, production-grade defaults)**: backups work with no
  configuration beyond the key. Environment variables carry deployment facts only. Schedules live
  in the database (FR-015).
- **Article XVI (Docs as surface)**: every new environment variable, check, command and start mode
  is documented in the group that introduces it.
- **Article XVII (Demo)**: the demo runs in development, so it needs no key and gets unencrypted
  backups. No demo change.

**Result: pass.** There is nothing in the Complexity Tracking table.

## Design

### `fairdm/backups/` (new app, in `INSTALLED_APPS` after `dbbackup` and `django_celery_beat`)

- `apps.py`: `BackupsConfig`. `ready()` connects `seed_default_tasks` to `post_migrate`, with
  `sender` set to the `django_celery_beat` app config, so it runs once that app's tables exist.
- `signals.py` (the repo puts receivers in `signals.py`): the two default tasks as data,
  `DEFAULT_TASKS = [(name, task path), …]`, and the receiver `seed_default_tasks(**kwargs)`. For
  each name with no `PeriodicTask`, it creates the task on a `CrontabSchedule` of minute 0, hour 3,
  day of week 0, in `settings.TIME_ZONE` (the schedule is `get_or_create`d), and enables it. An
  existing task is never touched (FR-001, FR-014).
- `run.py`: `run_backup(kind: Literal["database", "media"]) -> None`.
  - If `settings.BACKUP_PUBLIC_KEY` is set, it runs inside `BackupKey(...).keyring()` (below) with
    `encrypt=True`. With no key, `encrypt=False`.
  - Database: `call_command("dbbackup", clean=True, compress=False, encrypt=…)`. The custom format is
    already compressed.
  - Media: in Groups 1 and 2 it runs `call_command("mediabackup", clean=True, compress=True,
    encrypt=…)`. Group 3 swaps in `SkippingMediaBackup` (below).
  - Any exception propagates, so the task fails (FR-005). A failed `pg_dump` raises a connector
    error, not `CommandError`, and django-dbbackup's wrapper re-raises it.
- `media.py` (Group 3): `SkippingMediaBackup`, a subclass of
  `dbbackup.management.commands.mediabackup.Command` whose `_explore_storage` drops every path under
  the backup location when the backup storage and the media storage are S3 storages in the same
  bucket. It decides this from the two storages' configured bucket and location, and never lists the
  bucket to find out. There is no local case: `MEDIA_ROOT` and the backup directory are siblings.
- `tasks.py`: `backup_database` and `backup_media`, `shared_task(soft_time_limit=21000,
  time_limit=21600)`, each calling `run_backup`.
- `management/commands/backup.py`: `backup [--database-only | --media-only]`, which calls
  `run_backup` in the foreground (FR-021).
- `keys.py`: one class, `BackupKey(armored)`, used by both the production check and `run_backup`.
  - `fingerprint`: imports the key into a temporary keyring and returns the fingerprint of a key that
    can encrypt, or `None`. It is `None` when the text holds any secret key material, either a
    `PRIVATE KEY BLOCK` armour header or a secret key in the import result, so a private key pasted
    into the setting is refused (`fairdm.E701`).
  - `keyring()`: a context manager that imports the key into a fresh `GNUPGHOME` under
    `DBBACKUP_TMP_DIR`, and sets `dbbackup.settings.GPG_RECIPIENT` to the fingerprint and
    `dbbackup.settings.GPG_ALWAYS_TRUST` to `True` for the call. On exit it restores `GNUPGHOME`
    and both settings and removes the keyring. Trust has to be set here: in django-dbbackup 5.3.1 the
    `DBBACKUP_GPG_ALWAYS_TRUST` setting is overwritten at import (`dbbackup/settings.py:29-30`), and
    gpg refuses an untrusted recipient.

### Settings: `fairdm/conf/settings/database.py` (backup block replaced)

```python
BACKUP_PUBLIC_KEY = env.str("BACKUP_PUBLIC_KEY", default="", multiline=True)
DBBACKUP_HOSTNAME = env("BACKUP_SERVER_NAME", default="fairdm")
DBBACKUP_CLEANUP_KEEP = DBBACKUP_CLEANUP_KEEP_MEDIA = env.int("BACKUP_KEEP", default=4)
DBBACKUP_CONNECTORS = {"default": {"CONNECTOR": "dbbackup.db.postgresql.PgDumpBinaryConnector"}}
# filename templates kept as they are
```

There is no `DBBACKUP_GPG_ALWAYS_TRUST`: it has no effect in 5.3.1, and `BackupKey.keyring()` sets
trust for the call.

django-dbbackup reads its settings once, at import, so `override_settings` does not reach it. Tests
patch the attributes of `dbbackup.settings` (`STORAGE`, `STORAGE_OPTIONS`, `CLEANUP_KEEP`,
`CLEANUP_KEEP_MEDIA`) with `monkeypatch`, pointing the storage at a `tmp_path`. Every test that runs
a backup or restore command uses `transactional_db`: `pg_dump` and `pg_restore` use their own
connections, and each command closes Django's connection when it finishes.

`STORAGES["dbbackup"]` is set in `static_media.py`, after the media storage is chosen, because it
depends on that choice:

- media on S3: `S3Boto3Storage` with `OPTIONS = {"bucket_name": env("BACKUP_S3_BUCKET_NAME") or
  AWS_STORAGE_BUCKET_NAME, "location": "backups"}`
- otherwise: `FileSystemStorage` with `OPTIONS = {"location": env("BACKUP_DIR", default=str(BASE_DIR / "backups"))}`

`DBBACKUP_STORAGE` and `DBBACKUP_STORAGE_OPTIONS` are removed. A portal that assigns its own
`STORAGES["dbbackup"]` or `DBBACKUP_*` after `setup()` wins (FR-009).

The environment variables need declaring where `env` declares its defaults. They go in the same
place and file as the existing `S3_*` declarations.

### Checks: `fairdm/conf/checks.py`

- `fairdm.E700`: no `BACKUP_PUBLIC_KEY`. `fairdm.E701`: `BackupKey.fingerprint` is `None` (not a
  usable public key, or secret key material), or gpg is missing. Both are registered with `DeployTags.deploy, DeployTags.production_critical,
  deploy=True`, as `check_debug_false` is.
- `fairdm.W700`: the `dbbackup` storage backend is `FileSystemStorage`, and the resolved environment
  is production (the same test `FairDMConfig` uses). Registered without `deploy=True`, so `migrate`
  in the start sequence reports it.
- Tests settings run in development, so neither error fires in the suite unless a test asks.

### Images and stack

- `docker/Dockerfile`, runtime stage: add `postgresql-client-17 gnupg` to the apt line. Create
  `/var/lib/fairdm/backups` owned by `fairdm`. Add `ENV BACKUP_DIR=/var/lib/fairdm/backups`.
- `docker/entrypoint.sh`: add `beat)`, `shift`, `exec celery --app "${CELERY_APP:-config}" beat
  "$@"`, and document it in the header comment.
- `docker/smoke-test.sh`: assert that `pg_dump --version` reports 17 and that `gpg --version` runs
  in the runtime image, and that the `beat` mode starts Celery beat.
- `docker-compose.yml`: add a `celerybeat` service like `celeryworker`, running `celery --app
  fairdm.conf.celery beat --loglevel INFO`, and a `backups` named volume mounted at
  `/var/lib/fairdm/backups` on the django, worker and beat services. `BACKUP_DIR` needs no entry:
  the development image inherits it from the runtime stage.

### Documentation

| Page | Group |
|---|---|
| `docs/developers/reference/settings.md`: remove the `DBBACKUP_STORAGE*` entries, add `BACKUP_SERVER_NAME`, `BACKUP_KEEP` and `DBBACKUP_CONNECTORS`, and update `DBBACKUP_CLEANUP_KEEP` | 1 |
| `docs/developers/reference/management-commands.md`: `backup` | 1 |
| `docs/developers/how-to/back-up-a-portal.md` (new): what is backed up by default, changing or disabling a schedule and running one at once in the admin, the command in a container | 1, grown in 2 and 3 |
| `docs/developers/reference/settings.md`: `BACKUP_PUBLIC_KEY` | 2 |
| `docs/administrators/reference/configuration-checks.md`: E700, E701 | 2 |
| how-to section: creating the key pair, where to keep the private key | 2 |
| `docs/developers/reference/settings.md`: `BACKUP_DIR`, `BACKUP_S3_BUCKET_NAME` | 3 |
| `docs/administrators/reference/configuration-checks.md`: W700 | 3 |
| `docs/developers/reference/container-images.md`: the client tools, gnupg, `BACKUP_DIR`, the `beat` mode | 3 |
| `docs/developers/how-to/deploy-a-portal-in-a-container.md`: the beat service, the backups volume, the key | 3 |
| `docs/developers/how-to/restore-a-portal-from-a-backup.md` (new): listing backups, restoring the database and the media, a trial restore into a separate deployment | US2 |
| `docs/changelog.md` entries. Breaking for upgrades, and said so: a portal's own `DBBACKUP_STORAGE*` must move to `STORAGES["dbbackup"]` (1), production now requires `BACKUP_PUBLIC_KEY` and gpg in a custom image (2) | every group |

Each new page goes into its section's index and the `toctree` there.

## Project Structure

```text
fairdm/backups/
├── __init__.py
├── apps.py
├── signals.py
├── keys.py
├── media.py             # Group 3
├── run.py
├── tasks.py
└── management/commands/backup.py
tests/test_backups/
├── conftest.py          # a gpg key pair generated once per session; dbbackup.settings patched to a tmp_path storage
├── test_signals.py
├── test_run.py          # round trip, retention, failure, encryption, and TestRestore (US2)
├── test_keys.py
├── test_media.py        # Group 3: the shared-bucket prefix is skipped
└── test_management/test_commands/test_backup.py
tests/test_conf/test_settings/test_database.py      # backup settings resolution (existing module)
tests/test_conf/test_settings/test_static_media.py  # STORAGES["dbbackup"] selection (existing module)
tests/test_conf/test_checks.py                       # E700, E701, W700 (existing module)
```

The test tree mirrors the source tree, as the repo's testing standard requires.

## Risks the build must watch

- `post_migrate` runs under `--no-migrations` too, once the test database is created, so the
  receiver must not fail when tables are created by syncdb. It is safe as written, because it runs
  after `django_celery_beat`'s tables exist.
- The round-trip test restores into a second, empty PostGIS database. It creates and drops that
  database itself and needs the `CREATEDB` privilege the test role already has.
- Generating a GPG key in tests is slow. Generate one RSA 2048 key per session, with no passphrase.
- The encryption test must encrypt through the keyring `BackupKey.keyring()` builds, never the
  conftest keyring that generated the pair: that keyring trusts its own key ultimately, so a test
  using it cannot fail if trust is left off.
