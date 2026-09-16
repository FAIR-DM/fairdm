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
- **T013**: `tests/test_contrib/test_admin/` created (new package, mirrors `fairdm/contrib/
  admin/`) with `test_sites.py::TestAdministrationAccessForRoleHolders` - nine tests: each of
  the three rights-carrying roles reaches `admin:index` and one changelist both with an existing
  session and by signing in through `admin:login`; a Developer-only holder, an ordinary
  contributor and a deactivated role holder are each refused (302, unauthenticated). Observed
  failing first: the six "reaches" tests failed (302/anonymous) because `CustomAdminSite` still
  asked for `is_staff` alone; the three "refused" tests already passed, which is expected since
  nothing yet grants them anything (`poetry run pytest tests/test_contrib/test_admin/
  test_sites.py -v`). Commit `7fb8002`.
- **T014**: `CustomAdminSite.has_permission` (`fairdm/contrib/admin/sites.py`) now accepts
  `user.is_active and (user.is_staff or` membership in a rights-carrying role`)`, and a new
  `PortalAdminAuthenticationForm(AdminAuthenticationForm)` carries the same rule into
  `confirm_login_allowed` (calling straight through to `AuthenticationForm`'s own
  `is_active`-only check, skipping `AdminAuthenticationForm`'s `is_staff` requirement), set as
  `CustomAdminSite.login_form` - both were named in T014 because changing one without the other
  (research R3) leaves a role holder able to reach the interface only while already signed in.
  Nothing is stored on the person. All nine `test_sites.py` tests pass; the wider admin suites
  stay green (`test_contrib/test_contributors/test_admin.py`, 54 tests; `test_core/test_dataset/`
  admin/login/staff-marked tests, 92 tests) and `makemigrations --check --dry-run` shows only the
  pre-existing `identity`/`orbit` drift (#299, #325), nothing from this change. Commit `c3db8cd`.
- **T015**: `TestPersonAdminFields` added to `tests/test_contrib/test_contributors/test_admin.py`
  (beside the existing `TestPersonAdmin`, T126): a Community Manager's `get_fieldsets`/`get_form`
  omit `is_superuser`, `is_staff` and `password`; a superuser still gets all three; POSTing
  `is_superuser=on` through the form built for a Community Manager leaves the flag unchanged, for
  both the acting person and somebody else. Observed failing first (`poetry run pytest
  tests/test_contrib/test_contributors/test_admin.py::TestPersonAdminFields -v`): the two POST
  tests failed with the flag flipping to `True`, and the fieldset/form test failed on all three
  names still present - the "superuser still sees all three" test already passed, which is
  expected since nothing yet narrows anything. Commit `8f213fa`.
- **T016**: `UserAdmin.get_fieldsets` (`fairdm/contrib/contributors/admin.py`) drops
  `is_superuser`, `is_staff` and `password` from every fieldset for a request whose user is not
  a superuser. `get_form` additionally pops `password` from the built form's `base_fields` for a
  non-superuser: `is_superuser`/`is_staff` are plain model fields, so excluding them from
  `get_fieldsets` alone is enough - `ModelAdmin.get_form` derives its `fields` list from
  `get_fieldsets` - but `UserChangeForm.password` is a *declared* field
  (`ReadOnlyPasswordHashField`), and Django's `ModelFormMetaclass` re-adds every declared field
  to `base_fields` regardless of the fields list (`django/forms/models.py`, confirmed by reading
  the installed Django 5.2 source before writing this), so the fieldset exclusion alone would
  not have stopped it appearing in the form object. All nine `TestPersonAdminFields`/
  `TestPersonAdmin` tests pass; the full file (58 tests) stays green, and
  `makemigrations --check --dry-run` shows only the pre-existing `identity`/`orbit` drift.
  Commit `b081e31`.
- **Concern (D20)**: registering `PortalRolePermissionBackend` (T012) makes four pre-existing
  tests fail - `tests/test_core/test_dataset/test_plugins.py`'s
  `TestUpdatePageDoesNotDiscloseAPrivateDataset::test_a_model_level_holder_with_no_record_level_grant_is_refused`
  and `TestEachOfTheFourPagesGuardsAPrivateDatasetsVisibility::test_every_page_refuses_a_model_level_holder_with_no_grant_on_this_record`,
  and `tests/test_core/test_project/test_plugins.py`'s
  `TestTheOverviewGuardsAPrivateProjectsVisibility::test_every_page_refuses_a_model_level_holder_with_no_grant_on_this_record`
  and `TestUpdatePageOverHTTP::test_a_user_holding_only_model_level_change_permission_is_refused`.
  Found while running the wider dataset suite as a regression check after T012, not from a task
  in this story's own scope. Confirmed mechanical (reverting only the `AUTHENTICATION_BACKENDS`
  entry makes all four pass again) and confirmed unavoidable given both T011's unqualified
  acceptance (a direct grant answers `True` on every instance) and T017's own requirement (a
  curator reaches another team's *private* dataset by role alone). Not touched - the prohibition
  against editing a test this story did not author names exactly this situation ("mark the task
  blocked and say why"). Full write-up, evidence and the revisit condition in `decisions.md` D20.
  `tests/test_core/test_sample/` and `tests/test_core/test_measurement/` carry no equivalent test
  and are unaffected.
- **T017a**: `TestDeclaredPermissionsExist` added to `tests/test_portal_roles.py` - one test
  walking every declared permission on every role and asserting each resolves to a real
  `Permission` row. Observed failing first with exactly one gap:
  `['Data Curator: dataset.can_publish']` (`poetry run pytest
  tests/test_portal_roles.py::TestDeclaredPermissionsExist -v`) - `dataset.import_data` already
  resolved (declared in `Dataset.Meta.permissions` since migration `0010`, predating this
  feature), narrowing T017b's actual gap to `can_publish` alone, contrary to this task's own
  description ("nothing has ever declared either"). Commit (test) precedes T017b's below.
- **T017b**: `Dataset.Meta.permissions` gains `("can_publish", "Can publish dataset")`
  (`fairdm/core/dataset/models.py`); `poetry run python manage.py makemigrations dataset`
  produced exactly one migration, `0013_alter_dataset_options.py`, an `AlterModelOptions` - the
  only migration this story is permitted to produce. All fifteen `test_portal_roles.py` tests
  pass, including T017a's; `makemigrations --check --dry-run` shows only the pre-existing
  `identity`/`orbit` drift. Commit `946b666`.
- **T017**: `TestDataCuratorPortalPages`, `TestCommunityManagerPortalRights` and
  `TestAPersonHoldingTwoRolesHoldsBothSets` added to `tests/test_contrib/test_contributors/
  test_permissions.py`. A Data Curator reaches `dataset:overview-update` (HTTP 200) on another
  team's *private* dataset - the same route D20's four conflicting tests gate, confirming that
  conflict is this story's own deliverable, not a side effect - and `can_open(Edit, request,
  sample)` on its sample; the record's own model carries no `last_edited_by`/`edited_by`/
  `modified_by`/`changed_by` field. A Community Manager changes a person and an organisation,
  cannot change a dataset, cannot delete a person. A person in both roles holds both sets. All
  26 tests in the file pass (`poetry run pytest tests/test_contrib/test_contributors/
  test_permissions.py -v`). **Concern**: no test exercises "reach the import and publish plugin
  pages" - `fairdm.contrib.import_export.views` fails to import on its own
  (`ImportError: cannot import name 'FairDMModelFormMixin' from 'fairdm.views'`), confirmed by
  attempting the import directly; unrelated to this story and not named in any task, so left
  alone rather than fixed. Commit `2caea17`.
- **Bug found and fixed under T012** (surfaced while running T018's wider regression check):
  `PortalRolePermissionBackend` had no `authenticate` method, and
  `django.contrib.auth.authenticate()` inspects every configured backend's `authenticate`
  signature before calling any of them (`_get_compatible_backends`,
  `django/contrib/auth/__init__.py`), so registering the backend broke sign-in for every
  account, not only the ones this story cares about - caught by the pre-existing
  `tests/test_contrib/test_contributors/test_models.py::TestAttributionOnlyPerson::
  test_authenticate_fails_for_attribution_only_person` going red for the wrong reason
  (`AttributeError`, not the asserted refusal). Reproduced first with a new test,
  `tests/test_permissions.py::TestPortalRoleBackend::
  test_registering_the_backend_does_not_break_authenticate`, observed failing with the same
  `AttributeError`. Fixed by extending `django.contrib.auth.backends.BaseBackend`
  (`fairdm/permissions.py`), which supplies the no-op `authenticate`/`get_user` pair. All nine
  `test_permissions.py` tests pass, the previously-broken pre-existing test passes again, and
  the wider check (`test_contrib/test_contributors/test_models.py`,
  `test_contrib/test_plugins/`, `test_templatetags/`, 317 tests) is green. Commit `71d6588`.
- **T018**: five group-name decisions replaced by permission questions - `Person.is_data_admin`
  deleted (`fairdm/contrib/contributors/models.py`, `cached_property` import dropped alongside
  its only use); `check_has_edit_permission`'s `Data Administrators` branch removed
  (`fairdm/contrib/plugins/utils.py`) - the ordinary `has_perm(perm, instance)` question two
  lines below is now the only path beyond superuser/self; the `has_permission` template tag's
  branch (`fairdm/templatetags/fairdm.py`) replaced with `any(user.has_perm(perm) for perm in
  perms.split(","))`, which also subsumes the redundant explicit `is_superuser` check Django's
  own `has_perm` already grants; both `or user.is_data_admin` clauses in
  `fairdm/contrib/import_export/views.py` (lines 157, 224) removed. New tests first, observed
  failing for the right reason: `tests/test_contrib/test_plugins/test_utils.py` (new file,
  mirrors `fairdm/contrib/plugins/utils.py`) proved a group literally named
  `Data Administrators` with no real permissions granted nothing on its own (1 of 5 failed
  before the fix); `tests/test_templatetags/test_fairdm.py` gained the same proof plus a
  positive case for an actual permission holder (2 of 4 new cases failed before the fix).
  **Concern**: `import_export/views.py`'s two `check()` methods call `user.has_perm("import_data",
  instance)`/`user.has_perm("can_publish", instance)` without the `dataset.` app-label prefix
  Django's permission strings require, so neither call can ever resolve `True` through any
  backend - a pre-existing defect, not named in T018 (which named only the `is_data_admin`
  removal) and not exercised by any test because the module fails to import on its own (see the
  T017 concern above); left alone rather than fixed, since fixing it would touch behaviour this
  story was not asked to change in a module I cannot even run. All eleven new/updated tests
  pass; `makemigrations --check --dry-run` shows only the pre-existing `identity`/`orbit` drift.
  Commit `ab46649`.
- **T019**: `TestMergeAndClaimLinkViewsAdmitACommunityManager` added to
  `tests/test_contrib/test_contributors/test_admin.py` (beside the pre-existing
  `TestMergeAndClaimLinkViewsRequireSuperuser`, untouched) - a Community Manager reaches
  `merge_view` (200) and `claim_link_view` (the same already-reported `NoReverseMatch` defect
  the superuser case hits, proving the gate itself passed); a Data Curator, a rights-carrying
  role that does not hold `contributors.change_person`, is refused (403) by the view's own gate,
  not merely absent from the admin site; the action buttons are offered to a Community Manager
  in the Person changelist. Observed failing first for the right reasons (403 instead of 200,
  "did not raise NoReverseMatch", the action strings absent from the changelist). Implemented:
  a new `UserAdmin._may_manage_persons(request)` helper
  (`request.user.has_perm("contributors.change_person")`) replaces the `is_superuser` checks in
  `claim_link_view`, `merge_view`, and `get_actions` - `get_actions` too, because leaving its
  button-visibility check on `is_superuser` after the views changed would reopen the exact gap
  its own docstring (Route 2) exists to close, one route later. Both views' docstrings keep
  their original "superuser-only" reasoning and gain a line naming what supersedes it (D13's
  instruction: supersede, never rewrite). D21 in `decisions.md` records the ADR. All ten tests
  across the new and the two pre-existing classes pass unmodified; the full file (62 tests)
  stays green; `makemigrations --check --dry-run` shows only the pre-existing drift. Commit
  `455e4cf`.
