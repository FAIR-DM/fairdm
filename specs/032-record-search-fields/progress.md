# Progress: FS-032

- 2026-10-21: specification approved; issue graph built (#541, stories #544 to #551).
- 2026-10-21: sketch approved after three rounds at 7a4f2e4d.
- 2026-10-21: research, plan and tasks written.

## 2026-10-21T12:23:00Z · Implementer US1 · T001

Did: DatasetAutocompleteView on RecordAutocompleteView, scoped subclasses and the three dataset addresses; tests for edit/view/public, grouping, paging, visitors, escaping, uuid.
Verified: uv run pytest -q -n0 tests/test_contrib/test_autocomplete/test_views.py -> 16 passed.
Next: T002 project view.
Watch: page parameter is p, not page; sanitize_dict returns SafeString so no unescape.

## 2026-10-21T12:23:54Z · Implementer US1 · T002

Did: ProjectAutocompleteView and its three project addresses.
Verified: uv run pytest -q -n0 tests/test_contrib/test_autocomplete/test_views.py -> 20 passed.
Next: T003 limits on every address.
Watch: none.

## 2026-10-21T12:27:36Z · Implementer US1 · T003

Did: LimitedAutocompleteMixin (fixed page size, 100-char search, page cap, empty allow-lists, failure answer with nothing else) under RecordAutocompleteView.
Verified: uv run pytest -q -n0 tests/test_contrib/test_autocomplete/test_views.py -> 74 passed. Probed the filter allow-list by setting it to None: 12 tests failed, restored.
Next: T004 throttling.
Watch: f/e outside the allow-list yield no results (library behaviour), ordering is ignored because the view orders itself.
