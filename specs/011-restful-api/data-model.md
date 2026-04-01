# Data Model: Auto-Generated RESTful API

**Feature**: 011-restful-api
**Date**: 2026-03-31

## Overview

This feature does NOT add new database models. It creates an API layer that exposes the existing core models (Project, Dataset, Sample, Measurement, Contributor) and registry-registered custom types through auto-generated REST endpoints.

The data model document describes the runtime objects, configurations, and structures that the API module creates.

---

## Existing Models Exposed via API

### Core Models (always available)

| Model | App | Polymorphic | Lookup Field | Manager | Visibility Filter |
|-------|-----|-------------|--------------|---------|-------------------|
| `Project` | `fairdm.core.project` | No | `uuid` | `ProjectQuerySet` | `get_visible()` excludes non-public |
| `Dataset` | `fairdm.core.dataset` | No | `uuid` | `DatasetQuerySet` | Default excludes PRIVATE |
| `Person` | `fairdm.contrib.contributors` | Yes (Contributor) | `uuid` | default | public profiles only |
| `Organization` | `fairdm.contrib.contributors` | Yes (Contributor) | `uuid` | default | all |

### Registry-Registered Models (dynamic, per-portal)

| Model Base | Registry Property | Polymorphic | Lookup Field | Permission Cascade |
|------------|-------------------|-------------|--------------|-------------------|
| `Sample` | `registry.samples` | Yes | `uuid` | Dataset → Sample |
| `Measurement` | `registry.measurements` | Yes | `uuid` | Dataset → Measurement |

---

## Runtime Objects

### BaseAPIConfig (settings module)

Configuration class that lives in `fairdm/api/settings.py` (or `fairdm/conf/settings/api.py`). Provides the DRF `REST_FRAMEWORK` dict and related settings.

```python
# Settings structure (merged into Django settings)
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
```

### FairDMVisibilityFilter

Custom DRF filter backend in `fairdm/api/filters.py`. Replaces `ObjectPermissionsFilter` from `djangorestframework-guardian` as the list-level visibility gate.

```
class FairDMVisibilityFilter(BaseFilterBackend):
    """
    Restricts list querysets to objects the requesting user can see:
      - Objects where is_public=True are always included (anonymous-safe)
      - Objects where the user has an explicit guardian 'view' permission

    Combines both sets via queryset union to avoid N+1 queries.
    Uses get_objects_for_user() from guardian for the private-permitted set.

    Replaces ObjectPermissionsFilter which requires explicit guardian entries
    for ALL objects — unsuitable for publicly-visible records that have no
    guardian permission rows at all.
    """

    def filter_queryset(self, request, queryset, view):
        if request.user.is_authenticated:
            public_qs = queryset.filter(is_public=True)
            permitted_qs = get_objects_for_user(
                request.user,
                f"{queryset.model._meta.app_label}.view_{queryset.model._meta.model_name}",
                queryset,
            )
            return (public_qs | permitted_qs).distinct()
        # Anonymous: public only
        return queryset.filter(is_public=True)
```

Notes:
- `is_public` field must exist on models exposed via the API (Project, Dataset, Sample, Measurement). The existing `ProjectQuerySet.get_visible()` and `DatasetQuerySet` already implement similar logic — `FairDMVisibilityFilter` provides a uniform API-layer equivalent.
- `djangorestframework-guardian`'s `ObjectPermissionsFilter` is NOT used as a filter backend (it cannot handle objects with no guardian entries). The package is retained for `ObjectPermissionsAssignmentMixin` only.
- For models that don't have `is_public` (e.g., Contributor), override `filter_queryset()` in the viewset or subclass the filter.

---

### FairDMObjectPermissions

Custom DRF permission class in `fairdm/api/permissions.py`.

```
class FairDMObjectPermissions(DjangoObjectPermissions):
    """
    Extends DjangoObjectPermissions to:
    1. Add 'view' permissions to perms_map (required for guardian integration)
    2. Return 404 (not 403) for objects the user can't view (non-disclosure)
    3. Allow read access for unauthenticated users (public data)
    4. Require authentication for write operations
    """

    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': ['%(app_label)s.view_%(model_name)s'],
        'HEAD': ['%(app_label)s.view_%(model_name)s'],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }

    Behaviour:
    - GET/HEAD/OPTIONS: checked against view permission; FairDMVisibilityFilter
      handles queryset-level filtering so private objects never appear in lists
    - POST/PUT/PATCH/DELETE: requires authenticated user + object-level permission
    - If object exists but user lacks permission: returns 404 (not 403)

    Integration:
    - FairDMVisibilityFilter (queryset filter): restricts lists to public + permitted objects
    - ObjectPermissionsAssignmentMixin (serializer): assigns permissions on create/update
    - Calls user.has_perm() which routes through:
      - ModelBackend (global perms)
      - ObjectPermissionBackend (guardian, per-object)
      - SamplePermissionBackend (cascading from dataset)
      - MeasurementPermissionBackend (cascading from dataset)
      - OrganizationPermissionBackend (org-level)
```

### FairDMPagination

Pagination class in `fairdm/api/pagination.py`.

```
class FairDMPagination(PageNumberPagination):
    """
    Standard pagination with configurable defaults.

    Fields in response:
    - count: int           # total number of results
    - next: str | None     # URL to next page
    - previous: str | None # URL to previous page
    - results: list[dict]  # page of results

    Configurable via:
    - PAGE_SIZE setting (default: 25)
    - ?page_size query parameter (max: 100)
    """
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100
```

### BaseViewSet

Base viewset class in `fairdm/api/viewsets.py` that all auto-generated and custom viewsets inherit from.

```
class BaseViewSet(ModelViewSet):
    """
    Base viewset for FairDM API.

    Provides:
    - lookup_field = "uuid"  # all core models use a shortuuid field named `uuid`; URLs are short and URL-safe
    - get_queryset() that respects visibility/privacy
    - Automatic filterset_class from registry where available
    - Default ordering

    Methods:
    - get_queryset(): returns user-scoped queryset
    - get_serializer_class(): returns serializer from registry config
    - perform_create(serializer): enforces create permissions
    - perform_update(serializer): enforces update permissions
    - perform_destroy(instance): enforces delete permissions
    """
```

### SampleDiscoveryView / MeasurementDiscoveryView

Read-only API views at the base sample/measurement paths that return a catalog of all registered types with metadata.

```
GET /api/v1/samples/
Response:
{
    "types": [
        {
            "name": "RockSample",
            "verbose_name": "Rock Sample",
            "verbose_name_plural": "Rock Samples",
            "app_label": "fairdm_demo",
            "endpoint": "/api/v1/samples/rock-samples/",
            "description": "..."  // from ModelMetadata if available
            "fields": ["rock_type", "weight_kg", "collection_date"],
            "filterable_fields": ["rock_type", "collection_date"],
            "count": 42
        },
        ...
    ]
}

GET /api/v1/measurements/
Response: (same structure)
```

These views are plain `APIView` subclasses (not viewsets) that iterate over the registry
and build the response from each config's metadata. They are read-only (GET only),
non-paginated (the number of registered types is always small), and do not require
authentication.

### Auto-Generated Router Registration

The router registration happens in `fairdm/api/router.py` at module load time (URL resolution). It iterates over the registry and creates viewset/URL pairs.

FairDM exposes this router as the public `fairdm_api_router` symbol. Portal developers import it to register custom viewsets:

```python
# In portal's urls.py or api.py
from fairdm.api.router import fairdm_api_router

fairdm_api_router.register(r"my-custom", MyCustomViewSet, basename="my-custom")
```

Custom-registered viewsets are included automatically in the OpenAPI schema and appear under `/api/v1/` alongside the auto-generated endpoints.

```
Router registration logic:
1. Register core model endpoints:
   - /api/v1/projects/           → ProjectViewSet
   - /api/v1/datasets/           → DatasetViewSet
   - /api/v1/contributors/       → ContributorViewSet

2. Register discovery endpoints (read-only catalog views):
   - /api/v1/samples/            → SampleDiscoveryView
   - /api/v1/measurements/       → MeasurementDiscoveryView

3. For each registered Sample type (registry.samples):
   - /api/v1/samples/{slug}/     → auto-generated ViewSet
   - slug derived from model verbose_name_plural (e.g., "rock-samples")

4. For each registered Measurement type (registry.measurements):
   - /api/v1/measurements/{slug}/ → auto-generated ViewSet
   - slug derived from model verbose_name_plural

5. Register auth endpoints:
   - /api/v1/auth/               → dj-rest-auth URLs
```

---

## URL Pattern Summary

| URL Pattern | ViewSet/View | Method(s) | Auth Required |
|-------------|-------------|-----------|---------------|
| `/api/v1/projects/` | ProjectViewSet | GET, POST | POST only |
| `/api/v1/projects/{uuid}/` | ProjectViewSet | GET, PUT, PATCH, DELETE | PUT/PATCH/DELETE |
| `/api/v1/datasets/` | DatasetViewSet | GET, POST | POST only |
| `/api/v1/datasets/{uuid}/` | DatasetViewSet | GET, PUT, PATCH, DELETE | PUT/PATCH/DELETE |
| `/api/v1/contributors/` | ContributorViewSet | GET | No |
| `/api/v1/contributors/{uuid}/` | ContributorViewSet | GET | No |
| `/api/v1/samples/` | SampleDiscoveryView | GET | No |
| `/api/v1/samples/{type-slug}/` | Auto-generated ViewSet | GET, POST | POST only |
| `/api/v1/samples/{type-slug}/{uuid}/` | Auto-generated ViewSet | GET, PUT, PATCH, DELETE | PUT/PATCH/DELETE |
| `/api/v1/measurements/` | MeasurementDiscoveryView | GET | No |
| `/api/v1/measurements/{type-slug}/` | Auto-generated ViewSet | GET, POST | POST only |
| `/api/v1/measurements/{type-slug}/{uuid}/` | Auto-generated ViewSet | GET, PUT, PATCH, DELETE | PUT/PATCH/DELETE |
| `/api/v1/auth/login/` | dj-rest-auth | POST | No |
| `/api/v1/auth/logout/` | dj-rest-auth | POST | Yes |
| `/api/v1/auth/user/` | dj-rest-auth | GET, PUT | Yes |
| `/api/v1/auth/password/change/` | dj-rest-auth | POST | Yes |
| `/api/v1/auth/password/reset/` | dj-rest-auth | POST | No |
| `/api/v1/schema/` | drf-spectacular | GET | No |
| `/api/v1/docs/` | SpectacularSwaggerView | GET | No |
| `/api/v1/redoc/` | SpectacularRedocView | GET | No |

---

## ViewSet Generation Logic

For each registered model config, the auto-generated viewset is constructed as:

```python
def generate_viewset(config: ModelConfiguration, base_class: type = BaseViewSet) -> type:
    """Generate a ModelViewSet for a registered model config.

    Args:
        config: The ModelConfiguration from the registry
        base_class: Base viewset class (default: BaseViewSet)

    Returns:
        A ModelViewSet subclass configured for the model
    """
    attrs = {
        "serializer_class": config.serializer,
        "queryset": config.model.objects.all(),
        "lookup_field": "uuid",
    }

    # Attach filterset if available
    if config.filterset is not None and config.filterset is not type:
        attrs["filterset_class"] = config.filterset

    viewset_name = f"{config.model.__name__}ViewSet"
    return type(viewset_name, (base_class,), attrs)
```

---

## Serializer Enhancement Notes

The existing `SerializerFactory` in the registry already produces working `ModelSerializer` subclasses. For the API, the following enhancements are needed:

1. **URL field**: Add a `HyperlinkedIdentityField` or `url` field pointing to the API detail endpoint
2. **Read-only vs writable**: The factory-generated serializer may need to distinguish between read and write representations
3. **Nested relationships**: For related objects (e.g., dataset.project), use `StringRelatedField` for reads and `PrimaryKeyRelatedField` for writes
4. **Permission assignment on create/update**: Use `ObjectPermissionsAssignmentMixin` from `djangorestframework-guardian` to auto-assign guardian permissions when objects are created or updated via the API. The `get_permissions_map()` method maps permission codenames to users/groups.

---

## Permission Decision Matrix

| Operation | Anonymous | Authenticated (no perm) | Viewer | Editor | Owner |
|-----------|-----------|------------------------|--------|--------|-------|
| List (public) | ✅ | ✅ | ✅ | ✅ | ✅ |
| List (private) | ❌ (hidden) | ❌ (hidden) | ✅ | ✅ | ✅ |
| Detail (public) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Detail (private) | 404 | 404 | ✅ | ✅ | ✅ |
| Create | 403 | 403 | 403 | ✅ | ✅ |
| Update | 404 | 404 | 403 | ✅ | ✅ |
| Delete | 404 | 404 | 403 | ✅ | ✅ |
