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
the chain upward. The administration interface is where this has been guarded until now, and the
editing page keeps the same rule.

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

**ADR:** none. It follows the shape 019 set with `is_managed_by`, local to contributors.

## D3. Superusers get nothing extra on the editing pages

The specification lists who may edit and ends "nobody else", and SC-003 holds every seeded account
to that list. A superuser changes any record in the administration interface, as before.

**ADR:** none. A reading of the specification.

## D4. Editing your own profile is tested on who is signed in

Only an active account can sign in, so the signed-in user being the person is enough. A community
manager's right is tested on the profile's state: anything other than claimed.

**ADR:** none. Local to this feature.

## D5. The website is the first stored link

There is no website field and 019's checklist counts any link as "A website". The form offers
"Website" and "Other links" and stores them together, website first, so the stored shape and
everything that reads it stay as they are.

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

**ADR:** none yet. Judged again at convergence, once the code exists.
