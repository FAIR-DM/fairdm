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
