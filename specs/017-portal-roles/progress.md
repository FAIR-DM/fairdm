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
- **T011 (FIX-1)**: narrowed `PortalRolePermissionBackend.has_perm` from "any model-level
  permission the person holds" to "a model-level permission held through membership of one of
  the four shipped portal roles" (`fairdm/permissions.py`), resolving the D20 collision. Ran
  the four D20-named tests first and watched them fail (red, for the reported reason - 200
  instead of 404/403). `tests/test_permissions.py` updated: its own acceptance test for the wide
  reading rewritten from "a direct grant answers the same way" (True) to "a direct grant is
  refused" (False); a new test proves a group the portal invented itself is refused the same
  way; the existing group-based test renamed onto an actual shipped role (`Data Curator`) rather
  than an arbitrary group name, since the whole point of the narrowing is that the group's name
  matters now. Implementation: `user_obj.groups.filter(name__in=PortalRoles.shipped_names(),
  permissions__content_type__app_label=..., permissions__codename=...).exists()`, replacing the
  `user_obj.has_perm(perm)` call - no query against `user_permissions` or non-shipped groups.
  Module and class docstrings rewritten to state the narrower rule and D20's reasoning for it.
  `CHANGELOG.md:47` and `docs/portal-administration/roles.md:90-95` rewritten: no longer tell an
  upgrading portal to audit permissions granted outside the four roles, since under the narrower
  rule those grants are unchanged from before this feature. D22 in `decisions.md` records the
  ADR and supersedes D20. All ten tests in `tests/test_permissions.py` pass; the four D20 tests
  pass unmodified; the full `test_dataset`/`test_project` plugin files (150 tests) stay green.
  Commits `fa8e0f2`, `766e570`.
- **T011 (FIX-1) follow-up**: the full-suite run surfaced a regression the narrower
  implementation introduced - `perm.split(".", 1)` raises `ValueError` for a bare codename with
  no app label (e.g. `user.has_perm("change_project", project)`, the convention
  `tests/test_core/test_project/conftest.py`'s guardian-backed fixtures use), where the prior
  `user_obj.has_perm(perm)` call had silently answered `False` instead of raising. Reproduced
  first with a new test asserting `False` rather than a raise
  (`test_a_permission_string_with_no_app_label_answers_false_rather_than_raising`), watched it
  fail with the same `ValueError`, then guarded: `if "." not in perm: return False` before the
  split. `tests/test_core/test_project/test_factories.py`'s three previously-green tests (broken
  by the unguarded split) pass again; `tests/test_permissions.py` (11 tests) and the
  `test_dataset`/`test_project` plugin files (157 tests together) stay green. Commit `bc5732d`.

## US-3 implementation begins on `017-portal-roles-us3`, cut from `5c0ed51`

- **T020**: `tests/test_portal_roles.py::TestProtection` (8 tests) written and observed failing
  for the right reason (`Failed: DID NOT RAISE ValidationError`) before either receiver existed.
  Covers: deleting a shipped role raises and it and its members survive; the message names the
  role and says FairDM requires it, for both delete and rename; renaming one raises and the name
  is unchanged; re-saving a shipped role with its name unchanged is unaffected; creating a group
  is unaffected; `PortalRoles.reconcile()`'s own re-creation of a role removed by raw SQL is
  unaffected by the receiver it just installed; a group a portal created for itself deletes and
  renames normally. A `_delete_group_by_raw_sql` helper removes a group (and its
  `auth_group_permissions` rows, or SQLite's foreign-key check fails at teardown) without going
  through the ORM, per research R6. `delete()`/`save()` calls expected to raise are wrapped in
  their own `transaction.atomic()` so the receiver's exception - raised inside the atomic block
  `delete()`/`save()` already opens - doesn't mark the surrounding test's own transaction broken
  for every query after it. Commit `2b34140`.
- **T021**: `refuse_shipped_role_deletion` and `refuse_shipped_role_rename` added to
  `fairdm/contrib/contributors/receivers.py`, connected as `pre_delete`/`pre_save` on `Group` in
  `ContributorsConfig.ready()` with `dispatch_uid`s. The rename guard checks
  `instance._state.adding` first (true only for a `Group` that has never been saved) and returns
  without raising, so a portal's own new group and `PortalRoles.reconcile()`'s
  `Group.objects.get_or_create()` creation branch are both unaffected; for an existing row it
  compares the name **stored in the database** against `instance.name` (not the shipped-role list
  against `instance.name` alone), so a rename *away* from a shipped name is still caught and an
  unchanged re-save is not refused. `TestProtection` (T020) green. Commit `9ba8ff8`.
  - **Known regression, not fixed**: connecting `pre_delete` for `Group` disables Django's
    collector fast-delete path, so a bulk `Group.objects.all().delete()` now sends `pre_delete`
    per row and is refused once it reaches a shipped role - exactly the setup step
    `tests/test_portal_roles.py::TestReconcile` (5 tests, US-1) and
    `tests/test_apps.py::TestPortalRolesReconciliation` (2 tests, US-1) both use to reset state
    before testing `reconcile()`/`migrate`. Confirmed by running both classes after T021 landed:
    all seven fail with `ValidationError` naming a shipped role. Neither file is touched - this
    story's brief prohibits modifying a test authored elsewhere and instructs reporting the task
    blocked instead. See D23 and `report-us3.json`.
- **T022**: `tests/test_contrib/test_admin/test_group_admin.py` written and observed failing for
  the right reason before the admin class existed: no delete button on a shipped role's change
  form (the default `GroupAdmin` offers one), the delete view itself not refusing (200 instead of
  403), and the rename POST producing T021's uncaught `ValidationError` - a 500, with no
  admin-side explanation yet. Two tests for a group the portal made itself, and one for
  re-saving a shipped role with its name unchanged, already passed against the stock admin and
  stayed green throughout, proving the new class doesn't over-reach. Commit `7482d7c`.
- **T023**: `ShippedRoleGroupAdmin` and `ShippedRoleGroupForm` added to
  `fairdm/contrib/admin/admin.py` (the file this repository already uses for a third-party app's
  admin overrides, per its own docstring about Waffle). `admin.site.unregister(Group)` then
  `@admin.register(Group)` replaces `django.contrib.auth.admin.GroupAdmin` on the same site
  object `FairDMAdminSite`'s `default_site` substitution already made `CustomAdminSite` -
  `django.contrib.auth`'s own `admin.py` registers first (it is listed earlier in
  `INSTALLED_APPS`), so the unregister has something to remove.
  `has_delete_permission` returns `False` for a shipped role's object, which Django's admin reads
  for both the change-form delete button and the bulk `delete_selected` action - no extra action
  handling was needed for either. `ShippedRoleGroupForm.clean_name` compares the stored name
  (queried directly, not read off `self.instance` before validation) against the submitted one
  and attaches a field error, so a rename never reaches T021's receiver through this route at
  all - it stays the backstop for every other writer (research R6). `TestProtection` (T020) and
  `TestShippedRoleDeleteProtection`/`TestShippedRoleRenameProtection` (T022) all green. Commit
  `9d89ba2`.
- **T024**: `tests/test_conf/test_checks.py::TestPortalRolesPresent` written and observed failing
  for the right reason (`ImportError: cannot import name 'check_portal_roles_present'`) before
  T025 existed. Covers the check function directly (two missing roles named in one error, all
  four present returns nothing, an absent or unreadable group table returns nothing for
  `ProgrammingError`/`OperationalError`, stands down when `sys.argv` contains `migrate` and does
  not for an unrelated command), `check --deploy` reporting the condition regardless of
  environment (`call_command("check", deploy=True)`, in-process, `db` fixture), and the check's
  own registration carrying exactly the `deploy`/`production_critical` tags and only being
  visible with `include_deployment_checks=True`. The two live-production-boot scenarios in the
  brief's given/when/then (refuses and names them; `migrate` still completes) are not covered by
  a subprocess test: doing that for real needs a PostgreSQL connection (confirmed unreachable in
  this environment - no docker, no `psql`, port 5432 closed), and SQLite cannot stand in because
  `fairdm.E101` fires unconditionally for any non-development environment and
  `_check_production_configuration` does not consult `SILENCED_SYSTEM_CHECKS` (confirmed by
  trying exactly that and reading the raised error). The registration test plus
  `TestPortalRolesReconciliation` (`tests/test_apps.py`, proves `migrate` installs the roles
  against this suite's real database) together cover the wiring without one. Commit `1a2ca33`.
- **T025**: `check_portal_roles_present` added to `fairdm/conf/checks.py`, id `fairdm.E300`,
  tagged `DeployTags.deploy`/`DeployTags.production_critical` with `deploy=True`. Stands down by
  checking `_MIGRATE_COMMAND_NAME in sys.argv` before querying anything (D11). First version
  caught only `OperationalError`/`ProgrammingError`; running the wider suite surfaced four
  pre-existing `tests/test_apps.py` production-boot tests newly crashing with an uncaught
  `ImproperlyConfigured` traceback instead of their expected clean `SystemCheckError` - a
  `DATABASE_URL`-absent portal (`fairdm.E100`'s own case) composes a `DATABASES` entry with no
  resolvable engine, which raises that instead of a `django.db.utils` error the moment any query
  runs. Added to the except clause, and to `TestPortalRolesPresent` as its own test. `TestPortalRolesPresent`
  (T024) all green. Commit `3a08819`.
  - **Known ID collision, not resolved**: `fairdm.E300` is already `check_celery_broker`'s id
    (`fairdm/conf/checks.py`, pre-existing, not tagged `production_critical` so it never reaches
    the same boot-refusal aggregation) - every design doc in this spec (plan.md, decisions.md,
    tasks.md) assigns `E300` to the portal-roles check with no apparent awareness two checks
    would then share one id. `manage.py check --deploy` output and any future
    `SILENCED_SYSTEM_CHECKS` entry naming `fairdm.E300` cannot distinguish the two. Not fixed -
    renumbering either check is outside T020-T025's scope. See `report-us3.json`.
  - **Known regression, not fixed**: this is the first `production_critical` check that queries
    the database rather than reading settings, and six pre-existing tests in
    `tests/test_conf/test_checks.py` (`TestCheckCommandIntegration` x2, `TestDeployCommand` x4
    parametrised) run the full `check --deploy` pipeline with no database fixture enabled -
    reasonable when nothing registered under `deploy=True` ever needed one. Confirmed by running
    both classes in isolation: all six fail with `RuntimeError: Database access not allowed`.
    Neither file is touched, per this story's prohibition. See D24 and `report-us3.json`.

## FIX-2 (T025 renumbering and regression settlement)

- **T025 renumbering**: `check_portal_roles_present`'s id changed from `fairdm.E300` to
  `fairdm.E500` - `fairdm/conf/checks.py` numbers by hundreds (E0xx security, E1xx database, E2xx
  cache, E3xx celery, E4xx translation) and `E300` was already `check_celery_broker`'s, held since
  Spec 003, long before this feature. Updated `fairdm/conf/checks.py` (both the docstring and the
  registered `id=`), the two `TestPortalRolesPresent` assertions in `tests/test_conf/test_checks.py`
  that named the old id, and every reference in `tasks.md`, `plan.md` and `decisions.md` (D11, D16)
  - including D16's `fairdm.E301` for the not-yet-built `check_dev_accounts_absent` (T029), which
  collides with `check_celery_async`'s id the same way and is renumbered to `fairdm.E501` so the
  next story does not inherit the same bug. `report-us3.json` and `design-review-findings.json`
  are historical records of the collision as found and are left as written. Verified: narrow scope
  (`TestPortalRolesPresent` and `TestCeleryChecks`) green, 13 passed, ids no longer collide. See
  D26.
- **T025 database tolerance (D24)**: extended `check_portal_roles_present`'s except clause to
  also catch `RuntimeError`, so a test harness that refuses database access outright (raised by
  pytest-django's own safeguard for a test with no `db` fixture) is tolerated exactly like an
  absent or unreadable group table. Added `RuntimeError` to
  `test_an_absent_or_unreadable_group_table_returns_nothing`'s existing parametrisation rather
  than writing a new test, since it already asserts this same tolerance for two sibling
  `django.db.utils` exceptions - observed red for the right reason (the harness's own
  `RuntimeError: no such table: auth_group`, from the mock, before the except clause changed).
  `TestCheckCommandIntegration` (2 tests) and `TestDeployCommand` (4 parametrised) - the six D24
  named - pass unchanged; `tests/test_conf/test_checks.py` is 56 passed. See D27.
- **T021 guard fixture (D23)**: added `disconnect_shipped_role_guard` to `tests/conftest.py`, a
  fixture that disconnects `refuse_shipped_role_deletion`/`refuse_shipped_role_rename` from
  `Group`'s `pre_delete`/`pre_save` by `dispatch_uid` for a test's duration and reconnects them in
  a `finally` block. The five `TestReconcile` tests (`tests/test_portal_roles.py`) and the two
  `TestPortalRolesReconciliation` tests (`tests/test_apps.py`) D23 named now request it explicitly
  as a fixture parameter; setup is otherwise unchanged and no assertion in any of the seven
  changed. `TestProtection` does not request it and still passes on its own
  (`tests/test_portal_roles.py::TestProtection`, 8 passed), proving a shipped role cannot be
  deleted or renamed with the guard connected. `tests/test_portal_roles.py` (23 passed) and
  `tests/test_apps.py` (24 passed) both green, run together and in isolation. See D28.

## US-4 implementation begins on `017-portal-roles-us4`, cut from `acf79bf`

- **T026**: `tests/test_management/test_commands/test_create_dev_accounts.py` added, seven tests
  covering FR-023 to FR-029 - the five accounts and their stated roles, signing in with the shared
  password and no confirmation step, idempotent re-runs, refusing rather than adopting an address
  that already belongs to somebody, and refusing on the production baseline without touching the
  database. Observed red for the right reason: `ModuleNotFoundError:
  fairdm.management.commands.create_dev_accounts` at collection, since T027 had not been written
  yet. Commit `1c094dd`.
- **T027**: `fairdm/management/commands/create_dev_accounts.py` added. Creates the five accounts
  through the ORM (D7), hashing the shared password at run time, marking each address confirmed
  via an `allauth.account.models.EmailAddress` row so mandatory verification lets the account
  straight in, and refusing on any resolved environment outside
  `fairdm.apps.NON_PRODUCTION_ENVIRONMENTS` before the transaction that creates anything even
  opens. All seven T026 tests pass unchanged. Commit `0d4c5b8`.
  - **Probe, not just read**: before trusting the production-refusal test, temporarily removed the
    environment check and re-ran it. It failed with an uncaught `django.db.utils.OperationalError`
    (`connection to server at "localhost" ... Connection refused`) from the command's own query,
    confirming the assertion that stderr carries no `OperationalError` is a real guard against the
    command reaching the database before refusing, not a tautology. Reverted before continuing.
  - **Identity check for FR-029**: an existing account is treated as "ours" (safe to leave
    unchanged) only when its `first_name`/`last_name` match the specification's table for that
    address exactly; any other existing holder of the address fails the whole run rather than
    being adopted. See D29.
- **T028**: `TestDevAccountsAbsent` added to `tests/test_conf/test_checks.py`, ten tests covering
  a production portal holding one or all five development addresses (named together in one
  error), a development portal holding all five reporting nothing, the same database tolerance
  `check_portal_roles_present` carries (an unreadable table across three exception classes, and a
  database Django cannot resolve an engine for), registration under the portal-roles check's own
  tags, and that `fairdm.E501` appears nowhere else in the file. Observed red for the right
  reason: all ten fail on `ImportError: cannot import name 'check_dev_accounts_absent'`, since T029
  had not been written yet. Commit `8f78868`.
- **T029**: `check_dev_accounts_absent` added to `fairdm/conf/checks.py`, id `fairdm.E501`, tagged
  `DeployTags.deploy`/`DeployTags.production_critical` with `deploy=True` - the same tags D26
  reserved this id for. Unlike `check_portal_roles_present`, this check resolves the environment
  itself rather than relying only on `FairDMConfig._check_production_configuration()`'s boot-time
  stand-down, because `manage.py check --deploy` runs every `deploy=True` check regardless of
  environment (FR-015) and a development portal running it explicitly must still see nothing.
  Reuses `fairdm.management.commands.create_dev_accounts.DEV_ACCOUNT_EMAILS` rather than
  redeclaring the five addresses, imported inside the function body - a module-level import would
  be circular the moment `fairdm.apps` (which imports this module at load time) is reached through
  it. All ten T028 tests pass; `tests/test_conf/test_checks.py` is 66 passed and `tests/test_apps.py`
  (production boot) is unaffected at 16 passed. Commit `26619e3`.
  - **Probe, not just read**: temporarily removed the environment gate and re-ran
    `test_a_development_portal_holding_all_five_reports_nothing` - it failed (all five accounts
    reported present), confirming the gate is load-bearing and not redundant with the boot-time
    stand-down. Reverted before continuing.
- **T030**: `docs/portal-development/development_accounts.md` added - the command, the five-account
  table straight from the specification's *Key entities* table, the shared password, and a warning
  covering both the command's own refusal and what `fairdm.E501` guards against. Added to the "How
  to" toctree in `index.md` beside `portal_roles.md`. Cross-linked both ways: `portal_roles.md`
  points here for signing in as each role, and `getting_started.md`'s tip - previously only
  `createsuperuser` - now distinguishes the deployer's superuser from the four portal roles and
  points at this page. `docs/` is excluded from the lint gate (`.pre-commit-config.yaml`), so no
  lint scope applies. Commit `0e60bad`.
