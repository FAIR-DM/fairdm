"""Forms and widgets for entering locations."""

import re

from django import forms
from django.contrib.gis.gdal import CoordTransform, GDALException, SpatialReference
from django.contrib.gis.geos import Point as GeosPoint
from django.utils.translation import gettext_lazy as _

from .models import Point


class PointForm(forms.ModelForm):
    """Form for a location's coordinates."""

    class Meta:
        model = Point
        fields = ["x", "y"]


class LatitudeWidget(forms.TextInput):
    """Text input that masks a latitude as up to 2 digits and a set number of decimals.

    Args:
        attrs: Extra HTML attributes, which override the mask.
        precision: Number of decimal places the mask allows.
    """

    def __init__(self, attrs=None, precision=5):
        self.precision = precision
        x_precision = "9" * self.precision
        default_attrs = {
            "x-mask:dynamic": f"$input.startsWith('-') ? '-99.{x_precision}' : '99.{x_precision}'"
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)


class LongitudeWidget(forms.TextInput):
    """Text input that masks a longitude as up to 3 digits and a set number of decimals.

    Args:
        attrs: Extra HTML attributes, which override the mask.
        precision: Number of decimal places the mask allows.
    """

    def __init__(self, attrs=None, precision=5):
        self.precision = precision
        x_precision = "9" * self.precision
        default_attrs = {
            "x-mask:dynamic": f"$input.startsWith('-') ? '-999.{x_precision}' : '999.{x_precision}'"
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)


# ---------------------------------------------------------------------------------------------
# Sketch of the location input for FS-030. Untested prototype code: the build replaces it.
# ---------------------------------------------------------------------------------------------

WGS84 = 4326

#: Reference systems offered as suggestions. Any other EPSG code can be typed.
COMMON_SYSTEMS = [
    (4326, "WGS 84"),
    (4258, "ETRS89"),
    (25832, "ETRS89 / UTM zone 32N"),
    (25833, "ETRS89 / UTM zone 33N"),
    (32632, "WGS 84 / UTM zone 32N"),
    (32633, "WGS 84 / UTM zone 33N"),
    (31467, "DHDN / 3-degree Gauss-Kruger zone 3"),
    (27700, "OSGB36 / British National Grid"),
    (2193, "NZGD2000 / New Zealand Transverse Mercator"),
]

_DMS = re.compile(
    r"""^\s*(?P<h1>[NSEW])?\s*
        (?P<deg>[-+]?\d+(?:[.,]\d+)?)\s*(?:°|d|deg|\s)?\s*
        (?:(?P<min>\d+(?:[.,]\d+)?)\s*(?:'|\u2032|\s)?\s*)?
        (?:(?P<sec>\d+(?:[.,]\d+)?)\s*(?:"|\u2033|''|\s)?\s*)?
        (?P<h2>[NSEW])?\s*$""",
    re.IGNORECASE | re.VERBOSE,
)


def parse_coordinate(text, axis):
    """Read one geographic coordinate typed in decimal degrees, degrees and minutes, or DMS.

    Args:
        text: What was typed, such as ``48.9353``, ``48 56.118 N`` or ``48°56'07"N``.
        axis: ``"lat"`` or ``"lon"``, which sets the range and the hemisphere letters allowed.

    Returns:
        The coordinate in signed decimal degrees.

    Raises:
        ValidationError: The text cannot be read, or lies outside the axis's range.
    """
    match = _DMS.match(text or "")
    if not match:
        raise forms.ValidationError(
            _("Enter a %(axis)s such as 48.9353, 48 56.118 N or 48°56′07″N.")  # noqa: RUF001
            % {"axis": _("latitude") if axis == "lat" else _("longitude")}
        )
    deg = float(match["deg"].replace(",", "."))
    minutes = float((match["min"] or "0").replace(",", "."))
    seconds = float((match["sec"] or "0").replace(",", "."))
    if minutes >= 60 or seconds >= 60:
        raise forms.ValidationError(_("Minutes and seconds run from 0 to 59."))
    value = abs(deg) + minutes / 60 + seconds / 3600
    hemisphere = (match["h1"] or match["h2"] or "").upper()
    allowed = "NS" if axis == "lat" else "EW"
    if hemisphere and hemisphere not in allowed:
        raise forms.ValidationError(
            _("A latitude ends in N or S, a longitude in E or W.")
        )
    if deg < 0 or hemisphere in ("S", "W"):
        value = -value
    limit = 90 if axis == "lat" else 180
    if abs(value) > limit:
        raise forms.ValidationError(
            _("A latitude lies between -90 and 90.")
            if axis == "lat"
            else _("A longitude lies between -180 and 180.")
        )
    return value


def is_geographic(srid):
    """Whether coordinates in this system are typed as degrees."""
    try:
        return SpatialReference(srid).geographic
    except (GDALException, TypeError, ValueError):
        return True


class LocationWidget(forms.MultiWidget):
    """The location input: reference system, two coordinates, elevation and uncertainty.

    Args:
        full: Offer the reference system, elevation and uncertainty. Without it the widget asks
            for a latitude and a longitude in WGS 84 only, as an organization's point does.
    """

    template_name = "location/widgets/location.html"

    def __init__(self, full=True, attrs=None):
        self.full = full
        widgets = {
            "srid": forms.TextInput(
                attrs={
                    "class": "input w-full",
                    "list": "location-systems",
                    "inputmode": "numeric",
                }
            ),
            "first": forms.TextInput(
                attrs={
                    "class": "input w-full font-mono",
                    "autocomplete": "off",
                    "spellcheck": "false",
                }
            ),
            "second": forms.TextInput(
                attrs={
                    "class": "input w-full font-mono",
                    "autocomplete": "off",
                    "spellcheck": "false",
                }
            ),
            "elevation": forms.NumberInput(attrs={"class": "w-full", "step": "any"}),
            "uncertainty": forms.NumberInput(
                attrs={"class": "w-full", "step": "any", "min": "0"}
            ),
        }
        if not full:
            widgets = {"first": widgets["first"], "second": widgets["second"]}
        super().__init__(widgets, attrs)

    def decompress(self, value):
        """Split a stored location into the values the inputs show, in WGS 84 decimal degrees."""
        value = value or {}
        lat = value.get("lat")
        lon = value.get("lon")
        parts = {
            "srid": WGS84,
            "first": "" if lat is None else f"{float(lat):.5f}",
            "second": "" if lon is None else f"{float(lon):.5f}",
            "elevation": value.get("elevation"),
            "uncertainty": value.get("uncertainty"),
        }
        return [parts[name] for name in self.widgets_names_keys()]

    def widgets_names_keys(self):
        return (
            ["srid", "first", "second", "elevation", "uncertainty"]
            if self.full
            else ["first", "second"]
        )

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        subwidgets = dict(
            zip(self.widgets_names_keys(), context["widget"]["subwidgets"], strict=True)
        )
        context["widget"].update(
            {
                "full": self.full,
                "parts": subwidgets,
                "systems": COMMON_SYSTEMS,
            }
        )
        return context


class LocationField(forms.MultiValueField):
    """Read a location typed in any supported notation and reference system, as WGS 84.

    Cleans to ``None`` when every input is empty, or to a dict with ``lat``, ``lon`` and, for the
    full input, ``elevation`` and ``uncertainty``.
    """

    def __init__(self, full=True, **kwargs):
        self.full = full
        fields = [
            forms.CharField(required=False),
            forms.CharField(required=False),
        ]
        if full:
            fields = [
                forms.IntegerField(required=False),
                *fields,
                forms.FloatField(required=False),
                forms.FloatField(required=False, min_value=0),
            ]
        kwargs.setdefault("required", False)
        super().__init__(
            fields,
            require_all_fields=False,
            widget=LocationWidget(full=full),
            **kwargs,
        )

    def compress(self, data_list):
        if not data_list:
            return None
        if self.full:
            srid, first, second, elevation, uncertainty = data_list
        else:
            first, second = data_list
            srid, elevation, uncertainty = WGS84, None, None
        srid = srid or WGS84
        if not first and not second:
            if elevation is not None or uncertainty is not None:
                raise forms.ValidationError(
                    _(
                        "Enter the coordinates for the elevation and uncertainty to belong to."
                    )
                )
            return None
        if not first or not second:
            raise forms.ValidationError(_("Enter both coordinates, or neither."))
        if is_geographic(srid):
            lat = parse_coordinate(first, "lat")
            lon = parse_coordinate(second, "lon")
            point = GeosPoint(lon, lat, srid=srid)
        else:
            try:
                northing = float(str(first).replace(",", "."))
                easting = float(str(second).replace(",", "."))
            except ValueError as error:
                raise forms.ValidationError(
                    _("Enter the northing and easting in metres, such as 5420115.")
                ) from error
            point = GeosPoint(easting, northing, srid=srid)
        if srid != WGS84:
            try:
                point.transform(
                    CoordTransform(SpatialReference(srid), SpatialReference(WGS84))
                )
            except GDALException as error:
                raise forms.ValidationError(
                    _("EPSG:%(code)s is not a reference system the portal knows.")
                    % {"code": srid}
                ) from error
        lon, lat = point.x, point.y
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise forms.ValidationError(
                _("These coordinates fall outside the Earth's range once converted.")
            )
        return {
            "lat": lat,
            "lon": lon,
            "elevation": elevation,
            "uncertainty": uncertainty,
        }


def location_from_point(point, options=None):
    """The value a location input starts from: a sample's stored point plus its sketch extras."""
    if point is None:
        return None
    extra = (options or {}).get("location", {})
    return {
        "lat": float(point.y),
        "lon": float(point.x),
        "elevation": extra.get("elevation"),
        "uncertainty": extra.get("uncertainty"),
    }


def point_for(location):
    """The shared ``Point`` row for a location, found or created. Sketch only."""
    if not location:
        return None
    from decimal import ROUND_HALF_UP, Decimal

    places = Decimal("0.00001")
    x = Decimal(str(location["lon"])).quantize(places, rounding=ROUND_HALF_UP)
    y = Decimal(str(location["lat"])).quantize(places, rounding=ROUND_HALF_UP)
    return Point.objects.get_or_create(x=x, y=y)[0]
