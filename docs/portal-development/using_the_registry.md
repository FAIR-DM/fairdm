# Using the Registry

Once you've registered your Sample and Measurement models with FairDM, you'll want to access and work with them programmatically. The FairDM registry provides a powerful API for discovering, inspecting, and iterating over registered models.

## Accessing the Registry

The global registry instance is available throughout your application:

```python
from fairdm.registry import registry
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

## Best Practices

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

The registry system provides a powerful foundation for building data-driven applications that can adapt to your evolving data models. Use these patterns to create flexible, maintainable code that works with any combination of registered Sample and Measurement models.