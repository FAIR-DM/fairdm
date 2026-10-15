"""The location as four columns in tabular import and export."""

import math

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from import_export.fields import Field
from import_export.widgets import FloatWidget

from fairdm.contrib.location.forms import (
    MAX_TYPED_LENGTH,
    LocationField,
    parse_coordinate,
)


class MeasureWidget(FloatWidget):
    """A number cell that exports as the number itself, never localised, and empty for none."""

    def __init__(self):
        super().__init__(coerce_to_string=False)

    def clean(self, value, row=None, **kwargs):
        """Read one cell as a number.

        Args:
            value: The cell.
            row: The row the cell is in.
            **kwargs: Passed through by import-export.

        Returns:
            The number, or None for an empty cell.

        Raises:
            ValueError: The cell is not a number, or is ``nan`` or infinite.
        """
        number = super().clean(value, row=row, **kwargs)
        if number is not None and not math.isfinite(number):
            raise ValueError(
                _("“%(value)s” is not a number a measurement can have.")
                % {"value": value}
            )
        return number

    def render(self, value, obj=None, **kwargs):
        """Return the number, or an empty cell when the record has none."""
        return "" if value is None else value


class CoordinateWidget(MeasureWidget):
    """Read a latitude or a longitude typed in any notation the location input accepts.

    Args:
        axis: ``"lat"`` or ``"lon"``.
    """

    def __init__(self, axis):
        self.axis = axis
        super().__init__()

    def clean(self, value, row=None, **kwargs):
        """Read one cell as signed decimal degrees.

        Args:
            value: The cell.
            row: The row the cell is in.
            **kwargs: Passed through by import-export.

        Returns:
            The coordinate in decimal degrees, or None for an empty cell.

        Raises:
            ValueError: The cell cannot be read as this axis, with the input's message.
        """
        if value is None or str(value).strip() == "":
            return None
        try:
            return parse_coordinate(str(value), self.axis)
        except ValidationError as error:
            raise ValueError(" ".join(error.messages)) from error


class CoordinateField(Field):
    """The latitude or the longitude of a record's point.

    Args:
        axis: ``"lat"`` or ``"lon"``.
    """

    def __init__(self, axis):
        name = "latitude" if axis == "lat" else "longitude"
        super().__init__(column_name=name, widget=CoordinateWidget(axis))
        self.axis = axis

    def get_value(self, instance):
        """Return the record's own latitude or longitude, or None when it has no point."""
        point = getattr(instance, "location", None)
        if point is None:
            return None
        return point.y if self.axis == "lat" else point.x


def location_fields():
    """Build the four columns a ``location`` stands for in a resource.

    Returns:
        A dict of field name to ``Field``, in column order: ``latitude``, ``longitude``,
        ``location_elevation`` and ``location_uncertainty``.
    """
    return {
        "latitude": CoordinateField("lat"),
        "longitude": CoordinateField("lon"),
        "location_elevation": Field(
            attribute="location_elevation",
            column_name="location_elevation",
            widget=MeasureWidget(),
        ),
        "location_uncertainty": Field(
            attribute="location_uncertainty",
            column_name="location_uncertainty",
            widget=MeasureWidget(),
        ),
    }


class LocatedResourceMixin:
    """Give a resource of a ``LocatedRecord`` the four location columns.

    Where ``location`` is among the resource's fields, it is replaced by ``latitude``,
    ``longitude``, ``location_elevation`` and ``location_uncertainty``. Export writes the
    record's own values. Import reads the columns with the same rules as the location input
    and reports a row it refuses as invalid, so the row is not saved. A file without the
    columns leaves each record's location as it was, and a file with only some of them
    changes only those.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "location" not in self.fields:
            return
        expanded = {}
        for name, field in self.fields.items():
            if name == "location":
                for column, new in location_fields().items():
                    expanded.setdefault(column, self.fields.get(column, new))
            else:
                expanded.setdefault(name, field)
        self.fields = expanded

    def expand_order(self, order):
        """Put the four columns where ``location`` stood in an ordering.

        Args:
            order: Field names.

        Returns:
            The names, with ``location`` replaced by its four columns once each.
        """
        columns = list(location_fields())
        result = []
        for name in order:
            if name == "location":
                result.extend(c for c in columns if c not in result)
            elif name not in result:
                result.append(name)
        return tuple(result)

    def get_export_order(self):
        """Return the export order with the location columns in place of ``location``."""
        return self.expand_order(super().get_export_order())

    def get_import_order(self):
        """Return the import order with the location columns in place of ``location``."""
        return self.expand_order(super().get_import_order())

    def import_instance(self, instance, row, **kwargs):
        """Import the row's fields, then set the point from its coordinate columns.

        Args:
            instance: The record being imported.
            row: The row.
            **kwargs: Passed to the resource.

        Raises:
            ValidationError: The columns of any field, or the location as a whole, are refused.
        """
        errors = {}
        try:
            super().import_instance(instance, row, **kwargs)
        except ValidationError as error:
            errors = error.update_error_dict(errors)
        if not any(column in row for column in location_fields()):
            return
        try:
            self.set_location(instance, row)
        except ValidationError as error:
            errors["location"] = [*errors.get("location", []), *error.error_list]
        if errors:
            raise ValidationError(errors)

    def set_location(self, instance, row):
        """Set the record's point from the row's coordinates, by the input's rules.

        Args:
            instance: The record being imported, whose elevation and uncertainty are already
                set from their columns.
            row: The row.

        Raises:
            ValidationError: The coordinates are too long, cannot be read, are out of range or
                incomplete, or an elevation or uncertainty has no coordinates or is negative.
        """
        point = instance.location
        current = {"latitude": point.y, "longitude": point.x} if point else {}
        coordinates = [
            row.get(name, current.get(name)) for name in ("latitude", "longitude")
        ]
        if any(len(str(value).strip()) > MAX_TYPED_LENGTH for value in coordinates):
            raise ValidationError(
                _("A coordinate is at most %(limit)s characters long."),
                code="max_length",
                params={"limit": MAX_TYPED_LENGTH},
            )
        location = LocationField().compress(
            [
                None,
                *(str(value) if value is not None else "" for value in coordinates),
                instance.location_elevation,
                instance.location_uncertainty,
            ]
        )
        instance.location = location.point if location else None
