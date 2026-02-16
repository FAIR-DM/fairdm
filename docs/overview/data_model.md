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

A **Measurement** in FairDM represents a result or observation made **on a sample**. Think of it as the data you collect *from* a sample—like a weight, pH reading, chemical composition, image analysis, or laboratory test result.

Like samples, measurements are **polymorphic**, which means they can be **extended** to include additional fields specific to your scientific needs. However, measurements have unique characteristics that distinguish them from samples:

- **Measurements always reference a sample** - they cannot exist independently
- **Measurements belong to a dataset** - which may differ from the sample's dataset (enabling cross-dataset workflows)
- **Measurements are polymorphic** - different measurement types (XRF, ICP-MS, microscopy) can coexist with different field structures
- **Measurements have optimized querysets** - for efficient loading of related data (sample, dataset, metadata)

### Measurement Model Architecture

The `Measurement` model extends the core `SampleMetadataBase` class, giving it all the standard metadata capabilities (descriptions, dates, identifiers, contributors, tags) plus measurement-specific features:

```python
from fairdm.core import Measurement

class XRFMeasurement(Measurement):
    """X-ray fluorescence measurement for elemental analysis."""
    element = models.CharField(max_length=10)
    concentration_ppm = models.FloatField()
    detection_limit_ppm = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name = "XRF Measurement"
```

**Key features:**
- Inherits from `Measurement` base model (polymorphic)
- Automatically gets `sample` and `dataset` foreign keys
- Includes all FAIR metadata fields (descriptions, dates, identifiers)
- Can add domain-specific fields (element, concentration, etc.)

### Entity Relationship Diagram

The following diagram shows the core measurement model structure and relationships:

```{mermaid}
erDiagram
    Project ||--o{ Dataset : contains
    Dataset ||--o{ Sample : contains
    Dataset ||--o{ Measurement : contains
    Sample ||--o{ Measurement : "measured by"

    Measurement ||--o{ MeasurementDescription : "has"
    Measurement ||--o{ MeasurementDate : "has"
    Measurement ||--o{ MeasurementIdentifier : "has"
    Measurement ||--o{ Contribution : "has"

    Measurement {
        uuid id PK
        string name
        uuid sample_id FK
        uuid dataset_id FK
        datetime added
        datetime modified
        image image
    }

    Sample {
        uuid id PK
        string name
        uuid dataset_id FK
    }

    Dataset {
        uuid id PK
        string name
        uuid project_id FK
    }

    Project {
        uuid id PK
        string name
    }

    MeasurementDescription {
        int id PK
        string type
        text value
        uuid measurement_id FK
    }

    MeasurementDate {
        int id PK
        string type
        string value
        uuid measurement_id FK
    }

    MeasurementIdentifier {
        int id PK
        string type
        string value
        uuid measurement_id FK
    }

    Contribution {
        int id PK
        uuid contributor_id FK
        string roles
        int order
    }
```

**Key relationships:**
- **Measurement → Sample**: Every measurement references exactly one sample (required)
- **Measurement → Dataset**: Every measurement belongs to exactly one dataset (can differ from sample's dataset)
- **Measurement ↔ Metadata**: One-to-many relationships with descriptions, dates, and identifiers
- **Sample → Dataset**: Samples belong to datasets (establishing ownership and permissions)

### Polymorphic Measurement Types

FairDM supports multiple measurement types through polymorphic inheritance. Here's how different measurement types relate:

```{mermaid}
classDiagram
    class Measurement {
        <<abstract>>
        +uuid id
        +string name
        +Sample sample
        +Dataset dataset
        +image image
        +get_value() string
    }

    class XRFMeasurement {
        +string element
        +float concentration_ppm
        +float detection_limit_ppm
        +get_value() "X ppm Element"
    }

    class pHMeasurement {
        +float ph_value
        +float temperature_c
        +string instrument
        +get_value() "pH X @ Y°C"
    }

    class MicroscopyMeasurement {
        +string microscope_type
        +int magnification
        +float scale_bar_microns
        +file image
        +get_value() "Type Xmag"
    }

    class ICP_MS_Measurement {
        +string isotope
        +float counts_per_second
        +float concentration_ppb
        +string standard_used
        +get_value() "X ppb Isotope"
    }

    Measurement <|-- XRFMeasurement
    Measurement <|-- pHMeasurement
    Measurement <|-- MicroscopyMeasurement
    Measurement <|-- ICP_MS_Measurement
```

**How polymorphic measurements work:**
- All types share the base `Measurement` table (single table inheritance)
- Each type adds custom fields specific to that analysis method
- Query all measurements: `Measurement.objects.all()` returns all types
- Query specific type: `XRFMeasurement.objects.all()` returns only XRF measurements
- Admin interface automatically routes to type-specific forms and displays type-specific fields

### Relationship Flows: Measurement-Sample-Dataset

Measurements have two key relationships that enable flexible research workflows:

#### Standard Flow: Measurement in Same Dataset as Sample

```
Project
  └─ Dataset A
      ├─ Sample 1
      └─ Measurement 1 (references Sample 1, belongs to Dataset A)
```

This is the typical workflow where measurements are stored in the same dataset as their samples.

#### Cross-Dataset Flow: Measurement in Different Dataset

```
Project
  ├─ Dataset A (Sample Collection)
  │   └─ Sample 1 (collected 2024-01-15)
  └─ Dataset B (Laboratory Analysis)
      └─ Measurement 1 (references Sample 1 from Dataset A, belongs to Dataset B)
```

The following diagram visualizes cross-dataset measurement workflows:

```{mermaid}
graph TB
    subgraph Project["Project: Regional Geology Study"]
        subgraph DatasetA["Dataset A: Field Samples 2023"]
            S1[Sample: RS-001]
            S2[Sample: RS-002]
            S3[Sample: RS-003]
        end

        subgraph DatasetB["Dataset B: XRF Analysis 2024"]
            M1[Measurement: XRF-RS001-Fe]
            M2[Measurement: XRF-RS001-Si]
            M3[Measurement: XRF-RS002-Fe]
        end

        subgraph DatasetC["Dataset C: ICP-MS Analysis 2024"]
            M4[Measurement: ICPMS-RS001-U238]
            M5[Measurement: ICPMS-RS003-Th232]
        end
    end

    S1 -.->|measured by| M1
    S1 -.->|measured by| M2
    S2 -.->|measured by| M3
    S1 -.->|measured by| M4
    S3 -.->|measured by| M5

    style S1 fill:#e3f2fd
    style S2 fill:#e3f2fd
    style S3 fill:#e3f2fd
    style M1 fill:#fff9c4
    style M2 fill:#fff9c4
    style M3 fill:#fff9c4
    style M4 fill:#ffe0b2
    style M5 fill:#ffe0b2
```

**Why cross-dataset linking matters:**
- **Separation of concerns**: Sample collection metadata separate from analysis metadata
- **Different teams**: Field team manages samples, lab team manages measurements
- **Different timelines**: Samples collected years before analysis
- **Permission boundaries**: Lab team can add measurements without editing sample dataset
- **Provenance tracking**: Clear lineage showing which dataset performed which analyses

### Polymorphic Measurement Pattern

Measurements use Django's polymorphic models to support multiple measurement types in a single table structure:

**Benefits:**
- Query all measurements regardless of type: `Measurement.objects.all()`
- Filter by specific type: `XRFMeasurement.objects.all()`
- Admin interface shows type-specific fields automatically
- Type-safe: `isinstance(measurement, XRFMeasurement)` works correctly

**Type selection in admin:**
When creating a measurement, portal admins see a dropdown with all registered measurement types (XRF Measurement, ICP-MS Measurement, etc.). Selecting a type loads the appropriate form with type-specific fields.

### Measurement Lifecycle

```{mermaid}
flowchart LR
    A[Sample Collected] --> B[Measurement Created]
    B --> C[Measurement Edited]
    C --> D[Metadata Added]
    D --> E[Published]

    style A fill:#e3f2fd
    style B fill:#fff9c4
    style C fill:#fff9c4
    style D fill:#fff9c4
    style E fill:#c8e6c9
```

**1. Sample Collected** - Sample exists in a dataset
**2. Measurement Created** - Linked to sample and dataset
**3. Measurement Edited** - Values and metadata updated
**4. Metadata Added** - Descriptions, dates, identifiers, contributors
**5. Published** - Dataset made public (if desired)

### What does a Measurement include?

Each measurement records:

- **A name**: A descriptive title of what the measurement is (e.g., "XRF Analysis - Iron Content")
- **An image**: (Optional) A visual representation related to the measurement (e.g., spectrum plot)
- **Keywords and tags**: Help categorize and improve discoverability
- **A dataset**: All measurements are tied to a dataset for traceability
- **A sample**: Every measurement must be linked to the **sample it was measured from** (can be cross-dataset)
- **Timestamps**: Automatically track when the measurement was created and last modified
- **Contributors**: Optionally record who performed or contributed to the measurement
- **Descriptions**: Structured descriptions explaining what the measurement represents and how it was produced
  - Uses measurement-specific vocabulary types (`measured`, `method`, `protocol`, etc.)
- **Dates**: Structured dates for measurement events (analysis date, calibration date, etc.)
  - Uses measurement-specific vocabulary types (`analyzed`, `calibrated`, etc.)
- **Identifiers**: External IDs or references (lab notebook IDs, instrument IDs, etc.)

### Can I extend the Measurement model?

**Yes.** The Measurement model is designed to be flexible and domain-specific. You can create your own custom measurement types by subclassing the base `Measurement` model.

**Example: pH Measurement**
```python
class pHMeasurement(Measurement):
    """pH measurement with temperature compensation."""
    ph_value = models.FloatField(help_text="Measured pH value")
    temperature_c = models.FloatField(help_text="Temperature at measurement (°C)")
    instrument = models.CharField(max_length=100)

    def get_value(self):
        return f"pH {self.ph_value} at {self.temperature_c}°C"
```

**Example: Spectral Measurement**
```python
class SpectralMeasurement(Measurement):
    """Spectroscopic measurement with wavelength range."""
    min_wavelength_nm = models.FloatField(help_text="Minimum wavelength (nm)")
    max_wavelength_nm = models.FloatField(help_text="Maximum wavelength (nm)")
    resolution = models.FloatField(help_text="Resolution (nm)")
    spectrum_file = models.FileField(upload_to="spectra/")

    def get_value(self):
        return f"{self.min_wavelength_nm}-{self.max_wavelength_nm} nm ({self.resolution} nm resolution)"
```

**Registration with FairDM:**
After defining your measurement type, register it with the FairDM registry to enable automatic admin, forms, filters, and API endpoints:

```python
from fairdm.registry import register
from fairdm.registry.config import ModelConfiguration

@register
class XRFMeasurementConfig(ModelConfiguration):
    model = XRFMeasurement
    fields = ["name", "sample", "dataset", "element", "concentration_ppm"]
```

See the [Measurement Development Guide](../portal-development/measurements.md) for complete implementation details
