# Implementation Plan — 003 The project record

Branch `003-core-projects`. Seven stories, delivered as one pull request against `main`.

## Approach

The work divides cleanly by surface: two vocabulary repairs, one validation repair, one field
addition, one data-shape change with a migration, one new export module, and a set of small
administrative fixes. Nothing here needs a new abstraction — every piece attaches to machinery the
package already has, and `research.md` records what that machinery is.

Three of the seven stories carry migrations. They are kept separate and each is reversible, because
the test suite runs with `--no-migrations` and therefore never exercises them.

## Design decisions taken here

### Comparing partial dates

`PartialDate.__ge__` is `self.date >= other.date and self.precision >= other.precision`
(`partial_date/fields.py:122`), which mixes precision into the ordering: a year-only 2020 does not
compare as greater than a day-precision 2019-05-01, because its precision is lower. Comparing the
objects directly is therefore unsafe.

**The check compares at the coarser of the two precisions.** If either date is year-only, compare
years. If either is month-precision, compare year and month. Compare full dates only when both carry
day precision. A project that started in June 2020 and ended some time in 2020 is not an error, and
this rule is what keeps it from being reported as one.

### The shape of funding

Funding becomes a **list** of DataCite funding references, matching what the form's help text has
claimed all along (`fairdm/core/project/forms.py:64`). A single object is not accepted; a project
with one award carries a list of one, because DataCite permits repetition and a list avoids a second
code path.

Validation runs as a field validator so that it fires from `full_clean()` and from the admin without
either needing to know about it.

The existing data shape is the factory's flat `{"agency", "grant_number", "amount"}`
(`fairdm/factories/core.py:147`). The migration maps `agency` to `funderName` and `grant_number` to
`awardNumber`. **`amount` is dropped.** DataCite has no field for it, no portal is known to hold real
funding data, and inventing a non-standard key would defeat the reason for adopting the schema. The
migration is reversible in structure, and the reverse leaves `amount` absent.

### Modifying pre-existing tests

Three tests assert the flat funding shape: `tests/test_factories/test_core.py:234` and `:356`, and
`tests/test_factories/test_contributors.py:289`. They are correct about today's factory and wrong
about the specified shape, so they are rewritten against the new one.

This is a deliberate change to tests that already existed, recorded here because the constitution
requires such a change to be recorded rather than made quietly. No assertion is weakened: each keeps
testing that funding round-trips through the factory, against the schema the specification now
defines.

### Where the creator is written

Nothing in the model layer can see the request user, so `created_by` is set at the two places a
project is created: the portal create view (`fairdm/core/project/views.py:98`) and the API viewset
(`fairdm/api/viewsets.py:72`). Both are one-line additions.

The create view belongs to `013-project-crud-views`. Touching it is unavoidable — a field this
specification owns has to be populated somewhere — and the change is confined to setting the field.
No other behaviour in that file is altered.

### The project identifier vocabulary

A `Project` collection is added to `FairDMIdentifiers` with the identifier types that name a project:
DOI, grant number and proposal identifier. `ProjectIdentifier.VOCABULARY` is scoped to it with
`from_collection("Project")`, matching how descriptions and dates already bind.

`FairDMIdentifiers.Meta.name` is corrected from `"fairdm-descriptions"` to `"fairdm-identifiers"`.
Two vocabularies sharing one registry key collide in the `Concept` table, whose uniqueness is
`("vocabulary", "name")`. This is a prerequisite for the new terms resolving at all, not a tidy-up.

### Export

A new module `fairdm/core/project/export.py` holds two functions, `to_datacite(project)` and
`to_json_ld(project)`, each returning a dictionary. The administrative actions serialise whatever
they return. Keeping the mapping out of the admin is what makes it testable and reusable by the API
later.

Mappings that need stating:

- **Descriptions** — the DataCite description types are a fixed set. `Abstract` maps to `Abstract`;
  every other project description type maps to `Other` and carries its own type in
  `descriptionType`-adjacent free text rather than being lost.
- **Dates** — DataCite has no start/end pair, so each is emitted as its own entry with
  `dateInformation` naming which it is.
- **Identifiers** — a DOI becomes the record's `doi` and primary identifier; everything else becomes
  an alternate identifier.
- **Contributions** — the Creator role maps to `creators`, everything else to `contributors` with a
  `contributorType` drawn from `DataciteContributorRoles` (`fairdm/core/choices.py:89`). Each
  contributor's own representation comes from `Contributor.to_datacite()`, which already exists.
- **JSON-LD** — schema.org `ResearchProject`, with contributors from
  `Contributor.to_schema_org()`. `rdflib` is already available transitively, so the test can parse
  the output rather than merely assert on keys.

Absent optional metadata is omitted. The functions build their dictionaries by adding keys only when
there is something to add, rather than emitting empty lists.

## Complexity tracking

| Addition | Justification |
|---|---|
| `fairdm/core/project/export.py` | Two mapping functions with no home. Putting them in `admin.py` would make them untestable without the admin and unusable by anything else. |
| A funding validator | The specification requires a shape; a shape that is not enforced is documentation. |
| A `Project` collection in `FairDMIdentifiers` | Required by the specification, and the vocabulary has no project terms at all today. |

No new dependency. No new abstraction layer. `rdflib` is used in a test only, and it is already
installed.

## Risks

- The funding migration touches existing data. It is reversible and the suite does not exercise
  migrations, so it is reviewed by reading rather than by running. Keeping it small is the mitigation.
- Correcting `FairDMIdentifiers.Meta.name` changes the registry key that `Concept` rows are stored
  under. Existing rows keyed under the old name become orphaned rather than deleted, and `preload()`
  recreates them under the correct key.
- `ProjectDateFactory` defaults to `type = "Created"`, which is not a member of the project date
  collection (`fairdm/factories/core.py:121`). Fixing it may surface failures in tests that relied on
  the invalid value.

## Order of work

1. **US-3 identifiers** and **US-2 dates** first — both are defects, both are self-contained, and
   the identifier vocabulary is a prerequisite for the export mapping.
2. **US-7 creation record** and **US-4 funding** next; both carry migrations.
3. **US-1 descriptions, keywords and tags** and **US-6 administration** — mostly tests over existing
   behaviour, plus the two bulk-action fixes.
4. **US-5 export** last, because it consumes every one of the above.
