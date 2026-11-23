# Research: export the rows of any records table

## Assumptions checked

Run before the specification was put up for review, against the development stack of the
prototype branch (whose records tables differ from `main` only by the added export), and against
`main` at `eed6473e` for the code and the lock file.

| What the specification assumes | Result |
|---|---|
| The portal-wide listings are routed and render | Holds. `/collections/samples/<type>/` and `/collections/measurements/<type>/` answer 200. Routed by `DataTableView.get_urls()` in `fairdm/contrib/collections/urls.py` |
| A dataset's and a project's Samples and Measurements tabs render | Holds. `/datasets/<uuid>/samples/`, `/datasets/<uuid>/measurements/`, `/projects/<uuid>/samples/` and `/projects/<uuid>/measurements/` answer 200 to a signed-in viewer. A private dataset's tab answers 404 to a visitor, so its rows never reach an export by that visitor |
| A contributor's Samples tab renders | Holds. `/contributor/<uuid>/samples/` answers 200 |
| Every records tab is a `DataTableView` | Holds. `RecordsTab` in `fairdm/contrib/collections/plugins.py` subclasses `DataTableView`, so a mixin on `DataTableView` reaches every tab and listing |
| A tab that lists rows always has one chosen type | Holds. `RecordsTab` picks the first type when none is asked for, and sets `chosen` to `None` only in the empty state |
| The title row has a place for actions | Holds. django-mvp's `table_view.html`, which `record_lists/records.html` and `collections/listing.html` extend, has a `page.actions` block |
| The table's query already limits rows to what the viewer may see | Holds. `RecordsTab.get_queryset` returns `type_rows(chosen, visible_records(), user)` |
| The filter set gives the matching rows across all pages | Holds. The prototype exports `get_filterset().qs`, which pagination does not touch |
| The formats can be written with what is installed | Holds. `tablib[ods,xlsx]` 3.10.0 is a runtime dependency (with `odfpy` 1.4.1 and `openpyxl` 3.1.5 in the lock file). The prototype's export answers `?export=csv` on a listing with `text/csv` |
| Tests of these tables run locally | Not without GDAL, which the host lacks. The suite runs in the development image, as the repository's `AGENTS.md` describes |
