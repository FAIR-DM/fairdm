"""The columns of a record type's file, worked out from its configuration.

Nothing here is written per type. A sample or measurement type that is registered gets
its columns from the model and its configuration each time they are asked for:

- the identifiers first: the portal ID (``portal_id``) and the Local ID,
- the name, and for a measurement the sample it was made on,
- the type's own fields, in the order the model declares them,
- the fields every sample or measurement has: status and the four location columns.

When the configuration lists ``resource_fields`` only those are offered, plus the
identifiers and whatever a new record cannot be saved without.
"""

import re
from dataclasses import dataclass, field
from decimal import Decimal

from controlled_vocabularies.fields import ConceptField
from controlled_vocabularies.models import Record
from django.db import models
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _
from partial_dates.fields import PartialDateField
from quantityfield.fields import QuantityFieldMixin

from fairdm.core.measurement.models import Measurement
from fairdm.core.sample.models import Sample
from fairdm.registry.config import flatten_fields
from fairdm.utils.inspection import FieldInspector
from fairdm.utils.location.resources import LOCATION_COLUMNS

KIND_LABELS = {
    "id": _("Portal ID"),
    "text": _("Text"),
    "integer": _("Whole number"),
    "number": _("Number"),
    "boolean": _("Yes or no"),
    "date": _("Date"),
    "datetime": _("Date and time"),
    "time": _("Time"),
    "partial_date": _("Date, as precise as known"),
    "concept": _("One of a list"),
    "choice": _("One of a list"),
    "sample": _("A sample"),
    "quantity": _("Number with a unit"),
    "latitude": _("Decimal degrees"),
    "longitude": _("Decimal degrees"),
}
"""What each kind of column is called on screen."""

UNIT_IN_LABEL = re.compile(r"\s*\(([^)]+)\)\s*$")
"""A unit in brackets at the end of a label, such as ``Weight (grams)``."""

FRICTIONLESS_TYPES = {
    "id": "string",
    "text": "string",
    "integer": "integer",
    "number": "number",
    "boolean": "boolean",
    "date": "date",
    "datetime": "datetime",
    "time": "time",
    "partial_date": "string",
    "concept": "string",
    "choice": "string",
    "sample": "string",
    "quantity": "number",
    "latitude": "number",
    "longitude": "number",
}
"""The Frictionless field type of each kind of column."""

PARTIAL_DATE_PATTERN = r"^\d{4}(-\d{2}(-\d{2})?)?$"
"""A year, a year and month, or a full date, which is what a partial date cell holds."""

PORTAL_ID_EXAMPLES = {
    "sample": "s8T2as4Lg6UQKuW25tbFmfE",
    "measurement": "m4eKrbeo2iEEN3gx2WRu5Lh",
}


@dataclass
class Column:
    """One column of a type's file.

    Attributes:
        name: The heading an export writes and a template carries. It is the model
            field's name and is never translated.
        label: What the column is called on screen.
        kind: How its cells are read: a key of ``KIND_LABELS``.
        role: ``key`` (the portal ID), ``match`` (the Local ID), ``field`` or ``export``
            (written on export, ignored on import).
        required: Whether a new record needs a value.
        description: What goes in it.
        attribute: The model attribute it fills, or None.
        model_field: The model field behind it, or None.
        unit: The unit numbers are given in.
        allowed: For a list, ``(value, meaning)`` pairs. The value is what a cell holds.
        max_length: The most characters a text cell may hold.
        decimals: The most decimal places a number may have.
        minimum: The smallest number allowed.
        maximum: The largest number allowed.
        example: A value as a cell would hold it.
        aliases: Other headings the column is recognised by.
        group: Which part of the guide it belongs to: ``ids``, ``own`` or ``shared``.
    """

    name: str
    label: str
    kind: str
    role: str = "field"
    required: bool = False
    description: str = ""
    attribute: str | None = None
    model_field: models.Field | None = None
    unit: str = ""
    allowed: list[tuple[str, str]] = field(default_factory=list)
    max_length: int | None = None
    decimals: int | None = None
    minimum: float | None = None
    maximum: float | None = None
    example: str = ""
    aliases: list[str] = field(default_factory=list)
    group: str = "own"

    def widget(self, dataset=None, user=None):
        """Return the widget that reads and writes this column's cells.

        Args:
            dataset: The dataset a file is imported into, which a sample column looks in.
            user: The person importing, or None for a visitor.

        Returns:
            The widget for the column's kind.
        """
        from .widgets import widget_for

        return widget_for(self, dataset=dataset, user=user)

    def as_frictionless(self) -> dict:
        """Describe the column as a field of a Frictionless Table Schema.

        Returns:
            The field descriptor, with its title and description in the active
            language. The name is never translated.
        """
        entry = {
            "name": self.name,
            "title": str(self.label),
            "type": FRICTIONLESS_TYPES.get(self.kind, "string"),
            "description": str(self.description),
        }
        constraints = {}
        if self.role == "key":
            constraints["unique"] = True
        if self.required:
            constraints["required"] = True
        if self.max_length:
            constraints["maxLength"] = self.max_length
        if self.minimum is not None:
            constraints["minimum"] = self.minimum
        if self.maximum is not None:
            constraints["maximum"] = self.maximum
        if self.allowed:
            constraints["enum"] = [value for value, _meaning in self.allowed]
        if self.kind == "partial_date":
            constraints["pattern"] = PARTIAL_DATE_PATTERN
        if constraints:
            entry["constraints"] = constraints
        if self.kind in ("date", "datetime", "time"):
            entry["format"] = "default"
        if self.kind == "boolean":
            entry["trueValues"] = ["yes"]
            entry["falseValues"] = ["no"]
        if self.unit:
            entry["unit"] = self.unit
        if not self.importable:
            entry["readOnImport"] = False
        return entry

    @property
    def kind_label(self):
        """What this column's kind is called on screen.

        Returns:
            The label of the kind, or the kind itself when it has none.
        """
        return KIND_LABELS.get(self.kind, self.kind)

    @property
    def importable(self) -> bool:
        """Whether a file's cell in this column is read on import.

        Returns:
            False for a column written on export only.
        """
        return self.role != "export"

    @property
    def shown_aliases(self) -> list[str]:
        """The other headings worth listing: not the heading or the label again.

        Returns:
            The aliases, without repeats and without the heading or label, compared
            ignoring case.
        """
        seen = {self.name.casefold(), str(self.label).casefold()}
        shown = []
        for alias in self.aliases:
            key = str(alias).casefold()
            if key and key not in seen:
                seen.add(key)
                shown.append(alias)
        return shown

    @property
    def format_hint(self) -> str:
        """How a cell is written, in a few words.

        Returns:
            The hint, in the active language.
        """
        if self.kind == "text" and self.max_length:
            return _("Up to %(n)s characters") % {"n": self.max_length}
        hints = {
            "id": _("As shown on the record's page, such as s8T2as4Lg6UQKuW25tbFmfE"),
            "integer": _("Digits only, such as 42"),
            "number": _("A point for decimals, such as 12.5"),
            "boolean": _("yes or no (also true/false, 1/0)"),
            "date": _("YYYY-MM-DD, such as 2024-06-30"),
            "datetime": _("ISO 8601 in UTC, such as 2024-06-30T14:05:42Z"),
            "time": _("HH:MM:SS, such as 14:05:42"),
            "partial_date": _("YYYY, YYYY-MM or YYYY-MM-DD"),
            "concept": _("A label from the list, its code or its web address"),
            "choice": _("A value from the list"),
            "sample": _("The sample's portal ID, or its Local ID in this dataset"),
            "quantity": _(
                "A number in %(unit)s, or a number and a unit, such as 12 ppm"
            )
            % {"unit": self.unit or _("the stated unit")},
            "latitude": _("-90 to 90, north positive, WGS 84"),
            "longitude": _("-180 to 180, east positive, WGS 84"),
        }
        return str(hints.get(self.kind, _("Any text")))


@dataclass
class TableSchema:
    """Every column of one record type's file, in order.

    Attributes:
        model: The sample or measurement model.
        config: The configuration the schema was built from.
        columns: The columns, in the order a file has them.
    """

    model: type
    config: object
    columns: list[Column]

    @property
    def kind(self) -> str:
        """Whether the type is a ``sample`` or a ``measurement``.

        Returns:
            The word for the type's kind.
        """
        return "measurement" if issubclass(self.model, Measurement) else "sample"

    @property
    def slug(self) -> str:
        """The model's lower-case name.

        Returns:
            The name a Table Schema and a file are named by.
        """
        return self.model._meta.model_name

    @property
    def name(self) -> str:
        """The type's plural name, capitalised.

        Returns:
            The name in the active language.
        """
        return capfirst(str(self.model._meta.verbose_name_plural))

    @property
    def singular(self) -> str:
        """The type's name for one record.

        Returns:
            The name in the active language.
        """
        return str(self.model._meta.verbose_name)

    @property
    def importable(self) -> list[Column]:
        """The columns a file's cells are read from on import.

        Returns:
            The columns not written on export only.
        """
        return [column for column in self.columns if column.importable]

    @property
    def required(self) -> list[Column]:
        """The columns a new record needs a value in.

        Returns:
            The required columns.
        """
        return [column for column in self.columns if column.required]

    @property
    def headings(self) -> list[str]:
        """The headings of a file, in order.

        Returns:
            The name of every column.
        """
        return [column.name for column in self.columns]

    def get(self, name: str) -> Column | None:
        """Return the column with a heading.

        Args:
            name: The column's heading.

        Returns:
            The column, or None when the type has no such column.
        """
        return next((column for column in self.columns if column.name == name), None)

    def as_frictionless(self) -> dict:
        """Describe the file as a Frictionless Table Schema.

        The portal ID is unique and the schema names no primary key, because a file of
        new records leaves the portal ID empty.

        Returns:
            The descriptor: the type's name, title and fields, and the empty cell as
            the missing value.
        """
        return {
            "name": self.slug,
            "title": self.name,
            "fields": [column.as_frictionless() for column in self.columns],
            "missingValues": [""],
        }

    def groups(self) -> list[tuple[str, str, list[Column]]]:
        """Return the columns in the guide's sections.

        Returns:
            A ``(key, title, columns)`` triple for each section that has columns.
        """
        titles = {
            "ids": _("Identifying the record"),
            "own": _("About the %(type)s") % {"type": self.singular.lower()},
            "shared": _("Shared by every %(kind)s") % {"kind": self.kind},
        }
        return [
            (key, titles[key], [c for c in self.columns if c.group == key])
            for key in ("ids", "own", "shared")
            if any(c.group == key for c in self.columns)
        ]


def build_table_schema(config) -> TableSchema:
    """Work out the columns of a sample or measurement type.

    Nothing is read from the type's own table, so a stored record, and who may see it,
    never changes the result. Only the vocabularies a concept column lists are queried.

    Args:
        config: The type's ``ModelConfiguration``.

    Returns:
        The type's table schema.
    """
    model = config.model
    is_measurement = issubclass(model, Measurement)
    declared = set(flatten_fields(config.resource_fields))
    columns = identifier_columns(model, is_measurement)

    base = Measurement if is_measurement else Sample
    base_names = {f.name for f in base._meta.concrete_fields}
    excluded = set(config.exclude)
    inspector = FieldInspector(model)
    for model_field in model._meta.concrete_fields:
        name = model_field.name
        if name in base_names or inspector.should_exclude_field(name):
            continue
        if not kind_of(model_field):
            continue
        optional = not is_required(model_field)
        if optional and (name in excluded or (declared and name not in declared)):
            continue
        columns.append(field_column(model_field))

    if not is_measurement and (not declared or "status" in declared):
        columns.append(field_column(model._meta.get_field("status"), group="shared"))
    columns.extend(location_columns(is_measurement, declared))
    return TableSchema(model=model, config=config, columns=columns)


def identifier_columns(model, is_measurement: bool) -> list[Column]:
    """Return the columns every type starts with.

    Args:
        model: The sample or measurement model.
        is_measurement: Whether the model is a measurement.

    Returns:
        The portal ID, the Local ID and the name, and for a measurement its sample and
        that sample's name.
    """
    kind = "measurement" if is_measurement else "sample"
    columns = [
        Column(
            name="portal_id",
            label=_("Portal ID"),
            kind="id",
            role="key",
            description=_(
                "The identifier the portal gave the record. Leave it empty for a new "
                "record. A row with a portal ID updates that record, so keep it when "
                "you edit an export."
            ),
            aliases=["uuid", "id", "portal id", "record id"],
            example=PORTAL_ID_EXAMPLES[kind],
            group="ids",
        ),
        field_column(
            model._meta.get_field("local_id"),
            role="match",
            group="ids",
            description=_(
                "Your own identifier for the record within this dataset, such as a "
                "field number. A row with no portal ID updates the record with this "
                "Local ID, so give every row one if you import the same file more "
                "than once."
            ),
            aliases=["local id", "sample id", "field id", "lab id", "localid"],
        ),
        field_column(model._meta.get_field("name"), group="ids"),
    ]
    if is_measurement:
        columns.append(
            Column(
                name="sample",
                label=_("Sample"),
                kind="sample",
                required=True,
                description=_(
                    "The sample the measurement was made on: its portal ID, or its "
                    "Local ID if it is in this dataset."
                ),
                attribute="sample",
                model_field=model._meta.get_field("sample"),
                aliases=["sample id", "sample portal id", "sample_id"],
                example=PORTAL_ID_EXAMPLES["sample"],
                group="ids",
            )
        )
        columns.append(
            Column(
                name="sample_name",
                label=_("Sample name"),
                kind="text",
                role="export",
                description=_(
                    "The sample's name, to help a reader. It is not read on import."
                ),
                example=str(_("Core 14")),
                group="ids",
            )
        )
    return columns


def is_required(model_field) -> bool:
    """Say whether a new record cannot be saved without a value in a field.

    Args:
        model_field: The model field.

    Returns:
        False for a field that may be blank, a nullable field that is not a
        ``CharField``, a field with a default and a ``BooleanField``.
    """
    if model_field.blank or (
        model_field.null and not isinstance(model_field, models.CharField)
    ):
        return False
    if model_field.has_default():
        return False
    return not isinstance(model_field, models.BooleanField)


def kind_of(model_field) -> str:
    """Say what kind of cell a model field is read from and written to.

    Args:
        model_field: The model field.

    Returns:
        A key of ``KIND_LABELS``, or an empty string for a reference to a record of
        another model, which has no kind yet.
    """
    if isinstance(model_field, ConceptField):
        return "concept"
    if isinstance(model_field, QuantityFieldMixin):
        return "quantity"
    if isinstance(model_field, PartialDateField):
        return "partial_date"
    if model_field.is_relation:
        return ""
    if model_field.choices:
        return "choice"
    if isinstance(model_field, models.BooleanField):
        return "boolean"
    if isinstance(model_field, models.IntegerField):
        return "integer"
    if isinstance(model_field, (models.FloatField, models.DecimalField)):
        return "number"
    if isinstance(model_field, models.DateTimeField):
        return "datetime"
    if isinstance(model_field, models.DateField):
        return "date"
    if isinstance(model_field, models.TimeField):
        return "time"
    return "text"


def field_column(
    model_field, role="field", group="own", description=None, aliases=()
) -> Column:
    """Build the column a model field is read from and written to.

    Args:
        model_field: The model field.
        role: The column's role.
        group: The part of the guide the column belongs to.
        description: What goes in it, where it is not the field's help text.
        aliases: Other headings the column is recognised by.

    Returns:
        The column.
    """
    kind = kind_of(model_field)
    verbose = str(model_field.verbose_name)
    label = verbose if any(ch.isupper() for ch in verbose) else capfirst(verbose)
    unit = ""
    bare_label = label
    found = UNIT_IN_LABEL.search(label)
    if found:
        unit = found.group(1)
        bare_label = UNIT_IN_LABEL.sub("", label)
    column = Column(
        name=model_field.name,
        label=label,
        kind=kind,
        role=role,
        required=is_required(model_field) and role == "field",
        description=description
        if description is not None
        else str(model_field.help_text or ""),
        attribute=model_field.name,
        model_field=model_field,
        unit=unit,
        aliases=[bare_label, *aliases],
        group=group,
    )
    if kind == "text" and getattr(model_field, "max_length", None):
        column.max_length = model_field.max_length
    if isinstance(model_field, models.DecimalField):
        column.decimals = model_field.decimal_places
    if isinstance(
        model_field,
        (
            models.PositiveIntegerField,
            models.PositiveSmallIntegerField,
            models.PositiveBigIntegerField,
        ),
    ):
        column.minimum = 0
    if kind == "quantity":
        column.unit = str(model_field.base_units)
    if kind == "choice":
        column.allowed = [(str(v), str(m)) for v, m in model_field.flatchoices]
    if kind == "concept":
        column.allowed = concept_choices(model_field)
    column.example = example_for(column)
    return column


def concept_choices(model_field) -> list[tuple[str, str]]:
    """List the values a concept column accepts.

    Args:
        model_field: The concept field.

    Returns:
        A ``(preferred label, definition)`` pair for every concept the field allows. The
        value is the preferred label, which is the same in every language.
    """
    records = Record.objects.filter(model_field.resolve_restriction())
    return [
        (record.pref_label, concept_definition(record))
        for record in records.order_by("pref_label")
    ]


def concept_definition(record) -> str:
    """Return a concept's definition, or an empty string when it has none.

    Args:
        record: The vocabulary record.

    Returns:
        The definition as text.
    """
    data = record.data or {}
    for key in ("definition", "skos:definition"):
        value = data.get(key)
        if isinstance(value, dict):
            value = next(iter(value.values()), "")
        if isinstance(value, list):
            value = value[0] if value else ""
        if value:
            return str(value)
    return ""


def location_columns(is_measurement: bool, declared) -> list[Column]:
    """Build the location columns a type offers.

    Args:
        is_measurement: Whether the type is a measurement.
        declared: The names the configuration lists, empty when it lists none.

    Returns:
        All four columns when nothing is listed or ``location`` is. Otherwise the
        elevation or uncertainty that is named, with the latitude and longitude they
        need, or nothing.
    """
    named = declared & set(LOCATION_COLUMNS)
    if declared and "location" not in declared and not named:
        return []
    whose = _("measurement was made") if is_measurement else _("sample was taken")
    latitude, longitude, elevation, uncertainty = LOCATION_COLUMNS
    every = {
        latitude: Column(
            name=latitude,
            label=_("Latitude"),
            kind="latitude",
            description=_(
                "Where the %(whose)s, in decimal degrees north of the equator."
            )
            % {"whose": whose},
            attribute="location",
            minimum=-90,
            maximum=90,
            aliases=["lat", "y", "latitude dd", "decimal latitude"],
            example="48.9165",
            group="shared",
        ),
        longitude: Column(
            name=longitude,
            label=_("Longitude"),
            kind="longitude",
            description=_("Where the %(whose)s, in decimal degrees east of Greenwich.")
            % {"whose": whose},
            attribute="location",
            minimum=-180,
            maximum=180,
            aliases=["lon", "lng", "long", "x", "longitude dd", "decimal longitude"],
            example="7.8436",
            group="shared",
        ),
        elevation: Column(
            name=elevation,
            label=_("Elevation"),
            kind="number",
            unit="m",
            description=_(
                "Metres above mean sea level, negative below it. Needs a latitude and "
                "longitude."
            ),
            attribute=elevation,
            aliases=["elevation", "elevation m", "altitude", "height"],
            example="112.5",
            group="shared",
        ),
        uncertainty: Column(
            name=uncertainty,
            label=_("Location uncertainty"),
            kind="number",
            unit="m",
            minimum=0,
            description=_(
                "The distance in metres within which the true place lies. Needs a "
                "latitude and longitude."
            ),
            attribute=uncertainty,
            aliases=["uncertainty", "uncertainty m", "location accuracy", "accuracy"],
            example="25",
            group="shared",
        ),
    }
    wanted = (
        set(LOCATION_COLUMNS)
        if not declared or "location" in declared
        else {
            latitude,
            longitude,
            *named,
        }
    )
    return [every[name] for name in LOCATION_COLUMNS if name in wanted]


def example_for(column: Column) -> str:
    """Make an example cell from a column's kind and constraints.

    The example never comes from a stored record: a record may be private, and an
    example is shown to people who may not see it.

    Args:
        column: The column.

    Returns:
        A value as a cell would hold it, or an empty string for a kind with none.
    """
    if column.allowed:
        return column.allowed[0][0]
    if column.kind == "text":
        text = str(_("Core 14"))
        return text[: column.max_length] if column.max_length else text
    if column.kind in ("number", "quantity", "integer"):
        return number_example(column)
    fixed = {
        "boolean": "yes",
        "date": "2024-06-30",
        "datetime": "2024-06-30T14:05:42Z",
        "time": "14:05:42",
        "partial_date": "2024-06",
    }
    return fixed.get(column.kind, "")


def number_example(column: Column) -> str:
    """Make an example number that lies inside a column's range and decimal places.

    Args:
        column: A column of kind ``integer``, ``number`` or ``quantity``.

    Returns:
        The number as a cell would hold it.
    """
    value = Decimal(42 if column.kind == "integer" else "12.5")
    if column.minimum is not None:
        value = max(value, Decimal(str(column.minimum)))
    if column.maximum is not None:
        value = min(value, Decimal(str(column.maximum)))
    if column.decimals is not None:
        value = value.quantize(Decimal(1).scaleb(-column.decimals))
        max_digits = getattr(column.model_field, "max_digits", None)
        if max_digits and len(value.as_tuple().digits) > max_digits:
            value = Decimal(1).quantize(Decimal(1).scaleb(-column.decimals))
    return str(value)
