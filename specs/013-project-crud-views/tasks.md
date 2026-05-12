# Tasks: Project CRUD Views

**Input**: Design documents from `/specs/013-project-crud-views/`
**Propagated**: 2026-05-11 — Updated from spec.md refinement: added Phase 5b tasks for FR-028 form hierarchy (all completed).
**Propagated**: 2026-05-11 — Updated from spec.md refinement: `TypedChoiceField(coerce=int)` for `status`/`visibility`; concept-private validation rule removed; `ProjectForm.clean()` and `ProjectCreateForm.clean()` overrides must be deleted; `test_edit_form_cannot_set_public_for_concept` must be removed.
**Prerequisites**: plan.md, spec.md, research.md, data-model.md

**Tests**: Tests are included per the framework's test-first requirement (Constitution Principle V — URL Smoke Test Coverage mandatory for all new URL patterns)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US4)
- Exact file paths included in each description

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify environment, existing file state, and import structure before any changes

- [X] T001 Confirm feature branch `013-project-crud-views` is active (`git branch --show-current`) and Poetry virtualenv is activated
- [X] T002 Confirm existing view imports in `fairdm/core/project/views.py` — identify all classes imported from `django.views.generic` that will need replacing

### System Validation — Phase 1

- [X] T003 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` — MUST pass before proceeding to Phase 2

**Checkpoint — Setup Complete**: System checks pass. Proceed to Phase 2.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add the `PublicDatasetsProtect` exception and update the `pre_delete` signal — required by the delete view before it can be written. Must be complete before Phase 6.

**⚠️ CRITICAL**: The delete view (US4) cannot be implemented without this phase.

### Tests (Red → Green → Refactor)

- [X] T004 [P] Write `test_pre_delete_signal_blocks_public_datasets` in `tests/test_core/test_project/test_models.py`: given a project with a PUBLIC dataset, calling `project.delete()` MUST raise `PublicDatasetsProtect` (MUST FAIL before T007)
- [X] T005 [P] Write `test_pre_delete_signal_allows_private_only` in `tests/test_core/test_project/test_models.py`: given a project with only PRIVATE datasets, `project.delete()` MUST succeed (MUST FAIL before T007)
- [X] T006 [P] Write `test_pre_delete_signal_allows_no_datasets` in `tests/test_core/test_project/test_models.py`: given a project with no datasets, `project.delete()` MUST succeed (MUST FAIL before T007)

### Implementation

- [X] T007 Add `PublicDatasetsProtect` exception class in `fairdm/core/project/models.py` above the `@receiver` block, and update `prevent_project_deletion_with_datasets` to narrow the guard to `visibility=Visibility.PUBLIC` datasets and raise `PublicDatasetsProtect(public_datasets)` instead of `ValidationError`

### System Validation — Phase 2

- [X] T008 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` — MUST pass before proceeding
- [X] T009 ⚠️ CRITICAL: Run model tests: `poetry run pytest tests/test_core/test_project/test_models.py -v` — ALL tests MUST pass before proceeding to any user story

**Checkpoint — Foundation Ready**: Pre-delete guard raises `PublicDatasetsProtect` for public datasets only. Phase 3+ can begin.

---

## Phase 3: User Story 1 — Browse and Search the Project List (Priority: P1) 🎯 MVP

**Goal**: `ProjectListView` inherits `FairDMListView`, exposes creation-date ordering options, and is smoke-tested.

**Independent Test**: `GET /projects/` returns 200 for anonymous users; only public projects appear; ordering by `added` and `-added` returns results in chronological order.

### Tests for User Story 1 (Red → Green → Refactor)

- [X] T010 [P] [US1] Write `test_project_list_anonymous_200` smoke test in `tests/test_core/test_project/test_views.py`: `GET reverse("project-list")` by anonymous client returns 200 (MUST FAIL if view is broken or URL missing)
- [X] T011 [P] [US1] Write `test_project_list_shows_only_public` in `tests/test_core/test_project/test_views.py`: given one PUBLIC and one PRIVATE project, list shows only the public one (MUST FAIL before T013)
- [X] T012 [P] [US1] Write `test_project_list_order_by_added` in `tests/test_core/test_project/test_views.py`: `?o=added` and `?o=-added` return results in expected chronological order (MUST FAIL before T013)

### Implementation for User Story 1

- [X] T013 [US1] In `fairdm/core/project/views.py`, extend `ProjectListView.order_by` to include `("added", _("Date created (oldest first)"))` and `("-added", _("Date created (newest first)"))` alongside the existing name entries

### System Validation — Phase 3

- [X] T014 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` — MUST pass before proceeding
- [X] T015 ⚠️ CRITICAL: Run User Story 1 tests: `poetry run pytest tests/test_core/test_project/test_views.py::TestProjectListView -v` — ALL tests MUST pass

**Checkpoint — US1 Complete**: Project list renders for anonymous users, shows only public projects, supports creation-date ordering.

---

## Phase 4: User Story 2 — Create a New Project (Priority: P1)

**Goal**: `ProjectCreateView` inherits `FairDMCreateView`, requires login, redirects to `project-detail` on success, assigns permissions and contributor roles.

**Independent Test**: Authenticated `POST /projects/create/` with valid data creates the project, redirects to the detail page, and the creating user has all 5 permissions plus Creator/ProjectMember/ContactPerson roles.

### Tests for User Story 2 (Red → Green → Refactor)

- [X] T016 [P] [US2] Write `test_project_create_anonymous_redirects_to_login` smoke test in `tests/test_core/test_project/test_views.py`: `GET reverse("project-create")` by anonymous client returns 302 to login (MUST FAIL if view broken)
- [X] T017 [P] [US2] Write `test_project_create_authenticated_200` smoke test in `tests/test_core/test_project/test_views.py`: `GET reverse("project-create")` by authenticated client returns 200 (MUST FAIL if view broken)
- [X] T018 [P] [US2] Write `test_project_create_redirects_to_detail` in `tests/test_core/test_project/test_views.py`: valid POST redirects to `project-detail` URL (not `project:overview`) (MUST FAIL before T019)
- [X] T018a [P] [US2] Write `test_project_create_assigns_permissions_and_roles` in `tests/test_core/test_project/test_views.py`: after valid POST, assert creating user holds all 5 permissions (`view_project`, `change_project`, `delete_project`, `change_project_metadata`, `change_project_settings`) on the new project, and appears as contributor with Creator, ProjectMember, and ContactPerson roles (FR-012, FR-013 — MUST FAIL before T019)

### Implementation for User Story 2

- [X] T019 [US2] In `fairdm/core/project/views.py`, update `ProjectCreateView.get_success_url()` to return `reverse("project-detail", kwargs={"uuid": self.object.uuid})` — replacing `return self.object.get_absolute_url()`

### System Validation — Phase 4

- [X] T020 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` — MUST pass before proceeding
- [X] T021 ⚠️ CRITICAL: Run User Story 2 tests: `poetry run pytest tests/test_core/test_project/test_views.py::TestProjectCreateView -v` — ALL tests MUST pass

**Checkpoint — US2 Complete**: Create view requires login, creates project with correct permissions/roles, redirects to `project-detail`.

---

## Phase 5: User Story 3 — Edit Project Core Attributes (Priority: P2)

**Goal**: `ProjectUpdateView` inherits `FairDMUpdateView` (migrated from raw `UpdateView`), enforces `change_project` object permission, redirects to `project-detail` on success.

**Independent Test**: Authenticated `GET /projects/<uuid>/update/` by permitted user returns 200; by unpermitted user returns 403; valid `POST` persists changes and redirects to `project-detail`.

### Tests for User Story 3 (Red → Green → Refactor)

- [X] T022 [P] [US3] Write `test_project_update_anonymous_redirects_to_login` smoke test in `tests/test_core/test_project/test_views.py`: `GET reverse("project-update", ...)` by anonymous client returns 302 (MUST FAIL if view broken)
- [X] T023 [P] [US3] Write `test_project_update_without_permission_403` smoke test in `tests/test_core/test_project/test_views.py`: authenticated client without `change_project` permission returns 403 (MUST FAIL before T025)
- [X] T024 [P] [US3] Write `test_project_update_with_permission_200` smoke test in `tests/test_core/test_project/test_views.py`: client with `change_project` permission returns 200 (MUST FAIL if base class wrong)
- [X] T024a [P] [US3] Write `test_project_update_success_redirects_to_detail` in `tests/test_core/test_project/test_views.py`: valid POST by permitted user returns 302 to `project-detail` URL (FR-018a — MUST FAIL before T025)

### Implementation for User Story 3

- [X] T025 [US3] In `fairdm/core/project/views.py`, change `ProjectUpdateView` base class from `UpdateView` to `FairDMUpdateView`; add `FairDMUpdateView` to imports from `fairdm.views`; remove `UpdateView` from `django.views.generic` import if no longer used

### System Validation — Phase 5

- [X] T026 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` — MUST pass before proceeding
- [X] T027 ⚠️ CRITICAL: Run User Story 3 tests: `poetry run pytest tests/test_core/test_project/test_views.py::TestProjectUpdateView -v` — ALL tests MUST pass

**Checkpoint — US3 Complete**: Update view uses `FairDMUpdateView`, permission-enforces access, redirects to `project-detail`.

---

## Phase 5b: Form Hierarchy Refactoring (FR-028 refinement)

**Goal**: `ProjectForm` becomes the single full form class (all fields, widgets, help_texts, validation). `ProjectCreateForm` inherits it and restricts its field set. `ProjectUpdateForm` is removed. `ProjectUpdateView.form_class` updated.

**Status**: All tasks completed as part of spec refinement on 2026-05-11.

- [X] T041 Promote `ProjectForm` in `fairdm/core/project/forms.py` to declare all directly editable fields (`image`, `name`, `status`, `visibility`, `owner`, `funding`) with explicit widgets and help_texts; add owner-queryset setup in `__init__` (conditional on `"owner" in self.fields`); ~~add `clean()` enforcing the concept-private rule~~ — concept-private rule is removed; no `clean()` override required on `ProjectForm`
- [X] T042 Refactor `ProjectCreateForm` to inherit from `ProjectForm`; set `class Meta(ProjectForm.Meta)` with `fields = ["name", "status", "visibility"]`; override `visibility` field with `RadioSelect` widget; ~~override `clean()` to bypass concept-private rule via `super(ProjectForm, self).clean()`~~ — concept-private rule is removed; no `clean()` override required on `ProjectCreateForm`
- [X] T043 Remove `ProjectUpdateForm` class from `fairdm/core/project/forms.py`
- [X] T044 Update `fairdm/core/project/views.py`: replace `from .forms import ProjectCreateForm, ProjectUpdateForm` with `from .forms import ProjectCreateForm, ProjectForm`; set `ProjectUpdateView.form_class = ProjectForm`
- [X] T045 Update `tests/test_core/test_project/test_forms.py`: replace `ProjectUpdateForm` imports with `ProjectForm` in `TestProjectUpdateForm` tests
- [X] T046 Update `tests/test_core/test_project/test_integration.py`: use `ProjectCreateForm` (not `ProjectForm`) for `TestProjectForm` tests that submit creation-style data (no `owner` field)

### System Validation — Phase 5b

- [X] T047 ⚠️ CRITICAL: Run full project test suite: `poetry run pytest tests/test_core/test_project/ -v` — 74 passed, 2 skipped

**Checkpoint — Phase 5b Complete**: Form hierarchy consolidated; `ProjectUpdateForm` removed; all tests green.

---

## Phase 5c: TypedChoiceField + Concept-Private Rule Removal (FR-028 refinement)

**Goal**: `status` and `visibility` in `ProjectForm` use `TypedChoiceField(coerce=int)`; `ProjectForm.clean()` and `ProjectCreateForm.clean()` overrides are deleted; test that asserted the concept-private rule is removed.

- [X] T051 In `fairdm/core/project/forms.py`, change the `status` field declaration from `forms.ChoiceField(...)` to `forms.TypedChoiceField(coerce=int, ...)` in `ProjectForm`
- [X] T052 In `fairdm/core/project/forms.py`, change the `visibility` field declaration from `forms.ChoiceField(...)` to `forms.TypedChoiceField(coerce=int, ...)` in `ProjectForm`
- [X] T053 In `fairdm/core/project/forms.py`, change the `visibility` field override in `ProjectCreateForm` from `forms.ChoiceField(...)` to `forms.TypedChoiceField(coerce=int, ...)` (keeping `RadioSelect` widget)
- [X] T054 In `fairdm/core/project/forms.py`, delete `ProjectForm.clean()` entirely (removes manual `int()` coercion and the concept-private `ValidationError`); remove now-unused imports: `ValidationError` (if not used elsewhere in the file), `ProjectStatus`, `Visibility` (check whether still imported before removing)
- [X] T055 In `fairdm/core/project/forms.py`, delete `ProjectCreateForm.clean()` entirely (it only bypassed the now-removed rule)
- [X] T056 In `tests/test_core/test_project/test_forms.py`, delete `TestProjectUpdateForm.test_edit_form_cannot_set_public_for_concept` (this test asserted a rule that no longer exists)
- [X] T057 [P] In `tests/test_core/test_project/test_forms.py`, add `test_form_allows_concept_public_combination` to `TestProjectUpdateForm`: verify that submitting `status=CONCEPT, visibility=PUBLIC` is **valid** (form `is_valid()` returns `True`, no errors on `visibility` or `__all__`)

### System Validation — Phase 5c

- [X] T058 ⚠️ CRITICAL: Run full project test suite: `poetry run pytest tests/test_core/test_project/ -v` — ALL tests MUST pass

---

## Phase 6: User Story 4 — Delete a Project (Priority: P3)

**Goal**: New `ProjectDeleteView` enforces `delete_project` permission, requires name-confirmation, catches `PublicDatasetsProtect` and lists blocking datasets, redirects to `project-list` on success; wired to `project-delete` URL.

**Independent Test**: `DELETE` flow blocked for unauthenticated users (302), unpermitted users (403), wrong name confirmation (200 with error), project with public datasets (200 with dataset list). Correct name + no public datasets → 302 to `project-list`.

### Tests for User Story 4 (Red → Green → Refactor)

- [X] T028 [P] [US4] Write `test_project_delete_anonymous_redirects_to_login` smoke test in `tests/test_core/test_project/test_views.py`: `GET reverse("project-delete", ...)` by anonymous client returns 302 (MUST FAIL before T033 — URL doesn't exist yet)
- [X] T029 [P] [US4] Write `test_project_delete_without_permission_403` smoke test in `tests/test_core/test_project/test_views.py`: client without `delete_project` permission returns 403 (MUST FAIL before T033)
- [X] T030 [P] [US4] Write `test_project_delete_with_permission_200` smoke test in `tests/test_core/test_project/test_views.py`: client with `delete_project` permission `GET` returns 200 (MUST FAIL before T033)
- [X] T031 [P] [US4] Rewrite `test_project_delete_wrong_name_shows_error` in `tests/test_core/test_project/test_views.py`: POST with `{"confirmation": "Wrong Name"}` (the `DeleteConfirmForm` field name, NOT `confirm_name`) returns 200 with a form validation error; project not deleted (reopened — BUG-001: previous version tested `name_error` context key from custom `post()`, which no longer exists)
- [X] T032 [P] [US4] Update `test_project_delete_blocks_public_datasets` in `tests/test_core/test_project/test_views.py`: change POST key from `confirm_name` to `confirmation` (reopened — BUG-001: test code still uses old field name; description was updated but implementation was not)
- [X] T032a [P] [US4] Update `test_project_delete_allows_private_only_datasets` in `tests/test_core/test_project/test_views.py`: change POST key from `confirm_name` to `confirmation` (reopened — BUG-001)
- [X] T032b [P] [US4] Update `test_project_delete_no_datasets_success` in `tests/test_core/test_project/test_views.py`: change POST key from `confirm_name` to `confirmation` (reopened — BUG-001)

### Implementation for User Story 4

- [X] T033 [US4] Refactor `ProjectDeleteView` in `fairdm/core/project/views.py` (reopened — BUG-001): remove custom `post()` method; add `require_confirmation = True`; add `get_confirmation_value()` returning `self.object.name`; add `form_valid()` that calls `super().form_valid(form)` inside `try/except PublicDatasetsProtect` and re-renders with `protected_datasets` context on failure. `HttpResponseRedirect` import can be removed if no longer used elsewhere.
- [X] T034 [US4] In `fairdm/core/project/urls.py`, import `ProjectDeleteView` and add URL pattern `path("projects/<str:uuid>/delete/", ProjectDeleteView.as_view(), name="project-delete")` after the `project-update` entry

### System Validation — Phase 6

- [X] T035 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` — MUST pass before proceeding
- [X] T036 ⚠️ CRITICAL: Run User Story 4 tests: `poetry run pytest tests/test_core/test_project/test_views.py::TestProjectDeleteView -v` — ALL tests MUST pass (reopened — BUG-001: T031 rewrite and T033 refactor must complete first)

**Checkpoint — US4 Complete**: Delete view enforces permissions, name confirmation via `DeleteConfirmForm`, public-dataset guard in `form_valid()`, and redirects to `project-list`.

---

## Phase 6b: BUG-001 Fix — Name-Confirmation via MVPDeleteView

**Bugfix**: 2026-05-11 — BUG-001 Updated from bugfix patch

- [X] T048 [US4] Rewrite `test_project_delete_wrong_name_shows_error` in `tests/test_core/test_project/test_views.py`: POST `{"confirmation": "Wrong Name"}` (the `DeleteConfirmForm` field) returns 200; assert `form.errors` contains a validation error for `confirmation`; assert project still exists (replaces old `name_error` context-key assertion)
- [X] T049 [US4] Refactor `ProjectDeleteView` in `fairdm/core/project/views.py`: remove `post()` override; add `require_confirmation = True`; add `get_confirmation_value(self)` returning `self.object.name`; add `form_valid()` wrapping `super().form_valid(form)` in `try/except PublicDatasetsProtect` that re-renders with `protected_datasets` context; remove `HttpResponseRedirect` import if no longer used elsewhere
- [X] T050 ⚠️ CRITICAL: Run full project test suite: `poetry run pytest tests/test_core/test_project/ -v` — ALL tests MUST pass

---

## Phase 7: Polish & Cross-Cutting Concerns

**Goal**: Full regression sweep and cleanup.

- [X] T037 [P] Remove `UpdateView` from the `django.views.generic` import in `fairdm/core/project/views.py` if it is no longer referenced after T025; do NOT remove `DetailView` — it is used by the out-of-scope `ProjectDetailView` (FR-027)
- [X] T038 [P] Verify `project-detail` URL resolves correctly (it is out of scope but is the redirect target for create and update — a broken URL would cause test failures)

### System Validation — Final

- [X] T039 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` — MUST pass
- [X] T040 ⚠️ CRITICAL: Run complete project test suite: `poetry run pytest tests/test_core/test_project/ -v` — ALL tests MUST pass (2 pre-existing TestProjectDetailView failures excluded — out of scope)

**Checkpoint — Feature Complete**: All four views conform to FairDM base classes, all URLs wired, model guard narrowed to public datasets, full test suite green.

---

## Dependencies

```
Phase 1 (Setup)
  ├── Phase 3 (US1 — list ordering)      [no Phase 2 dependency]
  ├── Phase 4 (US2 — create redirect)    [no Phase 2 dependency]
  ├── Phase 5 (US3 — update base class)  [no Phase 2 dependency]
  └── Phase 2 (Foundational — PublicDatasetsProtect + signal)
        └── Phase 6 (US4 — delete view)  [depends on Phase 2]
              └── Phase 7 (Polish)
```

Phases 3, 4, 5, and 6 can proceed in parallel once Phase 2 is complete.

## Parallel Execution

After Phase 2 passes (T009 green), the following can be worked simultaneously:

| Stream A | Stream B | Stream C | Stream D |
|----------|----------|----------|----------|
| T010–T015 (US1 list) | T016–T021 (US2 create) | T022–T027 (US3 update) | T028–T036 (US4 delete) |

## Implementation Strategy

**MVP scope**: Phase 3 (US1) alone delivers a working, smoke-tested list page — the entry point for the project area.

**Recommended delivery order**: Phase 2 → Phase 6 (highest complexity, benefits most from early feedback) → Phases 3, 4, 5 in parallel → Phase 7.

**Task count**: 52 tasks total  

- Phase 1: 3 | Phase 2: 6 | Phase 3: 6 | Phase 4: 7 | Phase 5: 7 | Phase 5b: 7 | Phase 6: 11 | Phase 6b: 3 | Phase 7: 4  
- Test tasks: 21 | Implementation tasks: 20 | Validation tasks: 8 | Bugfix tasks: 3
