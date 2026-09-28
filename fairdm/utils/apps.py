"""App config for the FairDM utilities app."""

from django.apps import AppConfig


class UtilsConfig(AppConfig):
    """Register the FairDM utilities app."""

    name = "fairdm.utils"
    label = "utils"
    verbose_name = "FairDM Utilities"
    default_auto_field = "django.db.models.AutoField"
