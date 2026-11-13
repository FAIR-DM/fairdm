# Redesigned overview pages: hand-over

This branch is a prototype of the redesigned overview pages for projects, datasets, samples and
measurements. It is never merged. Its screens and the decisions on
https://github.com/FAIR-DM/fairdm/issues/668 are the agreed design. Everything below says how they
reach `main`.

- **The look is ported.** The templates, Cotton components, stylesheet and scripts listed under
  "The look" are copied into `main` and cleaned to the repository's standards. They are never
  redrawn from `main`'s `c-card.*` components.
- **The behaviour is rebuilt.** `fairdm/core/overview_proto.py` and the `render_to_response`
  override in `fairdm/core/plugins.py` are evidence of what the pages need. They are rebuilt
  test-first on the plugins that own them.

The pages already exist and are specified in `specs/018-overview-pages/spec.md`. Most of this
prototype changes how they look and where things sit, so most of it is changes that edit
that specification. Three things on the pages are new: specification 018 lists them as "not yet
available" (FR-016), and the prototype builds them.

## The features

Each is a new way for someone to use the site, with no specification to live in.

### F1. Citation downloads

**Who can newly do what:** a reader can take a record's citation as BibTeX or RIS, copied from the
Cite panel or downloaded as a file, on all four overview pages.

- **Screens:** the Cite panel at the head of the side column on every page. Its Text, BibTeX and RIS
  switch, Copy and Download.
- **Models:** none. The formats are built from the record (creators, year, title, publisher, DOI or
  address), not from the citation text as the prototype does. Each format is served at an address of
  its own, so a reference manager can fetch it.
- **Depends on:** C3, which ports the Cite panel with its text citation.
- **Related:** https://github.com/FAIR-DM/fairdm/issues/245 says there is no citation renderer
  anywhere in the repository. This feature builds the record's citation in three formats. It does not
  close that issue, which is about the contributor transforms.

### F2. Map of where a project's or dataset's samples come from

**Who can newly do what:** a reader sees every sample with a location on a map on the project and
dataset pages, grouped into clusters when zoomed out, and opens a sample from the map. The panel
says how many samples have no location.

- **Screens:** "Where the samples come from" on the project and dataset pages.
- **Models:** none. It reads sample locations and the spatial coverage from
  `specs/030-geospatial-locations` (FR-021 to FR-023). Only samples the viewer may open are mapped.
- **Depends on:** C3 (the panel) and C5 (the shared map script).
- **Related:** this is the dataset-map part of https://github.com/FAIR-DM/fairdm/issues/497. That
  issue plans the maps as an add-on with self-hosted tiles. The prototype draws the map in the core,
  from the same OpenFreeMap tiles the core's sample maps already use. Issue 497 keeps the community
  map of organizations and the self-hosted tiles.

### F3. Recent activity on a project or dataset

**Who can newly do what:** a reader sees what was added to a project or dataset recently, grouped by
day: samples and measurements added to each dataset, and datasets created.

- **Screens:** "Recent activity" on the project and dataset pages.
- **Built on:** the `activity` extra of
  [django-mvp-community](https://github.com/django-mvp/django-mvp-community), which is built on
  django-activity-stream (Sam, 2026-11-13). FairDM installs it, registers its records, records an
  action when something happens to a record, and shows the extra's recent-activity component in the
  panel, styled to the prototype's look. The prototype instead works activity out from when records
  were added, so it only shows additions. Recording actions also covers publishing, edits and people
  joining. The specification settles which of those it records.
- **Models:** none of FairDM's own. django-activity-stream brings its tables. Activity about a
  record a viewer may not open is never shown to them.
- **Depends on:** C3.

## Changes to the existing pages

None of these gives anyone a new way to use the site. C1 and C2 are an issue each. C3 to C6 are one issue delivered
in four pull requests.

| | Work | Edits | Closes |
|---|---|---|---|
| C1 | The type badge's "About" dialog opens. Its `onclick` reads the element id as a sum, so it fails on `main` today (`fairdm/templates/overview/includes/type_badge.html`) | | |
| C2 | Every badge is a pill. Keywords are solid pills in a light shade of the primary colour, everywhere they appear. Status pills take a light fill of their status colour. Settled in the theme, not as overrides | | |
| C3 | The shared page and the project page: header band, figures in the header, Cite first, one fact sheet, People with roles, readiness ring, descriptions with tabs and folds, the record's image in the header with a full-size view, the ruled grid on records without an image, and an Edit on each panel in place of the Manage menu | 018, 024 | https://github.com/FAIR-DM/fairdm/issues/377 |
| C4 | The dataset page: the timeline across the page, records by type as bars, related publications | 018 | |
| C5 | The sample page: properties, notes, history timeline, measurements with a filter by type, the location map after the citation, related samples | 018 | |
| C6 | The measurement page: the result in the header, analytical conditions, how it was measured, the sample, other measurements on the sample as a table | 018 | |

C3 also carries the development data the new screens need, from `seed_overview_prototype` into
`seed_overviews` (specification 018, FR-051 to FR-053).

The "not yet available" panels (specification 018, FR-016 and FR-017) for the map, recent activity
and exporting a citation are dropped by C3. F1, F2 and F3 each add their panel when they merge.

## Build order

1. C1 and C2, in parallel. Both are small and touch nothing else.
2. C3. Everything after it builds on its page.
3. C4, C5 and C6, in parallel. The specifications for F1, F2 and F3 are written while these run.
4. F1 and F3 after C3. F2 after C5.

## The shared pieces

Every pattern that recurs, where it occurs, and what it becomes. Paths are on this branch. The
first feature to need a piece builds it, and the others reuse it.

| Piece | Occurs at | Becomes | Built by | Reused by |
|---|---|---|---|---|
| Panel: heading, count, "See all", an edit control | `cotton/ov/panel.html`; `project_detail.html:72,119`; `dataset_detail.html:94,120,137,171`; `sample_overview.html:67,83,130`; `measurement_overview.html:65,72,101`; inside `cotton/ov/activity.html:8`, `coverage.html:8`, `history.html:7`, `location.html:9`, `people.html:10`, `props.html:7` | Cotton component. Check `c-mvp.card` and `c-mvp.section` first: it may be a styling of one of them | C3 | all |
| Edit control on a panel | `cotton/ov/edit.html`; `panel.html:18`; `descriptions.html:21,32`; `sheet.html:14,45`; `overview/page.html:110`; `project_detail.html:156,163` | Cotton component | C3 | C4–C6 |
| Headline figure | `cotton/ov/figure.html`; `project_detail.html:50–53`; `dataset_detail.html:71–75`; `sample_overview.html:56–58` | Cotton component. Check daisy-cotton-ext's `c-stats.*` first | C3 | C4, C5 |
| Which editing pages the viewer may open, keyed by panel | `overview_proto.py:247` (`edit_links`) | A function beside `manage_menu` in `fairdm/core/editing.py`, which it replaces | C3 | C4–C6 |
| People with roles, then faces | `overview_proto.py:95` (`credits_for_panel`), `cotton/ov/people.html` | Method on the overview plugin | C3 | all |
| The identifier that resolves | `overview_proto.py:227` (`primary_identifier`) | Method on the overview plugin | C3 | all |
| Records by type as bars | `overview_proto.py:235` (`mix`), `cotton/ov/mix.html`; `project_detail.html:121`, `dataset_detail.html:139` | Built on the existing `RecordOverviewPlugin._type_counts` | C3 | C4 |
| Dated timeline | `cotton/ov/history.html`; `sample_overview.html:79`, `measurement_overview.html:60` | Cotton component, replacing `c-card.timeline` on these pages | C5 | C6 |
| A type's own fields | `cotton/ov/props.html`, `prop.html`; `sample_overview.html:17`, `measurement_overview.html:16`, `demo/templates/demo/rocksample_overview.html:18`, `xrfmeasurement_overview.html:29` | Cotton components | C5 | C6 |
| Location map | `cotton/ov/location.html`; `sample_overview.html:124`; `measurement_overview.html:128–137` | Cotton component | C5 | C6 |
| Map script: start a map, attribution closed behind its (i) | `overview.js:181–285` (`addAttribution`, `initMaps`) | One shared script, replacing `overview/includes/map_library.html` | C5 | F2 |
| Tabs, folds, copy | `overview.js:12–110` | Shared script | C3 | all |
| Filter chips | `overview.js:160` (`initChips`) | Shared script | C5 | |
| Citation formats | `overview_proto.py:25` (`citation_formats`), `overview.js:111` (`initCite`) | Built from the record, each format at its own address | F1 | |
| Map points | `overview_proto.py:116` (`map_points`) | Uses the spatial coverage from specification 030 | F2 | |
| Activity | `overview_proto.py:149` (`activity`) | Replaced by actions recorded with django-activity-stream, shown through django-mvp-community's recent-activity component | F3 | |

## Duplication to remove

- The cover, tile and grid markup is written once, in `overview/page.html`. Keep it there.
- `overview_proto.py` and the `render_to_response` override gather context for every plugin in one
  place. Each piece moves onto the plugin that owns it.
- `fairdm/static/css/overview.css` repeats spacing and colour values the theme already has. It moves
  into the Tailwind build and uses the theme's variables.
- The pill and keyword overrides in `fairdm/static/css/fairdm.css` become the theme's badge (C2).

## The look

Port each file. Never redraw it.

| File on this branch | Ported by | Lands in `main` |
|---|---|---|
| `fairdm/templates/overview/page.html` | C3 | same path |
| `fairdm/static/css/overview.css` | C3, each page run adding its part | the Tailwind build |
| `fairdm/static/js/overview.js` | C3 (tabs, folds, copy); C5 (maps, chips); F1 (cite switch) | `fairdm/static/js/` |
| `fairdm/static/css/fairdm.css` (badge, keyword, record tag, record card type) | C2 | the theme |
| `cotton/ov/panel.html`, `edit.html`, `figure.html`, `descriptions.html`, `sheet.html`, `people.html`, `readiness.html`, `cite.html` | C3 | `fairdm/templates/cotton/`, under the name the plan picks |
| `cotton/ov/mix.html` | C3 | same |
| `cotton/ov/history.html`, `props.html`, `prop.html`, `location.html` | C5 | same |
| `cotton/ov/result.html` | C6 | same |
| `cotton/ov/coverage.html` | F2 | same |
| `cotton/ov/activity.html` | F3 | the look of django-mvp-community's recent-activity component on these pages, through a template override |
| `fairdm/core/project/templates/project/project_detail.html` | C3 | same path |
| `fairdm/core/dataset/templates/dataset/dataset_detail.html` | C4 | same path |
| `fairdm/core/sample/templates/sample/sample_overview.html`, `demo/templates/demo/rocksample_overview.html` | C5 | same paths |
| `fairdm/core/measurement/templates/measurement/measurement_overview.html`, `demo/templates/demo/xrfmeasurement_overview.html` | C6 | same paths |
| `cotton/project/card.html`, `cotton/dataset/card.html`, `cotton/landing/about.html`, `overview/includes/type_badge.html` (keyword pills) | C2 | same paths |
| `core_cover` thumbnail alias in `fairdm/conf/settings/static_media.py` | C3 | same |

### Screens for the parity checks

Seed with `seed_overviews`, then `seed_overview_prototype`. Check each at 390 and 1440 pixels wide,
signed out and signed in as `regular.user@example.com` (on the team) and
`regular.user2@example.com` (not on it). The password is `password`.

| Screen | Address | Run |
|---|---|---|
| Project, rich, no image | `/projects/p2u5RQQxsGcHgpnCE6TMcJQ/` | C3, F1–F3 |
| Project, empty (as `regular.user2`) | `/projects/pqKPfetoXwPy7HeDgH4aaGe/` | C3 |
| Project, private | `/projects/p7YLjcNuJARQMRS8KxTLRU3/` | C3 |
| Dataset | `/datasets/dAKZzsr4nsJSL4WMHeK4zao/` | C4, F1–F3 |
| Dataset, published | `/datasets/dxwBKsJrxYoBLcCRpUCZ6i6/` | C4 |
| Dataset, unpublished | `/datasets/dGEMhiQL3a9WJgwJphgLz9G/` | C4 |
| Dataset, empty (as `regular.user2`) | `/datasets/dhae3MtyMKmHBEm2KbdjaRJ/` | C4 |
| Sample with an image | `/samples/sC83matAoRS4zTtR8ALLthV/` | C3 (header), C5 |
| Sample, destroyed | `/samples/swzNC7hqgZynA9oFcZGioPF/` | C5 |
| Sample, empty | `/samples/sBL54pAssJKLsuG5dyzcWSg/` | C5 |
| Measurement, XRF | `/measurements/muDcAfazkE2zpNcjF7hQoFD/` | C6 |
| Measurement, ICP-MS | `/measurements/mXQ7byzYgrRX7c6SseyKyEq/` | C6 |
| Measurement, base type | `/measurements/mrrc4vfj9xbfQ6YZV4s7wGE/` | C6 |

The addresses are the seeded records on the prototype's database. A fresh seed gives new ones: find
the same records by name.

## The data model

No new models. One new thumbnail alias, `core_cover` (1200 pixels wide, uncropped).

## Sam's decisions and design rules

From https://github.com/FAIR-DM/fairdm/issues/668:

- The contour pattern behind the header is out.
- A record's image is shown more prominently. It fills the trailing side of the header band at full
  height on desktop, sits as a 16:9 banner above the header on a phone, and opens at full size. The
  image takes the icon tile's place, and the actions move under the keywords.
- Map tile credits start closed, behind their (i) button.
- The header uses the same ruled grid as the sign-in pages, for consistency across the site.
- The grid sits on the trailing side, fading out before the text so the text sits on a plain ground.
  On a phone it keeps to the top corner.
- The grid is only for a record without an image. With an image, the image takes its place and the
  band keeps its plain tinted ground.
- Every badge is a pill. Keywords are solid pills in a light shade of the primary colour, the same in
  the header, on record cards, on the landing page and in the type dialog. Status pills take a light
  fill of their status colour. The record-type label is a pill too.
- No central Manage menu. Each part of the record is edited from the panel that shows it:
  - the header's Edit opens the details
  - the keywords have their own Edit or Add keywords
  - descriptions, notes, key dates, identifiers and locations each have an Edit on their panel
  - the project's Datasets panel has Add dataset, beside "See all"
  - People has Manage
  - Publish sits in the Ready to publish? panel
  - Delete is the last line of the Details panel
- A change to one element keeps everything else where it was: a swap keeps the old element's
  placement, size and fade.

Decided during the prototype and not changed by Sam:

- The headline figures move into the header, and their icon tiles go.
- Cite moves to the top of the side column.
- Details, Identifiers and Funding become one fact sheet. A missing value is a dash.
- People are listed by name with their roles, six of them, then faces.
- Records by type are bars in each type's colour. The growth chart stays.
- A dataset's key dates move from the side column to a timeline across the page.
- On a sample, the map comes straight after the citation.
- The record tabs stay in the app header, since the header band only shows on Overview.

## Faked or skipped

| What | Done properly by |
|---|---|
| Pill shape and keyword style are CSS overrides of the theme's badge | C2 |
| Funding and related publications have no editing page, so their panels carry no Edit | Left as is. Not in this scope |
| Activity is worked out from when records were added. Publishing, edits and people joining are missing | F3, by recording actions through django-mvp-community's activity extra |
| The map shows at most 1,500 samples and only sample locations, with no list of points for screen readers beyond the counts | F2 |
| BibTeX and RIS are built from the citation text, with the year read out of it | F1 |
| Page context is gathered in one override and a helper module | C3–C6, F1–F3, each for its own piece |
| Plain CSS outside the Tailwind build, and `c-ov.*` beside the `c-card.*` components it replaces | C3–C6 |
| No tests and no docs | every run |
| `seed_overview_prototype` makes up sample locations and renames placeholder measurement names | C3, into `seed_overviews` |

## What it replaces

| In `main` | Replaced by | Cost of removing it |
|---|---|---|
| `c-card.citation`, `details`, `details/entry`, `descriptions`, `funding`, `identifiers`, `people` on the four record pages | C3's components | None on the record pages. `c-card.identifiers` and `c-card.readiness` are still used by the contributor overview pages, so those two stay |
| `c-card.placeholder` for the map, activity and citation export on the record pages | F1–F3, and dropped by C3 | None. The contributor pages still use it |
| `c-card.timeline` on the dataset and measurement pages | C4's timeline and C5's history | Remove it once neither page uses it |
| `c-card.location` on the sample and measurement pages | C5 | The organization page still uses it |
| `c-actions.manage` and `manage_menu` (`fairdm/core/editing.py:612`) | C3's edit controls | A breaking change for a portal that fills `overview.manage`. Specification 024's Manage-menu stories are rewritten |
| `overview/includes/map_library.html` | C5's map script | The organization page's map moves to it too |

Nothing is dropped from the database.
