# Model configuration

This page describes `ModelConfiguration`, the class a portal writes to register a sample or measurement type, and every option it takes. It also lists what the registry refuses and the classes that hold a type's metadata. It does not show how to register a type, which is in [How to register a sample or measurement type](../how-to/register-a-sample-or-measurement-type.md), or describe the registry that stores configurations, which is in [The registry](registry.md).

## Import

```python
from fairdm.registry import (
    Authority,
    Citation,
    MeasurementConfig,
    ModelConfiguration,
    ModelMetadata,
    SampleConfig,
    register,
)
from fairdm.core.measurement.config import BaseMeasurementConfiguration
from fairdm.core.sample.config import BaseSampleConfiguration
```

## Declaring a configuration

A configuration is a subclass that sets class attributes, the way `Meta` and `ModelAdmin` are written. The `register` decorator builds one instance of it.

```python
from fairdm.registry import ModelConfiguration, register

from .models import PlantSample


@register
class PlantSampleConfig(ModelConfiguration):
    model = PlantSample
    fields = ["name", "dataset", "species", "collected_on"]
```

`PlantSample` is a sample type with the fields `species` and `collected_on`.

An instance is built from this signature, which the decorator calls without arguments.

```python
ModelConfiguration(model=None, **overrides)
```

`model` is the model, and each keyword in `overrides` sets an option on that instance. The options that can be set this way are `metadata`, `fields`, `exclude`, `search_fields`, the six component field lists, the six component classes, `display_name` and `description`. Any other keyword raises `TypeError`. An instance gets its own copy of `fields` and `exclude`, so changing one instance's list never changes another's.

## Options

### `model`

Type: `type[Model]`. Default: none, the option is required.

The model the configuration describes.

Accepts a concrete subclass of `Sample` or of `Measurement`. A configuration built without a model raises `ConfigurationError`. The registry refuses any other model when it registers the configuration. See [Refused configurations](#refused-configurations).

### `metadata`

Type: `ModelMetadata | None`. Default: `None`, which becomes an empty `ModelMetadata()` when the instance is built.

Describes the type for people and for other systems. The API documentation and the page of each record of the type show it, and the home page shows its description. See [ModelMetadata](#modelmetadata).

Accepts a `ModelMetadata` instance.

### `fields`

Type: `list[str | tuple[str, ...]]`. Default: `[]`.

The field list that every component uses when it has none of its own. An empty list leaves the choice to the framework. See [How a field list is resolved](#how-a-field-list-is-resolved).

Accepts field names of the model. A name may be a double-underscore path, such as `dataset__name`. The registry checks each segment and refuses the configuration when one does not resolve. A tuple groups names for layout and gives the same fields as writing them one by one.

### `exclude`

Type: `list[str]`. Default: `[]`.

Names that are left out of every component, including the lists you declared.

Accepts any names. The registry does not check them, and a name that is not in a list has no effect.

### `search_fields`

Type: `list[str] | None`. Default: `None`, which means `["name"]`.

The paths that the listing's search box matches, through the `q` filter of the generated filter set. A record is kept when any word of the search term appears, ignoring case, in any of the paths. The option does not change the search of the administration interface, which takes its own from the field list in `admin_list_display`.

Accepts paths that end in a `CharField` or a `TextField`, including their subclasses. A path that names no field, or ends in a number, a boolean, a date or a geometry, is refused. See [How to search a registered type by more than its name](../how-to/search-a-registered-type-by-more-than-its-name.md).

### `display_name`

Type: `str`. Default: `""`, which becomes the model's `verbose_name` in title case when the instance is built.

A human-readable name for the type. `get_display_name()` returns it. The portal's own pages name a type by the model's `verbose_name` and `verbose_name_plural`, not by this option.

Accepts any string.

### `description`

Type: `str`. Default: `""`.

A sentence about the type. The portal shows it where it describes the type, unless `metadata.description` is set, which takes its place. `get_description()` returns `metadata.description` first, then this option, then `Configuration for <ModelName>`.

Accepts any string.

## Component field lists

Each of these gives one component a field list of its own. Each has the type `list[str | tuple[str, ...]] | None` and the default `None`, which means the component uses `fields`. Each accepts what `fields` accepts. An empty list is a list of no fields and is not the same as `None`.

| Name | Component | What it lists |
|---|---|---|
| `form_fields` | form | The fields of the form on a record's **Edit details** page. |
| `table_fields` | table | The columns of the listing table. |
| `filterset_fields` | filter set | The filters of the listing. |
| `serializer_fields` | serializer | The fields the API adds to those every sample or measurement carries. |
| `resource_fields` | resource | The columns of the import and export resource. |
| `admin_list_display` | admin | The fields the administration changelist draws its columns, search and filters from. The add and change forms show every field of the model. |

## Component classes

Each of these replaces one generated component. Each has the type `type | str | None` and the default `None`, which means the registry generates the component.

| Name | Component | The class must subclass |
|---|---|---|
| `form_class` | form | `django.forms.ModelForm` |
| `table_class` | table | `django_tables2.Table` |
| `filterset_class` | filter set | `django_filters.FilterSet` |
| `serializer_class` | serializer | `rest_framework.serializers.BaseSerializer`, and the base serializer of the type's kind when the API loads: `BaseSampleSerializer` or `BaseMeasurementSerializer` |
| `resource_class` | resource | `import_export.resources.ModelResource` |
| `admin_class` | admin | `django.contrib.admin.ModelAdmin`, and `SampleChildAdmin` or `MeasurementChildAdmin` for the type's kind |

A class option accepts the class or its dotted path. A path is imported when the instance is built, so a wrong path fails at start-up. A component whose class is set cannot also have a field list, whether declared on the configuration or inherited from its base. The registry refuses the configuration. See [How to customise a generated component](../how-to/customise-a-generated-component.md).

## Components

The six components are the rows of `fairdm.registry.config.COMPONENTS`. A factory in `fairdm.registry.factories` builds each one when its class option is not set. `ComponentFactory` takes `model` and `fields`, `FilterFactory` also takes `search_fields`, and each has a `generate()` method that returns the class.

| Component | Field list | Class | Factory | Left out of the framework's own choice |
|---|---|---|---|---|
| form | `form_fields` | `form_class` | `FormFactory` | |
| table | `table_fields` | `table_class` | `TableFactory` | |
| filter set | `filterset_fields` | `filterset_class` | `FilterFactory` | |
| serializer | `serializer_fields` | `serializer_class` | `SerializerFactory` | `options`, `tags` |
| resource | `resource_fields` | `resource_class` | `ResourceFactory` | |
| admin | `admin_list_display` | `admin_class` | `AdminFactory` | |

What each factory chooses is in [What registering a type produces](../explanation/what-registering-a-type-produces.md).

## How a field list is resolved

`resolve_fields(component)` decides which fields a component is built from. It takes the first of these that applies:

1. The component's own list, when it is not `None`.
2. `fields`, when it is not empty.
3. The framework's own choice for the model.

It then flattens tuples and removes every name in `exclude`.

The framework's own choice is every field of the model that can be edited, except the primary key, the polymorphic type columns, the inheritance pointers that end in `_ptr`, a field named `password`, fields that fill themselves in with `auto_now` or `auto_now_add`, and many-to-many fields that use an explicit through model. Reverse relations are not fields of the model and are never part of it. A portal that wants a field from this list to be absent says so in `exclude`, and one that wants it present says so in a list.

The measurement base configuration changes the rule for three components. See [Measurement model](measurement-model.md#base-configuration).

## Methods

| Method | Returns |
|---|---|
| `get_form_class()` | The form class: the one in `form_class`, or one generated from `resolve_fields("form")`. |
| `get_table_class()` | The table class, in the same way. |
| `get_filterset_class()` | The filter set class, generated with `get_search_fields()` as its search paths. |
| `get_serializer_class()` | The serializer class. |
| `get_resource_class()` | The resource class. |
| `get_admin_class()` | The admin class. |
| `resolve_fields(component)` | The flat list of field names for a component. `component` is `"form"`, `"table"`, `"filterset"`, `"serializer"`, `"resource"` or `"admin"`. |
| `get_search_fields()` | `search_fields`, or `["name"]` when it is `None`. |
| `get_default_fields(model)` | The framework's own choice of field names for a model. A class method. |
| `get_display_name()` | `display_name`, or the model's `verbose_name` in title case. |
| `get_description()` | The description, as `description` explains. |
| `get_slug()` | The model's lower-case name. The listing address and the listing's URL name use it. |
| `get_verbose_name()` and `get_verbose_name_plural()` | The model's `verbose_name` and `verbose_name_plural`. The menu entries and the listing headings use the plural. |

No accessor caches its result. Each call resolves or builds the class again, so overriding an accessor changes what every part of the framework receives.

## ModelMetadata

`ModelMetadata` holds what a registered type says about itself. It takes its attributes as arguments, all optional.

| Attribute | Type | Default | What it holds |
|---|---|---|---|
| `description` | `str` | `""` | What the type is. Wins over `description` on the configuration. |
| `authority` | `Authority \| None` | `None` | The body that maintains the type. |
| `keywords` | `list[str]` | `[]` | Words that describe the type. |
| `repository_url` | `str` | `""` | Where the type's code lives. The API documentation links to it. |
| `citation` | `Citation \| None` | `None` | How to cite the type's protocol. |
| `maintainer` | `str` | `""` | A person who maintains the type. |
| `maintainer_email` | `str` | `""` | The maintainer's address. |

The API documentation shows `description`, `authority`, `citation` and `keywords` in the description of the type's list operation, and `repository_url` as a link. The page of a record shows `description`, `authority`, `citation` and `keywords` too. `maintainer` and `maintainer_email` are not shown anywhere.

`Authority` and `Citation` take keyword arguments only.

| Class | Attribute | Type | Default | What it holds |
|---|---|---|---|---|
| `Authority` | `name` | `str` or a lazy translation | none, required | The authority's full name. |
| `Authority` | `short_name` | `str` | `""` | An abbreviation. |
| `Authority` | `website` | `str` | `""` | The authority's website. |
| `Citation` | `text` | `str` | `""` | The full citation. |
| `Citation` | `doi` | `str` | `""` | The DOI. A record's page shows a DOI without `https://` as `https://doi.org/` followed by the DOI. |

## Base configurations

`SampleConfig` and `MeasurementConfig` are subclasses of `ModelConfiguration` that add nothing. They say at the call site which kind of type is registered, and they set no fields.

`BaseSampleConfiguration` and `BaseMeasurementConfiguration` do set fields. A type extends the one for its kind, and the page of each model describes its values.

| Class | Module | Described on |
|---|---|---|
| `BaseSampleConfiguration` | `fairdm.core.sample.config` | [Sample model](sample-model.md#base-configuration) |
| `BaseMeasurementConfiguration` | `fairdm.core.measurement.config` | [Measurement model](measurement-model.md#base-configuration) |

## Refused configurations

The registry checks a configuration when it is built and when it is registered, and a refusal stops the portal at start-up. The exceptions are in `fairdm.registry.exceptions`, except `ImproperlyConfigured`, which is Django's. `ConfigurationError`, `FieldValidationError` and `DuplicateRegistrationError` all subclass `RegistryError`.

| What is refused | Exception | When |
|---|---|---|
| No `model`. | `ConfigurationError` | Built |
| A keyword argument that is not an option. | `TypeError` | Built |
| A component with both a field list and a class. | `ImproperlyConfigured` | Built |
| A name in a field list, or a segment of a path, that does not resolve. | `FieldValidationError` | Built |
| A `search_fields` path that ends in a field that is not a `CharField` or a `TextField`. | `FieldValidationError` | Built |
| A class that does not subclass the base its component requires. | `ConfigurationError` | Built |
| An `admin_class` that is not `SampleChildAdmin` or `MeasurementChildAdmin` for the type's kind. | `ConfigurationError` | Built |
| An abstract model, `Sample` or `Measurement` itself, or a model that extends neither. | `ConfigurationError` | Registered |
| A model that is already registered. | `DuplicateRegistrationError` | Registered |
| A class passed to `register` with no `model`. | `ValueError` | Registered |

A `FieldValidationError` names the model, the option that held the name, the name, and either a close match or the reason the path stopped:

```text
Invalid field 'rock_typ' in RockSample.fields: no such field on RockSample. Did you mean: rock_type?
```

```text
Invalid field 'rock_type__x' in RockSample.fields: 'rock_type' is not a relation, so the rest of the path cannot resolve
```

A `DuplicateRegistrationError` names the module and function of the first registration:

```text
RockSample already registered at rocks.config. Each model can only be registered once. Attempted duplicate registration from another.module.
```
