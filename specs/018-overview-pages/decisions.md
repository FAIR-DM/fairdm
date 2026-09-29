# Decisions: 018-overview-pages

Questions settled while writing the specification without asking the maintainer, with the reasoning
behind each. The maintainer's own rulings are recorded under *Clarifications* in `spec.md`.

## Where the extra cards go in the side column

The side column's order is readiness, Details, timeline, People, Identifiers, Funding, citation. Two
kinds of card fall outside it. The readiness checklist goes first. It is shown only to the team, and
it is the one card that asks them to act, so it belongs where they look first. Cards particular to
one kind of record (a dataset's related publications, a sample's location and related samples, a
measurement's sample location) go last. The shared cards then sit in the same position on every
page, whatever a record adds.

## The measurement page maps its sample only when the sample may be seen

A measurement can be published while its sample's dataset is not. The page already describes such a
sample without naming or linking it, and a map would give away where it was taken, so the map
follows the same rule as the sample's name.

## A sample's type badge opens the registry's description too

The review moved the measurement type's description into a dialog on its badge. Samples read the
same registry description through the same helper, so the sample page does the same rather than
keeping a card the measurement page no longer has.

## Projects and datasets do not choose a template by type

Samples and measurements are polymorphic, and portals subclass them, so a type needs somewhere to
put its own fields. Projects and datasets have fixed schemas that portals do not extend. A portal
that wants a different project page overrides the template the usual way, and the shared
`overview.` blocks give it the same points to change as a sample type has.
