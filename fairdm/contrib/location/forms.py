from django import forms

from .models import Point


class PointForm(forms.ModelForm):
    class Meta:
        model = Point
        fields = ["x", "y"]


class LatitudeWidget(forms.TextInput):
    def __init__(self, attrs=None, precision=5):
        self.precision = precision
        x_precision = "9" * self.precision  # Adjusting max_digits based on precision
        default_attrs = {"x-mask:dynamic": f"$input.startsWith('-') ? '-99.{x_precision}' : '99.{x_precision}'"}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)


class LongitudeWidget(forms.TextInput):
    def __init__(self, attrs=None, precision=5):
        self.precision = precision
        x_precision = "9" * self.precision  # Adjusting max_digits based on precision
        default_attrs = {"x-mask:dynamic": f"$input.startsWith('-') ? '-999.{x_precision}' : '999.{x_precision}'"}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)
