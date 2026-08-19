# Plan — 006 The measurement record

Reasoning behind each choice is in `research.md`; adjudications are in `decisions.md`. This file
says what gets built, in what order, and what it touches.

## Shape of the work

Eleven groups. Group 0 changes the fixtures every other group's tests are built on, so it runs
first and alone. Group 2 carries the registry changes that group 5 extends, so it runs second.
Everything from group 3 onwards is independent.

| Group | Story | Touches |
|---|---|---|
| 0 Foundations | US-1, US-10 | `fairdm/factories/core.py`, `fairdm_demo/factories.py`, the measurement suite's call sites |
| 1 The record | US-10 | `fairdm/core/measurement/models.py`, migrations |
| 2 Polymorphism and the registry | US-1 | `fairdm/core/admin.py` (deletions), `fairdm/registry/config.py`, `fairdm/registry/factories.py`, `tests/test_registry/test_config.py` |
| 3 Cross-dataset linking | US-2 | `models.py`, tests only where the behaviour is already right |
| 4 Descriptions, dates and identifiers | US-3 | `models.py` |
| 5 The mixins and their wiring | US-5 | `measurement/forms.py`, `measurement/filters.py`, `fairdm/registry/factories.py` |
| 6 Finding measurements | US-6 | `measurement/filters.py` |
| 7 Access | US-4 | `tests/test_core/test_measurement/test_permissions.py` — the backend itself is correct and is not modified |
| 8 The value | US-7 | `models.py`, the formatter's registration site, `fairdm_demo/models.py`, migrations |
| 9 Administration | US-8 | `measurement/admin.py` |
| 10 Loading | US-9 | `measurement/managers.py` |
| 11 Documentation | all | `docs/portal-development/measurements.md`, `docs/portal-administration/managing-measurements.md`, `docs/portal-development/using_the_registry.md`, `CHANGELOG.md` |

## The decisions that shape it

**The rendering moves out of the model rather than being repaired in it.** `print_value()` builds
its own string and reads an attribute the unit library does not have. It is not patched — it returns
`str(self.get_value())`, and the registry's formatter, which already produces `5.00 ± 0.30 m`, does
the work (R1). One definition of how a quantity looks, not two.

**That formatter's registration moves too, and this is a defect in its own right.** It is installed
as an import side effect of a template tag module, and Django imports those lazily. A value rendered
outside a template can therefore get the library's default formatting instead. Moving the
registration to application startup is what makes FR-038 testable without a template, so it is a
task rather than a note.

**The date-range filters do not use a date filter.** `MeasurementDate.value` is a partial date — a
year, a year and month, or a full date. Range lookups work when given a string or a `PartialDate`
and raise a validation error when given a `datetime.date`, which is precisely what a
`django_filters.DateFilter` produces after cleaning (R2). The filters hand a validated string
through instead. This is the whole content of the skip that has stood since the original run.

**The filter mixin becomes a filter set.** django-filter's metaclass collects declared filters only
from bases carrying `declared_filters`, which a plain class never does, so filters declared on a
plain mixin are silently dropped and filters declared elsewhere never arrive. The sample side solved
this and documented why in place; the measurement side copies it exactly, including the model-less
`Meta` that stops the metaclass generating a full unused filter set per subclass (R4).

**Two classes are deleted, not deprecated.** `MeasurementAdmin` and the second
`MeasurementParentAdmin` in `fairdm/core/admin.py` have no importer outside the two registry
references that are being repointed and the registry test that aliases one of them into place. There
is no external contract to keep: the class a portal is told to inherit is the configured one, and
the stub is what the registry wrongly enforced (R5).

**The demo keeps its existing fields when it gains a value.** `ICP_MS_Measurement` already carries a
concentration and an uncertainty as plain decimals. Adding a quantity-typed `value` and
`uncertainty` beside them, rather than replacing them, is what lets the demo show both a type that
has adopted the convention and the shape one has before it does (R8). Both new fields are optional,
so the migration is additive.

## Data model

One migration, additive, touching no existing column.

- `fairdm_demo`: `ICP_MS_Measurement.value` and `.uncertainty`, quantity fields, both nullable.
- No migration on `fairdm.core.measurement`. The record's fields do not change; what changes is what
  validates, what renders and what the registry generates.

Removing `MeasurementAdmin` needs no migration — administrative classes are not stored.

**Indexing, recorded as the constitution requires.** The researcher's own label is a plausible
search path and carries no index today; it gains one, because a portal consuming a published package
cannot add its own. The two new quantity fields on the demo type get none — a demonstration model
with no lookup path does not earn one, and adding it would suggest a pattern portals should copy.

## Ordering and parallelism

**Group 0 runs first and alone.** `MeasurementFactory` is declared against the bare record, which
FR-011 forbids and which the measurement suite reaches throughout. Landing the block before the
factory is retargeted would red the suite for the length of the run — the same ordering fault the
sample run's design review caught, and the reason that plan put its foundations first against their
stated priority.

**Group 2 runs second.** Group 5 adds a branch to the same two factory methods the registry work
touches, and the admin collapse changes what a generated component inherits. Sequencing them avoids
two implementers editing `fairdm/registry/factories.py` at once.

**Group 5 runs before group 6.** Three of group 6's tasks change filters that group 5 is in the
middle of moving from the concrete filter set onto the mixin. Run the other way round, that work
lands on a class the scope cut removes and has to be made twice — the design review caught this.

Groups 3, 4, 7, 8, 9 and 10 are independent of one another. Group 11 runs last, because a
documentation pass is only worth writing once the code it describes has settled.

**Stories run in parallel where their files are disjoint.** The earlier claim here — that the suite
shares one database, so implementers cannot run concurrently — was wrong, and was carried over from
the sample run without being checked. The test database is in memory and per process: two suites run
concurrently in two checkouts both pass. Measured, not assumed.

What actually constrains concurrency is the file each story edits, because two branches editing one
file collide at merge. Four clusters, run in parallel, sequential within each:

| Cluster | Stories, in order | Owns |
|---|---|---|
| A | US-10, US-3, US-2, US-9, US-7 | `measurement/models.py`, `managers.py`, `test_models.py`, migrations |
| B | US-1, US-5, US-6 | `fairdm/registry/`, `fairdm/core/admin.py`, `measurement/forms.py`, `filters.py` |
| C | US-8 | `measurement/admin.py` |
| D | US-4 | `test_permissions.py` |

The two ordering constraints sit inside cluster B, which is why they cost nothing: the registry work
precedes the mixins, and the mixins precede the filtering.

Every group writes its tests before its implementation. Test scope is one class per task; the whole
suite runs once per group, at its report.

## What this plan does not do

- The measurement pages, and the concrete form and filter set those pages would build (D-001, D-003).
- Restricting which samples a measurement may name (D-002). Selection stays open.
- Building the mechanism for reusing a sample across datasets without moving its ownership. That is
  issue #212 and it is a data-model change, not a repair.
- Correcting R18's note in the roadmap, or restoring the plugins removed on its reasoning. Both
  follow R16.
- Repairing the documentation beyond the pages this work makes wrong. The tree is known to be
  broadly out of date, and a general repair is not this feature's work.
- The API's representation of a measurement.
