# Feature Specification: Overview pages for people and organizations

**Feature Branch**: `019-contributor-overview-pages`

**Created**: 2026-10-01

**Status**: Draft

**Goals**: G5: a modern, extensible interface that every portal gets by default, with no frontend
work. G12: private and public data sit side by side, controlled per object. G15: external
identifiers for people, organisations and samples are carried through the record.

**Roadmap**: none. No roadmap item covers contributor pages. R9 delivered the contributor records
these pages read, and the specification behind it (009) left their pages to a later one. This is
that specification, for the overview page only.

**Input**: A person and an organization each need an overview page that matches the ones projects,
datasets, samples and measurements got in specification 018. Today the first tab of a contributor's
page shows a title and nothing else. A visitor who arrives from a credit should learn who the person
is, where they work, whether their ORCID iD is verified, what they are credited on in this portal
and who they work with. On an organization's page they should learn what it is, where it sits, who
belongs to it and which research it is behind. The person themself, and the people who keep an
organization's record, should also see what the record is still missing. Both pages were built as a
working prototype on the branch `sketch/contributor-profiles` and reviewed over six rounds. This
specification describes the design that review settled on.

## Clarifications

### Session 2026-10-01

- Q: A person is credited on a private project that the viewer happens to be a member of. Does the
  person's page list it for that viewer? → A: No. Projects and datasets appear on a contributor's
  page only when they are public, for every viewer, the person themself included. A profile is a
  public statement about someone's work, and it should read the same to the person as to the
  visitor they send the link to. Private work is reached from the project, not from a profile.
- Q: The frequent collaborators and the role counts are worked out from credits. Which credits? →
  A: Only credits on records the viewer may open. Someone who shares nothing but a private record
  with the person is not named as a collaborator, and a role held only on private records is not
  counted.
- Q: The Projects and Datasets tabs beside the overview list everything the contributor is credited
  on, private records included. The overview's cards and figures link to them. Do they change? → A:
  Yes. Both tabs follow the same rule as the overview, so following "view all" never names a record
  the overview left out.
- Q: Two more tabs, Statistics and Network, render blank pages today. Do they stay? → A: No. Both
  are removed until they have content. The overview already shows the roles and the collaborators
  those tabs were meant for.
- Q: Does a contributor's page follow the side column order specification 018 set for record
  pages? → A: No. That order belongs to the four record pages. A contributor has no Details card,
  because the facts it would hold are in the header, and no funding or citation card, because a
  person or an organization is not a citable research output. The order for these two pages is
  given in FR-019 and FR-027.
- Q: Who counts as a member of an organization on its page? → A: A person with a verified
  affiliation to it that has not ended. Pending requests and former members are not shown or
  counted.
- Q: Whose work does an organization's page count? → A: Its own: the projects it owns, the projects
  and datasets it is credited on, and the datasets inside the projects it owns. What its members
  did under their own names is not rolled up into it.
- Q: When is an ORCID iD shown as verified? → A: When the person has signed in to the portal with
  that ORCID account. An iD that somebody typed in is shown as unauthenticated, following ORCID's
  display guidelines.
- Q: Are the pages of unclaimed profiles and inactive accounts public? → A: Yes. The credit they
  hold stays public, so the page does too, with a notice saying which state the profile is in.
- Q: Are the pages translatable? → A: Yes. Every label, notice and placeholder is marked for
  translation, language names are shown in the active language, and dates and numbers follow the
  active locale.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A person's page tells a visitor who they are and what they have done here (Priority: P1)

Someone follows a credit on a dataset to the person behind it. At the top they read the person's
name with a link to their ORCID record, whether the profile has been claimed, any portal roles the
person holds, where they work and which languages they use. Three figures follow: the projects and
datasets the person is credited on, and since when they have had an account. Below that come the
person's biography, the projects and datasets themselves, and the contribution roles the person has
held with how often each. Beside the content, the side column lists the person's identifiers and
links, their current and past affiliations, and the contributors they most often share a credit
with. Things the portal cannot do yet, such as claiming the profile, contacting the person, a list
of publications, a map of fieldwork and recent activity, are shown as not available yet.

This is the first contributor page built on the shared page anatomy, so this story also delivers
what both pages share: the first tab's name, the visibility rule on the tabs beside it, and the
blocks a portal developer extends.

**Why this priority**: People are who credits point at. Every People card, header and citation on
the record pages already links here, and the page they land on is empty.

**Independent Test**: Load development data. Open each seeded person as a visitor and signed in:
the complete profile, an unclaimed profile, an inactive account, a person credited on nothing, and a
person credited on both public and private records. Compare what each shows against FR-005 to
FR-023.

**Acceptance Scenarios**:

1. **Given** a person credited on public and private projects and datasets, **When** anyone opens
   their page, **Then** the figures and the two record cards count and list the public ones only.
2. **Given** the same person, **When** a member of one of the private projects opens the page,
   **Then** that project is still not listed.
3. **Given** a person who shares a credit with someone only on a private record, **When** a visitor
   opens the page, **Then** that someone is not among the frequent collaborators.
4. **Given** a person with more projects than the card shows, some in progress and some not,
   **When** the page is opened, **Then** the projects in progress come first, each group most
   recently updated first, and the card offers a way to the full list.
5. **Given** a person who has signed in with ORCID, and one whose ORCID iD was only typed in,
   **When** each page is opened, **Then** the first links to the ORCID record as authenticated and
   the second as unauthenticated.
6. **Given** a profile nobody has claimed, **When** anyone opens it, **Then** a notice says the
   profile exists so the person can be credited and has not been claimed, the way to claim it is
   shown as not available yet, and the account figure says the person has no account.
7. **Given** a person whose account is no longer active, **When** anyone opens the page, **Then** a
   notice says so and the credited work is still shown.
8. **Given** a person with a primary affiliation, other current affiliations and past ones, **When**
   the page is opened, **Then** the header names the primary organization and its location, and the
   affiliations card lists the current ones with the primary first, then the past ones with the most
   recently ended first, each date shown as precisely as it was recorded.
9. **Given** a person with a pending affiliation, **When** the page is opened, **Then** that
   organization appears nowhere on it.
10. **Given** a person credited in several contribution roles, **When** the page is opened, **Then**
    each role is listed with the number of records it is held on, the most frequent first.
11. **Given** a person with more collaborators than the card shows, **When** the page is opened,
    **Then** the card shows the most frequent, counts the rest, and each one shown links to that
    contributor's page.
12. **Given** a person with no biography, no links, no affiliations and no credits, **When** a
    visitor opens the page, **Then** every card is still shown and says what is missing.
13. **Given** any person, **When** the page is rendered, **Then** its schema.org description is in
    the page head and neither it nor the page contains the person's email address.
14. **Given** a contributor credited on private records, **When** a visitor opens the Projects or
    Datasets tab, **Then** the private records are not listed.
15. **Given** any contributor, **When** their page is opened, **Then** the first tab is the
    overview, and there is no Statistics or Network tab.

---

### User Story 2 - An organization's page shows what it is, who belongs to it and what it is behind (Priority: P2)

A visitor opens an organization named as a project's owner or as someone's affiliation. At the top
they read its name with a link to its ROR record, what type of organization it is, the organization
it is part of, where it is based and which languages it works in. Three figures follow: its
projects, its datasets and its members. Below that come its description, its current members with
the people who run it marked, and its projects and datasets. Beside the content, the side column
lists its identifiers and links, shows where it is based on a map, and places it among the
organizations around it: its parent, the organizations beside it, and those beneath it. Asking to
join, managing members, refreshing from ROR, a map of where its members work and recent activity
are shown as not available yet.

**Why this priority**: The organization page reuses everything the person page establishes and adds
members and hierarchy. Fewer links lead to it than to a person.

**Independent Test**: Load development data. Open the seeded organization that has a logo, a ROR
ID, a location, a parent, sub-organizations, members and projects, the one the signed-in user owns,
and the one with nothing recorded, each as a visitor and signed in.

**Acceptance Scenarios**:

1. **Given** an organization that owns some projects and is credited on others, **When** anyone
   opens its page, **Then** both kinds are listed among its projects, the owned ones are marked as
   owned, and none is listed twice.
2. **Given** an organization that owns a project, **When** its page is opened, **Then** the public
   datasets in that project count among its datasets whether or not the organization is credited
   on them.
3. **Given** an organization that owns or is credited on private records, **When** anyone opens its
   page, **Then** those records are neither counted nor listed.
4. **Given** an organization whose members have credits of their own, **When** its page is opened,
   **Then** those records are not counted as the organization's.
5. **Given** an organization with current, pending and former members, **When** its page is opened,
   **Then** only the current, verified members are listed and counted, with the owner first, then
   the administrators, then the other members, each group by name.
6. **Given** an organization with more members than the card has places, **When** its page is
   opened, **Then** the last place counts the members not shown, and the card never takes more
   places than it has.
7. **Given** an organization with a parent and sub-organizations, **When** its page is opened,
   **Then** the hierarchy shows the parent, then this organization among the parent's other
   sub-organizations, then this organization's own direct sub-organizations, each of the others
   linking to its page.
8. **Given** an organization with no parent, **When** its page is opened, **Then** the hierarchy
   starts at this organization. **Given** one with neither a parent nor sub-organizations, **Then**
   the card says none is recorded.
9. **Given** an organization with a recorded location, **When** its page is opened, **Then** a map
   shows where it is based. **Given** one without, **Then** no map is shown.
10. **Given** a signed-in person who is not a member, **When** they open the page, **Then** asking
    to join is shown as not available yet. **Given** a visitor who is not signed in, or a current
    member, **Then** it is not shown at all.
11. **Given** an organization with nothing recorded but its name, **When** a visitor opens its page,
    **Then** every card except the map is still shown and says what is missing.
12. **Given** any organization, **When** its page is rendered, **Then** its schema.org description
    is in the page head.

---

### User Story 3 - The people who keep a record see what it is still missing (Priority: P3)

A person opens their own profile and sees a checklist nobody else sees: whether they have a photo,
an ORCID iD connected by signing in, a biography, a primary affiliation and links to their other
profiles, and how many of those are in place. Where a page exists that fixes a gap, the item links
to it. Their page also addresses them directly where something is empty, and offers editing the
profile as not available yet in place of the contact action. The owner and the administrators of an
organization see the equivalent checklist on its page: a ROR identifier, a logo, the type of
organization, its city and country, a description and a website, together with a menu of management
actions that are not available yet.

**Why this priority**: The checklist is useful only once the pages exist, and most of what it
points at cannot be fixed in the portal until profile editing is built.

**Independent Test**: Load development data. Sign in as the seeded user with an incomplete profile
and open their own page, then another person's. Open the organization that user owns, then one
they do not.

**Acceptance Scenarios**:

1. **Given** a signed-in person with an incomplete profile, **When** they open their own page,
   **Then** the checklist lists each item, says which are in place and how many of the total, and
   tells them that only they can see it.
2. **Given** the same person, **When** anyone else opens that page, signed in or not, **Then** no
   checklist is shown.
3. **Given** a person who has not connected ORCID, **When** they open their own page, **Then** the
   ORCID item links to the page where an account is connected.
4. **Given** a person whose ORCID iD was typed in but who has never signed in with ORCID, **When**
   they open their own page, **Then** the ORCID item is not in place.
5. **Given** a person on their own page, **When** it is shown, **Then** editing the profile is
   offered as not available yet and the contact action is not shown. **Given** anyone else, **Then**
   it is the other way round.
6. **Given** an organization's owner or one of its administrators, **When** they open its page,
   **Then** the checklist for the organization's record is shown, with a menu of management actions
   that are each not available yet.
7. **Given** an ordinary member of that organization, or a visitor, **When** they open its page,
   **Then** neither the checklist nor the menu is shown.
8. **Given** a former administrator whose affiliation has ended, **When** they open the page,
   **Then** neither the checklist nor the menu is shown.

---

### Edge Cases

- A person may have an account and no credits at all. Their page still opens, and the record cards,
  the roles card and the collaborators card each say there is nothing yet.
- A person may have no primary affiliation. The header then names no organization and no location,
  because a person has no location of their own.
- A contributor's name may be very long or in a non-Latin script. Neither breaks the header, the
  member list or the collaborators card at any breakpoint.
- A collaborator may be an organization as well as a person. The collaborators card handles both.
- A language code the portal does not recognise is shown as it was recorded.
- A link with no recognisable site name is shown as it was recorded.
- An identifier of a type with no resolver is listed without a link.
- Two collaborators with the same number of shared credits are ordered by name, so the card does
  not reshuffle between visits.
- The map library may fail to load in the browser. The organization's page still reads, and its
  city and country are still in the header.
- A contributor that does not exist answers "not found".

## Requirements *(mandatory)*

### Functional Requirements

**What both pages share**

- **FR-001**: The person page and the organization page MUST use the page anatomy the record
  overview pages use: notices, a header, a figures strip, then a wide content column beside a narrow
  side column that stack below the `lg` breakpoint with the content first.
- **FR-002**: The overview MUST be the first tab of a contributor's tabbed detail view and carry
  the same name as the first tab of every record. The Statistics and Network tabs MUST be removed.
- **FR-003**: Both pages MUST expose named blocks under the `overview.` prefix for the notices, the
  header's image, badges, name, byline and actions, the figures, the wide column, the side column
  and each card. A block that means the same thing on a contributor page as on a record page MUST
  have the same name. The list of blocks, in page order, MUST be documented for portal developers.
- **FR-004**: A card either page has MUST always be shown, saying what is missing when it has
  nothing to show. The exceptions are the checklist (FR-030, FR-031) and the organization's map
  (FR-027).

**Who sees what**

- **FR-005**: Every contributor's overview page MUST be open to everyone, including the page of an
  unclaimed profile and of an inactive account.
- **FR-006**: A project or dataset MUST appear on a contributor's page, in a list or in a count,
  only when it is public. This holds for every viewer, including the contributor.
- **FR-007**: The frequent collaborators and the role counts MUST be worked out only from credits on
  records the viewer may open.
- **FR-008**: The Projects and Datasets tabs of a contributor MUST list only public records.
- **FR-009**: Neither page, nor its schema.org description, may contain an email address.
- **FR-010**: The page head MUST carry the contributor's schema.org description, and it MUST carry
  nothing the viewer could not read on the page.

**Capabilities that are not available yet**

- **FR-011**: The pages MUST ship with these shown as not yet available: claiming a profile, editing
  a profile, writing a biography or description from the page, contacting a person, asking to join
  an organization, editing an organization's details, managing its members, refreshing it from ROR,
  the full member list, a person's publications, a map of the samples a person or an organization's
  members are credited on, and recent activity.
- **FR-012**: Each item in FR-011 MUST use the treatment the record pages use for a capability that
  is not available yet. It MUST NOT look or behave as if it works, and an action standing in for a
  missing one MUST be disabled and say why.

**The person page**

- **FR-013**: The header MUST carry the person's photo or initials, whether the profile is claimed,
  unclaimed or belongs to an inactive account, each portal role the person holds, and the person's
  name. Where the person has an ORCID iD, the name MUST be followed by a link to the ORCID record
  that says, to sighted readers and to assistive technology, whether the iD is authenticated.
- **FR-014**: Beneath the name the header MUST give the person's primary organization, linked to its
  page, that organization's location, and the person's languages named in the active language. Each
  is left out when not recorded.
- **FR-015**: The header's actions MUST be sharing the page, the person's address in the API, and
  either contacting the person or, on their own page, editing the profile.
- **FR-016**: An unclaimed profile MUST show a notice saying why the profile exists and that it has
  not been claimed. An inactive account MUST show a notice saying the account is no longer active
  and that the profile stays so the work remains credited.
- **FR-017**: The figures MUST be the number of projects and the number of datasets the person is
  credited on, each linking to the matching tab, and when the person's account was created. A
  profile with no account MUST say so in place of a date.
- **FR-018**: The content column MUST carry, in order: the biography; a projects card and a
  datasets card side by side; the contribution roles; and publications and a map as not yet
  available. Each record card MUST show at most five records, projects that are in progress first
  and then the most recently updated, and offer a way to the full list. The roles card MUST list
  each contribution role with the number of records it is held on, the most frequent first.
- **FR-019**: The side column MUST carry, in order: the checklist (FR-030), identifiers, links,
  affiliations, frequent collaborators, and recent activity as not yet available.
- **FR-020**: The identifiers card MUST list every identifier the contributor carries and the
  contributor's portal ID with a way to copy it. An identifier whose type has a resolver MUST link
  to it.
- **FR-021**: The links card MUST list each recorded link, named by the site it points at.
- **FR-022**: The affiliations card MUST list the person's verified affiliations: those that have
  not ended, the primary one first and the rest by organization name, then those that have ended,
  the most recently ended first. Each MUST link to the organization and give its start and end as
  precisely as they were recorded.
- **FR-023**: The frequent collaborators card MUST show the other contributors credited on the same
  records as the person, the most frequent first and ties by name. It MUST show at most eighteen
  and count the rest. Each MUST link to that contributor's page, with the name available on hover
  and to assistive technology.

**The organization page**

- **FR-024**: The header MUST carry the organization's logo or initials, its type, and its name.
  Where it has a ROR ID, the name MUST be followed by a link to its ROR record. Beneath the name the
  header MUST give the organization it is part of, linked to its page, its city and country, and
  its languages. Each is left out when not recorded.
- **FR-025**: The header's actions MUST be sharing the page and the organization's address in the
  API. A signed-in person who is not a current member MUST also be offered asking to join. The
  people who keep the record MUST instead be offered the management menu (FR-031).
- **FR-026**: The figures MUST be the organization's projects, its datasets and its current members.
  Its projects are the public projects it owns and those it is credited on. Its datasets are the
  public datasets it is credited on and those inside the projects it owns. Nothing is counted
  twice, and its members' own credits are not counted.
- **FR-027**: The content column MUST carry, in order: the description; the members; a projects
  card and a datasets card that follow the rules of FR-018, with a project the organization owns
  marked as owned; and a map of where its members work as not yet available. The side column MUST
  carry, in order: the checklist (FR-031), identifiers (FR-020), links (FR-021), a map of where the
  organization is based when a location is recorded, the hierarchy, and recent activity as not yet
  available.
- **FR-028**: The members card MUST list the people with a verified affiliation that has not ended:
  the owner, then administrators, then other members, each group by name. Each entry MUST link to
  the person's page, say since when they have been a member where that is recorded, and mark the
  owner and the administrators. The card MUST have ten places. With more than ten members, the
  tenth place MUST count those not shown.
- **FR-029**: The hierarchy card MUST show the organization's parent, the parent's sub-organizations
  with this organization marked among them, and this organization's direct sub-organizations, in
  name order. Every organization in it other than this one MUST link to its page. Without a parent,
  the hierarchy MUST start at this organization.

**The checklist**

- **FR-030**: A person's own page MUST show them a checklist of what a complete profile has: a
  photo, an ORCID iD connected by signing in with ORCID, a biography, a primary affiliation, and
  links to their other profiles. It MUST say which items are in place and how many of the total,
  mark the photo and the links as optional, link an item to the page that fixes it where such a
  page exists, and say that only they can see it. It MUST NOT be shown to anyone else.
- **FR-031**: An organization's page MUST show its owner and its administrators, meaning the people
  whose current affiliation to it is of that kind, a checklist of what a complete record has: a ROR
  identifier, a logo, the type of organization, its city and country, a description and a website,
  with the logo and the website marked as optional. The same people MUST be offered a menu of
  management actions (FR-011). Neither may be shown to anyone else.
- **FR-032**: On their own page, and on the page of an organization they keep, the viewer MUST be
  told what an empty biography or description is for and be offered writing it, as not yet
  available.

**Development data**

- **FR-033**: The demo application MUST provide development data that reaches every state the two
  pages answer for: a complete profile, the signed-in user's own incomplete profile, an unclaimed
  profile, an inactive account, a person credited on nothing, a very long name and a name in a
  non-Latin script; and an organization with everything recorded, one the signed-in user owns, and
  one with nothing recorded. It MUST use the three standard development accounts.

### Key Entities

- **Person**: someone credited on portal records, who may also hold the portal account. The page
  reads their name, photo, biography, languages, links, identifiers, account state and portal roles.
- **Organization**: an institution credited on records or named as an affiliation. The page reads
  its name, logo, type, description, city and country, location, parent, links and identifiers.
- **Affiliation**: a person's membership of an organization, with its kind (pending, member,
  administrator, owner), whether it is the person's primary one, and when it started and ended.
- **Contribution**: a contributor's credit on one project, dataset, sample or measurement, with the
  contribution roles held on it.
- **Collaborator**: another contributor credited on the same record. A new term for the glossary.
- **Member**: a person with a verified affiliation to an organization that has not ended. A new
  term for the glossary.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A visitor who follows a credit to a person can say, from the first screen and without
  scrolling on a desktop display, who the person is, where they work and whether their ORCID iD is
  authenticated.
- **SC-002**: For every seeded person and organization, opening the page as a visitor names no
  private project or dataset, no collaborator known only through a private record, and no email
  address, in the page or in its machine-readable description.
- **SC-003**: Every count on either page equals the number of entries reached by following its
  link, for the same viewer.
- **SC-004**: A person opening their own profile can tell which of the five items a complete
  profile has are still missing, and nobody else can.
- **SC-005**: On an organization with a hundred members and a person with a hundred collaborators,
  the page is no taller in those two cards than it is with ten and eighteen.
- **SC-006**: A portal developer who has extended a record overview page can add a card to a
  contributor page using the documentation alone, without reading the framework's templates.
- **SC-007**: Neither page scrolls sideways at widths of 375, 768, 1024 and 1440 pixels, with the
  longest seeded name.
- **SC-008**: No tab on a contributor's page renders an empty page or an error.

## Assumptions

- The page anatomy, the shared cards and the treatment for capabilities that are not available yet
  are those delivered by specification 018, and are used as they are.
- A contributor has no privacy settings today, so everything recorded on a person or organization
  other than the email address is public. A policy that lets a person hide parts of their profile
  is a separate feature and will narrow what these pages show when it arrives.
- A person has no location of their own. The location in a person's header is their primary
  organization's.
- "In progress" is the only project status that counts as active when ordering the projects card.
  Datasets have no such state and are ordered by when they were last updated.
- The management actions and the join request stay unavailable until the features that build them
  are specified. This specification commits only to where they will sit.
- The prototype branch has no tests. It shows what was agreed, and the pages are built to this
  specification with tests, not merged from it as it stands.
