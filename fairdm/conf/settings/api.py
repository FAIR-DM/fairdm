"""REST API settings: Django REST Framework, drf-spectacular and CORS.

Owns the Django REST Framework, drf-spectacular (OpenAPI schema) and CORS
configuration, including the SPECTACULAR_SETTINGS title and description. A portal
overrides any of it by assignment after ``fairdm.setup()`` returns::

    REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {"anon": "50/hour", "user": "500/hour"}
    SPECTACULAR_SETTINGS["TITLE"] = "My Portal API"
    SPECTACULAR_SETTINGS["DESCRIPTION"] = "A specialised API for my research domain."
    REST_KNOX["TOKEN_LIMIT_PER_USER"] = 5
    CORS_ALLOW_ALL_ORIGINS = False
    CORS_ALLOWED_ORIGINS = ["https://my-frontend.example.com"]

Overriding ``FAIRDM_API_TITLE``/``FAIRDM_API_DESCRIPTION`` after ``setup()``
has no effect on ``SPECTACULAR_SETTINGS`` — that dict is already built by the
time this layer's assignment runs. Override ``SPECTACULAR_SETTINGS`` itself.
"""

from fairdm.api.settings import (
    CORS_ALLOW_ALL_ORIGINS,
    CORS_ALLOWED_ORIGINS,
    CORS_URLS_REGEX,
    FAIRDM_API_DESCRIPTION,
    FAIRDM_API_DOCS_URL,
    FAIRDM_API_TITLE,
    REST_FRAMEWORK,
    REST_KNOX,
    SPECTACULAR_SETTINGS,
)

# Re-exported so `include()` picks them up in the caller's namespace.
__all__ = [
    "CORS_ALLOWED_ORIGINS",
    "CORS_ALLOW_ALL_ORIGINS",
    "CORS_URLS_REGEX",
    "FAIRDM_API_DESCRIPTION",
    "FAIRDM_API_DOCS_URL",
    "FAIRDM_API_TITLE",
    "REST_FRAMEWORK",
    "REST_KNOX",
    "SPECTACULAR_SETTINGS",
]
