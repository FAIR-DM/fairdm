# Why factories create metadata only when asked

This page explains two choices in FairDM's test factories: a portal reuses them instead of writing its own for the core records, and they create descriptions, dates and images only when a test asks for them. It does not list the factories or their arguments, which are in the [factories reference](../reference/factories.md), and it does not show how to write a test, which [How to test a portal with FairDM factories](../how-to/test-a-portal-with-fairdm-factories.md) does.

## Why a portal reuses FairDM's factories

A project, a dataset, a sample and a measurement each have required fields, parents that must exist first, and rules about what they may hold. A test that builds them by hand repeats all of that, and breaks whenever a FairDM release changes it.

A factory keeps that knowledge in one place. It fills in every required field with a valid value, creates the parents a record needs, and validates the types of descriptions and dates against the record's controlled vocabulary. When a model gains a required field, the factory is updated with it, and a portal's tests keep working without any edit.

A test then states only what it cares about. `ProjectFactory(visibility=Visibility.PUBLIC)` says that visibility matters here, and nothing else about the project does.

## Why metadata is opt-in

A factory creates the record and its parents and stops. It creates descriptions and dates only when you pass `descriptions` or `dates`. Three reasons decide it.

**A record holds one description and one date of each type.** If a factory created descriptions by default, a test that then adds its own `Abstract` would collide with the one the factory made, and the database would refuse it. The failure would appear in test code that did nothing wrong. When a test asks for the metadata, it knows what exists.

**Most tests need none.** A test of a permission rule or a list filter does not read a description. Creating two descriptions and a date for every project, dataset, sample and measurement adds rows to every test, and tests that build many records pay for them each time.

**A test that needs metadata should say how much and which kind.** `descriptions=2, descriptions__types=["Abstract", "Objectives"]` tells the next reader what the test depends on. A default of three random descriptions hides it.

The types are checked before anything is saved. A type that is not in the record's vocabulary raises `ValueError` with the list of valid ones, and asking for more descriptions than there are types raises it too. The mistake shows up at the line that made it, in plain words, and not as a database error somewhere below.

## Why images follow the same rule

A project, dataset, person or organization factory writes no image unless you pass `with_image=True` or an `image`. An image written for every record builds files under the media folder on every test run, and they stay there. The rule is the same as for metadata: the default is the smallest valid record, and anything else is requested.

## Why identifiers and credits are not created either

An identifier's value must be unique across every record that carries identifiers, not only across one kind of record. The identifier factories therefore generate their values from a sequence, and a test that wants one calls the factory for it and names the record it belongs to. A credit needs a person, a record and sometimes a level. Which of those a test wants is not something a factory can guess, so `ContributionFactory` takes them as arguments.

## Why the sample and measurement factories are abstract

`Sample` and `Measurement` are bases that cannot be created on their own. Only the types a portal registers can be. FairDM does not know the fields of those types, so it cannot ship a concrete factory for them. `SampleFactory` and `MeasurementFactory` carry what every sample and measurement shares, and a portal subclasses them for its own types, as [How to add a factory for a portal model](../how-to/add-a-factory-for-a-portal-model.md) shows.

The same reasoning explains why a `MeasurementFactory` has no default sample. A default would have to be a sample of some concrete type, and the factory has none to choose. A test passes one, or the portal's factory declares one.

For how the rest of the data model is arranged, see [The core data model](../../explanation/the-core-data-model.md) and [How sample and measurement types are stored](../../explanation/how-sample-and-measurement-types-are-stored.md).
