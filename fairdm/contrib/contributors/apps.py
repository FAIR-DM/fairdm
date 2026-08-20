from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ContributorsConfig(AppConfig):
    name = "fairdm.contrib.contributors"
    label = "contributors"
    verbose_name = _("Community")

    def ready(self):
        from allauth.account.signals import email_confirmed
        from django.db.models.signals import post_delete

        from .models import Contribution
        from .receivers import withdraw_rights_on_credit_deletion
        from .signals import handle_email_confirmed

        email_confirmed.connect(handle_email_confirmed)
        post_delete.connect(
            withdraw_rights_on_credit_deletion,
            sender=Contribution,
            dispatch_uid="contributors.withdraw_rights_on_credit_deletion",
        )
