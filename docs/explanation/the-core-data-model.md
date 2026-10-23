# The core data model

This page explains how FairDM organises research data into projects, datasets, samples and measurements, and why the structure is fixed. It covers what each level is for and how the levels relate. It does not list every field, which the [core models reference](../developers/reference/core-models.md) does, and it does not explain how your own sample and measurement types are stored, which is in [How sample and measurement types are stored](how-sample-and-measurement-types-are-stored.md).

## Four levels

Every FairDM portal holds research data at four levels.

```{mermaid}
erDiagram
    Project |o--o{ Dataset : "may hold"
    Dataset ||--o{ Sample : holds
    Dataset ||--o{ Measurement : holds
    Sample ||--o{ Measurement : "is measured by"
```

- A **project** is the research initiative: a grant, a collaboration or a programme. It groups datasets and carries what is true of the whole effort, such as its status, funding and the organization that owns it.
- A **dataset** is the unit a portal cites and distributes. It carries the metadata a repository needs to publish it, including a licence, and it holds the samples and measurements.
- A **sample** is a physical or digital object that was collected, prepared or analysed, such as a rock, a water sample or a scan.
- A **measurement** is an observation or calculation made on a sample.

A dataset may belong to a project, but does not have to. Samples and measurements always belong to a dataset, and a measurement always names the sample it was made on.

The projects and datasets are the same in every portal. Samples and measurements are the two levels you extend, by defining types of your own. A water sample has different fields from a rock sample, and a pH reading different fields from an X-ray fluorescence analysis, so the base models carry what all of them share and each type adds the rest.

## What every record carries

All four levels share a base of fields and related rows, so a tool can treat any record the same way.

- **A name and an optional image.**
- **A short identifier** with a prefix that tells the level apart: `p` for projects, `d` for datasets, `s` for samples and `m` for measurements. It is generated when the record is created and cannot be edited, and the API and addresses refer to records by it.
- **Keywords and tags.** Keywords point at concepts in a controlled vocabulary. Tags are free words a person types. See [Controlled vocabularies](controlled-vocabularies.md).
- **Descriptions, dates and identifiers.** Each is a typed row, such as an abstract, a start date or a DOI. A record holds at most one row of each type, and the types come from vocabularies set for that level. An identifier value is unique across every record in the portal.
- **Credits.** A credit says that a person or organization took part, in which roles. See [Why FairDM records contributors](why-fairdm-records-contributors.md).

Dates are partial dates, so a record can say "2021" or "June 2021" when the day is not known.

## Project

A project has a status that moves from concept through planning to in progress and complete, with a further state for projects searching for collaborators. It has a visibility, which is private until its team makes it public, and it can name a funding body in the shape DataCite uses for funding references. The organization that owns the project is recorded separately from the people credited on it.

A project cannot be deleted while it has public datasets. They must be made private or deleted first. Its private datasets are deleted with it.

## Dataset

A dataset is private until its visibility is set otherwise. It carries a licence, which falls back to the portal's default when none is chosen, and its relations to published literature use the relation types DataCite defines, such as "Is Cited By" and "Is Supplement To". One piece of literature can be named as the dataset's own data publication.

A dataset has two separate controls:

- **Visibility** decides whether the dataset's own metadata may be read.
- **Published** decides whether the data beneath it, the samples and measurements, may be shown.

They are independent, so a dataset can be published while private. The reasoning is in [ADR 0014](../adr/0014-publication-is-a-separate-flag-from-visibility.md).

## Sample

A sample belongs to the dataset it first appeared in. It has an optional local identifier, the one its collectors use on a label or in a notebook, and a custody status from a small vocabulary: available, in use, stored, destroyed or unknown. The status describes where the specimen physically is, not what has been done with its data.

A sample can be related to other samples. A relation says that one sample is a child of another, so a borehole core can be divided into depth intervals and each interval stay a sample in its own right. A sample cannot relate to itself, and two samples cannot each be the child of the other.

A sample holds its own location, with an optional elevation and uncertainty. Its identifier rows accept an IGSN, the persistent identifier for physical specimens, which is a DataCite DOI. See [How locations are stored and protected](how-locations-are-stored-and-protected.md).

## Measurement

A measurement names the dataset it belongs to and the sample it was made on. These can be different datasets. A field team can describe samples in one dataset while a laboratory records its analyses of them in another, so each team manages its own records and the lineage still shows which sample each result came from.

A measurement type declares a value, and an uncertainty beside it where one is recorded. The base model reads these to report and format the measurement. See [How a measurement reports its value](../developers/explanation/how-a-measurement-reports-its-value.md).

A measurement can hold its own location. Where it holds none, a viewer who may open its sample sees the sample's location instead. A sample cannot be deleted on its own while a measurement refers to it. Deleting the dataset removes both.

## Why the core is fixed

You can extend samples and measurements, but you cannot change the shape of projects and datasets, or the way the four levels connect. Three reasons lie behind that.

- **Interoperability.** A tool, an API client or a harvester that understands one FairDM portal understands them all at the structural level. Letting each portal restructure the core would lose that.
- **Citation.** The dataset level lines up with DataCite so that its metadata can be passed to a publisher without rework. A portal that reshaped datasets would have to redo that mapping.
- **Stability.** Research portals outlive their funding. A core that changes slowly is easier to keep running.

The [constitution](https://github.com/FAIR-DM/fairdm/blob/main/CONSTITUTION.md) states the principle in Article XII: the core models provide the canonical backbone and remain stable, while domain-specific structure is expressed as models that extend the base classes. Community-specific detail goes into sample and measurement types, where you can add as much as your science needs.

## Related pages

- [How sample and measurement types are stored](how-sample-and-measurement-types-are-stored.md)
- [How access to a record is decided](how-access-to-a-record-is-decided.md)
- [Sample model](../developers/reference/sample-model.md) and [Measurement model](../developers/reference/measurement-model.md) list the fields.
- [Build your first sample and measurement types](../developers/tutorial.md) builds a portal on this model.
