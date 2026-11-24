# Decisions: export the rows of any records table

Every reading below was made while the specification was written, from the issue, the prototype
and its recorded decisions. Each is open to veto at the specification review.

## D1. The feature is one story

Choosing a format, choosing the rows, the Excel guide and lists, the file name and the keyboard
behaviour are all part of one thing a person sets out to do: download a table's rows. They are
scenarios under one story. No developer story was written: a portal gets Export on its tables by
registering its types, which it already does, so no developer gains a new thing to do. Adding a
project's own import definition is specification 039's, and nothing uses it yet.

**ADR:** none — local to this feature, nothing downstream inherits it

## D2. "The rows the filters show" is every matching row, not the page on screen

The prototype drops the page number from the export address, and a person who has searched a
table wants what the search found. Exporting one page of 25 would be a surprise.

**ADR:** none — local to this feature, nothing downstream inherits it

## D3. Rows are in a stable record order, not the table's sort

The prototype writes rows in the order the records were created. A stable order lets two exports
be compared line by line and keeps the file the same when only the viewer's sort changed. The cost
is that a person who sorted the table sees a different order in the file. Sorting the file is one
click in any spreadsheet.

**ADR:** none — local to this feature, nothing downstream inherits it

## D4. The export is written while the request waits

The prototype writes files in the request, reading records in batches of 500, and the hand-over
does not list that among what was faked. R21's background work is for imports. A background export
with progress would add a job model, a queue and a status page to a feature that owns no models.
If large tables prove slow, that is a later change to how the file is written, not to what it holds.

**ADR:** none — local to this feature, nothing downstream inherits it

## D5. Anyone who can see the table can export it

The issue says "anyone who can see a records table". An export holds no more than the table
already shows that viewer, so it reveals nothing new. Signing in is not required.

**ADR:** none — local to this feature, nothing downstream inherits it

## D6. "Every row" means every row this table lists for this viewer

Not every record of that type in the portal. On a dataset's tab it is the dataset's records; on a
portal-wide listing it is what that listing lists. The prototype uses the table's own query.

**ADR:** none — local to this feature, nothing downstream inherits it

## D7. The column naming a measurement's sample holds the sample's name

The issue names it `sample_name`. Its heading and position come from specification 039's columns,
where it is marked as written on export and not read on import. This specification requires only
that it is present and filled.

**ADR:** none — local to this feature, nothing downstream inherits it

## D8. Count on the shown rows, none on every row

With a search active the menu says how many rows the shown choice holds, as the prototype does,
because that number is what tells the two choices apart. The wording is not specified.

**ADR:** none — local to this feature, nothing downstream inherits it

## D9. Export is part of the records table view, so a portal's own table gets it

The prototype adds the mixin to `DataTableView`, which every records tab and listing uses. A
portal that builds a table on it gets Export without configuration (G2). A table for a type with no
import definition offers no Export menu.

**ADR:** none — local to this feature, nothing downstream inherits it

## D10. No export from a table that lists no rows

The empty state is where the Import button will go (specification 041 and the fix in
https://github.com/FAIR-DM/fairdm/issues/698). An empty file has nothing for anyone; the empty
template download is specification 041's.

**ADR:** none — local to this feature, nothing downstream inherits it

## D11. A measurement's sample name is written only where the viewer may open the sample

The table of a tab holds a measurement whose sample the viewer may not open and draws a dash for
the sample. The specification's edge case says such a measurement is not in the table, which the
code does not do. SC-004 and FR-005 decide it: an export holds nothing the viewer may not see, so
the `sample_name` cell is empty for such a row. The cell is read from the `sample_open` annotation
every records tab already puts on its rows. The portal-wide listing does not, so the export adds the
same annotation, and a row that has none gets an empty cell. This does not change the specification:
the column is "filled with the sample's name" wherever the viewer may see that name.

**ADR:** none — local to this feature, nothing downstream inherits it

## D12. Excel cells are always text, never formulas

openpyxl turns a string that starts with `=` into a formula. A name typed by a contributor and
downloaded by someone else would then run in their spreadsheet. The workbook writer stores every
string as text. CSV and TSV are written unchanged: a leading quote would change the value an import
reads back (FR-008), and the unchanged file is the round trip this feature exists for.

**ADR:** none — local to this feature, nothing downstream inherits it

## D13. No menu while the table lists no rows, including a search that matches nothing

The specification says a table that lists no rows shows no Export menu (FR-014). A search or
filter that matches nothing leaves such a table, so it shows none either, and the clear-search
control the table already has is the way back to the rows.

**ADR:** none — local to this feature, nothing downstream inherits it

## D14. The five formats are this feature's own list

The import definition's `formats` is the list of formats an import reads and has no JSON. Export
offers CSV, Excel, OpenDocument, TSV and JSON from a list in the export module, in that order.

**ADR:** none — local to this feature, nothing downstream inherits it

## D15. The menu's markup is wrapped by the page, not by the component

The component draws only the menu. The title row's block wraps it in an element of its own, so the
Import button of specification 041 sits inside the same wrapper without the component changing.

**ADR:** none — local to this feature, nothing downstream inherits it
