"""FairDM API URL configuration.

Mounts all API endpoints under ``/api/v1/``.  Included from the main URL conf
via ``path("api/", include(("fairdm.api.urls", "api"), namespace="api"))``.
"""

from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from fairdm.api.router import fairdm_api_router
from fairdm.api.viewsets import MeasurementDiscoveryView, SampleDiscoveryView

# Namespaced so API route names cannot collide with portal routes like ``project-list``.
app_name = "api"

urlpatterns = [
    # Before the router include so they win over its '' pattern (the API root redirect).
    path("v1/samples/", SampleDiscoveryView.as_view(), name="api-sample-discovery"),
    path(
        "v1/measurements/",
        MeasurementDiscoveryView.as_view(),
        name="api-measurement-discovery",
    ),
    path("v1/", include(fairdm_api_router.urls)),
    path("v1/auth/", include("dj_rest_auth.urls")),
    path("v1/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path(
        "v1/docs/",
        SpectacularSwaggerView.as_view(url_name="api:api-schema"),
        name="api-docs",
    ),
    path(
        "v1/redoc/",
        SpectacularRedocView.as_view(url_name="api:api-schema"),
        name="api-redoc",
    ),
]
