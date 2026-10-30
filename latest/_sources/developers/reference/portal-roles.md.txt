# Portal roles in code

This page lists the classes, functions and signal receivers that declare, install, protect and read the four portal roles: `PortalRole`, `PortalRoles`, `PortalRolePermissionBackend`, the receivers that guard the role groups, the administration site that admits role holders, and `TeamView`. It does not list what each role may do, which is in [Portal roles](../../administrators/reference/portal-roles.md), or why access is divided this way, which is in [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md) and [ADR 0019](../../adr/0019-a-portal-role-is-the-unit-of-portal-wide-rights.md). To sign in as each role while you develop, see [Development accounts](development-accounts.md).

## PortalRole

`PortalRole` is a `NamedTuple` in `fairdm.portal_roles`. It describes one role.

| Field | Type | Default | What it holds |
|---|---|---|---|
| `name` | `str` | None, required | The stored name of the role's `auth.Group` |
| `label` | `str` or lazy string | None, required | The display label, translated |
| `permissions` | `tuple` of `str` | `()` | The permissions the role holds, each as `app_label.codename` |

## PortalRoles

`PortalRoles` carries the declarations and the methods that read and install them.

| Attribute | Type | What it is |
|---|---|---|
| `PORTAL_ADMINISTRATOR` | `PortalRole` | Name `Portal Administrator` |
| `DATA_CURATOR` | `PortalRole` | Name `Data Curator` |
| `COMMUNITY_MANAGER` | `PortalRole` | Name `Community Manager` |
| `DEVELOPER` | `PortalRole` | Name `Developer`, with no permissions |
| `ROLES` | `tuple` of `PortalRole` | The four roles in declaration order, which every method follows |

| Method | Returns | What it does |
|---|---|---|
| `shipped_names()` | `list` of `str` | The stored names of the four roles, in declaration order |
| `rights_carrying()` | `list` of `str` | The names of the roles that hold at least one permission. Holding any of these gives access to the administration interface. Holding only `Developer` does not |
| `is_held_by(user, role)` | `bool` | True when the user is authenticated, active and in the group named `role.name`. False for a visitor, a deactivated account and a user in another role. A superuser in no group does not hold the role. The check reads the group and never a Django permission |
| `reconcile()` | `None` | Installs the four roles. Creates each role that is missing and sets each role's permissions to exactly its declaration. Restores a permission removed by hand and removes one added by hand. Never changes who is in a role |

`reconcile()` skips a declared permission that has no database row yet, because the apps that define it may not have migrated. A later run picks it up.

```python
from fairdm.portal_roles import PortalRoles

PortalRoles.shipped_names()
# ['Portal Administrator', 'Data Curator', 'Community Manager', 'Developer']

PortalRoles.rights_carrying()
# ['Portal Administrator', 'Data Curator', 'Community Manager']

PortalRoles.DATA_CURATOR.permissions
# ('project.view_project', 'project.add_project', ...)

PortalRoles.is_held_by(person, PortalRoles.COMMUNITY_MANAGER)
```

Ask what a person may do with the permission system, never with a role name:

```python
person.has_perm("dataset.change_dataset", dataset)
```

### Installation

`FairDMConfig.ready()` connects `PortalRoles.reconcile` to Django's `post_migrate` signal with `dispatch_uid="fairdm.reconcile_portal_roles"`. It is connected with no sender, so it runs after the migration of every app, and a run that comes before the permissions of a later app exist is followed by one that finds them. The roles are therefore installed by `manage.py migrate`. `fairdm.E500` reports a portal where a role is missing. See [Configuration checks](../../administrators/reference/configuration-checks.md).

### Protection of the role groups

`ContributorsConfig.ready()` connects two receivers to `auth.Group`. Both raise `ValidationError`.

| Receiver | Signal | Refuses |
|---|---|---|
| `refuse_shipped_role_deletion` | `pre_delete` | Deleting a group named like a shipped role, including through a queryset delete |
| `refuse_shipped_role_rename` | `pre_save` | Renaming a shipped role. A new group, including one that `reconcile()` creates, passes |

## PortalRolePermissionBackend

`fairdm.permissions.PortalRolePermissionBackend` is last in `AUTHENTICATION_BACKENDS`. A role's permissions are declared at the model level and Django answers `False` to every object-level question about a model-level permission. This backend derives the object-level answer from role membership.

`has_perm(user_obj, perm, obj=None)` returns true when all of these hold:

- `obj` is not `None`. The model-level question is never answered here.
- The user is active.
- `perm` is not `contributors.manage_organization` or `manage_organization`, which is never answered here.
- `perm` has the form `app_label.codename`. A bare codename gives false.
- The user is in a group named like a shipped role, and that group holds the permission.

A permission granted straight to a person, or through a group your portal created, is not carried to individual records. The answer applies to every instance of the model.

## Administration interface

| Name | In | What it does |
|---|---|---|
| `CustomAdminSite` | `fairdm.contrib.admin.sites` | The default admin site. `has_permission(request)` is true for an active user who is staff or holds a rights-carrying role. Nothing is stored on the person, and no `is_staff` flag is set |
| `PortalAdminAuthenticationForm` | `fairdm.contrib.admin.sites` | The admin login form. `confirm_login_allowed(user)` admits staff and holders of a rights-carrying role, where Django's own form refuses anyone without `is_staff` |

Removing someone from their last rights-carrying role closes the administration interface to them again with no second step.

## TeamView

`TeamView` is in `fairdm.contrib.contributors.views.team`. It renders the **Team** page of the **Community** menu, at `community/team/` under the URL name `team`. It lists each shipped role with the active people who hold it, in declaration order, and leaves out a role nobody holds. It shows portal roles only. A role on a contribution is credit on a record and is never shown. The page is public.

| Attribute | Type | Default | What it does |
|---|---|---|---|
| `template_name` | `str` | `"contributors/team.html"` | The page template |
| `list_item_template` | `str` | `"contributors/contributor_card.html"` | The template that draws one holder. It receives the person as `object` |
| `grid_config` | `dict` | `{"cols": 1, "md": 2, "lg": 4, "gap": 4}` | The grid the holders are laid out in |
| `page_title` | lazy `str` | "Portal Team" | The page title |
| `page_subtitle`, `page_info` | lazy `str` | Fixed texts | The text under the title and the information text |
| `page_info_actions` | `list` of `dict` | One link, "About portal roles" | The actions beside the information text |

| Method | Returns | What it does |
|---|---|---|
| `get_roles()` | `list` of `{"role": PortalRole, "holders": [Person]}` | One entry for each role that has active holders, in declaration order. Uses two queries however many roles or holders there are. The holders are ordered by name and prefetched with `for_cards()` |
| `get_context_data(**kwargs)` | `dict` | Adds `roles`, `list_item_template` and `grid_config` |

What the page lists is not configurable. It reads `PortalRoles`, so the page and the rights agree. To change how it looks, see [How to change how the team page looks](../how-to/change-how-the-team-page-looks.md). To define a role that the page does not list, see [How to define a portal role of your own](../how-to/define-a-portal-role-of-your-own.md).
