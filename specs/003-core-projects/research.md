# Research — 003 The project record

What the surrounding machinery already provides, and what it constrains. Every claim here was read
out of the repository on 2026-08-18 and carries its citation.

## Controlled vocabularies

Vocabularies are `VocabularyBuilder` subclasses in `fairdm/core/vocabularies.py`, backed by
`django-research-vocabs`. A term is a class attribute — either a `Concept(prefLabel=…)` or a raw
dict with fully qualified SKOS keys — and its URI is derived from `Meta.namespace` plus the attribute
name rather than being written out. `Meta.name` is the registry key that `Concept` rows are stored
under.

A model binds to a vocabulary by setting `VOCABULARY`, and `GenericModel.__init_subclass__` pushes
`VOCABULARY.choices` onto the `type` field at class construction
(`fairdm/core/abstract.py:247`). The stored value is the attribute name — `"Abstract"`, `"Start"`,
`"ORCID"` — not a URI. `from_collection("Project")` returns a subclass scoped to one collection
(`research_vocabs/core.py:389`).

Two facts shape the identifier work:

- `FairDMIdentifiers` has no `Project` collection. Its two collections are `Person` and
  `Organization`, and its terms are ORCID, ResearcherID, ROR, Wikidata, ISNI and Crossref Funder ID
  (`fairdm/core/vocabularies.py:6`). There is no DOI term anywhere in it.
- `ProjectIdentifier` binds the whole unscoped vocabulary — `VOCABULARY = FairDMIdentifiers()`
  (`fairdm/core/project/models.py:177`) — where descriptions and dates both scope themselves with
  `from_collection("Project")`. That inconsistency is why the wrong terms are offered.

`FairDMIdentifiers.Meta.name` is `"fairdm-descriptions"` (`fairdm/core/vocabularies.py:65`), the same
registry key `FairDMDescriptions` uses (`:208`). Two vocabularies sharing one key is a collision in
the `Concept` table, whose uniqueness is `("vocabulary", "name")`
(`research_vocabs/models.py:126`).

## The related-record abstracts

All three inherit `GenericModel` (`fairdm/core/abstract.py:220`), which is a plain Django model with
`added` and `modified` explicitly removed.

| Abstract | Fields | Constraint |
|---|---|---|
| `AbstractDescription` (`:278`) | `type` char(50), `value` text | unique `(related, type)` |
| `AbstractDate` (`:295`) | `type` char(50), `value` `PartialDateField` | unique `(related, type)` |
| `AbstractIdentifier` (`:313`) | `type` char(50), `value` char(255) **globally unique** | unique `(related, type)` |

The decisive fact for the date work: **`AbstractDate` carries `type` and `value` and nothing else.**
There is no `end_date` and no `date`. So a project's start and end are two separate rows, and any
comparison between them is across records rather than within one. `ProjectDate.clean()` compares
`self.date` to `self.end_date` (`fairdm/core/project/models.py:168`), which is why it raises an
attribute error.

`value` is a `PartialDateField` (`fairdm/db/fields.py`), so a date may carry year-only, year-month or
full precision. Any comparison has to tolerate that.

An identifier's value is already unique across every row of a concrete subclass
(`fairdm/core/abstract.py:315`), so nothing is needed for the uniqueness requirement beyond a test.

## Contributions

`Contribution` (`fairdm/contrib/contributors/models.py:1068`) is a generic-foreign-key join with
`roles` as a `ConceptManyToManyField` onto the shared role vocabulary. `Project.contributors` is a
`GenericRelation` to it, so iterating it yields contributions rather than contributors, and a
contribution's roles are read with `contribution.roles.all()`.

`BaseModel.add_contributor()` (`fairdm/core/abstract.py:80`) creates the contribution and sets roles
by name. The project create view already calls it with Creator, ProjectMember and ContactPerson
(`fairdm/core/project/views.py:110`).

A DataCite transform for contributors already exists — `Contributor.to_datacite()`
(`fairdm/contrib/contributors/models.py:335`) emitting `name`, `nameType` and `nameIdentifiers` — and
so does a schema.org one, `Contributor.to_schema_org()` (`:349`). Export reuses both rather than
re-deriving them.

`DataciteContributorRoles` already exists in `fairdm/core/choices.py:89`, which is what makes the
role vocabulary expressible in DataCite's terms without a new table.

## Funding

The field is an unvalidated `JSONField` (`fairdm/core/project/models.py:86`). Two different shapes
are in play and neither is enforced:

- The factory writes a flat dict — `{"agency": …, "grant_number": …, "amount": …}`
  (`fairdm/factories/core.py:147`).
- The form's help text and placeholder describe a list of DataCite funding references
  (`fairdm/core/project/forms.py:64`).

Three tests assert the flat shape (`tests/test_factories/test_core.py:234`, `:356`;
`tests/test_factories/test_contributors.py:289`). Changing the shape means changing those tests,
which is a deliberate modification of pre-existing tests and is recorded as such in the plan.

DataCite's funding reference carries `funderName` (required), `funderIdentifier`,
`funderIdentifierType`, `awardNumber` and `awardTitle`. It has no field for an amount, so the
factory's `amount` has no destination.

## Export

What exists are two administrative actions using nothing but `json.dumps`. `export_json` emits six
scalar fields (`fairdm/core/project/admin.py:129`); `export_datacite` emits a title, a publication
year and a resource type (`:154`). Neither touches a related record, and neither has a test.

Elsewhere in the package there is a DataCite **XML** path, but it is dataset-scoped and template-driven
(`fairdm/contrib/import_export/utils.py:38`, rendering `publishing/datacite44.xml`). There is JSON-LD,
but only for contributors (`fairdm/contrib/contributors/utils/transforms.py:218`). No DataCite library
is in the dependency set, and none is needed — the output is a dictionary.

`rdflib` is present transitively through `django-research-vocabs`, so JSON-LD can be validated in a
test without adding a dependency.

## The user model and the creation record

`AUTH_USER_MODEL` is `contributors.Person` (`fairdm/conf/settings/auth.py:19`), a polymorphic,
email-keyed subclass of `AbstractUser`.

No model in the package records who created it. The nearest established pattern for a nullable
person reference is `ClaimingAuditLog.initiated_by` — `SET_NULL`, `null=True`, `blank=True`
(`fairdm/contrib/contributors/models.py:1290`). Core models use `fairdm.db.models.ForeignKey`, which
re-exports `auto_prefetch.ForeignKey` (`fairdm/db/models.py:3`).

Nothing in the model layer can observe the request user, so the creator has to be written where a
project is created. There are two such places: the portal create view
(`fairdm/core/project/views.py:98`) and the API viewset (`fairdm/api/viewsets.py:72`).

## Querysets

`ProjectQuerySet.with_metadata()` already selects the owner and prefetches descriptions, dates,
identifiers, contributors and keywords (`fairdm/core/project/models.py:35`). The requirement for a
bounded query count is therefore about proving it, not building it.

`with_list_data()` (`:49`) has no callers anywhere in the package or the tests.

## Tooling and conventions

- Python 3.13, Django 5.1–5.2, Poetry, the shared family dev bundle pinned at `v0.2.0`.
- pytest with `--no-migrations`, so **migrations are never exercised by the suite**. A migration's
  correctness has to be reasoned about rather than tested, which argues for keeping data migrations
  simple and reversible.
- Ruff at the default line length, with `E501` ignored; mypy with the Django plugin over `fairdm/`,
  excluding `fairdm/contrib/*`.
- No coverage floor is configured in `pyproject.toml`.
- Factories live in the package at `fairdm/factories/`, not under `tests/`. There is no identifier
  factory for projects, and `ProjectDateFactory` defaults to `type = "Created"`
  (`fairdm/factories/core.py:121`), which is not a member of the project date collection.
- Tests use `@pytest.mark.django_db` on the class, `Test<Subject>` class names, plain `assert`, and
  docstrings citing the requirement they cover.
- `tests/conftest.py` preloads vocabulary concepts once per session
  (`tests/conftest.py:12`), which is what makes role and type lookups resolve in tests.

## Open questions carried into the plan

1. How `PartialDateField` values compare when their precisions differ. The comparison in the date
   check has to be defined at the coarser of the two precisions, or a year-only end date will appear
   to precede a full-precision start in the same year.
2. Whether the funding migration should preserve the factory's `amount`. DataCite has nowhere to put
   it, and no real portal data is known to exist.
