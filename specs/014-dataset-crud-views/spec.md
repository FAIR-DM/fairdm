# Feature Specification: Dataset CRUD Views

**Feature Branch**: `014-dataset-crud-views`  
**Created**: 2026-05-12  
**Status**: Refined  
**Input**: User description: "CRUD views for the Dataset model — list, create, update, and delete — wired to URL patterns, with appropriate forms and filter class. DatasetForm is the full form (all fields, widgets, help_texts, validation) used directly by the update view. DatasetCreateForm inherits from it, restricts Meta.fields to necessary fields for creation only."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Browse and Search the Dataset List (Priority: P1)

A visitor or authenticated user navigates to the dataset listing page to discover publicly visible datasets. They can type a keyword into the search box, apply filters (license, project, visibility), and sort results by name or date added.

**Why this priority**: Without a working list page there is no entry point into the dataset area. It is the foundation all other views build on.

**Independent Test**: Can be fully tested by visiting the list URL as an anonymous user and verifying that public datasets appear, search by name returns matching results, and ordering controls change the result sequence.

**Acceptance Scenarios**:

1. **Given** the list URL is visited, **When** the page loads, **Then** only publicly visible datasets are shown.
2. **Given** datasets exist with matching names, **When** a search term is submitted, **Then** only matching datasets appear.
3. **Given** multiple datasets exist, **When** the user sorts by name, **Then** results are returned in alphabetical order.
4. **Given** multiple datasets exist, **When** the user sorts by date added, **Then** results are returned in chronological order.
5. **Given** filter options are available, **When** a license filter is applied, **Then** only datasets with that license are shown.
6. **Given** no datasets match the current search/filter, **When** the list renders, **Then** an empty-state message is displayed.

---

### User Story 2 - Create a New Dataset (Priority: P1)

An authenticated user submits a minimal creation form — providing at minimum a dataset name; the associated project is shown on the form but may be left blank — and the system creates the dataset record, assigns the creator full management permissions, and records them as a contributor with appropriate roles.

**Why this priority**: Dataset creation is the first action a researcher takes after establishing a project; it is a prerequisite for all data-entry workflows.

**Independent Test**: Can be fully tested by submitting the creation form as an authenticated user and verifying the dataset record is persisted, permissions are assigned, and the user is recorded as a contributor.

**Acceptance Scenarios**:

1. **Given** the user is authenticated, **When** a valid creation form is submitted, **Then** the dataset is saved and the user is redirected to the dataset detail page (`dataset-detail`).
2. **Given** the creation form is submitted without a dataset name, **When** the form is validated, **Then** an error is shown and no dataset is created.
3. **Given** a dataset is successfully created, **When** the creator's permissions are checked, **Then** they hold view, change, delete, change_metadata, and change_settings permissions on that dataset.
4. **Given** a dataset is successfully created, **When** the contributor list is checked, **Then** the creator appears with Creator, ProjectMember, and ContactPerson roles.
5. **Given** the user is not authenticated, **When** the create URL is accessed, **Then** the user is redirected to the login page.

---

### User Story 3 - Edit Dataset Core Attributes (Priority: P2)

An authenticated user with change permission on a dataset navigates to its edit page and updates one or more of the editable model fields: name, image, associated project, license, linked publication reference, or DOI. Related metadata (descriptions, dates, contributor records, samples) is not editable here.

**Why this priority**: Researchers need to correct or extend basic dataset attributes after initial creation; this is the primary self-service editing surface.

**Independent Test**: Can be fully tested by submitting the edit form as a permitted user and verifying the changed fields are persisted while fields out of scope (descriptions, dates, contributor entries) cannot be submitted through this form.

**Acceptance Scenarios**:

1. **Given** the user has change permission, **When** a valid edit form is submitted, **Then** the updated field values are persisted on the dataset.
2. **Given** the user lacks change permission, **When** the edit URL is accessed, **Then** a permission-denied response is returned.
3. **Given** the edit form is submitted with an empty dataset name, **When** the form is validated, **Then** an error is returned and the dataset is not saved.
4. **Given** the edit form is rendered, **Then** no fields relating to descriptions, dates, contributor records, or sample entries are present in the form.

---

### User Story 4 - Delete a Dataset (Priority: P3)

An authenticated user with delete permission confirms they want to remove a dataset by typing its exact name. The system validates the confirmation before carrying out the deletion.

**Why this priority**: Deletion is a destructive, infrequent operation; it is lower priority than creation and editing but must be correctly guarded.

**Independent Test**: Can be fully tested by attempting deletion of a dataset and submitting the confirmation form with both a correct and an incorrect dataset name.

**Acceptance Scenarios**:

1. **Given** the user types the correct dataset name and confirms, **When** the form is submitted, **Then** the dataset is deleted and the user is redirected to the dataset list page (`dataset-list`).
2. **Given** the delete confirmation form is shown, **When** the user types an incorrect dataset name, **Then** an error is shown and the dataset is not deleted.
3. **Given** the user lacks delete permission, **When** the delete URL is accessed, **Then** a permission-denied response is returned.

---

### Edge Cases

- What happens when the search term matches a dataset UUID but not its name? The UUID field is included in `search_fields`, so it should be found.
- What happens when the user submits the delete form with leading or trailing whitespace around the dataset name? The confirmation check should strip whitespace before comparing.
- What happens when `DatasetFilter` is applied with a project that has no public datasets? The list renders empty with an empty-state message.
- What happens when a DOI is submitted with an incorrect format in the update form? Form validation should reject it and display a format error before saving.

## Requirements *(mandatory)*

### Functional Requirements

#### List View (`dataset-list`)

- **FR-001**: The list view MUST inherit from `fairdm.views.base.FairDMListView`.
- **FR-002**: The list view MUST be accessible at a URL named `dataset-list`.
- **FR-003**: The list view MUST restrict the displayed queryset to publicly visible datasets only (via `.get_visible()`).
- **FR-004**: The list view MUST declare `search_fields` covering at minimum the dataset UUID, dataset name, and dataset description values.
- **FR-005**: The list view MUST attach `DatasetFilter` as its `filterset_class`.
- **FR-006**: The list view MUST support ordering by dataset name (ascending and descending) and by date added (ascending and descending).
- **FR-007**: A minimal placeholder card template MUST exist so the view renders without error; its visual design is deferred to a future spec.

#### Create View (`dataset-create`)

- **FR-008**: The create view MUST inherit from `fairdm.views.base.FairDMCreateView`.
- **FR-009**: The create view MUST be accessible at a URL named `dataset-create`.
- **FR-009a**: The create view MUST NOT pre-populate any form field from query parameters. The existing `get_initial()` override that reads a `?project=` query param MUST be removed. Pre-population via query param is deferred to a future spec.
- **FR-010**: The create view MUST require authentication; unauthenticated requests MUST be redirected to the login page.
- **FR-011**: The create view MUST use `DatasetCreateForm`, which MUST include only the fields `name`, `project`, and `license`. `DatasetCreateForm` MUST inherit from `DatasetForm` (see FR-028) and override `Meta.fields` to restrict the field set to those three fields. The `project` field MUST remain optional (`required=False`); a dataset may be created without being assigned to a project.
- **FR-012**: On successful submission the system MUST assign the creating user the permissions: `view_dataset`, `change_dataset`, `delete_dataset`, `change_dataset_metadata`, and `change_dataset_settings` on the newly created dataset.
- **FR-013**: On successful submission the creating user MUST be recorded as a contributor with the roles: Creator, ProjectMember, and ContactPerson.
- **FR-013a**: On successful submission the create view MUST redirect to the dataset detail page (`dataset-detail`) using the new dataset's `uuid`.

#### Update View (`dataset-update`)

- **FR-014**: The update view MUST inherit from `fairdm.views.base.FairDMUpdateView`.
- **FR-015**: The update view MUST be accessible at a URL named `dataset-update`, parameterised by the dataset's `uuid`.
- **FR-016**: The update view MUST require authentication; unauthenticated requests MUST be redirected to the login page.
- **FR-017**: The update view MUST check that the requesting user holds the `change_dataset` object-level permission; if not, a permission-denied response MUST be returned.
- **FR-017a**: The update view MUST override `get_form_kwargs()` to pass `request` to `DatasetForm`, ensuring the `project` field queryset is filtered to projects accessible to the authenticated user (matching the security behaviour of the create view).
- **FR-018**: The update view MUST use `DatasetForm` directly, covering all directly editable model fields: `name`, `image`, `project`, `license`, `reference`, and `doi`. The `visibility` field MUST NOT appear in this form — visibility is managed via a dedicated publish/unpublish workflow outside the scope of this feature. Related fields (descriptions, dates, contributor records, samples, keywords, tags) MUST NOT appear in this form.
- **FR-018a**: On successful submission the update view MUST redirect to the dataset detail page (`dataset-detail`) using the dataset's `uuid`.

#### Delete View (`dataset-delete`)

- **FR-019**: The delete view MUST inherit from `fairdm.views.base.FairDMDeleteView`.
- **FR-020**: The delete view MUST be accessible at a URL named `dataset-delete`, parameterised by the dataset's `uuid`.
- **FR-021**: The delete view MUST require authentication; unauthenticated requests MUST be redirected to the login page.
- **FR-022**: The delete view MUST check that the requesting user holds the `delete_dataset` object-level permission; if not, a permission-denied response MUST be returned.
- **FR-023**: The delete view MUST set `require_confirmation = True` (the `FairDMDeleteView` class attribute) and override `get_confirmation_value()` to return the dataset name. The platform's `DeleteConfirmForm` then validates that the user's typed value matches the dataset name (whitespace-trimmed); if it does not match, a form validation error is returned and the dataset is not deleted.
- **FR-023a**: On successful deletion the delete view MUST redirect to the dataset list page (`dataset-list`). A future spec will introduce a per-user dataset list and update this redirect target accordingly.

#### Form Base Class

- **FR-028**: `DatasetForm` MUST remain the single base form class in `fairdm/core/dataset/forms.py`, inheriting from `ModelForm`. It MUST centralise all field declarations, `help_texts`, `widgets`, and `__init__` setup (project queryset filtering by user permissions, license default, reference queryset, DOI pre-population). `Meta.fields` MUST list all directly editable Dataset fields: `["name", "image", "project", "license", "reference", "doi"]`. `DatasetForm` is used directly by the update view. `DatasetCreateForm` MUST inherit from `DatasetForm` and restrict `Meta(DatasetForm.Meta).fields` to `["name", "project", "license"]` — the three fields required for initial dataset creation.

#### URL Wiring

- **FR-029**: All four URL patterns MUST follow the `<model_name>-<action_name>` naming convention: `dataset-list`, `dataset-create`, `dataset-update`, `dataset-delete`.
- **FR-030**: The update and delete URL patterns MUST capture the dataset `uuid` as a path parameter.
- **FR-031**: The detail view (`dataset-detail`) is explicitly out of scope and MUST NOT be modified by this feature.

### Key Entities

- **Dataset**: The central entity. Directly editable fields via these CRUD views: `uuid` (auto-generated), `name`, `image`, `project`, `license`, `reference`, `doi` (via `DatasetIdentifier`). The `visibility` field is intentionally excluded — it is managed via a separate publish/unpublish workflow. Related data (descriptions, dates, contributors, samples, keywords, tags) is managed through separate, dedicated interfaces outside the scope of this feature.
- **DatasetFilter**: An existing `django_filters.FilterSet` subclass that provides filtering by license, project, visibility, and search. Referenced by the list view; its internal implementation is outside this feature's scope.
- **DatasetForm**: The full `ModelForm` for Dataset — all field declarations, `help_texts`, `widgets`, project-queryset filtering by user permissions, license default (CC BY 4.0), reference queryset, and DOI identifier handling. `Meta.fields = ["name", "image", "project", "license", "reference", "doi"]`. Used directly by the update view.
- **DatasetCreateForm**: Inherits from `DatasetForm`; restricts `Meta.fields` to `["name", "project", "license"]`. Used exclusively by the create view.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All four URLs (`dataset-list`, `dataset-create`, `dataset-update`, `dataset-delete`) resolve without error when visited by a user with appropriate access.
- **SC-002**: The list view returns only publicly visible datasets; no private datasets appear for any user.
- **SC-003**: A user who enters an incorrect dataset name during deletion confirmation is never able to proceed with the deletion.
- **SC-004**: All view classes use the correct FairDM base class; no view inherits directly from Django's generic views without going through the FairDM layer.
- **SC-005**: Unauthenticated requests to the create, update, and delete views are redirected to the login page in every case.
- **SC-006**: The create view uses `DatasetCreateForm` (restricting creation to name, project, and license); the update view uses `DatasetForm` (all editable fields).

## Assumptions

- The `DatasetFilter` class already exists in `fairdm.core.dataset.filters` and requires no new filtering fields for this spec.
- Both the create view and the update view MUST pass `request` to `DatasetForm` via `get_form_kwargs()` so the project queryset is filtered to the user's accessible projects. Anonymous users see no projects; authenticated users see only their accessible projects.
- The new `DatasetUpdateView` and `DatasetDeleteView` will be added to the existing `fairdm/core/dataset/views.py` module.
- The `uuid` field on `Dataset` is the URL slug; all parameterised URL patterns use `<str:uuid>`.
- Object-level permission checks use `django-guardian`; the permission model is already set up in the project.
- `DatasetForm` is the single form class for update and the base for create. It defines all fields, widgets, help_texts, and validation. `DatasetCreateForm` inherits it and restricts `Meta.fields` to `["name", "project", "license"]`. The `project` field is optional in both forms (`required=False`); a dataset does not require a project. The `visibility` field is excluded from both forms; it is managed via a separate publish/unpublish workflow in a future spec.
- Template content and visual layout for the update and delete views are out of scope; the existing `dataset_card.html` template serves the list view and requires no changes.
- The dataset detail view and its URL pattern (`dataset-detail`) are out of scope and must not be touched.
- The `added` timestamp on `Dataset` (auto-set on creation) is used for "date added" ordering in the list view.
- No model-level deletion guard is required for datasets at this stage; dataset deletion is protected solely by the name-confirmation mechanism and object-level permission check. A future spec may introduce a guard if datasets become tied to published, externally referenced records.

## Clarifications

### Session 2026-05-12

- Q: Should `visibility` be editable through `DatasetForm` / the update view, or managed via a separate publish/unpublish workflow? → A: `visibility` is intentionally excluded from `DatasetForm` and these CRUD views; it is managed via a dedicated publish/unpublish workflow in a future spec.
- Q: Should `project` be required in `DatasetCreateForm`? → A: Optional — `project` appears on the form but may be left blank. A Dataset does not require a Project.
- Q: Should the update and delete views use `django-guardian` object-level permissions or a simpler ownership check? → A: `django-guardian` object-level permissions (`change_dataset` / `delete_dataset`), matching the Project pattern.
- Q: Should the create view pre-populate the `project` field from a `?project=` query parameter? → A: No — remove this behaviour for now. Pre-population via query param will be reintroduced in a future spec when explicitly needed.
- Q: Should the update view pass `request` to `DatasetForm` via `get_form_kwargs()` to filter the project dropdown to the user's accessible projects? → A: Yes — both the create and update views MUST pass `request` to `DatasetForm` so the project queryset is filtered to projects accessible to the authenticated user.
