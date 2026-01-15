# Managing Projects

The Django admin interface provides comprehensive tools for managing research projects, including search, filtering, bulk operations, and inline metadata editing.

## Accessing Project Administration

1. Log in to the admin interface at `/admin/` (or your configured `ADMIN_URL`)
2. Navigate to **Projects** → **Projects** in the sidebar
3. You'll see the project list view with search and filter options

## Searching Projects

Use the search box at the top of the project list to find projects by:

- **Project name**: Search by full or partial project name
- **UUID**: Find a specific project by its unique identifier
- **Owner**: Search by the organization name that owns the project

**Example searches:**

- `"Climate Research"` - finds all projects with "Climate Research" in the name
- `"abc123"` - finds project with UUID starting with "abc123"
- `"University Lab"` - finds projects owned by organizations with "University Lab" in the name

## Filtering Projects

Use the filter panel on the right side to narrow down the project list:

- **Status**: Filter by Concept (draft), Active (ongoing), or Completed
- **Visibility**: Show only Public or Private projects
- **Date added**: Filter by when projects were created (Today, Past 7 days, This month, This year)

**Pro tip**: Combine filters to find specific project types, like "Active projects added this month"

## Editing Projects

### Quick Editing

Click on a project name in the list to open the detail/edit form.

### Form Organization

The project edit form is organized into collapsible sections:

1. **Basic Information** (always visible)
   - Project image
   - Project name
   - Status (Concept/Active/Completed)

2. **Access & Visibility** (collapsible)
   - Owner organization
   - Visibility (Public/Private)

3. **Organization** (collapsible)
   - Keywords for project discovery

4. **Metadata** (collapsible)
   - Funding information (JSON format)

Click section headers to expand/collapse them.

## Inline Metadata Editing

While editing a project, you can manage related metadata without leaving the page:

### Descriptions

Add multiple descriptions with different types:

- **Abstract**: Brief project summary
- **Methods**: Research methodology
- **Technical Info**: Implementation details
- And more...

**To add a description:**

1. Scroll to the "Project Descriptions" section
2. Fill in the Type and Value fields
3. Click "Add another Project Description" for additional entries

### Dates

Add important project dates:

- **Start Date**: Project beginning
- **End Date**: Project conclusion
- **Collection Period**: Data collection timeframe

### Identifiers

Add external identifiers:

- **DOI**: Digital Object Identifier
- **Grant Number**: Funding grant ID
- **ORCID**: Researcher identifier
- **URL**: Related web resources

## Bulk Operations

Select multiple projects using the checkboxes, then choose an action from the dropdown:

### Status Changes

- **Mark selected projects as Concept**: Set projects to draft status
- **Mark selected projects as Active**: Activate projects for active research
- **Mark selected projects as Completed**: Mark projects as finished

**Steps:**

1. Check boxes next to projects you want to update
2. Select the status action from the "Action" dropdown
3. Click "Go"
4. Confirm the operation

The system will show how many projects were updated.

### Export Operations

Export project data in different formats:

#### Export as JSON

**Use case**: Backup, data transfer, integration with other systems

Exports each project with:

- UUID
- Name
- Status
- Visibility
- Created and modified timestamps

**Steps:**

1. Select projects to export
2. Choose "Export selected projects as JSON"
3. Click "Go"
4. A `projects_export.json` file will download

#### Export as DataCite JSON

**Use case**: Publish project metadata to DataCite DOI registry

Exports projects in DataCite format with:

- Project ID (UUID)
- Title
- Publication year
- Resource type (Project)

**Steps:**

1. Select projects to export
2. Choose "Export selected projects as DataCite JSON"
3. Click "Go"
4. A `projects_datacite.json` file will download

## Best Practices

### Search Tips

- **Be specific**: Use full project names for exact matches
- **Use partial names**: Search "Climate" to find all climate-related projects
- **Combine with filters**: Search + filter for powerful queries

### Status Workflow

Follow this recommended project lifecycle:

1. **Concept**: Planning phase, internal only (Private)
2. **Active**: Ongoing research, can be Public or Private
3. **Completed**: Finished projects, typically Public

### Bulk Operations Safety

- **Double-check selections**: Review selected projects before bulk actions
- **Start small**: Test bulk operations on a few projects first
- **Use filters first**: Filter to your target set, then "Select all"

### Metadata Organization

- **Use descriptions wisely**: Don't duplicate information across description types
- **Date precision**: Add start/end dates for projects with defined timeframes
- **Identifiers matter**: Add DOIs for published projects to improve discoverability

## Common Tasks

### Making a Project Public

1. Open the project
2. Expand "Access & Visibility" section
3. Change Visibility to "Public"
4. Save

### Bulk Activating Projects

1. Filter by Status = "Concept"
2. Select all concept projects
3. Choose "Mark selected projects as Active"
4. Confirm

### Finding Recent Projects

1. Use "Date added" filter → "Past 7 days"
2. Review new projects
3. Update status as needed

### Exporting for Backup

1. Click "Select all" checkbox (top left)
2. Choose "Export selected projects as JSON"
3. Download and store securely

## Troubleshooting

**Search returns no results:**

- Check spelling
- Try partial words
- Clear filters and try again

**Can't edit a project:**

- Verify you have admin permissions
- Check if project has protection rules

**Bulk action doesn't work:**

- Ensure projects are selected (checkboxes checked)
- Try with fewer projects if timing out
- Check admin permissions

## See Also

- [Managing Users and Permissions](managing_users_and_permissions.md)
- [Adjusting Dataset Access](adjusting_dataset_access.md)
- [Reviewing Content](reviewing_content.md)
