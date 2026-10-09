# Tasks: The REST API reads and writes complete records

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md)

**How this list was written**: as if the repository held no API at all, so that it describes the
whole feature and not what happens to exist. It was then checked against the code. A task is
ticked only where the code that satisfies it is cited and a passing test covers it. The evidence
for each ticked task is in `feature-state.json`.

**Tests first**: in every story the test tasks come first and are seen to fail before the code
that makes them pass is written. API tests send requests to the real routes with `APIClient`,
once for each kind of caller the scenario names, and assert on the response and on what is stored
afterwards. They use the demonstration types in `demo/`. Wording and layout get no tests.

**Format**: `[ID] [Story] Description`.

**Story order**: US1 to US6, one after another, each from the previous story's accepted commit.

## Phase 1: US-1, a developer reads a complete record with a script (P1)

This story lays the serializers the others stand on.

- [x] T001 [US1] `tests/test_api/test_serializers.py`, `TestRecordReferenceField`: a related
  record is returned as its short identifier and its address. A bare identifier is accepted, and
  so is the returned object. An unknown identifier is refused. A database number is refused.
- [x] T002 [US1] `tests/test_api/test_viewsets.py`, `TestCompleteRecord`: for a public project,
  dataset, sample and measurement with metadata recorded, the record endpoint returns its own
  fields, its parent, descriptions, key dates, identifiers, keywords and credited contributors.
  A dataset returns its licence and a project its owner. The parent's address returns the parent.
  A public dataset in a private project returns its project as null to a visitor and as the
  reference to someone at the view level on the project, and the same for a measurement whose
  sample is in a private dataset.
- [x] T003 [US1] `tests/test_api/test_viewsets.py`, `TestCommonFields`: a record of every
  registered demonstration sample type carries the fields common to all samples and every field
  its type declares. The same for every measurement type, including its measured values.
- [x] T004 [US1] `tests/test_api/test_viewsets.py`, `TestNoDatabaseNumbers`: the list and record
  responses of every endpoint contain no `id` or `pk` key at any depth, and no relation is an
  integer.
- [x] T005 [US1] `tests/test_api/test_viewsets.py`, `TestContributor`: a person and an
  organisation are returned with their public profile fields. No response carries an email
  address, a password or an account flag. A superuser account is not in the list.
- [x] T006 [US1] `tests/test_api/test_viewsets.py`, `TestListAndRecordRoutes`: projects, datasets,
  contributors and every registered type have a list and a record route. A record is found by its
  short identifier. An unknown identifier and an unregistered type are answered 404.
- [x] T007 [US1] `tests/test_api/test_pagination.py`, `TestPageEnvelope`: a list carries the
  total, and the next and previous addresses, on the first, a middle and the last page. The total
  counts only what the caller may see.
- [x] T008 [US1] `tests/test_api/test_filters.py`, `TestVisibilityOfProjectsAndDatasets`: a
  private project or dataset is listed for someone holding the view level, directly or from the
  project above, and for nobody else. Public ones are listed for everyone, once.
- [x] T009 [US1] `tests/test_api/test_filters.py`, `TestVisibilityOfSamplesAndMeasurements`: on
  the real routes, samples and measurements in a private dataset are listed for someone with a
  level on the dataset and for nobody else.
- [x] T010 [US1] `tests/test_api/test_permissions.py`, `TestReadingARecord`: a public record is
  returned to a visitor. A private project or dataset is answered 404 to a visitor and to a
  signed-in person with no level, and returned to someone at the view level.
- [x] T011 [US1] `tests/test_api/test_permissions.py`, `TestReadingASampleOrMeasurement`: the same
  three callers against a sample and a measurement in a private dataset, on the real routes. A
  signed-in person with no level is also answered 404 on a private dataset's record route.
- [x] T012 [US1] `tests/test_api/test_viewsets.py`, `TestFiltering`: a registered type's declared
  filter narrows its list to matching records. A sample list and a measurement list narrowed by
  their dataset's short identifier, and a measurement list by its sample's, return only that
  parent's records, for a type that declares no such filter too. A database number in the same
  parameter is refused.
- [x] T013 [US1] `tests/test_api/test_viewsets.py`, `TestOrdering`: projects, datasets and every
  registered sample and measurement type return their list in a named order, ascending and
  descending.
- [x] T014 [US1] Implement to make T001 to T013 pass (plan D1, D2, D3 without `perform_destroy`
  and the catalogues). Remove `MeasurementConfig.serializer_fields`. The viewsets
  stop calling `build_model_serializer`. The function stays until T025, because the hand-built
  write tests still import it.
- [x] T015 [US1] Documentation: the reading half of `docs/portal-development/restful-api.md`, and
  a page for people using a portal on reading records with a script, in a table of contents. An
  architecture decision record under `docs/adr/` for references by short identifier.

## Phase 2: US-2, a member of a record's team creates, changes and deletes records (P1)

- [x] T016 [US2] `tests/test_api/test_viewsets.py`, `TestCreating`: on the real routes, someone at
  the edit level creates a sample of each demonstration type in a dataset, a measurement of each
  type on a sample with its values, and a dataset in a project. Any signed-in person creates a
  project. Each response is the complete record and each record is stored where it was sent.
- [x] T017 [US2] `tests/test_api/test_viewsets.py`, `TestCreatorIsCredited`: the person who
  creates a record through the real routes is listed on it at the manage level, and a `created_by`
  sent by the caller is ignored.
- [x] T018 [US2] `tests/test_api/test_viewsets.py`, `TestChanging`: a partial change alters the
  named field and nothing else. A full replacement sets the writable fields. A value sent for a
  read-only field, such as a description or the added date, changes nothing.
- [x] T019 [US2] `tests/test_api/test_viewsets.py`, `TestDeleting`: a deleted record is gone and
  then answered 404. A project with a public dataset, and a sample with measurements, are refused
  with a reason and nothing is deleted.
- [x] T020 [US2] `tests/test_api/test_viewsets.py`, `TestValidation`: a missing required field
  and an unacceptable value are answered 400 naming each field, with nothing saved. A parent that
  does not exist and one the caller may not add to get the same answer. An unparseable body is
  answered 400.
- [x] T021 [US2] `tests/test_api/test_permissions.py`, `TestWhoMayWrite`: on project routes, a
  write with no authentication is answered 401, by a signed-in person with no level on a public
  project 403 and on a private one 404, and by a viewer of a private project 403.
- [x] T022 [US2] `tests/test_api/test_permissions.py`, `TestWhoMayWriteSamplesAndMeasurements`:
  the same callers against a sample and a measurement on the real routes, and someone at the view
  level on a dataset cannot create in it.
- [x] T023 [US2] `tests/test_api/test_permissions.py`, `TestManageLevel`: on the real routes,
  someone at the edit level cannot change a record's visibility or move it, someone at the manage
  level can, a move that leaves nobody able to manage the record is refused, and sending the
  parent or visibility a record already has needs only the edit level.
- [x] T024 [US2] `tests/test_api/test_viewsets.py`, `TestNoServerErrors`: for every route, an
  empty body, a body of wrong types and a valid body are each answered below 500.
- [x] T025 [US2] Implement to make T016 to T024 pass (plan D1 writable parents, D3
  `perform_destroy`). Delete `build_model_serializer`, and in the same commit delete the
  hand-built write tests that T016 to T023 replace (`TestCreatedRecordsListTheirCreator`,
  `TestVisibilityNeedsManage`, `TestMovingARecordThroughTheApi`,
  `TestCreatingARecordThroughTheApi`, `TestParentChoicesThroughTheApi` and their fixtures in
  `tests/test_api/test_viewsets.py`).
- [x] T026 [US2] Documentation: creating, changing and deleting, what is read-only, who may do
  what, and the refusals, in both pages from T015.

## Phase 3: US-3, a portal developer gets an API for a registered type (P2)

- [x] T027 [US3] `tests/test_registry/test_factories.py`, `TestSerializerFactory`: with no API
  configuration the serializer carries the common fields and the default fields. With
  `serializer_fields` it carries those. With only `fields` it carries those. It builds on the
  sample or measurement base.
- [x] T028 [US3] `tests/test_api/test_viewsets.py`, `TestRegisteredSerializerIsUsed`: a route's
  serializer is the one the configuration returns, for a `serializer_class` named in the
  registration and for a configuration that overrides `get_serializer_class`.
- [x] T029 [US3] `tests/test_api/test_viewsets.py`, `TestSerializerMustBuildOnBase`: a
  configuration that overrides `get_serializer_class` with a serializer that does not build on the
  sample or measurement base is refused with `ImproperlyConfigured`, as a named
  `serializer_class` already is.
- [x] T030 [US3] `tests/test_api/test_checks.py`, `TestRegistrationCheck`: a registered type whose
  API fields leave out a field the model requires produces a system check error naming the type
  and the field. A complete registration produces none.
- [x] T031 [US3] `tests/test_api/test_router.py`, `TestRegistrationFailureIsReported`: a type
  whose endpoints cannot be built raises when the router is built and is not skipped.
- [x] T032 [US3] `tests/test_api/test_router.py`, `TestAddresses`: a generated route's address is
  the type's plural name under `samples/` or `measurements/`, and a sample type and a measurement
  type with the same plural name get different route names.
- [x] T033 [US3] `tests/test_api/test_router.py`, `TestRouteNamesAreSeparate`: the portal's page
  names and the API's route names for projects and datasets resolve to different views.
- [x] T034 [US3] `tests/test_api/test_router.py`, `TestCustomViewset`: a viewset registered on
  `fairdm_api_router` is served and appears in the generated schema.
- [x] T035 [US3] Implement to make T027 to T034 pass (plan D3 serializer check, D4).
- [x] T036 [US3] Documentation: the registration options that shape the API, the base
  serializers, the start-up check, addresses and renaming, and the router, in
  `docs/portal-development/restful-api.md` and the registry pages that mention serializers.

## Phase 4: US-4, a person reaches the API with a token from their account pages (P2)

- [x] T037 [US4] `tests/test_api/test_settings.py`, `TestTokens`: a request with a current
  token from the account pages' token store acts as its holder. A revoked, an expired and an
  unknown token are each answered 401.
- [x] T038 [US4] `tests/test_api/test_urls.py`, `TestTokenPages`: the pages that list,
  create and revoke tokens resolve, open for a signed-in person and send a visitor to sign in. A
  token created through the create page authenticates an API request. At the token limit the
  create page creates nothing.
- [x] T039 [US4] `tests/test_api/test_urls.py`, `TestNoAccountEndpoints`: no route under the API
  accepts a password, issues a token, or changes a password or an account.
- [x] T040 [US4] `tests/test_api/test_settings.py`, `TestSession`: a person signed in to the
  portal reads a private record of theirs through the API with their session, and a write with a
  session and no CSRF token is refused, with a client that enforces CSRF checks.
- [x] T041 [US4] `tests/test_api/test_settings.py`, `TestOtherOrigins`: a request from
  another origin is answered with permission for that origin to read the response, the
  `Authorization` header is allowed in a preflight, and no response permits credentials.
- [x] T042 [US4] Implement to make T037 to T041 pass (plan D5). Replace the token fixture in
  `tests/test_api/conftest.py`. The `make_token_client` helpers in `test_filters.py`,
  `test_permissions.py` and `test_urls.py` use it. `TestTokenLogin`, `TestTokenHeaderAccess` and
  `TestTokenLogout` in `test_urls.py` are deleted with the endpoint. The expired and revoked cases
  of T037 are seen to fail first against the installed package.
- [x] T043 [US4] Documentation: getting, using and revoking a token in the page for people using
  a portal, and the knox and CORS settings in `docs/portal-development/restful-api.md`, where the login and
  logout sections are removed. An architecture decision record under `docs/adr/` for tokens from
  the account pages.

## Phase 5: US-5, a developer finds out what the API offers (P3)

- [x] T044 [US5] `tests/test_api/test_urls.py`, `TestDocumentationRoutes`: the documentation page
  and the schema are served to a visitor, and the schema is an OpenAPI document with paths.
- [x] T045 [US5] `tests/test_api/test_urls.py`, `TestSidebarLink`: the portal's sidebar carries
  one entry that resolves to the API documentation page.
- [x] T046 [US5] `tests/test_api/test_schema.py`, `TestSchemaMatchesRoutes`: every route the
  router serves has a path in the schema, and each registered type's component lists its fields
  with the required and read-only ones marked as the serializer has them.
- [x] T047 [US5] `tests/test_api/test_schema.py`, `TestSchemaDescribesThePortal`: the schema's
  security schemes are the token header and the session, and its description carries the limits
  and page sizes the settings hold, following a changed setting.
- [x] T048 [US5] `tests/test_api/test_router.py`, `TestCatalogues`: each catalogue lists every
  registered type with its name, an address equal to its list route, a flat list of fields and
  its filters. With no registered types it is an empty list.
- [x] T049 [US5] `tests/test_api/test_router.py`, `TestCatalogueCounts`: a catalogue's count is
  of the records the caller may see, for a visitor, a signed-in person with no level and someone
  with a level on a private dataset.
- [x] T050 [US5] `tests/test_api/test_router.py`, `TestRoot`: the API's root links to every list
  route and both catalogues.
- [x] T051 [US5] Implement to make T046 to T050 pass (plan D3 catalogues, D7). Delete
  `FAIRDM_API_DOCS_URL` and `TestFairDMAPIDocsURLSetting`. The menu test counts the entries that
  lead to the documentation page across the whole menu, without relying on position.
- [x] T052 [US5] Documentation: the documentation page, the schema address and the catalogues, in
  both pages.

## Phase 6: US-6, a portal operator keeps the API within what one small server can carry (P3)

- [x] T053 [US6] `tests/test_api/test_throttling.py`, `TestLimits`: an anonymous caller past the
  per-minute rate, and past the daily rate, is answered 429 with a `Retry-After` header. A caller
  with a token is not stopped at the anonymous rate and is stopped at their own.
- [x] T054 [US6] `tests/test_api/test_throttling.py`, `TestLimitsAreSettings`: changing each of
  the four rates in the settings changes where the caller is stopped.
- [x] T055 [US6] `tests/test_api/test_pagination.py`, `TestPageSizes`: a list holds the default
  number of records, honours a larger size up to the ceiling and no further, and follows a changed
  default and a changed ceiling in the settings. A middle page carries both a next and a previous
  address. The envelope tests in `TestPagination` pass their page size explicitly.
- [x] T056 [US6] `tests/test_api/test_viewsets.py`, `TestQueryCount`: for projects, datasets and
  one sample and one measurement type with metadata recorded, a list of twelve records runs the
  same number of queries as a list of two.
- [x] T057 [US6] Implement to make T053 to T056 pass (plan D6, and the prefetching in D3). Retire
  `TestRateLimiting`, which pins the old rate names.
- [x] T058 [US6] Documentation: the limits, the page sizes and the settings that change them, for
  a portal administrator, in a table of contents. It names `REST_FRAMEWORK["NUM_PROXIES"]` as the
  setting for the number of proxies in front of the portal, and says the limits are per address
  only once it is set.

## Phase 7: closing

- [x] T059 [US6] An entry in `CHANGELOG.md` saying what a portal with API clients or its own serializers
  has to change.
- [x] T060 [US6] Remove `needs verification` from R11 in `docs/ROADMAP.md`.

## Phase 8: fixes from the code review

Each test task is written first and seen to fail.

- [x] T061 [US1] Samples and measurements of a public dataset that is not published are data the
  portal does not show, and the API showed them. `tests/test_api/test_filters.py`,
  `TestUnpublishedDataset`: for a sample and a measurement in a public, unpublished dataset, a
  visitor and a signed-in person with no level get nothing in the list, 404 on the record, a
  catalogue count that leaves them out, and 404 on a write. Someone with a level on the dataset
  still reads them. The dataset's own record stays readable. Then make the public rule for
  records that follow a dataset the portal's own: public and published, in
  `fairdm/api/filters.py` and `fairdm/api/permissions.py`.
- [x] T062 [US1] Three filters every sample list offers answered with a server error.
  `tests/test_api/test_viewsets.py`, `TestEveryListedFilter`: for every registered type, a
  request with each filter name its catalogue entry lists is answered below 500. Then point the
  sample filter set's description and date filters at the fields that exist, as the measurement
  filter set has them (`fairdm/core/sample/filters.py`).
- [x] T063 [US1] A reference could name a record its own address then refused, or a record the
  caller may not see. `tests/test_api/test_viewsets.py`, `TestReferencesFollowTheLists`: a
  contributor the contributor list leaves out is returned as null where a record credits them,
  and a relation a registered type declares to a project, dataset, sample or measurement is
  returned as a reference that is null when the caller may not see it. Then apply the contributor
  list's own rule in `RecordReferenceField`, and have the serializer factory use
  `RecordReferenceField` for relations to the four record types.
- [x] T064 [US1] `tests/test_api/test_viewsets.py`, beside the existing parent-filter tests: a
  visitor narrowing a sample list by a private dataset's identifier, and a measurement list by
  the identifier of a sample in a private dataset, is answered exactly as for an identifier that
  does not exist.
- [x] T065 [US3] An error in a developer's filter set was swallowed when its endpoint was built.
  `tests/test_api/test_router.py`: a configuration whose filter set cannot be built stops
  registration with the error. Then remove the suppression in `generate_viewset`. Correct the
  documentation and the docstring of `fairdm/api/settings.py`: the API title and description are
  changed by assigning items of `SPECTACULAR_SETTINGS`, and the examples assign items and never
  replace the dictionary. Replace the two tests in `tests/test_api/test_settings.py` that set a
  setting and read the same setting back with ones that read the generated schema.
- [x] T066 [US6] A list ran one query per record for a relation a registered type declares.
  `tests/test_api/test_viewsets.py`, `TestQueryCount`: add a sample type with a relation of its
  own on every record (the thin-section type with a location). Then have `generate_viewset`
  select or prefetch each relation among the serializer's fields that the parents do not cover.
- [x] T067 [US6] `tests/test_conf/` beside the existing deployment checks: `manage.py check
  --deploy` warns when `REST_FRAMEWORK` has no `NUM_PROXIES`, and is silent when it is set. Then
  add the warning in `fairdm/conf/checks.py`, pointing at the administrator page's section on
  proxies. No default number is chosen.

## Phase 9: changes the maintainer asked for at review

- [x] T068 [US5] The documentation page's authorisation dialog names the token scheme
  `knoxApiToken`, which means nothing to someone who does not know the package.
  `tests/test_api/test_schema.py`: the schema's security schemes are named `tokenAuth` and
  `cookieAuth`, no scheme name or description contains the package's name, and every operation's
  security refers to the new name. Then rename it where the schema is generated.
- [x] T069 [US1] `tests/test_api/test_viewsets.py`, `TestPageOnThePortal`: a project, dataset,
  sample, measurement, person and organisation each carry `html_url`, the absolute address of the
  record's own page on the portal, in list and record responses, and requesting that address as
  someone who may see the record returns the page. It is read-only and a value sent for it is
  ignored. Then add the field to the record serializers and the contributor serializer. Document
  it on both API pages and in the changelog entry.
- [x] T070 [US5] The catalogues repeat what the generated documentation already says about each
  type. `tests/test_api/test_router.py`: an entry carries `name`, `verbose_name`,
  `verbose_name_plural`, `endpoint` and `count` and nothing else. Then remove `fields`, `filters`
  and `app_label` from the entries, their response serializer and the documentation.
  `TestEveryListedFilter` takes each type's filter names from the API's filter set for that type
  in place of the catalogue.

## Phase 10: further changes the maintainer asked for at review

- [ ] T071 [US5] The two catalogues of registered types give nothing the API's root, the lists and
  the generated documentation do not. Remove both endpoints, their links from the root, their
  serializer and their tests, and every mention in the documentation. `tests/test_api/test_router.py`:
  the two addresses answer 404, and the root links to every list and to nothing that is not one.
- [ ] T072 [US1] `tests/test_api/test_viewsets.py`, `TestChangedSince`: on the lists of projects,
  datasets, contributors and every registered sample and measurement type, `modified_after` returns
  only records changed after the moment given and `modified_before` only those changed before it,
  a moment that cannot be read is refused with a 400, and both appear among the list's parameters
  in the generated documentation. Then add the two filters to every list.
- [ ] T073 [US5] `tests/test_api/test_schema.py`, `TestTypesInTheDocumentation`: each registered
  type's operations are grouped under a section named with the type's plural name. The section's
  description carries the registration's description and, where given, its authority, citation,
  keywords and repository link, and never a maintainer's name or email address. The description of
  each type's record is the type's own, and no description in the generated documentation is a
  docstring of the framework's base classes. Then build the sections from the registry when the
  documentation is generated.
