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

## Projects and datasets do not choose a template by type

Samples and measurements are polymorphic, and portals subclass them, so a type needs somewhere to
put its own fields. Projects and datasets have fixed schemas that portals do not extend. A portal
that wants a different project page overrides the template the usual way, and the shared
`overview.` blocks give it the same points to change as a sample type has.
