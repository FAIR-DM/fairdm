# Feature Specification: Project CRUD Views

**Feature Branch**: `013-project-crud-views`  
**Created**: 2026-05-11  
**Status**: Refined  
**Refined**: 2026-05-11 — `ProjectForm` is the full form (all fields, widgets, help_texts, validation) used directly by the update view. `ProjectCreateForm` inherits from it, restricts `Meta.fields` to the three creation fields, overrides the `visibility` widget to `RadioSelect`. `ProjectUpdateForm` is removed.  
**Refined**: 2026-05-11 — `status` and `visibility` fields in `ProjectForm` MUST use `TypedChoiceField` with `coerce=int` instead of `ChoiceField`. This eliminates the need for manual string-to-integer conversion in `clean()`.  
**Refined**: 2026-05-11 — ~~Concept-private validation rule removed.~~ Concept projects MAY be made public; this is actively encouraged to promote community engagement. `ProjectForm.clean()` no longer enforces any status/visibility cross-field rule. `ProjectCreateForm.clean()` override is also removed — it no longer needs to bypass a rule that no longer exists.  
**Input**: User description: "CRUD views for the Project model — list, create, update, and delete — wired to URL patterns, with appropriate forms and filter class."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Browse and Search the Project List (Priority: P1)

A visitor or authenticated user navigates to the project listing page to discover publicly visible projects. They can type a keyword into the search box, apply filters (status, owner, contributor, tag), and sort results by project title or creation date.

**Why this priority**: Without a working list page there is no entry point into the project area. It is the foundation all other views build on.

**Independent Test**: Can be fully tested by visiting the list URL as an anonymous user and verifying that public projects appear, search by name returns matching results, and ordering controls change the result sequence.

**Acceptance Scenarios**:

1. **Given** the list URL is visited, **When** the page loads, **Then** only publicly visible projects are shown.
2. **Given** projects exist with matching names, **When** a search term is submitted, **Then** only matching projects appear.
3. **Given** multiple projects exist, **When** the user sorts by project title, **Then** results are returned in alphabetical order.
4. **Given** multiple projects exist, **When** the user sorts by creation date, **Then** results are returned in chronological order.
5. **Given** filter options are available, **When** a status filter is applied, **Then** only projects with that status are shown.
6. **Given** no projects match the current search/filter, **When** the list renders, **Then** an empty-state message is displayed.

---

### User Story 2 - Create a New Project (Priority: P1)

An authenticated user submits a minimal creation form — providing at minimum a project name, a lifecycle status, and a visibility setting — and the system creates the project record, assigns the creator full management permissions, and records them as a contributor with appropriate roles.

**Why this priority**: Project creation is the first action a researcher takes; it is a prerequisite for all data-entry workflows.

**Independent Test**: Can be fully tested by submitting the creation form as an authenticated user and verifying the project record is persisted, permissions are assigned, and the user is recorded as a contributor.

**Acceptance Scenarios**:

1. **Given** the user is authenticated, **When** a valid creation form is submitted, **Then** the project is saved and the user is redirected to the project detail page (`project-detail`).
2. **Given** the creation form is submitted without a project name, **When** the form is validated, **Then** an error is shown and no project is created.
3. **Given** a project is successfully created, **When** the creator's permissions are checked, **Then** they hold view, change, delete, change_metadata, and change_settings permissions on that project.
4. **Given** a project is successfully created, **When** the contributor list is checked, **Then** the creator appears with Creator, ProjectMember, and ContactPerson roles.
5. **Given** the user is not authenticated, **When** the create URL is accessed, **Then** the user is redirected to the login page.

---

### User Story 3 - Edit Project Core Attributes (Priority: P2)

An authenticated user with change permission on a project navigates to its edit page and updates one or more of the direct model fields: name, image, lifecycle status, visibility, owner organisation, or funding information. Related metadata (descriptions, dates, contributor records) is not editable here.

**Why this priority**: Researchers need to correct or extend basic project attributes after initial creation; this is the primary self-service editing surface.

**Independent Test**: Can be fully tested by submitting the edit form as a permitted user and verifying the changed fields are persisted while fields out of scope (descriptions, dates, contributor entries) cannot be submitted through this form.

**Acceptance Scenarios**:

1. **Given** the user has change permission, **When** a valid edit form is submitted, **Then** the updated field values are persisted on the project.
2. **Given** the user lacks change permission, **When** the edit URL is accessed, **Then** a permission-denied response is returned.
3. **Given** the edit form is submitted with an empty project name, **When** the form is validated, **Then** an error is returned and the project is not saved.
4. **Given** the edit form is rendered, **Then** no fields relating to descriptions, dates, or contributor records are present in the form.

---

### User Story 4 - Delete a Project (Priority: P3)

An authenticated user with delete permission confirms they want to remove a project by typing its exact name. The system validates that no publicly available datasets are linked to the project before carrying out the deletion.

**Why this priority**: Deletion is a destructive, infrequent operation; it is lower priority than creation and editing but must be correctly guarded.

**Independent Test**: Can be fully tested by attempting deletion of a project with and without public datasets, and by submitting the confirmation form with both a correct and an incorrect project name.

**Acceptance Scenarios**:

1. **Given** the project has no publicly available datasets, **When** the user types the correct project name and confirms, **Then** the project is deleted and the user is redirected.

- **Given** the project has one or more publicly available datasets, **When** the user attempts deletion, **Then** the deletion is blocked, the confirmation page is re-rendered, and the specific public datasets blocking the deletion are listed by name.

1. **Given** the delete confirmation form is shown, **When** the user types an incorrect project name, **Then** an error is shown and the project is not deleted.
2. **Given** the user lacks delete permission, **When** the delete URL is accessed, **Then** a permission-denied response is returned.

---

### Edge Cases

- What happens when the search term matches a project UUID but not its name? The UUID field is included in `search_fields`, so it should be found.
- What happens when the user submits the delete form with leading or trailing whitespace around the project name? The confirmation check should strip whitespace before comparing.
- What happens when a public dataset is added to a project between the user loading the delete confirmation page and submitting the form? The model-level guard fires on the POST, so the deletion is still blocked and the updated list of blocking datasets is shown.
- What happens when `ProjectFilter` is applied with an owner that has no public projects? The list renders empty with an empty-state message.
- ~~What happens when the creation form is submitted with a `visibility` value of PUBLIC but the project status is CONCEPT?~~ The concept-private rule has been removed (2026-05-11). Concept projects may be made public and this is encouraged to promote community engagement. There is no cross-field validation between `status` and `visibility`.

## Requirements *(mandatory)*

### Functional Requirements

#### List View (`project-list`)

- **FR-001**: The list view MUST inherit from `fairdm.views.base.FairDMListView`.
- **FR-002**: The list view MUST be accessible at a URL named `project-list`.
- **FR-003**: The list view MUST restrict the displayed queryset to publicly visible projects only.
- **FR-004**: The list view MUST declare `search_fields` covering at minimum the project UUID and project name.
- **FR-005**: The list view MUST attach `ProjectFilter` as its `filterset_class`.
- **FR-006**: The list view MUST support ordering by project title (ascending and descending) and by creation date (ascending and descending).
- **FR-007**: A minimal placeholder list-item template MUST exist so the view renders without error; its visual design is deferred to a future spec.

#### Create View (`project-create`)

- **FR-008**: The create view MUST inherit from `fairdm.views.base.FairDMCreateView`.
- **FR-009**: The create view MUST be accessible at a URL named `project-create`.
- **FR-010**: The create view MUST require authentication; unauthenticated requests MUST be redirected to the login page.
- **FR-011**: The create view MUST use `ProjectCreateForm`, which MUST include only the fields `name`, `status`, and `visibility`. `ProjectCreateForm` MUST inherit from `ProjectForm` (see FR-028), override `Meta.fields` to restrict the field set, and override the `visibility` field with a `TypedChoiceField` using a `RadioSelect` widget and `coerce=int`. ~~`ProjectCreateForm` MUST NOT override `clean()` to bypass the concept-private rule~~ — that rule no longer exists; no `clean()` override is required on `ProjectCreateForm`.
- **FR-012**: On successful submission the system MUST assign the creating user the permissions: `view_project`, `change_project`, `delete_project`, `change_project_metadata`, and `change_project_settings` on the newly created project.
- **FR-013**: On successful submission the creating user MUST be recorded as a contributor with the roles: Creator, ProjectMember, and ContactPerson.
- **FR-013a**: On successful submission the create view MUST redirect to the project detail page (`project-detail`) using the new project's `uuid`.

#### Update View (`project-update`)

- **FR-014**: The update view MUST inherit from `fairdm.views.base.FairDMUpdateView`.
- **FR-015**: The update view MUST be accessible at a URL named `project-update`, parameterised by the project's `uuid`.
- **FR-016**: The update view MUST require authentication; unauthenticated requests MUST be redirected to the login page.
- **FR-017**: The update view MUST check that the requesting user holds the `change_project` object-level permission; if not, a permission-denied response MUST be returned.
- **FR-018**: The update view MUST use `ProjectForm` directly, covering all direct model fields: `name`, `image`, `status`, `visibility`, `owner`, and `funding`. Related fields (descriptions, dates, contributor records, keywords, tags) MUST NOT appear in this form.
- **FR-018a**: On successful submission the update view MUST redirect to the project detail page (`project-detail`) using the project's `uuid`.

#### Delete View (`project-delete`)

- **FR-019**: The delete view MUST inherit from `fairdm.views.base.FairDMDeleteView`.
- **FR-020**: The delete view MUST be accessible at a URL named `project-delete`, parameterised by the project's `uuid`.
- **FR-021**: The delete view MUST require authentication; unauthenticated requests MUST be redirected to the login page.
- **FR-022**: The delete view MUST check that the requesting user holds the `delete_project` object-level permission; if not, a permission-denied response MUST be returned.
- **FR-023**: The `Project` model MUST enforce a guard at the model level (e.g. via a `pre_delete` signal or override of `delete()`) that raises an exception when the project has one or more publicly visible datasets. The delete view MUST catch this exception inside a `form_valid()` override and re-render the confirmation page with an explanatory message that lists the specific blocking public datasets by name. The guard is integrated into the standard `MVPDeleteView` form flow — the view MUST NOT override `post()` to implement this check.
- **FR-024**: The delete view MUST set `require_confirmation = True` (the `MVPDeleteView` class attribute) and override `get_confirmation_value()` to return the project name. The platform's `DeleteConfirmForm` then validates that the user's typed value matches the project name (whitespace-trimmed); if it does not match, a form validation error is returned and the project is not deleted.
- **FR-024a**: On successful deletion the delete view MUST redirect to the project list page (`project-list`). A future spec will introduce a per-user project list and update this redirect target accordingly.

#### Form Base Class

- **FR-028**: `ProjectForm` MUST be the single base form class in `fairdm/core/project/forms.py`, inheriting from `ModelForm`. It MUST centralise all field declarations, `help_texts`, `widgets`, and `__init__` setup (owner queryset, conditional on field presence). `Meta.fields` MUST list all directly editable Project fields: `["image", "name", "status", "visibility", "owner", "funding"]`. The `status` and `visibility` fields MUST be declared as `TypedChoiceField` with `coerce=int` (not plain `ChoiceField`), so that submitted values are automatically coerced to integers; `clean()` MUST NOT manually convert these values from string to integer. ~~`ProjectForm.clean()` MUST enforce the concept-private rule~~ — that rule is removed; `ProjectForm` requires no cross-field `clean()` logic and MUST NOT define one solely for that purpose. `ProjectCreateForm` MUST inherit from `ProjectForm` and: (1) restrict `Meta(ProjectForm.Meta).fields` to `["name", "status", "visibility"]`; (2) override the `visibility` field with a `TypedChoiceField` using a `RadioSelect` widget and `coerce=int`. ~~(3) override `clean()` to bypass the concept-private rule~~ — no `clean()` override is needed. No separate `ProjectUpdateForm` class exists — `ProjectForm` serves as the update form.

**Bugfix**: 2026-05-11 — BUG-001 FR-023 and FR-024 clarified: delete view MUST use `require_confirmation = True` and `form_valid()` override, not a custom `post()`. Removed ambiguity about which mechanism enforces the name check.

#### URL Wiring

- **FR-025**: All four URL patterns MUST follow the `<model_name>-<action_name>` naming convention: `project-list`, `project-create`, `project-update`, `project-delete`.
- **FR-026**: The update and delete URL patterns MUST capture the project `uuid` as a path parameter.
- **FR-027**: The detail view (`project-detail`) is explicitly out of scope and MUST NOT be modified by this feature.

### Key Entities

- **Project**: The central entity. Direct model fields: `uuid` (auto-generated), `name`, `image`, `visibility`, `status`, `funding`, `owner`. Related data (descriptions, dates, contributors, keywords, tags) is managed through separate, dedicated interfaces outside the scope of this feature.
- **ProjectFilter**: An existing `django_filters.FilterSet` subclass that provides filtering by status, owner, tag, and contributor. Referenced by the list view; its internal implementation is outside this feature's scope.
- **Project (model-level guard)**: The `Project` model raises an exception when deletion is attempted while publicly visible datasets exist. The delete view is responsible for catching this exception and presenting the list of blocking datasets to the user.
- **ProjectForm**: The full `ModelForm` for Project — all field declarations, `help_texts`, `widgets`, and owner-queryset setup. `Meta.fields = ["image", "name", "status", "visibility", "owner", "funding"]`. `status` and `visibility` use `TypedChoiceField(coerce=int)`. No cross-field `clean()` validation. Used directly by the update view.
- **ProjectCreateForm**: Inherits from `ProjectForm`; restricts `Meta.fields` to `["name", "status", "visibility"]` and overrides the `visibility` field with a `TypedChoiceField` using `RadioSelect` and `coerce=int`. No `clean()` override. Used exclusively by the create view.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All four URLs (`project-list`, `project-create`, `project-update`, `project-delete`) resolve without error when visited by a user with appropriate access.
- **SC-002**: The list view returns only publicly visible projects; no private projects appear for any user.
- **SC-003**: A project with at least one public dataset cannot be deleted via the delete view; the attempt is blocked 100% of the time, and the blocking datasets are listed by name on the confirmation page.
- **SC-004**: A user who enters an incorrect project name during deletion confirmation is never able to proceed with the deletion.
- **SC-005**: All view classes use the correct FairDM base class; no view inherits directly from Django's generic views or from MVPCreateView/MVPUpdateView/MVPDeleteView without going through the FairDM layer.
- **SC-006**: Unauthenticated requests to the create, update, and delete views are redirected to the login page in every case.

## Clarifications

### Session 2026-05-11

- Q: Should this feature update the existing view classes in place, or replace/parallel them? → A: Update existing classes in place — migrate base classes, adjust form references, add missing permission checks.
- Q: Where is the public-dataset guard for deletion enforced, and how is it surfaced? → A: Guard is enforced at the model level (raises an exception on attempted deletion); the delete view catches that exception and renders a message listing the specific public datasets that are blocking deletion, mirroring the pattern used by MVPDeleteView for DB-level ProtectedError.
- Q: Where does the create view redirect after successful submission? → A: To the project detail page (`project-detail`).
- Q: Where does the update view redirect after successful submission? → A: To the project detail page (`project-detail`).
- Q: Where does the delete view redirect after successful deletion? → A: To the project list page (`project-list`) for now; a future spec will redirect to the user's own project list once that view is implemented.

## Assumptions

- The `ProjectFilter` class already exists in `fairdm.core.project.filters` and requires no new filtering fields for this spec.
- The existing view classes in `fairdm/core/project/views.py` will be updated in place: base classes migrated to the FairDM layer, form references adjusted, and missing permission checks added. No parallel or replacement module will be created.
- "Publicly available datasets" means datasets linked to the project whose `visibility` field equals `PUBLIC`; the definition of visibility values is already established in the codebase.
- The `created_at` / `add_date` timestamp used for ordering by creation date is provided by an inherited model field (Django's auto-generated `id` order serves as a proxy if no explicit timestamp field exists; the exact field name will be confirmed during planning).
- The `uuid` field on `Project` is the URL slug; all parameterised URL patterns use `<str:uuid>`.
- Template content and visual layout for all four views are out of scope; a placeholder list-item template must exist but need not contain meaningful markup.
- The detail view and its URL pattern (`project-detail`) are out of scope and must not be touched.
- Object-level permission checks use `django-guardian`; the permission model is already set up in the project.
- `ProjectForm` is the single form class for update and the base for create. It defines all fields, widgets, help_texts, and validation. `ProjectCreateForm` inherits it and restricts `Meta.fields`. No `ProjectUpdateForm` class exists.
