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
time, so a new registration needs no per-type wiring. US-6 is a deletion story: the redirect view,
the three overview views with their routes and templates, the unreached plugin, the unused
`table.html`, the `collection_tags` templatetag module that only `table.html` loaded, the export
machinery and the stale README all go.

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
| I — Test-First | Every new/changed route gets a smoke test asserting status code (FR-051); red-green-refactor per behaviour | PASS — every production task is preceded in tasks.md by the test that fails without it, including the admin change (its test is ordered ahead of it inside US-1 rather than left in the foundational block) and the duplicate-slug refusal |
| II — Simplicity | No new app, no new abstraction layer; extends `ModelConfiguration` and rewrites the existing view in place | PASS |
| III — Anti-Abstraction | `search_fields` is one new attribute on an existing class, following the exact shape `COMPONENTS` already uses for the other six | PASS |
| IV — Integration-First | The published-flag contract (FR-001–007) and the queryset filtering contract are the integration points; both get direct tests before column/template polish | PASS |
| V — Security & data-safety | Closes the standing leak (unfiltered `DataTableView` queryset serving private-dataset records) rather than adding a new one; publication check happens at queryset level, not template level | PASS — this is the feature's stated risk (decisions.md, "Risks") |
| VI — Documentation | README rewritten (FR-059), new `docs/portal-development/` page for `search_fields` and listing generation (FR-060), both in this PR | PASS |
| VII — Dependency discipline | No new dependency; reuses django-tables2/django-filter/flex_menu already in the shell | PASS |
| VIII — I18n | Every label (column headers, filter labels, empty state, switcher) MUST use `gettext_lazy`/`{% trans %}` (FR-021) | PASS — headers and filter labels are structurally guaranteed, the rest is a task. `TableFactory` and `FilterFactory` derive both from each model field's `verbose_name`, which Article IX already requires to be `gettext_lazy`, so this feature authors no header or label for a generated column and testing that path would be testing the framework. The four strings it does author — the empty state's heading and message, the switcher's group labels, and the one new measurement column header — carry `gettext_lazy` as named deliverables of their tasks |
| IX — Data-model conventions | `published` field needs `verbose_name` + `help_text`; both `db_index` decisions recorded in data-model.md, including that `BaseModel.name` indexes four concrete models (Sample, Measurement, Project, Dataset) and forces four migrations; migrations squashed at convergence | PASS |
| X — Test structure | `tests/test_contrib/test_collections/` mirrors `fairdm/contrib/collections/` module for module, one factory reused (`DatasetFactory`), grouped `Test<Subject>` classes; no test file named after a concern rather than a source module (Project Structure, below) | PASS |
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
│   ├── models.py                    # + Dataset.published field, + DatasetQuerySet.published()
│   ├── admin.py                     # + published in fieldsets, list_display, list_filter
│   └── migrations/                  # 0012_dataset_published.py, + a name-index migration
├── core/sample/
│   ├── managers.py                  # + SampleQuerySet.published()
│   └── migrations/                  # + a name-index migration
├── core/measurement/
│   ├── managers.py                  # + MeasurementQuerySet.published()
│   └── migrations/                  # + a name-index migration
├── core/project/migrations/         # + a name-index migration (BaseModel.name reaches Project too)
├── core/abstract.py                 # + db_index=True on BaseModel.name (4 migrations follow)
├── registry/
│   ├── config.py                    # + ModelConfiguration.search_fields (COMPONENTS-adjacent, not a component)
│   └── factories.py                 # FilterFactory._get_smart_filters scopes generated choice lists to published records
├── contrib/collections/
│   ├── apps.py                      # menu population, adjusted for get-or-create Samples/Measurements nodes, + per-node check
│   ├── urls.py                      # overview routes removed (US-6); the listing url names live in views.get_urls()
│   ├── views.py                     # DataTableView rebuilt (queryset, search_fields, empty state, template_name, url names, duplicate-slug refusal, switcher context); CollectionRedirectView, the export machinery and the three Overview views deleted
│   ├── tables.py                    # sample and dataset link suppression rebuilt as render methods, a measurement's own linkified column added, Meta.order_by with a unique tie-break
│   ├── plugins.py                   # DELETED (US-6, FR-057)
│   ├── templatetags/collection_tags.py  # DELETED — its only loader was table.html (FR-058)
│   ├── templates/collections/
│   │   ├── listing.html             # NEW — the page DataTableView renders, extends the shell's table_view.html, holds the switcher (research.md R12)
│   │   ├── table.html               # DELETED (unused as a table template, FR-058)
│   │   ├── overview.html / samples_overview.html / measurements_overview.html  # DELETED with their views and routes (research.md R12)
│   └── README.md                    # rewritten (FR-059)
└── conf/settings/apps.py            # only the commented DJANGO_TABLES2_TEMPLATE line removed, naming a template T058 deletes

fairdm_demo/
└── config.py                        # + search_fields on each registration (illustrates the default and the override)

docs/portal-development/
└── listing-a-registered-type.md     # NEW — FR-060

tests/
├── test_core/test_dataset/          # + published field tests, + DatasetQuerySet.published() tests
├── test_core/test_sample/           # + SampleQuerySet.published() tests
├── test_core/test_measurement/      # + MeasurementQuerySet.published() tests
├── test_core/test_abstract.py       # + TestNameIndex (BaseModel.name carries an index — SC-007)
├── test_registry/
│   ├── test_config.py               # + search_fields validation tests
│   └── test_factories.py            # + filter choice lists scoped to published records
└── test_contrib/test_collections/   # NEW — the app's first tests
    ├── test_apps.py                 # menu population and the empty-kind check
    ├── test_tables.py               # name/link suppression, default ordering and its tie-break
    ├── test_urls.py                 # route smoke tests, URL names, duplicate-slug refusal
    └── test_views.py                # listing content, search, filters, empty state, switcher, query counts, nothing-unreachable
```

**Test file placement is a constraint, not a convenience.** Article X requires a test module to
mirror a source module, and `fairdm/contrib/collections/` contains only `apps.py`, `plugins.py`
(deleted), `tables.py`, `urls.py` and `views.py`. A cross-cutting concern — search, filtering,
ordering, the switcher, query counts — is tested as a further `Test<Subject>` class inside the
module of its subject, not in a file named after the concern. `test_search.py`, `test_filters.py`,
`test_ordering.py`, `test_switcher.py`, `test_menus.py` and `test_queries.py` mirror nothing and are
not created. `tests/test_db/` already exists for its own reasons; this feature adds nothing to it.

**Two words that are not interchangeable.** *Collection* is the package and path name —
`fairdm/contrib/collections/`, `tests/test_contrib/test_collections/` — and it stays exactly where
it already is, because renaming a package is not this feature's work. *Listing* is the user-facing
concept the spec is written in, and it is the word that belongs in every rendered string, URL name
(`<slug>-list`), README sentence and documentation page. Neither word is a synonym for the other in
this feature's prose.

**Structure Decision**: single Django project, no new app. All changes land inside the existing
`fairdm/` package and its `fairdm_demo/` reference app, per Article II — a second collections-like
app would be the wrong abstraction for a rewrite of the only one that exists.

## Complexity Tracking

*No entries — no Constitution Check violation requires justification.*
