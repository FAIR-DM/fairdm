# What FairDM is for

This page explains the problem FairDM solves, who it is for and where its edges are. It covers the purpose of the framework as a whole. It does not list every feature, which the [reference pages](../developers/reference/core-models.md) and the guides for each reader do, and it does not explain the FAIR principles in depth, which is in [FAIR data and research data infrastructure](fair-data-and-research-data-infrastructure.md).

## The problem

A research community that wants to share data in a form others can find and reuse needs a research data portal. A portal needs a data model that fits the community's science, accounts and permissions, forms for entering data, pages for reading it, search, an API, and a way to run it on a server. Building all of that is a large web development project.

Groups with the money for professional developers get a bespoke portal, which then differs from every other portal in structure and technology. Groups without it usually build the portal in-house, often as a side task for a researcher who is not a web developer. The result is many portals that cannot be combined, searched together or read by the same tools. That fragmentation works against the interoperability the FAIR principles ask for.

FairDM is a Django framework for building these portals. It supplies everything that does not depend on the science, so a group only has to describe what is particular to its own data.

## Who it is for

FairDM is aimed at research groups, universities and scientific communities who need a dependable portal and have a small team, or one person with basic Python skills, to build and keep it running. It assumes you can write a Django model. It does not assume you can write views, templates or JavaScript.

Three kinds of reader use a FairDM portal, and the documentation is organised around them:

- **Portal developers** describe the community's data and deploy the portal.
- **Portal administrators** run it: people, roles and checking that the configuration is sound.
- **Portal users** add, edit and publish research data in it.

## What you describe and what FairDM supplies

You describe two things. The first is the samples and measurements particular to your science, written as Django models that extend FairDM's base models. The second is how each of them should appear, in a short registration class. See [Configuration over code](configuration-over-code.md) for why the framework works this way.

FairDM supplies the rest. A registered type gets a form, a table, a filter set, an API serializer, an import and export resource and an admin class, and the portal gives it list and overview pages and a place in the navigation. Around those it supplies:

- **A fixed core data model** of projects, datasets, samples and measurements, which every portal shares. See [The core data model](the-core-data-model.md).
- **Contributors and credits**, so each record says who took part and in which role. See [Why FairDM records contributors](why-fairdm-records-contributors.md).
- **Access control** that separates private from public records and gives each person a level on each record. See [How access to a record is decided](how-access-to-a-record-is-decided.md).
- **Controlled vocabularies** for description, date and identifier types, roles and sample status. See [Controlled vocabularies](controlled-vocabularies.md).
- **Locations** held on every sample and measurement and queried in the database. See [How locations are stored and protected](how-locations-are-stored-and-protected.md).
- **A REST API** for every core record and every registered type.
- **Sign-in** with email verification and with ORCID.
- **Container images** and a documented platform to run a portal on. See [The technology stack](the-technology-stack.md).

The interface is server-rendered. It is built on the django-mvp application shell with Tailwind CSS and daisyUI, and a portal gets it with no frontend work.

## What makes it different

Two choices set FairDM apart from a general-purpose repository.

**The schema belongs to the community.** A general-purpose repository accepts files with a title and a few fields of metadata. A FairDM portal stores the fields your science needs, as columns in a database, with validation. A measurement type for X-ray fluorescence has an element and a concentration, and the database enforces them.

**The backbone is shared.** Every portal uses the same project, dataset, sample and measurement structure, and the same shape for credits, identifiers and descriptions. A tool written against one portal's API reads another's. Your science is different from your neighbour's, but the structure around it is the same.

## What FairDM is not

FairDM keeps a narrow scope on purpose.

- **It is not a library of parts.** It is opinionated and owns the application shell. If you want to assemble your own stack from independent components, it is the wrong starting point.
- **It is not a generic content management system.** The core model is fixed, because that is what makes portals interoperable and citable.
- **It is not a single portal.** Domain-specific schemas belong in the portals built on FairDM, not in the framework.
- **It is not a formal publisher.** Publishing a dataset makes it visible to other users of the portal. Sending metadata to a data publisher and receiving a DOI is a separate act. See [Dataset publication, DOIs and DataCite metadata](dataset-publication-dois-and-datacite-metadata.md).
- **It is not the home of every feature.** The core stays small, and capabilities that only some portals need are addons.

## Where to go next

- [Build your first sample and measurement types](../developers/tutorial.md) takes you from an empty project to a working portal page.
- [FAIR data and research data infrastructure](fair-data-and-research-data-infrastructure.md) gives the background to the problem.
- The goals the framework steers by are in [GOALS.md](https://github.com/FAIR-DM/fairdm/blob/main/GOALS.md).
