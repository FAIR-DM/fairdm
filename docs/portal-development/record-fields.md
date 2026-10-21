# Record fields

Record fields are form fields that choose a project or a dataset by searching for it. Each field
sends its searches to an address that FairDM provides and answers with the records the person
using the field may reach. The fields are in `fairdm.contrib.autocomplete.fields`. For the steps
to add one to a form, see [How to add a record field to a form](add-a-record-field.md).

## Fields

| Single field | Multiple field | Chooses |
|---|---|---|
| `ProjectChoiceField` | `ProjectMultipleChoiceField` | a project |
| `DatasetChoiceField` | `DatasetMultipleChoiceField` | a dataset |

## Arguments

Both fields take the arguments of Django's `ModelChoiceField` and `ModelMultipleChoiceField`,
except `queryset`, which the field decides, and one more.

| Argument | Default | Meaning |
|---|---|---|
| `scope` | `"view"` for a single field, `"public"` for a multiple field | What the person must be able to do with a record for the field to offer it. |

## Scope

| Scope | Offers |
|---|---|
| `"public"` | Public records, to everyone, signed in or not. |
| `"view"` | Public records, and the records the person may view. |
| `"edit"` | Only the records the person may edit. Someone who is not signed in is offered nothing. |

A project is public when its visibility is public. A dataset is public when its visibility is
public and so is its project. A person may view or edit a record when they hold that level on it,
on its project for a dataset, or when a portal role gives them the right on every record, as the
Data Curator role does.

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
| `optgroup` | The heading of the group the result is listed under. |
| `html` | The row, drawn on the server. |

Records are grouped as the person's own first, then public records, then any further records a
portal-wide role lets them see. A record appears once, in its first group. Typing a record's UUID
exactly finds it and lists it first.

## Addresses

There is one address for each kind and scope, under the `autocomplete` namespace:
`autocomplete:project-public`, `autocomplete:project-view`, `autocomplete:project-edit`, and the
same three for `dataset`. The scope belongs to the address, so a request cannot widen it.

## Limits

| Limit | Value |
|---|---|
| Results in a page | 20, whatever `page_size` the request names |
| Last page served | 25 |
| Longest search text | 100 characters, cut when longer |
| Filters and ordering a request may name | None. A request naming a filter is offered nothing, and an ordering is ignored. |

A search that fails answers with status 500 and an empty list, and nothing else.

## Request rates

Each address limits a caller with four throttles. A signed-in caller is counted by account and
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
