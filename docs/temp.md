Despite these advancements, the current RDI landscape remains **incomplete and uneven**, particularly for domain-specific research communities. Many of the issues stem from a misalignment between the generic design of widely-used repositories and the nuanced needs of researchers working within specific fields. This misalignment manifests in several areas: -->

#### 🧾 Reusability

- **Inadequate domain-specific context**: General-purpose repositories like Zenodo or Figshare often lack support for field-specific metadata schemas. As a result, critical domain knowledge—such as experimental setups, data acquisition protocols, or terminologies—is poorly represented, limiting meaningful reuse.
- **Insufficient documentation**: Uploads frequently lack structured README files, data dictionaries, or provenance information. Without clear methodological context, datasets are harder to interpret, even within the originating discipline.
- **Unclear or inconsistent licensing**: Users often select ambiguous or overly restrictive licenses. Vague terms like “All Rights Reserved” or inconsistently applied Creative Commons licenses can introduce legal uncertainty around reuse.
- **Lack of curation or quality checks**: Most generalist platforms provide no peer review or automated validation of data quality. Consequently, the completeness, correctness, or usability of datasets cannot be guaranteed.

##### 📦 Metadata Quality

- **Limited metadata schemas**: Repositories often rely on generic schemas inspired by Dublin Core, which may not support domain-specific granularity, such as units of measurement, instrument parameters, or sampling strategies.
- **User-entered metadata prone to inconsistency**: Researchers may not have the time, knowledge, or incentives to produce structured, high-quality metadata. This results in sparse or inconsistent descriptions.
- **No use of controlled vocabularies or ontologies**: Free-text tagging and descriptions hinder semantic interoperability and reduce the discoverability of related datasets.

##### 🔓 Accessibility

- **Limited adherence to FAIR accessibility principles**: While data may be publicly downloadable, it is often poorly documented or locked in non-transparent formats that hinder meaningful access.
- **Use of obscure or proprietary file formats**: Datasets may require domain-specific or deprecated software to open, placing a technical barrier between users and the data.
- **Download-only access**: Many platforms do not offer APIs, subsetting capabilities, or data previews, requiring users to download entire files—often large and unstructured—without knowing their content.

##### 🔗 Interoperability

- **Lack of standardized formats and data models**: Datasets are often uploaded in arbitrary or project-specific formats, lacking adherence to interoperable standards like NetCDF, RDF, or CSV-W.
- **No semantic annotation or machine-actionable metadata**: Absence of ontologies or linked data representations makes it difficult to automate the discovery, parsing, or integration of datasets.
- **Poor integration with domain-specific tools and repositories**: Generic platforms do not typically align with discipline-specific ontologies, registries, or data pipelines, limiting their utility within research workflows.

These limitations underscore a broader issue: **one-size-fits-all data infrastructure cannot fully support the nuanced needs of domain-specific research communities**. While generalist repositories offer valuable services for rapid data sharing and citation, they often fall short in supporting deep reuse, semantic interoperability, and integration into domain-specific research ecosystems.





## Research Data Infrastructure

<!-- While the FAIR principles provide a robust framework for improving research data management, their practical implementation relies on the existence of suitable **Research Data Infrastructure (RDI)**. Over the past two decades, the RDI ecosystem has evolved considerably, transitioning from isolated institutional repositories to interconnected national and international data services. However, despite notable progress, significant barriers remain in achieving FAIR-aligned, domain-sensitive, and truly interoperable data infrastructures. -->

### The rise of generic data repositories

<!-- Early RDI developments were often fragmented and discipline-specific, led by grassroots initiatives such as **Dryad** in the life sciences, **ICPSR** in the social sciences, and **PANGAEA** in the Earth sciences. These repositories played a pioneering role in formalizing practices around data archiving and citation. In time, they were complemented by general-purpose platforms such as **Zenodo**, **Figshare**, and **Dataverse**, which made it easier for researchers across disciplines to share data in a lightweight, accessible manner. -->

While general-purpose repositories lowered the barrier to data sharing, their broad design often sacrificed the specificity and structure needed by domain experts. These platforms tend to lack support for discipline-specific metadata schemas, controlled vocabularies, and standardized data formats, which are critical for ensuring that data is **interpretable, comparable, and reusable** within a specific field. This lack of standardization leads to **semantic ambiguity**, where crucial contextual details such as measurement techniques, instrument settings, and classification schemes may not be captured or formalized. Consequently, researchers in the same domain may find it difficult to understand or reuse the data, particularly for tasks like automated workflows or meta-analyses.

Moreover, these repositories typically do not allow for the definition or validation of domain-specific data models. This inability to enforce shared expectations around data structure and interpretation means that **data sharing becomes a one-way act of deposit**, rather than a process fostering collaboration, iteration, and reuse.

The fragmented nature of current infrastructure, where each repository operates independently with its own idiosyncratic schema and technology stack, further hinders **interoperability**. Without a common foundation for describing, accessing, and exchanging data, integrating datasets or developing reusable tools becomes prohibitively complex. This fragmentation undermines not only data reuse but also the reproducibility, discoverability, and long-term preservation of data.

In short, while general-purpose repositories play an important role in making data public, they fall short of meeting the more sophisticated needs of domain-specific communities. For data to be truly FAIR—especially *Findable*, *Interoperable*, and *Reusable*—it must be shared within frameworks that support rich, standardized, and context-aware metadata, domain-enforced models, and a consistent technological foundation.

As such, large-scale, general-purpose data repositories focused primarily on file storage solutions—often with minimal regard for metadata standards, semantic structure, or content quality—should be increasingly viewed as a legacy solution.

### Moving forward

Initiatives like the **European Open Science Cloud (EOSC)**, **Germany’s National Research Data Infrastructure (NFDI)**, and **Australia’s ARDC** represent a more coordinated and strategic phase in RDI development. These projects aim to build interoperable infrastructures with common standards, persistent identifiers, and metadata frameworks that support cross-disciplinary data discovery and reuse. Additionally, technical tools and services such as the **FAIR Data Point**, **FAIRsharing**, and the **Data Stewardship Wizard** have further supported infrastructure providers and research communities in translating FAIR principles into operational practice. However, despite these ongoing initiatives, the current landscape of research data infrastructure remains incomplete and fragmented, particularly for domain-specific research communities.

## The FairDM Vision

The future of research data sharing lies in empowering individual communities to define, enforce, and deploy their own domain-specific data models. These models should reflect the unique structure and semantics of the specialised data collected within each discipline and be enforceable through modern, schema-driven database backends.

Thanks to lightweight deployment technologies such as Docker and affordable cloud or institutional server hosting, it is now entirely feasible for communities to develop and maintain their own research data portals. These portals can be overseen by domain experts, ensuring quality, contextual relevance, and long-term sustainability. Crucially, if these communities adopt a shared framework for declaring data models and building portals, interoperability, machine-actionability, and adherence to data standards can be systematically achieved across domains. This approach offers a scalable path forward—one that addresses the limitations of one-size-fits-all repositories and brings the FAIR principles into practical alignment with the real-world needs of diverse research communities.

Addressing these shortcomings requires an infrastructure paradigm that balances **generic standards** with **domain-specific flexibility**. This is the motivation behind the development of the **FairDM framework**—a web-based platform that empowers individual research communities to declare and manage their own **domain-specific data models**, while inheriting from standardized core models to ensure interoperability.

FairDM provides a structured yet customizable approach to FAIR data management. It allows domain experts to curate their own metadata templates, vocabularies, and validation rules, ensuring that the data and metadata collected are both meaningful within the discipline and reusable across domains. Furthermore, it supports the deployment of **community-driven research data portals**, managed by experts who understand the unique needs, workflows, and semantics of their field.

By combining **technical standardization** with **community-led customization**, FairDM represents a new generation of research data infrastructure—one that bridges the gap between FAIR theory and FAIR practice.