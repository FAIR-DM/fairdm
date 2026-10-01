# Feature Specification: Editing person and organization profiles in the portal

**Feature Branch**: `020-profile-editing`

**Created**: 2026-10-01

**Status**: Draft

**Goals**: G6: core records can be created and edited by hand through the portal. G8: portal roles
and their permissions ship with the framework, so running a portal is a standard job rather than a
bespoke setup.

**Roadmap**: none. R12 and R16 cover editing projects, datasets, samples and measurements, and no
item covers people or organizations. Specification 009 left the pages a researcher uses to edit a
contributor to a later specification, and 019 shows editing on both overview pages as not available
yet. This is the specification that makes it available.

**Input**: A person with an account needs to edit their own profile from their own page: photo,
name, alternative names, biography, links and languages. An organization's profile needs to be
editable from its page by its owner and administrators: logo, name, alternative names, type, parent
organization, city and country, description, website and links. People holding the Community
Manager portal role can edit any organization's profile the same way, and a person's profile whenever that person does not have an active account. A profile always has
one maintainer: the person it describes while their account is active, and the community managers
in every other state. The Data Curator role is unchanged and has no rights over
people or organizations. Each item on an overview page's completeness checklist leads to the field
that fixes it.

## Clarifications

### Session 2026-10-01

- Q: The request named data curators as the people who edit organization profiles alongside owners.
  Specification 017 gives the Data Curator role rights over research records and nothing over
  people or organizations. Which role edits them? → A: The Community Manager, which 017 already
  gives the right to change person and organisation records. The Data Curator role is not widened.
- Q: Who counts as an organization's administrator? → A: A person whose affiliation to it is of the
  owner or administrator type and has not ended, the same people 019 shows the organization's
  checklist to. An ordinary member, and an owner or administrator whose affiliation has ended, may
  not edit.
- Q: May a community manager edit any person's profile? → A: Only when the person does not have an
  active account. A person with an active account maintains their own profile and nobody else edits
  it in the portal. In any other state the community managers maintain it: a profile nobody has
  claimed, one whose owner has been invited and has not yet signed in, and one whose account has
  been deactivated, whether by its owner or by an administrator.
- Q: An account is deactivated and later made active again. Who maintains the profile then? → A:
  The person, from the moment the account is active again. Whatever a community manager changed in
  between stays as it was left.
- Q: A community manager corrects a person's profile or an organization. Is the edit marked as
  theirs anywhere a reader can see? → A: No. It is an ordinary edit, as 017 ruled for a curator
  correcting a research record. The edit does not change whether the profile is claimed or the account active.
- Q: May an organization be made part of itself, or of one of the organizations beneath it? → A:
  No. Either choice is refused and the editor is told why.
- Q: A field such as an organization's name may have been filled from ROR. May it be edited by
  hand? → A: Yes. Refreshing from ORCID or ROR is not built, so nothing overwrites a hand edit, and
  what happens when a refresh meets one is for the specification that builds refreshing.
- Q: Is a person's name on their profile the same name their credits show? → A: Yes. There is one
  record, so a changed name appears on every credit, list and citation that names the person.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A person edits their own profile (Priority: P1)

A researcher signs in, opens their own profile and sees that their biography and photo are missing.
They follow the edit action in the header, or one of the items on their checklist, and arrive at a
page where they can change their photo, the name they are publicly known by, their other names,
their biography, their links and the languages they work in. They save, land back on their profile
and see the change, and the checklist counts the items now in place.

**Why this priority**: A person's profile is what every credit points at, and the person it
describes is the one who knows what it should say. Today the only way to correct it is to ask
someone with access to the administration interface.

**Independent Test**: Load development data. Sign in as the seeded user with an incomplete profile,
open their own page, follow the edit action, fill in what is missing and save. Then try to reach
the same editing page for another person.

**Acceptance Scenarios**:

1. **Given** a signed-in person on their own profile, **When** the page is shown, **Then** the edit
   action in the header works and leads to the page where the profile is edited.
2. **Given** a person editing their own profile, **When** they change their photo, name,
   alternative names, biography, links or languages and save, **Then** they are returned to their
   profile, told the change was saved, and the profile shows the new values.
3. **Given** a person who changes their name, **When** a record they are credited on is opened,
   **Then** the credit shows the new name.
4. **Given** a person editing their own profile, **When** they clear their name and save, **Then**
   nothing is saved, the field says a name is required, and everything else they typed is still in
   the form.
5. **Given** a person editing their own profile, **When** they enter a link that is not a web
   address, a language the portal does not recognise, or a file that is not an image, **Then**
   nothing is saved and the field in question says what is wrong.
6. **Given** a person with a photo, **When** they remove it and save, **Then** their profile and
   every place that showed the photo show their initials instead.
7. **Given** a person on their own profile whose checklist says the photo, the biography or the
   links are missing, **When** they follow that item, **Then** they arrive at the field that fixes
   it. **When** they fill it in and save, **Then** the checklist counts it as in place.
8. **Given** a signed-in person holding no portal role, **When** they open somebody else's profile,
   **Then** no edit action is offered. **When** they request that profile's editing page directly,
   **Then** they are refused and nothing is changed.
9. **Given** a visitor who is not signed in, **When** they request any profile's editing page,
   **Then** they are sent to sign in, and after signing in the rules above decide whether they may
   continue.
10. **Given** a person editing their own profile, **When** the page is shown, **Then** it offers no
    way to change their email address, password, connected sign-ins, ORCID iD, affiliations, portal
    roles or account status, and says where email, password and connected sign-ins are managed.
11. **Given** a person who leaves the editing page without saving, **When** their profile is opened,
    **Then** nothing has changed.

---

### User Story 2 - An organization's owner and administrators edit its profile (Priority: P2)

The owner of a research institute's record opens its page and sees a checklist saying the logo, the
type and the description are missing. From the management menu, or from a checklist item, they
reach a page where they can change the organization's logo, name, alternative names, type, the
organization it is part of, its city and country, its description, its website and its other links.
An administrator of the same organization can do the same.

**Why this priority**: Organizations are named on projects and as people's affiliations, so an
empty or wrong record shows up widely. It follows the person story because fewer people keep an
organization's record than have a profile of their own, and the editing page is the same shape.

**Independent Test**: Load development data. Sign in as the seeded user who owns an organization,
open that organization, edit and save. Repeat as one of its administrators, then try as an ordinary
member and as someone whose administrator affiliation has ended.

**Acceptance Scenarios**:

1. **Given** an organization's owner or one of its administrators, **When** they open its page,
   **Then** the management menu's action for editing the organization's details works and leads to
   the page where the profile is edited. The menu's other actions are still shown as not available.
2. **Given** an owner or administrator editing an organization, **When** they change its logo,
   name, alternative names, type, parent organization, city, country, description, website or links
   and save, **Then** they are returned to the organization's page, told the change was saved, and
   the page shows the new values.
3. **Given** an organization named as a project's owner or as people's affiliation, **When** its
   name or logo is changed, **Then** those places show the new name and logo.
4. **Given** an editor choosing the organization this one is part of, **When** they choose the
   organization itself or one that is beneath it, **Then** nothing is saved and the field says why.
5. **Given** an editor who clears the parent organization and saves, **When** the page is opened,
   **Then** the organization is shown as part of nothing, and the organizations beneath it are
   unchanged.
6. **Given** an editor who clears the organization's name and saves, **Then** nothing is saved, the
   field says a name is required, and everything else they typed is still in the form.
7. **Given** an owner or administrator whose checklist says the logo, the type, the city and
   country, the description or the website is missing, **When** they follow that item, **Then**
   they arrive at the field that fixes it. **When** they fill it in and save, **Then** the
   checklist counts it as in place.
8. **Given** an ordinary member of the organization, a signed-in person with no affiliation to it,
   or a person holding only the Data Curator role, **When** they open its page, **Then** no editing
   action is offered. **When** they request its editing page directly, **Then** they are refused
   and nothing is changed.
9. **Given** an administrator whose affiliation to the organization has ended, or whose account has
   been deactivated, **When** they request its editing page, **Then** they are refused.
10. **Given** an owner editing an organization, **When** the page is shown, **Then** it offers no
    way to change the ROR identifier, the members or the owner.
11. **Given** an organization with no owner and no administrators, **When** anyone who is not a
    community manager requests its editing page, **Then** they are refused.

---

### User Story 3 - A community manager maintains the profiles nobody else can (Priority: P3)

A community manager notices that a person credited on a dataset, who has never signed in, has a
misspelt name and no biography, that a former colleague who closed their account still lists an old
website, and that an organization nobody owns has no country. They open each profile, find the same
edit action its keeper would see, and correct the record from the portal without going to the
administration interface. On the profile of someone with an active account they find no edit
action, because that profile is its owner's to maintain.

**Why this priority**: Most profiles are kept by the people they describe once the first two
stories exist. This story covers the ones that have nobody who can sign in and fix them: profiles
never claimed, accounts no longer active, and organizations with no owner.

**Independent Test**: Load development data. Sign in as the seeded Community Manager and edit an
unclaimed person, a person whose account is inactive and an organization that account has no
affiliation to, then try a person with an active account. Sign in as the seeded Data Curator and
try all four.

**Acceptance Scenarios**:

1. **Given** a person holding the Community Manager role, **When** they open any organization's
   page, or the profile of a person who does not have an active account, **Then** the working edit
   action is offered, and it leads to the same editing page with the same fields the profile's own
   keeper would get.
2. **Given** a community manager who edits an unclaimed profile and saves, **When** the profile is
   opened, **Then** it shows the new values and is still unclaimed.
3. **Given** a claimed profile whose account has been deactivated, **When** a community manager
   edits it and saves, **Then** the profile shows the new values and the account is still inactive.
4. **Given** a community manager on the profile of a person with an active account, **When** the
   page is shown, **Then** no edit action is offered. **When** they request its editing page
   directly, **Then** they are refused and nothing is changed.
5. **Given** a profile a community manager has open for editing, **When** the person claims it, or
   their account is made active again, before the community manager saves, **Then** the save is
   refused and nothing is changed.
6. **Given** a person whose account was deactivated and is active again, **When** they open their
   own profile, **Then** they can edit it, it shows whatever a community manager changed in
   between, and community managers can no longer edit it.
7. **Given** a community manager who edits an organization they have no affiliation to and saves,
   **When** the page is opened, **Then** it shows the new values and the organization's owner,
   administrators and members are unchanged.
8. **Given** a profile a community manager has corrected, **When** anyone reads it, **Then**
   nothing on it marks the correction as a community manager's.
9. **Given** a person holding the Data Curator role or the Developer role and no other, **When**
   they open somebody else's profile or an organization they do not keep, **Then** no edit action
   is offered and a direct request for the editing page is refused.
10. **Given** a person who holds the Community Manager role and is removed from it, **When** they
    next request an unclaimed person's editing page, **Then** they are refused.
11. **Given** a community manager on a person's profile or an organization they do not keep,
    **When** the page is shown, **Then** the completeness checklist is still not shown to them,
    because 019 shows it only to the people who keep the record.

---

### Edge Cases

- Two people may edit the same organization at once. The later save wins, and neither is refused.
- A name may be very long or in a non-Latin script. It is saved as typed and the editing page does
  not break at any breakpoint.
- A person may list the same link, alternative name or language twice. It is kept once.
- An alternative name or link left empty is dropped on save and is not stored as a blank entry.
- An image larger than the portal accepts is refused with a message saying the limit, and the rest
  of what was typed stays in the form.
- A person who is both an organization's administrator and a community manager sees one edit
  action, not two.
- An editor may lose the right to edit while the page is open, because their affiliation was ended,
  their role removed, or the profile's owner gaining an active account. Saving is then refused and nothing is changed.
- A profile that does not exist answers "not found" on its editing page, as it does on its overview.
- An organization that is the parent of others may itself be given a parent. Only a choice that
  would make an organization part of itself, directly or through others, is refused.

## Requirements *(mandatory)*

### Functional Requirements

**Who may edit**

- **FR-001**: A person with an active account MUST be able to edit their own profile.
- **FR-002**: A person whose affiliation to an organization is of the owner or administrator type
  and has not ended MUST be able to edit that organization's profile.
- **FR-003**: A person holding the Community Manager portal role MUST be able to edit any
  organization's profile, including an organization with no owner, and the profile of any person
  who does not have an active account: one nobody has claimed, one whose owner has been invited
  and has not signed in, and one whose account has been deactivated.
- **FR-003a**: The profile of a person with an active account MUST be editable in the portal only
  by that person. This holds from the moment the account becomes active, including for an editing
  page a community manager already had open.
- **FR-004**: Nobody else may edit a profile. In particular the Data Curator and Developer roles,
  ordinary membership of an organization, and an ended owner or administrator affiliation give no
  right to edit. The permissions the Data Curator role holds MUST NOT change.
- **FR-005**: The right to edit MUST be checked when the editing page is opened and again when it
  is saved. A request from someone without the right MUST be refused and change nothing. A visitor
  who is not signed in MUST be sent to sign in first.
- **FR-006**: An edit action MUST be offered on a profile only to someone who may use it.

**What is edited**

- **FR-007**: A person's editing page MUST allow changing the photo, the name the person is
  publicly known by, alternative names, the biography, links and languages, and nothing else.
- **FR-008**: An organization's editing page MUST allow changing the logo, the name, alternative
  names, the type, the organization it is part of, the city, the country, the description, the
  website and other links, and nothing else.
- **FR-009**: The same fields MUST be offered whoever is editing: the profile's keeper and a
  community manager get the same page.
- **FR-010**: Email address, password, connected sign-ins, ORCID iD, ROR identifier and other
  identifiers, affiliations, an organization's members and owner, portal roles, whether a profile
  is claimed and whether an account is active MUST NOT be changeable from an editing page. A
  person's editing page MUST say where email, password and connected sign-ins are managed.
- **FR-011**: A name MUST be required. A link MUST be a web address. A language MUST be one the
  portal recognises. A photo or logo MUST be an image within the size the portal accepts. An
  organization's type and country MUST be chosen from the lists the record already uses.
- **FR-012**: Choosing as an organization's parent the organization itself, or any organization
  that is part of it directly or through others, MUST be refused.
- **FR-013**: When a save is refused for any reason in FR-011 or FR-012, nothing MUST be saved,
  each field at fault MUST say what is wrong, and everything else the editor entered MUST remain in
  the form.
- **FR-014**: Empty and repeated entries among alternative names, links and languages MUST be
  dropped on save.
- **FR-015**: Removing a photo or logo MUST be possible, after which the profile shows initials.

**Reaching the editing page and returning from it**

- **FR-016**: The edit action 019 places in a person's header and the action for editing an
  organization's details in its management menu MUST work, replacing their not-available
  treatment. Every other capability 019 lists as not available MUST stay as 019 specifies it.
- **FR-017**: Each checklist item this feature can fix MUST lead to the field that fixes it. For a
  person these are the photo, the biography and the links. For an organization these are the logo,
  the type, the city and country, the description and the website. Items it cannot fix (a
  connected ORCID iD, a primary affiliation, a ROR identifier) MUST stay as 019 specifies them.
- **FR-018**: A successful save MUST return the editor to the profile's overview page, confirm that
  the change was saved, and show the new values. Leaving without saving MUST change nothing.
- **FR-019**: A changed name, photo or logo MUST appear wherever the contributor is shown,
  including credits, lists, affiliations and the project's owner.

**How an edit is recorded**

- **FR-020**: An edit by a community manager MUST NOT be marked as theirs anywhere a reader can
  see, and MUST NOT change whether the profile is claimed, whether the account is active, or who
  owns, administers or belongs to the organization.

**Documentation**

- **FR-021**: The documentation for portal administrators that lists each portal role MUST say who
  may edit person and organization profiles in the portal. The documentation for portal users MUST
  describe how a person edits their own profile and how an organization's profile is edited.
- **FR-022**: The documentation for portal developers MUST say how a portal changes the fields
  either editing page offers.

### Key Entities

- **Person**: a credited individual and, where they have signed in, the portal account. The
  profile is the public view of this record, not a record of its own.
- **Organization**: a credited institution. It may be part of another organization.
- **Affiliation**: a person's membership of an organization over a period, with a type. The owner
  and administrator types, while the affiliation has not ended, are what let a person edit the
  organization's profile.
- **Portal role**: one of the four named rights a person can hold on a portal. Only the Community
  Manager role bears on this feature.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A person who opens their own profile with nothing but a name on it can add a photo, a
  biography and a link and see all three on the profile in under two minutes, without leaving the
  portal's own pages.
- **SC-002**: An organization's owner can bring its checklist from nothing in place to every item
  this feature covers in place in a single visit to the editing page.
- **SC-003**: For every seeded account, the set of profiles whose editing page opens is exactly the
  set FR-001 to FR-003a give that account, and every other editing page refuses it.
- **SC-004**: No request by someone without the right to edit changes any stored value, whether the
  request opens the page or submits it.
- **SC-005**: The permissions held by the Data Curator role are the same after this feature as
  before it.
- **SC-006**: A community manager can correct an unclaimed profile and the profile of an inactive
  account without opening the
  administration interface.
- **SC-007**: The editing pages do not scroll sideways at widths of 375, 768, 1024 and 1440 pixels.
- **SC-008**: Each example in the documentation this feature adds or changes runs as written.

## Assumptions

- Specification 019 is delivered before this one is built. The edit action, the management menu and
  the checklists this feature brings to life are 019's.
- A person's affiliations are memberships and are edited with an organization's members, in a later
  specification. The same goes for transferring ownership.
- An ORCID iD is connected by signing in with ORCID, and a ROR identifier is set when the
  organization is created or by a community manager in the administration interface. Neither is
  typed into an editing page, because a hand-typed identifier would read as verified when it is
  not.
- Claiming a profile, refreshing from ORCID or ROR, privacy settings, contacting a person, asking
  to join an organization, and creating or deleting people and organizations are outside this
  specification.
- Email address, password and connected sign-ins stay on the account pages the portal already has.
- Portal Administrators who are not also community managers get no right to edit profiles in the
  portal from this feature. What they can already do in the administration interface is unchanged.
- The administration interface keeps every ability it has today. This feature adds a route in the
  portal and removes none.
