# Progress — 006-core-measurements, Group 0

## 2026-08-19T10:00:00Z · Implementer US10 · T001

Did: Added `MeasurementIdentifierFactory` (never existed) and fixed the invalid vocabulary
defaults on `MeasurementDescriptionFactory` (`"Abstract"` → `"MeasurementConditions"`) and
`MeasurementDateFactory` (`"Created"` → `"Setup"`) in `fairdm/factories/core.py`. All three now
default to a real member of their own vocabulary.

Verified: `poetry run pytest tests/test_core/test_measurement/test_factories.py -q -p no:randomly`
→ 6 passed. `poetry run ruff check fairdm/factories/core.py
tests/test_core/test_measurement/test_factories.py` → all checks passed.

Next: T002 — make `MeasurementFactory` abstract.

Watch: none.

## 2026-08-19T10:10:00Z · Implementer US10 · T002

Did: Set `abstract = True` on `MeasurementFactory.Meta` in `fairdm/factories/core.py`, mirroring
`SampleFactory`'s shape, and rewrote its docstring (and the module docstring's factory list) to
describe it as the abstract base with concrete subclasses living in `fairdm_demo.factories`.

Verified: `poetry run pytest tests/test_core/test_measurement/test_factories.py -q -p no:randomly`
→ 7 passed. `poetry run ruff check fairdm/factories/core.py
tests/test_core/test_measurement/test_factories.py` → all checks passed.

Next: T003 — concrete demo measurement factories.

Watch: making `MeasurementFactory` abstract breaks every direct call site elsewhere in the suite
until each is retargeted. T006 retargets every call site within
`tests/test_core/test_measurement/*.py` (this story's scope); call sites in other test
directories (`tests/test_factories/test_core.py`, `tests/test_factories/test_contributors.py`,
`tests/test_core/test_dataset/test_models.py`, `tests/test_registry/conftest.py`) are outside this
story's file scope and are expected to fail until a follow-up retargets them too - see the
completion report's `concerns`.

## 2026-08-19T10:20:00Z · Implementer US10 · T003

Did: Added `XRFMeasurementFactory` and `ICP_MS_MeasurementFactory` to `fairdm_demo/factories.py`,
each supplying its model's required (non-null) fields — `element`/`concentration_ppm` for XRF,
`isotope`/`counts_per_second` for ICP-MS. `ExampleMeasurementFactory` already existed and needed
no change (all its fields are optional).

Verified: `poetry run pytest tests/test_core/test_measurement/test_factories.py -q -p no:randomly`
→ 10 passed. `poetry run ruff check fairdm_demo/factories.py
tests/test_core/test_measurement/test_factories.py` → all checks passed.

Next: T004 — export the metadata factories from `fairdm.factories`.

Watch: none.

## 2026-08-19T10:30:00Z · Implementer US10 · T004

Did: Exported `MeasurementDescriptionFactory`, `MeasurementDateFactory` and
`MeasurementIdentifierFactory` from `fairdm/factories/__init__.py` (import + `__all__`), alongside
the already-exported `MeasurementFactory`. Updated the module docstring's factory list to match.

Verified: `poetry run pytest tests/test_core/test_measurement/test_factories.py -q -p no:randomly`
→ 12 passed. `poetry run ruff check fairdm/factories/__init__.py
tests/test_core/test_measurement/test_factories.py` → all checks passed.

Next: T005 — shared fixtures.

Watch: none.

## 2026-08-19T10:40:00Z · Implementer US10 · T005

Did: In `tests/test_core/test_measurement/conftest.py`: retargeted the `measurement` fixture onto
`ExampleMeasurementFactory` (it previously called the now-abstract `MeasurementFactory` directly);
added `second_dataset` and `second_sample` fixtures for cross-dataset cases; added `user_no_rights`
for a user holding no permissions.

Verified: `poetry run pytest tests/test_core/test_measurement/test_factories.py -q -p no:randomly`
→ 15 passed. `poetry run ruff check tests/test_core/test_measurement/conftest.py
tests/test_core/test_measurement/test_factories.py` → all checks passed.

Next: T006 — retarget every remaining measurement call site in the suite.

Watch: at this point, running the full `tests/test_core/test_measurement` directory shows 41
pre-existing failures in `test_admin.py`, `test_models.py` and `test_permissions.py` — all of them
direct `MeasurementFactory(...)` call sites now hitting the T002 abstract guard. That is exactly
T006's job, next.

## 2026-08-19T11:00:00Z · Implementer US10 · T006

Did: Retargeted every direct `MeasurementFactory(...)` / `MeasurementFactory.create(...)` call site
in `tests/test_core/test_measurement/test_admin.py`, `test_models.py` and `test_permissions.py`
onto `ExampleMeasurementFactory`, adding `sample=RockSampleFactory()` wherever the original call
had none (it never had a default). One assertion in `test_models.py`
(`TestMeasurementQuerySetOptimization::test_polymorphic_queries_return_correct_typed_instances`)
tested that bare `Measurement` instances existed in the DB (`type(m) is Measurement`) - the exact
thing this story exists to eliminate - and was rewritten to check for `ExampleMeasurement`
instances instead. See the completion report for every individual call-site change.

Verified: `poetry run pytest tests/test_core/test_measurement -q -p no:randomly` → 130 passed, 17
skipped. `poetry run ruff check tests/test_core/test_measurement/test_admin.py
tests/test_core/test_measurement/test_models.py tests/test_core/test_measurement/test_permissions.py`
→ all checks passed.

Next: story complete; run the full repo suite once for the completion report.

Watch: the full repo suite (`tests/`) is expected to still show failures in
`tests/test_factories/test_core.py`, `tests/test_factories/test_contributors.py`,
`tests/test_core/test_dataset/test_models.py` and `tests/test_registry/conftest.py` - all outside
this story's declared file scope, all direct `MeasurementFactory(...)` call sites that this story
was not permitted to touch. Reported as a concern in the completion report for Forge to reconcile
(a follow-up task/group, or a scope amendment).

## 2026-08-19T12:30:00Z · Implementer US10 · T006 (scope widened)

Did: Forge confirmed the scope-gap concern was its own error in the brief - the prohibition list
named only `tests/test_core/test_measurement/*.py`, but T006 itself says "retarget every
measurement call site in the suite", and the wider instruction governs. Scope widened to also
permit `tests/test_factories/test_core.py`, `tests/test_factories/test_contributors.py` and
`tests/test_core/test_dataset/test_models.py`. Retargeted every remaining direct
`MeasurementFactory(...)` call site in those three files onto `ExampleMeasurementFactory`.
`tests/test_registry/conftest.py`'s `ConcreteMeasurementFactory` is a separate, unrelated factory
and was never affected.

Two vocabulary-default assertions in `tests/test_factories/test_core.py` were corrected to match
T001's fix (`measurement_desc.type` `"Abstract"` → `"MeasurementConditions"`;
`measurement_date.type` `"Created"` → `"Setup"`). Three tests were asserting a claim FR-011 now
forbids - "MeasurementFactory creates/builds a valid instance" - and were rewritten, not merely
retargeted, per Forge's explicit instruction:
`TestMeasurementFactories.test_measurement_factory_creates_measurement` (renamed
`..._is_abstract_and_its_concrete_subclass_creates_measurement`),
`TestBasicFactoryFunctionality.test_all_factories_can_create_instances` and
`test_all_factories_can_build_instances`. Each now asserts `MeasurementFactory(...)` /
`.build()` raises `factory.errors.FactoryError` before exercising the concrete/usable factories.

Left `test_measurement_description_factory` and `test_measurement_date_factory`'s explicit
`type="Abstract"` / `type="Created"` keyword arguments unchanged - those pass an explicit type
rather than relying on the factory default, so they are testing "the factory stores whatever type
it is given" (still true; Django does not validate `choices` on save), not a default. Flagged as a
concern rather than fixed, since fixing it is not required for green and is not what T006 asks for.

Verified: `poetry run pytest tests/test_core/test_dataset/test_models.py -q -p no:randomly` → 136
passed. `poetry run pytest tests/test_factories/test_contributors.py -q -p no:randomly` → 18
passed. `poetry run pytest tests/test_factories/test_core.py -q -p no:randomly` → 56 passed.
`poetry run pytest tests/test_factories tests/test_core/test_dataset tests/test_core/test_measurement -q -p no:randomly`
→ 440 passed, 22 skipped. `poetry run ruff check` on every touched file → all checks passed.

Next: run the full repo suite once more for the follow-up completion report.

Watch: none outstanding.

## 2026-08-19T12:14:00Z · Implementer US10 · T007

Did: Added `TestMeasurementModelCreation.test_uuid_is_not_editable_afterwards`, mirroring
`TestSampleIdentity.test_uuid_is_not_editable_afterwards` on the sample side - asserts `uuid` is
excluded from `MeasurementForm.base_fields` and present in `MeasurementChildAdmin.readonly_fields`.
No production change: the mechanism (`editable=False`) already exists from T008.

Verified: `poetry run pytest tests/test_core/test_measurement/test_models.py::TestMeasurementModelCreation -q -p no:randomly`
→ 4 passed.

Next: T009.

Watch: none.

## 2026-08-19T12:16:00Z · Implementer US10 · T009

Did: Added `TestMeasurementFields` with `test_name_is_required` (asserts `full_clean()` raises with
`"name"` in `message_dict` for a bare `ExampleMeasurement`) and
`test_label_image_keywords_and_tags_are_all_optional` (asserts `local_id`, `image`, `keywords` and
`tags` are all unset/empty and `full_clean()` does not raise). No production change - all fields
were already optional except `name`.

Verified: `poetry run pytest tests/test_core/test_measurement/test_models.py::TestMeasurementFields -q -p no:randomly`
→ 2 passed.

Next: T010.

Watch: none.

## 2026-08-19T12:18:00Z · Implementer US10 · T010

Did: Added `TestMeasurementFieldMetadata.test_field_verbose_names_and_help_text_are_lazy`,
iterating `["dataset", "sample", "local_id"]` and asserting `verbose_name`/`help_text` are
`django.utils.functional.Promise` instances. `uuid` is excluded, matching the sibling Sample
record's `TestSampleTranslatable` - its `verbose_name="UUID"` is a plain string there too, not
wrapped in `_()`. No production change: all three fields already declare lazy translations.

Verified: `poetry run pytest tests/test_core/test_measurement/test_models.py::TestMeasurementFieldMetadata -q -p no:randomly`
→ 1 passed.

Next: T011.

Watch: none.

## 2026-08-19T12:20:00Z · Implementer US10 · T011

Did: Added `TestMeasurementLocalId.test_the_same_local_id_is_valid_in_two_different_datasets`,
creating two measurements with the same `local_id` in two different datasets and asserting both
`full_clean()` without raising. No production change: no uniqueness constraint was ever declared.

Verified: `poetry run pytest tests/test_core/test_measurement/test_models.py::TestMeasurementLocalId -q -p no:randomly`
→ 1 passed.

Next: T012.

Watch: none.

## 2026-08-19T12:24:00Z · Implementer US10 · T012

Did: Added `test_local_id_has_no_uniqueness_constraint` and `test_local_id_is_indexed` to
`TestMeasurementLocalId`. The index assertion failed red first (`field.db_index is False`).
Added `db_index=True` to `Measurement.local_id` in `fairdm/core/measurement/models.py` (plan.md's
"Data model" section records this as the story's one migration). Generated the migration with
`poetry run python manage.py makemigrations measurement` (scoped to the one app deliberately - see
Watch below) - `fairdm/core/measurement/migrations/0010_alter_measurement_local_id.py`.

Verified: `poetry run pytest tests/test_core/test_measurement/test_models.py::TestMeasurementLocalId -q -p no:randomly`
→ 3 passed (red-then-green observed on `test_local_id_is_indexed`).

Next: T013/T014.

Watch: running unscoped `makemigrations` (no app argument) also generated
`fairdm/contrib/identity/migrations/0004_alter_authoritytranslation_unique_together_and_more.py`.
Confirmed by stashing every change from this session and re-running `makemigrations --check
--dry-run` against a clean `006-cluster-a` tree (at the T011 commit): the `identity` app drift is
already present with none of my edits applied, so it predates this story and is unrelated to it.
Did not generate or commit that migration - out of scope, `identity` isn't named anywhere in the
brief. Flagged in the completion report's `concerns` for Forge to reconcile. (An unscoped run also
wrote a stray migration into the *installed* `orbit` package under site-packages, outside this git
worktree entirely; left alone, it is untracked and has no effect on this repo.)

## 2026-08-19T12:30:00Z · Implementer US10 · T013/T014

Did: Deleted the vacuous `TestMeasurementCascadeBehavior.test_deleting_dataset_cascades_to_measurements`
(it deleted the measurement before the dataset, so its assertion held whatever `on_delete` said -
named explicitly in the brief as a trap). Updated the class docstring to say so and to point at the
sound replacement, `TestMeasurementCRUDWorkflow.test_deleting_dataset_cascades_to_measurements`
(deletes the dataset while the measurement still exists), which was already correct and is
untouched. This is the one pre-existing test this story was told to delete by name - no other
existing test was modified or removed.

Verified: `poetry run pytest tests/test_core/test_measurement/test_models.py::TestMeasurementCascadeBehavior tests/test_core/test_measurement/test_models.py::TestMeasurementCRUDWorkflow -q -p no:randomly`
→ 7 passed.

Next: T017.

Watch: none.

## 2026-08-19T12:33:00Z · Implementer US10 · T017

Did: Added `TestMeasurementTimestamps` with `test_creation_and_modification_times_are_recorded`
and `test_modification_time_advances_on_change` (asserts `modified` moves forward and `added`
stays exactly equal after a save). No production change: both timestamps already come from
`fairdm/core/abstract.py` (T018).

Verified: `poetry run pytest tests/test_core/test_measurement/test_models.py::TestMeasurementTimestamps -q -p no:randomly`
→ 2 passed.

Next: T019/T020.

Watch: none.

## 2026-08-19T12:36:00Z · Implementer US10 · T019/T020

Did: Added `TestMeasurementContributions` with `test_measurement_role_vocabulary_members`
(asserts `Measurement.CONTRIBUTOR_ROLES.values == ["MeasurementPreparation",
"MeasurementCollection", "Support"]`, named one by one per the brief's established facts) and
`test_contribution_records_contributor_and_roles` (adds a contributor under two of those roles via
`add_contributor` and reads both back). No production change: `CONTRIBUTOR_ROLES` and the
`contributors` generic relation already existed.

Verified: `poetry run pytest tests/test_core/test_measurement/test_models.py::TestMeasurementContributions -q -p no:randomly`
→ 2 passed. Full-file check: `poetry run pytest tests/test_core/test_measurement/test_models.py -q -p no:randomly`
→ 68 passed, 3 skipped.

Next: T114.

Watch: none.

## 2026-08-19T12:45:00Z · Implementer US10 · T114 (blocked)

Did: Investigated rather than edited. The existing
`TestMeasurementViews.test_measurement_detail_view_accessible` wraps `client.get(reverse(
"measurement:overview", ...))` in a bare `try/except Exception: pytest.skip(...)`, and it is
skipping now. Requested the same address directly (no try/except): it raises
`django.template.exceptions.TemplateDoesNotExist: cotton/pst/components/section/index.html` while
rendering `fairdm/core/measurement/templates/measurement/detail.html`, the template
`MeasurementDetailView` (`fairdm/core/measurement/views.py`) renders - that view's own docstring
already calls it a placeholder.

Checked the sample equivalent per the brief's instruction, to test the "environment is missing the
whole `cotton/pst` namespace" hypothesis: requesting `reverse("sample:overview", ...)` directly
returns a clean 200. That falsifies the hypothesis - the namespace is not uniformly absent. The
reason sample's live route survives is that `sample:overview` is served through the registry's
plugin system (`sample/plugins/overview.html` extending `plugins/overview.html`), which never
references `c-pst`; `fairdm/core/sample/templates/sample/sample_detail.html` also uses
`c-pst.components.section` but is dead code - no URL renders it. `measurement/detail.html` is the
one live template using the component, so it is the one route that breaks. A filesystem search
across every installed package (`site-packages`) found no `pst` template directory anywhere, so
this is a genuine missing component, not a version/config mismatch specific to this checkout.

Setting `client.raise_request_exception = False` turns the exception into a deterministic
`response.status_code == 500`, but asserting `== 500` as the expected outcome would encode a known
defect as the specification, which is a weakened/special-cased assertion the brief and craft-tdd
both forbid. Per the brief's explicit instruction ("If you cannot get a clean status, report the
task blocked... Do not paper over it with another skip"), T114 is reported blocked rather than
completed. The pre-existing skip-wrapped test was left untouched - T114 names it to replace, but
only in service of a working replacement, which this defect prevents.

Verified (diagnostic only, not committed): ad hoc scratch tests confirming the above were written
to and removed from `tests/test_core/test_measurement/test_zzz_check.py`; none of that survives in
the tree.

Next: none - T114 is the last of this story's tasks bar the final full-suite run.

Watch: `fairdm/core/measurement/templates/measurement/detail.html`'s use of
`c-pst.components.section` needs a real fix (or `MeasurementDetailView` needs to route through the
same plugin-based template chain `sample:overview` already uses) before the measurement detail
page is reachable at all. Out of scope for this test-writing task and touches shared
cotton-component/template territory this story doesn't own.
