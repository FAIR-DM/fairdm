# Tasks: autocomplete fields for records, people and organizations

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [sketch.md](sketch.md)

**Tests first**: in every story the test tasks come first and are seen to fail before the code that
makes them pass is written. Views are tested through the test client on their real addresses,
fields through real forms built inside a request, pages through the test client on their real
routes. Wording and appearance get no tests.

**Format**: `[ID] [Story] Description`.

**Story order**: US1, US2, US3, US5, US6, US7, US8, then US4, each from the previous story's
accepted commit.

## Phase 1: US-1, a researcher chooses the dataset a new sample goes into (P1)

This story carries the foundation (plan D1 to D6). The sketch's `records.py`, `records_fields.py`,
`sketch_pages.py`, `seed_autocomplete_sketch.py` and their URL entries are deleted here, and
`fairdm/contrib/autocomplete/templates/` and `fairdm/templates/django_tomselect/` are kept.

- [ ] T001 [US1] `tests/test_contrib/test_autocomplete/test_views.py`, `TestDatasetAutocompleteView`:
  on the `edit` address a researcher is offered the private dataset they can edit, and not a
  public dataset they cannot edit, nor a private one they cannot see (AS 1.1 to 1.3). Each result
  carries the dataset's project and a private flag in its drawn row (AS 1.4). Results are grouped
  own before public before role-wide, a record once (FR-016), and a page past the first is served
  on request (AS 1.8). Someone not signed in gets nothing from `edit` and public datasets from
  `public` and `view` (FR-008).
- [ ] T002 [US1] Same module, `TestProjectAutocompleteView`: the `edit` address offers private
  projects the researcher can edit and no others (AS 1.7). A Data Curator gets every project, own
  first (clarification 5).
- [ ] T003 [US1] Same module, `TestRecordAutocompleteViewLimits`: a request's `page_size` is
  ignored, a search longer than 100 characters is cut, no page past 25 is served, and a `filter_by`
  lookup outside the view's allow-list is answered 400 with nothing searched (FR-011, FR-022). A
  failing search answers with nothing but the failure (FR-024).
- [ ] T004 [US1] `tests/test_contrib/test_autocomplete/test_throttling.py`: a visitor over the burst
  rate is answered 429 with `Retry-After`, and no query runs (`django_assert_num_queries(0)` after
  the throttle). A signed-in caller is counted by account, so two accounts behind one address are
  counted apart. Another caller is answered normally while one is over (SC-006, US 3 AS 9 and 10).
  The "searching is paused" message test is written and skipped with the upstream-gaps issue
  number (FR-021).
- [ ] T005 [US1] `tests/test_contrib/test_autocomplete/test_fields.py`, `TestRecordFields`: a
  `DatasetChoiceField(scope="edit")` on a form built inside a request accepts a dataset the user
  can edit and refuses, with the field's `invalid_choice` error, one they cannot (AS 1.5, AS 1.6,
  FR-010). A stored dataset the editor cannot see is kept when submitted unchanged and labelled as
  a private record, without its name, in the rendered widget (FR-012).
- [ ] T006 [US1] `tests/test_core/test_sample/test_forms.py` and
  `tests/test_core/test_dataset/test_forms.py`: replace the tests expecting `ModelSelect2Widget` and
  `AddAnotherWidgetWrapper` with tests that the sample form's dataset and the dataset form's
  project are the new fields at `edit` scope, and that a sample saved through the form belongs to
  the chosen dataset.
- [ ] T007 [US1] Write `throttling.py`, `RecordAutocompleteView` with `ProjectAutocompleteView` and
  `DatasetAutocompleteView`, the record fields function and the project and dataset pairs,
  `urls.py` entries, the throttle rates in `fairdm/api/settings.py`, `django_tomselect` and its
  middleware in `fairdm/conf/settings/apps.py` (below `mvp_forms`, with the reason as a comment),
  the stylesheet and script links in `fairdm/templates/base.html`. Keep the sketch's templates.
  Open the upstream-gaps issue in this repository (research, "Gaps in dependencies") and put its
  number in the two django-tomselect templates and the skipped test. Move `SampleFormMixin`,
  `MeasurementFormMixin.dataset` and `DatasetForm.project` to the fields. Delete the sketch's
  Python and its seed command.
- [ ] T008 [US1] Docs: `docs/portal-development/forms-and-filters/sample-mixins.md` and
  `measurements.md` say what the dataset field now is. Start the how-to and the reference page
  (plan D10) with the dataset and project fields.

## Phase 2: US-2, a researcher chooses the sample a measurement was made on (P1)

- [ ] T009 [US2] `test_views.py`, `TestSampleAutocompleteView`: narrowed by `dataset_id` only that
  dataset's samples are offered (AS 2.1). A local ID or an identifier typed exactly comes first
  (AS 2.2). Each row gives type, local ID and dataset (AS 2.3). Public samples are those in a public,
  published dataset. `TestMeasurementAutocompleteView` the same for measurements, without
  identifiers.
- [ ] T010 [US2] `test_fields.py`, `TestDependentFields`: `SampleChoiceField(depends_on="dataset")`
  renders the filter hook django-tomselect reads for `dataset`, and refuses a sample from another
  dataset on submit (AS 2.5). The measurement form test asserts the same through
  `tests/test_core/test_measurement/test_forms.py`.
- [ ] T011 [US2] Write `SampleAutocompleteView`, `MeasurementAutocompleteView` and their field
  pairs, and move `MeasurementFormMixin.sample`. Clearing the sample when the dataset changes is
  django-tomselect's own behaviour for a dependent field and gets no test of ours.
- [ ] T012 [US2] Docs: the reference page gains the sample and measurement fields and `depends_on`.

## Phase 3: US-3, a visitor filters a public list by a related record (P1)

- [ ] T013 [US3] `tests/test_contrib/test_autocomplete/test_filters.py`, `TestRecordMultipleFilter`:
  on the sample list the dataset filter offers public datasets to a visitor and to a signed-in
  researcher with private datasets alike (AS 3.1, 3.2). Two ticked datasets narrow the list to
  their samples (AS 3.3), and the filter's values come back from the list's address (AS 3.4).
- [ ] T014 [US3] `tests/test_core/test_project/test_filters.py`,
  `test_dataset/test_filters.py`, `test_measurement/test_filters.py`: the owner, contributor,
  project, dataset and sample filters are record filters at `public` scope and narrow their lists
  (AS 3.6). The keyword filters still narrow the project list with no django-autocomplete-light
  widget.
- [ ] T015 [US3] `tests/test_registry/test_factories.py`: a registered type's generated filter for a
  related dataset is a record filter at `public` scope (AS 3.5).
- [ ] T016 [US3] Write `filters.py`, move the list filters and the generated filters
  (`fairdm/registry/factories.py`, `_get_smart_filters`), and move the keyword filters to
  `mvp_forms.widgets.TomSelectMultiple(counted=True)`.
- [ ] T017 [US3] Docs: `docs/portal-development/filtering-by-vocabulary.md` drops
  `ConceptMultiSelect` and the `/autocomplete/concept/` address. The how-to covers filters.

## Phase 4: US-5, a researcher chooses a person or an organization (P2)

- [ ] T018 [US5] `test_views.py`, `TestOrganizationAutocompleteView`: name and alternative-name
  search, exact ROR first, the requester's current organizations grouped first (AS 5.1 to 5.3),
  row gives place and no identifier.
- [ ] T019 [US5] `test_views.py`, `TestPersonAutocompleteView`: collaborators grouped first
  (AS 5.4), an email typed finds nobody and no row carries one (AS 5.5, FR-019), an unclaimed person
  is marked (AS 5.6), a collaboration only through a record the requester cannot open does not
  group (AS 5.7), superusers are not offered.
- [ ] T020 [US5] `tests/test_contrib/test_contributors/test_forms/`: the affiliation form's
  organization, the organization profile's parent, `PersonCreateForm.affiliations`, the person
  merge target and `UpdateContributionForm.roles` draw and save with the new fields and with
  `TomSelectMultiple` for roles. `ProjectForm.owner` the same, in
  `tests/test_core/test_project/test_forms.py`.
- [ ] T021 [US5] Write the two views and the person and organization pairs, move those forms, and
  delete `ContributorSelect2Widget`, `PersonSelect2Widget`, `OrganizationSelect2Widget` and
  `QuickAddContributionForm`.
- [ ] T022 [US5] Docs: `docs/portal-development/contributors.md` (parent picker) and
  `docs/portal-administration/managing_contributors.md`.

## Phase 5: US-6, a researcher links a dataset to its data publication (P2)

- [ ] T023 [US6] `test_views.py`, `TestPublicationAutocompleteView`: title and author search, exact
  DOI first, row gives authors and year (AS 6.1 to 6.3). `test_dataset/test_forms.py`: the dataset
  saves the chosen publication (AS 6.4).
- [ ] T024 [US6] Write the view and `PublicationChoiceField`, move `DatasetForm.reference`.

## Phase 6: US-7, a researcher tags a record (P3)

- [ ] T025 [US7] `test_views.py`, `TestTagAutocompleteView`: tags in use are offered by part of
  their name (AS 7.1). `tests/test_contrib/test_generic/test_forms.py`: the keyword form saves an
  existing tag and a new one (AS 7.2) and shows its tags chosen when reopened (AS 7.3).
  `test_filters.py`, `TestTagFilter`: the project list's tag filter narrows by tags in use and
  offers no way to add one.
- [ ] T026 [US7] Write the view, `TagsField(allow_new=…)` and `TagFilter`, move `KeywordForm.tags`
  and the project list's tag filter, delete `TagWidget`.

## Phase 7: US-8, a profile maintainer looks up an organization's ROR record (P3)

- [ ] T027 [US8] `test_views.py`, `TestRorAutocompleteView`, with `Ror.search` faked at the network
  boundary: entries with their country (AS 8.1), 503 when ROR does not answer (AS 8.3), the same
  limits as the record views (FR-025). The organization form saves the chosen ROR ID and saves
  without one when ROR is down (AS 8.2, 8.3).
- [ ] T028 [US8] Write the view and `RorChoiceField`, move the organization form, delete
  `RORWidget` and `widgets/ror.html`.

## Phase 8: US-4, a portal developer adds a record field to a form or filter (P1)

- [ ] T029 [US4] `test_fields.py`, `TestFieldSettings`: a field with nothing configured offers what
  the person may see (AS 4.1), the multiple field saves every chosen record (AS 4.2), `scope` and
  `type` narrow as set (AS 4.3 to 4.5), `depends_on` narrows (AS 4.6), and `owner` offers that
  person's private records only to them (FR-009, US 3 AS 7 and 8).
- [ ] T030 [US4] `tests/test_registry/test_factories.py`: a registered type's generated form for a
  related dataset uses the dataset field at `edit` scope with no configuration (AS 4.7).
- [ ] T031 [US4] Write `owner` and `type`, the generated forms, and the admin moves (plan D8), with
  `tests/test_contrib/test_admin/` and the dataset admin tests loading the changed admin pages.
- [ ] T032 [US4] Remove django-autocomplete-light, django-select2 and django-addanother (plan D9),
  the old `views.py` and `fields.py` contents, `SelectizeWidget`, `CreatorsFormField`,
  `fairdm/templates/django_addanother/`, the Select2 suggestions in `fairdm/utils/inspection.py`
  and the select2 cache settings. `deptry` and `manage.py check` pass.
- [ ] T033 [US4] Demo: the seed command and one demo form using `SampleChoiceField(type=…)`, with
  a test in `demo/tests/`.
- [ ] T034 [US4] Docs: finish the how-to and the reference page (every field, argument, default,
  address and throttle setting, with a working example each), the CHANGELOG with the breaking
  changes and a migration guide, and `CONTEXT.md`'s Autocomplete field entry.
