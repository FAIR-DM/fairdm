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
pages should read as a set. Four separate redesigns (#368, #369, #370, #371) got the content of each page
right, but each one built its own header, side column, citation and people card. A reader moving
from a project to one of its measurements should find the same facts in the same places. A portal
developer should extend any of the four pages the same way. A sample or measurement type should add
its own content without the framework knowing about it.

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
- Q: Several parts of the pages stand in for capabilities FairDM does not have yet: maps, a recent
  activity feed, versions, publishing, importing data, and a full list of rows. Do they ship? → A:
  Yes. They ship, with one treatment across all four pages that makes it plain they are not
  available yet. Nothing that stands in for a missing capability looks or behaves as if it works.
- Q: Projects, datasets and samples open their overview inside a tabbed detail view that plugins
  add pages to. The measurement page stands alone with no tabs. Does it stay that way? → A: No. The
  measurement page gets the same tab strip, so all four records look and extend alike, and a
  measurement plugin added later has somewhere to go. Hiding the strip when a record has only one
  tab is a separate piece of work.
- Q: A visitor opens a dataset that is public but not yet published. They cannot see its rows.
  Should they see how many samples and measurements it holds? → A: Yes. The counts describe the
  dataset without revealing any of its data, and they tell a reuser that something is coming.
- Q: Each redesign shipped its own development data command, and each one created its own sign-in
  accounts. Which accounts does development data use? → A: Three accounts at `example.com`:
  `regular.user`, `staff.user` and `super.user`, each with the password `password`. These are the
  development sign-ins used across the maintainer's other projects, and FairDM will follow them. The
  command creates them if they are missing and leaves them alone if they exist.
- Q: Projects and datasets have no subtypes. Do their pages look for a type's own template the way
  samples and measurements do? → A: No. A portal changes a project or dataset page by overriding
  the template in the usual way and filling the same `overview.` blocks. Choosing a template by
  record type exists for samples and measurements only, because those are the records portals
  subclass.
- Q: The schema.org description in the page head is read by machines, not people. Does it follow
  the same visibility rules as the page? → A: Yes. It carries nothing the viewer could not read on
  the page. On a public, unpublished dataset it names the variables measured but gives no value
  ranges.
- Q: The redesigns write their text in English. Are the pages translatable? → A: Yes. Every label,
  notice, status description and placeholder is marked for translation, like the rest of FairDM.
  Dates and numbers follow the active locale.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A project's page tells a reuser, a citer and its team what they came for (Priority: P1)

Someone arrives at a project from a grant report or a paper. At the top they read what the project
is, its status and its keywords, then four headline figures. Beside the content they find the facts
a reuser checks before going further: how to cite it, its identifiers, the licences its public
datasets carry, who is behind it and who funded it. The five most recently updated datasets are
listed, each with its access state and licence written out. Two charts show what the project holds
and how it grew. The project's team sees all of that plus the private parts: a warning that the
project is private, the public and private split of its figures, and a checklist of what is still
missing before the record is complete enough to be found and trusted, each gap linking to where it
is fixed.

This is the first page built on the shared page anatomy, so this story also delivers the anatomy
itself: the layout, the shared cards, the block names and the treatment for capabilities that are
not available yet.

**Why this priority**: The project page is the landing page people are sent to from outside the
portal. Every other page in this feature is built from what this story establishes.

**Independent Test**: Load development data, then open each seeded project as a visitor and as a
member of its team. Confirm what each sees, and that a visitor's figures, charts and licence
summary count public datasets only.

**Acceptance Scenarios**:

1. **Given** a public project with public and private datasets, **When** a visitor opens it,
   **Then** the figures, the charts and the licence summary count the public datasets only, and no
   readiness checklist is shown.
2. **Given** the same project, **When** a member of its team opens it, **Then** the figures show
   the public and private split, and the readiness checklist lists every missing item with a link to
   the page that fixes it where such a page exists.
3. **Given** a private project, **When** a member of its team opens it, **Then** a notice says the
   project is private.
4. **Given** a project whose status is "Searching for collaborators", **When** anyone opens it,
   **Then** a notice says so and names the contact person.
5. **Given** a project with one, two and several creators, **When** the citation is shown, **Then**
   the creators are written in the citation style for each count.
6. **Given** a project with a start and end date, **When** it is opened before, during and after
   that period, **Then** the timeline reads correctly for each ("Year 3 of 4" during it).
7. **Given** any project, **When** its page is rendered, **Then** its schema.org description is in
   the page head.
8. **Given** a project with no datasets, **When** a member of its team opens it, **Then** the page
   shows the first-run state with a way to add a dataset, and no empty chart.

---

### User Story 2 - A dataset's page answers a reuser's questions in the order they ask them (Priority: P1)

A reuser opens a dataset and learns in order: what it is and whether its data is published, the
licence, what the data looks like and what each field means, how to cite it, and who made it. A
dataset has no page of its own for its samples or measurements, so its overview carries the data:
one tab per record type present, each with the type's description, a preview of the first rows, and
a summary of every field's meaning, kind, unit and the range of values the dataset spans. The
dataset's related publications are worded from the reader's side ("Describes this dataset"). Its
team sees what still stands between the dataset and publication.

**Why this priority**: The dataset is the unit a portal cites and distributes. It is the page a
reuser decides on.

**Independent Test**: Load development data. Open the published, the public-but-unpublished, the
private and the empty seeded datasets, each as a visitor and as a member of the team, and compare
what each sees against FR-016 and FR-018.

**Acceptance Scenarios**:

1. **Given** a published dataset, **When** a visitor opens it, **Then** they see its preview rows
   and value ranges for every record type present, and no readiness checklist.
2. **Given** a public dataset that is not yet published, **When** a visitor opens it, **Then** they
   see its description, its figures including sample and measurement counts, and each field's
   meaning, and they see no preview rows and no value ranges.
3. **Given** the same dataset, **When** a member of its team opens it, **Then** they see everything,
   plus the "Ready to publish?" checklist.
4. **Given** a published dataset, **When** a member of its team opens it, **Then** no readiness
   checklist is shown.
5. **Given** a dataset with a data publication set, **When** the citation is shown, **Then** it is
   that publication's citation. **Given** none, **Then** it is built from the dataset, with the year
   taken from the Published date, else the Available date, else the date the record was added.
6. **Given** a dataset holding more than one record type, **When** it is opened, **Then** a chart of
   records by type is shown. **Given** one type only, **Then** no chart is shown.
7. **Given** a dataset holding a record type that is no longer registered, **When** it is opened,
   **Then** that type is left out and the page still renders.
8. **Given** a dataset with a Withdrawn date, **When** anyone opens it, **Then** a notice says it
   has been withdrawn.
9. **Given** a dataset with related publications, **When** they are listed, **Then** each relation
   is worded from the publication's side and the relations a reuser cares about most come first.

---

### User Story 3 - A sample's page follows the specimen, and a sample type adds its own fields (Priority: P2)

A researcher opens a sample to decide whether to re-examine it or cite it. They see its custody
status and what that means for re-examining it, and a timeline of what happened to the specimen:
when it was collected, prepared and stored, by whom and how. They see the measurements made on it,
grouped by type, including measurements another team recorded in its own dataset. They see the
samples it was taken from and its subsamples, where it came from, and a citation in DataCite's form
for a physical object. A portal that defines a rock sample type adds a card of rock properties and a
rock-type badge by providing one template. It fills the blocks it wants and keeps everything else.

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
4. **Given** a sample whose dataset is public and published, **When** a visitor opens it, **Then**
   the page opens.
5. **Given** a sample whose dataset is private, or public but unpublished, **When** a visitor opens
   it, **Then** they get a "not found" response. **When** a member of the dataset's team opens it,
   **Then** the page opens.
6. **Given** a sample with measurements recorded in another team's unpublished dataset, **When** a
   visitor opens it, **Then** those measurements are not listed.
7. **Given** a sample with collection, preparation and storage steps, some dated only to the year or
   the month, **When** its timeline is shown, **Then** the steps are in date order and each date is
   shown as precisely as it was recorded.
8. **Given** a destroyed sample, **When** anyone opens it, **Then** a notice says the specimen no
   longer exists and that its record and measurements are kept.

---

### User Story 4 - A measurement's page shows the result and how it was obtained, and a measurement type adds its own (Priority: P2)

A researcher opens a measurement to judge whether its value is comparable with theirs. They see the
result, what kind of measurement it is and the protocol it follows, and how this one was made: set
up, measured and taken down, by whom. They see the sample it was made on, even when the sample sits
in another team's dataset, and the other measurements on the same sample. A citation is offered, and
where the measurement has no DOI of its own the page suggests citing its dataset. The page sits in
the same tabbed detail view as the other three records. A portal that defines an XRF measurement
type shows its element and concentration in place of a single value by providing one template.

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
3. **Given** a measurement whose own dataset is public and published, **When** a visitor opens it,
   **Then** the page opens, whatever the state of its sample's dataset.
4. **Given** a measurement whose own dataset is private, or public but unpublished, **When** a
   visitor opens it, **Then** they get a "not found" response.
5. **Given** a measurement whose sample's dataset is not published, **When** a visitor opens it,
   **Then** the sample is described as an unpublished sample, and is neither named nor
   linked.
6. **Given** a measurement type that declares a value, **When** the page is shown, **Then** the
   result is shown large with its uncertainty where there is one. **Given** a type that declares no
   value, **Then** the result area is left for the type to fill.
7. **Given** a measurement with other measurements on the same sample, some in unpublished datasets,
   **When** a visitor opens it, **Then** only the published ones are listed.
8. **Given** a measurement in a dataset with a project, and one without, **When** each is opened,
   **Then** the breadcrumbs read project, dataset, sample, measurement, leaving out what is absent.

---

### Edge Cases

- A record with none of the optional metadata filled in shows the first-run state on every page. A
  card with nothing to show is either left out or says what is missing, never left blank.
- A contributor credited on a record may be a person or an organisation. Citations and people cards
  handle both.
- A creator's name may be very long, and so may a project's title. Neither breaks the header or the
  facts column at any breakpoint.
- A field summary meets a field whose unit FairDM cannot read. It shows a dash rather than guessing.
- A preview meets a table class that relies on the request or on ordering. It renders without
  sorting and without failing.
- A sample's or measurement's status is stored as a vocabulary concept. The page reads its label
  wherever the status comes from.
- A private record is never confirmed to exist. A viewer who may not see it gets the same "not
  found" response as for a record that does not exist.
- The charting library fails to load in the browser. The page still reads, and each chart's text
  alternative still says what the chart shows.

## Requirements *(mandatory)*

### Functional Requirements

**The shared page anatomy**

- **FR-001**: Every overview page MUST have, in order: a header, notices, a figures strip, and then
  a wide content column beside a narrow facts column. Below the `lg` breakpoint the two columns
  MUST stack with the content first.
- **FR-002**: The header on every page MUST carry the record's badges, its name, a line of facts
  placing it (its parent records, dates, identifiers), and its actions, in the same arrangement.
- **FR-003**: The facts column on every page MUST present its cards in this order, leaving out any
  that do not apply to the record:
  1. the readiness checklist (team only, and only where the record has one)
  2. the citation
  3. identifiers, licence and access
  4. the people credited
  5. cards particular to the record type (funding, related publications, versions)
  6. the parent record
  7. dates
- **FR-004**: Each of the cards in FR-003 MUST be one shared component under the `card` namespace
  (for example `c-card.citation` and `c-card.people`), used by every page that shows that card, and
  usable by a portal developer in a type's own template.
- **FR-005**: Every page MUST expose the same named blocks under the `overview.` prefix for the
  header's badges, facts and actions, the notices, the figures, the wide column, the facts column,
  and each card in the facts column. A block that means the same thing on two pages MUST have the
  same name on both.
- **FR-006**: Blocks that only one kind of record needs, such as the type's own fields on a sample
  or measurement, MUST also sit under the `overview.` prefix.
- **FR-007**: A block that wraps other blocks MUST let a template add to it and keep its existing
  content, as well as replace it.
- **FR-008**: The list of blocks, in page order, with what each holds, MUST be documented for portal
  developers, together with a worked example of extending a page.
- **FR-009**: The overview MUST be the first tab of the record's tabbed detail view for all four
  record types.

**Capabilities that are not available yet**

- **FR-010**: The pages MUST ship with these capabilities shown as not yet available: the map of
  locations, recent activity, versions, publishing, importing data, the full list of rows for a
  record type, citation formats, and metadata downloads.
- **FR-011**: Each item in FR-010 MUST share one visual treatment across all four pages. It MUST say
  that the capability is not available yet, and it MUST NOT look or behave as if it works. A button
  standing in for a missing action MUST be disabled and say why.

**Who sees what**

- **FR-012**: A project or dataset a viewer may not see MUST answer "not found".
- **FR-013**: A sample MUST follow its dataset. Its page opens for everyone once that dataset is
  public and published, and otherwise only for the dataset's team. Anyone else MUST get "not found".
- **FR-014**: A measurement MUST follow its own dataset, not its sample's. The rule is otherwise the
  same as FR-013.
- **FR-015**: On a project, a visitor's figures, charts and licence summary MUST count only the
  datasets that visitor may see.
- **FR-016**: On a public, unpublished dataset, a visitor MUST see its description, its figures
  (including sample and measurement counts) and each field's meaning. They MUST NOT see preview rows
  or value ranges.
- **FR-017**: Wherever a page lists or links records from another dataset (measurements on a sample,
  other measurements on the same sample, the sample a measurement was made on), it MUST show a
  visitor only records whose own dataset is public and published. The team of that dataset sees them
  all. Where the record cannot be shown, the
  page MUST describe it without naming or linking it.
- **FR-018**: A readiness checklist MUST be shown only to the record's team, and on a dataset only
  until it is published.

**The project page**

- **FR-019**: The project page's header MUST carry status and visibility, the owning organisation,
  dates, last update and keywords, with Cite, Share, Add dataset and a Manage menu as actions.
- **FR-020**: Its figures MUST be datasets, samples, measurements and contributors, each with a
  one-line qualifier.
- **FR-021**: Its content column MUST carry the descriptions (abstract first, every other type in
  its own tab), the five most recently updated datasets with access state, licence, record counts
  and last update written out, a chart of records by type, and a chart of the running total of
  records by month.
- **FR-022**: Its facts column MUST carry the readiness checklist of ten items taken from DataCite's
  required and recommended properties, the citation, identifiers and licence summary with an API
  link, the team (leaders and the contact person by name, everyone else as avatars with a count),
  funding, and the project's dates with its timeline.
- **FR-023**: The page head MUST carry the project's schema.org description.

**The dataset page**

- **FR-024**: The dataset page's header MUST carry the access state in words and the licence as
  badges, and "Part of" the project, the collection period, last update, creators and keywords.
- **FR-025**: Its figures MUST be samples and measurements (each with its number of types),
  contributors, and related publications.
- **FR-026**: Its content column MUST carry the descriptions in tabs (abstract first), and one tab
  per record type present, labelled with its count, holding the type's description, a preview of
  its first ten rows through the type's own table, and a field summary.
- **FR-027**: The field summary MUST show each field's meaning, kind and unit, and for numeric
  fields the range the dataset spans. It MUST leave out bookkeeping fields and columns that are not
  model fields.
- **FR-028**: Where the registry names who maintains a record type's structure, the tab MUST credit
  them with a way to cite it.
- **FR-029**: Its facts column MUST carry the "Ready to publish?" checklist of seven required and
  three recommended items, the citation, licence and access with identifiers and an API link, the
  people credited (creators, then the contact person, then everyone else with their roles), related
  publications worded from the publication's side, the parent project with its status and how many
  other datasets it has, versions, and the dataset's dates.
- **FR-030**: The page head MUST carry a schema.org `Dataset` description including the variables
  measured.

**The sample page**

- **FR-031**: The sample page MUST read only the base `Sample` model and what the registry says
  about the sample's type.
- **FR-032**: Its header MUST carry the type and the custody status as badges. Its figures MUST be
  measurements, related samples and people credited.
- **FR-033**: Its content column MUST carry, in order: the type's own fields (left empty for the
  type to fill), notes, the history timeline, measurements made on it grouped by type (five latest
  per type, each marked when recorded in another dataset), the samples it was taken from and its
  subsamples, and its location.
- **FR-034**: The history timeline MUST join the sample's dates, contributor roles and descriptions
  for each step in the specimen's life into one entry per step, in date order, showing each date as
  precisely as it was recorded.
- **FR-035**: Its facts column MUST carry the citation in DataCite's form for a physical object
  (with the IGSN where there is one), identifiers, the dataset and project with the licence labelled
  as coming from the dataset, the people credited, and the custody status with what it means and the
  record's dates.

**The measurement page**

- **FR-036**: The measurement page MUST read only the base `Measurement` model and what the registry
  says about the measurement's type.
- **FR-037**: The measurement page MUST stay at the measurement's permanent address,
  `/measurement/<uuid>/`.
- **FR-038**: Where the type declares a value, the page MUST show the result large, with its
  uncertainty where there is one, in the figures strip's place.
- **FR-039**: Its content column MUST carry, in order: the type's own fields (left empty for the
  type to fill), what kind of measurement it is from the registry (description, keywords, the
  schema's maintainer and the protocol citation), the procedure timeline, notes, the sample it was
  made on, and up to eight other measurements on the same sample.
- **FR-040**: The procedure timeline MUST follow the same rules as FR-034, for set-up, measurement
  and take-down.
- **FR-041**: Its facts column MUST carry the citation (suggesting the dataset instead when the
  measurement has no DOI), identifiers, the dataset and project with the licence labelled as coming
  from the dataset, the people credited, and the record's type and dates.

**Extending a sample or measurement page by type**

- **FR-042**: The page for a sample or measurement MUST use the template belonging to the record's
  own type when one exists, then the nearest ancestor type's, then the shared page.
- **FR-043**: A type's template MUST be found by a naming convention alone
  (`<app_label>/<model_name>_overview.html`), with no registration step.
- **FR-044**: The demo application MUST include one sample type and one measurement type that
  extend their pages, and one of each that does not.

**Development data**

- **FR-045**: One command MUST load development data that reaches every state described in this
  specification, on all four pages.
- **FR-046**: The command MUST create, when they are missing, three development accounts:
  `regular.user@example.com`, `staff.user@example.com` and `super.user@example.com`, each with the
  password `password`. `staff.user` MUST be on the team of the seeded records that have one, and
  `regular.user` MUST be on none.
- **FR-047**: The command MUST be safe to run again, replacing only the records it created.

**Documentation**

- **FR-048**: The portal developer documentation MUST describe the four overview pages, the shared
  cards, the block list, and how a sample or measurement type provides its own template.
- **FR-049**: The changelog MUST record the new pages and the new way to extend them.

**Metadata in the page head, and language**

- **FR-050**: The schema.org description in a page's head MUST carry nothing the viewer could not
  read on the page itself.
- **FR-051**: Every piece of text the pages show MUST be marked for translation, and dates and
  numbers MUST follow the active locale.

### Which story owns which requirement

| Story | Requirements |
|---|---|
| US-1: the project page, and the shared anatomy | FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-015, FR-018, FR-019, FR-020, FR-021, FR-022, FR-023, FR-045, FR-046, FR-047, FR-048, FR-049, FR-050, FR-051 |
| US-2: the dataset page | FR-016, FR-024, FR-025, FR-026, FR-027, FR-028, FR-029, FR-030 |
| US-3: the sample page, and extending by type | FR-013, FR-017, FR-031, FR-032, FR-033, FR-034, FR-035, FR-042, FR-043, FR-044 |
| US-4: the measurement page | FR-014, FR-036, FR-037, FR-038, FR-039, FR-040, FR-041 |

Each later story extends the development data (FR-045) and the documentation (FR-048) for its own
page, and uses the anatomy, cards and blocks from US-1 without redefining them.

### Key entities

- **Overview page**: The first tab of a project's, dataset's, sample's or measurement's detail
  view. It describes the record to someone deciding whether to reuse, cite or complete it.
- **Card**: One box in the facts column, such as the citation or the people credited. It is a
  shared component, and it looks and behaves the same on every page.
- **Overview block**: A named part of an overview page (`overview.cite`, `overview.people`) that a
  template can add to or replace.
- **Type template**: A sample or measurement type's own overview template. It extends the shared
  page and is found by its name.
- **Readiness checklist**: The list, shown to a record's team, of metadata still missing before the
  record is complete enough to be found and trusted (projects) or to be published (datasets).
- **The team**: The people who may change a record. For a sample or measurement, the team of its
  dataset.
- **Published**: A dataset whose data may be shown publicly. A visitor sees a dataset's samples
  and measurements only when it is both public and published. A private dataset hides everything
  beneath it, whether or not it is published.

## Success Criteria *(mandatory)*

### Measurable outcomes

- **SC-001**: The same fact (citation, identifiers, people, parent record, dates) sits in the same
  position and is drawn by the same component on all four overview pages.
- **SC-002**: A portal developer adds a card to a sample type's page, and changes its badges, with
  one template and no Python.
- **SC-003**: No visitor is shown a count, chart, row, value range or linked record that depends on
  data they are not allowed to see, other than the sample and measurement counts of a public,
  unpublished dataset.
- **SC-004**: A private record, or one in an unpublished dataset, answers "not found" to a visitor on
  every page, and the response is the same as for a record that does not exist.
- **SC-005**: Every capability that is not available yet is announced as such, and no button on any
  overview page does nothing when pressed.
- **SC-006**: The tabs, charts, disclosure sections, menus and timelines on all four pages meet WCAG
  2.2 AA: keyboard reachable, named for assistive technology, and not relying on colour alone. Each
  chart has a text alternative.
- **SC-007**: After loading development data, every state in this specification is reachable by
  signing in as one of the three development accounts or as a visitor.

## Assumptions

- The content of each page is the content approved on its redesign branch (#368, #369, #370, #371).
  This feature brings those pages together and makes them consistent. It does not redesign them.
- Access to projects and datasets follows the rules FairDM already enforces. The rules for samples
  and measurements in FR-013 and FR-014 apply the same principle one level down.
- The components the pages need that django-mvp does not ship yet (statistics strip, list, tabs,
  progress) live in FairDM for now.
- Charts are drawn with django-mvp-charts and take their colours from the active theme.
- Out of scope, each to be filed as its own issue: carrying units explicitly in the registry,
  letting a measurement type opt out of its own page, schema.org metadata for samples, and hiding
  the tab strip when a record has only one tab.
- The fix links missing from the readiness checklists (keywords, funding, creators, contact person,
  related publications) stay missing until pages to edit those exist.
