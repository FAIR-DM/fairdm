# Records export

Every table that lists the samples or measurements of one registered type has an Export menu in its title row. This page describes what the menu offers, what a file holds, who sees what, and how a portal's own table gets the menu. The columns of a file come from the type's [table schema](table-schema.md), and the generated API reference describes every class and argument in [`exports`](api/fairdm/fairdm.contrib.import_export.exports.md) and [`mixins`](api/fairdm/fairdm.contrib.import_export.mixins.md).

## Formats

`EXPORT_FORMATS`, in `fairdm.contrib.import_export.exports`, lists the five formats in the order the menu shows them: CSV, Excel, OpenDocument, TSV and JSON. Each is an `ExportFormat` with its key, label, hint, content type and extension. `format_for(key)` returns the format with a key, or `None`.

- CSV and TSV are UTF-8. CSV starts with a byte order mark so Excel reads text in any script, and an import must read a file with one.
- JSON is a list with one object per row, keyed by the column headings.
- Excel holds the rows on its first sheet, the guide to the columns on its second and the allowed values of each column that has a fixed list on its third. The cells of those columns offer the values, and each heading carries a note with the column's label, type, unit, how to write it and whether a new record needs it. Every string is stored as text, so a name that starts with `=` is never run as a formula.

`TableExport(schema)` writes a file. `TableExport(schema).workbook()` with no rows writes the same workbook with no data, which the import's template download uses.

## What a file holds

The headings are the type's file columns in their order, with the portal ID first. A cell is written by the widget an import reads the column with. Rows are in primary-key order whatever order the table is sorted in, so two downloads of the same data compare line by line.

A measurement file has a `sample` and a `sample_name` column. Both are empty for a measurement whose sample the viewer may not open, because the table draws neither.

## Which rows

Without a search or filter the menu offers every row the table lists for the viewer. With one it offers the matching rows from every page and every row. The address is `?export=<format>`, with `&scope=all` for every row. The page number is ignored. The search and filters are read as the table reads them, so the file and the table cannot disagree.

An export never holds a record the table would not list for that viewer. A request for a format that is not offered, or on a table that lists no type, answers 404 and sends no file. A table with no rows shows no menu.

## Giving a table the menu

`RecordExportMixin`, in `fairdm.contrib.import_export.mixins`, is the first base of `DataTableView`. A table built on `DataTableView` has the export without configuration. The mixin puts `export_menu` in the context, and the `<c-import.export-menu>` component draws it.

The menu opens without script. `fairdm/static/js/export-menu.js` closes it on Escape, which returns focus to its button, on a click outside and on choosing a file.
