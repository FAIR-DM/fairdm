# Implementation Plan: One set of editing pages for projects, datasets, samples and measurements

**Branch**: `024-shared-editing-pages` | **Date**: 2026-10-07 | **Spec**: [spec.md](spec.md)

## Summary

Six plugin pages are written once in one module and registered on projects, datasets, samples and
measurements. One base class decides who may open each of them. One function lists the pages a
viewer may use on a record, and one component draws that list as the Manage menu on all four
overview pages. The three older sets of pages, and the generic bases only they used, are removed
in the story that replaces them.

## Technical context

**Language/version**: Python 3.13, Django 5.2
**Primary dependencies**: django-mvp 0.26 (form, inline and delete views), django-cotton. No new
dependency
**Storage**: no model change and no migration
**Testing**: pytest, pytest-django, factory-boy, per `docs/contributing/standards/testing.md`.
Tests request the real pages through the test client, for each kind of account a scenario names
**Target**: the `fairdm` package and the `demo` reference application
**Constraints**: every string translatable (Article VIII). The right to use a page is checked on
every request, GET and POST (FR-015). Layout, wording and appearance get no tests

## Constitution check

| Article | How the plan meets it |
|---|---|
| I Testing | Each story starts with tests of its acceptance scenarios through the test client, across the four record types and the kinds of account the story names |
| II Simplicity / III Anti-Abstraction | One module, one base class with six subclasses, one function for the menu. No registry of menu entries and no settings |
| IV Integration-First | Access is tested by requesting the page, never by calling the check directly |
| V Security | One decision point for all 24 page and record type combinations (D2), asked again on POST. A record the viewer may not see answers 404 |
| VI / XVI Documentation | Each story documents the pages it adds, in that story. FR-034's developer page is written in the first story and extended by the others |
| VII Dependencies | None added |
| VIII i18n | All labels and messages are translatable |
| IX Data-model conventions | No model change |
| X Cohesion | The six pages and what they share sit in one module. Row-set declarations stay in `related_records.py` |
| XVII Demo | The demo portal's sample and measurement types get all six pages with nothing written for them (SC-006) |

## Complexity tracking

| Addition | Why it is needed | Simpler alternative, and why not |
|---|---|---|
| `RecordEditingPage` base class | FR-011 to FR-015 are the same rule on six pages and four record types | State `permission` and `check` on each page as today: a plugin registered on four models has one `permission` attribute and needs four |
| `manage_menu()` and `<c-actions.manage>` | FR-006 and FR-008 want the same entries, in the same order, shown by the same rule on four pages | Keep the hand-written menu in each template: that is the three copies the feature exists to remove, and a fourth for measurements |

## Design

### D1. One module, six plugins, registered on four models

`fairdm/core/editing.py` holds the base class and the six pages. Each page is registered once:

```python
@plugins.register(Project, Dataset, Sample, Measurement, menu=False)
class EditDetails(RecordEditingPage, FairDMUpdateView): ...
```

| Page | Class | `name` and address segment | URL name on each record type |
|---|---|---|---|
| Edit details | `EditDetails` | `edit` | `<type>:edit` |
| Descriptions | `EditDescriptions` | `descriptions` | `<type>:descriptions` |
| Keywords | `EditKeywords` | `keywords` | `<type>:keywords` |
| Key dates | `EditKeyDates` | `key-dates` | `<type>:key-dates` |
| Identifiers | `EditIdentifiers` | `identifiers` | `<type>:identifiers` |
| Delete | `DeleteRecord` | `delete` | `<type>:delete` |

The address is the record's own address followed by the segment, on all four (FR-005). A record's
own address does not change. Plugin discovery reads the `plugins` module of each installed app, and
`fairdm.core` is not one, so the module is imported at the foot of `fairdm/core/project/plugins.py`,
the first of the four record apps to load.
`menu=False` keeps every page out of the tabs (FR-007).

A registration on `Sample` and `Measurement` reaches every type a portal registers, so a new type
gets the pages with no work (FR-002).

### D2. Who may open a page: `RecordEditingPage`

A mixin placed before `Plugin` in each page's bases. It carries one attribute, `access`, which is
`"change"` or `"delete"`, and two tables of permission names written out in full:

| Core model | `"change"` | `"delete"` |
|---|---|---|
| Project | `project.change_project` | `project.delete_project` |
| Dataset | `dataset.change_dataset` | `dataset.delete_dataset` |
| Sample | `sample.change_sample` | `sample.delete_sample` |
| Measurement | `measurement.change_measurement` | `measurement.delete_measurement` |

The core model of a record is `RecordAccess(record).model`, which resolves a registered type to
`Sample` or `Measurement`.

`dispatch` decides in this order, on every request:

1. `may_use` is `has_perm(request, permission, record)`, the memoised helper in
   `fairdm/contrib/plugins/access.py`.
2. `may_see` is the answer of the record type's own overview page, `can_open(overview, request,
   record)`, exactly as `ContributionPage.dispatch` asks it.
3. Neither `may_see` nor a level on the record that grants the permission
   (`request.user.has_perm(permission, record)`): raise `Http404` (FR-014).
4. Not `may_use`: a visitor is redirected to sign in, and a signed-in person gets
   `PermissionDenied` (FR-013).
5. Otherwise the page runs.

`has_permission()` returns the same answer, so the plugin machinery and the menu agree with
`dispatch`. A classmethod `may_be_used_by(request, record)` gives the menu that answer without an
instance.

This is the rule the project and dataset pages apply today (`visible_to_holder_of` plus
`permission`), so nobody gains or loses a page on those two (FR-012). On a sample it adds the
visibility step the old pages lacked. On a private project or dataset a viewer who may see the
record now gets 403 where they got 404, which is what FR-013 asks and what specification 022 left
for this feature to settle.

`PrivateRecordNotFoundMixin` is not used by these pages.

The base class also supplies what all six share: `get_object()` returns `base_object`, so no page
depends on a `model` attribute; the success address (the record's own page, FR-019); the success
message; and a `record_name` that is `str(record)` except for a measurement, which is named by its
name or, without one, its portal ID.

Each page still states its own access, as architecture decision 0012 asks: `access` is written on
every page, and the rule that reads it lives on the class the page inherits, not on an owning page.

### D3. The Manage menu

`manage_menu(request, record)` in `fairdm/core/editing.py` returns a list of entries, one per page
the viewer may use, in a fixed order: edit details, descriptions, keywords, key dates,
identifiers, delete. Each entry has a label, an icon, an address and a flag marking the delete
entry. It lists only pages that are registered, so the menu grows story by story.

`RecordOverviewPlugin.get_context_data` adds it to every overview as `manage_menu`.

`<c-actions.manage :entries="manage_menu">` draws the dropdown, with a divider before the delete
entry. It draws nothing when it has no entries and its slot is empty (FR-008). Its default slot
takes further entries a record's own template wants to add, which is how FR-009 is met without a
registry.

The component is used in the default `overview.actions` block of `overview/page.html`, so a
measurement's page gains the menu. The project, dataset and sample templates replace their
hand-written menus with it and keep whatever else their block carries, such as the project's Add
dataset button and the dataset's publish control, which sit beside the menu. The `urls` entries and
the `can_manage` and `can_edit` flags that only the old menus read are removed.

No entry disappears between stories. Until US-3 the project and dataset templates pass their
existing delete item through the component's slot, and until US-2 the sample template passes its
key dates item and until US-4 its keywords item the same way.

The project's "Manage contributors" entry is not carried over: specification 022 FR-007 says
managing contributors must not be a Manage menu entry, and the Contributors tab is where it is
done.

### D4. Edit details

`EditDetails(RecordEditingPage, FairDMUpdateView)`, `access = "change"`.

`get_form_class()` by core model:

- Project: `ProjectForm`. Dataset: `DatasetForm`. Both receive `request`, and keep withholding
  visibility and the parent record from anyone below the manage level.
- Sample and measurement: `registry.get_for_model(type(record)).get_form_class()`, with `dataset`
  and `sample` removed from its fields (FR-017). `request` is passed only when the constructor
  names a `request` parameter, read with `inspect.signature`, so a form that forwards `**kwargs`
  to `ModelForm` is not handed one. A type that is not registered falls back to a `ModelForm` of
  `name` and `image`.

The page uses django-mvp's `form_view.html`, which draws the form element and the Save buttons. A
form built by the registry carries a crispy helper that draws a form element and a Save button of
its own, and a form element nested in another ends the outer one early, leaving django-mvp's
buttons outside any form. Where the form carries a crispy helper, the page sets
`helper.form_tag = False` and empties `helper.inputs` before drawing it, so django-mvp's form
element and Save buttons are the only ones.

Until US-2 lands, the page keeps the identifier and date row sets on a project and a dataset, so
nothing is lost between stories. US-2 removes them (FR-016).

### D5. Descriptions

`EditDescriptions(RecordEditingPage, MVPFormView)`, `access = "change"`, with
`VocabularyDescriptionsForm`. The description model comes from a table: `ProjectDescription`,
`DatasetDescription`, `SampleDescription`, `MeasurementDescription`.

Where the vocabulary offers no types, the page says there is nothing to record and offers nothing
to save.

### D6. Key dates and identifiers

`EditKeyDates` and `EditIdentifiers`, both `RecordEditingPage, FairDMUpdateView` with `fields = ()`
so django-mvp draws rows alone, and `access = "change"`.

`fairdm/core/related_records.py` gains `SampleDateInline`, `SampleIdentifierInline`,
`MeasurementDateInline` and `MeasurementIdentifierInline`. Each page picks its row set by core
model in `get_inlines()`.

The rule that an end may not fall before a start applies where the vocabulary has a start and an
end: `ProjectDate` (Start, End) and `DatasetDate` (CollectionStart, CollectionEnd), through the two
existing `date_ordering_formset` subclasses. They move into `related_records.py` in US-1, because
`EditDetails` uses them until US-2 and must not import the two record modules that import it. A
measurement's Setup and TearDown are not read as a start and an end, and a sample's vocabulary has
neither, so no ordering rule applies to them.

When these pages land, the row sets leave `EditDetails` (FR-016, US-2 scenario 9).

### D7. Keywords

`EditKeywords(RecordEditingPage, FairDMUpdateView)`, `access = "change"`, with `KeywordForm`.

`KeywordForm` is repaired, not redesigned:

- it reads the keyword vocabularies configured for the record's core model, with a default of
  none, so a record type with nothing configured gets the free-text field alone (FR-023)
- it no longer rewrites `KeywordForm._meta.model` when it is built
- its crispy helper is treated as in D4, so the page has one form element

What it offers and how it saves are otherwise as today (FR-024).

### D8. Delete

`DeleteRecord(RecordEditingPage, FairDMDeleteView)`, `access = "delete"`, on django-mvp's
`delete_view.html`.

- **Confirmation**: typing the record's name, as projects and datasets ask today. A record with no
  name is confirmed by typing its portal ID.
- **What goes with it** (FR-030): a project and a dataset show counts of what is removed with
  them, by record type, from one method on the page. Listing every row would run to thousands of
  lines. A sample and a measurement use django-mvp's related-objects preview.
- **Protection on GET** (FR-031): a project with a public dataset lists those datasets. A sample
  with measurements names the ones the viewer may see
  (`Measurement.objects.visible_to(request.user)`), by `record_name`, and gives a count for the
  rest, because a measurement can sit in a dataset the viewer holds no level on. In both cases no
  confirmation form is drawn.
- **Protection on POST** (FR-032): django-mvp refuses a restricted or protected record on POST
  itself. `PublicDatasetsProtect` comes from a signal it does not see, so `form_valid` catches that
  one and draws the page again in its protected state.
- **Landing** (FR-033): a sample or a measurement lands on its dataset's page, or on the dataset
  list when the person who deleted it may not open that dataset. A dataset lands on the dataset
  list and a project on the project list, as today. Each sets a success message.
- **Back**: the record's own page.

### D9. What is removed, and when

| Story | Removed |
|---|---|
| US-1 | `Update` and `Descriptions` on project and dataset, with the update and descriptions entries of each overview's `directory` and `crud_views` and the `show_update_action` and `show_descriptions_action` methods that read them. `Edit` and `Descriptions` on sample. `UpdatePlugin`. `DescriptionsPlugin` and `plugins/descriptions.html`. `dataset/plugins/update.html` if nothing else uses it. The hand-written menus |
| US-2 | The sample `KeyDates` page, `KeyDatesPlugin` and `plugins/key-dates.html`. The row sets on `EditDetails` |
| US-3 | `Delete` on project and dataset. `DeletePlugin`. The delete entry of each overview's `crud_views`, `show_delete_action`, and `CRUDDirectoryMixin` on both overviews, which then has nothing left to do |
| US-4 | The sample `Keywords` page, `KeywordsPlugin` and `plugins/keywords.html` |

Code in `fairdm/contrib/generic/forms.py` that only a removed page used goes with that page.
Nothing else in that module is tidied.

Architecture decision 0008 is superseded by a new record written in US-1: a record's editing pages
are six shared pages registered on every record type, each a registration of its own, with dates
and identifiers on pages of their own.

### D10. Links into the pages

Every prompt, checklist item and link that named an old address names the shared page (FR-010):
the overview prompts for visibility and for a missing description, and the readiness checklists of
the project and dataset overviews. The checklist items for dates and identifiers move to the key
dates and identifiers pages in US-2, and the keywords item gains its link in US-4.

### D11. Documentation

- `docs/portal-development/record-editing-pages.md`, new: the six pages, their addresses, how they
  are reached, which right opens each, and that a registered type gets them with no work (FR-034).
- The user guide pages for updating, describing and deleting a project and a dataset are brought
  up to date in the story that changes what they describe.
- `docs/portal-development/overview-pages.md`, `create_a_plugin.md` and
  `docs/contributing/record-page-building-blocks.md` stop naming the removed pages.
- `CHANGELOG.md` gains an entry per story, naming the removed addresses and the removed public
  classes: `UpdatePlugin`, `DeletePlugin`, `KeywordsPlugin`, `DescriptionsPlugin`, `KeyDatesPlugin`.

## Tests

`tests/test_core/test_editing.py` mirrors the one new module, with one `Test<Subject>` class per
page plus `TestAccess`, `TestManageMenu` and `TestRegistration`. Access tests are parametrised over
the four record types and over the accounts a scenario names: a visitor, a signed-in person with no
level, and view, edit and manage levels, given with `ContributionFactory`. A demo sample type and a
demo measurement type stand for registered types.

Existing tests of a page that is removed are replaced by the new tests in the same story. The
task that removes a page names the test classes that go with it, and the story's progress entry
lists them.

## What is not built

- Any change to who may change or delete a record.
- A Manage menu entry contributed by an addon.
- Detecting two people saving the same page.
- Redirects from the old addresses.

## Watch items

- The crispy helper on a registry-built form (D4).
- A measurement in a different dataset from its sample takes its rights from its own dataset.
- `Dataset.objects` hides private datasets. The plugin base resolves a record through
  `all_objects` where the model has one, so the page's own decision is the guard.
