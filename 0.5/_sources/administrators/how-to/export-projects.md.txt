# How to export projects as JSON or DataCite JSON

Exporting writes the selected projects to a file you download. Choose the JSON export to give a project's description and people to a system that reads schema.org, and the DataCite export to prepare a project's metadata for a DataCite record.

## Before you start

You need the Data Curator role or be a superuser, so that you can open **Projects** in the administration interface. See [Portal roles](../reference/portal-roles.md).

The export covers every project you select, private ones included, and it names the people credited on each. Keep the file somewhere only the right people can read it.

## Steps

1. Open the administration interface. See [Reaching the administration interface](../reference/portal-roles.md#reaching-the-administration-interface).
2. Under **Project**, choose **Projects**.
3. Tick the box beside each project to export. To take every project, tick the box in the header and choose the link that offers to select all of them.
4. In the **Action** menu, choose **Export selected projects as JSON** or **Export selected projects as DataCite JSON**.
5. Choose **Go**. The browser downloads the file.

## The result

The JSON export downloads `projects_export.json`. It holds one schema.org JSON-LD entry for each project:

- The type `ResearchProject`.
- The project's name.
- The text of its abstract description, when it has one.
- The people credited, without their email addresses.

The DataCite export downloads `projects_datacite.json`. It holds one DataCite entry for each project:

- The title, with the resource type set to "Project".
- Every description. An abstract keeps its type and every other description is given the type "Other" with its own type beside it.
- Every date, as a date of type "Other" with the date's own type beside it.
- A DOI as the primary identifier, and every other identifier as an alternate identifier.
- The people credited. Those with the role Creator become creators and everyone else becomes a contributor.
- The funding references, when the project has any.

Parts a project does not have are left out. The DataCite entry carries no publisher and no publication year, so a registration needs those added elsewhere.

The fields of each project are described on [Projects](../reference/projects.md).
