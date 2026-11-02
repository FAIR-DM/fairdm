# How to find why a user can edit data they should not

When someone changes or deletes a record they were not meant to, the portal has given them the right in one of a few ways. Start from what they did, find the heading below that matches it, and follow the checks under it.

## Before you start

You need to open the record's **Contributors** tab, which a Data Curator can do for any record. To read people and their roles you need the Portal Administrator or Community Manager role. A superuser can do all of it. See [Portal roles](../reference/portal-roles.md).

## A person changes a record they are not credited on

Three things give a right over a record to someone who is not listed on it. Check them in this order.

1. Open the record in the portal and choose its **Contributors** tab. Under **People**, look for the person. Then look at the card headed "Access from the" record above. It lists people who hold a level only because of a project or dataset above this record. A level on a project reaches every dataset in it and everything in those datasets. If the person is there, the right comes from the record above, and that is where you change it.
2. Open the administration interface and choose **Users** under **Community**. See [Reaching the administration interface](../reference/portal-roles.md#reaching-the-administration-interface). Search for the person and open their page. In the **Permissions** section, read **Groups**. A person in **Data Curator** can view, change and delete every project, dataset, sample and measurement, and manage their contributors, without being listed. That is what the role is for.
3. In the **Account** section of the same page, read **Superuser status**. A superuser holds every permission, and a superuser cannot be credited on a record, so the Contributors tab never shows one.

To remove the right:

- For a level, choose **Edit** beside the person on the Contributors tab of the record that holds it and pick a lower level, or choose **Remove**.
- For the Data Curator role, remove it from **Groups** as described in [How to assign a portal role](assign-a-portal-role.md).

The portal refuses to lower or remove the last person who counts as able to manage a record. Give someone else **Can manage** first.

## A person deletes a sample or measurement

Deleting a record needs the **Can manage** level on it, or on the dataset or project above it, or the Data Curator role. The **Can edit** level is not enough.

Check the person's level as above. Lower it to **Can edit** if they should change records but not delete them.

## A person changes records in the administration interface

The administration interface asks a different question from the portal's pages. It asks whether the person holds the permission for the whole kind of record, such as changing samples, not a level on this record.

1. Open the person's page under **Users** and read **Groups**.
2. For each group that is not one of the four portal roles, open it under **Groups** and read its permissions. A permission to change or delete a kind of record applies to every record of that kind in the administration interface.
3. Edit the group to remove the permission, or take the person out of the group. Only a superuser can edit a group, because the Portal Administrator role holds no right to change one.

A permission given through a group of your own does not turn into a right over a particular record on the portal's pages. There, a level still decides, and a person who holds only such a permission is refused the editing pages of a private record.

The **Contributors** section on a sample's or a measurement's page in the administration interface sets levels too. A row there with a **Level** gives that person the level on the record. If a person turns out to hold a level nobody set on the Contributors tab, look at that section.

## Stored permissions are not the cause

A permission stored for a person or a group against a project, dataset, sample or measurement grants nothing. You will not find the cause there. The reasoning is in [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md).
