# How to find records by where they are

This guide finds samples, measurements or organizations inside an area, within a distance of a point, or nearest a point. You would do this to draw a map layer, answer a search by place, or list what was collected near a site.

## Before you start

The records need a location. See [How to give a sample or measurement a location](give-a-registered-type-a-location.md). The lookups are listed in [Location fields](../reference/location-fields.md). The examples use these imports.

```python
from fairdm.contrib.contributors.models import Organization
from fairdm.core.measurement.models import Measurement
from fairdm.core.sample.models import Sample
```

## Steps

1. Find the records inside an area. Pass a `(west, south, east, north)` tuple in degrees, or a GEOS polygon. A point on the edge counts as inside, and a record with no location is never inside.

   ```python
   from django.contrib.gis.geos import Polygon

   Sample.objects.inside((8.0, 47.0, 9.0, 48.0))
   Sample.objects.inside(Polygon(((0, 40), (20, 40), (10, 60), (0, 40)), srid=4326))
   ```

   A tuple whose west is greater than its east is a box across the 180th meridian.

2. Find the records within a distance of a point. Pass the distance as a `D` measure or as a number of metres. It is measured on the ground, so a kilometre is a kilometre near the equator and near a pole.

   ```python
   from django.contrib.gis.geos import Point
   from django.contrib.gis.measure import D

   karlsruhe = Point(8.4037, 49.0069, srid=4326)
   Sample.objects.within_distance(karlsruhe, D(km=5))
   Sample.objects.within_distance(karlsruhe, 5_000)
   ```

3. Order the records by distance from a point. Each gets a `distance`, a `D`, and records with no location come last with `None`.

   ```python
   for sample in Sample.objects.visible_to(request.user).nearest(karlsruhe)[:10]:
       sample.distance.km
   ```

4. Combine a lookup with any other filter, in either order. Use `visible_to()` so a visitor sees only the samples they may open.

   ```python
   Sample.objects.visible_to(request.user).inside((8.0, 47.0, 9.0, 48.0))
   ```

5. For measurements, pass the viewer to the lookup as well. A measurement is found by its effective location, which is its own or else its sample's for a viewer who may open the sample. `user=None` is a visitor who is not signed in.

   ```python
   Measurement.objects.visible_to(request.user).inside(
       (8.0, 47.0, 9.0, 48.0), user=request.user
   )
   Measurement.objects.nearest(karlsruhe, user=request.user)
   ```

   `visible_to()` does not tell the lookup who is asking. Without `user=`, a measurement placed only by a sample the viewer may open is left out.

6. Use the same three lookups on `Organization.objects`. A person has no location, so none applies.

## The result

Each call returns a queryset. A measurement with no location of its own is found by its sample's location only for a viewer who may open the sample, so a lookup never gives away where an unpublished sample was taken. For the reasoning and the index the lookups read, see [How locations are stored and protected](../../explanation/how-locations-are-stored-and-protected.md).
