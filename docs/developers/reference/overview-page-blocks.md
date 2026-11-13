# Overview page blocks

Every project, dataset, sample, measurement, person and organization opens on an overview page, the first tab of its detail view. All six extend one template, `overview/page.html`, which defines the blocks listed here. Each record's own template fills blocks and adds some of its own. This page lists the blocks, the template that owns each and the context entries the shared blocks read. It does not describe the plugins that build the context, which [Overview plugins](overview-plugins.md) covers, or what each page shows to a visitor, which the screen guides for [a project](../../users/projects/project.md), [a dataset](../../users/datasets/dataset.md), [a sample](../../users/samples/sample.md) and [a measurement](../../users/measurements/measurement.md) cover.

## Templates

| Page | Template |
|---|---|
| Project | `project/project_detail.html` |
| Dataset | `dataset/dataset_detail.html` |
| Sample | `sample/sample_overview.html`, or the sample type's own template |
| Measurement | `measurement/measurement_overview.html`, or the measurement type's own template |
| Person | `contributors/overview/person.html` |
| Organization | `contributors/overview/organization.html` |

A sample type or measurement type's own template is named `<app_label>/<model_name>_overview.html`. See [How to give a sample or measurement type its own overview page](../how-to/give-a-sample-or-measurement-type-its-own-overview-page.md).

## Anatomy

A page has, in order, notices, a header band in the record's colour, and a wide content column beside a narrow side column. Below the `lg` breakpoint the two columns stack, content first.

The header carries the record's badges, its name, the people behind it, a line of key facts, its keywords and its actions, with the headline figures along its foot. A record with an image shows it filling the header's trailing side, and on a phone as a banner above the header. Pressing it opens the image at full size. A record without an image shows its icon, with the sign-in pages' ruled grid on the trailing side.

The side column draws, in order: the readiness checklist, how to cite the record, one fact sheet (details, identifiers, funding and how a machine reaches it), the key dates where a record shows them there, the people credited, then what is particular to the record.

There is no central editing menu. Each part of the record is edited from the panel that shows it, through the `edit` links described in [Record editing pages](record-editing-pages.md#the-edit-links). A control is drawn only for someone who may use its page.

## Blocks of `overview/page.html`

The blocks are listed in page order. An indented block sits inside the block above it.

| Block | Holds |
|---|---|
| `overview.notices` | Alerts above the header, so they are read first. |
| `overview.image` | Header: the record's icon, drawn when the record has no image. A record with an image shows the image instead and draws no `overview.image`. |
| `overview.badges` | Header: the type, status and access badges. |
| `overview.name` | Header: the name inside the heading. Defaults to `record_title`, else `record.name`. |
| `overview.byline` | Header: the people behind the record, from `header_people`, each linked to their page. The first four are named and the rest counted. |
| `overview.facts` | Header: a line of key facts, each an `<li>` with a label and a value. Empty on the shared page. |
| `overview.keywords` | Header: the record's keywords, with their Edit, or Add keywords when there are none and the viewer may add them. |
| `overview.actions` | Header: the buttons. Cite and Share, then `overview.manage`. The Share menu is given the record's [permalink](permalinks.md) from the `permalink` tag, so a block that replaces this one without `{{ block.super }}` has to call the tag itself. |
| `overview.manage` | Inside the actions: the header's Edit, which opens the record's details. |
| `overview.figures` | The foot of the header: the headline figures, drawn with [`c-overview.figure`](components.md#c-overviewfigure). Empty on the shared page. |
| `overview.main` | The wide column. Empty on the shared page. |
| `overview.side` | The side column, which holds the blocks below. |
| `overview.readiness` | [`c-overview.readiness`](components.md#c-overviewreadiness), drawn when `readiness` is set. |
| `overview.cite` | [`c-overview.cite`](components.md#c-overviewcite), fed by `citation`. |
| `overview.details` | [`c-overview.sheet`](components.md#c-overviewsheet), fed by `details`, `edit`, `record_kind`, `identifiers`, `record.uuid`, `record.local_id`, the record's [permalink](permalinks.md) from the `permalink` tag, `funding`, `can_manage` and `api_url`. A block that replaces it without `{{ block.super }}` loses the Permalink row unless it calls the tag. |
| `overview.details_extra` | Inside the fact sheet: rows a record adds to the details, each written as `<div><dt>…</dt><dd>…</dd></div>`. |
| `overview.timeline` | Key dates, where a record shows them in the side column. Empty on the shared page. |
| `overview.people` | [`c-overview.people`](components.md#c-overviewpeople), fed by `people` and `people_url`, with Manage for the team. |
| `overview.record_facts` | Panels particular to the record. Empty on the shared page. |
| `overview.chart_library` | The ECharts script, loaded only when `has_charts` is true. Replace it to serve ECharts yourself. |
| `overview.map_library` | MapLibre's script and stylesheet, loaded only when `has_map` is true. Replace it to serve MapLibre yourself. |

A block that wraps other blocks (`overview.main`, `overview.side`, `overview.details`) keeps its content when you add to it with `{{ block.super }}`, and replaces it when you do not. The template also extends the shell's `head` and `extra_js` blocks: `head` carries the schema.org description from `json_ld`, and `extra_js` loads `js/overview.js`, which runs the description tabs, folds long text, copies identifiers and the citation, opens the image at full size, filters a list by type and draws the maps (see [Maps and filters](components.md#maps-and-filters-in-jsoverviewjs)).

### Context the shared blocks read

| Entry | Read by |
|---|---|
| `record` | `overview.keywords`, `overview.actions`, `overview.details`. |
| `request` | `overview.actions`, `overview.details`: the `permalink` tag reads it to build the absolute link. |
| `overview_icon` | The record's colour, and `overview.image`. |
| `cover_image` | The header: the record's image, set by `RecordOverviewPlugin`. A page without it draws `overview.image`. |
| `record_title` | `overview.name`. |
| `header_people`, `header_people_label`, `people_url` | `overview.byline`. |
| `edit` | Every Edit control: `overview.keywords`, `overview.manage`, `overview.details`. |
| `record_kind` | `overview.details`, which names it in the Delete line. |
| `readiness` | `overview.readiness`. Its `title`, `summary` and `about` are set by the plugin. |
| `citation` | `overview.cite`: `text`, and optionally `note`, `note_url` and `note_link`. |
| `details`, `identifiers`, `funding`, `can_manage`, `api_url` | `overview.details`. `funding` set to `None` leaves the Funding section out. |
| `people`, `people_url`, `can_manage` | `overview.people`. |
| `json_ld` | The page head. |
| `has_charts` | `overview.chart_library` and the chart scripts. |
| `has_map` | `overview.map_library`. |

## Blocks the record templates add

| Page | Fills | Adds, in the wide column | Adds, in the side column |
|---|---|---|---|
| Project | `overview.badges`, `overview.facts`, `overview.notices`, `overview.figures`, `overview.main`, `overview.details_extra` | `overview.about`, `overview.datasets`, `overview.charts` | |
| Dataset | `overview.badges`, `overview.facts`, `overview.readiness`, `overview.notices`, `overview.figures`, `overview.main`, `overview.record_facts` | `overview.about`, `overview.lifecycle`, `overview.data`, `overview.charts` | `overview.publications`, inside `overview.record_facts` |
| Sample | `overview.badges`, `overview.facts`, `overview.notices`, `overview.figures`, `overview.main`, `overview.side` | `overview.properties`, `overview.notes`, `overview.history`, `overview.measurements` | `overview.location` after `overview.cite`, and `overview.samples` after `overview.details` |
| Measurement | `overview.badges`, `overview.facts`, `overview.notices`, `overview.figures`, `overview.main`, `overview.side` | `overview.properties`, `overview.procedure`, `overview.notes`, `overview.sample`, `overview.siblings` | `overview.location`, between `overview.cite` and `overview.details` |
| Person | `overview.notices`, `overview.image`, `overview.badges`, `overview.name`, `overview.byline`, `overview.actions`, `overview.figures`, `overview.main`, `overview.side` | `overview.about`, `overview.records`, `overview.roles`, `overview.future` | |
| Organization | `overview.image`, `overview.badges`, `overview.name`, `overview.byline`, `overview.actions`, `overview.figures`, `overview.main`, `overview.side` | `overview.about`, `overview.members`, `overview.records`, `overview.future` | `overview.location`, `overview.hierarchy` |

A sample or measurement type fills `overview.properties`, which is empty on the shared page and is where a type draws its own fields. A measurement type that records its result without a single `value` fills `overview.result`, which sits inside `overview.figures`.

The person and organization pages define `overview.side` themselves and put these blocks inside it:

| Page | Blocks in `overview.side` |
|---|---|
| Person | `overview.readiness`, `overview.identifiers`, `overview.links`, `overview.affiliations`, `overview.people`, `overview.activity` |
| Organization | `overview.readiness`, `overview.identifiers`, `overview.links`, `overview.location`, `overview.hierarchy`, `overview.activity` |

The person page's `overview.future` holds the publications and map cards and the organization page's holds its members map. The activity blocks hold [`c-card.placeholder`](components.md#c-cardplaceholder) cards.

The project page's datasets panel carries Add dataset beside "See all" for the team, and its timeline row in the fact sheet carries the key dates' Edit. The dataset page's timeline panel carries the key dates' Edit and its readiness panel carries Publish.

## Tasks

- [How to extend an overview page](../how-to/extend-an-overview-page.md)
- [How to give a sample or measurement type its own overview page](../how-to/give-a-sample-or-measurement-type-its-own-overview-page.md)
- [How to add an action to an overview page](../how-to/add-an-action-to-an-overview-page.md)

The decision behind this design is [ADR 0023](../../adr/0023-an-overview-page-is-extended-through-blocks-plugin-methods-and-type-templates.md).
