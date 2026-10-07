# Feature Specification: Visitors can contact a record's team and report a problem

**Feature Branch**: `027-contact-and-report`

**Created**: 2026-10-02

**Status**: Draft

**Goals**: G21: a portal supports the research community around it, not only its data.

**Roadmap**: R30, a portal supports its research community. This is one slice of that item. It is
also one of the page actions listed in the plan for what record pages offer (#397).

**Input**: A visitor who finds a wrong value in a dataset, or who wants to ask its team a question,
has no route to them from the portal. Email addresses are not shown, so there is no route outside
it either. Two page actions ship with FairDM. Contact, on projects, datasets, people and
organizations, reaches the record's team, or the person or organization, without exposing anyone's
email address. It also covers asking for data ahead of publication and asking to borrow a specimen,
so neither needs an action of its own. Report a problem, on datasets, samples and measurements,
lets a reader flag something wrong with the record, and the people responsible for it are told.

## Clarifications

### Session 2026-10-02

The request left four things to settle. Each was settled while writing this specification, and the
reasoning is in `decisions.md`.

- Q: Must a visitor be signed in to send a message or report a problem? → A: Yes, with an account
  whose email address is verified. A visitor who is not signed in is offered both actions and is
  sent to sign in first, then returned to where they were.
- Q: Who receives a Contact message about a project or a dataset? → A: The people credited on it
  with the Contact Person contribution role who have an active account. When there are none, the
  people who may edit the record. When there are none of those either, the people holding the Data
  Curator portal role.
- Q: Who receives a Contact message about a person or an organization? → A: The person, when they
  have an active account. For an organization, its owner and administrators. When nobody can
  receive it, the action is not offered.
- Q: Who is told about a reported problem? → A: The people who may edit the record. When none of
  them has an active account, the people holding the Data Curator portal role.
- Q: Is a reported problem tracked on the record, or is it only a message? → A: It is tracked. A
  report stays on the record as open until someone who may edit the record marks it resolved. Only
  those people see it. The reader who reported it is told when it is resolved.
- Q: How is abuse limited? → A: Sending needs a signed-in account with a verified email address.
  One account can send a limited number of messages and reports in a day, a number the portal can
  change. Every message and report is recorded where portal staff can see who sent it, about which
  record, and when.
- Q: How does a recipient answer without the portal exposing their address? → A: The message
  arrives by email and a reply goes straight to the sender. The sender is told before sending that
  their own address will be given to the recipients. A recipient who replies reveals their address
  by their own choice, as with any email.
- Q: Does asking for data ahead of publication give the sender access? → A: No. It is a message
  like any other. Whoever receives it decides, and grants access where access to the record is
  managed.
- Q: Is the text of a Contact message kept by the portal? → A: No. The portal records that it was
  sent, by whom, about which record and when. A reported problem is different: its text is kept,
  because the report stays on the record.
- Q: May a person or an organization's team choose not to be contacted? → A: Not in this
  specification. See Assumptions.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A visitor asks a project's or dataset's team a question (Priority: P1)

A researcher reading a dataset wants to know how one column was measured. They open the page
actions and choose Contact. They say what the message is about, write it, and send it. The people
named as the dataset's contact receive it by email, with the researcher's name, a link to the
dataset and the message. One of them replies from their own mailbox and the reply goes straight to
the researcher. At no point did the portal show the researcher anyone's address.

The same action carries two other kinds of request. A researcher who wants the data before the
dataset is published says so when choosing what the message is about. So does one who wants to
borrow a specimen. The team sees which kind of request it is before reading it.

**Why this priority**: A dataset is the unit a portal distributes, and its team is who a reader
most often needs. This story also delivers everything the others build on: the form, the delivery,
the rule that no address is shown, and the limits on sending.

**Independent Test**: Load development data. Sign in as a seeded user with no part in a seeded
dataset, open the dataset, send a message through Contact, and read the email the portal sent.
Repeat on a project. Then try the same signed out, and as one of the dataset's own contacts.

**Acceptance Scenarios**:

1. **Given** a signed-in visitor on a project or dataset they may open, **When** the page actions
   are shown, **Then** Contact is among them and leads to a page where a message is written.
2. **Given** a visitor writing a message, **When** they choose what it is about, **Then** the
   choices include a general question, a request for data ahead of publication and a request to
   borrow a specimen.
3. **Given** a visitor who writes a message and sends it, **When** it is sent, **Then** every
   recipient receives an email naming the sender, the record with a link to it, what the message is
   about, and the message itself. The visitor is returned to the record and told the message was
   sent.
4. **Given** a dataset with two people credited as Contact Person who have active accounts,
   **When** a message is sent, **Then** those two receive it and nobody else does.
5. **Given** a dataset with nobody credited as Contact Person, or whose contact people have no
   active account, **When** a message is sent, **Then** the people who may edit the dataset
   receive it.
6. **Given** a dataset where nobody credited on it has an active account, **When** a message is
   sent, **Then** the people holding the Data Curator portal role receive it.
7. **Given** a record for which nobody at all can receive a message, **When** its page is opened,
   **Then** Contact is not offered, and a direct request to the message page is refused.
8. **Given** a recipient who replies to the email, **When** the reply is sent, **Then** it is
   addressed to the visitor who wrote the message and not to the portal.
9. **Given** a visitor about to send, **When** the page is shown, **Then** it says that their own
   email address will be given to the people who receive the message.
10. **Given** any page, confirmation or email the visitor sees while sending, **When** it is read,
    **Then** it contains no recipient's email address.
11. **Given** a visitor who sends an empty message, or one longer than the portal accepts,
    **Then** nothing is sent, the field says what is wrong, and what they typed is still there.
12. **Given** a visitor who is not signed in, **When** they choose Contact, **Then** they are sent
    to sign in, and afterwards arrive at the message page for the same record.
13. **Given** a signed-in visitor whose email address is not verified, **When** they choose
    Contact, **Then** nothing can be sent and they are told how to verify their address.
14. **Given** a person who would be the only recipient of a message about a record, **When** they
    open that record, **Then** Contact is not offered to them.
15. **Given** a private dataset, **When** someone who may not open it requests its message page,
    **Then** they are refused exactly as they are refused the dataset itself.
16. **Given** a message asking for data ahead of publication, **When** it is sent, **Then** the
    sender's access to the dataset is the same as before.
17. **Given** a message that contains markup or a script, **When** a recipient reads the email,
    **Then** it appears as the text the sender typed and nothing in it runs.

---

### User Story 2 - A visitor contacts a person or an organization (Priority: P2)

A researcher finds a collaborator's profile and wants to write to them. The Contact action on the
person's page leads to the same message page as on a dataset. The person receives the message by
email and replies directly. On an organization's page the message goes to the organization's owner
and administrators.

**Why this priority**: Specification 019 shipped a contact action on a person's page that says it
is not available yet. This story makes it work. It follows the first story because it reuses the
whole of it and changes only who receives the message.

**Independent Test**: Load development data. Sign in as a seeded user, open another seeded
person's profile and send a message. Open an organization with an owner and send one. Then open a
profile nobody has claimed and an organization with no owner or administrator.

**Acceptance Scenarios**:

1. **Given** a signed-in visitor on the page of a person with an active account, **When** they send
   a message through Contact, **Then** that person receives it and nobody else does.
2. **Given** the page of a person who has no active account, whether unclaimed, invited or
   deactivated, **When** it is opened, **Then** Contact is not offered and a direct request to the
   message page is refused.
3. **Given** a person on their own page, **When** it is shown, **Then** Contact is not offered.
4. **Given** an organization with an owner and two administrators who have active accounts,
   **When** a message is sent from its page, **Then** those three receive it and its ordinary
   members do not.
5. **Given** an organization with no owner or administrator who has an active account, **When**
   its page is opened, **Then** Contact is not offered.
6. **Given** a person's or an organization's page, **When** the visitor chooses what the message is
   about, **Then** requests for data and for a specimen are not among the choices.
7. **Given** a person's page, **When** it is shown to someone who may contact them, **Then** there
   is one Contact action on it, and it works.

---

### User Story 3 - A reader reports a problem with a dataset, sample or measurement (Priority: P2)

A reader notices that a measurement's value is a thousand times too large, most likely a unit
slip. They choose Report a problem from the measurement's page actions, describe what is wrong and
send it. The people who can correct the measurement are told by email, with a link to the
measurement and to the report. The reader is told the report was received.

**Why this priority**: A wrong value that nobody can flag stays wrong, and every reuse of the
dataset carries it forward. It sits beside the second story because both need the first, and
neither needs the other.

**Independent Test**: Load development data. Sign in as a seeded user with no part in a seeded
dataset. Report a problem on the dataset, on one of its samples and on one of its measurements.
Read the emails sent, then confirm the same pages offer no such action on a project, a person or
an organization.

**Acceptance Scenarios**:

1. **Given** a signed-in reader on a dataset, sample or measurement they may open, **When** the
   page actions are shown, **Then** Report a problem is among them and leads to a page where the
   problem is described.
2. **Given** a reader who describes a problem and sends it, **When** it is sent, **Then** a report
   is recorded against that record as open, the reader is returned to the record and told the
   report was received.
3. **Given** a report on a sample, **When** it is sent, **Then** the people who may edit that
   sample and have an active account are told by email, with the reader's name, a link to the
   sample and the description.
4. **Given** a record that nobody with an active account may edit other than through a portal
   role, **When** a problem is reported on it, **Then** the people holding the Data Curator portal
   role are told.
5. **Given** a record for which no email can be sent to anyone, **When** a problem is reported,
   **Then** the report is still recorded as open.
6. **Given** a reader who sends an empty description, or one longer than the portal accepts,
   **Then** nothing is recorded, the field says what is wrong, and what they typed is still there.
7. **Given** a reader who is not signed in, **When** they choose Report a problem, **Then** they
   are sent to sign in, and afterwards arrive at the report page for the same record.
8. **Given** a project, a person or an organization, **When** its page actions are shown, **Then**
   Report a problem is not among them.
9. **Given** someone who may edit a record, **When** they open it, **Then** Report a problem is
   still offered to them, and a report they make is recorded like any other.
10. **Given** a record a reader may not open, **When** they request its report page, **Then** they
    are refused exactly as they are refused the record itself.
11. **Given** a reader with no right to edit the record, **When** they look for reports others have
    made on it, **Then** the portal shows them none.

---

### User Story 4 - The people responsible for a record work through its reported problems (Priority: P3)

A dataset's maintainer opens its Manage menu and sees that it has reported problems. The list
shows each open report: who made it, when, which record it is about and what it says. Reports made
on the dataset's samples and measurements are in the same list, so nothing has to be hunted for
record by record. The maintainer corrects the value, marks the report resolved and adds a line
saying what was done. The reader who reported it receives that line by email.

**Why this priority**: Recording a report has value on its own, because the people responsible are
emailed. Working through reports in the portal is what stops one being lost in a mailbox, and it
can follow.

**Independent Test**: Load development data that includes open reports on a dataset, one of its
samples and one of its measurements. Sign in as someone who may edit the dataset, open the list,
resolve one report with a note and read the email sent. Then sign in as a user with no rights and
request the list.

**Acceptance Scenarios**:

1. **Given** someone who may edit a dataset, sample or measurement, **When** they open its Manage
   menu, **Then** it has an entry leading to the record's reported problems.
2. **Given** a dataset with open reports on itself, on a sample in it and on a measurement in it,
   **When** its list is opened, **Then** all three reports are in it, each saying which record it
   is about, and each leading to that record.
3. **Given** a sample with one open report, **When** the sample's own list is opened, **Then** it
   shows that report and none made on other records.
4. **Given** an open report, **When** someone who may edit the record marks it resolved, with or
   without a note, **Then** it is no longer among the open reports, and it records who resolved it
   and when.
5. **Given** a report that is resolved, **When** the reader who made it has an active account,
   **Then** they are told by email that it was resolved, with the note if one was written.
6. **Given** a resolved report, **When** the list is asked for resolved reports, **Then** the
   report is there with its note.
7. **Given** a resolved report that was resolved by mistake, **When** someone who may edit the
   record reopens it, **Then** it is among the open reports again.
8. **Given** someone who may not edit a record, **When** they open it, **Then** the Manage menu has
   no entry for reported problems. **When** they request the list, or try to resolve a report,
   **Then** they are refused and nothing changes.
9. **Given** a record with open reports, **When** someone who may edit it opens the record,
   **Then** the page tells them how many open reports it has. Nobody else is told.
10. **Given** a record with no reports, **When** its list is opened, **Then** the page says there
    are none.
11. **Given** a measurement whose dataset differs from its sample's dataset, **When** a problem is
    reported on the measurement, **Then** the report is in the list of the measurement's own
    dataset and not in the list of the sample's dataset.

---

### User Story 5 - A portal keeps these actions from being abused (Priority: P3)

A portal administrator hears from a researcher that the same account has written to them a dozen
times. In the administration interface they find every message and report that account has sent:
when, and about which record. They deactivate the account. Before it came to that, the portal had
already refused the account's messages past the day's limit.

**Why this priority**: The first story already requires a signed-in sender with a verified
address, which stops anonymous abuse. The limit and the record are what a portal needs once
someone with an account misbehaves.

**Independent Test**: Set the daily limit to three. Sign in as a seeded user and send three
messages, then a fourth. Sign in as a portal administrator and find the three in the
administration interface.

**Acceptance Scenarios**:

1. **Given** a sender who has reached the day's limit, **When** they send another message or
   report, **Then** nothing is sent or recorded as a report, and they are told they have reached
   the limit.
2. **Given** the limit, **When** it is counted, **Then** Contact messages and reported problems
   count together.
3. **Given** a portal that has set its own limit, **When** a sender reaches that number, **Then**
   that is where they are refused. A portal that sets none gets the limit FairDM ships.
4. **Given** a message that was sent, **When** a portal administrator looks in the administration
   interface, **Then** they find who sent it, about which record, what it was about and when, and
   not the text of the message.
5. **Given** a reported problem, **When** a portal administrator looks in the administration
   interface, **Then** they find it with its text, its state, and who resolved it.
6. **Given** a sender whose account is deactivated, **When** they try to send, **Then** they cannot
   sign in and so cannot send.
7. **Given** a message refused for any reason, **When** the day's count is taken, **Then** the
   refused message is not counted.

---

### Edge Cases

- The portal cannot send email at all. A Contact message is refused, and the sender is told it was
  not sent. A reported problem is still recorded, and the people responsible find it in the list.
- A recipient's account is deactivated between the page being opened and the message being sent.
  Recipients are worked out when the message is sent, so that person does not receive it. When
  nobody is left, the message is refused and the sender is told it could not be delivered.
- An organization is credited as a dataset's Contact Person. An organization credited on a record
  receives nothing through that record. Only people do.
- The sender is one of several recipients. They are left out, and the others receive the message.
- A record is deleted while it has reports. Its reports go with it.
- A reader who reported a problem later has their account deactivated. The report stays, still
  naming them, and no email is sent to them when it is resolved.
- A dataset is made private after a reader reported a problem on it. The report stays for the
  people responsible. The email telling the reader it was resolved names the record and carries
  the note, and gives them no access to the record.
- The same reader reports the same problem twice. Both are recorded. Nothing merges them.
- A sample or measurement type with its own overview template. Both actions are offered on it as
  on any other type.
- The portal-wide contact page a portal already has is unchanged. It writes to the people running
  the portal, not to a record's team.

## Requirements *(mandatory)*

### Functional Requirements

**The two actions**

- **FR-001**: Contact MUST be a page action on project, dataset, person and organization pages,
  and on no other record's page.
- **FR-002**: Report a problem MUST be a page action on dataset, sample and measurement pages,
  including every registered sample and measurement type, and on no other record's page.
- **FR-003**: The page actions of a record MUST be offered together in one dropdown in the header
  of its overview, open to any visitor and separate from the Manage menu. FairDM writes the
  dropdown's entries itself. The dropdown MUST NOT be shown when it would hold nothing for this
  visitor.
- **FR-004**: Each action MUST be offered only on a record the visitor may open, and a request for
  its page on a record the visitor may not open MUST be refused in the same way the record is.
- **FR-005**: The contact action specification 019 shows on a person's page as not available MUST
  be replaced by this one. A page MUST NOT carry two contact actions.

**Who may send**

- **FR-006**: Sending a Contact message or reporting a problem MUST require a signed-in account
  with a verified email address.
- **FR-007**: A visitor who is not signed in MUST still be offered both actions, MUST be sent to
  sign in when they choose one, and MUST arrive afterwards at the page for the same action on the
  same record.
- **FR-008**: A signed-in visitor without a verified email address MUST be told how to verify it
  and MUST NOT be able to send.

**Who receives a Contact message**

- **FR-009**: On a project or dataset, the recipients MUST be the people credited on it with the
  Contact Person contribution role who have an active account. When there are none, the recipients
  MUST be the people who may edit the record and have an active account, not counting anyone whose
  only right to edit comes from a portal role. When there are none, the recipients MUST be the
  people holding the Data Curator portal role.
- **FR-010**: On a person's page, the recipient MUST be that person, and only when they have an
  active account.
- **FR-011**: On an organization's page, the recipients MUST be the people whose affiliation to it
  is of the owner or administrator type, has not ended, and who have an active account.
- **FR-012**: An organization credited on a record MUST NOT make anyone a recipient.
- **FR-013**: The sender MUST NOT be among the recipients of their own message.
- **FR-014**: When nobody would receive a message, Contact MUST NOT be offered and a request for
  its page MUST be refused. Recipients MUST be worked out again when the message is sent.

**The Contact message**

- **FR-015**: The sender MUST say what the message is about. On a project or dataset the choices
  MUST include a general question, a request for data ahead of publication and a request to borrow
  a specimen. On a person or organization the two requests MUST NOT be offered.
- **FR-016**: A message MUST be required and MUST have a maximum length. A refused message MUST
  send nothing, say what is wrong, and keep what the sender typed.
- **FR-017**: Each recipient MUST receive the message by email. The email MUST name the sender,
  link to the sender's profile and to the record, say what the message is about, and carry the
  message as the plain text the sender typed.
- **FR-018**: A reply to that email MUST go to the sender's address.
- **FR-019**: Before sending, the sender MUST be told that their email address will be given to
  the recipients.
- **FR-020**: No page, confirmation or email shown or sent to the sender MUST contain a
  recipient's email address. Recipients MUST NOT be shown one another's addresses.
- **FR-021**: After sending, the sender MUST be returned to the record and told the message was
  sent. When the message could not be sent, they MUST be told that instead.
- **FR-022**: A message MUST NOT change anyone's access to any record, whatever it asks for.
- **FR-023**: The portal MUST NOT keep the text of a Contact message. It MUST record who sent it,
  about which record, what it was about and when.

**Reporting a problem**

- **FR-024**: A description MUST be required and MUST have a maximum length. A refused report MUST
  record nothing, say what is wrong, and keep what the reader typed.
- **FR-025**: A report MUST be recorded against the record it was made on, with the reader who
  made it, the description and the time, in the open state.
- **FR-026**: The people who may edit the record and have an active account, not counting anyone
  whose only right to edit comes from a portal role, MUST be told of a new report by email. When
  there are none, the people holding the Data Curator portal role MUST be told. The email MUST
  name the reader, link to the record and to the report, and carry the description as plain text.
- **FR-027**: A report MUST be recorded whether or not anyone could be emailed.
- **FR-028**: After reporting, the reader MUST be returned to the record and told the report was
  received.
- **FR-029**: Someone who may edit a record MUST be able to report a problem on it like anyone
  else.

**Working through reports**

- **FR-030**: A report MUST be either open or resolved.
- **FR-031**: Reports MUST be visible only to people who may edit the record they were made on,
  and to portal staff in the administration interface. Nobody else MUST be able to see that a
  record has reports, how many, or what they say.
- **FR-032**: The Manage menu of a dataset, sample and measurement MUST carry an entry leading to
  that record's reported problems, shown only to people who may edit the record and refused to
  anyone else.
- **FR-033**: A sample's or measurement's list MUST show the reports made on that record. A
  dataset's list MUST show the reports made on the dataset and on every sample and measurement
  that belongs to it, each naming and linking to the record it is about.
- **FR-034**: The list MUST show open reports first by default, MUST be able to show resolved
  ones, and MUST say so when there are none.
- **FR-035**: Someone who may edit the record MUST be able to mark an open report resolved, with
  an optional note, and to reopen a resolved one. The report MUST record who resolved it and when.
- **FR-036**: When a report is resolved, the reader who made it MUST be told by email, with the
  note when there is one, provided they have an active account.
- **FR-037**: A record with open reports MUST tell the people who may edit it how many it has,
  when they open the record.
- **FR-038**: Deleting a record MUST delete its reports.

**Limits and oversight**

- **FR-039**: One account MUST be limited in how many Contact messages and reports, counted
  together, it can send in a day. A sender at the limit MUST be refused and told why. A refused
  message MUST NOT count.
- **FR-040**: A portal MUST be able to set that limit through a documented setting, and FairDM
  MUST ship a default.
- **FR-041**: Portal staff MUST be able to find, in the administration interface, every Contact
  message's sender, record, subject and time, and every report with its text, state and resolver.
- **FR-042**: Text entered by a sender or reader MUST be shown and emailed as plain text.

**Documentation**

- **FR-043**: The documentation for portal users MUST describe contacting a record's team and
  reporting a problem, and say that the sender's address is given to the recipients.
- **FR-044**: The documentation for portal administrators MUST say who receives each kind of
  message, what the portal records, how the daily limit is set, and that sending needs outgoing
  email to be configured.

### Requirements by user story

| User story | Requirements |
|---|---|
| US-1: a visitor asks a project's or dataset's team a question | FR-001, FR-003, FR-004, FR-006 to FR-009, FR-012 to FR-023, FR-042, FR-043, FR-045 |
| US-2: a visitor contacts a person or an organization | FR-001, FR-005, FR-010, FR-011, FR-013 to FR-015 |
| US-3: a reader reports a problem | FR-002 to FR-004, FR-006 to FR-008, FR-024 to FR-029, FR-031, FR-042, FR-043 |
| US-4: the people responsible work through reports | FR-030 to FR-038 |
| US-5: a portal keeps these actions from being abused | FR-023, FR-039 to FR-041, FR-044 |

### Key Entities

- **Contact message**: one message from a signed-in person about a project, dataset, person or
  organization. The portal delivers it and keeps a record of who sent it, about which record, on
  what subject and when. It does not keep the text.
- **Reported problem**: a reader's description of something wrong with a dataset, sample or
  measurement. It belongs to that record, is open or resolved, and when resolved records who
  resolved it, when, and their note.
- **Recipient**: a person with an active account who receives a Contact message or is told of a
  reported problem. Always a person, never an organization.
- **Contact Person**: the contribution role that names who to write to about a project or dataset.
  It decides who receives a Contact message and gives its holder no rights.
- **Page action**: an entry in the dropdown of actions open to any visitor on a record's
  overview. FairDM writes the entries itself, and Contact and Report a problem are the two it has.
- **Manage menu**: the menu shown only to people with rights over a record. The entry for reported
  problems lives there.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A signed-in visitor can go from a dataset's page to a sent message to its team in
  under a minute, without leaving the portal's own pages and without being shown an email address.
- **SC-002**: Across every seeded record, each Contact message reaches exactly the people FR-009
  to FR-014 name for it, and nobody else.
- **SC-003**: No page served to a sender, and no email sent to a sender, contains the email address
  of any recipient.
- **SC-004**: Every problem reported is in the list of the record it was made on until someone
  resolves it, including when no email could be sent.
- **SC-005**: Someone who may edit a dataset can see every open report on it and on its samples and
  measurements from one page, and resolve one in a single step.
- **SC-006**: For every seeded account, the reports it can see are exactly those on records it may
  edit, and every other request for a list or a report is refused.
- **SC-007**: An account at the daily limit sends nothing more that day, and nothing it sends is
  delivered or recorded as a report.
- **SC-008**: The message page, the report page and the list of reports do not scroll sideways at
  widths of 375, 768, 1024 and 1440 pixels.
- **SC-009**: Each example in the documentation this feature adds or changes runs as written.

## Assumptions

- This feature draws the page actions dropdown itself, for the two actions it ships. There is no
  way for a portal or an addon to add an action to it, take one away or replace one. A request for
  that (#401) was decided against until developers building on FairDM need it.
- "May edit the record" means whatever the portal's access rules say when the message is sent.
  When #402 lets a team set permissions per contributor, the recipients follow those permissions
  with no change here.
- A sample or measurement has a Manage menu for the entry in FR-032 to live in, as specification
  018 describes for samples and #404 for measurements.
- Nobody can opt out of being contacted. A person with an active account can be written to, and so
  can an organization's owner and administrators. A setting for this belongs with the privacy
  settings a later specification covers.
- The choices for what a message is about are the ones FairDM ships. A portal that wants others
  changes them in its own project.
- A Contact message has no thread in the portal. The conversation continues by email. Discussion
  on a record is left to an addon.
- Reports are not public. A public list of known problems on a dataset would be a different
  feature.
- A reader does not get a page listing the reports they have made. They are told by email when one
  is resolved.
- The portal-wide contact page is unchanged.
- Outgoing email is configured on the portal. Without it, Contact messages are refused and reports
  are recorded without notification.
- Whether a sample page should offer Contact, for a request to borrow that specimen, is not
  changed here. The request is made from the sample's dataset.
