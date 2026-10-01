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

## D8. The `account-center` route comes after the includes

The plan put FairDM's own `account-center/` route ahead of the `mvp.urls` include. With the route
first, `reverse("account-center")` still returned `/account-center/account/`: Django reverses a name
to the last pattern that carries it. The route now follows the `dac.urls` include. Requests to
`/account-center/` match no pattern inside the includes, so they reach the route either way.

**ADR:** none. It preserves existing behaviour across a dependency update.

## D9. The two public sources are `get_public_projects` and `get_public_datasets`

**Decision:** `Contributor.get_public_projects()` and `get_public_datasets()` return the credited
public projects and the credited public datasets outside private projects. The overview page, its
cards and figures, both tabs and `get_visible_contributions` read them. The dataset rule is a
`DatasetQuerySet.get_visible()` method, matching `ProjectQuerySet.get_visible()`.

**Why:** a count then cannot disagree with the list behind its link, and Organization can override
the two methods in the organization story without touching the pages.

**Revisit if:** a contributor ever needs a different public rule per record type.

**ADR:** none. Two method names local to the contributors app.

## D10. Samples and measurements are resolved to ids

**Decision:** `get_visible_contributions` marks each contribution with `kind`, and with `record`
only for projects and datasets. Samples and measurements are checked against `visible_to(user)` and
the project rule by id, and never loaded. `get_collaborators` builds one condition per kind of
record, matching the ids with `__in`, instead of one per credit.

**Why:** no card lists a sample or a measurement, and loading polymorphic rows to throw them away
costs a query per kind and a row per credit. The T003 tests compare the kind and the id of each
credit for the same reason.

**Revisit if:** a card ever lists samples or measurements.

**ADR:** none. An implementation detail of one method.

## D11. An organization's two sources match credits with a subquery, not a join

**Decision:** `Organization.get_public_projects()` and `get_public_datasets()` filter on
`Q(pk__in=<credited records>) | Q(owner=self)` (and `project__owner=self` for datasets) and then
apply `get_visible()`. They do not join through the contributions and call `distinct()`.

**Why:** a join on the credits repeats a record the organization both owns and is credited on, and
`distinct()` on a queryset the tabs then order and annotate invites duplicate or reordered rows. The
subquery keeps the result one row per record, so a figure equals the entries behind its link
(SC-003) without a second pass.

**Revisit if:** the credited subquery shows up as a slow query on a portal with very many credits.

**ADR:** none. A query-shape choice inside one method.

## D12. The seed command already reached the organization states, so it is unchanged

**Decision:** T013 adds tests for the three organization states FR-033 names and changes nothing in
`seed_profiles`.

**Why:** the command already seeds an organization with a logo, ROR ID, location, parent,
sub-organizations, members and owned projects, one the signed-in user owns, and one with nothing
recorded. The new tests fail when each of those is removed from the command.

**Revisit if:** FR-033 names a further organization state.

**ADR:** none. A record that nothing changed.

## D13. The checklist's affiliation item and a person's location follow the header

**Decision:** `Person.get_profile_completeness()` counts a primary affiliation only when it is
verified and has not ended, and `Person.get_location_display()` reads the same affiliation. The
location filters `affiliations.all()` in Python so a listing that prefetches affiliations still
costs no query per person.

**Why:** the header and the schema.org description already name an organization only for a verified,
current primary affiliation. The checklist marked a pending request as in place while the header
showed no organization, and the public location method named the organization of a pending or ended
primary affiliation, the same gap `to_public_schema_org` had. The person's card in listings calls
the location method, so it needed to stay prefetch-friendly.

**Revisit if:** `primary_affiliation()` itself is changed to apply the rule, which would let both
methods read it.

**ADR:** none. It applies the rule the header already follows to two more places.

## D14. The two old plugin templates are deleted

**Decision:** `person/plugins/overview.html` and `organization/plugins/overview.html` are removed.

**Why:** the `Overview` plugin names its templates in `get_template_names`, so nothing resolves
them. A search of the templates, the Python code, the tests and the documentation found no
reference to either path.

**Revisit if:** a portal extends one of them; the changelog entry for this branch would then need a
removal note.

**ADR:** none. Removal of unused files.

## D15. One test added at convergence, written directly

Checking the requirements against the tests found FR-032 untested for organizations: the people
who keep a record are offered writing its description, as not yet available. One parametrised
test was added without dispatching a story for it, because it is a single test with no design
content.

**ADR:** none. A test maintenance record.
