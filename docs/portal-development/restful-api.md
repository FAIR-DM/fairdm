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

## What a Record Contains

A project, dataset, sample or measurement is returned whole, on its record route and in every row of
its list. The same fields appear in both.

| Kind | Fields of its own | Its parent |
|------|-------------------|------------|
| Project | `url`, `uuid`, `name`, `image`, `status`, `visibility`, `funding`, `added`, `modified` | `owner`, the organization that owns it |
| Dataset | `url`, `uuid`, `name`, `image`, `visibility`, `published`, `added`, `modified` | `project`, and `license` as `{"name", "url"}` |
| Sample | `url`, `uuid`, `name`, `local_id`, `status`, `added`, `modified`, then every field its type declares | `dataset` |
| Measurement | `url`, `uuid`, `name`, `added`, `modified`, then every field its type declares, measured values included | `sample` and `dataset` |

Every one of the four also carries its metadata, which is read-only:

| Field | Holds |
|-------|-------|
| `descriptions` | `{"type", "value"}` for each description |
| `dates` | `{"type", "value"}` for each key date, as a year, a month or a day |
| `identifiers` | `{"type", "value"}` for each external identifier, such as a DOI |
| `keywords` | `{"name", "label", "uri", "vocabulary"}` for each controlled keyword |
| `contributors` | `{"contributor", "roles", "affiliation"}` for each credit, in the order the record's team set |

A credit names the person or organization, the roles they hold on the record as `{"name", "label"}`
and the organization they are credited from. The level a person holds on the record is not shown,
as the record's page does not show it.

A rock sample looks like this:

```json
{
  "url": "https://portal.example.org/api/v1/samples/rock-samples/sxXGUGgXRVStFw3jbpBWQeM/",
  "uuid": "sxXGUGgXRVStFw3jbpBWQeM",
  "name": "RS-14",
  "local_id": "SAMPLE-5165",
  "status": "unknown",
  "dataset": {
    "uuid": "dV4DYUk6ohGJdizhxJotoZ8",
    "url": "https://portal.example.org/api/v1/datasets/dV4DYUk6ohGJdizhxJotoZ8/"
  },
  "added": "2026-10-08T23:25:13.384580Z",
  "modified": "2026-10-08T23:25:13.385372Z",
  "rock_type": "igneous",
  "collection_date": "2024-05-02",
  "descriptions": [{"type": "SampleCollection", "value": "Taken from the north face."}],
  "dates": [{"type": "Created", "value": "2024-05"}],
  "identifiers": [{"type": "IGSN", "value": "10.60516/AU1101"}],
  "keywords": [],
  "contributors": []
}
```

## How Records Refer to Each Other

A record names another by its short identifier and its address in the API, and never by a database
number. No response contains an `id` or a `pk`, and no request is accepted that carries one.

```json
"dataset": {
  "uuid": "dV4DYUk6ohGJdizhxJotoZ8",
  "url": "https://portal.example.org/api/v1/datasets/dV4DYUk6ohGJdizhxJotoZ8/"
}
```

Requesting the `url` returns the record it names. A reference is `null` when the caller may not
see the record it would name. A public dataset can sit in a private project, and a measurement's
sample can be in another, private dataset. Both references read `null` for a visitor and name the
record for someone who holds at least the view level on it, so a response never reveals a record
the caller could not open.

`fairdm.api.serializers.RecordReferenceField` is the field that does this. Use it in a serializer
of your own for a relation to a project, dataset, sample, measurement or contributor:

```python
from fairdm.api.serializers import RecordReferenceField

class RockSampleSerializer(BaseSampleSerializer):
    # A foreign key from RockSample to another sample.
    reference_sample = RecordReferenceField(read_only=True)

    class Meta(BaseSampleSerializer.Meta):
        model = RockSample
        fields = BaseSampleSerializer.Meta.fields + ["reference_sample"]
```

A relation you leave to Django REST Framework's defaults is returned as a database number. Declare
every relation you add as a `RecordReferenceField` or a `StringRelatedField`.

## Contributors

`/api/v1/contributors/` lists the people and organizations the portal's own lists show, so
superusers and the anonymous account are left out. A contributor is returned with what their
profile page shows a visitor:

| Field | Holds |
|-------|-------|
| `url`, `uuid`, `type`, `name`, `image`, `profile` | The profile, with `type` set to `person` or `organization` |
| `identifiers` | `{"type", "value", "link"}`, such as an ORCID iD or a ROR ID |
| `links`, `languages` | The web links and the languages the profile lists |
| `affiliation` | A person's primary organization, or an organization's parent |
| `location` | The city and country of that organization |
| `organization_type` | The kind of organization, `null` for a person |

Nothing about the account behind a person is ever returned: no email address, credential, flag or
sign-in date. Contributors are read-only.

## Filtering, Ordering and Paging

Every list is paged. The response carries `count`, the total number of records the caller may see,
and `next` and `previous`, the addresses of the pages either side.

A sample list takes `?dataset=<short identifier>`, and a measurement list takes that and
`?sample=<short identifier>`, whatever filters the type declares. A database number, an unknown
identifier and the identifier of a dataset the caller may not see are all answered `400`.

```http
GET /api/v1/samples/rock-samples/?dataset=dV4DYUk6ohGJdizhxJotoZ8
GET /api/v1/measurements/xrf-measurements/?sample=sd573eit27hDfnZD98NsqsW
```

A type's own filters, the ones its registration declares, apply as well, for example
`?rock_type=igneous`. These match what the portal's list pages accept.

`?ordering=name` sorts ascending and `?ordering=-name` descending. A list sorts on the stored
fields it returns, such as `name`, `added` and `modified`, and on the fields the type declares.
Relations and metadata cannot be sorted on.

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

The `count` field reflects only records visible to the requesting user (public records for anonymous users, additional private records for authenticated users who hold a level on them).

## Interactive Documentation

FairDM ships a Swagger UI and ReDoc interface powered by [drf-spectacular](https://drf-spectacular.readthedocs.io/):

| URL | URL name | Description |
|-----|----------|-------------|
| `/api/v1/docs/` | `api:api-docs` | Swagger UI — try endpoints interactively |
| `/api/v1/redoc/` | `api:api-redoc` | ReDoc — clean reference documentation |
| `/api/v1/schema/` | `api:api-schema` | Raw OpenAPI 3.0 schema (YAML) |

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
| Creator, or anyone at the manage level, on any operation | 200/201/204 OK |

Non-disclosure (404 instead of 403) is used for unauthorized access to detail endpoints to avoid leaking whether a private object exists.

Three rules about what a request may change apply to projects, datasets, samples and measurements,
and they are the ones the update forms apply:

- **Visibility and the record a record sits under need the manage level.** A `PUT` or `PATCH` that
  sets `visibility`, or a `project`, `dataset` or `sample` field, to a value different from the
  stored one answers 403 and stores nothing unless the requester can manage the record. Sending the
  value already stored is not a change.
- **A move that would leave the record with nobody to manage it answers 400.** The error is on the
  parent field and carries the code `no_manager`.
- **A record is created only inside a parent the requester holds the edit level on.** The
  `project`, `dataset` and `sample` fields of a serializer accept only the records the requester can
  edit, so a `POST` naming any other answers 400 as it does for any value that is not a choice,
  creates nothing and lists nobody.

### Permission Assignment on Create

When you create a project, dataset, sample or measurement via the API, the requesting user is
listed on it at the manage level, which makes them its creator. A superuser who creates one is not
listed, because a superuser cannot be a contributor. No django-guardian permission is stored.

```{note}
For any other model, the serializer still assigns stored guardian permissions (`view_*`,
`change_*`, `delete_*`) to the requesting user. If you are writing portal code outside the API that
grants or checks one of those on a contributor or organization programmatically, use the
`fairdm.core.utils` helpers described in
[Managing Users and Permissions](../portal-administration/managing_users_and_permissions.md)
rather than calling `django-guardian` directly: those records are polymorphic, and a raw guardian
call files or looks for the grant under the wrong content type.
```

## Customizing Serializer Fields

A sample or measurement type always carries the fields common to its kind (see
[What a Record Contains](#what-a-record-contains)) and its metadata. The fields you declare are
added to them, and a field you name that is already common appears once. FairDM resolves the list
you declare in three tiers.

### Tier 1 — `fields` (default)

If only `fields` is specified in the registry config, those fields are added:

```python
@fairdm.register
class RockSampleConfig(BaseSampleConfiguration):
    model = RockSample
    fields = ["name", "rock_type", "collection_date", "weight_grams"]
    # The API returns the common fields, then rock_type, collection_date and weight_grams,
    # then the metadata.
```

A measurement type declares the fields that hold its measured values the same way, and every one
of them is returned:

```python
@fairdm.register
class XRFMeasurementConfig(BaseMeasurementConfiguration):
    model = XRFMeasurement
    fields = ["element", "concentration_ppm", "detection_limit_ppm"]
```

### Tier 2 — `serializer_fields` (API-specific override)

Use `serializer_fields` when you want a different set of fields for the API compared to tables and
forms:

```python
@fairdm.register
class RockSampleConfig(BaseSampleConfiguration):
    model = RockSample
    fields = ["name", "rock_type", "collection_date", "weight_grams"]  # for forms and tables
    serializer_fields = ["rock_type", "collection_date"]               # added to the common fields
```

### Tier 3 — `serializer_class` (full custom override)

For complete control, provide your own serializer class. **Custom serializers must subclass `BaseSampleSerializer` (or `BaseMeasurementSerializer` for Measurement models)** — omitting this will raise a `django.core.exceptions.ImproperlyConfigured` error at startup.

```python
from fairdm.api.serializers import BaseSampleSerializer

class RockSampleSerializer(BaseSampleSerializer):
    class Meta(BaseSampleSerializer.Meta):
        model = RockSample
        fields = BaseSampleSerializer.Meta.fields + ["rock_type", "lab_code"]
        read_only_fields = ["lab_code"]

@fairdm.register
class RockSampleConfig(ModelConfiguration):
    model = RockSample
    serializer_class = RockSampleSerializer
```

Extending `Meta` from the base class keeps the common fields (`url`, `uuid`, `name`, `dataset`, `added`, `modified`, and `local_id` and `status` for a sample, `sample` for a measurement) and the metadata that FairDM depends on. You can add, reorder, or override fields, but you cannot remove the common ones without risking broken API clients.

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

## Customizing the API Description

FairDM ships with a rich default API description and title that appear in Swagger UI and the raw OpenAPI schema. You can override them without modifying the framework:

```python
# In your portal's settings.py
FAIRDM_API_TITLE = "Palaeo-Climate Data Portal API"
FAIRDM_API_DESCRIPTION = """\
## Palaeo-Climate Data Portal API

Programmatic access to all published palaeo-climate data in this portal.

### Resources

- `/api/v1/projects/` — Research projects
- `/api/v1/datasets/` — Sampled datasets
- `/api/v1/samples/` — Discover all sample types

See the [Developer Guide](https://my-portal.example.com/docs/api/) for full details.
"""
```

FairDM merges these settings into `SPECTACULAR_SETTINGS` automatically at startup. You can also override `SPECTACULAR_SETTINGS['VERSION']` directly if you need to change the API version string.

## Schema Naming Conventions

FairDM auto-generates serializer classes for all registered models. The serializer class names follow the pattern `{ModelName}Serializer` (e.g. `RockSampleSerializer`, `XRFMeasurementSerializer`). drf-spectacular strips the `Serializer` suffix when deriving OpenAPI schema component names, so the components appear as clean names in Swagger:

| Model class | Serializer class | Schema component |
|-------------|-----------------|------------------|
| `RockSample` | `RockSampleSerializer` | `RockSample` |
| `XRFMeasurement` | `XRFMeasurementSerializer` | `XRFMeasurement` |
| `Project` | `ProjectSerializer` | `Project` |

`Patched*` components (from `COMPONENT_SPLIT_PATCH=True`) follow the same clean naming pattern:

| Operation | Schema component |
|-----------|-----------------|
| `PATCH /samples/rock-samples/{uuid}/` | `PatchedRockSample` |

:::{note}
**Migration note**: If you were code-generating API clients from an older FairDM OpenAPI schema,
schema component names have changed — `RockSampleAPI` → `RockSample`, `PatchedProjectAPI` →
`PatchedProject`. Regenerate your client code after upgrading.
:::

## Model Descriptions in the API Docs

Swagger UI shows a description for each endpoint group. For auto-generated viewsets, FairDM
resolves the description from the registry configuration using the following priority order:

1. `ModelConfiguration.description` (top-level attribute)
2. `ModelConfiguration.metadata.description` (from `ModelMetadata`)
3. Model class docstring
4. Fallback: `"Endpoints for managing {verbose_name_plural}."`

To provide a meaningful description visible in Swagger, add it to your registry config:

```python
@fairdm.register
class RockSampleConfig(ModelConfiguration):
    model = RockSample
    metadata = ModelMetadata(
        description=(
            "Geological rock samples collected from field sites. Each sample records "
            "lithology, collection date, weight, and mineralogical observations."
        ),
        # ... other metadata ...
    )
    fields = [...]
```

The description is displayed in Swagger UI when users expand the endpoint group for `RockSample`.

## API Navigation Sidebar

FairDM adds an **API** group to the portal sidebar navigation automatically. It contains three links:

| Link | Resolved URL | Implementation |
|------|-------------|----------------|
| Interactive Docs | `/api/v1/docs/` | `view_name="api:api-docs"` |
| Browse API | `/api/v1/` | `view_name="api:api-root"` |
| How to use the API | `FAIRDM_API_DOCS_URL` | static `url=` (external) |

### `FAIRDM_API_DOCS_URL`

The third link points to external API documentation. The default value is `"https://fairdm.org/api/"`. Override it in your portal settings:

```python
# In your portal's settings.py
FAIRDM_API_DOCS_URL = "https://my-portal.example.com/docs/api/"
```

The sidebar group and its children are rendered automatically — no template changes are required.
