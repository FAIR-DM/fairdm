"""django-import-export resources built from a type's columns.

``build_resource`` turns a ``TableSchema`` into a ``ModelResource`` bound to one dataset. The
resource does the reading, the validation and the saving. What it adds to django-import-export:

- rows are matched to stored records by portal ID, then by Local ID within the dataset,
- the chosen mode skips rows the person did not ask for, with the reason kept,
- an empty cell keeps the stored value unless the person asked for it to clear it,
- every changed value is kept as old and new, which the review screen shows.
"""

from __future__ import annotations

import datetime as dt
import re
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from import_export import fields, resources, widgets

from fairdm.core.sample.models import Sample
from fairdm.utils.location.resources import LocatedResourceMixin, location_fields

from .schema import Column, TableSchema

TRUE = {"yes", "y", "true", "t", "1", "ja", "x", "✓"}
FALSE = {"no", "n", "false", "f", "0", "nein", ""}


class RowProblem(Exception):
    """A row that cannot be imported, with the column it belongs to."""

    def __init__(self, column, message):
        super().__init__(message)
        self.column = column
        self.message = message


def blank(value) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def clean_text(value):
    if blank(value):
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


class TextWidget(widgets.CharWidget):
    def __init__(self, column: Column):
        super().__init__(allow_blank=True, coerce_to_string=True)
        self.column = column

    def clean(self, value, row=None, **kwargs):
        value = clean_text(value)
        if self.column.max_length and len(value) > self.column.max_length:
            raise ValueError(
                _("Is %(n)s characters long. The most it may hold is %(max)s.")
                % {"n": len(value), "max": self.column.max_length}
            )
        if not value and self.column.model_field is not None and self.column.model_field.null:
            return None
        return value

    def render(self, value, obj=None, **kwargs):
        return "" if value is None else str(value)


class NumberWidget(widgets.Widget):
    def __init__(self, column: Column):
        super().__init__(coerce_to_string=False)
        self.column = column

    def clean(self, value, row=None, **kwargs):
        if blank(value):
            return None
        if isinstance(value, bool):
            raise ValueError(_("“%(v)s” is not a number.") % {"v": value})
        text = str(value).strip().replace(" ", "")
        if re.fullmatch(r"-?\d+,\d+", text):
            raise ValueError(
                _("“%(v)s” uses a comma for decimals. Write it with a point, such as %(fixed)s.")
                % {"v": value, "fixed": text.replace(",", ".")}
            )
        try:
            number = Decimal(text)
        except InvalidOperation:
            raise ValueError(_("“%(v)s” is not a number.") % {"v": value}) from None
        if not number.is_finite():
            raise ValueError(_("“%(v)s” is not a number.") % {"v": value})
        c = self.column
        if c.minimum is not None and number < Decimal(str(c.minimum)):
            raise ValueError(_("Must be at least %(min)s.") % {"min": c.minimum})
        if c.maximum is not None and number > Decimal(str(c.maximum)):
            raise ValueError(_("Must be at most %(max)s.") % {"max": c.maximum})
        if c.kind == "integer":
            if number != number.to_integral_value():
                raise ValueError(_("“%(v)s” is not a whole number.") % {"v": value})
            return int(number)
        if c.decimals is not None:
            exponent = number.as_tuple().exponent
            if isinstance(exponent, int) and -exponent > c.decimals:
                raise ValueError(
                    _("Has more than %(n)s decimal places.") % {"n": c.decimals}
                )
            return number
        return float(number)

    def render(self, value, obj=None, **kwargs):
        if value is None:
            return ""
        if isinstance(value, Decimal):
            return format(value.normalize(), "f") if value == value.to_integral() else format(value, "f")
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)


class BooleanCellWidget(widgets.Widget):
    def __init__(self, column: Column):
        super().__init__(coerce_to_string=False)
        self.column = column

    def clean(self, value, row=None, **kwargs):
        if isinstance(value, bool):
            return value
        text = clean_text(value).lower()
        if text in TRUE:
            return True
        if text in FALSE:
            return False
        raise ValueError(_("“%(v)s” is not yes or no.") % {"v": value})

    def render(self, value, obj=None, **kwargs):
        if value is None:
            return ""
        return "yes" if value else "no"


class DateCellWidget(widgets.Widget):
    FORMATS = {
        "date": ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"),
        "datetime": ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"),
        "time": ("%H:%M:%S", "%H:%M"),
    }

    def __init__(self, column: Column):
        super().__init__(coerce_to_string=False)
        self.column = column

    def clean(self, value, row=None, **kwargs):
        kind = self.column.kind
        if blank(value):
            return None
        if kind == "date" and isinstance(value, dt.datetime):
            return value.date()
        if kind == "date" and isinstance(value, dt.date):
            return value
        if kind == "datetime" and isinstance(value, dt.datetime):
            return value
        if kind == "time" and isinstance(value, (dt.time, dt.datetime)):
            return value if isinstance(value, dt.time) else value.time()
        text = str(value).strip()
        if kind == "datetime" and text.endswith("Z"):
            text = text[:-1]
        if kind == "datetime" and re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
            text += " 00:00"
        for fmt in self.FORMATS[kind]:
            try:
                parsed = dt.datetime.strptime(text, fmt)
            except ValueError:
                continue
            if kind == "date":
                return parsed.date()
            if kind == "time":
                return parsed.time()
            return parsed
        example = {"date": "2024-06-30", "datetime": "2024-06-30 14:05", "time": "14:05"}[kind]
        raise ValueError(
            _("“%(v)s” is not a date this column reads. Write it as %(example)s.")
            % {"v": value, "example": example}
        )

    def render(self, value, obj=None, **kwargs):
        if value is None:
            return ""
        if isinstance(value, dt.datetime):
            return value.strftime("%Y-%m-%d %H:%M")
        if isinstance(value, dt.date):
            return value.isoformat()
        if isinstance(value, dt.time):
            return value.strftime("%H:%M")
        return str(value)


class PartialDateWidget(widgets.Widget):
    def __init__(self, column: Column):
        super().__init__(coerce_to_string=False)
        self.column = column

    def clean(self, value, row=None, **kwargs):
        if blank(value):
            return None
        if isinstance(value, dt.date):
            return value.isoformat()[:10]
        text = clean_text(value)
        if not re.fullmatch(r"\d{4}(-\d{2}(-\d{2})?)?", text):
            raise ValueError(
                _("“%(v)s” is not YYYY, YYYY-MM or YYYY-MM-DD.") % {"v": value}
            )
        return text

    def render(self, value, obj=None, **kwargs):
        return "" if value is None else str(value)


class ChoiceWidget(widgets.Widget):
    def __init__(self, column: Column):
        super().__init__(coerce_to_string=False)
        self.column = column

    def clean(self, value, row=None, **kwargs):
        text = clean_text(value)
        if not text:
            return ""
        for stored, meaning in self.column.allowed:
            if text.lower() in (stored.lower(), meaning.lower()):
                return stored
        raise ValueError(
            _("“%(v)s” is not one of the allowed values: %(values)s.")
            % {"v": value, "values": ", ".join(v for v, _m in self.column.allowed[:8])}
        )

    def render(self, value, obj=None, **kwargs):
        return "" if value is None else str(value)


class ConceptWidget(widgets.Widget):
    """A concept by its label in any language, its slug or its URI."""

    def __init__(self, column: Column):
        super().__init__(coerce_to_string=False)
        self.column = column
        self._lookup = None

    def lookup(self):
        if self._lookup is None:
            from controlled_vocabularies.models import Record

            table = {}
            records = Record.objects.filter(self.column.model_field.resolve_restriction())
            for record in records:
                keys = {record.uri, record.slug, record.pref_label, str(record)}
                data = record.data or {}
                for key in ("prefLabel", "altLabel", "notation", "skos:prefLabel", "skos:altLabel", "skos:notation"):
                    value = data.get(key)
                    if isinstance(value, dict):
                        keys.update(str(v) for v in value.values())
                    elif isinstance(value, list):
                        keys.update(str(v) for v in value)
                    elif value:
                        keys.add(str(value))
                for key in keys:
                    if key:
                        table.setdefault(str(key).strip().lower(), record)
            self._lookup = table
        return self._lookup

    def clean(self, value, row=None, **kwargs):
        text = clean_text(value)
        if not text:
            return None
        record = self.lookup().get(text.lower())
        if record is None:
            shown = ", ".join(v for v, _m in self.column.allowed[:6])
            raise ValueError(
                _("“%(v)s” is not in the list. Allowed: %(values)s.") % {"v": value, "values": shown}
            )
        return record

    def render(self, value, obj=None, **kwargs):
        return "" if value is None else str(value)


class SampleWidget(widgets.Widget):
    """A sample by portal ID, or by Local ID or a unique name within the dataset."""

    def __init__(self, column: Column, dataset=None, user=None):
        super().__init__(coerce_to_string=False)
        self.column = column
        self.dataset = dataset
        self.user = user

    def clean(self, value, row=None, **kwargs):
        text = clean_text(value)
        if not text:
            return None
        found = Sample.objects.filter(uuid=text).first()
        if found is not None:
            if self.user is not None and not Sample.objects.filter(pk=found.pk).visible_to(self.user).exists():
                raise ValueError(_("You may not see the sample %(v)s.") % {"v": text})
            return found
        if self.dataset is not None:
            local = list(Sample.objects.filter(dataset=self.dataset, local_id=text)[:2])
            if len(local) == 1:
                return local[0]
            if len(local) > 1:
                raise ValueError(_("Two samples in this dataset have the Local ID “%(v)s”.") % {"v": text})
            named = list(Sample.objects.filter(dataset=self.dataset, name=text)[:2])
            if len(named) == 1:
                return named[0]
            if len(named) > 1:
                raise ValueError(
                    _("Several samples in this dataset are called “%(v)s”. Use the portal ID.")
                    % {"v": text}
                )
        raise ValueError(
            _("No sample has the portal ID or Local ID “%(v)s”.") % {"v": text}
        )

    def render(self, value, obj=None, **kwargs):
        return "" if value is None else str(value.uuid)


class QuantityWidget(NumberWidget):
    UNIT = re.compile(r"^\s*(-?[\d.eE+-]+)\s*([^\d\s].*)?$")

    def clean(self, value, row=None, **kwargs):
        if blank(value):
            return None
        field = self.column.model_field
        if isinstance(value, (int, float, Decimal)):
            magnitude, unit = value, None
        else:
            found = self.UNIT.match(str(value))
            if not found:
                raise ValueError(_("“%(v)s” is not a number with a unit.") % {"v": value})
            magnitude, unit = found.group(1), found.group(2)
        number = super().clean(magnitude, row)
        if unit:
            try:
                quantity = field.ureg.Quantity(Decimal(str(number)), unit.strip())
                return quantity.to(field.base_units)
            except Exception:  # noqa: BLE001
                raise ValueError(
                    _("“%(unit)s” is not a unit that converts to %(base)s.")
                    % {"unit": unit.strip(), "base": field.base_units}
                ) from None
        return field.ureg.Quantity(Decimal(str(number)), field.base_units)

    def render(self, value, obj=None, **kwargs):
        if value is None:
            return ""
        magnitude = getattr(value, "magnitude", value)
        return super().render(magnitude)


WIDGETS = {
    "text": TextWidget,
    "id": TextWidget,
    "integer": NumberWidget,
    "number": NumberWidget,
    "boolean": BooleanCellWidget,
    "date": DateCellWidget,
    "datetime": DateCellWidget,
    "time": DateCellWidget,
    "partial_date": PartialDateWidget,
    "choice": ChoiceWidget,
    "concept": ConceptWidget,
    "quantity": QuantityWidget,
}


def widget_for(column: Column, dataset=None, user=None):
    if column.kind == "sample":
        return SampleWidget(column, dataset=dataset, user=user)
    return WIDGETS.get(column.kind, TextWidget)(column)


def render_cell(column: Column, instance) -> str:
    """The cell an export writes for one column of one record."""
    if column.name == "portal_id":
        return instance.uuid or ""
    if column.name == "sample_name":
        sample = getattr(instance, "sample", None)
        return sample.name if sample else ""
    if column.kind in ("latitude", "longitude"):
        point = instance.location
        if point is None:
            return ""
        return NumberWidget(column).render(point.y if column.kind == "latitude" else point.x)
    value = getattr(instance, column.attribute)
    return widget_for(column).render(value)


class CellField(fields.Field):
    """A column whose cell is read by its column's widget, with the column kept for messages."""

    def __init__(self, column: Column, widget):
        super().__init__(attribute=column.attribute, column_name=column.name, widget=widget)
        self.column = column


class FairDMRecordResource(LocatedResourceMixin, resources.ModelResource):
    """The import of one type into one dataset. Built per run by ``build_resource``."""

    schema: TableSchema = None  # set by build_resource

    def __init__(self, dataset, mode="both", empty="keep", user=None):
        super().__init__()
        self.dataset = dataset
        self.mode = mode
        self.empty = empty
        self.user = user
        self.row_notes = {}
        self.on_row = None
        self._rows_seen = 0
        for field in self.fields.values():
            if isinstance(getattr(field, "widget", None), SampleWidget):
                field.widget.dataset = dataset
                field.widget.user = user

    # Rows ------------------------------------------------------------------------------

    def before_import_row(self, row, **kwargs):
        if self.empty == "keep":
            for key in list(row.keys()):
                if key not in ("portal_id", "local_id") and blank(row[key]):
                    del row[key]
        return super().before_import_row(row, **kwargs)

    def import_row(self, row, instance_loader, **kwargs):
        number = kwargs.get("row_number")
        self._current = number
        if self.belongs_elsewhere(row):
            # Left out rather than refused, so a file that mixes this dataset's records with
            # another dataset's still imports. Never offered as a copy: copies of another
            # dataset's records lose where the data came from. Only a measurement has a way to
            # use another dataset's records, by naming one of its samples.
            if issubclass(self._meta.model, Sample):
                note = _("Belongs to another dataset. An import adds and changes only this dataset's records.")
            else:
                note = _(
                    "Belongs to another dataset. An import adds and changes only this dataset's "
                    "records. A measurement made here can name a sample from another dataset in "
                    "the sample column."
                )
            self.row_notes[number] = note
            result = self.get_row_result_class()()
            result.import_type = result.IMPORT_TYPE_SKIP
        else:
            result = super().import_row(row, instance_loader, **kwargs)
        self._rows_seen += 1
        if self.on_row:
            self.on_row(self._rows_seen)
        return result

    def get_instance(self, instance_loader, row):
        model = self._meta.model
        portal_id = clean_text(row.get("portal_id"))
        local_id = clean_text(row.get("local_id"))
        if portal_id:
            base = model.type_of if hasattr(model, "type_of") else model
            found = base.objects.filter(uuid=portal_id).first()
            if found is None:
                raise RowProblem("portal_id", _("No record has the portal ID %(v)s.") % {"v": portal_id})
            typed = model.objects.filter(pk=found.pk).first()
            if typed is None:
                raise RowProblem(
                    "portal_id",
                    _("%(v)s is a %(other)s, not a %(this)s.")
                    % {
                        "v": portal_id,
                        "other": found.get_real_instance_class()._meta.verbose_name,
                        "this": model._meta.verbose_name,
                    },
                )
            return typed
        if local_id:
            matches = list(model.objects.filter(dataset=self.dataset, local_id=local_id)[:2])
            if len(matches) > 1:
                raise RowProblem(
                    "local_id",
                    _("Two records in this dataset have the Local ID %(v)s. Add a portal ID to say which.")
                    % {"v": local_id},
                )
            if matches:
                return matches[0]
        return None

    def belongs_elsewhere(self, row) -> bool:
        """Whether the row's portal ID names a record of another dataset."""
        portal_id = clean_text(row.get("portal_id"))
        if not portal_id:
            return False
        model = self._meta.model
        base = model.type_of if hasattr(model, "type_of") else model
        return base.objects.filter(uuid=portal_id).exclude(dataset=self.dataset).exists()

    def init_instance(self, row=None):
        return self._meta.model(dataset=self.dataset)

    def import_instance(self, instance, row, **kwargs):
        # LocatedResourceMixin.import_instance drops every field's error when the row has no
        # location columns, so the fields and the location are read here instead.
        errors = {}
        try:
            resources.ModelResource.import_instance(self, instance, row, **kwargs)
        except ValidationError as error:
            errors = error.update_error_dict(errors)
        if any(column in row for column in ("latitude", "longitude", "location_elevation", "location_uncertainty")):
            try:
                self.set_location(instance, row)
            except ValidationError as error:
                errors["location"] = [*errors.get("location", []), *error.error_list]
        if errors:
            raise ValidationError(errors)

    def validate_instance(self, instance, import_validation_errors=None, validate_unique=True):
        errors = dict(import_validation_errors or {})
        try:
            instance.full_clean(exclude=list(errors.keys()) + ["polymorphic_ctype", "uuid"], validate_unique=validate_unique)
        except ValidationError as e:
            errors = e.update_error_dict(errors)
        if errors:
            raise ValidationError(errors)

    def skip_row(self, instance, original, row, import_validation_errors=None):
        number = self._current
        is_new = original is None or original.pk is None
        if self.mode == "add" and not is_new:
            self.row_notes[number] = _("Matches %(name)s, and this import only adds new records.") % {"name": original}
            return True
        if self.mode == "update" and is_new:
            self.row_notes[number] = _("Matches no record in the dataset, and this import only updates.")
            return True
        if not is_new and not import_validation_errors:
            changes = changed_cells(self.schema, original, instance, row)
            self.row_notes[number] = changes
            if not changes:
                return True
        return False

    def save_instance(self, instance, is_create, row, **kwargs):
        # Polymorphic saves need the content type set on a new instance.
        super().save_instance(instance, is_create, row, **kwargs)


def changed_cells(schema, original, instance, row):
    """The cells that change a stored record, as (column, label, old, new)."""
    changes = []
    for column in schema.importable:
        if column.name in ("portal_id",) or column.name not in row:
            continue
        old = render_cell(column, original)
        new = render_cell(column, instance)
        if column.kind == "number" or column.kind in ("latitude", "longitude", "quantity", "integer"):
            try:
                if old != "" and new != "" and Decimal(old) == Decimal(new):
                    continue
            except InvalidOperation:
                pass
        if old != new:
            changes.append({"column": column.name, "label": str(column.label), "old": old, "new": new})
    return changes


def build_resource(schema: TableSchema, dataset, mode="both", empty="keep", user=None, columns=None):
    """A resource for ``schema``'s type, reading only ``columns`` when given."""
    attrs = {}
    names = []
    wanted = set(columns) if columns is not None else None
    for column in schema.importable:
        if column.role == "key":
            continue
        if wanted is not None and column.name not in wanted:
            continue
        if column.kind in ("latitude", "longitude"):
            continue
        if column.name in ("location_elevation", "location_uncertainty"):
            attrs[column.name] = location_fields()[column.name]
            names.append(column.name)
            continue
        attrs[column.name] = CellField(column, widget_for(column))
        names.append(column.name)
    for axis in ("latitude", "longitude"):
        if wanted is None or axis in wanted:
            attrs[axis] = location_fields()[axis]
            names.append(axis)
    meta = type(
        "Meta",
        (),
        {
            "model": schema.model,
            "fields": tuple(names),
            "skip_unchanged": False,
            "report_skipped": True,
            "clean_model_instances": False,
            "use_transactions": True,
        },
    )
    attrs["Meta"] = meta
    attrs["schema"] = schema
    return type(f"{schema.model.__name__}ImportResource", (FairDMRecordResource,), attrs)
