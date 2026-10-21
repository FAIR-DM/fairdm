"""Model fields that store quantities and partial dates."""

from decimal import Decimal

from partial_date import PartialDateField as BasePartialDateField
from quantityfield import fields

from fairdm.forms import fields as form_fields


class BigIntegerQuantityField(fields.BigIntegerQuantityField):
    """A quantity field storing big integer values."""

    form_field_class = form_fields.IntegerQuantityFormField
    to_number_type = int


class DecimalQuantityField(fields.DecimalQuantityField):
    """A quantity field storing decimal values."""

    form_field_class = form_fields.DecimalQuantityFormField
    to_number_type = Decimal


class IntegerQuantityField(fields.IntegerQuantityField):
    """A quantity field storing integer values."""

    form_field_class = form_fields.IntegerQuantityFormField
    to_number_type = int


class PositiveIntegerQuantityField(fields.PositiveIntegerQuantityField):
    """A quantity field storing positive integer values."""

    form_field_class = form_fields.IntegerQuantityFormField
    to_number_type = int


class QuantityField(fields.QuantityField):
    """A quantity field storing float values."""

    form_field_class = form_fields.QuantityFormField
    to_number_type = float


class PartialDateField(BasePartialDateField):
    """A date field that accepts a year, a year and month, or a full date."""

    def formfield(self, **kwargs):
        """Return FairDM's partial-date form field."""
        # Imported here to avoid a circular import.
        from fairdm.forms import PartialDateField as PartialDateFormField

        defaults = {
            "required": not self.blank,
            "label": self.verbose_name.capitalize() if self.verbose_name else None,
            "help_text": self.help_text,
        }
        defaults.update(kwargs)

        return PartialDateFormField(**defaults)
