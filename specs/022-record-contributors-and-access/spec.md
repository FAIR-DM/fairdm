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

### Session 2026-10-02: settled while writing the specification

- Q: What can be set as a contributor's rights on a record? → A: One of three levels, each
  including the one before it. View opens the record while it is private. Edit also changes the
  record and the data in it. Manage also changes its contributors and their access, changes its
  visibility and deletes it. "Full rights" is manage, and "downgraded" means moved to a lower
  level.
- Q: Which contribution roles are offered on each record type? → A: The ones the roles vocabulary
  already groups for that type: project roles on a project, dataset roles on a dataset, sample
  roles on a sample and measurement roles on a measurement. This feature adds and removes none.
- Q: Does a contribution role give any rights? → A: No. A contribution role is credit and decides
  nothing about what its holder may do, as `CONTEXT.md` already says. Roles and access are set side
  by side and neither changes the other. This is the answer to the open question of which roles
  confer which rights: none do.
- Q: Must a contributor hold a contribution role? → A: No. A colleague who only needs to get into a
  private record is added as a contributor with no role. They are listed on the record like anyone
  else.
- Q: Does a right over a project or dataset reach the records beneath it? → A: Yes. A person's
  level on a project applies to its datasets, and a person's level on a dataset applies to its
  samples and measurements. A record's own Contributors tab can raise a person above what they
  hold from above and cannot lower it.
- Q: Who may add, edit, remove and reorder contributors? → A: People who can manage the record, and
  people holding the Data Curator portal role, which specification 017 gives the right to change
  any research record.
- Q: Who decides the order of contributors? → A: The people who can manage the record. The order
  they set is the order the record names its contributors in everywhere, its citation included. A
  new contributor joins at the end.
- Q: Who sees what on the Contributors tab? → A: Anyone who may open the record sees its
  contributors and their contribution roles, in order. Each person's level, and the controls for
  changing anything, are shown only to someone who may manage the record.
- Q: When the last-manager rule is applied, who counts? → A: A person with an active account who
  can manage the record, whether they are listed on it or hold that level from a record above.
  People who can act only through a portal role do not count, so a record never depends on portal
  staff to stay manageable.
- Q: What happens to rights people already hold when a portal is upgraded? → A: Nobody loses
  anything. A person who holds rights over a record keeps the nearest level that covers them, and
  is listed as a contributor on it if they were not already.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A research team credits the people behind any record (Priority: P1)

A data manager opens a dataset their team is preparing and goes to its Contributors tab. They add
the three colleagues who collected the data and the institute that hosted the work, give each the
contribution roles that describe what they did, correct a role that was wrong, and remove someone
who was added by mistake. Later they do the same on one sample, to credit the person who collected
it, and on one measurement, to credit the person who made it. On each record the roles on offer are
the ones that make sense for that kind of record.

**Why this priority**: A dataset is the unit that gets cited, and today it cannot be credited
through the portal at all. This story is the whole of what R19 asks for, and it is useful on its
own even on a portal where every record is public.

**Independent Test**: Load development data. Sign in as an account that can manage a seeded
dataset. On the dataset, then on one of its samples, then on one of its measurements, and on a
project, add a person and an organization, set roles, change them and remove one contributor. Then
open each Contributors tab signed out.

**Acceptance Scenarios**:

1. **Given** a project, a dataset, a sample or a measurement, **When** someone who may open it
   views its page, **Then** a Contributors tab is offered beside the overview, and it lists the
   record's contributors with their contribution roles.
2. **Given** a person who can manage a record, **When** they add a person or an organization on its
   Contributors tab, **Then** that contributor is listed on the record and named wherever the
   record names its contributors.
3. **Given** a person who can manage a record, **When** they edit a contributor, **Then** the
   contribution roles offered are the ones the roles vocabulary groups for that record's type and
   no others.
4. **Given** a person who can manage a record, **When** they change a contributor's roles and save,
   **Then** the record shows the new roles, and the contributor's access is unchanged unless it was
   changed in the same edit.
5. **Given** a contributor already on a record, **When** someone tries to add them again, **Then**
   no second entry is made and the person adding is told the contributor is already listed.
6. **Given** a person who can manage a record, **When** they remove a contributor and confirm,
   **Then** the contributor is no longer listed on the record or named anywhere the record names
   its contributors.
7. **Given** a contributor added without a contribution role, **When** the record is opened,
   **Then** they are listed as a contributor with no role.
8. **Given** a signed-in person who cannot manage the record, or a visitor who is not signed in,
   **When** they open the Contributors tab of a record they may open, **Then** they see the
   contributors and their roles, and nothing for adding, editing, removing or reordering is
   offered. **When** they request any of those directly, **Then** they are refused and nothing is
   changed.
9. **Given** a sample or measurement of a type a portal has registered, **When** its page is
   opened, **Then** the Contributors tab behaves as it does on any other sample or measurement,
   with no work by the portal's developer.
10. **Given** a record with no contributors, **When** its Contributors tab is opened by someone who
    can manage it, **Then** the tab says there are none yet and offers the way to add the first.

---

### User Story 2 - A team lets a colleague into its own private record (Priority: P1)

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
7. **Given** an organization listed as a contributor on a private record, **When** a member of that
   organization who is not themself a contributor requests the record, **Then** they are refused.
   **When** someone who can manage the record edits the organization's entry, **Then** no level is
   offered for it.
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
    them, **Then** it is kept and takes effect when they have an active account.

---

### User Story 3 - Every record has someone who can manage it (Priority: P2)

A researcher creates a project, then a dataset in it. On both they find themselves already listed
as a contributor who can manage the record, without having done anything. Later they hand the
dataset to a colleague by raising the colleague to manage. They try to remove themself first and
are told they cannot, because nobody else could manage the dataset. Once the colleague can manage
it, the removal goes through.

**Why this priority**: The first two stories assume someone can manage each record. This one makes
that true from the moment a record exists and keeps it true. It follows them because existing
records already have a creator with rights, so the first two can be shown without it.

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

### User Story 4 - The team decides the order its contributors are named in (Priority: P2)

A dataset is about to be cited in a paper, and the order of its authors matters to the people on
it. The dataset's manager opens the Contributors tab, moves the lead author to the top and the
supervisor to the end, and checks the citation on the overview, which now names them in that order.

**Why this priority**: Order decides how a record is cited, and a wrong order is a real grievance.
It comes after the stories that create the list it sorts.

**Independent Test**: Load development data. Sign in as the manager of a seeded dataset with
several contributors, change their order on the Contributors tab, then read the overview and the
citation.

**Acceptance Scenarios**:

1. **Given** a record with several contributors, **When** someone who can manage it changes their
   order and the change is saved, **Then** the Contributors tab lists them in the new order for
   every viewer.
2. **Given** a record whose contributors have been reordered, **When** its overview or its citation
   names contributors, **Then** those it names appear in that order relative to each other.
3. **Given** a record with contributors in a set order, **When** a new contributor is added,
   **Then** they are placed last and nobody else moves.
4. **Given** a record with contributors in a set order, **When** one is removed or has their roles
   or level changed, **Then** the others keep their order.
5. **Given** someone who cannot manage the record, **When** they request a change of order,
   **Then** they are refused and the order is unchanged.

---

### User Story 5 - Portal staff can step in on any record (Priority: P3)

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
   able to manage a record, **Then** they are refused like anyone else.
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
  record. The record is then in the state story 5 exists for, and nothing is removed from it.
- Two profiles for the same person may be merged. The merged person holds the higher of the two
  levels on each record and appears on it once.
- A person who is removed and later added again starts at the view level, not the level they had.
- A record with hundreds of contributors stays usable: the tab can be searched by name, and a
  change to one contributor does not disturb the rest.
- A contributor's name may be very long or in a non-Latin script. The tab does not break at any
  breakpoint.
- A record that does not exist, and a private record the viewer may not open, give the same answer
  on the Contributors tab as on the overview.

## Requirements *(mandatory)*

### Functional Requirements

**The Contributors tab**

- **FR-001**: Projects, datasets, samples and measurements MUST each have a Contributors tab beside
  the overview, including every sample and measurement type a portal registers, with no work by the
  portal's developer.
- **FR-002**: The tab MUST list the record's contributors, people and organizations alike, each
  with their contribution roles, in the record's contributor order, to anyone who may open the
  record.
- **FR-003**: The tab MUST be searchable by contributor name.
- **FR-004**: Each person's level, the access people hold from a record above, and every control
  for changing contributors MUST be shown only to someone who may manage the record.
- **FR-005**: Managing contributors MUST happen on the tab. It MUST NOT appear as an entry in the
  Manage menu, as a page action or as an overview card, and there MUST NOT be a separate page for
  granting access.
- **FR-006**: Where a record's overview links to its contributors, the link MUST lead to this tab.

**Adding, editing and removing**

- **FR-007**: Someone who may manage a record MUST be able to add a person or an organization to it
  as a contributor, edit a contributor and remove one, on all four record types.
- **FR-008**: A contributor MUST appear on a record at most once. Adding one who is already listed
  MUST be refused with the reason.
- **FR-009**: Editing a contributor MUST allow setting their contribution roles and, for a person,
  their level, in one place.
- **FR-010**: The contribution roles offered MUST be those the roles vocabulary groups for the
  record's type. A role from another type's group MUST be refused.
- **FR-011**: A contributor MAY hold no contribution role.
- **FR-012**: Removing a contributor MUST ask for confirmation first.
- **FR-013**: Every change to a record's contributors MUST be checked when it is requested and
  again when it is saved. A request from someone who may not manage the record MUST be refused and
  change nothing. A visitor who is not signed in MUST be sent to sign in first.

**Levels**

- **FR-014**: A person's rights on a record MUST be one of three levels, each including the one
  before it: view, edit and manage.
- **FR-015**: View MUST let its holder open the record, and every tab and page of it open to an
  ordinary visitor of a public record, while the record is private.
- **FR-016**: Edit MUST also let its holder change the record and the data in it, including every
  editing page the record offers.
- **FR-017**: Manage MUST also let its holder change the record's contributors and their levels,
  change its visibility and delete it.
- **FR-018**: A person newly added as a contributor MUST be at the view level.
- **FR-019**: Removing a contributor MUST remove every right they held on the record through being
  listed on it.
- **FR-020**: A contribution role MUST NOT give, remove or change any right. Changing a
  contributor's roles MUST leave their level as it was.
- **FR-021**: An organization MUST NOT be given a level, and being a member, administrator or owner
  of an organization listed on a record MUST give no right over that record.
- **FR-022**: A level set for a person without an active account MUST be kept and MUST take effect
  when the account is active.
- **FR-023**: Every right over a record that the framework declares MUST be governed by one of the
  three levels. None may be left that nothing checks.

**Rights from the record above**

- **FR-024**: A person's level on a project MUST apply to every dataset in it. A person's level on
  a dataset MUST apply to every sample and measurement in it.
- **FR-025**: Where a person holds a level on a record and another from a record above it, the
  higher MUST apply. A record's own tab MUST NOT be able to lower or remove what a person holds
  from above.
- **FR-026**: A person listed on a record MUST be able to open it at their level whatever the
  visibility of the records above it, and MUST gain nothing over those records from it.

**Who gets into a private record**

- **FR-027**: A private record MUST open only to people who hold a level on it, directly or from a
  record above, and to holders of a portal role whose rights cover it.
- **FR-028**: Anyone else who requests a private record, any of its tabs or any of its editing
  pages MUST get the same answer as for a record that does not exist.
- **FR-029**: A public record MUST open to everyone. Levels MUST still decide who may change and
  manage it.
- **FR-030**: Every page that decides whether a person may open, change or manage a record MUST
  reach that decision the same way, so that what is not offered is also refused.

**A record always has a manager**

- **FR-031**: A signed-in person who creates a project, dataset, sample or measurement through the
  portal MUST become a contributor on it at the manage level.
- **FR-032**: A removal or a lowering of level that would leave a record with nobody who counts as
  able to manage it MUST be refused, with the reason, whoever asks for it.
- **FR-033**: The people who count for FR-032 MUST be people with an active account who hold the
  manage level on the record, directly or from a record above. Holders of portal roles MUST NOT
  count.
- **FR-034**: FR-032 MUST hold when two changes are requested at the same moment.
- **FR-035**: Moving a record to another project or dataset MUST be refused when it would leave the
  record with nobody who counts as able to manage it.

**Order**

- **FR-036**: Someone who may manage a record MUST be able to change the order of its contributors.
- **FR-037**: Wherever a record names its contributors, including its citation, those named MUST
  appear in that order.
- **FR-038**: A newly added contributor MUST be placed last. Removing or editing a contributor MUST
  NOT change the order of the others.

**Portal roles**

- **FR-039**: A person holding the Data Curator portal role MUST be able to view and change every
  record and manage its contributors, without being a contributor on it. Doing so MUST NOT add them
  to the record or mark the change as theirs.
- **FR-040**: FR-032 MUST apply to holders of portal roles as it does to anyone else. Raising a
  contributor on a record that has nobody who counts as able to manage it MUST be allowed.
- **FR-041**: The rights each portal role holds MUST be the same after this feature as before it.

**Upgrading a portal**

- **FR-042**: Bringing a portal up to date MUST leave every person able to do on every record what
  they could do before. A person holding rights over a record MUST be given the lowest level that
  covers all of them and MUST be listed as a contributor on it.
- **FR-043**: A person already listed as a contributor on a record who held no rights over it MUST
  be at the view level after the upgrade.

**Documentation**

- **FR-044**: The documentation for portal users MUST describe how contributors are added, edited,
  removed and reordered on a record, what each level allows and how a colleague is let into a
  private record.
- **FR-045**: The documentation for portal administrators MUST say how per-record levels and portal
  roles work together, and that an organization's members gain nothing from its credit.
- **FR-046**: The documentation for portal developers MUST say that a registered sample or
  measurement type gets the Contributors tab without configuration, and how a page of their own
  asks whether a person may view, edit or manage a record.
- **FR-047**: `CONTEXT.md` MUST define the three levels and say that a record's rights flow from
  the record above it.

### Key Entities

- **Contribution**: the link between a contributor and one project, dataset, sample or measurement.
  One per contributor per record. It carries the contribution roles, a place in the record's
  contributor order and, for a person, the level they hold on the record.
- **Contribution role**: the credit a contribution records for how a contributor took part. It is
  drawn from the group of the roles vocabulary for the record's type and carries no rights.
- **Level**: what a person may do on one record: view, edit or manage, each including the one
  before it.
- **Person** and **Organization**: the two kinds of contributor. Only a person can hold a level.
- **Portal role**: one of the four named rights a person can hold across the whole portal. The Data
  Curator role is the one that bears on this feature.
- **Visibility**: whether a record is private or public. A level matters for opening a record only
  while it is private.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A person who can manage a dataset can add a contributor, give them a contribution
  role and place them first in the order in under one minute, on a dataset, a sample, a measurement
  and a project alike.
- **SC-002**: A team can let a colleague into its private dataset, and later take that access away,
  without anyone opening the administration interface.
- **SC-003**: For every seeded account and every seeded record, what the account can open, change
  and manage is exactly what its level on that record, its levels on the records above and its
  portal roles give it.
- **SC-004**: No request by someone who may not manage a record changes its contributors, their
  roles, their levels or their order.
- **SC-005**: Every record created through the portal has at least one person who counts as able to
  manage it from the moment it exists, and no sequence of removals or changes of level through the
  portal leaves a record without one.
- **SC-006**: A member of an organization credited on a private record, who is not a contributor on
  it, is refused on every page of that record.
- **SC-007**: After a portal is brought up to date, no person has lost the ability to open, change
  or delete any record they could before.
- **SC-008**: The order set on the Contributors tab is the order contributors appear in on the
  record's overview and in its citation, on all four record types.
- **SC-009**: The permissions held by each portal role are the same after this feature as before
  it.
- **SC-010**: The Contributors tab does not scroll sideways at widths of 375, 768, 1024 and 1440
  pixels.
- **SC-011**: Each example in the documentation this feature adds or changes runs as written.

## Assumptions

- Specification 018 is delivered: every project, dataset, sample and measurement has an overview
  page for the tab to sit beside.
- The pages for editing a record's details, descriptions, keywords, key dates and identifiers, and
  for deleting it, are specified separately. Each is offered and refused by the levels defined
  here: the edit level for editing pages, the manage level for deleting.
- Which lists a private record appears in for the people who may open it is decided by each list's
  own specification. This feature decides who may open the record.
- Who appears in a record's citation, and how the citation is formatted, stays as specification 018
  has it. This feature decides only the order.
- Reviewing and publishing a dataset is a later feature and says for itself which level it needs.
- Nobody is told when they are added to a record, and there is no way to ask for access to one. A
  manager who adds a colleague passes the address on themself. Asking a record's team for early
  access is part of the contact feature.
- A contributor cannot remove themself from a record unless they can manage it.
- Records created by importing data, in the administration interface or in code are not given a
  manager by this feature. Samples and measurements made that way are managed through their
  dataset.
- A person to be added must already have a record in the portal. Creating a new person or
  organization from the tab, and inviting someone by email, are outside this specification.
- The affiliation recorded with a contribution stays editable where it is today and is not changed
  by this feature.
- The administration interface keeps every ability it has today.
- The API's rules about what it serves are unchanged by this feature.
