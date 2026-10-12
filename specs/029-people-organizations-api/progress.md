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
