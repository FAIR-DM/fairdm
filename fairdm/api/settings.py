"""Django REST Framework, OpenAPI and CORS settings for the FairDM API.

These settings configure the Django REST Framework, drf-spectacular (OpenAPI),
and CORS. They are merged into the main Django settings via fairdm/conf/settings/api.py.

Portal developers can override any of these in their own settings:

    # In portal's settings.py
    REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["user_day"] = "50000/day"
    REST_FRAMEWORK["PAGE_SIZE"] = 50
    FAIRDM_API_MAX_PAGE_SIZE = 500
    SPECTACULAR_SETTINGS["TITLE"] = "My Research Portal API"
    SPECTACULAR_SETTINGS["DESCRIPTION"] = "A specialised API for geochemical data."

``FAIRDM_API_TITLE`` and ``FAIRDM_API_DESCRIPTION`` below are the defaults that
``SPECTACULAR_SETTINGS`` is built from once, when this module is imported. A portal changes the
title and description by assigning items of ``SPECTACULAR_SETTINGS``, after ``fairdm.setup()``
returns. It assigns items and never a new dictionary: replacing the dictionary drops the hook
that writes the limits into the description.
"""

#: Default title, ``info.title`` of the OpenAPI schema. A portal sets
#: ``SPECTACULAR_SETTINGS["TITLE"]`` instead of this name.
FAIRDM_API_TITLE = "FairDM Portal API"

#: Default Markdown description, ``info.description`` of the OpenAPI schema. A portal sets
#: ``SPECTACULAR_SETTINGS["DESCRIPTION"]`` instead of this name.
FAIRDM_API_DESCRIPTION = """\
## FairDM Research Data Portal API

This API provides programmatic access to all data published in this portal, following
[FAIR data principles](https://www.go-fair.org/fair-principles/) — Findable, Accessible,
Interoperable, and Reusable.

### Available Resources

| Resource | Endpoint | Description |
|----------|----------|-------------|
| **Projects** | `/api/v1/projects/` | Top-level research projects |
| **Datasets** | `/api/v1/datasets/` | Collections of samples within a project |
| **Contributors** | `/api/v1/contributors/` | People and organisations contributing data |
| **Sample types** | `/api/v1/samples/{type}/` | Domain-specific sample data |
| **Measurement types** | `/api/v1/measurements/{type}/` | Analytical measurements |

`/api/v1/` links to every list the portal serves, and each type's description is on its list below.

### Filtering & Ordering

- `?<field>=<value>` — filter by exact field value (available fields vary by resource)
- `?modified_after=<date or date-time>` / `?modified_before=<date or date-time>` — only
  records changed after, or before, a moment (ISO 8601), on every list
- `?ordering=<field>` / `?ordering=-<field>` — ascending/descending ordering
"""

#: The most records a caller may ask for in one page of a list. The default page size is
#: ``REST_FRAMEWORK["PAGE_SIZE"]``. Both are read when a request is answered.
FAIRDM_API_MAX_PAGE_SIZE = 1000

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        # Token first: DRF answers 403 instead of 401 when the first authenticator
        # (SessionAuthentication) has no authenticate_header().
        "knox.auth.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
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
    "PAGE_SIZE": 100,
    # Two limits for each kind of caller: one over a minute to stop a burst, one over a day.
    # The figures suit a portal on one small server.
    "DEFAULT_THROTTLE_CLASSES": [
        "fairdm.api.throttling.AnonBurstThrottle",
        "fairdm.api.throttling.AnonDailyThrottle",
        "fairdm.api.throttling.UserBurstThrottle",
        "fairdm.api.throttling.UserDailyThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon_burst": "30/minute",
        "anon_day": "2000/day",
        "user_burst": "120/minute",
        "user_day": "20000/day",
    },
    "DEFAULT_FILTER_BACKENDS": [
        "fairdm.api.filters.FairDMVisibilityFilter",
        "fairdm.api.filters.FairDMFilterBackend",
        "rest_framework.filters.OrderingFilter",
    ],
}

SPECTACULAR_SETTINGS = {
    "TITLE": FAIRDM_API_TITLE,
    "DESCRIPTION": FAIRDM_API_DESCRIPTION,
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # Bundled assets, so the docs work in air-gapped environments.
    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "SCHEMA_PATH_PREFIX": r"/api/v[0-9]+",
    "SORT_OPERATIONS": False,
    "POSTPROCESSING_HOOKS": [
        "drf_spectacular.hooks.postprocess_schema_enums",
        "fairdm.api.schema.describe_api",
    ],
}

#: A token travels in a header a page chooses to send, so any website may call the API.
#: Credentials stay off (``CORS_ALLOW_CREDENTIALS`` is not set), so a sign-in cookie is
#: never accepted from another origin.
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS: list[str] = []
CORS_URLS_REGEX = r"^/api/.*$"

#: Settings of django-rest-knox, which stores the tokens people create on their account
#: pages. A token does not renew when it is used, and a person holds at most ten.
REST_KNOX = {"TOKEN_LIMIT_PER_USER": 10, "AUTO_REFRESH": False}
