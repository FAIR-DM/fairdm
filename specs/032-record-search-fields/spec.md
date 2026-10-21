# Feature Specification: Autocomplete fields for records, people and organizations

**Feature Branch**: `032-record-search-fields`

**Created**: 2026-10-21

**Status**: Draft

**Goals**: G5: a modern, extensible interface that every portal gets by default, with no frontend
work. G6: core records can be created and edited by hand through the portal. G9: records in the
core model can be searched, sorted and filtered from the portal. G12: private and public data sit
side by side, controlled per object.

**Roadmap**: none. No roadmap item covers choosing a related record in a form or filter, so this
is a gap in the roadmap. The nearest are R16, every core record type can be created and edited in
the portal, and R17, records can be found, sorted and filtered.

**Input**: #541. FairDM provides searchable fields, backed by views, that portals reuse wherever a form
or filter chooses a project, dataset, sample, measurement, person or organization. One field finds
the public records and the private records the person typing may see. Results show more than a
name and are grouped where grouping helps. Each field comes ready to use in a single and a
multiple form, so a portal developer never wires a view, an address or a script. The fields are
built on django-tomselect with the styling django-mvp-forms provides, and every other autocomplete
library is removed. This feature also resolves #304.

## What exists, and what this specification changes

FairDM draws its searchable selects with three libraries at once: django-autocomplete-light,
django-select2 (with django-addanother wrapped around it), and a Selectize widget nothing uses.
None of them filters by visibility. Several are broken today:

- The sample and measurement forms search datasets on a `title` field that `Dataset` does not
  have.
- The person form's affiliations field and the contribution form's roles field ask for addresses
  that do not exist, so drawing either one fails (#304).
- The "add another" wrapper does not render correctly in the portal, which is why the dataset form
  fell back to plain dropdowns in #295.
- The organization search reads a `label` attribute that organizations do not have.
- The measurement form marks its sample field as depending on the dataset, and nothing acts on it.

Fields that need a search and have none list every row in a plain dropdown: the dataset form's
data publication, the project form's owner, and the related-record filters on the project,
dataset, sample and measurement lists.

After this feature:

- FairDM provides a single and a multiple field for each of projects, datasets, samples,
  measurements, people and organizations. Each comes with its view and its address already in
  place.
- Every field offers only what the person using it may see, and a developer sets per field whether
  private records are offered at all.
- Results show the details that tell two similar records apart, grouped by how the person typing
  relates to them.
- Every form, filter and generated component in FairDM that chooses one of these records uses the
  new fields.
- The data publication field, the tag field and the ROR lookup move to django-tomselect as well.
- django-autocomplete-light, django-select2, django-addanother and the Selectize widget are gone,
  together with `fairdm.contrib.autocomplete` and its addresses.

## Needs today, and needs expected later

The fields are designed around everything below. Only the first table is built by this feature.
The second is listed so that nothing built now rules any of it out.

**Where FairDM chooses a related record today**

| Where | Chooses | Single or multiple | Private records offered |
|---|---|---|---|
| Sample form, measurement form | the dataset the record belongs to | single | those the person may edit |
| Measurement form | the sample it was made on, narrowed to the chosen dataset | single | those the person may view |
| Dataset form | the project it belongs to | single | those the person may edit |
| Dataset form | its data publication | single | not applicable |
| Project form | the owning organization | single | not applicable |
| Person form, affiliation form | organizations | multiple, single | not applicable |
| Organization profile | its parent organization | single | not applicable |
| Person merge, ownership transfer | the person to merge into or transfer to | single | not applicable |
| Project list filter | owner, contributor | multiple | none |
| Dataset list filter | project | multiple | none |
| Sample list filter | dataset | multiple | none |
| Measurement list filter | dataset, sample | multiple | none |
| Filters generated for a registered type | a related project, dataset, sample or measurement | multiple | none |
| Record forms | tags | multiple, free entry | not applicable |
| Organization form | its ROR record | single, outside the portal | not applicable |

**Needs expected later, not built here**

- Creating a related record from inside the form, which the "add another" wrapper was meant to
  give.
- A field for any registered model, beyond the six built here.
- Finding people and organizations outside the portal, through ORCID and ROR, to add them as new
  contributors.
- Fields for licences and for places.
- Filters on lists of one person's records, such as the projects on their profile, which use the
  setting this feature provides for them.
- Choosing records held by another portal (R29).
- Ranked, typo-tolerant matching once R17 provides it.

## Boundary

- **Vocabulary concepts** are out of scope. A dedicated concept field will come from
  django-controlled-vocabularies. Until then the keyword filters and the contribution roles field
  keep working without django-autocomplete-light.
- **Enforcing visibility on every other surface** is R14. These fields apply the visibility rules
  that exist when they are built.
- **Ranked search** is R17. These fields match what is typed against a few fields and put exact
  identifiers first.
- **Adding a contributor to a record**, through the tabbed search of the portal, the registry and a
  new person, keeps its own flow.
- **The Django admin's built-in `autocomplete_fields`** stay as they are. Admin pages that use
  django-autocomplete-light or django-select2 move to them.
- **Creating a record from inside a form** is not part of this feature.

## Clarifications

### Session 2026-10-21

Each question was answered from the maintainer's replies while the feature was agreed, without
putting it to him again. The longer reasoning is in [decisions.md](decisions.md).

- Q: Which private records does a field offer? → A: It depends on what the field is for. A field
  that places a record inside another, such as the dataset a new sample goes into, offers the
  records the person may edit. A field that links to a record offers the records the person may
  view. A filter on a public list, such as the portal's project or dataset list, offers public
  records only. A developer can change any of these defaults.
- Q: Does a signed-in researcher see their own private records in a public list's filter? → A: No.
  A public list shows public records to everyone, so its filter offers public records to everyone,
  signed in or not. Someone who is not signed in gets public records from every field, and nothing
  from a field that offers only records the person may edit.
- Q: What about a list of one person's records, such as the projects on their profile? → A: That
  person sees their private records and their public ones, and everyone else sees the public ones
  only. A filter on such a list offers the same: the person's private records when they are the
  one viewing, and public records to anyone else.
- Q: What counts as public? → A: The rules FairDM already applies when the feature is built. A
  project is public when its visibility is public. A dataset is public when it and its project are
  public. A sample or measurement is public when its dataset is public and published. Making these
  consistent everywhere is R14.
- Q: A record already links to a private record the person editing it cannot see. What does the
  field do? → A: It keeps the link, shows it as a private record without its name, and never
  offers it in a search. Saving the form unchanged keeps the link.
- Q: Someone holds a portal-wide role that lets them view every record, such as Data Curator. What
  do they get? → A: Every record their role allows, with the records they contribute to grouped
  first.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A researcher chooses the dataset a new sample goes into (Priority: P1)

A researcher adds a sample and has to say which dataset it belongs to. They type part of the
dataset's name and see the datasets they may edit, their own private ones among them. Each result
shows the project it belongs to and whether it is private, so two datasets with similar names can
be told apart. They choose one and save. The same field chooses the dataset of a measurement, and
a field like it chooses the project of a dataset.

**Why this priority**: The sample and measurement forms carry a broken control today (#304), and
choosing where a record goes is the first thing anyone entering data does.

**Independent Test**: Sign in as a researcher who can edit one private dataset, open the sample
form, search for a dataset, choose it and save.

**Acceptance Scenarios**:

1. **Given** a researcher who can edit a private dataset, **When** they search the sample form's
   dataset field for part of its name, **Then** the dataset is offered.
2. **Given** a public dataset the researcher cannot edit, **When** they search for it in the sample
   form's dataset field, **Then** it is not offered.
3. **Given** a private dataset the researcher cannot see, **When** they search for it, **Then** it
   is not offered.
4. **Given** offered datasets, **When** the results are shown, **Then** each gives its project and
   whether it is private.
5. **Given** a dataset chosen in the field, **When** the form is saved, **Then** the sample belongs
   to that dataset.
6. **Given** a dataset the researcher cannot edit, **When** its identifier is submitted in the
   dataset field anyway, **Then** the form is refused and nothing is saved.
7. **Given** a researcher who can edit a private project, **When** they search the dataset form's
   project field, **Then** the project is offered, and projects they cannot edit are not.
8. **Given** a search matching more datasets than one page of results holds, **When** the
   researcher asks for more, **Then** the next page is offered.

---

### User Story 2 - A researcher chooses the sample a measurement was made on (Priority: P1)

A researcher adds a measurement. Once they have chosen its dataset, the sample field offers only
that dataset's samples. They find the sample by its name, its local ID or an identifier it
carries, and each result shows the sample's type and local ID. Typing an identifier exactly puts
that sample first.

**Why this priority**: A measurement's sample field lists every sample in the portal today, which
is unusable in a portal of any size.

**Independent Test**: Choose a dataset on the measurement form, search the sample field, and check
that only that dataset's samples are offered.

**Acceptance Scenarios**:

1. **Given** a dataset chosen on the measurement form, **When** the researcher searches the sample
   field, **Then** only samples in that dataset are offered.
2. **Given** a sample, **When** the researcher types its local ID or an identifier it carries,
   **Then** that sample is offered first.
3. **Given** offered samples, **When** the results are shown, **Then** each gives its type, its
   local ID and its dataset.
4. **Given** a sample chosen, **When** the researcher changes the dataset, **Then** the sample
   field is cleared.
5. **Given** a sample from another dataset, **When** it is submitted with the form anyway, **Then**
   the form is refused and nothing is saved.

---

### User Story 3 - A visitor filters a public list by a related record (Priority: P1)

A visitor, signed in or not, filters the sample list by dataset. They search for datasets by name,
tick several, and the list narrows to samples in any of them. The field offers public datasets
only, to everyone, signed in or not, because the list itself shows only public records. The
project, dataset and measurement lists filter by their related records the same way. On a list of
one person's records, such as the projects on their profile, the filter also offers that person's
private records when they are the one viewing it.

Because these lists are public, so are their fields' addresses. Someone hammering an address with
requests is cut off once over a limit, and everyone else carries on searching.

**Why this priority**: Every list in the portal carries a related-record filter that loads every
row today, and these are the fields most visitors use.

**Independent Test**: Without signing in, open the sample list, search the dataset filter, tick two
datasets, and check the list holds only their samples.

**Acceptance Scenarios**:

1. **Given** a visitor who is not signed in, **When** they search the sample list's dataset filter,
   **Then** public datasets are offered and private ones are not.
2. **Given** a signed-in researcher with a private dataset, **When** they search the same filter,
   **Then** their private dataset is not offered.
3. **Given** two datasets ticked in the filter, **When** it is applied, **Then** the list holds
   samples from either dataset and no others.
4. **Given** a filtered list, **When** its address is opened again, **Then** the filter shows the
   same datasets chosen.
5. **Given** a registered sample type with a related dataset, **When** its list's generated filter
   is searched, **Then** it behaves as the sample list's dataset filter does.
6. **Given** the project list, **When** a visitor searches its owner and contributor filters,
   **Then** organizations and people are offered and the list narrows to the ones ticked.
7. **Given** a filter on a list of one person's records, **When** that person searches it, **Then**
   their private records and the public ones are offered.
8. **Given** the same filter, **When** anyone else searches it, **Then** only public records are
   offered, including to someone who may view that person's private records elsewhere.
9. **Given** a caller over a field's request limit, **When** they search again, **Then** the
   request is refused without searching, and the field says searching is paused.
10. **Given** one caller over the limit, **When** another visitor searches the same filter,
    **Then** the other visitor's search is answered as normal.

---

### User Story 4 - A portal developer adds a record field to a form or filter (Priority: P1)

A portal developer building a form for their own sample type wants a field that chooses a project.
They import FairDM's project field, put it on their form, and it works: no view, no address and no
script of their own. They choose the single or the multiple field, and they can say whether
private records are offered, what access a private record needs, which registered sample or
measurement type the field is narrowed to, and which other field on the form narrows it.

**Why this priority**: The fields are only reusable if a developer can use them without the wiring
that broke the current ones.

**Independent Test**: Put the project field and a sample field narrowed to one registered type on a
test form, render it, search each, and save.

**Acceptance Scenarios**:

1. **Given** a form with FairDM's project field and nothing else configured, **When** it is
   rendered and searched, **Then** it offers projects the person may see.
2. **Given** the multiple form of a field, **When** several records are chosen and the form is
   saved, **Then** every chosen record is saved.
3. **Given** a field set not to offer private records, **When** a researcher with private records
   searches it, **Then** none of their private records is offered.
4. **Given** a field set to need edit access, **When** a researcher searches it, **Then** only
   records they may edit are offered.
5. **Given** a sample field narrowed to one registered sample type, **When** it is searched,
   **Then** only samples of that type are offered.
6. **Given** a field narrowed by another field on the form, **When** the other field has a value,
   **Then** only records related to that value are offered.
7. **Given** a sample type registered by a portal, **When** its generated form has a related
   dataset, **Then** the form uses FairDM's dataset field with no configuration from the developer.

---

### User Story 5 - A researcher chooses a person or an organization (Priority: P2)

A researcher creating a person record adds their affiliations, a profile maintainer sets an
organization's parent, and a project manager chooses the organization that owns the project. They
type part of a name, an alternative name, an ORCID or a ROR identifier. People they have worked
with come first, and organizations they belong to come first. Each person shows their picture,
their primary affiliation and their ORCID. Each organization shows its city, its country and its
ROR identifier. A person whose profile nobody has claimed is marked as unclaimed, so nobody adds a
second record for them.

**Why this priority**: The person form's affiliations field fails to draw today (#304), but these
fields are used less often than the record fields.

**Independent Test**: Search the person form's affiliations field for an organization by part of
its name and by its ROR identifier, choose it and save.

**Acceptance Scenarios**:

1. **Given** organizations, **When** a researcher searches the affiliations field for part of a
   name or an alternative name, **Then** the matching organizations are offered.
2. **Given** an organization's ROR identifier, **When** it is typed exactly, **Then** that
   organization is offered first.
3. **Given** a researcher who belongs to an organization, **When** a search matches it, **Then** it
   is offered in the group of their own organizations, ahead of the rest.
4. **Given** a researcher who shares records with a person, **When** a search matches that person,
   **Then** they are offered in the group of people the researcher has worked with, ahead of the
   rest.
5. **Given** a person, **When** someone types that person's email address, **Then** the person is
   not offered, and no result shows an email address.
6. **Given** an unclaimed person, **When** they are offered, **Then** the result marks them as
   unclaimed.
7. **Given** a collaboration that exists only through a private record the researcher cannot open,
   **When** the people are grouped, **Then** that person is not counted as someone they have
   worked with.

---

### User Story 6 - A researcher links a dataset to its data publication (Priority: P2)

A researcher editing a dataset sets the publication that describes it. They search the portal's
literature by title, author or DOI instead of scrolling a list of every publication.

**Why this priority**: #304 names it as the field that most needs a search, since it lists every
publication in the portal.

**Independent Test**: With many publications in the portal, search the dataset form's data
publication field by part of a title and by a DOI, choose one and save.

**Acceptance Scenarios**:

1. **Given** publications in the portal, **When** the researcher types part of a title or an
   author's name, **Then** the matching publications are offered.
2. **Given** a publication's DOI, **When** it is typed exactly, **Then** that publication is offered
   first.
3. **Given** offered publications, **When** the results are shown, **Then** each gives its authors
   and year.
4. **Given** a publication chosen, **When** the form is saved, **Then** the dataset links to it.

---

### User Story 7 - A researcher tags a record (Priority: P3)

A researcher adds tags to a record. They see tags already used in the portal as they type, and can
add a tag nobody has used yet.

**Why this priority**: The tag field works today, but it runs on django-select2, which this feature
removes.

**Independent Test**: Add an existing tag and a new one to a record, save, and reopen the form.

**Acceptance Scenarios**:

1. **Given** a tag already used in the portal, **When** the researcher types part of it, **Then**
   it is offered.
2. **Given** a tag nobody has used, **When** the researcher types it and confirms, **Then** it is
   added to the record when the form is saved.
3. **Given** a record with tags, **When** its form is opened again, **Then** its tags are shown
   chosen.

---

### User Story 8 - A profile maintainer looks up an organization's ROR record (Priority: P3)

A profile maintainer editing an organization searches the ROR registry by name and chooses the
matching entry, so the organization carries its ROR identifier.

**Why this priority**: The lookup exists today, but it runs on django-select2's script, which this
feature removes.

**Independent Test**: On the organization form, search ROR for a known institution, choose it and
save.

**Acceptance Scenarios**:

1. **Given** the organization form, **When** the maintainer types part of an institution's name,
   **Then** matching ROR entries are offered with their country.
2. **Given** a ROR entry chosen, **When** the form is saved, **Then** the organization carries that
   ROR identifier.
3. **Given** the ROR registry does not answer, **When** the maintainer searches, **Then** the field
   says the lookup is unavailable and the rest of the form can still be saved.

---

### Edge Cases

- A record links to a private record the person editing it cannot see. The field shows it as a
  private record without its name, does not offer it in a search, and keeps it when the form is
  saved unchanged.
- A record that was chosen is deleted or made private before the form is submitted. The form is
  refused with a message on that field.
- A search with no matches says so.
- A search shorter than the field's minimum length offers nothing and says how much to type.
- The same record matches through two groups, for example a dataset that is both the person's own
  and public. It is offered once, in the first group.
- Someone holds a portal-wide role that can view every record. Records they contribute to are
  grouped first and the rest follow.
- A dependent field's source is cleared. The dependent field is cleared with it.
- A request to a field's address carries a type, a level or a filter the field does not allow. It
  is refused or ignored, and never widens what the field offers.
- One caller sends requests far faster than anyone types. Once over the limit, their requests are
  refused without searching, and other people's searches carry on as normal.
- A request asks for a page size of thousands, a page number deep in the results, or a search text
  thousands of characters long. It gets the field's own limit, never what it asked for.

## Requirements *(mandatory)*

### Functional Requirements

**The fields**

- **FR-001**: FairDM MUST provide a single and a multiple field for each of projects, datasets,
  samples, measurements, people and organizations, each with its view and address already in
  place. (US 4)
- **FR-002**: A developer MUST be able to use any of these fields on a form or a filter by adding
  it, with no view, address, template or script of their own. (US 4)
- **FR-003**: A field MUST let its developer set whether private records are offered, the access
  level a private record needs, and, for sample and measurement fields, the registered type it is
  narrowed to. (US 4)
- **FR-004**: A field MUST let its developer narrow it by the value of another field on the same
  form, and MUST clear itself when that value changes. (US 2, US 4)
- **FR-005**: A field that places a record inside another MUST default to offering private records
  the person may edit. A field that links to a record MUST default to offering records the person
  may view. A filter on a public list MUST default to offering public records only, to everyone.
  (US 1, US 3, US 4)
- **FR-006**: Forms and filters that FairDM generates for a registered model MUST use these fields
  for related projects, datasets, samples and measurements, with no configuration from the
  developer. (US 3, US 4)

**What a field offers**

- **FR-007**: A field MUST NOT offer a record the person may not view, and MUST NOT offer a private
  record at a lower access level than the field needs. (US 1, US 3, US 4)
- **FR-008**: Someone who is not signed in MUST be offered public records only. (US 3)
- **FR-009**: A field MUST be able to offer one person's private records only when that person
  is the one using it, and public records to everyone else, for filters on a list of that
  person's records. (US 3, US 4)
- **FR-010**: A submitted value outside what the field would offer that person MUST be refused when
  the form is validated, and nothing MUST be saved. A value already stored on the record is the
  exception: it is kept when submitted unchanged. (US 1, US 2)
- **FR-011**: A field's address MUST accept only the narrowing its field allows, and MUST NOT offer
  more because a request asked for it. (US 4)
- **FR-012**: A stored link to a record the person cannot view MUST be shown as a private record
  without its name. (US 1)

**Matching and results**

- **FR-013**: Project and dataset fields MUST match on name. Sample fields MUST match on name,
  local ID and identifiers. Measurement fields MUST match on name and local ID. Person fields MUST
  match on name, alternative names and ORCID. Organization fields MUST match on name, alternative
  names and ROR identifier. (US 1, US 2, US 5)
- **FR-014**: An exact match on an identifier MUST be offered first. (US 2, US 5, US 6)
- **FR-015**: Results MUST be offered a page at a time, with further pages on request. (US 1)
- **FR-016**: Record results MUST be grouped as the person's own records first, then public
  records, then any further records a portal-wide role lets them see. A record MUST appear once, in
  its first group. (US 1, US 4)
- **FR-017**: Person results MUST be grouped as people the person has worked with first, then
  everyone else. Organization results MUST be grouped as organizations the person belongs to
  first, then everyone else. Only records the person may open MUST count towards having worked
  with someone. (US 5)
- **FR-018**: Each result MUST give the details that tell it apart: for a project, whether it is
  private; for a dataset, its project and whether it is private; for a sample or measurement, its
  type, local ID and dataset; for a person, their picture, primary affiliation and ORCID, and
  whether their profile is unclaimed; for an organization, its city, country and ROR identifier.
  (US 1, US 2, US 5)
- **FR-019**: A person MUST NOT be found by, or shown with, an email address. (US 5)

**Standing up to abuse**

- **FR-020**: Every field's address MUST limit how many requests one caller makes, over a short
  window and over a day, counting a signed-in caller by account and anyone else by network
  address. Each limit MUST be a setting a portal can change, and the defaults MUST leave room for
  someone typing quickly into several fields. (US 3, US 4)
- **FR-021**: A request over a limit MUST be refused before any search runs, with an answer that
  says the caller made too many requests and when to try again. The field MUST tell the person
  typing that searching is paused, and the rest of the form MUST keep working. (US 3)
- **FR-022**: The work one request can cause MUST be bounded by the field and not by the request.
  The page size, the longest search text, the number of pages that can be asked for, and the
  narrowing a request may carry are set by the field, and a request asking for more is refused or
  cut to the field's limit. (US 3, US 4)
- **FR-023**: A search MUST NOT run until the text reaches the field's minimum length, and a field
  MUST wait for the person to pause before it asks for results, so typing a word sends one request
  rather than one per keystroke. (US 3, US 4)
- **FR-024**: A request that fails to search, for any reason, MUST NOT tell the caller more than
  that the search failed. (US 3)
- **FR-025**: The ROR lookup MUST be limited in the same way, so the portal cannot be used to send
  the ROR registry more requests than the portal's own limits allow. (US 8)

**Fields moved off the removed libraries**

- **FR-026**: Every form and filter in FairDM that chooses a project, dataset, sample,
  measurement, person or organization MUST use these fields, including the forms and filters
  listed under *Needs today*. (US 1, US 2, US 3, US 5)
- **FR-027**: The dataset form's data publication field MUST be searchable by title, author and
  DOI, with an exact DOI first. (US 6)
- **FR-028**: The tag field MUST offer tags already used in the portal and accept new ones. (US 7)
- **FR-029**: The organization form's ROR lookup MUST search the ROR registry, and MUST let the form
  be saved when the registry does not answer. (US 8)
- **FR-030**: The keyword filters and the contribution roles field MUST keep working without
  django-autocomplete-light, until django-controlled-vocabularies provides a concept field. (US 3)
- **FR-031**: Admin pages that use django-autocomplete-light or django-select2 MUST use the Django
  admin's own `autocomplete_fields` instead. (US 4)
- **FR-032**: django-autocomplete-light, django-select2 and django-addanother MUST NOT be
  dependencies of FairDM. `fairdm.contrib.autocomplete`, its addresses and the Selectize widget
  MUST be removed. (US 4)
- **FR-033**: The developer documentation MUST describe each field, its settings and its defaults,
  and every page that documents a removed widget MUST be updated in the same pull request. (US 4)

### Key Entities

- **Autocomplete field**: a form field that chooses one or more records of one kind by searching
  for them. It carries the settings a developer may change: whether private records are offered,
  the access a private record needs, a registered type, and another field that narrows it.
- **Result group**: a heading results are listed under, decided by how the person searching relates
  to each record.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Across every field and every access case the acceptance scenarios cover, no field
  offers, and no form accepts, a record the person may not view or a private record below the
  access level the field needs.
- **SC-002**: With 100,000 samples in the portal, a sample field search returns its first page in
  under one second on the development stack.
- **SC-003**: While one caller sends requests to a field's address as fast as it can, the caller
  is refused once over its limit, and another person's search on the same portal still returns its
  first page within the time SC-002 allows.
- **SC-004**: A person typing a ten-letter word into a field at ordinary speed causes no more than
  three requests, and stays well inside the default limits.
- **SC-005**: Once the feature is built, no module, template, setting or document in FairDM refers
  to django-autocomplete-light, django-select2, django-addanother, Selectize or
  `fairdm.contrib.autocomplete`.
- **SC-006**: Every form and filter listed under *Needs today* renders and saves in the test suite
  with the new fields.
- **SC-007**: A developer adds a working project field to a new form with one field declaration,
  as the documentation's example shows.

## Assumptions

- django-mvp-forms provides the styling for django-tomselect's widgets and the support for
  grouped results, so FairDM adds no styling of its own for them.
- The visibility and access rules are the ones FairDM applies when the feature is built. If R14
  changes them first, the fields follow.
- The concept field from django-controlled-vocabularies is separate work. The stopgap that keeps
  keyword filters and contribution roles working is replaced when it lands.
- `CONTEXT.md` gains the term Autocomplete field, with the difference between a field that places a
  record inside another and one that links to it.

## Breaking changes

- FairDM no longer installs django-autocomplete-light, django-select2 or django-addanother. A
  portal that imports any of them declares its own dependency or moves to the new fields.
- The `autocomplete/` and `select2/` addresses are gone, with the `autocomplete:concept`,
  `autocomplete:contributor` and `autocomplete:organization` names.
- `ConceptSelect`, `ConceptMultiSelect`, `ContributorSelect2Widget`, `PersonSelect2Widget`,
  `OrganizationSelect2Widget`, `SelectizeWidget` and `CreatorsFormField` are removed.
