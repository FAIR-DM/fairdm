# Tasks — 003 The project record

Written as if the repository contained no project code at all, so that the list describes building
this feature to the current standard rather than describing what happens to exist. The reconciliation
that follows marks each task done only where the code satisfies it **and** a test proves it.

Test-first throughout, per Article I. Test modules mirror the source tree; test classes are
`Test<Subject>`; factories live in `fairdm/factories/`.

## US-1 — Descriptions, keywords and tags (#158)

- [ ] T001 A factory for project descriptions, producing a valid type and body.
- [x] T002 Test: a description attached to a project is stored under its type and is retrievable by
      type.
      **Done:** fairdm/core/project/models.py:127 — covered by TestProjectModelIntegration::test_project_descriptions_relationship, TestProjectDescriptions::test_add_multiple_descriptions_to_project
- [x] T003 A typed description record for projects, bound to the project description vocabulary.
      **Done:** fairdm/core/project/models.py:127, fairdm/core/abstract.py:278 — covered by TestProjectDescriptions::test_add_multiple_descriptions_to_project
- [ ] T004 Test: attaching a second description of a type the project already carries fails
      validation, and the message names the type.
- [ ] T005 Validation refusing a duplicate description type.
- [ ] T006 Test: the duplicate is refused at the database as well, so a concurrent write cannot slip
      past validation.
- [ ] T007 A database constraint making description type unique per project.
- [ ] T008 Test: a term from a configured controlled vocabulary added as a keyword is stored as a
      reference to that vocabulary rather than as text.
- [ ] T009 Test: free tags are stored and remain distinguishable from controlled keywords.
- [ ] T010 Keyword and tag fields on the project.

## US-2 — Project dates and the timeline check (#159)

- [ ] T011 A factory for project dates, defaulting to a type the project date vocabulary contains.
- [x] T012 A typed date record for projects, bound to a project date vocabulary containing a start
      and an end.
      **Done:** fairdm/core/project/models.py:157, fairdm/core/vocabularies.py:388 — covered by TestProjectDates::test_add_date_range_to_project, TestProjectModelIntegration::test_project_dates_relationship
- [x] T013 Test: a start date attached to a project is stored under the start type.
      **Done:** fairdm/core/project/models.py:157 — covered by TestProjectDates::test_add_date_range_to_project
- [ ] T014 Test: a second start date on the same project is refused.
- [ ] T015 A database constraint making date type unique per project.
- [ ] T016 Test: an end date earlier than the project's start is refused, with a message naming both
      dates.
- [ ] T017 Test: changing the start to a date after the existing end is refused for the same reason.
- [ ] T018 Test: an end date on a project with no start date is accepted.
- [ ] T019 Test: a year-only end date in the same year as a month-precision start is accepted —
      comparison happens at the coarser precision.
- [ ] T020 Cross-record validation of the project timeline, comparing at the coarser of the two
      precisions.

## US-3 — Project identifiers (#160)

- [ ] T021 A project collection in the identifier vocabulary, containing a DOI, a grant number and a
      proposal identifier.
- [ ] T022 A registry key for the identifier vocabulary that does not collide with another
      vocabulary's.
- [ ] T023 The project identifier record bound to the project collection rather than to the whole
      vocabulary.
- [ ] T024 A factory for project identifiers.
- [ ] T025 Test: a DOI attached to a project is stored under the DOI type.
- [ ] T026 Test: a grant number is stored alongside the DOI.
- [ ] T027 Test: attaching the same identifier value to a second project is refused.
- [ ] T028 Test: the identifier types offered for a project contain a DOI and a grant number, and
      contain no identifier that names a person or an organisation.

## US-4 — Funding in DataCite's shape (#161)

- [ ] T029 A validator for funding, accepting a list of DataCite funding references.
- [ ] T030 The funding field carrying that validator.
- [ ] T031 Test: an award with funder name, funder identifier, scheme, award number and award title
      round-trips with each part readable individually.
- [ ] T032 Test: a project carrying two awards retains both.
- [ ] T033 Test: an award naming only a funder is accepted.
- [ ] T034 Test: an award naming a funder identifier scheme outside DataCite's set is refused, and
      the message names the accepted schemes.
- [ ] T035 Test: funding that is not a list is refused.
- [ ] T036 The project factory emits funding in the specified shape.
- [ ] T037 A reversible migration converting stored funding from the older flat shape to the list of
      funding references.
- [ ] T038 The pre-existing factory tests asserting the flat shape are rewritten against the
      specified one.

## US-5 — Metadata export (#162)

- [ ] T039 A module mapping a project to DataCite's JSON form, carrying its descriptions, dates,
      identifiers, contributions and funding.
- [ ] T040 Test: exporting a project that carries every kind of related record produces output
      containing every one of them.
- [ ] T041 Test: where a project carries a DOI, the export presents it as the record's primary
      identifier.
- [ ] T042 Test: exporting a minimally populated project omits the absent parts rather than emitting
      empty structures.
- [ ] T043 A module mapping a project to JSON-LD with an explicit context.
- [ ] T044 Test: the JSON-LD output parses as JSON-LD and carries a context.
- [ ] T045 Administrative actions serialising both forms over a selection.
- [ ] T046 Test: exporting several projects together produces output carrying all of them.

## US-6 — The administrative interface (#163)

- [ ] T047 Administrative search over project name, identifier and owning organisation.
- [ ] T048 Test: a search term matching each of those three finds the project.
- [x] T049 A status filter on the administrative list.
      **Done:** fairdm/core/project/admin.py:57 — covered by TestAdminFilterByStatus::test_filter_by_concept_status
- [x] T050 Test: the status filter leaves only projects with that status.
      **Done:** fairdm/core/project/admin.py:57 — covered by TestAdminFilterByStatus::test_filter_by_concept_status, TestAdminFilterByStatus::test_filter_by_visibility
- [ ] T051 Inline editing of a project's descriptions, dates and identifiers from its own page.
- [ ] T052 Test: a description, a date and an identifier added inline all persist.
- [ ] T053 List columns showing whether a project carries an abstract and whether it carries a start
      date.
- [ ] T054 Test: those columns reflect the presence and absence of each.
- [ ] T055 Bulk actions setting a project's status.
- [ ] T056 Test: every bulk status action leaves the selected projects in the status its label names.

## US-7 — The creation record (#164)

- [ ] T057 A nullable reference from a project to the user who created it, surviving that user's
      removal.
- [ ] T058 A migration adding that reference.
- [ ] T059 The creator written wherever a project is created.
- [ ] T060 Test: a project created by a known user names that user as its creator.
- [ ] T061 Test: a project whose creator's account has been removed survives with its creator reading
      as unknown.
- [ ] T062 Test: changing a project advances its modification timestamp and leaves its creator
      unchanged.

## US-8 — The project record itself (#166)

- [x] T063 A unique, short, human-readable project identifier, prefixed and generated on creation,
      not editable afterwards.
      **Done:** fairdm/core/project/models.py:73 — covered by TestProjectModel::test_project_creation_with_required_fields, TestProjectModel::test_project_uuid_is_unique
- [x] T064 Test: a newly created project carries a prefixed identifier, and the field cannot be
      edited.
      **Done:** fairdm/core/project/models.py:73 — covered by TestProjectModel::test_project_uuid_is_unique
- [ ] T065 A required name, and an optional image, owning organisation and funding.
- [ ] T066 Test: a project with no owning organisation is valid.
- [ ] T067 A lifecycle status drawn from a controlled set, every member labelled with the state it
      names.
- [ ] T068 Test: every status label matches the state its member names.
- [x] T069 A visibility of either private or public.
      **Done:** fairdm/utils/choices.py:14, fairdm/core/project/models.py:80 — covered by TestProjectModel::test_project_visibility_choices
- [x] T070 Test: visibility offers exactly private and public, and defaults to private.
      **Done:** fairdm/core/project/models.py:80 — covered by TestProjectModel::test_project_visibility_choices, TestProjectModelIntegration::test_project_visibility_default
- [ ] T071 Projects ordered most-recently-modified first by default.
- [ ] T072 Test: the default ordering is most-recently-modified first.
- [x] T073 Contributions associating a person or an organisation with a project under roles from a
      controlled set.
      **Done:** fairdm/core/abstract.py:80, fairdm/core/project/models.py:95 — covered by TestProjectModelIntegration::test_add_contributor
- [x] T074 Test: a contribution records its contributor and its roles, and the roles read back.
      **Done:** fairdm/core/abstract.py:80 — covered by TestProjectModelIntegration::test_add_contributor
- [ ] T075 Test: every role in the project role vocabulary is expressible as a DataCite contributor
      type.
- [ ] T076 Every string the model, its vocabularies, its validation messages and its administrative
      interface present to a user marked for translation in a way that resolves at request time.
- [ ] T077 Test: none of those surfaces binds a translated string at import time.
- [ ] T078 A queryset loading a project together with its descriptions, dates, identifiers,
      contributions and keywords in a bounded number of queries.
- [ ] T079 Test: the query count for loading a project with all its related metadata does not grow
      with the number of related records.

## Reconciliation

Seventy-nine tasks. **Twelve are proven done**, each with a code citation and a passing test.
Sixty-seven are open.

A task counts as done only where both halves exist. Code with no test leaves the task open and the
remaining work is the test — which turns this reconciliation into a complete test-gap audit of the
feature as a side effect. The old task list's checkboxes were not consulted.

Why each open task is open:

| Reason | Count | Examples |
|---|---|---|
| Never built | 26 | the whole of export and the creation record; the project identifier vocabulary; funding validation |
| Built, but no test proves it | 24 | the database constraints on description and date type; keywords and tags; the ordering; the metadata queryset; identifier uniqueness |
| Built differently, and the code is wrong | 8 | the date comparison reads fields that do not exist; two bulk actions set the wrong status; the identifier vocabulary offers person and organisation types; one status label does not name its state |
| Built partially | 9 | administrative search covers the owning organisation in code but not in test; inline editing is tested for descriptions only; the duplicate-description message does not name the type |

Two of the repository's existing tests are skipped rather than passing, both covering the date range
check: `test_end_date_before_start_date_raises_error` and `test_date_form_validates_range`. They are
counted as absent coverage.

One existing test is vacuous. `test_bulk_status_change_updates_selected_projects` posts the bulk
action and asserts only that the response is 200 — it never checks that any project's status
changed, which is why the wrong-status defect survived it. T056 replaces it.
