# How to transfer ownership of an organization

A transfer makes one member the owner of an organization and demotes every current owner to administrator. You do this when the person who runs an organization leaves or hands the role on, and you want one owner in place of two.

## Before you start

- You must be a superuser or a current owner of the organization. Holding the permission to change organizations is not enough, so a Community Manager who does not own the organization is refused.
- The organization must have at least one member.
- The new owner must already be a member with a current affiliation of type **Member** or higher. A pending affiliation, an ended affiliation, an unclaimed account and a deactivated account are all refused.

## Steps

1. In the administration interface, open **Community** and select **Organizations**.

2. Tick the box beside the one organization to transfer. Selecting none or several is refused.

3. In the **New owner** field next to the **Action** menu, search for the new owner by name, alternative name or ORCID iD. The field does not search email addresses, and it never offers a superuser account.

4. In the **Action** menu, choose **Transfer Ownership** and select **Go**.

## The result

A success message begins "Transferred ownership of" and names the organization and the new owner. Every earlier owner holds the type **Admin**, and the chosen member holds the type **Owner**. Nothing else changes, and ended affiliations stay as they were.

If the transfer is refused, an error message gives the reason and nothing changes. The reasons are:

- You do not hold the right to manage the organization.
- The organization has no members.
- You did not choose a new owner in the **New owner** field.
- The chosen person fails one of the conditions above. The message names the one that failed.

Ownership is not stored as a permission. It follows the owner affiliation, so the previous owner loses the right the moment they are demoted. See [How contributor accounts and credits work](../../explanation/how-contributor-accounts-and-credits-work.md#ownership-is-derived-from-the-affiliation).

The screen's other action and its fields are listed in [Organizations](../reference/organizations.md).
