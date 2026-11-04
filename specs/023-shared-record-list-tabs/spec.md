# Feature Specification: Record list tabs are shared across the pages that need them

**Feature Branch**: `023-shared-record-list-tabs`

**Created**: 2026-10-02

**Status**: Draft

**Goals**: G5: a modern, extensible interface that every portal gets by default, with no frontend
work. G9: records in the core model can be searched, sorted and filtered from the portal.

**Roadmap**: none. The request (#403) names no roadmap item. Specification 015 left a dataset's own
samples and measurements to a plugin on the dataset's page, and this is the specification that
writes it. The feature is one of seven collected in #397.

**Input**: A reader can open a dataset, a project, a person or an organization, and there is no
page that lists the samples and measurements that record holds or is credited on. The overviews
count them and link nowhere. Each of the four pages should carry a Samples tab and a Measurements
tab, showing the tables generated for each registered type, so that from any of these records a
reader can browse every sample and measurement associated with it.

## Clarifications

### Session 2026-10-01

Settled by the maintainer in conversation and recorded on #403.

- Q: How are samples and measurements shown? → A: With the tables generated for each registered
  type, the same ones the portal-wide listings use.
- Q: What does a list show to a viewer who may not see everything in it? → A: Only what that viewer
  may see.

### Session 2026-11-03

Settled by the maintainer in conversation.

- Q: Which pages carry Samples and Measurements tabs? → A: A dataset, a project, a person and an
  organization.
- Q: Which records does each of them list? → A: The ones associated with that record: those that
  belong to a dataset, those in a project's datasets, and those a person or an organization is
  credited on.

- Q: What does a viewer who may not see a public, unpublished dataset's records find? → A: No
  access means no access. The dataset's Samples and Measurements tabs are not offered to them and
  their addresses answer "not found", and its overview shows them no sample or measurement counts
  and no chart drawn from its records. This replaces specification 018's rule that a visitor sees
  those counts and charts.

### Session 2026-11-03, settled while writing

Settled while writing the specification. The reasoning for each is in `decisions.md`.

- Q: What counts as a person's samples and measurements? → A: The records they are credited on
  directly, and every record in a dataset or project they are credited on. Credit flows down from a
  project to its datasets and from a dataset to its records, as access already does.
- Q: What counts as an organization's? → A: The same as a person's, and also every record in the
  projects it owns.
- Q: Does credit flow anywhere else? → A: No. Being credited on a sample does not bring in the
  measurements others made of it. An organization does not get the records its members are
  credited on.
- Q: On a person's or an organization's page, which records are shown to whom? → A: A person
  viewing their own page sees every record of theirs they may see, unpublished and private ones
  included. Everyone else, and every viewer of an organization's page, sees released records only:
  those whose own dataset is public, published and not in a private project. This is the rule
  specification 032 set for lists of one person's records, and the filters follow it.
- Q: On a dataset's or a project's page? → A: What the viewer may see. The dataset's team sees its
  unpublished records, and a visitor sees published ones.
- Q: Which records count as a dataset's? → A: The ones that belong to it. A measurement that
  belongs to the dataset is listed even when its sample belongs to another dataset. That sample is
  not listed among this dataset's samples.
- Q: Which records count as a project's? → A: The ones that belong to the project's datasets, by the
  same rule.
- Q: A page holds several sample types. How does one tab show them? → A: One type's table at a
  time, with a way to move between the types present. Types with no records there are not offered.
- Q: On a page whose records come from several datasets, how does a reader tell them apart? → A:
  Each row names the dataset it belongs to.
- Q: Is a tab shown when its list is empty? → A: Yes. A page carries the same tabs whatever they
  hold, and an empty one says so.
- Q: Where a dataset's or a project's overview counts its samples and measurements, does the count
  lead anywhere? → A: Yes, to the matching tab.

### Session 2026-11-04

Settled by the maintainer in conversation and recorded on #644.

- Q: Does a sample get a list of its measurements? → A: Yes, a Measurements tab on the sample. It
  is a separate plugin from the Measurements tab of a dataset, a project and a contributor, and
  shares that tab's code.
- Q: Which measurements does it list? → A: Every measurement made on the sample that the viewer may
  see, whichever dataset it belongs to. Each is listed or left out by its own dataset.
- Q: How are several measurement types shown? → A: Each type in its own table, all on one page, one
  after another, so that results from different methods are read together. Each table pages on its
  own. There is no search and no filter.
- Q: Is the project's Export tab kept? → A: No. A dataset is the unit of distribution, and the tab
  is removed with nothing in its place.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A dataset's samples and measurements can be browsed from its page (Priority: P1)

A reader opens a dataset and wants to see what is in it. Beside the overview are two tabs, one for
the dataset's samples and one for its measurements. Each shows a table of the records of one
registered type, with the columns, filters and search that type's registration produces. A dataset
that holds more than one type offers a way to move between them. A row leads to the record's page.
A visitor sees the tabs, and the records, once the dataset is published. Until then only the
dataset's team does.

**Why this priority**: The dataset is the unit a reader cites and reuses. Its overview shows how
many samples and measurements it holds, and no page lists them. This story also puts in place the
tab, the type tables and the visibility rules the other stories reuse.

**Independent Test**: Load development data. As a visitor and as a member of the dataset's team,
open a published dataset holding several sample and measurement types, a public dataset that is not
published, and a dataset holding nothing. Open both tabs on each and compare what is shown against
FR-001 to FR-020.

**Acceptance Scenarios**:

1. **Given** a published dataset holding samples of two registered types, **When** a visitor opens
   its Samples tab, **Then** the samples of one type are shown in that type's table, and the visitor
   can move to the other type's table.
2. **Given** the same dataset, **When** the visitor has chosen a type and opens the page's address
   in a new window, **Then** the same type's table is shown.
3. **Given** a dataset holding samples of one type only, **When** its Samples tab is opened,
   **Then** that type's table is shown and no choice between types is offered.
4. **Given** a portal with a registered sample type the dataset holds none of, **When** the
   dataset's Samples tab is opened, **Then** that type is not offered.
5. **Given** a type's table on either tab, **When** the reader searches, filters or sorts it,
   **Then** the rows narrow or reorder as they do on that type's portal-wide listing, and never
   include a record from another dataset.
6. **Given** a row in either tab, **When** the reader follows it, **Then** they arrive at that
   record's page.
7. **Given** a dataset whose measurements include some made on samples that belong to another
   dataset, **When** its Measurements tab is opened, **Then** those measurements are listed, and the
   other dataset's samples are not listed on its Samples tab.
8. **Given** a measurement in the dataset whose sample belongs to a dataset the viewer may not
   open, **When** the Measurements tab is opened, **Then** the measurement is listed and its sample
   is neither named nor linked.
9. **Given** a public dataset that is not published, **When** a visitor opens it, **Then** it
   has no Samples or Measurements tab, either tab's address answers "not found", and its overview
   shows no sample or measurement count and no chart drawn from its records.
10. **Given** the same dataset, **When** a member of its team opens it, **Then** both tabs are
    there, its records are listed, and the overview shows the counts.
11. **Given** a private dataset, **When** a visitor requests either tab's address, **Then** the
    answer is the same "not found" the dataset's overview gives.
12. **Given** a dataset with no samples, **When** anyone who may open it opens the Samples tab,
    **Then** the tab is there and says the dataset has no samples.
13. **Given** a dataset's overview that counts its samples and measurements, **When** the reader
    follows a count, **Then** they arrive at the matching tab, and the records listed there for the
    same viewer number the same as the count.
14. **Given** a portal developer who registers a new sample type and adds records of it to a
    dataset, **When** the dataset's Samples tab is opened, **Then** the new type is offered with a
    working table, and nothing else was configured.
15. **Given** a table with a hundred rows and one with ten, **When** each is loaded, **Then** both
    issue the same number of database queries.

---

### User Story 2 - A project's samples and measurements can be browsed from its page (Priority: P2)

A reader opens a project and wants every sample and measurement gathered under it, without opening
each dataset in turn. The project's Samples and Measurements tabs list the records in the project's
datasets that the reader may see, in the same type tables as a dataset's tabs. Each row names the
dataset it belongs to.

**Why this priority**: A project groups several datasets, and the records a reader looks for are
spread across them. The dataset tabs already give access to each part, so this story is the next
step rather than the first.

**Independent Test**: Load development data. As a visitor and as a member of one of the project's
private datasets, open the tabs of a project holding public published, public unpublished and
private datasets, and of a project with no datasets. Compare against FR-021 to FR-025.

**Acceptance Scenarios**:

1. **Given** a project with two published public datasets, **When** a visitor opens its Samples
   tab, **Then** the samples of both datasets are listed, and each row names and links its dataset.
2. **Given** a project with a private dataset, **When** a visitor opens either tab, **Then** none
   of that dataset's records are listed, counted or offered as filter choices.
3. **Given** the same project, **When** a member of the private dataset's team opens either tab,
   **Then** that dataset's records are listed along with the public ones.
4. **Given** a project whose only dataset is public and not published, a project whose datasets
   hold no records the viewer may see, and a project with no datasets, **When** a visitor opens either tab on each, **Then** both say there are no records in
   the same way, so the reply does not reveal that hidden records exist.
5. **Given** a measurement in one of the project's datasets made on a sample in another project,
   **When** the Measurements tab is opened, **Then** the measurement is listed and the sample is not
   listed on the Samples tab.
6. **Given** a project's overview that counts its samples and measurements, **When** the reader
   follows a count, **Then** they arrive at the matching tab, and the records listed there for the
   same viewer number the same as the count.
7. **Given** a project the viewer may not open, **When** either tab's address is requested,
   **Then** the answer is the same "not found" the project's overview gives.

---

### User Story 3 - A contributor's samples and measurements can be browsed from their page (Priority: P2)

A reader opens a person's or an organization's page and wants to see the samples and measurements
that contributor has worked on. The Samples and Measurements tabs list the records the
contributor is credited on directly, and every record in the datasets and projects they are
credited on. An organization's tabs also list the records in the projects it owns. Visitors see
released records. A person on their own page also sees their unpublished and private ones. Each row
names the dataset it belongs to.

**Why this priority**: A contributor's page is where a reader learns what someone has done. It
already lists their projects and datasets, and the records within them are the natural next level.
Fewer readers need it than need the dataset's tabs.

**Independent Test**: Load development data. Open the tabs of a person credited on a project, on a
dataset in another project and on a single sample in a third, and of an organization that owns one
project and is credited on a dataset in another. Open each as a visitor and as the person. Compare
against FR-026 to FR-030.

**Acceptance Scenarios**:

1. **Given** a person credited on a public project, **When** anyone opens their Samples tab,
   **Then** the released samples in that project's datasets are listed.
2. **Given** a person credited on a dataset in a project they are not credited on, **When** their
   Samples tab is opened, **Then** that dataset's released samples are listed, and the project's
   other datasets are not.
3. **Given** a person credited on one released sample only, **When** their Samples tab is opened,
   **Then** that sample is listed, and its siblings in the same dataset are not.
4. **Given** a person credited on a sample, **When** their Measurements tab is opened, **Then** the
   measurements others made of that sample are not listed unless the person is credited on them or
   on their dataset or project.
5. **Given** an organization that owns a project, **When** its Samples tab is opened, **Then** the
   released samples in that project's datasets are listed, though the organization is credited on
   none of them.
6. **Given** an organization whose members are credited on records the organization is not, **When**
   its tabs are opened, **Then** those records are not listed.
7. **Given** a person credited on a private dataset, an unpublished public dataset and a public
   dataset in a private project, **When** anyone else opens the person's tabs, **Then** none of
   those records are listed, counted or offered as filter choices.
8. **Given** the same person, **When** they open their own tabs, **Then** the records in those
   datasets they may see are listed and offered as filter choices.
9. **Given** an organization credited on a private dataset, **When** anyone opens its tabs, a
   member of the dataset's team included, **Then** that dataset's records are not listed.
10. **Given** a record a contributor is credited on in more than one way, **When** their tab is
   opened, **Then** the record is listed once.
11. **Given** a contributor with no records the viewer may see, **When** either tab is opened, **Then** the tab
   is there and says there are none.

---

### User Story 4 - A sample's measurements can be browsed from its page (Priority: P2)

A reader opens a sample and wants to compare what has been measured on it. The sample's
Measurements tab lists every measurement made on the sample that the reader may see, whichever
dataset it belongs to. Each measurement type has its own table, with the columns its registration
produces, and every type is on the one page, one table after another, so that results from
different methods are read side by side. Each row names the dataset the measurement belongs to.

**Why this priority**: A sample is where the results of several methods meet. Its overview lists
the most recent measurements and counts the rest, and no page lists them all.

**Independent Test**: Load development data. As a visitor and as a member of the sample's dataset,
open the Measurements tab of a sample measured by several methods in its own dataset, in another
published dataset and in a dataset the visitor may not open, and of a sample with no measurements.
Compare against FR-034 to FR-040.

**Acceptance Scenarios**:

1. **Given** a sample with measurements of two registered types, **When** a reader opens its
   Measurements tab, **Then** both types' tables are on the page, the most numerous type first,
   each with that type's columns.
2. **Given** a measurement of the sample that belongs to another dataset the reader may open,
   **When** the tab is opened, **Then** it is listed, and its row names and links that dataset.
3. **Given** a measurement of the sample that belongs to a dataset the reader may not open, **When**
   the tab is opened, **Then** it is not listed or counted, even when the reader is on the team of
   the sample's own dataset.
4. **Given** a sample with no measurements the reader may see, **When** the tab is opened, **Then**
   the tab is there and says the sample has no measurements.
5. **Given** a sample the reader may not open, **When** the tab's address is requested, **Then** the
   answer is the same "not found" the sample's overview gives.
6. **Given** a table with more rows than one page holds, **When** the reader moves to its next page,
   **Then** that table moves and the others stay where they were.
7. **Given** measurements of a type that is no longer registered, **When** the tab is opened,
   **Then** they are listed in a table of the fields every measurement has.
8. **Given** the sample's overview, **When** the reader follows its Measurements figure or the
   card's link, **Then** they arrive at the tab.

---

### Edge Cases

- A page holds records of a type whose registration has since been removed. They are listed in a
  table of the fields every sample, or every measurement, has, and the tab does not fail.
- A type's registration declares its own table class. It is used unchanged, as on the type's
  portal-wide listing.
- The reader asks for a type by address that the page holds none of, or that is not registered.
  The answer is "not found".
- A filter on a table draws its choices from related records. It offers no value that would reveal
  a record the viewer may not see, for a visitor and for a team member alike.
- A dataset is published. On the next request a visitor finds its Samples and Measurements tabs,
  the records and the counts.
- A contributor is credited on a very large dataset. Their tab pages its results like any other,
  and the number of queries it issues does not grow with them.
- A dataset is moved to another project. The next request lists its records under the new project
  and not the old one.

## Requirements *(mandatory)*

### Functional Requirements

**Every Samples and Measurements tab**

- **FR-001**: A dataset, a project, a person and an organization MUST each carry a Samples tab and
  a Measurements tab. A sample MUST carry a Measurements tab of its own (FR-034). No other page gets
  one from this feature.
- **FR-002**: The Samples tab MUST be one plugin registered on all four pages, and the Measurements
  tab likewise. Each page supplies only which records it lists. FR-001 to FR-020 describe these two
  plugins. A sample's Measurements tab is described by FR-034 to FR-040.
- **FR-003**: A tab MUST have the same address segment, beneath the record's own address, on every
  page that carries it.
- **FR-004**: A tab MUST be present on its page whatever it holds, and an empty list MUST say that
  it is empty. The one exception is FR-022.
- **FR-005**: The two tabs MUST come in the order samples, measurements, after any Projects or
  Datasets tab the page already has.
- **FR-006**: A tab MUST open for exactly the viewers the record's overview opens for. Anyone else
  MUST get the same "not found" the overview gives them.
- **FR-007**: A tab MUST NOT name, count, link or otherwise reveal a record the viewer may not see.
  That covers its rows, its totals, its page count, the types it offers, the choices its filters
  offer and its empty state.
- **FR-008**: Each tab MUST show its records in the table generated for their registered type, one
  type at a time, with the columns that type's registration produces.
- **FR-009**: Where the page lists records of more than one type, the tab MUST offer a way to move
  between them, offering only the types it lists records of. Where it lists one type, no choice
  MUST be offered.
- **FR-010**: The chosen type MUST be part of the page's address, so that a link to it opens the
  same table. An address naming a type that is not offered MUST answer "not found".
- **FR-011**: A table MUST offer the search, the filters and the sortable columns its type's
  portal-wide listing offers, applied within the page's own records.
- **FR-012**: A table MUST page its results, and opened with no sort chosen it MUST return rows in a
  stable, repeatable order.
- **FR-013**: A row MUST lead to that record's page.
- **FR-014**: A measurement's row MUST name and link its sample only where the viewer may open that
  sample.
- **FR-015**: On a project, a person and an organization, each row MUST name the dataset the record
  belongs to and link to it.
- **FR-016**: A record MUST be listed once on a page, however many ways it is associated with that
  page's record.
- **FR-017**: A type registered after this feature ships MUST appear in the tabs, with a working
  table, from its registration alone.
- **FR-018**: Records of a type that is no longer registered MUST be listed in a table of the
  fields every record of that kind has.
- **FR-019**: The number of database queries a table issues MUST NOT grow with the number of rows
  it shows or the number of records the page lists.
- **FR-020**: The way to move between types MUST be reachable and operable by keyboard and named
  for assistive technology.

**On a dataset**

- **FR-021**: The tabs MUST list the samples and the measurements that belong to the dataset. A
  record that belongs to another dataset MUST NOT appear, however it is related to this one.
- **FR-022**: A viewer who may not see the dataset's records, such as a visitor to a public
  dataset that is not published, MUST NOT be offered its Samples or Measurements tab, and either
  tab's address MUST answer them "not found". The dataset's overview MUST NOT show them a sample or
  measurement count or a chart drawn from its records. Once the dataset is published, or for its
  team at any time, the tabs and the counts are shown.

**On a project**

- **FR-023**: The tabs MUST list the samples and measurements that belong to the project's
  datasets and that the viewer may see, by the rule that applies to each record's own dataset.
- **FR-024**: A project whose records the viewer may not see, because their datasets are private
  or not published, MUST say the same as a project with none. The project's overview MUST count
  only the samples and measurements the viewer may see.
- **FR-025**: Where a dataset's or a project's overview counts its samples or measurements, the
  count MUST lead to the matching tab, and the tab MUST list as many records as the overview counts
  for the same viewer.

**On a person and an organization**

- **FR-026**: A person's tabs MUST list the samples and measurements the person is credited on, and
  every sample and measurement that belongs to a dataset the person is credited on or to a dataset
  in a project the person is credited on.
- **FR-027**: An organization's tabs MUST list what FR-026 lists for it, and also every sample and
  measurement that belongs to a dataset in a project it owns.
- **FR-028**: Credit on a sample MUST NOT bring in measurements made of it. Credit held by an
  organization's members MUST NOT bring in records for the organization.
- **FR-029**: On a person's own page, viewed by that person, the tabs MUST list the records FR-026
  names that the person may see. To every other viewer, and on an organization's page to every
  viewer, they MUST list only released records. Filter choices MUST follow the same rule.
- **FR-030**: A measurement MUST be listed or left out by its own dataset, never by its sample's.

**On a sample**

- **FR-034**: A sample's Measurements tab MUST be a plugin of its own, registered on the sample. It
  MUST use the same type tables, dataset column and handling of unregistered types as the tabs of
  FR-001 to FR-020, defined once.
- **FR-035**: The tab MUST list every measurement made on the sample that the viewer may see,
  whichever dataset it belongs to. Each measurement MUST be listed or left out by its own dataset's
  visibility, never by its sample's (FR-030).
- **FR-036**: Each measurement type listed MUST have its own table, with the columns its
  registration produces, and every listed type MUST be on the one page, one table after another,
  the most numerous first. Types with no measurement listed MUST NOT be shown. The tab offers no
  search and no filters.
- **FR-037**: Each row MUST name the dataset the measurement belongs to and link it where the viewer
  may open it. A row MUST NOT name the sample, since every row is on it.
- **FR-038**: Each table MUST page its rows on its own: moving through one table MUST leave the
  others on the page they show.
- **FR-039**: The tab MUST open for exactly the viewers the sample's overview opens for, and anyone
  else MUST get the same "not found". It MUST be present when the sample has no measurements the
  viewer may see, and say so.
- **FR-040**: The number of database queries the tab issues MUST NOT grow with the number of rows
  it shows.

**Across the feature**

- **FR-031**: Every piece of text the tabs show MUST be marked for translation, and dates and
  numbers MUST follow the active locale.
- **FR-032**: The development data MUST make every state in this specification reachable as a
  visitor or as one of the development accounts: a dataset with several sample and measurement
  types, a public dataset that is not published, an empty dataset, a measurement on another
  dataset's sample, a project with public, unpublished and private datasets, a person credited at
  each level, an organization that owns a project, and a sample measured by several methods in its
  own dataset, in another dataset and in a dataset a visitor may not open.
- **FR-033**: The documentation for portal developers MUST name the two plugins, say which pages
  they are registered on, say which records each page lists, and say where a table's columns,
  filters and search come from. The documentation for portal users MUST describe how to browse the
  samples and measurements of a dataset, a project and a contributor, and the measurements of a
  sample.

### Which story owns which requirement

| Story | Requirements |
|---|---|
| US-1: a dataset's samples and measurements, and the rules every tab shares | FR-001 to FR-022, FR-025 for the dataset, FR-031 to FR-033 |
| US-2: a project's samples and measurements | FR-023 to FR-025 |
| US-3: a contributor's samples and measurements | FR-026 to FR-030 |
| US-4: a sample's measurements | FR-034 to FR-040 |

FR-001 to FR-020 describe every tab in this feature. US-1 puts them in place on the dataset, and
each later story meets them on its own pages. Each later story also extends the development data
(FR-032) and the documentation (FR-033) for its own pages.

### Key Entities

- **Samples tab, Measurements tab**: A tab beside a record's overview listing the samples, or the
  measurements, associated with that record. One plugin each, registered on four pages.
- **A sample's Measurements tab**: A tab beside a sample's overview listing the measurements made on
  it, every type at once. A plugin of its own, sharing the tables of the other tabs.
- **Type table**: The table FairDM generates for a registered sample or measurement type from its
  registration. The portal-wide listing of that type uses the same one.
- **A dataset's records**: The samples and measurements that belong to the dataset. A measurement
  belongs to its own dataset, which may differ from its sample's.
- **A contributor's records**: The records a person or organization is credited on, directly or
  through a dataset or project above them, and for an organization the records in the projects it
  owns.
- **Released**: A record whose own dataset is public, published and not in a private project. A
  contributor's tabs list released records only, except a person's own tabs viewed by that person.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A dataset, a project, a person and an organization each have a Samples and a
  Measurements tab, a sample has a Measurements tab, and no other page has either.
- **SC-002**: Each of the two tabs is defined once. A change made to one is seen on all four pages,
  with no second place to change.
- **SC-003**: Signed in as each development account and as a visitor, no tab names, counts or links
  a record that account may not see.
- **SC-004**: From any of the four pages, a reader reaches any associated sample or measurement
  they may see without leaving that page's tabs.
- **SC-005**: A portal that registers a new sample or measurement type sees it in the tabs with no
  template, view or address written for it.
- **SC-006**: The query count of a tab is the same for a contributor with ten records and one with
  ten thousand.

## Assumptions

- Access to projects, datasets, samples and measurements follows the rules FairDM already enforces
  and specification 018 states: a sample follows its dataset, and a measurement follows its own
  dataset, not its sample's. This feature applies those rules to lists. It changes one rule of
  specification 018: a viewer who may not see a public, unpublished dataset's records is no longer
  shown its sample and measurement counts or the charts drawn from them (FR-022), and a project's
  figures count only what the viewer may see (FR-024).
- Contributor pages keep the rule specification 019 set for them: they show the same public records
  to every viewer.
- The type tables, their filters and their search are the ones specification 015 delivered for the
  portal-wide listings. This feature narrows them to one record's associated records and adds
  nothing to what a registration can declare.
- The tabs sit in the tab strip the plugin system already provides (specification 008). Where
  another feature adds a tab to the same pages, such as Contributors, Map or Statistics, that tab
  comes after these.
- Out of scope, each owned elsewhere: merging the duplicate Projects and Datasets tabs, and an
  organization's Members tab (#649); an export or download on the dataset (#397); a data
  dictionary linked from the tabs (#397); the Contributors tab (#402); the Map tab (#405); the
  Statistics tabs (#406).
