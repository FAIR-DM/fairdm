# Managing Users and Permissions

```{admonition} You are here
:class: tip
**Admin Guide** → Managing Users and Permissions

This page covers user and permission management for portal administrators. If you landed here from a search, start with the [Admin Guide overview](index.md) to understand the admin role and core entities.
```

As a portal administrator, you control who can access and modify data in your FairDM portal. Two things decide it: the portal roles a person holds, which apply across the whole portal, and the level a person holds on each project, dataset, sample or measurement they are listed on as a contributor. Both are explained below. FairDM still uses [django-guardian](https://django-guardian.readthedocs.io/) for stored permissions on organizations and on any model your own portal defines.

## User Management Basics

### Creating User Accounts

Users can create their own accounts if self-registration is enabled in your portal settings. As an administrator, you can also create accounts manually through the Django admin interface:

1. Navigate to `/admin/` and log in with your administrator credentials
2. Go to **Users** under the authentication section
3. Click **Add User** and provide:
   - Username
   - Password (users can change this after first login)
   - Email address
4. Click **Save**

### User Roles

FairDM ships four portal roles (Portal Administrator, Data Curator, Community Manager and
Developer), declared in code and installed into your portal automatically. See
[Portal roles](roles.md) for what each one holds. You assign a role to a person on their own
record's **Groups** field, through the Django admin interface.

## Access to a record

### Levels

Access to a project, dataset, sample or measurement is a level held by a person listed as a
contributor on it: view, edit or manage. Each level includes the one before it.

| Level | What the person may do |
|---|---|
| View | Open the record and every page of it, even while it is private. |
| Edit | Also change the record and the data in it. |
| Manage | Also change its contributors and their levels, change its visibility and delete it. |

A level on a project applies to every dataset in it and to the samples and measurements in them,
and a level on a dataset applies to its samples and measurements. Where a person holds a level on
a record and another from a record above, the higher applies. A record's visibility decides who
may open it without holding a level: a public record opens to everyone, and a private one only to
people who hold a level on it, directly or from above, and to holders of a portal role whose
rights cover it.

People who manage a record set levels themselves, on its **Contributors** tab, and nobody needs to
ask an administrator. See [Crediting a record](../user-guide/crediting-a-record.md) for how.
An administrator does not grant access to a record in the administration interface: a permission
stored for a project, dataset, sample or measurement there, for a person or for a group, grants
nothing. Membership of an organization, or owning one, gives no access to a record either.

### How levels and portal roles work together

A portal role applies to every record of a kind, whoever is listed on it. The Data Curator role
holds the right to view and change every project, dataset, sample and measurement, so a Data
Curator opens and edits any record and manages its contributors without being listed. Levels apply
record by record. A person who holds both has everything either gives them. Portal roles never
change what a level allows, and a level never gives a person any right over other records. See
[Portal roles](roles.md).

### Samples, measurements and other polymorphic records

Contributors, and models your own portal defines, can still carry permissions stored through
django-guardian. If your portal's own code grants or checks one on a polymorphic record such as an
`Organization`, use the helpers in `fairdm.core.utils` rather than guardian's own functions:

```python
# Wrong: files the grant under the subclass's own content type, where
# the permission declared on the base is never looked for
from guardian.shortcuts import assign_perm
assign_perm("change_contributor", user, organization)

# Right: normalises the record to the one that actually owns the permission
from fairdm.core.utils import assign_perm
assign_perm("change_contributor", user, organization)
```

`fairdm.core.utils` provides `assign_perm`, `remove_perm`, `get_perms` and `get_objects_for_user`
as drop-in replacements for the same-named guardian functions. They are safe to use against a
plain, non-polymorphic record as well, since they only normalise the object when the permission
being checked actually needs it. Do not use them to give a person access to a project, dataset,
sample or measurement: list the person as a contributor at the level they need instead.

## Upgrading from stored record permissions

Earlier versions of FairDM gave access to a record through permissions stored in django-guardian,
granted when a project or dataset was created or by hand in the administration interface. Bringing
a portal up to date converts them once, so that nobody who could do something with a record can
do less afterwards:

- Each stored permission, for a person or for a group, on a project, dataset, sample or
  measurement, of any registered sample or measurement type, is mapped to a level. Permissions to
  view map to view, to add or change the record or its data, import data or edit its metadata map
  to edit, and to delete it, change its settings, publish it or change its contributors map to
  manage. A person gets the highest level their permissions map to on a record.
- A person who held permissions over a record without being listed on it is now listed on it,
  with no roles. A group's permissions become a level for each person who is a member of the group
  at the time of the upgrade.
- A person already listed on a record who held no permissions over it is at the view level.
- An organization already recorded with a person's entry on a record is kept as the organization
  they are credited from, and is listed among the record's organizations. An entry that had none
  is left with none.
- The stored permissions that were converted are then deleted. Permissions stored for an
  organization or for a model your portal defines are left alone.

The upgrade runs with the rest of `manage.py migrate`, and runs without trouble on a portal that
has no stored permissions. Reversing it restores nothing: migrating `contributors` back to
`0022` leaves the levels it set and does not bring back the permissions it deleted. Migrating back
to `0021` also removes the `level` column, and every level with it. Back up the database before the
upgrade if you may need to return to an earlier version.

One thing is stricter than before. Someone who held only the right to change a dataset could delete
its samples. Deleting a sample or a measurement now needs the manage level on it, or on its dataset
or project. Anyone who relied on that, such as data-entry staff, needs the manage level on the
dataset.

## Example: Letting a colleague into a dataset

Ask someone who manages the dataset to open its **Contributors** tab and add your colleague. They
can then open the dataset. To let them change it, the same person edits their entry and chooses
the **Edit** level. To close the dataset to them again, they remove the entry.

## Example: Restricting a dataset

Set the dataset's visibility to private on its edit details page, reached from the dataset's
**Manage** menu, which needs the manage level or a portal role that holds the right to change
datasets. Then only the people listed on it, or on its
project, and the holders of such a role, can open it. See [Adjusting dataset
access](adjusting_dataset_access.md).

## Best Practices

- **Give the lowest level that does the job**: View for readers, edit for people who change the data, manage for the few who decide who else is let in.
- **Give a project's level to the team that runs it**: A level on a project reaches every dataset in it, so one entry covers a whole team's work.
- **Review who is listed regularly**: Periodically read the Contributors tab of sensitive records, especially when team members leave or change roles.
- **Enable public read access thoughtfully**: For FAIR compliance, you may want to make datasets public once they are published, while keeping editing restricted to the research team.
- **Document your access policies**: Maintain clear internal documentation about who should have access to what, especially for multi-project portals.

## Troubleshooting

**User can't see a dataset they should have access to:**

- Check that the person is listed on the dataset, or on its project, on the Contributors tab, and that they hold a level there
- Check if the dataset itself has visibility restrictions (e.g., marked as private)
- Ensure the user is logged in and their account is active. A level set for a person without an active account takes effect when the account is active

**User can edit data they shouldn't have access to:**

- Read the Contributors tab of the dataset and of its project for the level the person holds
- Check if the user holds the Data Curator role, which reaches every project, dataset, sample
  and measurement in the portal by design (see [Portal roles](roles.md))
- Lower or remove their entry, and document the access policy

```{note}
For permissions stored on organizations or on models your portal defines, consult the [django-guardian documentation](https://django-guardian.readthedocs.io/).
```
