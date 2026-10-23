# Record fields

Record fields are form fields that choose a project, dataset, sample, measurement, person or organization by searching for it. Three more fields in the same module choose a publication, tags or a ROR entry. They are in `fairdm.contrib.autocomplete.fields`, and each sends its searches to an address that FairDM provides and answers with the records the person using the field may reach. This page lists the fields, their arguments, the results and addresses they use, and their limits. For the steps to put one on a form, see [How to add a record field to a form](../how-to/add-a-record-field-to-a-form.md). For the reasoning behind what they offer, see [How record fields decide what to offer](../explanation/how-record-fields-decide-what-to-offer.md).

## The fields

Each kind of record has a single field and a multiple field. Both are built by `record_fields()` and share the arguments below.

| Single field | Multiple field | Chooses | Scopes | Default scope |
|---|---|---|---|---|
| `ProjectChoiceField` | `ProjectMultipleChoiceField` | A project | `public`, `view`, `edit` | `view` |
| `DatasetChoiceField` | `DatasetMultipleChoiceField` | A dataset | `public`, `view`, `edit` | `view` |
| `SampleChoiceField` | `SampleMultipleChoiceField` | A sample | `public`, `view`, `edit` | `view` |
| `MeasurementChoiceField` | `MeasurementMultipleChoiceField` | A measurement | `public`, `view`, `edit` | `view` |
| `PersonChoiceField` | `PersonMultipleChoiceField` | A person | `public` | `public` |
| `OrganizationChoiceField` | `OrganizationMultipleChoiceField` | An organization | `public` | `public` |

```python
from django import forms

from fairdm.contrib.autocomplete.fields import (
    DatasetChoiceField,
    OrganizationMultipleChoiceField,
    PersonChoiceField,
    ProjectMultipleChoiceField,
    SampleChoiceField,
)
from myportal.models import CoreSample  # a sample type of your portal


class EveryKindForm(forms.Form):
    dataset = DatasetChoiceField(scope="edit")
    projects = ProjectMultipleChoiceField(scope="public")
    core_sample = SampleChoiceField(type=CoreSample)
    sample = SampleChoiceField(depends_on="dataset")
    person = PersonChoiceField()
    organizations = OrganizationMultipleChoiceField()
```

## Arguments

A record field takes the arguments of Django's `ModelChoiceField` or `ModelMultipleChoiceField` and five more. The field decides what it offers, so you do not pass a `queryset`.

| Argument | Type | Default | What it does | What it accepts |
|---|---|---|---|---|
| `scope` | `str` | The field's default scope | Sets what the person must be able to do with a record for the field to offer it. | `"public"`, `"view"` or `"edit"`. A person or organization field accepts `"public"` only. |
| `owner` | `Person` or primary key | — | Offers the records that person is credited on, and their private ones only when they are the person using the field. | A person, or a person's primary key. Cannot be given with `scope`. Not for people or organizations. |
| `type` | model class | — | Offers and accepts that type only. | A subclass of the kind's model, for samples and measurements. |
| `depends_on` | `str` | — | Offers only the records that belong to the value chosen in the named field of the same form. | `"dataset"` or `"polymorphic_ctype"`, for samples and measurements. |
| `prefer` | `str` | — | Lists the records that belong to the value chosen in the named field first, in a group of their own, and offers the rest after them. It narrows nothing. | The same names as `depends_on`. |

A field raises `ValueError` when it is created if:

- `scope` is not one the kind offers,
- `owner` is given with `scope`, or to a person or organization field,
- `depends_on` or `prefer` names a field the kind's address does not allow,
- `type` is not a subclass of the kind's model, or the kind is a project, dataset, person or organization.

### Dependent fields

A field with `depends_on` follows the field it names.

- In the browser, it searches only the records of the value chosen in the other field and clears its own choice when that value changes.
- On submit, it reads the value of the other field from the form's own data and accepts only a record that belongs to it. Any other record is refused with `invalid_choice`. The page's address plays no part.
- When the other field has no value, the field is not narrowed.

### Preferred fields

A field with `prefer` lists the records that belong to the value of the field it names under a heading of their own, such as "Samples in this dataset". It accepts the same records whatever the other field holds. When the other field has no value, the records are listed as usual.

## Scopes

| Scope | Offers |
|---|---|
| `public` | Public records, to everyone, signed in or not. |
| `view` | Public records, and the records the person may view. |
| `edit` | Only the records the person may edit. A person who is not signed in is offered nothing. |
| `profile` | The records one person, named by `owner`, is credited on. Set by giving `owner`, never by `scope`. |

A record is public when:

- a project's visibility is public,
- a dataset's visibility is public and so is its project's, or it has no project,
- a sample's or measurement's dataset is public and published.

A person may view or edit a record when they hold that level on it, on the project above a dataset, or on the dataset or its project above a sample or measurement. A right the portal gives on every record, as the superuser and Data Curator roles have, offers all of them. The levels are in [Contribution levels and record access](contribution-levels-and-record-access.md).

## Validation

A field accepts a value only when it would have offered that record to the same person. Any other record is refused with the error code `invalid_choice`.

- A record that already holds a link to a record the person cannot see keeps it. The field shows the stored link as "Private record", without a name, and accepts it when the form is saved unchanged. It never offers that record in a search.
- The person is the user on the form's `request` attribute. If the form has none, the field uses the request it was given (`given_request`), and then the request django-tomselect's middleware holds for the current thread.
- A form built outside any request, in a script or a test, accepts what is in the field's `queryset` and nothing by default.

## People and organizations

A person and an organization are public information, so these fields offer them at the `public` scope only and take neither `owner`, `depends_on` nor `prefer`.

- A person is found by name, by an alternative name, or by an ORCID iD typed exactly.
- An organization is found by name, by an alternative name, or by a ROR identifier typed exactly.
- An identifier typed exactly lists that person or organization first. A part of an identifier finds nothing.
- Superusers and the anonymous placeholder account are never offered. An email address is not searched and is never part of a result.

Results come in two groups:

| Kind | First group | Second group |
|---|---|---|
| Person | "People you have worked with": people credited on a record the searcher can open | "Everyone else" |
| Organization | "Your organizations": those where the searcher has a verified affiliation that has not ended | "Other organizations" |

A person's row shows their picture or initials, their primary affiliation and their ORCID iD, and marks a person nobody has claimed. An organization's row shows its city and country and no identifier.

## PublicationChoiceField

| Argument | Type | Default | What it does | What it accepts |
|---|---|---|---|---|
| Django's `ModelChoiceField` arguments | | | Choose one publication from the portal's literature. | Every argument except `queryset`. There is no `scope`, because a publication carries no visibility. |

The field accepts any publication that exists. A publication is found by part of its title, by part of an author's name, or by its DOI typed exactly. A DOI typed with a `doi:` prefix or as an address finds the same publication. Its address is `autocomplete:publication`.

## TagsField

`TagsField` chooses tags, which are words and not records. The tags are drawn as chips with a button to remove each one. The field cleans to a list of strings, with the spaces around each removed, empty entries dropped and repeats kept once.

| Argument | Type | Default | What it does | What it accepts |
|---|---|---|---|---|
| `scope` | `str` | `"view"` | Decides which tags are offered. | `"view"` offers the tags in use on records the person may view. `"public"` offers only the tags in use on public records. |
| `allow_new` | `bool` | `False` | Lets the person type a tag nobody has used. | With `True`, any tag that is not empty. With `False`, only a tag in use on the records its scope offers. |

A tag is offered when it is in use on a project, dataset, sample or measurement that the record fields of the same scope would offer. A tag in use on no record is not offered.

## RorChoiceField

`RorChoiceField` looks an organization up in the Research Organization Registry by name and chooses one entry. Its value is the ROR ID, or the ROR address, as the person chose it.

| Argument | Type | Default | What it does | What it accepts |
|---|---|---|---|---|
| Django's `ChoiceField` arguments | | | Choose one ROR entry. | Every argument. `label` defaults to "ROR ID". |

- The field accepts any value in the form of a ROR ID or its address and never asks ROR to check it, so a form saves while ROR does not answer.
- A value that is not in that form is refused with `invalid_choice`.
- A field that is not required accepts an empty value.
- The search starts at three characters, shows nothing for an empty search and lists at most ten active organizations, so there is one page.
- When ROR does not answer, the address answers with status 503 and an empty list.

## Filters

Both filters are in `fairdm.contrib.autocomplete.filters`.

| Filter | Arguments | Draws | Default scope |
|---|---|---|---|
| `RecordMultipleFilter` | The multiple field class, `scope`, and the arguments of django-filter's `ModelMultipleChoiceFilter` except `queryset` | The multiple field of one kind in a filter set | `"public"` |
| `TagFilter` | `scope`, and the arguments of django-filter's `Filter`. `field_name` names the tag's name, such as `"tags__name"`. | `TagsField` with no way to add a tag | `"public"` |

Choosing several records or tags keeps the rows that point at any of them. A filter set must be built with the request, or the filter offers and accepts nothing. The list filters FairDM ships use these: the dataset list's project filter, the sample list's dataset filter, the measurement list's dataset and sample filters, and the project list's owner, contributor and tag filters. A filter generated for a registered type's relation to a project, dataset, sample or measurement is a `RecordMultipleFilter`.

## Results

Each address answers with a page of results. A result carries these keys.

| Key | Holds | Present on |
|---|---|---|
| `id` | The record's primary key, which the form submits. | Records, people, organizations, publications, tags |
| `name` | The record's name. | Records, people, organizations, tags |
| `private` | `true` when the record is not public. | Records |
| `project` | A dataset's project name, or `null`. | Datasets |
| `type` | The record's type, such as "rock sample". | Samples, measurements |
| `local_id` | The creator's own identifier for the record. | Samples, measurements |
| `dataset` | The name of the record's dataset. | Samples, measurements |
| `optgroup` | The heading of the group the result is listed under. Absent when the page holds only public records. | Records, people, organizations |
| `detail` | A person's primary affiliation, an organization's place, or a ROR entry's kind and place. | People, organizations, ROR |
| `unclaimed` | `true` when nobody has claimed the profile. | People |
| `title`, `authors`, `year`, `doi` | The publication's title, its authors' family names joined with commas, a number or `null`, and its DOI or an empty string. | Publications |
| `value`, `label` | A ROR entry's address and the organization's name. | ROR |
| `html` | The row, drawn on the server. | All |

Record results are grouped, in this order:

| Group | Heading | Holds |
|---|---|---|
| Preferred | "Samples in this dataset", and so on | Records that match the field named by `prefer` |
| Own | "Your samples" | Records the person holds the view level on |
| Public | "Public samples" | Public records |
| Other | "Other samples" | Any further records a portal-wide right lets the person see |

A record appears once, in its first group. A record that matches the search text exactly is listed first. The rest follow group by group, in order of name.

## Searching

| Kind | Found by (contains, ignoring case) | Listed first when typed exactly |
|---|---|---|
| Project | Name | UUID |
| Dataset | Name | UUID |
| Sample | Name, local ID, identifier value | Local ID, UUID, identifier value |
| Measurement | Name, local ID | Local ID, UUID |
| Person | Name, alternative names | ORCID iD |
| Organization | Name, alternative names | ROR identifier |
| Publication | Title, author's name | DOI |
| Tag | Name | — |

## Addresses

The addresses are under the `autocomplete` namespace and the `autocomplete/` path. The scope belongs to the address, so a request cannot widen it.

| Name | Path | Serves |
|---|---|---|
| `autocomplete:<kind>-<scope>` | `records/<kind>/<scope>/` | A project, dataset, sample or measurement at `public`, `view`, `edit` or `profile` scope |
| `autocomplete:person-public` | `records/person/` | People |
| `autocomplete:organization-public` | `records/organization/` | Organizations |
| `autocomplete:publication` | `publication/` | Publications |
| `autocomplete:tag-public`, `autocomplete:tag-view` | `tags/<scope>/` | Tags |
| `autocomplete:ror` | `ror/` | ROR entries |

The `profile` address takes the owner's primary key in an `owner` query parameter.

## Limits

| Limit | Value |
|---|---|
| Results in a page | 20, whatever page size a request names |
| Last page served | 25 |
| Longest search text | 100 characters, cut when longer |
| Filters a request may name | None for projects, datasets, people, organizations, publications, tags and ROR. `dataset` and `polymorphic_ctype` for samples and measurements. A request naming any other filter is offered nothing. |
| Ordering a request may name | None. An ordering is ignored. |
| A search that fails | Status 500 and an empty list |
| A caller over a rate limit | Status 429, a `Retry-After` header and an empty list, before anything is searched |

### Request rates

Each address limits a caller with four throttles. A signed-in caller is counted by account and anyone else by network address. The rate of each scope is set in `REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]` and described in [Settings](settings.md). A scope left out uses the default on its throttle class. For why there are two limits, see [How API callers are limited](../explanation/how-api-callers-are-limited.md).

| Throttle class | Scope |
|---|---|
| `AutocompleteAnonBurstThrottle` | `autocomplete_anon_burst` |
| `AutocompleteAnonDailyThrottle` | `autocomplete_anon_day` |
| `AutocompleteUserBurstThrottle` | `autocomplete_user_burst` |
| `AutocompleteUserDailyThrottle` | `autocomplete_user_day` |

The throttles are in `fairdm.contrib.autocomplete.throttling`. To change the rates, see [How to change the API rate limits](../how-to/change-the-api-rate-limits.md).

## Classes behind the fields

A field needs none of these to work. They matter to a portal that builds a field of its own on the same address and limits.

Views, in `fairdm.contrib.autocomplete.views`:

| Class | Serves |
|---|---|
| `LimitedAutocompleteMixin` | The page size, page depth, search length, filter and ordering limits, and the throttles, for every view below |
| `RecordAutocompleteView` | The base of the record views: scope, grouping and exact-match ordering |
| `ProjectAutocompleteView` | Projects |
| `DatasetAutocompleteView` | Datasets, taken from `Dataset.all_objects` |
| `DatasetRecordsAutocompleteView` | The base of the two views below, for records that sit inside a dataset |
| `SampleAutocompleteView` | Samples |
| `MeasurementAutocompleteView` | Measurements |
| `ContributorAutocompleteView` | The base of the two views below, with the "near first" grouping |
| `PersonAutocompleteView` | People |
| `OrganizationAutocompleteView` | Organizations |
| `PublicationAutocompleteView` | The portal's literature |
| `TagAutocompleteView` | Tags in use on records the requester may see |
| `RorAutocompleteView` | The ROR registry |

`scoped_view(view_class, scope)` returns the subclass of a record view that serves one scope. `RecordAutocompleteView.for_scope(scope)` does the same. Each scope is its own class because django-tomselect rebuilds a view without the arguments given to `as_view()` when it validates a value. See [ADR 0038](../../adr/0038-each-autocomplete-scope-is-its-own-view.md).

```python
from django.urls import path

from fairdm.contrib.autocomplete.views import SampleAutocompleteView, scoped_view

urlpatterns = [
    path("samples/edit/", scoped_view(SampleAutocompleteView, "edit").as_view()),
]
```

Fields and widgets, in `fairdm.contrib.autocomplete.fields`:

| Name | Is |
|---|---|
| `record_fields()` | Makes the single and the multiple field for one record view |
| `RecordFieldMixin`, `RecordChoiceFieldMixin`, `RecordMultipleChoiceFieldMixin` | Carry the arguments, the validation through the view and the kept stored value |
| `RecordSelectWidget`, `RecordSelectMultipleWidget` | Write the address, the dependency and the count words on the control, built on `RecordSelectMixin` |
| `TagsWidget` | Draws the chips of `TagsField` |
