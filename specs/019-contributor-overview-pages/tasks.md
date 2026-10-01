# Tasks: Overview pages for people and organizations

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md)

**Design source**: the prototype already on this branch. Its markup, copy and layout are settled.
Change them only where a requirement, a plan decision or a failing acceptance test says so.

**Tests first**: in every story, the test tasks come first. Tests request real pages through the
Django test client and assert on what the page delivers, as a visitor and signed in. A test that
passes at once against the prototype is fine: it pins a scenario the prototype already meets. A
test that fails drives a fix in the story's fix task. Layout, width, stacking and copy get no
tests. No query-count assertions.

**Existing tests**: the five `pending_action.html` tests are handled as plan D8 says. Any other
pre-existing test stays as it is, and the code is fixed.

**Format**: `[ID] [Story] Description`.

**Story order**: the stories run one after another, each from the previous story's accepted commit.

## Phase 1: US-1, what both pages share and the person page (P1)

- [ ] T001 [US1] Housekeeping (plan D8, D3, D6):
  - declare Pillow as a direct dependency and re-lock, so `deptry` passes
  - restore `reverse("account-center") == "/account-center/"`
  - move the `TestPendingAction` assertions to `c-actions.pending` and remove the two badge tests
  - fold `ContributorOverviewMixin` into one registered `Overview` class in `plugins/overview.py`
  - delete the `Statistics` and `Network` plugins, their templates and any tests of them
  - the lint step and the existing suite pass
- [ ] T002 [US1] `tests/test_contrib/test_contributors/test_profiles.py`: `link_host` (with and
  without `www.`, a link with no host kept as written), `language_names` (known code, unknown
  code kept), `ranked_shares` (order, empty), `fill_slots` (fits, overflows, reserved last place),
  `active_then_recent` (active first, each group newest first, no active state).
- [ ] T003 [US1] Model tests in `tests/test_contrib/test_contributors/test_models.py`:
  - `get_visible_contributions`: public projects and datasets only, for a visitor, for the person
    and for a member of the private project; a public dataset inside a private project is left
    out; samples and measurements follow `visible_to(user)`
  - `get_role_counts` and `get_collaborators` over those credits: a role or a collaborator known
    only through a private record is absent; ties ordered by name
  - `Person.get_affiliation_history` (primary first, past by most recently ended, pending left
    out), `Person.member_since` per account state, `Affiliation.start_display` / `end_display` at
    year, month and day precision
  - `to_public_schema_org` carries no email; `get_links_display`; `resolver_url` for a type with
    and without a resolver
- [ ] T004 [US1] Component tests under `tests/test_templates/`: `c-card.records`, `c-card.roles`,
  `c-card.links`, `c-card.affiliations` and `c-missing` each render their documented inputs and
  say what is missing when given nothing; each entry links where FR-018 to FR-023 say it links.
- [ ] T005 [US1] `tests/test_contrib/test_contributors/test_plugins/test_overview.py`,
  `TestPersonOverview`: US-1 scenarios 1 to 13 and 15 against the rendered page.
  `test_plugins/test_person.py`, `TestContributorTabs`: scenario 14 for both tabs, and the
  Datasets tab answers 200 (#248).
- [ ] T006 [US1] Fix what T002 to T005 found, including plan D4: the dataset rule checks the
  project, and both tabs list public records only.
- [ ] T007 [US1] Seed command test under `tests/test_demo/`: `seed_profiles` runs, refuses
  outside development, and each person state FR-033 names answers 200.
- [ ] T008 [US1] Documentation: the contributor pages and their blocks in
  `docs/portal-development/overview-pages.md` (including `overview.name`); the new components in
  `component_library/cards.md`; the model methods and `profiles.py` helpers in
  `contributors.md`; **Collaborator** and **Member** in `CONTEXT.md`; a changelog entry. The docs
  check passes.

## Phase 2: US-2, the organization page (P2)

- [ ] T009 [US2] Model tests: `Organization.get_current_memberships` (current and verified only,
  owner, administrators, members, each by name), `has_member`, `is_managed_by` (ended and pending
  affiliations do not count), `get_hierarchy` (parent, siblings, children; no parent; neither),
  and `Project.is_active` in `tests/test_core/test_project/test_models.py`.
- [ ] T010 [US2] Component tests: `c-card.hierarchy` for the three shapes in T009, with this
  organization marked and not linked and every other one linked.
- [ ] T011 [US2] `TestOrganizationOverview` in `test_plugins/test_overview.py`: US-2 scenarios 1
  to 12 against the rendered page.
- [ ] T012 [US2] Fix what T009 to T011 found, including plan D4 for owned projects and the
  datasets inside them.
- [ ] T013 [US2] The organization states of FR-033 in the seed command test, and the organization
  page in the documentation.

## Phase 3: US-3, the checklist (P3)

- [ ] T014 [US3] Tests for `checklist` in `test_profiles.py`, and for
  `Person.get_profile_completeness` (an ORCID iD typed in is not connected) and
  `Organization.get_record_completeness` in `test_models.py`.
- [ ] T015 [US3] `TestPersonChecklist` and `TestOrganizationChecklist` in
  `test_plugins/test_overview.py`: US-3 scenarios 1 to 8 against the rendered pages.
- [ ] T016 [US3] Fix what T014 and T015 found, and document the checklist and who sees it.

- [ ] T017 [US3] Polish: `makemigrations --check` is clean with every app installed. Every new string in the
  plugin and the templates is marked for translation. The full verify gate passes.
