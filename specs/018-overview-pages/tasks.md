# Tasks: One consistent overview page for projects, datasets, samples and measurements

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md)

**Design source**: the prototype already on this branch. Its markup, copy and layout are settled.
Change them only where a requirement, a plan decision or a failing acceptance test says so.

**Tests first**: in every story, the test tasks come first. Tests request real pages through the
Django test client and assert on what the page delivers, as a visitor and as the team. A test that
passes at once against the prototype is fine: it pins a scenario the prototype already meets. A
test that fails drives a fix in the story's implementation task. Layout, width, stacking and copy
get no tests. No query-count assertions.

**Existing tests**: a pre-existing test that fails because the specification changed the
behaviour it describes (a sample in an unpublished dataset now answers "not found") is updated to
the new rule, and the change is recorded in `decisions.md`. A pre-existing test that fails because
the prototype dropped something the spec still requires (the Delete link) is kept as it is, and
the code is fixed.

**Format**: `[ID] [P?] [Story] Description`. `[P]` can run beside its neighbours.

## Phase 1: US-1, the shared anatomy and the project page (P1)

**Goal**: the skeleton, the cards, `RecordOverviewPlugin`, the seed command and the project page,
tested and documented.

**Independent test**: load development data, open each seeded project as a visitor and as
`staff.user`, and compare against US-1's acceptance scenarios.

- [ ] T001 [US1] Dependencies: declare `pyecharts` as a direct dependency, map `django-mvp-charts`
  to `mvp_charts` for `deptry` (it is used through `INSTALLED_APPS` and templates, so declare it as
  used rather than ignoring the rule), re-lock with `uv lock`. `deptry` passes.
- [ ] T002 [P] [US1] Tests for the shared pieces, written against the plan's D3 API so they fail
  first:
  - `tests/test_core/test_overview.py`: `format_authors` for zero, one, two and several creators,
    persons and organisations. `json_ld` escapes `<`, `>` and `&`. `as_date` keeps year-only and
    month-only dates as recorded.
  - `tests/test_core/test_plugins.py`: on `RecordOverviewPlugin`, `get_citation()` leaves out
    empty parts; `get_identifiers()` links DOIs and IGSNs to doi.org and leaves other types
    unlinked; `get_timeline()` puts dated steps in date order and undated ones last;
    `get_people()` leaves out anyone named in the header and caps at eighteen, counting the rest.
- [ ] T003 [P] [US1] Tests for the skeleton and the cards, under `tests/test_templates/`
  mirroring `fairdm/templates/`:
  - the side column renders its cards in FR-003's order
  - a child template can add to `overview.main` with `{{ block.super }}` and keep its content
    (FR-007)
  - each `c-card.*` component renders its documented inputs, and is left out or says what is
    missing when given nothing
  - `pending_action.html` renders a disabled button that says why (FR-017)
- [ ] T004 [P] [US1] `tests/test_core/test_project/test_overview.py`: US-1 scenarios 1 to 11
  against the rendered page, plus:
  - the Manage menu offers Delete to a user who may delete the project (the existing
    `test_a_user_who_may_delete_the_project_is_offered_the_link` stays as it is)
  - a private project's datasets never reach a visitor's figures, charts, licence summary or
    JSON-LD
- [ ] T005 [P] [US1] Tests for development data, under `tests/test_demo/`: `seed_overviews`
  refuses outside development, creates the three `example.com` accounts when missing and leaves
  existing ones alone, gives `staff.user` the team's rights and `regular.user` none, and running
  it twice leaves the same records. In `tests/test_conf/`: `fairdm.E501` reports an
  `example.com` account outside development.
- [ ] T006 [US1] Bring the pre-existing tests in `tests/test_contrib/test_plugins/`
  (`test_base.py`, `test_registration.py`, `test_menus.py`) up to date: give the sample and
  measurement fixtures a published, public dataset where the test is about something other than
  visibility, and record each change in `decisions.md`.
- [ ] T007 [US1] Implement D3 for the shared pieces and the project: add `RecordOverviewPlugin`
  with the shared methods, make all four `Overview` plugins subclass it, move the project's logic
  from `fairdm/core/project/overview.py` onto the project `Overview` plugin, and delete that
  module. The other pages keep calling their own modules until their stories. Output unchanged:
  T004 green.
- [ ] T008 [US1] Fix what T002 to T006 found against the prototype, including:
  - the header people block renamed `overview.byline` in the skeleton and every template
  - the Delete link restored in the project and dataset Manage menus
  - the unused `cotton/cards/statistic.html` deleted
  - the prototype's change-history code comments rewritten to say what the code does now
- [ ] T009 [US1] Documentation: `docs/portal-development/overview-pages.md` (the anatomy, the
  block list in page order, the project page, and extending a project page by overriding its
  template), `docs/portal-development/component_library/cards.md` (every `c-card.*` component and
  `stats`, `list`, `tabs`, `progress`, each with a working example),
  `docs/portal-development/development_accounts.md` (which command creates which accounts), and
  the stale `context_object_name` passage in
  `docs/portal-development/forms-and-filters/sample-mixins.md`. Changelog entry started. Docs
  check green for every name this story introduces.

## Phase 2: US-2, the dataset page (P1)

**Independent test**: open the published, public-but-unpublished, private and empty seeded
datasets as a visitor and as `staff.user`, and compare against FR-022 and FR-024.

- [ ] T010 [US2] `tests/test_core/test_dataset/test_overview.py`: US-2 scenarios 1 to 11, plus:
  the JSON-LD on a public, unpublished dataset names the variables measured and carries no values
  (FR-034, FR-056); Delete offered to a user who may delete the dataset. Update the pre-existing
  `TestNonCollectionPagesIgnorePublished` test in `tests/test_core/test_dataset/test_views.py` to
  the new rule that a visitor sees counts but no records, and record why in `decisions.md`.
- [ ] T011 [US2] Move the dataset's logic from `fairdm/core/dataset/overview.py` onto the dataset
  `Overview` plugin and delete the module. Delete what belonged to the removed data tabs:
  `field_summary`, `preview_table`, `field_kind`, `record_types` and the `overview.data` block.
  Fix what T010 found.
- [ ] T012 [US2] Documentation: the dataset page section in `overview-pages.md`, including the
  timeline card and the readiness checklist. Changelog entry extended.

## Phase 3: US-3, the sample page and extending by type (P2)

**Independent test**: open each seeded sample as a visitor and as `staff.user`, then a rock
sample and a sample type with no template of its own.

- [ ] T013 [US3] `tests/test_core/test_sample/test_overview.py`: US-3 scenarios 1 to 12. Template
  choice by own type, nearest ancestor and fallback (FR-048, FR-049). `visible_to` on
  `SampleQuerySet` and `Dataset.data_is_public` in `tests/test_core/test_sample/test_managers.py`
  and `tests/test_core/test_dataset/test_models.py`. Bring the pre-existing
  `tests/test_core/test_sample/test_plugins.py` gate tests up to date with a published dataset and
  record why.
- [ ] T014 [US3] Move the sample's logic from `fairdm/core/sample/overview.py` onto the sample
  `Overview` plugin and delete the module. Fix what T013 found.
- [ ] T015 [US3] Documentation: the sample page section and "Giving a sample or measurement type
  its own page" in `overview-pages.md`, with the demo's rock sample as the worked example (FR-008,
  FR-050). Changelog entry extended.

## Phase 4: US-4, the measurement page (P2)

**Independent test**: open each seeded measurement as a visitor and as `staff.user`, including the
one recorded in a different dataset from its sample.

- [ ] T016 [US4] `tests/test_core/test_measurement/test_overview.py`: US-4 scenarios 1 to 10,
  asserting the literal `/measurement/<uuid>/` path. `visible_to` on `MeasurementQuerySet` in
  `tests/test_core/test_measurement/test_managers.py`. Bring the pre-existing
  `TestMeasurementViews.test_detail_page_renders` up to date with a published dataset, add the
  "not found" case beside it, and record why.
- [ ] T017 [US4] Move the measurement's logic from `fairdm/core/measurement/overview.py` onto the
  measurement `Overview` plugin and delete the module. Remove from `fairdm/core/overview.py`
  everything that is not a pure function (D3). Fix what T016 found.
- [ ] T018 [US4] Documentation: the measurement page section in `overview-pages.md` with the demo's
  XRF measurement as the example, and the changelog entry completed (FR-055). Full docs check
  green.
