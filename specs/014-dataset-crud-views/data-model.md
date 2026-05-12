# Data Model: Dataset CRUD Views

**Branch**: `014-dataset-crud-views` | **Date**: 2026-05-12

> No new database models or migrations. This feature operates entirely at the view/form/URL layer.

---

## Existing Model: Dataset

The `Dataset` model is not modified by this feature. The relevant fields and permissions are documented here for reference.

### Fields used by views/forms

| Field | Type | Notes |
|-------|------|-------|
| `uuid` | ShortUUIDField | URL slug; prefix `"d"` |
| `name` | CharField | Human-readable name; used for deletion confirmation |
| `image` | ImageField (optional) | Shown in `DatasetForm` (update) only |
| `project` | ForeignKey → Project | Optional (`blank=True, null=True`) |
| `license` | ForeignKey → License | Defaults to CC BY 4.0 via form |
| `reference` | ForeignKey → literature (optional) | Shown in `DatasetForm` (update) only |
| `doi` | Handled via `DatasetIdentifier` | Entry field on `DatasetForm` (update) only |
| `visibility` | IntegerField (choices) | Excluded from all CRUD forms — managed via publish workflow |
| `added` | DateTimeField (auto) | Used for list ordering; set by tracking mixin |

### Object-level permissions (django-guardian)

| Permission codename | Purpose |
|--------------------|---------|
| `view_dataset` | Read access (assigned on create) |
| `change_dataset` | Edit access (required by update view) |
| `delete_dataset` | Delete access (required by delete view) |
| `change_dataset_metadata` | Edit metadata (assigned on create) |
| `change_dataset_settings` | Edit settings (assigned on create) |

All five permissions are assigned to the creating user by `DatasetCreateView.form_valid()`.

---

## New Form: DatasetCreateForm

```python
class DatasetCreateForm(DatasetForm):
    class Meta(DatasetForm.Meta):
        fields = ["name", "project", "license"]
```

### Field details

| Field | Required | Widget | Notes |
|-------|----------|--------|-------|
| `name` | Yes | TextInput | Dataset title |
| `project` | No | ModelSelect2Widget | Inherited from parent; queryset filtered via `request` |
| `license` | Yes | ModelSelect2Widget | Defaults to CC BY 4.0 via parent `__init__` |

### Inheritance chain

```
DatasetForm (base, full form for update)
└── DatasetCreateForm (restricted field set for creation)
```

`DatasetCreateForm` inherits all `__init__` logic from `DatasetForm` including request handling, queryset filtering, and license default. It only restricts `Meta.fields`.

---

## Modified Form: DatasetForm (no code changes)

`DatasetForm` is unchanged. For reference:

| Field | Required | Notes |
|-------|----------|-------|
| `name` | Yes | |
| `image` | No | |
| `project` | No | |
| `license` | Yes | |
| `reference` | No | Only shown when `fairdm.contrib.literature` installed |
| `doi` | No | Handled via `DatasetIdentifier` in `save()` |

`visibility` is intentionally excluded.

---

## View Design

### DatasetListView (existing — minor review only)

```python
class DatasetListView(FairDMListView):
    model = Dataset
    filterset_class = DatasetFilter
    search_fields = ["uuid", "name", "descriptions__value"]
    order_by = [
        ("name", _("Name (A-Z)"), "name"),
        ("-name", _("Name (Z-A)"), "-name"),
        ("added", _("Date created (oldest first)"), "added"),
        ("-added", _("Date created (newest first)"), "-added"),
    ]

    def get_queryset(self):
        return super().get_queryset().get_visible().with_contributors()
```

### DatasetCreateView (modified)

Changes:
- `form_class` → `DatasetCreateForm` (was `DatasetForm`)
- Remove `get_initial()` override (removed `?project=` pre-population)
- Existing `get_form_kwargs()` passing `request` is retained

### DatasetUpdateView (new)

```python
class DatasetUpdateView(LoginRequiredMixin, FairDMUpdateView):
    model = Dataset
    form_class = DatasetForm
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_object(self, queryset=None):
        uuid = self.kwargs.get("uuid")
        dataset = get_object_or_404(Dataset, uuid=uuid)
        if not self.request.user.has_perm("change_dataset", dataset):
            raise PermissionDenied(...)
        return dataset

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_success_url(self):
        return reverse("dataset-detail", kwargs={"uuid": self.object.uuid})
```

### DatasetDeleteView (new)

```python
class DatasetDeleteView(LoginRequiredMixin, FairDMDeleteView):
    model = Dataset
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    success_url = reverse_lazy("dataset-list")
    require_confirmation = True

    def get_object(self, queryset=None):
        uuid = self.kwargs.get("uuid")
        dataset = get_object_or_404(Dataset, uuid=uuid)
        if not self.request.user.has_perm("delete_dataset", dataset):
            raise PermissionDenied(...)
        return dataset

    def get_confirmation_value(self):
        return self.object.name
```

---

## URL Contracts

| Name | Pattern | View | Auth | Object Perm |
|------|---------|------|------|------------|
| `dataset-list` | `datasets/` | `DatasetListView` | None | None |
| `dataset-create` | `datasets/create/` | `DatasetCreateView` | Login required | None |
| `dataset-update` | `datasets/<str:uuid>/update/` | `DatasetUpdateView` | Login required | `change_dataset` |
| `dataset-delete` | `datasets/<str:uuid>/delete/` | `DatasetDeleteView` | Login required | `delete_dataset` |

> `dataset-list` and `dataset-create` already exist. Only `dataset-update` and `dataset-delete` are new.

---

## State Transitions

```
[Anonymous] ──GET /datasets/──→ DatasetListView (filtered to visible)

[Authenticated] ──GET /datasets/create/──→ DatasetCreateView
                ──POST /datasets/create/──→ [redirect to dataset-detail]

[has change_dataset] ──GET /datasets/<uuid>/update/──→ DatasetUpdateView
                     ──POST /datasets/<uuid>/update/──→ [redirect to dataset-detail]

[has delete_dataset] ──GET /datasets/<uuid>/delete/──→ DatasetDeleteView (confirmation form)
                     ──POST /datasets/<uuid>/delete/──→ [redirect to dataset-list]
```
