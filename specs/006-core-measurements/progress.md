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

## 2026-08-19T12:12:16Z · Implementer US1 · T030/T034

Did: `BaseMeasurementConfiguration` declared fixed `form_fields`/`table_fields`/`filterset_fields`,
which meant `ModelConfiguration.resolve_fields()` never fell back to a registered type's own
`fields` list for those three components - `XRFMeasurementConfig`'s own fields (`element`,
`concentration_ppm`, ...) never reached the generated form, table or filterset, only the fields
every measurement has. Confirmed by direct probe against the running registry before writing a
test. Added `BaseMeasurementConfiguration.resolve_fields()`, appending the type's own fields for
`form`/`table`/`filterset` only - `admin`'s generated `list_display` already drew from `fields`
directly (no `admin_list_display` override on the base config) and already carried a type's own
fields, confirmed by the same probe, so it is untouched. Strengthened
`tests/test_core/test_measurement/test_config.py`'s four `test_auto_generated_*_includes_*`
tests with new sibling tests asserting a named own field (`element`/`concentration_ppm`) is
present on each generated form/table/filterset/admin (T030), and replaced T034's
`hasattr(config, "table_fields")`-style checks with assertions that `"name"`/`"sample"`/`"dataset"`
are literally present in `config.table_fields`/`form_fields`/`filterset_fields`.

Verified: confirmed RED first by `git stash push` on the `config.py` fix alone and running
`poetry run pytest tests/test_core/test_measurement/test_config.py -q -p no:randomly -k
own_fields` → 3 failed for the right reason (form/filterset/table missing `element`), 1 passed
(admin, already correct). Restored the fix (`git stash pop`) and reran
`poetry run pytest tests/test_core/test_measurement/test_config.py -q -p no:randomly` → 16 passed.
`poetry run ruff check` + `ruff format --check` on both touched files → clean.

Next: T025/T026/T028/T029 (the bare-measurement refusal routes) and T032/T033 (admin type
selection reads the registry).

Watch: `fairdm/core/measurement/config.py` and its test file are not in this story's prohibited
list, so this was in scope; flagging here in case another concurrent story also touches
`BaseMeasurementConfiguration`.

## 2026-08-19T12:15:20Z · Implementer US1 · T036/T037/T038

Did: the audit's largest finding for this story - two administrative base classes existed for
measurement types, and the registry enforced the wrong one. `fairdm/core/measurement/admin.py`
defines `MeasurementChildAdmin` (176 lines: inlines, fieldsets, autocomplete, readonly fields) and
is what `fairdm.core.measurement.admin.MeasurementParentAdmin` (the class actually registered with
`admin.site` - confirmed via `admin.site._registry[Measurement]` before touching anything) already
uses. `fairdm/core/admin.py` carried a two-line `MeasurementAdmin` stub and a second,
never-registered `MeasurementParentAdmin` (its `@admin.register` commented out) built from
`get_subclasses()` rather than the registry. Both registry references pointed at the two-line stub:
validation (`fairdm/registry/config.py:377`, aliasing the stub in as `MeasurementChildAdmin`) and
generation (`fairdm/registry/factories.py:803`). A portal supplying `MeasurementChildAdmin` - the
class the docstring and both doc pages actually tell a developer to inherit - was refused, with a
message naming the two-line stub instead.

T036 (test-first): rewrote `tests/test_registry/test_config.py::TestAdminInheritanceValidation`'s
three Measurement-admin tests. `test_measurement_with_correct_admin_class_passes` and
`test_autogenerated_measurement_admin_inherits_from_child_admin` imported the stub under the real
class's name (`from fairdm.core.admin import MeasurementAdmin as MeasurementChildAdmin`), so both
asserted against the wrong class by construction and passed whether or not the registry checked
against the configured base; now both import `MeasurementChildAdmin` from
`fairdm.core.measurement.admin` under its own name.
`test_measurement_with_wrong_admin_class_raises_error`'s message assertion now expects
"MeasurementChildAdmin". Ran alone first and confirmed 3 failures for the right reason (old
config.py still checked/named the stub) before touching implementation.

T037: `fairdm/registry/config.py::ModelConfiguration._validate_admin_inheritance` now imports
`MeasurementChildAdmin` from `fairdm.core.measurement.admin` and the refusal message names
`MeasurementChildAdmin`, not `MeasurementAdmin`.

T038: `fairdm/registry/factories.py::PolymorphicAdminMixin._get_admin_base_class` (the branch that
generates an admin for a type supplying none) now imports and returns
`fairdm.core.measurement.admin.MeasurementChildAdmin`, matching the Sample branch immediately above
it, which already used `SampleChildAdmin` correctly - this was the asymmetry the audit named.
Checked every importer of the two `fairdm/core/admin.py` classes first
(`grep -rn "MeasurementAdmin\b"` across the tree): only the two registry references above and
`tests/registry_models/admin.py` (a test-support admin module, not one of this story's prohibited
test files) imported the stub, to build `ConcreteMeasurementAdmin` for the registry test suite's
own concrete type - repointed to `fairdm.core.measurement.admin.MeasurementChildAdmin`. Deleted
`MeasurementAdmin` and the commented-out `MeasurementParentAdmin` from `fairdm/core/admin.py`,
along with the imports (`PolymorphicChildModelAdmin`, `PolymorphicChildModelFilter`,
`PolymorphicParentModelAdmin`, `Measurement`, `get_subclasses`) that only they used -
`DescriptionInline`/`DateInline` (dataset-related, pre-existing, out of this story's scope) are the
only classes left in that file and needed none of them.

Verified: `poetry run pytest tests/test_registry/test_config.py::TestAdminInheritanceValidation -q
-p no:randomly` → 3 failed for the right reason before T037, 8 passed after T037+T038.
`poetry run pytest tests/test_registry/ tests/test_core/test_measurement/test_config.py
tests/test_core/test_sample -q -p no:randomly` → 513 passed, 7 skipped.
`poetry run pytest tests/test_core/test_measurement -q -p no:randomly` → 134 passed, 17 skipped
(unchanged skip count from the story's baseline run). `poetry run ruff check` +
`ruff format --check` on every touched file → clean. `grep -rn "from fairdm.core.admin import"`
across the tree → no remaining importers of the deleted names.

Next: T025/T026/T028/T029 (the bare-measurement refusal routes) and T032/T033 (admin type
selection reads the registry).

Watch: none outstanding. `DescriptionInline`/`DateInline` in `fairdm/core/admin.py` are themselves
unreferenced outside that file (confirmed by grep) but are dataset-related and outside this
story's scope - left untouched and not raised as a concern, since a plain unused-class question
for a different domain isn't this story's finding to make.

## 2026-08-19T12:18:16Z · Implementer US1 · T025/T032/T033

Did: added `tests/test_core/test_measurement/test_admin_registry.py` rather than extending
`tests/test_core/test_measurement/test_admin.py` - that file is on this story's prohibited list
(owned by a concurrently running story) even though T025 and T032 name it in `tasks.md`. A new
file carries zero merge-conflict risk with whatever that other story lands there, which is the
concern the prohibition protects against.

T033: `MeasurementParentAdmin.get_child_models()` already reads `registry.measurements`
(`fairdm/core/measurement/admin.py:172-176`) - confirmed by monkeypatching the registry property
to a sentinel list and observing the admin's child models change to match it, which the existing
`assert len(child_models) > 0` coverage could not distinguish from a hardcoded non-empty list. No
implementation change.

T032: registered `tests.registry_models.models.ConcreteMeasurement` (a real, installed-app type,
"the shape a portal actually registers" per its own docstring) via `registry.register()` inside
the test, standing in for a type registered from outside the framework. Asserted it appears among
`get_child_models()`, that a registered `ConcreteSample` (non-measurement) does not, and that the
unregistered base `Measurement` does not. `tests/test_core/test_measurement/conftest.py`'s local
`clean_registry` fixture only snapshots/restores `registry._registry` around the test rather than
clearing it first (unlike `tests/test_registry/conftest.py`'s fixture of the same name, which
empties it) - written the assertions to work with either registry state (framework types stay
registered during the test) rather than assuming an empty registry.

T025: the administrative-interface route was already refused - `Measurement` is never in
`registry.measurements`, so the parent admin's add view 403s on the base content type the same
way it would for any unregistered model. No implementation change; this route was untested.

Verified: `poetry run pytest tests/test_core/test_measurement/test_admin_registry.py -q -p
no:randomly` → 6 passed. `poetry run ruff check` + `ruff format` (one file needed reformatting,
applied and reconfirmed clean) on the new file.

Next: T026/T028/T029 (the bare-measurement manager and form refusal routes).

Watch: none outstanding.

## 2026-08-19T12:20:49Z · Implementer US1 · T026/T028

Did: closed the manager route around the base-Measurement refusal. `Measurement.objects.create()`
produced a bare record, because `clean()` (`models.py:111`) only runs when something calls it or
`full_clean()` - forms and the admin do, the manager and a bare `.save()` do not.

The natural home for this guard is `models.py`/`managers.py` (the working pattern already landed
for `Sample`: `fairdm/core/sample/models.py`'s `block_base_sample_creation`, a `pre_save` receiver
declared right beside `Sample.clean()`), but both files are on this story's prohibited list (owned
by a concurrently running story). Added the equivalent guard,
`block_base_measurement_creation`, to `fairdm/core/measurement/apps.py` instead, connected via
`AppConfig.ready()` with `sender=Measurement` - the one mechanism that also covers Django fixture
deserialization (`django.core.serializers` sends `pre_save` on every raw object before saving it),
and is scoped so a registered subclass's own save is untouched (a subclass instance sends its own
class on save, never `Measurement`). The message text mirrors `Measurement.clean()`'s exactly;
declared as a new module-level constant in `apps.py` rather than imported from `models.py`, for the
same file-scope reason.

New file `tests/test_core/test_measurement/test_managers.py` (mirrors `managers.py`; `test_models.py`
is prohibited) proves three routes: `Measurement.objects.create()`, a bare `Measurement().save()`,
and deserializing a raw fixture row for the base model (T026's "no fixture in the framework creates
one", read as Django fixture loading rather than a pytest fixture, matching the Sample precedent's
`test_fixture_loading_refuses_a_bare_sample`).

Verified: confirmed RED for the right reason before implementing - `poetry run pytest
tests/test_core/test_measurement/test_managers.py -q -p no:randomly` → first two tests "DID NOT
RAISE ValidationError" (the bug), third hit an unrelated `IntegrityError: NOT NULL constraint
failed: measurement_measurement.added` (the fixture-loading route skips `auto_now_add`, and would
never be reached once the guard fires before the INSERT). After the `apps.py` change: same command
→ 3 passed. `poetry run pytest tests/test_core/test_measurement tests/test_registry
tests/test_factories -q -p no:randomly` → 458 passed, 17 skipped, no regressions from a
framework-wide `pre_save` receiver. `poetry run ruff check` + `ruff format` (one auto-fix, an
f-string for a percent-format lint) on both touched files → clean.

Next: T029 (the form's refusal message).

Watch: the natural, single-file location for this guard is `fairdm/core/measurement/models.py`,
alongside `Measurement.clean()` (the exact shape already used for `Sample`). If the story owning
`models.py` lands its own change there before this merges, Forge's convergence pass may want to
fold `apps.py`'s guard into `models.py` to match the Sample precedent - flagging so it isn't
mistaken for a second, competing mechanism.

## 2026-08-19T12:22:22Z · Implementer US1 · T029

Did: `test_form_prevents_base_measurement_instantiation`
(`tests/test_core/test_measurement/test_forms.py`) only asserted `not form.is_valid()`. Probed the
actual `form.errors` first: the test's dataset is deliberately private and the form is built with
no `request`, so `MeasurementFormMixin`'s dataset-choice scoping alone puts a `"dataset"` error on
the form independently of the base-Measurement refusal - the old assertion passed whether or not
the refusal fired at all. The probe also confirmed the refusal message
("Cannot create base Measurement instances directly...") appears twice in `form.errors["__all__"]`,
once from `MeasurementForm.clean()` and once from the model's own `clean()` via `_post_clean()` -
exactly the duplicate rendering `tasks.md` names. Rewrote the test to assert the message
("subclass"/"directly") is present in `__all__`, alongside the existing `is_valid()` check.

Deviation from `tasks.md`'s T029 text: did not delete `MeasurementForm.clean()`. That edit is in
`fairdm/core/measurement/forms.py`, which is on this story's prohibited list (owned by a
concurrently running story). Only the test-side fix (asserting on the message) is in this story's
scope per the brief's acceptance criterion, which is scoped to the test's assertion and does not
itself require the form-side cleanup. The duplicate `__all__` entry remains; noted as a concern
for whichever story owns `forms.py`.

Verified: `poetry run pytest tests/test_core/test_measurement/test_forms.py -q -p no:randomly` →
11 passed. `poetry run ruff check` + `ruff format --check` on the touched file → clean.

Next: full-repo verify (`poetry run pytest tests/ -q` and `poetry run pre-commit run --all-files`)
for the story's completion report. All eleven of this story's tasks are now committed.

Watch: `MeasurementForm.clean()` (`fairdm/core/measurement/forms.py`) still duplicates the
base-Measurement refusal the model's own `clean()` already raises via `_post_clean()` - harmless
today (the duplicate error text is deduplicated by nothing, so a form re-render would show the
message twice), but it is dead logic once a form's `_post_clean()` runs, and `tasks.md`'s T029
already names the fix. Left alone because `forms.py` is out of this story's scope; flagging for
whichever story owns it.

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

## 2026-08-19T12:10:00Z · Implementer US8 · T095/T096

Did: FR-040 required the measurement admin list to be narrowable by dataset, sample and
measurement type; `list_filter` carried only `"added"` on both the child and parent admin classes,
and the three tests that looked like coverage (`TestMeasurementAdminFilters.test_filter_by_dataset`,
`test_filter_by_sample`, `test_filter_by_polymorphic_type`) accepted the `measurement_admin` fixture
and never used it, asserting `Measurement.objects.filter(...)` directly instead. Rewrote all three
to exercise the real registered `MeasurementParentAdmin` instance
(`django.contrib.admin.site._registry[Measurement]`) via `get_changelist_instance(request)` with
the filter's query-string parameter set, per FR-040's own acceptance wording ("asserted THROUGH the
administrative interface, not by querying the model directly"). Added two further tests asserting
`"dataset"` and `"sample"` are present in `list_filter` on both `MeasurementChildAdmin` and
`MeasurementParentAdmin` directly (T096's own acceptance: "the administrative classes are read").
Added `"dataset"` and `"sample"` to `list_filter` on both classes in `fairdm/core/measurement/admin.py`.

While proving `test_filter_by_dataset` green, found that Django's default `RelatedFieldListFilter`
draws its choices from `Dataset`'s default manager, which excludes private datasets (FR-019,
`fairdm/core/dataset/models.py:159` `DatasetManager`) - and a dataset's own model default is
private (documented in `tests/test_core/test_measurement/conftest.py`'s `dataset` fixture). With
only private datasets present, `has_output()` is `False` for fewer than two choices, and Django
silently drops the filter entirely rather than degrading to "no visible choices" - the query
parameter is consumed and discarded during filter construction regardless, so a hand-built
`?dataset__id__exact=` URL is silently ignored too. That would have made FR-040's dataset narrowing
fail in the ordinary case. Added `MeasurementDatasetListFilter(admin.RelatedFieldListFilter)` in
`admin.py`, overriding `field_choices` to draw from `Dataset.all_objects` instead - the same
reasoning `DatasetAdmin.get_queryset` already documents for itself ("the administrative interface
is where a portal is repaired and needs to see everything", FR-019a). `sample` needed no equivalent
fix: `Sample`'s own default manager carries no visibility exclusion (visibility is a `Dataset`-level
concept).

Verified: `poetry run pytest tests/test_core/test_measurement/test_admin.py -q -p no:randomly` →
25 passed. `poetry run ruff check fairdm/core/measurement/admin.py
tests/test_core/test_measurement/test_admin.py` → all checks passed. `poetry run ruff format --check`
on both files → already formatted (after one `ruff format` pass that only re-wrapped two
pre-existing search tests' argument lists, no content change).

Next: T097/T098 - inline row caps.

Watch: `MeasurementDatasetListFilter` is scoped to the `dataset` FK only; if a future filter is
added on another privacy-managed relation, the same silent-drop failure mode applies and needs the
same treatment.

## 2026-08-19T12:35:00Z · Implementer US8 · T097/T098

Did: inline row caps for descriptions, dates and identifiers were hard-coded to 6, 6 and 3,
but the specification requires each to offer no more rows than its own vocabulary has member
types - measured: descriptions 4 (`MeasurementConditions`, `MeasurementSetup`,
`MeasurementTearDown`, `Other`), dates 2 (`Setup`, `TearDown`), identifiers 1 (`DOI`). Changed
`MeasurementDescriptionInline.max_num`, `MeasurementDateInline.max_num` and
`MeasurementIdentifierInline.max_num` in `fairdm/core/measurement/admin.py` to
`len(<Model>.VOCABULARY.values)` each, so the cap tracks the vocabulary rather than repeating a
number by hand. Left `MeasurementContributionInline` with no `max_num` at all - contributions are
NOT capped, per the design review correction in the brief: a contribution credits a person or
organisation, not a vocabulary member, and capping it at a role vocabulary's size would limit how
many contributors a measurement can have.

Added `TestMeasurementAdminInlineRowCaps` asserting each of the three capped inlines' `max_num`
equals its vocabulary's member count, and a fourth test asserting
`MeasurementContributionInline.max_num is None`. Also added
`test_inline_contribution_can_be_added_and_changed` to `TestMeasurementAdminInlines` - the
existing inline tests covered creation for descriptions, dates and identifiers but nothing at all
for contributions, and T097's acceptance names all four record kinds and both "added and changed".

Verified: `poetry run pytest tests/test_core/test_measurement/test_admin.py -q -p no:randomly` →
30 passed (was 3 failing for the expected reason - `max_num` mismatched the vocabulary count -
before the admin.py change). `poetry run ruff check` and `ruff format --check` on both touched
files → all checks passed / already formatted.

Next: T099 - every registered measurement type offers the same attached-record editors.

Watch: none outstanding.

## 2026-08-19T12:45:00Z · Implementer US8 · T099

Did: added `TestMeasurementAdminSharedInlines.test_every_registered_type_offers_the_same_inlines`,
asserting that every registered measurement type's admin class (`ExampleMeasurementAdmin`,
`XRFMeasurementAdmin`, `ICP_MS_MeasurementAdmin`, read from `registry.measurements` and the real
`django.contrib.admin.site` registry) has `inlines == MeasurementChildAdmin.inlines`. No
implementation change was needed: none of the concrete admin classes in `fairdm_demo/admin.py`
override `inlines`, so they already inherit the shared set. Checked the assertion was not
tautological by temporarily setting `inlines = []` on `XRFMeasurementAdmin` in
`fairdm_demo/admin.py`, confirming the test fails with a clear diff, then reverting - `git diff`
on that file is empty.

Verified: `poetry run pytest tests/test_core/test_measurement/test_admin.py -q -p no:randomly` →
31 passed. `poetry run ruff check` / `ruff format --check` on the touched test file → all checks
passed / already formatted.

Next: T100/T101 - the administrative list names each row's measurement type.

Watch: none outstanding.

## 2026-08-19T12:55:00Z · Implementer US8 · T100/T101

Did: `measurement_type` was already in `list_display` on both `MeasurementChildAdmin` and
`MeasurementParentAdmin`, and the `measurement_type()` method existed (`admin.py:164`/`:211`), but
the only covering test (`test_list_display_configured`) never asserted the type column at all.
Added `TestMeasurementAdminTypeColumn` with three tests: `"measurement_type"` is present in
`list_display` on both admin classes, and `measurement_admin.measurement_type(obj)` - called the
way the changelist itself resolves a `list_display` callable - names the real polymorphic type
(`XRFMeasurement`'s and `ICP_MS_Measurement`'s own `verbose_name`, not the base `Measurement`'s,
and not equal to each other). No production change was needed - T101's column already existed;
only the test was missing. Checked the presence assertion was not tautological by temporarily
removing `"measurement_type"` from `MeasurementChildAdmin.list_display`, confirming the test fails,
then reverting - `git diff` on `admin.py` is empty.

Verified: `poetry run pytest tests/test_core/test_measurement/test_admin.py -q -p no:randomly` →
34 passed. `poetry run ruff check` / `ruff format --check` on the touched test file → all checks
passed / already formatted.

Next: run the full repo suite once and pre-commit for the completion report - all seven tasks in
this story (T095-T101) are now done.

Watch: none outstanding.

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

## 2026-08-19T12:43:00Z · Implementer US4 · T077-T078

Did: Read tests/test_core/test_measurement/test_permissions.py in full and
fairdm/core/measurement/permissions.py, fairdm/core/permissions.py, fairdm/core/utils.py per
ritual. Ran the baseline (`poetry run pytest tests/test_core/test_measurement -q -p no:randomly`) -
130 passed, 17 skipped, green. Removed TestMeasurementPermissionInheritance's skip (its reason
claimed "change/delete permission mapping needs debugging") and observed all 6 tests pass
unmodified, confirming the reason was false rather than something needing a fix. Rewrote the
class's 4 core tests (view/change/delete + none) plus test_multiple_measurements_inherit_from_same_dataset
against fairdm.core.utils.assign_perm - the entry point this codebase's own MeasurementPermissionBackend
implies - rather than guardian.shortcuts directly.

Verified: `poetry run pytest tests/test_core/test_measurement/test_permissions.py::TestMeasurementPermissionInheritance -q -p no:randomly`
→ 5 passed (exit 0).

Next: T079-T080 (TestMeasurementGuardianIntegration).

Watch: none yet - the assign-then-check pattern in this file later turned out to intermittently
fail for an unrelated reason; see the T085 entry.

## 2026-08-19T12:45:00Z · Implementer US4 · T079-T080

Did: Removed TestMeasurementGuardianIntegration's skip and ran it unmodified first (RED,
observed for the right reason): all 4 tests failed with `django.contrib.auth.models.Permission.DoesNotExist`
raised from `guardian.shortcuts.assign_perm` - the exact claim the skip made (guardian cannot
grant a permission directly on a polymorphic subclass instance), though the concrete exception
differs from the skip text's "WrongAppError" (same root cause, different code path: `assign_perm`
vs `has_perm`). Rewrote all 4 tests plus a new 5th
(test_direct_permission_coexists_with_inherited_dataset_permission) against
fairdm.core.utils.assign_perm/remove_perm/get_perms.

Verified: `poetry run pytest tests/test_core/test_measurement/test_permissions.py::TestMeasurementGuardianIntegration -q -p no:randomly`
→ 5 passed (exit 0); this class is included in the 6 clean full-file repeat runs recorded under T085.

Next: T081 (TestCrossDatasetPermissionBoundaries).

## 2026-08-19T12:47:00Z · Implementer US4 · T081

Did: Removed TestCrossDatasetPermissionBoundaries's skip. Its reason claimed the factory fails
building a Measurement whose sample belongs to a different dataset - confirmed false directly:
`ExampleMeasurementFactory(dataset=dataset_a, sample=sample_b)` builds without complaint on every
run, with and without the skip. Switched its grants to fairdm.core.utils.assign_perm for
consistency with the rest of the file and removed the now-dead top-level `guardian.shortcuts`
import.

Verified: `poetry run pytest tests/test_core/test_measurement/test_permissions.py::TestCrossDatasetPermissionBoundaries -q -p no:randomly`
→ 3 passed (exit 0); this class is included in the 6 clean full-file repeat runs recorded under
T085. Before that fix, this class's own tests intermittently failed for the reason documented
under T085 - not a defect in the isolation logic itself.

Next: T082-T083 (registered-type grant/consult).

## 2026-08-19T12:50:00Z · Implementer US4 · T082-T083

Did: Added TestMeasurementRegisteredTypePermissions (new class, not a re-enable): a grant via
fairdm.core.utils.assign_perm on a registered type (ExampleMeasurement) reads back identically on
the instance and on the bare record (`Measurement.objects.non_polymorphic().get(pk=...)`) (T082).
Added a test proving the negative space directly rather than assuming it: guardian's own
`assign_perm` still raises `Permission.DoesNotExist` for the identical call with no normalisation
in front of it. Added a third test unit-testing `fairdm.core.utils.get_permission_target` itself -
confirms it retargets an ExampleMeasurement instance to the base Measurement record (T083).

Verified: `poetry run pytest tests/test_core/test_measurement/test_permissions.py::TestMeasurementRegisteredTypePermissions -q -p no:randomly`
→ 3 passed (exit 0); this class is included in the 6 clean full-file repeat runs recorded under
T085.

Next: T084 (backend registration).

## 2026-08-19T12:52:00Z · Implementer US4 · T084

Did: Added TestMeasurementPermissionBackendRegistration - a settings-only test (no DB) asserting
`fairdm.core.measurement.permissions.MeasurementPermissionBackend`'s dotted path is present in
`settings.AUTHENTICATION_BACKENDS`. No production code change; the backend was already registered
(fairdm/conf/settings/auth.py:58), nothing asserted it before.

Verified: `poetry run pytest tests/test_core/test_measurement/test_permissions.py::TestMeasurementPermissionBackendRegistration -q -p no:randomly`
→ 1 passed (exit 0).

Next: T085 (final skip count + suite check).

## 2026-08-19T12:55:00Z · Implementer US4 · T085

Did: Confirmed zero `@pytest.mark.skip` remain in test_permissions.py. Ran
`poetry run pytest tests/test_core/test_measurement -q -p no:randomly -rs` repeatedly while
building T077-T084 and hit a genuinely reproducible intermittent failure: every re-enabled test
in this file, individually and in combination, would sometimes assert False right after a grant
that had just been made, with no consistent pattern across classes or run order. Ruled out (with
evidence, not assumption): the factory (isolated single-test reruns always passed), fairdm's
normalisation code (reproduced identically with a minimal repro using a plain Dataset and zero
fairdm permission code), and connection reuse (`CONN_MAX_AGE=0` made no difference).

Root cause: the directory conftest's `user` fixture is `PersonFactory()` with no override, and
`PersonFactory.is_active` is `Faker("boolean", chance_of_getting_true=80)` -
`fairdm/factories/contributors.py:72` - so roughly one user in five is created inactive.
`guardian.core.ObjectPermissionChecker.has_perm` denies every object permission to an inactive
user unconditionally, regardless of any grant. Added a local `user` fixture in
test_permissions.py forcing `is_active=True`, scoped to this file only (module-level fixture
override, `tests/conftest.py` and the directory conftest untouched).

Verified: `poetry run pytest tests/test_core/test_measurement/test_permissions.py -q -p no:randomly`
→ 21 passed, run 6 times consecutively, all clean. `poetry run pytest tests/test_core/test_measurement -q -p no:randomly`
→ 147 passed, 4 skipped, run 3 times consecutively, all clean. The 4 remaining skips, none of
them this story's:
- `test_filters.py:241` - "PartialDateField filtering requires investigation - field validation complex"
- `test_models.py:271` - "URL patterns not implemented yet - Phase 8"
- `test_models.py:716` - "Measurement detail URL not configured"
- `test_models.py:965` - "Demo ICPMSMeasurement not available"

Next: story-level final verify (`poetry run pytest tests/ -q`, `poetry run pre-commit run --all-files`)
and completion report.

Watch: `PersonFactory.is_active`'s 20%-inactive default is shared across the whole factory and
used by the directory's `user` fixture too - any *other* test file in this suite that calls
`user.has_perm(...)` without forcing `is_active=True` is exposed to the same intermittent
failure. Flagged in this story's completion report `concerns` rather than fixed, since
`fairdm/factories/contributors.py` and the directory conftest are shared, high-blast-radius files
outside this story's scope.

## 2026-08-19T12:58:00Z · Implementer US4 · decisions (recorded here, not in decisions.md)

The brief's prohibitions list forbids editing `decisions.md` for this story (it is not one of
the files the standard Implementer protocol's "append a decisions.md mini-ADR" step gets to
override). Recording the two non-obvious choices here instead.

**D-US4-1: `PersonFactory(is_active=True)` overridden locally in test_permissions.py, not fixed
at the source.** Decision: this file defines its own module-level `user` fixture
(`PersonFactory(is_active=True)`), shadowing the directory conftest's `user` for every test in
this file only. Why: `PersonFactory.is_active` (`fairdm/factories/contributors.py:72`) is
`Faker("boolean", chance_of_getting_true=80)` - about one user in five is created inactive, and
`guardian.core.ObjectPermissionChecker.has_perm` denies every object permission to an inactive
user unconditionally, independent of any grant. The correct permanent fix is
`fairdm/factories/contributors.py` or the directory conftest, both shared across the whole test
suite and outside this story's file scope - reported in `concerns` instead. Revisit if: a
follow-up fixes the shared fixture/factory directly, at which point this file's local override
becomes redundant rather than load-bearing.

**D-US4-2: Nine brief tasks landed as six commits, grouped by shared test class.** Decision:
T077+T078 landed together (both covered by `TestMeasurementPermissionInheritance`), T079+T080
landed together (`TestMeasurementGuardianIntegration`), T082+T083 landed together
(`TestMeasurementRegisteredTypePermissions`); T081, T084, T085 each landed alone. Why: splitting
a single pre-existing class's skip-removal and rewrite across two commits would mean transiently
deleting methods in one commit and restoring them in the next - keeping each class whole within
one commit was judged safer than following task numbering literally. Every commit subject names
every task it covers. Revisit if: a reviewer wants literal one-task-one-commit granularity.

## 2026-08-19T13:11:00Z · Implementer US3 · T042/T043/T044/T045/T046/T047

Did: `MeasurementDescription`/`MeasurementDate`/`MeasurementIdentifier` already carried a
direct `related` FK to `Measurement` with `on_delete=CASCADE`, and their `VOCABULARY` bindings
already existed - both open only for lack of a test. Added
`TestMeasurementMetadataRelations` (direct relation + cascade-on-delete for all three, in
`tests/test_core/test_measurement/test_models.py`) and
`TestMeasurementDescriptionVocabularyMembers`/`TestMeasurementDateVocabularyMembers`
(vocabulary members asserted by name: `MeasurementConditions`/`MeasurementSetup`/
`MeasurementTearDown`/`Other` and `Setup`/`TearDown`), mirroring the existing
`TestMeasurementIdentifierVocabulary` pattern (T048/T049).

Corrected the two pre-existing tests T044/T046 name by number:
`TestMeasurementVocabularyValidation.test_measurement_description_uses_measurement_vocabulary`
asserted `desc.type == "method"` and `..._date_uses_measurement_vocabulary` asserted
`date.type == "measured"` - neither is a member of its vocabulary; both passed only because
nothing validated `type`. Swapped for real members (`"MeasurementSetup"`, `"Setup"`). No other
pre-existing test touched.

Verified: `poetry run pytest tests/test_core/test_measurement/test_models.py -q -p no:randomly
-k "TestMeasurementMetadataRelations or TestMeasurementDescriptionVocabularyMembers or
TestMeasurementDateVocabularyMembers or TestMeasurementVocabularyValidation or
TestMeasurementIdentifierVocabulary"` → 10 passed. `poetry run ruff check
tests/test_core/test_measurement/test_models.py` → all checks passed.

Next: T050/T051.

Watch: none.

## 2026-08-19T13:11:00Z · Implementer US3 · T050/T051

Did: `GenericModel.__init_subclass__` (`fairdm/core/abstract.py`) already binds `type`'s
`choices` to `VOCABULARY`, so `full_clean()` already refuses an out-of-vocabulary type via
`clean_fields()`, naming the offending value in Django's own message - confirmed by test, no
code change needed for that half (T050). Django validates `choices` only through
`full_clean()`, though, so a direct `MeasurementDescription.objects.create(type="bogus", ...)`
or a bare `.save()` reached the database untouched. Closed that route (T051) with a `save()`
override on each of `MeasurementDescription`, `MeasurementDate` and `MeasurementIdentifier`
(`fairdm/core/measurement/models.py`) that checks `type` against `VOCABULARY.values` before
calling `super().save()`, raising `ValidationError` naming the offending type otherwise - the
same shape `SampleRelation.save()` uses to close the equivalent "direct save must refuse too"
gap for FR-027 (`fairdm/core/sample/models.py`). Did not touch `fairdm/core/abstract.py`,
`fairdm/core/sample/models.py`, or any other domain's description/date/identifier models -
duplicating the three-line check per class, matching the existing convention (Sample's own
`SampleDescription`/`SampleDate`/`SampleIdentifier.clean()` already duplicate the equivalent
vocabulary check three times) rather than generalising into shared, cross-domain infrastructure
outside this story's scope.

Added `TestMeasurementMetadataTypeValidation`: one test per record type (description, date,
identifier) proving `full_clean()` refuses, and one proving a direct
`MeasurementXFactory(type=...)` create (bypassing `full_clean()`) refuses too, asserting the
offending type string appears in the raised message.

RED confirmed for the right reason before implementing: `git stash` on
`fairdm/core/measurement/models.py` alone, reran the three `..._is_refused_on_direct_save`
tests - all three failed `Failed: DID NOT RAISE ValidationError` (not an import/fixture error),
then `git stash pop` to restore the implementation.

Consequence, not fixed (out of this story's authorized test-editing scope - only the two tests
T044/T046 name may be corrected, per the brief's prohibitions): running
`poetry run pytest tests/test_core/test_measurement -q -p no:randomly` after this change shows
14 pre-existing tests failing because they created a `MeasurementDescription`/`MeasurementDate`
with an out-of-vocabulary `type` (`"method"`, `"measured"`, `"instrument"`, `"calibrated"`) as
incidental filler data, not as a test of the vocabulary itself:

- `tests/test_core/test_measurement/test_models.py` (10, this story's own file, none named by
  a brief task): `TestMeasurementQuerySetOptimizations::test_with_metadata_prefetches_descriptions_dates_identifiers`
  (line 611); `TestMeasurementFAIRMetadata::test_measurement_description_uses_measurement_vocabulary`,
  `::test_measurement_date_uses_measurement_vocabulary`,
  `::test_measurement_vocabulary_types_differ_from_sample_vocabularies`,
  `::test_measurement_can_have_multiple_descriptions_of_different_types`,
  `::test_measurement_can_have_multiple_dates_of_different_types` (class at line 1218);
  `TestMeasurementQuerySetOptimization::test_with_metadata_prefetches_descriptions_dates_identifiers`,
  `::test_queryset_method_chaining_works_correctly`,
  `::test_large_measurement_collection_loads_efficiently` (class at line 1306).
- `tests/test_core/test_measurement/test_admin.py` (2, prohibited file - owned by a concurrent
  story): `TestMeasurementAdminInlines::test_inline_metadata_can_be_created`,
  `::test_inline_dates_can_be_created`;
  `TestMeasurementAdminVocabularyCorrectness::test_measurement_description_uses_measurement_vocabulary`,
  `::test_measurement_date_uses_measurement_vocabulary`.
- `tests/test_core/test_measurement/test_filters.py` (1, prohibited file - owned by a concurrent
  story): `TestMeasurementFilterCrossRelationshipFiltering::test_filter_by_description_text`.

Verified: `poetry run pytest tests/test_core/test_measurement/test_models.py -q -p no:randomly
-k "TestMeasurementMetadataTypeValidation"` → 6 passed. `poetry run ruff check
fairdm/core/measurement/models.py tests/test_core/test_measurement/test_models.py` → all checks
passed. `poetry run python manage.py makemigrations --check --dry-run` → no migration needed
for `measurement` (only an unrelated, pre-existing `identity` app migration surfaced, untouched
by this story).

Next: story-level final verify (`poetry run pytest tests/ -q`, `poetry run pre-commit run
--all-files`) and completion report.

Watch: the 14 tests listed above will keep failing until either their owning story/file corrects
the filler `type` value, or a follow-up task does. This directly affects merge readiness for
`test_models.py` (this story's own file, but the specific tests are unnamed by any brief task
here) and cross-story for `test_admin.py`/`test_filters.py`.

## 2026-08-19T13:16:00Z · Implementer US3 · story-level final verify

Did: ran `poetry run pytest tests/ -q` (once, per protocol). Result: 16 failed, 1957 passed, 17
skipped. 14 are the ones logged in the T050/T051 entry above. Two more, outside
`tests/test_core/test_measurement/` and so not visible from that directory's own baseline
check, surfaced here for the first time:

- `tests/test_factories/test_core.py::TestMeasurementFactories::test_measurement_description_factory`
  (line 623) - calls `MeasurementDescriptionFactory(related=measurement, type="Abstract")`;
  `"Abstract"` is a member of the Project/Dataset description vocabulary, not Measurement's.
- `tests/test_factories/test_core.py::TestMeasurementFactories::test_measurement_date_factory`
  (line 636) - calls `MeasurementDateFactory(related=measurement, type="Created")`; `"Created"`
  is a member of the Sample date vocabulary, not Measurement's.

Both docstrings assert the factory "creates valid descriptions/dates", which was never true of
the vocabulary - only of the absence of validation. Not fixed, for the same reason as the 14
above: not named by any task in this story's brief, and this file is outside
`tests/test_core/test_measurement/` entirely. All 16 are listed individually in the completion
report.

`poetry run pre-commit run --all-files` next, then the completion report.

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

## 2026-08-19T12:12:16Z · Implementer US1 · T030/T034

Did: `BaseMeasurementConfiguration` declared fixed `form_fields`/`table_fields`/`filterset_fields`,
which meant `ModelConfiguration.resolve_fields()` never fell back to a registered type's own
`fields` list for those three components - `XRFMeasurementConfig`'s own fields (`element`,
`concentration_ppm`, ...) never reached the generated form, table or filterset, only the fields
every measurement has. Confirmed by direct probe against the running registry before writing a
test. Added `BaseMeasurementConfiguration.resolve_fields()`, appending the type's own fields for
`form`/`table`/`filterset` only - `admin`'s generated `list_display` already drew from `fields`
directly (no `admin_list_display` override on the base config) and already carried a type's own
fields, confirmed by the same probe, so it is untouched. Strengthened
`tests/test_core/test_measurement/test_config.py`'s four `test_auto_generated_*_includes_*`
tests with new sibling tests asserting a named own field (`element`/`concentration_ppm`) is
present on each generated form/table/filterset/admin (T030), and replaced T034's
`hasattr(config, "table_fields")`-style checks with assertions that `"name"`/`"sample"`/`"dataset"`
are literally present in `config.table_fields`/`form_fields`/`filterset_fields`.

Verified: confirmed RED first by `git stash push` on the `config.py` fix alone and running
`poetry run pytest tests/test_core/test_measurement/test_config.py -q -p no:randomly -k
own_fields` → 3 failed for the right reason (form/filterset/table missing `element`), 1 passed
(admin, already correct). Restored the fix (`git stash pop`) and reran
`poetry run pytest tests/test_core/test_measurement/test_config.py -q -p no:randomly` → 16 passed.
`poetry run ruff check` + `ruff format --check` on both touched files → clean.

Next: T025/T026/T028/T029 (the bare-measurement refusal routes) and T032/T033 (admin type
selection reads the registry).

Watch: `fairdm/core/measurement/config.py` and its test file are not in this story's prohibited
list, so this was in scope; flagging here in case another concurrent story also touches
`BaseMeasurementConfiguration`.

## 2026-08-19T12:15:20Z · Implementer US1 · T036/T037/T038

Did: the audit's largest finding for this story - two administrative base classes existed for
measurement types, and the registry enforced the wrong one. `fairdm/core/measurement/admin.py`
defines `MeasurementChildAdmin` (176 lines: inlines, fieldsets, autocomplete, readonly fields) and
is what `fairdm.core.measurement.admin.MeasurementParentAdmin` (the class actually registered with
`admin.site` - confirmed via `admin.site._registry[Measurement]` before touching anything) already
uses. `fairdm/core/admin.py` carried a two-line `MeasurementAdmin` stub and a second,
never-registered `MeasurementParentAdmin` (its `@admin.register` commented out) built from
`get_subclasses()` rather than the registry. Both registry references pointed at the two-line stub:
validation (`fairdm/registry/config.py:377`, aliasing the stub in as `MeasurementChildAdmin`) and
generation (`fairdm/registry/factories.py:803`). A portal supplying `MeasurementChildAdmin` - the
class the docstring and both doc pages actually tell a developer to inherit - was refused, with a
message naming the two-line stub instead.

T036 (test-first): rewrote `tests/test_registry/test_config.py::TestAdminInheritanceValidation`'s
three Measurement-admin tests. `test_measurement_with_correct_admin_class_passes` and
`test_autogenerated_measurement_admin_inherits_from_child_admin` imported the stub under the real
class's name (`from fairdm.core.admin import MeasurementAdmin as MeasurementChildAdmin`), so both
asserted against the wrong class by construction and passed whether or not the registry checked
against the configured base; now both import `MeasurementChildAdmin` from
`fairdm.core.measurement.admin` under its own name.
`test_measurement_with_wrong_admin_class_raises_error`'s message assertion now expects
"MeasurementChildAdmin". Ran alone first and confirmed 3 failures for the right reason (old
config.py still checked/named the stub) before touching implementation.

T037: `fairdm/registry/config.py::ModelConfiguration._validate_admin_inheritance` now imports
`MeasurementChildAdmin` from `fairdm.core.measurement.admin` and the refusal message names
`MeasurementChildAdmin`, not `MeasurementAdmin`.

T038: `fairdm/registry/factories.py::PolymorphicAdminMixin._get_admin_base_class` (the branch that
generates an admin for a type supplying none) now imports and returns
`fairdm.core.measurement.admin.MeasurementChildAdmin`, matching the Sample branch immediately above
it, which already used `SampleChildAdmin` correctly - this was the asymmetry the audit named.
Checked every importer of the two `fairdm/core/admin.py` classes first
(`grep -rn "MeasurementAdmin\b"` across the tree): only the two registry references above and
`tests/registry_models/admin.py` (a test-support admin module, not one of this story's prohibited
test files) imported the stub, to build `ConcreteMeasurementAdmin` for the registry test suite's
own concrete type - repointed to `fairdm.core.measurement.admin.MeasurementChildAdmin`. Deleted
`MeasurementAdmin` and the commented-out `MeasurementParentAdmin` from `fairdm/core/admin.py`,
along with the imports (`PolymorphicChildModelAdmin`, `PolymorphicChildModelFilter`,
`PolymorphicParentModelAdmin`, `Measurement`, `get_subclasses`) that only they used -
`DescriptionInline`/`DateInline` (dataset-related, pre-existing, out of this story's scope) are the
only classes left in that file and needed none of them.

Verified: `poetry run pytest tests/test_registry/test_config.py::TestAdminInheritanceValidation -q
-p no:randomly` → 3 failed for the right reason before T037, 8 passed after T037+T038.
`poetry run pytest tests/test_registry/ tests/test_core/test_measurement/test_config.py
tests/test_core/test_sample -q -p no:randomly` → 513 passed, 7 skipped.
`poetry run pytest tests/test_core/test_measurement -q -p no:randomly` → 134 passed, 17 skipped
(unchanged skip count from the story's baseline run). `poetry run ruff check` +
`ruff format --check` on every touched file → clean. `grep -rn "from fairdm.core.admin import"`
across the tree → no remaining importers of the deleted names.

Next: T025/T026/T028/T029 (the bare-measurement refusal routes) and T032/T033 (admin type
selection reads the registry).

Watch: none outstanding. `DescriptionInline`/`DateInline` in `fairdm/core/admin.py` are themselves
unreferenced outside that file (confirmed by grep) but are dataset-related and outside this
story's scope - left untouched and not raised as a concern, since a plain unused-class question
for a different domain isn't this story's finding to make.

## 2026-08-19T12:18:16Z · Implementer US1 · T025/T032/T033

Did: added `tests/test_core/test_measurement/test_admin_registry.py` rather than extending
`tests/test_core/test_measurement/test_admin.py` - that file is on this story's prohibited list
(owned by a concurrently running story) even though T025 and T032 name it in `tasks.md`. A new
file carries zero merge-conflict risk with whatever that other story lands there, which is the
concern the prohibition protects against.

T033: `MeasurementParentAdmin.get_child_models()` already reads `registry.measurements`
(`fairdm/core/measurement/admin.py:172-176`) - confirmed by monkeypatching the registry property
to a sentinel list and observing the admin's child models change to match it, which the existing
`assert len(child_models) > 0` coverage could not distinguish from a hardcoded non-empty list. No
implementation change.

T032: registered `tests.registry_models.models.ConcreteMeasurement` (a real, installed-app type,
"the shape a portal actually registers" per its own docstring) via `registry.register()` inside
the test, standing in for a type registered from outside the framework. Asserted it appears among
`get_child_models()`, that a registered `ConcreteSample` (non-measurement) does not, and that the
unregistered base `Measurement` does not. `tests/test_core/test_measurement/conftest.py`'s local
`clean_registry` fixture only snapshots/restores `registry._registry` around the test rather than
clearing it first (unlike `tests/test_registry/conftest.py`'s fixture of the same name, which
empties it) - written the assertions to work with either registry state (framework types stay
registered during the test) rather than assuming an empty registry.

T025: the administrative-interface route was already refused - `Measurement` is never in
`registry.measurements`, so the parent admin's add view 403s on the base content type the same
way it would for any unregistered model. No implementation change; this route was untested.

Verified: `poetry run pytest tests/test_core/test_measurement/test_admin_registry.py -q -p
no:randomly` → 6 passed. `poetry run ruff check` + `ruff format` (one file needed reformatting,
applied and reconfirmed clean) on the new file.

Next: T026/T028/T029 (the bare-measurement manager and form refusal routes).

Watch: none outstanding.

## 2026-08-19T12:20:49Z · Implementer US1 · T026/T028

Did: closed the manager route around the base-Measurement refusal. `Measurement.objects.create()`
produced a bare record, because `clean()` (`models.py:111`) only runs when something calls it or
`full_clean()` - forms and the admin do, the manager and a bare `.save()` do not.

The natural home for this guard is `models.py`/`managers.py` (the working pattern already landed
for `Sample`: `fairdm/core/sample/models.py`'s `block_base_sample_creation`, a `pre_save` receiver
declared right beside `Sample.clean()`), but both files are on this story's prohibited list (owned
by a concurrently running story). Added the equivalent guard,
`block_base_measurement_creation`, to `fairdm/core/measurement/apps.py` instead, connected via
`AppConfig.ready()` with `sender=Measurement` - the one mechanism that also covers Django fixture
deserialization (`django.core.serializers` sends `pre_save` on every raw object before saving it),
and is scoped so a registered subclass's own save is untouched (a subclass instance sends its own
class on save, never `Measurement`). The message text mirrors `Measurement.clean()`'s exactly;
declared as a new module-level constant in `apps.py` rather than imported from `models.py`, for the
same file-scope reason.

New file `tests/test_core/test_measurement/test_managers.py` (mirrors `managers.py`; `test_models.py`
is prohibited) proves three routes: `Measurement.objects.create()`, a bare `Measurement().save()`,
and deserializing a raw fixture row for the base model (T026's "no fixture in the framework creates
one", read as Django fixture loading rather than a pytest fixture, matching the Sample precedent's
`test_fixture_loading_refuses_a_bare_sample`).

Verified: confirmed RED for the right reason before implementing - `poetry run pytest
tests/test_core/test_measurement/test_managers.py -q -p no:randomly` → first two tests "DID NOT
RAISE ValidationError" (the bug), third hit an unrelated `IntegrityError: NOT NULL constraint
failed: measurement_measurement.added` (the fixture-loading route skips `auto_now_add`, and would
never be reached once the guard fires before the INSERT). After the `apps.py` change: same command
→ 3 passed. `poetry run pytest tests/test_core/test_measurement tests/test_registry
tests/test_factories -q -p no:randomly` → 458 passed, 17 skipped, no regressions from a
framework-wide `pre_save` receiver. `poetry run ruff check` + `ruff format` (one auto-fix, an
f-string for a percent-format lint) on both touched files → clean.

Next: T029 (the form's refusal message).

Watch: the natural, single-file location for this guard is `fairdm/core/measurement/models.py`,
alongside `Measurement.clean()` (the exact shape already used for `Sample`). If the story owning
`models.py` lands its own change there before this merges, Forge's convergence pass may want to
fold `apps.py`'s guard into `models.py` to match the Sample precedent - flagging so it isn't
mistaken for a second, competing mechanism.

## 2026-08-19T12:22:22Z · Implementer US1 · T029

Did: `test_form_prevents_base_measurement_instantiation`
(`tests/test_core/test_measurement/test_forms.py`) only asserted `not form.is_valid()`. Probed the
actual `form.errors` first: the test's dataset is deliberately private and the form is built with
no `request`, so `MeasurementFormMixin`'s dataset-choice scoping alone puts a `"dataset"` error on
the form independently of the base-Measurement refusal - the old assertion passed whether or not
the refusal fired at all. The probe also confirmed the refusal message
("Cannot create base Measurement instances directly...") appears twice in `form.errors["__all__"]`,
once from `MeasurementForm.clean()` and once from the model's own `clean()` via `_post_clean()` -
exactly the duplicate rendering `tasks.md` names. Rewrote the test to assert the message
("subclass"/"directly") is present in `__all__`, alongside the existing `is_valid()` check.

Deviation from `tasks.md`'s T029 text: did not delete `MeasurementForm.clean()`. That edit is in
`fairdm/core/measurement/forms.py`, which is on this story's prohibited list (owned by a
concurrently running story). Only the test-side fix (asserting on the message) is in this story's
scope per the brief's acceptance criterion, which is scoped to the test's assertion and does not
itself require the form-side cleanup. The duplicate `__all__` entry remains; noted as a concern
for whichever story owns `forms.py`.

Verified: `poetry run pytest tests/test_core/test_measurement/test_forms.py -q -p no:randomly` →
11 passed. `poetry run ruff check` + `ruff format --check` on the touched file → clean.

Next: full-repo verify (`poetry run pytest tests/ -q` and `poetry run pre-commit run --all-files`)
for the story's completion report. All eleven of this story's tasks are now committed.

Watch: `MeasurementForm.clean()` (`fairdm/core/measurement/forms.py`) still duplicates the
base-Measurement refusal the model's own `clean()` already raises via `_post_clean()` - harmless
today (the duplicate error text is deduplicated by nothing, so a form re-render would show the
message twice), but it is dead logic once a form's `_post_clean()` runs, and `tasks.md`'s T029
already names the fix. Left alone because `forms.py` is out of this story's scope; flagging for
whichever story owns it.

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

## 2026-08-19T12:10:00Z · Implementer US8 · T095/T096

Did: FR-040 required the measurement admin list to be narrowable by dataset, sample and
measurement type; `list_filter` carried only `"added"` on both the child and parent admin classes,
and the three tests that looked like coverage (`TestMeasurementAdminFilters.test_filter_by_dataset`,
`test_filter_by_sample`, `test_filter_by_polymorphic_type`) accepted the `measurement_admin` fixture
and never used it, asserting `Measurement.objects.filter(...)` directly instead. Rewrote all three
to exercise the real registered `MeasurementParentAdmin` instance
(`django.contrib.admin.site._registry[Measurement]`) via `get_changelist_instance(request)` with
the filter's query-string parameter set, per FR-040's own acceptance wording ("asserted THROUGH the
administrative interface, not by querying the model directly"). Added two further tests asserting
`"dataset"` and `"sample"` are present in `list_filter` on both `MeasurementChildAdmin` and
`MeasurementParentAdmin` directly (T096's own acceptance: "the administrative classes are read").
Added `"dataset"` and `"sample"` to `list_filter` on both classes in `fairdm/core/measurement/admin.py`.

While proving `test_filter_by_dataset` green, found that Django's default `RelatedFieldListFilter`
draws its choices from `Dataset`'s default manager, which excludes private datasets (FR-019,
`fairdm/core/dataset/models.py:159` `DatasetManager`) - and a dataset's own model default is
private (documented in `tests/test_core/test_measurement/conftest.py`'s `dataset` fixture). With
only private datasets present, `has_output()` is `False` for fewer than two choices, and Django
silently drops the filter entirely rather than degrading to "no visible choices" - the query
parameter is consumed and discarded during filter construction regardless, so a hand-built
`?dataset__id__exact=` URL is silently ignored too. That would have made FR-040's dataset narrowing
fail in the ordinary case. Added `MeasurementDatasetListFilter(admin.RelatedFieldListFilter)` in
`admin.py`, overriding `field_choices` to draw from `Dataset.all_objects` instead - the same
reasoning `DatasetAdmin.get_queryset` already documents for itself ("the administrative interface
is where a portal is repaired and needs to see everything", FR-019a). `sample` needed no equivalent
fix: `Sample`'s own default manager carries no visibility exclusion (visibility is a `Dataset`-level
concept).

Verified: `poetry run pytest tests/test_core/test_measurement/test_admin.py -q -p no:randomly` →
25 passed. `poetry run ruff check fairdm/core/measurement/admin.py
tests/test_core/test_measurement/test_admin.py` → all checks passed. `poetry run ruff format --check`
on both files → already formatted (after one `ruff format` pass that only re-wrapped two
pre-existing search tests' argument lists, no content change).

Next: T097/T098 - inline row caps.

Watch: `MeasurementDatasetListFilter` is scoped to the `dataset` FK only; if a future filter is
added on another privacy-managed relation, the same silent-drop failure mode applies and needs the
same treatment.

## 2026-08-19T12:35:00Z · Implementer US8 · T097/T098

Did: inline row caps for descriptions, dates and identifiers were hard-coded to 6, 6 and 3,
but the specification requires each to offer no more rows than its own vocabulary has member
types - measured: descriptions 4 (`MeasurementConditions`, `MeasurementSetup`,
`MeasurementTearDown`, `Other`), dates 2 (`Setup`, `TearDown`), identifiers 1 (`DOI`). Changed
`MeasurementDescriptionInline.max_num`, `MeasurementDateInline.max_num` and
`MeasurementIdentifierInline.max_num` in `fairdm/core/measurement/admin.py` to
`len(<Model>.VOCABULARY.values)` each, so the cap tracks the vocabulary rather than repeating a
number by hand. Left `MeasurementContributionInline` with no `max_num` at all - contributions are
NOT capped, per the design review correction in the brief: a contribution credits a person or
organisation, not a vocabulary member, and capping it at a role vocabulary's size would limit how
many contributors a measurement can have.

Added `TestMeasurementAdminInlineRowCaps` asserting each of the three capped inlines' `max_num`
equals its vocabulary's member count, and a fourth test asserting
`MeasurementContributionInline.max_num is None`. Also added
`test_inline_contribution_can_be_added_and_changed` to `TestMeasurementAdminInlines` - the
existing inline tests covered creation for descriptions, dates and identifiers but nothing at all
for contributions, and T097's acceptance names all four record kinds and both "added and changed".

Verified: `poetry run pytest tests/test_core/test_measurement/test_admin.py -q -p no:randomly` →
30 passed (was 3 failing for the expected reason - `max_num` mismatched the vocabulary count -
before the admin.py change). `poetry run ruff check` and `ruff format --check` on both touched
files → all checks passed / already formatted.

Next: T099 - every registered measurement type offers the same attached-record editors.

Watch: none outstanding.

## 2026-08-19T12:45:00Z · Implementer US8 · T099

Did: added `TestMeasurementAdminSharedInlines.test_every_registered_type_offers_the_same_inlines`,
asserting that every registered measurement type's admin class (`ExampleMeasurementAdmin`,
`XRFMeasurementAdmin`, `ICP_MS_MeasurementAdmin`, read from `registry.measurements` and the real
`django.contrib.admin.site` registry) has `inlines == MeasurementChildAdmin.inlines`. No
implementation change was needed: none of the concrete admin classes in `fairdm_demo/admin.py`
override `inlines`, so they already inherit the shared set. Checked the assertion was not
tautological by temporarily setting `inlines = []` on `XRFMeasurementAdmin` in
`fairdm_demo/admin.py`, confirming the test fails with a clear diff, then reverting - `git diff`
on that file is empty.

Verified: `poetry run pytest tests/test_core/test_measurement/test_admin.py -q -p no:randomly` →
31 passed. `poetry run ruff check` / `ruff format --check` on the touched test file → all checks
passed / already formatted.

Next: T100/T101 - the administrative list names each row's measurement type.

Watch: none outstanding.

## 2026-08-19T12:55:00Z · Implementer US8 · T100/T101

Did: `measurement_type` was already in `list_display` on both `MeasurementChildAdmin` and
`MeasurementParentAdmin`, and the `measurement_type()` method existed (`admin.py:164`/`:211`), but
the only covering test (`test_list_display_configured`) never asserted the type column at all.
Added `TestMeasurementAdminTypeColumn` with three tests: `"measurement_type"` is present in
`list_display` on both admin classes, and `measurement_admin.measurement_type(obj)` - called the
way the changelist itself resolves a `list_display` callable - names the real polymorphic type
(`XRFMeasurement`'s and `ICP_MS_Measurement`'s own `verbose_name`, not the base `Measurement`'s,
and not equal to each other). No production change was needed - T101's column already existed;
only the test was missing. Checked the presence assertion was not tautological by temporarily
removing `"measurement_type"` from `MeasurementChildAdmin.list_display`, confirming the test fails,
then reverting - `git diff` on `admin.py` is empty.

Verified: `poetry run pytest tests/test_core/test_measurement/test_admin.py -q -p no:randomly` →
34 passed. `poetry run ruff check` / `ruff format --check` on the touched test file → all checks
passed / already formatted.

Next: run the full repo suite once and pre-commit for the completion report - all seven tasks in
this story (T095-T101) are now done.

Watch: none outstanding.

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

## 2026-08-19T12:43:00Z · Implementer US4 · T077-T078

Did: Read tests/test_core/test_measurement/test_permissions.py in full and
fairdm/core/measurement/permissions.py, fairdm/core/permissions.py, fairdm/core/utils.py per
ritual. Ran the baseline (`poetry run pytest tests/test_core/test_measurement -q -p no:randomly`) -
130 passed, 17 skipped, green. Removed TestMeasurementPermissionInheritance's skip (its reason
claimed "change/delete permission mapping needs debugging") and observed all 6 tests pass
unmodified, confirming the reason was false rather than something needing a fix. Rewrote the
class's 4 core tests (view/change/delete + none) plus test_multiple_measurements_inherit_from_same_dataset
against fairdm.core.utils.assign_perm - the entry point this codebase's own MeasurementPermissionBackend
implies - rather than guardian.shortcuts directly.

Verified: `poetry run pytest tests/test_core/test_measurement/test_permissions.py::TestMeasurementPermissionInheritance -q -p no:randomly`
→ 5 passed (exit 0).

Next: T079-T080 (TestMeasurementGuardianIntegration).

Watch: none yet - the assign-then-check pattern in this file later turned out to intermittently
fail for an unrelated reason; see the T085 entry.

## 2026-08-19T12:45:00Z · Implementer US4 · T079-T080

Did: Removed TestMeasurementGuardianIntegration's skip and ran it unmodified first (RED,
observed for the right reason): all 4 tests failed with `django.contrib.auth.models.Permission.DoesNotExist`
raised from `guardian.shortcuts.assign_perm` - the exact claim the skip made (guardian cannot
grant a permission directly on a polymorphic subclass instance), though the concrete exception
differs from the skip text's "WrongAppError" (same root cause, different code path: `assign_perm`
vs `has_perm`). Rewrote all 4 tests plus a new 5th
(test_direct_permission_coexists_with_inherited_dataset_permission) against
fairdm.core.utils.assign_perm/remove_perm/get_perms.

Verified: `poetry run pytest tests/test_core/test_measurement/test_permissions.py::TestMeasurementGuardianIntegration -q -p no:randomly`
→ 5 passed (exit 0); this class is included in the 6 clean full-file repeat runs recorded under T085.

Next: T081 (TestCrossDatasetPermissionBoundaries).

## 2026-08-19T12:47:00Z · Implementer US4 · T081

Did: Removed TestCrossDatasetPermissionBoundaries's skip. Its reason claimed the factory fails
building a Measurement whose sample belongs to a different dataset - confirmed false directly:
`ExampleMeasurementFactory(dataset=dataset_a, sample=sample_b)` builds without complaint on every
run, with and without the skip. Switched its grants to fairdm.core.utils.assign_perm for
consistency with the rest of the file and removed the now-dead top-level `guardian.shortcuts`
import.

Verified: `poetry run pytest tests/test_core/test_measurement/test_permissions.py::TestCrossDatasetPermissionBoundaries -q -p no:randomly`
→ 3 passed (exit 0); this class is included in the 6 clean full-file repeat runs recorded under
T085. Before that fix, this class's own tests intermittently failed for the reason documented
under T085 - not a defect in the isolation logic itself.

Next: T082-T083 (registered-type grant/consult).

## 2026-08-19T12:50:00Z · Implementer US4 · T082-T083

Did: Added TestMeasurementRegisteredTypePermissions (new class, not a re-enable): a grant via
fairdm.core.utils.assign_perm on a registered type (ExampleMeasurement) reads back identically on
the instance and on the bare record (`Measurement.objects.non_polymorphic().get(pk=...)`) (T082).
Added a test proving the negative space directly rather than assuming it: guardian's own
`assign_perm` still raises `Permission.DoesNotExist` for the identical call with no normalisation
in front of it. Added a third test unit-testing `fairdm.core.utils.get_permission_target` itself -
confirms it retargets an ExampleMeasurement instance to the base Measurement record (T083).

Verified: `poetry run pytest tests/test_core/test_measurement/test_permissions.py::TestMeasurementRegisteredTypePermissions -q -p no:randomly`
→ 3 passed (exit 0); this class is included in the 6 clean full-file repeat runs recorded under
T085.

Next: T084 (backend registration).

## 2026-08-19T12:52:00Z · Implementer US4 · T084

Did: Added TestMeasurementPermissionBackendRegistration - a settings-only test (no DB) asserting
`fairdm.core.measurement.permissions.MeasurementPermissionBackend`'s dotted path is present in
`settings.AUTHENTICATION_BACKENDS`. No production code change; the backend was already registered
(fairdm/conf/settings/auth.py:58), nothing asserted it before.

Verified: `poetry run pytest tests/test_core/test_measurement/test_permissions.py::TestMeasurementPermissionBackendRegistration -q -p no:randomly`
→ 1 passed (exit 0).

Next: T085 (final skip count + suite check).

## 2026-08-19T12:55:00Z · Implementer US4 · T085

Did: Confirmed zero `@pytest.mark.skip` remain in test_permissions.py. Ran
`poetry run pytest tests/test_core/test_measurement -q -p no:randomly -rs` repeatedly while
building T077-T084 and hit a genuinely reproducible intermittent failure: every re-enabled test
in this file, individually and in combination, would sometimes assert False right after a grant
that had just been made, with no consistent pattern across classes or run order. Ruled out (with
evidence, not assumption): the factory (isolated single-test reruns always passed), fairdm's
normalisation code (reproduced identically with a minimal repro using a plain Dataset and zero
fairdm permission code), and connection reuse (`CONN_MAX_AGE=0` made no difference).

Root cause: the directory conftest's `user` fixture is `PersonFactory()` with no override, and
`PersonFactory.is_active` is `Faker("boolean", chance_of_getting_true=80)` -
`fairdm/factories/contributors.py:72` - so roughly one user in five is created inactive.
`guardian.core.ObjectPermissionChecker.has_perm` denies every object permission to an inactive
user unconditionally, regardless of any grant. Added a local `user` fixture in
test_permissions.py forcing `is_active=True`, scoped to this file only (module-level fixture
override, `tests/conftest.py` and the directory conftest untouched).

Verified: `poetry run pytest tests/test_core/test_measurement/test_permissions.py -q -p no:randomly`
→ 21 passed, run 6 times consecutively, all clean. `poetry run pytest tests/test_core/test_measurement -q -p no:randomly`
→ 147 passed, 4 skipped, run 3 times consecutively, all clean. The 4 remaining skips, none of
them this story's:
- `test_filters.py:241` - "PartialDateField filtering requires investigation - field validation complex"
- `test_models.py:271` - "URL patterns not implemented yet - Phase 8"
- `test_models.py:716` - "Measurement detail URL not configured"
- `test_models.py:965` - "Demo ICPMSMeasurement not available"

Next: story-level final verify (`poetry run pytest tests/ -q`, `poetry run pre-commit run --all-files`)
and completion report.

Watch: `PersonFactory.is_active`'s 20%-inactive default is shared across the whole factory and
used by the directory's `user` fixture too - any *other* test file in this suite that calls
`user.has_perm(...)` without forcing `is_active=True` is exposed to the same intermittent
failure. Flagged in this story's completion report `concerns` rather than fixed, since
`fairdm/factories/contributors.py` and the directory conftest are shared, high-blast-radius files
outside this story's scope.

## 2026-08-19T12:58:00Z · Implementer US4 · decisions (recorded here, not in decisions.md)

The brief's prohibitions list forbids editing `decisions.md` for this story (it is not one of
the files the standard Implementer protocol's "append a decisions.md mini-ADR" step gets to
override). Recording the two non-obvious choices here instead.

**D-US4-1: `PersonFactory(is_active=True)` overridden locally in test_permissions.py, not fixed
at the source.** Decision: this file defines its own module-level `user` fixture
(`PersonFactory(is_active=True)`), shadowing the directory conftest's `user` for every test in
this file only. Why: `PersonFactory.is_active` (`fairdm/factories/contributors.py:72`) is
`Faker("boolean", chance_of_getting_true=80)` - about one user in five is created inactive, and
`guardian.core.ObjectPermissionChecker.has_perm` denies every object permission to an inactive
user unconditionally, independent of any grant. The correct permanent fix is
`fairdm/factories/contributors.py` or the directory conftest, both shared across the whole test
suite and outside this story's file scope - reported in `concerns` instead. Revisit if: a
follow-up fixes the shared fixture/factory directly, at which point this file's local override
becomes redundant rather than load-bearing.

**D-US4-2: Nine brief tasks landed as six commits, grouped by shared test class.** Decision:
T077+T078 landed together (both covered by `TestMeasurementPermissionInheritance`), T079+T080
landed together (`TestMeasurementGuardianIntegration`), T082+T083 landed together
(`TestMeasurementRegisteredTypePermissions`); T081, T084, T085 each landed alone. Why: splitting
a single pre-existing class's skip-removal and rewrite across two commits would mean transiently
deleting methods in one commit and restoring them in the next - keeping each class whole within
one commit was judged safer than following task numbering literally. Every commit subject names
every task it covers. Revisit if: a reviewer wants literal one-task-one-commit granularity.

## 2026-08-19T13:15:00Z · Implementer US5 · T052/T053

Did: Moved every filter `MeasurementFilterMixin`'s docstring advertises (dataset, sample,
polymorphic_ctype, search, description, date_after, date_before) onto the mixin itself, and made
it a `django_filters.FilterSet` subclass with a `Meta` that names no model - the same shape
`SampleFilterMixin` already uses, for the same reason (a plain class carries no
`declared_filters` for the metaclass to collect). `MeasurementFilter` now supplies only its own
`Meta.model`; every filter it used to declare is inherited.
Verified: `poetry run pytest tests/test_core/test_measurement/test_filters.py -q -p no:randomly`
- 9 passed, 1 skipped. `poetry run ruff check` clean on both changed files.
Next: T054-T056 (form dataset-scoping tests).
Watch: none.

## 2026-08-19T13:15:00Z · Implementer US5 · T054/T055/T056

Did: Added `TestMeasurementFormDatasetChoices` to test_forms.py - an entitled user offers exactly
their entitled (private) dataset, no user offers no dataset at all, and scoping derives from the
request's own user rather than any other authenticated user's entitlement. `MeasurementFormMixin`
(forms.py:76) already implements all three; no production code changed for these three tasks.
Verified: `poetry run pytest tests/test_core/test_measurement/test_forms.py -k
TestMeasurementFormDatasetChoices -q -p no:randomly` - 3 passed.
Next: T057/T058 (help_text typo).
Watch: none.

## 2026-08-19T13:15:00Z · Implementer US5 · T057/T058 and T059/T060

Did: `MeasurementForm.Meta` declared `help_text = {...}`; Django reads `help_texts` (plural), so
all four guidance strings were silently dropped. Renamed the attribute. Separately,
`MeasurementFormMixin`'s "add another" widget reversed `admin:core_dataset_add`, which does not
resolve (the dataset app's admin URL name is `admin:dataset_dataset_add`) - `reverse_lazy` defers
evaluation, so nothing had forced it to raise. Fixed the name. Both fixes verified RED-then-GREEN
against a new test each (`TestMeasurementFormHelpText`, `TestMeasurementFormDatasetAddAnotherUrl`).
Verified: `poetry run pytest tests/test_core/test_measurement/test_forms.py -q -p no:randomly` -
16 passed. `poetry run ruff check` clean.
Next: T061-T063 (registry wiring).
Watch: none.

## 2026-08-19T13:15:00Z · Implementer US5 · T061/T062/T063

Did: `FormFactory.get_base_form_class()` and `FilterFactory.get_base_filterset_class()`
(`fairdm/registry/factories.py:172`, `:479`) had a Sample branch only; a measurement type
registered with no `form_class`/`filterset_class` of its own fell through to a bare
`ModelForm`/`FilterSet`, losing `MeasurementFormMixin`'s widget configuration and dataset scoping
and `MeasurementFilterMixin`'s declared filters entirely. Added the Measurement branch to each,
mirroring the Sample branch's shape. New tests
(`TestFormFactoryMeasurementBranch`, `TestFilterFactoryMeasurementBranch` in
`tests/test_registry/test_factories.py`, per the brief's instruction to place them there) build
straight from the factories against a demo measurement type and assert the mixins' own behaviour
is present, not merely that generation runs without error.
Verified: `poetry run pytest tests/test_registry/test_factories.py -q -p no:randomly` - 53
passed. `poetry run pytest tests/test_registry -q -p no:randomly` - 243 passed. `poetry run
pytest tests/test_core/test_sample tests/test_core/test_measurement/test_config.py
tests/test_core/test_measurement/test_admin_registry.py -q -p no:randomly` - 278 passed, 7
skipped (checked for collateral impact on the Sample branch and on the measurement config/admin
registry paths - none found).
Next: T115 (dataset-choice privacy fix).
Watch: none.

## 2026-08-19T13:15:00Z · Implementer US5 · T115

Did: `MeasurementFilterMixin.__init__` assigned `Dataset.all_objects.all()` to the "dataset"
filter's choices unconditionally, with no reference to the requesting reader - offering the title
of every private dataset in the portal to anyone who could reach a filter set built on the mixin,
and (after T063) that reaches every registry-generated measurement filter set. `FilterSet` accepts
`request` as a constructor keyword natively (no `kwargs.pop` needed, unlike the form mixin).
Scoped through the requesting reader's `dataset.change_dataset` entitlement when `self.request`
carries an authenticated user, and left the privacy-first default manager (`Dataset.objects`)
alone otherwise - the same contract `MeasurementFormMixin` already holds, per the brief's
instruction to copy it. New tests: an entitled reader is offered exactly their entitled private
dataset and not one they hold no rights over; a reader with no entitlement (no request at all) is
offered no private dataset.

**D-US5-1 (recorded here; `decisions.md` is prohibited for this story): the fix breaks three
pre-existing tests that assumed the defect.** `TestMeasurementFilterDatasetFiltering::
test_filter_by_dataset`, `TestMeasurementFilterCombinedFilters::
test_combined_filters_dataset_and_sample`, and `TestMeasurementFilterMixinUsage::
test_custom_filter_inherits_from_mixin` (all in test_filters.py) each build a filter set with a
private dataset and no request at all, and assert `filterset.is_valid()`. That assertion now fails
for exactly the reason T115 exists: an anonymous reader is no longer offered a private dataset as
a filter choice. None of the three is named by any task in this story as one to replace, and I did
not author them, so per the Implementer protocol they are left exactly as they stood rather than
edited to fit the fix. They are stale evidence of the old (insecure) contract, now correctly red.
The mechanical fix is to pass `request=<entitled user's request>` through each of the three call
sites; flagged in this report's `concerns` rather than done here, since none of the three tasks
naming this file authorize touching those tests. Revisit if: a reviewer wants them repaired in the
same PR rather than triaged separately.

Verified: `poetry run pytest tests/test_core/test_measurement/test_filters.py -k
TestMeasurementFilterMixinDatasetPrivacy -q -p no:randomly` - 2 passed (the new behaviour).
`poetry run pytest tests/test_core/test_measurement/test_filters.py -q -p no:randomly` - 8 passed,
3 failed (the three pre-existing tests above), 1 skipped (full-file run, to identify exactly which
pre-existing tests the fix affects). `poetry run ruff check` clean on both changed files.
Next: none - this is the last task in the brief. Full-suite verify and pre-commit remain for the
completion report.
Watch: the three failing pre-existing tests named above; not fixed in this story, reported in
`concerns`.

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

## 2026-08-19T12:12:16Z · Implementer US1 · T030/T034

Did: `BaseMeasurementConfiguration` declared fixed `form_fields`/`table_fields`/`filterset_fields`,
which meant `ModelConfiguration.resolve_fields()` never fell back to a registered type's own
`fields` list for those three components - `XRFMeasurementConfig`'s own fields (`element`,
`concentration_ppm`, ...) never reached the generated form, table or filterset, only the fields
every measurement has. Confirmed by direct probe against the running registry before writing a
test. Added `BaseMeasurementConfiguration.resolve_fields()`, appending the type's own fields for
`form`/`table`/`filterset` only - `admin`'s generated `list_display` already drew from `fields`
directly (no `admin_list_display` override on the base config) and already carried a type's own
fields, confirmed by the same probe, so it is untouched. Strengthened
`tests/test_core/test_measurement/test_config.py`'s four `test_auto_generated_*_includes_*`
tests with new sibling tests asserting a named own field (`element`/`concentration_ppm`) is
present on each generated form/table/filterset/admin (T030), and replaced T034's
`hasattr(config, "table_fields")`-style checks with assertions that `"name"`/`"sample"`/`"dataset"`
are literally present in `config.table_fields`/`form_fields`/`filterset_fields`.

Verified: confirmed RED first by `git stash push` on the `config.py` fix alone and running
`poetry run pytest tests/test_core/test_measurement/test_config.py -q -p no:randomly -k
own_fields` → 3 failed for the right reason (form/filterset/table missing `element`), 1 passed
(admin, already correct). Restored the fix (`git stash pop`) and reran
`poetry run pytest tests/test_core/test_measurement/test_config.py -q -p no:randomly` → 16 passed.
`poetry run ruff check` + `ruff format --check` on both touched files → clean.

Next: T025/T026/T028/T029 (the bare-measurement refusal routes) and T032/T033 (admin type
selection reads the registry).

Watch: `fairdm/core/measurement/config.py` and its test file are not in this story's prohibited
list, so this was in scope; flagging here in case another concurrent story also touches
`BaseMeasurementConfiguration`.

## 2026-08-19T12:15:20Z · Implementer US1 · T036/T037/T038

Did: the audit's largest finding for this story - two administrative base classes existed for
measurement types, and the registry enforced the wrong one. `fairdm/core/measurement/admin.py`
defines `MeasurementChildAdmin` (176 lines: inlines, fieldsets, autocomplete, readonly fields) and
is what `fairdm.core.measurement.admin.MeasurementParentAdmin` (the class actually registered with
`admin.site` - confirmed via `admin.site._registry[Measurement]` before touching anything) already
uses. `fairdm/core/admin.py` carried a two-line `MeasurementAdmin` stub and a second,
never-registered `MeasurementParentAdmin` (its `@admin.register` commented out) built from
`get_subclasses()` rather than the registry. Both registry references pointed at the two-line stub:
validation (`fairdm/registry/config.py:377`, aliasing the stub in as `MeasurementChildAdmin`) and
generation (`fairdm/registry/factories.py:803`). A portal supplying `MeasurementChildAdmin` - the
class the docstring and both doc pages actually tell a developer to inherit - was refused, with a
message naming the two-line stub instead.

T036 (test-first): rewrote `tests/test_registry/test_config.py::TestAdminInheritanceValidation`'s
three Measurement-admin tests. `test_measurement_with_correct_admin_class_passes` and
`test_autogenerated_measurement_admin_inherits_from_child_admin` imported the stub under the real
class's name (`from fairdm.core.admin import MeasurementAdmin as MeasurementChildAdmin`), so both
asserted against the wrong class by construction and passed whether or not the registry checked
against the configured base; now both import `MeasurementChildAdmin` from
`fairdm.core.measurement.admin` under its own name.
`test_measurement_with_wrong_admin_class_raises_error`'s message assertion now expects
"MeasurementChildAdmin". Ran alone first and confirmed 3 failures for the right reason (old
config.py still checked/named the stub) before touching implementation.

T037: `fairdm/registry/config.py::ModelConfiguration._validate_admin_inheritance` now imports
`MeasurementChildAdmin` from `fairdm.core.measurement.admin` and the refusal message names
`MeasurementChildAdmin`, not `MeasurementAdmin`.

T038: `fairdm/registry/factories.py::PolymorphicAdminMixin._get_admin_base_class` (the branch that
generates an admin for a type supplying none) now imports and returns
`fairdm.core.measurement.admin.MeasurementChildAdmin`, matching the Sample branch immediately above
it, which already used `SampleChildAdmin` correctly - this was the asymmetry the audit named.
Checked every importer of the two `fairdm/core/admin.py` classes first
(`grep -rn "MeasurementAdmin\b"` across the tree): only the two registry references above and
`tests/registry_models/admin.py` (a test-support admin module, not one of this story's prohibited
test files) imported the stub, to build `ConcreteMeasurementAdmin` for the registry test suite's
own concrete type - repointed to `fairdm.core.measurement.admin.MeasurementChildAdmin`. Deleted
`MeasurementAdmin` and the commented-out `MeasurementParentAdmin` from `fairdm/core/admin.py`,
along with the imports (`PolymorphicChildModelAdmin`, `PolymorphicChildModelFilter`,
`PolymorphicParentModelAdmin`, `Measurement`, `get_subclasses`) that only they used -
`DescriptionInline`/`DateInline` (dataset-related, pre-existing, out of this story's scope) are the
only classes left in that file and needed none of them.

Verified: `poetry run pytest tests/test_registry/test_config.py::TestAdminInheritanceValidation -q
-p no:randomly` → 3 failed for the right reason before T037, 8 passed after T037+T038.
`poetry run pytest tests/test_registry/ tests/test_core/test_measurement/test_config.py
tests/test_core/test_sample -q -p no:randomly` → 513 passed, 7 skipped.
`poetry run pytest tests/test_core/test_measurement -q -p no:randomly` → 134 passed, 17 skipped
(unchanged skip count from the story's baseline run). `poetry run ruff check` +
`ruff format --check` on every touched file → clean. `grep -rn "from fairdm.core.admin import"`
across the tree → no remaining importers of the deleted names.

Next: T025/T026/T028/T029 (the bare-measurement refusal routes) and T032/T033 (admin type
selection reads the registry).

Watch: none outstanding. `DescriptionInline`/`DateInline` in `fairdm/core/admin.py` are themselves
unreferenced outside that file (confirmed by grep) but are dataset-related and outside this
story's scope - left untouched and not raised as a concern, since a plain unused-class question
for a different domain isn't this story's finding to make.

## 2026-08-19T12:18:16Z · Implementer US1 · T025/T032/T033

Did: added `tests/test_core/test_measurement/test_admin_registry.py` rather than extending
`tests/test_core/test_measurement/test_admin.py` - that file is on this story's prohibited list
(owned by a concurrently running story) even though T025 and T032 name it in `tasks.md`. A new
file carries zero merge-conflict risk with whatever that other story lands there, which is the
concern the prohibition protects against.

T033: `MeasurementParentAdmin.get_child_models()` already reads `registry.measurements`
(`fairdm/core/measurement/admin.py:172-176`) - confirmed by monkeypatching the registry property
to a sentinel list and observing the admin's child models change to match it, which the existing
`assert len(child_models) > 0` coverage could not distinguish from a hardcoded non-empty list. No
implementation change.

T032: registered `tests.registry_models.models.ConcreteMeasurement` (a real, installed-app type,
"the shape a portal actually registers" per its own docstring) via `registry.register()` inside
the test, standing in for a type registered from outside the framework. Asserted it appears among
`get_child_models()`, that a registered `ConcreteSample` (non-measurement) does not, and that the
unregistered base `Measurement` does not. `tests/test_core/test_measurement/conftest.py`'s local
`clean_registry` fixture only snapshots/restores `registry._registry` around the test rather than
clearing it first (unlike `tests/test_registry/conftest.py`'s fixture of the same name, which
empties it) - written the assertions to work with either registry state (framework types stay
registered during the test) rather than assuming an empty registry.

T025: the administrative-interface route was already refused - `Measurement` is never in
`registry.measurements`, so the parent admin's add view 403s on the base content type the same
way it would for any unregistered model. No implementation change; this route was untested.

Verified: `poetry run pytest tests/test_core/test_measurement/test_admin_registry.py -q -p
no:randomly` → 6 passed. `poetry run ruff check` + `ruff format` (one file needed reformatting,
applied and reconfirmed clean) on the new file.

Next: T026/T028/T029 (the bare-measurement manager and form refusal routes).

Watch: none outstanding.

## 2026-08-19T12:20:49Z · Implementer US1 · T026/T028

Did: closed the manager route around the base-Measurement refusal. `Measurement.objects.create()`
produced a bare record, because `clean()` (`models.py:111`) only runs when something calls it or
`full_clean()` - forms and the admin do, the manager and a bare `.save()` do not.

The natural home for this guard is `models.py`/`managers.py` (the working pattern already landed
for `Sample`: `fairdm/core/sample/models.py`'s `block_base_sample_creation`, a `pre_save` receiver
declared right beside `Sample.clean()`), but both files are on this story's prohibited list (owned
by a concurrently running story). Added the equivalent guard,
`block_base_measurement_creation`, to `fairdm/core/measurement/apps.py` instead, connected via
`AppConfig.ready()` with `sender=Measurement` - the one mechanism that also covers Django fixture
deserialization (`django.core.serializers` sends `pre_save` on every raw object before saving it),
and is scoped so a registered subclass's own save is untouched (a subclass instance sends its own
class on save, never `Measurement`). The message text mirrors `Measurement.clean()`'s exactly;
declared as a new module-level constant in `apps.py` rather than imported from `models.py`, for the
same file-scope reason.

New file `tests/test_core/test_measurement/test_managers.py` (mirrors `managers.py`; `test_models.py`
is prohibited) proves three routes: `Measurement.objects.create()`, a bare `Measurement().save()`,
and deserializing a raw fixture row for the base model (T026's "no fixture in the framework creates
one", read as Django fixture loading rather than a pytest fixture, matching the Sample precedent's
`test_fixture_loading_refuses_a_bare_sample`).

Verified: confirmed RED for the right reason before implementing - `poetry run pytest
tests/test_core/test_measurement/test_managers.py -q -p no:randomly` → first two tests "DID NOT
RAISE ValidationError" (the bug), third hit an unrelated `IntegrityError: NOT NULL constraint
failed: measurement_measurement.added` (the fixture-loading route skips `auto_now_add`, and would
never be reached once the guard fires before the INSERT). After the `apps.py` change: same command
→ 3 passed. `poetry run pytest tests/test_core/test_measurement tests/test_registry
tests/test_factories -q -p no:randomly` → 458 passed, 17 skipped, no regressions from a
framework-wide `pre_save` receiver. `poetry run ruff check` + `ruff format` (one auto-fix, an
f-string for a percent-format lint) on both touched files → clean.

Next: T029 (the form's refusal message).

Watch: the natural, single-file location for this guard is `fairdm/core/measurement/models.py`,
alongside `Measurement.clean()` (the exact shape already used for `Sample`). If the story owning
`models.py` lands its own change there before this merges, Forge's convergence pass may want to
fold `apps.py`'s guard into `models.py` to match the Sample precedent - flagging so it isn't
mistaken for a second, competing mechanism.

## 2026-08-19T12:22:22Z · Implementer US1 · T029

Did: `test_form_prevents_base_measurement_instantiation`
(`tests/test_core/test_measurement/test_forms.py`) only asserted `not form.is_valid()`. Probed the
actual `form.errors` first: the test's dataset is deliberately private and the form is built with
no `request`, so `MeasurementFormMixin`'s dataset-choice scoping alone puts a `"dataset"` error on
the form independently of the base-Measurement refusal - the old assertion passed whether or not
the refusal fired at all. The probe also confirmed the refusal message
("Cannot create base Measurement instances directly...") appears twice in `form.errors["__all__"]`,
once from `MeasurementForm.clean()` and once from the model's own `clean()` via `_post_clean()` -
exactly the duplicate rendering `tasks.md` names. Rewrote the test to assert the message
("subclass"/"directly") is present in `__all__`, alongside the existing `is_valid()` check.

Deviation from `tasks.md`'s T029 text: did not delete `MeasurementForm.clean()`. That edit is in
`fairdm/core/measurement/forms.py`, which is on this story's prohibited list (owned by a
concurrently running story). Only the test-side fix (asserting on the message) is in this story's
scope per the brief's acceptance criterion, which is scoped to the test's assertion and does not
itself require the form-side cleanup. The duplicate `__all__` entry remains; noted as a concern
for whichever story owns `forms.py`.

Verified: `poetry run pytest tests/test_core/test_measurement/test_forms.py -q -p no:randomly` →
11 passed. `poetry run ruff check` + `ruff format --check` on the touched file → clean.

Next: full-repo verify (`poetry run pytest tests/ -q` and `poetry run pre-commit run --all-files`)
for the story's completion report. All eleven of this story's tasks are now committed.

Watch: `MeasurementForm.clean()` (`fairdm/core/measurement/forms.py`) still duplicates the
base-Measurement refusal the model's own `clean()` already raises via `_post_clean()` - harmless
today (the duplicate error text is deduplicated by nothing, so a form re-render would show the
message twice), but it is dead logic once a form's `_post_clean()` runs, and `tasks.md`'s T029
already names the fix. Left alone because `forms.py` is out of this story's scope; flagging for
whichever story owns it.

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

## 2026-08-19T12:10:00Z · Implementer US8 · T095/T096

Did: FR-040 required the measurement admin list to be narrowable by dataset, sample and
measurement type; `list_filter` carried only `"added"` on both the child and parent admin classes,
and the three tests that looked like coverage (`TestMeasurementAdminFilters.test_filter_by_dataset`,
`test_filter_by_sample`, `test_filter_by_polymorphic_type`) accepted the `measurement_admin` fixture
and never used it, asserting `Measurement.objects.filter(...)` directly instead. Rewrote all three
to exercise the real registered `MeasurementParentAdmin` instance
(`django.contrib.admin.site._registry[Measurement]`) via `get_changelist_instance(request)` with
the filter's query-string parameter set, per FR-040's own acceptance wording ("asserted THROUGH the
administrative interface, not by querying the model directly"). Added two further tests asserting
`"dataset"` and `"sample"` are present in `list_filter` on both `MeasurementChildAdmin` and
`MeasurementParentAdmin` directly (T096's own acceptance: "the administrative classes are read").
Added `"dataset"` and `"sample"` to `list_filter` on both classes in `fairdm/core/measurement/admin.py`.

While proving `test_filter_by_dataset` green, found that Django's default `RelatedFieldListFilter`
draws its choices from `Dataset`'s default manager, which excludes private datasets (FR-019,
`fairdm/core/dataset/models.py:159` `DatasetManager`) - and a dataset's own model default is
private (documented in `tests/test_core/test_measurement/conftest.py`'s `dataset` fixture). With
only private datasets present, `has_output()` is `False` for fewer than two choices, and Django
silently drops the filter entirely rather than degrading to "no visible choices" - the query
parameter is consumed and discarded during filter construction regardless, so a hand-built
`?dataset__id__exact=` URL is silently ignored too. That would have made FR-040's dataset narrowing
fail in the ordinary case. Added `MeasurementDatasetListFilter(admin.RelatedFieldListFilter)` in
`admin.py`, overriding `field_choices` to draw from `Dataset.all_objects` instead - the same
reasoning `DatasetAdmin.get_queryset` already documents for itself ("the administrative interface
is where a portal is repaired and needs to see everything", FR-019a). `sample` needed no equivalent
fix: `Sample`'s own default manager carries no visibility exclusion (visibility is a `Dataset`-level
concept).

Verified: `poetry run pytest tests/test_core/test_measurement/test_admin.py -q -p no:randomly` →
25 passed. `poetry run ruff check fairdm/core/measurement/admin.py
tests/test_core/test_measurement/test_admin.py` → all checks passed. `poetry run ruff format --check`
on both files → already formatted (after one `ruff format` pass that only re-wrapped two
pre-existing search tests' argument lists, no content change).

Next: T097/T098 - inline row caps.

Watch: `MeasurementDatasetListFilter` is scoped to the `dataset` FK only; if a future filter is
added on another privacy-managed relation, the same silent-drop failure mode applies and needs the
same treatment.

## 2026-08-19T12:35:00Z · Implementer US8 · T097/T098

Did: inline row caps for descriptions, dates and identifiers were hard-coded to 6, 6 and 3,
but the specification requires each to offer no more rows than its own vocabulary has member
types - measured: descriptions 4 (`MeasurementConditions`, `MeasurementSetup`,
`MeasurementTearDown`, `Other`), dates 2 (`Setup`, `TearDown`), identifiers 1 (`DOI`). Changed
`MeasurementDescriptionInline.max_num`, `MeasurementDateInline.max_num` and
`MeasurementIdentifierInline.max_num` in `fairdm/core/measurement/admin.py` to
`len(<Model>.VOCABULARY.values)` each, so the cap tracks the vocabulary rather than repeating a
number by hand. Left `MeasurementContributionInline` with no `max_num` at all - contributions are
NOT capped, per the design review correction in the brief: a contribution credits a person or
organisation, not a vocabulary member, and capping it at a role vocabulary's size would limit how
many contributors a measurement can have.

Added `TestMeasurementAdminInlineRowCaps` asserting each of the three capped inlines' `max_num`
equals its vocabulary's member count, and a fourth test asserting
`MeasurementContributionInline.max_num is None`. Also added
`test_inline_contribution_can_be_added_and_changed` to `TestMeasurementAdminInlines` - the
existing inline tests covered creation for descriptions, dates and identifiers but nothing at all
for contributions, and T097's acceptance names all four record kinds and both "added and changed".

Verified: `poetry run pytest tests/test_core/test_measurement/test_admin.py -q -p no:randomly` →
30 passed (was 3 failing for the expected reason - `max_num` mismatched the vocabulary count -
before the admin.py change). `poetry run ruff check` and `ruff format --check` on both touched
files → all checks passed / already formatted.

Next: T099 - every registered measurement type offers the same attached-record editors.

Watch: none outstanding.

## 2026-08-19T12:45:00Z · Implementer US8 · T099

Did: added `TestMeasurementAdminSharedInlines.test_every_registered_type_offers_the_same_inlines`,
asserting that every registered measurement type's admin class (`ExampleMeasurementAdmin`,
`XRFMeasurementAdmin`, `ICP_MS_MeasurementAdmin`, read from `registry.measurements` and the real
`django.contrib.admin.site` registry) has `inlines == MeasurementChildAdmin.inlines`. No
implementation change was needed: none of the concrete admin classes in `fairdm_demo/admin.py`
override `inlines`, so they already inherit the shared set. Checked the assertion was not
tautological by temporarily setting `inlines = []` on `XRFMeasurementAdmin` in
`fairdm_demo/admin.py`, confirming the test fails with a clear diff, then reverting - `git diff`
on that file is empty.

Verified: `poetry run pytest tests/test_core/test_measurement/test_admin.py -q -p no:randomly` →
31 passed. `poetry run ruff check` / `ruff format --check` on the touched test file → all checks
passed / already formatted.

Next: T100/T101 - the administrative list names each row's measurement type.

Watch: none outstanding.

## 2026-08-19T12:55:00Z · Implementer US8 · T100/T101

Did: `measurement_type` was already in `list_display` on both `MeasurementChildAdmin` and
`MeasurementParentAdmin`, and the `measurement_type()` method existed (`admin.py:164`/`:211`), but
the only covering test (`test_list_display_configured`) never asserted the type column at all.
Added `TestMeasurementAdminTypeColumn` with three tests: `"measurement_type"` is present in
`list_display` on both admin classes, and `measurement_admin.measurement_type(obj)` - called the
way the changelist itself resolves a `list_display` callable - names the real polymorphic type
(`XRFMeasurement`'s and `ICP_MS_Measurement`'s own `verbose_name`, not the base `Measurement`'s,
and not equal to each other). No production change was needed - T101's column already existed;
only the test was missing. Checked the presence assertion was not tautological by temporarily
removing `"measurement_type"` from `MeasurementChildAdmin.list_display`, confirming the test fails,
then reverting - `git diff` on `admin.py` is empty.

Verified: `poetry run pytest tests/test_core/test_measurement/test_admin.py -q -p no:randomly` →
34 passed. `poetry run ruff check` / `ruff format --check` on the touched test file → all checks
passed / already formatted.

Next: run the full repo suite once and pre-commit for the completion report - all seven tasks in
this story (T095-T101) are now done.

Watch: none outstanding.

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

## 2026-08-19T12:43:00Z · Implementer US4 · T077-T078

Did: Read tests/test_core/test_measurement/test_permissions.py in full and
fairdm/core/measurement/permissions.py, fairdm/core/permissions.py, fairdm/core/utils.py per
ritual. Ran the baseline (`poetry run pytest tests/test_core/test_measurement -q -p no:randomly`) -
130 passed, 17 skipped, green. Removed TestMeasurementPermissionInheritance's skip (its reason
claimed "change/delete permission mapping needs debugging") and observed all 6 tests pass
unmodified, confirming the reason was false rather than something needing a fix. Rewrote the
class's 4 core tests (view/change/delete + none) plus test_multiple_measurements_inherit_from_same_dataset
against fairdm.core.utils.assign_perm - the entry point this codebase's own MeasurementPermissionBackend
implies - rather than guardian.shortcuts directly.

Verified: `poetry run pytest tests/test_core/test_measurement/test_permissions.py::TestMeasurementPermissionInheritance -q -p no:randomly`
→ 5 passed (exit 0).

Next: T079-T080 (TestMeasurementGuardianIntegration).

Watch: none yet - the assign-then-check pattern in this file later turned out to intermittently
fail for an unrelated reason; see the T085 entry.

## 2026-08-19T12:45:00Z · Implementer US4 · T079-T080

Did: Removed TestMeasurementGuardianIntegration's skip and ran it unmodified first (RED,
observed for the right reason): all 4 tests failed with `django.contrib.auth.models.Permission.DoesNotExist`
raised from `guardian.shortcuts.assign_perm` - the exact claim the skip made (guardian cannot
grant a permission directly on a polymorphic subclass instance), though the concrete exception
differs from the skip text's "WrongAppError" (same root cause, different code path: `assign_perm`
vs `has_perm`). Rewrote all 4 tests plus a new 5th
(test_direct_permission_coexists_with_inherited_dataset_permission) against
fairdm.core.utils.assign_perm/remove_perm/get_perms.

Verified: `poetry run pytest tests/test_core/test_measurement/test_permissions.py::TestMeasurementGuardianIntegration -q -p no:randomly`
→ 5 passed (exit 0); this class is included in the 6 clean full-file repeat runs recorded under T085.

Next: T081 (TestCrossDatasetPermissionBoundaries).

## 2026-08-19T12:47:00Z · Implementer US4 · T081

Did: Removed TestCrossDatasetPermissionBoundaries's skip. Its reason claimed the factory fails
building a Measurement whose sample belongs to a different dataset - confirmed false directly:
`ExampleMeasurementFactory(dataset=dataset_a, sample=sample_b)` builds without complaint on every
run, with and without the skip. Switched its grants to fairdm.core.utils.assign_perm for
consistency with the rest of the file and removed the now-dead top-level `guardian.shortcuts`
import.

Verified: `poetry run pytest tests/test_core/test_measurement/test_permissions.py::TestCrossDatasetPermissionBoundaries -q -p no:randomly`
→ 3 passed (exit 0); this class is included in the 6 clean full-file repeat runs recorded under
T085. Before that fix, this class's own tests intermittently failed for the reason documented
under T085 - not a defect in the isolation logic itself.

Next: T082-T083 (registered-type grant/consult).

## 2026-08-19T12:50:00Z · Implementer US4 · T082-T083

Did: Added TestMeasurementRegisteredTypePermissions (new class, not a re-enable): a grant via
fairdm.core.utils.assign_perm on a registered type (ExampleMeasurement) reads back identically on
the instance and on the bare record (`Measurement.objects.non_polymorphic().get(pk=...)`) (T082).
Added a test proving the negative space directly rather than assuming it: guardian's own
`assign_perm` still raises `Permission.DoesNotExist` for the identical call with no normalisation
in front of it. Added a third test unit-testing `fairdm.core.utils.get_permission_target` itself -
confirms it retargets an ExampleMeasurement instance to the base Measurement record (T083).

Verified: `poetry run pytest tests/test_core/test_measurement/test_permissions.py::TestMeasurementRegisteredTypePermissions -q -p no:randomly`
→ 3 passed (exit 0); this class is included in the 6 clean full-file repeat runs recorded under
T085.

Next: T084 (backend registration).

## 2026-08-19T12:52:00Z · Implementer US4 · T084

Did: Added TestMeasurementPermissionBackendRegistration - a settings-only test (no DB) asserting
`fairdm.core.measurement.permissions.MeasurementPermissionBackend`'s dotted path is present in
`settings.AUTHENTICATION_BACKENDS`. No production code change; the backend was already registered
(fairdm/conf/settings/auth.py:58), nothing asserted it before.

Verified: `poetry run pytest tests/test_core/test_measurement/test_permissions.py::TestMeasurementPermissionBackendRegistration -q -p no:randomly`
→ 1 passed (exit 0).

Next: T085 (final skip count + suite check).

## 2026-08-19T12:55:00Z · Implementer US4 · T085

Did: Confirmed zero `@pytest.mark.skip` remain in test_permissions.py. Ran
`poetry run pytest tests/test_core/test_measurement -q -p no:randomly -rs` repeatedly while
building T077-T084 and hit a genuinely reproducible intermittent failure: every re-enabled test
in this file, individually and in combination, would sometimes assert False right after a grant
that had just been made, with no consistent pattern across classes or run order. Ruled out (with
evidence, not assumption): the factory (isolated single-test reruns always passed), fairdm's
normalisation code (reproduced identically with a minimal repro using a plain Dataset and zero
fairdm permission code), and connection reuse (`CONN_MAX_AGE=0` made no difference).

Root cause: the directory conftest's `user` fixture is `PersonFactory()` with no override, and
`PersonFactory.is_active` is `Faker("boolean", chance_of_getting_true=80)` -
`fairdm/factories/contributors.py:72` - so roughly one user in five is created inactive.
`guardian.core.ObjectPermissionChecker.has_perm` denies every object permission to an inactive
user unconditionally, regardless of any grant. Added a local `user` fixture in
test_permissions.py forcing `is_active=True`, scoped to this file only (module-level fixture
override, `tests/conftest.py` and the directory conftest untouched).

Verified: `poetry run pytest tests/test_core/test_measurement/test_permissions.py -q -p no:randomly`
→ 21 passed, run 6 times consecutively, all clean. `poetry run pytest tests/test_core/test_measurement -q -p no:randomly`
→ 147 passed, 4 skipped, run 3 times consecutively, all clean. The 4 remaining skips, none of
them this story's:
- `test_filters.py:241` - "PartialDateField filtering requires investigation - field validation complex"
- `test_models.py:271` - "URL patterns not implemented yet - Phase 8"
- `test_models.py:716` - "Measurement detail URL not configured"
- `test_models.py:965` - "Demo ICPMSMeasurement not available"

Next: story-level final verify (`poetry run pytest tests/ -q`, `poetry run pre-commit run --all-files`)
and completion report.

Watch: `PersonFactory.is_active`'s 20%-inactive default is shared across the whole factory and
used by the directory's `user` fixture too - any *other* test file in this suite that calls
`user.has_perm(...)` without forcing `is_active=True` is exposed to the same intermittent
failure. Flagged in this story's completion report `concerns` rather than fixed, since
`fairdm/factories/contributors.py` and the directory conftest are shared, high-blast-radius files
outside this story's scope.

## 2026-08-19T12:58:00Z · Implementer US4 · decisions (recorded here, not in decisions.md)

The brief's prohibitions list forbids editing `decisions.md` for this story (it is not one of
the files the standard Implementer protocol's "append a decisions.md mini-ADR" step gets to
override). Recording the two non-obvious choices here instead.

**D-US4-1: `PersonFactory(is_active=True)` overridden locally in test_permissions.py, not fixed
at the source.** Decision: this file defines its own module-level `user` fixture
(`PersonFactory(is_active=True)`), shadowing the directory conftest's `user` for every test in
this file only. Why: `PersonFactory.is_active` (`fairdm/factories/contributors.py:72`) is
`Faker("boolean", chance_of_getting_true=80)` - about one user in five is created inactive, and
`guardian.core.ObjectPermissionChecker.has_perm` denies every object permission to an inactive
user unconditionally, independent of any grant. The correct permanent fix is
`fairdm/factories/contributors.py` or the directory conftest, both shared across the whole test
suite and outside this story's file scope - reported in `concerns` instead. Revisit if: a
follow-up fixes the shared fixture/factory directly, at which point this file's local override
becomes redundant rather than load-bearing.

**D-US4-2: Nine brief tasks landed as six commits, grouped by shared test class.** Decision:
T077+T078 landed together (both covered by `TestMeasurementPermissionInheritance`), T079+T080
landed together (`TestMeasurementGuardianIntegration`), T082+T083 landed together
(`TestMeasurementRegisteredTypePermissions`); T081, T084, T085 each landed alone. Why: splitting
a single pre-existing class's skip-removal and rewrite across two commits would mean transiently
deleting methods in one commit and restoring them in the next - keeping each class whole within
one commit was judged safer than following task numbering literally. Every commit subject names
every task it covers. Revisit if: a reviewer wants literal one-task-one-commit granularity.

## 2026-08-19T13:05:20Z · Implementer US9 · T104/T106/T107/T108

Did: added `tests/test_core/test_measurement/test_querysets.py` (new file — does not touch
`test_models.py`, owned by a concurrently running story) with four test classes:
- `TestWithRelatedQueryCountDoesNotGrow` (T104) — counts queries accessing sample, dataset and
  contributors at 5 and 25 measurements via `with_related()` and asserts the counts are equal.
- `TestWithMetadataQueryCountDoesNotGrow` (T106) — same pattern for `with_metadata()` against
  descriptions, dates and identifiers.
- `TestWithMetadataPrefetchesRecords` (T107) — proves `with_metadata()` genuinely prefetches by
  showing relation access after evaluation costs zero further queries, contrasted with the same
  access against a plain queryset (which does requery — 1 query).
- `TestBothLoadingsComposeWithFilteringAndOrdering` (T108) — `with_related().with_metadata()`
  chained with `.filter(dataset=...).order_by("name")`; asserts the result set is both correctly
  filtered (excludes a measurement in a different dataset) and correctly ordered, and that both
  prefetches still function (zero further queries) after composing.

No production code changed. `fairdm/core/measurement/managers.py`'s `with_related()` and
`with_metadata()` already prefetch correctly (T105 was already reconciled done for the first;
T107 closes the same way for the second) — this story's job was writing tests that actually
measure the growth-invariance property FR-046 requires, not fixing code that was already right.

Verified RED before green: temporarily edited `managers.py` so both methods returned `self`
unchanged (no `select_related`/`prefetch_related`), reran the new file — 4 of 5 tests failed for
the right reason (unequal/non-zero query counts); the fifth (the T107 contrast test, which
asserts the *unoptimised* path requeries) correctly still passed. Reverted via the backed-up
original file before proceeding; `git diff --stat` on `managers.py` confirmed no net change.

Verified: `poetry run pytest tests/test_core/test_measurement/test_querysets.py -q -p no:randomly`
— 5 passed. `poetry run pytest tests/test_core/test_measurement -q -p no:randomly` — 186 passed,
4 skipped (up from the 181 passed, 4 skipped baseline; no regressions). `poetry run ruff check`
and `poetry run ruff format --check` on the new file — both clean.

Watch: `PersonFactory.is_active`'s ~20%-inactive default (recorded previously by US4, D-US4-1 in
this file) applies here too — every `PersonFactory()` used as a contributor in the new tests is
called with `is_active=True` explicitly.

Next: story-level final verify (`poetry run pytest tests/ -q`, `poetry run pre-commit run
--all-files`) and completion report.

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

## 2026-08-19T12:12:16Z · Implementer US1 · T030/T034

Did: `BaseMeasurementConfiguration` declared fixed `form_fields`/`table_fields`/`filterset_fields`,
which meant `ModelConfiguration.resolve_fields()` never fell back to a registered type's own
`fields` list for those three components - `XRFMeasurementConfig`'s own fields (`element`,
`concentration_ppm`, ...) never reached the generated form, table or filterset, only the fields
every measurement has. Confirmed by direct probe against the running registry before writing a
test. Added `BaseMeasurementConfiguration.resolve_fields()`, appending the type's own fields for
`form`/`table`/`filterset` only - `admin`'s generated `list_display` already drew from `fields`
directly (no `admin_list_display` override on the base config) and already carried a type's own
fields, confirmed by the same probe, so it is untouched. Strengthened
`tests/test_core/test_measurement/test_config.py`'s four `test_auto_generated_*_includes_*`
tests with new sibling tests asserting a named own field (`element`/`concentration_ppm`) is
present on each generated form/table/filterset/admin (T030), and replaced T034's
`hasattr(config, "table_fields")`-style checks with assertions that `"name"`/`"sample"`/`"dataset"`
are literally present in `config.table_fields`/`form_fields`/`filterset_fields`.

Verified: confirmed RED first by `git stash push` on the `config.py` fix alone and running
`poetry run pytest tests/test_core/test_measurement/test_config.py -q -p no:randomly -k
own_fields` → 3 failed for the right reason (form/filterset/table missing `element`), 1 passed
(admin, already correct). Restored the fix (`git stash pop`) and reran
`poetry run pytest tests/test_core/test_measurement/test_config.py -q -p no:randomly` → 16 passed.
`poetry run ruff check` + `ruff format --check` on both touched files → clean.

Next: T025/T026/T028/T029 (the bare-measurement refusal routes) and T032/T033 (admin type
selection reads the registry).

Watch: `fairdm/core/measurement/config.py` and its test file are not in this story's prohibited
list, so this was in scope; flagging here in case another concurrent story also touches
`BaseMeasurementConfiguration`.

## 2026-08-19T12:15:20Z · Implementer US1 · T036/T037/T038

Did: the audit's largest finding for this story - two administrative base classes existed for
measurement types, and the registry enforced the wrong one. `fairdm/core/measurement/admin.py`
defines `MeasurementChildAdmin` (176 lines: inlines, fieldsets, autocomplete, readonly fields) and
is what `fairdm.core.measurement.admin.MeasurementParentAdmin` (the class actually registered with
`admin.site` - confirmed via `admin.site._registry[Measurement]` before touching anything) already
uses. `fairdm/core/admin.py` carried a two-line `MeasurementAdmin` stub and a second,
never-registered `MeasurementParentAdmin` (its `@admin.register` commented out) built from
`get_subclasses()` rather than the registry. Both registry references pointed at the two-line stub:
validation (`fairdm/registry/config.py:377`, aliasing the stub in as `MeasurementChildAdmin`) and
generation (`fairdm/registry/factories.py:803`). A portal supplying `MeasurementChildAdmin` - the
class the docstring and both doc pages actually tell a developer to inherit - was refused, with a
message naming the two-line stub instead.

T036 (test-first): rewrote `tests/test_registry/test_config.py::TestAdminInheritanceValidation`'s
three Measurement-admin tests. `test_measurement_with_correct_admin_class_passes` and
`test_autogenerated_measurement_admin_inherits_from_child_admin` imported the stub under the real
class's name (`from fairdm.core.admin import MeasurementAdmin as MeasurementChildAdmin`), so both
asserted against the wrong class by construction and passed whether or not the registry checked
against the configured base; now both import `MeasurementChildAdmin` from
`fairdm.core.measurement.admin` under its own name.
`test_measurement_with_wrong_admin_class_raises_error`'s message assertion now expects
"MeasurementChildAdmin". Ran alone first and confirmed 3 failures for the right reason (old
config.py still checked/named the stub) before touching implementation.

T037: `fairdm/registry/config.py::ModelConfiguration._validate_admin_inheritance` now imports
`MeasurementChildAdmin` from `fairdm.core.measurement.admin` and the refusal message names
`MeasurementChildAdmin`, not `MeasurementAdmin`.

T038: `fairdm/registry/factories.py::PolymorphicAdminMixin._get_admin_base_class` (the branch that
generates an admin for a type supplying none) now imports and returns
`fairdm.core.measurement.admin.MeasurementChildAdmin`, matching the Sample branch immediately above
it, which already used `SampleChildAdmin` correctly - this was the asymmetry the audit named.
Checked every importer of the two `fairdm/core/admin.py` classes first
(`grep -rn "MeasurementAdmin\b"` across the tree): only the two registry references above and
`tests/registry_models/admin.py` (a test-support admin module, not one of this story's prohibited
test files) imported the stub, to build `ConcreteMeasurementAdmin` for the registry test suite's
own concrete type - repointed to `fairdm.core.measurement.admin.MeasurementChildAdmin`. Deleted
`MeasurementAdmin` and the commented-out `MeasurementParentAdmin` from `fairdm/core/admin.py`,
along with the imports (`PolymorphicChildModelAdmin`, `PolymorphicChildModelFilter`,
`PolymorphicParentModelAdmin`, `Measurement`, `get_subclasses`) that only they used -
`DescriptionInline`/`DateInline` (dataset-related, pre-existing, out of this story's scope) are the
only classes left in that file and needed none of them.

Verified: `poetry run pytest tests/test_registry/test_config.py::TestAdminInheritanceValidation -q
-p no:randomly` → 3 failed for the right reason before T037, 8 passed after T037+T038.
`poetry run pytest tests/test_registry/ tests/test_core/test_measurement/test_config.py
tests/test_core/test_sample -q -p no:randomly` → 513 passed, 7 skipped.
`poetry run pytest tests/test_core/test_measurement -q -p no:randomly` → 134 passed, 17 skipped
(unchanged skip count from the story's baseline run). `poetry run ruff check` +
`ruff format --check` on every touched file → clean. `grep -rn "from fairdm.core.admin import"`
across the tree → no remaining importers of the deleted names.

Next: T025/T026/T028/T029 (the bare-measurement refusal routes) and T032/T033 (admin type
selection reads the registry).

Watch: none outstanding. `DescriptionInline`/`DateInline` in `fairdm/core/admin.py` are themselves
unreferenced outside that file (confirmed by grep) but are dataset-related and outside this
story's scope - left untouched and not raised as a concern, since a plain unused-class question
for a different domain isn't this story's finding to make.

## 2026-08-19T12:18:16Z · Implementer US1 · T025/T032/T033

Did: added `tests/test_core/test_measurement/test_admin_registry.py` rather than extending
`tests/test_core/test_measurement/test_admin.py` - that file is on this story's prohibited list
(owned by a concurrently running story) even though T025 and T032 name it in `tasks.md`. A new
file carries zero merge-conflict risk with whatever that other story lands there, which is the
concern the prohibition protects against.

T033: `MeasurementParentAdmin.get_child_models()` already reads `registry.measurements`
(`fairdm/core/measurement/admin.py:172-176`) - confirmed by monkeypatching the registry property
to a sentinel list and observing the admin's child models change to match it, which the existing
`assert len(child_models) > 0` coverage could not distinguish from a hardcoded non-empty list. No
implementation change.

T032: registered `tests.registry_models.models.ConcreteMeasurement` (a real, installed-app type,
"the shape a portal actually registers" per its own docstring) via `registry.register()` inside
the test, standing in for a type registered from outside the framework. Asserted it appears among
`get_child_models()`, that a registered `ConcreteSample` (non-measurement) does not, and that the
unregistered base `Measurement` does not. `tests/test_core/test_measurement/conftest.py`'s local
`clean_registry` fixture only snapshots/restores `registry._registry` around the test rather than
clearing it first (unlike `tests/test_registry/conftest.py`'s fixture of the same name, which
empties it) - written the assertions to work with either registry state (framework types stay
registered during the test) rather than assuming an empty registry.

T025: the administrative-interface route was already refused - `Measurement` is never in
`registry.measurements`, so the parent admin's add view 403s on the base content type the same
way it would for any unregistered model. No implementation change; this route was untested.

Verified: `poetry run pytest tests/test_core/test_measurement/test_admin_registry.py -q -p
no:randomly` → 6 passed. `poetry run ruff check` + `ruff format` (one file needed reformatting,
applied and reconfirmed clean) on the new file.

Next: T026/T028/T029 (the bare-measurement manager and form refusal routes).

Watch: none outstanding.

## 2026-08-19T12:20:49Z · Implementer US1 · T026/T028

Did: closed the manager route around the base-Measurement refusal. `Measurement.objects.create()`
produced a bare record, because `clean()` (`models.py:111`) only runs when something calls it or
`full_clean()` - forms and the admin do, the manager and a bare `.save()` do not.

The natural home for this guard is `models.py`/`managers.py` (the working pattern already landed
for `Sample`: `fairdm/core/sample/models.py`'s `block_base_sample_creation`, a `pre_save` receiver
declared right beside `Sample.clean()`), but both files are on this story's prohibited list (owned
by a concurrently running story). Added the equivalent guard,
`block_base_measurement_creation`, to `fairdm/core/measurement/apps.py` instead, connected via
`AppConfig.ready()` with `sender=Measurement` - the one mechanism that also covers Django fixture
deserialization (`django.core.serializers` sends `pre_save` on every raw object before saving it),
and is scoped so a registered subclass's own save is untouched (a subclass instance sends its own
class on save, never `Measurement`). The message text mirrors `Measurement.clean()`'s exactly;
declared as a new module-level constant in `apps.py` rather than imported from `models.py`, for the
same file-scope reason.

New file `tests/test_core/test_measurement/test_managers.py` (mirrors `managers.py`; `test_models.py`
is prohibited) proves three routes: `Measurement.objects.create()`, a bare `Measurement().save()`,
and deserializing a raw fixture row for the base model (T026's "no fixture in the framework creates
one", read as Django fixture loading rather than a pytest fixture, matching the Sample precedent's
`test_fixture_loading_refuses_a_bare_sample`).

Verified: confirmed RED for the right reason before implementing - `poetry run pytest
tests/test_core/test_measurement/test_managers.py -q -p no:randomly` → first two tests "DID NOT
RAISE ValidationError" (the bug), third hit an unrelated `IntegrityError: NOT NULL constraint
failed: measurement_measurement.added` (the fixture-loading route skips `auto_now_add`, and would
never be reached once the guard fires before the INSERT). After the `apps.py` change: same command
→ 3 passed. `poetry run pytest tests/test_core/test_measurement tests/test_registry
tests/test_factories -q -p no:randomly` → 458 passed, 17 skipped, no regressions from a
framework-wide `pre_save` receiver. `poetry run ruff check` + `ruff format` (one auto-fix, an
f-string for a percent-format lint) on both touched files → clean.

Next: T029 (the form's refusal message).

Watch: the natural, single-file location for this guard is `fairdm/core/measurement/models.py`,
alongside `Measurement.clean()` (the exact shape already used for `Sample`). If the story owning
`models.py` lands its own change there before this merges, Forge's convergence pass may want to
fold `apps.py`'s guard into `models.py` to match the Sample precedent - flagging so it isn't
mistaken for a second, competing mechanism.

## 2026-08-19T12:22:22Z · Implementer US1 · T029

Did: `test_form_prevents_base_measurement_instantiation`
(`tests/test_core/test_measurement/test_forms.py`) only asserted `not form.is_valid()`. Probed the
actual `form.errors` first: the test's dataset is deliberately private and the form is built with
no `request`, so `MeasurementFormMixin`'s dataset-choice scoping alone puts a `"dataset"` error on
the form independently of the base-Measurement refusal - the old assertion passed whether or not
the refusal fired at all. The probe also confirmed the refusal message
("Cannot create base Measurement instances directly...") appears twice in `form.errors["__all__"]`,
once from `MeasurementForm.clean()` and once from the model's own `clean()` via `_post_clean()` -
exactly the duplicate rendering `tasks.md` names. Rewrote the test to assert the message
("subclass"/"directly") is present in `__all__`, alongside the existing `is_valid()` check.

Deviation from `tasks.md`'s T029 text: did not delete `MeasurementForm.clean()`. That edit is in
`fairdm/core/measurement/forms.py`, which is on this story's prohibited list (owned by a
concurrently running story). Only the test-side fix (asserting on the message) is in this story's
scope per the brief's acceptance criterion, which is scoped to the test's assertion and does not
itself require the form-side cleanup. The duplicate `__all__` entry remains; noted as a concern
for whichever story owns `forms.py`.

Verified: `poetry run pytest tests/test_core/test_measurement/test_forms.py -q -p no:randomly` →
11 passed. `poetry run ruff check` + `ruff format --check` on the touched file → clean.

Next: full-repo verify (`poetry run pytest tests/ -q` and `poetry run pre-commit run --all-files`)
for the story's completion report. All eleven of this story's tasks are now committed.

Watch: `MeasurementForm.clean()` (`fairdm/core/measurement/forms.py`) still duplicates the
base-Measurement refusal the model's own `clean()` already raises via `_post_clean()` - harmless
today (the duplicate error text is deduplicated by nothing, so a form re-render would show the
message twice), but it is dead logic once a form's `_post_clean()` runs, and `tasks.md`'s T029
already names the fix. Left alone because `forms.py` is out of this story's scope; flagging for
whichever story owns it.

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

## 2026-08-19T12:10:00Z · Implementer US8 · T095/T096

Did: FR-040 required the measurement admin list to be narrowable by dataset, sample and
measurement type; `list_filter` carried only `"added"` on both the child and parent admin classes,
and the three tests that looked like coverage (`TestMeasurementAdminFilters.test_filter_by_dataset`,
`test_filter_by_sample`, `test_filter_by_polymorphic_type`) accepted the `measurement_admin` fixture
and never used it, asserting `Measurement.objects.filter(...)` directly instead. Rewrote all three
to exercise the real registered `MeasurementParentAdmin` instance
(`django.contrib.admin.site._registry[Measurement]`) via `get_changelist_instance(request)` with
the filter's query-string parameter set, per FR-040's own acceptance wording ("asserted THROUGH the
administrative interface, not by querying the model directly"). Added two further tests asserting
`"dataset"` and `"sample"` are present in `list_filter` on both `MeasurementChildAdmin` and
`MeasurementParentAdmin` directly (T096's own acceptance: "the administrative classes are read").
Added `"dataset"` and `"sample"` to `list_filter` on both classes in `fairdm/core/measurement/admin.py`.

While proving `test_filter_by_dataset` green, found that Django's default `RelatedFieldListFilter`
draws its choices from `Dataset`'s default manager, which excludes private datasets (FR-019,
`fairdm/core/dataset/models.py:159` `DatasetManager`) - and a dataset's own model default is
private (documented in `tests/test_core/test_measurement/conftest.py`'s `dataset` fixture). With
only private datasets present, `has_output()` is `False` for fewer than two choices, and Django
silently drops the filter entirely rather than degrading to "no visible choices" - the query
parameter is consumed and discarded during filter construction regardless, so a hand-built
`?dataset__id__exact=` URL is silently ignored too. That would have made FR-040's dataset narrowing
fail in the ordinary case. Added `MeasurementDatasetListFilter(admin.RelatedFieldListFilter)` in
`admin.py`, overriding `field_choices` to draw from `Dataset.all_objects` instead - the same
reasoning `DatasetAdmin.get_queryset` already documents for itself ("the administrative interface
is where a portal is repaired and needs to see everything", FR-019a). `sample` needed no equivalent
fix: `Sample`'s own default manager carries no visibility exclusion (visibility is a `Dataset`-level
concept).

Verified: `poetry run pytest tests/test_core/test_measurement/test_admin.py -q -p no:randomly` →
25 passed. `poetry run ruff check fairdm/core/measurement/admin.py
tests/test_core/test_measurement/test_admin.py` → all checks passed. `poetry run ruff format --check`
on both files → already formatted (after one `ruff format` pass that only re-wrapped two
pre-existing search tests' argument lists, no content change).

Next: T097/T098 - inline row caps.

Watch: `MeasurementDatasetListFilter` is scoped to the `dataset` FK only; if a future filter is
added on another privacy-managed relation, the same silent-drop failure mode applies and needs the
same treatment.

## 2026-08-19T12:35:00Z · Implementer US8 · T097/T098

Did: inline row caps for descriptions, dates and identifiers were hard-coded to 6, 6 and 3,
but the specification requires each to offer no more rows than its own vocabulary has member
types - measured: descriptions 4 (`MeasurementConditions`, `MeasurementSetup`,
`MeasurementTearDown`, `Other`), dates 2 (`Setup`, `TearDown`), identifiers 1 (`DOI`). Changed
`MeasurementDescriptionInline.max_num`, `MeasurementDateInline.max_num` and
`MeasurementIdentifierInline.max_num` in `fairdm/core/measurement/admin.py` to
`len(<Model>.VOCABULARY.values)` each, so the cap tracks the vocabulary rather than repeating a
number by hand. Left `MeasurementContributionInline` with no `max_num` at all - contributions are
NOT capped, per the design review correction in the brief: a contribution credits a person or
organisation, not a vocabulary member, and capping it at a role vocabulary's size would limit how
many contributors a measurement can have.

Added `TestMeasurementAdminInlineRowCaps` asserting each of the three capped inlines' `max_num`
equals its vocabulary's member count, and a fourth test asserting
`MeasurementContributionInline.max_num is None`. Also added
`test_inline_contribution_can_be_added_and_changed` to `TestMeasurementAdminInlines` - the
existing inline tests covered creation for descriptions, dates and identifiers but nothing at all
for contributions, and T097's acceptance names all four record kinds and both "added and changed".

Verified: `poetry run pytest tests/test_core/test_measurement/test_admin.py -q -p no:randomly` →
30 passed (was 3 failing for the expected reason - `max_num` mismatched the vocabulary count -
before the admin.py change). `poetry run ruff check` and `ruff format --check` on both touched
files → all checks passed / already formatted.

Next: T099 - every registered measurement type offers the same attached-record editors.

Watch: none outstanding.

## 2026-08-19T12:45:00Z · Implementer US8 · T099

Did: added `TestMeasurementAdminSharedInlines.test_every_registered_type_offers_the_same_inlines`,
asserting that every registered measurement type's admin class (`ExampleMeasurementAdmin`,
`XRFMeasurementAdmin`, `ICP_MS_MeasurementAdmin`, read from `registry.measurements` and the real
`django.contrib.admin.site` registry) has `inlines == MeasurementChildAdmin.inlines`. No
implementation change was needed: none of the concrete admin classes in `fairdm_demo/admin.py`
override `inlines`, so they already inherit the shared set. Checked the assertion was not
tautological by temporarily setting `inlines = []` on `XRFMeasurementAdmin` in
`fairdm_demo/admin.py`, confirming the test fails with a clear diff, then reverting - `git diff`
on that file is empty.

Verified: `poetry run pytest tests/test_core/test_measurement/test_admin.py -q -p no:randomly` →
31 passed. `poetry run ruff check` / `ruff format --check` on the touched test file → all checks
passed / already formatted.

Next: T100/T101 - the administrative list names each row's measurement type.

Watch: none outstanding.

## 2026-08-19T12:55:00Z · Implementer US8 · T100/T101

Did: `measurement_type` was already in `list_display` on both `MeasurementChildAdmin` and
`MeasurementParentAdmin`, and the `measurement_type()` method existed (`admin.py:164`/`:211`), but
the only covering test (`test_list_display_configured`) never asserted the type column at all.
Added `TestMeasurementAdminTypeColumn` with three tests: `"measurement_type"` is present in
`list_display` on both admin classes, and `measurement_admin.measurement_type(obj)` - called the
way the changelist itself resolves a `list_display` callable - names the real polymorphic type
(`XRFMeasurement`'s and `ICP_MS_Measurement`'s own `verbose_name`, not the base `Measurement`'s,
and not equal to each other). No production change was needed - T101's column already existed;
only the test was missing. Checked the presence assertion was not tautological by temporarily
removing `"measurement_type"` from `MeasurementChildAdmin.list_display`, confirming the test fails,
then reverting - `git diff` on `admin.py` is empty.

Verified: `poetry run pytest tests/test_core/test_measurement/test_admin.py -q -p no:randomly` →
34 passed. `poetry run ruff check` / `ruff format --check` on the touched test file → all checks
passed / already formatted.

Next: run the full repo suite once and pre-commit for the completion report - all seven tasks in
this story (T095-T101) are now done.

Watch: none outstanding.

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

## 2026-08-19T12:43:00Z · Implementer US4 · T077-T078

Did: Read tests/test_core/test_measurement/test_permissions.py in full and
fairdm/core/measurement/permissions.py, fairdm/core/permissions.py, fairdm/core/utils.py per
ritual. Ran the baseline (`poetry run pytest tests/test_core/test_measurement -q -p no:randomly`) -
130 passed, 17 skipped, green. Removed TestMeasurementPermissionInheritance's skip (its reason
claimed "change/delete permission mapping needs debugging") and observed all 6 tests pass
unmodified, confirming the reason was false rather than something needing a fix. Rewrote the
class's 4 core tests (view/change/delete + none) plus test_multiple_measurements_inherit_from_same_dataset
against fairdm.core.utils.assign_perm - the entry point this codebase's own MeasurementPermissionBackend
implies - rather than guardian.shortcuts directly.

Verified: `poetry run pytest tests/test_core/test_measurement/test_permissions.py::TestMeasurementPermissionInheritance -q -p no:randomly`
→ 5 passed (exit 0).

Next: T079-T080 (TestMeasurementGuardianIntegration).

Watch: none yet - the assign-then-check pattern in this file later turned out to intermittently
fail for an unrelated reason; see the T085 entry.

## 2026-08-19T12:45:00Z · Implementer US4 · T079-T080

Did: Removed TestMeasurementGuardianIntegration's skip and ran it unmodified first (RED,
observed for the right reason): all 4 tests failed with `django.contrib.auth.models.Permission.DoesNotExist`
raised from `guardian.shortcuts.assign_perm` - the exact claim the skip made (guardian cannot
grant a permission directly on a polymorphic subclass instance), though the concrete exception
differs from the skip text's "WrongAppError" (same root cause, different code path: `assign_perm`
vs `has_perm`). Rewrote all 4 tests plus a new 5th
(test_direct_permission_coexists_with_inherited_dataset_permission) against
fairdm.core.utils.assign_perm/remove_perm/get_perms.

Verified: `poetry run pytest tests/test_core/test_measurement/test_permissions.py::TestMeasurementGuardianIntegration -q -p no:randomly`
→ 5 passed (exit 0); this class is included in the 6 clean full-file repeat runs recorded under T085.

Next: T081 (TestCrossDatasetPermissionBoundaries).

## 2026-08-19T12:47:00Z · Implementer US4 · T081

Did: Removed TestCrossDatasetPermissionBoundaries's skip. Its reason claimed the factory fails
building a Measurement whose sample belongs to a different dataset - confirmed false directly:
`ExampleMeasurementFactory(dataset=dataset_a, sample=sample_b)` builds without complaint on every
run, with and without the skip. Switched its grants to fairdm.core.utils.assign_perm for
consistency with the rest of the file and removed the now-dead top-level `guardian.shortcuts`
import.

Verified: `poetry run pytest tests/test_core/test_measurement/test_permissions.py::TestCrossDatasetPermissionBoundaries -q -p no:randomly`
→ 3 passed (exit 0); this class is included in the 6 clean full-file repeat runs recorded under
T085. Before that fix, this class's own tests intermittently failed for the reason documented
under T085 - not a defect in the isolation logic itself.

Next: T082-T083 (registered-type grant/consult).

## 2026-08-19T12:50:00Z · Implementer US4 · T082-T083

Did: Added TestMeasurementRegisteredTypePermissions (new class, not a re-enable): a grant via
fairdm.core.utils.assign_perm on a registered type (ExampleMeasurement) reads back identically on
the instance and on the bare record (`Measurement.objects.non_polymorphic().get(pk=...)`) (T082).
Added a test proving the negative space directly rather than assuming it: guardian's own
`assign_perm` still raises `Permission.DoesNotExist` for the identical call with no normalisation
in front of it. Added a third test unit-testing `fairdm.core.utils.get_permission_target` itself -
confirms it retargets an ExampleMeasurement instance to the base Measurement record (T083).

Verified: `poetry run pytest tests/test_core/test_measurement/test_permissions.py::TestMeasurementRegisteredTypePermissions -q -p no:randomly`
→ 3 passed (exit 0); this class is included in the 6 clean full-file repeat runs recorded under
T085.

Next: T084 (backend registration).

## 2026-08-19T12:52:00Z · Implementer US4 · T084

Did: Added TestMeasurementPermissionBackendRegistration - a settings-only test (no DB) asserting
`fairdm.core.measurement.permissions.MeasurementPermissionBackend`'s dotted path is present in
`settings.AUTHENTICATION_BACKENDS`. No production code change; the backend was already registered
(fairdm/conf/settings/auth.py:58), nothing asserted it before.

Verified: `poetry run pytest tests/test_core/test_measurement/test_permissions.py::TestMeasurementPermissionBackendRegistration -q -p no:randomly`
→ 1 passed (exit 0).

Next: T085 (final skip count + suite check).

## 2026-08-19T12:55:00Z · Implementer US4 · T085

Did: Confirmed zero `@pytest.mark.skip` remain in test_permissions.py. Ran
`poetry run pytest tests/test_core/test_measurement -q -p no:randomly -rs` repeatedly while
building T077-T084 and hit a genuinely reproducible intermittent failure: every re-enabled test
in this file, individually and in combination, would sometimes assert False right after a grant
that had just been made, with no consistent pattern across classes or run order. Ruled out (with
evidence, not assumption): the factory (isolated single-test reruns always passed), fairdm's
normalisation code (reproduced identically with a minimal repro using a plain Dataset and zero
fairdm permission code), and connection reuse (`CONN_MAX_AGE=0` made no difference).

Root cause: the directory conftest's `user` fixture is `PersonFactory()` with no override, and
`PersonFactory.is_active` is `Faker("boolean", chance_of_getting_true=80)` -
`fairdm/factories/contributors.py:72` - so roughly one user in five is created inactive.
`guardian.core.ObjectPermissionChecker.has_perm` denies every object permission to an inactive
user unconditionally, regardless of any grant. Added a local `user` fixture in
test_permissions.py forcing `is_active=True`, scoped to this file only (module-level fixture
override, `tests/conftest.py` and the directory conftest untouched).

Verified: `poetry run pytest tests/test_core/test_measurement/test_permissions.py -q -p no:randomly`
→ 21 passed, run 6 times consecutively, all clean. `poetry run pytest tests/test_core/test_measurement -q -p no:randomly`
→ 147 passed, 4 skipped, run 3 times consecutively, all clean. The 4 remaining skips, none of
them this story's:
- `test_filters.py:241` - "PartialDateField filtering requires investigation - field validation complex"
- `test_models.py:271` - "URL patterns not implemented yet - Phase 8"
- `test_models.py:716` - "Measurement detail URL not configured"
- `test_models.py:965` - "Demo ICPMSMeasurement not available"

Next: story-level final verify (`poetry run pytest tests/ -q`, `poetry run pre-commit run --all-files`)
and completion report.

Watch: `PersonFactory.is_active`'s 20%-inactive default is shared across the whole factory and
used by the directory's `user` fixture too - any *other* test file in this suite that calls
`user.has_perm(...)` without forcing `is_active=True` is exposed to the same intermittent
failure. Flagged in this story's completion report `concerns` rather than fixed, since
`fairdm/factories/contributors.py` and the directory conftest are shared, high-blast-radius files
outside this story's scope.

## 2026-08-19T12:58:00Z · Implementer US4 · decisions (recorded here, not in decisions.md)

The brief's prohibitions list forbids editing `decisions.md` for this story (it is not one of
the files the standard Implementer protocol's "append a decisions.md mini-ADR" step gets to
override). Recording the two non-obvious choices here instead.

**D-US4-1: `PersonFactory(is_active=True)` overridden locally in test_permissions.py, not fixed
at the source.** Decision: this file defines its own module-level `user` fixture
(`PersonFactory(is_active=True)`), shadowing the directory conftest's `user` for every test in
this file only. Why: `PersonFactory.is_active` (`fairdm/factories/contributors.py:72`) is
`Faker("boolean", chance_of_getting_true=80)` - about one user in five is created inactive, and
`guardian.core.ObjectPermissionChecker.has_perm` denies every object permission to an inactive
user unconditionally, independent of any grant. The correct permanent fix is
`fairdm/factories/contributors.py` or the directory conftest, both shared across the whole test
suite and outside this story's file scope - reported in `concerns` instead. Revisit if: a
follow-up fixes the shared fixture/factory directly, at which point this file's local override
becomes redundant rather than load-bearing.

**D-US4-2: Nine brief tasks landed as six commits, grouped by shared test class.** Decision:
T077+T078 landed together (both covered by `TestMeasurementPermissionInheritance`), T079+T080
landed together (`TestMeasurementGuardianIntegration`), T082+T083 landed together
(`TestMeasurementRegisteredTypePermissions`); T081, T084, T085 each landed alone. Why: splitting
a single pre-existing class's skip-removal and rewrite across two commits would mean transiently
deleting methods in one commit and restoring them in the next - keeping each class whole within
one commit was judged safer than following task numbering literally. Every commit subject names
every task it covers. Revisit if: a reviewer wants literal one-task-one-commit granularity.

## 2026-08-19T13:02:35Z · Implementer US2 · T040

Did: Added `tests/test_core/test_measurement/test_cross_dataset.py` (new file, per the brief —
`test_models.py` and `test_permissions.py` belong to other concurrently-running stories) with
`TestCrossDatasetEditingRights`, proving both halves of the acceptance scenario: a user granted
`dataset.change_dataset` on the measurement's own dataset alone can edit a measurement whose
sample belongs to a different dataset, and cannot edit that sample. The behaviour was believed
already correct going in (`MeasurementPermissionBackend`/`SamplePermissionBackend` each derive
strictly from their own record's dataset) — this task adds only the missing proof. Both
assertions were confirmed to fail for the right reason when inverted, then reverted, before being
accepted.

Verified: `poetry run pytest tests/test_core/test_measurement/test_cross_dataset.py -q -p
no:randomly` → 2 passed. `poetry run ruff check
tests/test_core/test_measurement/test_cross_dataset.py` → all checks passed.

Next: T041 — cross-dataset deletion boundaries, same file.

Watch: none.

## 2026-08-19T13:20:00Z · Implementer US2 · T041

Did: Extended `tests/test_core/test_measurement/test_cross_dataset.py` with
`TestCrossDatasetDeletionBoundaries`, proving both halves of FR-004/FR-005 for the
cross-dataset case: deleting the measurement's own dataset cascades to (deletes) the
measurement and leaves its sample — which belongs to a different dataset — standing, and while
the measurement exists, deleting the sample raises `ProtectedError` and the measurement
survives. `Measurement.dataset` is `on_delete=models.CASCADE`
(`fairdm/core/measurement/models.py:57`) and `Measurement.sample` is `on_delete=models.PROTECT`
(`fairdm/core/measurement/models.py:68`) — confirmed already correct; this task adds only the
missing proof. Each of the three assertions was confirmed to fail for the right reason when
inverted (two flipped `exists()` checks, one removed `pytest.raises` wrapper which then raised
the uncaught `ProtectedError`), then reverted, before being accepted.

Verified: `poetry run pytest tests/test_core/test_measurement/test_cross_dataset.py -q -p
no:randomly` → 5 passed. `poetry run ruff check
tests/test_core/test_measurement/test_cross_dataset.py` → all checks passed.

Next: none — both tasks in this brief (US2: T040, T041) are complete.

Watch: `tests/test_core/test_measurement/test_permissions.py` already carries a
`TestCrossDatasetPermissionBoundaries` class (T081, a different story) covering closely related
ground to this story's T040; `test_models.py` carries `TestMeasurementCRUDWorkflow` cases
(`test_deleting_dataset_cascades_to_measurements`,
`test_deleting_sample_protects_measurements`) and a `TestCrossDatasetMeasurementSampleLinking`
class covering ground close to T041. Both files are owned by other concurrently-running stories
per this story's brief, so left untouched; noted here in case a later pass wants to consolidate
duplicate coverage.

## 2026-08-19T14:06:54Z · Implementer US6 · T066/T067

Did: Added `TestMeasurementFilterPolymorphicTypeChoices` to `test_filters.py`, proving the
`polymorphic_ctype` filter's choices are exactly the content types of `registry.measurements` —
by membership (every demo type, plus `tests.registry_models.ConcreteMeasurement` registered from
outside the framework) and by exclusion (the polymorphic base `Measurement`, and
`ConcreteSample`, a registered non-measurement) — and that narrowing by the outside-registered
type leaves only measurements of that type. Confirmed both new tests failed for the right reason
(`filterset.is_valid()` returned `False` because `ConcreteMeasurement`'s content type, app label
`registry_models`, was outside the hardcoded `app_label__in=["fairdm_core", "fairdm_demo"]`
list) before implementing T067: `MeasurementFilterMixin.__init__` now builds the
`polymorphic_ctype` queryset from `ContentType.objects.get_for_models(*registry.measurements)`
rather than the hardcoded list. `registry` imported locally in `__init__`, matching the existing
local imports of `Dataset`/`Sample` in the same method (avoids a module-level import cycle
between `fairdm.core.measurement.filters` and `fairdm.registry`).

Verified: `poetry run pytest tests/test_core/test_measurement/test_filters.py -q -p no:randomly`
→ 13 passed, 1 skipped (the T072 skip, not yet removed). `poetry run ruff check
fairdm/core/measurement/filters.py tests/test_core/test_measurement/test_filters.py` → all
checks passed (one import-wrap auto-fix applied by ruff itself).

Next: T072/T073 — the date-range filters and their skipped test.

Watch: none.

## 2026-08-19T14:20:00Z · Implementer US6 · T072/T073

Did: Removed the `pytest.mark.skip` on `test_filter_by_date_range` and extended it with a
year-and-month-only measurement date (`"2024-06"`) and a year-only one (`"2023"`), chosen well
clear of the two range boundaries (`"2024-02-01"` / `"2024-02-28"`) so each comparison is
unambiguous at its own precision — no reliance on the field's second-encoded precision as a
tie-breaker. Also fixed `type="analysis"` on the pre-existing fixture data to `type="Setup"`, a
real member of the Measurement date vocabulary (confirmed via `MeasurementDate.VOCABULARY.values`
→ `['Setup', 'TearDown']`) — invisible while the test was skipped, since `MeasurementDate.save()`
refuses an out-of-vocabulary `type`. Confirmed the un-skipped test failed for the reported reason
before implementing T073: reverted the filter fix and re-ran, hitting
`django.core.exceptions.ValidationError: ["'value' value must be a PartialDate instance, a valid
partial date string (YYYY, YYYY-MM, YYYY-MM-DD) or None, not '2024-02-01'"]` raised from
`PartialDateField.to_python` (`partial_date/fields.py:156`), reached via
`get_prep_lookup`→`get_prep_value` on the `date_after`/`date_before` `gte`/`lte` lookups — the
exact defect plan.md R2 names. Then reapplied T073: `date_after`/`date_before` changed from
`django_filters.DateFilter` to `django_filters.CharFilter`, so the cleaned value stays the string
django-filter received rather than being coerced to a `datetime.date` first; the string reaches
`PartialDateField.get_prep_value` intact and the field parses it itself at whatever precision it
carries.

Verified: `poetry run pytest tests/test_core/test_measurement/test_filters.py -q -p no:randomly`
→ 14 passed, 0 skipped. `poetry run ruff check fairdm/core/measurement/filters.py
tests/test_core/test_measurement/test_filters.py` → all checks passed.

Next: T074 — the registry-generated half of the dataset-choices coverage.

Watch: none.

## 2026-08-19T14:35:00Z · Implementer US6 · T074

Did: Added `TestMeasurementFilterRegistryGeneratedDatasetPrivacy` to `test_filters.py`, proving
the T115 dataset-choices widening also holds on the filter set the registry generates for a
registered measurement type (`fairdm.registry.factories.FilterFactory(XRFMeasurement,
fields=["dataset"]).generate()`), not only on `MeasurementFilter` built directly — the mixin half
was already covered by `TestMeasurementFilterMixinDatasetPrivacy`. Built via `FilterFactory`
rather than hand-assembled, matching `TestFilterFactoryMeasurementBranch`
(tests/test_registry/test_factories.py), so the test proves the registry's own wiring rather
than a stand-in. The behaviour was believed already correct going in — `FilterFactory` inherits
`MeasurementFilterMixin` as its base (`get_base_filterset_class`) and doesn't override
`__init__`, so the mixin's dataset-scoping logic runs unconditionally whether or not "dataset" is
also present in the factory's smart-filter overrides. The new test passed on first run; per
`craft-tdd`, confirmed it was not tautological by inverting the assertion (`offered == {other}`)
and watching it fail with the correct two-dataset mismatch, then reverting to the correct
assertion.

Verified: `poetry run pytest tests/test_core/test_measurement/test_filters.py -q -p no:randomly`
→ 15 passed. `poetry run ruff check tests/test_core/test_measurement/test_filters.py` → all
checks passed.

Next: T076 — make the combined-filters test load-bearing on both filters.

Watch: none.

## 2026-08-19T14:50:00Z · Implementer US6 · T076

Did: Rewrote `TestMeasurementFilterCombinedFilters.test_combined_filters_dataset_and_sample`
(named at the brief as this task's own to rewrite). The previous version's third measurement was
bound to `_measurement3` and never asserted, so the dataset filter did no provable work —
`sample` alone already excluded every other row. Replaced it with three measurements built so
each filter excludes a row the other cannot: `measurement_wrong_dataset` shares `sample1` with
`measurement_both` but is linked to `dataset2` (US-2 cross-dataset linking — a measurement's own
`dataset` need not match its sample's, so this is a legitimate row, not a fixture artefact);
`measurement_wrong_sample` shares `dataset1` with `measurement_both` but uses `sample2`. Filtering
by both `dataset=dataset1` and `sample=sample1` together leaves only `measurement_both`.
Confirmed each filter is load-bearing exactly as the brief asks: removed `"dataset"` from the
filter data and watched `measurement_wrong_dataset not in filterset.qs` fail (it reappeared,
alongside `measurement_both`), reverted; removed `"sample"` and watched `measurement_wrong_sample
not in filterset.qs` fail the same way, reverted to the full combination.

Verified: `poetry run pytest tests/test_core/test_measurement/test_filters.py -q -p no:randomly`
→ 15 passed. `poetry run ruff check tests/test_core/test_measurement/test_filters.py
fairdm/core/measurement/filters.py` → all checks passed.

Next: none — all six tasks in this brief (US6: T066, T067, T072, T073, T074, T076) are complete.

Watch: none.

## 2026-08-19T15:15:00Z · Implementer US6 · T073 follow-up

Did: Closed a defect the T073 fix introduced, reported by the coordinator against the delivered
filter set directly: `MeasurementFilter(data={"date_after": "not-a-date"}, ...)` reported
`is_valid() is True`, and evaluating `.qs` then raised an unhandled `django.core.exceptions.
ValidationError` from `PartialDateField.to_python` - a public filter form must never surface a
query-time exception as its error path. Added
`TestMeasurementFilterDateRangeValidation` (`test_filters.py`) with a parametrized case
(`"not-a-date"`, `"2024-13-45"`) asserting `is_valid() is False`, an error on `date_after`, and
that `list(filterset.qs)` does not raise, plus a case confirming an empty string stays valid.
Confirmed both parametrized cases failed for the right reason against the pre-fix code
(`is_valid()` was `True`). Implemented `PartialDateFilterField` (`forms.CharField` subclass) and
`PartialDateFilter` (`django_filters.CharFilter` subclass carrying it as `field_class`) in
`filters.py`: `to_python` calls `partial_date.PartialDate.parseDate()` - the same static method
`fairdm.db.fields.PartialDateField` itself uses - on the cleaned value, letting its
`ValidationError` propagate as a form error rather than reaching the ORM. `date_after`/
`date_before` are now declared with `PartialDateFilter` instead of the bare `CharFilter` T073
left them with. Re-ran `test_filter_by_date_range` on its own to confirm the year-only and
year-and-month cases (T072/T073's whole point) still pass - a validator that rejected `"2024"`
would have put the original bug back with a different face. Recorded as D-018 in `decisions.md`:
reusing the model field's own parser rather than a second regex that could drift from it.

Verified: `poetry run pytest tests/test_core/test_measurement/test_filters.py -q -p no:randomly`
→ 18 passed. `poetry run pytest tests/test_core/test_measurement/test_filters.py::
TestMeasurementFilterCrossRelationshipFiltering::test_filter_by_date_range -v -p no:randomly` →
1 passed. `poetry run ruff check fairdm/core/measurement/filters.py tests/test_core/
test_measurement/test_filters.py` → all checks passed. `poetry run pytest -q -p no:randomly` →
full suite green (see completion report). `poetry run pre-commit run --all-files` → all hooks
passed.

Next: none.

Watch: none.
