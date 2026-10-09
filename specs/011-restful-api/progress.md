
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

## 2026-10-08T23:44:48Z · Implementer US2 · T017

Did: Added TestCreatorIsCredited in tests/test_api/test_viewsets.py. For a project, a dataset, a sample and a measurement created through the real routes, the creator is listed on it at the manage level and a person named as `created_by` in the body is not credited. For a project and a dataset the stored `created_by` is the caller, not the person sent, and the response carries no `created_by`. A superuser creating a project is not credited. Samples and measurements have no `created_by` column, so that check covers the two models that do.
Verified: `uv run pytest -q -n0 tests/test_api/test_viewsets.py::TestCreatorIsCredited` gives 11 passed on the first run. Probe: replacing the credit call in `CreatorCreditMixin.create` with `pass` fails the four manage-level cases; reverted.
Next: T018.
Watch: The test helpers `create_through_the_api` and `stored_record` in the test module are used again by later tasks.

## 2026-10-08T23:45:48Z · Implementer US2 · T018

Did: Added TestChanging in tests/test_api/test_viewsets.py, run for a project, a dataset and every registered sample and measurement type, with someone at the edit level. A partial change of the name alters the name and leaves every other field of the record as a read returns it. A full replacement sets the writable fields to the values sent, with the parents the record already has. A value for a read-only field (identifier, address, added and modified dates, descriptions, key dates, identifiers, keywords, contributors) sent with a partial change and with a replacement leaves the record as it was. New fixtures in the test module: `a_private_record`, `replacement_for`, and the helper `writable_models`.
Verified: `uv run pytest -q -n0 tests/test_api/test_viewsets.py::TestChanging` gives 31 passed, 9 failed. All nine are the three measurement types, in the replacement test and in both read-only cases. Each answers 403 "Changing sample needs the manage level" when the request repeats the measurement's current sample. Cause: the sample field offers `Sample.objects.non_polymorphic()`, so the value sent is a base `Sample` while the stored sample is the type's own class, and `CreatorCreditMixin.update` compares them with `!=`, which Django answers unequal across the two classes. A parent repeated unchanged is read as a move.
Next: T019.
Watch: Red until T025, which compares parents by primary key. T023 adds the same case for the manage rule.

## 2026-10-08T23:46:09Z · Implementer US2 · T019

Did: Added TestDeleting in tests/test_api/test_viewsets.py. Someone at the manage level deletes a project, a dataset and a record of every registered sample and measurement type: the answer is 204, the record is gone from the database and a later request for it is answered 404. A project with a public dataset, and a sample with a measurement made on it, are each expected to be answered 409 with a non-empty `detail`, to leave both records stored, and not to name the other record's identifier in the answer.
Verified: `uv run pytest -q -n0 tests/test_api/test_viewsets.py::TestDeleting` gives 10 passed, 2 failed. The two refused cases fail because the error escapes the view: `PublicDatasetsProtect` for the project and `RestrictedError` for the sample reach the test client as exceptions, which the server would answer with a 500.
Next: T020.
Watch: Red until T025 adds `perform_destroy`.

## 2026-10-08T23:46:54Z · Implementer US2 · T020

Did: Added TestValidation in tests/test_api/test_viewsets.py. A create with required fields missing is answered 400 naming each of them for a rock sample (name, rock type, collection date), an XRF measurement (name, sample, element, concentration), a project and a dataset (name), and nothing is stored. A create with an unacceptable weight, an unreadable date and an over-long name is answered 400 naming exactly those three. A partial change with an unacceptable weight is 400 naming that field and the stored value is kept. A parent that does not exist, one the caller cannot see and one they can see but hold only the view level on get the same 400 on the parent field, with the sent value taken out of the messages before comparing, for the dataset of a sample, the sample of a measurement and the project of a dataset. A body that is not valid JSON is answered 400 for a project and a dataset.
Verified: `uv run pytest -q -n0 tests/test_api/test_viewsets.py::TestValidation` gives 10 passed on the first run. Probe: offering every parent instead of the ones the caller may edit fails the three parent cases; reverted.
Next: T022.
Watch: DRF's own "does not exist" message carries the value sent, which is why the comparison replaces it.

## 2026-10-08T23:47:38Z · Implementer US2 · T022

Did: Added TestWhoMayWriteSamplesAndMeasurements in tests/test_api/test_permissions.py, for a sample and a measurement on the real routes. A partial change, a replacement and a delete: no authentication is 401 on a public and a private record, a signed-in person with no level is 403 on a public one and 404 on a private one, and a viewer of the private dataset is 403. A refused change and delete leave the record as it was. A create with no authentication is 401. Someone at the view level on a dataset, and someone with no level, public dataset or private, cannot create in it: 400 on the dataset field and nothing stored.
Verified: `uv run pytest -q -n0 tests/test_api/test_permissions.py::TestWhoMayWriteSamplesAndMeasurements` gives 42 passed on the first run. Probes, both reverted: making the write check in `FairDMObjectPermissions` always allow fails 14 cases; offering every dataset as a choice fails 8.
Next: T023.
Watch: None.

## 2026-10-08T23:49:09Z · Implementer US2 · T023

Did: Added TestManageLevel in tests/test_api/test_permissions.py, on the real routes. For a private project and a private dataset: someone at the edit level cannot change visibility (403, unchanged), someone at the manage level can (200), an editor can change another field, and an editor sending the visibility the record already has is accepted. For a dataset (project), a sample (dataset) and a measurement (sample): an editor cannot move it (403, parent unchanged), a manager can, and an editor sending the parent the record already has is accepted. For a dataset and a sample, a manager who holds the manage level only on the old parent and the edit level on the new one is refused with a 400 on the parent field and the parent is unchanged.
Verified: `uv run pytest -q -n0 tests/test_api/test_permissions.py::TestManageLevel` gives 18 passed, 1 failed. The failure is a measurement re-sending its current sample: 403 "needs the manage level", the same cause recorded under T018. Probes, both reverted: emptying `manager_only_fields` fails seven cases; removing the stranding check fails the two stranding cases.
Next: T024.
Watch: Red until T025 for the measurement case.

## 2026-10-08T23:50:19Z · Implementer US2 · T024

Did: Added TestNoServerErrors in tests/test_api/test_viewsets.py. For every routed model (projects, datasets, contributors and every registered sample and measurement type), signed in as a superuser and as a person with no level on anything, it sends an empty body, a body of nested wrong types for every field, a list in place of an object and a valid body. These go to the list route as a create and to the record route as a replacement and as a partial change. A delete is sent to each record, and again to a project with a public dataset and to each sample with a measurement on it. Every answer must be below 500.
Verified: `uv run pytest -q -n0 tests/test_api/test_viewsets.py::TestNoServerErrors` gives 302 passed, 6 failed. The six are the deletes the portal refuses (a project with a public dataset, five sample types with a measurement): the protection error escapes the view. Every create and change answered below 500, valid bodies included, so no demonstration type's API fields leave out a required model field and demo/config.py needs no change.
Next: T025.
Watch: Red until T025 adds `perform_destroy`.

## 2026-10-08T23:53:53Z · Implementer US2 · T025

Did: Made T016 to T024 pass.
- fairdm/api/serializers.py: `CreatorCreditMixin.differs` compares a parent by primary key. A measurement's sample field offers the base `Sample` while the record holds the sample as its own type, which Django does not call equal, so a request that repeated the current sample was read as a move and refused. Deleted `build_model_serializer`, its cache and `_flatten_fields`, and the import of the guardian mixin. `BaseSerializerMixin` stays: the location app's GeoJSON serializer uses it, and its docstring no longer says it is applied by `generate_viewset`.
- fairdm/api/viewsets.py: `perform_destroy` answers 409 through a new `DeleteRefused` exception with a reason written here for each case: a project with public datasets (`PublicDatasetsProtect`), and a record that others depend on (`ProtectedError`, `RestrictedError`). The sentences name no other record.
- pyproject.toml and uv.lock: `djangorestframework-guardian` is dropped, as nothing under fairdm/ imports it any more. It is in no dependency-check map.
Tests removed from tests/test_api/test_serializers.py: the whole of `TestBuildModelSerializer` (test_generated_class_name, test_fields_included, test_url_field_included_when_view_name_provided, test_url_field_absent_when_no_view_name, test_is_model_serializer_subclass, test_a_core_record_serializer_credits_its_creator, test_a_serializer_for_another_model_still_assigns_stored_permissions, test_get_permissions_map_returns_correct_perms, test_caching_returns_same_class_object, test_different_fields_produce_different_classes, test_flattens_grouped_tuples) and the fixtures `project_model` and `simple_serializer`, which only it used.
Tests removed from tests/test_api/test_viewsets.py, replaced by T017, T022 and T023: `TestCreatedRecordsListTheirCreator` (test_a_project_or_dataset_lists_its_creator_at_the_manage_level, test_a_superuser_creates_without_being_credited), the fixture `private_record` and the helper `detail_url`, and `TestVisibilityNeedsManage` (test_an_editor_cannot_change_visibility, test_a_manager_can_change_visibility, test_an_editor_can_change_another_field, test_an_editor_can_send_the_visibility_it_already_has). `TestMovingARecordThroughTheApi`, `TestCreatingARecordThroughTheApi` and `TestParentChoicesThroughTheApi` had been removed already. The helpers `person_at` and `signed_in_as` stay, since `TestCompleteRecord` and `TestFiltering` use them.
Verified: `uv run pytest -q -n0 tests/test_registry tests/test_api` gives 1028 passed. `uv run pytest -q -n0 tests/test_contrib/test_location/test_api.py` passes. `uv run mypy fairdm/api` and `ruff` are clean.
Next: T026.
Watch: None.

## 2026-10-08T23:55:16Z · Implementer US2 · T026

Did: Documented creating, changing and deleting in both pages. docs/portal-development/restful-api.md has a new section on what can be written for each kind, creating, replacing and changing part of a record, deleting and the two refused deletes (409 with a reason), and a table of refused requests. The endpoint list and the core-model table show PUT. The permission section is rewritten around the three levels (view, edit, manage) and the answers for each caller, and names `owner` among the fields that need the manage level. The note about stored guardian permissions for other models is removed, as that behaviour went with the old serializer builder. docs/user-guide/reading-records-with-a-script.md is retitled "Reading and writing records with a script" and gains sections on creating (curl and Python), changing, what cannot be written, deleting, and the meaning of each refusal.
Verified: Ran each documented request against the branch through the test client: creating a rock sample answers 201, a partial change of `weight_grams` answers 200 and keeps the other fields, a replacement that leaves out an optional field keeps its value, a replacement that leaves out required fields answers 400 naming them, a project created with `visibility` 1 comes back public, a dataset created without it comes back private, and the delete answers 204. The docs step runs in the full verify.
Next: full verify and the completion report.
Watch: The pages do not say how to get a token. The authentication section is for a later story.

## 2026-10-09T00:07:33Z · Implementer US3 · T027

Did: Added TestSerializerFactory (sample and measurement variants) in tests/test_registry/test_factories.py. A type with no field list now gets the framework defaults without `options` and `tags` for its serializer only (Component.default_exclude in fairdm/registry/config.py); forms, tables and filters keep the full defaults, and a field named in serializer_fields or fields is always carried.
Verified: uv run pytest -q -n0 tests/test_registry/test_factories.py tests/test_registry/test_config.py: 181 passed. The options/tags test failed first for the right reason; the others passed on first run and were probed (serializer built on the plain base, and the shared list taking precedence over serializer_fields each turned tests red).
Next: T028.
Watch: none.

## 2026-10-09T00:09:25Z · Implementer US3 · T028

Did: Added TestRegisteredSerializerIsUsed in tests/test_api/test_viewsets.py. A route built from a configuration that names a serializer_class, and one built from a configuration overriding get_serializer_class, each answer with the fields of the serializer the configuration returns, for a sample and a measurement type. A new fixture in tests/test_api/conftest.py registers a viewset on the API router for one test, reloads the URL modules so the route is served, and undoes both at the end.
Verified: uv run pytest -q -n0 tests/test_api/test_viewsets.py::TestRegisteredSerializerIsUsed: 3 passed on first run, as the viewset already used the configuration's accessor. Probe: making generate_viewset build from the registry's own serializer instead of the accessor turned the accessor test red.
Next: T029.
Watch: none.

## 2026-10-09T00:09:25Z · Implementer US3 · T029

Did: Added TestSerializerMustBuildOnBase in tests/test_api/test_viewsets.py: generate_viewset refuses with ImproperlyConfigured a serializer off the base for a sample and for a measurement type, whether named in the registration or returned by an overridden get_serializer_class.
Verified: uv run pytest -q -n0 tests/test_api/test_viewsets.py::TestSerializerMustBuildOnBase: 4 passed on first run, as the check already applies to whatever the accessor returns. Probe: removing the two validate calls from generate_viewset turned all four red.
Next: T030.
Watch: none.

## 2026-10-09T00:10:53Z · Implementer US3 · T030

Did: Added TestRegistrationCheck in tests/test_api/test_checks.py. It calls the new start-up check on the shipped registrations (no errors), on a sample and a measurement type whose API fields leave out a required model field, on a type with several missing fields, on a developer's own serializer that omits a required field, and on one that only reads it; it asserts on the error id and that it names the type and the field.
Verified: uv run pytest -q -n0 tests/test_api/test_checks.py: 7 tests fail with ModuleNotFoundError for fairdm.api.checks, as expected before the check exists.
Next: T031.
Watch: the check is written and registered in T035.

## 2026-10-09T00:12:13Z · Implementer US3 · T034

Did: Added TestCustomViewset in tests/test_api/test_router.py: a viewset registered on fairdm_api_router is served at its address, is served beside the generated routes, and appears in the generated schema at /api/v1/schema/. The fixture from the earlier commit registers it for one test, reloads the URL modules and undoes both afterwards.
Verified: uv run pytest -q -n0 tests/test_api/test_router.py::TestCustomViewset: 3 passed on first run, as the router was already exposed. Probes: leaving out the URL reload turned the served and schema tests red; a following test confirmed the route and schema entry are gone after the fixture ends.
Next: T031.
Watch: the router's addresses are fixed when fairdm.api.urls is first imported, so a viewset registered after the URL configuration has loaded is served only once that module is loaded again. The module docstring says it can be registered "after Django startup"; T036 corrects that in the documentation and the docstring.

## 2026-10-09T00:12:26Z · Implementer US3 · T031

Did: Added TestRegistrationFailureIsReported in tests/test_api/test_router.py. It builds the registration of the registered types on a new router, with a sample type and then a measurement type configured so its endpoints cannot be built (a serializer off the base, and a serializer that raises), and expects the error to propagate.
Verified: uv run pytest -q -n0 tests/test_api/test_router.py::TestRegistrationFailureIsReported: 3 fail with AttributeError, because the registration is still two module-level loops that log a warning, so there is nothing to call. T035 turns the loops into FairDMAPIRouter.register_types and removes the swallowing.
Next: T032.
Watch: none.

## 2026-10-09T00:12:33Z · Implementer US3 · T032

Did: Added TestAddresses in tests/test_api/test_router.py: a sample type's address is its plural name under samples/ and a measurement type's is under measurements/; the generated routes are served at those addresses; a sample type and a measurement type given the same plural name get different route names; renaming a type's plural name moves its address.
Verified: uv run pytest -q -n0 tests/test_api/test_router.py::TestAddresses: the five tests that build a router fail with AttributeError (register_types does not exist yet); the one that reads the served routes passes, as the addresses already follow the plural name.
Next: T035.
Watch: none.

## 2026-10-09T00:14:24Z · Implementer US3 · T028

Did: Added TestRelationFiltersUseIdentifiers beside T028's class in tests/test_api/test_viewsets.py, for the filters a type declares on its own relations. A route built from a type whose filter set filters on a project (single and multiple choice) and on a content type is expected to match the project by short identifier, refuse a database number, and leave out the content-type filter, which has no identifier.
Verified: uv run pytest -q -n0 tests/test_api/test_viewsets.py::TestRelationFiltersUseIdentifiers: 4 fail for the right reason, the filters still match on database numbers (an identifier answers 400, a number answers 200, and the content-type number narrows the list).
Next: T035.
Watch: none.

## 2026-10-09T00:19:49Z · Implementer US3 · T035

Did: fairdm/api/checks.py with check_registered_types (fairdm.E600), registered under the models tag from the API app's ready(). FairDMAPIRouter.register_types replaces the two module-level loops and their try/except blocks. The API's copy of a type's filter set matches every relation filter on uuid and drops the filters on relations that have none (fairdm/api/filters.py). The module docstring of the router now says where a developer registers a viewset. Decisions in decisions.md D20. Added a test that Django's check command reports E600 to TestRegistrationCheck.
Verified: uv run pytest -q -n0 tests/test_api: 810 passed. Probes: letting the check count read-only fields turned the read-only test red, removing its registration turned the registration test red, and restoring a try/except in register_types turned all three failure tests red. manage.py check: no issues.
Next: T036.
Watch: the generated schema still lists the content-type filter of the sample mixin, which a request ignores.

## 2026-10-09T00:21:39Z · Implementer US3 · T036

Did: Documented what a registration decides for the API. docs/portal-development/restful-api.md: the order of the field lists and the defaults without options and tags, the base serializers and the refusal that applies to a named class and to an overridden get_serializer_class, the start-up check, route names and addresses, renaming a type, relation filters by short identifier, and where to register on the router and why. docs/portal-administration/configuration-checks.md gets fairdm.E600. docs/portal-development/model_configuration.md and using_the_registry.md no longer describe a plain serializer as accepted or the API as planned.
Verified: the E600 text, the refusal text, the route names and registering on the router before the URL configuration loads were each run against this branch and the pages match.
Next: full verify and the completion report.
Watch: CHANGELOG.md has no entry for this feature yet.

## 2026-10-09T00:33:02Z · Implementer US4 · T037

Did: Added TestTokens in tests/test_api/test_settings.py: a current token acts as its holder and shows a private project the holder may view, a visitor does not see it, a revoked, an expired and an unknown token are each answered 401, and the portal's token limit setting is live. The revoked and expired cases first send the token and expect 200, then delete it or move its expiry into the past, so they fail first instead of passing because the old authenticator rejects every token. Added a token fixture and a shared make_token_client helper to tests/test_api/conftest.py beside the old ones. Added the knox app to INSTALLED_APPS and the api extra of django-mvp-accounts to pyproject.toml, since the tests need knox's token table.
Verified: uv run pytest -q -n0 tests/test_api/test_settings.py::TestTokens: 4 fail for the right reason (the current token and the revoked and expired set-up requests get 401 from the old authenticator, the limit is unset), 3 pass because the old authenticator also answers 401 to a token it does not know.
Next: T038.
Watch: the old token mechanism stays installed until T042.

## 2026-10-09T00:33:26Z · Implementer US4 · T038

Did: Added TestTokenPages in tests/test_api/test_urls.py. The list, create and revoke pages open for a signed-in person and send a visitor to sign in. A token made through the create page is read from the next page's context and authenticates a request to the project list. A token revoked through the revoke page is answered 401 afterwards. With the limit set to two through the REST_KNOX setting, a post to the create page leaves the person's token count at two.
Verified: uv run pytest -q -n0 tests/test_api/test_urls.py::TestTokenPages: 3 fail and 2 error with NoReverseMatch, as the pages' routes are not included yet.
Next: T039.
Watch: none.

## 2026-10-09T00:33:41Z · Implementer US4 · T039

Did: Added TestNoAccountEndpoints in tests/test_api/test_urls.py. It walks the resolver under the api namespace, collecting each route's name and full path, and asserts none contains login, logout, password, registration or auth/user. A separate case posts an email and password to the old login address and expects 404.
Verified: uv run pytest -q -n0 tests/test_api/test_urls.py::TestNoAccountEndpoints: the two behaviour cases fail (the old endpoints are routed and the login answers 200); the guard that the walk finds routes passes.
Next: T040.
Watch: none.

## 2026-10-09T00:34:02Z · Implementer US4 · T040

Did: Added TestSession in tests/test_api/test_settings.py. A person with the edit level on a private project, signed in by session, reads the project through the API with a client that enforces CSRF checks. The same person's patch succeeds with a client that does not enforce them, and is refused with 403 and leaves the name unchanged with one that does.
Verified: uv run pytest -q -n0 tests/test_api/test_settings.py::TestSession: both pass on first run, as the API already accepted the session. Probe: removing SessionAuthentication from fairdm/api/settings.py made both fail; the file was restored.
Next: T041.
Watch: none.

## 2026-10-09T00:34:16Z · Implementer US4 · T041

Did: Added TestOtherOrigins in tests/test_api/test_settings.py. A read of the project list with an Origin header carries Access-Control-Allow-Origin. A preflight asking for the authorization header is allowed it. Neither a read nor a preflight carries Access-Control-Allow-Credentials. The home page, which is outside the API, gets no CORS header.
Verified: uv run pytest -q -n0 tests/test_api/test_settings.py::TestOtherOrigins: the read and the preflight fail with the header missing; the credentials and non-API cases pass already and guard against a later change.
Next: T042.
Watch: none.
