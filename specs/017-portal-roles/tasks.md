# Tasks: Portal roles and the people who hold them

**Input**: Design documents from `/specs/017-portal-roles/`

**Prerequisites**: spec.md, plan.md, research.md, decisions.md

**Requirements satisfied without a dedicated task**: FR-007 (rights accumulate) and FR-008 (losing
the last rights-carrying role closes the administration interface) fall out of Django's own group
permission union and of deriving administration access rather than storing it — both are asserted
by test tasks named against them, neither needs code of its own. FR-010 and FR-011 are properties
of the reconcile function written in T005 and pinned by T004.

**Requirements satisfied by adding nothing**: FR-021 forbids a visible mark on a record a curator
edited. It is met by writing no such mark, and T014 is the standing proof. FR-005 is met by the
Developer role's permission list being empty and T002 pinning it that way.

**Tests**: included. Article I requires red before green, and Article I's URL rule requires a
status-code smoke test for the one new route. Each story's Independent Test from the specification
is a test task below, not a manual step.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: no ordering dependency on its siblings. Test tasks marked `[P]` often share a module,
  because Article X puts several `Test*` classes in one file by design.
- **[Story]**: US1–US5, or `SETUP` / `POLISH`.

## Phase 1: Setup

- [ ] T001 [SETUP] Confirm the suite is green on the branch base before any change, and record the
      commit it was green at.

## Phase 2: US1 — The roles a portal needs arrive with the framework (P1)

- [ ] T002 [P] [US1] `tests/test_roles.py::TestDeclarations` — exactly four roles, named Portal
      Administrator, Data Curator, Community Manager and Developer; each one's permission set
      asserted exactly, not by subset; Developer's is empty. Covers FR-001 to FR-005.
- [ ] T003 [US1] `fairdm/roles.py` — declare the four roles: stored name, translated display label,
      and an explicit list of `app_label.codename` permissions per role. The Data Curator's list
      covers `Project`, `Dataset`, `Sample`, `Measurement` and their attached description, date and
      contribution records (research R9). The Community Manager's covers `Person`, `Organization`,
      `Affiliation` and `Contribution`, with no delete on `Person` (FR-004). Expose the shipped
      names and the rights-carrying subset as module-level helpers.
- [ ] T004 [P] [US1] `tests/test_roles.py::TestReconcile` — from an empty database all four appear
      with their rights; a second run changes nothing and duplicates nothing; permissions edited by
      hand are restored; the people in a role are untouched; a group the portal created itself is
      left alone. Covers FR-009 to FR-011.
- [ ] T005 [US1] `reconcile_portal_roles()` in `fairdm/roles.py`, plus a `post_migrate` receiver
      connected in `fairdm/apps.py` with no sender and a `dispatch_uid`. It tolerates a permission
      that does not exist yet — `INSTALLED_APPS` lists `fairdm` before the apps whose permissions
      the roles need, so early passes are incomplete and the last pass converges (research R5).
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
      terms and name the four roles. Covers FR-039.

## Phase 3: US2 — A role decides what its holder can actually do (P1)

- [ ] T010 [P] [US2] `tests/test_permissions.py::TestPortalRoleBackend` — a person holding a model
      permission through a role answers `True` for `has_perm(perm, instance)` on every instance of
      that model; a person without it answers `False`; a permission granted directly to the person
      behaves the same way; an anonymous user and a deactivated account answer `False`; a
      permission the person holds for one model does not answer for another. Covers FR-018, FR-020.
- [ ] T011 [US2] `fairdm/permissions.py::PortalRolePermissionBackend`, registered in
      `AUTHENTICATION_BACKENDS` after the existing backends. It answers an object-level question
      from the model-level permissions the person holds and never writes a row (research R2).
- [ ] T012 [P] [US2] `tests/test_contrib/test_admin/test_sites.py` — a holder of each
      rights-carrying role reaches the administration index and one changelist, signing in through
      the administration login as well as with an existing session; a Developer-only holder is
      refused; an ordinary contributor is refused; a deactivated holder is refused. Covers FR-006,
      FR-008.
- [ ] T013 [US2] `CustomAdminSite.has_permission` and its login form accept a holder of a
      rights-carrying role (research R3). Nothing is stored on the person.
- [ ] T014 [P] [US2] `tests/test_contrib/test_contributors/test_permissions.py` — a data curator
      can open and change another team's dataset and its samples through the portal's own pages,
      including a private one; the record page shows no mark saying a curator changed it; a
      community manager cannot change that dataset; a person holding two roles holds both sets.
      Covers FR-003, FR-007, FR-021.
- [ ] T015 [US2] Remove the three group-name decisions: `Person.is_data_admin`
      (`contributors/models.py`), the `has_permission` tag's branch
      (`templatetags/fairdm.py`), and `check_has_edit_permission`'s branch
      (`contrib/plugins/utils.py`). Each becomes an ordinary permission question. Covers FR-019.
- [ ] T016 [P] [US2] `tests/test_contrib/test_contributors/test_permissions.py::TestCommunityManager`
      — can change a person and an organisation and act on a profile claim and a merge; cannot
      delete a person; cannot change a project, dataset, sample or measurement. Covers FR-004.

## Phase 4: US3 — The roles cannot be lost by accident (P2)

- [ ] T017 [P] [US3] `tests/test_roles.py::TestProtection` — deleting a shipped role raises and the
      role and its members survive; renaming one raises and the name is unchanged; the same attempt
      through the administration interface's own delete view is refused; a group the portal created
      itself deletes and renames normally. Covers FR-012 to FR-014.
- [ ] T018 [US3] `pre_delete` and `pre_save` receivers on `Group` in
      `fairdm/contrib/contributors/receivers.py`, connected in that app's `ready()` with
      `dispatch_uid`s, raising with a message that names the role and says FairDM requires it
      (research R6).
- [ ] T019 [P] [US3] `tests/test_conf/test_checks.py::TestPortalRolesPresent` — on a migrated
      database missing two roles the check returns an error naming both; with all four present it
      returns nothing; with no group table at all it returns nothing; the production boot refusal
      raises for the first case and development does not; `check --deploy` reports it in
      development. Covers FR-015 to FR-017.
- [ ] T020 [US3] `check_portal_roles_present` in `fairdm/conf/checks.py`, id `fairdm.E300`, tagged
      `DeployTags.deploy` and `DeployTags.production_critical` with `deploy=True`, returning no
      error when the group table is absent or unreadable (research R4).

## Phase 5: US4 — Anyone building on the framework can sign in as each role (P2)

- [ ] T021 [P] [US4] `tests/test_management/test_create_dev_accounts.py` — creates exactly the five
      accounts of the specification's table, each in its stated role and the last in none; each
      signs in through the portal with the password `password` and meets no confirmation step;
      running it twice creates no duplicate; on the production baseline it fails and creates
      nothing; when one of the addresses already belongs to somebody it fails rather than adopting
      the account. Covers FR-023 to FR-029.
- [ ] T022 [US4] `fairdm/management/commands/create_dev_accounts.py` — creates the accounts through
      the ORM, hashing the password at run time, marking each address confirmed, and refusing on
      any resolved environment other than `development` (research R7). It ships with the package,
      not the demo. Covers FR-022.
- [ ] T023 [P] [US4] Document the accounts and the command where a portal developer will look for
      them (`docs/portal-development/`), including the warning that they exist only outside
      production, and point the demo's own getting-started page at it.

## Phase 6: US5 — A visitor can see who runs the portal (P3)

- [ ] T024 [P] [US5] `tests/test_contrib/test_contributors/test_views/test_team.py` — a visitor who
      is not signed in gets 200; roles appear in declaration order; a person holding two roles
      appears under both; a role nobody holds is absent from the response; no email address appears
      anywhere in it; contribution roles do not appear; the page holds its query count as the
      number of holders grows. Covers FR-030 to FR-035.
- [ ] T025 [US5] The view, template and route in `fairdm/contrib/contributors` beside
      `people-list` and `organization-list`. Each person is their name and a link to their public
      profile.
- [ ] T026 [US5] Add the page to the `Community` group in `fairdm/menus/menus.py`, beside People
      and Organizations, with an icon from the existing set. Covers FR-032.
- [ ] T027 [P] [US5] Document the page in the administrator guide: what it shows, and that putting
      somebody in a role is what puts them on it.

## Phase 7: Polish

- [ ] T028 [POLISH] Full suite, `pre-commit run --all-files`, and `makemigrations --check` clean —
      this feature adds no model change, so a migration appearing is a defect, not an output.
- [ ] T029 [POLISH] Simplification pass over the feature diff, inside its blast radius only.

## Dependencies

- T003 blocks everything after it: every later task reads the declarations.
- T005 blocks T017 and T019 — nothing can be protected or checked for until it is installed.
- T011 and T013 block T015: the replacements must work before the group-name branches go.
- T025 blocks T026.
- T028 and T029 run last.

## Boundary

Nothing in this plan builds per-record rights for a record's creator or for a project's members
(that is issue #345), changes how visibility is enforced (R14), routes the contact form, or builds
an announcement capability. No task should be read as licence to start one.
