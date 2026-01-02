# Understanding Core Data Structures

As a data contributor, understanding how FairDM organizes research data will help you enter accurate, complete metadata. This page explains the core structures from a contributor's perspective.

## The Four Levels of Data Organization

FairDM organizes research data into a hierarchical structure with four main levels:

### 1. Projects

A **Project** is a high-level container for related research activities. Think of it as the overarching research initiative, grant, or collaboration.

**Examples:**
- "Arctic Climate Monitoring 2020-2025"
- "Urban Water Quality Assessment"
- "Geological Survey of Region XYZ"

**What you'll provide:**
- Project title and description
- Principal investigator and collaborators
- Funding information
- Key dates (start, end, milestones)

### 2. Datasets

A **Dataset** is a collection of samples and measurements focused on a specific research question or hypothesis within a project. A project can have multiple datasets.

**Examples:**
- "Summer 2024 Ice Core Samples" (within an Arctic climate project)
- "River Water Sampling Campaign" (within an urban water quality project)
- "Basalt Formation Survey" (within a geological survey project)

**What you'll provide:**
- Dataset title and abstract
- Research methods and protocols
- Geographic coverage
- Temporal coverage (when data was collected)
- Keywords and subject areas
- License and access restrictions

```{tip}
**FAIR focus at dataset level**: Dataset metadata aligns with international standards (like DataCite) to enable formal publication and citation. Take extra care to complete required fields at this level.
```

### 3. Samples

A **Sample** is a physical or digital object that you collect, process, and analyze. Each sample belongs to a dataset.

**Examples:**
- A rock specimen labeled "ROCK-001"
- A water sample from "Site A, Date 2024-06-15"
- A digital scan or photograph

**What you'll provide:**
- Sample identifier (often a lab code or field ID)
- Sample name and description
- Collection location (coordinates, site name, depth)
- Collection date and time
- Sample type and material
- Storage location and conditions

```{note}
Samples can have **sub-samples**. For example, a borehole core might be subdivided into depth intervals, each treated as a related sample.
```

### 4. Measurements

A **Measurement** (or observation) is a quantifiable result from analyzing a sample. Each sample can have many measurements.

**Examples:**
- "Mineral composition analysis via X-ray diffraction"
- "pH and dissolved oxygen readings"
- "Grain size distribution"

**What you'll provide:**
- Measurement type (e.g., chemical analysis, physical property)
- Method and instrument used
- Measured values and units
- Uncertainty or precision
- Date and analyst information

## How These Levels Connect

```text
Project
 ├── Dataset 1
 │    ├── Sample A
 │    │    ├── Measurement 1
 │    │    └── Measurement 2
 │    └── Sample B
 │         └── Measurement 3
 └── Dataset 2
      └── Sample C
           └── Measurement 4
```

Each level builds on the previous one:

- **Projects** group related **Datasets**
- **Datasets** contain **Samples**
- **Samples** have **Measurements**

## Contributors and Organizations

In addition to the four data levels, FairDM tracks:

- **Contributors**: People (researchers, technicians, data managers) involved in data collection and processing
- **Organizations**: Institutions (universities, research centers, funding agencies) affiliated with the data

When entering data, you'll link contributors to projects, datasets, and samples, assigning them roles like "Principal Investigator," "Data Collector," "Analyst," etc. This ensures proper credit attribution and supports FAIR principles.

## Required vs. Optional Fields

When adding or editing data, you'll encounter:

- **Required fields** (marked with a red asterisk *): Must be completed before saving
- **Recommended fields**: Strongly encouraged for FAIR compliance, but not strictly required
- **Optional fields**: Provide additional context when available

```{tip}
**Best practice**: Even if a field is optional, fill it in if you have the information. More complete metadata means more discoverable and reusable data.
```

## Example Workflow

Here's how a typical contributor adds data to a FairDM portal:

1. **Navigate to a Dataset**: From the portal homepage, find the dataset you're contributing to (e.g., "Summer 2024 Field Campaign").
2. **Add a Sample**: Click "Add Sample" and provide:
   - Sample ID: `FIELD-2024-001`
   - Name: "Water sample from Site A"
   - Collection date: 2024-06-15
   - Coordinates: Latitude/Longitude
   - Sample type: Water
3. **Add Measurements**: Once the sample is saved, click "Add Measurement" and provide:
   - Measurement type: pH measurement
   - Method: Handheld pH meter, calibrated to standard buffers
   - Result: 7.2
   - Units: pH units
   - Date: 2024-06-15
4. **Review and Save**: Double-check that required fields are complete and that your entries are accurate.

The portal will validate your entries and flag any missing required fields before allowing you to save.

## Next Steps

- **[Getting Started](getting_started.md)**: Walkthrough for adding your first sample and measurement
- **[Metadata Best Practices](metadata_practices.md)**: Tips for ensuring high-quality, FAIR-compliant metadata

```{seealso}
For a more technical description of the data model, see the [Core Data Model documentation](../contributing/core_data_model.md) in the framework contributor guide.
```
