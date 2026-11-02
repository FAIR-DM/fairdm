# How to change the status of several projects

A project's status says where it is in its life, from a first idea to completion. Change several at once when a group of projects has moved on together, for example when a funding round ends.

## Before you start

You need the Data Curator role or be a superuser, so that you can open **Projects** in the administration interface. See [Portal roles](../reference/portal-roles.md).

The bulk actions set three statuses: **Concept**, **Active** and **Completed**. **Active** sets the status that the project form calls **In progress**, and **Completed** sets **Complete**. The other two statuses, **Planning** and **Searching for collaborators**, are set one project at a time on the project's own page. See [Projects](../reference/projects.md).

## Steps

1. Open the administration interface. See [Reaching the administration interface](../reference/portal-roles.md#reaching-the-administration-interface).
2. Under **Project**, choose **Projects**.
3. Narrow the list to the projects you want. Use the search box or the status, visibility and date added filters.
4. Tick the box beside each project. To take every project the list matches, tick the box in the header, then choose the link that offers to select all of them, such as "Select all 120 projects".
5. In the **Action** menu, choose **Mark selected projects as Concept**, **Mark selected projects as Active** or **Mark selected projects as Completed**.
6. Choose **Go**.

## The result

The action runs at once, with no confirmation page. The list reloads with a message such as "3 project(s) marked as Active."

Only the status changes. The action does not change a project's visibility, and it does not change its **Last modified** date. A project that already had the status is counted too.

The action keeps no record of the statuses it replaced. Note them before you run it, because a project that was **Planning** or **Searching for collaborators** can only be set back on its own page.
