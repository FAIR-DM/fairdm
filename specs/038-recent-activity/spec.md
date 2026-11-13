# Feature Specification: Show recent activity on project and dataset pages

**Feature Branch**: `038-recent-activity`

**Created**: 2026-11-13

**Status**: Draft

**Goals**: G5: a modern, extensible interface that every portal gets by default, with no frontend
work. G12: private and public data sit side by side, controlled per object.

**Roadmap**: none. The capability is listed as not yet available by specification 018 (FR-016),
and the redesigned overview pages built it as part of their prototype.

**Input**: https://github.com/FAIR-DM/fairdm/issues/675. A reader of a project or dataset page
cannot tell what has happened to it lately. Show its recent activity, grouped by day: samples and
measurements added to each dataset, datasets created, and the other events worth showing, such as
publishing, edits and people joining. Activity about a record the viewer may not open is never
shown to them.

## What exists, and what this specification changes

The project and dataset overview pages are specified by specification 018. They have no record of
what has happened to a project or dataset. Specification 018 lists recent activity among the
capabilities shown as not yet available (FR-016 and FR-017), and on `main` the project page carries
a "Recent activity" card that says so. The dataset page has none.

The redesigned overview pages (https://github.com/FAIR-DM/fairdm/issues/668) replace that card
with a working Recent activity panel on both pages. The prototype works the activity out from when
records were added, so it can only show additions.

After this feature:

- A project's page and a dataset's page each show what has happened to the record and to the
  records in it lately, newest first, grouped by the day it happened.
- What is shown covers additions (a project or dataset created, samples and measurements added to
  a dataset), a dataset being published, edits to a project's or dataset's details, and
  contributors being added to a project or dataset.
- A viewer only ever sees activity about records they may open, and that follows the records'
  visibility as it is when the page is viewed, not as it was when the activity happened.
- A portal that already holds records shows their additions from the day they were added.

**Specifications this changes.** Specification 018 lists recent activity as not yet available on
the overview pages (FR-016, with its treatment in FR-017). For project and dataset pages that is
replaced by this specification: recent activity is a working panel there, and FR-016 no longer
lists it for those pages. Specification 018 is edited to read that way in the pull request that
delivers this feature. The placeholder itself is removed by the redesign of the pages
(https://github.com/FAIR-DM/fairdm/issues/672), which this feature builds on.

## Boundary

- **The redesigned pages themselves** (header, panels, fact sheet, edit controls) belong to
  https://github.com/FAIR-DM/fairdm/issues/672. This feature adds one panel to the page that work
  delivers.
- **Sample and measurement pages**: they get no recent activity panel. A sample's history is its
  own timeline, carried into the sample page by https://github.com/FAIR-DM/fairdm/issues/672.
- **Person and organization pages**: they keep their "not yet available" card. Activity on a
  contributor's page is not part of this feature.
- **What changed in an edit**: an entry says that a record's details were edited, not which fields
  or what they were before. A record's revision history is
  https://github.com/FAIR-DM/fairdm/issues/170.
- **A page of all activity**: the panel shows the newest entries only. There is no page that lists
  a record's whole history, no site-wide activity page and no activity on the home page.
- **Following a record**, and notifications about activity: not part of this feature.
- **The citation downloads and the sample map** on the same pages are
  https://github.com/FAIR-DM/fairdm/issues/673 and https://github.com/FAIR-DM/fairdm/issues/674.

## Clarifications

### Session 2026-11-13

Each question was answered from the request, the prototype the maintainer has seen and liked, and
the decisions recorded on https://github.com/FAIR-DM/fairdm/issues/668, without putting it to him
again. The longer reasoning is in [decisions.md](decisions.md).

- Q: Which events are shown? → A: A project created, a dataset created, samples added to a dataset,
  measurements added to a dataset, a dataset published, a project's or dataset's details edited,
  and a contributor added to a project or dataset. Edits to samples and measurements, contributors
  added to samples and measurements, and deletions are not shown.
- Q: Does each sample added make its own entry? → A: No. As in the prototype, the samples added to
  one dataset on one day are one entry that says how many, and so are the measurements. Edits to
  one record on one day are one entry too.
- Q: What does the project page show? → A: The project's own activity and the activity of every
  dataset in it the viewer may open, including the samples and measurements added to those
  datasets. The dataset page shows the dataset's own activity, including its samples and
  measurements.
- Q: How is activity about a record the viewer may not open kept from them? → A: An entry is shown
  only to a viewer who may open the record it is about, decided when the page is viewed. A dataset
  made public later shows its earlier activity to everyone from then on. A dataset made private
  stops showing its activity to those who may no longer open it.
- Q: Where does a measurement count, when its sample is in another dataset? → A: In the dataset
  the measurement belongs to.
- Q: Does an entry say who did it? → A: A contributor being added names the contributor. Other
  entries name the record and what happened to it, as the prototype does, and not who made the
  change, since one entry can gather several people's additions.
- Q: Which day does an entry fall on? → A: The day in the portal's own time zone.
- Q: What does an existing portal show the day it upgrades? → A: The creation of its projects and
  datasets and the samples and measurements added to them, from when each was added. Publishing,
  edits and contributors added before the upgrade were never recorded and are not shown.
- Q: How many entries does the panel show? → A: The newest few, a fixed number. It has no link to
  a fuller list, since no such list exists.
- Q: What happens to an entry about a record that is later deleted? → A: It is no longer shown. A
  count of samples or measurements added counts only those that still exist, and an entry whose
  count falls to none is not shown.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A reader sees what has happened to a project or dataset lately (Priority: P1)

A reader opens a project's page. In its Recent activity panel they see, newest first and grouped
by day, that a dataset was created in it, that samples and measurements were added to one of its
datasets, that a dataset was published, that the project's details were edited and that a
contributor joined it. Each entry names the record it is about and leads to it. On a dataset's page
they see the same for that dataset alone. A reader who is not on a private dataset's team never
sees anything about that dataset, on either page. A portal's own sample and measurement types count
like any other, with nothing written by the portal.

**Why this priority**: this is the feature.

**Independent Test**: seed a project with datasets of each visibility, add samples and
measurements, publish one dataset, edit the project's and a dataset's details and add a
contributor. Open the project and dataset pages signed out, as a member of the team and as a
signed-in person who is not, and check what each one sees.

**Acceptance Scenarios**:

*What is shown*

1. **Given** a project in which a dataset was just created, **When** a reader opens the project's
   page, **Then** its Recent activity shows that the dataset was created, and the entry leads to the
   dataset's page.
2. **Given** a dataset to which samples were added today, **When** a reader opens the dataset's
   page or its project's page, **Then** one entry for today says how many samples were added to
   that dataset.
3. **Given** samples added to the same dataset on two different days, **When** a reader opens the
   page, **Then** there is one entry for each day, each with that day's count.
4. **Given** samples added to two datasets of a project on the same day, **When** a reader opens
   the project's page, **Then** there is one entry for each dataset under that day.
5. **Given** measurements added to a dataset, **When** a reader opens its page, **Then** an entry
   says how many measurements were added, separate from the samples.
6. **Given** a measurement that belongs to one dataset and was made on a sample in another,
   **When** a reader opens the pages, **Then** the measurement is counted in the dataset it belongs
   to and not in the sample's.
7. **Given** a dataset that was published, **When** a reader opens its page or its project's page,
   **Then** an entry says the dataset was published.
8. **Given** a project or dataset whose details were edited several times in one day, **When** a
   reader opens its page, **Then** one entry for that day says its details were edited.
9. **Given** a contributor added to a project or dataset, **When** a reader opens its page,
   **Then** an entry names the contributor and the record they were added to.
10. **Given** a sample's or measurement's details edited, or a contributor added to a sample,
    **When** a reader opens the project or dataset page, **Then** nothing is shown for it.
11. **Given** samples of a type the portal defines, **When** they are added, **Then** they are
    counted like any other sample, with no code or configuration in the portal.

*How it is laid out*

12. **Given** activity on several days, **When** a reader opens the page, **Then** the entries are
    grouped under the day they happened, the newest day first, and each day lists its entries
    newest first.
13. **Given** activity just before midnight in the portal's time zone, **When** a reader opens the
    page, **Then** the entry falls on that day in the portal's time zone.
14. **Given** more activity than the panel shows, **When** a reader opens the page, **Then** only
    the newest entries are shown, up to the panel's fixed number.
15. **Given** a project or dataset with no activity a reader may see, **When** they open its page,
    **Then** the panel says nothing has happened yet.
16. **Given** a page in a language the portal translates, **When** a reader opens it, **Then** the
    panel's own text, including each entry's description of what happened, is in that language,
    with counts that read correctly for one and for many.

*Who sees what*

17. **Given** a public project with a private dataset, **When** a reader who may not open that
    dataset opens the project's page, **Then** no entry about the dataset, its samples or its
    measurements is shown, and the project's other activity is.
18. **Given** the same project, **When** a member of the private dataset's team opens the project's
    page, **Then** the dataset's activity is shown to them.
19. **Given** a private project, **When** a person who may open it opens its page, **Then** they
    see the activity of its datasets they may open.
20. **Given** a private dataset with activity that is later made public, **When** a signed-out
    reader opens the pages, **Then** its earlier activity is shown.
21. **Given** a public dataset with activity that is later made private, **When** a reader who may
    no longer open it opens its project's page, **Then** none of its activity is shown.
22. **Given** any portal page or feed of activity that exists apart from these two panels, **When**
    a reader opens it, **Then** no activity from these records reaches them through it.

*Records that change*

23. **Given** samples added and then some deleted on the same day, **When** a reader opens the
    page, **Then** the count covers only the samples that still exist, and an entry whose samples
    were all deleted is not shown.
24. **Given** a dataset that was deleted, **When** a reader opens its project's page, **Then** none
    of that dataset's activity is shown.

*A portal that already holds records*

25. **Given** a portal with projects, datasets, samples and measurements from before this feature,
    **When** it upgrades and a reader opens a project's page, **Then** the creation of its datasets
    and the samples and measurements added to them are shown on the days they were added.
26. **Given** the same portal, **When** a reader opens the pages, **Then** no entry is shown for
    publishing, edits or contributors added before the upgrade.

### Edge Cases

- A dataset moved from one project to another: its activity is shown on the project it now belongs
  to, under the rules for who sees what, and no longer on the project it left.
- An import that adds thousands of samples to one dataset in one day: one entry, with the count
  (scenario 2), and recording it stays within SC-003.
- A contributor added and removed again on the same day: the entry stays. It records that they
  joined, not that they are still there.
- A contributor whose own page is not public: the entry names them without a link to their page.
- A project page with many datasets and a long history: the page answers in the same time as one
  with little, because the panel shows a fixed number of entries.

## Requirements *(mandatory)*

### Functional Requirements

**What is recorded**

- **FR-001**: The portal MUST record when a project is created, a dataset is created, a sample is
  added to a dataset, a measurement is added to a dataset, a dataset is published, a project's or
  dataset's details are edited, and a contributor is added to a project or dataset, however each
  happens: through the portal's pages, an import, the API or the administration interface. (US1)
- **FR-002**: Recording MUST cover every sample and measurement type a portal defines, with nothing
  written by the portal. (US1)
- **FR-003**: Recording an event MUST NOT make the change that caused it fail. (US1)

**What is shown**

- **FR-004**: The project and dataset overview pages MUST each have a Recent activity panel, shown
  to everyone who may open the page. (US1)
- **FR-005**: A dataset's panel MUST show its own activity and that of its samples and
  measurements. A project's panel MUST show its own activity and that of each of its datasets, with
  their samples and measurements. A measurement MUST count in the dataset it belongs to. (US1)
- **FR-006**: The samples added to one dataset on one day MUST be one entry stating how many, and
  so MUST the measurements. The edits to one record's details on one day MUST be one entry. (US1)
- **FR-007**: Entries MUST be grouped by the day they happened in the portal's time zone, newest day
  first, and newest first within a day. (US1)
- **FR-008**: Each entry MUST name the record it is about and lead to that record's page. An entry
  for a contributor added MUST name the contributor, leading to their page where the viewer may
  open it. (US1)
- **FR-009**: The panel MUST show at most a fixed number of the newest entries, and MUST say that
  nothing has happened yet when there is nothing to show. (US1)
- **FR-010**: The panel's text MUST be translatable, with counts in the singular and plural forms
  of the language. (US1)

**Who sees what**

- **FR-011**: An entry MUST be shown only to a viewer who may open the record it is about, judged by
  the record's visibility and the viewer's levels at the time the page is viewed. (US1)
- **FR-012**: Activity about these records MUST NOT reach anyone through any other page, feed or
  address that the activity package offers, unless that page applies the rule in FR-011. (US1)
- **FR-013**: An entry about a record that no longer exists MUST NOT be shown, and a count MUST
  cover only the records that still exist. (US1)

**Existing portals**

- **FR-014**: On upgrade, a portal's existing projects, datasets, samples and measurements MUST be
  shown as created or added on the day they were added. (US1)

**Documentation**

- **FR-015**: The documentation MUST describe the Recent activity panel: which events it shows, how
  entries are gathered by day, who sees what, and what an upgraded portal shows of its past. (US1)

### Key Entities

None of FairDM's own. The activity package's own record of each event is used.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a seeded project, every event kind in FR-001 appears in its panel within one page
  load of the change that caused it.
- **SC-002**: Across every combination of record visibility and viewer (signed out, signed in
  without a level, on the team), no viewer sees an entry about a record they cannot open, on either
  page.
- **SC-003**: Adding 10,000 samples to a dataset in one import produces one entry for that day, and
  the import takes no more than 10% longer than without recording.
- **SC-004**: The project page of a project with 50 datasets and a year of activity answers within
  the same budget as a project with one dataset and none.
- **SC-005**: An upgraded portal's project and dataset pages show their past additions with no step
  run by the portal beyond its usual migration.

## Assumptions

- The redesigned project and dataset pages from https://github.com/FAIR-DM/fairdm/issues/672 are on
  `main` before this feature is built. Its panel sits in those pages.
- The activity package used is the `activity` extra of django-mvp-community, built on
  django-activity-stream, at a version that supports the Django and Python versions FairDM
  supports.
- Who may open a record is decided as it is today, by its visibility and the viewer's levels
  (specification 018, FR-018 to FR-020).
