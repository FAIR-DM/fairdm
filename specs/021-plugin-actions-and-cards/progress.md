
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

## 2026-10-06T21:40:07Z · Implementer US1 · T003

Did: added the PluginSandbox fixture (plugin_sandbox) to tests/conftest.py, tests/test_conftest.py proving a declared plugin and its address are gone after close, and tests/test_templates/test_overview_page_actions.py (six record types, visitors, predicate, permission, subtype narrowing, empty and hidden, raising predicate, order, apart from the Manage menu).
Verified: uv run pytest tests/test_conftest.py -q -n0: 2 passed. uv run pytest tests/test_templates/test_overview_page_actions.py -q -n0: 13 failed, 3 passed; the failures are the dropdown listing nothing where an action is expected. pre-commit passes.
Next: T004 implementation.
Watch: the sandbox imports the six URL modules, the core include module and the root URL configuration again, so a portal with record types mounted elsewhere is not covered.
