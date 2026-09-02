# Quickstart — 015, browsing a portal's samples and measurements by type

Phase 1 output. Walks through the feature end to end, in the order a reviewer or a portal author
would actually hit it. Doubles as the manual check behind SC-001 and SC-005.

## 1. Publish a dataset

In the Django admin, open a `Dataset` and check **Published**. Save.

```python
# Equivalent, for a test or a shell session:
dataset.published = True
dataset.save()
```

No other page changes. `dataset.get_absolute_url()`, its visibility, its metadata form — all
identical to before this feature (US-1, Acceptance Scenario 3).

## 2. Register a type and write nothing else

```python
# fairdm_demo/config.py
@fairdm.register
class RockSampleConfig(BaseSampleConfiguration):
    model = RockSample
```

Restart the dev server. `RockSample`'s listing exists at its own address, reachable from the
navigation under **Samples**, with no `fields`, no `search_fields`, no URL entry and no menu entry
written by hand (SC-001, FR-015). Its columns come from the registry's own inspection of the model.
Searching the record's name works out of the box (FR-024) because nothing was declared.

Declaring `fields` narrows the columns and changes nothing else:

```python
@fairdm.register
class RockSampleConfig(BaseSampleConfiguration):
    model = RockSample
    fields = ["name", "rock_type", "collection_date", "weight_grams"]
```

## 3. Declare which fields search covers

```python
@fairdm.register
class WaterSampleConfig(BaseSampleConfiguration):
    model = WaterSample
    fields = ["name", "water_source", "ph_level"]
    search_fields = ["name", "water_source"]
```

Typing a word from `water_source` into the listing's search box now narrows to matching records
(US-3, Acceptance Scenario 2); a word that only appears in `ph_level` matches nothing (Acceptance
Scenario 3), because `ph_level` was not declared.

Two kinds of bad declaration are refused immediately, at import. A path that names nothing:

```python
search_fields = ["not_a_real_field"]
# FieldValidationError at server start, naming WaterSampleConfig and "not_a_real_field"
```

and a path that resolves to a field the framework cannot search — search is a case-insensitive
substring match over text, so a number, a boolean, a date or a geometry is refused:

```python
search_fields = ["name", "ph_level"]     # ph_level is a DecimalField
# FieldValidationError at server start, naming WaterSampleConfig and "ph_level"
```

Both fire at start-up rather than on the first search a visitor types.

## 4. Browse, narrow, and confirm publication is honoured

1. Sign out (or use an anonymous test client).
2. Open the listing for a type with at least one record in a published dataset and one in an
   unpublished dataset.
3. Confirm only the published record's row appears.
4. Search for a word unique to the unpublished record's name — confirm it returns nothing (US-3,
   Acceptance Scenario 5).
5. Open a measurement listing where one row's sample belongs to an unpublished dataset — confirm
   the row appears, but with no sample name and no link (US-2, Acceptance Scenario 7).
6. Publish a dataset while leaving its visibility private — the ordinary state, since visibility
   defaults to private. Confirm its records appear (publication alone decides that, US-1 Acceptance
   Scenario 5) and that their dataset column carries no link to the dataset's own page, which the
   visitor would be refused (D3, research.md R14).

## 5. Move between listings without a detour

From any listing, use the switcher control. It lists every other registered type's listing,
grouped under **Samples** and **Measurements**, with the current one marked. Choosing a measurement
type from a sample listing opens it unfiltered — no search term or filter value follows across
(D6, US-5 Acceptance Scenario 6).

## 6. Confirm the query count is flat

```python
from django.test.utils import CaptureQueriesContext
from django.db import connection

with CaptureQueriesContext(connection) as ctx:
    client.get(reverse("rocksample-list"))
n_one_page = len(ctx.captured_queries)

# ... create 50 more published RockSample records ...

with CaptureQueriesContext(connection) as ctx:
    client.get(reverse("rocksample-list"))
n_full_page = len(ctx.captured_queries)

assert n_one_page == n_full_page  # SC-006
```

## 7. Confirm the index (SC-007)

Introspect the table the column actually lives on. `name` is declared on `BaseModel`, so it belongs
to `Sample` and `Measurement`; `RockSample` is a concrete subclass whose own table holds only its
own fields, and no `name` index will ever be found there.

```python
from django.db import connection
from fairdm.core.measurement.models import Measurement
from fairdm.core.sample.models import Sample

for model in (Sample, Measurement):
    with connection.cursor() as cursor:
        indexes = connection.introspection.get_constraints(cursor, model._meta.db_table)
    assert any("name" in idx["columns"] for idx in indexes.values() if idx.get("index"))
```

## What this feature does not do

- No portal page lets a researcher publish their own dataset (FR-004) — that is the Django admin
  only, deliberately, until R22 designs the real workflow (D2).
- No dataset-scoped, project-scoped, or sample-scoped listing (FR-053) — that is R18.
- No download of any format from a listing (FR-052) — that is R21.
- No ranking, typo tolerance, or search across more than one type at once (FR-034) — that is R17.
