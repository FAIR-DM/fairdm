# Decisions: capture, store and query locations as geospatial data

Questions the specification settled, with the reasoning that is too long for the specification
itself. Each says what would reopen it.

## D1. A location is a value on each record, not a shared model

The maintainer asked for the two designs to be weighed and agreed with the outcome. The comparison
is recorded in full because #496 and #497 build on it.

**A shared location model.** One row per distinct place, which every sample and measurement at that
place points to.

| For | Against |
|---|---|
| "Every sample at this place" is a join on one id | Records share a row only when their numbers match exactly. Coordinates converted from a UTM zone or a national grid differ in the last digits of the float, so one site becomes two rows. Elevation and uncertainty are part of the match, so a 10 m and a 15 m uncertainty at one site also split it. Sharing means "the same numbers", not "the same site". |
| #496 tags one row per place | #496 tags organizations too, and they hold a point of their own. It needs per-record tagging whatever this feature does. |
| Each pair of coordinates is stored once | The saving is a few bytes per record |
| | The location page was the only thing that read the sharing, and it goes (D7). |
| | Every generated form, filter, import column, export column and API field needs custom code to turn the foreign key into coordinates and back. A field on the model gets all of them from the registry (G2). |
| | A row could never be edited, only replaced by a get-or-create on the new coordinates. Anyone editing one in place, through the admin or a shell, moves every record that shares it. |
| | Rows left with no record after a move, a unique constraint on floating-point geometry, a join on every list, and a get-or-create on every imported row |

**Location fields on the Sample and Measurement base models.**

| For | Against |
|---|---|
| A geometry field on the model is how GeoDjango is documented and how an experienced Django developer expects a location to be held. Editing a sample's location edits it. | The point, elevation and uncertainty fields are declared on two base models rather than one |
| Generated forms, filters, admin, API and import and export see an ordinary field | Nothing holds a name or other details for a place, unless a portal models one |
| No joins, no get-or-create, no orphaned rows, no uniqueness on floats | |
| Organizations hold a point field too, so all three record types share one input, one API format and one set of lookups | |
| "Samples at the same site" is a within-distance lookup, which matches what a site is better than exact equality does | |
| IGSN sample metadata and Darwin Core both put the coordinates on the sample or occurrence itself | |

**The maintainer's arguments for a shared model, and the answers.**

1. *One query on the location table gives the map layer of the whole portal, and each point opens a
   card that fetches everything at it.* A location table cannot feed a map by itself, because a point
   exists only because a record sits there, and that record may be private. The layer has to join to
   the samples and measurements the viewer may open either way. With fields it is still one query:
   `Sample` is a polymorphic base model, so every sample type's point is in its one base table, and
   the layer is the visible samples grouped by point with a count on each. Measurements add a second
   query in both designs. At a size where that matters, the map is served as vector tiles built by
   PostGIS from the table, which also works the same either way. The card at a point is one indexed
   query in both: the rows pointing at a location, or the visible records within a small distance of
   the point. The second also gathers a site whose coordinates arrived in two systems.
2. *Counting the records at a location is easy.* The count comes from the same grouping as the map
   layer. It is one query either way, and it has to respect visibility either way.
3. *Tagging happens once against a single row, not fifty times.* It writes fewer rows, but it is not
   less work. Tagging is one spatial join in a single SQL statement either way, and loading a new set
   of areas is one statement either way. Most of the fifty records are measurements, which hold no
   location of their own unless they were made elsewhere (D3), so they take their sample's tags and
   store nothing. #496 has to tag organizations per record regardless, so a location model would give
   it two mechanisms. And #496 may work tags out when they are read rather than storing them, in
   which case nothing is written in either design.

**Where sharing does belong.** A place that is a thing in its own right, with a name, a description,
a history and an identifier of its own, such as a borehole, a station or an outcrop. Research data
already models that as a parent sample with the samples taken from it as its children, and IGSN
registers it that way. A portal that needs sites declares that sample type. A shared row of bare
coordinates gives the grouping without anything that makes a site a site.

*Revisit if:* a portal needs places with properties of their own that a parent sample cannot carry.
**ADR:** docs/adr/0032-a-location-is-a-value-on-each-record.md

## D2. Organizations hold a plain point, and people hold none

The maintainer drew the line: the full location, with its reference systems, elevation and
uncertainty, is for samples and measurements. An organization gets a plain point. The location field
sits on the contributor base model today, so a person has one too, though nothing sets it. A person's
place on a map is already taken from their primary affiliation's organization, and an individual's
own coordinates would be personal data with no use in research metadata. The field moves to the
organization.

An organization's point is entered in the same notations as a sample's coordinates, so there is one
way to type a latitude, but only in WGS 84. Every organization's point comes from ROR or from someone
reading a map, and neither uses a projected system.

*Revisit if:* a portal needs to place a person somewhere other than where they work.
**ADR:** none — stated on the locations and contributors pages; it follows from the spec's boundary

## D3. A measurement falls back to its sample's location, but only for a viewer who may open the sample

A measurement is usually made where its sample was taken, so asking for a location on every
measurement would ask for the same coordinates again and again. Its own location is optional, and
anything that asks where a measurement is gets its own location first and its sample's otherwise.

A measurement can belong to a different dataset from its sample, so it can be public while its
sample is private. Falling back without a check would let a visitor read the private sample's
location from the public measurement, or work it out from which area lookups return the
measurement. So the fallback applies only for a viewer who may open the sample. The measurement page
already follows this rule: it says the sample belongs to a dataset the visitor cannot see, and shows
no map.

*Revisit if:* a measurement's location needs to be set to its sample's, rather than inherited from
it, so that later edits to the sample do not move it.
**ADR:** docs/adr/0033-a-measurement-borrows-its-samples-location-only-for-a-viewer-who-may-open-the-sample.md

## D4. The API returns what a record holds, and no fallback

The API returns the location stored on the record. A measurement with no location of its own
returns none, and its sample's location is read from the sample, which the measurement links to. A
fallback in the API would make a measurement's location change when its sample's does, with nothing
in the measurement's response to say so, and would need the visibility rule of D3 in every
serializer. A harvester that wants the effective location follows the link, as it does for
everything else about the sample.

Locations are GeoJSON geometries (RFC 7946): WGS 84, longitude first, elevation as an optional third
coordinate. The uncertainty is not part of GeoJSON, so it sits beside the geometry as a number of
metres. Darwin Core calls the same value `coordinateUncertaintyInMeters`.

*Revisit if:* callers routinely request every measurement's sample only to read its location.
**ADR:** none — the API page documents what a measurement returns

## D5. A location is a point

A survey line, a cruise track or a mapped area needs a line or polygon geometry, and boreholes need
a depth interval. The maintainer agreed to keep the core to a point. A borehole is a point at its
collar, and a sample type that needs a depth interval, or a line, declares fields of its own.

*Revisit if:* several portals declare the same line or area field on their own sample types.
**ADR:** none — the spec's boundary states it

## D6. Coordinates are stored in WGS 84, entered in WGS 84, and shown to five places

Storing one system means every lookup, API response and export agrees without converting again,
and WGS 84 is what GeoJSON, DataCite and IGSN use. The form first accepted any reference system
with an EPSG code and converted on the way in, for a notebook that gives a UTM zone or a national
grid. The maintainer withdrew that after the walkthrough (D29): every coordinate is entered in
WGS 84. The coordinates as typed are the stored point, and nothing is kept beside it.

The point is kept as typed, without rounding. It is shown to five decimal places of a degree,
about a metre at the equator, which is finer than any field position the portals hold. How good a
location is, is recorded in its uncertainty, not in how many decimals it carries, so no precision is
recorded per location and the three precision settings go.

Elevation is metres above mean sea level as the researcher gives it, negative below.

*Revisit if:* a portal needs the coordinates exactly as recorded for provenance.
**ADR:** none — the locations page states what is stored and how it is shown

## D7. A location has no page of its own

`/location/<lon>/<lat>/` listed the samples sharing one `Point` row. With no shared row there is
nothing for it to be the page of, and "what else is near here" is a question for a map (#497) or a
within-distance lookup. The page, its address, its plugin and the collection tables' link to it go.

*Revisit if:* #497 needs an address for the records near a point.
**ADR:** none — a removal recorded in the changelog

## D8. Existing locations are not carried across the upgrade

The maintainer said no portal holds location data yet. The migration that replaces `Point` with the
new fields need not copy coordinates across.

*Revisit if:* a portal with location data upgrades before this lands.
**ADR:** none — local to this upgrade, nothing downstream inherits it

## D9. The move to PostGIS is its own issue

Moving the database to PostGIS, replacing the development SQLite database, making
`docker-compose.yml` work, running the test suite on PostGIS, and correcting the documents that
describe a setup that does not exist, gives no developer or user a new way to do anything. It is
tracked in #500, which lands first. It can be merged and proven on its own, before any location code
exists, and the suite passing on PostGIS is the proof. The shared test workflow starts no database
service, so FairDM gets a test workflow of its own.
**ADR:** none — a delivery decision; the PostGIS move has ADR 0031

## D10. DataCite gets a box, and a box may cross the 180th meridian

DataCite's `geoLocationBox` is a western and an eastern bound, each anywhere from -180 to 180, and
the schema does not require the western one to be the smaller. A box across the 180th meridian is
written with its western bound east of its eastern one, as ISO 19115 bounding boxes are. A box taken
from the minimum and maximum longitude turns a Pacific cruise into one that covers the globe, so
spatial coverage chooses the narrower of the two boxes that hold the locations. A polygon would
describe a dataset more closely, and is left until a repository the portals publish to needs one.
The box is what the export already writes. The dataset metadata template also refers to a centroid
the dataset model has never had, and that reference goes.

*Revisit if:* a repository the portals publish to indexes `geoLocationPolygon`.
**ADR:** none — moved to #511 with the DataCite story

## D11. Coordinates are read by `lat-lon-parser`

The maintainer asked for the available packages to be surveyed. `lat-lon-parser`, NOAA's public
domain parser with no dependencies, reads every notation the spec asks for. It does not check
ranges, which axis a hemisphere letter belongs to, or a trailing `s` after seconds, which it reads
as south, so the field adds those checks. The comparison is in research.md.

*Revisit if:* the package stops being maintained, or a notation the spec needs is not read.
**ADR:** none — a dependency choice local to one field, recorded in research.md

## D12. The fields are `location`, `location_elevation` and `location_uncertainty`

A sample type is a subclass of `Sample` in its own table, and cannot declare a field with a name
`Sample` already uses. Portals give their own sample types an `elevation` or a `depth`. Prefixing
the two new values with `location_` keeps them out of the way, and reads as part of the location.

*Revisit if:* never; renaming a field later breaks every portal that reads it.
**ADR:** none — a naming choice the model docstring and the locations page state

## D13. A geometry column, measured as geography for distance

A geography column bows a box's edges along great circles, so "inside this box" would not follow
the parallels a researcher means. A geometry column in WGS 84 keeps the box's edges straight in
latitude and longitude, and the distance lookups cast to geography, which measures on the
spheroid. An expression index on the cast keeps them indexed.

*Revisit if:* lines and areas come into the core, where geography's edges might be wanted.
**ADR:** none — follows from D1 and is stated on the locations page

## D14. The API returns locations and does not take them

The record serializers accept writes, but the spec asks only that a location be read (FR-029).
The location fields are read-only in the API, so a create or a change through the API leaves a
location as it was.

*Revisit if:* a portal needs to write locations through the API.
**ADR:** none — the API page documents the field as read-only

## D15. Design review findings, as applied

The plan was reviewed before any code was written: no critical or high findings, eight medium and
three low. Applied as plan and task edits: the API's location fields all read-only (SEC-001), the
coverage narrowing measurements by `visible_to` (SEC-002), the latitude and longitude columns not
sortable (ARCH-001), the geography indexes listed in each model's own `Meta` (ARCH-002), the three
references the removal grep misses (ARCH-003), an organization geography index and its query-plan
test (ARCH-004), the measurement area lookup as two subqueries (ARCH-005), the import columns
named after the model fields (SPEC-001), both organization forms given the point input (SPEC-003),
one written visibility rule for the effective location (ARCH-006), the admin left on the plain
`ModelAdmin` (ARCH-007), and the foreign keys replaced by `RemoveField` and `AddField` (ARCH-008).

Not applied: a test that `/location/<lon>/<lat>/` answers "not found" (SPEC-002). A removed route
gets no test of its own, in line with the project's testing standard. SC-007 is read as excluding
the changelog, which names the removed settings so a portal knows to stop setting them.

Nearest-first ordering stays on `Distance`, which PostgreSQL sorts after filtering. Changing it to
the `<->` operator is a watch item for US2, taken only if the query plan in T016 shows a sequential
scan for the lookups SC-005 names.

*Revisit if:* the merge-gate review finds one of these did not hold.
**ADR:** none — review record, local to this feature

## D16. The location constraints are listed in each concrete model's own Meta

**Decision:** `LocatedRecord.Meta` declares only `abstract = True`. `Sample.Meta` and
`Measurement.Meta` each set `constraints = location_constraints()`, next to their own indexes.

**Why:** A sample type that declares no `Meta` of its own, such as the demo's `CustomParentSample`
and `ExampleMeasurement`, inherits the abstract parent's `Meta`. Constraints declared there landed
on the child's table, which has none of the three columns, and `makemigrations` proposed a check
constraint that cannot be created. Declared on the two concrete models they exist once, on the
table that holds the columns.

**Revisit if:** a third concrete model gains the three fields.
**ADR:** none — a model-layout detail stated in the model's docstring

## D17. `Dataset.bbox` reads the samples' points until the spatial coverage replaces it

**Decision:** `Dataset.bbox` aggregates `Extent("location")` over the dataset's samples and returns
the four bounds, or None. `fairdm/contrib/location/utils.py` is deleted as planned.

**Why:** The DataCite template and an existing test read `dataset.bbox`, and its helper read the
removed `Point` rows. The spatial coverage of plan D6 is a later story.

**Revisit if:** the spatial coverage story lands, which deletes `bbox`.
**ADR:** none — temporary, and `bbox` was removed in a later story

## D18. Existing tests whose subject the story removes

**Decision:** Tests that only asserted the removed location page or its link column are deleted,
and tests that built a `Point` row were changed to pass a GEOS point. Three kinds were changed
beyond that:

- `TestARecordWithoutAUuid` and `TestMenusExistForAnyRecord` used the location page as the one
  record with no uuid. Both are deleted. Nothing else in the codebase calls
  `declare_addressing`, so the machinery now has no test and no caller.
- The profile-form tests added a person's `location`, which a person no longer has. They add
  `config`, a `Person` field the shipped form leaves out, and the guide's example does the same.
- `test_generated_form_carries_the_specimen_types_own_fields` expects `location` among the rock
  sample form's fields, because the demo registration lists it.

**Why:** Each assertion was kept or, where its subject is gone, removed with it.

**Revisit if:** the plugin system gains another record without a uuid, which would take the
addressing test back.
**ADR:** none — test housekeeping, local to this feature

## D19. Migration 0023 does not read the contributor's location column

**Decision:** The data step in `0023_levels_from_stored_permissions` loads people with
`defer("location")`.

**Why:** Its test runs the historical models of the state before it against a database built from
the current models. Once a later migration drops `contributors_contributor.location_id`, loading a
person selected a column that does not exist and all twenty-one cases failed. The step uses nothing
in that column, so a migration run in order behaves as it did.

**Revisit if:** the test is rewritten to build its database at the historical state.
**ADR:** none — local to one historical migration

## D20. The measurement page reads one named tuple, and an own location needs no query

**Decision:** `Measurement.effective_location_for(user)` returns an `EffectiveLocation` named tuple
of point, elevation, uncertainty and source, which is the four-part tuple of the plan with names.
It answers from the instance when the measurement has a location of its own, and otherwise reads
the `with_effective_location` annotation for its own row. The overview template drops the
`own_location` context value, which only the prototype had, and branches on
`effective_location.source`. The card's markup and copy are as approved.

**Why:** The sample's visibility rule lives in the annotation alone, so the page cannot disagree
with a lookup. A measurement with its own location never needs the sample, so that case costs no
query. Names read better in the template than positions.

**Revisit if:** a location has a third source, or a measurement's own location becomes hidden from
some viewers, which would put the own branch behind the annotation too.
**ADR:** none — a template-context detail, local to the measurement page

## D21. Measurement lookups are two `pk__in` subqueries joined by a SQL `UNION`

**Decision:** `MeasurementQuerySet.inside` and `within_distance` filter `pk__in` over the `UNION` of
the pks of the measurements whose own location matches and the pks of the measurements with none
whose sample, visible to the viewer, matches. They are not an `OR` of two `pk__in` conditions.

**Why:** `pk IN (a) OR pk IN (b)` makes the planner scan the measurement table with two hashed
subplans, which reads no spatial index. The `UNION` form lets each branch use its own index
(`measurement_location_*` and `sample_location_*`), and the plans in `TestQueryPlan` show it.

**Revisit if:** a viewer's `visible_to()` subquery makes a plan slow enough on a large portal that
the sample branch should be narrowed by dataset first.
**ADR:** none — a query-shape detail stated in the lookup's docstring

## D22. A project's coverage counts public datasets and those the viewer holds a level on

**Decision:** `Project.spatial_coverage(user)` takes the project's datasets that are public, plus
those the viewer holds at least the view level on (including a portal-wide view right), then
narrows their samples and measurements by `visible_to(user)` as `Dataset.spatial_coverage` does.

**Why:** It is the rule the dataset overview already uses for the siblings it counts, so the box
never covers a dataset the viewer could not open. A person who holds a level on one sample of a
private dataset still counts that sample on the dataset's own coverage but not on the project's,
because they may not open the dataset.

**Revisit if:** #510 changes what a project's visibility hides, since this builds on `visible_to`
as it is.
**ADR:** none — follows the rule the project overview already uses

## D23. The geometry helpers sit on one class, and the DataCite template reads the coverage

**Decision:** The lookups' input readers and the geography cast are static methods of `Spatial` in
`fairdm/contrib/location/managers.py`, so they are not public methods of every queryset that mixes
the lookups in. `datacite44.xml` reads `dataset.spatial_coverage` (no viewer) for the box and leaves
its `centroid` block for the DataCite story.

**Why:** The measurement queryset needs the same readers but not the mixin's methods, whose
signatures differ by the viewer. The template change is the least that removes the last reader of
`Dataset.bbox`.

**Revisit if:** a third queryset needs them, which would still be this class.
**ADR:** none — an internal code layout choice

## D24. One GeoJSON field reads the elevation from the record, and the API gains no elevation field

**Decision:** `GeoJSONPointField` reads the whole record and appends `location_elevation` as the
third coordinate when the record has the attribute and it is set. `location_elevation` is not a
field of its own in the API's responses. It is in `read_only_fields` so a type whose registration
lists it still cannot be written through it.

**Why:** A GeoJSON position carries its elevation, so a second field would say the same thing
twice. An organization has no such attribute, so the same field gives it a two-coordinate point
without a separate class.

**Revisit if:** a portal needs to write locations through the API (D14).
**ADR:** none — the API page documents the field

## D25. A resource expands `location` when it is built, and the point is read by the input's own field

**Decision:** `LocatedResourceMixin` replaces `location` in a resource's fields with the four
columns when the resource is created, and sets the point on import by passing the row's two
coordinates, elevation and uncertainty to `LocationField.compress`. The registry's resource
factory puts the mixin ahead of `ModelResource` only where the type's fields list `location`, and
`BaseFairDMResource` carries it for the hand-written resources.

**Why:** Import-export's field list is fixed when the class is defined, and a registered type's
field list is not known until the factory runs, so the one place that sees both is the
constructor. Reading the point through `LocationField` gives the import every rule and message of
the form (both coordinates or neither, no elevation without a point, no negative uncertainty)
without a second copy of them, and a refused row reaches import-export as a validation error, so
it is reported and not saved.

**Revisit if:** a resource needs a reference-system column (the import then needs the input's
first part, which `compress` already takes).
**ADR:** none — the locations page documents the columns

## D26. Each organization form declares the point-only field and keeps its point

**Decision:** `OrganizationProfileForm` in `forms/profile.py` and the two forms in
`forms/organization.py` each declare `location = LocationField(full=False, ...)` and a
`clean_location` that returns the cleaned value's point. There is no shared mixin and
`LocationFormMixin` is not used.

**Why:** An organization has no elevation or uncertainty, so the mixin's second job (writing them
to the instance) does not apply, and three one-line methods are smaller than a class a third
caller would have to inherit. The field is declared, not swapped in `__init__`, so a portal's
subclass can replace it like any other declared field.

**Revisit if:** a fourth organization form needs the same pair.
**ADR:** none — a form-layout detail, local to the organization forms

## D27. The DataCite story moved out of this feature

The story for a dataset's DataCite metadata (US7, #508) assumed the export worked. When the build
reached it, the template could not be rendered (it loads a `partials` tag library that is not
installed on Django 5.2) and no route serves it. Delivering the story meant repairing an export
unrelated to locations, so the maintainer had it taken out. It is #511, with the four acceptance
scenarios it carried. The spatial coverage it needs is delivered here, and the template already
reads it.

*Revisit if:* never; #511 owns it.
**ADR:** none — a scope change recorded in the spec's boundary and in #511

## D28. The import path caps a coordinate cell where the row is read, not in the coordinate widget

**Decision:** The 64-character cap on an imported coordinate sits in `LocatedResourceMixin.set_location`,
before the cell reaches `LocationField.compress`. `CoordinateWidget.clean` is left as it was.

**Why:** The coordinate fields have no model attribute, so import-export never calls the widget's
`clean` on import. A cap there was never reached: a 65-character latitude cell imported with it in
place. `set_location` is where the cells go to the parser.

**Revisit if:** the coordinate fields gain an attribute and import starts cleaning through the widget.
**ADR:** none — a placement detail of FIX-1

## D29. Coordinates are entered in WGS 84 only

**Decision:** The location input takes a latitude and a longitude in WGS 84, in any of the three
notations, plus an elevation and an uncertainty on the full input. It has no reference-system box,
no suggestions, no Northing and Easting labels and no conversion. Accepting other systems is #512.

**Why:** The maintainer, after the walkthrough: all coordinate input must be declared in WGS 84, and
for now the onus is on the person entering data to convert if necessary. A reference-system box asks
a researcher to know an EPSG code, and a wrong code converts to a plausible wrong place. Tabular
import already took WGS 84 only, so the form and the import now agree. What went: the projected
branch of the reading, the magnitude and converted-range checks that only guarded conversion, the
suggested systems, and the script's label switching. What stayed: the notation parser, the range and
hemisphere checks, the 64-character cap, the elevation and uncertainty rules and the "Reads as" hint.

**Revisit if:** #512 is taken up.
**ADR:** none, #512 decides whether input in other systems returns
