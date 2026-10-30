# Core models

This page lists the fields, choices, managers and rules of the two fixed core models, `Project` and `Dataset`, and the fields they share with samples and measurements. It does not cover the two models you extend, which are on [Sample model](sample-model.md) and [Measurement model](measurement-model.md), or why the four levels exist, which is in [The core data model](../../explanation/the-core-data-model.md). Methods are listed by name only. Their signatures are on the [Python API](python-api.md) page.

Import the models from their own modules:

```python
from fairdm.core.dataset.models import Dataset
from fairdm.core.project.models import Project
```

`fairdm.core.models` also re-exports `Project`, `Dataset`, `Sample` and `Measurement`.

```{mermaid}
erDiagram
    Organization |o--o{ Project : owns
    Project |o--o{ Dataset : holds
    Dataset ||--o{ Sample : holds
    Dataset ||--o{ Measurement : holds
    Sample ||--o{ Measurement : "is measured by"
    Sample }o--o{ Sample : "SampleRelation"
```

## Fields every record has

`Project`, `Dataset`, `Sample` and `Measurement` all inherit these fields. `BaseModel` in `fairdm.core.abstract` supplies the first group, and `Model` in `fairdm.db.models` supplies `added` and `modified`.

| Field | Type | Default | What it does | Accepts |
|---|---|---|---|---|
| `id` | `BigAutoField` | Assigned on save | The database key. | Not editable. |
| `uuid` | `ShortUUIDField` | Generated on save | The identifier used in addresses and the API. A prefix names the kind of record: `p`, `d`, `s` or `m`, followed by 22 characters. | Not editable. Unique. |
| `name` | `CharField` | None | The record's title. | Up to 300 characters. Required. |
| `image` | `ThumbnailerImageField` | `None` | A picture of the record. The stored source is limited to 2400 by 1600 pixels without cropping. | An image file. Optional. |
| `keywords` | `MultiConceptField` | Empty | Controlled keywords for discoverability. | Concepts from any loaded vocabulary. Optional. |
| `tags` | `TaggableManager` through `fairdm.models.TaggedItem` | Empty | Free words. | Any text. Optional. |
| `options` | `JSONField` | `None` | A place for settings of your own. | Any JSON value. Optional. |
| `added` | `DateTimeField` | The time of creation | When the record was added. | Not editable. |
| `modified` | `DateTimeField` | The time of each save | When the record was last saved. | Not editable. |

`tracker` is a `FieldTracker` from django-model-utils. It adds no column.

### Methods every record has

| Name | Returns |
|---|---|
| `title` | The record's `name`. A property. |
| `icon` | The icon name for the model. A property. |
| `get_absolute_url()` | The address of the record's overview page. |
| `get_api_url()` | The address of the record's API detail endpoint. |
| `add_contributor(contributor, with_roles=None)` | The contributor's credit on the record, created or extended with the roles. |
| `is_contributor(user)` | Whether the user has a credit on the record. |
| `get_direct_contributors()` | The people and organizations credited on the record. |
| `get_affiliated_organizations()` | The organizations named as affiliations on the record's credits. |
| `get_all_contributors()` | The credited contributors together with those affiliated organizations. |
| `get_abstract()` | The record's description of type `Abstract`, or `None`. |
| `get_abstract_summary()` | The abstract as plain text of at most 400 characters. |
| `get_meta_description()` | The abstract's full text, or `None`. |
| `get_descriptions` | The record's descriptions as a list. A cached property. |
| `verbose_name()` and `verbose_name_plural()` | The model's names. |
| `get_non_polymorphic_instance()` | The record fetched again as its polymorphic base (`Sample` or `Measurement`), or the record itself when it has none. |

## Project

`fairdm.core.project.models.Project` is a body of research that groups datasets. A dataset may belong to a project but does not have to.

| Field | Type | Default | What it does | Accepts |
|---|---|---|---|---|
| `uuid` | `ShortUUIDField` | Generated, prefix `p` | See above. | Not editable. |
| `visibility` | `IntegerField` | `Visibility.PRIVATE` | Whether the project is public or private. | A value of [`Visibility`](#choices). |
| `status` | `IntegerField` | `ProjectStatus.CONCEPT` | The project's stage. | A value of [`ProjectStatus`](#choices). |
| `funding` | `JSONField` | `None` | Funding awards in the shape of DataCite's funding reference. | `None`, or a list of objects. See below. Optional. |
| `owner` | `ForeignKey` to `contributors.Organization` | `None` | The organization that owns the project. Related name `owned_projects`. Deleting an organization that owns a project is refused. | An organization. Optional. |
| `created_by` | `ForeignKey` to `contributors.Person` | `None` | The person who created the project. Related name `created_projects`. Set to empty if that person's account is removed. | Not editable. |
| `contributors` | `GenericRelation` to `contributors.Contribution` | | The project's credits. | |

Each object in `funding` accepts these keys and no others:

| Key | Required | Accepts |
|---|---|---|
| `funderName` | Yes | Text. |
| `funderIdentifier` | No | Text. |
| `funderIdentifierType` | No | `ISNI`, `GRID`, `Crossref Funder ID`, `ROR` or `Other`. |
| `awardNumber` | No | Text. |
| `awardTitle` | No | Text. |
| `awardURI` | No | Text. |

A value that is not a list of such objects fails validation with one of the codes `funding_not_list`, `funding_unknown_key`, `funding_missing_funder_name`, `funding_invalid_type` or `funding_invalid_identifier_type`.

### Class attributes

| Name | Value |
|---|---|
| `DEFAULT_ROLES` | `[PROJECT_MEMBER]`, the address of the project member role |
| `CONTRIBUTOR_ROLES` | The address of the project collection of the contributor roles. |
| `DATE_TYPES` | The address of the project collection of the date types. |
| `DESCRIPTION_TYPES` | The address of the project collection of the description types. |
| `STATUS_CHOICES` | `ProjectStatus` |
| `VISIBILITY` | `Visibility` |
| `STATUS_BADGE_VARIANTS` | The theme colour name of each status on a project card. |

### Properties and methods

| Name | Returns |
|---|---|
| `is_active` | Whether the status is `IN_PROGRESS`. |
| `status_badge_variant` | The colour name for the status badge. `neutral` when the status has none. |
| `spatial_coverage(user=None)` | The box that holds the locations the viewer may see in the project's datasets, or `None`. |

### Deletion

Deleting a project deletes its datasets. A project that still has a public dataset cannot be deleted. The attempt raises `PublicDatasetsProtect`, which carries the blocking datasets.

## Dataset

`fairdm.core.dataset.models.Dataset` is the unit a portal cites and distributes. Samples and measurements hang beneath it.

| Field | Type | Default | What it does | Accepts |
|---|---|---|---|---|
| `uuid` | `ShortUUIDField` | Generated, prefix `d` | See above. | Not editable. |
| `visibility` | `IntegerField`, indexed | `Visibility.PRIVATE` | Whether the dataset's metadata is shown to everyone. | A value of [`Visibility`](#choices). |
| `published` | `BooleanField`, indexed | `False` | Whether the data beneath the dataset may be shown publicly. It is independent of `visibility`, which governs metadata only. | `True` or `False`. Set in the administration interface. |
| `project` | `ForeignKey` to `project.Project` | `None` | The project the dataset belongs to. Related name `datasets`. Deleting the project deletes the dataset. | A project. Optional. |
| `reference` | `OneToOneField` to `literature.Item` | `None` | The data publication for the dataset. | A literature item. Optional. |
| `related_literature` | `ManyToManyField` to `literature.Item` through `DatasetLiteratureRelation` | Empty | Literature related to the dataset. | Literature items. Optional. |
| `license` | `LicenseField` | The licence named by `FAIRDM_DEFAULT_LICENSE` | The licence the dataset's data is published under. | A licence. Optional. |
| `created_by` | `ForeignKey` to `contributors.Person` | `None` | The person who created the dataset. Related name `created_datasets`. | Not editable. |
| `contributors` | `GenericRelation` to `contributors.Contribution` | | The dataset's credits. | |

`FAIRDM_DEFAULT_LICENSE` is described on [Settings](settings.md). The default is read when a dataset is created. If the portal has not loaded its licences yet, the default is empty.

### Class attributes

| Name | Value |
|---|---|
| `DEFAULT_ROLES` | `[PROJECT_MEMBER]`, the address of the project member role |
| `CONTRIBUTOR_ROLES` | The address of the dataset collection of the contributor roles. |
| `DATE_TYPES` | The address of the dataset collection of the date types. |
| `DESCRIPTION_TYPES` | The address of the dataset collection of the description types. |
| `IDENTIFIER_TYPES` | The address of the dataset collection of the identifier types. |
| `VISIBILITY_CHOICES` | `Visibility` |

### Properties and methods

| Name | Returns |
|---|---|
| `data_is_public` | Whether the visibility is public and the dataset is published. |
| `has_data` | Whether any sample or measurement hangs beneath the dataset. A cached property. |
| `spatial_coverage(user=None)` | The box that holds the locations the viewer may see in the dataset's samples and measurements, or `None`. |

`clean()` refuses to move a dataset to a project when that would leave nobody able to manage it.

### Managers

| Manager | Returns |
|---|---|
| `Dataset.objects` | Every dataset that is not private. |
| `Dataset.all_objects` | Every dataset. |

Use `all_objects` whenever you need private datasets. Following a relation to a dataset and cascading a deletion are not narrowed by `objects`. The reasoning for the separate publication flag is in [ADR 0014](../../adr/0014-publication-is-a-separate-flag-from-visibility.md).

### DatasetLiteratureRelation

`DatasetLiteratureRelation` links a dataset to a literature item with a DataCite relation type.

| Field | Type | Default | What it does | Accepts |
|---|---|---|---|---|
| `dataset` | `ForeignKey` to `Dataset` | None | The dataset. Related name `literature_relations`. | A dataset. |
| `literature_item` | `ForeignKey` to `literature.Item` | None | The literature item. Related name `dataset_relations`. | A literature item. |
| `relationship_type` | `CharField`, 50 characters | None | How the dataset relates to the item. | One of the 34 relation types of DataCite Metadata Schema 4.4, such as `IsCitedBy`, `Cites` or `IsDocumentedBy`. |

The combination of dataset, item and type is unique.

## Choices

| Name | Members |
|---|---|
| `ProjectStatus` in `fairdm.core.choices` | `CONCEPT` (0), `PLANNING` (1), `IN_PROGRESS` (2), `COMPLETE` (3), `SEARCHING_FOR_COLLABORATORS` (4) |
| `Visibility` in `fairdm.utils.choices` | `PRIVATE` (0), `PUBLIC` (1) |

## Querysets

Both models have a queryset with these methods.

| Method | Project | Dataset | Returns |
|---|---|---|---|
| `get_visible()` | Yes | Yes | For a project, the public projects. For a dataset, the public datasets that are not inside a private project. |
| `published()` | No | Yes | The datasets whose `published` flag is set. Call it on `all_objects`. |
| `with_contributors()` | Yes | Yes | The records with their credits loaded. |
| `with_metadata()` | Yes | Yes | The records with descriptions, dates, identifiers, credits and keywords loaded. A project also loads its owner. |
| `with_related()` | No | Yes | The records with project and credits loaded. |
| `with_list_data()` | Yes | Yes | The records with what a list card draws loaded, and a count. A project gets `dataset_count`, which counts public datasets only. A dataset gets `sample_count` and `measurement_count`. |
| `with_level(user, level)` | Yes | Yes | The records on which the user holds at least a level. |
| `accessible_to(user, level)` | Yes | Yes | The records the user may act on at a level, which is every record for a user with the matching portal-wide right. |

The two level methods are described on [Contribution levels and record access](contribution-levels-and-record-access.md).

## Descriptions, dates and identifiers

A project and a dataset each carry typed rows. A row model exists for each pair, such as `ProjectDescription` and `DatasetDate`. Every row model links back to its record by `related` and is reached from the record by `descriptions`, `dates` or `identifiers`.

| Rows | `type` is drawn from | `value` | Rules |
|---|---|---|---|
| Descriptions | The description types | Text of at most 20,000 characters. | One row of each type for each record. |
| Dates | The date types | A partial date: a year, a year and month, or a full date. See [Model fields](model-fields.md). | One row of each type for each record. The end may not be before the start. |
| Identifiers | The identifier types | Text of at most 255 characters. | One row of each type for each record. The value is unique across every kind of record. |

`type` is a `ConceptField` limited to the record's collection of the vocabulary, and holds the concept's address: the vocabulary's address, a slash and the identifier listed below. The start and end types are `start` and `end` for a project, `ProjectDate.START_TYPE` and `ProjectDate.END_TYPE`, and `collection-start` and `collection-end` for a dataset. The end is compared with the start at the coarser of their two precisions.

The types each record accepts, by identifier, in the order its collection lists them:

| Record | Descriptions | Dates | Identifiers |
|---|---|---|---|
| Project | `abstract`, `introduction`, `background`, `objectives`, `expected-output`, `conclusions`, `other` | `start`, `end` | `doi`, `grant-number`, `proposal-id` |
| Dataset | `abstract`, `methods`, `series-information`, `technical-info`, `other` | `available`, `collection-start`, `collection-end`, `submitted`, `published`, `withdrawn` | `doi` |

The roles a person or organization can hold on a record come from the contributor roles vocabulary, by identifier:

| Record | Roles |
|---|---|
| Project | `creator`, `project-leader`, `project-member`, `project-manager`, `contact-person`, `other` |
| Dataset | `creator`, `contact-person`, `data-collector`, `data-curator`, `data-manager`, `editor`, `producer`, `related-person`, `researcher`, `project-leader`, `project-manager`, `project-member`, `supervisor`, `work-package-leader`, `rights-holder`, `other` |

The vocabularies' addresses are constants in `fairdm.core.vocabularies`, and `get_type_concepts()` on a row model returns the concepts its collection offers. See [Controlled vocabularies](../../explanation/controlled-vocabularies.md).

## Permissions

Both models declare these permissions beside Django's four. Who holds them on a record is decided by the level a person has on it, as described in [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md).

| Model | Permissions |
|---|---|
| Project | `add_contributor`, `modify_contributor`, `modify_metadata`, `change_project_metadata`, `change_project_settings` |
| Dataset | `add_contributor`, `modify_contributor`, `modify_metadata`, `import_data`, `can_publish`, `change_dataset_metadata`, `change_dataset_settings` |

Both are ordered by `-modified` and indexed on `modified`.
