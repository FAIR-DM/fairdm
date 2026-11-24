# Planning notes: export the rows of any records table

Notes for research and planning. The plan answers each one by name.

## The prototype this feature comes from

Branch `prototype-import-export`, its hand-over document `PROTOTYPE.md` at the branch's root, and
this feature's part of it: "1. Export from any records table". The prototype's record is
https://github.com/FAIR-DM/fairdm/issues/692, and its "Decisions" bind this feature. The branch is
read, never merged and never branched from.

The hand-over numbers the features differently from the tracker. Its feature 2 (the column model
and guide) is specification 039, https://github.com/FAIR-DM/fairdm/issues/695. Its feature 1 (this
one) is specification 040. Its feature 3 (import) is specification 041,
https://github.com/FAIR-DM/fairdm/issues/697. They are built in the order 039, 040, 041.

The prototype's export code is `fairdm/contrib/tabular/mixins.py` (`RecordTransferMixin`),
`fairdm/contrib/tabular/exports.py` (`export_response`, `rows_for`, `workbook`, `guide_rows`) and
`fairdm/contrib/tabular/templates/tabular/partials/table_actions.html`.

## The shared pieces this feature builds or reuses

Copied from the hand-over's table "The shared pieces", in its words. The first feature to need a
piece builds it; later ones reuse it and their plans cite it.

| Piece | Where in the prototype | What it becomes | Here |
|---|---|---|---|
| Import definition lookup (`ImportDefinition`, `get_definition`, `register`) | `fairdm/contrib/tabular/definitions.py` | The one place every import page, the export menu and the import record find a file's columns, resource, formats and export rows, by name. FairDM builds one per registered type, named after it. `register` lets a project add its own; nothing uses that yet. Built by feature 2, before anything else reads columns | Reused. The export finds a table's definition through it, and takes its columns, formats and export rows from it |
| Column model (`Column`, `TableSchema`, `schema_for`) | `fairdm/contrib/tabular/schema.py` | Part of the registry: a `ModelConfiguration.get_table_schema()` next to `get_resource_class()`, built by feature 2 | Reused. Headings, the guide rows and the allowed lists are read from it |
| Cell widgets (number, date, boolean, concept, sample, quantity, choice) | `resources.py` top half | import-export widgets in `fairdm/contrib/import_export/widgets.py`, feature 2 | Reused. Every cell is written by the widget import reads it with (the prototype's `render_cell`) |
| Export menu and `?export=` handling | `mixins.py` `RecordTransferMixin`, `partials/table_actions.html` | A mixin on `DataTableView`, feature 1; the menu a Cotton component | Built here |
| Excel workbook writer (data, guide, allowed lists) | `exports.py` `workbook` | Feature 1, reused by the template download in feature 3 | Built here, able to write the workbook with no rows (the prototype's `example=True`) for feature 3 |

The prototype's mixin also puts the Import button and its dialog into the same context
(`import_url`, `import_chooser`, `imports_url`). That part is feature 3's. This feature builds the
mixin and the menu so feature 3 can add the Import button beside the menu without changing either.

## The look is ported, never redrawn

From the hand-over's "The look", the files this feature ports and where each lands on `main`:

| Prototype file | Lands on `main` as |
|---|---|
| `fairdm/contrib/tabular/templates/tabular/partials/table_actions.html`, its Export menu | A Cotton component under `fairdm/templates/cotton/` placed in the records table title row. Feature 3 adds the Import button beside it |
| `fairdm/contrib/tabular/static/tabular/tabular.css`, the export menu's rules (`.tx-tools`, `.tx-menu`, `.tx-menu__panel`, `__title`, `__formats`, `__fmt`, `__hint`, `__foot`, `.tx-caret`) | FairDM's stylesheet `fairdm/static/css/fairdm.css`, with `tx-` replaced by a class name for the component in the stylesheet's own style (it names classes after the thing they draw, as `record-card` and `ov-` do) |
| `fairdm/contrib/tabular/static/tabular/tabular.js`, the menu's closing (a click outside, choosing a file, Escape returning focus) | FairDM's scripts under `fairdm/static/js/`, linked from `base.html`. The drop zone and one-submit parts are feature 3's |
| `fairdm/templates/record_lists/records.html`, its `page.actions` block | The same file on `main`: the block places the component when the table lists rows |
| `fairdm/contrib/collections/templates/collections/listing.html`, its `page.actions` block | The same file on `main` |

The plan names each of these. The screens to compare, at 390 and 1400 wide, are the hand-over's
"Samples tab with Export and Import" (`/datasets/<seeded>/samples/soilsample/`) and "Export menu
open, with a search active" (the same, `?q=peat`), and a portal-wide listing
(`/collections/samples/<type>/`). The Import button on those screens is feature 3's and is absent
until it lands.

## Sam's decisions that bind this feature

From the hand-over's "Decisions":

- "The export's first column is `portal_id`, and import matches by it, then by Local ID within the
  dataset. A name never matches."
- "Headings are the field names, and labels work as headings too, so exports stay stable when
  labels are translated."
- "A type with no `resource_fields` gets every editable field. A type with `resource_fields` gets
  those, plus the identifiers and whatever a new record needs." (Worked out by feature 2; the
  export writes what it gives.)
- "Measurements name their sample by portal ID, Local ID or a name unique in the dataset. The
  export adds a `sample_name` column for readers, ignored on import."
- "Every page goes through one lookup for what a file holds. The import pages, the Export menu and
  the import record all ask for an import definition by name."
- "The prototype runs on django-mvp 0.36 and django-mvp-forms 0.11, the versions `main` moved to in
  https://github.com/FAIR-DM/fairdm/pull/693, so what is built from it starts on the same versions."

## Faked or skipped

The hand-over's "Faked or skipped" marks no item for feature 1. The export runs in the request in
the prototype and the hand-over does not list that as faked; this specification keeps it
(decisions.md, D4).

## What it replaces

The unrouted export views in `fairdm/contrib/import_export/` are replaced by feature 3, which
removes that module's views, forms and templates together. This feature adds nothing to them and
does not depend on them.
