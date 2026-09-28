"""Forms and widgets for entering locations."""

from django import forms

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
