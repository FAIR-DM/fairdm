# Research

## Assumptions checked

Run before the specification was put up for approval, against the development stack seeded with
`seed_overviews` and `seed_overview_prototype`.

| Assumption | Result |
|---|---|
| `Project.spatial_coverage(user)` returns the box of a project's located samples and measurements for a visitor | Works. A seeded project gave a box of about 7.8° to 8.7° E, 48.8° to 49.2° N |
| `Dataset.spatial_coverage(user)` does the same for a dataset | Works. A seeded dataset gave a smaller box inside the project's |
| The project and dataset samples lists are routed (`project:samples`, `dataset:samples`) | Both resolve and the project's list answers 200 |
| The samples list gives each sample's latitude and longitude, which FR-021 relies on | It does: the list has latitude and longitude columns filled for each located sample |
| A located sample the visitor may open has a page | Yes, through `Sample.objects.visible_to(None)` and `get_absolute_url()` |
| The sample and measurement maps draw OpenFreeMap tiles with no key | Yes: `fairdm/templates/overview/includes/map_library.html` uses `tiles.openfreemap.org`, with MapLibre 5 pinned |

None failed.

## Planning notes, answered

### N1. The prototype this feature comes from

**Adopted.** `PROTOTYPE.md` was read whole and part F2 against the prototype's code:
`fairdm/templates/cotton/ov/coverage.html`, the `data-points` branch of `initMaps` in
`fairdm/static/js/overview.js`, `map_points` in `fairdm/core/overview_proto.py`, the
`overview.map` block in the project and dataset templates and the `.ov-map-legend` and popup rules
in the prototype's stylesheet. The maintainer's design rules on #668 that touch this panel are
listed under N6.

### N2. The map points are built here

**Adopted, rebuilt.** The points and the counts come from the same `visible_to` queryset each
page already counts its Samples figure from, so FR-018 holds by construction. The view opens on
`Project.spatial_coverage(user)` and `Dataset.spatial_coverage(user)`, which already handle the
180th meridian and the viewer's access. The prototype's cap of 1,500 points, its points written
into the page and its fit to the points' minimum and maximum are not carried over (D2, D4).

### N3. The map script is reused, not rebuilt

**Adopted.** `startMap`, `addAttribution` and `initMaps` on `[data-map]` are on main
(`fairdm/static/js/overview.js`, merged with the sample page). `initMaps` gains a second kind of
`[data-map]` element, one that names the address of its points, and draws the prototype's
clustered source, cluster, count and point layers, the cluster click and the point popup through
`startMap`. No second map script.

### N4. The panel is reused, not rebuilt

**Adopted.** The panel sits in `c-overview.panel` (`fairdm/templates/cotton/overview/panel.html`
on main, the prototype's `c-ov.panel`). Its `more_url` gives the "See all" link to the samples
list that FR-021 asks for.

### N5. The look is ported, never redrawn

**Adopted.** `cotton/ov/coverage.html` lands as `cotton/overview/coverage.html`, under the
`c-overview.*` names main gave the prototype's `c-ov.*` components. The `overview.map` block
follows `overview.charts` in `project/project_detail.html` and `dataset/dataset_detail.html`, as
in the prototype. The `.ov-map-legend` and popup rules come from the prototype's stylesheet into
`fairdm/static/css/fairdm.css`, which holds main's `.ov-map` rules. The map is drawn on the
`positron` style, as the prototype's coverage map is.

### N6. Design rules from #668 that apply here

**Adopted.** The panel has no edit control, since a location is edited on its sample. The tile
credits start closed through `addAttribution`. No badge is added.

### N7. What departs from the prototype and why

**Adopted.** The five changes in behaviour are D2, D3, D4, D8 and FR-023. The one visible change
is a line in the legend stating the area covered and the "See all" link (D3). The points are
served from an address of their own beside the record's page and fetched once the page has drawn.
That address asks the record's own page whether the viewer may open it, so it answers "not found"
exactly where the page does (FR-024).

### N8. Specifications edited in the same pull request

**Adopted.** Two tasks: 018 FR-016 and the "Showing records on maps" line in 030's boundary.

## Decisions for the plan

### Where the points come from

An additional view of each record's overview plugin, as the sample page's redirect is, at
`<record address>sample-points/`, named `project:overview-sample-points` and
`dataset:overview-sample-points`. It builds the owning plugin for the same request and asks it:
its `has_permission()` decides access, its `handle_no_permission()` answers "not found" for a
private record and its samples are the ones the page counts. Nothing about access is written
twice.

The answer is GeoJSON, a `FeatureCollection` of points with the sample's name, its type, its
dataset and its address. MapLibre reads that directly into a clustered source.

### Scale

At 20,000 samples (SC-004) the answer is a few megabytes before compression. It is read with
`values()`, the type label from the content-type cache and the address reversed once per row, so
it costs one query and no model instances. The build times it at 20,000 and records the figure.

### Samples at one spot

At the zoom where clusters stop, samples at one location sit on top of each other. Selecting a
point reads every rendered point under the pointer and the popup lists each of them, so every
sample can be opened (FR-011, SC-003).

## What already exists

| Piece the plan would write | Found at | Where |
|---|---|---|
| Visible samples of a project or dataset | this repo | `Sample.objects.filter(...).visible_to(user)`, as each overview plugin counts them |
| The area the map opens on | this repo | `Project.spatial_coverage`, `Dataset.spatial_coverage` |
| An address beside a record's page that answers as the page does | this repo | `Plugin.extra_views` and `PrivateRecordNotFoundMixin` (`fairdm/contrib/plugins/`) |
| A JSON answer | Django | `JsonResponse` |
| Map, controls, credits closed, cooperative scrolling | this repo | `startMap`, `addAttribution` in `fairdm/static/js/overview.js` |
| Clustering, cluster expansion zoom, popups | installed package | MapLibre GL JS 5, loaded by `overview/page.html` when `has_map` is set |
| The panel frame, heading, "See all" | this repo | `c-overview.panel` |
| Number formatting in the legend | Django | `django.contrib.humanize` `intcomma` |
| The samples list with coordinates | this repo | `project:samples`, `dataset:samples` (specification 023) |
| Points as GeoJSON features | new code | `get_sample_points` on `RecordOverviewPlugin`, beside `get_type_mix` |
| The panel's figures | new code | `get_sample_map` on `RecordOverviewPlugin` |
| The area as a sentence | new code | `describe_coverage` in `fairdm/core/overview.py`, beside the other formatters |
| The coverage panel | ported | prototype `cotton/ov/coverage.html` |
| Cluster layers and point popup | ported | prototype `initMaps`, `data-points` branch |
