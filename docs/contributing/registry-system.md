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
│   Registry      │    │    Factories     │    │ • Admin         │
│                 │    │                  │    └─────────────────┘
│ • Model Storage │    │ Component        │
│ • Introspection │    │ Generation       │
│ • Validation    │    └──────────────────┘
└─────────────────┘
```

### Registration Flow

1. **Model definition**: a portal writes a concrete `Sample` or `Measurement` subclass.
2. **Configuration**: a `ModelConfiguration` subclass declares the model and the fields that matter.
3. **Validation**: the whole configuration is checked while it is built, and the registry checks that
   the model may be registered at all. A mistake stops the process here.
4. **Registration**: `@register` stores the configuration, and registers the model's admin class
   unless the portal already registered one of its own.
5. **Component access**: `get_<component>_class()` resolves the field list and builds the class, on
   every call.

### Component Generation

```python
# User defines model and configuration
@register
class MySampleConfig(ModelConfiguration):
    model = MySample
    fields = ["name", "location", "temperature"]

# Framework builds components from the configuration
config = registry.get_for_model(MySample)
form_class = config.get_form_class()        # ModelForm
table_class = config.get_table_class()      # django-tables2 Table
filter_class = config.get_filterset_class() # django-filter FilterSet
# ... and get_serializer_class(), get_resource_class(), get_admin_class()
```

Always call the accessor. It is the only public way to reach a component, so a configuration that
overrides one is honoured everywhere.

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

Start simple, add complexity as needed. There are three tiers, in increasing order of effort:

```python
# Tier 1: a field list, shared or per component
fields = ["name", "location", "temperature"]
table_fields = ["name", "location"]

# Tier 2: your own class for one component; the other five stay generated
table_class = MyCustomTable

# Tier 3: build one in code, when a declaration cannot say what you need
def get_table_class(self):
    return build_table(self.model, self.pick_columns())
```

Every part of the framework reaches a component through its accessor, so an override at tier 3 is
what all of it receives.

Declaring a component's own field list *and* its class is refused when the model is registered,
because the field list could never take effect. Django applies the same rule to `fields` beside
`form_class`.

### 3. Type Safety

Full type hints enable IDE support and catch errors early:

```python
def get_for_model(self, model: type[Model]) -> ModelConfiguration:
    """The configuration for a model. Raises if it is not registered."""

def get_form_class(self) -> type[ModelForm]:
    """The form class for this model. Override to build your own."""
```

### 4. Nothing is cached

An accessor builds or resolves its class on every call. This is what Django's own
`ModelFormMixin.get_form_class()` does, and it is what makes tier 3 work: a cached attribute is read
without consulting the method a portal may have overridden.

The cost was measured before the cache was removed. Generating the components a page needs takes
0.18 ms for a table and filter set on a six-field model, and 1.08 ms for a table, form and filter set
on a ten-field model, at roughly 0.1 ms per field per component. Rendering a twenty-cell table
fragment in the same process takes 0.12 ms, and a real page renders far more than that.

If profiling ever justifies caching, it returns inside the accessor behind an explicit, clearable
store, not a descriptor that also swallows overrides.

## Implementation Details

### Registry Storage

The registry uses a simple dictionary mapping models to configurations:

```python
class FairDMRegistry:
    def __init__(self):
        self._registry: dict[type[Model], ModelConfiguration] = {}
```

This provides O(1) lookup performance and simple introspection.

### Field Resolution

`resolve_fields()` is the one place a field list is worked out, and every component uses it. A
component's own list wins, then the shared `fields`, then the framework's own choice:

```python
def resolve_fields(self, component: str) -> list[str]:
    spec = COMPONENTS[component]
    declared = getattr(self, spec.fields_attr)
    chosen = (
        declared
        if declared is not None
        else (self.fields or self.get_default_fields(self.model))
    )
    return [n for n in flatten_fields(chosen) if n not in set(self.exclude)]
```

`COMPONENTS` is the table that describes all six: which attribute holds each one's field list, which
holds a supplied class, which base class that must subclass, and which factory builds it. Adding a
component is a row, not six near-identical methods.

The framework's own choice of fields lives on `FieldInspector` in `fairdm/utils/inspection.py`, and
only there. It includes the model's editable fields and leaves out the primary key, polymorphic type
columns, inheritance pointers, automatic timestamps, non-editable fields, reverse relations, and
many-to-many fields with an explicit through model, which Django's admin rejects.

### Component Factories

Each component type has a dedicated factory:

```python
class FormFactory(ComponentFactory):
    def generate(self) -> type[ModelForm]:
        return modelform_factory(
            model=self.model,
            fields=self.get_fields(),
            widgets=self._get_smart_widgets(),
        )
```

A factory receives a resolved field list and builds one class from it. It does no resolution of its
own, so there is one answer to "which fields does this model use" per component.

### Validation System

Registration-time validation prevents common errors:

Validation happens once, while the model is being registered, and nowhere else. Registration runs at
import, so a mistake stops the process on every start, including under a WSGI or ASGI server. There
are no Django system checks for the registry: a check only runs from a management command, which
makes it a weaker guarantee wearing the same clothes.

What is refused:

- a field name that does not exist, with a close match suggested where there is one
- a related path whose later segments do not resolve, not just its first
- a component's own field list declared beside its own class
- a supplied class that does not subclass the base its component requires
- a custom admin class that is not the polymorphic child admin for its hierarchy
- a model that is abstract, or is one of the polymorphic base classes, or is outside both hierarchies
- a model registered twice, with the module and qualified name of the first registration

An error names the model, the attribute that declared the offending value, the value itself, and
either a suggestion or the reason a path stopped resolving:

```text
Invalid field 'rock_typ' in RockSample.table_fields: no such field on RockSample.
Did you mean: rock_type?
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

`registry.get_for_model()` is the way to reach a configuration. There is no shortcut on the model
itself: a second path is how consumers drifted onto one that ignored overrides, and one that quietly
returned nothing turned a missing registration into an error somewhere else entirely.

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

`get_for_model()` raises `NotRegisteredError` for a model that was never registered. In a template,
use the `get_registry_info` tag instead, which returns nothing rather than raising, because a
template asking what the registry knows is asking rather than asserting.

## Performance Characteristics

### Registration

Validating a configuration costs about 0.007 ms, so 100 registered models add 0.69 ms to startup and
250 add 1.7 ms. Validation is `_meta` lookup only and never touches the database, which matters
because registration runs while Django is still populating the app registry.

### Component generation

Producing all six components for one model takes under 1 ms, scaling at roughly 0.1 ms per field per
component. Nothing is cached, so a view pays that cost per request rather than once.

The tests pin the deterministic property rather than the timings: registration and all six accessors
run with a query count of zero. Wall-clock assertions are not used, because they are flaky on shared
CI in the direction that blocks merges.

### Memory

The registry holds one configuration per model and nothing else.

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
- **Caching**: only if profiling shows a hot spot, and behind an explicit store

## Contributing Guidelines

When working on the registry system:

1. **Add comprehensive tests** - both unit and integration tests for new features
2. **Update type hints** - maintain 100% mypy compliance
3. **Document performance impact** - benchmark any changes affecting registration/generation
4. **Follow naming conventions** - use consistent naming for new components/methods
5. **Validate with demo app** - ensure changes work in fairdm_demo

The registry system is the foundation of FairDM's ease of use - changes here impact every user, so maintain high quality standards and thorough testing.
