# Implementation Plan: autocomplete fields for records, people and organizations

**Branch**: `032-record-search-fields` | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md) | **Sketch**: [sketch.md](sketch.md)

## Summary

`fairdm.contrib.autocomplete` is rebuilt on django-tomselect. It holds one view per kind of record
behind one address per scope, a single and a multiple field for each kind, and filter classes
that draw those fields. Results are drawn on the server from two templates approved in the sketch.
Every form, filter and admin page in FairDM that used django-autocomplete-light, django-select2,
django-addanother or the Selectize widget moves to these fields or to Django's own admin
autocomplete, and the three libraries are removed. The sketch's Python is replaced, not extended:
its templates and copy stay, and everything behind them is rebuilt test-first.

## Technical context

- Python 3.12 and 3.13, Django 5.2 to 6.1, PostgreSQL with PostGIS in development, tests and CI.
- New runtime dependency: `django-tomselect>=2026.6.2,<2027`. It replaces three
  (django-autocomplete-light, django-select2, django-addanother), so the dependency tree shrinks.
- django-mvp-forms 0.6.0 draws the controls and their groups. Django REST framework, already a
  dependency, supplies the request limits.
- No model or migration changes.

## Constitution check

| Article | How the plan meets it |
|---|---|
| I Testing | Every story's tests are written first and seen to fail. Views through the test client on their real addresses, fields through real forms. Wording and appearance get no tests |
| II Simplicity, III Anti-abstraction | One base view, `RecordAutocompleteView`, with four concrete record views as its second use. One function makes each pair of fields. No registry, no settings beyond the throttle rates |
| V Security | Scope is fixed by the address. Validation reuses the view's queryset for the request. Result HTML is drawn by Django templates with autoescaping. Limits answer before any query |
| VI Documentation | A how-to page for portal developers, a reference page for the fields and their settings, and every page that documents a removed widget is updated in the same pull request. CHANGELOG lists the breaking changes with a migration guide |
| VII Dependencies | One added, three removed. `deptry` passes |
| VIII i18n | Every label, heading, placeholder and count word is wrapped with `gettext_lazy` |
| IX Data model | Nothing changes |
| X Cohesion | The views, fields and filters are classes in three modules of one app |

## Design

### D1. Module layout

```
fairdm/contrib/autocomplete/
  views.py       RecordAutocompleteView and its four record views, PersonAutocompleteView,
                 OrganizationAutocompleteView, PublicationAutocompleteView,
                 TagAutocompleteView, RorAutocompleteView
  throttling.py  AutocompleteBurstThrottle, AutocompleteDailyThrottle
  fields.py      the field pairs, PublicationChoiceField, TagsField, RorChoiceField
  filters.py     RecordFilter, RecordMultipleFilter, TagFilter
  urls.py        one path per kind and scope
  templates/autocomplete/record_option.html, contributor_option.html   (from the sketch)
fairdm/templates/django_tomselect/tomselect.html          (extends django-mvp-forms')
fairdm/templates/django_tomselect/render/option.html      (django-tomselect's, one branch added)
```

`fairdm/contrib/autocomplete/records.py`, `records_fields.py`, `sketch_pages.py` and
`fairdm/management/commands/seed_autocomplete_sketch.py` from the sketch are deleted. The demo
gets a seed of its own in `demo/` (D10).

### D2. The views

`RecordAutocompleteView(AutocompleteModelView)` holds what the four record views share:

- `scope`: `"public"`, `"view"`, `"edit"` or `"profile"`, set by `as_view(scope=…)` in `urls.py`
  and never read from the request.
- `get_queryset()`:
  - `public`: the public records (D3), to everyone.
  - `view`: public records together with `accessible_to(user, VIEW)`.
  - `edit`: `accessible_to(user, EDIT)`, nothing for someone not signed in.
  - `profile`: the records the owner (a person's UUID in the address) is credited on. Private ones
    are included only when the requester is that owner, otherwise the public ones alone.
  - Each is annotated with a `group` rank (own, public, other) and, when the search is exact on an
    identifier the view names, an `exact` rank, then ordered by exact, group, name and pk.
- `search_lookups` and `exact_lookups` per concrete view. The search text is cut to 100 characters
  first.
- `allowed_filters`: the only `filter_by` lookups the view accepts (`dataset_id` and
  `polymorphic_ctype_id` for samples and measurements, nothing for the others). A request naming
  any other lookup is answered 400 and nothing is searched (FR-011).
- `page_size = 20`, the `page_size` request parameter ignored, no page past 25 (FR-022).
- `hook_prepare_results()` adds each result's `optgroup` heading (none when the page holds one
  group, as approved) and its `html`, drawn from `autocomplete/record_option.html`.
- `dispatch()` runs the two throttles before anything else (D5).
- `skip_authorization = True` and `allow_anonymous = True`: access is decided by the queryset, and
  django-tomselect's model-permission check would refuse a visitor every public record.

The four record views set `model`, the lookups and the detail line approved in the sketch:

| View | Searches | Exact first | Detail line | Badge |
|---|---|---|---|---|
| `ProjectAutocompleteView` | name | uuid | status | Private |
| `DatasetAutocompleteView` | name | uuid | project | Private |
| `SampleAutocompleteView` | name, local ID, identifier | local ID, identifier, uuid | type · local ID · dataset | Private |
| `MeasurementAutocompleteView` | name, local ID | local ID, uuid | type · local ID · dataset | Private |

`PersonAutocompleteView` and `OrganizationAutocompleteView` search name, alternative names and the
ORCID or ROR identifier, exact identifier first. People come from `Person.objects.real()`. People
the requester has worked with (`get_collaborators()`) and organizations they hold a current
affiliation to are grouped first. Rows are drawn from `autocomplete/contributor_option.html`:
picture or initials, name, affiliation, ORCID beneath it, and "Unclaimed" for a person nobody has
claimed. An organization shows its place and no ROR. No email is searched or shown.

`PublicationAutocompleteView` searches title, authors and DOI on `LiteratureItem`, exact DOI
first. `TagAutocompleteView` and `RorAutocompleteView` are `AutocompleteIterablesView`s over
taggit's tags and `Ror.search()`. A `RegistryUnavailable` from ROR answers 503.

### D3. What public means

Taken as FairDM applies it today (decisions D3): a project by its own visibility, a dataset by
`Dataset.all_objects.get_visible()`, a sample or measurement by a public and published dataset.
Each view writes this as one `public_records()` method, so R14 has one place per kind to change.

### D4. The fields

`fields.py` makes each pair with one function, `record_fields(view_name, …)`, returning the single
and the multiple class, so the six pairs read as six lines. Each field:

- takes `scope`, `owner`, `type` and `depends_on` and turns them into the address and django-tomselect's
  `filter_by`. Defaults: a single field `"view"`, a multiple field `"public"` (FR-005). The forms
  that place a record inside another pass `scope="edit"`.
- uses `PluginDropdownInput` and `PluginClearButton`, and on the multiple field
  `PluginCheckboxOptions` with the count words written on the select (`data-none-text`,
  `data-count-text`).
- sets `minimum_query_length=2`, `preload="focus"`, `load_throttle=300`, `loading_class="ts-loading"`.
- keeps a stored value the person cannot see (FR-012): `get_bound_field()` records the form's
  initial value on that form's copy of the field, `clean()` accepts it unchanged, and the widget
  labels it "Private record" when the view does not hold it.

`TagsField(allow_new=False)` is the multiple field over tags drawn as chips with a remove button.
`allow_new=True` turns on Tom Select's `create`. It cleans to a list of strings.
`RorChoiceField` is a single field over ROR whose value is the ROR ID.

### D5. Request limits

`throttling.py` holds two `SimpleRateThrottle` subclasses, each counting a signed-in caller by
account and anyone else by address, scopes `autocomplete_anon_burst`, `autocomplete_anon_day`,
`autocomplete_user_burst`, `autocomplete_user_day`. The default rates are added to
`REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]` in `fairdm/api/settings.py` beside the API's. A refused
request answers 429 with `Retry-After` and an empty result list, before any query. The cache is
the portal's default cache, as the API's limits use. The "searching is paused" message (FR-021) is
not built: its test is written and skipped, naming the upstream-gaps issue.

### D6. FairDM's two django-tomselect templates

- `django_tomselect/tomselect.html` extends django-mvp-forms' template of the same name and adds
  one `tomselect_extra_js` block: it copies the two count words to the control, and lets the empty
  first-page search through despite the two-character minimum. The block's comment names the
  upstream-gaps issue.
- `django_tomselect/render/option.html` is django-tomselect's with one branch added at the top:
  a result carrying `html` is shown as drawn. The comment names the django-tomselect version it was
  copied from and the issue.

### D7. The forms and filters

| Where | Field | Scope |
|---|---|---|
| `SampleFormMixin.dataset`, `MeasurementFormMixin.dataset` | `DatasetChoiceField` | edit |
| `MeasurementFormMixin.sample` | `SampleChoiceField(depends_on="dataset")` | view |
| `DatasetForm.project` | `ProjectChoiceField` | edit |
| `DatasetForm.reference` | `PublicationChoiceField` | — |
| `ProjectForm.owner` | `OrganizationChoiceField` | — |
| `AffiliationForm.organization`, organization profile `parent`, `PersonCreateForm.affiliations` | organization fields | — |
| person merge `merge_into`, ownership transfer `new_owner` | `PersonChoiceField` | — |
| `UpdateContributionForm.roles`, project keyword filters | `mvp_forms.widgets.TomSelectMultiple(counted=True)` | — |
| `KeywordForm.tags` | `TagsField(allow_new=True)` | — |
| organization form ROR lookup | `RorChoiceField` | — |
| project list owner, contributor; dataset list project; sample list dataset; measurement list dataset, sample | `RecordMultipleFilter` | public |
| project list tags | `TagFilter` | — |
| generated filters of a registered type, for a related project, dataset, sample or measurement | `RecordMultipleFilter` | public |
| generated forms of a registered type, for a related project, dataset, sample or measurement | the single field | edit for the record it sits in, view otherwise |

`QuickAddContributionForm` and the unused `PersonSelect2Widget` and `OrganizationSelect2Widget`
are deleted, not moved: nothing uses them.

### D8. The admin

The contributors admin's django-autocomplete-light widget and the dataset admin's django-select2
`formfield_overrides` are replaced by `autocomplete_fields` naming the same relations, with
`search_fields` on each target admin where it is missing.

### D9. Removal

django-autocomplete-light, django-select2 and django-addanother leave `pyproject.toml`, `uv.lock`,
`INSTALLED_APPS`, `fairdm/conf/urls.py` and the select2 cache settings. `fairdm/templates/django_addanother/`,
`SelectizeWidget`, `CreatorsFormField`, the old `views.py` and `fields.py` contents, and the
Select2 suggestions in `fairdm/utils/inspection.py` go. `deptry`'s ignore list loses the three.

### D10. Demo and documentation

- `demo/`: a management command seeding what the walkthrough needs, adapted from the sketch's
  seed, and one demo form using `SampleChoiceField(type=…)`.
- `docs/portal-development/`: a how-to, "Add a record field to a form or filter", and a reference
  page for every field, its arguments and defaults, the addresses and the throttle settings.
- `docs/portal-development/filtering-by-vocabulary.md`, `measurements.md`,
  `forms-and-filters/sample-mixins.md`, `contributors.md` and
  `docs/portal-administration/managing_contributors.md` updated to the new fields.
- `CHANGELOG.md`: the breaking changes from the spec with a migration guide.
- `CONTEXT.md`: the term Autocomplete field.

## Story order

US1 carries the foundation (D1 to D6). Then US2, US3, US5, US6, US7, US8, and US4 last, because
US4's removal needs every other form off the old libraries first. Each story starts from the
previous story's accepted commit.

## Risks

- **django-tomselect's request middleware.** A field validated outside a request (a form built in
  a test or a management command) has no request and validates against nothing. Tests build forms
  inside a request, and the fields document it.
- **Portals importing the removed libraries.** Listed in the CHANGELOG's migration guide.
- **The two template copies drift from django-tomselect.** The version is pinned below the next
  calendar year, and the issue asks for the upstream changes that remove them.

## Complexity tracking

| Addition | Why |
|---|---|
| `django-tomselect` dependency | The maintainer's choice of library. Replaces three |
| Two django-tomselect template overrides | The approved screens need a count and a first page that the packages do not give yet. Tracked for removal |
| `RecordAutocompleteView` base | Four concrete record views share scope, grouping, limits and ordering |
