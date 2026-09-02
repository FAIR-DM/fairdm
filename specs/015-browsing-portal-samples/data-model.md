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

### `DatasetQuerySet.published()` — `fairdm/core/dataset/models.py`

```python
def published(self):
    return self.filter(published=True)
```

On the dataset's own flag, not through a relation. Needed because `FilterFactory._get_smart_filters`
generates a `ModelChoiceFilter` for every `ForeignKey`, and every registered sample and measurement
type has one to `Dataset` — so scoping generated choice lists to published records (FR-030) calls
`.published()` on all three querysets, not two. Without it that scoping raises `AttributeError` at
the dataset filter.

**Reached through `Dataset.all_objects`, not `Dataset.objects`.** The default manager is
privacy-first and excludes private datasets, and publication is independent of visibility (D1,
FR-003), so a **published but private** dataset is the ordinary state rather than an edge case.
Building the choice list from `Dataset.objects.published()` would offer nothing for exactly those
datasets while the table beside it shows their records — a visible mismatch under FR-030. Publication
is the sole test a listing applies, so the unfiltered route is the correct one here. This is the only
place in the feature where the distinction bites: `SampleQuerySet.published()` and
`MeasurementQuerySet.published()` filter across a join on `dataset__published`, which never consults
`Dataset`'s manager.

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
by its own dataset, never its sample's.

Both are bare filters and carry no `select_related` of their own. The listing's eager loading —
`.select_related("sample__dataset", "sample__location")`, which is what makes `render_sample`'s read
of `sample.dataset.published` (FR-013) and `MeasurementTable`'s three `sample.location`-backed
columns cost no extra query — is added by `DataTableView.get_queryset()` instead, for the reasons in
research.md R3: `with_related()` documents itself as not doing deep nesting, and `published()` is
also used to scope filter choice lists, where those joins fetch nothing anyone reads.

Neither method touches the *default* manager (`Sample.objects`, `Measurement.objects` stay
unfiltered) — see research.md R1 for why this is a queryset method, not a manager-level default.

## `ModelConfiguration.search_fields` (registry attribute, not a DB field)

| Property | Value |
|---|---|
| Type | `list[str] \| None` |
| Default | `None` (resolves to `["name"]` via `get_search_fields()` — FR-024) |
| Declared on | `ModelConfiguration` (`fairdm/registry/config.py`), added to `_OVERRIDABLE` |
| Validated | At `__init__`, in two passes: `FieldInspector.resolve_path` per entry (same mechanism as `fields`/`exclude`), then `isinstance(field, (models.CharField, models.TextField))` on the resolved final field. Both raise `FieldValidationError` at import with the type and field named (FR-026) — the second because a numeric, boolean, date or geometry field resolves cleanly and then raises on the first search. It must be a positive test for a text field: Django registers `icontains` on `Field` itself, so asking whether the field *has* the lookup returns yes for every field type and rejects nothing. `FilterFactory._get_search_fields` (`fairdm/registry/factories.py:648-656`) already draws the line the same way |
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

**`name` gains an index and nothing else, deliberately.** Article IX asks a field for
`verbose_name` and `help_text`, and `BaseModel.name` (`fairdm/core/abstract.py:31`) carries only the
first. It is not given `help_text` here. The field is declared once on an abstract base and
inherited by four concrete models, so help text written for it appears in every form all four render
— a user-visible change to project, dataset, sample and measurement editing, decided on no evidence
about what those forms need, arriving inside a feature about browsing. The gap is real and predates
this feature; closing it is its own piece of work with its own review, and the index task is not the
place to smuggle it in.

**Reach of the change, recorded as intended (Article IX).** `name` is declared once on the abstract
`BaseModel`, so `db_index=True` there indexes **four** concrete models, not two: `Sample` and
`Measurement`, and also `Project` (`fairdm/core/project/models.py:62`) and `Dataset`
(`fairdm/core/dataset/models.py:186`). That is deliberate, not incidental — both of the latter
already search `name` from their own listings (`ProjectListView.search_fields`,
`DatasetListView.search_fields` at `fairdm/core/dataset/views.py:111`), so the index serves exactly
the query it exists for. The alternative, moving `db_index=True` off the base onto two concrete
declarations, would state the same decision twice and leave two live listings searching an
unindexed column. Four migrations follow — sample, measurement, project, dataset — and all four are
named deliverables of the index task, so `makemigrations --check` is clean across every app rather
than dirty in two the feature did not expect to touch.

## Entities carried over unchanged

`Sample`, `Measurement`, their existing FK-to-`Dataset` fields, `ModelConfiguration`'s other six
components, and the registry's `samples`/`measurements`/`get_for_model` accessors are all read, not
modified, beyond the two queryset methods and the one new attribute above.
