# Tasks: Auto-Generated RESTful API

**Input**: Design documents from `/specs/011-restful-api/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/api.md ✅, quickstart.md ✅

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1–US6)
- Exact file paths are included in every task description

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the `fairdm/api/` package skeleton, add all 6 new dependencies, and register apps.

- [x] T001 Create `fairdm/api/` package with `__init__.py` (empty module)
- [x] T002 Add 6 API dependencies to `pyproject.toml` (`djangorestframework`, `drf-spectacular[sidecar]`, `drf-orjson-renderer`, `dj-rest-auth`, `django-cors-headers`, `djangorestframework-guardian`) and run `poetry install`
- [x] T003 Create `fairdm/api/apps.py` with `FairDMApiConfig` AppConfig (name `fairdm.api`, verbose_name "FairDM API")
- [x] T004 Register new apps in `fairdm/conf/settings/apps.py` INSTALLED_APPS: add `fairdm.api`, `rest_framework`, `rest_framework.authtoken`, `drf_spectacular`, `drf_spectacular_sidecar`, `corsheaders`, `dj_rest_auth`; uncomment `corsheaders.middleware.CorsMiddleware` in MIDDLEWARE

### System Validation — Phase 1

- [x] T005 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` — MUST pass before proceeding to Phase 2

**Checkpoint — Setup Complete**: Package exists, all dependencies installed, apps registered, system checks pass.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create all base classes and configuration that every user story depends on. No API endpoints are exposed yet — this phase builds the building blocks.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T006 Create `fairdm/api/settings.py` with `REST_FRAMEWORK` dict (authentication classes, permission classes, renderer classes with ORJSONRenderer, parser classes with ORJSONParser, schema class, pagination class, throttle classes/rates, filter backends per data-model.md), `SPECTACULAR_SETTINGS` (title, description, version, sidecar config), and `CORS_*` defaults — integrate into Django settings via `fairdm/conf/settings/` or `fairdm.setup()`
- [x] T007 [P] Create `fairdm/api/pagination.py` with `FairDMPagination(PageNumberPagination)`: `page_size=25`, `page_size_query_param="page_size"`, `max_page_size=100`
- [x] T008 [P] Create `fairdm/api/filters.py` with `FairDMVisibilityFilter(BaseFilterBackend)`: `filter_queryset()` returns `queryset.filter(is_public=True) | get_objects_for_user(user, view_perm, queryset)` for authenticated users, `queryset.filter(is_public=True)` for anonymous — per data-model.md pseudocode; add `hasattr(queryset.model, 'is_public')` guard at the top of `filter_queryset()` to short-circuit models without `is_public` (e.g., Contributor) and return the full unfiltered queryset
- [x] T009 [P] Create `fairdm/api/permissions.py` with `FairDMObjectPermissions(DjangoObjectPermissions)`: extended `perms_map` with view permissions for GET/HEAD/OPTIONS, 404 non-disclosure for unauthorized detail access, unauthenticated read allowed
- [x] T010 [P] Create `fairdm/api/serializers.py` with `BaseSerializerMixin` and serializer generation logic supporting three-tier resolution: `fields` → `serializer_fields` → `serializer_class` from registry config; integrate `ObjectPermissionsAssignmentMixin` from `djangorestframework-guardian` for permission assignment on create/update
- [x] T011 Create `fairdm/api/viewsets.py` with `BaseViewSet(ModelViewSet)`: `lookup_field="uuid"`, `get_queryset()` returning model's default queryset, `get_serializer_class()` resolving from registry config, `filterset_class` attachment from registry; also define explicit `ProjectViewSet(BaseViewSet)`, `DatasetViewSet(BaseViewSet)` (full CRUD; model-specific querysets), and `ContributorViewSet(ReadOnlyModelViewSet)` (GET-only; `lookup_field="uuid"`) — these three core viewset classes are registered by the router in T017 and must exist before T017 runs
- [x] T012 [P] Create `tests/test_api/__init__.py` and `tests/test_api/conftest.py` with API test fixtures: `api_client` (unauthenticated DRF `APIClient`), `authenticated_client` (token-authenticated client), `editor_client` (client with edit permissions), sample/measurement model fixtures using existing factories

### System Validation — Phase 2

- [x] T013 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` — MUST pass before proceeding
- [x] T014 ⚠️ CRITICAL: Run foundational tests: `poetry run pytest tests/test_api/conftest.py --collect-only -v` — ALL fixtures must be importable and collectible before proceeding to any user story

**Checkpoint — Foundation Ready**: All base classes importable, settings merged, test fixtures available. User story phases can now begin.

---

## Phase 3: User Story 1 — Read-Only Browsing of Core Data via API (Priority: P1) 🎯 MVP

**Goal**: Auto-generate read-only list and detail endpoints for all core models (Project, Dataset, Person, Organization) and all registry-registered Sample/Measurement types. Provide discovery catalog endpoints at `/api/v1/samples/` and `/api/v1/measurements/`.

**Independent Test**: Start the portal with demo app models registered, make unauthenticated GET requests to projects list, datasets list, sample discovery, and type-specific sample list endpoints — verify paginated JSON responses with correct fields and navigation links.

- [x] T015 [US1] Add `generate_viewset(config, base_class=BaseViewSet)` factory function to `fairdm/api/viewsets.py` per data-model.md logic: creates a `ModelViewSet` subclass with `serializer_class`, `queryset`, `lookup_field="uuid"`, and optional `filterset_class` from the config
- [x] T016 [US1] Add `SampleDiscoveryView(APIView)` and `MeasurementDiscoveryView(APIView)` to `fairdm/api/viewsets.py` — GET-only views that iterate over `registry.samples` / `registry.measurements` and return the type catalog JSON (name, verbose_name, endpoint URL, fields, filterable_fields, count) per data-model.md and contract §6
- [x] T017 [US1] Create `fairdm/api/router.py` with auto-registration logic: instantiate `DefaultRouter` as `fairdm_api_router`, register core model viewsets (ProjectViewSet, DatasetViewSet, ContributorViewSet), iterate `registry.samples` and `registry.measurements` to register auto-generated viewsets with slug-based URL prefixes derived from `verbose_name_plural`
- [x] T018 [US1] Create `fairdm/api/urls.py` with `/api/v1/` URL patterns: include `fairdm_api_router.urls`, wire `SampleDiscoveryView` at `samples/`, wire `MeasurementDiscoveryView` at `measurements/`, add `dj-rest-auth` URLs at `auth/`, add `SpectacularAPIView` at `schema/`, `SpectacularSwaggerView` at `docs/`, `SpectacularRedocView` at `redoc/`
- [x] T019 [US1] Include API URL patterns in `fairdm/conf/urls.py`: add `path("api/", include("fairdm.api.urls"))` to urlpatterns
- [x] T020 [P] [US1] Write list and detail endpoint tests in `tests/test_api/test_viewsets.py`: GET project list returns paginated JSON with `count`/`next`/`previous`/`results`, GET project detail by uuid returns correct fields, GET dataset list works, GET type-specific sample list returns only samples of that type, GET with invalid uuid returns 404; also cover FR-015 filtering and ordering: `?<field>=<value>` query parameter reduces result set to matching records, `?ordering=<field>` returns results in ascending order, `?ordering=-<field>` returns results in descending order (tests use demo app models that have a FilterSet registered)
- [x] T021 [P] [US1] Write auto-registration and discovery endpoint tests in `tests/test_api/test_router.py`: all registered types produce URL patterns, discovery GET `/api/v1/samples/` returns type catalog with correct metadata (name, endpoint, fields, count), discovery GET `/api/v1/measurements/` returns measurement type catalog, empty registry returns empty catalog; verify `count` in each catalog entry is permission-aware (anonymous user sees only count of public records; authenticated user with additional permissions sees a higher count reflecting their accessible private records)
- [x] T022 [P] [US1] Write pagination tests in `tests/test_api/test_pagination.py`: default page_size=25, custom `?page_size=10` returns 10 results, `?page_size=200` capped at max 100, response includes `next`/`previous` navigation links, `count` reflects total accessible records

### System Validation — Phase 3

- [x] T023 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` — MUST pass before proceeding
- [x] T024 ⚠️ CRITICAL: Run User Story 1 tests: `poetry run pytest tests/test_api/test_viewsets.py tests/test_api/test_router.py tests/test_api/test_pagination.py -v` — ALL tests MUST pass

**Checkpoint — US1 Complete**: All list/detail/discovery endpoints return correct JSON. Pagination works. The API is browseable at `/api/v1/`. This is the MVP — deployable as a read-only API.

---

## Phase 4: User Story 2 — Interactive API Documentation (Priority: P2)

**Goal**: Ensure the drf-spectacular powered Swagger UI, ReDoc, and OpenAPI schema endpoints render correctly and reflect all registered model endpoints with accurate schemas.

**Independent Test**: Navigate to `/api/v1/docs/` in a browser, verify Swagger UI renders showing all registered endpoints grouped by resource type. Verify `/api/v1/schema/` returns a valid OpenAPI 3.0 document. Verify "Try it out" on a GET endpoint returns real data.

- [x] T025 [US2] Verify and refine `SPECTACULAR_SETTINGS` in `fairdm/api/settings.py`: ensure `SERVE_INCLUDE_SCHEMA=False`, sidecar dist paths, portal-overridable `TITLE`/`DESCRIPTION`/`VERSION`, proper schema grouping (one group per resource type, discovery endpoints grouped separately)
- [x] T026 [P] [US2] Write documentation endpoint tests in `tests/test_api/test_docs.py` (separate from `test_router.py` which covers router registration): GET `/api/v1/docs/` returns 200 with HTML containing Swagger UI, GET `/api/v1/redoc/` returns 200 with HTML, GET `/api/v1/schema/` returns valid OpenAPI 3.0 YAML/JSON, schema includes all registered type endpoints with accurate field types and required status, each registered Sample/Measurement type appears as separate endpoint group

### System Validation — Phase 4

- [x] T027 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` — MUST pass before proceeding
- [x] T028 ⚠️ CRITICAL: Run User Story 2 tests: `poetry run pytest tests/test_api/test_docs.py -v` — ALL tests MUST pass

**Checkpoint — US2 Complete**: Interactive documentation accessible, accurate, and reflecting all registered endpoints.

---

## Phase 5: User Story 3 — Authenticated CRUD Operations (Priority: P3)

**Goal**: Enable create, update, and delete operations via the API for authenticated users with appropriate permissions. Wire `dj-rest-auth` login/logout endpoints for token authentication.

**Independent Test**: Authenticate via POST to `/api/v1/auth/login/`, use the returned token to POST a new sample (verify 201), PATCH the sample (verify 200), DELETE the sample (verify 204), confirm deletion via GET (verify 404). Verify unauthenticated POST returns 401.

- [x] T029 [US3] Ensure `BaseViewSet` in `fairdm/api/viewsets.py` enforces authentication for write operations: `perform_create()` checks add permission, `perform_update()` checks change permission, `perform_destroy()` checks delete permission — unauthenticated write attempts return 401 per contract §3/§4/§5
- [x] T030 [US3] Wire `ObjectPermissionsAssignmentMixin` into serializer generation in `fairdm/api/serializers.py`: add `get_permissions_map()` method that assigns guardian object permissions (view, change, delete) to the requesting user when objects are created or updated via API
- [x] T031 [P] [US3] Write authentication endpoint tests in `tests/test_api/test_auth.py`: POST `/api/v1/auth/login/` with valid credentials returns token key, token in `Authorization: Token {key}` header grants access, POST `/api/v1/auth/logout/` revokes token, session authentication works for browser/Swagger UI, invalid credentials return 400
- [x] T032 [P] [US3] Write CRUD operation tests in `tests/test_api/test_viewsets.py`: authenticated POST with valid payload returns 201 + created object, PATCH with partial data returns 200 + updated fields, DELETE returns 204 + subsequent GET returns 404, POST with missing required fields returns 400 with field-level errors, unauthenticated POST returns 401

### System Validation — Phase 5

- [x] T033 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` — MUST pass before proceeding
- [x] T034 ⚠️ CRITICAL: Run User Story 3 tests: `poetry run pytest tests/test_api/test_auth.py tests/test_api/test_viewsets.py -v` — ALL tests MUST pass

**Checkpoint — US3 Complete**: Full CRUD lifecycle works through the API. Authentication endpoints functional. Permission assignment on create/update operational.

---

## Phase 6: User Story 4 — Permission-Enforced Access Control (Priority: P4)

**Goal**: Verify the API enforces object-level permissions identically to the web interface. Private datasets invisible to unauthorized users. Non-disclosure (404 not 403) for all unauthorized access attempts. Cascading permissions for samples/measurements inherited from parent datasets.

**Independent Test**: Create a private dataset. GET as anonymous → 404. GET as unrelated user → 404. GET as dataset owner → 200. PATCH as viewer → 403. PATCH as editor → 200. Verify list endpoint silently excludes private objects from non-permitted users.

- [x] T035 [US4] Verify and refine `FairDMObjectPermissions` in `fairdm/api/permissions.py`: ensure non-disclosure returns 404 (not 403) when user lacks view permission on an existing object, ensure `has_permission()` allows unauthenticated reads but blocks unauthenticated writes, test integration with `SamplePermissionBackend` and `MeasurementPermissionBackend` cascading
- [x] T036 [P] [US4] Write permission enforcement tests in `tests/test_api/test_permissions.py`: full permission matrix per data-model.md (anonymous/authenticated-no-perm/viewer/editor/owner × list-public/list-private/detail-public/detail-private/create/update/delete), non-disclosure 404 for private objects, cascading permissions from dataset to sample/measurement
- [x] T037 [P] [US4] Write visibility filter tests in `tests/test_api/test_filters.py`: public objects visible to anonymous users, private objects hidden from users without guardian view permission, authenticated user with view permission sees private objects, mixed public+private queryset returns correct subset via `.distinct()`, models without `is_public` field handled gracefully

### System Validation — Phase 6

- [x] T038 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` — MUST pass before proceeding
- [x] T039 ⚠️ CRITICAL: Run User Story 4 tests: `poetry run pytest tests/test_api/test_permissions.py tests/test_api/test_filters.py -v` — ALL tests MUST pass

**Checkpoint — US4 Complete**: All permission boundaries enforced. No private data leakage. Non-disclosure behavior verified.

---

## Phase 7: User Story 5 — Rate-Limited Public Access (Priority: P5)

**Goal**: Verify API throttling enforces separate rate limits for anonymous (100/hour) and authenticated (1000/hour) users. Throttled requests return 429 with `Retry-After` header. Rates are configurable per portal.

**Independent Test**: Override throttle rates to small values (e.g., 3/minute), make rapid requests as anonymous user, verify 429 after exceeding limit. Repeat as authenticated user with higher limit. Verify `Retry-After` header present.

- [x] T040 [US5] Verify throttle configuration in `fairdm/api/settings.py` uses `AnonRateThrottle` (100/hour) and `UserRateThrottle` (1000/hour), confirm cache backend availability for throttle state storage, ensure rates are overridable via portal settings
- [x] T041 [US5] Write rate limiting tests in `tests/test_api/test_viewsets.py`: anonymous user exceeds limit → 429 with `Retry-After` header, authenticated user gets higher limit, 429 response includes descriptive message, throttle rates configurable via `REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]` override

### System Validation — Phase 7

- [x] T042 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` — MUST pass before proceeding
- [x] T043 ⚠️ CRITICAL: Run User Story 5 tests: `poetry run pytest tests/test_api/test_viewsets.py -v -k "throttle or rate_limit"` — ALL tests MUST pass

**Checkpoint — US5 Complete**: Rate limiting enforced for both tiers. Portal operators can configure rates.

---

## Phase 8: User Story 6 — Declarative API Configuration for Developers (Priority: P6)

**Goal**: Verify that portal developers can control API field exposure using the same registry configuration patterns used for tables and forms. Three-tier resolution: (1) `fields` fallback, (2) `serializer_fields` override, (3) `serializer_class` full custom class. Configuration changes reflected after restart.

**Independent Test**: Register a model with explicit `serializer_fields` → verify API only exposes those fields. Register another model with a custom `serializer_class` → verify API uses the custom serializer. Register a model with only `fields` → verify API uses those fields as default.

- [x] T044 [US6] Verify and refine three-tier serializer resolution in `fairdm/api/serializers.py`: (1) when only `fields` is set, serializer includes those fields; (2) when `serializer_fields` is set, it overrides `fields` for the API serializer; (3) when `serializer_class` is set, it is used directly without auto-generation; (4) when nothing is set, sensible defaults from model field inspection
- [x] T045 [P] [US6] Write serializer generation tests in `tests/test_api/test_serializers.py`: model with `fields` only → serializer includes those fields, model with `serializer_fields` → only those fields exposed, model with `serializer_class` → custom serializer used directly, model with no field config → default fields from model inspection, URL field present in all generated serializers, config changes reflected after app restart

### System Validation — Phase 8

- [x] T046 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` — MUST pass before proceeding
- [x] T047 ⚠️ CRITICAL: Run User Story 6 tests: `poetry run pytest tests/test_api/test_serializers.py -v` — ALL tests MUST pass

**Checkpoint — US6 Complete**: Registry configuration directly controls API field exposure. Three-tier resolution working.

---

## Final Phase: Polish & Cross-Cutting Concerns

**Purpose**: Demo app verification, documentation, and full integration testing.

- [x] T048 [P] Verify demo app models (`fairdm_demo/`) get auto-generated API endpoints: confirm registered Sample and Measurement types appear in discovery catalogs, list/detail endpoints return correct data, add API smoke test in `fairdm_demo/tests/`
- [x] T049 [P] Add "RESTful API" developer guide section to `docs/portal-development/` covering: automatic endpoint generation, customizing serializer fields, extending the router with custom viewsets, authentication (token obtain + usage), and permission model
- [x] T050 [P] Run quickstart.md validation: verify all code examples from `specs/011-restful-api/quickstart.md` work as documented (model registration → endpoints available, token auth workflow, custom serializer override)

### System Validation — Final

- [x] T051 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` — MUST pass
- [x] T052 ⚠️ CRITICAL: Run full API test suite: `poetry run pytest tests/test_api/ -v` — ALL tests MUST pass

**Checkpoint — Feature Complete**: All API endpoints auto-generated, documented, permission-enforced, rate-limited, and tested. Demo app integration verified.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — **BLOCKS all user story phases**
- **US1 (Phase 3)**: Depends on Phase 2 (T013 + T014 must pass)
- **US2 (Phase 4)**: Depends on US1 (needs registered endpoints to document)
- **US3 (Phase 5)**: Depends on US1 (needs read endpoints before adding write)
- **US4 (Phase 6)**: Depends on US3 (needs write operations to test permission enforcement on CRUD)
- **US5 (Phase 7)**: Depends on Phase 2 — can overlap with US3, US4, US6
- **US6 (Phase 8)**: Depends on Phase 2 — can overlap with US3, US4, US5
- **Polish (Final Phase)**: Depends on all user stories complete

### User Story Dependencies

| Story | Depends On | Can Parallelize With |
|-------|-----------|----------------------|
| US1 (P1) | Phase 2 validation (T013+T014) | US5, US6 |
| US2 (P2) | US1 (endpoints must exist) | US5, US6 |
| US3 (P3) | US1 (read endpoints exist) | US5, US6 |
| US4 (P4) | US3 (write operations exist) | US5, US6 |
| US5 (P5) | Phase 2 validation (T013+T014) | US1–US4, US6 |
| US6 (P6) | Phase 2 validation (T013+T014) | US1–US5 |

### Within Each User Story

- Base infrastructure before viewsets/views
- Router and URL patterns before endpoint tests
- Implementation tasks before corresponding test tasks
- **System validation tasks** (⚠️ CRITICAL) MUST complete before moving to the next phase

---

## Parallel Opportunities

### Phase 2 (Foundational)

T006 must come first (settings). T007, T008, T009, T010, T012 are fully parallel. T011 (BaseViewSet) depends on T009+T010 (uses permissions/serializers).

### Phase 3 (US1)

T015 → T016 → T017 sequential (factory → discovery → router). T018 depends on T017 (urls include router). T019 depends on T018. T020, T021, T022 fully parallel once T019 done.

### Phase 4 (US2)

T025 before T026. T026 is a single parallel test task.

### Phase 5 (US3)

T029 and T030 can be parallel. T031 and T032 parallel once T029+T030 done.

### Phase 6 (US4)

T035 before T036 and T037. T036 and T037 fully parallel.

### Phase 7 (US5)

T040 before T041. Linear.

### Phase 8 (US6)

T044 before T045. Linear.

### Final Phase

T048, T049, T050 fully parallel. T051 before T052.

### Cross-Phase Parallelism

US5 (Phase 7) and US6 (Phase 8) can run in parallel with US3 (Phase 5) and US4 (Phase 6) — they depend only on Phase 2, not on US1–US4.

---

## Implementation Strategy

**MVP Scope** (Phase 1 + Phase 2 + Phase 3 only):

- `fairdm/api/` package created with all base classes
- All 6 dependencies installed and configured
- Auto-generated read-only endpoints for all core + registered models
- Discovery catalog endpoints at `/api/v1/samples/` and `/api/v1/measurements/`
- Pagination working (25/page, max 100)
- Swagger/ReDoc/schema URLs wired (will be tested in US2)
- Auth endpoints wired (will be tested in US3)

This MVP is deployable and delivers the highest-value capability: read-only API access to all portal data with zero configuration from portal developers.

**Incremental Delivery**:

1. MVP: Phases 1–3 (read-only browsing — highest traffic use case)
2. Add documentation: Phase 4 (interactive Swagger/ReDoc)
3. Add CRUD: Phase 5 (authenticated write operations)
4. Add permission enforcement: Phase 6 (object-level access control)
5. Add rate limiting: Phase 7 (abuse protection)
6. Add declarative config: Phase 8 (developer customization)

**Total Tasks**: 52
**Tasks per story**: US1=10 (incl. 2 validation), US2=4 (incl. 2 validation), US3=6 (incl. 2 validation), US4=5 (incl. 2 validation), US5=4 (incl. 2 validation), US6=4 (incl. 2 validation)
**Validation checkpoints**: 17 ⚠️ CRITICAL system validation tasks across all phases (Phase 1 has 1; all other phases have 2)
**Parallel opportunities**: 17 tasks marked [P]
