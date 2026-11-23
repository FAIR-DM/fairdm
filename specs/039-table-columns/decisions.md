# Decisions: the columns of a sample or measurement type

Rationale too long for the specification, and every ambiguity resolved while it was written. The
feature was agreed from the prototype the maintainer has seen and accepted
(https://github.com/FAIR-DM/fairdm/issues/692) and from #695. Each reading below was chosen without
putting it to him again, and each is open to his veto at the specification's review.

## The agreed reading

Every registered sample and measurement type says what a spreadsheet of its records holds. A
developer asks the type's configuration for its table schema with `get_table_schema()` and gets the
columns in order, each knowing its heading, label, other recognised headings, kind, unit, range,
allowed values, whether a new record needs it and an example, and each with a widget that reads and
writes its cells. Every type has an import definition named after it, found by name, and a project
can register its own. Anyone can download a type's columns as a Frictionless Table Schema. The
column guide is a component that lays the columns out for a person. Exporting rows is #696,
importing a file (including placing the guide and the schema link on the import page) is #697, and
the empty overview's Import data button is #698.

## D1. Two stories, one for the developer and one for the person downloading

The issue names two people: a developer who asks a type for its columns, and a person who downloads
the Table Schema. The import definition lookup, registering a project's own definition, the widgets
and the column guide are all things the same developer does with a type's columns, so they are
scenarios of the first story rather than stories of their own. The column guide is read by a site
user only once #697 places it on the import page, so the person reading it has no story here.

## D2. The sample's name is a column of the schema, written on export only

#696 says measurements add a `sample_name` column that import ignores. The prototype declares that
column in the type's columns, marked as written on export and not read on import, and the Table
Schema describes it. This feature keeps it there, so the Table Schema describes the file an export
writes, column for column. #696 fills the cells and #697 skips the column.

## D3. The Table Schema is served for the type, to anyone

The prototype serves it beneath a dataset's import page, which only someone who may change that
dataset can open. #695 says "a person can download it for any type". A type's columns describe the
type and hold nobody's records: the allowed values come from the portal's vocabularies and choices,
which are public, and examples come from no stored record (D4). A researcher preparing a file may
not yet have a dataset to import into. So the address depends on the type alone and is open to
anyone. #697's import page links to it, and nothing a person sees on that page changes.

## D4. Examples never come from stored records

The prototype fills a column's example from the first stored record of the type, in whichever
dataset it sits. That record can be private, and the guide and the Table Schema are read by people
who may not see it, so its values would be shown to them. Examples are made from the column's kind
and constraints instead. This is a change to how the prototype works, not to anything it shows: the
guide still gives an example for every column. Constitution Article V.

## D5. The Table Schema lists every allowed value

The prototype cuts a concept list at 40 values in both the guide and the Table Schema, and drops the
list from the Table Schema altogether when it is cut. A machine checking a file then accepts any
value in that column. The guide may still show part of a long list. The Table Schema lists every
value as an export writes it (a concept's preferred label), which is what a re-imported export holds.
A concept's other labels, codes and web addresses are still read on import, and the column's
description says so, but a strict validator would refuse them. That is the expected trade: a file
exported from the portal validates, and a hand-made file using another label may be flagged by a
validator and still import.

## D6. A sample the person may not see is refused as if it did not exist

The prototype's sample widget tells a person "you may not see the sample", which confirms that a
private sample with that portal ID exists. The refusal is the same as for a portal ID nobody holds,
in line with how the permalink (specification 034) and the citation addresses (specification 036)
answer for private records. Constitution Article V.

## D7. The guide is read as a table by assistive technology

PROTOTYPE.md, "Faked or skipped", says the guide uses table roles on plain elements and that the
rebuild should check that or replace it with real tables, in this feature. The requirement is the
outcome (each group is read as a table with its headers, checked with an accessibility audit), and
the means is left to planning, which must keep the prototype's look: at narrow widths the guide
stacks each column's cells, and a native table restyled that way can lose its table meaning in some
browsers. Planning tests both and records which.

## D8. Status is a sample's column only

#695 lists "the status" among the columns. Only `Sample` has a status field. A measurement has none,
so its table schema carries none, as in the prototype.

## D9. `get_table_schema()` can be overridden

The configuration's other components (`get_table_class()`, `get_filterset_class()`,
`get_resource_class()`) can be overridden by a portal's developer. `get_table_schema()` sits beside
them and follows the same rule, so a portal with an unusual type can adjust its columns without
changing FairDM. The import definition reads its columns through it.

## D10. The registry's generated resource stays until the import replaces it

PROTOTYPE.md says the dataset-bound resource replaces `BaseFairDMResource` and the registry's
`ResourceFactory`, in the import feature (#697). This feature adds the columns and widgets that
resource will be built from, and leaves `get_resource_class()` as it is, so nothing that reads it
changes before its replacement exists.

## D11. A name in `exclude` is never a column, unless the record cannot be saved without it

Every generated component drops the names in a configuration's `exclude`, so a field a developer
excluded everywhere does not reach a form, a table or the API. The column model follows, so an
export never writes it. A required field stays a column because a file of new records must stay
saveable (FR-003). No demo type sets `exclude`. **ADR:** none, local to this feature.

## D12. A type's own foreign key to another model is not a column yet

The specification lists thirteen kinds of column and a reference to a record of another model is
not one of them. Such a field has no kind and is left out. No registered demo type has one. A
portal type with a required one cannot have it filled from a file until a later feature adds the
kind. **ADR:** none, local to this feature.

## D13. A concept column's value is its preferred label, not the label in the active language

`str(record)` is the label in the language of the request, so using it would change the allowed
list, the Table Schema's `enum` and the cell an export writes with the portal's language, and a
file exported in one language would fail the Table Schema fetched in another (US2 scenario 8
changes only titles and descriptions). The preferred label is the same in every language.
**ADR:** none, local to this feature.

## D14. Dates and times are written with seconds, the datetime in UTC

A stored time with seconds must read back to the same value (SC-002). A cell is a datetime as
ISO 8601 in UTC with seconds (`2024-05-01T10:15:42Z`), a time as `HH:MM:SS` and a date as
`YYYY-MM-DD`, which is also the default form of the Frictionless types, so the Table Schema needs
no custom format. Cells with minutes only are still read. **ADR:** none, local to this feature.

## D15. The sample widget always filters by what the person may see

One queryset, `Sample.objects.visible_to(user)`, serves the portal ID, the Local ID and the name
lookups, and `None` means a visitor, as everywhere else in the portal. There is no mode that
reads every sample. **ADR:** none, local to this feature.

## D16. Import formats come from `IMPORT_FORMATS`

A definition is offered in the formats a portal reads, which leaves out the export-only LaTeX.
**ADR:** none, local to this feature.

## D17. The portal ID is unique, not the primary key

A ruling made at the build's spec gate on Sam's behalf by the orchestrating session. A primary key
makes the portal ID required, and a file of new records has it empty, so the standard validator
rejected every row and FR-018 failed for the file US2 exists to check (checked with frictionless 5).
US2 scenario 5 and FR-017 now give the portal ID a `unique` constraint and no primary key. A test
keeps that a file with duplicate portal IDs fails validation. **ADR:** none, local to this feature.
