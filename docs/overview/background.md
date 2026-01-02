# Background

## FAIR Data

The FAIR Data principles—**Findable, Accessible, Interoperable, and Reusable**—have become a cornerstone of modern data stewardship, particularly in the context of open science and research data management. Rooted in longstanding efforts to improve data sharing and reuse, the FAIR principles provide a framework for ensuring that data are not only available but also usable by both humans and machines. This movement has evolved significantly over the past two decades, shaped by policy developments, community-driven initiatives, and advances in data infrastructure.

### FAIR Data Movement

**2003 – OECD Declaration on Access to Research Data from Public Funding**  
The Organisation for Economic Co-operation and Development (OECD) emphasized the importance of open access to publicly funded research data, laying early groundwork for what would become the FAIR principles (OECD, 2007).

**2007 – Berlin Declaration on Open Access**  
Building on earlier declarations, this milestone further reinforced the importance of open access to scientific knowledge, including underlying research data (Max Planck Society, 2003).

**2011 – Force11 Community and the Birth of Data Citation Principles**  
The FORCE11 (Future of Research Communications and e-Scholarship) community was established, promoting better scholarly communication and leading to the development of the **Joint Declaration of Data Citation Principles** in 2014, which supported proper attribution and reuse of datasets (Data Citation Synthesis Group, 2014).

**2014 – Launch of the Research Data Alliance (RDA)**  
The RDA facilitated global discussions around data sharing, infrastructure, and standardization. Its working groups contributed significantly to the development of community norms and technologies that align with FAIR practices (RDA, 2024).

**2016 – Formalization of the FAIR Principles**  
The FAIR principles were first articulated in a seminal paper by Wilkinson et al. (2016), proposing that digital assets should be Findable, Accessible, Interoperable, and Reusable. Unlike prior open data efforts, FAIR emphasized machine-actionability as a core requirement, addressing the scalability of data reuse.

:::{epigraph}
The goal of FAIR is to improve the infrastructure supporting the reuse of scholarly data.

-- Wilkinson et al., 2016
:::

**2017 – European Commission Endorses FAIR**  
The European Open Science Cloud (EOSC) and the Horizon 2020 program adopted FAIR as a guiding framework, embedding the principles into funding requirements and infrastructure planning (European Commission, 2018).

**2018 – GO FAIR Initiative Established**  
The GO FAIR initiative was launched to support the practical implementation of FAIR principles through implementation networks (GO FAIR, 2018).

**2019 – National and International Policy Alignment**  
Key funders, including the NIH in the United States and various national research councils in Europe, began integrating FAIR compliance into their data management policies (NIH, 2023).

**2020 – UNESCO and OECD Push for Global Data Governance**  
The OECD’s “Recommendation on Access to Research Data from Public Funding” was updated, and UNESCO’s Open Science Recommendation (2021) reinforced the global relevance of FAIR-aligned data practices (UNESCO, 2021).

**2022–2024 – Expanding the FAIR Ecosystem**  
FAIR principles have increasingly influenced domain-specific data standards (e.g., in genomics, environmental sciences, and social sciences). Tools and services, such as FAIRsharing, the Data Stewardship Wizard, and the FAIR Evaluator, have helped operationalize FAIR compliance (Sansone et al., 2019; Groth et al., 2020).

### FAIR Data Today

Today, FAIR has transitioned from principle to practice across a wide range of scientific disciplines. The FAIRification process, however, remains complex—requiring coordination among researchers, institutions, funders, and infrastructure providers. While many repositories and data policies reference FAIR, the level of actual implementation varies. Challenges include disciplinary differences in metadata standards, limited incentives for researchers, and the need for sustainable infrastructure.

Nevertheless, the growing consensus around the importance of data stewardship and responsible data sharing — particularly in response to global crises like the COVID-19 pandemic — has underscored the urgency of FAIR-aligned practices.

## Research Data Infrastructure

While the FAIR principles provide a robust framework for improving research data management, their practical implementation depends on the existence of suitable **Research Data Infrastructure (RDI)**. Over the past two decades, the RDI ecosystem has evolved considerably—from isolated institutional repositories to interconnected national and international data services. However, despite notable progress, substantial barriers remain to achieving FAIR-aligned, domain-sensitive, and truly interoperable data infrastructures.

### Generic Data Infrastructure

Early RDI developments were often fragmented and discipline-specific, led by grassroots initiatives such as **Dryad** in the life sciences, **ICPSR** in the social sciences, and **PANGAEA** in the Earth sciences. These repositories played a pioneering role in formalizing practices around data archiving and citation. In time, they were complemented by general-purpose platforms such as **Zenodo**, **Figshare**, and **Dataverse**, which made it easier for researchers across disciplines to share data in a lightweight, accessible way.

While general-purpose repositories lowered the barrier to data sharing, their broad design often sacrificed the specificity and structure needed by domain experts. These platforms tend to lack support for discipline-specific metadata schemas, controlled vocabularies, and standardized data formats, which are critical for ensuring that data is **interpretable, comparable, and reusable** within a discipline. This lack of standardization leads to **semantic ambiguity**, where crucial contextual details such as measurement techniques, instrument settings, and classification schemes may not be captured or formalized. Consequently, researchers within a given discipline may find it difficult to understand or reuse the data, particularly for tasks like automated workflows or meta-analyses. This inability to enforce shared expectations around data structure and interpretation means that **data sharing becomes a one-way act of deposit**, rather than a process fostering collaboration, iteration, and reuse.

In short, general-purpose repositories play an important role in making data public, but they fall short of meeting the more specific needs of individual research communities. For data to be truly FAIR—especially *Findable*, *Interoperable*, and *Reusable*—it must be shared within frameworks that support rich, standardized, and **context-aware metadata**, community-defined data models, and a consistent technological foundation. As such, large-scale, general-purpose repositories may be insufficient for many domain-specific reuse and interoperability goals.

<!-- The fragmented nature of current infrastructure, where each repository operates independently with its own idiosyncratic schema and technology stack, further hinders **interoperability**. Without a common foundation for describing, accessing, and exchanging data, integrating datasets or developing reusable tools becomes prohibitively complex. This fragmentation undermines not only data reuse but also the reproducibility, discoverability, and long-term preservation of data. -->

### Focused Data Infrastructure

The problems associated with GDI have led to concerted efforts by individual research domains to establish **domain-specific repositories** and data portals. Such repositories are designed to address the unique needs of distinct scientific communities, providing tailored solutions for data sharing, management, and reuse. They often include features such as specialized metadata schemas, controlled vocabularies, and validation rules that reflect the specific practices and requirements of the discipline.

Many repositories of this nature currently exist, spanning a wide array of research disciplines and each designed to cater toward the needs of a particular research community. These repositories are vital for individual communities because they support the creation and sharing of data models and metadata schemas tailored to the specific needs of their fields. However, their proliferation across scientific disciplines has created a fragmented landscape of largely isolated portals.

Each domain-specific repository operates largely in isolation, with minimal shared infrastructure, technology stacks, or data formats. This lack of standardization across platforms creates a fragmented ecosystem that hinders the interoperability of datasets. The diverse technologies and data structures used by each portal often make it difficult to integrate data *across* disciplines, undermining the potential for cross-disciplinary research. In many cases, data may be stored in proprietary formats or with custom metadata schemas that cannot be easily understood or accessed by users from outside the discipline.

Moreover, the absence of common standards for data transmission further complicates the process of data sharing and reuse. While some repositories provide basic file download mechanisms, others may lack APIs or standardized interfaces for data retrieval. As a result, users are often forced to manually download datasets or navigate complex interfaces to access the data they need. This makes it difficult for automated workflows, software tools, or third-party platforms to interact with the data in a meaningful way.

The lack of interoperability between domain-specific repositories also impacts the broader goals of data integration and discovery. For example, aggregating data from multiple sources for large-scale meta-analyses or building cross-disciplinary tools requires a level of consistency and compatibility that is often absent in the current ecosystem. Furthermore, as the volume of research data grows, the need for effective data aggregation and integration becomes increasingly critical. Without common frameworks or standardized data exchange protocols, the vision of a truly interconnected, interoperable research data ecosystem remains elusive.

### Moving forward

In response to the shortcomings of both general-purpose and domain-specific repositories, there has been a growing recognition of the need for a more coordinated approach to research data infrastructure. Large-scale initiatives like the **European Open Science Cloud (EOSC)**, **Germany’s National Research Data Infrastructure (NFDI)**, and **Australia’s ARDC** represent a more coordinated and strategic phase in RDI development. These projects aim to build interoperable infrastructures with common standards, persistent identifiers, and metadata frameworks that support cross-disciplinary data discovery and reuse. 

Technical tools and services—such as the **FAIR Data Point**, **FAIRsharing**, and the **Data Stewardship Wizard**—have further supported infrastructure providers and research communities in translating FAIR principles into operational practice. However, despite these ongoing initiatives, the current landscape of research data infrastructure remains incomplete and fragmented, ***especially for domain-specific research communities***.

## The role of FairDM

FairDM presents itself as a tool for research communities to define, manage, and share domain-specific data models. It aims to address the limitations of both general-purpose repositories and isolated domain-specific portals by providing a framework that balances generic standards with domain-specific flexibility.

The future of research data sharing lies in empowering individual communities to define, manage, enforce, and share their own domain-specific data models. These models reflect the unique structure and semantics of the specialised data collected within each discipline and be enforceable through modern, schema-driven database backends.

Thanks to lightweight deployment technologies such as Docker and affordable cloud or institutional server hosting, it is now entirely feasible for communities to develop and maintain their own research data portals. These portals can be overseen by domain experts, ensuring quality, contextual relevance, and long-term sustainability. Crucially, if these communities adopt a shared framework for declaring data models and building portals, then interoperability, machine-actionability, and adherence to data standards can be systematically achieved across domains. This approach offers a scalable path forward—one that addresses the limitations of one-size-fits-all repositories and brings the FAIR principles into practical alignment with the real-world needs of diverse research communities.

Addressing these shortcomings requires an infrastructure paradigm that balances **generic standards** with **domain-specific flexibility**. This is the motivation behind the development of the **FairDM framework**—a powerful tool that empowers individual research communities to both declare and manage **domain-specific data models** and deploy **community-driven research data portals**, managed by experts who understand the unique needs, workflows, and semantics of their field.  

FairDM provides a structured yet customizable approach to FAIR data management. It allows domain experts to extend pre-defined *core data models*, which serve as a common foundation for all data and metadata schemas across scientific disciplines. Individual research communities inherit and build upon these core models with domain-specific data fields, vocabularies, and validation rules. This system ensures that data and metadata collected within a FairDM data portal are meaningful within the discipline and more reusable across different domains.



By combining **technical standardization** with **community-led customization**, FairDM represents a new generation of research data infrastructure—one that bridges the gap between FAIR theory and FAIR practice.

## References

- Data Citation Synthesis Group. (2014). *Joint Declaration of Data Citation Principles*. FORCE11. https://doi.org/10.25490/a97f-egyk
- European Commission. (2018). *Turning FAIR into Reality*. Final Report and Action Plan from the European Commission Expert Group on FAIR Data. https://doi.org/10.2777/1524
- GO FAIR. (2018). *GO FAIR: Making Data FAIR*. [https://www.go-fair.org](https://www.go-fair.org)
- Groth, P., Cousijn, H., & Schultes, E. (2020). *FAIR Data Reuse: The Path Through Data Citation*. Data Intelligence, 2(1-2), 78–86. https://doi.org/10.1162/dint_a_00034
- Max Planck Society. (2003). *Berlin Declaration on Open Access to Knowledge in the Sciences and Humanities*. https://openaccess.mpg.de/Berlin-Declaration
- NIH. (2023). *NIH Final Policy for Data Management and Sharing*. [https://sharing.nih.gov](https://sharing.nih.gov)
- OECD. (2007). *Principles and Guidelines for Access to Research Data from Public Funding*. https://doi.org/10.1787/9789264034020-en
- RDA. (2024). *Research Data Alliance*. [https://www.rd-alliance.org](https://www.rd-alliance.org)
- Sansone, S. A., et al. (2019). *FAIRsharing as a community approach to standards, repositories and policies*. *Nature Biotechnology*, 37, 358–367. https://doi.org/10.1038/s41587-019-0080-8
- UNESCO. (2021). *UNESCO Recommendation on Open Science*. [https://unesdoc.unesco.org/ark:/48223/pf0000379949](https://unesdoc.unesco.org/ark:/48223/pf0000379949)
- Wilkinson, M. D., et al. (2016). *The FAIR Guiding Principles for scientific data management and stewardship*. *Scientific Data*, 3, 160018. https://doi.org/10.1038/sdata.2016.18
