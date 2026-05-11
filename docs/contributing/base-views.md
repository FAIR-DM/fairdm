# Base View Classes

FairDM defines seven base view classes in `fairdm/views/base.py`. Each class
composes a django-mvp view with `django-meta`'s `MetadataMixin` to give every
FairDM page consistent AdminLTE layout *and* automatic SEO metadata (Open
Graph, Twitter Cards, Schema.org).

---

## Overview

Django's generic class-based views are powerful, but building a portal
requires three additional concerns:

1. **Consistent UI shell** — every page must render inside the AdminLTE layout
   with breadcrumbs, a page title, and a sidebar.
2. **SEO metadata** — every page should emit `<meta>` tags so portal content
   is discoverable by search engines and shareable on social networks.
3. **Stable API contract** — portal-specific code should always subclass the
   same base, so framework changes land in one place.

The FairDM view layer solves all three by introducing a thin wrapper per view
type.

---

## The Three-Layer Hierarchy

Every FairDM view sits in a three-layer stack:

| Django generic view | django-mvp view | FairDM view |
|---|---|---|
| `TemplateView` | `MVPTemplateView` | `FairDMTemplateView` |
| `ListView` + `FilterView` | `MVPFilteredListView` | `FairDMListView` |
| `DetailView` | `MVPDetailView` | `FairDMDetailView` |
| `CreateView` | `MVPCreateView` | `FairDMCreateView` |
| `UpdateView` | `MVPUpdateView` | `FairDMUpdateView` |
| `DeleteView` | `MVPDeleteView` | `FairDMDeleteView` |
| `ListView` + `FilterView` + `SingleTableMixin` | `MVPTableViewMixin` + `FilterView` | `FairDMTableView` |

**Layer 1 — Django** provides the standard HTTP/form/queryset lifecycle.

**Layer 2 — django-mvp** adds the AdminLTE page shell (`PageMixin`), CRUD
directory URL resolution (`CRUDDirectoryMixin`), list ordering/search
(`SearchOrderMixin`), and form rendering helpers (`MVPFormBase`). All
django-mvp views render the base AdminLTE layout automatically.

**Layer 3 — FairDM** adds `MetadataMixin` (from `django-meta`) on top of
every django-mvp view. This is the only layer portal-specific subclasses
should inherit from.

---

## SEO Metadata with `MetadataMixin`

`MetadataMixin` (from the [`django-meta`](https://django-meta.readthedocs.io/)
package) injects a `meta` object into every view's template context under the
key `"meta"`.  Templates use this object to render `<meta>` tags:

```html+django
{% load meta %}
{% block meta %}
    {% include "meta/meta.html" with meta=meta %}
{% endblock %}
```

Control the `meta` object via view-level attributes:

| Attribute | Description | Example |
|---|---|---|
| `title` | Page title for `<title>` and OG | `"FairDM Projects"` |
| `description` | OG / Twitter description | `"Browse all projects"` |
| `image` | Absolute URL of the share image | `static("img/og.jpg")` |
| `keywords` | Comma-separated keyword string | `"FAIR, data, research"` |

Alternatively, a model-level `_metadata` dict on the object being displayed
is respected automatically when the view has an `object` attribute (e.g.
`FairDMDetailView`).

See the [django-meta documentation](https://django-meta.readthedocs.io/)
for the full attribute reference.

---

## Quick Reference

| Operation | FairDM view | When to use |
|---|---|---|
| Static / lightly dynamic page | `FairDMTemplateView` | About pages, dashboards, landing pages |
| Card-style object list | `FairDMListView` | Browse pages, search results as cards |
| Object detail page | `FairDMDetailView` | Single-object display |
| Object creation form | `FairDMCreateView` | "New …" form pages |
| Object edit form | `FairDMUpdateView` | "Edit …" form pages |
| Object deletion confirmation | `FairDMDeleteView` | "Delete …" confirmation pages |
| Tabular object list | `FairDMTableView` | Admin-style table grids |

---

## View Class Reference

### `FairDMTemplateView`

Use for any page that renders a template without a database-backed object
list or detail.

**Inherits from**: `MetadataMixin`, `MVPTemplateView`

**Key attributes**: `template_name` (required), `title`, `description`

```python
from fairdm.views import FairDMTemplateView


class AboutView(FairDMTemplateView):
    template_name = "myapp/about.html"
    title = "About Us"
    description = "Learn about our research data portal."
```

**Context keys**: `meta`, `page`

---

### `FairDMListView`

Paginated, filterable list rendered as cards or custom list items.  Sets
`paginate_by = 25` and `grid = {"cols": 1, "gap": 2}` by default.

**Inherits from**: `MetadataMixin`, `MVPFilteredListView`

**Key attributes**:

| Attribute | Default | Description |
|---|---|---|
| `paginate_by` | `25` | Objects per page |
| `grid` | `{"cols": 1, "gap": 2}` | Responsive grid config |
| `list_item_template` | `None` (auto-derived) | Partial template per item |
| `search_fields` | `None` | ORM paths for `?q=` search |
| `filterset_class` | `None` | `django_filters.FilterSet` subclass |

```python
from fairdm.views import FairDMListView
from .filters import ProjectFilter
from .models import Project


class ProjectListView(FairDMListView):
    model = Project
    filterset_class = ProjectFilter
    search_fields = ["name", "uuid"]
    grid = {"cols": 1, "sm": 2, "lg": 3}
```

**Context keys**: `meta`, `page`, `grid_config`, `filter`, `object_list`

---

### `FairDMDetailView`

Single-object detail page.  The model's `_metadata` dict is automatically
picked up by `MetadataMixin` to populate `meta.title` and friends.

**Inherits from**: `MetadataMixin`, `MVPDetailView`

**Key attributes**: `model` (required), `slug_field`, `pk_url_kwarg`

```python
from fairdm.views import FairDMDetailView
from .models import Project


class ProjectDetailView(FairDMDetailView):
    model = Project
```

**Context keys**: `meta`, `page`, `object`

---

### `FairDMCreateView`

Model creation form.  This is a *thin* composition — it adds no attributes of
its own beyond what `MVPCreateView` and `MetadataMixin` already provide.

**Inherits from**: `MetadataMixin`, `MVPCreateView`

**Key attributes**: `model` (required), `fields` or `form_class`, `success_url`

```python
from fairdm.views import FairDMCreateView
from .models import Dataset


class DatasetCreateView(FairDMCreateView):
    model = Dataset
    fields = ["name", "description", "visibility"]
    success_url = "list"  # CRUD shorthand resolved by MVPCreateView
```

**Context keys**: `meta`, `page`, `form`

---

### `FairDMUpdateView`

Model update form.  Corrects the common mistake of copy-pasting from
`FairDMCreateView` — the page title and breadcrumbs read "Update …" not
"Create …".

**Inherits from**: `MetadataMixin`, `MVPUpdateView`

**Key attributes**: `model` (required), `fields` or `form_class`, `success_url`

```python
from fairdm.views import FairDMUpdateView
from .models import Dataset


class DatasetUpdateView(FairDMUpdateView):
    model = Dataset
    fields = ["name", "description", "visibility"]
    success_url = "detail"  # CRUD shorthand resolved by MVPUpdateView
```

**Context keys**: `meta`, `page`, `form`, `object`

---

### `FairDMDeleteView`

Object deletion confirmation page.  `success_url` is **required** because the
object no longer exists after deletion — `get_absolute_url()` cannot be used as
a fallback.

**Inherits from**: `MetadataMixin`, `MVPDeleteView`

**Key attributes**: `model` (required), `success_url` (required)

```python
from fairdm.views import FairDMDeleteView
from .models import Dataset


class DatasetDeleteView(FairDMDeleteView):
    model = Dataset
    success_url = "list"  # CRUD shorthand resolved by MVPDeleteView
```

**Context keys**: `meta`, `page`, `object`

---

### `FairDMTableView`

Tabular object list powered by `django-tables2`.  The template is responsible
for rendering the `{{ table }}` object — no automatic rendering is provided.

**Inherits from**: `MetadataMixin`, `MVPTableViewMixin`, `FilterView`

**Key attributes**:

| Attribute | Required | Description |
|---|---|---|
| `model` | Yes | The model to list |
| `table_class` | Yes | A `django_tables2.Table` subclass |
| `filterset_class` | No | `django_filters.FilterSet` subclass |
| `template_name` | Yes | Template that renders `{{ table }}` |

```python
import django_tables2 as tables
from fairdm.views import FairDMTableView
from .filters import MeasurementFilter
from .models import Measurement


class MeasurementTable(tables.Table):
    class Meta:
        model = Measurement
        fields = ["name", "value", "unit", "created"]


class MeasurementTableView(FairDMTableView):
    model = Measurement
    table_class = MeasurementTable
    filterset_class = MeasurementFilter
    template_name = "measurements/measurement_table.html"
```

**Context keys**: `meta`, `page`, `table`, `filter`

---

## `FairDMListView` vs `FairDMTableView`

Both views display a collection of objects, but they solve different problems:

| | `FairDMListView` | `FairDMTableView` |
|---|---|---|
| **Layout** | Cards / custom item templates | Rows-and-columns table |
| **Item template** | `list_item_template` (per-item partial) | `table_class` (columns defined in Python) |
| **Sorting** | `order_by` class attribute | `django-tables2` column ordering |
| **Use case** | Browse pages, search results, "gallery" views | Admin grids, data exports, comparison tables |

**Rule of thumb**: choose `FairDMListView` when the visual design calls for
rich per-object cards, and `FairDMTableView` when the user needs to scan and
compare many objects at once in a structured grid.
