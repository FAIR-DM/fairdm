# Implementation Plan: import a spreadsheet of samples or measurements into a dataset

**Branch**: `041-records-import` | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Summary

`fairdm.contrib.import_export` (app label `fairdm_import_export`) gains the import. Two models
hold it: `ImportJob`, one file uploaded into one dataset, and `ImportRow`, one row's outcome. A
reader turns a file into headings and rows, a matcher pairs headings with the columns of the type's
table schema, one dataset-bound resource reads a row into a record, and a runner checks or imports
a file in a Celery task and keeps every row's outcome. Undo and the 30-day discard are two more
functions over the same rows. The pages are dataset plugins, drawn by Cotton components under
`cotton/import/` ported from the prototype. The Import buttons sit beside the Export menu in the
two records templates and in the empty states, and open one dialog of types.

## Technical Context

- **Language and framework**: Python 3.13, Django 6.0, django-cotton, django-import-export,
  tablib (CSV, TSV, Excel, OpenDocument), openpyxl, Celery with django-celery-beat, HTMX as served
  by django-mvp 0.36.1, `c-mvp.modal`, django-mvp-forms 0.11.0 `CardSelect`.
- **New dependencies**: none. Every library above is already a dependency on `main`.
- **Storage**: two tables, `ImportJob` and `ImportRow`, one migration. Uploaded files go to the
  portal's file storage under `imports/%Y/%m/` and are deleted at the end of the import (D4).
- **Testing**: pytest with pytest-django against PostGIS, from the worktree's own `.venv`
  (`. ../fairdm-041-env.sh; .venv/bin/python -m pytest <path> -n0`). Tests sit in `Test<Subject>`
  classes in the module that mirrors the source file. No test of wording or layout. Celery tasks
  run eagerly in tests.
- **Standards that bind every task**: no leading-underscore names, line length 88, no
  compatibility aliases, no test of text or design preferences, Cotton components and never
  `{% include %}` partials, every new public name documented with a Google-style docstring.

## Constitution Check

- **Simplicity**: no new app. The reader, matcher, resource, runner, undo and pages are one module
  each. One options form, one chooser component. The import reuses the definition lookup, column
  model, cell widgets, guide and workbook writer that FS-039 and FS-040 built.
- **Privacy first**: the import checks `dataset.import_data` on every page and action and answers
  an unauthorised person as it answers a page they may not open (a 404). A row never reads or
  writes another dataset's record. A sample column reads only the samples the person may see.
- **Established packages over custom code**: django-import-export runs the dry run, row results
  and diffs. tablib reads the four formats. HTMX polls progress. See research.md "What already
  exists".
- **Works without custom JavaScript**: the pages are server-rendered forms and links. The script
  adds the file drop zone's feedback and a one-submit guard. Progress refreshes with HTMX and,
  without it, with a reload.

## What is ported

From `prototype-import-export`, read with `git show origin/prototype-import-export:<path>`. The
files are copied and cleaned, never redrawn from `main`'s older components. `tx-` classes become
`ie-`, `data-tx-*` become `data-ie-*`, every `{% include %}` becomes a Cotton component and every
inline panel, tag and badge in `job.html` and `columns.html` becomes a component under
`fairdm/templates/cotton/import/`.

| Prototype | Lands on `main` as |
|---|---|
| `cotton/tabular/import_menu.html` (the Import button and its dialog of types) | `cotton/import/import_menu.html`, `c-import.import-menu`, taking `chooser` and `label` |
| `tabular/start.html` | `fairdm/contrib/import_export/templates/import_export/import_start.html` (the import page of a type), extending `page_view.html` |
| `tabular/columns.html` | `.../import_export/import_columns.html` (column matching) |
| `tabular/job.html` | `.../import_export/import_job.html` (check, import, undo) |
| `tabular/history.html` | `.../import_export/import_history.html` (past imports) |
| `partials/steps.html` | `cotton/import/steps.html`, `c-import.steps`, taking `steps` and `current` |
| `partials/job_list.html` | `cotton/import/job_list.html`, `c-import.job-list`, taking `jobs` |
| `partials/progress.html` | `cotton/import/progress.html`, `c-import.progress`, taking `percent`, `done`, `total` and `url` |
| panels, tags and badges drawn inline | `cotton/import/panel.html`, `cotton/import/tag.html`, `cotton/import/outcome_badge.html` (names settled by the build, one component per repeated shape) |
| `tabular.css`, every rule that is not the guide's or the menu's | `fairdm/static/css/fairdm.css`, "Import and export" section, `tx-` renamed `ie-` |
| `tabular.js`, the drop zone and the one-submit guard (not the menu's close handlers, which FS-040 ported) | `fairdm/static/js/import.js`, linked from `base.html` with `defer` |
| `record_lists/records.html`, the Import button in `page.actions` and the empty-state button | the same file on `main`, inside the `ie-tools` wrapper FS-040 left |
| `collections/listing.html`, the Import part if any | the same file on `main` |

The guide, the export menu and the cell widgets already on `main` are not ported again. The
prototype's `partials/guide.html` is FS-039's `cotton/import/guide.html`, which the import page
places with `c-import.guide`.

The look is checked at the merge gate against the prototype's screens at 390 and 1400 wide, as
the brief lists them. Differences this plan names, and so accepts: none yet. A difference found
later is checked with `git diff origin/prototype-import-export HEAD -- <look files>` and either
fixed or recorded with that diff.

## Planning notes, answered

Each note in `planning-notes.md` is answered in research.md and below. In short:

- **Row outcomes are a table, not JSON on the job (D16).** A 50,000-row file would make one JSON
  value of tens of megabytes that every status poll and page load reads whole. `ImportRow`
  holds one row each, so the check's rows are read a page at a time with a filter on the outcome and
  an index. Adopted, with the reason.
- **Progress stays in the cache, fetched by HTMX (D17).** The cache is Redis in every portal. A
  database column cannot hold it, because the check's progress is written while the dry run's
  transaction is open and the same connection rolls it back. `hx-trigger="every 1s"` on the
  progress component and an `HX-Refresh` header when the run ends are what HTMX already offers.
  Adopted, with the reason.
- **Undo detects a change by a digest of the stored values (D18).** Adopted, see "Undo".
- **ARIA table roles on divs**: the matching page and the rows of a check use real `<table>`
  elements. Adopted.
- **Another dataset's records are left out**, **the located-resource defect is fixed on `main`**,
  and **the stored file is deleted** as the specification says.
- **The duplicated location column names**: the prototype's second copy is not ported. The
  resource reads `LOCATION_COLUMNS` from `fairdm/utils/location/resources.py`. The status-to-title
  and badge-label duplication is removed by one `STATUS_LABELS` mapping on `ImportJob.Status`,
  read by the page title, the badge and the job list.
- **`BaseImportExportView`** is checked first: FS-040 left it in `views.py` only for the unrouted
  `DataImportView` and `DataExportView`. Both go with it. `DatasetPublishConfirm`,
  `DatasetPackageDownloadView`, `MetadataDownloadView`, `TableSchemaView` and the package builder
  in `utils.py` stay.

## Data model: `fairdm/contrib/import_export/models.py`

`ImportJob`: `dataset` (FK, cascade, `related_name="import_jobs"`), `definition_name` (the
definition's name, never the model), `created_by` (FK to the user, set null), `created`,
`file` (FileField, blank when deleted), `filename`, `file_format`, `file_size`, `mode`
(`both`, `add`, `update`), `empty_cells` (`keep`, `clear`), `status` (the ten states of the
specification), `headers` (list), `samples` (dict of up to four values per heading), `column_map`
(heading to column name or empty), `row_count`, `summary` (counts by outcome), `file_problems`
(list), `error`, `checked_at`, `imported_at`, `imported_by`, `undone_at`, `undone_by`.
`STATUS_LABELS` names each state once. Properties: `definition`, `model`, `type_name`,
`is_running`, `is_finished`, `writes`, `get_absolute_url`. `Meta.ordering = ["-created"]`.

`ImportRow`: `job` (FK, cascade, `related_name="rows"`), `number` (position in the file, from 1),
`line` (the line in the file), `outcome` (`new`, `update`, `unchanged`, `skipped`, `problem`),
`label`, `portal_id` (blank for a row that adds nothing yet), `record_pk` (nullable, set once the
import writes it), `changes` (JSON list of `{column, label, old, new}`), `problems` (JSON list of
`{column, message}`), `note` (the reason a row was left out), `values` (JSON, the cells by
heading), `before` (JSON, the stored values an undo restores, update rows only) and `digest`
(a 64-character hex digest of the record's stored values after the import). Index on
`(job, outcome, number)`. `Meta.ordering = ["number"]`.

One migration, `0001_initial`, with a `dataset` dependency taken from the latest dataset
migration. No data migration.

## Modules

All in `fairdm/contrib/import_export/` unless named.

- **`reader.py`**: `FileProblem`, `READABLE` (CSV, TSV, Excel, OpenDocument), `MAX_BYTES = 20 MB`,
  `MAX_ROWS = 50_000`, `file_format(name)`, `read_grid(raw, fmt)`, `parse(raw, fmt)` returning
  headings, rows and line numbers. Rebuilt test-first from the prototype's `engine.py`. JSON and
  `.txt` are not read (FR-005). The delimiter of a CSV is sniffed between `,` and `;` and a tab is
  never a CSV's. The first sheet of a workbook is read.
- **`matching.py`**: `normalise(heading)` (case, spaces and punctuation removed), `match_heading(
  schema, heading)` over each importable column's name, label, label without its unit and
  aliases, `match_columns(schema, headings)` (the first heading to take a column wins, a second
  stays unmatched), `mapping_problems(job, schema)` and `mapping_warnings(job)` (FR-008 to FR-010),
  and `needs_matching(job, schema)` (FR-009). Adds `TableSchema.match`'s role without touching the
  schema module: the matcher takes the schema.
- **`forms.py`** (rewritten): `ImportOptionsForm` (mode, empty cells, `CardSelect` widgets, a
  `brief` switch that drops the descriptions, `chosen(mode, empty)`) and `UploadForm` (the file
  field, size and extension checked, so a refused file leaves no job). The old `ImportForm` and
  `ExportForm` go.
- **`resources.py`** (rewritten): `RecordResource(LocatedResourceMixin, ModelResource)` reading
  and writing through each column's widget (`widgets.widget_for`), with the portal ID and Local ID
  lookup, the three modes, the empty-cell rule, the leaving-out of another dataset's row, the
  field problems of every row and a `changed_cells` list. `build_resource(schema, dataset, ...)`
  returns the class for the columns the file has. `RowProblem(column, message)` is the error a
  lookup raises. `BaseFairDMResource`, `SampleResource`, `MeasurementResource` and the old
  `SampleWidget` go. `ImportDefinition.resource(dataset, **options)` in `definitions.py` calls
  `build_resource`.
- **`widgets.py`**: `SampleCellWidget` keeps a per-instance cache of looked-up cells, keyed by
  the cell text, holding the sample or the problem, so a file with a repeated sample asks the
  database once per distinct cell (the review finding carried from FS-039). The resource builds
  one widget per run, so the cache lives for one file.
- **`runner.py`**: `check(job)`, `perform(job, user)`, `progress(job)`. Both read the file once,
  build the data set from the column map, run `import_data` and write the `ImportRow` rows in
  chunks of 1,000 with `bulk_create`. `check` runs the dry run, so it writes nothing to the
  dataset, then replaces the job's rows. `perform` is below.
- **`undo.py`**: `digest(record)`, `conflicts(job, user)`, `undo(job, user)`. See "Undo".
- **`tasks.py`**: `check_job`, `import_job`, `discard_stale_jobs`, and `start(task, *args)` that
  queues on commit and runs inline when no broker answers.
- **`plugins.py`**: the pages, below.
- **`apps.py`**: `ready()` registers the periodic task through `post_migrate`, as
  `fairdm/backups/signals.py` does.
- **`views.py`**: loses `BaseImportExportView`, `DataImportView`, `DataExportView` and
  `UploadForm`. `utils.py`: `get_formats`, `get_export_formats` and `get_import_formats` stay if
  `settings.IMPORT_FORMATS` still reads them. `build_export_for_datatype` writes through
  `TableExport(definition.table_schema())` and the tablib dataset it builds, keeping its
  signature.
- **`fairdm/utils/location/resources.py`**: `LocatedResourceMixin.import_instance` raises the
  field problems of a row that has no location column (FR-017).
- **`fairdm/registry/`**: the `resource` component, `ResourceFactory`, `resource_class` and
  `get_resource_class()` are removed. `resource_fields` stays: the column model reads it.
  `docs/developers/how-to/import-and-export-locations.md`, `reference/model-configuration.md`
  and `docs/contributing/registry-system.md` are edited to match.
- **`fairdm/conf/settings/`**: no new setting. The beat task is a database row.

## The check and the import

`check(job)`: read the file (`reader.parse`), keep the columns of `column_map`, find duplicate keys
inside the file (two rows with the same portal ID or Local ID both need changes, FR-014), build the
resource with `ImportDefinition.resource`, and run
`import_data(dry_run=True, use_transactions=True, raise_errors=False,
rollback_on_validation_errors=True, retain_instance_in_row_result=True)`. Each row result becomes
one `ImportRow`: a row with validation errors, a `RowProblem` or a duplicate is `problem` with
each problem and its column (FR-017: every one, whether or not the row has location columns); a
skip with a note is `skipped`; a skip without one is `unchanged`; `new` and `update` carry their
changes. Progress is written to the cache every ten rows (`on_row`). The job's status ends as
`problems`, `checked` or `nothing`. A file that cannot be read ends as `failed` and its file is
deleted.

`perform(job, user)` runs in one `transaction.atomic()`:

1. Lock the dataset row with `Dataset.objects.select_for_update()`. Imports of one dataset write
   one at a time, and the second reads what the first wrote (FR-021).
2. Run the same import as the check with `dry_run=False` and collect each row's outcome and
   changes in memory.
3. Compare, row by row, the outcome and the changes with the check's `ImportRow` rows. Any
   difference sets the transaction to roll back and raises a local exception.
4. On a difference: outside the rolled-back block, replace the rows with the new outcomes, set the
   status back to `problems` or `checked`, and set `error` to a sentence saying the dataset
   changed since the check (FR-019).
5. Otherwise, for each written row: record `record_pk`, `portal_id`, `digest(record)` and, for an
   update, `before` (the stored values of the attributes that changed). Set `imported_at`,
   `imported_by` and the status `imported`, and delete the file.

The two phases share one function (`run(job, dry_run)`), as the prototype's engine does. The
resource itself never touches the job.

## Undo

- **What is kept**: for a created record, `record_pk` and `digest`. For an updated record,
  `record_pk`, `digest` and `before`, a map from attribute name to the stored string of the value
  that was replaced (JSON-safe: strings for decimals, ISO text for dates, WKT for a point,
  portal IDs for relations).
- **`digest(record)`** is the SHA-256 of a canonical JSON of every concrete field's stored value,
  `modified` included, read with `field.value_to_string(record)`. Computed inside the import's
  transaction after the save, so it describes what the database holds. A save that changes
  nothing still moves `modified`, so even that is a change since. A queryset `update()` that skips
  `modified` changes a value and so changes the digest. A deleted record has no digest at all.
- **`conflicts(job, user)`** loads the touched records in chunks of 500 by `record_pk`, and returns
  one entry per record whose digest differs or that no longer exists, per sample added that has
  measurements (`Measurement.objects.filter(sample_id__in=...)`) and per record the person
  may not change (D20). It returns the first 20 and the full count.
- **`undo(job, user)`** runs in one `transaction.atomic()` after locking the dataset: it recomputes
  `conflicts`, raises when there is any, deletes the created records (one `delete()` per
  chunk through the type's manager so signals and polymorphic children fire as a hand deletion's
  do), and restores each updated record's `before` values through the same cell widgets in
  reverse, then saves it. It sets `undone_at`, `undone_by` and the status `undone`, and deletes the
  file if one is left.

## Pages: `fairdm/contrib/import_export/plugins.py`

Registered with `@plugins.register(Dataset, menu=False)` as the prototype does, so the addresses
sit under the dataset: `import/<type>/`, `imports/`, `imports/<job>/`, `imports/<job>/columns/`,
`imports/<job>/status/`, `imports/<job>/problems.xlsx`, `import/<type>/template.<fmt>/`.
`can_import(request, dataset)` is `has_perm(request, "dataset.import_data", dataset)` and every
page answers a person without it with a 404 through `handle_no_permission` (FR-001).

- `ImportPage` (base): permission, the step bar's context, breadcrumb.
- `ImportStart`: the type's page. Uses `c-import.guide`, the template links
  (`TableExport(schema).workbook()` for Excel, a headings-only file for CSV), the link to the
  type's Table Schema (`table_schema` URL from FS-039), the downloads of the dataset's current
  records (the records tab's `?export=…&scope=all`), the options form and the upload. A refused
  file is shown on the same page and no job exists.
- `JobColumns`: the matching page, real `<table>`, a heading, a few values and a select per row.
- `JobDetail`: the check, the import and its outcome, with the rows by outcome a page at a time
  (`per_page = 100`, `?show=` and `?page=`), reading `ImportRow` with a filter and slice. Actions
  (`import`, `discard`, `recheck`, `undo`) are POSTs that start a task and redirect.
- `JobStatus`: the progress component for HTMX, answering `HX-Refresh: true` once the run is over.
- `JobProblems`: the workbook of a file with problems, built from `ImportRow.values` and
  `problems`, with a Problems column and the cells at fault marked.
- `DatasetImports`: past imports, `c-import.job-list`, empty state, and the dialog button.
- `import_chooser(dataset, kind=None)`: the dialog's data, as the prototype builds it, over
  `import_definitions.all(kind)` and `definition.table_schema()`.

The Import buttons: a single type's table links straight to `import/<type>/`. The Samples and
Measurements tabs before a type is chosen, their empty states and past imports render
`c-import.import-menu`. The records tab passes `import_chooser` in its context, built only when
`can_import` holds. The empty overview's Import data button stays the placeholder (issue 698).

## Tests

All new tests are seen to fail for the right reason before the code that makes them pass.
Fixtures (datasets with samples and measurements of every registered type, people at each level,
file builders for the four formats) go in `tests/test_contrib/test_import_export/conftest.py`.

- `test_reader.py`: `TestParse` over the four formats (a comma, a semicolon, a tab, an Excel
  and an OpenDocument file give the same headings and rows), the first sheet only, a blank first
  line, a file with no headings, no rows, over 50,000 rows and over 20 MB, a file of another
  format, `TestEncoding` for UTF-8 with and without a byte order mark and for cp1252.
- `test_matching.py`: `TestNormalise`, `TestMatchHeading` (name, label, label without unit,
  alias, case, spaces, punctuation), `TestMatchColumns` (two headings for one column),
  `TestMappingProblems` (a column a new record needs, two headings for one, update with no
  identifier) and `TestMappingWarnings` (no identifier while adding and updating, latitude without
  longitude), `TestNeedsMatching` (FR-009).
- `test_forms.py`: `TestImportOptionsForm` (defaults, `chosen`, `brief`) and `TestUploadForm`.
- `test_models.py`: `TestImportJob`, `TestImportRow` (status helpers, `writes`, ordering,
  cascade on dataset deletion).
- `test_resources.py` (rewritten): `TestRecordLookup` (portal ID, then Local ID within the
  dataset, never name, a portal ID of another type needs changes, a portal ID of another dataset
  is left out with the measurement note), `TestModes` (both, add, update), `TestEmptyCells`,
  `TestFieldProblems` (a row with no location column reports every field problem; the same row
  with location columns reports them too), `TestDecimalComma`, `TestMeasurementSample` (portal ID of
  a visible sample in any dataset, Local ID and a unique name in this dataset only, a shared
  name, an invisible sample), `TestSampleCache` (a file of 300 rows over three samples costs three
  lookups), `TestChangedCells`, and `TestEveryRegisteredType` (every registered sample and
  measurement type imports a file, SC-006).
- `test_runner.py`: `TestCheck` (writes nothing to the dataset, keeps every outcome, duplicate
  keys, progress), `TestPerform` (writes what the check showed, one transaction, the second
  of two imports re-checks against the first's rows, a changed dataset returns to the check and saves
  nothing, a deleted record does the same), `TestFileDeleted`, and `TestRoundTrip` (a file exported
  from a records table and imported back shows every row unchanged, SC-001).
- `test_undo.py`: `TestDigest`, `TestConflicts` (an edit by `save`, a queryset `update()` that
  skips `modified`, a deleted record, a measurement added to an added sample, a person without the
  change permission), `TestUndo` (added deleted, changed restored, one transaction, nothing changed
  when refused, SC-003).
- `test_tasks.py`: `TestStart` (queues on commit, runs inline with no broker), `TestDiscardStale`
  (30 days, the file deleted, the rows kept).
- `test_plugins.py`: `TestPermission` (view-only person, a visitor and a person of another dataset
  get a 404 on every address, no Import button), `TestImportStart`, `TestUpload` (a refused file
  records no job; a clean file goes to the check; an unmatched heading goes to matching),
  `TestJobColumns`, `TestJobDetail` (rows by outcome a page at a time, the actions,
  a double POST starts one task), `TestJobStatus`, `TestJobProblems` (the workbook carries each
  problem beside its row), `TestPastImports`, `TestChooser` (samples only, measurements only, both).
- `tests/test_utils/test_location_resources.py` (or the file that already tests the mixin):
  `TestImportInstance` for FR-017.
- `tests/test_registry/`: the tests that name `get_resource_class` or `resource_class` are
  removed or rewritten with the component. `tests/test_templates/test_import_menu.py`,
  `test_import_components.py`: each component renders the elements its states need (one link per
  type, the modal's id, the steps' current mark, the progress component's `hx-` attributes).
  `tests/test_contrib/test_collections/test_views.py` (additions): `TestImportOnPages`.

A test of a template or page output is mutation-checked at S5: delete the markup, flip the
condition, return the empty value.

## Pages checked in a browser

At S5, `forge browser-check` over the import page of a sample type and of a measurement type,
column matching, a check that needs changes, ready to import, imported, undone, past imports, the
Samples tab with Export and Import and the empty dataset's tab, at 390 and 1280 wide, with data
seeded for each state. A script drives once in headless Chrome: upload through the file input,
match a column, start an import and watch progress become the outcome, open the dialog from a tab,
close it with Escape.

## Specifications and documents edited

- `CHANGELOG.md`: "Added" for the import, "Removed" for `resource_class`, `get_resource_class()`
  and the unused import views.
- `docs/developers/reference/records-import.md` (new, beside `records-export.md`): the formats and
  limits, the options, how rows find records, the outcomes, undo, the retention rule, the periodic
  task. `docs/developers/index.md` lists it.
- `docs/developers/how-to/import-and-export-locations.md`, `reference/model-configuration.md`,
  `docs/contributing/registry-system.md`: the resource component is gone.
- `CONTEXT.md`: Import, Import definition (if absent), Local ID (D14).
- `docs/adr/`: the decisions that meet the bar at S5 (a row per outcome; a digest per touched
  record), numbered at the push for the merge gate.
- `docs/ROADMAP.md`: R21's status, derived at the merge gate.
- `specs/041-records-import/spec.md` is not edited by this build. D20 reads FR-026's "as the
  portal refuses it by hand" as the change permission alone and is reported at the merge gate.
