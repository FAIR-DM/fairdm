# Research: Auto-Generated RESTful API

**Feature**: 011-restful-api
**Date**: 2026-03-31

## R1: Serialization Performance — orjson vs stdlib JSON

**Decision**: Use `drf-orjson-renderer` as the default JSON renderer/parser.

**Rationale**: orjson is a Rust-backed JSON serializer that benchmarks 3–10x faster than Python's stdlib json. `drf-orjson-renderer` is a drop-in replacement for DRF's `JSONRenderer` and `JSONParser` — no API changes needed. It automatically pretty-prints for the Browsable API and handles Django/NumPy types natively.

**Alternatives considered**:

- `ujson` — faster than stdlib but slower than orjson; no native Django type support.
- stdlib `json` via DRF default — functional but measurably slower for large payloads (datasets with hundreds of samples).
- `msgpack` — binary format; not suitable for a human-readable REST API.

**Configuration**:

```python
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": (
        "drf_orjson_renderer.renderers.ORJSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
    "DEFAULT_PARSER_CLASSES": (
        "drf_orjson_renderer.parsers.ORJSONParser",
    ),
}
```

---

## R2: OpenAPI Schema & Interactive Documentation

**Decision**: Use `drf-spectacular` with the sidecar extras for OpenAPI 3.0 schema generation and Swagger UI.

**Rationale**: drf-spectacular is the de-facto standard for DRF schema generation. It replaces the deprecated `coreapi` schema and supports OpenAPI 3.0 with accurate type inference, enum handling, and polymorphic serializer support. The `[sidecar]` extra bundles Swagger UI and ReDoc static files so the docs page works without a CDN or internet access — important for air-gapped research environments.

**Alternatives considered**:

- `drf-yasg` — deprecated in favor of drf-spectacular; does not support OpenAPI 3.0.
- Manual OpenAPI YAML — maintenance burden; falls out of sync with code.
- `drf-schema-adapter`'s `AutoMetadata` — provides OPTIONS-based schema but NOT OpenAPI/Swagger UI. Package dropped from plan (see R7).

**Configuration**:

```python
INSTALLED_APPS = [
    ...
    "drf_spectacular",
    "drf_spectacular_sidecar",
]

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Portal API",  # overridable per portal
    "DESCRIPTION": "Auto-generated API for this FairDM research data portal.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "REDOC_DIST": "SIDECAR",
}
```

---

## R3: Authentication Strategy

**Decision**: Use `dj-rest-auth` for API authentication endpoints, configured with DRF Token Authentication (`rest_framework.authtoken`) for programmatic clients and session authentication for browser/Swagger UI. JWT is explicitly **out of scope for v1** (`REST_USE_JWT = False`; `djangorestframework-simplejwt` is not added).

**Rationale**: dj-rest-auth provides login, logout, password reset, and user detail endpoints out of the box, wired to allauth (already in use). Session authentication covers the browser/Swagger UI use case. DRF TokenAuthentication covers programmatic API clients. JWT with HTTP-only cookies (supported by dj-rest-auth) can be enabled later without breaking the API.

**Alternatives considered**:

- JWT-only (djangorestframework-simplejwt) — adds complexity; session auth is simpler for browser-based Swagger usage and matches the existing allauth stack.
- Session-only — insufficient for programmatic clients (CLI tools, scripts, other services).
- OAuth2 (django-oauth-toolkit) — overkill for v1; adds client/grant management overhead.

**Configuration**:

```python
INSTALLED_APPS = [
    ...
    "rest_framework",
    "rest_framework.authtoken",
    "dj_rest_auth",
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
}
```

**Auth endpoints provided by dj-rest-auth**:

- `POST /api/v1/auth/login/` — obtain token
- `POST /api/v1/auth/logout/` — revoke token
- `GET /api/v1/auth/user/` — current user details
- `POST /api/v1/auth/password/change/`
- `POST /api/v1/auth/password/reset/`

---

## R4: Endpoint Strategy for Sample/Measurement Types

**Decision**: Use **separate endpoints per registered type** with a **discovery catalog endpoint** at the base path. Do NOT use a polymorphic mixed-type list endpoint. Drop `django-rest-polymorphic` from dependencies.

**Rationale**: FairDM portals register domain-specific Sample and Measurement types. API consumers need to understand what types exist before querying them. A discovery-first approach serves this better than a polymorphic list:

1. **Discoverability (FAIR)**: `GET /api/v1/samples/` returns a catalog — type names, descriptions, field schemas, endpoint URLs, record counts. A developer immediately sees what the portal offers without prior knowledge of registered types.
2. **Clean OpenAPI schemas**: Each type-specific endpoint has a single, precise request/response schema. Polymorphic endpoints produce `oneOf` schemas that many code generators (Python, TypeScript, Java) handle poorly.
3. **Type-specific filtering**: Each endpoint exposes only the filters relevant to that type (e.g., `rock_type` for RockSample, `soil_composition` for SoilSample). A polymorphic endpoint cannot cleanly expose type-specific filters.
4. **Simpler implementation**: No polymorphic serializer mapping. Each viewset is a plain `ModelViewSet` with one serializer. One fewer dependency.
5. **Performance**: No polymorphic query JOINs. Type-specific querysets hit concrete tables directly.

**URL structure**:

```
GET /api/v1/samples/                    → Discovery catalog (read-only)
GET /api/v1/samples/rock-samples/       → RockSample list (full CRUD)
GET /api/v1/samples/rock-samples/{uuid}/ → RockSample detail
GET /api/v1/measurements/               → Discovery catalog (read-only)
GET /api/v1/measurements/seismic-data/  → SeismicData list (full CRUD)
```

**"All samples for dataset X"**: Handled by filtering each type endpoint with `?dataset={uuid}`. The discovery endpoint includes record counts per type, so a client can check which types have data for a given dataset without querying all endpoints.

**Alternatives considered**:

- `django-rest-polymorphic` with `PolymorphicSerializer` — produces mixed-type responses that are hard to consume, generates poor OpenAPI schemas with `oneOf`, requires an extra dependency, and doesn't add value when separate endpoints exist.
- Manual `to_representation` override — error-prone, doesn't integrate with OpenAPI schema generation.
- No discovery endpoint (separate endpoints only) — functional but requires API consumers to know type names in advance; violates FAIR discoverability.

---

## R5: Translated Field Serialization — DEFERRED

**Decision**: `django-parler-rest` is **NOT included in this feature**. It is deferred to the spec covering `fairdm.contrib.identity` (which owns the translatable models requiring it).

**Rationale**: The `fairdm.contrib.identity` app contains models with translated fields (e.g., `IdentifierType`) that need `TranslatedFieldsField` / `TranslatableModelSerializer`. That feature spec is the correct place to introduce `django-parler-rest` and document its integration pattern. Adding it here would be premature — no models in scope for Feature 011 require translated field serialization.

**Deferred to**: Future spec for `fairdm.contrib.identity` REST serialization.

**Alternatives considered for that future spec**:

- Manual serializer fields per language — verbose and error-prone.
- Ignoring translations in API — loses multilingual data.

---

## R6: CORS Configuration

**Decision**: Use `django-cors-headers` for Cross-Origin Resource Sharing support.

**Rationale**: API consumers (SPAs, Jupyter notebooks, external tools) will make cross-origin requests. `django-cors-headers` is the standard Django middleware for CORS. It integrates cleanly with Django middleware and supports per-origin allowlisting, credential support, and configurable headers.

**Configuration**:

```python
INSTALLED_APPS = [
    ...
    "corsheaders",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # must be as high as possible
    ...
]

# Default: restrictive. Portal operators configure allowed origins.
CORS_ALLOWED_ORIGINS = []  # populated from env or portal settings
CORS_ALLOW_CREDENTIALS = True
```

---

## R7: drf-schema-adapter — DROPPED

**Decision**: Do NOT use `drf-schema-adapter`. Build the auto-registration router in-house.

**Rationale**: Originally considered for its `drf_auto_endpoint` module (auto-generated viewsets/serializers/router). After review, the package is unnecessary:

1. **Redundant with existing infrastructure**: FairDM's registry already provides model iteration (`registry.samples`, `registry.measurements`, `get_all_configs()`), and `SerializerFactory` already generates serializers. The only missing piece — viewset generation and router registration — is < 100 lines of straightforward DRF code.
2. **Stale dependency risk eliminated**: Last release 3 years ago (v3.0.6), untested on Django 5.1. Dropping it removes a compatibility risk entirely rather than mitigating it.
3. **Metadata adapters not needed**: The custom `Metadata` adapters that `drf-schema-adapter` provides for richer `OPTIONS` responses are fully covered by `drf-spectacular`'s OpenAPI schema and the discovery catalog endpoints.
4. **Simpler dependency tree**: 7 new dependencies instead of 8.

**What replaces it**: A lightweight `fairdm/api/router.py` that iterates over the FairDM registry and registers auto-generated `ModelViewSet` subclasses on DRF's `DefaultRouter`. See `generate_viewset()` in data-model.md.

---

## R8: Rate Limiting Strategy

**Decision**: Use DRF's built-in throttling classes (`AnonRateThrottle`, `UserRateThrottle`) for rate limiting.

**Rationale**: DRF provides production-ready throttling out of the box. `AnonRateThrottle` throttles by IP for unauthenticated users. `UserRateThrottle` throttles by user ID for authenticated users. Both support configurable rates and use the configured cache backend (Redis in production).

**Alternatives considered**:

- `django-ratelimit` — more granular (per-view) but doesn't integrate with DRF's exception handling.
- Reverse proxy rate limiting (nginx/Cloudflare) — complementary but not sufficient for per-user limits, and not testable from within Django.

**Configuration**:

```python
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
    },
}
```

---

## R9: Permission Mapping for API

**Decision**: Use DRF's `DjangoObjectPermissions` as the base, with a custom subclass to enforce 404 (not 403) for unauthorized access and integrate with the existing cascading permission backends.

**Rationale**: `DjangoObjectPermissions` integrates with django-guardian's object-level permissions. The existing `SamplePermissionBackend` and `MeasurementPermissionBackend` cascade permissions from parent datasets. DRF's permission system calls `has_object_permission()` which in turn calls `user.has_perm()` — this already routes through the cascading backends configured in `AUTHENTICATION_BACKENDS`. A thin custom class is needed to return 404 instead of 403 for unauthorized users, preventing information leakage.

**Alternatives considered**:

- Custom permission class from scratch — unnecessary since cascading backends already work through Django's auth system.
- `rest_framework.permissions.IsAuthenticated` only — insufficient; doesn't enforce object-level permissions.

---

## R10: URL Routing & API Versioning

**Decision**: Mount the API under `/api/v1/` using DRF's `DefaultRouter`. Version via URL path.

**Rationale**: URL-based versioning (`/api/v1/`) is the most discoverable and cacheable strategy. It works naturally with Swagger documentation. When v2 is needed, endpoints can coexist at `/api/v2/` without breaking v1 clients.

**Alternatives considered**:

- Header-based versioning (`Accept: application/vnd.fairdm.v1+json`) — less discoverable, harder to test in browsers.
- Query parameter versioning (`?version=1`) — fragile, pollutes query params.

---

## R11: Guardian Integration for DRF — djangorestframework-guardian

**Decision**: Use `djangorestframework-guardian` for queryset-level permission filtering and permission assignment on create/update.

**Rationale**: This package provides two components that directly address plan requirements:

1. **`ObjectPermissionsFilter`** *(NOT used as a filter backend — see below)*: Would constrain querysets to objects with an explicit guardian `view` permission. Unsuitable here because publicly-visible objects have no guardian permission rows at all, meaning anonymous users would get empty lists.

2. **`ObjectPermissionsAssignmentMixin`**: A serializer mixin that assigns guardian object permissions when objects are created or updated. The `get_permissions_map()` method returns a dict mapping permission codenames to lists of users/groups. This replaces manual `assign_perm()` calls in `perform_create()` / `perform_update()`. **This is the primary reason `djangorestframework-guardian` is retained as a dependency.**

**Integration with FairDMObjectPermissions**: The package's `DjangoObjectPermissions` base provides the exact `perms_map` with `view` permissions pattern needed. The non-disclosure behavior is provided by two components:

- List endpoints: `FairDMVisibilityFilter` (custom, see data-model.md) restricts querysets to `is_public=True` OR guardian-permitted objects → private objects never appear for unauthorized users
- Detail endpoints: `FairDMObjectPermissions` returns 404 for unauthorized access → no information leakage

**Note on ObjectPermissionsFilter**: `ObjectPermissionsFilter` is NOT used as a filter backend. It requires guardian rows for every visible object — assigning guardian entries to all public objects is a scaling anti-pattern. `FairDMVisibilityFilter` replaces it at the list level, using guardian's `get_objects_for_user()` internally only for the private-permitted subset.

**Configuration** (updated):

```python
REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": [
        "fairdm.api.filters.FairDMVisibilityFilter",
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
    ],
}
```

**Alternatives considered**:

- `ObjectPermissionsFilter` directly — cannot handle publicly-visible objects with no guardian rows; returns empty lists for anonymous users.
- Manual queryset filtering in `get_queryset()` — error-prone, must be implemented per viewset, easy to forget for new types.
- Assigning global guardian `view` permissions to every public object — scaling anti-pattern; millions of guardian rows.
- Separate public/private endpoint pairs — doubles the URL surface, forces clients to merge results.


---

## New Additions Research (2026-04-01)

## R12: Exposing Discovery Endpoints in the DRF Browsable API Root

**Decision**: Introduce `FairDMAPIRouter(DefaultRouter)` in `fairdm/api/router.py` that overrides`get_api_root_dict()` to inject the discovery endpoint URL names into the root listing.

**Rationale**: `DefaultRouter` builds its root listing exclusively from viewsets registered via`register()`. Standalone `APIView` URL patterns mounted in `urls.py` are invisible to the root view.The cleanest solution is a minimal router subclass that appends the two discovery URL names to thedict returned by `super().get_api_root_dict()`. No view architecture or URL pattern changes needed.

**Alternatives considered**:

- Convert discovery views to ViewSets with `list()` action  more invasive, requires route registration changes.
- Override `APIRootView.get()` directly  couples to DRF internals; breaks on DRF version changes.
- Inject links via template  not visible to API clients programmatically.

## R13: verbose_name_plural Basename Strategy

**Decision**: `_model_to_slug()` uses `model._meta.verbose_name_plural.lower().replace(' ', '-')`.

**Rationale**: Produces human-readable, Django-idiomatic URL slugs controlled by portal developers via`class Meta: verbose_name_plural`. Per the 2026-04-01 clarification, this supersedes the CamelCase decomposition strategy used in the initial implementation.

**Impact**: URL names change for any model where the verbose_name_plural differs from what CamelCasedecomposition produces (e.g., `RockSample`  old: `rock-sample`, new: `rock-samples`).

**Alternatives considered**: Keep class-name strategy  contradicts the clarified spec assumption.

## R14: flex_menu API for Sidebar MenuGroup

**Decision**: Use existing `MenuGroup` / `MenuItem` from `mvp.menus` (already imported) to add thethree-child API group. Docs URL resolved from `FAIRDM_API_DOCS_URL` Django setting with a sensibledefault.

**Rationale**: Pattern already established for ''Community'' and ''Documentation'' groups in`fairdm/menus/menus.py`. No new dependencies. The setting approach avoids hard-coded external URLs.

**Alternatives considered**: Hard-code FairDM docs URL  inflexible for portals that host their own docs.
