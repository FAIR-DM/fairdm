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

# Namespaced so API route names cannot collide with portal routes like ``project-list``.
app_name = "api"

urlpatterns = [
    path("v1/", include(fairdm_api_router.urls)),
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
