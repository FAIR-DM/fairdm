# Feature Specification: Import a spreadsheet of samples or measurements into a dataset

**Feature Branch**: `041-records-import`

**Created**: 2026-11-23

**Status**: Draft

**Goals**: G11: round-trip import and export of tabular data. G2: registering a model is enough to
get a working portal surface. G6: core records can be created and edited through the portal.

**Roadmap**: R21, tabular data goes in and comes back out. This specification delivers its
import: reachable from the dataset it belongs to, validated before it writes, run in the
background with progress and failures per row, and able to take back a file the export wrote.

**Input**: https://github.com/FAIR-DM/fairdm/issues/697. A person who may change a dataset should
be able to fill it from a spreadsheet, see what the file would do before anything is saved, and
undo the import afterwards. A prototype of this is on the `prototype-import-export` branch,
described in its `PROTOTYPE.md`. Its record is https://github.com/FAIR-DM/fairdm/issues/692.

## What exists, and what this specification changes

On `main`, `fairdm/contrib/import_export/` holds import views, forms, templates and a
`BaseFairDMResource` that no address reaches. The registry builds a resource for every registered
type with `ResourceFactory`, and those resources leave out the identifiers and, for some types,
the sample. `LocatedResourceMixin.import_instance` returns early when a row has no location
columns, so every problem found in the row's other fields is dropped and the row is saved as if
it were valid. Nobody can import a file into a dataset.

After this feature:

- Every Import button in a dataset leads to an import of one registered sample or measurement
  type: straight to that type's import page from a single type's table, and through one dialog
  listing the types from everywhere else.
- A person who may change the dataset uploads a CSV, Excel, OpenDocument or TSV file, chooses
  what the file may do, matches its columns when they need matching, and sees what every row
  would do before anything is saved.
- A file with no problems is imported whole, in the background and in one transaction. A file
  with problems saves nothing and can be downloaded back with each row's problems written beside
  it.
- Each dataset lists its imports and their state, and an import can be undone while nothing it
  wrote has changed since.
- A row with problems in its fields and no location columns reports each of those problems.
- The unused import views, forms, templates and `BaseFairDMResource`, and the registry's
  `ResourceFactory`, are gone. Every registered type's resource reads and writes the columns of
  that type's column model, with nothing written by the portal.

## Boundary

- **The columns of a type** (which columns a file has, their headings, labels, recognised
  headings, types, units, allowed values and examples, the guide that shows them and the Table
  Schema download) are https://github.com/FAIR-DM/fairdm/issues/695. This feature reads them and
  places the guide on the import page.
- **Export** from a records table, its formats, its menu and the Excel workbook it writes are
  https://github.com/FAIR-DM/fairdm/issues/696. This feature reuses that workbook for its Excel
  template.
- **The Import data button on an empty dataset's overview** is
  https://github.com/FAIR-DM/fairdm/issues/698, which makes it open the dialog this feature
  builds.
- **The dataset publish confirmation** in `fairdm/contrib/import_export/` is kept.
  https://github.com/FAIR-DM/fairdm/issues/347 decides its future.
- **Using another dataset's samples in your own dataset** is
  https://github.com/FAIR-DM/fairdm/issues/212. Until it exists an import leaves such rows out.
- **Several types in one file** (samples and their measurements together) is R21's next step and
  not part of this feature. One file holds one type.
- **Keywords, tags, descriptions, dates, identifiers other than the portal ID and Local ID, and
  contributors** are not imported. A later feature takes them.
- **An import never deletes.** Records missing from a file are left as they are.
- **Registering import definitions of a portal's own**: the lookup that allows it is
  https://github.com/FAIR-DM/fairdm/issues/695. This feature adds no way for a portal to define
  its own import beyond the types it registers.

## Clarifications

### Session 2026-11-23

Each question was answered from the request, the prototype the maintainer has seen and accepted,
and his decisions on https://github.com/FAIR-DM/fairdm/issues/692. The reasoning is in
`decisions.md`.

- Q: Who may import a file into a dataset, and who may undo an import? → A person with the edit
  level on the dataset, or above, through the dataset's existing import permission. Undo needs the
  same level and is not limited to whoever ran the import (FR-001, FR-025).
- Q: What happens to the uploaded file once the import is over? → It is deleted when the import
  finishes: imported, undone, discarded or unreadable. An import left unfinished for 30 days is
  discarded and its file deleted. The record of the import, with its counts and row outcomes,
  stays (FR-027, FR-028).
- Q: What if the dataset changes between the check and the import? → The import works through the
  file again inside its transaction. If any row would now do something other than the check
  showed, nothing is saved and the import goes back to the check, showing the new outcomes
  (FR-019).
- Q: How large a file is accepted, and which sheet of a workbook is read? → Up to 20 MB and 50,000
  rows. The first sheet of an Excel or OpenDocument workbook is read, which is where the template
  and the export put the data (FR-005, FR-006).
- Q: When is undo refused? → When any record the import added or changed has been changed or
  deleted since, by any means, or a sample it added has gained measurements. Undo is all or
  nothing (FR-025, FR-026).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A person fills a dataset from a spreadsheet of one type (Priority: P1)

A person who may change a dataset presses Import on its Samples tab and picks a sample type from
the dialog, or presses Import on one type's table and lands on that type's import page. There
they read the guide to the type's columns, download a template if they want one, choose what the
file may do and what an empty cell means, and upload a file. If some headings are not recognised
they match them to the type's columns. The portal then checks every row in the background and
shows what each would do: new, changed with each value before and after, unchanged, left out
with the reason, or needing changes with each problem and its column. A file with no problems is
imported whole in the background, and they see the outcome. A file with problems saves nothing,
and they download it back with the problems beside each row, correct it and upload it again. A
portal's own sample and measurement types import like any other, with nothing written by the
portal.

**Why this priority**: this is the feature.

**Independent Test**: seed a dataset with samples and measurements of a registered type. As a
person with the edit level, import a file that adds, changes, leaves unchanged and refers to
another dataset's records, with one unrecognised heading. Match the heading, check the outcome of
every row, import, and compare the dataset with the file. Then import a file with problems and
check that nothing was saved and that the downloaded file carries each problem.

**Acceptance Scenarios**:

1. **Given** a dataset's Samples tab before a type is chosen, **When** a person who may change the
   dataset presses Import, **Then** a dialog lists the portal's registered sample types and no
   measurement types, each leading to that type's import page. The Measurements tab lists
   measurement types alone, and the empty states of both tabs do the same.
2. **Given** the table of one type in a dataset, **When** the person presses Import, **Then** they
   go straight to that type's import page, with no dialog.
3. **Given** past imports, **When** the person chooses to import a file, **Then** the same dialog
   opens listing both sample and measurement types.
4. **Given** a person who may view the dataset but not change it, or a signed-out visitor, **When**
   they open a records table or an import address of the dataset, **Then** they see no Import
   button and the import addresses refuse them as they refuse any page the person may not open.
5. **Given** a type's import page, **When** the person opens it, **Then** it shows the guide to the
   type's columns, the formats it reads, a template in Excel (with the guide and allowed values)
   and in CSV, the type's Table Schema, and the dataset's current records of that type to
   download.
6. **Given** the import options, **When** the person leaves them alone, **Then** the file may add
   and update records and an empty cell keeps the stored value. They may instead choose only add
   or only update, and that an empty cell clears the stored value.
7. **Given** a CSV, TSV, Excel or OpenDocument file whose every heading is recognised by field
   name, label, label without its unit or a listed alternative, ignoring case, spaces and
   punctuation, and which needs nothing else, **When** it is uploaded, **Then** the matching step
   is skipped and the check starts.
8. **Given** a file with a heading that matches no column, **When** it is uploaded, **Then** the
   person matches each heading to a column or chooses to ignore it, seeing a few of the column's
   values. Matching that leaves a column a new record needs unmatched, matches two headings to one
   column, or, when only updating, leaves neither the portal ID nor the Local ID matched, cannot go
   on to the check, and each reason is shown.
9. **Given** a file with neither a portal ID nor a Local ID column, while adding and updating,
   **When** its columns are matched, **Then** the person is warned that every row will add a new
   record and that importing it again would add them again.
10. **Given** the check, **When** it runs, **Then** each row finds its record by portal ID, then by
    Local ID within the dataset, and never by name. A row with neither is new. Each row is shown as
    new, changed (each value, before and after), unchanged, left out (with the reason) or needing
    changes (each problem, with its column), and the rows can be shown by outcome, a page at a
    time.
11. **Given** a row whose portal ID belongs to a record in another dataset, whoever owns it,
    **When** the file is checked, **Then** the row is left out with the reason and the rest of the
    file can still be imported. No import adds a copy of it or changes it. For a measurement, the
    reason says that a measurement's `sample` column may name any sample the person can see.
12. **Given** a row whose portal ID belongs to a record of another type, **When** the file is
    checked, **Then** the row needs changes.
13. **Given** two rows that point at the same record, **When** the file is checked, **Then** both
    need changes.
14. **Given** only add, **When** a row finds an existing record, **Then** it is left out with the
    reason. **Given** only update, **When** a row finds no record, **Then** it is left out with the
    reason.
15. **Given** a measurement row, **When** its `sample` column names a sample by portal ID, Local ID
    or a name unique in the dataset, **Then** that sample is used. A portal ID may name any sample
    the person can view, in any dataset. A Local ID or a name is looked up in this dataset alone. A
    sample that cannot be found, or a name that is not unique, needs changes. A `sample_name`
    column is ignored.
16. **Given** a number written with a decimal comma, **When** the row is checked, **Then** it needs
    changes and the problem offers the corrected value rather than guessing.
17. **Given** a row with problems in its fields and no location columns, **When** it is checked,
    **Then** every one of those problems is reported and the row is not saved.
18. **Given** a file with any row needing changes, **When** the check finishes, **Then** it cannot
    be imported, and the person can download it back with the problems written beside each row
    and the cells at fault marked, or upload a corrected file.
19. **Given** a checked file with no problems and something to write, **When** the person imports
    it, **Then** it is imported in the background in one transaction, the page shows its progress
    and the outcome when it ends, and the dataset holds what the check showed. A file that would
    change nothing cannot be imported.
20. **Given** a file being checked or imported, **When** the person leaves the page and comes back,
    **Then** the work has carried on and the page shows where it stands.
21. **Given** a checked file, **When** the person chooses not to import it, **Then** nothing is
    saved and the import is recorded as discarded. They may instead change the column matches or
    options, or check it again.
22. **Given** a file that is not one of the four formats, is over 20 MB, has more than 50,000 rows,
    has no headings or has no rows, **When** it is uploaded, **Then** it is refused with the reason
    and nothing is recorded.
23. **Given** a sample or measurement type a portal registers with no import code of its own,
    **When** a file of it is imported, **Then** it behaves as every scenario above describes.

---

### User Story 2 - A person looks back over a dataset's imports and undoes one (Priority: P2)

A person who may change a dataset opens its past imports and sees each one: the file, its type,
who ran it and when, its state and what it added and changed. They open an import that went
wrong and undo it: what it added is deleted and what it changed gets back the values it had.
When the dataset has moved on since, undo is refused and they are told which records stand in
the way.

**Why this priority**: importing works without it, but a person who can fill a dataset from a
file needs a way to see what they did and take back a mistake.

**Independent Test**: import a file that adds and changes records. Open past imports and check the
import is listed with its counts. Undo it and compare the dataset with its state before. Import
again, edit one of its records by hand, and check undo is refused, naming the record.

**Acceptance Scenarios**:

1. **Given** a dataset with imports, **When** a person who may change it opens past imports,
   **Then** every import of the dataset is listed, newest first, with its file, type, who ran it,
   when, its state and its counts, each leading to that import.
2. **Given** an imported file whose records nobody has changed since, **When** a person who may
   change the dataset undoes it, **Then** every record it added is deleted, every record it changed
   gets back the values it had before, in one transaction, and the import is recorded as undone,
   with who undid it and when.
3. **Given** an imported file, **When** any record it added or changed has been changed or deleted
   since, by any means, or a sample it added has measurements, **Then** undo is refused, nothing is
   changed and the records in the way are named.
4. **Given** an undo of records the portal would not let the person delete or change by hand,
   **When** they undo, **Then** it is refused as the portal refuses it by hand.
5. **Given** an import that has finished, **When** its file has been deleted, **Then** the import is
   still listed with its counts and row outcomes, and undo still works.
6. **Given** an import left unfinished for 30 days, **When** that time passes, **Then** it is
   recorded as discarded and its file deleted.
7. **Given** a dataset with no imports, **When** past imports is opened, **Then** it says there are
   none and offers to import a file.

### Edge Cases

- A file exported from a records table and imported back unchanged into the same dataset leaves
  every row unchanged.
- A file mixing this dataset's records with another dataset's imports this dataset's rows and
  leaves the others out.
- A file with only some of the four location columns changes only those, and a latitude without
  a longitude needs changes.
- A file with an extra column the person chose to ignore imports the rest.
- A semicolon-separated CSV is read like a comma-separated one.
- Two imports of one dataset started together import one after the other, and the second is
  checked against what the first wrote.
- A record the check found that is deleted before the import sends the import back to the check.
- Undo of an import whose added records were since deleted by hand is refused, like any other
  change since.
- An import whose dataset is deleted goes with the dataset.

## Requirements *(mandatory)*

### Functional Requirements

**Starting an import (US1)**

- **FR-001**: Importing into a dataset MUST be open only to a person with the edit level on it or
  above, through the dataset's existing import permission. Every import page and action MUST
  refuse anyone else as the portal refuses a page they may not open, and the Import buttons MUST
  NOT be shown to them.
- **FR-002**: A single type's table in a dataset MUST lead straight to that type's import page.
- **FR-003**: Every other Import button in a dataset (the Samples and Measurements tabs before a
  type is chosen, their empty states and past imports) MUST open one dialog of types built on the
  project's existing modal component: sample types alone from the Samples tab and its empty state,
  measurement types alone from the Measurements tab and its empty state, both kinds from past
  imports. There MUST be no page for choosing a type.
- **FR-004**: A type's import page MUST show the guide to the type's columns, the formats it reads,
  a template in Excel (with the guide and the allowed values) and in CSV, the type's Table Schema,
  downloads of the dataset's current records of that type, and the dataset's recent imports of
  that type.
- **FR-005**: The import MUST read CSV (comma- or semicolon-separated), TSV, Excel and OpenDocument
  files of up to 20 MB and 50,000 rows, reading the first sheet of a workbook. A file of another
  format, too large, with no headings or with no rows MUST be refused with the reason and MUST
  leave no import recorded.
- **FR-006**: One file MUST hold one type, the type of the import page it was uploaded on.
- **FR-007**: The import options MUST offer what the file may do (add and update, the default;
  only add; only update) and what an empty cell means (keep the stored value, the default; clear
  it), as a form drawn with django-mvp-forms' card choice widget: each choice with its explanation
  on the import page, labels alone on column matching.

**Matching columns (US1)**

- **FR-008**: A heading MUST match a column by its field name, its label, its label without the
  unit, or one of its listed alternative headings, ignoring case, spaces and punctuation.
- **FR-009**: When every heading matches and nothing else needs the person, the matching step MUST
  be skipped. It MUST stay reachable from the check.
- **FR-010**: Matching MUST let the person match each heading to a column or ignore it, showing a
  few of its values. It MUST refuse to go on while a column a new record needs is unmatched
  (unless only updating), while two headings are matched to one column, or, when only updating,
  while neither the portal ID nor the Local ID is matched, and MUST say why. It MUST warn when
  adding and updating with neither identifier matched, and when only one of latitude and longitude
  is matched.

**The check (US1)**

- **FR-011**: The check MUST run in the background once the upload is saved, MUST write nothing
  to the dataset, and MUST keep the outcome of every row: new, changed (each value before and
  after), unchanged, left out (with the reason) or needs changes (each problem with its column).
- **FR-012**: A row MUST find its record by portal ID, then by Local ID within the dataset, and
  never by name. A row with neither MUST be new.
- **FR-013**: A row whose portal ID is a record of another type MUST need changes. A row whose
  portal ID is a record of another dataset, whoever owns it, MUST be left out with the reason, and
  for a measurement the reason MUST say that its `sample` column may name any sample the person
  can see. No import MUST ever add a copy of another dataset's record, change one, or suggest
  clearing the portal ID to add one.
- **FR-014**: Two rows finding the same record MUST both need changes.
- **FR-015**: Only add MUST leave out a row that finds a record. Only update MUST leave out a row
  that finds none. Each MUST say why.
- **FR-016**: A measurement's `sample` column MUST accept a portal ID of any sample the person may
  view, or a Local ID or a name unique within the dataset. A sample not found, or a name shared by
  several, MUST need changes. A `sample_name` column MUST be ignored.
- **FR-017**: A number with a decimal comma MUST need changes, with the corrected value offered.
  Every problem in a row MUST be reported, whether or not the row has location columns, which
  fixes `LocatedResourceMixin.import_instance` on `main`.
- **FR-018**: The rows of a check MUST be shown by outcome, a page at a time. A file with any row
  needing changes MUST NOT be importable, and MUST be downloadable as a workbook with each row's
  problems beside it and the cells at fault marked.

**The import (US1)**

- **FR-019**: Importing a checked file with no problems and something to write MUST work through
  the file again in the background inside one transaction, and MUST save nothing if any row
  would now do something other than the check showed, returning to the check with the new
  outcomes. A file that would change nothing MUST NOT be importable.
- **FR-020**: The import MUST keep what undoing it restores: the records it added and the values
  it replaced. It MUST add and change only its own dataset's records and MUST never delete.
- **FR-021**: While a check or import runs, its page MUST show how far it has got and move on to
  the outcome when it ends, without the person reloading. Leaving the page MUST NOT stop it.
  Imports of one dataset MUST write one at a time.
- **FR-022**: A checked import MUST offer to import it, to change its matches or options, to check
  it again, and not to import it, which records it as discarded and saves nothing.
- **FR-023**: Every registered sample and measurement type MUST import through one dataset-bound
  resource that reads the type's column model, replacing `BaseFairDMResource` and the registry's
  `ResourceFactory`, with nothing written by the portal. The unused import views, forms and
  templates in `fairdm/contrib/import_export/` MUST be removed. The dataset publish confirmation
  there MUST be kept.

**Past imports and undo (US2)**

- **FR-024**: Each dataset MUST list its imports, newest first, with the file, type, who ran it,
  when, its state and its counts, to a person with the edit level or above. Each import MUST
  record the name of the import definition it was read with rather than the model.
- **FR-025**: Undo MUST delete what the import added and restore what it changed, in one
  transaction, and record who undid it and when. It MUST be open to anyone with the edit level on
  the dataset.
- **FR-026**: Undo MUST be refused, changing nothing and naming the records in the way, when any
  record the import added or changed has been changed or deleted since by any means, when a
  sample it added has measurements, or when the portal would refuse the person that deletion or
  change by hand.
- **FR-027**: The uploaded file MUST be deleted when its import finishes: imported, undone,
  discarded or unreadable. The record of the import, its counts and its row outcomes MUST stay.
- **FR-028**: An import left unfinished for 30 days MUST be recorded as discarded and its file
  deleted, by a scheduled task.

### Key Entities

- **Import**: one file uploaded into one dataset under one import definition, from upload to
  outcome. It holds the dataset, the definition's name, who uploaded it and when, the file while
  it is kept, its headings and a few values from each, the column matches, what the file may do
  and what an empty cell means, its state, every row's outcome, the counts, what undo restores,
  and who undid it and when. Its states are: matching columns, checking, ready to import, nothing
  to change, needs changes, importing, imported, could not be read, undone and discarded.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A file exported from a dataset's records table and imported back unchanged into the
  same dataset shows every row unchanged and changes nothing.
- **SC-002**: Nothing in a dataset changes until the person imports a checked file, and a file with
  any row needing changes saves nothing.
- **SC-003**: After an import is undone, the dataset's samples and measurements hold the same
  values as before the import.
- **SC-004**: A file of 50,000 rows is checked and imported in the background: the page that
  starts each step answers without waiting for it, and the check's rows open a page at a time.
- **SC-005**: No import adds, changes or copies a record of another dataset.
- **SC-006**: Every registered sample and measurement type in the demo portal imports a file with
  no import code written for it.

## Assumptions

- The column model, the guide and the Table Schema of a type exist as
  https://github.com/FAIR-DM/fairdm/issues/695 delivers them, and the export and its Excel
  workbook as https://github.com/FAIR-DM/fairdm/issues/696 delivers them. This feature is built
  after both.
- The portal runs a Celery worker, as the start sequence's worker mode provides, and scheduled
  tasks through django-celery-beat.
- django-import-export's dry runs, row results and diffs are what the check and the import are
  built on. tablib reads OpenDocument files.
