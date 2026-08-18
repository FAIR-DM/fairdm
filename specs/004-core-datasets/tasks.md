# Tasks — 004 The dataset record

**Written greenfield.** Every task below describes building this feature from nothing, to the
standard the constitution asks for now. Nothing here was written by reading the existing
implementation. What the code already satisfies is settled in the reconciliation pass that follows,
against a code citation and a passing test — never against this list's own optimism, and never
against the January task list, which reported 162 of 163 done.

Test tasks come before their implementation tasks (Article I). Each task names the file it lands in.

## Phase 0 — Foundations

- [ ] T001 Declare a `Dataset` collection on `FairDMIdentifiers` in `fairdm/core/vocabularies.py`,
  containing `DOI` and no identifier that names a person or an organisation.
- [ ] T002 Generalise the `DOI` member's definition in `fairdm/core/vocabularies.py`; it currently
  describes a link to a project record, and the member is now shared.
- [ ] T003 Confirm the `Dataset` collections on `FairDMDescriptions`, `FairDMDates` and `FairDMRoles`
  exist and contain the members FR-009, FR-010 and FR-018 require.
- [ ] T004 One factory per model in `fairdm/factories/core.py`: `DatasetFactory`,
  `DatasetDescriptionFactory`, `DatasetDateFactory`, `DatasetIdentifierFactory`,
  `DatasetLiteratureRelationFactory`, each using `factory.Sequence` for uniqueness-guarded fields and
  `factory.SubFactory` for relations, and each defaulting `type` to a member of its own vocabulary.
- [ ] T005 Export every dataset factory from `fairdm/factories/__init__.py`.
- [ ] T006 A `LiteratureItemFactory`, wherever the literature package's item is built for tests.
- [ ] T007 Shared fixtures in `tests/test_core/test_dataset/conftest.py` wrapping those factories —
  a public dataset, a private dataset, and a dataset carrying one of every related record.

## Phase 1 — US-8, the record itself

Runs first: it carries the manager change every other story's tests read through.

### Tests

- [x] T008 `TestDatasetIdentity` in `tests/test_core/test_dataset/test_models.py` — the generated
  identifier is unique, prefixed to mark it a dataset, generated rather than supplied, and not
  editable.
  **Done.** Code `fairdm/core/dataset/models.py:552`. Test `tests/test_core/test_dataset/test_models.py:236`, `tests/test_core/test_dataset/test_models.py:242`, `tests/test_core/test_dataset/test_models.py:260`, `tests/test_core/test_dataset/test_models.py:1243`.
- [ ] T009 `TestDatasetFields` — a name is required and its length bound is enforced; a dataset with
  no project is valid; image, project and data publication are each optional.
- [ ] T010 `TestDatasetOrdering` — listing datasets with no ordering applied returns the most
  recently changed first.
- [ ] T011 `TestDatasetLicence` — a dataset created without choosing a licence carries the portal's
  configured default; a portal that sets its own default gets that one instead.
- [ ] T012 `TestDatasetKeywords` — controlled keywords are stored as references to the vocabulary,
  free tags are stored as tags, and the two remain distinguishable.
- [ ] T013 `TestDatasetContributions` — a contribution records a contributor and one or more roles
  and reads both back; the role vocabulary's members are asserted by name.
- [ ] T014 `TestDatasetHasData` — a dataset with neither samples nor measurements reports no data;
  adding either flips it; the check costs a bounded number of queries under
  `django_assert_num_queries`.
- [ ] T015 `TestDatasetPrefetch` — loading a dataset with its descriptions, dates, identifiers,
  contributions and keywords costs a number of queries that does not grow when the number of related
  records grows. Asserted at two different related-record counts, not one.
- [ ] T016 `TestDatasetTranslatable` — model field labels and help text, and vocabulary terms, are
  lazy rather than resolved at import.
- [ ] T017 `TestDatasetVisibilityChoices` — the visibility vocabulary offers private and public and
  nothing else, and the field defaults to private.

### Implementation

- [ ] T018 `Dataset` in `fairdm/core/dataset/models.py`: generated identifier, name, image,
  visibility, licence, project, data publication, keywords and tags. Every field carries
  `verbose_name` and `help_text` through `gettext_lazy` (Article VIII), and every field's indexing is
  a stated decision (Article IX).
- [ ] T019 `Meta.ordering` most-recently-modified first.
- [ ] T020 `DatasetQuerySet` in the same module, offering the bounded-query load of T015 and nothing
  that claims to widen an already-narrowed query.
- [ ] T021 `DatasetManager` excluding private datasets, declared first so it is the default.
- [ ] T022 `all_objects` as the explicit unfiltered manager. Do **not** declare
  `Meta.base_manager_name`: `fairdm.db.models.PrefetchBase` overwrites it with `prefetch_manager`
  after the class is built, and `django-auto-prefetch` raises a system check if it is anything else.
  `prefetch_manager` is unfiltered, so following a relation and deleting a depended-on record already
  see every dataset. T060 and T061 assert that behaviour, not the attribute.
- [ ] T023 `has_data`, as a single bounded query rather than two counts.
- [ ] T024 The migration carrying the above.
- [ ] T025 Rewrite the model's docstrings so every statement they make is true of the code beside
  them (FR-031).

## Phase 2 — US-1, typed descriptions

### Tests

- [x] T026 `TestDatasetDescription` in `test_models.py` — an abstract is stored under its type and
  retrievable by type.
  **Done.** Code `fairdm/core/dataset/models.py:319`. Test `tests/test_core/test_dataset/test_models.py:611`.
- [x] T027 A second description of a type the dataset already carries is refused, and the message
  names the type.
  **Done.** Code `fairdm/core/dataset/models.py:335` (`DatasetDescription.clean()`). Test
  `tests/test_core/test_dataset/test_models.py:627`.
- [x] T028 The refusal holds at the database, so a concurrent write cannot slip past it.
  **Done.** Code `fairdm/core/abstract.py:287` — the `UniqueConstraint` on `(related, type)`.
  Test `tests/test_core/test_dataset/test_models.py:481`. The validation half of the same refusal is
  T027, which is open.
- [x] T029 A methods description is accepted — methods belong to the dataset.
  **Done.** Test `tests/test_core/test_dataset/test_models.py:644`.
- [x] T030 A dataset with two descriptions returns both, each under its own type.
  **Done.** Test `tests/test_core/test_dataset/test_models.py:662`.
- [x] T031 The description vocabulary's members are asserted **by name**. A loop over
  `VOCABULARY.choices` is not this test: it passes over an empty collection.
  **Done.** Test `tests/test_core/test_dataset/test_models.py:680`.
- [x] T032 A type outside the vocabulary is refused by validation.
  **Done.** Code `fairdm/core/abstract.py:247`. Test `tests/test_core/test_dataset/test_models.py:431`.

### Implementation

- [x] T033 `DatasetDescription` bound to the dataset description collection, one row per type
  enforced by a database constraint.
  **Done.** Code `fairdm/core/dataset/models.py:635`, `fairdm/core/dataset/models.py:644`, `fairdm/core/abstract.py:287`. Test `tests/test_core/test_dataset/test_models.py:481`.
- [x] T034 Each field exposed under one name only — no second name for a field (FR-014).
  **Done.** `description_type`/`description` property aliases removed from `DatasetDescription`
  (`fairdm/core/dataset/models.py:319-356`). Call sites updated: `tests/test_core/test_dataset/test_models.py:992`.

## Phase 3 — US-2, dates and the collection period

### Tests

- [x] T035 `TestDatasetDate` — a collection start is stored under its type.
  **Done.** Test `tests/test_core/test_dataset/test_models.py:698`.
- [x] T036 A second date of a type already carried is refused at the database.
  **Done.** Code `fairdm/core/abstract.py:305` — the `UniqueConstraint` on `(related, type)`.
  Test `tests/test_core/test_dataset/test_models.py:383`.
- [x] T037 A collection end earlier than the start is refused, and the message names both dates.
  **Done.** Code `fairdm/core/dataset/models.py:382` (`DatasetDate.clean()`). Test
  `tests/test_core/test_dataset/test_models.py:725`.
- [x] T038 The same refusal when the start is moved after an existing end.
  **Done.** Test `tests/test_core/test_dataset/test_models.py:744`.
- [x] T039 A collection end with no start present is accepted.
  **Done.** Test `tests/test_core/test_dataset/test_models.py:761`.
- [x] T040 Dates of differing precision compare at the coarser precision, so a year and a full date
  do not compare falsely.
  **Done.** Code `fairdm/core/dataset/models.py:432` (`DatasetDate._precedes()`). Tests
  `tests/test_core/test_dataset/test_models.py:772`, `tests/test_core/test_dataset/test_models.py:786`.
- [x] T041 A date record with no value is refused.
  **Done.** Test `tests/test_core/test_dataset/test_models.py:800`.
- [x] T042 The date vocabulary's members are asserted by name.
  **Done.** Test `tests/test_core/test_dataset/test_models.py:812`.
- [x] T043 The check fires through the administrative inline too, where both dates arrive in one
  submission and neither is in the database yet.
  **Done.** Code `fairdm/core/dataset/admin.py:67` (`DateInlineFormSet`). Tests
  `tests/test_core/test_dataset/test_admin.py:390`, `tests/test_core/test_dataset/test_admin.py:428`.

### Implementation

- [x] T044 `DatasetDate` bound to the dataset date collection, one row per type.
  **Done.** Code `fairdm/core/dataset/models.py:673`, `fairdm/core/dataset/models.py:682`. Test `tests/test_core/test_dataset/test_models.py:383`.
- [x] T045 The collection-period check, comparing against the sibling record rather than within one
  instance, at the coarser of the two precisions.
  **Done.** Code `fairdm/core/dataset/models.py:382-445` (`DatasetDate.clean()`, `_sibling_value()`,
  `_precedes()`) — duplicated from `ProjectDate`, not lifted to `AbstractDate` (Article III, R2).
- [x] T046 Each field exposed under one name only.
  **Done.** `date_type`/`date` property aliases removed from `DatasetDate`
  (`fairdm/core/dataset/models.py:359-445`). No call sites outside the removed aliases themselves
  used them (verified by repository-wide grep).

## Phase 4 — US-3, identifiers

### Tests

- [x] T047 `TestDatasetIdentifier` — a DOI is stored under the DOI type.
  **Done.** Code `fairdm/core/dataset/models.py:711`, `fairdm/core/abstract.py:312`. Test `tests/test_core/test_dataset/test_models.py:585`.
- [x] T048 The available types are asserted by name and contain no identifier for a person or an
  organisation.
  **Done.** Test `tests/test_core/test_dataset/test_models.py:830`.
- [x] T049 The same identifier value on a second record is refused, across every record type that
  carries identifiers, not merely within one dataset.
  **Done.** Code `fairdm/core/dataset/models.py:467` (`DatasetIdentifier.clean()`, checks every
  `AbstractIdentifier.__subclasses__()`). Test `tests/test_core/test_dataset/test_models.py:847`.
- [x] T050 **Withdrawn.** Two identifiers of different types on one dataset cannot be
  demonstrated honestly: the collection is `DOI` alone, so there is no second member. The test that
  claimed it wrote a type the vocabulary does not contain through `objects.create()`, which skips
  validation — the exact shape this run exists to remove. Deleted, and US-3's fourth acceptance
  scenario struck from the specification with it (D-021).
- [x] T051 A second identifier of a type already carried is refused at the database.
  **Done.** Code `fairdm/core/abstract.py:324` — the `UniqueConstraint` on `(related, type)`.
  Test `tests/test_core/test_dataset/test_models.py:635`.
- [x] T052 A type outside the vocabulary is refused by validation.
  **Done.** Code `fairdm/core/dataset/models.py:722`, `fairdm/core/abstract.py:247`. Test `tests/test_core/test_dataset/test_models.py:522`.

### Implementation

- [x] T053 `DatasetIdentifier` bound to the dataset identifier collection, one row per type,
  value unique across all identifiers.
  **Done.** Code `fairdm/core/dataset/models.py:464` (`VOCABULARY`), `:467` (cross-model `clean()`).
  A blocking upstream defect surfaced doing this: `research_vocabs`'s `VocabularyBuilder.choices`
  (`core.py:205`) crashes with `TypeError: 'Concept' object is not iterable` on a `from_collection`
  scope with exactly one member, because a single RDF triple doesn't promote to a list the way two or
  more do. `DOI` alone (R3) is exactly that case. Worked around in `fairdm/core/vocabularies.py`
  (`FairDMIdentifiers.choices` override) rather than in the third-party library — see the completion
  report.
- [x] T054 The class attribute naming the identifier types agrees with what the related model binds.
  **Done.** Code `fairdm/core/dataset/models.py:209-214` (`Dataset.IDENTIFIER_TYPES`). Test
  `tests/test_core/test_dataset/test_models.py:873`.
- [x] T055 Each field exposed under one name only.
  **Done.** `identifier_type`/`identifier` property aliases removed from `DatasetIdentifier`
  (`fairdm/core/dataset/models.py:448-487`). Call sites updated: `tests/test_core/test_dataset/test_models.py:1083`,
  `:1145-1146`, `:1201`, and `tests/test_core/test_dataset/test_filters.py` (factory kwargs).

## Phase 5 — US-4, visibility

### Tests

- [x] T056 `TestDatasetVisibility` in `test_models.py` — reading datasets with no visibility
  condition returns only public ones.
  **Done.** Test `tests/test_core/test_dataset/test_models.py:141`.
- [x] T057 The named route to private datasets returns both, and honours a condition applied to it.
  **Done.** Test `tests/test_core/test_dataset/test_models.py:152`.
- [x] T058 No queryset method offers to add private datasets back to a query that has already
  excluded them (FR-019). Asserted over the queryset's public surface, not by naming one method.
  **Done.** Test `tests/test_core/test_dataset/test_models.py:168` — enumerates
  `vars(DatasetQuerySet)`'s own public methods and asserts none reintroduces a PRIVATE row.
- [x] T059 A dataset created with no visibility stated reads back private.
  **Done.** Pre-existing `test_visibility_default_is_private`
  (`tests/test_core/test_dataset/test_models.py:114`) already covered this; strengthened with
  `test_a_dataset_created_with_no_visibility_stated_reads_back_private`
  (`tests/test_core/test_dataset/test_models.py:195`), which reads back through both `all_objects`
  and `objects` rather than the in-memory factory instance.
- [x] T060 Following a relation to a private dataset still finds it.
  **Done.** Test `tests/test_core/test_dataset/test_models.py:217`
  (`TestDatasetVisibilityGuarantees`). Asserts the behaviour (forward FK traversal through
  `DatasetIdentifier.related`), never `Dataset._meta.base_manager_name` (D-019, research.md R1).
- [x] T061 Deleting a record a private dataset depends on still cascades to it.
  **Done.** Test `tests/test_core/test_dataset/test_models.py:233`.
- [x] T062 The administrative dataset list shows private datasets.
  **Done.** Test `tests/test_core/test_dataset/test_admin.py:207`
  (`TestAdminChangelistIncludesPrivateDatasets`).
- [x] T063 Any permission a visibility check consults is declared on the model — asserted by
  reading the model's declared permissions, so a check against an undeclared one cannot survive.
  **Done.** Test `tests/test_core/test_dataset/test_models.py:246`. Scans the dataset app's
  `models.py`/`admin.py` source for `has_perm(...)` calls and asserts every one names a permission
  `Dataset._meta.permissions` (or Django's default add/change/delete/view set) actually declares;
  also asserts `"view_private"` is not among them.

### Implementation

- [x] T064 Wire the privacy-first manager as the default (delivered in T021, verified here).
  **Done, pre-existing.** `DatasetManager` (`fairdm/core/dataset/models.py:159-181`), declared
  first on `Dataset` so it is `_default_manager`. Verified by T056/T059.
- [x] T065 Remove every queryset method that claims to widen an already-narrowed query.
  **Done, pre-existing.** `DatasetQuerySet` (`fairdm/core/dataset/models.py:120-156`) carries only
  prefetch helpers; `with_private`/`get_visible`/`for_user` are absent. Verified by T058.
- [x] T066 Remove the role-to-permission map, which names roles the vocabulary does not contain and
  has no readers.
  **Done, pre-existing.** `Dataset.ROLE_PERMISSIONS` is absent from
  `fairdm/core/dataset/models.py` (D-010).
- [x] T067 Override the administrative queryset to use the unfiltered manager, with the reason
  stated in the code.
  **Done, pre-existing.** `DatasetAdmin.get_queryset()` (`fairdm/core/dataset/admin.py:227-235`)
  returns `Dataset.all_objects.all()`, reason stated in its docstring. Verified by T062.

## Phase 6 — US-5, literature relations

### Tests

- [x] T068 `TestDatasetLiterature` — a dataset names at most one data publication.
  **Done.** Tests `tests/test_core/test_dataset/test_models.py:1345` (new class) —
  `test_a_data_publication_is_recorded_as_the_datasets_reference` (`:1350`) and
  `test_the_same_publication_cannot_be_named_by_two_datasets` (`:1362`), the latter proving the
  `OneToOneField`'s uniqueness the acceptance scenario names.
- [x] T069 Deleting that publication leaves the dataset intact with no publication named.
  **Done.** Test `tests/test_core/test_dataset/test_models.py:1373`.
- [x] T070 A literature item related under a stated type stores both.
  **Done.** Pre-existing `test_create_relation_with_valid_type`
  (`TestDatasetLiteratureRelationValidation`), unskipped (D-016 — the stated reason for the skip
  no longer holds; `LiteratureItemFactory` exists).
- [x] T071 The same item related under a second type retains both relationships.
  **Done.** Pre-existing `test_different_types_allowed` (`TestUniqueTogetherConstraint`),
  unskipped.
- [x] T072 The same relationship recorded twice is refused.
  **Done.** Pre-existing `test_duplicate_relationship_raises_error`
  (`TestUniqueTogetherConstraint`), unskipped.
- [x] T073 The relationship types are asserted by name against the external schema's set.
  **Done.** `test_all_datacite_types_accepted` — a loop over `DATACITE_RELATIONSHIP_TYPES` itself
  proving nothing about its contents — rewritten to
  `test_relationship_types_match_the_datacite_schema_by_name`
  (`tests/test_core/test_dataset/test_models.py:1420`), asserting the 34 DataCite relationType
  codes by name (plan.md's pre-existing-test authorisation table, SC-009).

### Implementation

- [x] T074 The intermediate model carrying dataset, item and relationship type, with the pair-plus-type
  uniqueness enforced at the database and the relationship type indexed.
  **Done, pre-existing.** `DatasetLiteratureRelation` (`fairdm/core/dataset/models.py:79-117`).
  Verified by T070-T072.
- [x] T075 The data-publication relation, surviving the publication's deletion.
  **Done, pre-existing.** `Dataset.reference` (`OneToOneField`, `on_delete=SET_NULL`,
  `fairdm/core/dataset/models.py:280-287` in the current line numbering). Verified by T068/T069.

## Phase 7 — US-6, the administrative interface

### Tests

- [ ] T076 `TestDatasetAdminSearch` in `tests/test_core/test_dataset/test_admin.py` — each search
  term in FR-023 finds a dataset that matches it: name, generated identifier, external identifier,
  project. Each asserted against the result set, not against the page containing a word.
- [ ] T077 `TestDatasetAdminFilters` — each filter narrows to the matching datasets **and** removes
  the non-matching ones.
- [ ] T078 `TestDatasetAdminInlines` — a description, a date and an identifier added inline all
  persist, through a real submission rather than by the page mentioning the word.
- [ ] T079 Each inline offers no more rows than its vocabulary has types.
- [ ] T080 `TestDatasetAdminColumns` — each row shows whether the dataset has an abstract and whether
  it has a DOI, and the list costs a bounded number of queries however many datasets it shows.
- [ ] T081 `TestDatasetAdminActions` — no action changes the visibility of more than one dataset.
- [ ] T082 `TestDatasetAdminReadonly` — the generated identifier and the timestamps cannot be
  changed, asserted against the form's fields rather than against markup.
- [ ] T083 `TestDatasetAdminLicenceWarning` — changing the licence of a dataset carrying a DOI warns
  the administrator; changing it on a dataset with no DOI does not.

### Implementation

- [ ] T084 `DatasetAdmin` with the searches, filters, columns and fieldsets FR-023 to FR-027 require.
- [ ] T085 Inline editors for descriptions, dates and identifiers, each bounded by its vocabulary.
- [ ] T086 The abstract and DOI columns computed in the list query rather than per row.
- [ ] T087 The licence-change warning.
- [ ] T088 The administrative docstrings state only what the code does (FR-031).

## Phase 8 — US-7, the creation record

### Tests

- [x] T089 `TestDatasetCreationRecord` — a dataset created by a known user names that user.
  **Done.** Test `tests/test_core/test_dataset/test_models.py:2015` (new class, mirrors
  `TestProjectCreator`).
- [x] T090 Changing a field advances the modification timestamp and leaves the creator unchanged.
  **Done.** Test `tests/test_core/test_dataset/test_models.py:2024`.
- [x] T091 Removing the creator's account leaves the dataset, with the creator reading as unknown.
  **Done.** Test `tests/test_core/test_dataset/test_models.py:2038`.

### Implementation

- [x] T092 The creator field, surviving the user's removal.
  **Done.** `Dataset.created_by` (`fairdm/core/dataset/models.py:258-268`), copied field-for-field
  from `Project.created_by` (`fairdm/core/project/models.py:113`, `on_delete=SET_NULL`, D-015).
  Migration: added to the existing, unapplied, branch-local `0011_alter_dataset_options_...py`
  rather than a new migration (Article IX; verified branch-local via `git log --all` — the file has
  no history before this branch). `makemigrations --check` is clean for the `dataset` app.
  Test `tests/test_core/test_dataset/test_models.py:2052` asserts `editable=False`.
  Also fixed `DatasetViewSet`, which had no `perform_create` override and so never recorded a
  creator at all (parity gap with `ProjectViewSet.perform_create`, `fairdm/api/viewsets.py:97-107`,
  noted as in-scope by the brief). Added `DatasetViewSet.perform_create`
  (`fairdm/api/viewsets.py:143-152`), with a red-then-green test
  `tests/test_api/test_viewsets.py:216` (`TestDatasetCreatorParity`).
- [x] T093 The creation and modification timestamps.
  **Done, pre-existing.** `added`/`modified` come from `fairdm.db.models.Model`
  (`fairdm/db/models.py:69-77`), inherited by every core model including `Dataset`. Verified by
  T090.

## Phase 9 — Licences available on a portal

### Tests

- [ ] T094 From an empty database, standing up a portal makes the recommended licences available and
  the configured default resolves.
- [ ] T095 Running the step twice changes nothing, including a licence the portal has edited.
- [ ] T096 A portal that declines the step is not given the licences.

### Implementation

- [ ] T097 A command creating the recommended licences, keyed on the licence name.
- [ ] T098 The step added to the pipeline that stands a portal up.
- [ ] T099 The test suite obtains licences through that command rather than by loading a fixture by
  hand.

## Phase 10 — Documentation and closing

- [ ] T100 Docstrings on every public surface this work touches, describing behaviour in testable
  terms (Article VI).
- [ ] T101 A usage example for each public surface a portal author touches.
- [ ] T102 CHANGELOG entry.
- [ ] T103 Every module docstring in the dataset app states only what its module does — no visibility
  level that does not exist, no manager that is not wired, no export that was never written, no path
  to a test file or documentation page that does not exist (FR-031).
- [ ] T104 `makemigrations --check` clean, and the branch's schema migrations consolidated to one.
- [ ] T105 Remove the `needs verification` tag from R4 in `docs/ROADMAP.md`.

## Reconciliation

The list above was written greenfield, then walked against the codebase. A task is ticked only where
a code citation **and** a passing test that genuinely covers it both exist. Nine of one hundred and
five closed.

| | |
|---|---|
| Tasks | 105 |
| Proven done | 9 |
| Open | 96 |

The old `tasks.md` in this directory reported 162 of 163 complete. None of its checkboxes was
consulted; they are a claim by a run that is over.

**Why the open tasks are open:**

| Reason | Count | Examples |
|---|---|---|
| Never built | 54 | the dataset identifier collection, the collection-period check, the creator field, the licence seeding, the abstract and DOI admin columns, the identifier inline |
| Built without a test that covers it | 27 | the literature relations (all eleven tests skipped), the licence-change warning (both tests skip on their first line), keywords and tags, the data publication relation, identifier value uniqueness |
| Built, and the code is what this specification changes | 15 | the queryset methods that claim to widen, the role-to-permission map, the property aliases, the default ordering, the module docstrings |

**Four ticks the first pass wanted and did not get**, recorded because the reasoning is the useful
part:

- *A DOI is stored under the DOI type.* `test_create_doi_identifier` asserts through
  `identifier_type` and `identifier` — the property aliases FR-014 removes — and writes through
  `objects.create()`, which skips validation. It proves nothing about the type. The tick went to
  `test_query_datasets_with_doi` instead, which queries `identifiers__type="DOI"` against real rows
  and asserts membership in both directions.
- *An abstract is stored and retrievable by type.* The only test asserting it reads the alias, and
  nothing retrieves a description by type at all.
- *A methods description is accepted.* One test creates one incidentally, through `objects.create()`.
  Since Django does not validate `choices` on save, that would pass for any string.
- *No administrative action changes visibility in bulk.* The three tests assert that the changelist
  markup does not contain "make public", "make private" or "change visibility". An action named
  anything else would pass. The behaviour has to be read off the administrative class's actions.

That last shape is the one worth naming. **A test that asserts a string is absent from a page proves
almost nothing**, and four of the administrative tests are built that way — readonly fields,
autocomplete, and both inline-presence tests match on words that appear in ordinary Django admin
markup regardless.

**Three ticks were narrowed on a second pass**, for the same reason and in the other direction.
T028, T033 and T036 each claimed the one-row-per-type limit was enforced "at the database as well as
in validation". Their cited tests — `test_unique_together_constraint` at `test_models.py:481`, `:383`
and `:635` — each write a duplicate through `objects.create()` and assert `IntegrityError`, which
skips `full_clean()` entirely. Their cited code lines are the `constraints` blocks on the abstract
bases (`abstract.py:287`, `:305`, `:324`), which are the database half and only the database half.
The claim was cut back to what the evidence carries. T051 was checked and already claimed only the
refusal, so it was left alone.

The validation half is a real requirement — FR-009 states it, SC-002 measures it, and Django 5.2's
`validate_unique()` does check an unconditional `UniqueConstraint`, so the code very likely satisfies
it. **No task claims it.** T027 carries it for descriptions and is open; dates and identifiers have
no equivalent. It is left unclaimed rather than ticked on a plausible reading of the framework, and
no test was invented for it here: writing one is implementation work, and this is a plan.
