# Controlled vocabularies

This page explains what a controlled vocabulary is, where FairDM's vocabularies are published and how a portal uses them. It covers the ideas and the vocabularies FairDM uses. It does not show how to put a vocabulary field in a model, which is in [Model fields](../developers/reference/model-fields.md), or list the settings that use vocabularies, which are on the [settings reference](../developers/reference/settings.md).

## What a controlled vocabulary is

A controlled vocabulary is an agreed list of terms, each with a definition. A field that takes its values from the list can only hold those terms, so everyone who fills it in uses the same word for the same thing.

For research data this does three jobs.

- **Consistency.** Two people describing the same kind of sample use the same term, so the records can be compared.
- **Findability.** A search or filter on a term finds every record that uses it. With free text, "granite", "Granite" and "granit" are three different values.
- **Interoperability.** A term with a definition and an address can be matched against the same term in another portal or in a published vocabulary.

A vocabulary does not fit every field. Where the possible values are not known in advance, free text is the honest choice. FairDM keeps both, and the keywords section below shows how.

## Where the vocabularies live

FairDM's vocabularies are published, not written in its code. Each is a SKOS concept scheme in [FAIR-DM/fairdm-vocabularies](https://github.com/FAIR-DM/fairdm-vocabularies), and every term in it has a permanent address under `https://w3id.org/fairdm/vocabularies/`. A record stores the address of the term it carries, so:

- a stored term can be followed to its definition, its translations and its matches in other vocabularies
- the same term means the same thing in every portal that uses it
- a new term reaches a portal when the portal loads the vocabulary again, with no FairDM release

The fields that hold terms come from [django-controlled-vocabularies](https://github.com/FAIR-DM/django-controlled-vocabularies), which FairDM depends on. It imports a published vocabulary into its own tables and gives a model `ConceptField`, which holds one concept, and `MultiConceptField`, which holds several. Both store the concept's address, and a concept a record still holds cannot be deleted.

`python manage.py sync_vocabularies` loads every vocabulary a field names. A portal runs it when it is set up and on every deploy. A vocabulary declared in `CONTROLLED_VOCABULARIES` is read from the file the declaration names, which is how a portal ships its own copies so that a deploy never depends on another server.

## The vocabularies FairDM uses

| Vocabulary | Address | Provides |
|---|---|---|
| Identifier types | `https://w3id.org/fairdm/vocabularies/identifier-types` | DOI, IGSN, ORCID iD, ROR, grant number and the other kinds of identifier |
| Description types | `https://w3id.org/fairdm/vocabularies/description-types` | Abstract, methods, introduction and the other kinds of description |
| Date types | `https://w3id.org/fairdm/vocabularies/date-types` | Start, end, collection start, published and the other kinds of date |
| Contributor roles | `https://w3id.org/fairdm/vocabularies/contributor-roles` | Creator, data collector, project leader and the other roles on a credit |
| Sample status | `https://w3id.org/fairdm/vocabularies/sample-status` | The custody states of a specimen: available, in use, stored, destroyed and unknown |

A term's address is its vocabulary's address, a slash and the term's identifier: the abstract is `https://w3id.org/fairdm/vocabularies/description-types/abstract`. `fairdm.core.vocabularies` holds these addresses, and the addresses of the terms FairDM's own code names, as constants.

Each term also carries a `skos:notation`, the code it was stored under before it had an address, such as `Abstract`. FairDM writes it where another standard expects a code: the DataCite metadata names each description type, date type, contributor role and identifier scheme by it, because for each of those terms it is DataCite's own value.

### One vocabulary, a collection for each level

The identifier, description and date types and the contributor roles are each one vocabulary divided into ordered collections, one for each level of the data model, at the vocabulary's address followed by the level: `https://w3id.org/fairdm/vocabularies/date-types/sample`. A project is offered the description types that make sense for a project, and a sample is offered the ones that make sense for a sample, in the order the collection lists them.

The split keeps wrong choices out of reach. A sample can carry an IGSN but not an ORCID iD, and a measurement is not offered the role "project leader". Each model that holds typed rows names its collection, so the type field on a dataset description only offers the dataset's description types. The vocabulary stays one list with one definition for each term, whichever level uses it.

## How a portal uses vocabularies

Four places in a record draw on a vocabulary.

**Typed rows.** A description, a date and an identifier each have a `type`, a concept field limited to the collection for that level, and a record can hold one row of each type. See [The core data model](the-core-data-model.md).

**Roles on a credit.** The roles a contributor holds on a record come from the contributor roles vocabulary, and each record type offers its own collection of them. See [Why FairDM records contributors](why-fairdm-records-contributors.md).

**Concept fields.** A sample's `status` is a concept field on the sample status vocabulary. A sample type you define can use the same field with a vocabulary of its own, for example a published list of rock types.

**Keywords.** Every project, dataset, sample and measurement, and the portal itself, has `keywords`, a set of concepts from any vocabulary the portal has loaded.

## Keywords and free words

A record carries two kinds of keyword, and they are different fields.

- **Keywords** point at vocabulary concepts. They are controlled.
- **Tags** are free words a person types. Nothing limits them.

The keywords page of a record edits the free words. A record's vocabulary keywords are left alone when that page is saved, and the page does not offer a way to choose them. Vocabulary keywords reach a record through code or, for projects and datasets, through the administration interface.

A portal can filter its project list by the terms of chosen vocabularies. See [How to filter projects by vocabulary keywords](../developers/how-to/filter-projects-by-vocabulary-keywords.md).

## Why FairDM leans on vocabularies

The FAIR principles ask for metadata that uses shared vocabularies with resolvable identifiers. FairDM applies that in two places in particular. In the core, it limits what a record can say about itself to published terms with definitions, so that every portal describes a dataset's abstract or a creator's role the same way and by the same address. In your types, it makes it easy to name the vocabulary for a field when the values are a known list. See [FAIR data and research data infrastructure](fair-data-and-research-data-infrastructure.md).
