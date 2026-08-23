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

1. Click **Add Sample**. The bare `Sample` record cannot be created directly — by design, no
   route can create one, including this one — so the admin's first step is always a type-choice
   page listing every registered sample type (e.g. "Rock Sample", "Water Sample").
2. Pick a type, then fill in required fields:
   - **Name**: Short identifier for the sample
   - **Dataset**: Parent dataset (every dataset is offered here, including private ones — the
     admin is where a portal is repaired)
3. Fill in optional fields:
   - **Local ID**: Internal lab identifier
   - **Location**: Geographic location (if applicable)
   - **Status**: Custody status (see the Status filter below; defaults to Unknown)
4. Add type-specific fields (e.g., rock type, pH level, temperature)
5. Click **Save** or **Save and continue editing**

### Adding Metadata

Sample metadata is managed through inline forms on the sample edit page:

#### Descriptions

Add multiple descriptions of different types:

1. In the **Descriptions** section, click **Add another Description**
2. Select **Type**
3. Enter **Value** (the actual description text)
4. Repeat for additional descriptions — the form offers at most one row per type in the
   vocabulary, so a fully-described sample cannot add a sixth

**Sample description types**:

- **Collection**: How and where the specimen was collected
- **Preparation**: How it was prepared for storage or analysis
- **Storage**: How and where it is stored
- **Destruction**: Circumstances of its destruction, where applicable
- **Other**: Anything that does not fit the four types above

#### Dates

Track important dates related to the sample:

1. In the **Dates** section, click **Add another Date**
2. Select **Type**
3. Enter **Value** in YYYY, YYYY-MM, or YYYY-MM-DD format
4. Repeat for additional dates — one row per type, same limit as descriptions

**Sample date types**:

- **Created**: When the sample record was created in the database
- **Destroyed**: When the specimen was destroyed
- **Collected**: When the sample was collected in the field
- **Returned**: When the specimen was returned (e.g. from loan)
- **Prepared**: When the specimen was prepared for storage or analysis
- **Archival**: When the specimen entered long-term storage
- **Restored**: When the specimen was restored from destroyed or another lapsed state

#### Identifiers

Assign persistent identifiers to samples:

1. In the **Identifiers** section, click **Add another Identifier**
2. Select **Type** — **IGSN** or **DOI**. These are the only two; the identifier vocabulary
   for samples does not include a lab barcode or a generic "other" type, and it is a different
   vocabulary from the one used for people, organisations and projects
3. Enter **Value** (the identifier string)
4. Repeat for additional identifiers

**Sample identifier types**:

- **IGSN**: The International Generic Sample Number. Validated as any DataCite DOI
  (`10.NNNN/…`, case-insensitive) or the legacy `10273/…` handle — IGSN allocation moved to
  DataCite in 2023 and there is no longer a single prefix or suffix pattern to check against
- **DOI**: A Digital Object Identifier, for portals that mint DOIs for specimens directly

Two normalisation rules apply to every identifier value, sample or otherwise:

- A common display prefix — `https://doi.org/`, `http://doi.org/`, `https://igsn.org/`,
  `hdl.handle.net/`, `doi:`, `igsn:` — is stripped before the value is stored, so pasting an
  IGSN as a full resolvable URL and pasting its bare identifier both store the same value.
- An identifier value must be unique across **every** record type that carries identifiers —
  projects, datasets, samples and measurements — not only within samples. The same value cannot
  identify two different records, whatever kind they are.

#### Contributors

Track who collected, analyzed, or owns samples:

1. In the **Contributors** section, click **Add another Contributor**
2. Select **Contributor** (user or contact)
3. Select one or more **Roles**. The sample-specific roles are **Collector**, **Preparer**,
   **Archivist**, **Destroyer** and **Restorer** - but the field is not scoped to those: it
   lists every role in the framework's shared roles vocabulary, including ones meant for a
   project, dataset or measurement contribution. Roles are this controlled vocabulary, not free
   text - a role from outside it entirely is refused when the contribution is saved.
4. Optionally set **Order** for display ordering
5. Repeat for additional contributors

### Sample Relationships

Track provenance and relationships between samples:

1. In the **Relationships (as source)** section, click **Add another Relationship**
2. Select **Target** sample (the sample this one came from)
3. Select **Type** — `child_of` is the only type the vocabulary offers today
4. Repeat for additional relationships

There is currently one relationship type, `child_of`, and the relationship record carries no
description field to explain it. A sample cannot be related to itself, the reverse of an
existing link cannot also be recorded, and the same link cannot be saved twice — all three are
refused however the relationship is created, not only when a form validates it.

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

Filter by sample status. Status describes physical custody — where a specimen is, not what has
been done with its data — and it is a fixed, locally-declared vocabulary rather than one fetched
from a third party:

- **Available**: The specimen is accessible and not currently checked out, in storage, or
  destroyed
- **In Use**: The specimen is currently checked out or otherwise in active use
- **Stored**: The specimen is held in long-term storage
- **Destroyed**: The specimen has been consumed, destroyed, or is otherwise no longer physically
  available. This is not a terminal state — a specimen recorded as destroyed can be moved back
  to any other status, because a mistaken "destroyed" entry must be correctable
- **Unknown**: The specimen's current custody status is not known — this is what a sample reads
  as when nobody has set one

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
3. Add/update/remove metadata using inline forms
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

- Shows the sample this one is recorded as a child of
- E.g., "Section-A is child_of Core-001"

**Relationships (as target)**:

- Shows the samples recorded as children of this one
- E.g., "Core-001 is the parent of Section-A"

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

- Set to **Available** when the specimen enters the lab and is not otherwise occupied
- Change to **In Use** while it is checked out or being worked on
- Use **Stored** for long-term storage
- Update to **Destroyed** if the specimen no longer exists — and move it back to any other
  status if that turns out to be wrong, since the move is never refused
- Leave as **Unknown** rather than guessing; it is the default for a reason

### Metadata Completeness

Aim for complete metadata:

- Add at least one description (Collection, at minimum)
- Record the collection date if known
- Assign a persistent identifier (IGSN or DOI) where the specimen has one
- Track contributors (collector, analyst)

### Relationship Documentation

When adding relationships:

- `child_of` is the only relationship type today; there is nowhere to record why one sample
  came from another beyond the link itself
- Create relationships from child to parent — `source` is the child, `target` is the parent
- Check both the source and target sides after saving to verify the direction is what you meant

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

A right granted directly on one sample (through the admin's **Object permissions** section, or
programmatically) holds independently of any dataset-level grant. If you are writing code that
grants sample permissions rather than using the admin, see
[Managing Users and Permissions](managing_users_and_permissions.md) — samples are polymorphic,
and granting or checking their permissions needs FairDM's own helpers rather than django-guardian's
directly.

## See Also

- [Managing Projects](managing_projects.md) - Parent project management
- [Adjusting Dataset Access](adjusting_dataset_access.md) - Permission management
- [Managing Users and Permissions](managing_users_and_permissions.md) - User access control
- [Developer Guide: Custom Samples](../portal-development/models/custom-samples.md) - For developers creating new sample types
