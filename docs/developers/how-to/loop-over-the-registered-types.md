# How to loop over the registered types

The registry knows every sample and measurement type in the portal, so code that has to work for all of them can ask it instead of naming each one. You do this for a page that counts records by type, a report or a command that visits every type.

## Before you start

You need at least one registered type. See [How to register a sample or measurement type](register-a-sample-or-measurement-type.md).

## Steps

1. Import the registry.

   ```python
   from fairdm.registry import registry
   ```

2. Choose what to loop over.

   | To get | Use | Each item is |
   |---|---|---|
   | The sample types | `registry.samples` | A model class |
   | The measurement types | `registry.measurements` | A model class |
   | Both | `registry.models` | A model class |
   | Every configuration | `registry.get_all_configs()` | A `ModelConfiguration` |

3. Fetch the configuration of each model when you need it.

   ```python
   for model in registry.samples:
       config = registry.get_for_model(model)
       print(config.get_verbose_name_plural(), model.objects.count())
   ```

4. Use what the configuration offers. A configuration names its model as `config.model`, its listing as the URL name `<config.get_slug()>-list` and its generated components through accessors such as `get_table_class()`. This function returns one row for each type, with its name, its record count and the address of its listing.

   ```python
   from django.urls import reverse

   from fairdm.registry import registry


   def type_summary():
       rows = []
       for config in registry.get_all_configs():
           rows.append(
               {
                   "name": config.get_verbose_name_plural(),
                   "count": config.model.objects.count(),
                   "url": reverse(f"{config.get_slug()}-list"),
               }
           )
       return rows
   ```

5. In a template, ask about one model or record with the `get_registry_info` tag. It returns nothing for a model that is not registered.

   ```django
   {% load fairdm %}
   {% get_registry_info object as info %}
   {% if info %}{{ info.get_verbose_name_plural }}{% endif %}
   ```

## The result

`type_summary()` returns a list like this when the portal has two registered types:

```python
[
    {"name": "Plant Samples", "count": 12, "url": "/collections/samples/plantsample/"},
    {"name": "Leaf Area Measurements", "count": 40, "url": "/collections/measurements/leafareameasurement/"},
]
```

The lists come back in the order the types were registered, and each call builds a new list, so changing one changes nothing in the registry.

To check one model without a loop, call `registry.is_registered(model)`, which returns `False` where `get_for_model` would raise. The registry's methods and properties are on [The registry](../reference/registry.md), and the configuration's methods are on [Model configuration](../reference/model-configuration.md#methods).
