
## 2026-10-06T12:11:56Z · Planner · plan

Did: wrote research.md, plan.md, tasks.md (32 tasks over 7 stories) and the ledger, on the branch brought up to date with origin/main at 5998b914.
Verified: manage.py check clean after uv sync and migrate; the shared dev server reloaded and answers.
Next: design review, one reviewer with three lenses.
Watch: no page creates a sample or measurement, so the creator rule is delivered for projects and datasets and as a callable for the other two.

## 2026-10-06T12:31:23Z · Implementer US1 · T001

Did: wrote tests/test_contrib/test_contributors/test_access.py (TestRecordsAbove, TestLevelOf, TestLevelParts, TestPeopleAbove, TestManagers, TestCanManage, TestRequiredLevel) and TestPersonCanSignIn in test_models.py, plus the record_chain and grant fixtures in the contributors conftest. TestLevelParts, TestPeopleAbove and TestRequiredLevel go past the list in tasks.md: the tab reads the two halves of a level and the people above, and REQUIRED_LEVEL must cover every permission the four record types declare.
Verified: `uv run pytest tests/test_contrib/test_contributors/test_access.py -q -n0` fails at collection with ImportError (RecordAccess and REQUIRED_LEVEL do not exist); `uv run pytest tests/test_contrib/test_contributors/test_models.py::TestPersonCanSignIn -q -n0` gives 4 failed with AttributeError (no can_sign_in). Both are the expected reason.
Next: T002.
Watch: the tree is red between T001 and T004 on purpose.

## 2026-10-06T12:31:23Z · Implementer US1 · T002

Did: wrote tests/test_contrib/test_contributors/test_services/test_crediting.py: TestAdd (view level on each of the four record types, none for an organization, placed last, duplicate refused with code duplicate, superuser refused with code superuser), TestOfferedRoles, TestUpdate (roles saved and replaced, none allowed, role_not_offered, level untouched), TestRemove.
Verified: `uv run pytest tests/test_contrib/test_contributors/test_services/test_crediting.py -q -n0` fails at collection with ImportError on RecordAccess, the expected reason.
Next: T003.
Watch: Crediting.offered_roles is a method beyond the three the brief lists; the edit page needs the offered roles from the same place the service checks them.

## 2026-10-06T12:31:23Z · Implementer US1 · T003

Did: wrote tests/test_contrib/test_contributors/test_plugins/test_contribution_tab.py (TestContributorsTab, TestChangingPagesRefuseAnyoneButAManager, TestAddFromPortal, TestEditRoles, TestRemoveContributor), run on a project, a dataset, the demo's registered sample type and its registered measurement type. Fixtures (public_chain, record, manager, reader, colleague, partner, newcomer, curator) are in test_plugins/conftest.py.
Verified: `uv run pytest tests/test_contrib/test_contributors/test_plugins/test_contribution_tab.py -q -n0 -x` fails at collection with ImportError on RecordAccess, the expected reason.
Next: T004, implementation.
Watch: records in the page tests are public so the tests stay valid when the tab refuses strangers on private records (US4).

## 2026-10-06T12:43:11Z · Implementer US1 · T004

Did: ContributionLevel and Contribution.level with migration 0022 (applied to the dev server's database with the development settings). access.py rebuilt as RecordAccess (above, kind, level_of, own_level, level_from_above, people_above, managers, can_manage) and REQUIRED_LEVEL. Person.can_sign_in, which is_editable_by now asks. services/crediting.py with Crediting.add, update (roles), remove and offered_roles. plugins/shared.py moved onto both: list, portal tab of both add pages, roles on the edit page, remove page; the prototype's affiliation choice, level radio, last-manager refusal and the move page are left as they were. RecordOverviewPlugin sets people_url for all four record types. Seeds: contributors.py credits through Crediting; common.py and projects.py also set the level next to the guardian rows they still grant (give_level). Dev database: contributions of the records seed_contributors made were given the level their guardian rows amount to with a one-off shell snippet (53 contributions; not a migration).
Pre-existing tests brought up to date: tests/test_contrib/test_plugins/test_registration.py::TestExtraViews::test_the_shipped_contribution_views_address_their_target (now reverses the tab's five views: add-person, add-organization, edit, remove, move) and tests/test_core/test_dataset/test_plugins.py::TestRetiredManagementPages::test_the_dataset_menu_carries_one_entry (the dataset menu now also carries contribution-list).
Template change: cotton/contribution/access.html reads entry.manages in place of comparing entry.effective with the word "manage"; what it draws is the same. entry.manages is new in the context beside the names the brief lists.
Verified: `uv run pytest tests/test_contrib/test_contributors tests/test_contrib/test_plugins tests/test_core/test_dataset/test_plugins.py::TestRetiredManagementPages -q -n auto --dist loadscope` 1244 passed; `uv run pytest tests/test_core tests/test_templates tests/test_api -q -n auto --dist loadscope` 1792 passed, 7 skipped; `uv run pytest tests/test_demo tests/test_smoke.py -q -n auto --dist loadscope` 58 passed; `uv run python manage.py makemigrations contributors demo --check --dry-run` no changes; `uv run pre-commit run --all-files` passes. Opened the tab, both add pages, edit and remove as regular.user on the seeded private dataset through the test client against the dev database: all 200.
Next: T005, the documentation.
Watch: a person added from the tab now holds the view level and no guardian row, so on a private record the permission backends still guard they cannot open it until the backend switches. The :outline attribute on the level badge in access.html is a Cotton expression that cannot be resolved, so it was never applied; left alone so the page draws as approved.

## 2026-10-06T12:43:11Z · Implementer US1 · T005

Did: docs/user-guide/crediting-a-record.md (linked from the user guide index): the tab, who may change it, adding from the portal, roles, removing. docs/portal-development/contributors.md: new section The Contributors tab (registered types get it with no configuration, the page classes and addresses, levels, REQUIRED_LEVEL, RecordAccess and how a page asks whether a person may view, edit or manage, Person.can_sign_in, Crediting and its codes); the sentence on who may edit a profile now points at can_sign_in, and the note that creating a credit grants nothing now says what Crediting.add gives. CHANGELOG entry under Unreleased.
Verified: ran every code block of the new portal-development section through a throwaway test (deleted afterwards) with a project, dataset, registered sample and person: all ran as written. The kit's docs audit (`forgekit.docs_check.audit(repo, base="origin/main")`) now lists four names: ContributionMove (moving and order, US6), level_choices (levels on the edit page, US4), give_level in demo/seed/common.py (US4, with the rows it sits beside) and ContributorSeed (the seed command, US7). Before this story's docs it listed 13.
Next: the full gate once, then the completion report.
Watch: the user guide page describes only what the tab does today: adding from the portal, roles, removing. ORCID, ROR and by-hand adding, the affiliation choice, levels on the edit page and ordering are for the stories that own them to add to it.
