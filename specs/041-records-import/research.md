# Research: import a spreadsheet of samples or measurements into a dataset

## Assumptions checked

Each assumption the specification makes about what already works, checked against `main` at
`eed6473e` with its locked dependencies installed.

- **The modal component exists.** django-mvp 0.36.1 is installed and ships
  `mvp/templates/cotton/mvp/modal.html`, so `c-mvp.modal` is available for the dialog of types.
- **The card choice widget exists.** django-mvp-forms 0.11.0 is installed and
  `mvp_forms/widgets.py` defines `CardSelect` (a `RadioSelect` drawn as cards with an icon, a
  description and a mark), for the import options.
- **The import permission exists at the edit level.** `fairdm/contrib/contributors/access.py`
  maps `import_data` to `ContributionLevel.EDIT`, so a person with the edit level on a dataset
  holds `dataset.import_data`.
- **Both types carry a Local ID.** `Sample.local_id` (`fairdm/core/sample/models.py`) and
  `Measurement.local_id` (migration `measurement/0008_measurement_local_id`) both exist.
- **The reading libraries are installed.** django-import-export, tablib with its `ods` and `xlsx`
  extras (odfpy and openpyxl), Celery and django-celery-beat are dependencies on `main`.
- **The old import module is unreachable.** `fairdm/contrib/import_export/urls.py` registers no
  routes. Its views include `DataImportView`, `DataExportView` and `DatasetPublishConfirm`, and
  `BaseFairDMResource` lives in its `resources.py`. The registry's `ResourceFactory` is in
  `fairdm/registry/factories.py` and is the default for `resource_class` in
  `fairdm/registry/config.py`.
- **The location defect is real.** `LocatedResourceMixin.import_instance`
  (`fairdm/utils/location/resources.py`) catches the field errors into `errors`, then returns
  when no location column is in the row, before `raise ValidationError(errors)`. A row with
  invalid fields and no location columns is therefore reported valid. The fix is a requirement
  of this feature (FR-017).

## What main holds after the two earlier features

Read at `4c32f3e7`, the merge of the export.

- **The import definition lookup is built.** `fairdm/contrib/import_export/definitions.py`:
  `ImportDefinition` (`name`, `model`, `formats`, `kind`, `table_schema()`), `import_definitions`
  with `all(kind)`, `get` and `register`, and the names `get_definition` and `register`. It has no
  resource method yet, which this feature adds.
- **The column model is built.** `schema.py`: `Column` (with `widget(dataset, user)`,
  `importable`), `TableSchema` (`importable`, `required`, `headings`, `get`, `groups`, `name`,
  `singular`, `slug`) and `ModelConfiguration.get_table_schema()`. It has no heading matcher: the
  prototype's `schema.match(heading)` is this feature's to add (D15).
- **The cell widgets are built.** `widgets.py`: `CellWidget` and one subclass per kind, `widget_for`
  and `render_cell`. `SampleCellWidget` looks up each cell on its own (the carried-over review
  finding).
- **The export is built.** `exports.py` `TableExport(schema)` with `rows`, `response` and
  `workbook(rows=())`; `mixins.py` `RecordExportMixin` on `DataTableView`; the menu component
  `cotton/import/export_menu.html`; the guide `cotton/import/guide.html`; `TableSchemaView` at
  `table-schemas/<slug:name>/`.
- **The old import module is still there.** `views.py` holds `BaseImportExportView`,
  `DataImportView`, `DataExportView` beside `DatasetPublishConfirm`, `DatasetPackageDownloadView`,
  `MetadataDownloadView` and `TableSchemaView`. `forms.py` holds `ImportForm` and `ExportForm`.
  `resources.py` holds `BaseFairDMResource`, `SampleResource` and `MeasurementResource`. The
  templates `import_export/import.html` and `cotton/import_export/**` serve the unrouted views.
  `utils.build_export_for_datatype` still builds its resource from
  `ModelConfiguration.get_resource_class()`, so removing the registry's resource component means
  rewriting it to write through `TableExport`.
- **The registry's resource component.** `ModelConfiguration` has `resource_fields` (read by the
  column model, so it stays), `resource_class` and `get_resource_class()`, and `COMPONENTS` holds the
  `resource` component with `ResourceFactory`. `docs/developers/how-to/import-and-export-locations.md`
  and `reference/model-configuration.md` document `resource_class`.
- **The app label is `fairdm_import_export`.** The third-party `import_export` app owns the plain
  label, so the new models live in `fairdm.contrib.import_export` under the label already set, and
  the migration is `fairdm_import_export/0001_initial`.
- **Scheduled work.** `fairdm/backups/signals.py` and `fairdm/contrib/contributors/receivers.py`
  create a `django_celery_beat` `PeriodicTask` on `post_migrate`. The 30-day discard is
  registered the same way. Celery settings are in `fairdm/conf/settings/celery.py`, the cache is
  Redis through `CACHES` (`fairdm/conf/settings/cache.py`).
- **Permissions.** Importing is `dataset.import_data` (the edit level). Deleting a sample or
  measurement by hand is `delete_<model>`, which needs the manage level. The portal holds no rule
  about a dataset's published state that blocks a change, so D8's "as the portal refuses by hand"
  has only the permission to read (D20).
- **Link to a record.** A record's permalink is its portal ID at the root (ADR 0042), so a stored
  portal ID is enough to link a row's record.

## What already exists

One line per piece of new code, the first place the search stopped.

- File reading (CSV with a sniffed delimiter, TSV, Excel, OpenDocument): tablib reads CSV, TSV
  and Excel (`tablib.Dataset().load` with `openpyxl`) and `csv.Sniffer` reads the delimiter.
  tablib's OpenDocument reader ignores repeated rows and cells and raises on a workbook with more
  than one table, so OpenDocument is read with `odfpy` directly (first table only, repeats
  expanded and capped).
  New code: the size and row limits, the first-sheet rule and the heading row, which are this
  feature's rules and not a package's.
- Dry run, row results, diffs, row-level errors: `django-import-export` `Resource.import_data`
  (a maintained package). New code: the dataset-bound resource's lookup, modes and empty-cell rule.
- Background run: Celery, already a dependency and run by the portal's worker.
- Progress polling and a page that refreshes itself: HTMX, loaded from a CDN in `base.html`
  (`hx-get` with `hx-trigger="every 1s"`, and the `HX-Refresh` response header). New code: a few
  lines in a status view. No polling script of our own.
- Progress storage: the Redis cache the portal already runs. A database column cannot carry it,
  because the check's writes to the import record happen outside the dry run's rolled-back
  transaction only at the end.
- The dialog: `c-mvp.modal` from django-mvp 0.36.1.
- The option cards: `CardSelect` from django-mvp-forms 0.11.0.
- The Excel template and the problems workbook: `TableExport.workbook()` and openpyxl.
- Scheduled discard: `django_celery_beat` `PeriodicTask`, created as the portal's other scheduled
  tasks are.
- Row outcomes, undo data, change detection: a table of rows (new), a digest of each touched
  record's stored values (new, `hashlib` from the standard library).

## Timing of a 50,000-row import

One file of 50,000 new records of ICP-MS measurements, the demo portal's widest type at 18 columns, every row naming one existing sample, on the shared test PostGIS in a development worktree (one process, no other load):

- The check (a dry run that saves and rolls back every record) took 668 seconds.
- The import took 768 seconds, including the second run of the resource, the comparison with the check's rows, and reading every written record back in chunks of 500 for its digest.

The tasks' soft limit is 2,400 seconds (a little over three times the longer run) and the hard limit is 2,700 seconds, so a slower worker or a busier database still finishes, and a file that is stuck is stopped within 45 minutes. The same file made only of rows that fail checking (50,000 problems) took 201 seconds to check.
