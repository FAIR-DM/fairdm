# Why FairDM records contributors

This page explains why a FairDM portal keeps a record of who took part in each piece of research data, and what a credit on a record holds. It covers the reasoning behind people, organizations and credits. It does not explain how accounts and sign-in work, which is in [How contributor accounts and credits work](how-contributor-accounts-and-credits-work.md), or how a credit controls access, which is in [How access to a record is decided](how-access-to-a-record-is-decided.md).

## Why a portal records contributors at all

Recording who did the work serves three purposes.

- **Provenance.** Someone deciding whether to reuse a dataset needs to know who collected it, who processed it and who to contact. A name on the record answers all three.
- **Recognition.** Data management, curation and fieldwork are often invisible in a publication list. A credit makes that work visible and attributable to a person.
- **Accountability.** A team can see who did what and in which role, which supports internal audit and funder reporting.

These are the same reasons FAIR data asks for clear provenance. A record with no attribution is hard to cite and hard to trust, so FairDM treats attribution as part of the record rather than an optional extra.

## Two kinds of contributor

A contributor is either a person or an organization.

- A **person** is an individual. A person can also sign in, so the same record serves as both the credit on a dataset and the account of its author.
- An **organization** is a university, institute, company, agency, funder or similar body. Organizations can belong to other organizations, such as a department inside a university.

They share the same attribution fields: a name, other names the contributor is known by, a free-text profile, links, and identifiers. Each kind has a preferred identifier scheme. A person is shown with their ORCID iD, and an organization with its ROR ID. Both identifiers are persistent and are resolved outside the portal, so a credit can be matched with the same person or institution elsewhere.

The two kinds are separate types rather than one type with a flag. Only a person has an account, an email address and an affiliation to an organization, and only an organization has a type, a parent and a place on a map. Keeping them apart avoids a record full of fields that apply to only half of it.

## What a credit is

A person or organization is not attached to a record directly. They are attached through a **credit**, which says that this contributor took part in this project, dataset, sample or measurement. A credit holds:

- **The roles** the contributor held. The roles come from a vocabulary of contribution roles, such as creator, data collector, data curator, project leader or supervisor. The vocabulary is controlled so that two portals mean the same thing by the same word. A contributor does not need a role, and a credit with none is listed without one.
- **The organization the person was credited from.** This is where the person worked when they did the work, and it is kept with the credit.
- **A level of access**, for a person only. It is described in the page on access, and it is separate from the roles. A role says how someone took part. A level says what they may do on the record.

A contributor appears on a record once. Their roles on that record are gathered on their one credit rather than spread over several.

### The organization belongs to the credit

A person's profile records where they work now. A credit records where they worked then. If the credit copied the organization from the profile, a dataset collected at one institute would change its attribution to a second institute the day the author moved there, and a record would change without anyone editing it. So the organization on a credit is chosen when the person is credited and does not follow the profile. A person credited with no organization is shown with none, whatever their profile says.

Adding an organization to a credit also does not add anything to the person's own affiliations. Those are a separate record of who belongs to an organization.

### A credit follows the shape DataCite asks of a creator

DataCite is the metadata schema that many repositories and harvesters use to exchange descriptions of datasets. A credit carries the properties DataCite defines for a creator or contributor: a name, whether it is a personal or organizational name, given and family names for a person, name identifiers with their scheme, and the one affiliation recorded on the credit. A credit therefore maps onto DataCite field for field, and a caller can cite a dataset without first requesting every author and then every author's institution.

The credit does not decide which roles make someone a DataCite creator, and it carries no DataCite contributor type. The portal's roles are finer than DataCite's types, and a portal can add its own. Fixing one mapping into every credit would fix it for good, so the choice is left to whatever exports a record as DataCite metadata. See [Dataset publication, DOIs and DataCite metadata](dataset-publication-dois-and-datacite-metadata.md).

The credit never exposes the level of access it grants, and it carries nothing else from the contributor's profile. The reasoning is in [ADR 0030](../adr/0030-a-credit-carries-what-datacite-asks-of-a-creator.md).

## Consequences of how credits are stored

- A change to a person's name or identifier appears on every credit they hold, because a credit reads those from the contributor.
- A credit held by an account that public people lists leave out is still returned by the API, with no profile address, so a record's attribution stays complete.
- An affiliation on a credit is one organization or none. DataCite allows several, so an export writes it as a list of one.
- A record's contributors are kept in an order that people who manage the record set. Two lists are kept, one for people and one for organizations, and wherever a record names both together the people come first.

## Where to go next

- [How contributor accounts and credits work](how-contributor-accounts-and-credits-work.md) covers account states and how an organization is owned.
- [How a profile is claimed](how-a-profile-is-claimed.md) covers how a credited person takes over their profile.
- [Contributor models](../developers/reference/contributor-models.md) lists the fields.
- [Contributors](../users/contributors/contributors-tab.md) describes the tab where people are credited.
