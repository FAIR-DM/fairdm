# Implementation Plan: map where a project's or dataset's samples come from

**Branch**: `037-sample-map` | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Summary

The project and dataset overview pages gain the prototype's "Where the samples come from" panel.
The page carries the counts, the area covered and a link to the samples list, and a map element
naming an address beside the record's page. Once the page has drawn, the shared map script fetches
the samples from that address as GeoJSON and draws them clustered, on the record's spatial
coverage. The address asks the record's own overview plugin who may open it and which samples
they see, so the map, the counts and the page's Samples figure agree for every viewer.

## Technical Context

- **Language and framework**: Python 3.13, Django 6.0, django-cotton components, plain JavaScript
  with no build step, MapLibre GL JS 5 as the overview pages already load it.
- **New dependencies**: none.
- **Storage**: none. No model changes and no migration.
- **Testing**: pytest with pytest-django, against PostGIS. Tests are grouped in `Test<Subject>`
  classes in the module that mirrors the source file. Script behaviour is driven once in headless
  Chrome at the browser pass and is not unit-tested.

## Constitution Check

- **Simplicity**: two helper functions, one additional view and one Cotton component. No setting
  and no new hook: a portal changes the panel by overriding the `overview.map` block.
- **Privacy first**: the points' address answers exactly as the record's page does, because it asks
  the page's plugin, and gives only the samples the page counts.
- **Works without custom JavaScript (Article XIII)**: every figure the map conveys is text in the
  panel, and the samples list gives each location.
- **No new dependency.**

## The helpers (`fairdm/core/overview.py`)

- `sample_points(samples)` returns a GeoJSON `FeatureCollection` dict with one `Point` feature per
  sample in `samples` that has a location. It reads the rows with `values()` (`uuid`, `name`,
  `location`, `polymorphic_ctype_id`, `dataset__name`), never model instances. Coordinates are
  `[x, y]` rounded to five places. Properties: `name`, `type` (the sample type's `verbose_name`
  through `sentence_case`, read once per content type through `ContentType.objects.get_for_id`),
  `dataset` (the dataset's name) and `url` (`reverse("sample:overview", kwargs={"uuid": ...})`).
  Ordered by name so the answer is stable.
- `sample_map(samples, coverage, points_url, *, count_datasets=False)` returns `None` when
  `samples` is empty (FR-002). Otherwise a dict: `located`, `missing` (`total - located`),
  `datasets` (distinct datasets among located samples, only when `count_datasets`), `bounds` (the
  coverage as `[west, south, east, north]`, with `east + 360` when `west > east` so MapLibre fits
  the narrow box across the 180th meridian), `area` (the coverage as a sentence, see below),
  `points_url`. With no located sample, `located` is 0 and there are no `bounds` and no `area`.
  Two aggregate queries: one count with a filtered count of located samples (and a distinct dataset
  count when asked), no rows.
- `describe_coverage(coverage)` returns the area as text for the panel and the map's accessible
  name, for instance "48.80° N to 49.20° N, 7.80° E to 8.70° E". Latitudes N or S and longitudes E
  or W from the sign, two decimal places. A single spot reads as one point, "48.80° N, 7.80° E".
  Translated with `gettext`.

## The plugins

- `RecordOverviewPlugin` gets nothing new. Project and dataset `Overview` each:
  - define `get_map_samples()`, the queryset its Samples figure counts:
    `Sample.objects.filter(dataset__project=project).visible_to(user)` and
    `Sample.objects.filter(dataset=dataset).visible_to(user)`. `get_context_data` uses it for the
    samples it already builds, so there is one source.
  - add `sample_map` to the page context from `sample_map(...)`, with
    `self.base_object.spatial_coverage(user)` and the points address from
    `safe_reverse("<project|dataset>:overview-sample-points", uuid=...)`, `count_datasets=True` on
    the project. On the dataset, `sample_map` is `None` unless `shows_records` is true, as its
    charts are.
  - set `has_map` true when `sample_map` has located samples, so `overview/page.html` loads
    MapLibre. Nothing else on these pages sets it.
  - override `get_extra_views()` as `[*super().get_extra_views(), SamplePoints]`, so an extra view
    declared on `RecordOverviewPlugin` (the citation files being built alongside) is kept.

## The address (`SamplePoints` in `fairdm/core/plugins.py`)

- A `Plugin` subclass, `name = "sample-points"`, `url_path = "sample-points"`, so the route is
  `<record address>sample-points/` and its name `project:overview-sample-points` or
  `dataset:overview-sample-points`.
- `has_permission()` builds the owning plugin (`self.plugin_class`) for the same request and
  arguments with `setup()`, keeps it, and returns its `has_permission()`.
  `handle_no_permission()` returns the owner's, so a private record answers "not found" (018,
  FR-018).
- `get()` returns `JsonResponse(sample_points(owner.get_map_samples()))`. On a dataset whose
  records the viewer may not see, it returns an empty `FeatureCollection`.
- Its docstring says why it delegates.

## The panel (`fairdm/templates/cotton/overview/coverage.html`)

Ported from the prototype's `cotton/ov/coverage.html`
(`git show origin/prototype-overview-pages:fairdm/templates/cotton/ov/coverage.html`), with the
gallery annotations (`@description`, `@prop`) other components on main carry.

- `<c-vars map id title more_url empty />`. `c-overview.panel` with the prototype's title "Where
  the samples come from", `more_url` the samples list, `data-card="coverage"`.
- With located samples: the map element, `class="ov-map record-sample"`, `role="img"`, `data-map`,
  `data-points-url`, `data-bounds` (JSON array), and an `aria-label` stating the number mapped and
  the area (FR-020). Then the prototype's `.ov-map-legend`: the number with a location, the number
  without one when there are any, on a project the number of datasets, the area covered (`area`),
  and the prototype's hint "Select a cluster to zoom in, or a point to open its sample."
- With no located sample: the prototype's empty line and no map (FR-019).
- Rendered by `{% block overview.map %}` after `overview.charts` in
  `project/project_detail.html` and `dataset/dataset_detail.html`, only when `sample_map` is set.

## The script (`fairdm/static/js/overview.js`)

`initMaps` handles two kinds of `[data-map]`: the existing single point (`data-lon`, `data-lat`)
and the new one with `data-points-url`. For the new one, in a function of its own
(`startSampleMap`):

- `startMap(el, { style: positron, bounds, fitBoundsOptions: { padding: 48, maxZoom: 10 } })`,
  bounds from `data-bounds`. `startMap` already sets the credits closed and cooperative gestures
  (FR-013, FR-015).
- On `load`, `fetch` the points address (same origin, credentials included). On success, the
  prototype's clustered `samples` source (`clusterRadius: 38`, `clusterMaxZoom: 11`) and its
  `clusters`, `cluster-count` and `points` layers, colour from `mapColour`. On failure, nothing
  more: the panel's text is already there (FR-022).
- The prototype's cluster click: zoom to the cluster's expansion zoom.
- A point click lists every rendered point under the pointer (FR-011): one entry per sample, its
  name as a link to its page and its type and dataset beneath, in one popup. Built with DOM
  methods and `textContent`, never `innerHTML`.
- The prototype's pointer cursor on clusters and points.

## The look (`fairdm/static/css/fairdm.css`)

Beside main's `.ov-map` rules: the prototype's `.ov-map-legend` and `.maplibregl-popup-content`
rules, and the popup list's spacing between entries.

## Specifications edited

- `specs/018-overview-pages/spec.md`: the sentence naming "the map of a project's or dataset's
  samples" among capabilities shown as not yet available now names the panel this feature adds.
- `specs/030-geospatial-locations/spec.md`: the "Showing records on maps" boundary line names
  specification 037 for the project and dataset maps and keeps #497 for the map of organizations
  and filters drawn on a map.

## Documentation

- `docs/developers/reference/overview-page-blocks.md`: `overview.map` in the project and dataset
  rows, and `sample_map` and `has_map` in the context table.
- `docs/developers/reference/components.md`: `c-overview.coverage` with its attributes.
- `docs/users/projects/` and `docs/users/datasets/`: the page describing a project's and a
  dataset's page gains a sentence on the map, where such a page exists.
- `CHANGELOG.md`: an entry under `[Unreleased]`, Added.

## Tests

`tests/test_core/test_overview.py`:

- `TestSamplePoints`: one feature per located sample, none for a sample without a location;
  coordinates, name, type label, dataset name and address for a seeded sample.
- `TestSampleMap`: `None` for an empty queryset; `located` and `missing` adding up to the total;
  `datasets` only when asked; bounds across the 180th meridian get `east + 360`; no `bounds` or
  `area` when nothing is located.
- `TestDescribeCoverage`: hemispheres from the sign and a single spot. Values, not wording: the
  test reads the numbers and hemisphere letters, not the sentence.

`tests/test_core/test_project/test_plugins.py` and `tests/test_core/test_dataset/test_plugins.py`,
`TestOverviewSampleMap`:

- A visitor's map counts only samples of public, published datasets; a private dataset's samples
  add to neither count nor bounds; a member of that dataset's team gets them.
- `located + missing` equals the page's Samples figure for each viewer (FR-018).
- No samples: `sample_map` is `None`. Samples, none located: `located` is 0. `has_map` is true only
  with located samples.
- On the project, `datasets` counts the datasets the mapped samples come from.
- On a public, unpublished dataset seen by a visitor: `sample_map` is `None`.

`tests/test_core/test_plugins.py`, `TestSamplePoints`:

- The project and dataset addresses resolve and answer GeoJSON with the viewer's samples only.
- A private project or dataset answers 404 to a visitor and to a signed-in stranger.
- A citation view declared on `RecordOverviewPlugin.extra_views` is kept beside the points: a
  test plugin subclass shows `get_extra_views()` returns both.

`tests/test_templates/test_overview_components.py`, `TestCoverage`:

- With located samples: the map element carries `data-points-url`, `data-bounds` and an accessible
  name holding the count; the legend holds the counts; the "See all" link is the samples list.
- With none located: no map element.
- The project page with no samples renders no coverage panel; with samples it does, and loads
  MapLibre (`overview/page.html` through `has_map`).

## Proof of scale (SC-004)

At the browser pass: seed one project with 20,000 located samples on the test database, time the
points address and the page, and record both in the ledger. The page's time must not grow with the
number of samples beyond the two counting queries.

## What is not built

- No unit test of the script. Its behaviour is driven once in headless Chrome at the browser pass:
  points arrive, a cluster click zooms, a point opens a popup with a link, samples at one spot are
  listed together.
- No drawing of the coverage box, no list filtering by area, no measurement points (spec Boundary).
- No server-side cache of the points. Nothing measured asks for one.
