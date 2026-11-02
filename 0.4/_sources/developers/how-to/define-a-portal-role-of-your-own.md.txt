# How to define a portal role of your own

FairDM ships four portal roles and keeps their permissions fixed. This guide adds a fifth group of your own, with the permissions you choose, and installs it with every `migrate`. Use it when your community needs a different split of rights than the shipped roles give.

Do not edit the permissions of a shipped role. `PortalRoles.reconcile()` puts them back on the next `migrate`, because those rights belong to FairDM's definition of the role.

## Steps

1. Declare the role as a `PortalRole`. Give it a name that no shipped role uses, and list each permission as `app_label.codename`.

   ```python
   # myportal/roles.py
   from django.utils.translation import gettext_lazy as _

   from fairdm.portal_roles import PortalRole

   REVIEWER = PortalRole(
       name="Reviewer",
       label=_("Reviewer"),
       permissions=("dataset.view_dataset", "dataset.change_dataset"),
   )
   ```

2. Write the function that installs it. It creates the group and sets its permissions to exactly the declaration. It never touches who is in the group.

   ```python
   # myportal/roles.py
   from django.contrib.auth.models import Group, Permission
   from django.db.models import Q


   def install_reviewer_role(**kwargs):
       group, _created = Group.objects.get_or_create(name=REVIEWER.name)
       query = Q()
       for permission in REVIEWER.permissions:
           app_label, codename = permission.split(".", 1)
           query |= Q(content_type__app_label=app_label, codename=codename)
       # An empty Q() matches every permission, so a role with none is set to none.
       group.permissions.set(Permission.objects.filter(query) if REVIEWER.permissions else [])
   ```

3. Connect it to `post_migrate` with no sender, as FairDM does for its own roles. A portal's apps load before the apps whose permissions the role names, so a run may come before those permissions exist, and a later run in the same `migrate` finds them.

   ```python
   # myportal/apps.py
   from django.apps import AppConfig
   from django.db.models.signals import post_migrate


   class PortalConfig(AppConfig):
       name = "myportal"

       def ready(self):
           from .roles import install_reviewer_role

           post_migrate.connect(
               install_reviewer_role, dispatch_uid="myportal.install_reviewer_role"
           )
   ```

4. Run `uv run python manage.py migrate` and add people to the group. An administrator does this on the person's own page, in the **Groups** field. In code:

   ```python
   from django.contrib.auth.models import Group

   person.groups.add(Group.objects.get(name="Reviewer"))
   ```

5. Ask whether a person holds the role. `PortalRoles.is_held_by` reads the group named by `role.name`, so it works with your own `PortalRole`.

   ```python
   from fairdm.portal_roles import PortalRoles
   from myportal.roles import REVIEWER

   PortalRoles.is_held_by(request.user, REVIEWER)
   ```

   To ask what a person may do, ask the permission system with `person.has_perm("dataset.change_dataset")`. Do not branch on a role name.

## What the role does not get

A group of your own works the way Django groups work. It does not get what the shipped roles get:

- Its permissions are not carried to individual records. A person who holds `dataset.change_dataset` only through your group is refused on a private dataset, because `PortalRolePermissionBackend` answers only for the four shipped roles. To give a person rights on a record, list them on it with a level. See [How to credit a person on a record](credit-a-person-on-a-record.md).
- It does not open the administration interface. Only the roles in `PortalRoles.rights_carrying()` do.
- It is not listed on the portal's **Team** page, which reads the four shipped roles.

For the reasons behind these limits, see [ADR 0019](../../adr/0019-a-portal-role-is-the-unit-of-portal-wide-rights.md). The classes and functions are listed in [Portal roles in code](../reference/portal-roles.md).
