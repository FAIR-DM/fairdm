# Crediting

This page lists `Crediting`, the one place the contributors of a project, dataset, sample or measurement change, and the classes around it: the ORCID and ROR lookups (`Orcid`, `Ror`), the level choices and the views of the Contributors tab. It does not cover the `Contribution` model, which is in [Contributor models](contributor-models.md), or the levels a credit carries, which are in [Contribution levels and record access](contribution-levels-and-record-access.md). For the task, see [How to credit a person on a record](../how-to/credit-a-person-on-a-record.md).

## The Crediting class

`Crediting(record)` is in `fairdm.contrib.contributors.services.crediting`. `record` is a project, dataset, sample or measurement of any registered type. A sample or measurement held as its base class is changed as its real type, which is where its contributors and their levels are read.

Every method that changes contributors runs in a transaction that first locks the record's row with `select_for_update`, through the model's `all_objects` manager where it has one so that a private record is found. Two changes to one record wait for each other, and each sees what the other left. A database that cannot lock rows, such as SQLite, runs the change in the transaction alone.

Each refusal is a `ValidationError` with a code, so a page can attach it to a field and a test can assert on it. When several refusals apply to one `update`, the error holds them all in its `error_list` and nothing is saved.

| Method | Returns | What it does |
|---|---|---|
| `add(contributor, *, organization=None)` | `Contribution` | Lists the contributor last among its own kind. A person starts at the view level, an organization with no level. `organization` is the organization a person is credited from on this record, which is listed on the record too when it is not already. `None` credits the person from none. Ignored for an organization. Adds no roles |
| `update(contribution, *, roles, level=None, organization=UNCHANGED)` | `None` | Replaces the roles with `roles` (concepts of the contributor roles vocabulary, possibly none). For a person it also sets `level` when one is given and `organization` when it is not `UNCHANGED`. `level` and `organization` are ignored for an organization |
| `remove(contribution)` | `None` | Deletes the credit, and the level goes with it |
| `move(contribution, direction)` | `None` | Moves the credit one place earlier (`"up"`) or later (`"down"`) among the credits of its own kind. Changes nothing for the first moving earlier or the last moving later. The Contributors tab orders people with `mvp.ordering.save_order` instead, so a whole order is saved at once |
| `make_creator(user, *, roles=())` | `Contribution` or `None` | Lists the person who made the record at the manage level, with the named roles, or raises their existing entry to it. Does nothing and returns `None` for a superuser. The roles are names, and are not checked against the record type's group |
| `offered_roles()` | `list` of concepts | The concepts of the collection the record's `CONTRIBUTOR_ROLES` names, in the collection's order |
| `credited_from()` | `dict` | Organization id to the list of people credited from it on this record, in their order |
| `list_organization(organization)` | `None` | Lists an organization on the record, unless it already is |
| `would_leave_no_manager(contribution, level=None)` | `bool` | Whether removing the credit (`level=None`) or lowering it to `level` leaves a record that has someone who can manage it with nobody. Changes nothing |
| `last_manager_refusal(contribution)` | `ValidationError` | The refusal with code `last_manager`. Its `params` hold `name` and `kind` |
| `locked()` | Context manager | Locks the record's row for the length of a change. A method you add to `Crediting` that changes contributors uses it too |

`UNCHANGED` is a sentinel in the same module. Passed as `organization` to `update`, it leaves the organization as it is. An organization sets it and `None` sets it to none.

### Refusal codes

| Method | Raises when | Code |
|---|---|---|
| `add` | The contributor is already listed | `duplicate` |
| `add` | The contributor is a superuser | `superuser` |
| `add` | The contributor is the placeholder account that stands for every visitor | `anonymous` |
| `update` | A role is not in the group the record's type offers | `role_not_offered` |
| `update` | `level` is below what the person holds from a record above | `below_inherited` |
| `update` | The change would leave the record with nobody who counts as able to manage it | `last_manager` |
| `remove` | The credit is an organization that people on the record are credited from | `credited_from` |
| `remove` | The credit is the only thing that makes the record manageable | `last_manager` |
| `move` | `direction` is neither `"up"` nor `"down"` | `direction` |
| `move` | The credit is not listed on this record | `not_listed` |

The `credited_from` refusal carries the people in `params["people"]`, so a page can name them.

### Order

A record names its people in one order and its organizations in another. `Crediting.move` and the tab's reorder sheet change the people's order, and the sheet saves it in one write. It swaps `order` with the neighbour of the same kind on the same record. Credits that share an order value are told apart by their creation order, so a move gives the same result every time. `add` places a contributor last. `update` and `remove` leave the others' order as it is.

`Contribution.objects.for_entity(record).people()` and `.organizations()` read the two lists, each ordered by `order` then `pk`. `RecordOverviewPlugin.get_contributions()` returns the two lists one after the other, people first. `get_credits()` follows that order and gives a person credited with no organization an `affiliation` of `None`.

### The last manager

A record that has someone who counts as able to manage it, as `RecordAccess(record).managers()` reckons, keeps one. `update` and `remove` refuse a change that would take the record from at least one such person to none, whoever asks. A record that has none already may lose or raise anyone. The person's own level and the level they hold from a record above are both read, so lowering a manager who also manages through the dataset is allowed.

## Orcid and Ror

`Orcid` and `Ror` are in `fairdm.contrib.contributors.services.registries`. They are two plain classes with no shared base, and the Contributors tab searches them. Each has the same four methods, and each has more.

| Method | Returns | What it does |
|---|---|---|
| `search(term)` | `{"results": [...], "more": bool}` | Searches by name, or by identifier when `term` has the form of one or is the address of one. Returns at most `RESULTS_SHOWN` (10) records and whether the registry holds more. `Orcid().search(term, affiliation="")` also takes the name of an affiliation to narrow by. A name is searched as a phrase over the given and family names first, then by each word with the last as a prefix ORCID records of people with no public name and ROR records of organizations that are not active are left out |
| `fetch(identifier)` | record or `None` | Fetches one record. `None` when the identifier is malformed (no request is made), the registry has no such record, or the record cannot be chosen |
| `known(record)` | `Person`, `Organization` or `None` | The contributor the portal already holds under the record's identifier. A ROR identifier stored as an address is found too |
| `profile(record)` | `Person` or `Organization` | The contributor that `known` finds, or a new one with the name and the identifier and nothing else. A new person has no email, an unusable password and no account. A profile is never matched by name |

`Orcid().affiliations(orcid_id)` returns every organization on a person's public ORCID record, ended ones included, each once and the current ones first, as `{"name", "ror", "current"}`. An empty list means ORCID has none listed or could not be asked. `Ror().resolve(source, value)` finds the ROR ID of an organization another registry names: `source` is `"FUNDREF"`, `"GRID"` or `"RINGGOLD"`. It returns the bare ROR ID or `None`. ROR indexes Funder Registry and GRID IDs, and has no Ringgold field, so a Ringgold ID resolves only when the organization's record happens to carry it.

A record is a plain dictionary:

| Key | `Orcid` | `Ror` |
|---|---|---|
| `id` | The ORCID iD | The ROR address, `https://ror.org/...` |
| `shown_id` | The ORCID iD | The address without its scheme |
| `name` | Given and family names | ROR's display name |
| `detail` | The employer and where it is, or a note that none is listed | The kind of organization and where it is |
| `given`, `family`, `employer` | The two names and the first current employer (or `""`) | Not present |

The module also holds:

| Name | Type | What it is |
|---|---|---|
| `RegistryUnavailable` | Exception | Raised for a network error, a timeout, an answer that is not a 200 (a 404 on `fetch` is an answer) and an answer in a form the registry does not document |
| `ask(address, parse, *, params=None, headers=None, missing_ok=False)` | Function | The one function the searches and lookups make a request through. `parse` turns the decoded answer into what the caller wants. Both classes use it, and a third registry can pass its own address and `parse` |
| `fetch_record(address, headers=None)` | Function | The one function the sync and the transforms' `fetch_from_api()` fetch a record to store through. Uncached. Returns the decoded record, or `None` for a 404. Raises `RegistryRateLimited` for a 429, `requests.RequestException` for any other failure and `ValueError` for an answer that is not JSON. It never retries: the sync task does |
| `RegistryRateLimited` | Exception, a `requests.RequestException` | Raised by `fetch_record` for a 429. `retry_after` holds the seconds the registry asked to wait, or `None` |
| `seconds_to_wait(retry_after)` | Function | Reads a `Retry-After` value, seconds or an HTTP date, into whole seconds. `None` when the value says nothing |
| `RESULTS_SHOWN` | `10` | The most matches a search returns |
| `TIMEOUT` | `5` | The seconds a registry has to answer a search or lookup |
| `FETCH_TIMEOUT` | `10` | The seconds a registry has to answer `fetch_record` |
| `SEARCHES_PER_MINUTE` | `60` | The most registry searches one person may make in a minute |
| `SearchLimitReached` | Exception, a `RegistryUnavailable` | Raised by `count_search(user)` past the limit. The count is kept in the default cache |
| `KEPT` | `300` | The seconds an answer is kept in the default cache, by address, parameters and active language. An answer of "no such record" is kept. A failure is not |

Search terms go in the request's parameters and never into the address. No identifier reaches an address unless it matches `ORCID_PATTERN` or `ROR_PATTERN`, both in `fairdm.contrib.contributors.models`. Saving the identifier queues the sync that every `ContributorIdentifier` queues, so a worker fills in the rest of the profile later.

## Level choices

`level_choices(record, floor=None)` is in `fairdm.contrib.contributors.plugins.shared`. It returns the three levels as the edit page draws them, as a list of `{"value", "label", "hint", "disabled"}`. The hint names the record's kind. A level below `floor`, the level the person holds from above, is `disabled`.

## The Contributors tab

`ContributionList` in `fairdm.contrib.contributors.plugins.tab` is the plugin behind the **Contributors** tab. It is registered on `Project`, `Dataset`, `Sample` and `Measurement`, with the label "Contributors", the icon `users` and order 150. Registered sample and measurement types inherit it, and their roles, levels and addresses are read from the core model they extend.

The tab is one page, `contributors/tab/page.html`, whose body is the Cotton component `c-contributor.tab.region`. Every change answers with that region drawn again, and the sheets that collect a change are drawn into the page by htmx. The views share the base class `ContributorsBase` in `plugins/tab_base.py`, which extends `ContributionPage` and so opens only when the record's overview would. The views that change anything answer 403 to a signed-in person who cannot manage the record and send a visitor to sign in.

| Class | Extra view `name` | Method | What it does |
|---|---|---|---|
| `ContributionList` | none | GET | The two lists, and for a manager the people who hold access from a record above |
| `AddPerson` | `add-person` | GET | The sheet's search of the portal's people |
| `AddPersonStep` | `add-person-step` | GET, POST | The later steps: who they are, their affiliation, their roles. A POST adds the person |
| `AddOrganization` | `add-organization` | GET, POST | The organization sheet and its steps. A POST lists the organization |
| `EditCredit` | `edit` | GET, POST | Sets a contributor's roles and, for a person, the affiliation and the level |
| `CreditOrganization` | `credit-organization` | GET, POST | Gives an organization that is only someone's affiliation roles of its own |
| `RemoveCredit` | `remove` | POST | Removes a contributor and answers with an Undo |
| `UndoRemove` | `undo` | POST | Puts a removed contributor back from the signed token in `undo`, valid for five minutes |
| `Reorder` | `reorder` | GET, POST | Saves the order of the people |

Addresses resolve with the plugin `reverse`, and an extra view's name is prefixed with the plugin's:

```python
from fairdm.contrib.plugins import reverse

reverse(dataset, "contribution-list")
reverse(dataset, "contribution-list-add-person")
reverse(dataset, "contribution-list-edit", pk=contribution.pk)
reverse(sample, "contribution-list-remove", pk=contribution.pk)
```

Everyone added to a record that offers the role holds Project Member, ticked and locked in the roles field, and someone who holds it keeps it on edit. A registry search counts against `SEARCHES_PER_MINUTE`, and a registry that cannot be reached, or a person who has searched too often, is told so in the step and nothing is added.

### Helpers

The views lean on a few functions, which a project that builds its own step on the tab can call too.

| Function | Module | Returns |
|---|---|---|
| `role_by_slug(slug)` | `plugins.tab_base` | The contributor role with that slug, or `None` |
| `first_name_of(person, new_name=None)` | `plugins.tab_base` | The first of a person's given names, or their family name when they have none |
| `initials_of(record, organization=False)` | `plugins.tab_base` | The initials an avatar shows for a registry record |
| `affiliation_choices(person)` | `plugins.tab_base` | `(theirs, others)`: the organizations on the person's profile as `(organization, current)` pairs, then every other organization |
| `split_name(typed)` | `plugins.tab_people` | `{"first_name", "last_name"}` from a name typed whole: the last word is the family name |
| `portal_organization(entry)` | `plugins.tab_people` | The portal's organization for one picked from ORCID or ROR, made only when no ROR ID or name matches |

See [Plugins](plugins.md) for the plugin registration arguments.
