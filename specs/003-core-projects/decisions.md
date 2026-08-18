# Decisions — 003 Core Projects

The original specification was written on 2026-01-14, before most of the project app existed. It
described five layers at once: the domain model, the forms, the portal views, the admin, and a set
of cross-cutting concerns. Nineteen of its twenty-five requirements no longer match the code.

This file records what the old text said, what the code does, which way each disagreement was
settled, and why. It is the reason the specification now says what it says.

Every decision below was taken on 2026-08-18. Where a decision was settled without the maintainer
present it is marked **self-resolved**, and it stands unless he says otherwise.

## D-001 — Scope: this specification covers the project domain, not the portal views

**Settled by the maintainer, 2026-08-17.**

The original text owned the Project model, its related records, its forms, its list and detail
pages, its filters, its search, its admin, its exports and its permissions. Most of that portal
surface was later specified properly and separately by `013-project-crud-views`, which is narrower,
better adjudicated, and describes what actually shipped.

Keeping both meant two live documents claiming the same views, and in one case claiming opposite
things (see D-002). The specification is therefore narrowed to what only it can own:

**In scope** — the `Project` model and its fields, the related description, date, identifier and
contribution records, their controlled vocabularies, the administrative interface, metadata export,
funding, and the record of who created and last changed a project.

**Out of scope, owned by 013** — the list, create, update and delete pages, the forms behind them,
the search box and filter attachment on the list page, and the view-level permission checks.

**Out of scope, owned by neither** — the detail page. 013 excludes it explicitly (its FR-027) and
it is a portal surface rather than a domain concern, so it is routed out rather than absorbed here.

## D-002 — Deleting a project is blocked by public datasets only, not by any dataset

**Self-resolved.**

The old FR-021 blocked deletion whenever *any* dataset was attached, and allowed an administrator to
force it. 013's FR-023 blocks only when a *publicly visible* dataset is attached, with no override.
The code implements 013: `fairdm/core/project/models.py:196`.

Settled in 013's favour. A private dataset is the author's own unpublished work and should not lock
their project; a public one has been handed to other people and may already be cited. The
administrator override is dropped rather than built — nothing has asked for it, and a guard with a
bypass is a weaker guarantee than the one the code already makes.

The requirement leaves this specification entirely; 013 owns it.

## D-003 — Project identifiers use the wrong vocabulary, and the code is wrong

**Self-resolved. This is a defect, not drift.**

The old FR-005 called for identifier types a project would actually carry: DOI, grant number,
proposal ID. `ProjectIdentifier` instead points at `FairDMIdentifiers`
(`fairdm/core/project/models.py:167`), whose terms are ORCID, ResearcherID, ROR, Wikidata, ISNI and
Crossref Funder ID (`fairdm/core/vocabularies.py:6`). Those identify people and organisations. None
of them identifies a project.

The consequence is that a project cannot be given a DOI today. Since a citable, findable project
record is the point of the package's first goal, the specification keeps its original requirement
and the code is treated as wrong. A project identifier vocabulary is introduced.

The pre-existing global uniqueness of an identifier value (`fairdm/core/abstract.py:316`) is kept.
Two projects sharing one DOI is a data error, not a use case.

## D-004 — Project dates are Start and End, one of each

**Self-resolved.**

The old FR-004 asked for data-collection start and end dates alongside project start and end. The
code offers Start and End only (`fairdm/core/vocabularies.py:388`), and the shared abstract allows
one date per type (`fairdm/core/abstract.py:305`).

Settled in the code's favour. Data collection is something a dataset does, and the dataset record is
where those dates belong; putting them on the project would duplicate them across every dataset
beneath it. One date per type is consistent with how descriptions already behave and keeps the
timeline unambiguous.

The dropped date types are recorded here deliberately, so that reinstating them later is a decision
rather than a rediscovery.

## D-005 — Project status keeps the shipped set, and one label is corrected

**Self-resolved.**

The old FR-006 named six states including "On Hold" and "Cancelled". The code has four usable ones
plus a fifth that is broken: `SEARCHING_FOR_COLLABORATORS = 4` carries the label "Unknown"
(`fairdm/core/choices.py:12`).

Settled in the code's favour on the set — a shorter list of states that portals actually use beats a
longer one nobody selects, and neither missing state has been asked for. The mislabelled member is a
straightforward defect: the stored value stays 4 and the label is corrected to match the name it has
had all along.

## D-006 — Visibility stays private or public

**Self-resolved.**

The old FR-007 called for a third, organisation-scoped level. The code has two
(`fairdm/utils/choices.py:14`) and 013 built its whole list-page guarantee on them.

Settled in the code's favour here, because an organisation-scoped tier is a genuine feature rather
than a defect, and it reaches well past this specification — it would change dataset visibility,
the API serialisers and every queryset that filters on public. It is routed out as its own request
rather than smuggled in through a repair.

## D-007 — A project may exist without an owning organisation

**Self-resolved.**

The old FR-008 required an owner and said it should default to the creator's primary organisation.
The field is nullable (`fairdm/core/project/models.py:98`), the create form omits it, and no
defaulting logic exists anywhere.

Settled in the code's favour. 013 deliberately made creation a three-field form so that starting a
project is cheap, and requiring an owner at that moment contradicts it. Many researchers also have
no single owning organisation to name. Ownership stays optional, and the defaulting rule is dropped
rather than deferred.

## D-008 — Contribution roles keep the shipped vocabulary

**Self-resolved.**

The old FR-009 named Principal Investigator, Co-Investigator and Data Manager. The code offers
Creator, ProjectLeader, ProjectMember, ProjectManager, ContactPerson and Other
(`fairdm/core/vocabularies.py:616`).

Settled in the code's favour. The shipped set follows DataCite contributor types, which is what
metadata export has to emit anyway, whereas the old list was grant-office vocabulary that would need
translating at every export boundary.

## D-009 — The role-to-permission matrix is dropped from this specification

**Self-resolved.**

The old FR-018 laid out a matrix: principal investigators edit everything, data managers edit
metadata only, everyone else reads. None of it exists. Permissions are granted to the creator alone
(`fairdm/core/project/views.py:98`), and two of the five declared permissions —
`change_project_metadata` and `change_project_settings` (`fairdm/core/project/models.py:122`) — are
never checked anywhere.

The matrix as written is unbuildable in any case, because it names three roles the vocabulary does
not contain (see D-008). It is dropped here and routed out as a request in its own right: deciding
which contribution roles confer which rights is a real piece of design, and it belongs to the goal
about portal roles rather than to the project model.

The two unchecked permissions are left declared. Removing them is a migration on a core model for no
present benefit, and the routed request will decide their fate.

## D-010 — The audit trail records who created a project

**Self-resolved.**

The old FR-022 asked for created, modified and by whom. The code has timestamps
(`fairdm/db/models.py:74`) and nothing else — no `created_by`, no history table.

Settled in the specification's favour, partially. A creator is recorded, because attribution is the
part that cannot be reconstructed after the fact and because the create view already writes a
Creator contribution that a database-level field should mirror. Full revision history is a much
larger commitment — a dependency, a table per model, and a retention policy — and it is routed out
rather than folded in.

## D-011 — Date range validation is repaired rather than restated

**Self-resolved. This is a defect.**

The old FR-020 required that a project could not be saved with an end date before its start date.
`ProjectDate.clean()` compares `self.date` and `self.end_date` (`fairdm/core/project/models.py:168`)
and neither field exists — the abstract carries `type` and `value` only
(`fairdm/core/abstract.py:295`). Any full validation of a project date raises an attribute error
rather than a validation error, and both tests covering it are skipped.

The requirement is kept and restated to match the data actually stored: the check is across the
project's date records, not within one of them. The broken method goes.

## D-012 — Metadata export is kept and is largely unbuilt

**Self-resolved.**

The old FR-023 required machine-readable export carrying descriptions, dates, identifiers and
contributors. What exists are two administrative actions: one emitting six scalar fields
(`fairdm/core/project/admin.py:129`) and one emitting three (`:154`). Neither carries a related
record. There is no linked-data export for projects at all, and the export tab in the portal is an
empty page (`fairdm/core/project/plugins.py:35`).

Settled in the specification's favour. Export is the mechanism by which a project record becomes
findable outside the portal, which is most of why the metadata is collected. The requirement stands
and the work is real.

The empty portal export tab is out of scope here — it is a view.

## D-013 — Funding becomes structured

**Self-resolved.**

The old FR-024 called for funding in DataCite's shape. The field is a free-form JSON column with no
validation (`fairdm/core/project/models.py:86`), is deliberately excluded from the portal form
(`fairdm/core/project/forms.py:79`), and is rendered by dumping the raw object into a template that
is itself unreachable (`fairdm/core/project/templates/project/plugins/overview.html:27`).

Settled in the specification's favour on the data, and out of scope on the form. Funding that is not
validated cannot be exported to DataCite, which is the only reason to hold it in DataCite's shape,
so the structure is specified and enforced here. Whether the portal form exposes the field is 013's
call to make, and 013's FR-018 already says it should.

The retired flat shape carried an `amount`. DataCite's funding reference schema has no field for it —
funding a project's amount is not part of what DataCite records about a funder or an award — so the
conversion migration (`fairdm/core/project/migrations/0008_convert_funding_to_datacite_shape.py`)
drops it on the way in. There is nowhere for it to go, forwards or back, so that migration is
irreversible: a reverse built from `funderName` and `awardNumber` alone would also drop
`funderIdentifier`, `funderIdentifierType`, `awardTitle` and `awardURI` from any record that carries
them, and could not distinguish a record it produced from a project created directly in the new shape
afterwards. It declares no reverse, so a rollback fails loudly rather than destroying data.

## D-014 — Internationalisation is split along the same scope line

**Self-resolved.**

The old FR-019 required every user-facing string to be translatable. Models, admin and filters use
the lazy translation function; forms and views use the eager one
(`fairdm/core/project/forms.py:5`, `fairdm/core/project/views.py:8`), so their labels and help text
are frozen at import. No translation catalogues exist in the repository at all.

The requirement is kept for the surfaces this specification owns — model fields, vocabularies, admin
labels and validation messages. The eager-translation defect in the form and view modules is a
013-layer defect and is routed out.

## Routed out

Findings that are real but are not this feature's work:

| Finding | Where it goes |
|---|---|
| Detail page shows four count tiles and no metadata (`views.py:219`) | #167 |
| Organisation-scoped visibility (D-006) | #168 |
| Which contribution roles confer which permissions (D-009) | #169 |
| Full revision history for core records (D-010) | #170 |
| Descriptions, keywords and key dates have no portal page — the plugin classes exist but are never registered (`plugins.py:52`) | #171 |
| Administrative bulk actions set the wrong status: "Active" writes Planning, "Completed" writes In Progress (`admin.py:115`, `:123`) | Repaired here — it is an admin defect, and the admin is in scope |
| Keyword filtering combines terms with OR while the old text promised AND (`filters.py:85`) | #172 |
| Eager translation in the form and view modules (D-014) | #173 |
| Update, delete and detail views bypass their own querysets and their prefetching (`views.py:157`, `:199`, `:250`) | #174 |
| Detail view compares visibility against the literal `1` (`views.py:253`) | #174 |
| `ProjectQuerySet.with_list_data()` has no callers (`models.py:49`) | #174 |
| The project overview template extends a parent that does not exist and is registered nowhere (`templates/project/plugins/overview.html:1`) | #167 |
| The REST API exposes project create, update and delete, which no specification describes (`fairdm/api/viewsets.py:72`) | Noted against 011, the API specification |

## D-015 — A methods description belongs to a dataset, not a project

**Self-resolved, after implementation surfaced it.**

The rewritten specification's first user story described a researcher writing "a description of the
methods". The project description vocabulary deliberately omits that type — it is commented out of
the project collection at `fairdm/core/vocabularies.py` and present in the dataset collection.

Settled in the code's favour, and the specification is the thing corrected. Methods describe how data
was produced, and the dataset is the record that carries them; repeating them on the parent would
duplicate them across every dataset beneath it. This is the same reasoning as D-004 on
data-collection dates, and finding the two independently is evidence the line is in the right place.

A pre-existing test attached a methods description to a project and passed anyway, because the type
field is a plain character field and Django does not validate choices on save. That is the blind spot
the vocabulary-binding tests added on this branch exist to close. The test now uses a type the
project vocabulary contains.
