# Feature Specification: Contributors and contributions

**Feature Branch**: `009-fairdm-contributors`

**Created**: 2026-02-18 · **Rewritten**: 2026-08-20

**Status**: Draft

**Goals**: G1 — a core data model of projects, datasets, samples, measurements and contributors that
domain schemas can extend and rely on. G4 — contributions can be recorded and revised against any
object in the core model. G15 — external identifiers for people, organisations and samples are
carried through the record.

**Roadmap**: R9 — contributors and contributions.

**Input**: Everyone credited on a portal's research outputs is one record. A contributor is either a
person or an organisation, and the two share the attribution data that citation and provenance need:
a name, other names they are known by, where they are based, and the external identifier the wider
scholarly world knows them by. A person is also the portal's account, so credit and identity are the
same row and a researcher can be credited long before they ever sign in. Organisations hold people
as members over time, and one of those members may own the organisation. A contribution records who
did what on a project, a dataset, a sample or a measurement.

This specification describes those records: the fields they carry, how they relate to one another,
what may and may not be true of them, the questions a developer can ask of them, and how an
administrator maintains them. It does not describe the pages a researcher uses to browse or edit a
contributor, nor the fetching of data from ORCID and ROR, nor the export of contributor metadata to
external formats. The reasoning behind that line, and behind everything else this document settles,
is in `decisions.md`.

## Clarifications

### Session 2026-08-20

The original text was written on 2026-02-18. It described a system that is substantially not the one
that shipped: nineteen requirements, six user stories, and a task list of 174 items every one of
which was marked complete — including the whole of the organisation-ownership story, whose mechanism
a later migration deleted. Each disagreement with the code was settled and recorded in
`decisions.md`; the questions and answers below are the ones that shaped this document.

- Q: The original text scopes itself to "developer-facing" concerns, but the application ships
  browse pages, create pages, nine plugins, forms, widgets, a bulk importer and a component library
  that no requirement mentions. Does this specification own them? → A: No. Views, plugins and
  anything that creates, edits or deletes through the portal are deferred to a later specification.
  The administrative interface stays (D1).
- Q: The document covers four unrelated concerns at once. Should it be split into one specification
  for people and one for organisations? → A: No. The seam is wrong — most of the behaviour lives on
  the shared base, and the relationships cross both types. External identifier synchronisation and
  metadata export are lifted out into their own specifications instead (D2).
- Q: If synchronisation is lifted out, does the identifier record go with it? → A: No. The record
  stays here as data — that a contributor carries typed external identifiers, and the rules on them.
  Fetching, refreshing and recording the outcome of a fetch belong to the synchronisation
  specification (D3).
- Q: Three of the seven fields the original text names for an organisation do not exist. Which are
  wording and which are unbuilt? → A: Logo and URL are wording — they are the shared profile image
  and the shared list of related resources. Organisation type is genuinely unbuilt and stays, drawn
  from the set the ROR registry defines (D6).
- Q: An affiliation is required to carry a "role", and carries a membership type instead. Is a
  person's position at an institution something a portal records? → A: Not for now. "Role" already
  means what a contributor did on a record, and a second unrelated meaning would collide with it
  (D7).
- Q: A four-state account machine is required and none of it exists in code. Build it? → A: Not as
  stored state. The state is derivable from what is already stored, and a stored copy alongside
  would be a second truth to drift. It becomes a readable, filterable derivation, and "banned"
  becomes "inactive" (D8).
- Q: Per-field privacy controls are built and nothing anywhere calls them. Keep, enforce or drop?
  → A: Replace. The privacy field becomes a general-purpose configuration field whose contents a
  later specification settles, and the unused visibility method goes (D9).
- Q: A portal administrator who is staff but not a superuser is refused management of an
  organisation, and the test suite asserts that refusal is correct. Which is intended? → A: Neither
  is settled here. The requirement's intent is right and its home is wrong — it waits on the
  specification that defines a portal's default administrative roles (D10).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - One record for everyone credited (Priority: P1)

As a portal developer, people and organisations are one family of records sharing the attribution
data that citation needs, so that I can credit either kind on anything without branching on which it
is.

**Why this priority**: Every other story here builds on it. Credit that had to know in advance
whether it was crediting a person or an institution would push that branch into every caller.

**Independent Test**: Create a person and an organisation, query the base, and confirm each comes
back as the type it was created as with its shared fields intact.

**Acceptance Scenarios**:

1. **Given** a person and an organisation exist, **When** I query contributors, **Then** I receive
   both, each as its own type, without asking which it is
2. **Given** I am creating a contributor of either kind, **When** I save it, **Then** it receives a
   stable public identifier that is recognisable as a contributor's and cannot afterwards be changed
3. **Given** a contributor exists, **When** I read it, **Then** it carries a preferred name, and may
   carry other names it is known by, a description, an image, related online resources, a location
   and language preferences
4. **Given** I supply a language preference, **When** it is not an ISO 639-1 code, **Then** the
   record is refused with a message naming the offending value
5. **Given** a contributor exists, **When** I read it, **Then** it records when it was created and
   when it was last changed

---

### User Story 2 - A person is also the account (Priority: P1)

As a portal developer, the person credited on a dataset and the account that signs in are the same
record, so that a researcher's credit and their identity never have to be reconciled.

**Why this priority**: The alternative — a profile beside an account — is the failure this design
exists to avoid, and every claiming flow depends on there being one row to claim.

**Independent Test**: Confirm the portal's account model is the person record, create a person with
no email address, and confirm they cannot sign in but can be credited.

**Acceptance Scenarios**:

1. **Given** a portal is running, **When** I ask which model holds its accounts, **Then** it is the
   person record, and no separate account record exists
2. **Given** I add a person for attribution alone, **When** I save them, **Then** they have no email
   address and no usable password, and cannot sign in
3. **Given** a person added for attribution alone, **When** I inspect them, **Then** they remain
   eligible for activation later, so that an invitation or a reset can reach them
4. **Given** a person has claimed their account, **When** they try to remove their email address,
   **Then** the change is refused
5. **Given** a person exists with an email address, **When** another person is created with the same
   address, **Then** the second is refused

---

### User Story 3 - Know whether a profile has been claimed (Priority: P1)

As a portal administrator, I can tell at a glance which of four states a person's account is in, so
that I know who is waiting to be invited and who has gone.

**Why this priority**: A portal accumulates people credited by others. Without a reliable reading of
who has taken ownership of their record, an administrator cannot tell follow-up work from noise.

**Independent Test**: Create a person in each of the four states and confirm each reports the state
it is in, that the states cannot overlap, and that each can be filtered for.

**Acceptance Scenarios**:

1. **Given** a person was added for attribution and has no email address, **When** I read their
   state, **Then** it is ghost
2. **Given** a person has an email address and has not claimed their account, **When** I read their
   state, **Then** it is invited
3. **Given** a person has claimed their account, **When** I read their state, **Then** it is claimed
4. **Given** a person's account has been deactivated, **When** I read their state, **Then** it is
   inactive, whatever their claim status
5. **Given** people in every state exist, **When** I filter for one of them, **Then** I receive
   exactly the people in that state, and the four filters together return everyone exactly once

---

### User Story 4 - Institutions and their hierarchy (Priority: P2)

As a portal developer, institutions are records in their own right that can be described, typed and
nested, so that a department, its faculty and its university are all representable.

**Why this priority**: Attribution to an institution is a FAIR requirement, and institutions are not
flat. A department credited without its parent is a weaker record than one credited with it.

**Independent Test**: Create a university and a department beneath it, confirm the hierarchy holds,
and confirm deleting the university does not delete the department.

**Acceptance Scenarios**:

1. **Given** I am creating an organisation, **When** I set its type, **Then** the value must be one
   the ROR registry defines, and any other value is refused
2. **Given** a university exists, **When** I create a department naming it as parent, **Then** the
   department is reachable from the university and the university from the department
3. **Given** a department names a parent, **When** that parent is deleted, **Then** the department
   survives with no parent, and its own members and credits are untouched
4. **Given** an organisation exists, **When** I read it, **Then** it may record the city and the
   country it is based in

---

### User Story 5 - Membership of an institution over time (Priority: P2)

As a portal developer, a person's membership of an institution is a record with a beginning and an
end, so that a dataset collected in 2019 can be attributed to where its author worked in 2019.

**Why this priority**: Researchers move. Attribution that silently followed them would misstate the
provenance of everything they did before the move.

**Independent Test**: Record a person's membership of two institutions across different periods,
confirm both are preserved, and confirm which is current.

**Acceptance Scenarios**:

1. **Given** a person and an organisation, **When** I record a membership, **Then** it carries a
   period and a membership type
2. **Given** a membership has no end date, **When** I ask for current memberships, **Then** it is
   included, and when it has one, it is not
3. **Given** I know only the year a membership began, **When** I record it, **Then** the year alone
   is accepted, as is a year and month, as is a full date
4. **Given** a person is a member of several organisations, **When** I mark one as primary, **Then**
   it is the only primary one, and marking another moves the mark
5. **Given** a person is already a member of an organisation, **When** a second membership of the
   same organisation is recorded, **Then** it is refused

---

### User Story 6 - Who owns an organisation (Priority: P2)

As a portal administrator, an organisation's management rights follow from who its owner is, so that
delegating an institution to the person who runs it does not mean maintaining a second list of
permissions.

**Why this priority**: Every stored permission is a copy that can fall out of step with the fact it
was copied from. Deriving the right from the membership means the two can never disagree.

**Independent Test**: Make a member an owner, confirm they hold management rights on that
organisation and no other, demote them, and confirm the rights go with the demotion immediately.

**Acceptance Scenarios**:

1. **Given** a person's membership of an organisation is set to owner, **When** their rights over
   that organisation are checked, **Then** they hold management rights
2. **Given** an owner is demoted, **When** their rights are checked again, **Then** they no longer
   hold them, with no separate revocation step and no stale answer
3. **Given** an organisation has no owner, **When** anyone's rights over it are checked, **Then**
   nobody holds management rights by membership, and no member is promoted automatically
4. **Given** an organisation has an owner, **When** ownership is transferred to another member,
   **Then** the incumbent becomes an administrator of it and the new owner holds the rights
5. **Given** a person owns one organisation, **When** their rights over a different organisation are
   checked, **Then** they hold nothing there

---

### User Story 7 - Credit on a record (Priority: P1)

As a portal developer, a contributor is credited on a project, a dataset, a sample or a measurement
through one entry that carries every role they played, so that a person who both collected and
analysed appears once rather than twice.

**Why this priority**: This is what the whole family of records exists for, and one entry per
contributor per object is what keeps a citation list from repeating people.

**Independent Test**: Credit one person on one dataset under two roles, confirm a single entry
carries both, and confirm a second entry for the same pair is refused.

**Acceptance Scenarios**:

1. **Given** a contributor and a research output, **When** I credit them, **Then** one entry records
   the pairing, and its roles are drawn from the framework's controlled set
2. **Given** a contributor is already credited on an output, **When** a second entry is created for
   the same pairing, **Then** it is refused, and adding a further role adds it to the existing entry
3. **Given** a person has a primary organisation, **When** they are credited and no organisation is
   named on the entry, **Then** their primary one is recorded against the credit
4. **Given** a contributor is credited on several outputs, **When** I ask what they have contributed
   to, **Then** I receive their projects, datasets, samples and measurements, and counts by kind
5. **Given** contributors share credits with one another, **When** I ask who a contributor works
   with, **Then** I receive the others credited alongside them, most frequent first

---

### User Story 8 - Carry external identifiers (Priority: P2)

As a portal developer, a contributor carries the identifiers the scholarly world knows them by, so
that credit in this portal can be matched to credit anywhere else.

**Why this priority**: An identifier is what makes attribution verifiable rather than a name that
might be someone else's. It is the whole of G15 as far as people and institutions are concerned.

**Independent Test**: Attach an ORCID to a person and a ROR to an organisation, confirm each is
retrievable as that contributor's default identifier, and confirm a second identifier of the same
type is refused.

**Acceptance Scenarios**:

1. **Given** a person, **When** I attach an external identifier, **Then** it carries a type and a
   value, and the type expected of a person by default is ORCID
2. **Given** an organisation, **When** I attach an external identifier, **Then** the type expected of
   it by default is ROR
3. **Given** a contributor already carries an identifier of a given type, **When** a second of that
   same type is attached, **Then** it is refused
4. **Given** a contributor carries several identifiers, **When** I ask for their default one, **Then**
   I receive the one of the type expected for their kind

---

### User Story 9 - Ask questions about contributors (Priority: P2)

As a portal developer, the questions I need to ask about contributors are answered by the framework's
own managers, so that I am not rewriting the same filters in every portal and addon.

**Why this priority**: These queries are the interface every consumer of this data uses. Left to
callers, each writes its own and they disagree.

**Independent Test**: Use each manager method against a fixture covering every case it distinguishes,
and confirm the answers partition the data as documented.

**Acceptance Scenarios**:

1. **Given** a portal with real people and machine accounts, **When** I ask for real contributors,
   **Then** superusers and the anonymous placeholder are excluded
2. **Given** people in each account state, **When** I ask for one state, **Then** I receive exactly
   those people
3. **Given** memberships past and present, **When** I ask an organisation for its current members,
   **Then** ended memberships are excluded, and asking for past ones returns only those
4. **Given** credits under several roles, **When** I ask for the credits under one role, **Then** I
   receive only those
5. **Given** any of these queries, **When** it is run, **Then** it is composed from the queryset
   rather than reimplemented on the manager

---

### User Story 10 - Administer contributors (Priority: P2)

As a portal administrator, one screen per record type lets me maintain people, institutions and
memberships, so that keeping the community record accurate is an ordinary job.

**Why this priority**: With the portal's own editing pages deferred, the administrative interface is
the only way this data is maintained at all.

**Independent Test**: Open each administrative screen, confirm the fields and inline lists it
promises are present, and confirm the actions it offers do what they say.

**Acceptance Scenarios**:

1. **Given** I open a person, **When** the screen loads, **Then** account fields and profile fields
   appear together, and no separate account screen exists
2. **Given** I open an organisation, **When** the screen loads, **Then** its members appear as an
   editable list and its sub-organisations appear as a list
3. **Given** I filter people by claim status, **When** I choose a state, **Then** the results agree
   with what the record itself reports
4. **Given** I transfer an organisation's ownership to a member, **When** I confirm, **Then** the
   transfer happens, rather than a message describing how I might do it by hand

---

### Edge Cases

- A person is credited on a record and then deleted. What becomes of the credit?
- A department's parent is deleted while people hold memberships of both.
- Two people are added by different administrators for the same human being.
- A membership is recorded with an end date earlier than its start date.
- An organisation's ROR identifier changes, or the institution merges with another.
- A person's only membership is of an organisation that is deleted.
- A contributor's name is written in a script that has no concept of a given and a family name.

## Requirements *(mandatory)*

### The contributor record

- **FR-001**: The contributor record MUST be a polymorphic base with exactly two concrete types, a
  person and an organisation, and querying contributors MUST return each as the type it was created
  as.
- **FR-002**: Every contributor MUST carry a preferred name, and a stable public identifier
  generated on creation, prefixed so that it is recognisable as a contributor's, and not editable
  afterwards.
- **FR-003**: A contributor MAY carry other names it is known by, a free-text description, an image,
  a list of related online resources, a geographic location, and a list of language preferences.
- **FR-004**: A language preference MUST be refused unless it is an ISO 639-1 code, and the refusal
  MUST name the offending value.
- **FR-005**: A contributor MUST record when it was created and when it was last changed.
- **FR-006**: A contributor MUST carry a general-purpose configuration store held per contributor.
  This specification defines neither its contents nor its schema.
- **FR-007**: Every field a contributor carries MUST declare a human-readable name and an
  explanation of what it holds, both translatable.

### People

- **FR-008**: A person MUST be the portal's authentication account. There MUST be no separate
  account record and no link between the two.
- **FR-009**: A person MUST be identified for signing in by their email address, and an email
  address MUST be unique across people.
- **FR-010**: A person MUST be able to exist with no email address and no usable password, and such
  a person MUST NOT be able to sign in.
- **FR-011**: A person added for attribution alone MUST remain eligible for later activation, so
  that an invitation or a password reset can reach them once an address is known.
- **FR-012**: A person MUST record whether their account has been claimed, as a stored value, and
  that value MUST be the only stored expression of claim status.
- **FR-013**: A person MUST report their account state as exactly one of ghost, invited, claimed or
  inactive. The state MUST be derived from stored values and MUST NOT be stored itself. A
  deactivated person is inactive whatever else is true of them; otherwise a person who has claimed
  their account is claimed, a person carrying an email address is invited, and a person carrying
  none is a ghost.
- **FR-014**: Each of the four account states MUST be filterable as well as readable, and the four
  filters together MUST return every person exactly once.
- **FR-015**: A person who has claimed their account MUST NOT be able to remove their email address.

### Organisations

- **FR-016**: An organisation MUST carry a type drawn from the controlled set the ROR registry
  defines, and a value outside that set MUST be refused.
- **FR-017**: An organisation MAY name another organisation as its parent, and MUST be reachable
  from that parent as one of its sub-organisations.
- **FR-018**: Deleting an organisation MUST NOT delete its sub-organisations. Each surviving
  sub-organisation MUST simply have no parent, and its members and credits MUST be untouched.
- **FR-019**: An organisation MAY record the city and the country in which it is based.

### Membership of an organisation

- **FR-020**: A person's membership of an organisation MUST be held in a single record carrying the
  person, the organisation, a period and a membership type.
- **FR-021**: A person MUST NOT hold two memberships of the same organisation.
- **FR-022**: A membership with no end date MUST be current, and one with an end date MUST NOT be.
- **FR-023**: The beginning and end of a membership MUST each be recordable as a year alone, a year
  and a month, or a full date.
- **FR-024**: A person MUST have at most one primary membership, and marking a membership primary
  MUST unmark any other.
- **FR-025**: Membership type MUST be one of pending, member, administrator or owner, ordered so
  that a pending membership is distinguishable from a confirmed one.

### Ownership of an organisation

- **FR-026**: A person MUST hold management rights over an organisation exactly when they hold an
  owner membership of it, and MUST hold them over no other organisation on that account.
- **FR-027**: Management rights MUST be derived from the membership at the moment they are checked.
  No permission record MUST be stored, granted or revoked to express them.
- **FR-028**: An organisation with no owner MUST confer management rights on nobody by membership,
  and no member MUST be promoted to owner automatically.
- **FR-029**: Ownership MUST be transferable to an existing member, and the transfer MUST demote the
  incumbent owner to administrator in the same operation.

### Contributions

- **FR-030**: A contributor MUST be creditable on a project, a dataset, a sample or a measurement.
- **FR-031**: There MUST be exactly one credit per contributor per object. A second MUST be refused,
  and a further role MUST accumulate on the existing one.
- **FR-032**: A credit MUST carry one or more roles drawn from the framework's controlled set of
  contribution roles.
- **FR-033**: Where a person is credited and no organisation is named on the credit, their primary
  membership's organisation MUST be recorded against it.
- **FR-034**: A contributor MUST be able to report the projects, datasets, samples and measurements
  it is credited on, and counts of its credits by kind.
- **FR-035**: A contributor MUST be able to report the contributors most often credited alongside
  it.
- **FR-036**: Deleting a person's credit on an object MUST withdraw that person's object-level
  rights over that object. This MUST be stated wherever the behaviour is documented, because no
  corresponding grant happens when the credit is created.

### External identifiers

- **FR-037**: A contributor MUST be able to carry external identifiers, each with a type and a
  value.
- **FR-038**: A contributor MUST NOT carry two identifiers of the same type.
- **FR-039**: The identifier type expected of a person by default MUST be ORCID, and of an
  organisation ROR, and a contributor MUST be able to report its default identifier.

### Finding contributors

- **FR-040**: The queries in FR-041 and FR-042 MUST be defined once on a queryset and composed onto
  the manager, matching the pattern the core models already use, rather than reimplemented as
  manager methods.
- **FR-041**: The framework MUST answer, for people: real contributors excluding superusers and the
  anonymous placeholder, active accounts, and each of the four account states.
- **FR-042**: The framework MUST answer, for memberships, which are current and which have ended;
  and for credits, which carry a given role.

### Administration

- **FR-043**: The administrative screen for a person MUST present account fields and profile fields
  together, and no separate account screen MUST exist.
- **FR-044**: The administrative screen for an organisation MUST present its members as an editable
  inline list and its sub-organisations as an inline list.
- **FR-045**: An administrative filter on claim status MUST derive from the stored claim value, and
  MUST agree with the state the record itself reports.
- **FR-046**: An administrative action offering to transfer an organisation's ownership MUST perform
  the transfer.

### Key Entities

- **Contributor**: The polymorphic base for everyone credited on portal content, holding the
  attribution data common to both kinds — name, other names, description, image, related resources,
  location, languages, configuration, and the timestamps. It has its own table and its own public
  identifier.

- **Person**: A contributor who is an individual, and simultaneously the portal's account record. A
  person may exist purely for attribution, with no email address and no usable password, and may
  later claim that record rather than a duplicate being created beside it.

- **Organisation**: A contributor that is an institution, carrying a type from the ROR set, an
  optional parent, and the city and country it is based in. Its members are people, held through
  affiliations.

- **Affiliation**: One person's membership of one organisation, over a period recorded to whatever
  precision is known, at a membership type that is also what confers ownership. At most one of a
  person's affiliations is primary.

- **Contribution**: One contributor's credit on one project, dataset, sample or measurement,
  carrying the roles they played and the organisation to credit them under. There is one per
  contributor per object.

- **ContributorIdentifier**: One external identifier of one type belonging to one contributor. This
  specification covers the record and its rules. What populates it is elsewhere.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A person and an organisation are created, retrieved through the base, and each comes
  back as its own type carrying the shared fields; each has a public identifier that a second save
  does not change.
- **SC-002**: A language preference outside ISO 639-1 is refused with a message naming the value,
  and a valid one is accepted.
- **SC-003**: The portal's account model is the person record, asserted by name; a person created
  for attribution has no email address, has no usable password, is eligible for activation, and an
  attempt to authenticate as them fails.
- **SC-004**: A person in each of the four account states reports that state; no person reports two;
  and the four state filters together return the whole population exactly once.
- **SC-005**: A claimed person's attempt to clear their email address is refused, and a second
  person cannot take an address already in use.
- **SC-006**: An organisation type outside the ROR set is refused, and every member of that set is
  asserted by name rather than by iterating whatever the code happens to hold.
- **SC-007**: A parent organisation is deleted and its sub-organisation survives with no parent, its
  members and its credits intact.
- **SC-008**: A second membership of the same organisation by the same person is refused; a
  membership with no end date is current and one with an end date is not; year-only, year-month and
  full-date precision all round-trip; and marking a second membership primary unmarks the first.
- **SC-009**: An owner membership confers management rights on that organisation and on no other; a
  demotion withdraws them on the next check with no intervening step; an organisation with no owner
  confers them on nobody; and a transfer leaves the incumbent an administrator and the successor the
  owner.
- **SC-010**: One contributor credited on one object under two roles is a single credit carrying
  both; a second credit for the same pairing is refused; and a person credited without a named
  organisation carries their primary one.
- **SC-011**: A contributor credited across all four kinds of research output reports each of them,
  reports counts by kind, and reports the contributors most often credited alongside them.
- **SC-012**: Deleting a person's credit on an object withdraws that person's object-level rights
  over it, proven by checking a right before and after.
- **SC-013**: A second identifier of a type a contributor already carries is refused; a person's
  default identifier type is ORCID and an organisation's is ROR.
- **SC-014**: Every query in FR-041 and FR-042 returns exactly the records it names against a
  fixture containing the cases it distinguishes, and each is reachable both from the queryset and
  from the manager.
- **SC-015**: The person screen presents account and profile fields together; the organisation
  screen presents both an editable member list and a sub-organisation list, asserted by the presence
  of the inline itself rather than by any field name appearing in the page; the claim-status filter
  agrees with the state the record reports; and the ownership transfer action performs a transfer.

## Assumptions

- The framework's controlled vocabulary of contribution roles is the authority on which roles exist.
  This specification names none of its members.
- ROR's set of organisation types is stable enough to embed as a controlled set, and changes to it
  arrive as ordinary vocabulary maintenance.
- A person's given and family names are recorded because DataCite asks for them, not because every
  name in the world divides that way. Where it does not, the preferred name is the record.
- Geographic location is held by the framework's own location record, not by coordinates on the
  contributor.
- The portal has an authentication system; this specification supplies the record it authenticates
  against and nothing else about it.

## Out of scope

- Every page a researcher uses to browse, create or edit a contributor, the plugins that attach to a
  contributor's page, and the forms, widgets and components those pages use — a later specification
  (D1).
- Fetching data from ORCID and ROR, refreshing it on a schedule, and recording the outcome of a
  fetch, along with the fields that hold what was fetched and when — the external identifier
  synchronisation specification (D2, D3).
- Exporting contributor metadata to DataCite, Schema.org, CSL or any other format, the interface for
  defining further such formats, and the generation of formatted citations — the contributor
  metadata export specification (D2, D11).
- What a contributor's configuration store holds, including any privacy policy expressed in it, and
  the enforcement of such a policy at any response boundary — a later specification (D9).
- Which portal-wide administrative roles exist and what they may do, including whether staff who are
  not superusers manage every organisation (D10).
- Claiming a profile, merging duplicates, and detecting candidates for either — `010-profile-claiming`.
- The REST API's representation of a contributor — `011-restful-api`.
- Bulk import of contributors from spreadsheets.
- A person's position or job title at an institution (D7).
