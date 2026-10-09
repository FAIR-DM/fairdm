"""FairDM API app configuration."""

from django.apps import AppConfig
from django.core.checks import Tags, register


class FairDMApiConfig(AppConfig):
    """App configuration for the FairDM auto-generated RESTful API."""

    name = "fairdm.api"
    verbose_name = "FairDM API"

    def ready(self) -> None:
        """Register the check that every registered type can be created through the API."""
        from fairdm.api.checks import check_registered_types

        register(check_registered_types, Tags.models)
        return super().ready()
