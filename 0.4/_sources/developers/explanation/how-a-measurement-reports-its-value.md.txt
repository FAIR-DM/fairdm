# How a measurement reports its value

This page explains how a measurement turns its result into the text a portal shows, and why a measurement type names its result rather than formatting it. It covers the `value` and `uncertainty` convention and the formatter behind it. It does not show how to declare the fields, which is in [How to add a measurement type](../how-to/add-a-measurement-type.md), or list the methods, which are on [Measurement model](../reference/measurement-model.md).

## A type names its result

Measurement types differ in what they record, but the portal needs one way to show a measurement's result in a list, on its page and in text. FairDM settles this by convention. A measurement type that has a headline result declares a field called `value`, and it may declare a field called `uncertainty` beside it. The base `Measurement` model reads those two fields and does the rest.

The base model supplies two methods, and a type does not override either.

- `get_value()` returns the result.
- `print_value()` returns the result as text for a person.

`str(measurement)` uses the same result, so a measurement shows its value wherever the portal prints it as text.

## What `get_value()` returns

The answer depends on what the type declares.

1. **The type declares `value` and `uncertainty`, and both are set.** If `value` is a quantity, which is a number with units, `get_value()` returns the value with the uncertainty attached, so it reads as "48.25 ± 0.50 μm".
2. **The type declares `value`, and no uncertainty is set.** `get_value()` returns the value as it is.
3. **`value` is a plain number.** `get_value()` returns the number as it is, because only a quantity can carry an uncertainty. A type can still use a plain number, and it loses only the "±" in the text.
4. **The type declares no `value`.** `get_value()` returns the measurement's name. A microscopy image, for example, has no single result to report, so its name stands in for one.

A type that declares `value` but leaves it empty on a record gets `None`. `str()` then falls back to the record's name, or to its portal ID when it has no name.

`print_value()` turns whatever `get_value()` returned into text. A measurement's page shows that text as its result when the type declares a `value` that is set.

## Why the type does not format it

The alternative is to have every type override a method and return its own formatted string. That puts presentation in the model layer once for each type. Every portal then writes the same formatting by hand, gets it slightly differently, and the framework cannot show a measurement it did not define.

Naming a field is the smaller thing to ask of a portal developer, and the framework already knows how to show a quantity with an uncertainty. A type declares what its result is, and the framework decides how to write it. The decision is recorded in [ADR 0005](../../adr/0005-a-measurement-type-nominates-its-value.md).

## One format for the whole portal

A quantity is formatted with two decimals, the unit's symbol and spaces around the "±". FairDM installs that formatter on the shared unit registry when the application starts, and not when a template first loads it.

The difference matters. A formatter installed by importing a template tag module would exist only after some page had rendered. A value printed in a management command, an API response or a test would then use the unit library's default format. Installing it at start-up makes the format a property of the portal.

## Where the convention stops

The convention is single-valued. A type with more than one result per measurement, such as a spectrum with several peak heights, has no second special field to name. It records the extra results as ordinary fields and fills the result block of the measurement's page itself, as described on [Overview page blocks](../reference/overview-page-blocks.md). `value` stays the one headline figure.

A type also decides whether `value` is a quantity. A quantity field gives the formatted "value ± uncertainty unit" text, so declare both fields as quantity fields in the same units to get it. See [Model fields](../reference/model-fields.md#quantity-fields).
