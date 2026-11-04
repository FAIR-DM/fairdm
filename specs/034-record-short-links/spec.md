# Feature Specification: Open any record from its portal ID at a short, permanent link

**Feature Branch**: `034-record-short-links`

**Created**: 2026-11-04

**Status**: Draft

**Goals**: G14: dataset metadata is complete enough for a formal-publication addon to submit it
unaided. G15: external identifiers for people, organisations and samples are carried through the
record.

**Roadmap**: none. No roadmap item covers record links, so this is a gap in the roadmap.

**Input**: #650. Every project, dataset, sample, measurement, person and organization already has
a portal ID whose first letter says what kind of record it is. A visitor opens any record from its
ID alone, at the portal's root, and is taken to the record's page wherever it lives. That gives
every record a short link that stays the same when a portal changes how its page addresses are
laid out.

## What exists, and what this specification changes

Every core record carries a portal ID: 23 characters, of which the first names the record's kind.
`p` is a project, `d` a dataset, `s` a sample, `m` a measurement and `c` a contributor, a person or
an organization. The ID already appears on each record's page, in the identifiers card, with a
button that copies it.

A record's page address is built from its kind and its ID: `/projects/<id>/`, `/datasets/<id>/`,
`/measurements/<id>/`, and so on. Anyone who shares or cites a record today shares that address,
so a portal that rearranges its addresses breaks every link it has handed out. Where a dataset has
no DOI, or a sample no IGSN, the citation the portal writes points at that address too, and so does
a dataset's DataCite export.

After this feature:

- `<portal>/<portal ID>/` opens the record with that ID, for all six kinds of record.
- The identifiers card offers that link, and copying it copies the whole link.
- A citation with no DOI or IGSN to point at, and a dataset's DataCite export, give that link.

## Boundary

- **Collections and other records without a portal ID** get no link here.
- **The API** is unchanged. The `url` each record carries in the API stays the address of its page.
- **Persistent identifiers issued by outside services**, such as DOIs and IGSNs, are not minted or
  changed by this feature. Where a record has one, citations go on pointing at it.
- **Changing where any record's page lives** is not part of this feature. It makes such a change
  safe later.

## Clarifications

### Session 2026-11-04

Each question was answered from the maintainer's replies while the feature was agreed, without
putting it to him again. The longer reasoning is in [decisions.md](decisions.md).

- Q: Does the link live under its own prefix, such as `/id/<portal ID>/`, or at the portal's root?
  → A: At the root. Only an address shaped exactly like a portal ID is read as one: one of the five
  letters followed by 22 characters. No word a portal uses for its own pages has that shape, and a
  page the portal or an addon declares always wins over the link.
- Q: Should a browser remember where a link led? → A: No. A link is followed afresh every time, so
  when a portal moves its pages, everyone who opens an old link reaches the new page, including
  people who opened it before the move.
- Q: May the link tell a visitor that a private record exists? → A: It tells them nothing the
  record's page would not. A visitor who opens the link of a record they may not see gets the same
  answer as if they had opened its page directly.
- Q: Is the ID case-sensitive? → A: Yes, as it is everywhere else. An ID is copied, not typed, and
  two IDs may differ only in case.
- Q: Which page does a sample, a measurement or a contributor reach? → A: The page of the kind it
  really is: a sample's page for its own sample type, a measurement's for its own measurement type,
  a person's page for a person and an organization's for an organization.
- Q: Where does the link appear? → A: On the record's page, in its identifiers card, and wherever
  the portal cites a record that has no DOI or IGSN, including a dataset's DataCite export.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A visitor opens a record from its portal ID (Priority: P1)

A visitor has a record's portal ID, from a sample label, a paper or a colleague, and opens
`<portal>/<portal ID>/`. They land on the record's page, wherever the portal keeps it.

**Why this priority**: this is the feature. Without it there is no short link to share.

**Independent Test**: create one record of each kind, open each one's link and check where it
lands, then open the link of a record that does not exist.

**Acceptance Scenarios**:

1. **Given** a public project, **When** a visitor opens the link made from its portal ID, **Then**
   they arrive at the project's page. The same holds for a public dataset, sample, measurement,
   person and organization.
2. **Given** a sample of a portal's own sample type, **When** a visitor opens its link, **Then**
   they arrive at the page for that sample type. The same holds for a measurement of a portal's own
   measurement type, and for a person or an organization.
3. **Given** an address shaped like a portal ID that belongs to no record, including the ID of a
   record that has been deleted, **When** a visitor opens it, **Then** they get the portal's
   not-found page.
4. **Given** a private record, **When** a visitor who may not see it opens its link, **Then** the
   answer is the same as if they had opened the record's page directly. **When** someone who may
   see it opens the link, **Then** they arrive at its page.
5. **Given** a visitor who has opened a record's link before, **When** the portal has since moved
   that kind of record's pages to new addresses, **Then** opening the same link takes them to the
   new page.
6. **Given** a link written without its closing slash, **When** a visitor opens it, **Then** they
   arrive at the record's page as with the slash.
7. **Given** any address at the portal's root that is not shaped like a portal ID, or a page the
   portal or an addon declares at the root, **When** a visitor opens it, **Then** it behaves
   exactly as it did before this feature.

---

### User Story 2 - A visitor shares or cites a record by its permanent link (Priority: P2)

A visitor reading a record's page wants a link to it that will keep working: to print on a label,
put in a paper or send to someone. They take it from the record's identifiers, and the portal's
own citations use it too.

**Why this priority**: the link only lasts if it is the one people pass on. Until the portal hands
it out, people go on sharing page addresses.

**Independent Test**: open a record's page, copy its link from the identifiers card and open it;
read a citation for a dataset with no DOI and a sample with no IGSN; export a dataset's DataCite
record.

**Acceptance Scenarios**:

1. **Given** a record's page, **When** a visitor reads its identifiers, **Then** the record's link
   is there, and opening it reaches the record.
2. **Given** a record's page, **When** a visitor copies the link from its identifiers, **Then**
   what they copied is the whole link, which opens the record when pasted into a browser.
3. **Given** a dataset with no DOI, a sample with no IGSN, or a measurement, **When** the portal
   writes its citation, **Then** the citation points at the record's link.
4. **Given** a dataset with a DOI, or a sample with an IGSN, **When** the portal writes its
   citation, **Then** the citation points at the DOI or IGSN as it does today.
5. **Given** a dataset, **When** its DataCite record is exported, **Then** the web address it gives
   for the dataset is the dataset's link.

---

### Edge Cases

- An address with an ID of the right length but a letter no kind uses is not a portal ID, and gets
  whatever answer the portal gives that address today.
- A portal ID that differs from a real one only in case belongs to no record, and gets the
  not-found page.
- A person who has not claimed their profile, or whose account is deactivated, still has a page.
  Their link reaches it.
- A link followed with a query string or fragment attached reaches the record's page. What the
  page does with them is the page's own business.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every project, dataset, sample, measurement, person and organization MUST be
  reachable at `<portal>/<portal ID>/`. (US1)
- **FR-002**: The link MUST lead to the page of the record's own kind: its sample or measurement
  type for a sample or a measurement, and its person or organization page for a contributor. (US1)
- **FR-003**: An address shaped like a portal ID that belongs to no record MUST get the not-found
  page. (US1)
- **FR-004**: Only an address shaped exactly like a portal ID MUST be read as one. Every other
  address, and every page the portal or an addon declares at its root, MUST behave as it did
  before. (US1)
- **FR-005**: A link MUST tell a visitor nothing about a record that its page would not. (US1)
- **FR-006**: A link MUST be followed afresh each time, so that a change to where records' pages
  live reaches every visitor, including those who opened the link before. (US1)
- **FR-007**: A record's identifiers MUST include its link, and copying it MUST copy the whole
  link. (US2)
- **FR-008**: A citation the portal writes for a record with no DOI or IGSN MUST point at the
  record's link. A citation for a record with a DOI or IGSN MUST point at that identifier as
  before. (US2)
- **FR-009**: A dataset's DataCite export MUST give the dataset's link as its web address. (US2)

### Key Entities

- **Portal ID**: the identifier every core record carries, the existing `uuid` field. Its first
  letter names the record's kind. Unchanged by this feature.
- **Record link**: `<portal>/<portal ID>/`. Not stored. It is the portal ID put at the portal's
  root.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For each of the six kinds of record, a record's link reaches its page.
- **SC-002**: When a kind of record's page address changes, every link handed out before the change
  still reaches the record, with no change to the link.
- **SC-003**: Every page address the portal served before this feature is answered as it was.
- **SC-004**: A record with no DOI or IGSN is cited by its link everywhere the portal writes a
  citation for it.

## Assumptions

- Portal IDs keep their present form: one letter for the kind, then 22 characters. A portal that
  changes the ID's form is outside this feature.
- No two kinds of record share a letter, other than people and organizations, which share `c` and
  are told apart by the record itself.
