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

## D5 — Design review applied to the plan

The design review raised eleven findings, all checked against the code. Applied as plan and task
edits: the dataset's `overview.data` block and a slim record-types method stay, because the
first-run state, the figures and `variableMeasured` depend on them; the composition chart skips
unregistered types; dates use locale-aware named formats; the stories run in sequence; the typed
page's permission check goes through the base model's manager; page tests live in each app's
`test_plugins.py`; the seed command leaves existing accounts alone and keeps `regular.user` off
every team; `visible_to` is shared by one QuerySet mixin; `TypedOverviewPlugin` subclasses
`RecordOverviewPlugin`; three helper tests the page scenarios already cover are dropped. Not
applied here: `CONTEXT.md` says a private project hides everything beneath it, which FairDM does
not enforce for datasets. That predates this feature and is raised separately.

Decision numbers in this file and section numbers in `plan.md` are separate series. Tasks cite
plan sections as "plan D<n>".

**ADR:** none — plan edits, recorded here.

## D6 — Six existing sample-page tests open the page from a published, public dataset

The tests were about something other than who may see a sample: that the record reaches the
template context, that the breadcrumb trail links to it and carries no placeholder link, that the
page declares its media, that it serves at all, and that its navigation points somewhere. Each
built its sample with `RockSampleFactory()`, which puts it in a private, unpublished dataset. The
sample page now answers a visitor with "not found" for such a sample, as the specification asks,
so each test built a page nobody could open. Each one now builds its sample with
`RockSampleFactory(dataset=DatasetFactory(visibility=Visibility.PUBLIC, published=True))` and
asserts what it asserted before.

Changed, by file (`tests/test_contrib/test_plugins/`):

- `test_base.py`: `TestReachingTheRecord.test_the_record_is_in_the_context`,
  `TestTheNavigationTrail.test_the_record_entry_links_to_the_record`,
  `TestTheNavigationTrail.test_no_entry_carries_a_placeholder_link` and
  `TestDeclaredAssets.test_declared_stylesheets_and_scripts_reach_the_response`
- `test_registration.py`: `TestRecordPagesServe.test_sample_overview`
- `test_menus.py`: `TestNavigationRenders.test_every_visible_entry_points_somewhere`

The sample's visibility rules have their own tests in the sample story.

**Revisit if:** the sample page's visibility rule changes again.

## D7 — The shared page logic moved onto the plugin classes in one step, and the other pages call it there

`RecordOverviewPlugin` now holds what every overview page works out the same way: `get_credits`,
`get_people`, `get_identifiers`, `get_citation`, `get_timeline`, `get_license_entry`,
`get_composition_chart` and `get_growth_chart`. `TypedOverviewPlugin` subclasses it and adds
`get_type_info`. The project's own logic moved from `fairdm/core/project/overview.py` onto its
`Overview` plugin, and that module is gone. The four `Overview` plugins all subclass
`RecordOverviewPlugin`.

The dataset, sample and measurement modules stay until their stories, but their `build()`
functions now take the plugin as their first argument and call these methods in place of the
module functions they replace. Keeping both would have left the same chart, credit and identifier
code in two places for three more stories, and every fix this story makes (translatable strings,
locale-aware dates, skipping types the registry does not hold) would have had to be made twice.
What stays in `fairdm/core/overview.py` is what no class owns: `format_authors`, `author_name`,
`json_ld`, `as_date`, `sentence_case`, `safe_reverse`, and the small readers of a credit
(`contributions_of`, `roles_of`, `is_person`, `with_role`) that the dataset module's own logic
still calls.

The project page's own steps have their own names on the plugin: `get_progress` for how far
through its dates the project is (the shared `get_timeline` joins dated steps of a sample or
measurement), `get_citation_details` for the project's citation with its DOI facts (the shared
`get_citation` only writes the text), and `get_readiness(page)` and `get_details(licenses)`, which
take what the page has gathered so far, so nothing is queried twice.

Checked by rendering every project, dataset, sample and measurement in the development data as a
visitor, as `staff.user` and as `regular.user` before and after the move: 297 responses, byte for
byte the same.

**Revisit if:** a story finds a method that belongs on one page's plugin alone.

## D8 — Dates on the pages use `SHORT_DATE_FORMAT` and `YEAR_MONTH_FORMAT`

Every date the four pages and the cards write out goes through one of Django's named formats, so
it follows the active language: `SHORT_DATE_FORMAT` for a day, `YEAR_MONTH_FORMAT` for a month and
for the growth chart's axis and description. A date recorded only to the month is written as a
month, and one recorded only to the year as the year. In English a day now reads `09/29/2026`
where the prototype wrote `29 Sep 2026`, because the named format is the locale's own. If that
reads badly to the portal's audience, the change is one format name in the templates.

**Revisit if:** the maintainer prefers `DATE_FORMAT` (`Sept. 29, 2026`) for days.

## D9 — The development data recognises its own projects by name and by who created them

`seed_overviews` used to delete every project with a seeded name, which removed a project somebody
else had made under the same name, and its datasets. Each seeded project now records `super.user`
as its creator, and the clean-up removes only a project with a seeded name that `super.user`
created. A database seeded by the earlier version holds a few projects with no creator recorded
(the sample and measurement examples) or another one (the empty project); those stay, and the next
run creates fresh copies beside them.

**Revisit if:** a run needs to find its records by something other than a name and a creator.

## D10 — The type dialog is written out in `type_badge.html`

`c-modal` draws a `<dialog>` with no accessible name, and the description of a sample or
measurement type opens in one. The include now writes the same markup itself with an `aria-label`,
so the dialog is announced by the type's name.

**Revisit if:** `c-modal` names its dialog.
