# Tasks: Browsing a portal's samples and measurements by type

**Input**: Design documents from `/specs/015-browsing-portal-samples/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Requirements satisfied without a dedicated task**: FR-008–010, FR-014, FR-015, FR-016, FR-017,
FR-022, FR-028, FR-035–038, FR-044, FR-045, FR-046 and FR-048 fall directly out of the tasks below
(`DataTableView.get_queryset()`, `TableFactory`/`model_config.get_table_class()`, the shell's
existing pagination and `SearchMixin`, and the T047/T053 rewrites) with no separate line needed.
Each is still asserted by a test task, named against it in the coverage column.

**Requirements satisfied by adding nothing**: FR-005 and FR-006 are prohibitions. FR-005 forbids
any completeness check, review step or state transition on the flag, and FR-006 forbids anything
outside the listings specified here from reading it — the API, the permission layer and every
existing view included. They are met by the field being a bare boolean with no `save()` override,
no signal and no consumer beyond the three `published()` querysets, and T015 is the standing proof
that nothing else changed behaviour.

FR-034, FR-053, FR-054 and FR-055 are boundary requirements — nothing in this plan builds ranking,
typo tolerance, cross-type search, dataset/project/sample-scoped listings, CRUD pages, or a
publication workflow, and no task should be read as license to start one.

**Tests**: included — Article I requires red-green-refactor and a status-code smoke test per
route; the spec's Independent Test for every story is a test task below, not a manual step.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: no ordering dependency on its siblings, so it can be written alongside them. Test tasks
  marked `[P]` often share a test module, because Article X's mirroring rule puts several `Test*`
  classes in one file by design; what `[P]` promises is that neither task's content depends on the
  other's, not that the files are disjoint.
- **[Story]**: which user story owns the task (US1–US6), or `SETUP`/`FOUND`/`POLISH`

## Phase 1: Setup

- [ ] T001 [SETUP] Confirm `fairdm_demo`'s eight registrations still pass `poetry run pytest
      tests/test_registry/` before any change (baseline)

## Phase 2: Foundational (blocks every user story)

**Purpose**: the `published` field and the queryset methods every story reads through. No listing
work can start until this phase is green.

- [ ] T002 [FOUND] Test: `Dataset.published` defaults to `False`, migration leaves existing rows
      unpublished — `tests/test_core/test_dataset/test_models.py` (red first; FR-001, FR-002)
- [ ] T003 [FOUND] Add `Dataset.published` field — `fairdm/core/dataset/models.py` (data-model.md,
      FR-001)
- [ ] T004 [FOUND] Migration for `Dataset.published` — `fairdm/core/dataset/migrations/0012_dataset_published.py`
      (FR-001, FR-002)
- [ ] T006 [P] [FOUND] Test: no page a researcher can reach exposes the flag —
      `tests/test_core/test_dataset/test_forms.py` asserts `DatasetForm.Meta.fields` and the
      create-form field list exclude `published` (FR-004)
- [ ] T007 [P] [FOUND] Test: `Sample.objects.published()` / `Measurement.objects.published()`
      filter on the record's own dataset, not a related one — `tests/test_core/test_sample/test_managers.py`,
      `tests/test_core/test_measurement/test_managers.py` (red first; covers FR-011, FR-012)
- [ ] T008 [FOUND] Add `SampleQuerySet.published()` — `fairdm/core/sample/managers.py` (data-model.md)
- [ ] T009 [FOUND] Add `MeasurementQuerySet.published()` as a bare filter on
      `dataset__published=True` — `fairdm/core/measurement/managers.py`. It carries **no**
      `select_related`: the joins the listing needs are the listing's, and `published()` is also
      called to scope filter choice lists (T040), where those joins are pure waste. The eager
      loading belongs at the view and is T025's deliverable (data-model.md, research.md R3)
- [ ] T067 [P] [FOUND] Test: `Dataset.all_objects.published()` returns published datasets only,
      **including one published while its visibility is private** — the ordinary state, and the
      reason the choice list in T040 cannot use the privacy-first default manager —
      `tests/test_core/test_dataset/test_models.py` (red first; FR-030, D3)
- [ ] T068 [FOUND] Add `DatasetQuerySet.published()` returning `self.filter(published=True)` —
      `fairdm/core/dataset/models.py`. Required by T040: every registered type has a FK to
      `Dataset`, so scoping generated choice lists calls `.published()` on all three querysets
      (data-model.md)
- [ ] T010 [P] [FOUND] Test: `BaseModel.name` carries a database index after migration, asserted
      against `Sample._meta.db_table` and `Measurement._meta.db_table` — as a `TestNameIndex` class
      in `tests/test_core/test_abstract.py` (SC-007; red first). **Not** against an MTI child such
      as `RockSample`, whose own table does not hold `name` at all, and not in a new
      `tests/test_db/` package, which mirrors no source module
- [ ] T011 [FOUND] Add `db_index=True` to `BaseModel.name` — `fairdm/core/abstract.py` — plus the
      **four** migrations it forces: `Sample`, `Measurement`, and also `Project` and `Dataset`,
      which inherit the same abstract field. All four are deliverables of this task, so
      `makemigrations --check` stays clean; the reach is recorded as intended in data-model.md
      under Article IX (research.md R5; FR-027, SC-007)
- [ ] T012 [P] [FOUND] Test: declaring `ModelConfiguration.search_fields` raises
      `FieldValidationError` at import in both failure modes, naming the type and field — a path that
      resolves to nothing, and a path that resolves to a non-text field. Parametrise the second over
      a `DecimalField`, a `BooleanField` and a `DateField`, so a check that happens to reject one of
      them cannot pass — `tests/test_registry/test_config.py` (red first; FR-026)
- [ ] T013 [FOUND] Add `search_fields` to `ModelConfiguration`: attribute, `_OVERRIDABLE` entry,
      validation in two passes — `FieldInspector.resolve_path` per entry, then
      `isinstance(field, (models.CharField, models.TextField))` on the resolved final field — and
      `get_search_fields()` returning `self.search_fields or ["name"]` —
      `fairdm/registry/config.py`. Both passes raise `FieldValidationError`, the class
      `_validate_field_path` already raises (`config.py:334`), so the two refusals read alike.
      The type check is what makes FR-026 hold: `resolve_path` alone passes a `DecimalField`, which
      then raises on the first search a visitor types. It has to be a **positive test for text**,
      not an absence-of-lookup test — Django registers `icontains` on `Field` itself, so
      `get_lookup("icontains")` returns a lookup for every field type there is and would reject
      nothing. `FilterFactory._get_search_fields` (`fairdm/registry/factories.py:648-656`) already
      decides searchability this exact way, and matching it keeps one answer in the codebase
      (data-model.md, research.md R4; FR-023, FR-026)

**Checkpoint**: `Dataset.published`, all three `published()` querysets, the name index, and
`search_fields` all exist and are tested in isolation. User stories can begin.

## Phase 3: User Story 1 — Mark a dataset published (P1) 🎯

**Goal**: the flag exists, persists, and changes nothing else (spec US-1).

**Independent Test**: mark a dataset published in the admin, confirm the value persists, confirm no
other portal page's behaviour changes, confirm the migration leaves existing datasets unpublished.

- [ ] T014 [US1] Test: the admin exposes `published` as an editable field and a list filter, and
      marking it persists independently of `visibility` — `tests/test_core/test_dataset/test_admin.py`
      (red first, before T005; Acceptance Scenarios 2, 5, FR-003)
- [ ] T005 [US1] Add `published` to `DatasetAdmin.fieldsets`, `list_display`, `list_filter` —
      `fairdm/core/dataset/admin.py` (FR-003). Sits in this story, not Foundational: no other story
      reads the admin, and Article I requires T014 red before it
- [ ] T015 [US1] Test: every non-collection portal page renders identically whether `published` is
      `True` or `False` — extend existing `tests/test_core/test_dataset/` view tests with a
      parametrized `published` value (Acceptance Scenario 3, SC-010, FR-006)

Apart from T005, US-1's production code is entirely T002–T013, T067 and T068 (Foundational) — this
story is largely the acceptance proof that those tasks satisfy the spec.

**Checkpoint**: US-1 independently shippable — the flag works and is invisible everywhere it
should be.

## Phase 4: User Story 2 — Browse a type's records (P1) 🎯 MVP

**Goal**: the core listing — published-only, per-type columns, paged, linked, flat query count
(spec US-2).

**Independent Test**: register two sample types and one measurement type, publish one dataset and
leave another unpublished, open each listing signed out, confirm columns differ per type, only
published records appear, paging works.

### Tests for User Story 2 (write first)

- [ ] T016 [P] [US2] Smoke test: every generated listing URL returns 200 for an anonymous client,
      **and each one reverses by its `<slug>-list` name** — a status code passes under either
      naming, so the name is asserted explicitly or T028 is untested —
      `tests/test_contrib/test_collections/test_urls.py`. Creates the package's
      `__init__.py` alongside it, as its sibling test packages carry (Article I, Article X,
      FR-049, FR-051)
- [ ] T072 [P] [US2] Test: two registrations resolving to the same listing address are refused at
      import with `ImproperlyConfigured` naming both models — same file (red first, before T029;
      FR-050)
- [ ] T017 [P] [US2] Test: a listing shows only records from published datasets — identically for a
      signed-out client, the record's owner, a contributor **and portal staff**, since FR-011 names
      all four and a staff client is the one most likely to be widened by accident —
      `tests/test_contrib/test_collections/test_views.py` (Acceptance Scenarios 1, 4, 5, FR-011,
      SC-002, SC-010)
- [ ] T018 [P] [US2] Test: two types with different `fields` declarations produce different columns
      — same file (Acceptance Scenario 2, SC-003)
- [ ] T019 [P] [US2] Test: a type registered with no field declarations renders with framework
      defaults rather than failing — same file (Acceptance Scenario 3)
- [ ] T020 [P] [US2] Test: paging works past one page — same file (Acceptance Scenario 6)
- [ ] T021 [P] [US2] Test: a measurement whose sample's dataset is unpublished shows the row with
      no sample name **and no anchor** — assert the response body contains no href to that sample's
      `get_absolute_url()`, not merely that its name is absent — as a `TestSampleColumn` class in
      `tests/test_contrib/test_collections/test_tables.py` (Acceptance Scenario 7, FR-013)
- [ ] T070 [P] [US2] Test: a dataset that is published while its visibility is private shows its
      records, and no row carries an href to that dataset's page — same file (D3, research.md R14)
- [ ] T022 [P] [US2] Test: a type with no published records renders the empty state's **own words**
      — the heading and message this feature sets, not the shell's "Click the button below to get
      started" — as a `TestEmptyState` class in `test_views.py`, because T027 sets all three hooks
      on the view (Acceptance Scenario 8, FR-018)
- [ ] T023 [P] [US2] Test: selecting a row opens that record's page, **for a measurement listing as
      well as a sample listing** — assert the row carries an href to the record's own
      `get_absolute_url()`. `MeasurementTable` has no such column today, so this is red for
      measurements before T073 — `test_views.py` (Acceptance Scenario 9, FR-019)
- [ ] T024 [P] [US2] Test: query count for one row equals query count for a full page, **for the
      measurement listing as well as the sample listing** — as a `TestQueryCount` class in
      `tests/test_contrib/test_collections/test_views.py`, using `CaptureQueriesContext`
      (Acceptance Scenario 10, FR-020, SC-006; depends on T025's `select_related`,
      `sample__location` included)

### Implementation for User Story 2

- [ ] T025 [US2] Rewrite `DataTableView.get_queryset()` to narrow `super().get_queryset()` through
      `.published()` composed with `.with_related()`, then chain the listing's own
      `select_related("sample__dataset", "sample__location")` for a measurement type —
      `fairdm/contrib/collections/views.py`. Two constraints meet here:
      1. It **must chain from `super()`**, not build a queryset from scratch. A fresh queryset
         bypasses `SearchMixin` and `BaseFilterView` and silently disables US-3 and US-4
         (research.md R1, R6).
      2. The deep `select_related` lands **here, not in `with_related()`**, whose docstring
         (`fairdm/core/measurement/managers.py:40-53`) states outright that it does not prefetch
         nested relationships and that views needing them should chain their own. `sample__location`
         is load-bearing: `MeasurementTable` renders three columns off it (`latitude`, `longitude`,
         `location`), so without it every row costs a query and SC-006 fails. `sample__dataset` is
         what T026's publication read needs (research.md R3, FR-020)
- [ ] T026 [US2] `MeasurementTable`: drop `linkify=True` from the `sample` column and **replace the
      body of the existing `render_sample`** — it currently returns the sample *type's* verbose
      name, and a render method cannot suppress a `linkify` anchor. The new body returns an anchor
      built with `format_html` when `value.dataset.published`, and a `gettext_lazy` placeholder
      otherwise. Also remove `__init__`'s now-redundant `prefetch_related("sample")`, which
      double-fetches once T025 selects it — `fairdm/contrib/collections/tables.py`
      (research.md R2, R3)
- [ ] T071 [US2] `BaseTable`: drop `linkify=True` from the `dataset` column and build the anchor
      inside the existing `render_dataset` only when the dataset is readable (`visibility` is not
      `PRIVATE`), returning the bare icon otherwise. Publication and visibility are independent by
      design, so a published-but-private dataset is the ordinary state and its page refuses the
      visitor — `fairdm/contrib/collections/tables.py` (research.md R14, D3)
- [ ] T073 [US2] `MeasurementTable`: add a linkified column on the measurement's own record,
      mirroring `SampleTable.name` — `fairdm/contrib/collections/tables.py`. The table currently
      links only `sample` and `location`, so a measurement row leads to its sample's page and never
      to its own, and FR-019 fails for every measurement listing. Its header is the one column label
      this feature authors rather than inherits, so it is declared with `gettext_lazy`. Sequenced
      with T026 and T071, which write the same file (FR-019, FR-021, Acceptance Scenario 9)
- [ ] T027 [US2] Empty state, two hooks not one, and all three on the view: supply `empty_text`
      through `get_table_kwargs()` to enable the block, **and** override `empty_state_heading` /
      `empty_state_message` on `DataTableView` with `gettext_lazy` strings written for a public
      read-only listing, built from `model_config.get_verbose_name_plural()`. `empty_text` alone
      only gates the block and leaves the shell's authoring copy on screen. All three land in
      `fairdm/contrib/collections/views.py`, not in `TableFactory` — the copy is the listing page's,
      not the generated table's, and keeping them together is what lets one test class in
      `test_views.py` cover them (research.md R11, FR-018, FR-021)
- [ ] T028 [US2] Rename URL names from `f"{slug}-collection"` to `f"{slug}-list"` in
      `DataTableView.get_urls()` — `fairdm/contrib/collections/views.py`. The literals are all in
      `get_urls()`; `urls.py` holds none of them (research.md R10, FR-049, D7)
- [ ] T029 [US2] Add duplicate-slug detection in `get_urls()`, raising `ImproperlyConfigured` naming
      both models — `fairdm/contrib/collections/views.py` (FR-050)
**Checkpoint**: US-2 independently shippable — a reader can browse any registered type's published
records, paged, linked, with per-type columns and a flat query count. This is the MVP.

## Phase 5: User Story 3 — Narrow a listing to what is wanted (P1)

**Goal**: search, filters, sort, all declared per type, all respecting publication (spec US-3).

**Independent Test**: load a type with enough records to page, search a word held by one, apply
each generated filter, sort each sortable column both ways, confirm each searched-by-default field
is indexed.

### Tests for User Story 3 (write first)

All four concerns below — search, filters, ordering, the switcher — are tested as further
`Test<Subject>` classes in the module of their subject, per Article X. No test file is named after
a concern that mirrors no source module.

- [ ] T031 [P] [US3] Test: with no `search_fields` declared, a word from the record's name matches
      and unrelated records do not — as a `TestSearch` class in
      `tests/test_contrib/test_collections/test_views.py` (Acceptance Scenario 1, FR-024, SC-004)
- [ ] T032 [P] [US3] Test: with `search_fields` declared, a word held only by a declared field
      matches; a word held only by an undeclared field does not — same class (Acceptance Scenarios
      2, 3, FR-025)
- [ ] T033 [P] [US3] Test: a search matching nothing renders the empty state — same class
      (Acceptance Scenario 4)
- [ ] T034 [P] [US3] Test: a search that would match an unpublished record's field returns nothing
      — same class (Acceptance Scenario 5, FR-031)
- [ ] T035 [P] [US3] Test: every generated filter narrows correctly and raises nothing — as a
      `TestFilters` class in `test_views.py` (Acceptance Scenario 6, FR-029)
- [ ] T036 [P] [US3] Test: a related-record filter's choice list excludes values that exist only on
      an unpublished record, for the sample, measurement **and dataset** filters, **and includes a
      dataset that is published while private** — the ordinary state, and the case that fails if
      the choice list is built from `Dataset.objects` — as a `TestPublishedChoiceLists` class in
      `tests/test_registry/test_factories.py`, which mirrors the module the change lands in
      (Acceptance Scenario 7, FR-030, D3)
- [ ] T037 [P] [US3] Test: sorting a sortable column both directions reorders rows; unsorted order
      is stable and repeatable across pages — as a `TestOrdering` class in
      `tests/test_contrib/test_collections/test_tables.py` (Acceptance Scenarios 8, 9, FR-032,
      FR-033)
- [ ] T038 [US3] Test: every field `get_search_fields()` returns for every registered `fairdm_demo`
      type carries a database index when it is the default (`name`) — extends T010's
      `TestNameIndex` in `tests/test_core/test_abstract.py`, introspecting `Sample` and
      `Measurement` tables rather than an MTI child's (Acceptance Scenario 10, SC-007)

### Implementation for User Story 3

- [ ] T030 [US3] Register `search_fields` on at least two `fairdm_demo` sample configs and one
      measurement config, illustrating the default and an explicit declaration —
      `fairdm_demo/config.py` (Article XVIII, FR-025). Sits here rather than in US-2 because T032 is
      the test that fails without it, and Article I puts the test first — a demo registration is
      production code like any other
- [ ] T039 [US3] **Assign** `self.search_fields = self.model_config.get_search_fields()` on
      `DataTableView` before `SearchMixin` runs — `fairdm/contrib/collections/views.py`. Assigning
      the attribute is the requirement, not overriding `get_search_fields()`: the shell publishes
      `context["is_searchable"] = bool(self.search_fields)` by reading the attribute directly, so
      an override alone hides the search box while search still works (research.md R4)
- [ ] T040 [US3] Scope `FilterFactory`'s generated `ModelChoiceFilter` querysets to
      `.published()` when the related model is `Sample`, `Measurement`, or `Dataset` —
      `fairdm/registry/factories.py` `_get_smart_filters`. Depends on T068. **The dataset branch
      goes through `Dataset.all_objects`, not `Dataset.objects`**: the default manager excludes
      private datasets, and a published-but-private dataset is the ordinary state, so
      `Dataset.objects.published()` would leave the filter offering nothing while the table shows
      that dataset's rows. Publication is the only test the listing applies (D1, FR-003)
      (research.md R7, FR-030)
- [ ] T041 [US3] Add `Meta.order_by` to `SampleTable` and `MeasurementTable` so every listing has a
      stable default order without any view declaring `order_by`, **including a unique tie-break** —
      neither declares one today, and `Sample.Meta.ordering` is a single non-unique field, so paging
      can repeat or skip rows and FR-033's "stable and repeatable" fails —
      `fairdm/contrib/collections/tables.py`, on the two base tables every generated table inherits
      from, not in `TableFactory` (D5, FR-033; `MVPTableViewMixin.__init_subclass__` raises if a
      view sets `order_by`, so this must not be a view-level change)

**Checkpoint**: US-3 independently shippable — every listing is searchable, filterable, and
sortable per its own registration, and the index requirement is provably met.

## Phase 6: User Story 4 — Find the listings from the navigation (P2)

**Goal**: every registered type appears in the sidebar automatically, correctly grouped, with no
per-type wiring and no boot failure (spec US-4).

**Independent Test**: register a new type in the demo app, restart, confirm it appears in the
navigation under the correct heading with its declared plural name, confirm the entry opens its
listing.

### Tests for User Story 4 (write first)

Menu population lives in `apps.py`, so its tests are `Test<Subject>` classes in
`tests/test_contrib/test_collections/test_apps.py`.

- [ ] T042 [P] [US4] Test: every `registry.samples` model has a navigation entry under Samples,
      named by `get_verbose_name_plural()` — `tests/test_contrib/test_collections/test_apps.py`
      (Acceptance Scenarios 1, 3)
- [ ] T043 [P] [US4] Test: same for `registry.measurements` under Measurements — same file
      (Acceptance Scenario 2)
- [ ] T044 [P] [US4] Test: selecting a navigation entry opens that type's listing — same file
      (Acceptance Scenario 4)
- [ ] T045 [P] [US4] Test: a portal with **no registered types of one kind** renders no heading for
      it — the assertion is made against an empty registry for that kind, not against the populated
      demo, where it would pass without exercising anything — same file (Acceptance Scenario 5,
      FR-040)
- [ ] T046 [P] [US4] Test: with `fairdm.contrib.collections` removed from `INSTALLED_APPS`, the
      navigation still renders without error — same file, using an isolated settings override
      (Acceptance Scenario 6, FR-041)

### Implementation for User Story 4

- [ ] T047 [US4] Rewrite `populate_data_collection_menu()` — `fairdm/contrib/collections/apps.py`
      — with three changes (research.md R8, FR-039, FR-040):
      0. `view_name=f"{config.get_slug()}-collection"` becomes `-list`, at both call sites
         (`apps.py:37` and `:48`). T028 renamed the URLs and this is the only live consumer of the
         old names, so from T028 landing until this task every navigation entry is a dead link —
         `flex_menu`'s `resolve_url()` swallows the `NoReverseMatch` and logs a warning rather than
         raising, so nothing fails loudly and T044 is what catches it
      1. get-or-create for the Samples/Measurements nodes, mirroring
         `fairdm/contrib/plugins/registration.py:148-157`, so a renamed or absent node cannot raise
         in `ready()`.
      2. a **check** on each node returning false when its registry list is empty. Conditional
         population is not enough on its own: both collapses are declared unconditionally in
         `fairdm/menus/menus.py` at import, and the menu library evaluates suppression only for
         nodes that have children — so a childless node renders as a visible empty heading, which
         is what FR-040 forbids. Set it as `node._check = fn`, or pass `check=fn` when the node is
         constructed. **Not** `node.check = fn`: `check` is a method on `MenuItem`
         (`flex_menu/menu.py:351`) and the per-request copy is built from `self._check`
         (`menu.py:449`), so assigning to `check` shadows the method, is never consulted, and T045
         fails for a reason that reads as unrelated.

**Checkpoint**: US-4 independently shippable — navigation is fully automatic and cannot hard-fail
the portal's boot.

## Phase 7: User Story 5 — Move between listings (P2)

**Goal**: a switcher control on every listing, grouped by kind, current one marked, opens
unnarrowed (spec US-5).

**Independent Test**: with several types of each kind registered, open one listing, confirm the
control lists every other listing grouped by kind and marks the current one, follow it to a listing
of the other kind.

### Tests for User Story 5 (write first)

The switcher is built in `views.py` and rendered from the app's own page template, so its tests are
a `TestSwitcher` class in `tests/test_contrib/test_collections/test_views.py`.

- [ ] T048 [P] [US5] Test: the switcher lists every other registered type's listing —
      `tests/test_contrib/test_collections/test_views.py` (Acceptance Scenario 1)
- [ ] T049 [P] [US5] Test: entries are grouped under Samples and Measurements — same class
      (Acceptance Scenario 2, FR-043)
- [ ] T050 [P] [US5] Test: the current listing is marked — same class (Acceptance Scenario 3)
- [ ] T051 [P] [US5] Test: choosing a measurement type from a sample listing opens it unfiltered,
      even when the originating listing was searched/filtered — same class (Acceptance Scenarios 4,
      6, D6, FR-046)
- [ ] T052 [P] [US5] Test: with exactly one registered type, the switcher does not render a
      no-op control — same class (Acceptance Scenario 5, FR-047)

### Implementation for User Story 5

- [ ] T069 [US5] Create `fairdm/contrib/collections/templates/collections/listing.html`, extending
      the shell's `table_view.html` and overriding **`page.header`** with `{{ block.super }}` first,
      so the switcher renders under the heading, and set `DataTableView.template_name` to it
      explicitly — `fairdm/contrib/collections/views.py`. The block choice is behavioural, not
      cosmetic: `page.actions` is the other candidate and its default body is
      `<c-page.list.actions />`, the search box and buttons, which an override without
      `{{ block.super }}` silently removes and US-3 then fails.
      Without this the app owns no page template: `template_name_suffix = "_table"` resolves to a
      path per *registering* app that a framework cannot provide, and resolution falls through to
      the shell package's own template, which this feature cannot edit. **Runs before T053/T054**
      (research.md R12)
- [ ] T053 [US5] Rebuild `get_context_data()`'s ad hoc list into two grouped lists
      (`sample_listings`, `measurement_listings`), each `{name, url, is_current}`, reversing the
      new `-list` names — `fairdm/contrib/collections/views.py` (research.md R9, FR-042–045)
- [ ] T054 [US5] Render the switcher in `listing.html`, only when the combined list has more than
      one entry. The two group headings (Samples, Measurements) are the switcher's own strings and
      must be wrapped for translation alongside the type labels —
      `fairdm/contrib/collections/templates/collections/listing.html` (FR-047, FR-021)
- [ ] T076 [US5] Test: on a page with more than one registered type the switcher control is
      rendered and carries a link to every other listing — same class. T048–T051 read the context
      the template consumes, and T052 asserts the control's absence, so the rendered positive case
      is the one thing nothing covers: a wrong comparison in the gate hides the switcher on every
      page and all five still pass (FR-042, FR-047)

**Checkpoint**: US-5 independently shippable — every listing can reach every other listing in one
step.

## Phase 8: User Story 6 — Clear away what the app no longer needs (P3)

**Goal**: no dead code, no false documentation, existing tests still pass (spec US-6).

**Independent Test**: confirm each named item is absent, the README describes the code as it
stands, the full suite and the demo app still pass.

- [ ] T074 [P] [US6] Test: a listing response offers no download control in any format, and every
      module remaining in `fairdm/contrib/collections/` is imported by a reachable route or by
      another module in the package — as a `TestNothingUnreachable` class in
      `tests/test_contrib/test_collections/test_views.py`. Deletions alone cannot demonstrate an
      absence, and the suite in T061 cannot detect an unreached template (Acceptance Scenarios 1
      and 2, SC-009, FR-052)
- [ ] T055 [US6] Delete `CollectionRedirectView` — `fairdm/contrib/collections/views.py`
      (FR-056)
- [ ] T056 [P] [US6] Delete `DataTablePlugin` — `fairdm/contrib/collections/plugins.py` (delete
      file if nothing else remains in it) (FR-057)
- [ ] T057 [US6] Delete `export_formats`, `export_choices`, and any download UI —
      `fairdm/contrib/collections/views.py`, its templates (FR-052). Take the dead context with it:
      `get_context_data` publishes `collection_type`, `collection_type_verbose`,
      `current_model_verbose_name`, `current_model_verbose_name_plural`, `available_collections` and
      a hand-built `page` dict, none of which any template in the repository reads. Its
      `description` key is doubly dead — the shell renders `page.subtitle`, and the English string
      advertises the download this task removes. Confirm each key has no consumer, then delete it
- [ ] T058 [P] [US6] Delete `templates/collections/table.html` and
      `templatetags/collection_tags.py` (unused once T057/T056 land; the tag library's only loader
      is `table.html`, and the new `listing.html` from T069 loads none) — confirm no other
      reference first. Also delete the commented `DJANGO_TABLES2_TEMPLATE` line naming that path at
      `fairdm/conf/settings/apps.py:246`, which would otherwise point at a file that no longer
      exists (FR-058)
- [ ] T059 [US6] Delete `CollectionsOverview`, `SamplesOverview` and `MeasurementsOverview`,
      their three templates, and their routes — `fairdm/contrib/collections/views.py`,
      `templates/collections/`, `urls.py`. No deferral: their URL names (`data-collections`,
      `samples-overview`, `measurements-overview`) are reversed only from `urls.py` and the three
      templates deleted here, no other template, view or test in the repository reaches them, and
      no story asks for a portal-wide overview page (research.md R12)
- [ ] T075 [US6] Delete `BasePolymorphicModel.get_collection_url()` — `fairdm/core/abstract.py:176`.
      It reverses `f"{slug}-collection"`, a name T028 removed, so it now raises `NoReverseMatch` for
      every model that inherits it. Nothing in the repository calls it — confirm that by grep before
      deleting, and take its test with it only if one exists that asserts nothing else (FR-058)
- [ ] T060 [US6] Rewrite `fairdm/contrib/collections/README.md` against the code as it now stands —
      every named component exists, every example works (FR-059)
- [ ] T061 [US6] Test: the full suite passes, and `git log` shows no test deleted without a
      recorded decision — run `poetry run pytest` and `poetry run pytest fairdm_demo/tests/`
      (Acceptance Scenario 4, Article XVIII). **`fairdm_demo/tests/` is red before this branch
      starts**: `test_admin_views.py::TestICPMSMeasurementAdminViews::test_change_view_loads_without_error`,
      `test_admin_views.py::TestAllMeasurementAdminViewsWork::test_all_measurement_change_views_load`
      and `test_contributors.py::TestDemoPersonCreation::test_demo_person_creation` all fail on
      `8c9290f`, the commit this branch left `main` at, and none of them is this feature's to fix.
      The bar here is therefore **no new failure** rather than a green run: reproduce the three at
      the base commit, confirm the set at HEAD is the same three and no larger, and say so. A fourth
      failure is a real regression and blocks
- [ ] T077 [US6] Delete the residue the deletions left behind, which the reachability test in T074
      cannot see: the now-empty `templatetags/` package (its only module went with T058, and
      `__init__.py` is excluded from the reachability walk by design), and the commented-out block
      in `DataTableView.get_urls()` that returns `f"{slug}-collection"` — a URL name T028 removed,
      so the comment describes an address that no longer exists (FR-058)

**Checkpoint**: all six stories independently shippable; the app contains only reachable code.

## Phase 9: Polish & documentation

- [ ] T062 [P] [POLISH] New docs page: what registering a type produces, how to override one piece
      without losing the rest, that a declared field beyond the default is the author's to index —
      `docs/portal-development/listing-a-registered-type.md`, linked from
      `docs/portal-development/index.md` (FR-060)
- [x] T063 [P] [POLISH] Annotate FS-014 FR-066 in place as superseded by this feature, pointing here
      — `specs/014-dataset-crud-views/spec.md` (FR-007). Already done: the requirement is struck
      through and forward-tagged at `specs/014-dataset-crud-views/spec.md:452-458`
- [ ] T064 [POLISH] Run `quickstart.md` end to end against the demo app. It is the only check on
      SC-001 — a portal author who registers a type and writes nothing else gets a working listing,
      reachable from the navigation, with no URL entry and no menu entry written by hand. That is a
      claim about the authoring experience, and no automated test states it. SC-005 is a reader
      criterion, not an authoring one, and it is already covered by T048–T052
- [ ] T065 [POLISH] Confirm coverage on `fairdm/contrib/collections/` meets the project floor
      (`codecov.yml`: project ≥ 90%, patch ≥ 85%, each with a 1% threshold) — the app had zero tests
      before this feature (SC-008)
- [ ] T066 [POLISH] Consolidate this branch's migrations per Article IX before merge
- [ ] T078 [POLISH] Close the review's publication leak in the filter choice lists: a
      `PublishedChoicesMixin` in `fairdm/registry/factories.py` narrowing every filter whose own
      queryset is over `Sample`, `Measurement` or `Dataset`, applied by
      `DataTableView.get_filterset_class()` to whatever filter set it is handed, so the three tiers
      of the configuration API are all covered. Five tests on the rendered page's own filter set,
      not on the generated class (FR-030, SC-002, decisions.md D24)
- [ ] T079 [POLISH] Move the Samples/Measurements emptiness check onto the headings' own
      declaration in `fairdm/menus/menus.py`, where it holds for a portal that does not install
      `fairdm.contrib.collections` — the app's `ready()` now supplies it only for a heading it has
      to create itself (FR-040, FR-041)
- [ ] T080 [POLISH] Correct the two documentation claims the review checked against the code: the
      README's "linkified sample column", and ADR 0015's "goes blank" for a cell whose record the
      visitor cannot read (FR-059)

## Dependencies & execution order

- **Setup (T001)** — no dependencies.
- **Foundational (T002–T013, T067, T068)** — blocks every user story. `published`, all three
  `published()` querysets, the name index, and `search_fields` must all exist and be tested first.
- **US1 (T014, T005, T015)** depends only on Foundational — it is largely the acceptance proof for
  T002–T013, T067 and T068, plus the one admin change no other story reads.
- **US2 (T016, T072, T017–T024, T070, T025–T029, T071, T073)** depends on Foundational. This is the
  MVP, and every later story depends on `DataTableView` existing in its rebuilt form.
- **US3 (T031–T038, T030, T039–T041)** depends on US2 (`DataTableView.get_queryset()` from T025 must
  exist before search/filter/sort compose with it). T030 declares `search_fields` on the demo
  configs and sits here, behind T032, because that is the test that fails without it.
- **US4 (T042–T047)** depends on Foundational and on US2's URL names (T028) for its "entry leads to
  that listing" assertions, but not on US3.
- **US5 (T048–T054, T069)** depends on US2's URL renaming (T028) and benefits from US4 existing
  (shares the registry-iteration pattern) but does not require US3. T069 creates `listing.html` and
  runs before T053 and T054, which render the switcher into it.
- **US6 (T074, T055–T059, T075, T060, T061)** should run last among the stories — it deletes code some earlier tasks might
  still be reading during development, and it is explicitly "the story to drop if the run runs
  short" (decisions.md D8).
- **Polish (T062–T066)** depends on all six stories.

### Shared files, and what that forces

Four of the six stories write to the same two modules, so they are **not** independently
parallelisable however independently shippable they are. `fairdm/registry/factories.py` is US-3's
alone (T040) once T027's empty state is settled onto the view:

| File | Stories that write it |
|---|---|
| `fairdm/contrib/collections/views.py` | US-2 (T025, T027, T028, T029), US-3 (T039), US-5 (T069, T053), US-6 (T055, T057, T059) |
| `fairdm/contrib/collections/tables.py` | US-2 (T026, T071, T073), US-3 (T041) |

So the four land **in sequence, US-2 → US-3 → US-5 → US-6**, one at a time. That is the order the
dependency list already gives for other reasons, so the constraint costs nothing: no two of them
were going to be written concurrently regardless.

## Parallel opportunities

Parallelism is within a story, never across the four that share `views.py`.

- Within Foundational: T002, T006, T007, T010, T012, T067 (all test-writing, different files) can
  run in parallel once their corresponding production task is scoped.
- Within US2: every test task (T016, T072, T017–T024, T070) in parallel; then T025–T029 sequential
  in `views.py`, and T026, T071, T073 sequential in `tables.py`. The two files can proceed
  alongside each other.
- Within US3: T031–T038 in parallel.
- Within US4: all test tasks in parallel, then T047.
- Within US5: all test tasks in parallel; then T069 before T053 and T054, which are sequential.
- Within US6: T074 first (red), then T056 and T058 in parallel — they delete different files. T055,
  T057 and T059 are sequential: all three edit `views.py`. T060, then T061, last.
