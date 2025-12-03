from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FairDMProjectConfig(AppConfig):
    name = "fairdm.core.project"
    label = "project"
    verbose_name = _("Project")
    verbose_name_plural = _("Projects")
