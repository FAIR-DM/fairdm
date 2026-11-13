# Tasks: download a record's citation as BibTeX or RIS

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md),
[decisions.md](decisions.md)

**Tests first**: in every group the test tasks come first, and each is seen to fail before the code
that makes it pass is written. Wording and appearance get no tests.

**How tests run**: from the worktree's own virtual environment against the shared test PostGIS,
with the environment in `/home/sam/projects/worktrees/fairdm-036-env.sh` sourced first.

**Format**: `[ID] [Story] Description`.

**Order**: US2, then US1 from US2's verified commit. The panel's Download is a link to the format's
address and its formats come from the plugins, so the story that builds the formats and their
addresses goes first.

## Phase 1: User Story 2, a reference manager or a script fetches a record's citation (P2)

### Group 1

- [ ] T001 [US2] Add `pybtex>=0.26,<0.27` and `rispy>=0.10,<0.11` to `[project].dependencies` and
  `pylatexenc>=2.10,<3` to the `dev` dependency group in `pyproject.toml`, and update `uv.lock`
  with `uv lock`. No test: deptry and the suite cover it.
- [ ] T002 [US2] `tests/test_core/test_citation.py`: `TestToBibtex`, `TestToRis`,
  `TestPublicationTypes` and `TestCitationFilename` as plan.md "Tests, US2" describes, built on
  `Citation` and `CitedName` values directly, with no database.
- [ ] T003 [US2] `fairdm/core/citation.py`: `CitedName`, `Citation`, `cited_name`,
  `cited_name_from_item_name`, `escape_tex`, `to_bibtex`, `to_ris`, `citation_filename`,
  `publication_types` and `FORMATS`, as plan.md "The citation" describes. T002 goes green.

### Group 2

- [ ] T004 [US2] `TestOverviewCitationFormats` in each of
  `tests/test_core/test_project/test_plugins.py`, `tests/test_core/test_dataset/test_plugins.py`,
  `tests/test_core/test_sample/test_plugins.py` and
  `tests/test_core/test_measurement/test_plugins.py`, as plan.md "Tests, US2" describes.
- [ ] T005 [US2] `fairdm/core/plugins.py`: `get_publisher` and `get_citation_formats` on
  `RecordOverviewPlugin`, `get_citation` reading the publisher from `get_publisher`. Each record's
  `get_citation_details` builds its `Citation` and returns `work` and `formats` beside what it
  returns today, as plan.md "The plugins" describes. T004 goes green. Every existing citation test
  stays as it is.
- [ ] T006 [US2] `TestCitationFile` in `tests/test_core/test_plugins.py`, as plan.md "Tests, US2"
  describes.
- [ ] T007 [US2] `CitationFile` in `fairdm/core/plugins.py`, `RecordOverviewPlugin.extra_views`,
  and `CitationFile` added to the sample overview's `extra_views`, as plan.md "The address"
  describes. T006 goes green.
- [ ] T008 [US2] Documentation: a section on citations in
  `docs/developers/reference/overview-plugins.md`, as plan.md "Documentation" describes, and a
  `CHANGELOG.md` entry under `[Unreleased]`. Run every example in it against the branch.

## Phase 2: User Story 1, a reader takes a record's citation in their format (P1)

### Group 3

- [ ] T009 [US1] Tests in `tests/test_templates/test_overview_components.py` and
  `tests/test_templates/test_overview_page.py`, as plan.md "Tests, US1" describes. Change the
  existing cite-component and page tests that pass `text` only where they must now pass
  `formats`, and say which in the report.
- [ ] T010 [US1] `fairdm/templates/cotton/overview/cite.html` and the `overview.cite` block of
  `fairdm/templates/overview/page.html`, ported from the prototype as plan.md "The panel"
  describes. Read the prototype with
  `git show origin/prototype-overview-pages:fairdm/templates/cotton/ov/cite.html`. T009 goes green.
- [ ] T011 [US1] `fairdm/static/js/overview.js`: `initCite` ported from the prototype's
  `overview.js` (`git show origin/prototype-overview-pages:fairdm/static/js/overview.js`, lines
  110 to 157), and `initTabs` skipping the switch, as plan.md "The script" describes. No test
  (plan.md "What is not built").
- [ ] T012 [US1] `fairdm/static/css/fairdm.css`: the `.ov-seg` rules and the BibTeX and RIS rule
  ported from the prototype's `fairdm/static/css/overview.css` (lines 435 to 443 and 458), beside
  `.ov-cite__text`. No test.
- [ ] T013 [US1] `specs/018-overview-pages/spec.md`: FR-014 and FR-016, and any scenario that names
  the citation as text only, rewritten as plan.md "Specification 018" describes (FR-012).
- [ ] T014 [US1] Documentation: the Cite panel in `docs/users/projects/project.md`,
  `docs/users/datasets/dataset.md`, `docs/users/samples/sample.md` and
  `docs/users/measurements/measurement.md`, and a `CHANGELOG.md` entry under `[Unreleased]`.

## Coverage

| Requirement | Tasks |
|---|---|
| FR-001 | T009, T010 |
| FR-002 | T009, T010, T011 |
| FR-003 | T011 |
| FR-004 | T004, T005 |
| FR-005 | T004, T005 |
| FR-006 | T002, T003 |
| FR-007 | T002, T003, T004, T005 |
| FR-008 | T004, T005, T007 |
| FR-009 | T006, T007 |
| FR-010 | T006, T007 |
| FR-011 | T006, T007, T009, T010, T011 |
| FR-012 | T013 |
| SC-001 | T004, T009 |
| SC-002 | T002, T004 |
| SC-003 | T006, T011 |
| SC-004 | T006 |
