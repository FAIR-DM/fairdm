# Feature Specification: FairDM Base Views — Documentation & Testing

**Feature Branch**: `012-base-views-docs`  
**Created**: 2026-05-11  
**Status**: Draft  
**Input**: User description: "A core set of basic views are essential to provide a consistent entrypoint for developers wishing to integrate functionality into the fairdm framework within the constraints of a consistent framework api and UI. fairdm.views.base already provides 7 basic architectural views that extend the base views from django-mvp and provide functionality for additional metadata context via django-meta. The role of this spec is to test and document these base views."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Developer reads inline docstrings (Priority: P1)

A developer exploring the FairDM codebase opens `fairdm/views/base.py` and wants to understand what each view class does, when to use it, and which class attributes they can configure — without leaving their editor or opening a browser to read external docs.

**Why this priority**: Inline docstrings are the lowest-friction source of truth. Every developer who subclasses a view will encounter them first. Accurate, complete docstrings directly reduce onboarding time and misuse.

**Independent Test**: Can be validated by reading `fairdm/views/base.py` alone and checking that each class has a docstring that (a) explains purpose/use-case and (b) lists key configurable attributes.

**Acceptance Scenarios**:

1. **Given** a developer opens `fairdm/views/base.py`, **When** they read the docstring for any of the 7 view classes, **Then** they can determine in under 30 seconds what the view is for and what attributes they can set.
2. **Given** a developer wants to display a paginated list of objects, **When** they scan the docstrings, **Then** they can immediately identify `FairDMListView` as the correct base class and learn about `paginate_by` and `grid` attributes.
3. **Given** a developer wants to create a new object with SEO metadata, **When** they read `FairDMCreateView`'s docstring, **Then** they understand that `MetadataMixin` is already composed in and can use it directly without additional configuration.

---

### User Story 2 - Developer reads contributing docs for architectural context (Priority: P2)

A developer new to FairDM wants to understand why the framework has its own view layer rather than using plain Django views or django-mvp views directly. They navigate to `docs/contributing/` to find an explanation of the view hierarchy, the role of each base class, and practical guidance on when to use each.

**Why this priority**: Inline docstrings describe the *what*; contributing docs explain the *why*. This context prevents developers from bypassing the framework layer and writing inconsistent views.

**Independent Test**: A new contributor reads only the view documentation page in `docs/contributing/` and can answer: (a) why FairDM provides its own view layer, (b) what django-meta's `MetadataMixin` adds, (c) which view to subclass for each CRUD operation.

**Acceptance Scenarios**:

1. **Given** a developer opens the contributing docs, **When** they read the base views section, **Then** they find an explanation of the three-layer hierarchy (Django → django-mvp → FairDM).
2. **Given** a developer reads the contributing docs, **When** they want to build a table-style list view, **Then** the docs explain when to use `FairDMTableView` vs `FairDMListView` and what the difference is.
3. **Given** a developer reads the contributing docs, **When** they are unsure which view to subclass, **Then** there is a quick-reference table or decision guide mapping CRUD operations to view classes.

---

### User Story 3 - CI catches regressions in view behaviour (Priority: P3)

A contributor modifies `fairdm/views/base.py` and submits a pull request. The test suite runs and confirms that all 7 view classes still render correctly, respond with expected status codes, inject expected context keys, and compose `MetadataMixin` correctly.

**Why this priority**: Without tests, documentation can drift from actual behaviour. Tests anchor the specification to real runtime behaviour.

**Independent Test**: A `pytest` run against the views test module produces a green suite, exercising at least one happy-path scenario per view class.

**Acceptance Scenarios**:

1. **Given** the test suite runs, **When** each view class is exercised with a minimal configuration, **Then** all views return HTTP 200 and do not raise errors.
2. **Given** `FairDMListView`, **When** rendered, **Then** context contains a `grid_config` key (exact default value is not asserted; key presence is sufficient).
3. **Given** any FairDM view, **When** rendered with a model that provides `Meta` properties, **Then** `MetadataMixin` context keys (e.g. `meta`) are present in the response context.

---

### Edge Cases

- What does `FairDMTableView` require beyond `model` — does the template need to be provided explicitly?
- How does `FairDMListView.grid` interact with `MVPListViewMixin.grid` when both are set?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each of the 7 view classes in `fairdm/views/base.py` MUST have a docstring that describes the class purpose and when a developer should use it over alternatives.
- **FR-002**: Each docstring MUST follow the django-mvp docstring style, using `Config:`, `Override hooks:`, `Context:`, and `Example::` sections where applicable — mirroring the conventions used in the parent view classes in django-mvp.
- **FR-003**: `FairDMTemplateView`, `FairDMDetailView`, `FairDMUpdateView`, and `FairDMDeleteView` currently have no docstring or minimal content; these MUST be completed.
- **FR-004**: `FairDMCreateView`'s docstring MUST describe its purpose as a thin composition of `MetadataMixin` + `MVPCreateView` and note that it provides no additional attributes beyond its parents.
- **FR-005**: `FairDMListView`'s docstring MUST document `paginate_by` and `grid` attributes and explain the filtered list behaviour inherited from `MVPFilteredListView`.
- **FR-006**: `FairDMTableView`'s docstring MUST explain the difference from `FairDMListView` and describe what template responsibilities the developer takes on.
- **FR-007**: A documentation page MUST be created at `docs/contributing/base-views.md` covering: the three-layer view hierarchy, the role of `django-meta`'s `MetadataMixin`, a summary of each view class, a quick-reference table mapping CRUD operations to view classes, and code examples for each view.
- **FR-008**: The contributing docs index (`docs/contributing/index.md`) MUST include a link to the new base views page.
- **FR-009**: Tests MUST be written for all 7 view classes as integration tests using `RequestFactory` or the Django test client, covering at minimum: HTTP status code, presence of expected context keys, and correct template resolution.
- **FR-010**: The test for `FairDMCreateView` MUST verify a successful POST creates the object, returns the expected redirect, and that `MetadataMixin` context keys are present.

### Key Entities

- **FairDMTemplateView**: Combines `MetadataMixin` + `MVPTemplateView`; used for static or lightly dynamic pages with SEO metadata support.
- **FairDMListView**: Combines `MetadataMixin` + `MVPFilteredListView`; adds `paginate_by = 25` and `grid` config; used for filtered, paginated lists.
- **FairDMDetailView**: Combines `MetadataMixin` + `MVPDetailView`; used for object detail pages.
- **FairDMCreateView**: Combines `MetadataMixin` + `MVPCreateView`; a thin wrapper that brings SEO metadata support to object creation pages.
- **FairDMUpdateView**: Combines `MetadataMixin` + `MVPUpdateView`; used for object edit pages.
- **FairDMDeleteView**: Combines `MetadataMixin` + `MVPDeleteView`; used for object deletion confirmation pages.
- **FairDMTableView**: Combines `MetadataMixin` + `MVPTableViewMixin` + `FilterView`; used for tabular data displays with filtering.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 7 view classes have complete, accurate docstrings; a reviewer unfamiliar with the codebase can determine the purpose and key attributes of any class within 30 seconds of reading its docstring.
- **SC-002**: The contributing documentation page covers all 7 view classes and includes at least one code example per class.
- **SC-003**: The test suite includes at least one test per view class and achieves 100% line coverage of `fairdm/views/base.py`. Context key assertions check for key *presence* only — not specific default values — to keep tests resilient to config changes.
- **SC-004**: All existing tests continue to pass after the docstring and test additions (no regressions).
- **SC-005**: The contributing docs page is discoverable from the contributing index with a single click.

## Clarifications

### Session 2026-05-11

- Q: Should FairDM view docstrings follow django-mvp's docstring style (`Config:`, `Override hooks:`, `Context:`, `Example::`) or a different format? → A: Mirror django-mvp style — `Config:`, `Override hooks:`, `Context:`, `Example::` sections
- Q: Should tests be unit tests (FairDM-specific additions only) or integration tests (full request/response cycle)? → A: Integration tests — use `RequestFactory`/test client to exercise the full request/response cycle for each view
- Q: Should the contributing docs page be a standalone top-level file or live in a subdirectory? → A: Single top-level file — `docs/contributing/base-views.md`
- Q: Should the `default_roles` / `add_contributor` guard in `FairDMCreateView` be explicitly tested? → A: Functionality removed from `FairDMCreateView`; no test needed
- Q: Should tests assert the exact default value of `FairDMListView.grid` or only that `grid_config` exists in context? → A: Assert key existence only (`"grid_config" in response.context`)

## Assumptions

- The 7 view classes in `fairdm/views/base.py` are the complete and stable set; no new views will be added as part of this feature.
- `django-meta`'s `MetadataMixin` is already a project dependency and its attributes (`title`, `description`, `keywords`, `image`) are the primary SEO surface exposed by all FairDM views.
- Tests will use `pytest` with `pytest-django`, consistent with the project's existing test suite.
- The contributing documentation uses MyST Markdown and is built with Sphinx, consistent with existing `docs/contributing/` pages.
- `FairDMTableView` requires a `table_class` attribute and a template that renders the table; this is not changing as part of this feature — only documenting the requirement.
- `FairDMCreateView` has no additional attributes beyond its parent classes; its docstring needs only describe the composition and use-case.
- No behaviour changes to the view classes themselves are in scope; this feature is documentation and testing only.
