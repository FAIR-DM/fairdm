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

A hand-written form uses `SampleFormMixin`, which carries the input, or `LocationFormMixin` on its
own for any `ModelForm` whose model has the three fields:

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

## Upgrading

A sample's `location` used to be a foreign key to a shared `Point`. It is now a point, and existing
locations are not carried across. A portal that holds locations has to write them again:

- Code that reads `location.latitude` or `location.longitude` reads `location.y` and `location.x`.
- Code that filters on `location__x`, `location__y` or `location__crs` has to change.
- `FAIRDM_CRS`, `FAIRDM_X_COORD` and `FAIRDM_Y_COORD` are gone.
- A contributor's `location` is gone. An organization has a point of its own.
- The page at `/location/<lon>/<lat>/` is gone, and so is the link to it in the collection tables.
