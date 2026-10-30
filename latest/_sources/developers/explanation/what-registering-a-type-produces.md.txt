# What registering a type produces

This page explains what the registry builds from the configuration of a sample or measurement type, where each part appears in the portal and what a type's listing shows. It does not show how to register a type, which is in [How to register a sample or measurement type](../how-to/register-a-sample-or-measurement-type.md), or list the options, which are on [Model configuration](../reference/model-configuration.md). The reasons for declaring a portal instead of coding it are in [Configuration over code](../../explanation/configuration-over-code.md).

## One configuration, six components

A configuration names a model and the fields that matter. From it the registry builds six components, each with the library that already does that job.

| Component | Built with | Used by |
|---|---|---|
| Form | Django forms and crispy-forms | The **Edit details** page of a record of the type |
| Table | django-tables2 | The type's listing |
| Filter set | django-filter | The type's listing and its API endpoints |
| Serializer | Django REST Framework | The type's API endpoints and the API documentation |
| Resource | django-import-export | The code that packages a dataset's records for export |
| Admin | Django's admin | The administration interface |

Nothing builds a component until something asks for it. Each is reached through an accessor such as `get_table_class()`, and the accessor builds or resolves the class again on every call. A portal that overrides one accessor therefore changes what the whole framework receives.

## What each component chooses

Each generator looks at the types of the fields it is given and makes a choice for each one.

- **The form** gives a date field a date input, a date and time field a date and time input, and a `TextField` or a long `CharField` a text area. A relation to a project, a dataset, a sample or a measurement becomes a search box over the records the person may use.
- **The table** shows a column for each field and a link on the name. It leaves out text fields, `CharField`s longer than 200 characters and geometry fields, so one long value cannot push the other columns off the page. Every table also has a dataset icon and the **Latitude** and **Longitude** of the record's location.
- **The filter set** gives dates a range of two dates, numbers a range, fields with choices a choice list, relations to records a list of published records and text a case-insensitive match. It also carries the search box when the type has search paths.
- **The serializer** carries the fields every sample or measurement has, then the type's own fields, then the descriptions, dates, identifiers, keywords and contributors of the record. A relation to a record appears as a reference to it, and any other relation as its text.
- **The resource** matches a relation on the related model's natural key when it has one, and on its primary key otherwise. A type that lists `location` gets the location columns.
- **The admin** extends the polymorphic child admin of its kind. The changelist shows up to five columns, and its search and its filters are built from the types of the fields. The add and change forms show every field of the model.

The form and the filter set also carry the framework's mixins for their kind of record, so a type that writes neither still gets the same widgets and dataset scoping as one that writes both. See [ADR 0006](../../adr/0006-generated-components-carry-the-framework-mixins.md).

## What the portal adds

Registration also changes the portal around the components. For each type the portal has:

- A listing page at `collections/samples/<model name>/` or `collections/measurements/<model name>/`, under the URL name `<model name>-list`. See [ADR 0017](../../adr/0017-listings-are-addressed-and-named-apart-from-records.md).
- An entry in the menu, named by the model's `verbose_name_plural`, under **Samples** or **Measurements**.
- A switcher on each listing that offers the listing of every other type.
- A card on the home page, with the type's description and the number of records that a visitor who is not signed in can see.
- API endpoints at `api/v1/samples/<plural name>/` or `api/v1/measurements/<plural name>/`, where the plural name is `verbose_name_plural` in lower case with hyphens. They appear in the API documentation with the description, authority, citation and keywords from the configuration's metadata.
- An administration page, and a place in the polymorphic list of all samples or all measurements.
- A line on the page of each dataset that holds records of the type, with the labels of the fields in the type's table list.

The page of each record is the same for every type. A type can give it a template of its own. See [How to give a sample or measurement type its own overview page](../how-to/give-a-sample-or-measurement-type-its-own-overview-page.md).

Renaming `verbose_name_plural` changes the type's API address, and so breaks anyone who reads it. See [How to change a type's API address](../how-to/change-a-types-api-address.md).

## What a listing shows

A listing shows the records of its type that sit in published datasets, and shows the same rows to every viewer. Signing in changes nothing. Publication is a flag on the dataset that an administrator sets in the administration interface. It is separate from the dataset's visibility, so a private dataset that is published contributes its records to the listings. Its rows carry the dataset's name and no link to a page that the reader could not open. See [ADR 0013](../../adr/0013-a-listing-shows-published-records-only-for-everyone.md).

A portal that has registered a type and published no dataset has empty listings.

## What registration does not produce

- **A screen for creating a record.** The portal has no screen that creates a sample or a measurement. Records arrive through the administration interface or the API.
- **An import or export page.** The resource is built, and the portal serves no page that uses it for a type.
- **A registrable base.** `Sample` and `Measurement` are never registered, only their types. See [How sample and measurement types are stored](../../explanation/how-sample-and-measurement-types-are-stored.md).

## Mistakes appear at start-up

The registry checks a configuration as it is built and refuses what could not work. It refuses a field name that does not exist, a component with both a field list and a class, a class on the wrong base, a model registered twice and a search path that a text match cannot read. The refusal stops the portal when it starts, so a visitor does not find the mistake. The list is under [Refused configurations](../reference/model-configuration.md#refused-configurations).
