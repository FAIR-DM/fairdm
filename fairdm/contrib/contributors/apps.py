from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ContributorsConfig(AppConfig):
    name = "fairdm.contrib.contributors"
    label = "contributors"
    verbose_name = _("Community")
