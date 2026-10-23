# Location fields

A sample and a measurement can say where they are, and an organization can say where it is based. This page describes the model fields that hold a location, the form field and widget that read one, the queryset lookups that find records by place, the spatial coverage of a dataset, and the columns, API fields and table columns that carry a location. For the reasoning, see [How locations are stored and protected](../../explanation/how-locations-are-stored-and-protected.md). For the tasks, see [How to give a sample or measurement a location](../how-to/give-a-registered-type-a-location.md), [How to find records by where they are](../how-to/find-records-by-where-they-are.md), [How to place an organization on a map](../how-to/place-an-organization-on-a-map.md) and [How to import and export locations](../how-to/import-and-export-locations.md).

## Model fields

A `Sample` and a `Measurement` carry three fields of their own. An `Organization` carries `location` only. A `Person` carries none.

| Field | Type | Default | What it holds | What it accepts |
|---|---|---|---|---|
| `location` | `PointField`, SRID 4326 | `None` | A point in WGS 84, longitude first | A GEOS `Point`, or nothing |
| `location_elevation` | `FloatField` | `None` | Metres above mean sea level | Any number, negative below sea level. Needs a `location`. |
| `location_uncertainty` | `FloatField` | `None` | Metres from the point within which the true place lies | Zero or more. Needs a `location`. |

All three are optional. The database refuses an elevation or an uncertainty on a record that has no point, and it refuses a negative uncertainty. The point is stored as it was given, without rounding. Pages show it to five decimal places, about one metre.

`Organization` also has the properties `lat` and `lon`, which are `None` when it has no point.

```python
from django.contrib.gis.geos import Point

sample = CoreSample.objects.create(
    name="Core 14, 3512 m",
    dataset=dataset,
    location=Point(8.4115, 49.0094, srid=4326),
    location_elevation=112,
    location_uncertainty=5,
)
sample.location.y  # latitude, 49.0094
sample.location.x  # longitude, 8.4115
```

## Location input

All three names are in `fairdm.utils.location.forms`.

### `Location`

A named tuple that a `LocationField` cleans to.

| Attribute | Type | Default | What it holds |
|---|---|---|---|
| `point` | `Point` | — | The point, in SRID 4326 |
| `elevation` | `float` or `None` | `None` | Metres above mean sea level |
| `uncertainty` | `float` or `None` | `None` | Metres, zero or more |

### `LocationField(full=True, **kwargs)`

A `MultiValueField` that reads a latitude and a longitude and, with `full=True`, an elevation and an uncertainty.

| Argument | Type | Default | What it does | What it accepts |
|---|---|---|---|---|
| `full` | `bool` | `True` | Chooses whether the elevation and uncertainty are asked for. | `False` asks for a latitude and a longitude only, as an organization's point does. |
| `**kwargs` | | `required=False` | Passed to `MultiValueField`. | |

The field cleans to `None` when every input is empty, and otherwise to a `Location`. The inputs, in order, are latitude, longitude, elevation and uncertainty, submitted as `<name>_0` to `<name>_3`.

```python
from fairdm.utils.location.forms import LocationField

location = LocationField().clean(["49.0094", "8.4115", "112", "5"])
location.point.srid  # 4326
location.elevation  # 112.0
location.uncertainty  # 5.0
```

The input reads every coordinate as a signed decimal number of degrees in WGS 84, the system a GPS receiver records. South and west are negative, such as `49.0094` and `-8.4115`. It has no reference-system input and does not read degrees, minutes and seconds or hemisphere letters. It refuses a value, and saves nothing, when:

- a coordinate is not a number, or lies outside its range: latitude beyond 90, longitude beyond 180,
- one coordinate is given without the other (code `incomplete`),
- an elevation or an uncertainty is given with no coordinates (code `no_point`),
- the uncertainty is negative.

### `LocationWidget(full=True, attrs=None)`

The input a `LocationField` draws, built from number inputs. Its template is `location/widgets/location.html`. With `full=False` it draws the point-only variant.

### `LocationFormMixin`

A mixin for a `ModelForm` of a model that has the three fields.

| Provides | When |
|---|---|
| Replaces `location` with a full `LocationField` that starts from the instance's point, elevation and uncertainty | `location` is among the form's fields |
| Removes `location_elevation` and `location_uncertainty` from the form, because the input holds them | `location` is among the form's fields |
| On clean, puts the point on `location` and the elevation and uncertainty on the instance | `location` is among the form's fields |
| Clears all three when the coordinates are cleared | The coordinates are submitted empty |

`SampleFormMixin` and `MeasurementFormMixin` include it. See [Form and filter mixins](form-and-filter-mixins.md).

## Queryset lookups

`Sample.objects` and `Organization.objects` carry `inside()`, `within_distance()` and `nearest()` from `LocatedQuerySet`, in `fairdm.utils.location.managers`. Each returns a queryset, so it combines with any other filter, `visible_to()` included, in either order. A person has no location, so no lookup applies to people.

| Method | Arguments | Returns |
|---|---|---|
| `inside(area)` | `area`: a GEOS polygon, or a `(west, south, east, north)` tuple in degrees | The records whose location lies in the area. A point on the edge counts. A record with no location is never inside. |
| `within_distance(point, distance)` | `point`: a GEOS point. `distance`: a `D` measure, or a number of metres. | The records within the distance, measured on the ground |
| `nearest(point)` | `point`: a GEOS point | The records ordered by distance, nearest first, each with a `distance` attribute that is a `D`. Records with no location come last with `None`. |

A tuple whose west is greater than its east is a box across the 180th meridian, the shape `spatial_coverage` returns. A point given without a reference system is taken to be in WGS 84.

`inside` and `within_distance` read a spatial index. The distance lookups cast the point to a geography, and the index they use is built on the same cast.

### Measurements

A measurement is found by its effective location, so its lookups take the viewer as well.

| Method | Arguments | Returns |
|---|---|---|
| `inside(area, user=None)` | As above, and the viewer | The measurements whose effective location lies in the area |
| `within_distance(point, distance, user=None)` | As above, and the viewer | The measurements within the distance |
| `nearest(point, user=None)` | As above, and the viewer | The measurements nearest first, with `distance` |

`user=None` is a visitor who is not signed in. `visible_to()` does not tell a lookup who is asking, so pass the viewer to both.

`inside` and `within_distance` are the union of two subqueries, one on the measurement table and one on the sample table, each using its own index.

## A measurement's effective location

A measurement's effective location is its own where it has one, and its sample's otherwise. The sample's counts only for a viewer who may open the sample. For anyone else a measurement with no location of its own has none.

### `Measurement.effective_location_for(user=None)`

Returns an `EffectiveLocation`, or `None` when the viewer has no location to be shown. `EffectiveLocation` is a named tuple in `fairdm.core.measurement.models`.

| Attribute | Type | What it holds |
|---|---|---|
| `point` | `Point` | The point, in SRID 4326 |
| `elevation` | `float` or `None` | Metres above mean sea level |
| `uncertainty` | `float` or `None` | Metres |
| `source` | `str` | `"own"` for the measurement's own location, `"sample"` for its sample's |

```python
found = measurement.effective_location_for(request.user)
if found is not None:
    found.point.y  # latitude
    found.source  # "own" or "sample"
```

### `MeasurementQuerySet.with_effective_location(user=None)`

Annotates each measurement with `effective_location`, a WGS 84 point or `None`, by the same rule and in the same query.

```python
for measurement in Measurement.objects.with_effective_location(request.user):
    measurement.effective_location
```

## Spatial coverage

A spatial coverage is the smallest box that holds a set of locations. The box is a `Coverage` named tuple in `fairdm.utils.location.coverage`.

| Attribute | Type | What it holds |
|---|---|---|
| `west` | `float` | The western bound, a longitude |
| `south` | `float` | The southern bound, a latitude |
| `east` | `float` | The eastern bound, a longitude |
| `north` | `float` | The northern bound, a latitude |

A box across the 180th meridian has `west` greater than `east`. Locations at 176 and -176 degrees give a narrow box with `west` 176 and `east` -176, not one that spans the globe.

| Call | Returns |
|---|---|
| `dataset.spatial_coverage(user=None)` | The box that holds the locations of the dataset's samples and measurements the viewer may see, or `None` |
| `project.spatial_coverage(user=None)` | The same over the datasets of the project the viewer may open |
| `spatial_coverage(*pairs)` | The box that holds every location in the `(queryset, field)` pairs, or `None`. `field` names a point column or a point annotation. |

A measurement counts by its effective location for the viewer, so a measurement placed only by a sample the viewer may not open adds nothing.

```python
from fairdm.utils.location.coverage import spatial_coverage

spatial_coverage(
    (CoreSample.objects.filter(dataset=dataset), "location"),
    (Organization.objects.all(), "location"),
)
```

A dataset's DataCite metadata carries its coverage for a visitor as one `geoLocationBox`, and none when nothing a visitor may see is located. See [Dataset publication, DOIs and DataCite metadata](../../explanation/dataset-publication-dois-and-datacite-metadata.md).

## Model helpers

Both are in `fairdm.utils.location.db`. A concrete model that holds a `location` lists them in its own `Meta`, as `Sample` and `Measurement` do.

| Function | Returns |
|---|---|
| `location_constraints()` | Two check constraints: an uncertainty is empty or zero or more, and an elevation or an uncertainty needs a point |
| `geography_index(name)` | A GiST index on the location as a geography, which the distance lookups read. `name` is 30 characters or fewer. |

## In import and export

A type whose `fields`, or whose `resource_fields`, list `location` gets four columns in its import and export file, in place of one.

| Column | Holds | Accepts |
|---|---|---|
| `latitude` | Degrees north, or south when negative | A signed decimal number from -90 to 90 |
| `longitude` | Degrees east, or west when negative | A signed decimal number from -180 to 180 |
| `location_elevation` | Metres above mean sea level | A plain number |
| `location_uncertainty` | Metres | A plain number, zero or more |

An export writes each record's own values as WGS 84 decimal degrees and leaves the four cells empty for a record that has none. A measurement never writes its sample's location.

```text
id,name,latitude,longitude,location_elevation,location_uncertainty
31,RS-14,49.0094,8.4115,112.5,25.0
32,RS-15,,,,
```

An import reads the cells with the same rules as the location input and reports a row it refuses with the input's own message. The refused row is not saved and the rest of the file is read as usual.

- A file that has none of the four columns leaves every record's location as it was.
- A file with only some of the columns changes only those.
- An empty cell clears the value.
- Clearing a point also clears the elevation and uncertainty, so a file that empties `latitude` and `longitude` for a record that holds either must carry those two columns too, with empty cells.
- A file with only the two coordinate columns is refused for a row whose record holds an elevation or an uncertainty and would be left without a point.
- The cells are always WGS 84. The file has no reference-system column.

The pieces are in `fairdm.utils.location.resources`.

| Name | Is |
|---|---|
| `LocatedResourceMixin` | A mixin that replaces `location` in a resource's fields with the four columns, and sets the point on import |
| `location_fields()` | The four import-export fields, keyed by column name, in column order |
| `CoordinateField(axis)` | The `latitude` or `longitude` field, for `axis` `"lat"` or `"lon"` |
| `MeasureWidget` | Reads a number cell, writes the number itself or an empty cell for none, and refuses `nan` and infinite values |

`fairdm.contrib.import_export.resources.BaseFairDMResource` includes `LocatedResourceMixin`. The resource the registry generates for a type does too, when the type's fields list `location`.

## In the API

A sample and a measurement return `location` and `location_uncertainty`. An organization returns `location`. A person returns neither.

```json
{
  "name": "RS-14",
  "location": {"type": "Point", "coordinates": [8.4115, 49.0094, 112.5]},
  "location_uncertainty": 25.0
}
```

- `location` is a GeoJSON `Point` in WGS 84 with longitude first, and the record's elevation as the third coordinate when it holds one. It is `null` for a record with no location.
- `location_uncertainty` is in metres and sits beside the geometry, because GeoJSON has no place for it.
- A measurement returns only its own location. The sample's place is read from the sample.
- All three fields are read-only. A request that sends one leaves the record's location as it was.

See [REST API](rest-api.md).

## In the collection tables

The listing of a sample or measurement type has a Latitude and a Longitude column and no location column. A sample's columns read its own point. A measurement's read its effective location for the viewer. Neither column sorts, because a point has no order. The table the registry generates leaves any geometry field out of the columns it builds from a type's `table_fields`, since the two columns are always there.
