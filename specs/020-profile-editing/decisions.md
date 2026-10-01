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
