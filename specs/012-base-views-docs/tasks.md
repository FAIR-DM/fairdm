# Tasks: FairDM Base Views — Documentation & Testing

**Input**: Design documents from `specs/012-base-views-docs/`
**Prerequisites**: plan.md, spec.md, research.md

**Tests**: Included — integration tests are a primary deliverable of this feature (US3, P3)

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Verify environment and create the new test directory structure.

- [X] T001 Verify `poetry run python manage.py check` passes with zero errors
- [X] T002 Create `tests/test_views/__init__.py` (empty file to make the directory a Python package)

### System Validation

- [X] T003 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` — MUST pass before proceeding

---

## Phase 2: Foundational (No blockers for stories — all three stories are independent)

No foundational prerequisites. US1 (docstrings), US2 (docs page), and US3 (tests) can each be started independently after Phase 1.

---

## Phase 3: User Story 1 — Inline Docstrings (P1)

**Story goal**: Every FairDM view class in `fairdm/views/base.py` has a complete, accurate docstring in django-mvp style so a developer can understand the class in ≤30 seconds without leaving their editor.

**Independent test criteria**: Read `fairdm/views/base.py` — each class docstring has (a) a purpose sentence, (b) `Context:` section listing `meta` key, (c) `Example::` section, and (d) `Config:` section where the class adds attributes.

- [X] T004 [P] [US1] Write docstring for `FairDMTemplateView` in `fairdm/views/base.py` — purpose, `Context:` (`meta`), `Example::` (minimal subclass with `template_name`)
- [X] T005 [P] [US1] Write docstring for `FairDMListView` in `fairdm/views/base.py` — purpose, `Config:` (`paginate_by`, `grid`), `Context:` (`meta`, `grid_config`, `page`), `Example::` (subclass with `model` and `filterset_class`)
- [X] T006 [P] [US1] Write docstring for `FairDMDetailView` in `fairdm/views/base.py` — purpose, `Context:` (`meta`, `object`), `Example::` (subclass with `model`)
- [X] T007 [P] [US1] Write docstring for `FairDMCreateView` in `fairdm/views/base.py` — purpose (thin composition; no additional attributes), `Context:` (`meta`, `form`), `Example::` (subclass with `model` and `fields`)
- [X] T008 [P] [US1] Write docstring for `FairDMUpdateView` in `fairdm/views/base.py` — purpose (correct "updating" not "creating"), `Context:` (`meta`, `form`, `object`), `Example::` (subclass with `model` and `fields`)
- [X] T009 [P] [US1] Write docstring for `FairDMDeleteView` in `fairdm/views/base.py` — purpose, `Context:` (`meta`, `object`), `Example::` (subclass with `model` and `success_url`)
- [X] T010 [P] [US1] Write docstring for `FairDMTableView` in `fairdm/views/base.py` — purpose (table-style vs card-list), `Config:` (`table_class` required, template responsibility), `Context:` (`meta`, `table`, `filter`), `Example::` (subclass with `model`, `table_class`, `filterset_class`)

### System Validation

- [X] T011 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` — MUST pass before proceeding
- [X] T012 ⚠️ CRITICAL: Run existing tests to confirm no regressions: `poetry run pytest tests/ -v --ignore=tests/test_views/ -x` — ALL tests MUST pass

---

## Phase 4: User Story 2 — Contributing Documentation (P2)

**Story goal**: A new contributor can read `docs/contributing/base-views.md` and answer: why FairDM has its own view layer, what `MetadataMixin` adds, and which view to subclass for each CRUD operation.

**Independent test criteria**: Open `docs/contributing/base-views.md` — page contains: three-layer hierarchy explanation, quick-reference table mapping operations to view classes, per-class subsections with code examples, `MetadataMixin` explanation. `docs/contributing/index.md` links to it.

- [X] T013 [US2] Create `docs/contributing/base-views.md` with the following sections:
  - **Overview** — why FairDM has its own view layer (consistency, SEO metadata, framework API contract)
  - **The three-layer hierarchy** — table: Django generic view → django-mvp view → FairDM view, for each of the 7 classes
  - **SEO metadata with `MetadataMixin`** — what it injects (`meta` context key), which view-level attributes drive it (`title`, `description`, `image`, `keywords`), link to django-meta docs
  - **Quick reference** — table: CRUD operation → FairDM view class → when to use it
  - **View class reference** — one subsection per class: `FairDMTemplateView`, `FairDMListView`, `FairDMDetailView`, `FairDMCreateView`, `FairDMUpdateView`, `FairDMDeleteView`, `FairDMTableView` — each with a purpose paragraph, key attributes, and minimal code example
  - **`FairDMListView` vs `FairDMTableView`** — explicit comparison paragraph explaining when to choose each
- [X] T014 [US2] Add `base-views` entry to the `toctree` in `docs/contributing/index.md` — insert after `registry-system` entry

### System Validation

- [X] T015 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` — MUST pass before proceeding
- [X] T016 ⚠️ CRITICAL: Run existing tests: `poetry run pytest tests/ -v --ignore=tests/test_views/ -x` — ALL tests MUST pass

---

## Phase 5: User Story 3 — Integration Tests (P3)

**Story goal**: A green `pytest` suite for `tests/test_views/test_base.py` validates all 7 view classes across: HTTP 200 status, `meta` context key presence, key context keys per view type (e.g., `grid_config` for list view, `form` for create/update/delete, `object` for detail/update/delete).

**Independent test criteria**: `poetry run pytest tests/test_views/test_base.py -v` produces a fully green suite with ≥1 test per view class. Coverage report shows 100% line coverage of `fairdm/views/base.py`.

- [X] T017 [US3] Create `tests/test_views/test_base.py` with module docstring, imports (`pytest`, `django.test.RequestFactory`/`rf`, `django.urls.reverse`, `override_settings`, factories), and a shared `urlconf` fixture or `pytest.mark.urls` setup using `fairdm_demo` URL patterns for model-based views
- [X] T018 [P] [US3] Write `TestFairDMTemplateView` class in `tests/test_views/test_base.py` — tests: `test_get_returns_200`, `test_meta_context_key_present`; use a minimal in-test concrete subclass with `template_name`
- [X] T019 [P] [US3] Write `TestFairDMListView` class in `tests/test_views/test_base.py` — tests: `test_get_returns_200`, `test_meta_context_key_present`, `test_grid_config_context_key_present`; use `ProjectListView` or a minimal test subclass with `Project` model
- [X] T020 [P] [US3] Write `TestFairDMDetailView` class in `tests/test_views/test_base.py` — tests: `test_get_returns_200`, `test_meta_context_key_present`, `test_object_in_context`; use `Project` model + `ProjectFactory`
- [X] T021 [P] [US3] Write `TestFairDMCreateView` class in `tests/test_views/test_base.py` — tests: `test_get_returns_200`, `test_meta_context_key_present`, `test_form_in_context`, `test_post_creates_object_and_redirects`; use `Project` model + authenticated client
- [X] T022 [P] [US3] Write `TestFairDMUpdateView` class in `tests/test_views/test_base.py` — tests: `test_get_returns_200`, `test_meta_context_key_present`, `test_form_in_context`, `test_object_in_context`; use `Project` model + `ProjectFactory`
- [X] T023 [P] [US3] Write `TestFairDMDeleteView` class in `tests/test_views/test_base.py` — tests: `test_get_returns_200`, `test_meta_context_key_present`, `test_object_in_context`; use `Project` model + `ProjectFactory`
- [X] T024 [P] [US3] Write `TestFairDMTableView` class in `tests/test_views/test_base.py` — tests: `test_get_returns_200`, `test_meta_context_key_present`; use a minimal in-test concrete subclass with `Project` model and a simple `django_tables2.Table` subclass

### System Validation

- [X] T025 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` — MUST pass before proceeding
- [X] T026 ⚠️ CRITICAL: Run new test suite: `poetry run pytest tests/test_views/test_base.py -v` — ALL tests MUST pass
- [X] T027 ⚠️ CRITICAL: Run full test suite + coverage: `poetry run pytest tests/ -v --cov=fairdm/views/base --cov-report=term-missing` — ALL tests MUST pass and `fairdm/views/base.py` MUST show 100% line coverage

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final review pass to confirm spec outcomes are met across all three user stories.

- [X] T028 Review all 7 docstrings in `fairdm/views/base.py` for consistency — ensure `Context:` section mentions `meta` key in all classes, `Config:` sections use consistent type annotation style, `Example::` code blocks are syntactically valid Python
- [X] T029 Review `docs/contributing/base-views.md` — confirm every code example matches the current docstrings, quick-reference table covers all 7 classes, hierarchy table is accurate
- [X] T030 Verify `docs/contributing/index.md` toctree renders correctly (no duplicate entries, correct indentation)

### Final System Validation

- [X] T031 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` — MUST pass
- [X] T032 ⚠️ CRITICAL: Run complete feature test suite: `poetry run pytest tests/test_views/test_base.py tests/ -v --cov=fairdm/views/base --cov-report=term-missing` — ALL tests MUST pass, 100% coverage on `fairdm/views/base.py`

---

## Dependencies

```
Phase 1 (Setup)
  └── Phase 3 (US1 — Docstrings)   — independent, starts after Phase 1
  └── Phase 4 (US2 — Docs page)    — independent, can start after Phase 1
                                     (but benefits from Phase 3 being done first,
                                      since docs derive from docstrings)
  └── Phase 5 (US3 — Tests)        — independent, starts after Phase 1
                                     (tests validate docstring contracts, so
                                      Phase 3 should be done first in practice)
Phase 3 + Phase 4 + Phase 5
  └── Phase 6 (Polish)
```

## Parallel Execution

Within each phase, all `[P]`-marked tasks operate on different files and can run concurrently:

- **Phase 3**: T004–T010 — 7 independent docstring edits within the same file (one author; but each is a self-contained hunk)
- **Phase 5**: T018–T024 — 7 independent test classes; all can be written in parallel if pair-programming

## Implementation Strategy

**MVP scope (US1 alone, Phase 3 only)**: Writing all 7 docstrings delivers immediate, tangible value. A developer reading the file gets complete self-service documentation. Estimated effort: small.

**Full delivery order** (recommended):

1. Phase 1 → Phase 3 (docstrings) → Phase 5 (tests, validating docstring contracts) → Phase 4 (docs page, referencing both) → Phase 6 (polish)

**Rationale**: Tests written after docstrings serve as executable proof that the documented contracts hold. The docs page written last can confidently copy from both docstrings and verified test behaviour.
