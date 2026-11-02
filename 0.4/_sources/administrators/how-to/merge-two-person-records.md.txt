# How to merge two person records

A merge moves everything one person record holds onto another and deletes the first. You do this when the same researcher appears twice, for example as an imported profile and as a registered account.

Only people who hold the permission to change people see **Merge selected Person into another**. The Portal Administrator and Community Manager roles hold it, and so does a superuser.

```{warning}
A merge cannot be undone. The record you merge away is deleted, and so are the sessions it held. Check which record is which before you confirm.
```

## Before you start

Decide which record survives. Keep the one the person signs in with, because the survivor is marked claimed and active when the merge finishes. Merging into an invited or ghost profile marks it claimed even though nobody has signed in to it.

## Steps

1. In the administration interface, open **Community** and select **Users**.

2. Tick the box beside the record to merge away. This is the one that will be deleted. Tick exactly one box.

3. In the **Action** menu, choose **Merge selected Person into another** and select **Go**.

4. On the **Merge Person** page, search for the record to keep in **Merge into**. The field finds people by name, alternative name or ORCID iD. It does not search email addresses and it never offers a superuser account. Choosing the person you are merging away is refused.

5. Check the table at the foot of the page. It counts the contributions, identifiers and affiliations that will move.

6. Select **Confirm Merge**.

To start from a likely duplicate instead, open the person's change form and look for the **Possible Duplicate Persons** panel at the foot. Select **Merge** beside a name to open the same page for the person whose form you are on. You still choose the record to keep in **Merge into**.

## The result

The administration interface opens the surviving record and confirms the merge. The surviving record has taken over:

- The contributions of the discarded record. Where both people are credited on the same record, one credit remains, at the higher of the two levels, with the survivor's own organization.
- The identifiers, unless the survivor already holds one of the same type or the same value is held elsewhere. Those are dropped.
- The affiliations, unless the survivor already has an affiliation with that organization.
- The confirmed email addresses and the linked sign-in accounts, such as ORCID.
- The permissions stored on objects other than projects, datasets, samples and measurements.
- The profile text and the photo, only where the survivor has none.

Nothing else is copied. The names, links, alternative names, languages and email address on the survivor stay as they were.

The merge is recorded in the claiming audit log with the method **Admin-Initiated Merge**. Because the discarded record no longer exists, its **Source person** shows no name. See [Claiming audit logs](../reference/claiming-audit-log.md).

Why a merge is limited to a role rather than to superusers is in [ADR 0021](../../adr/0021-claims-and-merges-belong-to-a-named-role.md). What a merge means for a profile is in [How a profile is claimed](../../explanation/how-a-profile-is-claimed.md).
