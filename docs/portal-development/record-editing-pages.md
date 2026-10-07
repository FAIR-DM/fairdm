# Record editing pages

A project, a dataset, a sample and a measurement are edited through the same pages. Each page is
written once, in `fairdm/core/editing.py`, and registered on all four record types. A sample type
or measurement type your portal registers receives every page below with no work beyond the
registration itself.

## The pages

| Page | Class | Address | Right needed |
| --- | --- | --- | --- |
| Edit details | `EditDetails` | `<record address>/edit/` | change the record |
| Descriptions | `EditDescriptions` | `<record address>/descriptions/` | change the record |
| Key dates | `EditKeyDates` | `<record address>/key-dates/` | change the record |
| Identifiers | `EditIdentifiers` | `<record address>/identifiers/` | change the record |

The record address is the record's permanent address with the `overview/` segment left off where
the record has one. For a record `<uuid>` of each kind the pages are at:

| Record | Edit details |
| --- | --- |
| Project | `/projects/<uuid>/edit/` |
| Dataset | `/datasets/<uuid>/edit/` |
| Sample | `/samples/<uuid>/edit/` |
| Measurement | `/measurement/<uuid>/edit/` |

The other pages follow the same pattern, with `descriptions/`, `key-dates/` or `identifiers/` in
place of `edit/`. The URL names are `edit`, `descriptions`, `key-dates` and `identifiers` in the
namespace of the record's kind, so `reverse("sample:key-dates", kwargs={"uuid": sample.uuid})`
gives a sample's key dates address, whatever type the sample is.

None of the pages is a tab. They are registered with `menu=False`, so the tab strip beside the
overview never lists them.

## How they are reached

A record's overview page carries a **Manage** menu in its header. It lists the pages the
signed-in person may use, in a fixed order, and is not drawn at all when there is nothing in it.
The same entries appear on a project, a dataset, a sample and a measurement, in this order: edit
details, descriptions, key dates, identifiers.

Two pieces draw the menu:

- `manage_menu(request, record)` returns the entries for a record: a `label`, an `icon` and a
  `url` for each page the viewer may open. `RecordOverviewPlugin` adds the list to every overview's
  context as `manage_menu`.
- `<c-actions.manage :entries="manage_menu">` draws it. The shared overview template puts it in the
  `overview.manage` block.

To add an entry of your own, fill the component's slot from your record's template. The entry
stays in the same menu as the shared ones, and the menu is drawn when the slot has content even if
the person has none of the shared pages:

```django
{% block overview.manage %}
  <c-actions.manage :entries="manage_menu">
    <c-menu.item label="Import data" icon="upload" href="{{ import_url }}" />
  </c-actions.manage>
{% endblock overview.manage %}
```

Put any button that belongs before the menu in the same block, ahead of the component.

## Who may open a page

A page opens for whoever may change the record. That is the right the portal already checks for a
record: the edit or manage level on the record or on a record above it, or a portal role that
confers it. See [Contributors](contributors.md) for how levels are given.

Every request is answered in the same order, on a view and again on a save:

1. A person who may neither see the record nor hold the right on it is told the record does not
   exist (404).
2. A visitor who is not signed in, and who may see the record, is sent to sign in.
3. A signed-in person who may see the record and may not use the page is refused (403).

The right is read from `RecordEditingPage`, the class every page inherits. A page names its right
in its `access` attribute, and the class holds the table of permission names for the four core
models. A person whose level is removed while a page is open is refused when they save.

## Edit details

The page edits the record's own fields.

- A project is edited with `ProjectForm` and a dataset with `DatasetForm`. Visibility, and the
  owner of a project or the project of a dataset, are offered only to someone at the manage level.
- A sample or a measurement is edited with the form its registered type creates records with,
  which comes from the type's registry configuration. The fields that would move the record to
  another dataset or sample are removed. Set `form_class` or `form_fields` on the type's
  configuration to change what the page offers.
- Dates and identifiers are not on this page. They have the pages described below.

When a form carries a crispy-forms helper with a form tag or buttons of its own, the page turns
both off. The page draws one form element and its own Save buttons.

## Descriptions

The page has one text area for each description type the record's vocabulary offers, filled with
what is recorded. Saving an area with text records or replaces that description, and saving an
empty area removes it. The vocabularies are `ProjectDescription.VOCABULARY`,
`DatasetDescription.VOCABULARY`, `SampleDescription.VOCABULARY` and
`MeasurementDescription.VOCABULARY`.

## Key dates

The page is a set of rows, one per date, each with a type and a value. The types on offer are the
ones in the record's date vocabulary: `ProjectDate.VOCABULARY`, `DatasetDate.VOCABULARY`,
`SampleDate.VOCABULARY` and `MeasurementDate.VOCABULARY`. A date can be added, changed and
removed, and a record holds at most one date of each type.

- A date is kept as precisely as it was entered. A year, a month and a full day are each stored
  and shown as entered, never rounded to a day.
- A project refuses an end that falls before its start, and a dataset refuses a collection end
  that falls before its collection start. The page keeps what was typed and says which dates
  clash, and nothing is saved. No other record type has an ordering rule: a sample's types are not
  a start and an end, and a measurement's setup and tear down are not read as one.

The page edits only the rows, never a field of the record itself.

## Identifiers

The page is a set of rows with a type and a value, laid out like the key dates page. The types
on offer are the ones in the record's identifier vocabulary: `ProjectIdentifier.VOCABULARY`,
`DatasetIdentifier.VOCABULARY`, `SampleIdentifier.VOCABULARY` and
`MeasurementIdentifier.VOCABULARY`. An identifier can be added, changed and removed, and a record
holds at most one identifier of each type.

- An identifier value that is already recorded against any other record is refused, whatever kind
  of record holds it, and so is the same value entered twice in one save.
- The identifier the portal gives the record is its `uuid`. It is shown on the record's page, is
  never a row on this page, and cannot be changed through it.
- A row set that fails validation saves none of its rows.

The row sets behind both pages are declared in `fairdm/core/related_records.py`: `ProjectDatesInline`
and `ProjectIdentifierInline`, `DatasetDatesInline` and `DatasetIdentifierInline`,
`SampleDateInline` and `SampleIdentifierInline`, and `MeasurementDateInline` and
`MeasurementIdentifierInline`. A sample type or measurement type you register uses the row sets of
its base record, so it needs no declaration.

## After a save

Every page returns to the record's own page and adds a message saying what was saved. A
measurement with no name is called by its portal ID in that message.
