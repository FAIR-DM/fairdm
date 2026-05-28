# Feature Specification: Image Field Requirements for Core Models

**Feature Branch**: `015-image-field-spec`  
**Created**: 2026-05-28  
**Status**: Draft  
**Input**: User description: "Each of the core models in FairDM support an image field where the user can upload a representative image for their Project, Dataset, Sample or Measurement. This spec will solidify requirements regarding aspect-ratio, default size, thumbnail variations and form fields that convey expectations to the end user. We will be using a standard image field for uploading images so it is important users are aware of the details in order to avoid unwanted cropping in the application."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Upload Representative Image (Priority: P1)

A researcher creates or edits a Project (or Dataset, Sample, or Measurement) and uploads a representative image using the image field in the edit form. The form clearly communicates the recommended dimensions and aspect ratio before the user selects a file, helping them choose or crop an appropriate image upfront and avoid unexpected cropping in the application.

**Why this priority**: This is the core interaction. Without clear guidance at upload time, users will upload arbitrarily sized images and be surprised by how they are displayed across the portal.

**Independent Test**: Can be fully tested by navigating to any core model edit form, observing the image upload field, uploading a correctly-sized image, and verifying the image displays at the expected aspect ratio across all view contexts.

**Acceptance Scenarios**:

1. **Given** a user is editing a Project, **When** they view the image upload field, **Then** the field displays the recommended aspect ratio and minimum/recommended pixel dimensions as helper text.
2. **Given** a user uploads an image matching the recommended dimensions, **When** they save the record, **Then** the image is stored and displayed without any cropping or distortion.
3. **Given** a user uploads an image that does not match the recommended aspect ratio, **When** they save the record, **Then** the application warns the user that cropping may occur and shows a preview of the result.
4. **Given** a user uploads an oversized image file, **When** they submit the form, **Then** the system rejects the file with a clear message stating the maximum allowed file size.

---

### User Story 2 - View Thumbnails Across Portal Contexts (Priority: P2)

A portal visitor browses a listing of Projects or Datasets and sees representative thumbnail images displayed consistently in card or list views. The thumbnails are rendered at standardized sizes suited to their display context without distortion.

**Why this priority**: Consistent thumbnail presentation is the primary visual impact of this feature and drives the need for well-defined size variants.

**Independent Test**: Can be fully tested by viewing the Project listing page and confirming that all thumbnails render at a uniform size and aspect ratio, regardless of the original uploaded image dimensions.

**Acceptance Scenarios**:

1. **Given** a Project has an uploaded image, **When** it appears in a card/grid listing view, **Then** a small thumbnail variant is rendered at the defined small thumbnail dimensions.
2. **Given** a Project has an uploaded image, **When** it appears on the Project detail page header, **Then** a large thumbnail variant is rendered at the defined larger dimensions.
3. **Given** a record has no image uploaded, **When** it appears in any listing or detail view, **Then** a default placeholder image is displayed in place of the missing image.
4. **Given** thumbnails are generated, **When** the portal page loads, **Then** each size variant loads the appropriately sized image rather than downloading a full-resolution file.

---

### User Story 3 - Consistent Image Display Across All Core Model Types (Priority: P3)

All four core model types � Project, Dataset, Sample, and Measurement � use the same aspect ratio and thumbnail size conventions, so the portal presents a visually uniform appearance regardless of the record type being viewed.

**Why this priority**: Uniformity across model types reduces design and maintenance complexity and creates a coherent user experience.

**Independent Test**: Can be fully tested by uploading images to one instance each of a Project, Dataset, Sample, and Measurement and confirming thumbnail dimensions are identical across all four.

**Acceptance Scenarios**:

1. **Given** images uploaded to each of the four core model types, **When** they are displayed in comparable listing views, **Then** all thumbnails share the same aspect ratio and rendered dimensions.
2. **Given** the same image file uploaded to a Project and a Sample, **When** displayed side by side, **Then** the visual result (size, cropping behavior, placeholder) is identical.

---

### Edge Cases

- **[Resolved]** What happens when a user uploads a very small image (e.g., 50×50 pixels)? **Decision**: Small images are accepted and displayed as-is. `resize_source` only scales images *down* to fit within the 2400×1600 maximum; no upscaling is applied. The recommended minimum (1200×800 px) in the help text is advisory only; enforcing a minimum pixel size is out of scope for v1.
- What happens if a user uploads a non-image file (e.g., a PDF or text file) � the system must reject it with a clear file-type error message.
- What happens when a user uploads a very large file (e.g., 50 MB RAW photo) � the system must enforce a maximum file-size limit.
- **[Out of scope for v1]** What happens if image thumbnail generation fails? **Decision**: Templates must use conditional rendering (`{% if image %}`) to display the placeholder rather than calling `.url` on a potentially missing file. Automated test coverage for this failure path is deferred to v2; easy-thumbnails handles low-level processor errors internally.
- What happens when a user removes a previously uploaded image � the placeholder must reappear consistently across all views.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each core model (Project, Dataset, Sample, Measurement) MUST include a single optional image upload field on its create/edit form.
- **FR-002**: The image upload field MUST display helper text specifying the recommended aspect ratio (3:2) and minimum recommended pixel dimensions (1200×800 px) before the user selects a file.
- **FR-003**: The image upload field MUST display the maximum allowed file size in the helper text.
- **FR-004**: The system MUST reject uploaded files that are not valid image formats (JPEG, PNG, WebP), showing a clear error message identifying the disallowed format.
- **FR-005**: The system MUST reject uploaded files that exceed the defined maximum file size, showing the limit in the error message.
- **FR-006**: The system MUST generate at least two thumbnail size variants from every uploaded image: a **small** thumbnail for listing/card views and a **large** thumbnail for detail/header views.
- **FR-007**: All four core model types MUST use the same aspect ratio for their image fields (a single shared convention across the application).
- **FR-008**: When no image has been uploaded for a record, the system MUST display a consistent default placeholder image in all view contexts.
- **FR-009** *(Deferred — v2)*: When a user uploads an image whose aspect ratio does not match the recommended ratio, the form SHOULD display a warning and a visual preview of the cropped result before saving. For v1, the help text (FR-002) communicates that cropping may occur; dynamic JS ratio detection and live preview are out of scope.
- **FR-010**: When displaying thumbnails in listing or card views, the system MUST serve the small thumbnail variant � not the full-resolution image � to minimize data transfer.
- **FR-011**: The image upload field MUST display a preview of the currently saved image (or placeholder) when the form is rendered in edit mode.

### Key Entities

- **RepresentativeImage**: The uploaded image associated with a core model record. Attributes: original file, recommended aspect ratio, recommended minimum dimensions, maximum file size, storage reference.
- **Thumbnail Variant**: A resized derivative of the uploaded image. Attributes: size label (small, large), pixel dimensions, storage reference, aspect ratio (inherits shared convention).
- **Placeholder Image**: The default image displayed when no representative image has been uploaded. Attributes: shared across all four core model types, consistent dimensions per variant.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of image upload form fields across all four core model types display recommended dimensions and aspect ratio helper text before file selection.
- **SC-002**: Zero full-resolution images are served in listing or card view contexts � only the appropriate small thumbnail variant is loaded.
- **SC-003**: When a user uploads an image matching the recommended dimensions, the image is displayed without cropping or distortion in all view contexts.
- **SC-004**: Invalid file types and oversized files are rejected at the form level with an informative error message in 100% of cases.
- **SC-005**: All four core model types render images at a visually identical aspect ratio across equivalent view contexts (listing, detail), with no inconsistencies visible to users.
- **SC-006**: Records without an uploaded image display a placeholder image consistently across all listing and detail views, with zero broken image states.

## Assumptions

- All four core model types (Project, Dataset, Sample, Measurement) share the same aspect ratio � a single ratio applies uniformly across the application.
- The required aspect ratio is **3:2** — the standard landscape ratio produced by digital cameras and DSLRs. This applies uniformly across all four core model types and all thumbnail variants.
- Two thumbnail size variants are sufficient for v1: **small** (for listing/card grids) and **large** (for detail page headers).
- The recommended minimum upload dimensions align with the large thumbnail size so no upscaling is required when displaying the largest variant.
- A maximum file size of **5 MB** per upload is assumed as a reasonable default for a research data portal audience.
- Supported upload formats are JPEG, PNG, and WebP. GIF support is out of scope for v1.
- The placeholder image is a single shared asset used by all four core model types; per-model-type placeholders are out of scope for v1.
- Image cropping, when required due to aspect ratio mismatch, uses entropy-based smart cropping (`crop="smart"` via easy-thumbnails) rather than a fixed center crop. User-controlled crop positioning is out of scope for v1.
- Mobile responsiveness of image display follows existing portal responsive layout conventions; no new responsive behavior is specified here.
