# Implementation Plan: One consistent overview page for projects, datasets, samples and measurements

**Branch**: `018-overview-pages` | **Date**: 2026-09-25 | **Spec**: [spec.md](spec.md)

## Summary

Four redesign branches (`wip/project-overview`, `wip/dataset-overview`, `wip/sample-overview`,
`wip/measurement-overview`) already hold the approved content of each page. This plan brings their
code onto one branch and replaces what each page built for itself with shared pieces:

- one page skeleton template that owns the layout and every `overview.*` block
- the facts-column cards as `c-card.*` Cotton components
- one module of shared Python for credits, citations, identifiers, timelines and visibility
- one small plugin base class that picks a sample's or measurement's template by type

The four page templates then only fill blocks. The measurement page moves from a standalone
`DetailView` into the plugin system at the same address. The branches' three development-data
commands become one.

The approved branches are the design source. Wherever a page's content, wording or look is not
changed by a requirement in the spec, the implementation keeps what the branch has.

## Technical context

**Language/version**: Python 3.12+, Django 5.x
**Primary dependencies**: django-mvp `>=0.24,<0.25` (raised from 0.23), django-mvp-charts
`>=0.2,<0.3` (new), pyecharts (new direct dependency, see *Complexity tracking*),
django-cotton, django-polymorphic, django-guardian
**Storage**: no model or migration changes
**Testing**: pytest, pytest-django, factory-boy. The tests mirror the source tree (Article X)
**Target**: the `fairdm` package and the `demo` reference application
**Performance**: not a goal of this feature (maintainer ruling, 2026-09-25). No query-count pins.
Obvious per-row queries found while porting are fixed with `select_related` or
`prefetch_related`, nothing more
**Constraints**: every string translatable (Article VIII); WCAG 2.2 AA on tabs, charts,
disclosures, menus and timelines (SC-006); nothing a visitor can't see reaches the page or its head
(FR-013–FR-017, FR-050)

## Constitution check

| Article | How the plan meets it |
|---|---|
| I Test-First | Every story's tasks start with failing tests through the test client, asserting on rendered HTML |
| II Simplicity / III Anti-Abstraction | One new base class (`TypedOverviewPlugin`), with two concrete uses from the start (sample, measurement). One shared helper module, whose functions each replace two to four copies on the branches. No settings, no registry hooks |
| IV Integration-First | Acceptance tests request the real pages as a visitor and as a team member |
| V Security | JSON-LD goes through the existing escaping helper. Visibility is decided by one function per rule (see D3), and FR-017's filtering is applied in the queryset, never in the template |
| VI / XVII Documentation | Each new component and block gets a usage example in the same story that introduces it |
| VII Dependencies | django-mvp-charts and pyecharts justified below. `deptry` must stay green |
| VIII i18n | Branch templates already use `{% translate %}`. The tasks check Python strings in the ported modules |
| X Test structure | New tests under `tests/test_core/…` mirroring `fairdm/core/…`, factories reused from the existing conftests |
| XVIII Demo | The demo's rock sample and XRF measurement extend their pages. Water, soil and ICP-MS stay generic (FR-044) |

## Design

### D1. One page skeleton, four page templates

`fairdm/templates/overview/page.html` extends `detail_view.html` and owns the whole anatomy
(FR-001–FR-003, FR-005–FR-007): header (badges, name, meta line, actions), notices, figures, and
the two-column grid (`lg:grid-cols-3`, content `lg:col-span-2`, stacking content first). Every
block is defined here, in page order, most of them empty.

| Area | Blocks |
|---|---|
| Header | `overview.badges`, `overview.meta`, `overview.actions` |
| Above the columns | `overview.notices`, `overview.figures` |
| Wide column | `overview.main`, which wraps the page-specific content blocks listed per page below |
| Facts column | `overview.side`, which wraps, in order: `overview.readiness`, `overview.cite`, `overview.identifiers`, `overview.people`, `overview.record_facts`, `overview.parent`, `overview.dates` |

The page-specific content blocks all sit under `overview.`, named for what they hold:

- **Project:** `about`, `datasets`, `charts`, `map`, `activity`. Record facts: `funding`.
- **Dataset:** `about`, `data`, `charts`, `map`. Record facts: `publications`, `versions`.
- **Sample:** `properties`, `notes`, `history`, `measurements`, `samples`, `location`.
- **Measurement:** `result` (in the figures position), `properties`, `method`, `procedure`,
  `notes`, `sample`, `siblings`.

Where two pages hold the same thing, they use the same name (`overview.notes`,
`overview.properties`).

The templates become:

- `project/project_detail.html` and `dataset/dataset_detail.html` (their existing names, so plugin
  template resolution is unchanged)
- `sample/sample_overview.html` and `measurement/measurement_overview.html`

Each one extends `overview/page.html` and only fills blocks. The block list lives in one place,
the skeleton's header comment, and the portal developer docs copy it.

### D2. Cards under the `card` namespace

These go in `fairdm/templates/cotton/card/`. django-mvp's `card` folder has only `index.html` and
`wrapper.html`, so nothing collides. Each component wraps `<c-card>` and takes plain values from
the page's context.

| Component | Replaces on the branches | Takes |
|---|---|---|
| `c-card.citation` | "Cite this …" ×4 | `text`, optional `note` (e.g. "cite the dataset instead"), copy button |
| `c-card.identifiers` | "Access and reuse", "Licence and access", "Identifiers" ×2 | identifiers list, optional licence, access state, API link |
| `c-card.people` | "Team", "People" ×3 | credits list, grouping (`named` roles shown by name, others as avatars when `condensed`) |
| `c-card.parent` | "Part of a project", "Where this … belongs" ×2 | parent links (project; dataset + project), licence-from-dataset note |
| `c-card.dates` | "Project details", "Dates", "Record" ×2 | label/value rows, optional timeline bar, optional slot (sample custody status) |
| `c-card.readiness` | "Metadata readiness", "Ready to publish?" | items (label, done, fix URL, required/recommended) |
| `c-card.timeline` | sample "History", measurement "How it was measured" | steps (label, date or partial date, people, note) |
| `c-card.placeholder` | four hand-built placeholder cards | title, what is coming (composes django-mvp's `c-placeholder.card`) |

**Placeholder actions** (Publish, Import data, All rows, citation formats, metadata downloads) are
rendered as `<c-button>` with `disabled` and a visible "Not available yet" label or tooltip that
names what is missing (FR-011). This is one partial,
`overview/includes/pending_action.html`, rather than a component, because it wraps a single
element.

The four general components the branches added (`stats`, `list`, `tabs`, `progress`) stay where
the branches put them (`fairdm/templates/cotton/`), byte-identical to the branches. They get
documented, and the unused `cards/statistic.html` is deleted once no template references it.

### D3. Shared Python: `fairdm/core/overview.py`

This starts from the dataset branch's module. Each function replaces copies on the branches:

- `credits(obj)`: contributions with each contributor as its real Person or Organization and its
  roles. Replaces `contributions_of` and three inline copies.
- `format_authors(contributors)` and `author_name(contributor)`: replace three copies.
- `citation(*, authors, year, title, publisher, link)`: DataCite's
  `Creators (Year). Title. Publisher. Identifier`. Each page picks its own inputs (collectors and
  IGSN for a sample, measurers and DOI for a measurement, `reference` first for a dataset).
  Replaces four builders.
- `identifiers(obj)`: value, type, and a doi.org link for DOIs and IGSNs. Replaces three copies.
- `timeline(step_table, dates, descriptions, credits)`: one entry per step, dated steps in date
  order, partial dates kept as recorded (FR-034, FR-040). Driven by the existing `LIFECYCLE` and
  `PROCEDURE` tables, which stay with their pages.
- `dataset_is_published(dataset)` and `on_dataset_team(request, dataset)`: the two halves of every
  "follows its dataset" rule (FR-013, FR-014, FR-017). Replaces `sample_is_visible`,
  `dataset_is_open`, `is_team` and the inline filters. There is also a queryset helper,
  `published_datasets_only(queryset, path)`, for FR-017's lists.
- `type_counts`, `composition_chart`, `json_ld`, `safe_reverse`, `as_date`, `sentence_case`: kept
  as the dataset branch has them.

Per-page modules stay (`fairdm/core/{project,dataset,sample,measurement}/overview.py`), each with
one `build(request, obj, can_manage)` that returns its page's context and imports the shared
helpers.

### D4. `TypedOverviewPlugin` for samples and measurements

This goes in `fairdm/core/plugins.py`, subclassing `OverviewPlugin`:

- `base_model` and `fallback_template` class attributes
- `get_template_names()` walks `type(self.base_object).__mro__` down to `base_model`, adding
  `<app_label>/<model_name>_overview.html` for each concrete class, then the fallback (FR-042,
  FR-043)
- `check` is the "follows its dataset" rule from D3, and `handle_no_permission()` raises
  `Http404` (FR-013, FR-014, SC-004)

The sample's `Overview` plugin and a new measurement `Overview` plugin both subclass it.

### D5. Measurements join the plugin system at the same address

- Register an `Overview` plugin against `Measurement` in `fairdm/core/measurement/plugins.py`,
  replacing the module docstring that says measurements have no plugin pages.
- `fairdm/core/measurement/urls.py` mounts `registry.get_urls_for_model(Measurement)` at
  `<str:uuid>/`. The existing `measurement/` prefix and `app_name = "measurement"` stay, so
  `reverse("measurement:overview", uuid=…)`, and with it `Measurement.get_absolute_url`, keep
  resolving to `/measurement/<uuid>/` (FR-037).
- The plugin overrides `get_breadcrumbs()` to give project › dataset › sample › measurement,
  leaving out a missing project (US-4 scenario 8). An unpublished sample appears as
  "Unpublished sample" with no link (FR-017).
- `MeasurementDetailView` and `measurement/detail.html` are deleted.
  `test_detail_page_renders` in `tests/test_core/test_measurement/test_models.py` gets a
  published, public dataset, plus a 404 case beside it.

### D6. One development-data command

`demo/management/commands/seed_overviews.py` merges the three branch commands:

- It refuses to run outside development, reusing the environment guard `create_dev_accounts`
  already uses.
- It creates `regular.user@example.com`, `staff.user@example.com` and `super.user@example.com`
  (password `password`) when they are missing (FR-046). `staff.user` holds object permissions on
  the seeded projects and datasets, `regular.user` on none, and `super.user` is a superuser.
- It seeds every state the spec names: the three projects, five datasets, four samples and four
  measurements described in #368–#371.
- It deletes and recreates only the records it created, found by a fixed name prefix or UUID set
  (FR-047).

Each story extends the command for its own page. The three branch commands are not carried over.

### D7. Charts

The composition and growth charts use django-mvp-charts' `<c-chart>`, and the branch's
`fairdm/static/js/chart-theme.js` paints them with theme colours. ECharts loads as the
django-mvp-charts README prescribes: a pinned jsDelivr URL with SRI, from the skeleton's
`extra_js` block, only when the context holds a chart. Each chart's text alternative (the
branch's `description`) is rendered as visible text or `aria-describedby`, so the page still reads
when the script fails (spec edge case, SC-006).

## Project structure

```text
fairdm/
  core/
    overview.py                      # D3 shared helpers
    plugins.py                       # + TypedOverviewPlugin (D4)
    project/{overview.py, plugins.py, templates/project/project_detail.html}
    dataset/{overview.py, plugins.py, templates/dataset/dataset_detail.html}
    sample/{overview.py, plugins.py, templates/sample/sample_overview.html}
    measurement/{overview.py, plugins.py, urls.py, templates/measurement/measurement_overview.html}
    measurement/views.py             # MeasurementDetailView removed
  templates/
    overview/page.html               # D1 skeleton
    overview/includes/pending_action.html
    cotton/card/{citation,identifiers,people,parent,dates,readiness,timeline,placeholder}.html
    cotton/{stats,list,tabs}/…, cotton/progress.html   # from the branches
  static/js/chart-theme.js
  conf/settings/{apps.py, addons.py}  # mvp_charts app, cite icon
demo/
  management/commands/seed_overviews.py
  templates/demo/{rocksample_overview.html, xrfmeasurement_overview.html}
docs/portal-development/
  overview-pages.md                  # pages, blocks, type templates, worked example
  component_library/cards.md         # c-card.* and the four general components
tests/test_core/
  test_overview.py
  test_plugins.py                    # TypedOverviewPlugin
  test_project/test_overview.py, test_dataset/test_overview.py,
  test_sample/test_overview.py, test_measurement/test_overview.py
```

## Complexity tracking

| Addition | Why it's needed | Simpler alternative rejected because |
|---|---|---|
| django-mvp-charts | FR-021 and FR-026's charts. It is the charting component django-mvp projects use | Hand-written ECharts config in templates duplicates what the package does and escapes nothing |
| pyecharts as a direct dependency | `fairdm/core/overview.py` imports it to build chart options. `deptry` rejects relying on it through django-mvp-charts | Passing raw option dicts loses the typed builder the branches were written against |
| `TypedOverviewPlugin` | Two concrete uses now (sample, measurement), identical logic on the branches | Duplicating it in two plugins is what the branches did, and FR-042 then has two implementations to keep in step |
| Four general Cotton components in FairDM | The pages need stats, list, tabs and progress, and django-mvp 0.24 doesn't ship them | Moving them upstream is out of scope (maintainer ruling, 2026-09-25) |
