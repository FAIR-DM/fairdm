# API Contracts: Auto-Generated RESTful API

**Feature**: 011-restful-api
**Date**: 2026-03-31

This document defines the public interface contracts for the FairDM REST API. These are the external-facing interfaces that API consumers depend on.

---

## 1. List Endpoint Contract

**Applies to**: All list endpoints (projects, datasets, contributors, and type-specific sample/measurement endpoints like `/api/v1/samples/rock-samples/`)

### Request

```
GET /api/v1/{resource}/
Headers:
  Accept: application/json (optional, default)
  Authorization: Token {token} (optional)
Query Parameters:
  page: int (default: 1)
  page_size: int (default: 25, max: 100)
  ordering: str (field name, prefix with - for descending)
  {filter_field}: str (from model's filterset configuration)
```

### Response (200 OK)

```json
{
    "count": 42,
    "next": "https://portal.example.com/api/v1/projects/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "uuid": "abc123",
            "url": "https://portal.example.com/api/v1/projects/abc123/",
            "...": "model-specific fields from serializer"
        }
    ]
}
```

### Error Responses

| Status | Condition | Body |
|--------|-----------|------|
| 429 | Rate limit exceeded | `{"detail": "Request was throttled. Expected available in X seconds."}` |

**Contract guarantees**:

- `count` is always the total number of accessible results
- `results` never contains objects the requester doesn't have permission to view
- Private objects are silently excluded from results (no 403)
- Pagination is stable: same query returns same ordering within a transaction

---

## 2. Detail Endpoint Contract

**Applies to**: All detail endpoints

### Request

```
GET /api/v1/{resource}/{uuid}/
Headers:
  Accept: application/json
  Authorization: Token {token} (optional)
```

### Response (200 OK)

```json
{
    "id": 1,
    "uuid": "abc123",
    "url": "https://portal.example.com/api/v1/projects/abc123/",
    "...": "all configured fields for this model"
}
```

### Error Responses

| Status | Condition | Body |
|--------|-----------|------|
| 404 | Object does not exist OR user lacks view permission | `{"detail": "Not found."}` |
| 429 | Rate limit exceeded | `{"detail": "Request was throttled."}` |

**Contract guarantees**:

- 404 is returned for BOTH nonexistent objects and objects the user can't view (non-disclosure)
- Response never includes fields excluded by the serializer configuration

---

## 3. Create Endpoint Contract

**Applies to**: Projects, datasets, samples, measurements

### Request

```
POST /api/v1/{resource}/
Headers:
  Content-Type: application/json
  Authorization: Token {token} (required)
Body:
  {field: value pairs matching writable serializer fields}
```

### Response (201 Created)

```json
{
    "id": 2,
    "uuid": "def456",
    "url": "https://portal.example.com/api/v1/{resource}/def456/",
    "...": "created object fields"
}
```

### Error Responses

| Status | Condition | Body |
|--------|-----------|------|
| 400 | Validation error | `{"field_name": ["Error message."], ...}` |
| 401 | Not authenticated | `{"detail": "Authentication credentials were not provided."}` |
| 403 | Authenticated but lacks create permission | `{"detail": "You do not have permission to perform this action."}` |
| 429 | Rate limit exceeded | `{"detail": "Request was throttled."}` |

**Contract guarantees**:

- 401 is returned for unauthenticated write attempts (not 404)
- 400 errors include field-level detail with all validation failures
- Successful create returns the full object representation

---

## 4. Update Endpoint Contract

**Applies to**: Projects, datasets, samples, measurements

### Request

```
PATCH /api/v1/{resource}/{uuid}/
Headers:
  Content-Type: application/json
  Authorization: Token {token} (required)
Body:
  {field: value pairs to update}
```

### Response (200 OK)

```json
{
    "...": "updated object fields"
}
```

### Error Responses

| Status | Condition | Body |
|--------|-----------|------|
| 400 | Validation error | `{"field_name": ["Error message."], ...}` |
| 401 | Not authenticated | `{"detail": "Authentication credentials were not provided."}` |
| 404 | Object not found OR user lacks view permission | `{"detail": "Not found."}` |
| 429 | Rate limit exceeded | `{"detail": "Request was throttled."}` |

**Contract guarantees**:

- PATCH is partial update (only submitted fields are changed)
- PUT is full update (all writable fields required)
- 404 for unauthorized access (non-disclosure)

---

## 5. Delete Endpoint Contract

### Request

```
DELETE /api/v1/{resource}/{uuid}/
Headers:
  Authorization: Token {token} (required)
```

### Response (204 No Content)

Empty body.

### Error Responses

| Status | Condition | Body |
|--------|-----------|------|
| 401 | Not authenticated | `{"detail": "Authentication credentials were not provided."}` |
| 404 | Object not found OR user lacks permission | `{"detail": "Not found."}` |
| 429 | Rate limit exceeded | `{"detail": "Request was throttled."}` |

---

## 6. Discovery Endpoint Contract

**Applies to**: `/api/v1/samples/` and `/api/v1/measurements/`

These are the primary entry points for exploring registered types. They return a read-only catalog of all registered types with rich metadata — no authentication required.

### Request

```
GET /api/v1/samples/
GET /api/v1/measurements/
```

No query parameters, no pagination (the number of registered types is always small).

### Response (200 OK)

```json
{
    "types": [
        {
            "name": "RockSample",
            "verbose_name": "Rock Sample",
            "verbose_name_plural": "Rock Samples",
            "app_label": "fairdm_demo",
            "endpoint": "/api/v1/samples/rock-samples/",
            "description": "Geological rock samples collected from field sites",
            "fields": ["rock_type", "weight_kg", "collection_date"],
            "filterable_fields": ["rock_type", "collection_date"],
            "count": 42
        },
        {
            "name": "SoilSample",
            "verbose_name": "Soil Sample",
            "verbose_name_plural": "Soil Samples",
            "app_label": "fairdm_demo",
            "endpoint": "/api/v1/samples/soil-samples/",
            "description": "Soil composition samples",
            "fields": ["soil_composition", "depth_cm", "moisture_pct"],
            "filterable_fields": ["soil_composition"],
            "count": 18
        }
    ]
}
```

**Contract guarantees**:

- Every registered Sample/Measurement type appears in the list
- `endpoint` is a valid, working URL that returns instances of that type
- `fields` lists the serializer field names for that type
- `filterable_fields` lists fields that can be used as query parameters on the type endpoint
- `count` reflects the number of records accessible to the requester (respects permissions)
- Order is stable (registration order)
- Response is never paginated (type catalogs are always small)
- No authentication required

---

## 7. Authentication Endpoints Contract

Provided by `dj-rest-auth`. Mounted at `/api/v1/auth/`.

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/api/v1/auth/login/` | POST | No | Returns auth token |
| `/api/v1/auth/logout/` | POST | Yes | Revokes current token |
| `/api/v1/auth/user/` | GET, PUT, PATCH | Yes | Current user details |
| `/api/v1/auth/password/change/` | POST | Yes | Change password |
| `/api/v1/auth/password/reset/` | POST | No | Initiate password reset |
| `/api/v1/auth/password/reset/confirm/` | POST | No | Confirm password reset |

### Login Request

```
POST /api/v1/auth/login/
Content-Type: application/json

{"username": "user@example.com", "password": "..."}
```

### Login Response (200 OK)

```json
{"key": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"}
```

**Contract guarantee**: The returned key is a valid DRF Token that can be used in `Authorization: Token {key}` header.

---

## 8. Rate Limiting Contract

| Tier | Limit | Identified By | Header |
|------|-------|---------------|--------|
| Anonymous | 100 requests/hour | IP address | `Retry-After: {seconds}` |
| Authenticated | 1000 requests/hour | User ID | `Retry-After: {seconds}` |

**Contract guarantees**:

- Throttled requests return 429 with `Retry-After` header
- Rate limits are configurable per portal via `REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]`
- Authentication endpoints are NOT rate-limited by the API throttle (use Django-level protection)

---

## 9. OpenAPI Schema Contract

```
GET /api/v1/schema/
Accept: application/yaml  (or application/json)
```

### Response

A valid OpenAPI 3.0 schema document describing all registered endpoints, their request/response schemas, authentication requirements, and error responses.

**Contract guarantees**:

- Schema reflects 100% of registered endpoints
- Schema includes accurate field types, required status, and descriptions
- Schema is regenerated on each request (reflects current registry state)
- Swagger UI at `/api/v1/docs/` renders the schema interactively
- ReDoc at `/api/v1/redoc/` renders the schema as documentation
