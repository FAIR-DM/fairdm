# Tasks: Contributors and access are managed on every core record

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [sketch.md](sketch.md)

**Tests first**: in every story the test tasks come first and are seen to fail before the code
that makes them pass is written. Page tests open and submit the real page through the Django test
client, once for each kind of account the scenario names, and assert on the response and on what
is stored afterwards. Access rules are tested through `user.has_perm` and the functions in
`access.py`. Layout, width, stacking and copy get no tests. No query-count assertions except where
a task names one.

**The approved prototype** is on this branch. Its templates and components are kept as they are.
A task replaces the code behind a page and changes a template only to follow a context name.

**Existing tests** that assert guardian grants on projects, datasets, samples or measurements
describe behaviour this feature replaces. Where one does, it is updated in the task that changes
the behaviour, and the change is named in `progress.md`.

**Format**: `[ID] [Story] Description`.

**Story order**: US1, US2, US3, US4, US5, US6, US7, one after another, each from the previous
story's accepted commit.

## Phase 1: US-1, a research team credits the people and organizations behind any record (P1)

This story also lays the ground the others stand on: the stored level, the functions that read it,
and the service that changes contributors.

- [ ] T001 [US1] `tests/test_contrib/test_contributors/test_access.py`, new. `TestRecordsAbove`:
  project, dataset with and without a project, sample, measurement in a different dataset from its
  sample. `TestLevelOf`: none; own level; a level from the dataset; from the project; the higher
  of two; a visitor; an inactive user. `TestManagers`: counts a manager on the record and one
  above; leaves out a person who cannot sign in. `TestCanManage`: a manager; an editor; a person
  holding `change_dataset` for the whole portal; a superuser; a visitor. `TestPersonCanSignIn`
  in `test_models.py`: active and claimed; active and signed in but not marked claimed; never
  signed in; inactive.
- [ ] T002 [US1] `tests/test_contrib/test_contributors/test_services/test_crediting.py`, new.
  `TestAdd`: placed last; a person gets the view level; an organization gets none; a duplicate is
  refused (`duplicate`); a superuser is refused with a validation error and not an exception.
  `TestUpdate`: roles saved; a role from another record type's group
  refused (`role_not_offered`); changing roles leaves the level alone (FR-040). `TestRemove`: the
  contribution and the person's level are gone.
- [ ] T003 [US1] `tests/test_contrib/test_contributors/test_plugins/test_shared.py`,
  new. `TestContributorsTab`, for a project, a dataset, a registered sample type and a registered
  measurement type: the tab opens and lists people and organizations separately (scenario 1); a
  manager is offered the two add pages (2); a reader and a visitor are offered no controls and are
  refused add, edit, remove and move on GET and POST with nothing changed (10, SC-005); an empty
  record shows both lists empty and still offers both add pages to a manager (12); the search
  narrows both lists. `TestAddFromPortal`: a person and an organization already in the portal are
  added and the manager is sent to the edit page (3, FR-020); one already listed cannot be added
  (6). `TestEditRoles`: only the record type's roles are offered and saved (4, 5); no role is
  allowed (8). `TestRemoveContributor`: confirmation first, then removed (7).
- [ ] T004 [US1] Implement to make T001 to T003 pass (plan D1, D2 without the backend, D3 `add`,
  `update` roles, `remove`, D5 for the list, portal add, edit roles and remove):
  - `ContributionLevel` and `Contribution.level`, with the schema migration
  - `access.py` rebuilt on the field as `RecordAccess`, and the "can sign in" method on `Person`,
    which `Person.is_editable_by` now uses
  - `services/crediting.py`: `Crediting` with `add`, `update`, `remove`
  - `plugins/shared.py`: the list, the portal tab of both add pages, the roles part of the edit
    page and the remove page, over the service
  - `RecordOverviewPlugin` sets `people_url` for all four record types (FR-008)
  - `demo/seed/contributors.py`, `demo/seed/common.py` and `demo/seed/projects.py` set levels
    through `Crediting` in place of guardian rows
  - the two existing tests that pin the old tab are brought up to date:
    `tests/test_contrib/test_plugins/test_registration.py::TestExtraViews::test_the_shipped_contribution_views_address_their_target`
    and `tests/test_core/test_dataset/test_plugins.py::TestRetiredManagementPages::test_the_dataset_menu_carries_one_entry`
- [ ] T005 [US1] Documentation: a page on crediting a record under `docs/user-guide/`, linked from
  its index, covering the tab, adding from the portal, roles and removing; the tab, `access.py`'s
  public functions and `services/crediting.py` in `docs/portal-development/contributors.md`,
  including that a registered sample or measurement type gets the tab with no configuration and
  how a page asks whether a person may view, edit or manage a record (FR-068); a changelog entry.
  The docs check passes.

## Phase 2: US-2, a person is credited from where they were at the time (P1)

- [ ] T006 [US2] `test_services/test_crediting.py`: `TestCreditedFrom`. Adding a person with an
  organization lists the organization once (FR-025, scenario 10); adding a person with no
  organization stores none even when they have a primary affiliation (FR-024); deleting an
  organization from the portal leaves the person on the record credited from none; `update` changes it; the
  organization stays when its last person leaves or is credited from elsewhere, and can then be
  removed (FR-027); removing an organization people are credited from is refused (`credited_from`)
  and names them (FR-026).
- [ ] T007 [US2] `test_plugins/test_shared.py`: `TestAffiliationChoice`. After a person
  with affiliations is chosen, their primary affiliation is selected and the others, past and
  present, are offered (scenario 1); another organization and none can be chosen (2); an
  organization not in the portal is made from its name; an empty name is refused on the field. The
  tab shows the person with the chosen organization (3), with none when none was chosen whatever
  the profile says (5, FR-024), and unchanged after the person's primary affiliation changes (4,
  SC-008). The edit page offers the same choice with the current one selected (6).
  `TestOrganizationRemoval`: no removal offered for an organization people are credited from; a
  direct request is refused with nothing changed and the people named (7); a standalone one is
  removed (8).
- [ ] T008 [US2] `tests/test_contrib/test_contributors/test_components.py`, new: given a contribution with no organization, `c-contributor.item` and
  `c-contributor.card.person` show none; given a person, they show the primary organization as
  before (plan D10).
- [ ] T009 [US2] Implement to make T006 to T008 pass (plan D3 organization handling, D5
  `AffiliationChoice`, D7 `SET_NULL`, D10): `Crediting`, the form field group, the edit and
  portal-add pages, the remove page's refusal, the two components, the migration. Delete
  `Contribution.set_default_affiliation`.
- [ ] T010 [US2] Documentation: how the organization a person is credited from is chosen, and why
  it does not follow their profile, in the user guide page from T005; `CONTEXT.md` says a
  contribution carries the organization a person is credited from (FR-069, in part).

## Phase 3: US-3, someone who is not in the portal yet can be credited (P2)

- [ ] T011 [US3] `tests/test_contrib/test_contributors/test_services/test_registries.py`, new,
  with `requests.get` replaced. `TestSearchOrcid`: by name; by iD; results carry what the template
  reads; a record with no name is left out; more results than the limit sets the flag; a timeout,
  a connection error and a 500 each raise `RegistryUnavailable`; a malformed identifier makes
  no request. The replaced responses are built from a recorded real response of each endpoint. `TestSearchRor`: the same, with a
  withdrawn organization left out. `TestProfileFromRegistry`: makes a person with the ORCID iD and
  no account, or an organization with the ROR ID (scenarios 7, 8); returns the existing profile
  when the identifier is already held (9).
- [ ] T012 [US3] `test_plugins/test_shared.py`: `TestAddPages`. Each add page carries
  all three ways in one response (scenario 1) and reopens on the way named in the address or the
  form (3). `TestAddFromRegistry`: results; no results; a chosen record; adding makes the profile
  from a fresh fetch by identifier, not from posted fields, and sends the manager to the edit page
  (7, 8, 14); a registry that cannot be reached shows that it is unavailable, answers 200, and the
  other two ways still work (15). `TestAddByHand`: a person needs both names (10) and an
  organization a name; a person's same name offers the existing profiles first and can still be
  made (11); an organization's same name offers the existing one and makes no second (12); the
  optional fields are stored; an email address the portal already holds is refused on the field
  and the response does not name or link the profile it belongs to; a person added by any way is asked for their organization (13).
  Nothing is made by a request from someone who may not manage the record (SC-005).
- [ ] T013 [US3] Implement to make T011 and T012 pass (plan D4, D5 `NewPersonForm` and
  `NewOrganizationForm`): `Orcid` and `Ror` in `services/registries.py`; the registry and by-hand ways on both add
  pages; delete the fixed records and the pause.
- [ ] T014 [US3] Documentation: the three ways of adding in the user guide page; what the portal
  needs in order to search ORCID and ROR, and what happens when it cannot, in
  `docs/portal-administration/` (FR-067, in part); `services/registries.py` in the developer page.

## Phase 4: US-4, a team lets a colleague into its own private record (P1)

From this story on, stored guardian rows no longer apply to core records. The data migration and
the creator's level land here with the backend, so no commit leaves a creator locked out.

- [ ] T015 [US4] `tests/test_contrib/test_contributors/test_permissions.py`:
  `TestRecordLevelBackend`, through `user.has_perm`. For each core record type and each level,
  every permission in the table is granted at its level and above and refused below (FR-035 to
  FR-037, FR-043); a permission not in the table is refused; a registered sample type asked with
  its own app-labelled permission answers as the core model's; a level on a dataset reaches its
  samples and measurements, and a level on a project reaches its datasets and theirs (FR-044); the
  higher of two applies (FR-045); a person listed on a dataset in a private project opens the
  dataset and not the project (FR-046); a stored guardian row on a core record grants nothing; an
  organization's members and owner gain nothing (FR-041); an inactive user is refused. A guardian
  row on an organization still works as before.
- [ ] T016 [US4] Where each is tested today, or `tests/test_core/test_managers.py`: `with_level`
  and `visible_to`. A person with a level on the dataset, or on its project, sees the dataset's
  samples and measurements. A person listed only on one sample or measurement sees that record and
  not its siblings. A person with no level anywhere sees neither. For each reader in plan D2's
  table: a level holder with no guardian row is listed or offered, and a stored row alone is not
  (the API list, the dataset choices on the sample and measurement forms, the two filters, the
  dataset plugin's list, the demo model).
- [ ] T021a [US4] `tests/test_core/test_project/test_views.py`, the dataset equivalent and the API
  serializer tests: creating a project or a dataset through the portal, or a sample or measurement
  through the API, lists the creator at the manage level (story 5 scenario 1) and writes no
  guardian row. A superuser creating a record succeeds and is not credited.
- [ ] T022 [US4] `tests/test_contrib/test_contributors/test_migrations.py`, new, using the
  project's migration-test helper if it has one and `MigrationExecutor` if not: a person with
  view, change and delete rows becomes a manager; change only becomes an editor; view only a
  viewer; a person with rows and no contribution gains one; a contributor with no rows gets the
  view level; an organization gets none; a member of a group holding rows gets the level those
  rows map to; a registered subtype with one row under the base content type and one under its own
  is read from both; the rows are gone; an organization already stored on a person's entry is kept
  and listed on the record, and an entry with none is left with none (FR-063 to FR-065, SC-010).
- [ ] T017 [US4] `test_plugins/test_shared.py`: `TestLevels`. A newly added person can
  open a private record and cannot change it (scenario 1, FR-038); the edit page sets the level
  with the roles (2); an editor may use the record's update page, and a POST from them that
  changes the visibility or the record it sits under leaves both unchanged, while a manager's and
  a Data Curator's succeeds; an editor is refused the delete page and the tab's changing pages
  (3); a manager may (4); a lowered person is refused (5); a removed person is refused unless they
  hold a level from above (6); no level is offered for an organization (7); a level below what is
  held from above is refused on the field (`below_inherited`); the tab shows a manager the people
  who hold access from above and where from, and shows a reader nobody's level (9, 14, FR-006,
  FR-047); a person with no active account keeps the level set for them and the tab's context
  marks it as not yet in effect (13, FR-042). `TestPrivateRecordTab`: a stranger and a visitor get
  404 on every page of a private record's tab, the same as its overview (11, FR-049); a public
  record's tab opens to everyone (12); a person listed on a dataset in a private project opens the
  dataset's tab (10); a person listed only on a sample in a private dataset opens the sample and
  not the dataset.
- [ ] T018 [US4] Implement to make T015, T016, T021a, T022 and T017 pass (plan D2, D3 level
  handling in `update` and `make_creator`, D5 the level on the edit form, the tab's check and the
  update forms, D7 data step):
  - `RecordLevelBackend` and the settings; core records refused by
    `PolymorphicObjectPermissionBackend`; the sample and measurement backends removed
  - `with_level` on the core querysets and `visible_to` on it
  - every reader and writer in plan D2's table, by file
  - `make_creator` on the two create pages and the API's create serializers
  - the data migration
  - visibility and the parent field left out of the four update forms for anyone who cannot manage
  - docstrings that describe the old behaviour, corrected where the behaviour changes
- [ ] T019 [US4] Documentation: what each level allows and how a colleague is let into a private
  record, in the user guide page; how per-record levels and portal roles work together, and that
  an organization's members gain nothing, in `docs/portal-administration/roles.md` (FR-067);
  `RecordLevelBackend`, the permission table, `with_level` and the removed backends in the
  developer page and the changelog; the upgrade and what it does to stored record permissions,
  user-level and group-level, and that deleting a sample now needs manage, in the administrator
  guide and the changelog; `CONTEXT.md` defines the three levels and says rights flow from the
  record above (FR-069).

## Phase 5: US-5, every record has someone who can manage it (P2)

- [ ] T020 [US5] `test_services/test_crediting.py`: `TestLastManager`. Removing or lowering the
  only manager is refused (`last_manager`) with nothing changed (scenario 2); with two it is saved
  (3); a manager through the dataset counts (4); a person who cannot sign in does not count (6).
  `TestRecordLock`: `add`, `update`, `remove` and `move` each lock the record's row inside a
  transaction before reading its contributors (FR-055), asserted on the queries issued and skipped
  on a database that cannot lock rows.
- [ ] T021 [US5] `tests/test_core/` model tests: `TestMoveKeepsManager` for a dataset's
  project and a sample's and measurement's dataset (`no_manager`, FR-056).
- [ ] T022a [US5] The merge service's existing test module: merging two people who are both on a
  record leaves one entry with the higher level; a contribution only the discarded person held
  moves with its level; the kept entry's organization is unchanged, including when it is none.
- [ ] T023 [US5] `test_plugins/test_shared.py`: `TestLastManagerPages`. The edit page
  refuses lowering the only manager on the level field and the remove page refuses and offers no
  way to go ahead, for a manager and for a superuser alike.
- [ ] T024 [US5] Implement to make T020 to T023 pass (plan D3 `last_manager` and the row lock, D8,
  D9): `Crediting`; the models' `clean`; the merge service.
- [ ] T025 [US5] Documentation: the last-manager rule, and that a record cannot be moved somewhere
  that would leave it without a manager, in the user guide page.

## Phase 6: US-6, the team decides the order its contributors are named in (P2)

- [ ] T026 [US6] `test_services/test_crediting.py`: `TestMove`. A person moves among people and an
  organization among organizations, each leaving the other list alone (scenarios 1, 2); the first
  cannot move earlier nor the last later; a new person is last among people and a new organization
  last among organizations (4); removing or editing one leaves the others in place (5).
- [ ] T027 [US6] `test_plugins/test_shared.py`: `TestMovePage`, a POST moves and
  redirects to the tab, and someone who cannot manage is refused (6). `tests/test_core/`:
  `get_contributions()` returns people in order, then organizations in order, and the dataset and
  project citations name creators in that order (3, FR-058, SC-011).
- [ ] T028 [US6] Implement to make T026 and T027 pass (plan D3 `move`, D6).
- [ ] T029 [US6] Documentation: ordering, and that people come before organizations where both are
  named, in the user guide page.

## Phase 7: US-7, portal staff can step in on any record (P3)

- [ ] T030 [US7] `test_plugins/test_shared.py`: `TestPortalRoles`, with the development
  accounts. A Data Curator opens a private record they are not listed on and manages its
  contributors, and is not listed afterwards (scenarios 1, 2); raises a contributor on a record
  with no manager (3); is refused the last-manager removal and the removal of an organization
  people are credited from (4). A Community Manager, a Developer and a Portal Administrator who are
  not contributors are refused the private record (5, FR-062); a person removed from the Data Curator role
  is refused on their next request (6).
  `tests/test_portal_roles.py`: the permissions each shipped role holds are the same as on `main`
  (FR-062, SC-012).
- [ ] T031 [US7] Implement whatever T030 shows is missing. Extend `seed_contributors` so the Data
  Curator development account has a private record to step in on.
- [ ] T032 [US7] Documentation: stepping in on a record, in `docs/portal-administration/roles.md`.
  Read every page this feature added or changed once more against the finished branch, and run
  each example (SC-014).
