# Research: FS-042 Find a record from anywhere in the portal

Written at specification time. The build's research adds to it.

## Assumptions checked

Each item is something the specification takes as already working. Checked 2026-11-25 against
`main` at `ddf99b47` with django-mvp 0.37.0 installed, the version `pyproject.toml` requires, and
against the prototype branch served on port 8000, which mounts the same search.

| Assumption | How it was checked | Result |
|---|---|---|
| django-mvp ships a results page, a dialog partial, a field, a button and a dialog | Read `mvp/search/urls.py`, `views.py` and the `cotton/mvp/search/` templates in the installed package | Present. `mvp.actions.search` draws the field, the button and the dialog |
| The search works for a signed-out visitor | Requested `/search/?q=alp` and `/search/panel/?q=` on the prototype, signed out | 200, results grouped by record type |
| An empty query lists the record types with their descriptions | Requested `/search/panel/?q=` | Lists each type with its description |
| A query that matches nothing says so | Requested `/search/panel/?q=zzzzqqq` | "Nothing found" state |
| Narrowing to one record type pages its results | Requested `/search/?q=alp&kind=samples` and read `SearchView` (20 a page) | Works |
| A record type that found nothing is left out of the dialog and counted as none on the results page | Read `search_panel` and `SearchView.get_context_data` | As stated |
| The query is stripped and cut before any kind sees it | Read `normalise_query` (100 characters) | As stated |
| The visitor's landing page has no app header, so no search | Read `fairdm/templates/fairdm/landing.html` (overrides `app.header`) and requested `/` signed out on the prototype | No search on the page |
| Every record type already has a list search naming the fields it matches | Read the `q` filters: project (`uuid`, `name`, `identifiers__value`), dataset (`name`, `uuid`, `identifiers__value`, …), sample (`name`, `local_id`, `uuid`), measurement (`name`, `uuid`), person and organization (`name`), literature (`literature/ui/filters.py`, `SEARCH_FIELDS`) | Present for all seven |
| The project and dataset lists show public records only, to everyone | Read `ProjectListView.get_queryset` (`get_visible()`) and `DatasetListView.get_queryset` (`Dataset.objects`, which excludes private, then `outside_private_projects()`) | As stated. Hence `decisions.md` D2 and D3 |
| Datasets, samples and measurements have a "may open" queryset | Read `DatasetQuerySet.visible_to` and the shared `visible_to` in `fairdm/core/managers.py` | Present. Projects have `accessible_to(user, level)` and `get_visible()`, no `visible_to` |
| django-mvp's model kind could search FairDM's records | Read `mvp/search/model_kind.py`: it filters `model._default_manager` by the visible primary keys | Would hide private datasets from everyone, because `Dataset.objects` excludes them. Hence `decisions.md` D1 |
| The people list leaves out superusers | Read `PersonListView` (`Person.objects.real()`) | As stated |
| Literature has a page per reference | Read `literature.models.Item.get_absolute_url` and `fairdm/conf/urls.py` (`literature/` mounted) | Present |

The host has no GDAL, so the portal's own `manage.py check` was not run outside its container. The
start-up checks the search adds (`mvp.E004` to `mvp.E009`) were read in `mvp/search/checks.py`.
