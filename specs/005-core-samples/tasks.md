# Tasks — 005 The sample record

**Written greenfield.** Every task below describes building this feature from nothing, to the
standard the constitution asks for now. Nothing here was written by reading the existing
implementation. What the code already satisfies is settled in the reconciliation pass that follows,
against a code citation and a passing test — never against this list's own optimism, and never
against the January task list.

Test tasks come before their implementation tasks (Article I). Each task names the file it lands in.

Three tasks changed at reconciliation, marked `[~]` or noted in place: T028 withdrawn, T044 folded
into T043, T053 restated. Numbers are never reused, because the reconciliation ledger cites them.

## Phase 0 — Foundations

- [ ] T001 Declare a `Sample` collection on `FairDMIdentifiers` in `fairdm/core/vocabularies.py`
  containing `IGSN` and `DOI`, and no identifier that names a person, an organisation or a project.
- [ ] T002 Add an `IGSN` member to `FairDMIdentifiers` in `fairdm/core/vocabularies.py` with its
  definition and its authority's source URL. No member for it exists today.
- [ ] T003 Declare a sample status vocabulary of custody states — available, in use, stored,
  destroyed, unknown — locally, with no remote source, in `fairdm/core/vocabularies.py` alongside
  the other four. Two mechanical constraints, both of which the vocabulary it replaces gets wrong:
  set `Meta.name`, whose absence is why the status filter queries an empty vocabulary name and is
  permanently blank; and name the unknown member in lower case, because the attribute name is the
  stored value and the field's default depends on it.
- [~] T004 **Folded into T034, T038 and T015 at review.** "Confirm a collection exists" produces no
  artifact, so it can never close against a code citation and a passing test. Each of those three
  tasks already has to name its vocabulary's members, which is the same check with an assertion
  behind it.
- [ ] T005 One factory per model in `fairdm/factories/core.py`: `SampleDescriptionFactory`,
  `SampleDateFactory`, `SampleIdentifierFactory`, `SampleRelationFactory`, each using
  `factory.Sequence` for uniqueness-guarded fields, `factory.SubFactory` for relations, and each
  defaulting `type` to a member of its own vocabulary.
- [ ] T006 Make `SampleFactory` in `fairdm/factories/core.py` an abstract factory base, and have the
  reference implementation supply the concrete ones in `fairdm_demo/factories.py`. The framework
  ships the abstract factory; the demo ships a specimen. A concrete factory in
  `fairdm/factories/core.py` would make the framework import its own demo app, which inverts the
  dependency and would ship the demo models as a hard requirement.
- [ ] T007 Export every sample factory from `fairdm/factories/__init__.py`.
- [ ] T008 Shared fixtures in `tests/test_core/test_sample/conftest.py` wrapping those factories — a
  specimen of each registered type, a specimen carrying one of every related record, and a
  three-deep provenance chain.

## Phase 1 — US-10, the record itself

Runs first: every other story's tests are written against the record these tasks define.

### Tests

- [ ] T009 `TestSampleIdentity` in `tests/test_core/test_sample/test_models.py` — the generated
  identifier is unique, prefixed to mark it a sample, generated rather than supplied, and not
  editable afterwards.
- [ ] T010 `TestSampleFields` — a name is required; laboratory identifier, image and location are
  each optional.
- [ ] T011 `TestSampleLocalId` — two specimens in different datasets may carry the same laboratory
  identifier, and both are valid.
- [ ] T012 `TestSampleDatasetRelation` — a specimen belongs to exactly one dataset, and deleting
  that dataset deletes the specimen.
- [ ] T013 `TestSampleLocationRelation` — deleting a location a specimen refers to is refused while
  any specimen refers to it.
- [ ] T014 `TestSampleKeywords` — controlled keywords are stored as references to the vocabulary,
  free tags as tags, and the two remain distinguishable.
- [ ] T015 `TestSampleContributions` — a contribution records a contributor and one or more roles
  and reads both back; the sample role vocabulary's members are asserted by name.
- [ ] T016 `TestSampleTimestamps` — creation and modification times are recorded, and modification
  advances on any change.
- [ ] T017 `TestSamplePrefetch` — loading a list of specimens with their dataset, location,
  descriptions, dates, identifiers, contributions and keywords costs a number of queries that does
  not grow with the number of specimens or of related records. Asserted at two different counts of
  each, not one.
- [ ] T018 `TestSampleQuerySetChaining` — the queryset's own methods chain with one another and with
  ordinary query operations, in either order, and the result is correct rather than merely
  non-empty.
- [ ] T019 `TestSampleTranslatable` — model field labels and help text, and vocabulary terms, are
  lazy rather than resolved at import.

### Implementation

- [ ] T020 The `Sample` model in `fairdm/core/sample/models.py` — generated identifier, name,
  laboratory identifier, image, status, dataset, location, keywords, tags, timestamps and the
  contribution relation, each field carrying `verbose_name` and `help_text` under lazy translation.
- [ ] T021 The dataset relation deletes the specimen with its dataset; the location relation refuses
  a delete while referenced.
- [ ] T022 A queryset in `fairdm/core/sample/managers.py` offering the prefetch T017 requires, in
  one method per group of related records, each chainable.
- [ ] T023 Migrations for the above, one schema file, squashed at convergence.

## Phase 2 — US-1, defining a specimen type

### Tests

- [ ] T024 `TestSamplePolymorphism` in `tests/test_core/test_sample/test_models.py` — querying
  samples without naming a type returns each row as its own type and carries that type's own fields.
- [ ] T025 `TestBaseSampleRefused` — creating a bare base sample is refused through validation,
  through a form, through the administrative interface and through the manager. Each route asserted
  separately, because they fail independently. **Runs with T030 in the foundation group, not here**
  — the block and the factory retargeting are one change.
- [ ] T026 `TestSampleRegistryGeneration` in `tests/test_core/test_sample/test_config.py` — a
  registered specimen type receives a generated form, filter set, table and administrative entry,
  each carrying that type's own fields, asserted by naming the fields rather than by checking the
  object is not `None`.
- [ ] T027 `TestBaseSampleConfiguration` — a specimen type configuration inheriting the base
  configuration receives the base defaults for a component setting it omits.
- [~] T028 **Withdrawn at reconciliation.** Reading rows whose specimen type has left the code as
  base records is not behaviour django-polymorphic offers; building it means a custom real-instance
  fallback, which is a design decision this specification does not make. FR-013 is withdrawn with
  it.

### Implementation

- [ ] T029 The polymorphic base and the registry integration in `fairdm/core/sample/models.py`, using
  the framework's existing registry rather than a mechanism of this record's own.
- [ ] T030 Block creation of the base record at every route T025 names, in
  `fairdm/core/sample/models.py`. A `pre_save` receiver scoped to the base class is the mechanism —
  it is the only one that also covers fixture loading, and it cannot fire on the framework's own
  read path, which constructs base instances on every polymorphic query. `Sample.clean()` stays
  alongside it so forms and the administrative interface still produce a validation error rather
  than a server error. **Runs in the foundation group, after T006 and T094.**
- [ ] T031 A base registry configuration in `fairdm/core/sample/config.py` carrying the component
  defaults every specimen type should inherit.
- [ ] T032 Make the framework's reference specimen types in `fairdm_demo/config.py` inherit that base
  configuration, so the example a portal copies is the one the framework recommends.

## Phase 3 — US-2, typed descriptions

### Tests

- [ ] T033 `TestSampleDescriptions` in `tests/test_core/test_sample/test_models.py` — a description
  of a type in the sample vocabulary is stored under that type and retrievable by type.
- [ ] T034 `TestSampleDescriptionVocabulary` — a type outside the sample vocabulary is refused by
  full validation with a message naming the type, and the vocabulary's members are asserted by name
  rather than by iterating whatever it holds.
- [ ] T035 `TestSampleDescriptionValidationReturns` — full validation of a description returns a
  verdict rather than raising an error of its own. This is the test the current validator fails.

### Implementation

- [ ] T036 `SampleDescription` in `fairdm/core/sample/models.py` with its vocabulary scoped to
  samples and a validator that enumerates the vocabulary correctly.

## Phase 4 — US-3, typed dates

### Tests

- [ ] T037 `TestSampleDates` in `tests/test_core/test_sample/test_models.py` — a date of a type in
  the sample vocabulary is stored under that type.
- [ ] T038 `TestSampleDateVocabulary` — a type outside the sample vocabulary is refused by full
  validation, and the vocabulary's members are asserted by name.
- [ ] T039 `TestSampleDateValidationReturns` — full validation of a date returns a verdict rather
  than raising.

### Implementation

- [ ] T040 `SampleDate` in `fairdm/core/sample/models.py` with its vocabulary scoped to samples and a
  validator that enumerates the vocabulary correctly.

## Phase 5 — US-4, identifiers

### Tests

- [ ] T041 `TestSampleIdentifiers` in `tests/test_core/test_sample/test_models.py` — an IGSN is
  stored under the IGSN type and a DOI under the DOI type.
- [ ] T042 `TestSampleIdentifierVocabulary` — the available types are asserted by name, and none of
  them names a person, an organisation or a project.
- [ ] T043 `TestIGSNFormat` — a malformed IGSN is refused with a message naming the expected format,
  and a well-formed one is accepted. The values used are real examples, and the rule they are
  checked against is the one research establishes rather than the one the old code assumed.
- [~] T044 **Folded into T043 at reconciliation.** Written as a separate task it is a tautology:
  once T001, T002 and T047 put IGSN in the vocabulary, a passing T043 is itself the proof that the
  format check is reachable. T043 carries the requirement.
- [ ] T045 `TestSampleIdentifierUniqueness` — the same identifier value cannot be attached to a
  second record of any type, and a second identifier of a type the specimen already carries is
  refused.
- [ ] T046 `TestSampleIdentifierValidationReturns` — full validation of an identifier returns a
  verdict rather than raising.

### Implementation

- [ ] T047 `SampleIdentifier` in `fairdm/core/sample/models.py` bound to the sample identifier
  collection, with a validator that enumerates the vocabulary correctly.
- [ ] T048 IGSN format validation, to the rule research establishes, with the expected format in the
  message.

## Phase 6 — US-5, status

### Tests

- [ ] T049 `TestSampleStatusVocabulary` in `tests/test_core/test_sample/test_models.py` — the
  members are custody states, asserted by name.
- [ ] T050 `TestSampleStatusDefault` — a specimen created with no status reads as unknown.
- [ ] T051 `TestSampleStatusTransitions` — every transition between states is accepted, including
  out of destroyed.
- [ ] T052 `TestNoRemoteVocabulary` — loading the sample record and creating a specimen both succeed
  with outbound network calls blocked. Asserted by blocking the call, not by reading the source.
- [ ] T053 `TestStatusMigration` in `tests/test_core/test_sample/test_models.py` — insert rows
  carrying the previous vocabulary's values by raw SQL against the base sample table, call the data
  migration's forward callable with the historical model, then assert every row reads unknown.
  **Restated twice.** The original needed a migration-runner harness the project does not depend
  on. The first restatement — "every stored status is a member of the vocabulary" — was vacuous,
  because a test database holds only the rows the test itself created and those are valid by
  construction. Calling the forward function directly tests the thing that matters and needs no new
  dependency.

### Implementation

- [ ] T054 Point `Sample.status` at the local status vocabulary in `fairdm/core/sample/models.py`,
  defaulting to unknown.
- [ ] T055 Retire the remote status vocabulary. `fairdm/core/sample/migrations/0001_initial.py:105`
  names `fairdm.core.choices.SampleStatus` inside a field deconstruction, so deleting the class
  outright makes that file unimportable and breaks migrating from an empty database. Leave an inert
  local stub carrying the old member names for migration history, with a comment saying why, and
  remove the remote source. Also drop the `SampleStatus` import at `fairdm/core/sample/filters.py:155`.
  The report runs `makemigrations --check` and a migrate-from-zero to prove both.
- [ ] T056 A standalone data migration rewriting every existing status value to unknown, through
  `QuerySet.update()` rather than by iterating instances — iterating invokes the field conversion
  that raises on a value the new vocabulary does not contain. It declares
  `reverse_code=migrations.RunPython.noop`, because the previous values are discarded and cannot be
  reconstructed, and a migration with no reverse blocks a rollback of everything after it. It is
  ordered after the field alteration in the same run.

## Phase 7 — US-6, access

### Tests

- [ ] T057 `TestSampleDeclaredPermissions` in `tests/test_core/test_sample/test_permissions.py` —
  every right any check consults is declared on the record, asserted by naming them.
- [ ] T058 `TestSampleDirectPermissions` — a right granted directly on one specimen holds for that
  specimen and not for another. Asserted on a concrete specimen type, not the base record.
- [ ] T059 `TestSamplePermissionInheritance` — reading a dataset confers reading its specimens;
  changing a dataset confers changing them, deleting them and adding to that dataset.
- [ ] T060 `TestSampleNoRights` — a user holding rights on neither the specimen nor its dataset holds
  none over it.
- [ ] T061 `TestSampleWritePluginsAreGated` in `tests/test_core/test_sample/test_plugins.py` — every
  editing surface registered against a specimen refuses an anonymous request and a signed-in user
  with no rights, and admits a user holding change rights on the parent dataset. The reading surface
  stays open.
- [ ] T062 `TestNoUnconditionalPredicate` — no plugin carries an access predicate that returns true
  for every request.

### Implementation

- [ ] T063 A shared permission backend that normalises a polymorphic instance to its base before
  the object-level check. **Gate on the object, not on the permission string** — the underlying
  library only compares application labels when the permission carries one, so a gate keyed on that
  comparison never fires for an unqualified permission, and the failure becomes a silent denial
  rather than an error. Normalise when the instance's real class differs from its polymorphic base
  and that base owns the permission, whether or not the permission is qualified.
- [ ] T100 Re-parent `fairdm/core/sample/permissions.py`, `fairdm/core/measurement/permissions.py`
  and `fairdm/contrib/contributors/permissions.py` onto that backend, so none of them can delegate
  around the normalisation.
- [ ] T101 Register the shared backend in `fairdm/conf/settings/auth.py` in place of the raw
  object-permission backend. Registering it directly matters: leaving the other models' object
  permissions to reach it by delegation through a sample or organisation backend is an unwritten
  contract that the next tidy-up of either backend would silently break.
- [ ] T064 Declare the required permission on every editing plugin in
  `fairdm/core/sample/plugins.py`, and remove the predicate that returns true unconditionally.

## Phase 8 — US-7, the reusable mixins

### Tests

- [ ] T065 `TestSampleFilterMixinInheritance` in `tests/test_core/test_sample/test_filters.py` — a
  filter set for a specimen type inheriting the mixin carries every filter the mixin declares
  alongside its own, asserted by naming the filters.
- [ ] T066 `TestSampleFilterBehaviour` — each inherited filter narrows a queryset correctly, one test
  per filter, over fixtures that would fail if the filter were a no-op.
- [ ] T067 `TestSampleFormMixinWidgets` in `tests/test_core/test_sample/test_forms.py` — the common
  sample fields carry the controls the mixin configures, asserted by widget class rather than by the
  presence of an attribute every widget has.
- [ ] T068 `TestSampleFormDatasetChoices` — a form given the requesting user offers exactly the
  datasets that user may add specimens to; a form given no user offers no dataset that user has not
  been shown to be entitled to. Asserted by comparing the offered set to an expected set.
- [ ] T069 `TestSampleFormHelpText` — the guidance a form defines for a field reaches the rendered
  field.
- [ ] T070 `TestRegistryUsesTheMixins` in `tests/test_core/test_sample/test_config.py` — the form and
  filter set the registry generates for a specimen type supplying neither carry the mixins'
  behaviour rather than plain defaults.

### Implementation

- [ ] T071 Make `SampleFilterMixin` in `fairdm/core/sample/filters.py` a base whose declared filters
  survive inheritance, carrying the filters FR-034 names and no filter that names a field the model
  does not have.
- [ ] T072 `SampleFormMixin` in `fairdm/core/sample/forms.py` — the controls for the common fields,
  the dataset queryset narrowed to what the requesting user may add to, and guidance text that
  reaches the rendered field.
- [ ] T073 Make the registry's generated forms and filter sets for specimen types build on the mixins
  in `fairdm/registry/factories.py`.

## Phase 9 — US-8, provenance

### Tests

- [ ] T074 `TestSampleRelation` in `tests/test_core/test_sample/test_models.py` — one specimen
  recorded as having come from another is readable from both ends.
- [ ] T075 `TestSampleHierarchy` — over a three-deep chain, direct children, direct parents, all
  descendants and all ancestors each return the right specimens and none from the wrong direction.
- [ ] T076 `TestSampleHierarchyDepth` — a depth limit of one returns direct children only, and the
  limit is respected at each further depth.
- [ ] T077 `TestSampleRelationRefusals` — self-reference, a two-step loop and a duplicate link are
  each refused when saved directly, not only under validation.
- [ ] T078 `TestSingleTraversalImplementation` — the record's helpers and its queryset return the
  same specimens for the same question, in the same direction.

### Implementation

- [ ] T079 `SampleRelation` in `fairdm/core/sample/models.py` — the link, its single type, and the
  refusals enforced where they cannot be walked past.
- [ ] T080 One hierarchy traversal in `fairdm/core/sample/managers.py`, with the record's helpers
  delegating to it.

## Phase 10 — US-9, administration

### Tests

- [ ] T081 `TestSampleAdminSearch` in `tests/test_core/test_sample/test_admin.py` — each supported
  search term finds a matching specimen. Asserted through the administrative changelist, not
  through the model manager.
- [ ] T082 `TestSampleAdminFilters` — each supported filter removes the specimens that do not match,
  asserted through the changelist.
- [ ] T083 `TestSampleAdminInlines` — a description, a date, an identifier, a contribution and a
  provenance link can each be added from the specimen's own page.
- [ ] T084 `TestSampleAdminInlineLimits` — the rows each inline editor offers are bounded by the
  number of types its vocabulary contains, and the bound moves when the vocabulary does.
- [ ] T085 `TestSampleAdminTypeColumn` — the changelist names the specimen type of each row.
- [ ] T086 `TestSampleAdminReadonly` — the generated identifier and the timestamps are presented as
  unchangeable.
- [ ] T087 `TestEveryTypeGetsTheInlines` — every registered specimen type offers the same inline
  editors.

### Implementation

- [ ] T088 The administrative interface in `fairdm/core/sample/admin.py` — search, filters, inline
  editors, the type column, the unchangeable fields, and the inline bounds derived from the
  vocabularies.
- [ ] T089 Ensure the administrative entry actually registered for the record carries the inline
  editors, not only the class a specimen type inherits.

## Phase 11 — Closing

- [ ] T090 Remove the specification directory's artifacts from the previous run that no longer
  describe this feature.
- [ ] T091 Module docstrings across `fairdm/core/sample/` describe the code beside them; remove any
  documented behaviour the code does not implement.
- [ ] T092 Changelog entry.
- [ ] T093 Drop the `needs verification` tag from R5 in `docs/ROADMAP.md`.

## Phase 12 — Added at design review

The review blocked the plan on nine findings beyond the reconciliation ones. These are the tasks
that close them.

- [ ] T094 Retarget every `SampleFactory(` call site outside `tests/test_core/test_sample/` to a
  concrete specimen factory — about 140 sites across 14 files, plus the fixture at
  `tests/test_contrib/test_plugins/conftest.py:43` that calls `Sample.objects.create` directly, and
  the two factories that reach the base without naming it (`MeasurementFactory.sample`, both ends of
  `SampleRelationFactory`). This is the bulk of T030's cost and it is separated so that the blocking
  change and the retargeting land together rather than one before the other.
- [ ] T095 A permission-assignment wrapper applying the same normalisation as T063, in
  `fairdm/core/utils.py`. **The backend fixes the check side only** — granting a right takes no part
  in the backend chain, so `assign_perm` on a specimen type still fails after T063. Route the
  framework's own assignment sites through it and correct the examples in
  `fairdm/core/sample/permissions.py`'s docstring, which currently tell a portal developer to make
  the call that fails.
- [ ] T096 `TestObjectPermissionsSurvive` in `tests/test_core/test_sample/test_permissions.py` — a
  right granted on a dataset, on a project and on an organisation still resolves after the backend
  change. These are the models that lose their answering backend when the raw one is removed, and
  nothing else in this work would notice if they stopped resolving.
- [ ] T097 Cross-record identifier uniqueness for `SampleIdentifier`. The uniqueness on the shared
  abstract is per-table, so the same value can name a sample and a dataset at once; the dataset
  record solves this in its own validation and the sample record has no equivalent. Lift the check
  onto the shared abstract so every record type inherits it, rather than copying it a third time.
  The check is validation-only, so T045's test must use full validation rather than creating a row.
- [ ] T098 Update the tests the status change reds: the three that assert the previous vocabulary's
  terms (`tests/test_core/test_sample/test_models.py:132`,
  `tests/test_core/test_sample/test_forms.py:135`,
  `tests/test_core/test_sample/test_filters.py:42`), and the skipped status-filter test whose
  premise the change removes.
- [ ] T099 Remove the unreachable code at `tests/test_core/test_sample/test_admin.py:48` — a second
  `return` referencing two names the module does not define — and resolve the skipped
  `select_subclasses` test at `tests/test_core/test_sample/test_models.py:834`, which SC-011 does not
  permit to stay skipped.
