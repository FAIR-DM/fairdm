"""FairDM API router.

This module creates and auto-populates the ``fairdm_api_router`` — the central
DRF ``DefaultRouter`` that wires all registry-registered models to URL prefixes.

Auto-registration happens when this module is imported (triggered by
:meth:`~fairdm.api.apps.FairDMApiConfig.ready`).

Portal developers can extend the router *before* or *after* Django startup::

    # In portal's urls.py or api.py
    from fairdm.api.router import fairdm_api_router

    fairdm_api_router.register(r"my-custom", MyCustomViewSet, basename="my-custom")

The router instance is the public ``fairdm_api_router`` symbol.  All registered
viewsets automatically appear in the OpenAPI schema and under ``/api/v1/``.
"""

from rest_framework.routers import DefaultRouter

from fairdm.api.viewsets import (
    ContributorViewSet,
    DatasetViewSet,
    ProjectViewSet,
    _model_to_slug,
    generate_viewset,
)

# Public router instance — importable by portal developers
fairdm_api_router = DefaultRouter()

# ── 1. Core model endpoints ────────────────────────────────────────────────
fairdm_api_router.register(r"projects", ProjectViewSet, basename="project")
fairdm_api_router.register(r"datasets", DatasetViewSet, basename="dataset")
fairdm_api_router.register(r"contributors", ContributorViewSet, basename="contributor")

# ── 2. Registry-registered Sample types ───────────────────────────────────
try:
    from fairdm.registry import registry  # noqa: E402

    for _model in registry.samples:
        _slug = _model_to_slug(_model)
        _config = registry.get_for_model(_model)
        _viewset = generate_viewset(_config)
        fairdm_api_router.register(
            rf"samples/{_slug}",
            _viewset,
            basename=f"samples-{_slug}",
        )

    # ── 3. Registry-registered Measurement types ───────────────────────────
    for _model in registry.measurements:
        _slug = _model_to_slug(_model)
        _config = registry.get_for_model(_model)
        _viewset = generate_viewset(_config)
        fairdm_api_router.register(
            rf"measurements/{_slug}",
            _viewset,
            basename=f"measurements-{_slug}",
        )
except Exception:
    # Registry may not be fully populated yet during initial setup.
    # The router will be re-populated the next time the module is imported
    # after the registry is ready (i.e. after all app ready() calls).
    pass
