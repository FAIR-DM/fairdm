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
