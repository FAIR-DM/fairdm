
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
