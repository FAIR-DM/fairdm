"""The smallest box that holds the locations of a set of records."""

from typing import NamedTuple

from django.contrib.gis.db.models import Extent, PointField
from django.db.models import Func


class Coverage(NamedTuple):
    """A box in WGS 84 degrees. A box across the 180th meridian has ``west`` greater than ``east``.

    Attributes:
        west: The western bound, a longitude.
        south: The southern bound, a latitude.
        east: The eastern bound, a longitude.
        north: The northern bound, a latitude.
    """

    west: float
    south: float
    east: float
    north: float


def spatial_coverage(*querysets_and_fields):
    """Return the smallest box holding every location in the given querysets.

    Each queryset is read twice, as longitudes in -180 to 180 and as longitudes in 0 to 360, and
    the narrower of the two boxes is kept. Locations on both sides of the 180th meridian therefore
    give a narrow box with ``west`` greater than ``east``, as DataCite writes it, and not one
    that spans the globe.

    Args:
        *querysets_and_fields: ``(queryset, field)`` pairs, ``field`` naming a point column or
            a point annotation on the queryset.

    Returns:
        The ``Coverage``, or ``None`` when nothing in the querysets is located.

    Example:
        ```python
        spatial_coverage(
            (dataset.samples.all(), "location"),
            (dataset.measurements.with_effective_location(None), "effective_location"),
        )
        ```
    """
    plain = []
    shifted = []
    for queryset, field in querysets_and_fields:
        extents = queryset.aggregate(
            plain=Extent(field),
            shifted=Extent(
                Func(
                    field,
                    function="ST_ShiftLongitude",
                    output_field=PointField(srid=4326),
                )
            ),
        )
        if extents["plain"] is not None:
            plain.append(extents["plain"])
            shifted.append(extents["shifted"])
    if not plain:
        return None

    west, south, east, north = (
        min(box[0] for box in plain),
        min(box[1] for box in plain),
        max(box[2] for box in plain),
        max(box[3] for box in plain),
    )
    shifted_west = min(box[0] for box in shifted)
    shifted_east = max(box[2] for box in shifted)
    if shifted_east - shifted_west < east - west:
        west = shifted_west if shifted_west <= 180 else shifted_west - 360
        east = shifted_east if shifted_east <= 180 else shifted_east - 360
    return Coverage(west, south, east, north)
