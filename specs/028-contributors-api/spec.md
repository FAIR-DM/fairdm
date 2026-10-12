# Feature Specification: People and organizations can be created and changed through the API

**Feature Branch**: `028-contributors-api`

**Created**: 2026-10-12

**Status**: Draft

**Goals**: G10: data and metadata are reachable by machines through a documented API. G4:
contributions can be recorded and revised against any object in the core model.

**Roadmap**: R11, the machine-readable API. That item is delivered. This feature extends what it
delivered and no other item covers it.

**Input**: The API returns people and organizations and cannot create or change them. A script that
loads a dataset can create the dataset, its samples and its measurements, but when one of the
authors is not in the portal yet, someone has to open the portal and add them by hand. A person with
a token should be able to add a person or an organization through the API, with their ORCID iD or
ROR ID, and find the existing record when the portal already holds one with that identifier. The
people who may edit a profile on the portal's editing pages should be able to change it through the
API under the same rules.

## What exists, and what this specification changes

`/api/v1/contributors/` lists people and organizations and returns one of them, with what their
public profile page shows. It accepts no write of any kind. FS-011 specified it that way and left
creating a contributor to a later feature, which is this one.

In the portal, FS-020 lets a profile's keeper edit it: a person their own, an organization's owner
and administrators theirs, and a community manager any organization and any person without an
active account. No page in the portal lets an ordinary researcher add a person or an organization
that is not there yet.

After this feature, the same address accepts a new person or organization from any signed-in
caller, accepts changes from whoever may edit that profile in the portal, and can be asked whether
the portal already holds the contributor with a given identifier.

## Boundary

- **Crediting a contributor on a record**, with roles, an affiliation and a level, is #462, along
  with writing a record's descriptions, key dates, identifiers and keywords. This feature makes the
  contributor exist. #462 credits them.
- **Deleting a person or an organization** is not offered. FS-017 gives no portal role the right to
  delete a person, and the API does not go further than the portal.
- **Merging two profiles for the same contributor**, **claiming a profile** and everything about a
  person's account (email address, password, sign-ins, whether the account is active, portal roles)
  stay in the portal. The API neither returns nor accepts them.
- **A person's affiliations and an organization's members and owner** are read with the contributor
  and changed in the portal.
- **Hiding parts of a profile from some readers** is #246.
- **Checking an identifier against its scheme's own rules** belongs to the roadmap item that
  introduces that check for the portal and the API together.

## Clarifications

### Session 2026-10-12

Each question was answered from the maintainer's confirmation of the feature's reading, and from
the specifications this one sits beside, without putting it to the maintainer again. The longer
reasoning is in [decisions.md](decisions.md).

- Q: Who may add a person or an organization? → A: Any signed-in caller. A script loading a dataset
  runs as an ordinary researcher, and restricting this to community managers would leave that
  script unable to name a new author.
- Q: What is a person added this way? → A: A record for attribution only. It has no email address
  and no account, nobody has claimed it, and nobody can sign in as it.
- Q: Who keeps a profile after it is added? → A: Whoever FS-020 says. Adding a profile gives no
  right to change it afterwards. A person nobody has claimed is kept by the community managers,
  and so is an organization with no owner.
- Q: Which fields can be written? → A: The ones the portal's editing pages offer, including the
  photo or logo, and the contributor's identifiers. Nothing else.
- Q: FS-020 keeps identifiers off the editing pages. Why are they written here? → A: Because an
  identifier is what tells a loading script, and later the portal, which real person or institution
  a record stands for. It can be given when the contributor is added, and added later where the
  contributor has none of that kind. An identifier already on a contributor is never changed or
  removed through the API.
- Q: May a person add an ORCID iD to their own profile through the API? → A: No. A person with an
  active account proves an ORCID iD is theirs by connecting it as a sign-in, and typing one into a
  request proves nothing.
- Q: What happens when the identifier sent already belongs to a contributor? → A: Nothing is
  created or changed, and the response names the contributor who holds it, so the caller can use
  that record.
- Q: Two people share a name and neither has an identifier. Is the second refused? → A: No. Names
  are not unique. Finding and merging duplicates is the community managers' work in the portal.
- Q: Is a person distinguished from an organization by the address? → A: No. There is one address
  for contributors, as there is for reading, and the request says which of the two it is adding.
- Q: Can a person be turned into an organization, or the reverse? → A: No.
- Q: Is adding contributors limited separately from other writes? → A: Yes. Adding is open to every
  signed-in caller, so it has a limit of its own, lower than the general limit for a caller with a
  token, and the operator can change it.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A researcher's script adds a person or an organization who is not in the portal (Priority: P1)

A researcher is loading a published dataset with a script. Two of its authors and one of their
institutes are not in the portal. The script adds the institute with its name, country and ROR ID,
then adds each author with their name and ORCID iD. Each response is the new contributor, complete,
with the address the script will use to refer to them. The authors now appear in the portal's
people list as profiles nobody has claimed.

**Why this priority**: This is the gap. Without it, loading data through the API stops at the first
author the portal has not seen.

**Independent Test**: With a token for an ordinary signed-in person, add an organization and a
person with identifiers, then request each one and open its profile page. Repeat with no token,
with a missing name, and with account fields in the request.

**Acceptance Scenarios**:

1. **Given** a signed-in caller, **When** they add a person with a name, **Then** the person exists
   and the response is the complete new contributor with its address.
2. **Given** a signed-in caller, **When** they add an organization with a name, **Then** the
   organization exists and the response is the complete new contributor with its address.
3. **Given** a person added through the API, **When** the portal is asked about them, **Then** they
   have no email address and no account, nobody has claimed them, and nobody can sign in as them.
4. **Given** a request to add a contributor that carries an ORCID iD, a ROR ID or another
   identifier a contributor may hold, **When** it is processed, **Then** the new contributor holds
   that identifier.
5. **Given** a request to add a contributor that carries any of the fields the portal's editing
   page offers for that kind of contributor, **When** it is processed, **Then** the new contributor
   has those values.
6. **Given** a request to add an organization that names another organization as the one it is part
   of, **When** it is processed, **Then** the new organization is part of that one.
7. **Given** a request to add a person that carries an email address, a password, a portal role or
   any other account detail, **When** it is processed, **Then** the person is added without it.
8. **Given** a request to add a contributor with no name, a link that is not a web address, a
   language or country the portal does not recognise, or an identifier of a kind a contributor
   cannot hold, **When** it is processed, **Then** nothing is added and the response names each
   field at fault and says why.
9. **Given** a request to add a contributor that does not say whether it is a person or an
   organization, **When** it is processed, **Then** nothing is added and the response says so.
10. **Given** a request to add a contributor with no token and no session, **When** it is
    processed, **Then** it is refused as unauthenticated.
11. **Given** a person who has just added a contributor, **When** they try to change that
    contributor and hold no right FS-020 gives, **Then** they are refused.
12. **Given** a contributor added through the API, **When** anyone requests the list of
    contributors or opens the portal's people or organizations list, **Then** the contributor is
    there.

---

### User Story 2 - A script finds out whether the portal already holds a contributor (Priority: P1)

The same script is run a second time after a failure half way through. Before adding each author it
asks the API for the contributor with that ORCID iD, receives the one it added on the first run and
uses it. For an author it forgot to look up first, it sends the request to add them anyway. The API
adds nothing and answers with the contributor who already holds that ORCID iD.

**Why this priority**: Adding is open to every signed-in caller, so without this every re-run and
every second script fills the portal with duplicates of the same people.

**Independent Test**: Add a person with an ORCID iD. Ask the list for that ORCID iD, and for one
nobody holds. Add a second person with the same ORCID iD. Add two people with the same name and no
identifier.

**Acceptance Scenarios**:

1. **Given** a contributor who holds an identifier, **When** the list of contributors is requested
   for that identifier, **Then** that contributor alone is returned.
2. **Given** an identifier no contributor holds, **When** the list is requested for it, **Then**
   the list is empty.
3. **Given** a contributor who holds an identifier, **When** a request to add a contributor carries
   the same identifier, **Then** nothing is added and the response names the contributor who holds
   it, by short identifier and by address.
4. **Given** two requests to add a contributor with the same name and no identifier, **When** both
   are processed, **Then** both contributors exist.
5. **Given** the list of contributors, **When** it is requested for people only or for
   organizations only, **Then** only that kind is returned.
6. **Given** an identifier held by an account the contributor list leaves out, such as a
   superuser's, **When** the list is requested for it or a request to add a contributor carries it,
   **Then** the response reveals nothing about that account.

---

### User Story 3 - A profile's keeper changes it through the API (Priority: P2)

An institute keeps its staff directory in its own system. An administrator of the institute's
organization in the portal runs a script that keeps the organization's description, website and
city in step with that system. A researcher updates the biography and links on their own profile
from a script of their own. A community manager's clean-up script corrects the spelling of a name
on a profile nobody has claimed and adds the ROR ID an organization was missing. An ordinary member
of the institute tries to change its name and is refused.

**Why this priority**: It brings the API level with the portal's editing pages. It follows the
first two stories because a loading script needs to add and find contributors before anyone needs
to maintain them by script.

**Independent Test**: With a token for each of a person, an organization's administrator and a
community manager, change the profiles FS-020 lets them edit, one field and then all fields. Repeat
as an ordinary member, as a signed-in person with no connection, and with no token. Try to delete a
contributor.

**Acceptance Scenarios**:

1. **Given** a person with an active account, **When** they send a change to their own profile,
   **Then** it is saved.
2. **Given** a person whose affiliation to an organization is of the owner or administrator type
   and has not ended, **When** they send a change to that organization, **Then** it is saved.
3. **Given** a community manager, **When** they send a change to any organization, or to a person
   who does not have an active account, **Then** it is saved.
4. **Given** a community manager, **When** they send a change to a person who has an active
   account, **Then** they are refused and nothing changes.
5. **Given** an ordinary member of an organization, an owner or administrator whose affiliation has
   ended, or a signed-in person with no connection to a profile, **When** they send a change to it,
   **Then** they are refused and nothing changes.
6. **Given** a contributor a caller may change, **When** they send a change to one field, **Then**
   that field changes and every other field is as it was.
7. **Given** a contributor a caller may change, **When** they send a full replacement, **Then** the
   fields the editing page offers take the values sent.
8. **Given** a contributor a caller may change, **When** they send a photo or logo, **Then** the
   profile shows it. **When** they remove it, **Then** the profile shows none.
9. **Given** a change that names as an organization's parent the organization itself, or one that
   is part of it directly or through others, **When** it is processed, **Then** it is refused and
   nothing changes.
10. **Given** a change with a value a field does not accept, **When** it is processed, **Then**
    nothing is saved and the response names each field at fault and says why.
11. **Given** a contributor a caller may change who has no identifier of some kind, **When** the
    caller sends one of that kind, **Then** the contributor holds it.
12. **Given** a contributor who already holds an identifier, **When** a change tries to replace it
    or remove it, **Then** the identifier is as it was.
13. **Given** a person with an active account, **When** they send an ORCID iD for their own
    profile, **Then** it is not added.
14. **Given** a change that carries an email address, a password, an affiliation, whether the
    profile is claimed, or whether the contributor is a person or an organization, **When** it is
    processed, **Then** each of those is as it was.
15. **Given** a request to change a contributor with no token and no session, **When** it is
    processed, **Then** it is refused as unauthenticated.
16. **Given** any caller, **When** they try to delete a contributor, **Then** the API answers that
    deleting is not offered and the contributor is untouched.
17. **Given** an account the contributor list leaves out, **When** any caller sends a change to it,
    **Then** they are answered as for a contributor that does not exist.
18. **Given** a changed name, photo or logo, **When** the contributor is next shown on a credit, a
    list or a record returned by the API, **Then** it shows the new value.

---

### User Story 4 - A portal operator limits how quickly contributors can be added (Priority: P3)

A research group runs its portal on one small server and lets anyone register. Out of the box, an
account that starts adding hundreds of people is stopped after a modest number and told when it may
continue, while its other requests carry on under the ordinary limit. Before a planned import of a
large author list, the operator raises the limit in the settings and restarts.

**Why this priority**: The default protects a portal nobody has tuned. A portal can launch with it
and adjust later.

**Independent Test**: With a token, add contributors until refused and read the refusal. Confirm a
read and a change to a record still succeed. Change the limit in the settings and repeat.

**Acceptance Scenarios**:

1. **Given** a signed-in caller, **When** they add more contributors than the limit allows in its
   window, **Then** further requests to add are refused as too many, and the refusal says when to
   try again.
2. **Given** a caller stopped by that limit, **When** they read, look a contributor up by
   identifier, or change a record or a contributor, **Then** they are not stopped by it.
3. **Given** an operator who changes the limit in the portal's settings, **When** the portal
   restarts, **Then** the API follows the new value.

---

### Edge Cases

- Two requests to add a contributor with the same identifier arrive at once. One contributor is
  added, and the other request is answered as for an identifier already held.
- A caller sends an identifier with spaces, in lower case or as the full web address of the
  identifier. It is treated as the same identifier as its plain form, when looking a contributor up
  and when deciding whether it is already held.
- A request to add a contributor carries two identifiers of the same kind. It is refused, as the
  portal allows one of each kind.
- A person's account becomes active while a community manager's script is part way through a run of
  corrections. The next change is judged by the state the account is in then, and is refused.
- An administrator's affiliation to an organization ends while their token is in use. The next
  change is judged by the affiliation they hold then.
- A profile nobody has claimed is later claimed by the person it describes. They keep it from then
  on, and what was written when it was added stays as it was until they change it.
- A caller sends a photo or logo that is not an image, or is larger than the portal accepts. It is
  refused and the profile keeps the one it had.
- Empty and repeated entries among alternative names, links and languages are dropped on save, as
  on the editing pages.
- A request to add an organization names a parent that does not exist. Nothing is added and the
  response says the parent is not one the caller can choose.

## Requirements *(mandatory)*

### Functional Requirements

**Adding**

- **FR-001**: An authenticated caller MUST be able to add a person or an organization through the
  contributors endpoint. The request MUST say which of the two it is adding.
- **FR-002**: A person added through the API MUST have no email address, no credential and no
  account, MUST be unclaimed, and MUST NOT be able to sign in.
- **FR-003**: A request to add a contributor MUST accept the fields the portal's editing page
  offers for that kind of contributor, and the contributor's identifiers. Any account detail it
  carries MUST be left out of what is saved.
- **FR-004**: A name MUST be required. Every other value MUST be held to the rule the editing pages
  hold it to: a link is a web address, a language and a country are ones the portal recognises, an
  organization's type is from the list the record uses, and a photo or logo is an image within the
  size the portal accepts.
- **FR-005**: An identifier MUST be of a kind a contributor may hold, and a contributor MUST hold at
  most one of each kind.
- **FR-006**: The response to adding a contributor MUST be the complete contributor as the API
  returns it when read.
- **FR-007**: Adding a contributor MUST give the caller no right over it beyond what FS-020 gives
  them.

**Finding, and not adding twice**

- **FR-008**: The list of contributors MUST be able to be narrowed to the contributor who holds a
  given identifier, and to people only or organizations only.
- **FR-009**: A request to add a contributor with an identifier another contributor already holds
  MUST add nothing and MUST name the contributor who holds it, by short identifier and by address.
- **FR-010**: An identifier MUST be compared in one normal form, so that the same identifier
  written with spaces, in another case or as its web address is recognised as the same.
- **FR-011**: Two contributors MUST NOT come to hold the same identifier through requests that
  arrive together.
- **FR-012**: Contributors with the same name and no identifier in common MUST both be accepted.
- **FR-013**: The accounts the contributor list leaves out MUST stay out of every answer this
  feature gives, including the answer to an identifier one of them holds.

**Changing**

- **FR-014**: A change to a contributor MUST be allowed to exactly the people FS-020 allows to edit
  that profile in the portal, and refused to everyone else. The rule MUST be the portal's own and
  not a second statement of it.
- **FR-015**: The right to change MUST be judged at the time of each request.
- **FR-016**: The API MUST accept both a change to part of a contributor and a full replacement. A
  partial change MUST leave every field it does not name as it was.
- **FR-017**: A contributor's photo or logo MUST be able to be set, replaced and removed.
- **FR-018**: Making an organization part of itself, or of an organization beneath it, MUST be
  refused.
- **FR-019**: An identifier of a kind the contributor does not hold MUST be able to be added by
  someone who may change the contributor. An identifier the contributor already holds MUST NOT be
  changed or removed through the API.
- **FR-020**: A person with an active account MUST NOT be able to add an ORCID iD to their own
  profile through the API.
- **FR-021**: A person's affiliations, an organization's members and owner, whether a profile is
  claimed, every account detail, and whether a contributor is a person or an organization MUST NOT
  be changeable through the API. A request that carries any of them MUST leave it as it was.
- **FR-022**: Empty and repeated entries among alternative names, links and languages MUST be
  dropped on save.
- **FR-023**: The API MUST NOT let any caller delete a contributor.

**Answers**

- **FR-024**: Adding or changing with no authentication MUST be answered as unauthenticated. A
  change refused to an authenticated caller MUST be answered as forbidden. A write to an account
  the contributor list leaves out MUST be answered as for a contributor that does not exist.
- **FR-025**: A request refused for what it contains MUST save nothing and MUST name each field at
  fault and say why.
- **FR-026**: No request to the contributors endpoint, valid or invalid, may be answered with a
  server error.
- **FR-027**: Everything FS-011 requires of the contributors endpoint when it is read MUST still
  hold: what a contributor is returned with, no internal database number, no account detail,
  paging, ordering and the general limits.

**Limits**

- **FR-028**: Adding contributors MUST have a limit of its own for each caller, lower by default
  than the general limit for a caller with a token. Reaching it MUST NOT stop the caller's other
  requests, and the refusal MUST say when to try again.
- **FR-029**: That limit MUST be a setting the portal operator can change.

**Documentation**

- **FR-030**: The generated API documentation MUST show the contributors endpoint's writes, with
  the fields each kind of contributor accepts, which are required and which are read-only.
- **FR-031**: The documentation for portal developers MUST describe adding a contributor, looking
  one up by identifier, what is answered when an identifier is already held, who may change a
  contributor, and that deleting is not offered.
- **FR-032**: The documentation for portal administrators that lists the API's limits MUST include
  the limit on adding contributors and how to change it.

### Key Entities

- **Contributor**: a person or an organization credited on records. Read by anyone, added by any
  signed-in caller, changed by its keeper.
- **Person**: a credited individual. One added through the API has no account and is unclaimed
  until the person it describes claims it.
- **Organization**: a credited institution, which may be part of another.
- **Contributor identifier**: an external identifier a contributor holds, such as an ORCID iD or a
  ROR ID. One of each kind for each contributor, and no two contributors hold the same one.
- **Keeper**: whoever FS-020 lets edit a profile. A person with an active account for their own,
  an organization's current owner and administrators for theirs, and the community managers for any
  organization and for any person without an active account.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A script with an ordinary researcher's token adds every author and institute of a
  dataset that the portal did not hold, with nobody opening the portal.
- **SC-002**: Running that script a second time adds no contributor.
- **SC-003**: Every person FS-020 lets edit a profile in the portal can change the same fields of
  it through the API, and nobody else can change any.
- **SC-004**: No request to the contributors endpoint returns, sets or changes an email address, a
  credential, an account's state or a portal role.
- **SC-005**: A person added through the API can later be claimed by the person it describes in the
  way the portal already provides.
- **SC-006**: An account adding contributors without pause is stopped at the default limit while
  its other requests continue.
- **SC-007**: The automated tests send every kind of valid and invalid request this specification
  describes to the contributors endpoint, and none is answered with a server error.

## Assumptions

- FS-011's API, FS-020's rules on who edits a profile, FS-010's claiming and FS-017's portal roles
  are as their own specifications describe them. This feature changes none of them.
- A photo or logo is the first file the API accepts. FS-011 put file upload out of scope for
  records, and that stands for records.
- Nothing has been released that carries the API, so the contributors endpoint can gain writes
  without a new version in its address.
- The figure for the limit on adding contributors is chosen at planning for a single small server.
- A portal that does not want open adding of contributors can set that limit to nothing allowed.
  A switch that restricts adding to community managers is not part of this feature.
