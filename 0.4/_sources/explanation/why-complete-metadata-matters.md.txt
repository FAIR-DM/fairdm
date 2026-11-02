# Why complete metadata matters

This page explains why a FairDM portal asks for descriptions, dates, identifiers, licences and credits as well as the data itself, and what the portal does with them. It covers the reasoning. It does not tell you how to write good metadata, which is in [How to write metadata others can reuse](../users/datasets/write-metadata-others-can-reuse.md), and it does not describe each screen where metadata is entered.

## Metadata is what makes a record usable

A number in a database is only a number. It becomes a measurement when someone can tell what was measured, on what, how, when, by whom and under what conditions. All of that is metadata. Without it, data held in a portal cannot be interpreted, trusted or cited, however carefully it was collected.

The person who needs the metadata is often not the person who wrote it. They may be a colleague a year later, a researcher in another country, or the same person after their memory of the fieldwork has faded. The metadata is the only thing that travels with the data to them.

## Who reads metadata

Four kinds of reader depend on it.

- **People deciding whether to reuse data.** They read the abstract, the methods and the dates to judge whether a dataset suits their question. A dataset with a one-line description is passed over.
- **Search.** A portal finds records through their names, descriptions, identifiers and keywords. A record without them is hard to find, however good its data.
- **Repositories and harvesters.** Services that index or publish datasets need a fixed set of properties. A dataset that lacks them cannot be submitted without someone filling the gaps by hand.
- **Programs.** A script that reads a portal's API relies on typed fields it can parse. A date written as free text, or a unit left out of a value, is something a program cannot recover.

These readers correspond to the FAIR principles. Findability needs identifiers and descriptive metadata. Reuse needs a licence, provenance and enough context to interpret the data. Interoperability needs typed fields and shared vocabularies. See [FAIR data and research data infrastructure](fair-data-and-research-data-infrastructure.md).

Metadata can be open when the data is not. The FAIR principles ask that metadata stay accessible even when the data is no longer available. A FairDM dataset keeps two controls, one for whether its own metadata may be read and one for whether the data beneath it is published. See [The core data model](the-core-data-model.md).

## Provenance

Provenance is the history of a record: where it came from, who handled it and how it was produced. FairDM keeps it in the structure of the record, not in free text alone.

- A **credit** records each person or organization that took part and the roles they held. See [Why FairDM records contributors](why-fairdm-records-contributors.md).
- A **sample relation** records that one sample was divided from another.
- A **measurement** always names the sample it was made on, even when the sample sits in another dataset.
- **Typed dates** record when a sample was collected or prepared, or when a measurement was set up.
- **Typed descriptions** hold the methods, the preparation and the conditions.

Provenance decides whether two results can be compared. If two campaigns used different instruments or different calibration, the difference has to be recorded for a later reader to account for it.

## What the portal does with metadata

The portal uses what is entered, so incomplete metadata shows up as visible gaps.

**Citation.** A dataset's overview page builds a citation in DataCite's form from its creators, year, title and identifier. When the dataset has no DOI, the page says so and cites the page itself.

**Readiness.** The people who manage a dataset see a checklist headed "Ready to publish?" until its data is public. It is drawn from what DataCite requires and recommends, and from what a formal publication would need to submit the record without help. The required items are an abstract, a description of the methods, at least one creator, a named contact, a licence, some samples or measurements and a collection period. Keywords, a related publication and public visibility are recommended. A project has a similar "Metadata readiness" checklist. Each item that is missing links to the page that fixes it where one exists.

**Export.** A project can be exported as DataCite JSON. The credits on a record follow the properties DataCite defines for a creator, so they map across without reshaping. See [Dataset publication, DOIs and DataCite metadata](dataset-publication-dois-and-datacite-metadata.md).

**Search and filters.** Listings search records by name and identifier. A record with a thin name and no identifier has little to match.

## Typed and controlled where it helps

The portal limits free text where a list of agreed terms serves better. A description is one of a fixed set of types, so every dataset's abstract can be found in the same place. A date has a type and can be partial, so a record can say "2021" when the day is not known. An identifier has a type, and its value is unique across the portal, so one DOI cannot name two records. Roles and sample status come from controlled vocabularies. See [Controlled vocabularies](controlled-vocabularies.md).

## What a portal cannot do

A portal can ask for metadata and show what is missing. It cannot tell whether what was entered is true. A readiness checklist counts whether an abstract exists, not whether it is a good one. The quality of the metadata depends on the people who enter it, which is why the guidance for them is a separate page.

Entering metadata also takes time, and the benefit goes mostly to later readers. The portal tries to reduce the cost by supplying defaults, such as a licence for a new dataset, and by putting the fix for a missing item one click from the checklist.
