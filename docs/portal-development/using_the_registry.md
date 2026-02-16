# Using the Registry

Once you've registered your Sample and Measurement models with FairDM, you'll want to access and work with them programmatically. The FairDM registry provides a powerful API for discovering, inspecting, and iterating over registered models.

## Accessing the Registry

The global registry instance is available throughout your application:

```python
from fairdm.registry import registry
```

## Introspection API (New)

The FairDM registry provides convenient properties for programmatically discovering and iterating over registered models. This introspection API enables dynamic workflows and flexible data processing.

### Iterate Over All Registered Samples

```python
# Get all registered Sample model classes
for sample_model in registry.samples:
    print(f"Sample: {sample_model.__name__}")
    print(f"Module: {sample_model.__module__}")

    # Get configuration for this model
    config = registry.get_for_model(sample_model)
    print(f"Display Name: {config.display_name}")
    print(f"Fields: {config.fields}")
    print("---")
```

### Iterate Over All Registered Measurements

```python
# Get all registered Measurement model classes
for measurement_model in registry.measurements:
    print(f"Measurement: {measurement_model.__name__}")
    print(f"Module: {measurement_model.__module__}")

    # Access the model's configuration
    config = registry.get_for_model(measurement_model)
    print(f"Display Name: {config.display_name}")
    print(f"Description: {config.description}")
    print("---")
```

### Access All Registered Models

```python
# Get all registered models (Samples + Measurements combined)
all_models = list(registry.models)
print(f"Total registered models: {len(all_models)}")

for model_class in registry.models:
    config = registry.get_for_model(model_class)
    model_type = "Sample" if issubclass(model_class, Sample) else "Measurement"
    print(f"{model_type}: {model_class.__name__} - {config.display_name}")
```

### Dynamic Model Discovery

The introspection API is particularly useful for building dynamic UIs and processing workflows:

```python
from fairdm.core.models import Sample, Measurement

def process_all_samples():
    """Process all registered sample models dynamically."""
    for sample_model in registry.samples:
        # Get recent instances
        recent_samples = sample_model.objects.filter(
            created__gte=timezone.now() - timedelta(days=30)
        )

        print(f"Processing {len(recent_samples)} recent {sample_model.__name__} instances")

        # Access auto-generated components
        config = registry.get_for_model(sample_model)
        form_class = config.form
        table_class = config.table

        # Dynamic processing based on model type
        # ... your processing logic here

def create_measurement_reports():
    """Generate reports for all measurement types."""
    for measurement_model in registry.measurements:
        config = registry.get_for_model(measurement_model)

        # Generate report using model's table configuration
        report_data = measurement_model.objects.all()
        table = config.table(report_data)

        print(f"Generated report for {measurement_model.__name__}: {len(report_data)} records")
```

### Model Filtering and Selection

```python
# Filter models by specific criteria
def get_models_with_geo_fields():
    """Find all registered models that have geographic fields."""
    geo_models = []

    for model_class in registry.models:
        # Check if model has geographic fields
        for field in model_class._meta.get_fields():
            if field.name in ['latitude', 'longitude', 'location', 'coordinates']:
                geo_models.append(model_class)
                break

    return geo_models

# Get models by app
def get_models_by_app(app_label):
    """Get all registered models from a specific Django app."""
    app_models = []

    for model_class in registry.models:
        if model_class._meta.app_label == app_label:
            app_models.append(model_class)

    return app_models
```

### Integration with Django Admin

```python
from django.contrib import admin

# Dynamically register all Sample models with custom admin
for sample_model in registry.samples:
    config = registry.get_for_model(sample_model)
    admin_class = config.admin  # Auto-generated ModelAdmin

    # Customize admin registration
    if not admin.site.is_registered(sample_model):
        admin.site.register(sample_model, admin_class)
```

## Registry Overview

Get a quick overview of all registered models:

```python
# Print a formatted summary of all registered models
registry.summarise()
```

This will output something like:

```
============================================================
FairDM Registry Summary
============================================================
Total Registered Models: 4

📊 SAMPLES (2)
----------------------------------------
  • WaterSample (myproject)
    Display: Water Sample
    Verbose: water sample

  • SoilSample (myproject)
    Display: Soil Sample
    Verbose: soil sample

📊 MEASUREMENTS (2)
----------------------------------------
  • ChemicalAnalysis (myproject)
    Display: Chemical Analysis
    Verbose: chemical analysis

  • PhysicalMeasurement (myproject)
    Display: Physical Properties
    Verbose: physical measurement

============================================================
```

You can also get the summary data programmatically without printing:

```python
summary = registry.summarise(print_output=False)
print(f"Total models: {summary['total_registered']}")
print(f"Samples: {summary['samples']['count']}")
print(f"Measurements: {summary['measurements']['count']}")
```

## Accessing All Registered Models

```python
# Get all registered models
all_models = registry.all

# Each item is a dictionary with model metadata
for model_info in all_models:
    print(f"Model: {model_info['class'].__name__}")
    print(f"App: {model_info['app_label']}")
    print(f"Type: {model_info['type']}")  # 'sample' or 'measurement'
    print(f"Verbose Name: {model_info['verbose_name']}")
    print("---")
```

## Working with Samples

### Get All Registered Samples

```python
# Get all registered sample models
samples = registry.samples

for sample_info in samples:
    model_class = sample_info['class']
    config = sample_info['config']

    print(f"Sample Model: {model_class.__name__}")
    print(f"Display Name: {config.display_name}")
    print(f"Description: {config.get_description()}")
    print(f"List Fields: {config.get_list_fields()}")
    print("---")
```

### Iterate Over Sample Instances

```python
from django.apps import apps

# Get all sample model classes
for sample_info in registry.samples:
    model_class = sample_info['class']

    # Query all instances of this sample type
    instances = model_class.objects.all()

    print(f"\n{model_class.__name__} instances:")
    for instance in instances[:5]:  # Show first 5
        print(f"  - {instance.name} (ID: {instance.id})")
```

### Access Sample Configuration

```python
# Get configuration for a specific sample model

# Method 1: Using model class
from myproject.models import WaterSample

sample_config = registry.get_for_model(WaterSample)
if sample_config:
    config = sample_config['config']
    print(f"Display Name: {config.display_name}")
    print(f"List Fields: {config.get_list_fields()}")
    print(f"Filter Fields: {config.get_filter_fields()}")
    print(f"Private Fields: {config.private_fields}")

# Method 2: Using string reference (useful for dynamic lookups)
sample_config = registry.get_for_model("myproject.watersample")
if sample_config:
    config = sample_config['config']
    print(f"Model class: {sample_config['class']}")
```

## Working with Measurements

### Get All Registered Measurements

```python
# Get all registered measurement models
measurements = registry.measurements

for measurement_info in measurements:
    model_class = measurement_info['class']
    config = measurement_info['config']

    print(f"Measurement Model: {model_class.__name__}")
    print(f"Display Name: {config.display_name}")
    print(f"Description: {config.get_description()}")
    print("---")
```

## Filtering Models by App

If you have models from multiple Django apps, you can filter by app label:

```python
# Get models from a specific app
myapp_models = [
    model_info for model_info in registry.all
    if model_info['app_label'] == 'myproject'
]

for model_info in myapp_models:
    print(f"{model_info['type'].title()}: {model_info['class'].__name__}")
```

## Checking if a Model is Registered

```python
from myproject.models import WaterSample

# Check if a model is registered
if registry.get_for_model(WaterSample):
    print("WaterSample is registered")
else:
    print("WaterSample is not registered")
```

## Advanced Usage

### Accessing Auto-Generated Components

The registry automatically generates forms, tables, filters, and serializers for registered models. You can access these:

```python
from myproject.models import WaterSample

# Get the model registration info
model_info = registry.get_for_model(WaterSample)
config = model_info['config']

# Access auto-generated components
if hasattr(config, 'get_form_class'):
    form_class = config.get_form_class()
    print(f"Form class: {form_class}")

if hasattr(config, 'get_table_class'):
    table_class = config.get_table_class()
    print(f"Table class: {table_class}")
```

### Working with Field Configurations

```python
# Inspect field configurations for all models
for model_info in registry.all:
    config = model_info['config']
    model_name = model_info['class'].__name__

    print(f"\n{model_name} Field Configuration:")
    print(f"  List Fields: {config.get_list_fields()}")
    print(f"  Detail Fields: {config.get_detail_fields()}")
    print(f"  Filter Fields: {config.get_filter_fields()}")

    if hasattr(config, 'private_fields') and config.private_fields:
        print(f"  Private Fields: {config.private_fields}")
```

## Integration with Django Admin

If you're using Django admin, you can create a custom admin view that shows registry information:

```python
from django.contrib import admin
from django.http import HttpResponse
from fairdm.registry import registry

def registry_summary_view(request):
    """Admin view showing registry summary."""
    summary = registry.summarise(print_output=False)

    html = "<h1>FairDM Registry Summary</h1>"
    html += f"<p>Total Registered Models: {summary['total_registered']}</p>"

    html += f"<h2>Samples ({summary['samples']['count']})</h2><ul>"
    for model in summary['samples']['models']:
        html += f"<li><strong>{model['name']}</strong> - {model['display_name']}</li>"
    html += "</ul>"

    html += f"<h2>Measurements ({summary['measurements']['count']})</h2><ul>"
    for model in summary['measurements']['models']:
        html += f"<li><strong>{model['name']}</strong> - {model['display_name']}</li>"
    html += "</ul>"

    return HttpResponse(html)

# Add to your admin URLs
# admin.site.register_view('registry-summary/', registry_summary_view, name='Registry Summary')
```

## Measurement-Specific Registration

Measurements have additional configuration options beyond basic model registration. This section covers measurement-specific patterns and configurations.

### Base Measurement Configuration Fields

When registering measurements, you can configure these model-specific options:

```python
from fairdm.registry import register
from fairdm.registry.config import ModelConfiguration
from myapp.models import XRFMeasurement

@register
class XRFMeasurementConfig(ModelConfiguration):
    model = XRFMeasurement

    # Core Configuration
    display_name = "XRF Measurement"
    description = "X-ray fluorescence elemental analysis"

    # Field Sets
    fields = ["name", "sample", "dataset", "element", "concentration_ppm"]  # General use
    list_fields = ["name", "sample", "element", "concentration_ppm"]  # Admin list view
    detail_fields = ["name", "sample", "dataset", "element", "concentration_ppm", "detection_limit_ppm"]  # Forms
    filterset_fields = ["element", "dataset", "sample"]  # Filter sidebar

    # Admin Configuration
    search_fields = ["name", "element", "sample__name"]
    ordering = ["-created"]

    # Custom Components (Optional)
    form_class = None  # Use auto-generated form
    table_class = None  # Use auto-generated table
    filterset_class = None  # Use auto-generated filterset
    admin_class = None  # Use auto-generated admin
```

**Field Set Priority:**

1. If `list_fields` is specified, it's used for admin list view
2. If `list_fields` is not specified, falls back to `fields`
3. If neither is specified, uses model's first 5 fields

The same logic applies for `detail_fields` and `filterset_fields`.

### Polymorphic Admin Validation Rules

Measurements use polymorphic models, which have special validation rules in the admin:

**Rule 1: Child admin must inherit from `MeasurementChildAdmin`**

```python
from fairdm.core.measurement.admin import MeasurementChildAdmin

class XRFMeasurementAdmin(MeasurementChildAdmin):
    # Configuration for XRFMeasurement specifically
    list_display = ["name", "sample", "element", "concentration_ppm"]
```

**Rule 2: Don't register polymorphic parent directly**

```python
# ❌ BAD
from fairdm.core import Measurement
admin.site.register(Measurement, SomeAdmin)

# ✅ GOOD - Register specific types only
from myapp.models import XRFMeasurement
admin.site.register(XRFMeasurement, XRFMeasurementAdmin)
```

The parent `Measurement` model is registered automatically with `MeasurementParentAdmin` which provides the type selection interface.

**Rule 3: Fieldsets must only include fields that exist on the specific model**

```python
class XRFMeasurementAdmin(MeasurementChildAdmin):
    fieldsets = [
        ("Basic", {
            "fields": ["name", "sample", "dataset"]  # ✅ These exist on all measurements
        }),
        ("XRF Data", {
            "fields": ["element", "concentration_ppm"]  # ✅ These exist on XRFMeasurement
        }),
        # ❌ DON'T include fields from other measurement types
        # ("ICP-MS Data", {
        #     "fields": ["isotope"]  # ❌ This is ICP_MS_Measurement only
        # }),
    ]
```

**Rule 4: Use `base_form` for polymorphic types**

If you need custom validation that applies to all measurement types:

```python
from fairdm.core.measurement.forms import MeasurementFormMixin

class CustomMeasurementForm(MeasurementFormMixin, forms.ModelForm):
    def clean(self):
        # Custom validation for all measurements
        cleaned_data = super().clean()
        # Your validation here
        return cleaned_data

class XRFMeasurementAdmin(MeasurementChildAdmin):
    form = CustomMeasurementForm
```

### QuerySet Optimization for Measurements

When working with measurements, use the built-in QuerySet methods:

```python
# Get measurement configuration
from myapp.models import XRFMeasurement
config = registry.get_for_model(XRFMeasurement)

# Access the model class
model_class = config.model

# Use optimized querysets
measurements = model_class.objects.with_related()  # Loads sample, dataset
measurements = model_class.objects.with_metadata()  # Loads descriptions, dates, identifiers
measurements = model_class.objects.with_related().with_metadata()  # Both
```

### Measurement Registration Examples

**Example 1: Minimal Configuration**

```python
@register
class SimpleMeasurementConfig(ModelConfiguration):
    model = SimpleMeasurement
    fields = ["name", "sample", "dataset", "value", "unit"]
```

Auto-generates:

- Admin with list/detail views
- ModelForm for create/edit
- FilterSet for sidebar filtering
- Table for list display

**Example 2: Full Configuration**

```python
@register
class AdvancedMeasurementConfig(ModelConfiguration):
    model = AdvancedMeasurement

    # Display names
    display_name = "Advanced Measurement"
    description = "Complex measurement with multiple analysis steps"

    # Field configuration
    list_fields = ["name", "sample", "method", "result", "dataset"]
    detail_fields = ["name", "sample", "dataset", "method", "result", "uncertainty", "quality_flag"]
    filterset_fields = {
        "method": ["exact"],
        "quality_flag": ["exact"],
        "dataset": ["exact"],
        "created": ["gte", "lte"],
    }
    search_fields = ["name", "sample__name", "method"]

    # Admin configuration
    ordering = ["-created", "name"]
    list_filter = ["method", "quality_flag", "dataset"]

    # Custom components
    form_class = AdvancedMeasurementForm
    table_class = AdvancedMeasurementTable
    filterset_class = AdvancedMeasurementFilter
```

**Example 3: Measurement with Custom Admin**

```python
# First define custom admin
class SpectroscopyMeasurementAdmin(MeasurementChildAdmin):
    list_display = ["name", "sample", "wavelength_range", "resolution", "dataset"]

    fieldsets = [
        ("Identification", {
            "fields": ["name", "sample", "dataset"]
        }),
        ("Spectroscopy Parameters", {
            "fields": ["min_wavelength_nm", "max_wavelength_nm", "resolution", "instrument"]
        }),
        ("Data Files", {
            "fields": ["spectrum_file"],
            "classes": ["collapse"]
        }),
    ]

    def wavelength_range(self, obj):
        return f"{obj.min_wavelength_nm}-{obj.max_wavelength_nm} nm"
    wavelength_range.short_description = "Wavelength Range"

# Then register with custom admin reference
@register
class SpectroscopyMeasurementConfig(ModelConfiguration):
    model = SpectroscopyMeasurement
    fields = ["name", "sample", "dataset", "min_wavelength_nm", "max_wavelength_nm"]
    admin_class = SpectroscopyMeasurementAdmin  # Reference custom admin
```

### Troubleshooting

**Problem: Measurement not appearing in admin**

Check these common issues:

1. **Migrations not run**

   ```bash
   poetry run python manage.py makemigrations
   poetry run python manage.py migrate
   ```

2. **Model not registered**

   ```python
   # Verify registration
   from fairdm.registry import registry
   config = registry.get_for_model(YourMeasurement)
   if config is None:
       print("Not registered!")
   ```

3. **Import error in models.py**

   ```python
   # Make sure base import works
   from fairdm.core import Measurement  # Should not error
   ```

**Problem: Admin shows wrong fields for measurement type**

Cause: Polymorphic type confusion

Solution: Ensure correct admin base class:

```python
# ✅ Correct
class YourMeasurementAdmin(MeasurementChildAdmin):
    pass

# ❌ Wrong
class YourMeasurementAdmin(admin.ModelAdmin):  # Missing polymorphic handling
    pass
```

**Problem: Registration validation errors**

Example error: `"Field 'nonexistent_field' does not exist on model YourMeasurement"`

Solution: Check that all fields in your configuration exist on the model:

```python
@register
class YourMeasurementConfig(ModelConfiguration):
    model = YourMeasurement
    fields = ["name", "sample", "dataset", "your_field"]  # All must exist
```

**Problem: N+1 queries in admin list**

Cause: Not using optimized querysets

Solution: Override `get_queryset` in admin:

```python
class YourMeasurementAdmin(MeasurementChildAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).with_related()
```

**Problem: Type dropdown empty when creating measurement**

Cause: No measurement types registered

Solution: Check registry:

```python
from fairdm.registry import registry
print("Registered measurements:", len(list(registry.measurements)))
for model in registry.measurements:
    print(f"  - {model.__name__}")
```

If empty, ensure your `config.py` is being imported (check `apps.py`):

```python
# myapp/apps.py
class MyAppConfig(AppConfig):
    name = 'myapp'

    def ready(self):
        import myapp.config  # Trigger registration
```

1. **Cache Registry Queries**: If you're accessing the registry frequently, consider caching the results:

   ```python
   from django.core.cache import cache

   def get_cached_samples():
       samples = cache.get('registry_samples')
       if samples is None:
           samples = registry.samples
           cache.set('registry_samples', samples, 300)  # Cache for 5 minutes
       return samples
   ```

2. **Use Type Checking**: When iterating over models, check their type:

   ```python
   for model_info in registry.all:
       if model_info['type'] == 'sample':
           # Handle sample-specific logic
           pass
       elif model_info['type'] == 'measurement':
           # Handle measurement-specific logic
           pass
   ```

3. **Error Handling**: Always check if models exist before accessing them:

   ```python
   model_info = registry.get_for_model(MyModel)
   if model_info is not None:
       config = model_info['config']
       # Safe to use config
   ```

4. **Performance Considerations**: For large datasets, use select_related() and prefetch_related():

   ```python
   for measurement_info in registry.measurements:
       model_class = measurement_info['class']
       instances = model_class.objects.select_related('sample', 'dataset')
   ```

## REST API Support

**Current Status**: The FairDM registry auto-generates Django REST Framework serializers for registered models, but a full REST API with ViewSets and URL routing is not yet implemented.

**What's Available Now:**

The registry creates serializers for each registered model:

```python
from fairdm.registry import registry

# Access auto-generated serializer
config = registry.get_for_model(MyMeasurement)
serializer_class = config.serializer

# Use in your own views
from rest_framework.views import APIView
from rest_framework.response import Response

class MyMeasurementAPIView(APIView):
    def get(self, request):
        measurements = MyMeasurement.objects.all()
        serializer = serializer_class(measurements, many=True)
        return Response(serializer.data)
```

**Custom Serializers:**

You can provide custom serializers in your configuration:

```python
from rest_framework import serializers
from fairdm.registry import register
from fairdm.registry.config import ModelConfiguration

class MyMeasurementSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyMeasurement
        fields = ["id", "name", "sample", "dataset", "element", "concentration_ppm"]
        read_only_fields = ["id"]

@register
class MyMeasurementConfig(ModelConfiguration):
    model = MyMeasurement
    serializer_class = MyMeasurementSerializer  # Use custom serializer
```

**Planned Features:**

A full REST API module is planned for a future release, which will include:

- Auto-generated ModelViewSets for all registered models
- Automatic URL routing configuration
- Polymorphic API endpoints (measurements by type)
- Filtering, searching, and pagination support
- Nested serializers for relationships (sample → measurements, dataset → samples)
- Permission integration with object-level access control
- API documentation generation

For more information, see the [project roadmap](../../roadmap.md).

**Current Workaround:**

If you need a REST API now, you can create ViewSets manually:

```python
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

class MyMeasurementViewSet(viewsets.ModelViewSet):
    """API endpoint for MyMeasurement."""
    queryset = MyMeasurement.objects.with_related()
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        # Use registry-generated serializer
        config = registry.get_for_model(MyMeasurement)
        return config.serializer
```

Then add to your URLs:

```python
from rest_framework.routers import DefaultRouter
from myapp.api import MyMeasurementViewSet

router = DefaultRouter()
router.register(r'measurements/xrf', MyMeasurementViewSet, basename='xrf-measurement')

urlpatterns = [
    path('api/', include(router.urls)),
]
```

The registry system provides a powerful foundation for building data-driven applications that can adapt to your evolving data models. Use these patterns to create flexible, maintainable code that works with any combination of registered Sample and Measurement models.
