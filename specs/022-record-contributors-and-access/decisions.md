# Decisions: 022-record-contributors-and-access

Questions settled while writing the specification, with the reasoning behind each. The
maintainer's own rulings are recorded under *Clarifications* in `spec.md` and are not repeated
here, except where one confirmed a choice first made in this file.

## Not yet seen by the maintainer

One choice changes what gets built and has not been in front of the maintainer, on paper or on a
screen:

- **Upgrade keeps access by listing people.** When a portal is brought up to date, anyone holding
  rights over a record they are not credited on is listed on it as a contributor, so that nobody
  loses access. See *Upgrade* below.

Three smaller choices were made when the specification was revised after the prototype was
approved. They follow from what was approved and were not themselves on a screen:

- Where a record names people and organizations together, people come first.
- A match from ORCID or ROR that the portal already holds under the same identifier uses the
  existing profile.
- Choosing an organization for a person's credit does not add an affiliation to that person's
  profile.

## Confirmed by the maintainer on the prototype

These were first decided here and were then on the screens the maintainer reviewed and approved on
2026-10-06.

### Three levels, not separate permissions

The request speaks of "full rights", of a contributor who "can manage" a record and of one being
"downgraded". Those words describe an ordered scale, so the specification uses one: view, edit,
manage. A list of independent permissions would let a team build combinations nobody can reason
about, such as someone who can delete a dataset and cannot open it. The framework declares several
record-level permissions today, and two of them on projects are checked nowhere. FR-043 requires
every declared right to be governed by a level, which closes that gap without the specification
naming any of them.

Visibility and deletion were put with manage because both affect everyone on the record. The names
of the levels are for the specification's own use and are not required wording.

### Rights flow downward

The request says nobody gets into a private record without being listed as a contributor on it. An
earlier request, which this feature settles, says membership of a project or dataset should carry
rights over what sits beneath it. Read together: a person must be listed somewhere on the chain
above the record. The framework already works this way for samples, which take their rights from
their dataset, and `CONTEXT.md` says access flows downward. Requiring a person to be listed on
every one of a dataset's thousand samples before they could open them would make the feature
unusable.

A record's own tab can raise a person and cannot lower what they hold from above. Allowing a
dataset to shut out a project manager would make the last-manager rule depend on exceptions
scattered across records.

### Everything on the tab needs manage

Adding a contributor gives them the view level, and removing one takes their rights away, so both
are changes to access. Letting the edit level do either would let an editor let people into a
private record or remove its manager. The cost is that someone who only enters data cannot credit a
sample's collector without being given manage on the dataset.

### Access-only contributors are listed, with no role

The maintainer ruled that there is no separate page for granting access and that nobody gets in
without being listed. A colleague who needs to read a private dataset and did no work on it is
therefore a contributor. Requiring a contribution role would force the team to invent credit for
them, so a contributor may hold none. Whether a citation names them is decided by the citation's
own rules, which pick by role.

### An organization stays when its last person leaves

An organization is listed on a record when a person is credited from it. When that person is
removed, or credited from somewhere else, the organization is left where it is and can then be
removed by hand. Taking it away automatically would remove credit nobody asked to remove, and
would have to guess whether the organization had also been credited in its own right.

## How the request was read

A Contributors tab on all four core record types, where the people who can manage a record add,
edit, remove and order its contributors, and where each person's rights on that record are set next
to their contribution roles. It replaces granting record-level rights in the administration
interface as the way a team shares a private record. Everything under "Agreed so far" in the
request was taken as given. A working prototype was then reviewed, and the specification was
revised to describe what was approved.

## Contribution roles confer no rights

An earlier question asked which contribution roles should confer which rights. `CONTEXT.md` already
says a contribution role "carries no rights of any kind", and the request sets roles and
permissions as two separate things in one edit. The answer is that none do. A team that wants its
project leader to manage the project gives them that level.

## A person listed on a dataset inside a private project can open the dataset

`CONTEXT.md` says a private project hides every dataset in it. That is about visitors. A person
listed on the dataset has been let in deliberately by someone who can manage it, so it opens for
them, and they gain nothing over the project.

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
permissions change. A community manager can make people and organizations elsewhere in the portal.
On this tab, making one is part of crediting a record, so it needs the right to manage the record
and nothing more.

## Two orders, and how they combine

The maintainer ruled that people and organizations are separate lists with separate orders. A
citation is a single sequence, so the specification has to say how the two join. People come
first, in their order, and organizations follow in theirs. That is how author lists are read in
practice: a consortium or an institute named as an author follows the individuals. Each place that
names contributors keeps its own rule for whom it names. A new contributor goes last in their own
list so that adding someone never reshuffles an agreed order.

## The organization a person is credited from

The maintainer ruled that it is chosen for each record and defaults to the primary affiliation.
Three things were added around that ruling:

- It is kept with the record. This is what makes the maintainer's own example work: a dataset
  from someone's time at one institute must go on saying so after they move.
- A person credited with no organization is shown with none. Falling back to their profile's
  primary affiliation would bring back the problem the ruling removes.
- Choosing an organization for a record does not add an affiliation to the person. An affiliation
  is a statement on the person's own profile, which the profile's keeper makes. A manager crediting
  a dataset is not in a position to make it for them.

An organization typed by name that the portal does not hold is made as a new organization, so that
a manager is never stopped partway through crediting someone.

## Creating people and organizations from the tab

The first version of this specification left this out. The maintainer asked for it on the
prototype: search the portal, look up in ORCID or ROR, or enter by hand.

- A profile made from a registry takes the name and the identifier, and nothing else is promised.
  Filling in the rest and keeping it current is the work of identifier synchronisation (R13 and
  R28), and promising it here would duplicate that.
- The identifier decides whether a registry match is already in the portal. Matching by name would
  merge namesakes.
- A person entered by hand whose name is already in the portal can still be made, because two
  people do share names. An organization with the same name is not made twice, because two
  organizations with one name are almost always one organization entered twice.
- A person made here has no account. An email address may be recorded for later claiming and is
  never shown. Nothing is sent to anyone.
- A registry being unreachable must not stop a team crediting someone, so the other two ways keep
  working.

## The organization's entry on the tab

The maintainer ruled that it shows the logo and the name only. The people an organization is
listed for are therefore named where they matter, which is where its removal is refused. The
specification requires that the reason is given in place of the removal control and that the
people are named on a direct request, and leaves the rest to the page.

## Upgrade

Portals already hold record-level rights granted on creation or in the administration interface.
The specification keeps every one of them by mapping it to the lowest level that covers it. A
person who holds rights over a record without being credited on it is added as a contributor,
because after this feature the tab is the one place that says who can get in, and it has to tell
the truth. Existing contributors with no rights get the view level, the same as a newly added one.

The organization already stored with a person's entry is kept as the one they are credited from,
and is listed on the record. An entry with none is left with none. Filling it from the person's
profile at upgrade would write a guess into the record as if someone had chosen it.

## Left out on purpose

- Telling a person they were added, and asking for access. The first needs a notification system
  and the second belongs to the contact feature (#407).
- Inviting a person by email.
- Editing a person's affiliations from the tab.
- Leaving a record without being able to manage it.
- Giving a manager to records created by import or in the administration interface.
- Which lists show a private record to the people who may open it. The record list feature (#403)
  states that every list shows only what the viewer may see.
- The editing pages themselves (#404). This specification says which level each kind of page needs.

## Dependencies on sibling features

None. The tab is an ordinary plugin on a record's page and needs nothing from the feature that adds
page actions, overview cards and plugin replacement (#401). The editing pages feature (#404) and
the record list feature (#403) rely on the levels defined here and not the other way round.

## Decisions made while planning the build

Each has a number so later notes can point at it.

## D1. Stored record permissions stop applying to core records

**Decision**: a level on a contribution is the only thing that gives a person rights over a
project, dataset, sample or measurement. Rows stored by django-guardian for those records are
converted once, at upgrade, and are not consulted afterwards. The two backends that passed a
dataset's rows down to its samples and measurements are removed.
**Why**: the specification wants one decision for every page (FR-051) and a private record open
only to people who hold a level (FR-048). A second route through stored rows would be a way in
that the Contributors tab does not show.
**Revisit if**: a portal needs to grant rights over core records to a whole group. That would be a
feature of its own, with the group shown on the tab.

## D2. Visibility and the record a record sits under need the manage level on the update forms

**Decision**: on the existing update forms of the four record types, the visibility field and the
parent field (a dataset's project, a sample's or measurement's dataset, a project's owner) are
offered only to someone who can manage the record.
**Why**: the design review showed that the edit level otherwise reaches both through the ordinary
update page. FR-037 puts visibility with manage. Moving a record changes who holds rights over it
from above, which is a change to access, and the specification puts every change to access with
manage. The specification does not name the parent field, so this is a reading of it and not a
quotation.
**Revisit if**: the feature that rebuilds the editing pages (#404) gives moving a record a page of
its own.

## D3. Group-level rows are converted too

**Decision**: at upgrade, each current member of a group that holds stored rows on a core record
gets the level those rows map to.
**Why**: FR-063 says nobody loses anything at upgrade. Leaving group rows behind would have taken
access away from their members with only a changelog line to say so.
**Revisit if**: never. It runs once.

## D4. Deleting a sample now needs the manage level on it or above

**Decision**: before this feature a person holding only the right to change a dataset could delete
its samples. Deleting is now a manage-level action on every core record.
**Why**: the specification puts deleting with manage (FR-037) without an exception for samples.
The people affected are those given a change right and no delete right by hand, in code or a
shell. The pages that create records grant both together. The changelog says so.
**Revisit if**: a portal reports data-entry staff who need to delete samples they added.

## D5. Classes for the access questions, the changes and the registries

**Decision**: `RecordAccess(record)`, `Crediting(record)`, `Orcid` and `Ror`, with no shared base
classes.
**Why**: the constitution's cohesion article asks that functions sharing a subject and a first
argument sit on a class. `Crediting` also gives the transaction and the row lock one home.
**Revisit if**: a third registry is added, which is when a shared shape would have three callers.

## D6. The default affiliation is the page's, not the model's

**Decision**: the model hook that filled a new contribution's affiliation from the person's
primary affiliation is deleted. The primary affiliation is only the option selected to begin with
on the page.
**Why**: a person added with no organization must be shown with none (FR-024). The hook made that
impossible for anyone who has a primary affiliation.
**Revisit if**: never.

## D7. A superuser is not credited

**Decision**: the existing rule that a superuser cannot be saved as a contributor stays. Adding
one from the tab is refused with a message, and a superuser who creates a record is not listed on
it.
**Why**: the rule predates this feature and the specification does not ask for it to change. A
record a superuser creates is the one case where a record starts without a manager from its own
team, and a superuser can always add one.
**Revisit if**: the maintainer wants superusers credited like anyone else.

## Decisions made while building story 1

## D8. Levels set on the edit page and by the seeds are written to the field directly

**Decision**: until the story that gives `Crediting.update` a `level`, the edit page and the seeds
set `Contribution.level` with a plain save. `Crediting.add` gives a person the view level; the
seed and the page raise or clear it from there.
**Why**: `update` with a level, and the refusal of a level below what is held from above, belong to
the story that moves levels into the service. The edit page already had that refusal and the
last-manager refusal, and both stay in the page for now.
**Revisit if**: never. That story moves the page's level handling into `Crediting.update` and the
seeds follow it.

## D9. A person added from the tab holds no stored permission row until the backend switches

**Decision**: the add page no longer writes the guardian rows the prototype wrote. A person added
from the tab holds the view level on the contribution and nothing else.
**Why**: the module that wrote those rows is replaced, and rewriting them in the page would be
code the backend story deletes. Until it lands, a person added from the tab cannot open a private
record the permission backends still guard.
**Revisit if**: a release is cut between this story and the backend story.

## D10. `entry.manages` replaces a comparison with the word "manage"

**Decision**: the page's description of a contributor carries `manages`, true when their
effective level is manage, and `cotton/contribution/access.html` reads it in place of comparing
`entry.effective` with a string. The `:outline` attribute on that badge is a Cotton dynamic
attribute that cannot be resolved from an expression, so it was never applied, before or after;
the badge draws as it did.
**Why**: levels are integers now, so the comparison had to change, and the instruction was to
change a template only where a context name has to.
**Revisit if**: the maintainer wants the non-manage badges outlined, which needs a boolean in the
context rather than an expression.

## D11. The edit page checks the roles by asking the service, inside a transaction

**Decision**: the edit page calls `Crediting.update` and, when other fields on the form are also
refused, rolls the roles back with `transaction.set_rollback`.
**Why**: the page must report every refused field in one answer and save nothing, and the offered
roles must be decided in one place.
**Revisit if**: `Crediting.update` takes the level and the organization as well, which makes the
whole save one call.

## D12. The tab's page tests live in test_shared.py

**Decision**: the tests of the Contributors tab and its pages are in
`tests/test_contrib/test_contributors/test_plugins/test_shared.py`, not in the
`test_contribution_tab.py` that `tasks.md` names.
**Why**: the pages are in `plugins/shared.py`, and the conformance step refuses a test module that
mirrors no source module.
**Revisit if**: the pages move to a module of their own, which is when a test module of that name
would mirror it. Later stories add their classes to `test_shared.py`.

## Decisions made while building story 2

## D13. `Crediting.update` tells three answers apart with a module constant

**Decision**: `update(contribution, *, roles, organization=UNCHANGED)`. `UNCHANGED` is a public
constant in `services/crediting.py`. Leaving the argument out leaves the organization as it is, an
organization sets it, and `None` sets it to none. An organization argument is ignored for a
contribution whose contributor is an organization, in `add` and `update` alike.
**Why**: `None` has to mean "none", and the edit page must be able to save the roles without
touching the organization. A keyword default of `None` cannot say both.
**Revisit if**: `update` takes the level too, which makes the sentinel one of three.

## D14. The choice accepts an affiliation only from the person's own, and makes the organization at save time

**Decision**: `AffiliationChoice` accepts `org:<id>` only for an affiliation the person holds. Any
other organization is chosen with `other` and a name, matched case-insensitively against the portal
and made when it is not there. `organization()` does the matching and the making, and the pages
call it inside the transaction that saves the credit.
**Why**: the prototype made the organization while reading the form, so a save refused for another
field (a level, a role) left an organization behind. A request naming an organization the person
holds no affiliation with by id is outside what the page offers.
**Revisit if**: the registry ways of adding (story 3) need to credit a person from an organization
by id.

## D15. The two components fall back through `get_real_instance`, not through the credit

**Decision**: `c-contributor.item` and `c-contributor.card.person` read the fallback organization
from `contributor.get_real_instance.primary_organization`, a name a contribution does not have, in
place of `c.primary_organization`, which resolved the contribution to its person first.
**Why**: only that expression had to change. A filter argument that does not resolve raises
instead of falling through, so the name is read in the outer `with`, where a missing name is an
empty value. `get_real_instance` keeps the fallback for a plain contributor row that is really a
person, which the old expression also handled.
**Revisit if**: a third component needs the same rule, which is when it belongs in a template tag.

## D16. Callers of the deleted hook

**Decision**: `Contribution.add_to`, `Contributor.add_to`, `add_contributor` and the other seeds
(`seed_profiles`, `generate_fake_data`, the project, sample and measurement seeds) are left as they
are and now credit a person from none unless an organization is passed. `demo/seed/contributors.py`
credits through `Crediting`. The one pre-existing test that asserted the hook
(`test_models.py::...::test_contribution_default_affiliation`) is updated to assert the new
behaviour.
**Why**: nothing but that test read the default. A seeded record whose people had a primary
affiliation drew it through the hook, and now shows them with none, which is what FR-024 says a
credit with no organization is.
**Revisit if**: the maintainer wants the example records to show organizations again, which is a
change to the seeds.
