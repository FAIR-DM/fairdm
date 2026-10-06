# Implementation Plan: Contributors and access are managed on every core record

**Branch**: `022-record-contributors-and-access` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md)

## Summary

A working prototype of every screen is on this branch and was approved. Its templates, components
and wording stay. Everything behind them is rebuilt with tests.

A person's rights on a record become one stored level on their contribution. One permission
backend answers every question about a project, dataset, sample or measurement from those levels,
reading up through the dataset and the project. One service module is the only place a record's
contributors change, and it holds the two refusals: the last manager, and an organization people
are credited from. The pages of the tab are thin over that module. A second small module searches
ORCID and ROR.

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
| II Simplicity / III Anti-Abstraction | One field, one backend, one service module, one registry module. No level model, no per-permission table, no registry client class hierarchy |
| IV Integration-First | Acceptance tests open and submit the real pages. The backend is tested through `user.has_perm`, the way every caller asks |
| V Security | One decision point for every core record (D2). Every changing request re-checks the right to manage. Registry input is fetched again by identifier on the server before a profile is made, never taken from the form. Outbound requests go to two fixed hosts with a timeout |
| VI / XVI Documentation | Each story documents the public names it introduces, in the story that introduces them |
| VII Dependencies | None added |
| VIII i18n | All labels, help text and messages are translatable |
| IX Data-model conventions | The new field has `verbose_name`, `help_text` and choices. The migration is reversible for the schema and one-way for the data, and says so |
| X Cohesion | The rules on levels live in `access.py`, changes to contributors in `services/crediting.py`, registry calls in `services/registries.py`, pages in `plugins/shared.py` |
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

Rebuilt from the prototype's module of the same name, keeping the names the templates' context
relies on.

- `records_above(record)`: the dataset of a sample or measurement, then that dataset's project;
  the project of a dataset; nothing for a project. A measurement follows its own dataset.
- `level_of(user, record)`: the highest level the user holds on the record or any record above,
  or `None`. Refuses a visitor and an inactive user. One query for the chain.
- `own_level(person, record)` and `level_from_above(person, record)`: the two halves, with the
  source record, for the tab.
- `levels_for(record, people)`: the same for a list of people in a fixed number of queries, for
  the tab's list.
- `people_above(record)`: everyone holding a level from a record above.
- `managers(record)`: ids of people who can sign in and hold manage on the record or above.
- `REQUIRED_LEVEL`: permission codename to level, as in `research.md`. `required_level(perm,
  record)` returns the level or `None` for a permission the table does not know.
- `can_manage(user, record)`: `level_of(...) == MANAGE`, or the user holds `change_<model>` for
  the whole portal.

`RecordLevelBackend` in `permissions.py`, added to `AUTHENTICATION_BACKENDS`: for a project,
dataset, sample or measurement (including registered subtypes) it answers
`level_of(user, obj) >= required_level(perm, obj)`, and `False` for an unknown permission. For
anything else it answers `False` and leaves the question to the other backends.

Stored guardian rows stop applying to core records: `PolymorphicObjectPermissionBackend.has_perm`
returns `False` for a core record, the way it already does for `manage_organization`.
`SamplePermissionBackend` and `MeasurementPermissionBackend` then have nothing left to do and are
removed from the settings and deleted. `PortalRolePermissionBackend` is unchanged.

`CoreRecordQuerySet.visible_to(user)` in `core/managers.py` is rewritten to the datasets the user
holds a level on, directly or through the project, in place of the guardian lookup.

### D3. One place changes contributors: `services/crediting.py`

Every function takes the record and runs in a transaction that first locks the record's row
(`select_for_update`), so two changes to one record cannot interleave (FR-055).

- `add(record, contributor, *, organization=None)`: refuses a duplicate. Places the contributor
  last. A person gets the view level unless they already hold a contribution level, and is
  credited from `organization`, which is listed on the record if it is not already.
- `update(contribution, *, roles, level=None, organization=None)`: roles must come from the record
  type's group. A level below what the person holds from above is refused. Lowering the last
  manager is refused.
- `remove(contribution)`: refuses the last manager, and refuses an organization that anyone on the
  record is credited from.
- `move(contribution, direction)`: swaps `order` with the neighbour of the same kind.
- `credited_from(record)`: organization id to the people credited from it there.
- `make_creator(record, user)`: adds the user at the manage level. Called by the project and
  dataset create pages in place of their guardian grants.

Refusals are `ValidationError`s with codes (`duplicate`, `role_not_offered`, `below_inherited`,
`last_manager`, `credited_from`), so pages attach them to fields and tests assert on codes.

### D4. The registries: `services/registries.py`

`search_orcid(term)`, `search_ror(term)`, `fetch_orcid(orcid_id)`, `fetch_ror(ror_id)`. Each
returns plain dictionaries with the keys the approved templates already read (`id`, `shown_id`,
`name`, `detail`, and for a person `given`, `family`, `employer`). A term that is an ORCID iD or a
ROR ID searches by identifier. Results are limited, and a flag says when more exist. Records with
no public name and withdrawn organizations are left out. Any network error, timeout or non-200
answer raises `RegistryUnavailable`. The timeout is five seconds.

`profile_from_orcid(record)` and `profile_from_ror(record)` return the existing contributor with
that identifier, or make one with the name and the identifier.

### D5. The pages: `plugins/shared.py`

The five pages keep their addresses, templates and context names. Each becomes a form over the
service:

- `ContributionForm` (edit): roles, and for a person the affiliation choice and the level.
- `AffiliationChoice`: the field group behind `c-contribution.affiliation`, shared by the edit
  form and the three ways of adding a person.
- `NewPersonForm`, `NewOrganizationForm`: the typed fields, with the same-name check.

Every page that changes anything asks `can_manage` on every request and sends a visitor to sign
in. The list page, and every page of the tab, opens only when the record's overview would: the
tab reuses the overview's own check for its record type, so a private record's tab answers as a
record that does not exist (FR-049).

### D6. Order

`ContributionQuerySet.people()` and `.organizations()` narrow by kind and order by `order`.
`RecordOverviewPlugin.get_contributions()` returns people first, then organizations, each in
order, which is what every overview and citation already reads (FR-058). `people_url` is set there
for all four record types (FR-008).

### D7. The upgrade

One migration in `contributors`: add `level`; change `affiliation` to `SET_NULL`; then a data step
as described in `research.md`. The data step has no reverse beyond leaving the levels in place.

### D8. Moving a record

`Dataset.clean`, `Sample.clean` and `Measurement.clean` refuse a change of parent that would leave
`managers(record)` empty when it was not empty before (FR-056), with code `no_manager`.

### D9. Merging

`_reassign_contributions` passes the higher level, and the organization when the kept entry has
none, to the kept contribution before dropping a duplicate. `_transfer_permissions` is left for
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
- The shared dev server runs this worktree. The migration lands in the first story.
