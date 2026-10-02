# Feature Specification: Statistics pages for projects, datasets, people and organizations

**Feature Branch**: `026-statistics-pages`

**Created**: 2026-10-02

**Status**: Draft

**Goals**: G5: a modern, extensible interface that every portal gets by default, with no frontend
work.

**Roadmap**: none. No roadmap item covers statistics. The request is part of the plan for what
record pages offer, tracked in issue #397.

**Input**: A reader has no way to see a record in numbers beyond the handful of counts and the two
charts on its overview. Contributor pages had a Statistics tab that rendered blank, and
specification 019 removed it until it had content. Projects, datasets, people and organizations
should each have a Statistics tab. These are four separate pages, because each record needs
different figures. A dataset's page summarises the fields of its samples and measurements: how many
values, their range, their mean, the share missing and how they are distributed. A project's page
shows the same rolled up across its datasets, and how the project has grown. A person's page shows
what they have contributed over time and in which contribution roles, and who they have worked
with. An organization's page shows the output of its members over time, and which organizations it
works with. Figures are taken only over records the viewer may see. Plotting one field against
another is left to an addon, and so are views, downloads and citations.

## Clarifications

### Session 2026-10-02

- Q: Which fields of a sample or measurement type does a dataset's page summarise? → A: The fields
  the type's registration lists, the same ones its table shows. A portal developer can name a
  different set for statistics where that default is wrong. Fields are grouped by type, because two
  types rarely share a field that means the same thing.
- Q: A field holding a number can have a mean. What about the others? → A: The summary depends on
  the kind of field. Every field gets the number of values and the share missing. A number also
  gets its smallest and largest value, its mean, its median and a distribution. A date gets its
  earliest and latest value and a distribution over time. A field with a fixed set of choices, a
  controlled vocabulary term or a yes/no value gets a count for each value. Free text and
  identifiers get the count and the share missing and nothing else.
- Q: A public dataset that is not yet published shows its sample and measurement counts on the
  overview, and none of its records. What does a visitor see on its Statistics page? → A: No field
  summaries. The request says figures are taken only over records the viewer may see, and a range
  or a mean discloses values in a way a bare count does not. The page says there is nothing to
  summarise yet.
- Q: Which records does a person's or an organization's Statistics page count? → A: The ones
  specification 019 allows on a contributor's page. Projects and datasets are counted only when
  they are public, for every viewer, the contributor included. Contribution roles and collaborators
  are worked out from credits on records the viewer may open.
- Q: The overview page of an organization counts only its own work and does not roll up its
  members' credits. Does the Statistics page? → A: It does both and keeps them apart. The request
  asks for the output of its members, so the page reports the public projects and datasets its
  current members are credited on, beside the organization's own.
- Q: What makes two organizations work together? → A: A shared record. Another organization counts
  when it is credited on a record this page counts, or when it is the affiliation recorded on a
  person's credit on such a record.
- Q: Where in time does a contribution sit? → A: At the date its record was added to the portal.
  A contribution has no date of its own.
- Q: Is the tab shown when there is nothing to count? → A: Yes. The tab is present on every
  project, dataset, person and organization the viewer can open, and a page with nothing to count
  says so.
- Q: Do the samples and measurements pages get a Statistics tab? → A: No. The request names four
  record types, and a single sample or measurement has nothing to aggregate.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A dataset's page summarises its samples and measurements field by field (Priority: P1)

A researcher deciding whether a dataset is worth downloading opens its Statistics tab. The page is
arranged by sample type and then by measurement type. Under each type they read how many records
of that type the dataset holds, and then one summary for each of the type's fields: how many
records have a value, what share have none, and, depending on the kind of field, its range, mean
and median, or the count for each value. A field of numbers, dates or categories also shows how its
values are distributed. A person on the dataset's team sees the same page over the dataset's
working records before it is published.

This is the first Statistics page, so this story also delivers what all four share: where the tab
sits, who may open it, how an empty page reads, and how figures are presented in the reader's
language.

**Why this priority**: The dataset is the unit of distribution, and its field summaries are the
figures a reader cannot get anywhere else in the portal. The project page is a roll-up of this one.

**Independent Test**: Load development data. Open the Statistics tab of a published dataset, an
unpublished public dataset, an empty dataset and a private dataset, as a visitor and as a member
of the dataset's team. Check each summary against the dataset's records by hand.

**Acceptance Scenarios**:

1. **Given** a published dataset with samples of two types, **When** a visitor opens its Statistics
   tab, **Then** each sample type is summarised separately with the number of its records, and
   measurement types follow in the same way.
2. **Given** a type with a numeric field recorded on some of its records, **When** the page is
   opened, **Then** the field's summary gives the number of records with a value, the share with
   none, the smallest and largest value, the mean, the median and a distribution of the values.
3. **Given** a numeric field recorded with a unit, **When** the page is opened, **Then** its
   figures are given in that unit.
4. **Given** a field with a fixed set of choices or a controlled vocabulary, **When** the page is
   opened, **Then** the summary counts the records holding each value, the most frequent first.
5. **Given** a date field, **When** the page is opened, **Then** the summary gives the earliest and
   latest date and how the values are spread over time.
6. **Given** a free-text field, **When** the page is opened, **Then** the summary gives the number
   of records with a value and the share with none, and no distribution.
7. **Given** a field that no record of the type has a value for, **When** the page is opened,
   **Then** the field is still listed, as entirely missing, with no range, mean or distribution.
8. **Given** a public dataset that is not published, **When** a visitor opens its Statistics tab,
   **Then** no field summary is shown and the page says there is nothing to summarise yet.
   **When** a member of its team opens it, **Then** the summaries cover the dataset's records.
9. **Given** a private dataset, **When** someone who may not open it requests its Statistics tab,
   **Then** the request is refused in the same way its overview is.
10. **Given** a dataset with no samples and no measurements, **When** anyone who may open it opens
    the tab, **Then** the page says the dataset holds nothing to summarise and shows no empty
    chart.
11. **Given** a measurement in this dataset made on a sample that belongs to another dataset,
    **When** the page is opened, **Then** the measurement is counted here and the sample is not.
12. **Given** a reader using another language and locale, **When** the page is opened, **Then**
    numbers and dates follow that locale and field names appear as the portal translates them.
13. **Given** any distribution on the page, **When** it is read without the chart, **Then** the
    same figures are available as text.

---

### User Story 2 - A project's page rolls its datasets up and shows how it has grown (Priority: P2)

A funder or a new collaborator opens a project's Statistics tab to see what the project has
produced as a whole. The field summaries from the dataset page appear again, this time over the
samples and measurements of every dataset in the project the viewer may see. The page also shows
how much each dataset contributes, and how the project's datasets, samples, measurements and
contributors have accumulated over time.

**Why this priority**: A project's page is the dataset page applied across several datasets, plus
growth. It depends on the first story's summaries and adds the view that funders and coordinators
ask for.

**Independent Test**: Load development data. Open the Statistics tab of a project holding a
published dataset, an unpublished public dataset and a private dataset, as a visitor and as a
member of the project. Confirm that each viewer's figures equal the sum of what the same viewer
sees on the Statistics tabs of the project's datasets.

**Acceptance Scenarios**:

1. **Given** a project with two published datasets holding samples of the same type, **When** a
   visitor opens its Statistics tab, **Then** each field of that type is summarised once, over the
   samples of both datasets.
2. **Given** a project with a published dataset and a private one, **When** a visitor opens the
   tab, **Then** every figure covers the published dataset only, and nothing on the page reveals
   that the private dataset exists.
3. **Given** the same project, **When** a person with rights over the private dataset opens the
   tab, **Then** the figures cover both datasets.
4. **Given** a project with several datasets, **When** the page is opened, **Then** it shows how
   many samples and measurements each dataset the viewer may see contributes, and each dataset
   links to its own page.
5. **Given** a project whose records were added over more than one month, **When** the page is
   opened, **Then** it shows the running totals of datasets, samples, measurements and contributors
   over time.
6. **Given** a project with no datasets the viewer may see, **When** the page is opened, **Then**
   it says there is nothing to summarise and shows no empty chart.
7. **Given** a private project, **When** someone who may not open it requests its Statistics tab,
   **Then** the request is refused in the same way its overview is.

---

### User Story 3 - A person's page shows what they have contributed and with whom (Priority: P3)

A visitor who knows a person from one dataset wants to see the shape of their work in the portal.
The person's Statistics tab shows how many projects and datasets they have been credited on in each
year, which contribution roles they have held and how often, and how their credits divide between
projects, datasets, samples and measurements. It also lists everyone they have worked with, people
and organizations alike, with the number of records shared with each. The overview shows only the
most frequent collaborators; this page lists them all.

**Why this priority**: Contributor pages already carry role counts and frequent collaborators on
the overview, so the need is less pressing than on record pages, where nothing of the kind exists.

**Independent Test**: Load development data. Open the Statistics tab of a person credited on public
and private records, of a person credited on nothing, and of an unclaimed profile, as a visitor and
signed in as a member of one of the private records.

**Acceptance Scenarios**:

1. **Given** a person credited on public projects and datasets added in different years, **When**
   anyone opens their Statistics tab, **Then** the page shows the number of projects and datasets
   they were credited on in each year.
2. **Given** a person credited on a private project, **When** anyone opens the tab, the person
   included, **Then** that project is not counted in any year.
3. **Given** a person holding several contribution roles, **When** the page is opened, **Then**
   each role is listed with the number of records it is held on, the most frequent first, and the
   counts agree with the roles shown on the person's overview for the same viewer.
4. **Given** a person credited on projects, datasets, samples and measurements, **When** the page
   is opened, **Then** it shows how many of each the person is credited on, counting only records
   the viewer may open.
5. **Given** a person with more collaborators than the overview shows, **When** the page is opened,
   **Then** every collaborator is listed with the number of records shared, the most frequent first
   and ties by name, and each links to that contributor's page.
6. **Given** a person who shares a credit with someone only on a private record, **When** a visitor
   opens the page, **Then** that someone is not listed.
7. **Given** a person credited on nothing, **When** the page is opened, **Then** it says there is
   nothing to show yet and shows no empty chart.
8. **Given** any person, **When** their Statistics tab is opened, **Then** the page contains no
   email address.

---

### User Story 4 - An organization's page shows what its members produce and who it works with (Priority: P4)

Someone assessing an institution opens its Statistics tab. The page shows, year by year, the public
projects and datasets its current members have been credited on, kept apart from the projects and
datasets that are the organization's own. It shows how many members were active in each year, and
it lists the other organizations this one works with, with the number of records shared with each.

**Why this priority**: It relies on the same contribution figures as the person page and adds the
roll-up over members, which fewer readers need.

**Independent Test**: Load development data. Open the Statistics tab of an organization with
current members, a former member and a pending request, and of an organization with no members and
no credits.

**Acceptance Scenarios**:

1. **Given** an organization whose current members are credited on public datasets, **When**
   anyone opens its Statistics tab, **Then** the page shows the number of projects and datasets its
   members were credited on in each year.
2. **Given** a dataset on which two members of the organization are both credited, **When** the
   page is opened, **Then** the dataset is counted once.
3. **Given** a former member and a person with a pending request, **When** the page is opened,
   **Then** the records only they are credited on are not counted.
4. **Given** a member credited on a private dataset, **When** anyone opens the page, **Then** that
   dataset is not counted.
5. **Given** an organization that owns projects and is credited on datasets itself, **When** the
   page is opened, **Then** its own records are reported separately from its members' output, and
   their number equals the figures on its overview.
6. **Given** records the page counts on which other organizations are credited, or named as the
   affiliation on a person's credit, **When** the page is opened, **Then** those organizations are
   listed with the number of records shared, the most frequent first and ties by name, each linking
   to its page, and the organization itself is not in the list.
7. **Given** an organization with no members and no credits, **When** the page is opened, **Then**
   it says there is nothing to show yet and shows no empty chart.

---

### User Story 5 - A portal developer decides which fields are summarised (Priority: P5)

A portal developer registers a sample type with thirty fields and finds that three of them are
internal bookkeeping that should not be summarised. They name the fields that belong on the
Statistics pages for that type, in the same place they configure the type's table and form. A
developer who changes nothing gets a working page.

**Why this priority**: The default covers most types. The override matters only where the default
is wrong, and the pages are useful without it.

**Independent Test**: In the demo portal, register one type with no statistics configuration and
one that names a subset of its fields. Open a dataset holding both and compare the fields listed.

**Acceptance Scenarios**:

1. **Given** a registered type that says nothing about statistics, **When** a dataset holding it is
   opened, **Then** the page summarises the fields the type's registration lists.
2. **Given** a registered type that names its statistics fields, **When** a dataset or project
   holding it is opened, **Then** the page summarises those fields, in the order given, and no
   others.
3. **Given** a registered type that names a field which does not exist on the model, **When** the
   portal starts, **Then** it reports the mistake and names the type and the field.
4. **Given** a registered type that names no statistics fields at all, **When** a dataset holding
   it is opened, **Then** the type is listed with its record count and no field summaries.

---

### Edge Cases

- A numeric field may hold one value, or the same value on every record. The summary gives that
  value as both ends of the range and shows no misleading spread.
- A categorical field may have more distinct values than fit on a page. The summary shows the most
  frequent, counts the rest together, and says how many distinct values there are.
- A dataset may hold a type that the portal no longer registers. Its records are counted under the
  type and no field summaries are attempted.
- A type may be registered in the portal and absent from the dataset, or present only in records
  the viewer may not see. It is not listed.
- A field may hold values far apart in scale. The range and mean are still reported as recorded,
  and the page makes no attempt to remove outliers.
- A project may hold a single dataset. Its page still opens, and its roll-up equals that dataset's
  figures.
- Every record of a project may have been added in the same month. The growth view has nothing to
  plot and is replaced by the totals alone.
- A collaborator may be an organization as well as a person. The list handles both.
- A person may be a current member of two organizations. Their records count toward both.
- The charting library may fail to load in the browser. Every figure is still readable as text.
- A project, dataset, person or organization that does not exist answers "not found".

## Requirements *(mandatory)*

### Functional Requirements

**What all four pages share**

- **FR-001**: Projects, datasets, people and organizations MUST each have a Statistics tab beside
  the overview. Samples and measurements MUST NOT.
- **FR-002**: Each of the four MUST be a page of its own, so that a portal can replace or extend
  one without touching the others.
- **FR-003**: A Statistics tab MUST be open to exactly the people who may open the overview of the
  same record. Where the tab is not shown, a direct request for it MUST be refused.
- **FR-004**: Every figure MUST be worked out only from records the viewer may see. A page MUST NOT
  reveal, by a count, a range, a list or a link, a record the viewer may not see.
- **FR-005**: A page with nothing to count MUST say so, and MUST NOT show an empty chart or an
  empty table.
- **FR-006**: Every figure shown as a chart MUST also be available as text on the same page.
- **FR-007**: Labels MUST be translatable, and numbers and dates MUST follow the active locale.
- **FR-008**: The pages MUST NOT offer plotting one field against another, and MUST NOT report
  views, downloads or citations.

**The dataset page**

- **FR-009**: The page MUST group its summaries by sample type and then by measurement type, list
  only the types that have records in the dataset the viewer may see, and give the number of those
  records for each type.
- **FR-010**: For each type, the page MUST summarise each of the type's statistics fields
  (FR-029). Every summary MUST give the number of records with a value and the share with none.
- **FR-011**: The summary of a numeric field MUST also give its smallest and largest value, its
  mean, its median and a distribution of its values. Where the field carries a unit, the figures
  MUST be given in it.
- **FR-012**: The summary of a date field MUST also give its earliest and latest value and a
  distribution over time.
- **FR-013**: The summary of a field with a fixed set of choices, a controlled vocabulary term or a
  yes/no value MUST also count the records holding each value, the most frequent first. When there
  are more values than the summary shows, it MUST count the rest together and say how many distinct
  values there are.
- **FR-014**: The summary of a free-text field or an identifier MUST give only the number of
  records with a value and the share with none.
- **FR-015**: A field with no values MUST still be listed, as entirely missing.
- **FR-016**: A measurement MUST be counted in the dataset it belongs to, whichever dataset its
  sample belongs to.
- **FR-017**: A visitor to a public dataset that is not published MUST be shown no field summaries.

**The project page**

- **FR-018**: The page MUST give the same summaries as the dataset page (FR-009 to FR-016), worked
  out over the samples and measurements of every dataset in the project the viewer may see. A type
  present in several datasets MUST be summarised once.
- **FR-019**: The page MUST show how many samples and measurements each dataset the viewer may see
  contributes, with each dataset linking to its page.
- **FR-020**: The page MUST show the running totals of the project's datasets, samples,
  measurements and contributors over time, counting only what the viewer may see.

**The person page**

- **FR-021**: The page MUST show the number of projects and datasets the person was credited on in
  each year. Only public projects and public datasets are counted, for every viewer, the person
  included. A record is placed in the year it was added to the portal.
- **FR-022**: The page MUST list each contribution role the person holds with the number of records
  it is held on, the most frequent first, and MUST show how the person's credits divide between
  projects, datasets, samples and measurements. Both MUST count only credits on records the viewer
  may open, and the role counts MUST equal those on the person's overview for the same viewer.
- **FR-023**: The page MUST list all of the person's collaborators, people and organizations, with
  the number of records shared with each, the most frequent first and ties by name. Each MUST link
  to that contributor's page. The ranking MUST be the one the overview's collaborators card uses.
- **FR-024**: The page MUST NOT contain an email address.

**The organization page**

- **FR-025**: The page MUST show the number of public projects and public datasets the
  organization's current members were credited on in each year, placed in time as in FR-021. A
  record on which several members are credited MUST be counted once. Former members and pending
  requests MUST NOT contribute.
- **FR-026**: The page MUST report the organization's own projects and datasets separately from
  its members' output. Its own records are those its overview counts.
- **FR-027**: The page MUST show how many of the organization's current members were credited on
  at least one counted record in each year.
- **FR-028**: The page MUST list the other organizations that are credited on a record the page
  counts, or are the affiliation recorded on a person's credit on such a record, with the number of
  records shared with each, the most frequent first and ties by name. Each MUST link to its page.

**Configuration**

- **FR-029**: A type's statistics fields MUST default to the fields its registration lists. A
  portal developer MUST be able to name a different list for a type, in the same place the type's
  other field lists are configured. Naming a field that does not exist MUST be reported when the
  portal starts.
- **FR-030**: How to choose a type's statistics fields, and how to extend or replace one of the
  four pages, MUST be documented for portal developers with a working example.

**Development data**

- **FR-031**: The demo application MUST provide development data that reaches every state the four
  pages answer for: a dataset with numeric, date, categorical and free-text fields, some with
  missing values and one entirely missing; a public dataset that is not published; an empty
  dataset; a project mixing published, unpublished and private datasets; a person credited across
  several years and roles; a person credited on nothing; and an organization with current members,
  a former member and a pending request.

### Key Entities

- **Project**: the container whose datasets the project page rolls up.
- **Dataset**: the unit of distribution whose samples and measurements the dataset page
  summarises.
- **Sample and measurement types**: the registered types a portal defines. Each brings its own
  fields, and each is summarised separately.
- **Contribution**: a contributor's credit on one project, dataset, sample or measurement, with
  the contribution roles held on it. The person and organization pages count these.
- **Collaborator**: another contributor credited on the same record, as the glossary defines it.
- **Member**: a person with a verified affiliation to an organization that has not ended.
- **Statistics fields**: the fields of a registered type that the Statistics pages summarise. A
  new term for the glossary.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A reader can learn the number of values, the range, the mean and the share missing
  for any summarised field of a dataset from the dataset's own page, without downloading anything.
- **SC-002**: For every seeded project, dataset, person and organization, no figure on its
  Statistics page changes when records the viewer may not see are added, changed or removed.
- **SC-003**: For any viewer, each record count on a project's Statistics page equals the sum of
  the matching counts on the Statistics pages of its datasets for that viewer.
- **SC-004**: For any viewer, the top of a person's collaborator list and their role counts match
  the person's overview, and an organization's own projects and datasets match its overview.
- **SC-005**: A portal that registers a new sample or measurement type gets its fields summarised
  on dataset and project pages with no further work.
- **SC-006**: A dataset holding 100,000 measurements opens its Statistics page in under three
  seconds on the reference development machine.
- **SC-007**: No Statistics tab renders a blank page, an empty chart or an error, on any seeded
  record, for a visitor or a signed-in user.
- **SC-008**: Every figure on the four pages can be read with charts unavailable and with a screen
  reader.

## Assumptions

- The pages use the page anatomy, the cards and the charting delivered by specification 018, and
  take their colours from the active theme.
- A contributor's page names only public projects and public datasets, as specification 019
  ruled. This specification does not reopen that rule.
- A contribution carries no date of its own, so a credit is placed in time by the date its record
  was added to the portal. Where a record was imported long after the work was done, the year
  shown is the year of import.
- An organization's member output counts everything a current member is credited on, including
  work from before they joined. Nothing today records which organization a person belonged to when
  a given credit was earned, other than the optional affiliation on the credit itself.
- The pages do not depend on any other feature in issue #397. A tab is something a plugin can
  already contribute. If the feature that shares the record list tabs (#403) lands first, links
  from these pages to a dataset or a contributor are unaffected.
- Summaries are worked out for the viewer who asks. Whether any of them are prepared ahead of time
  is a planning decision, as long as FR-004 holds for every viewer.
- Publications are not counted on any page. They wait on issue #194.
