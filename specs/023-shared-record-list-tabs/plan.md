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

`RecordsTab.scope()` returns the unfiltered association for the page's record (research R1).
`RecordsTab.viewer()` returns the request user, or `None` on a contributor's page not viewed by
that person. `visible_records()` is `scope().visible_to(viewer())`. Organizations always use
`None`. Kept from the sketch, with the contributor branch reading `Dataset.all_objects` and
`Project.objects`.

### D3. Types, the address and not-published

`type_counts(queryset)` groups by `polymorphic_ctype`, keeps registered types, most numerous
first, ties broken by verbose name so the order is stable. `resolve_type()` picks the type from
the `type` URL keyword (the registry slug), 404 for a type not listed, and sets `record_state` to
`listed`, `unpublished` or `empty` (research R2). An address naming a type on an empty tab is 404.

### D4. Records of a type that is no longer registered

`type_counts` currently drops them. They are listed under a fallback entry using the base model's
table (`SampleTable` or `MeasurementTable` from `fairdm/contrib/collections/tables.py`) and the
base model's filter set, with slug `other`. Only offered when such records exist.

### D5. The table

`get_queryset()` is the chosen type's rows among `visible_records()`, with `with_related()`,
`select_related("dataset")`, and for measurements `select_related("sample")` and
`with_effective_location(request.user)`. It is annotated with `dataset_open` and, for measurements,
`sample_open`, as `Exists` subqueries against what the request user may open (research R4).
`get_table_kwargs()` adds `DatasetColumn` on a project and a contributor, replaces the base
table's `sample` column with `SampleColumn` on measurements, drops the dataset icon column
everywhere, and pins the lead sequence `name`, dataset, sample. Both columns render from the
annotation, never from a per-row query. Ordering by name is stable with `id` as the tie-break the
base tables already declare.

### D6. Filter choices

`ScopedChoicesMixin` in `fairdm/registry/factories.py`, beside `PublishedChoicesMixin`, applied by
the tab's `get_filterset_class()` and given the visible rows through `get_filterset_kwargs()`. In
`__init__`, after the chain, each related-record filter's queryset is narrowed to
`queryset.filter(pk__in=rows.values(filter.field_name))`, and for samples and datasets also
intersected with what the request user may see. On a dataset's own tab the `dataset` filter is
removed (approved by eye). `applied_to` is idempotent per class, as its sibling is.

### D7. The tab mark

`PluginTabItem(MenuItem)` in `fairdm/contrib/plugins/menus.py`, built by `configure_tab`, holds
the set of view names the plugin mounts: its own, every `extra_views` entry, and any extra pattern
its `get_urls` adds (read from the patterns it returns). `match_url` marks the tab when the
resolved view name is in the set. This also marks the Contributors tab on its add and edit pages.

### D8. The breadcrumb trail

`DataTableView.get_page_title()` returns the type's verbose name; `get_context_data` stops
replacing `page`. `RecordsTab.get_page_title()` returns its kind label, so `Plugin.get_breadcrumbs`
ends with "Samples" or "Measurements".

### D9. The template

`fairdm/templates/record_lists/records.html` is kept as approved: heading or dropdown switcher in
the title block, the boosted menu, the summary, and the empty and not-published panels, with the
filter panel and the toolbar panel drawn only when records are listed.

### D10. Overview counts

The dataset and project overview figures link to the tabs (kept from the sketch). Their counts are
unchanged (research R9).

### D11. Development data and documentation

`demo/seed/record_lists.py` and `seed_record_lists` are kept, refused outside development, safe to
run twice. Documentation: `docs/developers/reference/plugins.md` gains a section naming the two
plugins, their pages, which records each page lists, and where columns, filters and search come
from. A user guide page `docs/users/` describes browsing a dataset's, a project's and a
contributor's samples and measurements, linked from the user guide's index.

## Story order

US1 builds the tab, the dataset registration and every shared rule, in three groups. US2 adds the
project, US3 the contributor, each from the previous story's accepted commit.

## Risks

- `DataTableView` changes for the portal-wide listings too (D8). Their tests pin the title.
- The tab-mark change touches every record page's tab strip (D7). The strip's existing tests cover
  the overview and editing pages.
