"""App configuration for activity."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ActivityConfig(AppConfig):
    """Configuration for the activity app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "fairdm.contrib.activity"
    label = "activity"
    verbose_name = _("Activity")
