# Quickstart Guide - FairDM Registry System

**Feature**: 002-fairdm-registry
**Audience**: Portal developers using FairDM framework
**Date**: 2026-01-12

This guide provides practical examples of using the FairDM Registry System to auto-generate components for Sample and Measurement models.

---

## 1. Basic Registration

### 1.1 Simple Configuration (All Components Share Fields)

The simplest registration uses only the `fields` attribute. All components (forms, tables, filters, etc.) will auto-generate using these fields.

```python
# myapp/registry.py
from fairdm.registry import registry, ModelConfiguration
from .models import RockSample


@registry.register
class RockSampleConfig(ModelConfiguration):
    model = RockSample
    fields = ['name', 'location', 'date_collected', 'contributor']
    display_name = "Rock Sample"
    description = "Geological rock samples collected in the field"
```

**Result**: All components use `['name', 'location', 'date_collected', 'contributor']`

### 1.2 Smart Defaults (Empty Fields)

If `fields` is empty or omitted, smart defaults are generated automatically:

```python
@registry.register
class RockSampleConfig(ModelConfiguration):
    model = RockSample
    # fields not specified - smart defaults used
```

**Smart defaults include**:

- All user-defined model fields
- Excludes technical fields: `id`, `polymorphic_ctype`, `*_ptr`
- Excludes auto-timestamp fields: `created`, `modified`
- Excludes non-editable fields

---

## 2. Component-Specific Field Lists

### 2.1 Different Fields Per Component

Use component-specific attributes to customize field lists for each component type:

```python
@registry.register
class RockSampleConfig(ModelConfiguration):
    model = RockSample

    # Default fields (fallback)
    fields = ['name', 'location', 'date_collected']

    # Table shows contributor column
    table_fields = ['name', 'location', 'date_collected', 'contributor']

    # Form includes description field
    form_fields = ['name', 'description', 'location', 'date_collected']

    # Filters for searchable fields only
    filterset_fields = ['name', 'location', 'contributor']
```

**Result**:

- **Table**: Shows 4 columns (name, location, date_collected, contributor)
- **Form**: Has 4 input fields (name, description, location, date_collected)
- **Filters**: Provides 3 filters (name, location, contributor)
- **Serializer/Resource/Admin**: Use default `fields` (3 fields)

### 2.2 Related Field Paths

Include related model fields using double-underscore notation:

```python
@registry.register
class MeasurementConfig(ModelConfiguration):
    model = XRFMeasurement

    # Include related fields in table
    table_fields = [
        'name',
        'sample__name',         # Related sample name
        'sample__location',      # Related sample location
        'date_measured',
        'operator__name',        # Related user name
    ]

    # Form can't edit related fields - use local fields only
    form_fields = ['name', 'date_measured', 'operator']
```

**Important**: Forms cannot include double-underscore paths (cannot edit related fields). Tables and filters CAN include related paths.

---

## 3. Custom Component Classes

### 3.1 Override with Custom Form

Provide custom classes for full control. Custom classes completely replace auto-generation:

```python
# myapp/forms.py
from django import forms
from .models import RockSample


class RockSampleForm(forms.ModelForm):
    """Custom form with validation logic."""

    class Meta:
        model = RockSample
        fields = ['name', 'description', 'location', 'date_collected']

    def clean_name(self):
        """Ensure name is uppercase."""
        name = self.cleaned_data['name']
        return name.upper()


# myapp/registry.py
from fairdm.registry import registry, ModelConfiguration
from .models import RockSample
from .forms import RockSampleForm


@registry.register
class RockSampleConfig(ModelConfiguration):
    model = RockSample
    fields = ['name', 'location', 'date_collected']  # Default for other components

    form_class = RockSampleForm  # Custom form (ignores all field configuration)
```

**Result**:

- **Form**: Uses custom `RockSampleForm` (ignores `fields` and `form_fields`)
- **Table/Filters/Serializer/etc.**: Auto-generate from `fields` attribute

### 3.2 Override with Custom Table

```python
# myapp/tables.py
import django_tables2 as tables
from .models import RockSample


class RockSampleTable(tables.Table):
    """Custom table with special columns."""

    # Add action buttons column
    actions = tables.TemplateColumn(
        template_name='tables/action_buttons.html',
        orderable=False,
        verbose_name='Actions'
    )

    class Meta:
        model = RockSample
        fields = ['name', 'location', 'contributor', 'actions']


# myapp/registry.py
@registry.register
class RockSampleConfig(ModelConfiguration):
    model = RockSample
    fields = ['name', 'location', 'date_collected']

    table_class = RockSampleTable  # Custom table
```

### 3.3 Mix Custom and Auto-Generated

You can provide custom classes for some components while auto-generating others:

```python
@registry.register
class RockSampleConfig(ModelConfiguration):
    model = RockSample
    fields = ['name', 'location', 'date_collected', 'contributor']

    form_class = RockSampleForm        # Custom form
    table_class = RockSampleTable      # Custom table
    # filterset auto-generated from fields
    # serializer auto-generated from fields
    # resource auto-generated from fields
    # admin auto-generated from fields
```

---

## 4. Excluding Fields

### 4.1 Exclude from All Components

Use `exclude` to remove fields from all auto-generated components:

```python
@registry.register
class RockSampleConfig(ModelConfiguration):
    model = RockSample
    # fields not specified - smart defaults used

    # Remove these from ALL components
    exclude = ['internal_notes', 'legacy_id', 'sync_status']
```

**Result**: `internal_notes`, `legacy_id`, and `sync_status` excluded from forms, tables, filters, serializers, etc.

### 4.2 Component-Specific Exclusion

To exclude from one component only, specify the component's field list explicitly:

```python
@registry.register
class RockSampleConfig(ModelConfiguration):
    model = RockSample
    fields = ['name', 'description', 'location', 'date_collected', 'notes']

    # Exclude 'notes' from table only (large text field)
    table_fields = ['name', 'location', 'date_collected']
```

---

## 5. Using Generated Components

### 5.1 In Views

```python
# myapp/views.py
from django.views.generic import ListView, CreateView
from fairdm.registry import registry
from .models import RockSample


class RockSampleListView(ListView):
    """List view using auto-generated table and filters."""
    model = RockSample
    template_name = 'samples/list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get configuration from registry
        config = registry.get_for_model(RockSample)

        # Get auto-generated components (using cached properties)
        TableClass = config.table
        FilterSetClass = config.filterset

        # Apply filtering
        queryset = self.get_queryset()
        filterset = FilterSetClass(self.request.GET, queryset=queryset)

        # Create table
        table = TableClass(filterset.qs)

        context['table'] = table
        context['filterset'] = filterset
        return context


class RockSampleCreateView(CreateView):
    """Create view using auto-generated form."""
    model = RockSample
    template_name = 'samples/create.html'

    def get_form_class(self):
        config = registry.get_for_model(RockSample)
        return config.form
```

### 5.2 In Templates

```django
{# templates/samples/list.html #}
{% load render_table from django_tables2 %}

<div class="container">
    <h1>{{ config.display_name }}s</h1>
    <p>{{ config.description }}</p>

    {# Render filters #}
    <form method="get">
        {{ filterset.form.as_p }}
        <button type="submit" class="btn btn-primary">Filter</button>
    </form>

    {# Render table #}
    {% render_table table %}
</div>
```

### 5.3 In API Views (DRF)

```python
# myapp/views.py (REST API)
from rest_framework import viewsets
from fairdm.registry import registry
from .models import RockSample


class RockSampleViewSet(viewsets.ModelViewSet):
    """API viewset using auto-generated serializer."""
    queryset = RockSample.objects.all()

    def get_serializer_class(self):
        config = registry.get_for_model(RockSample)
        return config.serializer
```

---

## 6. Registry Introspection

### 6.1 Check Registration

```python
from fairdm.registry import registry
from .models import RockSample


# Check if model is registered
if registry.is_registered(RockSample):
    print("RockSample is registered")

# Get configuration
config = registry.get_for_model(RockSample)
print(f"Display name: {config.display_name}")
print(f"Fields: {config.fields}")
```

### 6.2 List All Registered Models

```python
# Get all registered Sample models
for sample_model in registry.samples:
    config = registry.get_for_model(sample_model)
    print(f"Sample: {config.display_name}")

# Get all registered Measurement models
for measurement_model in registry.measurements:
    config = registry.get_for_model(measurement_model)
    print(f"Measurement: {config.display_name}")

# Get all models (Samples + Measurements)
for model in registry.models:
    config = registry.get_for_model(model)
    print(f"Model: {model.__name__} ({config.display_name})")
```

### 6.3 Iterate Over Configurations

```python
# Process all configurations
for config in registry.get_all_configs():
    print(f"{config.model.__name__}:")
    print(f"  Display name: {config.display_name}")
    print(f"  Fields: {len(config.fields)}")

    # Generate components using cached properties
    form_class = config.form
    table_class = config.table
    print(f"  Form fields: {form_class._meta.fields}")
    print(f"  Table columns: {list(table_class.base_columns.keys())}")
```

---

## 7. Common Patterns

### 7.1 Minimal Registration (1 Line)

```python
@registry.register
class RockSampleConfig(ModelConfiguration):
    model = RockSample
    # That's it! Smart defaults handle everything
```

**Result**: All components auto-generated with sensible defaults

### 7.2 Display-Only Configuration

For read-only models, configure table and exclude form:

```python
@registry.register
class RockSampleConfig(ModelConfiguration):
    model = RockSample
    fields = ['name', 'location', 'date_collected', 'contributor']

    # No form_class = forms won't work
    # But tables and filters will work fine
```

### 7.3 API-Only Configuration

For API-only models, provide serializer fields:

```python
@registry.register
class RockSampleConfig(ModelConfiguration):
    model = RockSample

    # API fields (include related data)
    serializer_fields = [
        'id', 'name', 'location',
        'project__title',        # Include project title
        'dataset__identifier',   # Include dataset ID
        'contributor__name',     # Include contributor name
    ]
```

### 7.4 Import/Export Configuration

For bulk data operations, configure resource fields:

```python
@registry.register
class RockSampleConfig(ModelConfiguration):
    model = RockSample

    # Fields for CSV import/export
    resource_fields = [
        'name', 'description', 'location',
        'date_collected', 'contributor__email'  # Natural key for contributor
    ]
```

---

## 8. Multiple Models Registration

```python
# myapp/registry.py
from fairdm.registry import registry, ModelConfiguration
from .models import RockSample, SoilSample, WaterSample


@registry.register
class RockSampleConfig(ModelConfiguration):
    model = RockSample
    fields = ['name', 'rock_type', 'location']
    display_name = "Rock Sample"


@registry.register
class SoilSampleConfig(ModelConfiguration):
    model = SoilSample
    fields = ['name', 'soil_type', 'depth', 'location']
    display_name = "Soil Sample"


@registry.register
class WaterSampleConfig(ModelConfiguration):
    model = WaterSample
    fields = ['name', 'source', 'ph', 'temperature']
    display_name = "Water Sample"
```

**Loading**: These registrations are executed during Django startup when the app's `AppConfig.ready()` method imports `registry.py`.

---

## 9. Best Practices

### ✅ DO

- Use simple `fields` attribute for most cases
- Use component-specific fields (`table_fields`, etc.) when components need different fields
- Provide custom classes when you need validation, special widgets, or complex logic
- Use descriptive `display_name` and `description` for UI clarity
- Use related field paths (`project__title`) in tables and filters
- Keep registry definitions in `myapp/registry.py` file

### ❌ DON'T

- Mix `fields` with component-specific fields unnecessarily (prefer simple `fields` unless needed)
- Use related field paths (`project__title`) in `form_fields` (forms can't edit related fields)
- Register the same model twice (raises `DuplicateRegistrationError`)
- Forget to import `registry.py` in `AppConfig.ready()` method

---

## 10. Next Steps

**For detailed API specification**: See `data-model.md`
**For implementation contracts**: See `contracts/` directory
**For field resolution algorithm**: See `data-model.md` Section 2
**For validation rules**: See `data-model.md` Section 3
**For exception handling**: See `contracts/exceptions.py`

**To implement**:

1. Review `data-model.md` for complete ModelConfiguration specification
2. Review research findings in `research/` directory
3. Follow implementation checklist in `data-model.md` Section 7
4. Update `fairdm_demo` to demonstrate new patterns
5. Write tests following checklist in `data-model.md` Section 7.5
