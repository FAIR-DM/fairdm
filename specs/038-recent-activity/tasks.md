# Tasks: show recent activity on project and dataset pages

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md),
[decisions.md](decisions.md)

**Tests first**: in every group the test tasks come first, and each is seen to fail before the code
that makes it pass is written. Wording and appearance get no tests.

**How tests run**: from the worktree's own virtual environment against the shared test PostGIS.

**Format**: `[ID] [Story] Description`.

## Phase 1: User Story 1, a reader sees what has happened to a project or dataset lately (P1)

### Group 1

- [x] T001 [US1] Add `django-mvp-community[activity]` and `django-activity-stream` to
  `pyproject.toml` with their deptry entries, lock and sync, install `fairdm.contrib.activity`,
  `mvp_community` and `actstream` in `fairdm/conf/settings/apps.py`, and move the change tracker
  from `BaseModel` to `Project` and `Dataset`, as plan.md "Dependency and settings" describes.
- [x] T002 [US1] Tests: `TestRecordEdits`, `TestRecordPublished`, `TestRecordJoined` and
  `TestRecordingNeverFails` in `tests/test_contrib/test_activity/test_receivers.py`, and
  `TestNoOtherFeed` in `tests/test_contrib/test_activity/test_apps.py`, as plan.md "Tests"
  describes.
- [x] T003 [US1] `fairdm/contrib/activity/` with `apps.py` and `receivers.py`, as plan.md
  "Recording" describes. T002 goes green.

### Group 2

- [x] T004 [US1] Tests: `TestActivityLines` in `tests/test_contrib/test_activity/test_lines.py`, as
  plan.md "Tests" describes.
- [x] T005 [US1] `fairdm/contrib/activity/lines.py`: `Line`, `ActivityLines` and
  `recent_activity`, as plan.md "Gathering" describes. T004 goes green.

### Group 3

- [x] T006 [US1] Tests: `TestActivityPanel` and `TestOverrides` in
  `tests/test_templates/test_activity.py`, the two page checks there, and `TestActivityPage` in
  `tests/test_contrib/test_activity/test_plugins.py`, as plan.md "Tests" describes.
- [x] T007 [US1] The panel, the row override, the `overview.activity` block in both detail
  templates and `activity` in both overview plugins' context, as plan.md "The panel and the
  overrides" describes, ported from the prototype as "What is ported" lists.
- [x] T008 [US1] `fairdm/contrib/activity/plugins.py` and `activity/activity_list.html`, as plan.md
  "The full list" describes. T006 goes green.
- [x] T009 [US1] `fairdm/static/css/fairdm.css`: the `.ov-activity` rules, ported onto the
  package's list inside the panel. No test.

### Group 4

- [x] T010 [US1] Edit `specs/018-overview-pages/spec.md` as plan.md "Specifications edited"
  describes.
- [x] T011 [US1] Documentation and `CHANGELOG.md`, as plan.md "Documentation" describes.

### Found after planning

- [x] T012 [US1] Move `TestNoOtherFeed` to `tests/test_contrib/test_activity/test_apps.py`, the
  module that mirrors the app's configuration.
- [x] T013 [US1] Assert the logged failure on the receivers' own logger, so the test no longer
  depends on log propagation, which another test's logging setup can switch off.
- [x] T014 [US1] A test that a public action of the same kind gives no line, which the mutation pass
  found missing.
- [x] T015 [US1] Wrap the new modules to 88 characters.
- [x] T016 [US1] Give each sentence its own translation call, so all thirteen are extracted (code
  review).
- [x] T017 [US1] Check that no address reaches a view of django-activity-stream or of
  django-mvp-community's activity pages, and correct ADR 0045, decision D4 and the docs to say a
  portal must not include `actstream.urls` (code review).
- [x] T018 [US1] Credit someone on the private dataset in the visitor and stranger case, so the
  contributor lines are held to the scope (code review).
- [x] T019 [US1] Carry each line's count, assert it, and test that a count covers only the samples
  the viewer may see (code review).
- [x] T020 [US1] Assert the full list's address in the panel, not a patched one (code review).
- [x] T021 [US1] Move the change tracker's sentence to the Project and Dataset sections of the
  model reference (code review).
- [x] T022 [US1] Document the arguments and results of the gathering helpers (code review).
- [x] T023 [US1] A developer reference page for the activity app, naming every public class the
  docs check found undocumented.
- [x] T024 [US1] At phone width, release the activity row's children from the list row's first grid
  row, so the day sits on its own line above its lines (parity check at the merge gate).
