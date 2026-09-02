# Progress — FS-015, browsing a portal's samples and measurements by type

## Spec gate — approved 2026-09-01

Sam approved in session, with no amendments. Approved surface: `spec.md` and `decisions.md` at
`015-browsing-portal-samples`, epic #315, stories #316–321, draft pull request #322.

All four decisions put to him at the gate stand as written:

- A listing shows published data only, identically for every viewer.
- A record's own dataset decides its presence, and an unpublished referent loses its name as well
  as its link.
- Listing URL names move to the `<name>-list` convention, away from `<slug>-collection`.
- Retiring the dead code in `fairdm/contrib/collections` is US-6, not an implicit tidy.

The accepted consequence was stated at the gate and accepted: portals upgrading to this version see
empty listings until an administrator publishes a dataset.

## Stages

| Stage | State | Note |
|---|---|---|
| S0 INTAKE | done | Eight questions. The feature statement was confirmed verbatim on 2026-09-01. |
| S1 SPECIFY | done | `spec.md`: 6 stories, 60 requirements, 10 success criteria, 9 clarifications. `decisions.md`: D1–D8. FR-066 of `014-dataset-crud-views` annotated in place as superseded. |
| S2 SETUP | done | Epic #315, stories #316–321, draft PR #322. Branch `015-browsing-portal-samples`. |
| Spec gate | approved | 2026-09-01, in session, no amendments. |
| S3 PLAN | done | `plan.md`, `research.md` (13 items), `data-model.md`, `quickstart.md`, `tasks.md` (66 tasks across 6 stories). `feature-state.json` generated, all tasks `todo`. Baseline `tests/test_registry/` (243 tests) confirmed green before any change. |
| S3R DESIGN_REVIEW | next | |

## Where the boundaries were drawn

Three of the eight intake answers moved the boundary and are worth finding here rather than in the
clarification list:

- The feature owns `fairdm/contrib/collections` outright. Nothing in that app counts as delivered.
- It takes part of R17: each type declares the fields its search covers, the record's name is
  searched where nothing is declared, and every field searched by default is indexed. Ranking,
  typo tolerance and cross-type search stay with R17.
- The published flag is set in the Django admin and nowhere else, which supersedes FR-066 of
  `014-dataset-crud-views`. The recommendation at intake was a control on the dataset's own
  attributes page; it was declined, and D2 records why the more awkward placement is the right one
  until R22 designs the workflow.

## US-1 — Mark a dataset published

### 2026-09-02T09:07:32Z · Implementer US1 · T001

Did: confirmed the baseline. Verified: `poetry run pytest tests/test_registry/` — 243 passed.
Next: T002. Watch: nothing.

### 2026-09-02T09:07:32Z · Implementer US1 · T002

Did: added `TestDatasetPublished` to `tests/test_core/test_dataset/test_models.py` — a dataset
created without naming `published` reads back `False`, and so does a batch of three created the
same way, read through `Dataset.all_objects`. Verified: ran red first (`AttributeError: 'Dataset'
object has no attribute 'published'`), confirming it failed for the right reason. Next: T003.
Watch: nothing.

### 2026-09-02T09:07:32Z · Implementer US1 · T003

Did: added `Dataset.published` (`BooleanField`, default `False`, `db_index=True`, `verbose_name`
and `help_text` both `gettext_lazy`, help text verbatim from data-model.md) beside `visibility` in
`fairdm/core/dataset/models.py`. No `save()` override, no signal, no validation coupling to
`visibility`, per FR-005. Verified: `poetry run pytest tests/test_core/test_dataset/test_models.py::TestDatasetPublished`
— 2 passed. Next: T004. Watch: nothing.

### 2026-09-02T09:07:32Z · Implementer US1 · T004

Did: `poetry run python manage.py makemigrations dataset --name dataset_published` →
`fairdm/core/dataset/migrations/0012_dataset_published.py`, `AddField` only. Verified:
`poetry run python manage.py makemigrations --check --dry-run` reports no pending migration for
`dataset` (the identity/orbit drift it still reports is pre-existing and unrelated — confirmed by
running the same check against the base commit, before this story's model change, where it is
already present). Next: T006. Watch: the pre-existing `identity`/`orbit` migration drift, in
`concerns` below — out of this story's scope to fix.

### 2026-09-02T09:07:32Z · Implementer US1 · T006

Did: added `TestPublishedFieldNotExposed` to `tests/test_core/test_dataset/test_forms.py`,
asserting `published` is absent from both `DatasetForm.Meta.fields` and `DatasetCreateForm.Meta.fields`
and from each form's bound `fields`. Green on first run, as the acceptance criterion anticipated —
both forms already name their fields explicitly, so this is the standing guard against a later
change exposing it, not a red-first task. Verified:
`poetry run pytest tests/test_core/test_dataset/test_forms.py::TestPublishedFieldNotExposed` — 2
passed. Next: T014. Watch: nothing.

### 2026-09-02T09:07:32Z · Implementer US1 · T014

Did: added `TestDatasetAdminPublished` to `tests/test_core/test_dataset/test_admin.py` — `published`
is an editable form field and a list filter, and posting it `on` with `visibility` left `PRIVATE`
persists both independently. Verified: ran red first (`AssertionError: 'published' not in
{...base_fields...}`), confirming it failed for the right reason. Next: T005. Watch: nothing.

### 2026-09-02T09:07:32Z · Implementer US1 · T005

Did: added `published` to `DatasetAdmin.fieldsets` (Basic Information, beside `visibility`),
`list_display` and `list_filter` in `fairdm/core/dataset/admin.py`. Verified:
`poetry run pytest tests/test_core/test_dataset/test_admin.py` — 35 passed (T014's 3 plus the
existing 32, none of which changed). Next: T015. Watch: nothing.

### 2026-09-02T09:07:32Z · Implementer US1 · T015

Did: added `TestNonCollectionPagesIgnorePublished` to `tests/test_core/test_dataset/test_views.py` —
the dataset list, overview, update and delete pages each render identically whether `published` is
toggled `False`→`True` on the same record (toggled via `.update()`, not `.save()`, so `modified`'s
`auto_now` cannot confound the comparison). First run surfaced a real difference unrelated to
`published`: Django's CSRF middleware masks the token afresh on every response, so two otherwise
identical GETs to a page carrying a form never come back byte-identical. Both comparisons now blank
the `csrfmiddlewaretoken` value before comparing (see `decisions.md`). Verified:
`poetry run pytest tests/test_core/test_dataset/test_views.py::TestNonCollectionPagesIgnorePublished`
— 4 passed; `poetry run pytest tests/test_core/test_dataset/test_views.py` (full file) — 78 passed.
Next: none — US-1's tasks are complete. Watch: nothing.

### 2026-09-02T10:31:08Z · Implementer US2 · T007

Did: added `TestPublished` to `tests/test_core/test_sample/test_managers.py` (new file, mirroring
`managers.py`) and to `tests/test_core/test_measurement/test_managers.py` — a sample/measurement is
present in `.published()` iff its own dataset is published, and the measurement half proves the
"own dataset, never the sample's" rule in both directions (own dataset unpublished but sample's
published → absent; own dataset published but sample's unpublished → present). Verified: ran red
first (`AttributeError: ... object has no attribute 'published'`) on both files. Next: T008.
Watch: nothing.

### 2026-09-02T10:31:08Z · Implementer US2 · T008

Did: added `SampleQuerySet.published()` (`fairdm/core/sample/managers.py`) — a bare
`filter(dataset__published=True)`, no `select_related`. Verified:
`poetry run pytest tests/test_core/test_sample/test_managers.py` — 2 passed. Next: T009.
Watch: nothing.

### 2026-09-02T10:31:08Z · Implementer US2 · T009

Did: added `MeasurementQuerySet.published()` (`fairdm/core/measurement/managers.py`) — deliberately
`dataset__published`, never `sample__dataset__published`, no `select_related`. Verified:
`poetry run pytest tests/test_core/test_measurement/test_managers.py` — 5 passed (T007's full
scope, both files). Next: T016. Watch: nothing.

### 2026-09-02T10:31:08Z · Implementer US2 · T016/T072

Did: created `tests/test_contrib/test_collections/` (`__init__.py`, `conftest.py`, `test_urls.py`)
— every registered type's listing returns 200 and reverses by `f"{slug}-list"` explicitly
(`TestListingAddresses`), and two registrations resolving to the same address raise
`ImproperlyConfigured` naming both models (`TestDuplicateListingAddress`, slugs forced to collide
via `monkeypatch` on the registered configs' `get_slug`). Verified: ran red first — `NoReverseMatch`
on `rocksample-list` (the name is still `-collection`) and "DID NOT RAISE" for the duplicate case.
Next: T017. Watch: nothing.

### 2026-09-02T10:31:08Z · Implementer US2 · T017

Did: added `TestPublicationFiltering` to `test_views.py` — a listing shows only published records,
identically for a signed-out client, the record's owner (`change_dataset` permission holder), a
contributor (`add_contributor`, no permission grant) and portal staff (`is_staff=True`). Added the
supporting fixtures (`published_dataset`, `unpublished_dataset`, `published_sample`,
`unpublished_sample`, `dataset_owner`, `dataset_contributor`, `staff_user`) to `conftest.py`.
Verified: ran red first (`NoReverseMatch`, same underlying cause as T016 — the URL doesn't exist by
this name yet). Next: T018. Watch: nothing.

### 2026-09-02T10:31:08Z · Implementer US2 · T018

Did: added `TestColumnsPerType` — `RockSample` (fields incl. `rock_type`) and `SoilSample`
(`table_fields` incl. `soil_type`) each show the other's column and not their own. Verified: red
first (`NoReverseMatch`). Next: T019. Watch: nothing.

### 2026-09-02T10:31:08Z · Implementer US2 · T019

Did: added `TestDefaultColumns` — `CustomSample` (declares no `fields` at all) still renders 200
with a non-empty column set. Verified: red first (`NoReverseMatch`). Next: T020. Watch: nothing.

### 2026-09-02T10:31:08Z · Implementer US2 · T020

Did: added `TestPaging` — 25 published records, page 1 and page 2 return disjoint slices and both
report the expected `page_obj.number`. Verified: red first (`NoReverseMatch`). Next: T021.
Watch: nothing.

### 2026-09-02T10:31:08Z · Implementer US2 · T021/T070

Did: created `test_tables.py` — `TestSampleColumn`: a measurement whose sample's dataset is
unpublished shows the measurement's own name but neither the sample's name nor an href to it
(scoped to the row's own `sample` cell via `table.rows` / `get_cell`, not a full-page substring
check — a "sample" filter widget elsewhere on the page legitimately lists every sample by name,
published or not, which a page-wide check first tripped on). `TestDatasetColumn`: a dataset that is
published while private still shows its records, with no href to the dataset's own page. Verified:
red first (`NoReverseMatch`) for both. Next: T022. Watch: nothing.

### 2026-09-02T10:31:08Z · Implementer US2 · T022

Did: added `TestEmptyState` to `test_views.py` — a type with no published records shows this
feature's own heading and message (both present, both rendered), and not the shell's "Click the
button below to get started". Verified: red first (`NoReverseMatch`). Next: T023. Watch: nothing.

### 2026-09-02T10:31:08Z · Implementer US2 · T023

Did: added `TestRowLinksToRecord` — a sample listing row and a measurement listing row each carry
an href to the record's own `get_absolute_url()`. Verified: red first (`NoReverseMatch` x2).
Next: T024. Watch: nothing.

### 2026-09-02T10:31:08Z · Implementer US2 · T024

Did: added `TestQueryCount` — query count for one row equals query count for a full page, for both
the sample and the measurement listing. First pass used `CaptureQueriesContext` around two
`client.get()` calls; both failed with a real-looking but spurious per-row scaling (563→640,
758→1147) traced to `orbit.watchers.record_signal` hooking `template_rendered` and `repr()`-ing the
render context on every node rendered, which re-evaluates any queryset in scope — see decisions.md
D17. Rewrote to build `DataTableView` via `RequestFactory` and call `table.as_html(request)`
directly, excluding `orbit_orbitentry` from the count. Verified: red first (`NoReverseMatch` x2,
before rewriting for the query-count issue); after the rewrite, a bare
`RockSample.objects.published().with_related()[:20]` confirmed flat (2 queries, 1 row vs 20) before
trusting the table-level measurement. Next: T025. Watch: nothing.

### 2026-09-02T10:31:08Z · Implementer US2 · T025

Did: `DataTableView.get_queryset()` (`fairdm/contrib/collections/views.py`) — narrows
`super().get_queryset()` through `.published().with_related()`, then chains
`select_related("sample__dataset", "sample__location")` when `self.model in registry.measurements`.
Verified: `poetry run ruff check fairdm/contrib/collections/views.py` clean; full behavioural
verification deferred to T029 (URL rename lands first) per the brief's task order. Next: T026.
Watch: nothing.

### 2026-09-02T10:31:08Z · Implementer US2 · T026

Did: `MeasurementTable.render_sample` (`fairdm/contrib/collections/tables.py`) rewritten — `sample`
column loses `linkify=True`; the new body returns a `format_html` anchor to `value.get_absolute_url()`
when `value.dataset.published`, else `_("Unpublished")`. Removed `__init__`'s now-redundant
`prefetch_related("sample")` (double-fetch once T025 selects it) — and the whole `__init__` override
with it, since nothing else was left in it. Verified: ruff clean; behavioural verification deferred
with T025. Next: T071. Watch: nothing.

### 2026-09-02T10:31:08Z · Implementer US2 · T071

Did: `BaseTable.render_dataset` — loses `linkify=True`; new body returns a `format_html` anchor
around the dataset icon when `value.visibility != Visibility.PRIVATE`, else the bare icon. Verified:
ruff clean; behavioural verification deferred with T025. Next: T073. Watch: nothing.

### 2026-09-02T10:31:08Z · Implementer US2 · T073

Did: added `MeasurementTable.name = tables.Column(linkify=True, verbose_name=_("Name"))` — the
first column declared, mirroring `SampleTable.name`'s purpose (a self-link) with an explicitly
authored `gettext_lazy` header rather than relying on inheriting the model field's own verbose_name.
Verified: ruff clean; behavioural verification deferred with T025. Next: T027. Watch: nothing.

### 2026-09-02T10:31:08Z · Implementer US2 · T027

Did: `DataTableView.get_table_kwargs()` now adds `empty_text` (set to
`self.get_empty_state_heading()`, enabling the shell's empty-state block); added
`get_empty_state_heading()`/`get_empty_state_message()` overrides, both built per-instance from
`self.model_config.get_verbose_name_plural()`. `get_empty_state_message()` overrides the hook
outright rather than the attribute — the base hook only returns it when `show_action("create")` is
true, which this read-only listing never sets — see decisions.md D16. Verified: ruff clean;
behavioural verification (T022) deferred with T025. Next: T028. Watch: nothing.

### 2026-09-02T10:31:08Z · Implementer US2 · T028

Did: renamed the two `path(..., name=f"{slug}-collection")` calls in `get_urls()` to
`f"{slug}-list"`, and the one in-scope internal `reverse(f"{slug}-collection")` call in
`get_context_data()` (the switcher list) to match — the only two `-collection` reverse call sites
inside this story's scope. `apps.py`'s menu wiring and `abstract.py`'s unused `get_collection_url()`
also reference the old name but are both outside this story's file scope (menu wiring is a later
story's deliverable per plan.md; `get_collection_url()` is dead code, called nowhere) — left alone;
`apps.py`'s menu entries degrade to no-link (caught by `flex_menu`'s own `NoReverseMatch` handling,
logged not raised) until that story rewires them. Verified:
`poetry run pytest tests/test_contrib/test_collections/test_urls.py::TestListingAddresses` — now
green (T016 fully passes). Next: T029. Watch: apps.py's stale menu `view_name`s, noted above —
Forge's to pick up when that story runs, not a defect introduced here.

### 2026-09-02T10:31:08Z · Implementer US2 · T029

Did: `get_urls()` refactored to a shared `add_listing_url(prefix, model_class)` closure tracking
`seen_addresses` (keyed by the full `"prefix/slug/"` path, not slug alone — a sample and a
measurement type sharing a slug do not collide, since they sit under different prefixes); raises
`ImproperlyConfigured` naming both model classes on a repeat. Verified:
`poetry run pytest tests/test_contrib/test_collections/test_urls.py` — 2 passed (both T016 and
T072 now green). Next: full-story re-verification. Watch: nothing.

### 2026-09-02T10:35:00Z · Implementer US2 · full-story re-verification

Did: ran `tests/test_contrib/test_collections/` (16 tests, all new) and
`tests/test_core/test_sample/ tests/test_core/test_measurement/` (the two managers files T007-T009
touch) together. Verified: 16 passed in the new package; 512 passed, 7 skipped (pre-existing,
unrelated) across the three directories combined. Recorded decisions.md D16 (empty-state hook
override) and D17 (query-count test methodology). Next: T027's docs check — nothing under `docs/`
describes the `-collection` URL name, the empty-state copy, or anything else this story touched
(searched for `-collection` and `DataTableView`/`get_urls` outside `docs/_build`; the two source
hits are unrelated vocabulary). Watch: the full repo verify command, not yet run.

### 2026-09-02T14:36:00Z · Implementer US3 · T012

Did: `TestSearchFieldsValidation` in `tests/test_registry/test_config.py` - a path that does not
resolve, and a `DecimalField`/`BooleanField`/`DateField` parametrised over `search_fields`, both
raising `FieldValidationError`. Verified: `poetry run pytest
tests/test_registry/test_config.py::TestSearchFieldsValidation` - red (4 failed, `search_fields`
not yet an accepted keyword). Next: T013. Watch: nothing.

### 2026-09-02T14:36:00Z · Implementer US3 · T013

Did: `ModelConfiguration.search_fields` attribute, `_OVERRIDABLE` entry, `_validate_search_fields()`
(two passes - `_validate_field_path` then a positive `isinstance(field, (CharField, TextField))`
check on the resolved final field, matching `FilterFactory._get_search_fields`'s existing line per
D12), and `get_search_fields()` returning `self.search_fields or ["name"]`. Verified: T012's class -
4 passed; `tests/test_registry/test_config.py` - 67 passed; `pre-commit run` (ruff, mypy) clean.
Next: T067. Watch: mypy needed `model: Any` inside the path-walk loop, matching
`FieldInspector.resolve_path`'s own typing - `type[Model] | None` from `related_model` otherwise
conflicts with the first assignment's inferred `type[Model]`.

### 2026-09-02T14:36:00Z · Implementer US3 · T067

Did: `TestPublishedQuerySet` in `tests/test_core/test_dataset/test_models.py` - one published
private, one published public, one unpublished dataset; asserts `Dataset.all_objects.published()`
returns the first two, not the third. Verified: red (`AttributeError:
'ManagerFromDatasetQuerySet' object has no attribute 'published'`). Next: T068. Watch: nothing.

### 2026-09-02T14:36:00Z · Implementer US3 · T068

Did: `DatasetQuerySet.published()` - `self.filter(published=True)`. Verified: T067's test green;
`tests/test_core/test_dataset/` - 373 passed; pre-commit clean. Next: T010. Watch: nothing.

### 2026-09-02T14:36:00Z · Implementer US3 · T010

Did: `TestNameIndex` in `tests/test_core/test_abstract.py` - introspects `Sample._meta.db_table`
and `Measurement._meta.db_table` via `connection.introspection.get_constraints` for an index or
unique constraint on exactly `["name"]`. Verified: red (both tables report no such constraint,
under `--no-migrations` so the test DB reflects the model as it stands, not a migration file).
Next: T011. Watch: nothing.

### 2026-09-02T14:36:00Z · Implementer US3 · T011

Did: `db_index=True` on `BaseModel.name`. `makemigrations dataset measurement project sample`
(scoped to the four apps the abstract field reaches - not `identity`/`orbit`, whose own pending
migrations are unrelated drift, left alone) - four `AlterField` migrations, each touching only
`name`. Verified: T010's class - 2 passed; `makemigrations --check` on the four apps - clean;
`tests/test_core/test_sample/ test_measurement/ test_project/` - 760 passed, 7 skipped
(pre-existing); pre-commit clean. Next: T031. Watch: nothing.

### 2026-09-02T14:36:00Z · Implementer US3 · T031-T038

Did: wrote every US3 test task in brief order before any implementation, per the design review's
correction (T032 red before T030, not reversed):
- T031 `TestSearch` (`test_views.py`): no `search_fields` declared - a word from `name` matches,
  an unrelated record does not (`WaterSample`, untouched by T030 - stays on the default).
- T032 same class: a word held only by a declared field matches, one held only by an undeclared
  field does not (`RockSample`, whose `search_fields` T030 will set to `["rock_type"]`).
- T033 same class: a search matching nothing renders this feature's own empty state.
- T034 same class: a search matching an unpublished record's field returns nothing.
- T035 `TestFilters` (`test_views.py`): a char filter and two range filters (`Decimal`, `Integer`)
  each narrow to the matching record and return 200.
- T036 `TestPublishedChoiceLists` (`test_factories.py`): the sample, dataset and measurement
  branches of a generated `ModelChoiceFilter`'s queryset each exclude an unpublished record, and
  the dataset branch includes one published while private. The sample/dataset cases use
  `ExampleMeasurement` with an explicit `fields=["name", "sample"|"dataset"]` passed straight to
  `FilterFactory` - passing the name through `_get_smart_filters` rather than leaving it to
  `MeasurementFilterMixin`'s own dynamically-set "sample"/"dataset" filters, which T040 does not
  touch. The measurement case has no real registered FK-to-Measurement field anywhere in the
  schema, so it declares one inline (`MeasurementReferrer`, `app_label="test_app"`, cleaned up by
  the directory's autouse fixture) - the same throwaway-model pattern `test_config.py` already
  uses.
- T037 `TestOrdering` (`test_tables.py`): sorting a column both directions reorders rows (already
  green - generic column sorting predates this story); the unsorted-order test forces every row to
  one `added` timestamp (the opposite of `TestPaging`'s staggering, on purpose - ties are exactly
  what a missing tie-break exposes) and additionally pins `table.order_by` containing `id`
  directly, since the page-comparison alone can hold by coincidence of how Postgres happens to
  return tied rows today.
- T038 extends `TestNameIndex`: for every currently-registered demo type with no `search_fields`
  of its own, `get_search_fields()` returns exactly `["name"]`, plus the two index assertions
  T010 already has.

Verified, each red for its own reason except where noted: T031 both records returned (search not
wired); T032 both filters return every record; T033 the record still renders, no empty state;
T035 all three green immediately (generic filtering predates this story) - probed by returning
`None` from `get_filterset_class()`, confirmed all three then raise `TypeError`; T036 all three red
(`_default_manager.all()`/`Dataset.objects` is what ships today); T037's column-sort case green
immediately, its ordering case red on the new `table.order_by` assertion only (`None`) - the
page-disjointness assertions already passed even with ties forced, so that half was probed by
temporarily removing `.published()` from `get_queryset()` in an unrelated check, not this one;
T034 and T038 both green immediately - T034 probed by temporarily dropping `.published()` from
`DataTableView.get_queryset()` (then failed as expected, confirming the guard is real); T038
probed by temporarily returning `["wrong_field"]` from `get_search_fields()` (then failed as
expected). Next: T030. Watch: three genuinely red suites at this point -
`test_views.py::TestSearch` (partial), `test_factories.py::TestPublishedChoiceLists` (all three),
`test_tables.py::TestOrdering` (one assertion) - all expected, closed by T030/T039/T040/T041 below.

### 2026-09-02T14:36:00Z · Implementer US3 · T030

Did: `search_fields` on three `fairdm_demo/config.py` registrations - `RockSampleConfig` (`["rock_type"]`,
narrower than the default), `SoilSampleConfig` (`["name", "soil_type"]`, naming the default
explicitly alongside an addition), `ExampleMeasurementConfig` (`["char_field"]`). Verified: import
succeeds (validation passes for all three field types, all `CharField`); `tests/test_registry/
tests/test_contrib/test_collections/ fairdm_demo/tests/` - only the pre-existing, unrelated
`fairdm_demo/tests/` failures (admin change views, `is_claimed`) plus the still-open T035/T036/T037
reds; confirmed those three pre-existing failures reproduce identically with this commit's change
stashed out. Next: T039. Watch: nothing.

### 2026-09-02T14:36:00Z · Implementer US3 · T039

Did: `DataTableView.setup()` override - `self.search_fields = self.model_config.get_search_fields()`
after `super().setup()`, before dispatch (and therefore before `SearchMixin.get_queryset()` runs).
Verified: `TestSearch` - 5 passed (T031-T034 all green now); `tests/test_contrib/test_collections/`
- 25 passed, 1 failed (T037's still-open `order_by` assertion, expected); pre-commit clean.
Next: T040. Watch: nothing.

### 2026-09-02T14:36:00Z · Implementer US3 · T040

Did: `FilterFactory._get_smart_filters`'s `ForeignKey` branch now calls a new
`_published_related_queryset(related_model)` helper - `Dataset.all_objects.published()` for a
Dataset relation (never `Dataset.objects`, which would already exclude the published-but-private
case before publication is even considered), `related_model._default_manager.published()` for
Sample/Measurement, unscoped `_default_manager.all()` otherwise. Verified: `TestPublishedChoiceLists`
- 3 passed; `tests/test_registry/test_factories.py` - 56 passed; `tests/test_registry/
tests/test_contrib/test_collections/ fairdm_demo/tests/` - only the same pre-existing failures plus
T037's still-open assertion; pre-commit clean. Next: T041. Watch: nothing.

### 2026-09-02T14:36:00Z · Implementer US3 · T041

Did: `Meta.order_by = ("added", "id")` on `SampleTable`, `Meta.order_by = ("-modified", "id")` on
`MeasurementTable` - `id` is always a column (declared on `BaseTable`), so it survives the
column-membership check in every generated table regardless of what fields a type declares.
Verified: `TestOrdering` - 2 passed; `tests/test_contrib/test_collections/` - 26 passed; pre-commit
clean. Next: full-story re-verification. Watch: nothing.
