# Tasks: One consistent overview page for projects, datasets, samples and measurements

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md)

**Design source**: the approved branches. Port content, wording and markup from them with
`git show origin/wip/<page>-overview:<path>`, and change only what a requirement or plan decision
changes.

**Test-first**: in every story, the test tasks come first and must fail before the implementation
tasks start. Tests request real pages through the Django test client and assert on the rendered
HTML, as a visitor and as a member of the team. There are no query-count assertions.

**Format**: `[ID] [P?] [Story] Description`. `[P]` means it can run in parallel with its
neighbours (different files, no shared state).

## Phase 1: US-1, the shared anatomy and the project page (P1) 🎯

**Goal**: the skeleton, the cards, the shared helpers, the charts and the one seed command, with
the project page as their first user.

**Independent test**: load development data, then open each seeded project as a visitor and as
`staff.user`. The page matches the approved branch and the acceptance scenarios for US-1.

### Groundwork

- [ ] T001 [US1] Raise `django-mvp` to `>=0.24,<0.25`, add `django-mvp-charts >=0.2,<0.3` and
  `pyecharts` to `pyproject.toml`, add `pyecharts`/`mvp_charts` to `package_module_name_map`,
  re-lock (`uv lock`), add `mvp_charts` after `mvp` in `fairdm/conf/settings/apps.py` and the
  `cite` icon in `fairdm/conf/settings/addons.py`. `deptry` and the existing suite stay green.
- [ ] T002 [P] [US1] Bring over `fairdm/templates/cotton/{stats,list,tabs}/` and
  `fairdm/templates/cotton/progress.html` from `wip/project-overview`, byte for byte, plus
  `fairdm/static/js/chart-theme.js`.

### Tests (write first, must fail)

- [ ] T003 [P] [US1] Tests for the shared pieces:
  - `tests/test_core/test_overview.py`: `format_authors` for zero, one, two and several
    contributors, persons and organisations; `json_ld` escapes `<`, `>` and `&`.
  - `tests/test_core/test_plugins.py`: `RecordOverviewPlugin.get_citation()` omits empty parts;
    `get_identifiers()` links DOIs and IGSNs through doi.org and leaves other types unlinked;
    `get_timeline()` orders dated steps, puts undated steps last and keeps year-only and
    month-only dates as recorded; `get_credits()` returns persons and organisations as their own
    types.
- [ ] T004 [P] [US1] `tests/test_core/test_project/test_overview.py`: US-1 scenarios 1–8 against
  the rendered page, including:
  - a visitor's figures, charts and licence summary exclude private datasets
  - the readiness checklist is absent for visitors and present for the team, and each of its ten
    items turns on and off
  - the private and "Searching for collaborators" notices
  - the timeline wording before, during and after the project
  - the schema.org JSON-LD in `<head>`
  - the empty-project state with an Add dataset action and no chart
- [ ] T005 [P] [US1] `tests/test_templates/test_overview_page.py` (new directory, mirroring
  `fairdm/templates/`): the skeleton renders every facts-column block in FR-003's order;
  a child template can extend `overview.main` with `{{ block.super }}` and keep its content
  (FR-007); each `c-card.*` component renders its documented inputs and renders nothing, or its
  empty message, when given nothing (spec edge case); a pending action renders `disabled` with its
  explanation (FR-011).

### Implementation

- [ ] T006 [US1] Plan D3: `RecordOverviewPlugin` in `fairdm/core/plugins.py` with
  `get_credits`, `get_identifiers`, `get_citation`, `get_timeline` and
  `get_records_by_type_chart`, and `fairdm/core/overview.py` holding only the pure formatting
  functions (`format_authors`, `author_name`, `json_ld`, `as_date`, `sentence_case`,
  `safe_reverse`). Python strings through `gettext`/`gettext_lazy`.
- [ ] T007 [US1] `fairdm/templates/overview/page.html`: the skeleton with every block from plan
  D1 in page order, the block list in its header comment, the `lg` stacking grid, and the
  conditional ECharts/chart-theme/mvp-charts scripts in `extra_js` (plan D7). Use
  `{% comment %}`, never a multi-line `{# #}`.
- [ ] T008 [US1] `fairdm/templates/cotton/card/`: `citation`, `identifiers`, `people`, `parent`,
  `dates`, `readiness`, `timeline`, `placeholder`, plus
  `fairdm/templates/overview/includes/pending_action.html` (plan D2). Markup taken from the
  branch cards they replace. Copy buttons, tabs and disclosures are keyboard reachable and
  labelled.
- [ ] T009 [US1] `fairdm/core/project/plugins.py`: the project `Overview` subclasses
  `RecordOverviewPlugin`, and the branch's `project/overview.py` logic (counts, dataset preview,
  team, timeline, readiness, growth chart, licences) becomes methods on it, assembled in
  `get_context_data()`. No `project/overview.py` module. `project/project_detail.html` extends `overview/page.html` and fills only
  blocks. The branch's placeholders (map, activity, citation formats, metadata downloads) use
  `c-card.placeholder` or the pending action.
- [ ] T010 [US1] Charts on the project page: each chart shows its text alternative to assistive
  technology and when the script fails (SC-006).
- [ ] T011 [US1] `demo/management/commands/seed_overviews.py`: the development guard (the
  `NON_PRODUCTION_ENVIRONMENTS` check `create_dev_accounts` uses), the three
  `example.com` accounts, and the three seeded projects with their datasets as on
  `wip/project-overview`. Safe to run twice (FR-045–FR-047). Define `EXAMPLE_ACCOUNT_EMAILS`
  beside `DEV_ACCOUNT_EMAILS` in `fairdm/management/commands/create_dev_accounts.py`, import it
  in the seed, and make check `fairdm.E501` in `fairdm/conf/checks.py` report the union (plan D6).
  Tests:
  - `tests/test_demo/test_management/test_commands/test_seed_overviews.py` (new directory,
    mirroring `demo/`): it refuses outside development, creates the accounts once, and a second
    run leaves the same record count.
  - An E501 test in the existing checks tests: `super.user@example.com` outside development is
    reported.
- [ ] T012 [US1] Docs:
  - `docs/portal-development/overview-pages.md` with the anatomy, the full block list, and a
    worked example that overrides `project/project_detail.html` and fills one block
  - `docs/portal-development/component_library/cards.md` with a usage example for every
    `c-card.*` and for `stats`, `list`, `tabs` and `progress`
  - both pages linked from their table of contents
  - a changelog entry under Unreleased (FR-048, FR-049, Article XVII)
  - `docs/portal-development/development_accounts.md`: which accounts `create_dev_accounts`
    creates, which `seed_overviews` creates, and that E501 covers both

**Checkpoint**: the project page is complete, and every later story reuses what this phase
built without redefining it.

## Phase 2: US-2, the dataset page (P1)

**Goal**: the dataset page on the shared anatomy, with its data section.

**Independent test**: open the published, public-unpublished, private and empty seeded datasets
as a visitor and as `staff.user`.

### Tests (write first, must fail)

- [ ] T013 [P] [US2] `tests/test_core/test_dataset/test_overview.py`: US-2 scenarios 1–9,
  including:
  - a visitor on an unpublished dataset gets counts and field meanings but no preview table and
    no value ranges, and the JSON-LD carries no ranges either (FR-050)
  - a visitor on a published dataset gets both
  - the checklist is absent for visitors and once the dataset is published
  - the citation prefers `reference`, and the year falls back through Published, Available and
    Added
  - relation wording and ordering
  - the field summary skips bookkeeping fields and non-model columns
  - an unregistered record type is skipped
  - the chart appears only with more than one type
  - the withdrawal notice
  - the registry's schema maintainer credited with a way to cite it (FR-028)
  - a public dataset in a private project, visited anonymously: the project is not named,
    linked or put in the JSON-LD (plan D3)

### Implementation

- [ ] T014 [US2] `fairdm/core/dataset/plugins.py`: the dataset `Overview` subclasses
  `RecordOverviewPlugin`, and the branch's `dataset/overview.py` logic becomes methods on it.
  The parent project is shown only when `project_is_visible` passes (plan D3).
  `dataset/dataset_detail.html` extends `overview/page.html` and fills only blocks, with the
  record facts `publications` and `versions` (a placeholder card). Publish, Import data, CSV
  download and All rows use the pending action.
- [ ] T015 [US2] Preview tables render through the registry's table class without a request and
  without ordering. A table class that needs the request must not raise (spec edge case). Add
  one test with such a table class.
- [ ] T016 [US2] Extend `seed_overviews` with the five dataset states from #369.
- [ ] T017 [US2] Docs: the dataset page's blocks in `overview-pages.md`, and a changelog line.
- [ ] T018 [US2] Delete `fairdm/templates/cotton/cards/statistic.html` once `grep` shows no
  template references it.

## Phase 3: US-3, the sample page and choosing a template by type (P2)

**Goal**: the generic sample page, `TypedOverviewPlugin`, and the demo rock sample's extension.

**Independent test**: open each seeded sample as a visitor and as `staff.user`, and open a rock
sample next to a water sample.

### Tests (write first, must fail)

- [ ] T019 [P] [US3] `tests/test_core/test_plugins.py`: `TypedOverviewPlugin` resolves a type's
  own template, a subtype's parent template and the generic fallback, using test-local templates.
  A type template that fills one block leaves every other block showing the shared content
  (US-3 scenario 1). The sample overview's address is unchanged (`/samples/<uuid>/overview/`).
- [ ] T019a [P] [US3] `tests/test_core/test_sample/test_managers.py` and
  `tests/test_core/test_measurement/test_managers.py` (or their existing QuerySet test modules):
  `visible_to(user)` for an anonymous visitor, a holder of `dataset.view_dataset` on one dataset
  only, and a model-level permission holder, across public-published, public-unpublished and
  private datasets. `tests/test_core/test_dataset/test_models.py`: `Dataset.data_is_public`.
- [ ] T020 [P] [US3] `tests/test_core/test_sample/test_overview.py`: US-3 scenarios 4–8, covering:
  - visibility in each dataset state, for a visitor and a team member, with a 404 that matches a
    missing record
  - measurements from unpublished datasets hidden from visitors
  - a member of the sample's own dataset team is not shown a measurement from a third dataset
    they hold no rights on (the rule is per row, plan D3)
  - a published sample whose parent and subsample sit in an unpublished dataset: a visitor sees
    neither named nor linked, and the related-samples figure doesn't count them
  - a sample in a private project: the project is not named or linked
  - history merging and ordering with partial dates
  - the label and meaning of every custody status, including a status stored as a vocabulary
    concept
  - the destroyed notice

### Implementation

- [ ] T021 [US3] `Dataset.data_is_public`, `SampleQuerySet.visible_to(user)` and
  `MeasurementQuerySet.visible_to(user)` (plan D3), then `TypedOverviewPlugin` in
  `fairdm/core/plugins.py` (plan D4), with its `check` built on `visible_to` and the comment on
  why `PrivateRecordNotFoundMixin` isn't reused. Neither plugin class sets `url_path`.
- [ ] T022 [US3] `fairdm/core/sample/plugins.py`: the sample `Overview` subclasses
  `TypedOverviewPlugin`, and the branch's `sample/overview.py` logic becomes methods on it, with
  `LIFECYCLE` as a class attribute. Measurements made on it and related samples are filtered per
  row with `visible_to` (plan D3). `sample/sample_overview.html` extends `overview/page.html` and uses
  `overview.*` block names. `c-card.timeline` draws the history.
- [ ] T023 [US3] `demo/templates/demo/rocksample_overview.html` rewritten to the `overview.*`
  blocks, with a docstring-style comment linking the docs page (Article XVIII).
- [ ] T024 [US3] Extend `seed_overviews` with the four sample states from #370.
- [ ] T025 [US3] Docs: the sample blocks and "Giving a sample type its own page" in
  `overview-pages.md`, with the rock sample as the worked example. Add a changelog line.

## Phase 4: US-4, the measurement page (P2)

**Goal**: measurements in the plugin system at `/measurement/<uuid>/`, on the shared anatomy, with
the XRF extension.

**Independent test**: open each seeded measurement as a visitor and as `staff.user`, including
the one in a different dataset from its sample.

### Tests (write first, must fail)

- [ ] T026 [P] [US4] `tests/test_core/test_measurement/test_overview.py`: US-4 scenarios 1–8,
  covering:
  - the tab strip, with the overview first
  - the address unchanged: the response's request path and `get_absolute_url()` both equal the
    literal `f"/measurement/{uuid}/"` (plan D5)
  - template resolution through `TypedOverviewPlugin`
  - visibility against the measurement's own dataset, including a sample and a measurement in
    different datasets
  - the unpublished-sample wording with no link, in the page, the breadcrumbs and the citation
  - the result only for a non-empty `value`
  - procedure merging
  - siblings filtered for visitors, and per row: a member of the measurement's dataset team is
    not shown a sibling in a third dataset they hold no rights on
  - breadcrumbs with and without a project, and with a private project left out
- [ ] T027 [US4] Update `test_detail_page_renders` in
  `tests/test_core/test_measurement/test_models.py` to use a public, published dataset, and add
  the 404 case beside it. This is a pre-existing test whose premise the feature changes, so it
  needs a tamper-check waiver line in `decisions.md` (D-series entry).

### Implementation

- [ ] T028 [US4] Register the measurement `Overview` plugin (a `TypedOverviewPlugin`) in
  `fairdm/core/measurement/plugins.py`, mount the registry URLs in
  `fairdm/core/measurement/urls.py` with `url_path = None` on the plugin, override
  `get_breadcrumbs()`, and delete
  `MeasurementDetailView` and `measurement/detail.html` (plan D5).
- [ ] T029 [US4] The branch's `measurement/overview.py` logic becomes methods on the measurement
  `Overview`, with `PROCEDURE` as a class attribute. Siblings and the measured sample are filtered
  per row with `visible_to`. The citation says "an unpublished sample" when the sample can't be
  shown.
  `measurement/measurement_overview.html` extends `overview/page.html`, with `overview.result` in
  the figures position.
- [ ] T030 [US4] `demo/templates/demo/xrfmeasurement_overview.html` rewritten to the `overview.*`
  blocks.
- [ ] T031 [US4] Extend `seed_overviews` with the four measurement states from #371.
- [ ] T032 [US4] Docs: the measurement blocks, the note in `docs/portal-development/measurements.md`
  that measurements now have plugin pages, and a changelog line (measurement pages moved into
  the plugin system).

## Dependencies

- Phase 1 blocks everything. US-2, US-3 and US-4 each depend only on Phase 1, not on each other,
  except that US-4 uses `TypedOverviewPlugin` from US-3 (T021). Phases run in order, one
  implementer at a time.
- Within a story: the tests, then the shared or plugin code, then the templates, then the seed,
  then the docs.

## Requirement coverage

| Requirement | Tasks |
|---|---|
| FR-001, FR-005 | T007 |
| FR-002 | T007, T009 |
| FR-003, FR-007 | T005, T007 |
| FR-004, FR-011 | T005, T008 |
| FR-006 | T007, T022, T029 |
| FR-008 | T012, T017, T025, T032 |
| FR-009 | T026, T028 (projects, datasets and samples already open on their overview tab) |
| FR-010 | T009, T014, T022, T029 |
| FR-012 | T004, T013 |
| FR-013 | T019a, T020, T021, T022 |
| FR-014 | T026, T028 |
| FR-015, FR-019–FR-023 | T004, T009, T010 |
| FR-016, FR-024–FR-030 | T013, T014, T015 |
| FR-017 | T019a, T020, T022, T026, T029 |
| FR-018 | T004, T013 |
| FR-031–FR-035 | T020, T022 |
| FR-036–FR-041 | T026, T029 |
| FR-042, FR-043 | T019, T021 (T019 also asserts US-3 scenario 1) |
| FR-044 | T023, T030 |
| FR-045–FR-047 | T011, T016, T024, T031 |
| FR-048, FR-049 | T012, T017, T025, T032 |
| FR-050 | T004, T013 |
| FR-051 | T006, T008, and every template task: strings through `{% translate %}`, dates through Django's locale-aware filters |
| SC-001 | T005, T007, T008 |
| SC-002 | T023, T025 |
| SC-003 | T004, T013, T020, T026 |
| SC-004 | T020, T026 |
| SC-005 | T005, T008 |
| SC-006 | T008, T010 |
| SC-007 | T011, T016, T024, T031 |
