# Implementation Plan: Record list tabs are shared across the pages that need them

**Input**: [spec.md](spec.md), [research.md](research.md), [sketch.md](sketch.md)

## Summary

Two plugins, Samples and Measurements, registered on a dataset, a project and a contributor. Each
lists one registered type's table at a time, chosen by a heading that is a dropdown where more
than one type is listed. Each page supplies only which records it is about; visibility, filter
choices, links and counts follow from the existing querysets. The approved sketch's templates,
markup and copy are kept. Everything behind them is rebuilt test-first.

## Technical context

Django 6, django-tables2, django-filter, django-mvp 0.33 (page shell, dropdown, empty panel),
daisy-cotton (menu), htmx 2 (already loaded). PostgreSQL with PostGIS. No new dependency and no
migration.

## Constitution check

- Tests first for every behaviour the specification states; wording and layout get none.
- No new dependency. No change to what a registration can declare.
- Access follows the rules FairDM already enforces (FS-018, FS-019, FS-032); nothing is relaxed.

## Design

### D1. The module and the registrations

`fairdm/contrib/collections/plugins.py` (moved from the sketch's `fairdm/core/record_lists.py`)
holds `RecordsTab`, a `Plugin` + `DataTableView` with `base_model` set by its two subclasses,
`Samples` and `Measurements`, each registered on `Dataset`, `Project` and `Contributor` with
`url_path` `samples` and `measurements` and orders 300 and 400. The sketch's import from the
contributors plugin package is removed.

### D2. Scope and viewer

`RecordsTab.scope()` returns the unfiltered association for the page's record (research R1): a
dataset's and a project's are one-line filters; a contributor's comes from a new
`Contributor.get_associated_records(base_model)`, which returns the records credited directly and
those beneath a credited dataset or project, reading `Dataset.all_objects` and `Project.objects`.
`Organization` overrides it to add `dataset__project__owner=self`, as it already does for
`get_public_datasets`. `RecordsTab.viewer()` returns the request user, or `None` on a contributor's
page not viewed by that person; an organization always gives `None`. `visible_records()` is
`scope().visible_to(viewer())`.

### D3. Types, the address and not-published

`type_counts(queryset)` groups by `polymorphic_ctype`, most numerous first, ties broken by verbose
name. Each entry carries its own table class, filter set, plural name and slug, so nothing later
reads the registry or `model_config` for the chosen type. `resolve_type()` picks the entry from the
`type` URL keyword, 404 for one not listed, and sets `record_state` to `listed` or `empty`. There is
no not-published state (research R2). **A tab whose state is not `listed` builds no table and no filter set and
borrows no registered type**, so a portal with no measurement type registered still answers 200 on
every Measurements tab. An address naming a type on an empty tab is 404.

### D3a. Who is offered a dataset's tabs

The two plugins' `check` on a dataset is `dataset_records_visible(request, dataset)`, a new function
beside `dataset_is_visible` in `fairdm/core/dataset/plugins.py`: the dataset's overview opens for the
viewer **and** the viewer may see its records, which holds when the dataset is published and no
private project hides it, or the viewer holds a level on it or its project, or a portal-wide view
right. The tab strip reads the same `check`, so the tab is not offered to anyone else and its
address answers 404 through `PrivateRecordNotFoundMixin`'s rule for a record the viewer cannot
reach. On a project and a contributor the check is the overview's own.

### D4. Records of a type that is no longer registered

They are listed under a fallback entry, slug `other`, carrying `SampleTable` or `MeasurementTable`
(`fairdm/contrib/collections/tables.py`), `SampleFilter` or `MeasurementFilter`, and the base
model's plural name. Offered only when such records exist.

### D5. The table

`get_queryset()` is the chosen type's rows among `visible_records()`, with `with_related()`,
`select_related("dataset")`, and for measurements `select_related("sample")` and
`with_effective_location(request.user)`. It is annotated with `dataset_open` and, for measurements,
`sample_open`, as `Exists` subqueries against what the request user may open (research R4).
`get_table_kwargs()` adds `DatasetColumn` on a project and a contributor, replaces the base
table's `sample` column with `SampleColumn` on measurements, drops the dataset icon column
everywhere, and pins the lead sequence `name`, dataset, sample. Both columns render from the
annotation, never from a per-row query. `SampleColumn` orders by `("-sample_open",
"sample__name")`, so hidden samples sort as one block after the named ones and reveal no position.

The default order is the table's `Meta.order_by` (`added`, `id` on the base tables). Whatever order
applies, `get_queryset` appends `pk`, so a registration's own table with no `order_by` still pages
stably.

### D6. Filter choices

`ScopedChoicesMixin` in `fairdm/registry/factories.py`, beside `PublishedChoicesMixin`, applied by
the tab's `get_filterset_class()`. In `__init__`, after the chain, each related-record filter's
queryset is narrowed to `queryset.filter(pk__in=self.queryset.values(filter.field_name))`, and for
samples and datasets also intersected with what the request user may see. On a dataset's own tab
`__init__` pops `dataset` from `self.filters` (approved by eye).

### D7. The tab mark

`PluginTabItem(MenuItem)` in `fairdm/contrib/plugins/menus.py`, built by `configure_tab`, carries
the set of view names the plugin mounts (its own, every `extra_views` entry, and every pattern its
`get_urls` returns) in `extra_context`, which flex_menu copies onto each per-request item, and
`match_url` marks the tab when the resolved view name is in that set. This also marks the
Contributors tab on its add and edit pages.

### D8. The breadcrumb trail

`DataTableView.get_page_title()` returns the type's verbose name; `get_context_data` stops
replacing `page`. `RecordsTab.get_page_title()` returns its kind label, so `Plugin.get_breadcrumbs`
ends with "Samples" or "Measurements".

### D9. The template

`fairdm/templates/record_lists/records.html` is kept as approved: heading or dropdown switcher in
the title block, the boosted menu, the summary, and the empty and not-published panels, with the
filter panel and the toolbar panel drawn only when records are listed.

### D10. Overview counts

The dataset and project overview figures link to the tabs (kept from the sketch). Both overviews
count through `visible_to(request.user)`, so the figures, the charts and the spatial coverage are
drawn only from records the viewer may see and always agree with the tabs. On a dataset whose
records the viewer may not see (D3a), the Samples and Measurements figures are left out of the
strip rather than shown as zero. This replaces specification 018's rule that a visitor sees a
public, unpublished dataset's counts and charts (spec FR-022, FR-024).

### D11. Development data and documentation

`demo/seed/record_lists.py` and `seed_record_lists` are kept, refused outside development, safe to
run twice. Documentation: `docs/developers/reference/plugins.md` gains a section naming the two
plugins, their pages, which records each page lists, and where columns, filters and search come
from. A user guide page `docs/users/` describes browsing a dataset's, a project's and a
contributor's samples and measurements, linked from the user guide's index. `CHANGELOG.md`
[Unreleased] names the two tabs, the tab mark on a plugin's other addresses and the listings' page
context; `docs/developers/reference/management-commands.md` gains `seed_record_lists`.

## Story order

US1 builds the tab, the dataset registration and every shared rule, in three groups. US2 adds the
project, US3 the contributor, each from the previous story's accepted commit.

## Risks

- `DataTableView` changes for the portal-wide listings too (D8). Their tests pin the title.
- The tab-mark change touches every record page's tab strip (D7). The strip's existing tests cover
  the overview and editing pages.
