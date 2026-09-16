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
