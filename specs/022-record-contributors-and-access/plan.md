# Implementation Plan: Contributors and access are managed on every core record

**Branch**: `022-record-contributors-and-access` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md)

## Summary

A working prototype of every screen is on this branch and was approved. Its templates, components
and wording stay. Everything behind them is rebuilt with tests.

A person's rights on a record become one stored level on their contribution. One permission
backend answers every question about a project, dataset, sample or measurement from those levels,
reading up through the dataset and the project. One class is the only place a record's
contributors change, and it holds the two refusals: the last manager, and an organization people
are credited from. The pages of the tab are thin over it. A second small module searches ORCID
and ROR.

## Technical context

**Language/version**: Python 3.13, Django 5.2
**Primary dependencies**: django-mvp 0.26, django-cotton, django-guardian, django-polymorphic,
django-ordered-model, `requests`, htmx and Alpine as shipped by django-mvp. No new dependency
**Storage**: one new field on `Contribution`, one changed foreign-key rule, one data migration
**Testing**: pytest, pytest-django, factory-boy, per `docs/contributing/standards/testing.md`.
Tests mirror the source tree and request the real pages through the test client. Registry calls
are replaced at `requests.get`; no test reaches the network
**Target**: the `fairdm` package and the `demo` reference application
**Constraints**: every string translatable (Article VIII). The right to change contributors is
checked on every request (FR-033). Layout, width, stacking and copy get no tests. The approved
templates are not redesigned: a template changes only where the code behind it changes its
context, and the page it draws stays the same

## Constitution check

| Article | How the plan meets it |
|---|---|
| I Testing | Each story starts with tests of its acceptance scenarios, through the test client for pages and directly for the access rules, for every kind of account the story names |
| II Simplicity / III Anti-Abstraction | One field, one backend, one class that answers access questions about a record, one that changes its contributors, one per registry. No level model, no per-permission table, no base class and no registry of implementations |
| IV Integration-First | Acceptance tests open and submit the real pages. The backend is tested through `user.has_perm`, the way every caller asks |
| V Security | One decision point for every core record (D2). Every changing request re-checks the right to manage. Registry input is fetched again by identifier on the server before a profile is made, never taken from the form. Outbound requests go to two fixed hosts with a timeout |
| VI / XVI Documentation | Each story documents the public names it introduces, in the story that introduces them |
| VII Dependencies | None added |
| VIII i18n | All labels, help text and messages are translatable |
| IX Data-model conventions | The new field has `verbose_name`, `help_text` and choices. The migration is reversible for the schema and one-way for the data, and says so |
| X Cohesion | Functions that share a subject sit on a class: `RecordAccess` for the questions about one record, `Crediting` for the changes to one record's contributors, `Orcid` and `Ror` for the two registries. Querying records by level is a queryset method. Pages stay in `plugins/shared.py` |
| XVII Demo | `seed_contributors` reaches every state the seven stories name, with the three standard sign-ins |

## Complexity tracking

| Addition | Why it is needed | Simpler alternative, and why not |
|---|---|---|
| `Contribution.level` | The tab shows and sets one level per person per record (FR-034) | Keep inferring it from guardian rows, as the prototype did: several rows per person per record, no way to store a level for someone guardian has no rows for, and a list costs a query per row |
| `RecordLevelBackend` | FR-051 wants one decision for every page | Teach each of the three existing record backends about levels and projects: three copies of the same walk, and a fourth for projects |
| `services/crediting.py` | Two refusals and a lock have to hold whichever page asks | Put them in the views: the organization rule is needed by add, edit and remove alike |
| `services/registries.py` | Two outbound searches with the same failure handling | Call `requests` from the view: the unavailable case (FR-015) would be written twice |

## Design

### D1. The level is stored on the contribution

`Contribution.level`: a nullable small integer with choices `VIEW = 1`, `EDIT = 2`, `MANAGE = 3`
(`ContributionLevel` in `choices.py`). It is empty for an organization. Integers so that "at
least" is a comparison.

### D2. One place decides: `fairdm/contrib/contributors/access.py`

Rebuilt from the prototype's module of the same name. The questions about one record sit on one
class, `RecordAccess(record)`:

- `above`: the dataset of a sample or measurement, then that dataset's project; the project of a
  dataset; nothing for a project. A measurement follows its own dataset.
- `level_of(user)`: the highest level the user holds on the record or any record above, or `None`.
  Refuses a visitor and an inactive user. One query for the chain.
- `own_level(person)` and `level_from_above(person)`: the two halves, with the source record, for
  the tab.
- `levels_for(people)`: the same for a list of people in a fixed number of queries.
- `people_above()`: everyone holding a level from a record above.
- `managers()`: ids of people who can sign in and hold manage on the record or above.
- `can_manage(user)`: `level_of(user) == MANAGE`, or the user holds `change_<model>` for the whole
  portal.

Beside it, `REQUIRED_LEVEL` maps a permission codename to a level, as in `research.md`, and
`required_level(perm, record)` returns the level or `None` for a permission the table does not
know. A registered sample or measurement type's own default permissions (`view_`, `add_`,
`change_` and `delete_` followed by the subtype's model name, under the subtype's app label) are
read as the core model's, because the API and the plugin helpers build permission names from the
record's own class.

"Can sign in" is one method on `Person`, with the rule specification 020 settled: active, and
claimed or has signed in. `Person.is_editable_by` uses it.

`RecordLevelBackend` in `permissions.py`, added to `AUTHENTICATION_BACKENDS`: for a project,
dataset, sample or measurement (including registered subtypes) it answers
`RecordAccess(obj).level_of(user) >= required_level(perm, obj)`, and `False` for an unknown
permission. For anything else it answers `False` and leaves the question to the other backends.

Stored guardian rows stop applying to core records: `PolymorphicObjectPermissionBackend.has_perm`
returns `False` for a core record, the way it already does for `manage_organization`.
`SamplePermissionBackend` and `MeasurementPermissionBackend` then have nothing left to do and are
removed from the settings and deleted. `PortalRolePermissionBackend` is unchanged.

**Querying by level.** One queryset method on each core model's queryset, `with_level(user,
level)`, returns the records the user holds at least that level on, on the record itself or from a
record above. `CoreRecordQuerySet.visible_to(user)` becomes the released records plus
`with_level(user, VIEW)`, so a person listed only on a sample sees that sample and not its
siblings (FR-046).

Several places read or write guardian rows on core records without going through a backend. Each
reader moves to `with_level`, and each writer moves to `Crediting` or is deleted:

| Place | Today | Becomes |
|---|---|---|
| `fairdm/api/filters.py:79` | lists records by stored rows | `with_level(user, VIEW)` |
| `fairdm/core/sample/forms.py:71`, `fairdm/core/measurement/forms.py:65` | offers datasets with a stored `change_dataset` row | `with_level(user, EDIT)` |
| `fairdm/core/measurement/filters.py:149`, `fairdm/core/dataset/filters.py:77`, `fairdm/core/dataset/plugins.py:704`, `demo/models.py:124` | stored rows | `with_level` at the level each asks for |
| `fairdm/api/serializers.py:28` and `:71` | grants the API creator three rows | `Crediting(record).make_creator(user)` |
| `fairdm/contrib/contributors/receivers.py:19` | removes rows when a credit is deleted | deleted; the level goes with the contribution |
| `demo/seed/common.py:95`, `demo/seed/projects.py:285`, `:337`, `:398` | seeds rows | seeds levels through `Crediting` |

`fairdm/utils/permissions.py` keeps its two helpers for records that are not core records.
Docstrings that describe the old behaviour are corrected in the task that changes it.

### D3. One place changes contributors: `services/crediting.py`

`Crediting(record)`. Every changing method runs in a transaction that first locks the record's
row (`select_for_update`), so two changes to one record cannot interleave (FR-055).

- `add(contributor, *, organization=None)`: refuses a duplicate. Places the contributor last. A
  person gets the view level unless they already hold a contribution level, and is credited from
  `organization`, which is listed on the record if it is not already. No organization means none:
  the model hook that fills a new contribution's affiliation from the person's primary
  affiliation (`Contribution.set_default_affiliation`) is deleted, and the default lives only as
  the initial value of the choice on the page (FR-024).
- `update(contribution, *, roles, level=None, organization=None)`: roles must come from the record
  type's group. A level below what the person holds from above is refused. Lowering the last
  manager is refused.
- `remove(contribution)`: refuses the last manager, and refuses an organization that anyone on the
  record is credited from.
- `move(contribution, direction)`: swaps `order` with the neighbour of the same kind.
- `credited_from()`: organization id to the people credited from it there.
- `make_creator(user)`: adds the user at the manage level. Called by the project and dataset
  create pages and by the API's create serializers, in place of their guardian grants.

Refusals are `ValidationError`s with codes (`duplicate`, `role_not_offered`, `below_inherited`,
`last_manager`, `credited_from`), so pages attach them to fields and tests assert on codes.

### D4. The registries: `services/registries.py`

Two plain classes with no shared base, `Orcid` and `Ror`, each with `search(term)`,
`fetch(identifier)` and `profile(record)`. `search` and `fetch` return plain dictionaries with the
keys the approved templates already read (`id`, `shown_id`, `name`, `detail`, and for a person
`given`, `family`, `employer`). A term that is an ORCID iD or a ROR ID searches by identifier.
Results are limited, and a flag says when more exist. Records with no public name and withdrawn
organizations are left out.

`fetch` refuses an identifier that does not match the registry's format before any request is
made, reusing the ORCID pattern in `models.py` and the ROR cleaner in `utils/transforms.py`. Search
terms are passed through `requests`' `params`, never formatted into the address. Both classes use
the versioned ROR and ORCID addresses. Any network error, timeout or non-200 answer raises
`RegistryUnavailable`. The timeout is five seconds.

`profile(record)` returns the existing contributor with that identifier, or makes one with the
name and the identifier.

### D5. The pages: `plugins/shared.py`

The five pages keep their addresses, templates and context names. Each becomes a form over the
service:

- `ContributionForm` (edit): roles, and for a person the affiliation choice and the level.
- `AffiliationChoice`: the field group behind `c-contribution.affiliation`, shared by the edit
  form and the three ways of adding a person.
- `NewPersonForm`, `NewOrganizationForm`: the typed fields, with the same-name check. An email
  address the portal already holds is refused on the field without naming or offering the profile
  it belongs to.

Every page that changes anything asks `can_manage` on every request and sends a visitor to sign
in. The list page, and every page of the tab, opens only when the record's overview would: the
tab reuses the overview's own check for its record type, so a private record's tab answers as a
record that does not exist (FR-049).

**The existing update forms.** Visibility, and the record a record sits under (the project of a
dataset, the dataset of a sample or measurement, the owner of a project), decide who can get in.
On the update forms of the four record types those fields are offered only to someone for whom
`can_manage` is true, and are left out of the form otherwise, so an editor's request cannot change
them (FR-037). A Data Curator keeps them through `can_manage`.

### D6. Order

`ContributionQuerySet.people()` and `.organizations()` narrow by kind and order by `order`.
`RecordOverviewPlugin.get_contributions()` returns people first, then organizations, each in
order, which is what every overview and citation already reads (FR-058). `people_url` is set there
for all four record types (FR-008).

### D7. The upgrade

Three steps in `contributors`, written in the stories that need them and squashed into one
migration before the pull request is ready: add `level` (story 1); change `affiliation` to
`SET_NULL` (story 2); the data step described in `research.md` (story 4, together with the backend
that stops reading guardian rows, so no commit leaves a creator locked out of their own record).
The data step reads user-level and group-level rows, under the four core content types and under
every registered subtype's, and writes each contribution under the record's own content type. It
has no reverse beyond leaving the levels in place.

### D8. Moving a record

`Dataset.clean`, `Sample.clean` and `Measurement.clean` refuse a change of parent that would leave
`managers(record)` empty when it was not empty before (FR-056), with code `no_manager`.

### D9. Merging

`_reassign_contributions` passes the higher level to the kept contribution before dropping a
duplicate. The kept entry's organization is left as it is, including when it is none. A
contribution that is not a duplicate moves with its level. The service has no path that merges
organizations, so the specification's edge case about merged organizations has nothing to act on. `_transfer_permissions` is left for
non-core records.

### D10. Shared display components

`c-contributor.item` and `c-contributor.card.person` stop falling back to the person's primary
organization when they are given a contribution. Given a person, they behave as before.

## What is not rebuilt

The templates under `contributors/plugins/` and `cotton/contribution/`, the seed command, and the
wording. A story edits a template only to follow a context name it had to change, and says so in
`progress.md`. The prototype's fixed registry records and its pause are deleted in the story that
builds the registry module.

## Watch items

- No page creates a sample or a measurement, so FR-052 is delivered for projects and datasets and
  as a callable for the other two. The pull request says so.
- Existing tests that assert guardian grants on core records (project and dataset creation, the
  sample and measurement backends, `visible_to`) describe behaviour this feature replaces. Each is
  changed in the task that changes the behaviour, and named in `progress.md`.
- The shared dev server runs this worktree. The schema step lands in story 1, `SET_NULL` in story
  2 and the data step in story 4.
- A superuser cannot be saved as a contributor outside debug mode (`Contribution.save`). `Crediting`
  refuses one with a `ValidationError` the add page can show, and `make_creator` skips the credit
  for a superuser without failing the create.
- Before this feature a person holding only `change_dataset` could delete that dataset's samples.
  Deleting now needs manage. The changelog says so.
