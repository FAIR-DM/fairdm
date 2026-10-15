"""Lookups that find records by where they are."""

from django.contrib.gis.db.models import PointField
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Polygon
from django.contrib.gis.measure import D
from django.db.models import F
from django.db.models.functions import Cast

WGS84 = 4326


class Spatial:
    """Read what a lookup is given, and build the expressions its queries compare.

    Every method is static: the class only groups what the lookups of this module share.
    """

    @staticmethod
    def polygon(area):
        """Read an area as a polygon in WGS 84.

        Args:
            area: A GEOS polygon, or a ``(west, south, east, north)`` tuple in degrees. A tuple
                with west greater than east is a box across the 180th meridian, the shape
                ``spatial_coverage`` returns.

        Returns:
            The polygon, in SRID 4326.
        """
        if isinstance(area, GEOSGeometry):
            if area.srid is None:
                area.srid = WGS84
            return area
        west, south, east, north = area
        if west > east:
            return MultiPolygon(
                Polygon.from_bbox((west, south, 180, north)),
                Polygon.from_bbox((-180, south, east, north)),
            )
        return Polygon.from_bbox((west, south, east, north))

    @staticmethod
    def point(point):
        """Read a point as a WGS 84 point.

        Args:
            point: A GEOS point. One without a reference system is taken to be in WGS 84.

        Returns:
            The point, in SRID 4326.
        """
        if point.srid is None:
            point.srid = WGS84
        return point

    @staticmethod
    def distance(distance):
        """Read a distance as a measure.

        Args:
            distance: A ``D`` measure, or a number of metres.

        Returns:
            The distance as a ``D``.
        """
        return distance if isinstance(distance, D) else D(m=distance)

    @staticmethod
    def geography(field="location"):
        """Cast a point column to a geography, the expression the geography indexes are built on.

        Args:
            field: The name of the point column or annotation.

        Returns:
            The cast expression.
        """
        return Cast(field, PointField(geography=True))


class LocatedQuerySet:
    """Queryset methods for a model that holds its own ``location``.

    Mix it into a model's queryset. Each method returns a queryset, so it combines with any other
    filter, ``visible_to()`` included.

    Example:
        ```python
        Sample.objects.inside((8.0, 47.0, 9.0, 48.0))
        Sample.objects.within_distance(Point(8.4, 48.9, srid=4326), D(km=5))
        Sample.objects.nearest(Point(8.4, 48.9, srid=4326))[:10]
        ```
    """

    def inside(self, area):
        """Return the records whose location lies in an area. A point on the edge counts.

        Args:
            area: A GEOS polygon, or a ``(west, south, east, north)`` tuple in degrees.

        Returns:
            The records inside the area. Records with no location are never inside.
        """
        return self.filter(location__coveredby=Spatial.polygon(area))

    def within_distance(self, point, distance):
        """Return the records whose location is within a distance of a point.

        The distance is measured on the ground, not in degrees, so the answer is the same near the
        equator and near a pole.

        Args:
            point: A GEOS point.
            distance: A ``D`` measure, or a number of metres.

        Returns:
            The records within the distance.
        """
        return self.alias(location_geography=Spatial.geography()).filter(
            location_geography__dwithin=(
                Spatial.point(point),
                Spatial.distance(distance),
            )
        )

    def nearest(self, point):
        """Order the records by their distance from a point, nearest first.

        Args:
            point: A GEOS point.

        Returns:
            The records ordered by distance, each carrying ``distance`` as a ``D`` measure, or
            ``None`` for a record with no location, which comes last.
        """
        return self.annotate(
            distance=Distance(Spatial.geography(), Spatial.point(point))
        ).order_by(F("distance").asc(nulls_last=True))
