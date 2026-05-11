# Research: FairDM Base Views — Documentation & Testing

**Phase 0 output for spec 012-base-views-docs**

No NEEDS CLARIFICATION items were identified in the spec. All technology choices
are pre-determined by the existing codebase. This file records findings from
codebase exploration that inform the design decisions in plan.md.

---

## Decision 1: Docstring style

**Decision**: Mirror django-mvp's docstring conventions — `Config:`, `Override hooks:`, `Context:`, `Example::` sections.

**Rationale**: FairDM views are direct subclasses of django-mvp views. Using identical conventions means developers who already know django-mvp can read FairDM docstrings immediately. The parent classes in `django-mvp/mvp/views/` (e.g., `MVPListViewMixin`, `MVPUpdateView`) already use this style extensively and serve as direct templates to copy from.

**Alternatives considered**: Google-style (`Args:`, `Returns:`, `Raises:`) — rejected; inconsistent with the parent library. Minimal prose-only — rejected; insufficient for developer self-service navigation.

---

## Decision 2: Test approach

**Decision**: Integration tests using Django's `RequestFactory` (via `pytest-django`'s `rf` fixture) or `client` fixture; one test class per view class.

**Rationale**: The FairDM view classes are thin wrappers — the main risk is MRO/mixin composition breaking silently. Request-level tests catch that class of regression far better than unit tests that mock the parents. The existing `tests/test_core/test_project/test_views.py` already establishes this pattern and serves as the reference implementation.

**Alternatives considered**: Unit tests only — rejected; mocking all of django-mvp's mixin chain would be fragile and wouldn't catch composition errors. Both unit + integration — rejected as over-engineered for this scope.

---

## Decision 3: Test file location

**Decision**: `tests/test_views/test_base.py` — mirroring `fairdm/views/base.py` per the constitution.

**Rationale**: Constitution §Architecture & Stack Constraints specifies: "Test organization MUST mirror the `fairdm/` source code structure." `fairdm/views/base.py` → `tests/test_views/test_base.py`. No `tests/test_views/` directory exists yet; it must be created with an `__init__.py`.

**Alternatives considered**: Adding tests to an existing test file — rejected; no related test file exists. Using `fairdm_demo` tests — rejected; the demo is for demonstration, not framework unit/integration coverage.

---

## Decision 4: Views requiring test fixtures

Four of the seven views require a model+URL setup. Codebase exploration shows:

- `FairDMListView` and `FairDMDetailView` require a `model` and a URL route.
- `FairDMCreateView` and `FairDMUpdateView` require a model, URL route, and `fields`.
- `FairDMDeleteView` requires a model, URL route, and an existing object.
- `FairDMTemplateView` requires only a `template_name`.
- `FairDMTableView` requires a model, `table_class`, and URL route.

**Strategy**: Define minimal in-test concrete subclasses using `fairdm_demo` models (e.g., `Project`, `Dataset`) and register URL patterns in-test using `override_settings` + `urlconf` parameter on the test client. Existing `ProjectFactory`, `DatasetFactory` from `fairdm.factories` can be used directly.

---

## Decision 5: Documentation page structure

**Decision**: Single file at `docs/contributing/base-views.md`, added to the existing `toctree` in `docs/contributing/index.md`.

**Rationale**: The contributing section already has 7 top-level pages; adding one more is consistent. The view surface (7 thin classes) does not warrant a subdirectory. The `index.md` toctree already contains `registry-system` and `core_data_model` as comparable standalone pages.

**Alternatives considered**: Subdirectory `docs/contributing/views/` — deferred; can be introduced later if the surface grows significantly.

---

## Findings: MetadataMixin

`django-meta`'s `MetadataMixin` injects a `meta` object into the template context via `get_context_data`. It reads from view-level attributes: `title`, `description`, `keywords`, `image`, `object_type`, `twitter_type`, `og_type`, `url`, `locale`, `use_og`, `use_twitter`, `use_schema_org`. All of these are optional; the mixin degrades gracefully when none are set.

**Test implication**: Testing for `"meta" in response.context` is a sufficient integration assertion. No need to set any of these attributes on the test views.

---

## Findings: Existing docstring gaps

| Class | Current state |
|---|---|
| `FairDMTemplateView` | No docstring |
| `FairDMListView` | Minimal one-liner |
| `FairDMDetailView` | No docstring |
| `FairDMCreateView` | Minimal one-liner |
| `FairDMUpdateView` | Incorrect one-liner ("creating" instead of "updating") |
| `FairDMDeleteView` | Minimal one-liner |
| `FairDMTableView` | One-liner, no Config/Example sections |
