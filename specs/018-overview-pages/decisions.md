# Decisions: 018-overview-pages

Questions settled while writing the specification without asking the maintainer, with the reasoning
behind each. The maintainer's own rulings are recorded under *Clarifications* in `spec.md`.

## Where the extra cards go in the facts column

The agreed order is citation, identifiers and licence, people, parent record, dates. Two kinds of
card fall outside it. The readiness checklist goes first. It is shown only to the team, and it is
the one card that asks them to act, so it belongs where they look first. Cards particular to one
kind of record (funding on a project, related publications and versions on a dataset) go between
the people credited and the parent record. They describe the record itself, and the parent record
and dates describe where it sits.

## Development data uses the accounts FairDM already ships

The four redesign branches each created `regular.user`, `staff.user` and `super.user` accounts at
`example.com`. FairDM ships five development accounts through `create_dev_accounts` (ADR 0022),
and check `fairdm.E501` reports those addresses if they reach a portal outside development.
Accounts created anywhere else escape that check. So the development data command calls
`create_dev_accounts` and gives its records to those accounts. The Data Curator account sees every
state of every page, and the Regular User account sees what a signed-in visitor sees.

## Projects and datasets do not choose a template by type

Samples and measurements are polymorphic, and portals subclass them, so a type needs somewhere to
put its own fields. Projects and datasets have fixed schemas that portals do not extend. A portal
that wants a different project page overrides the template the usual way, and the shared
`overview.` blocks give it the same points to change as a sample type has.

## "Released" as one defined term

The redesigns each described the same visibility rule in their own words ("public and published",
"released to the viewer", "open"). The specification uses one term with one meaning, defined under
*Key entities*, so the rule reads the same wherever it applies.
