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

## Re-read against specification 039, as merged

Done at the start of the build, against `main` at `1da05c97`. Each row is something the specification
or the planning notes assumed about 039 and what is actually there.

| Assumed | Found |
|---|---|
| A definition gives a type's columns, formats and export rows | It gives `name`, `model`, `formats` and `table_schema()`. `formats` lists the formats an import reads (`csv`, `tsv`, `xls`, `xlsx`, `ods`) and has no JSON, so the five export formats are this feature's own list. There is no `export_rows`: the stable order is applied here |
| Cells are written by the widget import reads them with | `fairdm.contrib.import_export.widgets.render_cell(column, instance)`. It writes the portal ID from `instance.uuid`, the sample's name from `instance.sample` whoever may open that sample, a location column from the record's own `location`, and any other column through its widget |
| The Excel guide's content comes from 039 | The columns carry `label`, `kind_label`, `unit`, `format_hint`, `required`, `description`, `example` and `allowed`. The guide text of the workbook is built from those. The page guide (`c-import.guide`) is HTML and is not reused |
| The portal-wide listing and every tab share one view | Holds. `DataTableView` in `fairdm/contrib/collections/views.py`; `RecordsTab` subclasses it |

## What the checks found that the specification did not say

- **A measurement row can name a sample the viewer may not open.** `type_rows` annotates every
  measurement row of a tab with `sample_open`, and `SampleColumn` draws a dash where it is false, so
  such rows are in the table, contrary to the "Edge Cases" paragraph of the specification. The
  specification's own requirement settles it: SC-004 and FR-005 say an export holds nothing the
  viewer may not see, and a sample's name is something they may not see. The export writes an empty
  `sample_name` cell where the viewer may not open the sample (decisions.md, D11).
- **`render_cell` is not viewer-aware.** It writes `sample.name` unconditionally. This feature does
  not change it: the writer blanks the cell from the row's `sample_open` annotation, and a row
  without the annotation gets an empty cell, so the failure is closed.
- **A measurement's location cells hold its own location.** The table's latitude and longitude read
  `effective_location` (the measurement's own, else its sample's where the viewer may open the
  sample). The file holds `location` itself, as 039's column definition says, so a measurement with
  no location of its own has empty cells and an unchanged file does not copy a sample's place onto it.
- **`openpyxl` is not a declared dependency.** It arrives through `tablib[xlsx]`. The workbook writer
  imports it directly, so it is added to `[project] dependencies` (deptry reads a transitive import
  as an error).
- **The prototype's CSV starts with a byte order mark.** `("﻿" + data.export("csv"))`, so Excel
  reads UTF-8 text in other scripts correctly. The port keeps it and the import (specification 041)
  must read a file with one.
- **Spreadsheet formulas.** openpyxl turns a string starting with `=` into a formula. A sample's
  name is typed by a contributor and downloaded by anyone, so the workbook writes every string cell
  as text (decisions.md, D12).

## What already exists

| New piece | Where the search stopped |
|---|---|
| Writing CSV, TSV, JSON and OpenDocument | tablib (installed, `tablib[ods,xlsx]`): `Dataset.export(format)`. No new code but the call and the byte order mark |
| Writing the workbook | openpyxl (installed through tablib, now declared): sheets, comments, list validation. New code only for the three sheets' content |
| A column's cell text | This repo: `render_cell` and the widgets of specification 039 |
| A column's guide text | This repo: the columns' own `label`, `kind_label`, `unit`, `format_hint`, `description`, `example` |
| Which rows the table lists, and the search and filters on them | This repo and django-mvp: `get_queryset()`, `get_filterset().qs`, `result_count`, `refinements` in the view's context |
| Whether the viewer may open a measurement's sample | This repo: `Sample.objects.visible_to(user)`, the same `Exists` `type_rows` annotates |
| The Export menu's markup | Browser: `<details>`/`<summary>` with DaisyUI's `dropdown` classes, ported from the prototype. New code only for the component that wraps it |
| Closing the menu on Escape, outside click and choosing a file | New code, about 25 lines of script ported from the prototype: `<details>` closes on none of those itself |
| The file name | Django: `django.utils.text.slugify` |
| The download response | Django: `HttpResponse` with `Content-Disposition`. The records are read in batches by `QuerySet.iterator`, which streams nothing: the file is built and then sent (D4) |
