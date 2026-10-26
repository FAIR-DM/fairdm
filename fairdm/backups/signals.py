"""Receivers that create the default backup tasks."""

from django.conf import settings
from django_celery_beat.models import CrontabSchedule, PeriodicTask

#: The two tasks every portal gets: ``(name, task path)``.
DEFAULT_TASKS = [
    ("Back up the database", "fairdm.backups.tasks.backup_database"),
    ("Back up the media", "fairdm.backups.tasks.backup_media"),
]


def seed_default_tasks(**kwargs):
    """Create each default backup task that does not exist, weekly on Sunday at 03:00.

    A task that exists is never touched, so a portal that changed a schedule or switched a
    task off keeps its choice.

    Args:
        **kwargs: The signal's arguments, unused.
    """
    for name, task in DEFAULT_TASKS:
        if PeriodicTask.objects.filter(name=name).exists():
            continue
        crontab, _created = CrontabSchedule.objects.get_or_create(
            minute="0",
            hour="3",
            day_of_week="0",
            day_of_month="*",
            month_of_year="*",
            timezone=settings.TIME_ZONE,
        )
        PeriodicTask.objects.create(name=name, task=task, crontab=crontab, enabled=True)
