# Tasks: Browsing a portal's samples and measurements by type

**Input**: Design documents from `/specs/015-browsing-portal-samples/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Requirements satisfied without a dedicated task**: FR-008–010, FR-014, FR-016, FR-017, FR-019,
FR-022, FR-023, FR-028, FR-035–038, FR-044, FR-045 and FR-048 fall directly out of the tasks above
(`DataTableView.get_queryset()`, `TableFactory`/`model_config.get_table_class()`, the shell's
existing pagination and `SearchMixin`, and the T047/T053 rewrites) with no separate line needed.
FR-034, FR-053, FR-054 and FR-055 are boundary requirements — nothing in this plan builds ranking,
typo tolerance, cross-type search, dataset/project/sample-scoped listings, CRUD pages, or a
publication workflow, and no task should be read as license to start one.

**Tests**: included — Article I requires red-green-refactor and a status-code smoke test per
route; the spec's Independent Test for every story is a test task below, not a manual step.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no shared state)
- **[Story]**: which user story owns the task (US1–US6), or `SETUP`/`FOUND`/`POLISH`

## Phase 1: Setup

- [ ] T001 Confirm `fairdm_demo`'s eight registrations still pass `poetry run pytest tests/test_registry/` before any change (baseline)
- [ ] T001a [SETUP] Bump `django-mvp` to `>=0.20.0,<0.21.0` in `pyproject.toml`, `poetry lock`,
      reinstall. django-mvp 0.20.0 removes `MVPInlineCreateView`/`MVPInlineUpdateView` (fairdm uses
      neither — confirmed by grep) and changes the default theme pair (fairdm sets no
      `MVP_CONFIG["theme"]` override — confirmed). Neither change touches `MVPTableViewMixin`,
      `SearchMixin`, `PageMixin`, or any mechanism this plan reads through; `poetry run pytest` must
      stay green after the bump with no other code change required

## Phase 2: Foundational (blocks every user story)

**Purpose**: the `published` field and the queryset methods every story reads through. No listing
work can start until this phase is green.

- [ ] T002 [FOUND] Test: `Dataset.published` defaults to `False`, migration leaves existing rows
      unpublished — `tests/test_core/test_dataset/test_models.py` (red first)
- [ ] T003 [FOUND] Add `Dataset.published` field — `fairdm/core/dataset/models.py` (data-model.md)
- [ ] T004 [FOUND] Migration for `Dataset.published` — `fairdm/core/dataset/migrations/0012_dataset_published.py`
- [ ] T005 [FOUND] Add `published` to `DatasetAdmin.fieldsets`, `list_display`, `list_filter` —
      `fairdm/core/dataset/admin.py` (FR-003)
- [ ] T006 [P] [FOUND] Test: no page a researcher can reach exposes the flag —
      `tests/test_core/test_dataset/test_forms.py` asserts `DatasetForm.Meta.fields` and the
      create-form field list exclude `published` (FR-004)
- [ ] T007 [P] [FOUND] Test: `Sample.objects.published()` / `Measurement.objects.published()`
      filter on the record's own dataset, not a related one — `tests/test_core/test_sample/test_managers.py`,
      `tests/test_core/test_measurement/test_managers.py` (red first; covers FR-011, FR-012)
- [ ] T008 [FOUND] Add `SampleQuerySet.published()` — `fairdm/core/sample/managers.py` (data-model.md)
- [ ] T009 [FOUND] Add `MeasurementQuerySet.published()` with `select_related("dataset", "sample__dataset")`
      — `fairdm/core/measurement/managers.py` (research.md R3)
- [ ] T010 [P] [FOUND] Test: `BaseModel.name` carries a database index after migration —
      `tests/test_db/test_indexes.py` or equivalent (SC-007; red first)
- [ ] T011 [FOUND] Add `db_index=True` to `BaseModel.name` — `fairdm/core/abstract.py`, plus the
      migrations it forces on `Sample`/`Measurement` concrete subtypes (research.md R5)
- [ ] T012 [P] [FOUND] Test: declaring `ModelConfiguration.search_fields` with a bad path is
      refused at import, naming the type and field — `tests/test_registry/test_config.py` (red
      first; FR-026)
- [ ] T013 [FOUND] Add `search_fields` to `ModelConfiguration`: attribute, `_OVERRIDABLE` entry,
      validation via `FieldInspector.resolve_path`, `get_search_fields()` returning
      `self.search_fields or ["name"]` — `fairdm/registry/config.py` (data-model.md, research.md R4)

**Checkpoint**: `Dataset.published`, both `published()` querysets, the name index, and
`search_fields` all exist and are tested in isolation. User stories can begin.

## Phase 3: User Story 1 — Mark a dataset published (P1) 🎯

**Goal**: the flag exists, persists, and changes nothing else (spec US-1).

**Independent Test**: mark a dataset published in the admin, confirm the value persists, confirm no
other portal page's behaviour changes, confirm the migration leaves existing datasets unpublished.

- [ ] T014 [US1] Test: marking published in the admin persists and is independent of `visibility`
      — `tests/test_core/test_dataset/test_admin.py` (Acceptance Scenarios 2, 5)
- [ ] T015 [US1] Test: every non-collection portal page renders identically whether `published` is
      `True` or `False` — extend existing `tests/test_core/test_dataset/` view tests with a
      parametrized `published` value (Acceptance Scenario 3)

US-1's production code is entirely T002–T013 (Foundational) — this story is the acceptance proof
that those tasks satisfy the spec, not new code of its own.

**Checkpoint**: US-1 independently shippable — the flag works and is invisible everywhere it
should be.

## Phase 4: User Story 2 — Browse a type's records (P1) 🎯 MVP

**Goal**: the core listing — published-only, per-type columns, paged, linked, flat query count
(spec US-2).

**Independent Test**: register two sample types and one measurement type, publish one dataset and
leave another unpublished, open each listing signed out, confirm columns differ per type, only
published records appear, paging works.

### Tests for User Story 2 (write first)

- [ ] T016 [P] [US2] Smoke test: every generated listing URL returns 200 for an anonymous client —
      `tests/test_contrib/test_collections/test_urls.py` (Article I, FR-051)
- [ ] T017 [P] [US2] Test: a listing shows only records from published datasets, for signed-out and
      signed-in-as-owner clients alike — `tests/test_contrib/test_collections/test_views.py`
      (Acceptance Scenarios 1, 4, 5)
- [ ] T018 [P] [US2] Test: two types with different `fields` declarations produce different columns
      — same file (Acceptance Scenario 2)
- [ ] T019 [P] [US2] Test: a type registered with no field declarations renders with framework
      defaults rather than failing — same file (Acceptance Scenario 3)
- [ ] T020 [P] [US2] Test: paging works past one page — same file (Acceptance Scenario 6)
- [ ] T021 [P] [US2] Test: a measurement whose sample's dataset is unpublished shows the row with
      no sample name and no link — same file (Acceptance Scenario 7, FR-013)
- [ ] T022 [P] [US2] Test: a type with no published records shows its empty state, not a blank
      table — same file (Acceptance Scenario 8, FR-018)
- [ ] T023 [P] [US2] Test: selecting a row opens that record's page — same file (Acceptance
      Scenario 9)
- [ ] T024 [US2] Test: query count for one row equals query count for a full page —
      `tests/test_contrib/test_collections/test_queries.py`, using `CaptureQueriesContext`
      (Acceptance Scenario 10, SC-006; depends on T009's `select_related`)

### Implementation for User Story 2

- [ ] T025 [US2] Rewrite `DataTableView.get_queryset()` to return `self.model.objects.published()`
      composed with `.with_related()` — `fairdm/contrib/collections/views.py` (research.md R1, R6)
- [ ] T026 [US2] `render_sample` on `MeasurementTable`: suppress name and link when
      `value.dataset.published` is falsy — `fairdm/contrib/collections/tables.py` (research.md R2)
- [ ] T027 [US2] Set `Meta.empty_text` (or construction-time `empty_text=`) on generated tables from
      `model_config.get_verbose_name_plural()`, translatable — `fairdm/contrib/collections/views.py`
      or `fairdm/registry/factories.py` `TableFactory` (research.md R11, FR-018, FR-021)
- [ ] T028 [US2] Rename URL names from `f"{slug}-collection"` to `f"{slug}-list"` in
      `DataTableView.get_urls()` — `fairdm/contrib/collections/urls.py`,
      `fairdm/contrib/collections/views.py` (research.md R10, FR-049, D7)
- [ ] T029 [US2] Add duplicate-slug detection in `get_urls()`, raising `ImproperlyConfigured` naming
      both models — `fairdm/contrib/collections/views.py` (FR-050)
- [ ] T030 [US2] Register `search_fields` on at least two `fairdm_demo` sample configs and one
      measurement config, illustrating the default and an explicit declaration —
      `fairdm_demo/config.py` (Article XVIII)

**Checkpoint**: US-2 independently shippable — a reader can browse any registered type's published
records, paged, linked, with per-type columns and a flat query count. This is the MVP.

## Phase 5: User Story 3 — Narrow a listing to what is wanted (P1)

**Goal**: search, filters, sort, all declared per type, all respecting publication (spec US-3).

**Independent Test**: load a type with enough records to page, search a word held by one, apply
each generated filter, sort each sortable column both ways, confirm each searched-by-default field
is indexed.

### Tests for User Story 3 (write first)

- [ ] T031 [P] [US3] Test: with no `search_fields` declared, a word from the record's name matches
      and unrelated records do not — `tests/test_contrib/test_collections/test_search.py`
      (Acceptance Scenario 1, FR-024)
- [ ] T032 [P] [US3] Test: with `search_fields` declared, a word held only by a declared field
      matches; a word held only by an undeclared field does not — same file (Acceptance Scenarios
      2, 3, FR-025)
- [ ] T033 [P] [US3] Test: a search matching nothing renders the empty state — same file
      (Acceptance Scenario 4)
- [ ] T034 [P] [US3] Test: a search that would match an unpublished record's field returns nothing
      — same file (Acceptance Scenario 5, FR-031)
- [ ] T035 [P] [US3] Test: every generated filter narrows correctly and raises nothing —
      `tests/test_contrib/test_collections/test_filters.py` (Acceptance Scenario 6, FR-029)
- [ ] T036 [P] [US3] Test: a related-record filter's choice list excludes values that exist only on
      an unpublished record — same file (Acceptance Scenario 7, FR-030)
- [ ] T037 [P] [US3] Test: sorting a sortable column both directions reorders rows; unsorted is
      stable and repeatable — `tests/test_contrib/test_collections/test_ordering.py` (Acceptance
      Scenarios 8, 9, FR-032, FR-033)
- [ ] T038 [US3] Test: every field in `get_search_fields()` for every registered `fairdm_demo` type
      carries a database index when it is the default (`name`) — extends T010's index test
      (Acceptance Scenario 10, SC-007)

### Implementation for User Story 3

- [ ] T039 [US3] Wire `self.search_fields = self.model_config.get_search_fields()` into
      `DataTableView` before `SearchMixin` runs — `fairdm/contrib/collections/views.py`
      (research.md R4)
- [ ] T040 [US3] Scope `FilterFactory`'s generated `ModelChoiceFilter` querysets to
      `.published()` when the related model is `Sample`, `Measurement`, or `Dataset` —
      `fairdm/registry/factories.py` `_get_smart_filters` (research.md R7, FR-030)
- [ ] T041 [US3] Confirm/adjust table `Meta.order_by` defaults so every listing has a stable
      default order without any view declaring `order_by` — `fairdm/contrib/collections/tables.py`
      or `TableFactory` (D5, FR-033; `MVPTableViewMixin.__init_subclass__` raises if a view sets
      `order_by`, so this must not be a view-level change)

**Checkpoint**: US-3 independently shippable — every listing is searchable, filterable, and
sortable per its own registration, and the index requirement is provably met.

## Phase 6: User Story 4 — Find the listings from the navigation (P2)

**Goal**: every registered type appears in the sidebar automatically, correctly grouped, with no
per-type wiring and no boot failure (spec US-4).

**Independent Test**: register a new type in the demo app, restart, confirm it appears in the
navigation under the correct heading with its declared plural name, confirm the entry opens its
listing.

### Tests for User Story 4 (write first)

- [ ] T042 [P] [US4] Test: every `registry.samples` model has a navigation entry under Samples,
      named by `get_verbose_name_plural()` — `tests/test_contrib/test_collections/test_menus.py`
      (Acceptance Scenarios 1, 3)
- [ ] T043 [P] [US4] Test: same for `registry.measurements` under Measurements — same file
      (Acceptance Scenario 2)
- [ ] T044 [P] [US4] Test: selecting a navigation entry opens that type's listing — same file
      (Acceptance Scenario 4)
- [ ] T045 [P] [US4] Test: a portal with no registered types of one kind shows no empty heading for
      it — same file (Acceptance Scenario 5, FR-040)
- [ ] T046 [P] [US4] Test: with `fairdm.contrib.collections` removed from `INSTALLED_APPS`, the
      navigation still renders without error — same file, using an isolated settings override
      (Acceptance Scenario 6, FR-041)

### Implementation for User Story 4

- [ ] T047 [US4] Rewrite `populate_data_collection_menu()` with get-or-create for the Samples/
      Measurements nodes (mirroring `fairdm/contrib/plugins/registration.py:148-157`), and only
      create/populate a kind's node when its registry list is non-empty —
      `fairdm/contrib/collections/apps.py` (research.md R8, FR-039, FR-040)

**Checkpoint**: US-4 independently shippable — navigation is fully automatic and cannot hard-fail
the portal's boot.

## Phase 7: User Story 5 — Move between listings (P2)

**Goal**: a switcher control on every listing, grouped by kind, current one marked, opens
unnarrowed (spec US-5).

**Independent Test**: with several types of each kind registered, open one listing, confirm the
control lists every other listing grouped by kind and marks the current one, follow it to a listing
of the other kind.

### Tests for User Story 5 (write first)

- [ ] T048 [P] [US5] Test: the switcher lists every other registered type's listing —
      `tests/test_contrib/test_collections/test_switcher.py` (Acceptance Scenario 1)
- [ ] T049 [P] [US5] Test: entries are grouped under Samples and Measurements — same file
      (Acceptance Scenario 2)
- [ ] T050 [P] [US5] Test: the current listing is marked — same file (Acceptance Scenario 3)
- [ ] T051 [P] [US5] Test: choosing a measurement type from a sample listing opens it unfiltered,
      even when the originating listing was searched/filtered — same file (Acceptance Scenarios 4,
      6, D6, FR-046)
- [ ] T052 [P] [US5] Test: with exactly one registered type, the switcher does not render a
      no-op control — same file (Acceptance Scenario 5, FR-047)

### Implementation for User Story 5

- [ ] T053 [US5] Rebuild `get_context_data()`'s ad hoc list into two grouped lists
      (`sample_listings`, `measurement_listings`), each `{name, url, is_current}`, reversing the
      new `-list` names — `fairdm/contrib/collections/views.py` (research.md R9, FR-042–045)
- [ ] T054 [US5] Template: render the switcher only when the combined list has more than one entry
      — `fairdm/contrib/collections/templates/collections/` (wherever `DataTableView`'s template
      resolves — confirm against `table_view.html` override point) (FR-047)

**Checkpoint**: US-5 independently shippable — every listing can reach every other listing in one
step.

## Phase 8: User Story 6 — Clear away what the app no longer needs (P3)

**Goal**: no dead code, no false documentation, existing tests still pass (spec US-6).

**Independent Test**: confirm each named item is absent, the README describes the code as it
stands, the full suite and the demo app still pass.

- [ ] T055 [P] [US6] Delete `CollectionRedirectView` — `fairdm/contrib/collections/views.py`
      (FR-056)
- [ ] T056 [P] [US6] Delete `DataTablePlugin` — `fairdm/contrib/collections/plugins.py` (delete
      file if nothing else remains in it) (FR-057)
- [ ] T057 [P] [US6] Delete `export_formats`, `export_choices`, and any download UI —
      `fairdm/contrib/collections/views.py`, its templates (FR-052)
- [ ] T058 [P] [US6] Delete `templates/collections/table.html` and
      `templatetags/collection_tags.py` (unused once T057/T056 land) — confirm no other reference
      first (FR-058)
- [ ] T059 [US6] Decide and act on `CollectionsOverview`/`SamplesOverview`/`MeasurementsOverview`
      and their templates per research.md R12 — delete if no story reaches them, keep only if a
      route to them is still needed
- [ ] T060 [US6] Rewrite `fairdm/contrib/collections/README.md` against the code as it now stands —
      every named component exists, every example works (FR-059)
- [ ] T061 [US6] Test: the full suite passes, and `git log` shows no test deleted without a
      recorded decision — run `poetry run pytest` and `poetry run pytest fairdm_demo/tests/`
      (Acceptance Scenario 4, Article XVIII)

**Checkpoint**: all six stories independently shippable; the app contains only reachable code.

## Phase 9: Polish & documentation

- [ ] T062 [P] [POLISH] New docs page: what registering a type produces, how to override one piece
      without losing the rest, that a declared field beyond the default is the author's to index —
      `docs/portal-development/listing-a-registered-type.md`, linked from
      `docs/portal-development/index.md` (FR-060)
- [ ] T063 [P] [POLISH] Annotate FS-014 FR-066 in place as superseded by this feature, pointing here
      — `specs/014-dataset-crud-views/spec.md` (FR-007)
- [ ] T064 [POLISH] Run `quickstart.md` end to end against the demo app
- [ ] T065 [POLISH] Confirm coverage on `fairdm/contrib/collections/` meets the project floor
      (`codecov.yml`: patch ≥ 85%) — the app had zero tests before this feature (SC-008)
- [ ] T066 [POLISH] Consolidate this branch's migrations per Article IX before merge

## Dependencies & execution order

- **Setup (T001)** — no dependencies.
- **Foundational (T002–T013)** — blocks every user story. `published`, both `published()`
  querysets, the name index, and `search_fields` must all exist and be tested first.
- **US1 (T014–T015)** depends only on Foundational — it is the acceptance proof for T002–T013.
- **US2 (T016–T030)** depends on Foundational. This is the MVP; every later story depends on
  `DataTableView` existing in its rebuilt form.
- **US3 (T031–T041)** depends on US2 (`DataTableView.get_queryset()` from T025 must exist before
  search/filter/sort compose with it).
- **US4 (T042–T047)** depends on Foundational and on US2's URL names (T028) for its "entry leads to
  that listing" assertions, but not on US3.
- **US5 (T048–T054)** depends on US2's URL renaming (T028) and benefits from US4 existing (shares
  the registry-iteration pattern) but does not require US3.
- **US6 (T055–T061)** should run last among the stories — it deletes code some earlier tasks might
  still be reading during development, and it is explicitly "the story to drop if the run runs
  short" (decisions.md D8).
- **Polish (T062–T066)** depends on all six stories.

## Parallel opportunities

- Within Foundational: T006, T007, T010, T012 (all test-writing, different files) can run in
  parallel once their corresponding production task is scoped.
- Within US2: T016–T023 (all test files, no shared state) in parallel; then T025–T029 mostly
  sequential (same file, `views.py`).
- Within US3: T031–T037 in parallel.
- Within US4/US5: all test tasks in parallel; T047 and T053/T054 touch different files and can
  proceed in parallel once US2's renaming (T028) lands.
- Within US6: T055–T058 in parallel (different files/deletions); T059–T060 sequential after.
