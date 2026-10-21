# Research: autocomplete fields for records, people and organizations

Read against `origin/main` at 7d020a36, with the approved sketch at 7a4f2e4d on top.

## The maintainer's planning notes

### Build on django-tomselect and django-mvp-forms

**Adopted.** django-tomselect 2026.6.2 is added as a runtime dependency. django-mvp-forms 0.6.0,
already a dependency, draws its widgets as daisyUI selects and lists a result under the heading
its `optgroup` key names, through its own `django_tomselect/tomselect.html`. That template only
wins while `mvp_forms` sits above `django_tomselect` in `INSTALLED_APPS`, so the order is set
there and a comment says why. `django_tomselect.middleware.TomSelectMiddleware` is added, because
a model-backed field reads the current request when it validates and when it labels a stored
value. The stylesheets and the script are linked once in `fairdm/templates/base.html`, as the
django-mvp-forms README asks.

### Single and multiple, ready to use

**Adopted.** `fairdm.contrib.autocomplete.fields` holds a single and a multiple field for each of
projects, datasets, samples, measurements, people and organizations, plus the data publication
field, the tag field and the ROR field. Each one names its view by address, and the addresses are
registered in `fairdm.contrib.autocomplete.urls`, which `fairdm/conf/urls.py` already includes.
A developer adds a field to a form and writes nothing else.

### Checkboxes for multiple selection, chips for tags only

**Adopted**, refined by the sketch review into a count: every multiple field shows how many values
are chosen ("3 datasets"), with a checkbox beside each option. django-mvp-forms already draws
that, as its counted control, from two words written on the control (`data-none-text` and
`data-count-text`). Only its own `TomSelectMultiple` copies the words from the select to the
control, so FairDM writes them on the select and copies them across in its own
`django_tomselect/tomselect.html`, which extends django-mvp-forms' template of the same name, the
extension the django-mvp-forms README documents. The copy belongs in django-mvp-forms and is
tracked in this repository's issue for the upstream gaps (see "Gaps in dependencies").

### The search box sits in the dropdown

**Adopted.** Tom Select's `dropdown_input` plugin, turned on through django-tomselect's
`PluginDropdownInput`, which django-mvp-forms already styles.

### Fields can be customised

**Adopted**, as four arguments on each field and nothing else (FR-003, FR-004, FR-009):

- `scope`: `"public"`, `"view"` or `"edit"`, the access a private record needs to be offered.
- `owner`: a person whose own records are offered privately only to that person (FR-009).
- `type`: a registered sample or measurement model the field is narrowed to.
- `depends_on`: the name of another field on the form whose value narrows this one.

Each scope is its own address, so a request can never ask for a wider one (FR-011).

### Vocabulary concepts wait for their own field

**Adopted.** The keyword filters and the contribution roles field move to
`mvp_forms.widgets.TomSelectMultiple` with `counted=True`, which needs no view: the choices are a
vocabulary's concepts, a few hundred at most. `fairdm.contrib.autocomplete.fields.ConceptSelect`
and `ConceptMultiSelect` are removed with django-autocomplete-light.

### Resistant to abuse

**Adopted.** Every field's view counts requests per caller with Django REST framework's
`SimpleRateThrottle`, which FairDM already depends on and already uses for its API
(`fairdm/api/throttling.py`). Four new scopes, `autocomplete_anon_burst`, `autocomplete_anon_day`,
`autocomplete_user_burst` and `autocomplete_user_day`, sit in the same
`REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]` a portal already sets for its API, so there is one place
to change limits. A signed-in caller is counted by account and anyone else by network address,
exactly as the API counts them. The defaults (60 a minute and 3,000 a day for a visitor, 120 a
minute and 10,000 a day signed in) leave a person typing into several fields far inside the
limit. A refused request answers 429 with `Retry-After` before any query runs.

Each request's cost is set by the view, never by the request (FR-022): the page size is fixed at
20 and django-tomselect's `page_size` parameter is ignored, a search is cut to 100 characters,
and no page past the 25th is served. Tom Select waits 300 ms after the last keystroke before it
asks (`load_throttle`, django-tomselect's default) and nothing is asked below two characters, so
a ten-letter word sends at most a request or two (SC-007).

### Sketch review, round 1

**Adopted, all three.** The count is above. The tag field takes `allow_new`, on for the free
keywords form and off for the project list's tag filter. Searching starts at two characters
(`minimum_query_length=2`), and the first page is fetched when a field opens. django-tomselect
refuses an empty search once a minimum length is set, so the same FairDM template lets the empty
search through, which is the second item in the upstream issue.

## What the sketch needs and what it faked

| From `sketch.md` | Met by |
|---|---|
| An address per scope | One URL per kind and scope in `fairdm/contrib/autocomplete/urls.py` |
| Group, name, detail, badge, picture | Each view draws a result on the server from a template, and FairDM's copy of django-tomselect's `render/option.html` shows that HTML. Drawn with Django's autoescaping, so nothing typed by a user reaches the page raw |
| Order: own, public, role-wide, exact identifier first | `RecordAutocompleteView.order_queryset`, from annotations on the visible queryset |
| Sample field narrowed by the dataset | `depends_on="dataset"` → django-tomselect's `filter_by`, with the lookup on the view's allow-list |
| Public filters offer public records to everyone | Filters default to `scope="public"` |
| Collaborators counted on records the person may open | `Person.get_collaborators()` counts the person's own credits, every one of which they may open, since a credit gives at least view. A test pins it (US 5 scenario 7) |
| Publication search reads the CSL item | `title__icontains`, `item__DOI__iexact` and `item__author__icontains` on `LiteratureItem`. No index: literature tables in a portal are hundreds of rows, and SC-002 is measured on samples |
| `__init_subclass__` empties the lists of a shared base | Each concrete view sets its own `search_lookups` and `value_fields`. The shared base sets none, so nothing is lost and no helper class is needed |
| Request-set page size | Ignored, as above |
| Count copied for django-tomselect widgets | FairDM's `django_tomselect/tomselect.html`, as above |
| Throttled-search message in the theme | Not built. See "Gaps in dependencies" |
| Fake views, fields and stand-in pages | Rebuilt test-first. The stand-in create pages, `sketch_pages.py` and `seed_autocomplete_sketch` are deleted |
| Request limits, length and page caps | Built, as above |
| Stored link to an unseen private record | Built in the field (FR-012), see below |
| Profile list filter (FR-009) | The `owner` argument and its `profile` address are built and tested. No profile page has a filter today, so none is wired |
| ROR lookup | A view over the existing `fairdm.contrib.contributors.services.registries.Ror.search`, behind the same limits (FR-025) |
| Keyword filters still on django-autocomplete-light | Moved as above |
| Old libraries installed | Removed (FR-032) |

## A stored link the editor cannot see (FR-012)

django-tomselect validates a value against the view's queryset for the current request
(`forms.py`, `clean`) and labels a stored value from the same queryset (`widgets.py`,
`_get_selected_options`). Both drop a value the person cannot see. Two small overrides in the
FairDM fields close that:

- `get_bound_field(form, name)` records the value the bound form started with, from
  `form.initial`, on that form's copy of the field.
- `clean` accepts that one stored value unchanged even when the view would not offer it, and the
  widget labels it "Private record" when the view's queryset does not hold it.

## Gaps in dependencies

Tracked together in one issue in this repository, opened in the build, describing each gap in
the package that owns it:

1. django-mvp-forms' counted control copies its two words only for its own widget. FairDM copies
   them for django-tomselect's.
2. django-tomselect refuses the empty first-page request once a minimum search length is set.
   FairDM lets it through.
3. django-tomselect's option renderer can only substitute values, so a result with a picture or an
   optional line has to be drawn on the server. FairDM keeps a copy of `render/option.html` with
   one added branch.
4. django-tomselect shows one fixed message, in fixed colours, for any failed search, so a field
   cannot say that searching is paused (FR-021). Not worked around: the server answers 429 with
   `Retry-After`, and the test for the paused message is skipped with this issue's number.

## Decisions settled here

- **Where the code lives.** `fairdm.contrib.autocomplete`, which exists, is installed and owns the
  `autocomplete` URL namespace. Its django-autocomplete-light views and fields are replaced in
  place.
- **Public, per kind.** A project is public when its visibility is public. A dataset is public
  when it and its project are public (`DatasetQuerySet.get_visible`). A sample or measurement is
  public when its dataset is public and published (`RecordVisibilityMixin.visible_to`, the
  anonymous branch). Taken as they stand (D3).
- **Who counts as "yours".** Records the person holds a level on, directly or from a record above
  (`RecordLevelMixin.with_level`).
- **People offered.** `Person.objects.real()`: superusers and django-guardian's anonymous user are
  left out, as on the people list.
- **Admin.** The contributors admin's django-autocomplete-light widget and the dataset admin's
  django-select2 `formfield_overrides` move to Django's `autocomplete_fields`, with `search_fields`
  on each target admin.
- **No migration.** Nothing in the data model changes.

## What already exists

```
field addresses and views          · 3, package · django_tomselect.autocompletes.AutocompleteModelView
ROR search behind a field          · 3, package · django_tomselect.autocompletes.AutocompleteIterablesView over fairdm/contrib/contributors/services/registries.py Ror.search
tag search behind a field          · 3, package · AutocompleteIterablesView over taggit.models.Tag
single and multiple fields         · 3, package · django_tomselect.forms.TomSelectModelChoiceField / TomSelectModelMultipleChoiceField
fields as filters                  · 3, package · django_filters ModelChoiceFilter / ModelMultipleChoiceFilter with field_class
dropdown search, checkboxes        · 3, package · django_tomselect.app_settings PluginDropdownInput, PluginCheckboxOptions
count in place of chips            · 3, package · mvp_forms/static/mvp_forms/tomselect.css counted control (+ the word copy, see gap 1)
group headings                     · 3, package · mvp_forms/templates/django_tomselect/tomselect.html optgroup
keyword and role choices           · 3, package · mvp_forms.widgets.TomSelectMultiple(counted=True)
visible records per user           · 2, repo    · fairdm/core/managers.py with_level, accessible_to, visible_to; get_visible on projects and datasets
collaborators                      · 2, repo    · Contributor.get_collaborators
person and organization details    · 2, repo    · Person.primary_affiliation, Person.orcid, Organization.city/country, ContributorIdentifier
avatar in a result                 · 2, repo    · cotton/contributor/avatar.html
request limits                     · 3, package · rest_framework.throttling.SimpleRateThrottle, as fairdm/api/throttling.py
admin search                       · 4, Django  · ModelAdmin.autocomplete_fields
result rows drawn on the server    · 7, new     · two templates in fairdm/contrib/autocomplete/templates/autocomplete/; searched mvp and fairdm cotton components, none draws a selectable row without links
FairDM's tomselect.html extension  · 7, new     · searched django-mvp-forms and django-tomselect settings for the word copy and the empty first page, neither has one
stored-value keeping (FR-012)      · 7, new     · searched django-tomselect for an initial-value allowance, none
```
