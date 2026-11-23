"""The widgets that read and write the cells of a type's file.

Each kind of column has one widget over ``import_export.widgets.Widget``. ``clean``
turns a cell into the value a model field stores and ``render`` turns a stored value
into a cell, so a value written by ``render`` is read back by ``clean`` as the same
value. A cell that cannot be read is refused with a ``ValueError`` and a reason, which
django-import-export turns into an error on the row.
"""

import datetime as dt
import re
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from import_export import widgets
from pint.errors import PintError

from fairdm.core.sample.models import Sample

TRUE = {"yes", "y", "true", "t", "1", "ja", "x", "✓"}
FALSE = {"no", "n", "false", "f", "0", "nein"}
DATE_FORMATS = ("%Y-%m-%d", "%d.%m.%Y")
TIME_FORMATS = ("%H:%M:%S", "%H:%M")
PARTIAL_DATE = re.compile(r"(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?")
QUANTITY = re.compile(
    r"\s*([+-]?(?:\d+[.,]?\d*|[.,]\d+)(?:[eE][+-]?\d+)?)\s*([^\d\s].*)?"
)
CHOICES_SHOWN = 8
CONCEPTS_SHOWN = 6
LABEL_KEYS = (
    "prefLabel",
    "altLabel",
    "notation",
    "skos:prefLabel",
    "skos:altLabel",
    "skos:notation",
)


class CellWidget(widgets.Widget):
    """What every cell widget shares: the column it reads and how a cell is emptied.

    Attributes:
        column: The column whose cells the widget reads and writes.
    """

    def __init__(self, column):
        """Keep the column.

        Args:
            column: The column whose cells the widget reads and writes.
        """
        super().__init__(coerce_to_string=False)
        self.column = column

    @staticmethod
    def is_empty(value) -> bool:
        """Say whether a cell holds nothing.

        Args:
            value: The cell as the file gave it.

        Returns:
            True for no value and for text that is only spaces.
        """
        return value is None or (isinstance(value, str) and not value.strip())

    @staticmethod
    def text_of(value) -> str:
        """Return a cell as text with the spaces around it removed.

        Args:
            value: The cell as the file gave it.

        Returns:
            Empty text for an empty cell, and a whole number a spreadsheet stored as a
            decimal without its point.
        """
        if value is None:
            return ""
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value).strip()

    def some_of_the_allowed(self, limit: int) -> str:
        """List the first of the values a column allows.

        Args:
            limit: The most values to list.

        Returns:
            The values joined by commas, with an ellipsis when there are more.
        """
        values = [pair[0] for pair in self.column.allowed]
        return ", ".join(values[:limit]) + (", …" if len(values) > limit else "")

    def render(self, value, obj=None, **kwargs):
        """Write a stored value as a cell.

        Args:
            value: The stored value.
            obj: The record the value belongs to.
            **kwargs: What django-import-export passes on.

        Returns:
            The cell, which is empty text for no value.
        """
        return "" if value is None else str(value)


class TextCellWidget(CellWidget):
    """Text, with the spaces around it removed."""

    def clean(self, value, row=None, **kwargs):
        """Read a text cell.

        Args:
            value: The cell as the file gave it.
            row: The row the cell is in.
            **kwargs: What django-import-export passes on.

        Returns:
            The text. An empty cell is None when the field may be null, and empty text
            when it may not.

        Raises:
            ValueError: When the text is longer than the field holds.
        """
        text = self.text_of(value)
        maximum = self.column.max_length
        if maximum and len(text) > maximum:
            raise ValueError(
                _("Is %(n)s characters long. The most it may hold is %(max)s.")
                % {"n": len(text), "max": maximum}
            )
        if not text and getattr(self.column.model_field, "null", False):
            return None
        return text


class NumberCellWidget(CellWidget):
    """A whole number, a decimal number or a coordinate."""

    def parse(self, value) -> Decimal:
        """Read a cell as a number inside the column's range.

        Args:
            value: The cell as the file gave it.

        Returns:
            The number.

        Raises:
            ValueError: When the cell is not a finite number, writes its decimals with a
                comma, or lies outside the range.
        """
        text = str(value).strip().replace(" ", "")
        if re.fullmatch(r"[+-]?\d+,\d+", text):
            raise ValueError(
                _(
                    "“%(v)s” uses a comma for decimals. Write it with a point, such as "
                    "%(fixed)s."
                )
                % {"v": value, "fixed": text.replace(",", ".")}
            )
        try:
            number = Decimal(text)
        except InvalidOperation:
            raise ValueError(_("“%(v)s” is not a number.") % {"v": value}) from None
        if not number.is_finite():
            raise ValueError(_("“%(v)s” is not a number.") % {"v": value})
        column = self.column
        if column.minimum is not None and number < Decimal(str(column.minimum)):
            raise ValueError(_("Must be at least %(min)s.") % {"min": column.minimum})
        if column.maximum is not None and number > Decimal(str(column.maximum)):
            raise ValueError(_("Must be at most %(max)s.") % {"max": column.maximum})
        return number

    def check_places(self, number: Decimal) -> None:
        """Refuse a number with more decimal places than the column allows.

        Args:
            number: The number.

        Raises:
            ValueError: When it has more decimal places.
        """
        if self.column.decimals is None:
            return
        exponent = number.normalize().as_tuple().exponent
        if isinstance(exponent, int) and -exponent > self.column.decimals:
            raise ValueError(
                _("Has more than %(n)s decimal places.") % {"n": self.column.decimals}
            )

    def clean(self, value, row=None, **kwargs):
        """Read a number cell.

        Args:
            value: The cell as the file gave it.
            row: The row the cell is in.
            **kwargs: What django-import-export passes on.

        Returns:
            None for an empty cell, an ``int`` for a whole-number column, a ``Decimal``
            for a column with decimal places and a ``float`` otherwise.

        Raises:
            ValueError: When the cell is not a number the column allows.
        """
        if self.is_empty(value):
            return None
        number = self.parse(value)
        if self.column.kind == "integer":
            if number != number.to_integral_value():
                raise ValueError(_("“%(v)s” is not a whole number.") % {"v": value})
            return int(number)
        if self.column.decimals is not None:
            self.check_places(number)
            return number
        return float(number)

    def render(self, value, obj=None, **kwargs):
        """Write a number as a cell, without a point when it is whole.

        Args:
            value: The stored number.
            obj: The record the value belongs to.
            **kwargs: What django-import-export passes on.

        Returns:
            The cell.
        """
        if value is None:
            return ""
        if isinstance(value, (Decimal, float)) and value == int(value):
            return str(int(value))
        if isinstance(value, Decimal):
            return format(value, "f")
        return str(value)


class BooleanCellWidget(CellWidget):
    """Yes or no."""

    def clean(self, value, row=None, **kwargs):
        """Read a yes-or-no cell.

        Args:
            value: The cell as the file gave it.
            row: The row the cell is in.
            **kwargs: What django-import-export passes on.

        Returns:
            None for an empty cell, otherwise True or False.

        Raises:
            ValueError: When the cell is neither yes nor no.
        """
        if isinstance(value, bool):
            return value
        if self.is_empty(value):
            return None
        text = self.text_of(value).lower()
        if text in TRUE:
            return True
        if text in FALSE:
            return False
        raise ValueError(_("“%(v)s” is not yes or no.") % {"v": value})

    def render(self, value, obj=None, **kwargs):
        """Write a boolean as yes or no.

        Args:
            value: The stored value.
            obj: The record the value belongs to.
            **kwargs: What django-import-export passes on.

        Returns:
            ``yes``, ``no`` or empty text.
        """
        if value is None:
            return ""
        return "yes" if value else "no"


class DateCellWidget(CellWidget):
    """A date, a date and time, or a time of day.

    A spreadsheet's own date or time object reads the same as the text for it. A
    date and time with no zone is read in the active time zone.
    """

    EXAMPLES = {
        "date": "2024-06-30",
        "datetime": "2024-06-30T14:05:42Z",
        "time": "14:05:42",
    }

    def clean(self, value, row=None, **kwargs):
        """Read a date, date and time or time cell.

        Args:
            value: The cell as the file gave it.
            row: The row the cell is in.
            **kwargs: What django-import-export passes on.

        Returns:
            None for an empty cell, otherwise a ``date``, ``datetime`` or ``time``
            as the column's kind asks.

        Raises:
            ValueError: When the text is not in a form the column reads.
        """
        if self.is_empty(value):
            return None
        kind = self.column.kind
        if not isinstance(value, str):
            return getattr(self, f"from_object_{kind}")(value)
        text = value.strip()
        parsed = getattr(self, f"from_text_{kind}")(text)
        if parsed is None:
            raise ValueError(
                _("“%(v)s” is not a date this column reads. Write it as %(example)s.")
                % {"v": value, "example": self.EXAMPLES[kind]}
            )
        return parsed

    @staticmethod
    def from_object_date(value):
        """Read a date a spreadsheet stored as a date or a date and time.

        Args:
            value: The spreadsheet's object.

        Returns:
            The date, or None when the object is neither.
        """
        if isinstance(value, dt.datetime):
            return value.date()
        return value if isinstance(value, dt.date) else None

    @staticmethod
    def from_object_datetime(value):
        """Read a date and time a spreadsheet stored as an object.

        Args:
            value: The spreadsheet's object.

        Returns:
            The datetime, in the active time zone when it has none, or None when the
            object is neither a date nor a date and time.
        """
        if not isinstance(value, dt.date):
            return None
        if not isinstance(value, dt.datetime):
            value = dt.datetime.combine(value, dt.time())
        return DateCellWidget.zoned(value)

    @staticmethod
    def from_object_time(value):
        """Read a time of day a spreadsheet stored as an object.

        Args:
            value: The spreadsheet's object.

        Returns:
            The time, or None when the object is neither a time nor a date and time.
        """
        if isinstance(value, dt.datetime):
            return value.time()
        return value if isinstance(value, dt.time) else None

    @staticmethod
    def from_text_date(text: str):
        """Read a date written as text.

        Args:
            text: The cell, without spaces around it.

        Returns:
            The date, or None when the text is in no form the column reads.
        """
        for form in DATE_FORMATS:
            try:
                return dt.datetime.strptime(text, form).date()
            except ValueError:
                continue
        return None

    @staticmethod
    def from_text_datetime(text: str):
        """Read a date and time written as text.

        Args:
            text: The cell, without spaces around it.

        Returns:
            The datetime, in the active time zone when it has none, or None when
            the text is in no form the column reads.
        """
        try:
            parsed = dt.datetime.fromisoformat(text)
        except ValueError:
            return None
        return DateCellWidget.zoned(parsed)

    @staticmethod
    def from_text_time(text: str):
        """Read a time of day written as text.

        Args:
            text: The cell, without spaces around it.

        Returns:
            The time, or None when the text is in no form the column reads.
        """
        for form in TIME_FORMATS:
            try:
                return dt.datetime.strptime(text, form).time()
            except ValueError:
                continue
        return None

    @staticmethod
    def zoned(value: dt.datetime) -> dt.datetime:
        """Put a date and time with no zone in the active time zone.

        Args:
            value: The datetime.

        Returns:
            The datetime, unchanged when it has a zone or time zones are not in use.
        """
        if settings.USE_TZ and timezone.is_naive(value):
            return timezone.make_aware(value)
        return value

    def render(self, value, obj=None, **kwargs):
        """Write a date, date and time or time as a cell.

        Args:
            value: The stored value.
            obj: The record the value belongs to.
            **kwargs: What django-import-export passes on.

        Returns:
            A date as ``YYYY-MM-DD``, a datetime as ISO 8601 in UTC with its
            seconds and a time as ``HH:MM:SS``.
        """
        if value is None:
            return ""
        if isinstance(value, dt.datetime):
            if timezone.is_aware(value):
                value = value.astimezone(dt.UTC)
                return value.isoformat(timespec="seconds").replace("+00:00", "Z")
            return value.isoformat(timespec="seconds")
        if isinstance(value, dt.date):
            return value.isoformat()
        if isinstance(value, dt.time):
            return value.strftime("%H:%M:%S")
        return str(value)


class PartialDateCellWidget(CellWidget):
    """A year, a year and month, or a whole date."""

    def clean(self, value, row=None, **kwargs):
        """Read a partial date cell.

        Args:
            value: The cell as the file gave it.
            row: The row the cell is in.
            **kwargs: What django-import-export passes on.

        Returns:
            None for an empty cell, otherwise the text the field stores.

        Raises:
            ValueError: When the cell is not ``YYYY``, ``YYYY-MM`` or ``YYYY-MM-DD``, or
                names a month or day that does not exist.
        """
        if self.is_empty(value):
            return None
        if isinstance(value, dt.date):
            return value.isoformat()[:10]
        text = self.text_of(value)
        found = PARTIAL_DATE.fullmatch(text)
        if found and self.exists(*found.groups()):
            return text
        raise ValueError(
            _("“%(v)s” is not YYYY, YYYY-MM or YYYY-MM-DD.") % {"v": value}
        )

    @staticmethod
    def exists(year, month, day) -> bool:
        """Say whether the parts of a partial date name a real date.

        Args:
            year: The year as text.
            month: The month as text, or None.
            day: The day as text, or None.

        Returns:
            False for a month past 12 or a day the month does not have.
        """
        try:
            dt.date(int(year), int(month or 1), int(day or 1))
        except ValueError:
            return False
        return True


class ChoiceCellWidget(CellWidget):
    """One of the values a field allows, by the value or by what it means."""

    def clean(self, value, row=None, **kwargs):
        """Read a choice cell.

        Args:
            value: The cell as the file gave it.
            row: The row the cell is in.
            **kwargs: What django-import-export passes on.

        Returns:
            The stored value. An empty cell is None when the field may be null,
            and empty text when it may not.

        Raises:
            ValueError: When the cell matches no value or meaning, ignoring case.
        """
        text = self.text_of(value)
        if not text:
            return None if getattr(self.column.model_field, "null", False) else ""
        for stored, meaning in self.column.allowed:
            if text.lower() in (stored.lower(), meaning.lower()):
                return stored
        raise ValueError(
            _("“%(v)s” is not one of the allowed values: %(values)s.")
            % {"v": value, "values": self.some_of_the_allowed(CHOICES_SHOWN)}
        )


class ConceptCellWidget(CellWidget):
    """A concept by its label in any language, its code or its address.

    The values are looked up in a table built the first time a cell is read.
    """

    def __init__(self, column):
        """Keep the column.

        Args:
            column: The column whose cells the widget reads and writes.
        """
        super().__init__(column)
        self.table = None

    @staticmethod
    def labels_of(data: dict) -> set[str]:
        """Collect the labels and codes a concept's document gives.

        Args:
            data: The concept's document.

        Returns:
            Its preferred and alternative labels in every language, and its notations.
        """
        found = set()
        for key in LABEL_KEYS:
            values = data.get(key)
            for item in values if isinstance(values, list) else [values]:
                if isinstance(item, dict):
                    item = item.get("@value")
                if item:
                    found.add(str(item))
        return found

    def lookup(self) -> dict:
        """Build the table of what a cell may hold, once.

        Returns:
            The concepts of the column's vocabulary by address, code and label, lower
            case. A preferred label always wins over another concept's other labels.
        """
        if self.table is None:
            from controlled_vocabularies.models import Record

            records = list(
                Record.objects.filter(self.column.model_field.resolve_restriction())
            )
            table = {}
            for record in records:
                table.setdefault(record.pref_label.strip().lower(), record)
            for record in records:
                keys = {record.uri, record.slug, *self.labels_of(record.data or {})}
                for key in keys:
                    table.setdefault(key.strip().lower(), record)
            self.table = table
        return self.table

    def clean(self, value, row=None, **kwargs):
        """Read a concept cell.

        Args:
            value: The cell as the file gave it.
            row: The row the cell is in.
            **kwargs: What django-import-export passes on.

        Returns:
            The concept, or None for an empty cell.

        Raises:
            ValueError: When the vocabulary has no concepts or has none the cell names.
        """
        text = self.text_of(value)
        if not text:
            return None
        table = self.lookup()
        if not table:
            raise ValueError(_("This column has no values to choose from."))
        record = table.get(text.lower())
        if record is None:
            raise ValueError(
                _("“%(v)s” is not in the list. Allowed: %(values)s.")
                % {"v": value, "values": self.some_of_the_allowed(CONCEPTS_SHOWN)}
            )
        return record

    def render(self, value, obj=None, **kwargs):
        """Write a concept as its preferred label.

        Args:
            value: The concept.
            obj: The record the value belongs to.
            **kwargs: What django-import-export passes on.

        Returns:
            The preferred label, which is the same in every language.
        """
        return "" if value is None else value.pref_label


class SampleCellWidget(CellWidget):
    """A sample by portal ID, or by Local ID or name within the dataset.

    Every lookup reads the samples the person may see, so a sample they may not see is
    refused with the words used for one that does not exist.

    Attributes:
        dataset: The dataset the file is imported into.
        user: The person importing, or None for a visitor.
    """

    def __init__(self, column, dataset=None, user=None):
        """Keep the column, the dataset and the person.

        Args:
            column: The column whose cells the widget reads and writes.
            dataset: The dataset the file is imported into.
            user: The person importing, or None for a visitor.
        """
        super().__init__(column)
        self.dataset = dataset
        self.user = user

    def clean(self, value, row=None, **kwargs):
        """Read a sample cell.

        Args:
            value: The cell as the file gave it.
            row: The row the cell is in.
            **kwargs: What django-import-export passes on.

        Returns:
            The sample, or None for an empty cell.

        Raises:
            ValueError: When no sample the person may see has the portal ID, and none in
                the dataset has the Local ID or name, or when the Local ID or name is
                shared by several samples.
        """
        text = self.text_of(value)
        if not text:
            return None
        visible = Sample.objects.visible_to(self.user)
        found = visible.filter(uuid=text).first()
        if found is not None:
            return found
        if self.dataset is not None:
            in_dataset = visible.filter(dataset=self.dataset)
            for field in ("local_id", "name"):
                matches = list(in_dataset.filter(**{field: text})[:2])
                if len(matches) == 1:
                    return matches[0]
                if len(matches) > 1:
                    raise ValueError(
                        _(
                            "Several samples in this dataset have this Local ID or "
                            "name. Use the portal ID."
                        )
                    )
        raise ValueError(
            _("No sample you may see has this portal ID, Local ID or name.")
        )

    def render(self, value, obj=None, **kwargs):
        """Write a sample as its portal ID.

        Args:
            value: The sample.
            obj: The record the value belongs to.
            **kwargs: What django-import-export passes on.

        Returns:
            The portal ID.
        """
        return "" if value is None else str(value.uuid)


class QuantityCellWidget(NumberCellWidget):
    """A number in the column's unit, or a number and a unit to convert from."""

    def clean(self, value, row=None, **kwargs):
        """Read a quantity cell.

        Args:
            value: The cell as the file gave it.
            row: The row the cell is in.
            **kwargs: What django-import-export passes on.

        Returns:
            None for an empty cell, otherwise a quantity in the field's unit.

        Raises:
            ValueError: When the cell is not a number, or its unit is unknown or
                does not convert to the field's.
        """
        if self.is_empty(value):
            return None
        if isinstance(value, str):
            found = QUANTITY.fullmatch(value)
            if not found:
                raise ValueError(
                    _("“%(v)s” is not a number with a unit.") % {"v": value}
                )
            magnitude, unit = found.group(1), (found.group(2) or "").strip()
        else:
            magnitude, unit = value, ""
        number = self.parse(magnitude)
        self.check_places(number)
        field = self.column.model_field
        if self.column.decimals is None:
            number = float(number)
        quantity = field.ureg.Quantity(number, field.base_units)
        if not unit:
            return quantity
        try:
            given = field.ureg.Quantity(number, unit)
            return given.to(field.base_units)
        except (PintError, TypeError, ValueError, AttributeError):
            raise ValueError(
                _("“%(unit)s” is not a unit that converts to %(base)s.")
                % {"unit": unit, "base": field.base_units}
            ) from None

    def render(self, value, obj=None, **kwargs):
        """Write a quantity as its number in the field's unit.

        Args:
            value: The quantity.
            obj: The record the value belongs to.
            **kwargs: What django-import-export passes on.

        Returns:
            The number.
        """
        if value is None:
            return ""
        field = self.column.model_field
        return super().render(value.to(field.base_units).magnitude)


WIDGETS = {
    "text": TextCellWidget,
    "id": TextCellWidget,
    "integer": NumberCellWidget,
    "number": NumberCellWidget,
    "latitude": NumberCellWidget,
    "longitude": NumberCellWidget,
    "boolean": BooleanCellWidget,
    "date": DateCellWidget,
    "datetime": DateCellWidget,
    "time": DateCellWidget,
    "partial_date": PartialDateCellWidget,
    "choice": ChoiceCellWidget,
    "concept": ConceptCellWidget,
    "quantity": QuantityCellWidget,
}
"""The widget for each kind of column except a sample, which needs a dataset."""


def widget_for(column, dataset=None, user=None):
    """Return the widget that reads and writes a column's cells.

    Args:
        column: The column.
        dataset: The dataset a file is imported into, which a sample column looks in.
        user: The person importing, or None for a visitor.

    Returns:
        The widget for the column's kind, text for a kind with none.
    """
    if column.kind == "sample":
        return SampleCellWidget(column, dataset=dataset, user=user)
    return WIDGETS.get(column.kind, TextCellWidget)(column)


def render_cell(column, instance) -> str:
    """Write one column of one record as the cell an export holds.

    Args:
        column: The column.
        instance: The sample or measurement.

    Returns:
        The portal ID for the ``portal_id`` column, the sample's name for the sample
        name column, a point's latitude or longitude for those columns, and otherwise
        the attribute written by the column's widget.
    """
    if column.name == "portal_id":
        return instance.uuid or ""
    if column.name == "sample_name":
        sample = getattr(instance, "sample", None)
        return sample.name if sample else ""
    widget = widget_for(column)
    if column.kind in ("latitude", "longitude"):
        point = instance.location
        if point is None:
            return ""
        return widget.render(point.y if column.kind == "latitude" else point.x)
    return widget.render(getattr(instance, column.attribute))
