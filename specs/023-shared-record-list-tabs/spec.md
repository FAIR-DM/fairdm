# Feature Specification: Record list tabs are shared across the pages that need them

**Feature Branch**: `023-shared-record-list-tabs`

**Created**: 2026-10-02

**Status**: Draft

**Goals**: G5: a modern, extensible interface that every portal gets by default, with no frontend
work. G9: records in the core model can be searched, sorted and filtered from the portal.

**Roadmap**: none. The request (#403) names no roadmap item. Specification 015 left a dataset's own
samples and measurements to a plugin on the dataset's page, and this is the specification that
writes it. The feature is one of seven collected in #397.

**Input**: The tabs that list one kind of record on another record's page are uneven. A project
lists its datasets and a contributor lists theirs, through two separate plugins that do the same
job. A dataset has no tab listing its samples or its measurements, a sample has none for its
measurements, and an organization has none for its members. Each list should be one plugin, written
once and registered on every page it applies to: Projects on a person and an organization, Datasets
on a project, a person and an organization, Samples and Measurements on a dataset, Measurements on a
sample, and Members on an organization. Every list shows only what the viewer may see. The project's
Export tab is removed, because a dataset is the unit of distribution and export belongs there.

## Clarifications

### Session 2026-10-01

These were settled by the maintainer in conversation and are recorded on #403.

- Q: How are a dataset's samples and measurements shown? → A: With the tables generated for each
  registered type, the same ones the portal-wide listings use.
- Q: Is Measurements on a sample the same plugin as Measurements on a dataset? → A: No. On a sample
  it shows one sample's results so they can be compared across methods. On a dataset it shows the
  dataset's measurements by type.
- Q: Do person and organization pages get Samples or Measurements tabs? → A: No.
- Q: Does a project get Samples or Measurements tabs? → A: No. They are reached through its
  datasets.
- Q: What does a list show to a viewer who may not see everything in it? → A: Only what that viewer
  may see.
- Q: Does the project keep its Export tab? → A: No. It is removed. A dataset is the unit of
  distribution, so export belongs there.

### Session 2026-10-02

These were settled while writing the specification. The reasoning for each is in `decisions.md`.

- Q: "Only what the viewer may see" and specification 019's rule for contributor pages differ. On a
  person's or an organization's page, which applies? → A: 019's. Those two pages list public
  projects and public datasets only, for every viewer, the contributor included. Public records are
  records every viewer may see, so the rule on #403 holds there too.
- Q: Which datasets does a project's Datasets tab list? → A: The project's datasets that the viewer
  may open. A project member sees the private ones they have access to, and a visitor sees the
  public ones.
- Q: Which records count as a dataset's samples and measurements? → A: The ones that belong to it.
  A measurement that belongs to the dataset is listed even when its sample belongs to another
  dataset. A sample from another dataset is not listed among this dataset's samples because one of
  this dataset's measurements was made on it.
- Q: What does a visitor find on the Samples and Measurements tabs of a public dataset that is not
  published? → A: No records, and a statement that the data is not published yet, which is a
  different state from a dataset that holds nothing.
- Q: A dataset holds several sample types. How does one tab show them? → A: One type's table at a
  time, with a way to move between the types the dataset holds. Types it holds none of are not
  offered.
- Q: Which measurements does a sample's Measurements tab list, and what does comparing across
  methods mean? → A: Every measurement made on the sample that the viewer may see, whichever dataset
  it belongs to. All of them are on one page, grouped by measurement type, each group in that type's
  own table, so results from different methods are read together.
- Q: Who is listed on an organization's Members tab? → A: Its members as the glossary defines them:
  people with a verified affiliation that has not ended. Pending requests and former members are
  left out, as on the overview.
- Q: Is a tab shown when its list is empty? → A: Yes. A page carries the same tabs whatever they
  hold, and an empty one says so.
- Q: Do the addresses of the existing Projects and Datasets tabs survive? → A: No. Each list gets
  one address segment, the same on every page that carries it. The old ones are not redirected.
- Q: Does removing the project's Export tab add an export to the dataset? → A: No. This feature
  removes the tab and nothing else. What a dataset offers for download is described in #397 and is
  not specified here.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A dataset's samples and measurements can be browsed from its page (Priority: P1)

A reader opens a dataset and wants to see what is in it. Beside the overview are two tabs, one for
the dataset's samples and one for its measurements. Each shows a table of the records of one
registered type, with the columns, filters and search that type's registration produces. A dataset
that holds more than one type offers a way to move between them. A row leads to the record's page.
A visitor sees the records once the dataset is published, and the dataset's team sees them at any
time.

**Why this priority**: This is the list that does not exist at all. The dataset is the unit a
reader cites and reuses, its overview shows how many samples and measurements it holds, and there is
no page that lists them.

**Independent Test**: Load development data. As a visitor and as a member of the dataset's team,
open a published dataset holding several sample and measurement types, a public dataset that is not
published, and a dataset holding nothing. Open both tabs on each and compare what is shown against
FR-008 to FR-021.

**Acceptance Scenarios**:

1. **Given** a published dataset holding samples of two registered types, **When** a visitor opens
   its Samples tab, **Then** the samples of one type are shown in that type's table, and the visitor
   can move to the other type's table.
2. **Given** the same dataset, **When** the visitor has chosen a type and copies the page's address
   into a new window, **Then** the same type's table is shown.
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
9. **Given** a public dataset that is not published, **When** a visitor opens either tab, **Then**
   no record is listed and the page tells the visitor the data is not published, which it does not
   do for a dataset that holds no records.
10. **Given** the same dataset, **When** a member of its team opens either tab, **Then** its records
    are listed.
11. **Given** a private dataset, **When** a visitor requests either tab's address, **Then** the
    answer is the same "not found" the dataset's overview gives.
12. **Given** a dataset with no samples, **When** anyone who may open it opens the Samples tab,
    **Then** the tab is there and says the dataset has no samples.
13. **Given** a portal developer who registers a new sample type and adds records of it to a
    dataset, **When** the dataset's Samples tab is opened, **Then** the new type is offered with a
    working table, and nothing else was configured.
14. **Given** a table with a hundred rows and one with ten, **When** each is loaded, **Then** both
    issue the same number of database queries.

---

### User Story 2 - A sample's measurements are read together across methods (Priority: P2)

A reader opens a sample that has been measured several ways, perhaps by more than one team. The
overview names the most recent measurements and counts the rest. The Measurements tab lists all of
them on one page, grouped by measurement type, each group in that type's own table. The reader sees
what each method found for this one sample without opening each measurement in turn. A measurement
that belongs to a different dataset than the sample says which.

**Why this priority**: A measurement may belong to a different dataset than its sample, which is
how one team measures another team's specimens. The sample's page is the only place where all of
those results meet, and today it shows a short list and a count.

**Independent Test**: Load development data. Open a sample measured by two methods in its own
dataset and by a third in another dataset, a sample measured in a dataset the viewer may not open,
and a sample with no measurements. Compare the Measurements tab on each against FR-022 to FR-028.

**Acceptance Scenarios**:

1. **Given** a sample with measurements of three registered types, **When** its Measurements tab is
   opened, **Then** all three types are on the one page, each as its own group with the columns its
   registration produces.
2. **Given** a sample with a measurement that belongs to another dataset the viewer may open,
   **When** the tab is opened, **Then** that measurement is listed and its row identifies the
   dataset it belongs to.
3. **Given** a sample with a measurement that belongs to a dataset the viewer may not open,
   **When** the tab is opened, **Then** that measurement is not listed, counted or hinted at.
4. **Given** a member of the sample's dataset team and a measurement on the sample in a private
   dataset they are not part of, **When** they open the tab, **Then** that measurement is not
   listed.
5. **Given** a sample whose overview counts more measurements than it shows, **When** the reader
   follows the overview's way to the rest, **Then** they arrive at the Measurements tab, and the
   number of measurements listed there equals the overview's total.
6. **Given** a sample with no measurements the viewer may see, **When** the tab is opened, **Then**
   the tab is there and says there are none.
7. **Given** a row in the tab, **When** the reader follows it, **Then** they arrive at that
   measurement's page.
8. **Given** a sample the viewer may not open, **When** the tab's address is requested, **Then**
   the answer is the same "not found" the sample's overview gives.

---

### User Story 3 - Projects and Datasets lists are one plugin each, wherever they appear (Priority: P2)

A reader moves between a project, a person and an organization, and the Datasets tab on each looks
and works the same way: the same list, the same search, the same ordering, the same way of reaching
a dataset. The Projects tab on a person and an organization is likewise one list. A portal
developer or addon author finds one plugin behind each, so a fix or an improvement to it reaches
every page. On the way, the project's Datasets tab stops listing datasets the viewer may not open,
and the project's Export tab is removed.

**Why this priority**: These lists exist and work. The gain is that they behave alike and are
maintained once. The one defect this story fixes is that a project's Datasets tab lists every
dataset in the project, whoever is looking.

**Independent Test**: Load development data. As a visitor and as a project member, open the
Datasets tab on a project with public and private datasets, on a person and on an organization, and
the Projects tab on the person and the organization. Compare against FR-029 to FR-037. Confirm the
project has no Export tab and that its old address is not found.

**Acceptance Scenarios**:

1. **Given** a project with public and private datasets, **When** a visitor opens its Datasets tab,
   **Then** only the public datasets are listed.
2. **Given** the same project, **When** a person with access to one of its private datasets opens
   the tab, **Then** that dataset is listed along with the public ones, and private datasets they
   have no access to are not.
3. **Given** a person credited on public and private datasets, **When** anyone opens the Datasets
   tab on that person's page, the person included, **Then** only the public datasets are listed.
4. **Given** an organization that owns a project, is credited on a second, and is credited on a
   dataset in a third, **When** its Projects and Datasets tabs are opened, **Then** Projects lists
   the first two, Datasets lists the public datasets of the project it owns and the dataset it is
   credited on, and nothing is listed twice.
5. **Given** the Datasets tab on a project, a person and an organization, **When** each is
   searched and reordered, **Then** each offers the same search and the same orderings, and the
   results stay within that page's own datasets.
6. **Given** the Datasets tab on any of the three pages, **When** its address is compared with the
   others, **Then** the segment after the record's own address is the same on all three. The same
   holds for the Projects tab on a person and an organization.
7. **Given** a contributor's overview card that offers a way to the full list of their projects or
   datasets, **When** it is followed, **Then** it arrives at the Projects or Datasets tab.
8. **Given** any project, **When** its page is opened, **Then** there is no Export tab, and the
   address the Export tab had answers "not found".
9. **Given** a project, a dataset or a measurement, **When** its tabs are read, **Then** the project
   has no Samples or Measurements tab, the measurement has no list tab from this feature, and a
   person and an organization have no Samples or Measurements tab.
10. **Given** the plugins FairDM registers, **When** they are counted, **Then** there is exactly one
    for each of Projects, Datasets, Samples, Measurements on a dataset, Measurements on a sample
    and Members.

---

### User Story 4 - An organization's members are listed in full (Priority: P3)

A visitor opens an organization and wants to know who belongs to it. The overview shows as many
members as its card has places and counts the rest. The Members tab lists all of them, the people
who run the organization first, and each entry leads to that person's page. A large organization
can be searched by name.

**Why this priority**: The overview already shows the first members and announces the full list as
not available yet. This story supplies it. Fewer readers arrive at an organization than at a
dataset or a sample.

**Independent Test**: Load development data. Open the Members tab of an organization with an owner,
administrators, ordinary members, a pending request and a former member, and of an organization
with no members. Compare against FR-038 to FR-044.

**Acceptance Scenarios**:

1. **Given** an organization with current, pending and former members, **When** its Members tab is
   opened, **Then** only people with a verified affiliation that has not ended are listed.
2. **Given** an organization with an owner, administrators and other members, **When** the tab is
   opened, **Then** the owner comes first, then the administrators, then the other members, each
   group by name, and the owner and administrators are marked as such.
3. **Given** an entry in the list, **When** it is followed, **Then** the reader arrives at that
   person's page.
4. **Given** an organization with more members than one page of the list holds, **When** the reader
   searches for a name, **Then** the list narrows to the members whose name matches.
5. **Given** an organization whose overview counts members beyond those its card shows, **When**
   the reader follows the overview's way to the rest, **Then** they arrive at the Members tab, and
   the number listed equals the overview's member count.
6. **Given** any organization, **When** the Members tab is rendered, **Then** no member's email
   address is in the page.
7. **Given** an organization with no members, **When** the tab is opened, **Then** the tab is there
   and says the organization has no members.
8. **Given** a person or a project, **When** its tabs are read, **Then** there is no Members tab.

---

### Edge Cases

- A dataset holds records of a type whose registration has since been removed. They are listed in
  a table of the fields every sample, or every measurement, has, and the tab does not fail.
- A type's registration declares its own table class. It is used unchanged, as on the type's
  portal-wide listing.
- The reader asks for a type by address that the dataset holds none of, or that is not registered.
  The answer is "not found".
- A filter on a dataset's table draws its choices from related records. It offers no value that
  would reveal a record the viewer may not see.
- A dataset is published while a visitor has its Samples tab open. The next request lists the
  records.
- A person is both the owner of an organization and has a second affiliation to it that has ended.
  They are listed once, as the owner.
- A person's page is opened by that person. The Projects and Datasets tabs list the same records a
  visitor sees.
- A measurement's dataset is made private after a reader has opened the sample's Measurements tab.
  The next request leaves it out, and its own page answers "not found".
- A project has no datasets the viewer may open. The Datasets tab is there and says so, in the
  same way for a project that has none at all, so the reply does not reveal that hidden datasets
  exist.

## Requirements *(mandatory)*

### Functional Requirements

**Where the tabs are**

- **FR-001**: The pages MUST carry these list tabs and no others from this feature:

  | Tab | On |
  |---|---|
  | Projects | person, organization |
  | Datasets | project, person, organization |
  | Samples | dataset |
  | Measurements | dataset |
  | Measurements | sample |
  | Members | organization |

- **FR-002**: Each row of that table MUST be served by one plugin. Measurements on a dataset and
  Measurements on a sample MUST be two different plugins. No second plugin doing the same job may
  remain registered.
- **FR-003**: A tab MUST have the same address segment, beneath the record's own address, on every
  page that carries it. The addresses the Projects and Datasets tabs had before this feature are
  not kept and are not redirected.
- **FR-004**: A tab MUST be present on its page whatever it holds, and an empty list MUST say that
  it is empty.
- **FR-005**: The list tabs on a page MUST come directly after the overview, in the order projects,
  datasets, samples, measurements, members.
- **FR-006**: A tab MUST open for exactly the viewers the record's overview opens for. Anyone else
  MUST get the same "not found" the overview gives them.
- **FR-007**: A list MUST NOT name, count, link or otherwise reveal a record the viewer may not
  see. That covers its rows, its totals, its page count, the choices its filters offer and its
  empty state.

**Samples and Measurements on a dataset**

- **FR-008**: The Samples tab MUST list the samples that belong to the dataset, and the
  Measurements tab the measurements that belong to it. A record that belongs to another dataset
  MUST NOT appear in either, however it is related to this one.
- **FR-009**: Each tab MUST show its records in the table generated for their registered type, one
  type at a time, with the columns that type's registration produces.
- **FR-010**: Where the dataset holds records of more than one type, the tab MUST offer a way to
  move between them. It MUST offer only the types the dataset holds records of that the viewer may
  see. Where it holds one type, no choice MUST be offered.
- **FR-011**: The chosen type MUST be part of the page's address, so that a link to it opens the
  same table. An address naming a type that is not offered MUST answer "not found".
- **FR-012**: A table MUST offer the search, the filters and the sortable columns its type's
  portal-wide listing offers, applied within the dataset's own records.
- **FR-013**: A table MUST page its results, and opened with no sort chosen it MUST return rows in a
  stable, repeatable order.
- **FR-014**: A row MUST lead to that record's page.
- **FR-015**: A visitor MUST be shown the records only once the dataset is published. The dataset's
  team MUST be shown them at any time.
- **FR-016**: Where the viewer may open the dataset and may not yet see its records, the tab MUST
  tell them the data is not published. It MUST NOT present that state as a dataset that holds
  nothing.
- **FR-017**: A measurement's row MUST name and link its sample only where the viewer may open that
  sample.
- **FR-018**: A type registered after this feature ships MUST appear in the tab, with a working
  table, from its registration alone.
- **FR-019**: Records of a type that is no longer registered MUST be listed in a table of the
  fields every record of that kind has.
- **FR-020**: The number of database queries a table issues MUST NOT grow with the number of rows
  it shows.
- **FR-021**: The way to move between types MUST be reachable and operable by keyboard and named
  for assistive technology.

**Measurements on a sample**

- **FR-022**: The tab MUST list every measurement made on the sample that the viewer may see,
  including those that belong to a different dataset than the sample.
- **FR-023**: Whether a measurement is shown MUST be decided by the dataset the measurement belongs
  to. Being on the sample's dataset team MUST NOT show a measurement in a dataset the viewer may not
  open.
- **FR-024**: All of the sample's measurements MUST be on one page, grouped by measurement type,
  each group in the table generated for its type.
- **FR-025**: A measurement that belongs to a different dataset than the sample MUST identify that
  dataset in its row and link to it.
- **FR-026**: A row MUST lead to that measurement's page.
- **FR-027**: The sample overview's way to the measurements it does not show MUST lead to this tab,
  and the tab MUST list as many measurements as the overview counts for the same viewer.
- **FR-028**: The number of database queries the tab issues MUST NOT grow with the number of
  measurements. It may grow with the number of measurement types shown.

**Projects and Datasets**

- **FR-029**: On a project, the Datasets tab MUST list the project's datasets that the viewer may
  open, and no others.
- **FR-030**: On a person, the Projects and Datasets tabs MUST list the public projects and public
  datasets the person is credited on, for every viewer, the person included.
- **FR-031**: On an organization, the Projects tab MUST list the public projects it owns or is
  credited on. The Datasets tab MUST list the public datasets it is credited on and the public
  datasets in the projects it owns. Neither MUST list a record twice.
- **FR-032**: A tab's search and orderings MUST be those the portal-wide list of the same kind of
  record offers, applied within the page's own records, and MUST be the same on every page that
  carries the tab.
- **FR-033**: Each entry MUST lead to that project's or dataset's page.
- **FR-034**: Whatever a tab offered before this feature for adding a record from the list, such as
  adding a dataset to a project, MUST still be offered to the people who may use it. This feature
  adds no new way to create a record.
- **FR-035**: Every link on an overview page that leads to a contributor's full list of projects or
  datasets MUST lead to these tabs.
- **FR-036**: The project's Export tab MUST be removed, and its address MUST answer "not found".
  This feature MUST NOT add an export to any other page.
- **FR-037**: A project MUST NOT have a Samples or Measurements tab. A person and an organization
  MUST NOT have one either.

**Members**

- **FR-038**: The Members tab MUST list the organization's members: people with a verified
  affiliation to it that has not ended. Pending requests and former members MUST NOT be listed or
  counted.
- **FR-039**: The owner MUST come first, then the administrators, then the other members, each
  group by name. The owner and administrators MUST be marked, to sighted readers and to assistive
  technology.
- **FR-040**: A person MUST be listed once, whatever number of affiliations they have to the
  organization.
- **FR-041**: Each entry MUST lead to that person's page.
- **FR-042**: The list MUST page its results and MUST be searchable by name.
- **FR-043**: No email address MUST appear in the tab.
- **FR-044**: The organization overview's way to the members its card does not show MUST lead to
  this tab, in place of the notice that the full list is not available. The tab MUST NOT offer any
  way to add, change or remove a member.

**Across the feature**

- **FR-045**: Every piece of text the tabs show MUST be marked for translation, and dates and
  numbers MUST follow the active locale.
- **FR-046**: The development data MUST make every state in this specification reachable as a
  visitor or as one of the development accounts: a dataset with several sample and measurement
  types, a public dataset that is not published, an empty dataset, a sample measured in more than
  one dataset, a project with public and private datasets, and an organization with every kind of
  affiliation.
- **FR-047**: The documentation for portal developers MUST name each of the six plugins, say which
  pages it is registered on, and say where a list's columns, filters and search come from. The
  documentation for portal users MUST describe how to browse a dataset's samples and measurements
  and a sample's measurements. Any page that describes the project's Export tab MUST be corrected.

### Which story owns which requirement

| Story | Requirements |
|---|---|
| US-1: a dataset's samples and measurements, and the rules every tab shares | FR-001 to FR-021, FR-045 to FR-047 |
| US-2: a sample's measurements | FR-022 to FR-028 |
| US-3: Projects and Datasets, and the Export tab | FR-029 to FR-037 |
| US-4: an organization's members | FR-038 to FR-044 |

FR-001 to FR-007 describe every tab in this feature. US-1 puts them in place for the dataset's two
tabs, and each later story meets them for its own. Each later story also extends the development
data (FR-046) and the documentation (FR-047) for its own tabs.

### Key Entities

- **List tab**: A tab beside a record's overview that lists records of one kind related to that
  record. It is a plugin registered against the pages it appears on.
- **Type table**: The table FairDM generates for a registered sample or measurement type from its
  registration. The portal-wide listing of that type uses the same one.
- **A dataset's records**: The samples and measurements that belong to the dataset. A measurement
  belongs to its own dataset, which may differ from its sample's.
- **Member**: A person with a verified affiliation to an organization that has not ended. Owner and
  administrator are kinds of member.
- **Published**: A dataset whose data may be shown publicly. A visitor sees a dataset's samples and
  measurements only once it is published.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every tab in FR-001's table is on every page the table names and on no other page.
- **SC-002**: Each of the six lists is defined once. A change made to one of them is seen on every
  page that carries it, with no second place to change.
- **SC-003**: Signed in as each development account and as a visitor, no list tab names, counts or
  links a record that account may not see.
- **SC-004**: From a dataset's page, a reader reaches any one of its samples or measurements they
  may see without leaving that page's tabs. The same holds from a sample to its measurements and
  from an organization to its members.
- **SC-005**: A portal that registers a new sample or measurement type sees it in the dataset tabs
  with no template, view or address written for it.
- **SC-006**: The Datasets tab offers the same search and the same orderings on a project, a person
  and an organization, and the Projects tab the same on a person and an organization.
- **SC-007**: No project page has an Export tab.

## Assumptions

- Access to projects, datasets, samples and measurements follows the rules FairDM already enforces
  and specification 018 states: a sample follows its dataset, and a measurement follows its own
  dataset, not its sample's. This feature applies those rules to lists and does not change them.
- Contributor pages keep the rule specification 019 set: they name public projects and public
  datasets only, for every viewer.
- The type tables, their filters and their search are the ones specification 015 delivered for the
  portal-wide listings. This feature narrows them to one dataset or one sample and adds nothing to
  what a registration can declare.
- The tabs sit in the tab strip the plugin system already provides (specification 008). This
  feature needs nothing from the sibling features in #397. Where another feature adds a tab to the
  same page, such as Contributors, Map or Statistics, that tab comes after the list tabs.
- Out of scope, each owned elsewhere: an export or download on the dataset (#397), a data
  dictionary linked from the Samples and Measurements tabs (#397), the Contributors tab (#402), the
  Map tab (#405), the Statistics tabs (#406), page actions and overview cards contributed by plugins
  and removing or replacing a registered plugin (#401), managing an organization's members, and a
  Publications tab (#194).
- Charts, plots of one field against another and derived statistics over a sample's measurements
  are out of scope. Comparing across methods here means reading every method's results for one
  sample on one page.
