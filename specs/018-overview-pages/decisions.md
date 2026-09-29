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

## D1 — Implementation starts from the reviewed prototype

The pages were built and reviewed as a working prototype before this plan was written, and the
specification describes what that review settled. The implementation keeps the prototype's markup,
copy and layout, and adds the tests, the documentation and the structural changes it lacks, rather
than rebuilding the pages from the specification.

**ADR:** none — how this feature was sequenced, nothing downstream inherits it.

## D2 — Page logic lives on the overview plugins

The prototype keeps each page's logic in a module of functions called from the plugin. The
cohesion rule in the constitution puts behaviour that shares a subject on a class, preferring the
class Django already owns, so the logic moves onto each page's `Overview` plugin and the shared
part onto `RecordOverviewPlugin`. A portal then changes one piece of a page by overriding one
method.

**ADR:** pending — decided at convergence, once the shape has settled in code.

## D3 — The header's people row is `overview.byline`

The prototype called the header's people row `overview.meta`, which says nothing about what it
holds, beside `overview.people` for the People card. The specification asks for one name per
thing, so the header row becomes `overview.byline`.

**ADR:** none — a block name, documented with the block list.

## D4 — Existing tests that describe the old rules are updated, not kept

Several existing tests open a sample or measurement in an unpublished dataset as a visitor and
expect the page. The specification now answers that with "not found". Where a test is about
something other than visibility, its fixture gets a published, public dataset. Where it is about
visibility, it is rewritten to the new rule. A test that fails because the prototype dropped
something the specification still requires, such as the Delete link, is left as it is and the code
is fixed.

**ADR:** none — follows from the specification.
