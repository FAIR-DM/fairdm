# Decisions: 020-profile-editing

Questions settled while writing the specification without asking the maintainer, with the reasoning
behind each. The maintainer's own rulings are recorded under *Clarifications* in `spec.md`.

## An invited person's profile is maintained by community managers

The maintainer ruled that a person with an active account maintains their own profile and that in
any other state the community managers do. A person who has been invited and has not yet signed in
has no active account, so their profile falls to the community managers until they do.

## Regaining an active account takes the profile back

The right to edit is checked again on save. A profile claimed, or an account made active again,
while a community manager has the editing page open refuses that save, because the record is now
its owner's. Changes a community manager saved before that stay as they were left.

## Community managers get the edit action but not the checklist

Specification 019 shows the completeness checklist and the management menu only to the people
responsible for one record, so that portal staff do not see a checklist on every profile they open.
That stands. A community manager is offered the edit action alone.

## Portal administrators are not given the right

The Portal Administrator role can change person records in the administration interface today. The
maintainer named one role for editing in the portal, so the specification keeps to it. A portal
that wants its administrators to edit profiles puts them in the Community Manager role as well.

## Identifiers are not typed in

A ROR identifier and an ORCID iD both carry a meaning beyond their text: 019 distinguishes an ORCID
iD the person authenticated from one that was typed. Letting either be entered on an editing page
would blur that, so both stay where they are set today.

## Hand edits to fields filled from ORCID or ROR are allowed

Nothing refreshes a record from its registry yet, so there is nothing for a hand edit to conflict
with. Marking such fields now would describe behaviour that does not exist.

## A parent that would form a loop is refused

An organization that is part of itself, directly or through others, breaks every page that walks
the chain upward. Nothing guarded this before, so the rule goes on the model (D6 below).

# Decisions made while planning and building

## D1. Built while another pull request was open

The queue holds a repository while any pull request is open, and #383 (the overview image banner)
was. The maintainer said to build alongside it. The two touch different templates, apart from the
shared overview skeleton, which this feature does not change.

**ADR:** none. A scheduling record for this run.

## D2. The right to edit is a method on the record, not a Django permission

`contributors.change_person` is held by Portal Administrators as well as Community Managers, and
the specification gives Portal Administrators nothing. The rule also depends on the state of the
profile. `is_editable_by(user)` on the record states the whole rule in one place and the page and
the overview both ask it.

**Revisit if:** a third kind of editor is added, at which point a permission backend may read
better than a growing method.

**ADR:** docs/adr/0024-the-right-to-edit-a-profile-is-asked-of-the-record.md

## D3. Superusers get nothing extra on the editing pages

The specification lists who may edit and ends "nobody else", and SC-003 holds every seeded account
to that list. A superuser changes any record in the administration interface, as before.

**ADR:** docs/adr/0024-the-right-to-edit-a-profile-is-asked-of-the-record.md

## D4. Editing your own profile is tested on who is signed in

Only an active account can sign in, so the signed-in user being the person is enough. A community
manager may edit a person whose account is inactive, or who is not claimed and has never signed
in. The account state alone would hand them the profiles of people who signed up without email
verification, or were made with `createsuperuser`, since nothing marks those accounts claimed.

**ADR:** none. Local to this feature.

## D5. The website is the first stored link

There is no website field and 019's checklist counts any link as "A website". The form offers
"Website" and "Other links" and stores them together, website first, so the stored shape and
everything that reads it stay as they are.

A consequence: clearing the website and saving makes the next link the website when the form is
reopened, and an organization imported from ROR with only a Wikipedia address shows that as its
website.

**Revisit if:** a website needs to be told apart from other links anywhere but this form.

**ADR:** none. No stored shape changes.

## D6. The parent loop guard goes on the model

The specification says the administration interface already refuses a parent that would form a
loop. It does not. The check goes into `Organization.clean`, so the editing page and the
administration interface both refuse it.

**ADR:** none. A validation rule, stated in the model's own docstring.

## D7. Lists are typed one per line

Alternative names and links are short hand-typed lists. A text area with one entry per line needs
no JavaScript and no new dependency. Languages are a multiple choice over ISO 639-1.

**ADR:** none. A form detail.

## D8. A setting names the two forms

`FAIRDM_PROFILE_FORMS` maps `person` and `organization` to dotted paths, as allauth's
`ACCOUNT_FORMS` does for the account forms this package already configures. A registered page's
form cannot otherwise be replaced from a portal's own code.

**Revisit if:** registered pages gain a general way to be replaced.

**ADR:** none. One setting, documented in the developer guide, following a setting the package already uses.

## D9. A person's given and family names are not on the editing page

The specification lists the fields and says "nothing else", and given and family name are not
among them. Citations and exported metadata are built from the given and family names where they
are set, so a changed name reaches credits and lists but not those. Raised with the maintainer as
a question about the specification. Until it is ruled, the page edits `name` only.

**ADR:** none. An open question on the specification.

## D10. Design review: what was carried instead of changed

- An owner may make their organization part of any other organization, which then lists it among
  its sub-organizations. The specification forbids only loops. Left as specified, and noted for
  the specification that covers organization membership.
- The parent field is a plain select unless the package already has an organization picker.
- A deactivated editor is signed out by Django, so a page test of one expects the redirect to
  sign in. The inactive check stays in `is_editable_by` for portals whose sign-in backend keeps
  inactive users signed in.

**ADR:** none. Review notes for this feature.

## D11. The shipped fallback form lives on the page, the default in the setting

`FAIRDM_PROFILE_FORMS` ships with a `person` entry (the documented default). `Update` also keeps
its own `shipped_forms` map, so a portal that deletes the setting or names only another kind still
gets the shipped form without the setting being read back through a default.

**Revisit if:** the organization form lands and the two maps start to drift; the page could then
read the setting's default instead.

**ADR:** none. Where a default lives, local to one class.

## D12. The ISO 639-1 code list is a module constant

The languages field offers the same codes the model's validator accepts. The set lived inside the
validator function, so it moved to `ISO_639_1_CODES` in `validators.py` and the function reads it
there. No behaviour of the validator changed.

**ADR:** none. A constant moved within its module.

## D13. Checklist links changed three existing overview tests

The person checklist now links the photo, biography and links items to their fields (FR-017).
Three existing tests asserted that the ORCID item's link was the checklist's only link, so they
now assert on the ORCID link itself: it is present while the item is missing, and gone once ORCID
is connected. The links to the editing fields are asserted in full by the new tests in
`TestPersonOverview`. Named here because `tasks.md` allows changing only tests that pinned a
disabled stand-in; these pinned the absence of links the story adds.

**ADR:** none. A test maintenance record.

## D14. The saved message crashed the page a save returns to

Saving a profile redirects to the overview with a success message. The message list is drawn by
django-mvp's `messages` component, which hands each message's `level_tag` to the alert as its
variant and icon name. `MESSAGE_TAGS` in `fairdm/conf/settings/apps.py` still held the old
Bootstrap-era mapping (`"success alert-success"`), so the tag was not an icon name and the overview
raised `IconNotFoundError` for as long as a message was waiting. The first story's tests stopped at
the redirect and never opened the page it leads to. The setting is removed, so Django's own tags
(`success`, `error`, `warning`, `info`, `debug`) reach the component. Nothing in `fairdm/` or `demo/`
reads `message.tags`.

This is outside the files the story names. It is a separate commit so it can be reverted alone, and
the two tests that open the page after a save (`TestReturnToTheOverview`) fail without it.

**Revisit if:** a portal's own templates style messages by the old tag strings.

**ADR:** none. Removal of an unused setting, named in the changelog.

## D15. The parent field uses the package's organization picker

`AffiliationForm` already selects an organization with django-autocomplete-light's `ModelSelect2`
against `autocomplete:organization`, so the parent field uses the same widget. The two select2
widgets in `forms/widgets.py` are multiple choice and do not fit a single parent. The picker
searches every organization, the one being edited included, and the refusal then arrives as an
error on the field naming the reason (code `parent_loop`) instead of the generic "not a valid
choice" a narrowed queryset would give.

**Revisit if:** the picker should hide the organizations that would be refused.

**ADR:** none. A widget choice for one field.

## D16. Editing an organization requires an active account

`Organization.is_editable_by` is `is_managed_by(user)` and `user.is_active`. `is_managed_by` alone
does not look at the account, and an inactive account must not keep the right even where the
sign-in backend lets it stay signed in (D10). There is no superuser or community manager term in
this story.

**ADR:** none. Covered by the record of who may edit, ADR 0024.

## D17. One base form for the two profile forms

An error the model raises for a field the form lacks is attached to the form as a whole, in
`ProfileForm._update_errors`, which both profile forms extend. Overriding `_update_errors` keeps
Django's own handling for every error on a field the form has, and the page needs nothing more. The
`form_tag = False` line both forms repeated moved into the same base.

**Revisit if:** a third kind of form needs the same, at which point it is already shared.

**ADR:** none. A base class local to one module.

## D18. A stored ROR address fails the model's own check

`Organization.clean` matches a stored ROR identifier against `^0[a-z0-9]{6}[0-9]{2}$`, the bare
identifier. `update_identifier` stores `synced_data["id"]`, and ROR's records give that as the full
address (`https://ror.org/02nr0ka47`), which fails the check: `full_clean` on an organization holding
it reports an error on `identifiers`. With the fix in D17 such an organization shows a form-level
error and cannot be saved from the editing page. The seeded organizations store bare identifiers
and are not affected. Left alone, because the check is outside this story's files and the right
answer (accept the address, or store the bare identifier) is the model's to settle. Reported in the
completion report.

**ADR:** none. A defect record, fixed by D19.

## D19. A stored ROR address validates

`Organization.clean` removes a leading `https://ror.org/` from a stored ROR value before matching
the bare-identifier pattern, so both forms validate and a malformed value of either form still
fails on `identifiers`. `update_identifier` is unchanged and still stores the address it is given,
as D18 left it. This settles the open point D18 reported.

**Revisit if:** the model should store only the bare identifier, which would be a data migration.

**ADR:** none. A validation detail on one field.

## D20. A manager's page has no disabled edit entry

Everyone who sees the management menu or the About card's prompt on an organization may edit it,
so the disabled versions of the edit entry and the prompt had no viewer and were removed.

**ADR:** none. A template cleanup.

## D21. The migration smoke test fails now and then, on main as well

`tests/test_smoke.py::TestMigrations::test_every_model_change_has_a_migration` failed in one of
four full parallel runs on main and at the same rate on this branch, and passes alone. It is not
caused by this feature and is left for its own fix.

**ADR:** none. A defect record for another piece of work.

## D22. Review findings fixed directly

The code review approved with no critical or high finding. Five of its seven low findings were a
few lines each and were fixed without a dispatched story: the two documentation pages that said
three seeded accounts now say five, the photo and logo fields refuse formats the page does not
name, a list field accepts at most 50 lines, the developer guide says a form that keeps the
website field has to keep the links field, and the test that posted fields the page does not
carry now posts real model fields and checks each stored value.

Two were carried. A stored record that fails the model's validation on a field the page does not
carry cannot be saved from the page, and the message does not yet say where to correct it. An old
script for a contribution dialog looks for a message class the removed setting used to supply,
and the dialog it belongs to already depends on a library the package no longer loads.

**ADR:** none. A record of the review's fixes.
