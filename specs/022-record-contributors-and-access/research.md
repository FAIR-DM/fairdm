# Research: Contributors and access are managed on every core record

Investigated against `main` at `5998b914` on 2026-10-06, after the prototype was approved. Each
finding ends with what the plan does about it.

## What the screens need, and how each is met

The numbers follow `sketch.md`, "What the screens need from the code".

| # | Need | Finding | Decision |
|---|---|---|---|
| 1 | A level per person per record, read for a whole list | Rights are rows in django-guardian, one per permission per person per record. Reading a level means collecting several rows and inferring it | A `level` field on `Contribution`. One row already exists per contributor per record, and the list already loads it |
| 2 | The level held from records above, and from which | `SamplePermissionBackend` and `MeasurementPermissionBackend` each hard-code a map from their own permissions to the dataset's. Nothing reaches a project | One function walks record, dataset, project and returns the highest level and its source. One backend uses it for every core record |
| 3 | Who counts as able to manage, checked safely | Nothing exists | `managers(record)` in the same module. Changes run in a transaction that locks the record's row first |
| 4 | Whether a person can sign in | `Person.account_state` misreports accounts made by `createsuperuser` or unverified sign-up, as specification 020 found. 020 settled on "active, and claimed or has signed in" | Reuse 020's rule through one method on `Person` |
| 5, 6 | Two orders, and moving within one | `Contribution` is an `OrderedModel` with a single `order` column across every record. Its `up()` and `down()` would swap with a row on another record | Keep the one column. Order is only ever compared within one record and one kind, so a move swaps the `order` values of two neighbours of the same kind on the same record |
| 7 | Searching a record's contributors, and the portal's people and organizations | Plain name matching is enough at the sizes involved. `Contributor.objects` is polymorphic and can be narrowed by kind | `icontains` on `name`, limited, with a count of what was left out |
| 8 | Roles per record type, in vocabulary order | `CONTRIBUTOR_ROLES` on each core model already holds them in order | Used as is |
| 9 | A link from each overview's People card | `people_url` is set by the project overview only | Set in `RecordOverviewPlugin` for all four |
| 10 | The tab on every registered type | Registering a plugin on `Sample` and `Measurement` already reaches every subtype | As the prototype does |
| 11 | Searching ORCID and ROR | `tasks.py` and `utils/transforms.py` already call `pub.orcid.org/v3.0/<id>` and `api.ror.org/organizations/<id>` with `requests`. Both registries have public search endpoints that need no credentials: ORCID `v3.0/expanded-search` returns given and family names, the iD and institution names; ROR `v2/organizations?query=` returns names, types, locations and status | A small module with two search functions and two fetch-by-identifier functions over `requests`, with a short timeout. No new dependency |
| 12 | Profiles from registry records, without duplicates | `ContributorIdentifier` stores ORCID and ROR values against a contributor | Look the identifier up first. Make the profile and its identifier together when it is absent |
| 13 | Profiles from typed fields | `Person` can be saved with no email and an unusable password, which is how unclaimed profiles already exist. `Organization` has `name`, `city`, `country` and links | Two plain forms |
| 14 | The organization on a credit, never read from the profile | `Contribution.affiliation` already exists as a foreign key to `Organization`. The shared display components fall back to the person's primary organization when it is empty | Use the field. The fallback is removed for credits in `c-contributor.item` and `c-contributor.card.person`, which are given a contribution in exactly the places a record names its people |
| 15 | A person's affiliations with dates | `Affiliation` has `is_primary`, `start_date`, `end_date` | Used as is |
| 16, 17 | Who is credited from each organization, and refusing removal | Derivable from `Contribution.affiliation` | One query per record, in the module that changes contributions |
| 18 | A small organization card | The prototype's `c-contribution.organization` | Kept |

## What the prototype faked, and what replaces it

- **Levels read from guardian rows.** Replaced by the field and the backend above. Guardian rows on
  core records are converted by a data migration and are no longer consulted for those records.
- **Nothing enforced who may open a record.** Projects and datasets already ask
  `has_perm("…view_…", record)` for a private record, and samples and measurements ask
  `visible_to(user)`. The backend makes the first true for level holders. `visible_to` is rewritten
  to ask for the datasets a user holds a level on, directly or through the project. The Contributors
  tab gets the same check its record's overview has.
- **Rights from above shown only.** The backend applies them.
- **No guard against two changes at once.** A row lock on the record inside the transaction.
- **Creator not made a manager.** The project and dataset create pages give the creator the manage
  level in place of five guardian rows. The portal has no page that creates a sample or a
  measurement, so nothing can trigger it for them yet. The service is written so the page that
  will create them calls one function.
- **Fixed ORCID and ROR records.** Replaced by the registry module. The pause that made the
  searching state visible goes with them.
- **Names only.** Registry profiles keep their identifier. Typed profiles keep the optional fields.
- **Affiliation dropped from the edit page.** Restored by the choice the prototype settled on.
- **One stored order.** Stays, read as two.

## Other things the plan needs settled

### Which permission means which level

Every permission the four core models declare is mapped, so none is left unchecked (FR-043).

| Level | Permissions on the record |
|---|---|
| view | `view_<model>` |
| edit | `change_<model>`, `add_<model>`, `import_data`, `modify_metadata`, `change_<model>_metadata` |
| manage | `delete_<model>`, `add_contributor`, `modify_contributor`, `change_<model>_settings`, `can_publish` |

A permission on a core record that is not in the table is refused, so a new one cannot be added
without deciding its level. `can_publish` sits with manage until the feature that builds publishing
says otherwise.

### Who may manage contributors

A person at the manage level, or a person who holds `change_<model>` for the whole portal. The
second is how the Data Curator role reaches the tab without the role's permissions changing
(FR-060, FR-062), and it is what a superuser passes.

### The upgrade

Guardian's user-level rows on the four core models are read once. For each person and record the
highest level any of their rows maps to is written to their contribution, which is made when they
have none. The rows are then deleted. Existing contributions of people with no rows get the view
level. Group-level rows are left alone and stop applying to core records, which is recorded in the
changelog and the administrator guide. `Contribution.affiliation` changes from `PROTECT` to
`SET_NULL`, so deleting an organization leaves the person credited with none. Each organization a
person is already credited from gets an entry on that record.

### Moving a record

A dataset's `project`, and a sample's or measurement's `dataset`, can change on their forms. The
check that the record keeps a manager afterwards belongs with the models' validation, where every
form reaches it.

### Merging

`services/merge.py` moves a discarded person's contributions to the kept one and skips duplicates,
and copies guardian rows. With levels on the contribution, a skipped duplicate has to pass on its
level when it is higher. Organizations are merged by the same service's organization path, if one
exists at build time. If none does, the edge case in the specification has nothing to act on.

### Packages considered

None is added. `django-guardian` stays for organizations and for anything a portal defines.
`django-ordered-model` stays as the base class. `requests` is already a dependency. A typeahead
widget was not needed: the prototype's suggestion list is a native `datalist`.
