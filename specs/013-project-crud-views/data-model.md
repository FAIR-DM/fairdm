# Data Model: Project CRUD Views

**Feature**: 013-project-crud-views  
**Date**: 2026-05-11  
**Phase**: Phase 1 — Design

---

## Entities

### Existing (unchanged schema)

#### `Project` (`fairdm.core.project.models.Project`)

No schema changes. Direct model fields relevant to this feature:

| Field | Type | Notes |
|-------|------|-------|
| `uuid` | `ShortUUIDField` | URL slug; auto-generated; prefix `"p"` |
| `name` | `CharField(max_length=300)` | Inherited from `BaseModel` |
| `image` | `ThumbnailerImageField` | Inherited from `BaseModel` |
| `visibility` | `IntegerField(choices=Visibility)` | `PRIVATE=0`, `PUBLIC=1` |
| `status` | `IntegerField(choices=ProjectStatus)` | `CONCEPT`, `PLANNING`, etc. |
| `funding` | `JSONField(null=True, blank=True)` | DataCite FundingReference schema |
| `owner` | `ForeignKey(Organization, null=True, blank=True)` | Owning organisation |
| `added` | `DateTimeField(auto_now_add=True)` | Inherited from `fairdm.db.models.Model`; creation timestamp |
| `modified` | `DateTimeField(auto_now=True)` | Inherited; last-modified timestamp |

Reverse accessor for datasets: `project.datasets` (from `Dataset.project` FK with `related_name="datasets"`)

#### `Dataset` (`fairdm.core.dataset.models.Dataset`)

No schema changes. Relevant field for deletion guard:

| Field | Type | Notes |
|-------|------|-------|
| `project` | `ForeignKey(Project, related_name="datasets")` | Links dataset to project |
| `visibility` | `IntegerField(choices=Visibility)` | `PUBLIC=1` datasets block project deletion |

---

## New Exception Class

### `PublicDatasetsProtect`

**Location**: `fairdm/core/project/models.py` (module level, above the signal handler)

```python
class PublicDatasetsProtect(Exception):
    """Raised by pre_delete signal when a Project has publicly visible datasets.

    Attributes:
        datasets: QuerySet of public Dataset instances blocking deletion.
    """
    def __init__(self, datasets):
        self.datasets = datasets
        super().__init__(
            f"Cannot delete project: {datasets.count()} public dataset(s) must be made private or deleted first."
        )
```

**Raised by**: `prevent_project_deletion_with_datasets` (pre_delete signal handler)  
**Caught by**: `ProjectDeleteView.post()`

---

## Modified Signal Handler

### `prevent_project_deletion_with_datasets`

**Location**: `fairdm/core/project/models.py` (at module bottom, after `Project` class)

**Change**: Narrow from blocking on ALL datasets to blocking only on PUBLIC datasets; raise `PublicDatasetsProtect` instead of `ValidationError`.

```python
@receiver(pre_delete, sender=Project)
def prevent_project_deletion_with_datasets(sender, instance, **kwargs):
    public_datasets = instance.datasets.filter(visibility=Visibility.PUBLIC)
    if public_datasets.exists():
        raise PublicDatasetsProtect(public_datasets)
```

**Before (existing)**:
- Raised `ValidationError` when ANY dataset (`instance.datasets.exists()`) exists
- Carried only a string message

**After**:
- Raises `PublicDatasetsProtect` when only PUBLIC datasets exist
- Carries the queryset so the view can list them by name

---

## View Changes

### `ProjectListView` (existing — modify)

| Attribute | Before | After |
|-----------|--------|-------|
| `order_by` | `[("name", "Name (A-Z)"), ("-name", "Name (Z-A)")]` | Add `("added", "Date created (oldest)"), ("-added", "Date created (newest)")` |

All other attributes unchanged.

---

### `ProjectCreateView` (existing — modify)

| Method | Before | After |
|--------|--------|-------|
| `get_success_url()` | `return self.object.get_absolute_url()` → `project:overview` | `return reverse("project-detail", kwargs={"uuid": self.object.uuid})` |

All other attributes unchanged.

---

### `ProjectUpdateView` (existing — migrate base class)

| Attribute | Before | After |
|-----------|--------|-------|
| Base class | `LoginRequiredMixin, UpdateView` | `LoginRequiredMixin, FairDMUpdateView` |
| Import | `from django.views.generic import ..., UpdateView` | Remove `UpdateView`; add `FairDMUpdateView` from `fairdm.views` |

All other attributes and methods unchanged.

---

### `ProjectDeleteView` (new)

**Location**: `fairdm/core/project/views.py`

```
ProjectDeleteView
  ├── LoginRequiredMixin
  └── FairDMDeleteView
        model = Project
        slug_field = "uuid"
        slug_url_kwarg = "uuid"
        success_url = reverse_lazy("project-list")

  get_object()         — calls super(); then checks delete_project permission
  get()                — inherited (renders confirmation page)
  post()               — name-confirmation + PublicDatasetsProtect catch
```

**`get_object()` logic**:
1. Call `super().get_object()` (handles 404)
2. If `not request.user.has_perm("delete_project", obj)` → raise `PermissionDenied`
3. Return `obj`

**`post()` logic**:
1. `self.object = self.get_object()`
2. Extract `confirm_name = request.POST.get("confirm_name", "").strip()`
3. If `confirm_name != self.object.name` → re-render with `{"name_error": True}`
4. `try: self.object.delete()` → `return HttpResponseRedirect(self.success_url)`
5. `except PublicDatasetsProtect as e:` → re-render with `{"protected_datasets": e.datasets}`

---

## URL Pattern Addition

**File**: `fairdm/core/project/urls.py`

```python
path("projects/<str:uuid>/delete/", ProjectDeleteView.as_view(), name="project-delete"),
```

Added after the `project-update` pattern.

---

## Test Coverage

**File**: `tests/test_core/test_project/test_views.py`

### New smoke tests required (Constitution Principle V)

| URL name | Method | Actor | Expected status |
|----------|--------|-------|-----------------|
| `project-list` | GET | anonymous | 200 |
| `project-create` | GET | anonymous | 302 (→ login) |
| `project-create` | GET | authenticated | 200 |
| `project-update` | GET | anonymous | 302 (→ login) |
| `project-update` | GET | user without permission | 403 |
| `project-update` | GET | user with permission | 200 |
| `project-delete` | GET | anonymous | 302 (→ login) |
| `project-delete` | GET | user without permission | 403 |
| `project-delete` | GET | user with permission | 200 |

### Behaviour tests required

| Scenario | What to verify |
|----------|---------------|
| POST `project-delete` — correct name, no public datasets | Project deleted; redirect to `project-list` (302) |
| POST `project-delete` — wrong name | Project not deleted; 200 re-render with `name_error` |
| POST `project-delete` — correct name, has public dataset | Project not deleted; 200 re-render with `protected_datasets` listing the blocking dataset |
| POST `project-delete` — correct name, has only private datasets | Project deleted (private datasets do NOT block deletion) |
