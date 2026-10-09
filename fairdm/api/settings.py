"""Django REST Framework, OpenAPI and CORS settings for the FairDM API.

These settings configure the Django REST Framework, drf-spectacular (OpenAPI),
and CORS. They are merged into the main Django settings via fairdm/conf/settings/api.py.

Portal developers can override any of these in their own settings:

    # In portal's settings.py
    REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {"anon": "50/hour", "user": "500/hour"}
    FAIRDM_API_TITLE = "My Research Portal API"
    FAIRDM_API_DESCRIPTION = "A specialised API for geochemical data."
"""

#: Title displayed in Swagger UI and OpenAPI schema ``info.title``.
#: Override in your portal settings: ``FAIRDM_API_TITLE = "My Portal API"``
FAIRDM_API_TITLE = "FairDM Portal API"

#: Rich Markdown description shown in Swagger UI and OpenAPI schema ``info.description``.
#: Override in your portal settings: ``FAIRDM_API_DESCRIPTION = "..."``
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
| **Sample types** | `/api/v1/samples/{type}/` | Domain-specific sample data (see discovery endpoint) |
| **Measurement types** | `/api/v1/measurements/{type}/` | Analytical measurements (see discovery endpoint) |

Use the discovery endpoints to list all registered sample and measurement types:

- `GET /api/v1/samples/` — catalogue of all sample types with field and count information
- `GET /api/v1/measurements/` — catalogue of all measurement types

### Authentication

Most data is publicly readable without authentication.  To **create, update, or delete**
records you need a token:

1. Sign in to the portal and create a token on your account pages, under API tokens.
   The token is shown once, so copy it then.
2. Include it in each request: `Authorization: Token <your-token>`

Revoke a token on the same page when you no longer need it.

### Rate Limits

| Client type | Limit |
|-------------|-------|
| Anonymous | 100 requests / hour |
| Authenticated | 1 000 requests / hour |

Throttled requests receive `HTTP 429` with a `Retry-After` header.
Portal operators can adjust limits via the `REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]` setting.

### Pagination

All list endpoints are paginated (default page size: 25, maximum: 100).

- `?page=<n>` — page number
- `?page_size=<n>` — results per page (capped at 100)

### Filtering & Ordering

- `?<field>=<value>` — filter by exact field value (available fields vary by resource)
- `?ordering=<field>` / `?ordering=-<field>` — ascending/descending ordering
"""

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
    "TITLE": FAIRDM_API_TITLE,
    "DESCRIPTION": FAIRDM_API_DESCRIPTION,
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # Bundled assets, so the docs work in air-gapped environments.
    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "REDOC_DIST": "SIDECAR",
    "SCHEMA_PATH_PREFIX": r"/api/v[0-9]+",
    "SORT_OPERATIONS": False,
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

#: URL of the API documentation. Override it in portal settings to point elsewhere.
FAIRDM_API_DOCS_URL = "https://fairdm.org/api/"
