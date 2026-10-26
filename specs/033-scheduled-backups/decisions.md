# Decisions: scheduled, encrypted backups of the database and media

Rationale too long to keep in the specification, and every ambiguity resolved while it was written.

## Which backup package

FairDM keeps django-dbbackup, which it already depends on. A different package with a similar
name, django-db-backups, was considered and set aside: it is at version 0.1, stores backups only
on local disk or Dropbox, describes itself as a minimal implementation for its author's own use,
and installs management commands with the same names as django-dbbackup's, so the two cannot be
installed together. The maintainer confirmed django-dbbackup was the package he meant.

## Schedules live in the periodic task table, not in configuration

An earlier reading made each schedule an environment variable holding a cron expression. The
maintainer rejected it: "This is not user friendly. We already include celery_beat which I'm
pretty sure allows portal devs to set task schedules in the admin site. We should be shipping items
in celery_beat by default, then a dev can change it in the admin site if required."

FR-015 follows from that. If a setting could also decide a schedule, there would be two places a
schedule comes from, and a change in the administration interface could be undone by a deployment.

## Created when missing, never reset

The default tasks must exist without anyone creating them, and a developer's changes must survive
every later deployment. Creating each task only when no task of its name exists does both. The cost
is that a deleted task comes back on the next database update. That is accepted: the task's enabled
state is the supported way to stop a backup, and it is what the documentation shows.

## Weekly, Sunday 03:00

The maintainer judged nightly too often for a typical research portal. Sunday 03:00 in the
portal's own time zone avoids working hours for most groups. Retention defaults to four of each
kind, a month of weekly backups, replacing the ten that the existing settings keep.

## Encrypted by default, refused in production without a key

The maintainer asked for backups to be encrypted by default. FS-001 already rules that the
baseline never supplies a working default for a security-critical value and that a production
portal omitting one refuses to start. An encryption key is such a value, so a production portal
without one refuses to start (FR-011). A development portal makes unencrypted backups instead, so
that the development stack can try backups with no key to manage (FR-012).

Encryption is to a public key. The portal holds only the public half, so a portal that is
compromised does not expose its own past backups.

## A warning, not an error, for backups on the database's machine

Some groups copy a backup directory off the machine with tools of their own. Refusing to start
would force them to fake an off-site location. The warning is a system check like the others, so
`SILENCED_SYSTEM_CHECKS` silences it.

## The backup bucket when media is in S3

The default is the media bucket under a prefix holding only backups, so a portal that already has
S3 credentials needs nothing new. A backup in the bucket it protects shares that bucket's fate, so a
separate bucket can be named (FR-017) and the documentation recommends one. Retention is confined to
the backup prefix (FR-018), because a pruning step that could reach media files would be the most
dangerous part of the feature.

## One name for the person who deploys

During agreement a new term, "portal operator", was proposed for whoever runs the deployment,
because "Portal Administrator" is already a portal role. FairDM's documentation already splits its
readers: portal developers build and deploy a portal, and administrators look after a running one
through the administration interface. The deployer is a portal developer, and the maintainer
described the person changing a schedule as "a dev". The specification uses "portal developer"
throughout and adds no new term, keeping one name for one thing.

## #597 is taken in

#597 reports that neither image has a PostgreSQL client, so no backup can run in a container. That
gap is a precondition of this feature rather than a separate decision, so FR-007 covers it and the
feature's pull request closes #597.

## Two stories, not six

The first draft had six stories: default backups, the encryption key, changing a schedule, S3
storage with its warning, restoring, and a backup by hand. The maintainer asked for them to be
condensed. Encryption, the storage location, the warning and the schedule are all parts of one
thing a developer gets, a portal that is backed up by default, so they are scenarios under US1.
A backup by hand is not a story of its own either: the periodic task screens already run a
selected task at once, so it is one more scenario under US1. Restoring is a separate thing a
developer sets out to do, and stays US2. Nothing was dropped. Every scenario and requirement of the
first draft is still in the specification.
