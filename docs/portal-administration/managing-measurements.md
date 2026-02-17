# Managing Measurements

This guide explains how portal administrators can manage measurements through the Django admin interface.

## Overview

Measurements represent analytical results or observations made on samples in your research portal. Each measurement is linked to a sample and optionally to a dataset. Measurements can have rich metadata including descriptions, dates, identifiers, and contributor information.

**Key Concepts:**

- Measurements are always linked to a sample
- Measurements can belong to a different dataset than their sample (cross-dataset measurements)
- Different measurement types capture different kinds of analytical data (XRF, pH, microscopy, etc.)
- Each measurement type has custom fields specific to that analysis method

## Accessing the Measurement Admin

### Option 1: From the Main Menu

1. Log in to the Django admin at `/admin/`
2. Navigate to **CORE** → **Measurements**
3. You'll see a type selection page with all registered measurement types

### Option 2: Direct to Measurement Type

1. Log in to the Django admin
2. Navigate directly to your measurement type (e.g., **CORE** → **XRF Measurements**)
3. You'll see a list of all measurements of that type

### Understanding the Type Selection Interface

When you click **Add Measurement**, you'll see a list of available measurement types:

- **XRF Measurement** - X-ray fluorescence elemental analysis
- **pH Measurement** - pH and temperature readings
- **Microscopy Measurement** - Microscope images and observations
- **Spectroscopy Measurement** - Spectral analysis data
- *...and other custom types*

**Choose the type that matches your analysis method**, then proceed with data entry.

## Creating Measurements

### Basic Measurement Creation

1. Click **Add Measurement** and select your measurement type
2. Fill in required fields:
   - **Name**: Descriptive identifier for the measurement
   - **Sample**: The sample this measurement was made on (searchable dropdown)
   - **Dataset**: The dataset this measurement belongs to (can differ from sample's dataset)
3. Fill in type-specific fields (varies by measurement type)
4. Click **Save** or **Save and continue editing**

### Measurement Type Examples

#### XRF Measurements

For X-ray fluorescence elemental analysis:

**Required fields:**

- Name: e.g., "XRF-RS001-Si"
- Sample: The analyzed sample
- Dataset: Your analytical dataset

**Type-specific fields:**

- Element: Chemical element (Fe, Si, Al, etc.)
- Concentration (ppm): Measured concentration
- Detection Limit (ppm): Instrument detection limit
- Instrument: XRF instrument used

**Example:**

```text
Name: XRF-RS001-Fe
Sample: RockSample-001
Dataset: XRF-Analysis-2024
Element: Fe
Concentration: 45000 ppm
Detection Limit: 10 ppm
Instrument: Bruker M4 Tornado
```

#### pH Measurements

For pH and related measurements:

**Required fields:**

- Name: e.g., "pH-WS001"
- Sample: Water or soil sample
- Dataset: Your measurement dataset

**Type-specific fields:**

- pH Value: Measured pH (0-14)
- Temperature (°C): Temperature during measurement
- Instrument: pH meter model

**Example:**

```text
Name: pH-WS001
Sample: WaterSample-001
Dataset: Water-Quality-2024
pH Value: 7.2
Temperature: 22.5°C
Instrument: Hanna HI98191
```

#### Microscopy Measurements

For microscope observations:

**Required fields:**

- Name: e.g., "SEM-RS001-Surface"
- Sample: Sample that was imaged
- Dataset: Your imaging dataset

**Type-specific fields:**

- Microscope Type: Optical, SEM, TEM
- Magnification: e.g., 1000x
- Scale Bar (μm): Length of scale bar
- Image: Upload microscope image

### Cross-Dataset Measurements

Measurements can belong to a different dataset than their sample:

**Why?**

- Sample from one project (e.g., "Field Samples 2023")
- Measurements from different analysis project (e.g., "Lab Analysis 2024")

**How to create:**

1. Select sample from any accessible dataset
2. Choose the appropriate measurement dataset
3. The system links them while preserving dataset boundaries

**Example:**

```text
Sample: RS-001 (from "Geological Survey 2023" dataset)
Measurement: XRF-RS001-Si (in "Laboratory XRF Analysis 2024" dataset)
```

This allows:

- Sample owners keep control of their samples
- Lab manages their analytical results separately
- Both teams can access relevant data

### Adding Metadata

Measurement metadata is managed through inline forms on the measurement edit page:

#### Descriptions

Add multiple descriptions of different types:

1. In the **Descriptions** section, click **Add another Description**
2. Select **Type**:
   - **Abstract**: Brief summary of the measurement
   - **Methods**: Analytical methods and parameters used
   - **Other**: Additional information
3. Enter **Value** (the description text)
4. Repeat for additional descriptions

**Example uses:**

- **Abstract**: "Silicon concentration in rock sample by XRF"
- **Methods**: "Analyzed using Bruker M4 Tornado XRF with 20kV beam energy, 30s dwell time, helium purge"
- **Other**: "Sample prepared by crushing and pressing into pellet"

#### Dates

Track important dates related to the measurement:

1. In the **Dates** section, click **Add another Date**
2. Select **Type**:
   - **Collected**: When data was collected/measured
   - **Available**: When data became available
   - **Created**: When the record was created
3. Enter **Value** in YYYY, YYYY-MM, or YYYY-MM-DD format
4. Repeat for additional dates

**Common date patterns:**

- **Collected**: 2024-03-15 (day sample was analyzed)
- **Available**: 2024-03 (month data was processed and QC'd)
- **Created**: 2024 (year record was entered into database)

#### Identifiers

Assign persistent identifiers to measurements:

1. In the **Identifiers** section, click **Add another Identifier**
2. Select **Type**:
   - **DOI**: Digital Object Identifier (for published data)
   - **Analysis ID**: Internal lab analysis number
   - **Other**: Custom identifier schemes
3. Enter **Value** (the identifier string)
4. Repeat for additional identifiers

**Example identifiers:**

- **Analysis ID**: "LAB-2024-0123"
- **DOI**: "10.5555/example.123"
- **Other**: "QC-CHECK-001"

#### Contributors

Track who performed, analyzed, or owns measurements:

1. In the **Contributors** section, click **Add another Contributor**
2. Select **Contributor** (user or contact from your portal)
3. Enter **Roles** (e.g., "analyst", "operator", "reviewer")
4. Optionally set **Order** for display ordering
5. Repeat for additional contributors

**Common contributor roles:**

- **analyst**: Person who performed the analysis
- **operator**: Instrument operator
- **reviewer**: QC reviewer who validated results
- **supervisor**: Lab supervisor

## Searching Measurements

The admin provides multiple ways to find measurements:

### Text Search

Use the search box at the top to search by:

- Measurement name
- Sample name (linked sample)
- UUID (unique identifier)

**Examples:**

- Search "XRF-RS001" to find measurements by name
- Search "RockSample-001" to find all measurements on that sample
- Search "m_abc123def456" to find by UUID

### Filters

Use the right sidebar to filter measurements by:

#### Dataset

Filter by parent dataset:

1. Click on a dataset name to show only measurements from that dataset
2. Useful for focusing on a specific analytical project

#### Sample

Filter by the sample analyzed:

1. Search for or select a sample
2. View all measurements made on that sample
3. Useful for sample-centric data exploration

#### Measurement Type

For mixed measurement lists, filter by specific type:

- XRF Measurements
- pH Measurements
- Microscopy Measurements
- Spectroscopy Measurements
- Etc.

### Advanced Filters (Type-Specific)

Each measurement type may provide additional filters:

**XRF Measurements:**

- Element (Fe, Si, Al, etc.)
- Concentration range (e.g., > 1000 ppm)

**pH Measurements:**

- pH range (e.g., 6.0 - 8.0)
- Temperature range

**Microscopy Measurements:**

- Microscope type
- Magnification range

### Combining Filters

Combine multiple filters for precise searches:

**Example: Find all XRF iron measurements above 10000 ppm**

1. Filter by type: "XRF Measurements"
2. Filter by element: "Fe"
3. Filter by concentration: "> 10000"

## Editing Measurements

### Quick Edit

From the measurement list:

1. Click the measurement name to open the edit page
2. Modify any fields
3. Add/edit/remove metadata using inline forms
4. Click **Save** or **Save and continue editing**

### Bulk Actions

Select multiple measurements using checkboxes, then:

**Available actions:**

- **Delete selected measurements**: Permanently remove measurements
  - ⚠️ Use with caution - this cannot be undone
  - Will also delete related metadata

**Custom actions** (if configured):

- Export selected measurements
- Recalculate values
- Assign to different dataset
- Run quality control checks

## Measurement List Display

The measurement list shows key information:

### Columns

- **Name**: Measurement identifier (click to edit)
- **Sample**: Linked sample name
- **Dataset**: Parent dataset name
- **Value**: Result from `get_value()` method (varies by type)
- **Type**: Measurement type (XRFMeasurement, pHMeasurement, etc.)
- **Created**: When record was created
- **Modified**: Last modification date

### Measurement Value Display

Each measurement type defines a `get_value()` method that shows in the admin:

**XRF Measurement:**

- Shows: "45000 ppm Fe"

**pH Measurement:**

- Shows: "pH 7.2 @ 22.5°C"

**Microscopy Measurement:**

- Shows: "SEM 1000x"

This provides quick insight into measurement results without opening each record.

### Sorting

Click column headers to sort:

- Name (alphabetical)
- Sample (alphabetical)
- Dataset (alphabetical)
- Created/Modified (chronological)

Click again to reverse sort order.

## Polymorphic Measurements

FairDM uses polymorphic inheritance for measurements:

**What this means:**

- All measurement types share the same base Measurement model
- Each type can have additional custom fields specific to that analysis method
- Queries automatically return the correct type
- Admin displays type-specific fields only for their type

**For administrators:**

- You can view all measurements together or filter by type
- Custom fields only appear for their specific type
- The type selection interface lets you choose the right type when creating measurements
- You cannot change a measurement's type after creation (delete and recreate instead)

**Example:**

When viewing an XRF Measurement, you'll see:

- Base fields: name, sample, dataset (all measurements have these)
- XRF fields: element, concentration_ppm, detection_limit_ppm (only XRF has these)

When viewing a pH Measurement, you'll see different custom fields:

- Base fields: name, sample, dataset
- pH fields: ph_value, temperature_c, instrument (only pH has these)

## Best Practices

### Naming Conventions

**Consistent naming:**

- Include measurement type prefix (e.g., "XRF-", "PH-", "SEM-")
- Include sample identifier (e.g., "XRF-RS001-Fe")
- Include analyte/parameter when relevant
- Use sequential numbers for batches

**Examples:**

- **Good**: `XRF-RS001-Fe`, `PH-WS-2024-0001`, `SEM-Sample01-Surface`
- **Bad**: `measurement1`, `test`, `data`

### Linking to Samples

**Always link to the correct sample:**

- Use the searchable dropdown to find samples
- Verify sample name before saving
- Check that sample exists in an accessible dataset

**Cross-dataset considerations:**

- Ensure you have permission to both the sample's dataset and the measurement's dataset
- Document the relationship in measurement description
- Consider which dataset should own the measurement

### Metadata Completeness

Aim for complete analytical metadata:

- **Descriptions**: Add Methods description with:
  - Instrument model
  - Operating parameters
  - Calibration standards used
  - Sample preparation steps
- **Dates**: Record when measurement was collected
- **Identifiers**: Assign lab analysis IDs for traceability
- **Contributors**: Credit the analyst and instrument operator

**Example complete metadata:**

```text
Measurement: XRF-RS001-Fe

Descriptions:
  - Abstract: "Iron concentration in rock sample by XRF"
  - Methods: "Bruker M4 Tornado XRF. 20kV, 600μA, 30s live time, helium purge.
             Calibrated against NIST SRM 2709a. Sample prepared by crushing to
             <100μm and pressing into 32mm pellet."

Dates:
  - Collected: 2024-03-15

Identifiers:
  - Analysis ID: LAB-2024-0123

Contributors:
  - Jane Analyst (analyst)
  - Lab Tech (operator)
```

### Quality Control

**Document QC measures:**

- Use descriptions to note QC samples run
- Track replicate measurements
- Document when values are below detection limits
- Note any quality flags or warnings

**Example QC documentation:**

```text
Description (Methods):
"Standard NIST-610 run before and after sample batch. RSD < 5% for all elements.
Blank run between samples. Detection limit calculated as 3σ of blank."
```

### Data Organization

**Organize by analytical project:**

- Create dedicated datasets for analytical campaigns
- Use consistent naming within a dataset
- Group related measurements together
- Consider batch processing for similar samples

## Troubleshooting

### Can't See Expected Measurements

**Check filters:**

1. Look at the right sidebar filters
2. Click "Clear all filters" to reset
3. Verify you have permission to view the dataset

**Check permissions:**

- Ensure you have view permission for the measurement's dataset
- If measurement is cross-dataset, check sample's dataset permissions too
- Contact a superuser if you need additional permissions

**Check measurement type:**

- If viewing "XRF Measurements", you won't see pH measurements
- Go to main "Measurements" page to see all types
- Filter by type to find specific measurement kinds

### Can't Create Measurement

**Sample not found:**

- Verify sample exists and is accessible
- Check that you have view permission for sample's dataset
- Try searching by sample's exact name or ID

**Dataset permission issues:**

- You need add permission for the measurement's dataset
- Contact dataset owner or superuser to grant permissions

**Type selection page empty:**

- No measurement types are registered in your portal
- Contact administrator to register measurement types
- See developer guide for adding custom measurement types

### Measurement Value Not Displaying

**get_value() returns None:**

- Check that required fields are filled in
- For XRF: both element and concentration must be set
- For pH: ph_value must be set
- For Microscopy: microscope_type and magnification must be set

**Value shows "None" in list:**

- Implementation issue with get_value() method
- Contact developer to fix measurement type
- Edit measurement and verify all required fields are present

### Cross-Dataset Errors

**"Permission denied to sample's dataset":**

- You need view permission for sample's dataset to link to it
- Request access to sample's dataset from owner
- Or choose a different sample from an accessible dataset

**"Sample not found in dataset":**

- Sample and measurement can be in different datasets (this is OK)
- Only the sample must exist in an accessible dataset
- Measurement belongs to your selected measurement dataset

### Missing Custom Fields

**Wrong measurement type:**

- Custom fields only appear for their specific type
- Verify you're editing the correct measurement type
- E.g., "element" only appears on XRF Measurements

**Need to change measurement type:**

- ⚠️ You cannot change type after creation
- Create a new measurement with the correct type
- Delete the incorrect measurement
- Copy data to the new measurement

## Data Export

### Exporting Measurement Data

To export measurements:

1. Select measurements using checkboxes (or select all)
2. Choose **Export selected measurements** from action dropdown
3. Click **Go**
4. Choose export format (CSV, JSON, Excel)
5. Download the exported file

**Exported data includes:**

- All base Measurement fields (name, sample, dataset, etc.)
- Type-specific custom fields (element, pH, magnification, etc.)
- Related metadata (descriptions, dates, identifiers, contributors)
- Sample information (linked sample details)

### Export Formats

**CSV:**

- Best for spreadsheet import and analysis
- One row per measurement
- Sample data in separate columns
- Nested metadata flattened

**JSON:**

- Best for data interchange and APIs
- Preserves full structure including nested metadata
- Includes sample relationships
- Easy to re-import

**Excel:**

- Best for reporting and sharing
- Multiple sheets (measurements, metadata)
- Formatted for readability
- Includes charts (if configured)

### Export Use Cases

**For publication:**

1. Export measurements as CSV
2. Import into R, Python, or Excel for analysis
3. Generate figures and tables
4. Include export file as supplementary data

**For collaboration:**

1. Export as JSON with full metadata
2. Share with collaborators
3. They can import into their portal
4. Preserves all relationships and provenance

**For reporting:**

1. Export as Excel
2. Use for grant reports or presentations
3. Ready-made tables with formatting
4. No additional processing needed

## Data Import

### Importing Measurements

To import measurements:

1. Click **Import** button (if available)
2. Choose file format (CSV, JSON, Excel)
3. Upload your file
4. Review import preview showing what will be created
5. Confirm import if preview looks correct

**Import requirements:**

- Must include required fields (name, sample, dataset)
- Sample must exist (referenced by name or ID)
- Dataset must exist and you must have permission
- File format must match expected structure

### Import Validation

The import system validates:

- Required fields are present (name, sample)
- Sample references are valid (sample exists and is accessible)
- Dataset exists and you have add permission
- Field values are valid (proper types, within ranges)
- No duplicate identifiers

**If errors occur:**

- Review the error messages carefully
- Fix issues in source file
- Common issues:
  - Sample names don't match exactly (check spelling)
  - Missing required fields
  - Invalid field values (e.g., pH > 14)
- Retry import after fixing

### Import Best Practices

**Prepare your data:**

1. Export an example measurement first to see expected format
2. Match column names exactly (case-sensitive)
3. Include all required fields
4. Validate data before import (check ranges, formatting)

**Test with small batch:**

1. Import 3-5 measurements first
2. Verify they appear correctly
3. Check metadata and relationships
4. Then import full dataset

**Document your import:**

1. Add description noting data source
2. Include import date
3. Reference original file name
4. Note any transformations applied

## Permissions and Access Control

### Required Permissions

To manage measurements, you need:

**View permission**: See measurements in admin

- `view_measurement` or `view_<measurementtype>`

**Add permission**: Create new measurements

- `add_measurement` or `add_<measurementtype>`
- Also need `view_sample` for the linked sample

**Change permission**: Edit existing measurements

- `change_measurement` or `change_<measurementtype>`

**Delete permission**: Remove measurements

- `delete_measurement` or `delete_<measurementtype>`

### Dataset-Level Permissions

Measurements inherit permissions from their dataset:

- If you can edit a dataset, you can edit its measurements
- If you can only view a dataset, you can only view its measurements

**For cross-dataset measurements:**

- Need view permission for sample's dataset (to link to samples)
- Need appropriate permission for measurement's dataset (to create/edit measurements)

**Example scenario:**

```text
Sample: RS-001 in "Field Samples" dataset
Measurement: XRF-RS001 in "Lab Analysis" dataset

To create this measurement, you need:
- View permission for "Field Samples" (to select sample)
- Add permission for "Lab Analysis" (to create measurement)
```

### Requesting Permissions

**To request permissions:**

1. Contact the dataset owner or project manager
2. Or contact a portal administrator
3. Specify:
   - Which datasets you need access to
   - What permission level you need (view/add/change/delete)
   - Why you need access (e.g., "I'm the XRF analyst for this project")

## See Also

- [Managing Samples](managing-samples.md) - Sample management guide
- [Managing Projects](managing-projects.md) - Parent project management
- [Adjusting Dataset Access](adjusting-dataset-access.md) - Permission management
- [Managing Users and Permissions](managing-users-and-permissions.md) - User access control
- [Developer Guide: Custom Measurements](../portal-development/measurements.md) - For developers creating new measurement types
- [Understanding Controlled Vocabularies](../portal-development/controlled_vocabularies.md) - Vocabulary management
