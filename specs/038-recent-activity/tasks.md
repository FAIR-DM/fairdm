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
  `TestNoOtherFeed` in `tests/test_contrib/test_activity/test_exposure.py`, as plan.md "Tests"
  describes.
- [x] T003 [US1] `fairdm/contrib/activity/` with `apps.py` and `receivers.py`, as plan.md
  "Recording" describes. T002 goes green.

### Group 2

- [ ] T004 [US1] Tests: `TestActivityLines` in `tests/test_contrib/test_activity/test_lines.py`, as
  plan.md "Tests" describes.
- [ ] T005 [US1] `fairdm/contrib/activity/lines.py`: `Line`, `ActivityLines` and
  `recent_activity`, as plan.md "Gathering" describes. T004 goes green.

### Group 3

- [ ] T006 [US1] Tests: `TestActivityPanel` and `TestOverrides` in
  `tests/test_templates/test_activity.py`, the two page checks there, and `TestActivityPage` in
  `tests/test_contrib/test_activity/test_plugins.py`, as plan.md "Tests" describes.
- [ ] T007 [US1] The panel, the row override, the `overview.activity` block in both detail
  templates and `activity` in both overview plugins' context, as plan.md "The panel and the
  overrides" describes, ported from the prototype as "What is ported" lists.
- [ ] T008 [US1] `fairdm/contrib/activity/plugins.py` and `activity/activity_list.html`, as plan.md
  "The full list" describes. T006 goes green.
- [ ] T009 [US1] `fairdm/static/css/fairdm.css`: the `.ov-activity` rules, ported onto the
  package's list inside the panel. No test.

### Group 4

- [ ] T010 [US1] Edit `specs/018-overview-pages/spec.md` as plan.md "Specifications edited"
  describes.
- [ ] T011 [US1] Documentation and `CHANGELOG.md`, as plan.md "Documentation" describes.
