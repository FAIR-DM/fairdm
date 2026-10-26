"""App configuration for scheduled backups."""

from django.apps import AppConfig, apps
from django.db.models.signals import post_migrate


class BackupsConfig(AppConfig):
    """Creates the default backup tasks once ``django_celery_beat`` has its tables."""

    name = "fairdm.backups"
    label = "backups"

    def ready(self):
        """Connect the receiver that creates the default tasks."""
        from .signals import seed_default_tasks

        post_migrate.connect(
            seed_default_tasks,
            sender=apps.get_app_config("django_celery_beat"),
            dispatch_uid="backups.seed_default_tasks",
        )
