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
- [x] T017 [US1] Create `fairdm/api/router.py` with auto-registration logic: instantiate `DefaultRouter` as `fairdm_api_router`, register core model viewsets (ProjectViewSet, DatasetViewSet, ContributorViewSet), iterate `registry.samples` and `registry.measurements` to register auto-generated viewsets with slug-based URL prefixes derived from `verbose_name_plural` *(Note: `_model_to_slug()` was implemented using CamelCase decomposition rather than `verbose_name_plural`; the correct strategy is implemented in T060 as a separate task. T017 is functionally complete for slug generation; T060 corrects the slug strategy.)*
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

### Original Final Phase

T048, T049, T050 fully parallel. T051 before T052.

### Cross-Phase Parallelism (Phases 1–8)

US5 (Phase 7) and US6 (Phase 8) can run in parallel with US3 (Phase 5) and US4 (Phase 6) — they depend only on Phase 2, not on US1–US4.

---

## Phase 9: Base Serializer Classes — Implementation & Tests (FR-006 Expanded)

**Goal**: Implement `BaseSampleSerializer` and `BaseMeasurementSerializer` in
`fairdm/api/serializers.py` with the field sets mandated by FR-006, implement the `_validate_*`
enforcement helpers, update `build_model_serializer()` to accept a `base_class` parameter, then
write complete tests verifying field correctness and `ImproperlyConfigured` enforcement.

> **Note**: These base classes were specified during the 2026-04-01 clarification session and
> **implemented in Phase 9 (T053–T055)**. `fairdm/api/viewsets.py` was cleaned up (no outstanding
> `ImportError`); the `_validate_*` enforcement calls in `generate_viewset()` Tier 3 and the
> `base_class` wiring in the Tier 1/2 auto-generate path were restored in T053.

**Independent Test**: Import `BaseSampleSerializer` and `BaseMeasurementSerializer` from
`fairdm.api.serializers`, assert their `Meta.fields` lists; call `generate_viewset()` for a
registered Sample/Measurement type and confirm the serializer_class inherits from the correct base;
attempt `generate_viewset()` with a non-conforming `serializer_class` and assert `ImproperlyConfigured`.

- [x] T053 [US6] Two files require changes:
  - **`fairdm/api/serializers.py`**: Add `BaseSampleSerializer` (`Meta.model = Sample`, `Meta.fields = ["url", "uuid", "name", "local_id", "status", "dataset", "added", "modified", "polymorphic_ctype"]`) and `BaseMeasurementSerializer` (`Meta.model = Measurement`, `Meta.fields = ["url", "uuid", "name", "sample", "dataset", "added", "modified", "polymorphic_ctype"]`) — both are concrete `(ObjectPermissionsAssignmentMixin, serializers.ModelSerializer)` subclasses implementing `get_permissions_map()`. Add `_validate_sample_serializer(cls)` and `_validate_measurement_serializer(cls)` helpers that raise `django.core.exceptions.ImproperlyConfigured` if `cls` is not a subclass of the relevant base. Update `build_model_serializer()` signature to accept an optional `base_class` parameter (default: `serializers.ModelSerializer`) and use it in the `type(...)` call instead of the hardcoded `serializers.ModelSerializer`.
  - **`fairdm/api/viewsets.py`**: Add top-level imports for `BaseSampleSerializer`, `BaseMeasurementSerializer`, `_validate_sample_serializer`, and `_validate_measurement_serializer` from `fairdm.api.serializers` (these symbols exist in `serializers.py` after the first bullet above is done). Then in `generate_viewset()` Tier 3 path (custom `serializer_class`), re-add the validation calls after `serializer_cls = config._get_class(config.serializer_class)`: call `_validate_sample_serializer(serializer_cls)` if `issubclass(model, Sample)`, or `_validate_measurement_serializer(serializer_cls)` if `issubclass(model, Measurement)` — `Sample` and `Measurement` are already imported at the top of the file. In the Tier 1/2 auto-generate path, pass the correct `base_class` to `build_model_serializer()`: `BaseSampleSerializer` if `issubclass(model, Sample)`, `BaseMeasurementSerializer` if `issubclass(model, Measurement)`, else the default.
- [x] T054 [P] [US6] Write complete test coverage in `tests/test_api/test_serializers.py`: (a) field tests — assert `BaseSampleSerializer.Meta.fields == ["url", "uuid", "name", "local_id", "status", "dataset", "added", "modified", "polymorphic_ctype"]`; assert `BaseMeasurementSerializer.Meta.fields` matches its spec list; assert auto-generated serializer for a registered Sample subtype is `issubclass(..., BaseSampleSerializer)`; same for Measurement subtype. (b) enforcement tests — call `generate_viewset()` with a config whose `serializer_class` is a plain `ModelSerializer` (not inheriting `BaseSampleSerializer`) for a Sample type, assert `ImproperlyConfigured` raised; repeat for Measurement type; assert a correctly subclassed custom serializer (inheriting `BaseSampleSerializer`) succeeds without error

### System Validation — Phase 9

- [x] T055 ⚠️ CRITICAL: Run serializer tests: `poetry run pytest tests/test_api/test_serializers.py -v` — ALL tests MUST pass before proceeding to Phase 10

**Checkpoint — Phase 9 Complete**: Base serializer classes and enforcement helpers implemented. Enforcement calls in `generate_viewset()` restored. Tests in place and passing. Safe to proceed with Phase 10.

---

## Phase 10: Discovery Endpoints in API Root (FR-003/FR-004)

**Goal**: `GET /api/v1/` (the DRF browsable API root) includes `sample-types` and `measurement-types`
links alongside the viewset links, satisfying the "MUST appear in the DRF browsable API root"
clauses of FR-003 and FR-004.

**Independent Test**: Call `GET /api/v1/` with `Accept: application/json`, assert the response JSON
contains keys `"sample-types"` and `"measurement-types"` each with a URL pointing to the correct
discovery endpoint.

- [x] T056 [US1] Introduce `FairDMAPIRouter(DefaultRouter)` in `fairdm/api/router.py`: subclass `DefaultRouter`, override `get_api_root_dict()` to call `super().get_api_root_dict()` then inject `ret["sample-types"] = "api-sample-discovery"` and `ret["measurement-types"] = "api-measurement-discovery"`, return `ret`; replace `fairdm_api_router = DefaultRouter()` with `fairdm_api_router = FairDMAPIRouter()` — no changes to URL patterns or view code required
- [x] T057 [P] [US1] Update `tests/test_api/test_router.py`: add test `test_api_root_contains_discovery_links` — call `GET /api/v1/` with `HTTP_ACCEPT="application/json"`, assert response status 200, assert `"sample-types"` key present in response data with a URL ending in `/api/v1/samples/`, assert `"measurement-types"` key present with a URL ending in `/api/v1/measurements/`; verify no existing `isinstance(fairdm_api_router, DefaultRouter)` assertions break (the new class still passes `isinstance`)

### System Validation — Phase 10

- [x] T058 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check --settings=tests.settings` — MUST pass
- [x] T059 ⚠️ CRITICAL: Run router tests: `poetry run pytest tests/test_api/test_router.py -v` — ALL tests MUST pass

**Checkpoint — Phase 10 Complete**: Browsable API root lists discovery endpoints. FR-003 and FR-004 fully satisfied.

---

## Phase 11: verbose_name_plural Router Basename

**Goal**: `_model_to_slug()` derives URL prefixes and basenames from `model._meta.verbose_name_plural`
(lowercased, spaces → hyphens) instead of CamelCase decomposition of the Python class name.

**Independent Test**: Register a model with `verbose_name_plural = "rock samples"`. Call
`_model_to_slug(model)` and assert it returns `"rock-samples"`. Confirm `fairdm_api_router` contains
a route with prefix `samples/rock-samples` and basename `samples-rock-samples`.

- [x] T060 [US1] Update `_model_to_slug()` in `fairdm/api/viewsets.py`: replace the `re.sub` CamelCase decomposition with `model._meta.verbose_name_plural.lower().replace(" ", "-")`; update the docstring to document the `verbose_name_plural` strategy, explain that portal developers control the slug via `class Meta: verbose_name_plural`, and note the URL stability implication
- [x] T061 [P] [US1] Audit and update URL name assertions in `tests/test_api/test_router.py` and `tests/test_api/test_viewsets.py`: identify all hardcoded URL names (e.g., `rock-sample-list`, `rock-sample-detail`) and update them to match the `verbose_name_plural`-derived form (e.g., `rock-samples-list`, `rock-samples-detail`); confirm each `fairdm_demo` model has an appropriate `verbose_name_plural` set to produce the expected slug
- [x] T062 Update `specs/011-restful-api/quickstart.md`: add a section titled "URL name changes (verbose_name_plural strategy)" documenting before/after slugs for the demo app models and providing an example of setting `class Meta: verbose_name_plural = "..."` to control the generated URL prefix

### System Validation — Phase 11

- [x] T063 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check --settings=tests.settings`
- [x] T064 ⚠️ CRITICAL: Run router and viewset tests: `poetry run pytest tests/test_api/test_router.py tests/test_api/test_viewsets.py -v` — ALL tests MUST pass

**Checkpoint — Phase 11 Complete**: Router slugs derived from `verbose_name_plural`. All URL name assertions updated. quickstart.md documents the migration.

---

## Phase 12: User Story 7 — API Menu Group in Portal Sidebar (Priority: P7)

**Goal**: An "API" `MenuGroup` appears in the portal sidebar after the Measurements entry, containing
three child `MenuItem` links: "Interactive Docs" → `view_name="api-docs"` (resolves to `/api/v1/docs/`), "Browse API" → `view_name="api-root"` (resolves to `/api/v1/`), and
"How to use the API" → `FAIRDM_API_DOCS_URL` (configurable external URL, default `"https://fairdm.org/api/"`).

**Independent Test**: Introspect `AppMenu` children, find the group named "API", assert it has
exactly 3 child items. Assert the first two use `view_name` (not hardcoded `_url`). Assert the
third uses `_url` pointing to `FAIRDM_API_DOCS_URL`.

- [x] T065 Add `FAIRDM_API_DOCS_URL = "https://fairdm.org/api/"` to `fairdm/conf/settings/api.py`; verify it is included when the API settings module is merged — portal developers can override it in their own settings file
- [x] T066 [US7] Add "API" `MenuGroup` to `fairdm/menus/menus.py` after the `MenuCollapse` for Measurements: three child `MenuItem` entries — (1) `name=_("Interactive Docs"), view_name="api-docs", extra_context={"icon": "api"}`, (2) `name=_("Browse API"), view_name="api-root", extra_context={"icon": "api"}`, (3) `name=_("How to use the API"), url=getattr(django_settings, "FAIRDM_API_DOCS_URL", "https://fairdm.org/api/"), extra_context={"icon": "literature"}`; internal links use `view_name` for URL reversal — never hardcoded strings; add `from django.conf import settings as django_settings` import at the top of the file if not already present
- [x] T067 [P] [US7] Create `tests/test_api/test_menu.py`: import `AppMenu` from `mvp.menus` and assert (1) `AppMenu` children contain a group whose `name` resolves to "API", (2) the group has exactly 3 children, (3) the first child has `view_name="api-docs"` and empty `_url`, (4) the second child has `view_name="api-root"` and empty `_url`, (5) the third child has `_url` equal to `FAIRDM_API_DOCS_URL` default (`"https://fairdm.org/api/"`) and empty `view_name`, (6) overriding `settings.FAIRDM_API_DOCS_URL` changes the Django setting value

### System Validation — Phase 12

- [x] T068 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check --settings=tests.settings`
- [x] T069 ⚠️ CRITICAL: Run menu tests: `poetry run pytest tests/test_api/test_menu.py -v` — ALL tests MUST pass

**Checkpoint — Phase 12 Complete**: Sidebar "API" menu group visible on all portal pages. Three child links functional. `FAIRDM_API_DOCS_URL` setting respected.

---

## Final Phase (New Additions): Verification & Documentation

**Purpose**: Developer guide updated for new base class requirements and sidebar setting; full API test suite green.

- [x] T070 [P] Update `docs/portal-development/restful-api.md` (or create if absent): add section "Providing a Custom Serializer" showing how to subclass `BaseSampleSerializer` / `BaseMeasurementSerializer`; show the `ImproperlyConfigured` error message; add section "URL Naming (verbose_name_plural)" documenting the strategy and migration from class-name slugs; add section "API Navigation Sidebar" documenting the "API" menu group and the `FAIRDM_API_DOCS_URL` setting with example override
- [x] T071 ⚠️ CRITICAL: Run full API test suite: `poetry run pytest tests/test_api/ -v` — ALL tests MUST pass
- [x] T072 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check --settings=tests.settings` — MUST pass

**Checkpoint — Phases 9–12 Complete**: Base serializer tests in, API root lists discovery endpoints, router uses verbose_name_plural slugs, sidebar menu group live, developer docs updated.

---
---

## Phase 13: Schema Component Naming Cleanup (Swagger/OpenAPI Quality)

**Goal**: Remove the "API" postfix from auto-generated serializer class names so drf-spectacular produces clean OpenAPI schema component names (e.g., `RockSample` instead of `RockSampleAPI`, `PatchedProject` instead of `PatchedProjectAPI`).

**Independent Test**: Fetch the OpenAPI schema from `/api/v1/schema/`, verify that all component names for registered Sample/Measurement/core types do NOT contain "API" postfix. Verify `Patched*` variants also lack the postfix.

**Breaking Change Notice**: Schema component names change globally. Clients code-generating from the OpenAPI spec (TypeScript, Python via `openapi-generator`) must regenerate. E.g., `RockSampleAPI` → `RockSample`, `PatchedProjectAPI` → `PatchedProject`.

### Tests for Phase 13

- [ ] T073 [P] [US2] Write schema naming tests in `tests/test_api/test_swagger.py`: fetch the OpenAPI schema via `GET /api/v1/schema/`; assert component names for registered Sample types (e.g., `RockSample`, `SoilSample`) do NOT contain "API" postfix; assert component names for registered Measurement types (e.g., `XRFMeasurement`) do NOT contain "API" postfix; assert core model schemas (`Project`, `Dataset`, `Contributor`) also lack "API" postfix; assert `Patched*` variants follow the same clean naming pattern (e.g., `PatchedRockSample` not `PatchedRockSampleAPI`); assert `COMPONENT_SPLIT_PATCH=True` still generates separate `Patched*` components

### Implementation for Phase 13

- [ ] T074 [US2] In `fairdm/api/serializers.py`, rename auto-generated serializer classes: change `build_model_serializer()` line `f"{model.__name__}APISerializer"` to `f"{model.__name__}Serializer"`; verify `_SERIALIZER_CACHE` key does not include the class name (it doesn't — uses `(model, fields, view_name, extra_kwargs, base_class)`) so no cache changes needed
- [ ] T075 [P] [US2] Update any existing test assertions in `tests/test_api/test_serializers.py` that reference the old `*APISerializer` class naming pattern (search for `APISerializer` string); verify the serializer cache still returns the same instance for duplicate calls with identical parameters

### System Validation — Phase 13

- [ ] T076 ⚠️ CRITICAL: Run schema naming tests: `poetry run pytest tests/test_api/test_swagger.py -v` — ALL tests MUST pass
- [ ] T077 ⚠️ CRITICAL: Run full API test suite: `poetry run pytest tests/test_api/ -v` — ALL tests MUST pass (catch regressions from rename)

**Checkpoint — Phase 13 Complete**: Schema component names are clean (`RockSample`, `PatchedProject`, etc.). No "API" postfix in Swagger UI or OpenAPI schema. All existing tests still pass.

---

## Phase 14: Meaningful Endpoint Descriptions (Swagger/OpenAPI Quality)

**Goal**: Replace internal-implementation docstrings with consumer-facing API descriptions that surface in Swagger UI. Generated viewsets pull descriptions from registry configuration; core viewsets get hand-written descriptions.

**Independent Test**: Fetch the OpenAPI schema, verify that operation descriptions for registered types contain text from `config.description` or `config.metadata.description` (NOT "Base viewset for all FairDM API resource endpoints"). Verify core endpoint descriptions don't mention `lookup_field`, `get_queryset`, or `perform_create`.

### Tests for Phase 14

- [ ] T078 [P] [US2] Write endpoint description tests in `tests/test_api/test_swagger.py`: fetch the OpenAPI schema via `GET /api/v1/schema/`; for each registered Sample/Measurement type with a non-empty `config.description` or `config.metadata.description`, assert the GET list operation description contains text from that description; assert NO endpoint descriptions contain the strings "Base viewset for all FairDM API resource endpoints", "lookup_field", "get_queryset()", "perform_create", or "perform_update" (internal implementation details); assert core endpoints (`/api/v1/projects/`, `/api/v1/datasets/`, `/api/v1/contributors/`) have consumer-facing descriptions mentioning what the resource IS

### Implementation for Phase 14

- [ ] T079 [US2] In `fairdm/api/viewsets.py`, update `generate_viewset()` to set `__doc__` on the generated viewset class: after creating the dynamic class, resolve description using priority order: (1) `config.description` if non-empty, (2) `config.metadata.description` if `config.metadata` and non-empty, (3) `model.__doc__` if non-empty, (4) fallback `f"Endpoints for managing {model._meta.verbose_name_plural}."`; set `_GeneratedViewSet.__doc__ = description`
- [ ] T080 [US2] In `fairdm/api/viewsets.py`, replace docstrings on core viewsets: `ProjectViewSet.__doc__` → "Research projects registered in the portal. Projects are the top-level organizational unit containing datasets, samples, and measurements."; `DatasetViewSet.__doc__` → "Datasets within research projects. Each dataset contains samples and associated measurements."; `ContributorViewSet.__doc__` → "People and organizations that contribute to research projects. Contributor profiles are read-only."; `BaseViewSet.__doc__` → brief developer-facing note: "Internal base class — see generated subclasses for API documentation."
- [ ] T081 [P] [US2] Update `fairdm_demo/config.py`: ensure ALL registered model configurations have a non-empty `description` or `metadata.description` value; for models currently without descriptions, add a meaningful 1–2 sentence description explaining what the data type represents (this ensures the demo app demonstrates the description-flow feature)

### System Validation — Phase 14

- [ ] T082 ⚠️ CRITICAL: Run description tests: `poetry run pytest tests/test_api/test_swagger.py -v` — ALL tests MUST pass
- [ ] T083 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check --settings=tests.settings` — MUST pass

**Checkpoint — Phase 14 Complete**: Swagger endpoint descriptions show meaningful model descriptions instead of internal BaseViewSet implementation details. Demo app models all have descriptions that surface in the API docs.

---

## Phase 15: Portal-Developer API Description Customization (Swagger/OpenAPI Quality)

**Goal**: Provide a rich default API description and title, and allow portal developers to customize both via Django settings (`FAIRDM_API_TITLE`, `FAIRDM_API_DESCRIPTION`) without touching framework code.

**Independent Test**: Verify `SPECTACULAR_SETTINGS['DESCRIPTION']` contains key phrases about FairDM, available resources, authentication, and rate limits. Override `FAIRDM_API_TITLE` in test settings and verify the Swagger output reflects the override.

### Tests for Phase 15

- [ ] T084 [P] [US2] Write API description customization tests in `tests/test_api/test_swagger.py`: assert the default `FAIRDM_API_DESCRIPTION` setting (from `fairdm/api/settings.py`) is a multi-line string containing key phrases: "FairDM", "Projects", "Datasets", "Samples", "Measurements", "Contributors", "Authentication" or "Token", "Rate Limits"; assert the default `FAIRDM_API_TITLE` is `"FairDM Portal API"`; assert `SPECTACULAR_SETTINGS['TITLE']` equals `FAIRDM_API_TITLE`; assert `SPECTACULAR_SETTINGS['DESCRIPTION']` equals `FAIRDM_API_DESCRIPTION`; using `@override_settings(FAIRDM_API_TITLE="Custom Portal API")`, verify the setting is accessible and overrideable

### Implementation for Phase 15

- [ ] T085 [US2] In `fairdm/api/settings.py`: define `FAIRDM_API_TITLE = "FairDM Portal API"` and `FAIRDM_API_DESCRIPTION` as a rich multi-line Markdown string (covering available resources, authentication methods, rate limits, link to documentation — see research R17 for content); update `SPECTACULAR_SETTINGS['TITLE']` to reference `FAIRDM_API_TITLE` and `SPECTACULAR_SETTINGS['DESCRIPTION']` to reference `FAIRDM_API_DESCRIPTION`
- [ ] T086 [US2] In `fairdm/conf/setup.py`: ensure that portal-level overrides of `FAIRDM_API_TITLE` and `FAIRDM_API_DESCRIPTION` are reflected in `SPECTACULAR_SETTINGS` after all settings files are merged by updating `SPECTACULAR_SETTINGS['TITLE']` and `['DESCRIPTION']` with `getattr(settings, 'FAIRDM_API_TITLE', FAIRDM_API_TITLE)` and `getattr(settings, 'FAIRDM_API_DESCRIPTION', FAIRDM_API_DESCRIPTION)` at settings finalization time

### System Validation — Phase 15

- [ ] T087 ⚠️ CRITICAL: Run customization tests: `poetry run pytest tests/test_api/test_swagger.py -v` — ALL tests MUST pass

**Checkpoint — Phase 15 Complete**: Rich default API description and title in place. Portal developers can override via `FAIRDM_API_TITLE` / `FAIRDM_API_DESCRIPTION` settings.

---

## Final Phase (Phases 13–15): Verification, Documentation & Visual Inspection

**Purpose**: Developer docs updated for Swagger doc quality improvements; full test suite green; visual verification of Swagger UI.

- [ ] T088 [P] Update `docs/portal-development/restful-api.md`: add section "Customizing the API Description" documenting `FAIRDM_API_TITLE` and `FAIRDM_API_DESCRIPTION` settings with example override; add section "Schema Naming Conventions" explaining that schema names match model class names without postfix; add migration note for clients code-generating from the OpenAPI schema (schema name changes from `*API` to clean names)
- [ ] T089 [P] Update `specs/011-restful-api/quickstart.md`: add section "Swagger Documentation" explaining schema naming convention, endpoint descriptions from registry (`description` / `metadata.description`), and API description/title customization via settings
- [ ] T090 [P] Update `fairdm_demo/config.py` docstrings: ensure each registered config class has a docstring linking to the "Developer Guide > RESTful API > Model Descriptions" documentation section, demonstrating the description-flow pattern for the demo app

### System Validation — Final (Phases 13–15)

- [ ] T091 ⚠️ CRITICAL: Run full API test suite: `poetry run pytest tests/test_api/ -v` — ALL tests MUST pass
- [ ] T092 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check --settings=tests.settings` — MUST pass
- [ ] T093 Visually verify Swagger UI at `/api/v1/docs/` using browser: confirm (1) schema component names have no "API" postfix, (2) endpoint descriptions show model descriptions not BaseViewSet internals, (3) API title and description are rich and informative

**Checkpoint — Phases 13–15 Complete**: Schema names clean, endpoint descriptions meaningful, API description rich and customizable, developer docs updated, Swagger UI verified. Feature 011 fully complete including documentation quality improvements.

---
---

## Dependencies & Execution Order

### Phase Dependencies (Full Feature)

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — **BLOCKS all user story phases**
- **US1 (Phase 3)**: Depends on Phase 2 (T013 + T014 must pass)
- **US2 (Phase 4)**: Depends on US1 (needs registered endpoints to document)
- **US3 (Phase 5)**: Depends on US1 (needs read endpoints before adding write)
- **US4 (Phase 6)**: Depends on US3 (needs write operations to test permission enforcement on CRUD)
- **US5 (Phase 7)**: Depends on Phase 2 — can overlap with US3, US4, US6
- **US6 (Phase 8)**: Depends on Phase 2 — can overlap with US3, US4, US5
- **Polish (Original Final Phase)**: Depends on Phases 3–8 complete
- **Phase 9 (FR-006 impl & tests)**: Depends on Phase 8 complete — implemented `BaseSampleSerializer` / `BaseMeasurementSerializer` in `serializers.py` (T053–T055 ✅); enforcement calls in `generate_viewset()` restored; **BLOCKS** Phases 10–12
- **Phase 10 (API root discovery)**: Depends on Phase 9 (T055 must pass) — constitution-mandated test gate
- **Phase 11 (verbose_name_plural)**: Depends on Phase 10 complete — URL name changes must be stable before slug refactor
- **Phase 12 (US7 sidebar)**: Depends on Phase 11 complete — sequential; independent of Phase 10 technically but ordered for cleanliness
- **Final Phase (Phases 9–12)**: Depends on Phases 9–12 complete
- **Phase 13 (Schema naming)**: Depends on Phases 1–12 complete — modifies `serializers.py`; must validate against full test suite
- **Phase 14 (Endpoint descriptions)**: Depends on Phase 13 (T077 must pass) — modifies `viewsets.py` and `config.py`; serializer rename must be stable
- **Phase 15 (API description customization)**: Depends on Phase 14 (T083 must pass) — modifies `settings.py` and `setup.py`
- **Final Phase (Phases 13–15)**: Depends on Phases 13–15 complete

### User Story Dependencies (Full Feature)

| Story | Depends On | Can Parallelize With |
|-------|-----------|----------------------|
| US1 (P1) | Phase 2 validation (T013+T014) | US5, US6 |
| US2 (P2) | US1 (endpoints must exist) | US5, US6 |
| US3 (P3) | US1 (read endpoints exist) | US5, US6 |
| US4 (P4) | US3 (write operations exist) | US5, US6 |
| US5 (P5) | Phase 2 validation (T013+T014) | US1–US4, US6 |
| US6 (P6) | Phase 2 validation (T013+T014) | US1–US5 |
| US7 (P7) | Phase 11 complete (slug strategy stable) | — |

> **Note**: Phases 13–15 all map to US2 (Interactive API Documentation) as they improve the Swagger/OpenAPI
> documentation quality for the same set of endpoints and schemas.

### Within Each Phase

- Phase 9: T053 (implementation) → T054 (tests) → T055 (validation)
- Phase 10: T056 (implementation) → T057 (tests) → T058/T059 (validation)
- Phase 11: T060 (implementation) → T061 (test updates) → T062 (quickstart) → T063/T064 (validation)
- Phase 12: T065 (setting) → T066 (menu) → T067 (tests) → T068/T069 (validation)
- Final (9–12): T070 parallel with T071/T072; T072 after T071
- Phase 13: T073 (tests) parallel with T075 (test updates); T074 (implementation) → T076/T077 (validation)
- Phase 14: T078 (tests) → T079 (viewset docstrings) → T080 (core viewsets) → T081 (demo config) → T082/T083 (validation)
- Phase 15: T084 (tests) → T085 (settings) → T086 (setup merge) → T087 (validation)
- Final (13–15): T088, T089, T090 all parallel → T091/T092 (validation) → T093 (visual verify)

---

## Parallel Opportunities (Full Feature)

### Phase 8 (US6)

T044 before T045. Linear.

### Phase 9 (FR-006 impl & tests)

T053 (implementation) must complete before T054 (tests) — tests depend on the classes existing. T055 validation after T054.

### Phase 10 (API root)

T056 (implementation) before T057 (test). T058 and T059 sequential validation.

### Phase 11 (verbose_name_plural)

T060 (implementation) before T061 (test audit). T062 (docs) parallel with T061. T063/T064 validation after T060+T061.

### Phase 12 (US7 sidebar)

T065 (setting) before T066 (menu, needs the setting name). T067 (tests) after T066. T068/T069 validation.

### Final Phase (Phases 9–12)

T070 (docs) parallel with T071 (test run) and T072 (system check). T072 after T071.

### Phase 13 (Schema naming)

T073 (tests) and T075 (test updates) are parallel with each other. T074 (rename implementation) can start anytime. T076 and T077 sequential validation after T073+T074+T075.

### Phase 14 (Endpoint descriptions)

T078 (tests) before T079. T079 before T080 (both in `viewsets.py`). T081 (demo config) parallel with T079/T080. T082/T083 validation after all.

### Phase 15 (API description customization)

T084 (tests) before T085. T085 before T086 (settings → setup merge). T087 validation after T084+T085+T086.

### Final Phase (Phases 13–15)

T088, T089, T090 fully parallel (docs, quickstart, demo config updates). T091 (tests) and T092 (system check) after all three. T093 (visual verify) after T092.

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
7. Remediate constitution violation: Phase 9 (base serializer tests — test-first)
8. Fix API root discovery: Phase 10 (FairDMAPIRouter)
9. Correct URL naming: Phase 11 (verbose_name_plural slug strategy)
10. Add sidebar navigation: Phase 12 (US7 — API menu group)

11. Swagger/OpenAPI schema naming: Phase 13 (remove "API" postfix)
12. Swagger endpoint descriptions: Phase 14 (registry-driven descriptions)
13. API description customization: Phase 15 (portal-developer settings)

**Total Tasks**: 93 (T001–T093)
**Tasks per story**: US1=10+5=15 (incl. validation), US2=4+21=25 (incl. Phases 13–15), US3=6, US4=5, US5=4, US6=4+3=7 (incl. Phase 9), US7=5 (Phase 12)
**Validation checkpoints**: 33 ⚠️ CRITICAL system validation tasks across all phases
**Parallel opportunities**: 28 tasks marked [P]
