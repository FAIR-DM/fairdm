# Affiliations

The affiliation screens of the administration interface list, add and change the links between people and organizations. An affiliation carries a type that says whether the link is verified and what the person may do for the organization, and it can carry dates. This page describes each part of the screens as FairDM configures them. It does not explain how ownership is worked out, which is in [How contributor accounts and credits work](../../explanation/how-contributor-accounts-and-credits-work.md).

You reach the screens from the administration index. Open **Community** and select **Affiliations**. The same rows also appear as inline sections on the [People](people.md) and [Organizations](organizations.md) forms, with fewer fields.

## Who can open it

A person needs the permission to view or change affiliations. The Community Manager role holds both. Adding an affiliation needs `contributors.add_affiliation`, which no shipped role holds, so by default only a superuser adds one.

The list is narrowed for anyone who is not a superuser. It shows only the affiliations of organizations where you hold a current **Owner** affiliation. A change or a delete of any row needs the right to manage that row's organization, which a superuser and a current owner hold. A Community Manager who owns no organization therefore sees an empty list.

## Types

| Type | Value | Meaning |
|---|---|---|
| Pending | 0 | Declared and not verified. It carries no rights. |
| Member | 1 | A verified member. This is the default. |
| Admin | 2 | A member who can edit the organization's profile. |
| Owner | 3 | The member who holds the right to manage the organization. |

Setting a type to **Admin** or **Owner**, and changing or deleting a row that already has one of those types, needs the right to manage the organization. The rule applies on this screen and on both inline sections.

## The list

### Columns

| Column | Shows |
|---|---|
| Person | The person. |
| Organization | The organization. |
| Type | The type. |
| Primary organization | Whether this is the person's primary affiliation. |

### Search

The list has no search box. The **Person** and **Organization** fields of the form are search fields of their own, the person field finds people by email address, display name or public identifier, and the organization field finds organizations by name.

### Filters

| Filter | Options |
|---|---|
| By type | **Pending**, **Member**, **Admin** and **Owner**. |
| By primary organization | **Yes** or **No**. |

### Actions

The only action is **Delete selected affiliations**, and it appears only to someone who may delete affiliations. No action approves a batch of pending affiliations.

### When the list is empty

With no matching row the list has no rows. Clear the filters. A person who is not a superuser also sees no rows when they own no organization.

## The add and change forms

The forms show every field of an affiliation.

| Field | Holds |
|---|---|
| Person | The affiliated person. |
| Organization | The organization. |
| Type | One of the four types. |
| Primary organization | Whether this is the person's primary affiliation. |
| Start date | When the affiliation began. |
| End date | When it ended. Leave blank for a current affiliation. |

Both dates take a year, a year and month, or a full date. An end date ends the rights the type gave and keeps the row as history.

These rules hold on every route that saves an affiliation:

- A person has at most one affiliation with a given organization. A second is refused.
- A person has at most one primary affiliation. Saving a row as primary clears the flag on the person's other row.
- An affiliation with no end date is current. One with an end date is past.

## What you can do here

- Approve a pending affiliation. See [How to approve a pending affiliation](../how-to/approve-a-pending-affiliation.md).
- End an affiliation. See [How to end someone's affiliation](../how-to/end-someones-affiliation.md).
- Add a member. See [How to add a member to an organization](../how-to/add-a-member-to-an-organization.md).
- Hand an organization to another person. See [How to transfer ownership of an organization](../how-to/transfer-ownership-of-an-organization.md).
