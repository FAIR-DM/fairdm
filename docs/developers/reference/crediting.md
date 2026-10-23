# Crediting

This page lists `Crediting`, the one place the contributors of a project, dataset, sample or measurement change, and the classes around it: the organization choice (`AffiliationChoice`), the two forms for people and organizations typed in by hand (`NewPersonForm`, `NewOrganizationForm`), the ORCID and ROR lookups (`Orcid`, `Ror`) and the pages of the Contributors tab. It does not cover the `Contribution` model, which is in [Contributor models](contributor-models.md), or the levels a credit carries, which are in [Contribution levels and record access](contribution-levels-and-record-access.md). For the task, see [How to credit a person on a record](../how-to/credit-a-person-on-a-record.md).

## The Crediting class

`Crediting(record)` is in `fairdm.contrib.contributors.services.crediting`. `record` is a project, dataset, sample or measurement of any registered type. A sample or measurement held as its base class is changed as its real type, which is where its contributors and their levels are read.

Every method that changes contributors runs in a transaction that first locks the record's row with `select_for_update`, through the model's `all_objects` manager where it has one so that a private record is found. Two changes to one record wait for each other, and each sees what the other left. A database that cannot lock rows, such as SQLite, runs the change in the transaction alone.

Each refusal is a `ValidationError` with a code, so a page can attach it to a field and a test can assert on it. When several refusals apply to one `update`, the error holds them all in its `error_list` and nothing is saved.

| Method | Returns | What it does |
|---|---|---|
| `add(contributor, *, organization=None)` | `Contribution` | Lists the contributor last among its own kind. A person starts at the view level, an organization with no level. `organization` is the organization a person is credited from on this record, which is listed on the record too when it is not already. `None` credits the person from none. Ignored for an organization. Adds no roles |
| `update(contribution, *, roles, level=None, organization=UNCHANGED)` | `None` | Replaces the roles with `roles` (concepts of the roles vocabulary, possibly none). For a person it also sets `level` when one is given and `organization` when it is not `UNCHANGED`. `level` and `organization` are ignored for an organization |
| `remove(contribution)` | `None` | Deletes the credit, and the level goes with it |
| `move(contribution, direction)` | `None` | Moves the credit one place earlier (`"up"`) or later (`"down"`) among the credits of its own kind. Changes nothing for the first moving earlier or the last moving later |
| `make_creator(user, *, roles=())` | `Contribution` or `None` | Lists the person who made the record at the manage level, with the named roles, or raises their existing entry to it. Does nothing and returns `None` for a superuser. The roles are names, and are not checked against the record type's group |
| `offered_roles()` | `list` of concepts | The concepts the record's `CONTRIBUTOR_ROLES` group offers, in the vocabulary's order |
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

A record names its people in one order and its organizations in another. `Crediting.move` is the only code that changes either. It swaps `order` with the neighbour of the same kind on the same record. Credits that share an order value are told apart by their creation order, so a move gives the same result every time. `add` places a contributor last. `update` and `remove` leave the others' order as it is.

`Contribution.objects.for_entity(record).people()` and `.organizations()` read the two lists, each ordered by `order` then `pk`. `RecordOverviewPlugin.get_contributions()` returns the two lists one after the other, people first. `get_credits()` follows that order and gives a person credited with no organization an `affiliation` of `None`.

### The last manager

A record that has someone who counts as able to manage it, as `RecordAccess(record).managers()` reckons, keeps one. `update` and `remove` refuse a change that would take the record from at least one such person to none, whoever asks. A record that has none already may lose or raise anyone. The person's own level and the level they hold from a record above are both read, so lowering a manager who also manages through the dataset is allowed.

## AffiliationChoice

`AffiliationChoice` is a form in `fairdm.contrib.contributors.plugins.shared`. It is the choice of the organization a person is credited from on one record, and the form behind the `c-contribution.affiliation` component.

| Argument | Type | Default | What it does |
|---|---|---|---|
| `person` | `Person` or `None` | `None` | The person, when they are already in the portal. Their affiliations become the options, the current primary one first |
| `credit` | `Contribution` or `None` | `None` | The person's credit on the record, when it is being edited. Its organization is selected |
| `suggested` | `str` | `""` | An organization name to offer, such as an employer from ORCID |

| Field | Accepts |
|---|---|
| `affiliation` | `org:<id>` for one of the person's affiliations, `other` for an organization named in `affiliation_name`, or `none`. An empty value means `none`. Any other value is refused with the code `invalid_choice` |
| `affiliation_name` | The organization's name, up to the length of `Contributor.name`. Required when `affiliation` is `other` |

| Member | Returns | What it does |
|---|---|---|
| `organization()` | `Organization` or `None` | The organization chosen. For `other`, it finds an organization with that name (ignoring case) or creates one. Call it inside the transaction that saves the credit, so that an organization made for a save that is then refused is not kept |
| `choice()` | `dict` | The options, which one is selected, the name typed for another organization, and every organization name for the suggestions. A refused form keeps what was entered |
| `problem` | Property, `str` or `None` | The first error message |
| `held_by(person)` | `list` of `dict` | Static. One `{"value", "organization", "note"}` for each of the person's affiliations |

## NewPersonForm and NewOrganizationForm

Both are forms in `fairdm.contrib.contributors.plugins.shared`. They are behind the by-hand tab of the add pages. `save()` makes the contributor and does nothing else, so a page can make it, make the organization chosen and write the credit in one transaction.

`NewPersonForm`:

| Field | Type | Accepts |
|---|---|---|
| `given` | `CharField` | The given name, up to the length of `Person.first_name`. Required |
| `family` | `CharField` | The family name, up to the length of `Person.last_name`. Required |
| `confirmed` | `BooleanField` | Whether the user has seen the profiles that share the name. Optional |

A posted `email` is ignored. `save()` returns an active, unclaimed `Person` with an unusable password and no account. `same_name` lists up to five people whose name matches, and the form is not valid while it is not empty unless `confirmed` is sent. The error has the code `same_name`.

`NewOrganizationForm`:

| Field | Type | Accepts |
|---|---|---|
| `name` | `CharField` | The name. Required |
| `city` | `CharField` | A city. Optional |
| `country` | `CharField` | A country name or a code from the country field's list. Anything else is refused with the code `invalid_country`. Optional |
| `website` | `URLField` | A web address. A missing scheme is read as `https`. It is stored in the organization's `links`. Optional |

The form is never valid while `same_name` holds an organization with the same name (ignoring case). The error has the code `same_name`.

## Orcid and Ror

`Orcid` and `Ror` are in `fairdm.contrib.contributors.services.registries`. They are two plain classes with no shared base, and the add pages search them. Each has the same four methods.

| Method | Returns | What it does |
|---|---|---|
| `search(term)` | `{"results": [...], "more": bool}` | Searches by name, or by identifier when `term` has the form of one or is the address of one. Returns at most `RESULTS_SHOWN` (10) records and whether the registry holds more. ORCID records of people with no public name and ROR records of organizations that are not active are left out |
| `fetch(identifier)` | record or `None` | Fetches one record. `None` when the identifier is malformed (no request is made), the registry has no such record, or the record cannot be chosen |
| `known(record)` | `Person`, `Organization` or `None` | The contributor the portal already holds under the record's identifier. A ROR identifier stored as an address is found too |
| `profile(record)` | `Person` or `Organization` | The contributor that `known` finds, or a new one with the name and the identifier and nothing else. A new person has no email, an unusable password and no account. A profile is never matched by name |

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
| `ask(address, parse, *, params=None, headers=None, missing_ok=False)` | Function | The one function that makes a request. `parse` turns the decoded answer into what the caller wants. Both classes use it, and a third registry can pass its own address and `parse` |
| `RESULTS_SHOWN` | `10` | The most matches a search returns |
| `TIMEOUT` | `5` | The seconds a registry has to answer |
| `KEPT` | `300` | The seconds an answer is kept in the default cache, by address, parameters and active language. An answer of "no such record" is kept. A failure is not |

Search terms go in the request's parameters and never into the address. No identifier reaches an address unless it matches `ORCID_PATTERN` or `ROR_PATTERN`, both in `fairdm.contrib.contributors.models`. Saving the identifier queues the sync that every `ContributorIdentifier` queues, so a worker fills in the rest of the profile later.

## Level choices

`level_choices(record, floor=None)` is in `fairdm.contrib.contributors.plugins.shared`. It returns the three levels as the edit page draws them, as a list of `{"value", "label", "hint", "disabled"}`. The hint names the record's kind. A level below `floor`, the level the person holds from above, is `disabled`.

## The Contributors tab

`ContributionList` in `fairdm.contrib.contributors.plugins.shared` is the plugin behind the **Contributors** tab. It is registered on `Project`, `Dataset`, `Sample` and `Measurement`, with the label "Contributors", the icon `users` and order 150. Registered sample and measurement types inherit it, and their roles, levels and addresses are read from the core model they extend.

The pages share the base class `ContributionPage`, which works out the record, its kind and whether the viewer may manage it. A page opens only when the record's overview would. A page that changes anything answers 403 to a signed-in person who cannot manage the record and sends a visitor to sign in.

| Class | `url_path` | Method | What it does |
|---|---|---|---|
| `ContributionList` | `contributors` | GET | Lists the people and the organizations, each in their own order |
| `ContributionAddPerson` | `add-person` | GET, POST | Adds a person from the portal, from ORCID or by hand |
| `ContributionAddOrganization` | `add-organization` | GET, POST | Adds an organization from the portal, from ROR or by hand |
| `ContributionEdit` | `<int:pk>/edit` | GET, POST | Sets a contributor's roles and, for a person, the level and the organization |
| `ContributionRemove` | `<int:pk>/remove` | GET, POST | Confirms, then removes a contributor |
| `ContributionMove` | `<int:pk>/move` | POST | Moves a contributor one place. A `direction` of `up` or `down` is required, and anything else answers 400 |

`ContributionAddPerson` and `ContributionAddOrganization` share the base `ContributionAdd`:

| Attribute | Type | Default | What it does |
|---|---|---|---|
| `is_person` | `bool` | `True` | Whether the page adds a person |
| `registry_class` | `Orcid` or `Ror` | `Orcid` (`Ror` on the organization page) | The registry behind the second tab |
| `form_class` | form | `NewPersonForm` (`NewOrganizationForm` on the organization page) | The form behind the by-hand tab |
| `results_shown` | `int` | `20` | The most matches the portal search lists |

The page offers three tabs, `portal`, `registry` and `new`, and `via` in the address or the form names the one to open. The portal search reads `q` and the registry search reads `rq`. The context's `adding` carries `registry_results`, `registry_more` and `registry_unavailable`. A registry that cannot be reached leaves the other two tabs working, and the page answers 200. Choosing a registry record only fetches it. Adding posts the identifier, and the page fetches the record again before it makes a profile.

A refused add or edit answers 422 and draws the page again with what was entered.

Addresses resolve with the plugin `reverse`:

```python
from fairdm.contrib.plugins import reverse

reverse(dataset, "contribution-list")
reverse(dataset, "contribution-list-contribution-add-person")
reverse(dataset, "contribution-list-contribution-edit", pk=contribution.pk)
reverse(sample, "contribution-list-contribution-remove", pk=contribution.pk)
```

See [Plugins](plugins.md) for the plugin registration arguments.
