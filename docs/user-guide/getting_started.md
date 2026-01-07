# Getting Started as a Contributor

```{admonition} You are here
:class: tip
**User Guide** → Getting Started

This page walks you through your first data contribution. If you landed here from a search, you may want to start with the [User Guide overview](index.md) to understand the contributor role and FAIR principles.
```

This guide walks you through your first data contribution to a FairDM portal. You'll learn how to locate an existing dataset, understand its structure, add a new sample, and record measurements while following FAIR metadata practices.

## Prerequisites

- A FairDM portal account with contributor permissions for at least one dataset
- Basic familiarity with the research domain and data you're contributing

```{tip}
If you don't yet have an account, contact your portal administrator to request access.
```

## Step 1: Log In and Navigate to Your Dataset

### Log In

1. Navigate to your portal's homepage
2. Click **Log In** (usually in the top-right corner)
3. Enter your username and password
4. Click **Sign In**

### Find Your Dataset

1. From the homepage, click **Datasets** in the main navigation
2. Browse or search for the dataset you're contributing to (e.g., "Field Campaign 2024")
3. Click on the dataset name to open its detail page

You should now see:

- Dataset title and description
- Existing samples (if any have been added)
- Option to **Add Sample** (if you have contributor permissions)

```{note}
If you don't see an "Add Sample" button, you may not have contributor permissions for this dataset. Contact your portal administrator to request access.
```

## Step 2: Review Existing Data and Field Meanings

Before adding new data, take a moment to review what's already in the dataset:

### Review Existing Samples

If samples are already listed:

1. Click on one or two sample names to view their detail pages
2. Note the structure:
   - **Sample ID**: Usually a lab code or field identifier
   - **Name**: A human-readable description
   - **Collection details**: Location, date, depth, etc.
   - **Sample type**: Rock, water, sediment, etc.
3. Observe which fields are filled in and which are left blank

This helps you understand the expected level of detail and consistency.

### Understand Required Fields

On the sample detail page, look for:

- **Required fields** (marked with a red asterisk *): Must be completed
- **Recommended fields**: Strongly encouraged for FAIR compliance
- **Optional fields**: Provide if available

```{tip}
**Consistency matters**: Try to match the level of detail and naming conventions used in existing samples. For example, if location names follow a specific pattern (e.g., "Site A-1", "Site A-2"), continue that pattern.
```

## Step 3: Add a New Sample

Now you're ready to add your own sample to the dataset.

### Start the Add Sample Form

1. Return to the dataset's main page (click the dataset name in the breadcrumb navigation)
2. Click **Add Sample**
3. You'll see a form with multiple fields

### Fill in Sample Details

Here's a typical example for a water sample:

**Sample ID** (required): `WATER-2024-045`  
- Use a unique identifier that follows your lab or field naming convention

**Name** (required): `River water sample from Site B, June 2024`  
- Provide a descriptive name that helps identify the sample at a glance

**Description** (optional but recommended): `Water sample collected from the main channel at Site B during low-flow conditions. Part of the summer monitoring campaign.`  
- Add context that will help future users (including your future self) understand the sample

**Collection Date** (required): `2024-06-20`  
- Use the date picker or enter the date in YYYY-MM-DD format

**Collection Location** (required):  
- **Latitude**: `45.5231`
- **Longitude**: `-122.6765`
- **Site Name**: `Site B - Main Channel`

**Sample Type** (required): Select `Water` from the dropdown (or enter a custom type if your portal allows)

**Storage Location** (optional): `Lab Freezer 3, Shelf B`  
- Record where the sample is physically stored for future reference

### Save the Sample

1. Review your entries to ensure accuracy
2. Click **Save** at the bottom of the form

If any required fields are missing, the form will highlight them in red and prevent saving until they're completed.

```{seealso}
For a detailed explanation of each field and how it supports FAIR principles, see [Understanding Core Data Structures](core_data_model.md).
```

## Step 4: Add Measurements to Your Sample

Once your sample is saved, you can record observations and analysis results as measurements.

### Navigate to the Sample

After saving, you should be redirected to the sample's detail page. If not:

1. Go back to the dataset page
2. Click on the sample you just created

### Start Adding a Measurement

1. On the sample detail page, click **Add Measurement**
2. You'll see a measurement form

### Fill in Measurement Details

Here's an example for a pH measurement:

**Measurement Type** (required): Select `pH Measurement` from the dropdown (or enter a custom type)

**Method** (required): `Handheld pH meter (Brand XYZ Model 123), calibrated with standard pH 4.0, 7.0, and 10.0 buffers prior to measurement.`  
- Be specific about the instrument and method used

**Result** (required): `7.35`  
- Enter the measured value

**Units** (required): `pH units` (dimensionless)

**Uncertainty** (optional but recommended): `±0.05`  
- If known, provide the measurement precision or uncertainty

**Analysis Date** (required): `2024-06-21`  
- The date the measurement was performed (may differ from sample collection date)

**Analyst** (optional): Link or enter the name of the person who performed the analysis

**Notes** (optional): `Measurement taken at field site immediately after sample collection; sample temperature was 18°C.`  
- Add any relevant context

### Save the Measurement

1. Review your entries
2. Click **Save**

The measurement will now appear associated with your sample.

```{tip}
**Add multiple measurements**: Repeat this process to add additional measurements (e.g., dissolved oxygen, temperature, turbidity) for the same sample.
```

## Step 5: Review Your Contribution

After saving, return to the dataset page to see your sample and measurements listed.

### Verify Your Entries

1. Click on your sample name
2. Review all fields for accuracy
3. Check that measurements are correctly associated with the sample
4. If you spot an error, click **Edit** (if you have edit permissions) to make corrections

### Understand Required vs. Optional Metadata

As you review, notice which fields you filled in:

- **Required fields**: Sample ID, Name, Collection Date, Location, Type → These are essential for identifying and locating the sample.
- **Recommended fields**: Description, Storage Location, Method details → These improve discoverability and reusability.
- **Optional fields**: Notes, Analyst, Uncertainty → Nice to have when available; they provide additional scientific context.

```{important}
**FAIR-compliant metadata**: The more complete your metadata, the more valuable your data becomes for future research. Even optional fields contribute to making data Findable, Accessible, Interoperable, and Reusable.
```

## What You've Accomplished

Congratulations! You've completed your first data contribution:

✅ Logged in and navigated to a dataset  
✅ Reviewed existing samples to understand field meanings and conventions  
✅ Added a new sample with required metadata  
✅ Recorded a measurement with method details and results  
✅ Verified your entries for accuracy  

## Next Steps

- **[Metadata Best Practices](metadata_practices.md)**: Learn tips for ensuring high-quality, FAIR-compliant contributions
- **[Understanding Core Data Structures](core_data_model.md)**: Deep dive into Projects, Datasets, Samples, and Measurements
- **Explore other datasets**: Contribute to additional datasets within your portal's projects

```{tip}
**Questions or issues?** If you encounter any problems while contributing data, contact your portal administrator or consult the portal's help documentation for dataset-specific guidance.
```
