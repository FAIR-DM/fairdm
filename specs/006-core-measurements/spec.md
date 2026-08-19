# Feature Specification: The measurement record

**Feature Branch**: `006-core-measurements`

**Created**: 2026-02-16 · **Rewritten**: 2026-08-19

**Status**: Draft

**Goals**: G1 — a core data model of projects, datasets, samples, measurements and contributors that
domain schemas can extend and rely on. G2 — registering a model is enough to get a working portal
surface. G4 — contributions can be recorded against any object in the core model. G9 — records in
the core model can be searched, sorted and filtered. G12 — private and public data side by side,
controlled per object.

**Roadmap**: R6 — measurements.

**Input**: A measurement is the record of one observation or result obtained from a sample. It is
the polymorphic base every portal-defined measurement type inherits from, whatever the science: an
elemental concentration, a water temperature, a tensile strength, a species count. This
specification describes the measurement record itself: the fields it carries, the typed
descriptions, dates and identifiers attached to it, who is credited on it, how its access follows
from the dataset it belongs to, how a measurement recorded in one dataset can describe a sample
belonging to another, how an administrator manages it, how the value it reports is presented, and
the form and filter behaviour a portal developer inherits when defining a measurement type of their
own.

It does not describe the pages a researcher uses to create, list or edit a measurement. Those
belong to the CRUD specification, roadmap item R16, which does not exist yet. The reasoning behind
that line, and behind everything else this document settles, is in `decisions.md`.

## Clarifications

### Session 2026-08-19

The original text was written on 2026-02-16 as a companion to the sample specification, and its own
task list stopped part-way through. Seventy-two requirements described five layers at once, twelve
of them describing the tests rather than the feature. Each disagreement with the code was settled
and recorded in `decisions.md`; the questions and answers below are the ones that shaped this
document.

- Q: Does this specification own the measurement pages, the form behind them and the filter set
  behind the list? → A: It owns the record, and it owns `MeasurementFormMixin` and
  `MeasurementFilterMixin` because those are what a portal developer inherits from rather than what
  a page constructs. The pages and the concrete `MeasurementForm` and `MeasurementFilter` belong to
  the CRUD specification (D1).
- Q: The original text requires a measurement's sample choices to be limited to samples "included in
  the measurement's dataset", while its own headline story exists so that a measurement can describe
  a sample from a different dataset. A sample belongs to exactly one dataset, so the two cannot both
  hold. Which is intended? → A: Neither restriction applies here. Sample selection stays open, and
  narrowing it is a later refinement that waits on a way to reuse another group's sample without
  taking ownership of it (D2).
- Q: One roadmap item records that a measurement is a component of its sample's page rather than a
  record with a page of its own; another promises every registered measurement type a detail page.
  Which is intended? → A: A measurement gets its own page. Every record in the database needs one
  for auditing, and it keeps the editing interface uniform across record types. The page itself is
  the CRUD specification's work; the address is this one's (D3).
- Q: A measurement's value and uncertainty are reported by two methods that have never run — no
  measurement type anywhere defines a value, and the renderer reads an attribute the underlying
  library does not have. Keep the convention or drop it? → A: Keep it, and prove it. A demo type
  defines a value with an uncertainty so the path is exercised rather than asserted (D4).
- Q: The registry validates a supplied measurement admin against a two-line class, while the class
  the framework actually configures is a different one entirely, and a component the registry
  generates inherits the two-line one. Which is the real base? → A: The configured one. The
  two-line class and the parent admin beside it are unreachable duplicates and go (D5).
- Q: Should the requirements naming query-count reductions, registration times and boilerplate
  savings be kept? → A: No. None of them can be measured as stated. What replaces them is a query
  count that does not grow with the number of rows (D6).
- Q: Should the twelve requirements describing the tests be kept? → A: No. How tests are organised
  is settled by the project's own standards, and what matters here is that no test covering this
  behaviour is skipped or passes vacuously — which is a success criterion (D7).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Define a measurement type and get a working record (Priority: P1)

As a portal developer, I define a measurement type for my discipline and register it, and the portal
can store, present, filter and administer it without my writing a form, a filter set, a table or an
administrative entry.

**Why this priority**: this is the extensibility the framework exists to provide. Without it a
portal cannot capture its own results at all.

**Independent Test**: define a measurement type with fields of its own, register it, and confirm
that its generated components exist and carry those fields.

**Acceptance Scenarios**:

1. **Given** a measurement type defined by subclassing the measurement record, **When** it is
   registered, **Then** a form, a filter set, a table and an administrative entry exist for it,
   each carrying the type's own fields alongside those every measurement has.
2. **Given** two registered measurement types, **When** measurements are queried, **Then** each is
   returned as the type it was created as, carrying that type's fields.
3. **Given** an attempt to create a bare measurement belonging to no type, **When** it is saved
   through validation, through a form, through the administrative interface or through the manager,
   **Then** it is refused.
4. **Given** a registered measurement type, **When** an administrator adds a measurement, **Then**
   the type selection offers every registered type and nothing else.
5. **Given** a measurement type registered with an administrative class of its own, **When** that
   class is not built on the base the framework configures, **Then** registration is refused with a
   message naming the base it should have been built on.

---

### User Story 2 - Record a measurement against a sample from another dataset (Priority: P1)

As a researcher, I record my own measurements against a specimen another group collected, so that my
results are attributed to my dataset while the specimen stays attributed to theirs.

**Why this priority**: reusing another group's material is ordinary research practice, and getting
the attribution wrong misstates who did what.

**Independent Test**: create a measurement in one dataset naming a sample from another, and confirm
both attributions survive and that rights over the two records stay separate.

**Acceptance Scenarios**:

1. **Given** a sample belonging to one dataset, **When** a measurement in a second dataset names it,
   **Then** the measurement is created, the measurement is attributed to the second dataset and the
   sample stays attributed to the first.
2. **Given** such a measurement, **When** a user holding editing rights on the measurement's dataset
   but not on the sample's attempts to edit each, **Then** the measurement is editable and the
   sample is not.
3. **Given** a measurement naming a sample, **When** the sample is deleted, **Then** the deletion is
   refused while the measurement refers to it.
4. **Given** a measurement, **When** its own dataset is deleted, **Then** the measurement is deleted
   with it, whatever dataset its sample belongs to.

---

### User Story 3 - Describe how a measurement was made (Priority: P1)

As a researcher, I attach the conditions, the setup, the dates and the persistent identifier of a
measurement, using terms drawn from a controlled set, so that someone else can judge and reproduce
the result.

**Why this priority**: a number with no method behind it cannot be reused, which is the whole
purpose of publishing it.

**Independent Test**: attach a description, a date and an identifier of each permitted type, and
confirm a type outside the permitted set is refused.

**Acceptance Scenarios**:

1. **Given** a measurement, **When** a description is attached, **Then** its type comes from the
   measurement description vocabulary and no other.
2. **Given** a measurement, **When** a date is attached, **Then** its type comes from the
   measurement date vocabulary and no other.
3. **Given** a measurement, **When** an identifier is attached, **Then** its type comes from the
   measurement identifier collection, which contains no type belonging to another record.
4. **Given** a description, date or identifier carrying a type outside its vocabulary, **When** it
   is validated, **Then** it is refused with a message naming the offending type.
5. **Given** a measurement carrying descriptions, dates and identifiers, **When** it is deleted,
   **Then** they are deleted with it.

---

### User Story 4 - Access to a measurement follows the dataset it belongs to (Priority: P1)

As a portal administrator, I grant rights over a dataset once and have them apply to the
measurements in it, rather than granting them again per record.

**Why this priority**: measurements are the most numerous records in a portal. Rights that do not
derive are rights nobody will maintain.

**Independent Test**: grant rights on a dataset alone and confirm they resolve on its measurements;
confirm a user holding neither holds nothing.

**Acceptance Scenarios**:

1. **Given** a user holding a right over a dataset, **When** that right is consulted on one of its
   measurements, **Then** it is held.
2. **Given** a user holding a right over one measurement directly, **When** it is consulted on that
   measurement, **Then** it is held, and it is not held on any other.
3. **Given** a user holding neither, **When** any right is consulted, **Then** it is not held.
4. **Given** a measurement of a registered type, **When** a right is granted on it directly, **Then**
   the grant succeeds and reads back, as it does on a bare measurement.

---

### User Story 5 - Inherit form and filter behaviour when defining a measurement type (Priority: P2)

As a portal developer defining a measurement type, I inherit the controls and filters every
measurement needs, so that I write only what is particular to my type — and I get them even when I
write no form or filter set at all.

**Why this priority**: this is the difference between registering a type and building one. Behaviour
that only reaches developers who write their own classes reaches almost nobody.

**Independent Test**: build a form and a filter set from the mixins and confirm they carry the
declared behaviour; then register a type supplying neither and confirm the generated components
carry the same.

**Acceptance Scenarios**:

1. **Given** a filter set inheriting the filter mixin, **When** its filters are listed, **Then**
   every filter the mixin declares is present.
2. **Given** a form inheriting the form mixin and the requesting user, **When** it renders, **Then**
   it offers only the datasets that user may add measurements to.
3. **Given** a form inheriting the form mixin and no user, **When** it renders, **Then** it offers
   no dataset.
4. **Given** a registered measurement type supplying neither a form nor a filter set, **When** the
   registry generates them, **Then** they carry the mixins' behaviour rather than the framework's
   plain defaults.
5. **Given** a form that defines guidance text for a field, **When** the field renders, **Then** the
   guidance text is present.
6. **Given** any control the form offers, **When** it renders, **Then** every address it refers to
   resolves.

---

### User Story 6 - Narrow a long list of measurements (Priority: P2)

As someone reading a portal, I narrow a long list of measurements down to the ones I want by the
dataset they belong to, the sample they describe, their type, the words in their descriptions and
the dates they were made, so that I can find a result without paging through everything.

**Why this priority**: measurements are the most numerous records a portal holds. A list of them
that cannot be narrowed is a list nobody reads.

**Independent Test**: create measurements differing in each respect and confirm each filter and the
search return exactly the ones they name.

**Acceptance Scenarios**:

1. **Given** measurements across several datasets, **When** the list is narrowed by one dataset,
   **Then** only that dataset's measurements remain.
2. **Given** measurements against several samples, **When** the list is narrowed by one sample,
   **Then** only that sample's measurements remain.
3. **Given** measurements of several types, **When** the type choices are offered, **Then** they are
   exactly the registered measurement types, and narrowing by one leaves only measurements of that
   type.
4. **Given** a search term, **When** it is applied, **Then** measurements whose name or generated
   identifier contains it are returned and no others.
5. **Given** measurements carrying descriptions and dates, **When** the list is narrowed by
   description text or by a range of dates, **Then** only measurements matching remain.
6. **Given** a reader entitled to a dataset that is not publicly visible, **When** the dataset
   choices are offered, **Then** that dataset is among them.
7. **Given** two filters applied together, **When** the list is shown, **Then** only measurements
   satisfying both remain.

---

### User Story 7 - Report a measurement's value, with its uncertainty (Priority: P2)

As a researcher, the value a measurement reports carries its uncertainty wherever the type records
one, so that precision survives from data entry through to display.

**Why this priority**: a result quoted without its uncertainty overstates what was measured, and
uncertainty is the one piece of a scientific value that generic machinery keeps losing.

**Independent Test**: define a measurement type carrying a value and an uncertainty, and confirm
both the machine-readable value and the human-readable rendering carry the uncertainty.

**Acceptance Scenarios**:

1. **Given** a measurement type nominating a value, **When** the value is requested, **Then** that
   value is returned.
2. **Given** a measurement type nominating a value with an uncertainty recorded, **When** the value
   is requested, **Then** the uncertainty is carried with it.
3. **Given** a measurement type nominating no value, **When** the value is requested, **Then** the
   record's name is returned instead.
4. **Given** a value carrying an uncertainty, **When** it is rendered for a person, **Then** the
   rendering shows the value and its uncertainty together.
5. **Given** a value carrying units, **When** it is requested or rendered, **Then** the units
   survive.

---

### User Story 8 - Manage measurements as an administrator (Priority: P2)

As a portal administrator, I find a measurement, correct it and edit its attached records from one
page, whatever type it is.

**Why this priority**: until the portal's own editing pages exist, this is the only route to
correcting a measurement, and it stays the route for administrative work afterwards.

**Independent Test**: search and narrow the measurement list by each supported term, then add each
kind of attached record inline.

**Acceptance Scenarios**:

1. **Given** the measurement list, **When** it is searched by name or by generated identifier,
   **Then** matching measurements are returned.
2. **Given** the measurement list, **When** it is narrowed by dataset, by sample or by measurement
   type, **Then** only matching measurements remain.
3. **Given** a measurement, **When** it is edited, **Then** its descriptions, dates, identifiers and
   contributions can each be added and changed from that page.
4. **Given** the measurement list, **When** it is displayed, **Then** each row names its measurement
   type.
5. **Given** a measurement, **When** it is edited, **Then** its generated identifier and its
   timestamps are presented as unchangeable.
6. **Given** any two registered measurement types, **When** each is edited, **Then** both offer the
   same attached-record editors.

---

### User Story 9 - Load many measurements without a query for each (Priority: P2)

As a developer building a page that lists measurements, I load them together with their datasets,
samples, contributors and attached records without the database being asked once per row.

**Why this priority**: measurements are the most numerous records a portal holds, so a page that
queries per row is the one that fails first.

**Independent Test**: load a set of measurements with their related records and count the queries as
the number of measurements grows.

**Acceptance Scenarios**:

1. **Given** measurements with samples, datasets and contributors, **When** they are loaded with
   their related records, **Then** the number of queries does not grow with the number of
   measurements.
2. **Given** measurements with descriptions, dates and identifiers, **When** they are loaded with
   their attached records, **Then** the number of queries does not grow with the number of
   measurements.
3. **Given** either loading, **When** it is combined with the other and with ordinary filtering and
   ordering, **Then** the combination applies correctly.

---

### User Story 10 - The measurement record itself (Priority: P2)

As a portal developer, the measurement record carries what every measurement needs whatever its
type: an identifier the portal generates, a name, the researcher's own label, the dataset it belongs
to, the sample it describes, credit for the people who made it, and an address of its own.

**Why this priority**: everything else in this document rests on the record being right, and its
address is what lets any other page link to it.

**Independent Test**: create a measurement, confirm each field behaves as specified, and confirm its
address resolves to that measurement.

**Acceptance Scenarios**:

1. **Given** a new measurement, **When** it is created, **Then** it carries a short generated
   identifier, recognisable as a measurement's, which cannot afterwards be changed.
2. **Given** two measurements in different datasets carrying the same researcher's label, **When**
   both are saved, **Then** both are valid.
3. **Given** a measurement, **When** a person or organisation is credited on it, **Then** the
   credit records one or more roles drawn from a controlled set.
4. **Given** a measurement, **When** its address is requested, **Then** it is the measurement's own
   address and not its sample's.
5. **Given** a measurement, **When** it is created and when it is changed, **Then** both times are
   recorded.

---

### Edge Cases

- A measurement's own label may be absent, and may repeat across datasets. It is the researcher's
  label, not a key.
- Two measurements may carry the same name. Nothing distinguishes them but their generated
  identifiers.
- Several measurements of the same type against the same sample are a normal state; repeating an
  analysis is ordinary practice.
- A measurement whose sample belongs to another dataset is a normal state, not an error to correct.
- Deleting a dataset deletes its measurements. Deleting a sample a measurement refers to is refused.
- A measurement type that nominates no value is a normal state, and its records read back by name.
- A measurement type may nominate a value that carries no uncertainty.
- Non-ASCII characters in names, labels and descriptions are stored unchanged.

## Requirements *(mandatory)*

### The measurement record

- **FR-001**: Each measurement MUST carry a unique, short, human-readable identifier generated on
  creation, prefixed so that it is recognisable as a measurement's, and not editable afterwards.
- **FR-002**: A measurement MUST carry a name. A measurement MAY carry a label of the researcher's
  own devising, an image, terms drawn from a controlled vocabulary, and free-form tags.
- **FR-003**: A researcher's own label MUST NOT be required to be unique. Two measurements in
  different datasets carrying the same one MUST both be valid.
- **FR-004**: A measurement MUST belong to exactly one dataset, and MUST be deleted when that
  dataset is deleted.
- **FR-005**: A measurement MUST name exactly one sample, and deleting that sample MUST be refused
  while any measurement refers to it.
- **FR-006**: The sample a measurement names MAY belong to a different dataset from the measurement,
  and neither attribution MUST be altered by the other.
- **FR-007**: A measurement MUST record when it was created and when it was last changed.
- **FR-008**: A measurement MUST support contributions associating a person or an organisation with
  it under one or more roles drawn from a controlled set.
- **FR-009**: A measurement MUST have an address of its own, resolving to that measurement rather
  than to the sample it describes.

### Polymorphism and the registry

- **FR-010**: The measurement record MUST be a polymorphic base from which a portal defines its own
  measurement types, and querying measurements MUST return each as the type it was created as.
- **FR-011**: Creating a measurement belonging to no type MUST be refused through validation,
  through a form, through the administrative interface and through the manager. The framework's own
  test fixtures MUST NOT create one.
- **FR-012**: Registering a measurement type MUST produce a form, a filter set, a table and an
  administrative entry for it, each carrying that type's own fields, with none of them written by
  hand.
- **FR-013**: The administrative type selection MUST list the registered measurement types, taken
  from the registry rather than from a fixed list.
- **FR-014**: The framework MUST supply a configuration base that a portal's measurement type
  inherits, carrying the fields every measurement has.
- **FR-015**: Where the registry checks that a supplied administrative class is suitable for a
  measurement type, it MUST check against the class the framework itself configures, and MUST name
  that class in the message when it refuses.

### Descriptions, dates and identifiers

- **FR-016**: A measurement's descriptions, dates and identifiers MUST each refer to the measurement
  directly, and MUST be deleted when it is deleted.
- **FR-017**: A description's type MUST be drawn from the measurement description vocabulary.
- **FR-018**: A date's type MUST be drawn from the measurement date vocabulary.
- **FR-019**: An identifier's type MUST be drawn from the measurement identifier collection, which
  MUST contain no type belonging to another kind of record.
- **FR-020**: A description, date or identifier carrying a type outside its vocabulary MUST be
  refused by validation, with a message naming the offending type.

### Access

- **FR-021**: A right over a measurement MUST derive from the same right over the dataset the
  measurement belongs to.
- **FR-022**: A right MUST also be grantable over one measurement alone, and MUST then apply to that
  measurement and no other.
- **FR-023**: Rights over the sample a measurement names MUST derive from that sample's own dataset,
  independently of the measurement's.
- **FR-024**: A right MUST be grantable over a measurement as well as consulted on it, and MUST
  behave the same whether the measurement is a registered type or the bare record.

### Reusable form and filter behaviour

- **FR-025**: The framework MUST supply a form mixin that configures the controls for the fields
  every measurement carries, and a filter mixin that supplies the filters a reader expects.
- **FR-026**: Every filter the filter mixin declares MUST be present on a filter set that inherits
  it. A filter declared where the framework's filtering library will not collect it MUST NOT be
  carried.
- **FR-027**: A measurement form given the requesting user MUST offer only the datasets that user
  may add measurements to. A measurement form given no user MUST offer no dataset at all.
- **FR-028**: What the registry generates for a measurement type supplying neither a form nor a
  filter set MUST carry the mixins' behaviour rather than the framework's plain defaults.
- **FR-029**: Guidance text a form defines for a field MUST reach the rendered field.
- **FR-030**: Every address a form's controls refer to MUST resolve.

### Finding measurements

- **FR-031**: A reader MUST be able to narrow measurements by the dataset they belong to, by the
  sample they describe, and by measurement type.
- **FR-032**: The measurement types offered MUST be the registered ones, taken from the registry
  rather than from a fixed list of applications.
- **FR-033**: A reader MUST be able to search measurements by name and by generated identifier
  together.
- **FR-034**: A reader MUST be able to narrow measurements by the text of their descriptions and by
  the range of their dates.
- **FR-035**: The datasets offered as choices MUST include those not publicly visible, so that a
  reader entitled to a private dataset can narrow by it.

### The value a measurement reports

- **FR-036**: A measurement MUST report a value. Where its type nominates one, that value MUST be
  reported; where its type nominates none, the record's name MUST be reported instead.
- **FR-037**: Where a measurement type records an uncertainty alongside its value, the reported
  value MUST carry the uncertainty.
- **FR-038**: A measurement MUST render its value for a person, showing the uncertainty alongside
  the value wherever one is carried, and preserving any units.
- **FR-039**: At least one measurement type distributed with the framework MUST nominate a value and
  record an uncertainty, so that this behaviour is exercised rather than only described.

### Administration

- **FR-040**: The administrative interface MUST allow measurements to be found by name and by
  generated identifier, and MUST allow the list to be narrowed by dataset, by sample and by
  measurement type.
- **FR-041**: The administrative interface MUST allow a measurement's descriptions, dates,
  identifiers and contributions to be edited from the measurement's own page. For the three records
  whose type comes from a vocabulary, it MUST offer no more rows than that vocabulary has types.
  Contributions MUST NOT be capped — a measurement may credit any number of people, and each is a
  row of its own. *Amended at design review: the original wording applied the cap to all four, which
  would have limited how many contributors a measurement can carry and contradicted FR-008.*
- **FR-042**: Every registered measurement type MUST offer the same attached-record editors as every
  other.
- **FR-043**: The administrative list MUST name the measurement type of each row.
- **FR-044**: The generated identifier and the timestamps MUST be presented as unchangeable.
- **FR-045**: The framework MUST define exactly one administrative class for the measurement record
  and exactly one base for the types beneath it, with no unreachable duplicate of either.

### Loading measurements

- **FR-046**: Loading measurements together with their datasets, samples and contributors, and
  loading them together with their descriptions, dates and identifiers, MUST each take a number of
  queries that does not grow with the number of measurements.
- **FR-047**: Both MUST combine with each other and with ordinary filtering and ordering.

### Key Entities

- **Measurement**: the record of one observation or result obtained from a sample. The polymorphic
  base a portal's own measurement types inherit from. Belongs to one dataset, names one sample,
  carries a generated identifier, a name, an optional label of the researcher's own, credit for
  contributors, and an address of its own.
- **Measurement description**: typed free text recording how a measurement was made, its type drawn
  from the measurement description vocabulary.
- **Measurement date**: a typed date in a measurement's history, its type drawn from the measurement
  date vocabulary.
- **Measurement identifier**: an identifier issued by an outside authority, its type drawn from the
  measurement identifier collection.
- **Form mixin and filter mixin**: what a portal developer inherits when defining a measurement
  type's form or filter set, and what the registry builds on when a type supplies neither.
- **Sample**: the specimen a measurement describes. It may belong to a different dataset, and its
  own access is governed there.
- **Dataset**: the container a measurement belongs to, and the record its access derives from.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A measurement type is defined and registered, and its form, filter set, table and
  administrative entry all exist and carry that type's own fields, with nothing written by hand.
- **SC-002**: Creating a bare measurement belonging to no type is refused through validation,
  through a form, through the administrative interface and through the manager. The framework's own
  test fixtures do not create one.
- **SC-003**: A description, a date and an identifier of a type outside the measurement vocabularies
  are each refused by validation with a message naming the type, and each of the three measurement
  vocabularies is asserted by naming the members it contains rather than by iterating whatever it
  holds.
- **SC-004**: A measurement in one dataset describing a sample in another is created and read back
  with both attributions intact; deleting the measurement's dataset removes it, and deleting the
  sample is refused while it remains.
- **SC-005**: A user holding rights on a dataset alone holds the corresponding rights on its
  measurements; a user holding rights on one measurement alone holds them on that measurement; a
  user holding neither holds nothing. A right can be granted on a registered measurement type as
  well as consulted, and the same answers hold for the bare record.
- **SC-006**: A filter set inheriting the filter mixin carries every filter the mixin declares, and
  the form and filter set the registry generates for a type supplying neither carry the same
  behaviour.
- **SC-007**: Every search term and every filter in FR-031 to FR-035 finds or removes the
  measurements it names; the measurement types offered are exactly those registered; and a private
  dataset can be chosen.
- **SC-008**: A measurement type nominating a value with an uncertainty reports both, and renders
  them together for a person with any units intact; a type nominating no value reads back its name.
- **SC-009**: Every search term and filter in FR-040 returns what it names, a description, date,
  identifier and contribution can each be added from a measurement's own page, and every registered
  type offers the same editors.
- **SC-010**: Loading a list of measurements together with all their related records takes a number
  of queries that does not grow with the number of measurements or of related records.
- **SC-011**: A measurement's address resolves to that measurement.
- **SC-012**: No test covering behaviour in this specification is skipped, and no test in it passes
  when the behaviour it names is removed.
- **SC-013**: Every statement the measurement models, admin, forms, filters and vocabularies make
  about their own behaviour is true of the code as it stands.

## Assumptions

- The controlled vocabulary machinery, the contribution model, the polymorphic model library, the
  object-level permission library and the tagging library are already in place and are not changed
  by this work.
- The registry described by `002-fairdm-registry` generates components from a registered
  configuration, and this work uses it rather than replacing it.
- The dataset record specified by `004-core-datasets` supplies the container a measurement belongs
  to and the rights its access derives from; its own model is not changed here.
- The sample record specified by `005-core-samples` supplies the specimen a measurement describes;
  its own model is not changed here.
- The unit-and-uncertainty library the value convention rests on is available. A measurement type is
  not obliged to use it, and a type that does not still reports a value.
- The pages through which a researcher creates, lists and edits a measurement are specified by the
  CRUD specification, roadmap item R16. Where a field specified here needs a form control on a page,
  that document decides whether it gets one.
- Translation catalogues do not exist in the repository yet. This work marks strings for
  translation; it does not produce catalogues.

## Out of scope

- The measurement list, detail, create, edit and delete pages, and the concrete form and filter set
  those pages would instantiate — the CRUD specification, roadmap item R16 (D1, D3).
- Restricting which samples a measurement may name. Selection stays open until a sample can be
  reused across datasets without its ownership moving (D2).
- Reusing a sample across datasets without transferring ownership of it, which the data model does
  not yet support.
- Import and export of measurement data beyond what the administrative interface offers.
- The REST API's representation of a measurement — `011-restful-api`.
- Statistical analysis, aggregation or quality control over measurement values.
- Relationships between one measurement and another, such as a derived or recalculated result.
- Versioning a measurement's value over time.
- Registering a measurement with an external identifier authority. Identifiers are stored, not
  minted.
