# Research — 009 contributors and contributions

Questions the plan needed answered before the work could be ordered. Each was resolved against a
source that can be checked, and the source is named.

## R1 — Which organisation types ROR defines, and whether an organisation has one or several

**Finding.** ROR schema 2.1 defines exactly nine, as an enumeration on `types`:

`education`, `funder`, `healthcare`, `company`, `archive`, `nonprofit`, `government`, `facility`,
`other`.

Read from the schema itself rather than from documentation about it —
`ror-community/ror-schema/ror_schema_v2_1.json`, the `types` array's `items.enum`.

**The one thing that does not carry across.** In ROR, `types` is an **array**: one organisation may
be both a `funder` and a `government` body, and many are. The decision taken here is a single
selection, which is a deliberate narrowing. It is the right narrowing for now — a portal displaying
and filtering by institution kind wants one answer, and nothing in this specification consumes more
than one — but it means an organisation synchronised from ROR in future has to choose which of its
types to keep. That choice belongs to the synchronisation work (#244), and is recorded as an
assumption in the specification rather than left to be discovered there.

**Shape.** A `TextChoices` enumeration, not a controlled vocabulary. The repository reserves
vocabularies for multi-valued scientific terms bound through `ConceptManyToManyField`, and uses
plain choices for small fixed framework sets — `Visibility` in `fairdm/utils/choices.py` is the
precedent. Nine stable values selected one at a time is the second case.

## R2 — Composing a manager from a queryset when the manager is also a user manager

**Finding.** `from_queryset` works unchanged for a user manager, and the repository already does the
equivalent everywhere else: `fairdm/core/dataset/models.py:159`,
`fairdm/core/sample/models.py:134`, `fairdm/core/measurement/models.py:50`.

The contributors application is the outlier. `UserManager` (`managers.py:9`) inherits
`BaseUserManager` and `PrefetchPolymorphicManager`, overrides `get_queryset` to return
`PersonQuerySet`, and then hand-writes six methods that do nothing but forward
(`managers.py:77`–`:99`). `PersonQuerySet` is defined below the manager that names it, which works
only because the reference sits inside a method body.

**Resolution.** `UserManager` is built as
`BaseUserManager.from_queryset(PersonQuerySet)` composed with the polymorphic prefetch manager, with
the queryset defined above it. The six forwarding methods are deleted rather than rewritten. Nothing
about `create_user`, `create_superuser` or `create_unclaimed` changes — those are manager
responsibilities and stay on the manager.

## R3 — What replacing the privacy field with a configuration field does to existing rows

**Finding.** A rename preserves the column and its contents; a new field plus a drop does not.
`privacy_settings` currently holds, at most, a single key seeded by `Person.save()` — `email` set to
`public` or `private`. Nothing reads it.

**Resolution.** `RenameField` to `config`, then `AlterField` for the new help text, and a data
migration that empties the column. The rename keeps the operation reversible and keeps Django from
treating it as a drop-and-add. The contents are cleared because the one key they can contain
describes a policy this specification removes, and leaving it would be a stale instruction to
whatever eventually reads the store (#246).

Nothing outside this repository is affected: `privacy_settings`, `get_visible_fields`, `weight` and
`calculate_weight` appear nowhere in `ghfdb-portal` or `django-literature`, the two consumers
available to check.

## R4 — Making a derived account state both readable and filterable

**Finding.** A Python property cannot be filtered on, and a stored field would be the second truth
D8 rejects. The two have to be written separately and kept in step, which is the standard Django
shape for a derived state: a property for reading one record, an annotation or a queryset method for
selecting many.

**Resolution.** A `state` property on the person returning a member of a `PersonState` text
enumeration, and one queryset method per state on `PersonQuerySet`. The property is the definition;
each queryset method expresses the same condition in the database.

Because the two express the same rule twice, they are tested against each other rather than
separately: a fixture containing every state asserts that filtering for a state returns exactly the
people whose property reports it, and that the four filters partition the population. That test is
what stops the pair drifting, and it is cheaper than any abstraction that would prevent the
duplication.

The precedence is fixed so the states cannot overlap: inactive, then claimed, then invited, then
ghost.

## R5 — Whether the identifier uniqueness rule already exists

**Finding.** It does. `migrations/0007_add_unique_type_constraints.py` adds
`UniqueConstraint(fields=("related", "type"))`, preceded by
`0006_cleanup_duplicate_types.py` which clears existing violations. So "a contributor carries at
most one identifier of a given type" is enforced at the database level today.

**Resolution.** No work beyond a test. The audit found no test covering it, and a constraint with no
test is a constraint that can be dropped by an unrelated migration without anything noticing.

## R6 — Listing sub-organisations in the administrative interface

**Finding.** `Organization.parent` is a self-referential foreign key with
`related_name="sub_organizations"` (`models.py:894`). Django's `InlineModelAdmin` requires
`fk_name` when a model has more than one foreign key to the parent model; here there is exactly one,
so `fk_name="parent"` is not strictly required but is stated for clarity. The inline is over
`Organization` itself.

The existing commented-out attempt (`admin.py:86`) is the shape needed. What it lacks is a reason it
was commented out, and nothing in the history says. The likely cause is recursion in the change
form, which a read-only inline with no add permission avoids.

**Resolution.** A read-only inline listing sub-organisations, with adding and deleting disabled.
Re-parenting an organisation happens on that organisation's own page, which is where the parent
field lives, so an editable inline here would offer a second route to the same fact.

The existing test asserts that the page contains the string "parent" or the string "sub"
(`test_admin.py:223`), which the parent form field alone satisfies. It is replaced by an assertion
on the inline's presence in `ModelAdmin.inlines`.

## R7 — Whether changing the parent key to `SET_NULL` needs more than an `AlterField`

**Finding.** No. The field is already `null=True, blank=True` (`models.py:894`), so `SET_NULL` is
valid without a schema change beyond the constraint's delete rule, and no existing row is affected —
the change alters what happens on a future delete, not any stored value.

**Resolution.** A single `AlterField`. The test that matters is behavioural rather than structural:
delete a parent, and assert the child survives with a null parent and with its members and credits
intact.

## R8 — What removing the ranking score costs

**Finding.** Nothing reads it. `weight` (`models.py:165`) is stored, `calculate_weight`
(`models.py:305`) computes it, and no caller exists — not an ordering, not a view, not a test, not a
downstream package. `calculate_profile_completion` (`models.py:292`) has one caller, which is
`calculate_weight`. Every row therefore holds the default of 1.0.

**Resolution.** Remove all three with a `RemoveField`. The public list this was built to order is
deferred by D1, and that work is better served by a ranking that is computed than by a column that
looks computed and is not.

## What was not researched, and why

- **How to fetch from ORCID and ROR.** Lifted out with #244.
- **How to render a citation.** Lifted out with #245.
- **What belongs in the configuration store.** Lifted out with #246.
- **Which portal roles exist.** Lifted out with #247.
- **Whether the derived ownership permission is the right mechanism.** Settled by D13 against the
  code and its migration, which carries the reasoning. The alternative — stored permission rows —
  was already tried in this repository and deliberately removed.
