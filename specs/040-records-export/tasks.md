# Tasks: export the rows of any records table

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md),
[decisions.md](decisions.md)

**Tests first**: in every group the test tasks come first, and each is seen to fail for the right
reason before the code that makes it pass is written. Wording and appearance get no tests.

**How tests run**: from the worktree's own virtual environment against the shared test PostGIS
(`. ../fairdm-040-env.sh; .venv/bin/python -m pytest <path> -n0`).

**Format**: `[ID] [Story] Description`.

## Phase 1: Foundational

### Group 1

- [ ] T001 [US1] Add `openpyxl (>=3.1,<4.0)` to `[project] dependencies` in `pyproject.toml`, run
  `uv lock` and `uv sync --group dev --locked`, and check `uv run pre-commit run deptry --all-files`
  stays green.

## Phase 2: User Story 1, a person downloads the rows of a records table (P1)

### Group 2

- [x] T002 [US1] Tests: `TestExportResponse`, `TestExportOrder`, `TestSampleName` and `TestWorkbook`
  in `tests/test_contrib/test_import_export/test_exports.py`, as plan.md "Tests" describes.
- [x] T003 [US1] `fairdm/contrib/import_export/exports.py` (`ExportFormat`, `EXPORT_FORMATS`,
  `format_for`, the class `TableExport`), as plan.md "The writer"
  describes, rebuilt from the prototype's `exports.py`. T002 goes green.

### Group 3

- [x] T004 [US1] Tests: `TestExportRequest`, `TestExportVisibility`, `TestExportStability`,
  `TestExportMenuContext` and `TestFileName` and `TestExportQueries` in
  `tests/test_contrib/test_import_export/test_mixins.py` (fixtures in that directory's `conftest.py`), and `TestExportOnPages` in
  `tests/test_contrib/test_collections/test_views.py`, as plan.md "Tests" describes.
- [x] T005 [US1] `fairdm/contrib/import_export/mixins.py` (`RecordExportMixin`) and
  `DataTableView` taking it, as plan.md "The mixin" describes. T004's request, visibility,
  stability and context tests go green. The placement tests wait for T007.

### Group 4

- [ ] T006 [US1] Tests: `TestExportMenuComponent` in `tests/test_templates/test_export_menu.py`,
  as plan.md "Tests" describes.
- [ ] T007 [US1] `fairdm/templates/cotton/import/export_menu.html`, its `page.actions` placement in
  `fairdm/templates/record_lists/records.html` and
  `fairdm/contrib/collections/templates/collections/listing.html`, as plan.md "The component and its
  placement" describes, ported from the prototype's `partials/table_actions.html`. T006 and T004's
  placement tests go green.
- [ ] T008 [US1] `fairdm/static/css/fairdm.css` (the `ie-tools` and `ie-menu` rules, ported from the
  prototype's `tabular.css` lines 300-315 with `tx-` renamed `ie-`) and
  `fairdm/static/js/export-menu.js` linked from `fairdm/templates/base.html` with `defer`, as plan.md
  "What is ported" lists. No test.

## Phase 3: Documents

### Group 5

- [ ] T009 [US1] Documentation: the reference page, the `CHANGELOG.md` line and the `CONTEXT.md`
  glossary entry, as plan.md "Specifications and documents edited" describes.
