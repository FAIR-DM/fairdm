"""App configuration for locations."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class LocationConfig(AppConfig):
    """Configuration for the location app."""

    name = "fairdm.contrib.location"
    label = "fairdm_location"
    verbose_name = _("Location")
