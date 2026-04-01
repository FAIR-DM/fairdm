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

import logging

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

_logger = logging.getLogger(__name__)

# ── 2. Registry-registered Sample types ───────────────────────────────────
# Samples and measurements use separate try/except so a failure in one
# doesn't prevent the other from registering.
try:
    from fairdm.registry import registry as _registry

    for _model in _registry.samples:
        _slug = _model_to_slug(_model)
        _config = _registry.get_for_model(_model)
        _viewset = generate_viewset(_config)
        fairdm_api_router.register(
            rf"samples/{_slug}",
            _viewset,
            basename=f"samples-{_slug}",
        )
except Exception as _e:
    _logger.warning("FairDM API: failed to register sample viewsets: %s", _e, exc_info=True)

# ── 3. Registry-registered Measurement types ───────────────────────────────
try:
    from fairdm.registry import registry as _registry

    for _model in _registry.measurements:
        _slug = _model_to_slug(_model)
        _config = _registry.get_for_model(_model)
        _viewset = generate_viewset(_config)
        fairdm_api_router.register(
            rf"measurements/{_slug}",
            _viewset,
            basename=f"measurements-{_slug}",
        )
except Exception as _e:
    _logger.warning("FairDM API: failed to register measurement viewsets: %s", _e, exc_info=True)
