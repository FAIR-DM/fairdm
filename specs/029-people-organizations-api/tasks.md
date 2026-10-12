# Tasks: people, organizations and a record's credits can be read through the API

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md)

**Tests first**: in every story the test tasks come first and are seen to fail before the code
that makes them pass is written. API tests send requests to the real routes with `APIClient` and
assert on the response. Wording gets no tests.

**Format**: `[ID] [Story] Description`.

**Story order**: US1 to US4, one after another, each from the previous story's accepted commit.

## Phase 1: US-1, a developer's script attributes a record from one request (P1)

This story changes what every record returns and moves contributors to their two new addresses.

- [ ] T001 [US1] `tests/test_api/test_viewsets.py`, `TestCredit`: on a project, a dataset, a
  sample and a measurement, a credit for a person with an ORCID iD and an organization recorded on
  the credit carries `uuid`, `url`, `name`, `name_type`, `given_name`, `family_name`,
  `name_identifiers` with scheme and scheme address, `affiliation` with the organization's name,
  identifier, scheme, `uuid` and `url`, and `roles`. A person with neither has empty
  `name_identifiers` and `affiliation`, even when their profile has a primary affiliation. An
  organization's credit has `name_type` `Organizational` and null given and family names. The
  credit's `url` returns that person or organization. Credits come in the record's order. A record
  with none returns an empty list. A credit carries no key beyond those named here.
- [ ] T002 [US1] `tests/test_api/test_viewsets.py`, `TestReferencesFollowTheLists`: a credit held
  by a superuser or by the anonymous account is returned with its name, identifiers and roles and
  with `uuid` and `url` null. Replaces the case that expected the whole contributor to be null.
- [ ] T003 [US1] `tests/test_api/test_viewsets.py`, `TestCreditQueries`: the number of queries for
  a page of datasets is the same with one dataset holding one credit as with ten datasets holding
  five credits each, people and organizations mixed, with identifiers and affiliations. The same
  for projects and for one registered sample type and one measurement type.
- [ ] T004 [US1] `tests/test_api/test_router.py` and `tests/test_api/test_viewsets.py`: `people`
  and `organizations` each have a list and a record route, found by short identifier.
  `/api/v1/contributors/` and a record address beneath it are answered 404. The API root links to
  people and organizations and not to contributors. Every existing test that names
  `api:contributor-list` or `api:contributor-detail` is moved to the new routes, keeping what it
  asserts.
- [ ] T005 [US1] `fairdm/api/serializers.py`: `NameIdentifierSerializer`,
  `CreditAffiliationSerializer` and the rewritten `ContributionSerializer` (plan D1).
  `RecordSerializer.load_related()` and `RecordListSerializer` load identifiers and real `Person`
  instances so that T003 holds. A credit whose contributor is gone is left out.
- [ ] T006 [US1] `fairdm/api/serializers.py`, `viewsets.py`, `router.py`, `schema.py`,
  `settings.py` and `fairdm/contrib/contributors/plugins/overview.py`: `PersonListSerializer`,
  `OrganizationListSerializer`, `PersonViewSet` and `OrganizationViewSet` serving the list shape,
  the two routes, `RecordReferenceField.route_name()` returning the typed routes, the headings,
  the endpoint table, and the profile page's API address. `ContributorSerializer`,
  `ContributorViewSet` and the `contributors` route are deleted (plan D6).
- [ ] T007 [US1] Documentation: in `docs/portal-development/restful-api.md` the endpoint table,
  the shape of a credit and how each field corresponds to a DataCite creator or contributor, and
  the note on a credit held by an account the people list leaves out. In
  `docs/user-guide/reading-records-with-a-script.md` the paragraph on contributors. In
  `specs/011-restful-api/spec.md` every statement about the contributors endpoint and the shape
  of a credit, edited to read as the API now behaves (FR-027).

## Phase 2: US-2, a developer pages through the people a portal holds (P1)

- [ ] T008 [US2] `tests/test_api/test_viewsets.py`, `TestPeopleList`: the list holds people only.
  An entry carries `url`, `html_url`, `uuid`, `name`, `given_name`, `family_name`, `identifiers`,
  `primary_organization`, `added` and `modified`, and none of `profile`, `links`, `languages`,
  `affiliations`, `image` or `alternative_names`. A person whose primary affiliation has ended has
  no primary organization. A superuser and the anonymous account are absent, and each is answered
  404 by address. An unclaimed profile is listed. The list is paged, sorts by name ascending and
  descending, and narrows by `modified_after`.
- [ ] T009 [US2] `tests/test_api/test_viewsets.py`, `TestPerson`: a single person carries the list
  fields and `alternative_names`, `profile`, `links`, `languages`, `image` and `affiliations`.
  Each affiliation names its organization by `uuid`, `url` and `name` and gives `type`, `start`,
  `end` and `is_primary`. A pending affiliation is absent. An ended one is present with its end.
  No response about a person, list or record, has a key for an email address, a password, an
  account flag, a portal role, a sign-in date or a preference, at any depth.
- [ ] T010 [US2] `tests/test_api/test_filters.py`, `TestPeopleFilters`: `organization` returns the
  people with a verified affiliation to it that has not ended, and not a pending or ended one.
  `identifier` returns the one holder, given the bare value or its full address, and an empty list
  for a value nobody holds. A database number for `organization` is refused.
- [ ] T011 [US2] `tests/test_api/test_viewsets.py`, `TestPeopleQueries`: the query count for a
  page of people is the same for one person as for twenty with identifiers and affiliations.
- [ ] T012 [US2] `fairdm/api/serializers.py`, `viewsets.py`, `filters.py`: `PersonSerializer`,
  `OrganizationReferenceSerializer`, `PersonViewSet.get_serializer_class()`, `PersonFilterSet`
  and `IdentifierFilter` (plan D2, D4).
- [ ] T013 [US2] `tests/test_api/test_schema.py` and documentation: the generated documentation
  describes the people list entry and the single person with their own fields and lists the two
  filters. `docs/portal-development/restful-api.md` gains a People section: the two shapes, what
  the list leaves out, the filters, and what is never returned.

## Phase 3: US-3, a developer pages through the organizations a portal holds (P1)

- [ ] T014 [US3] `tests/test_api/test_viewsets.py`, `TestOrganizationsList`: the list holds
  organizations only. An entry carries `url`, `html_url`, `uuid`, `name`, `type`, `type_label`,
  `country`, `country_name`, `identifiers`, `added` and `modified`, and none of `profile`,
  `links`, `members`, `sub_organizations`, `parent`, `city` or `image`. The list is paged and
  sorts by name.
- [ ] T015 [US3] `tests/test_api/test_viewsets.py`, `TestOrganization`: a single organization
  carries the list fields and `alternative_names`, `profile`, `city`, `links`, `image`, `parent`,
  `sub_organizations` and `members`. Parent and sub-organizations are named by `uuid`, `url` and
  `name`. A member names the person the same way and gives the type of affiliation. A pending
  member, a member whose affiliation has ended and a member who is a superuser are absent. An
  organization with no parent has a null parent.
- [ ] T016 [US3] `tests/test_api/test_filters.py`, `TestOrganizationFilters`: `type`, `country`,
  `parent` by short identifier, `top_level` and `identifier` (bare and as an address) each return
  only what matches. A database number for `parent` is refused.
- [ ] T017 [US3] `tests/test_api/test_viewsets.py`, `TestOrganizationQueries`: the query count for
  a page of organizations is the same for one as for twenty, and for a single organization the
  same with one member as with thirty.
- [ ] T018 [US3] `fairdm/api/serializers.py`, `viewsets.py`, `filters.py`:
  `OrganizationSerializer`, the member serializer, `OrganizationViewSet.get_serializer_class()`
  and `OrganizationFilterSet` (plan D3).
- [ ] T019 [US3] `tests/test_api/test_schema.py` and documentation: the generated documentation
  describes the organization list entry and the single organization and lists the filters.
  `docs/portal-development/restful-api.md` gains an Organizations section, the serializer
  reference table names the new classes and drops the removed ones, and the list of documentation
  headings is corrected.

## Phase 4: US-4, a developer finds what a person or an organization is credited on (P2)

- [ ] T020 [US4] `tests/test_api/test_filters.py`, `TestContributorRecords`: the project list and
  the dataset list narrowed to a person return exactly the public records they are credited on.
  A private project, a private dataset and a public dataset in a private project are not returned
  and not counted, for a visitor, for the person themself and for a member of the private record's
  team. For an organization the lists match its profile page, including a project it owns. An
  identifier that names nobody, and one that names a superuser, give an empty list with status
  200. A database number is refused.
- [ ] T021 [US4] `tests/test_api/test_viewsets.py`: a single person and a single organization
  carry `projects` and `datasets`, and requesting each address returns the narrowed list.
- [ ] T022 [US4] `fairdm/api/filters.py`, `viewsets.py`, `serializers.py`:
  `ContributorRecordsFilterSet` on `ProjectViewSet` and `DatasetViewSet`, and the `projects` and
  `datasets` fields on `PersonSerializer` and `OrganizationSerializer` (plan D5).
- [ ] T023 [US4] Documentation: `docs/portal-development/restful-api.md` describes the
  `contributor` filter, that it returns public records only, and the two addresses on a person and
  an organization. `docs/user-guide/reading-records-with-a-script.md` shows going from a person to
  their datasets.
