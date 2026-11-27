# Organizations

The organization screens of the administration interface list, add and change the organizations a portal knows about: institutions, groups and companies that people belong to and that records are credited from. This page describes each part of the screens as FairDM configures them. It does not cover the portal's own organization pages, which are in the [user guide](../../users/account/organization.md).

You reach the screens from the administration index. Open **Community** and select **Organizations**.

## Who can open it

A person needs the permission to view or change organizations. The Community Manager role holds both. Adding an organization needs `contributors.add_organization` and deleting one needs `contributors.delete_organization`. No shipped role holds either, so by default only a superuser adds or deletes organizations.

The actions and the member rows each have a further rule, given where they appear below.

## The list

The list is ordered by name. Its first column is a tick box for the actions.

### Columns

| Column | Shows |
|---|---|
| Name | The organization's name. |
| City | Its city, empty when unknown. |
| Country | Its country. |
| Lat | The latitude of its location. |
| Lon | The longitude of its location. |

### Search

The search box matches against the name.

### Filters

| Filter | Options |
|---|---|
| By country | One option for each country in the list. |

### Actions

The **Action** menu offers these. Tick the organizations first.

| Action | Does |
|---|---|
| Delete selected organizations | Deletes the organizations. It appears only to someone who may delete them. |
| Sync from ROR | Queues a background sync for each ticked organization that holds a ROR identifier. A message gives the count, or warns that none of them holds one. |
| Transfer Ownership | Makes the person chosen in **New owner** the owner of the one ticked organization and demotes each earlier owner to **Admin**. |

The action bar carries a **New owner** field next to the menu. The field finds people by name, alternative name or ORCID iD, and it never offers a superuser. **Transfer Ownership** is refused with a message in these cases:

- You ticked none or several organizations.
- The organization has no members.
- You do not hold the right to manage the organization. A superuser and a current owner of the organization hold it.
- You chose no new owner.
- The chosen person is not a member, has an ended or pending affiliation, has not claimed their account or is deactivated.

### When the list is empty

With no matching organization the list has no rows. Clear the search and the filter.

## The add and change forms

Both forms have the same sections.

| Section | Fields |
|---|---|
| No heading | Profile image, Preferred name, Profile, Parent organization, UUID. |
| Location | City, Country, Location. |
| Synchronisation | Last synced, Synced data, Date added, Last modified. |

UUID, Last synced, Synced data, Date added and Last modified are read-only. **Preferred name** is the organization's name, **Profile** is its description and **Parent organization** is the organization it is part of. A parent that would make the organization part of itself, or of an organization beneath it, is refused.

Once an organization holds synced data, **Preferred name**, **City** and **Country** are read-only too. **Location** stays editable. A sync can overwrite the city, country and location with the registry's values, so a correction to them belongs at the registry.

### Inline sections

| Section | Rows hold |
|---|---|
| Members | Person, Type, Primary organization. |
| Sub-organizations | Name. |

Neither inline starts with an empty row. Use its **Add another** link. A **Members** row is an affiliation, and a row for a person who is already a member is refused. Setting a row's type to **Admin** or **Owner**, or changing or deleting a row that already has one of those types, needs the right to manage the organization. A **Members** row has no date fields. Dates are on the [Affiliations](affiliations.md) screen.

The form has no identifiers section, so an identifier such as a ROR ID cannot be added here. An organization made from a ROR search already holds its ROR identifier.

## What you can do here

- Add a member. See [How to add a member to an organization](../how-to/add-a-member-to-an-organization.md).
- Hand an organization to another person. See [How to transfer ownership of an organization](../how-to/transfer-ownership-of-an-organization.md).
- Fix a sync that does not update. See [How to fix an ORCID or ROR sync that does not update](../how-to/fix-an-orcid-or-ror-sync-that-does-not-update.md).
- End a membership. See [How to end someone's affiliation](../how-to/end-someones-affiliation.md).
