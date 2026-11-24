# Implementation Plan: export the rows of any records table

**Branch**: `040-records-export` | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Summary

`fairdm.contrib.import_export` gains two modules: `exports.py` holds the class `TableExport`, which writes a file from a type's table
schema and a queryset (CSV, TSV, JSON and OpenDocument through tablib, Excel through one workbook
writer), and `mixins.py` holds `RecordExportMixin`, which answers `?export=<format>` on a records
table and gives the template the menu's data. `DataTableView` takes the mixin, so every tab and
listing has it. The menu is the Cotton component `c-import.export-menu`, placed in the title row by
the two templates that draw a records table, with its look and its closing script ported from the
prototype.

## Technical Context

- **Language and framework**: Python 3.13, Django 6.0, django-cotton, tablib 3.10, openpyxl 3.1.
- **New dependencies**: `openpyxl (>=3.1,<4.0)` in `[project] dependencies`. It is already
  installed through `tablib[xlsx]`, and the writer imports it directly (research.md).
- **Storage**: none. No model and no migration.
- **Testing**: pytest with pytest-django against PostGIS, from the worktree's own `.venv`
  (`. ../fairdm-040-env.sh; .venv/bin/python -m pytest <path> -n0`). Tests sit in `Test<Subject>`
  classes in the module that mirrors the source file. No test of wording or layout.

## Constitution Check

- **Simplicity**: two modules, one component, one script file. No setting, no model, no route.
- **Privacy first**: the export reads the rows the table lists, through the table's own query. The
  one cell that reaches past a row, a measurement's sample name, is written only where the viewer
  may open the sample, and an unannotated row gets an empty cell (D11).
- **Established packages over custom code**: tablib writes four of the five formats, openpyxl the
  fifth (research.md, "What already exists"). Written here: the workbook's three sheets and the
  menu's closing script, which `<details>` does not do itself.
- **Works without custom JavaScript**: the menu opens, and each link downloads, without the script.
  The script only closes the menu on Escape, an outside click and a chosen file.

## What is ported

From `prototype-import-export`, read with `git show origin/prototype-import-export:<path>`. The
files are copied and cleaned, never redrawn from `main`'s older components.

| Prototype | Lands on `main` as |
|---|---|
| `partials/table_actions.html`, the Export `<details>` | `fairdm/templates/cotton/import/export_menu.html`, `c-import.export-menu`, taking `menu`. Markup and copy are copied. Changes: `tx-` classes become `ie-`, `data-tx-menu` becomes `data-ie-menu`, the Import button and its wrapper stay out (the page wraps the menu, D15), and the unfiltered title reads "All rows of the type" without a count (D8) |
| `tabular.css` lines 300-315 (`.tx-tools`, `.tx-menu`, `.tx-caret`, `.tx-menu__panel`, `__title`, `__formats`, `__fmt`, `__hint`, `__foot`) | `fairdm/static/css/fairdm.css`, in the existing "Import and export" section, `tx-` renamed `ie-`, with `.ie-tools` not declaring `--ie-*` (the menu reads `--color-*` only) |
| `tabular.js`, the `click` and `keydown` handlers on `details[data-tx-menu]` | `fairdm/static/js/export-menu.js`, `data-ie-menu`, linked from `base.html` with `defer`. The drop zone and one-submit parts are specification 041's |
| `record_lists/records.html`, its `page.actions` block | The same block in `fairdm/templates/record_lists/records.html` |
| `collections/listing.html`, its `page.actions` block | The same block in `fairdm/contrib/collections/templates/collections/listing.html` |
| `exports.py` (`export_response`, `rows_for`, `guide_rows`, `workbook`) | `fairdm/contrib/import_export/exports.py`, rebuilt test-first (below) |
| `mixins.py` (`RecordTransferMixin`) | `fairdm/contrib/import_export/mixins.py`, `RecordExportMixin`, rebuilt test-first. The Import parts of it are specification 041's |

The look is checked at the merge gate side by side with the prototype's "Samples tab with Export
and Import" (without the Import button), "Export menu open, with a search active" and a portal-wide
listing, at 390 and 1400 wide. The differences this plan names, and so accepts: the Import button is
absent until 041, and an unfiltered menu's title carries no count (D8).

## The writer: `fairdm/contrib/import_export/exports.py`

```python
EXPORT_FORMATS: tuple[ExportFormat, ...]   # csv, xlsx, ods, tsv, json, in this order
```

`ExportFormat` is a frozen dataclass: `key`, `label`, `hint` (lazy translated, the menu's one-line
note), `content_type`, `extension`. The labels are CSV, Excel, OpenDocument, TSV and JSON.
`format_for(key)` returns the entry or `None`.

`TableExport(schema)` is the one class (Article X: the writing functions share the schema). It is
what specification 041's template download calls as `TableExport(schema).workbook()`.

- `rows(queryset)`: a generator that reads `queryset.iterator(chunk_size=500)` and yields one list
  of cells per record, each `render_cell(column, record)`. Two columns are the exception: `sample_name`
  and `sample` write `""` unless `getattr(record, "sample_open", False)` is true (D11, D16).
- `response(queryset, key, filename_stem)`: builds the payload and returns an `HttpResponse` with
  the format's content type and the header from `django.utils.http.content_disposition_header(True,
  filename)`, where the file name is `slugify(stem, allow_unicode=True)` plus the extension, so a
  name in any script still identifies the record.
  - CSV and TSV: `tablib.Dataset(headers=schema.headings)`, each row appended, `export("csv")` or
    `export("tsv")`, UTF-8, CSV preceded by a byte order mark (research.md).
  - OpenDocument: `export("ods")`.
  - JSON: `export("json")`, UTF-8: a list of one object per row keyed by the headings.
  - Excel: `workbook(rows)`.
- `workbook(rows=())` returns the workbook's bytes. It takes any iterable of rows, so it writes the
  same workbook with none (FR-011).
  1. **Sheet 1**, named for the type: the plural name with the characters Excel forbids
     removed and cut to 31 characters. The first row holds the headings, bold and
     coloured by whether the column is required, written on export only, or neither; the panes
     below it are frozen; column widths follow the heading's length. Every string is written as text
     (`cell.data_type = "s"`), never as a formula (D12).
  2. **A note on each heading** (an openpyxl `Comment`): the column's label, kind label, unit where
     it has one, how to write it (`format_hint`), "Required for new records." where it is, "Not read
     on import." for a column written on export only, and its description.
  3. **Sheet 2, the guide**, named "Column guide" (translated, cut to 31): a title line, one line on
     the portal ID, then one row per column: heading, label, needed, type, unit, how to write it,
     example, what it holds. "Needed" is "Required for new records", "Optional" or "Written on
     export, not read".
  4. **Sheet 3, the allowed values**, named "Allowed values" (translated, cut to 31): one column per
     column of the file that has `allowed` values, or is a yes-or-no kind (`yes`, `no`), headed by
     the heading, the values below.
  5. **A list validation** on each such column of sheet 1 from row 2 to row `max(rows + 1000, 5000)`,
     pointing at that column's range on sheet 3 (a range, never an inline list, so a long list
     works), `allow_blank=True`, `showErrorMessage=False` so a value outside the list is allowed.
  6. A sheet name that would repeat another sheet's gets `" (2)"` before the cut so the workbook
     opens.
  Every word written is passed through `gettext`, so FR-016 holds. The wording is not specified.

## The mixin: `fairdm/contrib/import_export/mixins.py`

`RecordExportMixin` is added first in `DataTableView`'s bases. It does nothing unless the request
carries `export`.

- `export_definition()`: `get_definition(self.model._meta.model_name)`, returned only when its
  `model is self.model` and the view lists a type (`getattr(self, "chosen", True)` is not `None`).
  Otherwise `None`.
- `get(request, ...)`: no `export` parameter, `super().get(...)`. Otherwise, with no definition or a
  key outside `EXPORT_FORMATS`, `Http404` (FR-014). Otherwise
  `TableExport(definition.table_schema()).response(self.export_queryset(), key, stem)`.
- `export_queryset()`: the queryset is `self.get_queryset()` when the request carries
  `scope=all`, else `self.get_filterset().qs` (or `get_queryset()` when the view has no filter set).
  The filter set is built from the request's own parameters, so the file and the table cannot
  disagree (Edge Cases). The page number is ignored because a filter set does not read it. The
  result is `.order_by("pk").prefetch_related(None)`, and on a measurement type is annotated with
  `sample_open = Exists(Sample.objects.visible_to(self.request.user).filter(pk=OuterRef("sample_id")))`
  unless the queryset already has that annotation (D3, D11). It also calls `select_related` on
  every column of kind `concept` whose attribute is a relation (a sample's status is one on every
  type) and on `sample` for a measurement, so a cell costs no query of its own.
- The file's stem (slugified with `allow_unicode=True` by the response): the record whose tab it is (`self.base_object`, where the view has one) and the
  type's plural name, then the date from `timezone.localdate().isoformat()`, joined with spaces and
  slugified by the response (FR-013).
- `get_context_data()`: `context["export_menu"]` is `None` when there is no definition or
  `result_count` is 0 (D13), else a dict: `filtered` (whether `refinements` is non-empty), `shown`
  (`result_count`), `type_name` (the type's plural name) and `formats`, a list of `{label, hint,
  shown_url, all_url}` one per format. `all_url` is `?export=<key>&scope=all`. `shown_url` is the
  request's own query with `export`, `scope` and `page` removed and `export=<key>` added.

The measurement's `sample_open` annotation and the ordering are the only changes to the table's
query. Nothing in the table's own pages changes.

## The component and its placement

`fairdm/templates/cotton/import/export_menu.html`, `c-import.export-menu`, `<c-vars menu />`. It
draws nothing when `menu` is empty. Otherwise a `<details class="dropdown dropdown-end ie-menu"
data-ie-menu>` whose `<summary class="btn btn-sm btn-ghost">` holds the download icon, "Export"
and the caret. The panel lists, when `menu.filtered`, "The N row(s) the filters show" with each
format's `shown_url`, then "Every <type> here" with each `all_url`; otherwise "All <type>" with each
`all_url`. A footer line says the files keep each record's portal ID. Each link carries `download`.

The two templates place it in `{% block page.actions %}`:

```django
{% if export_menu %}<div class="ie-tools"><c-import.export-menu :menu="export_menu" /></div>{% endif %}
{{ block.super }}
```

`records.html` wraps the `if` in `record_state == "listed"` as the prototype does. A tab with no
records shows its empty state and no menu. Specification 041 adds its Import button inside the same
`div`.

## Tests

All new tests are seen to fail for the right reason before the code that makes them pass. Fixtures
the export tests need (published and private datasets with samples and measurements, built from
the repository's factories) are added to `tests/test_contrib/test_import_export/conftest.py`, since
`test_collections/conftest.py` does not reach that directory.

- `tests/test_contrib/test_import_export/test_exports.py`
  - `TestExportResponse`: parametrised over every registered sample and measurement type (SC-001, SC-002) and every format; headings equal `schema.headings` in order with
    `portal_id` first (SC-002); content type and extension; a value with a delimiter, a quote or a
    line break stays one row after being read back by `csv`/`tablib`; non-ASCII text survives every
    format; JSON is a list of objects keyed by the headings; CSV starts with the byte order mark;
    an empty optional value and a record with no location give empty cells.
  - `TestExportOrder`: rows come out in primary-key order given a queryset sorted otherwise.
  - `TestSampleName`: a measurement row with `sample_open` true writes the sample's name and portal ID, false or
    unannotated writes `""` in both the `sample_name` and `sample` cells.
  - `TestWorkbook`: with openpyxl's `load_workbook`, sheet 1 holds the rows, sheet 2 the guide with
    a row per column, sheet 3 an allowed list per listed column; a heading note carries the label,
    kind, unit and whether needed; each listed column has a list validation pointing at its range; a
    type name of more than 31 characters and one with `/` gives a workbook that opens with valid
    sheet names; a column with 300 allowed values keeps all 300 on sheet 3; a name `=1+1` is read
    back as the text `=1+1`; the same call with no rows writes the same three sheets and the same
    headings.
- `tests/test_contrib/test_import_export/test_mixins.py`
  - `TestExportRequest`: on a dataset's Samples tab, `?export=csv` returns the dataset's rows only;
    each of the five keys answers 200 with its content type; `?export=xls`, `?export=` and
    `?export=csv` on a tab with no types answer 404 and send no file; `?q=` search plus `export` gives
    exactly the matching rows from across several pages (page size patched to 2 to span pages) and
    `scope=all` gives every row; `page=2` in the address does not change the file.
  - `TestExportVisibility`: a visitor's and another person's export of a portal-wide listing
    holds none of a private dataset's samples, in both choices of rows (SC-004); a measurement whose
    sample the viewer may not open is in the file with an empty `sample_name`.
  - `TestExportStability`: two downloads of the same rows are equal whatever `?sort=` the table
    was given (SC-005).
  - `TestExportMenuContext`: `export_menu` is `None` on an empty table and on a search with no
    match, `filtered` is false without a search and true with one, `shown` equals `result_count`,
    and the URLs drop `page`.
  - `TestFileName`: the name carries the type, the record's name where there is one, and the date (also a name in a non-Latin script).
  - `TestExportQueries`: exporting a sample type's rows costs the same number of queries for 3 rows as
    for 30 (`django_assert_max_num_queries`).
- `tests/test_contrib/test_collections/test_views.py` (additions): `TestExportOnPages`: the portal
  listing and a dataset, project and contributor tab each render the menu and a custom
  `DataTableView` subclass inherits it (FR-018). The tab with no records renders none.
- `tests/test_templates/test_export_menu.py`: `TestExportMenuComponent` renders the component with
  a filtered and an unfiltered menu and asserts one link per format per choice, each with
  `download`, the `<details>` carrying `data-ie-menu`, the filtered choice only when `filtered`, and nothing for `menu=None`.

Mutation pass at S5: for each template or page-output test above, delete the markup or flip the
condition it names and see it fail.

## Pages checked in a browser

At S5, `forge browser-check` over the Samples tab, the same with `?q=`, and the portal listing, at
390 and 1280 wide, with the seeded data. A short script driven once in headless Chrome opens the
menu, presses Escape and checks focus is back on the button, clicks outside and checks it closes,
and clicks a format and checks it closes.

## Specifications and documents edited

- `CHANGELOG.md`: an "Added" line under Unreleased.
- `docs/developers/reference/table-schema.md` or a new reference page `export.md` beside it (the
  implementer picks the one that reads best): the five formats, the choice of rows, the columns, the
  order, who sees what, the byte order mark, and how a portal's own `DataTableView` gets the menu.
- `CONTEXT.md`: a glossary entry for "export".
- `specs/040-records-export/spec.md` is not edited by this build. Its Edge Cases line about a
  measurement whose sample the viewer may not see is wrong about the table (research.md). The build
  meets SC-004 as written and reports the line to the orchestrator for correction (D11).
