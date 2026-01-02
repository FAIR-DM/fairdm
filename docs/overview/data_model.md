# Core Data Model

A major strength of the FairDM framework lies in its use of a **shared core data model**. This foundational structure ensures that all domain-specific extensions are built on a consistent, interoperable base, which dramatically improves data discoverability, integration, and reuse across disciplines.

![Core data model of FairDM](/_static/core_data_model.png)

The core model is organized into four interconnected levels—**Project**, **Dataset**, **Sample**, and **Measurement**—each designed to capture essential metadata common to a wide range of research domains:

- The **Project** level captures overarching metadata such as collaborators, funding, and general project descriptions.
- The **Dataset** level aligns with internationally-recognised standards like **DataCite**, making it easier to formally publish and cite datasets using external services.
- The **Sample** level supports persistent identification through systems like **IGSN**, and enables structured relationships between complex physical or digital samples.
- The **Measurement** level offers a generalizable framework for describing observed values, while allowing communities to define their own domain-specific measurement schemas.

By establishing this shared foundation, FairDM ensures that even as individual communities define their own specialized data models, they continue to **speak a common language** at the structural level. This has several important benefits:

- **Interoperability by design**: Since all community-defined models inherit from the same base, data produced in different domains can be more easily integrated, compared, or reused in broader research contexts.
- **Reduced duplication of effort**: Communities don't need to reinvent basic structures or metadata concepts. Instead, they can focus their energy on refining and extending what’s already there, adding only the domain-specific details that matter most.
- **Tool and service compatibility**: Standardized core schemas enable the development of reusable tools, APIs, and validation mechanisms that can operate across all FairDM-based portals without custom configuration for each community.
- **Scalability and sustainability**: A modular, extensible approach encourages collaboration across communities, while also supporting long-term maintenance of the infrastructure as standards evolve.

In short, the core model acts as a **semantic and technical glue** that connects diverse research communities under a unified, extensible framework—balancing the need for local autonomy with the broader goals of FAIR data stewardship.

## The `Project` Model

In FairDM, a **Project** is the highest-level concept in the data model. Think of it as a **container for all the research activities and data** associated with a particular scientific investigation. Every dataset, sample, and measurement **can be** linked to a specific project—this helps keep things organized and traceable.

### What does a Project represent?

A project typically includes:

- **A name** that identifies the research.
- **An image** that visually represents the project (like a logo or key figure).
- **Keywords and tags** that make the project easier to find in searches.
- **Status information**, like whether the project is still being developed or is already published.
- **Visibility settings**, which control who can see the project (private, public, etc.).
- **Contributor information**, such as the people and organizations involved.
- **Funding details**, like grant numbers or funding agencies.
- **Time stamps**, to show when the project was created or last updated.

These fields make sure that each project includes enough **essential metadata** to support the FAIR principles (Findable, Accessible, Interoperable, Reusable).

## The `Dataset` Model

In FairDM, a **Dataset** is the second key building block, directly below a Project. You can think of a dataset as a **folder of research data** that belongs to a specific project. This folder not only contains data itself—like measurements or samples—but also all the extra information needed to understand and reuse that data.

Every dataset **must belong to a project**, and every sample, measurement, or site you add will be connected to a dataset.

### What does a Dataset include?

A dataset typically holds:

- **A name**: The title or short description of what the dataset contains.
- **An image**: (Optional) A visual related to the dataset, like a photo of a study site or chart.
- **Keywords and tags**: These help people find the dataset more easily when searching.
- **Visibility settings**: These control who can view the dataset (private or public).
- **Time stamps**: Indicate when the dataset was created or last modified.
- **Contributor information**: Who created or worked on this dataset.
- **Descriptions**: Structured descriptions explaining what the dataset contains and how it was collected.
- **Optional links to publications**: References to scientific articles or reports related to the dataset.
- **License information**: Explains how the data can be reused. By default, FairDM comes with support for standard Creative Commons licenses.

## The `Sample` Model

A **Sample** in FairDM represents a physical or digital object that is part of a dataset. This could be anything from a rock or water sample, to a digital file like an image, audio clip, or simulation result. Every sample belongs to a dataset, which in turn is part of a project.

While `Project` and `Dataset` are not meant to be extended or modified, the **Sample model *can* be extended**. This means researchers or developers can create custom sample types to store extra information specific to their scientific domain.

### What does a Sample include?

Each sample by default includes:

- **A name**: A short, descriptive title for the sample.
- **An image**: (Optional) A visual representation of the sample.
- **Keywords and tags**: Help make the sample more searchable and easier to categorize.
- **A local ID**: A custom identifier used internally by the researchers, often printed on labels or containers.
- **A status**: Such as "collected", "analyzed", or "unknown" to indicate the sample’s current state.
- **A location**: If the sample has a known geographic origin, you can link it to a location record.
- **Time stamps**: Automatically track when the sample was created and last updated.
- **Contributors**: You can list who helped collect, prepare, or manage the sample.
- **Descriptions**: Structured descriptions explaining what the sample is and how it was collected.

And most importantly:

- **It must belong to a dataset**, ensuring traceability and context.

### Can I add custom fields to the Sample model?

**Yes.** Unlike Project or Dataset, the Sample model is **designed to be extended**. This means we encourage you to develop and maintain data model appropriate to your specific research community.

For example, if you're studying tree cores, you could create a new sample type called `TreeCoreSample` that inherits the default Sample metadata and adds extra fields like:

- Tree species
- Core length
- Ring count

This way, you don’t directly modify the base Sample model, but you still get all of its standard features and metadata.

### What does it mean to extend the Sample model?

Technically, your custom sample type will still be treated as a Sample in the system, so all search tools and visualizations will work seamlessly. But you'll also have your own extra fields, which only appear on your specialized sample type.

This makes the system flexible and powerful across disciplines—whether you're studying soil, ice cores, fossils, or digital simulations.

## Understanding the `Measurement` Model

A **Measurement** in FairDM represents a result or observation made **on a sample**. Think of it as the data you collect *from* a sample—like a weight, pH reading, chemical composition, or even an image analysis.

Like samples, measurements are **polymorphic**, which means they can be **extended** to include additional fields specific to your scientific needs.

### What does a Measurement include?

Each measurement records:

- **A name**: A descriptive title of what the measurement is.
- **An image**: (Optional) A visual representation related to the measurement (e.g., microscope image).
- **Keywords and tags**: Help categorize and improve discoverability.
- **A dataset**: All measurements are tied to a dataset for traceability.
- **A sample**: Every measurement must be linked to the **sample it was taken from**.
- **Timestamps**: Automatically track when the measurement was created and last modified.
- **Contributors**: Optionally record who performed or contributed to the measurement.
- **Descriptions**: Structured descriptions explaining what the measurement represents and how it was produced.

### Can I extend the Measurement model?

**Yes.** The Measurement model is designed to be flexible. You can create your own custom measurement types by subclassing the base `Measurement` model.

For example, you could define a `pHMeasurement` model that adds:

- pH value
- Temperature at measurement
- Instrument used

Or a `SpectralMeasurement` model with:

- Wavelength range
- Resolution
- File upload for the spectrum data
