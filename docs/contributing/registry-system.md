# Registry System Architecture

The FairDM registry system is a core component that enables automatic generation of Django components (forms, tables, filters, etc.) from model definitions. This document explains the fundamental architecture, design decisions, and implementation details.

## Why We Need a Registry System

### The Problem

Research data portals typically need:

- **Forms** for data entry and editing
- **Tables** for displaying data lists with sorting/pagination
- **Filters** for searching and filtering data
- **Import/Export** functionality for bulk operations
- **REST API serializers** for programmatic access
- **Admin interfaces** for management

Traditionally, developers must manually create each of these components for every model, leading to:

- **Repetitive boilerplate code** (forms, admin classes, serializers)
- **Inconsistent UI patterns** across different models
- **Maintenance overhead** when models change
- **High barrier to entry** for domain experts who aren't Django developers

### The Solution

The FairDM registry system provides:

- **Auto-generation**: Automatically create all necessary components from model definitions
- **Convention over configuration**: Sensible defaults that work out of the box
- **Declarative configuration**: Simple, readable configuration classes
- **Progressive complexity**: Start simple, add customization as needed
- **Type safety**: Full type hints and Protocol definitions

## Core Architecture

### Key Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   @register     │───▶│ ModelConfiguration│───▶│   Components    │
│   Decorator     │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    │ • Forms         │
                                ▲              │ • Tables        │
                                │              │ • Filters       │
                                ▼              │ • Serializers   │
┌─────────────────┐    ┌──────────────────┐    │ • Resources     │
│   Registry      │◀───│  FieldResolver   │    │ • Admin         │
│                 │    │                  │    └─────────────────┘
│ • Model Storage │    └──────────────────┘
│ • Introspection │
│ • Validation    │    ┌──────────────────┐
└─────────────────┘    │    Factories     │
                       │                  │
                       │ Component        │
                       │ Generation       │
                       └──────────────────┘
```

### Registration Flow

1. **Model Definition**: User creates Sample/Measurement subclass
2. **Configuration**: User defines ModelConfiguration with fields and options
3. **Registration**: `@register` decorator stores configuration in registry
4. **Validation**: Registry validates model inheritance and field existence
5. **Component Access**: Properties generate components on-demand using cached_property
6. **Field Resolution**: FieldResolver determines appropriate fields for each component

### Component Generation

```python
# User defines model and configuration
@register
class MySampleConfig(ModelConfiguration):
    model = MySample
    fields = ["name", "location", "temperature"]

# Framework auto-generates components
config = registry.get_for_model(MySample)
form_class = config.form        # Auto-generated ModelForm
table_class = config.table      # Auto-generated django-tables2 Table
filter_class = config.filterset # Auto-generated django-filter FilterSet
# ... etc
```

## Design Principles

### 1. Zero-Configuration Default

Models should work with minimal configuration:

```python
@register
class MinimalSampleConfig(ModelConfiguration):
    model = MySample  # Only model is required
    # Everything else auto-generated with smart defaults
```

### 2. Progressive Enhancement

Start simple, add complexity as needed:

```python
# Level 1: Basic field list
fields = ["name", "location", "temperature"]

# Level 2: Component-specific fields
table_fields = ["name", "location"]
form_fields = ["name", "location", "temperature", "notes"]

# Level 3: Custom component classes
form_class = MyCustomForm
table_class = MyCustomTable
```

### 3. Type Safety

Full type hints enable IDE support and catch errors early:

```python
def get_for_model(self, model: type[Model]) -> ModelConfiguration:
    """Get configuration for model with full type safety."""

@cached_property
def form(self) -> type[ModelForm]:
    """Return form class with correct typing."""
```

### 4. Performance Optimization

Components are generated lazily and cached:

```python
@cached_property
def form(self) -> type[ModelForm]:
    """Generated once, cached forever per configuration instance."""
    return FormFactory(self.model, self.form_fields).create()
```

## Implementation Details

### Registry Storage

The registry uses a simple dictionary mapping models to configurations:

```python
class FairDMRegistry:
    def __init__(self):
        self._registry: dict[type[Model], ModelConfiguration] = {}
```

This provides O(1) lookup performance and simple introspection.

### Field Resolution Algorithm

The FieldResolver implements a 3-tier fallback system:

```python
def resolve_fields_for_component(self, component_type: str) -> list[str]:
    # Tier 1: Component-specific fields (e.g., form_fields)
    if hasattr(config, f"{component_type}_fields"):
        return getattr(config, f"{component_type}_fields")

    # Tier 2: General fields list
    if config.fields:
        return config.fields

    # Tier 3: Smart defaults (exclude auto-generated, non-editable)
    return config.get_default_fields()
```

### Component Factories

Each component type has a dedicated factory:

```python
class FormFactory:
    def create(self) -> type[ModelForm]:
        fields = self.resolver.resolve_fields_for_component("form")
        return modelform_factory(
            model=self.model,
            fields=fields,
            widgets=self.get_widgets()
        )
```

### Validation System

Registration-time validation prevents common errors:

```python
def _validate_model_inheritance(self, model: type[Model]) -> None:
    """Ensure model inherits from Sample or Measurement."""
    if not issubclass(model, (Sample, Measurement)):
        raise ConfigurationError(...)

def _validate_field_existence(self, fields: list[str]) -> None:
    """Ensure all field names exist on model."""
    valid_fields = {f.name for f in self.model._meta.get_fields()}
    for field_name in fields:
        if field_name not in valid_fields:
            suggestions = difflib.get_close_matches(field_name, valid_fields)
            raise FieldValidationError(f"Invalid field: {field_name}. Did you mean: {suggestions}?")
```

## Introspection API

The registry provides powerful introspection capabilities for dynamic workflows:

### Model Discovery

```python
# Get all registered Sample models
for sample_model in registry.samples:
    print(f"Sample: {sample_model.__name__}")

# Get all registered Measurement models
for measurement_model in registry.measurements:
    print(f"Measurement: {measurement_model.__name__}")

# Get all registered models
for model in registry.models:
    print(f"Model: {model.__name__}")
```

### Configuration Access

```python
# Check if model is registered
if registry.is_registered(MySample):
    config = registry.get_for_model(MySample)

# String-based lookup for dynamic scenarios
config = registry.get_for_model("myapp.MySample")

# Bulk operations
all_configs = registry.get_all_configs()
for config in all_configs:
    print(f"{config.model.__name__}: {len(config.fields)} fields")
```

## Performance Characteristics

### Registration Performance

- **Target**: <10ms per model registration
- **Actual**: ~4 microseconds (well under target)
- **Scalability**: Linear with number of models

### Component Generation Performance

- **Target**: <50ms per component on first access
- **Actual**: ~100 microseconds (well under target)
- **Caching**: Subsequent access ~1 microsecond

### Memory Usage

- **Registry**: O(n) where n = number of registered models
- **Components**: Generated lazily, cached per configuration
- **Footprint**: Minimal until components are accessed

## Extension Points

### Custom Component Classes

Users can provide custom implementations:

```python
@register
class AdvancedSampleConfig(ModelConfiguration):
    model = MySample
    form_class = MyCustomForm      # Override auto-generation
    table_class = MyCustomTable    # Custom table implementation
    # Other components still auto-generated
```

### Custom Factories

Advanced users can extend factory behavior:

```python
class CustomFormFactory(FormFactory):
    def get_widgets(self) -> dict[str, Any]:
        widgets = super().get_widgets()
        # Add custom widget logic
        return widgets
```

### Plugin Integration

The registry enables plugin development:

```python
class AnalysisPlugin:
    def get_compatible_models(self) -> list[type[Model]]:
        """Find models that work with this plugin."""
        compatible = []
        for config in registry.get_all_configs():
            if self.is_compatible(config.model):
                compatible.append(config.model)
        return compatible
```

## Testing Strategy

### Unit Tests

- **Component generation**: Test each factory independently
- **Field resolution**: Test 3-tier fallback algorithm
- **Validation**: Test error cases and edge conditions
- **Introspection**: Test registry API methods

### Integration Tests

- **End-to-end registration**: Model → config → components
- **Django integration**: Forms work with views, tables render correctly
- **Performance**: Benchmark against requirements

### Contract Tests

- **Protocol compliance**: Verify implementations match Protocol definitions
- **API stability**: Ensure public API remains consistent

## Future Enhancements

### Planned Features

- **Dynamic field discovery**: Automatically detect model fields and relationships
- **UI generation**: Auto-generate complete CRUD views
- **Plugin marketplace**: Registry for community plugins
- **Visual configuration**: GUI for non-developers

### Extension Areas

- **Component types**: Add support for charts, dashboards, reports
- **Field types**: Enhanced support for geospatial, scientific data types
- **Validation**: Runtime schema validation and data quality checks
- **Caching**: Distributed caching for multi-instance deployments

## Contributing Guidelines

When working on the registry system:

1. **Add comprehensive tests** - both unit and integration tests for new features
2. **Update type hints** - maintain 100% mypy compliance
3. **Document performance impact** - benchmark any changes affecting registration/generation
4. **Follow naming conventions** - use consistent naming for new components/methods
5. **Validate with demo app** - ensure changes work in fairdm_demo

The registry system is the foundation of FairDM's ease of use - changes here impact every user, so maintain high quality standards and thorough testing.
