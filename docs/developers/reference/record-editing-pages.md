# Record editing pages

A project, a dataset, a sample and a measurement are edited through the same six pages. Each page is a plugin class in `fairdm/core/editing.py`, registered on all four record models, so a sample type or measurement type your portal registers receives them with no further work. This page lists the classes, their addresses, who may open each one and the building blocks behind them. It does not walk through changing them, which the how-to guides linked at the end do, or show what each screen looks like, which the user guides do: [Edit details](../../users/projects/edit-details.md), [Descriptions](../../users/editing-a-record/descriptions.md), [Keywords](../../users/editing-a-record/keywords.md), [Key dates](../../users/editing-a-record/key-dates.md), [Identifiers](../../users/editing-a-record/identifiers.md) and [Delete](../../users/editing-a-record/delete.md). The decision behind the design is [ADR 0026](../../adr/0026-a-records-editing-pages-are-six-shared-pages.md).

## The pages

| Class | Plugin name | Menu label | Icon | `access` |
|---|---|---|---|---|
| `EditDetails` | `edit` | Edit details | `edit` | `change` |
| `EditDescriptions` | `descriptions` | Edit descriptions | `description` | `change` |
| `EditKeywords` | `keywords` | Keywords | `keywords` | `change` |
| `EditKeyDates` | `key-dates` | Key dates | `date` | `change` |
| `EditIdentifiers` | `identifiers` | Identifiers | `identifier` | `change` |
| `DeleteRecord` | `delete` | Delete | `delete` | `delete` |

The plugin name is the last segment of the page's address and its URL name in the namespace of the record's kind. For a sample, `reverse("sample:key-dates", kwargs={"uuid": sample.uuid})` gives the key dates address whatever type the sample is. The kinds' namespaces are `project`, `dataset`, `sample` and `measurement`.

The pages are registered with `menu=False`, so the tab strip beside the overview never lists them.

## Addresses

A page's address is the record's own address followed by the plugin name and a slash.

| Record | Edit details |
|---|---|
| Project | `/projects/<uuid>/edit/` |
| Dataset | `/datasets/<uuid>/edit/` |
| Sample | `/samples/<uuid>/edit/` |
| Measurement | `/measurement/<uuid>/edit/` |

The other pages replace `edit/` with `descriptions/`, `keywords/`, `key-dates/`, `identifiers/` or `delete/`.

## `RecordEditingPage`

The class every page inherits. It holds who may open a page and where the page leads afterwards.

| Attribute | Default | What it sets |
|---|---|---|
| `access` | `"change"` | `"change"` for the pages that edit the record, `"delete"` for the one that removes it. |
| `menu_label` | `""` | The page's entry in the Manage menu. |
| `menu_icon` | `"edit"` | The icon beside that entry. |
| `PERMISSIONS` | a dictionary | For each `access`, the permission name for each of the four core models, such as `project.change_project`. |

| Method | Returns |
|---|---|
| `permission_for(record)` | The permission that opens the page on a record. |
| `overview_for(record)` | The overview plugin class of the record's kind, whose `check` decides who may see the record. |
| `verdict(request, record, may_see=None)` | `OPEN`, `MISSING` or `REFUSED`. |
| `may_be_used_by(request, record, may_see=None)` | `True` when the verdict is `OPEN`. |
| `name_of(record)` | The record's name. A measurement with no name is named by its portal ID. |
| `without_form_tag(form)` | The form with its crispy-forms helper's form tag and buttons removed. |
| `get_success_message(cleaned_data)` | "Saved" and the record's name. |
| `get_success_url()` | The record's own page. |

### Who may open a page

A page opens for whoever holds the permission its `access` names on the record: change for the five editing pages, delete for the delete page. These are the permissions the portal already checks, whether the level is held on the record, on a record above it or comes from a portal role. See [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md).

Every request is answered in this order, on a view and again on a save:

1. A person who may neither see the record nor hold the permission is told the record does not exist (404).
2. A visitor who is not signed in, and who may see the record, is sent to sign in.
3. A signed-in person who may see the record and may not use the page is refused (403).

A person whose level is removed while a page is open is refused when they save.

## The Manage menu

`manage_menu(request, record)` returns one entry for each page the viewer may open, in the order edit details, descriptions, keywords, key dates, identifiers and delete. Each entry has `label`, `icon`, `url` and `destructive`, which is true only for delete. `RecordOverviewPlugin` adds the list to every overview's context as `manage_menu`. [`c-actions.manage`](components.md#c-actionsmanage) draws it, in the `overview.manage` block, and draws nothing when there are no entries and the slot is empty.

## Edit details

`EditDetails` edits the record's own fields.

- A project is edited with `ProjectForm` and a dataset with `DatasetForm`. Visibility, and the owner of a project or the project of a dataset, are offered only to someone at the manage level (`manager_only_fields`).
- A sample or a measurement is edited with the form class its registered type's configuration returns from `get_form_class()`. The fields `dataset` and `sample` are removed, so a record cannot be moved. Set `form_class` or `form_fields` on the type's configuration to change what the page offers. See [Model configuration](model-configuration.md).
- A type that is not registered is edited with a form of `name` and `image`.
- A form whose `__init__` takes `request` receives it.
- Dates and identifiers are not on this page.

When a form carries a crispy-forms helper with a form tag or buttons of its own, the page turns both off. The page draws one form element and its own Save buttons. The keywords page does the same.

## Descriptions

`EditDescriptions` uses `VocabularyDescriptionsForm` from `fairdm.core.descriptions`. It makes one text area for each concept in the collection the record's description model offers, in the collection's order, named after the concept's address, labelled with its name and helped by its definition, so the page grows with the vocabulary. Saving writes, updates or deletes one row for each area: a non-blank area becomes one row of its type, and a blank one (including whitespace only) removes the row already stored.

| Record | Description collection |
|---|---|
| Project | `ProjectDescription.get_type_concepts()` |
| Dataset | `DatasetDescription.get_type_concepts()` |
| Sample | `SampleDescription.get_type_concepts()` |
| Measurement | `MeasurementDescription.get_type_concepts()` |

## Keywords

`EditKeywords` uses `KeywordForm` from `fairdm.core.forms`: one `tags` field where a person chooses a tag already in use or types a new one. Saving replaces the record's free keywords with the field's contents, and an empty field removes them all. The page offers nothing from a controlled vocabulary. Vocabulary keywords a record already carries are left as they are.

## Key dates and identifiers

`EditKeyDates` and `EditIdentifiers` are sets of rows, one per date or identifier, each with a `type` and a `value`. Both use the template `editing/rows.html`. The types on offer are those of the record's collection, drawn as a drop-down in the collection's order, and a record holds at most one row of each type.

| Record | Date collection | Identifier collection |
|---|---|---|
| Project | `ProjectDate.get_type_concepts()` | `ProjectIdentifier.get_type_concepts()` |
| Dataset | `DatasetDate.get_type_concepts()` | `DatasetIdentifier.get_type_concepts()` |
| Sample | `SampleDate.get_type_concepts()` | `SampleIdentifier.get_type_concepts()` |
| Measurement | `MeasurementDate.get_type_concepts()` | `MeasurementIdentifier.get_type_concepts()` |

- A date is kept as precisely as it was entered: a year, a month and a full day are each stored and shown as entered.
- An identifier value already recorded against any other record is refused, and so is the same value entered twice in one save.
- The identifier the portal gives the record is its `uuid`. It is never a row on this page.
- A row set that fails validation saves none of its rows.

### Row sets

The row sets are declared in `fairdm/core/related_records.py`.

`RelatedRecordInline` is the base, built on django-mvp's `InlineFormSet`. It fixes `fields = ("type", "value")`, `extra = 0` so that no blank rows appear beyond the existing ones, draws `type` with `ConceptSelectField`, and caps the set at one row for each type in the model's collection (`max_num`, with `validate_max`). A subclass names only its `model`:

```python
from fairdm.core.related_records import RelatedRecordInline
from fairdm.core.project.models import ProjectDate


class ProjectDateInline(RelatedRecordInline):
    model = ProjectDate
```

| Record | Dates | Identifiers |
|---|---|---|
| Project | `ProjectDatesInline` | `ProjectIdentifierInline` |
| Dataset | `DatasetDatesInline` | `DatasetIdentifierInline` |
| Sample | `SampleDateInline` | `SampleIdentifierInline` |
| Measurement | `MeasurementDateInline` | `MeasurementIdentifierInline` |

`ProjectDatesInline` and `DatasetDatesInline` add the ordering rule below to `ProjectDateInline` and `DatasetDateInline`. A sample type or measurement type uses the row sets of its base record, so it declares none.

### Date ordering

`date_ordering_formset(start_type, end_type, message)` in `fairdm.core.formsets` returns a `BaseInlineFormSet` subclass that refuses an end earlier than its start across the whole formset. It reads the two values from each form's `cleaned_data`, so it works when both rows are new in the same submission. `message` is a whole sentence with `%(start)s` and `%(end)s` placeholders.

```python
from django.utils.translation import gettext_lazy as _

from fairdm.core.formsets import date_ordering_formset
from fairdm.core.project.models import ProjectDate
from fairdm.core.related_records import ProjectDateInline


class ProjectDatesInline(ProjectDateInline):
    formset = date_ordering_formset(
        ProjectDate.START_TYPE,
        ProjectDate.END_TYPE,
        _("The project's end date (%(end)s) cannot be before its start date (%(start)s)."),
    )
```

A project refuses an end before its start, and a dataset refuses a collection end before its collection start. No other record type has an ordering rule.

`precedes(a, b)` in `fairdm.core.dates` is the comparison every date rule rests on. It compares two `PartialDate` values at the coarser of their two precisions, so `2020` and `2020-03-14` are the same year and neither precedes the other. Use it instead of comparing partial dates with `<`.

## Delete

`DeleteRecord` removes the record and everything recorded beneath it. It requires confirmation: nothing is deleted until the person types the record's name, or the portal ID of a measurement with no name. It has `require_confirmation = True` and `show_related_objects = True`, and the template `editing/delete_record.html`.

| Record | What is shown before confirming |
|---|---|
| Project, dataset | A count for each kind of record that goes with it, by concrete type. `related_objects_summary()` builds them. |
| Sample, measurement | The rows that go with it, such as descriptions, dates and identifiers, and never the record itself. A relationship row names both samples, so a relationship that reaches a sample the viewer may not see is left out and counted in `related_unlisted`. |

A record that cannot be deleted says so, names what is in the way and offers no way to confirm:

- A project with a public dataset lists those datasets.
- A sample with measurements made on it, and a dataset whose samples another dataset measures, list the measurements. A measurement the viewer may not see is counted in `protected_unlisted` and never named.

The protection is checked again when the deletion is confirmed. If the record became protected after the page opened, nothing is deleted and the page is drawn again in its protected state.

After a deletion a sample or a measurement leads to the dataset it belonged to, or to the dataset list when the person may not open that dataset. A dataset leads to the dataset list and a project to the project list. The page adds a message saying which record was deleted.

## After a save

Every editing page returns to the record's own page and adds a message saying what was saved.

## Tasks

- [How to add an entry to the Manage menu](../how-to/add-an-entry-to-the-manage-menu.md)
- [How to change what the edit details page offers](../how-to/change-what-the-edit-details-page-offers.md)
