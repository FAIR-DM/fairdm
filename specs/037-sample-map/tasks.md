# Tasks: map where a project's or dataset's samples come from

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md),
[decisions.md](decisions.md)

**Tests first**: in every group the test tasks come first, and each is seen to fail before the code
that makes it pass is written. Wording and appearance get no tests.

**How tests run**: from the worktree's own virtual environment against the shared test PostGIS,
with the environment in `/home/sam/projects/worktrees/fairdm-037-env.sh` sourced first.

**Format**: `[ID] [Story] Description`.

## Phase 1: User Story 1, a reader sees where a project's or dataset's samples come from (P1)

### Group 1

- [x] T001 [US1] Tests: `TestDescribeCoverage` in `tests/test_core/test_overview.py`, and
  `TestGetSamplePoints` and `TestGetSampleMap` in `tests/test_core/test_plugins.py`, as plan.md
  "Tests" describes.
- [x] T002 [US1] `describe_coverage` in `fairdm/core/overview.py`, and `get_sample_points` and
  `get_sample_map` on `RecordOverviewPlugin` in `fairdm/core/plugins.py`, as plan.md "The helpers"
  describes. T001 goes green.
- [x] T003 [US1] Tests: `TestOverviewSampleMap` in `tests/test_core/test_project/test_plugins.py`
  and `tests/test_core/test_dataset/test_plugins.py`, and `TestSamplePoints` in
  `tests/test_core/test_plugins.py`, as plan.md "Tests" describes.
- [x] T004 [US1] `SamplePoints` in `fairdm/core/plugins.py`, and on the project and dataset
  `Overview`: `get_map_samples`, `sample_map` and `has_map` in the context, and
  `get_extra_views`, as plan.md "The plugins" and "The address" describe. T003 goes green.

### Group 2

- [x] T005 [US1] Tests: `TestCoverage` in `tests/test_templates/test_overview_components.py`, and
  the project and dataset page tests in `tests/test_templates/test_overview_page.py`, as plan.md
  "Tests" lists.
- [x] T006 [US1] `fairdm/templates/cotton/overview/coverage.html`, ported from the prototype, and
  the `overview.map` block in `fairdm/core/project/templates/project/project_detail.html` and
  `fairdm/core/dataset/templates/dataset/dataset_detail.html`, as plan.md "The panel" describes.
  T005 goes green.
- [x] T007 [US1] `fairdm/static/js/overview.js`: `startSampleMap` and its branch in `initMaps`,
  ported from the prototype's `initMaps`, as plan.md "The script" describes. No test (plan.md
  "What is not built").
- [x] T008 [US1] `fairdm/static/css/fairdm.css`: the legend and popup rules, as plan.md "The look"
  describes. No test.

### Group 3

- [x] T009 [US1] Edit `specs/018-overview-pages/spec.md` and `specs/030-geospatial-locations/spec.md`
  as plan.md "Specifications edited" describes.
- [x] T010 [US1] Documentation and `CHANGELOG.md`, as plan.md "Documentation" describes.

### Found after planning

- [x] T011 [US1] Wrap the lines group 1 added to 88 characters.
