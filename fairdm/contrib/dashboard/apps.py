from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DashboardConfig(AppConfig):
    """The dashboard's models, pages and the middleware that counts record use."""

    name = "fairdm.contrib.dashboard"
    label = "dashboard"
    verbose_name = _("Dashboard")
    default_auto_field = "django.db.models.BigAutoField"
