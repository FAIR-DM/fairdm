import datetime

from django import forms
from partial_date import PartialDate


class PartialDateWidget(forms.SelectDateWidget):
    def __init__(self, attrs=None, years=None, months=None, empty_label=None):
        super().__init__(attrs, years, months, empty_label)
        if not years:
            this_year = datetime.date.today().year
            self.years = list(range(1900, this_year + 1))
            self.years.reverse()

    def get_context(self, name, value, attrs):
        # reorder the subwidgets to year, month, day
        context = super().get_context(name, value, attrs)
        m, d, y = context["widget"]["subwidgets"]
        context["widget"]["subwidgets"] = [y, m, d]
        return context

    def format_value(self, value):
        # convert PartialDate to dict for SelectDateWidget
        if isinstance(value, PartialDate):
            return {
                "year": value.date.year,
                "month": value.date.month if value.precision >= PartialDate.MONTH else None,
                "day": value.date.day if value.precision == PartialDate.DAY else None,
            }
        return {"year": None, "month": None, "day": None}

    def value_from_datadict(self, data, files, name):
        # build a PartialDate from the separate fields

        y = data.get(self.year_field % name)
        m = data.get(self.month_field % name)
        d = data.get(self.day_field % name)
        if y == m == d == "":
            return None

        # build the date string
        value = y
        if m:
            value += f"-{m}"
        if m and d:
            value += f"-{d}"

        return value


class PartialDateFormField(forms.CharField):
    """A form field that provides separate fields for day, month, and year. Values from the separate fields are combined into a value suitable for a partial_date.PartialDateField."""

    widget = PartialDateWidget


class PartialDateField(forms.CharField):
    widget = forms.TextInput(
        attrs={
            "x-mask": "****-**-**",
            "placeholder": "yyyy-mm-dd",
        }
    )

    def clean(self, value):
        if value:
            # Remove leading and trailing hyphens
            return value.strip("-")
        return None


class DecimalField(forms.DecimalField):
    """A custom DecimalField that formats the input with a specific mask for integer and decimal places."""

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
        self.precision = "9" * self.decimal_places  # Adjusting max_digits based on precision
        self.integer_places = "9" * (self.max_digits - self.decimal_places)
        self.mask = f"{self.integer_places}.{self.precision}"
        super().__init__(**kwargs)

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        if self.min_value is None or (self.min_value is not None and self.min_value < 0):
            # If min_value is negative, allow negative values in the mask
            attrs["x-mask:dynamic"] = f"$input.startsWith('-') ? '-{self.mask}' : '{self.mask}'"
        else:
            # If min_value is non-negative, use the standard mask
            attrs["x-mask"] = self.mask
        return attrs


class LatitudeField(DecimalField):
    """A custom DecimalField for coordinates that allows negative values and formats the input with a specific mask for integer and decimal places."""

    def __init__(self, *args, max_digits=7, decimal_places=5, **kwargs):
        super().__init__(*args, max_digits=max_digits, decimal_places=decimal_places, **kwargs)


class LongitudeField(DecimalField):
    """A custom DecimalField for coordinates that allows negative values and formats the input with a specific mask for integer and decimal places."""

    def __init__(self, *args, max_digits=8, decimal_places=5, **kwargs):
        super().__init__(*args, max_digits=max_digits, decimal_places=decimal_places, **kwargs)
