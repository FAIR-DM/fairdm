from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ContributorsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "fairdm.contrib.contributors"
    label = "contributors"
    verbose_name = _("Community")

    def ready(self):
        from allauth.account.signals import email_confirmed
        from django.db.models.signals import m2m_changed, post_delete

        from .models import Contribution
        from .receivers import (
            refuse_off_vocabulary_role,
            withdraw_rights_on_credit_deletion,
        )
        from .signals import handle_email_confirmed

        email_confirmed.connect(handle_email_confirmed)
        post_delete.connect(
            withdraw_rights_on_credit_deletion,
            sender=Contribution,
            dispatch_uid="contributors.withdraw_rights_on_credit_deletion",
        )
        m2m_changed.connect(
            refuse_off_vocabulary_role,
            sender=Contribution.roles.through,
            dispatch_uid="contributors.refuse_off_vocabulary_role",
        )
