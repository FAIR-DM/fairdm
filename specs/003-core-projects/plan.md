# Implementation Plan — 003 The project record

Branch `003-core-projects`. Eight stories, delivered as one pull request against `main`.

## Approach

The work divides cleanly by surface: two vocabulary repairs, one validation repair, one field
addition, one data-shape change with a migration, one new export module, and a set of small
administrative fixes. Nothing here needs a new abstraction — every piece attaches to machinery the
package already has, and `research.md` records what that machinery is.

Three stories carry migrations. Each is written reversible, and at convergence the ordinary schema
migrations are squashed into a single file per Article IX, which exempts data migrations — so the
funding conversion stays standalone. The suite runs with `--no-migrations`, so none of them is
exercised by a test; that is a reason to keep them small and to read them carefully, not a reason to
leave them scattered.

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

The accepted keys are exactly `funderName`, `funderIdentifier`, `funderIdentifierType`,
`awardNumber`, `awardTitle` and `awardURI`. `funderName` is required within a record; the rest are
optional; any other key is refused. `funderIdentifierType` is drawn from DataCite's set — ISNI, GRID,
Crossref Funder ID, ROR and Other. Each member of the list must be an object, so a list of scalars is
refused with the same message rather than raising.

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
project is created: the portal create view (`fairdm/core/project/views.py:98`) and the project's own
API viewset.

**The API change is an override of `perform_create` on `ProjectViewSet`, and `BaseViewSet` is not
touched.** `BaseViewSet.perform_create` (`fairdm/api/viewsets.py:51`) is inherited by the dataset,
sample and measurement viewsets as well, and none of those models has this field — passing the
keyword there would break every create through those endpoints.

The field is set from the request user and is never exposed as a writable serializer field, a form
field or an editable admin field. Attribution a client can assert is not attribution.

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
  recreates them under the correct key. **Five models bind this vocabulary, not one** — projects
  (`fairdm/core/project/models.py:177`), datasets (`fairdm/core/dataset/models.py:722` and `:534`),
  samples (`fairdm/core/sample/models.py:349`), measurements
  (`fairdm/core/measurement/models.py:206`) and contributors
  (`fairdm/contrib/contributors/models.py:1201`). Stored types are character fields rather than
  foreign keys, so no row is lost; what changes is which concepts resolve and what the admin offers.
  The existing contributor and dataset identifier tests are run after the rename.
- The JSON-LD contributor representation carries an email address wherever one is recorded
  (`fairdm/contrib/contributors/utils/transforms.py`, the person branch). The export drops that key
  rather than changing the shared transform, which other callers rely on.
- `ProjectDateFactory` defaults to `type = "Created"`, which is not a member of the project date
  collection (`fairdm/factories/core.py:121`). Fixing it may surface failures in tests that relied on
  the invalid value.

## Order of work

1. **US-3 identifiers** and **US-2 dates** first — both are defects, both are self-contained, and
   the identifier vocabulary is a prerequisite for the export mapping.
2. **US-7 creation record** and **US-4 funding** next; both carry migrations.
3. **US-1 descriptions, keywords and tags** and **US-6 administration** — mostly tests over existing
   behaviour, plus the two bulk-action fixes.
4. **US-8 the record itself** — the status label repair, the role-to-DataCite mapping and the
   bounded-query proof. The role mapping is a precondition for the export's contributor block.
5. **US-5 export** last, because it consumes every one of the above.
