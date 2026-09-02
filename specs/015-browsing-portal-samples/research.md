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

**Finding**: the column already exists in both halves, and neither is what a first reading suggests.
`MeasurementTable.sample = tables.Column(linkify=True)` (`fairdm/contrib/collections/tables.py:128`),
and `render_sample` is **already defined** at `tables.py:145-147`:

```python
def render_sample(self, value):
    sample_type = value.get_real_instance_class()
    return sample_type._meta.verbose_name
```

So the cell today shows the sample *type's* verbose name rather than the sample's own name, wrapped
in an anchor. A render method cannot suppress that anchor: django-tables2 composes the link *around*
whatever the method returns — `.venv/lib/python3.13/site-packages/django_tables2/rows.py:197`,
`return bound_column.link(content, **render_kwargs) if bound_column.link else content` — and
`django_tables2/columns/base.py`'s `LinkTransform.compose_url` builds the href from the record via
`get_absolute_url()`, never from the returned string. Returning a placeholder would remove the name
and leave `<a href="/samples/<uuid>/">` in the row.

**Decision**: drop `linkify=True` from the column declaration and **replace the body of the existing
`render_sample`** — not add a second method, and not preserve the verbose-name output. The new body
reads `value.dataset.published` (a cache hit, not a query — see R3) and returns either an anchor
built with `django.utils.html.format_html` around `value.get_absolute_url()`, or a `gettext_lazy`
placeholder string when the sample's dataset is unpublished. The FR-013 test asserts that the
response body carries no href to the unpublished sample's absolute URL, not merely that its name is
absent. No new field or annotation is needed. `BaseTable.dataset` is declared `linkify=True` in the
same way and needs the same treatment — see R14.

## R3 — Keeping the query count flat (FR-020, SC-006)

**Question**: the publication check and the FR-013 suppression must not add a per-row query.

**Finding**: `MeasurementQuerySet.with_related()` already does `select_related("sample", "dataset")`
(`fairdm/core/measurement/managers.py`, ~line 68). `SampleQuerySet.with_related()` selects
`dataset`, `dataset__project`, `location`. Neither currently selects the *sample's* dataset from a
measurement queryset. Nor the sample's *location*, and that matters more than it first appears:
`MeasurementTable` declares three columns reading through it — `latitude` (accessor
`sample.location.x`), `longitude` (`sample.location.y`) and `location` (`sample.location`,
`linkify=True`) — against a `ForeignKey` at `fairdm/core/sample/models.py:111`. Nothing in the
plan loads it, so a 20-row page issues 20 extra queries and SC-006's flat-query assertion fails on
the measurement listing.

**Decision**: the eager loading lives in `DataTableView.get_queryset()`, which chains
`.published().with_related()` onto `super().get_queryset()` — never off the bare default manager,
see R6 for why that difference is not cosmetic — and then adds
`.select_related("sample__dataset", "sample__location")` for a measurement type, so both
`value.dataset.published` in R2's `render_sample` and the three location-backed columns are cache
hits rather than queries.

**Not in `with_related()`, and not in `published()`.** `with_related()`'s docstring
(`fairdm/core/measurement/managers.py:40-53`) says it deliberately does not prefetch deep nested
relationships — "Views requiring deep nested data should chain additional select_related calls" —
so widening it would break a documented contract for every other caller to serve one listing.
`published()` stays a bare filter because it is also called to scope generated filter choice lists
(R7), where these joins fetch columns nothing reads. The view is the only place that knows it is
about to render those three columns, so it is the place that asks for them.
`MeasurementTable.__init__`'s `data.prefetch_related("sample")` becomes redundant
once the view selects the sample, and currently double-fetches it — remove it in the same task that
changes the queryset. This is verified by an explicit `django.test.utils.CaptureQueriesContext` test
per FR-020/SC-006, covering **the measurement listing as well as the sample listing** — not inferred
from code reading alone (Article I; `never-cite-a-count-i-did-not-read`).

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
consistent with how a bad `fields` entry is already refused today (`config.py:319-344`).

`resolve_path` alone is not enough for FR-026. It checks that each segment names a field and that
intermediate segments expose a `related_model` (`fairdm/utils/inspection.py:166-190`), with no type
check — so a numeric, boolean, date or geometry field resolves cleanly and then raises at
request time, because `SearchMixin._apply_search` builds `Q(**{f"{field}__icontains": word})` for
every declared field. A field the framework cannot search must be refused at import, not at the
first search.

The second pass is a **positive test that the resolved final field is a text field** —
`isinstance(field, (models.CharField, models.TextField))` — raising `FieldValidationError` naming
the type and the field. The obvious alternative, asking whether the field supports the lookup, does
not work: Django registers `IContains` on `Field` itself, so `get_lookup("icontains")` returns a
lookup class for a `FloatField`, `DecimalField`, `BooleanField` and `DateField` alike (verified in
this project's environment against all four). A check written that way would reject nothing and
FR-026's second failure mode would be unenforceable. `FilterFactory._get_search_fields`
(`fairdm/registry/factories.py:648-656`) already decides which fields are searchable by exactly
this isinstance test, so reusing it keeps one answer to that question in the codebase rather than
two. Add
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
`search_fields` falls back to, per R4). **`name` is declared once on the abstract base, so this
indexes every concrete model that inherits it — `Sample` and `Measurement`, and also `Project` and
`Dataset`.** That reach is intended and recorded here rather than discovered at
`makemigrations --check`: `Project` and `Dataset` already have their own name-searched listings
(`ProjectListView.search_fields`, `DatasetListView.search_fields`), so indexing their name column
serves the same query the index exists for, and the alternative — moving `db_index=True` off the
base onto two concrete declarations — would duplicate the same decision in two places and leave the
other two listings searching an unindexed column. Article IX is satisfied by naming the four
migrations this forces (sample, measurement, project, dataset) as deliverables of the index task,
not by narrowing the change. Where a
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

**Decision**: `DataTableView.get_queryset()` is added, and it narrows **what `super()` returns** —
`super().get_queryset().published().with_related()` (R3) — never a queryset built from scratch off
the manager. That distinction is load-bearing precisely because the view declares no `get_queryset`
today: `super()` is the shell's own chain, and that chain is where `SearchMixin` and
`BaseFilterView` do their work. Writing `self.model.objects.published()` instead reads as
equivalent, silently drops both, and disables search (US-3) and filtering (US-4) while every
publication test still passes. Because django-filter's `FilterSet(queryset=...)` filters
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
plugin system already treats the same class of failure.

**FR-040 needs more than conditional population.** The `Samples` and `Measurements` collapses are
declared unconditionally in `fairdm/menus/menus.py`'s `AppMenu.extend([...])`, at import, whether or
not `fairdm.contrib.collections` is installed, so get-or-create finds them already present and
"never create one" is not available as a remedy. And the menu library does not hide a childless
container: `.venv/lib/python3.13/site-packages/flex_menu/menu.py`'s `process()` evaluates
suppression only inside its `if children_to_process:` branch, so a node with zero children is never
considered for it and renders as a visible heading with nothing beneath it. A portal with no
registered sample types would show exactly the empty heading FR-040 forbids.

So each of the two nodes gets a **check** that returns false when its registry list is empty, set
from the collections app alongside the population. That is the menu library's own mechanism for a
conditionally-visible node, it needs no change to `fairdm/menus/menus.py`, and it holds whether the
node was found or created. The FR-040 test asserts against a registry with no types of that kind
rather than against the populated demo, where it would pass without exercising anything.

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

**Decision**: two hooks, not one, because in the resolved shell template `empty_text` only *gates*
the block — the words the reader actually sees come from somewhere else.
`.venv/lib/python3.13/site-packages/mvp/templates/django_tables2/bootstrap5-mvp.html:61-76` guards
the block with `{% if table.empty_text %}` and then renders `table.context.empty_state.heading` and
`table.context.empty_state.message`, published by `MVPListViewMixin` as
`empty_state_heading = _("There's nothing here yet")` and
`empty_state_message = _("You haven't added any records yet. Click the button below to get started.")`.
Setting only `empty_text` therefore turns the block on and shows the shell's authoring copy, which
is wrong for a public read-only listing and does not satisfy FR-018.

So: set `Meta.empty_text` (or pass `empty_text=` at construction) to enable the block, **and**
override `empty_state_heading` / `empty_state_message` on `DataTableView` with strings written for a
public listing, built from `model_config.get_verbose_name_plural()`. Both are translatable per
FR-021, so `gettext_lazy` with `%(type)s` interpolation, not string formatting on a lazy proxy at
class-definition time. The FR-018 test asserts the rendered words, not the presence of the block —
an assertion on the block alone passes while the reader is told to click a button that does not
exist. `create_url` is not needed for a read-only listing with no create action, so that half of the
partial's gap is irrelevant here; `page.icon` absence just falls back to the partial's own
`"search"` default, which is acceptable and needs no `PageMixin` change (Article II — fix only what
this feature's acceptance criteria require).

## R12 — What survives from the existing app (US-6 scope, FR-056–058)

**Finding**, itemised against the exploration report:

| Item | Disposition |
|---|---|
| `CollectionRedirectView` | delete — unrouted, addresses don't match real routes (FR-056) |
| `DataTablePlugin` (`plugins.py`) | delete — unregistered, wrong MRO for `get_urls` (FR-057) |
| `templates/collections/table.html` | delete — unused as a django-tables2 *table* template, `DJANGO_TABLES2_TEMPLATE` never points at it (FR-058) |
| `templates/collections/listing.html` | **NEW** — the page template `DataTableView` renders, extending the shell's `table_view.html` and adding the switcher block (below) |
| `CollectionsOverview`, `SamplesOverview`, `MeasurementsOverview` + their templates and routes | delete. Their URL names (`data-collections`, `samples-overview`, `measurements-overview`) are reversed only from `urls.py` and the three templates the same story removes; no other template, view or test in the repository reaches them. No FR or story asks for a portal-wide overview page, and D7 gives listings their own addresses without one, so FR-041's "navigation renders" story does not need a route to them |
| `templatetags/collection_tags.py` | delete — duplicates `tables.py`'s `field_map`/row-class logic, and its only loader is `table.html:2`, which goes with it. The new `listing.html` loads no custom tag library |
| `export_formats`, `get_context_data`'s `export_choices` | delete — FR-052 |
| `README.md` | rewritten from scratch against the surviving code (FR-059) |
| `tables.py` (`BaseTable`, `SampleTable`, `MeasurementTable`) | kept — depended on by `TableFactory` (`factories.py:322-336`) outside this app; modified per R2 and R14 |

**Why the app keeps a page template of its own.** Deleting `table.html` with nothing in its place
leaves `DataTableView` with no template it owns, and US-5's switcher then has nowhere to render.
`views.py` sets `template_name_suffix = "_table"`, which resolves to
`<app_label>/<model>_table.html` per *registering* app — a path a framework cannot provide for a
consumer's models — and `BaseTemplateNameMixin.get_template_names()`
(`.venv/lib/python3.13/site-packages/mvp/views/base.py`) appends `base_template_name` last, which
`mvp/integrations/django_tables/views.py:28-59` sets to the shell's own `table_view.html`. That
template belongs to the shell package and this feature cannot edit it.

So the app keeps exactly one template — `templates/collections/listing.html`, extending
`table_view.html` and overriding the block the switcher goes in — and `DataTableView` sets
`template_name` to it explicitly rather than relying on suffix resolution. It is created before the
switcher markup is written into it. This is one template replacing one template, not a new layer.

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

## R14 — The dataset column when a published dataset's metadata is private (FR-013, D3)

**Question**: publication and visibility are independent by design (D2), and `visibility` defaults
to `PRIVATE`, so the ordinary state of a freshly published dataset is published-and-private. Every
listing row carries a dataset column. What does it render when the dataset's own page will refuse
the visitor?

**Finding**: the rows are correct and the column is not. `DatasetManager.get_queryset()`
(`fairdm/core/dataset/models.py:182-183`) excludes `Visibility.PRIVATE`, but a listing filters on
`dataset__published=True` through a JOIN, which never passes through that manager — which is exactly
what the spec asks for: publication is independent of visibility and is the sole test for a record's
presence in a listing (US-1 Acceptance Scenario 5, and Key Entities: "It is the sole test for a
record's presence in a listing"). The column, though, is
`dataset = tables.Column(linkify=True, orderable=False, verbose_name=False)` with an existing
`render_dataset` returning `icon("dataset")` (`fairdm/contrib/collections/tables.py`). It shows no
name, so nothing is leaked there — but per R2, `linkify` wraps the icon in an anchor regardless of
what the render method returns, so every row emits the address of a page the visitor is refused.

**Decision**: the same defect R2 fixes on the sample column, one relation over, and settled the same
way rather than by changing which rows appear. D3's rule already reads "where a row would name or
link a record whose own dataset is not published, it shows neither the name nor the link"; the
dataset column extends it by one word — no link to a dataset that is not **readable**, meaning
`visibility` is `PRIVATE`. So `BaseTable` drops `linkify=True` from the dataset column and
`render_dataset` builds the anchor itself with `format_html` around `get_absolute_url()` when the
dataset is readable, returning the bare icon when it is not. The rows are untouched, so the approved
rule in FR-011/FR-012 stands exactly as Sam gated it. Recorded in `decisions.md` as an extension
of D3.

`visibility` is already loaded by the `select_related("dataset")` R3 specifies, so this costs no
query. The test is a published-but-private dataset: its records appear in the listing, and the
response carries no href to that dataset's page.
