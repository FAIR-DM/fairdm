
## 2026-10-14T21:48:43Z · Forge · PLAN

Did: research, plan and tasks written after the sketch was approved. Ledger initialised at PLAN.
Verified: lat-lon-parser 1.3.1 tried against the notations in the spec.
Next: design review.
Watch: US1 is large: fields, removal of Point and the input.

## 2026-10-14T22:15:52Z · Implementer US1 · T001

Did: added lat-lon-parser 1.3.1 (pyproject, uv.lock) and parse_coordinate(text, axis) in fairdm/contrib/location/forms.py, with TestParseCoordinate* tests written first (seen failing on import). The dependency landed here, not in T006, because the function needs it.
Verified: uv run pytest -q -n0 tests/test_contrib/test_location/test_forms.py -> 60 passed. pre-commit on the changed files passed.
Next: T002, LocationField, Location and the widget class.
Watch: the package refuses whole degrees above 180 itself, so the range check reads the first number before calling it, otherwise 181 reports as unreadable.
