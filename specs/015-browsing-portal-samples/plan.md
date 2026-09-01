# Implementation Plan: Browsing a portal's samples and measurements by type

**Branch**: `015-browsing-portal-samples` | **Date**: 2026-09-01 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/015-browsing-portal-samples/spec.md`

## Summary

`fairdm/contrib/collections` is rewritten in place. A new `Dataset.published` boolean (FR-001–007)
gives every listing a single, uniform test for what it may show. `DataTableView` is rebuilt on the
registry's generated table and filterset classes, filtered through that flag by dataset-owning
queryset methods so the filter runs once per model rather than once per row. Search and filtering
are declared per type via a new `ModelConfiguration.search_fields` attribute (mirroring the shell's
own `SearchMixin.search_fields`), defaulting to `["name"]`. Navigation entries and the
cross-listing switcher are both built from `registry.samples` / `registry.measurements` at render
time, so a new registration needs no per-type wiring. The redirect view, the unreached plugin, the
unused template, the export machinery and the stale README are deleted as US-6.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: Django 5.1/5.2, django-tables2 3.0, django-filter 24.3, django-polymorphic,
django-flex-menus 0.4.3, django-mvp 0.19.3 (`MVPTableViewMixin`, `SearchMixin`, `FairDMTableView`)

**Storage**: PostgreSQL (existing `Dataset` table gains one migration-added column; no new tables)

**Testing**: pytest / pytest-django, `--reuse-db --no-migrations`, mirrored under `tests/test_contrib/test_collections/`

**Target Platform**: Django web application (server-rendered, PostgreSQL backend)

**Project Type**: Single Django project (framework package `fairdm/` + reference app `fairdm_demo/`)

**Performance Goals**: query count for a listing page is O(1) in row count (FR-020, SC-006) — no
per-row query for dataset publication state, sample/measurement linkage, or column rendering

**Constraints**: no view may declare `order_by` (`MVPTableViewMixin.__init_subclass__` raises
`ImproperlyConfigured`); the publication filter must be expressible as a queryset method so it
composes with the registry-generated filterset without touching per-request user state (D1 — the
page must stay cacheable in principle)

**Scale/Scope**: 8 registered demo types today (5 sample, 3 measurement); the mechanism must hold
for portals with dozens of registered types and no records at all

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Article | Check | Status |
|---|---|---|
| I — Test-First | Every new/changed route gets a smoke test asserting status code (FR-051); red-green-refactor per behaviour | PASS — planned into every task |
| II — Simplicity | No new app, no new abstraction layer; extends `ModelConfiguration` and rewrites the existing view in place | PASS |
| III — Anti-Abstraction | `search_fields` is one new attribute on an existing class, following the exact shape `COMPONENTS` already uses for the other six | PASS |
| IV — Integration-First | The published-flag contract (FR-001–007) and the queryset filtering contract are the integration points; both get direct tests before column/template polish | PASS |
| V — Security & data-safety | Closes the standing leak (unfiltered `DataTableView` queryset serving private-dataset records) rather than adding a new one; publication check happens at queryset level, not template level | PASS — this is the feature's stated risk (decisions.md, "Risks") |
| VI — Documentation | README rewritten (FR-059), new `docs/portal-development/` page for `search_fields` and listing generation (FR-060), both in this PR | PASS |
| VII — Dependency discipline | No new dependency; reuses django-tables2/django-filter/flex_menu already in the shell | PASS |
| VIII — I18n | Every label (column headers via `verbose_name`, filter labels, empty state, switcher) MUST use `gettext_lazy`/`{% trans %}` (FR-021) | PASS — planned into UI tasks |
| IX — Data-model conventions | `published` field needs `verbose_name` + `help_text`; `db_index` decision recorded (Data Model, below); migration squashed at convergence | PASS |
| X — Test structure | `tests/test_contrib/test_collections/` mirrors `fairdm/contrib/collections/`, one factory reused (`DatasetFactory`), grouped `Test<Subject>` classes | PASS |
| XI — Cohesion | Queryset methods live on `DatasetQuerySet`/`SampleQuerySet`/`MeasurementQuerySet`, not module functions | PASS |
| XIV — Configuration over plumbing | `search_fields` is declarative on `ModelConfiguration`; a type registering nothing still works (FR-015) | PASS — this is the design's spine |
| XVIII — Living demo | `fairdm_demo/config.py` registrations gain `search_fields` examples; demo exercises the new listings | PASS |

No violations. Complexity Tracking is not filled.

## Project Structure

### Documentation (this feature)

```text
specs/015-browsing-portal-samples/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md         # Phase 1 output
├── quickstart.md         # Phase 1 output
└── tasks.md              # Phase 2 output (not created by /plan)
```

### Source Code (repository root)

```text
fairdm/
├── core/dataset/
│   ├── models.py                    # + Dataset.published field
│   ├── admin.py                     # + published in fieldsets, list_display, list_filter
│   └── migrations/0012_*.py         # new migration
├── core/sample/managers.py          # + SampleQuerySet.published()
├── core/measurement/managers.py     # + MeasurementQuerySet.published()
├── registry/
│   └── config.py                    # + ModelConfiguration.search_fields (COMPONENTS-adjacent, not a component)
├── contrib/collections/
│   ├── apps.py                      # menu population, adjusted for get-or-create Samples/Measurements nodes
│   ├── urls.py                      # url names -> `<slug>-list`
│   ├── views.py                     # DataTableView rebuilt; CollectionRedirectView, plugins-based views trimmed to what US-1..5 need
│   ├── tables.py                    # unchanged base tables; any dead render helpers removed
│   ├── menus.py                     # NEW — switcher control construction, if not folded into views.py context
│   ├── plugins.py                   # DELETED (US-6, FR-057)
│   ├── templates/collections/
│   │   ├── table.html               # DELETED (unused, FR-058) or promoted to the one actually rendered — decided in research.md
│   │   ├── overview.html / samples_overview.html / measurements_overview.html  # reviewed for FR-058 status
│   └── README.md                    # rewritten (FR-059)
└── conf/settings/apps.py            # unchanged (DJANGO_TABLES2_TEMPLATE already correct)

fairdm_demo/
└── config.py                        # + search_fields on each registration (illustrates the default and the override)

docs/portal-development/
└── listing-a-registered-type.md     # NEW — FR-060

tests/
├── test_core/test_dataset/          # + published field tests
├── test_core/test_sample/           # + SampleQuerySet.published() tests
├── test_core/test_measurement/      # + MeasurementQuerySet.published() tests
├── test_registry/                   # + search_fields validation tests
└── test_contrib/test_collections/   # NEW — the app's first tests (views, urls, menus, switcher)
```

**Structure Decision**: single Django project, no new app. All changes land inside the existing
`fairdm/` package and its `fairdm_demo/` reference app, per Article II — a second collections-like
app would be the wrong abstraction for a rewrite of the only one that exists.

## Complexity Tracking

*No entries — no Constitution Check violation requires justification.*
