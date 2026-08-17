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
      **Done:** fairdm/core/project/models.py:127 — covered by TestProjectDescriptions::test_add_multiple_descriptions_to_project
- [ ] T003 A typed description record for projects, bound to the project description vocabulary.
      Code exists (`fairdm/core/project/models.py:127`), but `type` is a plain character field and
      Django does not validate choices on save, so no existing test can tell a correct binding from a
      wrong one. Remaining work: a test asserting the offered choices are exactly the project
      description collection's members.
- [ ] T004 Test: attaching a second description of a type the project already carries fails
      validation, and the message names the type.
- [ ] T005 Validation refusing a duplicate description type.
- [ ] T006 Test: the duplicate is refused at the database as well, so a concurrent write cannot slip
      past validation.
- [ ] T007 A database constraint making description type unique per project.
      Already in code — `fairdm/core/abstract.py:278`, and re-declared as `unique_together` at
      `fairdm/core/project/models.py:130`, so this table carries it twice. **Add no third mechanism
      and no migration.** Remaining work is T006, the test.
- [ ] T008 Test: a term from a configured controlled vocabulary added as a keyword is stored as a
      reference to that vocabulary rather than as text.
- [ ] T009 Test: free tags are stored and remain distinguishable from controlled keywords.
- [ ] T010 Keyword and tag fields on the project.

## US-2 — Project dates and the timeline check (#159)

- [ ] T011 A factory for project dates, defaulting to a type the project date vocabulary contains.
- [ ] T012 A typed date record for projects, bound to a project date vocabulary containing a start
      and an end.
      Code exists (`fairdm/core/project/models.py:157`), and the binding is demonstrably unproven:
      `ProjectDateFactory` defaults to `type = "Created"`, which is not a member of the project date
      collection, and saves without error. Remaining work: a test asserting the offered choices are
      exactly the project date collection's members.
- [x] T013 Test: a start date attached to a project is stored under the start type.
      **Done:** fairdm/core/project/models.py:157 — covered by TestProjectDates::test_add_date_range_to_project
- [ ] T014 Test: a second start date on the same project is refused.
- [ ] T015 A database constraint making date type unique per project.
      Already in code — `fairdm/core/abstract.py:295`. **Add no second mechanism and no migration.**
      Remaining work is a test that the constraint refuses a duplicate date type.
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
      vocabulary's. Five models bind this vocabulary — projects, datasets, samples, measurements and
      contributors — so run the existing contributor and dataset identifier tests after the rename.
- [ ] T023 The project identifier record bound to the project collection rather than to the whole
      vocabulary.
- [ ] T024 A factory for project identifiers.
- [ ] T025 Test: a DOI attached to a project is stored under the DOI type.
- [ ] T026 Test: a grant number is stored alongside the DOI.
- [ ] T027 Test: attaching the same identifier value to a second project is refused.
- [ ] T028 Test: the identifier types offered for a project contain a DOI and a grant number, and
      contain no identifier that names a person or an organisation.

## US-4 — Funding in DataCite's shape (#161)

- [ ] T029 A validator for funding, accepting a list of DataCite funding references. The accepted
      keys are exactly `funderName`, `funderIdentifier`, `funderIdentifierType`, `awardNumber`,
      `awardTitle` and `awardURI`; `funderName` is required within a record; any other key is
      refused; every member of the list must be an object.
- [ ] T030 The funding field carrying that validator.
- [ ] T031 Test: an award with funder name, funder identifier, scheme, award number and award title
      round-trips with each part readable individually.
- [ ] T032 Test: a project carrying two awards retains both.
- [ ] T033 Test: an award naming only a funder is accepted.
- [ ] T034 Test: an award naming a funder identifier scheme outside DataCite's set is refused, and
      the message names the accepted schemes.
- [ ] T035 Test: funding that is not a list is refused, and a list whose members are not objects is
      refused with the same message rather than raising.
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
- [ ] T043 A module mapping a project to JSON-LD with an explicit context. The contributor block
      omits any email address — drop the key from each contributor's representation in the export
      rather than changing the shared transform, which other callers rely on.
- [ ] T044 Test: the JSON-LD output parses as JSON-LD and carries a context.
- [ ] T045 Administrative actions serialising both forms over a selection.
- [ ] T046 Test: exporting several projects together produces output carrying all of them.

## US-6 — The administrative interface (#163)

- [ ] T047 Administrative search over project name, the project's own generated identifier, any
      external identifier attached to it, and owning organisation. Name and generated identifier and
      owner are already in `search_fields` (`fairdm/core/project/admin.py:50`); the external
      identifier is not.
- [ ] T048 Test: a search term matching each of those three finds the project.
- [x] T049 A status filter on the administrative list.
      **Done:** fairdm/core/project/admin.py:57 — covered by TestAdminFilterByStatus::test_filter_by_concept_status
- [x] T050 Test: the status filter leaves only projects with that status.
      **Done:** fairdm/core/project/admin.py:57 — covered by TestAdminFilterByStatus::test_filter_by_concept_status
- [ ] T051 Inline editing of a project's descriptions, dates and identifiers from its own page.
- [ ] T052 Test: a description, a date and an identifier added inline all persist.
- [ ] T053 List columns showing whether a project carries an abstract and whether it carries a start
      date.
- [ ] T054 Test: those columns reflect the presence and absence of each.
- [ ] T055 Bulk actions setting a project's status.
- [ ] T056 Test: every bulk status action leaves the selected projects in the status its label names.

## US-7 — The creation record (#164)

- [ ] T057 A nullable reference from a project to the user who created it, surviving that user's
      removal. Not editable, and carrying `verbose_name` and `help_text` per Article IX.
- [ ] T058 A migration adding that reference.
- [ ] T059 The creator written wherever a project is created: the portal create view, and an
      override of `perform_create` on the project's own API viewset. **`BaseViewSet` is not
      modified** — the dataset, sample and measurement viewsets inherit it and have no such field.
      The value is set server-side from the request user and is never a writable serializer, form or
      admin field.
- [ ] T060 Test: a project created by a known user names that user as its creator.
- [ ] T061 Test: a project whose creator's account has been removed survives with its creator reading
      as unknown.
- [ ] T062 Test: changing a project advances its modification timestamp and leaves its creator
      unchanged.

## US-8 — The project record itself (#166)

- [x] T063 A unique, short, human-readable project identifier, prefixed and generated on creation,
      not editable afterwards.
      **Done:** fairdm/core/project/models.py:73 — covered by TestProjectModel::test_project_creation_with_required_fields, TestProjectModel::test_project_uuid_is_unique
- [ ] T064 Test: a newly created project carries a prefixed identifier, and the field cannot be
      edited.
      The prefix and uniqueness halves are covered; nothing asserts the field is not editable.
      Remaining work: that one assertion.
- [ ] T065 A required name, and an optional image, owning organisation and funding.
- [ ] T066 Test: a project with no owning organisation is valid.
- [ ] T067 A lifecycle status drawn from a controlled set, every member labelled with the state it
      names. The fields this task touches carry `verbose_name` and `help_text` per Article IX.
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
- [ ] T074 Test: a contribution records its contributor and its roles, and the roles read back.
      `test_add_contributor` passes roles in and never reads them back — it would pass unchanged if
      `add_contributor` ignored them. Remaining work: assert over the contribution's roles.
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

Seventy-nine tasks. **Eight are proven done**, each with a code citation and a passing test.
Seventy-one are open.

A task counts as done only where both halves exist. Code with no test leaves the task open and the
remaining work is the test — which turns this reconciliation into a complete test-gap audit of the
feature as a side effect. The old task list's checkboxes were not consulted.

Twelve were ticked on the first pass. A review of the reconciliation removed four of them, because
their cited tests could not observe the behaviour they claimed to prove:

- **T003 and T012** — `type` is a plain character field and Django does not validate choices on save,
  so no test that merely creates a row can tell a correct vocabulary binding from a wrong one. The
  proof that this blind spot is real is in the repository: the date factory defaults to a type the
  project date collection does not contain, and it saves without error.
- **T064** — the cited tests cover the prefix and the uniqueness, and say nothing about editability.
- **T074** — the cited test passes roles in and never reads them back. It would pass unchanged if
  roles were ignored entirely.

Why each open task is open:

| Reason | Count | Examples |
|---|---|---|
| Never built | 26 | the whole of export and the creation record; the project identifier vocabulary; funding validation |
| Built, but no test proves it | 28 | the database constraints on description and date type; the vocabulary bindings; keywords and tags; the ordering; the metadata queryset; identifier uniqueness |
| Built differently, and the code is wrong | 8 | the date comparison reads fields that do not exist; two bulk actions set the wrong status; the identifier vocabulary offers person and organisation types; one status label does not name its state |
| Built partially | 9 | administrative search has no external-identifier term; inline editing is tested for descriptions only; the duplicate-description message does not name the type |

Two of the repository's existing tests are skipped rather than passing, both covering the date range
check: `test_end_date_before_start_date_raises_error` and `test_date_form_validates_range`. They are
counted as absent coverage.

Four existing tests pass vacuously and are counted as gaps rather than coverage:

- `test_bulk_status_change_updates_selected_projects` posts the bulk action and asserts only that the
  response is 200. It never checks that any project's status changed, which is why two actions
  setting the wrong status survived it.
- `test_filter_by_visibility` asserts a public project appears and never that the private one is
  absent, so it would pass with the filter removed.
- `test_project_descriptions_relationship` and `test_project_dates_relationship` assert a count is
  greater than or equal to zero, which is true of any project including one with the relation gone.
