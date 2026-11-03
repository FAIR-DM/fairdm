# Research: 023-shared-record-list-tabs

Read against `main` at v0.5.0 and the approved sketch. There is no `planning-notes.md`.

## R1. Which records each page lists

Every rule is already a queryset in the repository, so the tab composes them and adds no
visibility logic of its own.

- **Visibility**: `RecordVisibilityMixin.visible_to(user)` (`fairdm/core/managers.py`) on samples
  and measurements decides per record by its own dataset, gives a level held on the record, its
  dataset or the project above, and reads portal-wide rights. `visible_to(None)` is
  `released_to_everyone()`: public, published, and no private project above. That is exactly
  FR-029's "released".
- **Dataset**: `filter(dataset=obj)`. **Project**: `filter(dataset__project=obj)`.
- **Contributor**: `Contributor.credited_object_ids(Sample|Measurement)` gives direct credits,
  stored under the concrete subclass's content type. Credits on datasets and projects are
  contributions on those records; `Dataset.all_objects` and `Project.objects` must be used, since
  `Dataset.objects` leaves private datasets out and a person's own page lists them. An organization
  adds `dataset__project__owner=obj`.
- **Viewer**: the request user on a dataset or project; on a contributor's page the request user
  only when it is that person, `None` otherwise (FS-032's rule for a list of one person's records).
  An organization never "views its own page", so it is always `None`.

**Decision**: a `scope()` per page kind returning the unfiltered association, and
`visible_records() = scope().visible_to(viewer)`. The sketch's code already has this shape and is
kept.

## R2. Not published yet, and empty

The sketch decides "not published yet" by whether the scope holds records in a public, unpublished
dataset that the viewer cannot see. That matches FR-022 and FR-024 and never reveals private
records, since the check is on public datasets only. A contributor's tabs never show it: their
hidden records are hidden for many reasons, and naming one would reveal it.

## R3. Filter choices scoped to the viewer and the page

`PublishedChoicesMixin` (`fairdm/registry/factories.py`) narrows every related-record filter of a
listing to published records, after the filter mixins' own `__init__` has assigned their choice
lists. It is the right mechanism and the wrong rule here: a team member and a person on their own
page see unpublished records, and every listing-wide choice would also offer records from outside
the page.

**Decision**: a sibling mixin built the same way, applied by the tab instead of
`PublishedChoicesMixin`. Each related-record filter's queryset is narrowed to the records that the
tab's visible rows point at through that filter's field: `queryset.filter(pk__in=rows.values(field))`.
A dataset filter therefore offers the datasets of rows the viewer can see, and a sample filter the
samples of those rows that the viewer may also see. A filter on a model visibility says nothing
about is left alone, as the existing mixin does. `applied_to` stays idempotent per class; the rows
are passed at instantiation, so no class is made per request.

## R4. A measurement's sample, and each row's dataset

The sketch decided openability per dataset with a set of all openable dataset ids, which grows with
the portal and misses a sample opened by a credit on itself.

**Decision**: annotate the table's queryset with `Exists` subqueries: `dataset_open` against
`Dataset.all_objects.visible_to(request.user)` and, for measurements, `sample_open` against
`Sample.objects.visible_to(request.user)`. The columns render a link, the plain name, or `—` from
the annotation. The request user, not the list's viewer, decides links: a person's page lists
released records, but a staff member reading it may still open a dataset. Query count stays flat.

## R5. The tab stays marked on a type's own address

`PluginRegistry.configure_tab` (`fairdm/contrib/plugins/registration.py`) builds each tab as a
flex_menu `MenuItem` with one `view_name`; flex_menu's `match_url` compares it to the resolved view
name exactly. A plugin's own additional addresses (`extra_views`, named `<plugin>-<child>`) are
therefore never marked either: the Contributors tab loses its mark on its add and edit pages today.

**Decision**: the tab item is marked for the plugin's own view name and every name the plugin's
`get_urls` mounts. A `MenuItem` subclass in `fairdm/contrib/plugins/menus.py` holds the set of
names and overrides `match_url`. The type address is mounted through `get_urls` as today, named
`<plugin>-type`, so it is in the set. The sketch's rewriting of the resolved view name goes.

## R6. The breadcrumb trail

`DataTableView.get_context_data` (`fairdm/contrib/collections/views.py`) replaces the whole `page`
dict that `MVPViewMixin.get_page_context` (django-mvp `mvp/views/base.py`) builds, to set a title.
That drops `breadcrumbs`, which `Plugin.get_breadcrumbs` supplies.

**Decision**: `DataTableView` sets its title through `get_page_title()` and leaves `page` alone.
The portal-wide listings keep their title and now carry whatever trail their view declares, which
is none. The tab overrides nothing for the trail.

## R7. Where the plugins live

The tab reuses `DataTableView` and the type tables, which belong to `fairdm.contrib.collections`.
That app is installed after the four core record apps, and its own `plugins.py` is discovered by
`autodiscover_modules("plugins")` (`fairdm/apps.py`).

**Decision**: the module becomes `fairdm/contrib/collections/plugins.py`. The import from the
contributors app's plugin package goes.

## R8. The type switcher

The approved sketch uses django-mvp's `c-mvp.dropdown` with a `button` slot holding the heading,
and daisy-cotton's `c-menu` items, inside a container boosted with `hx-target="main"
hx-select="main" hx-swap="outerHTML"`. htmx 2 is already on every page. Nothing on the server
changes for the boost. Kept as approved.

## R9. Overview counts and the tabs

FS-018 counts a public, unpublished dataset's samples and measurements on its overview and on its
project's overview for a visitor, and shows none of its records. FR-025 asks the tab to list as many
records as the overview counts for the same viewer.

**Decision**: the counts lead to the tabs. Where the viewer may see every counted record, the two
agree, and a test pins that. Where some counted records are unpublished, the tab lists the records
the viewer may see and the not-published state covers a tab with none; the overview keeps FS-018's
counts. Recorded as D2 in `decisions.md`.

## R10. Query counts

`django_assert_num_queries` is used for list pages already (`tests/test_contrib/test_collections`).
Per-page work in the tab: the type counts (one query), the not-published check (one, only when
empty), the table page, the annotations (subqueries, no extra queries), the paginator count, the
filter set's choice querysets (lazy, rendered once each).

## What already exists

| Piece | Where the search stopped |
|---|---|
| Which records a viewer may see | this repo: `RecordVisibilityMixin.visible_to`, `released_to_everyone` |
| A contributor's direct credits | this repo: `Contributor.credited_object_ids` |
| The type table, filter set and search | this repo: registry `get_table_class`, `get_filterset_class`, `DataTableView` |
| Counting records per type | this repo: `DatasetOverview.get_record_types` counts per type for the chart; the tab's `type_counts` also needs the registry entry and the order, so it stays, and the plan reuses one helper for both where the shapes match |
| Choice scoping after the mixins' `__init__` | this repo: `PublishedChoicesMixin` is the pattern; the new mixin is its sibling |
| Openable link per row | Django: `Exists` annotation |
| The tab staying marked | new code: flex_menu matches one view name only |
| The dropdown and menu | installed: django-mvp `cotton/mvp/dropdown/index.html`, daisy-cotton `cotton/menu/item.html` |
| Swapping the page in place | installed: htmx 2 `hx-boost` |
| Empty and not-published panels | installed: django-mvp `cotton/mvp/page/list/empty.html` |
| Development data | this repo: `demo/seed/` and its `seed_*` commands |
