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

**Chosen:** the text those terms already carry in the current vocabularies. Terms with no
definition today get one written as part of this work.

**Why:** the existing definitions were written deliberately and are the reason this layer exists
at all. Reauthoring them would put a documentation change inside a migration, where nobody would
review it as one. A set that only half explains itself does not satisfy US-1, so the gaps are
filled rather than carried.

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
