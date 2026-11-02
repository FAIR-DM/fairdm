# Projects

The Projects screen of the administration interface lists every project in the portal, private ones included, and opens each for editing. It is where you change a project's status in bulk, export projects and repair a project that its own managers cannot.

You reach it by opening the administration interface and choosing **Projects** under **Project**. You need the Data Curator role or a superuser account. The address of the administration interface is described under [Reaching the administration interface](portal-roles.md#reaching-the-administration-interface).

## The list

The list shows 50 projects to a page, with the most recently modified first. A project's name opens its form.

### Columns

| Column | What it shows | Sorts |
|---|---|---|
| Name | The project's name | Yes |
| Status | One of **Concept**, **Planning**, **In progress**, **Complete** or **Searching for collaborators** | Yes |
| Visibility | **Private** or **Public** | Yes |
| Owner | The organization that owns the project, or a dash | Yes |
| Abstract | A tick when the project has a description of the type **Abstract** | No |
| Start date | A tick when the project has a date of the type **Start Date** | No |
| Date added | When the project was added | Yes |

### Search

The search box matches part of any of these, whatever its case:

- The project's portal ID.
- The project's name.
- The name of the organization that owns it.
- The value of any of its identifiers, such as a DOI or a grant number.

### Filters

| Filter | Choices |
|---|---|
| Status | **All**, **Concept**, **Planning**, **In progress**, **Complete**, **Searching for collaborators** |
| Visibility | **All**, **Private**, **Public** |
| Date added | **Any date**, **Today**, **Past 7 days**, **This month**, **This year** |

### Actions

Choose projects with the boxes, then choose an action and **Go**. Each action runs at once and asks for no confirmation.

| Action | What it does |
|---|---|
| Mark selected projects as Concept | Sets the status to **Concept** |
| Mark selected projects as Active | Sets the status to **In progress** |
| Mark selected projects as Completed | Sets the status to **Complete** |
| Export selected projects as JSON | Downloads `projects_export.json`, in schema.org JSON-LD |
| Export selected projects as DataCite JSON | Downloads `projects_datacite.json`, in DataCite's form |
| Delete selected projects | Django's own delete action |

The three status actions change the status only and report a message such as "3 project(s) marked as Active." No action sets **Planning** or **Searching for collaborators**. A project that has public datasets cannot be deleted until those datasets are made private or deleted.

### When the list is empty

The list reads "0 projects" and shows no rows. A search or filter that matches nothing shows the same.

## The project form

The form has four sections. The last three are collapsed until you select their headings.

| Section | Fields | Notes |
|---|---|---|
| First, with no heading | **Image**, **Name**, **Status** | **Status** starts as **Concept** |
| Access & Visibility | **Owner**, **Visibility** | **Visibility** starts as **Private**. **Owner** is an organization, and can be left empty |
| Organization | **Keywords** | Controlled keywords, chosen from the vocabulary |
| Metadata | **Funding** | A list of funding references in JSON |

### Funding

**Funding** takes a list. Each entry is an object that must carry `funderName` and may carry `funderIdentifier`, `funderIdentifierType`, `awardNumber`, `awardTitle` and `awardURI`. Every value is text. `funderIdentifierType`, when given, is one of `ISNI`, `GRID`, `Crossref Funder ID`, `ROR` or `Other`. Any other key is refused.

```json
[
  {
    "funderName": "Example Research Council",
    "awardNumber": "ABC-123"
  }
]
```

### Inlines

Three sections below the fields hold the rows attached to the project. They start with no rows and each has an **Add another** link.

| Section | Layout | Rows | Types offered |
|---|---|---|---|
| Project descriptions | Stacked | Up to 6 | **Abstract**, **Introduction**, **Background**, **Objectives**, **Expected Output**, **Conclusions**, **Other** |
| Project dates | Table | Up to 10 | **Start Date**, **End Date** |
| Project identifiers | Table | Up to 5 | **DOI**, **Grant Number**, **Proposal Identifier** |

A project can carry each type once. A date takes a year (`2024`), a year and month (`2024-06`) or a full date (`2024-06-01`). An end date earlier than the start date is refused with a message that names both dates. An identifier's value has to be unique among the identifiers of every kind of record, and a value already in use is refused.

When a project has no rows in a section, the section shows only its **Add another** link.

## What you can do here

- Change the status of several projects. See [How to change the status of several projects](../how-to/change-the-status-of-several-projects.md).
- Export projects. See [How to export projects as JSON or DataCite JSON](../how-to/export-projects.md).
- Make a project public. See [How to make a project public](../how-to/make-a-project-public.md).
