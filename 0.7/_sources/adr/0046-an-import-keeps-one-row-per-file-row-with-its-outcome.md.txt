# ADR 0046: An import keeps one row per file row, with its outcome

**Status:** accepted

## Decision

A check of an uploaded file is stored as `ImportRow` records, one for each row of the file, in
a table of their own that belongs to the `ImportJob`. Each row holds its outcome (new, update,
unchanged, left out or problem), the changed cells of an update, the problems found and the
record it matched. The outcome column is indexed together with the job and the row number.

A page of the review reads one outcome with a filter and a slice. The rows are replaced when a
file is checked again. No cell of the file itself is stored, so deleting the file leaves nothing
of its contents behind.

## Why

A file may hold 50,000 rows. Kept as one JSON value on the job, the whole check would be read and
decoded by every page view and every progress poll. A table of rows lets a page ask the database
for the hundred rows it shows. The cost is a second table and a `bulk_create` in chunks.

## Revisit if

Files may grow far beyond 50,000 rows, which would make the chunked insert itself the slow part
of a check.
