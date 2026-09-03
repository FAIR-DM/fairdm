# Feature Specification: Managing a dataset through the portal

**Feature Branch**: `014-dataset-crud-views`

**Created**: 2026-05-12 · **Rewritten**: 2026-08-25

**Status**: Draft

**Goals**: G6 — core records can be created and edited by hand through the portal.

**Roadmap**: R12 — editing projects and datasets in the portal.

**Input**: A researcher with data to register needs to create a dataset, describe it, correct it and
occasionally remove it, without an administrator and without the Django admin. This specification
covers every portal page through which a dataset record is managed: the public listing, the
creation form, the page for its own attributes, the page for its descriptions, the deletion page,
and the links that join them. It does not cover the dataset's public detail page, which presents
the record rather than editing it, nor anything to do with the data held beneath a dataset.

This is the dataset half of R12. The project half is specified in `013-project-crud-views` and is
built. The two features are deliberately alike, and where the portal already has a facility built
for the project's pages, this feature configures it rather than building a second one.

## Clarifications

### Session 2026-08-25

- Q: The previous specification kept visibility off both dataset forms, deferring it to a
  publish-and-unpublish workflow that does not exist, leaving a dataset created through the portal
  private with no portal page able to change that. Is visibility part of this feature? → A: Yes,
  and what it means is now settled. A **public** dataset is one whose *metadata* anyone using the
  portal may read. It says what a researcher is working on, which is what makes a portal a
  community rather than a filing cabinet, so the switch belongs to the researcher. The *data* held
  beneath a dataset is a separate matter: reaching it and publishing it are gated behind a
  publication process run by portal administrators or by peer review, which is a later feature.
  Nothing in this feature publishes data.
- Q: A project refuses deletion while any of its datasets is public. What is the dataset's
  equivalent? → A: None, in this feature. A **published** dataset may not be deleted, because
  others may cite it and reuse its data, but publication is the later feature above and no such
  state exists yet. A dataset that is public but not published may be deleted, and so may one with
  samples and measurements attached. What the deletion page owes the researcher instead is a plain
  and prominent warning naming exactly what will go with it.
- Q: The refusal on the project side is therefore keyed on the wrong state — it stops a project
  being deleted because a dataset's *metadata* is public. Does this feature correct it? → A: No.
  This feature is about datasets. The inconsistency is recorded as an issue, with the two
  candidate answers: refuse a project's deletion while any dataset is attached at all, or detach
  the datasets before deleting.
- Q: Keywords are edited today on a page of their own, registered against the dataset. Projects
  have no such page, and 013 deferred keywords entirely. Do the dataset's keywords stay? → A: No.
  The page is removed. All keyword editing is rebuilt in a later specification, against the
  controlled vocabularies, and it is better to have no page than one that will be replaced whole.
- Q: A dataset's DOI is edited through a dedicated text box that writes an identifier record
  behind the scenes, where a project edits its identifiers as typed rows. Which arrangement does a
  dataset get? → A: The rows. The DOI box goes, and identifiers are edited the same way on every
  record, so the page grows by itself as the identifier vocabulary does.
- Q: A project is registered from its name, its lifecycle status and its visibility. A dataset has
  no status. What does its creation form ask for? → A: Its name, its visibility, its licence and
  its project. The project field is always present, defaults to empty, and offers the researcher
  their own projects. This is the plain creation page; a later feature adds a second route into it
  from a record that already implies the project, which fills the field in advance. That route is
  not built here.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find a dataset (Priority: P1)

Anyone, signed in or not, opens the dataset listing to see what a portal holds. They search by
name, narrow the results by licence, project or the kinds of description and date a dataset
carries, and sort by name or by when each dataset was added. Selecting an entry opens that dataset.

**Why this priority**: the listing is the only route into the dataset area for someone who does not
already hold a link. Every other page in this feature is reached through it or through a dataset it
leads to.

**Independent Test**: visit the listing while signed out, confirm private datasets are absent,
search for a known name, sort each way, apply each filter in turn, and follow an entry through to
its dataset.

**Acceptance Scenarios**:

1. **Given** datasets exist with both visibilities, **When** the listing is opened by any visitor,
   **Then** only public datasets appear.
2. **Given** a dataset whose name contains a distinctive word, **When** that word is searched,
   **Then** the dataset appears and unrelated datasets do not.
3. **Given** a dataset's identifier is known, **When** it is searched, **Then** that dataset is
   found.
4. **Given** several datasets, **When** the visitor sorts by name, **Then** they appear in
   alphabetical order, and reversing the sort reverses the order.
5. **Given** several datasets added at different times, **When** the visitor sorts by date added,
   **Then** they appear oldest first, and reversing the sort reverses the order.
6. **Given** datasets under differing licences, **When** a licence is chosen, **Then** only
   datasets under it remain.
7. **Given** datasets carrying dates of differing types, **When** a date type is chosen, **Then**
   only datasets carrying a date of that type remain, and no error is raised.
8. **Given** a visitor who may not see a particular project, **When** they open the listing's
   project filter, **Then** that project is not among the choices.
9. **Given** a search that matches nothing, **When** the listing renders, **Then** it says so
   rather than rendering an empty page.
10. **Given** a listing entry, **When** it is selected, **Then** that dataset's page opens.

---

### User Story 2 - Register a dataset (Priority: P1)

A signed-in researcher registers a dataset by giving it a name, choosing whether its metadata is
public, choosing the licence its data will carry, and optionally saying which of their projects it
belongs to. The portal creates the record, makes them its owner, and records them among its
contributors so the dataset is attributable from the moment it exists.

**Why this priority**: nothing else in the feature can be exercised until a dataset can be made,
and the permissions granted here are what every later page checks.

**Independent Test**: submit the form while signed in and confirm the record exists, the creator can
edit and delete it, and the creator appears as a contributor.

**Acceptance Scenarios**:

1. **Given** a visitor who is not signed in, **When** the creation page is opened, **Then** they are
   sent to sign in.
2. **Given** a signed-in researcher, **When** they open the creation page, **Then** they are asked
   for a name, a visibility, a licence and a project, and for nothing else.
3. **Given** the form is opened, **When** it first renders, **Then** Public is the pre-selected
   visibility, the portal's default licence is pre-selected, and the project is empty.
4. **Given** a signed-in researcher, **When** they open the project field, **Then** it offers the
   projects they may use and no others.
5. **Given** the form is submitted with no name, **When** it is validated, **Then** an error is
   shown and no dataset is created.
6. **Given** the form is submitted with no project, **When** it is validated, **Then** the dataset
   is created and belongs to no project.
7. **Given** a valid submission, **When** the dataset is created, **Then** the creator may view,
   change and delete it and may change its metadata and its settings.
8. **Given** a valid submission, **When** the contributors are examined, **Then** the creator is
   among them as Creator, ProjectMember and ContactPerson.
9. **Given** a valid submission, **When** the record is examined, **Then** it remembers who created
   it.
10. **Given** a valid submission, **When** the form is accepted, **Then** the researcher arrives at
    the new dataset's page.

---

### User Story 3 - Correct a dataset's own attributes (Priority: P1)

A researcher with permission to change a dataset opens its update page and adjusts its name, image,
project, licence, visibility and the publication that describes it. On the same page they record
the dataset's external identifiers and the dates its collection began and ended, adding, changing
and removing them as the work progresses.

**Why this priority**: a dataset is registered from four fields and is incomplete until the rest are
filled in, so this is the page that turns a stub into a record worth citing.

**Independent Test**: submit the page as a permitted user, changing an attribute, adding an
identifier and setting both dates, then confirm all three persist and that a user without
permission is refused.

**Acceptance Scenarios**:

1. **Given** a user without change permission, **When** the page is opened, **Then** they are
   refused.
2. **Given** a visitor who is not signed in, **When** the page is opened, **Then** they are sent to
   sign in.
3. **Given** a permitted user, **When** they change the name, image, project, licence, visibility or
   publication, **Then** the change persists.
4. **Given** the name is cleared, **When** the page is submitted, **Then** an error is shown and
   nothing is saved.
5. **Given** a permitted user, **When** they add an identifier of a chosen type and save, **Then**
   the identifier is recorded against the dataset.
6. **Given** an existing identifier, **When** it is removed and the page saved, **Then** it is gone
   from the dataset.
7. **Given** an identifier value already recorded against another record, **When** it is submitted,
   **Then** an error is shown and nothing is saved.
8. **Given** a permitted user, **When** they set a collection start date and a collection end date,
   **Then** both are recorded against the dataset.
9. **Given** a collection end date earlier than the collection start date, **When** the page is
   submitted, **Then** an error is shown and nothing is saved.
10. **Given** the page is rendered, **When** its fields are examined, **Then** it offers no
    descriptions, keywords, tags or contributors.
11. **Given** a successful submission, **When** the page is accepted, **Then** the researcher
    arrives at the dataset's page.

---

### User Story 4 - Describe a dataset (Priority: P2)

A researcher with permission to change a dataset opens its descriptions page and writes each kind of
description the portal recognises for a dataset, each in its own area. They fill in what they have
and leave the rest empty, returning later to extend them.

**Why this priority**: descriptions are the substance a reader judges a dataset by, and they are
long-form prose that does not belong beside single-line attributes.

**Independent Test**: write two descriptions, save, reopen the page and confirm both are shown as
written, then clear one, save, and confirm it is gone.

**Acceptance Scenarios**:

1. **Given** a user without change permission, **When** the descriptions page is opened, **Then**
   they are refused.
2. **Given** a dataset with no descriptions, **When** the page is opened, **Then** it offers one
   empty area per description type, each labelled and explained.
3. **Given** text entered in one area, **When** the page is saved, **Then** a description of that
   type is recorded and the others are not.
4. **Given** a dataset with an existing description, **When** the page is opened, **Then** that text
   appears in the area for its type.
5. **Given** an existing description, **When** its area is cleared and the page saved, **Then** the
   description is removed from the dataset.
6. **Given** a successful submission, **When** the page is accepted, **Then** the researcher arrives
   at the dataset's page.

---

### User Story 5 - Move between a dataset's pages (Priority: P2)

Someone looking at a dataset reaches everything they may do to it from the dataset itself, and
returns from each page without using the browser's back button. Someone who may not edit the dataset
is not shown links to pages that would refuse them.

**Why this priority**: every page in this feature is currently reachable only by typing its address,
so without this the rest of the feature is unusable by anyone who is not a developer.

**Independent Test**: as a permitted user, start at a dataset and reach its update, descriptions and
deletion pages by following links, returning to the dataset from each. Repeat as a user without
permission and confirm the links are absent.

**Acceptance Scenarios**:

1. **Given** a user who may change a dataset, **When** they view it, **Then** they are offered its
   update page and its descriptions page.
2. **Given** a user who may delete a dataset, **When** they view it, **Then** they are offered its
   deletion page.
3. **Given** a user who may do neither, **When** they view a dataset, **Then** neither is offered.
4. **Given** any page in this feature, **When** it is rendered, **Then** every link it draws
   resolves to a real address.
5. **Given** the deletion page, **When** the visitor declines, **Then** a working link returns them
   whence they came.
6. **Given** the update page, **When** a user who may delete the dataset views it, **Then** the
   deletion page is offered from there too.

---

### User Story 6 - Remove a dataset (Priority: P3)

A researcher with permission to delete a dataset confirms by typing its name exactly. Before they
do, the page tells them plainly what else will go: the samples and the measurements held beneath it,
counted, and its descriptions, dates and identifiers.

**Why this priority**: deletion is rare and destructive, and a dataset is the only record in the
portal whose deletion takes a body of data with it. It matters most that nobody does it without
knowing what they are about to lose.

**Independent Test**: open the deletion page for a dataset holding samples and measurements, confirm
the page names what will be lost and how much of it, then delete it and confirm all of it is gone.
Separately confirm a mistyped name stops the deletion.

**Acceptance Scenarios**:

1. **Given** a user without delete permission, **When** the deletion page is opened, **Then** they
   are refused.
2. **Given** a visitor who is not signed in, **When** the deletion page is opened, **Then** they are
   sent to sign in.
3. **Given** a dataset holding samples or measurements, **When** the deletion page is opened,
   **Then** it warns prominently that the data will be deleted with the dataset, and says how many
   samples and how many measurements.
4. **Given** a dataset holding no samples or measurements, **When** the deletion page is opened,
   **Then** it does not warn about data.
5. **Given** the deletion page, **When** a name that is not the dataset's is typed, **Then** an
   error is shown and the dataset remains.
6. **Given** the dataset's name typed with leading or trailing spaces, **When** it is confirmed,
   **Then** the spaces are disregarded and the deletion proceeds.
7. **Given** a public dataset whose name is typed correctly, **When** it is confirmed, **Then** it is
   deleted — being public is not, on its own, grounds for refusal.
8. **Given** a successful deletion, **When** it completes, **Then** the researcher arrives at the
   dataset listing and the samples and measurements that belonged to the dataset are gone.

---

### Edge Cases

- A sample is added to a dataset between the deletion page being drawn and the deletion being
  confirmed. The counts shown were true when the page was drawn; the deletion still proceeds and
  still takes the new sample with it. The warning exists to inform, not to lock a count.
- A dataset belongs to no project. This is normal and is accepted everywhere: it may be created,
  edited, listed and deleted exactly as one that does.
- A dataset's project is deleted. The dataset goes with it — that is the project's own behaviour and
  it is unchanged here.
- A filter is applied that no dataset satisfies. The listing renders its empty state rather than a
  blank page.
- A description is written and then cleared to whitespace. It is treated as empty and the
  description is removed rather than stored blank.
- A dataset has a collection start date and no end date. This is normal for collection still under
  way and is accepted.
- The same identifier value is submitted twice on one page. The page reports the collision rather
  than saving one and dropping the other.
- A researcher makes a dataset public and later makes it private again. Both are ordinary edits on
  the update page and neither is restricted.

## Requirements *(mandatory)*

Requirements state what a person can do and what the portal guarantees. Where the application shell
already provides a facility, the requirement is to use it rather than to build an equivalent, per
Article XIV. Where the project's pages already established an arrangement, this feature adopts it
rather than inventing a second one.

### The dataset listing

- **FR-001**: The listing MUST be reachable at a stable address named `dataset-list` and MUST be
  open to visitors who are not signed in.
- **FR-002**: The listing MUST show only public datasets, whoever is looking.
- **FR-003**: The listing MUST offer a search covering at least the dataset's name, its identifier
  and its descriptions.
- **FR-004**: The listing MUST offer ordering by name and by date added, in both directions.
- **FR-005**: The listing MUST offer filters by licence, by project, and by the types of description
  and date a dataset carries.
- **FR-006**: Every filter the listing offers MUST work when it is applied. A filter that raises an
  error, or that cannot change the result set, MUST NOT be offered.
- **FR-007**: The listing's project filter MUST offer only projects the visitor may see.
- **FR-008**: The listing MUST show an empty state when nothing matches, rather than an empty page.
- **FR-009**: Each entry in the listing MUST link to its dataset's page.
- **FR-010**: The visual design of a listing entry is out of scope. The entry keeps its current
  design and gains only the link required by FR-009.

### Registering a dataset

- **FR-011**: The creation page MUST be reachable at a stable address named `dataset-create` and
  MUST require the visitor to be signed in, sending them to sign in otherwise.
- **FR-012**: The creation page MUST ask for the dataset's name, its visibility, its licence and its
  project, and MUST ask for nothing else.
- **FR-013**: The creation page MUST present visibility as a visible choice between its options
  rather than a hidden default, and MUST pre-select Public.
- **FR-014**: The creation page MUST pre-select the portal's configured default licence.
- **FR-015**: The project field MUST be optional and MUST start empty. A dataset MUST be creatable
  without a project.
- **FR-016**: The project field MUST offer only projects the signed-in researcher may use, and MUST
  offer none at all to a visitor who is not signed in.
- **FR-017**: A dataset MUST NOT be created without a name.
- **FR-018**: On creation the creator MUST be granted permission to view, change and delete the
  dataset and to change its metadata and its settings.
- **FR-019**: On creation the creator MUST be recorded among the dataset's contributors as Creator,
  ProjectMember and ContactPerson.
- **FR-020**: On creation the dataset MUST record who created it.
- **FR-021**: On successful creation the researcher MUST arrive at the new dataset's page.
- **FR-022**: The creation page MUST use the same declared form as the update page, narrowed to the
  fields FR-012 names, so that a field's label, help text and widget are stated once and are the
  same on both pages.

### The dataset's own attributes

- **FR-023**: The update page MUST be reachable at a stable address identifying the dataset by its
  identifier, and MUST require the visitor to be signed in.
- **FR-024**: The update page MUST refuse a user who does not hold permission to change that
  dataset.
- **FR-025**: The update page MUST cover the dataset's own attributes: image, name, project,
  licence, visibility and the publication that describes the dataset.
- **FR-026**: The project field on the update page MUST offer only projects the signed-in researcher
  may use, on the same terms as FR-016.
- **FR-027**: The update page MUST allow the dataset's external identifiers to be added, changed and
  removed, any number of them, each with a type from the portal's dataset identifier vocabulary.
- **FR-028**: The update page MUST allow the dataset's collection start and collection end dates to
  be set, changed and removed.
- **FR-029**: The update page MUST refuse a collection end date earlier than the collection start
  date, and MUST report which field is at fault.
- **FR-030**: The update page MUST refuse an identifier value already recorded against another
  record, and MUST report the collision rather than saving part of the submission.
- **FR-031**: The update page MUST NOT offer descriptions, keywords, tags or contributors.
- **FR-032**: A dataset MUST NOT be saved without a name.
- **FR-033**: On successful submission the researcher MUST arrive at the dataset's page.
- **FR-034**: Identifiers and dates MUST be edited through the application shell's facility for
  editing related records, the same facility the project's own page uses, not through a
  hand-written equivalent.

### The dataset's descriptions

- **FR-035**: The descriptions page MUST be reachable at a stable address of its own, identifying
  the dataset by its identifier, and MUST require the visitor to be signed in.
- **FR-036**: The descriptions page MUST refuse a user who does not hold permission to change that
  dataset.
- **FR-037**: The descriptions page MUST offer one editable area for each description type in the
  portal's dataset description vocabulary, labelled with the type's name and explained by its
  definition.
- **FR-038**: Saving text into an area MUST record a description of that type against the dataset. A
  dataset MUST NOT hold more than one description of any type.
- **FR-039**: Clearing an area MUST remove that description from the dataset.
- **FR-040**: An area left empty MUST NOT create an empty description.
- **FR-041**: On successful submission the researcher MUST arrive at the dataset's page.
- **FR-042**: The descriptions page MUST use the same vocabulary-driven form the project's
  descriptions page uses, rather than the row-based editor it uses today.

### Removing a dataset

- **FR-043**: The deletion page MUST be reachable at a stable address identifying the dataset by its
  identifier, and MUST require the visitor to be signed in.
- **FR-044**: The deletion page MUST refuse a user who does not hold permission to delete that
  dataset.
- **FR-045**: The deletion page MUST require the visitor to type the dataset's name exactly before
  it will proceed, disregarding leading and trailing spaces.
- **FR-046**: The deletion page MUST state what will be deleted along with the dataset, before the
  confirmation is offered — the samples and measurements held beneath it, and its descriptions,
  dates and identifiers. This MUST use the application shell's own facility for previewing what a
  deletion would take, per Article XIV, rather than a hand-written equivalent. *(Amended 2026-08-25:
  originally required the two counts and a warning of this feature's own making, written before the
  shell's facility had been read properly.)*
- **FR-047**: Where a dataset holds no samples and no measurements, the page MUST NOT warn about
  data it does not hold.
- **FR-048**: A dataset's visibility MUST NOT, on its own, prevent its deletion. A public dataset
  whose data has not been published through the portal is deleted like any other.
- **FR-049**: On successful deletion the researcher MUST arrive at the dataset listing.

### Moving between the pages

- **FR-050**: A dataset's page MUST itself draw a link to its update page and to its descriptions
  page for a user who may change the dataset, and to its deletion page for a user who may delete it.
  A navigation entry generated for one of those pages does not satisfy this — the link belongs to
  the dataset's own page.
- **FR-051**: A page MUST NOT offer a link to a page that would refuse the user looking at it.
- **FR-052**: Every link drawn by the pages in this feature MUST resolve to a real address. A link
  that cannot be resolved MUST NOT be drawn as an empty one.
- **FR-053**: The update, descriptions and deletion pages MUST each offer a way back to the dataset.
- **FR-054**: The update page MUST offer the deletion page to a user who may delete the dataset.
- **FR-055**: Links MUST be declared through the application shell's current mechanism for declaring
  which actions a page offers. The superseded mechanism, which the shell deprecated and will remove,
  MUST NOT be used.
- **FR-056**: The content and layout of the dataset's own page are out of scope. It keeps its
  current design and gains only the links required by FR-050.

### Addresses

- **FR-057**: Every address in this feature MUST follow the portal's convention of naming a record
  type and an action, and MUST name the record type in the plural. The singular form MUST NOT
  answer.
- **FR-058**: Every address identifying a particular dataset MUST do so by the dataset's identifier,
  and every page belonging to that dataset MUST sit below the dataset's own address.
- **FR-059**: The dataset's own page, its update page, its descriptions page and its deletion page
  MUST all be registered against the dataset record rather than addressed independently, so that the
  portal's own navigation can reach every one of them. A page reachable only by an address the
  navigation cannot construct does not satisfy this.
- **FR-060**: Each of those pages MUST state the permission it requires for itself. A page that
  states none MUST NOT be treated as inheriting one.
- **FR-061**: Each of those pages MUST also state its own visibility rule, so that a private dataset
  is refused at every one of its addresses. A page MUST NOT be treated as inheriting the visibility
  rule of the page it belongs to.
- **FR-062**: A dataset's pages MUST contribute exactly one entry to the portal's per-record
  navigation. The pages for updating a dataset, describing it and deleting it MUST NOT each take an
  entry of their own; they belong to the dataset's page and are reached by links that page draws.

### Deliberate omissions

- **FR-063**: Keywords MUST NOT be editable through this feature, and the dataset's existing
  keywords page MUST be removed rather than left in place or carried over. Keyword editing is
  rebuilt whole against the controlled vocabularies in a later specification.
- **FR-064**: Tags MUST NOT be editable through this feature, for the same reason.
- **FR-065**: Contributors MUST NOT be managed through this feature. It records the creator on
  creation and does nothing else with contributions.
- **FR-066**: ~~Nothing in this feature MUST publish a dataset's data, gate access to it, or
  introduce a published state. A dataset's visibility governs its metadata alone.~~
  **Superseded on 2026-09-01 by `015-browsing-portal-samples` FR-001, which adds a published flag
  to a dataset.** The half of this requirement that still holds is unchanged and now lives there: a
  dataset's visibility governs its metadata alone, the published flag is a separate and independent
  thing, and the checked process that decides when a dataset may be published remains R22's work.
  Nothing in *this* feature publishes a dataset's data or reads that flag.
- **FR-067**: This feature MUST NOT change how a project's deletion is refused, even though that
  refusal is keyed on a dataset's visibility.

### Key Entities

- **Dataset**: the record being managed. Its own attributes are its identifier, name, image, owning
  project, licence, visibility and the publication that describes it, together with a record of who
  created it. A dataset need not belong to a project.
- **Visibility**: whether a dataset's metadata may be read by anyone using the portal. Two values,
  private and public. It says nothing about the data held beneath the dataset, and it is not a
  publication state.
- **Dataset description**: a passage of prose about a dataset, of one type drawn from a closed
  vocabulary, with at most one of each type per dataset.
- **Dataset date**: a date in the dataset's life, of one type drawn from a closed vocabulary,
  including the start and end of collection, where the end may not precede the start.
- **Dataset identifier**: an external identifier for the dataset, of one type drawn from a
  vocabulary, whose value names one record and no other.
- **Sample and measurement**: the data held beneath a dataset. This feature neither creates nor
  edits them, and touches them only in counting what a deletion would destroy.
- **Contribution**: the record connecting a person to a dataset in one or more roles. This feature
  creates one, for the creator, and does not otherwise manage them.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A researcher can register a dataset and reach a complete record — attributes,
  identifiers, dates and descriptions — using only links, without typing an address and without an
  administrator.
- **SC-002**: No private dataset appears in the listing, for any visitor, signed in or not, and no
  private project's name is disclosed by the listing's filters.
- **SC-003**: Every filter the listing offers changes the result set when it is applied, and none
  raises an error.
- **SC-004**: A deletion never proceeds unless the dataset's name was typed correctly.
- **SC-005**: No researcher deletes a dataset holding data without having been told, on the page
  they confirmed from, what they were destroying with it.
- **SC-006**: Every page in this feature refuses a user who lacks the permission it requires, and
  offers no link to a page that would refuse them.
- **SC-007**: Every link drawn by these pages resolves. None renders empty.
- **SC-008**: The pages emit no deprecation warnings from the application shell.
- **SC-009**: Nothing in this feature offers keywords or tags for editing, and the portal has no
  keywords page for a dataset.
- **SC-010**: A dataset's metadata visibility is settable by its owner through the portal, and no
  page in this feature exposes, publishes or gates the data beneath it.

## Assumptions

- The application shell provides the view classes for editing related records alongside a parent,
  and the project's pages already use them, so identifiers and dates are configuration rather than
  new machinery. The row-set declarations for a dataset's dates and identifiers already exist.
- The vocabulary-driven descriptions form already exists and is already used by the project's
  descriptions page. It reads its field set from the related model's vocabulary, so it serves a
  dataset without modification.
- Object-level permissions are already established through the portal's permission layer, and this
  feature checks them rather than defining them.
- The description, date and identifier vocabularies for datasets already exist and are not changed
  here.
- Visibility has two values, public and private, already established in the portal.
- A dataset's own page and its listing entry already exist and are changed only to add links.
- Datasets are addressed by their identifier, as they already are.
- Samples and measurements are counted for the deletion warning through relations the dataset
  already carries.
