"""App configuration for autocomplete."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AutocompleteConfig(AppConfig):
    """Configuration for the autocomplete app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "fairdm.contrib.autocomplete"
    verbose_name = _("Autocomplete")
