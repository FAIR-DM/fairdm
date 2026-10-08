# Feature Specification: One set of editing pages for projects, datasets, samples and measurements

**Feature Branch**: `024-shared-editing-pages`

**Created**: 2026-10-02

**Status**: Draft

**Goals**: G6: core records can be created and edited by hand through the portal.

**Roadmap**: none. R12 and R16 delivered editing for projects, datasets, samples and measurements
one record type at a time, and no open item covers bringing those pages together. The feature is one
of seven drawn from the plan in [#397](https://github.com/FAIR-DM/fairdm/issues/397).

**Input**: The pages for editing a record's details, descriptions, keywords, key dates and
identifiers, and for deleting it, exist three times over. Projects carry their own copies, datasets
carry their own, samples use a third generic set, and measurements have none. A fix made in one does
not reach the others, and a measurement cannot be edited through the portal beyond what its create
form offered. There should be one set of six pages (edit details, descriptions, keywords, key dates,
identifiers and delete), registered on projects, datasets, samples and measurements alike, and
reached from the Manage menu, not from tabs. Each is shown only to someone who may use it, and
refused to anyone else.

## Clarifications

### Session 2026-10-02

These questions came out of reading the request against the code as it stands. Each was answered
from the request, the plan in #397 and the earlier specifications, without putting it to the
maintainer. The reasoning is in [decisions.md](decisions.md), which also lists the answers the
maintainer should confirm.

- Q: Who may use each page? → A: Whoever may change the record uses the five editing pages, and
  whoever may delete it uses the delete page. Both are the rights the portal already checks today.
  This feature grants nothing new and takes nothing away. How those rights are given to a research
  team is #402's subject.
- Q: A project's and a dataset's key dates and identifiers are edited today on the same page as
  their other details. Do they stay there? → A: No. Each is edited on its own page, on all four
  record types, and the details page no longer carries them.
- Q: Descriptions are edited two ways today: one area per description type on a project and a
  dataset, and rows that are added and removed on a sample. Which does the shared page use? → A: One
  area per description type the record's vocabulary offers.
- Q: Keyword editing is to be rebuilt in #298. What does this feature ship? → A: The keywords page
  as it works today, registered on all four record types. #298 replaces what is inside it and
  inherits the registration, the Manage menu entry and the access rule from this feature.
- Q: What does the details page edit on a sample or a measurement? → A: The fields its registered
  type offers for editing, which are the same ones offered when a record of that type is created. It
  does not offer moving a sample to another dataset or a measurement to another sample or dataset.
- Q: What stops a record being deleted? → A: What stops it today. A project with a public dataset is
  refused. A sample with measurements made on it is refused. Nothing else is added.
- Q: Do the addresses of the existing editing pages keep working? → A: Each record's own address
  does not move. The editing pages take one address pattern across all four record types, and the
  old addresses of the pages being replaced are not kept.
- Q: Can an addon add its own entry to the Manage menu? → A: Not through this feature. It covers the
  six entries above and leaves alone whatever else the menu carries.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A record's team edits its details and descriptions from the Manage menu (Priority: P1)

A researcher on a dataset's team opens one of its measurements and sees that the value was entered
wrongly and that nothing is written about how it was made. They open the Manage menu in the page
header, choose to edit the details, correct the value, and save. They return through the same menu
to the descriptions page, where each description type the measurement's vocabulary offers has its
own area, and write up the conditions. The same two entries, leading to the same two pages, are in
the Manage menu of the sample the measurement was made on, of the dataset, and of its project.

**Why this priority**: A measurement cannot be corrected through the portal at all today, and the
details and descriptions pages are the two a team uses most. Delivered alone, this story already
gives all four record types one place to reach editing and one behaviour once there.

**Independent Test**: Load development data. Sign in as someone on a dataset's team. On the
dataset's project, the dataset, one of its samples and one of its measurements, open the Manage
menu, edit the details and the descriptions, and save each. Then sign in as someone with no rights
over the dataset and request the same pages.

**Acceptance Scenarios**:

1. **Given** someone who may change a project, a dataset, a sample or a measurement, **When** they
   open that record's page, **Then** its Manage menu offers an entry for editing its details and an
   entry for editing its descriptions, and each leads to a working page.
2. **Given** any of the four record types, **When** its page is shown, **Then** none of the editing
   pages appears as a tab beside the overview.
3. **Given** someone editing a record's details, **When** they change a field and save, **Then**
   they are returned to the record's own page, told the change was saved, and the page shows the new
   value.
4. **Given** someone editing a record's details, **When** they submit a value the field does not
   accept or leave out a required one, **Then** nothing is saved, the field says what is wrong, and
   everything else they entered is still in the form.
5. **Given** a sample or a measurement of a registered type, **When** its details page is shown,
   **Then** it offers the fields that type offers when a record of it is created, with their current
   values, and no field for moving the record to another dataset or sample.
6. **Given** a portal developer who registers a new sample or measurement type, **When** a record
   of that type is opened by someone who may change it, **Then** the Manage menu and the editing
   pages are there with no further work by the developer.
7. **Given** someone editing a record's descriptions, **When** the page is shown, **Then** it
   carries one area for each description type that record's vocabulary offers, filled with what is
   already recorded.
8. **Given** someone editing a record's descriptions, **When** they fill in an area and save,
   **Then** the record's page shows that description. **When** they empty an area and save,
   **Then** the record no longer carries a description of that type.
9. **Given** a signed-in person who may see a record and may not change it, **When** they open its
   page, **Then** no entry for editing is offered. **When** they request an editing page directly,
   **Then** they are refused and nothing is changed.
10. **Given** a visitor who is not signed in, **When** they request an editing page of a record
    they are able to see, **Then** they are sent to sign in, and after signing in the rules above
    decide whether they may continue.
11. **Given** a record the viewer may not see, **When** they request any of its editing pages,
    **Then** the portal answers as it does for a record that does not exist.
12. **Given** a prompt on a record's page that leads its team to an editing page, such as the one
    shown when no description has been written, **When** it is followed, **Then** it arrives at the
    shared page for that record.

---

### User Story 2 - Key dates and identifiers each have a page of their own (Priority: P2)

A researcher has a sample that was collected in 2019, prepared a year later and has since been
given an IGSN. From the sample's Manage menu they open the key dates page, record the two dates
against the date types the sample vocabulary offers, and save. They go back to the menu, open the
identifiers page and add the IGSN. The project the sample sits under has the same two entries, and
its start and end dates and its grant identifier are edited the same way.

**Why this priority**: Dates and identifiers are what a citation and a repository record are built
from. They can be edited on a project and a dataset today, on a sample only in part, and on a
measurement not at all.

**Independent Test**: Sign in as someone on a dataset's team. On a project, a dataset, a sample and
a measurement, open the key dates page and the identifiers page from the Manage menu, add an entry
on each, change one, remove one, and save. Check the record's own page after each.

**Acceptance Scenarios**:

1. **Given** someone who may change a record of any of the four types, **When** they open its
   Manage menu, **Then** it offers an entry for key dates and an entry for identifiers, each leading
   to a working page.
2. **Given** someone on the key dates page, **When** it is shown, **Then** it offers the date types
   that record's vocabulary defines and shows the dates already recorded.
3. **Given** someone on the key dates page, **When** they add a date, change one or remove one and
   save, **Then** the record's own page shows the dates as they now stand.
4. **Given** a record type whose vocabulary has a start and an end, **When** someone saves an end
   that falls before the start, **Then** nothing is saved and the page says which date is wrong.
5. **Given** a date known only to the year or the month, **When** it is saved, **Then** it is kept
   and shown as precisely as it was entered and no more.
6. **Given** someone on the identifiers page, **When** it is shown, **Then** it offers the
   identifier types that record's vocabulary defines and shows the identifiers already recorded.
7. **Given** someone on the identifiers page, **When** they add an identifier, change one or remove
   one and save, **Then** the record's own page shows the identifiers as they now stand.
8. **Given** someone on the identifiers page, **When** it is shown, **Then** the identifier the
   portal itself gave the record is not offered for editing.
9. **Given** someone editing a project's or a dataset's details, **When** the page is shown,
   **Then** it carries no key dates and no identifiers, which are edited on their own pages.
10. **Given** someone who may not change the record, **When** they request its key dates page or its
    identifiers page, **Then** access is decided exactly as in User Story 1.

---

### User Story 3 - A record's team deletes it from the Manage menu (Priority: P2)

A researcher entered a measurement against the wrong sample and wants it gone. From the
measurement's Manage menu they choose to delete it. The page says what will be removed with it and
asks them to confirm. They confirm and land on the dataset the measurement belonged to. Later they
try to delete a sample that still has measurements made on it. The page says the sample cannot be
deleted and names what is in the way.

**Why this priority**: A project and a dataset can be deleted through the portal today. A sample
and a measurement cannot, so a record entered by mistake stays until someone with access to the
administration interface removes it.

**Independent Test**: Sign in as someone who may delete records in a dataset. Delete a measurement,
then a sample with no measurements, then try a sample that has measurements and a project that has
a public dataset. Sign in as someone who may change the dataset's records and may not delete them,
and look for the entry.

**Acceptance Scenarios**:

1. **Given** someone who may delete a record of any of the four types, **When** they open its
   Manage menu, **Then** it offers an entry for deleting the record.
2. **Given** someone who may change a record and may not delete it, **When** they open its Manage
   menu, **Then** the editing entries are offered and the delete entry is not. **When** they request
   the delete page directly, **Then** they are refused and nothing is deleted.
3. **Given** someone on a record's delete page, **When** it is shown, **Then** it says what else
   will be removed with the record and nothing is deleted until they confirm.
4. **Given** someone on a record's delete page, **When** they leave without confirming, **Then**
   the record is unchanged.
5. **Given** someone who confirms deleting a measurement or a sample, **When** the deletion
   completes, **Then** they land on the dataset it belonged to and are told the record was deleted.
6. **Given** someone who confirms deleting a dataset or a project, **When** the deletion completes,
   **Then** they land on a page that still exists and are told the record was deleted.
7. **Given** a sample with measurements made on it, **When** someone requests its delete page,
   **Then** the page says the sample cannot be deleted, names what prevents it, and offers no way to
   confirm.
8. **Given** a project with a public dataset, **When** someone requests its delete page, **Then**
   the page says the project cannot be deleted, names the datasets that prevent it, and offers no
   way to confirm.
9. **Given** a record that became protected after its delete page was opened, **When** the
   deletion is confirmed, **Then** nothing is deleted and the page says why.

---

### User Story 4 - Keywords are edited the same way on every record type (Priority: P3)

A researcher wants a project to be found under the same keywords as its datasets. From the
project's Manage menu they open the keywords page, choose the keywords and save. The page they used
is the one a dataset, a sample and a measurement offer.

**Why this priority**: Keywords matter for discovery, but only a sample has a page for them today
and that page's interior is due to be rebuilt in #298. This story puts the page in the same place on
every record type so the rebuild has one page to replace. It comes last because the page itself is
not improved here.

**Independent Test**: Sign in as someone on a dataset's team. On a project, a dataset, a sample and
a measurement, open the keywords page from the Manage menu, add a keyword, remove one, and save.
Check the record's own page after each.

**Acceptance Scenarios**:

1. **Given** someone who may change a record of any of the four types, **When** they open its
   Manage menu, **Then** it offers an entry for keywords leading to a working page.
2. **Given** someone on the keywords page, **When** it is shown, **Then** the keywords the record
   already carries are shown as chosen.
3. **Given** someone on the keywords page, **When** they add keywords, remove keywords and save,
   **Then** the record's own page shows the keywords as they now stand.
4. **Given** a portal that configures no keyword vocabulary for a record type, **When** the
   keywords page of a record of that type is shown, **Then** the page still works and says nothing
   that suggests a fault.
5. **Given** someone who may not change the record, **When** they request its keywords page,
   **Then** access is decided exactly as in User Story 1.

---

### Edge Cases

- A person loses the right to change a record while an editing page is open. The save is refused
  and nothing is changed, because the right is checked again on saving.
- A record is deleted by someone else while its editing page is open. The save answers as for a
  record that does not exist.
- A record is made private while someone without rights over it has its page open. Their next
  request for an editing page answers as for a record that does not exist.
- A person may use none of the six pages and nothing else the Manage menu carries. The menu is not
  shown at all, so it never opens empty.
- A person holds a portal role that lets them change every record of a kind without being on any
  team. They are offered the pages on every record of that kind they may see, as 017 rules.
- A measurement belongs to a different dataset than the sample it was made on. Rights over the
  measurement come from the measurement's own dataset, as they do today.
- A measurement has no name. Its editing pages and its delete page name it by its portal ID, as its
  overview does.
- A record's vocabulary offers no description types, no date types or no identifier types. The page
  for that kind of information says there is nothing to record and offers nothing to save.
- A record type offers no fields for editing beyond those the base record has. Its details page
  carries the base fields alone.
- Two people save the same page one after the other. The later save stands. Nothing here detects or
  merges the two.
- A dataset is public. Its samples and measurements may still be edited and deleted by those with
  the right to, as they may be today.

## Requirements *(mandatory)*

### Functional Requirements

**One set, on four record types**

- **FR-001**: The portal MUST provide six pages for a record: edit details, descriptions, keywords,
  key dates, identifiers and delete.
- **FR-002**: Each of the six MUST be available on projects, datasets, samples and measurements,
  including every sample type and measurement type a portal registers, with no work by the portal
  developer beyond registering the type.
- **FR-003**: Each of the six MUST be defined once and shared by all four record types, so that a
  change to how one page behaves reaches every record type that has it. The separate copies that
  projects, datasets and samples carry today MUST be removed.
- **FR-004**: Each page MUST behave the same on every record type, differing only in what the
  record itself supplies: its fields, its vocabularies and what protects it from deletion.
- **FR-005**: Each record's own address MUST stay where it is. The six pages MUST follow one
  address pattern across all four record types.

**Reached from the Manage menu**

- **FR-006**: The page of a project, a dataset, a sample and a measurement MUST carry a Manage menu
  with an entry for each of the six pages the viewer may use, in the same order on every record
  type.
- **FR-007**: The six pages MUST NOT appear as tabs beside the overview or as entries among the
  actions open to any visitor.
- **FR-008**: An entry MUST be shown only to someone who may use the page it leads to. Where a
  viewer may use nothing the Manage menu carries, the menu MUST NOT be shown.
- **FR-009**: Whatever else the Manage menu carries on a record, such as importing data on a
  dataset, MUST remain in the menu and keep working.
- **FR-010**: Every prompt and checklist item on a record's page that leads its team to an editing
  page MUST lead to the shared page for that record.

**Who may use them**

- **FR-011**: The five editing pages MUST be open to whoever may change the record, and to nobody
  else. The delete page MUST be open to whoever may delete the record, and to nobody else.
- **FR-012**: This feature MUST NOT change who may change or delete any record.
- **FR-013**: A signed-in person who may see a record and may not use a page MUST be refused when
  they request it directly, and nothing MUST be changed. A visitor who is not signed in MUST be sent
  to sign in.
- **FR-014**: A request for any of the six pages of a record the viewer may not see MUST be answered
  as a request for a record that does not exist.
- **FR-015**: The right to use a page MUST be checked again when it is saved or confirmed, not only
  when it is shown.

**Edit details**

- **FR-016**: The details page MUST edit the record's own fields. For a project and a dataset these
  are the fields their details pages edit today, without key dates and identifiers. For a sample and
  a measurement they are the fields its registered type offers when a record of that type is
  created.
- **FR-017**: The details page of a sample MUST NOT offer moving it to another dataset. The details
  page of a measurement MUST NOT offer moving it to another sample or another dataset.
- **FR-018**: A save that a field refuses MUST save nothing, say at the field what is wrong, and
  keep everything else that was entered.
- **FR-019**: A successful save on any of the five editing pages MUST return the person to the
  record's own page, tell them it was saved, and show the change there.

**Descriptions**

- **FR-020**: The descriptions page MUST carry one area for each description type the record's
  vocabulary offers, filled with what is recorded.
- **FR-021**: Saving an area with text MUST record or replace that description. Saving an empty
  area MUST remove it.

**Keywords**

- **FR-022**: The keywords page MUST let the record's keywords be added to and removed from, and
  MUST show the keywords the record already carries.
- **FR-023**: The keywords page MUST work on a record type for which the portal configures no
  keyword vocabulary.
- **FR-024**: Keyword editing MUST keep the behaviour it has today on the record type that has it.
  Rebuilding it against the controlled vocabularies is #298.

**Key dates**

- **FR-025**: The key dates page MUST let a date be added, changed and removed for each date type
  the record's vocabulary offers.
- **FR-026**: Where a record type's dates include a start and an end, an end before the start MUST
  be refused, with the page saying which date is wrong.
- **FR-027**: A date MUST be kept and shown as precisely as it was entered.

**Identifiers**

- **FR-028**: The identifiers page MUST let an identifier be added, changed and removed, for each
  identifier type the record's vocabulary offers.
- **FR-029**: The identifier the portal gives a record MUST NOT be editable.

**Delete**

- **FR-030**: The delete page MUST say what else is removed with the record and MUST delete nothing
  until the person confirms.
- **FR-031**: Whatever protects a record from deletion today MUST still protect it: a project with a
  public dataset and a sample with measurements made on it MUST be refused. The page MUST say the
  record cannot be deleted, name what prevents it, and offer no way to confirm.
- **FR-032**: A protection that takes effect between the page being shown and the deletion being
  confirmed MUST stop the deletion.
- **FR-033**: After a sample or a measurement is deleted, the person MUST land on the dataset it
  belonged to. After a project or a dataset is deleted, they MUST land on a page that still exists.
  In each case they MUST be told the record was deleted.

**Documentation**

- **FR-034**: The developer documentation MUST say which pages a registered sample or measurement
  type receives, how they are reached, and which right opens each.

### Key Entities

- **Record**: a project, a dataset, a sample or a measurement. Samples and measurements include
  every type a portal registers.
- **Editing page**: one of the six pages. It is a plugin registered against all four record types
  and is not listed beside the overview.
- **Manage menu**: the menu in a record's page header, shown only to people with rights over the
  record. It is distinct from the tabs beside the overview, from the actions open to any visitor,
  and from the cards on the overview.
- **Description, date, identifier**: the typed entries a record carries, each drawn from that
  record type's own vocabulary.
- **Keyword**: a term attached to a record for discovery.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On each of the four record types, someone with full rights over a record reaches all
  six pages from its Manage menu: 24 of 24 combinations.
- **SC-002**: A measurement's details, descriptions, keywords, key dates and identifiers can all be
  changed, and the measurement deleted, without opening the administration interface.
- **SC-003**: No editing page is listed beside the overview on any of the four record types.
- **SC-004**: For every one of the 24 combinations, someone who may not use the page is offered no
  entry for it and is refused when they request it directly, and a record they may not see answers
  as one that does not exist.
- **SC-005**: Each of the six pages has one definition in the codebase. The repository holds no
  second copy of any of them for a particular record type.
- **SC-006**: A sample type and a measurement type registered in the demo portal have all six pages
  with nothing written for them beyond the registration.
- **SC-007**: Nobody gains or loses the ability to change or delete any record as a result of this
  feature.

## Assumptions

- The Manage menu specified in 018 for the sample page, and already present on project and dataset
  pages, is the menu meant by the request. A measurement's page gains one.
- The rights checked are those the portal defines today. On a sample and a measurement they are
  inherited from the record's dataset. #402 may change how rights are granted, and these pages
  follow whatever it settles without being specified again.
- Entries the Manage menu carries beyond these six, such as importing data or reviewing and
  publishing a dataset, belong to other features.
- People and organizations are not covered. Their editing pages are specified in 020.
- An addon cannot remove or replace one of these pages on a record type. #401, which would have
  specified that, was closed without being built. Nothing here depends on it.
- The portal has not had a stable release, so the addresses of the pages being replaced are not
  preserved.
