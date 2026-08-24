# Progress — 013 Managing a project through the portal

## 2026-08-24T12:50:39+02:00 · Implementer US3 · T001

**Did**: Exported `ProjectDateFactory` from `fairdm/factories/__init__.py`, alongside the
already-exported `ProjectDescriptionFactory` and `ProjectIdentifierFactory`.

**Verified**: `poetry run pytest tests/test_core/test_project/test_factories.py -q` — 2 passed.

**Next**: T002.

**Watch**: the package docstring's "Relations" list (`fairdm/factories/__init__.py:50-55`) was
already incomplete before this task — it omits `ProjectDescriptionFactory`/`ProjectIdentifierFactory`
and several dataset/sample equivalents. Left as-is rather than rewritten out of scope; see `concerns`
in the completion report.

---

## 2026-08-24T12:54:01+02:00 · Implementer US3 · T002

**Did**: Added `fairdm/core/related_records.py` — `RelatedRecordInline` (the shared row-set base:
`fields = ("type", "value")`, `extra = 0`) and four subclasses naming only their model:
`ProjectDateInline`, `ProjectIdentifierInline`, `DatasetDateInline`, `DatasetIdentifierInline`.

Hit a real bug mid-task: `fields` as a list is the same list object `BaseInlineFormSet.__init__`
mutates in place (appends the parent FK's name), so the first formset built from any subclass
permanently corrupted the shared base class attribute for every other subclass. Reproduced with a
failing test, fixed by declaring `fields` as a tuple (Django's own copy-on-write branch for that
case), kept the regression test. See `decisions.md` (Implementer decisions, this task).

**Verified**: `poetry run pytest tests/test_core/test_related_records.py -q` — 12 passed.
`poetry run ruff check fairdm/core/related_records.py tests/test_core/test_related_records.py` — clean.

**Next**: T004 (built next, out of brief order — see `decisions.md`).

**Watch**: nothing.

---

## 2026-08-24T12:54:06+02:00 · Implementer US3 · T004

**Did**: Added `fairdm/core/descriptions.py` — `VocabularyDescriptionsForm`, a plain `forms.Form`
generating one `CharField` per concept in `related_model.VOCABULARY`, labelled with the concept's
name and helped by its definition. `save()` writes, updates or deletes one row per area
(whitespace-only treated as blank).

Originally built in the same module as T002's row sets; split into its own file before committing
so each task's commit stays clean and the module boundary matches who consumes each piece later
(portal row sets vs. the descriptions page). See `decisions.md`.

**Verified**: `poetry run pytest tests/test_core/test_descriptions.py -q` — 6 passed.
`poetry run ruff check fairdm/core/descriptions.py tests/test_core/test_descriptions.py` — clean.

**Next**: T003.

**Watch**: nothing.

---

## 2026-08-24T12:56:01+02:00 · Implementer US3 · T003

**Did**: Added `fairdm/core/formsets.py` — `date_ordering_formset(start_type, end_type, noun)`,
returning a `BaseInlineFormSet` refusing a backwards pair across the whole formset (logic and
message lifted from `ProjectAdmin.DateInlineFormSet`, generalised to take its noun as a parameter).
Pointed `fairdm/core/project/admin.py` and `fairdm/core/dataset/admin.py` at it; deleted the
duplicate `DateInlineFormSet` class body in both (the module-level name stays, now bound to the
shared factory's return value, so `DateInline.formset = DateInlineFormSet` needed no further
change). Removed the now-unused `ValidationError`/`BaseInlineFormSet`/`PartialDate` imports from
both admin modules.

The dataset message's wording narrows from "collection end date"/"collection start date" to the
shared template's "end date"/"start date" (with "dataset" as the noun) — no test asserts on the
literal string, but recorded in `decisions.md` since it's user-facing text that changed on purpose.

**Verified**: `poetry run pytest tests/test_core/test_formsets.py tests/test_core/test_project/test_admin.py tests/test_core/test_dataset/test_admin.py -q`
— 64 passed (5 new + 59 pre-existing, all pre-existing ones still green with no edits).
`poetry run ruff check fairdm/core/formsets.py fairdm/core/project/admin.py fairdm/core/dataset/admin.py tests/test_core/test_formsets.py` — clean.

**Next**: T005.

**Watch**: nothing.

---

## 2026-08-24T12:57:22+02:00 · Implementer US3 · T005

**Did**: Added `tests/test_core/test_project/conftest.py` — `public_project`, `private_project`,
`user_with_change_permission`, `user_with_delete_permission`, `user_with_no_permission`. The three
user fixtures each build their own project and carry it as an in-memory `.project` attribute on the
returned user, so a test can assert the grant using only the one fixture it asked for. See
`decisions.md`.

**Verified**: `poetry run pytest tests/test_core/test_project/test_conftest.py -q` — 5 passed.
`poetry run pytest tests/test_core/test_project -q` — 146 passed (whole package, no regressions from
the new conftest). `poetry run ruff check tests/test_core/test_project/conftest.py tests/test_core/test_project/test_conftest.py` — clean.

**Next**: story complete. Full-suite verify at the completion report.

**Watch**: nothing.

## 2026-08-24T15:20:00+02:00 · Implementer US3 · T026

**Did**: Added `TestAttributesPageOverHTTP` to `tests/test_core/test_project/test_plugins.py` —
asserts the attributes page's reversed URL is keyed by the project's own identifier
(`/projects/<uuid>/attributes/`) rather than an address of its own, and that an anonymous GET
redirects to sign-in. Both pieces of this behaviour already existed spread across
`TestAttributesAndDeletionAreExtraViewsNotEntries` (URL shape) and
`tests/test_core/test_project/test_views.py::TestProjectUpdateView` (anonymous redirect, under
stale pre-restructuring numbering) — this test composes both claims in one place as the
canonical acceptance test named by the brief, without touching either pre-existing test.

**Verified**: `poetry run pytest tests/test_core/test_project/test_plugins.py::TestAttributesPageOverHTTP -q`
— 2 passed. `poetry run ruff check tests/test_core/test_project/test_plugins.py` — clean.

**Next**: T028.

**Watch**: nothing.

---

## 2026-08-24T15:22:00+02:00 · Implementer US3 · T028

**Did**: Added `test_a_user_holding_change_permission_at_the_model_level_is_admitted` to
`TestAttributesPageOverHTTP` — grants `project.change_project` via Django's own
`user_permissions` (model level, no per-object grant) and asserts a real GET to a project the
user holds no individual grant on returns 200. Confirms `has_perm`'s two-call shape
(`fairdm/contrib/plugins/access.py`) carries across from the retiring standalone page, per plan
P1. No production code changed — the behaviour already exists; only the model-level case had no
test.

**Verified**: `poetry run pytest tests/test_core/test_project/test_plugins.py::TestAttributesPageOverHTTP -q`
— 3 passed. `poetry run ruff check tests/test_core/test_project/test_plugins.py` — clean.

**Next**: T029.

**Watch**: nothing.

## 2026-08-24T15:40:00+02:00 · Implementer US3 · T029-T033

**Did**: Added `TestProjectUpdateForm.test_the_field_set_is_exactly_image_name_status_visibility_owner`
(T029, set equality) and `test_the_form_offers_no_description_keyword_tag_contributor_or_funding_field`
(T030) to `tests/test_core/test_project/test_forms.py`. Both passed on first run — `ProjectForm.Meta.fields`
already pinned this set exactly; no production change needed.

Added three submission tests to `TestProjectUpdateView` in `tests/test_core/test_project/test_views.py`:
`test_changing_name_status_visibility_and_owner_each_persists` (T031, one field changed at a time
against a fresh copy of the same starting project), `test_uploading_an_image_persists_it_and_clearing_it_removes_it`
(T032, upload then `image-clear`), `test_submitting_an_empty_name_reports_an_error_and_saves_nothing`
(T033). All three passed on first run against the existing `ProjectForm`/`Attributes` view.

**Verified**: `poetry run pytest tests/test_core/test_project/test_forms.py tests/test_core/test_project/test_views.py -q`
— all passing. `poetry run ruff check tests/test_core/test_project/test_forms.py tests/test_core/test_project/test_views.py` — clean.

**Next**: T034.

**Watch**: nothing.

---

## 2026-08-24T15:55:00+02:00 · Implementer US3 · T034

**Did**: Attached the identifiers row set to the attributes page — `fairdm/core/project/plugins.py`
`Attributes` now inherits `mvp.views.inline.InlinesMixin` (ahead of `FairDMUpdateView` in its MRO)
and declares `inlines = [ProjectIdentifierInline]` (imported from `fairdm/core/related_records.py`,
built in an earlier phase). Added `TestAttributesIdentifierRowSet.test_existing_identifiers_are_presented_one_row_each_with_no_blank_row_beyond_them`
to `test_views.py`, observed it fail for the right reason (`KeyError: 'inlines'`) before the wiring
landed.

Attaching the row set means every submission now needs the `identifiers` formset's management-form
data, which broke three tests that predate this: the pre-existing `test_project_update_success_redirects_to_detail`
(named explicitly by the brief for this task) and my own `test_changing_name_status_visibility_and_owner_each_persists`
/ `test_uploading_an_image_persists_it_and_clearing_it_removes_it` from T031/T032, authored this
story. Added a shared `_identifier_management_data()` helper and threaded it into all three.

**Verified**: `poetry run pytest tests/test_core/test_project -q` — 200 passed (whole package, no
regressions). `poetry run ruff check tests/test_core/test_project/test_views.py fairdm/core/project/plugins.py`
— clean (ruff also reordered two import blocks in files this task already touches).

**Next**: T035.

**Watch**: the same pattern repeats at T040 when the dates row set is attached — every submission
test will then need both formsets' management data.

---

## 2026-08-24T16:05:00+02:00 · Implementer US3 · T035-T039

**Did**: Added five tests to `TestAttributesIdentifierRowSet` in `test_views.py`, each posting to
the real attributes page URL: `test_adding_an_identifier_of_a_chosen_type_records_it_against_the_project`
(T035), `test_changing_an_existing_identifiers_value_persists` (T036, carries `identifiers-0-id`),
`test_removing_an_identifier_row_deletes_it_from_the_project` (T037, `identifiers-0-DELETE=on`),
`test_a_value_already_recorded_against_a_different_project_is_refused` (T038, asserts the error
lands on `value` and that the same submission's own name change is not saved either — the
atomic-transaction guarantee `InlinesMixin.form_valid` already provides), and
`test_the_same_value_submitted_twice_in_one_submission_reports_the_collision` (T039, relies on
`BaseModelFormSet.validate_unique()` against `value`'s `unique=True`, not custom code). All five
passed against the existing shared modules — no production code changed in this batch. Added a
`_project_field_data(project)` helper alongside `_identifier_management_data()` to cut the
per-test boilerplate.

**Verified**: `poetry run pytest tests/test_core/test_project -q` — 205 passed.
`poetry run ruff check tests/test_core/test_project/test_views.py` — clean.

**Next**: T040 — attach the dates row set, built from `related_records.ProjectDateInline` plus
the parameterised `formsets.date_ordering_formset` (`ProjectDate.START_TYPE`/`END_TYPE`), which
will need its own subclass declared in `plugins.py` (the ordering rule is page-specific
configuration, not something `related_records.py` itself declares — that file is out of this
story's scope per the brief's prohibitions).

**Watch**: attaching the second formset will again touch every existing submission test's POST
data, this time to add the `dates` prefix's management form too.

## 2026-08-24T16:25:00+02:00 · Implementer US3 · T040

**Did**: Wired the dates row set into the attributes page. Added `ProjectDatesInline(ProjectDateInline)`
to `fairdm/core/project/plugins.py`, pairing the shared declaration with `formsets.date_ordering_formset`
parameterised on `ProjectDate.START_TYPE`/`END_TYPE` and a message mirroring `ProjectDate.clean()`'s
own wording; declared in `plugins.py` rather than `related_records.py` since combining a shared
declaration with a shared rule is this page's own choice (see `decisions.md`). `Attributes.inlines`
now lists both `ProjectIdentifierInline` and `ProjectDatesInline`. Added
`TestAttributesDateRowSet.test_existing_dates_are_presented_one_row_each_with_no_blank_row_beyond_them`,
observed it fail (`KeyError: 'dates'`) before the wiring landed.

As with T034, attaching the second formset broke every existing submission test that didn't carry
`dates` management-form data — six tests across `TestProjectUpdateView` and
`TestAttributesIdentifierRowSet`. Added `_date_management_data()` next to `_identifier_management_data()`
and threaded it through all of them (including the two refusal-case tests, T038/T039, for
submission realism even though their assertions didn't strictly require it).

**Verified**: `poetry run pytest tests/test_core/test_project -q` — 206 passed.
`poetry run ruff check tests/test_core/test_project/test_views.py fairdm/core/project/plugins.py` — clean.

**Next**: T041.

**Watch**: nothing further — both row sets are now attached; no more formsets to add.

---

## 2026-08-24T16:40:00+02:00 · Implementer US3 · T041-T045

**Did**: Added five tests to `TestAttributesDateRowSet`: `test_adding_a_date_of_a_chosen_type_records_it_against_the_project`
(T041), `test_changing_an_existing_dates_value_persists` (T042), `test_removing_a_date_row_deletes_it_from_the_project`
(T043), two tests for T044 — `test_a_backwards_pair_both_newly_added_is_refused_and_saves_nothing`
(non_form_errors, the case the formset-level rule specifically exists for) and
`test_a_backwards_pair_with_the_start_already_stored_is_refused_and_saves_nothing` (caught instead
by the per-row `ProjectDate.clean()`, since the sibling is already in the database — asserted via
`is_valid() is False` rather than `non_form_errors()`, since the error lands on the row, not the
formset) — and `test_a_start_date_with_no_end_date_is_accepted` (T045). All passed against the
existing shared modules; no production code changed in this batch.

**Verified**: `poetry run pytest tests/test_core/test_project -q` — 211 passed.
`poetry run ruff check tests/test_core/test_project/test_views.py` — clean.

**Next**: T046.

**Watch**: nothing.

---

## 2026-08-24T16:50:00+02:00 · Implementer US3 · T046-T047

**Did**: Added `TestAttributesSaveIsOneAtomicSubmission` to `test_views.py` with
`test_an_invalid_identifier_row_blocks_the_projects_own_field_changes_too` (T046 — an identifier
row missing its required `value`, submitted with a valid name change, saves neither; a different
invalidity than T038's cross-project duplicate, to exercise the atomicity guarantee on its own
terms) and `test_a_successful_submission_redirects_to_the_projects_own_page` (T047). Both passed
against `InlinesMixin.form_valid`'s existing one-transaction save — no production code changed.

**Verified**: `poetry run pytest tests/test_core/test_project/test_views.py::TestAttributesSaveIsOneAtomicSubmission -q`
— 2 passed. `poetry run ruff check tests/test_core/test_project/test_views.py` — clean.

**Next**: T048.

**Watch**: nothing.

---

## 2026-08-24T17:00:00+02:00 · Implementer US3 · T048

**Did**: Deleted `ProjectDateForm` and `ProjectIdentifierForm` from `fairdm/core/project/forms.py`
and their own test classes (`TestProjectDateForm`, `TestProjectIdentifierForm`) from
`tests/test_core/test_project/test_forms.py`, per the brief's explicit exception to the
no-test-tampering rule. Re-confirmed by grep, before and after, that neither class had any other
caller in the tree (only their own module and their own tests referenced them).

**Verified**: `poetry run pytest tests/test_core/test_project -q` — 212 passed.
`poetry run ruff check fairdm/core/project/forms.py tests/test_core/test_project/test_forms.py` — clean.

**Next**: T049.

**Watch**: nothing.

---

## 2026-08-24T17:05:00+02:00 · Implementer US3 · T049

**Did**: Added `TestExactlyOnePageOffersTheProjectsOwnAttributes` to `test_plugins.py` —
walks every top-level registration against `Project` plus each one's `get_extra_views()`, and
asserts exactly one (`Attributes`) has a `form_class` whose `Meta.fields` overlaps
`{"image", "name", "status", "visibility", "owner"}`. Checked by field-set overlap rather than by
name, per `decisions.md`, so a `ProjectConfigure`-shaped page reintroduced under a different name
would still be caught. Passed on first run — no production code changed.

**Verified**: `poetry run pytest tests/test_core/test_project -q` — 213 passed.
`poetry run ruff check tests/test_core/test_project/test_plugins.py` — clean.

**Next**: T088.

**Watch**: nothing.

---

## 2026-08-24T17:10:00+02:00 · Implementer US3 · T088

**Did**: Removed the unreachable `funding = forms.JSONField(...)` declaration and the TODO
comment above `Meta.fields` from `ProjectForm` (`fairdm/core/project/forms.py`). No behavioural
change — `Meta.fields` already excluded `funding`, and T029/T030 already pin the form's exact
field set and its absence. No test of its own, per the brief.

**Verified**: `poetry run pytest tests/test_core/test_project -q` — 213 passed (unchanged count).
`poetry run ruff check fairdm/core/project/forms.py` — clean.

**Next**: story complete (T026, T028-T049, T088 all done). Full-suite verify and documentation
check at the completion report.

**Watch**: T027, T050 and T092/T093-adjacent US-5/US-6 work are other stories/tracks, already
excluded from this brief's task list — not touched here.

---

## 2026-08-24T18:10:00+02:00 · Implementer US4 · T051

**Did**: Registered `Descriptions` against `Project` in `fairdm/core/project/plugins.py` as a
top-level registration (not an extra view of `Overview`, unlike `Attributes`/`Delete` — matching
Dataset and Sample per plan P2), built on `MVPFormView` + `VocabularyDescriptionsForm`. Deleted
the unregistered, generic-formset `Descriptions`, `Keywords` and `KeyDates` classes it replaced
(the last two were dead — no caller, no registration). Reachable at
`project:descriptions` → `/projects/<uuid>/descriptions/`; an anonymous request redirects to
sign in.

**Verified**: `poetry run pytest tests/test_core/test_project/test_plugins.py -q` — 27 passed.
`poetry run ruff check fairdm/core/project/plugins.py tests/test_core/test_project/test_plugins.py`
— clean (ruff auto-removed one unused import from my own new test).

**Next**: T052.

**Watch**: nothing.

---

## 2026-08-24T18:15:00+02:00 · Implementer US4 · T052

**Did**: Added `TestDescriptionsPageStatesItsOwnPermission` asserting `can_open()` against
`project.change_project` — refuses a signed-in user without it and every anonymous request,
admits a holder. Passed immediately: the permission line was already in place as part of T051's
own anonymous-redirect requirement. No production change.

**Verified**: `poetry run pytest tests/test_core/test_project/test_plugins.py::TestDescriptionsPageStatesItsOwnPermission -q`
— 3 passed (narrowest scope; the full file was next re-run at T053 and stood at 32, consistent
with 27 + these 3 + T053's own 2). `poetry run ruff check` on both changed files — clean.

**Next**: T053.

**Watch**: nothing.

---

## 2026-08-24T18:20:00+02:00 · Implementer US4 · T053

**Did**: Added `TestDescriptionsPageOffersOneAreaPerVocabularyType`, asserting the rendered
form's field set matches `ProjectDescription.VOCABULARY.values` exactly and every area starts
empty for a project with none. This surfaced a real gap: `MVPFormView` (plain `FormView`, no
`SingleObjectMixin`) derives no template name of its own, so Django's base
`TemplateResponseMixin.get_template_names` raised `ImproperlyConfigured` before
`BaseTemplateNameMixin`'s `form_view.html` fallback was ever appended — unlike the model-backed
`Attributes` page, which resolves its template through `SingleObjectTemplateResponseMixin`
instead. Fixed by setting `template_name = "form_view.html"` explicitly on `Descriptions`.

**Verified**: `poetry run pytest tests/test_core/test_project/test_plugins.py -q` — 32 passed.
`poetry run ruff check` on both changed files — clean.

**Next**: T054.

**Watch**: nothing.

---

## 2026-08-24T18:25:00+02:00 · Implementer US4 · T054

**Did**: Added `TestDescriptionsPageAreasAreLabelledFromTheVocabulary`, asserting the first
area's label and help text equal the vocabulary concept's own `label()`/`definition()` through a
real page render. Passed immediately — `VocabularyDescriptionsForm` already sources both from
the concept (013 plan P2); this proves the page renders what it was handed. No production
change.

**Verified**: `poetry run pytest tests/test_core/test_project/test_plugins.py -q` — 33 passed.
`poetry run ruff check` — clean.

**Next**: T055.

**Watch**: nothing.

---

## 2026-08-24T18:30:00+02:00 · Implementer US4 · T055-T061

**Did**: Added one test class per acceptance scenario, each exercising the page end-to-end
through `client.get`/`client.post` rather than the form directly — all passed immediately
against the T051 implementation, since `form_valid()` already calls `form.save()` and
`get_success_url()` already returns `self.base_object.get_absolute_url()`:

- T055 `TestSavingTextIntoOneAreaRecordsOnlyThatType` — one POST creates exactly one row.
- T056 `TestExistingDescriptionsShowInTheirOwnArea` — an existing row's text appears only in its
  own area.
- T057 `TestEditingAnExistingDescriptionPersists` — a repeat POST with different text updates the
  stored row rather than duplicating it.
- T058 `TestClearingAnAreaRemovesTheDescription` — an empty resubmission deletes the row.
- T059 `TestEmptyAndWhitespaceOnlyAreasCreateNothing` — an unfilled area on a project with none
  creates nothing; a stored row cleared to whitespace-only is treated as empty and removed.
- T060 `TestRepeatSubmissionNeverDuplicatesAType` — three POSTs to the same area leave exactly
  one row, holding the last value (asserted on the count, not merely that the save succeeded).
- T061 `TestASuccessfulSubmissionRedirectsToTheProjectsPage` — the redirect target equals
  `reverse("project:overview", ...)` exactly, not a substring match.

No production code changed across these seven tasks.

**Verified**: `poetry run pytest tests/test_core/test_project/test_plugins.py -q` — 41 passed
after T061 (one commit per task; ruff clean at each).

**Next**: T062.

**Watch**: nothing.

---

## 2026-08-24T18:45:00+02:00 · Implementer US4 · T062

**Did**: Deleted `ProjectDescriptionForm` from `fairdm/core/project/forms.py` (used by no
running code once T051 replaced its caller) and its test class `TestProjectDescriptionForm` from
`test_forms.py`, plus the now-unused `ValidationError` import. Re-confirmed by grep, before and
after, that the form had no other caller in the tree. `decisions.md` records the coverage that
replaces the deleted uniqueness test — spread across T055/T057/T060 rather than concentrated in
one form-level test.

**Verified**: `poetry run pytest tests/test_core/test_project -q` — 228 passed.
`poetry run ruff check fairdm/core/project/forms.py tests/test_core/test_project/test_forms.py`
— clean.

**Next**: story complete (T051-T062 all done). Full-suite verify at the completion report.

**Watch**: checked `docs/` for pages describing `ProjectDescriptionForm`, the retired
`Descriptions`/`Keywords`/`KeyDates` plugin classes, or the new `project:descriptions` route —
found none. `docs/user-guide/project/descriptions.md` is an unrelated stub ("Coming soon...").
`docs/portal-administration/managing_projects.md` describes the Django admin's own inline
formset editing for `ProjectDescription`, a different surface this story does not touch.

---

## 2026-08-24T16:45:00+02:00 · Implementer US6 · T078

**Did**: Added `test_project_delete_confirmation_ignores_surrounding_whitespace`, POSTing
`"  Spaced Project  "` against a project named `"Spaced Project"`. Passed immediately — the
shared `DeleteConfirmForm.clean_confirmation()` (`mvp/forms.py`) already strips the submitted
value with `.strip()` before comparing it to `get_confirmation_value()`, and
`Delete.get_confirmation_value()` already returns the unstripped project name, so a padded
match already succeeds. No production change; this pins FR-037 as a regression test.

**Verified**: `poetry run pytest tests/test_core/test_project/test_views.py::TestProjectDeleteView::test_project_delete_confirmation_ignores_surrounding_whitespace -q`
— 1 passed. `poetry run ruff check tests/test_core/test_project/test_views.py` — clean.

**Next**: T083.

**Watch**: nothing.

---

## 2026-08-24T16:55:00+02:00 · Implementer US6 · T083

**Did**: Rewrote `test_project_delete_blocks_public_datasets` in place to assert the blocking
dataset's name appears in the rendered response, instead of asserting the invented
`protected_datasets` context key (the one prohibitions-listed exception; recorded in
`decisions.md`). Ran it first against the unchanged view to confirm RED for the right reason —
the confirmation form and Delete button rendered, since nothing populated `is_protected`. Added
`Delete.get_context_data()` in `fairdm/core/project/plugins.py`, querying the project's public
datasets fresh on every call and setting the shell's own `is_protected`/`protected_objects`
context keys (plan P4) — after `super().get_context_data()`, not through keyword arguments, which
the shell's own assignment would overwrite. Simplified `form_valid()`'s except branch to call
`get_context_data()` with no extra kwargs, since it now derives the refusal itself rather than
being handed `e.datasets`.

**Verified**: `poetry run pytest tests/test_core/test_project/test_views.py::TestProjectDeleteView -q`
— 8 passed. `poetry run ruff check fairdm/core/project/plugins.py tests/test_core/test_project/test_views.py`
— clean.

**Next**: T084.

**Watch**: nothing.

---

## 2026-08-24T17:05:00+02:00 · Implementer US6 · T084

**Did**: Added `test_project_delete_refused_page_hides_confirmation_and_delete_control`,
asserting the refused page contains the explanation and neither `id="id_confirmation"` nor
`id="delete-submit-btn"`. Ran RED first: the custom type-to-confirm UI and Delete button were
already correctly withheld by `delete_view.html`'s `is_protected` branch, but a *second*,
duplicate confirmation input was still rendered — `cotton/form/index.html` renders the raw
Django form via `{% if form_obj %}<c-form.render :form="form_obj" />{% endif %}` unconditionally
whenever a `form` is present in context, regardless of `is_protected`. This is a shell rendering
gap the `is_protected`/`protected_objects` contract has no way to express, not something this
story introduced. Fixed by setting `context["form"] = None` in `Delete.get_context_data()` when
protected — confined to this page's own context, not a shell change, and it doesn't touch
`post()`'s or `form_valid()`'s own local `form` used for actual validation.

**Verified**: `poetry run pytest tests/test_core/test_project/test_views.py::TestProjectDeleteView -q`
— 9 passed. `poetry run ruff check fairdm/core/project/plugins.py tests/test_core/test_project/test_views.py`
— clean.

**Next**: T085.

**Watch**: nothing.

---

## 2026-08-24T17:10:00+02:00 · Implementer US6 · T085

**Did**: Added `test_project_delete_get_shows_refusal_without_submitting`, opening the deletion
page with a GET request against a project with a public dataset and asserting the refusal and
dataset name are already present, with no confirmation field. Passed immediately —
`Delete.get_context_data()` (T083) runs on every render, GET included, since Django's
`DeleteView.get()` calls it the same way `post()`'s refusal path does. No production change; this
pins FR-038's "evaluate on GET too" requirement as its own regression test.

**Verified**: `poetry run pytest tests/test_core/test_project/test_views.py::TestProjectDeleteView -q`
— 10 passed. `poetry run ruff check tests/test_core/test_project/test_views.py` — clean.

**Next**: T086.

**Watch**: nothing.

---

## 2026-08-24T17:15:00+02:00 · Implementer US6 · T086

**Did**: Added `test_project_delete_evaluates_visibility_at_submission_time`: opens the deletion
page while the project's one dataset is private (GET shows no refusal), makes the dataset public,
then posts the correct confirmation and asserts the refusal fires and names the newly-public
dataset. Passed immediately — `get_context_data()` queries `self.base_object.datasets.filter(...)`
fresh on every call rather than caching anything from the GET, and the `pre_delete` signal
(`fairdm/core/project/models.py`) independently re-queries at `.delete()` time, so both the
context shown after a refused submission and the enforcement itself are evaluated at submission,
not captured when the page was drawn. No production change; this pins the spec's edge case as a
regression test.

**Verified**: `poetry run pytest tests/test_core/test_project/test_views.py::TestProjectDeleteView -q`
— 11 passed. `poetry run ruff check tests/test_core/test_project/test_views.py` — clean.

**Next**: T089.

**Watch**: nothing.
