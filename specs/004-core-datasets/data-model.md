# Data model — 004 The dataset record

**Regenerated 2026-08-18**, against `spec.md`, `decisions.md`, `plan.md` and `research.md`.

The January version of this file survived the specification rewrite untouched and described a design
this document no longer holds: a `PROTECT` project relation, a three-level visibility, `with_private()`
as the recommended route to private datasets, and an identifier set containing ARK, Handle, URL and
URN. None of that is carried here. It is replaced rather than corrected, because a document that
disagrees with the specification in four places probably disagrees in a fifth.

**This describes the shape the work builds to, not the shape the code has today.** Where the two
differ the difference is named, because the difference is the work. Line citations are to the code as
it stands.

## Dataset

`fairdm/core/dataset/models.py`. Extends `BaseModel` (`fairdm/core/abstract.py:22`), which extends
`fairdm.db.models.Model` — a lifecycle-aware, prefetch-aware base carrying the two timestamps.

### Fields

| Field | Type | Constraints | Origin |
|---|---|---|---|
| `added` | `DateTimeField` | `auto_now_add` | `fairdm.db.models.Model` |
| `modified` | `DateTimeField` | `auto_now` | `fairdm.db.models.Model` |
| `name` | `CharField(300)` | required | `BaseModel` |
| `image` | `ThumbnailerImageField` | optional | `BaseModel` |
| `keywords` | `ManyToManyField` → `research_vocabs.Concept` | optional | `BaseModel` |
| `tags` | `TaggableManager` through `generic.TaggedItem` | optional | `BaseModel` |
| `options` | `JSONField` | optional | `BaseModel` |
| `uuid` | `ShortUUIDField` | `unique`, `editable=False`, prefix `d` | `Dataset` |
| `visibility` | `IntegerField` | `choices=Visibility`, default `PRIVATE`, **newly indexed** | `Dataset` |
| `project` | `ForeignKey` → `project.Project` | `on_delete=CASCADE`, optional | `Dataset` |
| `reference` | `OneToOneField` → `literature.LiteratureItem` | `on_delete=SET_NULL`, optional | `Dataset` |
| `related_literature` | `ManyToManyField` → `literature.LiteratureItem` | through `DatasetLiteratureRelation` | `Dataset` |
| `license` | `LicenseField` | optional, no column default | `Dataset` |
| `contributors` | `GenericRelation` → `contributors.Contribution` | — | `Dataset` |
| `created_by` | `ForeignKey` → `contributors.Person` | `on_delete=SET_NULL`, optional, `editable=False` | **new** |

`keywords` and `tags` are two mechanisms and stay distinguishable: a keyword is a reference to a term
in a configured vocabulary, a tag is free text (FR-005).

`created_by` is copied field-for-field from `Project.created_by`
(`fairdm/core/project/models.py:113`), including the reasoning recorded beside it. It is a foreign
key rather than a name, so it carries a database index without a separate decision, and it is not
editable — the creator is written server-side, never through a form or a serialiser field. `SET_NULL`
is what makes FR-021 hold: removing the account leaves the dataset with an unknown creator rather
than deleting the dataset.

`image` exists here, but its aspect ratio, dimensions, thumbnails and upload guidance belong to
`015-image-field-spec`.

### Class attributes

| Attribute | Value | Change |
|---|---|---|
| `CONTRIBUTOR_ROLES` | `FairDMRoles.from_collection("Dataset")` | unchanged |
| `DATE_TYPES` | `FairDMDates.from_collection("Dataset")` | unchanged |
| `DESCRIPTION_TYPES` | `FairDMDescriptions.from_collection("Dataset")` | unchanged |
| `IDENTIFIER_TYPES` | `FairDMIdentifiers.from_collection("Dataset")` | **was** `FairDMIdentifiers().choices` (D-003) |
| `VISIBILITY_CHOICES` | `Visibility` | unchanged |
| `DEFAULT_ROLES` | `["ProjectMember"]` | unchanged |
| `ROLE_PERMISSIONS` | — | **removed** (D-010) |

`IDENTIFIER_TYPES` and `DatasetIdentifier.VOCABULARY` are two statements of the same thing and must
name the same collection (T054). Today they are both the unscoped vocabulary, which is the defect
D-003 records.

`ROLE_PERMISSIONS` names `Viewer` and `Manager`, neither of which is a member of the dataset role
collection, and nothing reads it. It goes, and the question it was reaching for is issue #169.

### Meta

- `verbose_name` / `verbose_name_plural` — "dataset" / "datasets"
- `default_related_name` — `datasets`
- `ordering` — `["-modified"]`. **Was `["modified"]`** (D-013): ascending put the stalest record
  first, and `Project` was corrected the same way in `003-core-projects`.
- `permissions` — `add_contributor`, `modify_contributor`, `modify_metadata`
  (`fairdm/core/utils.py:10`), plus `import_data`, `change_dataset_metadata` and
  `change_dataset_settings`.

FR-020 binds this list: any permission a visibility check consults must appear in it. The
`dataset.view_private` that `for_user()` gates on does not, which is why `for_user()` can never
return anything but the public set, and why it is removed rather than repaired.

### Managers

Three parts, which is what Django's guidance for a filtered default manager asks for (R1):

| Manager | Shape | Purpose |
|---|---|---|
| `objects` | `DatasetManager()`, excluding `visibility=PRIVATE` | the ordinary route; declared first, so it is `_default_manager` |
| `all_objects` | `DatasetQuerySet.as_manager()` | the explicit, named route to every dataset |

`DatasetManager` already exists and already excludes private datasets (`models.py:331-371`). It is
commented out at `:548-550`. Switching it on is the whole of US-8's privacy work.

Two consequences follow from `_default_manager` changing, and both are handled rather than
discovered:

- `ModelAdmin.get_queryset()` reads `_default_manager`, so the administrative list would stop showing
  private datasets. `DatasetAdmin.get_queryset()` is overridden to use `all_objects`, with the reason
  stated in the code (T067). The administrative interface is where a portal is repaired, and an
  unfinished dataset is exactly what needs reaching.
- A reverse many-to-one manager is built from `related_model._default_manager.__class__`, so
  `project.datasets.all()` stops returning private datasets. That is correct for portal surfaces. The
  deletion guard in `fairdm/core/project/models.py:280` counts public datasets, so it is unaffected.

**`Meta.base_manager_name` is not declared, and cannot be.** `fairdm.db.models.PrefetchBase` assigns
`_meta.base_manager_name = "prefetch_manager"` after the class is built
(`fairdm/db/models.py:30-55`), so a value declared in `Meta` is silently overwritten — and
`django-auto-prefetch` raises a system check if it is anything else. The guarantee FR-019a asks for
holds anyway: `prefetch_manager` is a plain unfiltered manager, so forward relations and the deletion
collector see every dataset regardless of visibility. Verified against `Dataset._meta` directly, not
inferred. This is the correction to R1's third part, recorded in D-019.

### Removed from the queryset

| Method | Because |
|---|---|
| `with_private()` | Rebuilds from the model and discards `self`, so `Dataset.objects.filter(project=p).with_private()` returns every dataset in the table (`models.py:239-241`) |
| `get_visible()` | With two visibility levels it selects the same rows as the default manager — a second name for the default |
| `for_user()` | No callers, and gates on `dataset.view_private`, a permission no model declares (`models.py:195`) |

There is no correct implementation of `with_private()`, only correct entry points. Once the exclusion
lives in the manager it is in the SQL by the time a caller holds a queryset, and no method can take
it back out. FR-019 is written to forbid the shape rather than to require the method: a widening that
silently discards the caller's conditions is worse than no widening at all.

What the queryset keeps is the bounded load — a dataset together with its descriptions, dates,
identifiers, contributions and keywords in a number of queries that does not grow with how many of
each it carries (FR-030).

### Properties

- `has_data` — whether the dataset holds any samples or measurements. A single bounded query rather
  than the two `exists()` calls it is today (T023, FR-008).
- `bbox` — the geographic bounding box, from `fairdm.contrib.location`.

## The related records

`DatasetDescription`, `DatasetDate` and `DatasetIdentifier` share one shape, inherited from
`fairdm/core/abstract.py`. Each carries exactly three fields and **exposes each of them under one
name only** (FR-014).

| Field | Type | Notes |
|---|---|---|
| `related` | `ForeignKey` → `Dataset`, `on_delete=CASCADE` | declared on each concrete model |
| `type` | `CharField(50)` | choices assigned from `VOCABULARY` by `GenericModel.__init_subclass__` |
| `value` | varies — see below | the content |

Each carries a `UniqueConstraint(fields=["related", "type"], name="%(class)s_unique_type")` from its
abstract base, so **one row per type is enforced at the database**: `AbstractDescription`
(`abstract.py:287`), `AbstractDate` (`:305`), `AbstractIdentifier` (`:324`).

The same limit is required in validation as well (FR-009, SC-002), so a researcher gets a message
naming the type rather than a database error. That half is built in `clean()` and is not yet proven
by any test — see the reconciliation note in `tasks.md`.

**The six property aliases are removed** (D-012, R5). `description_type`, `description`, `date_type`,
`date`, `identifier_type` and `identifier` are second names for `type` and `value`, documented as
"API compatibility" for an API that exposes none of these records
(`fairdm/api/viewsets.py:128`). No other core model has them, nothing outside the dataset app reads
them, and one of them is the direct cause of `DatasetFilter.date_type` raising `FieldError` on every
application — `field_name="dates__date_type"` is an ORM path through a Python property. The filter is
routed out as #186. The aliases go here.

### DatasetDescription

`value` is a `TextField`. Vocabulary: `FairDMDescriptions.from_collection("Dataset")` — **Abstract,
Methods, SeriesInformation, TechnicalInfo, Other** (`fairdm/core/vocabularies.py:267`). Indexed on
`type` as `dataset_desc_type_idx`.

`Methods` is the member worth naming: `003-core-projects` established that a methods description
belongs to the dataset rather than the project, and the project collection has it commented out.

### DatasetDate

`value` is a `PartialDateField`, so a date may carry year, month or day precision. Vocabulary:
`FairDMDates.from_collection("Dataset")` — **Available, CollectionStart, CollectionEnd, Submitted,
Published, Withdrawn** (`vocabularies.py:431`). Ordered by `value`. Indexed on `type` as
`dataset_date_type_idx`.

`Created` is **not** a member, and never was. `DatasetDateFactory` defaults to it
(`fairdm/factories/core.py:275`) and four tests use it as an example of a valid type. They pass
because `objects.create()` does not call `full_clean()` and Django does not validate `choices` on
save. The factory and the tests are corrected (D-008).

The collection period is checked in `clean()`, comparing against the sibling row rather than within
one instance, because the two dates are two rows. It follows `ProjectDate.clean()` with
`_sibling_value()` and `_precedes()` (`fairdm/core/project/models.py:196-250`), including comparison
at the coarser of the two precisions — years only if either is year-precision, the full date only
when both carry day precision. The helpers are duplicated rather than lifted: this is the second use
of the pattern, not of a shared implementation (R2).

`START_TYPE = "CollectionStart"`, `END_TYPE = "CollectionEnd"`.

The administrative inline needs the same check across the formset's forms, because a formset
validates every row before saving any of them and a sibling lookup in the database misses a row being
added in the same submission. `ProjectAdmin.DateInlineFormSet` is the pattern
(`fairdm/core/project/admin.py:24-67`).

### DatasetIdentifier

`value` is a `CharField(255)` with `unique=True` and `db_index=True` on the abstract, so **an
identifier value is unique across every record that carries identifiers**, not merely within one
dataset (FR-013). That global uniqueness predates this work and is kept.

Vocabulary: `FairDMIdentifiers.from_collection("Dataset")`, a collection this work adds. It contains
**DOI alone** (D-003, R3).

Today the model binds `FairDMIdentifiers()` unscoped (`models.py:722`), which offers ORCID,
ResearcherID, ROR, Wikidata, ISNI and the Crossref Funder ID — identifiers for people and
organisations — alongside the DOI, grant number and proposal identifier that `003-core-projects`
added for projects. So a dataset is offered mostly types for things a dataset is not, and the three
plausible ones were added for a different record.

Neither ARK nor Handle is added, though the model docstring names them. Nothing in the repository or
the roadmap asks for either, and an unused member is a wrong choice offered to every user. A second
scheme is a three-line addition when one is asked for.

`DOI`'s definition reads "a persistent, resolvable link to a project record"
(`vocabularies.py:68`) — written for projects, now shared, so it is generalised (T002).

The trap this closes: `GenericModel.__init_subclass__` assigns `cls.type.field.choices` from the
`VOCABULARY` (`abstract.py:247`), and Django does not validate `choices` on save. A row written
through `objects.create()` with any string persists silently. Tests for the vocabularies therefore
**assert their members by name**. A test that iterates `VOCABULARY.choices` proves nothing, because
it passes over an empty collection (SC-004).

## DatasetLiteratureRelation

The intermediate model behind `Dataset.related_literature` (`models.py:61-98`). Built, and this work
gives it its first test that runs.

| Field | Type | Constraints |
|---|---|---|
| `dataset` | `ForeignKey` → `Dataset` | `on_delete=CASCADE`, related name `literature_relations` |
| `literature_item` | `ForeignKey` → `literature.LiteratureItem` | `on_delete=CASCADE`, related name `dataset_relations` |
| `relationship_type` | `CharField(50)` | `choices=DATACITE_RELATIONSHIP_TYPES` |

`unique_together` on all three, so the same item may be related under two types but not twice under
one (FR-016). `relationship_type` carries its own index.

All eleven of its tests are skipped behind four class-level marks reading "Literature app not yet
complete", and they reference a `LiteratureItemFactory` that exists nowhere in the repository —
removing the skips would raise `NameError` rather than run them. The literature package is a live
dependency and `LiteratureItem` exists, so the stated reason no longer holds. The missing factory is
part of the work (T006, D-016).

`reference` is the separate one-to-one naming a dataset's own data publication. It is `SET_NULL`, so
deleting that publication leaves the dataset intact with no publication named (FR-015).

## Contributions

A dataset's contributors are `contributors.Contribution` rows reached through a `GenericRelation`.
Each associates a person or an organisation with the dataset under one or more roles drawn from
`FairDMRoles.from_collection("Dataset")` — Creator, ContactPerson, DataCollector, DataCurator,
DataManager, Editor, Producer, RelatedPerson, Researcher, ProjectLeader, ProjectManager,
ProjectMember, Supervisor, WorkPackageLeader, RightsHolder, Other (`vocabularies.py:664`).

The contribution model itself is not changed by this work. Which roles confer which rights is issue
#169, not this specification.

## Licences

`Dataset.license` is the only licence field in the package. It carries **no column default**, and
that is deliberate (D-007): the field points at a `License` row, so a default would resolve a
database lookup at import time and fail wherever the licence rows have not been loaded.

The default is a guarantee about creation instead — a dataset created without choosing a licence
carries the portal's configured `FAIRDM_DEFAULT_LICENSE`, falling back to CC BY 4.0 (FR-007).

For that to resolve at all, a portal needs licence rows. `django-content-license` ships a fixture and
no data migration, so a portal that has migrated and never run `loaddata` by hand has an empty
`License` table — the configured default silently resolves to `None`, and the portal's dataset form
declares `license` as a required field over an empty queryset. The recommended set — **CC0 1.0,
CC BY 4.0, CC BY-SA 4.0** — is seeded by an idempotent management command keyed on `License.name`,
registered `always_run` in the deployment pipeline at `fairdm/conf/settings/apps.py:254-282`
(FR-007a, D-018, R4). The NC and ND variants are not seeded: they fail the Open Definition.

Not a data migration. Which licences a portal offers is the portal's own decision, and a pipeline
entry is a default a portal can drop where a migration is not.

## Indexes

Article IX asks every field's indexing to be a stated decision.

| Column | State | Reason |
|---|---|---|
| `Dataset.visibility` | **newly indexed** | Once the default manager filters on it, every query the framework issues carries `visibility != PRIVATE`, making it the most-used predicate in the package. It was unindexed while nothing filtered by it by default. |
| `Dataset.created_by` | indexed | By virtue of being a foreign key. "Which datasets did this user create" is a real query. |
| `Dataset.project` | indexed | Foreign key. |
| `DatasetIdentifier.value` | indexed and unique | Already so on the abstract. |
| `DatasetDescription.type` | indexed | `dataset_desc_type_idx`, already present. |
| `DatasetDate.type` | indexed | `dataset_date_type_idx`, already present. |
| `DatasetLiteratureRelation.relationship_type` | indexed | Already present. |

## Migrations

Two, per Article IX's request for consolidation:

1. One schema migration carrying `created_by`, the `Meta.ordering` change, the `visibility` index and
   the identifier vocabulary's narrowed choices.
2. Nothing else. The licence seeding is a management command rather than a migration (R4, D-018), and
   the alias removal is Python-only — properties are not fields, so they generate no migration.

`makemigrations --check` is green at the end or the work is not finished.

## What this document does not describe

The dataset list, create, edit and delete pages, the forms behind them, the list search box and
`DatasetFilter` — those are `014-dataset-crud-views`. The image field's dimensions and thumbnails —
`015-image-field-spec`. The REST API's representation of a dataset — `011-restful-api`. Metadata
export, which does not exist and is expected to arrive as an addon (D-002).
