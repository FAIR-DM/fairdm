"""Coordinate and dataset-location helpers."""

import json
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

from django.contrib.gis.measure import Distance
from django.core.exceptions import ValidationError
from django.db.models import F, Max, Min

from .models import Point


def normalize_coordinate(value, precision=5, coerce=str):
    """Round a coordinate to five decimal places.

    Args:
        value: The coordinate, in any type convertible to ``Decimal``.
        precision: Not used. The result always has five decimal places.
        coerce: The type of the result. ``str`` gives a fixed-point string.

    Returns:
        The rounded coordinate as ``coerce``.

    Raises:
        ValidationError: The value cannot be converted to a ``Decimal``.
    """
    try:
        dec = Decimal(str(value))
    except Exception as err:
        raise ValidationError(f"Invalid coordinate value: {value}") from err

    -dec.as_tuple().exponent if dec.as_tuple().exponent < 0 else 0

    rounded = dec.quantize(Decimal("0.00001"), rounding=ROUND_HALF_UP)
    if coerce is str:
        return f"{rounded:.5f}"
    return coerce(rounded)


def serialize_dataset_samples(self, dataset):
    """Return the dataset's samples serialized for the map, currently always empty.

    Args:
        self: Not used.
        dataset: The dataset whose samples are serialized.

    Returns:
        A dict mapping the dataset's UUID to a JSON list, which is always empty.
    """
    qs = dataset.samples.annotate(geom=F("location__point"))  # noqa: F841
    return {str(dataset.uuid): json.dumps([])}


def get_sites_within(location, radius=25):
    """Build the query for points within a radius of a location, without returning it.

    Args:
        location: The location to search around.
        radius: The search radius in kilometres.
    """
    Point.objects.filter(point__distance_lt=(location.point, Distance(km=radius)))


def locations_for_dataset(dataset):
    """Return the locations of a dataset's samples.

    Args:
        dataset: The dataset to look up.

    Returns:
        A queryset of points.
    """
    from .models import Point

    return Point.objects.filter(samples__dataset=dataset)


def bbox_for_dataset(dataset):
    """Return the bounding box of a dataset's locations.

    Args:
        dataset: The dataset to measure.

    Returns:
        A dict with ``min_x``, ``max_x``, ``min_y`` and ``max_y`` rounded down to five
        decimal places, each None when the dataset has no locations.
    """
    point_qs = locations_for_dataset(dataset)

    bounds = point_qs.aggregate(
        min_x=Min("x"),
        max_x=Max("x"),
        min_y=Min("y"),
        max_y=Max("y"),
    )
    precision = Decimal("0.00001")
    rounded_bounds = {
        key: (
            value.quantize(precision, rounding=ROUND_DOWN)
            if value is not None
            else None
        )
        for key, value in bounds.items()
    }

    return rounded_bounds
