# Decisions: FS-042 Find a record from anywhere in the portal

Each decision below was made while specifying, from the issue, the prototype and the code on
`main`, and is open to veto at the specification review.

## D1. Records are matched by the fields their own list search uses, not indexed

**Ambiguity.** The issue leaves open whether records are indexed (django-mvp's model kind, backed by
modelsearch) or matched by name and identifier.

**Chosen.** Matched. Each record type finds a record by the same text its own list search finds it
by. Every record type already has one: the project, dataset, sample and measurement filters, the
people and organization filters, and the literature catalogue's search.

**Why.**

- One rule for what matches means a person never finds a record from the header that its own list
  will not find for the same text, or the other way round.
- R17 plans to improve matching and ranking on the list pages, with an index. Built this way, that
  work improves the site search at the same time instead of leaving two search mechanisms to keep
  in step.
- django-mvp's model kind does not fit FairDM's models as they are. It searches through the model's
  default manager. `Dataset.objects` excludes private datasets, so a person who holds a level on a
  private dataset could never find it. Samples, measurements and contributors are polymorphic, and
  the model kind asks for a model with "no special manager". Literature's `Item` belongs to another
  package, so FairDM cannot make it indexed.
- django-mvp's documentation offers a kind class over any queryset as a supported way to build a
  kind, so this stays inside what django-mvp provides.

**Revisit if** R17 builds an index for the list searches. The site search then follows it.

**ADR:** docs/adr/0048-the-site-search-matches-with-each-lists-own-search.md

## D2. A person who holds a level on a private record finds it

**Ambiguity.** The issue says each kind shows what the person may see "the same way that record's
list page does", and asks separately whether a person on a private project finds it. On `main` the
project and dataset lists show public records only, to everyone, so the two readings disagree.

**Chosen.** Each record type shows the records the person may open. For projects and datasets that
includes the private ones the person holds a level on, and everything for someone a portal role
lets view every record.

**Why.**

- Searching for a record you work on and not finding it is the failure a site search exists to
  prevent. The list page is a public catalogue. The search is how a person gets to a record.
- Samples and measurements have no list page, so for them the rule is already "what the person may
  open" (`visible_to`). Using the same rule for projects and datasets keeps the four record types
  consistent: otherwise a person would find the samples of a private project and not the project.
- Nobody is shown more than they can already open by following a link, so nothing new is disclosed.
- django-mvp's search states the same principle: a record a visitor may not open is neither listed
  nor counted, and one they may open is.

**Terminology.** The spec says "a person who holds a level on" a record, the phrase `CONTEXT.md` uses
under Visibility. "Member" in `CONTEXT.md` means an affiliation to an organization, so it is not used
for projects.

**ADR:** none — follows the portal's existing rule that a record is shown to the people who may open it

## D3. The rest of a record type's matches are on the search's own results page

**Ambiguity.** django-mvp lets a kind point "see all" at an address of its own. The prototype pointed
projects, datasets, people and organizations at their list pages with the query.

**Chosen.** No kind gives an address of its own, so "see all" opens the search results narrowed to
that record type, twenty to a page, as django-mvp does by default.

**Why.** After D2 the list page can show fewer records than the search found (it leaves out private
ones the person holds a level on), so a link to it would lose matches. Samples and measurements have
no list page, so the default keeps every record type the same.

**ADR:** none — local to this feature, the default django-mvp behaviour

## D4. The record types and their order

**Chosen.** Projects, datasets, samples, measurements, people, organizations, literature, the order of
the issue and of the prototype. Each is registered by FairDM, so a portal gets all seven with no
setting. A portal that wants fewer, or another order, uses django-mvp's `search.kinds` setting, which
already exists.

**ADR:** none — local to this feature, a list in one function

## D5. Registered sample and measurement types are found with no extra step

**Chosen.** The sample and measurement record types search the base models, so every registered
type is found as a sample or a measurement and links to its own page.

**Why.** G2: registering a model is enough to get a working portal surface. A domain type that the
search could not find until its developer registered something would break that.

**ADR:** none — local to this feature, follows from searching the base models

## D6. The visitor's landing page keeps its own header

**Chosen.** The landing page a signed-out visitor sees replaces the app header with one of its own,
on `main` (`fairdm/templates/fairdm/landing.html`, `app.header` block). It stays that way, so it
carries no search. Every other page does, the signed-in dashboard included.

**Why.** The landing page is its own design, and the prototype left it alone. Adding the search to
it is a change to that page, not part of finding a record.

**ADR:** none — local to this feature, the landing page is left as it is

## D7. No look of FairDM's own

**Chosen.** The results page, dialog, field and button are django-mvp's as they ship. The rule in
the prototype's stylesheet that placed the results page's icon is not carried: that fix is made in
django-mvp (https://github.com/django-mvp/django-mvp/issues/724).

**Why.** Sam, 2026-11-25: the search is built off what django-mvp provides and need not match the
prototype exactly.

**ADR:** none — local to this feature, nothing is added

## D8. Stories

One story. Everything a person does with the search (open it, type, narrow to one record type, page
through the rest) is one thing they set out to do, so these are scenarios under it. There is no
developer story: a portal's developer does nothing to get the search, and limiting or reordering
the record types is django-mvp's existing setting.

**ADR:** none — a statement of how the feature is cut, nothing downstream inherits it

## D9. A dataset is found by the text the dataset list matches, descriptions and keywords included

**Ambiguity.** FR-004 listed the dataset's matching fields as name, portal ID and external
identifier. The dataset list's search also matches descriptions and keywords. SC-004 says every
record the list search finds is also found by the site search.

**Chosen.** The dataset kind uses the dataset list's search as it is, so descriptions and keywords
match too. FR-004 is corrected to say so.

**Why.** A narrower rule would break SC-004 and let the header find fewer datasets than the list
does for the same text. Reading the filter itself means the two cannot drift (D1).

**ADR:** none — local to this feature, nothing downstream inherits it

## D10. A type's own search fields match in its own table only

**Ambiguity.** A registered sample or measurement type can add fields to its table's search through
`search_fields` (default `["name"]`). The site search matches samples and measurements by the base
fields only (name, local ID and portal ID), because it searches the base models (D5).

**Chosen.** The site search uses the base filter. A field a type adds matches in that type's own
table and not in the header. With the default registration the site search finds a superset of the
table's matches.

**Why.** Matching on a type's own fields would need one query per registered type. Parity for types
that add search fields is a change to the specification, so it is not made here.

**ADR:** none — local to this feature, nothing downstream inherits it

## D11. Every record type's order ends with the primary key

**Chosen.** Each kind orders by its name or title and then by primary key.

**Why.** The results page pages twenty at a time. Two records with the same name in no fixed order
could appear on two pages or on none. django-mvp's own sort rule says the same.

**ADR:** none — local to this feature, nothing downstream inherits it

## D12. The result line names the record's parent, as the record's card does

**Chosen.** A dataset's result line names its project, a sample's names its dataset and its local
ID, and a measurement's names its sample. Nothing wider: no description and no contributor names.

**Why.** The portal's cards already name the parent, so nothing is disclosed that a person may not
already see on a record they can open.

**ADR:** none — local to this feature, nothing downstream inherits it

## D13. The three search components are copied into the header block, not set as a layout widget

**Chosen.** `base.html`'s `app.navbar.end` block gains the three components, as the prototype has
them. The `layout.navbar.end` setting is left alone.

**Why.** The look is ported from the prototype's block, and the header changes in
https://github.com/FAIR-DM/fairdm/issues/719 edit the same block. The setting route would put the
search in a second place the next feature has to find.

**ADR:** none — local to this feature, nothing downstream inherits it

## D14. A reference that is only a DOI prefix lists nothing

**Chosen.** When the catalogue's search reads a query as no words, because it is only `doi:` or a
DOI address prefix, the literature kind returns no references.

**Why.** The catalogue's filter returns the unfiltered set for an empty term, which would list every
reference for a query that names none.

**ADR:** none — local to this feature, nothing downstream inherits it

## D15. Registering the kinds twice leaves them as they are

**Chosen.** `register_kinds()` skips a kind whose name is already registered.

**Why.** `FairDMConfig.ready()` runs more than once in one process, and a test calls it again.
django-mvp refuses a second registration under the same name, so an unguarded call stops the app
from starting the second time.

**Revisit if.** django-mvp makes registering the same instance again harmless.

**ADR:** none — local to this feature, nothing downstream inherits it

## D16. The dataset kind's description does not begin with "Published"

**Chosen.** The dataset kind is described as "Collections of samples and measurements".

**Why.** The dialog draws every kind's description on every page, and a dataset card's test asserts
that the word "Published" appears nowhere on a page for an unpublished dataset.

**Revisit if.** The test is written to look inside the card rather than the whole page.

**ADR:** none — local to this feature, nothing downstream inherits it

## D17. Two older tests are narrowed to leave the header's search out

**Chosen.** The dataset listing's test that it offers one search control counts only the fields
outside the header's search dialog. The overview page's test that a record without an image has
nothing to open looks for dialogs other than the header's search dialog. Neither assertion is
weakened: the listing still has exactly one search field of its own, and a record with no image
still opens nothing.

**Why.** Every page with the portal's header now carries the search dialog (FR-002), so a count
over the whole page and a search for any dialog both meet it. The specifications those tests guard
are about the listing's own toolbar and the record's image.

**ADR:** none — local to this feature, nothing downstream inherits it
