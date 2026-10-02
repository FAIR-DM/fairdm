"""Django app configuration for contacting a record's team and reporting a problem."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ContactConfig(AppConfig):
    """Configuration for the Contact and Report a problem page actions."""

    name = "fairdm.contrib.contact"
    label = "contact"
    verbose_name = _("Contact and reported problems")
    default_auto_field = "django.db.models.BigAutoField"
