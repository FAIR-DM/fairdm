# FairDM Registry API Reference

Detailed attribute and method documentation for the registry system.

## Table of Contents

- [ModelConfiguration](#modelconfiguration)
- [SampleConfig / MeasurementConfig](#sampleconfig--measurementconfig)
- [BaseSampleConfiguration](#basesampleconfiguration)
- [Metadata Dataclasses](#metadata-dataclasses)
- [FairDMRegistry](#fairdmregistry)
- [register decorator](#register-decorator)
- [FieldResolver](#fieldresolver)
- [Component Factories](#component-factories)
- [Exceptions](#exceptions)

---

## ModelConfiguration

`fairdm.registry.config.ModelConfiguration` — dataclass

### Required Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `model` | `type[Model]` | Django model class. Must be a `Sample` or `Measurement` subclass. |

### Parent Field Configuration (Tier 1)

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `fields` | `list[str]` | `[]` | Shared field list for all components. Supports related paths (`project__title`), tuples for grouping. Empty = smart defaults. |
| `exclude` | `list[str]` | `[]` | Fields excluded from all components. Auto-excluded: `id`, `polymorphic_ctype`, `*_ptr`, `auto_now` fields, `editable=False`. |

### Component-Specific Fields (Tier 2)

All default to `None` (fall back to `fields`).

| Attribute | Type | Description |
|-----------|------|-------------|
| `table_fields` | `list[str] \| None` | Columns for django-tables2 Table |
| `form_fields` | `list[str] \| None` | Inputs for Django ModelForm |
| `filterset_fields` | `list[str] \| None` | Filters for django-filter FilterSet |
| `serializer_fields` | `list[str] \| None` | Fields for DRF ModelSerializer |
| `resource_fields` | `list[str] \| None` | Fields for django-import-export Resource |
| `admin_list_display` | `list[str] \| None` | Columns for Django Admin list view |

### Custom Class Overrides (Tier 3)

All default to `None` (auto-generate).

| Attribute | Type | Description |
|-----------|------|-------------|
| `form_class` | `type[ModelForm] \| None` | Custom ModelForm class |
| `table_class` | `type[Table] \| None` | Custom django-tables2 Table |
| `filterset_class` | `type[FilterSet] \| None` | Custom django-filter FilterSet |
| `serializer_class` | `type[ModelSerializer] \| None` | Custom DRF serializer |
| `resource_class` | `type[ModelResource] \| None` | Custom import/export Resource |
| `admin_class` | `type[ModelAdmin] \| str \| None` | Custom admin class (or dotted import path) |

### Display Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `display_name` | `str` | `""` | Human-readable name. Defaults to `model._meta.verbose_name.title()`. |
| `description` | `str` | `""` | Model description for docs/help text. |
| `metadata` | `ModelMetadata \| None` | `None` | Structured FAIR metadata (see below). |

### Component Properties (cached_property)

Lazily generated on first access. Return the custom class if provided, otherwise auto-generate.

| Property | Returns | Description |
|----------|---------|-------------|
| `form` | `type[ModelForm]` | Form with crispy-forms FormHelper and smart widgets |
| `table` | `type[Table]` | Table with Bootstrap 5 template and smart columns |
| `filterset` | `type[FilterSet]` | FilterSet with type-appropriate filters |
| `serializer` | `type[ModelSerializer]` | Serializer with nested related objects |
| `resource` | `type[ModelResource]` | Import/export resource with natural keys |
| `admin` | `type[ModelAdmin]` | Admin class with list_display |

### Methods

```python
# Display helpers
config.get_display_name() -> str
config.get_description() -> str
config.get_slug() -> str                  # model._meta.model_name
config.get_verbose_name() -> str
config.get_verbose_name_plural() -> str

# Custom class checks
config.has_custom_form() -> bool
config.has_custom_table() -> bool
config.has_custom_filterset() -> bool
config.has_custom_serializer() -> bool
config.has_custom_resource() -> bool
config.has_custom_admin() -> bool

# Cache management
config.clear_cache()  # force re-generation of all components

# Smart defaults (classmethod)
ModelConfiguration.get_default_fields(model) -> list[str]
```

`get_default_fields(model)` excludes: `id`, `polymorphic_ctype`, `*_ptr` fields, `auto_now`/`auto_now_add` fields, non-editable fields, reverse relations, and M2M through non-auto models.

---

## SampleConfig / MeasurementConfig

`fairdm.registry.config.SampleConfig` and `MeasurementConfig`

Identical to `ModelConfiguration`. Use for semantic clarity:

```python
from fairdm.registry import SampleConfig, MeasurementConfig
```

---

## BaseSampleConfiguration

`fairdm.core.sample.config.BaseSampleConfiguration`

Pre-configured `ModelConfiguration` subclass with field defaults for common Sample fields. Set `model = None` — subclass must provide it.

Default field sets:

```python
fields           = ["name", "dataset", "local_id", "status", "location", "image"]
table_fields     = ["name", "dataset", "local_id", "status", "added", "modified"]
form_fields      = ["name", "dataset", "local_id", "status", "location", "image"]
filterset_fields = ["dataset", "status", "added"]
serializer_fields = ["id", "uuid", "name", "dataset", "local_id", "status",
                     "location", "added", "modified"]
display_name     = "Sample"
description      = "Physical or digital specimen/artifact for research"
```

---

## Metadata Dataclasses

### Authority

`fairdm.registry.config.Authority` — frozen dataclass

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | *(required)* | Full authority name |
| `short_name` | `str` | `""` | Abbreviated name |
| `website` | `str` | `""` | Authority website URL |

### Citation

`fairdm.registry.config.Citation` — frozen dataclass

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `text` | `str` | `""` | Full citation text |
| `doi` | `str` | `""` | DOI URL |

### ModelMetadata

`fairdm.registry.config.ModelMetadata` — dataclass

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `description` | `str` | `""` | Model description |
| `authority` | `Authority \| None` | `None` | Responsible organization |
| `keywords` | `list[str]` | `[]` | Discoverability keywords |
| `repository_url` | `str` | `""` | Source code URL |
| `citation` | `Citation \| None` | `None` | How to cite |
| `maintainer` | `str` | `""` | Current maintainer |
| `maintainer_email` | `str` | `""` | Maintainer email |

---

## FairDMRegistry

`fairdm.registry.registry.FairDMRegistry`

Global instance: `from fairdm.registry import registry`

### Methods

```python
registry.register(model_class, config=None)   # register a model
registry.get_for_model(model_or_string) -> ModelConfiguration
registry.is_registered(model_or_string) -> bool
registry.get_all_configs() -> list[ModelConfiguration]
registry.summarise(print_output=True) -> dict
```

### Properties

```python
registry.samples       -> list[type[Sample]]
registry.measurements  -> list[type[Measurement]]
registry.models        -> list[type[Model]]
```

### String model references

Format: `"app_label.ModelName"` (model name is case-insensitive, passed to `apps.get_model`).

```python
config = registry.get_for_model("myapp.rocksample")
```

Raises `ValueError` if format is not `"X.Y"`, `LookupError` if model not found, `KeyError` if not registered.

---

## register decorator

`fairdm.registry.registry.register`

```python
from fairdm.registry import register

@register
class MyConfig(ModelConfiguration):
    model = MyModel
    fields = [...]
```

- Reads `model` from the config class.
- Instantiates the config class.
- Calls `registry.register(model, config_instance)`.
- Returns the config class unchanged.
- Raises `ValueError` if `model` attribute is missing.

---

## FieldResolver

`fairdm.registry.field_resolver.FieldResolver`

Internal utility used by factories. Implements the three-tier resolution.

```python
resolver = FieldResolver(config)
fields = resolver.resolve_fields_for_component("table")  # "form", "filterset", etc.
resolver.validate_field_exists("name")  # bool
resolver.validate_field_path("project__title")  # bool
resolver.get_field_type("name")  # type | None
```

---

## Component Factories

Located in `fairdm.registry.factories`. Called internally by `ModelConfiguration` cached properties.

| Factory | Output | Key features |
|---------|--------|--------------|
| `FormFactory` | `ModelForm` | Smart widgets (DateInput, Textarea, EmailInput), crispy-forms FormHelper |
| `TableFactory` | `Table` | Bootstrap 5 template, smart columns, large text filtering |
| `FilterFactory` | `FilterSet` | Type-appropriate filters (CharFilter, DateFromToRangeFilter, etc.) |
| `SerializerFactory` | `ModelSerializer` | Nested serializers for FK relations |
| `ResourceFactory` | `ModelResource` | Natural key support for import/export |
| `AdminFactory` | `ModelAdmin` | Polymorphic-aware admin with list_display |

All inherit from `ComponentFactory(model, fields)` with a `.generate()` method.

---

## Exceptions

All in `fairdm.registry.exceptions`. Inherit from `RegistryError`.

### RegistryError

Base class. Catch this for blanket handling.

### ConfigurationError

```python
ConfigurationError(message, model=None, config_class=None)
```

Invalid config: wrong base class, missing model, bad admin inheritance.

### FieldValidationError

```python
FieldValidationError(field_name, model, suggestion=None, valid_fields=None)
```

Field doesn't exist on model. Includes fuzzy-match suggestions.

### DuplicateRegistrationError

```python
DuplicateRegistrationError(model, original_location, new_location=None)
```

Model already registered.

### ComponentGenerationError

```python
ComponentGenerationError(component_type, model, original_exception)
```

Factory failed. Wraps the original exception with context.

### FieldResolutionError

```python
FieldResolutionError(field_path, model, failed_at)
```

Related field path can't be resolved (e.g., `project__nonexistent`).

### ComponentWarning

`UserWarning` subclass for non-fatal issues during generation (e.g., JSONField excluded from table).
