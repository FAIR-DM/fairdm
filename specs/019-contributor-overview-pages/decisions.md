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
