# RESTful API

FairDM automatically generates a fully documented RESTful API for every model you register. You do not need to write any Django REST Framework views, serializers, routers, or URL patterns — the framework handles everything.

## Automatic Endpoint Generation

When you register a Sample or Measurement model, FairDM creates the following endpoints automatically:

```
GET  /api/v1/samples/<model-slug>/          — list all publicly visible records
GET  /api/v1/samples/<model-slug>/{uuid}/   — detail for a specific record
POST /api/v1/samples/<model-slug>/          — create (authenticated users only)
PATCH /api/v1/samples/<model-slug>/{uuid}/  — partial update (authorized users only)
DELETE /api/v1/samples/<model-slug>/{uuid}/ — delete (authorized users only)
```

The `<model-slug>` is derived from your model's `verbose_name_plural` (lowercased, spaces replaced with hyphens). For example, a model with `verbose_name_plural = "rock samples"` becomes `rock-samples`. See [URL Slugs and verbose_name_plural](#url-slugs-and-verbose-name-plural) for details.

Core model endpoints are also available:

| Endpoint | Methods |
|----------|---------|
| `/api/v1/projects/` | GET, POST |
| `/api/v1/projects/{uuid}/` | GET, PATCH, DELETE |
| `/api/v1/datasets/` | GET, POST |
| `/api/v1/datasets/{uuid}/` | GET, PATCH, DELETE |
| `/api/v1/contributors/` | GET |
| `/api/v1/contributors/{uuid}/` | GET |
| `/api/v1/samples/` | GET (discovery catalog) |
| `/api/v1/measurements/` | GET (discovery catalog) |

## Discovery Catalog

`GET /api/v1/samples/` and `GET /api/v1/measurements/` return a machine-readable catalog of all registered types:

```json
{
  "types": [
    {
      "name": "RockSample",
      "verbose_name": "Rock Sample",
      "endpoint": "/api/v1/samples/rock-sample/",
      "fields": ["name", "location", "date_collected"],
      "filterable_fields": ["location", "date_collected"],
      "count": 42
    }
  ]
}
```

The `count` field reflects only records visible to the requesting user (public records for anonymous users, additional private records for authenticated users with guardian permissions).

## Interactive Documentation

FairDM ships a Swagger UI and ReDoc interface powered by [drf-spectacular](https://drf-spectacular.readthedocs.io/):

| URL | Description |
|-----|-------------|
| `/api/v1/docs/` | Swagger UI — try endpoints interactively |
| `/api/v1/redoc/` | ReDoc — clean reference documentation |
| `/api/v1/schema/` | Raw OpenAPI 3.0 schema (YAML) |

## Authentication

### Obtaining a Token

```http
POST /api/v1/auth/login/
Content-Type: application/json

{"email": "user@example.com", "password": "secret"}
```

Response:

```json
{"key": "abc123def456..."}
```

### Using the Token

Include the token in the `Authorization` header of every authenticated request:

```http
GET /api/v1/projects/
Authorization: Token abc123def456...
```

### Session Authentication

Browser-based session authentication is also supported (used automatically by the Swagger UI "Authorize" button).

### Logging Out

```http
POST /api/v1/auth/logout/
Authorization: Token abc123def456...
```

## Permission Model

FairDM's API enforces the same object-level permission model as the web interface:

| Scenario | Result |
|----------|--------|
| Anonymous GET on public object | 200 OK |
| Anonymous GET on private object | 404 Not Found (non-disclosure) |
| Anonymous POST/PATCH/DELETE | 401 Unauthorized |
| Authenticated GET on private object without view perm | 404 Not Found |
| Authenticated PATCH on public object without change perm | 403 Forbidden |
| Authenticated PATCH on private object without any perm | 404 Not Found |
| Owner (has guardian perms) on any operation | 200/201/204 OK |

Non-disclosure (404 instead of 403) is used for unauthorized access to detail endpoints to avoid leaking whether a private object exists.

### Permission Assignment on Create

When you create an object via the API, FairDM's `ObjectPermissionsAssignmentMixin` automatically assigns guardian object permissions (`view_*`, `change_*`, `delete_*`) to the requesting user, making the creator the object owner.

## Customizing Serializer Fields

FairDM uses a three-tier resolution to determine which fields appear in API responses:

### Tier 1 — `fields` (default)

If only `fields` is specified in the registry config, those fields are used for the API serializer:

```python
@fairdm.register
class RockSampleConfig(ModelConfiguration):
    model = RockSample
    fields = ["name", "location", "date_collected", "notes"]
    # API will expose: url, name, location, date_collected, notes
```

### Tier 2 — `serializer_fields` (API-specific override)

Use `serializer_fields` when you want a different set of fields for the API compared to tables/forms:

```python
@fairdm.register
class RockSampleConfig(ModelConfiguration):
    model = RockSample
    fields = ["name", "location", "date_collected", "notes"]           # for forms/tables
    serializer_fields = ["name", "location", "date_collected", "uuid"] # API-only subset
```

### Tier 3 — `serializer_class` (full custom override)

For complete control, provide your own serializer class. **Custom serializers must subclass `BaseSampleSerializer` (or `BaseMeasurementSerializer` for Measurement models)** — omitting this will raise a `django.core.exceptions.ImproperlyConfigured` error at startup.

```python
from fairdm.api.serializers import BaseSampleSerializer

class RockSampleSerializer(BaseSampleSerializer):
    class Meta(BaseSampleSerializer.Meta):
        model = RockSample
        fields = BaseSampleSerializer.Meta.fields + ["location", "date_collected", "lab_code"]
        read_only_fields = ["lab_code"]

@fairdm.register
class RockSampleConfig(ModelConfiguration):
    model = RockSample
    serializer_class = RockSampleSerializer
```

Extending `Meta` from the base class preserves the mandatory fields (`url`, `uuid`, `name`, `status`, `dataset`, `added`, `modified`, `polymorphic_ctype`) that FairDM depends on. You can add, reorder, or override fields — but you cannot remove the mandatory ones without risking broken API clients.

```{warning}
Passing a serializer that does not inherit from `BaseSampleSerializer` or `BaseMeasurementSerializer` raises:

    ImproperlyConfigured: RockSampleSerializer must subclass BaseSampleSerializer.
```

## URL Slugs and verbose_name_plural

FairDM derives the `<model-slug>` component of every endpoint from the model's `verbose_name_plural` metadata (lowercased, spaces → hyphens). This gives you full control over URL structure without touching router configuration.

### Default derivation

The `verbose_name_plural` is set automatically by Django using the `Meta.verbose_name` (or the class name if not specified):

| Model class | Derived slug |
|-------------|--------------|
| `RockSample` (no Meta) | `rock-samples` |
| `SoilSample` (no Meta) | `soil-samples` |
| `XRFMeasurement` (no Meta) | `xrf-measurements` |

### Overriding the slug

Set `Meta.verbose_name_plural` in your model class:

```python
class ThinSection(Sample):
    """Petrographic thin section sample."""

    class Meta(Sample.Meta):
        verbose_name = "thin section"
        verbose_name_plural = "thin sections"  # → endpoint: /api/v1/samples/thin-sections/
```

### Migration note for existing portals

If you are upgrading from a FairDM version that used CamelCase-decomposed slugs, your URL names and endpoint paths have changed. The table below shows the old and new slugs for common patterns:

| Model class | Old slug (CamelCase) | New slug (verbose_name_plural) |
|-------------|----------------------|--------------------------------|
| `RockSample` | `rock-sample` | `rock-samples` |
| `SoilSample` | `soil-sample` | `soil-samples` |
| `WaterSample` | `water-sample` | `water-samples` |
| `XRFMeasurement` | `x-r-f-measurement` | `xrf-measurements` |
| `ICP_MS_Measurement` | `i-c-p-m-s-measurement` | `icp-ms-measurements` |

Update any hardcoded API clients, `{% url %}` references, or OpenAPI schema snapshots after upgrading.

## Extending the Router with Custom Viewsets

If you need a custom viewset for a specific model, you can extend the FairDM router in your portal's `urls.py`:

```python
from fairdm.api.router import fairdm_api_router
from fairdm.api.viewsets import BaseViewSet
from myportal.models import SpecialSample
from myportal.serializers import SpecialSampleSerializer

class SpecialSampleViewSet(BaseViewSet):
    queryset = SpecialSample.objects.all()
    serializer_class = SpecialSampleSerializer

fairdm_api_router.register(r"samples/special-sample", SpecialSampleViewSet, basename="special-sample")
```

## Rate Limiting

The API enforces the following default throttle rates:

| User type | Default rate |
|-----------|-------------|
| Anonymous | 100 requests/hour |
| Authenticated | 1000 requests/hour |

Portal operators can override these in their settings:

```python
# In your portal's settings.py
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
    "anon": "50/hour",
    "user": "500/hour",
}
```

Throttled requests receive a `429 Too Many Requests` response with a `Retry-After` header indicating when the quota resets.

## CORS

The API restricts cross-origin access by default. To allow specific origins (e.g., for a JavaScript frontend):

```python
# In your portal's settings.py
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "https://my-portal-frontend.example.com",
]
```

## OpenAPI Schema Customisation

Override the API title, description, and version in your portal settings:

```python
SPECTACULAR_SETTINGS = {
    "TITLE": "My Research Portal API",
    "DESCRIPTION": "RESTful API for the My Research Portal research data portal.",
    "VERSION": "2.0.0",
}
```

## API Navigation Sidebar

FairDM adds an **API** group to the portal sidebar navigation automatically. It contains three links:

| Link | Target URL |
|------|------------|
| Interactive Docs | `/api/docs/` — Swagger UI |
| Browse API | `/api/v1/` — DRF browsable root |
| How to use the API | `FAIRDM_API_DOCS_URL` (see below) |

### `FAIRDM_API_DOCS_URL`

The third link points to external API documentation. The default value is `"https://fairdm.org/api/"`. Override it in your portal settings:

```python
# In your portal's settings.py
FAIRDM_API_DOCS_URL = "https://my-portal.example.com/docs/api/"
```

The sidebar group and its children are rendered automatically — no template changes are required.
