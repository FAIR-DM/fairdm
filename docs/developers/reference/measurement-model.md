# Measurement model

This page lists the fields, vocabularies, methods, querysets and rules of the `Measurement` base model that every measurement type extends. It does not list the fields all four core records share, which are on [Core models](core-models.md), or show how to write a type, which is in [How to add a measurement type](../how-to/add-a-measurement-type.md). Methods are listed by name only. Their signatures are on the [Python API](python-api.md) page.

```python
from fairdm.core.measurement.models import Measurement
```

`Measurement` is a polymorphic base. A measurement type is a subclass that adds its own fields, and each type has a table of its own. See [How sample and measurement types are stored](../../explanation/how-sample-and-measurement-types-are-stored.md). Validating a bare `Measurement` raises a `ValidationError`, and `MeasurementForm` refuses to create one.

## Fields

A measurement has the fields of [every core record](core-models.md#fields-every-record-has) and these.

| Field | Type | Default | What it does | Accepts |
|---|---|---|---|---|
| `uuid` | `ShortUUIDField` | Generated, prefix `m` | The identifier used in addresses and the API. | Not editable. Unique. |
| `dataset` | `ForeignKey` to `dataset.Dataset` | None | The dataset the measurement belongs to. It may differ from the sample's dataset. Related name `measurements`. Deleting the dataset deletes the measurement. | A dataset. Required. |
| `sample` | `ForeignKey` to `sample.Sample` | None | The sample the measurement was made on. Deleting a sample that still has measurements is refused, unless they are deleted in the same operation. | A sample of any type. Required. |
| `local_id` | `CharField`, 255 characters, indexed | `None` | The creator's own identifier for the measurement within its dataset. | Text. Optional. |
| `location` | `PointField`, SRID 4326 | `None` | Where the measurement was made, when that differs from where its sample was taken. | A point. Optional. |
| `location_elevation` | `FloatField` | `None` | Metres above mean sea level. Negative below it. | A number. Needs a location. |
| `location_uncertainty` | `FloatField` | `None` | The distance in metres from the location within which the true place lies. | A number of zero or more. Needs a location. |
| `contributors` | `GenericRelation` to `contributors.Contribution` | | The measurement's credits. | |

The location fields are described on [Location fields](location-fields.md). A measurement with no location of its own takes its sample's, for a viewer who may open the sample. See [ADR 0033](../../adr/0033-a-measurement-borrows-its-samples-location-only-for-a-viewer-who-may-open-the-sample.md).

### The value fields

`Measurement` declares no `value` or `uncertainty` field. A type that records a result declares them, and `get_value()` and `print_value()` read them.

| Field | Declared by | Used for |
|---|---|---|
| `value` | The measurement type | The result. A quantity field, or a plain number. |
| `uncertainty` | The measurement type | The uncertainty of `value`. Optional. |

The rules are described in [How a measurement reports its value](../explanation/how-a-measurement-reports-its-value.md).

### Names a type cannot reuse

A field on a measurement type that has one of these names clashes with an inherited field or a reverse accessor.

- Fields: `id`, `polymorphic_ctype`, `added`, `modified`, `image`, `name`, `keywords`, `tags`, `options`, `dataset`, `uuid`, `sample`, `local_id`, `location`, `location_elevation`, `location_uncertainty`, `contributors`.
- Reverse accessors: `descriptions`, `dates`, `identifiers`.

## Class attributes

| Name | Value |
|---|---|
| `CONTRIBUTOR_ROLES` | The `Measurement` collection of `FairDMRoles`. |
| `DATE_TYPES` | The `Measurement` collection of `FairDMDates`. |
| `DESCRIPTION_TYPES` | The `Measurement` collection of `FairDMDescriptions`. |
| `type_of` | `Measurement`. A class property that polymorphic queries use. |

## Descriptions, dates and identifiers

`MeasurementDescription`, `MeasurementDate` and `MeasurementIdentifier` link to a measurement by `related` and are reached as `descriptions`, `dates` and `identifiers`. A measurement has at most one row of each type. Saving a row with a `type` outside the vocabulary raises a `ValidationError`, even through `objects.create()`.

| Rows | Types | `value` |
|---|---|---|
| `MeasurementDescription` | `MeasurementConditions`, `MeasurementSetup`, `MeasurementTearDown`, `Other` | Text of at most 20,000 characters. |
| `MeasurementDate` | `Setup`, `TearDown` | A partial date. See [Model fields](model-fields.md). |
| `MeasurementIdentifier` | `DOI` | Text of at most 255 characters, unique across every kind of record. |

The roles a person or organization can hold on a measurement are `MeasurementPreparation`, `MeasurementCollection` and `Support`.

## Methods

| Name | Returns |
|---|---|
| `get_value()` | The `value`, paired with the `uncertainty` when the value supports it. The measurement's `name` when the type declares no `value`. |
| `print_value()` | The result of `get_value()` as text. |
| `__str__()` | The value as text when there is one, otherwise the `name`, otherwise the `uuid`. |
| `effective_location_for(user=None)` | An `EffectiveLocation` for the viewer, or `None`. |
| `get_absolute_url()` | The address of the measurement's overview page. |
| `get_template_name()` | The card templates to try, `<app_label>/<model_name>_card.html` then `fairdm/measurement_card.html`. |

`clean()` refuses to move a measurement to a dataset when that would leave nobody able to manage it.

### EffectiveLocation

`EffectiveLocation` is a named tuple that `effective_location_for()` returns.

| Attribute | Type | What it holds |
|---|---|---|
| `point` | `Point`, SRID 4326 | The location. |
| `elevation` | `float` or `None` | Metres above mean sea level. |
| `uncertainty` | `float` or `None` | Metres. |
| `source` | `str` | `"own"` for the measurement's location and `"sample"` for its sample's. |

## Queryset

`Measurement.objects` serves `MeasurementQuerySet`, which is polymorphic. Every method returns a queryset and chains with the others. A type's own queryset should extend it, as in [How to add queryset methods to a measurement type](../how-to/add-queryset-methods-to-a-measurement-type.md).

| Method | Returns |
|---|---|
| `with_related()` | The measurements with sample, dataset, credits and their roles loaded. |
| `with_metadata()` | The measurements with descriptions, dates and identifiers loaded. |
| `with_effective_location(user=None)` | The measurements with `effective_location` added: their own location, otherwise their sample's when the viewer may open the sample. |
| `inside(area, user=None)` | The measurements whose effective location lies in a polygon or a `(west, south, east, north)` box. |
| `within_distance(point, distance, user=None)` | The measurements whose effective location is within a distance of a point. |
| `nearest(point, user=None)` | The measurements ordered by distance of their effective location, each carrying `distance`. |
| `published()` | The measurements whose own dataset is published. |
| `visible_to(user)` | The measurements the user may see. |
| `with_level(user, level)` | The measurements on which the user holds at least a level. |
| `accessible_to(user, level)` | The measurements the user may act on at a level. |
| `instance_of(*types)` and `not_instance_of(*types)` | Measurements that are, or are not, of the given types. These come from [django-polymorphic](https://django-polymorphic.readthedocs.io/). |

A measurement follows its own dataset for access, not its sample's. The visibility and level methods are described on [Contribution levels and record access](contribution-levels-and-record-access.md).

## Meta

| Option | Value |
|---|---|
| `ordering` | `["-modified"]` |
| `default_related_name` | `measurements` |
| `permissions` | `add_contributor`, `modify_contributor`, `modify_metadata` |

## Base configuration

`BaseMeasurementConfiguration` in `fairdm.core.measurement.config` is the registry configuration to extend for a measurement type.

| Attribute | Value |
|---|---|
| `fields` | `name`, `sample`, `dataset`, `image` |
| `form_fields` | `name`, `sample`, `dataset`, `image` |
| `table_fields` | `name`, `sample`, `dataset`, `added`, `modified` |
| `filterset_fields` | `sample`, `dataset`, `added` |
| `display_name` | `Measurement` |
| `description` | `Observation or calculation recorded from a sample` |

For the form, table and filter set, the component's own list above comes first and the type's `fields` follow, minus anything in `exclude`. The serializer, resource and admin read only the type's `fields`, so a type lists `name`, `sample` and `dataset` there too. Because the base sets `form_fields`, `table_fields` and `filterset_fields`, a type that supplies `form_class`, `table_class` or `filterset_class` sets the matching field list to `None`. See [Model configuration](model-configuration.md).

## Admin, form and filter bases

| Class | Module | Described on |
|---|---|---|
| `MeasurementChildAdmin` | `fairdm.core.measurement.admin` | [How to customise the admin for a measurement type](../how-to/customise-the-admin-for-a-measurement-type.md) |
| `MeasurementFormMixin` | `fairdm.core.measurement.forms` | [Form and filter mixins](form-and-filter-mixins.md) |
| `MeasurementFilterMixin` | `fairdm.core.measurement.filters` | [Form and filter mixins](form-and-filter-mixins.md) |
