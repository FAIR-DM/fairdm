"""Forms and widgets for entering locations."""

import math
import re
from decimal import Decimal
from typing import NamedTuple

from django import forms
from django.contrib.gis import geos
from django.contrib.gis.gdal import GDALException, SpatialReference
from django.utils.translation import gettext_lazy as _
from lat_lon_parser import parse

AXIS_LIMITS = {"lat": 90, "lon": 180}
AXIS_HEMISPHERES = {"lat": "ns", "lon": "ew"}
HEMISPHERE_WORD = r"north|south|east|west|[nsew]"
LEADING_HEMISPHERE = re.compile(rf"^\s*({HEMISPHERE_WORD})(?![a-z])\s*", re.IGNORECASE)
TRAILING_HEMISPHERE = re.compile(
    rf"\s*(?<![a-z])({HEMISPHERE_WORD})\s*$", re.IGNORECASE
)
MINUTES_LETTER = re.compile(r"(?<=\d)\s*m(?![a-z])", re.IGNORECASE)
DEGREE_LETTER = re.compile(r"(?<=\d)\s*(?:deg|d)(?![a-z])", re.IGNORECASE)
NUMBER = re.compile(r"\d+(?:[.,]\d+)?")
EPSG_CODE = re.compile(r"(?:epsg:)?(\d{1,8})", re.IGNORECASE)
WGS84 = 4326
#: The largest northing or easting taken in metres. No projected system produces more.
MAX_PROJECTED_METRES = 1e9

#: EPSG codes the input suggests. Any other code can be typed.
SUGGESTED_SYSTEMS = (4326, 4258, 25832, 25833, 32632, 32633, 31467, 27700, 2193)


def parse_coordinate(text, axis):
    """Read one geographic coordinate typed in decimal degrees, degrees and minutes, or DMS.

    The reading is ``lat_lon_parser.parse``. On top of it this refuses a value outside the
    axis's range, a hemisphere that belongs to the other axis, minutes written with the letter
    ``m`` (the package would read the ``s`` after seconds as south), and text with more than
    degrees, minutes and seconds in it.

    Args:
        text: What was typed, such as ``48.9353``, ``48 56.118 N`` or ``48°56'07"N``.
        axis: ``"lat"`` or ``"lon"``, which sets the range and the hemisphere letters allowed.

    Returns:
        The coordinate in signed decimal degrees.

    Raises:
        ValidationError: The text cannot be read, names the other axis's hemisphere, writes
            minutes with ``m``, or lies outside the axis's range. The code is ``invalid``,
            ``wrong_axis``, ``minutes_letter`` or ``out_of_range``.
    """
    text = (text or "").strip()
    params = {
        "value": text,
        "axis": _("latitude") if axis == "lat" else _("longitude"),
        "limit": AXIS_LIMITS[axis],
    }
    invalid = forms.ValidationError(
        _(
            "“%(value)s” is not a %(axis)s the portal can read. Write degrees, minutes and "
            "seconds, degrees and decimal minutes, or decimal degrees, such as 48.9353, "
            "48 56.118 N or 48 56 7 N."
        ),
        code="invalid",
        params=params,
    )
    if MINUTES_LETTER.search(text):
        raise forms.ValidationError(
            _(
                "“%(value)s” writes minutes with the letter m. Leave the letter out: "
                "48 56 7 N."
            ),
            code="minutes_letter",
            params=params,
        )

    body = text
    hemispheres = []
    for pattern in (LEADING_HEMISPHERE, TRAILING_HEMISPHERE):
        found = pattern.search(body)
        if found:
            hemispheres.append(found[1].lower()[0])
            body = body[: found.start()] + body[found.end() :]
    if len(hemispheres) > 1:
        raise invalid
    if hemispheres and hemispheres[0] not in AXIS_HEMISPHERES[axis]:
        raise forms.ValidationError(
            _(
                "“%(value)s” ends in the hemisphere of the other axis. A %(axis)s "
                "takes %(letters)s."
            ),
            code="wrong_axis",
            params={**params, "letters": AXIS_HEMISPHERES[axis].upper()},
        )

    words = DEGREE_LETTER.sub(" ", body)
    numbers = NUMBER.findall(words)
    if not 1 <= len(numbers) <= 3 or re.search(r"[a-z]", words, re.IGNORECASE):
        raise invalid
    out_of_range = forms.ValidationError(
        _("“%(value)s” is outside the %(axis)s range of -%(limit)s to %(limit)s."),
        code="out_of_range",
        params=params,
    )
    # The package refuses whole degrees beyond 180 itself, which would read as unreadable text.
    if float(numbers[0].replace(",", ".")) > AXIS_LIMITS[axis]:
        raise out_of_range
    try:
        value = parse(text)
    except ValueError as error:
        raise invalid from error

    if abs(value) > AXIS_LIMITS[axis]:
        raise out_of_range
    return value


class Location(NamedTuple):
    """What a location input cleans to: a WGS 84 point with its elevation and uncertainty.

    Attributes:
        point: The point, in SRID 4326.
        elevation: Metres above mean sea level, or None.
        uncertainty: Metres, zero or more, or None.
    """

    point: geos.Point
    elevation: float | None = None
    uncertainty: float | None = None


class LocationWidget(forms.MultiWidget):
    """The location input: reference system, two coordinates, elevation and uncertainty.

    Args:
        full: Offer the reference system, elevation and uncertainty. Without it the widget asks
            for a latitude and a longitude in WGS 84 only, as an organization's point does.
        attrs: HTML attributes for the widget.
    """

    template_name = "location/widgets/location.html"
    full_parts = ("srid", "first", "second", "elevation", "uncertainty")
    point_parts = ("first", "second")

    def __init__(self, full=True, attrs=None):
        self.full = full
        self.parts = self.full_parts if full else self.point_parts
        inputs = {
            "srid": forms.TextInput(),
            "first": forms.TextInput(),
            "second": forms.TextInput(),
            "elevation": forms.NumberInput(attrs={"step": "any"}),
            "uncertainty": forms.NumberInput(attrs={"step": "any", "min": "0"}),
        }
        super().__init__({name: inputs[name] for name in self.parts}, attrs)

    def decompress(self, value):
        """Split a stored location into the values the inputs show.

        Args:
            value: A ``Location``, a bare GEOS point, or None.

        Returns:
            The input values in order, with the coordinates as WGS 84 decimal degrees written
            out in full, so that saving an unchanged form leaves the point where it was.
        """
        point = getattr(value, "point", value)
        values = {
            "srid": WGS84,
            "first": None,
            "second": None,
            "elevation": getattr(value, "elevation", None),
            "uncertainty": getattr(value, "uncertainty", None),
        }
        if point is not None:
            values["first"] = format(Decimal(repr(float(point.y))), "f")
            values["second"] = format(Decimal(repr(float(point.x))), "f")
        return [values[name] for name in self.parts]

    def get_systems(self):
        """Describe the suggested reference systems, as the script and the suggestions read them.

        Returns:
            A list of dicts with each system's ``code``, ``name`` and whether it is
            ``geographic`` (typed as degrees) rather than projected (typed in metres).
        """
        systems = []
        for code in SUGGESTED_SYSTEMS:
            system = SpatialReference(code)
            systems.append(
                {"code": code, "name": system.name, "geographic": system.geographic}
            )
        return systems

    def get_context(self, name, value, attrs):
        """Add what the template reads: ``full``, ``parts`` by name and ``systems``."""
        # A Location is a tuple, which MultiWidget would take for the inputs' own values.
        if isinstance(value, Location):
            value = self.decompress(value)
        context = super().get_context(name, value, attrs)
        widget = context["widget"]
        widget["full"] = self.full
        widget["parts"] = dict(zip(self.parts, widget["subwidgets"], strict=True))
        widget["systems"] = self.get_systems()
        widget["systems_id"] = f"{widget['attrs'].get('id') or name}_systems"
        return context


class LocationField(forms.MultiValueField):
    """Read a location typed in any supported notation and reference system, as WGS 84.

    Cleans to ``None`` when every input is empty, or to a ``Location`` whose point is in
    SRID 4326.

    Args:
        full: Take a reference system, elevation and uncertainty besides the two coordinates.
            Without it the field takes a latitude and a longitude in WGS 84 only.
        **kwargs: Passed to ``MultiValueField``.
    """

    def __init__(self, full=True, **kwargs):
        self.full = full
        fields = [forms.CharField(required=False), forms.CharField(required=False)]
        if full:
            fields = [
                forms.CharField(required=False),
                *fields,
                forms.FloatField(required=False),
                forms.FloatField(required=False),
            ]
        kwargs.setdefault("required", False)
        super().__init__(
            fields,
            require_all_fields=False,
            widget=LocationWidget(full=full),
            **kwargs,
        )

    def compress(self, data_list):
        """Combine the inputs into a ``Location`` in WGS 84, or None when all are empty.

        Args:
            data_list: The cleaned values of the inputs, in widget order.

        Returns:
            A ``Location``, or None.

        Raises:
            ValidationError: The coordinates are incomplete, unreadable or out of range, the
                reference system is unknown, or an elevation or uncertainty has no coordinates
                or a negative uncertainty.
        """
        if not data_list:
            return None
        if self.full:
            code, first, second, elevation, uncertainty = data_list
        else:
            (first, second), code, elevation, uncertainty = data_list, None, None, None

        if not first and not second:
            if elevation is not None or uncertainty is not None:
                raise forms.ValidationError(
                    _("Enter the coordinates the elevation and uncertainty belong to."),
                    code="no_point",
                )
            return None
        if not first or not second:
            raise forms.ValidationError(
                _("Enter both coordinates, or neither."), code="incomplete"
            )
        if uncertainty is not None and uncertainty < 0:
            raise forms.ValidationError(
                _("The uncertainty is a distance, so it cannot be negative."),
                code="negative_uncertainty",
            )
        return Location(self.read_point(code, first, second), elevation, uncertainty)

    def read_point(self, code, first, second):
        """Read two typed coordinates in a reference system and convert them to WGS 84.

        Args:
            code: The EPSG code as typed, or None or empty for WGS 84.
            first: The latitude, or the northing of a projected system.
            second: The longitude, or the easting of a projected system.

        Returns:
            A GEOS point in SRID 4326.

        Raises:
            ValidationError: The reference system is unknown, the coordinates cannot be read,
                or the point cannot be converted to WGS 84.
        """
        found = EPSG_CODE.fullmatch(str(code or WGS84).strip())
        try:
            system = SpatialReference(int(found[1])) if found else None
        except GDALException:
            system = None
        if system is None:
            raise forms.ValidationError(
                _(
                    "“%(value)s” is not a reference system the portal knows. Give its EPSG "
                    "code, such as 4326 or 25832."
                ),
                code="unknown_system",
                params={"value": code},
            )
        srid = int(found[1])
        outside_area = forms.ValidationError(
            _(
                "These coordinates lie outside the area EPSG:%(code)s covers, so "
                "they cannot be converted to WGS 84."
            ),
            code="out_of_range",
            params={"code": srid},
        )

        if system.geographic:
            point = geos.Point(
                parse_coordinate(second, "lon"),
                parse_coordinate(first, "lat"),
                srid=srid,
            )
        else:
            try:
                northing, easting = (
                    float(v.replace(",", ".")) for v in (first, second)
                )
            except ValueError:
                northing = easting = math.nan
            if not math.isfinite(northing + easting):
                raise forms.ValidationError(
                    _(
                        "Enter the northing and easting in metres, as the reference system "
                        "gives them, such as 5428667 and 456964."
                    ),
                    code="invalid",
                )
            # PROJ does not return for some projections given a magnitude like 1e18.
            if max(abs(northing), abs(easting)) > MAX_PROJECTED_METRES:
                raise outside_area
            point = geos.Point(easting, northing, srid=srid)

        if srid != WGS84:
            try:
                point.transform(WGS84)
            except GDALException as error:
                raise outside_area from error
            if abs(point.y) > AXIS_LIMITS["lat"] or abs(point.x) > AXIS_LIMITS["lon"]:
                raise outside_area
        return point


class LocationFormMixin:
    """Give a ``ModelForm`` of a ``LocatedRecord`` the location input.

    When ``location`` is among the form's fields, it becomes a full ``LocationField`` that
    starts from the instance's point, elevation and uncertainty. On clean the point goes to
    ``location`` and the elevation and uncertainty to the instance, so that model validation
    sees the three together.

    Example:
        ```python
        class RockSampleForm(LocationFormMixin, forms.ModelForm):
            class Meta:
                model = RockSample
                fields = ["name", "location"]
        ```
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "location" not in self.fields:
            return
        current = self.fields["location"]
        self.fields["location"] = LocationField(
            label=current.label, help_text=current.help_text
        )
        instance = self.instance
        stored = getattr(instance, "location", None)
        self.initial["location"] = (
            Location(
                stored,
                instance.location_elevation,
                instance.location_uncertainty,
            )
            if stored is not None
            else None
        )

    def clean(self):
        """Move the cleaned location's elevation and uncertainty onto the instance."""
        cleaned_data = super().clean()
        if "location" not in self.fields or "location" in self.errors:
            return cleaned_data
        location = cleaned_data.get("location")
        cleaned_data["location"] = location.point if location else None
        self.instance.location_elevation = location.elevation if location else None
        self.instance.location_uncertainty = location.uncertainty if location else None
        return cleaned_data
