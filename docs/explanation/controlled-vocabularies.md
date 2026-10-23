# Controlled vocabularies

This page explains what a controlled vocabulary is, where FairDM's support for them comes from and how a portal uses them. It covers the ideas and the vocabularies FairDM ships. It does not show how to put a vocabulary field in a model, which is in [Model fields](../developers/reference/model-fields.md), or list the settings that use vocabularies, which are on the [settings reference](../developers/reference/settings.md).

## What a controlled vocabulary is

A controlled vocabulary is an agreed list of terms, each with a definition. A field that takes its values from the list can only hold those terms, so everyone who fills it in uses the same word for the same thing.

For research data this does three jobs.

- **Consistency.** Two people describing the same kind of sample use the same term, so the records can be compared.
- **Findability.** A search or filter on a term finds every record that uses it. With free text, "granite", "Granite" and "granit" are three different values.
- **Interoperability.** A term with a definition and an address can be matched against the same term in another portal or in a published vocabulary.

A vocabulary does not fit every field. Where the possible values are not known in advance, free text is the honest choice. FairDM keeps both, and the keywords section below shows how.

## Where the support comes from

The vocabulary machinery is in [django-research-vocabs](https://github.com/SamuelJennings/django-research-vocabs), a separate package that FairDM depends on. FairDM adds its own vocabularies and uses the package's fields.

This matters when you write a model. `ConceptField`, the field that stores a term from a vocabulary, is imported from `research_vocabs.fields`, not from `fairdm.db.models`.

django-research-vocabs describes a vocabulary as a set of concepts in the SKOS model, with a label, a definition and an address for each. It offers three ways to define one:

- **In Python.** A `VocabularyBuilder` subclass declares the concepts as class attributes. This is how FairDM writes its own.
- **From a file.** A `LocalVocabulary` subclass points at a file in your code, such as a Turtle file downloaded from a vocabulary service.
- **From a URL.** A `RemoteVocabulary` subclass points at a published file, and the package caches it after the first read.

All three give a field the same thing to read, so a portal can mix them.

## The vocabularies FairDM ships

FairDM defines five vocabularies in `fairdm.core.vocabularies`. They share the namespace `https://www.fairdm.org/vocabularies/`.

| Vocabulary | Provides |
|---|---|
| `FairDMIdentifiers` | Identifier types, such as DOI, IGSN, ORCID, ROR and grant number |
| `FairDMDescriptions` | Description types, such as abstract, methods and introduction |
| `FairDMDates` | Date types, such as start, end, collection start and published |
| `FairDMRoles` | Contribution roles, such as creator, data collector and project leader |
| `FairDMSampleStatus` | The custody states of a specimen: available, in use, stored, destroyed and unknown |

### One vocabulary, a collection for each level

The identifiers, descriptions, dates and roles are each one vocabulary that is divided into collections, one for each level of the data model. A project is offered the description types that make sense for a project, and a sample is offered the ones that make sense for a sample.

The split keeps wrong choices out of reach. A sample can carry an IGSN but not an ORCID iD, and a measurement is not offered the role "project leader". Each model that holds typed rows names its collection, so the type field on a dataset description only offers the dataset's description types. The vocabulary stays one list with one definition for each term, whichever level uses it.

## How a portal uses vocabularies

Four places in a record draw on a vocabulary.

**Typed rows.** A description, a date and an identifier each have a `type`. The type is limited to the collection for that level, and a record can hold one row of each type. See [The core data model](the-core-data-model.md).

**Roles on a credit.** The roles a contributor holds on a record come from `FairDMRoles`. The vocabulary is controlled so that two portals mean the same thing by the same role. A portal can add roles of its own. See [Why FairDM records contributors](why-fairdm-records-contributors.md).

**Concept fields.** A `ConceptField` on a model holds one term from a vocabulary. A sample's `status` is one, drawn from `FairDMSampleStatus`. The field stores the concept's name as text, offers the vocabulary's terms as its choices and accepts only names that are safe to use in an address. A sample type you define can use the same field with a vocabulary of its own, for example a list of rock types.

**Keywords.** Every project, dataset, sample and measurement has a `keywords` relation to concepts in the database, so a record can be tagged with terms from a vocabulary. The concepts are rows that FairDM's start-up steps copy in from the registered vocabularies with the `preload` command.

## Keywords and free words

A record carries two kinds of keyword, and they are different fields.

- **Keywords** point at vocabulary concepts. They are controlled.
- **Tags** are free words a person types. Nothing limits them.

The keywords page of a record edits the free words. A record's vocabulary keywords are left alone when that page is saved, and the page does not offer a way to choose them. Vocabulary keywords reach a record through code or, for projects and datasets, through the administration interface.

A portal can filter its project list by terms from chosen vocabularies. See [How to filter projects by vocabulary keywords](../developers/how-to/filter-projects-by-vocabulary-keywords.md).

## Why FairDM leans on vocabularies

The FAIR principles ask for metadata that uses shared vocabularies. FairDM applies that in two places in particular. In the core, it limits what a record can say about itself to terms with definitions, so that every portal describes a dataset's abstract or a creator's role the same way. In your types, it makes it easy to declare the vocabulary for a field when the values are a known list. See [FAIR data and research data infrastructure](fair-data-and-research-data-infrastructure.md).
