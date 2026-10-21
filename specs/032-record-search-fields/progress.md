# Progress: FS-032

- 2026-10-21: specification approved; issue graph built (#541, stories #544 to #551).
- 2026-10-21: sketch approved after three rounds at 7a4f2e4d.
- 2026-10-21: research, plan and tasks written.

## 2026-10-21T12:23:00Z · Implementer US1 · T001

Did: DatasetAutocompleteView on RecordAutocompleteView, scoped subclasses and the three dataset addresses; tests for edit/view/public, grouping, paging, visitors, escaping, uuid.
Verified: uv run pytest -q -n0 tests/test_contrib/test_autocomplete/test_views.py -> 16 passed.
Next: T002 project view.
Watch: page parameter is p, not page; sanitize_dict returns SafeString so no unescape.

## 2026-10-21T12:23:54Z · Implementer US1 · T002

Did: ProjectAutocompleteView and its three project addresses.
Verified: uv run pytest -q -n0 tests/test_contrib/test_autocomplete/test_views.py -> 20 passed.
Next: T003 limits on every address.
Watch: none.

## 2026-10-21T12:27:36Z · Implementer US1 · T003

Did: LimitedAutocompleteMixin (fixed page size, 100-char search, page cap, empty allow-lists, failure answer with nothing else) under RecordAutocompleteView.
Verified: uv run pytest -q -n0 tests/test_contrib/test_autocomplete/test_views.py -> 74 passed. Probed the filter allow-list by setting it to None: 12 tests failed, restored.
Next: T004 throttling.
Watch: f/e outside the allow-list yield no results (library behaviour), ordering is ignored because the view orders itself.

## 2026-10-21T12:30:57Z · Implementer US1 · T004

Did: throttling.py with four scoped classes and a default_rate fallback; LimitedAutocompleteMixin.dispatch refuses over-limit callers with 429, Retry-After and an empty result list before any query.
Verified: uv run pytest -q -n0 tests/test_contrib/test_autocomplete tests/test_api/test_throttling.py passed. No-query check calls the view directly because the test client wraps requests in savepoints.
Next: T005 field.
Watch: rates not added to the API dictionary (decisions D14): a pre-existing API test pins that dictionary to four scopes.

## 2026-10-21T12:34:42Z · Implementer US1 · T005

Did: RecordFieldMixin, record_fields(), Project/Dataset single and multiple fields. Fields validate through the scoped view offered() plus the stored value; label stored unseen value as private without a name.
Verified: pytest tests/test_contrib/test_autocomplete passed. Probed four mutations (allow all, drop stored, leak name, widen offered): each failed tests.
Next: T006 forms.
Watch: fields read the person from form.request, else the current request.

## 2026-10-21T12:44:08Z · Implementer US1 · T006

Did: sample and measurement forms use DatasetChoiceField(scope=edit), DatasetForm uses ProjectChoiceField(scope=edit). Replaced six tests that pinned the old widgets (sample, measurement, dataset forms; sample config; registry factories) and removed the two add-another URL tests.
Verified: pytest over autocomplete, sample, dataset, measurement, registry, project -> 1789 passed, 7 skipped.
Next: T007 settings, base.html, dependencies check, sketch cleanup, issue number.
Watch: field with no request validates against its own queryset (decisions D15).

## 2026-10-21T12:45:12Z · Implementer US1 · T007

Did: foundation complete across T001-T006 (throttling.py, views, fields, urls, form moves); named #554 in the two django_tomselect templates; removed sketch labels from the four templates. Sketch Python and seed were already deleted at the branch start.
Verified: manage.py check clean, deptry clean (DEP002 gone), autocomplete tests pass.
Next: T008 docs.
Watch: rates stay on the throttle classes (decisions D14).

## 2026-10-21T12:46:25Z · Implementer US1 · T008

Did: sample-mixins.md and measurements.md describe the dataset field; new how-to add-a-record-field.md and reference record-fields.md, both in the portal-development toctree.
Verified: link targets checked by reading; the documentation build was not run here (sphinx missing).
Next: full verify and report.
Watch: the reference lists only the project and dataset kinds, which are the ones built so far.

## 2026-10-21T13:07:57Z · Implementer US2 · T009

Did: SampleAutocompleteView and MeasurementAutocompleteView over a shared base for records inside a dataset; registered at sample/measurement x public/view/edit. offered() gained depends_on. Fixtures make_sample/make_measurement; make_record now builds all four kinds, so the shared limit tests cover the new addresses.
Verified: pytest test_views.py full file 140 passed; the two new classes 12 passed. ruff clean.
Next: T010 dependent fields and the measurement form move.
Watch: django-tomselect empties value_fields on a subclass that does not set it on its own class, so each concrete view names DATASET_RECORD_FIELDS itself.

## 2026-10-21T13:10:28Z · Implementer US2 · T010

Did: depends_on on the record fields (filter hook for the widget, narrowing read from the bound form's data, refused value that is not a key); SampleChoiceField, MeasurementChoiceField and their multiple pairs; MeasurementFormMixin.sample now SampleChoiceField(depends_on='dataset').
Verified: test_fields.py and test_measurement/test_forms.py: 49 passed, 1 failed (pre-existing test_form_handles_cross_dataset_sample_reference, which contradicts AS 2.5; not edited).
Next: T011 check, T012 docs.
Watch: the pre-existing cross-dataset test; docs still describe cross-dataset measurements.

## 2026-10-21T13:10:28Z · Implementer US2 · T011

Did: nothing further beyond T010's field pairs and form move; ran the project check.
Verified: manage.py check: no issues.
Next: T012 docs.
Watch: none.

## 2026-10-21T13:10:28Z · Implementer US2 · T012

Did: record-fields.md gains the sample and measurement fields, depends_on with an example, the row keys and the filters; measurements.md describes the form's dataset and sample fields as they now are.
Verified: the example mirrors DependentSampleForm in TestDependentFields, which passes.
Next: full verify and report.
Watch: managing-measurements.md and the cross-dataset lines of measurements.md left as they were, pending a ruling.

## 2026-10-21T13:31:54Z · Implementer US3 · T013

Did: RecordMultipleFilter in fairdm/contrib/autocomplete/filters.py (a ModelMultipleChoiceFilter drawing the multiple record field, public scope by default, handing the field the filter set's request); the sample list's dataset filter now uses it. Tests in test_autocomplete/test_filters.py. Updated the sample and collections tests that pinned the old ModelChoiceFilter queryset.
Verified: uv run pytest -q -n0 tests/test_contrib/test_autocomplete tests/test_core/test_sample/test_filters.py tests/test_contrib/test_collections/test_views.py::TestFilterChoicesOnTheRenderedPage: 264 passed, 4 skipped (earlier skips). tests/test_api ran green on the first pass of the change (1710 passed across sample, collections, api).
Next: T014 other list filters and project keyword filters.
Watch: the old privacy tests offered a private dataset to a reader who may view it; at public scope nobody is offered one.

## 2026-10-21T13:38:07Z · Implementer US3 · T014

Did: dataset list project filter, measurement list dataset and sample filters moved to RecordMultipleFilter at public scope; project keyword filters now use mvp_forms TomSelectMultiple(counted=True) with no django-autocomplete-light widget. Project list owner and contributor left as they are (US5). Updated the dataset, measurement and dataset-view tests that pinned the old ModelChoiceFilter queryset or offered private records.
Verified: uv run pytest -q -n 8 tests/test_contrib tests/test_core tests/test_api tests/test_registry: 6305 passed, 7 skipped, 5 failed; the failures were the one known cross-dataset test plus tests pinning the old types, since fixed (110 passed on the re-run of those files). tests/test_api green.
Next: T015 generated filters for related project, dataset, sample, measurement.
Watch: two collections tests on ExampleMeasurement's dataset and sample filters still pin .queryset; they change with T015, because that type's filters come from the generated set.

## 2026-10-21T13:40:54Z · Implementer US3 · T015

Did: FilterFactory._get_smart_filters makes a RecordMultipleFilter (public scope) for a foreign key to a project, dataset, sample or measurement; other foreign keys keep their ModelChoiceFilter. Rewrote TestPublishedChoiceLists as TestGeneratedRelatedRecordFilters; moved the two collections tests on ExampleMeasurement's dataset and sample filters to the field's offered records.
Verified: uv run pytest -q -n0 tests/test_registry: 271 passed; collections TestFilterChoicesOnTheRenderedPage 5 passed.
Next: T016 API.
Watch: PublishedChoicesMixin still scopes any filter that has a queryset; record filters have none and are scoped by their view.

## 2026-10-21T13:40:55Z · Implementer US3 · T016

Did: the API's DatasetFilterSet.match_relations_on_uuid swaps a RecordMultipleFilter for a plain ModelMultipleChoiceFilter (RecordMultipleFilter.for_api) over the public records, then matches on uuid as before. The sample, dataset and measurement mixins no longer assign querysets to those filters.
Verified: tests/test_api full folder green in the combined run (6305 passed with the one known failure); TestRecordFiltersInTheApi fails when the swap is removed (probe) and passes with it.
Next: T017 docs, then the full suite.
Watch: none.

## 2026-10-21T13:41:37Z · Implementer US3 · T017

Did: filtering-by-vocabulary.md now describes the counted TomSelectMultiple keyword control and drops ConceptMultiSelect and the /autocomplete/concept/ address; add-a-record-field.md gains "Filter a list by a record"; record-fields.md gains a Filters section; sample-mixins.md says the dataset filter offers public datasets.
Verified: docs only; the example filter in the how-to mirrors the tested sample list filter.
Next: full suite.
Watch: ConceptMultiSelect, ConceptSelect and ConceptAutocomplete still exist in code (removal belongs to the django-autocomplete-light removal story).

## 2026-10-21T14:05:03Z · Implementer US5 · T018

Did: OrganizationAutocompleteView and the shared ContributorAutocompleteView, the organization-public and person-public addresses, and 9 tests. The old django-autocomplete-light contributor and organization views and their addresses are deleted.
Verified: pytest tests/test_contrib/test_autocomplete/test_views.py: 149 passed. Red first on NoReverseMatch (9 failed).
Next: person tests (the person view is already in the same commit).
Watch: the shared base answers for_scope() with itself.

## 2026-10-21T14:05:03Z · Implementer US5 · T019

Did: 15 tests for the person view.
Verified: pytest TestPersonAutocompleteView: 15 passed. The view was written in T018, so no red step; probed by mutation instead: Person.objects.real() replaced by all() (4 failed), every credit counted (1 failed), email added to search_lookups (1 failed). Each mutation reverted.
Next: forms and fields.
Watch: e= and f= naming email give an empty page by the library allow-list, see D25.

## 2026-10-21T14:05:03Z · Implementer US5 · T020

Did: PersonChoiceField, OrganizationChoiceField and their multiple pairs (scopes=("public",)). Moved AffiliationForm.organization, the organization profile parent, PersonCreateForm.affiliations, MergePersonForm.merge_into, OrganizationActionForm.new_owner, ProjectForm.owner. Roles use TomSelectMultiple(counted=True). merge_person.html carries form.media. Deleted the three select2 widgets and QuickAddContributionForm. PersonCreateForm no longer passes is_current (D26).
Verified: red first (10 failed); then pytest tests/test_contrib/test_contributors/test_forms tests/test_core/test_project/test_forms.py tests/test_contrib/test_contributors/test_admin.py tests/test_contrib/test_autocomplete: 450 passed.
Next: project list filters.
Watch: ruff format on the whole tree reformats unrelated test files; I restored them.

## 2026-10-21T14:05:04Z · Implementer US5 · T021

Did: the project list owner and contributor filters are RecordMultipleFilter over the organization and person multiple fields. Scope check for the new fields.
Verified: red first (4 failed); pytest tests/test_core/test_project tests/test_views: 418 passed; test_fields.py 23 passed.
Next: docs.
Watch: the old owner filter listed only organizations that own projects; the new one offers every organization.

## 2026-10-21T14:05:04Z · Implementer US5 · T022

Did: record-fields.md gains a people and organizations section, the two fields, addresses and result keys. contributors.md parent picker. managing_contributors.md: New owner and Merge into pickers.
Verified: grep finds no mention of the deleted classes in docs, fairdm, demo or tests.
Next: lint and the full suite.
Watch: CHANGELOG is not touched.

## 2026-10-21T14:30:42Z · Implementer US2 · T035

Did: added `prefer` to the record fields (beside depends_on). The widget sends `prefer=<relation>=<value>` through the tomselect template override; the sample and measurement views rank the matching records first in a group of their own ("Samples in this dataset") and filter nothing. The view accepts the preference only for the relations it allows a request to filter on (dataset, polymorphic_ctype) and ignores a value that cannot name a record. The measurement form's sample field uses prefer="dataset". Reworked the US2 tests (views, fields, measurement form) to the amended scenarios; updated record-fields.md and measurements.md.
Verified: uv run pytest -n0 tests/test_contrib/test_autocomplete tests/test_core/test_measurement/test_forms.py: 321 passed, 1 failed. Full suite -n 8: 7324 passed, 8 skipped, 1 failed. forge verify lint,typecheck,build: passed.
Next: Forge to rule on test_form_handles_cross_dataset_sample_reference. Its sample sits in a private dataset the user holds no level on, so AS 2.5 requires refusing it. I did not edit the test or special-case the field.
Watch: the JS in the tomselect template override (prefer wiring and the reset on change) is not covered by any test.

## 2026-10-21T14:43:44Z · Implementer US6-US8 · T024

Did: PublicationAutocompleteView (title, author and DOI search, exact DOI first, row from record_option.html with authors and year and the DOI as an outline badge), its address `autocomplete:publication`, PublicationChoiceField (validates against all literature, never calls django-tomselect's clean), DatasetForm.reference moved to it. The old test pinning a plain Select on reference is replaced by two that pin the new field and its saving.
Verified: red first (7 view tests fail for the missing address, test_forms.py fails to import the field); then pytest -n0 tests/test_contrib/test_autocomplete/test_views.py::TestPublicationAutocompleteView tests/test_core/test_dataset/test_forms.py: 37 passed.
Next: tags.
Watch: ruff check fixes files outside the story (it rewrote tests/test_core/test_dataset/test_plugins.py); I restored it and use --no-fix.

## 2026-10-21T14:43:53Z · Implementer US6-US8 · T023

Did: TestPublicationAutocompleteView (title, author, exact DOI first, a DOI typed as an address, a DOI typed in part finds nothing, the row's authors/year/DOI, a bare publication), make_publication fixture, and a limits test that takes each new address in turn (publication now; tag and ROR join with their views). The dataset form tests for AS 6.4 were committed with T024.
Verified: the tests failed first on the missing address; pytest -n0 TestPublicationAutocompleteView and the publication case of TestNewViewsTakeTheLimits: passed.
Next: tags.
Watch: none.

## 2026-10-21T14:51:51Z · Implementer US6-US8 · T026

Did: TagAutocompleteView (a model view over taggit's Tag; the tags in use on records the record views of the same scope offer, at addresses tag-view and tag-public), TagsField(scope, allow_new) with its widget (chips with a remove button, chosen tags shown without a lookup, cleans to stripped unique strings, refuses a tag nobody uses unless allow_new), TagFilter, KeywordForm.tags moved to TagsField(allow_new=True), the project list's tag filter moved to TagFilter, TagWidget deleted. record-fields.md gains publications and tags sections; record-editing-pages.md describes the keyword field.
Verified: red first (9 view/form tests failed, filter tests failed to import); pytest -n4 tests/test_core/test_project tests/test_contrib/test_generic tests/test_contrib/test_autocomplete tests/test_core/test_editing.py: 1112 passed, 8 failed (the keyword page tests that read option[selected] out of the old widget); those two tests now read the form's value, and the `chosen` helper they alone used is gone: 28 passed in TestEditKeywords. Probed: removing the content-type restriction in TagAutocompleteView.offered makes the same-key test fail.
Next: Tag tests are committed as T025.
Watch: TaggedItem.object_id is the text of an integer key and equal across tables, so the view restricts by content type (the concrete model's, for samples and measurements).

## 2026-10-21T14:52:09Z · Implementer US6-US8 · T025

Did: TestTagAutocompleteView (found by part of a name, a private record's tag withheld, a public record's tag offered to a visitor, the public address offering only public records' tags, an unused tag not offered, a tag on several records offered once, a same-key record of another kind not leaking its tag), TestTagFilter (narrowing by either of two tags, once for a project with both, a private project's tag refused, a researcher offered the same as a visitor, an unused tag refused, no way to add), TestKeywordFormTags (existing and new tag saved, stripping and blanks, removal, clearing, shown as chosen on reopening, new tags allowed), and the tag addresses join the limits test.
Verified: the tests failed first for the missing address, the missing filter and the old widget; now pytest -n0 on the four classes: 23 passed.
Next: the ROR lookup.
Watch: none.

## 2026-10-21T14:57:13Z · Implementer US6-US8 · T028

Did: RorAutocompleteView (an AutocompleteIterablesView over Ror.search with the mixin's throttles and text cut; nothing asked for an empty search; 503 on RegistryUnavailable; 500 with no detail on any other failure; one page), address autocomplete:ror, RorChoiceField (clean() accepts a value that is a ROR ID or address by form through Ror.identifier_in and never asks the registry), the organization form's from_ror moved to it, RORWidget and widgets/ror.html deleted. record-fields.md gains a ROR lookup section.
Verified: red first (the form test module failed to import the field, the view tests had no address); then pytest -n4 tests/test_contrib/test_contributors tests/test_contrib/test_autocomplete: 2527 passed.
Next: lint and the full suite.
Watch: the field shows a chosen value's ROR ID as its label when a form is shown again after a refusal, since the form has no organization name to give it. The "lookup is unavailable" message of AS 8.3 is not drawn: the address answers 503 and the control shows no results.
