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

**ADR:** none — a reading of the request, nothing downstream inherits it.

## D2 — Who may import and undo

The edit level on the dataset, through the existing `dataset.import_data` permission, which the
record-level backend already grants at edit. Undo needs the same level and is not limited to the
person who ran the import: the dataset's team shares its data, and an import left by someone who
has since left the team must still be undoable.

**ADR:** none — superseded by D20 and local to this feature.

## D3 — Two stories

Importing a file and looking back over imports to undo one are the two things a person sets out
to do. Choosing the type, the options, matching, the check, the problems download and the
progress are all parts of importing a file, so they are scenarios under the first story. Past
imports and undo go together because a person opens past imports to find the import they want to
take back. There is no developer story: a portal's own types import with nothing written, which
is a scenario of the first story, and the lookup a portal could register its own definitions with
belongs to https://github.com/FAIR-DM/fairdm/issues/695.

**ADR:** none — how the work is split, not a structure of the code.

## D4 — The stored file is deleted when the import finishes

The prototype never deletes the uploaded file and names a retention rule as this feature's to
settle. Undo restores from what the import kept, not from the file, and the problems download is
only offered before an import finishes. So the file has no use once the import is imported,
undone, discarded or unreadable, and it is deleted then. Research files are often unpublished
data, so keeping copies nobody needs is a risk, not a convenience. The import's record, counts and
row outcomes stay, so past imports still says what happened.

**ADR:** none — a retention rule of this feature, recorded in the reference page.

## D5 — An import left unfinished for 30 days is discarded

Without this, an import abandoned at the check keeps its file for ever. Thirty days is long enough
for a person to come back to a file they are correcting, and a scheduled task does it, as the
portal's other scheduled work is done. It is a fixed period rather than a setting: no portal has
asked for another, and a setting can be added when one does.

**ADR:** none — a retention rule of this feature, recorded in the reference page.

## D6 — The import re-checks, and goes back to the check when the outcome differs

The request promises that a person sees what the file would do before anything is saved. If the
dataset changes between the check and the import (another import, an edit by hand, a deleted
record), writing the file anyway would save something the person never saw. So the import works
through the file again inside its transaction, and if any row's outcome differs from the check it
saves nothing and shows the new outcomes. Imports of one dataset write one at a time, so two
started together cannot interleave.

**ADR:** none — local to this feature's runner.

## D7 — Undo is refused on any change since, not only an edit

The prototype checks the records' modification times only, which it names as this feature's to
settle. A modification time misses a change made without saving the record (a bulk update) and a
record deleted since. Undo is refused when any record the import added or changed has been changed
or deleted since by any means, or a sample it added has measurements, and it is all or nothing:
a partial undo leaves a dataset in a state nobody chose. How a change is detected is for the plan.

**ADR:** none — carried by the ADR for D18.

## D8 — Undo follows the portal's own rules for deleting and changing

Undo deletes records and changes values, so it is refused wherever the portal would refuse the
same deletion or change by hand, for instance on a published dataset. The feature adds no rule of
its own about publication.

**ADR:** none — superseded by D20.

## D9 — File limits and the sheet read

20 MB and 50,000 rows, as the prototype set them, and the first sheet of a workbook, which is
where the template and the export write the data, ahead of the guide and the allowed values. A
semicolon-separated CSV is read as well as a comma-separated one, because spreadsheet programs in
many European locales write one.

**ADR:** none — limits of this feature, recorded in the reference page.

## D10 — Row outcomes are browsed a page at a time

The prototype keeps every row's outcome on the import record and shows them by outcome a page at
a time. A 50,000-row file makes that record large, and the prototype names how to store them as
this feature's to settle. The specification fixes what a person sees (every row's outcome, by
outcome, a page at a time) and leaves the storage to the plan.

**ADR:** none — a page's behaviour, local to this feature.

## D11 — Progress is shown without reloading

The prototype keeps progress in the cache and polls every second, which it names as this
feature's to settle. The specification asks only that the page show how far a check or import has
got and move on by itself when it ends. How progress is kept and fetched is for the plan.

**ADR:** none — carried by D17.

## D12 — What leaves `fairdm/contrib/import_export/`

The import views, forms and templates, `BaseFairDMResource` and its sample and measurement
resources, and the registry's `ResourceFactory`. The dataset publish confirmation stays, because
https://github.com/FAIR-DM/fairdm/issues/347 decides it. Export views and templates there are
https://github.com/FAIR-DM/fairdm/issues/696's to keep or remove.

**ADR:** none — a removal list, recorded in the changelog.

## D13 — The fix to `LocatedResourceMixin.import_instance` ships here

The mixin returns early when a row has no location columns, dropping every problem found in the
row's other fields. The import relies on every problem being reported, so the fix is part of this
feature rather than a separate change, as the prototype hand-over assigns it.

**ADR:** none — a bug fix, recorded in the changelog and its tests.

## D14 — Glossary terms

The build adds to `CONTEXT.md`: **Import** (one file uploaded into one dataset, from upload to
outcome), **Import definition** if https://github.com/FAIR-DM/fairdm/issues/695 has not already
added it, and **Local ID** (the creator's own identifier for a sample or measurement within its
dataset), which the request uses and the glossary does not yet define.

**ADR:** none — glossary entries live in CONTEXT.md.

## D15 — The heading matcher is its own module, not a method of the schema

The prototype's column model had `match(heading)`. On `main` the column model is FS-039's, and the
import's rules (which column a heading means, which matches stop an import) belong to the import.
`matching.py` takes a `TableSchema` and reads its columns' name, label, label without unit and
aliases. Nothing in `schema.py` changes.

**ADR:** none — local to this feature, nothing downstream
inherits it.

## D16 — Row outcomes are a table of rows

`ImportRow` holds one row of a check each, with an index on the outcome. A 50,000-row file kept as
one JSON value would be read whole by every page and every progress poll. The page reads one page
of one outcome with a filter and a slice. The rows are replaced when a file is checked again. The
cost is a second table and one `bulk_create` in chunks.

**ADR:** docs/adr/0046-an-import-keeps-one-row-per-file-row-with-its-outcome.md

## D17 — Progress stays in the cache and is fetched by HTMX

The check's progress is written while the dry run's transaction is open, and a database column
written on the same connection is rolled back with it. The Redis cache the portal already runs
holds it. The page asks for it with `hx-trigger="every 1s"` and the status view answers
`HX-Refresh: true` when the run is over, so the person never reloads and the portal carries no
polling script of its own.

**ADR:** none — local to this feature.

## D18 — Undo compares a digest of each touched record's stored values

A record's `modified` is not enough (D7): a bulk update skips it and a deletion leaves nothing to
compare. The import stores, for each record it adds or changes, a digest of every concrete field's
stored value taken inside its transaction after the save. Undo recomputes it, and a missing record
or a different digest stops the undo. Any save, even one that changes no value, moves `modified`
and so counts as a change since.

**ADR:** docs/adr/0047-undo-compares-a-digest-of-each-touched-record.md

## D19 — The registry's resource component is removed with its factory

FR-023 replaces `ResourceFactory` with the dataset-bound resource. The `resource` component, the
`resource_class` configuration option and `ModelConfiguration.get_resource_class()` go with it,
since nothing would call them and the specification gives a portal no way to define its own import
resource. `resource_fields` stays because the column model reads it. A portal that set
`resource_class` has a configuration key the registry no longer reads, which the changelog states
under "Removed".

**ADR:** none — a removal, recorded in the changelog.

## D20 — Undo asks for the change permission, not the delete permission

Q1 of the specification lets anyone with the edit level undo, and FR-026 refuses where the portal
would refuse the change by hand. The portal holds a record's deletion at the manage level and its
change at the edit level. Reading "by hand" as a deletion would make an import that added records
impossible to undo for the people the specification names. The import itself added those records
at the edit level. So undo asks `change_<model>` of each record it touches, which an edit-level
person holds, and refuses a record the person may not change. The portal has no rule about a
dataset's published state that blocks a change, so there is nothing more to read. Ruled on Sam's behalf by the
orchestrator (2026-11-24): undo needs only the dataset's import permission. It takes back only what
that import did and is refused once any of those records has been changed since, so it never
deletes a record that existed before the import and gives nobody a delete they did not already
have. The per-record permission check is dropped.

**ADR:** none — local to this feature.

## D21 — The stored rows keep no cell of the file

`ImportRow` holds the outcome, changes, problems, the record and its digest, and no copy of the
file's cells. The problems workbook is built by reading the stored file again, which exists while
an import can still have problems. When the file is deleted, the values shown on column matching
are cleared with it, so no cell outlives the file (D4).

**ADR:** none — local to this feature.

## D22 — The new modules are one class each

The constitution asks for classes, so the file reader is `FileReader`, the heading matcher is
`HeadingMatcher(schema)`, the check and the import are `ImportRun(job)` and the undo is
`ImportUndo(job)`. No base class.

**ADR:** none — a code layout choice local to this feature.

## Watch items from the design review

Each is folded into the plan or a task. The build briefs carry the ones that bind code.

- Job pages look the job up through the dataset and POST actions move the status with one
  conditional update (plan, "Pages").
- `Dataset.all_objects` takes the lock, since the default manager hides private datasets.
- The digest and `before` come from a fresh read after the writes, in `value_to_string` form.
- Celery limits on both tasks, caught `SoftTimeLimitExceeded`, a timed 50,000-row run.
- Duplicates are found by the resolved record, and an empty required cell is a row problem.
- The problems workbook goes through `TableExport.write_text`.
- Reading stops at 50,001 rows and refuses an oversized uncompressed sheet.
- A `post_delete` receiver deletes the stored file.
- The upload is parsed before the job is created.
- Undo conflicts are computed on the undo POST, and `plugins.py` is edited by Groups 7 and 9 in
  sequence, never together.

## D23 — Job status names stay on `ImportJob.Status`, and the job address waits for its route

**Decision:** `ImportJob.Status.choices` is the one mapping from a status to its title, so no
separate `STATUS_LABELS` dictionary exists. `ImportJob.get_absolute_url` is added in the group
that adds the job route, because the address it reverses does not exist yet and a property that
cannot be called is untestable. `UploadForm` holds the 20 MB limit and the four extensions until
`FileReader` exists.

**Why:** A `TextChoices` label is already one name per state, which is what the plan's
`STATUS_LABELS` is for. A second dictionary would be a second copy.

**Revisit if:** the badge and the page title need different words for one status, or
`FileReader` lands with its own limit (the form should then read it, not repeat it).

**ADR:** none — a naming choice inside one module.

## D24 — `build_resource` returns the resource, and a row's note, changes and record are three maps

**Decision:** `build_resource(schema, dataset, ...)` and `ImportDefinition.resource(dataset, ...)`
return a `RecordResource` instance, not a class. The resource keeps `notes` (why a row was left
out), `changes` (the cells of an updated row, from `changed_cells`) and `record_pks` (the stored
record each row matched), each by row number. The prototype held notes and changes in one map of
mixed values.

**Why:** The call already takes the dataset and the options, which only an instance holds, and one
instance per file is what gives each file its own sample cache. Three maps of one kind each need
no `isinstance` at the reader, and `record_pks` is what the runner needs to find two rows that
mean one record.

**Revisit if:** a caller needs the class itself, for instance to subclass it for a project's
type.

**ADR:** none — local to this feature's resource module.

## D25 — an import refuses a file with problem rows, and a run is its own class

**Decision:** `ImportRun.confirm` raises `DatasetChanged` when any row the import's own run read is a problem, as well as when a row's outcome or changes differ from the check's. `check_job` does nothing unless the job is `checking`. The undone and discarded states delete the file through `ImportRun.delete_file`, which groups 7 and 9 call.

**Why:** a job in `importing` with problem rows would otherwise match the check's own problem rows and end as `imported` with nothing written. A queued check that arrives after the job moved on would replace the rows of an imported job.

**Revisit if:** the pages stop being the only way a job reaches `importing`.

**ADR:** none — local to this feature's runner.

## D26 — undo runs in the request, claimed under the dataset lock

**Decision:** the `undo` action calls `ImportUndo.undo` in the request. The job has no `undoing` status, so the claim is made inside the undo: the dataset row is locked, the job is read again, and the status moves from `imported` to `undone` with one conditional update after the records are changed, in the same transaction. A second post finds the job undone and changes nothing.

**Why:** an `undoing` state needs a change to the `status` choices and so to `models.py` and a migration, outside this group. Undo also refuses before it writes, so there is no state worth showing while it runs.

**Revisit if:** an undo of a 50,000-row import is measured at the browser pass to outlast a request, which would make it a task with an `undoing` status.

**ADR:** none — local to this feature, revisit if the measured time says otherwise.

*Section end: superseded by D29.*


## D27 — undo is confirmed in a dialog, as the prototype draws it

**Decision:** the Undo button on an imported job opens a dialog that says what the undo deletes and restores, with "Keep it" and "Undo the import". The post of the `undo` action is unchanged and sits in the dialog's form.

**Why:** the look comparison with the prototype found undo posting at once, on the one action that deletes records. The prototype asks first, and the plan carries the prototype's look into `main`.

**Revisit if:** the pages stop carrying a destructive action behind a button of this kind.

**ADR:** none — local to this feature.

## D28 — measured at the browser pass: the undo of 50,000 rows outlasts a request

**Decision:** nothing is redesigned here. On the branch's server a 50,000-row import of the simplest sample type was checked in 226 s and imported in 274 s by the worker. The job page of the imported job took 11.3 to 12.3 s to load (it scans every row to decide whether Undo shows) and the undo post took 43.4 s.

**Why:** D26 named this measurement as the trigger to revisit. The undo is over the 15 s the browser pass allows, so it is reported as a finding, not fixed in the pass.

**Revisit if:** now. A task with an `undoing` status, and a job page that decides whether Undo shows without reading every row, are the two changes the numbers point at.

**ADR:** none — the revisit decides whether one is needed.

## D29 — undo is a task with an undoing status (supersedes D26)

**Decision:** `ImportJob.Status` gains `undoing`. The `undo` action claims an `imported` job on the dataset with one conditional update to `undoing` and queues `undo_job(job_pk, user_pk)`, so a double post starts one task. The task runs `ImportUndo.undo`, which keeps its transaction, its dataset lock and its all-or-nothing refusal, and moves the job from `undoing` to `undone` in that transaction. A refusal returns the job to `imported` with the records in the way written to its `error`, one line each with a last line counting the rest, and an unexpected error or a time limit returns it to `imported` with a plain message. The job page shows the Undo button on every imported job without reading any record and shows the refusal after the task. Progress is the cache count that checks and imports use. The stale-job discard leaves undoing jobs alone, and the branch's one migration is regenerated.

**Why:** D26's revisit condition was met at the browser pass: on a 50,000-row import the job page took 11 to 12 s to load, because it scanned every added or changed row to decide whether the Undo button shows, and the undo post took 43 s inside the request, which a web server's request timeout cuts off.

**Revisit if:** a stuck `undoing` job needs a way back that does not wait for a person to look at the database.

**ADR:** none — local to this feature.
