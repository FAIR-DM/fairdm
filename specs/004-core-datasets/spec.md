# Feature Specification: The dataset record

**Feature Branch**: `004-core-datasets`

**Created**: 2026-01-15 · **Rewritten**: 2026-08-18

**Status**: Draft

**Goals**: G1 — a core data model of projects, datasets, samples, measurements and contributors that
domain schemas can extend and rely on. G12 — private and public data side by side, controlled per
object. G14 — metadata complete enough for a formal-publication addon to submit it unaided. G15 —
external identifiers carried through the record.

**Roadmap**: R4 — datasets.

**Input**: A dataset is the unit a portal cites and distributes. It sits beneath a project, and
samples and measurements hang beneath it. This specification describes the dataset record itself —
the fields it carries, the typed descriptions, dates and identifiers attached to it, the literature
it relates to, who is credited on it, who created it, how an administrator manages it, and the rule
that keeps an unfinished dataset out of sight until its author says otherwise.

It does not describe the pages a researcher uses to create or edit a dataset. Those are
`014-dataset-crud-views`. It does not describe how a dataset's metadata leaves the portal; there is
no export today and it is expected to arrive as an addon. The reasoning behind both exclusions is in
`decisions.md`.

## Clarifications

### Session 2026-08-18

The original text was written on 2026-01-15, before most of the dataset app existed, and it
described five layers at once. Each disagreement with the code was settled and recorded in
`decisions.md`; the questions and answers below are the ones that shaped this document.

- Q: Does this specification own the dataset list, create, edit and delete pages, their forms and the
  filter set behind the list? → A: No. It owns the domain record, its related records, its
  vocabularies, the administrative interface and the creation record. The portal pages belong to
  `014-dataset-crud-views` (D-001).
- Q: Does it own metadata export? → A: No. No export exists today, and it is expected to become an
  addon rather than part of the core record (D-002).
- Q: A dataset cannot be given a type of identifier that means anything for a dataset, because its
  identifier vocabulary lists identifiers for people and organisations. Is that intended? → A: No,
  it is a defect. A dataset needs its own identifier types, and a DOI is the one that matters
  (D-003).
- Q: Should a dataset be private unless someone says otherwise, including in code that forgets to
  ask? → A: Yes. The default way of reading datasets excludes private ones, and reaching them is an
  explicit act (D-004).
- Q: Should deleting a project delete its datasets? → A: Yes for private ones, and a separate guard
  already blocks deletion when any dataset is public. The record's own documentation claiming
  otherwise is what is wrong (D-005).
- Q: Is a licence part of the record or part of the form? → A: Both. The record may carry no
  licence, and wherever a dataset is created the configured default is applied, so a dataset does
  not reach a reader unlicensed by accident (D-007).
- Q: The related-record models carry a second name for each of their two fields — `description_type`
  for `type`, `date` for `value`, and so on. Are those wanted? → A: No. Nothing consumes them, only
  the dataset models have them, and one of them is the direct cause of a filter that raises an error
  whenever it is used (D-012).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Describe a dataset in the terms its field uses (Priority: P1)

A researcher records what a dataset contains. They write an abstract, and separately a description
of the methods that produced the data, and separately the technical detail a reuser needs. Each one
is stored under its own type rather than concatenated into a single field, so that a reader — or
another system — can ask for the abstract alone.

**Why this priority**: Without typed descriptions the record carries prose and nothing else, and
prose is not something an external repository can consume. Methods in particular are what make data
reusable, and the dataset is the record that carries them.

**Independent Test**: Attach an abstract and a methods description to a dataset, confirm both are
retrievable independently under their own types, and confirm a second abstract is refused.

**Acceptance Scenarios**:

1. **Given** a dataset with no descriptions, **When** an abstract is attached, **Then** it is stored
   against that dataset under the abstract type and can be retrieved by type.
2. **Given** a dataset that already has an abstract, **When** a second abstract is attached,
   **Then** the attempt is refused with a message naming the type that is already used.
3. **Given** a dataset, **When** a methods description is attached, **Then** it is accepted — methods
   describe how the data was produced and belong to the dataset.
4. **Given** a dataset with an abstract and a methods description, **When** its descriptions are
   read, **Then** both are returned, each carrying its own type.
5. **Given** the dataset description vocabulary, **When** its members are read, **Then** they are the
   types a dataset carries, and a type outside that set is refused by validation.

---

### User Story 2 - Record when the data was collected and released (Priority: P1)

A researcher records when data collection started and finished, and when the dataset was submitted,
published or withdrawn. The dates are stored as typed records rather than as columns, so the
vocabulary can grow without a migration, and the record refuses a collection period that runs
backwards.

**Why this priority**: Collection dates are what a reader needs to judge whether data is current, and
they are required by every metadata schema a dataset is submitted to. A collection period that ends
before it starts will be rejected by those schemas rather than by the portal.

**Independent Test**: Attach a collection start and a collection end to a dataset, confirm both
persist, then attempt an end earlier than the start and confirm the save is refused with a message a
researcher can act on.

**Acceptance Scenarios**:

1. **Given** a dataset, **When** a collection start date is attached, **Then** it is stored under
   the collection start type.
2. **Given** a dataset with a collection start, **When** a second collection start is attached,
   **Then** the attempt is refused.
3. **Given** a dataset with a collection start, **When** a collection end earlier than that start is
   attached, **Then** the save is refused and the message states that the end cannot precede the
   start.
4. **Given** a dataset with a collection start and end, **When** the start is changed to a date after
   the existing end, **Then** that save is refused for the same reason.
5. **Given** a dataset with a collection end and no collection start, **When** the end is saved,
   **Then** it is accepted — there is nothing to contradict.
6. **Given** the dataset date vocabulary, **When** its members are read, **Then** they are the dates
   a dataset carries and no other.

---

### User Story 3 - Give a dataset an identifier the outside world recognises (Priority: P1)

A researcher attaches a DOI to a dataset so that it can be cited. It is stored as a typed identifier
drawn from a set that means something for a dataset, and the same identifier cannot be attached to
two records.

**Why this priority**: A dataset is the unit that gets cited, and a dataset that cannot be cited is
not findable. Today the vocabulary offers no identifier type that applies to a dataset — the choices
are ORCID, ResearcherID, ROR, Wikidata, ISNI and a funder identifier, none of which names a dataset.

**Independent Test**: Attach a DOI to a dataset, confirm it persists under the DOI type, confirm the
available types contain none that name a person or an organisation, and confirm that attaching the
same DOI to a second record is refused.

**Acceptance Scenarios**:

1. **Given** a dataset, **When** a DOI is attached, **Then** it is stored under the DOI type.
2. **Given** a dataset with a DOI, **When** the same DOI value is attached to a different record,
   **Then** the attempt is refused.
3. **Given** a dataset identifier, **When** its available types are read, **Then** they are types
   that apply to a dataset, and none of them is an identifier for a person or an organisation.
4. **Given** a dataset, **When** two identifiers of different types are attached, **Then** both are
   retained.
5. **Given** a dataset, **When** a second identifier of a type it already carries is attached,
   **Then** the attempt is refused.

---

### User Story 4 - An unfinished dataset stays out of sight (Priority: P1)

A researcher's dataset is private until they decide otherwise, and code that reads datasets without
thinking about visibility does not see it. Reaching a private dataset is an explicit act, written
where a reader of the code can see it.

**Why this priority**: A private dataset is unpublished research. Exposing one is the failure with
the highest cost in the whole package, and the ordinary way of writing a query is the way it
happens. Today the guard exists in the file and is commented out, so every default query returns
private datasets.

**Independent Test**: Create a private and a public dataset, read datasets the ordinary way and
confirm only the public one appears, then ask for private datasets explicitly and confirm both
appear — including when the request already carries a filter.

**Acceptance Scenarios**:

1. **Given** a private and a public dataset, **When** datasets are read with no visibility
   condition, **Then** only the public one is returned.
2. **Given** the same two datasets, **When** private datasets are explicitly included, **Then** both
   are returned.
3. **Given** a query that has already been narrowed by some condition, **When** private datasets are
   explicitly included, **Then** the earlier condition still applies and the result is not widened
   beyond it.
4. **Given** a dataset created with no visibility stated, **When** it is read back, **Then** it is
   private.
5. **Given** the visibility vocabulary, **When** it is read, **Then** it offers private and public
   and nothing else.

---

### User Story 5 - Relate a dataset to the literature about it (Priority: P2)

A researcher names the publication that describes the dataset, and separately records other
literature the dataset relates to, saying in each case what the relationship is — this dataset is
cited by that paper, supplements another, is documented by a third.

**Why this priority**: The link between data and the writing about it is what turns a deposit into a
citable contribution, and the relationship types are the ones an external repository expects. It is
P2 because a dataset with no literature is still a usable record.

**Independent Test**: Name a data publication on a dataset, relate two further items under different
relationship types, and confirm the same item cannot be related twice under the same type.

**Acceptance Scenarios**:

1. **Given** a dataset, **When** a data publication is named, **Then** it is recorded as the
   dataset's reference and at most one such publication can be named.
2. **Given** a dataset, **When** a literature item is related under a stated relationship type,
   **Then** both the item and the type are stored.
3. **Given** a dataset already related to an item under one type, **When** the same item is related
   under a different type, **Then** both relationships are retained.
4. **Given** a dataset already related to an item under one type, **When** the same relationship is
   recorded again, **Then** it is refused.
5. **Given** the available relationship types, **When** they are read, **Then** they are the ones the
   external schema defines.
6. **Given** a dataset whose named data publication is deleted, **When** the dataset is read,
   **Then** the dataset survives with no publication named.

---

### User Story 6 - Manage datasets as an administrator (Priority: P2)

A portal administrator finds a dataset by name, by its generated identifier, by an external
identifier attached to it or by its project, narrows a long list by project, licence or visibility,
edits its descriptions, dates and identifiers without leaving the page, and sees at a glance which
datasets are missing the metadata that matters.

**Why this priority**: The administrative interface is how a portal is repaired when something has
gone wrong elsewhere. It is P2 because researchers do not use it.

**Independent Test**: Search the dataset list by each supported term, apply each filter, and add a
description, a date and an identifier through the inline editors.

**Acceptance Scenarios**:

1. **Given** the dataset list, **When** a search term matching a dataset's name, its generated
   identifier, an external identifier attached to it, or its project's name is entered, **Then** that
   dataset appears in the results.
2. **Given** the dataset list, **When** the project, licence or visibility filter is applied,
   **Then** only datasets matching it remain.
3. **Given** a dataset open for editing, **When** a description, a date and an identifier are added
   inline and saved, **Then** all three persist without leaving the page.
4. **Given** a dataset open for editing, **When** the inline editors are displayed, **Then** the
   number of rows each offers is bounded by the number of types its vocabulary contains.
5. **Given** the dataset list, **When** it is displayed, **Then** each row shows whether the dataset
   has an abstract and whether it has a DOI.
6. **Given** the administrative actions available on the list, **When** they are read, **Then** none
   of them changes the visibility of several datasets at once.
7. **Given** a dataset carrying a DOI, **When** its licence is changed, **Then** the administrator is
   warned that metadata published under the old licence may need updating elsewhere.

---

### User Story 7 - Know who made a dataset and when it last changed (Priority: P3)

Anyone looking at a dataset can tell who created it, when it was created, and when it was last
changed. The creator is recorded on the dataset itself, so the attribution survives the removal of
their contribution record.

**Why this priority**: Attribution is the part that cannot be reconstructed later. It is P3 because
nothing else in this specification depends on it.

**Independent Test**: Create a dataset as a known user, confirm the creator is recorded against it,
then modify it and confirm the modification timestamp moves while the creator does not.

**Acceptance Scenarios**:

1. **Given** a dataset created by a known user, **When** the record is read, **Then** it names that
   user as its creator.
2. **Given** an existing dataset, **When** any field is changed, **Then** the modification timestamp
   advances and the creator is unchanged.
3. **Given** a dataset whose creator's account has been removed, **When** the record is read,
   **Then** the dataset survives and its creator reads as unknown.

---

### User Story 8 - The dataset record itself (Priority: P2)

A dataset carries a generated identifier that names it inside the portal, a name, an optional image,
an optional project, a licence, keywords and free tags. Contributions are recorded against it under
roles that mean something to the systems it is submitted to. Everything it presents to a person is
translatable, and loading it with all its related metadata costs a bounded number of queries however
much metadata it carries.

**Why this priority**: These are the guarantees the other seven stories rest on. It is P2 rather than
P1 because most of them already hold — what is missing is the proof.

**Independent Test**: Create a dataset, confirm its identifier is generated and prefixed, confirm it
is valid without a project, confirm it lists most-recently-changed first, record a contribution with
roles and read them back, and count the queries needed to load it with all its related records.

**Acceptance Scenarios**:

1. **Given** a new dataset, **When** it is saved, **Then** it carries a unique prefixed identifier
   that was generated rather than supplied and cannot be edited afterwards.
2. **Given** a dataset with no project, **When** it is validated, **Then** it is valid.
3. **Given** a dataset created with no licence chosen, **When** it is read back, **Then** it carries
   the portal's configured default licence.
4. **Given** several datasets changed at different times, **When** they are listed with no ordering
   applied, **Then** the most recently changed comes first.
5. **Given** a contribution recorded against a dataset with roles, **When** the contribution is read,
   **Then** its contributor and each of its roles read back.
6. **Given** a dataset carrying many descriptions, dates, identifiers and contributions, **When** it
   is loaded with all of them, **Then** the number of queries does not grow with the number of
   related records.
7. **Given** a dataset with no samples and no measurements, **When** it is asked whether it holds
   data, **Then** it answers that it does not, and it answers that it does once either is added.

---

### Edge Cases

- A dataset name longer than the field allows is refused by the field's own validation; no truncation
  occurs.
- A dataset with no project is a normal state, not an orphan — data migrated from a system with no
  project structure arrives this way.
- Deleting a project deletes the private datasets beneath it. Deletion is blocked outright while any
  of its datasets is public, and that guard belongs to `013-project-crud-views` (D-005).
- Two descriptions, dates or identifiers of the same type are refused at the database as well as in
  validation, so a concurrent write cannot slip past the check.
- A date record whose value is absent is refused; a type without a date carries no meaning.
- Attaching the same identifier value to two records is refused globally, not merely within one
  dataset.
- Two datasets may carry the same name. Nothing distinguishes them but their generated identifiers,
  which is accepted — a name is a label, not a key (D-011).
- A dataset with no samples and no measurements is a normal state. It is reported, not prevented.
- Non-ASCII characters in names, descriptions and keywords are stored unchanged.

## Requirements *(mandatory)*

### The dataset record

- **FR-001**: Each dataset MUST carry a unique, short, human-readable identifier generated on
  creation, prefixed so that it is recognisable as a dataset, and not editable afterwards.
- **FR-002**: A dataset MUST carry a name. A dataset MAY carry an image, a project, a licence and a
  named data publication.
- **FR-003**: A dataset MAY belong to one project. A dataset without one MUST be valid. Deleting a
  project MUST delete the datasets beneath it.
- **FR-004**: A dataset MUST carry a visibility of either private or public, and MUST be private
  unless a visibility is stated.
- **FR-005**: A dataset MUST support categorisation both by terms drawn from a configured controlled
  vocabulary and by free-form tags, and the two MUST remain distinguishable.
- **FR-006**: Datasets MUST be ordered most-recently-modified first by default.
- **FR-007**: Where no licence is chosen at creation, the portal's configured default licence MUST be
  applied. The default MUST be settable by the portal and MUST be CC BY 4.0 where the portal states
  none.
- **FR-008**: A dataset MUST be able to report whether it holds any samples or measurements, in a
  number of queries that does not grow with how many it holds.

### Descriptions, dates and identifiers

- **FR-009**: A dataset MUST support several descriptions, each drawn from a controlled set of
  description types, with at most one description per type. The limit MUST be enforced by a database
  constraint as well as by validation. The set MUST contain an abstract and a methods description.
- **FR-010**: A dataset MUST support several dates, each drawn from a controlled set of date types,
  with at most one date per type. The set MUST contain a collection start and a collection end.
- **FR-011**: The system MUST refuse to save a dataset date that would place the end of data
  collection before its start, whichever of the two is being edited, and the message MUST state which
  two dates conflict.
- **FR-012**: A dataset MUST support several external identifiers, each drawn from a controlled set
  of identifier types that apply to datasets. That set MUST include a DOI, and MUST NOT be the
  vocabulary used for people and organisations.
- **FR-013**: An identifier value MUST be unique across every record that carries identifiers, so the
  same identifier cannot name two things.
- **FR-014**: The related description, date and identifier records MUST expose each field under one
  name only. A second name for a field that no caller uses MUST NOT be carried.

### Literature

- **FR-015**: A dataset MAY name one data publication. Where that publication is deleted, the dataset
  MUST survive with no publication named.
- **FR-016**: A dataset MUST support relationships to any number of literature items, each carrying
  the type of the relationship drawn from the set the external schema defines. The same item MUST NOT
  be related twice under the same type.

### Contributions

- **FR-017**: A dataset MUST support contributions associating a person or an organisation with the
  dataset under one or more roles drawn from a controlled set.
- **FR-018**: The role vocabulary MUST be expressible in DataCite's contributor types, so that a
  future submission needs no translation table.

### Visibility

- **FR-019**: The ordinary way of reading datasets MUST exclude private ones. Including them MUST
  require an explicit call, and that call MUST preserve every condition already applied to the query.
- **FR-020**: Any permission a visibility check consults MUST be declared on the model. A check
  against a permission that is never declared MUST NOT be carried.

### The creation record

- **FR-021**: A dataset MUST record the user who created it, and MUST survive that user's removal
  with the creator reading as unknown.
- **FR-022**: A dataset MUST record when it was created and when it was last changed.

### Administration

- **FR-023**: The administrative interface MUST allow datasets to be found by name, by the dataset's
  own generated identifier, by any external identifier attached to it, and by project, and MUST allow
  the list to be narrowed by project, licence and visibility.
- **FR-024**: The administrative interface MUST allow a dataset's descriptions, dates and identifiers
  to be edited from the dataset's own page, offering no more rows for each than its vocabulary has
  types.
- **FR-025**: The administrative list MUST show, for each dataset, whether it carries an abstract and
  whether it carries a DOI.
- **FR-026**: The administrative interface MUST NOT offer any action that changes the visibility of
  more than one dataset at a time.
- **FR-027**: The generated identifier and the timestamps MUST be presented as unchangeable.
- **FR-028**: Changing the licence of a dataset that carries a DOI MUST warn the administrator that
  metadata published under the previous licence may need updating elsewhere.

### Presentation and performance

- **FR-029**: Every string this specification's surfaces present to a user — field labels, help text,
  vocabulary terms, administrative labels and validation messages — MUST be marked for translation in
  a way that resolves at request time rather than at import time.
- **FR-030**: The dataset model MUST offer a queryset that loads a dataset together with its
  descriptions, dates, identifiers, contributions and keywords in a bounded number of queries, so
  that a caller assembling a full record does not issue one query per related record.
- **FR-031**: The record's own documentation MUST describe the behaviour the record has. Documented
  behaviour that the code does not implement MUST be removed rather than left standing.

### Key Entities

- **Dataset** — the unit of citation and distribution. Carries its identifier, name, image,
  visibility, licence, project, data publication, creator and timestamps. Related to descriptions,
  dates, identifiers, contributions, keywords, tags, literature, samples and measurements.
- **Dataset description** — a typed block of prose about the dataset. One per type.
- **Dataset date** — a typed date marking a point in the dataset's life. One per type.
- **Dataset identifier** — a typed external identifier naming the dataset outside the portal. Its
  value is unique across all identifiers.
- **Dataset literature relation** — the association of a dataset with a literature item under a
  stated relationship type.
- **Contribution** — the association of a person or an organisation with the dataset under one or
  more roles.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A dataset can be given an abstract, a methods description, a collection start, a
  collection end and a DOI, and every one of them can be read back under its own type.
- **SC-002**: A second description, date or identifier of a type the dataset already carries is
  refused every time, both through validation and at the database.
- **SC-003**: A collection end earlier than the collection start is refused every time, from either
  direction of editing, with a message naming both dates.
- **SC-004**: The dataset identifier vocabulary contains a DOI and contains no identifier type that
  names a person or an organisation. Each of the three dataset vocabularies is asserted by naming the
  members it contains, not by iterating whatever it happens to hold.
- **SC-005**: Reading datasets without stating a visibility never returns a private one, and
  including private datasets after a query has already been narrowed returns no record the narrowing
  excluded.
- **SC-006**: The same literature item can be related to a dataset under two different types and not
  twice under one, and deleting a dataset's named data publication leaves the dataset intact.
- **SC-007**: Every administrative search term in FR-023 finds a dataset that matches it, and every
  filter in FR-023 removes the datasets that do not.
- **SC-008**: Loading a dataset together with all its related metadata takes a number of queries that
  does not grow with the number of related records.
- **SC-009**: No test covering behaviour in this specification is skipped, and no test in it passes
  when the behaviour it names is removed.
- **SC-010**: Every statement the dataset models, admin and vocabularies make about their own
  behaviour is true of the code as it stands.

## Assumptions

- The controlled vocabulary machinery, the contribution model, the licence field and the tagging
  library are already in place and are not changed by this work.
- DataCite's schema is the reference for relationship types and contributor roles.
- The portal pages through which a researcher creates and edits a dataset are specified by
  `014-dataset-crud-views`. Where a field specified here needs a form control, that document decides
  whether it gets one.
- The image field's dimensions, thumbnails and upload guidance are specified by
  `015-image-field-spec`.
- The literature package supplies the item this record relates to; its own model is not changed here.
- Translation catalogues do not exist in the repository yet. This work marks strings for translation;
  it does not produce catalogues.

## Out of scope

- Metadata export in any form — no export exists today and it is expected to arrive as an addon
  (D-002).
- The dataset list, create, edit and delete pages, their forms, the list search box and the filter
  set behind it — `014-dataset-crud-views`.
- The dataset detail page and the portal pages for editing descriptions, keywords and key dates.
- The image field's dimensions and thumbnails — `015-image-field-spec`.
- Funding recorded against a dataset — deferred to the work that gives projects and datasets a shared
  funding record.
- Blocking deletion of a project that has public datasets — `013-project-crud-views`.
- Which contribution roles confer which rights, and the granting of permissions when a dataset is
  created.
- Enforcing visibility consistently across the portal, the API and the collection tables — this
  specification makes the record's own default private and stops there.
- The REST API's representation of a dataset — `011-restful-api`.
