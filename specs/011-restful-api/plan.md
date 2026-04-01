# Implementation Plan: Auto-Generated RESTful API

**Branch**: `011-restful-api` | **Date**: 2026-03-31 | **Spec**: [spec.md](specs/011-restful-api/spec.md)
**Input**: Feature specification from `/specs/011-restful-api/spec.md`

## Summary

Build a REST API layer (`fairdm/api/`) that auto-generates CRUD endpoints for every model registered in the FairDM registry. Portal developers register Sample and Measurement types as usual; the API discovers them at startup and exposes type-specific CRUD endpoints, discovery catalog endpoints, OpenAPI 3.0 documentation (Swagger UI + ReDoc), token/session authentication, object-level permissions via django-guardian, and rate limiting — all without any manual endpoint configuration.

Technical approach: leverage the existing registry iteration API (`registry.samples`, `registry.measurements`, `get_all_configs()`) and `SerializerFactory` to auto-generate DRF `ModelViewSet` subclasses and register them on a router. Discovery endpoints at `/api/v1/samples/` and `/api/v1/measurements/` provide a read-only catalog of registered types with metadata (field names, filterable fields, record counts, endpoint URLs). Use `drf-spectacular` for OpenAPI schema, `dj-rest-auth` for auth endpoints, `djangorestframework-guardian` for guardian permission filtering and assignment, `drf-orjson-renderer` for fast JSON, and `django-cors-headers` for CORS.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: Django 5.1.3+, djangorestframework, drf-spectacular[sidecar], dj-rest-auth, drf-orjson-renderer, django-cors-headers, djangorestframework-guardian
**Storage**: PostgreSQL (existing)
**Testing**: pytest + pytest-django (existing)
**Target Platform**: Linux server (containerized)
**Project Type**: Django app within the FairDM framework
**Performance Goals**: Sub-200ms p95 for list endpoints with default page size; orjson renderer for fast serialization
**Constraints**: Must integrate with existing registry, existing guardian permission backends, existing allauth authentication
**Scale/Scope**: ~20 auto-generated URL patterns per portal; scales with number of registered types

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. FAIR-First | ✅ PASS | API directly serves FAIR: machine-readable endpoints, stable identifiers (UUID), discoverable metadata, OpenAPI schema. Public read access without custom client code. |
| II. Domain-Driven, Declarative Modeling | ✅ PASS | No new database models. API auto-derives from registry-declared models. Schema declarations remain the single source of truth. |
| III. Configuration Over Custom Plumbing | ✅ PASS | Zero configuration required from portal developers. Registration drives API generation. Override points available (custom serializer_class, custom viewset). |
| IV. Opinionated, Production-Grade Defaults | ✅ PASS | Uses DRF (governance-approved API layer per constitution). Sensible defaults for pagination, throttling, auth. Container-friendly. |
| V. Test-First Quality | ✅ PASS | Test structure mirrors source (`tests/test_api/`). Contract tests for all endpoints. pytest-django fixtures. |
| VI. Documentation Critical | ✅ PASS | drf-spectacular auto-generates OpenAPI docs. Developer guide section planned. |
| VII. Living Demo | ✅ PASS | Demo app's registered models will automatically get API endpoints. Demo app tests will verify API functionality. |

**Post-design re-check**: All gates still pass. Auto-registration handled by a lightweight custom router in `fairdm/api/router.py` — no third-party risk.

## Project Structure

### Documentation (this feature)

```text
specs/011-restful-api/
├── plan.md              # This file
├── spec.md              # Feature specification (6 user stories, 16 FRs)
├── research.md          # Phase 0 output (11 research decisions, R1–R11)
├── data-model.md        # Phase 1 output (runtime objects, URL patterns, permission matrix)
├── quickstart.md        # Phase 1 output (portal developer quick setup guide)
├── contracts/
│   └── api.md           # Phase 1 output (9 endpoint contracts)
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
fairdm/api/
├── __init__.py
├── apps.py              # Django AppConfig for 'fairdm.api'
├── permissions.py       # FairDMObjectPermissions (404 non-disclosure, view perms)
├── filters.py           # FairDMVisibilityFilter (is_public OR guardian view perm)
├── pagination.py        # FairDMPagination (25/page, max 100, page_size param)
├── viewsets.py          # BaseViewSet + generate_viewset() factory
├── serializers.py       # BaseSerializerMixin, serializer builders
├── router.py            # Auto-registration from registry → DRF router; exposes `fairdm_api_router` as public extension point
├── urls.py              # /api/v1/ URL patterns (router + auth + schema + docs)
└── settings.py          # REST_FRAMEWORK defaults, SPECTACULAR_SETTINGS, CORS

tests/test_api/
├── __init__.py
├── conftest.py          # API-specific fixtures (api_client, authenticated_client)
├── test_permissions.py  # FairDMObjectPermissions, non-disclosure, anonymous access
├── test_filters.py      # FairDMVisibilityFilter (public, private, anonymous edge cases)
├── test_viewsets.py     # BaseViewSet, auto-generated viewsets, CRUD operations
├── test_serializers.py  # Serializer generation, type-specific serialization
├── test_router.py       # Auto-registration, URL patterns, discovery endpoints
├── test_pagination.py   # Page size, max page size, navigation links
└── test_auth.py         # Token auth, session auth, login/logout endpoints
```

**Structure Decision**: Single Django app (`fairdm/api/`) within the existing framework, mirroring the pattern of other `fairdm/` subpackages. Test directory mirrors source as required by constitution. No separate frontend — API only.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| 6 new dependencies | Each addresses a distinct, well-scoped concern: token auth + auth endpoints (`dj-rest-auth`), object-level permissions (`djangorestframework-guardian`), OpenAPI schema + Swagger UI (`drf-spectacular[sidecar]`), CORS (`django-cors-headers`), fast JSON rendering (`drf-orjson-renderer`), core DRF (`djangorestframework`). `django-parler-rest` dropped — deferred to future identity spec. | Fewer deps would mean reimplementing well-tested functionality. All are actively maintained, MIT/BSD licensed, and standard in the DRF ecosystem. |
