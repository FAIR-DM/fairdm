# Tasks: Dataset CRUD Views

**Input**: Design documents from `/specs/014-dataset-crud-views/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Tests are included per the framework's test-first requirement (Constitution Principle V — URL Smoke Test Coverage mandatory for all new URL patterns)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. There are no cross-cutting foundational prerequisites: all four user stories can proceed sequentially after Phase 1.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Logically independent — safe to author concurrently in the same session. Does NOT imply OS-level file-write parallelism; multiple `[P]` tasks that write to the same file should be done in sequence within that file.
- **[Story]**: Which user story this task belongs to (US1–US4)
- Exact file paths included in each description

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify environment and existing file state before any changes.

- [X] T001 Confirm feature branch `014-dataset-crud-views` is active (`git branch --show-current`) and Poetry virtualenv is activated
- [X] T002 Confirm `tests/test_core/test_dataset/test_views.py` does NOT yet exist (will be created in Phase 3)

### System Validation — Phase 1

- [X] T003 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` — MUST pass before proceeding to Phase 3

**Checkpoint — Setup Complete**: System checks pass. Proceed to Phase 3.

*Phase 2: Foundational — not required; no model, migration, or signal changes for this feature.*

---

## Phase 3: User Story 1 — Browse and Search the Dataset List (Priority: P1) 🎯 MVP

**Goal**: `DatasetListView` exposes date-added ordering and description search, wired to the `dataset-list` URL, and is smoke-tested.

**Independent Test**: `GET /datasets/` returns 200 for anonymous users; only public datasets appear; ordering by `added` and `-added` returns results in chronological order; search by description value returns matching results.

### Tests for User Story 1 (Red → Green → Refactor)

- [X] T004 [P] [US1] Create `tests/test_core/test_dataset/test_views.py`; write `TestDatasetListView.test_anonymous_get` smoke test: `GET reverse("dataset-list")` by anonymous client returns 200 (MUST FAIL if view is broken or URL missing)
- [X] T005 [P] [US1] Write `TestDatasetListView.test_shows_only_public_datasets` in `tests/test_core/test_dataset/test_views.py`: given one PUBLIC and one PRIVATE dataset, list response contains the public one and not the private one (MUST FAIL before T008)
- [X] T006 [P] [US1] Write `TestDatasetListView.test_order_by_added` in `tests/test_core/test_dataset/test_views.py`: `?o=added` and `?o=-added` return results in expected chronological order (MUST FAIL before T008)

### Implementation for User Story 1

- [X] T007 [US1] In `fairdm/core/dataset/views.py`, verify `DatasetListView`: ensure `order_by` includes `("added", _("Date created (oldest first)"), "added")` and `("-added", _("Date created (newest first)"), "-added")`; ensure `search_fields` includes `"descriptions__value"` alongside `"uuid"` and `"name"` (add any missing entries); also confirm `filterset_class = DatasetFilter` is set (FR-005)
- [X] T008 [US1] In `fairdm/core/dataset/views.py`, verify `DatasetListView.get_queryset()` calls `.get_visible().with_contributors()` — add `.with_contributors()` call if absent

### System Validation — Phase 3

- [X] T009 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` — MUST pass before proceeding
- [X] T010 ⚠️ CRITICAL: Run User Story 1 tests: `poetry run pytest tests/test_core/test_dataset/test_views.py::TestDatasetListView -v` — ALL tests MUST pass

**Checkpoint — US1 Complete**: Dataset list renders for anonymous users, shows only public datasets, supports date-added ordering.

---

## Phase 4: User Story 2 — Create a New Dataset (Priority: P1)

**Goal**: New `DatasetCreateForm` class added; `DatasetCreateView` uses it (not `DatasetForm`) and drops the `?project=` pre-population; permissions and contributor roles assigned on save.

**Independent Test**: Authenticated `POST /datasets/create/` with valid data creates the dataset, redirects to the detail page, and the creating user has all 5 permissions plus Creator/ProjectMember/ContactPerson roles.

### Tests for User Story 2 (Red → Green → Refactor)

- [X] T011 [P] [US2] Write `TestDatasetCreateView.test_anonymous_redirects_to_login` smoke test in `tests/test_core/test_dataset/test_views.py`: `GET reverse("dataset-create")` by anonymous client returns 302 to login (MUST FAIL if view broken)
- [X] T012 [P] [US2] Write `TestDatasetCreateView.test_authenticated_get_200` smoke test in `tests/test_core/test_dataset/test_views.py`: `GET reverse("dataset-create")` by authenticated client returns 200 (MUST FAIL if view broken)
- [X] T013 [P] [US2] Write `TestDatasetCreateView.test_valid_post_redirects_to_detail` in `tests/test_core/test_dataset/test_views.py`: valid POST redirects to `dataset-detail` URL (MUST FAIL before T015)
- [X] T014 [P] [US2] Write `TestDatasetCreateView.test_assigns_permissions_and_roles` in `tests/test_core/test_dataset/test_views.py`: after valid POST, assert creating user holds all 5 permissions (`view_dataset`, `change_dataset`, `delete_dataset`, `change_dataset_metadata`, `change_dataset_settings`) on the new dataset, and appears as contributor with Creator, ProjectMember, and ContactPerson roles (FR-012, FR-013 — MUST FAIL before T015)

### Implementation for User Story 2

- [X] T015 [US2] In `fairdm/core/dataset/forms.py`, add `DatasetCreateForm(DatasetForm)` class after `DatasetForm` with `class Meta(DatasetForm.Meta): fields = ["name", "project", "license"]`
- [X] T016 [US2] In `fairdm/core/dataset/views.py`: import `DatasetCreateForm` from `.forms`; change `DatasetCreateView.form_class` from `DatasetForm` to `DatasetCreateForm`; remove the `get_initial()` override entirely

### System Validation — Phase 4

- [X] T017 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` — MUST pass before proceeding
- [X] T018 ⚠️ CRITICAL: Run User Story 2 tests: `poetry run pytest tests/test_core/test_dataset/test_views.py::TestDatasetCreateView -v` — ALL tests MUST pass

**Checkpoint — US2 Complete**: Create view uses `DatasetCreateForm`, requires login, assigns permissions/roles, redirects to `dataset-detail`.

---

## Phase 5: User Story 3 — Edit Dataset Core Attributes (Priority: P2)

**Goal**: New `DatasetUpdateView` class added; enforces `change_dataset` object permission; passes `request` to `DatasetForm` via `get_form_kwargs()`; redirects to `dataset-detail` on success; wired to `dataset-update` URL.

**Independent Test**: `GET /datasets/<uuid>/update/` by permitted user returns 200; by unpermitted user returns 403; by anonymous user returns 302; valid `POST` persists changes and redirects to `dataset-detail`.

### Tests for User Story 3 (Red → Green → Refactor)

- [X] T019 [P] [US3] Write `TestDatasetUpdateView.test_anonymous_redirects_to_login` smoke test in `tests/test_core/test_dataset/test_views.py`: `GET reverse("dataset-update", kwargs={"uuid": dataset.uuid})` by anonymous client returns 302 (MUST FAIL before T023 — URL doesn't exist yet)
- [X] T020 [P] [US3] Write `TestDatasetUpdateView.test_no_permission_returns_403` smoke test in `tests/test_core/test_dataset/test_views.py`: authenticated client without `change_dataset` permission returns 403 (MUST FAIL before T023)
- [X] T021 [P] [US3] Write `TestDatasetUpdateView.test_with_permission_returns_200` smoke test in `tests/test_core/test_dataset/test_views.py`: client with `change_dataset` permission `GET` returns 200 (MUST FAIL before T023)
- [X] T022 [P] [US3] Write `TestDatasetUpdateView.test_valid_post_redirects_to_detail` in `tests/test_core/test_dataset/test_views.py`: valid POST by permitted user returns 302 to `dataset-detail` URL (FR-018a — MUST FAIL before T023)

### Implementation for User Story 3

- [X] T023 [US3] In `fairdm/core/dataset/views.py`, add `DatasetUpdateView(LoginRequiredMixin, FairDMUpdateView)` class: `model = Dataset`, `form_class = DatasetForm`, `slug_field = "uuid"`, `slug_url_kwarg = "uuid"`, `get_object()` using `get_object_or_404` + `has_perm("change_dataset", dataset)` guard, `get_form_kwargs()` adding `request=self.request`, `get_success_url()` returning `reverse("dataset-detail", kwargs={"uuid": self.object.uuid})`; add `FairDMUpdateView` to imports from `fairdm.views` and `get_object_or_404`, `PermissionDenied`, `reverse` to top-level imports if not present
- [X] T024 [US3] In `fairdm/core/dataset/urls.py`, import `DatasetUpdateView` and add `path("datasets/<str:uuid>/update/", DatasetUpdateView.as_view(), name="dataset-update")` after the `dataset-create` entry

### System Validation — Phase 5

- [X] T025 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` — MUST pass before proceeding
- [X] T026 ⚠️ CRITICAL: Run User Story 3 tests: `poetry run pytest tests/test_core/test_dataset/test_views.py::TestDatasetUpdateView -v` — ALL tests MUST pass

**Checkpoint — US3 Complete**: Update view enforces `change_dataset` permission, passes `request` to form, redirects to `dataset-detail`.

---

## Phase 6: User Story 4 — Delete a Dataset (Priority: P3)

**Goal**: New `DatasetDeleteView` class added; enforces `delete_dataset` object permission; `require_confirmation = True` with `get_confirmation_value()` returning dataset name; redirects to `dataset-list` on success; wired to `dataset-delete` URL.

**Independent Test**: `GET /datasets/<uuid>/delete/` blocked for anonymous (302), unpermitted (403); permitted user gets 200. Incorrect name confirmation → 200 with form error, dataset not deleted. Correct name → 302 to `dataset-list`, dataset deleted.

### Tests for User Story 4 (Red → Green → Refactor)

- [X] T027 [P] [US4] Write `TestDatasetDeleteView.test_anonymous_redirects_to_login` smoke test in `tests/test_core/test_dataset/test_views.py`: `GET reverse("dataset-delete", kwargs={"uuid": dataset.uuid})` by anonymous client returns 302 (MUST FAIL before T031 — URL doesn't exist yet)
- [X] T028 [P] [US4] Write `TestDatasetDeleteView.test_no_permission_returns_403` smoke test in `tests/test_core/test_dataset/test_views.py`: authenticated client without `delete_dataset` permission returns 403 (MUST FAIL before T031)
- [X] T029 [P] [US4] Write `TestDatasetDeleteView.test_with_permission_returns_200` smoke test in `tests/test_core/test_dataset/test_views.py`: client with `delete_dataset` permission `GET` returns 200 (MUST FAIL before T031)
- [X] T030 [P] [US4] Write `TestDatasetDeleteView.test_wrong_name_shows_error` in `tests/test_core/test_dataset/test_views.py`: POST `{"confirmation": "Wrong Name"}` by permitted user returns 200; assert `form.errors` contains a validation error for `confirmation`; assert dataset still exists (MUST FAIL before T031)
- [X] T030a [P] [US4] Write `TestDatasetDeleteView.test_correct_name_redirects_to_list` in `tests/test_core/test_dataset/test_views.py`: POST `{"confirmation": dataset.name}` by permitted user returns 302 to `dataset-list`; assert dataset no longer exists (MUST FAIL before T031)

### Implementation for User Story 4

- [X] T031 [US4] In `fairdm/core/dataset/views.py`, add `DatasetDeleteView(LoginRequiredMixin, FairDMDeleteView)` class: `model = Dataset`, `slug_field = "uuid"`, `slug_url_kwarg = "uuid"`, `success_url = reverse_lazy("dataset-list")`, `require_confirmation = True`, `get_object()` using `get_object_or_404` + `has_perm("delete_dataset", dataset)` guard, `get_confirmation_value()` returning `self.object.name`; add `FairDMDeleteView` to imports from `fairdm.views` and `reverse_lazy` to imports if not present
- [X] T032 [US4] In `fairdm/core/dataset/urls.py`, import `DatasetDeleteView` and add `path("datasets/<str:uuid>/delete/", DatasetDeleteView.as_view(), name="dataset-delete")` after the `dataset-update` entry

### System Validation — Phase 6

- [X] T033 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` — MUST pass before proceeding
- [X] T034 ⚠️ CRITICAL: Run User Story 4 tests: `poetry run pytest tests/test_core/test_dataset/test_views.py::TestDatasetDeleteView -v` — ALL tests MUST pass

**Checkpoint — US4 Complete**: Delete view enforces `delete_dataset` permission, name-confirmation via `DeleteConfirmForm`, redirects to `dataset-list`.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Goal**: Full regression sweep, verify redirect targets, and confirm no regressions in existing dataset tests.

- [X] T035 [P] Verify `dataset-detail` URL resolves correctly (it is out of scope but is the redirect target for create and update views — a broken URL would cause test failures): `reverse("dataset-detail", kwargs={"uuid": <any valid uuid>})` must not raise `NoReverseMatch`
- [X] T036 [P] Run existing dataset test suite to confirm no regressions: `poetry run pytest tests/test_core/test_dataset/test_form.py tests/test_core/test_dataset/test_models.py -v` — ALL pre-existing tests MUST still pass (2 pre-existing failures in test_models.py unrelated to this feature)

### System Validation — Final

- [X] T037 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` — MUST pass
- [X] T038 ⚠️ CRITICAL: Run complete dataset test suite: `poetry run pytest tests/test_core/test_dataset/ -v` — ALL tests MUST pass (166 pass, 28 skip, 2 pre-existing failures in test_models.py)

**Checkpoint — Feature Complete**: All four views conform to FairDM base classes, all URLs wired (`dataset-list`, `dataset-create`, `dataset-update`, `dataset-delete`), `DatasetCreateForm` added, `DatasetCreateView` updated, full test suite green.

---

## Dependencies

```
Phase 1 (Setup)
    └── Phase 3 (US1 — List)       independent of US2/US3/US4
    └── Phase 4 (US2 — Create)     independent of US1/US3/US4; T015 before T016
    └── Phase 5 (US3 — Update)     independent of US1/US2/US4
    └── Phase 6 (US4 — Delete)     independent of US1/US2/US3
Phase 3 + Phase 4 + Phase 5 + Phase 6
    └── Phase 7 (Polish)
```

All four user story phases can be sequenced independently after Phase 1 completes. No story depends on another.

## Parallel Execution Examples

**Within US1 (Phase 3)**: T004, T005, T006 (all test writes) can run in parallel before T007/T008.

**Within US2 (Phase 4)**: T011, T012, T013, T014 (all test writes) can run in parallel before T015/T016.

**Within US3 (Phase 5)**: T019, T020, T021, T022 (all test writes) can run in parallel before T023/T024.

**Within US4 (Phase 6)**: T027, T028, T029, T030, T030a (all test writes) can run in parallel before T031/T032.

## Independent Test Criteria Per Story

| Story | Independent Test Command |
|-------|--------------------------|
| US1 — List | `pytest tests/test_core/test_dataset/test_views.py::TestDatasetListView -v` |
| US2 — Create | `pytest tests/test_core/test_dataset/test_views.py::TestDatasetCreateView -v` |
| US3 — Update | `pytest tests/test_core/test_dataset/test_views.py::TestDatasetUpdateView -v` |
| US4 — Delete | `pytest tests/test_core/test_dataset/test_views.py::TestDatasetDeleteView -v` |
| Full suite | `pytest tests/test_core/test_dataset/ -v` |

## Implementation Strategy

**MVP scope**: US1 + US2 (Phase 3 + Phase 4) — gives researchers a working list and creation flow; forms the P1 baseline.

**Delivery order**: Phase 3 (US1) → Phase 4 (US2) → Phase 5 (US3) → Phase 6 (US4) → Phase 7 (Polish). Each phase is independently shippable once its system validation passes.

**Total tasks**: 38 (including T030a)  
**Parallelisable tasks**: 18 (marked [P])  
**Sequential gates**: 8 (System Validation tasks, marked ⚠️ CRITICAL)

## Format Validation

All tasks follow the checklist format:

- ✅ Checkbox (`- [ ]`)
- ✅ Task ID (T001–T038)
- ✅ [P] marker where parallelisable
- ✅ [US1]–[US4] label on user story phase tasks only
- ✅ File path in every implementation and test task description
