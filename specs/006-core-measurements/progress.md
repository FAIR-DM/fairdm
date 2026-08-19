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
