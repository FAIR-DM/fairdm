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
