# Progress — 017 Portal roles and the people who hold them

## 2026-09-16

- **Spec gate: approved** by Sam in session, 2026-09-16. Epic #338, stories #339–#343, draft PR #344.
  Approval carried one instruction: re-sync the branch with `main`, which had just moved.
- Branch rebased onto `1a03eec` (the demo-directory rename) and force-pushed as the bot.
- S3 PLAN begins.
- US1 implementation begins on `017-portal-roles-us1`, cut from `3ac8a56`.
- **T002**: `tests/test_portal_roles.py::TestDeclarations` written and observed failing
  (`ModuleNotFoundError: No module named 'fairdm.portal_roles'`) before `fairdm/portal_roles.py`
  existed. Commit `fce8f53`.
- **T003**: `fairdm/portal_roles.py` declares `PortalRoles` with the four roles as class-level
  `PortalRole` data, `shipped_names()`, `rights_carrying()` and `reconcile()` (stubbed to
  install, not yet wired to a signal). `TestDeclarations` (8 tests) green. Commit `323b255`.
  The worktree's synced virtualenv resolved to Python 3.14, under which `django-environ`
  fails to import (`pkgutil.find_loader` was removed) and the whole suite could not collect —
  an environment fault, not a code one. Fixed by pointing Poetry at the already-installed
  Python 3.13 (`poetry env use`) and re-running `poetry install --sync --with dev,test,docs`;
  no repository file changed. Noted in the completion report's `concerns`.
- **T004**: `TestReconcile` added to `tests/test_portal_roles.py`. `reconcile()` was already
  implemented as part of T003's commit rather than stubbed, so the red step for this task was a
  probe, not a fresh failure: `reconcile()`'s body was temporarily replaced with `pass`, five of
  six new tests failed for the expected reason (roles and renames not installed), the body was
  restored byte-for-byte (`git diff` empty), and all fourteen tests in the file pass. Commit
  `15f28cc`.
- **T005**: `FairDMConfig._connect_portal_roles_reconciliation()` connects
  `post_migrate` with no sender and `dispatch_uid="fairdm.reconcile_portal_roles"`, calling
  `PortalRoles.reconcile()`. `TestPortalRolesReconciliation` in `tests/test_apps.py` (new) was
  written first and observed failing (`Group.DoesNotExist`) before the connection existed, then
  passed after it — a real, not probed, red-green cycle, exercised through `call_command
  ("migrate")` rather than a direct `reconcile()` call, so it proves the wiring and not just the
  method. Commit `43085b0`.
- **T006**: `fairdm/fixtures/groups.json` deleted, `("loaddata", "groups")` removed from
  `DJANGO_SETUP_TOOLS`'s `on_initial` list (`fairdm/conf/settings/apps.py`). New tests in
  `tests/test_conf/test_settings/test_apps.py::TestGroupsFixtureRemoved`, observed failing
  (file still present; step still listed) before the change. Full `test_settings/test_apps.py`
  scope (9 tests) green. Commit `cb7e676`.
- **T007**: `DefaultGroups` removed from `fairdm/contrib/contributors/choices.py` (it had no
  call sites anywhere in the package — confirmed by grep before deleting); `PersonFilter.is_staff`
  relabelled from "Portal Administrators" to "Staff Only", matching `is_active`'s "Active Only"
  sibling. New tests in `test_choices.py::TestDefaultGroupsRemoved` and the new
  `test_filters.py::TestPersonFilterIsStaffLabel`, both observed failing first. Full
  `tests/test_contrib/test_contributors/` scope (386 tests) green. Commit `34ed2c9`.
