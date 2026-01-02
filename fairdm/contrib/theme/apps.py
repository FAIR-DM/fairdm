"""App configuration for FairDM Theme."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ThemeConfig(AppConfig):
    """Configuration for the FairDM Theme app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "fairdm.contrib.theme"
    label = "fairdm_theme"
    verbose_name = _("FairDM Theme")
