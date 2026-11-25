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

## D3. The rest of a record type's matches are on the search's own results page

**Ambiguity.** django-mvp lets a kind point "see all" at an address of its own. The prototype pointed
projects, datasets, people and organizations at their list pages with the query.

**Chosen.** No kind gives an address of its own, so "see all" opens the search results narrowed to
that record type, twenty to a page, as django-mvp does by default.

**Why.** After D2 the list page can show fewer records than the search found (it leaves out private
ones the person holds a level on), so a link to it would lose matches. Samples and measurements have
no list page, so the default keeps every record type the same.

## D4. The record types and their order

**Chosen.** Projects, datasets, samples, measurements, people, organizations, literature, the order of
the issue and of the prototype. Each is registered by FairDM, so a portal gets all seven with no
setting. A portal that wants fewer, or another order, uses django-mvp's `search.kinds` setting, which
already exists.

## D5. Registered sample and measurement types are found with no extra step

**Chosen.** The sample and measurement record types search the base models, so every registered
type is found as a sample or a measurement and links to its own page.

**Why.** G2: registering a model is enough to get a working portal surface. A domain type that the
search could not find until its developer registered something would break that.

## D6. The visitor's landing page keeps its own header

**Chosen.** The landing page a signed-out visitor sees replaces the app header with one of its own,
on `main` (`fairdm/templates/fairdm/landing.html`, `app.header` block). It stays that way, so it
carries no search. Every other page does, the signed-in dashboard included.

**Why.** The landing page is its own design, and the prototype left it alone. Adding the search to
it is a change to that page, not part of finding a record.

## D7. No look of FairDM's own

**Chosen.** The results page, dialog, field and button are django-mvp's as they ship. The rule in
the prototype's stylesheet that placed the results page's icon is not carried: that fix is made in
django-mvp (https://github.com/django-mvp/django-mvp/issues/724).

**Why.** Sam, 2026-11-25: the search is built off what django-mvp provides and need not match the
prototype exactly.

## D8. Stories

One story. Everything a person does with the search (open it, type, narrow to one record type, page
through the rest) is one thing they set out to do, so these are scenarios under it. There is no
developer story: a portal's developer does nothing to get the search, and limiting or reordering
the record types is django-mvp's existing setting.
