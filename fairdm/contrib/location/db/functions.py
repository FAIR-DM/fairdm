"""Database functions for GeoJSON features and point coordinates."""

from django.contrib.gis.db.models.functions import AsGeoJSON, GeoFunc
from django.db.models import F, FloatField, JSONField, Value
from django.db.models.functions import Cast, JSONObject


def AsGeoFeature(*args):
    """Build a GeoJSON ``Feature`` expression from the row's ``geom`` field.

    Args:
        *args: Field names that become the feature's properties.

    Returns:
        A ``JSONObject`` expression with the feature's id, geometry and properties.
    """
    return JSONObject(
        type=Value("Feature"),
        id=F("uuid"),
        geometry=Cast(AsGeoJSON("geom"), output_field=JSONField()),
        properties=JSONObject(**{p: F(p) for p in args}),
    )


class Lat(GeoFunc):
    """Extract a geometry's ``ST_X`` value as a float."""

    function = "ST_X"
    output_field = FloatField()


class Lon(GeoFunc):
    """Extract a geometry's ``ST_Y`` value as a float."""

    function = "ST_Y"
    output_field = FloatField()


class OrientedEnvelope(GeoFunc):
    """Compute a geometry's oriented envelope with ``ST_OrientedEnvelope``."""

    function = "ST_OrientedEnvelope"
    output_field = FloatField()
