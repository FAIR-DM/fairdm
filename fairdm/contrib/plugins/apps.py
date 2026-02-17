"""Django app configuration for plugin system."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PluginsConfig(AppConfig):
    """Configuration for the FairDM plugin system."""

    name = "fairdm.contrib.plugins"
    label = "plugins"
    verbose_name = _("Plugins")
    default_auto_field = "django.db.models.BigAutoField"
