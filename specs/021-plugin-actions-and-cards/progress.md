
## 2026-10-06T21:23:29Z · Planner · plan

Did: wrote research.md, plan.md, tasks.md (17 tasks over 4 stories) and the ledger, on the branch brought up to date with origin/main at dafb8efb.
Verified: the application starts and answers from this branch after uv sync and migrate.
Next: design review, one reviewer with three lenses.
Watch: US-1 carries the groundwork every later story builds on, so it is the largest of the four.

## 2026-10-06T21:36:55Z · Implementer US1 · T001

Did: wrote tests/test_contrib/test_plugins/test_places.py (place option, resolve, page actions, record types that offer places).
Verified: uv run pytest tests/test_contrib/test_plugins/test_places.py -q -n0 fails at collection, ModuleNotFoundError fairdm.contrib.plugins.places, which is the missing feature. pre-commit passes.
Next: T002 tests for the navigation and startup validation.
Watch: Place has no card member yet; a column is refused whatever the place.

## 2026-10-06T21:37:27Z · Implementer US1 · T002

Did: added TestNavigationUnchanged to test_registration.py and TestPluginRegistryValidatedAtStartup to tests/test_apps.py.
Verified: uv run pytest on both classes -q -n0: 2 failed (action listed in navigation; ready() does not refuse an action against Point), 3 passed. The passing action-served-under-its-own-name test guards FR-007 while the patterns are rebuilt from mounts; it passed before the change because an unrecognised place is ignored today.
Next: T003 page tests and the registry-and-URL fixture.
Watch: ready() is called a second time in-process by these tests; it is safe to repeat.
