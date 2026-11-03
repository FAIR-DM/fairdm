# The registry

This page describes the registry, the object that holds every registered sample and measurement type, with the `register` decorator, the lookups, the exceptions and the template tag that read it. It does not describe the options of a configuration, which are on [Model configuration](model-configuration.md), or show how to register or find types, which is in [How to register a sample or measurement type](../how-to/register-a-sample-or-measurement-type.md) and [How to loop over the registered types](../how-to/loop-over-the-registered-types.md).

## Import

```python
from fairdm.registry import FairDMRegistry, register, registry
```

After `import fairdm`, `fairdm.register` is the same decorator and `fairdm.registry` is the same registry.

`registry` is the one instance of `FairDMRegistry` in the process. It holds one configuration for each registered model.

## Discovery

When the portal starts, FairDM imports the module named `config` in every installed app. A registration in a module of that name needs no other import. A registration anywhere else takes effect only when something imports its module.

Registration happens as the module is imported, so a refused registration stops the process on every start, under a development server and under a production one alike. Registered types are held in the order they were registered. Apps that `fairdm.setup(apps=[...])` lists come ahead of FairDM's own, in the order listed. See [ADR 0004](../../adr/0004-portal-apps-precede-framework-apps.md).

## `register`

Signature: `register(config_cls)`.

A class decorator. It builds one instance of `config_cls` with no arguments, registers the model that the class names with that instance, and returns the class unchanged.

| Raises | When |
|---|---|
| `ValueError` | `config_cls` has no `model` attribute, or it is empty. |
| `ConfigurationError` | The configuration or the model is refused. See [Refused configurations](model-configuration.md#refused-configurations). |
| `DuplicateRegistrationError` | The model is already registered. |

## `registry.register`

Signature: `registry.register(model_class, config=None)`.

Registers a model. `config` is a `ModelConfiguration` instance, a configuration class that the registry instantiates with the model, or `None`, which registers the model with a default configuration that lets the framework choose every field list. The registry refuses a model that is not a concrete subclass of `Sample` or `Measurement`, then a model that is already registered. It then registers the model's admin class and stores the configuration. It raises `ConfigurationError` and `DuplicateRegistrationError`.

```python
registry.register(PlantSample, PlantSampleConfig)
```

## `registry.register_admin`

Signature: `registry.register_admin(model_class, config_instance)`.

Registers the admin class that `config_instance.get_admin_class()` returns with Django's admin site. A model that the admin site already holds is left alone, so an admin class that the portal registered with `@admin.register` is the one used. `registry.register` calls it.

## `registry.get_config`

Signature: `registry.get_config(model_class, config=None)`.

Returns the configuration instance for a model. A class is instantiated with the model, an instance is returned as it is, and `None` gives the registered configuration or, for a model that is not registered, a default one.

## `registry.get_for_model`

Signature: `registry.get_for_model(model_reference)`.

Returns the registered `ModelConfiguration` of a model. It never returns `None`.

Accepts a model class, or a string in the form `app_label.model_name` with the model name in lower case, such as `"rocks.rocksample"`.

| Raises | When |
|---|---|
| `NotRegisteredError` | The model is not registered. It is also a `KeyError`. |
| `ValueError` | The string has no `.` in it. |
| `LookupError` | The string names no model. |

## `registry.is_registered`

Signature: `registry.is_registered(model_reference)`.

Returns `True` when the model is registered and `False` when it is not. It also returns `False` for a string that is malformed or names no model. It accepts what `get_for_model` accepts.

## `registry.samples`

A property. A new list of the registered `Sample` model classes, in registration order. Each item is a model class, not a configuration.

## `registry.measurements`

A property. A new list of the registered `Measurement` model classes, in registration order.

## `registry.models`

A property. A new list of every registered model class, samples and measurements together.

## `registry.get_all_configs()`

Returns a new list of every registered `ModelConfiguration` instance, in registration order.

## Exceptions

All are in `fairdm.registry.exceptions`.

| Class | Subclasses | Attributes | Raised for |
|---|---|---|---|
| `RegistryError` | `Exception` | | The base of the four below. Catch it to catch any of them. |
| `ConfigurationError` | `RegistryError` | `model`, `config_class` | A configuration or a model that is refused. The message starts with the model's name. |
| `FieldValidationError` | `RegistryError` | `field_name`, `model`, `attribute`, `suggestion`, `reason` | A name in a field list that does not resolve, or a `search_fields` path that is not a text field. |
| `NotRegisteredError` | `RegistryError`, `KeyError` | `model` | `get_for_model` on a model that is not registered. |
| `DuplicateRegistrationError` | `RegistryError` | `model`, `original_location`, `new_location` | A model registered twice. |

## Template tag

`get_registry_info` is in the `fairdm` tag library. It returns the registry configuration of a model, a model instance or a queryset, and returns nothing when the model is not registered, where `registry.get_for_model` would raise.

```django
{% load fairdm %}
{% get_registry_info object as info %}
{% if info %}{{ info.get_verbose_name_plural }}{% endif %}
```

The other tags are on [Template tags](template-tags.md).
