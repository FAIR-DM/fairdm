# Feature Specification: A basic map of sample locations on record and contributor pages

**Feature Branch**: `025-sample-location-map`

**Created**: 2026-10-02

**Status**: Draft

**Goals**: G5: a modern, extensible interface that every portal gets by default, with no frontend
work. G12: private and public data sit side by side, controlled per object.

**Roadmap**: none. No roadmap item covers a map. The feature is one of the ideas collected in #397
and was requested in #405.

**Input**: Samples carry a location, and nothing in the portal shows more than one of them on a
map. A sample's overview maps its own point, and the overviews of projects, datasets, people and
organizations each say that a map of samples is not available yet. The location app's only plugin
is an edit form registered against a point. FairDM should ship one basic map tab that plots sample
locations as points: a project's samples, a dataset's samples, the one sample on a sample's page,
and on a person's or an organization's page the samples in the datasets they are credited on. It
reads plain latitude and longitude, shows only what the viewer may see, and stays basic. It has no
settings and no hooks. A portal that wants something different overrides the tab's template, as it
would for any page.

## Clarifications

### Session 2026-10-02

The first five answers are the maintainer's, agreed while the request was written. The rest were
settled while writing this specification, and the reasoning behind each is in `decisions.md`.

- Q: Is this one map or five? → A: One plugin, registered on five pages. Each page gives it a
  different set of samples.
- Q: Does the map need a geospatial database? → A: No. It reads the latitude and longitude a
  location already stores as plain numbers, so dropping GeoDjango (#196) does not affect it.
- Q: How far does it go? → A: It stays basic. It plots points and has no settings or hooks. A
  portal that wants something different overrides the tab's template.
- Q: Which samples are plotted? → A: Only samples the viewer may see.
- Q: What happens to the location app's existing overview plugin? → A: It is retired.
- Q: On a person's or an organization's page, does a member of a private dataset's team see that
  dataset's samples on the map? → A: No. A contributor's page names only public projects and public
  datasets, for every viewer, and the map follows the same rule. Private work is mapped on the
  project's or the dataset's own page.
- Q: Which datasets count for a person or an organization? → A: The ones the contributor is
  credited on directly. A dataset reached only through a credit on its project, or through an
  organization owning the project, is not included.
- Q: What does the tab do when there is nothing to plot? → A: It is still offered, and the page
  says that none of the samples has a location. A tab that came and went with the data would break
  links to it.
- Q: What about samples with no location? → A: They are left off the map, and the page says how
  many samples are plotted and how many could not be.
- Q: What does a point lead to? → A: Selecting a point names the sample or samples at that location,
  with their type, and links to each sample's page.
- Q: The overviews of projects, datasets, people and organizations each show a map as not available
  yet. Do they change? → A: Yes. Those four placeholders are removed, because the map now exists
  beside the overview. The overview gains no map card of its own in this feature.
- Q: Does a measurement's page get the tab? → A: No. Its overview already maps its sample's
  location, and a measurement has no samples of its own to plot.
- Q: A location has a page of its own, reached from its coordinates. Does that change? → A: No.
  Only the plugin registered against a location is retired, and the address it answered at stops
  answering.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A visitor sees where a dataset's or a project's samples were taken (Priority: P1)

Someone deciding whether a dataset is useful to them wants to know where its samples come from. On
the dataset's page they open the map tab and see each located sample as a point, with the map
framed so that all the points are in view. The page tells them how many samples are on the map and
how many have no location. Selecting a point names the sample, says what type it is, and links to
its page. A project's page offers the same tab over the samples of all its datasets, and a sample's
page offers it for that one sample.

This story also delivers the plugin itself and the rule for what it may show, which the second
story reuses, and it retires the location app's old plugin.

**Why this priority**: A dataset is the unit a visitor judges for reuse, and where its samples were
taken is often the first thing they ask. The project and sample pages get the same tab from the
same work.

**Independent Test**: Load development data. Open the map tab on a dataset with located and
unlocated samples, on a project with a public and a private dataset, and on a sample with and
without a location, as a visitor and as a member of the private dataset's team. Compare the points
and the counts each viewer gets against FR-001 to FR-017.

**Acceptance Scenarios**:

1. **Given** a dataset whose samples all have locations, **When** a viewer who may open it opens
   the map tab, **Then** every sample is plotted and all the points are in view.
2. **Given** a dataset in which some samples have a location and some do not, **When** the map tab
   is opened, **Then** only the located samples are plotted, and the page states how many samples
   are plotted and how many have no location.
3. **Given** a dataset in which no sample has a location, or which has no samples, **When** the map
   tab is opened, **Then** the page says there is nothing to plot and no error is shown.
4. **Given** a plotted sample, **When** its point is selected, **Then** the sample is named with its
   type and a link leads to its page.
5. **Given** several samples recorded at the same location, **When** that point is selected,
   **Then** each of them is named and linked.
6. **Given** a project with one dataset the visitor may see and one they may not, **When** the
   visitor opens the project's map tab, **Then** only samples of the first dataset are plotted and
   counted, and the page carries nothing about the samples of the second.
7. **Given** the same project, **When** a member of the private dataset's team opens the map tab,
   **Then** the samples of both datasets are plotted.
8. **Given** a sample with a location, **When** its map tab is opened, **Then** that one sample is
   plotted. **Given** a sample without one, **Then** the page says it has no location.
9. **Given** a record the viewer may not open, **When** they request its map tab's address,
   **Then** the request is refused in the same way as the record itself.
10. **Given** samples of several sample types in one dataset, **When** the map tab is opened,
    **Then** samples of every type are plotted together.
11. **Given** a location whose coordinates are not a valid latitude and longitude, **When** the map
    tab is opened, **Then** that sample is not plotted and is counted with the samples that could
    not be.
12. **Given** a measurement, **When** its page is opened, **Then** no map tab is offered.
13. **Given** a project or a dataset, **When** its overview is opened, **Then** it no longer says
    that a map of its samples is not available yet.
14. **Given** a location, **When** the address of the retired location plugin is requested,
    **Then** it is not found, and the location's own page still opens.

---

### User Story 2 - A visitor sees where a person or an organization has worked (Priority: P2)

Someone reading a person's page wants to see the ground their work covers. They open the map tab
and see the samples of the public datasets that person is credited on. An organization's page does
the same for the datasets the organization is credited on. The page reads the same to the person
themself as to the visitor they send the link to.

**Why this priority**: It rests on the plugin from the first story and adds only a different set of
samples. A contributor's page is useful without it. A dataset's map is not something a visitor can
work out any other way.

**Independent Test**: Load development data. Open the map tab on a person and on an organization
credited on public and private datasets, on a contributor credited on nothing, and on one credited
only on a project. Open each as a visitor, as the person themself, and as a member of a private
dataset's team. Compare against FR-018 to FR-022.

**Acceptance Scenarios**:

1. **Given** a person credited on two public datasets with located samples, **When** anyone opens
   the map tab on their page, **Then** the located samples of both datasets are plotted.
2. **Given** a person credited on a public and a private dataset, **When** a visitor opens the map
   tab, **Then** only the public dataset's samples are plotted and counted.
3. **Given** the same person, **When** they open their own page, or a member of the private
   dataset's team opens it, **Then** the private dataset's samples are still not plotted.
4. **Given** a person credited on a public dataset inside a private project, **When** anyone opens
   the map tab, **Then** that dataset's samples are not plotted.
5. **Given** an organization credited on a public dataset, **When** anyone opens the map tab on its
   page, **Then** that dataset's located samples are plotted.
6. **Given** a contributor credited on a project and on none of its datasets, **When** the map tab
   is opened, **Then** the samples of that project's datasets are not plotted.
7. **Given** a contributor credited on no dataset, **When** the map tab is opened, **Then** the
   page says there is nothing to plot and no error is shown.
8. **Given** a person or an organization, **When** their overview is opened, **Then** it no longer
   says that a map of samples is not available yet, and an organization's overview still shows
   where the organization is based.

---

### Edge Cases

- A dataset may hold thousands of located samples. The map tab still opens and can be moved and
  zoomed.
- Many samples may share one location, for example cores taken at one site. They appear as one
  point that names all of them.
- All the plotted samples may sit at one location. The map still opens framed on that point at a
  scale where the surroundings can be recognised.
- Samples may lie on both sides of the 180th meridian or close to a pole. Every point is still
  plotted.
- A sample's measurement may belong to another dataset. The map is drawn from samples and their own
  datasets, so measurements do not change what is plotted.
- A sample in a public dataset whose project is private is hidden with its project, on every page.
- A portal may be configured to store coordinates in a reference system other than latitude and
  longitude. Locations whose numbers are not a valid latitude and longitude are not plotted, and
  the page counts them with the samples that could not be.
- The map library may fail to load in the browser. The page still reads, and the counts of plotted
  and unplotted samples are still shown.
- A record that does not exist answers "not found" on its map tab as on any other tab.

## Requirements *(mandatory)*

### Functional Requirements

**The map plugin**

- **FR-001**: FairDM MUST ship one map plugin and register it on the project, dataset, sample,
  person and organization pages, where it appears as a tab beside the overview. It MUST NOT be
  registered on the measurement page.
- **FR-002**: The map MUST plot each sample in its set that has a usable location as a point. What
  the set is depends on the page, as FR-009 to FR-011 and FR-018 to FR-020 state.
- **FR-003**: The map MUST read a location's stored latitude and longitude as plain numbers and
  MUST work on a database with no geospatial extension.
- **FR-004**: A location is usable when its latitude lies between -90 and 90 and its longitude
  between -180 and 180. A sample with no location, or with one that is not usable, MUST NOT be
  plotted.
- **FR-005**: The page MUST state, as text and not only on the map, how many samples are plotted
  and how many of the samples in the set could not be plotted. Both figures MUST be taken over the
  same set of samples as the points.
- **FR-006**: When the map opens, every plotted point MUST be in view.
- **FR-007**: Selecting a point MUST name each sample at that location with its sample type and
  link to that sample's page. Samples at the same location MUST share one point.
- **FR-008**: When the set holds no sample with a usable location, the tab MUST still be offered,
  and the page MUST say that there is nothing to plot. It MUST NOT show an error or an empty page.

**Which samples each record page plots**

- **FR-009**: On a dataset's page the set is the dataset's samples.
- **FR-010**: On a project's page the set is the samples of the project's datasets that the viewer
  may see.
- **FR-011**: On a sample's page the set is that sample.
- **FR-012**: Samples of every registered sample type MUST be plotted together.

**What the viewer may see**

- **FR-013**: The map MUST plot and count only samples the viewer may see, under the rules FairDM
  already applies: a private project hides everything in it, and under a public project a sample
  follows its dataset.
- **FR-014**: Nothing about a sample the viewer may not see, including its coordinates, name and
  existence, may reach the viewer's browser through the map tab, whether in the page, in data the
  page loads, or in a count.
- **FR-015**: The map tab's address MUST be refused to anyone who may not open the record it
  belongs to, in the same way the record is.

**Retiring what the map replaces**

- **FR-016**: The plugin registered against a location MUST be removed, and its address MUST no
  longer answer. A location's own page is unchanged.
- **FR-017**: The overviews of projects, datasets, people and organizations MUST stop showing a map
  of samples as not available yet. No map card is added to an overview. The maps the overviews
  already draw (a sample's location, a measurement's sample's location, where an organization is
  based) are unchanged.

**Person and organization pages**

- **FR-018**: On a person's page the set is the samples of the datasets the person is credited on.
- **FR-019**: On an organization's page the set is the samples of the datasets the organization is
  credited on. Datasets its members are credited on under their own names are not included.
- **FR-020**: A dataset counts for FR-018 and FR-019 only when the contributor holds a credit on
  the dataset itself. A credit on its project, or owning its project, does not count.
- **FR-021**: On a person's or an organization's page the map MUST plot only samples of public
  datasets in public projects, for every viewer, the person themself and the members of a private
  dataset's team included.
- **FR-022**: FR-002 to FR-008 and FR-012 to FR-015 apply to the person and organization pages as
  they do to the record pages.

**Keeping it basic**

- **FR-023**: The map plugin MUST offer no settings and no hooks for changing what it plots or how.
  Its page is an ordinary template, which a portal can override like any other.

**Accessibility, language, documentation and development data**

- **FR-024**: The map's controls and the links to samples MUST be operable by keyboard. The text
  required by FR-005 and FR-008 is the map's text alternative and MUST be readable when the map
  library has not loaded.
- **FR-025**: Every piece of text the tab shows MUST be marked for translation, and numbers MUST
  follow the active locale.
- **FR-026**: The documentation MUST say which pages carry the map, which samples each page plots,
  what a viewer may see on it, and that it has no settings or hooks. It MUST name the template a
  portal overrides to change the page.
- **FR-027**: The development data MUST include what the stories are tested against: a dataset with
  located and unlocated samples, several samples at one location, a project with a public and a
  private dataset, and a person and an organization credited on public and private datasets.

### Which story owns which requirement

| Story | Requirements |
|---|---|
| US-1: the map on dataset, project and sample pages | FR-001 to FR-016, FR-017 for projects and datasets, FR-023, FR-024, FR-025 |
| US-2: the map on person and organization pages | FR-017 for people and organizations, FR-018 to FR-022 |

Each story extends the documentation (FR-026) and the development data (FR-027) for its own part.

### Key entities

- **Location**: A point given by its latitude and longitude, stored as plain numbers. A sample has
  at most one, and several samples may share one.
- **Map tab**: The page beside a record's overview that plots a set of samples as points. It is one
  plugin on all five pages.
- **Set of samples**: The samples a page's map is drawn from, before locations are considered. It
  is already limited to what the viewer may see.
- **Usable location**: A location whose numbers are a valid latitude and longitude.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On every seeded project, dataset and sample, the number of samples plotted on
  the map equals the number of samples with a usable location that the same viewer can reach by
  browsing that record.
- **SC-002**: For every seeded record and contributor, a visitor's map tab carries no sample from a
  private project or a private dataset, in the page, in the data it loads or in its counts.
- **SC-003**: For every seeded person and organization, the map tab shows the same points and
  counts to a visitor, to the person themself and to a member of a private dataset's team.
- **SC-004**: The plotted and unplotted counts on a map tab add up to the number of samples in its
  set, for the same viewer.
- **SC-005**: On a dataset with 5,000 located samples the map tab opens, and the map can be moved
  and zoomed.
- **SC-006**: The map tab works on a portal whose database has no geospatial extension installed.
- **SC-007**: No map tab renders an empty page or an error, whatever the record holds.
- **SC-008**: No overview page says that a map of samples is not available yet.

## Assumptions

- A tab is contributed the way plugins contribute tabs today.
- The stored coordinates are latitude and longitude in degrees, which is what a portal gets unless
  it changes the coordinate settings. A portal that stores something else gets no points, as the
  edge cases say, and an addon's map is the answer for it.
- Samples are plotted from their own location only. A sample does not inherit a location from a
  parent sample, a dataset or a project.
- The map is drawn with the map library and the openly licensed tiles the overview pages already
  use, which need no key.
- The list of a dataset's samples is the Samples tab (#403), not the map. The map does not list
  samples other than at a selected point.
- Out of scope: lines, areas, layers, heat maps, filtering, searching by place, drawing or editing
  a location on the map, exporting the points, a map card on an overview, a map of where an
  organization's members work, and a portal-wide map of every sample. A richer map is left to an
  addon.
