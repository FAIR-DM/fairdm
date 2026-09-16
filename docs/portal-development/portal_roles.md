# Portal roles

Every FairDM portal arrives with four roles, installed the first time its database is brought up to
date and repaired every time after that. They are ordinary `auth.Group` rows; what is different
about them is that FairDM owns their definition, so a portal never has to invent a set of roles or
work out which permissions each one needs.

| Role | The job | Holds rights |
|---|---|---|
| Portal Administrator | Runs the portal, and decides who holds which role | Yes |
| Data Curator | Looks after the content: projects, datasets, samples, measurements | Yes |
| Community Manager | Looks after the people: accounts, profiles, organisations | Yes |
| Developer | Builds and maintains the portal | No |

What each role can do is the administrator's reference, in
[Roles and permissions](../portal-administration/roles.md). This page is about reading them from
code.

## Reading the shipped roles

`fairdm.portal_roles.PortalRoles` carries the declarations and the methods that read them. Each
role is a `PortalRole`: a stored name, a translated display label, and the exact permissions it
holds.

```python
from fairdm.portal_roles import PortalRoles

PortalRoles.shipped_names()
# ['Portal Administrator', 'Data Curator', 'Community Manager', 'Developer']

PortalRoles.rights_carrying()
# ['Portal Administrator', 'Data Curator', 'Community Manager']

PortalRoles.DATA_CURATOR.permissions
# ('project.view_project', 'project.add_project', ...)
```

`rights_carrying()` is the list that matters for access: holding any role on it gives a person the
administration interface, and holding only the Developer role does not.

To ask whether somebody holds a role, ask the ordinary Django question:

```python
person.groups.filter(name=PortalRoles.DATA_CURATOR.name).exists()
```

Deciding what a person may *do* is a different question, and the answer is never a role name. Ask
the permission system:

```python
person.has_perm("dataset.change_dataset", dataset)
```

## Installing and repairing them

`PortalRoles.reconcile()` runs on every `migrate`, through a `post_migrate` receiver. It creates
whatever role is missing and sets each role's permissions to exactly what the declaration says, so
a permission removed or added by hand in the administration interface is corrected on the next
update. It never changes who is in a role.

A portal upgrading from a version before this existed keeps its people: the three groups FairDM used
to ship as a fixture are renamed into the roles that replace them, and a rename carries their
membership across.

## Defining your own roles

Nothing here limits a portal to four groups. If your community needs a different split of rights,
create a group of your own and give it the permissions you want. Do not edit the permissions on a
shipped role: `reconcile()` will put them back on the next `migrate`, because those rights belong to
the framework's definition of what the role is.
