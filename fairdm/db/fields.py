from decimal import Decimal

from django.db import models
from partial_date import PartialDateField as BasePartialDateField
from quantityfield import fields

from fairdm.forms import PartialDateField


class BigIntegerQuantityField(fields.BigIntegerQuantityField):
    to_number_type = int

    def formfield(self, **kwargs):
        return models.BigIntegerField.formfield(self, **kwargs)


class DecimalQuantityField(fields.DecimalQuantityField):
    to_number_type = Decimal

    def formfield(self, **kwargs):
        return models.DecimalField.formfield(self, **kwargs)


class IntegerQuantityField(fields.IntegerQuantityField):
    to_number_type = int

    def formfield(self, **kwargs):
        return models.IntegerField.formfield(self, **kwargs)


class PositiveIntegerQuantityField(fields.PositiveIntegerQuantityField):
    to_number_type = int

    def formfield(self, **kwargs):
        return models.PositiveIntegerField.formfield(self, **kwargs)


class QuantityField(fields.QuantityField):
    to_number_type = float

    def formfield(self, **kwargs):
        return models.FloatField.formfield(self, **kwargs)


class PartialDateField(BasePartialDateField):  # type: ignore[no-redef]
    def formfield(self, **kwargs):
        # Import here to avoid circular import
        from fairdm.forms import PartialDateField as PartialDateFormField

        # Build the default arguments for the form field
        defaults = {
            "required": not self.blank,
            "label": self.verbose_name.capitalize() if self.verbose_name else None,
            "help_text": self.help_text,
        }
        defaults.update(kwargs)

        # Return an instance of our custom form field
        return PartialDateFormField(**defaults)
