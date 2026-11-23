# Feature Specification: Export the rows of any records table

**Feature Branch**: `040-records-export`

**Created**: 2026-11-23

**Status**: Draft

**Goals**: G11: round-trip import and export of tabular data. G12: private and public data sit
side by side, controlled per object.

**Roadmap**: R21, tabular data goes in and comes back out. This feature is the export half of the
single-type workflow. The import half is https://github.com/FAIR-DM/fairdm/issues/697.

**Input**: https://github.com/FAIR-DM/fairdm/issues/696. Anyone who can see a records table should
be able to download its rows: a dataset's, project's or contributor's Samples and Measurements tabs,
and the portal-wide listings. The formats are CSV, Excel, OpenDocument, TSV and JSON. The file holds
either the rows the current search and filters show, or all of them. It has exactly the columns an
import of that type reads, with the portal ID first, so it can be edited and imported back.
Measurements add a `sample_name` column for people reading the file, which import ignores. The
Excel file also carries the column guide and the lists of allowed values.

The feature comes from a prototype the maintainer has seen and accepted, on the
`prototype-import-export` branch. Its record is https://github.com/FAIR-DM/fairdm/issues/692.

## What exists, and what this specification changes

A records table lists one registered sample or measurement type at a time. There are two kinds:

- the Samples and Measurements tabs of a dataset, a project, a person and an organization, which
  list the records that belong to or credit that record
- the portal-wide listings of each sample and measurement type

Each table can be searched, filtered and paged, and lists only the records the viewer may see. On
`main` none of them can be downloaded. The export views in `fairdm/contrib/import_export/` are not
routed and nobody can reach them.

After this feature:

- Every records table that lists rows has an Export menu in its title row.
- The menu offers five formats: CSV, Excel, OpenDocument, TSV and JSON.
- While a search or filter is active, the menu offers the rows it shows or every row of the table.
  Without one, it offers every row.
- The file's columns are exactly the columns an import of that type reads, in the same order, with
  the portal ID first. A measurement file also carries the name of each measurement's sample, for
  people reading it.
- The Excel file also carries the guide to the columns and the lists of allowed values, and offers
  those values in the cells that take them.

## Boundary

Owned elsewhere, and not built here:

- **What a type's columns are** (https://github.com/FAIR-DM/fairdm/issues/695, specification 039).
  The columns of a file, their order, headings, labels, types, units, allowed values, which a new
  record needs, and how each cell is written, all come from that feature. This feature reads them
  and never works them out. The guide written into the Excel file is that feature's guide.
- **The Frictionless Table Schema download** belongs to specification 039.
- **Importing a file** (https://github.com/FAIR-DM/fairdm/issues/697, specification 041). The Import
  button beside the Export menu, the dialog of types, the template download and everything after
  an upload belong to that feature. It reuses this feature's Excel workbook for its template.
- **The Import data button on an empty dataset's overview** is a fix
  (https://github.com/FAIR-DM/fairdm/issues/698), not part of any feature.
- **A dataset exported as one archive** covering its samples, measurements and metadata is a later
  part of R21.
- **Keywords, tags, descriptions, dates, identifiers and contributors** are not columns of these
  files. Exporting them is a later feature.
- **Several types in one file** is the step R21 takes after single-table import and export.

## Clarifications

### Session 2026-11-23

- Q: Does "the rows the current search and filters show" mean the page on screen, or every row
  that matches? → A: Every row that matches, across all pages. Paging is a way to read the table,
  not a choice of rows. The page number is dropped from the export's address.
- Q: Are rows written in the order the table is sorted in? → A: No. Rows are written in a stable
  record order that does not depend on how the viewer sorted the table, so two downloads of the
  same data compare line by line. Sorting is a reading aid. This follows the prototype.
- Q: Who sees the Export menu? → A: Anyone who can see the table, signed in or not. The table's
  existing visibility decides which rows are in it, and an export never holds a row the table
  would not list for that viewer, in either choice of rows.
- Q: What happens on a table with no rows? → A: The table shows its empty state and no Export menu.
  An export asked for by address on a table that lists no type, or in a format the type is not
  offered in, answers "not found".
- Q: Does a large table export in the background? → A: No. The file is written while the request
  waits, as in the prototype, reading the records in batches. A background export with progress
  is not part of this feature (decisions.md, D4).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A person downloads the rows of a records table (Priority: P1)

A person looking at a records table (a dataset's, project's, person's or organization's Samples or
Measurements tab, or a portal-wide listing) opens the Export menu in the table's title row, picks a
format and, when a search or filter is active, whether they want the rows it shows or every row.
The file downloads at once. Its columns are the columns an import of that type reads, so they can
edit it and bring it back.

**Why this priority**: it is the whole feature. It is also the first half of the round trip that
R21 promises, and the import (specification 041) relies on files written this way.

**Independent Test**: on a dataset's Samples tab with several samples, download each format with
no filter, then search and download the shown rows, and compare each file's headings and rows with
the type's columns and the table's results.

**Acceptance Scenarios**:

1. **Given** a records table that lists rows of one type, **When** the person opens its Export
   menu, **Then** it offers CSV, Excel, OpenDocument, TSV and JSON.
2. **Given** no search or filter is active, **When** the person picks a format, **Then** the file
   holds every row the table lists for them, across all its pages.
3. **Given** a search or filter is active, **When** the person opens the Export menu, **Then** it
   offers both the rows the search and filters show and every row of the table, and says how many
   rows the first choice holds.
4. **Given** a search or filter is active and the table runs to several pages, **When** the person
   downloads the rows it shows, **Then** the file holds every matching row from every page and no
   other row.
5. **Given** a search or filter is active, **When** the person downloads every row, **Then** the
   file holds every row the table would list for them with no search or filter.
6. **Given** a table of a sample type, **When** a file of any format is downloaded, **Then** its
   headings are the type's file columns, in their order, with the portal ID first, and nothing
   else.
7. **Given** a table of a measurement type, **When** a file is downloaded, **Then** its headings
   are the type's file columns in their order, including the column naming each measurement's
   sample for readers, and that column holds the sample's name.
8. **Given** a record in the file, **When** its row is read, **Then** the portal ID cell holds the
   record's portal ID and every other cell holds the record's value written the way an import of
   that type reads it.
9. **Given** a record with no location, or an empty optional value, **When** its row is written,
   **Then** those cells are empty.
10. **Given** the table holds records the viewer may not see (another person's private dataset's
    samples on a portal-wide listing, for example), **When** they download either choice of rows,
    **Then** the file holds none of those records.
11. **Given** the same records and the same choice, **When** the file is downloaded twice, **Then**
    the rows are in the same order both times, whatever order the table was sorted in.
12. **Given** the person picks Excel, **When** the workbook opens, **Then** its first sheet holds
    the rows, a second sheet holds the guide to every column, and a third holds the allowed values
    of each column that has a fixed list.
13. **Given** an Excel export of a type with a column that takes one of a fixed list of values (or
    yes or no), **When** a person edits a cell in that column, **Then** the spreadsheet offers the
    allowed values.
14. **Given** an Excel export, **When** a person looks at a column heading, **Then** a note on it
    gives the column's label, type, unit where it has one, how to write it, and whether a new
    record needs it.
15. **Given** the person picks JSON, **When** the file is read, **Then** it is a list with one
    object per row, keyed by the column headings.
16. **Given** a downloaded file, **When** it is saved, **Then** its name identifies the type, the
    record whose tab it came from where there is one, and the date of the download, and ends in
    the format's usual extension.
17. **Given** a person using the keyboard, **When** they open the Export menu, **Then** they can
    reach every choice, download a file with the keyboard, and close the menu with Escape, which
    returns them to the menu's button. Choosing a file, or clicking outside the menu, also closes
    it.
18. **Given** a table that lists no rows, **When** the person looks at it, **Then** there is no
    Export menu.
19. **Given** an export asked for by address in a format that is not offered, or on a table that
    lists no type, **When** the request arrives, **Then** it answers "not found" and sends no file.

### Edge Cases

- A value holding the delimiter, a quote or a line break is quoted in CSV and TSV so the row still
  reads as one row.
- Text in any script survives every format. Text formats are UTF-8.
- A type whose name runs past a spreadsheet's sheet-name limit still produces a workbook that opens:
  the sheet name is shortened.
- A column with a very long list of allowed values still gets its list sheet and its offered
  values.
- A measurement whose sample the viewer may not see is not in the table, so it is not in the file.
- Search terms and filters in the address are carried into the export of the shown rows exactly as
  the table read them, so the file and the table can never disagree about which rows match.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every records table that lists rows of a type MUST offer an Export menu in its title
  row: the Samples and Measurements tabs of datasets, projects, people and organizations, and the
  portal-wide listings of each sample and measurement type.
- **FR-002**: The menu MUST offer CSV, Excel, OpenDocument, TSV and JSON.
- **FR-003**: Without an active search or filter the menu MUST offer every row of the table. With
  one, it MUST offer the rows it shows, with how many there are, and every row of the table.
- **FR-004**: "The rows it shows" MUST mean every row matching the active search and filters across
  all pages. "Every row" MUST mean every row the table lists for the viewer with no search or
  filter.
- **FR-005**: An export MUST never hold a record the table would not list for that viewer.
- **FR-006**: A file's columns MUST be exactly the type's file columns as specification 039 defines
  them, in their order, with the portal ID first, read through that feature's lookup and never
  worked out here.
- **FR-007**: A measurement file MUST include the column naming each measurement's sample for
  readers, filled with the sample's name. Import ignores it (specification 041).
- **FR-008**: Every cell MUST be written the way an import of the type reads that column, using
  specification 039's cell writing, so an unchanged file imports back without changes.
- **FR-009**: Rows MUST be written in a stable record order that does not depend on the table's
  sort.
- **FR-010**: An Excel file MUST hold the rows on its first sheet, the guide to the columns on a
  second sheet and the allowed values of each column with a fixed list on a third, MUST offer those
  values in the cells of those columns, and MUST put a note on each heading giving the column's
  label, type, unit, how to write it and whether a new record needs it.
- **FR-011**: The Excel workbook MUST be produced by one writer that can also produce the same
  workbook with no rows, for the template download of specification 041.
- **FR-012**: A JSON file MUST be a list with one object per row, keyed by the column headings.
  CSV and TSV MUST be UTF-8 and quote values that need it.
- **FR-013**: A file's name MUST identify the type, the record whose tab it came from where there
  is one, and the date, and MUST end in the format's usual extension.
- **FR-014**: An export asked for in a format that is not offered, or on a table that lists no
  type, MUST answer "not found" and send no file. A table with no rows MUST show no Export menu.
- **FR-015**: The menu MUST be usable with the keyboard alone: every choice reachable, Escape
  closing it and returning focus to its button. Choosing a file or clicking outside MUST close it.
- **FR-016**: Every word the menu shows and every word written into the workbook's guide and notes
  MUST be translatable.
- **FR-017**: The Export menu MUST be a component the title row places, so the Import button of
  specification 041 can sit beside it without changing it.
- **FR-018**: Export MUST be added to the records table view itself, so a table built on it,
  including one a portal adds, offers Export without further configuration.

### Key Entities

None. The feature stores nothing. It reads a type's file columns from specification 039 and the
rows a records table already lists.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every records table of every registered sample and measurement type that lists rows
  offers all five formats.
- **SC-002**: For every registered type, the headings of an exported file equal that type's file
  columns, in order, with the portal ID first.
- **SC-003**: With a search or filter active, the number of rows in a "rows it shows" file equals
  the table's result count. Without one, an export holds as many rows as the table lists.
- **SC-004**: No export, by any viewer, in either choice of rows, holds a record that viewer may
  not see.
- **SC-005**: Two exports of unchanged records in the same format and choice of rows hold the same
  rows in the same order.

## Assumptions

- Specification 039 provides the lookup that gives a type's file columns, the column guide's
  content and the writing of each cell. This feature is built after it.
- The records tables keep their current routing, search, filters and visibility. The checks run
  while this specification was written are in `research.md`.
- The libraries already installed write the formats: tablib with its ODS and XLSX extras for CSV,
  TSV, JSON and OpenDocument, and openpyxl for the workbook.
