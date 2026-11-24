# Records import

A person with the edit level on a dataset imports a file of one registered sample or measurement type into it. This page describes what the import stores and how the options form is built. The columns of a file come from the type's [table schema](table-schema.md), and the generated API reference describes every class and argument in [`models`](api/fairdm/fairdm.contrib.import_export.models.md) and [`forms`](api/fairdm/fairdm.contrib.import_export.forms.md).

## What an import stores

`ImportJob` is one file uploaded into one dataset, from upload to outcome. It holds the dataset, the registered type's name, who uploaded it, the stored file, the two options, the column map and a status. The status is one of matching columns, checking, ready to import, nothing to change, needs changes, importing, imported, undone, discarded or failed. The stored file is deleted when the import ends in imported, undone, discarded or failed, and deleting a job deletes it too, so a deleted dataset leaves no file behind. The values shown beside each heading on the column matching page are cleared with the file.

`ImportRow` is the outcome of one row of the file: new, update, unchanged, left out or problem. It holds the row's number and line in the file, the record it resolves to, the cells that change, the problems found, and what undo needs: the values an update replaced and a digest of the record's stored values after the import. A row keeps no cell of the file. A job lists its rows through `job.rows`, in file order, and a dataset lists its jobs through `dataset.import_jobs`.

## The options

`ImportOptionsForm` asks two questions with a card for each choice. What the file may do is add new records and update existing ones, only add, or only update. What an empty cell means is keep the stored value or clear it. `ImportOptionsForm(brief=True)` leaves each card's explanation out, for the column matching page where the choices are already known. `chosen(mode, empty)` returns the two choices the form holds, or the two it is given when the form is unbound or a choice is missing.

`UploadForm` reads the file of an import. It refuses a file over the size limit or of a format the import does not read.

## Reading a file

`FileReader` turns the bytes of a file into headings and rows. Every method is a class method, so nothing is kept between calls. The generated API reference describes each argument in [`reader`](api/fairdm/fairdm.contrib.import_export.reader.md).

`FileProblem` is the error for a file that cannot be imported. Its message says why in the active language, and its `code` names the reason: `format`, `too_large`, `too_large_unpacked`, `unreadable`, `empty`, `no_rows` or `too_many_rows`.

The class attributes hold the limits and the formats:

- `FORMATS` lists the formats read: `csv`, `tsv`, `xlsx` and `ods`. JSON and `.txt` files are refused.
- `MAX_BYTES` is the largest file, 20 MB. `MAX_ROWS` is the most data rows, 50,000.
- `MAX_UNCOMPRESSED` is the largest a workbook's or spreadsheet's first sheet may be once unpacked. `SHEET_ENTRIES` names the archive entry that holds the first sheet of each of the two formats.
- `MAX_REPEAT` is the most empty cells one repeated cell of an OpenDocument row expands to.
- `ENCODINGS` lists the text encodings tried in order: UTF-8 with or without a byte order mark, then Windows-1252, then Latin-1.

`file_format(name)` names a file's format by its extension in any case. `parse(raw, fmt)` returns the headings, the rows and the line of the file each row came from. Headings are trimmed text with empty ones at the end dropped. Each row is cut or filled with `None` to the number of headings, and rows with no value are left out, so a line number counts them. The first row with a value holds the headings, so a blank first line is skipped.

`parse` reads through `read_grid(raw, fmt)`, which returns every row as a list of cells and stops one row past `MAX_ROWS` instead of reading to the end of the file. It reads through `read_csv`, `read_xlsx` and `read_ods`. A comma-separated file's delimiter is sniffed between a comma and a semicolon, and a tab is never its delimiter. An Excel workbook is read through openpyxl's read-only mode, first sheet only.

An OpenDocument spreadsheet is read with odfpy and never with tablib, which drops repeated rows and fails on a second sheet. `read_ods` reads the first table only. `ods_rows` repeats a row as many times as it is repeated, and `ods_cells` repeats a cell likewise, giving text, a number, a date as text, a truth value or `None`.

An Excel or OpenDocument file whose first sheet is larger than `MAX_UNCOMPRESSED` once unpacked is refused before it is opened. `check_unpacked(raw, fmt)` reads the size from the archive's index. `decode(raw)` reads the bytes of a text file in `ENCODINGS`, `blank(cell)` says whether a cell holds nothing, and `limited(rows)` is the iterator that stops a read at the row limit.

## Matching headings

`HeadingMatcher(schema)` finds the column each heading of a file means, for the [table schema](table-schema.md) of one type. Its `schema` attribute is that schema, and its `keys` attribute is the column each normalised heading means. The matcher reads the schema and changes nothing in it. The generated API reference describes each argument in [`matching`](api/fairdm/fairdm.contrib.import_export.matching.md).

`normalise(heading)` reduces a heading to its lower-case letters and digits, so `Rock type`, `rock_type` and `ROCK-TYPE` are the same. `match(heading)` returns the column a heading means, or `None`. A heading means a column by its name, its label, its label without a unit in brackets at the end, or one of its aliases. A column written on export only is never matched.

Where two columns claim the same words, the first column of the schema keeps them. `Sample ID` is an alias of both the Local ID and a measurement's sample column, so it goes to the Local ID.

`match_columns(headings)` matches a whole file and returns the column name of each heading. The first heading to take a column keeps it, and a second heading for the same column, or one that means no column, is an empty string.

`problems(job)` lists what stops the matched columns from being checked: no column matched, two headings matched to one column, a column a new record needs left unmatched unless the job only updates, and a job that only updates with neither the portal ID nor the Local ID matched. `warnings(job)` lists what is worth knowing and does not stop the check: a job that adds and updates with no identifier column, and a latitude matched without a longitude or the reverse. `needs_matching(job)` is true when a heading of the job is matched to no column or `problems` is not empty. A warning alone leaves the matching to be skipped.

## Importing rows

`ImportDefinition.resource(dataset, **options)` builds the resource that imports a file of the definition's type into a dataset. It passes the options to `build_resource(schema, dataset, mode="both", empty="keep", user=None, columns=None)`, which builds a `RecordResource` that reads only the columns the file has, named by `columns`, and returns it. Each call builds new widgets, so the resource of one file shares nothing with the resource of another. The generated API reference describes each argument in [`resources`](api/fairdm/fairdm.contrib.import_export.resources.md).

`RecordResource` is a django-import-export `ModelResource` that reads and writes each cell through its column's widget. Its `schema`, `dataset`, `mode` and `empty` attributes hold what it was built from. Rows are numbered from 1 in file order, and `row_number` is the one being imported. After an import, `notes` holds why a row was left out, `changes` holds the cells each updated row changes, and `record_pks` holds the primary key of the stored record each row matched, so a caller can find two rows that mean one record. A row that adds a record has no entry in `record_pks`, as its record has no key until it is saved. `on_row` is a function called with `rows_done`, the number of rows imported so far, after each row.

A row finds its record in `get_instance(instance_loader, row)`. A portal ID is looked up first, among all samples or all measurements whatever their type, and `located` holds the record it names. Without a portal ID the Local ID is looked up within the dataset. A name never finds a record. `base_model` is `Sample` or `Measurement`, the model a portal ID is looked up in. A portal ID that names no record, a record of another type, or a Local ID held by several records, raises `RowProblem`. A portal ID that names a record of another dataset leaves the row out, through `leave_out_other_dataset()`, with a note, and a measurement's note says that it may name a sample of another dataset in the sample column. `init_instance(row)` starts a new record in the dataset.

`import_instance(instance, row, **kwargs)` first calls `settle_empty_cells(instance, row)` and then reads the cells. A new record has nothing to clear, so its empty cells are dropped and the model's defaults stand. A stored record keeps its value where a cell is empty, unless `empty` is `clear`. An empty cell in a column a new record needs, or one that would clear a column the record needs, raises `RowProblem`. Problems found reading the cells are reported together for the row, whether or not the file has location columns. `skip_row(instance, original, row, import_validation_errors)` leaves out a row that the mode does not ask for, with a note, and a stored record's row that changes nothing, without one.

`RowProblem(column, message)` is the error a row's lookup or empty cell raises. Its `column` is the heading of the column the problem is in and its `message` says what is wrong, so the check can show it beside that column.

`changed_cells(schema, original, instance, row)` lists the cells a row changes in a stored record. It compares the columns the row has, as the cells an export would write, and returns a dict of `column`, `label`, `old` and `new` for each one that differs.

`SampleCellWidget` reads a measurement's sample cell once for each distinct text. `found` holds, for each cell read so far, the sample or the refusal it came to, and `look_up(text)` does the lookup that fills it. A widget serves one file, so its `found` is empty when the file starts.

## Checking and importing a file

`ImportRun(job)` runs the check or the import of one `ImportJob`. Its `job` attribute is the job. `run(dry_run, user)` reads the job's file once, keeps the columns the job's column matches name, runs the type's resource over the rows and returns the unsaved `ImportRow` of every row, plus the record key and stored state before the import of every row the import wrote. The generated API reference describes each argument in [`runner`](api/fairdm/fairdm.contrib.import_export.runner.md).

`check()` runs the file as a dry run, so nothing is written to the dataset, and replaces the job's rows with the outcome of every row: new, update, unchanged, left out with its note, or a problem with each column that has one. A row whose record another row is also about is a problem, whether the two rows name the record by portal ID, by Local ID or one of each. The job ends as `problems` when any row is a problem, as `checked` when the import would write a record, and as `nothing` otherwise. A file that cannot be read ends the job as `failed` with the reason in `error`, and its file is deleted.

`perform(user)` writes the rows the check showed, in one transaction. It locks the dataset row first, so the imports of one dataset write one at a time, and then reads the job again and does nothing unless its status is `importing`. It compares each row's outcome and changes with the check's rows. When any differs, nothing is saved, the rows are replaced with the new outcomes, and the job returns to `problems`, `checked` or `nothing` with an `error` that says the dataset changed since the check. Otherwise it reads every written record back in chunks of 500 and keeps its key, portal ID and digest on the row, and for an updated record the stored values it replaced in `before`, each written with `field.value_to_string` so a restore reads it with `field.to_python`. The job then ends as `imported` and its file is deleted.

`progress()` returns how many rows the running phase has finished, as of the last ten, or `None` when no phase is running. `progress_key` is the cache key it reads, and `write_progress(done)` writes it. `delete_file()` deletes the stored file and clears the job's example values, so no cell of the file outlives it. `fail(message)` ends the job as failed, and `stop(message)` returns an import that ran out of time to `checked`. `DatasetChanged` is the error `confirm(rows)` raises when the import's rows differ from the check's, and its `rows` attribute holds the import's own rows.

`ImportUndo(job).digest(record)` is the SHA-256 of the canonical JSON of every concrete field of a record, each written with `field.value_to_string`. `modified` is one of the fields, so a save that changes nothing still changes the digest. Read the record from the database before calling it.

`ImportUndo(job).conflicts(user, limit=20)` lists the records that stand in the way of an undo: a record that no longer exists, one whose digest differs from the one the import stored, and a sample the import added that now has measurements. It returns a dict with `entries`, up to `limit` dicts of `pk`, `label` and `reason` (`deleted`, `changed` or `measurements`), and `more`, the count of the records beyond the limit. It reads no per-record permission: whoever holds the dataset's `import_data` permission may undo.

`ImportUndo(job).undo(user)` locks the dataset row with `select_for_update()`, reads the job's status again and, when the job is still `imported` and nothing is in the way, deletes the records the import added (one `delete()` per chunk of 500, through the type's manager, so signals and polymorphic children fire) and restores each changed record's stored values with `setattr(record, field.attname, field.to_python(value))` and a save, all in one transaction. It then sets the status to `undone`, records `undone_at` and `undone_by` and deletes the file if one is left. It returns `None` when the job is not imported, and the result of `conflicts` otherwise, which has no entries once the undo is done. When anything is in the way, nothing is changed.

`tasks.discard_stale_jobs` discards the jobs left in matching, checking, checked, nothing to change or needs changes for 30 days, and deletes their files. Their rows stay. The app schedules it daily at 02:30 through a `PeriodicTask` created after `django_celery_beat` migrates, and never touches one that exists, so a portal may change its schedule or switch it off.

The tasks in `fairdm.contrib.import_export.tasks` run the two phases on the portal's worker. `check_job(job_pk)` checks a job that is `checking`, and ends it as failed when it runs out of time. `import_job(job_pk, user_pk)` imports a job, and a job that runs out of time has written nothing and returns to `checked`. Each task carries its own `soft_time_limit` and `time_limit`, set in `CHECK_LIMITS` and `IMPORT_LIMITS`. `start(task, *args)` queues a task when the current transaction commits, queues nothing when it rolls back, and never runs the task in place: the portal runs a worker.

## The import pages

`fairdm.contrib.import_export.plugins` registers the import pages on a dataset with `@plugins.register(Dataset, menu=False)`, so they have no menu entry of their own. Every page answers a person without the dataset's `import_data` permission with a 404, and a job is only ever read through the dataset's own `import_jobs`, so another dataset's job is a 404 too.

`can_import(request, dataset)` is the permission check every page uses. `import_chooser(dataset, kind=None)` builds the data of the dialog that lists the types a person can import: its `id`, a `title` and `groups` of entries, each with the type's `name`, row `count`, `url`, whether it is `required` and the number of `columns` a file can have. `kind` limits it to samples or measurements.

`ImportPage` is the base of the pages that belong to a dataset's imports, and `DefinitionMixin` finds the `ImportDefinition` a page's address names. `ImportStart` is the page at `import/<type>/` that takes the options and the file. It reads the file with `FileReader.parse` before it saves a job, so a refused file shows its problem on the same page and leaves no job. A job whose headings all match goes to `checking`, and one with a heading that needs matching goes to `matching`. `ImportTemplate` downloads the type's template as Excel or as a CSV with only the headings.

`DatasetImports` is the page at `imports/` that lists the dataset's jobs, newest first, with the Import dialog. `JobPage` is the base of the pages of one job, `JobColumns` is the matching page at `imports/<job>/columns/`, and `JobDetail` is the job itself at `imports/<job>/`. `JobDetail` runs the actions the job's status allows (`import`, `recheck` and `discard`) with one conditional update of the status, and queues the task only when that update changed a row, so a second post does nothing. The `undo` action runs in the request: it calls `ImportUndo.undo`, which checks the status under the dataset lock, so a second post finds the job undone and changes nothing. When records are in the way the job's page is shown again with up to 20 of them named and a count of the rest, and the Undo button is not shown on an imported job whose records have changed. It lists the job's rows by outcome, 100 to a page, with `?show=` for the outcome and `?page=` for the page. `JobStatus` at `imports/<job>/status/` answers the progress component's poll, and answers with an `HX-Refresh` header once the run is over. `JobProblems` at `imports/<job>/problems.xlsx` downloads the file's own rows with a column of their problems, for a job that ended as `problems`. It reads the stored file again and writes every cell as text.

`ImportJob.get_absolute_url()` is the address of the job's page.

The pages are built from the components in `fairdm/templates/cotton/import/`: `c-import.steps`, `c-import.progress`, `c-import.panel`, `c-import.tag`, `c-import.outcome-badge`, `c-import.job-list`, `c-import.alert`, `c-import.choice`, `c-import.downloads` and `c-import.import-menu`. Each component's file lists its props and slots in its own annotations.

`c-import.import-menu` takes a `chooser`, the dict `import_chooser` returns, and a `label`. It draws the Import button and, on `c-mvp.modal`, a dialog whose id is the chooser's `id` and which links each type to its import page. The Samples and Measurements tabs of a dataset put the button beside the Export menu for a person holding `dataset.import_data`, and in the empty state of an empty tab. A tab whose address names a type links straight to that type's import page instead, using `import_url`. `RecordsTab.import_context()` builds `import_url` and `import_chooser` for the page, and both are `None` on a project's or a contributor's tab and for a person who may not import.
