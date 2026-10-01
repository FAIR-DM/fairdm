# Decisions: 019-contributor-overview-pages

Questions settled while writing the specification without asking the maintainer, with the reasoning
behind each. The maintainer's own rulings are recorded under *Clarifications* in `spec.md`.

## Private projects and datasets are left out for every viewer

The agreed rule was that a page never names a record the viewer cannot open. That leaves one case
open: a viewer who is on the team of a private project the person is credited on could open it, so
the rule alone would list it for them. The specification leaves it out anyway. The prototype shows
public records only, the page's own empty-state text speaks of "public" projects, and a profile that
changes with the viewer is hard to reason about: the person could not tell what a visitor sees by
looking at their own page. Private work stays reachable from the project.

The collaborators and the role counts are different. They are worked out from credits on all four
record types, and samples and measurements have no visibility of their own, so those follow what
the viewer may open through the dataset.

## The checklist follows the affiliation, not the portal role

A portal role such as Community Manager may give someone the right to change any organization. The
checklist and the management menu are still shown only to the organization's own owner and
administrators. The checklist is advice to the people responsible for one record. Portal staff
manage organizations from the administration interface, and showing them a checklist on every
organization would make it noise there.

## The organization's map is left out when no location is recorded

Specification 018 shows every card a page has and lets it say what is missing. The organization's
map is the exception here. Its city and country are already in the header, so an empty map card
would repeat "no location" beside a header that may well name one.

## Removing the Statistics and Network tabs

Both tabs exist today and render blank pages. Neither was part of the reviewed prototype. Leaving
them beside a finished overview would put two dead ends on every contributor, so they are removed.
Their intended content (role counts, collaborators) is on the overview. A statistics page with real
content is a later feature.

## The sizes of the lists are requirements

Five records, ten members and eighteen collaborators were each settled in review, and each decides
what a visitor sees and what is counted instead. They are stated as requirements so the tests pin
the behaviour at the limit. How the lists look is not specified.

## What the specification leaves to the prototype

Wording, icons, colours, badge styles and spacing were reviewed on the prototype and are not
restated. A requirement here says what the page tells a reader, and the prototype branch
`sketch/contributor-profiles` shows how it was agreed to look.

## D1. The build starts from the prototype

The prototype branch is merged onto the build branch and its markup, copy and layout are kept.
Tests are written against the specification's scenarios, and a test that fails drives a fix.

**ADR:** none. The same approach as specification 018, local to how this feature was built.

## D2. One plugin class, no mixin

The prototype's `ContributorOverviewMixin` has a single user. It is folded into the registered
`Overview` plugin.

**ADR:** none. A local simplification, nothing downstream inherits it.

## D3. A public dataset inside a private project is not listed

The prototype filters datasets on their own visibility. The glossary says a private project hides
everything beneath it, so a contributor's page checks the project as well.

**ADR:** none. It applies an existing rule and adds no new one.

## D4. The pending-action tests follow the component, and the badge tests go

`overview/includes/pending_action.html` became the `c-actions.pending` component. Three existing
tests move to it unchanged in what they assert. Two expected a "Coming soon" badge on the button,
which the maintainer removed in review of the prototype; they are deleted.

**ADR:** none. A test maintenance record.

## D5. Pillow is declared directly

The development data command draws placeholder logos with Pillow, and FairDM's image fields need
it at run time already.

**ADR:** none. It records an existing dependency, and changes no behaviour.

## D6. Design review: what was applied and what is carried

One reviewer, three lenses, one round. Two high findings were applied as plan edits: the page head
keeps an affiliation only when the header shows it, and each contributor has one model source for
its public projects and one for its public datasets, read by the overview and by both tabs. The
medium and low findings were applied too: the project check extends to samples and measurements,
the `account-center` cause is named with its fix, the tab module's strings become lazy, and the
mixin fold and tab removal move behind the tests that pin the page. One is carried as a watch
item: samples and measurements are resolved to ids, not loaded as objects.

**ADR:** none. A record of the review, with each change made in the plan.

## D7. FairDM keeps the `/account-center/` address

django-mvp 0.25.1 moved its landing page to `account/` inside its own URL module. FairDM declares
its own `account-center/` route to that view, so the address people already use stays.

**ADR:** none. It preserves existing behaviour across a dependency update.
