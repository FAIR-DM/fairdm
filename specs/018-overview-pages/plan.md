# Implementation Plan: One consistent overview page for projects, datasets, samples and measurements

**Branch**: `018-overview-pages` | **Date**: 2026-09-29 | **Spec**: [spec.md](spec.md)

## Summary

The four overview pages already exist as a working prototype, reviewed page by page with the
maintainer and brought onto this branch from `sketch/018-overview-pages`. Its markup, copy and
layout are the settled design. What the prototype does not have is what this plan adds:

- tests for every acceptance scenario, through the rendered pages
- the page logic moved off module functions and onto classes, as the constitution's cohesion
  article requires
- the gaps between the prototype and the specification, found by those tests and fixed
- documentation for portal developers, and a changelog entry
- the existing tests that describe the pages as they were, brought up to date

Wherever a page's content, wording or look is not changed by a requirement in the spec, the
implementation keeps what the prototype has. A test that disagrees with the prototype's look is
not written (layout, width, stacking and copy get no tests).

## Technical context

**Language/version**: Python 3.13, Django 5.2
**Primary dependencies**: django-mvp, django-mvp-charts (new), pyecharts (new direct dependency),
django-cotton, django-polymorphic, django-guardian. MapLibre GL 5.24.0 from jsDelivr with SRI
**Storage**: no model fields and no migrations. `Dataset` gains one property
**Testing**: pytest, pytest-django, factory-boy, per `docs/contributing/standards/testing.md`.
Tests mirror the source tree
**Target**: the `fairdm` package and the `demo` reference application
**Performance**: not a goal. No query-count tests. Obvious per-row queries are fixed with
`select_related` or `prefetch_related`
**Constraints**: every string translatable (Article VIII). WCAG 2.2 AA on tabs, charts, dialogs,
menus, maps, avatar grid and timelines (SC-006). Nothing a visitor may not see reaches the page or
its head (FR-018 to FR-024, FR-056)

## Starting state

The merged prototype renders all four pages for every seeded record. Against the branch today:

- **12 existing tests fail.** Most request a sample or measurement in an unpublished dataset, which
  FR-019 and FR-020 now answer with "not found", or read context keys the new pages renamed. The
  project and dataset pages no longer offer their Delete link, which the existing tests rightly
  catch.
- **`deptry` fails.** `pyecharts` is imported but not declared, and `django-mvp-charts` is
  declared but only named in settings.
- **The docs check fails.** One page documents `context_object_name` on a class that lost it, and
  37 new public names are undocumented. Most of those names are module functions that D3 moves
  onto classes.

## Constitution check

| Article | How the plan meets it |
|---|---|
| I Testing | Every story starts with tests of its acceptance scenarios through the test client, as a visitor and as the team. Tests that fail drive the fixes. The testing standard decides what gets a test |
| II Simplicity / III Anti-Abstraction | Two plugin classes with present concrete uses: `RecordOverviewPlugin` (four pages) and `TypedOverviewPlugin` (sample and measurement). No settings, no registry hooks |
| IV Integration-First | Acceptance tests request the real pages |
| V Security | JSON-LD goes through one escaping helper. Visibility is decided on the QuerySets (D4) and applied per row, never in a template |
| VI / XVI Documentation | Every new component and block gets a working example, in the story that introduces it |
| VII Dependencies | django-mvp-charts and pyecharts justified below. `deptry` green |
| VIII i18n | The prototype's templates already translate. Tasks check the Python strings as they move |
| X Cohesion | D3: shared behaviour on `RecordOverviewPlugin`, page logic on each page's `Overview` plugin, visibility on the QuerySets, pure formatting as module functions |
| XI FAIR | schema.org JSON-LD on projects and datasets, identifiers linked to their resolvers |
| XVII Demo | The demo's rock sample and XRF measurement extend their pages. Water, soil and ICP-MS stay generic (FR-050) |

## Design

### D1. One page skeleton, four page templates

`fairdm/templates/overview/page.html` owns the anatomy (FR-001, FR-002) and defines every block
in page order. Each page template extends it and only fills blocks. The skeleton's header comment
is the one block list, and the portal documentation copies it (FR-008).

Two block changes against the prototype, so the names follow FR-005 and say what they hold:

- The header's people row is `overview.byline`, not `overview.meta`. `overview.people` stays the
  People card.
- The dataset template's `overview.data` block and the dataset module's `field_summary`,
  `preview_table`, `field_kind` and `record_types` belonged to the data tabs the spec removed.
  They are deleted.

Side-column blocks, in FR-003's order: `overview.readiness`, `overview.details` (with
`overview.details_extra` inside it), `overview.timeline`, `overview.people`,
`overview.identifiers`, `overview.funding`, `overview.cite`, `overview.record_facts`.

### D2. Cards under the `card` namespace

The prototype's ten components in `fairdm/templates/cotton/card/` stay as they are: `citation`,
`descriptions`, `details` (with `details.entry`), `funding`, `identifiers`, `location`, `people`,
`placeholder`, `readiness` and `timeline` (FR-004). Each carries the component annotation header
the code documentation standard asks for. The general components the pages need (`stats`, `list`,
`tabs`, `progress`) stay in `fairdm/templates/cotton/`. The unused `cards/statistic.html` is
deleted.

Anything not available yet (FR-016, FR-017) is `c-card.placeholder` for a card or
`overview/includes/pending_action.html` for a button: disabled, labelled "Coming soon", and saying
why.

### D3. Shared behaviour on classes

The prototype keeps its logic in `fairdm/core/overview.py` and one `overview.py` module per page,
each with a `build()` function the plugin calls. Article X puts behaviour that shares a subject on
a class, and prefers the class Django already owns: here, the view. So:

- **`RecordOverviewPlugin(OverviewPlugin)`** in `fairdm/core/plugins.py` holds what every overview
  page does: `get_credits()`, `get_people()` (the People card, excluding the header's names),
  `get_identifiers()`, `get_citation()`, `get_timeline()`, `get_license_entry()`,
  `get_type_info()`, and the two charts, `get_composition_chart()` and `get_growth_chart()`. All
  four `Overview` plugins subclass it.
- **Each page's own logic** moves from its `overview.py` module onto that page's `Overview` plugin
  as methods (`get_readiness()`, `get_datasets_preview()`, `get_related_samples()`,
  `get_siblings()` and the rest), and `get_context_data()` assembles the context. The per-page
  `overview.py` modules are deleted.
- **`fairdm/core/overview.py`** keeps only pure functions with no shared subject: `format_authors`,
  `author_name`, `json_ld`, `as_date`, `sentence_case` and `safe_reverse`.

A portal changes one piece of a page by subclassing its plugin and overriding one method. Moving
the code changes no output. The acceptance tests written first in each story prove that.

### D4. Visibility

- `Dataset.data_is_public`: the dataset is public and published.
- `SampleQuerySet.visible_to(user)` and `MeasurementQuerySet.visible_to(user)`: records whose
  **own** dataset is public and published, or on whose own dataset the user holds view or change
  rights (FR-019, FR-020).
- The rule applies per row, against each listed record's own dataset, wherever a page lists,
  links or maps a record from another dataset (FR-023). A hidden record is counted or described,
  never named, linked or mapped.
- A parent project the viewer may not see is neither named nor linked, in Details, breadcrumbs
  and JSON-LD.

### D5. Samples and measurements choose their template by type

`TypedOverviewPlugin` (prototype, kept) walks the record's class ancestry to `base_model` and
offers `<app_label>/<model_name>_overview.html` for each, then the fallback (FR-048, FR-049). Its
`check` asks `visible_to`, and a refusal raises `Http404` (SC-004).

### D6. Measurements join the tab strip at the same address

The measurement `Overview` plugin sets `url_path = None`, so it serves `/measurement/<uuid>/`
(FR-041). `MeasurementDetailView` and `measurement/detail.html` are gone. Tests assert the literal
path. Breadcrumbs are the record list, then the measurement (FR-047).

### D7. One development-data command

`demo/management/commands/seed_overviews.py` with its data in `demo/seed/`. It refuses to run
outside development, loads the vocabularies' role concepts first, creates the three `example.com`
accounts when missing (FR-052), seeds every state the spec names (FR-051) and replaces only its
own records (FR-053). `fairdm.E501` reports the `example.com` accounts too.
`docs/portal-development/development_accounts.md` says which command creates which accounts.

### D8. Charts and maps

Charts use django-mvp-charts' `<c-chart>`, painted from theme tokens by
`fairdm/static/js/chart-theme.js`. ECharts loads from a pinned CDN script inside the replaceable
`overview.chart_library` block, only when the page has a chart. Maps use one shared include,
`overview/includes/map_library.html`, only when the page has a map. Each chart's text alternative
and each map's coordinates are in the page as text (spec edge case, SC-006).

## Project structure

```text
fairdm/
  core/
    overview.py                  # D3 pure functions only
    plugins.py                   # RecordOverviewPlugin, TypedOverviewPlugin
    project/plugins.py           # Overview: page logic as methods (project/overview.py deleted)
    dataset/{models.py, plugins.py}      # data_is_public; (dataset/overview.py deleted)
    sample/{managers.py, plugins.py}     # visible_to; (sample/overview.py deleted)
    measurement/{managers.py, plugins.py, urls.py}   # (measurement/overview.py deleted)
    */templates/…                # the four page templates
  templates/
    overview/page.html, overview/includes/*.html
    cotton/card/*.html, cotton/{stats,list,tabs}/, cotton/progress.html
  static/js/chart-theme.js, static/css/fairdm.css
  conf/checks.py, management/commands/create_dev_accounts.py
demo/
  management/commands/seed_overviews.py, seed/*.py
  templates/demo/{rocksample_overview.html, xrfmeasurement_overview.html}
docs/portal-development/
  overview-pages.md              # pages, blocks, type templates, worked example
  component_library/cards.md     # c-card.* and the general components
tests/
  test_core/test_overview.py, test_core/test_plugins.py
  test_core/test_{project,dataset,sample,measurement}/test_overview.py
  test_templates/…               # skeleton and components
  test_demo/…                    # seed command
```

## Complexity tracking

| Addition | Why it's needed | Simpler alternative rejected because |
|---|---|---|
| django-mvp-charts | The records-by-type and growth charts. It is the charting component django-mvp projects use | Hand-written ECharts options in templates duplicate the package and escape nothing |
| pyecharts as a direct dependency | `fairdm/core/plugins.py` builds chart options with it. `deptry` rejects relying on it through django-mvp-charts | Raw option dicts lose the typed builder |
| MapLibre GL from a CDN | The sample and measurement location maps. No key, openly licensed tiles | A static image has no pan or zoom, and a Python map package adds a dependency for one card |
| `RecordOverviewPlugin` | Four concrete uses. It holds what the pages share | Module functions, which Article X rules out and a portal cannot override |
| `TypedOverviewPlugin` | Two concrete uses (sample, measurement) | Two copies of the same template lookup |
| Four general Cotton components in FairDM | django-mvp does not ship stats, list, tabs or progress | Moving them upstream is out of scope |
