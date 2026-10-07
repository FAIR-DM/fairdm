# Decisions: 024-shared-editing-pages

Questions settled while writing the specification without asking the maintainer, with the reasoning
behind each. The request in #404 named the six pages, the four record types, the Manage menu and the
rule that each page is shown only to someone who may use it. Everything below fills a place where it
was silent.

## For Sam to confirm

Each of these changes what gets built and was not stated in the request. The specification is
written on the reading given here. If any is wrong, it is one requirement to change.

1. **Key dates and identifiers leave the details page.** On a project and a dataset they are edited
   today on the same page as the other details. The request lists them as entries of their own, so
   the specification moves them to their own pages and takes them off the details page (FR-016). The
   alternative is to keep them on the details page as well, which would mean two places to edit the
   same thing.
2. **Descriptions use one area per description type.** A project and a dataset edit descriptions
   that way. A sample uses rows that are added and removed, each with a type chosen from a list. The
   specification takes the first for all four (FR-020), because the vocabulary already says which
   descriptions a record can carry and the row form lets the same type be chosen twice. A sample's
   descriptions page changes as a result.
3. **The keywords page ships as it is, on all four record types.** Only a sample has a keywords
   page today. A dataset's was removed on the grounds that #298 would replace it whole. The request
   lists keywords among the six and puts the rebuild out of scope, so the specification registers
   the existing page everywhere (FR-022 to FR-024) and leaves its interior to #298. The alternative
   is to leave the keywords entry out until #298 is built. That is why keywords are the last story:
   dropping it costs nothing else.
4. **A sample's and a measurement's details page edits the type's own fields.** A sample's edit
   page offers only its name and image today, and a measurement has none. The specification makes
   the details page offer what the registered type offers on creation (FR-016), since the request
   says a measurement cannot be edited beyond what its create form offered. It does not offer moving
   a record to another dataset or sample (FR-017), because that changes who has rights over it and
   deserves a decision of its own.
5. **Deleting adds no new protection.** A project with a public dataset is refused, and a sample
   with measurements on it is refused, as now. A sample or a measurement in a public dataset can
   still be deleted by someone with the right, as it can be today through other routes. The glossary
   says publication constrains deletion. If a public dataset should also protect its samples and
   measurements, that is a requirement to add here (FR-031).
6. **The right to delete is the one the portal checks.** Deleting any of the four record types
   needs the manage level, which specification 022 settled. The specification does not change it
   (FR-012).

## Rights are the ones the portal checks today

The request says each page is shown only to someone who may use it. It does not say who that is.
The portal already has a right to change and a right to delete each record type, and 017 gives
portal roles their share of both. Using those keeps this feature to its subject, which is the pages,
and leaves granting rights to a research team with #402. Nothing in the specification depends on
#402 being delivered first.

## No dependency on a sibling feature

The specification relies on nothing the other six features in #397 deliver. The Manage menu exists
already on three of the four record types (018). #401 adds page actions, overview cards and
replacing a plugin, none of which these pages need. #403 removes and adds tabs, and these pages are
not tabs. The epic's `Depends on:` footer is therefore empty.

## Manage menu entries from addons are out of scope

#397 lists the Manage menu as one of four places something can appear on a record's page, and #401
opens two of the others to addons. Neither issue asks for addons to add Manage menu entries. The
specification covers the six entries and requires that the menu's other entries survive (FR-009). A
general way for a plugin to contribute an entry would be a feature of its own.

## Old addresses are not kept

The existing pages sit at different addresses on each record type. Sharing one set means one
pattern. The package is at version 0.0.1 with no stable release, so the specification does not ask
for the old addresses to redirect. The record's own address is the one that must not move (FR-005),
because that is what a citation points at.

## Landing place after a deletion

A deleted sample or measurement leaves its dataset behind, so that is where the person lands
(FR-033). A project and a dataset land where they do today. The specification says only that the
page still exists, so the choice stays with the build.

## How a deletion is confirmed is left open

A project and a dataset are confirmed today by typing the record's name. A measurement may have no
name. The specification requires a deliberate confirmation and a statement of what goes with the
record (FR-030), and leaves the form of the confirmation to the build.

## Simultaneous edits are not detected

Two saves of the same page are applied in order and the later one stands. No editing page in the
portal detects this today, and adding it is not what the request asks for.

## No sketch before the build

Every page here is a form or a confirmation in a layout the portal already has, reached from a menu
that already exists. Nothing needs to be drawn first.

## Decisions made while planning the build

Read against `main` on 2026-10-07, after specifications 020 and 022 were delivered and #401 was
closed.

## D1. The right to delete is no longer uneven

Item 6 above described deleting a sample as needing the right to change its dataset, and deleting a
measurement as needing the right to delete its dataset. Specification 022 changed both: deleting any
of the four record types needs the manage level, through `<type>.delete_<type>`. The delete page
asks that permission and nothing else. FR-012 holds because the page reads the right that exists.

**ADR:** none — the rule is recorded in 0025, and this page only reads it

## D2. A viewer who may see a record and not use a page gets 403, not 404

**Decision:** a request for an editing page answers 404 only when the viewer may not see the
record. A signed-in viewer who may see it is refused with 403, and a visitor is sent to sign in.
**Why:** FR-013 and FR-014 draw that line. The project and dataset pages answer 404 to every
refusal on a private record today, and specification 022 (its D29) left that to be revisited when
these pages were rebuilt.
On a sample the old pages asked only for the permission, so a person granted
`sample.change_sample` for the whole portal, with no level on a record, could open the pages of a
sample they could not see. They now get 404. FR-014 is taken over a literal reading of FR-012 here,
and it is the rule the project and dataset pages already apply. A Data Curator is unaffected.
**Revisit if:** a refusal is found to reveal something the record's own page does not.

**ADR:** docs/adr/0026-a-records-editing-pages-are-six-shared-pages.md

## D3. The project's "Manage contributors" entry is not carried into the shared menu

**Decision:** the shared Manage menu has the six entries and no entry for contributors.
**Why:** specification 022 FR-007 says managing contributors must not appear in the Manage menu.
The entry on the project page predates it. FR-009 here keeps whatever else the menu carries, and it
was written with entries such as importing data in mind, none of which is in the menu today.
**Revisit if:** the Contributors tab stops being offered on a record type.

**ADR:** none — local to this feature, and the rule it follows is specification 022's

## D4. The keywords form is repaired to a working state

**Decision:** `KeywordForm` is changed so that it reads the configured vocabularies with a default
of none and no longer rewrites its own class. Nothing else about it changes.
**Why:** FR-024 asks for the page as it works today, and it does not work: the form raises for every
sample type because it reads a setting that does not exist. FR-023 asks for a page that works with
no vocabulary configured. The smallest change that satisfies both is this one.
**Revisit if:** #298 lands first, in which case US-4 only registers its page.

**ADR:** none — a repair inside this feature, and the form is replaced by #298

## D5. Dates and identifiers leave the details page, and the pages are registrations of their own

**Decision:** the six pages are six registered plugins, not additional views of the overview, and
dates and identifiers are edited on their own pages.
**Why:** the specification asks for both (FR-003, FR-016). Architecture decision 0008 says the
opposite on each point, so a new record supersedes it.
**Revisit if:** never without a new specification.

**ADR:** docs/adr/0026-a-records-editing-pages-are-six-shared-pages.md

## D6. Started while another pull request is open

**Decision:** the build started while #383, which shows a record's image as a banner on its
overview, is open and waiting for review.
**Why:** the maintainer asked for this feature to be built now. #383 changes the overview's header
image and two user guide pages. If it merges first, this branch is brought up to date before it is
marked ready.
**Revisit if:** #383 changes the overview's actions block.

**ADR:** none — an ordering note for this run

## D7. The design review's findings, and what was done with each

One reviewer read the plan through three lenses before any code was written. One finding was high:
a form built by the registry draws its own form element, which would have left the page's Save
buttons outside any form. The plan now turns that off (D4, D7 of the plan). The others changed the
order in which old code is removed so no story leaves a broken page, limited the measurements a
sample's delete page names to those the viewer may see, and removed one test nothing asked for.

One edge is recorded and built the simple way: a person who holds the manage level on a sample
alone, and no level on its dataset, lands on the dataset list after deleting it, because they may
not open the dataset.

**ADR:** none — review record for this feature

## D8. The shared pages are imported from the last of the four record plugin modules

**Decision:** `fairdm/core/editing.py` is imported at the foot of `fairdm/core/measurement/plugins.py`,
not at the foot of `fairdm/core/project/plugins.py` as the plan says.
**Why:** plugin discovery loads the project, dataset, sample and measurement modules in that order.
Importing from the project module registers the six pages on `Sample` and `Measurement` before
those models' own overview pages, and an existing test in `tests/test_contrib/test_plugins/`
(`test_a_predicate_written_to_the_wrong_signature_hides_its_entry`) takes the first plugin
registered on `Sample` to be the overview. Importing from the measurement module keeps each
overview first on every record type and leaves that test as written.
**Revisit if:** a fifth core record type is added, or that test stops reading `registered[0]`.

**ADR:** none — an import placement

## D9. Dates and identifiers on the details page draw stacked until they leave it

**Decision:** `EditDetails` sets no template of its own. A project's and a dataset's identifier and
date rows draw in django-mvp's default stacked layout, where the dataset's old update page drew
them as a two-column table through `dataset/plugins/update.html`.
**Why:** the shared page serves four record types and only two of them carry row sets, and US-2
takes the rows off this page. A template that exists for two stories would be deleted by US-2.
**Revisit if:** the stacked rows read badly enough that US-2 should not wait.

**ADR:** none — a short-lived layout choice

## D10. An empty crispy helper is falsy, so the registry's own button never nests

**Decision:** `EditDetails.get_form` still sets `form_tag = False` and empties `inputs` on any form
that carries a helper.
**Why:** django-mvp draws the helper only when `form.helper` is truthy, and a `FormHelper` with no
layout is falsy. The registry's default form therefore never nested a second `<form>`. A form whose
helper has a layout does, and a portal can supply one through its configuration. The test
`test_a_form_whose_helper_draws_its_own_tag_and_button_still_gives_one_form` builds such a form.
**Revisit if:** django-mvp stops drawing the helper from `form.helper`.

**ADR:** none — a test note

## D11. The sample keywords page is reachable from the menu and fails to open

**Decision:** the Manage menu keeps the sample's keywords item through the component's slot, and the
tests assert the item and not that the page opens.
**Why:** `Keywords` in `fairdm/core/sample/plugins.py` sets no `model`, `queryset` or
`get_queryset`, and the page raises `ImproperlyConfigured` on the base commit. Repairing the
keywords page is story US-4.
**Revisit if:** US-4 lands, when its page tests take over.

**ADR:** none — a pre-existing fault left for US-4

## D12. The descriptions page does not handle a vocabulary with no types

**Decision:** `EditDescriptions` draws the form its vocabulary gives it and has no separate
state for a record type whose description vocabulary offers nothing.
**Why:** the four core vocabularies are fixed and never empty, so the state cannot occur on a core
record, and a test of it would have to empty a vocabulary by patching library internals. The
specification lists the edge as a requirement for a record's vocabulary, which only a portal that
replaces one could meet.
**Revisit if:** a portal can configure a core record's description vocabulary, or a test seam for
an empty vocabulary exists.

**ADR:** none — a scope note

## D13. The Manage menu draws no divider or flag for the delete entry yet

**Decision:** `manage_menu` entries carry a label, an icon and an address, and
`<c-actions.manage>` draws them in order. The delete entry reaches the menu through the
component's slot, with its own divider, until the delete page is registered.
**Why:** the plan gives each entry a flag marking the delete entry and a divider before it. Nothing
in this story registers a delete page, so neither branch could be exercised by a test.
**Revisit if:** the delete page is registered, when the flag and the divider move into the
component.

**ADR:** none — deferred to the story that needs it

## D14. Existing tests changed in story 1 were checked against the list in the progress log

Twelve existing test modules were flagged as changed. Each change is one the task list allows: the
test requested a page this feature removes or reversed its old URL name. The list in `progress.md`
under T002 names every class. The two reversals of behaviour are the ones decisions D2 and D3
record.

**ADR:** none — a record of a check on this feature's tests

## D15. The key dates and identifiers pages draw their rows stacked

**Decision:** `EditKeyDates` and `EditIdentifiers` set no template, so their rows draw in
django-mvp's default stacked layout. The dataset's old update page drew its rows as a table.
**Why:** the tabular layout is a `layout="tabular"` argument to `<c-form.formset>`, chosen in the
page template's `formset` block. Neither the view nor the row set can ask for it, so using it needs
a template of our own. The brief asked for the table only where it is available without one.
**Revisit if:** the stacked rows read badly on a walkthrough. A template extending `form_view.html`
that overrides the `formset` block with `layout="tabular"` is the change, and it serves both pages.

**ADR:** none, a layout choice

## D16. The vocabulary-with-no-types state is not built for dates and identifiers

**Decision:** the key dates and identifiers pages have no separate state for a record whose
vocabulary offers no date types or no identifier types.
**Why:** the four core date vocabularies and the four core identifier vocabularies are fixed and
never empty, so the state cannot occur on a core record, and a test of it would have to empty a
vocabulary by patching library internals. This is the same reasoning as D12.
**Revisit if:** a portal can configure a core record's date or identifier vocabulary.

**ADR:** none, a scope note

## D17. `DateForm` is left in place

**Decision:** `fairdm/contrib/generic/forms.py` keeps `DateForm`, which only the removed
`KeyDatesPlugin` used.
**Why:** the brief forbids tidying that module in this story. It is listed in the completion report
as dead code.
**Revisit if:** a later tidy of that module is scheduled.

**ADR:** none, a scope note

## D18. Existing tests changed in story 2 were checked against the list in the progress log

Five existing test modules were flagged. The row-set tests on the old details pages are replaced by
the tests of the two new pages, and the tests of one save covering a form and its rows no longer
have a page to describe, because a page is now either a form or rows. The list in `progress.md`
under T005 names every class.

**ADR:** none — a record of a check on this feature's tests

## D19. Any measurement that blocks a deletion is named only if the viewer may see it

**Decision:** the delete page filters every protected measurement through
`Measurement.objects.visible_to(request.user)`, not only the ones that block a sample. Those the
viewer may see are named by `name_of`, the rest are counted in the `protected_unlisted` context
entry, and a small template over django-mvp's `delete_view.html` draws that count.
**Why:** a dataset whose samples another dataset measures is refused by the same RESTRICT relation,
and its old page printed `str()` of a measurement from a dataset the viewer might hold no level on.
One rule on the page closes both, and `str()` of a measurement is its value, not its name.
**Revisit if:** a record type other than a measurement can sit in a dataset the viewer cannot see.

**ADR:** none, a scope note

## D20. The delete entry is drawn after the menu's slot items

**Decision:** `<c-actions.manage>` draws the delete entry, after a divider, within the entries
loop, so a sample's Edit keywords item, still passed through the slot, comes after it until the
keywords story removes that item.
**Why:** the component draws the entries and then the slot, and moving the slot above the entries
would change where every record's own items sit. The keywords item goes in the next story.
**Revisit if:** the keywords story is dropped.

**ADR:** none, a scope note

## D21. Existing tests changed in story 3 are listed in the progress log

The old project and dataset delete pages are gone, so the tests that requested them were swapped to
the shared page where they assert something the new tests do not, and removed where they do. The
list in `progress.md` under T008 names every class.

**ADR:** none, a record of a check on this feature's tests

## D22. Existing tests changed in story 3 were checked against the list in the progress log

Eight existing test modules were flagged. Each change is to a test of a delete page this story
removes, or to one that reversed its URL name. The list in `progress.md` under T008 names every
class. The one reversal of behaviour is the 403 that decision D2 records.

**ADR:** none — a record of a check on this feature's tests

## D23. The helper reset moves onto the shared page base so the keywords page reuses it

**Decision:** the two lines in `EditDetails.get_form` that turn off a crispy helper's form tag and
empty its buttons are now `RecordEditingPage.without_form_tag`, and `EditDetails` and
`EditKeywords` both call it.
**Why:** the brief asks for the keywords page to treat its helper as the details page does and not to
write a second copy. The details page had the reset inline, not as a function, so it was lifted
unchanged.
**Revisit if:** a page needs a different helper treatment.

**ADR:** none, a refactor inside the module

## D24. The keywords form shows and saves free-text keywords as well as vocabulary ones

**Decision:** `KeywordForm` offers the record's recorded tags as the choices of its tag input and
as its initial value, and passes the tags to `instance.tags.set` as one list.
**Why:** FR-022 asks the page to show the keywords a record carries and let them be removed. The tag
input drew no option for a recorded tag, so opening the page and saving it would have cleared every
tag. The save also called `set` with the tags spread as separate arguments, which the installed
taggit version rejects with a `TypeError`, so a save with any tag failed. On a record type with no
vocabulary configured the tag input is the whole page, so both repairs are what FR-023 needs.
Vocabulary fields are unchanged.
**Revisit if:** #298 replaces the form.

**ADR:** none, a repair inside this feature

## D25. The module that held the sample keywords page's base class goes with the page

**Decision:** `fairdm/contrib/generic/plugins.py` is deleted. It held `KeywordsPlugin` and nothing
else, and only the removed sample page used it.
**Why:** the plan removes code that only a removed page used.
**Revisit if:** none.

**ADR:** none
