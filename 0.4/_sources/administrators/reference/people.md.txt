# People

The people screens of the administration interface list, add and change the people a portal knows about: accounts that sign in, profiles waiting to be claimed and profiles made only for credit. This page describes each part of the screens as FairDM configures them. It does not cover the portal's own profile pages, which are in the [user guide](../../users/account/your-profile.md).

You reach the screens from the administration index. Open **Community** and select **Users**. The administration interface names the model by Django's word for it, so the screens say "user" where this page says "person".

## Who can open it

A person needs the permission to view or change people. Of the four shipped portal roles, Portal Administrator and Community Manager hold it. Adding a person needs `contributors.add_person` and deleting one needs `contributors.delete_person`. No shipped role holds either, so by default only a superuser adds or deletes people.

A person who is not a superuser does not see the **Password**, **Staff status** and **Superuser status** fields, so the permission to change people is not a route to a superuser account. The **Groups** field, which gives a portal role, shows only to a person who can view groups. The Portal Administrator role can.

## The list

The list is ordered by last name. Its first column is a tick box for the actions.

### Columns

| Column | Shows |
|---|---|
| First name | The given name. |
| Last name | The family name. |
| Email | The email address, empty for a ghost. |
| Staff status | Whether the person has the staff flag. |
| Account state | **Ghost**, **Invited**, **Claimed** or **Inactive**, worked out from the active flag, the claimed flag and the email address. |
| Impersonate user | A button from django-hijack that signs you in as the person, for those allowed to use it. |

### Search

The search box matches against the email address, the display name and the public identifier (`uuid`).

### Filters

The filters are on the right of the list.

| Filter | Options |
|---|---|
| Claimed Status | **Claimed** shows active people who have claimed their account. **Unclaimed** shows everyone else, which is every inactive, invited and ghost person. |
| By staff status | **Yes** or **No**. |
| By superuser status | **Yes** or **No**. |
| By active | **Yes** or **No**. |
| By groups | One option for each group, which is each portal role. |
| By affiliations | One option for each affiliation. |

### Buttons above the list

- **Add user** opens the add form.
- **Import** loads people from a spreadsheet. Every row is applied without a confirmation step.
- **Export** downloads people as a file.

The import reads these columns: `uuid`, `name`, `first_name`, `last_name`, `orcid`, `ror_id` and `affiliation`. A row with an `orcid` finds or creates the person from ORCID. A row naming an affiliation links the person to that organization as a **Member** and creates the organization when it does not exist, using the `ror_id` when given. A row that matches a claimed person is refused, so an import cannot overwrite an account in use. The import pauses 1.5 seconds after each row to stay under the registries' limits. The `uuid` identifies a row and is never written.

### Actions

The **Action** menu offers these. Tick the people first.

| Action | Does |
|---|---|
| Delete selected users | Deletes the people. It appears only to someone who may delete people. |
| Merge selected Person into another | Opens the merge page for the one person ticked. Selecting none or several is refused. It appears only to someone who can change people. |

### When the list is empty

With no matching person the list has no rows. Clear the search and the filters.

## The add form

The add form has one section without a heading.

| Field | Holds |
|---|---|
| First name and Last name | The two parts of the name. The display name is built from them when you save. |
| Email address | The address. |
| Password and Password confirmation | The password, typed twice. |

The form also shows the inline sections listed below.

## The change form

### Sections

| Section | Fields |
|---|---|
| Basic info | Profile image, First name, Last name, Preferred name, Email address, Profile, UUID, Last synced, Date added, Last modified. |
| Account | Password, Active, Staff status, Superuser status. |
| Permissions | Groups. |

UUID, Last synced, Date added and Last modified are read-only. **Preferred name** is the display name, and **Profile** is the biography. **Active** is the flag that deactivates an account. **Groups** is where a person is given or loses a portal role.

### Inline sections

| Section | Rows hold |
|---|---|
| Email addresses | Email address, Primary, Verified. These are the addresses held for sign-in. |
| Affiliations | Organization, Type, Primary organization. |
| Identifiers | Type, Identifier. For example an ORCID iD. An identifier value is unique across the portal, and a person holds one of each type. |

Each inline starts with no empty row. Use its **Add another** link. Adding an identifier queues a background sync with the registry.

### Possible Duplicate Persons

A panel at the foot of the form lists other people whose display name scores 85 percent or more against this person's, ignoring the order of the words. It appears only when there are such people. Each row shows the name, the email address, the similarity and two buttons.

- **Merge** opens the merge page for the person whose form you are on.
- **Dismiss** hides that suggestion for the rest of your session.

The panel only suggests. Nothing is merged or claimed because two names look alike.

### The merge page

The page is titled **Merge Person** and warns that the merge cannot be undone. It has one field, **Merge into**, which finds people by name, alternative name or ORCID iD and never offers a superuser. **Confirm Merge** runs the merge and **Cancel** returns to the list. A table under the form counts the contributions, identifiers and affiliations that will move.

## What you can do here

- Add a person. See [How to add a person in the administration interface](../how-to/add-a-person-in-the-admin.md).
- Merge two records. See [How to merge two person records](../how-to/merge-two-person-records.md).
- Reactivate a deactivated profile. See [How to reactivate a deactivated profile](../how-to/reactivate-a-deactivated-profile.md).
- Correct an unclaimed profile. See [How to correct a profile that nobody has claimed](../how-to/correct-an-unclaimed-profile.md).
- Import people from ORCID with a script. See [How to import people from a list of ORCID iDs](../../developers/how-to/import-people-from-orcid.md).
- Give a person a portal role. See [Portal roles](portal-roles.md).
