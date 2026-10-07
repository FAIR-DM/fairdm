# Sketch: 027-contact-and-report

A prototype of the screens in `spec.md`, built to be looked at before anything is planned. It
has no tests. The markup, the wording and the layout are what is being shown. The code behind them
is throwaway and is rebuilt test-first when the feature is planned.

## What exists

**Records and people.** Projects, datasets, samples, measurements, people and organizations each
have an overview page built on one shared template, `overview/page.html`. A contribution carries
roles, and "Contact Person" is one of them. The dataset creation form already gives it to whoever
creates a dataset. A person is active, claimed, invited or unclaimed, and only an active, claimed
person has an address the portal can write to. An affiliation has a type, and owner and
administrator are the two that run an organization.

**Rights.** "May edit" is a permission on the record (`dataset.change_dataset` and its
equivalents), held either through a portal role or as a grant on the one record. Samples and
measurements are visible through their dataset. The Data Curator portal role is a group.

**Pages.** A plugin is a page attached to a record, registered with `@plugins.register`. Every
plugin today is either a tab or a page reached from somewhere else, such as the editing pages. A
form page built on the shared form view gets its title, breadcrumbs and layout for free.

**The header.** Each overview fills an `overview.actions` block with buttons: Cite and Share by
default, then a Manage menu for people with rights. Projects, datasets and samples have a Manage
menu. Measurements have none yet. A person's page carries a Contact button that is disabled and
says it is not available. Notices go above the header in `overview.notices`.

**What is missing.** There is no dropdown of actions open to any visitor. This feature draws one
for its own two actions. The portal sends email for sign-in and nothing else, and it has no record of messages
or reports. The portal-wide contact page writes to the people running the portal and is a
different thing.

## The screens

| Screen | What it is |
|---|---|
| The actions dropdown | A "More" dropdown at the end of every overview header, holding Contact and Report a problem where each applies |
| Contact | The record, who the message goes to and why them, what it is about, the message, the note about the sender's address, Send |
| Contact, blocked | The same page with the form left out: address not confirmed, or the day's limit reached |
| Report a problem | The record, the description, the note about who sees it, Send |
| Reported problems | Open and Resolved tabs. Each report shows who made it, when, which record, the text, and a "Mark as resolved" panel with an optional note |
| The notice | For people who may edit a record with open reports: a line above the header saying how many, with a Review button |
| The Manage entry | "Reported problems" in the Manage menu, with the open count |
| Three emails | The message to recipients, the new report to the people who can fix it, and "resolved" to the reader. Plain text |

## What the screens need from the code

- The Contact page needs the list of people a message will go to, and which rule chose them:
  named contact, the record's maintainers, the data curators, the person, or the organization's
  owner and administrators.
- The actions dropdown needs to know, for the visitor looking at the page, whether anyone would
  receive a message, so Contact is left out when nobody would.
- The Contact page needs the choices of subject for this kind of record: three on a project or
  dataset, none on a person or organization, where the question is not asked at all.
- Both sending pages need to know whether the visitor's email address is confirmed and whether
  they have reached the day's limit, before drawing the form.
- Both sending pages need the visitor's own email address, to show it in the note above the
  button.
- The limit message needs the portal's number.
- Sending needs to return the visitor to the record with a confirmation.
- The list needs each report's reporter, time, text, state, the record it is about and that
  record's kind as its own type calls itself ("rock sample", not "sample").
- A dataset's list needs the reports on the dataset and on every sample and measurement in it. A
  sample's or measurement's list needs only its own.
- The tabs need a count of open and of resolved reports.
- A resolved report needs who resolved it, when, and the note.
- The notice and the Manage entry need the open count, and only for someone who may edit the
  record.
- Each email needs full addresses for the record, the sender's profile and the list of reports.
- A message to several people needs to be sent one email per person, so none sees another's
  address.
- The administration interface needs both records listed: messages without text, reports with it.

## What the sketch faked

- Nothing about the actions dropdown. It is one component, `c-actions.page`, drawn by the shared
  overview template from a template tag that knows only about these two actions, and that is how
  it is meant to be built. Contact and Report a problem are ordinary plugins kept out of the tab
  strip.
- A measurement's Manage menu. Measurements have none until #404. The sketch draws one that
  holds only the reported-problems entry.
- Who may edit. The recipients and the list read the grants that exist today. Specification
  022 (#402) changes how a team grants rights, and the rule will follow it.
- A sample's or measurement's maintainers. With no grants of its own, the sketch falls back to
  the dataset's.
- The daily limit. A count over the last 24 hours against a hard-coded default of 10, read
  from a setting that is not documented.
- Email. Sent to the console by the development settings. There is no handling of a failed
  send, and the "From" line is whatever the portal's default is.
- Sign-in and return. A signed-out visitor is sent to sign in and comes back to the form. A
  visitor who signs up from there was not followed through.
- Recipients worked out twice. The page shows them and sending works them out again, with
  nothing said to the sender if they changed in between.
- Deleting a record. Reports on a deleted sample or measurement are hidden from the list. They
  are not deleted with the record, as the specification requires.
- No tests, no documentation, no translations.
- Seeded accounts. `regular.user2` has an unconfirmed address and `regular.user3` is at the
  limit. The seeded staff account holds a grant on each showcase dataset.

## What was ruled by eye

Nothing has been reviewed yet. These are the choices made without a rule to settle them, each open
to being changed on sight:

- The dropdown is labelled "More" and sits last in the header, after Manage.
- Contact and Report a problem share one page layout.
- The Contact page names the recipients, with their pictures, and says in one line why the message
  goes to them.
- The subject is three radio buttons, with a general question chosen to start with.
- The note about the sender's address sits directly above the Send button, as a soft information
  alert, and shows the address itself.
- A blocked sender sees the reason and no form.
- Reports are a list, open first, with resolved ones behind a second tab.
- Resolving opens under the report it belongs to. The note is optional and the button says
  "Resolve and notify".
- Open reports raise a warning-coloured notice above the header for the people who may edit the
  record, as well as a count in the Manage menu.
- The empty list carries a tick and one sentence.

## Where the choices to confirm would move a screen

`decisions.md` lists six choices for the maintainer to confirm. This is what each one changes
here.

1. **Sign-in required.** If anyone could send, the Contact and report pages gain a name field and
   an email field, and something to stop automated senders. The "confirm your email address"
   screen goes away, and the limit can no longer be per account.
2. **Recipients.** The "Goes to" block on the Contact page shows the outcome of this rule and the
   sentence under it names which step applied. A different rule changes those sentences and
   nothing else.
3. **Reports are tracked.** If a report were only an email, the reported-problems list, the
   notice, the Manage entry and the "resolved" email all go. The report page stays, and its note
   loses the promise of an email when it is resolved.
4. **Abuse limits.** Without a daily limit the "today's limit" screen goes. If the text of a
   Contact message were kept, the note above the Send button would have to say so.
5. **No opting out.** If a person could opt out, their page would lose Contact and a direct visit
   to the form would be refused, as it already is for a person without an account. No new screen
   here; the setting itself would live with profile editing.
6. **This prototype.** No effect on the screens.
