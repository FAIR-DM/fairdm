# Decisions: export the rows of any records table

Every reading below was made while the specification was written, from the issue, the prototype
and its recorded decisions. Each is open to veto at the specification review.

## D1. The feature is one story

Choosing a format, choosing the rows, the Excel guide and lists, the file name and the keyboard
behaviour are all part of one thing a person sets out to do: download a table's rows. They are
scenarios under one story. No developer story was written: a portal gets Export on its tables by
registering its types, which it already does, so no developer gains a new thing to do. Adding a
project's own import definition is specification 039's, and nothing uses it yet.

## D2. "The rows the filters show" is every matching row, not the page on screen

The prototype drops the page number from the export address, and a person who has searched a
table wants what the search found. Exporting one page of 25 would be a surprise.

## D3. Rows are in a stable record order, not the table's sort

The prototype writes rows in the order the records were created. A stable order lets two exports
be compared line by line and keeps the file the same when only the viewer's sort changed. The cost
is that a person who sorted the table sees a different order in the file. Sorting the file is one
click in any spreadsheet.

## D4. The export is written while the request waits

The prototype writes files in the request, reading records in batches of 500, and the hand-over
does not list that among what was faked. R21's background work is for imports. A background export
with progress would add a job model, a queue and a status page to a feature that owns no models.
If large tables prove slow, that is a later change to how the file is written, not to what it holds.

## D5. Anyone who can see the table can export it

The issue says "anyone who can see a records table". An export holds no more than the table
already shows that viewer, so it reveals nothing new. Signing in is not required.

## D6. "Every row" means every row this table lists for this viewer

Not every record of that type in the portal. On a dataset's tab it is the dataset's records; on a
portal-wide listing it is what that listing lists. The prototype uses the table's own query.

## D7. The column naming a measurement's sample holds the sample's name

The issue names it `sample_name`. Its heading and position come from specification 039's columns,
where it is marked as written on export and not read on import. This specification requires only
that it is present and filled.

## D8. Count on the shown rows, none on every row

With a search active the menu says how many rows the shown choice holds, as the prototype does,
because that number is what tells the two choices apart. The wording is not specified.

## D9. Export is part of the records table view, so a portal's own table gets it

The prototype adds the mixin to `DataTableView`, which every records tab and listing uses. A
portal that builds a table on it gets Export without configuration (G2). A table for a type with no
import definition offers no Export menu.

## D10. No export from a table that lists no rows

The empty state is where the Import button will go (specification 041 and the fix in
https://github.com/FAIR-DM/fairdm/issues/698). An empty file has nothing for anyone; the empty
template download is specification 041's.
