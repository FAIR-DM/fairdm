# Tasks: scheduled, encrypted backups of the database and media

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md)

**Tests first**: in every group the test tasks come first, and each is seen to fail before the code
that makes it pass is written. The tests run in the development image built from the branch, so
any group that changes `docker/Dockerfile` rebuilds that image before its tests run. Wording and
appearance get no tests.

**Format**: `[ID] [Story] Description`.

**Order**: US1 Group 1, Group 2 and Group 3, then US2. Each starts from the previous group's
verified commit.

## Phase 1: US-1, a portal developer deploys a portal and it is backed up by default (P1)

### Group 1: backups run by default

- [ ] T001 [US1] `docker/Dockerfile`, runtime stage: add `postgresql-client-17` to the apt line,
  create `/var/lib/fairdm/backups` owned by `fairdm`, and set `ENV BACKUP_DIR=/var/lib/fairdm/backups`
  (FR-006, FR-007). Rebuild the development image. The tests below need `pg_dump` and `pg_restore`.
- [ ] T002 [US1] `tests/test_backups/test_defaults.py`: after the test database is created there is
  one enabled database task and one enabled media task, each on a crontab of minute 0, hour 3,
  Sunday, in `TIME_ZONE` (AS 1). Running the receiver again leaves a task whose schedule and
  enabled state were changed unchanged (AS 19). A deleted task is created again with the default
  schedule (AS 20). Running the database task through the periodic-task admin's "Run selected
  tasks" action, as a superuser on the portal's admin site, sends the task (AS 21). The periodic
  task changelist answers a superuser (FR-013).
- [ ] T003 [US1] `tests/test_backups/test_run.py`, with the `dbbackup` storage pointed at a
  temporary directory: `run_backup("database")` writes one database backup (AS 2), and
  `run_backup("media")` writes one media archive, counted separately (AS 3). A PostGIS database
  holding a sample with a location is backed up and restored with `pg_restore` into a freshly
  created empty database, and the sample and its point are there (AS 4, FR-002). With `BACKUP_KEEP`
  backups already present, a new successful backup removes the oldest and leaves the count unchanged,
  and media is counted on its own (AS 5). A backup whose dump fails raises, and every existing
  backup is still there (AS 6, FR-005). The `backup` command with no option writes one of each, and
  `--database-only` and `--media-only` write one (AS 21). A backup directory inside `MEDIA_ROOT` is
  absent from the media archive.
- [ ] T004 [US1] `tests/test_backups/test_storage_settings.py`: with media stored locally, the
  `dbbackup` storage is a `FileSystemStorage` at `BACKUP_DIR` (AS 11). `BACKUP_KEEP`,
  `BACKUP_SERVER_NAME` and the binary connector resolve as planned. A portal assigning its own
  `STORAGES["dbbackup"]` and `DBBACKUP_CLEANUP_KEEP` after `setup()` keeps its values (AS 7, FR-009).
  `DBBACKUP_STORAGE` is no longer set. Use the settings-resolution harness the existing
  `tests/test_conf/test_settings` tests use.
- [ ] T005 [US1] Settings: replace the backup block in `fairdm/conf/settings/database.py`, add
  `STORAGES["dbbackup"]` for local media in `static_media.py`, and declare the new environment
  variables (plan, Settings).
- [ ] T006 [US1] `fairdm/backups/`: `apps.py`, `defaults.py`, `run.py` without encryption,
  `media.py` with the local case, `tasks.py` with the time limits, and
  `management/commands/backup.py`. Add the app to `INSTALLED_APPS` after `dbbackup` and
  `django_celery_beat`.
- [ ] T007 [US1] Docs: `docs/developers/how-to/back-up-a-portal.md` (new), covering what runs by
  default, changing, disabling and running a task in the admin, and the `backup` command. Update the
  `docs/developers/reference/settings.md` backup entries and `management-commands.md`, add the
  page to the how-to index, and add a changelog entry.

### Group 2: encryption

- [ ] T008 [US1] Add `python-gnupg` to the runtime dependencies (`uv add`) and `gnupg` to the
  runtime stage's apt line, then rebuild the development image.
- [ ] T009 [US1] `tests/test_backups/conftest.py`: a session-scoped RSA 2048 key pair with no
  passphrase, generated in a temporary keyring. `tests/test_backups/test_encryption.py`: with
  `BACKUP_PUBLIC_KEY` set, a database backup and a media backup are each written encrypted to that
  key, and decrypting with the private key gives back a dump and an archive (AS 8, FR-010). With no
  key, in development, each is written unencrypted (AS 10, FR-012). After a backup,
  `dbbackup.settings.GPG_RECIPIENT` is what it was before.
- [ ] T010 [US1] `tests/test_conf/test_checks.py`: `fairdm.E700` is reported when there is no key,
  and `fairdm.E701` when the key is not an armoured public key or is a key with no encryption
  capability. Neither is reported for a usable key. A production boot (`FairDMConfig` aggregation)
  with no key refuses, and names the key alongside another production error (AS 9, FR-011).
- [ ] T011 [US1] `fairdm/backups/keys.py`, encryption in `run.py`, and the two checks in
  `fairdm/conf/checks.py`.
- [ ] T012 [US1] Docs: the key settings in `settings.md`, E700 and E701 in
  `docs/administrators/reference/configuration-checks.md`, and in the how-to, creating a key pair
  with `gpg`, supplying the public key, and keeping the private key off the portal. Changelog entry.

### Group 3: where backups go, and running the scheduler

- [ ] T013 [US1] `tests/test_backups/test_storage_settings.py`: with the `S3_*` variables set, the
  `dbbackup` storage is `S3Boto3Storage` in the media bucket with location `backups` (AS 12), or in
  `BACKUP_S3_BUCKET_NAME` when it is set (AS 13). With the media and backup storages sharing a
  bucket, the media archive leaves out everything under `backups/`, using an in-memory stand-in for
  the media storage. Retention given that storage lists and deletes only under the backup location
  (AS 14, FR-018).
- [ ] T014 [US1] `tests/test_conf/test_checks.py`: `fairdm.W700` is reported in production for a
  `FileSystemStorage` backup storage (AS 15), not for S3 (AS 16), not in development, and not when it
  is listed in `SILENCED_SYSTEM_CHECKS`. A production boot with only W700 still starts.
- [ ] T015 [US1] `tests/test_docker/test_entrypoint.py`: `beat` runs `celery --app <CELERY_APP>
  beat` with the extra arguments passed on, and none of the web steps.
- [ ] T016 [US1] S3 selection in `static_media.py`, the S3 case of `media.py`, the W700 check, and
  the `beat` mode in `docker/entrypoint.sh`.
- [ ] T017 [US1] `docker-compose.yml`: add a `celerybeat` service, add the `backups` volume to django,
  worker and beat, and set `BACKUP_DIR`. `docker/smoke-test.sh`: check the client is major version 17,
  that gpg runs, and that `beat` starts. Run the smoke test against the branch's images.
- [ ] T018 [US1] Docs: `BACKUP_DIR` and `BACKUP_S3_BUCKET_NAME` in `settings.md`, W700 in the
  checks reference, and in `container-images.md` the client tools, gnupg, the backup directory and
  the `beat` mode. Add the beat service, the backups volume and the key to
  `deploy-a-portal-in-a-container.md`, and say that one beat runs per portal. Changelog entry.

## Phase 2: US-2, a portal developer restores the portal from a backup (P2)

### Group 1

- [ ] T019 [US2] `tests/test_backups/test_restore.py`: `listbackups` lists the backups written,
  each with its date (AS 1). An encrypted database backup restored with `dbrestore --decrypt` and the
  private key, into a database changed since the backup, gives back the records at the time of the
  backup (AS 2). An encrypted media backup restored with `mediarestore --decrypt --replace` gives
  back the files (AS 3). A restore with a key that does not match fails, and the database and media
  are unchanged (AS 5).
- [ ] T020 [US2] Fix whatever T019 shows the commands need from FairDM's settings. Expect nothing
  beyond the private key being in gpg's default keyring.
- [ ] T021 [US2] Docs: `docs/developers/how-to/restore-a-portal-from-a-backup.md` (new), covering
  listing backups, importing the private key into a one-off container, restoring the database,
  restoring the media, and a trial restore into a separate, empty deployment that leaves the
  original untouched (AS 4, FR-020). Link it from the backup how-to and the index. Changelog entry.
