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
