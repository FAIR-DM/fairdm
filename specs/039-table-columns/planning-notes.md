# Planning notes

Notes for whoever plans and builds this feature. Each one is answered by name when the build is
researched.

## N1. The prototype this feature was specified from

The agreed design is the prototype on the `prototype-import-export` branch, described in
`PROTOTYPE.md` at that branch's root. This feature is its feature 2, "The column model and guide of a
type (the shared foundation)". The prototype's export is #696 and its import #697. Its screens, and
the maintainer's decisions recorded on https://github.com/FAIR-DM/fairdm/issues/692, are already
agreed. The branch is read, never merged and never branched from. Build order: this feature, then
#696, then #697.

## N2. The shared pieces this feature builds

From PROTOTYPE.md, "The shared pieces", in the hand-over's words. This feature is the first to need
each of them, so it builds them. #696 and #697 reuse them and their plans cite them.

| Piece | Where in the prototype | What it becomes |
|---|---|---|
| Import definition lookup (`ImportDefinition`, `get_definition`, `register`) | `fairdm/contrib/tabular/definitions.py` | The one place every import page, the export menu and the import record find a file's columns, resource, formats and export rows, by name. FairDM builds one per registered type, named after it. `register` lets a project add its own; nothing uses that yet. Built by feature 2, before anything else reads columns |
| Column model (`Column`, `TableSchema`, `schema_for`) | `fairdm/contrib/tabular/schema.py` | Part of the registry: a `ModelConfiguration.get_table_schema()` next to `get_resource_class()`, built by feature 2 |
| Cell widgets (number, date, boolean, concept, sample, quantity, choice) | `resources.py` top half | import-export widgets in `fairdm/contrib/import_export/widgets.py`, feature 2 |
| Column guide | `partials/guide.html` | Cotton component, feature 2 |

The prototype's `ImportDefinition.resource()` builds the dataset-bound resource, which is #697's.
This feature's definition carries the name, model, kind, formats and columns. #697 adds the resource,
and #696 uses the export rows.

`render_cell` (the cell an export writes for one column of one record) sits beside the widgets in
the prototype's `resources.py` and is part of what this feature builds: FR-007's round trip is
`render_cell` and the widget's `clean` meeting.

## N3. The shared pieces this feature does not build

None of these is built here. Each is named so nobody reaches for it in this feature:

- Import options form, dataset-bound resource, step bar and panels: #697.
- Export menu and `?export=` handling, Excel workbook writer: #696. The workbook writes the guide
  into the Excel file from this feature's columns.

## N4. The look this feature ports

From PROTOTYPE.md, "The look". Ported, never redrawn.

| Prototype file | Lands in `main` as |
|---|---|
| `fairdm/contrib/tabular/templates/tabular/partials/guide.html` | A Cotton component under `fairdm/templates/cotton/` (for example `cotton/import/guide.html`, beside the components #697 adds under `cotton/import/`), taking a table schema |
| `fairdm/contrib/tabular/static/tabular/tabular.css`, the column guide section (`.tx-guide*`, `.tx-allowed*`) and the small pieces the guide uses (`.tx-tag`, `.tx-tag--required`, `.tx-tag--key`, `.tx-code`, `.tx-code--example`, `.tx-alias`, `.tx-dim`, and the `--tx-*` colour variables they read) | `fairdm/static/css/fairdm.css`, with `tx-` renamed to the stylesheet's house prefix for this area (the overview pages use `ov-`). #696 and #697 port their own parts of `tabular.css` and reuse these |

`tabular.js` is not used by the guide and is ported by #696 and #697.

The guide's screen to compare, at 390 and 1400 wide: "Import page and guide",
`/datasets/<seeded>/import/soilsample/` on the prototype, seeded with
`DJANGO_ENV=development python manage.py seed_import_export_prototype` and signed in as
`regular.user@example.com`. Until #697 places the guide on the import page, the comparison is the
guide component rendered for `soilsample` on a page of the same width.

## N5. Carried from "Faked or skipped"

- The guide and match tables use ARIA table roles on divs, "which the rebuild should check or replace
  with real tables. Features 2 and 3." This feature's part is the guide: FR-014, SC-005, and
  decisions D7. The match table is #697's.

## N6. Duplication to remove

PROTOTYPE.md: "`engine.py` and `resources.py` both know the location column names." The four
location columns are declared once, in the column model, and everything else reads them from it.
`fairdm/utils/location/` on `main` already holds the location input and the import columns
(CONTEXT.md, Location): research whether the column model's location columns should be built from
there rather than written again.

## N7. Departures from the prototype the specification makes

- Examples never come from a stored record (decisions D4).
- The Table Schema lists every allowed value (D5).
- A sample the person may not see is refused as one that does not exist (D6).
- The Table Schema's address depends on the type alone and is open to anyone (D3). The prototype's
  `ImportSchema` view sits under the dataset's import page.
