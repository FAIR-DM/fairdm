# Implementation Plan: capture, store and query locations as geospatial data

**Branch**: `030-geospatial-locations` | **Date**: 2026-10-14 | **Spec**: [spec.md](spec.md)

**Input**: [spec.md](spec.md), [research.md](research.md), [sketch.md](sketch.md),
[planning-notes.md](planning-notes.md), [decisions.md](decisions.md)

## Summary

Replace the shared `Point` table with three fields on every sample and every measurement, and a
point on every organization. Coordinates are typed in any of three notations and any EPSG system
through one form input, and stored in WGS 84. Samples, measurements and organizations gain area,
distance and nearest-first lookups, datasets and projects gain a spatial coverage, and the API,
tabular import and export and the DataCite metadata carry the new location. The prototype's screens
are kept. Everything behind them is rebuilt test first.

## Technical context

- Python 3.13, Django 5.2, GeoDjango on PostGIS 3.5 (since #500), django-polymorphic, DRF,
  drf-spectacular, django-import-export 4.4, crispy-forms with django-mvp's daisyUI templates
- New dependency: `lat-lon-parser` 1.3.1 (research, "Survey the available packages")
- Tests: pytest on PostGIS, `tests/` mirrors `fairdm/`
- No data migration: no portal holds location data (decisions D8)

## Constitution check

- Tests are written first and seen to fail (testing standard). No test pins wording or appearance.
- Documentation ships in the same pull request, in the story that introduces each public name.
- No compatibility alias for `Point`, `bbox` or the removed settings. No leading-underscore names.
- Breaking changes are listed in the changelog with what a portal has to change.

## Design

### D1. Three fields on each sample and measurement

`fairdm/contrib/location/models.py` holds one abstract model, `LocatedRecord`, and nothing else:

| Field | Type | Notes |
|---|---|---|
| `location` | `PointField(srid=4326, null=True, blank=True)` | GiST index from GeoDjango |
| `location_elevation` | `FloatField(null=True, blank=True)` | Metres above mean sea level |
| `location_uncertainty` | `FloatField(null=True, blank=True)` | Metres |

Its `Meta` declares two `CheckConstraint`s, named with `%(app_label)s_%(class)s_` prefixes: the
uncertainty is null or at least 0, and the elevation and uncertainty are null whenever the location
is. It also declares a `GistIndex` on `Cast("location", PointField(geography=True))`, which the
distance lookups use (research, "Geometry, not geography").

`Sample` and `Measurement` inherit it. Both already declare `indexes` in their own `Meta`, which
replaces an inherited list rather than adding to it, so each `Meta` lists the geography index
itself, next to its `modified` index, under a name of 30 characters or fewer
(`sample_location_geog_idx`, `measurement_location_geog_idx`). The constraints are declared on
`LocatedRecord.Meta` with `%(app_label)s_%(class)s_` names and each `Meta` inherits it. The names
do not clash with a portal's own sample fields (research, "Names that do not clash").

The sample's `location` changes from a foreign key to a point under the same name. The
autodetector would write that as an `AlterField`, which PostgreSQL cannot do from an integer to a
geometry, so the migration is written as `RemoveField` then `AddField`, and the same for the
contributor's.

`fairdm.contrib.location` keeps its app label, `fairdm_location`, so its migrations run in order.
Its migration `0002` deletes `Point` and depends on the sample and contributor migrations that
remove the foreign keys to it.

### D2. A point on each organization, none on a person

`Contributor.location` is removed. `Organization.location` is a `PointField(srid=4326,
null=True, blank=True)`, with a geography index of its own in `Organization.Meta`, since the
distance lookups of D4 run on organizations too (FR-020). `RORTransform.import_location` sets it to `Point(lng, lat)` and stops
creating shared rows. `Person.as_geojson()`, `Organization.as_geojson()` and the
`Organization.lat`/`lon` properties read the point's `y` and `x`. The ROR export address in
`transforms.py` reads the same.

### D3. One location input

In `fairdm/contrib/location/forms.py`:

- `parse_coordinate(text, axis)` wraps `lat_lon_parser.parse`. It refuses text the package cannot
  read, a hemisphere letter or word that belongs to the other axis, a value out of range for the
  axis, and minutes written with the letter `m` (research). Messages name the value and say what
  is accepted.
- `LocationField(MultiValueField)`, with `full=True` for reference system, two coordinates,
  elevation and uncertainty, and `full=False` for two coordinates in WGS 84. It cleans to `None`,
  or to a `Location(point, elevation, uncertainty)` named tuple whose point is in SRID 4326. A
  geographic system is read with `parse_coordinate`. A projected one reads two numbers as northing
  and easting. Anything else is converted with `GEOSGeometry.transform()`. An unknown code, a
  result outside WGS 84's range, one coordinate without the other, and an elevation or
  uncertainty without coordinates are refused (FR-005, FR-008).
- `LocationWidget(MultiWidget)` with the prototype's template, moved to
  `fairdm/contrib/location/templates/location/widgets/location.html` as it was approved.
  `decompress()` takes a `Location`. The suggested systems are a module constant of codes, each
  given its name and kind (`SpatialReference(code).name`, `.geographic`) when the widget renders.
  The script reads that list from a `json_script` element instead of its own copy. A code outside
  the list is labelled Northing and Easting until the form is saved, and the server decides.
- `LocationFormMixin` for a `ModelForm` whose model is a `LocatedRecord`. When `location` is in
  the form's fields, it replaces it with a full `LocationField`, starts it from the instance's
  three fields, and in `clean()` sets `location_elevation` and `location_uncertainty` on the
  instance and the point as the cleaned `location`, so that model validation sees all three
  together.

`SampleFormMixin` and `MeasurementFormMixin` use `LocationFormMixin`. A sample or measurement type
shows the input only when its registration lists `location` (FR-009). The measurement field's help
text is the prototype's. `OrganizationProfileForm` lists `location` in its "Location" section
under the label "Coordinates", with a `full=False` field, as approved. The two forms in
`forms/organization.py`, `OrganizationCreateForm` and the older profile form, list `location` too
and get the same `full=False` field (FR-010), rather than GeoDjango's default map widget.

The old `PointForm`, `LatitudeWidget`, `LongitudeWidget` and `normalize_coordinate` are deleted.

### D4. Lookups

`LocatedQuerySet` in `fairdm/contrib/location/managers.py` is a mixin with three methods. Each
returns a queryset, so it combines with any other filter, `visible_to()` included:

- `inside(area)`: `area` is a GEOS polygon or a `(west, south, east, north)` tuple in degrees.
  Filters on `location__coveredby`, so a point on the edge counts (spec edge case).
- `within_distance(point, distance)`: `distance` is a `D` or a number of metres. Filters on the
  geography cast with `dwithin`, measured on the spheroid.
- `nearest(point)`: annotates `distance` from the geography cast and orders by it, records with
  no location last.

`SampleQuerySet` and an `OrganizationQuerySet` mix it in. The polymorphic sample manager keeps its
existing chainable methods.

### D5. A measurement's effective location

`MeasurementQuerySet` mixes in its own version of the three lookups. Each takes the viewer,
`user=None` meaning a visitor who is not signed in:

- `inside(area, user=None)` is the union of two subqueries, `pk__in` the measurements whose own
  location is covered by the area, and `pk__in` those with none whose sample, visible to the
  viewer, is covered by it. Each subquery runs on one table, so each uses its own spatial index.
  An `OR` across the join would use neither.
- `with_effective_location(user=None)` annotates `effective_location` with `Case`: the
  measurement's own location, else its sample's when the sample is visible to the viewer, else
  null. `within_distance` and `nearest` work on that annotation. Collection tables use it too.

`Measurement.effective_location_for(user)` returns `(point, elevation, uncertainty, "own" |
"sample")` or `None`, for the measurement page. It reads the `with_effective_location` annotation
for its own row, so the visibility rule is written once (FR-014).

### D6. Spatial coverage

`fairdm/contrib/location/coverage.py` holds `Coverage(west, south, east, north)` and
`spatial_coverage(*querysets_and_fields)`. For each `(queryset, field)` pair it runs two
aggregates, `Extent(field)` and `Extent(Func(field, function="ST_ShiftLongitude"))`, merges the
boxes, and keeps the narrower of the two in longitude, converting longitudes above 180 back into
the range. A crossing box has `west > east` (FR-022, DataCite's convention). It returns `None`
when there is nothing located.

- `Dataset.spatial_coverage(user=None)`: the dataset's samples narrowed by
  `visible_to(user)`, and its measurements narrowed by `visible_to(user)` with their effective
  locations for the viewer (FR-023). A person holding a level on one record counts that record and
  nothing else in the dataset.
- `Project.spatial_coverage(user=None)`: the same over the datasets the viewer may open.

`Dataset.bbox` and `fairdm/contrib/location/utils.py` are deleted. The DataCite template's
`geoLocationBox` reads `dataset.spatial_coverage` with no viewer. Producing that metadata, and
testing it, is #511, because the export cannot be rendered or reached today.

### D7. Pages and tables

- `c-card.location` takes `location` (anything with `x` and `y`), `elevation` and `uncertainty`,
  as approved.
- The sample overview passes the sample's three fields. The measurement overview uses
  `effective_location_for(request.user)` and titles the card "Measurement location" or "Sample
  location" by its kind, as approved. The organization overview's `has_map` reads
  `organization.location is not None`.
- `SampleTable` reads `location.y` for Latitude and `location.x` for Longitude. The two columns
  are not orderable, because `location__y` is not a lookup on a geometry field.
  `MeasurementTable` reads the annotated `effective_location`, and the collections view annotates
  measurement querysets with `with_effective_location(request.user)`. The location link column and
  `render_location` are gone.
- The registry's table factory leaves out any `GeometryField`, since the base tables carry the
  latitude and longitude.
- The location page, its URLs, plugin, address declaration, view, template and admin are deleted.
  `/location/<lon>/<lat>/` answers "not found" because nothing routes it.
- `SampleAdmin` and `MeasurementAdmin` show the three fields. The location leaves
  `autocomplete_fields`. Querysets that `select_related` the old foreign key
  (`SampleQuerySet.with_related()`, the measurement collection view) stop naming it, since the
  location is now a column on the row.

### D8. Settings and factories

`FAIRDM_CRS`, `FAIRDM_X_COORD` and `FAIRDM_Y_COORD` are removed from the settings modules.
`PointFactory` is removed. `RockSampleFactory` and the other sample factories take
`location=GEOSPoint(...)`, with a `factory.Trait` or a `LazyFunction` for a random WGS 84 point
where a test wants one. Existing tests that build a `PointFactory` are changed to pass a point.

### D9. API

`GeoJSONPointField` in `fairdm/api/serializers.py` is a read-only DRF field. Given a record, it
returns `{"type": "Point", "coordinates": [lon, lat]}` with the elevation appended when there is
one, or `None`. It is annotated for drf-spectacular as a GeoJSON point. `BaseSampleSerializer` and
`BaseMeasurementSerializer` add `location` and `location_uncertainty` to `common_fields`.
`OrganizationListSerializer` adds `location` without elevation. A measurement returns its own
location only (decisions D4). The location is read-only: `location`, `location_elevation` and
`location_uncertainty` are all in `read_only_fields`, so a write through the API leaves them as
they were and never reaches the database constraint (decisions D14).

### D10. Tabular import and export

Where a sample or measurement resource's fields include `location`, the resource factory expands
it into four columns, `latitude`, `longitude`, `location_elevation` and
`location_uncertainty`. The last two carry the model fields' names, so they do not collide with an
`elevation` column a sample type declares of its own. Each is an
import-export `Field` with a widget in `fairdm/contrib/location/resources.py`. Export writes the
record's own values in WGS 84 decimal degrees. Import reads the two coordinates with
`parse_coordinate` and sets the three model fields, and a refused value is reported as that row's
error with the message the form gives. No resource exports a location as a table of its own
(FR-033).

### D11. Documentation and records

- A new page, `docs/portal-development/locations.md`, describing the three fields, the input and
  the notations it reads, the lookups with examples, the effective location, the spatial coverage,
  the API shape and the import columns. It is linked from the portal development table of
  contents. Each story extends the page for its own surface.
- `CONTEXT.md` gains Location, Reference system and Spatial coverage. FS-005, FS-011, FS-018 and
  FS-019 are edited where they describe a location (spec assumptions).
- `CHANGELOG.md`: added, changed and removed entries, with every breaking change in the spec.
- ADR 0032 records D1 of `decisions.md`: a location is a value on each record, not a shared row.

### D12. Demo

The demo's seeds set the three fields instead of `options`. The XRF measurement registration lists
`location`, so the measurement input shows in the demo. `demo/plugins.py` and `demo/models.py`
read `location.y` and `location.x`.

## Story order

US1 first, because it carries the fields, the removal of `Point` and the input every other story
reads. Then US3 and US2, which share the effective location and the coverage. Then US4, US5 and
US6. Each story starts from the previous one's accepted commit.

## Risks

- **Every test that builds a `Point`** changes in US1. The changes are mechanical and listed in its
  tasks. Each one keeps what its test asserts.
- **Multi-table polymorphism**: a lookup on `Sample.objects` runs on the base table, which holds
  the location column, so a lookup across every sample type is one query. A lookup on a concrete
  type joins its base row as any query on it does.
- **The geography cast index** must match the expression the lookups use exactly, or PostgreSQL
  will not use it. SC-005 checks the query plan.
