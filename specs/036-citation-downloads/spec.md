# Feature Specification: Download a record's citation as BibTeX or RIS

**Feature Branch**: `036-citation-downloads`

**Created**: 2026-11-13

**Status**: Draft

**Goals**: G10: data and metadata are reachable by machines through a documented API. G14: dataset
metadata is complete enough for a formal-publication addon to submit it unaided.

**Roadmap**: none. No roadmap item covers citation formats. The feature comes from the redesign of
the overview pages (#668).

**Input**: #673. A reader who wants to cite a project, dataset, sample or measurement can copy its
citation as text, but a reference manager needs a file. Every record's citation is given as BibTeX
and RIS as well, both to copy from the Cite panel and to download as a file. Each format is served
at an address of its own, so a reference manager or a script can fetch it. The formats are built
from the record itself, not from the citation text.

## What exists, and what this specification changes

Each of the four overview pages (specification 018) gives the record's citation as text, in
DataCite's form: creators, year, title, publisher and identifier. The page offers a way to copy it,
and a note when the citation points at the record's permalink because the record has no DOI or
IGSN. Who counts as a creator, which year is used and what the title says differ by kind of record,
and specification 018 sets them:

- a project names its creators, and the year its work started
- a dataset names its creators, and the year it was published or made available. A dataset with a
  data publication is cited as that publication
- a sample names the people who collected it, and the year it was collected. Its title carries its
  sample type
- a measurement names the people who made it, and the year it was set up. Its title carries its
  measurement type and the sample it was made on

Specification 018 lists exporting a citation among the capabilities that are not available yet
(FR-016). The redesign of the pages (#672) moves the citation to a Cite panel at the head of the
side column and drops that placeholder.

After this feature:

- The Cite panel switches between Text, BibTeX and RIS. Copy copies the format on show, and
  Download saves BibTeX or RIS as a file.
- Each format of each record's citation has an address of its own, which a reference manager, a
  script or a browser can open.
- BibTeX and RIS cite the same work as the text: the same people, year, title, publisher and
  identifier, taken from the record.

**Specification 018 is amended** where this feature changes it. FR-014 says the citation is offered
as text, BibTeX and RIS, to copy and, for BibTeX and RIS, to download. FR-016 no longer lists
exporting a citation. Both are rewritten in this feature's pull request so specification 018 reads
as the pages now are.

## Boundary

- **The redesigned pages and the Cite panel itself** (its place at the head of the side column, its
  text citation and its Copy) are carried into `main` by #672. This feature adds the formats to that
  panel.
- **How a record's citation is worded** is unchanged. Who is named, which year and what title stay
  as specification 018 sets them, and BibTeX and RIS follow them.
- **Other citation styles** (APA, Chicago and the like, or a style switch for the text) are not part
  of this feature. The text stays in DataCite's form.
- **A contributor's metadata in other formats**, and the contributor transforms, belong to #245.
  This feature cites records, not people.
- **Metadata downloads** (a record's full metadata as a file, specification 018 FR-016) are a
  different capability and stay listed there as not yet available.
- **The API** (specification 011) is unchanged. The formats are served at addresses of the
  record's own, beside its page.
- **The overview pages of people and organizations** (specification 019) are not part of this
  feature.

## Clarifications

### Session 2026-11-13

The feature was agreed from the prototype the maintainer had already seen (#668), and each question
was answered from it and from the issue, without putting it to him again. The longer reasoning is in
[decisions.md](decisions.md).

- Q: The issue says the formats name "the people credited as creators, or everyone credited when no
  one is". The text citation names different people for a sample and a measurement. Which wins?
  → A: The formats name exactly the people the text citation names. Two citations of one record that
  disagree about who made it would be a defect, and specification 018 already settled who each kind
  of record credits. The issue's wording came from the prototype, which builds every kind of record
  the same way.
- Q: A dataset with a data publication is cited as that publication. Is its BibTeX and RIS the
  publication's or the dataset's? → A: The publication's, so that all three formats cite the same
  work, and the panel's note to cite the publication holds for each of them.
- Q: Which entry type does each kind of record take? → A: A dataset and a measurement are data in
  both formats. A project and a sample have no closer type in either format and take the general
  one. A dataset cited as its data publication takes the publication's own type.
- Q: Who may open a format's address? → A: Whoever may open the record's page. Anyone else gets the
  same answer as for the page, so the address tells nobody that a private record exists.
- Q: Is Download offered for the text? → A: No. Text is for pasting, and Download is offered for
  BibTeX and RIS only, as on the prototype.
- Q: Does the panel remember the format a reader chose? → A: Yes. The prototype keeps it in the
  browser, so a reader who works in BibTeX sees BibTeX on the next record they open.
- Q: What does a format say for a record with no DOI or IGSN? → A: It gives the record's permalink as
  its address, as the text does, and no DOI.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A reader takes a record's citation in the format their reference manager reads (Priority: P1)

A reader on a project's, dataset's, sample's or measurement's page wants to cite it. In the Cite
panel they switch from Text to BibTeX or RIS, then copy it or download it as a file and import it
into their reference manager.

**Why this priority**: this is the feature. A reference manager imports a file, not a sentence, so
until the panel offers one a reader retypes the citation by hand.

**Independent Test**: on a page of each of the four kinds, switch the Cite panel to each format,
copy it and download it, then read each file with a BibTeX or RIS parser and compare what it gives
back with the record.

**Acceptance Scenarios**:

1. **Given** the page of a project, dataset, sample or measurement, **When** a reader opens it,
   **Then** the Cite panel offers the citation as Text, BibTeX and RIS, and shows the text.
2. **Given** the Cite panel, **When** the reader chooses BibTeX or RIS, **Then** the panel shows the
   citation in that format, and choosing Text shows the text again.
3. **Given** the Cite panel showing any format, **When** the reader copies it, **Then** what they
   copied is the citation in that format, complete.
4. **Given** the Cite panel showing BibTeX or RIS, **When** the reader downloads it, **Then** they
   get a file in that format that a reference manager imports as one entry. **Given** the panel
   showing Text, **Then** no download is offered.
5. **Given** a record, **When** its BibTeX or RIS is read back by a parser for that format, **Then**
   it gives the same people in the same order, year, title, publisher and DOI or address as the
   record's text citation.
6. **Given** a record with no DOI or IGSN, **When** its BibTeX or RIS is read, **Then** it gives the
   record's permalink as its address and no DOI. **Given** a project, dataset or measurement with a
   DOI, or a sample with an IGSN, **Then** it gives that identifier and its resolver's address.
7. **Given** a dataset with a data publication, **When** its BibTeX or RIS is read, **Then** it
   cites the data publication, as the text does.
8. **Given** a record whose citation names nobody, **When** its BibTeX or RIS is read, **Then** it
   has no author and is otherwise complete. **Given** a person or organization whose name holds
   characters that BibTeX treats as markup, or letters outside English, **Then** the name reads
   back as it is written on the record.
9. **Given** a reader who chose BibTeX or RIS on one record's page, **When** they open another
   record's page in the same browser, **Then** the Cite panel shows that format.
10. **Given** a portal's own sample or measurement type, **When** a reader opens a record of it,
    **Then** its Cite panel offers all three formats, with no work by the portal's developer.

---

### User Story 2 - A reference manager or a script fetches a record's citation from its address (Priority: P2)

A reader, their reference manager or a script they wrote wants a record's citation without opening
its page. They open the address of the format they need and get the citation in that format.

**Why this priority**: the panel is how most readers will cite a record. An address of its own lets
a tool fetch the citation for many records, and gives the panel's Download something to save.

**Independent Test**: for a record of each kind, open the address of its BibTeX and of its RIS
without a browser, check what kind of file each answer says it is and parse it. Then open the
address of a private record as someone who may not see it, and of a record that does not exist.

**Acceptance Scenarios**:

1. **Given** a record a visitor may open, **When** they open the address of its BibTeX or its RIS,
   **Then** the answer is the citation in that format, marked as that kind of file, and the same
   citation the Cite panel shows.
2. **Given** that answer, **When** a browser opens it, **Then** it saves it as a file named after
   the record, with the extension of its format.
3. **Given** a private record, **When** someone who may not open its page opens the address of one
   of its formats, **Then** the answer is the same as for its page. **When** someone who may open
   the page does, **Then** they get the citation.
4. **Given** an address of a format for a record that does not exist, **When** anyone opens it,
   **Then** they get the portal's not-found answer.
5. **Given** the Cite panel, **When** a reader downloads BibTeX or RIS, **Then** what they get is
   what the format's address answers.

---

### Edge Cases

- A sample is cited only by someone who may open it, which follows its dataset. A measurement whose
  sample the viewer may not open is cited with the sample's place in its title held as the text
  holds it.
- A title with characters BibTeX or RIS treat as markup, such as braces, percent signs or a line
  break, reads back as written.
- A record cited in a language other than English gives the same citation in each format: the
  format's own field names are never translated, and the record's values are never altered.
- A portal with no site name gives no publisher, in the text and in both formats alike.
- Two records with the same title get files of the same name. Nothing in the file depends on its
  name, so a reference manager imports both.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Cite panel on the overview page of every project, dataset, sample and measurement
  MUST offer the record's citation as Text, BibTeX and RIS, and show the text until the reader
  chooses another. (US1)
- **FR-002**: Copy MUST copy the format on show, complete. Download MUST be offered for BibTeX and
  RIS and MUST NOT be offered for the text. (US1)
- **FR-003**: The panel MUST remember in the reader's browser the format they last chose, and show
  it on the next record they open. (US1)
- **FR-004**: BibTeX and RIS MUST be built from the record. They MUST give the same people in the
  same order, year, title, publisher and DOI or address as the record's text citation, and MUST
  cite a dataset with a data publication as that publication. (US1)
- **FR-005**: A record with a DOI, or a sample with an IGSN, MUST give that identifier and its
  resolver's address in both formats. A record with neither MUST give its permalink as its address
  and no DOI. (US1)
- **FR-006**: Each format MUST be valid for its format: a standard parser for it MUST read it as one
  entry and give back every value as it is written on the record, whatever characters it holds.
  (US1)
- **FR-007**: The entry type MUST be data for a dataset and a measurement, the general type for a
  project and a sample, and the publication's own type for a dataset cited as its data
  publication. (US1)
- **FR-008**: Every sample and measurement type a portal registers MUST get the formats without any
  work by the portal's developer. (US1)
- **FR-009**: Each format of each record's citation MUST have an address of its own. Its answer MUST
  say what kind of file it is and MUST ask a browser to save it as a file named after the record.
  (US2)
- **FR-010**: A format's address MUST answer whoever may not open the record's page as the page
  does, and MUST answer an unknown record with not found. (US2)
- **FR-011**: The panel's Download MUST give what the format's address answers. (US2)
- **FR-012**: Specification 018 MUST be rewritten where this feature changes it: FR-014 to offer the
  three formats, and FR-016 to no longer list exporting a citation. (US1)

### Key Entities

- **Citation**: what a record's overview page gives for citing it, worded as specification 018 sets
  for its kind. Not stored. Built from the record each time.
- **Citation format**: one way of writing the citation. Text is DataCite's form for reading and
  pasting. BibTeX and RIS are the files reference managers import. Each has an address of its own.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For every kind of record, and every sample and measurement type a portal registers,
  the Cite panel offers the citation as Text, BibTeX and RIS.
- **SC-002**: Every BibTeX and RIS file the portal gives is read by a standard parser for its format
  as one entry, with the same people, year, title, publisher and identifier as the record's text
  citation.
- **SC-003**: A reader goes from a record's page to its citation in their reference manager with one
  download and one import, typing nothing.
- **SC-004**: No format's address tells anyone anything about a record that its page would not.

## Assumptions

- #672's first pull request, which carries the Cite panel into `main` with its text citation and
  Copy, is merged before this feature is built. The issue records the dependency.
- The permalink (specification 034) stays the address a citation gives for a record with no DOI or
  IGSN.
- BibTeX and RIS are the two formats reference managers import most widely. Others, such as CSL
  JSON or EndNote XML, can be added later as more formats in the same panel.
