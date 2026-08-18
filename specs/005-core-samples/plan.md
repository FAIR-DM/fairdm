# Plan — 005 The sample record

Reasoning behind each choice is in `research.md`; adjudications are in `decisions.md`. This file
says what gets built, in what order, and what it touches.

## Shape of the work

Eleven groups. Groups 0 and 1 change the record and the factories that build it, so everything
downstream depends on them and they run first, together. Groups 3 to 10 are independent of one
another once 2 is in.

| Group | Story | Touches |
|---|---|---|
| 0 Foundations | US-10 | `fairdm/core/vocabularies.py`, `fairdm/factories/core.py`, `fairdm_demo/factories.py`, the test suite's sample call sites |
| 1 The record | US-10 | `fairdm/core/sample/models.py`, `managers.py`, migrations |
| 2 Polymorphism and the registry | US-1 | `models.py`, `config.py`, `fairdm_demo/config.py`, factories |
| 3 Descriptions | US-2 | `models.py` |
| 4 Dates | US-3 | `models.py` |
| 5 Identifiers | US-4 | `models.py`, `fairdm/core/vocabularies.py` |
| 6 Status | US-5 | `models.py`, `fairdm/core/vocabularies.py`, an inert stub in `choices.py`, migrations |
| 7 Access | US-6 | new shared backend, `fairdm/conf/settings/auth.py`, `sample/permissions.py`, `sample/plugins.py` |
| 8 The mixins | US-7 | `sample/filters.py`, `sample/forms.py`, `fairdm/registry/factories.py` |
| 9 Provenance | US-8 | `models.py`, `managers.py` |
| 10 Administration | US-9 | `sample/admin.py` |

## The decisions that shape it

**Identifier validation is loose and deliberate.** An IGSN is a DataCite DOI spread across at least
38 prefixes with no shared prefix and no enforced suffix grammar (R1). The check normalises common
prefixes away and then accepts a DOI or the legacy Handle form, case-insensitively. Nothing
resolves over the network. The shipped regex is replaced rather than widened, because every one of
its four clauses is wrong.

**Permissions are fixed once, in a shared backend, for every polymorphic record.** Normalising the
object to its base instance before the guardian check is the only option that satisfies both a
direct grant on a specimen and a grant inherited from its dataset (R2). It is gated on the object —
normalise when the instance's real class differs from its polymorphic base and that base owns the
permission — so no currently-passing check changes behaviour. Raw guardian leaves
`AUTHENTICATION_BACKENDS` and the shared backend is registered in its place, because a backend that
delegates blindly reintroduces the raise, and leaving the other records' permissions to reach the
replacement by delegation is an unwritten contract (D-018).

This reaches measurements and contributors. That is the fix's natural surface rather than scope
creep: the defect is in the backend chain, and writing it for samples alone would leave a blind
delegator in front of it. Measurements gain working object permissions as a consequence, and their
three skipped permission test classes are left for their own specification to un-skip — this work
does not claim them.

**The status change carries a mandatory data migration.** A `ConceptField` stores the concept's
name and raises on read when the stored name is absent from the field's vocabulary (R3). Leaving
old values in place would make every affected sample unreadable, so the migration is correctness,
not tidiness. It rewrites through `QuerySet.update()`, never by iterating instances, because
iterating triggers the conversion that raises.

**The base record is blocked with a `pre_save` receiver.** It is the only single mechanism that also
covers fixture loading, and it cannot fire on the framework's own read path, which a guard in
`__init__` would (R4). `Sample.clean()` stays so that forms and the admin still produce a validation
error rather than a server error.

**The permission repair has two halves that fail separately.** The backend fixes the check side.
Granting a right takes no part in the backend chain, so it needs the same normalisation again in a
wrapper — otherwise the record ends up with a right that can be consulted and never given (D-019).
The gate is keyed on the object rather than on the permission string, because the library only
compares application labels when the permission carries one, and a gate keyed on that comparison
would turn today's loud error into a silent denial.

**Blocking the base record is mostly a factory change.** The framework's own factory declares the
base model, and two more reach it without naming it. The sample factory becomes an abstract base and
concrete specimen factories live in the demo app, which is where a portal developer looks for the
example. That is the correct layering: the framework ships the abstract factory, the reference
implementation ships a concrete one.

**The filter mixin becomes a real filter set base**, with no `Meta` of its own, mirroring
`BaseListFilter` which already does exactly this for projects and datasets. The registry gains a
base-filter hook shaped like the base-table hook it already has.

## Data model

No new models. Changes to existing fields:

- `Sample.status` — repointed at the new custody vocabulary; `max_length` grows from 8 to 9, derived
  from the longest member name rather than written by hand.
- `SampleIdentifier.VOCABULARY` — scoped to a new `Sample` collection carrying IGSN and DOI.
- `SampleDescription.VOCABULARY`, `SampleDate.VOCABULARY` — unchanged; their validators are
  repaired.
- `SampleRelation` — unchanged. One relationship type, per D-004.

Indexing (Article IX): no new fields, so no new indexing decisions. The existing
`unique_together` on `SampleRelation` and the uniqueness on the generated identifier stay.

Migrations: one schema file for the field alterations, plus one standalone data migration for the
status rewrite, which Article IX exempts from squashing.

## Ordering and parallelism

**US-10 runs first, whatever its priority says.** It carries the factories and the block on creating
the base record, and those two are one change: the framework's own sample factory builds the record
the specification forbids, and about 140 call sites across fourteen test files reach it. Landing the
block before the retargeting would red the suite for the length of the run. The design review caught
this — the first draft had the block in the first story and the factories in the last.

Then US-1, which carries the registry work US-7 reads through. US-4 needs the identifier vocabulary
and US-5 the status vocabulary, both of which are the first task in their own story. Everything else
runs in parallel.

Every group writes its tests before its implementation (Article I). Test scope is one class per
task; the whole suite runs once per group, at its report.

## What this plan does not do

- Portal pages for samples, and the concrete form and filter set those pages would build (D-001).
- A material field, or relationship types beyond one (D-004, D-012).
- Un-skipping the measurement permission tests. Their skip reasons are wrong — they use base
  measurement instances and would not hit the error they blame — but they belong to `006`.
- Resolving identifiers against DataCite. Identifiers are stored and shape-checked, not verified.
- The `IdentifierLookup` gap that leaves an IGSN unlinked in the interface. Filed, not fixed here.
- The API's subclass-scoped permission scheme, which disagrees with the record's own. Two schemes
  cannot both be right, and choosing between them is a question for the maintainer rather than a
  repair to slip into this work.
