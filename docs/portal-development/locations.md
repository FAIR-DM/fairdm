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
point, and refuses a negative uncertainty. The point is stored as it was typed, without
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

from fairdm.utils.location.forms import LocationFormMixin


class RockSampleForm(LocationFormMixin, forms.ModelForm):
    class Meta:
        model = RockSample
        fields = ["name", "location"]
```

When `location` is among the fields, the form replaces it with a `LocationField`, starts it from
the instance's point, elevation and uncertainty, and on clean puts the elevation and uncertainty
on the instance. Clearing the coordinates clears all three.

## Placing an organization

An organization's form asks for **Coordinates**: a latitude and a longitude in WGS 84, with no
elevation or uncertainty. Both are signed decimal degrees, as the sample input reads them (see
[What the input reads](#what-the-input-reads)). Leaving both empty gives the organization no point.
One coordinate without the other is refused.

The profile editing page (`OrganizationProfileForm`), the form that adds an organization
(`OrganizationCreateForm`) and the older profile form in `forms/organization.py` all use this
input. Each declares a `LocationField(full=False)` and keeps the point of its cleaned value, so a
form of your own does the same:

```python
from fairdm.utils.location.forms import LocationField


class MyOrganizationForm(forms.ModelForm):
    location = LocationField(full=False, label="Coordinates")

    class Meta:
        model = Organization
        fields = ["name", "location"]

    def clean_location(self):
        location = self.cleaned_data["location"]
        return location.point if location is not None else None
```

An organization created or updated from ROR takes the coordinates ROR publishes for it, and an
organization ROR gives none for keeps the point it had. Two organizations at the same coordinates
each hold their own point, so moving one leaves the other where it was.

The organization's page shows a map when it has a point and none when it does not. A person is
placed on a map at their primary affiliation's organization's point, and not placed when that
organization has none.

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
combines with any other filter, `visible_to()` included, in either order. A measurement's lookups
are the exception, described under [Measurements](#measurements).

`inside(area)` takes a GEOS polygon, or a `(west, south, east, north)` tuple in degrees. A point on
the edge counts as inside, and a record with no location is never inside. A tuple whose west is
greater than its east is a box across the 180th meridian, as `spatial_coverage` returns it:

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

`visible_to()` does not tell the lookup who is asking, so pass the viewer to both. Without `user=`
the lookup answers for a visitor, and a measurement placed only by a sample the member may open is
left out:

```python
Measurement.objects.visible_to(request.user).inside(area, user=request.user)
```

### Why the lookups are fast

`inside` and `within_distance` read a spatial index, not the whole table. The distance lookups cast
the point to a geography, and the index they use is built on that same cast, which is what
`geography_index` returns. A measurement's `inside` and `within_distance` are two subqueries, one
on the measurement table and one on the sample table, each using its own index. A model of your own
that mixes in `LocatedQuerySet` from `fairdm.utils.location.managers` and lists the index in its
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

For records of your own, `spatial_coverage` in `fairdm.utils.location.coverage` takes any number
of `(queryset, field)` pairs and merges them into one box:

```python
from fairdm.utils.location.coverage import spatial_coverage

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

## In import and export

A registered type whose `fields`, or whose `resource_fields`, list `location` gets four columns in
its import and export file, in place of one:

| Column | Holds |
|---|---|
| `latitude` | Degrees north, or south when negative |
| `longitude` | Degrees east, or west when negative |
| `location_elevation` | Metres above mean sea level |
| `location_uncertainty` | Metres, zero or more |

The last two carry the model fields' names, so they cannot collide with an `elevation` column a
type declares of its own. A location is never exported or imported as a table of its own.

An export writes each record's own values, as WGS 84 decimal degrees, and leaves the four cells
empty for a record that has none. A measurement never writes its sample's location, so one with no
location of its own has four empty cells even when its sample is placed.

```csv
id,name,latitude,longitude,location_elevation,location_uncertainty
31,RS-14,49.0094,8.4115,112.5,25.0
32,RS-15,,,,
```

An import reads `latitude` and `longitude` as signed decimal degrees, such as `49.0094` or
`-8.4115`, with the same ranges as the location input. The cells are always WGS 84, as the input's
are: the file has no reference-system column, so convert projected coordinates first, and write
degrees, minutes and seconds as decimal degrees. Elevation and uncertainty are plain numbers.

A row the input would refuse is reported with the input's own message and is not saved. The rest of the file is read as usual. A row is refused when:

- a coordinate is not a number, or lies outside its range,
- one coordinate is given without the other,
- an elevation or an uncertainty is given with no coordinates,
- the uncertainty is negative.

A file that has none of the four columns leaves every record's location as it was, and a file with
only some of them changes only those. An empty cell clears the value. Clearing a point also clears
the elevation and uncertainty, so a file that empties `latitude` and `longitude` for a record that
holds an elevation or an uncertainty has to carry those two columns as well, with empty cells.
A file with only the two coordinate columns is refused for that row, since an elevation or an
uncertainty cannot be left without a point.

A resource that derives from `fairdm.contrib.import_export.resources.BaseFairDMResource` gets the
same columns where its fields list `location`. A `ModelResource` of your own gets them by
inheriting `fairdm.utils.location.resources.LocatedResourceMixin` ahead of `ModelResource`.

The columns are built from these pieces in `fairdm.utils.location.resources`, which a resource
that declares its columns by hand can use directly:

| Name | Is |
|---|---|
| `location_fields()` | The four import-export fields, keyed by column name, in column order |
| `CoordinateField` | The `latitude` or `longitude` field: `CoordinateField("lat")` or `CoordinateField("lon")` |
| `MeasureWidget` | Reads a number cell, and writes the number itself, or an empty cell for none |

## What the input reads

The input takes a latitude and a longitude, an elevation and an uncertainty. Every coordinate is
entered as a signed decimal number of degrees in WGS 84, the system a GPS receiver records. South
and west are negative: `49.0094` and `-8.4115`. There is no reference-system input and there are no
degrees, minutes and seconds, no minutes and no hemisphere letters. A researcher whose coordinates
are in a projected system, such as a UTM zone, or in another notation converts them first (other
systems are #512, other notations #513).

The input refuses, and saves nothing, when:

- a coordinate is not a number, or lies outside its range: latitude beyond 90, longitude beyond 180,
- one coordinate is given without the other,
- an elevation or an uncertainty is given with no coordinates,
- the uncertainty is negative.

## Reading coordinates in your own code

`LocationField` is a `MultiValueField`. `full=False` asks for a latitude and a longitude
only, as an organization's point does. It cleans to `None` when everything is empty, and otherwise
to a `Location` named tuple whose point is in SRID 4326:

```python
from fairdm.utils.location.forms import LocationField

field = LocationField()
location = field.clean(["49 0.564 N", "8 24.69 E", "112", "5"])
location.point.srid  # 4326
location.elevation  # 112.0
location.uncertainty  # 5.0
```

The list is the input's parts in order: latitude, longitude, elevation, uncertainty.

`LocationWidget` is the input a `LocationField` draws, with `full=False` for the point-only
variant. Its template is `location/widgets/location.html`.

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
