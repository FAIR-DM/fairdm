"""FairDM API app configuration."""

from django.apps import AppConfig


class FairDMApiConfig(AppConfig):
    """App configuration for the FairDM auto-generated RESTful API."""

    name = "fairdm.api"
    verbose_name = "FairDM API"

    # def ready(self) -> None:
    # Register Sample and Measurement viewsets from the FairDM registry.
    # Must run in ready() so the registry is fully populated before registration.
    # from fairdm.api.router import register_dynamic_viewsets

    # register_dynamic_viewsets()
