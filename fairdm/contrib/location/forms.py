"""Forms and widgets for entering locations."""

import re

from django import forms
from django.utils.translation import gettext_lazy as _
from lat_lon_parser import parse

from .models import Point

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
