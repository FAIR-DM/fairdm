# Decisions: import a spreadsheet of samples or measurements into a dataset

Each decision below was made without putting it to the maintainer, from the request, the
prototype he has seen and accepted, and his decisions on
https://github.com/FAIR-DM/fairdm/issues/692. Each can be overturned before the build starts.

## D1 — What the feature is, as read from the request

A person with the edit level on a dataset imports a file of one registered sample or measurement
type into it: they choose the type, upload the file, match its columns where needed, see what
every row would do, import it whole, look back over the dataset's imports and undo one. The
screens and rules are the prototype's, which the maintainer has seen and accepted, and this
specification describes what they do rather than reopening them.

## D2 — Who may import and undo

The edit level on the dataset, through the existing `dataset.import_data` permission, which the
record-level backend already grants at edit. Undo needs the same level and is not limited to the
person who ran the import: the dataset's team shares its data, and an import left by someone who
has since left the team must still be undoable.

## D3 — Two stories

Importing a file and looking back over imports to undo one are the two things a person sets out
to do. Choosing the type, the options, matching, the check, the problems download and the
progress are all parts of importing a file, so they are scenarios under the first story. Past
imports and undo go together because a person opens past imports to find the import they want to
take back. There is no developer story: a portal's own types import with nothing written, which
is a scenario of the first story, and the lookup a portal could register its own definitions with
belongs to https://github.com/FAIR-DM/fairdm/issues/695.

## D4 — The stored file is deleted when the import finishes

The prototype never deletes the uploaded file and names a retention rule as this feature's to
settle. Undo restores from what the import kept, not from the file, and the problems download is
only offered before an import finishes. So the file has no use once the import is imported,
undone, discarded or unreadable, and it is deleted then. Research files are often unpublished
data, so keeping copies nobody needs is a risk, not a convenience. The import's record, counts and
row outcomes stay, so past imports still says what happened.

## D5 — An import left unfinished for 30 days is discarded

Without this, an import abandoned at the check keeps its file for ever. Thirty days is long enough
for a person to come back to a file they are correcting, and a scheduled task does it, as the
portal's other scheduled work is done. It is a fixed period rather than a setting: no portal has
asked for another, and a setting can be added when one does.

## D6 — The import re-checks, and goes back to the check when the outcome differs

The request promises that a person sees what the file would do before anything is saved. If the
dataset changes between the check and the import (another import, an edit by hand, a deleted
record), writing the file anyway would save something the person never saw. So the import works
through the file again inside its transaction, and if any row's outcome differs from the check it
saves nothing and shows the new outcomes. Imports of one dataset write one at a time, so two
started together cannot interleave.

## D7 — Undo is refused on any change since, not only an edit

The prototype checks the records' modification times only, which it names as this feature's to
settle. A modification time misses a change made without saving the record (a bulk update) and a
record deleted since. Undo is refused when any record the import added or changed has been changed
or deleted since by any means, or a sample it added has measurements, and it is all or nothing:
a partial undo leaves a dataset in a state nobody chose. How a change is detected is for the plan.

## D8 — Undo follows the portal's own rules for deleting and changing

Undo deletes records and changes values, so it is refused wherever the portal would refuse the
same deletion or change by hand, for instance on a published dataset. The feature adds no rule of
its own about publication.

## D9 — File limits and the sheet read

20 MB and 50,000 rows, as the prototype set them, and the first sheet of a workbook, which is
where the template and the export write the data, ahead of the guide and the allowed values. A
semicolon-separated CSV is read as well as a comma-separated one, because spreadsheet programs in
many European locales write one.

## D10 — Row outcomes are browsed a page at a time

The prototype keeps every row's outcome on the import record and shows them by outcome a page at
a time. A 50,000-row file makes that record large, and the prototype names how to store them as
this feature's to settle. The specification fixes what a person sees (every row's outcome, by
outcome, a page at a time) and leaves the storage to the plan.

## D11 — Progress is shown without reloading

The prototype keeps progress in the cache and polls every second, which it names as this
feature's to settle. The specification asks only that the page show how far a check or import has
got and move on by itself when it ends. How progress is kept and fetched is for the plan.

## D12 — What leaves `fairdm/contrib/import_export/`

The import views, forms and templates, `BaseFairDMResource` and its sample and measurement
resources, and the registry's `ResourceFactory`. The dataset publish confirmation stays, because
https://github.com/FAIR-DM/fairdm/issues/347 decides it. Export views and templates there are
https://github.com/FAIR-DM/fairdm/issues/696's to keep or remove.

## D13 — The fix to `LocatedResourceMixin.import_instance` ships here

The mixin returns early when a row has no location columns, dropping every problem found in the
row's other fields. The import relies on every problem being reported, so the fix is part of this
feature rather than a separate change, as the prototype hand-over assigns it.

## D14 — Glossary terms

The build adds to `CONTEXT.md`: **Import** (one file uploaded into one dataset, from upload to
outcome), **Import definition** if https://github.com/FAIR-DM/fairdm/issues/695 has not already
added it, and **Local ID** (the creator's own identifier for a sample or measurement within its
dataset), which the request uses and the glossary does not yet define.
