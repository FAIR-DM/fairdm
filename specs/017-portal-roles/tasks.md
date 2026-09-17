# Tasks: Portal roles and the people who hold them

**Input**: Design documents from `/specs/017-portal-roles/`

**Prerequisites**: spec.md, plan.md, research.md, decisions.md

**Revised 2026-09-16** after the design review. Thirteen findings, all verified: two critical, four
high, five medium, two low. Every one is applied below. What changed in substance: the legacy
groups are renamed rather than abandoned, the boot refusal stands down for the command that repairs
it, the Person administration form stops offering `is_superuser` to a non-superuser, two more
group-name call sites were found, the object-level fallback gains the exclusion the framework
already carries, and the Portal Administrator's permissions are named rather than left to the
implementer.

**Requirements satisfied without a dedicated task**: FR-007 (rights accumulate) and FR-008 (losing
the last rights-carrying role closes the administration interface) fall out of Django's own group
permission union and of deriving administration access rather than storing it — both are asserted
by test tasks named against them. FR-010 and FR-011 are properties of the reconcile method written
in T005 and pinned by T004.

**Requirements satisfied by adding nothing**: FR-021 forbids a visible mark on a record a curator
edited; it is met by writing no such mark, and T017 is the standing proof. FR-005 is met by the
Developer role's permission list being empty and T002 pinning it that way.

**Tests**: included. Article I requires red before green, and its URL rule requires a status-code
smoke test for the one new route. Each story's Independent Test from the specification is a test
task below, not a manual step.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: no ordering dependency on its siblings. Test tasks marked `[P]` often share a module,
  because Article X puts several `Test*` classes in one file by design.
- **[Story]**: US1–US5, or `SETUP` / `POLISH`.

## Phase 1: Setup

- [ ] T001 [SETUP] Confirm the suite is green on the branch base before any change, and record the
      commit it was green at.

## Phase 2: US1 — The roles a portal needs arrive with the framework (P1)

- [ ] T002 [P] [US1] `tests/test_portal_roles.py::TestDeclarations` — exactly four roles, named
      Portal Administrator, Data Curator, Community Manager and Developer; each one's permission set
      asserted exactly, not by subset; Developer's is empty; the Portal Administrator's holds
      neither `auth.add_group` nor `auth.change_group` nor `auth.delete_group`, so the role cannot
      edit what any role may do. Covers FR-001 to FR-005.
- [ ] T003 [US1] `fairdm/portal_roles.py` — one class, `PortalRoles`, holding the four declarations
      as class-level data with `shipped_names()`, `rights_carrying()` and `reconcile()` as its
      methods (Article XI). The module is named `portal_roles`, not `roles`, because this codebase
      already spends the bare word on contribution roles. Each declaration is a stored name, a
      translated display label, and an explicit list of `app_label.codename` permissions:
      - **Portal Administrator** — `auth.view_group`, `contributors.view_person`,
        `contributors.change_person`, and change rights over the portal's identity records.
        Membership is edited on the Person form's `groups` field, so no `auth.change_group` is
        needed and none is granted: a role that can edit groups can rewrite its own rights.
      - **Data Curator** — view/add/change/delete over `Project`, `Dataset`, `Sample`,
        `Measurement` and their attached description, date and contribution records, plus
        `import_data` and `can_publish` (research R1, five call sites).
      - **Community Manager** — view/change over `Person`, `Organization`, `Affiliation` and
        `Contribution`; no delete on `Person` (FR-004).
      - **Developer** — nothing.
- [ ] T004 [P] [US1] `tests/test_portal_roles.py::TestReconcile` — from an empty database all four
      appear with their rights; a second run changes nothing and duplicates nothing; permissions
      edited by hand are restored; the people in a role are untouched; a group the portal created
      itself is left alone; **and a database holding the three legacy groups with members ends with
      those same people in the corresponding new roles**. Covers FR-009 to FR-011, US-1 AC3, SC-002.
- [ ] T005 [US1] `PortalRoles.reconcile()`, plus a `post_migrate` receiver connected in
      `fairdm/apps.py` with no sender and a `dispatch_uid`. Before creating anything it renames the
      legacy rows in place — `Portal Administrators` → `Portal Administrator`, `Data
      Administrators` → `Data Curator`, `Developers` → `Developer` — which carries their membership
      across without a data migration, and only when the target name is not already taken. It
      tolerates a permission that does not exist yet: `INSTALLED_APPS` lists `fairdm` before the
      apps whose permissions the roles need, so early passes are incomplete and the last pass
      converges (research R5).
- [ ] T006 [US1] Delete `fairdm/fixtures/groups.json` and remove `("loaddata", "groups")` from
      `DJANGO_SETUP_TOOLS` in `fairdm/conf/settings/apps.py`. Covers FR-036.
- [ ] T007 [US1] Remove `DefaultGroups` from `fairdm/contrib/contributors/choices.py`. Relabel
      `PersonFilter.is_staff` in `fairdm/contrib/contributors/filters.py`, which currently reads
      "Portal Administrators" for a field that has never meant that.
- [ ] T008 [P] [US1] Rewrite `docs/portal-administration/roles.md` as the reference for the four
      roles and what each can do, replacing the five that never existed in the code. Reconcile
      `docs/portal-administration/managing_users_and_permissions.md` against it, and state that a
      superuser is the deployer's account while the Portal Administrator role is the portal job.
      Covers FR-037, FR-038.
- [ ] T009 [P] [US1] `CONTEXT.md` — define **portal role** and **contribution role** as distinct
      terms, name the four roles, and define **rights-carrying role**, which FR-006 and FR-008 lean
      on. Covers FR-039.
- [ ] T010 [P] [US1] Upgrade note, in the changelog and in `docs/portal-administration/`: a
      permission held through one of the four shipped roles now applies to every instance of that
      model. A permission granted any other way behaves exactly as it did before, so an upgrading
      portal has nothing to audit. *(Rewritten after the narrowing — the first version described a
      portal-wide widening that was reverted for reopening a disclosure guard.)*

## Phase 3: US2 — A role decides what its holder can actually do (P1)

- [ ] T011 [P] [US2] `tests/test_permissions.py::TestPortalRoleBackend` — a person holding a model
      permission through a role answers `True` for `has_perm(perm, instance)` on every instance of
      that model; a person without it answers `False`; a permission granted directly to the person,
      or through a group the portal invented, is refused; an anonymous user and a deactivated
      account answer `False`; a
      permission held for one model does not answer for another; `has_perm(perm)` with no object
      answers `False` from this backend, so the chain cannot recurse into it; and
      `contributors.manage_organization` is never answered by it, even for a person carrying the
      stale permission row. Covers FR-018, FR-020.
- [ ] T012 [US2] `fairdm/permissions.py::PortalRolePermissionBackend`, registered in
      `AUTHENTICATION_BACKENDS` after the existing backends. It answers an object-level question
      from the model-level permissions the person holds **through one of the four shipped roles**,
      and from no other source, never writes a row, returns `False` when `obj is None`, and carries the same explicit exclusion for
      `contributors.manage_organization` that `fairdm/core/permissions.py:44-53` already documents —
      that right comes from a current owner affiliation and from nothing else, and Django ORs
      backends so no later backend can veto a wrongly granted yes.
- [ ] T013 [P] [US2] `tests/test_contrib/test_admin/test_sites.py` — a holder of each
      rights-carrying role reaches the administration index and one changelist, both with an
      existing session and by signing in through the administration login form; a Developer-only
      holder is refused; an ordinary contributor is refused; a deactivated holder is refused.
      Covers FR-006, FR-008.
- [ ] T014 [US2] `CustomAdminSite.has_permission` and its login form accept a holder of a
      rights-carrying role (research R3). Nothing is stored on the person.
- [ ] T015 [P] [US2] `tests/test_contrib/test_contributors/test_admin.py::TestPersonAdminFields` —
      a Community Manager opening the Person change form is offered neither `is_superuser` nor
      `is_staff` nor `password`, and a POST setting `is_superuser` on their own account or on
      anybody else's leaves the flag unchanged; a superuser still sees and can set all three.
- [ ] T016 [US2] Narrow the Person administration form: `get_fieldsets`/`get_form` on the `Person`
      admin drop `is_superuser`, `is_staff` and `password` for a request whose user is not a
      superuser. Without this, `contributors.change_person` — which FR-004 requires the Community
      Manager to hold — is a route to superuser for anyone in that role.
- [ ] T017 [P] [US2] `tests/test_contrib/test_contributors/test_permissions.py` — a data curator
      can open and change another team's dataset and its samples through the portal's own pages,
      including a private one, and can reach the import and publish plugin pages; the record page
      shows no mark saying a curator changed it; a community manager can change a person and an
      organisation and cannot change that dataset and cannot delete a person; a person holding two
      roles holds both sets. Covers FR-003, FR-004, FR-007, FR-021.
- [ ] T017a [P] [US2] `tests/test_portal_roles.py::TestDeclaredPermissionsExist` — every permission
      named in any role's declaration resolves to a real `Permission` row once the database is up to
      date. Reconciliation skips a permission that does not exist, which is right for the ordering it
      runs in and wrong as a permanent state: without this test a typo, or a right nobody declares,
      is silently absent from the role forever. *(Added after US-1: `dataset.import_data` and
      `dataset.can_publish` turned out to be declared by no model at all, so the Data Curator was
      quietly not holding the two rights the import and publish plugins ask for.)*
- [ ] T017b [US2] Declare `import_data` and `can_publish` in `Dataset.Meta.permissions`, with the
      `AlterModelOptions` migration that follows. The framework's import and publish plugins have
      always asked `has_perm("import_data", instance)` and `has_perm("can_publish", instance)`, and
      nothing has ever declared either, so today only the group-name branch can answer them. T018
      cannot replace that branch with a permission question until the permission exists.

- [ ] T018 [US2] Remove the five group-name decisions, each one becoming an ordinary permission
      question: `Person.is_data_admin` (`contributors/models.py`), the `has_permission` tag's branch
      (`templatetags/fairdm.py`), `check_has_edit_permission`'s branch (`contrib/plugins/utils.py`),
      and **both** `or user.is_data_admin` clauses in `contrib/import_export/views.py` (lines 157
      and 224), which the first plan missed and which would have raised `AttributeError` on every
      import and publish page once the property was deleted. Covers FR-019.
- [ ] T019 [US2] Replace the `is_superuser` gates on `claim_link_view` and `merge_view`
      (`contrib/contributors/admin.py:440`, `:482`) with permission checks the Community Manager
      role holds. FR-004 requires the role to act on profile claims and merges, and today both are
      superuser-only by a decision recorded in those docstrings. That decision was written when the
      only alternative was "any staff member"; a named role a portal administrator grants
      deliberately is a different thing, which is the argument the superseding record must make.
      Record it in `decisions.md` for an ADR at convergence, and keep both actions out of reach of
      a person who holds no portal role.

## Phase 4: US3 — The roles cannot be lost by accident (P2)

- [ ] T020 [P] [US3] `tests/test_portal_roles.py::TestProtection` — deleting a shipped role raises
      and the role and its members survive; renaming one raises and the name is unchanged; creating
      a group is unaffected, including the creation `reconcile()` itself performs; a group the
      portal created itself deletes and renames normally. Covers FR-012 to FR-014.
- [ ] T021 [US3] `pre_delete` and `pre_save` receivers on `Group` in
      `fairdm/contrib/contributors/receivers.py`, connected in that app's `ready()` with
      `dispatch_uid`s, raising with a message that names the role and says FairDM requires it. The
      `pre_save` guard fires only for an existing row, or `reconcile()`'s own creation is refused by
      the receiver it just installed (research R6).
- [ ] T022 [P] [US3] `tests/test_contrib/test_admin/test_group_admin.py` — the delete action and
      the delete button are absent for a shipped role in the administration interface, and renaming
      one through the change form comes back as a field error naming the role rather than a 500.
- [ ] T023 [US3] A `Group` administration class registered on `CustomAdminSite` whose
      `has_delete_permission` is `False` for a shipped role and whose form rejects a change to the
      name of one, with a message. FR-012 and FR-013 require the person who clicked to be told why;
      a raising receiver alone gives them a server error. The receivers stay as the enforcement that
      holds for every other writer.
- [ ] T024 [P] [US3] `tests/test_conf/test_checks.py::TestPortalRolesPresent` — on a migrated
      database missing two roles the check returns an error naming both; with all four present it
      returns nothing; with no group table at all it returns nothing; the production boot refusal
      raises for the first case and development does not; `check --deploy` reports it in
      development; **and a production database holding data but none of the four roles still runs
      `migrate` to completion**, which is the upgrade path of every portal already running.
      Covers FR-015 to FR-017.
- [ ] T025 [US3] `check_portal_roles_present` in `fairdm/conf/checks.py`, id `fairdm.E500`, tagged
      `DeployTags.deploy` and `DeployTags.production_critical` with `deploy=True`, returning no
      error when the group table is absent or unreadable — **and standing down for the commands
      that repair the condition**. The boot refusal runs in `AppConfig.ready()`, which fires before
      `migrate` does anything, and `post_migrate` is the only thing that installs the roles: without
      the stand-down, a production portal upgrading to this version can neither start nor migrate,
      and nothing inside it can repair that (research R4).

## Phase 5: US4 — Anyone building on the framework can sign in as each role (P2)

- [ ] T026 [P] [US4] `tests/test_management/test_commands/test_create_dev_accounts.py` — creates
      exactly the five accounts of the specification's table, each in its stated role and the last
      in none; each signs in through the portal with the password `password` and meets no
      confirmation step; running it twice creates no duplicate; on the production baseline it fails
      and creates nothing; when one of the addresses already belongs to somebody it fails rather
      than adopting the account. Covers FR-023 to FR-029.
- [ ] T027 [US4] `fairdm/management/commands/create_dev_accounts.py` — creates the accounts through
      the ORM, hashing the password at run time, marking each address confirmed, and refusing on any
      resolved environment other than `development` (research R7). It ships with the package, not
      the demo. Covers FR-022.
- [ ] T028 [P] [US4] `tests/test_conf/test_checks.py::TestDevAccountsAbsent` — a production portal
      holding any of the five development addresses reports `fairdm.E501` naming them; a
      development portal holding all five reports nothing; a database with no user table reports
      nothing.
- [ ] T029 [US4] `check_dev_accounts_absent` in `fairdm/conf/checks.py`, id `fairdm.E501`, tagged
      as `fairdm.E500` is. The command's refusal guards the act of loading and not the resulting
      state: an account with a published password that reached production by a database copy, a
      dump restore or an environment variable changing under a live database is exactly the
      condition this feature already built a check for.
- [ ] T030 [P] [US4] Document the accounts and the command in `docs/portal-development/`, including
      that they exist only outside production, and point the demo's getting-started page at it.

## Phase 6: US5 — A visitor can see who runs the portal (P3)

- [ ] T031 [P] [US5] `tests/test_contrib/test_contributors/test_views/test_team.py` — a visitor who
      is not signed in gets 200; roles appear in declaration order; a person holding two roles
      appears under both; a role nobody holds is absent from the response; a deactivated holder is
      absent; no email address appears anywhere in it; contribution roles do not appear; the page
      holds its query count as the number of holders grows. Covers FR-030 to FR-035.
- [ ] T032 [US5] The view, template and route in `fairdm/contrib/contributors` beside `people-list`
      and `organization-list`. Each person is their name and a link to their public profile.
- [ ] T033 [US5] Add the page to the `Community` group in `fairdm/menus/menus.py`, beside People
      and Organizations, with an icon from the existing set. Covers FR-032.
- [ ] T034 [P] [US5] Document the page in the administrator guide: what it shows, and that putting
      somebody in a role is what puts them on it.

## Phase 7: Polish

- [ ] T035 [POLISH] Full suite, `pre-commit run --all-files`, and `makemigrations --check` clean.
      This feature's only migration is T017b's `AlterModelOptions` on `Dataset`, which declares two
      permissions the framework has always asked for; any other migration appearing is a defect
      rather than an output. Two pending migrations on `identity` and `orbit` are pre-existing drift
      (#299, #325) and are not this feature's to fix.
- [ ] T036 [POLISH] Simplification pass over the feature diff, inside its blast radius only.

## Watch items for implementers

Recorded from the design review; none of them forces a task, and each is cheaper to know than to
rediscover.

- `fairdm/menus/menus.py:104` gates the Admin Guide link on `user_is_staff`, so a role holder who is
  not staff loses that link once administration access is derived. There is no in-portal link to the
  administration interface at all today; if T033 is touching this file anyway, that is the moment.
- The `has_permission` template tag has no call site in this repository and reads a `user_permissions`
  context key nothing sets. It is still public template surface for consuming portals, so T018
  changes it rather than deleting it.
- The Data Curator's `Sample` and `Measurement` permissions are largely redundant:
  `SamplePermissionBackend` and `MeasurementPermissionBackend` already derive those from
  `change_dataset`/`delete_dataset`. Granting them anyway is the honest declaration of what the role
  holds and does not depend on that derivation staying as it is.
- The administration fixture-upload view carries its own `superuser_required`, and django-hijack
  defaults to superusers only, so widening `has_permission` opens neither.
- `fairdm/contrib/contributors/views/` and `templates/` already exist; the plan's structure diagram
  marked them new.

## Dependencies

- T003 blocks everything after it: every later task reads the declarations.
- T005 blocks T020, T022 and T024 — nothing can be protected or checked for until it is installed.
- T012 and T014 block T018: the replacements must work before the group-name branches go, and T017b
  blocks it too — the import and publish branches cannot become permission questions until the
  permissions exist.
- T016 lands with or before T017, because T017 signs in as a Community Manager.
- T027 blocks T028. T032 blocks T033.
- T035 and T036 run last.

## Boundary

Nothing in this plan builds per-record rights for a record's creator or for a project's members
(that is issue #345), changes how visibility is enforced (R14), routes the contact form, or builds
an announcement capability. No task should be read as licence to start one.
