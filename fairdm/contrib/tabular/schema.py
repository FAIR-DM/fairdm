"""The columns of a record type's file, worked out from its registration.

Nothing here is written per type. A sample or measurement type that is registered gets its
columns, their guide, its templates and its import from the model and its configuration:

- the identifiers first: the portal ID (``portal_id``) and the Local ID,
- the name, and for a measurement the sample it was made on,
- the type's own fields, in the order the model declares them,
- the fields every sample or measurement has: status and the four location columns.

When the configuration lists ``resource_fields`` only those are offered, plus the identifiers
and whatever a new record cannot be saved without.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal

from django.db import models
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _

from fairdm.core.measurement.models import Measurement
from fairdm.core.sample.models import Sample
from fairdm.registry import registry

# Fields no person types into a spreadsheet.
SKIPPED = {
    "id",
    "polymorphic_ctype",
    "added",
    "modified",
    "image",
    "options",
    "dataset",
    "uuid",
    "keywords",
    "tags",
    "location",
    "location_elevation",
    "location_uncertainty",
}

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


def normalise(heading) -> str:
    """Reduce a heading to letters and digits, so 'Rock type', 'rock_type' and 'ROCK-TYPE' meet."""
    return re.sub(r"[^a-z0-9]", "", str(heading or "").lower())


@dataclass
class Column:
    """One column of a type's file.

    Attributes:
        name: The heading an export writes and a template carries.
        label: What the column is called on screen.
        kind: How its cells are read: a key of ``KIND_LABELS``.
        role: ``key`` (the portal ID), ``match`` (the Local ID), ``field`` or ``export``
            (written on export, ignored on import).
        required: Whether a new record needs a value.
        description: What goes in it.
        attribute: The model attribute it fills, or None.
        model_field: The model field behind it, or None.
        unit: The unit numbers are given in.
        allowed: For a list, ``(value, meaning)`` pairs, the value being what a cell holds.
        allowed_total: How many values the list has, when ``allowed`` is cut short.
        max_length: The most characters a text cell may hold.
        decimals: The most decimal places a number may have.
        minimum: The smallest number allowed.
        maximum: The largest number allowed.
        example: A value as a cell would hold it.
        aliases: Other headings the column is recognised by.
        group: Which part of the guide it belongs to.
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
    allowed_total: int = 0
    max_length: int | None = None
    decimals: int | None = None
    minimum: float | None = None
    maximum: float | None = None
    example: str = ""
    aliases: list[str] = field(default_factory=list)
    group: str = "own"

    @property
    def kind_label(self):
        return KIND_LABELS.get(self.kind, self.kind)

    @property
    def importable(self):
        return self.role != "export"

    @property
    def shown_aliases(self) -> list[str]:
        """The other headings worth listing: not the heading or the label again."""
        own = {normalise(self.name), normalise(self.label)}
        out, seen = [], set()
        for alias in self.aliases:
            key = normalise(alias)
            if key and key not in own and key not in seen:
                seen.add(key)
                out.append(alias)
        return out

    @property
    def keys(self) -> set[str]:
        """Every normalised heading that means this column."""
        return {normalise(x) for x in [self.name, self.label, *self.aliases] if x}

    @property
    def format_hint(self) -> str:
        """How a cell is written, in a few words."""
        hints = {
            "id": _("As shown on the record's page, such as s8T2as4Lg6UQKuW25tbFmfE"),
            "integer": _("Digits only, such as 42"),
            "number": _("A point for decimals, such as 12.5"),
            "boolean": _("yes or no (also true/false, 1/0)"),
            "date": _("YYYY-MM-DD, such as 2024-06-30"),
            "datetime": _("YYYY-MM-DD HH:MM, such as 2024-06-30 14:05"),
            "time": _("HH:MM, such as 14:05"),
            "partial_date": _("YYYY, YYYY-MM or YYYY-MM-DD"),
            "concept": _("A label from the list, its code or its web address"),
            "choice": _("A value from the list"),
            "sample": _("The sample's portal ID, or its Local ID in this dataset"),
            "quantity": _("A number in %(unit)s, or a number and a unit, such as 12 ppm")
            % {"unit": self.unit or "the stated unit"},
            "latitude": _("-90 to 90, north positive, WGS 84"),
            "longitude": _("-180 to 180, east positive, WGS 84"),
        }
        if self.kind == "text" and self.max_length:
            return _("Up to %(n)s characters") % {"n": self.max_length}
        return str(hints.get(self.kind, _("Any text")))

    def as_frictionless(self) -> dict:
        entry = {
            "name": self.name,
            "title": str(self.label),
            "type": FRICTIONLESS_TYPES.get(self.kind, "string"),
            "description": str(self.description),
        }
        constraints = {}
        if self.required:
            constraints["required"] = True
        if self.max_length:
            constraints["maxLength"] = self.max_length
        if self.minimum is not None:
            constraints["minimum"] = self.minimum
        if self.maximum is not None:
            constraints["maximum"] = self.maximum
        if self.allowed and not self.allowed_total:
            constraints["enum"] = [value for value, _meaning in self.allowed]
        if constraints:
            entry["constraints"] = constraints
        if self.unit:
            entry["unit"] = self.unit
        if self.kind in ("date",):
            entry["format"] = "%Y-%m-%d"
        if self.role == "export":
            entry["description"] = f"{entry['description']} Written on export, ignored on import."
        return entry


@dataclass
class TableSchema:
    """Every column of one record type's file, in order."""

    model: type
    config: object
    columns: list[Column]

    @property
    def kind(self) -> str:
        return "measurement" if issubclass(self.model, Measurement) else "sample"

    @property
    def slug(self) -> str:
        return self.model._meta.model_name

    @property
    def name(self) -> str:
        return capfirst(str(self.model._meta.verbose_name_plural))

    @property
    def singular(self) -> str:
        return str(self.model._meta.verbose_name)

    @property
    def importable(self) -> list[Column]:
        return [c for c in self.columns if c.importable]

    @property
    def required(self) -> list[Column]:
        return [c for c in self.columns if c.required]

    @property
    def headings(self) -> list[str]:
        return [c.name for c in self.columns]

    def get(self, name) -> Column | None:
        return next((c for c in self.columns if c.name == name), None)

    def match(self, heading) -> Column | None:
        """Return the column a file's heading means, or None."""
        key = normalise(heading)
        if not key:
            return None
        for column in self.importable:
            if key in column.keys:
                return column
        return None

    def groups(self):
        """The columns in the guide's sections."""
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

    def as_frictionless(self) -> dict:
        return {
            "name": self.slug,
            "title": self.name,
            "fields": [c.as_frictionless() for c in self.columns],
            "primaryKey": ["portal_id"],
            "missingValues": [""],
        }


def schema_for(model) -> TableSchema:
    """Build the columns of a registered sample or measurement type."""
    config = registry.get_for_model(model)
    is_measurement = issubclass(model, Measurement)
    base = Measurement if is_measurement else Sample
    declared = getattr(config, "resource_fields", None)
    if declared:
        declared = {str(f) for f in declared}

    columns: list[Column] = [
        Column(
            name="portal_id",
            label=_("Portal ID"),
            kind="id",
            role="key",
            description=_(
                "The identifier the portal gave the record. Leave it empty for a new record. "
                "A row with a portal ID updates that record, so keep it when you edit an export."
            ),
            aliases=["uuid", "id", "portal id", "record id"],
            example="s8T2as4Lg6UQKuW25tbFmfE" if not is_measurement else "m4eKrbeo2iEEN3gx2WRu5Lh",
            group="ids",
        )
    ]
    columns.append(
        field_column(
            model._meta.get_field("local_id"),
            role="match",
            group="ids",
            description=_(
                "Your own identifier for the record within this dataset, such as a field number. "
                "A row with no portal ID updates the record with this Local ID, so give every "
                "row one if you import the same file more than once."
            ),
            aliases=["local id", "sample id", "field id", "lab id", "localid"],
        )
    )
    columns.append(field_column(model._meta.get_field("name"), group="ids"))
    if is_measurement:
        sample_field = model._meta.get_field("sample")
        columns.append(
            Column(
                name="sample",
                label=_("Sample"),
                kind="sample",
                required=True,
                description=_(
                    "The sample the measurement was made on: its portal ID, or its Local ID "
                    "if it is in this dataset."
                ),
                attribute="sample",
                model_field=sample_field,
                aliases=["sample id", "sample portal id", "sample_id"],
                example="s8T2as4Lg6UQKuW25tbFmfE",
                group="ids",
            )
        )
        columns.append(
            Column(
                name="sample_name",
                label=_("Sample name"),
                kind="text",
                role="export",
                description=_("The sample's name, to help a reader. It is not read on import."),
                group="ids",
            )
        )

    base_names = {f.name for f in base._meta.concrete_fields}
    for model_field in model._meta.concrete_fields:
        if model_field.name in SKIPPED or model_field.name in base_names:
            continue
        if model_field.auto_created or isinstance(model_field, models.OneToOneField):
            continue
        if declared and model_field.name not in declared and not is_required(model_field):
            continue
        columns.append(field_column(model_field, group="own"))

    if not is_measurement and (not declared or "status" in declared):
        columns.append(field_column(model._meta.get_field("status"), group="shared"))
    if not declared or "location" in declared:
        columns.extend(location_columns(is_measurement))

    fill_examples(model, columns)
    return TableSchema(model=model, config=config, columns=columns)


def is_required(model_field) -> bool:
    if model_field.blank or model_field.null and not isinstance(model_field, models.CharField):
        return False
    if model_field.has_default():
        return False
    return not isinstance(model_field, models.BooleanField)


def kind_of(model_field) -> str:
    from controlled_vocabularies.fields import ConceptField

    try:
        from partial_dates.fields import PartialDateField
    except ImportError:  # pragma: no cover
        PartialDateField = ()
    try:
        from quantityfield.fields import QuantityFieldMixin
    except ImportError:  # pragma: no cover
        QuantityFieldMixin = ()

    if isinstance(model_field, ConceptField):
        return "concept"
    if QuantityFieldMixin and isinstance(model_field, QuantityFieldMixin):
        return "quantity"
    if PartialDateField and isinstance(model_field, PartialDateField):
        return "partial_date"
    if model_field.choices:
        return "choice"
    if isinstance(model_field, models.BooleanField):
        return "boolean"
    if isinstance(model_field, (models.IntegerField,)):
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


UNIT_IN_LABEL = re.compile(r"\s*\(([^)]+)\)\s*$")


def field_column(model_field, role="field", group="own", description=None, aliases=()):
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
        description=description if description is not None else str(model_field.help_text or ""),
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
    if isinstance(model_field, (models.PositiveIntegerField, models.PositiveSmallIntegerField, models.PositiveBigIntegerField)):
        column.minimum = 0
    if kind == "quantity":
        column.unit = str(model_field.base_units)
    if kind == "choice":
        column.allowed = [(str(v), str(m)) for v, m in model_field.flatchoices]
    if kind == "concept":
        concepts = concept_choices(model_field)
        column.allowed_total = len(concepts) if len(concepts) > 40 else 0
        column.allowed = concepts[:40]
    return column


def concept_choices(model_field) -> list[tuple[str, str]]:
    """The labels a concept column accepts, with the concept's definition where it has one."""
    from controlled_vocabularies.models import Record

    records = Record.objects.filter(model_field.resolve_restriction()).order_by("pref_label")
    out = []
    for record in records:
        definition = ""
        data = record.data or {}
        for key in ("definition", "skos:definition"):
            value = data.get(key)
            if isinstance(value, dict):
                value = next(iter(value.values()), "")
            if isinstance(value, list):
                value = value[0] if value else ""
            if value:
                definition = str(value)
                break
        out.append((str(record), definition))
    return out


def location_columns(is_measurement: bool) -> list[Column]:
    whose = _("measurement was made") if is_measurement else _("sample was taken")
    return [
        Column(
            name="latitude",
            label=_("Latitude"),
            kind="latitude",
            description=_("Where the %(whose)s, in decimal degrees north of the equator.")
            % {"whose": whose},
            attribute="location",
            minimum=-90,
            maximum=90,
            aliases=["lat", "y", "latitude dd", "decimal latitude"],
            example="48.9165",
            group="shared",
        ),
        Column(
            name="longitude",
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
        Column(
            name="location_elevation",
            label=_("Elevation"),
            kind="number",
            unit="m",
            description=_(
                "Metres above mean sea level, negative below it. Needs a latitude and longitude."
            ),
            attribute="location_elevation",
            aliases=["elevation", "elevation m", "altitude", "height"],
            example="112.5",
            group="shared",
        ),
        Column(
            name="location_uncertainty",
            label=_("Location uncertainty"),
            kind="number",
            unit="m",
            minimum=0,
            description=_(
                "The distance in metres within which the true place lies. Needs a latitude and "
                "longitude."
            ),
            attribute="location_uncertainty",
            aliases=["uncertainty", "uncertainty m", "location accuracy", "accuracy"],
            example="25",
            group="shared",
        ),
    ]


def fill_examples(model, columns):
    """Give each column an example, from a stored record of the type where one exists."""
    from .resources import render_cell

    instance = model.objects.order_by("pk").first()
    for column in columns:
        if column.example:
            continue
        value = ""
        if instance is not None and column.attribute and column.kind not in ("sample",):
            try:
                value = render_cell(column, instance)
            except Exception:  # noqa: BLE001
                value = ""
        if value in ("", None):
            value = default_example(column)
        column.example = str(value)[:60]


def default_example(column):
    examples = {
        "text": _("Core 14"),
        "integer": "42",
        "number": "12.5",
        "boolean": "yes",
        "date": "2024-06-30",
        "datetime": "2024-06-30 14:05",
        "time": "14:05",
        "partial_date": "2024-06",
        "quantity": "12.5",
    }
    if column.allowed:
        return column.allowed[0][0]
    if column.decimals is not None:
        return str(Decimal("12.5").quantize(Decimal(1).scaleb(-column.decimals)))
    return examples.get(column.kind, "")


def importable_types():
    """Every registered sample type, then every measurement type, as schemas."""
    return [schema_for(m) for m in registry.samples] + [
        schema_for(m) for m in registry.measurements
    ]


def type_for_slug(slug):
    for model in [*registry.samples, *registry.measurements]:
        if model._meta.model_name == slug:
            return model
    return None
