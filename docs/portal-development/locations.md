# Locations

A sample and a measurement can say where they are. The place is three fields on the record itself.
Nothing is shared: two samples taken at the same coordinates each hold their own copy, and
correcting one never moves the other.

| Field | Type | Holds |
|---|---|---|
| `location` | `PointField`, SRID 4326 | A point in WGS 84, longitude first |
| `location_elevation` | `FloatField` | Metres above mean sea level, negative below it |
| `location_uncertainty` | `FloatField` | Metres from the point within which the true place lies, zero or more |

All three are optional. The database refuses an elevation or an uncertainty on a record that has no
point, and refuses a negative uncertainty. The point is stored as it was converted, without
rounding. Pages show it to five decimal places, about one metre.

An organization holds a plain `location` point, with no elevation and no uncertainty. A person has
no location of their own: where a person is placed on a map, the point is their primary
affiliation's organization's.

## Setting a location in code

Pass a GEOS point in WGS 84:

```python
from django.contrib.gis.geos import Point

sample = RockSample.objects.create(
    name="GPK-2 core, 3512 m",
    dataset=dataset,
    location=Point(8.4115, 49.0094, srid=4326),
    location_elevation=112,
    location_uncertainty=5,
)
sample.location.y  # latitude, 49.0094
sample.location.x  # longitude, 8.4115
```

Read the coordinates with `.y` for latitude and `.x` for longitude. A point is not a model, so it
has no page, no address and no primary key.

## Showing the input in a sample type's form

A sample type gets the location input when its registration lists `location` among its fields, and
none when it does not:

```python
@fairdm.register
class RockSampleConfig(ModelConfiguration):
    model = RockSample
    fields = ["name", "rock_type", "location"]
```

A hand-written sample form uses `SampleFormMixin`, which carries the input, and a measurement form
uses `MeasurementFormMixin`. Either is `LocationFormMixin` plus the dataset and sample choices, and
`LocationFormMixin` on its own does the same for any `ModelForm` whose model has the three fields:

```python
from django import forms

from fairdm.contrib.location.forms import LocationFormMixin


class RockSampleForm(LocationFormMixin, forms.ModelForm):
    class Meta:
        model = RockSample
        fields = ["name", "location"]
```

When `location` is among the fields, the form replaces it with a `LocationField`, starts it from
the instance's point, elevation and uncertainty, and on clean puts the elevation and uncertainty
on the instance. Clearing the coordinates clears all three.

## A measurement's own location and its effective location

A measurement is usually made where its sample was taken, so most measurements record no location
of their own. A measurement type lists `location` in its registration to offer the input, for the
reading taken in the field at a site some distance from the core it belongs to:

```python
@fairdm.register
class XRFMeasurementConfig(BaseMeasurementConfiguration):
    model = XRFMeasurement
    fields = ["location", "element", "concentration_ppm"]
```

The measurement's own location is a value on the measurement and nothing more. Changing its
sample's location leaves it where it was, and the reverse.

A measurement's *effective location* is its own where it has one, and its sample's otherwise. The
sample's counts only for a viewer who may open the sample, which is the rule
`Sample.objects.visible_to(user)` applies. For anyone else a measurement with no location of its own
has none, so a published measurement never gives away where an unpublished sample was taken.

Ask for it on one measurement with `effective_location_for`, which takes the viewer, or `None` for a
visitor who is not signed in:

```python
found = measurement.effective_location_for(request.user)
if found is not None:
    found.point.y  # latitude
    found.point.x  # longitude
    found.elevation, found.uncertainty
    found.source  # "own" or "sample"
```

It returns an `EffectiveLocation` named tuple of the point, the elevation, the uncertainty and
`source`, which says whose location it is, or `None`. The measurement's page uses it to title the
card as the measurement's own location or its sample's.

For a queryset, `with_effective_location` annotates each measurement with `effective_location`, a
WGS 84 point or `None`, by the same rule and in the same query:

```python
for measurement in Measurement.objects.with_effective_location(request.user):
    measurement.effective_location
```

## Finding records by where they are

Samples and organizations carry three lookups on their queryset. Each returns a queryset, so it
combines with any other filter, `visible_to()` included, in either order.

`inside(area)` takes a GEOS polygon, or a `(west, south, east, north)` tuple in degrees. A point on
the edge counts as inside, and a record with no location is never inside:

```python
from django.contrib.gis.geos import Point, Polygon

Sample.objects.inside((8.0, 47.0, 9.0, 48.0))
Sample.objects.inside(Polygon(((0, 40), (20, 40), (10, 60), (0, 40)), srid=4326))
```

`within_distance(point, distance)` takes a point and a distance, as a `D` or as a number of
metres. The distance is measured on the ground, so a kilometre is a kilometre near the equator and
near a pole:

```python
from django.contrib.gis.measure import D

karlsruhe = Point(8.4037, 49.0069, srid=4326)
Sample.objects.within_distance(karlsruhe, D(km=5))
Sample.objects.within_distance(karlsruhe, 5_000)
```

`nearest(point)` orders by distance from a point, nearest first, and gives each record a
`distance`, a `D`. Records with no location come last and carry `None`:

```python
for sample in Sample.objects.visible_to(request.user).nearest(karlsruhe)[:10]:
    sample.distance.km
```

Organizations have the same three lookups on `Organization.objects`, whose queryset is
`OrganizationQuerySet`. A person has no location, so none of them applies.

### Measurements

A measurement is found by its effective location, so its lookups take the viewer as well:
`inside(area, user=None)`, `within_distance(point, distance, user=None)` and
`nearest(point, user=None)`. `user=None` is a visitor who is not signed in.

```python
Measurement.objects.inside((8.0, 47.0, 9.0, 48.0), user=request.user)
Measurement.objects.nearest(karlsruhe, user=request.user)
```

A measurement with a location of its own is found by that one. A measurement with none is found by
its sample's location, but only for a viewer who may open the sample. For anyone else it has no
location and no area contains it, so a lookup never gives away where an unpublished sample was
taken.

### Why the lookups are fast

`inside` and `within_distance` read a spatial index, not the whole table. The distance lookups cast
the point to a geography, and the index they use is built on that same cast, which is what
`geography_index` returns. A measurement's `inside` and `within_distance` are two subqueries, one
on the measurement table and one on the sample table, each using its own index. A model of your own
that mixes in `LocatedQuerySet` from `fairdm.contrib.location.managers` and lists the index in its
`Meta` gets the same.

## Spatial coverage

A dataset's spatial coverage is the smallest box that holds the locations of its samples and its
measurements. Ask for it with `spatial_coverage`, which takes the viewer, or `None` for a visitor:

```python
coverage = dataset.spatial_coverage(request.user)
if coverage is not None:
    coverage.west, coverage.south, coverage.east, coverage.north
```

It returns a `Coverage` named tuple of `west`, `south`, `east` and `north` in WGS 84 degrees, or
`None` when nothing the viewer may see has a location. Only what the viewer may open counts,
measurements included: a measurement placed only by a sample the viewer may not open adds nothing,
and a person who holds a level on one sample counts that sample and no other.

Locations on both sides of the 180th meridian give a narrow box, not one that spans the globe.
Such a box has `west` greater than `east`, which is how DataCite writes it:

```python
# Samples at 176 and -176 degrees longitude
coverage.west, coverage.east  # (176.0, -176.0)
```

A project's coverage is the same over the datasets the viewer may open: the public ones and those
the viewer holds a level on.

```python
project.spatial_coverage(request.user)
```

For records of your own, `spatial_coverage` in `fairdm.contrib.location.coverage` takes any number
of `(queryset, field)` pairs and merges them into one box:

```python
from fairdm.contrib.location.coverage import spatial_coverage

spatial_coverage(
    (Sample.objects.filter(dataset=dataset), "location"),
    (Organization.objects.all(), "location"),
)
```

A dataset no longer has a bounding-box property. Use `spatial_coverage()`, whose `west` and `east`
stand where the property's `min_x` and `max_x` did.

## In the API

A sample and a measurement return `location` and `location_uncertainty`, and an organization
returns `location`. A person returns neither.

```json
{
  "name": "RS-14",
  "location": {"type": "Point", "coordinates": [8.4115, 49.0094, 112.5]},
  "location_uncertainty": 25.0
}
```

- `location` is a GeoJSON `Point` in WGS 84 with longitude first, and the record's elevation as the
  third coordinate when it holds one. It is `null` for a record with no location.
- `location_uncertainty` is in metres and sits beside the geometry, since GeoJSON has no place for
  it. It is `null` when none is recorded.
- A measurement returns only its own location. One with none of its own returns `null`, and the
  sample's place is read from the sample its `sample` address points to.
- All three fields are read-only. A request that sends one leaves the record's location as it was.

The schema at `/api/v1/schema/` describes `location` as a GeoJSON point. A registered type that
lists `location` in its fields gets the same field. See
[A record's location](restful-api.md#a-records-location) on the API page.

## In the collection tables

The listing of a sample or measurement type has a Latitude and a Longitude column, and no location
column. A sample's columns read its own point. A measurement's read its effective location for the
viewer, so a visitor sees a measurement placed by its sample only where the visitor may open the
sample. Neither column sorts, since a point has no order. A registered type's `table_fields` may
list `location`: the generated table leaves any geometry field out, because the two columns are
always there.

## What the input reads

The input takes a reference system, two coordinates, an elevation and an uncertainty. The
reference system is an EPSG code and defaults to 4326, WGS 84. The coordinates are read in
the system's own notation:

| Typed | Read as |
|---|---|
| `49.0094` | decimal degrees |
| `49 0.564 N` | degrees and decimal minutes |
| `49°0'33.84"N`, `N 49 0 33.84` | degrees, minutes and seconds |
| `49.0094 South`, `S49.0094`, `-49.0094` | the southern hemisphere |

A hemisphere letter or word can stand in front or behind. Latitude and longitude are each read in
their own notation, so they need not match. Minutes written with the letter `m` are refused,
because a trailing `s` after seconds would then read as south.

A projected system, such as ETRS89 / UTM zone 32N (EPSG 25832), takes a northing in the first box
and an easting in the second, in metres. Whatever was typed is converted to WGS 84 before it is
saved. Elevation is never converted.

The input refuses, and saves nothing, when:

- a coordinate cannot be read, or lies outside its range: latitude beyond 90, longitude beyond 180,
- a hemisphere belongs to the other axis, as in a latitude ending in `E`,
- the EPSG code is unknown,
- the coordinates lie outside the area the system covers,
- one coordinate is given without the other,
- an elevation or an uncertainty is given with no coordinates,
- the uncertainty is negative.

## Giving a model of your own the three fields

`Sample` and `Measurement` inherit `LocatedRecord`, an abstract model that holds the three fields.
A portal model that is neither can inherit it as well. List the two check constraints and the
geography index in the model's own `Meta`, because a `Meta` that sets `indexes` replaces an
inherited list, and a subclass without a `Meta` would copy constraints onto a table that has none
of the columns:

```python
from django.db import models

from fairdm.contrib.location.models import (
    LocatedRecord,
    geography_index,
    location_constraints,
)


class Station(LocatedRecord):
    name = models.CharField(max_length=50)

    class Meta:
        constraints = location_constraints()
        indexes = [geography_index("station_location_geog_idx")]
```

`location_constraints()` returns the two checks that keep an elevation or an uncertainty from
standing without a point and an uncertainty from being negative. `geography_index(name)` returns
the index distance lookups use, which casts the point to a geography. The name is 30 characters
or fewer.

## Reading coordinates in your own code

`parse_coordinate` reads one coordinate for one axis, and raises a `ValidationError` with a code of
`invalid`, `out_of_range`, `wrong_axis` or `minutes_letter`:

```python
from fairdm.contrib.location.forms import parse_coordinate

parse_coordinate("49 0.564 N", "lat")  # 49.0094
parse_coordinate("8 24 41.4 E", "lon")  # 8.4115
```

`LocationField` is a `MultiValueField`. `full=False` asks for a latitude and a longitude in WGS 84
only, as an organization's point does. It cleans to `None` when everything is empty, and otherwise
to a `Location` named tuple whose point is in SRID 4326:

```python
from fairdm.contrib.location.forms import LocationField

field = LocationField()
location = field.clean(["25832", "5428667", "456964", "112", "5"])
location.point.srid  # 4326
location.elevation  # 112.0
location.uncertainty  # 5.0
```

The list is the input's parts in order: reference system, first coordinate, second coordinate,
elevation, uncertainty.

`LocationWidget` is the input a `LocationField` draws, with `full=False` for the point-only
variant. It suggests the codes in `SUGGESTED_SYSTEMS` and reads from the server which of them are
typed as degrees, so the page's script and the server agree. Its template is
`location/widgets/location.html`.

## Upgrading

A sample's `location` used to be a foreign key to a shared `Point`. It is now a point, and existing
locations are not carried across. A portal that holds locations has to write them again:

- Code that reads `location.latitude` or `location.longitude` reads `location.y` and `location.x`.
- Code that filters on `location__x`, `location__y` or `location__crs` has to change.
- `FAIRDM_CRS`, `FAIRDM_X_COORD` and `FAIRDM_Y_COORD` are gone.
- A contributor's `location` is gone. An organization has a point of its own.
- The page at `/location/<lon>/<lat>/` is gone, and so is the link to it in the collection tables.
- A dataset's bounding-box property is gone. `Dataset.spatial_coverage()` returns a `Coverage` with
  `west`, `south`, `east` and `north`.
