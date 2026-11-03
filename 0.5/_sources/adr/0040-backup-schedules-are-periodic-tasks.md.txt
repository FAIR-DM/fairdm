# ADR 0040 — Backup schedules are periodic tasks

**Status:** accepted

## Decision

FairDM's database and media backups run as two django-celery-beat periodic tasks. After every
migration, a `post_migrate` receiver creates each one, weekly on Sunday at 03:00 in the portal's
time zone, but only when no task of that name exists. A task that exists is never changed. No
setting or environment variable decides when a backup runs.

## Why

A portal developer changes, disables or runs a backup in the periodic task admin, which
django-celery-beat already provides. If a setting could also decide a schedule, there would be two
places a schedule comes from, and a deployment could undo a change made in the admin. Creating a
task only when it is missing gives every portal backups with no configuration, and keeps each
developer's changes through every later deployment.

The cost is that a deleted task comes back with its default schedule at the next migration.
Disabling a task is the supported way to stop a backup.

## Revisit if

A portal needs backups on a deployment that runs no Celery beat.
