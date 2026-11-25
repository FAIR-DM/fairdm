# Tasks: Find a record from anywhere in the portal

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md),
[decisions.md](decisions.md)

**Tests first**: test tasks come first and each is seen to fail for the right reason before the
code that makes it pass is written. Wording and appearance get no tests.

**How tests run**: from the worktree's own virtual environment against the shared test PostGIS
(`. ../fairdm-042-env.sh; .venv/bin/python -m pytest tests/test_search.py -n0`).

**Standards in every task**: no leading-underscore names, line length 88, no compatibility
aliases, Cotton components and never `{% include %}`, a Google-style docstring on every new
public name.

**Format**: `[ID] [Story] Description`.

## Phase 1: User Story 1 — A person finds a record from any page (P1)

### Group 1

- [x] T001 [US1] Tests: `tests/test_search.py` as plan.md "Tests" lists them (all eight
  classes). They fail because nothing is registered or mounted.
- [x] T002 [US1] `fairdm/search.py`: `RecordKind` and the seven kinds as plan.md "Modules"
  describes, and `register_kinds()`. Call it from `FairDMConfig.ready()` in `fairdm/apps.py`. The
  kind tests that do not need the address go green.
- [x] T003 [US1] Mount `path("search/", include("mvp.search.urls"))` in `fairdm/conf/urls.py` and
  add the three search components to the `app.navbar.end` block of `fairdm/templates/base.html`
  beside "Create new". `tests/test_search.py` is green and the portal's system checks pass.
- [x] T004 [US1] Documentation: `docs/developers/reference/site-search.md` as plan.md
  "Documentation" describes (a reference page, no steps), its entry in the reference index, and
  the `CHANGELOG.md` entry under `Added`.
- [x] T005 [US1] Narrow two tests the header's search overtook, as D17 describes:
  `tests/test_core/test_dataset/test_views.py::TestDatasetListingSearch::test_the_listing_offers_no_second_search_control`
  and `tests/test_templates/test_overview_page.py::TestHeaderImage::test_a_record_without_an_image_has_nothing_to_open`.
- [x] T006 [US1] Tests for the header's field and button hooks, and for the order every kind returns
  (ends with the record id). Found by mutating the build and watching which tests stayed green.
- [x] T007 [US1] Review fix: a measurement names its sample only when the person may open it.
- [x] T008 [US1] Review fix: a dataset names its project only when the person may open it.
- [x] T009 [US1] Review fix: a test for the portal-wide right on private projects.
