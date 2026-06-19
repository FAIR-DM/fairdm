# Tasks: Image Field Requirements for Core Models

**Input**: Design documents from `/specs/015-image-field-spec/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md
**Tests**: Included per Constitution Principle V (test-first)
**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify all prerequisites are in place before any changes

- [x] T001 Confirm `easy_thumbnails` = 2.10 is listed in `pyproject.toml` and resolvable: `poetry run python -c "import easy_thumbnails; print(easy_thumbnails.__version__)"`
- [x] T002 Confirm `"easy_thumbnails"` appears in `INSTALLED_APPS` in `fairdm/conf/settings/apps.py`

### System Validation � Phase 1

- [x] T003 ?? CRITICAL: Run Django system checks: `poetry run python manage.py check` � MUST pass before proceeding

**Checkpoint � Setup Complete**: System checks pass. Proceed to Phase 2.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared utilities and settings changes that ALL user story phases depend on

**?? CRITICAL**: No user story work can begin until this phase is complete

### Shared Image Utilities

- [x] T004 Create `fairdm/core/image_utils.py` with:
  - `MAX_IMAGE_UPLOAD_BYTES = 5 * 1024 * 1024`
  - `IMAGE_HELP_TEXT` lazy-translated string: recommended 3:2 ratio (e.g., 1200�800 px), accepted formats (JPEG/PNG/WebP), max 5 MB, note about centre-cropping on mismatch
  - `validate_image_file_size(file)` validator raising `ValidationError` when `file.size > MAX_IMAGE_UPLOAD_BYTES` with a human-readable message including the actual file size in MB

### BaseModel Field Update

- [x] T005 Add `resize_source=dict(size=(2400, 1600), crop=False)` to the `ThumbnailerImageField` in `fairdm/core/abstract.py` (no migration needed � Python-level kwarg only)

### Thumbnail Aliases

- [x] T006 Add project-wide thumbnail aliases to `THUMBNAIL_ALIASES` in `fairdm/conf/settings/static_media.py`:
  ```python
  "": {
      "core_small": {"size": (600, 400), "crop": "smart"},
      "core_large": {"size": (1200, 800), "crop": "smart"},
  }
  ```

### System Validation � Phase 2

- [x] T007 ?? CRITICAL: Run Django system checks: `poetry run python manage.py check` � MUST pass before proceeding
- [x] T008 ?? CRITICAL: Run foundation tests: `poetry run pytest tests/ -k "image" -v` � ALL tests MUST pass before proceeding

**Checkpoint � Foundation Ready**: System checks pass and no existing image-related tests are broken. User story phases can now begin.

---

## Phase 3: User Story 1 - Upload Representative Image (Priority: P1) ?? MVP

**Goal**: All four core model edit forms communicate 3:2 ratio, max file size, and accepted formats via help text; enforce 5 MB limit via a form validator; and display the current image as a preview in edit mode via `ImageClearableFileInput`.

**Independent Test**: Navigate to each of the four model edit forms; confirm the image field shows "3:2" in its help text; attempt to upload a 6 MB file and confirm a validation error is returned; confirm an existing saved image appears as a preview thumbnail.

### Tests for User Story 1 — Write FIRST, confirm they FAIL before T013–T016

- [x] T009 [P] [US1] In `tests/test_forms/test_image_fields.py` write `test_image_help_text_contains_ratio` � instantiate ProjectForm, DatasetForm, SampleForm, MeasurementForm; assert each `image` field `help_text` contains "3:2"
- [x] T010 [P] [US1] In `tests/test_forms/test_image_fields.py` write `test_image_field_uses_clearable_widget` � assert each form's `image` field widget is an instance of `ImageClearableFileInput`
- [x] T011 [P] [US1] In `tests/test_forms/test_image_fields.py` write `test_image_field_rejects_oversized_file` � create an in-memory file of 6 MB, bind to ProjectForm, assert `form.errors["image"]` contains the file size error message
- [x] T012 [P] [US1] In `tests/test_forms/test_image_fields.py` write `test_image_field_accepts_valid_file` � bind a valid 1 MB JPEG to ProjectForm, assert `form.is_valid()` is True
- [x] T034 [P] [US1] In `tests/test_forms/test_image_fields.py` write `test_image_field_rejects_non_image` — bind a 1 MB PDF file (wrong format) to ProjectForm, assert `form.errors["image"]` contains a format-validation error (covers FR-004)
- [x] T035 [P] [US1] In `tests/test_forms/test_image_fields.py` write `test_image_field_clear_shows_placeholder` — submit a bound form with the `image-clear` checkbox set, verify the resulting model instance has a falsy `image` field, and assert that the object card template renders the static placeholder path in the `<img>` src (covers FR-008 / Edge Case 5)

### Implementation for User Story 1

- [x] T013 [P] [US1] Update `fairdm/core/project/forms.py`: replace the bare `ImageField(required=False, label=False)` with an explicit `ImageField` using `IMAGE_HELP_TEXT`, `validate_image_file_size`, and `ImageClearableFileInput(thumbnail_options={"size": (150, 100), "crop": True})`
- [x] T014 [P] [US1] Update `fairdm/core/dataset/forms.py`: replace the existing `ImageField` (which incorrectly references 16:9) with the same standard declaration using `IMAGE_HELP_TEXT` from `fairdm/core/image_utils.py`
- [x] T015 [P] [US1] Update `fairdm/core/sample/forms.py`: remove the `"image": forms.ClearableFileInput(...)` entry from `Meta.widgets` and `Meta.help_text`, and add an explicit top-level `ImageField` declaration matching the standard pattern
- [x] T016 [P] [US1] Update `fairdm/core/measurement/forms.py`: same as T015 � remove `ClearableFileInput` from `Meta.widgets` and `Meta.help_text["image"]`, add explicit `ImageField` declaration

### System Validation � Phase 3

- [x] T017 ?? CRITICAL: Run Django system checks: `poetry run python manage.py check` � MUST pass before proceeding
- [x] T018 ?? CRITICAL: Run User Story 1 tests: `poetry run pytest tests/test_forms/test_image_fields.py -v` � ALL tests MUST pass

**Checkpoint � US1 Complete**: All four forms show 3:2 help text, reject oversized files, accept valid images, and display edit-mode previews.

---

## Phase 4: User Story 2 - View Thumbnails Across Portal Contexts (Priority: P2)

**Goal**: Card/listing views serve the `core_small` (600�400) thumbnail; detail view templates serve the `core_large` (1200�800) thumbnail; no full-resolution images are loaded in listing contexts; the external `placehold.net` placeholder URL is replaced with a static asset.

**Independent Test**: Browse the Project listing page; open browser DevTools Network tab; confirm image requests return files whose URL contains `600x400` (or the `core_small` alias); confirm that records with no image show the local placeholder, not a 404 or external URL.

### Tests for User Story 2 � Write FIRST, confirm they FAIL before T022

- [x] T019 [P] [US2] In `tests/test_forms/test_image_fields.py` write `test_core_small_alias_resolves` � create a Project instance with a real uploaded image fixture; call `thumbnailer["core_small"].url`; assert the result is a non-empty string and the thumbnail file exists
- [x] T020 [P] [US2] In `tests/test_forms/test_image_fields.py` write `test_core_large_alias_resolves` � same for `core_large`

### Implementation for User Story 2

- [x] T021 [US2] Add placeholder static image `fairdm/static/fairdm/img/placeholder-3x2.png` — a production-quality 600×400 grey PNG in the correct 3:2 aspect ratio, used by all four core model types across listing and detail views
- [x] T022 [US2] Update `fairdm/templates/cotton/components/object_card.html`:
  - Replace `{{ image.url }}` with `{{ image|thumbnail_url:"core_small" }}` (add `{% load thumbnail %}` at top)
  - Replace the `placehold.net` fallback `<img src>` with `{% static 'fairdm/img/placeholder-3x2.png' %}`
- [x] T023 [US2] Update `fairdm/core/measurement/templates/measurement/plugins/overview.html`:
  - Replace `{{ measurement.dataset.project.image.url }}` with `{{ measurement.dataset.project.image|thumbnail_url:"core_small" }}`
  - Wrap in an `{% load thumbnail %}` tag at the top of the file if not already present
- [x] T036 [P] [US2] Update the Project and Dataset detail page header templates to serve the `core_large` (1200×800) thumbnail (US2 Acceptance Scenario 2):
  - In `fairdm/core/project/templates/project/project_detail.html`, find the header `<img>` element and replace direct `.url` access with `{{ object.image|thumbnail_url:"core_large" }}` (add `{% load thumbnail %}` at top if absent)
  - Apply the same change to the equivalent Dataset detail template

### System Validation — Phase 4

- [x] T024 ?? CRITICAL: Run Django system checks: `poetry run python manage.py check` � MUST pass before proceeding
- [x] T025 ?? CRITICAL: Run User Story 2 tests: `poetry run pytest tests/test_forms/test_image_fields.py -v` � ALL tests MUST pass

**Checkpoint � US2 Complete**: Listing views use `core_small` thumbnails; detail contexts use `core_large`; placeholder is served locally.

---

## Phase 5: User Story 3 - Consistent Image Display Across All Core Model Types (Priority: P3)

**Goal**: Automated tests confirm that Project, Dataset, Sample, and Measurement all expose identical image field configuration (help text, widget, validator, thumbnail aliases), eliminating the possibility of silent divergence.

**Independent Test**: Run the cross-model consistency test suite; all four model types must pass identical assertions with no model-specific exceptions.

### Tests for User Story 3 � Write FIRST, confirm they FAIL before T027

- [x] T026 [P] [US3] In `tests/test_forms/test_image_fields.py` write `test_all_core_forms_image_field_uniform` � parameterised test over [ProjectForm, DatasetForm, SampleForm, MeasurementForm]; for each form assert:
  - `image` field `help_text` contains "3:2"
  - `image` field widget is `ImageClearableFileInput`
  - `validate_image_file_size` is in `image` field `validators`
  - `image` field `required` is `False`

### Implementation for User Story 3

- [x] T027 [US3] Review all four updated forms side-by-side and confirm no per-model divergence in the `image` field declaration; fix any inconsistencies found

### System Validation � Phase 5

- [x] T028 ?? CRITICAL: Run Django system checks: `poetry run python manage.py check` � MUST pass
- [x] T029 ?? CRITICAL: Run User Story 3 tests: `poetry run pytest tests/test_forms/test_image_fields.py -v` � ALL tests MUST pass

**Checkpoint � US3 Complete**: All three user stories are independently functional and cross-model consistency is verified by tests.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Admin integration, optional HiRes support note, and final test suite run

- [x] T030 [P] Set `THUMBNAIL_WIDGET_OPTIONS = {"size": (150, 100)}` in `fairdm/conf/settings/static_media.py` so the Django admin automatically uses 3:2 preview dimensions for `ThumbnailerImageField` via `formfield_overrides`
- [x] T031 [P] Add a brief comment block above the new `"": { ... }` entry in `THUMBNAIL_ALIASES` explaining the 3:2 convention and the two alias names, for future maintainers

### System Validation � Final

- [x] T032 ?? CRITICAL: Run Django system checks: `poetry run python manage.py check` � MUST pass
- [x] T033 ?? CRITICAL: Run full feature test suite: `poetry run pytest tests/test_forms/test_image_fields.py -v` � ALL tests MUST pass

**Checkpoint � Feature Complete**: System checks pass and entire image field test suite is green.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies � start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 � BLOCKS all user story phases
- **US1 (Phase 3)**: Depends on Phase 2 (needs `image_utils.py`) � independent of US2/US3
- **US2 (Phase 4)**: Depends on Phase 2 (needs `THUMBNAIL_ALIASES`) � independent of US1/US3
- **US3 (Phase 5)**: Depends on Phase 3 being complete (needs all four forms updated)
- **Polish (Phase 6)**: Depends on all user story phases

### Within Each Phase

- Tests MUST be written and confirmed FAILING before implementation tasks
- T013�T016 (form updates) are all parallel � different files, no shared state
- T022�T023 (template updates) are parallel � different files

---

## Parallel Example: User Story 1

```bash
# After T009�T012 tests are written and confirmed red:
# T013, T014, T015, T016 can all run in parallel (four different form files)
```

## Parallel Example: User Story 2

```bash
# After T019�T020 tests are written and confirmed red:
# T021, T022, T023 can all run in parallel (static file + two template files)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: US1 (form guidance + validation)
4. **STOP and VALIDATE**: All four forms show 3:2 guidance and reject 6 MB uploads
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational ? base is ready
2. US1 ? forms are consistent and informative (MVP)
3. US2 ? card listings use thumbnails, no full-res images in lists
4. US3 ? consistency is verified by tests
5. Polish ? admin widget and code clarity

### Total Task Count

| Phase | Tasks | Parallel opportunities |
|-------|-------|----------------------|
| Phase 1: Setup | 3 | � |
| Phase 2: Foundational | 5 | � |
| Phase 3: US1 | 12 | T009–T012, T013–T016, T034–T035 |
| Phase 4: US2 | 8 | T019–T020, T021–T023, T036 |
| Phase 5: US3 | 4 | T026 |
| Phase 6: Polish | 4 | T030�T031 |
| **Total** | **36** | |
