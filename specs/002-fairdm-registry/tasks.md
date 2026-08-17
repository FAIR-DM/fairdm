# Tasks: Model registry and generated components

**Input**: `spec.md`, `plan.md`, `research.md` in `specs/002-fairdm-registry/`

**Written greenfield.** This list describes building the feature from an empty repository to the
current standard. It was written from the specification and the constitution, not from the existing
implementation, so that omissions surface instead of being described away. It is reconciled against
the code in the section at the end: a task counts as satisfied only with a code citation *and* a
passing test that covers it.

**Tests are required**, per Article I. Every behaviour task is preceded by the test that fails first.

## Format: `[ID] [P?] [Story] Description`

- **[P]** — can run in parallel with its neighbours, different files, no shared dependency
- **[Story]** — the user story the task serves

---

## Phase 1: Setup

- [x] T001 [US1] Create `fairdm/registry/` with `__init__.py` exporting `register`, `registry` and `ModelConfiguration` as the package's public surface.
- [x] T002 [US1] Create `tests/test_registry/` with `__init__.py`, mirroring the source path per Article X.
- [ ] T003 [P] [US1] Define the suite's test models in `tests/test_registry/conftest.py`: a concrete `Sample` subclass, a concrete `Measurement` subclass, a related model reachable by a path, and a model carrying a many-to-many field with an explicit through model.
- [ ] T004 [P] [US1] Add one `DjangoModelFactory` per test model in `tests/test_registry/conftest.py`, using `factory.Sequence` for uniqueness-guarded fields and `factory.SubFactory` for relations. Expose thin fixtures over them.

---

## Phase 2: Foundational (blocking)

Nothing in Phase 3 onward can be written until these exist.

- [ ] T005 [US3] Write failing tests in `tests/test_registry/test_exceptions.py` asserting each error this feature raises carries the model and the offending attribute in its message.
- [ ] T006 [US3] Implement `fairdm/registry/exceptions.py` with a base registry error and the errors the specification names: a configuration error, a field validation error, a duplicate registration error, and a not-registered error. No error type without a raise site.
- [ ] T007 [US1] Write failing tests in `tests/test_utils/test_inspection.py` for the default field list: that it includes the model's own editable fields, and excludes `id`, polymorphic type columns, multi-table inheritance pointers, `auto_now` and `auto_now_add` fields, anything with `editable=False`, reverse relations, and a many-to-many field with an explicit through model.
- [ ] T008 [US1] Implement default field list derivation on `FieldInspector` in `fairdm/utils/inspection.py`.
- [ ] T009 [US3] Write failing tests in `tests/test_utils/test_inspection.py` for related-path resolution: a single-segment name, a valid two-segment path, a path whose final segment does not exist, and a path that continues past a non-relational field.
- [ ] T010 [US3] Implement related-path resolution on `FieldInspector`, using `django.db.models.constants.LOOKUP_SEP` rather than a literal separator.
- [ ] T011 [US1] Write failing tests, then implement, flattening of field lists that contain tuples used for layout grouping. One implementation, used everywhere a field list reaches a factory.

---

## Phase 3: User Story 1 — Register a model and get every component (P1)

**Goal**: a field list is enough to get all six components.

**Independently testable**: register a model with a field list, ask for each of the six classes, check each type and its fields.

- [x] T012 [US1] Write a failing test that a configuration declaring a model and `fields` registers, and its model appears in the registry.
- [ ] T013 [US1] Implement `ModelConfiguration` in `fairdm/registry/config.py` as a plain class whose configuration is read from class attributes. The model attribute is required and its absence is an error.
- [x] T014 [US1] Implement `FairDMRegistry` in `fairdm/registry/registry.py` holding a model-to-configuration mapping, and the `register` decorator that instantiates a configuration class and stores it.
- [x] T015 [US1] Write failing tests for field resolution order: a component-specific list wins, otherwise the shared `fields`, otherwise the default list. Cover a configuration declaring only `fields`, one declaring `table_fields` alongside it, and one declaring neither.
- [ ] T016 [US1] Implement field resolution on `ModelConfiguration`, in one place, used by every component.
- [ ] T017 [US1] Implement the component table in `fairdm/registry/config.py` mapping each of the six components to its factory, its component-specific field attribute, its custom-class attribute and its expected base class.
- [x] T018 [P] [US1] Write failing tests then implement the form generator in `fairdm/registry/factories.py`: a `ModelForm` subclass over the resolved fields, with the widget appropriate to each field type.
- [x] T019 [P] [US1] Write failing tests then implement the table generator: a `django_tables2.Table` subclass with a column per resolved field.
- [x] T020 [P] [US1] Write failing tests then implement the filter set generator: a `django_filters.FilterSet` over the resolved fields, leaving filter type per field to the library unless configured.
- [ ] T021 [P] [US1] Write failing tests then implement the serializer generator: a DRF `ModelSerializer` subclass over the resolved fields.
- [ ] T022 [P] [US1] Write failing tests then implement the import and export resource generator, supporting natural keys for foreign keys.
- [x] T023 [P] [US1] Write failing tests then implement the admin generator, choosing the polymorphic child admin base appropriate to the model's hierarchy.
- [x] T024 [US1] Write failing tests then implement the six accessors `get_form_class()`, `get_table_class()`, `get_filterset_class()`, `get_serializer_class()`, `get_resource_class()` and `get_admin_class()`, each returning a generated class when no custom class is declared.
- [ ] T025 [US1] Write a failing test that calling an accessor twice returns a class built afresh both times, so that nothing caches.
- [ ] T026 [US1] Write a failing test that every component can be produced with no database available, then confirm no generation path touches it.
- [x] T027 [US1] Write failing tests then implement the metadata classes and the display name and description defaults derived from the model's verbose name.

**Checkpoint**: a model registered with a field list yields all six components, and User Story 1 stands alone.

---

## Phase 4: User Story 2 — Replace one component without touching the others (P1)

**Goal**: supplying one class leaves the other five generated.

**Independently testable**: register with a custom table class and confirm the table is it and the rest are generated.

- [x] T028 [US2] Write failing tests then implement returning a declared custom class unchanged from its accessor, accepting either a class or a dotted import path.
- [ ] T029 [US2] Write a failing test that a configuration with a custom table class still yields a generated form, filter set, serializer, resource and admin.
- [ ] T030 [US2] Write failing tests then implement validation at registration that a declared custom class subclasses the base its component requires, with a message naming the model, the attribute and the expected base.
- [x] T031 [US2] Write failing tests then implement the requirement that a custom admin class for a sample or measurement subclass subclasses the framework's polymorphic child admin base for that hierarchy.

**Checkpoint**: every component is independently replaceable.

---

## Phase 5: User Story 3 — Configuration mistakes stop the process at registration (P1)

**Goal**: every class of misconfiguration is refused while the model is being registered.

**Independently testable**: attempt each bad registration and assert it raises with a message naming the model, the attribute and the offending value.

- [x] T032 [US3] Write failing tests then implement validation that every name in every field list exists on the model, with a close-match suggestion in the message where one exists.
- [ ] T033 [US3] Write failing tests then implement validation that every segment of a related path resolves, not only the first.
- [ ] T034 [US3] Write failing tests then implement refusal, as `ImproperlyConfigured`, of a configuration declaring both a component's field list and its custom class, naming both attributes.
- [x] T035 [US3] Write failing tests then implement rejection of any model that is not a concrete subclass of `Sample` or `Measurement`, naming both permitted bases.
- [ ] T036 [US3] Write failing tests then implement the duplicate registration error carrying the module and qualified name of the first registration.
- [ ] T037 [US3] Write failing tests then implement raising, rather than returning nothing, when the configuration of an unregistered model is requested. Provide the non-raising membership test alongside it.
- [ ] T038 [US3] Write a failing test that a failure to register a model's admin class with the admin site propagates, then remove the suppression that would swallow it.
- [ ] T039 [US3] Write a test asserting `manage.py check` reports nothing from the registry, so that validation exists in exactly one place. Depends on the check module removal tracked in issue #140.
- [ ] T040 [US3] Write a test asserting that all validation happens during registration: a configuration that would fail validation never reaches the registry's mapping.

**Checkpoint**: a misconfigured portal cannot start.

---

## Phase 6: User Story 4 — Build a component in code when a field list cannot say it (P2)

**Goal**: an overridden accessor is what the whole framework receives.

**Independently testable**: subclass a configuration, override one accessor, confirm every framework path gets the override.

- [ ] T041 [US4] Write a failing test that a configuration overriding `get_form_class()` returns the overridden class, and that its other five components are still generated.
- [ ] T042 [US4] Write a failing test that an overridden accessor runs on every call rather than once.
- [ ] T043 [US4] Write a test that no public attribute or property on a configuration returns a component class, so nothing can bypass an override. Remove any that does.
- [ ] T044 [US4] Migrate every consumer inside the framework onto the accessors, so no consumer can receive a generated class in place of an override. Add a test per migrated consumer.

**Checkpoint**: the third tier of customisation is real rather than nominal.

---

## Phase 7: User Story 5 — Find out what a portal has registered (P2)

**Goal**: the registered types and their configurations are reachable without naming a model.

**Independently testable**: register several types and assert each introspection call returns exactly the expected set.

- [x] T045 [P] [US5] Write failing tests then implement the sample, measurement and all-models listings, each returning only what belongs to it.
- [x] T046 [P] [US5] Write failing tests then implement the listing of every configuration, and the non-raising membership test.
- [x] T047 [US5] Write failing tests then implement lookup by model class and by `"app_label.model_name"` string, returning the same configuration for both, and a clear error for a malformed string or an unknown model.

**Checkpoint**: the framework's own API, browse pages and admin can be built on this.

---

## Phase 8: Polish and cross-cutting

- [ ] T048 [P] [US4] Add demo registrations in `fairdm_demo/config.py` covering at least three sample types and two measurement types, and between them a bare field list, per-component field lists, a custom component class, and an overridden accessor.
- [x] T049 [P] [US1] Add `fairdm_demo/tests/test_registry_api.py` asserting the demo's registrations behave as its docstrings claim.
- [ ] T050 [P] [US1] Add performance tests pinning both non-functional requirements: validation for 100 registered models under 5 ms, and all six components for one model under 5 ms.
- [ ] T051 [P] [US1] Write `docs/contributing/registry-system.md` describing the mechanism as built, and the portal-development guides for the three tiers of customisation.
- [x] T052 [US1] Remove the superseded artifacts in this spec directory: `data-model.md`, `quickstart.md`, `RESEARCH.md`, `contracts/`, `research/` and `checklists/`. They describe the previous design, including a protocol for a resolver that is being deleted.
- [ ] T053 [US1] Run the machine verify gate: lint, type check, full test suite, build.

---

## Dependencies

- Phase 1 before everything.
- Phase 2 before every story phase. `FieldInspector` and the exceptions are used by all of them.
- T013 and T014 before every other task in Phase 3.
- T017 before T024.
- T018 to T023 are parallel with each other, and all precede T024.
- Story phases 3 to 7 are independent of one another once Phase 2 is done, and are ordered by priority.
- T039 depends on issue #140 landing.
- T044 depends on T043.
- T053 last.

---

## Reconciliation against the codebase

Reconciled 2026-08-17 against `origin/main` at `6fa863a`, which already carries the removal of the
superseded configuration system. Baseline: 222 tests pass in 6.0 s across `tests/test_registry/`,
`tests/test_utils/` and `fairdm_demo/tests/test_registry_api.py`.

**20 of 53 tasks satisfied, 33 open.** A task is ticked only with a code citation *and* a passing
test that covers the behaviour. The previous run's checkboxes were not consulted.

### Satisfied, with evidence

| Task | Code | Test |
|---|---|---|
| T001 | `fairdm/registry/__init__.py:8` | every module in `tests/test_registry/` imports through it |
| T002 | `tests/test_registry/__init__.py` | suite collects |
| T012 | `fairdm/registry/registry.py:414` | `test_registry.py::TestBasicRegistration` |
| T014 | `fairdm/registry/registry.py:24`, `:414` | `test_registry.py::TestRegistrationBasics` |
| T015 | — | `test_config.py::TestFieldResolutionAlgorithm`, 12 tests across four components |
| T018 | `fairdm/registry/factories.py:77` | `test_factories.py::TestFormFactory` |
| T019 | `fairdm/registry/factories.py:173` | `test_factories.py::TestTableFactory` |
| T020 | `fairdm/registry/factories.py:314` | `test_factories.py::TestFilterFactory` |
| T023 | `fairdm/registry/factories.py:455`, `:740` | `test_factories.py::TestAdminFactoryBasics`, `test_config.py::TestAdminInheritanceValidation::test_autogenerated_sample_admin_inherits_from_child_admin` |
| T024 | `fairdm/registry/config.py:695-735` | `test_config.py::TestAutoGeneratedComponents`, `test_registry.py::TestSampleAutoGeneratedComponents` |
| T027 | `fairdm/registry/config.py:32`, `:56`, `:72`, `:278` | `test_config.py::TestModelMetadata`, `TestAuthority`, `TestCitation` |
| T028 | `fairdm/registry/config.py:459`, `:544` | `test_config.py::TestComponentOverrides`, `TestCustomClassOverride`, `TestAdminInheritanceValidation::test_admin_class_as_string_reference` |
| T031 | `fairdm/registry/config.py:345` | `test_config.py::TestAdminInheritanceValidation`, 8 tests |
| T032 | `fairdm/registry/config.py:331-343` | `test_config.py::TestFieldValidationWithFuzzyMatching`, `TestRegistrationValidation::test_invalid_field_name_in_list_fields` |
| T035 | `fairdm/registry/registry.py:238` | `test_config.py::TestRegistrationValidation::test_model_must_inherit_from_sample_or_measurement` |
| T045 | `fairdm/registry/registry.py:163`, `:175`, `:187` | `test_registry.py::TestRegistrySamplesProperty`, `TestRegistryMeasurementsProperty` |
| T046 | `fairdm/registry/registry.py:138`, `:197` | `test_registry.py::TestRegistryEnhancedMethods` |
| T047 | `fairdm/registry/registry.py:82` | `test_registry.py::TestRegistryGetForModel`, `TestRegistryEnhancedMethods` |
| T049 | `fairdm_demo/tests/test_registry_api.py` | 10 tests pass |
| T052 | superseded artifacts removed in this commit | n/a, a deletion |

### Open, and why

**Never built** (15): T003, T004, T005, T009, T010, T017, T026, T029, T033, T034, T039, T041, T042,
T050, T053.

Worth naming among those: there are no `factory_boy` factories in `tests/test_registry/conftest.py`
at all, so T003 and T004 are an Article X gap the suite has carried since it was written. Test models
are declared inline inside test methods instead.

**Built without a test** (6):

- T006 — `exceptions.py` carries four error classes, each with a raise site, but no test module of its own, and it has no not-registered error for T037 to raise.
- T007, T008 — the default field list covers every exclusion rule except the many-to-many-with-explicit-through case at `config.py:435-453`, which no test reaches.
- T021, T022 — the serializer and resource generators exist at `factories.py:773` and `:851` with no test class of their own. Two of the six components ship untested.
- T040 — validation does run before the configuration is stored, but nothing asserts the registry mapping is untouched after a refused registration.

**Built, but the code contradicts the specification** (12):

- T011 — three flattening implementations rather than one: `config.py:322` inline, `config.py:516`, and `api/serializers.py:161`.
- T013 — `ModelConfiguration` is still a `@dataclass` (`config.py:98`), with the 80-line attribute-copying block that forces.
- T016 — field resolution works but is written out six times (`config.py:551, 573, 596, 620, 644, 667`).
- T025 — the accessors delegate to `@cached_property` (`config.py:540` onward), so a class is built once and reused.
- T030 — only the admin class has its base validated at registration. The form, table and filter set base checks live in `checks.py:87`, which runs from management commands only.
- T036 — the error raises (`registry.py:251`) but carries `original_location="Unknown"` with a `TODO` at `registry.py:254`.
- T037 — `get_for_model` raises, but `Model.config` returns `None` for an unregistered model (`fairdm/core/abstract.py:173-176`).
- T038 — admin registration is wrapped in `except Exception: pass` (`registry.py:275`).
- T043 — the six cached properties are public, so any consumer can bypass an override.
- T044 — `api/viewsets.py:223` reads `config.filterset` instead of calling the accessor.
- T048 — the demo covers a bare field list, per-component lists and custom classes, but no overridden accessor.
- T051 — `docs/contributing/registry-system.md` is current for the code as it stands, not for the design in this specification.

### One test asserts the behaviour this specification reverses

`tests/test_registry/test_config.py:1123`, `test_invalid_related_field_path`, reads as coverage for
related-path validation and is the opposite. Its docstring states that only the base field is checked
and gives three reasons not to check the rest. It is a passing test pinning the limitation, so T033
cannot count it as evidence, and closing T033 means changing it. Article I forbids modifying a
pre-existing test without a recorded decision; that decision is D4 in `decisions.md`.

### What the split says

Every task about *producing* a component is satisfied. The feature was built and it works. What is
missing is almost everything that makes it dependable.

Per story, counting the setup and polish tasks against the story each one serves:

| Story | Satisfied | Total |
|---|---|---|
| US-1 register and get every component (P1) | 13 | 28 |
| US-2 replace one component (P1) | 2 | 4 |
| US-3 mistakes stop the process (P1) | 2 | 13 |
| US-4 override an accessor (P2) | 0 | 5 |
| US-5 introspection (P2) | 3 | 3 |

Introspection is complete. Refusing bad configuration is 2 of 13. The override tier is 0 of 5 and has
never been exercised by anything. Two of the six generators ship with no test at all, and the test
suite has no `factory_boy` factories, which is an Article X gap older than this audit.

The tasks in the Setup and Foundational phases serve more than one story. Each is assigned to the
story it most unblocks, so that the ledger has one home per task: the exception handling and path
resolution go to US-3, whose subject they are, the demo's override example goes to US-4, and the rest
go to US-1.
