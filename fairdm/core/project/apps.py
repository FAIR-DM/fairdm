"""App configuration for the project app."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FairDMProjectConfig(AppConfig):
    """Configuration for the ``fairdm.core.project`` app."""

    name = "fairdm.core.project"
    label = "project"
    verbose_name = _("Project")
    verbose_name_plural = _("Projects")
