# Implementation Plan: Auto-Generated RESTful API (New Additions)

**Branch**: `011-restful-api` | **Date**: 2026-04-02 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/011-restful-api/spec.md`

> **Scope note**: Phases 1–8 of this feature are already implemented (T001–T052 in `tasks.md`).
> Phases 9–12 were planned during the 2026-04-01 session and cover: US7 (sidebar API menu group,
> FR-017), discovery endpoints in API root (FR-003/FR-004), mandatory base serializer classes
> (FR-006 expanded), and `verbose_name_plural` router basename.
>
> **This update** (2026-04-02) adds **Phases 13–15** covering Swagger/OpenAPI documentation
> quality improvements: meaningful endpoint descriptions, schema component naming cleanup,
> registry-driven model descriptions in API docs, and portal-developer customization of the
> overall API description.

## Summary

### Phases 9–12 (planned 2026-04-01)

Four additions harden and complete the API feature after initial implementation:

1. **BaseSampleSerializer / BaseMeasurementSerializer** (FR-006) — Concrete DRF `ModelSerializer`
   base classes that all Sample and Measurement subtype serializers must inherit from. **Not yet
   implemented.** `fairdm/api/viewsets.py` has been cleaned up (no outstanding `ImportError`);
   the `_validate_*` enforcement calls in `generate_viewset()` Tier 3 and the `base_class`
   wiring in the Tier 1/2 auto-generate path were removed during that cleanup. Phase 9 adds them
   back alongside the base class implementations, followed by full test coverage.
2. **Discovery endpoints in DRF browsable API root** (FR-003/FR-004) — `SampleDiscoveryView` and
   `MeasurementDiscoveryView` are currently mounted as standalone `APIView` URL patterns that
   bypass the DRF router and therefore do not appear in the browsable `/api/v1/` root listing.
   Fix by introducing `FairDMAPIRouter(DefaultRouter)` that overrides `get_api_root_dict()` to
   inject the discovery endpoint links.
3. **`verbose_name_plural` router basename** (assumption, clarified 2026-04-01) — Currently
   `_model_to_slug()` in `fairdm/api/viewsets.py` derives the URL slug from the Python class name
   (CamelCase → kebab-case). The assumption requires using `model._meta.verbose_name_plural`
   (lowercased and hyphenated). This changes generated URL names and prefixes.
4. **US7 sidebar API menu group** (FR-017) — Add an "API" `MenuGroup` to `fairdm/menus/menus.py`
   after the Measurements entry, with three child `MenuItem` entries: "Interactive Docs"
   (`view_name="api-docs"`, resolves to `/api/v1/docs/`), "Browse API" (`view_name="api-root"`,
   resolves to `/api/v1/`), and "How to use the API" (external URL from `FAIRDM_API_DOCS_URL`
   setting). Internal links use `view_name` for Django URL reversal — never hardcoded strings.

### Phases 13–15 (planned 2026-04-02) — Swagger/OpenAPI Documentation Quality

Three improvements address poor Swagger documentation quality identified during manual inspection
of the `/api/v1/docs/` Swagger UI:

1. **Meaningful endpoint descriptions** — Generated viewsets currently inherit the `BaseViewSet`
   docstring, which exposes internal implementation details (``lookup_field``, ``get_queryset()``,
   ``perform_create/update/destroy()`` methods) as the operation description in Swagger UI.
   Every endpoint in the Swagger docs shows "Base viewset for all FairDM API resource endpoints.
   Features: lookup_field = 'uuid'…" which is useless to API consumers. Fix by injecting
   registry-driven descriptions into generated viewsets via `@extend_schema` or docstring
   construction, sourced from `ModelConfiguration.metadata.description` or `ModelConfiguration.description`.
2. **Schema component naming cleanup** — Auto-generated serializer classes are named
   ``{ModelName}APISerializer`` (e.g., ``RockSampleAPISerializer``). drf-spectacular strips
   "Serializer" to derive schema component names, yielding ``RockSampleAPI``,
   ``PatchedRockSampleAPI``, ``ProjectAPI``, etc. The "API" postfix is redundant and confusing
   in Swagger. Fix by renaming auto-generated serializers to ``{ModelName}Serializer`` (dropping
   the "API" infix), producing clean schema names like ``RockSample``, ``PatchedRockSample``,
   ``Project``.
3. **Portal-developer API description customization** — The current `SPECTACULAR_SETTINGS.DESCRIPTION`
   is a static string ``"Auto-generated API for this FairDM research data portal."`` which is
   generic and unhelpful. Provide a richer default description that explains FairDM API capabilities,
   and allow portal developers to customize it via a Django setting (`FAIRDM_API_DESCRIPTION`)
   that flows into `SPECTACULAR_SETTINGS['DESCRIPTION']` at startup.

## Technical Context

**Language/Version**: Python 3.12, Django 5.x
**Primary Dependencies**: djangorestframework, drf-spectacular, django-flex-menus (`flex_menu`), djangorestframework-guardian
**Storage**: PostgreSQL (primary); SQLite (dev/tests)
**Testing**: pytest, pytest-django
**Target Platform**: Linux server (web-service)
**Project Type**: web-service
**Performance Goals**: No new latency requirements; all changes are startup-time or schema-generation-time
**Constraints**: Discovery URLs already stable (`/api/v1/samples/`, `/api/v1/measurements/`); breaking URL changes to registered sample/measurement endpoints must be acknowledged in quickstart. Schema component name changes (removing "API" postfix) are a breaking change for any clients code-generating from the OpenAPI spec.
**Scale/Scope**: Phases 9–12: 4 files in `fairdm/api/`, 1 in `fairdm/menus/`. Phases 13–15: 3 files in `fairdm/api/` (`serializers.py`, `viewsets.py`, `settings.py`), no new files, tests and docs.

### Key Technical Facts (Phases 13–15)

- **drf-spectacular schema naming**: Component names are derived from the Python class name of the serializer by stripping the "Serializer" suffix. `RockSampleAPISerializer` → schema name `RockSampleAPI`. `RockSampleSerializer` → schema name `RockSample`. The `COMPONENT_SPLIT_PATCH` setting (currently `True`) generates separate `Patched*` variants for PATCH endpoints.
- **Viewset docstring → Swagger description**: drf-spectacular extracts the viewset class docstring as the operation description for all endpoints on that viewset. Generated viewsets inherit from `BaseViewSet` and currently have no docstring of their own, so they inherit `BaseViewSet.__doc__` which contains internal implementation notes.
- **`@extend_schema` alternative**: drf-spectacular supports `@extend_schema(description=...)` on individual viewset actions, but for generated viewsets the cleanest approach is to set the class docstring at generation time in `generate_viewset()`.
- **`ModelConfiguration.description`**: Already exists as a top-level attribute on `ModelConfiguration`. Also available via `metadata.description` on the `ModelMetadata` dataclass. Both are populated in the demo app's `config.py` for some models (e.g., `CustomParentSampleConfig`).
- **`SPECTACULAR_SETTINGS` merging**: Settings are defined in `fairdm/api/settings.py` and merged into Django settings. drf-spectacular picks up `SPECTACULAR_SETTINGS['DESCRIPTION']` at schema generation time, not at import time, so dynamic values (e.g., from a Django setting) work naturally.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. FAIR-First** | ✅ PASS | Discovery endpoints in API root improve findability (FR-003/FR-004). Consistent base serializer fields guarantee interoperability for consumers. |
| **II. Domain-Driven Modeling** | ✅ PASS | `BaseSampleSerializer`/`BaseMeasurementSerializer` enforce canonical field sets on domain entities. No schema changes. Registry-driven descriptions make domain knowledge surface in API docs (Phases 13–15). |
| **III. Configuration Over Plumbing** | ✅ PASS | `FAIRDM_API_DOCS_URL` setting for the docs link avoids hard-coded URLs. `FAIRDM_API_DESCRIPTION` setting (Phase 15) lets portal developers customize the API description without touching code. Router customisation is implementation-only, not exposed to portal developers. |
| **IV. Opinionated Defaults** | ✅ PASS | `verbose_name_plural` basenames are more human-readable defaults. The sidebar menu group provides discoverability out of the box. Rich default API description and per-model descriptions (Phases 13–15) provide meaningful defaults. Clean schema naming (no "API" postfix) is more intuitive. |
| **V. Test-First Quality** | ✅ PASS | Retroactively remediated in Phase 9 (T053–T055): comprehensive tests cover base class field correctness and `ImproperlyConfigured` enforcement. Phases 13–15 follow test-first discipline (T073→T074, T078→T079, T084→T085). |
| **VI. Documentation Critical** | ✅ PASS | quickstart.md and developer-guide section to be updated with new base class usage requirements, sidebar menu configuration, API description customization, and schema naming migration notes. |

**Gate decision**: No violations block progress. All principles pass, including Principle V which was retroactively remediated in Phase 9 (T053–T055).

## Project Structure

### Documentation (this feature)

```text
specs/011-restful-api/
├── plan.md              # This file (new additions plan)
├── research.md          # Phase 0 output (original + new additions appendix)
├── data-model.md        # Phase 1 output (original; updated with FairDMAPIRouter)
├── quickstart.md        # Phase 1 output (original; updated with base serializer usage)
├── contracts/           # Original contracts; no new contracts required
└── tasks.md             # Phases 1–8 complete; Phases 9–15 appended by this plan
```

### Source Code (files in scope)

#### Phases 9–12 (existing)

```text
fairdm/
├── api/
│   ├── router.py            # ADD FairDMAPIRouter; replace DefaultRouter usage
│   ├── viewsets.py          # CHANGE _model_to_slug() to use verbose_name_plural
│   ├── serializers.py       # ALREADY updated (BaseSampleSerializer, BaseMeasurementSerializer)
│   └── urls.py              # UPDATE to use FairDMAPIRouter (no URL pattern changes)
└── menus/
    └── menus.py             # ADD "API" MenuGroup after Measurements entry

tests/
└── test_api/
    ├── test_serializers.py  # ADD base class inheritance + ImproperlyConfigured tests
    ├── test_router.py       # ADD api-root-contains-discovery tests
    └── test_menu.py         # NEW: sidebar API menu group tests

fairdm/conf/settings/
└── api.py (or settings.py) # ADD FAIRDM_API_DOCS_URL default setting

docs/
└── portal-development/
    └── restful-api.md      # UPDATE: add BaseSampleSerializer/BaseMeasurementSerializer usage
```

#### Phases 13–15 (new — Swagger/OpenAPI doc quality)

```text
fairdm/
├── api/
│   ├── serializers.py       # CHANGE: rename auto-generated serializer classes
│   │                        #   {ModelName}APISerializer → {ModelName}Serializer
│   ├── viewsets.py          # CHANGE: inject model description as docstring on
│   │                        #   generated viewsets; improve core viewset docstrings
│   └── settings.py          # CHANGE: add FAIRDM_API_DESCRIPTION setting;
│                            #   update SPECTACULAR_SETTINGS to use richer default description
│                            #   and wire TITLE from FAIRDM_API_TITLE
└── conf/
    └── settings/
        └── api.py           # CHANGE: ensure FAIRDM_API_DESCRIPTION is re-exported

tests/
└── test_api/
    ├── test_swagger.py      # NEW: verify Swagger schema component names, endpoint
    │                        #   descriptions, and portal-customizable API description
    └── test_serializers.py  # UPDATE: adjust assertions for renamed serializer classes

fairdm_demo/
└── config.py               # UPDATE: ensure all registered models have meaningful
                            #   metadata.description values for demonstration

docs/
└── portal-development/
    └── restful-api.md      # UPDATE: add section on customizing API description
                            #   and documenting schema naming conventions
```

**Structure Decision**: All changes are narrow additions to existing files. No new packages or app directories. The `fairdm/api/` module stays flat.

## Phase 0: Research Summary

All unknowns were resolved during analysis of the existing codebase and DRF internals. Findings are appended to [research.md](research.md) as **R12–R14**.

---

### R12: Exposing Discovery Endpoints in the DRF Browsable API Root

**Decision**: Introduce `FairDMAPIRouter(DefaultRouter)` in `fairdm/api/router.py` that overrides
`get_api_root_dict()` to inject discovery endpoint URL names alongside the router-registered viewset
URLs.

**Rationale**: `DefaultRouter` builds the root listing exclusively from `self.registry` (the list
of `(prefix, viewset, basename)` tuples maintained by `register()` calls). Non-router URL patterns
— even when mounted under the same prefix — are invisible to the root view. The cleanest fix is a
minimal `DefaultRouter` subclass; it requires no view architecture changes and adds ~8 lines.

**Implementation**:

```python
from collections import OrderedDict
from rest_framework.routers import DefaultRouter

class FairDMAPIRouter(DefaultRouter):
    """DefaultRouter subclass that includes discovery endpoint links in the API root."""

    def get_api_root_dict(self):
        ret = super().get_api_root_dict()
        # Inject discovery endpoint URL names so they appear in the browsable API root.
        ret["sample-types"] = "api-sample-discovery"
        ret["measurement-types"] = "api-measurement-discovery"
        return ret
```

`fairdm_api_router = FairDMAPIRouter()` replaces the existing `DefaultRouter()` instantiation.
No changes to URL patterns, view code, or URL names are needed.

**Alternatives considered**:

- Convert discovery views to `ViewSet` with `list()` action — requires refactoring `_BaseDiscoveryView` and changing how the router registers them; more invasive.
- Override `APIRootView.get()` directly — fragile; couples to DRF internals more deeply.
- Manual link injection in a custom `APIRoot` template — frontend-only; API clients never see it.

---

### R13: `verbose_name_plural` Basename Strategy

**Decision**: Update `_model_to_slug()` in `fairdm/api/viewsets.py` to use
`model._meta.verbose_name_plural.lower().replace(" ", "-")` instead of CamelCase decomposition
of the Python class name.

**Rationale**: The clarification session explicitly chose this approach for human-readable,
stable URL patterns. `verbose_name_plural` is the Django-idiomatic string for plural
model representation. Portal developers control it via `class Meta: verbose_name_plural = "..."`.

**URL change impact**: This changes the generated URL prefix and basename for existing demo app
models. For example, `RockSample` (with default `verbose_name_plural = "rock samples"`) currently
generates slug `rock-sample` (from class name); it will generate `rock-samples` (from plural).
Existing test assertions using specific URL names must be updated. The quickstart.md migration
note documents this change.

**Implementation**:

```python
def _model_to_slug(model) -> str:
    return model._meta.verbose_name_plural.lower().replace(" ", "-")
```

**Alternatives considered**:

- Keep class-name strategy — contradicts the spec assumption.
- Use `verbose_name` (singular) — inconsistent with DRF convention of plural URL prefixes.

---

### R14: flex_menu API for Sidebar Menu Group

**Decision**: Use `MenuGroup(name, children=[...])` from `mvp.menus` (already imported in
`fairdm/menus/menus.py`) with three `MenuItem` children. Internal links use `view_name` for
Django URL reversal. The external docs link uses `url=` with the `FAIRDM_API_DOCS_URL` setting.

**Rationale**: `MenuGroup` is already used for "Community" and "Documentation" groups in
`fairdm/menus/menus.py`. Consistent pattern. `MenuItem` supports both `view_name` (resolved at
render time via `django.urls.reverse`) and `url` (static string or callable). Internal API routes
have stable named URL patterns (`api-docs` → `/api/v1/docs/`, `api-root` → `/api/v1/`) registered
in `fairdm/api/urls.py`. Using `view_name` means the resolved path automatically tracks URL
prefix changes. The "How to use the API" link is external so must use `url=`.

Correction from earlier implementation: `url="/api/docs/"` was incorrect — the Swagger UI is
mounted at `/api/v1/docs/` (URL name `api-docs`). All internal links must use `view_name`.

**Implementation sketch** (see data-model.md for final code):

```python
from django.conf import settings as django_settings

MenuGroup(
    name=_("API"),
    children=[
        MenuItem(name=_("Interactive Docs"), view_name="api-docs", extra_context={"icon": "api"}),
        MenuItem(name=_("Browse API"), view_name="api-root", extra_context={"icon": "api"}),
        MenuItem(
            name=_("How to use the API"),
            url=getattr(django_settings, "FAIRDM_API_DOCS_URL", "https://fairdm.org/api/"),
            extra_context={"icon": "literature"},
        ),
    ],
)
```

The group is inserted after the `MenuCollapse` for Measurements in `AppMenu.extend(...)`.

## Phase 1: Design & Contracts

### Data Model Updates

No new Django models. The changes are confined to the API layer and navigation configuration.

#### FairDMAPIRouter

New class in `fairdm/api/router.py`. Inherits `DefaultRouter`. Single override: `get_api_root_dict()` adds `"sample-types"` and `"measurement-types"` entries pointing to their named URL patterns. The public `fairdm_api_router` symbol changes from `DefaultRouter()` to `FairDMAPIRouter()`.

**Impact on existing code**: `fairdm/api/urls.py` imports `fairdm_api_router` — no change needed there. Tests in `test_router.py` that assert on the router type will need updating if they do `isinstance(fairdm_api_router, DefaultRouter)` (unlikely; the new class still passes that check).

#### Updated `_model_to_slug()`

```python
def _model_to_slug(model) -> str:
    """Derive URL-safe kebab slug from verbose_name_plural.

    Example: model with verbose_name_plural="rock samples" → "rock-samples"
    """
    return model._meta.verbose_name_plural.lower().replace(" ", "-")
```

**Impact**: All router `register()` calls that use `_model_to_slug()` will produce different slugs if any model's `verbose_name_plural` differs from what CamelCase decomposition would have produced. In practice:

- `RockSample` (class name) → old slug `rock-sample`, new slug `rock-samples` (assuming `verbose_name_plural = "rock samples"`)
- Any test asserting on `rock-sample-list`, `rock-sample-detail` must be updated to `rock-samples-list`, `rock-samples-detail`.

#### FAIRDM_API_DOCS_URL Setting

New optional Django setting added to `fairdm/conf/settings/api.py`. Default: `"https://fairdm.org/api/"`.

```python
# fairdm/conf/settings/api.py (additions)
FAIRDM_API_DOCS_URL = "https://fairdm.org/api/"
```

Portal developers can override in their settings file.

#### BaseSampleSerializer / BaseMeasurementSerializer

Already present in `fairdm/api/serializers.py`. No further code changes needed.

**Fields guaranteed by `BaseSampleSerializer`**:
`uuid`, `url`, `name`, `local_id`, `status`, `dataset`, `added`, `modified`, `polymorphic_ctype`

**Fields guaranteed by `BaseMeasurementSerializer`**:
`uuid`, `url`, `name`, `sample`, `dataset`, `added`, `modified`, `polymorphic_ctype`

### Contracts

No new external API contracts (no new URL patterns, no new response shapes beyond what FR-003/FR-004 already specify). The `api-root` response format changes to include two new keys: `sample-types` and `measurement-types`.

**Updated `GET /api/v1/` response** (addition to existing `contracts/api.md`):

```json
{
  "projects": "http://localhost/api/v1/projects/",
  "datasets": "http://localhost/api/v1/datasets/",
  "contributors": "http://localhost/api/v1/contributors/",
  "sample-types": "http://localhost/api/v1/samples/",
  "measurement-types": "http://localhost/api/v1/measurements/",
  "<sample-slug>": "http://localhost/api/v1/samples/<slug>/",
  "<measurement-slug>": "http://localhost/api/v1/measurements/<slug>/"
}
```

### Quickstart Updates

`specs/011-restful-api/quickstart.md` needs two additions:

1. **Custom serializer usage** — add a section showing how to subclass `BaseSampleSerializer` or `BaseMeasurementSerializer` when providing a custom `serializer_class`. Show the `ImproperlyConfigured` error message to set expectations.
2. **URL change migration note** — clarify that router basenames now derive from `verbose_name_plural`. Provide a before/after table for the demo app models.

## New Tasks (append to tasks.md as Phase 9–12)

The following tasks are appended to `tasks.md`. They depend on the existing Phases 1–8 being complete (all checkboxes ticked in the existing tasks.md).

---

### Phase 9: Base Serializer Classes (FR-006 Expanded)

**Goal**: Ensure `BaseSampleSerializer` and `BaseMeasurementSerializer` have comprehensive test
coverage confirming: correct fields, inheritance enforcement for auto-generated serializers, and
`ImproperlyConfigured` raised for non-conforming custom `serializer_class` registrations.

- [ ] T053 [P] [US6] Write base serializer tests in `tests/test_api/test_serializers.py`: `BaseSampleSerializer.Meta.fields` contains all required fields (`uuid`, `url`, `name`, `local_id`, `status`, `dataset`, `added`, `modified`, `polymorphic_ctype`); `BaseMeasurementSerializer.Meta.fields` contains all required fields; auto-generated serializer for a registered Sample subtype is an instance of `BaseSampleSerializer`; auto-generated serializer for a registered Measurement subtype is an instance of `BaseMeasurementSerializer`
- [ ] T054 [P] [US6] Write `ImproperlyConfigured` enforcement tests in `tests/test_api/test_serializers.py`: registering a Sample type with a custom `serializer_class` that does NOT inherit `BaseSampleSerializer` raises `ImproperlyConfigured` at `generate_viewset()` call time; same test for Measurement type with non-conforming serializer; registering with a correctly subclassed custom serializer succeeds without error
- [ ] T055 ⚠️ CRITICAL: Run base serializer tests: `poetry run pytest tests/test_api/test_serializers.py -v` — ALL tests MUST pass before Phase 10

---

### Phase 10: Discovery Endpoints in API Root (FR-003/FR-004)

**Goal**: Discovery endpoints (`/api/v1/samples/` and `/api/v1/measurements/`) appear as named
links in the DRF browsable API root (`GET /api/v1/`).

- [ ] T056 [US1] Introduce `FairDMAPIRouter(DefaultRouter)` in `fairdm/api/router.py`: class overrides `get_api_root_dict()` to inject `"sample-types": "api-sample-discovery"` and `"measurement-types": "api-measurement-discovery"`; replace the existing `DefaultRouter()` instantiation with `FairDMAPIRouter()`
- [ ] T057 [US1] Update `tests/test_api/test_router.py`: add assertions that `GET /api/v1/` response JSON contains `"sample-types"` and `"measurement-types"` keys with correct URLs; remove any `isinstance(..., DefaultRouter)` assertions that would fail after the router class change (none expected, but verify)
- [ ] T058 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check --settings=tests.settings` — MUST pass
- [ ] T059 ⚠️ CRITICAL: Run router + discovery tests: `poetry run pytest tests/test_api/test_router.py -v` — ALL tests MUST pass

---

### Phase 11: verbose_name_plural Basename (Clarification Assumption)

**Goal**: Router basenames and URL prefixes for auto-registered Sample and Measurement viewsets
derive from `model._meta.verbose_name_plural`, not the Python class name.

- [ ] T060 [US1] Update `_model_to_slug()` in `fairdm/api/viewsets.py`: replace CamelCase decomposition with `model._meta.verbose_name_plural.lower().replace(" ", "-")`; add a docstring explaining the strategy, the URL stability implication, and that portals can control the slug via `class Meta: verbose_name_plural`
- [ ] T061 [P] [US1] Update test assertions in `tests/test_api/test_router.py` and `tests/test_api/test_viewsets.py` that reference URL names derived from the class-name strategy (e.g., `rock-sample-list` → `rock-samples-list`); confirm demo app `fairdm_demo` models have `verbose_name_plural` set appropriately to produce expected slugs
- [ ] T062 Update `specs/011-restful-api/quickstart.md`: add a migration note section titled "URL name changes (verbose_name_plural)" documenting the before/after slug for each demo app model; add a usage example showing `class Meta: verbose_name_plural = "..."` to control the generated URL prefix
- [ ] T063 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check --settings=tests.settings`
- [ ] T064 ⚠️ CRITICAL: Run full router/viewset tests: `poetry run pytest tests/test_api/test_router.py tests/test_api/test_viewsets.py -v` — ALL tests MUST pass

---

### Phase 12: US7 — Sidebar API Menu Group (FR-017)

**Goal**: "API" `MenuGroup` added to `fairdm/menus/menus.py` after the Measurements entry with
3 child links. Docs URL configurable via `FAIRDM_API_DOCS_URL` setting.

- [ ] T065 Add `FAIRDM_API_DOCS_URL` setting to `fairdm/conf/settings/api.py` with default `"https://fairdm.org/api/"`; ensure it is included in `fairdm/conf/setup.py` when API settings are merged
- [ ] T066 [US7] Add "API" `MenuGroup` to `fairdm/menus/menus.py` after the Measurements `MenuCollapse`: three child `MenuItem` entries — (1) `name=_("Interactive Docs"), view_name="api-docs", extra_context={"icon": "api"}`, (2) `name=_("Browse API"), view_name="api-root", extra_context={"icon": "api"}`, (3) `name=_("How to use the API"), url=getattr(django_settings, "FAIRDM_API_DOCS_URL", "https://fairdm.org/api/"), extra_context={"icon": "literature"}`; internal links use `view_name` — never hardcoded URL strings
- [ ] T067 [P] [US7] Create `tests/test_api/test_menu.py`: verify the `AppMenu` contains a group named "API"; verify the group has exactly 3 children; verify the first child has `view_name="api-docs"` and empty `_url`; verify the second child has `view_name="api-root"` and empty `_url`; verify the third child has `_url` equal to `FAIRDM_API_DOCS_URL` default and empty `view_name`; verify `FAIRDM_API_DOCS_URL` override is respected when set in settings
- [ ] T068 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check --settings=tests.settings`
- [ ] T069 ⚠️ CRITICAL: Run menu tests: `poetry run pytest tests/test_api/test_menu.py -v` — ALL tests MUST pass

---

### Final Phase (Phases 9–12 Additions): Verification & Documentation

- [ ] T070 [P] Update `docs/portal-development/restful-api.md`: add section "Providing a Custom Serializer" showing subclass of `BaseSampleSerializer` / `BaseMeasurementSerializer`; add note on `ImproperlyConfigured` enforcement; update URL name format to reflect `verbose_name_plural` strategy; add section "API Navigation" describing the sidebar menu group and `FAIRDM_API_DOCS_URL` setting
- [ ] T071 ⚠️ CRITICAL: Run full API test suite: `poetry run pytest tests/test_api/ -v` — ALL tests MUST pass
- [ ] T072 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check --settings=tests.settings`

---
---

## Phase 0 Research (Phases 13–15): Swagger/OpenAPI Documentation Quality

Findings appended to [research.md](research.md) as **R15–R17**.

### R15: Schema Component Naming — Removing the "API" Postfix

**Decision**: Rename auto-generated serializer classes from `{ModelName}APISerializer` to
`{ModelName}Serializer` in `build_model_serializer()`.

**Rationale**: drf-spectacular derives OpenAPI schema component names by stripping the "Serializer"
suffix from the serializer class name. The current naming convention `{Model}APISerializer` →
schema name `{Model}API` (e.g., `RockSampleAPI`, `PatchedRockSampleAPI`, `ProjectAPI`). The "API"
postfix is redundant within an API schema and confusing to API consumers reviewing Swagger docs.

Renaming to `{Model}Serializer` → schema name `{Model}` (e.g., `RockSample`, `PatchedRockSample`,
`Project`). This is the standard DRF convention and produces the cleanest schema.

**Impact**: This is a **breaking change** for clients that code-generate from the OpenAPI schema
(TypeScript types, Python clients via `openapi-generator`, etc.). Schema component names change
from `RockSampleAPI` to `RockSample`. The `COMPONENT_SPLIT_PATCH` setting (currently `True`)
means `Patched*` variants also change (e.g., `PatchedRockSampleAPI` → `PatchedRockSample`).

**Implementation**:

```python
# In build_model_serializer():
serializer_cls = type(
    f"{model.__name__}Serializer",  # was: f"{model.__name__}APISerializer"
    bases,
    serializer_attrs,
)
```

**Alternatives considered**:

- Use `SPECTACULAR_SETTINGS['POSTPROCESSING_HOOKS']` to strip "API" from component names after
  generation — fragile, non-obvious, and doesn't fix the Python class name mismatch.
- Use `@extend_schema(component_name=...)` per-viewset — too verbose for auto-generated viewsets;
  requires changes in `generate_viewset()` anyway.
- Keep "API" postfix — contradicts user feedback; confusing in Swagger UI.

---

### R16: Endpoint Descriptions — Injecting Model Descriptions into Generated Viewsets

**Decision**: Set the `__doc__` attribute on generated viewset classes in `generate_viewset()` using
the model's description from the registry configuration.

**Rationale**: drf-spectacular uses the viewset's `__doc__` (class docstring) as the operation
description for all endpoints on that viewset. Currently, all generated viewsets inherit
`BaseViewSet.__doc__` which contains internal implementation details:

> "Base viewset for all FairDM API resource endpoints. Features: lookup_field = 'uuid' …
> get_queryset() … get_serializer_class() … perform_create/update/destroy() …"

This is useless to API consumers and actively harmful — it exposes framework internals.

The fix has two parts:

1. **Generated viewsets** (`generate_viewset()`): Construct a meaningful docstring from
   `config.description` or `config.metadata.description`, falling back to the model's
   `verbose_name_plural`. The docstring should describe what the resource IS, not how the
   viewset is implemented.

2. **Core viewsets** (`ProjectViewSet`, `DatasetViewSet`, `ContributorViewSet`): Replace the
   current implementation-detail docstrings with consumer-facing descriptions that describe
   the resource and available operations.

**Description resolution order**:

1. `config.description` (top-level, if non-empty)
2. `config.metadata.description` (from `ModelMetadata`, if non-empty)
3. Model class docstring (`model.__doc__`, if non-empty)
4. Auto-generated fallback: `"Endpoints for managing {model._meta.verbose_name_plural}."`

**Implementation sketch** (in `generate_viewset()`):

```python
# After creating _GeneratedViewSet class:
description = (
    config.description
    or (config.metadata.description if config.metadata else "")
    or (model.__doc__ or "").strip()
    or f"Endpoints for managing {model._meta.verbose_name_plural}."
)
_GeneratedViewSet.__doc__ = description
```

For core viewsets, replace the docstrings with API-consumer-facing text:

```python
class ProjectViewSet(BaseViewSet):
    """Research projects registered in the portal.

    Projects are the top-level organizational unit. Each project contains
    one or more datasets, which in turn contain samples and measurements.
    """
    ...
```

**Alternatives considered**:

- Use `@extend_schema(description=...)` on each generated action — requires decorating
  every CRUD action (`list`, `create`, `retrieve`, `update`, `partial_update`, `destroy`);
  much more code for the same result.
- Set `SPECTACULAR_SETTINGS['GET_LIB_DOC_EXCLUDES']` to exclude `BaseViewSet` — only prevents
  the fallback, doesn't provide a good replacement description.
- Override `AutoSchema.get_description()` globally — too heavy; affects third-party viewsets too.

---

### R17: Portal-Developer API Description Customization

**Decision**: Add a `FAIRDM_API_DESCRIPTION` Django setting that flows into
`SPECTACULAR_SETTINGS['DESCRIPTION']`. Provide a rich default that describes the FairDM API.
Also add `FAIRDM_API_TITLE` for the API title.

**Rationale**: The current description is a single sentence: "Auto-generated API for this
FairDM research data portal." This tells an API consumer nothing about what data the API
exposes, how to authenticate, or what they can do. Portal developers need a way to add their
own portal-specific context (e.g., what data domain, what institution, data policies).

The mechanism is simple: define two Django settings (`FAIRDM_API_TITLE`, `FAIRDM_API_DESCRIPTION`)
with FairDM defaults. Reference them in `SPECTACULAR_SETTINGS` using `getattr(settings, ...)` at
settings-merge time. Portal developers override in their own settings to customize.

The default description should be a Markdown-formatted string (drf-spectacular supports Markdown
in descriptions) that covers:

- What FairDM is
- What resources the API exposes (projects, datasets, samples, measurements, contributors)
- How to authenticate (Token auth header, or session auth via browser)
- Rate limiting policy
- Link to full documentation

**Implementation** (in `fairdm/api/settings.py`):

```python
FAIRDM_API_TITLE = "FairDM Portal API"

FAIRDM_API_DESCRIPTION = """
This API provides programmatic access to research data managed by this
[FairDM](https://fairdm.org) portal.

## Available Resources

- **Projects** — Top-level research projects
- **Datasets** — Collections of samples and measurements within a project
- **Samples** — Physical or virtual specimens (domain-specific types registered by the portal)
- **Measurements** — Analytical results tied to samples (domain-specific types registered by the portal)
- **Contributors** — People and organizations associated with projects and datasets

## Authentication

- **Browser**: Session authentication (log in via the portal web interface)
- **Programmatic**: Token authentication — include `Authorization: Token <your-token>` header

## Rate Limits

- Anonymous: {anon_rate} requests per hour
- Authenticated: {user_rate} requests per hour
""".strip()

SPECTACULAR_SETTINGS = {
    "TITLE": FAIRDM_API_TITLE,
    "DESCRIPTION": FAIRDM_API_DESCRIPTION,
    ...
}
```

Portal developers override like:

```python
# In portal settings.py
FAIRDM_API_TITLE = "GeoRock Data Portal API"
FAIRDM_API_DESCRIPTION = "API for the GeoRock geological data portal..."
```

**Alternatives considered**:

- Inject via `SPECTACULAR_SETTINGS['POSTPROCESSING_HOOKS']` — overkill; the description is a
  static string that should be settable directly.
- Use a template file for the description — too complex; a string setting is sufficient and
  consistent with other `FAIRDM_*` settings.
- Don't provide a default at all — violates Constitution Principle IV (Opinionated Defaults).

---

## Phase 1 Design (Phases 13–15): Swagger Documentation Quality

### Data Model Updates

No Django model changes. All changes are in the API serialization layer, viewset factory, and
settings.

#### Serializer Class Naming Change

In `fairdm/api/serializers.py`, `build_model_serializer()`:

```python
# BEFORE:
serializer_cls = type(
    f"{model.__name__}APISerializer",
    bases,
    serializer_attrs,
)

# AFTER:
serializer_cls = type(
    f"{model.__name__}Serializer",
    bases,
    serializer_attrs,
)
```

**Cache key**: The `_SERIALIZER_CACHE` uses `(model, fields, view_name, extra_kwargs, base_class)`
as the key — no change needed since the key doesn't include the class name.

**Impact on existing tests**: Any test that references `RockSampleAPISerializer` or similar class
names by string will need updating. The `test_serializers.py` test for schema component names will
validate the new naming.

#### Viewset Description Injection

In `fairdm/api/viewsets.py`, `generate_viewset()`, after creating the dynamic class:

```python
# Resolve description from registry config
description = (
    config.description
    or (config.metadata.description if config.metadata else "")
    or (model.__doc__ or "").strip()
    or f"Endpoints for managing {model._meta.verbose_name_plural}."
)
_GeneratedViewSet.__doc__ = description
```

For core viewsets, replace docstrings:

- `BaseViewSet`: Keep the docstring but make it internal-only by setting it to a brief
  developer-facing note. drf-spectacular's `GET_LIB_DOC_EXCLUDES` already excludes DRF base
  classes, but `BaseViewSet` is a project class so it needs a clean docstring OR the generated
  subclasses must override it.
- `ProjectViewSet`: "Research projects registered in the portal. Projects are the top-level
  organizational unit containing datasets, samples, and measurements."
- `DatasetViewSet`: "Datasets within research projects. Each dataset contains samples and
  associated measurements."
- `ContributorViewSet`: "People and organizations that contribute to research projects.
  Contributor profiles are read-only."

#### API Settings Changes

In `fairdm/api/settings.py`:

```python
# New settings
FAIRDM_API_TITLE = "FairDM Portal API"
FAIRDM_API_DESCRIPTION = """..."""  # (see R13 for full text)

SPECTACULAR_SETTINGS = {
    "TITLE": FAIRDM_API_TITLE,
    "DESCRIPTION": FAIRDM_API_DESCRIPTION,
    ...  # rest unchanged
}
```

Portal developers override `FAIRDM_API_TITLE` and/or `FAIRDM_API_DESCRIPTION` in their own settings.
Since FairDM merges settings files and SPECTACULAR_SETTINGS is a dict, the override mechanism is:

1. Portal sets `FAIRDM_API_TITLE = "MyPortal API"` in their settings
2. Portal sets `SPECTACULAR_SETTINGS["TITLE"] = FAIRDM_API_TITLE` (or FairDM's settings merge
   handles this via `fairdm/conf/setup.py`)

The simplest approach: in `fairdm/conf/setup.py` (or the settings initialization), after all
settings are loaded, update `SPECTACULAR_SETTINGS['TITLE']` and `['DESCRIPTION']` from
`FAIRDM_API_TITLE` / `FAIRDM_API_DESCRIPTION` if they were overridden. This ensures the last
value set wins.

### Contracts

**Schema component name changes** (breaking for code-generated clients):

| Before | After |
|--------|-------|
| `RockSampleAPI` | `RockSample` |
| `PatchedRockSampleAPI` | `PatchedRockSample` |
| `SoilSampleAPI` | `SoilSample` |
| `PatchedSoilSampleAPI` | `PatchedSoilSample` |
| `WaterSampleAPI` | `WaterSample` |
| `PatchedWaterSampleAPI` | `PatchedWaterSample` |
| `CustomParentSampleAPI` | `CustomParentSample` |
| `PatchedCustomParentSampleAPI` | `PatchedCustomParentSample` |
| `XRFMeasurementAPI` | `XRFMeasurement` |
| `PatchedXRFMeasurementAPI` | `PatchedXRFMeasurement` |
| `ProjectAPI` | `Project` |
| `PatchedProjectAPI` | `PatchedProject` |

**Endpoint descriptions**: No contract change (descriptions are informational, not structural).

**API title and description**: Informational only; no structural contract change.

---

## New Tasks (Phases 13–15) — append to tasks.md

The following tasks are appended after Phase 12. They depend on Phases 9–12 being complete.

---

### Phase 13: Schema Component Naming Cleanup

**Goal**: Remove the "API" postfix from auto-generated serializer class names so drf-spectacular
produces clean schema component names (e.g., `RockSample` instead of `RockSampleAPI`).

- [ ] T073 [P] [US2] Write schema naming tests in `tests/test_api/test_swagger.py`: fetch the OpenAPI schema from `/api/v1/schema/`; verify that component names for registered Sample/Measurement types do NOT contain "API" postfix (e.g., assert `"RockSample"` in components, NOT `"RockSampleAPI"`); verify `Patched*` variants follow the same pattern; verify core model schemas (`Project`, `Dataset`) also lack "API" postfix
- [ ] T074 [US2] In `fairdm/api/serializers.py`, change `build_model_serializer()` to name generated classes `{ModelName}Serializer` instead of `{ModelName}APISerializer`: change line `f"{model.__name__}APISerializer"` to `f"{model.__name__}Serializer"`
- [ ] T075 [P] [US2] Update any existing test assertions in `tests/test_api/test_serializers.py` that reference the old `*APISerializer` naming pattern; verify the serializer cache still works correctly with the new names
- [ ] T076 ⚠️ CRITICAL: Run schema naming tests: `poetry run pytest tests/test_api/test_swagger.py -v` — ALL tests MUST pass
- [ ] T077 ⚠️ CRITICAL: Run full API test suite: `poetry run pytest tests/test_api/ -v` — ALL tests MUST pass (to catch any regressions from the rename)

---

### Phase 14: Meaningful Endpoint Descriptions

**Goal**: Replace internal-implementation docstrings with consumer-facing API descriptions that
surface in Swagger UI. Generated viewsets pull descriptions from registry configuration;
core viewsets get hand-written descriptions.

- [ ] T078 [P] [US2] Write endpoint description tests in `tests/test_api/test_swagger.py`: fetch the OpenAPI schema; for each registered Sample/Measurement type, verify the GET list operation description contains text from `config.description` or `config.metadata.description` (NOT "Base viewset for all FairDM API resource endpoints"); verify core endpoints (`/api/v1/projects/`, `/api/v1/datasets/`, `/api/v1/contributors/`) have consumer-facing descriptions that don't mention `lookup_field`, `get_queryset`, or `perform_create`
- [ ] T079 [US2] In `fairdm/api/viewsets.py`, update `generate_viewset()` to set `__doc__` on the generated viewset class using the description resolution order: (1) `config.description`, (2) `config.metadata.description`, (3) `model.__doc__`, (4) fallback `"Endpoints for managing {verbose_name_plural}."`
- [ ] T080 [US2] In `fairdm/api/viewsets.py`, replace docstrings on `ProjectViewSet`, `DatasetViewSet`, and `ContributorViewSet` with consumer-facing descriptions. Keep `BaseViewSet.__doc__` as a brief developer note (e.g., "Internal base class — see generated subclasses for API documentation.")
- [ ] T081 [P] [US2] Update `fairdm_demo/config.py`: ensure ALL registered model configurations have a non-empty `description` or `metadata.description` value. For models currently without descriptions, add a meaningful 1–2 sentence description explaining what the data type represents.
- [ ] T082 ⚠️ CRITICAL: Run description tests: `poetry run pytest tests/test_api/test_swagger.py -v` — ALL tests MUST pass
- [ ] T083 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check --settings=tests.settings`

---

### Phase 15: Portal-Developer API Description Customization

**Goal**: Provide a rich default API description and title, and allow portal developers to
customize both via Django settings (`FAIRDM_API_TITLE`, `FAIRDM_API_DESCRIPTION`).

- [ ] T084 [P] [US2] Write API description customization tests in `tests/test_api/test_swagger.py`: verify the default `SPECTACULAR_SETTINGS['DESCRIPTION']` contains key phrases about FairDM, authentication, and rate limits; verify `SPECTACULAR_SETTINGS['TITLE']` defaults to "FairDM Portal API"; verify that overriding `FAIRDM_API_TITLE` / `FAIRDM_API_DESCRIPTION` in settings changes the Swagger output accordingly
- [ ] T085 [US2] In `fairdm/api/settings.py`: add `FAIRDM_API_TITLE` and `FAIRDM_API_DESCRIPTION` settings with rich defaults (see R17 for content); update `SPECTACULAR_SETTINGS['TITLE']` and `['DESCRIPTION']` to reference these settings
- [ ] T086 [US2] In `fairdm/conf/setup.py`: ensure that portal-level overrides of `FAIRDM_API_TITLE` / `FAIRDM_API_DESCRIPTION` are reflected in `SPECTACULAR_SETTINGS` after all settings are merged
- [ ] T087 ⚠️ CRITICAL: Run customization tests: `poetry run pytest tests/test_api/test_swagger.py -v` — ALL tests MUST pass

---

### Final Phase (Phases 13–15): Verification, Documentation & Visual Inspection

- [ ] T088 [P] Update `docs/portal-development/restful-api.md`: add section "Customizing the API Description" documenting `FAIRDM_API_TITLE` and `FAIRDM_API_DESCRIPTION` settings with examples; add section "Schema Naming Conventions" explaining that schema names match model class names without postfix; add migration note for clients code-generating from the OpenAPI schema (schema name changes)
- [ ] T089 [P] Update `specs/011-restful-api/quickstart.md`: add section "Swagger Documentation" explaining schema naming, endpoint descriptions from registry, and API description customization
- [ ] T090 [P] Update `fairdm_demo/config.py` docstrings: ensure each registered config class has a docstring linking to the "Developer Guide > RESTful API > Model Descriptions" documentation section, demonstrating the description-flow pattern for the demo app
- [ ] T091 ⚠️ CRITICAL: Run full API test suite: `poetry run pytest tests/test_api/ -v` — ALL tests MUST pass
- [ ] T092 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check --settings=tests.settings` — MUST pass
- [ ] T093 Visually verify Swagger UI at `/api/v1/docs/` using browser: confirm (1) schema component names have no "API" postfix, (2) endpoint descriptions show model descriptions not BaseViewSet internals, (3) API title and description are rich and informative

## Complexity Tracking

No constitution violations. No complexity justification required.
