# Prototype: importing and exporting samples and measurements

Branch `prototype-import-export`, never merged. Record: https://github.com/FAIR-DM/fairdm/issues/692

Seed: `DJANGO_ENV=development python manage.py seed_import_export_prototype`, then sign in as
`regular.user@example.com` (a dataset filled by imports, with every state of an import) or
`regular.user2@example.com` (an empty dataset). Password `password`.

## The features

1. **Export from any records table.** Anyone who can see a records table (a dataset's, project's or
   contributor's Samples and Measurements tabs, and the portal-wide listings) downloads its rows as
   CSV, Excel, OpenDocument, TSV or JSON: the rows the filters show, or all of them. The file has
   exactly the columns an import reads, with the portal ID first.
   Screens: the **Export** menu on `/datasets/<uuid>/samples/<type>/` and `/collections/samples/<type>/`.
   Owns no models. Depends on the column model (feature 2).
2. **The column model and guide of a type** (the shared foundation). Every registered sample and
   measurement type gets its columns worked out from its registration: identifiers, name, sample
   (measurements), its own fields, status and the four location columns. Each column knows its
   heading, label, other recognised headings, type, unit, range, allowed values, whether a new
   record needs it, and an example. Shown as the guide on the import page, written into the Excel
   template and export, and published as a Frictionless Table Schema.
   Screens: "The columns of a … file" on `/datasets/<uuid>/import/<type>/`.
3. **Import a file into a dataset.** A person who may change a dataset picks a type, uploads a file,
   matches its columns, sees what every row would do, imports it whole, and can undo it.
   Screens: the dialog of types (no page of its own), `/import/<type>/` (file, options, guide,
   templates), `/imports/<job>/columns/` (match columns), `/imports/<job>/` (check, import, undo),
   `/imports/` (past imports). Owns `ImportJob`. Depends on feature 2. Build after feature 1.

Where Import starts: a single type's table (`/samples/<type>/`) links straight to that type's
import page. Every other Import button opens one dialog listing the types, each linking to its
import page: the Samples or Measurements tab before a type is chosen, and their empty states, list
only that kind. The empty dataset overview's **Import data** button (currently a disabled
placeholder on `main`, resolve work) and **Import a file** on past imports list both kinds. There
is no page for choosing a type.

## How an import works

- Rows find their record by portal ID, then by Local ID within the dataset, never by name. A row
  with neither adds a record. A portal ID of another type is refused. So is a portal ID from another
  dataset, whoever owns it: an import adds and changes only its own dataset's records, and never
  offers to add a copy, since copies of copies lose where the data came from. For a measurement
  the message points to the existing way to use another dataset's records: a measurement's
  `sample` column may name any sample the person can see.
- Modes: add and update (default), only add, only update. Empty cells keep the stored value
  (default) or clear it.
- Matching: headings match field name, label, the label without its unit, and listed aliases,
  ignoring case, spaces and punctuation. A file whose every heading matches and that needs nothing
  skips the matching page.
- The check runs `Resource.import_data(dry_run=True)` in Celery and keeps every row's outcome: new,
  changes (each value old and new), unchanged, left out (with the reason), needs changes (each
  problem with its column). Two rows pointing at the same record are refused.
- A file with any problem cannot be imported. The person downloads it back with a Problems column
  and the bad cells marked.
- The import re-runs the file for real in Celery, inside a transaction, and keeps the previous
  values of what it changed. Undo deletes what it added and restores what it changed, and is
  refused once any of those records has been edited since, or a sample it added has measurements.

## The shared pieces

| Piece | Where in the prototype | What it becomes |
|---|---|---|
| Import definition lookup (`ImportDefinition`, `get_definition`, `register`) | `fairdm/contrib/tabular/definitions.py` | The one place every import page, the export menu and the import record find a file's columns, resource, formats and export rows, by name. FairDM builds one per registered type, named after it. `register` lets a project add its own; nothing uses that yet. Built by feature 2, before anything else reads columns |
| Column model (`Column`, `TableSchema`, `schema_for`) | `fairdm/contrib/tabular/schema.py` | Part of the registry: a `ModelConfiguration.get_table_schema()` next to `get_resource_class()`, built by feature 2 |
| Cell widgets (number, date, boolean, concept, sample, quantity, choice) | `resources.py` top half | import-export widgets in `fairdm/contrib/import_export/widgets.py`, feature 2 |
| Dataset-bound resource (matching, modes, empty cells, change list) | `resources.py` `FairDMRecordResource`, `build_resource` | Replaces `BaseFairDMResource` and the registry's `ResourceFactory`, feature 3 |
| Export menu and `?export=` handling | `mixins.py` `RecordTransferMixin`, `partials/table_actions.html` | A mixin on `DataTableView`, feature 1; the menu a Cotton component |
| Step bar, panels, tags, badges, job list | `templates/tabular/partials/*.html`, `tabular.css` | Cotton components under `cotton/import/`, feature 3 |
| Column guide | `partials/guide.html` | Cotton component, feature 2 |
| Excel workbook writer (data, guide, allowed lists) | `exports.py` `workbook` | Feature 1, reused by the template download in feature 3 |

What already exists: django-import-export gives dry runs, row results and diffs, and is what
the import is built on. tablib reads ODS. openpyxl writes the workbooks.

## Duplication to remove

- `engine.py` and `resources.py` both know the location column names.
- Status-to-title maps in `plugins.py` and status labels in `models.py`.
- Tile labels in `plugins.py` and badge labels in `job.html`.

## The look

| File | Ported by | Lands in `main` as |
|---|---|---|
| `fairdm/contrib/tabular/static/tabular/tabular.css` | features 1–3 (each its part) | FairDM's stylesheet, `tx-` classes renamed to the house prefix |
| `static/tabular/tabular.js` | features 1 and 3 | FairDM's scripts |
| `templates/tabular/partials/table_actions.html` | 1 | Cotton component in the records table title row |
| `templates/tabular/partials/guide.html` | 2 | Cotton component |
| `templates/cotton/tabular/import_menu.html` (the Import button and its dialog of types, on `c-mvp.modal`) | 3 | Cotton component |
| `start.html`, `columns.html`, `job.html`, `history.html`, `partials/steps.html`, `partials/job_list.html`, `partials/progress.html` | 3 | The import pages |
| `fairdm/templates/record_lists/records.html` (actions block, empty-state button), `collections/listing.html` | 1 and 3 | Same files on `main` |

Screens to compare, at 390 and 1400 wide, signed in as `regular.user` unless named:

- Samples tab with Export and Import: `/datasets/<seeded>/samples/soilsample/`
- Export menu open, with a search active: same, `?q=peat`
- Dialog of types: Import on `/datasets/<seeded>/samples/` and `/measurements/`; as `regular.user2`,
  **Import data** on the empty dataset's overview
- Import page and guide: `/datasets/<seeded>/import/soilsample/`
- Column matching: upload `static/tabular/examples/soil-samples-field-headings.xlsx`
- Needs changes: the `xrf-batch-2.csv` import
- Ready to import: the `soil-samples-autumn.csv` import
- Imported, undoable: the `soil-ph-corrections.xlsx` import
- Imported, no longer undoable: `soil-samples-spring.csv`, `rock-samples-field-sheet.csv`
- Undone: `water-test.csv`
- Past imports: `/datasets/<seeded>/imports/`
- Empty dataset, as `regular.user2`: its overview and Samples tab

## The data model

`ImportJob` (feature 3): dataset, the name of the import definition it was read with, who and when, the stored file, its headings and
sample values, the column matches, mode and empty-cell rule, status, per-row outcome (JSON), counts,
what undo restores, who undid it and when.

## Decisions

See the issue.

## Faked or skipped

- The stored file is never deleted. A retention rule is needed.
- Row outcomes are stored as JSON on the job. A 50,000-row file makes a large row; the rebuild may
  want a row table or a file.
- Progress is kept in the cache and polled every second.
- No import of keywords, tags, descriptions, dates, identifiers or contributors.
- Only one type per file. Several related tables in one file (samples and their measurements) is
  roadmap's next step.
- No accessibility audit beyond semantic markup and labels: the guide and match tables use ARIA
  table roles on divs, which the rebuild should check or replace with real tables.
- Undo checks `modified` timestamps only.
- A dataset can't reference another dataset's samples. A sample belongs to exactly one dataset
  (`Sample.dataset`), so referencing them is a change to the core data model, outside this
  prototype. Only measurements can point at another dataset's samples.
- The existing `LocatedResourceMixin.import_instance` on `main` drops every field's error when a
  row has no location columns. The prototype works around it; the rebuild fixes it.

## What it replaces

- `fairdm/contrib/import_export/` views, forms, templates and `BaseFairDMResource` (never routed).
- The registry's `ResourceFactory`, whose generated resources omit identifiers and, for some
  types, the sample. Nothing stored is dropped.
