# Tasks — 006 The measurement record

**Written greenfield.** Every task below describes building this feature from nothing, to the
standard the constitution asks for now. Nothing here was written by reading the existing
implementation. What the code already satisfies is settled in the reconciliation pass that follows,
against a code citation and a passing test whose assertion is quoted — never against this list's own
optimism, and never against the February task list.

Test tasks come before their implementation tasks. Each task names the file it lands in.

**Design review, 2026-08-19.** Ten of the thirty-four ticks did not survive the reconciliation lens
and are reopened in place with the reason. Two tasks were added and carry the next free numbers:
T114 and T115. Numbers are never reused, because the ledger cites them.

**Reconciled 2026-08-19.** Thirty-four of the hundred and thirteen tasks are closed against the code
as it stands. A task closed here cites the code that satisfies it *and* a passing test, with that
test's assertion quoted — a line number proves a test exists, not what it checks. Seventy-nine stay
open, and each says why in one of three shapes: never built, built without a test that covers it, or
built differently from what the specification now asks for.

Two of those shapes matter more than the count. **Built without tests** is not a bookkeeping
category: it is code nobody can change safely, and on this feature it covers the permission
derivation, the dataset scoping on the form and the whole of the value convention. **Built
differently** is where the code and the specification disagree, and every one of those was
adjudicated in `decisions.md` before it reached this list.

## Phase 0 — Foundations

- [X] T001 One factory per metadata model in `fairdm/factories/core.py` —
  `MeasurementDescriptionFactory`, `MeasurementDateFactory`, `MeasurementIdentifierFactory` — each
  using `factory.Sequence` for uniqueness-guarded fields, `factory.SubFactory` for relations, and
  each defaulting `type` to a member of its own vocabulary.
  - **Closed by group 0.** `MeasurementIdentifierFactory` added; the description and date factories now default to real vocabulary members and all three are tested.
- [X] T002 Make `MeasurementFactory` in `fairdm/factories/core.py` an abstract factory base. The
  framework ships the abstract factory; the reference implementation ships concrete measurement
  types. A concrete factory here would make the framework import its own demo application.
  - **Closed by group 0.** `MeasurementFactory` is an abstract base; calling it directly refuses.
- [X] T003 Concrete measurement factories in `fairdm_demo/factories.py`, one per demo measurement
  type, each supplying its own required fields.
  - **Closed by group 0.** `XRFMeasurementFactory` and `ICP_MS_MeasurementFactory` added beside the existing example.
- [X] T004 Export every measurement factory from `fairdm/factories/__init__.py`.
  - **Closed by group 0.** All three metadata factories exported and asserted present in `__all__`.
- [X] T005 Shared fixtures in `tests/test_core/test_measurement/conftest.py` wrapping those
  factories: a dataset, a concrete sample, a measurement of a concrete type, a second dataset with
  its own sample for the cross-dataset cases, and a user holding no rights at all.
  - **Closed by group 0.** The measurement fixture yields a concrete type; a second dataset, its sample, and a user holding no rights added.
- [X] T006 Retarget every measurement call site in the suite onto a concrete type, so that no test
  depends on the bare record being creatable.
  - **Closed by group 0.** Every bare-record call site retargeted, including twenty-two outside the measurement suite that the first brief's file scope wrongly excluded. Three tests changed meaning rather than call site and are named in the implementation report.

## Phase 1 — The record

- [X] T007 Tests in `tests/test_core/test_measurement/test_models.py` that a measurement is given a
  short generated identifier on creation, that it is prefixed so as to be recognisable as a
  measurement's, and that it cannot be changed afterwards.
  - **Open:** built without tests — the prefix and uniqueness are asserted, nothing asserts the identifier cannot be changed
- [X] T008 The generated identifier field on `Measurement` in `fairdm/core/measurement/models.py`.
  - **Reconciled done.** Code: `fairdm/core/measurement/models.py:60`. Test: `tests/test_core/test_measurement/test_models.py:53` — `assert measurement.uuid.startswith("m")`
- [X] T009 Tests that a measurement requires a name, and that its own label, image, vocabulary terms
  and free-form tags are each optional.
  - **Open:** never built — no test covers the model's own field requirements
- [X] T010 Those fields on `Measurement`, with `verbose_name`, `help_text` and translation marking.
  - **Open:** built without tests — `local_id` (`models.py:78`) has no test at all
- [X] T011 Tests that two measurements in different datasets may carry the same label, and that both
  save.
  - **Open:** never built
- [X] T012 The label field declared without a uniqueness constraint.
  - **Open:** built without tests — the label carries no uniqueness constraint (`models.py:78`) and nothing asserts it
- [X] T013 Tests that a measurement requires a dataset, and that deleting the dataset deletes the
  - **Reopened at design review:** the cited test deletes the measurement before it deletes the dataset (`test_models.py:293`), so the assertion holds whatever `on_delete` says. Close it against `test_models.py:784`, which deletes the dataset while the measurement lives.
  measurement.
- [X] T014 The dataset relation on `Measurement`, cascading on delete.
  - **Reopened at design review:** same vacuous citation as T013. Close against `test_models.py:784`.
- [X] T015 Tests that a measurement requires a sample, and that deleting a sample is refused while
  - **Reconciled done.** Code: `fairdm/core/measurement/models.py:71`. Test: `tests/test_core/test_measurement/test_models.py:308` — `with pytest.raises(ProtectedError): sample.delete()`
  any measurement refers to it.
- [X] T016 The sample relation on `Measurement`, refusing deletion while referenced.
  - **Reconciled done.** Code: `fairdm/core/measurement/models.py:71`. Test: `tests/test_core/test_measurement/test_models.py:308` — `with pytest.raises(ProtectedError): sample.delete()`
- [X] T017 Tests that a measurement records when it was created and when it was last changed.
  - **Open:** built without tests — creation timestamps are asserted, nothing asserts `modified` moves on a change
- [X] T018 Those timestamps on `Measurement`.
  - **Reconciled done.** Code: `fairdm/core/abstract.py:23`. Test: `tests/test_core/test_measurement/test_models.py:54` — `assert measurement.added is not None`
- [X] T019 Tests that a person or organisation can be credited on a measurement under one or more
  roles, and that the roles offered come from the measurement contributor vocabulary, asserted by
  naming the members it contains.
  - **Open:** never built
- [X] T020 The contributions relation and the contributor role vocabulary binding on `Measurement`.
  - **Open:** built without tests — `CONTRIBUTOR_ROLES` (`models.py:46`) and the relation (`:68`) have no covering test
- [X] T021 Tests that a measurement's address resolves to that measurement and not to its sample.
  - **Reconciled done.** Code: `fairdm/core/measurement/models.py:155`. Test: `tests/test_core/test_measurement/test_models.py:637` — `assert url == f"/measurement/{measurement.uuid}/"`
- [X] T022 The address on `Measurement`, and the name it reverses, in
  - **Reconciled done.** Code: `fairdm/core/measurement/models.py:164, fairdm/core/measurement/urls.py:7`. Test: `tests/test_core/test_measurement/test_models.py:637` — `assert url == f"/measurement/{measurement.uuid}/"`
  `fairdm/core/measurement/models.py` and `fairdm/core/measurement/urls.py`.

## Phase 2 — Polymorphism and the registry

- [X] T023 Tests that querying measurements without naming a type returns each as the type it was
  - **Reconciled done.** Code: `fairdm/core/measurement/models.py:27`. Test: `tests/test_core/test_measurement/test_models.py:137` — `assert isinstance(xrf_instance, XRFMeasurement)`
  created as, carrying that type's own fields.
- [X] T024 `Measurement` as a polymorphic base in `fairdm/core/measurement/models.py`.
  - **Reconciled done.** Code: `fairdm/core/measurement/models.py:27`. Test: `tests/test_core/test_measurement/test_models.py:137` — `assert isinstance(xrf_instance, XRFMeasurement)`
- [X] T025 Tests in `test_models.py` that creating a bare measurement belonging to no type is
  refused through validation, and tests in `test_forms.py` and `test_admin.py` that it is refused
  through a form and through the administrative interface.
  - **Open:** built without tests — validation is covered; the form's refusal passes for an unrelated reason (see T029) and nothing covers the administrative interface
- [X] T026 Tests that creating one through the manager is refused, and that no fixture in the
  framework creates one.
  - **Open:** never built
- [X] T027 The refusal in the record's own validation.
  - **Reconciled done.** Code: `fairdm/core/measurement/models.py:111`. Test: `tests/test_core/test_measurement/test_models.py:265` — `assert "subclass" in error_message or "directly" in error_message`
- [X] T028 The refusal in the manager, so that a direct create cannot bypass validation.
  - **Open:** never built — `Measurement.objects.create()` produces a bare record today
- [X] T029 The refusal in the form.
  - **Reopened at design review:** the cited assertion is satisfied by an unrelated error. The form is built with a private dataset and no request, so the dataset choice alone invalidates it; deleting the refusal leaves the test passing. Close it by asserting on the message, and delete `MeasurementForm.clean()` — the model already raises the same error through `_post_clean`, which is why it currently renders twice.
- [X] T030 Tests in `tests/test_core/test_measurement/test_config.py` that registering a measurement
  type produces a form, a filter set, a table and an administrative entry, each carrying that type's
  own fields alongside those every measurement has, with none of them written by hand.
  - **Open:** built without tests — the generated components are asserted to exist, not to carry the type's own fields
- [X] T031 The registration path for measurement types through the registry.
  - **Reconciled done.** Code: `fairdm/registry/registry.py:281`. Test: `tests/test_core/test_measurement/test_config.py:29` — `assert config.get_form_class().Meta.model == XRFMeasurement`
- [X] T032 Tests in `test_admin.py` that the administrative type selection offers every registered
  measurement type and nothing else, including a type registered from outside the framework.
  - **Open:** built without tests — `assert len(child_models) > 0` does not establish that the choices are the registered types
- [X] T033 Type discovery from the registry on the parent administrative class.
  - **Open:** built without tests — the code reads the registry (`admin.py:172`) but no assertion distinguishes that from any non-empty list
- [X] T034 Tests that a configuration base exists carrying the fields every measurement has, and
  that a type inheriting it receives them.
  - **Open:** built without tests — `hasattr(config, 'table_fields')` establishes nothing about content
- [X] T035 `BaseMeasurementConfiguration` in `fairdm/core/measurement/config.py`.
  - **Reconciled done.** Code: `fairdm/core/measurement/config.py:25`. Test: `tests/test_core/test_measurement/test_config.py:184` — `assert isinstance(config, BaseMeasurementConfiguration)`
- [X] T036 Tests in `tests/test_registry/test_config.py` that a configuration supplying an
  administrative class not built on the framework's configured base is refused, and that the message
  names that base. The test imports the base under its own name, never under an alias.
  - **Open:** built differently — the test imports the stub under the real class's name (`tests/test_registry/test_config.py:641`), so it asserts against the wrong class by construction
- [X] T037 That validation in `fairdm/registry/config.py`, checking against the configured base.
  - **Open:** built differently — validation checks `fairdm.core.admin.MeasurementAdmin` (`fairdm/registry/config.py:377`), the two-line stub
- [X] T038 Exactly one administrative class for the measurement record and exactly one base for the
  types beneath it, with no unreachable duplicate of either anywhere in the framework. Both registry
  references are repointed: the validation in `fairdm/registry/config.py` and the generation in
  `fairdm/registry/factories.py`.
  - **Open:** built differently — two administrative classes and two parent admins exist (`fairdm/core/admin.py:26`, `:33`)

## Phase 3 — Cross-dataset linking

- [X] T039 Tests that a measurement in one dataset naming a sample from another is created, and that
  - **Reconciled done.** Code: `fairdm/core/measurement/models.py:71`. Test: `tests/test_core/test_measurement/test_models.py:222` — `assert measurement.sample.dataset != measurement.dataset`
  the measurement is attributed to its own dataset while the sample stays attributed to the sample's.
- [X] T040 Tests that a user holding editing rights on the measurement's dataset and not on the
  sample's may edit the measurement and may not edit the sample.
  - **Open:** never built — every test covering the cross-dataset rights boundary is skipped
- [X] T041 Tests that deleting the measurement's dataset removes the measurement whatever dataset
  - **Reopened at design review:** same vacuous citation as T013. `test_models.py:784` covers both halves, including the cross-dataset sample.
  its sample belongs to, and that deleting the sample is refused while the measurement refers to it.

## Phase 4 — Descriptions, dates and identifiers

- [X] T042 Tests that a measurement's descriptions, dates and identifiers each refer to the
  measurement directly, and that all three are deleted when it is.
  - **Open:** built without tests — the direct relation is asserted (`test_models.py:647`); the cascade on delete is not
- [X] T043 The three records with direct relations to `Measurement`, cascading on delete.
  - **Open:** built without tests — same
- [X] T044 Tests that a description's type is drawn from the measurement description vocabulary,
  asserted by naming the members that vocabulary contains rather than by iterating whatever it holds.
  - **Open:** built differently — the test asserts `desc.type == "method"`, which is not a member of the measurement description vocabulary, and passes only because nothing validates
- [X] T045 The description vocabulary binding on `MeasurementDescription`.
  - **Open:** built without tests — the binding exists (`models.py:184`) but its only test asserts an invalid member
- [X] T046 Tests that a date's type is drawn from the measurement date vocabulary, asserted the same
  way.
  - **Open:** built differently — the test asserts `date.type == "measured"`, not a member of the measurement date vocabulary
- [X] T047 The date vocabulary binding on `MeasurementDate`.
  - **Open:** built without tests — the binding exists (`models.py:195`) but its only test asserts an invalid member
- [X] T048 Tests that an identifier's type is drawn from the measurement identifier collection, and
  - **Reconciled done.** Code: `fairdm/core/measurement/models.py:208`. Test: `tests/test_core/test_measurement/test_models.py:183` — `assert set(MeasurementIdentifier.VOCABULARY.values) == {"DOI"}`
  that the collection contains no type belonging to another kind of record.
- [X] T049 The identifier collection and its binding on `MeasurementIdentifier`.
  - **Reconciled done.** Code: `fairdm/core/measurement/models.py:208`. Test: `tests/test_core/test_measurement/test_models.py:183` — `assert set(MeasurementIdentifier.VOCABULARY.values).isdisjoint(...)`
- [X] T050 Tests that a description, date or identifier carrying a type outside its vocabulary is
  refused by validation with a message naming the offending type.
  - **Open:** never built
- [X] T051 That validation on the three metadata records.
  - **Open:** never built — the metadata records carry field choices and no validation, and a direct create bypasses choices entirely

## Phase 5 — The mixins and their wiring

- [X] T052 Tests in `test_filters.py` that a filter set inheriting the filter mixin carries every
  filter the mixin declares, named one by one.
  - **Open:** built differently — the only covering test asserts two measurements are present, which an empty filter set also satisfies
- [X] T115 The dataset choices offered by the filter mixin are scoped to what the requesting
  reader may see, the way the form mixin already scopes them — the mixin currently assigns every
  dataset in the portal unconditionally, so a private dataset's name is offered to a reader holding
  no right over it, and T063 would carry that into every filter set the registry generates.
- [X] T053 `MeasurementFilterMixin` in `fairdm/core/measurement/filters.py` carrying those filters,
  built so that the filtering library collects them from an inheriting class, and with a `Meta` that
  names no model so no unused filter set is generated per subclass.
  - **Open:** never built — the mixin declares no filters (`filters.py:19`)
- [X] T054 Tests in `test_forms.py` that a form inheriting the form mixin and given the requesting
  user offers only the datasets that user may add measurements to, including datasets that are not
  publicly visible.
  - **Open:** built differently — the covering test asserts `hasattr(form, 'request')`
- [X] T055 Tests that a form inheriting the form mixin and given no user offers no dataset at all.
  - **Open:** never built
- [X] T056 The dataset scoping in `MeasurementFormMixin` in `fairdm/core/measurement/forms.py`.
  - **Open:** built without tests — the scoping exists (`forms.py:76`) and nothing asserts it
- [X] T057 Tests that guidance text a form defines for a field reaches the rendered field, asserted
  on the rendered field rather than on the form's configuration.
  - **Open:** never built
- [X] T058 The guidance text on the measurement form's fields, marked for translation.
  - **Open:** built differently — declared as `help_text` rather than `help_texts` (`forms.py:150`), so all four strings are inert
- [X] T059 Tests that every address the form's controls refer to resolves.
  - **Open:** never built
- [X] T060 Those controls in `MeasurementFormMixin`.
  - **Open:** built differently — the control reverses `admin:core_dataset_add` (`forms.py:64`), which does not resolve
- [X] T061 Tests in `tests/test_registry/` that the form and the filter set the registry generates
  for a measurement type supplying neither carry the mixins' behaviour rather than the framework's
  plain defaults.
  - **Open:** never built
- [X] T062 The measurement branch in the registry's form factory, in `fairdm/registry/factories.py`.
  - **Open:** never built — the form factory has a sample branch only (`fairdm/registry/factories.py:172`)
- [X] T063 The measurement branch in the registry's filter factory.
  - **Open:** never built — the filter factory has a sample branch only (`fairdm/registry/factories.py:479`)

## Phase 6 — Finding measurements

- [X] T064 Tests that narrowing by one dataset leaves only that dataset's measurements, and
  - **Reconciled done.** Code: `fairdm/core/measurement/filters.py:88`. Test: `tests/test_core/test_measurement/test_filters.py:63` — `assert measurement1 in filterset.qs / assert measurement2 not in filterset.qs`
  narrowing by one sample only that sample's.
- [X] T065 The dataset and sample filters.
  - **Reconciled done.** Code: `fairdm/core/measurement/filters.py:88`. Test: `tests/test_core/test_measurement/test_filters.py:63` — `assert measurement2 not in filterset.qs`
- [ ] T066 Tests that the measurement type choices offered are exactly the registered measurement
  types — including one registered from outside the framework and excluding records that are not
  measurements — and that narrowing by one leaves only measurements of that type.
  - **Open:** built without tests — narrowing is asserted, nothing asserts which choices are offered
- [ ] T067 The type filter, drawing its choices from the registry.
  - **Open:** built differently — choices come from a fixed application list (`filters.py:151`) that excludes the record's own application and any portal's
- [X] T068 Tests that a search term returns measurements whose name or generated identifier contains
  - **Reconciled done.** Code: `fairdm/core/measurement/filters.py:112`. Test: `tests/test_core/test_measurement/test_filters.py:184` — `assert measurement1 in filterset.qs (searched by name, then by uuid at :194)`
  it, and no others.
- [X] T069 The search filter.
  - **Reconciled done.** Code: `fairdm/core/measurement/filters.py:155`. Test: `tests/test_core/test_measurement/test_filters.py:184` — `assert measurement3 not in filterset.qs`
- [X] T070 Tests that narrowing by description text leaves only measurements whose descriptions
  - **Reconciled done.** Code: `fairdm/core/measurement/filters.py:118`. Test: `tests/test_core/test_measurement/test_filters.py:238` — `assert measurement2 not in filterset.qs (filtered on description text)`
  match.
- [X] T071 The description filter.
  - **Reconciled done.** Code: `fairdm/core/measurement/filters.py:118`. Test: `tests/test_core/test_measurement/test_filters.py:238` — `assert measurement1 in filterset.qs`
- [ ] T072 Tests that narrowing by a range of dates works, including for dates recorded only as a
  year or as a year and month.
  - **Open:** never built — the covering test is skipped
- [ ] T073 The date-range filters, passing a value the partial-date field accepts.
  - **Open:** built differently — a date filter cleans input to a `date`, which the partial-date field refuses (`filters.py:125`)
- [ ] T074 Tests that a reader entitled to a dataset that is not publicly visible finds it among the
  dataset choices, on a filter set built from the mixin as well as on one built by the registry.
  - **Open:** built without tests — the mixin half is covered (`test_filters.py:352` builds a filter set from the mixin and validates against a private dataset); the registry-generated half is not
- [X] T075 The dataset choices, widened on the mixin so that an inheriting filter set inherits the
  - **Reconciled done.** Code: `fairdm/core/measurement/filters.py:59`. Test: `tests/test_core/test_measurement/test_filters.py:62` — `assert filterset.is_valid() - the test's datasets are deliberately left private (its own comment says so), so an unwidened choice field would fail validation`
  widening.
- [ ] T076 Tests that two filters applied together leave only measurements satisfying both.
  - **Reopened at design review:** the second filter does no work — the only row the dataset filter would remove is assigned to a discarded name and never asserted (`test_filters.py:307`).

## Phase 7 — Access

- [X] T077 Tests in `test_permissions.py` that a user holding view, change or delete over a dataset
  holds the corresponding right over its measurements, and that a user holding nothing holds nothing.
  - **Open:** never built — the covering tests are skipped
- [X] T078 The derivation of a measurement's rights from its dataset, in
  `fairdm/core/measurement/permissions.py`.
  - **Open:** built without tests — the derivation works (`permissions.py:96`) and every covering test is skipped
- [X] T079 Tests that a right granted over one measurement applies to that measurement and to no
  other.
  - **Open:** never built — skipped
- [X] T080 Direct rights over a measurement.
  - **Open:** built without tests — skipped
- [X] T081 Tests that rights over the sample a measurement names derive from that sample's own
  dataset, independently of the measurement's.
  - **Open:** never built — skipped
- [X] T082 Tests that a right can be granted over a measurement of a registered type as well as
  consulted on it, and that the answers match those for the bare record.
  - **Open:** never built — skipped
- [X] T083 Whatever normalisation that grant needs, so that a registered type is not treated as a
  record of its own.
  - **Open:** built without tests — the normalisation lives in `fairdm/core/permissions.py` and no measurement test reaches it
- [X] T084 The backend registered in the project's authentication settings.
  - **Open:** built without tests — registered (`fairdm/conf/settings/auth.py:58`) with nothing asserting it
- [X] T085 Confirm no test covering behaviour in this specification is skipped, and that the suite
  reports none.
  - **Open:** never built — seventeen tests are skipped

## Phase 8 — The value a measurement reports

- [ ] T086 Tests that a measurement type nominating a value reports that value, and that a type
  nominating none reports the record's name.
  - **Open:** built without tests — the fallback is asserted; the nominated-value case cannot be, because no type nominates one
- [ ] T087 The value report on `Measurement`.
  - **Open:** built without tests — same
- [ ] T088 Tests that where a type records an uncertainty alongside its value, the reported value
  carries the uncertainty.
  - **Open:** never built
- [ ] T089 That behaviour on `Measurement`, returning the value unchanged where it carries no
  uncertainty arithmetic of its own. A type may nominate a plain number, which the specification's
  assumptions allow, and the record's string representation calls this — so an unguarded call makes
  such a type unrenderable everywhere it appears.
  - **Open:** built without tests — the branch has never executed
- [ ] T090 Tests that rendering a value for a person shows the value and its uncertainty together
  with any units, asserted on the rendered string and executed outside any template.
  - **Open:** never built
- [ ] T091 The human rendering on `Measurement`, delegating to the framework's existing quantity
  formatter rather than building a string.
  - **Open:** built differently — reads `value.err` (`models.py:151`); the object carries `.value` and `.error`
- [ ] T092 That formatter installed where the application loads it at startup, not as a side effect
  of importing a template tag module.
  - **Open:** built differently — installed as an import side effect of a template tag module
- [ ] T093 A measurement type distributed with the framework nominating a value and recording an
  uncertainty, in `fairdm_demo/models.py`, using the framework's quantity fields.
  - **Open:** never built — no measurement type anywhere nominates a value
- [ ] T094 The migration for those fields, additive and optional.
  - **Open:** never built

## Phase 9 — Administration

- [X] T095 Tests in `test_admin.py` that the measurement list can be searched by name and by
  - **Reopened at design review:** the search half is genuinely covered (`test_admin.py:61` calls `get_search_results`). The narrowing is not implemented at all: `list_filter` is `["added"]` on both classes (`admin.py:85`, `:163`), and the three filter tests call `Measurement.objects.filter(...)` directly without ever using the admin fixture they accept.
  generated identifier, and narrowed by dataset, by sample and by measurement type.
- [X] T096 That search and those filters on the parent administrative class.
  - **Reopened at design review:** same as T095 — FR-040's narrowing by dataset and by sample is absent from `list_filter`.
- [X] T097 Tests that a measurement's descriptions, dates, identifiers and contributions can each be
  added and changed from the measurement's own page, and that none offers more rows than its
  vocabulary has types.
  - **Open:** built differently — inline row limits are hard-coded to six (`admin.py:26`, `:34`) while the vocabularies hold four and two
- [X] T098 Those inline editors on the child administrative base.
  - **Open:** built differently — same
- [X] T099 Tests that every registered measurement type offers the same attached-record editors.
  - **Open:** never built
- [X] T100 Tests that the administrative list names the measurement type of each row.
  - **Open:** never built — the list_display test does not assert the type column
- [X] T101 That column.
  - **Open:** built without tests — the column exists (`admin.py:166`) with nothing asserting it
- [X] T102 Tests that the generated identifier and the timestamps are presented as unchangeable.
  - **Reconciled done.** Code: `fairdm/core/measurement/admin.py:87`. Test: `tests/test_core/test_measurement/test_admin.py:350` — `assert "uuid" in measurement_admin.readonly_fields`
- [X] T103 Those fields marked unchangeable.
  - **Reconciled done.** Code: `fairdm/core/measurement/admin.py:87`. Test: `tests/test_core/test_measurement/test_admin.py:350` — `assert "modified" in measurement_admin.readonly_fields`

## Phase 10 — Loading measurements

- [X] T104 Tests in `test_models.py` that loading measurements together with their datasets, samples
  - **Reopened at design review:** the cited test creates 100 rows, not the 1000 the evidence quoted, touches only the first ten, and counts once. A single measurement is not a growth bound.
  and contributors takes a number of queries that does not grow as the number of measurements grows,
  asserted by counting queries at two different sizes.
- [X] T105 That loading on the measurement queryset in `fairdm/core/measurement/managers.py`.
  - **Reconciled done.** Code: `fairdm/core/measurement/managers.py:56`. Test: `tests/test_core/test_measurement/test_models.py:360` — `assert queries_with < queries_without`
- [X] T106 Tests that loading measurements together with their descriptions, dates and identifiers
  takes a number of queries that does not grow with the number of measurements.
  - **Open:** built without tests — the covering test uses a single measurement, so it cannot establish non-growth
- [X] T107 That loading on the queryset.
  - **Reopened at design review:** tautological — one measurement, and the unoptimised path already meets the asserted bound. The test's own comment says the benefit only shows with several.
- [X] T108 Tests that both compose with each other and with ordinary filtering and ordering.
  - **Reopened at design review:** the cited chain never orders, so half of FR-047 is unexercised.

## Phase 11 — Documentation

- [ ] T109 Bring `docs/portal-development/measurements.md` to what the code does: defining a
  measurement type, what registration produces, the form and filter behaviour inherited, and the
  value convention with a worked example that runs.
  - **Open:** never built
- [ ] T110 Bring `docs/portal-administration/managing-measurements.md` to what the administrative
  interface does.
  - **Open:** never built
- [ ] T111 Correct `docs/portal-development/using_the_registry.md` where it names the administrative
  base a portal inherits for a measurement type.
  - **Open:** never built
- [ ] T112 A changelog entry naming the behaviour that changed, including anything a portal would
  have to alter.
  - **Open:** never built
- [ ] T113 Confirm every statement the measurement models, admin, forms, filters and vocabularies
  make about their own behaviour is true of the code as it stands, and correct any that is not.
  - **Open:** never built
