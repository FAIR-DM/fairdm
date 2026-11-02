# ADR 0019 — A portal role is the unit of portal-wide rights

**Status:** accepted

## Decision

FairDM ships four portal roles — Portal Administrator, Data Curator, Community Manager and
Developer — declared in `fairdm/portal_roles.py` as a name and an explicit list of permissions, and
installed into every portal. Three carry rights. The fourth carries none and exists so that the
people who build a portal are named on its team.

A role's rights reach individual records: a permission held through one of these four applies to
every instance of that model. A permission held any other way — granted straight to a person, or
through a group a portal created for itself — does not.

## Why

**Running a portal is a standard job, and it was being invented per portal.** An administrator had
to work out a set of roles and a permission list before anyone could do anything, and the three
group names the framework did carry held no permissions at all. Three places in the code granted
broad edit rights by matching one of those names, outside the permission system entirely, where no
portal author could discover them and no object-level rule could override them.

**Three rights-carrying roles rather than two, because looking after people is not looking after
records.** The people side touches email addresses, account states, profile claims and duplicate
merges. The person a research group trusts with their sample data is not automatically the person
they want reading account records. A small portal puts one volunteer in both roles at no cost;
splitting the roles later, after portals have handed out a combined one, costs a migration and a
conversation with every portal.

**Portal-wide rights have to reach records, and Django will not do it.** `ModelBackend.has_perm`
answers `False` for every object-level question, so a Data Curator holding `change_dataset` could
change nothing. One more backend derives the object-level answer from role membership.

**It is narrow on purpose.** The first version of that backend honoured any model-level permission,
which reopened a disclosure guard this codebase had put in deliberately: a person holding only a
model-level grant is refused on a private record's editing pages, because a page that inherits its
visibility rule is not guarded at all. Four tests caught it. Restricting the derivation to the four
shipped roles serves the requirement exactly and leaves that guard standing.

## Consequences

What a role can do is readable in one place and pinned by a test that asserts each permission set
exactly rather than by subset, so widening a role is a visible change rather than a quiet one.

A portal wanting a different split of rights creates a group of its own. Nothing here narrows what
an administrator may define; it sets what they start with. The rights on a shipped role belong to
the framework and are restored on every update, so a local edit to one does not survive.

The Portal Administrator holds no right to edit a group. Membership is edited on a person's record
instead, because a role that can edit groups can rewrite its own rights.

Any right to change a person is a right over the fields that make somebody a superuser, unless the
form says otherwise. The Person administration form drops `is_superuser`, `is_staff` and `password`
for anybody who is not a superuser, and a test asserts a role holder cannot set the flag on
themselves or on anyone else.
