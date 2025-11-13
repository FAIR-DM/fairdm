# Model Registration and Configuration

FairDM provides a powerful configuration system that allows you to register your Sample and Measurement subclasses with auto-generated forms, tables, filters, and serializers. This system follows Django conventions and enables you to create a fully functional data portal with minimal code.

## Overview

The registration system uses a simple `@register` decorator with declarative configuration classes (similar to Django admin) that automatically generates all the components needed to display and interact with your models in the FairDM interface:

- **Forms** for creating and editing records
- **Tables** for displaying lists of records  
- **Filters** for searching and filtering data
- **Resources** for import/export functionality
- **Serializers** for REST API endpoints (when DRF is available)

You can configure different fields for each component, or use general field lists that apply to all components. FairDM handles all the auto-generation!

## Quick Start

Here's how to register a simple Sample model:

```python
# myapp/models.py
from fairdm.core.sample.models import Sample
from django.db import models

class WaterSample(Sample):
    location = models.CharField(max_length=200)
    ph_level = models.FloatField()
    temperature = models.FloatField()
    collected_at = models.DateTimeField()
```

```python  
# myapp/fairdm_config.py
from fairdm.registry import ModelConfig, ModelMetadata, register
from .models import WaterSample

@register
class WaterSampleConfig(ModelConfig):
    model = WaterSample
    metadata = ModelMetadata(
        description="Water samples collected for chemical analysis"
    )
    # Simple approach - use same fields for all components
    fields = ["name", "location", "ph_level", "collected_at"]
```

That's it! FairDM will automatically generate forms, tables, filters, and API endpoints for your WaterSample model.

## Basic Registration

### Sample Registration

For Sample models, inherit from `ModelConfig` and use the `@register` decorator:

```python
from fairdm.registry import ModelConfig, ModelMetadata, Authority, register
from .models import SoilSample

@register
class SoilSampleConfig(ModelConfig):
    model = SoilSample
    metadata = ModelMetadata(
        description="Samples of soil collected for geological analysis",
        authority=Authority(
            name="Geological Survey Lab",
            short_name="GSL",
            website="https://geosurvey.example.com"
        )
    )
    
    # Component-specific field configuration
    table_fields = ["name", "location", "depth", "collected_at"]      # For table views
    form_fields = ["name", "location", "depth", "composition"]       # For forms
    filterset_fields = ["location", "depth", "collected_at"]         # For filtering
```

### Measurement Registration  

For Measurement models, also inherit from `ModelConfig`:

```python
from fairdm.registry import ModelConfig, ModelMetadata, register
from .models import TemperatureMeasurement

@register
class TemperatureMeasurementConfig(ModelConfig):
    model = TemperatureMeasurement
    metadata = ModelMetadata(
        description="Temperature readings from various samples"
    )
    
    # Simple approach - same fields for all components
    fields = ["name", "sample", "value", "unit", "measured_at"]
    
    # Or fine-grained control
    # table_fields = ["name", "sample", "value", "measured_at"]
    # form_fields = ["name", "sample", "value", "uncertainty", "unit", "method", "measured_at"]
    # filterset_fields = ["sample", "measured_at", "unit"]
```

## Configuration Options

### Required Settings

| Setting | Type | Description |
|---------|------|-------------|
| `model` | Model class | The Sample or Measurement subclass to register |

### Metadata Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `metadata` | `ModelMetadata` | Empty metadata | Structured metadata with description, authority, citation, etc. |

### Field Configuration

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `fields` | `list[str]` | `[]` | General fields used by all components when specific fields not provided |
| `form_fields` | `list[str]` | Uses `fields` | Fields for ModelForm generation (create/edit forms) |
| `table_fields` | `list[str]` | Uses `fields` | Fields for Table generation (list views) |
| `filterset_fields` | `list[str]` | Uses `fields` | Fields for FilterSet generation (search/filter) |
| `resource_fields` | `list[str]` | Uses `fields` | Fields for import/export Resource generation |
| `serializer_fields` | `list[str]` | Uses `fields` | Fields for DRF Serializer generation (when available) |
| `private_fields` | `list[str]` | `[]` | Fields to exclude from all auto-generation |

### Backward Compatibility

| Legacy Setting | Maps To | Description |
|---------|------|-------------|
| `list_fields` | `table_fields` | Backward compatibility for table field configuration |
| `detail_fields` | `form_fields` | Backward compatibility for form field configuration |
| `filter_fields` | `filterset_fields` | Backward compatibility for filter field configuration |

### Field Defaults

FairDM uses a hierarchical approach for field configuration:

1. **Component-specific fields** (e.g., `form_fields`, `table_fields`)
2. **General fields** (e.g., `fields`) when component-specific not provided
3. **Sensible defaults** when nothing is specified

Default behavior for each component:
- **`table_fields`**: Defaults to `["name", "created", "modified"]`
- **`form_fields`**: Uses `table_fields` as fallback
- **`filterset_fields`**: Defaults to `["created", "modified"]` 

```python
@register
class MinimalConfig(ModelConfig):
    model = MySample
    # Uses sensible defaults for all field lists
    # Tables will show: name, created, modified
    # Forms will include all model fields
    # Filters will have: created, modified
```

### Private Fields

Use `private_fields` to exclude sensitive or internal fields from all auto-generation:

```python
@register  
class SecureSampleConfig(ModelConfig):
    model = MySample
    fields = ["name", "location", "status", "data"]
    private_fields = ["internal_notes", "processing_id"]  # Excluded from all components
```

## Advanced Configuration

### Custom Components

You can provide custom classes to override auto-generation for specific components:

```python
from .forms import CustomWaterSampleForm
from .filters import CustomWaterSampleFilter

@register
class AdvancedWaterSampleConfig(ModelConfig):
    model = WaterSample
    metadata = ModelMetadata(
        description="Advanced water sample with custom components"
    )
    
    # Custom classes - auto-generation skipped for these components
    form_class = CustomWaterSampleForm
    filterset_class = CustomWaterSampleFilter
    
    # Field configs for auto-generated components
    table_fields = ["name", "location", "ph_level"] 
    resource_fields = ["name", "location", "ph_level", "temperature"]
```

### Fine-Grained Field Control

Use component-specific field attributes for precise control:

```python
@register
class FineTunedConfig(ModelConfig):
    model = WaterSample
    metadata = ModelMetadata(description="Fine-tuned water sample configuration")
    
    # Different fields for different purposes
    table_fields = ["name", "location", "status"]              # Minimal table view
    form_fields = ["name", "description", "location",          # Comprehensive forms
                  "ph_level", "temperature", "collected_at"]
    filterset_fields = ["location", "status", "collected_at"]  # Targeted filtering  
    resource_fields = ["name", "location", "ph_level",         # Export/import data
                      "temperature", "volume", "collected_at"]
    
    # Still use custom classes when needed
    table_class = CustomTable
    filterset_class = CustomFilter
```

### Flexible Configuration Patterns

The configuration system supports multiple patterns - use what works best for your needs:

**Pattern 1: Simple (same fields everywhere)**
```python
@register
class SimpleConfig(ModelConfig):
    model = WaterSample
    fields = ["name", "location", "ph_level"]  # Used for all components
```

**Pattern 2: Component-specific fields**  
```python
@register
class TargetedConfig(ModelConfig):
    model = WaterSample
    table_fields = ["name", "status"]
    form_fields = ["name", "location", "ph_level", "temperature"]
    filterset_fields = ["location", "status"]
```

**Pattern 3: Mixed (custom classes + field configs)**
```python
@register  
class MixedConfig(ModelConfig):
    model = WaterSample
    form_class = CustomForm          # Custom form
    table_class = CustomTable        # Custom table
    filterset_fields = ["location"]  # Auto-generated filter
    resource_fields = ["name", "data"] # Auto-generated resource
```

## File Organization

### Recommended Structure

Create a dedicated configuration file in your app:

```
myapp/
├── __init__.py
├── models.py          # Your Sample/Measurement models
├── fairdm_config.py   # FairDM registrations (recommended)
├── forms.py           # Custom forms (optional)
├── filters.py         # Custom filters (optional)
└── tables.py          # Custom tables (optional)
```

### Loading Configurations

Ensure your configurations are loaded by importing them in your app's `__init__.py` or `apps.py`:

```python
# myapp/apps.py
from django.apps import AppConfig

class MyAppConfig(AppConfig):
    name = 'myapp'
    
    def ready(self):
        # Import configurations to trigger registration
        from . import fairdm_config
```

Or in your `__init__.py`:

```python
# myapp/__init__.py
default_app_config = 'myapp.apps.MyAppConfig'
```

## Validation and Error Handling

### Model Validation

FairDM only allows Sample and Measurement subclasses to be registered:

```python
# ✅ Valid - Sample subclass
@fairdm.register
class WaterSampleConfig(fairdm.SampleConfig):
    model = WaterSample  # Inherits from Sample

# ✅ Valid - Measurement subclass  
@fairdm.register
class TemperatureConfig(fairdm.MeasurementConfig):
    model = TemperatureMeasurement  # Inherits from Measurement

# ❌ Invalid - raises TypeError
@fairdm.register  
class InvalidConfig(fairdm.SampleConfig):
    model = Person  # Person is not a Sample or Measurement subclass
```

### Configuration Validation

The `model` attribute is required:

```python
# ❌ Invalid - raises ValueError
@fairdm.register
class IncompleteConfig(fairdm.SampleConfig):
    display_name = "Missing Model"
    # Missing: model = SomeModel
```

### Field Validation

FairDM validates that specified fields exist on the model:

```python
@fairdm.register
class WaterSampleConfig(fairdm.SampleConfig):
    model = WaterSample
    list_fields = ["name", "invalid_field"]  # ❌ Will raise error if invalid_field doesn't exist
```

## Migration from Legacy System

If you're upgrading from the old inner `FairDM` class pattern:

### Before (Legacy)
```python
class MyMeasurement(Measurement):
    value = models.FloatField()
    
    class FairDM:
        description = "My measurement"
        filterset_class = "myapp.filters.MyFilter"
        table_class = "myapp.tables.MyTable"
```

### After (New System)  
```python
class MyMeasurement(Measurement):
    value = models.FloatField()

# In fairdm_config.py
from fairdm.registry import ModelConfig, ModelMetadata, register

@register
class MyMeasurementConfig(ModelConfig):
    model = MyMeasurement
    metadata = ModelMetadata(description="My measurement")
    
    # Use same custom classes
    filterset_class = MyFilter
    table_class = MyTable
    
    # Configure fields for auto-generated components
    fields = ["name", "value", "sample", "created"]
```

## Best Practices

### 1. Start Simple
Begin with minimal configuration and add complexity as needed:

```python
# Start with this
@fairdm.register
class MyConfig(fairdm.SampleConfig):
    model = MySample
    list_fields = ["name", "location"]

# Add more as your needs grow
# detail_fields = [...]
# filter_fields = [...]  
# form_options = {...}
```

### 2. Use Structured Metadata
Include comprehensive metadata for better data management:

```python
@register
class WellDocumentedConfig(ModelConfig):
    model = MySample
    metadata = ModelMetadata(
        description="Detailed description of the sample type",
        authority=Authority(
            name="Research Institution", 
            website="https://institution.edu"
        ),
        citation=Citation(
            text="Institution (2025). Sample Collection Protocol.",
            doi="10.1000/xyz123"
        ),
        keywords=["geology", "analysis", "field-work"]
    )
```

### 3. Progressive Enhancement
Start simple, add complexity only where needed:

```python
@register
class ProgressiveConfig(ModelConfig):
    model = MySample
    
    # Start with simple field configuration
    fields = ["name", "location", "status"]
    
    # Add component-specific fields as needed
    table_fields = ["name", "status"]  # Minimal table
    form_fields = ["name", "location", "status", "description"]  # Detailed forms
    
    # Use custom classes only when necessary
    form_class = CustomForm  # When auto-generation isn't enough
```

### 4. Consistent Naming
Use descriptive configuration class names:

```python
# Good
class WaterSampleConfig(ModelConfig):
class TemperatureMeasurementConfig(ModelConfig):
class SoilAnalysisConfig(ModelConfig):

# Avoid
class Config1(ModelConfig):
class MyConfig(ModelConfig):
class SampleConfig(ModelConfig):  # Too generic
```

### 5. Keep Configurations Focused
One configuration per model, keep them simple and focused:

```python
# Good - focused and clear
@register
class WaterSampleConfig(ModelConfig):
    model = WaterSample
    metadata = ModelMetadata(description="Water sample analysis")
    fields = ["name", "location", "ph_level"]

# Avoid - overly complex configurations
@register  
class OverlyComplexConfig(ModelConfig):
    model = ComplexSample
    # ... 50 lines of field configurations for every component
    # Consider splitting into multiple models instead
```

## Accessing Generated Components

You can access the generated components programmatically:

```python
from fairdm.registry import registry

# Get registered model information
item = registry.get_for_model(WaterSample)

# Access the configuration
config = item["config"]

# Get generated classes
form_class = config.get_form_class()
filterset_class = config.get_filterset_class()
table_class = config.get_table_class()  
resource_class = config.get_resource_class()
serializer_class = config.get_serializer_class()  # if DRF available
```

## Troubleshooting

### Common Issues

**Registration not working?**
- Ensure your configurations are imported in `apps.py` or `__init__.py`
- Check that your model inherits from Sample or Measurement
- Verify the `model` attribute is set correctly

**Fields not showing up?**  
- Check that field names match your model's fields exactly
- Verify fields aren't listed in `private_fields`
- Ensure fields exist on the model

**Auto-generation not working?**
- Make sure you haven't provided a custom class for that component
- Check that the field lists are properly defined
- Verify there are no import errors in your configuration file

**Type errors during registration?**
- Ensure your model inherits from Sample or Measurement, not a different base class
- Check that you're inheriting from `ModelConfig` and using the `@register` decorator
- Verify your imports are correct: `from fairdm.registry import ModelConfig, register`

### Debug Tips

Enable debug logging to see what's happening during registration:

```python
import logging
logging.getLogger('fairdm.registry').setLevel(logging.DEBUG)
```

Check what's been registered:

```python
from fairdm.registry import registry

# See all registered models
for item in registry.all:
    print(f"Model: {item['class'].__name__}")
    print(f"Config: {item['config'].__class__.__name__}")
    print(f"Fields: {item['config'].get_list_fields()}")
```

## Complete Example

Here's a comprehensive example showing a complete Sample model with controlled vocabularies and registration:

```python
# myapp/models.py
from fairdm.core.sample.models import Sample
from fairdm.db import models
from research_vocabs.fields import ConceptField

class WaterSample(Sample):
    """A sample of water collected for analysis."""
    
    # Standard Django fields
    location = models.CharField(max_length=200, help_text="Collection location")
    ph_level = models.FloatField(help_text="pH level of the sample")
    temperature = models.FloatField(help_text="Temperature in Celsius")
    collected_at = models.DateTimeField(help_text="When the sample was collected")
    
    # FairDM special fields
    sample_type = ConceptField(
        vocabulary="water_sample_types",
        help_text="Type of water sample"
    )
    
    # Quantity field with units
    volume = models.QuantityField(
        help_text="Volume of sample collected"
    )
    
    class Meta:
        verbose_name = "Water Sample"
        verbose_name_plural = "Water Samples"
        ordering = ['-collected_at']
```

```python
# myapp/fairdm_config.py
from fairdm.registry import (
    Authority, Citation, ModelConfig, ModelMetadata, register
)
from .models import WaterSample

@register
class WaterSampleConfig(ModelConfig):
    """Configuration for water sample registration."""
    
    model = WaterSample
    metadata = ModelMetadata(
        description="Water samples collected from various locations for chemical and physical analysis",
        authority=Authority(
            name="Environmental Research Lab",
            short_name="ERL", 
            website="https://env-lab.university.edu"
        ),
        citation=Citation(
            text="Environmental Research Lab (2025). Water Quality Assessment Protocol v2.1",
            doi="10.1000/water.protocol.v2.1"
        ),
        repository_url="https://github.com/env-lab/water-samples",
        keywords=["water", "environmental", "chemistry", "analysis"]
    )
    
    # Component-specific field configuration
    table_fields = [
        "name", 
        "location", 
        "sample_type",
        "ph_level", 
        "collected_at"
    ]
    
    form_fields = [
        "name",
        "description", 
        "location",
        "sample_type",
        "ph_level",
        "temperature", 
        "volume",
        "collected_at"
    ]
    
    filterset_fields = [
        "location",
        "sample_type", 
        "collected_at",
        "ph_level"
    ]
    
    resource_fields = [
        "name",
        "location",
        "sample_type",
        "ph_level",
        "temperature",
        "volume", 
        "collected_at"
    ]
    
    # Exclude internal fields from all components
    private_fields = ["internal_processing_id"]
```

```python
# myapp/apps.py
from django.apps import AppConfig

class MyAppConfig(AppConfig):
    name = 'myapp'
    default_auto_field = 'django.db.models.BigAutoField'
    
    def ready(self):
        # Import registrations to trigger them
        from . import fairdm_config
```

This example demonstrates:
- A complete Sample model with various field types
- Integration with controlled vocabularies via `ConceptField`
- Special fields like `QuantityField` for scientific data
- Comprehensive registration configuration
- Auto-generation of all interface components
- Proper Django app configuration

## Related Documentation

- [Defining Models](defining_models.md) - How to create Sample and Measurement models
- [Special Fields](special_fields.md) - Using FairDM's research-specific fields
- [Controlled Vocabularies](controlled_vocabularies.md) - Adding semantic meaning to your data
