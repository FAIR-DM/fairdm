"""Form fields and widgets for partial dates and fixed-precision decimals."""

import datetime

from django import forms
from partial_date import PartialDate


class PartialDateWidget(forms.SelectDateWidget):
    """Date select widget that orders year, month, day and accepts partial dates.

    Args:
        attrs: HTML attributes for the rendered selects.
        years: Years offered in the year select. Defaults to 1900 through the
            current year, newest first.
        months: Months offered in the month select.
        empty_label: Label of the empty choice in each select.
    """

    def __init__(self, attrs=None, years=None, months=None, empty_label=None):
        super().__init__(attrs, years, months, empty_label)
        if not years:
            this_year = datetime.date.today().year
            self.years = list(range(1900, this_year + 1))
            self.years.reverse()

    def get_context(self, name, value, attrs):
        """Reorder the subwidgets to year, month, day."""
        context = super().get_context(name, value, attrs)
        m, d, y = context["widget"]["subwidgets"]
        context["widget"]["subwidgets"] = [y, m, d]
        return context

    def format_value(self, value):
        """Split a ``PartialDate`` into the year, month and day the selects show."""
        if isinstance(value, PartialDate):
            return {
                "year": value.date.year,
                "month": (
                    value.date.month if value.precision >= PartialDate.MONTH else None
                ),
                "day": value.date.day if value.precision == PartialDate.DAY else None,
            }
        return {"year": None, "month": None, "day": None}

    def value_from_datadict(self, data, files, name):
        """Join the year, month and day selects into a partial-date string."""
        y = data.get(self.year_field % name)
        m = data.get(self.month_field % name)
        d = data.get(self.day_field % name)
        if y == m == d == "":
            return None

        value = y
        if m:
            value += f"-{m}"
        if m and d:
            value += f"-{d}"

        return value


class PartialDateFormField(forms.CharField):
    """Field with separate year, month and day selects for a ``PartialDateField``."""

    widget = PartialDateWidget


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
