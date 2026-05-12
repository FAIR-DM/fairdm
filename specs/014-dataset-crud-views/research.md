# Research: Dataset CRUD Views

**Branch**: `014-dataset-crud-views` | **Date**: 2026-05-12

## Research Questions Addressed

This feature has no external unknowns — the entire implementation is a direct application of the already-proven Project CRUD pattern to the Dataset entity. All decisions below are resolved by inspection of the existing codebase.

---

## Decision 1: View inheritance hierarchy

**Decision**: `DatasetUpdateView` and `DatasetDeleteView` inherit from `LoginRequiredMixin` + `FairDMUpdateView` / `FairDMDeleteView` respectively, matching the Project pattern exactly.

**Rationale**: `FairDMUpdateView` and `FairDMDeleteView` extend MVP base classes with `MetadataMixin` (SEO metadata). `LoginRequiredMixin` is composed at the view class level (not baked into the base) — consistent with `ProjectUpdateView` and `ProjectDeleteView`.

**Alternatives considered**: Inheriting directly from Django's `UpdateView`/`DeleteView` — rejected per SC-004/FR-014/FR-019.

---

## Decision 2: Object-level permission check mechanism

**Decision**: Both new views use `get_object()` override with `get_object_or_404` + `request.user.has_perm(perm, obj)` + `raise PermissionDenied(...)` — identical to `ProjectUpdateView` and `ProjectDeleteView`.

**Rationale**: `django-guardian` is already installed and used. This is the established pattern in the codebase. No new permission infrastructure is needed.

**Alternatives considered**: `PermissionRequiredMixin` from guardian — adds config complexity without benefit for this case.

---

## Decision 3: DatasetCreateForm field set

**Decision**: `DatasetCreateForm(DatasetForm)` overrides `Meta` with `fields = ["name", "project", "license"]`. No other overrides.

**Rationale**: These three fields are sufficient for initial dataset creation. `project` is optional (`required=False` inherited from `DatasetForm`). `license` defaults to CC BY 4.0 via `DatasetForm.__init__`. No `visibility` field (managed separately). No widget overrides needed (project uses Select2 from parent; license uses Select2 from parent).

**Alternatives considered**: Adding `image` to create form — deferred; image upload is a secondary concern at creation time.

---

## Decision 4: Removing get_initial() from DatasetCreateView

**Decision**: Remove the existing `get_initial()` override that reads `?project=<id>` from query params.

**Rationale**: Explicitly decided in clarification session (Q4 — Option B). The behaviour is not wrong but is being deferred to avoid scope creep. The existing implementation used `project_id.isdigit()` for the ID, which would break anyway since Dataset now identifies projects by UUID, not integer PK.

**Alternatives considered**: Keeping it — rejected per clarification.

---

## Decision 5: request passing in update view

**Decision**: `DatasetUpdateView` overrides `get_form_kwargs()` to add `request=self.request`, matching `DatasetCreateView`.

**Rationale**: `DatasetForm.__init__` uses `request` to filter the `project` queryset to the user's accessible projects. Without it, the project dropdown shows all projects — a data-disclosure risk (project names visible to users who don't have access). Decided in clarification session (Q5 — Option A).

**Code pattern** (mirrors existing `DatasetCreateView`):

```python
def get_form_kwargs(self):
    kwargs = super().get_form_kwargs()
    kwargs["request"] = self.request
    return kwargs
```

---

## Decision 6: Deletion confirmation mechanism

**Decision**: `require_confirmation = True` (class attribute on `FairDMDeleteView`) + `get_confirmation_value()` returning `self.object.name`. No `form_valid()` override needed (no model-level deletion guard for Dataset at this stage).

**Rationale**: The Dataset model has no `PublicDatasetsProtect` equivalent (that guard exists only on `Project`). The `FairDMDeleteView` base class handles the `DeleteConfirmForm` flow automatically when `require_confirmation = True`. Confirmed in clarification session (Q — no deletion guard).

**Alternatives considered**: Adding a guard for datasets linked to published samples — deferred to a future spec.

---

## Decision 7: slug_field / slug_url_kwarg

**Decision**: Both new views use `slug_field = "uuid"` and `slug_url_kwarg = "uuid"`, consistent with `DatasetDetailView` and all Project views.

**Rationale**: The Dataset `uuid` field (ShortUUIDField with prefix "d") is the canonical URL identifier. Confirmed by existing `DatasetDetailView` and the URL pattern `dataset/<str:uuid>/`.

---

## Decision 8: success_url for delete view

**Decision**: `success_url = reverse_lazy("dataset-list")`.

**Rationale**: Explicitly decided in spec (FR-023a). Matches how `ProjectDeleteView` redirects to `project-list`.

---

## Decision 9: Test file location

**Decision**: Tests go in `tests/test_core/test_dataset/test_views.py` (new file).

**Rationale**: The constitution mandates test organisation mirrors source code structure. `fairdm/core/dataset/views.py` → `tests/test_core/test_dataset/test_views.py`. The directory already exists (confirmed: `test_form.py`, `test_models.py`, etc. are present there). No `test_views.py` exists yet.

---

## Resolved Unknowns Summary

| Unknown | Resolution |
|---------|-----------|
| Test file exists? | No — must be created at `tests/test_core/test_dataset/test_views.py` |
| Dataset model has `added` field? | Yes — inherited via tracking mixin (confirmed in DatasetListView `order_by`) |
| Project uses integer PK or UUID for queryset filtering? | `DatasetForm` already uses `ModelSelect2Widget` with `name__icontains` search — queryset filtering is queryset-based, not PK-based |
| Any template needed for update/delete views? | FairDMUpdateView and FairDMDeleteView use generic templates from mvp — no new templates needed for basic function |
| Does `DatasetCreateView` currently set `form_class`? | Yes — `form_class = DatasetForm`. This changes to `form_class = DatasetCreateForm`. |
