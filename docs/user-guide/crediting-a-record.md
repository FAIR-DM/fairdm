# Crediting a record

Every project, dataset, sample and measurement has a **Contributors** tab beside its overview. It
lists the people and organizations credited on the record, and it is where the people who manage
the record change who is credited.

## What the tab shows

People are listed in the main column, each with the contribution roles they hold on the record.
Organizations are listed beside them, each by its logo and its name, and each leads to the
organization's own page. The two lists keep their own order, which is the order the record names
its people and organizations in, its citation included.

The search box above the lists narrows both by name. A list with nobody in it says so.

The Contributors tab opens exactly when the record's overview does. A private record's tab, and
every page of it, answers anyone who may not open the record as if the record did not exist. Only
people who manage the record are offered anything for changing it. Everyone else who may open the
record sees the two lists and nothing more, and a request for one of the changing pages is
refused: a visitor is sent to sign in, and a signed-in person who does not manage the record is
told they may not.

## What each level allows

Each person listed on a record holds one level, and each level includes the ones before it.

| Level | What the person may do |
|---|---|
| View | Open the record and every tab and page of it, even while it is private. |
| Edit | Also change the record and the data in it: its details, descriptions, dates, identifiers and keywords, and the samples and measurements in a dataset. |
| Manage | Also change the record's contributors and their levels, change its visibility and the record it sits under, publish it and delete it. |

A contribution role says how a person took part. It never gives or takes away a level, and
changing a person's roles leaves their level as it was.

An organization holds no level. Being a member, administrator or owner of an organization that is
credited on a record gives no access to it, and neither does being credited from one.

### Levels reach the records beneath

A level on a project applies to every dataset in it, and to the samples and measurements in those
datasets. A level on a dataset applies to its samples and measurements. A level never reaches the
record above: a person listed only on a dataset can open that dataset and cannot open, edit or
manage its project, even when the project is private.

A person who is listed on a record and also holds a level from the record above holds the higher
of the two. The Contributors tab shows a person who manages a record everyone who holds a level on
it from a record above, with the level and the record it comes from. Those levels are changed on
the record above, not here, and the tab does not let you lower one of them.

## Who may change the contributors

A person manages a record when they hold the manage level on it, or on the record above it: a
project's managers manage its datasets, and a dataset's managers manage its samples and
measurements. People who can change every record of that kind in the portal, such as a Data
Curator, manage them too, without being listed.

A person who can edit a record, and one who can only view it, cannot add, edit or remove a
contributor. Only people who manage a record see what level anyone holds on it.

## Letting a colleague into a private record

1. Open the private record's **Contributors** tab. You need to manage it.
2. Choose **Add person** and add your colleague. They start at the view level, so they can open the
   record and cannot change it.
3. To let them change the record, choose **Edit** beside them, choose the **Edit** level and save.
   Choose **Manage** to let them manage the contributors too.
4. To close the record to them again, choose **Remove** beside them. Unless they hold a level on
   the record above, they are treated like any other signed-in person who is not a contributor,
   and the private record answers them as if it did not exist.

A level can be set for a person who has no active account yet. It is kept and takes effect when
their account is active, and the tab tells you that it has not taken effect yet.

Whoever creates a project or a dataset in the portal is listed on it at the manage level, with the
roles Creator, Project member and Contact person. A superuser who creates one is not listed,
because a superuser cannot be a contributor.

## Adding a person or an organization

1. Open the record's **Contributors** tab.
2. Choose **Add person** above the people, or **Add organization** above the organizations.
3. Find the contributor in one of the three ways below.
4. For a person, choose the organization they are credited from (see below).
5. Confirm. You arrive on the page where you set the contributor's roles.

The page offers the three ways side by side as tabs. Moving between them does not reload the page,
and what you typed or found in one is still there when you come back. A search stays on the tab you
searched in, and each tab keeps its own search.

A person who is added holds the view level and nothing more, so on a private record they can open
it and cannot change it. Their contribution roles say how they took part and give them no access.
Organizations are credited only: they hold no access, and their members gain none from the credit.
Nobody is invited or emailed when they are added.

Superusers cannot be credited as contributors. If you choose one, the page tells you so and adds
nobody.

### Someone already in the portal

Search the portal by name, or by part of a name, and choose the person or the organization. When
there are more matches than the page lists, it says so: add more of the name to narrow the search.

Someone who is already credited on the record is marked in the search results and cannot be added
a second time. A contributor appears on a record once.

### Someone in ORCID or ROR

For a person, search ORCID by name or by ORCID iD. For an organization, search ROR by name or by
ROR ID. While the search runs the page says it is searching. Each match shows enough to tell
similar names apart: for a person the institution ORCID lists, and for an organization its kind
and where it is. Organizations that ROR has withdrawn and people with no public name are not
listed. When there are more matches than the page lists, it says so.

Choose a match to see it on its own, then add it. The portal fetches the record from the registry
again when you add it, and makes a profile with the name and the identifier from that record. A
person made this way has no email address and no account, and can claim the profile later by
signing in with ORCID. Nothing else is copied from the registry when the profile is made.

If the portal already holds a profile with that ORCID iD or ROR ID, that profile is used and no
second one is made. A profile is never matched by name alone, so two people who share a name stay
two profiles.

When you choose a person from ORCID, the first current employer ORCID lists is offered as the
organization they are credited from.

When the registry cannot be reached, the tab says that searching it is unavailable. Searching the
portal and entering someone by hand still work.

### Someone entered by hand

For a person with no profile and no ORCID iD, enter a given name and a family name. The page does
not ask for an email address, and the person made has none and no account. They can claim the
profile later by signing in with ORCID.

For an organization, enter its name, and optionally a city, a country and a website. Give the
country by name or by its two-letter code. A country the portal does not recognise is refused.

If a person's name is the same as a profile already in the portal, the page lists those profiles
first. If one of them is who you mean, choose them instead, so that their work stays on one
profile. Two people can share a name, so you can still make the new profile. An organization with
the same name as one in the portal is never made twice: the page offers the existing one and adds
nothing until you choose it.

When a submission is refused, nothing is made or added, each field at fault says what is wrong, and
everything else you entered stays where it was.

## The organization a person is credited from

When you add a person you are asked which organization they are credited from on this record, the
one they were at when they did the work. The person's primary affiliation is selected to begin
with, and their other affiliations, past and present, are offered beneath it. You can also choose
another organization by typing its name, or choose none. A name the portal does not have yet makes
a new organization.

The organization is listed among the record's organizations, once, however many people on the
record are credited from it. The person is shown with it on the Contributors tab.

It is kept with the record and does not follow the person's profile. If the person later moves to
another institute, the record still names the one you chose, so a dataset made at one institute
goes on saying so. A person added with no organization is shown with none, whatever their profile
says. Choosing an organization for a record adds nothing to the person's own affiliations.

To change it later, choose **Edit** beside the person and pick a different organization or none.
Only that changes. Their roles and what they may do on the record stay as they were.

## Every record keeps a manager

A record always has someone who can manage it. The portal refuses to remove the last person who
can, and to lower their level below manage, so that a record is never left with nobody to look
after it. The refusal applies to everyone, a superuser and a Data Curator included. Nothing is
changed when it happens: the edit page shows the refusal beside the level, and the page for
removing a person says so and offers no way to go ahead. Give someone else the manage level first,
and the change can then be made.

Only people who can manage the record count. A person counts when they can sign in and hold the
manage level on the record or on the record above it. So a sample's only listed manager can be
removed when someone manages its dataset, and a person who has no account yet does not count, even
at the manage level. Holding a role in the portal, such as Data Curator, does not count either.
Raising someone on a record that has no manager at all is always allowed. The rule only refuses a
change that takes a record from having a manager to having none.

The same holds when a record is moved. A dataset cannot be moved to another project, and a sample
or a measurement cannot be moved to another dataset, if nobody would then be able to manage it
there. The form shows the refusal beside the project or dataset field. A record that is moved keeps
the people listed on it, and a person who manages the new project or dataset manages it too, so a
move is accepted when someone who can sign in would still manage the record afterwards.

When two profiles are merged and both are listed on a record, one entry remains, at the higher of
the two levels. A person who was listed on a record the other was not keeps that entry and its
level.

## Setting a contributor's roles

Choose **Edit** beside a contributor. The roles offered are the ones the portal groups for that
kind of record, so a dataset offers different roles from a sample. Tick the roles that describe
what the contributor did and save. For a person the same page sets the organization they are
credited from and their level, and all of it is saved together. The level cannot be set below what
the person holds from a record above. No level is offered for an organization.

A contributor does not need a role. One who has none is listed without one. Changing a
contributor's roles never changes what they may do on the record.

## Removing a contributor

Choose **Remove** beside a contributor. The page says what removing them does and waits for you to
confirm. Once you do, the contributor is no longer credited on the record or named wherever the
record names its contributors, and a person loses the access they held through being listed on it.
Access they hold through a record above stays, and is changed on that record's own tab.

If you add them again later they start with the view level and no roles, and you are asked for
their organization again.

### Removing an organization

An organization cannot be removed while anyone on the record is credited from it. The tab says so
in place of offering removal, and asking for it directly changes nothing and names the people.
Change their organization or remove them, and the organization can then be removed.

An organization stays on the record when the last person credited from it leaves or is credited
from elsewhere. It is removed by hand, like any other organization with nobody credited from it.
If an organization is deleted from the portal, the people credited from it stay on the record and
are shown with none.
