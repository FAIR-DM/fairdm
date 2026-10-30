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

A page has, in order, notices, a header, a strip of figures, and a wide content column beside a narrow side column. Below the `lg` breakpoint the two columns stack, content first. The side column draws these cards in order: readiness, details, timeline, people, identifiers, funding, citation, then the cards particular to the record.

## Blocks of `overview/page.html`

The blocks are listed in page order. An indented block sits inside the block above it.

| Block | Holds |
|---|---|
| `overview.notices` | Alerts above the header, so they are read first. |
| `overview.image` | Header: the record's image, or its icon. |
| `overview.badges` | Header: status badges. |
| `overview.name` | Header: the name inside the heading. Defaults to `record_title`, else `record.name`. |
| `overview.byline` | Header: the people behind the record, from `header_people`, each linked to their page. |
| `overview.keywords` | Header: the record's keywords. |
| `overview.actions` | Header: the buttons. Cite and Share, then `overview.manage`. |
| `overview.manage` | Inside the actions: the [`c-actions.manage`](components.md#c-actionsmanage) menu, fed by `manage_menu`. |
| `overview.figures` | The strip of figures. Empty on the shared page. |
| `overview.main` | The wide column. Empty on the shared page. |
| `overview.side` | The side column, which holds the blocks below. |
| `overview.readiness` | [`c-card.readiness`](components.md#c-cardreadiness), drawn when `readiness` is set. |
| `overview.details` | [`c-card.details`](components.md#c-carddetails), fed by `details` and `api_url`. |
| `overview.details_extra` | Inside Details: entries a record adds. |
| `overview.timeline` | Key dates in the record's life. Empty on the shared page. |
| `overview.people` | [`c-card.people`](components.md#c-cardpeople), fed by `people` and `people_url`. |
| `overview.identifiers` | [`c-card.identifiers`](components.md#c-cardidentifiers), fed by `identifiers`, `record.uuid` and `record.local_id`. |
| `overview.funding` | [`c-card.funding`](components.md#c-cardfunding), drawn when `funding` is not `None`. |
| `overview.cite` | [`c-card.citation`](components.md#c-cardcitation), fed by `citation`. |
| `overview.record_facts` | Cards particular to the record. Empty on the shared page. |
| `overview.chart_library` | The ECharts script, loaded only when `has_charts` is true. Replace it to serve ECharts yourself. |

A block that wraps other blocks (`overview.main`, `overview.side`, `overview.details`) keeps its content when you add to it with `{{ block.super }}`, and replaces it when you do not. The template also extends the shell's `head` and `extra_js` blocks: `head` carries the schema.org description from `json_ld`.

### Context the shared blocks read

| Entry | Read by |
|---|---|
| `record` | `overview.image`, `overview.keywords`, `overview.identifiers`. |
| `overview_icon` | `overview.image`, when the record has no image. |
| `record_title` | `overview.name`. |
| `header_people`, `header_people_label` | `overview.byline`. |
| `manage_menu` | `overview.manage`. |
| `readiness` | `overview.readiness`. Its `title`, `summary` and `about` are set by the plugin. |
| `details`, `api_url` | `overview.details`. |
| `people`, `people_url` | `overview.people`. |
| `identifiers` | `overview.identifiers`. |
| `funding`, `can_manage` | `overview.funding`. |
| `citation` | `overview.cite`: `title`, `text`, and optionally `note`, `note_url` and `note_link`. |
| `json_ld` | The page head. |
| `has_charts` | `overview.chart_library` and the chart scripts. |

## Blocks the record templates add

| Page | Fills | Adds, in the wide column | Adds, in the side column |
|---|---|---|---|
| Project | `overview.badges`, `overview.manage`, `overview.notices`, `overview.figures`, `overview.main`, `overview.details_extra` | `overview.about`, `overview.datasets`, `overview.charts`, `overview.map`, `overview.activity` | |
| Dataset | `overview.badges`, `overview.manage`, `overview.notices`, `overview.figures`, `overview.main`, `overview.timeline`, `overview.record_facts` | `overview.about`, `overview.data`, `overview.charts`, `overview.map` | `overview.publications`, inside `overview.record_facts` |
| Sample | `overview.badges`, `overview.notices`, `overview.figures`, `overview.main`, `overview.record_facts` | `overview.properties`, `overview.notes`, `overview.history`, `overview.measurements` | `overview.location` and `overview.samples`, inside `overview.record_facts` |
| Measurement | `overview.badges`, `overview.notices`, `overview.figures`, `overview.main`, `overview.record_facts` | `overview.properties`, `overview.procedure`, `overview.notes`, `overview.sample`, `overview.siblings` | `overview.location`, inside `overview.record_facts` |
| Person | `overview.notices`, `overview.image`, `overview.badges`, `overview.name`, `overview.byline`, `overview.actions`, `overview.figures`, `overview.main`, `overview.side` | `overview.about`, `overview.records`, `overview.roles`, `overview.future` | |
| Organization | `overview.image`, `overview.badges`, `overview.name`, `overview.byline`, `overview.actions`, `overview.figures`, `overview.main`, `overview.side` | `overview.about`, `overview.members`, `overview.records`, `overview.future` | `overview.location`, `overview.hierarchy` |

A sample or measurement type fills `overview.properties`, which is empty on the shared page and is where a type draws its own fields. A measurement type that records its result without a single `value` fills `overview.result`, which sits inside `overview.figures`.

The person and organization pages define `overview.side` themselves and put these blocks inside it:

| Page | Blocks in `overview.side` |
|---|---|
| Person | `overview.readiness`, `overview.identifiers`, `overview.links`, `overview.affiliations`, `overview.people`, `overview.activity` |
| Organization | `overview.readiness`, `overview.identifiers`, `overview.links`, `overview.location`, `overview.hierarchy`, `overview.activity` |

The person page's `overview.future` holds the publications and map cards and the organization page's holds its members map. The activity blocks and the project page's `overview.map` and `overview.activity` hold [`c-card.placeholder`](components.md#c-cardplaceholder) cards.

## Tasks

- [How to extend an overview page](../how-to/extend-an-overview-page.md)
- [How to give a sample or measurement type its own overview page](../how-to/give-a-sample-or-measurement-type-its-own-overview-page.md)
- [How to add an entry to the Manage menu](../how-to/add-an-entry-to-the-manage-menu.md)

The decision behind this design is [ADR 0023](../../adr/0023-an-overview-page-is-extended-through-blocks-plugin-methods-and-type-templates.md).
