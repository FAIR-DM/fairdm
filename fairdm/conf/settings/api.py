"""REST API Settings

Configuration for Django REST Framework, drf-spectacular (OpenAPI schema),
and CORS. These settings power the auto-generated RESTful API (Feature 011).

Portal developers can override individual keys after calling fairdm.setup()::

    REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {"anon": "50/hour", "user": "500/hour"}
    SPECTACULAR_SETTINGS["TITLE"] = "My Portal API"
    CORS_ALLOWED_ORIGINS = ["https://my-frontend.example.com"]

    # Or use the dedicated title/description settings (recommended):
    FAIRDM_API_TITLE = "My Research Portal API"
    FAIRDM_API_DESCRIPTION = "A specialised API for my research domain."
"""

from fairdm.api.settings import (
    CORS_ALLOW_ALL_ORIGINS,
    CORS_ALLOWED_ORIGINS,
    CORS_URLS_REGEX,
    FAIRDM_API_DESCRIPTION,
    FAIRDM_API_DOCS_URL,
    FAIRDM_API_TITLE,
    REST_FRAMEWORK,
    SPECTACULAR_SETTINGS,
)

# Re-export so split_settings include() picks them up in the caller's namespace
__all__ = [
    "REST_FRAMEWORK",
    "SPECTACULAR_SETTINGS",
    "CORS_ALLOW_ALL_ORIGINS",
    "CORS_ALLOWED_ORIGINS",
    "CORS_URLS_REGEX",
    "FAIRDM_API_DOCS_URL",
    "FAIRDM_API_TITLE",
    "FAIRDM_API_DESCRIPTION",
]
