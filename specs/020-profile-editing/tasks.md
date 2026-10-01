# Tasks: Editing person and organization profiles in the portal

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md)

**Tests first**: in every story the test tasks come first and are seen to fail before the code
that makes them pass is written. Page tests open and submit the real editing page through the
Django test client, once for each kind of account the scenario names, and assert on the response
and on what is stored afterwards. Layout, width, stacking and copy get no tests. No query-count
assertions.

**Existing tests** stay as they are. Where one pins a disabled stand-in this feature brings to
life, it is updated in the task that changes the template, and the change is named in
`progress.md`.

**Format**: `[ID] [Story] Description`.

**Story order**: the stories run one after another, each from the previous story's accepted commit.

## Phase 1: US-1, a person edits their own profile (P1)

- [ ] T001 [US1] `tests/test_contrib/test_contributors/test_forms/test_profile.py`, new package.
  `TestLinesField`: one entry per line; blank lines dropped; repeats kept once in first-seen
  order; surrounding spaces trimmed; a list as initial value is shown one per line; the per-entry
  validator names the entry at fault. `TestPersonProfileForm`: the fields are exactly photo,
  name, alternative names, biography, links and languages (FR-007); a name is required; a link
  that is not an `http` or `https` address, a language code outside ISO 639-1, a file that is not
  an image and an image over the size limit are each refused on their own field (FR-011); a
  cleared photo is removed (FR-015); a valid form saves every field.
- [ ] T002 [US1] `tests/test_contrib/test_contributors/test_models.py`, `TestPersonIsEditableBy`:
  the person themself; another signed-in person; a visitor; a superuser who is somebody else; a
  person holding the Data Curator, Developer or Portal Administrator role and no other. Only the
  first may edit. A person who has signed in and is not marked claimed (as `createsuperuser`
  makes one) may edit their own profile. `TestContributorUpdateUrl`: `get_update_url()` is the editing page's address.
- [ ] T003 [US1] `tests/test_contrib/test_contributors/test_plugins/test_update.py`,
  `TestPersonUpdate`: US-1 scenarios 2 to 6 and 8 to 11 against the real page. A save redirects
  to the overview and leaves a success message (FR-018). A refused save stores nothing, answers
  200 with the error on its field and the other typed values still in the form (FR-013). A
  visitor is redirected to sign in, GET and POST. A signed-in stranger gets 403 on GET and POST
  and nothing is stored (SC-004). The page has no input for email, password, ORCID iD,
  affiliations, roles or account status, and links to the account centre (FR-010). A changed name
  shows on a record the person is credited on (FR-019). A profile that does not exist answers 404.
  With `FAIRDM_PROFILE_FORMS` naming a form for one kind only, the other kind's page still opens
  with the shipped form. The changed-name case covers `name` only (decisions D9).
- [ ] T004 [US1] `test_plugins/test_overview.py`, added to `TestPersonOverview`: on their own
  profile the header's edit action is a link to the editing page (scenario 1); the checklist's
  photo, biography and links items each link to the editing page with the field's id as the
  fragment, and the ORCID and primary affiliation items are unchanged (scenario 7, FR-017); the
  About card's prompt links to the biography field; someone else's profile offers no edit link
  (scenario 8).
- [ ] T005 [US1] Implement to make T001 to T004 pass (plan D1 to D4, the person half):
  - `Contributor.is_editable_by` and the `Person` override (own profile only in this story)
  - `forms/profile.py` with `LinesField` and `PersonProfileForm`
  - `FAIRDM_PROFILE_FORMS` with its `person` entry
  - `plugins/update.py` with `Update`, added to `Overview.extra_views`, and its template if the
    shared form page needs one
  - `get_update_url()` reverses `contributor:overview-update`; delete `UserProfileForm`
  - the person overview context and template changes
- [ ] T006 [US1] Documentation: a page on editing your profile under
  `docs/user-guide/account_management/`, linked from its index; `FAIRDM_PROFILE_FORMS`,
  `PersonProfileForm`, `LinesField`, `is_editable_by` and the `Update` page in
  `docs/portal-development/contributors.md`, with an example of a portal adding a field that runs
  as written (FR-022, SC-008); a changelog entry. The docs check passes.

## Phase 2: US-2, an organization's owner and administrators edit its profile (P2)

- [ ] T007 [US2] `test_models.py`: `TestOrganizationDescendantIds` (none, children, grandchildren);
  `TestOrganizationParentLoop`: `full_clean` refuses the organization itself and one beneath it as
  parent, on the `parent` field, and accepts an unrelated organization and one that already has
  children of its own. `TestOrganizationIsEditableBy`: owner and administrator may; an ordinary
  member, a stranger, a visitor, an administrator whose affiliation has ended, a deactivated
  administrator, a Data Curator and a superuser may not; an organization with no owner or
  administrators is editable by none of them (scenario 11).
- [ ] T008 [US2] `test_forms/test_profile.py`, `TestOrganizationProfileForm`: the fields are
  exactly logo, name, alternative names, type, parent, city, country, description, website and
  other links (FR-008); the website is shown from, and saved as, the first stored link, with the
  other links after it and no repeat; clearing the website keeps the other links; a name is
  required; type and country outside their lists are refused; the organization itself and one
  beneath it are refused as parent with the reason on the field (FR-012); clearing the parent
  leaves the sub-organizations as they were (scenario 5).
- [ ] T009 [US2] `test_plugins/test_update.py`, `TestOrganizationUpdate`: US-2 scenarios 2 to 6 and
  8 to 11 against the real page, for the owner, an administrator, a member, a stranger, a Data
  Curator, an ended administrator and a visitor. A deactivated administrator is signed out by
  Django, so that request is redirected to sign in. No input for the ROR identifier, members or
  owner (FR-010). A changed name shows on a project the organization owns and on a member's
  profile (FR-019).
- [ ] T010 [US2] `test_plugins/test_overview.py`, added to `TestOrganizationOverview`: for the
  owner and an administrator the menu's edit entry links to the editing page and the other two
  entries are still disabled (scenario 1, FR-016); the checklist's logo, type, city and country,
  description and website items link to their fields and the ROR item is unchanged (scenario 7);
  a member and a stranger are offered no edit link (scenario 8).
- [ ] T011 [US2] Implement to make T007 to T010 pass: `Organization.get_descendant_ids`, the loop
  check in `Organization.clean`, the `Organization.is_editable_by` override (keepers only in this
  story), `OrganizationProfileForm`, the `organization` entry of `FAIRDM_PROFILE_FORMS`, the
  organization overview context and template changes.
- [ ] T012 [US2] `seed_profiles` gains, on the organization the regular user owns, an
  administrator, an ordinary member and an administrator whose affiliation has ended, each a
  sign-in account at `example.com` with the password the other development accounts share. The seed command's test
  under `tests/test_demo/` covers them. Documentation: a user-guide page on editing an
  organization's profile; `OrganizationProfileForm` and the loop rule in `contributors.md`; the
  changelog entry extended. The docs check passes.

## Phase 3: US-3, a community manager maintains the profiles nobody else can (P3)

- [ ] T013 [US3] `tests/test_portal_roles.py`, `TestIsHeldBy`: a member of the role's group; a
  member of another role; a deactivated member; a visitor; a superuser in no group.
  `test_models.py`, added to `TestPersonIsEditableBy` and `TestOrganizationIsEditableBy`: a
  community manager may edit an unclaimed, an invited and an inactive person and any
  organization, including one with no owner; may not edit a person with an active account, including one who has signed in and is not
  marked claimed; a
  person removed from the role may not (scenario 10); the Data Curator's permissions are the same
  set as before (SC-005, asserted against the declared tuple's content, not its length).
- [ ] T014 [US3] `test_plugins/test_update.py`, `TestCommunityManagerUpdate`: scenarios 1 to 10.
  The form a community manager gets has the same fields as the keeper's (FR-009). Saving an
  unclaimed profile leaves it unclaimed, and saving an inactive one leaves it inactive (FR-020).
  A profile claimed, or an account reactivated, between opening the page and saving refuses the
  save with 403 and stores nothing (scenario 5). After reactivation the person can edit and sees
  the community manager's changes (scenario 6). Saving an organization leaves its affiliations
  unchanged (scenario 7). `test_overview.py`: a community manager is offered the edit action on
  an unclaimed and an inactive person and on an organization they do not keep, exactly one edit
  link per page (edge case), no checklist (scenario 11), and none on an active person's profile
  (scenario 4); nothing on a corrected profile names the community manager (scenario 8).
- [ ] T015 [US3] Implement to make T013 and T014 pass: `PortalRoles.is_held_by`, the community
  manager branch of both `is_editable_by` overrides, the single "Edit details" button on the
  organization page for an editor who does not keep the record.
- [ ] T016 [US3] `seed_profiles` creates `community-manager.user@example.com` and
  `data-curator.user@example.com` holding those roles, covered by the seed test. Documentation:
  who may edit person and organization profiles in `docs/portal-administration/roles.md`
  (FR-021); correcting a profile from the portal in `managing-unclaimed-profiles.md`;
  `PortalRoles.is_held_by` in `portal_roles.md`; **Profile maintainer** in `CONTEXT.md`; the
  changelog entry completed. The docs check passes.
- [ ] T017 [US3] `test_plugins/test_update.py`, `TestWhoMayEdit`: SC-003 as one table. For each
  seeded kind of account against each kind of profile, the editing page opens exactly where
  FR-001 to FR-003a say, and every other combination is refused on GET and on POST.

## Added during the build

- [ ] T018 [US2] A stored record may fail the model's validation on a field the editing form does
  not carry (a person's malformed identifier, an organization's malformed ROR). Saving then raises
  a server error. Test first in `test_forms/test_profile.py`, for both forms: the form is invalid
  and reports the problem as a form-level error, and nothing is saved. Then fix it in the shared
  base of the two forms.
- [ ] T019 [US3] An organization created from ROR stores its identifier as the full address
  (`https://ror.org/...`), which `Organization.clean` rejects, so its profile cannot be saved
  (SC-002, US-3 scenario 7). Test first in `test_models.py`: `full_clean` accepts a ROR stored as
  the bare identifier and as the full address, and still rejects a malformed one. Then make the
  check accept both.
- [ ] T020 [US3] A portal's form that leaves a shipped field out, as `contributors.md` says it may,
  must build (FR-022). Test first in `test_forms/test_profile.py`: a subclass of each shipped form
  without its languages, website or parent field builds and saves. Then fix the forms.
