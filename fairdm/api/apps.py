"""FairDM API app configuration."""

from django.apps import AppConfig


class FairDMApiConfig(AppConfig):
    """App configuration for the FairDM auto-generated RESTful API."""

    name = "fairdm.api"
    verbose_name = "FairDM API"

    def ready(self) -> None:
        # Ensure the router is auto-populated when Django starts
        from fairdm.api import router  # noqa: F401
