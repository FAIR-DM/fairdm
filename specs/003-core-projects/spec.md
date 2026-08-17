# Feature Specification: The project record

**Feature Branch**: `003-core-projects`

**Created**: 2026-01-14 · **Rewritten**: 2026-08-18

**Status**: Draft

**Goals**: G1 — a core data model of projects, datasets, samples, measurements and contributors that
domain schemas can extend and rely on. G14 — metadata complete enough for a formal-publication
addon to submit it unaided. G15 — external identifiers carried through the record.

**Roadmap**: R3 — projects.

**Input**: A project is the outermost container of the core model. Everything a portal holds hangs
beneath one: datasets, and through them samples and measurements. This specification describes the
project record itself — the fields it carries, the typed descriptions, dates and identifiers
attached to it, who is credited on it, who funded it, how an administrator manages it, and how its
metadata leaves the portal in a form another system can read.

It does not describe the pages a researcher uses to create or edit a project. Those are
`013-project-crud-views`, and the reasoning behind the split is in `decisions.md`.

## Clarifications

### Session 2026-08-18

The original text was written before the app existed and disagreed with the code in nineteen places.
Each disagreement was settled and recorded in `decisions.md`; the questions and answers below are
the ones that shaped this document.

- Q: Does this specification own the project list, create, edit and delete pages? → A: No. It owns
  the domain model, the related records, the administrative interface, funding, export and the
  creation record. The portal pages belong to `013-project-crud-views` (D-001).
- Q: A project cannot currently be given a DOI, because its identifier vocabulary lists identifiers
  for people and organisations. Is that intended? → A: No, it is a defect. A project needs its own
  identifier types, and a DOI is the one that matters (D-003).
- Q: Should a project carry data-collection dates as well as start and end? → A: No. Data collection
  is something a dataset does, and repeating those dates on the parent would duplicate them across
  every dataset beneath it (D-004).
- Q: Must a project name an owning organisation? → A: No. Creation is deliberately cheap, and many
  researchers have no single organisation to name. Ownership stays optional (D-007).
- Q: Which contribution roles may edit which fields? → A: Out of scope. The matrix in the original
  text named roles the vocabulary does not contain, and deciding the real one is a separate piece of
  design (D-009).
- Q: What does "audit trail" mean here — timestamps, or full revision history? → A: The creator and
  the timestamps. History is a much larger commitment and is routed out (D-010).
- Q: Funding is stored as free-form JSON. Should it stay that way? → A: No. Funding that is not
  validated cannot be exported, and export is the only reason to hold it in this shape (D-013).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Describe a project in the terms its field uses (Priority: P1)

A researcher records what a project is about. They write an abstract, and separately a description
of the methods, and separately a statement of why the work matters. Each one is stored under its own
type rather than concatenated into a single field, so that a reader — or another system — can ask
for the abstract alone. They also categorise the work, using terms from a controlled vocabulary
where one applies and free tags where none does.

**Why this priority**: Without typed descriptions the record carries prose and nothing else, and
prose is not something an external repository can consume. This is the smallest thing that makes a
project record more than a name.

**Independent Test**: Attach an abstract and a methods description to a project, confirm both are
retrievable independently under their own types, confirm a second abstract is refused, and confirm
that controlled keywords and free tags round-trip.

**Acceptance Scenarios**:

1. **Given** a project with no descriptions, **When** an abstract is attached, **Then** it is stored
   against that project under the abstract type and can be retrieved by type.
2. **Given** a project that already has an abstract, **When** a second abstract is attached,
   **Then** the attempt is refused with a message naming the type that is already used.
3. **Given** a project with an abstract and a methods description, **When** its descriptions are
   read, **Then** both are returned, each carrying its own type.
4. **Given** a project, **When** a term from a configured controlled vocabulary is added as a
   keyword, **Then** the term is stored as a reference to that vocabulary rather than as text.
5. **Given** a project, **When** free tags are added, **Then** they are stored and are
   distinguishable from controlled keywords.

---

### User Story 2 - Record when the work happened (Priority: P1)

A researcher records the project's start and its end. The two dates are stored as typed records
rather than as two columns, so that the vocabulary of dates can grow without a migration, and the
record refuses a timeline that runs backwards.

**Why this priority**: Dates are required by every metadata schema the package exports to, and a
project whose end precedes its start will be rejected by those schemas rather than by the portal.

**Independent Test**: Attach a start and an end date to a project, confirm both persist, then attempt
an end date earlier than the start and confirm the save is refused with a message a researcher can
act on.

**Acceptance Scenarios**:

1. **Given** a project, **When** a start date is attached, **Then** it is stored under the start type.
2. **Given** a project with a start date, **When** a second start date is attached, **Then** the
   attempt is refused.
3. **Given** a project with a start date, **When** an end date earlier than that start is attached,
   **Then** the save is refused and the message states that the end cannot precede the start.
4. **Given** a project with a start and an end date, **When** the start is changed to a date after
   the existing end, **Then** that save is refused for the same reason.
5. **Given** a project with an end date and no start date, **When** the end date is saved, **Then**
   it is accepted — there is nothing to contradict.

---

### User Story 3 - Give a project an identifier the outside world recognises (Priority: P1)

A researcher attaches a DOI to a project so that it can be cited, and a grant number so that the
funder's records and the portal's records can be reconciled. Both are stored as typed identifiers,
and the same identifier cannot be attached to two projects.

**Why this priority**: A project record that cannot be cited is not findable, and findability is the
first of the principles the package is named for. Today the vocabulary offers no identifier type
that applies to a project at all.

**Independent Test**: Attach a DOI and a grant number to a project, confirm both persist under the
correct types, and confirm that attaching the same DOI to a second project is refused.

**Acceptance Scenarios**:

1. **Given** a project, **When** a DOI is attached, **Then** it is stored under the DOI type.
2. **Given** a project with a DOI, **When** the same DOI is attached to a different project,
   **Then** the attempt is refused.
3. **Given** a project, **When** a grant number is attached, **Then** it is stored under the grant
   type alongside the DOI.
4. **Given** a project identifier, **When** its type is read, **Then** the available types are those
   that apply to a project, and none of them is an identifier for a person or an organisation.

---

### User Story 4 - Record who paid for the work (Priority: P2)

A researcher records the funder, the funder's own identifier, the award number and the award title.
The record is structured, because the point of holding it is to hand it to DataCite, and DataCite
will not accept an unstructured blob. A project may carry several awards.

**Why this priority**: Funding acknowledgement is a condition of most grants, and it is one of the
fields a publication addon has to supply. It is P2 rather than P1 because a project without it is
still a usable record.

**Independent Test**: Attach two award records to a project with all four parts populated, confirm
both persist, then attempt a record with a malformed funder identifier type and confirm it is
refused.

**Acceptance Scenarios**:

1. **Given** a project, **When** funding is recorded with a funder name, a funder identifier, an
   award number and an award title, **Then** all four are stored under their own names and can be
   read back individually.
2. **Given** a project with one award recorded, **When** a second award is added, **Then** both are
   retained.
3. **Given** a funding record, **When** it names a funder identifier scheme the schema does not
   define, **Then** the record is refused with a message naming the accepted schemes.
4. **Given** a funding record, **When** it carries a funder name and nothing else, **Then** it is
   accepted — the funder's name is the only part DataCite requires.

---

### User Story 5 - Hand a project's metadata to another system (Priority: P1)

A portal administrator exports a project's metadata in a form an external repository can ingest,
carrying not only the project's own fields but the descriptions, dates, identifiers, contributions
and funding attached to it. The export is complete enough that the receiving system needs no manual
completion.

**Why this priority**: Export is the mechanism by which the metadata collected everywhere else in
this specification becomes useful outside the portal. Without it the rest is bookkeeping.

**Independent Test**: Build a project carrying every kind of related record, export it, and confirm
each related record appears in the output under the correct schema key.

**Acceptance Scenarios**:

1. **Given** a project with descriptions, dates, identifiers, contributions and funding, **When** it
   is exported in DataCite's JSON form, **Then** every one of those related records appears in the
   output.
2. **Given** the same project, **When** it is exported as linked data, **Then** the output is valid
   JSON-LD carrying an explicit context.
3. **Given** a project with a DOI, **When** it is exported, **Then** the DOI appears as the record's
   primary identifier rather than as one identifier among others.
4. **Given** a project with no optional metadata beyond its required fields, **When** it is exported,
   **Then** the export succeeds and omits the absent parts rather than emitting empty ones.
5. **Given** several projects selected together, **When** they are exported, **Then** the output
   carries all of them.

---

### User Story 6 - Manage projects as an administrator (Priority: P2)

A portal administrator finds a project by name, identifier or owning organisation, narrows a long
list by status, edits its descriptions, dates and identifiers without leaving the page, sees at a
glance which projects are missing the metadata that matters, and changes the status of many at once.

**Why this priority**: The administrative interface is how a portal is repaired when something has
gone wrong elsewhere. It is P2 because researchers do not use it.

**Independent Test**: Search the project list by each supported term, apply the status filter, add a
description through the inline editor, and run a bulk status change over a selection.

**Acceptance Scenarios**:

1. **Given** the project list, **When** a search term matching a project's name or identifier is
   entered, **Then** that project appears in the results.
2. **Given** the project list, **When** the status filter is applied, **Then** only projects with
   that status remain.
3. **Given** a project open for editing, **When** a description, a date and an identifier are added
   inline and saved, **Then** all three persist without leaving the page.
4. **Given** the project list, **When** it is displayed, **Then** each row shows whether the project
   has an abstract and whether it has a start date.
5. **Given** several projects selected, **When** a bulk status change is applied, **Then** every
   selected project ends in the status named by the action.

---

### User Story 7 - Know who made a project and when it last changed (Priority: P3)

Anyone looking at a project can tell who created it, when it was created, and when it was last
changed. The creator is recorded on the project itself, so the attribution survives the removal of
their contribution record.

**Why this priority**: Attribution is the part that cannot be reconstructed later. It is P3 because
nothing else in this specification depends on it.

**Independent Test**: Create a project as a known user, confirm the creator is recorded against it,
then modify it and confirm the modification timestamp moves while the creator does not.

**Acceptance Scenarios**:

1. **Given** a project is created by a known user, **When** the record is read, **Then** it names
   that user as its creator.
2. **Given** an existing project, **When** any field is changed, **Then** the modification timestamp
   advances and the creator is unchanged.
3. **Given** a project whose creator's account has been removed, **When** the record is read,
   **Then** the project survives and its creator reads as unknown.

---

### Edge Cases

- A project name longer than the field allows is refused by the field's own validation; no truncation
  occurs.
- A project with no owning organisation is a normal state, not an orphan (D-007).
- Two descriptions of the same type are refused at the database as well as in validation, so a
  concurrent write cannot slip past the check.
- A date record whose value is absent is refused; a type without a date carries no meaning.
- Attaching the same identifier value to two projects is refused globally, not merely within a
  project (D-003).
- Deleting a project that has public datasets is blocked. That guard belongs to
  `013-project-crud-views` and is not restated here (D-002).
- A project with several awards recorded exports all of them; DataCite permits repetition.
- Non-ASCII characters in names, descriptions and keywords are stored and exported unchanged.

## Requirements *(mandatory)*

### The project record

- **FR-001**: Each project MUST carry a unique, short, human-readable identifier generated on
  creation, prefixed so that it is recognisable as a project, and not editable afterwards.
- **FR-002**: A project MUST carry a name. A project MAY carry an image, an owning organisation and
  funding information.
- **FR-003**: A project MUST carry a lifecycle status drawn from a controlled set. Every member of
  that set MUST be labelled with the state it names.
- **FR-004**: A project MUST carry a visibility of either private or public.
- **FR-005**: A project MAY name one owning organisation. A project without one MUST be valid.
- **FR-006**: A project MUST support categorisation both by terms drawn from a configured controlled
  vocabulary and by free-form tags, and the two MUST remain distinguishable.
- **FR-007**: Projects MUST be ordered most-recently-modified first by default.

### Descriptions, dates and identifiers

- **FR-008**: A project MUST support several descriptions, each drawn from a controlled set of
  description types, with at most one description per type. The limit MUST be enforced by a database
  constraint as well as by validation.
- **FR-009**: A project MUST support several dates, each drawn from a controlled set of date types,
  with at most one date per type. The set MUST contain a start and an end.
- **FR-010**: The system MUST refuse to save a project date that would place the project's end before
  its start, whichever of the two is being edited, and the message MUST state which two dates
  conflict.
- **FR-011**: A project MUST support several external identifiers, each drawn from a controlled set
  of identifier types that apply to projects. That set MUST include a DOI and a grant number, and
  MUST NOT be the vocabulary used for people and organisations.
- **FR-012**: An identifier value MUST be unique across every record that carries identifiers, so the
  same identifier cannot name two things.

### Contributions

- **FR-013**: A project MUST support contributions associating a person or an organisation with the
  project under one or more roles drawn from a controlled set.
- **FR-014**: The role vocabulary MUST be expressible in DataCite's contributor types, so that export
  needs no translation table.

### Funding

- **FR-015**: Funding MUST be stored in the shape DataCite defines for a funding reference: funder
  name, funder identifier, funder identifier scheme, award number and award title. A project MAY
  carry several.
- **FR-016**: Funder name MUST be required within a funding record; every other part MUST be
  optional. A funder identifier scheme outside the set DataCite defines MUST be refused.

### The creation record

- **FR-017**: A project MUST record the user who created it, and MUST survive that user's removal
  with the creator reading as unknown.
- **FR-018**: A project MUST record when it was created and when it was last changed.

### Administration

- **FR-019**: The administrative interface MUST allow projects to be found by name, by identifier and
  by owning organisation, and MUST allow the list to be narrowed by status.
- **FR-020**: The administrative interface MUST allow a project's descriptions, dates and identifiers
  to be edited from the project's own page.
- **FR-021**: The administrative list MUST show, for each project, whether it carries an abstract and
  whether it carries a start date.
- **FR-022**: Every bulk action that sets a status MUST set the status its label names.

### Export

- **FR-023**: The system MUST export a project's metadata in DataCite's JSON form, carrying its
  descriptions, dates, identifiers, contributions and funding as well as its own fields.
- **FR-024**: The system MUST export a project's metadata as JSON-LD carrying an explicit context.
- **FR-025**: Where a project carries a DOI, the export MUST present it as the record's primary
  identifier.
- **FR-026**: Export MUST omit absent optional metadata rather than emitting empty structures, and
  MUST be available over a selection of several projects.

### Presentation and performance

- **FR-027**: Every string this specification's surfaces present to a user — field labels, help text,
  vocabulary terms, administrative labels and validation messages — MUST be marked for translation in
  a way that resolves at request time rather than at import time.
- **FR-028**: The project model MUST offer a queryset that loads a project together with its
  descriptions, dates, identifiers, contributions and keywords in a bounded number of queries, so
  that a caller assembling a full record does not issue one query per related record.

### Key Entities

- **Project** — the outermost container of the core model. Carries its identifier, name, image,
  status, visibility, owning organisation, funding, creator and timestamps. Related to descriptions,
  dates, identifiers, contributions, keywords, tags and datasets.
- **Project description** — a typed block of prose about the project. One per type.
- **Project date** — a typed date marking a point in the project's life. One per type.
- **Project identifier** — a typed external identifier naming the project outside the portal. Its
  value is unique across all identifiers.
- **Contribution** — the association of a person or an organisation with the project under one or
  more roles.
- **Funding reference** — an award recorded against the project in DataCite's shape.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A project can be given an abstract, a methods description, a start date, an end date, a
  DOI, a grant number and an award record, and every one of them can be read back under its own type.
- **SC-002**: A second description of a type the project already carries is refused every time, both
  through validation and at the database.
- **SC-003**: An end date earlier than the start date is refused every time, from either direction of
  editing, with a message naming both dates.
- **SC-004**: The project identifier vocabulary contains a DOI and a grant number and contains no
  identifier type that names a person or an organisation.
- **SC-005**: A funding record naming a funder and nothing else is accepted; one naming an
  identifier scheme outside DataCite's set is refused.
- **SC-006**: A DataCite export of a fully populated project contains every related record attached
  to it, and the same export of a minimally populated project contains no empty structures.
- **SC-007**: The JSON-LD export parses as JSON-LD and carries a context.
- **SC-008**: Every bulk status action in the administrative interface leaves the selected projects in
  the status its label names.
- **SC-009**: Loading a project together with all its related metadata takes a number of queries that
  does not grow with the number of related records.
- **SC-010**: Every lifecycle status label matches the state it names.

## Assumptions

- The controlled vocabulary machinery, the contribution model and the tagging library are already in
  place and are not changed by this work.
- DataCite's schema is the reference for funding and contributor shapes. Where this specification and
  that schema disagree, the schema wins.
- The portal pages through which a researcher edits a project are specified by
  `013-project-crud-views`. Where a field specified here needs a form control, that document decides
  whether it gets one.
- Translation catalogues do not exist in the repository yet. This work marks strings for translation;
  it does not produce catalogues.

## Out of scope

- The project list, create, edit and delete pages, their forms, the list search box and the filter
  attachment — `013-project-crud-views`.
- The project detail page and the pages for editing descriptions, keywords and dates in the portal.
- Blocking deletion of a project that has public datasets — `013-project-crud-views`.
- An organisation-scoped visibility level between private and public.
- Any mapping from contribution role to permission.
- Full revision history for core records.
- The REST API's representation of a project — `011-restful-api`.
