# Managing Users and Permissions

```{admonition} You are here
:class: tip
**Admin Guide** → Managing Users and Permissions

This page covers user and permission management for portal administrators. If you landed here from a search, start with the [Admin Guide overview](index.md) to understand the admin role and core entities.
```

As a portal administrator, you control who can access and modify data in your FairDM portal. FairDM uses Django's built-in permissions system combined with [django-guardian](https://django-guardian.readthedocs.io/) for object-level permissions, allowing you to grant fine-grained access control at the project and dataset level.

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

FairDM includes pre-configured user groups that define common roles for research portals:

- **Portal Admin**: Full control over portal configuration and user management
- **Database Admin**: Can view, edit, create, or delete any research data objects
- **Site Content**: Can modify general site content and pages
- **Literature Manager**: Can add, edit, or delete literature entries
- **Reviewer**: Can review datasets for quality control purposes

You can assign users to groups through the Django admin interface.

## Object-Level Permissions

### Project and Dataset Access

FairDM uses object-level permissions to control access to individual projects and datasets. This allows you to:

- Grant specific users or groups access to view or edit a particular dataset
- Restrict sensitive datasets to authorized collaborators only
- Enable public read access while restricting editing to project members

### Permission Types

For each project or dataset, you can assign:

- **View permission**: User can see the object and its metadata
- **Change permission**: User can edit the object and its metadata
- **Delete permission**: User can remove the object (use carefully)
- **Add permission**: User can create new child objects (e.g., samples within a dataset)

### Samples, Measurements and Other Polymorphic Records

Samples and measurements are polymorphic — a `RockSample` is stored as its own database row but
the rights that govern it (`sample.view_sample`, `sample.change_sample`, and so on) are declared
on the shared `Sample` record, not on `RockSample` itself. The admin's own **Object permissions**
section on a sample or measurement page handles this correctly. Custom code that grants or checks
these rights does not, if it calls django-guardian directly:

```python
# Wrong: files the grant under RockSample's own content type, where
# sample.change_sample is never looked for
from guardian.shortcuts import assign_perm
assign_perm("change_sample", user, rock_sample)

# Right: normalises rock_sample to the record that actually owns the permission
from fairdm.core.utils import assign_perm
assign_perm("change_sample", user, rock_sample)
```

`fairdm.core.utils` provides `assign_perm`, `remove_perm`, `get_perms` and
`get_objects_for_user` as drop-in replacements for the same-named guardian functions. Use them
whenever your portal's own code — a management command, a signal receiver, a data migration —
grants or checks a permission on a sample, a measurement, or a contributor (`Organization` and
`Person` are polymorphic too). They are safe to use against a plain, non-polymorphic record as
well, since they only normalise the object when the permission being checked actually needs it.

## Example: Granting Access to a Dataset

To grant a user access to a specific dataset:

1. Navigate to the dataset's detail page in the admin interface
2. Scroll to the **Object permissions** section
3. Click **Add user permissions** or **Add group permissions**
4. Select the user or group
5. Check the appropriate permissions (e.g., "Can view dataset", "Can change dataset")
6. Click **Save**

The user will now have the specified access to that dataset.

## Example: Restricting Dataset Access

By default, datasets may be visible to all authenticated users depending on your portal configuration. To restrict a dataset:

1. Go to the dataset in the admin interface
2. In the **Object permissions** section, review who currently has access
3. Remove permissions for "All users" or specific users/groups as needed
4. Add permissions only for authorized users or groups
5. Click **Save**

```{seealso}
For a complete walkthrough of adjusting dataset access, see [Adjusting Dataset Access](adjusting_dataset_access.md).
```

## Best Practices

- **Use groups over individual permissions**: Assign users to groups (e.g., "Project A Team") and grant permissions to the group rather than individual users. This makes permission management scalable.
- **Review permissions regularly**: Periodically audit who has access to sensitive datasets, especially when team members leave or change roles.
- **Enable public read access thoughtfully**: For FAIR compliance, you may want to make datasets publicly readable once they're published, while keeping editing restricted to the research team.
- **Document your permission policies**: Maintain clear internal documentation about who should have access to what, especially for multi-project portals.

## Troubleshooting

**User can't see a dataset they should have access to:**

- Verify the user is assigned the correct permissions in the admin interface
- Check if the dataset itself has visibility restrictions (e.g., marked as private)
- Ensure the user is logged in and their account is active

**User can edit data they shouldn't have access to:**

- Review object-level permissions for the dataset or project
- Check if the user is in a group with overly broad permissions (e.g., Database Admin)
- Remove unnecessary permissions and document the access policy

```{note}
For advanced permission scenarios, consult the [django-guardian documentation](https://django-guardian.readthedocs.io/) and consider reaching out to the FairDM community for guidance.
```
