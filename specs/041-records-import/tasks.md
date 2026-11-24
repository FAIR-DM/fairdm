# Tasks: import a spreadsheet of samples or measurements into a dataset

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md),
[decisions.md](decisions.md)

**Tests first**: in every group the test tasks come first, and each is seen to fail for the right
reason before the code that makes it pass is written. Wording and appearance get no tests.

**How tests run**: from the worktree's own virtual environment against the shared test PostGIS
(`. ../fairdm-041-env.sh; .venv/bin/python -m pytest <path> -n0`).

**Standards in every task**: no leading-underscore names, line length 88, no compatibility
aliases, Cotton components and never `{% include %}`, a Google-style docstring on every new
public name.

**Format**: `[ID] [Story] Description`.

## Phase 1: Foundational

### Group 1

- [x] T001 [US1] Tests: `TestImportInstance` for `LocatedResourceMixin` in the test module that
  covers `fairdm/utils/location/resources.py` (a row with an invalid field and no location column
  is refused with that field's problem; the same with location columns reports the field's and the
  location's). The module is `tests/test_utils/test_location/test_resources.py`.
- [ ] T002 [US1] Fix `LocatedResourceMixin.import_instance` in `fairdm/utils/location/resources.py`
  as plan.md "Modules" describes. T001 goes green.

### Group 2

- [ ] T003 [US1] Remove the unused import module pieces: `BaseImportExportView`, `DataImportView`,
  `DataExportView` and `UploadForm` from `fairdm/contrib/import_export/views.py`; `ImportForm` and
  `ExportForm` from `forms.py` (the file is rewritten in Group 4); `BaseFairDMResource`,
  `SampleResource`, `MeasurementResource` and the old `SampleWidget` from `resources.py` (the file
  keeps only what Group 5 replaces it with, so for now an empty module with its docstring); the
  templates `import_export/import.html` and `cotton/import_export/**`. Remove the tests that
  covered them. `DatasetPublishConfirm`, `DatasetPackageDownloadView`, `MetadataDownloadView`,
  `TableSchemaView` and the package builder stay.
- [ ] T004 [US1] Tests first, then code: `build_export_for_datatype` in `utils.py` writes through
  `TableExport` and keeps its signature (a test in `test_utils.py` that it returns the rows'
  headings and cells for a registered type in `csv`).
- [ ] T005 [US1] Remove the registry's `resource` component, `ResourceFactory`, `resource_class`
  and `get_resource_class()` (D19). Rewrite or delete the registry tests that name them. Edit
  `docs/developers/how-to/import-and-export-locations.md`,
  `docs/developers/reference/model-configuration.md`, `docs/contributing/registry-system.md` and
  `docs/developers/reference/location-fields.md` (which names `BaseFairDMResource`). Name
  `resource_fields` explicitly in the registry's `_OVERRIDABLE` and `_field_lists` so the column
  model still reads it, with a test (DR-010). `tests/test_registry/test_config.py` lists
  `get_resource_class` and is edited.

### Group 3

- [ ] T006 [US1] Tests: `TestImportJob` and `TestImportRow` in
  `tests/test_contrib/test_import_export/test_models.py`, as plan.md "Tests" lists.
- [ ] T007 [US1] `fairdm/contrib/import_export/models.py` (`ImportJob`, `ImportRow`) and
  `migrations/0001_initial.py` (squashed to one file), `verbose_name`, `help_text` and the index on every
  field as plan.md "Data model" describes, the `post_delete` receiver that deletes the file, and
  `ImportJobFactory` and `ImportRowFactory` in `tests/factories.py` (DR-017, DR-018). T006
  goes green. `makemigrations --check` is clean.
- [ ] T008 [US1] Tests: `TestImportOptionsForm` and `TestUploadForm` in
  `tests/test_contrib/test_import_export/test_forms.py`.
- [ ] T009 [US1] `fairdm/contrib/import_export/forms.py`: `ImportOptionsForm` (with
  `CardSelect`, ported from the prototype's `forms.py`) and `UploadForm`. T008 goes green.

## Phase 2: User Story 1, a person fills a dataset from a spreadsheet of one type (P1)

### Group 4

- [ ] T010 [US1] Tests: `test_reader.py` and `test_matching.py`, as plan.md "Tests" lists.
- [ ] T011 [US1] `reader.py` (`FileProblem` and `FileReader`: limits, `file_format`, `read_grid`, `parse`; OpenDocument
  read with odfpy directly) rebuilt from the prototype's `engine.py` reading part, and `matching.py`
  (`HeadingMatcher`: `normalise`, `match`, `match_columns`, `problems`, `warnings`,
  `needs_matching`). T010 goes green.

### Group 5

- [ ] T012 [US1] Tests: `test_resources.py` (rewritten) and the sample cache test in
  `test_widgets.py`, as plan.md "Tests" lists.
- [ ] T013 [US1] `resources.py` (`RowProblem`, `RecordResource`, `changed_cells`,
  `build_resource`), `ImportDefinition.resource()` in `definitions.py`, the per-file cache in
  `SampleCellWidget`, as plan.md "Modules" describes, rebuilt from the prototype's `resources.py`.
  T012 goes green.

### Group 6

- [ ] T014 [US1] Tests: `test_runner.py` (check, perform, divergence, lock, file deletion,
  round trip) and `test_tasks.py` `TestStart`.
- [ ] T015 [US1] `runner.py` (`ImportRun`: `run`, `check`, `perform`, `progress`) and `tasks.py`
  (`check_job` and `import_job` with their own time limits, `start` with no inline fallback), as plan.md "The check and the import" describes. T014
  goes green.

### Group 7

- [ ] T016 [US1] Tests: `test_plugins.py` `TestPermission`, `TestImportStart`, `TestUpload`,
  `TestJobColumns`, `TestJobDetail`, `TestJobStatus`, `TestJobProblems`, `TestChooser`.
- [ ] T017 [US1] `plugins.py` (the pages), the templates under
  `fairdm/contrib/import_export/templates/import_export/` and the Cotton components under
  `fairdm/templates/cotton/import/` (`steps`, `progress`, `panel`, `tag`, `outcome_badge`,
  `job_list`), ported from the prototype as plan.md "What is ported" lists. Exports
  `template_response`-style functions beside `TableExport` for the template download and the
  problems workbook. T016 goes green except the placement tests.
- [ ] T018 [US1] `fairdm/static/css/fairdm.css` ("Import and export" section, the import part of
  the prototype's `tabular.css`, `tx-` renamed `ie-`) and `fairdm/static/js/import.js` linked from
  `base.html` with `defer`. No test.

### Group 8

- [ ] T019 [US1] Tests: `test_import_menu.py` (the component), `TestImportOnPages` in
  `tests/test_contrib/test_collections/test_views.py` (a single type's table links straight to its
  import page; a tab before a type is chosen and an empty tab open the dialog; a person who may
  not import sees no button; the dialog lists samples only, measurements only or both).
- [ ] T020 [US1] `cotton/import/import_menu.html`, its placement in `record_lists/records.html`
  and `collections/listing.html` beside the Export menu, the records tab's `import_chooser`
  context. T019 and T016's placement tests go green.

## Phase 3: User Story 2, a person looks back over a dataset's imports and undoes one (P2)

### Group 9

- [ ] T021 [US2] Tests: `test_undo.py` and `TestDiscardStale` in `test_tasks.py`, and the undo and
  past-imports tests in `test_plugins.py` (`TestPastImports`, undo refused naming the records,
  undo done).
- [ ] T022 [US2] `undo.py` (`ImportUndo`), the `undo` action and conflicts on the job page, `DatasetImports`,
  `discard_stale_jobs` and its periodic task registered in `apps.py`, as plan.md "Undo" describes.
  T021 goes green.

## Phase 4: Documents

### Group 10

- [ ] T023 [US1] Documentation: `docs/developers/reference/records-import.md`, the `index.md`
  entry, the `CHANGELOG.md` lines and the `CONTEXT.md` glossary entries, as plan.md
  "Specifications and documents edited" describes.

## Phase 5: Convergence

(Tasks are added here by the converge and review stages.)
