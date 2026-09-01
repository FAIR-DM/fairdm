# Data Model — 015, browsing a portal's samples and measurements by type

Phase 1 output. Covers the one new field, the queryset/manager surface it needs, and the registry
attribute that is not a database change but is part of this feature's schema-adjacent contract
(`search_fields` governs which columns get an index — see `research.md` R5).

## `Dataset.published`

| Property | Value |
|---|---|
| Type | `models.BooleanField` |
| Default | `False` |
| Null/blank | Not nullable; no blank option — always has a value |
| Index | `db_index=True` (read on every listing request — R13) |
| Verbose name | `_("published")` |
| Help text | `_("Whether the data beneath this dataset may be shown publicly. Independent of visibility, which governs metadata only. Set in the Django admin.")` |
| Location | `fairdm/core/dataset/models.py`, alongside `visibility` (~line 245) |
| Migration | New file after `0011_...`, `AddField` only, no data migration (every existing row gets the column default, `False` — FR-002) |

**Relationships to existing fields**: independent of `visibility` (FS-014 D1) — no signal, no
`save()` override, no validation coupling between the two. `Dataset.Meta.permissions` is unchanged;
FR-004/FR-005 mean no new permission is introduced for this flag, because nothing outside the admin
sets it.

**State transitions**: none. It is a bare boolean an administrator flips; FR-005 explicitly forbids
this feature from adding any transition, review, or completeness check.

**Validation rules**: none beyond Django's own `BooleanField` validation. FR-005 forbids adding any.

## Queryset additions

### `SampleQuerySet.published()` — `fairdm/core/sample/managers.py`

```python
def published(self):
    return self.filter(dataset__published=True)
```

### `MeasurementQuerySet.published()` — `fairdm/core/measurement/managers.py`

```python
def published(self):
    return self.filter(dataset__published=True)
```

Deliberately **not** `sample__dataset__published` — FR-012/D3: a measurement's presence is decided
by its own dataset, never its sample's. Combined with `.select_related("dataset", "sample__dataset")`
at the call site (research.md R3) so `render_sample`'s read of `sample.dataset.published` (FR-013)
costs no extra query.

Neither method touches the *default* manager (`Sample.objects`, `Measurement.objects` stay
unfiltered) — see research.md R1 for why this is a queryset method, not a manager-level default.

## `ModelConfiguration.search_fields` (registry attribute, not a DB field)

| Property | Value |
|---|---|
| Type | `list[str] \| None` |
| Default | `None` (resolves to `["name"]` via `get_search_fields()` — FR-024) |
| Declared on | `ModelConfiguration` (`fairdm/registry/config.py`), added to `_OVERRIDABLE` |
| Validated | At `__init__`, via `FieldInspector.resolve_path` per entry (same mechanism as `fields`/`exclude`), refusing at import with the type and field named (FR-026) |
| Accessor | `get_search_fields(self) -> list[str]`: `return self.search_fields or ["name"]` |
| Consumed by | `DataTableView.get_queryset()`/`setup()`, assigned to `self.search_fields` before `SearchMixin` runs |

This is not one of the six `COMPONENTS` entries (form/table/filterset/serializer/resource/admin) —
it generates no class, so it does not fit that table's `Component(fields_attr, class_attr, base,
factory)` shape. It is a plain declared list consumed directly by the view layer, mirroring how
`ProjectListView.search_fields` and `DatasetListView.search_fields` are already plain view
attributes (`fairdm/core/project/views.py`, `fairdm/core/dataset/views.py`) — the registry's job is
only to let a *type* declare it once instead of a portal author subclassing the view.

## Index requirement (FR-027, SC-007)

`BaseModel.name` (`fairdm/core/abstract.py:31`) gains `db_index=True`. This is the field every
`get_search_fields()` call falls back to when a type declares nothing (FR-024), so it is the one
field this feature is responsible for indexing. A field a `search_fields` declaration adds beyond
`name` is the model author's own field to index (FR-027's stated boundary, D4) — this feature adds
no automatic indexing of arbitrary declared fields.

## Entities carried over unchanged

`Sample`, `Measurement`, their existing FK-to-`Dataset` fields, `ModelConfiguration`'s other six
components, and the registry's `samples`/`measurements`/`get_for_model` accessors are all read, not
modified, beyond the two queryset methods and the one new attribute above.
