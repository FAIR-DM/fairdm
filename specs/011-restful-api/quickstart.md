# Quickstart: Auto-Generated RESTful API

**Feature**: 011-restful-api

## Goal

Add a RESTful API to FairDM that auto-generates endpoints for every registered model. Portal developers register their Sample and Measurement types as usual — the API layer discovers them and exposes CRUD endpoints, OpenAPI documentation, and authentication without any additional configuration.

## Quick Setup (Portal Developer Perspective)

### 1. Enable the API

No code changes needed. The API app ships with FairDM core and is enabled by default. The following URLs are available as soon as the portal starts:

```
/api/v1/                    → API root
/api/v1/docs/               → Swagger UI
/api/v1/redoc/              → ReDoc
/api/v1/schema/             → OpenAPI 3.0 schema (YAML/JSON)
```

### 2. Register Models (Existing Workflow)

Models registered with the FairDM registry automatically get API endpoints:

```python
# models.py
from fairdm.core.sample.models import Sample

class RockSample(Sample):
    rock_type = models.CharField(max_length=100)
    weight_kg = models.DecimalField(max_digits=10, decimal_places=3)
```

```python
# options.py
from fairdm.registry import register, SampleConfig

@register(RockSample)
class RockSampleConfig(SampleConfig):
    fields = ["rock_type", "weight_kg"]
```

This produces:

- `GET /api/v1/samples/rock-samples/` — list all rock samples
- `GET /api/v1/samples/rock-samples/{uuid}/` — detail
- `POST /api/v1/samples/rock-samples/` — create (authenticated)
- `PATCH /api/v1/samples/rock-samples/{uuid}/` — update (authorized)
- `DELETE /api/v1/samples/rock-samples/{uuid}/` — delete (authorized)
- Plus the rock sample type appears in `GET /api/v1/samples/` (discovery catalog)

### 3. Customize (Optional)

Override the auto-generated serializer in the registration config:

```python
@register(RockSample)
class RockSampleConfig(SampleConfig):
    fields = ["rock_type", "weight_kg"]
    serializer_class = RockSampleSerializer  # custom serializer
```

### 4. Authentication

Obtain a token:

```bash
curl -X POST /api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "user@example.com", "password": "..."}'
# Returns: {"key": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"}
```

Use it:

```bash
curl /api/v1/projects/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
```

## Key Files (Implementation)

```
fairdm/api/
├── __init__.py
├── apps.py              # Django app config
├── permissions.py       # FairDMObjectPermissions (404 non-disclosure)
├── pagination.py        # FairDMPagination (25/page, max 100)
├── viewsets.py          # BaseViewSet + generate_viewset()
├── serializers.py       # Serializer builders, BaseSerializerMixin
├── router.py            # Auto-registration from registry
├── urls.py              # /api/v1/ URL patterns
└── settings.py          # REST_FRAMEWORK defaults

tests/test_api/
├── __init__.py
├── conftest.py          # API-specific fixtures
├── test_permissions.py
├── test_viewsets.py
├── test_serializers.py
├── test_router.py
├── test_pagination.py
└── test_auth.py
```

## Dependencies

All new (added to pyproject.toml):

- `djangorestframework`
- `drf-spectacular[sidecar]`
- `dj-rest-auth`
- `drf-orjson-renderer`
- `django-cors-headers`
- `djangorestframework-guardian`
