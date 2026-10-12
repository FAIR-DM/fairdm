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
