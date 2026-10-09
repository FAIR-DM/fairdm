"""The central DRF router that wires registry-registered models to URL prefixes.

Auto-registration happens when this module is imported, and a type whose endpoints cannot
be built stops the import with the real error.

Portal developers can add a viewset of their own to the router from an app's ``ready()``,
or any module imported before the URL configuration loads ``fairdm.api.urls``, which reads
the router's addresses once::

    from fairdm.api.router import fairdm_api_router

    fairdm_api_router.register(r"my-custom", MyCustomViewSet, basename="my-custom")

The router instance is the public ``fairdm_api_router`` symbol.  All registered
viewsets are served under ``/api/v1/`` and appear in the OpenAPI schema.
"""

from rest_framework.routers import DefaultRouter

from fairdm.api.viewsets import (
    ContributorViewSet,
    DatasetViewSet,
    ProjectViewSet,
    _model_to_slug,
    generate_viewset,
)


class FairDMAPIRouter(DefaultRouter):
    """DefaultRouter that can register the portal's sample and measurement types."""

    def register_types(self) -> None:
        """Register the list and record routes of every registered sample and measurement type.

        A sample type is served at ``samples/<plural name>/`` with the route name
        ``samples-<plural name>``, and a measurement type likewise under ``measurements/``.

        Raises:
            ImproperlyConfigured: When a type's serializer does not build on the base
                serializer of its kind.
        """
        from fairdm.registry import registry

        for prefix, models in (
            ("samples", registry.samples),
            ("measurements", registry.measurements),
        ):
            for model in models:
                slug = _model_to_slug(model)
                viewset = generate_viewset(registry.get_for_model(model))
                self.register(rf"{prefix}/{slug}", viewset, basename=f"{prefix}-{slug}")


fairdm_api_router = FairDMAPIRouter()

fairdm_api_router.register(r"projects", ProjectViewSet, basename="project")
fairdm_api_router.register(r"datasets", DatasetViewSet, basename="dataset")
fairdm_api_router.register(r"contributors", ContributorViewSet, basename="contributor")
fairdm_api_router.register_types()
