# Base views

This page lists the view classes your portal subclasses: the seven base views in `fairdm.views` and the mixin for views behind a record. It gives each class's parents, attributes, hooks and context. It does not explain why the classes are layered this way, which is in [How FairDM views are layered](../explanation/how-fairdm-views-are-layered.md), and it does not cover the home page view, which is in [Home page](home-page.md).

All seven classes are importable from `fairdm.views`:

```python
from fairdm.views import (
    FairDMCreateView,
    FairDMDeleteView,
    FairDMDetailView,
    FairDMListView,
    FairDMTableView,
    FairDMTemplateView,
    FairDMUpdateView,
)
```

Each class puts django-mvp's view under django-meta's `MetadataMixin`. django-mvp draws the page inside the application shell. `MetadataMixin` adds a `meta` object to the context.

## Which view to subclass

| To build | Subclass | Based on |
|---|---|---|
| A page with a template and no object | `FairDMTemplateView` | `MVPTemplateView` |
| A list of objects as cards | `FairDMListView` | `MVPListView` |
| A list of objects as a table | `FairDMTableView` | `MVPTableView` |
| A page for one object | `FairDMDetailView` | `MVPDetailView` |
| A form that creates an object | `FairDMCreateView` | `MVPCreateView` |
| A form that edits an object | `FairDMUpdateView` | `MVPUpdateView` |
| A confirmation page that deletes an object | `FairDMDeleteView` | `MVPDeleteView` |

## What every view shares

### Page attributes

These come from django-mvp's `PageMixin`. Each has a `get_*` method of the same name for values that depend on the request.

| Attribute | Type | Default | What it does |
|---|---|---|---|
| `page_title` | `str` | `""` | The page heading |
| `page_subtitle` | `str` | `""` | The line under the heading |
| `page_class` | `str` | `""` | Classes added to the page container, after `mvp-page` |
| `page_width` | `PageWidth` | `PageWidth.WIDE` | How wide the content is. One of `NARROW`, `MEDIUM`, `WIDE`, `FULL`, importable from `mvp.views` |
| `breadcrumbs` | list of dicts | `[]` | The trail. Each dict has `text` and, optionally, `href` |
| `page_info` | `str` | `""` | Text that explains the page. When set, an info icon beside the heading opens it |
| `page_info_actions` | list of dicts | `[]` | Buttons at the foot of the info dialog |

The context holds a `page` dict with the keys `title`, `subtitle`, `class`, `breadcrumbs`, `info`, `info_actions` and `width`.

### Metadata attributes

`MetadataMixin` builds `meta` from view attributes. The ones you set most are:

| Attribute | What it sets |
|---|---|
| `title` | The page title in the `<title>` tag and in Open Graph and Twitter Card tags |
| `description` | The description in those tags |
| `image` | The share image, as an absolute URL |
| `keywords` | The keywords, as an iterable of strings |

The mixin has more attributes, such as `url`, `object_type`, `site_name` and `schema`, and a `get_meta_*` method for each. They are described in the [django-meta documentation](https://django-meta.readthedocs.io/).

To output the tags, include django-meta's template in the `<head>` of your base template:

```django
{% include "meta/meta.html" with meta=meta %}
```

## `FairDMTemplateView`

A page that renders a template.

- Based on: `MetadataMixin`, `MVPTemplateView`.
- Default `template_name`: `"page_view.html"`, django-mvp's page template.
- Context: `meta`, `page`.

```python
from fairdm.views import FairDMTemplateView


class AboutView(FairDMTemplateView):
    template_name = "myapp/about.html"
    page_title = "About us"
    title = "About us"
    description = "Learn about our research data portal."
```

## `FairDMListView`

A paginated list drawn as cards or custom items. The search, the sort and the filters all come from one filterset.

- Based on: `MetadataMixin`, `MVPListView`.
- Context: `meta`, `page`, `grid_config`, `list_item_template`, `empty_state`, `filter`, `object_list`.

| Attribute | Type | Default | What it does |
|---|---|---|---|
| `model` | model class | None | The model to list |
| `paginate_by` | `int` | `25` | Objects per page |
| `grid` | dict | `{"cols": 1, "gap": 2}` | The responsive grid, passed to the template as `grid_config` |
| `list_item_template` | `str` or `None` | `None` | The template drawn for each item. `None` uses `<app_label>/<model_name>_list_item.html` |
| `filterset_class` | `FilterSet` subclass or `None` | `None` | The filterset that holds the search (`mvp.filters.SearchFilter`), the sort (`mvp.filters.SortFilter`) and the filters |
| `toolbar_filters` | list of `str` | `[]` | The names of the filterset fields drawn in the toolbar. The others sit in the filter panel |
| `empty_state_heading` | `str` or `None` | "There's nothing here yet" | The heading shown when the list is empty. `None` shows none |
| `empty_state_message` | `str` or `None` | A line pointing at the create button | The text under that heading. It is left out for a user who cannot create |

Hooks: `get_queryset()`, `get_grid_config()`, `get_list_item_template()`, `get_empty_state_heading()` and `get_empty_state_message()`.

A view that declares `search_fields` or `order_by`, or that also inherits django-filter's `FilterView`, raises `ImproperlyConfigured` when its module is imported. Put the search and the sort on the filterset. See [How to add search and sort to a list view](../how-to/add-search-and-sort-to-a-list-view.md).

```python
import django_filters
from mvp.filters import SearchFilter, SortFilter

from fairdm.views import FairDMListView
from .models import Project


class ProjectFilter(django_filters.FilterSet):
    q = SearchFilter(fields=["name", "uuid"])
    o = SortFilter(
        options=[
            ("name", "Name (A-Z)", ["name", "pk"]),
            ("-added", "Newest first", ["-added", "-pk"]),
        ]
    )

    class Meta:
        model = Project
        fields = ["status"]


class ProjectListView(FairDMListView):
    model = Project
    filterset_class = ProjectFilter
    toolbar_filters = ["q", "status"]
    grid = {"cols": 1, "sm": 2, "lg": 3}
```

## `FairDMTableView`

A paginated list drawn as a table by django-tables2. The template must render `{{ table }}`. Nothing renders it for you.

- Based on: `MetadataMixin`, `MVPTableView`.
- Context: `meta`, `page`, `table`, `filter`.

| Attribute | Type | Default | What it does |
|---|---|---|---|
| `model` | model class | None | The model to list |
| `table_class` | `django_tables2.Table` subclass | None | The columns. Required |
| `template_name` | `str` | None | The template that renders `{{ table }}`. Required |
| `filterset_class` | `FilterSet` subclass or `None` | `None` | The filterset that holds the search and the filters. A `SortFilter` on it is ignored, because the column headers sort |
| `toolbar_filters` | list of `str` | `[]` | The names of the filterset fields drawn in the toolbar |
| `paginate_by` | `int` | `100` | Rows per page. It is the only page-size control. It takes precedence over `Table.Meta.per_page` |

A view that declares `order_by` raises `ImproperlyConfigured`. Put the ordering on the table class.

```python
import django_tables2 as tables

from fairdm.views import FairDMTableView
from .filters import StationFilter
from .models import Station


class StationTable(tables.Table):
    class Meta:
        model = Station
        fields = ["name", "code", "added"]


class StationTableView(FairDMTableView):
    model = Station
    table_class = StationTable
    filterset_class = StationFilter
    template_name = "stations/station_table.html"
```

## `FairDMDetailView`

A page for one object. It adds nothing to `MVPDetailView` apart from the metadata.

- Based on: `MetadataMixin`, `MVPDetailView`.
- Context: `meta`, `page`, `object`.
- Attributes: `model`, plus Django's `slug_field` and `pk_url_kwarg`.
- Default page title: the object's string form.

```python
from django.shortcuts import get_object_or_404

from fairdm.views import FairDMDetailView
from .models import Station


class StationDetailView(FairDMDetailView):
    model = Station
    template_name = "stations/station_detail.html"

    def get_object(self, queryset=None):
        return get_object_or_404(Station, code=self.kwargs["code"])
```

The pages of a project, dataset, sample or measurement are not subclasses of this class. Each is a plugin. See [Plugins](plugins.md).

## `FairDMCreateView`

A form that creates an object. It adds no attributes of its own.

- Based on: `MetadataMixin`, `MVPCreateView`.
- Context: `meta`, `page`, `form`.
- Attributes: `model`, `fields` or `form_class`, `success_url`.
- Default page title: "Create" and the model's name.

```python
from fairdm.views import FairDMCreateView
from .models import Station


class StationCreateView(FairDMCreateView):
    model = Station
    fields = ["name", "code"]
    success_url = "list"
```

`success_url` is a literal path or one of django-mvp's shorthands for the model's other pages, such as `"list"` and `"detail"`. A view with no `success_url` redirects to the object's `get_absolute_url()`, and raises `ImproperlyConfigured` when there is none. A `?next=` address that stays on the site is used first.

## `FairDMUpdateView`

A form that edits an object.

- Based on: `MetadataMixin`, `MVPUpdateView`.
- Context: `meta`, `page`, `form`, `object`, and `delete_url` when a deletion page is registered.
- Attributes: `model`, `fields` or `form_class`, `success_url`, with the same rules as `FairDMCreateView`.
- Default page title: "Update" and the model's name.

```python
from fairdm.views import FairDMUpdateView
from .models import Station


class StationUpdateView(FairDMUpdateView):
    model = Station
    fields = ["name", "code"]
    success_url = "detail"
```

## `FairDMDeleteView`

A confirmation page that deletes an object.

- Based on: `MetadataMixin`, `MVPDeleteView`.
- Context: `meta`, `page`, `object`, and the deletion preview and protection state.

| Attribute | Type | Default | What it does |
|---|---|---|---|
| `model` | model class | None | The model to delete |
| `success_url` | `str` | None | Where to go after deleting. A literal path or a shorthand such as `"list"`. When unset, the model's list page is used, and `ImproperlyConfigured` is raised when there is none |
| `show_related_objects` | `bool` | `False` | Lists the records that deleting also deletes |
| `require_confirmation` | `bool` | `False` | Makes the user type the object's name before **Delete** works |
| `confirmation_label` | `str` | "Type the name to confirm" | The label of that input |
| `related_objects_max_per_group` | `int` | `25` | How many related objects are listed in each group |
| `related_objects_attrs` | dict | `{"variant": "info"}` | Attributes of the alert that holds the related-objects summary |

Hooks: `get_confirmation_value()`, `get_back_url()`, `get_back_url_fallback()`, `get_success_url()`.

FairDM changes two behaviours of `MVPDeleteView`:

- A record that something else relies on cannot be deleted, and the page says so instead of offering the confirmation. It lists what is in the way and draws no submit control. This covers relations declared `on_delete=PROTECT` and `on_delete=RESTRICT`.
- `get_back_url()` uses the `?back` address only when it stays on the site. Otherwise it returns `get_back_url_fallback()`, which is the model's list page, or an empty string when there is none.

```python
from fairdm.views import FairDMDeleteView
from .models import Station


class StationDeleteView(FairDMDeleteView):
    model = Station
    success_url = "list"
```

## `RelatedObjectMixin`

For a view behind the page of a core record. It fetches the record from the address and adds it to the context. List it before the view class.

```python
from fairdm.views.mixins import RelatedObjectMixin
```

| Attribute | Type | Default | What it does |
|---|---|---|---|
| `base_model` | model class | `None` | The model the record is fetched from |
| `base_object_url_kwarg` | `str` | `"uuid"` | The URL keyword that holds the record's `uuid` |

| Name | Returns |
|---|---|
| `base_object` | The record with that `uuid`. A record that does not exist answers 404 |
| `get_related_model()` | The model class the `uuid` belongs to |

The mixin adds these keys to the context: `base_object`, `base_model`, `base_model_name`, `non_polymorphic_object`, and the record again under its lowercase model name.

```python
from django.views.generic import ListView

from fairdm.core.sample.models import Sample
from fairdm.views.mixins import RelatedObjectMixin


class SampleNotesView(RelatedObjectMixin, ListView):
    base_model = Sample

    def get_queryset(self):
        return self.base_object.notes.all()
```

A view that is reached through a registered address should be a [plugin](plugins.md), which resolves the record itself.
