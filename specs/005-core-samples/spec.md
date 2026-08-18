# Feature Specification: The sample record

**Feature Branch**: `005-core-samples`

**Created**: 2026-01-16 · **Rewritten**: 2026-08-18

**Status**: Draft

**Goals**: G1 — a core data model of projects, datasets, samples, measurements and contributors that
domain schemas can extend and rely on. G2 — registering a model is enough to get a working portal
surface. G12 — private and public data side by side, controlled per object. G15 — external
identifiers for people, organisations and samples carried through the record.

**Roadmap**: R5 — samples.

**Input**: A sample is a physical or digital specimen collected as part of a dataset. It is the
polymorphic base every portal-defined specimen type inherits from, whatever the science: a rock, a
water column, a tissue culture, an alloy coupon. This specification describes the sample record
itself: the fields it carries, the typed descriptions, dates and identifiers attached to it, the
links back to the samples it came from, who is credited on it, how its access follows from the
dataset it belongs to, how an administrator manages it, and the form and filter behaviour a portal
developer inherits when defining a sample type of their own.

Its metadata follows IGSN — the International Generic Sample Number — as its reference schema.
IGSN is deliberately domain-independent, and following it is what keeps this record neutral between
sciences rather than shaped by one.

It does not describe the pages a researcher uses to create, list or edit a sample. Those belong to
the CRUD specification for samples, roadmap item R16, which does not exist yet. The reasoning behind
that line, and behind everything else this document settles, is in `decisions.md`.

## Clarifications

### Session 2026-08-18

The original text was written on 2026-01-16, before most of the sample app existed. It described
five layers at once, and the file itself is damaged — three of its user stories and two of its
section headings appear twice, with different content. Each disagreement with the code was settled
and recorded in `decisions.md`; the questions and answers below are the ones that shaped this
document.

- Q: Does this specification own the sample pages, the forms behind them and the filter set behind
  the list? → A: It owns the record, and it owns `SampleFormMixin` and `SampleFilterMixin` because
  those are what a portal developer inherits from rather than what a page constructs. The pages and
  the concrete `SampleForm` and `SampleFilter` belong to the CRUD specification (D-001).
- Q: A sample's status is drawn from a vocabulary of Complete, Ongoing, Planned and Unknown, fetched
  over plain HTTP from a third-party host. Those describe a data-collection activity, not a
  specimen. Is that intended? → A: No, it is a defect. A sample status vocabulary describes physical
  custody — available, in use, stored, destroyed, unknown — and the remote fetch goes (D-002).
- Q: A sample cannot be given an IGSN, because its identifier vocabulary lists identifiers for
  people, organisations and projects and contains no IGSN member at all. Is that intended? → A: No,
  it is a defect. A sample needs its own identifier types, and they are IGSN and DOI (D-003).
- Q: Should the single `child_of` relationship type grow into a vocabulary carrying derived-from and
  split-from? → A: No. At most child-of, and expanding it is overreach for this specification
  (D-004).
- Q: Is following the IGSN schema a geoscience bias that should be demoted? → A: No — the opposite.
  IGSN is generic by design, and following it is what makes the record domain-neutral (D-005).
- Q: The vocabulary validators on descriptions, dates and identifiers raise a type error rather than
  a validation error, and always have. Which is right, the specification or the code? → A: The
  specification. The validators are repaired (D-006).
- Q: The queryset's ancestor and descendant traversals run in the opposite direction to the model's
  own. Which direction is right? → A: The model's, which is the direction the stored data uses. The
  duplicate traversal is removed rather than corrected in two places (D-007).
- Q: Should a sample carry a material field, as IGSN alignment would suggest? → A: No. A material
  vocabulary spanning every science is the same overreach as the relationship vocabulary (D-012).
- Q: What format should an IGSN be validated against, given that sample identifiers may be moving to
  DataCite? → A: Whatever the issuing authority defines, settled from its documentation during
  research rather than frozen into this document from an unverified report (D-014).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Define a sample type and get a working record (Priority: P1)

A portal developer defines a specimen type for their own science — a rock sample with a mineral
content, a tissue sample with a preservation method — by inheriting from the sample record and
registering it. Registration alone produces the form, filter set, table and administrative entry for
that type. Querying samples returns each one as the type it actually is, and the bare base record
cannot be created by anyone.

**Why this priority**: This is what the sample record is for. Every other story in this document
describes something a portal-defined type inherits, and none of it matters if defining a type does
not work.

**Independent Test**: Register two sample types with different extra fields, confirm each receives a
generated form, filter set, table and administrative entry carrying its own fields, query all
samples and confirm each comes back as its own type, then attempt to create a bare base sample by
every route and confirm each is refused.

**Acceptance Scenarios**:

1. **Given** a sample type inheriting from the sample record, **When** it is registered with a
   configuration naming its fields, **Then** a form, a filter set, a table and an administrative
   entry are generated for it without any of them being written by hand.
2. **Given** two registered sample types holding records, **When** samples are queried without
   naming a type, **Then** each result is an instance of its own type and carries that type's own
   fields.
3. **Given** a sample type whose configuration inherits the base sample configuration, **When** it
   omits a component setting, **Then** it receives the base defaults rather than restating them.
4. **Given** an attempt to create a bare base sample, **When** it is made through validation, a
   form, the administrative interface, or the manager directly, **Then** every route refuses it.
5. **Given** the registered sample types, **When** the administrative interface offers to add a
   sample, **Then** it asks which type, and routes to that type's own administrative entry.

---

### User Story 2 - Describe a sample in the terms its discipline uses (Priority: P1)

A researcher records how a specimen was collected, how it was prepared, and how it is stored. Each
one is stored under its own type rather than concatenated into a single field, so a reader — or
another system — can ask for the collection method alone. A type outside the sample vocabulary is
refused.

**Why this priority**: Typed descriptions are what make a specimen record interpretable by something
other than a person reading prose. The validation that keeps the types meaningful has never run.

**Independent Test**: Attach descriptions of two different types to a sample, confirm both are
retrievable independently under their own types, and confirm that a type belonging to a different
record's vocabulary is refused by validation.

**Acceptance Scenarios**:

1. **Given** a sample with no descriptions, **When** a description of a type in the sample
   vocabulary is attached, **Then** it is stored under that type and can be retrieved by type.
2. **Given** a sample, **When** a description is attached whose type is not in the sample
   vocabulary, **Then** validation refuses it and names the offending type.
3. **Given** a sample with descriptions of two types, **When** its descriptions are read, **Then**
   both are returned, each carrying its own type.
4. **Given** the sample description vocabulary, **When** its members are read, **Then** they are the
   types a sample carries, asserted by naming them rather than by iterating whatever it holds.
5. **Given** a sample description, **When** it is fully validated, **Then** validation completes and
   returns a verdict rather than raising an error of its own.

---

### User Story 3 - Record when a sample was collected, prepared and stored (Priority: P1)

A researcher records the dates in a specimen's life: when it was collected, when it was prepared,
when it was archived, when it was destroyed. The dates are stored as typed records rather than as
columns, so the vocabulary can grow without a migration, and a type outside the sample vocabulary is
refused.

**Why this priority**: Collection date is the single piece of metadata every specimen schema asks
for, and the same validator defect that affects descriptions affects dates.

**Independent Test**: Attach dates of two types to a sample, confirm both persist under their own
types, and confirm a type outside the sample vocabulary is refused by validation.

**Acceptance Scenarios**:

1. **Given** a sample, **When** a date of a type in the sample vocabulary is attached, **Then** it
   is stored under that type.
2. **Given** a sample, **When** a date is attached whose type is not in the sample vocabulary,
   **Then** validation refuses it and names the offending type.
3. **Given** the sample date vocabulary, **When** its members are read, **Then** they are the dates
   a sample carries, asserted by naming them.
4. **Given** a sample date, **When** it is fully validated, **Then** validation completes and
   returns a verdict rather than raising an error of its own.

---

### User Story 4 - Give a sample an identifier the outside world recognises (Priority: P1)

A researcher attaches an IGSN to a specimen so that it can be cited and resolved outside the portal,
or a DOI where the portal mints those instead. Each is stored as a typed identifier drawn from a set
that means something for a sample, its format is checked against what its issuing authority defines,
and the same identifier cannot name two things.

**Why this priority**: A specimen that cannot be identified outside the portal is not findable, and
identifiers are the whole reason the record follows IGSN. Today the type list offers ORCID,
ResearcherID, ROR, Wikidata, ISNI, a funder identifier, a grant number and a proposal identifier —
none of which names a sample — and no IGSN at all.

**Independent Test**: Attach an IGSN to a sample and confirm it persists under the IGSN type,
confirm the available types contain none that name a person, an organisation or a project, confirm
a malformed IGSN is refused, and confirm the same identifier value cannot be attached to a second
record.

**Acceptance Scenarios**:

1. **Given** a sample, **When** an IGSN is attached, **Then** it is stored under the IGSN type.
2. **Given** a sample, **When** a DOI is attached, **Then** it is stored under the DOI type.
3. **Given** a sample identifier, **When** its available types are read, **Then** they are types
   that name a sample, and none of them names a person, an organisation or a project.
4. **Given** a sample, **When** an identifier value that does not match the format its issuing
   authority defines is attached, **Then** validation refuses it and the message names the expected
   format.
5. **Given** a sample carrying an identifier, **When** the same value is attached to any other
   record, **Then** the attempt is refused.
6. **Given** a sample, **When** a second identifier of a type it already carries is attached,
   **Then** the attempt is refused.

---

### User Story 5 - A sample's status says where the specimen physically is (Priority: P1)

A researcher records whether a specimen is available, in use, in storage, destroyed, or of unknown
whereabouts. The terms describe custody of a physical object, and the record does not reach across
the network to a third party to find out what they are.

**Why this priority**: Status is the field a curator reads before promising a specimen to someone.
Today its terms describe whether a data-collection activity is complete, which says nothing about
a specimen, and the vocabulary is fetched over plain HTTP from a host outside the project.

**Independent Test**: Read the status vocabulary and confirm it names custody states, create a
sample without stating a status and confirm it reads as unknown, move a sample between every pair of
states and confirm none is refused, and confirm nothing in the record's definition reaches the
network.

**Acceptance Scenarios**:

1. **Given** the sample status vocabulary, **When** its members are read, **Then** they are states a
   physical specimen can be in, asserted by naming them.
2. **Given** a sample created with no status stated, **When** it is read back, **Then** its status is
   unknown.
3. **Given** a sample in any status, **When** its status is changed to any other, **Then** the change
   is accepted, including from destroyed back to available, because a specimen recorded as destroyed
   in error must be correctable.
4. **Given** a portal with no network access, **When** the sample record is loaded and a sample is
   created, **Then** both succeed.
5. **Given** samples holding status values from the previous vocabulary, **When** the migration has
   run, **Then** each reads as unknown rather than as a term that no longer exists.

---

### User Story 6 - Access to a sample follows the dataset it belongs to (Priority: P1)

Someone who may read a dataset may read its samples. Someone who may change a dataset may change and
add samples within it. Nobody has to be granted rights on each specimen individually, and rights
granted directly on a specimen still hold.

**Why this priority**: Samples are the records a portal holds most of, and granting rights per
specimen does not scale. This is also the mechanism the framework's access rules will build on.

**Independent Test**: Grant a user rights on a dataset alone and confirm they hold the corresponding
rights on its samples, grant rights on a single sample and confirm those hold too, and confirm a
user with rights on neither holds nothing.

**Acceptance Scenarios**:

1. **Given** a user granted the right to read a dataset, **When** their rights over a sample in that
   dataset are checked, **Then** they may read it.
2. **Given** a user granted the right to change a dataset, **When** their rights over a sample in
   that dataset are checked, **Then** they may change it, delete it and add samples to that dataset.
3. **Given** a user granted a right directly on one sample, **When** their rights over that sample
   are checked, **Then** the direct grant holds independently of any dataset grant.
4. **Given** a user with no rights on a sample or its dataset, **When** their rights are checked,
   **Then** they hold none.
5. **Given** the rights the sample record declares, **When** they are read, **Then** every right any
   check consults is among them.

---

### User Story 7 - Inherit form and filter behaviour when defining a sample type (Priority: P2)

A portal developer writing a form or a filter set for their own specimen type inherits the common
sample behaviour instead of restating it: the fields every sample has, configured with the controls
that suit them, and the filters a reader expects. What they inherit is what the registry generates
for a type that supplies neither.

**Why this priority**: This is the developer-facing half of the registry promise, and the original
clarification session called it very important. The filter mixin currently declares filters that are
silently discarded before an inheriting class ever sees them.

**Independent Test**: Write a form and a filter set for a sample type that inherit the mixins and add
one field each, confirm the inherited fields and filters are all present alongside the new ones,
then register a type supplying neither and confirm the generated form and filter set carry the same
inherited behaviour.

**Acceptance Scenarios**:

1. **Given** a filter set for a sample type that inherits the sample filter mixin, **When** its
   filters are read, **Then** every filter the mixin declares is present alongside the type's own.
2. **Given** a form for a sample type that inherits the sample form mixin, **When** it is rendered,
   **Then** the common sample fields carry the controls the mixin configures.
3. **Given** a sample form that is given the requesting user, **When** its dataset choices are read,
   **Then** they are the datasets that user may add samples to and no others.
4. **Given** a sample form that is given no user, **When** its dataset choices are read, **Then**
   they contain no dataset that user has not been shown to be entitled to.
5. **Given** a registered sample type supplying neither a form nor a filter set, **When** the
   registry generates them, **Then** both carry the mixins' behaviour rather than plain defaults.
6. **Given** a sample form, **When** its fields are rendered, **Then** each carries the guidance text
   the form defines for it.

---

### User Story 8 - Track where a sample came from (Priority: P2)

A researcher records that one specimen came from another — a subsample of a core, a slide cut from a
block — and can walk that chain in both directions, from a parent to everything descended from it
and from a specimen back to its origin. A specimen cannot be its own parent, and the chain cannot
close into a loop.

**Why this priority**: Provenance is what makes a derived measurement traceable to the material it
was made on. It is P2 because a specimen with no parent is a complete record.

**Independent Test**: Build a chain three deep, confirm children, parents and all descendants are
returned correctly from each end, then attempt to relate a specimen to itself and to close a
two-step loop, and confirm both are refused however they are attempted.

**Acceptance Scenarios**:

1. **Given** two samples, **When** one is recorded as having come from the other, **Then** the link
   is stored and readable from both ends.
2. **Given** a chain of samples three deep, **When** all descendants of the first are requested,
   **Then** every sample below it is returned and none above it.
3. **Given** the same chain, **When** the ancestors of the last are requested, **Then** every sample
   above it is returned and none below it.
4. **Given** descendants requested with a depth limit, **When** the limit is one, **Then** only
   direct children are returned.
5. **Given** a sample, **When** it is recorded as having come from itself, **Then** the attempt is
   refused, whether through validation or saved directly.
6. **Given** two samples already linked, **When** the reverse link is recorded, **Then** the attempt
   is refused, whether through validation or saved directly.
7. **Given** the same link recorded twice, **When** the second is saved, **Then** it is refused.
8. **Given** a sample hierarchy, **When** it is traversed, **Then** one implementation of that
   traversal exists, and the record's own helpers and its queryset agree on direction.

---

### User Story 9 - Manage samples as an administrator (Priority: P2)

A portal administrator finds a specimen by its name, its laboratory identifier or its generated
identifier, narrows a long list by dataset, status or type, and edits its descriptions, dates,
identifiers, credits and provenance links without leaving the page, whichever specimen type it is.

**Why this priority**: The administrative interface is how a portal is repaired when something has
gone wrong elsewhere, and it is the only route to sample data until the portal pages exist. It is P2
because researchers do not use it.

**Independent Test**: Search the sample list by each supported term, apply each filter, and add a
description, a date, an identifier, a credit and a provenance link through the inline editors of a
registered sample type.

**Acceptance Scenarios**:

1. **Given** the sample list, **When** a term matching a sample's name, its laboratory identifier or
   its generated identifier is entered, **Then** that sample appears in the results.
2. **Given** the sample list, **When** the dataset, status or type filter is applied, **Then** only
   samples matching it remain.
3. **Given** a sample open for editing, **When** a description, a date, an identifier, a credit and a
   provenance link are added inline and saved, **Then** all five persist without leaving the page.
4. **Given** a sample open for editing, **When** the inline editors are displayed, **Then** the
   number of rows each offers is bounded by the number of types its vocabulary contains.
5. **Given** the sample list, **When** it is displayed, **Then** each row names the type of specimen
   it is.
6. **Given** the generated identifier and the timestamps, **When** a sample is open for editing,
   **Then** they are presented as unchangeable.
7. **Given** a registered sample type, **When** its administrative entry is opened, **Then** it
   offers the same inline editors as every other sample type.

---

### User Story 10 - The sample record itself (Priority: P2)

A sample carries a generated identifier that names it inside the portal, a name, an optional
laboratory identifier of the researcher's own devising, an optional image, an optional collection
location, keywords and free tags. It belongs to exactly one dataset and does not outlive it.
Contributions are recorded against it under roles that mean something to the systems it is submitted
to. Everything it presents to a person is translatable, and loading a sample with all its related
records costs a number of queries that does not grow with how many there are.

**Why this priority**: These are the guarantees the other nine stories rest on. It is P2 rather than
P1 because most of them already hold. What is missing is the proof.

**Independent Test**: Create a sample, confirm its identifier is generated and prefixed, confirm two
samples in different datasets may share a laboratory identifier, delete a dataset and confirm its
samples go with it, record a contribution with roles and read them back, and count the queries
needed to load a list of samples with all their related records.

**Acceptance Scenarios**:

1. **Given** a new sample, **When** it is saved, **Then** it carries a unique prefixed identifier
   that was generated rather than supplied and cannot be edited afterwards.
2. **Given** two samples in different datasets, **When** both are given the same laboratory
   identifier, **Then** both are accepted, because that identifier is the researcher's own and means
   nothing outside their dataset.
3. **Given** a sample, **When** its dataset is deleted, **Then** the sample is deleted with it.
4. **Given** a sample with a collection location, **When** that location is deleted, **Then** the
   deletion is refused while the sample refers to it.
5. **Given** a contribution recorded against a sample with roles, **When** the contribution is read,
   **Then** its contributor and each of its roles read back.
6. **Given** many samples each carrying descriptions, dates, identifiers and contributions, **When**
   they are loaded with all of them, **Then** the number of queries does not grow with the number of
   samples or of related records.
7. **Given** a sample, **When** keywords from a controlled vocabulary and free tags are attached,
   **Then** both are stored and remain distinguishable.
8. **Given** any string this record presents to a person, **When** the active language changes,
   **Then** the string resolves in that language rather than the one in force when the code was
   imported.

---

### Edge Cases

- A sample's laboratory identifier may be absent, and may repeat across datasets. It is the
  researcher's own label, not a key.
- Two samples may carry the same name. Nothing distinguishes them but their generated identifiers.
- A sample with no location is a normal state; not every specimen has a collection point, and a
  digital specimen has none at all.
- Deleting a dataset deletes its samples. Deleting a location a sample refers to is refused.
- A sample with no measurements is a normal state, not an incomplete record.
- A status may move in any direction, including out of destroyed — a specimen recorded as destroyed
  in error must be correctable.
- A specimen type registered by a portal and later removed from the code leaves rows behind. Reading
  them degrades to the base record rather than failing.
- Attaching the same identifier value to two records is refused globally, not merely within one
  dataset.
- Non-ASCII characters in names, descriptions and keywords are stored unchanged.

## Requirements *(mandatory)*

### The sample record

- **FR-001**: Each sample MUST carry a unique, short, human-readable identifier generated on
  creation, prefixed so that it is recognisable as a sample, and not editable afterwards.
- **FR-002**: A sample MUST carry a name. A sample MAY carry a laboratory identifier of the
  researcher's own devising, an image, and a collection location.
- **FR-003**: A laboratory identifier MUST NOT be required to be unique. Two samples in different
  datasets carrying the same one MUST both be valid.
- **FR-004**: A sample MUST belong to exactly one dataset, and MUST be deleted when that dataset is
  deleted.
- **FR-005**: Deleting a location a sample refers to MUST be refused while any sample refers to it.
- **FR-006**: A sample MUST support categorisation both by terms drawn from a controlled vocabulary
  and by free-form tags, and the two MUST remain distinguishable.
- **FR-007**: A sample MUST record when it was created and when it was last changed.
- **FR-008**: A sample MUST support contributions associating a person or an organisation with it
  under one or more roles drawn from a controlled set.

### Polymorphism and the registry

- **FR-009**: The sample record MUST be a polymorphic base from which a portal defines its own
  specimen types, and querying samples MUST return each as the type it was created as.
- **FR-010**: The base sample record MUST NOT be creatable directly, by any route — validation, a
  form, the administrative interface, or the manager. Only a defined specimen type may be created.
- **FR-011**: Registering a specimen type MUST produce its form, filter set, table and
  administrative entry without any of them being written by hand, using the framework's existing
  registry rather than a mechanism of this record's own.
- **FR-012**: The framework MUST supply a base registry configuration that a specimen type's
  configuration inherits component defaults from, and the framework's own reference implementation
  MUST use it.
- **FR-013**: A specimen type registered by a portal and later removed from the code MUST leave its
  rows readable as base sample records rather than failing.

### Descriptions, dates and identifiers

- **FR-014**: A sample MUST support several descriptions, each drawn from a controlled set of
  description types scoped to samples. A type outside that set MUST be refused by validation.
- **FR-015**: A sample MUST support several dates, each drawn from a controlled set of date types
  scoped to samples. A type outside that set MUST be refused by validation.
- **FR-016**: A sample MUST support several external identifiers, each drawn from a controlled set
  of identifier types that apply to samples. That set MUST contain an IGSN and a DOI, and MUST NOT
  be the vocabulary used for people, organisations or projects.
- **FR-017**: An IGSN MUST be validated against the format its issuing authority defines. Which
  format that is MUST be established from that authority's documentation rather than assumed, and
  the check MUST be reachable — a value of a type the vocabulary does not contain can never reach a
  format check.
- **FR-018**: An identifier value MUST be unique across every record that carries identifiers, so
  the same identifier cannot name two things.
- **FR-019**: Validating a sample description, date or identifier MUST return a verdict. A validator
  that raises an error of its own instead of accepting or refusing the value MUST NOT be carried.
- **FR-020**: The sample record's metadata MUST be sufficient to describe a specimen in the terms
  IGSN defines, so that a portal minting IGSNs needs nothing this record does not hold.

### Status

- **FR-021**: A sample MUST carry a status drawn from a controlled set describing the custody of a
  physical specimen. The set MUST contain available, in use, stored, destroyed and unknown.
- **FR-022**: A sample created with no status stated MUST read as unknown.
- **FR-023**: A status MUST be changeable to any other status without restriction, in either
  direction.
- **FR-024**: No vocabulary this record depends on MAY be fetched from a remote host at import time
  or at save time. Loading the record and creating a sample MUST succeed with no network access.
- **FR-025**: Samples holding a status value from the previous vocabulary MUST be migrated to
  unknown, because no term in that vocabulary describes a custody state.

### Provenance

- **FR-026**: A sample MUST support recording that it came from another sample, readable from both
  ends.
- **FR-027**: A sample MUST NOT be recordable as having come from itself, and two samples MUST NOT
  each be recordable as having come from the other. Both MUST be refused when saved directly, not
  only during validation.
- **FR-028**: The same link between the same two samples MUST NOT be recordable twice.
- **FR-029**: The record MUST support retrieving a sample's direct children, its direct parents, all
  its descendants and all its ancestors, with an optional depth limit on the two unbounded ones.
- **FR-030**: Exactly one implementation of the hierarchy traversal MUST exist. Where the record's
  own helpers and its queryset both offer it, one MUST delegate to the other.

### Access

- **FR-031**: A user's rights over a sample MUST derive from their rights over the dataset it
  belongs to: reading a dataset confers reading its samples; changing a dataset confers changing and
  deleting its samples and adding samples to it.
- **FR-032**: Rights granted directly on a sample MUST hold independently of any dataset grant.
- **FR-033**: Every right any check consults MUST be declared on the sample record.

### Reusable form and filter behaviour

- **FR-034**: The framework MUST supply a form mixin that configures the controls for the fields
  every sample carries, and a filter mixin that supplies the filters a reader expects.
- **FR-035**: Every filter the filter mixin declares MUST be present on a filter set that inherits
  it. A filter declared where the framework's filtering library will not collect it MUST NOT be
  carried.
- **FR-036**: A sample form given the requesting user MUST offer only the datasets that user may add
  samples to. A sample form given no user MUST NOT offer any dataset that user has not been shown to
  be entitled to.
- **FR-037**: What the registry generates for a specimen type supplying neither a form nor a filter
  set MUST carry the mixins' behaviour rather than the framework's plain defaults.
- **FR-038**: Guidance text a form defines for a field MUST reach the rendered field.

### Administration

- **FR-039**: The administrative interface MUST allow samples to be found by name, by laboratory
  identifier and by the sample's own generated identifier, and MUST allow the list to be narrowed by
  dataset, status and specimen type.
- **FR-040**: The administrative interface MUST allow a sample's descriptions, dates, identifiers,
  contributions and provenance links to be edited from the sample's own page, offering no more rows
  for each than its vocabulary has types.
- **FR-041**: Every registered specimen type MUST offer the same inline editors as every other.
- **FR-042**: The administrative list MUST name the specimen type of each row.
- **FR-043**: The generated identifier and the timestamps MUST be presented as unchangeable.

### Presentation and performance

- **FR-044**: The sample record MUST offer a queryset that loads samples together with their
  dataset, location, descriptions, dates, identifiers, contributions and keywords in a number of
  queries that does not grow with the number of samples or of related records.
- **FR-045**: Queryset methods MUST be chainable with one another and with ordinary query
  operations.
- **FR-046**: Every string this specification's surfaces present to a user — field labels, guidance
  text, vocabulary terms, administrative labels and validation messages — MUST be marked for
  translation in a way that resolves at request time rather than at import time.
- **FR-047**: The record's own documentation MUST describe the behaviour the code has. Documented
  behaviour the code does not implement MUST be removed rather than left standing.

### Key Entities

- **Sample** — a physical or digital specimen belonging to one dataset. The polymorphic base every
  portal-defined specimen type inherits from. Carries its generated identifier, name, laboratory
  identifier, image, status, location, keywords, tags and timestamps. Related to descriptions,
  dates, identifiers, contributions, measurements and other samples.
- **Sample description** — a typed block of prose about the specimen, drawn from the sample
  description vocabulary.
- **Sample date** — a typed date marking a point in the specimen's life, drawn from the sample date
  vocabulary.
- **Sample identifier** — a typed external identifier naming the specimen outside the portal. Its
  value is unique across all identifiers.
- **Sample relation** — the record that one sample came from another.
- **Contribution** — the association of a person or an organisation with the sample under one or
  more roles.
- **Dataset** — the record a sample belongs to, and the record its access rights derive from.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A specimen type is defined and registered, and its form, filter set, table and
  administrative entry all exist and carry that type's own fields, with nothing written by hand.
- **SC-002**: Creating a bare base sample is refused through validation, through a form, through the
  administrative interface and through the manager. The framework's own test fixtures do not create
  one.
- **SC-003**: A description, a date and an identifier of a type outside the sample vocabularies are
  each refused by validation with a message naming the type, and each of the three sample
  vocabularies is asserted by naming the members it contains rather than by iterating whatever it
  holds.
- **SC-004**: A sample can be given an IGSN and a DOI and both read back under their own types; the
  sample identifier vocabulary contains no type naming a person, an organisation or a project; and a
  malformed IGSN is refused.
- **SC-005**: The status vocabulary names custody states, a sample created without one reads as
  unknown, every transition between states is accepted, and loading the record and creating a sample
  both succeed with no network access.
- **SC-006**: A user holding rights on a dataset alone holds the corresponding rights on its
  samples; a user holding rights on one sample alone holds them on that sample; a user holding
  neither holds nothing.
- **SC-007**: A filter set inheriting the filter mixin carries every filter the mixin declares, and
  the form and filter set the registry generates for a type supplying neither carry the same
  behaviour.
- **SC-008**: A three-deep chain returns the correct children, parents, descendants and ancestors
  from each end, a depth limit of one returns direct children only, and self-reference, a two-step
  loop and a duplicate link are each refused when saved directly.
- **SC-009**: Every search term and every filter in FR-039 finds or removes the samples it names,
  and a description, date, identifier, contribution and provenance link can each be added inline.
- **SC-010**: Loading a list of samples together with all their related records takes a number of
  queries that does not grow with the number of samples or of related records.
- **SC-011**: No test covering behaviour in this specification is skipped, and no test in it passes
  when the behaviour it names is removed.
- **SC-012**: Every statement the sample models, admin, forms, filters and vocabularies make about
  their own behaviour is true of the code as it stands.

## Assumptions

- The controlled vocabulary machinery, the contribution model, the polymorphic model library, the
  object-level permission library and the tagging library are already in place and are not changed
  by this work.
- IGSN is the reference schema for specimen metadata, and is domain-independent by design.
- The registry described by `002-fairdm-registry` generates components from a registered
  configuration, and this work uses it rather than replacing it.
- The dataset record specified by `004-core-datasets` supplies the container a sample belongs to and
  the rights its access derives from; its own model is not changed here.
- The location model supplies the collection point a sample refers to; its own model is not changed
  here, and geographic querying is not part of this work.
- The pages through which a researcher creates, lists and edits a sample are specified by the CRUD
  specification for samples, roadmap item R16. Where a field specified here needs a form control on
  a page, that document decides whether it gets one.
- Translation catalogues do not exist in the repository yet. This work marks strings for
  translation; it does not produce catalogues.

## Out of scope

- The sample list, detail, create, edit and delete pages, the concrete form and filter set those
  pages would instantiate, and the view-level permission checks — the CRUD specification for
  samples, roadmap item R16 (D-001).
- A material field and a vocabulary of materials spanning every science (D-012).
- Relationship types beyond one sample having come from another (D-004).
- Geographic querying — bounding box, radius, coordinate reference systems — and any change to the
  location model.
- Registering a sample with an external identifier authority. Identifiers are stored, not minted.
- Import and export of sample data beyond what the administrative interface offers.
- The REST API's representation of a sample — `011-restful-api`.
- Enforcing visibility consistently across the portal, the API and the collection tables. This
  specification makes a sample's rights derive from its dataset and stops there.
- Measurements recorded against a sample — `006-core-measurements`.
