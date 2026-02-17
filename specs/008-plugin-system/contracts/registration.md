# Contract: Plugin Registration

## `@plugins.register(*models)` Decorator

### Signature
```python
# From the PluginRegistry class
def register(*models: type[Model]) -> Callable[[type[Plugin | PluginGroup]], type[Plugin | PluginGroup]]

# Usage
from fairdm import plugins

@plugins.register(Model)
```

### Preconditions
- Each `model` must be a Django Model class
- The decorated class must be either a `Plugin` subclass or a `PluginGroup` subclass
- For `Plugin`: must be mixed with a Django CBV (e.g., `TemplateView`, `UpdateView`)
- For `PluginGroup`: `plugins` attribute must be a non-empty list of `Plugin` subclasses

### Postconditions
- The plugin/group is added to `registry._registry[model]` for each model
- The plugin's `model` attribute is set (for single-model registration) or left as `None` (for multi-model)
- The decorated class is returned unmodified (or with `model` set)

### Invariants
- No two plugins/groups registered for the same model may share the same `name`
- No two plugins/groups registered for the same model may produce conflicting URL paths
- A plugin that is part of a PluginGroup must not also be registered standalone for the same model

### Error Behavior
- Invalid class type → `TypeError` at decoration time
- Duplicate name → detected at system check time (`plugins.E002`)
- URL conflict → detected at system check time (`plugins.E003`)

### Examples

```python
from fairdm import plugins
from fairdm.contrib.plugins import Plugin, is_instance_of

# Base model with type filtering
@plugins.register(Sample)
class AnalysisPlugin(Plugin, TemplateView):
    check = is_instance_of(RockSample)  # Only for RockSample
    menu = {"label": "Analysis", "icon": "chart-bar", "order": 10}
    ...

# Multiple base models
@plugins.register(Project, Dataset, Sample, Measurement)
class ActivityPlugin(Plugin, TemplateView):
    menu = {"label": "Activity", "order": 40}
    ...

# PluginGroup with type filtering
@plugins.register(Sample)
class MetadataGroup(PluginGroup):
    check = is_instance_of(RockSample, WaterSample)
    plugins = [MetadataView, MetadataEdit]
    url_prefix = "metadata"
    menu = {"label": "Metadata", "icon": "database", "order": 20}
```

### Allowed Base Models

Plugins should only register on these base models:
- `Project`
- `Dataset`
- `Sample` (not `RockSample`, `WaterSample`, etc.)
- `Measurement` (not `XRFMeasurement`, `ImagingMeasurement`, etc.)
- `Contributor`

Use the `check` attribute to filter by polymorphic subclass.

---

## Visibility Helper: `is_instance_of(*model_classes)`

### Signature
```python
def is_instance_of(*model_classes: type[Model]) -> Callable[[HttpRequest, Model | None], bool]
```

### Preconditions
- `model_classes` must be Django Model classes

### Postconditions
- Returns a check function suitable for use as `Plugin.check` or `PluginGroup.check`
- The returned function accepts `(request, obj)` and returns `True` if `obj` is an instance of any of the specified model classes
- Returns `True` when `obj is None` (allows model-level access)

### Example
```python
from fairdm import plugins
from fairdm.contrib.plugins import is_instance_of

@plugins.register(Sample)
class AnalysisPlugin(Plugin, TemplateView):
    check = is_instance_of(RockSample)  # Only RockSample
    ...

@plugins.register(Sample)
class GeologyPlugin(Plugin, TemplateView):
    check = is_instance_of(RockSample, SoilSample)  # Multiple types
    ...
```

---

## `registry.get_plugins_for_model(model)`

### Signature
```python
def get_plugins_for_model(model: type[Model]) -> list[type[Plugin | PluginGroup]]
```

### Preconditions
- `model` must be a Django Model class

### Postconditions
- Returns all registered plugins and groups for the given model
- Order matches registration order
- For polymorphic models: includes plugins registered on parent classes

### Error Behavior
- Unregistered model → returns empty list `[]`

---

## `registry.is_registered(plugin, model)`

### Signature
```python
def is_registered(plugin: type[Plugin | PluginGroup], model: type[Model]) -> bool
```

### Postconditions
- Returns `True` if `plugin` is registered for `model`
- For PluginGroups: checks the group itself, not individual wrapped plugins
