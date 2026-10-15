# Research: capture, store and query locations as geospatial data

Written 2026-10-14 against `origin/main` at `c9c12314`, after the prototype was approved.

## The maintainer's planning note

### Survey the available packages

**Adopted.** Each part of the feature was checked against what Django, GeoDjango and published
packages already provide before any new code was planned.

| Need | Found | Verdict |
|---|---|---|
| Store a point, index it, query it | GeoDjango's `PointField`, PostGIS GiST indexes, the `coveredby`, `dwithin` and `distance` lookups, `Distance` and `Extent` | Use GeoDjango. Nothing to add |
| Convert from any EPSG system to WGS 84 | GeoDjango's `GEOSGeometry.transform()` over GDAL and PROJ, installed since #500 | Not used: coordinates are entered in WGS 84 only (D29, #512) |
| Read coordinates typed in three notations | [`lat-lon-parser`](https://pypi.org/project/lat-lon-parser/) 1.3.1 was surveyed and first adopted; `LatLon23` was the alternative (GPL) | Not used: coordinates are entered as signed decimal degrees (D29, #513), which Django's `FloatField` reads with `MinValueValidator` and `MaxValueValidator` |
| A form input for a location | Django's GIS form widgets (`OSMWidget`, `OpenLayersWidget`) draw a map to click on and take no typed coordinates. `django-map-widgets` is the same idea with Google or Mapbox | Not adopted. The approved screen is typed coordinates, so the input is a `MultiValueField` and `MultiWidget` of our own, which is how Django composes one |
| GeoJSON in the API | [`djangorestframework-gis`](https://pypi.org/project/djangorestframework-gis/) 1.3.0 (2026-09, BSD, needs DRF below 3.19, which fairdm's 3.18.1 meets) gives a `GeometryField`. The elevation is a separate column, so the third coordinate has to be composed whichever field is used | Not adopted. One read-only field that writes `{"type": "Point", "coordinates": [...]}` from three model values is a few lines over `GEOSGeometry.coords`, and a dependency for it was removed in #196 |
| Location columns in tabular import and export | `django-import-export` 4.4.1 has no geometry widget | One `Widget` per column, with the coordinates read by the form's own field |
| Spatial coverage across the 180th meridian | PostGIS `ST_Extent` takes the minimum and maximum longitude. `ST_ShiftLongitude` moves western longitudes past 180 | Two `Extent` aggregates, one on the shifted points, and the narrower box kept. No package does this |

## What the prototype asks for

Every line under *What the screens need from the code* and *What the sketch faked* in
[sketch.md](sketch.md), and how the plan meets it:

| Prototype line | Met by |
|---|---|
| An input reading decimal degrees in WGS 84 | `LocationField` (plan D3) on Django's number fields and GeoDjango |
| Latitude and Longitude | The boxes are always Latitude and Longitude, in WGS 84 (D29) |
| The stored location back in decimal degrees | The widget's `decompress` reads the three model fields |
| Elevation and uncertainty on the sample page | Two fields on the record (plan D1) |
| The measurement's own location, and its sample's for a viewer who may open the sample | `Measurement.located_for()` (plan D5) |
| A plain point on an organization | `Organization.location`, with the WGS 84-only input (plan D2) |
| Latitude and longitude the right way round in the tables, the measurement table on the effective location | Columns read `location.y` and `location.x`, the measurement table reads the annotated effective location (plan D7) |
| No repeated Location column | The table factory leaves a geometry field out and the base tables carry latitude and longitude |
| Faked: elevation, uncertainty and the measurement's location in `options` | Model fields. The demo's seeded `options` go |
| Faked: the shared `Point` table | Removed (plan D1, D8) |
| Faked: the measurement input on every measurement form | Shown only when the registration lists `location`, as for samples (FR-009) |
| Faked: the hard-coded list of geographic codes in the script | Gone with the reference-system box (D29) |
| Faked: a second parser in the browser | Not needed: the boxes are number inputs and the browser's own range check applies. The server's check is the one that decides |
| Faked: the table factory dropping `location` by name | Dropped by field type, any `GeometryField` |
| Faked: the location page still served | Removed (FR-028) |

## What already exists

One line for each piece of new code, with where the search stopped.

- **Point, elevation and uncertainty fields** — Django and GeoDjango: `PointField`, `FloatField`,
  `CheckConstraint`.
- **Area lookup** — GeoDjango: `coveredby`, which counts a point on the edge as inside, where
  `within` does not.
- **Distance lookup and nearest first** — GeoDjango: `dwithin` and `Distance` on a geography cast,
  `D(m=...)`.
- **Measurement's effective location** — Django: `Coalesce`, `Case` and `When` over the sample's
  location, filtered by the existing `Sample.objects.visible_to()`.
- **Spatial coverage** — GeoDjango `Extent`, plus `Func(function="ST_ShiftLongitude")`. New code
  only for choosing the narrower box.
- **Coordinate parsing** — Django's `FloatField` with range validators; nothing of our own.
- **Conversion between reference systems** — not needed; coordinates are entered in WGS 84 (D29).
- **The location input** — Django `MultiValueField` and `MultiWidget`. New code: the field, the
  widget and its template.
- **GeoJSON in the API** — DRF `Field`. New code: one read-only serializer field.
- **Import and export columns** — `django-import-export` `Field` and `Widget`. New code: the four
  columns.
- **The location card** — the existing `c-card.location` component, extended with elevation and
  uncertainty.
- **ROR coordinates** — the existing `RORTransform.import_location`, writing a point instead of a
  shared row.
- **The admin** — GeoDjango's `GISModelAdmin`, which draws a point field on a map without any
  configuration.

## Everything else the plan needed settled

### Geometry, not geography, for the column

A geography column measures distance in metres along the Earth, but its polygon edges are great
circles. A box from 40° to 50° N drawn in geography bows away from the 50th parallel, so "inside
this box" would not mean what a researcher drawing it means. A geometry column in WGS 84 keeps
the box's edges on the parallels and meridians, and the distance lookups cast the point to
geography, which measures on the spheroid. An expression GiST index on that cast keeps the
distance lookups indexed (FR-020).

### Names that do not clash with a sample type's own fields

Samples are a multi-table polymorphic model, so a sample type cannot declare a field with the same
name as one on `Sample`. Portals already declare `elevation` and `depth` on their own sample types
(the Global Heat Flow Database portal's sites carry an elevation). The new fields are named
`location`, `location_elevation` and `location_uncertainty`, so that none of them takes a name a
portal is likely to have used.

### The shared rows go

`Point` stops existing. The sample and contributor foreign keys are replaced by fields, the
location page, its plugin, its address and its admin are removed, and the migration that drops the
table runs after the two that remove the keys. No data is carried across (decisions D8).

### The API stays read-only for locations

The API serializers for records accept writes. The location is returned and not written, because
the spec asks only that it be read (FR-029). Writing it is a later question.

### Visibility

`Sample.objects.visible_to(user)` and `Measurement.objects.visible_to(user)` exist and decide
every page. A measurement's fallback to its sample's location is a subquery on
`Sample.objects.visible_to(user)`, so the rule a viewer meets on the measurement page is the same
rule every lookup, every table and the spatial coverage meet.
