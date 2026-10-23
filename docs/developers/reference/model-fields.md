# Model fields

This page lists the model fields that FairDM and its vocabulary package add to Django's own, with the signature, default, behaviour and accepted values of each. It does not show how to use a field in a type, which is in [How to add a sample type](../how-to/add-a-sample-type.md), [How to add a measurement type](../how-to/add-a-measurement-type.md) and [How to use a controlled vocabulary in a model](../how-to/use-a-controlled-vocabulary-in-a-model.md). Location fields are on [Location fields](location-fields.md) and record fields on [Record fields](record-fields.md).

Import the quantity and partial-date fields from `fairdm.db.models`, which also exports every field and class that `django.db.models` does:

```python
from fairdm.core.sample.models import Sample
from fairdm.db import models


class CoreSample(Sample):
    depth = models.QuantityField("meter")
```

`ConceptField` is not part of FairDM. Import it from `research_vocabs.fields`.

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
| Import | `research_vocabs.fields.ConceptField` |
| Signature | `ConceptField(vocabulary=..., include_only=None, **kwargs)`. Pass `vocabulary` by keyword. |
| Default | `vocabulary` is required, and leaving it out raises `MissingConceptSchemeError`. `include_only` is `None`, which offers every term. `verbose_name` defaults to the vocabulary's label. |
| Stores | The term's name as text, in a `CharField`. `max_length` is the length of the longest term name. |
| Python value | A `research_vocabs.core.Concept` when read from the database. Its `str()` is the name, and it has `label()` and `definition()`. |
| Form field | A choice field. The choices are the vocabulary's terms, or the terms in `include_only`. |
| Accepts | The name of a term, or a `Concept`. A name that is not in the vocabulary raises `ValueError`. The name may use only letters, digits, `-`, `_` and `.`. |

`vocabulary` is a vocabulary class, never a string. `include_only` is a list of term names that narrows the choices.

The field adds a class attribute `<field name>_vocab` that holds the vocabulary instance, so a model with a `status` field has `status_vocab`. The migration for the field records the vocabulary class by its import path, and `max_length`, so a term whose name is longer than the longest existing one changes the migration. The vocabulary classes are described in [Controlled vocabularies](../../explanation/controlled-vocabularies.md).
