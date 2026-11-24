"""App configuration for import and export."""

from django.apps import AppConfig, apps
from django.db.models.signals import post_migrate
from django.utils.translation import gettext_lazy as _

DISCARD_TASK = "fairdm.contrib.import_export.tasks.discard_stale_jobs"
"""The task path of the daily discard of imports left unfinished."""


def seed_discard_task(**kwargs):
    """Schedule the daily discard of stale imports at 02:30, if it is missing.

    A task that exists is never touched, so a portal that changed its schedule or
    switched it off keeps its choice. The task is found by its task path.

    Args:
        **kwargs: The signal's arguments, unused.
    """
    from django.conf import settings
    from django_celery_beat.models import CrontabSchedule, PeriodicTask

    if PeriodicTask.objects.filter(task=DISCARD_TASK).exists():
        return
    crontab = CrontabSchedule.objects.get_or_create(
        minute="30",
        hour="2",
        day_of_week="*",
        day_of_month="*",
        month_of_year="*",
        timezone=settings.TIME_ZONE,
    )[0]
    PeriodicTask.objects.create(
        name="Discard imports left unfinished for 30 days",
        task=DISCARD_TASK,
        crontab=crontab,
        enabled=True,
    )


class FairDMImportExportConfig(AppConfig):
    """Configuration for the import and export app."""

    name = "fairdm.contrib.import_export"
    label = "fairdm_import_export"
    verbose_name = _("Import / Export")

    def ready(self):
        """Schedule the discard of stale imports once the beat tables exist."""
        post_migrate.connect(
            seed_discard_task,
            sender=apps.get_app_config("django_celery_beat"),
            dispatch_uid="import_export.seed_discard_task",
        )
