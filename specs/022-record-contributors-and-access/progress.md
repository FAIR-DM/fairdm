
## 2026-10-06T12:11:56Z · Planner · plan

Did: wrote research.md, plan.md, tasks.md (32 tasks over 7 stories) and the ledger, on the branch brought up to date with origin/main at 5998b914.
Verified: manage.py check clean after uv sync and migrate; the shared dev server reloaded and answers.
Next: design review, one reviewer with three lenses.
Watch: no page creates a sample or measurement, so the creator rule is delivered for projects and datasets and as a callable for the other two.

## 2026-10-06T12:31:23Z · Implementer US1 · T001

Did: wrote tests/test_contrib/test_contributors/test_access.py (TestRecordsAbove, TestLevelOf, TestLevelParts, TestPeopleAbove, TestManagers, TestCanManage, TestRequiredLevel) and TestPersonCanSignIn in test_models.py, plus the record_chain and grant fixtures in the contributors conftest. TestLevelParts, TestPeopleAbove and TestRequiredLevel go past the list in tasks.md: the tab reads the two halves of a level and the people above, and REQUIRED_LEVEL must cover every permission the four record types declare.
Verified: `uv run pytest tests/test_contrib/test_contributors/test_access.py -q -n0` fails at collection with ImportError (RecordAccess and REQUIRED_LEVEL do not exist); `uv run pytest tests/test_contrib/test_contributors/test_models.py::TestPersonCanSignIn -q -n0` gives 4 failed with AttributeError (no can_sign_in). Both are the expected reason.
Next: T002.
Watch: the tree is red between T001 and T004 on purpose.

## 2026-10-06T12:31:23Z · Implementer US1 · T002

Did: wrote tests/test_contrib/test_contributors/test_services/test_crediting.py: TestAdd (view level on each of the four record types, none for an organization, placed last, duplicate refused with code duplicate, superuser refused with code superuser), TestOfferedRoles, TestUpdate (roles saved and replaced, none allowed, role_not_offered, level untouched), TestRemove.
Verified: `uv run pytest tests/test_contrib/test_contributors/test_services/test_crediting.py -q -n0` fails at collection with ImportError on RecordAccess, the expected reason.
Next: T003.
Watch: Crediting.offered_roles is a method beyond the three the brief lists; the edit page needs the offered roles from the same place the service checks them.

## 2026-10-06T12:31:23Z · Implementer US1 · T003

Did: wrote tests/test_contrib/test_contributors/test_plugins/test_contribution_tab.py (TestContributorsTab, TestChangingPagesRefuseAnyoneButAManager, TestAddFromPortal, TestEditRoles, TestRemoveContributor), run on a project, a dataset, the demo's registered sample type and its registered measurement type. Fixtures (public_chain, record, manager, reader, colleague, partner, newcomer, curator) are in test_plugins/conftest.py.
Verified: `uv run pytest tests/test_contrib/test_contributors/test_plugins/test_contribution_tab.py -q -n0 -x` fails at collection with ImportError on RecordAccess, the expected reason.
Next: T004, implementation.
Watch: records in the page tests are public so the tests stay valid when the tab refuses strangers on private records (US4).

## 2026-10-06T12:43:11Z · Implementer US1 · T004

Did: ContributionLevel and Contribution.level with migration 0022 (applied to the dev server's database with the development settings). access.py rebuilt as RecordAccess (above, kind, level_of, own_level, level_from_above, people_above, managers, can_manage) and REQUIRED_LEVEL. Person.can_sign_in, which is_editable_by now asks. services/crediting.py with Crediting.add, update (roles), remove and offered_roles. plugins/shared.py moved onto both: list, portal tab of both add pages, roles on the edit page, remove page; the prototype's affiliation choice, level radio, last-manager refusal and the move page are left as they were. RecordOverviewPlugin sets people_url for all four record types. Seeds: contributors.py credits through Crediting; common.py and projects.py also set the level next to the guardian rows they still grant (give_level). Dev database: contributions of the records seed_contributors made were given the level their guardian rows amount to with a one-off shell snippet (53 contributions; not a migration).
Pre-existing tests brought up to date: tests/test_contrib/test_plugins/test_registration.py::TestExtraViews::test_the_shipped_contribution_views_address_their_target (now reverses the tab's five views: add-person, add-organization, edit, remove, move) and tests/test_core/test_dataset/test_plugins.py::TestRetiredManagementPages::test_the_dataset_menu_carries_one_entry (the dataset menu now also carries contribution-list).
Template change: cotton/contribution/access.html reads entry.manages in place of comparing entry.effective with the word "manage"; what it draws is the same. entry.manages is new in the context beside the names the brief lists.
Verified: `uv run pytest tests/test_contrib/test_contributors tests/test_contrib/test_plugins tests/test_core/test_dataset/test_plugins.py::TestRetiredManagementPages -q -n auto --dist loadscope` 1244 passed; `uv run pytest tests/test_core tests/test_templates tests/test_api -q -n auto --dist loadscope` 1792 passed, 7 skipped; `uv run pytest tests/test_demo tests/test_smoke.py -q -n auto --dist loadscope` 58 passed; `uv run python manage.py makemigrations contributors demo --check --dry-run` no changes; `uv run pre-commit run --all-files` passes. Opened the tab, both add pages, edit and remove as regular.user on the seeded private dataset through the test client against the dev database: all 200.
Next: T005, the documentation.
Watch: a person added from the tab now holds the view level and no guardian row, so on a private record the permission backends still guard they cannot open it until the backend switches. The :outline attribute on the level badge in access.html is a Cotton expression that cannot be resolved, so it was never applied; left alone so the page draws as approved.

## 2026-10-06T12:43:11Z · Implementer US1 · T005

Did: docs/user-guide/crediting-a-record.md (linked from the user guide index): the tab, who may change it, adding from the portal, roles, removing. docs/portal-development/contributors.md: new section The Contributors tab (registered types get it with no configuration, the page classes and addresses, levels, REQUIRED_LEVEL, RecordAccess and how a page asks whether a person may view, edit or manage, Person.can_sign_in, Crediting and its codes); the sentence on who may edit a profile now points at can_sign_in, and the note that creating a credit grants nothing now says what Crediting.add gives. CHANGELOG entry under Unreleased.
Verified: ran every code block of the new portal-development section through a throwaway test (deleted afterwards) with a project, dataset, registered sample and person: all ran as written. The kit's docs audit (`forgekit.docs_check.audit(repo, base="origin/main")`) now lists four names: ContributionMove (moving and order, US6), level_choices (levels on the edit page, US4), give_level in demo/seed/common.py (US4, with the rows it sits beside) and ContributorSeed (the seed command, US7). Before this story's docs it listed 13.
Next: the full gate once, then the completion report.
Watch: the user guide page describes only what the tab does today: adding from the portal, roles, removing. ORCID, ROR and by-hand adding, the affiliation choice, levels on the edit page and ordering are for the stories that own them to add to it.

## 2026-10-06T12:45:24Z · Implementer US1 · T003

Did: renamed tests/test_contrib/test_contributors/test_plugins/test_contribution_tab.py to test_shared.py. The conformance step of the full gate refused the first name because a test module has to mirror a source module, and the tab's pages live in plugins/shared.py. The classes in it are unchanged.
Verified: `forge verify --repo . --base origin/main --steps conformance` is rerun after the rename (result in the report).
Next: the completion report.
Watch: tasks T007, T012, T017, T023, T027 and T030 in tasks.md name test_plugins/test_contribution_tab.py. Their stories add their classes to test_shared.py, which the conformance rule requires.

## 2026-10-06T13:05:27Z · Implementer US2 · T006

Did: added TestCreditedFrom to tests/test_contrib/test_contributors/test_services/test_crediting.py: adding with an organization (on each record type), the organization listed once, an organization already listed, added with none whatever the primary affiliation is, a refused add listing nothing, deleting the organization from the portal, update setting an organization, none, and leaving it alone, a refused update changing nothing, the organization staying when its last person leaves or is credited elsewhere and then being removable, the credited_from refusal with the people, and credited_from() on its own.
Verified: `uv run pytest tests/test_contrib/test_contributors/test_services/test_crediting.py::TestCreditedFrom -q -n0 -p no:randomly` failed 19 of 19 before the code: 18 with TypeError (add and update took no organization) and the primary-affiliation case with the old hook's value; after Crediting took the organization the deletion test failed with ProtectedError until the migration.
Next: T007, the page tests.
Watch: none.

## 2026-10-06T13:05:27Z · Implementer US2 · T007

Did: added TestAffiliationChoice and TestOrganizationRemoval to tests/test_contrib/test_contributors/test_plugins/test_shared.py, with the fixtures institutes and affiliate in the page conftest. They open the add page and the edit page through the test client, find the radio buttons by field name and the checked one by attribute, and read the tab's entries from the context.
Verified: before the code, 16 of 108 new cases failed: an organization the person holds no affiliation with was accepted, deleting an organization raised ProtectedError, the edit page selected the primary affiliation for a person credited from none, and an organization made for a refused save was kept. The other cases pass on the prototype's code, which this story keeps, so I probed three of them: the tab falling back to the profile's primary organization, removable fixed to true, and the remove page's refusal swallowed each made at least one test fail, and the file was restored after each.
Next: T008.
Watch: the removal page for an organization people are credited from is also linked from the tab as "See who", so the remove address is on the page either way and the tests read entry.removable from the context.

## 2026-10-06T13:05:27Z · Implementer US2 · T008

Did: added TestCreditedFromNone to tests/test_templates/test_contributor_components.py, parametrized over c-contributor.item and c-contributor.card.person: a credit with no organization shows none, a credit shows the one it names, a person shows their primary organization, and a person handed over as a plain contributor row does too.
Verified: `uv run pytest tests/test_templates/test_contributor_components.py::TestCreditedFromNone -q -n0 -p no:randomly`: before the template change the two "shows none" cases failed and the other four passed.
Next: T009.
Watch: the tests are in tests/test_templates/, not the test_components.py module the brief names. tests/test_templates/ is the repository's declared non-mirror path for component tests (pyproject [tool.forge.conformance]); a module of that name under test_contributors mirrors no source module, and the conformance step would refuse it.

## 2026-10-06T13:05:44Z · Implementer US2 · T008

Did: checked the note above. A throwaway tests/test_contrib/test_contributors/test_components.py, removed again, was refused by `forge verify --repo . --base origin/main --steps conformance` with "mirrors no source module (expected fairdm/contrib/contributors/components.py ...)". The T008 tests stay in tests/test_templates/test_contributor_components.py.
Verified: the conformance output above, read directly.
Next: T009.
Watch: none.

## 2026-10-06T13:05:44Z · Implementer US2 · T009

Did: Crediting.add(contributor, *, organization=None) and update(contribution, *, roles, organization=UNCHANGED) list the organization on the record once through list_organization, and remove refuses an organization people are credited from with code credited_from and the people in params; credited_from() maps organization id to people. Contribution.affiliation is SET_NULL (migration 0023_credited_from_set_null, applied to the dev database with `DJANGO_ENV=development DJANGO_SETTINGS_MODULE=config.devserver uv run python manage.py migrate`) and Contribution.set_default_affiliation is deleted. plugins/shared.py: AffiliationChoice (the form behind c-contribution.affiliation, fields affiliation and affiliation_name) replaces affiliation_choice, read_affiliation and credit_from; the edit page, the add page's portal, registry and by-hand ways, and the remove page call it and Crediting. c-contributor.item and c-contributor.card.person show no organization for a credit that names none. demo/seed/contributors.py affiliate() credits through Crediting.
Pre-existing test updated: tests/test_contrib/test_contributors/test_models.py, test_contribution_default_affiliation, which asserted the deleted hook, is now test_a_credit_is_not_given_the_primary_affiliation and asserts the credit holds none.
Template changes: item.html and card/person.html change the fallback expression only (decisions D15). No template under contributors/plugins/ or cotton/contribution/ changed, and no context or field name changed: the pages still pass affiliation (the choice), errors.affiliation, entry.attached and entry.removable.
Verified: `uv run pytest tests/test_contrib/test_contributors tests/test_templates -q -n auto --dist loadscope` 1333 passed; `uv run python manage.py makemigrations --check --dry-run` reports only orbit; `uv run pre-commit run --all-files` passes. Ran the seed command in a throwaway test against the test database (deleted afterwards), twice, the second time with --keep-records: Lea Brandt and Regular User are credited from Karlsruhe, Yusuf Demir from Tübingen, each organization is listed once. The development database was not reseeded.
Next: T010.
Watch: fairdm/core/plugins.py get_credits still falls back to the person's primary affiliation for the overview's People card when a credit names none. The brief names only the two components, so it is left; it shows an organization on the overview for a person the tab shows with none (concern in the report). The seeds other than seed_contributors, and generate_fake_data, now credit people from none (decisions D16).

## 2026-10-06T13:05:44Z · Implementer US2 · T010

Did: docs/user-guide/crediting-a-record.md says how the organization is chosen, why it does not follow the profile, how it is changed, and when an organization can be removed. docs/portal-development/contributors.md replaces the section on the crediting organisation default and the sentence quoting the deleted hook, and documents Crediting's organization argument, UNCHANGED, list_organization, credited_from, the credited_from refusal and AffiliationChoice. CONTEXT.md's Contribution entry says a contribution carries the organization a person is credited from. Changelog: Added, Changed and Removed entries.
Verified: `forgekit.docs_check.audit(Path("."), base="origin/main")` lists the same four names as before this story (ContributionMove, ContributorSeed, give_level, level_choices) and none of mine. The code blocks that call Crediting and AffiliationChoice are the calls the tests make.
Next: the full gate, then the report.
Watch: none.

## 2026-10-06T13:40:16Z · Implementer US3 · T011

Did: tests/test_contrib/test_contributors/test_services/test_registries.py (TestSearchOrcid, TestFetchOrcid, TestSearchRor, TestFetchRor, TestProfileFromRegistry) with requests.get replaced by the RegistryNetwork fixture in the contributors conftest. The replaced answers are trimmed copies of the recorded ones, kept in tests/test_contrib/test_contributors/recorded/ (the ORCID record cut to the name and the employments, the ROR search to five organizations); no test reads from specs/. The tests cover a search by name and by iD, the keys the template reads, the term in params and never in the address, the limit and the more flag, a record with no public name and a withdrawn organization left out, a timeout, a connection error, a 500, a 429 and an unreadable answer each raising RegistryUnavailable, a malformed identifier making no request, and a profile made from a record, found again by identifier and never by name.
Verified: `uv run pytest tests/test_contrib/test_contributors/test_services/test_registries.py -q -n0 -p no:randomly` failed at collection before the code (ModuleNotFoundError for services.registries) and passed 90 after it. Six mutations of services/registries.py each made tests fail and were restored: the ORCID pattern off (12 failed), the ROR pattern off (25), no timeout (4), a withdrawn organization kept (3), the profile matched by name (4), the ROR more flag fixed false (2).
Next: T012.
Watch: fetch returns None for a malformed identifier, a 404, no public name and a withdrawn organization; decisions D17.

## 2026-10-06T13:40:16Z · Implementer US3 · T012

Did: TestAddPages, TestAddFromRegistry and TestAddByHand in tests/test_contrib/test_contributors/test_plugins/test_shared.py, with the fixtures way and way_person (ORCID behind the person page, ROR behind the organization page) built from the replaced responses. They cover all three ways in one response, reopening on the way named by via in the address, each tab keeping its own term, the portal search saying when there are more results, nobody but a manager making anything or asking a registry (a reader, a signed-in stranger and a visitor, seven requests each), the registry search, no results, the more flag, a chosen record fetched by identifier, adding from a fresh fetch and not from posted fields, a malformed or unknown identifier making nothing, an existing profile used, the duplicate and superuser refusals, the organization choice for a person from ORCID and by hand, a registry that cannot be reached (200, the line on the tab, the other two ways working), a person needing both names, the optional fields stored, the email stored without an account or mail, an email the portal holds refused on the field without naming or linking its owner, the same name offered and still makeable for a person, never twice for an organization, and the country by name or code.
Verified: before the code `uv run pytest tests/test_contrib/test_contributors/test_plugins/test_shared.py::TestAddPages ...::TestAddFromRegistry ...::TestAddByHand -q -n auto --dist loadscope -p no:randomly` failed 220 of 352 cases (KeyError on the new context names, no profile made from the registry, nothing stored for the optional fields). The 132 that passed already are what the prototype kept: the three ways in one response, reopening, each term, the access refusals, a portal search asking no registry. After the code was written I probed the cases that had passed on the prototype by mutating the page: via fixed to portal (65 failed), manager_only off (1), the registry asked whatever the tab (2), the credit validation of the registry way off (10), a posted record trusted in place of the fetch (4); the profile made outside the transaction passed all of them, so I added the refused-credit case (an organization made for a refused credit is not kept) and it fails (4) with the transaction removed. After the code: 356 passed, the 352 above and the four of the refused-credit case.
Next: T013.
Watch: ruff format had reformatted five spots of story 1 and 2 tests in test_shared.py and removed one unused import; I put them back exactly (git diff against the verified base shows only the two imports I had to extend). The tests of both stories are untouched.

## 2026-10-06T13:40:16Z · Implementer US3 · T013

Did: services/registries.py (Orcid, Ror, RegistryUnavailable and ask, the one function that makes a request); ORCID_PATTERN and ROR_PATTERN named in models.py in place of two literals; NewPersonForm and NewOrganizationForm and the three ways on both add pages in plugins/shared.py; ORCID_RECORDS, ROR_RECORDS, registry_delay and time.sleep deleted. AffiliationChoice.choice() selects a person's primary affiliation before the employer ORCID lists, so a person the portal holds is offered their own.
Template changes, all in the two approved add templates and none moving or rewording anything drawn: one new plain sentence where the portal results end and one where the registry results end, each only when the matches are more than are shown (`data-results="more"`), and one new sentence on the registry tab when the registry cannot be reached (`data-registry="unavailable"`), which replaces the no-results block in that case. The sentences are "There are more matches than are shown, so add more of the name to narrow the search." and "Searching ORCID is unavailable right now, but the other two tabs still work." (ROR on the organization page). No context or form field name the templates read changed.
Verified: `uv run pytest tests/test_contrib/test_contributors tests/test_templates -q -n auto --dist loadscope` 1779 passed; the 90 registry cases and the 356 page cases pass; `uv run pre-commit run --all-files` passes. No migration; the development database is untouched.
Next: T014.
Watch: decisions D17 to D24. A person entered by hand with an email is INVITED and the portal's password reset page mails the address (D19).

## 2026-10-06T13:40:16Z · Implementer US3 · T014

Did: docs/user-guide/crediting-a-record.md describes the three ways of adding, what each registry match shows, what is made, the same-name offer and the refusals; docs/portal-administration/looking-up-contributors.md (new, in the toctree and linked from managing_contributors.md) says the server must reach pub.orcid.org and api.ror.org, the five-second timeout, the limit of ten, what the tab does when a registry cannot be reached, and the state of what is made; docs/portal-development/contributors.md documents Orcid, Ror, RegistryUnavailable, ask, NewPersonForm and NewOrganizationForm with calls the tests make. CHANGELOG.md has an Added entry.
Verified: `forge verify --repo . --base origin/main --steps docs` lists only ContributionMove, ContributorSeed, give_level and level_choices, the four names that belong to later stories; before the page for `ask` it also listed `ask`. The examples on the developer page are the calls test_registries.py makes.
Next: the full gate and the report.
Watch: none.
