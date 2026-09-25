# Decisions — FS-016: Controlled vocabularies replace django-research-vocabs

Rationale too long to sit inline in `spec.md`, plus every ambiguity resolved without asking. Each
entry records what was open, what was chosen, and why the choice is defensible.

Decisions D-001 to D-007 were settled with the maintainer before the spec was written. D-008
onward were resolved during specification from that context.

---

## D-001 — The six vocabulary surfaces split into two kinds

**Open:** whether all six surfaces move to the controlled-vocabularies package, or only some.

**Chosen:** four move to closed, code-defined sets carrying definitions (sample status,
description type, date type, identifier type); two move to the package (contribution roles,
keywords).

**Why:** the four are enumerations of FairDM's own metadata model. They change when FairDM cuts a
release, nobody curates them, and a portal adding a member would break the interoperability the
framework exists to provide. Holding them as database rows buys extensibility that is explicitly
unwanted and charges a query for it.

There is also a forcing function. The generic metadata models push a vocabulary's members onto a
plain character column at class-construction time. The controlled-vocabularies package cannot
supply that, because its vocabularies are rows that may not exist when Python imports the model.
Those four surfaces could not be ported unchanged even if we wanted to.

Roles and keywords go the other way: both are already stored as concept references, both carry
definitions people argue about, and keywords are open by nature.

## D-002 — Identifier type is closed, with the rest

**Open:** identifier schemes (DOI, ORCID, IGSN, ROR) are externally defined and arguably a real
vocabulary with resolvable identity, unlike the other three.

**Chosen:** closed, with the rest.

**Why:** the maintainer's ruling, and it follows from D-001. Which identifier schemes FairDM
understands is a framework capability rather than a curatorial question — a portal cannot invent a
scheme and expect the framework to resolve it. Validating and resolving identifiers is a separate
roadmap item (R28), and nothing there needs the scheme list to be curated data.

## D-003 — FairDM's vocabularies ship as files in the package

**Open:** ship as files and import at deploy, ship as fixtures applied by migration, or publish at
resolvable addresses and fetch over the network.

**Chosen:** files in the package, loaded by a documented command.

**Why:** it keeps FairDM the author of its own vocabularies, and it makes a vocabulary change a
reviewable diff rather than a Python edit. Fixtures applied by migration would remove the operator
step but bury vocabulary content inside migration history, where it cannot be reviewed or
corrected without another migration. Publishing at resolvable addresses is wanted later and adds a
deploy-time network dependency that is not worth paying yet.

## D-004 — This is a breaking change carried by a guide, not by compatibility shims

**Open:** whether the framework must carry unknown downstream portals across automatically.

**Chosen:** no. One portal consumes FairDM, FairDM has not cut an official release, and the two
settings that let a portal plug in its own vocabulary classes have been unused for some time and
are removed here.

**Why:** the maintainer's ruling. Compatibility machinery for consumers that do not exist is cost
with no beneficiary, and it would have to be maintained through the very releases that are meant
to stabilise this layer.

## D-005 — Portals may not extend the four closed sets

**Open:** whether a portal can add a sample status or reword a description type for its domain.

**Chosen:** no, and there is no supported route to do so.

**Why:** the maintainer's ruling, and it is the reason the framework is worth adopting. A
framework whose core metadata model bends per portal provides no interoperability, and every
portal inventing its own terms is the outcome FairDM exists to prevent. A portal's own domain
terms belong on its own models, where the vocabulary field types are available to it.

Recorded as an architectural decision in `docs/adr/` as part of this work, because it is the
premise D-001, D-002 and D-006 all rest on.

## D-006 — Contribution roles stay concept references

**Open:** roles are closed to portals under D-005, so they could have become a closed set like the
other four.

**Chosen:** concept references, in the package.

**Why:** three reasons, none of which is extensibility.

1. Roles are many-valued, and Django has no clean multi-valued choice field. Converting would mean
   an array column or a through table holding strings — a real data migration buying nothing.
2. Roles carry external identity. The community role schemes have published definitions and
   addresses, and a concept models that natively where a choice member does not.
3. The dependency is already paid. Keywords need the package regardless, so roles cost nothing
   extra.

"Closed" here is an authoring rule rather than an architecture: FairDM ships the roles vocabulary
and portals do not import their own.

## D-007 — Existing migration history is not rewritten

**Open:** squash each app's migrations to remove every trace of the retired library, or write
forward migrations and leave the history intact.

**Chosen:** forward migrations. The history keeps its references to the retired library.

**Why:** the live portal is expected to be in an inconsistent migration state already, and a
deployment window is close. Coupling a history rewrite to a data conversion means a failed
upgrade cannot be attributed to either one. Kept apart, this change is a plain migrate against a
history that is already trusted.

The cost is acknowledged: three migration files continue to name the retired library's field
classes and a FairDM vocabulary class, so those import paths must stay resolvable. The squash is
worth doing and is deferred to its own change, when the portal's migration state is known good.

## D-008 — An unloaded portal warns, it does not refuse to start

**Open:** FR-010 originally said a portal must "report" unloaded vocabularies without saying
whether it starts.

**Chosen:** it starts, and raises a system check warning naming the missing vocabularies and the
command that loads them.

**Why:** a fresh install has an empty database by definition, so refusing to start would make the
portal unusable before its first setup step and would break the framework's promise that
registration alone produces a working portal. A warning is the level Django reserves for a
condition that is wrong but not fatal, and it is visible in exactly the place an operator is
already looking during setup.

## D-009 — FairDM supplies the load command

**Open:** whether portals run the vocabulary package's own import command against a file path, or
FairDM wraps it.

**Chosen:** FairDM supplies its own command, defaulting to every vocabulary it owns.

**Why:** a portal maintainer should not have to know where inside an installed package the
vocabulary files sit, and that path is not part of any published interface — it would break on a
layout change that is otherwise invisible. FairDM may also ship more than one vocabulary, and a
single command that loads them all is one documented step instead of a list that grows.

The preload step the retired library required in the always-run setup tooling is removed with the
library, so the number of setup steps does not grow.

## D-010 — The keyword vocabulary setting is portal-wide

**Open:** the entry it replaces sat under the dataset configuration, implying a per-record-type
list.

**Chosen:** one portal-wide list.

**Why:** a keyword means the same thing wherever it is applied, no open issue asks for a
per-record-type keyword set, and one list is simpler to document and to reason about. If a record
type ever needs its own, narrowing a portal-wide list is additive and breaks nothing written
against this decision.

## D-011 — The upgrade is all-or-nothing, and checks before it writes

**Open:** FR-017 originally said an unresolved term "stops the migration", which permits stopping
at the first one.

**Chosen:** resolve every recorded term first, then either report the complete list of failures
and convert nothing, or convert all of them.

**Why:** stopping at the first failure makes an operator discover the remaining bad rows one run
at a time, against a live database, with no way to see how much work is ahead. Reporting
everything at once turns the upgrade into a single decision. Converting nothing on failure means a
half-migrated database is not a state the upgrade can produce.

A rejected row means the data needs attention, not that the conversion is wrong. The upgrade
therefore names the terms it could not resolve rather than guessing, because a guess here silently
rewrites research credit and attribution.

## D-012 — Definitions are carried across, not reauthored

**Open:** where the definitions for the four closed sets come from.

**Chosen:** the text those terms already carry in the current vocabularies.

**Why:** the existing definitions were written deliberately and are the reason this layer exists
at all. Reauthoring them would put a documentation change inside a migration, where nobody would
review it as one.

The clause about filling gaps has no subject: all 98 terms already carry a `gettext_lazy`
definition (`research.md` §2), so nothing has to be written.

## D-013 — Per-record-type role narrowing is out of scope

**Open:** the roles vocabulary declares groupings for projects, datasets, samples, measurements
and contributors, and nothing enforces them. The form, the admin and the validation receiver all
check against the whole vocabulary.

**Chosen:** out of scope. The behaviour after this change is the behaviour before it.

**Why:** it is a deliverable of the portal-contributions roadmap item (R19), which owns offering
roles per record type. Building it here would widen a substrate change into a behaviour change,
and the substrate is what everything else is waiting on.

Worth stating plainly because the groupings look implemented: they are declared and ignored.

## D-014 — The keyword editing interface is out of scope

**Open:** issue #298 rebuilds keyword editing against the controlled vocabularies, which overlaps
this feature's subject.

**Chosen:** #298 owns the interface, this feature owns the substrate, and #298 depends on it.

**Why:** the two answer different questions. This feature decides what a keyword *is* and how it
is stored, scoped and migrated. #298 decides how a researcher edits one, which is a portal page
with its own navigation and form design, and which cannot be built until keywords are concepts.
Splitting them keeps this change reviewable and lets the interface be designed against a settled
substrate rather than alongside a moving one.

---

Decisions D-015 onward were taken during planning, from the evidence in `research.md`.

## D-015 — A metaclass subclass, not a new dependency

**Open:** the rich-choices mechanism could come from `django-enum` with its `enum-properties`
extra, which solves exactly this and is actively maintained.

**Chosen:** roughly fifteen lines subclassing Django's own `ChoicesType`, in
`fairdm/utils/choices.py`.

**Why:** Article VII asks a new runtime dependency to justify itself against the simplicity of the
dependency tree, and this is a closed problem with a small, verified answer. The mechanism was run
in this environment before being chosen: `.choices`, `.labels`, `.values` and `.names` keep
Django's exact semantics, `choices=` on a plain character column is unchanged, `gettext_lazy` works
for both label and definition, and templates reach all three because `do_not_call_in_templates` is
inherited.

`django-enum` would be the right call if FairDM wanted symmetric lookups, enum-typed field access
and the rest of its surface. It does not, and taking two dependencies to avoid fifteen lines trades
the wrong way.

## D-016 — Adopting the package drops Django 5.1

**Open:** FairDM declares `django = ">=5.1,<6.0"` and its required checks test both 5.1 and 5.2.
`django-controlled-vocabularies` requires Django `>=5.2`.

**Chosen:** narrow FairDM to Django `>=5.2`, and raise it with Sam before implementing rather than
assuming it.

**Why:** Django 5.1 reached the end of extended support in April 2026, so FairDM is currently
testing against an unsupported Django and the narrowing is correct independently of this feature.
The alternative — lowering the vocabulary package's own floor to 5.1 — would hold a second package
back to an end-of-life Django to preserve a version FairDM has no consumer on.

It is raised rather than self-resolved because it needs an edit to `.github/workflows/tests.yml`
and a change to the repository's required checks, neither of which is the run's to make.

## D-017 — Three frozen migrations are edited, and this is not the squash D-007 refused

**Open:** FR-020 removes the retired stub at `fairdm/core/choices.py:305`, which exists only so
`sample/migrations/0001_initial.py` stays importable. D-007 keeps migration history. Both cannot
hold while that migration names the class.

**Chosen:** edit the three migration files that name the retired library's field classes and the
stub, replacing them with the plain field the column has always been. Nothing else in the history
is touched.

**Why:** the two rules are only in tension if "keep the history" means "never edit a frozen file".
What D-007 refused was squashing — collapsing many migrations into new initials, which changes what
an existing database has to be reconciled against. This changes no applied state and no column: the
stored values, the column types and the ordering are identical before and after, and a database
that has applied these migrations needs nothing done to it.

Called out explicitly for the design review, because it is the only point where this plan touches
migration history and the distinction is exactly the kind that reads wrong at a glance.

## D-018 — Two dependencies in, one out

**Open:** Article VII requires a stated justification for each new runtime dependency.

**Chosen:** add `django-controlled-vocabularies` and `django-tomselect`; remove
`django-research-vocabs`.

**Why:** the first is the feature. The second is not a choice — the vocabulary package imports it
at module scope in both its views and its forms, so it arrives whether or not FairDM renders a
concept field, and it additionally requires its middleware and a mounted route or the field renders
as an empty control with nothing raised.

Net dependency count rises by one. The removed dependency is a git reference with no released
version, which is itself worth ending: nothing pinned it, and a resolution could change under the
project without any version number moving. D-019 defers the removal of the declaration itself to
the squash; the dependency stops being used by anything at this change, which is what Article VII
is about.

## D-019 — The retirement is from the running framework, not from the repository

**Open:** FR-019 as first written required the retired library gone from the migrations too, which
is the squash D-007 refused. The design review found the two mutually exclusive: thirteen migration
files across six applications name the library, and twelve of them do it through a
`dependencies = [("research_vocabs", …)]` graph edge or a `to="research_vocabs.concept"` lazy
reference. A graph edge needs the application installed, not merely importable, so uninstalling it
makes a migrate from empty fail at graph-load time and takes the test suite with it.

**Chosen:** narrow the retirement. The library stops being imported, referenced or drawn on by any
model, form, filter, admin class, table, template, setting or documentation page. Its distribution
and its `INSTALLED_APPS` entry stay, each carrying a comment saying why, until the deferred squash
removes them.

**Why:** the alternative is to edit the graph edges and lazy references in all thirteen files, which
sounds like more of D-017 and is not. Two things break. The historical state would say the keyword
join tables point at the new concept table from the start, while the live portal's tables actually
point at the old one — a divergence between Django's model state and the database that nothing
reconciles. And the upgrade migration has to read the old concept rows to resolve their names, which
it cannot do through historical models once the application is out of the history, so it would fall
back to raw SQL against a table that may not exist. Both land on the riskiest migration in the
change, on a live database, to buy a cleanup that the squash performs safely once the portal's
migration state is known good.

Leaving the old concept table in place has a second benefit worth naming: the source data survives
the upgrade, so a conversion that went wrong can be inspected rather than reconstructed.

## D-020 — The concept fields are added under temporary names, then renamed

**Open:** whether `Contribution.roles` and `keywords` can be converted in place.

**Chosen:** no. Each is added as a second field under a temporary name, the upgrade copies the rows
across, and a following migration drops the old field and renames the new one onto the original.

**Why:** `research.md` §6 assumed the new field would generate a through table under a different
name, so old and new could coexist. That is false. `ConceptsField` sets its membership model's
`db_table` to `field._get_m2m_db_table(cls._meta)` — Django's standard `<owner_table>_<field>`,
which is exactly the table the current field already uses. Converting in place therefore emits an
`AlterField` on a many-to-many whose old and new through models are both auto-created, and the
schema editor alters the existing join table's concept column to point at the new concept table
while keeping primary-key values that belong to the old one. Contributions would silently end up
crediting unrelated concepts, which is SC-003 failing without an error.

## D-021 — The upgrade migration lives in the contributors application

**Open:** `plan.md` placed the one data migration in `fairdm.core`, which is not an installed
application and has no migrations directory.

**Chosen:** `fairdm.contrib.contributors`, declaring dependencies on the latest migration of each of
the six applications that own an affected join table and on `controlled_vocabularies`, and
`run_before` on the migrations that drop the old fields.

**Why:** it has to be a real application, and it should be the one furthest downstream so the
dependency list reads forwards rather than backwards. Contributors owns the roles conversion and
already sits after the four record applications.

## D-022 — The mounted autocomplete route requires a signed-in user

**Open:** the vocabulary package's autocomplete view is mounted in every portal and no decision
recorded who may query it.

**Chosen:** mount it behind a login requirement, with one route smoke test as Article XVI requires.

**Why:** the search is a leading-wildcard match over an unindexed label column with a `distinct()`
over a join (`research.md` §4, raised upstream). That is cheap to abuse and expensive to serve on a
portal that has loaded a large domain vocabulary. FairDM cannot know how exposed a given portal is,
so the conservative default is the right one and a portal that wants it open can say so.
