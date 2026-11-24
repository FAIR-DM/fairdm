# Records import

A person with the edit level on a dataset imports a file of one registered sample or measurement type into it. This page describes what the import stores and how the options form is built. The columns of a file come from the type's [table schema](table-schema.md), and the generated API reference describes every class and argument in [`models`](api/fairdm/fairdm.contrib.import_export.models.md) and [`forms`](api/fairdm/fairdm.contrib.import_export.forms.md).

## What an import stores

`ImportJob` is one file uploaded into one dataset, from upload to outcome. It holds the dataset, the registered type's name, who uploaded it, the stored file, the two options, the column map and a status. The status is one of matching columns, checking, ready to import, nothing to change, needs changes, importing, imported, undone, discarded or failed. The stored file is deleted when the import ends in imported, undone, discarded or failed, and deleting a job deletes it too, so a deleted dataset leaves no file behind. The values shown beside each heading on the column matching page are cleared with the file.

`ImportRow` is the outcome of one row of the file: new, update, unchanged, left out or problem. It holds the row's number and line in the file, the record it resolves to, the cells that change, the problems found, and what undo needs: the values an update replaced and a digest of the record's stored values after the import. A row keeps no cell of the file. A job lists its rows through `job.rows`, in file order, and a dataset lists its jobs through `dataset.import_jobs`.

## The options

`ImportOptionsForm` asks two questions with a card for each choice. What the file may do is add new records and update existing ones, only add, or only update. What an empty cell means is keep the stored value or clear it. `ImportOptionsForm(brief=True)` leaves each card's explanation out, for the column matching page where the choices are already known. `chosen(mode, empty)` returns the two choices the form holds, or the two it is given when the form is unbound or a choice is missing.

`UploadForm` reads the file of an import. It refuses a file over the size limit or of a format the import does not read.
