
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
