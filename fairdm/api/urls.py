"""FairDM API URL configuration.

Mounts all API endpoints under ``/api/v1/``.  Included from the main URL conf
via ``path("api/", include(("fairdm.api.urls", "api"), namespace="api"))``.
"""

from django.conf import settings
from django.urls import include, path
from drf_spectacular.settings import SPECTACULAR_DEFAULTS
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from fairdm.api.router import fairdm_api_router

#: The schema the second documentation page reads: the first, with each registered type
#: nested under its kind.
NESTED_SCHEMA_SETTINGS = {
    "POSTPROCESSING_HOOKS": [
        *getattr(settings, "SPECTACULAR_SETTINGS", {}).get(
            "POSTPROCESSING_HOOKS", SPECTACULAR_DEFAULTS["POSTPROCESSING_HOOKS"]
        ),
        "fairdm.api.schema.nest_types",
    ]
}

# Namespaced so API route names cannot collide with portal routes like ``project-list``.
app_name = "api"

urlpatterns = [
    path("v1/", include(fairdm_api_router.urls)),
    path("v1/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path(
        "v1/schema/nested/",
        SpectacularAPIView.as_view(custom_settings=NESTED_SCHEMA_SETTINGS),
        name="api-schema-nested",
    ),
    path(
        "v1/docs/",
        SpectacularSwaggerView.as_view(url_name="api:api-schema"),
        name="api-docs",
    ),
    path(
        "v1/redoc/",
        SpectacularRedocView.as_view(url_name="api:api-schema-nested"),
        name="api-redoc",
    ),
]
