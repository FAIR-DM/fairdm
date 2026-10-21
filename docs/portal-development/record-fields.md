# Record fields

Record fields are form fields that choose a project, a dataset, a sample, a measurement, a person
or an organization by searching for it. Each field
sends its searches to an address that FairDM provides and answers with the records the person
using the field may reach. The fields are in `fairdm.contrib.autocomplete.fields`. For the steps
to add one to a form, see [How to add a record field to a form](add-a-record-field.md).

## Fields

| Single field | Multiple field | Chooses |
|---|---|---|
| `ProjectChoiceField` | `ProjectMultipleChoiceField` | a project |
| `DatasetChoiceField` | `DatasetMultipleChoiceField` | a dataset |
| `SampleChoiceField` | `SampleMultipleChoiceField` | a sample |
| `MeasurementChoiceField` | `MeasurementMultipleChoiceField` | a measurement |
| `PersonChoiceField` | `PersonMultipleChoiceField` | a person |
| `OrganizationChoiceField` | `OrganizationMultipleChoiceField` | an organization |

## Arguments

Both fields take the arguments of Django's `ModelChoiceField` and `ModelMultipleChoiceField`,
except `queryset`, which the field decides, and five more.

| Argument | Default | Meaning |
|---|---|---|
| `scope` | `"view"` | What the person must be able to do with a record for the field to offer it. A field that places a record inside another needs `"edit"`. A filter on a public list passes `"public"`. |
| `owner` | none | A person, or a person's primary key. The field then offers the records that person is credited on, and their private ones only when they are the one using the field. Cannot be given with `scope`. Not for people or organizations. |
| `type` | none | A registered sample or measurement model. The field then offers and accepts that type only. Samples and measurements only; any other model raises `ValueError`. |
| `depends_on` | none | The name of another field on the same form. The field then offers only the records that belong to the value chosen in that field. Samples and measurements accept `"dataset"`. |
| `prefer` | none | The name of another field on the same form. The field then lists the records that belong to the value chosen in that field first, in a group of their own, and offers the rest after them. It narrows nothing and changes nothing the field accepts. Samples and measurements accept `"dataset"`. |

## Examples

One field of each kind on a form. Each line works as written in a form built inside a request.

```python
from django import forms

from demo.models import RockSample
from fairdm.contrib.autocomplete.fields import (
    DatasetChoiceField,
    MeasurementChoiceField,
    OrganizationMultipleChoiceField,
    PersonChoiceField,
    ProjectChoiceField,
    ProjectMultipleChoiceField,
    PublicationChoiceField,
    RorChoiceField,
    SampleChoiceField,
    TagsField,
)


class EveryFieldForm(forms.Form):
    # A record this form places something inside needs edit access.
    dataset = DatasetChoiceField(scope="edit")
    # A link to a record needs view access, the default.
    project = ProjectChoiceField()
    # Several projects, public ones only.
    projects = ProjectMultipleChoiceField(scope="public")
    # Only samples of one registered type, found by name, local ID or identifier.
    rock_sample = SampleChoiceField(type=RockSample)
    # Only the samples of the dataset chosen in the field above.
    sample = SampleChoiceField(depends_on="dataset")
    # The measurement is listed after the ones in the chosen dataset.
    measurement = MeasurementChoiceField(prefer="dataset")
    person = PersonChoiceField()
    organizations = OrganizationMultipleChoiceField()
    reference = PublicationChoiceField()
    keywords = TagsField(allow_new=True)
    ror = RorChoiceField()
```

## Filters

`fairdm.contrib.autocomplete.filters.RecordMultipleFilter` is a django-filter filter that draws a
multiple field in a filter set. It takes the multiple field class and the filter's usual arguments,
and one more.

| Argument | Default | Meaning |
|---|---|---|
| `scope` | `"public"` | As for the fields. A list filter offers public records to everyone. |

The list filters FairDM ships use it: the dataset list's project filter, the sample list's dataset
filter, the measurement list's dataset and sample filters, and the project list's owner and
contributor filters, which offer organizations and people. A filter generated for a registered
type's relation to a project, dataset, sample or measurement is one too. Choosing several records
keeps the rows that point at any of them.

## Scope

| Scope | Offers |
|---|---|
| `"public"` | Public records, to everyone, signed in or not. |
| `"view"` | Public records, and the records the person may view. |
| `"edit"` | Only the records the person may edit. Someone who is not signed in is offered nothing. |

A project is public when its visibility is public. A dataset is public when its visibility is
public and so is its project. A sample or a measurement is public when its dataset is public and
published. A person may view or edit a record when they hold that level on it,
on its project for a dataset, on its dataset or that dataset's project for a sample or a
measurement, or when a portal role gives them the right on every record, as the
Data Curator role does.

## People and organizations

The person and organization fields take `scope` like the others, but a person or
an organization is public information, so they are offered at the `"public"` scope only and a
different scope raises `ValueError`. Neither accepts `depends_on` or `prefer`.

A person is found by name, by an alternative name or by an ORCID iD typed exactly. An organization
is found by name, by an alternative name or by a ROR identifier typed exactly. An identifier typed
exactly lists that person or organization first. A part of an identifier finds nothing.

Results are grouped. People the person searching has worked with come first, then everyone else.
Two people have worked together when both are credited on a record the searcher can open. A
credit on a private record the searcher has no access to does not count. Organizations the
searcher belongs to come first, then the rest. Belonging means an affiliation that is verified and
has not ended, so a pending request does not count.

People come from the portal's real people: superusers and the anonymous placeholder account are
never offered. An email address is not searched and is never part of a result. A request that
names `email` in `f` or `e` is offered nothing, and an `ordering` that names it is ignored.

A person's row shows their picture or initials, their primary affiliation and their ORCID iD, and
marks a person nobody has claimed. An organization's row shows its city and country and no
identifier. A person's result carries `unclaimed`, `true` when nobody has claimed the profile. A
person's `detail` is the name of their primary affiliation, and an organization's is its place.

## One person's records

A field given `owner` offers the records one person is credited on, for a filter on a list of that
person's records, such as the projects on their profile. The records are the ones the person holds at
least the view level on, on the record itself or on a record above it. Their private records are
offered only when the person using the field is that person. Everyone else, including someone who
may view those private records elsewhere, is offered the public ones. The field is served by the
profile address of its kind and sends the owner's key with each search, and it validates what it is
sent by the same rule.

```python
from fairdm.contrib.autocomplete.fields import ProjectMultipleChoiceField


projects = ProjectMultipleChoiceField(owner=person)
```

`owner` is a value of the page being shown, so a filter set creates the field when the page is
built and replaces the one it declares. Giving `owner` together with `scope`, or to a person or
organization field, raises `ValueError`.

## A registered sample or measurement type

A sample or measurement field given `type` offers, and accepts, samples or measurements of that
registered type and no other. The address is told to filter by the type, and the form refuses a
record of another type with `invalid_choice`.

```python
from demo.models import RockSample
from fairdm.contrib.autocomplete.fields import SampleChoiceField

rock_sample = SampleChoiceField(type=RockSample)
```

`type` must be a subclass of the kind's model. A project or dataset field, or a model of another
kind, raises `ValueError` when the field is created.

## Publications

`PublicationChoiceField` chooses one publication from the portal's literature. It takes the
arguments of Django's `ModelChoiceField` except `queryset`, and takes no `scope`: a publication
carries no visibility, so the field accepts any publication that exists. The dataset form's data
publication uses it.

A publication is found by part of its title, by part of an author's name, or by its DOI typed
exactly. A DOI typed as a `doi:` prefix or an address (`https://doi.org/10.1000/abc`) finds the
same publication, and a part of a DOI finds nothing. A publication whose DOI was typed exactly is
listed first, and the rest follow in order of title. Besides `id` and `title`, a result carries
`authors` (the family names, joined with commas), `year` (a number, or `null`), `doi` (empty when
the publication has none) and `html`. The row shows the title, then the authors and year, with
the DOI in an outline badge. The address is `autocomplete:publication`.

## Tags

`TagsField` chooses tags, which are words and not records. The tags are drawn as chips, each with
a button to remove it, and the field cleans to a list of strings with the spaces around each
removed, empty entries dropped and repeats kept once.

| Argument | Default | Meaning |
|---|---|---|
| `scope` | `"view"` | `"view"` offers the tags in use on records the person may view, and `"public"` offers only the tags in use on public records, to everyone. |
| `allow_new` | `False` | With `True` the person may type a tag nobody has used, and the field accepts any tag that is not empty. With `False` it accepts only a tag in use on the records its scope offers. |

The free keywords page uses `TagsField(allow_new=True)`. A tag is offered when it is in use on a
project, a dataset, a sample or a measurement that the record fields of the same scope would
offer, so a tag never reveals a record the person cannot reach. A tag in use on no record is not
offered. The addresses are `autocomplete:tag-view` and `autocomplete:tag-public`, and a result
carries the tag's `id` and `name`.

`fairdm.contrib.autocomplete.filters.TagFilter` draws the field in a filter set, at `public` scope
unless told otherwise and with no way to add a tag. Choosing several tags keeps the rows that
carry any of them. The project list's tag filter is one.

## ROR lookup

`RorChoiceField` looks an organization up in the Research Organization Registry (ROR) by name and
chooses one entry. Its value is the ROR ID, or the ROR address, as the person chose it. The
organization form's lookup uses it. It takes the arguments of Django's `ChoiceField` and nothing
else.

The field accepts any value in the form of a ROR ID or its address, and never asks ROR to check
it, so a form saves while ROR does not answer. A value that is not in that form is refused with
the error code `invalid_choice`. A field that is not required accepts an empty value.

The address is `autocomplete:ror`. It searches ROR for the text typed, shows nothing for an empty
search and cuts the text at 100 characters. A result carries `value` (the ROR address), `label`
(the organization's name), `detail` (its kind and where it is, with the country), and `html`. The
row shows the name, the place and the ROR ID in an outline badge. ROR answers at most ten
organizations for a search, so there is only one page. When ROR does not answer, the address
answers with status 503 and an empty list. The address takes the same limits as the others and the
same request rates.

## Fields that depend on another field

A field with `depends_on` follows the field it names. In the browser, the field searches only the
records of the value chosen in the other field, and clears its own choice when that value changes.
On submit, the field checks the value of the other field in the form's own data, and accepts only
a record that belongs to it. A sample of another dataset is refused with `invalid_choice`. The
value in the page's address plays no part. When the other field has no value, the field is not
narrowed.

```python
from django import forms

from fairdm.contrib.autocomplete.fields import DatasetChoiceField, SampleChoiceField


class XRFMeasurementForm(forms.Form):
    dataset = DatasetChoiceField(scope="edit")
    sample = SampleChoiceField(depends_on="dataset")
```

`depends_on` accepts only a name that the field's address lets a request filter on. Any other
name raises `ValueError` when the field is created.

## Fields that prefer another field's value

A field with `prefer` lists first the records that belong to the value chosen in the field it
names, under a heading of their own such as "Samples in this dataset", and offers every other
record the person may see after them. The measurement form's sample field works this way, because
a measurement may name a sample from another dataset. The preference only orders and groups. The
field accepts the same records whatever the other field holds: a sample of another dataset that
the person may view is accepted, and one the person may not view is refused with
`invalid_choice`. When the other field has no value, the records are listed as usual.

```python
class XRFMeasurementForm(forms.Form):
    dataset = DatasetChoiceField(scope="edit")
    sample = SampleChoiceField(prefer="dataset")
```

`prefer` accepts the same names as `depends_on`, and any other name raises `ValueError` when the
field is created.

## Validation

A field accepts a value only when it would have offered that record to the same person. A record
the person may not reach is refused with the error code `invalid_choice`, whatever the page's own
search parameters say.

A record that already holds a link to a record the person cannot see keeps it. The field shows the
stored link as a private record, without its name, and accepts it when the form is saved
unchanged. It never offers that record in a search.

The person is the user on the form's `request` attribute, or else on the request the form is built
in. A form built outside any request, in a script or a test, accepts what is in the field's
`queryset` and nothing by default.

## Results

Each address answers with a page of results. A result carries these keys.

| Key | Holds |
|---|---|
| `id` | The record's primary key, which the form submits. |
| `name` | The record's name. |
| `private` | `true` when the record is not public. |
| `project` | A dataset's project name, or `null`. Datasets only. |
| `type` | The record's type, such as "rock sample". Samples and measurements only. |
| `local_id` | The creator's own identifier for the record. Samples and measurements only. |
| `dataset` | The name of the record's dataset. Samples and measurements only. |
| `optgroup` | The heading of the group the result is listed under. |
| `html` | The row, drawn on the server. |

Records are grouped as the person's own first, then public records, then any further records a
portal-wide role lets them see. A record appears once, in its first group. Typing a record's UUID
exactly finds it and lists it first. A sample is also found by its local ID and by its
identifiers, and a measurement by its local ID. A local ID or an identifier typed exactly is
listed first.

## Addresses

There is one address for each kind and scope, under the `autocomplete` namespace:
`autocomplete:project-public`, `autocomplete:project-view`, `autocomplete:project-edit`,
`autocomplete:project-profile`, and the same four for `dataset`, `sample` and `measurement`. The
profile address offers the records of the person named by its `owner` parameter. Tags have `autocomplete:tag-public` and
`autocomplete:tag-view`, and publications have `autocomplete:publication`. ROR has `autocomplete:ror`. People and organizations have one address
each, `autocomplete:person-public` and `autocomplete:organization-public`. The scope belongs to
the address, so a request cannot widen it.

## Limits

| Limit | Value |
|---|---|
| Results in a page | 20, whatever `page_size` the request names |
| Last page served | 25 |
| Longest search text | 100 characters, cut when longer |
| Filters a request may name | None for projects, datasets, publications, tags, people, organizations and ROR. `dataset` and `polymorphic_ctype` for samples and measurements. A request naming any other filter is offered nothing. |
| Ordering a request may name | None. An ordering is ignored. |

A search that fails answers with status 500 and an empty list, and nothing else.

## Request rates

Each address limits a caller with four throttles. For what to set, see [Limits on the API](../portal-administration/api-limits.md#limits-on-the-search-fields). A signed-in caller is counted by account and
anyone else by network address. A caller over a limit is answered with status 429, a `Retry-After`
header and an empty list, before anything is searched.

| Scope | Default rate |
|---|---|
| `autocomplete_anon_burst` | 60 per minute |
| `autocomplete_anon_day` | 5000 per day |
| `autocomplete_user_burst` | 240 per minute |
| `autocomplete_user_day` | 50000 per day |

Add a scope to `REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]` to change its rate. A scope left out
uses the default above.

## Classes behind the fields

A field needs none of these to work. They are listed for a portal that builds a field of its own
on the same address and limits.

**Views**, in `fairdm.contrib.autocomplete.views`:

| Class | Serves |
|---|---|
| `LimitedAutocompleteMixin` | The page size, page depth, search length, filter and ordering limits, and the request throttles, for every view below |
| `RecordAutocompleteView` | The base of the record views: scope, the "yours, public, other" grouping and the exact-identifier ordering |
| `ProjectAutocompleteView` | Projects |
| `DatasetAutocompleteView` | Datasets, counted from `Dataset.all_objects` |
| `DatasetRecordsAutocompleteView` | The base of the two views below, for records that sit inside a dataset |
| `SampleAutocompleteView` | Samples |
| `MeasurementAutocompleteView` | Measurements |
| `ContributorAutocompleteView` | The base of the two views below, with the "near first" grouping |
| `PersonAutocompleteView` | People |
| `OrganizationAutocompleteView` | Organizations |
| `PublicationAutocompleteView` | The portal's literature |
| `TagAutocompleteView` | Tags in use on records the requester may see |
| `RorAutocompleteView` | The ROR registry |

`scoped_view(view_class, scope)` returns the subclass of a record view that serves one scope.
django-tomselect rebuilds a view without the arguments given to `as_view()` when it validates a
value, so each scope is its own class:

```python
from django.urls import path

from fairdm.contrib.autocomplete.views import SampleAutocompleteView, scoped_view

urlpatterns = [
    path("samples/edit/", scoped_view(SampleAutocompleteView, "edit").as_view()),
]
```

**Throttles**, in `fairdm.contrib.autocomplete.throttling`: `AutocompleteAnonBurstThrottle`,
`AutocompleteAnonDailyThrottle`, `AutocompleteUserBurstThrottle` and
`AutocompleteUserDailyThrottle`, one per scope in the table under Request rates. Each takes
`DefaultRateMixin`, which falls back to the default rate when a portal's settings leave the scope
out.

**Fields and widgets**, in `fairdm.contrib.autocomplete.fields`:

- `record_fields()` makes the single and the multiple field for one record view, as each pair
  above is made.
- `RecordFieldMixin`, with `RecordChoiceFieldMixin` and `RecordMultipleChoiceFieldMixin`, carries
  the arguments, the validation through the view and the kept stored value.
- `RecordSelectWidget` and `RecordSelectMultipleWidget`, built on `RecordSelectMixin`, write the
  address, the dependency and the count words on the control.
- `TagsWidget` draws the chips of `TagsField`.

## Demo records

The demo's `seed_record_search` command, written as `RecordSearchSeed` in `demo/seed/record_search.py`,
seeds the records these fields are shown with: organizations with ROR identifiers, people with
ORCID identifiers, unclaimed people, private and public projects, datasets and samples,
publications with DOIs, and tags. `--large` adds 100,000 samples.

```console
DJANGO_ENV=development python manage.py seed_record_search
```
