# Progress: people, organizations and a record's credits can be read through the API

## 2026-10-12T09:51:21Z · orchestrator · research and plan

Research, plan and task list written against origin/main at 5201beed. 23 tasks in four stories,
all open. No migration and no new dependency. Started on the maintainer's instruction while #383
is open.

## 2026-10-12T10:09:36Z · Implementer US1 · T001

Did: Added TestCredit (tests/test_api/test_viewsets.py) and TestCreditComponent (tests/test_api/test_schema.py): the credit keys, DataCite name and identifier mapping, empty affiliation, organizational credit, order, empty list, deleted contributor and affiliation, create and partial change bodies, schema component keys.
Verified: uv run pytest -q -n0 tests/test_api/test_viewsets.py::TestCredit tests/test_api/test_schema.py::TestCreditComponent -> 29 failed, all on the old credit shape (key set differs, KeyError name/uuid/name_identifiers), none on an import or fixture error.
Next: T002.
Watch: TestCompleteRecord.test_a_credited_contributor_is_named_with_roles_and_affiliation and TestReferencesFollowTheLists.test_a_credit_to_a_listed_contributor_is_a_reference read the old credit keys and cannot stay as they are; they are changed in T005 and named in progress.

## 2026-10-12T10:09:58Z · Implementer US1 · T002

Did: Replaced TestReferencesFollowTheLists.test_a_credit_to_that_contributor_reads_null (named by the brief) with test_a_credit_to_that_contributor_names_them_and_gives_no_address, for a superuser and the anonymous account: uuid and url null, name, ORCID name identifier and two roles present. Added the add_credit helper beside TestCredit.
Verified: uv run pytest -q -n0 tests/test_api/test_viewsets.py::TestReferencesFollowTheLists -> 2 failed (KeyError uuid, old shape), 5 passed.
Next: T003.
Watch: none.

## 2026-10-12T10:10:36Z · Implementer US1 · T003

Did: Added TestCreditQueries: a page of 12 records, each with 3 person credits holding an identifier and an affiliation with an identifier plus an organization credit, runs the queries of a page of 2 records with 1 person credit each, for projects, datasets, one sample type and one measurement type.
Verified: uv run pytest -q -n0 tests/test_api/test_viewsets.py::TestCreditQueries -> 4 passed on the old code, as expected: the old credit read nothing per credit. This is a guard for the rewrite in T005; it is probed there by removing the new prefetches and watching it fail.
Next: T004.
Watch: none.

## 2026-10-12T10:13:59Z · Implementer US1 · T004

Did: Moved every test that named api:contributor-list or api:contributor-detail to api:person-* / api:organization-* (tests/test_api/test_router.py, test_filters.py, test_viewsets.py, test_schema.py), including routable_models(), the ContributorViewSet import and the Contributors heading in test_schema.py, the contributor kind of TestQueryCount (now people and organizations kinds), TestChangedSince and TestNoServerErrors (which parametrize over routable_models). Added route tests (list and record routes, 404 at the old address and at the other kind's route, root links) and TestPeopleList and TestOrganizationsList (kind only, exact list keys, keys left out, no added or modified but orderable, primary organization from a verified current primary entry only).
Verified: uv run pytest -q -n0 tests/test_api/test_viewsets.py tests/test_api/test_router.py tests/test_api/test_filters.py tests/test_api/test_schema.py -> all new and moved tests red on NoReverseMatch for person-* / organization-* (routes do not exist yet) or on the old credit shape.
Next: T005, then T006.
Watch: pre-existing tests changed beyond a route rename, each because the brief's list shape (D10, D11) or the new credit shape leaves the old assertion with nothing to read:
- TestContributor.test_a_person_is_returned_with_what_their_profile_page_shows: dropped the assertions on type, profile and links (a list entry has none; the single person serializer arrives with US2) and moved affiliation to primary_organization.
- TestContributor.test_an_organisation_is_returned_with_what_its_profile_page_shows: dropped type and the parent assertion (US3 adds parent); added name.
- TestContributor.test_no_response_carries_an_account_detail: added the organizations list to the responses it walks.
- TestCompleteRecord.test_a_credited_contributor_is_named_with_roles_and_affiliation: reads credit["uuid"] and credit["affiliation"][0]["uuid"] instead of the old nested contributor and affiliation references.
- TestReferencesFollowTheLists.test_a_credit_to_a_listed_contributor_is_a_reference: reads the credit's uuid.
- TestContributorListEndpoint and TestVisibilityFilterContributors: parametrized over both new lists.

## 2026-10-12T10:16:18Z · Implementer US1 · T005

Did: fairdm/api/serializers.py: NameIdentifierSerializer, CreditAffiliationSerializer (ROR ID else first identifier, null keys when none), ContributionListSerializer (leaves out a credit whose contributor is gone; fills given and family name for credits without the annotation with one query), the rewritten ContributionSerializer (uuid, url, name, name_type, given_name, family_name, name_identifiers, affiliation as a list, roles; uuid and url null for an account the people list leaves out, read from the context's hidden_contributors set through the new RecordReferenceField.hidden_contributor_pks), and RecordSerializer.load_related() prefetching contributor and affiliation identifiers and annotating the person's names on the credit queryset.
Verified: uv run pytest -q -n0 tests/test_api/test_viewsets.py::TestCredit tests/test_api/test_schema.py::TestCreditComponent tests/test_api/test_viewsets.py::TestCreditQueries -> 30 passed, 8 failed; the 8 only reverse api:person-detail / api:organization-detail, which T006 adds. Probed TestCreditQueries: without the identifier prefetches 4 failed, without the name annotation 4 failed. uv run pre-commit run --files fairdm/api/serializers.py -> passed (ruff, mypy).
Next: T006.
Watch: the credit's url still resolves through the old contributor route until T006 changes RecordReferenceField.route_name; test_the_contributor_list_leaves_the_account_out reverses person-detail and stays red until T006. In TestReferencesFollowTheLists the replaced test now compares the credit name with get_full_name_display, because the anonymous account's stored name is empty.

## 2026-10-12T10:19:45Z · Implementer US1 · T006

Did: fairdm/api/serializers.py: OrganizationReferenceSerializer (CreditAffiliationSerializer builds on it), PersonListSerializer, OrganizationListSerializer, RecordReferenceField.route_name returning api:person-detail or api:organization-detail from the real class, ContributorSerializer deleted. fairdm/api/viewsets.py: PersonViewSet (Person.objects.real(), identifiers and affiliations__organization prefetched, ordered by name then pk) and OrganizationViewSet, ContributorViewSet deleted, module docstring corrected. router.py registers people and organizations. schema.py CORE_HEADINGS gains people and organizations, loses contributors. settings.py endpoint table. plugins/overview.py builds the profile's API address from the contributor's real type, with a test for each kind. Both viewsets are AllowAny with no visibility rule, as the old one was.
Verified: uv run pytest -q tests/test_api -n auto --dist loadscope -> 1186 passed. uv run pytest -q tests/test_contrib/test_contributors tests/test_templates/test_contributor_cards.py tests/test_templates/test_contributor_components.py -n auto --dist loadscope -> 2161 passed, 6 skipped. Probe: with overview.py reverted the two new profile-link tests fail. pre-commit on the api files and overview.py passed (ruff, mypy).
Next: T007 documentation.
Watch: an organization's country is None when unset (CountryField hands back None, not a Country with an empty code). The two new profile-link tests in tests/test_contrib/test_contributors/test_plugins/test_overview.py are an addition outside the files T004 names, written because the profile page's API address is part of this task.

## 2026-10-12T10:25:28Z · Implementer US1 · T007

Did: docs/portal-development/restful-api.md: endpoint table, a "A credit on a record" section with an example and a table mapping each credit field to its DataCite property, the hidden-account sentence, the People and Organizations sections (list entry only) in place of Contributors, the serializer reference table (new classes ContributionListSerializer, NameIdentifierSerializer, CreditAffiliationSerializer, PersonListSerializer, OrganizationListSerializer, OrganizationReferenceSerializer, plus PersonViewSet and OrganizationViewSet named in the two sections), the documentation headings and the changed-since sentence. docs/user-guide/reading-records-with-a-script.md: the people and organizations paragraph and the sentence on what /api/v1/ links to. specs/011-restful-api/spec.md: the input paragraph, scenarios 1 and 5, FR-001, FR-003, FR-006 and FR-015 edited to the present behaviour; the other files in specs/011-restful-api/ untouched.
Verified: kit/forge verify --repo <worktree> --base origin/main -> conformance, docs, uv:lint, uv:typecheck, uv:test and uv:build all passed (exit 0).
Next: completion report.
Watch: the docs and spec pages describe the single record as returning the list fields, which is what it does until the fuller serializers land.

## 2026-10-12T10:38:28Z · Implementer US2 · T008

Did: tests/test_api/test_viewsets.py, TestPeopleList: a superuser and the anonymous account are absent from the list and answered 404 by address, the list is paged, sorts by name both ways, and narrows by modified_after. The unclaimed-profile test was already there.
Verified: uv run pytest -q -n0 tests/test_api/test_viewsets.py::TestPeopleList -> passed once T012 landed (the behaviour existed from story 1). Probe: with Person.objects.real() changed to .all() the hidden-account, paging and ordering tests fail (6 failed across the three classes).
Next: T009.
Watch: nothing in these tests failed before T012 because the behaviour is story 1's; the probe is the evidence they can fail.

## 2026-10-12T10:38:29Z · Implementer US2 · T009

Did: tests/test_api/test_viewsets.py, TestPerson (new class): exact keys of a single person, the list entry's fields unchanged on the record, profile, alternative_names, links (a non-web address left out), languages, image, an affiliation's organization/type/start/end/is_primary, type for each level, null dates, a pending affiliation absent, an ended one present after the current ones, primary first, an explicit set of forbidden account-state keys walked over the list and the record at any depth, and the query count for a record with 2 versus 12 affiliations.
Verified: red before T012 (16 failed); uv run pytest -q -n0 tests/test_api/test_viewsets.py::TestPerson -> 20 passed after T012.
Next: T010.
Watch: the moved TestContributor person test is not edited; profile and links are asserted in TestPerson.

## 2026-10-12T10:38:29Z · Implementer US2 · T010

Did: tests/test_api/test_filters.py, TestPeopleFilters: organization keeps verified affiliations that have not ended and not pending, ended or other organizations; a person with a past and a current affiliation is listed once; a database number and an unknown identifier for organization are 400; identifier by bare value, by https, http and trailing-slash address, trimmed; a value written with spaces; a value nobody holds; a value a superuser holds; the two filters together. PersonFactory is added to the file's existing factory import.
Verified: red before T012 (10 failed); uv run pytest -q -n0 tests/test_api/test_filters.py::TestPeopleFilters -> 12 passed after T012. Probes: dropping the end_date clause, the type clause, and the space removal each fail one test.
Next: T012.
Watch: none.

## 2026-10-12T10:38:29Z · Implementer US2 · T012

Did: fairdm/api/serializers.py: AffiliationSerializer and PersonSerializer(PersonListSerializer) adding alternative_names, profile, links, languages, image, affiliations (from get_affiliation_history(), current then past), with Meta.fields on the list serializer annotated tuple[str, ...] so the subclass type-checks. fairdm/api/filters.py: IdentifierFilter and PersonFilterSet (organization as a ModelChoiceFilter on uuid, identifier). fairdm/api/viewsets.py: filterset_class and get_serializer_class on PersonViewSet.
Verified: uv run pytest -q -n0 tests/test_api -> 1225 passed, including TestQueryCount's people kind. uv run pre-commit run --files fairdm/api/filters.py fairdm/api/serializers.py fairdm/api/viewsets.py -> ruff, ruff format, mypy, deptry passed.
Next: T013.
Watch: the schema generator warns that it cannot guess the type of the organization filter and defaults to string; the parameter is offered and works.

## 2026-10-12T10:38:29Z · Implementer US2 · T013

Did: tests/test_api/test_schema.py, TestPeopleComponents: the list entry component has the list fields only, the single person's has them plus the six, an affiliation lists its five keys, the list offers organization and identifier, a record offers neither. docs/portal-development/restful-api.md: the single person's fields and an affiliation in tables, what the list leaves out, the two filters with an example request each, what is never returned, and PersonSerializer, AffiliationSerializer, PersonFilterSet and IdentifierFilter in the reference table. docs/user-guide/reading-records-with-a-script.md: a paragraph on the single person and the two filters.
Verified: uv run pytest -q -n0 tests/test_api/test_schema.py -> passed. Probes: the list serving the full person fails the entry test, removing filterset_class fails the filters test.
Next: full verify, then the completion report.
Watch: none.

## 2026-10-12T10:45:50Z · Implementer US3 · T014

Did: added test_the_list_is_paged, test_the_list_sorts_by_name_in_either_direction (both directions) and test_the_list_narrows_by_the_moment_an_organization_was_changed to TestOrganizationsList.
Verified: `uv run pytest -q -n0 tests/test_api/test_viewsets.py::TestOrganizationsList` 12 passed. They pass on arrival because the list route and its backends came with story 1. Probed by setting filter_backends=[] and pagination_class=None on OrganizationViewSet: 12 failed; the file was restored.
Next: T015, the single organization.
Watch: none.

## 2026-10-12T10:47:15Z · Implementer US3 · T015

Did: added TestOrganization to tests/test_api/test_viewsets.py: the key set, equality with the list entry, profile/alternative_names/city, links, image, parent (named and null), sub_organizations by name, member shape and type wording, ordering (owner, admin, member then name), absence of pending, ended, superuser and anonymous members, no account state keys. The parent assertions that story 1 took out of TestContributor are in test_the_parent_is_named_by_identifier_address_and_name.
Verified: `uv run pytest -q -n0 tests/test_api/test_viewsets.py::TestOrganization` 18 failed, 2 passed; the failures are KeyError for each missing key (members, parent, links, sub_organizations, profile, image) and the key-set assertion. The two passing are the list-entry equality and the account-state guard, which hold already.
Next: T016, the organization filters.
Watch: the ordering of sub_organizations (by name) is this story's reading of "by name" in the brief.

## 2026-10-12T10:47:58Z · Implementer US3 · T016

Did: added TestOrganizationFilters to tests/test_api/test_filters.py: type, country, parent by short identifier, a database number and an unknown identifier for parent refused with 400, top_level true and false, identifier bare and as an address (https, http, trailing slash, padded), no holder, and the filters combined.
Verified: `uv run pytest -q -n0 tests/test_api/test_filters.py::TestOrganizationFilters` red before T018: the filters are not declared, so every narrowing test returns the whole list and the refusals answer 200.
Next: T017, the query count for a single organization.
Watch: the unknown-type case is deliberately untested; the spec names no behaviour for it.

## 2026-10-12T10:48:24Z · Implementer US3 · T017

Did: added TestOrganizationQueries: one organization with two members, one with thirty, each with a parent and two sub-organizations; the query count of the single record is equal, and the test asserts the members are present so it cannot pass with none.
Verified: `uv run pytest -q -n0 tests/test_api/test_viewsets.py::TestOrganizationQueries` fails with KeyError 'members' before T018.
Next: T018, the serializer, the member serializer, the filter set and get_serializer_class.
Watch: probe this test after T018 by dropping the member prefetch.

## 2026-10-12T10:50:22Z · Implementer US3 · T018

Did: added OrganizationSerializer (alternative_names, profile, city, links, image, parent, sub_organizations, members), MemberSerializer, PersonReferenceSerializer and AffiliationTypeField (the wording of an affiliation's type, now used by AffiliationSerializer too); OrganizationFilterSet with type, country, parent, top_level and identifier; OrganizationViewSet.get_serializer_class() and a single-record queryset that selects the parent and prefetches sub_organizations and the current verified affiliations with their people. The list queryset is unchanged.
Verified: `uv run pytest -q -n0` on TestOrganization, TestOrganizationQueries, TestOrganizationsList and TestOrganizationFilters: 47 passed. `uv run pytest -q -n auto --dist loadscope tests/test_api`: 1269 passed. Probes: removing the affiliations Prefetch makes TestOrganizationQueries fail (35 queries against 7); removing the hidden-account exclusion fails both hidden-member cases. Both files restored.
Next: T019, schema tests and the Organizations section of the documentation.
Watch: AffiliationSerializer changed from a method field to AffiliationTypeField (story 2's code, same output); decisions.md D17.

## 2026-10-12T10:51:30Z · Implementer US3 · T019

Did: added TestOrganizationComponents to tests/test_api/test_schema.py (list component, single component, member component, the five filters on the list and none on the record). Rewrote the Organizations section of docs/portal-development/restful-api.md: the single organization's fields and members in tables, what the list leaves out, one example request per filter, that only current verified members are listed, the classes behind it, and rows for OrganizationSerializer, MemberSerializer, AffiliationTypeField, PersonReferenceSerializer and OrganizationFilterSet in the serializer table. Added a paragraph for the single organization and its filters to docs/user-guide/reading-records-with-a-script.md, which described people and organizations and now would have left the organization record out.
Verified: `uv run pytest -q -n0 tests/test_api/test_schema.py::TestOrganizationComponents` 5 passed. Probed by returning the list serializer for every action and dropping the filter set: 3 failed; restored.
Next: the full verify, then the report.
Watch: the user guide page is outside the paths the brief names; the protocol asks for every page the story changed the truth of.

## 2026-10-12T11:05:23Z · Implementer US4 · T020

Did: tests/test_api/test_filters.py, TestContributorRecords: the project list and the dataset list narrowed to a person and to an organization return exactly the public records credited; a private project, a private dataset and a public dataset in a private project are never returned or counted for a visitor, for the person themself and for a member of the private record's team (each with a check that the plain list shows the caller the private records); a public project an organization owns and is not credited on is not returned; an unknown identifier, a superuser's, the anonymous account's and a database number give an empty list with status 200; the unfiltered list is not narrowed. A second commit credits an organization with no level, as a credit to one is stored.
Verified: red before T022 (20 failed, 1 passed): every narrowing test fails on the unfiltered list. After T022, uv run pytest -q -n0 tests/test_api/test_filters.py::TestContributorRecords -> 21 passed. Probes: reading get_public_projects()/get_public_datasets() instead fails the owned-project test; dropping get_visible() fails 5.
Next: T021.
Watch: none.

## 2026-10-12T11:05:23Z · Implementer US4 · T021

Did: tests/test_api/test_viewsets.py, TestContributorRecordAddresses: for a person and an organization, the projects and datasets addresses are absolute with the contributor as a query, requesting each returns the narrowed list, a list entry carries neither, and a private record the caller may see is credited on its own page and left out of the person's datasets list. Edits to earlier stories' tests, key sets only: PERSON_KEYS and ORGANIZATION_KEYS in tests/test_api/test_viewsets.py, and RECORD_ONLY_KEYS of the person and organization classes in tests/test_api/test_schema.py, each gaining projects and datasets.
Verified: red before T022: KeyError 'projects' and 'datasets' in the address tests and the four key-set assertions fail on the two extra keys; the list-entry test passes already. After T022 all pass.
Next: T022.
Watch: none.

## 2026-10-12T11:05:23Z · Implementer US4 · T022

Did: fairdm/api/filters.py: ContributorRecordsFilterSet with the one contributor filter. fairdm/api/viewsets.py: it is the filterset_class of ProjectViewSet and DatasetViewSet. fairdm/api/serializers.py: ContributorRecordsMixin with the projects and datasets address fields, used by PersonSerializer and OrganizationSerializer and added to their Meta.fields. decisions.md D18.
Verified: uv run pre-commit run --files fairdm/api/filters.py fairdm/api/serializers.py fairdm/api/viewsets.py -> ruff, ruff format, mypy and deptry passed. uv run pytest -q -n auto --dist loadscope tests/test_api -> 1306 passed, including TestQueryCount and TestCreditQueries unchanged.
Next: T023.
Watch: none.

## 2026-10-12T11:05:23Z · Implementer US4 · T023

Did: docs/portal-development/restful-api.md: the projects and datasets rows in the single person and single organization tables, the counts of fields a list entry leaves out, a subsection on the contributor filter with an example for a person and one for an organization, that it holds public records only whoever asks, ContributorRecordsFilterSet and ContributorRecordsMixin in the class table. docs/user-guide/reading-records-with-a-script.md: a worked step from a person to their datasets.
Verified: read against the branch; the addresses and the empty-list behaviour are the ones the tests in T020 and T021 pin.
Next: the full verify, then the report.
Watch: the same user guide page still says the portal root lists "projects, datasets and contributors" under "Find out what a portal offers"; that is story 1's wording and was left as it is.
