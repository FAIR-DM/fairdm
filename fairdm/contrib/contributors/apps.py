"""App configuration for contributors."""

from django.apps import AppConfig, apps
from django.utils.translation import gettext_lazy as _


class ContributorsConfig(AppConfig):
    """Configuration for the contributors app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "fairdm.contrib.contributors"
    label = "contributors"
    verbose_name = _("Community")

    def ready(self):
        """Connect the receivers for claiming, the shipped portal roles and the weekly refresh."""
        from allauth.account.signals import email_confirmed
        from django.contrib.auth.models import Group
        from django.db.models.signals import post_migrate, pre_delete, pre_save

        from .receivers import (
            refuse_shipped_role_deletion,
            refuse_shipped_role_rename,
            seed_refresh_task,
        )
        from .signals import handle_email_confirmed

        email_confirmed.connect(handle_email_confirmed)
        pre_delete.connect(
            refuse_shipped_role_deletion,
            sender=Group,
            dispatch_uid="contributors.refuse_shipped_role_deletion",
        )
        pre_save.connect(
            refuse_shipped_role_rename,
            sender=Group,
            dispatch_uid="contributors.refuse_shipped_role_rename",
        )
        post_migrate.connect(
            seed_refresh_task,
            sender=apps.get_app_config("django_celery_beat"),
            dispatch_uid="contributors.seed_refresh_task",
        )
