---
name: fairdm-registry
description: >-
  Registering custom Sample and Measurement models with the FairDM registry.
  Use when creating, modifying, or troubleshooting model registration configurations —
  covers the @register decorator, ModelConfiguration options, field resolution (parent fields,
  component-specific fields, custom class overrides), metadata (Authority, Citation, ModelMetadata),
  auto-generated components (form, table, filterset, serializer, resource, admin), registry
  introspection, SampleConfig/MeasurementConfig base classes, and common registration errors.
---

# FairDM Registry

Register custom `Sample` and `Measurement` subclasses so that FairDM auto-generates forms, tables, filters, serializers, import/export resources, and admin classes.

## Quick Start

```python
# myapp/models.py
from fairdm.core.models import Sample, Measurement
from fairdm.db import models

class RockSample(Sample):
    rock_type = models.CharField("Rock Type", max_length=100)
    weight_grams = models.FloatField("Weight (g)", null=True, blank=True)
    collection_date = models.DateField("Collection Date")

    class Meta:
        verbose_name = "Rock Sample"
        verbose_name_plural = "Rock Samples"


class XRFMeasurement(Measurement):
    element = models.CharField("Element", max_length=10)
    concentration_ppm = models.DecimalField("Concentration (ppm)", max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "XRF Measurement"
        verbose_name_plural = "XRF Measurements"
```

```python
# myapp/config.py
from fairdm.registry import ModelConfiguration, register
from .models import RockSample, XRFMeasurement

@register
class RockSampleConfig(ModelConfiguration):
    model = RockSample
    fields = ["name", "rock_type", "weight_grams", "collection_date"]

@register
class XRFMeasurementConfig(ModelConfiguration):
    model = XRFMeasurement
    fields = ["sample", "element", "concentration_ppm"]
```

> **App loading**: `config.py` must be imported at startup. Add `import myapp.config` in your app's `AppConfig.ready()` method.

## Rules

- Models **must** inherit from `fairdm.core.models.Sample` or `fairdm.core.models.Measurement`.
- Each model can only be registered **once** (`DuplicateRegistrationError`).
- The config class **must** set a `model` attribute.
- All field names in field lists **must** exist on the model (`FieldValidationError`).
- Never register the **base** `Sample` or `Measurement` classes — only polymorphic subclasses.
- Use `SampleConfig` or `MeasurementConfig` instead of `ModelConfiguration` for semantic clarity (they are identical in behavior).
- String model references use `"app_label.ModelName"` format (case-insensitive model name).
- Custom `admin_class` for Sample subclasses must inherit `SampleChildAdmin`; for Measurement subclasses must inherit `MeasurementAdmin`.

## Three-Tier Field Configuration

Resolution order (first match wins):

| Tier | What | Example |
|------|-------|---------|
| 3 - Custom class | Full override class provided | `table_class = MyTable` |
| 2 - Component fields | Component-specific field list | `table_fields = ["name", "type"]` |
| 1 - Parent fields | Shared field list for all components | `fields = ["name", "type"]` |
| 0 - Smart defaults | Auto-detected from model | *(all user-defined editable fields)* |

### Pattern 1 — Minimal (parent fields only)

```python
@register
class RockSampleConfig(ModelConfiguration):
    model = RockSample
    fields = ["name", "rock_type", "collection_date", "weight_grams"]
```

All components (form, table, filterset, etc.) use the same field list.

### Pattern 2 — Component-specific fields

```python
@register
class SoilSampleConfig(ModelConfiguration):
    model = SoilSample
    fields = ["name", "soil_type", "ph_level", "depth_cm"]  # fallback

    table_fields = ["name", "soil_type", "ph_level", "depth_cm"]
    form_fields  = ["name", "soil_type", "ph_level", "organic_matter_percent",
                    "texture", "moisture_content", "depth_cm"]
    filterset_fields = ["soil_type", "ph_level", "depth_cm"]
```

Available component-specific attributes:

- `table_fields` — django-tables2 columns
- `form_fields` — ModelForm inputs
- `filterset_fields` — django-filter filters
- `serializer_fields` — DRF serializer fields
- `resource_fields` — import/export resource fields
- `admin_list_display` — Django admin list columns

### Pattern 3 — Custom class override

```python
from .tables import WaterSampleTable
from .filters import WaterSampleFilter

@register
class WaterSampleConfig(ModelConfiguration):
    model = WaterSample
    fields = ["name", "water_source", "ph_level"]   # used by non-overridden components
    table_class = WaterSampleTable                    # bypasses field resolution for tables
    filterset_class = WaterSampleFilter               # bypasses field resolution for filters
```

Custom class attributes: `form_class`, `table_class`, `filterset_class`, `serializer_class`, `resource_class`, `admin_class`.

### Grouped fields with tuples

Use tuples inside field lists to hint at visual grouping (rendered side-by-side in forms):

```python
fields = [
    ("name", "status"),
    "char_field",
    ("isotope", "counts_per_second"),
]
```

## Metadata

```python
from fairdm.registry.config import Authority, Citation, ModelMetadata

@register
class RockSampleConfig(ModelConfiguration):
    model = RockSample
    metadata = ModelMetadata(
        description="Geological rock samples for mineral analysis",
        authority=Authority(
            name="Geological Survey Lab",
            short_name="GSL",
            website="https://geolab.example.com",
        ),
        citation=Citation(
            text="Smith et al. (2024). Rock Analysis Methods.",
            doi="https://doi.org/10.1234/example",
        ),
        keywords=["geology", "rocks", "minerals"],
        repository_url="https://github.com/example/rock-portal",
        maintainer="J. Smith",
        maintainer_email="smith@example.com",
    )
    fields = ["name", "rock_type", "collection_date"]
```

`display_name` and `description` on `ModelConfiguration` are shortcuts:

```python
@register
class RockSampleConfig(ModelConfiguration):
    model = RockSample
    display_name = "Rock Sample"
    description = "Geological rock specimens"
    fields = ["name", "rock_type"]
```

If `display_name` is omitted, it defaults to `model._meta.verbose_name.title()`.

## Accessing Auto-Generated Components

```python
from fairdm.registry import registry

config = registry.get_for_model(RockSample)
# or by string: config = registry.get_for_model("myapp.RockSample")

form_class       = config.form        # ModelForm with crispy-forms helper
table_class      = config.table       # django-tables2 Table with Bootstrap 5
filterset_class  = config.filterset   # django-filter FilterSet
serializer_class = config.serializer  # DRF ModelSerializer
resource_class   = config.resource    # django-import-export Resource
admin_class      = config.admin       # Django ModelAdmin

# Check custom vs auto-generated
config.has_custom_form()       # True if form_class was provided
config.has_custom_table()      # etc.
```

Components are lazily generated via `@cached_property` — created on first access.

## Registry Introspection

```python
from fairdm.registry import registry

registry.is_registered(RockSample)          # True / False
registry.is_registered("myapp.RockSample")  # string reference

registry.samples        # list of registered Sample model classes
registry.measurements   # list of registered Measurement model classes
registry.models         # all registered model classes

for config in registry.get_all_configs():
    print(config.model.__name__, config.get_display_name())
    print(config.get_slug())             # URL-safe model name
    print(config.get_verbose_name())     # singular verbose name
    print(config.get_verbose_name_plural())

registry.summarise()    # prints formatted summary to stdout
```

## SampleConfig / MeasurementConfig

Semantic aliases for `ModelConfiguration` — identical behavior, better readability:

```python
from fairdm.registry import SampleConfig, MeasurementConfig, register

@register
class RockSampleConfig(SampleConfig):
    model = RockSample
    fields = ["name", "rock_type"]

@register
class XRFConfig(MeasurementConfig):
    model = XRFMeasurement
    fields = ["sample", "element", "concentration_ppm"]
```

## BaseSampleConfiguration

Inherit from `fairdm.core.sample.config.BaseSampleConfiguration` to get pre-configured field defaults for common Sample fields:

```python
from fairdm.core.sample.config import BaseSampleConfiguration
from fairdm.registry import register

@register
class MySampleConfig(BaseSampleConfiguration):
    model = MySample
    # Inherits default fields, table_fields, form_fields, filterset_fields
    # Override only what you need:
    fields = ["name", "dataset", "local_id", "status", "my_custom_field"]
```

Pre-configured defaults in `BaseSampleConfiguration`:

- `fields`: name, dataset, local_id, status, location, image
- `table_fields`: name, dataset, local_id, status, added, modified
- `form_fields`: name, dataset, local_id, status, location, image
- `filterset_fields`: dataset, status, added

## Error Reference

| Exception | When raised |
|-----------|------------|
| `ConfigurationError` | Model not a Sample/Measurement subclass; missing `model` attribute; invalid admin inheritance |
| `FieldValidationError` | Field name doesn't exist on model (includes fuzzy-match suggestions) |
| `DuplicateRegistrationError` | Model already registered |
| `ComponentGenerationError` | Factory fails to create a component class |
| `FieldResolutionError` | Related field path (e.g. `project__title`) can't be resolved |

All inherit from `RegistryError`. Catch `RegistryError` for blanket handling.

## Checklist for New Model Registration

1. Define model inheriting from `Sample` or `Measurement` in `models.py`
2. Set `class Meta` with `verbose_name` / `verbose_name_plural`
3. Create `config.py` with `@register` decorated config class
4. Import `config.py` in `AppConfig.ready()`
5. Run `makemigrations` and `migrate`
6. Verify with `registry.summarise()` or Django system checks (`manage.py check`)

## Detailed API Reference

For complete attribute documentation, constructor signatures, and factory internals, see [references/api-reference.md](references/api-reference.md).
