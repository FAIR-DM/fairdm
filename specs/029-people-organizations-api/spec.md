# Feature Specification: People, organizations and a record's credits can be read through the API

**Feature Branch**: `029-people-organizations-api`

**Created**: 2026-10-12

**Status**: Draft

**Goals**: G10: data and metadata are reachable by machines through a documented API. G14: dataset
metadata is complete enough for a formal-publication addon to submit it unaided. G15: external
identifiers for people, organisations and samples are carried through the record.

**Roadmap**: R11, the machine-readable API. That item is delivered. This feature extends what it
delivered and no other item covers it.

**Input**: The API returns people and organizations mixed together in one list, in a single
flattened shape that fits neither. A record names the people credited on it only as pointers, so a
script that wants to cite a dataset has to make two more requests for every author. A developer's
script should be able to page through people and through organizations separately, each with the
fields that kind of contributor has, compact in a list and complete for a single one. Every
project, dataset, sample and measurement should list its credits in full: the name, the
identifiers, the affiliation and the roles, close to how DataCite describes a creator or
contributor, and without the rest of the profile. Everything here is read-only.

## What exists, and what this specification changes

FS-011 serves `/api/v1/contributors/`, one list holding people and organizations together. Each
entry has a name, an image, a biography, identifiers, links, languages, one organization and a
location written as text. A person's given and family name, their other affiliations, an
organization's city and country, its parent, its sub-organizations and its members are absent.

A record returned by the API lists its credits. Each credit is a pointer to the contributor, the
roles they hold and a pointer to an organization. It carries no name and no identifier.

After this feature:

- People are read at `/api/v1/people/` and organizations at `/api/v1/organizations/`, each in a
  shape of its own.
- `/api/v1/contributors/` is gone. No release has carried the API, so nothing depends on it.
- A credit on a record carries everything needed to attribute it, in the record's own response.

## Boundary

- **Creating or changing a person or an organization** through the API is #468, which is deferred.
- **Crediting a contributor on a record** through the API is #462. Here credits are read.
- **Letting each person choose what the API shares about them** is #246. Until it is delivered,
  the API returns only what a contributor's public page already shows to every visitor.
- **Searching through the API** belongs to roadmap item R17.
- **Exporting a record as DataCite metadata** is not this feature. A credit is shaped so that such
  an export has what it needs, and the mapping of roles to DataCite's own types stays with the
  export.

## Clarifications

### Session 2026-10-12

Each question was answered from the maintainer's replies while the feature was agreed, and from the
specifications this one sits beside, without putting it to the maintainer again. The longer
reasoning is in [decisions.md](decisions.md).

- Q: One endpoint for contributors, or one each for people and organizations? → A: One each, and
  the mixed endpoint is removed. Each endpoint then has one shape, every person and every
  organization has one address, and the question the mixed list answered, who is credited on this
  record, is answered by the record.
- Q: Does a list entry carry the whole profile? → A: No. A list entry carries what identifies the
  person or organization. The biography or description, links, languages and the related people
  and organizations come with the single record.
- Q: DataCite keeps creators apart from contributors. Does a record? → A: No. A record has one list
  of credits, and each credit carries its roles.
- Q: Which roles does a credit show? → A: The portal's own contribution roles, by name and label.
- Q: Which affiliation does a credit show? → A: The organization recorded on that credit. Where
  the credit records none, it shows none. It does not fall back to where the person works today,
  because a credit says where they worked when they did the work.
- Q: What may the API say about a person? → A: What their public page says to every visitor. No
  email address, nothing about their account, no portal roles, no preferences, and only
  affiliations that are verified.
- Q: A credit is held by an account the people list leaves out, such as a superuser's. What does
  the record show? → A: The credit, with the name and identifiers the record's own page shows, and
  no address to follow, since no profile is served for that account.
- Q: How does a script find what a person or organization is credited on? → A: By asking the
  project list or the dataset list for that contributor. The answer holds public records only, for
  every caller, as the contributor's page does.
- Q: May a portal developer replace the person and organization serializers? → A: Not in this
  feature. Nothing has asked for it.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A developer's script attributes a record from one request (Priority: P1)

Someone writing a harvester requests a dataset. The response lists its credits in the order the
dataset's team put them. For each one the script reads the name, the given and family name where
it is a person, the ORCID iD with its scheme, the institution they are credited from with its ROR
ID, and their roles. It writes a citation and a metadata record without asking the API anything
else. The same is true of a project, a sample and a measurement.

**Why this priority**: Attribution is what a record's metadata is for, and it is the part of this
feature that changes what every record returns.

**Independent Test**: Load development data. Request a project, a dataset, a sample and a
measurement that have credits for a person with an ORCID iD and an affiliation, a person with
neither, and an organization. Compare each credit with the record's own page.

**Acceptance Scenarios**:

1. **Given** a record with credits, **When** it is returned, **Then** each credit carries the
   contributor's name and whether it is a person or an organization.
2. **Given** a credit held by a person, **When** it is returned, **Then** it carries their given
   name and family name.
3. **Given** a credit whose contributor holds identifiers, **When** it is returned, **Then** it
   carries each identifier with the scheme it belongs to and that scheme's address.
4. **Given** a credit that records an organization the person is credited from, **When** it is
   returned, **Then** it carries that organization's name, its identifiers with their schemes, and
   its address in the API.
5. **Given** a credit that records no organization, **When** it is returned, **Then** it shows no
   affiliation, whatever the person's profile says about where they work.
6. **Given** a credit, **When** it is returned, **Then** it carries every role held on it, each by
   name and label.
7. **Given** a credit, **When** it is returned, **Then** it carries the address of the person or
   organization in the API, and requesting that address returns them.
8. **Given** a record with several credits, **When** it is returned, **Then** the credits are in
   the order the record keeps them.
9. **Given** a credit, **When** it is returned, **Then** it carries no biography, description,
   link, language, image, email address or access level.
10. **Given** a credit held by an account the people list leaves out, **When** the record is
    returned, **Then** the credit is there with its name, identifiers and roles and without an
    address.
11. **Given** a list of records that each have credits, **When** a page of it is requested,
    **Then** the number of database queries does not grow with the number of records or credits on
    the page.
12. **Given** a record with no credits, **When** it is returned, **Then** its list of credits is
    empty.

---

### User Story 2 - A developer pages through the people a portal holds (Priority: P1)

A developer building a directory asks the API for people. Each page gives, for every person, their
name, given and family name, identifiers and the organization they mainly belong to. They narrow
the list to one institute, and look one person up by ORCID iD. For a person they want to show in
full they request that person and receive the biography, links, languages, other names and every
verified affiliation with its dates.

**Why this priority**: People are half of what the mixed list served, and the half most callers
want to page through on its own.

**Independent Test**: Request the list of people, page through it, sort it, narrow it to an
organization and to an ORCID iD. Request one person and compare with their public page as a visitor
sees it. Request a superuser.

**Acceptance Scenarios**:

1. **Given** a portal holding people and organizations, **When** the list of people is requested,
   **Then** it holds people only.
2. **Given** a person in the list, **When** the entry is read, **Then** it carries their name,
   given and family name, identifiers with their schemes, their primary organization where they
   have one, and their address in the API and on the portal.
3. **Given** a person in the list, **When** the entry is read, **Then** it carries no biography, no
   links, no languages and no list of affiliations.
4. **Given** a single person, **When** they are requested, **Then** the response carries everything
   the list entry does, together with their other names, biography, links, languages, image and
   every verified affiliation.
5. **Given** an affiliation in that response, **When** it is read, **Then** it names the
   organization by name and address, and gives the kind of affiliation, when it began, when it
   ended if it has, and whether it is the person's primary one.
6. **Given** a person with an affiliation that has not been verified, **When** they are requested,
   **Then** that affiliation is not in the response.
7. **Given** any response about a person, **When** it is read, **Then** it carries no email
   address, no credential, nothing about their account, no portal role and no preference.
8. **Given** the list of people, **When** it is requested for one organization, **Then** it holds
   the people with a verified affiliation to it that has not ended.
9. **Given** a person who holds an identifier, **When** the list is requested for that identifier,
   **Then** that person alone is returned.
10. **Given** the list of people, **When** it is requested in a named order, ascending or
    descending, **Then** the people come back in that order.
11. **Given** an account the portal's own people list leaves out, **When** the list is requested,
    **Then** it is absent, and requesting it directly is answered as a person that does not exist
    is.
12. **Given** a profile nobody has claimed, **When** it is requested, **Then** it is returned as
    any other person is.

---

### User Story 3 - A developer pages through the organizations a portal holds (Priority: P1)

The same developer asks for organizations. Each entry gives the name, the type, the country and the
ROR ID. They narrow the list to one country, then to the departments of one university. For one
organization they request the full record and receive its description, city, links, the
organization it is part of, the organizations that are part of it, and its current members.

**Why this priority**: It is the other half of what the mixed list served, and the fields that set
an organization apart from a person are the ones the mixed shape dropped.

**Independent Test**: Request the list of organizations, page through it, sort it, and narrow it by
type, by country, by parent and by ROR ID. Request an organization with a parent, sub-organizations
and members, and compare with its public page.

**Acceptance Scenarios**:

1. **Given** a portal holding people and organizations, **When** the list of organizations is
   requested, **Then** it holds organizations only.
2. **Given** an organization in the list, **When** the entry is read, **Then** it carries its name,
   type, country, identifiers with their schemes, and its address in the API and on the portal.
3. **Given** an organization in the list, **When** the entry is read, **Then** it carries no
   description, no links, no members and no sub-organizations.
4. **Given** a single organization, **When** it is requested, **Then** the response carries
   everything the list entry does, together with its other names, description, city, links, image,
   the organization it is part of, the organizations that are part of it, and its current members.
5. **Given** a member in that response, **When** it is read, **Then** it names the person by name
   and address and gives the kind of affiliation they hold.
6. **Given** a person whose affiliation to the organization is unverified or has ended, **When**
   the organization is requested, **Then** that person is not among its members.
7. **Given** the list of organizations, **When** it is requested for a type, a country or a parent
   organization, **Then** only matching organizations are returned.
8. **Given** an organization that holds an identifier, **When** the list is requested for that
   identifier, **Then** that organization alone is returned.
9. **Given** an organization with several hundred members, **When** it is requested, **Then** the
   number of database queries does not grow with the number of members.
10. **Given** a member who is an account the people list leaves out, **When** the organization is
    requested, **Then** that member is not listed.

---

### User Story 4 - A developer finds what a person or an organization is credited on (Priority: P2)

Having found a researcher, the directory's developer wants their datasets. The script asks the
dataset list for that person and receives the public datasets they are credited on, each one
complete. It does the same for an institute's projects.

**Why this priority**: It closes the loop from a contributor to their work. It follows the first
three because the records and the contributors must be readable first.

**Independent Test**: For a person credited on a public dataset, a private dataset and a dataset in
a private project, request the dataset list for that person as a visitor, as the person and as a
member of the private dataset's team.

**Acceptance Scenarios**:

1. **Given** a person or an organization credited on public projects, **When** the project list is
   requested for them, **Then** exactly those projects are returned.
2. **Given** a person or an organization credited on public datasets, **When** the dataset list is
   requested for them, **Then** exactly those datasets are returned.
3. **Given** a contributor credited on a private project, a private dataset or a dataset in a
   private project, **When** either list is requested for them, **Then** that record is not
   returned and not counted, whoever asks.
4. **Given** a contributor who does not exist, or an account the people list leaves out, **When**
   either list is requested for them, **Then** the list is empty.
5. **Given** a response about a person or an organization, **When** it is read, **Then** it gives
   the addresses at which their projects and their datasets are listed.

---

### Edge Cases

- A request to `/api/v1/contributors/`, or to a contributor's old address beneath it, is answered
  as an address that does not exist.
- A contributor is deleted while credited on a record. The credit no longer names anyone, and the
  record is returned without it.
- The organization recorded on a credit is deleted. The credit is returned with no affiliation.
- A person holds two identifiers of different kinds. Both are in every response about them and in
  every credit they hold.
- An identifier of a kind that has no web address to resolve to is returned with its scheme and
  without a scheme address.
- An organization is its own top level. Its parent is empty and the list can be asked for
  organizations with no parent.
- A person's primary affiliation has ended. They have no primary organization in the list, and the
  ended affiliation is still among the affiliations of the single record.
- A person is credited on a private record that the caller may see. The record's own response shows
  the credit. The person's lists of projects and datasets still leave the record out.

## Requirements *(mandatory)*

### Functional Requirements

**Endpoints**

- **FR-001**: The API MUST serve a list and a single-record endpoint for people, and the same for
  organizations, with no configuration by the portal developer. Both MUST be read-only and need no
  authentication.
- **FR-002**: The mixed contributors endpoint MUST be removed. Nothing in the API, its root or its
  documentation may refer to it.
- **FR-003**: A person and an organization MUST each be addressed by short identifier, at one
  address only.
- **FR-004**: Both lists MUST be paged, ordered and limited as FS-011 requires of every list, and
  MUST be able to be narrowed to what changed after or before a given moment.
- **FR-005**: The accounts the portal's own people list leaves out MUST be absent from both lists,
  from an organization's members and from the answer to any filter, and a direct request for one
  MUST be answered as for a person that does not exist.

**People**

- **FR-006**: A person in the list MUST carry their name, given name, family name, identifiers with
  schemes, primary organization, and their addresses in the API and on the portal.
- **FR-007**: A single person MUST carry all of FR-006 together with their other names, biography,
  links, languages, image and every verified affiliation, each with its organization, kind, start,
  end and whether it is primary.
- **FR-008**: The list of people MUST be able to be narrowed to the current members of an
  organization and to the holder of an identifier.

**Organizations**

- **FR-009**: An organization in the list MUST carry its name, type, country, identifiers with
  schemes, and its addresses in the API and on the portal.
- **FR-010**: A single organization MUST carry all of FR-009 together with its other names,
  description, city, links, image, the organization it is part of, the organizations that are part
  of it, and its current members, each with the kind of affiliation they hold.
- **FR-011**: The list of organizations MUST be able to be narrowed by type, by country, by parent
  organization, to those with no parent, and to the holder of an identifier.

**Credits on a record**

- **FR-012**: Every project, dataset, sample and measurement MUST be returned with its credits
  nested in it, in the order the record keeps them, in a list and as a single record alike.
- **FR-013**: A credit MUST carry the contributor's name, whether they are a person or an
  organization, a person's given and family name, the contributor's identifiers each with its
  scheme and scheme address, the roles held on the credit by name and label, and the contributor's
  address in the API.
- **FR-014**: A credit MUST carry the organization recorded on it, with that organization's name,
  identifiers and address in the API. Where the credit records none it MUST show none.
- **FR-015**: A credit MUST NOT carry anything else from the contributor's profile, and MUST NOT
  carry the access level it grants.
- **FR-016**: Creators and other contributors MUST NOT be separated. A record has one list of
  credits.
- **FR-017**: A credit held by an account the people list leaves out MUST be returned with its
  name, identifiers and roles and without an address.
- **FR-018**: The fields of a credit MUST be enough to fill a DataCite creator or contributor
  entry (name, name type, given name, family name, name identifiers with schemes, and affiliation
  with identifier and scheme) without a further request.

**A contributor's records**

- **FR-019**: The project list and the dataset list MUST be able to be narrowed to the records a
  given person or organization is credited on. The answer MUST hold public records only, for every
  caller.
- **FR-020**: A person and an organization MUST each carry the addresses at which their projects
  and datasets are listed.

**Privacy**

- **FR-021**: No response may carry a person's email address, a credential, any account detail, a
  portal role or a preference.
- **FR-022**: No response may carry about a person or an organization anything their public page
  does not show to a visitor who is not signed in. An affiliation MUST be shown only when verified,
  and a member only while their verified affiliation has not ended.
- **FR-023**: No response may contain an internal database number.

**Performance**

- **FR-024**: The number of database queries for a page of people, a page of organizations, or a
  page of records with their credits MUST NOT grow with the number of entries on the page, and for
  a single organization MUST NOT grow with the number of its members.

**Documentation**

- **FR-025**: The generated API documentation MUST show the people and organizations endpoints with
  the fields of a list entry and of a single record, their filters, and the shape of a credit on
  each kind of record.
- **FR-026**: The documentation for portal developers MUST describe the two endpoints, what a list
  entry leaves out, the shape of a credit and how it corresponds to a DataCite creator or
  contributor, and how to list a contributor's projects and datasets.
- **FR-027**: FS-011's specification MUST be brought up to date wherever it describes the
  contributors endpoint or the shape of a credit, so that it reads as the API now behaves.

### Key Entities

- **Person**: a credited individual. Read at the people endpoint, compact in the list and complete
  as a single record.
- **Organization**: a credited institution, which may be part of another. Read at the
  organizations endpoint in the same two forms.
- **Contribution**: one contributor's credit on one project, dataset, sample or measurement, with
  its roles and the organization the contributor is credited from. The API calls it a credit and
  returns it inside the record.
- **Affiliation**: a person's membership of an organization over a period. Shown on a person, and
  as a member on an organization, only when verified.
- **Contributor identifier**: an external identifier a person or organization holds, such as an
  ORCID iD or a ROR ID, returned with its scheme.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A script builds a complete DataCite creator entry for every credit on a dataset from
  the one response that returned the dataset.
- **SC-002**: A script pages through every person a portal holds, and separately every
  organization, without meeting an entry of the other kind.
- **SC-003**: A single person or organization read through the API carries what their public page
  shows a visitor who is not signed in, and nothing that page does not.
- **SC-004**: No response of any endpoint carries an email address or an account detail of a
  person.
- **SC-005**: A page of one hundred datasets, each with ten credits, is answered with the same
  number of database queries as a page of one.
- **SC-006**: Starting from a person, a script reaches every public dataset they are credited on in
  one further request for each page.
- **SC-007**: The generated documentation describes the people endpoint, the organizations endpoint
  and a credit with fields that match what is returned.

## Assumptions

- FS-011's API, FS-019's rules on what a contributor's page shows, and FS-022's credits are as
  their own specifications describe them. This feature changes what FS-011 says about contributors
  and credits and nothing else.
- Nothing has been released that carries the API, so an endpoint can be removed and the shape of a
  credit changed without a new version in the address.
- A contribution keeps one organization. Where DataCite allows several affiliations on one entry,
  a credit gives the one it has.
- Samples and measurements are not offered as lists narrowed to a contributor, because a
  contributor's page lists projects and datasets only.
- A portal developer cannot replace the person and organization serializers in this feature.
