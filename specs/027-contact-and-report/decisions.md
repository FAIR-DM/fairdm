# Decisions: 027-contact-and-report

The request (#407) fixed which pages carry each action, that no email address is exposed, and that
Contact also covers asking for early access and asking to borrow a specimen. It left four things
open: who receives each message, whether a visitor must be signed in, how abuse is limited, and
whether a reported problem is tracked. Everything below was settled while writing the
specification, without asking the maintainer.

## For Sam to confirm

Each of these changes what gets built, and none was decided in the request. The reasoning for each
is in the section of the same name further down.

1. A visitor must be signed in, with a verified email address, to send a message or report a
   problem. The alternative is to let anyone send after a spam check.
2. A Contact message about a project or dataset goes to its Contact Person contributors, then to
   the people who may edit it, then to the Data Curators. A problem report goes to the people who
   may edit the record, then to the Data Curators.
3. A reported problem is tracked: it stays on the record as open until resolved, is listed in the
   Manage menu, and is seen only by the people who may edit the record. The alternative is that a
   report is only an email, which removes the fourth user story.
4. Abuse is limited by the sign-in rule, a daily limit per account that a portal can change, and a
   record of who sent what in the administration interface. The portal does not keep the text of a
   Contact message.
5. Nobody can opt out of being contacted.
6. The message form, the report form and the list of reports get a prototype for review before
   they are planned.

## Sending requires a signed-in account with a verified email address

A form that emails researchers on behalf of anyone on the internet is a spam relay, and the people
it would be aimed at are the ones the portal exists to serve. The usual defence, a challenge the
visitor solves, adds a dependency and an accessibility cost and still lets a determined sender
through. An account costs a reader one sign-in, which on most portals is their ORCID iD.

It also gives the recipient something an anonymous form cannot: a name linked to a profile, and a
reply address the portal has verified. A reply therefore reaches a real person.

The cost is real. A reader who spots a wrong value and has no account must make one before saying
so, and some will not. That is why the actions stay visible to a signed-out visitor and lead
through sign-in back to the same form.

## Recipients of a Contact message on a project or dataset

The Contact Person contribution role exists to answer "who do I write to about this", and the
dataset create form already gives it to whoever creates a dataset. Using it means a team decides
who receives messages in the place it already manages its credits.

A team that named nobody, or whose contact people have no account, still has people who may edit
the record, so they come next. When a record's whole team is made of people without accounts, the
Data Curators are the people on the portal with rights over it, and a message about its data is
better with them than nowhere.

People whose only right to edit comes from a portal role are left out of the middle step.
Otherwise every Data Curator would receive every message about every record that lacks a contact
person.

## Recipients for a person and an organization

A person without an active account has no address the portal can reach, or has one they never
confirmed, so the action is not offered. Routing those messages to the community managers was
considered and dropped: a message written to one researcher is not something portal staff can
answer.

An organization's owner and administrators are the people specification 020 lets edit its profile,
so they are the people who speak for it. Ordinary members are not.

## Who is told about a reported problem

The people who can fix it. A report that goes to someone credited on the record who may not change
it produces a forwarded email at best. The Data Curators are the fallback for the same reason as
above.

## A reported problem is tracked, privately

If a report were only an email, Report a problem would be Contact with a different recipient list,
and a report would be lost the first time it landed in a mailbox nobody reads. Keeping it on the
record with two states is the least that makes it a different thing: it can be found later, by
someone who was not on the original email, and it can be shown to be dealt with.

It stays private to the people who may edit the record. A public list of problems is a statement
about a dataset's quality that its team has not reviewed, and readers could use it to say anything
about anyone. Discussion in public is what the planned discussions addon is for.

A dataset's list includes reports on its samples and measurements because a dataset's maintainer
works dataset by dataset. A measurement's reports appear under the measurement's own dataset, not
its sample's, because the two can differ and the measurement's team is the one that can fix it.

Two states and no more. Assigning a report to someone, labelling it, or rejecting it with a reason
are each a step toward an issue tracker, and nothing in the request asks for one. Resolving with a
note covers "fixed" and "not a problem" alike.

## The reader is told when their report is resolved

Someone who took the trouble to report a wrong value should learn what happened to it, and it
costs one email. They get no page listing their reports, which would be a second surface to build
for little gain.

## Replies go straight to the sender, and the sender is told so

The portal has to hide recipients' addresses, and the simplest way for a recipient to answer is to
reply to the email. That hands the sender's address to the recipients, so the form says so before
sending. A recipient who replies reveals their own address by choosing to, as with any
correspondence. Relaying replies through the portal so that neither side ever sees an address
would be a mail system of its own.

## The text of a Contact message is not kept

It is correspondence between two parties, and holding it would make portal staff able to read
researchers' mail. What the portal keeps (sender, record, subject, time) is enough to see a
pattern of abuse, and a recipient who complains has the email itself.

## A daily limit per account, counted across both actions

Signing in stops anonymous abuse and does nothing about one account writing to two hundred people.
A cap per day does. Counting messages and reports together leaves one number to set and no way to
get twice the allowance. The portal can change the number because a small community portal and a
large public one will want different values.

Blocking an individual sender, beyond deactivating the account, is left out. Deactivation already
exists and is what a portal would do to someone abusing it.

## Early access and specimen loans are subjects of a message, nothing more

The request says Contact covers both so that neither needs an action of its own. So each is a
choice of subject that tells the team what kind of request they are reading. Nothing is granted
by sending one. Access is granted where access to the record is managed, and a loan is arranged
between people.

The two requests are offered on projects and datasets and not on people or organizations, where
there is no data or specimen to ask about.

## Contact on a person's page replaces the placeholder from specification 019

Specification 019 put a contact action on a person's page marked as not available. The plan in
#397 lists Contact as a page action. This specification requires one working action on the page
and leaves where it sits to #401, which owns the dropdown.

## Sample pages do not get Contact

The plan lists Contact on projects, datasets, people and organizations. A request to borrow a
specimen would most naturally start from the sample's own page, which this leaves out. The plan's
list was the maintainer's, so it is kept, and the gap is noted under Assumptions in the
specification.

## No opting out

A setting to refuse contact needs a place to live, and a person's privacy settings are named in
specifications 019 and 020 as later work. Until then the sender is always identified and limited,
and the recipient's address is never shown.

## The existing portal-wide contact page is left alone

The portal already serves a general contact page that writes to the people running the portal. It
answers a different question, so it is neither reused nor removed.

## A prototype before planning

This feature puts two new forms and one new list in front of people, and what the sender is told
about their address being shared is a judgement about wording and placement that a test cannot
make. That fits the rule for building a prototype first.
