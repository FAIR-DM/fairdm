
## 2026-10-08T22:54:13Z · orchestrator · plan and reconciliation

Research, plan and task list written. The task list was written as if no API existed and then
checked against the code: 60 tasks, 7 proven done by cited code and a passing test (T007, T008,
T010, T021, T033, T044, T045), 53 open. Of the open ones, most are open because the behaviour was
never built or fails; the write-path rules from FS-022 are built but tested only through a
hand-made viewset that sends database numbers, so their tasks stay open until tests use the real
routes.

## 2026-10-08T23:12:58Z · Implementer US1 · T001

Did: Added TestRecordReferenceField in tests/test_api/test_serializers.py. It covers a reference returned as its short identifier and address, a bare identifier and the returned object both accepted, an unknown identifier and a database number (as an integer and as text) refused, and a record the caller may not see returned as null.
Verified: `uv run pytest -q -n0 tests/test_api/test_serializers.py::TestRecordReferenceField` fails on collection of the field, which does not exist yet (8 errors, ImportError).
Next: T002.
Watch: These tests stay red until the serializers land in T014.

## 2026-10-08T23:12:58Z · Implementer US1 · T002

Did: Added TestCompleteRecord in tests/test_api/test_viewsets.py, and the fixtures it uses to tests/test_api/conftest.py (route name lookup, record builders, one of each kind of metadata). It checks a project, dataset, sample and measurement with metadata recorded: own fields, descriptions, dates, identifiers, keywords, credited contributors with roles and affiliation, a dataset's licence, a project's owner, parent addresses that return the parent, and the hidden-parent cases (public dataset in a private project, measurement whose sample is in a private dataset, and a list of such datasets).
Verified: `uv run pytest -q -n0 tests/test_api/test_viewsets.py::TestCompleteRecord` gives 16 failed, each from a missing key (descriptions, contributors, project, owner, dataset) or an integer where a reference is expected.
Next: T003.
Watch: Red until T014.

## 2026-10-08T23:13:30Z · Implementer US1 · T003

Did: Added TestCommonFields in tests/test_api/test_viewsets.py. For every registered demonstration sample type (five) and measurement type (three) it checks the record carries the fields common to its kind and every field the registration declares for the serializer, with the parent named by identifier. A separate case checks an XRF measurement's measured values come back as recorded.
Verified: `uv run pytest -q -n0 tests/test_api/test_viewsets.py::TestCommonFields` gives 9 failed, each a missing declared field (element, rock_type and the like) or a missing common field.
Next: T004.
Watch: Red until T014.

## 2026-10-08T23:14:08Z · Implementer US1 · T004

Did: Added TestNoDatabaseNumbers in tests/test_api/test_viewsets.py. It builds a public project, dataset, one record of every registered sample and measurement type with metadata, and a person and organisation, requests the list and record routes of each, and walks every response to any depth for an `id` or `pk` key and for an integer under any relation key.
Verified: `uv run pytest -q -n0 tests/test_api/test_viewsets.py::TestNoDatabaseNumbers` fails. The first stop is that a contributor's record route answers 404 to a visitor today, because the object-level permission class has no rule for a model that is neither public nor private. That is a defect T006 also covers, and the fix goes in with the viewsets.
Next: T005.
Watch: The failure hides the number walk behind the contributor 404 until the permission fix lands in T014.

## 2026-10-08T23:14:30Z · Implementer US1 · T005

Did: Added TestContributor in tests/test_api/test_viewsets.py. A person with a biography, links, a language, an ORCID iD and a primary affiliation, and an organisation with a parent and a ROR ID, are each requested. The tests check the public profile fields come back, no response (list or record) carries an account key (email, password, staff, superuser, active, last login, joined date, groups, permissions, claim flag) or the person's address as text, and a superuser and the anonymous account are left out of the list and answered 404.
Verified: `uv run pytest -q -n0 tests/test_api/test_viewsets.py::TestContributor` gives 4 failed, 1 passed. The failures are the contributor record route answering 404 to a visitor. The passing case (superuser answered 404) passes only because every contributor record is 404 today; it is a guard for once that is fixed.
Next: T006.
Watch: Red until T014.

## 2026-10-08T23:14:57Z · Implementer US1 · T006

Did: Added TestListAndRecordRoutes in tests/test_api/test_viewsets.py. For projects, datasets, contributors and every registered sample and measurement type it checks a list is served to a visitor with the record in it, a record is found by its short identifier, an unknown identifier is answered 404, and that unregistered types (under both prefixes) and a sample type under the measurement prefix are answered 404.
Verified: `uv run pytest -q -n0 tests/test_api/test_viewsets.py::TestListAndRecordRoutes` gives 11 failed, 27 passed. The failures are the five sample lists and records (no `uuid` in the response today) and the contributor record (404). The 404 cases for unknown identifiers and unregistered types already hold.
Next: T009.
Watch: Red until T014.

## 2026-10-08T23:15:16Z · Implementer US1 · T009

Did: Added TestVisibilityOfSamplesAndMeasurements in tests/test_api/test_filters.py. With a public and a private dataset each holding a record of the kind, it requests the real list route of a sample type and a measurement type as a person with the view level on the private dataset, a signed-in person with no level, and a visitor. It checks which records are listed and that the total counts only what the caller may see.
Verified: `uv run pytest -q -n0 tests/test_api/test_filters.py::TestVisibilityOfSamplesAndMeasurements` gives 3 failed, 3 passed. The sample cases fail only on the missing `uuid` in a sample row today. The measurement cases already pass, so the filter behaviour exists; it is probed at the end.
Next: T011.
Watch: Red for samples until T014.

## 2026-10-08T23:16:05Z · Implementer US1 · T011

Did: Added TestReadingASampleOrMeasurement in tests/test_api/test_permissions.py. For a private dataset, a sample in it and a measurement in it, it requests the real record route as a visitor, a signed-in person with no level, and a person at the view level on the dataset.
Verified: `uv run pytest -q -n0 tests/test_api/test_permissions.py::TestReadingASampleOrMeasurement` gives 9 passed, so the behaviour already holds. Probed by removing the mechanism: with only the object-permission check removed, or only the list filter removed, all 9 still pass because each stops the request on its own. With both removed the six 404 cases fail, so the tests detect the behaviour. The mutations were reverted (git shows no change under fairdm/).
Next: T012.
Watch: This task adds coverage and no code.

## 2026-10-08T23:16:37Z · Implementer US1 · T012

Did: Added TestFiltering in tests/test_api/test_viewsets.py. It checks that a filter a type declares narrows its list (soil type, XRF element, and the water source filter built by overriding the accessor), that every sample and measurement type's list is narrowed by `?dataset=<short identifier>` whether or not the type declares a dataset filter, that every measurement list is narrowed by `?sample=<short identifier>`, that someone with the view level can narrow by a private dataset, and that a database number in either parameter is answered 400 and names the parameter.
Verified: `uv run pytest -q -n0 tests/test_api/test_viewsets.py::TestFiltering` fails: measurement and WaterSample/Soil/Rock lists answer 400 to an identifier (the registered filter matches on database numbers), sample types that declare no dataset filter ignore the parameter and answer 200 to a database number, and sample rows have no `uuid` yet.
Next: T013.
Watch: Red until T014.

## 2026-10-08T23:17:31Z · Implementer US1 · T013

Did: Added TestOrdering in tests/test_api/test_viewsets.py. For projects, datasets and every registered sample and measurement type it creates three records named out of order and requests the list ordered by name and by `-name`, and by `added` and `-added`.
Verified: `uv run pytest -q -n0 tests/test_api/test_viewsets.py::TestOrdering` gives 24 failed, 6 passed. Projects and datasets already sort. All 24 sample and measurement cases (8 types x 3 tests) raise `AttributeError: 'NoneType' object has no attribute 'attname'`.
Cause found: the error does not come from a polymorphic queryset. With no `ordering_fields` on the view, DRF's ordering filter inspects every property on the model class, and reading django-polymorphic's `polymorphic_primary_key_name` on a sample or measurement subclass raises because the abstract polymorphic base has no primary key. Giving the generated viewset an explicit `ordering_fields` avoids the lookup.
Next: T014.
Watch: Recorded as a concern for the report, since it is a defect in a dependency's class property rather than a queryset problem.

## 2026-10-08T23:29:12Z · Implementer US1 · T014

Did: Built the serializers and viewsets that make T001 to T013 pass.
- fairdm/api/serializers.py: `RecordReferenceField` (identifier and address, null for a record the caller may not see, checked once per page through `RecordListSerializer`), `RecordURLField`, the five read-only metadata serializers, `RecordSerializer`, `ProjectSerializer`, `DatasetSerializer`, `BaseSampleSerializer` and `BaseMeasurementSerializer` (with `common_fields`, no `polymorphic_ctype`) and `ContributorSerializer`. `build_model_serializer` is still there, unused by the viewsets.
- fairdm/registry/factories.py: `SerializerFactory` builds on the sample or measurement base, adds every declared field after the common ones, and shows other relations as strings.
- fairdm/core/measurement/config.py: removed the fixed `serializer_fields` list.
- fairdm/api/viewsets.py: `generate_viewset` takes `config.get_serializer_class()` and checks it against the base. Each generated endpoint serves its one concrete type with parents selected and metadata prefetched, names its sortable fields, and filters through `FairDMFilterBackend`. `ContributorViewSet` lists what the portal lists show and is readable by anyone.
- fairdm/api/filters.py: `DatasetFilterSet` and `SampleFilterSet` match `dataset` and `sample` by `uuid` over the records the caller may see, and drop the content-type filter.
Cause of the sorting failure: not a polymorphic queryset. See the T013 entry and decisions.md D17.
Tests changed in this task, all of them pinning the old generated shape: tests/test_api/test_serializers.py `TestBaseSampleSerializer::test_meta_fields_include_all_required`, `TestBaseSampleSerializer::test_meta_fields_exact`, `TestBaseMeasurementSerializer::test_meta_fields_include_all_required`, `TestBaseMeasurementSerializer::test_meta_fields_exact` (`polymorphic_ctype` is a database number and is gone; the five metadata fields are in). Also, in tests I wrote in this story, the reference-field test no longer passes a route name and checks the error code through `errors`, and TestFiltering gained a case for the content-type filter.
Verified: `uv run pytest -q -n0 tests/test_api tests/test_registry` gives 599 passed, 3 failed, 14 errors. All 17 are existing write tests that this story cannot leave untouched (see Watch). `uv run mypy fairdm/api fairdm/registry/factories.py fairdm/core/measurement/config.py` is clean and so is `ruff`.
Next: T015 and the full verify.
Watch: BLOCKED on 17 existing tests in tests/test_api/test_viewsets.py. `TestCreatedRecordsListTheirCreator::test_a_sample_lists_its_creator_at_the_manage_level` and `::test_a_measurement_lists_its_creator_at_the_manage_level` (2) send the dataset and sample as database numbers to a serializer built on the new base, which refuses them. `TestParentChoicesThroughTheApi::test_a_measurement_cannot_name_a_sample_the_person_cannot_edit` (1) and the fixtures behind `TestMovingARecordThroughTheApi` (6) and `TestCreatingARecordThroughTheApi` (8) hand `generate_viewset` a SimpleNamespace in place of a configuration, which has no `get_serializer_class`, and send database numbers too. Either way the test sends what the specification says is refused, or hands the builder something the registry never would. Making them pass would mean accepting database numbers or special-casing a test double. They are replaced on the real routes by T016 to T023 and deleted in T025.

## 2026-10-08T23:29:12Z · Implementer US1 · T015

Did: Documentation for reading. docs/portal-development/restful-api.md now has sections on what a record contains, how records refer to each other, contributors, and filtering, ordering and paging, and its serializer-field section describes the common fields, measurement values and the base serializers as they are now. New page docs/user-guide/reading-records-with-a-script.md (curl and Python), added to the user guide's table of contents. New decision record docs/adr/0027-records-refer-to-each-other-by-short-identifier.md, listed in docs/adr/index.md. docs/portal-development/using_the_registry.md: the serializer example now passes the request, which the serializer needs for addresses. decisions.md D3 points at the record and D17 records the choices made while building.
Verified: the Python and curl addresses in the new page match the routes the tests call; the snippets in restful-api.md were checked against the serializers by reading them. The docs step of the full verify is run once at the end with --base origin/main.
Next: full verify and the completion report.
Watch: The authentication, writing, limits and sidebar sections of restful-api.md are for later stories and were not touched.

## 2026-10-08T23:44:08Z · Implementer US2 · T016

Did: Added TestCreating in tests/test_api/test_viewsets.py and four fixtures in tests/test_api/conftest.py (`member_at`, `signed_in`, `body_for`, `saved`). Someone at the edit level creates a sample of each of the five registered sample types in a dataset and a measurement of each of the three measurement types on a sample with its values. Someone at the edit level on a project creates a dataset in it, and any signed-in person creates a project. Each test checks the status is 201, that the record is stored under the parent sent with the values sent, and that the response equals what a read of the new record returns.
Verified: `uv run pytest -q -n0 tests/test_api/test_viewsets.py::TestCreating` gives 10 passed. They passed on the first run, which the first story's serializers explain: the sample and measurement base serializers now carry the dataset and sample, and the dataset serializer carries the project. To check the tests can fail, I made the dataset serializer's project read-only and the dataset test failed (project came back None); the change was reverted.
Next: T017.
Watch: A vocabulary concept (a sample's status) has no primary key and compares by identity, so the stored-value comparison reads it by name.
