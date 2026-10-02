# Decisions: 022-record-contributors-and-access

Questions settled while writing the specification without asking the maintainer, with the reasoning
behind each. The maintainer's own rulings are recorded under *Clarifications* in `spec.md`, in the
session dated 2026-10-01 and 2026-10-02, and are not repeated here.

## For Sam to confirm

These five change what gets built and were not among the points already agreed. Each is explained
under its own heading below.

1. Rights are three levels (view, edit, manage) and not a list of separate permissions. Changing
   visibility and deleting sit with manage.
2. Rights flow downward: a level on a project applies to its datasets, and a level on a dataset to
   its samples and measurements.
3. Everything on the Contributors tab needs the manage level. Someone at the edit level cannot add
   or change credits.
4. A colleague added only for access is listed publicly as a contributor, with no contribution
   role.
5. On upgrade, anyone holding rights over a record they are not credited on is listed on it as a
   contributor, so that nobody loses access.

## How the request was read

The request was written up as an interpretation and treated as confirmed, with no questions put to
the maintainer. The reading: a Contributors tab on all four core record types, where the people who
can manage a record add, edit, remove and order its contributors, and where each person's rights on
that record are set next to their contribution roles. It replaces granting record-level rights in
the administration interface as the way a team shares a private record. Everything under "Agreed so
far" in the request was taken as given.

## Three levels, not separate permissions

The request speaks of "full rights", of a contributor who "can manage" a record and of one being
"downgraded". Those words describe an ordered scale, so the specification uses one: view, edit,
manage. A list of independent permissions would let a team build combinations nobody can reason
about, such as someone who can delete a dataset and cannot open it. The framework declares several
record-level permissions today, and two of them on projects are checked nowhere. FR-023 requires
every declared right to be governed by a level, which closes that gap without the specification
naming any of them.

Visibility and deletion were put with manage because both affect everyone on the record. The names
of the levels are for the specification's own use and are not required wording.

## Contribution roles confer no rights

An earlier question asked which contribution roles should confer which rights. `CONTEXT.md` already
says a contribution role "carries no rights of any kind", and the request sets roles and
permissions as two separate things in one edit. The answer is that none do. A team that wants its
project leader to manage the project gives them that level.

## Rights flow downward

The request says nobody gets into a private record without being listed as a contributor on it. An
earlier request, which this feature settles, says membership of a project or dataset should carry
rights over what sits beneath it. Read together: a person must be listed somewhere on the chain
above the record. The framework already works this way for samples, which take their rights from
their dataset, and `CONTEXT.md` says access flows downward. Requiring a person to be listed on
every one of a dataset's thousand samples before they could open them would make the feature
unusable.

The alternative for projects was to stop at the dataset, so that a project's contributors gain
nothing over its datasets. That was not chosen because a project lead who cannot see the project's
own datasets is the situation the earlier request describes as broken.

A record's own tab can raise a person and cannot lower what they hold from above. Allowing a
dataset to shut out a project manager would make the last-manager rule depend on exceptions
scattered across records.

## A person listed on a dataset inside a private project can open the dataset

`CONTEXT.md` says a private project hides every dataset in it. That is about visitors. A person
listed on the dataset has been let in deliberately by someone who can manage it, so it opens for
them, and they gain nothing over the project.

## Everything on the tab needs manage

Adding a contributor gives them the view level, and removing one takes their rights away, so both
are changes to access. Letting the edit level do either would let an editor let people into a
private record or remove its manager. Splitting credit from access on the tab was considered and
not chosen: it would need two sets of rules for one list.

The cost is that someone who only enters data cannot credit a sample's collector without being
given manage on the dataset.

## Access-only contributors are listed, with no role

The maintainer ruled that there is no separate page for granting access and that nobody gets in
without being listed. A colleague who needs to read a private dataset and did no work on it is
therefore a contributor. Requiring a contribution role would force the team to invent credit for
them, so a contributor may hold none. They are still shown on the tab to anyone who may open the
record. Whether a citation names them is decided by the citation's own rules, which pick by role.

## Who counts for the last-manager rule

The rule exists so that a record never becomes unmanageable by its own team. Three choices follow
from that purpose:

- A person who can manage the record through the record above counts, because they can in fact
  manage it. Without this, a sample created by hand could never have its creator removed.
- A person without an active account does not count, because they cannot sign in and act.
- A holder of a portal role does not count, because the point is not to depend on portal staff.

A data curator is bound by the rule like anyone else, and can always raise someone on a record that
has no manager.

## Portal roles

Only the Data Curator role bears on research records, as specification 017 has it. Managing a
record's contributors is treated as part of changing the record, which that role may already do.
The Portal Administrator, Community Manager and Developer roles gain nothing here, and no role's
permissions change.

## Order

The roadmap item asks that order be under the research team's control because it decides how the
record is cited. The order set on the tab is a single order for the whole record. Each place that
names contributors keeps its own rule for whom it names and takes their relative order from the
tab. A new contributor goes last so that adding someone never reshuffles an agreed author order.

## Upgrade

Portals already hold record-level rights granted on creation or in the administration interface.
The specification keeps every one of them by mapping it to the lowest level that covers it. A
person who holds rights over a record without being credited on it is added as a contributor,
because after this feature the tab is the one place that says who can get in, and it has to tell
the truth. Existing contributors with no rights get the view level, the same as a newly added one.

## Left out on purpose

- Telling a person they were added, and asking for access. The first needs a notification system
  and the second belongs to the contact feature (#407).
- Creating a person or organization from the tab, and inviting by email.
- Leaving a record without being able to manage it.
- Giving a manager to records created by import or in the administration interface.
- Which lists show a private record to the people who may open it. The record list feature (#403)
  states that every list shows only what the viewer may see.
- The editing pages themselves (#404). This specification says which level each kind of page needs.

## Dependencies on sibling features

None. The tab is an ordinary plugin on a record's page and needs nothing from the feature that adds
page actions, overview cards and plugin replacement (#401). The editing pages feature (#404) and
the record list feature (#403) rely on the levels defined here and not the other way round.

## Prototype before building

The feature should be shown as a working prototype before it is planned in detail. The existing
tab on projects only lists and adds. Setting roles and a level in one edit, showing access held
from the record above, and reordering are new, and whether they read clearly is a judgement for
the maintainer's eye.
