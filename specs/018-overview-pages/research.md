# Research: 018-overview-pages

What planning found in the code and on the four redesign branches, and what each finding means
for the plan.

## The branches

| Branch | Base | Relation to main | Notes |
|---|---|---|---|
| `wip/project-overview` | `8ecea75` | 3 commits behind | Dependency bump, the four general components, chart colours, project page, project seed |
| `wip/dataset-overview` | `8ecea75` | 3 behind | Contains all of `wip/project-overview`, plus `fairdm/core/overview.py` and the dataset page. It extends the project seed |
| `wip/sample-overview` | `8ecea75` | 3 behind | Independent. Carries byte-identical copies of `stats` and `tabs` |
| `wip/measurement-overview` | `8022425` | 2 behind | Independent. Replaces `MeasurementDetailView` |

Main has moved by a dependency-group bump (#367), the specification (#373) and a spec-directory
cleanup (#364). Only `uv.lock` is likely to conflict, and it is regenerated in T001 rather than
merged.

## Duplication the plan removes

- `format_authors`: three copies (`core/overview.py`, `sample/overview.py`,
  `measurement/overview.py`). The copies are identical in behaviour.
- The "contributions with their real contributor" loop: four copies.
- The identifier-with-doi.org-link list: three copies.
- The timeline builder: two copies (`lifecycle`, `procedure`). They differ only in the step
  table, and the measurement copy doesn't sort. The plan sorts both, which the spec requires
  (FR-040 refers to FR-034).
- The "follows its dataset" visibility rule: `sample_is_visible`,
  `measurement.overview.dataset_is_open` / `is_team`, and inline
  `dataset__visibility=PUBLIC, dataset__published=True` filters in three places.
- Template resolution by class hierarchy: two identical methods (sample plugin, measurement view).

## Plugin addressing

`registry.get_urls_for_model(model)` builds a record's plugin URLs and its tab menu. A record's
address comes from `registry.declare_addressing`, which defaults to `<str:uuid>`. The sample URL
configuration mounts its plugins at `samples/<str:uuid>/` under the `sample` namespace, and the
Overview plugin's URL name is `overview`. So mounting the measurement's plugins at `<str:uuid>/`
inside the existing `measurement/` include, with `app_name = "measurement"`, keeps
`reverse("measurement:overview", kwargs={"uuid": …})` and the permanent address unchanged. No
`declare_addressing` call is needed.

`Plugin.get_breadcrumbs()` is an overridable method on the plugin base
(`fairdm/contrib/plugins/base.py`), so the measurement breadcrumbs move from the deleted view to
the plugin unchanged.

## Findings on the branches the plan corrects

- **The measurement citation names the sample even when the sample's dataset is unpublished.**
  `measurement/overview.py` puts `measurement.sample` in the citation title unconditionally, and
  the page elsewhere hides the sample's name. FR-017 requires it hidden everywhere, so the
  citation uses "an unpublished sample" in that case.
- **The measurement procedure isn't sorted by date.** The sample's history is. The shared
  `timeline()` sorts both.
- **pyecharts is imported directly but not declared.** It arrives through django-mvp-charts,
  which `deptry` rejects (Article VII). T001 declares it.
- **Each branch seed creates its own accounts.** The plan replaces them with one command that
  creates the three `example.com` accounts once, behind the environment guard
  `create_dev_accounts` already uses.
- **`test_detail_page_renders`** opens a factory measurement while signed out. Factory datasets
  are private, so it fails once measurements follow their dataset. T027 updates it.

## django-mvp components

django-mvp 0.24 ships `card` (`index`, `wrapper`), `placeholder.card`, `badge`, `button`,
`dropdown`, `menu`, `avatar`, `alert` and `rule`. It doesn't ship `stats`, `list`, `tabs` or
`progress`, which is why the branches added them. Putting FairDM's cards in `cotton/card/` adds
to django-mvp's `card` folder without replacing either of its files.
