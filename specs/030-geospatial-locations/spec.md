# Feature Specification: Capture, store and query locations as geospatial data

**Feature Branch**: `030-geospatial-locations`

**Created**: 2026-10-14

**Status**: Draft

**Goals**: G1: a core data model of projects, datasets, samples, measurements and contributors that
domain schemas can extend and rely on. G9: records in the core model can be searched, sorted and
filtered from the portal.

**Roadmap**: none. No roadmap item covers locations, so this is a gap in the roadmap. The nearest is
R26, a research group can deploy the shipped stack.

**Input**: #494. Portals capture, store and query locations as real geospatial data. A researcher
records where a sample was taken as decimal degrees in WGS 84. Portal
code asks which records lie inside an area or near a point without loading every location into
Python. Machines read a record's location from the API.

## What exists, and what this specification changes

`fairdm.contrib.location` holds one model, `Point`, with `x` and `y` as five-place decimal columns
and a `crs` string that is only a label. Every sample and contributor at the same coordinates
shares one `Point` row, and each pair has a page at `/location/<lon>/<lat>/`. The sample form picks
an existing `Point` through a search box. The only spatial calculation is a dataset's bounding box, taken from the minimum and
maximum of the two columns.

After this feature:

- Every sample and every measurement has a location of its own: a point on the Earth, an optional
  elevation and an optional uncertainty. Changing one record's location never changes another's.
- An organization has a point of its own. A person has none.
- Coordinates are entered as signed decimal degrees in WGS 84, and are stored in WGS 84. Another
  reference system or another notation is converted by the person typing.
- Portal code can ask the database which samples, measurements or organizations lie inside an
  area, lie within a distance of a point, or are nearest a point.
- `Point`, its page, and the `FAIRDM_CRS`, `FAIRDM_X_COORD` and `FAIRDM_Y_COORD` settings are gone.

## Boundary

- **Running FairDM on PostgreSQL with PostGIS**, in development, in the test suite and in CI, is
  #500. This feature builds on it.
- **Tagging records with the areas their location falls in** is #496.
- **Showing records on maps**, including a map of a dataset's spatial coverage and any filter drawn
  on a map, is #497. The maps that sample, measurement and organization pages already show keep
  working here.
- **Lines, areas and depth intervals** are not part of the core. A location is a point. A borehole
  is a point, and a sample type that needs a depth interval declares fields of its own.
- **Showing a sensitive location less precisely** to the public is not part of this feature.
- **Keeping coordinates exactly as they were typed**, beside the stored WGS 84 point, is not part of
  this feature.
- **Typing coordinates in another reference system**, by its EPSG code, with the portal converting
  them to WGS 84, is #512. Until then a coordinate is entered in WGS 84.
- **Typing coordinates as degrees and minutes, or degrees, minutes and seconds**, with or without
  hemisphere letters, is #513. Until then a coordinate is a signed decimal number of degrees.
- **Filtering API lists by area or distance** is not part of this feature.
- **A dataset's DataCite metadata describing its spatial coverage** is #511. The DataCite export
  cannot be produced today, so it is delivered with that issue. The spatial coverage it needs is
  part of this feature.
- **Import and export becoming reachable and dependable** is R21. This feature makes a location go
  in and come out with the rest of a sample's or measurement's row wherever tabular import and
  export exist.

## Clarifications

### Session 2026-10-14

Each question was answered from the maintainer's replies while the feature was agreed, without
putting it to him again. The longer reasoning is in [decisions.md](decisions.md).

- Q: Is a location a record that samples share, or a value on each sample? → A: A value on each
  sample and each measurement. Two samples at the same place hold the same coordinates and share
  nothing else. Correcting one never moves the other.
- Q: Does a person have a location of their own? → A: No. Where a person is shown on a map, the
  place is their primary affiliation's organization, as it is today.
- Q: A measurement records no location of its own. Where is it? → A: Where its sample is. Anything
  that asks where a measurement is gets its own location first and its sample's otherwise.
- Q: A measurement is public and its sample is not. May a visitor learn the sample's location
  through the measurement? → A: No. A measurement's location falls back to its sample's only for
  someone who may open the sample. For anyone else a measurement with no location of its own has
  none.
- Q: What does the API return for a measurement with no location of its own? → A: No location. The
  API returns what the record holds, and the sample's location is on the sample.
- Q: What does elevation measure? → A: Metres above mean sea level, negative below it, as given.
- Q: What does uncertainty measure? → A: The distance in metres from the point within which the
  true location lies. It is never negative.
- Q: Does an organization's point carry elevation and uncertainty? → A: No. It is a plain point.
  Its coordinates are entered as decimal degrees, as a sample's are, in WGS 84 only.
- Q: May a researcher type coordinates in a projected system or another reference system? → A: No.
  Every coordinate is entered in WGS 84, and a researcher whose notebook uses another system
  converts it first. The maintainer asked for this after the walkthrough, and accepting other
  systems is #512.
- Q: May a researcher type degrees and minutes, degrees, minutes and seconds, or hemisphere
  letters? → A: No. A coordinate is a signed decimal number of degrees, south and west negative.
  The maintainer asked for decimal degrees only for now, and the other notations are #513.
- Q: How precisely is a location shown? → A: To five decimal places of a degree, about one metre.
  It is stored as typed, without rounding.
- Q: Are existing locations carried across the upgrade? → A: They need not be. No portal holds
  location data yet.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A researcher records where a sample was taken (Priority: P1)

A researcher opens a sample's form and types the coordinates from their field notebook. They may
type them as signed decimal degrees in WGS 84, as a GPS receiver records them, with south and west
negative. Where the notebook uses a projected system, such as a UTM zone or a national grid, or
degrees, minutes and seconds, they convert it first. They may
add an elevation and an uncertainty. The portal checks what they typed and stores it on that sample
alone. The sample's page shows where it was taken.

**Why this priority**: Recording a location is what every other part of this feature reads.

**Independent Test**: Create a sample with coordinates in decimal degrees, then open its page and read the stored point back.

**Acceptance Scenarios**:

1. **Given** a sample form, **When** the researcher enters a latitude and longitude in decimal
   degrees, **Then** the sample is saved with that point in WGS 84.
2. **Given** a sample form, **When** the researcher enters a negative latitude or longitude,
   **Then** the sample is saved with a point south or west of the origin.
3. **Given** a sample form, **When** it is opened, **Then** it asks for a latitude and a longitude
   in WGS 84 and offers no choice of reference system.
4. **Given** a sample form, **When** the researcher enters an elevation or an uncertainty, **Then**
   the sample is saved with each one given, and without the one not given.
5. **Given** coordinates outside the range of WGS 84, a latitude beyond 90 degrees or a longitude
   beyond 180, text that is not a decimal number, or a negative uncertainty, **When** the form is
   submitted, **Then** it is refused, says which value is wrong, and nothing is saved.
6. **Given** an elevation or an uncertainty with no coordinates, **When** the form is submitted,
   **Then** it is refused and nothing is saved.
7. **Given** two samples at the same coordinates, **When** the researcher changes one sample's
   location, **Then** the other sample's location is unchanged.
8. **Given** a sample with a location, **When** the researcher clears it, **Then** the sample has no
   location, and its elevation and uncertainty are cleared with it.
9. **Given** a sample with a location, **When** its page is opened, **Then** the page gives the
   latitude and longitude to five decimal places, and the elevation and uncertainty where they are
   recorded.
10. **Given** a sample with a location, **When** its form is opened again, **Then** the form holds
    the stored location in WGS 84 decimal degrees.

---

### User Story 2 - A portal developer finds records by where they are (Priority: P1)

A portal developer writing a page or a report asks the database for the samples that lie inside an
area, the samples within a distance of a point, or the samples nearest a point. They ask the same of
measurements and of organizations, and combine each with any other filter, including the one that
keeps what a viewer may open. They also ask for the area a dataset's or a project's records cover.
None of it loads every location into Python.

**Why this priority**: Spatial questions are the reason for storing locations as geospatial data,
and #496 and #497 are both built on them.

**Independent Test**: Load samples, measurements and organizations at known places, then run each
lookup and compare its result with the places by hand.

**Acceptance Scenarios**:

1. **Given** samples inside and outside a box, **When** a developer asks for the samples inside it,
   **Then** they get exactly those inside.
2. **Given** samples inside and outside a polygon, **When** a developer asks for the samples inside
   it, **Then** they get exactly those inside.
3. **Given** samples at known distances from a point, **When** a developer asks for those within a
   distance in metres or kilometres, **Then** they get exactly those within it.
4. **Given** samples at known distances from a point, **When** a developer asks for them nearest
   first, **Then** they come back in order of distance and each carries its distance.
5. **Given** a measurement with no location of its own, **When** a developer asks for measurements
   inside an area that holds its sample, **Then** the measurement is included.
6. **Given** a measurement whose own location lies outside an area that holds its sample, **When**
   a developer asks for measurements inside the area, **Then** the measurement is not included.
7. **Given** organizations inside and outside an area, **When** a developer asks for organizations
   inside it, **Then** they get exactly those inside.
8. **Given** any of these lookups, **When** it is combined with the filter that keeps what a viewer
   may open, **Then** the result holds only records inside the area that the viewer may open, and
   no measurement placed there only by a sample the viewer may not open.
9. **Given** a dataset whose samples and measurements have locations, **When** a developer asks for
   its spatial coverage, **Then** they get the smallest area that holds every one of them, and none
   when none has a location.
10. **Given** a dataset whose locations lie on both sides of the 180th meridian and close to it,
    **When** a developer asks for its spatial coverage, **Then** the area spans the meridian and not
    the rest of the globe.
11. **Given** a project, **When** a developer asks for its spatial coverage, **Then** they get the
    area that holds the locations of every dataset in it.

---

### User Story 3 - A researcher records where a measurement was made (Priority: P2)

A researcher's measurement was made somewhere other than where its sample was taken, such as a
reading taken in the field at a site some distance from the core it belongs to. They record the
measurement's own location the same way as a sample's. A measurement with no location of its own is
where its sample is.

**Why this priority**: Most measurements are made where their sample was taken, so most never need
a location of their own.

**Independent Test**: Create a measurement with a location and one without on a sample with a
location, then open each page and run a lookup over both.

**Acceptance Scenarios**:

1. **Given** a measurement form, **When** the researcher enters a location, **Then** the
   measurement is saved with it, checked as a sample's is.
2. **Given** a measurement with a location of its own, **When** its page is opened, **Then** the
   page shows the measurement's location.
3. **Given** a measurement with no location of its own whose sample has one and may be opened by the
   viewer, **When** its page is opened, **Then** the page shows the sample's location as the
   sample's.
4. **Given** a measurement with no location of its own whose sample the viewer may not open,
   **When** its page is opened, **Then** the page shows no location.
5. **Given** a measurement with a location of its own, **When** its sample's location changes,
   **Then** the measurement's location is unchanged.

---

### User Story 4 - A developer's script reads a record's location from the API (Priority: P2)

Someone writing a harvester requests samples, measurements and organizations from the API. Each one
carries its location as a GeoJSON geometry, longitude first, with the elevation as the third
coordinate where one is recorded, and the uncertainty beside it.

**Why this priority**: The API is how machines reach a portal's data (G10), and today it has no
location in a form a GIS can read.

**Independent Test**: Request a sample with a location, elevation and uncertainty, one with a point
only, one with none, a measurement with and without a location of its own, and an organization with
a point, and read each location back.

**Acceptance Scenarios**:

1. **Given** a sample with a location, **When** it is returned, **Then** it carries a GeoJSON point
   with longitude, then latitude, in WGS 84.
2. **Given** a sample with an elevation, **When** it is returned, **Then** the point carries the
   elevation as its third coordinate.
3. **Given** a sample with an uncertainty, **When** it is returned, **Then** it carries the
   uncertainty in metres beside the point.
4. **Given** a sample with no location, **When** it is returned, **Then** its location is empty.
5. **Given** a measurement with no location of its own, **When** it is returned, **Then** its
   location is empty.
6. **Given** an organization with a point, **When** it is returned, **Then** it carries the point as
   a GeoJSON geometry.
7. **Given** a person, **When** they are returned, **Then** the response carries no location of
   their own.

---

### User Story 5 - A researcher imports and exports locations with their samples (Priority: P2)

A researcher exports a dataset's samples or measurements, and the file has the location in columns
of each row: latitude and longitude in WGS 84 decimal degrees, elevation and uncertainty. They edit
the file or prepare a new one, and import it. Coordinates in the file are decimal degrees, as the
form takes them. A location is never exported or imported as a table of its own.

**Why this priority**: A research group's existing data arrives as spreadsheets (G11), and a
location that cannot go in with its row has to be entered again by hand.

**Independent Test**: Export samples with and without locations, import the file into an empty
dataset, and compare the locations.

**Acceptance Scenarios**:

1. **Given** samples with locations, **When** they are exported, **Then** each row carries its
   latitude, longitude, elevation and uncertainty, and a row without a location carries none.
2. **Given** an exported file, **When** it is imported into a dataset, **Then** each record has the
   location it was exported with.
3. **Given** a file with a row whose coordinates are not decimal numbers or are out of range, **When** it is
   imported, **Then** that row is reported with the value that is wrong, and is not saved.
5. **Given** measurements with and without locations of their own, **When** they are exported,
   **Then** a row carries only the measurement's own location.

---

### User Story 6 - A profile maintainer places an organization (Priority: P2)

A profile maintainer adds an organization from ROR, and it gets the coordinates ROR publishes for
it. For an organization ROR does not know, or one ROR places wrongly, they enter the point on the
organization's form. The organization's page shows where it is, and the people affiliated with it
are placed there too.

**Why this priority**: An organization's place is what the community map in #497 shows, and what a
person's place is taken from.

**Independent Test**: Create an organization from ROR and one by hand, then open both pages and
read the points back.

**Acceptance Scenarios**:

1. **Given** a ROR record with coordinates, **When** an organization is created or updated from it,
   **Then** the organization has that point.
2. **Given** an organization form, **When** the maintainer enters a latitude and longitude in
   decimal degrees, **Then** the organization is saved with that point.
3. **Given** two organizations at the same coordinates, **When** one is moved, **Then** the other is
   unchanged.
4. **Given** a person whose primary affiliation is to an organization with a point, **When** the
   person is placed on a map, **Then** they are placed at the organization's point.

---

### Edge Cases

- A point exactly on an area's edge counts as inside it.
- A distance lookup measures along the Earth's surface, not in degrees, so a lookup at high latitude
  is as accurate as one at the equator.
- Projected coordinates, such as an easting and a northing in metres, are not a latitude and a
  longitude in range, and are refused as out of range.
- Degrees, minutes and seconds, and hemisphere letters, are not decimal numbers and are refused.
- A sample type whose registered fields leave out the location gets no location input in its forms
  and no location columns in its import and export. The sample still has a location, empty.
- A dataset with a single located record, or with every location at one place, has a spatial
  coverage of that one point.
- Deleting a sample or a measurement deletes its location with it. Nothing else refers to it.
- The location page's address, `/location/<lon>/<lat>/`, answers "not found".

## Requirements *(mandatory)*

### Functional Requirements

**Recording a location**

- **FR-001**: Every sample and every measurement MUST have a location of its own, made of an
  optional point, an optional elevation and an optional uncertainty. No location is shared between
  records.
- **FR-002**: A point MUST be stored in WGS 84 as longitude and latitude, as typed, without
  rounding.
- **FR-003**: An elevation MUST be stored in metres above mean sea level, negative below it, and
  MUST NOT be changed.
- **FR-004**: An uncertainty MUST be stored as a distance in metres, zero or more.
- **FR-005**: An elevation or an uncertainty MUST NOT be stored without a point.
- **FR-006**: The location input MUST take a latitude and a longitude as signed decimal degrees,
  and MUST NOT accept degrees and minutes, degrees, minutes and seconds, or hemisphere letters
  (#513).
- **FR-007**: The location input MUST take every coordinate as a latitude and a longitude in
  WGS 84, and MUST NOT offer a choice of reference system. Converting from another system is
  the researcher's to do first (#512).
- **FR-008**: A latitude outside -90 to 90, a longitude outside -180 to 180, text that is not a
  number, and one coordinate without the other MUST be refused with a message, and nothing MUST be
  saved.
- **FR-009**: A sample or measurement type MUST get the location input in its generated forms, and
  location columns in its import and export, when its registration lists the location among its
  fields, and MUST NOT when it does not.

**Organizations and people**

- **FR-010**: An organization MUST have an optional point of its own, in WGS 84, with no elevation
  and no uncertainty, entered as FR-006 says.
- **FR-011**: An organization created or updated from ROR MUST take its point from the coordinates
  in the ROR record.
- **FR-012**: A person MUST NOT have a location of their own. A person placed on a map MUST be placed
  at their primary affiliation's organization's point.

**A measurement's location**

- **FR-013**: A measurement's effective location MUST be its own location where it has one, and its
  sample's otherwise.
- **FR-014**: A measurement's effective location MUST fall back to its sample's only for a viewer who
  may open the sample. For any other viewer, a measurement with no location of its own MUST have
  none.

**Lookups**

- **FR-015**: Portal code MUST be able to narrow any queryset of samples, measurements or
  organizations to the records whose location lies inside a box or a polygon.
- **FR-016**: Portal code MUST be able to narrow any such queryset to the records within a given
  distance of a point, measured along the Earth's surface.
- **FR-017**: Portal code MUST be able to order any such queryset by distance from a point, nearest
  first, with each record's distance available.
- **FR-018**: Lookups on measurements MUST use the effective location of FR-013.
- **FR-019**: Every lookup MUST combine with any other filter on the same queryset, including the
  filter that keeps what a viewer may open, and the combination MUST honour FR-014.
- **FR-020**: Lookups MUST run in the database, using a spatial index.
- **FR-021**: Portal code MUST be able to ask for the spatial coverage of a dataset or a project: the
  smallest area holding the locations of its samples and measurements, or none when none has a
  location.
- **FR-022**: Spatial coverage MUST span the 180th meridian, rather than the rest of the globe,
  where that gives the smaller area.
- **FR-023**: Spatial coverage computed for a viewer MUST count only records that viewer may open,
  under FR-014.

**Pages and tables**

- **FR-024**: A sample's page MUST show its location, with latitude and longitude to five decimal
  places, and its elevation and uncertainty where recorded.
- **FR-025**: A measurement's page MUST show its own location, or its sample's under FR-014, and
  MUST say which of the two it is.
- **FR-026**: The maps already shown on sample, measurement and organization pages MUST keep working.
- **FR-027**: The collection tables of samples and measurements MUST show latitude as the latitude
  and longitude as the longitude.
- **FR-028**: A location MUST NOT have a page of its own. The address `/location/<lon>/<lat>/` and
  the collection tables' link to it MUST be removed.

**API, import and export**

- **FR-029**: The API MUST return each sample's, measurement's and organization's own location as a
  GeoJSON geometry in WGS 84, longitude first, with the elevation as a third coordinate where
  recorded, and the uncertainty in metres beside it.
- **FR-030**: The API MUST return an empty location for a record with no location of its own.
- **FR-031**: Tabular export of samples and measurements MUST write each record's own location as
  latitude, longitude, elevation and uncertainty columns of its row, in WGS 84 decimal degrees.
- **FR-032**: Tabular import of samples and measurements MUST read those columns, read
  them as FR-006 says, and report a row whose location is refused under FR-008 without
  saving it.
- **FR-033**: A location MUST NOT be exported or imported as a table of its own.

**Removals and documentation**

- **FR-035**: The `Point` model, its form, its latitude and longitude input masks,
  `normalize_coordinate`, `serialize_dataset_samples`, and the `FAIRDM_CRS`, `FAIRDM_X_COORD` and
  `FAIRDM_Y_COORD` settings MUST be removed.
- **FR-036**: The documentation MUST describe a location, the decimal degrees in WGS 84 it is
  entered in, the lookups and spatial coverage, and the breaking changes a portal meets when it
  upgrades.

### Key Entities

- **Location**: where a sample or a measurement is on the Earth. A WGS 84 point, entered as signed decimal degrees, with an optional
  elevation in metres and an optional uncertainty in metres. It belongs to the one record that holds
  it and is never shared.
- **Organization point**: where an organization is. A WGS 84 point and nothing more.
- **Spatial coverage**: the smallest area holding the locations of a dataset's or a project's
  records, as seen by a given viewer.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A place typed as signed decimal degrees is stored as a point that agrees with the
  typed value to within one metre, for every hemisphere.
- **SC-002**: Changing one record's location changes no other record, in every case the acceptance
  scenarios cover.
- **SC-003**: Every area, distance and nearest-first lookup returns the same records as the same
  question answered by hand over the test data, for samples, measurements and organizations.
- **SC-004**: No lookup, page, export or API response reveals the location of a sample to a viewer
  who may not open it, including through a measurement.
- **SC-005**: A lookup over 100,000 located samples answers without reading every sample, as the
  database's query plan shows.
- **SC-006**: A dataset whose locations lie within 5 degrees of the 180th meridian on both sides has
  a spatial coverage less than 10 degrees of longitude wide.
- **SC-007**: Once the feature is built, no module, setting, document or template refers to `Point`,
  `FAIRDM_CRS`, `FAIRDM_X_COORD` or `FAIRDM_Y_COORD`.

## Assumptions

- #500 has landed: the database is PostgreSQL with PostGIS, GeoDjango is installed, and the test
  suite runs against PostGIS locally and in CI.
- No portal holds location data yet, so existing locations need not be carried across the upgrade.
- The specifications that describe locations today, FS-005 (samples), FS-011 (the API), FS-018
  (overview pages) and FS-019 (contributor overview pages), are edited to match this one in the
  same pull request.
- `CONTEXT.md` gains the terms Location, Reference system and Spatial coverage, and stops using
  "Point" for a model.
- Tabular import and export are whatever exists when the feature is built. The location columns
  are added to them, and their reachability stays with R21.

## Breaking changes

- Code that reads or filters on `Point.x`, `Point.y` or `Point.crs`, such as `location__x=...`, has
  to change.
- A sample's or a contributor's `location` is no longer a foreign key to a shared row.
- A person no longer has a `location`.
- `/location/<lon>/<lat>/` no longer exists.
- The `FAIRDM_CRS`, `FAIRDM_X_COORD` and `FAIRDM_Y_COORD` settings are removed.
