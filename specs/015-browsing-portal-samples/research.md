# Research — 015, browsing a portal's samples and measurements by type

Phase 0 output. Each item resolves one technical unknown left open by `plan.md`'s Technical
Context, or records the codebase fact the design decision rests on. Judgement calls with a "why"
long enough to matter belong in `decisions.md`, not here — this file is about what the code
already does and what the framework already offers.

## R1 — Where the publication filter lives

**Question**: FR-011 needs "record if and only if its dataset is published" applied identically
everywhere a listing reads records. Where should that live so it cannot be bypassed by a future
caller?

**Finding**: `Dataset` already has this exact shape for `visibility` — `DatasetManager.get_queryset()`
excludes `PRIVATE` at `fairdm/core/dataset/models.py:182-183`, and `Dataset.objects` is the default
manager, while `Dataset.all_objects` is the explicit escape hatch used by admin and staff-facing
code (`fairdm/core/dataset/admin.py:227`). `Sample` and `Measurement` have no equivalent today —
their managers filter nothing (`fairdm/core/sample/managers.py`, `fairdm/core/measurement/managers.py`).

**Decision**: add `published()` **queryset methods**, not manager-level default filtering, on
`SampleQuerySet` and `MeasurementQuerySet` (`Sample.objects.published()`,
`Measurement.objects.published()`). Not a new default manager, for two reasons: (1) unlike
`Dataset.objects`, `Sample.objects`/`Measurement.objects` are read throughout the codebase — the
API viewsets, the admin, the demo — and are not safe to narrow by default without a wider audit
this feature does not own (FR-006: "nothing outside the listings specified below MUST read the
flag"); (2) a queryset method composes cleanly with the registry-generated filterset's `.qs`
without fighting a default-manager override, and is grep-discoverable as exactly what a collection
view calls. `Measurement.objects.published()` filters on `dataset__published`, its own dataset —
never `sample__dataset__published` (FR-012, D3).

## R2 — How to suppress a name and a link without hiding the row (FR-013, D3)

**Question**: a measurement's sample may belong to an unpublished dataset. The row stays; the
sample's name and the link to it must disappear.

**Finding**: `MeasurementTable.sample = tables.Column(linkify=True)` (`fairdm/contrib/collections/tables.py:128`)
renders the sample's `str()` linked to `get_absolute_url()`. `linkify` calls `get_absolute_url` on
the accessor's value; there is no built-in conditional form.

**Decision**: replace the column with a `render_sample(self, value)` method reading
`value.dataset.published` (already available without an extra query — see R3) and returning either
the linkified value (built manually via `django.utils.html.format_html` with `value.get_absolute_url()`)
or a plain placeholder string for an unpublished sample. No new field or annotation is needed
beyond the `select_related`/`prefetch_related` already used for `with_related()`.

## R3 — Keeping the query count flat (FR-020, SC-006)

**Question**: the publication check and the FR-013 suppression must not add a per-row query.

**Finding**: `MeasurementQuerySet.with_related()` already does `select_related("sample", "dataset")`
(`fairdm/core/measurement/managers.py`, ~line 68). `SampleQuerySet.with_related()` selects
`dataset`, `dataset__project`, `location`. Neither currently selects the *sample's* dataset from a
measurement queryset.

**Decision**: `Measurement.objects.published()` chains `.select_related("dataset", "sample__dataset")`
so `value.dataset.published` in R2's `render_sample` is a cache hit, not a query. `DataTableView`
calls `.published().with_related()` (or a combined method) rather than the bare default manager.
This is verified by an explicit `django.test.utils.CaptureQueriesContext` test per FR-020/SC-006 —
not inferred from code reading alone (Article I; `never-cite-a-count-i-did-not-read`).

## R4 — `search_fields` as a new `ModelConfiguration` attribute

**Question**: D4 requires a per-type declaration of searchable fields, defaulting to `["name"]`,
validated at import, backed by an index requirement.

**Finding**: `ModelConfiguration` has no such attribute (confirmed by reading `_OVERRIDABLE` at
`fairdm/registry/config.py:237-245` — it is not present, and passing it today raises `TypeError`).
The `COMPONENTS` table (`config.py:111-124`) generates six components (form/table/filterset/
serializer/resource/admin) each backed by a factory; search is not a generated *component* — it is
a plain list consumed directly by `mvp.views.list.SearchMixin.search_fields`, which the shell
already validates only at request time (an invalid ORM path raises `FieldError` from Django itself,
not a registration-time check).

**Decision**: add `search_fields: list[str] | None = None` as a **plain declarable attribute**
(not a `COMPONENTS` entry — it produces no generated class, so it does not fit that table's shape).
Add it to `_OVERRIDABLE`. Validate it in `__init__` alongside the existing `_validate_fields` pass,
reusing `FieldInspector.resolve_path` (already used for `fields`/`exclude`) so a bad path — including
a relation path — is refused at import with a message naming the type and the field (FR-026),
consistent with how a bad `fields` entry is already refused today (`config.py:319-344`). Add
`get_search_fields()` returning `self.search_fields or ["name"]` (FR-024). `DataTableView` sets
`self.search_fields = self.model_config.get_search_fields()` in `get_queryset()`/`setup()` before
calling `super()`, which is how `SearchMixin` (`mvp/views/list.py:57,65`) already expects to receive
per-view configuration — no shell change needed, per Article XIV.

## R5 — The index requirement (FR-027, SC-007)

**Question**: every field the framework searches *by default* needs a database index. How is that
enforced without indexing fields the framework does not touch?

**Finding**: `Sample.name` and `Measurement.name` are inherited from `BaseModel.name`
(`fairdm/core/abstract.py:31`), currently `CharField(max_length=300)` with no `db_index=True` and
no explicit index in either model's `Meta`. Django does not index `CharField` by default.

**Decision**: add `db_index=True` to `BaseModel.name` directly (it is the field every default
`search_fields` falls back to, per R4), via a migration on every concrete model inheriting it —
scoped to this feature's two apps (Sample, Measurement) since `Dataset`/`Project` names are not in
scope here (FR-027 binds only the fields *this feature's* listings search by default). Where a
`ModelConfiguration` declares `search_fields` explicitly, indexing those fields is the model
author's responsibility (FR-027's boundary, D4) — this feature does not walk declared
`search_fields` and force indexes onto arbitrary columns, only onto the one field it defaults to.
This is stated in the new docs page (FR-060).

## R6 — Building the listing's queryset and filterset together (FR-029–031)

**Question**: FR-031 requires the publication filter applied "before the publication rule is
relaxed in any way" — search and filtering must never widen past it.

**Finding**: `DataTableView` today (`views.py:12`) sets no `get_queryset()` at all, so
`MultipleObjectMixin.get_queryset()` reads `self.model._default_manager.all()` — the unfiltered
default manager — and `BaseFilterView.get()` builds the filterset directly from
`self.get_queryset()`. `FilterFactory`-generated filtersets (`fairdm/registry/factories.py:348-426`)
build a `Meta.fields` list straight off local model fields; they never receive a pre-filtered
queryset argument other than the one `django_filters.views.BaseFilterView` passes them.

**Decision**: `DataTableView.get_queryset()` is added, returning `self.model.objects.published()`
composed with `.with_related()` (R3). Because django-filter's `FilterSet(queryset=...)` filters
*on top of* whatever queryset it is given (`django_filters/filters.py` — a `ModelChoiceFilter`'s
own `queryset` for building choice lists is separate and must also be scoped, see R7), narrowing
this base queryset is sufficient for FR-031: nothing downstream can add rows back.

## R7 — Filter choice lists must not leak unpublished values (FR-030)

**Question**: `FilterFactory._get_smart_filters` (`factories.py:428-487`) gives a FK field a
`ModelChoiceFilter(queryset=related._default_manager.all())` — the related model's *unfiltered*
default manager, independent of the listing's own queryset.

**Finding**: confirmed by reading `factories.py:428-487` directly — the generated filter's choice
queryset is a fresh call to the related model's default manager, not derived from the table's rows.
For a Sample/Measurement FK field pointing at, e.g., another sample or a controlled vocabulary
concept, this could surface a value that exists only on an unpublished record.

**Decision**: this is in scope for FR-030 only where the related model is Sample, Measurement, or
Dataset (the models this feature governs) — a vocabulary `Concept` choice list is not scoped by
publication, because concepts are shared reference data, not owned by one dataset. Where
`FilterFactory` builds a `ModelChoiceFilter` against `Sample`, `Measurement`, or `Dataset`, its
`queryset=` argument must be the published-only queryset (R1), not the bare default manager. This
is a targeted change inside `_get_smart_filters`, gated on `issubclass(related_model, (Sample,
Measurement)) or related_model is Dataset`, not a blanket rewrite of the factory's behaviour for
every FK in the framework (Article II — narrowest change satisfying the requirement).

## R8 — Navigation entries with no per-type wiring, and no boot failure on a missing node (D-equivalent to the collections app's own bug)

**Question**: FR-039/FR-041 require every registered type to appear, and the navigation to render
even if collections is not installed. Section D3 of the exploration found `CollectionsConfig.
populate_data_collection_menu()` dereferences `AppMenu.get("Samples")` unguarded — a hard
`AttributeError` in `ready()` if that node is ever absent or renamed.

**Finding**: `fairdm/contrib/plugins/registration.py:148-157` already solves the identical problem
for per-model plugin menus with a get-or-create:
```python
menu = root.get(menu_name)
if menu is None:
    menu = Menu(menu_name)
    root.append(menu)
```

**Decision**: apply the same get-or-create pattern in the rebuilt `populate_data_collection_menu()`
(or its `menus.py` replacement) — `AppMenu.get("Samples") or MenuCollapse(name=_("Samples"), parent=AppMenu)`
— rather than assuming the node declared in `fairdm/menus/menus.py` always exists. This does not
change `fairdm/menus/menus.py` itself; it makes the *consumer* defensive, consistent with how the
plugin system already treats the same class of failure. FR-040 (no empty heading) is handled by
each `MenuCollapse`'s existing empty-children behaviour once populated conditionally — only append
the collapse's own `MenuItem` children when `registry.samples`/`registry.measurements` is non-empty,
and skip creating the collapse-level node at all when there is nothing to put in it, so an empty
kind produces no heading rather than a heading with zero children (closing the D2/D3 gap found
during exploration, where an empty `MenuCollapse` renders visible with no content).

## R9 — The switcher control (FR-042–047)

**Question**: every listing needs a control offering every other registered type's listing,
grouped by kind, current one marked, opened unnarrowed (D6).

**Finding**: `DataTableView.get_context_data()` already builds an equivalent list by hand
(`views.py:44-62`) — `available_collections`, a list of dicts with `name`, `verbose_name`, `url`,
`slug`, `is_current`, reversing `f"{slug}-collection"` inside a `try/except NoReverseMatch`. This is
the right shape, built the wrong way (string concatenation of a URL name that is about to change,
FR-049) and not grouped by kind (FR-043).

**Decision**: keep the hand-built list approach — it is simpler than forcing this into flex_menu
(Article II; a per-request, non-global, two-group list has no need for a tree with checks,
`extra_context`, and process-global caching). Rebuild it as two lists (`sample_listings`,
`measurement_listings`), each entry `{name, url, is_current}`, built from `registry.samples`
/`registry.measurements` and `reverse(f"{config.get_slug()}-list")` (new name, R-equivalent to D7),
guarded by the same `NoReverseMatch` pattern already in place. FR-047 (no journey to nowhere) is
satisfied by only rendering the control's markup when the combined list has more than one entry —
a template-level check, not a view-level one, keeping the view logic identical regardless of
portal size.

## R10 — URL naming migration (D7, FR-049)

**Question**: move from `<slug>-collection` to `<name>-list`, matching `project-list`/`dataset-list`.

**Finding**: `DataTableView.get_urls()` (`views.py:110-148`) generates both the path and the name in
one place; nothing else in the codebase constructs a `-collection` URL name by string formatting
except the view's own `get_context_data` (R9) and `CollectionRedirectView` (deleted, US-6). Grep
confirms no template or test references the old name.

**Decision**: change the `name=f"{slug}-collection"` literals in `get_urls()` to
`name=f"{slug}-list"`. Because two different registered types could theoretically produce the same
slug only if they share a `model_name`, which Django's app registry already forbids across apps
sharing a label — FR-050's "refused at import" duplicate-address check is implemented as an explicit
check in `get_urls()` (or in registry validation) raising `ImproperlyConfigured` naming both models
if two slugs collide, since Django's own `path()` would otherwise silently let the second shadow the
first.

## R11 — Empty-state rendering actually works (FR-018, gap found in exploration)

**Question**: exploration found the table-view empty state never renders today —
`table.empty_text` defaults to `None` and nothing sets it, `table.context.create_url` and
`table.context.page.icon` are read by the shared partial but never published by
`MVPTableViewMixin`/`PageMixin`.

**Finding**: confirmed at `mvp/templates/django_tables2/bootstrap5-mvp.html:61-76` and
`PageMixin.get_page_context()` (`mvp/views/base.py:188-193`, which emits no `icon` key at all).

**Decision**: the generated table class (or `get_table_kwargs()`) must set `Meta.empty_text` (or
pass `empty_text=` at construction) to the type's own message, e.g. built from
`model_config.get_verbose_name_plural()` (FR-018, FR-021 — must be translatable, so built with
`gettext_lazy` and `%(type)s` interpolation, not string formatting on a lazy proxy at class-definition
time). `create_url` is not needed for a read-only listing with no create action, so that half of the
partial's gap is irrelevant here; `page.icon` absence just falls back to the partial's own
`"search"` default, which is acceptable and needs no `PageMixin` change (Article II — fix only what
this feature's acceptance criteria require).

## R12 — What survives from the existing app (US-6 scope, FR-056–058)

**Finding**, itemised against the exploration report:

| Item | Disposition |
|---|---|
| `CollectionRedirectView` | delete — unrouted, addresses don't match real routes (FR-056) |
| `DataTablePlugin` (`plugins.py`) | delete — unregistered, wrong MRO for `get_urls` (FR-057) |
| `templates/collections/table.html` | delete — unused, `DJANGO_TABLES2_TEMPLATE` never points at it (FR-058) |
| `CollectionsOverview`, `SamplesOverview`, `MeasurementsOverview` + their templates | not named by any FR or story; superseded by the per-type listing + switcher (US-5). Kept only if a route to them is still needed for FR-041's "navigation renders" story — otherwise delete as unreached, since no story asks for a portal-wide overview page and D7 gives listings their own addresses without one |
| `templatetags/collection_tags.py` | delete — duplicates `tables.py`'s `field_map`/row-class logic, used only by the deleted `table.html` |
| `export_formats`, `get_context_data`'s `export_choices` | delete — FR-052 |
| `README.md` | rewritten from scratch against the surviving code (FR-059) |
| `tables.py` (`BaseTable`, `SampleTable`, `MeasurementTable`) | kept — depended on by `TableFactory` (`factories.py:322-336`) outside this app; modified per R2 |

## R13 — `Dataset.published` field shape (FR-001–007)

**Finding**: `visibility` (`fairdm/core/dataset/models.py:239-245`) is the closest sibling field —
`IntegerField` with choices, because it has two named states with room to grow. `published` per
D2/FR-005 is a plain boolean with no states, no workflow, no transitions.

**Decision**: `models.BooleanField(_("published"), default=False, db_index=True, help_text=_("..."))`.
`db_index=True` because every listing's queryset filters on it directly (R1) — this is the field
FR-011 tests on every request, unlike a field indexed only for admin convenience. Added directly to
`Dataset`, not a mixin (FR-001 — "on `Dataset`"; no other model gets one). Admin: add to
`fieldsets` (`admin.py:180-219`, a new field near `visibility` at line 188 or its own section),
`list_display` and `list_filter` (FR-003, and D2's "admin and nothing else" is satisfied by adding
no form/view surface elsewhere).
