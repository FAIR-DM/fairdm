# Managing Samples

This guide explains how portal administrators can manage samples through the Django admin interface.

## Overview

Samples represent physical or digital objects in your research portal. Each sample belongs to a dataset and can have rich metadata including descriptions, dates, identifiers, and relationships to other samples.

## Accessing the Sample Admin

1. Log in to the Django admin at `/admin/`
2. Navigate to **CORE** → **Samples** (or your specific sample type like "Rock Samples")
3. You'll see a list of all samples with search and filter options

## Creating Samples

### Basic Sample Creation

1. Click **Add Sample** (or specific type like "Add Rock Sample")
2. Fill in required fields:
   - **Name**: Short identifier for the sample
   - **Dataset**: Parent dataset (dropdown filtered by your permissions)
3. Fill in optional fields:
   - **Local ID**: Internal lab identifier
   - **Location**: Geographic location (if applicable)
   - **Status**: Sample status (Available, Used, Archived, etc.)
4. Add type-specific fields (e.g., rock type, pH level, temperature)
5. Click **Save** or **Save and continue editing**

### Adding Metadata

Sample metadata is managed through inline forms on the sample edit page:

#### Descriptions

Add multiple descriptions of different types:

1. In the **Descriptions** section, click **Add another Description**
2. Select **Type** (Abstract, Methods, Other)
3. Enter **Value** (the actual description text)
4. Repeat for additional descriptions

**Example uses**:

- **Abstract**: Brief summary of what the sample is
- **Methods**: How it was collected or prepared
- **Other**: Any other relevant information

#### Dates

Track important dates related to the sample:

1. In the **Dates** section, click **Add another Date**
2. Select **Type** (Collected, Available, Created)
3. Enter **Value** in YYYY, YYYY-MM, or YYYY-MM-DD format
4. Repeat for additional dates

**Common date types**:

- **Collected**: When the sample was collected in the field
- **Available**: When the sample became available for analysis
- **Created**: When the sample record was created in the database

#### Identifiers

Assign persistent identifiers to samples:

1. In the **Identifiers** section, click **Add another Identifier**
2. Select **Type** (IGSN, Barcode, Other)
3. Enter **Value** (the identifier string)
4. Repeat for additional identifiers

**Common identifier types**:

- **IGSN**: International Geo Sample Number (for geological samples)
- **Barcode**: Internal lab barcode
- **Other**: Any other identifier system

#### Contributors

Track who collected, analyzed, or owns samples:

1. In the **Contributors** section, click **Add another Contributor**
2. Select **Contributor** (user or contact)
3. Enter **Roles** (e.g., "collector", "analyst", "owner")
4. Optionally set **Order** for display ordering
5. Repeat for additional contributors

### Sample Relationships

Track provenance and relationships between samples:

1. In the **Relationships (as source)** section, click **Add another Relationship**
2. Select **Target** sample (the related sample)
3. Select **Type** (child_of, derived-from, split-from, replicate-of)
4. Optionally add **Description** explaining the relationship
5. Repeat for additional relationships

**Common relationship types**:

- **child_of**: Sample is a child/subsample of another
- **derived-from**: Sample derived through processing (e.g., powder from rock)
- **split-from**: Sample split from a larger sample
- **replicate-of**: Duplicate/replicate sample for QC

## Searching Samples

The admin provides multiple ways to find samples:

### Text Search

Use the search box at the top of the list to search by:

- Sample name
- Local ID
- UUID (unique identifier)

**Examples**:

- Search "RS-001" to find samples by name
- Search "ABC123" to find by local ID
- Search "s_abc123def456" to find by UUID

### Filters

Use the right sidebar to filter samples by:

#### Dataset

Filter by parent dataset:

1. Click on a dataset name to show only samples from that dataset
2. Useful for focusing on a specific research project

#### Status

Filter by sample status:

- **Available**: Samples ready for analysis
- **Used**: Samples that have been consumed/analyzed
- **Archived**: Samples in long-term storage
- **Destroyed**: Samples that no longer exist
- **Loan**: Samples on loan to another institution

#### Sample Type

For mixed sample lists, filter by specific type:

- Rock Samples
- Water Samples
- Soil Samples
- Etc.

### Combining Filters

You can combine multiple filters:

1. Select a dataset
2. Then select a status
3. Results show samples matching both filters

## Editing Samples

### Quick Edit

From the sample list:

1. Click the sample name to open the edit page
2. Modify any fields
3. Add/edit/remove metadata using inline forms
4. Click **Save** or **Save and continue editing**

### Bulk Actions

Select multiple samples using checkboxes, then:

**Available actions**:

- **Delete selected samples**: Permanently remove samples
  - ⚠️ Use with caution - this cannot be undone
  - Will also delete related metadata

**Custom actions** (if configured):

- Export selected samples
- Change status of selected samples
- Assign to different dataset

## Sample List Display

The sample list shows key information:

### Columns

- **Name**: Sample identifier (click to edit)
- **Local ID**: Internal lab ID
- **Dataset**: Parent dataset name
- **Type**: Sample type (RockSample, WaterSample, etc.)
- **Status**: Current status
- **Created**: When record was created
- **Modified**: Last modification date

### Sorting

Click column headers to sort:

- Name (alphabetical)
- Dataset (alphabetical)
- Created/Modified (chronological)

Click again to reverse sort order.

## Sample Relationships Visualization

### Viewing Relationships

On a sample's edit page, relationships are shown in two sections:

**Relationships (as source)**:

- Shows samples this sample is related to
- E.g., "This powder was derived-from Rock-001"

**Relationships (as target)**:

- Shows samples related to this one
- E.g., "Powder-001 was derived-from this rock"

### Creating Hierarchies

To create a sample hierarchy:

1. Create parent sample (e.g., core sample)
2. Create child samples (e.g., sections)
3. For each child:
   - Edit the child sample
   - Add relationship: source=child, target=parent, type=child_of
4. Navigate back to parent to see all children listed

## Polymorphic Samples

FairDM uses polymorphic inheritance, meaning:

- All sample types share the same database table
- Each type can have additional custom fields
- Queries automatically return the correct type

**What this means for admins**:

- You can view all samples together or filter by type
- Custom fields only appear for their specific type
- Relationships work across different sample types

## Best Practices

### Naming Conventions

**Consistent naming**:

- Use consistent prefixes (e.g., "RS-" for rock samples)
- Include sequential numbers (e.g., "RS-001", "RS-002")
- Avoid special characters that might cause issues

**Bad**: `Rock #1!!!`, `sample`, `test123`
**Good**: `RS-001`, `WS-2024-0001`, `CORE-A-001`

### Status Tracking

Keep status up to date:

- Set to **Available** when sample enters lab
- Change to **Used** after analysis that consumes sample
- Use **Archived** for long-term storage
- Update to **Destroyed** if sample no longer exists

### Metadata Completeness

Aim for complete metadata:

- Add at least one description (Abstract)
- Record collection date if known
- Assign persistent identifiers (IGSN, etc.)
- Track contributors (collector, analyst)

### Relationship Documentation

When adding relationships:

- Always include a description explaining the relationship
- Be consistent with relationship types
- Create relationships from child to parent
- Check both directions to verify correctness

## Troubleshooting

### Can't See Expected Samples

**Check filters**:

1. Look at the right sidebar filters
2. Click "Clear all filters" to reset
3. Verify you have permission to view the dataset

**Check permissions**:

- Ensure you have view permission for the dataset
- Contact a superuser if you need additional permissions

### Can't Edit Sample

**Permission issues**:

- You need change permission for the dataset
- Contact a superuser to grant permissions

**Sample in use**:

- Some samples may be locked during analysis
- Wait for analysis to complete or contact analyst

### Relationship Errors

**"Circular relationship detected"**:

- You cannot create A → B and B → A relationships
- Review the relationship structure and fix the cycle

**"Sample cannot relate to itself"**:

- Source and target must be different samples
- Check that you selected the correct target sample

### Missing Custom Fields

**Wrong sample type**:

- Custom fields only appear for their specific type
- Verify you're editing the correct sample type
- E.g., "rock_type" only appears on Rock Samples

## Data Export

### Exporting Sample Data

To export samples:

1. Select samples using checkboxes (or select all)
2. Choose **Export selected samples** from action dropdown
3. Click **Go**
4. Choose export format (CSV, JSON, Excel)
5. Download the exported file

**Exported data includes**:

- All base Sample fields (name, local_id, status, etc.)
- Type-specific custom fields
- Related metadata (descriptions, dates, identifiers)
- Relationship information

### Export Formats

**CSV**:

- Best for spreadsheet import
- One row per sample
- Nested data (descriptions, etc.) in separate columns

**JSON**:

- Best for data interchange
- Preserves full structure
- Includes all relationships

**Excel**:

- Best for reporting
- Multiple sheets for related data
- Formatted for readability

## Data Import

### Importing Samples

To import samples:

1. Click **Import** button (if available)
2. Choose file format (CSV, JSON, Excel)
3. Upload your file
4. Review import preview
5. Confirm import

**Import requirements**:

- Must include required fields (name, dataset)
- Dataset must exist and you must have permission
- File format must match expected structure

### Import Validation

The import system validates:

- Required fields are present
- Foreign key references exist (dataset, location)
- Field values are valid (status choices, etc.)
- No duplicate identifiers

**If errors occur**:

- Review the error messages
- Fix issues in source file
- Retry import

## Permissions and Access Control

### Required Permissions

To manage samples, you need:

**View permission**: See samples in admin

- `view_sample` or `view_<sampletype>`

**Add permission**: Create new samples

- `add_sample` or `add_<sampletype>`

**Change permission**: Edit existing samples

- `change_sample` or `change_<sampletype>`

**Delete permission**: Remove samples

- `delete_sample` or `delete_<sampletype>`

### Dataset-Level Permissions

Samples inherit permissions from their dataset:

- If you can edit a dataset, you can edit its samples
- If you can only view a dataset, you can only view its samples

**To request permissions**:

1. Contact the dataset owner or project manager
2. Or contact a portal administrator
3. Specify which datasets you need access to

## See Also

- [Managing Projects](managing_projects.md) - Parent project management
- [Adjusting Dataset Access](adjusting_dataset_access.md) - Permission management
- [Managing Users and Permissions](managing_users_and_permissions.md) - User access control
- [Developer Guide: Custom Samples](../portal-development/models/custom-samples.md) - For developers creating new sample types
