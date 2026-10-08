
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
