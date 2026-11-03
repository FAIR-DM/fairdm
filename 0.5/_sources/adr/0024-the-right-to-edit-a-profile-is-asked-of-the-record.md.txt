# ADR 0024 — The right to edit a profile is asked of the record

**Status:** accepted

## Decision

Each contributor answers the question itself. `Contributor.is_editable_by(user)` returns False,
and `Person` and `Organization` override it with their own rule. The editing page asks it on every
request, and the overview pages ask it before offering an edit action.

Role membership is read from the role's group with `PortalRoles.is_held_by(user, role)`, never
from a permission the role happens to hold.

Superusers, staff and the holders of other portal roles get no right to edit from these pages.
The administration interface, where they can change any record, is unchanged.

## Why

A person's or an organization's profile can be edited in the portal. Who may do so depends on the
record as much as on the user: a person edits their own profile, an organization's owner and
current administrators edit its profile, and a community manager edits any organization and any
person nobody can sign in as.

Django's model permissions cannot say this. `contributors.change_person` is held by Portal
Administrators as well as Community Managers, and only one of those roles may edit profiles in the
portal. A model permission also knows nothing about the state of the profile being edited. The
existing permission backend for organizations lets a superuser manage any organization, which the
editing pages must not do.

## Consequences

- The whole rule for a kind of record is in one method, and the page and the links that lead to
  it cannot disagree.
- A portal that wants its administrators to edit profiles in the portal adds them to the
  Community Manager role. Granting a Django permission does nothing here.
- `user.has_perm("contributors.change_person", person)` does not describe who may use the editing
  page. Code that needs to know asks `is_editable_by`.
- A new kind of editor is a change to the method. If the list grows long, a permission backend
  that reads the same rules may serve better, and this record would be superseded.
