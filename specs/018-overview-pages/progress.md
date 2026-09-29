# Progress: 018-overview-pages

- 2026-09-29: build branch cut from main with the reviewed prototype merged in. Plan and tasks written against the revised specification. Baseline: 12 pre-existing tests red, lint and docs checks red, all folded into US-1 to US-4.

## 2026-09-29 · Implementer US1 · T001

- Did: declared `pyecharts` as a direct dependency, added `django-mvp-charts` to the deptry DEP002 ignore list, re-locked. Fixed the ten ruff findings without `noqa`: the seeds read the published development password from `create_dev_accounts`, en dashes written as `–`, the silent `except` replaced by a lookup, the `credits` function and `license` argument renamed (`credits_of`, `licence`), list concatenation replaced by unpacking.
- Verified: `uv run pre-commit run --all-files` passes all eight hooks.
- Next: T002.
- Watch: `ruff format` over `demo` and `fairdm` touches files outside this branch's diff (`demo/README.md`, `tests/test_core/test_abstract.py`); run pre-commit rather than the formatter directly.

## 2026-09-29 · Implementer US1 · T002

- Did: `tests/test_core/test_overview.py` (`format_authors`, `json_ld`, `as_date`) and `tests/test_core/test_plugins.py` (`RecordOverviewPlugin.get_identifiers`).
- Verified: `uv run pytest tests/test_core/test_overview.py -q` passes, 17 tests. `tests/test_core/test_plugins.py` fails at import (`RecordOverviewPlugin` does not exist yet), the failure T007 removes. It also asserts that a grant number that looks like a DOI is not linked, which the prototype's value-prefix rule gets wrong; T008 fixes it.
- Next: T003.

## 2026-09-29 · Implementer US1 · T003

- Did: `tests/test_templates/` (declared under `[tool.forge.conformance] non-mirror-paths`): `test_overview_page.py` (side column order, `block.super` on the wrapping blocks, header people row, chart library block), `test_cards.py` (every `c-card.*` component with its inputs, empty states and the accessible names), `test_includes.py` (`pending_action.html`, `type_badge.html`). Components are rendered through `django_cotton.render_component`, and slot content and child templates through a template written into a temporary directory the engine searches.
- Verified: `uv run pytest tests/test_templates -q -n0`: 68 passed, 4 failed. The four failures are the defects this task exists to find, each for the right reason: the header people block is still called `overview.meta`; the type dialog has no accessible name; a Details date and a timeline day use a literal pattern rather than the locale's named format.
- Next: T004.

## 2026-09-29 · Implementer US1 · T004

- Did: `TestOverview…` classes in `tests/test_core/test_project/test_plugins.py` with the `overview_showcase` and `project_team_member` fixtures in the project `conftest.py`: scenarios 1 to 11 as a visitor and as the team, the Manage menu offering Delete, private datasets never reaching a visitor's figures, charts, licences or JSON-LD, SC-006 chart text alternatives, what is not available yet, and the FR-057 language checks (the request carries `Accept-Language`, since the locale middleware decides the language, not `translation.override` around the client).
- Verified: `uv run pytest tests/test_core/test_project -q`: 352 passed, 7 failed. One failure is the untouched pre-existing `test_a_user_who_may_delete_the_project_is_offered_the_link`. The other six are new and fail for the right reason: Delete not offered to a user who may delete but not change; the composition chart lists a type the registry does not hold; the composition chart crashes on a stale content type; the growth chart labels, the growth chart description and a dataset's last-updated date use literal patterns rather than the locale's named formats. Probe: removing the visitor's dataset filter from `fairdm/core/project/overview.py` fails seven of the scenario 1 tests, then restored.
- Next: T005.
- Watch: the JSON-LD tests pass against the prototype because the project's export names no datasets. They pin that it stays so.

## 2026-09-29 · Implementer US1 · T005

- Did: `tests/test_demo/test_management/test_commands/test_seed_overviews.py` (refusal outside development, the three accounts, accounts left untouched, team rights, safe to run again, a foreign project sharing a seeded name) and `TestDevAccountsAbsentReportsTheExampleAccounts` in `tests/test_conf/test_checks.py`.
- Verified: `uv run pytest tests/test_demo tests/test_conf/test_checks.py -q -n0 -k "Seed or ExampleAccounts"`: 17 passed, 5 failed. The failures are the defects T008 fixes: an existing account has its password and names overwritten; the empty project's team is `regular.user` rather than `staff.user`; the regular user can open the private empty project; a foreign project sharing a seeded name is deleted. The `fairdm.E501` tests pass already, because the prototype extended the check.
- Next: T006.
