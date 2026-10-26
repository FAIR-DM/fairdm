"""Celery tasks that run the scheduled backups."""

from celery import shared_task

from .run import run_backup

# A backup of a large portal runs for hours: the global limits of one and five minutes
# would kill it.
BACKUP_LIMITS = {"soft_time_limit": 21000, "time_limit": 21600}


@shared_task(**BACKUP_LIMITS)
def backup_database() -> None:
    """Back up the database."""
    run_backup("database")


@shared_task(**BACKUP_LIMITS)
def backup_media() -> None:
    """Back up the media files."""
    run_backup("media")
