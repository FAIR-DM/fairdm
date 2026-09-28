"""App configuration for the portal admin."""

from django.apps import AppConfig
from django.contrib.admin import apps


class FairDMAdminConfig(AppConfig):
    """Configuration for the portal admin app."""

    name = "fairdm.contrib.admin"
    label = "fairdm_admin"


class FairDMAdminSite(apps.AdminConfig):
    """Admin config that swaps in the portal's custom admin site."""

    default_site = "fairdm.contrib.admin.sites.CustomAdminSite"
