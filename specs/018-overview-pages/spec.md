# Feature Specification: One consistent overview page for projects, datasets, samples and measurements

**Feature Branch**: `018-overview-pages`

**Created**: 2026-09-25

**Status**: Draft

**Goals**: G5: a modern, extensible interface that every portal gets by default, with no frontend
work. G3: addons and community-specific views attach to the core models without changes to the
framework. G1: a core data model of projects, datasets, samples, measurements and contributors that
domain schemas can extend and rely on.

**Roadmap**: none. No roadmap item covers the overview pages. The access rules the pages obey are
R14's, and the plugin tab strip they sit in is R18's.

**Input**: Projects, datasets, samples and measurements each need an overview page, and the four
pages should read as a set. Four separate redesigns (#368, #369, #370, #371) worked out what each
page should say, but each one built its own header, side column, citation and people card. A reader
moving from a project to one of its measurements should find the same facts in the same places. A
portal developer should extend any of the four pages the same way. A sample or measurement type
should add its own content without the framework knowing about it. The four pages were then built
together as one working prototype on the branch `sketch/018-overview-pages` and reviewed page by
page. This specification describes the design that review settled on.

## Clarifications

### Session 2026-09-25

- Q: The four redesigns disagree on how a page is extended. The sample and measurement pages name
  their blocks after the record (`sample.cite`, `measurement.cite`), and the project and dataset
  pages have no blocks at all. Which scheme do the pages share? → A: One set of names on every page,
  under `overview.`: `overview.cite` means the same place on a project as on a measurement. A
  developer who has extended one page already knows how to extend the other three.
- Q: The side-column cards are built separately on each page. Where do the shared ones live? → A:
  As components under the `card` namespace, such as `c-card.citation` and `c-card.people`. A portal
  developer uses the same components to build a type's own cards, so they match the rest of the page.
- Q: Several parts of the pages stand in for capabilities FairDM does not have yet: a project's or
  dataset's map, a recent activity feed, publishing, importing data, and a full list of a sample's
  measurements. Do they ship? → A: Yes. They ship, with one treatment across all four pages that
  makes it plain they are not available yet. Nothing that stands in for a missing capability looks
  or behaves as if it works.
- Q: Projects, datasets and samples open their overview inside a tabbed detail view that plugins
  add pages to. The measurement page stands alone with no tabs. Does it stay that way? → A: No. The
  measurement page gets the same tab strip, so all four records look and extend alike, and a
  measurement plugin added later has somewhere to go. Hiding the strip when a record has only one
  tab is a separate piece of work.
- Q: A visitor opens a dataset that is public but not yet published. Should they see how many
  samples and measurements it holds? → A: Yes. The counts describe the dataset without revealing
  any of its data, and they tell a reuser that something is coming.
- Q: Each redesign shipped its own development data command, and each one created its own sign-in
  accounts. Which accounts does development data use? → A: Three accounts at `example.com`:
  `regular.user`, `staff.user` and `super.user`, each with the password `password`. The command
  creates them if they are missing and leaves them alone if they exist.
- Q: Projects and datasets have no subtypes. Do their pages look for a type's own template the way
  samples and measurements do? → A: No. A portal changes a project or dataset page by overriding
  the template in the usual way and filling the same `overview.` blocks. Choosing a template by
  record type exists for samples and measurements only, because those are the records portals
  subclass.
- Q: The schema.org description in the page head is read by machines, not people. Does it follow
  the same visibility rules as the page? → A: Yes. It carries nothing the viewer could not read on
  the page. On a public, unpublished dataset it names the variables measured but gives no values.
- Q: Are the pages translatable? → A: Yes. Every label, notice, status description and placeholder
  is marked for translation, like the rest of FairDM. Dates and numbers follow the active locale.

### Session 2026-09-29: review of the working prototype

- Q: What does the header say beneath the record's name? → A: The people behind the record, each
  with their avatar and name, linking to their page: a project's leaders and a dataset's creators.
  Samples and measurements have no such row. The parent records, dates and identifiers that sat
  there before now live in the side column only, so no fact is shown twice.
- Q: How are the side column's facts grouped? → A: One Details card holds what the record belongs
  to, its licence, its status and its dates, and how a machine reaches it. Every entry in it has
  the same layout. Identifiers, funding and the citation each have their own card. The entry that
  said who can see the data is gone: on a sample or measurement the licence implies it, and on a
  dataset the header's badges and notices already say it.
- Q: In what order do the side column's cards appear? → A: The readiness checklist (team only),
  Details, a dataset's timeline, then People, Identifiers, Funding and the citation, then cards
  particular to the record. Every page follows that order and leaves out what it does not have.
- Q: Who appears in the People card? → A: Everyone credited who is not already named in the header,
  as a grid of avatars. Each links to the contributor's page and shows their name on hover. After
  three rows the rest are counted, and the count links to the same full list as the card's own
  link. When everyone credited is already named in the header, the card is left out.
- Q: What replaces the dataset's per-type data tabs? → A: The same two charts the project page
  has: records by type, and how the number of samples and measurements grew over time. The row
  previews, field summaries and value ranges are gone from the page. An empty dataset shows its
  first-run state in their place.
- Q: Where do a dataset's key dates go? → A: A timeline card of its own in the side column:
  collected, added to the portal, submitted, published, available from and withdrawn, in the order
  they happened. The Details card keeps only when the record was last updated.
- Q: Does the dataset keep a versions card? → A: No. Versioning is not planned soon, so the page
  does not announce it.
- Q: How are a record's descriptions shown? → A: With more than one, the tabs stand in the card's
  header, and each tab's name is the heading. With one, its name is the card's title.
- Q: What is a sample's "custody" status? → A: It is the sample's status field (available, in use,
  stored, destroyed), and the page calls it by that field's name.
- Q: How does a sample show its measurements and related samples? → A: Measurements as one list,
  most recent first, each naming its type and marked when recorded in another dataset, with no
  tabs per type. Related samples go in the side column as one list, each entry saying how that
  sample relates to this one (parent sample or subsample).
- Q: Does a sample's location get a map? → A: Yes, an interactive map in the side column with the
  point marked and the coordinates listed with it. A measurement shows its sample's location on the
  same kind of map, when the sample has one and the viewer may see the sample.
- Q: Where does a measurement's "About this type" content go? → A: Into a dialog that opens from the
  type badge in the header, and the card is gone. A sample's type badge works the same way, since
  both read the same registry description. A type the registry does not describe has a plain badge.
- Q: How does a measurement show the sample it was made on? → A: As a smaller version of the
  sample's own header: its image or icon, type and status, name, local ID, dataset and keywords.
- Q: What do a measurement's breadcrumbs say? → A: The same as a sample's: the list of that kind of
  record, then this record. The trail no longer walks down through the project, dataset and sample,
  which the Details card already names.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A project's page tells a reuser, a citer and its team what they came for (Priority: P1)

Someone arrives at a project from a grant report or a paper. At the top they read what the project
is, its status, who leads it and its keywords, then four headline figures. The descriptions follow,
one tab per description type. The five most recently updated datasets are listed, each saying
whether it is published and which licence it carries. Two charts show what the project holds and how
it grew. Beside the content, the side column gives the facts a reuser checks before going further:
the details of the project (its organisation, status, the licences its datasets carry, its dates and
how far through its timeline it is), everyone else credited on it, its identifiers, who funded it,
and how to cite it. The project's team also sees a warning when the project is private, and a
checklist of what is still missing before the record is complete enough to be found and trusted,
each gap linking to where it is fixed.

This is the first page built on the shared page anatomy, so this story also delivers the anatomy
itself: the layout, the shared cards, the block names and the treatment for capabilities that are
not available yet.

**Why this priority**: The project page is the landing page people are sent to from outside the
portal. Every other page in this feature is built from what this story establishes.

**Independent Test**: Load development data, then open each seeded project as a visitor and as a
member of its team. Confirm what each sees, and that a visitor's figures, charts and licence
summary count only the datasets they may see.

**Acceptance Scenarios**:

1. **Given** a public project with public and private datasets, **When** a visitor opens it,
   **Then** the figures, the charts and the licence summary count the public datasets only, and no
   readiness checklist is shown.
2. **Given** the same project, **When** a member of its team opens it, **Then** the figures count
   every dataset, and the readiness checklist lists every missing item with a link to the page that
   fixes it where such a page exists.
3. **Given** a private project, **When** a member of its team opens it, **Then** a notice says the
   project is private.
4. **Given** a project whose status is "Searching for collaborators", **When** anyone opens it,
   **Then** a notice says so and names who to contact.
5. **Given** a project with leaders and other contributors, **When** it is opened, **Then** the
   header names the leaders, and the People card shows everyone else and not the leaders.
6. **Given** a project with more contributors than the People card shows, **When** it is opened,
   **Then** the card counts the rest and the count links to the full list of contributors.
7. **Given** a project with one, two and several creators, **When** the citation is shown, **Then**
   the creators are written in the citation style for each count.
8. **Given** a project with a start and end date, **When** it is opened before, during and after
   that period, **Then** its timeline in the Details card says where the project stands for each.
9. **Given** a project with funding, and one without, **When** each is opened by a visitor, **Then**
   the first shows its funding and the second shows no funding card. **When** a member of the team
   opens the second, **Then** the funding card says none is recorded.
10. **Given** any project, **When** its page is rendered, **Then** its schema.org description is in
    the page head.
11. **Given** a project with no datasets, **When** a member of its team opens it, **Then** the page
    shows the first-run state with a way to add a dataset, and no empty chart.

---

### User Story 2 - A dataset's page answers a reuser's questions in the order they ask them (Priority: P1)

A reuser opens a dataset and learns what it is, whether its data is published and under which
licence, who created it, what it holds and how it grew, when each step of its life happened, how to
cite it, and which publications relate to it. The header names its creators. Two charts show its
records by type and how the number of its samples and measurements grew. A timeline card in the side
column lists its key dates in the order they happened. Its related publications are worded from the
reader's side ("Describes this dataset"). Its team sees what still stands between the dataset and
publication.

**Why this priority**: The dataset is the unit a portal cites and distributes. It is the page a
reuser decides on.

**Independent Test**: Load development data. Open the published, the public-but-unpublished, the
private and the empty seeded datasets, each as a visitor and as a member of the team, and compare
what each sees against FR-022 and FR-024.

**Acceptance Scenarios**:

1. **Given** a public dataset that is not yet published, **When** a visitor opens it, **Then** they
   see its description, its figures including sample and measurement counts, and its charts, and a
   notice says its data is not published yet.
2. **Given** the same dataset, **When** a member of its team opens it, **Then** they also see the
   "Ready to publish?" checklist.
3. **Given** a published dataset, **When** a member of its team opens it, **Then** no readiness
   checklist is shown.
4. **Given** a dataset with a data publication set, **When** the citation is shown, **Then** it is
   that publication's citation. **Given** none, **Then** it is built from the dataset, with the year
   taken from the Published date, else the Available date, else the date the record was added.
5. **Given** a dataset holding samples or measurements, **When** it is opened, **Then** a chart of
   records by type is shown, and once its records span more than one month, a chart of how they
   grew.
6. **Given** a dataset holding no samples or measurements, **When** a member of its team opens it,
   **Then** the page shows the first-run state with a way to add data, and no empty chart.
7. **Given** a dataset holding a record type that is no longer registered, **When** it is opened,
   **Then** that type is left out and the page still renders.
8. **Given** a dataset with collection, submission, publication and availability dates, **When** its
   timeline is shown, **Then** those dates and the date it was added to the portal are listed in
   the order they happened.
9. **Given** a dataset with a Withdrawn date, **When** anyone opens it, **Then** a notice says it
   has been withdrawn, and the withdrawal is on its timeline.
10. **Given** a dataset with related publications, **When** they are listed, **Then** each relation
    is worded from the publication's side and the relations a reuser cares about most come first.
11. **Given** a dataset whose project the viewer may not see, **When** it is opened, **Then** the
    project is neither named nor linked.

---

### User Story 3 - A sample's page follows the specimen, and a sample type adds its own fields (Priority: P2)

A researcher opens a sample to decide whether to re-examine it or cite it. They see its type and its
status, and what that status means for re-examining it. They see a timeline of what happened to the
specimen: when it was collected, prepared and stored, by whom and how. They see the measurements
made on it, including measurements another team recorded in its own dataset. In the side column
they see where it sits (project and dataset), its licence, the people credited, its identifiers, a
citation in DataCite's form for a physical object, a map of where it was taken, and the samples it
is related to, each saying how. Opening the type badge shows what the registry says about that kind
of sample. A portal that defines a rock sample type adds a card of rock properties and a rock-type
badge by providing one template. It fills the blocks it wants and keeps everything else.

**Why this priority**: Samples are the first record type portals extend. This story proves the
extension works on a subclassed record.

**Independent Test**: Load development data. Open each seeded sample as a visitor and as a member of
its dataset's team. Open a rock sample and a sample type with no template of its own and compare.

**Acceptance Scenarios**:

1. **Given** a sample type that provides its own overview template, **When** one of its samples is
   opened, **Then** the page uses that template, and the blocks it did not fill show the shared
   content.
2. **Given** a subtype of that sample type with no template of its own, **When** one of its samples
   is opened, **Then** its parent type's template is used.
3. **Given** a sample type with no template of its own anywhere in its ancestry, **When** one of its
   samples is opened, **Then** the shared page is used.
4. **Given** a sample whose dataset is published, **When** a visitor opens it, **Then** the page
   opens.
5. **Given** a sample whose dataset is private, or public but unpublished, **When** a visitor opens
   it, **Then** they get a "not found" response. **When** a member of the dataset's team opens it,
   **Then** the page opens.
6. **Given** a sample with measurements recorded in another team's unpublished dataset, **When** a
   visitor opens it, **Then** those measurements are not listed.
7. **Given** a sample with more measurements than the list shows, **When** it is opened, **Then**
   the list shows the most recent and counts the rest.
8. **Given** a sample with parent samples and subsamples, some in unpublished datasets, **When** a
   visitor opens it, **Then** the visible ones are listed together, each saying how it relates to
   this sample, and the hidden ones are counted without being named or linked.
9. **Given** a sample with collection, preparation and storage steps, some dated only to the year or
   the month, **When** its timeline is shown, **Then** the steps are in date order and each date is
   shown as precisely as it was recorded.
10. **Given** a sample with a location, **When** it is opened, **Then** a map shows the point and
    the coordinates are listed. **Given** one without, **Then** the page says no location is
    recorded.
11. **Given** a sample whose type the registry describes, **When** the type badge is activated,
    **Then** a dialog shows the registry's description of the type. **Given** a type the registry
    does not describe, **Then** the badge opens nothing.
12. **Given** a destroyed sample, **When** anyone opens it, **Then** a notice says the specimen no
    longer exists and that its record and measurements are kept.

---

### User Story 4 - A measurement's page shows the result and how it was obtained, and a measurement type adds its own (Priority: P2)

A researcher opens a measurement to judge whether its value is comparable with theirs. They see the
result, and the type badge opens what the registry says about this kind of measurement and the
protocol it follows. They see how this one was made: set up, measured and taken down, by whom. They
see the sample it was made on, laid out like a small version of the sample's own header, even when
the sample sits in another team's dataset, and the other measurements on the same sample. When the
sample has a location, the side column maps it. A citation is offered, and where the measurement has
no DOI of its own the page suggests citing its dataset. The page sits in the same tabbed detail view
as the other three records. A portal that defines an XRF measurement type shows its element and
concentration in place of a single value by providing one template.

**Why this priority**: Measurements are the other record type portals extend. The page depends on
the anatomy and cards from US-1 and on the extension mechanism from US-3.

**Independent Test**: Load development data. Open each seeded measurement as a visitor and as a
member of its dataset's team, including the one recorded in a different dataset from its sample.

**Acceptance Scenarios**:

1. **Given** any measurement, **When** it is opened at its permanent address, **Then** it shows in
   the same tabbed detail view as projects, datasets and samples, with the overview as its first tab.
2. **Given** a measurement type that provides its own overview template, a subtype without one, and
   a type with none in its ancestry, **When** a measurement of each is opened, **Then** the template
   is chosen the same way as for samples.
3. **Given** a measurement whose own dataset is published, **When** a visitor opens it, **Then** the
   page opens, whatever the state of its sample's dataset.
4. **Given** a measurement whose own dataset is private, or public but unpublished, **When** a
   visitor opens it, **Then** they get a "not found" response.
5. **Given** a measurement whose sample's dataset is not published, **When** a visitor opens it,
   **Then** the sample is described as an unpublished sample and is neither named nor linked, and
   no map of its location is shown.
6. **Given** a measurement whose sample has a location and may be seen, **When** it is opened,
   **Then** a map shows the sample's location. **Given** a sample with no location, **Then** no map
   is shown.
7. **Given** a measurement type that declares a value, **When** the page is shown, **Then** the
   result is shown with its uncertainty where there is one. **Given** a type that declares no value,
   **Then** the result area is left for the type to fill.
8. **Given** a measurement whose type the registry describes, **When** the type badge is activated,
   **Then** a dialog shows the type's description, keywords, the schema's maintainer and the
   protocol citation, whichever of those the registry has.
9. **Given** a measurement with other measurements on the same sample, some in unpublished datasets,
   **When** a visitor opens it, **Then** only the published ones are listed.
10. **Given** any measurement, **When** it is opened, **Then** the breadcrumbs lead from the list of
    measurements to this measurement, as a sample's lead from the list of samples.

---

### Edge Cases

- A record with none of the optional metadata filled in shows the first-run state on every page. A
  card with nothing to show is either left out or says what is missing, never left blank.
- A contributor credited on a record may be a person or an organisation. Citations, the header's
  people and the People card handle both.
- Everyone credited on a project may be one of its leaders. The People card is then left out rather
  than shown empty.
- A creator's name may be very long, and so may a record's title. Neither breaks the header or the
  side column at any breakpoint.
- A sample's status is stored as a vocabulary concept. The page reads its label wherever the status
  comes from, and says when no status is recorded.
- A private record is never confirmed to exist. A viewer who may not see it gets the same "not
  found" response as for a record that does not exist.
- The charting or map library fails to load in the browser. The page still reads, each chart's text
  alternative still says what the chart shows, and the coordinates are still listed with the map.

## Requirements *(mandatory)*

### Functional Requirements

**The shared page anatomy**

- **FR-001**: Every overview page MUST have, in order: a header, notices, a figures strip, and then
  a wide content column beside a narrow side column. Below the `lg` breakpoint the two columns MUST
  stack with the content first.
- **FR-002**: The header on every page MUST carry the record's image or icon, its badges, its name,
  the people behind it where the record names any (FR-025, FR-030), its keywords and its actions, in
  the same arrangement. Each person named there MUST link to their page.
- **FR-003**: The side column on every page MUST present its cards in this order, leaving out any
  that do not apply to the record:
  1. the readiness checklist (team only, and only where the record has one)
  2. Details
  3. the record's timeline of key dates, where it has one
  4. People
  5. Identifiers
  6. Funding
  7. the citation
  8. cards particular to the record (related publications, location, related samples)
- **FR-004**: Each shared card MUST be one component under the `card` namespace, used by every page
  that shows that card, and usable by a portal developer in a type's own template. The shared cards
  are the readiness checklist, Details, the timeline, People, Identifiers, Funding, the citation,
  descriptions, location, and the placeholder for a capability that is not available yet.
- **FR-005**: Every page MUST expose the same named blocks under the `overview.` prefix for the
  header's image, badges, people, keywords and actions, the notices, the figures, the wide column,
  the side column, and each card in the side column. A block that means the same thing on two pages
  MUST have the same name on both.
- **FR-006**: Blocks that only one kind of record needs, such as the type's own fields on a sample
  or measurement, MUST also sit under the `overview.` prefix.
- **FR-007**: A block that wraps other blocks MUST let a template add to it and keep its existing
  content, as well as replace it.
- **FR-008**: The list of blocks, in page order, with what each holds, MUST be documented for portal
  developers, together with a worked example of extending a page.
- **FR-009**: The overview MUST be the first tab of the record's tabbed detail view for all four
  record types.

**The shared cards**

- **FR-010**: The Details card MUST hold, as entries of one layout: the records this one belongs to
  (linked, and left out when the viewer may not see them), its licence (linked to the licence's
  text, or saying none is chosen), its status where it has one, its dates, and how a machine reaches
  it (its API address, and metadata downloads as not yet available). A record MAY add entries of the
  same layout.
- **FR-011**: The People card MUST show everyone credited on the record who is not already named in
  the header. Each MUST link to the contributor's page, and their name MUST be available on hover and
  to assistive technology. It MUST show at most eighteen, then count the rest, with a link to the
  full list of contributors where the record has one. It MUST be left out when nobody remains to
  show.
- **FR-012**: The Identifiers card MUST list every identifier the record carries, the team's own ID
  where there is one, and the record's portal ID with a way to copy it. DOIs and IGSNs MUST link to
  their resolver.
- **FR-013**: The Funding card MUST list each award with its funder, title and number, linked where
  the award records a link. It MUST be shown on records that carry funding, and to the team as an
  empty state when none is recorded.
- **FR-014**: The citation card MUST give the record's citation with a way to copy it, and say when
  the citation points at the page because the record has no DOI.
- **FR-015**: The descriptions card MUST show each description the record has, the abstract first.
  With more than one, each MUST be reachable from a tab in the card's header. With none, it MUST
  show the record's first-run state.

**Capabilities that are not available yet**

- **FR-016**: The pages MUST ship with these capabilities shown as not yet available: the map of a
  project's or dataset's samples, recent activity, publishing a dataset, importing data, the full
  list of a sample's measurements, exporting a citation, and metadata downloads.
- **FR-017**: Each item in FR-016 MUST share one treatment across all four pages. It MUST say that
  the capability is not available yet, and it MUST NOT look or behave as if it works. A button
  standing in for a missing action MUST be disabled and say why.

**Who sees what**

- **FR-018**: A project or dataset a viewer may not see MUST answer "not found".
- **FR-019**: A sample MUST follow its dataset. Its page opens for everyone once that dataset is
  published, and otherwise only for the dataset's team. Anyone else MUST get "not found".
- **FR-020**: A measurement MUST follow its own dataset, not its sample's. The rule is otherwise the
  same as FR-019.
- **FR-021**: On a project, a visitor's figures, charts and licence summary MUST count only the
  datasets that visitor may see.
- **FR-022**: On a public, unpublished dataset, a visitor MUST see its description, its figures
  (including sample and measurement counts) and its charts, and none of its records.
- **FR-023**: Wherever a page lists, links or maps records from another dataset (measurements on a
  sample, related samples, other measurements on the same sample, the sample a measurement was made
  on and its location), it MUST show a visitor only records whose own dataset is published. The
  team of that dataset sees them all. Where a record cannot be shown, the page MUST describe or
  count it without naming, linking or mapping it.
- **FR-024**: A readiness checklist MUST be shown only to the record's team, and on a dataset only
  until it is published.

**The project page**

- **FR-025**: The project page's header MUST carry its status and, when private, its visibility as
  badges, name its leaders, and offer Cite, Share, Add dataset and a Manage menu as actions.
- **FR-026**: Its figures MUST be datasets, samples, measurements and contributors.
- **FR-027**: Its content column MUST carry the descriptions card, the five most recently updated
  datasets (each saying whether it is published, its licence, its record counts and its last
  update, with a way to the full list), a chart of records by type, a chart of the running total of
  samples and measurements by month, and the map and recent activity as not yet available.
- **FR-028**: Its side column MUST carry the readiness checklist of ten items taken from DataCite's
  required and recommended properties, and a Details card holding its organisation, status, the
  licences of its datasets, when it was added and last updated, and its timeline from start to end
  with how far through it the project is. People, Identifiers, Funding and the citation follow.
- **FR-029**: The page head MUST carry the project's schema.org description.

**The dataset page**

- **FR-030**: The dataset page's header MUST carry whether it is published, public or private, and
  its licence, as badges, and name its creators.
- **FR-031**: Its figures MUST be samples, measurements, contributors and related publications.
- **FR-032**: Its content column MUST carry the descriptions card, a chart of records by type, a
  chart of the running total of samples and measurements by month, and the map as not yet
  available. An empty dataset MUST show its first-run state in place of the charts.
- **FR-033**: Its side column MUST carry the "Ready to publish?" checklist of seven required and
  three recommended items, a Details card holding its project (with how many other datasets the
  project has), its licence and when it was last updated, and a timeline card of its key dates:
  collected, added to the portal, submitted, published, available from and withdrawn, in the order
  they happened. People, Identifiers and the citation follow, then related publications worded
  from the publication's side.
- **FR-034**: The page head MUST carry a schema.org `Dataset` description including the variables
  measured.

**The sample page**

- **FR-035**: The sample page MUST read only the base `Sample` model and what the registry says
  about the sample's type.
- **FR-036**: Its header MUST carry the type and the status as badges. Where the registry describes
  the type, the type badge MUST open that description in a dialog. Its figures MUST be
  measurements, related samples and people credited.
- **FR-037**: Its content column MUST carry, in order: the type's own fields (left empty for the
  type to fill), notes, the history timeline, and the measurements made on it as one list, most
  recent first, each naming its type and marked when recorded in another dataset.
- **FR-038**: The history timeline MUST join the sample's dates, contributor roles and descriptions
  for each step in the specimen's life into one entry per step, in date order, showing each date as
  precisely as it was recorded.
- **FR-039**: Its side column MUST carry a Details card holding its project, dataset, licence, status
  with what it means for re-examining the specimen, and when it was added and last updated. People,
  Identifiers and the citation (in DataCite's form for a physical object, with the IGSN where there
  is one) follow, then its location on a map with its coordinates, then its related samples as one
  list, each saying how it relates to this sample.

**The measurement page**

- **FR-040**: The measurement page MUST read only the base `Measurement` model and what the registry
  says about the measurement's type.
- **FR-041**: The measurement page MUST stay at the measurement's permanent address,
  `/measurement/<uuid>/`.
- **FR-042**: Where the type declares a value, the page MUST show the result, with its uncertainty
  where there is one, in the figures strip's place.
- **FR-043**: Its header MUST carry the type as a badge. Where the registry describes the type, the
  badge MUST open that description, its keywords, the schema's maintainer and the protocol citation
  in a dialog.
- **FR-044**: Its content column MUST carry, in order: the type's own fields (left empty for the
  type to fill), the procedure timeline, notes, the sample it was made on (with its image or icon,
  type, status, name, local ID, dataset and keywords), and up to eight other measurements on the
  same sample.
- **FR-045**: The procedure timeline MUST follow the same rules as FR-038, for set-up, measurement
  and take-down.
- **FR-046**: Its side column MUST carry a Details card holding its project, dataset, licence, and
  when it was added and last updated. People, Identifiers and the citation (suggesting the dataset
  instead when the measurement has no DOI) follow, then its sample's location on a map where the
  sample has one and may be seen.
- **FR-047**: Its breadcrumbs MUST lead from the list of measurements to the measurement, the same
  way a sample's do.

**Extending a sample or measurement page by type**

- **FR-048**: The page for a sample or measurement MUST use the template belonging to the record's
  own type when one exists, then the nearest ancestor type's, then the shared page.
- **FR-049**: A type's template MUST be found by a naming convention alone
  (`<app_label>/<model_name>_overview.html`), with no registration step.
- **FR-050**: The demo application MUST include one sample type and one measurement type that
  extend their pages, and one of each that does not.

**Development data**

- **FR-051**: One command MUST load development data that reaches every state described in this
  specification, on all four pages, including contributors credited with each role the pages read.
- **FR-052**: The command MUST create, when they are missing, three development accounts:
  `regular.user@example.com`, `staff.user@example.com` and `super.user@example.com`, each with the
  password `password`. `staff.user` MUST be on the team of the seeded records that have one, and
  `regular.user` MUST be on none.
- **FR-053**: The command MUST be safe to run again, replacing only the records it created.

**Documentation**

- **FR-054**: The portal developer documentation MUST describe the four overview pages, the shared
  cards, the block list, and how a sample or measurement type provides its own template.
- **FR-055**: The changelog MUST record the new pages and the new way to extend them.

**Metadata in the page head, and language**

- **FR-056**: The schema.org description in a page's head MUST carry nothing the viewer could not
  read on the page itself.
- **FR-057**: Every piece of text the pages show MUST be marked for translation, and dates and
  numbers MUST follow the active locale.

### Which story owns which requirement

| Story | Requirements |
|---|---|
| US-1: the project page, and the shared anatomy | FR-001 to FR-018, FR-021, FR-024 to FR-029, FR-051 to FR-057 |
| US-2: the dataset page | FR-022, FR-030 to FR-034 |
| US-3: the sample page, and extending by type | FR-019, FR-023, FR-035 to FR-039, FR-048 to FR-050 |
| US-4: the measurement page | FR-020, FR-040 to FR-047 |

Each later story extends the development data (FR-051) and the documentation (FR-054) for its own
page, and uses the anatomy, cards and blocks from US-1 without redefining them.

### Key entities

- **Overview page**: The first tab of a project's, dataset's, sample's or measurement's detail
  view. It describes the record to someone deciding whether to reuse, cite or complete it.
- **Card**: One box on an overview page, such as Details or the citation. A shared card is one
  component and looks and behaves the same on every page.
- **Overview block**: A named part of an overview page (`overview.cite`, `overview.people`) that a
  template can add to or replace.
- **Type template**: A sample or measurement type's own overview template. It extends the shared
  page and is found by its name.
- **Readiness checklist**: The list, shown to a record's team, of metadata still missing before the
  record is complete enough to be found and trusted (projects) or to be published (datasets).
- **The team**: The people who may change a record. For a sample or measurement, the team of its
  dataset.
- **Published**: A dataset whose data may be shown publicly. Publishing a dataset makes it public,
  so a published dataset is never private. A visitor sees a dataset's samples and measurements only
  once it is published.
- **Status (of a sample)**: The sample's status field: whether the specimen is available, in use,
  stored or destroyed.

## Success Criteria *(mandatory)*

### Measurable outcomes

- **SC-001**: The same fact (details, people, identifiers, citation) sits in the same position and
  is drawn by the same component on all four overview pages.
- **SC-002**: A portal developer adds a card to a sample type's page, and changes its badges, with
  one template and no Python.
- **SC-003**: No visitor is shown a count, chart, record, location or link that depends on data they
  are not allowed to see, other than the sample and measurement counts and charts of a public,
  unpublished dataset.
- **SC-004**: A private record, or one in an unpublished dataset, answers "not found" to a visitor on
  every page, and the response is the same as for a record that does not exist.
- **SC-005**: Every capability that is not available yet is announced as such, and no button on any
  overview page does nothing when pressed.
- **SC-006**: The tabs, charts, dialogs, menus, maps, avatar grid and timelines on all four pages
  meet WCAG 2.2 AA: keyboard reachable, named for assistive technology, and not relying on colour
  alone. Each chart and map has a text alternative.
- **SC-007**: After loading development data, every state in this specification is reachable by
  signing in as one of the three development accounts or as a visitor.

## Assumptions

- The content of each page is the design settled in review of the working prototype on
  `sketch/018-overview-pages`. Where it differs from the four redesigns (#368, #369, #370, #371),
  the prototype's design applies.
- Access to projects and datasets follows the rules FairDM already enforces. The rules for samples
  and measurements in FR-019 and FR-020 apply the same principle one level down.
- The components the pages need that django-mvp does not ship yet (statistics strip, list, tabs,
  progress) live in FairDM for now.
- Charts are drawn with django-mvp-charts and take their colours from the active theme. Maps are
  drawn with MapLibre GL on openly licensed tiles that need no key.
- Out of scope, each to be filed as its own issue: carrying units explicitly in the registry,
  letting a measurement type opt out of its own page, schema.org metadata for samples, hiding the
  tab strip when a record has only one tab, and showing the project image more prominently (#377).
- A published dataset is always public, because publishing makes it public. The code does not
  enforce that yet. Enforcing it belongs to the checked publication process (R22), not to these
  pages.
- The fix links missing from the readiness checklists (keywords, funding, creators, contact person,
  related publications) stay missing until pages to edit those exist.
