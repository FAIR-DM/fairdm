# Quickstart — 004 The dataset record

**Regenerated 2026-08-18**, against `spec.md`, `decisions.md`, `plan.md`, `research.md` and
`data-model.md`.

The January version of this file survived the specification rewrite untouched and taught patterns
this work removes — `Dataset.objects.with_private()`, `Dataset.objects.get_all()`, the
`description_type` / `date_type` / `identifier_type` field aliases, a four-level visibility and a
`PROTECT` project relation. A developer following it would build the exact behaviour this
specification exists to remove, so it is replaced rather than corrected.

**These are the patterns the work builds to, not the ones the code has today.** Where today's code
differs, it says so.

This covers the dataset record and the administrative interface. It does not cover the portal's
list, create, edit and delete pages, their forms or the filter set behind the list — those are
`014-dataset-crud-views`.

## Reading datasets

Start here, because this is the one that matters.

```python
from fairdm.core.dataset.models import Dataset

# The ordinary route. Never returns a private dataset.
Dataset.objects.all()
Dataset.objects.filter(project=project)

# The explicit route. Returns every dataset, including private ones.
Dataset.all_objects.all()
Dataset.all_objects.filter(project=project)
```

`Dataset.objects` is a manager that excludes private datasets before you narrow anything, so the
exclusion is in the SQL by the time you hold a queryset. Reaching a private dataset is a decision you
make **before** narrowing, by naming a different manager — not after, by calling a method.

There is deliberately no method that adds private datasets back:

```python
# Does not exist, and will not. It cannot work.
Dataset.objects.filter(project=project).with_private()
```

The version of `with_private()` in the code today rebuilds the queryset from the model and discards
everything you narrowed by, so that line returns every dataset in the table rather than the ones on
`project`. A widening that silently discards the caller's conditions is worse than no widening at
all, so the method is removed rather than repaired (FR-019, R1).

`get_visible()` and `for_user()` go with it. There are two visibility levels, so "exclude private"
and "only public" select the same rows and `get_visible()` was a second name for the default.
`for_user()` had no callers and gated on a permission no model declares.

**What still sees every dataset, whichever manager you use:**

```python
dataset.project            # forward relations
project.delete()           # the deletion collector cascades to private datasets
```

Those go through the base manager, which is unfiltered. Following a relation to a private dataset
never raises `DoesNotExist` because of visibility.

**What does not:**

```python
project.datasets.all()     # reverse relation — excludes private datasets
```

That is correct for portal surfaces. Where you need every dataset on a project, ask the other way
round: `Dataset.all_objects.filter(project=project)`.

## Creating a dataset

```python
from fairdm.core.dataset.models import Dataset
from fairdm.utils.choices import Visibility

dataset = Dataset.objects.create(
    name="Rhine Valley heat flow, 2024 field season",
    project=project,
)

dataset.visibility  # Visibility.PRIVATE — the default
dataset.uuid        # "dQ7bR2..." — generated, prefixed "d", not editable
dataset.license     # the portal's configured default
```

A dataset is **private unless you say otherwise**. A dataset with no project is valid — data migrated
from a system with no project structure arrives that way. Two datasets may carry the same name.
The generated identifier is what names one unambiguously.

To publish it:

```python
dataset.visibility = Visibility.PUBLIC
dataset.save()
```

`Visibility` has two members, `PRIVATE` and `PUBLIC`, and nothing else. Docstrings and filters around
the package still refer to an `INTERNAL` tier — no such value exists, and correcting those statements
is part of this work (D-006, FR-031). An organisation-scoped level between the two is issue #168.

## Descriptions, dates and identifiers

All three related records carry the same three fields: `related`, `type` and `value`. **Each field
has exactly one name.**

```python
dataset.descriptions.create(type="Abstract", value="Heat flow measurements from …")
dataset.descriptions.create(type="Methods", value="Needle-probe measurements at …")

dataset.dates.create(type="CollectionStart", value="2024-03")
dataset.dates.create(type="CollectionEnd", value="2024-09-14")

dataset.identifiers.create(type="DOI", value="10.5880/fidgeo.2024.017")
```

Reading back by type:

```python
abstract = dataset.descriptions.get(type="Abstract")
abstract.value

doi = dataset.identifiers.filter(type="DOI").first()
```

The aliases the code carries today — `description_type`, `description`, `date_type`, `date`,
`identifier_type`, `identifier` — are removed (FR-014, D-012). They were documented as "API
compatibility" for an API that exposes none of these records, nothing outside the dataset app read
them, and `dates__date_type` as an ORM path is the direct cause of a filter that raises `FieldError`
every time it is applied. **Write `type` and `value`.**

`.in_order()` returns rows in the order the vocabulary declares, rather than by primary key:

```python
for description in dataset.descriptions.in_order():
    print(description.type, description.value[:60])
```

### One row per type

A dataset carries at most one description, date or identifier of each type. The limit is enforced by
a database constraint, so a concurrent write cannot slip past it, and in `clean()`, so a researcher
gets a message naming the type rather than a database error.

```python
dataset.descriptions.create(type="Abstract", value="First")
dataset.descriptions.create(type="Abstract", value="Second")  # IntegrityError
```

Different types are fine, and an identifier value is unique across **every** record that carries
identifiers — not just within one dataset. The same DOI cannot name two things.

### The vocabularies

| Record | Members |
|---|---|
| Descriptions | Abstract, Methods, SeriesInformation, TechnicalInfo, Other |
| Dates | Available, CollectionStart, CollectionEnd, Submitted, Published, Withdrawn |
| Identifiers | DOI |

`Created` is not a dataset date type — the moment a record was created is already its `added`
timestamp, and a dataset's collection period is what these dates are for. `ARK`, `Handle`, `URL` and
`URN` are not identifier types. Nothing in the repository or the roadmap asks for them, and an unused
member is a wrong choice offered to every user.

Watch for this, because it is why the drift above went unnoticed for so long:

```python
# Persists silently. Django does not validate choices on save.
dataset.dates.create(type="Created", value="2024-01-15")

# Refused.
date = DatasetDate(related=dataset, type="Created", value="2024-01-15")
date.full_clean()  # ValidationError
```

`objects.create()` does not call `full_clean()`. If you are checking that a type is valid, validate
explicitly — and if you are writing a test about a vocabulary, **assert its members by name**. A loop
over `VOCABULARY.choices` passes over an empty collection and proves nothing (SC-004).

### The collection period

A collection end earlier than the collection start is refused, whichever of the two you are editing,
with a message naming both dates.

```python
dataset.dates.create(type="CollectionStart", value="2024-09")

end = DatasetDate(related=dataset, type="CollectionEnd", value="2024-03")
end.full_clean()  # ValidationError — the end cannot precede the start
```

Dates are partial: `"2024"`, `"2024-09"` and `"2024-09-14"` are all valid, and comparison happens at
the coarser of the two precisions. `"2024"` against `"2024-09-14"` compares as years and does not
conflict. A collection end with no start present is accepted, because there is nothing to
contradict.

## Literature

A dataset names at most one data publication, and relates to any number of other items under a stated
relationship type.

```python
dataset.reference = paper          # the publication describing this dataset
dataset.save()

from fairdm.core.dataset.models import DatasetLiteratureRelation

DatasetLiteratureRelation.objects.create(
    dataset=dataset,
    literature_item=other_paper,
    relationship_type="IsCitedBy",
)
```

Relationship types are DataCite's. The same item may be related under two different types, but not
twice under one. Deleting the named data publication leaves the dataset intact with no publication
named.

```python
for relation in dataset.literature_relations.select_related("literature_item"):
    print(relation.get_relationship_type_display(), relation.literature_item)
```

## Contributors

```python
dataset.add_contributor(person, with_roles=["Creator", "DataCollector"])

dataset.is_contributor(user)
dataset.get_direct_contributors()
```

Roles come from the dataset role collection — Creator, ContactPerson, DataCollector, DataCurator,
DataManager, Editor, Producer, RelatedPerson, Researcher, ProjectLeader, ProjectManager,
ProjectMember, Supervisor, WorkPackageLeader, RightsHolder, Other. They are expressible in DataCite's
contributor types, so a future submission needs no translation table.

**A role does not confer a permission.** The `ROLE_PERMISSIONS` map in the code today names `Viewer`
and `Manager`, neither of which is a role in that collection, and nothing reads it. It is removed.
Which roles confer which rights is issue #169.

Separately from contributions, a dataset records who created it:

```python
dataset.created_by          # a Person, or None if that account has been removed
```

The creator is written server-side, never through a form or a serialiser field, and survives the
removal of both the account and the contribution record. A contribution can be withdrawn. The fact of
authorship cannot.

## Loading a full record

```python
datasets = Dataset.objects.with_related()

for dataset in datasets:
    dataset.project.name
    dataset.descriptions.all()
    dataset.identifiers.all()
```

The number of queries does not grow with the number of related records a dataset carries (FR-030).
If you are asserting that in a test, assert it at **two different related-record counts** — a single
count cannot tell a bounded query from an unbounded one.

```python
dataset.has_data   # whether any samples or measurements hang beneath it
```

## Licences on a portal

```python
FAIRDM_DEFAULT_LICENSE = "CC BY-SA 4.0"   # in the portal's settings
```

Standing a portal up seeds the licences the framework recommends — CC0 1.0, CC BY 4.0 and
CC BY-SA 4.0 — so the configured default resolves without anyone loading a fixture by hand. The step
is idempotent and keyed on the licence name, so running it twice changes nothing, including a licence
the portal has edited. A portal that wants a different set drops the step and curates its own rows.
Which licences a portal offers is its own decision.

The NC and ND variants are not seeded. They fail the Open Definition, and a framework named for
reusability should not present "no derivatives" as a recommendation for research data. A portal that
needs one adds it.

Without this, a portal that has migrated has no `License` rows at all: the configured default
silently resolves to `None`, and the create form is a required field over an empty list (D-018, R4).

## In the administrative interface

The administrative dataset list **shows private datasets**, and that is a requirement rather than an
oversight — the interface that repairs a portal has to reach the records that need repairing. It gets
there by overriding the queryset:

```python
class DatasetAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        # The default manager hides private datasets. The admin is where an
        # unfinished dataset gets repaired, so it uses the unfiltered manager.
        return Dataset.all_objects.get_queryset()
```

Datasets are findable by name, by their own generated identifier, by any external identifier attached
to them, and by project. The list narrows by project, licence and visibility. Descriptions, dates and
identifiers are edited inline, each offering no more rows than its vocabulary has types. Each row
shows whether the dataset has an abstract and whether it has a DOI, computed in the list query rather
than per row.

No administrative action changes the visibility of more than one dataset at a time. Publishing is a
deliberate act on one record.

Changing the licence of a dataset that carries a DOI warns the administrator that metadata published
under the previous licence may need updating elsewhere.

## Writing tests

```python
from fairdm.factories import DatasetFactory

dataset = DatasetFactory()
public = DatasetFactory(visibility=Visibility.PUBLIC)

# Related metadata is opt-in
dataset = DatasetFactory(
    descriptions=2,
    descriptions__types=["Abstract", "Methods"],
)
```

Every factory defaults `type` to a member of its own vocabulary. `DatasetDateFactory` defaults to
`"Created"` today, which is not a member of the dataset date collection — that is corrected as part
of this work, along with the four tests using it as their example of a valid type (D-008).

Three habits, each earned by a test in this suite that passed while proving nothing:

- **Assert vocabulary members by name.** Iterating `VOCABULARY.choices` passes over an empty
  collection.
- **Do not assert that a string is absent from a page.** Three administrative tests check that the
  changelist markup does not contain "make public", "make private" or "change visibility". An action
  named anything else passes them. Read the behaviour off the administrative class instead.
- **Validate explicitly when you mean to test validation.** `objects.create()` skips `full_clean()`,
  so a test written through it proves the database constraint and nothing about `clean()`.

## What changed, if you have code against the old shape

| Was | Now |
|---|---|
| `Dataset.objects.with_private()` | `Dataset.all_objects` |
| `Dataset.objects.get_all()` | `Dataset.all_objects` |
| `Dataset.objects.get_visible()` | `Dataset.objects` |
| `Dataset.objects.for_user(user)` | removed; no replacement in this specification |
| `Dataset.objects.all()` returning private datasets | it no longer does |
| `description_type`, `description` | `type`, `value` |
| `date_type`, `date` | `type`, `value` |
| `identifier_type`, `identifier` | `type`, `value` |
| Deleting a project raising `ProtectedError` | it cascades to private datasets, and is blocked outright while any dataset is public |
| `Visibility.INTERNAL` | never existed |
| `Dataset.ROLE_PERMISSIONS` | removed |
| Datasets listed oldest-touched first | most recently changed first |
