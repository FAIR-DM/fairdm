# Tasks: the columns of a sample or measurement type

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md),
[decisions.md](decisions.md)

**Tests first**: in every group the test tasks come first, and each is seen to fail for the right
reason before the code that makes it pass is written. Wording and appearance get no tests.

**How tests run**: from the worktree's own virtual environment against the shared test PostGIS
(`. ../fairdm-039-env.sh; .venv/bin/python -m pytest <path> -n0`).

**Format**: `[ID] [Story] Description`.

## Phase 1: Foundational

### Group 1

- [ ] T001 [US1] Add `frictionless` (>=5,<6) to the `dev` dependency group of `pyproject.toml`, run
  `uv lock` and `uv sync --group dev --locked`, and check `uv run pre-commit run deptry --all-files`
  stays green.
- [ ] T002 [US1] `fairdm/utils/location/resources.py`: add `LOCATION_COLUMNS` and build
  `location_fields()` from it, as plan.md "The column model" describes. The existing location tests
  stay green.

## Phase 2: User Story 1, a developer asks a type for its columns (P1)

### Group 2

- [ ] T003 [US1] Tests: `TestColumnOrder`, `TestResourceFieldsRule`, `TestColumnContents`,
  `TestExamples`, `TestLocationColumns` and `TestPortalConfig` in
  `tests/test_contrib/test_import_export/test_schema.py`, and `TestGetTableSchema` in
  `tests/test_registry/test_config.py`, as plan.md "Tests" describes.
- [ ] T004 [US1] `fairdm/contrib/import_export/schema.py` (`Column`, `TableSchema`,
  `build_table_schema`, `kind_of`, `example_for`) and `ModelConfiguration.get_table_schema()`, as
  plan.md "The column model" describes, ported from the prototype's `schema.py`. T003 goes green.

### Group 3

- [ ] T005 [US1] Tests: `TestRoundTrip`, `TestRefusals`, `TestConceptWidget`, `TestSampleWidget` and
  `TestQuantityWidget` in `tests/test_contrib/test_import_export/test_widgets.py`, as plan.md
  "Tests" describes.
- [ ] T006 [US1] `fairdm/contrib/import_export/widgets.py` (the widgets, `widget_for`,
  `render_cell`) and `Column.widget()`, as plan.md "The widgets" describes, ported from the
  prototype's `resources.py`. T005 goes green.

### Group 4

- [ ] T007 [US1] Tests: `TestLookup` and `TestRegister` in
  `tests/test_contrib/test_import_export/test_definitions.py`, as plan.md "Tests" describes.
- [ ] T008 [US1] `fairdm/contrib/import_export/definitions.py`, as plan.md "The import definitions"
  describes. T007 goes green.

### Group 5

- [ ] T009 [US1] Tests: `TestGuideComponent` in `tests/test_templates/test_import_guide.py`, as
  plan.md "Tests" describes.
- [ ] T010 [US1] `fairdm/templates/cotton/import/guide.html`, ported from the prototype's
  `partials/guide.html` with native table elements and explicit roles (decision D7), as plan.md
  "The column guide" describes. T009 goes green. Then read Chrome's accessibility tree for the guide
  rendered for `soilsample` at 390 and 1400 wide, confirm one table with column headers per group,
  and record the result as a decision in `decisions.md` (SC-005).
- [ ] T011 [US1] `fairdm/static/css/fairdm.css`: the `ie-` section, ported from the prototype's
  `tabular.css` as plan.md "What is ported" lists. No test.

## Phase 3: User Story 2, a person downloads a type's Table Schema (P2)

### Group 6

- [ ] T012 [US2] Tests: `TestTableSchemaView` in
  `tests/test_contrib/test_import_export/test_views.py`, and `TestFrictionlessValidation` in
  `tests/test_contrib/test_import_export/test_schema.py`, as plan.md "Tests" describes.
- [ ] T013 [US2] `Column.as_frictionless()`, `TableSchema.as_frictionless()`, `TableSchemaView` and
  the `table_schema` route, as plan.md "The Table Schema" describes. T012 goes green.

## Phase 4: Documents

### Group 7

- [ ] T014 [US1] Documentation: a developer reference page and a how-to, the `CHANGELOG.md` line,
  and `CONTEXT.md` glossary entries for table schema, column, import definition and column guide,
  as plan.md "Specifications and documents edited" describes.
