# Implementation Plan: One consistent overview page for projects, datasets, samples and measurements

**Branch**: `018-overview-pages` | **Date**: 2026-09-25 | **Spec**: [spec.md](spec.md)

## Summary

Four redesign branches (`wip/project-overview`, `wip/dataset-overview`, `wip/sample-overview`,
`wip/measurement-overview`) already hold the approved content of each page. This plan brings their
code onto one branch and replaces what each page built for itself with shared pieces:

- one page skeleton template that owns the layout and every `overview.*` block
- the facts-column cards as `c-card.*` Cotton components
- one overview plugin class holding what every page does (credits, citations, identifiers,
  timelines, the records-by-type chart), and visibility rules on the Sample and Measurement
  QuerySets
- one small plugin class that picks a sample's or measurement's template by type

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
| II Simplicity / III Anti-Abstraction | Two new plugin classes, each with present concrete uses: `RecordOverviewPlugin` (four pages) and `TypedOverviewPlugin` (sample, measurement). One shared helper module, whose functions each replace two to four copies on the branches. No settings, no registry hooks |
| IV Integration-First | Acceptance tests request the real pages as a visitor and as a team member |
| V Security | JSON-LD goes through the existing escaping helper. Visibility is decided by one function per rule (see D3), and FR-017's filtering is applied in the queryset, never in the template |
| VI / XVII Documentation | Each new component and block gets a usage example in the same story that introduces it |
| VII Dependencies | django-mvp-charts and pyecharts justified below. `deptry` must stay green |
| VIII i18n | Branch templates already use `{% translate %}`. The tasks check Python strings in the ported modules |
| XI Cohesion | Shared overview behaviour lives on `RecordOverviewPlugin`, page logic on each page's `Overview` plugin, and visibility on the Sample and Measurement QuerySets and a Dataset property (D3). Module functions are kept only for pure formatting |
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

### D3. Shared behaviour, grouped the way Article XI asks

The branches spread the shared logic across module functions and a `build()` helper per page.
Article XI puts related behaviour on a class, and prefers the class Django already owns. So the
shared behaviour lands in three places.

**The overview plugin classes.** `RecordOverviewPlugin(OverviewPlugin)` in `fairdm/core/plugins.py`
holds what every overview page does to its record. All four `Overview` plugins subclass it, which
is its concrete use today (Article III):

- `get_credits()`: contributions with each contributor as its real Person or Organization, and
  its roles. Replaces `contributions_of` and three inline copies.
- `get_identifiers()`: value, type, and a doi.org link for DOIs and IGSNs. Replaces three copies.
- `get_citation(*, authors, year, title, link)`: DataCite's
  `Creators (Year). Title. Publisher. Identifier`, with the publisher taken from the site. Each
  page passes its own inputs (collectors and IGSN for a sample, measurers and DOI for a
  measurement, `reference` first for a dataset). Replaces four builders.
- `get_timeline(steps, dates, descriptions, credits)`: one entry per step, dated steps in date
  order and undated ones after, partial dates kept as recorded (FR-034, FR-040). The `LIFECYCLE`
  and `PROCEDURE` step tables stay on their own plugins as class attributes, so a portal can
  subclass and change them.
- `get_records_by_type_chart(samples, measurements)`: the composition chart. Replaces
  `type_counts` and `composition_chart`.

Each page's own logic moves from its branch `overview.py` module into methods on that page's
`Overview` plugin, and `get_context_data()` assembles the context. For example, the dataset
page's `field_summary` and `preview_table`, the project's `timeline` and `readiness`, and the
sample's `measurement_summary` all become plugin methods. The per-page `overview.py` modules are
not created.

**QuerySets and models, for visibility.** The FR-013, FR-014 and FR-017 rules become:

- `Dataset.data_is_public` (property): the dataset is public and its `published` flag is set.
- `SampleQuerySet.visible_to(user)` and `MeasurementQuerySet.visible_to(user)`: the records whose
  **own** dataset is public and published, or on whose own dataset the user holds
  `dataset.view_dataset` or `dataset.change_dataset` (guardian's `get_objects_for_user`, plus
  model-level permission holders).
- The rule is applied **per row, against each record's own dataset**, and nothing switches it off
  because the viewer is on the *page's* dataset team. This covers:
  - measurements made on a sample (FR-033)
  - related samples, both parents and subsamples (FR-033)
  - other measurements on the same sample (FR-039)
  - the sample a measurement was made on (FR-041)
- A related record the viewer may not see is shown as "an unpublished sample" (or measurement),
  neither named nor linked, and it isn't counted in figures a visitor sees.
- **The parent project** (the header meta line, `c-card.parent`, the breadcrumbs and JSON-LD
  `isPartOf`) is shown only when the existing `project_is_visible(request, project)` passes.
  Nothing ties a dataset's visibility to its project's, so a public dataset can sit in a private
  project. The spec's edge case says a private record is never confirmed to exist.

**Module functions, for pure formatting only.** `fairdm/core/overview.py` keeps the functions that
have no subject beyond their arguments: `format_authors` and `author_name` (replacing three
copies), `json_ld`, `as_date`, `sentence_case` and `safe_reverse`.

### D4. `TypedOverviewPlugin` for samples and measurements

This goes in `fairdm/core/plugins.py`, subclassing `RecordOverviewPlugin`:

- `base_model` and `fallback_template` class attributes
- `get_template_names()` walks `type(self.base_object).__mro__` down to `base_model`, adding
  `<app_label>/<model_name>_overview.html` for each concrete class, then the fallback (FR-042,
  FR-043)
- `check` asks whether the record is in `base_model.objects.visible_to(user)`, and
  `handle_no_permission()` raises `Http404` (FR-013, FR-014, SC-004). A code comment explains why
  `PrivateRecordNotFoundMixin` isn't reused: it reads `obj.visibility`, and samples and
  measurements have none.

The sample's `Overview` plugin and a new measurement `Overview` plugin both subclass it. Neither
this class nor `RecordOverviewPlugin` sets `url_path`. The sample overview stays at
`/samples/<uuid>/overview/`.

### D5. Measurements join the plugin system at the same address

- Register an `Overview` plugin against `Measurement` in `fairdm/core/measurement/plugins.py`,
  replacing the module docstring that says measurements have no plugin pages.
- **The measurement `Overview` sets `url_path = None`**, as the project and dataset overviews do.
  Without it, the plugin base mounts it at `overview/`, and the address moves to
  `/measurement/<uuid>/overview/`.
- `fairdm/core/measurement/urls.py` mounts `registry.get_urls_for_model(Measurement)` at
  `<str:uuid>/`. The existing `measurement/` prefix and `app_name = "measurement"` stay, so
  `Measurement.get_absolute_url` keeps returning `/measurement/<uuid>/` (FR-037). Tests assert
  that literal path, not equality with `reverse()`, which would move with it.
- The plugin overrides `get_breadcrumbs()` to give project › dataset › sample › measurement. It
  leaves out a missing or invisible project (US-4 scenario 8, D3), and shows an unpublished sample
  as "Unpublished sample" with no link (FR-017).
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
- The three addresses are defined once in the package, as `EXAMPLE_ACCOUNT_EMAILS` next to
  `DEV_ACCOUNT_EMAILS` in `fairdm/management/commands/create_dev_accounts.py`. The seed command
  imports them, and check `fairdm.E501` reports the union of both sets. ADR 0022's reasoning
  applies to these accounts as much as the shipped ones: a refusal guards the act, and only the
  check guards a database copied between environments.
- It seeds every state the spec names: the three projects, five datasets, four samples and four
  measurements described in #368–#371.
- It deletes and recreates only the records it created, found by a fixed name prefix or UUID set
  (FR-047).

Each story extends the command for its own page. The three branch commands are not carried over.
`docs/portal-development/development_accounts.md` explains which accounts come from which
command.

### D7. Charts

The composition and growth charts use django-mvp-charts' `<c-chart>`, and the branch's
`fairdm/static/js/chart-theme.js` paints them with theme colours. django-mvp-charts expects
production projects to bundle ECharts themselves, and loads it from a CDN in development. So the
skeleton puts the pinned jsDelivr `<script>` (with SRI) in its own block,
`overview.chart_library`, inside `extra_js`. A portal that bundles ECharts replaces that one
block. The scripts load only when the context holds a chart. Each chart's text alternative (the
branch's `description`) is rendered as visible text or through `aria-describedby`, so the page
still reads when the script fails (spec edge case, SC-006).

## Project structure

```text
fairdm/
  core/
    overview.py                      # D3 pure formatting functions only
    plugins.py                       # + RecordOverviewPlugin, TypedOverviewPlugin (D3, D4)
    project/{plugins.py, templates/project/project_detail.html}
    dataset/{models.py, plugins.py, templates/dataset/dataset_detail.html}   # + data_is_public
    sample/{models.py, plugins.py, templates/sample/sample_overview.html}    # + visible_to
    measurement/{models.py, plugins.py, urls.py, templates/measurement/measurement_overview.html}
    measurement/views.py             # MeasurementDetailView removed
  templates/
    overview/page.html               # D1 skeleton
    overview/includes/pending_action.html
    cotton/card/{citation,identifiers,people,parent,dates,readiness,timeline,placeholder}.html
    cotton/{stats,list,tabs}/…, cotton/progress.html   # from the branches
  static/js/chart-theme.js
  conf/settings/{apps.py, addons.py}  # mvp_charts app, cite icon
  conf/checks.py                     # E501 covers the example.com accounts
  management/commands/create_dev_accounts.py  # + EXAMPLE_ACCOUNT_EMAILS
demo/
  management/commands/seed_overviews.py
  templates/demo/{rocksample_overview.html, xrfmeasurement_overview.html}
docs/portal-development/
  overview-pages.md                  # pages, blocks, type templates, worked example
  component_library/cards.md         # c-card.* and the four general components
tests/test_core/
  test_overview.py                   # pure formatting functions
  test_plugins.py                    # RecordOverviewPlugin, TypedOverviewPlugin
  test_project/test_overview.py, test_dataset/test_overview.py,
  test_sample/test_overview.py, test_measurement/test_overview.py
```

## Complexity tracking

| Addition | Why it's needed | Simpler alternative rejected because |
|---|---|---|
| django-mvp-charts | FR-021 and FR-026's charts. It is the charting component django-mvp projects use | Hand-written ECharts config in templates duplicates what the package does and escapes nothing |
| pyecharts as a direct dependency | `fairdm/core/plugins.py` imports it to build chart options. `deptry` rejects relying on it through django-mvp-charts | Passing raw option dicts loses the typed builder the branches were written against |
| `RecordOverviewPlugin` | Four concrete uses now. It holds the behaviour the four branches each copied (credits, identifiers, citation, timeline, chart) | Module functions, which Article XI rules out for behaviour sharing a subject, and which a portal can't override |
| `TypedOverviewPlugin` | Two concrete uses now (sample, measurement), identical logic on the branches | Duplicating it in two plugins is what the branches did, and FR-042 then has two implementations to keep in step |
| Four general Cotton components in FairDM | The pages need stats, list, tabs and progress, and django-mvp 0.24 doesn't ship them | Moving them upstream is out of scope (maintainer ruling, 2026-09-25) |
