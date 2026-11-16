# How to assign a portal role

A portal role gives a person rights across the whole portal, such as looking after every record or every account. Assign one when someone takes on that job, and take it away when they leave it.

## Before you start

You need to hold the Portal Administrator role, or be a superuser. The **Groups** field is hidden from anyone who cannot view groups, and none of the other roles can.

## Steps

1. Open the administration interface. See [Reaching the administration interface](../reference/portal-roles.md#reaching-the-administration-interface).
2. Under **Community**, choose **Users**.
3. Find the person. The search box matches an email address, a name or a portal ID.
4. Choose the person's name to open their page.
5. In the **Permissions** section, select the **Groups** field and type the name of the role: **Portal Administrator**, **Data Curator**, **Community Manager** or **Developer**. Choose it from the list.
6. Choose **Save**.

To take a role away, remove it from the **Groups** field in the same way and save.

## The result

The person holds the role from their next request. A person who holds a role that carries rights can sign in to the administration interface. The role also lists them on the portal's [Team](../../users/community/team.md) page, unless their account is deactivated.

To see who holds a role, open the **Users** list and filter it by **groups**.

Assign a role on the person, not by editing the role. The Portal Administrator role holds no right to change a group. Changes made to a role's permissions are put back the next time the database is brought up to date. What each role holds is listed under [Portal roles](../reference/portal-roles.md).
