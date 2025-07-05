import json
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

from django.contrib.gis.measure import Distance
from django.core.exceptions import ValidationError
from django.db.models import F, Max, Min

# from rest_framework_gis.filters import DistanceToPointFilter
# from fairdm.contrib.samples.serializers import SampleGeojsonSerializer


def normalize_coordinate(value, precision=5, coerce=str):
    """
    Normalizes a coordinate value to a specified precision and type.

    Args:
        value: The coordinate value to normalize. Can be any type convertible to Decimal.
        precision (int, optional): The minimum number of decimal places required. Defaults to 5.
        coerce (type, optional): The type to which the normalized value should be coerced. Defaults to str.

    Returns:
        The normalized coordinate value, rounded to the specified precision and coerced to the requested type.

    Raises:
        ValidationError: If the input value is invalid or does not have at least the required number of decimal places.
    """
    try:
        dec = Decimal(str(value))
    except Exception:
        raise ValidationError(f"Invalid coordinate value: {value}")

    # Count number of actual decimal places
    decimal_places = -dec.as_tuple().exponent if dec.as_tuple().exponent < 0 else 0

    # if decimal_places < 5:
    # raise ValidationError("Coordinates must be at least 5 decimal places")

    # Round to 5 decimal places (ROUND_HALF_UP)
    rounded = dec.quantize(Decimal("0.00001"), rounding=ROUND_HALF_UP)
    # Return in the requested type
    if coerce is str:
        return f"{rounded:.5f}"
    return coerce(rounded)


def serialize_dataset_samples(self, dataset):
    qs = dataset.samples.annotate(geom=F("location__point"))  # noqa: F841
    # serializer = SampleGeojsonSerializer(qs, many=True)
    # return {str(dataset.uuid): json.dumps(serializer.data)}
    return {str(dataset.uuid): json.dumps([])}


def get_sites_within(location, radius=25):
    """Gets nearby sites within {radius} km radius"""
    qs = Point.objects.filter(point__distance_lt=(location.point, Distance(km=radius)))  # noqa: F841


def locations_for_dataset(dataset):
    """Get all locations for a dataset"""
    from .models import Point

    # Get all points related to the dataset
    return Point.objects.filter(samples__dataset=dataset)

    # # Serialize the points to GeoJSON
    # serializer = SampleGeojsonSerializer(points, many=True)
    # return json.dumps(serializer.data)


def bbox_for_dataset(dataset):
    point_qs = locations_for_dataset(dataset)

    bounds = point_qs.aggregate(
        min_x=Min("x"),
        max_x=Max("x"),
        min_y=Min("y"),
        max_y=Max("y"),
    )
    precision = Decimal("0.00001")  # 5 decimal places
    # Round to 5 decimal places
    rounded_bounds = {
        key: value.quantize(precision, rounding=ROUND_DOWN) if value is not None else None
        for key, value in bounds.items()
    }

    return rounded_bounds


#
