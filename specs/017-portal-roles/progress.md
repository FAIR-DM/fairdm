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
- **T008**: `docs/portal-administration/roles.md` rewritten for the four shipped roles, the
  superuser-vs-Portal-Administrator distinction, the legacy-group rename on upgrade, and the
  model-level-permission upgrade note. `managing_users_and_permissions.md`'s "User Roles" section
  and one stale "Database Admin" troubleshooting reference reconciled against it. No automated
  test — this codebase has no doc-content test convention (checked: no existing test opens a
  `docs/*.md` file) — so this was proofread by hand rather than red-green. Commit `c522b7a`.
- **T009**: `CONTEXT.md` gains a "Roles" section defining *portal role*, *contribution role* and
  *rights-carrying role*, and naming the four roles. Prose-reviewed by hand, same as T008.
  Commit `b11867f`.
- **T010**: `CHANGELOG.md` gains the `groups` fixture removal under Removed, the model-level-
  permission upgrade note under Changed, and a new "Portal roles (Feature 017)" entry under
  Added. Commit `98aaf26`.
- **Concern for triage**: `docs/portal-administration/adjusting_dataset_access.md:130` still
  names the pre-existing "Database Admin" group in a troubleshooting bullet. Out of T008's named
  file scope (`roles.md`, `managing_users_and_permissions.md`), so left alone and flagged here
  rather than fixed.

## US2 implementation begins on `017-portal-roles-us2`, cut from `8735205`

- **T011**: `tests/test_permissions.py::TestPortalRoleBackend` added, eight tests, importing
  `fairdm.permissions.PortalRolePermissionBackend`. Observed failing with
  `ModuleNotFoundError: No module named 'fairdm.permissions'` (`poetry run pytest
  tests/test_permissions.py -x`) - the module does not exist yet, which is the right reason for
  a new-file task. Commit `76c46b9`.
- **T012**: `fairdm/permissions.py::PortalRolePermissionBackend` added and registered last in
  `AUTHENTICATION_BACKENDS` (`fairdm/conf/settings/auth.py`). Answers `has_perm(perm, obj)` from
  `user_obj.has_perm(perm)` (the model-level question), returns `False` outright when `obj is
  None` (so the nested `has_perm(perm)` call cannot recurse into this backend a second time) and
  when the permission is `contributors.manage_organization`/`manage_organization` (D14). All
  eight `TestPortalRoleBackend` tests pass (`poetry run pytest tests/test_permissions.py -v`);
  the manage_organization test manufactures the stale `Permission` row directly
  (`ContentType.objects.get_for_model(Organization)` + `get_or_create`), since a fresh database
  never creates it — `fairdm/contrib/contributors/migrations/
  0017_remove_manage_organization_permission.py` deletes it as part of the same migration that
  removed it from `Organization.Meta.permissions`, so the row only survives on a database that
  ran migration `0013` before `0017` shipped. The adjacent permission-backend suites
  (`test_contrib/test_contributors/test_permissions.py`, `test_core/test_sample/
  test_permissions.py`, `test_core/test_measurement/test_permissions.py`, 61 tests) stay green.
  Commit `00e2b14`.
