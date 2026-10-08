# Research: One set of editing pages for projects, datasets, samples and measurements

Investigated against `main` at `9abbd75a` on 2026-10-07. Each finding ends with what the plan does
about it. There are no planning notes and no prototype for this feature.

## What exists today

| Record | Details | Descriptions | Keywords | Key dates | Identifiers | Delete |
|---|---|---|---|---|---|---|
| Project | `Update`, an additional view of the overview (`fairdm/core/project/plugins.py:110`) | `Descriptions`, additional view (`:192`) | none | rows on the details page | rows on the details page | `Delete`, additional view (`:149`) |
| Dataset | `Update` (`fairdm/core/dataset/plugins.py:110`) | `Descriptions` (`:150`) | none | rows on the details page | rows on the details page | `Delete` (`:181`) |
| Sample | `Edit`, name and image only (`fairdm/core/sample/plugins.py:324`) | `Descriptions`, add and remove rows (`:339`) | `Keywords` (`:352`) | `KeyDates` (`:365`) | none | none |
| Measurement | none | none | none | none | none | none |

The generic bases behind the sample pages are `UpdatePlugin` and `DeletePlugin` in
`fairdm/core/plugins.py:570, 611` and `KeywordsPlugin`, `DescriptionsPlugin` and `KeyDatesPlugin` in
`fairdm/contrib/generic/plugins.py:18, 28, 58`. `DeletePlugin` is used by nothing and names a
template that is not in the repository.

## Findings, and what the plan does about each

| # | Finding | Decision |
|---|---|---|
| 1 | One plugin can be registered against several models: `PluginRegistry.register(*models)` (`fairdm/contrib/plugins/registration.py:45`), and `Plugin.get_urls` binds the model per mount (`base.py:99`). `ContributionList` is already registered on all four record types (`fairdm/contrib/contributors/plugins/shared.py:900`). `menu=False` mounts the address and leaves the page out of the tabs (`registration.py:182`) | Six plugins, each registered once on the four models with `menu=False` (D1) |
| 2 | A duplicate plugin name or address on one model is refused at start-up (`checks.py:161`) | The old pages are removed in the story that registers their replacement |
| 3 | Since specification 022, `user.has_perm(perm, record)` is answered from the person's level on the record, its dataset and its project (`fairdm/contrib/contributors/permissions.py:68`, `access.py:19`). Changing needs the edit level. Deleting needs the manage level, on all four record types | The pages ask the permissions that already exist, written out per record type (D2). Decision 6 of the specification's `decisions.md`, which described an uneven right to delete, no longer applies |
| 4 | `RecordAccess(record).model` gives the core model of any registered type (`access.py:79`), and `ContributionPage.dispatch` (`shared.py:350`) already answers 404 through the record's overview check and then refuses by level | The same two steps, in one base class for the six pages (D2) |
| 5 | The project and dataset pages answer 404 to anyone refused on a private record, including a person who may see it (`PrivateRecordNotFoundMixin`, `fairdm/contrib/plugins/mixins.py:10`). Specification 022 recorded that as something to revisit when these pages were rebuilt. The sample pages have no visibility check at all | 404 only when the viewer may not see the record. A viewer who may see it and not use the page is refused, and a visitor is sent to sign in (FR-013, FR-014) |
| 6 | The Manage menu is written by hand in three templates inside `{% block overview.actions %}`, with links from a `urls` dictionary each overview builds. A measurement's page has none. The project's menu still carries "Manage contributors", which specification 022 FR-007 says must not be a Manage menu entry | One function lists the entries a viewer may use, and one component draws them on all four pages (D3). The contributors entry is dropped, as 022 requires. Nothing else is in the menu today, so FR-009 has nothing further to keep |
| 7 | `ProjectForm` and `DatasetForm` withhold visibility and the parent record from anyone below the manage level (`fairdm/core/forms.py:8`) | Kept as they are |
| 8 | A sample's or a measurement's form comes from its registration: `registry.get_for_model(type(record)).get_form_class()` (`fairdm/registry/registry.py:100`, `config.py:537`). Without a custom form it is built on `SampleFormMixin` or `MeasurementFormMixin`, which keep the `dataset` field for a manager and never withhold `sample`. The built form carries a crispy helper with its own Save button. A portal's own form class may not accept `request`. The portal has no page that creates a sample or a measurement, so this form is "the fields offered on creation" | The details page uses that form class, removes `dataset` and `sample` from it, passes `request` only where the form takes it, and is tested to draw one Save control (D4) |
| 9 | `VocabularyDescriptionsForm(related_model=…, instance=…)` draws one area per description type and removes a row saved empty (`fairdm/core/descriptions.py:14`). All four records have a description model with a `VOCABULARY` | Used for all four (D5). The sample's row-based page goes |
| 10 | Dates and identifiers are edited as row sets declared in `fairdm/core/related_records.py`, one class per model, capped at one row per type. Only project and dataset classes exist. django-mvp draws a page of rows alone when a view's `fields` is empty (`mvp/views/inline.py:221` in the installed package). `date_ordering_formset` refuses an end before a start (`fairdm/core/formsets.py:10`) | Add the four missing row-set classes. Each page is rows alone (D6). The ordering rule stays on the two record types whose vocabulary has a start and an end: projects and datasets |
| 11 | A partial date is kept with its precision by `PartialDateField` (`fairdm/db/fields.py:60`) and its form field (`fairdm/forms/fields.py:69`) | Nothing to build for FR-027 beyond a test |
| 12 | The identifier the portal gives a record is its `uuid`, a non-editable field. It is never a row among the record's identifiers | FR-029 holds already. A test pins it |
| 13 | The sample keywords page cannot be opened today. `KeywordForm` (`fairdm/contrib/generic/forms.py:148`) reads a settings name that does not exist for any sample type and raises. It also rewrites its own `Meta.model` each time it is built. No test opens the page | The specification asks for the page "as it works today" (FR-024) and for it to work with no vocabulary configured (FR-023). The form is repaired to the smallest working state: it reads the configured vocabularies with a default of none, and stops rewriting its own class (D7). What the page offers is otherwise unchanged, and #298 still replaces it |
| 14 | Deleting a project with a public dataset raises `PublicDatasetsProtect` from a `pre_delete` receiver (`fairdm/core/project/models.py:300`). Deleting a sample with measurements raises `RestrictedError`, because `Measurement.sample` is `on_delete=RESTRICT` (`fairdm/core/measurement/models.py:75`). django-mvp's delete page shows protected objects on GET and refuses a restricted record on POST. It does not see the project's signal | The delete page catches `PublicDatasetsProtect` on POST and shows the page again (D8, FR-032) |
| 15 | `str(measurement)` is its value. Its overview names it by name, or by portal ID when it has none | The pages name a measurement as its overview does |
| 16 | Record architecture decision 0008 says a record has one page for its own attributes, that dates and identifiers are rows on that page, and that the page is an additional view of the overview | The specification reverses all three. A new decision record supersedes 0008 (D9) |
| 17 | Links to the old addresses: three overview templates, the readiness checklists of the project and dataset overviews, five documentation pages, and about 220 lines across nine test modules | Each is repointed in the story that removes the page it names |

## Dependencies

None added. The pages use django-mvp 0.26 form, inline and delete views, which the project already
depends on.

## Not investigated further

- Rebuilding keyword editing against the controlled vocabularies. That is #298.
- Moving a sample or a measurement between datasets. The specification rules it out (FR-017).
- A way for an addon to add a Manage menu entry. The specification rules it out.
