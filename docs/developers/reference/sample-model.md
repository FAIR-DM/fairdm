# Sample model

This page lists the fields, vocabularies, relations, querysets and rules of the `Sample` base model that every sample type extends. It does not list the fields all four core records share, which are on [Core models](core-models.md), or show how to write a type, which is in [How to add a sample type](../how-to/add-a-sample-type.md). Methods are listed by name only. Their signatures are on the [Python API](python-api.md) page.

```python
from fairdm.core.sample.models import Sample
```

`Sample` is a polymorphic base. A sample type is a subclass that adds its own fields, and each type has a table of its own. See [How sample and measurement types are stored](../../explanation/how-sample-and-measurement-types-are-stored.md). The base model cannot be saved. Saving a bare `Sample` by any route raises a `ValidationError`, and `full_clean()` on one reports the same error.

## Fields

A sample has the fields of [every core record](core-models.md#fields-every-record-has) and these.

| Field | Type | Default | What it does | Accepts |
|---|---|---|---|---|
| `uuid` | `ShortUUIDField` | Generated, prefix `s` | The identifier used in addresses and the API. | Not editable. Unique. |
| `dataset` | `ForeignKey` to `dataset.Dataset` | None | The dataset the sample first appeared in. Related name `samples`. Deleting the dataset deletes the sample. | A dataset. Required. |
| `local_id` | `CharField`, 255 characters | `None` | The creator's own identifier for the sample within its dataset. It need not be unique. | Text. Optional. |
| `status` | `ConceptField` on the sample status vocabulary | The address of `unknown` | The custody state of the physical specimen. | The address of a [status](#status). |
| `location` | `PointField`, SRID 4326 | `None` | Where the sample was taken, as a point in WGS 84. | A point. Optional. |
| `location_elevation` | `FloatField` | `None` | Metres above mean sea level. Negative below it. | A number. Needs a location. |
| `location_uncertainty` | `FloatField` | `None` | The distance in metres from the location within which the true place lies. | A number of zero or more. Needs a location. |
| `contributors` | `GenericRelation` to `contributors.Contribution` | | The sample's credits. | |
| `related` | `ManyToManyField` to `Sample` through `SampleRelation` | Empty | The samples this one is related to. Not symmetrical. Related name `related_from`. | Samples. Optional. |

Two check constraints keep the location fields consistent: an uncertainty is empty or zero or more, and an elevation or uncertainty needs a location. The location fields are described on [Location fields](location-fields.md). The reasoning for keeping a location on each record is in [ADR 0032](../../adr/0032-a-location-is-a-value-on-each-record.md).

### Names a type cannot reuse

A field on a sample type that has one of these names clashes with an inherited field or a reverse accessor.

- Fields: `id`, `polymorphic_ctype`, `added`, `modified`, `image`, `name`, `keywords`, `tags`, `options`, `dataset`, `uuid`, `local_id`, `status`, `location`, `location_elevation`, `location_uncertainty`, `contributors`, `related`.
- Reverse accessors: `descriptions`, `dates`, `identifiers`, `measurements`, `related_samples`, `related_to`, `related_from`.

## Status

`Sample.status` holds the address of one of the concepts of the sample status vocabulary, `https://w3id.org/fairdm/vocabularies/sample-status`, which `fairdm.core.vocabularies` names `SAMPLE_STATUS`. A concept's address is the vocabulary's address, a slash and the identifier below. A sample can move from any status to any other, including out of `destroyed`.

| Identifier | Label | Meaning |
|---|---|---|
| `available` | Available | Accessible and not checked out, in storage or destroyed. |
| `in-use` | In Use | Checked out or in active use. |
| `stored` | Stored | In long-term storage. |
| `destroyed` | Destroyed | Consumed, destroyed or otherwise no longer physically available. |
| `unknown` | Unknown | The custody state is not known. |

## Class attributes

| Name | Value |
|---|---|
| `CONTRIBUTOR_ROLES` | The address of the sample collection of the contributor roles. |
| `DATE_TYPES` | The address of the sample collection of the date types. |
| `DESCRIPTION_TYPES` | The address of the sample collection of the description types. |
| `type_of` | `Sample`. A class property that polymorphic queries use. |

## Descriptions, dates and identifiers

`SampleDescription`, `SampleDate` and `SampleIdentifier` link to a sample by `related` and are reached as `descriptions`, `dates` and `identifiers`. A sample has at most one row of each type. `type` is a `ConceptField` limited to the sample collection of its vocabulary, and holds the concept's address. `full_clean()` refuses a `type` outside the collection, but a plain `objects.create()` does not call it. The types, by identifier, in the order their collections list them:

| Rows | Types | `value` |
|---|---|---|
| `SampleDescription` | `sample-collection`, `sample-preparation`, `sample-storage`, `sample-destruction`, `other` | Text of at most 20,000 characters. |
| `SampleDate` | `created`, `destroyed`, `collected`, `returned`, `prepared`, `archival`, `restored` | A partial date. See [Model fields](model-fields.md). |
| `SampleIdentifier` | `igsn`, `doi` | Text of at most 255 characters, unique across every kind of record. |

When an identifier is validated, a common display prefix is removed first: `https://doi.org/`, `http://doi.org/`, `https://igsn.org/`, `hdl.handle.net/`, `doi:` or `igsn:`. An IGSN must then be a DataCite DOI (`10.` followed by four to nine digits, a slash and a suffix) or a legacy handle beginning `10273/`. The match ignores case.

The roles a person or organization can hold on a sample, by identifier, are `collection`, `preparation`, `storage`, `destruction` and `restoration`.

## SampleRelation

`SampleRelation` records that one sample came from another. It has no timestamps.

| Field | Type | Default | What it does | Accepts |
|---|---|---|---|---|
| `type` | `CharField`, 255 characters | None | The kind of relationship. | `child_of`. It is the only type. |
| `source` | `ForeignKey` to `Sample` | None | The child. Related name `related_samples`. | A sample. |
| `target` | `ForeignKey` to `Sample` | None | The parent. Related name `related_to`. | A sample. |

The combination of source, target and type is unique. Both `clean()` and `save()` refuse a sample related to itself and a link whose reverse already exists with the same type. For the steps, see [How to record sample relationships](../how-to/record-sample-relationships.md).

## Methods

| Name | Returns |
|---|---|
| `get_all_relationships()` | The `SampleRelation` objects in which the sample is the source or the target. |
| `get_related_samples(relationship_type=None)` | The samples related to this one in either direction, optionally of one type. |
| `get_children()` | The samples that are children of this one. |
| `get_parents()` | The samples that are parents of this one. |
| `get_descendants(depth=None)` | The descendants, to a depth. `None` means unlimited and `1` means direct children only. |
| `get_ancestors(depth=None)` | The ancestors, to a depth. |
| `get_absolute_url()` | The address of the sample's overview page. |
| `get_template_name()` | The card templates to try, `<app_label>/<model_name>_card.html` then `fairdm/sample_card.html`. |

`clean()` also refuses to move a sample to a dataset when that would leave nobody able to manage it.

## Queryset

`Sample.objects` serves `SampleQuerySet`, which is polymorphic. Every method returns a queryset and chains with the others.

| Method | Returns |
|---|---|
| `with_related()` | The samples with dataset, project and credits loaded. |
| `with_metadata()` | The samples with descriptions, dates and identifiers loaded. |
| `with_keywords()` | The samples with keywords loaded. |
| `by_relationship(related_to=None, relationship_type=None)` | With `related_to`, the children of that sample. Without it, every sample in a matching relation. |
| `get_descendants(sample, max_depth=None)` | The descendants of a sample. |
| `get_ancestors(sample, max_depth=None)` | The ancestors of a sample. |
| `inside(area)` | The samples located in a polygon or a `(west, south, east, north)` box. |
| `within_distance(point, distance)` | The samples within a distance of a point, measured on the ground. |
| `nearest(point)` | The samples ordered by distance, each carrying `distance`. |
| `published()` | The samples whose own dataset is published. |
| `visible_to(user)` | The samples the user may see. |
| `with_level(user, level)` | The samples on which the user holds at least a level. |
| `accessible_to(user, level)` | The samples the user may act on at a level. |
| `instance_of(*types)` and `not_instance_of(*types)` | Samples that are, or are not, of the given types. These come from [django-polymorphic](https://django-polymorphic.readthedocs.io/). |

`inside`, `within_distance` and `nearest` are described on [Location fields](location-fields.md). The visibility and level methods are described on [Contribution levels and record access](contribution-levels-and-record-access.md).

## Meta

| Option | Value |
|---|---|
| `ordering` | `["added"]` |
| `default_related_name` | `samples` |
| `permissions` | `add_contributor`, `modify_contributor`, `modify_metadata`, `import_data` |

## Base configuration

`BaseSampleConfiguration` in `fairdm.core.sample.config` is the registry configuration to extend for a sample type. It sets only `fields`.

| Attribute | Value |
|---|---|
| `fields` | `name`, `dataset`, `local_id`, `status`, `location`, `image` |

It sets no per-component field list, so a subclass that sets `fields` changes every component at once. See [Model configuration](model-configuration.md).
