# Implementation Plan: Auto-Generated RESTful API (New Additions)

**Branch**: `011-restful-api` | **Date**: 2026-04-01 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/011-restful-api/spec.md`

> **Scope note**: Phases 1–8 of this feature are already implemented (T001–T052 in `tasks.md`).
> This plan covers only the **new additions** introduced during the 2026-04-01 clarification
> session: US7 (sidebar API menu group, FR-017), discovery endpoints in API root (FR-003/FR-004),
> mandatory base serializer classes (FR-006 expanded), and `verbose_name_plural` router basename
> (clarification assumption). Tasks generated from this plan will be appended to `tasks.md` as
> a new **Phase 9** and beyond.

## Summary

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

## Technical Context

**Language/Version**: Python 3.12, Django 5.x
**Primary Dependencies**: djangorestframework, drf-spectacular, django-flex-menus (`flex_menu`), djangorestframework-guardian
**Storage**: PostgreSQL (primary); SQLite (dev/tests)
**Testing**: pytest, pytest-django
**Target Platform**: Linux server (web-service)
**Project Type**: web-service
**Performance Goals**: No new latency requirements; router customization is startup-time only
**Constraints**: Discovery URLs already stable (`/api/v1/samples/`, `/api/v1/measurements/`); breaking URL changes to registered sample/measurement endpoints must be acknowledged in quickstart
**Scale/Scope**: Narrow changes — 4 files touched in `fairdm/api/`, 1 in `fairdm/menus/`, tests and docs

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. FAIR-First** | ✅ PASS | Discovery endpoints in API root improve findability (FR-003/FR-004). Consistent base serializer fields guarantee interoperability for consumers. |
| **II. Domain-Driven Modeling** | ✅ PASS | `BaseSampleSerializer`/`BaseMeasurementSerializer` enforce canonical field sets on domain entities. No schema changes. |
| **III. Configuration Over Plumbing** | ✅ PASS | `FAIRDM_API_DOCS_URL` setting for the docs link avoids hard-coded URLs. Router customisation is implementation-only, not exposed to portal developers. |
| **IV. Opinionated Defaults** | ✅ PASS | `verbose_name_plural` basenames are more human-readable defaults. The sidebar menu group provides discoverability out of the box. |
| **V. Test-First Quality** | ⚠️ FLAG | `BaseSampleSerializer`/`BaseMeasurementSerializer` were implemented before tests were written (error during clarify session). The plan mandates tests covering base class inheritance, `ImproperlyConfigured` enforcement, and API root discovery listing before any further code changes. |
| **VI. Documentation Critical** | ✅ PASS | quickstart.md and developer-guide section to be updated with new base class usage requirements and sidebar menu configuration. |

**Gate decision**: No violations block progress. The Principle V flag is a known historical anomaly (pre-existing code in workspace); tests must be written in Phase 0 of this plan before any implementation changes land.

## Project Structure

### Documentation (this feature)

```text
specs/011-restful-api/
├── plan.md              # This file (new additions plan)
├── research.md          # Phase 0 output (original + new additions appendix)
├── data-model.md        # Phase 1 output (original; updated with FairDMAPIRouter)
├── quickstart.md        # Phase 1 output (original; updated with base serializer usage)
├── contracts/           # Original contracts; no new contracts required
└── tasks.md             # Phases 1–8 complete; new Phase 9–11 appended by this plan
```

### Source Code (files in scope)

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

**Structure Decision**: All changes are narrow additions to existing files. No new packages or app directories. The `fairdm/api/` module stays flat.

## Phase 0: Research Summary

All unknowns were resolved during analysis of the existing codebase and DRF internals. Findings are appended to [research.md](research.md) as **R8–R10**.

---

### R8: Exposing Discovery Endpoints in the DRF Browsable API Root

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

### R9: `verbose_name_plural` Basename Strategy

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

### R10: flex_menu API for Sidebar Menu Group

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

## New Tasks (append to tasks.md as Phase 9–11)

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

### Final Phase (New Additions): Verification & Documentation

- [ ] T070 [P] Update `docs/portal-development/restful-api.md`: add section "Providing a Custom Serializer" showing subclass of `BaseSampleSerializer` / `BaseMeasurementSerializer`; add note on `ImproperlyConfigured` enforcement; update URL name format to reflect `verbose_name_plural` strategy; add section "API Navigation" describing the sidebar menu group and `FAIRDM_API_DOCS_URL` setting
- [ ] T071 ⚠️ CRITICAL: Run full API test suite: `poetry run pytest tests/test_api/ -v` — ALL tests MUST pass
- [ ] T072 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check --settings=tests.settings`

## Complexity Tracking

No constitution violations. No complexity justification required.
