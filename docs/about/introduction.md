# Introduction

## Who is FairDM for?

FairDM is designed for researchers and part-time developers who are tasked with building and maintaining research data portals—often without formal training in software development. This is a common scenario in academia and research, where limited budgets make it difficult to hire dedicated technical staff. As a result, researchers are frequently left to navigate the complexities of web development themselves.

The framework is particularly suited for universities, research groups, and niche scientific communities that need a reliable, easy-to-maintain system but lack the resources for professional development. These projects often require a solution that is flexible enough to accommodate domain-specific data models, while also offering strong defaults that simplify deployment, maintenance, and collaboration.

Without a dedicated framework like FairDM, many research portals end up being built on ad hoc tech stacks that vary widely from one project to another. This fragmentation poses a major obstacle to interoperability between repositories—an essential requirement of the FAIR data principles. FairDM addresses this by offering a coherent, standardized foundation that lowers the barrier to entry and promotes sustainable, FAIR-aligned research infrastructure.


## What problems does FairDM solve?

Building a research data portal from scratch involves navigating a wide range of technical and organizational challenges—something that many researchers and part-time developers are not equipped or resourced to handle. FairDM directly addresses these issues by offering ready-made solutions that work out of the box while remaining flexible enough to support domain-specific needs.

On the technical side, FairDM provides:

- A robust core data model that includes metadata structures for projects, datasets, samples, and measurements—reflecting common patterns in research data organization.
- Easy extensibility for sample and measurement models, allowing projects to define domain-specific fields without compromising compatibility.
- Built-in user account management with support for authentication, email validation, two-factor authentication, and integration with ORCID and other third-party login providers.
- A standardized RESTful API available by default, ensuring consistent and interoperable access to data.
- Pre-configured Docker Compose setups to simplify deployment across a variety of hosting environments.

Beyond the technical layer, FairDM also addresses common non-technical challenges:

- It encourages adherence to established data standards such as [DataCite](https://datacite.org/) for datasets and [IGSN](https://www.igsn.org/) for sample identification, helping projects align with best practices in research data publishing.
- It provides extensive documentation for all user types, including a user guide, an admin guide, and a developer guide—lowering the barrier for onboarding and long-term maintenance.
- FairDM includes a flexible contributor system that allows for the precise attribution of individuals and organizations to objects in the data model. This supports clear documentation of roles and responsibilities across a research project.

By offering sensible defaults, modular extensibility, and a standards-aligned foundation, FairDM significantly reduces the burden of building sustainable, FAIR-compliant research infrastructure.

## How does FairDM support the FAIR principles?

FairDM is built from the ground up to support the **FAIR** data principles—**Findability, Accessibility, Interoperability**, and **Reusability**—not just in spirit, but through concrete design choices and built-in features.

### Findability

FairDM ensures that research data is easy to discover by:

- Enforcing metadata standards that enable consistent, searchable records.
- Including full indexing and filterable list views for core objects like projects and datasets.
- Introducing "data collections" for samples and measurements—customizable tabular views that span multiple datasets and projects—so users can find specific data types without navigating or downloading each dataset manually.
- Supporting persistent identifiers (e.g., DOIs, IGSNs) to make datasets and objects reliably referenceable.

### Accessibility

Data stored in a FairDM portal can be easily accessed through:

- A standardized RESTful API that provides machine-readable access to all core objects.
- Configurable access controls that support both public and private datasets.
- Required license declarations for all datasets, with a recommendation to use Creative Commons licenses—though portal administrators remain free to define their own licensing policies.

### Interoperability

FairDM promotes interoperability by:

- Encouraging the use of structured metadata and standardized formats for data exchange.
- Supporting controlled vocabularies to ensure semantic consistency across records.
- Offering import/export mechanisms that align with community-recognized data standards.

### Reusability

To maximize the reusability of research data, FairDM:

- Requires clear licensing and metadata descriptions for all datasets.
- Tracks provenance and contributor information using a detailed contributor framework that records individual and organizational roles.
- Includes thorough documentation for users, administrators, and developers, ensuring that data and the systems that manage it remain understandable and maintainable over time.

By tightly integrating FAIR-aligned practices into the architecture of the framework, FairDM empowers research communities to make their data truly open, usable, and valuable in the long term.


## What makes FairDM different?

Unlike many existing research data platforms—which are often either too generic or too inflexible—FairDM is purpose-built to address the real-world needs of research communities, especially those operating without dedicated development teams. In fact, the lack of dedicated frameworks in this space is what has led to a patchwork of custom-built portals using a wide range of tech stacks, often making data sharing and interoperability an afterthought.

FairDM takes a different approach. Built on **Django**, a mature web framework written in **Python**—a language already widely used in scientific computing—FairDM is accessible to researchers and developers with minimal web development experience. Its goal is to replace inconsistent and ad hoc solutions with a coherent, standardized platform that’s easy to use, easy to extend, and inherently FAIR-aligned.

Where other tools focus on data upload and storage, often without structure or validation, FairDM emphasizes **data integrity** and **community-defined standards**. It ensures that datasets follow clearly defined schemas and metadata models, helping research communities produce higher-quality, reusable data from the start.

### Core Design Principles

FairDM is shaped by a set of clear design philosophies:

- **Simplicity**  
FairDM strives to be straightforward and easy to use—for both data contributors and portal developers. The focus is on reducing friction, not adding complexity.
- **Consistency**  
Embracing the “convention over configuration” principle, FairDM provides strong defaults and a consistent structure that developers can rely on, freeing them to focus on designing data schemas rather than implementation details.
- **Batteries Included**  
FairDM comes with a robust set of built-in features that cover common research data portal needs, including user management, metadata editing, contributor tracking, REST APIs, and more. All essential services are pre-integrated and ready to use.
- **Isolation**  
Each FairDM portal is self-contained and self-hosted, giving research groups full control over their data and infrastructure—important for long-term sustainability and data sovereignty.
- **Integration**  
FairDM avoids reinventing the wheel. Where possible, it integrates with existing tools and standards from the research data management ecosystem (e.g., ORCID, IGSN, DataCite), but never in ways that compromise its core mission.
- **Interoperability**  
FairDM portals are interoperable by design. They share a common structure and export format, making it easy to exchange data between portals or with external systems.

This combination of focus, flexibility, and strong defaults makes FairDM a uniquely valuable option for research communities that want to build reliable, FAIR-compliant data infrastructure without the overhead of starting from scratch.