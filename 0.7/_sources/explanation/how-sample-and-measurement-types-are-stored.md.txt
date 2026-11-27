# How sample and measurement types are stored

This page explains how the database holds the sample and measurement types you define, and why FairDM stores them this way. It covers inheritance, what that means for queries and what it rules out. It does not show how to write a type, which is in [How to add a sample type](../developers/how-to/add-a-sample-type.md) and [How to add a measurement type](../developers/how-to/add-a-measurement-type.md).

## One base table and one table for each type

`Sample` and `Measurement` are base models, and each type you define is a subclass of one of them. FairDM uses [django-polymorphic](https://django-polymorphic.readthedocs.io/) for this, which builds on Django's multi-table inheritance.

With multi-table inheritance, the shared fields live in the base model's table and each subclass has a table of its own for the fields it adds. A one-to-one link joins the two. For a `RockSample`, the base table holds the name, the dataset, the location and the other fields every sample has. The `RockSample` table holds `rock_type`, `weight_grams` and the rest, and points back at the base row.

django-polymorphic adds a column to the base table that records which concrete type each row is. That column is what lets a query on the base model return the right subclass.

```{mermaid}
erDiagram
    Sample ||--o| RockSample : "is a"
    Sample ||--o| WaterSample : "is a"
    Measurement ||--o| XRFMeasurement : "is a"
    Measurement ||--o| ICPMSMeasurement : "is a"
```

## Querying by base or by type

You can ask for records at either level.

- `Sample.objects` returns every sample, and each result is an instance of its own type. A list of samples can hold a `RockSample` next to a `WaterSample`, and each shows its own fields.
- `RockSample.objects` returns only rock samples.

django-polymorphic reads the base rows first and then loads the type-specific columns with one further query for each type in the result. A list that mixes two types costs two more queries than one made of a single type.

Everything that is the same for all types attaches to the base model, so it works for any type without extra code:

- the dataset a sample or measurement belongs to
- descriptions, dates, identifiers and credits
- relations between samples
- the sample a measurement was made on

A measurement refers to a sample, not to a rock sample or a water sample, so it can name a sample of any type. Pages, the API and the collections that list records across types use the same property.

## Why it is stored this way

**Each type is a real schema.** A type's fields are columns with the types, constraints and validators you declare, so the database enforces them. The alternative was to keep type-specific values in a JSON column or a generic key-value structure. That is easy to create and hard to validate, filter or index, and it moves the schema out of code and into data. The constitution asks for domain structure as explicit Django models with declarative fields, not ad-hoc runtime structures. See [Configuration over code](configuration-over-code.md).

**Shared things are written once.** A single base table means a dataset's samples can be listed, counted, related and credited without knowing in advance which types exist. A portal that adds a type later does not have to change how any of that works.

**Types are ordinary Django models.** You write them as you would any model. They get migrations, the Django admin, validators and the ORM, and the registry can read their fields to build forms, tables, filters and API serializers. See [What registering a type produces](../developers/explanation/what-registering-a-type-produces.md).

## What it rules out

**The base model cannot be saved.** `Sample` and `Measurement` are never records in their own right, only the shared part of a type. Saving one raises a validation error. A form or the admin shows the error, and saving the model directly, loading a fixture or running a factory raises it too. A type must be a concrete subclass.

**The registry refuses the base models.** Registering `Sample` or `Measurement` itself, or an abstract model, is refused when the registration is read, so a mistake stops the portal at start-up.

**A type cannot reuse a reserved name.** Every sample and measurement already has `location`, `location_elevation` and `location_uncertainty`. A type that declares a field of the same name clashes with the inherited one. See [ADR 0032](../adr/0032-a-location-is-a-value-on-each-record.md).

**Reading a type's own fields costs a join.** The price of a table for each type is that a type's own fields live in a second table. A list of one type reads that table directly. A list that mixes types needs the extra query for each type described above.

## The same rule for the core levels

Projects and datasets are not polymorphic. They have one shape in every portal, which is part of what makes portals interoperable. See [The core data model](the-core-data-model.md).

## Related pages

- [Sample model](../developers/reference/sample-model.md) and [Measurement model](../developers/reference/measurement-model.md) list the base fields.
- [How to register a sample or measurement type](../developers/how-to/register-a-sample-or-measurement-type.md) covers registration.
