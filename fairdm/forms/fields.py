"""Form fields and widgets for partial dates, quantities and fixed-precision decimals."""

import pint
from django import forms
from quantityfield import fields


class PartialDateField(forms.CharField):
    """Text field for a partial date typed as ``yyyy-mm-dd``, with a masked input."""

    widget = forms.TextInput(
        attrs={
            "x-mask": "****-**-**",
            "placeholder": "yyyy-mm-dd",
        }
    )

    def clean(self, value):
        """Strip leading and trailing hyphens, returning ``None`` for an empty value."""
        if value:
            return value.strip("-")
        return None


class QuantityFormFieldMixin:
    """Hand the number input and unit select a stored quantity in the field's base units.

    django-pint's form field hands its widget the quantity itself, and the widget
    names the unit the way pint prints it ("meter"). That matches none of the unit
    choices when the field spells its units short ("m"), so the select shows no unit
    and an unchanged form fails to save.
    """

    def prepare_value(self, value):
        """Split a quantity into its magnitude in base units and the base unit choice."""
        if isinstance(value, pint.Quantity):
            return [value.to(self.base_units).magnitude, self.base_units]
        return super().prepare_value(value)


class QuantityFormField(QuantityFormFieldMixin, fields.QuantityFormField):
    """django-pint's float quantity form field, showing stored values in base units."""


class IntegerQuantityFormField(QuantityFormFieldMixin, fields.IntegerQuantityFormField):
    """django-pint's integer quantity form field, showing stored values in base units."""


class DecimalQuantityFormField(QuantityFormFieldMixin, fields.DecimalQuantityFormField):
    """django-pint's decimal quantity form field, showing stored values in base units."""


class DecimalField(forms.DecimalField):
    """Decimal field whose input is masked to the allowed integer and decimal places.

    Args:
        max_value: Accepted for signature compatibility but not applied.
        min_value: Accepted for signature compatibility but not applied.
        max_digits: Total number of digits allowed. Required.
        decimal_places: Number of digits after the decimal point. Required.
        **kwargs: Passed to :class:`django.forms.DecimalField`.

    Attributes:
        widget: The widget class, a plain text input carrying the mask.

    Raises:
        ValueError: ``max_digits`` or ``decimal_places`` is missing.
    """

    widget = forms.TextInput

    def __init__(
        self,
        *,
        max_value=None,
        min_value=None,
        max_digits=None,
        decimal_places=None,
        **kwargs,
    ):
        self.max_digits, self.decimal_places = max_digits, decimal_places
        if not self.max_digits or not self.decimal_places:
            raise ValueError("max_digits and decimal_places must be specified")
        self.precision = "9" * self.decimal_places
        self.integer_places = "9" * (self.max_digits - self.decimal_places)
        self.mask = f"{self.integer_places}.{self.precision}"
        super().__init__(**kwargs)

    def widget_attrs(self, widget):
        """Add the input mask, allowing a minus sign unless ``min_value`` is >= 0."""
        attrs = super().widget_attrs(widget)
        if self.min_value is None or (
            self.min_value is not None and self.min_value < 0
        ):
            attrs["x-mask:dynamic"] = (
                f"$input.startsWith('-') ? '-{self.mask}' : '{self.mask}'"
            )
        else:
            attrs["x-mask"] = self.mask
        return attrs


class LatitudeField(DecimalField):
    """Decimal field for a latitude, masked to seven digits with five decimal places.

    Args:
        *args: Passed to :class:`DecimalField`.
        max_digits: Total number of digits allowed.
        decimal_places: Number of digits after the decimal point.
        **kwargs: Passed to :class:`DecimalField`.
    """

    def __init__(self, *args, max_digits=7, decimal_places=5, **kwargs):
        super().__init__(
            *args, max_digits=max_digits, decimal_places=decimal_places, **kwargs
        )


class LongitudeField(DecimalField):
    """Decimal field for a longitude, masked to eight digits with five decimal places.

    Args:
        *args: Passed to :class:`DecimalField`.
        max_digits: Total number of digits allowed.
        decimal_places: Number of digits after the decimal point.
        **kwargs: Passed to :class:`DecimalField`.
    """

    def __init__(self, *args, max_digits=8, decimal_places=5, **kwargs):
        super().__init__(
            *args, max_digits=max_digits, decimal_places=decimal_places, **kwargs
        )
