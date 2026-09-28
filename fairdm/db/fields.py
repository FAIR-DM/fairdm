"""Model fields that store quantities and partial dates, with plain form fields."""

from decimal import Decimal

from django.db import models
from partial_date import PartialDateField as BasePartialDateField
from quantityfield import fields


class BigIntegerQuantityField(fields.BigIntegerQuantityField):
    """A quantity field storing big integer values, edited through a plain number input."""

    to_number_type = int

    def formfield(self, **kwargs):
        """Return the plain number form field rather than the quantity one."""
        return models.BigIntegerField.formfield(self, **kwargs)


class DecimalQuantityField(fields.DecimalQuantityField):
    """A quantity field storing decimal values, edited through a plain number input."""

    to_number_type = Decimal

    def formfield(self, **kwargs):
        """Return the plain number form field rather than the quantity one."""
        return models.DecimalField.formfield(self, **kwargs)


class IntegerQuantityField(fields.IntegerQuantityField):
    """A quantity field storing integer values, edited through a plain number input."""

    to_number_type = int

    def formfield(self, **kwargs):
        """Return the plain number form field rather than the quantity one."""
        return models.IntegerField.formfield(self, **kwargs)


class PositiveIntegerQuantityField(fields.PositiveIntegerQuantityField):
    """A quantity field storing positive integer values, edited through a plain number input."""

    to_number_type = int

    def formfield(self, **kwargs):
        """Return the plain number form field rather than the quantity one."""
        return models.PositiveIntegerField.formfield(self, **kwargs)


class QuantityField(fields.QuantityField):
    """A quantity field storing float values, edited through a plain number input."""

    to_number_type = float

    def formfield(self, **kwargs):
        """Return the plain number form field rather than the quantity one."""
        return models.FloatField.formfield(self, **kwargs)


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
