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
code. To sign in as each role in your own development environment, see
[Development accounts](development_accounts.md).

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

## How a role's rights reach a record

A role's permissions are declared at the model level: the Data Curator holds
`dataset.change_dataset`, not a grant on any particular dataset. Django answers `False` to every
object-level question asked of a model-level permission, so on its own that declaration would let a
curator change nothing.

`fairdm.permissions.PortalRolePermissionBackend` closes that gap. It sits last in
`AUTHENTICATION_BACKENDS` and answers one question: does this person hold this permission through
one of the four shipped roles? If they do, the answer applies to every instance of that model.

```python
# A person in the Data Curator role
person.has_perm("dataset.change_dataset", any_dataset)   # True, including a private one
```

It is deliberately narrow. A permission granted straight to a person, or through a group your portal
invented, is **not** carried to individual records:

```python
# A person holding dataset.change_dataset directly, in no portal role
person.user_permissions.add(change_dataset)
person.has_perm("dataset.change_dataset", private_dataset)   # False
```

That distinction matters. Several of the framework's pages rely on an object-level check to keep a
private record from being disclosed, and treating every model-level grant as portal-wide would
reopen that. Portal-wide rights are what a portal role is for; a group of your own still works the
way Django groups have always worked.

One permission is never answered here at all: `contributors.manage_organization` comes from a
current owner affiliation and from nothing else.

## Reaching the administration interface

Holding a rights-carrying role is enough. Nothing is stored on the person — no `is_staff` flag is
set — so removing somebody from their last rights-carrying role closes the interface to them again
with no second step to remember. `PortalAdminAuthenticationForm` is what lets a role holder sign in
at the administration login, which Django's own form refuses for anybody without `is_staff`.

## The portal team page

`fairdm.contrib.contributors.views.team.TeamView` renders **Community → Team**: each shipped role
with the active people holding it, in declaration order, with roles nobody holds left out. It is
public, and it shows portal roles only — a contribution's role is credit on a record and belongs
nowhere near it.

```python
from fairdm.contrib.contributors.views.team import TeamView


class MyPortalTeamView(TeamView):
    """Same people, your own card template."""

    list_item_template = "myportal/team_member.html"
```

Override the view if your portal wants a different presentation, and point your own route at it.
What the page lists is not configurable by design: it reads `PortalRoles`, so the page and the
rights always agree.
