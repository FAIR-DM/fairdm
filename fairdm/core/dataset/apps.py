"""App configuration for the dataset app."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FairDMDatasetConfig(AppConfig):
    """Configuration for the ``fairdm.core.dataset`` app."""

    name = "fairdm.core.dataset"
    label = "dataset"
    verbose_name = _("Dataset")
    verbose_name_plural = _("Dataset")
