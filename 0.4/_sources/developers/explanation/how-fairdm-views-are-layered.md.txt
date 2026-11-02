# How FairDM views are layered

This page explains why every FairDM view sits on top of a django-mvp view, which sits on top of a Django view, and which layer your portal's views should extend. It covers the reasoning and the choice between a list view and a table view. It does not list the classes and their attributes, which are in [Base views](../reference/base-views.md).

## Three layers

Every FairDM view is a three-layer stack:

| Django view | django-mvp view | FairDM view |
|---|---|---|
| `TemplateView` | `MVPTemplateView` | `FairDMTemplateView` |
| `ListView` | `MVPListView` | `FairDMListView` |
| `DetailView` | `MVPDetailView` | `FairDMDetailView` |
| `CreateView` | `MVPCreateView` | `FairDMCreateView` |
| `UpdateView` | `MVPUpdateView` | `FairDMUpdateView` |
| `DeleteView` | `MVPDeleteView` | `FairDMDeleteView` |
| `ListView` with django-tables2 | `MVPTableView` | `FairDMTableView` |

**Django** supplies the request lifecycle: forms, querysets, pagination and redirects.

**django-mvp** puts the result in the application shell. It adds the page title, subtitle and breadcrumbs, resolves the addresses of a model's other pages for `success_url` and the back link, builds the search, sort and filters of a list from one django-filter filterset, and renders forms and deletion pages in the shell's layout.

**FairDM** puts django-meta's `MetadataMixin` first, ahead of the django-mvp view. Every page then carries a `meta` object that describes it for search engines and for link previews.

## Why there is a FairDM layer

A portal has three needs that Django's views do not meet alone:

1. **Every page sits in the same shell.** A page that extends a plain Django view has no heading, no breadcrumbs and no navigation.
2. **Every page can describe itself.** Search engines and link previews read metadata, and portal content should be found.
3. **Your code has one stable place to extend.** When your views extend the FairDM class, a change that FairDM makes for every page lands in one place, and your views get it without edits.

The third need has a visible example. `FairDMDeleteView` changes two behaviours of the layer beneath it, and every portal view that extends it receives both. A record that something else relies on is refused with an explanation, whether the relation is `PROTECT` or `RESTRICT`. The back link follows only an address on the same site.

Because the FairDM layer is thin, a view that extends it behaves as the django-mvp view would, plus metadata. `FairDMCreateView` and `FairDMDetailView` add nothing else.

## Which layer to extend

Extend the FairDM class. Do not extend `MVPListView` or Django's `ListView` directly. A view that skips the FairDM layer has no `meta` object and misses any change FairDM makes there.

A project, dataset, sample or measurement page is not a standalone detail view. It is a plugin, which combines `Plugin` with a FairDM view, so the page gets its address, its tab and its record from the plugin machinery and its layout from the view. Extend `FairDMDetailView` directly when a record's page needs no extra pages and no tab of its own. See [Plugins](../reference/plugins.md).

## A list view or a table view

Both show a collection, but they answer different needs.

| | `FairDMListView` | `FairDMTableView` |
|---|---|---|
| Layout | Cards or custom items | Rows and columns |
| What you write | An item template | A `django_tables2.Table` class |
| Sorting | A `SortFilter` on the filterset | The column headers |
| Page size | 25 | 100 |
| Suits | Browsing, search results, galleries | Scanning and comparing many records |

Choose the list view when each record deserves a card of its own. Choose the table view when the reader needs to compare many records at once.

The two differ in where they put ordering because a table already has a natural control for it, the column header. A table view therefore ignores a `SortFilter` and refuses an `order_by` on the view, and sends you to the table class instead. A list view has no headers, so its sort is a filter.
