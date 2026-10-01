# Progress: 019-contributor-overview-pages

- 2026-10-01: build branch cut from main with the reviewed prototype merged in (98a231c7). Plan and tasks written against the specification. Baseline: 6 pre-existing tests red, `deptry` and the docs check red, all folded into US-1.

## 2026-10-01T10:14Z · Implementer US1 · T001

- Did: declared Pillow in `pyproject.toml` and re-locked; added FairDM's `account-center/` route to django-mvp's landing view in `fairdm/conf/urls.py`; moved three `TestPendingAction` tests to `c-actions.pending` and deleted the two badge tests; `plugins/person.py` imports `gettext_lazy`.
- Verified: `uv run pytest tests/test_conf/test_urls.py tests/test_templates/test_includes.py -q -n0` (15 passed, exit 0); `uv run pre-commit run --all-files` (all hooks passed, deptry included).
- Next: T002, the pure helpers.
- Watch: the route sits after the `mvp.urls` include, not before it, because Django reverses a name to the last pattern that carries it. See decisions.md.

## 2026-10-01T10:14Z · Implementer US1 · T002

- Did: added `test_profiles.py` with a class per helper (`link_host`, `language_names`, `ranked_shares`, `fill_slots`, `active_then_recent`).
- Verified: `uv run pytest tests/test_contrib/test_contributors/test_profiles.py -q -n0` (18 passed, exit 0, all green on first run against the prototype). Mutated the `www.` prefix, the reserved slot and the active sort in `profiles.py` and watched three of the tests fail; restored the file afterwards. `uv run pre-commit run --all-files` clean.
- Next: T003, model tests.
- Watch: none.

## 2026-10-01T10:17Z · Implementer US1 · T003

- Did: added a `credited_world` fixture (a person credited on public and private projects, datasets, samples and measurements, with a mate on each private record) and ten test classes in `test_models.py` for visible contributions, the public project and dataset sources (`get_public_projects`, `get_public_datasets`, which do not exist yet), role counts, collaborators, affiliation history, member since, affiliation date display, `to_public_schema_org`, link display and identifier resolver URLs.
- Verified: `uv run pytest tests/test_contrib/test_contributors/test_models.py -q -n0` gives 12 failed, 192 passed. The 12 failures are the new tests that find real gaps: private-project datasets, samples and measurements listed, roles and collaborators known only through them counted, a pending or ended primary affiliation in the schema.org data, and the two missing source methods. I read each failure and each is the symptom, not a fixture error. Mutating the collaborator tie order, the affiliation sort and filter, and the member-since states failed the matching tests; models.py restored. `uv run pre-commit run --all-files` clean.
- Next: T004, component tests.
- Watch: the tree is red on purpose until T006, which fixes these.

## 2026-10-01T10:18Z · Implementer US1 · T004

- Did: added `tests/test_templates/test_contributor_cards.py` with a class for `c-missing`, `c-card.records`, `c-card.roles`, `c-card.links` and `c-card.affiliations`. Entries are checked for where they link, counts for their numbers, and empty states are found by the card's `data-card` attribute and the alert role.
- Verified: `uv run pytest tests/test_templates/test_contributor_cards.py -q -n0` (18 passed, exit 0; all green on first run against the prototype). Removed the link `rel` and the "more" link from the templates in turn and watched two tests fail; templates restored. `uv run pre-commit run --all-files` clean.
- Next: T005, the page tests.
- Watch: `c-card.hierarchy` is US2's and is not tested here.

## 2026-10-01T10:23Z · Implementer US1 · T005

- Did: added `test_plugins/` with `TestPersonOverview` (scenarios 1 to 13 and 15, SC-003, the not-found case) and `TestContributorTabs` (scenario 14, the Datasets tab answering 200), with fixtures in the package `conftest.py`.
- Verified: `uv run pytest tests/test_contrib/test_contributors/test_plugins -q -n0` gives 14 failed, 27 passed. I read each failure: the Projects and Datasets figures and the View all link render `href="None"` (the plugin reverses `contributor:contributorprojects`, the route is `contributor-projects`); the Datasets card and tab list a public dataset inside a private project; a collaborator and roles known only through private records are shown; a pending primary affiliation's organization is in the schema.org description in the head; the Statistics and Network tabs still exist. Mutated the card and collaborator limits, the unclaimed flag, the active-first sort and the project filter and watched the matching tests fail; all restored. `uv run pre-commit run --all-files` clean.
- Next: T006, the fixes.
- Watch: the Datasets-tab 200 test (#248) and the Projects-tab visibility test pass against the prototype, as the brief expects.

## 2026-10-01T10:28Z · Implementer US1 · T006

- Did: three commits. First the visibility fixes (`DatasetQuerySet.get_visible`, `Contributor.get_public_projects` and `get_public_datasets` read by the page and both tabs, the project check on samples and measurements, samples and measurements resolved to ids, collaborators found with one condition per kind of record, the affiliation rule in `Person.to_public_schema_org`, the figure and View all links now using the real route name). Then the fold: `ContributorOverviewMixin` and the registered class are one `Overview(OverviewPlugin)` in `plugins/overview.py`, registered there, and `plugins/person.py` keeps only the Projects and Datasets tabs. The Statistics and Network plugins and the statistics template are gone; no other test or docstring mentioned them. `get_visible_contributions` no longer sets `record` on samples and measurements, so I changed the helper in my own T003 tests to compare each credit's kind and id; each assertion still compares against the same expected records.
- Verified: `uv run pytest tests/test_contrib tests/test_templates tests/test_conf tests/test_core/test_dataset tests/test_core/test_project -q -n 4` (1923 passed, 1 skipped, exit 0); `uv run pre-commit run --all-files` clean; `makemigrations --check --dry-run` for the five core apps reports no changes. Added four tests for `DatasetQuerySet.get_visible`.
- Next: T007, the seed command test.
- Watch: the plan's attempt count here is three commits for one task. `person/plugins/overview.html` and `organization/plugins/overview.html` are older overview templates that nothing renders any more; I left them alone as out of scope. See D9 and D10 in decisions.md.

## 2026-10-01T10:29Z · Implementer US1 · T007

- Did: added `test_seed_profiles.py` next to the `seed_overviews` test: refusal outside development, one test per person state FR-033 names (complete profile, the signed-in user's incomplete one, unclaimed, inactive, credited on nothing, very long name, non-Latin name), every seeded page answering 200 for a visitor, the user's own page answering for them, and a rerun leaving the same people and a bystander alone. The seeded organization states are US2's (T013).
- Verified: `uv run pytest tests/test_demo/test_management/test_commands/test_seed_profiles.py -q -n0` (13 passed, exit 0, all green on first run against the prototype). Closed the inactive account and gave the non-Latin person a Latin name in the command and watched the two matching tests fail; command restored. `uv run pre-commit run --all-files` clean.
- Next: T008, documentation.
- Watch: the file takes about 22 seconds because each test runs the command.

## 2026-10-01T10:32Z · Implementer US1 · T008

- Did: added the `overview.name` block, a person page section and an extension example to `overview-pages.md`; `c-card.records`, `c-card.roles`, `c-card.links`, `c-card.affiliations`, `c-missing` and `c-actions.pending` to `cards.md`; the profile methods and the `profiles.py` helpers to `contributors.md`; Collaborator and Member to `CONTEXT.md`, with the two visibility sentences reconciled; and changelog entries under the existing headings.
- Verified: `forge verify --repo . --base origin/main --steps docs` passed (it first reported two stale mentions of the removed tabs in my own text, which I reworded). I ran the Django template extension example and the Python snippets in a scratch test that I did not commit: the extension rendered the added card beside the cards FairDM draws, and the helper outputs matched the pages. `uv run pre-commit run --all-files` clean.
- Next: the full gate and the report.
- Watch: the organization page is not documented here; US2 owns it.

## 2026-10-01T10:39Z · Implementer US2 · T009

- Did: added model tests for Organization.get_current_memberships (current and verified only, owner then administrators then members each by name), has_member and is_managed_by (pending, ended and portal-role cases), get_hierarchy (parent, siblings, children; no parent; neither) and Project.is_active (in progress only).
- Verified: 26 passed on the first run, as the prototype already has these methods. Probed by mutation: dropping current() and the type floor in get_current_memberships, lowering is_managed_by to member, dropping current() in has_member, and making is_active always true each made the matching tests fail; the source is restored. Removing order_by(name) from get_hierarchy left the tests green because Contributor already orders by name, so that mutation changes nothing. uv run pre-commit run --all-files clean.
- Next: T010, the c-card.hierarchy tests.
- Watch: These methods needed no fix, so T012 has nothing to change in them.

## 2026-10-01T10:40Z · Implementer US2 · T010

- Did: added TestHierarchyCard to test_contributor_cards.py: parent with siblings and children, no parent, parent without children and neither, each found by the card data attribute and aria-current, never by wording. Every organization except this one links to its page and this one is marked and not linked; with nothing it shows the empty state and no list.
- Verified: 5 passed on the first run against the prototype. Probed the template by mutation: never marking, always marking, ignoring children in the empty-state test and marking the wrong sibling each failed between one and four tests; the template is restored. uv run pre-commit run --all-files clean.
- Next: T011, the organization page tests.
- Watch: The component needed no change, so nothing from T010 reaches T012.

## 2026-10-01T10:45Z · Implementer US2 · T011

- Did: added TestOrganizationOverview with its helpers and an owner_world fixture to test_overview.py: scenarios 1 to 12 as a visitor and signed in (owned and credited projects listed once with the owned ones marked, datasets of an owned project counted without a credit, private records neither counted nor named for a visitor, a member and a manager, members credits not counted, members listed current and verified only in owner, administrator, member order, ten places with the last counting the rest, the hierarchy in document order, the map only with a location, asking to join and the management menu, every card but the map with nothing recorded, the schema.org description) and the SC-003 comparison of each figure with its tab for an organization that owns a project it is not credited on.
- Verified: 27 passed and 2 failed against the prototype. I read the failures: the Projects tab lists only the credited projects, so the owned project is missing from it and the figure disagrees with the tab. That is the plan D4 defect T012 fixes. Probed the passing tests by mutating the plugin: listing private owned projects, never marking owned, dropping the owned-project filter, dropping the dataset de-duplication, changing the member places, making every manager a member and over-counting members each failed several tests. Forcing has_map true did not fail any: the location card draws nothing without a location, so the page is the same. uv run pre-commit run --all-files clean.
- Next: T012, the model sources.
- Watch: The commit leaves the two tab tests red on purpose, as the task order asks; the next commit makes them pass.

## 2026-10-01T10:49Z · Implementer US2 · T012

- Did: Organization now overrides get_public_projects (public projects it owns plus those it is credited on) and get_public_datasets (public datasets it is credited on plus those in its projects, never one inside a private project), each a single queryset with nothing twice. The overview plugin reads both, marks a project owned from its owner, and no longer builds the lists itself; get_record_entries had no caller left and is gone. The Projects and Datasets tabs read the same methods through Contributor. Added TestOrganizationPublicRecordSources for the two overrides.
- Verified: The two red tab tests from T011 pass. The contributors, templates, project and dataset suites give 1533 passed. Mutated each half of both overrides (the owner condition, the dataset project owner condition, the credited condition, the visibility filter) and each made a model test fail; restored. makemigrations --check for the five core apps reports no changes; a check over every app also names a pending alteration in the third-party orbit package, which this story does not touch. uv run pre-commit run --all-files clean.
- Next: T013, the seed command and the documentation.
- Watch: My first dataset fixture failed because DatasetFactory gives a dataset a private project by default; the new tests pass project=None where they mean no project.

## 2026-10-01T10:53Z · Implementer US2 · T013

- Did: added TestSeedProfilesOrganizationStates: an organization with everything recorded, one the signed-in user owns, one with nothing recorded, every seeded organization page answering 200 for a visitor, and for the signed-in user with the checklist shown only on the organization they keep. seed_profiles needed no change. Wrote the organization page into overview-pages.md (anatomy, members and hierarchy, whose work it counts, who keeps the record, extending it), c-card.hierarchy into cards.md with the owner badge on records, the four membership and hierarchy methods and the two Organization sources into contributors.md, and changelog entries. Decisions D11 and D12 recorded.
- Verified: uv run pytest on the seed test file gives 18 passed. Mutated the seed command (the user as plain member instead of owner, no location on the complete organization, a parent on the empty one, no organization type) and each made a test fail; restored. forge verify docs step passed. I ran the Django extension example and the model snippets in a scratch test that I did not commit: the extension rendered the added card beside the cards FairDM draws and every context key the docs list was present. uv run pre-commit run --all-files clean.
- Next: The full gate and the report.
- Watch: The seed file now takes about 33 seconds because each test runs the command. The testing standard has no class-scoped database fixture and unittest setUpTestData is not allowed, so I could not share one run.

## 2026-10-01T11:00Z · Implementer US3 · T014

- Did: added TestChecklist to test_profiles.py (done count, total and ready for the items given), TestPersonProfileCompleteness and TestOrganizationRecordCompleteness to test_models.py. They pin each flag on its own, that an ORCID iD typed in is not connected and signing in with ORCID is, that only a ROR identifier counts as the ROR item, that a location needs both the city and the country, and that a primary affiliation counts only when current and verified.
- Verified: 19 passed and 1 failed on the first run. The failure is real: a pending primary affiliation counts toward the checklist's affiliation item while the header names no organization for it. T016 fixes it. Probed by mutating the two methods (location with or, ROR as any identifier, ORCID as a typed identifier) and seven tests failed between them; restored. uv run pre-commit run --all-files clean.
- Next: T015, the rendered pages for scenarios 1 to 8.
- Watch: The commit leaves that one test red on purpose, as the task order asks; T016 makes it pass.

## 2026-10-01T11:04Z · Implementer US3 · T015

- Did: added TestPersonChecklist and TestOrganizationChecklist to test_overview.py for scenarios 1 to 8, with the incomplete_person and keeper_world fixtures. A person's checklist is shown to that person and not to a visitor, another signed-in user, a staff user or a superuser; its progress equals the completeness flags, the photo and the links are optional, the ORCID item links to the connected-accounts page and a typed-in iD leaves it open, and editing replaces the contact action only on the person's own page. The organization checklist and the all-disabled management menu are shown to an owner and an administrator and to nobody else: not a member, a pending request, a stranger, a visitor, staff, a superuser, or a former administrator or owner whose affiliation ended. Elements are found by data-card, the progress element, hrefs and the icon each button carries, never by wording.
- Verified: 33 passed and 1 failed. The failure is the same defect T014 found, seen on the page: a pending primary affiliation counts as in place though the header names no organization. One test of mine was wrong at first (it picked the wrong menu list) and I fixed the test. Probed by mutating the plugin and the person template: showing the person checklist to everyone, showing the organization checklist to any signed-in user, making the ORCID item always done, letting staff manage, and swapping the edit and contact branch failed between 2 and 11 tests each; restored. uv run pre-commit run --all-files clean.
- Next: T016, the fixes and the documentation.
- Watch: Scenarios 6 to 8 were partly covered by US2's tests; the new class adds the former administrator, the pending request and the superuser cases and does not edit US2's tests.

## 2026-10-01T11:07Z · Implementer US3 · T016

- Did: Person.get_profile_completeness now counts a primary affiliation only when it is verified and has not ended, which is what the header shows. Person.get_location_display reads the same affiliation, filtered in Python over affiliations.all() so a prefetch still costs no query per person; TestPersonLocationDisplay was written first and failed for the pending and ended cases. Deleted person/plugins/overview.html and organization/plugins/overview.html after a search of fairdm, docs, tests and demo found no reference. Documented the checklist, its items and who sees it in overview-pages.md, the completeness methods, the location rule and the checklist helper in contributors.md, and the changelog (Added, Fixed and Removed). Decisions D13 and D14 recorded.
- Verified: the two T014 and T015 tests that were red pass. tests/test_contrib plus tests/test_demo gave 949 passed before the deletion, and tests/test_contributors plus tests/test_templates gave 778 passed after it. uv run pre-commit run --all-files clean.
- Next: T017, the polish checks and the full gate.
- Watch: The person card in listings also calls get_location_display, so a pending or ended primary affiliation no longer shows a place there either. primary_affiliation() and primary_organization still apply no verification; the card's organization line reads them. That is outside this story and is in the report's concerns.

## 2026-10-01T11:10Z · Implementer US3 · T017

- Did: ran makemigrations --check --dry-run over the 18 apps of the fairdm and demo packages (No changes detected, exit 0) and over every installed app, where the only pending change is the third-party orbit migration 0008_alter_orbitentry_type. Scanned the contributor plugin and every page and card template this feature added for text outside gettext and translate tags: the ROR iD title on the organization header and the authenticated ORCID title on the person header were plain text and are now marked. The repository has no locale catalogue to regenerate.
- Verified: tests/test_contrib/test_contributors/test_plugins gives 99 passed after the change. The full gate, forge verify --repo . --base origin/main, exited 0 with conformance, docs, lint, typecheck, test and build all passed.
- Next: the completion report.
- Watch: The gate ran with the two template edits staged and not yet committed; the commit contains exactly those edits plus the ledger and this entry.
