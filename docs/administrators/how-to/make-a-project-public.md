# How to make a project public

A public project opens for everyone, and its public datasets can be found in the portal. Make a project public in the administration interface when the project's own managers cannot, for example when nobody who manages it can sign in.

## Before you start

You need the Data Curator role or be a superuser, so that you can change projects in the administration interface. See [Portal roles](../reference/portal-roles.md).

A person who manages the project can do this themselves, and it is the usual route. See [Edit details](../../users/projects/edit-details.md).

## Steps

1. Open the administration interface. See [Reaching the administration interface](../reference/portal-roles.md#reaching-the-administration-interface).
2. Under **Project**, choose **Projects**.
3. Find the project with the search box and choose its name.
4. Open the **Access & Visibility** section. It is collapsed until you select its heading.
5. Set **Visibility** to **Public**.
6. Choose **Save**.

## The result

The project's page opens for everyone, and the project appears in the portal's list of projects. The project's status is unchanged.

Its datasets keep their own visibility. A private dataset stays closed, and the samples and measurements of a public dataset stay hidden until the dataset is published. See [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md).

The administration interface has no bulk action for visibility, so a project is made public one at a time. To close a project again, set **Visibility** to **Private**.
