from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class LocationConfig(AppConfig):
    name = "fairdm.contrib.location"
    label = "fairdm_location"
    verbose_name = _("Location")
