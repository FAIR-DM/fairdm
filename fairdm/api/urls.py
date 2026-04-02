"""FairDM API URL configuration.

Mounts all API endpoints under ``/api/v1/``.  Included from the main URL conf
via ``path("api/", include("fairdm.api.urls"))``.
"""

from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from fairdm.api.router import fairdm_api_router
from fairdm.api.viewsets import MeasurementDiscoveryView, SampleDiscoveryView

urlpatterns = [
    # ── Discovery catalog views ────────────────────────────────────────────
    # These must come *before* the router include so they take priority over the
    # router's own '' pattern (the API root redirect).
    path("v1/samples/", SampleDiscoveryView.as_view(), name="api-sample-discovery"),
    path("v1/measurements/", MeasurementDiscoveryView.as_view(), name="api-measurement-discovery"),
    # ── Router-generated endpoints ─────────────────────────────────────────
    path("v1/", include(fairdm_api_router.urls)),
    # ── Authentication endpoints (dj-rest-auth) ────────────────────────────
    path("v1/auth/", include("dj_rest_auth.urls")),
    # ── OpenAPI schema and interactive docs ───────────────────────────────
    path("v1/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path("v1/docs/", SpectacularSwaggerView.as_view(url_name="api-schema"), name="api-docs"),
    path("v1/redoc/", SpectacularRedocView.as_view(url_name="api-schema"), name="api-redoc"),
]
