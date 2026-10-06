# ADR 0025 — A level on the contribution decides rights over a core record

**Status:** accepted

## Decision

What a person may do on a project, dataset, sample or measurement is one stored level on their
contribution to it: view, edit or manage, each including the one before. A level on a dataset
applies to its samples and measurements, and a level on a project applies to its datasets. The
higher of two applies.

One permission backend, `RecordLevelBackend`, answers every object-level question about these
records from that level. Each permission the four models declare is mapped to the level it needs,
and a permission the map does not know is refused.

Permissions stored per person per record by django-guardian are not read for these records. An
upgrade migration converts the ones that exist into levels. The backends that passed a dataset's
stored permissions down to its samples and measurements are removed. django-guardian stays for
organizations and for any model a portal defines.

Holders of a portal role are answered as before, by `PortalRolePermissionBackend`.

## Why

Before this, rights over a record were several permission rows per person per record, granted to
the creator and otherwise only in the administration interface. A research team could not let a
colleague into its own private dataset. Three backends each knew part of the rule, none reached a
project, and several lists read the rows directly without asking any backend.

The Contributors tab had to show and set what each person may do. A level is something a person
can read and choose. A set of independent permissions is not: it allows combinations nobody can
reason about, such as being able to delete a dataset and not open it.

Leaving the stored rows in force beside the levels would have kept a second way into a private
record that the tab does not show.

## Consequences

- Code that asks `user.has_perm("dataset.change_dataset", dataset)` keeps working and is answered
  from the level.
- Code that grants rights with `assign_perm` on a core record no longer grants anything. It
  credits the person through `Crediting` at the level it means.
- A list of the records a user may see or change uses `with_level(user, level)` on the model's
  queryset. A lookup of stored rows finds nothing.
- No level gives the right to delete without the right to change.
- Deleting a sample needs the manage level on it or above. The right to change its dataset used to
  be enough.
- Rights cannot be given over a core record to a whole group. If that is needed, it is a feature
  of its own, with the group shown on the tab, and this record would be amended.
- A new permission on a core model has to be added to the map, or it is refused for everyone but
  holders of a portal role.
