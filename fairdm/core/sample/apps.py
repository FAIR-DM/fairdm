from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FairDMSampleConfig(AppConfig):
    name = "fairdm.core.sample"
    label = "sample"
    verbose_name = _("Sample")
    verbose_name_plural = _("Sample")
