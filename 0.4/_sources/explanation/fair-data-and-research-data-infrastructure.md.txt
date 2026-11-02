# FAIR data and research data infrastructure

This page gives the background FairDM is built against. It explains what the FAIR principles ask of data, why general-purpose repositories and isolated domain portals fall short of them, and where FairDM sits between the two. It does not describe FairDM's features in full, which [What FairDM is for](what-fairdm-is-for.md) summarises, and it does not explain how a portal publishes a dataset, which is in [Dataset publication, DOIs and DataCite metadata](dataset-publication-dois-and-datacite-metadata.md).

## What the FAIR principles ask

The FAIR principles say that data should be Findable, Accessible, Interoperable and Reusable. Wilkinson and colleagues set them out in 2016, and their stated aim is to improve the infrastructure that supports reuse of scholarly data. They build on earlier work on open access to research data, including the Berlin Declaration on Open Access (2003), the OECD principles on access to research data from public funding (2007) and the Joint Declaration of Data Citation Principles (2014).

FAIR differs from earlier open data efforts in one respect. It asks that machines can act on data and metadata without a person in the loop, so that reuse scales beyond what people can do by hand.

- **Findable.** Data has a persistent identifier and rich, machine-readable metadata, and it is registered where it can be searched.
- **Accessible.** Data and metadata can be retrieved by their identifier over a standard protocol, with clear terms. The metadata stays available even when access to the data is restricted.
- **Interoperable.** Data and metadata use shared vocabularies and formats, and they refer to other data in a way machines can follow.
- **Reusable.** Data carries a clear licence, its provenance and the context needed to interpret it.

## Research data infrastructure

The principles say what good data looks like. Whether researchers can meet them depends on the research data infrastructure available to them, meaning the repositories, portals and services that hold data and make it findable.

### General-purpose repositories

Services such as Zenodo, Figshare and Dataverse let any researcher in any discipline deposit data with little effort. That breadth is also their limit. A generic schema cannot hold what a discipline needs to interpret its data, such as units, instrument settings, sampling strategy or classification scheme. In practice this leads to:

- **Thin metadata.** Fields are generic, free text is common and domain context is missing, so data is hard to interpret outside the group that produced it.
- **No shared vocabularies.** Without controlled terms, the same thing is described in many ways and related datasets are hard to find or combine.
- **Little structure.** Files arrive in project-specific formats with no enforced data model, so deposit is a one-way act and reuse depends on reading a README.
- **Download-only access.** Many services offer no way to query or subset data, so a reuser must fetch whole files without knowing what is in them.

General-purpose repositories do important work in making data public and citable. They do not give a research community a way to define, enforce and share its own data model.

### Domain-specific portals

Many disciplines have built their own repositories and portals to meet these gaps. These carry specialised metadata schemas, vocabularies and validation rules, and they serve their communities well.

The cost is fragmentation. Each portal is built on its own technology with its own data structure and its own way of exchanging data. A tool written for one cannot read another. Combining data across portals for a meta-analysis, or across disciplines, needs custom work every time. Many portals are also built by people whose main job is research, so they are hard to keep running.

### Coordinated initiatives

National and international programmes such as the European Open Science Cloud, Germany's National Research Data Infrastructure and the Australian Research Data Commons aim to join these services with common standards, persistent identifiers and metadata frameworks. Services such as FAIRsharing and the FAIR Data Point help providers apply the principles. These efforts leave the problem of the individual domain portal largely open. Someone still has to build each portal, and a portal built from scratch is unlikely to share structure with another.

## Where FairDM sits

FairDM takes the position that each research community should define, enforce and share its own data model, and that communities who do so on a shared framework gain interoperability at no extra cost.

A FairDM portal has two layers:

- **A core model that every portal shares.** Projects, datasets, samples, measurements and contributors have the same structure in every portal. See [The core data model](the-core-data-model.md).
- **Domain models that each community defines.** A sample or measurement type adds the fields, vocabularies and validation particular to the discipline. See [How sample and measurement types are stored](how-sample-and-measurement-types-are-stored.md).

The shared layer is what lets a tool, an API client or a harvester work across portals. The domain layer is what makes the data meaningful within a discipline. Containers and affordable hosting make it realistic for a community to run its own portal, and a framework that supplies the shared parts leaves the community to do the part only it can do.

## How a portal supports each principle

FairDM does not make data FAIR on its own. It gives a portal the machinery, and the people entering data supply the content. These are the places the machinery sits.

**Findable.** Every record has a short, stable identifier and its own page. Projects, datasets and each registered type have list pages with search and filters. Records carry typed external identifiers, such as DOIs, IGSNs, ORCID iDs and ROR identifiers, from controlled lists. Free and vocabulary keywords help searches.

**Accessible.** Records are reachable through a REST API as well as through pages, using the same permission rules. A record is private or public, and a dataset carries a separate flag for whether the data beneath it is published. See [How access to a record is decided](how-access-to-a-record-is-decided.md). Each dataset names its licence.

**Interoperable.** The core structure is shared. Description, date, identifier and role types come from controlled vocabularies, which makes terms mean the same across portals. See [Controlled vocabularies](controlled-vocabularies.md). Credits follow the shape DataCite asks of a creator, and a project can be exported as DataCite JSON from the administration interface.

**Reusable.** A dataset carries a licence, typed descriptions such as an abstract and methods, dates and a list of credited contributors with their roles. Samples record where they came from, and a measurement names the sample it was made on. See [Why complete metadata matters](why-complete-metadata-matters.md) and [Why FairDM records contributors](why-fairdm-records-contributors.md).

## Limits

A framework cannot supply what only the data's authors know. A portal can ask for an abstract and a licence and show what is missing, but it cannot judge whether the abstract is accurate. FairDM does not mint DOIs and does not check the scientific quality of the data. A portal that wants either adds it through an addon or an external service.

## References

- Berlin Declaration on Open Access to Knowledge in the Sciences and Humanities (2003). Max Planck Society. <https://openaccess.mpg.de/Berlin-Declaration>
- OECD (2007). Principles and Guidelines for Access to Research Data from Public Funding. <https://doi.org/10.1787/9789264034020-en>
- Data Citation Synthesis Group (2014). Joint Declaration of Data Citation Principles. FORCE11. <https://doi.org/10.25490/a97f-egyk>
- Wilkinson, M. D., et al. (2016). The FAIR Guiding Principles for scientific data management and stewardship. Scientific Data, 3, 160018. <https://doi.org/10.1038/sdata.2016.18>
