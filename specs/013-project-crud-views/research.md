# Research: Project CRUD Views

**Feature**: 013-project-crud-views  
**Date**: 2026-05-11  
**Phase**: Phase 0 — Resolving unknowns from Technical Context

---

## R-001 — Creation-date ordering field name

**Question**: What field does the `Project` model expose for creation-date ordering?

**Finding**: `Project` inherits from `BaseModel` which inherits from `fairdm.db.models.Model`. That base class defines:

```python
added = models.DateTimeField(auto_now_add=True)   # creation timestamp
modified = models.DateTimeField(auto_now=True)     # last-modified timestamp
```

**Decision**: Use `added` / `-added` as the ordering keys for creation-date ascending / descending in `ProjectListView.order_by`.

**Rationale**: `added` is the authoritative creation timestamp; it is set once and never mutated. `id`-based ordering is a valid proxy but `added` is semantically correct and already exists.

**Alternatives considered**: `id` ordering (rejected — not semantically a date field, confuses developers reading the code).

---

## R-002 — Existing `pre_delete` signal scope

**Question**: Does a model-level deletion guard already exist, and does it match the spec requirement?

**Finding**: A `@receiver(pre_delete, sender=Project)` handler called `prevent_project_deletion_with_datasets` already exists at the bottom of `fairdm/core/project/models.py`. It:

- Blocks deletion when `instance.datasets.exists()` (i.e., ANY linked dataset, public or private)
- Raises `ValidationError` with a string message
- Does **not** carry the list of blocking objects

**Mismatches vs spec**:

1. Scope: must block only on PUBLIC datasets, not all datasets
2. Exception type: `ValidationError` is not catchable in a view's `post()` without extra work; a custom exception is cleaner
3. Payload: must expose the list of blocking datasets for the view to render

**Decision**: Replace the existing signal handler body. Keep `@receiver(pre_delete, sender=Project)` but narrow the guard to `visibility=PUBLIC` and raise a new custom exception class `PublicDatasetsProtect` (carrying the list of blocking datasets).

**Rationale**: Narrowing to PUBLIC matches the spec. A custom exception allows the view to catch it, retrieve the dataset list from `e.datasets`, and render it without a separate queryset. Using `ValidationError` for a deletion guard is semantically awkward.

**Alternatives considered**:

- Keep `ValidationError`, catch it in the view via `try/except` — rejected because `ValidationError` is not specific enough; it can collide with other unrelated validation errors.
- Move guard to view only — rejected per the clarified spec (model-level enforcement).

---

## R-003 — Placeholder list-item template

**Question**: Does a list-item template for `ProjectListView` already exist?

**Finding**: `fairdm/core/project/templates/project/project_card.html` exists. `ProjectListView` already references it via `list_item_template = "project/project_card.html"`.

**Decision**: No new template file needed. FR-007 is already satisfied.

---

## R-004 — `get_absolute_url()` vs `project-detail` redirect target

**Question**: `ProjectCreateView.get_success_url()` calls `self.object.get_absolute_url()`, which resolves to `reverse("project:overview", ...)`. The spec says to redirect to `project-detail`. Are these the same page?

**Finding**:

- `get_absolute_url()` → `project:overview` — the plugin-based project overview page (registered via the plugin/registry system)
- `project-detail` — maps to `ProjectDetailView` at `/projects/<uuid>/`

These are two distinct URL names pointing to two different views. The spec explicitly names `project-detail` as the redirect target for both create and update.

**Decision**: Change `ProjectCreateView.get_success_url()` to `reverse("project-detail", kwargs={"uuid": self.object.uuid})` to match the spec. `ProjectUpdateView.get_success_url()` already returns `reverse("project-detail", ...)` — no change needed there.

**Rationale**: Redirecting to `project-detail` is what the spec requires. The detail view itself is out of scope (not being changed), but redirecting to it is fine.

**Alternatives considered**: Keep `get_absolute_url()` — rejected because the spec is explicit about `project-detail`.

---

## R-005 — `ProjectUpdateView` base class migration

**Question**: `ProjectUpdateView` currently inherits from raw Django `UpdateView`. What changes are needed to migrate to `FairDMUpdateView`?

**Finding**: Current class:

```python
class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectUpdateForm
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    ...
```

- Imports `UpdateView` from `django.views.generic` — needs to be replaced with `FairDMUpdateView` from `fairdm.views`
- `LoginRequiredMixin` stays
- The permission check in `get_object()` stays (it uses `django-guardian`)
- `get_success_url()` already returns `reverse("project-detail", ...)` ✓
- No template name is declared — `FairDMUpdateView` will auto-derive `project/project_form.html`; check if it exists

**Decision**: Replace `UpdateView` import with `FairDMUpdateView`. Keep all other class attributes unchanged.

---

## R-006 — `ProjectDeleteView` design

**Question**: `ProjectDeleteView` does not exist. How should it be designed?

**Finding**:

- `FairDMDeleteView` exists in `fairdm.views.base`
- Django's standard `DeleteView` does not include name-confirmation; this must be added
- The spec requires: (1) object-level permission check, (2) model-level guard catch, (3) name confirmation via POST field

**Decision**: Add `ProjectDeleteView` that:

1. Inherits `LoginRequiredMixin, FairDMDeleteView`
2. Overrides `get_object()` to check `delete_project` object-level permission
3. Overrides `post()` to:
   a. Extract `confirm_name` from `POST` data
   b. Compare (stripped) against `self.object.name`; if mismatch, re-render with a name-error flag
   c. Call `self.object.delete()`; catch `PublicDatasetsProtect` exception; re-render with `protected_datasets` context
   d. On success, redirect to `project-list`

**Rationale**: Using a custom `post()` is simpler than wiring a form class through `FairDMDeleteView` (whose `form_valid` path is unclear without deeper inspection of `MVPDeleteView`). The name-confirmation via raw POST data is standard for this pattern.

---

## R-007 — URL wiring for `project-delete`

**Question**: What path and kwarg pattern should the delete URL use?

**Finding**: Existing patterns in `urls.py`:

- `projects/<str:uuid>/update/` → `project-update`
- `projects/<str:uuid>/` → `project-detail`

**Decision**: Use `projects/<str:uuid>/delete/` → `project-delete`. Consistent with the `edit/` sibling pattern.

---

## R-008 — Name-confirmation exception class location

**Question**: Where should `PublicDatasetsProtect` be defined?

**Decision**: Define it at module level in `fairdm/core/project/models.py`, above the signal handler that raises it, so both models and views can import it without a circular dependency.

---

## Summary of Changes Required

| File | Change Type | Description |
|------|-------------|-------------|
| `fairdm/core/project/models.py` | Modify + Add | Add `PublicDatasetsProtect` exception; narrow `pre_delete` signal to PUBLIC datasets only |
| `fairdm/core/project/views.py` | Modify + Add | Add `added`/`-added` ordering; fix `ProjectCreateView.get_success_url`; migrate `ProjectUpdateView` to `FairDMUpdateView`; add `ProjectDeleteView` |
| `fairdm/core/project/urls.py` | Modify | Add `project-delete` URL pattern; add `ProjectDeleteView` to imports |
| `tests/test_core/test_project/test_views.py` | Modify | Add/update smoke tests for list, create, update, delete |
