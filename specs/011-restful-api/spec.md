# Feature Specification: The REST API reads and writes complete records

**Feature Branch**: `011-restful-api`

**Created**: 2026-03-31. Rewritten 2026-10-08 after an audit of the specification against the code.

**Status**: Draft

**Goals**: G10: data and metadata are reachable by machines through a documented API. G2:
registering a model is enough to get a working portal surface. G12: private and public data sit side
by side, controlled per object.

**Roadmap**: R11, the machine-readable API.

**Input**: Every record a portal holds should be reachable by a program, complete, with nothing for
the portal developer to write. A script reads a whole project, dataset, sample, measurement or
contributor. A person with the right level on a record creates it, changes it and deletes it through
the API, under the same access rules as the portal's pages. A portal developer who registers a
sample or measurement type gets its endpoints with no further work, and can say which fields they
carry. A person reaches the API with a token they create and revoke on their own account pages. The
API documents itself, and its limits suit a research group running one small server.

## What exists, and what this specification changes

The API has been in the code since April 2026 and the roadmap lists it as delivered and unverified.
An audit on 2026-10-08 ran it against the demonstration portal. Reading a list or a single record
works. Almost nothing else does what was specified:

- Creating a sample or a measurement fails with a server error, for every registered type.
- Creating a dataset succeeds and discards the project it was sent with.
- A project or dataset is returned as five or six fields. Its descriptions, key dates, identifiers,
  keywords, contributors, licence and owner are absent.
- A measurement is returned without any of its measured values, and a sample without its dataset.
- Sorting a list of samples or measurements fails with a server error.
- Records refer to each other by internal database number, while their addresses use the short
  identifier.
- A token is obtained by posting an email address and a password to the API, which takes no account
  of two-factor sign-in.

This specification states what the API is for and requires the code to meet it. Each difference
between the earlier specification and the code, what was decided about it and why, is recorded in
[decisions.md](decisions.md).

## Boundary

- **Writing a record's descriptions, key dates, identifiers, keywords and contributors through the
  API** is a separate feature. Here they are read with the record and changed in the portal. So is
  creating a contributor through the API.
- **Searching through the API** belongs to roadmap item R17, which delivers one search for the
  portal and the API together.
- **The pages on which a person creates and revokes a token** are django-mvp-accounts' own. This
  feature turns them on and makes the API accept their tokens.
- **A record's page showing its API address** is #432.
- **Import and export of tabular data** is R21. **Dataset versions in the API** is R23.
- **The location module's GeoJSON endpoints** are not part of this feature. That file imports code
  that no longer exists and is never loaded, which makes it roadmap item R20's to remove or repair.

## Clarifications

### Session 2026-10-08

These questions came out of the audit. Each was answered from the maintainer's reply to the audit's
reading, from the roadmap and from the specifications this one sits beside, without putting it to
the maintainer again. The reasoning is in [decisions.md](decisions.md).

- Q: How does one record name another, such as a dataset naming its project? → A: By the short
  identifier that is already in the record's address, together with the address itself. Internal
  database numbers do not appear anywhere in the API, in what it returns or in what it accepts.
- Q: What does "the complete record" contain? → A: Everything a visitor who may see the record is
  shown on its overview page: its own fields, its parent, its descriptions, key dates, identifiers,
  keywords, licence, owner and credited contributors. A sample or measurement also carries every
  field its registered type declares for the API.
- Q: Which of those can be written here? → A: The record's own fields, its visibility and its
  parent. The rest are read-only in this feature and say so in the documentation.
- Q: Who may create, change and delete? → A: Whoever may do the same thing in the portal. The level
  a person holds on a record decides it, the creator is credited at the manage level, and changing
  visibility or moving a record needs the manage level. These rules are FS-022's and are not
  restated differently here.
- Q: What stops a record being deleted? → A: What stops it in the portal. A project with a public
  dataset is refused, and so is a sample with measurements made on it. The API refuses with a
  reason and deletes nothing.
- Q: Does the API accept replacing a whole record as well as changing part of one? → A: Both. A
  partial change leaves every field it does not name as it was.
- Q: How does a person get a token? → A: On their account pages, after signing in the way the
  portal requires, two-factor included. The API has no endpoint that exchanges a password for a
  token and none for resetting or changing a password.
- Q: Can a browser session use the API? → A: Yes, for a person signed in to the portal, which is
  what lets the documentation page try a request. A script uses a token.
- Q: May a page on another website call the API? → A: Yes, to read, and to write with a token. A
  portal's sign-in cookie is never accepted from another website.
- Q: What are the limits on use? → A: Two for each kind of caller, one over a short window to stop
  a burst and one over a day. A caller with a token is allowed several times what an anonymous
  caller is. A page of results is large enough that walking a whole dataset takes few requests, and
  a caller may ask for larger pages up to a stated ceiling. The figures are chosen at planning for a
  single small server and every one of them is a setting.
- Q: Does the changed output need a new version in the address? → A: No. No release has carried the
  API, so `/api/v1/` is still the first version.
- Q: The earlier specification asked for a group of three API links in the sidebar and a setting
  for a documentation link. Are they kept? → A: No. The maintainer reduced the sidebar to one link
  to the API documentation in August 2026, and that stands. The setting has nothing left to read it
  and is removed.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A developer reads a complete record with a script (Priority: P1)

Someone writing an analysis script wants a dataset from a portal. They ask the API for the list of
datasets, pick one, and receive it whole: its name, its project, its licence, its descriptions, key
dates, identifiers and keywords, and the people credited on it. They follow the address of its
samples, receive each sample with every field its type records, and follow on to the measurements
with their measured values. They narrow a list to the rows they want and sort it. They never signed
in, because the dataset is public.

**Why this priority**: Reading is what almost every caller does, and G10 asks for data and metadata.
A record returned as a name and two dates meets neither half.

**Independent Test**: Load development data. Without signing in, request the list and one record of
each of the five kinds, and compare what is returned with what the record's overview page shows.
Filter and sort each list. Request a private record, and a record that does not exist.

**Acceptance Scenarios**:

1. **Given** a public project, dataset, sample or measurement, **When** anyone requests it,
   **Then** the response carries its own fields, its parent, its descriptions, key dates,
   identifiers, keywords and credited contributors, and for a dataset its licence.
2. **Given** a record that sits under another, **When** it is returned, **Then** it names its
   parent by short identifier and by address, and requesting that address returns the parent.
3. **Given** a sample or measurement of a registered type, **When** it is returned, **Then** it
   carries every field that type declares for the API, together with the fields every sample or
   every measurement has.
4. **Given** any response from the API, **When** it is read, **Then** it contains no internal
   database number, for the record or for anything it refers to.
5. **Given** a contributor, **When** anyone requests them, **Then** the response carries what
   their public profile page shows, and never an email address, a password or anything about their
   account.
6. **Given** a list of more records than one page holds, **When** it is requested, **Then** the
   response says how many there are in all and gives the address of the next and previous pages.
7. **Given** a registered type that declares filters, **When** its list is requested with one of
   them, **Then** only matching records are returned.
8. **Given** any list, **When** it is requested in a named order, ascending or descending,
   **Then** the records come back in that order.
9. **Given** a private record, **When** a visitor or a signed-in person with no level on it
   requests it, **Then** it is in no list they receive, and requesting it directly is answered as a
   record that does not exist is.
10. **Given** a private record, **When** someone holding at least the view level on it requests
    it, **Then** they receive it.
11. **Given** samples and measurements in a private dataset, **When** someone with no level on the
    dataset requests them, **Then** none is returned and none is counted.

---

### User Story 2 - A member of a record's team creates, changes and deletes records through the API (Priority: P1)

A laboratory's instrument software holds a token belonging to a researcher on a dataset's team.
After each run it creates a sample in that dataset, then a measurement on the sample with the
measured values. When a value is corrected it changes that one field. When a run is thrown out it
deletes the measurement. A colleague who is only a viewer of the dataset tries the same and is
refused each time.

**Why this priority**: This is the change the maintainer asked for. The endpoints accept these
requests today and most of them fail, so the API is read-only in practice.

**Independent Test**: With a token for someone at the edit level on a dataset, create a sample of a
registered type in it, create a measurement on the sample, change one field of each, and delete
both. Create a dataset in a project and a project. Repeat each step as a viewer, as someone with no
level, and with no token.

**Acceptance Scenarios**:

1. **Given** someone at the edit level on a dataset, **When** they create a sample of a registered
   type naming that dataset, **Then** the sample exists in that dataset with the values sent, and
   the response is the complete new record.
2. **Given** someone at the edit level on a sample, **When** they create a measurement of a
   registered type on it with its measured values, **Then** the measurement exists with those
   values.
3. **Given** someone at the edit level on a project, **When** they create a dataset naming that
   project, **Then** the dataset exists in that project.
4. **Given** any signed-in person, **When** they create a project, **Then** it exists and they are
   credited on it at the manage level.
5. **Given** a record a person may change, **When** they send a change to one field, **Then** that
   field changes and every other field is as it was.
6. **Given** a record a person may change, **When** they send a full replacement, **Then** the
   record's writable fields take the values sent.
7. **Given** a record a person may delete, **When** they delete it, **Then** it is gone and a
   later request for it is answered as a record that does not exist is.
8. **Given** a request to create or change a record with a required field missing or a value the
   field does not accept, **When** it is processed, **Then** nothing is saved and the response names
   each field at fault and says why.
9. **Given** a request that names a parent the person may not add to, or one that does not exist,
   **When** it is processed, **Then** nothing is saved and the response says the parent is not one
   they can choose, in the same way for both cases.
10. **Given** a request that tries to set a field the API only reads, such as a description or
    the date a record was added, **When** it is processed, **Then** that field is left as it was.
11. **Given** someone at the edit level and not the manage level, **When** they try to change a
    record's visibility or move it to another parent, **Then** they are refused and nothing changes.
12. **Given** a record the portal refuses to delete, such as a project with a public dataset or a
    sample with measurements, **When** someone who may otherwise delete it tries through the API,
    **Then** it is refused with the reason and nothing is deleted.
13. **Given** a request to create, change or delete with no token and no session, **When** it is
    processed, **Then** it is refused as unauthenticated.
14. **Given** a public record and a signed-in person with no level on it, **When** they try to
    change or delete it, **Then** they are refused. **Given** a private record they cannot see,
    **Then** they are answered as for a record that does not exist.
15. **Given** any valid or invalid write request, **When** it is processed, **Then** the response
    is never a server error.

---

### User Story 3 - A portal developer gets an API for a registered type and decides what it carries (Priority: P2)

A portal developer adds a new sample type and registers it. Without writing anything else, the type
has a list address and a record address, it appears in the API's root and its generated documentation, and its records can
be read and written. The developer then decides the API should carry two fields the tables do not,
and says so in the registration. Later they need a computed field, so they write their own
serializer and name it in the registration. A colleague adds a viewset of their own for something
the registry does not cover.

**Why this priority**: G2 is the framework's promise. It follows the two reading and writing
stories because they define what a generated endpoint must do.

**Independent Test**: Register a new sample type with no API configuration and exercise its
endpoints. Add an API field list and confirm the output follows it. Replace the serializer and
confirm the output is the replacement's. Register a serializer that does not build on the base and
start the portal. Add a custom viewset to the router.

**Acceptance Scenarios**:

1. **Given** a sample or measurement type registered with no API configuration, **When** the portal
   starts, **Then** the type has working list and record endpoints, reading and writing, with a
   default set of fields.
2. **Given** a registration that names the fields for the API, **When** a record is returned,
   **Then** it carries those fields, together with the fields every sample or every measurement has.
3. **Given** a registration that names only the type's general field list, **When** a record is
   returned, **Then** the API uses that list.
4. **Given** a registration that names a serializer of the developer's own, or a configuration that
   overrides how the serializer is obtained, **When** a record is returned, **Then** the API uses
   it.
5. **Given** a developer's own serializer that does not build on the framework's base for samples
   or for measurements, **When** the portal starts, **Then** it refuses to start and says which
   base to build on.
6. **Given** a type registered with a field list that leaves out a field the type requires,
   **When** the portal starts, **Then** the developer is told, before any caller meets a failure.
7. **Given** two registered types, **When** their endpoints are built, **Then** each has its own
   address taken from the type's plural name, and a sample type and a measurement type with the
   same plural name do not collide.
8. **Given** a developer who registers a viewset of their own on the framework's router, **When**
   the portal starts, **Then** it is served beside the generated endpoints and appears in the
   documentation.
9. **Given** a type that fails to register for the API, **When** the portal starts, **Then** the
   failure is reported to the developer and is not swallowed.

---

### User Story 4 - A person reaches the API with a token from their account pages (Priority: P2)

A researcher wants their script to add samples. They sign in to the portal as usual, with their
second factor, open their account pages and create a token that lasts ninety days. They paste it
into the script, which sends it with each request. When the laptop is lost they return to the same
page and revoke the token, and the script's next request is refused.

**Why this priority**: Writing needs a caller the portal can identify. The earlier way of getting a
token asked for a password over the API and ignored two-factor sign-in.

**Independent Test**: Sign in, create a token on the account pages, and use it to create a record.
Revoke it and repeat the request. Let a token expire and repeat. Post an email address and password
to the address the earlier login endpoint had.

**Acceptance Scenarios**:

1. **Given** a signed-in person, **When** they open their account pages, **Then** they can create
   an API token, see the tokens they hold and revoke any of them.
2. **Given** a request carrying a token that is current, **When** it is processed, **Then** it is
   treated as coming from the person who holds the token, with that person's levels.
3. **Given** a request carrying a token that has been revoked, has expired or was never issued,
   **When** it is processed, **Then** it is refused as unauthenticated.
4. **Given** the API, **When** its addresses are listed, **Then** none of them exchanges a
   password for a token, and none resets or changes a password.
5. **Given** a person signed in to the portal in a browser, **When** they use the documentation
   page to try a request, **Then** it is made as them.
6. **Given** a page on another website, **When** it calls the API, **Then** it can read public
   records and can write with a token, and a portal sign-in cookie it carries is not accepted.

---

### User Story 5 - A developer finds out what the API offers and tries it in the browser (Priority: P3)

A developer who has never seen the portal opens its API documentation from the sidebar. The page
lists every endpoint the portal has, including the sample and measurement types this particular
portal registered, with the fields each accepts and returns. They try a request from the page and
read the response. Sample types are together under one heading and measurement types under another, each
operation named for its type and described in its developer's words. Their script asks the API's root which lists exist
and where each one is.

**Why this priority**: Documentation that matches the running portal is what makes the API usable
by someone outside the team. It is generated, so it follows the endpoints being right.

**Independent Test**: Open the documentation from the sidebar on a portal with several registered
types. Check each type appears with its fields, and that read-only fields are marked. Try a request.
Request the API's root.

**Acceptance Scenarios**:

1. **Given** a running portal, **When** anyone follows the sidebar's API link, **Then** they reach
   a documentation page that lists every endpoint, grouped by kind of record.
2. **Given** a registered type, **When** its entry in the documentation is read, **Then** it shows
   the fields that type accepts and returns, which are required, and which are read-only.
3. **Given** the documentation page, **When** a request is tried from it, **Then** a real request
   is sent and its response shown.
4. **Given** the documentation, **When** it describes how to authenticate and what the limits are,
   **Then** what it says is what the portal does.
5. **Given** registered sample and measurement types, **When** the documentation page is read,
   **Then** every sample type's operations are under one heading for samples and every measurement
   type's under one for measurements, each operation is titled with its type's own plural name, and
   a type's list operation carries the description from its registration and, where the
   registration gives them, the authority behind the type, how to cite it, its keywords and a link
   to its repository.
6. **Given** a registered type, **When** the description of its records in the documentation is
   read, **Then** it is the type's own description, and never text written for the framework's
   developers.
7. **Given** the address of the API's root, **When** it is requested, **Then** the response links
   to every list endpoint.

---

### User Story 6 - A portal operator keeps the API within what one small server can carry (Priority: P3)

A research group runs its portal on one modest server. Out of the box, a crawler that hammers the
API is slowed down within seconds and cut off for the day soon after, while a colleague's nightly
harvest with a token runs to completion. When a partner institute needs to pull the whole portal
weekly, the operator raises the limit for signed-in callers in the settings and restarts.

**Why this priority**: The defaults protect a portal nobody has tuned. It comes last because a
portal can launch with the defaults and adjust later.

**Independent Test**: Exceed the anonymous limit and read the refusal. Exceed it again with a token
and confirm the higher limit applies. Change each limit and the page sizes in the settings and
confirm the portal follows them.

**Acceptance Scenarios**:

1. **Given** an anonymous caller, **When** they exceed the short-window limit or the daily limit,
   **Then** further requests are refused as too many, and the refusal says when to try again.
2. **Given** a caller with a token, **When** they make the number of requests that would stop an
   anonymous caller, **Then** they are not stopped, and they are stopped at a higher limit of their
   own.
3. **Given** a list requested with no page size, **When** it is answered, **Then** it holds the
   default number of records. **Given** a larger size is asked for, **Then** it is honoured up to
   the ceiling and no further.
4. **Given** an operator who changes a limit, the default page size or the ceiling in the portal's
   settings, **When** the portal restarts, **Then** the API follows the new value.
5. **Given** a list of several hundred records with their descriptions, dates, identifiers and
   contributors, **When** it is requested, **Then** the number of database queries does not grow
   with the number of records on the page.

---

### Edge Cases

- A request for a sample or measurement type that is not registered is answered as an address that
  does not exist.
- A type's plural name changes between releases of a portal. Its address changes with it. The
  documentation for portal developers says so and says how to keep the old address.
- Two writes reach the same record at once. The later one wins. Detecting the conflict is out of
  scope.
- A record is deleted while a caller is paging through its list. The pages that follow are still
  valid and may be one record short.
- A person's level on a dataset is removed while their token is in use. The next request is judged
  by the level they hold then.
- A caller sends a body the API cannot parse. It is refused as a bad request and nothing is saved.
- A caller sends a request to change a record's parent to the parent it already has. That is not a
  move and needs only the edit level.
- A portal's token feature is restricted to some people. A person who may not hold a token can still
  read public records anonymously.
- The API is asked for a format other than JSON. JSON, and the browsable pages for a person in a
  browser, are the only formats.

## Requirements *(mandatory)*

### Functional Requirements

**Reading**

- **FR-001**: The API MUST serve a list and a single-record endpoint for projects, datasets and
  contributors, and for every sample and measurement type in the registry, with no configuration by
  the portal developer.
- **FR-002**: A single record MUST be addressed by its short identifier.
- **FR-003**: A project, dataset, sample or measurement MUST be returned with its own fields, its
  parent, its descriptions, key dates, identifiers, keywords and credited contributors. A dataset
  MUST also carry its licence, and a project its owner. Each record, and each contributor, MUST
  carry the address of its own page on the portal's website beside its address in the API, so
  that anyone who republishes the record can link back to the portal.
- **FR-004**: A sample MUST always carry the fields common to every sample, and a measurement those
  common to every measurement, whatever field list its type declares. Each MUST also carry every
  field its type declares for the API.
- **FR-005**: A record MUST refer to another record by that record's short identifier and its
  address in the API. No response and no accepted request may contain an internal database number.
- **FR-006**: A contributor MUST be returned with what their public profile shows. No endpoint may
  return an email address, a credential or any other account detail of a person.
- **FR-007**: Every list MUST be paged, and each page MUST carry the total number of records and
  the addresses of the next and previous pages.
- **FR-008**: A list MUST accept the filters its registered type declares, and every list MUST
  accept a named ordering, ascending or descending, on that record type's sortable fields.
- **FR-045**: Every list MUST be able to be narrowed to the records changed after a given moment
  and to those changed before one, so that a caller who has read the list once can ask only for
  what is new.
- **FR-009**: JSON MUST be the API's format, with browsable pages for a person using a browser.

**Access**

- **FR-010**: Reading a public record MUST need no authentication.
- **FR-011**: A list MUST contain only records the caller may see: public ones, and private ones
  the caller holds at least the view level on. Samples and measurements take the visibility of
  their dataset.
- **FR-012**: A request for a single record the caller may not see MUST be answered exactly as a
  request for a record that does not exist.
- **FR-013**: Creating, changing or deleting MUST need an authenticated caller, and MUST be decided
  by the same rule the portal's pages apply to that person and that record.
- **FR-014**: A refused write on a record the caller can see MUST be answered as forbidden. On a
  record the caller cannot see, it MUST be answered as for a record that does not exist.

**Writing**

- **FR-015**: Projects, datasets and every registered sample and measurement type MUST support
  create, full replacement, partial change and delete. Contributors are read-only.
- **FR-016**: A record's own fields, its visibility and its parent MUST be writable. Its
  descriptions, key dates, identifiers, keywords and contributors MUST be read-only, and an attempt
  to set one MUST leave it unchanged.
- **FR-017**: Creating a record under a parent MUST need the level on that parent that the portal
  requires for the same act, and the parents a caller may name MUST be the ones they may add to.
- **FR-018**: The person who creates a record MUST be credited on it as its creator, as FS-022
  requires, and the caller MUST NOT be able to name someone else as creator.
- **FR-019**: Changing a record's visibility or moving it to another parent MUST need the manage
  level, and a move that would leave the record with nobody able to manage it MUST be refused.
- **FR-020**: A delete the portal refuses for the state the record is in MUST be refused by the API
  with the reason.
- **FR-021**: A request that fails validation MUST save nothing and MUST name each field at fault
  with the reason.
- **FR-022**: No request, valid or not, may be answered with a server error because of what the
  caller sent.

**For portal developers**

- **FR-023**: The fields a generated endpoint carries MUST come from the registration: the API's
  own field list where one is given, otherwise the type's general list, otherwise a default.
- **FR-024**: A serializer the developer names in the registration, or supplies by overriding how
  the configuration obtains it, MUST be the one the API uses. There MUST be one way the framework
  builds a serializer for a registered type.
- **FR-025**: A developer's own serializer for a sample or measurement type MUST build on the
  framework's base for that kind, and the portal MUST refuse to start when it does not.
- **FR-026**: A registration whose API fields cannot produce a record that can be created, or a
  type that fails to get its endpoints, MUST be reported to the developer when the portal starts.
- **FR-027**: A generated endpoint's address MUST come from the type's plural name, under a prefix
  for samples or for measurements. API route names MUST stay separate from the names of the
  portal's pages.
- **FR-028**: The framework MUST expose its router so a developer can add a viewset of their own
  beside the generated ones.

**Tokens and sessions**

- **FR-029**: The API MUST accept a token a person created on their account pages, and MUST refuse
  one that is revoked, expired or unknown.
- **FR-030**: The portal MUST turn on the account pages for creating, listing and revoking tokens
  that django-mvp-accounts provides. This feature builds no such page of its own.
- **FR-031**: The API MUST have no endpoint that exchanges a password for a token, and none that
  resets or changes a password or edits an account.
- **FR-032**: The API MUST accept the portal's own sign-in session from the portal's own pages.
- **FR-033**: The API MUST be callable from pages on other websites, for reading and for writing
  with a token, and MUST NOT accept a sign-in cookie sent from one.

**Documentation and discovery**

- **FR-034**: The portal MUST serve an interactive documentation page generated from the running
  endpoints, showing for each the fields accepted and returned, which are required and which are
  read-only, and allowing a request to be tried.
- **FR-044**: The generated documentation MUST name the ways of authenticating in plain words. It
  MUST NOT show the name of the package that provides tokens.
- **FR-035**: What the generated documentation says about authentication, limits and paging MUST
  match what the portal does.
- **FR-036**: The generated documentation MUST group every registered sample type under one
  heading and every measurement type under another. Each operation MUST be titled with its type's
  own plural name, and a type's list operation MUST carry the description its registration gives,
  with the authority, citation, keywords and repository link where the registration gives them. It
  MUST NOT show a maintainer's name or email address. The portal serves one documentation page.
  The API serves no separate catalogue of types.
- **FR-037**: The API's root MUST link to every list endpoint.
- **FR-038**: The sidebar MUST carry one link to the API documentation.
- **FR-039**: The documentation for portal developers MUST describe the registration options that
  shape the API, the base serializers, the router, and every setting this feature reads. The
  documentation for people using a portal MUST describe getting a token and calling the API.

**Limits**

- **FR-040**: The API MUST limit how many requests a caller makes over a short window and over a
  day, with separate, higher limits for an authenticated caller than for an anonymous one.
- **FR-041**: A refusal for too many requests MUST say when the caller may try again.
- **FR-042**: Every limit, the default page size and the largest page size a caller may ask for
  MUST be a setting, with defaults chosen for a portal on one small server.
- **FR-043**: The number of database queries behind a list response MUST NOT grow with the number
  of records on the page.

### Key Entities

- **Record**: a project, dataset, sample or measurement. It has its own fields, a visibility of its
  own or its dataset's, a parent except for a project, and metadata the API reads with it.
- **Contributor**: a person or an organisation credited on records. Read-only in the API.
- **Registered type**: a kind of sample or measurement a portal developer has added through the
  registry. Its registration decides what its API endpoints carry.
- **Token**: a secret a person creates on their account pages and a script sends with each request.
  It stands for that person until it expires or is revoked.
- **Level**: what a person may do with a record: view, edit or manage. Defined by FS-022.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a portal with development data, a record of each of the five kinds read through
  the API carries everything its overview page shows a visitor.
- **SC-002**: A person with a token completes create, change and delete on a project, a dataset and
  one record of every registered sample and measurement type, with no failure.
- **SC-003**: A portal developer adds a sample type and a measurement type by registering them, and
  both can be read and written through the API with no other code.
- **SC-004**: No private record, and no count of private records, reaches a caller who may not see
  it, on any endpoint.
- **SC-005**: A person with two-factor sign-in turned on cannot obtain a token without passing it.
- **SC-006**: Every endpoint the portal serves appears in the generated documentation with fields
  that match what the endpoint accepts and returns.
- **SC-007**: A caller walks a dataset of ten thousand samples in no more than a hundred requests,
  and an anonymous caller doing so stays within the default limits.
- **SC-008**: The automated tests send every kind of valid and invalid request this specification
  describes, and none is answered with a server error.

## Assumptions

- The registry, the four record types, contributors and the levels of FS-022 are as their own
  specifications describe them. This feature changes none of them.
- django-mvp-accounts provides the token pages from version 0.2.0, using django-rest-knox. The
  portal is moved to that version, and to the django-mvp release it needs, in a change of its own
  that lands before this feature is built.
- A portal in production has the shared cache it is already required to have, which the request
  limits count in.
- Nothing has been released that carries the API, so its output can change without a new version in
  the address.
- JSON is the only data format. File upload and download, bulk operations in one request, and
  detecting conflicting writes are out of scope.
