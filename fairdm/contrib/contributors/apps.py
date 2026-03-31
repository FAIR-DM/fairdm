from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ContributorsConfig(AppConfig):
    name = "fairdm.contrib.contributors"
    label = "contributors"
    verbose_name = _("Community")

    def ready(self):
        from allauth.account.signals import email_confirmed

        from .signals import handle_email_confirmed

        email_confirmed.connect(handle_email_confirmed)
