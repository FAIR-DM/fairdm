# Feature Specification: Map where a project's or dataset's samples come from

**Feature Branch**: `037-sample-map`

**Created**: 2026-11-13

**Status**: Draft

**Goals**: G5: a modern, extensible interface that every portal gets by default, with no frontend
work.

**Roadmap**: none. No roadmap item covers the overview pages' maps, so this is a gap in the roadmap.

**Input**: #674. A reader of a project or dataset page cannot see where its samples were taken.
The project and dataset overview pages map every sample with a location that the viewer may open.
Dense areas group into clusters that open on a click and each point opens its sample. The panel
says how many samples are mapped, across how many datasets and how many have no location. The
agreed panel is on the `prototype-overview-pages` branch (#668).

## What exists and what this specification changes

A sample's page and a measurement's page each show a map of one location, drawn with MapLibre on
OpenFreeMap tiles, which need no key. Specification 030 gives every sample and measurement a
location of its own and lets portal code ask for the spatial coverage of a project or a dataset:
the smallest box holding the locations the viewer may open, crossing the 180th meridian where that
gives the smaller box (030, FR-021 to FR-023).

The project and dataset pages show no map. Specification 018 lists "the map of a project's or
dataset's samples" among the capabilities shown as not yet available (018, FR-016 and FR-017). The
redesign of the four overview pages (#672) drops those placeholders and leaves a place for each
panel that a feature brings back.

After this feature:

- The project page and the dataset page each have a panel showing where their samples come from:
  a map of every sample with a location that the viewer may open.
- Samples that crowd together at the current zoom are grouped into clusters and a cluster opens
  as the reader zooms in or selects it.
- Every sample on the map can be opened from it.
- The panel says how many samples are mapped, across how many datasets on a project and how many
  have no location.
- A reader who cannot use the map or whose browser runs no scripts, gets the same counts and the
  area covered as text and a link to the record's samples list, which gives each sample's latitude
  and longitude.

## What this replaces

- **Specification 018, FR-016**: "the map of a project's or dataset's samples" is no longer a
  capability shown as not yet available. The build edits 018 so it reads as current: the project
  and dataset pages show the panel this specification describes.
- **Specification 030, Boundary**: a map of a dataset's samples and its spatial coverage is no
  longer left to #497. The build edits that line so it names this specification for the project and
  dataset maps and keeps #497 for the map of organizations.

## Boundary

- **The redesigned pages** (header, panels, fact sheet, edit controls) are #672. This feature's
  panel sits in the page #672 builds and is built after #672's sample-page pull request, which
  brings the map script this panel shares with the sample and measurement pages.
- **The map is part of FairDM itself, not an add-on** and draws the same OpenFreeMap tiles as the
  maps on sample and measurement pages. #497 keeps the community map of organizations and serving
  map tiles from the portal itself.
- **Measurements are not points on this map.** A measurement with a location of its own counts in
  the record's spatial coverage, as 030 defines it and so in the area the map opens on, but the
  map places samples only.
- **Drawing the spatial coverage as a box** on the map is not part of this feature.
- **Filtering a list by an area drawn on the map** and any map on a list page, are not part of
  this feature.
- **Showing a sensitive location less precisely** is not part of this feature, as in 030.
- **The citation downloads (#673) and recent activity (#675)** are the other two panels the
  redesign brings back. Each is its own feature.

## Clarifications

### Session 2026-11-13

Each question was answered from the agreed prototype and the maintainer's decisions on #668,
without putting it to him again. The longer reasoning is in [decisions.md](decisions.md).

- Q: The prototype maps at most 1,500 samples. How many does the map show? → A: Every sample with
  a location that the viewer may open, with no limit. The page itself does not wait for them: it
  opens and reads in full while the map's samples are still arriving, however many there are.
- Q: What does a reader who cannot see the map get? → A: The map has a text equivalent: how many
  samples it shows and the area they cover. The panel also links to the record's samples list,
  which gives every sample with its latitude and longitude, so each location the map shows can be
  reached as text. The same counts and link are there when the browser runs no scripts.
- Q: Which samples count? → A: Only those the viewer may open (018, FR-019). On a project, only
  the samples in datasets the viewer may open. A sample the viewer may not open adds no point, no
  count and nothing to the area the map opens on (030, FR-023).
- Q: Where does the map open? → A: On the record's spatial coverage for that viewer (030, FR-021
  to FR-023), so samples on both sides of the 180th meridian open on a narrow view rather than the
  whole globe. A coverage of a single spot opens close in, not at the closest zoom the tiles allow.
- Q: When is the panel shown? → A: When the viewer may open at least one sample in the record. A
  viewer who may open no sample sees no panel. A viewer who may open samples none of which has a
  location sees the panel saying there is nothing to map yet and no map.
- Q: What happens to samples at exactly the same spot, which no zoom separates? → A: Selecting
  them lists each of those samples and each opens its page.
- Q: Are the tile credits shown? → A: They start closed, behind an information control that opens
  them, as on every map in the redesigned pages (#668).
- Q: Does scrolling the page over the map zoom the map? → A: No. Scrolling over the map scrolls
  the page. The map zooms with its own controls, a pinch or a scroll with the platform's modifier
  key held.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A reader sees where a project's or dataset's samples come from and opens one (Priority: P1)

A reader on a project or dataset page wants to know where its samples were taken. The page shows
them every sample they may open that has a location, on a map. Crowded areas are grouped and open
as the reader zooms in. The reader opens any sample from its point. The panel tells them how many
samples are mapped and how many have no location and a reader who cannot use the map reaches the
same facts and every location as text.

**Why this priority**: this is the feature. Without it the pages give no sense of where the
research took place.

**Independent Test**: seed a project with two datasets of located samples, a few samples with no
location and one private dataset. Open the project page and its datasets' pages as a visitor, as a
member of the private dataset's team and as someone outside it and check what each map, count and
link shows.

**Acceptance Scenarios**:

1. **Given** a dataset whose samples the viewer may open, some with a location and some without,
   **When** the viewer opens the dataset page, **Then** its map shows one point for each located
   sample and the panel gives the number mapped and the number with no location.
2. **Given** a project with several datasets the viewer may open, **When** the viewer opens the
   project page, **Then** its map shows the located samples of all those datasets and the panel
   gives the number mapped, the number of datasets they come from and the number with no location.
3. **Given** a project with a dataset the viewer may not open, **When** the viewer opens the
   project page, **Then** none of that dataset's samples is a point, none is counted and none
   widens the area the map opens on.
4. **Given** a member of that dataset's team, **When** they open the same project page, **Then**
   its samples are on the map and in the counts.
5. **Given** a record whose samples are spread over an area, **When** the map opens, **Then** it
   shows the whole of the record's spatial coverage for the viewer.
6. **Given** samples on both sides of the 180th meridian, **When** the map opens, **Then** it opens
   on the narrow area spanning the meridian, not the whole globe.
7. **Given** many samples close together, **When** the map is zoomed out, **Then** they are grouped
   into clusters, each saying how many samples it holds and the clusters' numbers add up to the
   number mapped.
8. **Given** a cluster, **When** the reader selects it, **Then** the map zooms in until its samples
   separate.
9. **Given** several samples at exactly the same location, **When** the reader selects them,
   **Then** each of those samples is listed and each opens its page.
10. **Given** a point, **When** the reader selects it, **Then** they see the sample's name, its type
    and its dataset, with a link that opens the sample's page.
11. **Given** a record with tens of thousands of located samples, **When** the reader opens its
    page, **Then** the page opens and reads in full before the map's samples have arrived and the
    map then shows every one of them.
12. **Given** samples the viewer may open, none of which has a location, **When** the viewer opens
    the page, **Then** the panel says there is nothing to map yet and shows no map.
13. **Given** a record in which the viewer may open no sample, **When** they open its page,
    **Then** the page shows no map panel.
14. **Given** a reader using a screen reader, **When** they reach the map, **Then** it is announced
    with the number of samples it shows and the area they cover and the panel offers a link to the
    record's samples list, which gives each sample's latitude and longitude.
15. **Given** a browser that runs no scripts, **When** the reader opens the page, **Then** the panel
    still gives the counts, the area covered and the link to the samples list.
16. **Given** the map has opened, **When** the reader looks for the tile credits, **Then** they are
    closed behind an information control and selecting it opens them.
17. **Given** the reader scrolls the page with the pointer over the map, **When** no modifier key is
    held, **Then** the page scrolls and the map does not zoom.

### Edge Cases

- **A record with one located sample**: the map opens close in on it, not at the closest zoom the
  tiles allow.
- **Many samples at one spot and no others**: the coverage is a single point. The map opens close
  in and the samples are reachable as scenario 9 says.
- **A sample whose dataset belongs to another project**: a project's map shows the samples of the
  project's own datasets, as the project's Samples figure counts them.
- **A sample moves or loses its location**: the next time the page is opened, the map and the
  counts follow.
- **The tile service cannot be reached**: the counts, the area covered and the link to the samples
  list still show and the samples' points still open their pages where the map can draw them.
- **The map's samples fail to load**: the panel's counts, area and link stay and the page is
  otherwise unaffected.
- **A viewer with no right to open the record itself**: the record's page answers "not found" (018,
  FR-018) and so does any address the map loads its samples from.

## Requirements *(mandatory)*

### Functional Requirements

**Where the panel is shown**

- **FR-001**: The project overview page and the dataset overview page MUST each show a panel of
  where the record's samples come from when the viewer may open at least one sample in the record.
- **FR-002**: Where the viewer may open no sample in the record, the page MUST NOT show the panel.

**What the map holds**

- **FR-003**: A dataset's map MUST show one point for every sample in the dataset that has a
  location and that the viewer may open.
- **FR-004**: A project's map MUST show one point for every sample with a location in the project's
  datasets that the viewer may open, counting only datasets the viewer may open.
- **FR-005**: A sample the viewer may not open MUST add no point, no count and nothing to the area
  the map opens on.
- **FR-006**: The map MUST show every such sample, however many there are. No sample may be left
  off because of the number of samples.
- **FR-007**: Measurements MUST NOT be points on the map.

**Opening and moving about the map**

- **FR-008**: The map MUST open on the record's spatial coverage for the viewer (030, FR-021 to
  FR-023), including a coverage that spans the 180th meridian.
- **FR-009**: Where the coverage is a single spot or very small, the map MUST open close in on it
  but no closer than a fixed zoom that still shows the area around it.
- **FR-010**: Samples close together at the current zoom MUST be grouped into clusters, each stating
  how many samples it holds. Clusters MUST separate into their samples as the reader zooms in.
- **FR-011**: Selecting a cluster MUST zoom the map in until the cluster's samples separate.
  Selecting samples at the same location, which no zoom separates, MUST list each of them.
- **FR-012**: Selecting a point MUST show the sample's name, its type and its dataset, with a link to
  the sample's page.
- **FR-013**: Scrolling the page with the pointer over the map MUST scroll the page. The map MUST zoom
  only by its own controls, a pinch or a scroll with the platform's modifier key held.
- **FR-014**: The map MUST draw its background from the same tile source as the maps on sample and
  measurement pages, needing no key, no account and no add-on.
- **FR-015**: The tile credits MUST start closed, behind an information control that opens them.

**What the panel says**

- **FR-016**: The panel MUST state how many samples the map shows and how many of the samples the
  viewer may open in the record have no location.
- **FR-017**: On a project, the panel MUST also state how many datasets the mapped samples come from.
- **FR-018**: The number mapped and the number with no location MUST add up to the record's Samples
  figure for the same viewer.
- **FR-019**: Where none of the samples the viewer may open has a location, the panel MUST say there
  is nothing to map yet and MUST NOT show a map.

**Reaching it without the map**

- **FR-020**: The map MUST carry a text equivalent stating how many samples it shows and the area they
  cover.
- **FR-021**: The panel MUST link to the record's samples list (specification 023), which gives each
  sample's latitude and longitude.
- **FR-022**: The counts, the area covered and the link MUST be present and readable when the browser
  runs no scripts, when the tile service cannot be reached and when the map's samples fail to load.

**Speed and access**

- **FR-023**: The page MUST open and be readable in full without waiting for the map's samples,
  however many there are.
- **FR-024**: Anything the map loads its samples from MUST answer only for a record the viewer may
  open and "not found" otherwise (018, FR-018) and MUST give only what FR-003 to FR-005 allow.

Every requirement above belongs to User Story 1.

### Key Entities

- **Sample**: the record placed on the map, at its location (030). The map shows its name, type and
  dataset and links to its page.
- **Spatial coverage**: the smallest box holding the locations the viewer may open in a project or
  dataset (030, FR-021 to FR-023). The map opens on it and the text equivalent states it.
- **Project, Dataset**: the records whose pages carry the panel.

No model is added or changed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For every viewer, the number of points on a record's map equals the number of samples
  with a location in it that the viewer may open and the number mapped plus the number with no
  location equals the Samples figure the same viewer sees in the page's header.
- **SC-002**: A viewer who may not open a sample finds no trace of it on the project or dataset page:
  not as a point, not in a count and not in the area the map opens on.
- **SC-003**: Every sample on the map can be opened from it, including samples that share one
  location.
- **SC-004**: A project with 20,000 located samples maps all 20,000 and its page is readable before
  the map's samples have arrived.
- **SC-005**: A reader using only a keyboard and a screen reader can learn from the panel how many
  samples are mapped, how many have no location and the area covered and reach every mapped
  sample's location as text, without using the map.

## Assumptions

- The redesigned project and dataset pages (#672) provide the panel this feature fills and the
  sample-page pull request of #672 provides the map script shared by every map on the overview
  pages. This feature is built after both.
- Project and dataset spatial coverage for a viewer (030, FR-021 to FR-023) works as specified. It
  was run against this repository before this specification was written (research.md).
- The record's samples list (specification 023) gives every sample's latitude and longitude. It was
  checked on the development data before this specification was written (research.md).
- OpenFreeMap stays reachable without a key. A portal that needs its own tiles waits for #497.
