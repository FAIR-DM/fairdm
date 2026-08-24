# Feature Specification: Managing a project through the portal

**Feature Branch**: `013-project-crud-views`

**Created**: 2026-05-11 · **Rewritten**: 2026-08-23

**Status**: Draft

**Goals**: G6 — core records can be created and edited by hand through the portal.

**Roadmap**: R12 — editing projects and datasets in the portal.

**Input**: A researcher who has a project to register needs to create it, describe it, correct it
and occasionally remove it, without an administrator and without the Django admin. This
specification covers every portal page through which a project record is managed: the public
listing, the creation form, the page for its own attributes, the page for its descriptions, the
deletion page, and the links that join them. It does not cover the project's public detail page,
which presents the record rather than editing it.

## Clarifications

### Session 2026-08-23

- Q: The previous specification required funding to be editable on the project's own attributes
  page. The form declares a funding field and the application shell then removes it before
  rendering, because the field is absent from the form's declared field list. A note in the code
  says a raw JSON text area is the wrong interface for it. Was the omission deliberate? → A:
  Deliberate, and it now stands. Funding leaves this feature entirely and the unreachable field
  declaration is removed. Issue #175 replaces the JSON field with a related model across projects
  and datasets, and funding becomes editable there.
- Q: The four pages set an attribute the application shell deprecated at 0.16 and removes at 0.18,
  which is why the deletion page's back link renders empty and the attributes page draws no link
  to deletion. Is repairing that part of this feature? → A: Yes. These are this feature's own
  pages and the navigation between them is part of it working.
- Q: Should this feature also cover the project's descriptions, dates and identifiers, which are
  related records rather than fields on the project? → A: Yes, wired up plainly. The application
  shell already provides the view classes for editing related records, so this is configuration
  rather than new machinery. Descriptions get a page of their own. Dates and identifiers are
  edited alongside the project's own attributes.
- Q: The creation form offers Public as its pre-selected visibility while the model's own default
  is Private. Which is intended? → A: Both. The model default protects records created outside the
  portal, where nobody is reading a form. The form default encourages openness where a person is
  making the choice deliberately.
- Q: Keywords are named alongside descriptions and dates in issue #171. Are they in scope? → A:
  No. Keywords are deferred until the controlled-vocabulary package is properly integrated, at
  which point they get an interface suited to selecting from a vocabulary. Issue #171 stays open
  for keywords alone.
- Q: The project's pages were addressed independently of the portal's own per-record navigation,
  which is why nothing links them. Should they be registered against the record instead? → A: Yes.
  The project's page is its overview registration, and the attributes and deletion pages belong to
  that registration rather than taking navigation entries of their own. A registration is a
  collection of related functionality carrying one entry; its own pages are linked from within it.
  This restores an arrangement the portal had until a registry change dropped it.
- Q: A project sits under the plural form of its record type while the pages registered against it
  sit under the singular form, and bringing them together means moving one of the two. Which moves?
  → A: The singular form goes. A project keeps the address it has and its pages become segments
  below it, so the pages already registered against a project change address.
- Q: The description vocabulary for projects is a closed set of seven types and a project may hold
  at most one description of each. Does the descriptions page present a list to add to, or a fixed
  set of slots? → A: A fixed set of slots, one editable area per type.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find a project (Priority: P1)

Anyone, signed in or not, opens the project listing to see what a portal holds. They search by
name, narrow the results by status, owner, contributor or tag, and sort by name or by when each
project was added. Selecting an entry opens that project.

**Why this priority**: the listing is the only route into the project area for someone who does not
already hold a link. Every other page in this feature is reached through it or through a project
it leads to.

**Independent Test**: visit the listing while signed out, confirm private projects are absent,
search for a known name, sort each way, and follow an entry through to its project.

**Acceptance Scenarios**:

1. **Given** projects exist with both visibilities, **When** the listing is opened by any visitor,
   **Then** only public projects appear.
2. **Given** a project whose name contains a distinctive word, **When** that word is searched,
   **Then** the project appears and unrelated projects do not.
3. **Given** a project's identifier is known, **When** it is searched, **Then** that project is
   found.
4. **Given** several projects, **When** the visitor sorts by name, **Then** they appear in
   alphabetical order, and reversing the sort reverses the order.
5. **Given** several projects added at different times, **When** the visitor sorts by date added,
   **Then** they appear oldest first, and reversing the sort reverses the order.
6. **Given** projects with differing statuses, **When** a status is chosen, **Then** only projects
   with that status remain.
7. **Given** a search that matches nothing, **When** the listing renders, **Then** it says so
   rather than rendering an empty page.
8. **Given** a listing entry, **When** it is selected, **Then** that project's page opens.

---

### User Story 2 - Register a project (Priority: P1)

A signed-in researcher registers a project by giving it a name, saying where it is in its
lifecycle, and choosing whether it is public. The portal creates the record, makes them its owner,
and records them among its contributors so the project is attributable from the moment it exists.

**Why this priority**: nothing else in the feature can be exercised until a project can be made,
and the permissions granted here are what every later page checks.

**Independent Test**: submit the form while signed in and confirm the record exists, the creator
can edit and delete it, and the creator appears as a contributor.

**Acceptance Scenarios**:

1. **Given** a visitor who is not signed in, **When** the creation page is opened, **Then** they
   are sent to sign in.
2. **Given** a signed-in researcher, **When** they open the creation page, **Then** they are asked
   for a name, a status and a visibility, and for nothing else.
3. **Given** the form is opened, **When** it first renders, **Then** Public is the pre-selected
   visibility.
4. **Given** the form is submitted with no name, **When** it is validated, **Then** an error is
   shown and no project is created.
5. **Given** a valid submission, **When** the project is created, **Then** the creator may view,
   change and delete it and may change its metadata and its settings.
6. **Given** a valid submission, **When** the contributors are examined, **Then** the creator is
   among them as Creator, ProjectMember and ContactPerson.
7. **Given** a valid submission, **When** the record is examined, **Then** it remembers who created
   it.
8. **Given** a valid submission, **When** the form is accepted, **Then** the researcher arrives at
   the new project's page.

---

### User Story 3 - Correct a project's own attributes (Priority: P1)

A researcher with permission to change a project opens its attributes page and adjusts its name,
image, lifecycle status, visibility and owning organisation. On the same page they record the
project's external identifiers and its start and end dates, adding, changing and removing them as
the project progresses.

**Why this priority**: a project is registered from three fields and is incomplete until the rest
are filled in, so this is the page that turns a stub into a record worth publishing.

**Independent Test**: submit the page as a permitted user, changing an attribute, adding an
identifier and setting both dates, then confirm all three persist and that a user without
permission is refused.

**Acceptance Scenarios**:

1. **Given** a user without change permission, **When** the page is opened, **Then** they are
   refused.
2. **Given** a visitor who is not signed in, **When** the page is opened, **Then** they are sent to
   sign in.
3. **Given** a permitted user, **When** they change the name, status, visibility, owner or image,
   **Then** the change persists.
4. **Given** the name is cleared, **When** the page is submitted, **Then** an error is shown and
   nothing is saved.
5. **Given** a permitted user, **When** they add an identifier of a chosen type and save, **Then**
   the identifier is recorded against the project.
6. **Given** an existing identifier, **When** it is removed and the page saved, **Then** it is gone
   from the project.
7. **Given** an identifier value already recorded against another project, **When** it is submitted,
   **Then** an error is shown and nothing is saved.
8. **Given** a permitted user, **When** they set a start date and an end date, **Then** both are
   recorded against the project.
9. **Given** an end date earlier than the start date, **When** the page is submitted, **Then** an
   error is shown and nothing is saved.
10. **Given** the page is rendered, **When** its fields are examined, **Then** it offers no
    descriptions, keywords, tags, contributors or funding.
11. **Given** a successful submission, **When** the page is accepted, **Then** the researcher
    arrives at the project's page.

---

### User Story 4 - Describe a project (Priority: P2)

A researcher with permission to change a project opens its descriptions page and writes its
abstract, introduction, background, objectives, expected output and conclusions, each in its own
area. They fill in what they have and leave the rest empty, returning later to extend them.

**Why this priority**: descriptions are the substance a reader judges a project by, and they are
long-form prose that does not belong beside single-line attributes.

**Independent Test**: write two descriptions, save, reopen the page and confirm both are shown as
written, then clear one, save, and confirm it is gone.

**Acceptance Scenarios**:

1. **Given** a user without change permission, **When** the descriptions page is opened, **Then**
   they are refused.
2. **Given** a project with no descriptions, **When** the page is opened, **Then** it offers one
   empty area per description type, each labelled and explained.
3. **Given** text entered in one area, **When** the page is saved, **Then** a description of that
   type is recorded and the others are not.
4. **Given** a project with an existing description, **When** the page is opened, **Then** that
   text appears in the area for its type.
5. **Given** an existing description, **When** its area is cleared and the page saved, **Then** the
   description is removed from the project.
6. **Given** a successful submission, **When** the page is accepted, **Then** the researcher
   arrives at the project's page.

---

### User Story 5 - Move between a project's pages (Priority: P2)

Someone looking at a project reaches everything they may do to it from the project itself, and
returns from each page without using the browser's back button. Someone who may not edit the
project is not shown links to pages that would refuse them.

**Why this priority**: every page in this feature is currently reachable only by typing its
address, so without this the rest of the feature is unusable by anyone who is not a developer.

**Independent Test**: as a permitted user, start at a project and reach its attributes,
descriptions and deletion pages by following links, returning to the project from each. Repeat as
a user without permission and confirm the links are absent.

**Acceptance Scenarios**:

1. **Given** a user who may change a project, **When** they view it, **Then** they are offered its
   attributes page and its descriptions page.
2. **Given** a user who may delete a project, **When** they view it, **Then** they are offered its
   deletion page.
3. **Given** a user who may do neither, **When** they view a project, **Then** neither is offered.
4. **Given** any page in this feature, **When** it is rendered, **Then** every link it draws
   resolves to a real address.
5. **Given** the deletion page, **When** the visitor declines, **Then** a working link returns them
   whence they came.
6. **Given** the attributes page, **When** a user who may delete the project views it, **Then** the
   deletion page is offered from there too.

---

### User Story 6 - Remove a project (Priority: P3)

A researcher with permission to delete a project confirms by typing its name exactly. The portal
refuses while any of the project's datasets are public, and says which ones, so that published
data cannot be withdrawn by deleting what holds it.

**Why this priority**: deletion is rare and destructive. It matters most that it is hard to do by
accident and impossible to do to published data.

**Independent Test**: attempt deletion of a project with a public dataset and confirm it is
refused and the dataset named, then of a project with only private datasets and confirm it
succeeds, and separately confirm a mistyped name stops the deletion.

**Acceptance Scenarios**:

1. **Given** a user without delete permission, **When** the deletion page is opened, **Then** they
   are refused.
2. **Given** a visitor who is not signed in, **When** the deletion page is opened, **Then** they
   are sent to sign in.
3. **Given** a project with no public datasets, **When** its name is typed correctly and confirmed,
   **Then** the project is deleted.
4. **Given** the deletion page, **When** a name that is not the project's is typed, **Then** an
   error is shown and the project remains.
5. **Given** the project's name typed with leading or trailing spaces, **When** it is confirmed,
   **Then** the spaces are disregarded and the deletion proceeds.
6. **Given** a project with one or more public datasets, **When** deletion is confirmed, **Then**
   it is refused.
7. **Given** a refused deletion, **When** the page is redrawn, **Then** it explains why and names
   each public dataset standing in the way.
8. **Given** a successful deletion, **When** it completes, **Then** the researcher arrives at the
   project listing.

---

### Edge Cases

- A public dataset is added to a project between the deletion page being opened and confirmed. The
  refusal is decided when the deletion is attempted, not when the page is drawn, so the deletion is
  still refused and the newly added dataset is among those named.
- A project is public and has no datasets at all, or only private ones. It may be deleted. The
  refusal protects published datasets, not the project record itself.
- A filter is applied that no project satisfies. The listing renders its empty state rather than a
  blank page.
- A description is written and then cleared to whitespace. It is treated as empty and the
  description is removed rather than stored blank.
- A project has a start date and no end date. This is normal for a running project and is accepted.
- The same identifier value is submitted twice on one page. The page reports the collision rather
  than saving one and dropping the other.

## Requirements *(mandatory)*

Requirements state what a person can do and what the portal guarantees. Where the application shell
already provides a facility, the requirement is to use it rather than to build an equivalent, per
Article XIV.

### The project listing

- **FR-001**: The listing MUST be reachable at a stable address named `project-list` and MUST be
  open to visitors who are not signed in.
- **FR-002**: The listing MUST show only public projects, whoever is looking.
- **FR-003**: The listing MUST offer a search covering at least the project's name and its
  identifier.
- **FR-004**: The listing MUST offer the portal's existing project filters: status, owner,
  contributor and tag.
- **FR-005**: The listing MUST offer ordering by name and by date added, in both directions.
- **FR-006**: The listing MUST show an empty state when nothing matches, rather than an empty page.
- **FR-007**: Each entry in the listing MUST link to its project's page.
- **FR-008**: The visual design of a listing entry is out of scope. The entry keeps its current
  design and gains only the link required by FR-007.

### Registering a project

- **FR-009**: The creation page MUST be reachable at a stable address named `project-create` and
  MUST require the visitor to be signed in, sending them to sign in otherwise.
- **FR-010**: The creation page MUST ask for the project's name, its lifecycle status and its
  visibility, and MUST ask for nothing else.
- **FR-011**: The creation page MUST present visibility as a visible choice between its options
  rather than a hidden default, and MUST pre-select Public.
- **FR-012**: A project MUST NOT be created without a name.
- **FR-013**: On creation the creator MUST be granted permission to view, change and delete the
  project and to change its metadata and its settings.
- **FR-014**: On creation the creator MUST be recorded among the project's contributors as Creator,
  ProjectMember and ContactPerson.
- **FR-015**: On creation the project MUST record who created it.
- **FR-016**: On successful creation the researcher MUST arrive at the new project's page.

### The project's own attributes

- **FR-017**: The attributes page MUST be reachable at a stable address identifying the project by
  its identifier, and MUST require the visitor to be signed in.
- **FR-018**: The attributes page MUST refuse a user who does not hold permission to change that
  project.
- **FR-019**: The attributes page MUST cover the project's own attributes: image, name, lifecycle
  status, visibility and owning organisation.
- **FR-020**: The attributes page MUST allow the project's external identifiers to be added,
  changed and removed, any number of them, each with a type from the portal's identifier
  vocabulary.
- **FR-021**: The attributes page MUST allow the project's start and end dates to be set, changed
  and removed.
- **FR-022**: The attributes page MUST refuse an end date earlier than the project's start date,
  and MUST report which field is at fault.
- **FR-023**: The attributes page MUST refuse an identifier value already recorded against another
  project, and MUST report the collision rather than saving part of the submission.
- **FR-024**: The attributes page MUST NOT offer descriptions, keywords, tags, contributors or
  funding.
- **FR-025**: A project MUST NOT be saved without a name.
- **FR-026**: On successful submission the researcher MUST arrive at the project's page.
- **FR-027**: Identifiers and dates MUST be edited through the application shell's facility for
  editing related records, not through a hand-written equivalent.

### The project's descriptions

- **FR-028**: The descriptions page MUST be reachable at a stable address of its own, identifying
  the project by its identifier, and MUST require the visitor to be signed in.
- **FR-029**: The descriptions page MUST refuse a user who does not hold permission to change that
  project.
- **FR-030**: The descriptions page MUST offer one editable area for each description type in the
  portal's project description vocabulary, labelled with the type's name and explained by its
  definition.
- **FR-031**: Saving text into an area MUST record a description of that type against the project.
  A project MUST NOT hold more than one description of any type.
- **FR-032**: Clearing an area MUST remove that description from the project.
- **FR-033**: An area left empty MUST NOT create an empty description.
- **FR-034**: On successful submission the researcher MUST arrive at the project's page.

### Removing a project

- **FR-035**: The deletion page MUST be reachable at a stable address identifying the project by its
  identifier, and MUST require the visitor to be signed in.
- **FR-036**: The deletion page MUST refuse a user who does not hold permission to delete that
  project.
- **FR-037**: The deletion page MUST require the visitor to type the project's name exactly before
  it will proceed, disregarding leading and trailing spaces.
- **FR-038**: A project MUST NOT be deleted while any of its datasets is public. The refusal MUST
  be enforced by the project record itself, so that it holds however the deletion is attempted, and
  not by the page alone.
- **FR-039**: When a deletion is refused, the page MUST be redrawn with an explanation and MUST
  name each public dataset standing in the way.
- **FR-040**: On successful deletion the researcher MUST arrive at the project listing.

### Moving between the pages

- **FR-041**: A project's page MUST offer its attributes page and its descriptions page to a user
  who may change the project, and its deletion page to a user who may delete it.
- **FR-042**: A page MUST NOT offer a link to a page that would refuse the user looking at it.
- **FR-043**: Every link drawn by the pages in this feature MUST resolve to a real address. A link
  that cannot be resolved MUST NOT be drawn as an empty one.
- **FR-044**: The attributes, descriptions and deletion pages MUST each offer a way back to the
  project.
- **FR-045**: The attributes page MUST offer the deletion page to a user who may delete the
  project.
- **FR-046**: Links MUST be declared through the application shell's current mechanism for
  declaring which actions a page offers. The superseded mechanism, which the shell deprecated and
  will remove, MUST NOT be used.
- **FR-047**: The content and layout of the project's own page are out of scope. It keeps its
  current design and gains only the links required by FR-041.

### Addresses

- **FR-048**: Every address in this feature MUST follow the portal's convention of naming a record
  type and an action, and MUST name the record type in the plural. The singular form MUST NOT
  answer.
- **FR-049**: Every address identifying a particular project MUST do so by the project's identifier,
  and every page belonging to that project MUST sit below the project's own address.
- **FR-050**: The project's own page, its attributes page, its descriptions page and its deletion
  page MUST all be registered against the project record rather than addressed independently, so
  that the portal's own navigation can reach every one of them. A page reachable only by an address
  the navigation cannot construct does not satisfy this.
- **FR-051**: Each of those pages MUST state the permission it requires for itself. A page that
  states none MUST NOT be treated as inheriting one.

### Deliberate omissions

- **FR-052**: Funding MUST NOT be editable through this feature, and the unreachable funding field
  declared on the project form MUST be removed rather than left in place. Funding editing is issue
  #175, which replaces the field with a related model across projects and datasets.
- **FR-053**: Keywords and tags MUST NOT be editable through this feature. They are deferred until
  the controlled-vocabulary package is integrated, which is what will give them an interface suited
  to choosing from a vocabulary.

### Key Entities

- **Project**: the record being managed. Its own attributes are its identifier, name, image,
  lifecycle status, visibility and owning organisation, together with a record of who created it.
- **Project description**: a passage of prose about a project, of one type drawn from a closed
  vocabulary, with at most one of each type per project. The project vocabulary holds seven types.
- **Project date**: a date in the project's life, of one type drawn from a closed vocabulary. The
  project vocabulary holds two, a start and an end, and the end may not precede the start.
- **Project identifier**: an external identifier for the project, of one type drawn from a
  vocabulary, whose value names one project and no other.
- **Dataset**: a record belonging to a project, whose visibility is its own. A public dataset
  prevents its project being deleted.
- **Contribution**: the record connecting a person to a project in one or more roles. This feature
  creates one, for the creator, and does not otherwise manage them.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A researcher can register a project and reach a complete record — attributes,
  identifiers, dates and descriptions — using only links, without typing an address and without an
  administrator.
- **SC-002**: No private project appears in the listing, for any visitor, signed in or not.
- **SC-003**: A project with at least one public dataset is never deleted through the portal, and
  every refusal names the datasets responsible.
- **SC-004**: A deletion never proceeds unless the project's name was typed correctly.
- **SC-005**: Every page in this feature refuses a user who lacks the permission it requires, and
  offers no link to a page that would refuse them.
- **SC-006**: Every link drawn by these pages resolves. None renders empty.
- **SC-007**: The pages emit no deprecation warnings from the application shell.
- **SC-008**: Nothing in this feature offers funding, keywords or tags for editing.

## Assumptions

- The application shell provides the view classes for editing related records alongside a parent,
  so identifiers and dates are configuration rather than new machinery. Which of them fits each
  case is settled during planning.
- The portal's existing project filter is adequate as it stands and gains no new filters here.
- Object-level permissions are already established through the portal's permission layer, and this
  feature checks them rather than defining them.
- The description, date and identifier vocabularies already exist and are not changed here.
- Visibility has two values, public and private, already established in the portal.
- A project's own page and its listing entry already exist and are changed only to add links.
- Projects are addressed by their identifier, as they already are.
