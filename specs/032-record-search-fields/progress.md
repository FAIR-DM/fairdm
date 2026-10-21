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
