# Model fields

This page lists the model fields that FairDM and its vocabulary package add to Django's own, with the signature, default, behaviour and accepted values of each. It does not show how to use a field in a type, which is in [How to add a sample type](../how-to/add-a-sample-type.md), [How to add a measurement type](../how-to/add-a-measurement-type.md) and [How to use a controlled vocabulary in a model](../how-to/use-a-controlled-vocabulary-in-a-model.md). Location fields are on [Location fields](location-fields.md) and record fields on [Record fields](record-fields.md).

Import the quantity and partial-date fields from `fairdm.db.models`, which also exports every field and class that `django.db.models` does:

```python
from fairdm.core.sample.models import Sample
from fairdm.db import models


class CoreSample(Sample):
    depth = models.QuantityField("meter")
```

`ConceptField` and `MultiConceptField` are not part of FairDM. Import them from `controlled_vocabularies.fields`.

## Quantity fields

A quantity field stores a number in the units you name as its base units and gives it back as a [pint](https://pint.readthedocs.io/) quantity. FairDM's classes extend the fields of [django-pint](https://github.com/CarliJoy/django-pint) and replace the form field, so that an edit form shows a stored value in the base units.

All five fields share these rules:

- `base_units` is required. It is the name of a unit that pint knows, such as `"meter"`, `"degC"` or `"microgram / liter"`. An unknown name raises `UndefinedUnitError` when the model is defined.
- `unit_choices` lists further units for the form. Each must measure the same dimension as `base_units`, or the model fails to load with a `DimensionalityError`. The base unit is always the first choice, whether or not you list it.
- A value is stored as a plain number in the base units. A quantity in another unit is converted when it is saved. A plain number is taken to be in the base units.
- A value read from the database is a quantity in the base units. A value you have only assigned to an unsaved instance stays as you assigned it until the record is read back.
- Validators run against the number, not the quantity. `MinValueValidator(0)` works.
- The form field is a number box with a unit list beside it. A value entered in any listed unit is converted to the base units.

### QuantityField

| | |
|---|---|
| Import | `fairdm.db.models.QuantityField`, defined in `fairdm.db.fields` |
| Signature | `QuantityField(base_units, *args, unit_choices=None, **kwargs)` |
| Default | `unit_choices` is `None`, which offers only the base units. |
| Stores | A float, as a `FloatField`. |
| Form field | `fairdm.forms.fields.QuantityFormField` |
| Accepts | A pint quantity, or a number. |

### DecimalQuantityField

| | |
|---|---|
| Import | `fairdm.db.models.DecimalQuantityField` |
| Signature | `DecimalQuantityField(base_units, *args, unit_choices=None, verbose_name=None, name=None, max_digits=None, decimal_places=None, **kwargs)` |
| Default | `unit_choices` is `None`. `max_digits` and `decimal_places` have no default. |
| Stores | A decimal, as a `DecimalField`. |
| Form field | `fairdm.forms.fields.DecimalQuantityFormField` |
| Accepts | A pint quantity, or a number. `max_digits` and `decimal_places` must be integers, with `max_digits` at least 1 and `decimal_places` between 0 and `max_digits`. Otherwise the field raises `ValueError`. |

### IntegerQuantityField

| | |
|---|---|
| Import | `fairdm.db.models.IntegerQuantityField` |
| Signature | `IntegerQuantityField(base_units, *args, unit_choices=None, **kwargs)` |
| Default | `unit_choices` is `None`. |
| Stores | An integer, as an `IntegerField`. |
| Form field | `fairdm.forms.fields.IntegerQuantityFormField` |
| Accepts | A pint quantity, or a whole number. |

### BigIntegerQuantityField

| | |
|---|---|
| Import | `fairdm.db.models.BigIntegerQuantityField` |
| Signature | `BigIntegerQuantityField(base_units, *args, unit_choices=None, **kwargs)` |
| Default | `unit_choices` is `None`. |
| Stores | An integer, as a `BigIntegerField`. |
| Form field | `fairdm.forms.fields.IntegerQuantityFormField` |
| Accepts | A pint quantity, or a whole number. |

### PositiveIntegerQuantityField

| | |
|---|---|
| Import | `fairdm.db.models.PositiveIntegerQuantityField` |
| Signature | `PositiveIntegerQuantityField(base_units, *args, unit_choices=None, **kwargs)` |
| Default | `unit_choices` is `None`. |
| Stores | A non-negative integer, as a `PositiveIntegerField`. |
| Form field | `fairdm.forms.fields.IntegerQuantityFormField` |
| Accepts | A pint quantity, or a whole number of zero or more. |

## PartialDateField

| | |
|---|---|
| Import | `fairdm.db.models.PartialDateField`, defined in `fairdm.db.fields` |
| Signature | `PartialDateField(*args, **kwargs)` |
| Default | None. Django's field options apply. |
| Stores | A date and its precision, in one date-time column. The precision is held in the seconds. |
| Python value | A `partial_date.PartialDate` with `date` and `precision`. |
| Form field | `fairdm.forms.fields.PartialDateField`, a text box with the mask `yyyy-mm-dd`. Hyphens at either end of the entry are removed. |
| Accepts | `None`, a `PartialDate`, or a string in one of the forms `YYYY`, `YYYY-MM` and `YYYY-MM-DD`. Any other value, a `datetime.date` included, raises a `ValidationError`. |

A year-only value is stored as the first of January and a year-and-month value as the first of the month. The precision records what was entered. You can filter with the same strings, such as `dates__value__gte="2020"`.

## ConceptField

| | |
|---|---|
| Import | `controlled_vocabularies.fields.ConceptField` |
| Signature | `ConceptField(vocabulary=None, collection=None, branch=None, **kwargs)`. Pass the arguments by keyword. |
| Default | `vocabulary` is `None`, which admits a concept of any loaded vocabulary. `collection` and `branch` are `None`, which offer every concept of the vocabulary. |
| Stores | The concept's address, in a foreign key to `controlled_vocabularies.Record` by its `uri`, with `on_delete=PROTECT`. The column is `<field name>_id`. |
| Python value | The `Record` the address names. `record.uri` is its address, `record.display_label()` its name in the reading language, and `record.first_value("skos:notation")` its notation. |
| Form field | A search box over the concepts the field admits. FairDM's own forms draw the description, date and identifier types and the sample status as a drop-down instead, through `fairdm.core.forms.ConceptSelectField`. |
| Accepts | A `Record`, or an address assigned to `<field name>_id`. `full_clean()` refuses a concept the field does not admit. |

`vocabulary` is the address of a concept scheme, several addresses, or a `Vocabulary(uri)` from the same module. A slug raises `TypeError` when the field is declared. `collection` is the address of one of the vocabulary's collections and limits the field to its members, and `branch` is the address of a concept and limits the field to it and every concept below it. Each needs exactly one vocabulary.

The field adds `get_<field name>_label()` and `get_<field name>_uri()` to the model. Its migration records the addresses only. `python manage.py sync_vocabularies` loads the vocabulary. The vocabularies FairDM uses are described in [Controlled vocabularies](../../explanation/controlled-vocabularies.md).

## MultiConceptField

| | |
|---|---|
| Import | `controlled_vocabularies.fields.MultiConceptField` |
| Signature | `MultiConceptField(vocabulary=None, collection=None, branch=None, **kwargs)`, as `ConceptField`. |
| Stores | A set of concepts, in a table that links each row to each concept's address. A concept a row holds cannot be deleted. |
| Python value | A related manager of `Record` rows. |
| Accepts | `Record` rows, through `add()` and `set()`. A concept the field does not admit is refused with a `ValidationError` before anything is written. |

The field adds `get_<field name>_labels()` and `get_<field name>_uris()` to the model. The `keywords` of every record and `Contribution.roles` are this field.

