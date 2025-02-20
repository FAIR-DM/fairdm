import json
from decimal import ROUND_DOWN, Decimal

from django.contrib.gis.measure import Distance
from django.db.models import F, Max, Min

# from rest_framework_gis.filters import DistanceToPointFilter
# from fairdm.contrib.samples.serializers import SampleGeojsonSerializer


def serialize_dataset_samples(self, dataset):
    qs = dataset.samples.annotate(geom=F("location__point"))  # noqa: F841
    # serializer = SampleGeojsonSerializer(qs, many=True)
    # return {str(dataset.pk): json.dumps(serializer.data)}
    return {str(dataset.pk): json.dumps([])}


def get_sites_within(location, radius=25):
    """Gets nearby sites within {radius} km radius"""
    qs = Point.objects.filter(point__distance_lt=(location.point, Distance(km=radius)))  # noqa: F841


def bbox_for_dataset(dataset):
    from .models import Point

    bounds = Point.objects.filter(samples__dataset=dataset).aggregate(
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
