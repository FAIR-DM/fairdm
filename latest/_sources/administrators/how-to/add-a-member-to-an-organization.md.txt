# How to add a member to an organization

Adding a member links an existing person to an organization through an affiliation. You do this when a person belongs to an institution and the portal should show it.

## Before you start

Your account needs the permission to add affiliations, `contributors.add_affiliation`. The four shipped portal roles do not hold it, so by default only a superuser sees the **Add another Member** link.

The person must already exist. See [How to add a person in the administration interface](add-a-person-in-the-admin.md).

Only an owner of the organization, or a superuser, can give a member the type **Admin** or **Owner**. To hand the organization to someone else, see [How to transfer ownership of an organization](transfer-ownership-of-an-organization.md).

## Steps

1. In the administration interface, open **Community** and select **Organizations**.

2. Select the organization.

3. In the **Members** section, select **Add another Member**.

4. In **Person**, choose the person from the list.

5. Leave **Type** as **Member**. The other types are **Pending**, **Admin** and **Owner**. They are described in [Affiliations](../reference/affiliations.md#types).

6. Tick **Primary organization** if this is the person's main affiliation. A person has one primary affiliation, and saving this one clears the flag on the old one.

7. Select **Save**.

## The result

The person is listed under **Members** with no end date, so the affiliation is current. It also appears in the affiliations section of the person's change form.

The form refuses a second affiliation between the same person and organization. To change an existing one, edit its row. To set when it started or ended, use the **Affiliations** screen, because the inline rows have no date fields. See [How to end someone's affiliation](end-someones-affiliation.md).

The fields of the screen are listed in [Organizations](../reference/organizations.md).
