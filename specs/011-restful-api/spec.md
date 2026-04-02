# Feature Specification: Auto-Generated RESTful API

**Feature Branch**: `011-restful-api`
**Created**: 2026-03-31
**Status**: Draft
**Prerequisites**: Feature 002 (FairDM Registry), Feature 003–006 (Core Models), Feature 009 (Contributors)
**Input**: User description: "RESTful API that automatically populates itself based on the models registered by portal developers, without requiring manual endpoint configuration. Core endpoints for projects, datasets, sample types, measurement types, and contributors. Full CRUD via viewsets. Swagger/OpenAPI docs. Integration with existing auth and permissions. Public access rate-limited; account holders less restricted. Fast and performant."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read-Only Browsing of Core Data via API (Priority: P1)

As a researcher or application developer, I can browse projects, datasets, sample types, measurement types, and contributors through a RESTful API without configuring anything, so that I can programmatically discover and access data published on the portal.

**Why this priority**: Read access is the foundational capability that all other API interactions depend on. It delivers immediate value by enabling programmatic data discovery based on FairDM's FAIR principles. Most API consumers will be read-heavy; listing and retrieving records is the highest-traffic use case.

**Independent Test**: Start a portal with registered Sample and Measurement models, make unauthenticated GET requests to the projects, datasets, samples, measurements, and contributors list endpoints, verify JSON responses with correct data. Test passes when all list and detail endpoints return valid JSON responses containing the expected fields for each model.

**Acceptance Scenarios**:

1. **Given** a portal with registered Sample and Measurement types and published data, **When** a user sends a GET request to the projects list endpoint, **Then** a paginated JSON response is returned containing project records with the fields configured in the registry
2. **Given** a portal with at least two registered Sample types (e.g., RockSample, SoilSample), **When** a user sends a GET request to the sample-types discovery endpoint, **Then** the response lists all registered Sample types with their names and endpoint URLs
3. **Given** a specific Sample type is registered, **When** a user sends a GET request to that type's list endpoint, **Then** only samples of that type are returned with the fields defined in the registry configuration
4. **Given** a project with a known identifier exists, **When** a user sends a GET request to the project detail endpoint using that identifier, **Then** the full project record is returned with all configured fields
5. **Given** a dataset belongs to a project, **When** a user retrieves the dataset detail, **Then** the response includes a reference to the parent project
6. **Given** the list endpoint returns many records, **When** a user requests the list without pagination parameters, **Then** the response is paginated with a configurable default page size and includes navigation links (next, previous, count)

---

### User Story 2 - Interactive API Documentation (Priority: P2)

As a developer integrating with a FairDM portal, I can visit an interactive API documentation page that displays all available endpoints, request/response schemas, and allows me to try out requests directly from the browser.

**Why this priority**: API documentation is essential for developer adoption. Without it, developers cannot discover endpoints or understand schemas. An auto-generated documentation page removes the maintenance burden and ensures docs always match the actual API.

**Independent Test**: Navigate to the API documentation URL in a browser, verify that all registered model endpoints are listed with their schemas, and that the "Try it out" functionality executes a real request and displays the response. Test passes when the documentation page renders without errors and accurately reflects all registered endpoints.

**Acceptance Scenarios**:

1. **Given** a portal is running with registered models, **When** a developer navigates to the API documentation URL, **Then** an interactive documentation page is displayed listing all available endpoints grouped by resource type
2. **Given** a Sample type is registered with specific fields, **When** a developer views that type's endpoint schema in the documentation, **Then** the schema accurately reflects the configured fields, their types, and whether they are required
3. **Given** the documentation page is loaded, **When** a developer uses the "Try it out" feature on a GET endpoint, **Then** a real request is sent and the response is displayed inline
4. **Given** the portal has multiple registered Sample and Measurement types, **When** the documentation page loads, **Then** each registered type appears as a separate endpoint group within the documentation

---

### User Story 3 - Authenticated CRUD Operations (Priority: P3)

As an authenticated portal user with appropriate permissions, I can create, update, and delete records through the API, so that I can manage data programmatically without using the web interface.

**Why this priority**: Write operations extend the API from a read-only data access tool to a full data management interface. This enables integrations, automated data pipelines, and programmatic workflows. It depends on the read endpoints from US1 to be meaningful.

**Independent Test**: Authenticate as a user with editor permissions on a dataset, create a new sample via POST, update it via PATCH, delete it via DELETE, verify each operation succeeds and the changes are reflected in subsequent GET requests. Test passes when the full CRUD lifecycle completes without errors and the data is persisted correctly.

**Acceptance Scenarios**:

1. **Given** a user is authenticated and has edit permission on a dataset, **When** they POST a valid sample payload to the samples endpoint, **Then** a new sample record is created and the response contains the created record with a 201 status
2. **Given** an existing sample record owned by the user, **When** they send a PATCH request with updated field values, **Then** the record is updated and the response reflects the changes
3. **Given** an existing sample record the user has permission to delete, **When** they send a DELETE request, **Then** the record is removed and subsequent GET requests return 404
4. **Given** a user attempts a POST with invalid data (missing required fields), **When** the request is processed, **Then** a 400 response is returned with clear error messages indicating which fields are invalid
5. **Given** a user provides a valid payload but references a non-existent parent (e.g., dataset ID that does not exist), **When** the request is processed, **Then** a 400 response is returned indicating the referenced resource was not found

---

### User Story 4 - Permission-Enforced Access Control (Priority: P4)

As a portal administrator, I need the API to enforce the same object-level permissions as the web interface, so that private datasets remain inaccessible to unauthorized users and contributors can only modify data they have permission to edit.

**Why this priority**: Security is a first-class requirement. Without permission enforcement, the API becomes a data leak vector. This story ensures the API respects the existing guardian-based permission model and visibility settings. It builds on US1 (read) and US3 (write) by adding authorization gates.

**Independent Test**: Create a private dataset, make GET requests as an unauthenticated user (expect 404), as an unrelated authenticated user (expect 404), and as the dataset owner (expect 200). Attempt a PATCH as a non-editor (expect 403) and as an editor (expect 200). Test passes when every permission boundary is correctly enforced.

**Acceptance Scenarios**:

1. **Given** a dataset is marked as private, **When** an unauthenticated user requests it via the API, **Then** the dataset does not appear in list results and a detail request returns 404 (not 403, to avoid leaking existence)
2. **Given** a dataset is marked as private, **When** an authenticated user without permission requests it, **Then** the dataset is not visible in list results and detail returns 404
3. **Given** a dataset is marked as private, **When** the dataset owner requests it via the API, **Then** the full dataset record is returned
4. **Given** a user has "viewer" role on a project, **When** they attempt to create a new dataset under that project via POST, **Then** a 403 response is returned
5. **Given** a user has "editor" role on a project, **When** they create a new dataset under that project via POST, **Then** the dataset is created successfully with a 201 response
6. **Given** a user has no permissions on a sample, **When** they attempt to PATCH or DELETE that sample, **Then** a 404 response is returned (consistent non-disclosure)

---

### User Story 5 - Rate-Limited Public Access (Priority: P5)

As a portal operator, I can configure the API so that unauthenticated users have heavily rate-limited access while authenticated account holders receive higher rate limits, protecting the portal from abuse while keeping data accessible.

**Why this priority**: Rate limiting is essential to prevent abuse and ensure fair resource usage. Public access without limits would expose the portal to scraping and denial-of-service. However, it is lower priority because the API can launch with basic throttling and be tuned later.

**Independent Test**: Make rapid repeated requests as an unauthenticated user and verify that requests are rejected after exceeding the configured threshold. Repeat as an authenticated user and verify a higher limit applies. Test passes when both limits are enforced and appropriate error responses are returned.

**Acceptance Scenarios**:

1. **Given** an unauthenticated user, **When** they exceed the anonymous rate limit, **Then** subsequent requests return 429 (Too Many Requests) with a Retry-After header
2. **Given** an authenticated user, **When** they exceed the authenticated rate limit, **Then** subsequent requests return 429 with a Retry-After header, but the limit is higher than the anonymous limit
3. **Given** rate limiting is active, **When** an unauthenticated user is throttled, **Then** the 429 response includes a clear message explaining rate limits and how to authenticate for higher limits
4. **Given** the rate-limit configuration, **When** a portal operator reviews the settings, **Then** both anonymous and authenticated rate limits are configurable through portal settings

---

### User Story 6 - Declarative API Configuration for Developers (Priority: P6)

As a portal developer, I can configure which fields are exposed in the API for my custom Sample and Measurement types using the same registry system I already use for tables and forms, and optionally provide a custom serializer for advanced needs.

**Why this priority**: Developer experience is critical for framework adoption, but this story is about customization of an already-working API (from US1). The auto-generated defaults should work well enough out of the box; this story enables fine-tuning.

**Independent Test**: Register a Sample type with explicit `serializer_fields`, verify the API only exposes those fields. Then register another type with a custom `serializer_class`, verify the API uses the custom serializer. Test passes when the registry configuration directly controls what the API exposes.

**Acceptance Scenarios**:

1. **Given** a model is registered with only `fields` set (no `serializer_fields`), **When** the API serializer is generated, **Then** it includes the fields from the `fields` configuration
2. **Given** a model is registered with explicit `serializer_fields`, **When** the API serializer is generated, **Then** it includes only the fields listed in `serializer_fields`, overriding the default `fields`
3. **Given** a model is registered with a custom `serializer_class`, **When** the API viewset is created, **Then** it uses the custom serializer class directly without auto-generating one
4. **Given** a model is registered with no explicit field configuration, **When** the API serializer is generated, **Then** it uses sensible defaults by inspecting the model's fields (same behavior as other auto-generated components like tables and forms)
5. **Given** a developer changes the `serializer_fields` or `serializer_class` in their registration, **When** the portal restarts, **Then** the API reflects the updated configuration without any additional steps

---

### User Story 7 - API Menu Group in Portal Sidebar (Priority: P7)

As any portal visitor, I can access the API and its documentation directly from the portal's sidebar navigation menu, so that I can quickly find the interactive API explorer, the browsable API root, and guidance on consuming the API without hunting through the site.

**Why this priority**: Discoverability is valuable but lower priority than a working, secure, documented API. The menu group is pure navigation sugar layered on top of a fully functional API.

**Independent Test**: Load the portal, check the sidebar renders an "API" menu group containing exactly three child links: one to `/api/v1/docs/` (Swagger UI, via `view_name="api-docs"`), one to `/api/v1/` (browsable API root, via `view_name="api-root"`), and one to the FairDM docs page for API consumption. Each link resolves to the correct URL.

**Acceptance Scenarios**:

1. **Given** any portal page is loaded, **When** the sidebar is rendered, **Then** an "API" menu group is visible containing three child menu items
2. **Given** the API menu group is expanded, **When** a user clicks "Interactive Docs", **Then** they are taken to the Swagger UI page at `/api/v1/docs/` (resolved via `view_name="api-docs"`)
3. **Given** the API menu group is expanded, **When** a user clicks "Browse API", **Then** they are taken to the DRF browsable API root at `/api/v1/` (resolved via `view_name="api-root"`)
4. **Given** the API menu group is expanded, **When** a user clicks "How to use the API", **Then** they are taken to the FairDM documentation page covering API consumption (external URL, configurable via setting)
5. **Given** the sidebar is rendered, **Then** the API menu group appears after the Measurements entry, consistent with existing sidebar ordering

---

### Edge Cases

- What happens when no Sample or Measurement types are registered? The API serves only the core model endpoints (projects, datasets, contributors) and the sample/measurement discovery endpoints return empty lists.
- How does the system handle a request for a Sample type endpoint that does not exist? A 404 response with a message indicating the sample type is not registered.
- What happens when a model is registered after the API URLs have been generated (e.g., during testing)? The API URL configuration is generated at startup during URL resolution and reflects whatever is registered at that time.
- How does the API handle concurrent write requests to the same record? Standard database-level concurrency applies; the last write wins. Optimistic locking is out of scope for v1.
- What if a registered model has very large text or binary fields? The API serializer respects the field configuration; if a developer excludes large fields via `serializer_fields`, they are omitted. Default behavior includes all configured fields.
- How does the API respond when the database is unreachable? Standard 500 error responses; detailed error information is not exposed to the client.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST automatically generate API list and detail endpoints for each core model (Project, Dataset) and for the contributor model (Person, Organization) at startup
- **FR-002**: System MUST automatically generate API list and detail endpoints for each Sample and Measurement subtype registered through the FairDM registry
- **FR-003**: System MUST provide a discovery endpoint that lists all registered Sample types with their names and API endpoint URLs. This endpoint MUST appear in the DRF browsable API root (the index listing at `/api/v1/`) alongside all other registered endpoints.
- **FR-004**: System MUST provide a discovery endpoint that lists all registered Measurement types with their names and API endpoint URLs. This endpoint MUST appear in the DRF browsable API root (the index listing at `/api/v1/`) alongside all other registered endpoints.
- **FR-005**: System MUST support full CRUD operations (Create, Read, Update, Delete) on Project, Dataset, Sample, and Measurement endpoints. Contributor endpoints are read-only (GET only) — no create, update, or delete operations are supported for contributors via the API.
- **FR-006**: System MUST auto-generate API data representations for registered models using the existing registry field configuration, respecting the three-tier resolution order (default fields → component-specific fields → custom class override). All auto-generated serializers for Sample subtypes MUST inherit from `BaseSampleSerializer`; all auto-generated serializers for Measurement subtypes MUST inherit from `BaseMeasurementSerializer`. Portal developers who provide a custom `serializer_class` MUST subclass the relevant base; the framework enforces this at registration time.
- **FR-007**: System MUST serve an interactive API documentation page that auto-generates from the registered endpoints and their schemas
- **FR-008**: System MUST enforce the existing object-level permission system on all API operations, including per-object permissions and cascading permission inheritance for samples and measurements
- **FR-009**: System MUST enforce authentication requirements such that write operations (POST, PUT, PATCH, DELETE) require an authenticated user
- **FR-010**: System MUST apply rate limiting with separate thresholds for anonymous and authenticated users
- **FR-011**: System MUST paginate all list endpoints with configurable page sizes and include navigation metadata (next, previous, total count)
- **FR-012**: System MUST return 404 (not 403) for resources the requesting user does not have permission to view, to avoid leaking existence of private data
- **FR-013**: System MUST return structured error responses for validation failures (400) including field-level error details
- **FR-014**: System MUST filter list results using a custom `FairDMVisibilityFilter` backend that returns objects where `is_public=True` OR the requesting user has an explicit guardian `view` permission. Objects matching neither condition are excluded silently from list results. Public objects are always visible regardless of authentication state; private objects require an explicit guardian permission grant.
- **FR-015**: System MUST support filtering and ordering on list endpoints using the existing `FilterSet` configurations from the registry where available
- **FR-016**: System MUST use content negotiation to support JSON as the primary response format
- **FR-017**: System MUST register an "API" menu group in the portal's sidebar navigation (US7) containing exactly three child items: (1) "Interactive Docs" using `view_name="api-docs"` (resolves to `/api/v1/docs/`, Swagger UI), (2) "Browse API" using `view_name="api-root"` (resolves to `/api/v1/`, DRF browsable API root), and (3) "How to use the API" using a static external URL from a configurable Django setting `FAIRDM_API_DOCS_URL` (default: `"https://fairdm.org/api/"`). Internal links MUST use `view_name` for URL reversal — never hardcoded URL strings. The group MUST appear after the Measurements sidebar entry.

### Key Entities

- **API Endpoint**: A URL path mapped to a viewset for a specific model. Generated automatically from the registry. Has a resource name, URL pattern, serializer, and permission configuration.
- **Discovery Endpoint**: A meta-endpoint that lists all registered Sample or Measurement types and their corresponding API URLs. Enables clients to discover available data types dynamically.
- **Serializer**: Defines the fields and representation of a model in API requests and responses. Auto-generated from registry configuration or provided as a custom class by the developer.
- **BaseSampleSerializer**: Abstract DRF `ModelSerializer` base class (in `fairdm/api/serializers.py`) that all Sample subtype serializers MUST inherit from. Exposes the consistent set of fields present on every `Sample` record: `uuid`, `url`, `name`, `local_id`, `status`, `dataset`, `added`, `modified`, and `polymorphic_ctype`. Portal developers must subclass this when providing a custom serializer; auto-generated serializers inherit from it automatically.
- **BaseMeasurementSerializer**: Abstract DRF `ModelSerializer` base class (in `fairdm/api/serializers.py`) that all Measurement subtype serializers MUST inherit from. Exposes the consistent set of fields present on every `Measurement` record: `uuid`, `url`, `name`, `sample`, `dataset`, `added`, `modified`, and `polymorphic_ctype`. Portal developers must subclass this when providing a custom serializer; auto-generated serializers inherit from it automatically.
- **Rate Limit Tier**: A named throttling level (anonymous vs. authenticated) with a configured request count per time window. Applied per-user or per-IP.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001** *(post-launch monitoring target)*: Authenticated users can complete a full CRUD cycle (create, read, update, delete a record) through the API in under 60 seconds using only the documentation page as reference
- **SC-002** *(post-launch monitoring target)*: 95% of API read requests return responses in under 500 milliseconds under normal load
- **SC-003**: All registered Sample and Measurement types are automatically discoverable through the API without any manual endpoint configuration by the portal developer
- **SC-004**: The interactive documentation page accurately reflects 100% of available endpoints and their schemas
- **SC-005**: No private data is accessible to unauthorized users through any API endpoint
- **SC-006**: Rate limiting prevents a single anonymous client from making more than the configured threshold of requests per time window
- **SC-007**: Portal developers can control their API field exposure using the same registry configuration patterns they already use for tables and forms, with no additional boilerplate

## Assumptions

- The existing FairDM registry system and its three-tier field resolution (`fields` → `serializer_fields` → `serializer_class`) will be used as-is for serializer generation; no changes to the registry architecture are needed
- The existing `SerializerFactory` in the registry provides a working base for auto-generating serializers; it may need enhancement but not replacement
- The existing object-level permission system (django-guardian + cascading backends for samples/measurements) is sufficient for API authorization; no new permission models are needed
- JSON is the only required response format for v1; XML or other formats are out of scope
- The API is mounted under a single URL prefix (e.g., `/api/v1/`) and versioned via URL path
- FairDM exposes a shared `fairdm_api_router` instance that portal developers can import to register custom viewsets alongside the auto-generated endpoints; this is the documented extension point for custom API endpoints
- Session-based authentication (for browser/Swagger UI) and DRF Token Authentication (`rest_framework.authtoken`) are both used; `dj-rest-auth` is configured with `REST_USE_JWT = False`. JWT is explicitly out of scope for v1.
- WebSocket or real-time push notifications are out of scope
- File upload/download via the API is out of scope for v1
- The external `fairdm-rest-api` dev dependency package will be replaced by this built-in implementation
- GraphQL or alternative query languages are out of scope; this feature is REST-only
- The DRF router `basename` for auto-generated Sample and Measurement viewsets is derived from `model._meta.verbose_name_plural` (lowercased, spaces replaced with hyphens), NOT the Python class name. For example, a model named `RockSample` with `verbose_name_plural = "rock samples"` gets basename `rock-samples`, producing URL names `rock-samples-list` and `rock-samples-detail`.
- `BaseSampleSerializer` and `BaseMeasurementSerializer` are defined in `fairdm/api/serializers.py`. They are concrete (non-abstract) DRF `ModelSerializer` subclasses tied to the `Sample` and `Measurement` base models respectively. All framework-generated serializers inherit from them; the framework validates `issubclass(custom_cls, BaseSampleSerializer)` (or `BaseMeasurementSerializer`) at registration time and raises `ImproperlyConfigured` if the check fails.
- The configurable FairDM documentation link in the sidebar API menu group is controlled by the Django setting `FAIRDM_API_DOCS_URL` (defined in `fairdm/conf/settings/api.py`). Its default value is `"https://fairdm.org/api/"`. Portal developers can override it in their settings file to point to a custom API usage guide.
- Bulk operations (batch create/update/delete) are out of scope for v1

## Clarifications

### Session 2026-03-31

- Q: How should public objects remain visible to anonymous users given `ObjectPermissionsFilter` requires explicit guardian `view` permissions that public objects don't have? → A: Replace `ObjectPermissionsFilter` with a custom `FairDMVisibilityFilter` backend (in `fairdm/api/filters.py`) that returns `queryset.filter(is_public=True) | queryset.filter(<guardian_view_perm_exists>)`. Single endpoint, no client-side merging, public objects bypass guardian entirely. `ObjectPermissionsFilter` from `djangorestframework-guardian` is NOT used as a filter backend; the package is retained only for `ObjectPermissionsAssignmentMixin` (serializer-level permission assignment on create/update).
- Q: Which token authentication strategy should `dj-rest-auth` use? → A: DRF Token Auth (`rest_framework.authtoken`). One opaque token per user, stored in DB, server-side revocable. `dj-rest-auth` default (`REST_USE_JWT = False`). JWT is out of scope for v1; `djangorestframework-simplejwt` is NOT added as a dependency.
- Q: How should portal developers add custom API endpoints outside of the FairDM registry? → A: FairDM exposes a shared `fairdm_api_router` instance (a DRF `DefaultRouter`). Auto-generated endpoints are registered on this router. Portal developers import it and call `fairdm_api_router.register(...)` from their own `urls.py` or `api.py` to add custom viewsets alongside generated ones. This is the documented extension point. No separate URL prefix required.
- Q: What is `django-parler-rest`'s role in this feature? → A: Removed from Feature 011. It will be introduced in the spec covering `fairdm.contrib.identity`, which owns the translatable models that require `TranslatedFieldsField`. No models in scope for this feature have translated fields. Final dependency count: **6** (dropped from 7).
- Q: What lookup field should API detail URLs use? → A: The existing `uuid` field on all core models. This field is already a shortuuid (generated via `shortuuid`), so URLs are short and URL-safe (e.g., `/api/v1/projects/YK2yFz2gQsSQFXkGd7Eywd/`). `lookup_field = "uuid"` on all viewsets. No separate slug or full UUID field needed.

### Session 2026-04-01

- Q: Should the Sample-types and Measurement-types discovery endpoints appear in the DRF browsable API root index at `/api/v1/`? → A: Yes. Both discovery endpoints MUST appear in the browsable API root listing alongside all other registered endpoints. Implementation must register them via the router (as a ViewSet or custom `APIRoot`) rather than as standalone APIViews that bypass the router listing. FR-003 and FR-004 updated accordingly.
- Q: What strategy should be used for the DRF router `basename` of auto-generated Sample and Measurement viewsets? → A: Use `model._meta.verbose_name_plural`, lowercased and hyphenated (not the Python class name). Example: `RockSample` with `verbose_name_plural = "rock samples"` → basename `rock-samples` → URL names `rock-samples-list`, `rock-samples-detail`. Assumptions section updated accordingly.
- Q: What form should the sidebar API entry take — a single link or a menu group, and what should it link to? → A: A menu group with one heading ("API") and three child links: (1) "Interactive Docs" → `/api/v1/docs/` (Swagger UI, via `view_name="api-docs"`), (2) "Browse API" → `/api/v1/` (DRF browsable API root, via `view_name="api-root"`), (3) "How to use the API" → configurable FairDM docs URL (external, uses `url=`). Internal links MUST use `view_name` for Django URL reversal — hardcoded URL strings are forbidden for internal routes. US7 and FR-017 added accordingly.
- Q: Should there be mandatory base serializer classes for Sample and Measurement subtypes, and what fields must they guarantee? → A: Yes. `BaseSampleSerializer` (fields: `uuid`, `url`, `name`, `local_id`, `status`, `dataset`, `added`, `modified`, `polymorphic_ctype`) and `BaseMeasurementSerializer` (fields: `uuid`, `url`, `name`, `sample`, `dataset`, `added`, `modified`, `polymorphic_ctype`) are defined in `fairdm/api/serializers.py`. Auto-generated serializers inherit from them. Portal developers MUST subclass the relevant base; the framework enforces this at registration time via `issubclass` check raising `ImproperlyConfigured` on violation. FR-006, Key Entities, and Assumptions updated accordingly.
