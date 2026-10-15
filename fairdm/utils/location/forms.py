"""Forms and widgets for entering locations."""

from decimal import Decimal
from typing import NamedTuple

from django import forms
from django.contrib.gis import geos
from django.utils.translation import gettext_lazy as _


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
    """The location input: a latitude and a longitude in WGS 84, elevation and uncertainty.

    Args:
        full: Offer the elevation and uncertainty. Without it the widget asks for a latitude
            and a longitude only, as an organization's point does.
        attrs: HTML attributes for the widget.
    """

    template_name = "location/widgets/location.html"
    full_parts = ("first", "second", "elevation", "uncertainty")
    point_parts = ("first", "second")

    def __init__(self, full=True, attrs=None):
        self.full = full
        self.parts = self.full_parts if full else self.point_parts
        inputs = {
            "first": forms.NumberInput(
                attrs={"step": "any", "min": "-90", "max": "90"}
            ),
            "second": forms.NumberInput(
                attrs={"step": "any", "min": "-180", "max": "180"}
            ),
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
            "first": None,
            "second": None,
            "elevation": getattr(value, "elevation", None),
            "uncertainty": getattr(value, "uncertainty", None),
        }
        if point is not None:
            values["first"] = format(Decimal(repr(float(point.y))), "f")
            values["second"] = format(Decimal(repr(float(point.x))), "f")
        return [values[name] for name in self.parts]

    def get_context(self, name, value, attrs):
        """Add what the template reads: ``full`` and ``parts`` by name."""
        # A Location is a tuple, which MultiWidget would take for the inputs' own values.
        if isinstance(value, Location):
            value = self.decompress(value)
        context = super().get_context(name, value, attrs)
        widget = context["widget"]
        widget["full"] = self.full
        widget["parts"] = dict(zip(self.parts, widget["subwidgets"], strict=True))
        return context


class LocationField(forms.MultiValueField):
    """Read a latitude and a longitude in signed decimal degrees, WGS 84.

    Cleans to ``None`` when every input is empty, or to a ``Location`` whose point is in
    SRID 4326.

    Args:
        full: Take an elevation and uncertainty besides the two coordinates. Without it the
            field takes a latitude and a longitude only.
        **kwargs: Passed to ``MultiValueField``.
    """

    def __init__(self, full=True, **kwargs):
        self.full = full
        fields = [
            forms.FloatField(required=False, min_value=-90, max_value=90),
            forms.FloatField(required=False, min_value=-180, max_value=180),
        ]
        if full:
            fields = [
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
        """Combine the inputs into a ``Location`` in WGS 84, or None when all are empty.

        Args:
            data_list: The cleaned values of the inputs, in widget order.

        Returns:
            A ``Location``, or None.

        Raises:
            ValidationError: Only one coordinate is given, or an elevation or uncertainty has
                no coordinates.
        """
        if not data_list:
            return None
        first, second, elevation, uncertainty = [*data_list, None, None][:4]

        if first is None and second is None:
            if elevation is not None or uncertainty is not None:
                raise forms.ValidationError(
                    _("Enter the coordinates the elevation and uncertainty belong to."),
                    code="no_point",
                )
            return None
        if first is None or second is None:
            raise forms.ValidationError(
                _("Enter both coordinates, or neither."), code="incomplete"
            )
        point = geos.Point(second, first, srid=4326)
        return Location(point, elevation, uncertainty)


class LocationFormMixin:
    """Give a ``ModelForm`` of a model with a ``location`` the location input.

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
        # The input holds these two itself; a registration with no field list adds them again.
        self.fields.pop("location_elevation", None)
        self.fields.pop("location_uncertainty", None)
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
