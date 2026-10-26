# Feature Specification: Scheduled, encrypted backups of the database and media

**Feature Branch**: `033-scheduled-backups`

**Created**: 2026-10-26

**Status**: Draft

**Goals**: G16: a research group with no operations staff can deploy and run its own portal. G7:
development and production settings stay out of a portal's way while remaining configurable where
it matters.

**Roadmap**: R26, a research group can deploy the shipped stack. This is the backups slice of it.
The production stack of services, upgrades, log access and the first-run path stay with the rest of
R26.

**Input**: #601. A FairDM portal backs up its database and its uploaded media on a schedule out of
the box. The schedules are ordinary periodic tasks that a portal developer changes, or turns off, in
the administration interface. Backups are encrypted by default, go off the machine whenever the
portal already stores media off it, and are pruned so only a set number are kept. The
documentation explains how to back up, restore, and check that a backup restores. Takes in #597.

## What exists, and what this specification changes

FairDM installs django-dbbackup and names it in `INSTALLED_APPS`. Its settings send backups to a
fixed local directory, `/app/dbbackups/`, and keep the last ten. Nothing else is in place:

- nothing ever starts a backup, so a portal has backups only if someone runs the command by hand
- neither base image carries the PostgreSQL client tools, so that command cannot back up the
  database inside a container (#597)
- the runtime image starts a web server or a background worker, and nothing runs the scheduler
  that periodic tasks depend on
- the backup directory is inside the container and on no volume, so a backup is lost with the
  container that made it
- backups are not encrypted
- no page of the documentation mentions backups or restores

The periodic task scheduler is already installed and keeps its schedules in the database, where
they can be edited in the administration interface. No FairDM task uses it yet.

After this feature:

- A newly deployed portal backs up its database and its media every week, encrypted, with no
  backup configuration written by the portal.
- The two schedules are periodic tasks that a portal developer changes or turns off in the
  administration interface.
- A portal whose media is stored off the machine keeps its backups off the machine too, and a
  production portal whose backups would stay on the database's machine is warned at start-up.
- The base images can back up and restore a PostGIS database, and a portal can run the scheduler
  from the runtime image.
- The documentation covers taking a backup by hand, restoring one, and checking that one restores.

## Boundary

- **The rest of R26**: the production stack of services, upgrades, log access and the first-run
  path from an empty database.
- **Restoring from the administration interface**: restores stay a documented command. A restore
  replaces the whole database, and it is not offered as a button.
- **Backups of anything but the default database and the media files**: static files are
  rebuilt at every start, and caches and the message broker hold nothing that needs keeping.
- **Storage services other than a local directory and S3-compatible object storage**: a portal
  that wants another one names any Django storage itself, through the settings it already has.

## Clarifications

### Session 2026-10-26

Each question was answered from the maintainer's replies while the feature was agreed, without
putting it to him again. The longer reasoning is in [decisions.md](decisions.md).

- Q: Where does a portal change how often backups run? → A: In the administration interface's
  periodic tasks, and nowhere else. FairDM ships one periodic task for the database and one for the
  media, each weekly on Sunday at 03:00 in the portal's time zone. Neither schedule is an
  environment variable or a setting. The maintainer ruled out environment variables and cron
  strings as not user friendly.
- Q: What happens to a schedule someone has changed when the database is brought up to date
  again? → A: Nothing. The two default tasks are created only when they do not exist, and an
  existing task is never reset. A task that has been deleted is created again on the next update,
  so the way to stop a backup is to disable its task.
- Q: What happens in production when no encryption key is supplied? → A: The portal refuses to
  start, with the other production-critical checks. Backups are encrypted by default, and FairDM
  ships no working default for a security-critical value. In development a portal without a key
  makes unencrypted backups, so the development stack needs no key to try backups.
- Q: Is the warning about backups on the database's machine an error? → A: No, a warning. A group
  may copy its backup directory off the machine by other means, and it can silence the warning in
  the usual way.
- Q: When media is in S3, are its backups stored in the same bucket? → A: By default, yes, under
  a prefix of their own, so a portal that already stores media off the machine needs no new
  credentials. A portal can name a different bucket for backups. The documentation recommends one,
  since a backup kept in the bucket it protects is lost along with that bucket.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A portal developer deploys a portal and its database and media are backed up every week (Priority: P1)

A portal developer deploys a portal on FairDM's images, with the scheduler running beside the web
server and the worker as the deployment guide shows. They write no backup configuration. Every
week the portal backs up its database and, separately, its media files, and keeps only the most
recent backups of each.

**Why this priority**: this is the feature. Everything else adjusts where, when or how the backups
it produces are kept.

**Independent Test**: start a portal from the documented stack against an empty PostGIS database,
run the two default tasks' backups, and find one database backup and one media backup in the
backup location.

**Acceptance Scenarios**:

1. **Given** a portal whose database has just been brought up to date for the first time,
   **When** a developer lists its periodic tasks, **Then** there is one enabled task that backs up
   the database and one that backs up the media, each due weekly on Sunday at 03:00 in the portal's
   time zone.
2. **Given** a portal deployed on the runtime image with the scheduler running, **When** a
   database backup task falls due, **Then** a backup of the database is written to the backup
   location.
3. **Given** the same portal, **When** a media backup task falls due, **Then** an archive of the
   media files is written to the backup location, separate from the database backup.
4. **Given** a PostGIS database holding records with locations, **When** it is backed up and the
   backup is restored into an empty database, **Then** the records and their locations are
   present.
5. **Given** a backup location that already holds the configured number of database backups,
   **When** a new database backup succeeds, **Then** the oldest database backup is removed and the
   number kept does not change. Media backups are counted and removed on their own.
6. **Given** a backup run that fails, **When** it ends, **Then** no existing backup has been
   removed, and the failure is reported as a failed task.
7. **Given** a portal that configures none of the backup location, **When** it is deployed in a
   container, **Then** backups are written to a location that survives the container being
   replaced.
8. **Given** a portal that already sets its own backup settings, **When** settings resolve,
   **Then** the portal's values win over FairDM's.

---

### User Story 2 - A portal developer supplies the key the backups are encrypted with (Priority: P1)

A portal developer gives the portal a public encryption key through its environment. Every backup,
database and media alike, is encrypted with it, so a backup is unreadable to anyone who holds the
file but not the private key. A production portal given no key refuses to start.

**Why this priority**: backups hold every record and every person's details, including those that
are private. They are copied to places with weaker access control than the database, so they are
encrypted from the first one.

**Independent Test**: configure a key, take a backup, and check that the file cannot be read
without the private key and restores with it. Then start a production portal without a key and
check that it refuses.

**Acceptance Scenarios**:

1. **Given** a portal configured with a public key, **When** a database or media backup is taken,
   **Then** the backup is encrypted to that key.
2. **Given** an encrypted backup and the matching private key, **When** a developer restores it
   following the documentation, **Then** the restore succeeds.
3. **Given** a production portal with no encryption key, **When** it starts, **Then** it refuses
   to start and the message names the missing key alongside any other production problem.
4. **Given** a development portal with no encryption key, **When** a backup is taken, **Then** it
   is written unencrypted and the portal starts normally.
5. **Given** a key that is not a usable public key, **When** a production portal starts, **Then**
   it refuses to start and says the key cannot be used.

---

### User Story 3 - A portal developer changes or turns off a backup schedule in the administration interface (Priority: P1)

A portal developer decides weekly is wrong for their portal: a busy database every night, a large
media store once a month, or no media backups at all because the storage service keeps its own
copies. They change or disable the task in the administration interface's periodic tasks, and the
change holds through every later deployment.

**Why this priority**: a single schedule fits few portals, and the maintainer chose this screen as
the one place a schedule is changed.

**Independent Test**: change the database task's schedule and disable the media task in the
administration interface, bring the database up to date again, and check that both changes still
stand and that the scheduler follows them.

**Acceptance Scenarios**:

1. **Given** the default database task, **When** a developer gives it another schedule in the
   administration interface, **Then** the next backup runs on the new schedule without the portal
   being redeployed or restarted.
2. **Given** a developer has disabled the media task, **When** its old schedule comes round,
   **Then** no media backup is taken.
3. **Given** a changed or disabled task, **When** the database is brought up to date again,
   **Then** the task keeps the developer's schedule and its enabled state.
4. **Given** a developer has deleted a default task, **When** the database is brought up to date
   again, **Then** the task exists again with its default schedule.

---

### User Story 4 - A portal developer whose media is in S3 gets backups off the machine with no extra setup (Priority: P2)

A portal developer already stores the portal's media in an S3 bucket. Without configuring
anything for backups, the backups go to that bucket under a prefix of their own. A developer who
wants them elsewhere names a different bucket. A production portal whose backups would stay on
the machine its database runs on is warned at every start.

**Why this priority**: a backup on the machine it protects is lost with that machine, so a portal
needs off-site backups. Most portals can still run safely without this story, which is why it is
P2 rather than P1.

**Independent Test**: start a portal with S3 media configured, take a backup, and find it under
the backup prefix in the media bucket. Then start a production portal with local backups and read
the warning.

**Acceptance Scenarios**:

1. **Given** a portal storing media in S3, **When** a backup is taken, **Then** it is written to
   the media bucket under a prefix that holds only backups, and no media file is overwritten.
2. **Given** a portal storing media in S3 that names a separate backup bucket, **When** a backup is
   taken, **Then** it is written to that bucket.
3. **Given** a production portal whose backups go to a local directory, **When** it starts,
   **Then** a warning says its backups are kept on the machine they protect, and the portal still
   starts.
4. **Given** a production portal whose backups go to S3, **When** it starts, **Then** no such
   warning is given.
5. **Given** a portal that silences the warning, **When** it starts, **Then** the warning is not
   shown.
6. **Given** a portal storing media in S3, **When** retention removes old backups, **Then** only
   backups are removed, never media files.

---

### User Story 5 - A portal developer restores the portal from a backup (Priority: P2)

Something has gone wrong: records were deleted by mistake, or the machine is gone. The portal
developer finds the backups they have, picks one, and restores the database and the media from it
by following the documentation. They have also practised it beforehand: the documentation shows
them how to restore a backup into a separate, empty portal to check that their backups restore.

**Why this priority**: a backup that cannot be restored is not a backup. It is P2 because the
tools to restore exist once US1 does, and this story makes their use dependable for someone who
has never done it.

**Independent Test**: follow the restore guide from a fresh deployment and an encrypted backup of
another portal, and check that the restored portal shows the original records and files.

**Acceptance Scenarios**:

1. **Given** a backup location with several backups, **When** a developer follows the
   documentation, **Then** they can list the available backups with their dates and choose one.
2. **Given** an encrypted database backup and its private key, **When** the developer restores it
   into the portal following the documentation, **Then** the portal's records are those at the
   time of the backup.
3. **Given** an encrypted media backup and its private key, **When** the developer restores it
   following the documentation, **Then** the media files are those at the time of the backup.
4. **Given** a separate, empty deployment, **When** a developer follows the documentation's check
   that a backup restores, **Then** they end with a portal whose records and files match the
   backup, and the portal the backup came from is untouched.

---

### User Story 6 - A portal developer takes a backup by hand before an upgrade (Priority: P3)

Before moving the portal to a new FairDM version, the portal developer takes a database and media
backup there and then, rather than relying on last Sunday's. The backup is encrypted, stored and
counted like a scheduled one.

**Why this priority**: an upgrade migrates the database, and the routine R26 asks for begins with a
backup. Scheduled backups already make this possible by hand with the same commands, so it ranks
lowest.

**Independent Test**: run the documented commands in a running container and find a new
encrypted backup of each kind in the backup location.

**Acceptance Scenarios**:

1. **Given** a running portal, **When** the developer runs the documented backup commands in its
   container, **Then** one new database backup and one new media backup are written to the backup
   location, encrypted like scheduled ones.
2. **Given** backups taken by hand, **When** retention next runs, **Then** they are counted along
   with scheduled backups.

---

### Edge Cases

- **The scheduler is not running.** Nothing falls due and no backup is taken. The deployment guide
  shows the scheduler as part of the stack, and the restore guide's first step lists the backups
  that exist, so a missing scheduler shows up as missing backups rather than staying hidden.
- **The backup location cannot be reached** (a full disk, wrong S3 credentials, a missing bucket).
  The task fails, is reported as a failed task, and removes nothing.
- **Two backups of the same kind run at once**, for instance a backup by hand started while a
  scheduled one is running. Each writes its own file. Neither replaces the other.
- **Media is in S3 and very large.** The media backup still runs weekly by default. A developer
  who relies on the storage service's own versioning disables the media task (US3).
- **An empty media store.** The media backup produces an empty archive and succeeds.
- **The portal's time zone changes.** The default tasks keep the time zone they were created
  with. A developer changes it in the administration interface like any other schedule.
- **A restore with the wrong private key.** The restore fails before the database is touched.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001** (US1): When a portal's database is brought up to date, FairDM MUST create a periodic
  task that backs up the database and one that backs up the media, if they do not already exist.
  Each is enabled and due weekly on Sunday at 03:00 in the portal's time zone.
- **FR-002** (US1): A database backup MUST be one that restores a PostGIS database completely,
  including its geospatial data.
- **FR-003** (US1): A media backup MUST be a single archive of the media files, written and counted
  separately from database backups.
- **FR-004** (US1): After each successful backup, the backups of that kind beyond the number to
  keep MUST be removed, oldest first. The number to keep defaults to four of each kind and can be
  changed through the portal's environment.
- **FR-005** (US1): A failed backup MUST NOT remove any existing backup and MUST end as a failed
  task.
- **FR-006** (US1): With no backup location configured and media stored locally, backups MUST be
  written to a local directory that the documented container stack keeps on a named volume.
- **FR-007** (US1): Both base images MUST carry PostgreSQL client tools able to back up and restore
  the PostgreSQL major version FairDM's stack runs.
- **FR-008** (US1): The runtime image MUST be able to run the periodic task scheduler, and the
  documented stack MUST run it.
- **FR-009** (US1): Backup settings a portal assigns itself MUST win over FairDM's, under the
  precedence order of `fairdm.setup()`.
- **FR-010** (US2): When the portal's environment supplies a public encryption key, every backup,
  database and media alike, MUST be encrypted to it.
- **FR-011** (US2): In production, a portal with no encryption key, or with one that cannot be
  used, MUST refuse to start, reported with the other production-critical checks.
- **FR-012** (US2): In development, a portal with no encryption key MUST make unencrypted backups
  and start normally.
- **FR-013** (US3): The schedule and enabled state of each default task MUST be changeable in the
  administration interface, and a change MUST take effect without a redeploy or restart.
- **FR-014** (US3): Bringing the database up to date MUST NOT change the schedule or enabled state
  of a default task that already exists.
- **FR-015** (US3): When a backup runs MUST be decided by its periodic task alone. No environment
  variable or setting decides it.
- **FR-016** (US4): When media is stored in S3 and no backup location is configured, backups MUST
  be written to the media bucket under a prefix that holds only backups.
- **FR-017** (US4): A portal MUST be able to send backups to a different S3 bucket through its
  environment.
- **FR-018** (US4): Removing old backups MUST NOT remove anything outside the backup location.
- **FR-019** (US4): In production, a portal whose backups go to a local directory MUST be warned at
  start-up that its backups are kept on the machine they protect. The warning MUST NOT stop the
  start, and MUST be silenceable like any other system check.
- **FR-020** (US5): The documentation for portal developers MUST explain how to list backups,
  restore the database, restore the media, and check that a backup restores into a separate
  deployment, including the encryption keys each step needs.
- **FR-021** (US6): The documentation MUST give the commands that take a database and a media
  backup by hand in a running container. Those backups MUST be encrypted, stored and counted like
  scheduled ones.

### Key Entities

- **Default backup task**: one of the two periodic tasks FairDM creates, one for the database and
  one for the media. A portal developer owns its schedule and enabled state from the moment it
  exists.
- **Backup location**: where backups are written. A local directory on a named volume, or a prefix
  in an S3 bucket.
- **Off-site backup**: a backup kept somewhere other than the machine the database runs on. A
  backup in S3 is off-site, and a local directory is not.
- **Encryption key**: the public key every backup is encrypted to. The matching private key is
  needed to restore a backup and is kept away from the portal.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A portal deployed by following the deployment guide, with no backup setting written,
  holds one encrypted database backup and one encrypted media backup after the first run of its
  default tasks.
- **SC-002**: Following the restore guide on an empty deployment returns every record and media
  file present when the backup was taken, checked against the original portal.
- **SC-003**: A schedule changed in the administration interface is followed at its next due time,
  with no redeploy or restart.
- **SC-004**: Every production start without a usable encryption key is refused.
- **SC-005**: The number of backups of each kind never exceeds the number to keep after a
  successful run, and a failed run removes none.
- **SC-006**: After any number of database updates, a developer's changes to a default task stand
  unchanged.

## Assumptions

- The portal runs FairDM's documented container stack or an equivalent one that runs a Celery
  worker and the scheduler. A portal that runs neither gets no scheduled backups, and the
  deployment guide says so.
- Restoring is done by a portal developer with shell access to a container, not by a person using
  the administration interface.
- The encryption key pair is created and kept by the group that runs the portal. FairDM never
  generates, stores or sends a private key.
- Weekly is the default because the maintainer judged nightly too often for a typical research
  portal. Portals that need more often change it under US3.
