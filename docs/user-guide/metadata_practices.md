# Metadata Best Practices

```{admonition} You are here
:class: tip
**User Guide** → Metadata Best Practices

This page provides tips for high-quality metadata that supports FAIR principles. If you landed here from a search, you may want to start with the [User Guide overview](index.md) or [Getting Started](getting_started.md) for context on the contributor role.
```

High-quality metadata is the foundation of FAIR (Findable, Accessible, Interoperable, Reusable) data. This guide provides practical tips for ensuring your data contributions are as valuable as possible for future research.

## Why Metadata Matters

When you contribute data to a FairDM portal, you're not just recording measurements—you're creating a lasting scientific record. Complete, accurate metadata ensures that:

- **Future researchers** (including your future self) can understand and reuse your data
- **Collaborators** can find relevant datasets and samples quickly
- **Data repositories** can correctly index and preserve your work
- **Funders and institutions** can demonstrate research impact and compliance

```{important}
**FAIR Principle**: "Data should be as open as possible, and as closed as necessary—but metadata should always be open." Even if data access is restricted, good metadata makes your research discoverable.
```

## Required vs. Optional Fields

### Always Provide Required Fields

Required fields (marked with a red asterisk *) are essential for identifying and locating samples and measurements. These typically include:

- **Sample ID**: A unique identifier following your lab or field convention
- **Collection Date**: When the sample was collected
- **Collection Location**: Geographic coordinates or site name
- **Sample Type**: Rock, water, sediment, etc.

**Why they matter**: Without these basics, samples cannot be reliably identified or located in the future.

### Strongly Recommended Fields

While not technically required, these fields dramatically improve data quality:

- **Description**: Contextual information about the sample or measurement
- **Method**: Details of how measurements were performed
- **Units**: Always specify units for numeric results
- **Uncertainty**: Measurement precision or error estimates
- **Storage Location**: Where physical samples are kept

**Why they matter**: They provide the scientific context needed to interpret and compare results.

### Optional Fields Are Still Valuable

Don't skip optional fields just because they're optional:

- **Notes**: Additional observations or anomalies
- **Analyst**: Who performed the analysis
- **Environmental Conditions**: Temperature, weather, etc., during sampling
- **References**: Related publications or protocols

**Why they matter**: These details often become critical when data is reused years later.

```{tip}
**When in doubt, include it**: If you're unsure whether to record a piece of information, err on the side of including it. You can't go back in time to collect metadata you didn't record.
```

## Use Controlled Vocabularies When Available

Many fields in FairDM portals use **controlled vocabularies**—predefined lists of standardized terms.

### Why Use Controlled Vocabularies?

- **Consistency**: Everyone uses the same term for the same concept (e.g., "pH" instead of "acidity")
- **Searchability**: Users can find all measurements of a specific type
- **Interoperability**: Data can be compared across projects and institutions

### How to Use Them

When you encounter a dropdown field:

1. **Select from the list** whenever possible rather than entering custom text
2. **Check existing entries** in the dataset to see which terms are already in use
3. **Contact your administrator** if the vocabulary is missing a term you need—they can add it system-wide

**Example**: If your portal has a controlled vocabulary for rock types, always select from the dropdown rather than typing "granite" manually in a free-text field.

```{seealso}
For discipline-specific controlled vocabularies, see:
- [Research Vocabularies](https://vocabularies.example.org) (link to your portal's vocabulary service if available)
- [IGSN Sample Types](https://www.geosamples.org/help/sampletypes)
- [CF Standard Names](http://cfconventions.org/standard-names.html) (for climate/ocean/atmosphere data)
```

## Record Provenance and Methods

**Provenance** is the history of a sample or measurement—where it came from, who collected it, how it was processed, and how it was analyzed.

### Best Practices for Provenance

#### For Samples

- **Record the collector**: If known, note who collected the sample
- **Document sample preparation**: If the sample was processed (e.g., filtered, dried, ground), describe the steps
- **Link to related samples**: If this sample is a subsample or related to another sample, note the connection

#### For Measurements

- **Specify the method**: Don't just say "pH meter"—include the make/model and calibration details
- **Record the analyst**: Who performed the analysis?
- **Document calibration and QA/QC**: Include calibration standards, blanks, replicates, etc.
- **Note instrument settings**: If relevant, record settings like detection limits, wavelengths, etc.

**Example (Good Provenance)**:  
Method: *Water pH measured using Hach HQ40d handheld meter (serial #12345), calibrated with NIST-traceable pH 4.0, 7.0, and 10.0 buffers immediately prior to measurement. Measurement precision ±0.05 pH units based on replicate measurements (n=3) of field blank.*

**Example (Insufficient Provenance)**:  
Method: *pH meter*

```{important}
**Why it matters**: Future researchers need to know if measurements from different campaigns are directly comparable, or if method differences require calibration.
```

## Be Specific and Consistent

### Use Specific, Descriptive Names

- **Good**: "River water sample from Site B main channel, low-flow conditions, June 2024"
- **Poor**: "Water sample 45"

### Maintain Consistent Naming Conventions

If your dataset uses a naming pattern (e.g., "SITE-YEAR-SEQUENCE"), continue it:

- **Good**: `SITE-B-2024-045`, `SITE-B-2024-046`, `SITE-B-2024-047`
- **Poor**: `SITE-B-2024-045`, `Site B 46`, `B-047`

### Use Standard Units and Formats

- **Dates**: Use ISO 8601 format (YYYY-MM-DD) whenever possible
- **Coordinates**: Decimal degrees (e.g., `45.5231, -122.6765`) are preferred over degrees/minutes/seconds
- **Units**: Use standard abbreviations (e.g., `mg/L`, `°C`, `ppm`) and always include them with numeric values

```{tip}
**Coordinate consistency**: If your portal uses a specific coordinate reference system (e.g., WGS84), always provide coordinates in that system. Don't mix coordinate systems within a single dataset.
```

## Review Before Saving

Before clicking "Save," take a moment to:

1. **Check for typos**: Especially in sample IDs and numeric values
2. **Verify required fields**: Are they all filled in?
3. **Ensure units are specified**: For all numeric measurements
4. **Review free-text fields**: Are descriptions clear and complete?
5. **Confirm links**: If you linked to a related sample, project, or contributor, is it correct?

```{tip}
**Use the preview**: If your portal offers a preview mode, use it to see how your entry will appear to others.
```

## Common Pitfalls to Avoid

❌ **Don't leave fields blank without reason**: If a field is optional but you have the information, provide it.

❌ **Don't use ambiguous abbreviations**: What's obvious to you now may be cryptic in five years (or to other researchers).

❌ **Don't mix units**: If most measurements are in mg/L, don't switch to ppm without clear documentation.

❌ **Don't skip methods**: "Standard method" or "usual procedure" is not sufficient. Reference specific protocols or SOPs.

❌ **Don't enter placeholder data**: If you don't have a value yet, leave the field blank rather than entering "TBD" or "999."

## When to Seek Help

Contact your portal administrator if:

- A required field doesn't make sense for your sample type
- The controlled vocabulary is missing a critical term
- You're unsure how to record a complex measurement or relationship
- You need to correct or delete data after submission

## Additional Resources

- **[Understanding Core Data Structures](core_data_model.md)**: Learn more about the purpose of each field
- **[Getting Started Guide](getting_started.md)**: Step-by-step walkthrough for your first contribution
- **Portal-Specific Guidance**: Check if your portal has additional metadata guidelines for your discipline

```{note}
**Keep learning**: Metadata best practices evolve. Check back periodically for updates to these guidelines, and share feedback with your portal team to improve documentation for future contributors.
```
