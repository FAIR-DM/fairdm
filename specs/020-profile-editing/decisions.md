# Decisions: 020-profile-editing

Questions settled while writing the specification without asking the maintainer, with the reasoning
behind each. The maintainer's own rulings are recorded under *Clarifications* in `spec.md`.

## A claimed profile of a deactivated account stays closed to community managers

The maintainer ruled that a community manager edits a person's profile only while it is unclaimed,
and that a claimed profile is its owner's alone to maintain. A claimed profile whose account has
been deactivated has an owner who cannot sign in. The specification keeps to the claim: the profile
is still that person's, deactivation is often temporary, and the administration interface remains
for a correction that cannot wait.

## A claim made while a community manager is editing wins

The right to edit is checked again on save, so a profile claimed in the meantime refuses the
community manager's save. The alternative would let a stale page overwrite what is now the
owner's record.

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
