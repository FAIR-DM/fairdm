# Feature Specification: Contributors and access are managed on every core record

**Feature Branch**: `022-record-contributors-and-access`

**Created**: 2026-10-02

**Status**: Draft

**Goals**: G4: contributions can be recorded and revised against any object in the core model.
G8: portal roles and their permissions ship with the framework, so running a portal is a standard
job rather than a bespoke setup.

**Roadmap**: R19, contributions can be managed on every core record. This feature also delivers the
per-record half of R15 that specification 017 left open: a record's creator gains rights over what
they created, and rights over a project or dataset carry to the records beneath it.

**Input**: Contributors can be added, edited and removed on a project and nowhere else. A dataset,
a sample and a measurement can be credited in principle and not in practice. Separately, who may
see or change a record is decided by rights that can only be granted in the administration
interface, so a research team cannot let a colleague into its own private dataset. The Contributors
tab should exist on projects, datasets, samples and measurements, and it should be where access to
the record is controlled. Someone with the right to do so adds a contributor, edits one or removes
one. Editing a contributor sets both their contribution roles and what they may do on that record.

## Clarifications

### Session 2026-10-01 and 2026-10-02: the maintainer's rulings

- Q: What can a newly added contributor do on the record? → A: View it. Anything more is given
  deliberately afterwards.
- Q: What happens to a contributor's rights when they are removed? → A: They go with the
  contributor.
- Q: Who can manage a record nobody has been given rights over yet? → A: Whoever creates a record
  becomes a contributor with full rights over it, so no record starts with nobody able to manage
  it.
- Q: Can a record be left with nobody able to manage it? → A: No. The last contributor who can
  manage a record cannot be removed or downgraded.
- Q: An organization is credited on a record. Do its members gain anything? → A: No. Rights apply
  to people. An organization gets credit and nothing else.
- Q: Does a person holding a portal role need to be a contributor to act on a record? → A: No.
  Portal roles keep working on every record without their holders being contributors.
- Q: Can somebody who is not a contributor be let into a private record some other way? → A: Not
  for now. Nobody outside the portal's staff gets into a private record without being listed as a
  contributor.
- Q: Is there a separate page for granting access? → A: No. Access is set per contributor in the
  Contributors tab.

### Session 2026-10-06: the maintainer's rulings on a working prototype

- Q: Are people and organizations one list? → A: No. People are listed in the main column and
  organizations in a narrower column beside it. Each list has its own order.
- Q: Is adding a contributor one page? → A: No. Adding a person and adding an organization are
  separate pages, each reached from its own list.
- Q: Must a contributor already have a profile in the portal? → A: No. A person can be found in the
  portal, looked up in ORCID, or entered by hand. An organization can be found in the portal,
  looked up in ROR, or entered by hand. The three ways are offered side by side on one page, and
  moving between them does not reload it.
- Q: Which organization is a person shown with on a record? → A: The one they were at for that
  work. It is chosen when the person is added and can be changed later. It defaults to their
  primary affiliation, and may be any of their affiliations past or present, any other
  organization, or none. Someone who moved from one institute to another is still credited from the
  first on the dataset they made there.
- Q: Does that organization appear on the record? → A: Yes. It is listed with the record's
  organizations.
- Q: When can an organization be removed from a record? → A: Only when nobody on the record is
  credited from it. Otherwise the removal is refused and the people are named.
- Q: What does an organization's entry on the tab show? → A: Its logo and its name, and nothing
  else.
- Q: Rights are three levels, they flow downward, everything on the tab needs the manage level, and
  a colleague added only for access is listed with no role. Are these right? → A: Yes. All four
  were on the screens that were approved.

### Session 2026-10-02 and 2026-10-06: settled while writing the specification

- Q: What can be set as a contributor's rights on a record? → A: One of three levels, each
  including the one before it. View opens the record while it is private. Edit also changes the
  record and the data in it. Manage also changes its contributors and their access, changes its
  visibility and deletes it. "Full rights" is manage, and "downgraded" means moved to a lower
  level.
- Q: Which contribution roles are offered on each record type? → A: The ones the roles vocabulary
  already groups for that type. This feature adds and removes none.
- Q: Does a contribution role give any rights? → A: No. A contribution role is credit and decides
  nothing about what its holder may do, as `CONTEXT.md` already says. This is the answer to the
  open question of which roles confer which rights: none do.
- Q: Does a right over a project or dataset reach the records beneath it? → A: Yes. A person's
  level on a project applies to its datasets, and a person's level on a dataset applies to its
  samples and measurements. A record's own Contributors tab can raise a person above what they
  hold from above and cannot lower it.
- Q: Who may change a record's contributors? → A: People who can manage the record, and people
  holding the Data Curator portal role, which specification 017 gives the right to change any
  research record.
- Q: Where a record names people and organizations together, as in a citation, how do the two
  orders combine? → A: People first, in their order, then organizations in theirs.
- Q: Is the organization a person is credited from read from their profile? → A: No. It is kept
  with the record, so a later change of affiliation never changes a record made before it.
- Q: What happens to an organization that was listed because a person is credited from it, when
  that person leaves the record or is credited from somewhere else? → A: It stays. It no longer has
  anyone credited from it, so it can be removed by hand.
- Q: A person looked up in ORCID, or an organization looked up in ROR, is already in the portal.
  What happens? → A: The existing profile is used. No second one is made.
- Q: What is kept about a person or organization entered by hand? → A: A person's name and nothing
  else. No email address is asked for: an address stored on a profile nobody has claimed could be
  used to take the profile over through the portal's password reset. An organization's name, and
  its city, country and website if given. The person has a profile and no account.
- Q: When the last-manager rule is applied, who counts? → A: A person with an active account who
  can manage the record, whether they are listed on it or hold that level from a record above.
  People who can act only through a portal role do not count, so a record never depends on portal
  staff to stay manageable.
- Q: What happens to rights people already hold when a portal is upgraded? → A: Nobody loses
  anything. A person who holds rights over a record keeps the nearest level that covers them, and
  is listed as a contributor on it if they were not already.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A research team credits the people and organizations behind any record (Priority: P1)

A data manager opens a dataset their team is preparing and goes to its Contributors tab. It shows
the people credited on the dataset in one list and the organizations in another beside it. They add
three colleagues who are already in the portal, give each the contribution roles that describe what
they did, correct a role that was wrong, and remove someone who was added by mistake. They add the
funder as an organization in its own right. Later they do the same on one sample, to credit the
person who collected it, and on one measurement, to credit the person who made it. On each record
the roles on offer are the ones that make sense for that kind of record.

**Why this priority**: A dataset is the unit that gets cited, and today it cannot be credited
through the portal at all. This story is the whole of what R19 asks for, and it is useful on its
own even on a portal where every record is public.

**Independent Test**: Load development data. Sign in as an account that can manage a seeded
dataset. On the dataset, then on one of its samples, then on one of its measurements, and on a
project, add a person and an organization that are already in the portal, set roles, change them
and remove one contributor. Then open each Contributors tab signed out.

**Acceptance Scenarios**:

1. **Given** a project, a dataset, a sample or a measurement, **When** someone who may open it
   views its page, **Then** a Contributors tab is offered beside the overview. It lists the people
   credited on the record, each with their contribution roles and the organization they are
   credited from there, and separately the organizations on the record.
2. **Given** a person who can manage a record, **When** they open its Contributors tab, **Then**
   the way to add a person is offered with the people and the way to add an organization is offered
   with the organizations, and each leads to its own page.
3. **Given** a person who can manage a record, **When** they add a person or an organization that
   is already in the portal, **Then** that contributor is listed on the record and named wherever
   the record names its contributors.
4. **Given** a person who can manage a record, **When** they edit a contributor, **Then** the
   contribution roles offered are the ones the roles vocabulary groups for that record's type and
   no others.
5. **Given** a person who can manage a record, **When** they change a contributor's roles and save,
   **Then** the record shows the new roles for a person, and the contributor's access is unchanged
   unless it was changed in the same edit.
6. **Given** a contributor already on a record, **When** someone looks for them in order to add
   them again, **Then** they are shown as already listed and no second entry can be made.
7. **Given** a person who can manage a record, **When** they remove a person and confirm, **Then**
   that person is no longer listed on the record or named anywhere the record names its
   contributors.
8. **Given** a contributor added without a contribution role, **When** the record is opened,
   **Then** they are listed as a contributor with no role.
9. **Given** an organization on a record, **When** anyone who may open the record views the tab,
   **Then** the organization is shown by its logo and its name, and leads to the organization's own
   page.
10. **Given** a signed-in person who cannot manage the record, or a visitor who is not signed in,
    **When** they open the Contributors tab of a record they may open, **Then** they see the people
    and the organizations, and nothing for adding, editing, removing or reordering is offered.
    **When** they request any of those directly, **Then** they are refused and nothing is changed.
11. **Given** a sample or measurement of a type a portal has registered, **When** its page is
    opened, **Then** the Contributors tab behaves as it does on any other sample or measurement,
    with no work by the portal's developer.
12. **Given** a record with no contributors, **When** its Contributors tab is opened by someone who
    can manage it, **Then** both lists say they are empty and the ways to add a person and an
    organization are still offered.

---

### User Story 2 - A person is credited from where they were at the time (Priority: P1)

A researcher did the fieldwork for a dataset while at one institute and has since moved to another,
which is now the affiliation on their profile. The dataset's manager adds them and is asked which
organization they should be credited from for this dataset. The researcher's current institute is
offered first, with their earlier ones beneath it. The manager picks the earlier institute. The
dataset shows the researcher with that institute, the institute appears among the dataset's
organizations, and neither changes when the researcher moves again next year.

**Why this priority**: A credit that names the wrong institute is wrong in the citation and wrong
for the institute that paid for the work. Reading the affiliation from the profile would rewrite
every old record each time someone changed jobs.

**Independent Test**: Load development data. On a seeded dataset, add the seeded person who has a
current affiliation and an earlier one, choose the earlier one, and check the person's entry and
the organizations. Change that person's primary affiliation on their profile and check the dataset
again. Then try to remove the organization.

**Acceptance Scenarios**:

1. **Given** a manager adding a person who has affiliations, **When** the person has been chosen,
   **Then** the manager is asked which organization the person is credited from on this record,
   with the person's primary affiliation already selected and their other affiliations, past and
   present, offered.
2. **Given** that choice, **When** the manager wants an organization the person has no recorded
   affiliation with, or no organization at all, **Then** both can be chosen.
3. **Given** a person added with an organization, **When** the record's Contributors tab is opened,
   **Then** the person is shown with that organization, and the organization is among the record's
   organizations.
4. **Given** a person credited from one organization on a record, **When** their primary
   affiliation later changes on their profile, **Then** the record still shows the organization
   that was chosen for it.
5. **Given** a person credited on a record with no organization, **When** the tab is opened,
   **Then** they are shown with none, whatever their profile says.
6. **Given** a person on a record, **When** a manager edits them, **Then** the same choice of
   organization is offered with the current one selected, and saving a different one changes the
   record and nothing else.
7. **Given** an organization that one or more people on a record are credited from, **When** a
   manager looks at it on the tab, **Then** removing it is not offered and the reason is given.
   **When** removal is requested directly, **Then** it is refused, nothing is changed, and the
   people credited from it are named.
8. **Given** an organization nobody on the record is credited from, **When** a manager removes it
   and confirms, **Then** it is no longer listed.
9. **Given** an organization that was listed through one person, **When** that person is removed or
   credited from a different organization, **Then** the organization stays on the record and can
   now be removed.
10. **Given** an organization named as a person's affiliation for a record that is already among
    the record's organizations, **When** the person is added, **Then** the organization appears
    once.

---

### User Story 3 - Someone who is not in the portal yet can be credited (Priority: P2)

A dataset's manager needs to credit a collaborator from another university who has never used the
portal. On the page for adding a person they search the portal first and find nobody. Without
leaving the page they switch to looking the collaborator up by ORCID, find them by name, check the
institution shown against the one they expect, and add them. For a retired technician with no ORCID
iD they switch to entering a person by hand and give a name. Adding an organization works the same
way, with ROR in place of ORCID. Whichever way is used, they land on the new contributor's entry
to say what that contributor did.

**Why this priority**: The first two stories work for anyone already in the portal. Most teams will
meet someone who is not within the first dataset they credit. It comes second only because the
stories before it are what it adds people to.

**Independent Test**: On a seeded dataset, add one person by each of the three ways and one
organization by each of the three ways. Search each registry for something that does not exist.
Enter by hand a name the portal already has.

**Acceptance Scenarios**:

1. **Given** the page for adding a person, **When** it is opened, **Then** three ways are offered:
   someone already in the portal, someone looked up in ORCID, and someone entered by hand. The page
   for adding an organization offers the portal, ROR, and entry by hand.
2. **Given** either page, **When** the manager moves from one way to another, **Then** the page is
   not reloaded and what was typed or found in the first is still there on return.
3. **Given** a search in one of the ways, **When** it returns, **Then** the manager is still on
   that way.
4. **Given** a search of ORCID by name or by ORCID iD, **When** there are matches, **Then** each
   shows enough to tell namesakes apart, and one can be chosen. **When** there are none, **Then**
   the page says so and the other ways remain available.
5. **Given** a search of ROR by name or by ROR ID, **When** there are matches, **Then** each shows
   enough to tell similar organizations apart, and one can be chosen.
6. **Given** a search of a registry that is still running, **When** the manager is waiting,
   **Then** the page shows that it is searching.
7. **Given** a person chosen from ORCID, **When** they are added, **Then** a profile is made for
   them with their name and ORCID iD, they are on the record, and they have no account.
8. **Given** an organization chosen from ROR, **When** it is added, **Then** a profile is made for
   it with its name and ROR ID and it is on the record.
9. **Given** a match from ORCID or ROR that the portal already holds under the same identifier,
   **When** it is added, **Then** the existing profile is used and no second one is made.
10. **Given** a person entered by hand with a given name and a family name, **When** they are
    added, **Then** a profile is made for them with no account and they are on the record.
    **When** either name is missing, **Then** nothing is made and the field says what is needed.
11. **Given** a person entered by hand whose name matches a profile already in the portal,
    **When** the manager submits, **Then** the matching profiles are offered before anything is
    made, and the manager can still make the new profile.
12. **Given** an organization entered by hand whose name matches one already in the portal,
    **When** the manager submits, **Then** the existing organization is offered and no second one
    is made.
13. **Given** a person being added by any of the three ways, **When** they are added, **Then** the
    organization they are credited from on this record is asked for as in the previous story.
14. **Given** a contributor added by any way, **When** the adding is done, **Then** the manager
    arrives where that contributor's roles, and a person's access, are set.
15. **Given** a registry that cannot be reached, **When** the manager searches it, **Then** the
    page says the search is unavailable, and the portal search and entry by hand still work.

---

### User Story 4 - A team lets a colleague into its own private record (Priority: P1)

A principal investigator has a private dataset that a new postdoc needs to work on. They open the
dataset's Contributors tab and add the postdoc, who can now open the dataset and read it. A week
later the investigator edits the postdoc's entry and raises them to the level that lets them change
the dataset, and its samples and measurements with it. When a visiting student's stay ends, the
investigator removes them, and the student can no longer open the dataset. At no point does anyone
ask a portal administrator for anything.

**Why this priority**: Without this, a private record is usable only by its creator and by portal
staff, and every other grant goes through the administration interface. It is the reason the
Contributors tab is where access lives.

**Independent Test**: Load development data. Sign in as the manager of a seeded private dataset,
add a seeded person who holds no portal role, and confirm as that person that the dataset opens and
cannot be changed. Raise them a level and confirm they can change it and one of its samples. Remove
them and confirm they are refused.

**Acceptance Scenarios**:

1. **Given** a private record, **When** a person is added to it as a contributor, **Then** that
   person can open the record and cannot change it.
2. **Given** a person who can manage a record, **When** they edit a contributor who is a person,
   **Then** they can set that person's level to view, edit or manage, in the same place they set
   the contribution roles.
3. **Given** a contributor at the edit level, **When** they use any of the record's pages for
   changing it or its data, **Then** they succeed, and they are still refused changing its
   contributors, changing its visibility and deleting it.
4. **Given** a contributor at the manage level, **When** they change the record's contributors,
   change its visibility or delete it, **Then** they succeed.
5. **Given** a contributor whose level is lowered, **When** they next try something only the higher
   level allows, **Then** they are refused.
6. **Given** a contributor who is removed from a record, **When** they next request the record
   while it is private, **Then** they are treated like any other signed-in person who is not a
   contributor, unless they still hold a level from a record above it.
7. **Given** an organization on a private record, **When** a member of that organization who is
   not themself a contributor requests the record, **Then** they are refused. **When** someone who
   can manage the record edits the organization's entry, **Then** no level is offered for it.
8. **Given** a person at some level on a dataset, **When** they open one of its samples or
   measurements, **Then** they hold the same level there without being listed on it. The same holds
   for a person on a project and the datasets in it.
9. **Given** a person who holds a level on a record from a record above it, **When** someone who
   can manage the record opens its Contributors tab, **Then** that person's access and where it
   comes from are shown, and it cannot be lowered or removed from this record.
10. **Given** a person listed on a dataset inside a private project they hold nothing on, **When**
    they open the dataset, **Then** it opens, and the project stays closed to them.
11. **Given** a signed-in person who is not a contributor on a private record or on any record
    above it and holds no portal role, **When** they request the record, any of its tabs or any of
    its editing pages, **Then** they get the same answer as for a record that does not exist.
12. **Given** a public record, **When** anyone opens it, **Then** it opens whatever level they
    hold, and levels still decide who may change and manage it.
13. **Given** a person credited on a record who has no active account, **When** a level is set for
    them, **Then** it is kept and takes effect when they have an active account, and the tab tells
    a manager that it has not taken effect yet.
14. **Given** a person who may open a record and cannot manage it, **When** they view its
    Contributors tab, **Then** nobody's level is shown to them.

---

### User Story 5 - Every record has someone who can manage it (Priority: P2)

A researcher creates a project, then a dataset in it. On both they find themselves already listed
as a contributor who can manage the record, without having done anything. Later they hand the
dataset to a colleague by raising the colleague to manage. They try to remove themself first and
are told they cannot, because nobody else could manage the dataset. Once the colleague can manage
it, the removal goes through.

**Why this priority**: The stories before this one assume someone can manage each record. This one
makes that true from the moment a record exists and keeps it true. It follows them because existing
records already have a creator with rights, so they can be shown without it.

**Independent Test**: Sign in as a seeded person with no portal role. Create a project and a
dataset, and check both Contributors tabs. Try to remove and to lower the only manager. Add a
second manager and try again.

**Acceptance Scenarios**:

1. **Given** a signed-in person who creates a project, dataset, sample or measurement through the
   portal, **When** the record is saved, **Then** they are listed on it as a contributor at the
   manage level.
2. **Given** a record with exactly one person who counts as able to manage it, **When** anyone
   tries to remove that contributor or lower their level, **Then** the change is refused, nothing
   is changed, and the reason is given.
3. **Given** a record with two people who count as able to manage it, **When** one of them is
   removed or lowered, by themself or by the other, **Then** the change is saved.
4. **Given** a sample whose only listed manager is being removed, **When** somebody else can manage
   the sample through its dataset, **Then** the removal is saved.
5. **Given** two managers who each remove the other at the same moment, **When** both requests
   arrive, **Then** at most one is saved and the record still has someone who can manage it.
6. **Given** a record whose only manager is a person without an active account, **When** a second
   person is raised to manage, **Then** the second person counts and the first does not, so the
   second cannot then be removed or lowered.
7. **Given** a portal brought up to date from a version before this feature, **When** any person
   who could open, change or delete a record before the upgrade tries the same thing after it,
   **Then** they still can, and they are listed as a contributor on that record.

---

### User Story 6 - The team decides the order its contributors are named in (Priority: P2)

A dataset is about to be cited in a paper, and the order of its authors matters to the people on
it. The dataset's manager opens the Contributors tab, moves the lead author to the top of the
people and the supervisor to the end, and puts the host institute ahead of the funder among the
organizations. The citation on the overview now names them in that order.

**Why this priority**: Order decides how a record is cited, and a wrong order is a real grievance.
It comes after the stories that create the lists it sorts.

**Independent Test**: Load development data. Sign in as the manager of a seeded dataset with
several people and several organizations, change the order of each, then read the overview and the
citation.

**Acceptance Scenarios**:

1. **Given** a record with several people, **When** someone who can manage it moves one of them
   earlier or later, **Then** the tab lists the people in the new order for every viewer, and the
   organizations are unmoved.
2. **Given** a record with several organizations, **When** someone who can manage it moves one of
   them earlier or later, **Then** the tab lists the organizations in the new order, and the people
   are unmoved.
3. **Given** a record whose contributors have been reordered, **When** its overview or its citation
   names people, **Then** those it names appear in the people's order. **When** it names
   organizations too, **Then** they follow the people, in the organizations' order.
4. **Given** a record with contributors in a set order, **When** a person is added, **Then** they
   are placed last among the people. **When** an organization is added, **Then** it is placed last
   among the organizations. Nobody else moves.
5. **Given** a record with contributors in a set order, **When** one is removed or has their roles,
   organization or level changed, **Then** the others keep their order.
6. **Given** someone who cannot manage the record, **When** they request a change of order,
   **Then** they are refused and the order is unchanged.
7. **Given** a manager moving contributors without a pointing device, or without dragging,
   **When** they move one, **Then** they can.

---

### User Story 7 - Portal staff can step in on any record (Priority: P3)

A research team's only manager has left the institution and nobody else can add people to their
dataset. A data curator opens the dataset, which they can do without being listed on it, goes to
the Contributors tab and raises one of the remaining contributors to manage. The curator is not
added to the dataset by doing so and does not appear on it.

**Why this priority**: It is the route out when a record's own team is stuck. Specification 017
already gives the role its rights, so this story mostly confirms they reach the Contributors tab.

**Independent Test**: Load development data. Sign in as the seeded Data Curator and manage the
contributors of a private dataset that account is not listed on. Repeat as the seeded Community
Manager, Developer and Portal Administrator accounts.

**Acceptance Scenarios**:

1. **Given** a person holding the Data Curator portal role, **When** they open any record, private
   or public, **Then** they can view it, change it and manage its contributors without being a
   contributor on it.
2. **Given** a data curator who changes a record's contributors, **When** the record is opened,
   **Then** the curator is not listed as a contributor and nothing marks the change as theirs.
3. **Given** a record with nobody who counts as able to manage it, **When** a data curator raises a
   contributor to manage, **Then** the change is saved.
4. **Given** a data curator, **When** they try to remove or lower the last person who counts as
   able to manage a record, or to remove an organization people on the record are credited from,
   **Then** they are refused like anyone else.
5. **Given** a person holding only the Community Manager or the Developer portal role, **When**
   they request a private record they are not a contributor on, **Then** they are refused.
6. **Given** a person removed from the Data Curator role, **When** they next request a private
   record they are not a contributor on, **Then** they are refused.

---

### Edge Cases

- A person may hold different levels on a record and on the record above it. The higher one
  applies.
- A measurement may sit in a different dataset from its sample. It follows its own dataset, and a
  level on the sample's dataset gives nothing over it.
- A dataset that belongs to no project has nothing above it. Only the people listed on it, and the
  holders of portal roles, have any rights over it.
- A record moved to another project or dataset loses whatever people held on it through the old
  parent and gains what the new parent gives. If the move would leave it with nobody who counts as
  able to manage it, the move is refused.
- A contributor may be removed while they have the record open. Their next request is decided by
  what they hold at that moment.
- A manager may lose that level while a change to the contributors is half made. The save is
  refused and nothing is changed.
- A person's account may be deactivated while they are the only one who counts as able to manage a
  record. The record is then in the state story 7 exists for, and nothing is removed from it.
- Two profiles for the same person may be merged. The merged person holds the higher of the two
  levels on each record, appears on it once, and keeps the organization the surviving entry was
  credited from.
- Two organizations may be merged. People credited from either on a record are then credited from
  the one that remains, and it appears on the record once.
- A person who is removed and later added again starts at the view level with no roles, and their
  organization is asked for again.
- An organization a person is credited from on a record may be deleted from the portal. The person
  stays on the record with no organization.
- The organization typed for a person's credit may not be in the portal. It is made as a new
  organization with that name.
- A search of the portal, of ORCID or of ROR may match many entries. The page stays usable and says
  when there are more than it shows.
- An ORCID record may have no public name, and a ROR record may be withdrawn. Neither can be
  chosen.
- A record with hundreds of people stays usable: the tab can be searched by name, and a change to
  one contributor does not disturb the rest.
- A contributor's name may be very long or in a non-Latin script. The tab does not break at any
  breakpoint.
- An organization may have no logo. Its initials stand in for it.
- A record that does not exist, and a private record the viewer may not open, give the same answer
  on the Contributors tab as on the overview.

## Requirements *(mandatory)*

### Functional Requirements

**The Contributors tab**

- **FR-001**: Projects, datasets, samples and measurements MUST each have a Contributors tab beside
  the overview, including every sample and measurement type a portal registers, with no work by the
  portal's developer.
- **FR-002**: The tab MUST list the record's people and its organizations as two separate lists,
  each in its own order, to anyone who may open the record.
- **FR-003**: Each person MUST be shown with their contribution roles on the record and the
  organization they are credited from there, if any.
- **FR-004**: Each organization MUST be shown by its logo and its name and nothing more, and MUST
  lead to the organization's own page. An organization without a logo MUST still be recognisable.
- **FR-005**: The tab MUST be searchable by contributor name across both lists.
- **FR-006**: Each person's level, the access people hold from a record above, and every control
  for changing contributors MUST be shown only to someone who may manage the record.
- **FR-007**: Managing contributors MUST happen on the tab and the pages it leads to. It MUST NOT
  appear as an entry in the Manage menu, as a page action or as an overview card, and there MUST
  NOT be a separate page for granting access.
- **FR-008**: Where a record's overview links to its contributors, the link MUST lead to this tab.
- **FR-009**: An empty list MUST say that it is empty, and MUST still offer a manager the way to
  add to it.

**Adding a contributor**

- **FR-010**: Adding a person and adding an organization MUST be separate pages, each reached from
  its own list on the tab.
- **FR-011**: The page for adding a person MUST offer three ways: a person already in the portal, a
  person looked up in ORCID, and a person entered by hand. The page for adding an organization MUST
  offer an organization already in the portal, one looked up in ROR, and one entered by hand.
- **FR-012**: Moving between the three ways MUST NOT reload the page or discard what was entered or
  found in another. A search MUST leave the manager on the way they searched in.
- **FR-013**: The portal search MUST match by name and MUST mark the people or organizations
  already on the record, which MUST NOT be addable again. A contributor MUST appear on a record at
  most once.
- **FR-014**: The ORCID search MUST accept a name or an ORCID iD, and the ROR search a name or a
  ROR ID. Each match MUST show enough to tell it from others of a similar name. While a search is
  running the page MUST show that it is. When nothing matches the page MUST say so.
- **FR-015**: When a registry cannot be reached, the page MUST say that its search is unavailable,
  and the other two ways MUST keep working.
- **FR-016**: Adding a match from ORCID MUST make a person with that name and ORCID iD and no
  account. Adding a match from ROR MUST make an organization with that name and ROR ID. Where the
  portal already holds a profile with the same identifier, that profile MUST be used.
- **FR-017**: A person entered by hand MUST have a given name and a family name, and MUST be made
  with no account and no email address. The page MUST NOT ask for one. An organization entered by
  hand MUST have a name, and MAY have a city, a country and a website.
- **FR-018**: When a person entered by hand has the same name as a profile in the portal, the
  matching profiles MUST be offered before anything is made, and making the new profile MUST remain
  possible. When an organization entered by hand has the same name as one in the portal, the
  existing one MUST be offered and no second one made.
- **FR-019**: When a submission is refused, nothing MUST be made or added, each field at fault MUST
  say what is wrong, and everything else that was entered MUST remain.
- **FR-020**: After a contributor is added, the manager MUST arrive where that contributor's roles,
  and a person's organization and level, are set.

**The organization a person is credited from**

- **FR-021**: A person's entry on a record MUST carry the organization they are credited from on
  that record, or none.
- **FR-022**: That organization MUST be asked for whenever a person is added, by any of the three
  ways, and MUST be changeable when the person is edited.
- **FR-023**: The choice MUST offer the person's affiliations, past and present, with their primary
  affiliation selected to begin with. It MUST also allow any other organization, and no
  organization. An organization that is not in the portal MUST be made from the name given.
- **FR-024**: The organization MUST be kept with the record. A later change to the person's
  affiliations or primary affiliation MUST NOT change it, and a person credited with no
  organization MUST be shown with none.
- **FR-025**: An organization a person is credited from on a record MUST be among that record's
  organizations, once.
- **FR-026**: An organization MUST NOT be removable from a record while any person on that record
  is credited from it. The tab MUST say so in place of offering removal, and a direct request MUST
  be refused, change nothing and name those people.
- **FR-027**: An organization MUST stay on a record when the last person credited from it there is
  removed or credited from elsewhere. It MUST then be removable.

**Editing and removing**

- **FR-028**: Someone who may manage a record MUST be able to edit a contributor and remove one, on
  all four record types.
- **FR-029**: Editing a contributor MUST allow setting their contribution roles and, for a person,
  their organization and their level, in one place and saved together.
- **FR-030**: The contribution roles offered MUST be those the roles vocabulary groups for the
  record's type. A role from another type's group MUST be refused.
- **FR-031**: A contributor MAY hold no contribution role.
- **FR-032**: Removing a contributor MUST ask for confirmation first and MUST say what goes with
  them.
- **FR-033**: Every change to a record's contributors MUST be checked when it is requested and
  again when it is saved. A request from someone who may not manage the record MUST be refused and
  change nothing. A visitor who is not signed in MUST be sent to sign in first.

**Levels**

- **FR-034**: A person's rights on a record MUST be one of three levels, each including the one
  before it: view, edit and manage.
- **FR-035**: View MUST let its holder open the record, and every tab and page of it open to an
  ordinary visitor of a public record, while the record is private.
- **FR-036**: Edit MUST also let its holder change the record and the data in it, including every
  editing page the record offers.
- **FR-037**: Manage MUST also let its holder change the record's contributors and their levels,
  change its visibility and delete it.
- **FR-038**: A person newly added as a contributor MUST be at the view level.
- **FR-039**: Removing a contributor MUST remove every right they held on the record through being
  listed on it.
- **FR-040**: A contribution role MUST NOT give, remove or change any right. Changing a
  contributor's roles or organization MUST leave their level as it was.
- **FR-041**: An organization MUST NOT be given a level. Being a member, administrator or owner of
  an organization on a record, or being credited from it elsewhere, MUST give no right over that
  record.
- **FR-042**: A level set for a person without an active account MUST be kept and MUST take effect
  when the account is active. Until then the tab MUST tell a manager that it has not taken effect.
- **FR-043**: Every right over a record that the framework declares MUST be governed by one of the
  three levels. None may be left that nothing checks.

**Rights from the record above**

- **FR-044**: A person's level on a project MUST apply to every dataset in it. A person's level on
  a dataset MUST apply to every sample and measurement in it.
- **FR-045**: Where a person holds a level on a record and another from a record above it, the
  higher MUST apply. A record's own tab MUST NOT be able to lower or remove what a person holds
  from above.
- **FR-046**: A person listed on a record MUST be able to open it at their level whatever the
  visibility of the records above it, and MUST gain nothing over those records from it.
- **FR-047**: The tab MUST show a manager the people who hold a level on the record from a record
  above without being listed on it, with the level and where it comes from.

**Who gets into a private record**

- **FR-048**: A private record MUST open only to people who hold a level on it, directly or from a
  record above, and to holders of a portal role whose rights cover it.
- **FR-049**: Anyone else who requests a private record, any of its tabs or any of its editing
  pages MUST get the same answer as for a record that does not exist.
- **FR-050**: A public record MUST open to everyone. Levels MUST still decide who may change and
  manage it.
- **FR-051**: Every page that decides whether a person may open, change or manage a record MUST
  reach that decision the same way, so that what is not offered is also refused.

**A record always has a manager**

- **FR-052**: A signed-in person who creates a project, dataset, sample or measurement through the
  portal MUST become a contributor on it at the manage level.
- **FR-053**: A removal or a lowering of level that would leave a record with nobody who counts as
  able to manage it MUST be refused, with the reason, whoever asks for it.
- **FR-054**: The people who count for FR-053 MUST be people with an active account who hold the
  manage level on the record, directly or from a record above. Holders of portal roles MUST NOT
  count.
- **FR-055**: FR-053 MUST hold when two changes are requested at the same moment.
- **FR-056**: Moving a record to another project or dataset MUST be refused when it would leave the
  record with nobody who counts as able to manage it.

**Order**

- **FR-057**: Someone who may manage a record MUST be able to move a person earlier or later among
  the record's people, and an organization earlier or later among its organizations. Moving one
  MUST be possible without dragging.
- **FR-058**: Wherever a record names people, including its citation, those named MUST appear in
  the people's order. Where it names organizations as well, they MUST follow the people, in the
  organizations' order.
- **FR-059**: A newly added person MUST be placed last among the people and a newly added
  organization last among the organizations. Removing or editing a contributor MUST NOT change the
  order of the others.

**Portal roles**

- **FR-060**: A person holding the Data Curator portal role MUST be able to view and change every
  record and manage its contributors, without being a contributor on it. Doing so MUST NOT add them
  to the record or mark the change as theirs.
- **FR-061**: FR-026 and FR-053 MUST apply to holders of portal roles as they do to anyone else.
  Raising a contributor on a record that has nobody who counts as able to manage it MUST be
  allowed.
- **FR-062**: The rights each portal role holds MUST be the same after this feature as before it.

**Upgrading a portal**

- **FR-063**: Bringing a portal up to date MUST leave every person able to do on every record what
  they could do before. A person holding rights over a record MUST be given the lowest level that
  covers all of them and MUST be listed as a contributor on it.
- **FR-064**: A person already listed as a contributor on a record who held no rights over it MUST
  be at the view level after the upgrade.
- **FR-065**: An organization already recorded with a person's entry on a record MUST be kept as
  the organization they are credited from, and MUST be among the record's organizations after the
  upgrade. A person's entry that has none MUST be left with none.

**Documentation**

- **FR-066**: The documentation for portal users MUST describe how people and organizations are
  added, edited, removed and reordered on a record, how the organization a person is credited from
  is chosen and why it does not follow their profile, what each level allows and how a colleague is
  let into a private record.
- **FR-067**: The documentation for portal administrators MUST say how per-record levels and portal
  roles work together, that an organization's members gain nothing from its credit, and what the
  portal needs in order to search ORCID and ROR.
- **FR-068**: The documentation for portal developers MUST say that a registered sample or
  measurement type gets the Contributors tab without configuration, and how a page of their own
  asks whether a person may view, edit or manage a record.
- **FR-069**: `CONTEXT.md` MUST define the three levels, say that a record's rights flow from the
  record above it, and say that a contribution carries the organization a person is credited from.

### Key Entities

- **Contribution**: the link between a contributor and one project, dataset, sample or measurement.
  One per contributor per record. It carries the contribution roles and a place in the order of the
  record's people or of its organizations. For a person it also carries the level they hold on the
  record and the organization they are credited from there.
- **Contribution role**: the credit a contribution records for how a contributor took part. It is
  drawn from the group of the roles vocabulary for the record's type and carries no rights.
- **Level**: what a person may do on one record: view, edit or manage, each including the one
  before it.
- **Person** and **Organization**: the two kinds of contributor. Only a person can hold a level. A
  person may exist as a profile with no account.
- **Affiliation**: a person's membership of an organization over a period, one of which may be
  their primary affiliation. A person's affiliations are what is offered when their organization
  for a record is chosen. They do not decide it afterwards.
- **Portal role**: one of the four named rights a person can hold across the whole portal. The Data
  Curator role is the one that bears on this feature.
- **Visibility**: whether a record is private or public. A level matters for opening a record only
  while it is private.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A person who can manage a dataset can add a colleague who is already in the portal,
  choose the organization they are credited from, give them a contribution role and place them
  first among the people in under two minutes, on a dataset, a sample, a measurement and a project
  alike.
- **SC-002**: A manager can credit a person who has never used the portal, and an organization the
  portal has never held, without leaving the record's pages and without asking anyone for help.
- **SC-003**: A team can let a colleague into its private dataset, and later take that access away,
  without anyone opening the administration interface.
- **SC-004**: For every seeded account and every seeded record, what the account can open, change
  and manage is exactly what its level on that record, its levels on the records above and its
  portal roles give it.
- **SC-005**: No request by someone who may not manage a record changes its contributors, their
  roles, their organizations, their levels or their order, and none makes a person or an
  organization.
- **SC-006**: Every record created through the portal has at least one person who counts as able to
  manage it from the moment it exists, and no sequence of removals or changes of level through the
  portal leaves a record without one.
- **SC-007**: A member of an organization on a private record, who is not a contributor on it, is
  refused on every page of that record.
- **SC-008**: After a person's primary affiliation changes, every record they were already credited
  on shows the same organization for them as it did before.
- **SC-009**: No record lists a person credited from an organization that is not among that
  record's organizations.
- **SC-010**: After a portal is brought up to date, no person has lost the ability to open, change
  or delete any record they could before.
- **SC-011**: The order set on the Contributors tab is the order people and organizations appear in
  on the record's overview and in its citation, on all four record types.
- **SC-012**: The permissions held by each portal role are the same after this feature as before
  it.
- **SC-013**: The Contributors tab and the two pages for adding do not scroll sideways at widths of
  375, 768, 1024 and 1440 pixels.
- **SC-014**: Each example in the documentation this feature adds or changes runs as written.

## Assumptions

- Specification 018 is delivered: every project, dataset, sample and measurement has an overview
  page for the tab to sit beside.
- The pages for editing a record's details, descriptions, keywords, key dates and identifiers, and
  for deleting it, are specified separately. Each is offered and refused by the levels defined
  here: the edit level for editing pages, the manage level for deleting.
- Which lists a private record appears in for the people who may open it is decided by each list's
  own specification. This feature decides who may open the record.
- Who appears in a record's citation, and how the citation is formatted, stays as specification 018
  has it. This feature decides only the order, and that people come before organizations.
- Reviewing and publishing a dataset is a later feature and says for itself which level it needs.
- Nobody is told when they are added to a record, and there is no way to ask for access to one. A
  manager who adds a colleague passes the address on themself. Asking a record's team for early
  access is part of the contact feature.
- Nobody is invited or emailed by this feature. A person made from ORCID or by hand has a profile
  that the existing claiming process can later attach to an account.
- A profile made from ORCID or ROR takes the name and the identifier. Filling in the rest of it
  from the registry, and keeping it in step afterwards, belong to identifier synchronisation.
- A person's affiliations are edited on their profile, not on this tab. Choosing an organization
  for a record does not add an affiliation to the person.
- A contributor cannot remove themself from a record unless they can manage it.
- Records created by importing data, in the administration interface or in code are not given a
  manager by this feature. Samples and measurements made that way are managed through their
  dataset.
- The administration interface keeps every ability it has today.
- The API's rules about what it serves are unchanged by this feature.
