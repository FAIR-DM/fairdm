"""FairDM API settings.

These settings configure the Django REST Framework, drf-spectacular (OpenAPI),
and CORS. They are merged into the main Django settings via fairdm/conf/settings/api.py.

Portal developers can override any of these in their own settings:

    # In portal's settings.py
    REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {"anon": "50/hour", "user": "500/hour"}
"""

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "fairdm.api.permissions.FairDMObjectPermissions",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "drf_orjson_renderer.renderers.ORJSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "drf_orjson_renderer.parsers.ORJSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "fairdm.api.pagination.FairDMPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
    },
    "DEFAULT_FILTER_BACKENDS": [
        "fairdm.api.filters.FairDMVisibilityFilter",
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
    ],
}

SPECTACULAR_SETTINGS = {
    "TITLE": "FairDM Portal API",
    "DESCRIPTION": "Auto-generated API for this FairDM research data portal.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # Use bundled sidecar dist — works in air-gapped environments
    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "REDOC_DIST": "SIDECAR",
    # Group endpoints by resource type tag
    "SCHEMA_PATH_PREFIX": r"/api/v[0-9]+",
    "SORT_OPERATIONS": False,
}

# CORS: restrictive defaults; portal operators override for their origin lists
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS: list[str] = []
CORS_URLS_REGEX = r"^/api/.*$"
