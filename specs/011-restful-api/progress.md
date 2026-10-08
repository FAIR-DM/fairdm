
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
