# Progress: 018-overview-pages

- 2026-09-29: build branch cut from main with the reviewed prototype merged in. Plan and tasks written against the revised specification. Baseline: 12 pre-existing tests red, lint and docs checks red, all folded into US-1 to US-4.

## 2026-09-29 · US1 · T001

- Did: declared `pyecharts` as a direct dependency, added `django-mvp-charts` to the deptry DEP002 ignore list, re-locked. Fixed the ten ruff findings without `noqa`: the seeds read the published development password from `create_dev_accounts`, en dashes written as `–`, the silent `except` replaced by a lookup, the `credits` function and `license` argument renamed (`credits_of`, `licence`), list concatenation replaced by unpacking.
- Verified: `uv run pre-commit run --all-files` passes all eight hooks.
- Next: T002.
- Watch: `ruff format` over `demo` and `fairdm` touches files outside this branch's diff (`demo/README.md`, `tests/test_core/test_abstract.py`); run pre-commit rather than the formatter directly.

## 2026-09-29 · US1 · T002

- Did: `tests/test_core/test_overview.py` (`format_authors`, `json_ld`, `as_date`) and `tests/test_core/test_plugins.py` (`RecordOverviewPlugin.get_identifiers`).
- Verified: `uv run pytest tests/test_core/test_overview.py -q` passes, 17 tests. `tests/test_core/test_plugins.py` fails at import (`RecordOverviewPlugin` does not exist yet), the failure T007 removes. It also asserts that a grant number that looks like a DOI is not linked, which the prototype's value-prefix rule gets wrong; T008 fixes it.
- Next: T003.

## 2026-09-29 · US1 · T003

- Did: `tests/test_templates/` (declared under `[tool.forge.conformance] non-mirror-paths`): `test_overview_page.py` (side column order, `block.super` on the wrapping blocks, header people row, chart library block), `test_cards.py` (every `c-card.*` component with its inputs, empty states and the accessible names), `test_includes.py` (`pending_action.html`, `type_badge.html`). Components are rendered through `django_cotton.render_component`, and slot content and child templates through a template written into a temporary directory the engine searches.
- Verified: `uv run pytest tests/test_templates -q -n0`: 68 passed, 4 failed. The four failures are the defects this task exists to find, each for the right reason: the header people block is still called `overview.meta`; the type dialog has no accessible name; a Details date and a timeline day use a literal pattern rather than the locale's named format.
- Next: T004.

## 2026-09-29 · US1 · T004

- Did: `TestOverview…` classes in `tests/test_core/test_project/test_plugins.py` with the `overview_showcase` and `project_team_member` fixtures in the project `conftest.py`: scenarios 1 to 11 as a visitor and as the team, the Manage menu offering Delete, private datasets never reaching a visitor's figures, charts, licences or JSON-LD, SC-006 chart text alternatives, what is not available yet, and the FR-057 language checks (the request carries `Accept-Language`, since the locale middleware decides the language, not `translation.override` around the client).
- Verified: `uv run pytest tests/test_core/test_project -q`: 352 passed, 7 failed. One failure is the untouched pre-existing `test_a_user_who_may_delete_the_project_is_offered_the_link`. The other six are new and fail for the right reason: Delete not offered to a user who may delete but not change; the composition chart lists a type the registry does not hold; the composition chart crashes on a stale content type; the growth chart labels, the growth chart description and a dataset's last-updated date use literal patterns rather than the locale's named formats. Probe: removing the visitor's dataset filter from `fairdm/core/project/overview.py` fails seven of the scenario 1 tests, then restored.
- Next: T005.
- Watch: the JSON-LD tests pass against the prototype because the project's export names no datasets. They pin that it stays so.

## 2026-09-29 · US1 · T005

- Did: `tests/test_demo/test_management/test_commands/test_seed_overviews.py` (refusal outside development, the three accounts, accounts left untouched, team rights, safe to run again, a foreign project sharing a seeded name) and `TestDevAccountsAbsentReportsTheExampleAccounts` in `tests/test_conf/test_checks.py`.
- Verified: `uv run pytest tests/test_demo tests/test_conf/test_checks.py -q -n0 -k "Seed or ExampleAccounts"`: 17 passed, 5 failed. The failures are the defects T008 fixes: an existing account has its password and names overwritten; the empty project's team is `regular.user` rather than `staff.user`; the regular user can open the private empty project; a foreign project sharing a seeded name is deleted. The `fairdm.E501` tests pass already, because the prototype extended the check.
- Next: T006.

## 2026-09-29 · US1 · T006

- Did: gave the six pre-existing tests named in the task a sample in a published, public dataset (fixture line only, assertions untouched), recorded as D6 in `decisions.md`.
- Verified: `uv run pytest tests/test_contrib/test_plugins -q`: 164 passed (6 of them were red before).
- Next: T007.

## 2026-09-29 · US1 · T007

- Did: added `RecordOverviewPlugin` (shared methods) and gave `TypedOverviewPlugin` `get_type_info`; all four `Overview` plugins subclass it; moved the project's logic onto its `Overview` plugin and deleted `fairdm/core/project/overview.py`; the dataset, sample and measurement modules take the plugin as first argument and call the shared methods; the moved functions left `fairdm/core/overview.py`. See D7.
- Verified: `uv run pytest tests/test_core tests/test_templates tests/test_contrib/test_plugins tests/test_demo -q`: the same failures as before the move, all of them tests written to fail before T008 plus the pre-existing ones (two delete-link tests, and four tests for the dataset, sample and measurement stories). Every project, dataset, sample and measurement page in the development data, rendered as visitor, `staff.user` and `regular.user` before and after: 297 responses, no difference. `uv run pre-commit run --all-files` passes.
- Next: T008.

## 2026-09-29 · US1 · T008

- Did: the header's people block is `overview.byline`; the project and dataset Manage menus offer Delete to a user who may delete, with or without the right to change (the two pre-existing Delete tests pass untouched); the composition chart skips a type the registry does not hold and a content type whose model is gone; identifiers link to doi.org by type as well as value; the type dialog carries an accessible name (D10); the seed creates the example accounts only when missing, replaces only the projects it created, and puts the empty project's team on `staff.user` (D9); the sample plugin's change-history comment says what the code does; dates use named locale formats and the growth chart's labels and description follow the language (D8); project leaders are sorted by role name, not by its translated label.
- Verified: `uv run pytest tests -q`: 2996 passed, 8 skipped, 4 failed. The four failures are pre-existing tests for the sample (two), dataset and measurement stories, which belong to those stories. Every test added in T002 to T005 is green.
- Next: T009.
- Watch: a scan of the templates and Python that build the four pages found no untranslated shown string; the one English literal compared against a translated label was the leader sort.

## 2026-09-29 · US1 · T009

- Did: `docs/portal-development/overview-pages.md` (anatomy, block list, project page, extending a project page by template, the plugin methods and helper functions, development data), `docs/portal-development/component_library/cards.md` (every `c-card.*` component and `c-stats`, `c-list`, `c-tabs`, `c-progress`, each with a working example), the new section of `development_accounts.md`, the `context_object_name` passage of `sample-mixins.md`, both pages added to their toctrees, and a changelog entry under Unreleased.
- Verified: every fenced `django` example in `cards.md` rendered against the branch (16 examples), both template examples in `overview-pages.md` rendered as overrides of `project/project_detail.html` on a real project. The documentation check over the branch diff now reports 13 undocumented names, all in the dataset, sample and measurement modules that stay until their stories: `field_kind`, `field_summary`, `literature`, `preview_table`, `project_info`, `record_types`, `schema_org`, `shared_context` (dataset); `measurement_summary`, `related_samples`, `relations_summary` (sample); `sample_status`, `siblings` (measurement).

## 2026-09-29 · US2 · T010

- Did: `TestOverview…` classes in `tests/test_core/test_dataset/test_plugins.py` for scenarios 1 to 11, the JSON-LD of a public unpublished dataset, and the Delete offer. The old published-or-not test in `test_views.py` now states the new rule (decision D11).
- Verified: `uv run pytest tests/test_core/test_dataset/test_plugins.py -q -k TestOverview`: 25 passed on the first run, so the page already met every scenario. Probed by mutation: checklist for everyone, year order, project visibility, relation order and the timeline sort each turned a test red. The timeline sort probe first survived; the test now puts the added date before the collection so the sort decides it.
- Next: T011.
- Watch: a dataset holding only unregistered types shows the first-run card, because the card follows the types the registry knows.

## 2026-09-29 · US2 · T011

- Did: the dataset's logic is methods on the dataset `Overview` plugin (`get_lifecycle`, `get_access`, `get_dates`, `get_team`, `get_literature`, `get_record_types`, `get_counts`, `get_project_info`, `get_citation_details`, `get_schema_org`, `get_readiness`, `get_shared_context`, `get_details`) and `fairdm/core/dataset/overview.py` is deleted, with `preview_table`, `field_kind` and the value ranges of `field_summary`. `get_citation` from the shared plugin now writes the built citation. Nothing in `fairdm/core/overview.py` lost its last caller: the project plugin still uses `contributions_of`, `is_person` and `roles_of`, and the plugin base and the sample and measurement modules use `with_role`.
- Verified: `uv run pytest tests/test_core/test_dataset -q`: 417 passed, five runs. A T010 test was flaky on the first run (a random sample name showed up elsewhere on the page) and now uses distinctive names. Rendered all 14 seeded datasets as visitor, `staff.user` and `regular.user` before and after the move: 42 pages, no difference. `uv run pre-commit run --all-files`: all hooks pass.
- Next: T012.
- Watch: T010 found nothing to fix, so the move changed no rendered output.

## 2026-09-29 · US2 · T011 (a gap T010 found)

- Did: the readiness checklist counted eight required items and two recommended; FR-033 says seven and three. "The dataset is public" is now the third recommended item (decision D13). Two tests in `TestOverviewReadinessChecklist` fail before the change (8 required; a complete private dataset not ready) and pass after.
- Verified: `uv run pytest tests/test_core/test_dataset -q`: 419 passed.
- Next: T012.
- Watch: FR-033's count is the only statement of the split. If the maintainer meant the eight-and-two of the prototype, revert the one `False` and the two tests.

## 2026-09-29 · US2 · T012

- Did: `docs/portal-development/overview-pages.md` gained the dataset page (header, notices, figures, content and side columns, the timeline card, the readiness checklist, the citation, related publications, what a visitor sees before publication, the page head), extending a dataset page by template, and the dataset plugin's methods. The changelog entry for the overview pages is extended with the dataset page.
- Verified: the template example in the dataset section rendered as an override of `dataset/dataset_detail.html` on a real dataset. `forge verify --steps docs --base origin/main`: the only names left undocumented are the five that belong to the sample and measurement stories.
- Next: the full verify, then the report.

## 2026-09-29 · US3 · T013

- Did: `TestOverview…` classes in `tests/test_core/test_sample/test_plugins.py` for scenarios 1 to 12, template choice by own type, nearest ancestor and fallback, and a subtype with a plain manager. `TestVisibleTo` in `test_managers.py`, `TestDatasetDataIsPublic` in `test_models.py`. The two gate tests use a published dataset (decision D14). The plain-manager test failed with an `AttributeError` on `visible_to`; the typed check now reads through the base model (decision D15).
- Verified: `uv run pytest tests/test_core/test_sample/test_plugins.py -q`: 51 passed. The rest of the page already met every scenario, so T014 moves code without changing output.
- Next: T014.
- Watch: `related_samples` says hidden relations are not counted; the code and FR-023 count them, so the docstring changes as it moves.

## 2026-09-29 · US3 · T014

- Did: the sample's logic is methods on the sample `Overview` plugin (`get_status`, `get_measurements`, `get_related_samples`, `get_relations_summary`, `get_citation_details`, `get_details`) and `fairdm/core/sample/overview.py` is deleted. The `related_samples` docstring no longer says hidden relations are not counted; they are, in `hidden`. `published()` and `visible_to()` moved into `RecordVisibilityMixin` and both querysets use it (decisions D16, D17). The measurement module reads the status colours from the sample plugin.
- Verified: `uv run pytest tests/test_core/test_sample tests/test_core/test_measurement tests/test_core/test_managers.py -q`: only the known measurement test fails, which belongs to the measurement story. Rendered all 141 seeded samples as visitor, `staff.user` and `regular.user` before and after the move: 423 pages, no difference. `uv run pre-commit run --all-files`: all hooks pass.
- Next: T015.
- Watch: T013 found one gap, the visibility check on a typed overview, fixed in the same commit as its test.

## 2026-09-29 · US3 · T015

- Did: `docs/portal-development/overview-pages.md` gained the sample page (header, notices, figures, both columns, the history, who can open it) and "Giving a sample or measurement type its own page" with the demo's rock sample as the worked example, the plain-manager note, the visibility mixin and the sample plugin's methods. The changelog entry for the overview pages is extended.
- Verified: `forge verify --steps docs --base origin/main`: the only names left undocumented are `sample_status` and `siblings`, which belong to the measurement story.
- Next: the full verify, then the report.

## 2026-09-29 · US4 · T016

- Did: `tests/test_core/test_measurement/test_plugins.py` covers US-4 scenarios 1 to 10 (address, template choice, visibility by the measurement's own dataset, the unpublished sample, the map, the result, the type badge, siblings, procedure, citation, breadcrumbs) as visitor and team, asserting the literal `/measurement/<uuid>/`. `TestVisibleTo` added to the measurement manager tests. The authorised detail-page test now uses a published dataset, with a 404 case beside it (D18).
- Verified: `uv run pytest tests/test_core/test_measurement/test_plugins.py tests/test_core/test_measurement/test_managers.py tests/test_core/test_measurement/test_models.py::TestMeasurementViews -q`: 55 passed. Probed by making the sample always visible (3 failed) and dropping the siblings `visible_to` (2 failed), then restored.
- Next: T017.
- Watch: the page's behaviour already met every scenario; T016 found no gap. A sample's list crumb has no link (no `sample-list` route exists), and the measurement's matches it.

## 2026-09-29 · US4 · T017

- Did: the measurement's logic is methods on its `Overview` plugin (`get_result`, `get_sample_status`, `get_siblings`, `get_citation_details`, `get_details`) and `fairdm/core/measurement/overview.py` is deleted. `get_contributions`, `get_role_names` and `get_contributors_with_role` moved onto `RecordOverviewPlugin`; the project, dataset and sample plugins call them, and `fairdm/core/overview.py` holds the six pure functions (D19). Direct tests for the three credit methods added to `tests/test_core/test_plugins.py`.
- Verified: `uv run pytest tests/test_core/test_measurement tests/test_core/test_sample tests/test_core/test_project/test_plugins.py tests/test_core/test_dataset/test_plugins.py tests/test_core/test_overview.py tests/test_core/test_plugins.py tests/test_core/test_managers.py -q`: green. Rendered 56 seeded records (projects, datasets, up to eight of each sample and measurement type) as visitor, staff.user and regular.user before and after the move: 168 responses, status, length and content hash identical in every one.
- Next: T018.
- Watch: no test other than my own was edited.

## 2026-09-29 · US4 · T018

- Did: `docs/portal-development/overview-pages.md` gained "The measurement page" (header, figures, both columns, who can open it, the unpublished sample), the demo's XRF measurement as the worked example under "Giving a sample or measurement type its own page", the measurement plugin's methods with `procedure_steps` and `siblings_shown`, and the three credit methods on `RecordOverviewPlugin`. The changelog entry for the measurement page is added under Added.
- Verified: `forge verify --steps docs --base origin/main`: passed.
- Next: the full verify, then the report.

## 2026-09-29 · FIX-1 · TC01–TC06

- Did: TC01 type badge is plain when the registry has nothing to say (falls back to the configuration description); TC02 dataset and project dates shown as precisely as recorded (`format_partial_date`, `as_date` kept for sorting); TC03 sibling-dataset count limited to what the viewer may open; TC04 funder identifier and award URI linked only when http(s); TC05 hidden and missing records raise the same 404, bare protocol DOIs link to doi.org; TC06 changelog entries, false "moved from" sentences removed, docstrings added, docs pages updated.
- Verified: each task's own test class red then green; `forge verify --base origin/main` green on lint, typecheck, test, build, conformance and docs.
- Next: review.
- Watch: no test other than my own was edited. The project-manager rule in TC03 uses `project.change_project`, held per project.

## 2026-09-30 · FIX-2 · TC07

- Did: `grant_team_rights` in `demo/seed/common.py` gives `staff.user` view/change/delete on every seeded project and dataset; the sparse project, the sample-page and the measurement-page examples now use it.
- Verified: `uv run pytest tests/test_demo/test_management/test_commands/test_seed_overviews.py -q`: 19 passed (new rights test red first); `pre-commit run --all-files` green.
- Next: TC08.
- Watch: `regular.user` still holds nothing.

## 2026-09-30 · FIX-2 · TC08

- Did: the `overview.notices` block now renders before the header, inside the page-title block, on all four pages; the block table in `docs/portal-development/overview-pages.md` moved it to the top.
- Verified: `uv run pytest tests/test_templates/test_overview_page.py -q`: 13 passed. Layout only, no new test.
- Next: TC09.
- Watch: none.

## 2026-09-30 · FIX-2 · TC09

- Did: `get_people` lists everyone credited (no `exclude`); the People card always renders, carries `data-card="people"` and says no one is credited yet when empty; docs updated.
- Verified: `uv run pytest tests/test_core/test_project/test_plugins.py tests/test_templates tests/test_core/test_dataset tests/test_core/test_sample tests/test_core/test_measurement -q`: 1213 passed, 7 skipped (the skips were already there); the changed tests failed first. Pre-commit green.
- Next: TC10.
- Watch: five branch tests edited, listed in D20.

## 2026-09-30 · FIX-2 · TC10

- Did: every side-column card renders with an empty-state line: funding (everyone), identifiers, citation, dataset timeline and publications, sample Related and Location, measurement Sample location (no location, or sample hidden: no coordinates), and the project's timeline entry in Details. Each carries a `data-card` hook. Readiness stays team-only. Docs updated.
- Verified: `uv run pytest tests/test_core tests/test_templates tests/test_demo -q -n auto --dist loadscope`: 1570 passed, 7 skipped (already skipped); new tests red first. Pre-commit green.
- Next: TC11.
- Watch: two branch tests replaced and one removed, listed in D21.

## 2026-09-30 · FIX-2 · TC11

- Did: the sample's Edit, Descriptions, Keywords and Key Dates pages are registered with `menu=False`, so they leave the tab strip; a Manage menu in the sample header links to them for users holding `sample.change_sample`. Addresses and URL names unchanged. Docs updated.
- Verified: `uv run pytest tests/test_core/test_sample tests/test_contrib/test_plugins tests/test_templates -q`: 544 passed, 7 skipped (already skipped); the two new behaviour tests failed first. Pre-commit green.
- Next: TC12.
- Watch: chose `menu=False` over `extra_views`, see D22. No existing test was edited.
