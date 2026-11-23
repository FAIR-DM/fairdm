# Planning notes: import a spreadsheet of samples or measurements into a dataset

Notes for research and planning. The plan answers each one by name.

## The prototype this feature comes from

Branch `prototype-import-export`, its hand-over document `PROTOTYPE.md` at the branch's root, and
this feature's part of it: feature 3, "Import a file into a dataset". The prototype's record is
https://github.com/FAIR-DM/fairdm/issues/692, and its decisions bind this feature. The branch is
read, never merged and never branched from. The hand-over numbers the features differently:
its feature 2 is https://github.com/FAIR-DM/fairdm/issues/695, its feature 1 is
https://github.com/FAIR-DM/fairdm/issues/696, and this one is built after both.

## The shared pieces this feature builds or reuses

From the hand-over's "The shared pieces", in its words:

| Piece | Where in the prototype | What it becomes |
|---|---|---|
| Import definition lookup (`ImportDefinition`, `get_definition`, `register`) | `fairdm/contrib/tabular/definitions.py` | The one place every import page, the export menu and the import record find a file's columns, resource, formats and export rows, by name. FairDM builds one per registered type, named after it. `register` lets a project add its own; nothing uses that yet. Built by feature 2, before anything else reads columns |
| Column model (`Column`, `TableSchema`, `schema_for`) | `fairdm/contrib/tabular/schema.py` | Part of the registry: a `ModelConfiguration.get_table_schema()` next to `get_resource_class()`, built by feature 2 |
| Cell widgets (number, date, boolean, concept, sample, quantity, choice) | `resources.py` top half | import-export widgets in `fairdm/contrib/import_export/widgets.py`, feature 2 |
| Import options form (what the file may do, what an empty cell means) | `forms.py` `ImportOptionsForm`, drawn with django-mvp-forms' `CardSelect`: with each choice's explanation on the import page, labels alone on column matching | The form behind the options on both pages, feature 3 |
| Dataset-bound resource (matching, modes, empty cells, change list) | `resources.py` `FairDMRecordResource`, `build_resource` | Replaces `BaseFairDMResource` and the registry's `ResourceFactory`, feature 3 |
| Step bar, panels, tags, badges, job list | `templates/tabular/partials/*.html`, `tabular.css` | Cotton components under `cotton/import/`, feature 3 |
| Column guide | `partials/guide.html` | Cotton component, feature 2 |
| Excel workbook writer (data, guide, allowed lists) | `exports.py` `workbook` | Feature 1, reused by the template download in feature 3 |

This feature builds the import options form, the dataset-bound resource and the step bar, panels,
tags, badges and job list. It reuses the import definition lookup, the column model, the cell
widgets and the column guide from https://github.com/FAIR-DM/fairdm/issues/695, and the Excel
workbook writer from https://github.com/FAIR-DM/fairdm/issues/696. The plan cites where each
reused piece landed on `main`.

## The look is ported, never redrawn

From the hand-over's "The look", the files this feature ports and where each lands on `main`.
Class names change from the prototype's `tx-` to the house prefix the two earlier features
settle, so the three use one prefix.

| Prototype file | Lands on `main` as |
|---|---|
| `fairdm/contrib/tabular/templates/cotton/tabular/import_menu.html` (the Import button and its dialog of types, on `c-mvp.modal`) | A Cotton component for the Import button and its dialog |
| `templates/tabular/start.html` | The import page of a type |
| `templates/tabular/columns.html` | The column matching page |
| `templates/tabular/job.html` | The page of one import: check, import, undo |
| `templates/tabular/history.html` | Past imports |
| `templates/tabular/partials/steps.html` | Cotton component under `cotton/import/` (the step bar) |
| `templates/tabular/partials/job_list.html` | Cotton component under `cotton/import/` (the list of imports) |
| `templates/tabular/partials/progress.html` | Cotton component under `cotton/import/` (progress of a running check or import) |
| `fairdm/contrib/tabular/static/tabular/tabular.css` (the import part) | FairDM's stylesheet |
| `static/tabular/tabular.js` (the import part) | FairDM's scripts |
| `fairdm/templates/record_lists/records.html` (the Import button in the actions block, the empty-state button) | The same file on `main` |
| `collections/listing.html` (the Import part, if any) | The same file on `main` |

The plan names each of these. The panels, tags and badges that `job.html` and `columns.html` draw
inline become Cotton components under `cotton/import/` with them. The screens to compare, at 390
and 1400 wide, are the hand-over's list under "The look", from the dialog of types onwards.

## The prototype's skipped parts this feature settles

From the hand-over's "Faked or skipped", the parts marked for feature 3:

- **The stored file is never deleted.** Settled in `decisions.md` D4 and D5: deleted when the
  import finishes, and an unfinished import is discarded after 30 days.
- **Row outcomes are stored as JSON on the job.** "A 50,000-row file makes a large row; the
  rebuild may want a row table or a file." The specification fixes what a person sees
  (`decisions.md` D10). The plan chooses the storage and says why.
- **Progress is kept in the cache and polled every second.** The plan chooses how progress is
  kept and fetched (`decisions.md` D11), and checks what django-mvp or HTMX already offer before
  writing its own.
- **ARIA table roles on divs** in the match table: "the rebuild should check or replace with real
  tables." The column matching page and the rows of a check use real tables where they are
  tables.
- **Undo checks `modified` timestamps only.** Settled in `decisions.md` D7. The plan chooses how a
  change since the import is detected, including a change made without saving the record and a
  deleted record.
- **Another dataset's samples are left out.** "Feature 3 builds the leaving out."
- **`LocatedResourceMixin.import_instance` drops every field's error when a row has no location
  columns.** "The prototype works around it. Feature 3 fixes it on `main`."

## The hand-over's duplication to remove

"`engine.py` and `resources.py` both know the location column names." "Status-to-title maps in
`plugins.py` and status labels in `models.py`." "Tile labels in `plugins.py` and badge labels in
`job.html`." Each has one home on `main`.

## What already exists

"django-import-export gives dry runs, row results and diffs, and is what the import is built on.
tablib reads ODS. openpyxl writes the workbooks." The check and the import queue their work only
once the upload is saved, as the prototype's decision says.

## Removing the old import module's pieces

`BaseImportExportView` in `fairdm/contrib/import_export/views.py` is shared by the import view and
the export view. The plan checks what https://github.com/FAIR-DM/fairdm/issues/696 left there
before removing it, and keeps `DatasetPublishConfirm`.
