# Registry System Architecture

This page is for people changing the registry itself. How a portal uses it is in the developers' section: [What registering a type produces](../developers/explanation/what-registering-a-type-produces.md), [Model configuration](../developers/reference/model-configuration.md) and [The registry](../developers/reference/registry.md).

The FairDM registry system is a core component that enables automatic generation of Django components (forms, tables, filters, etc.) from model definitions. This document explains the fundamental architecture, design decisions, and implementation details.

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

## Performance Characteristics

### Registration

Validating a configuration costs about 0.007 ms, so 100 registered models add 0.69 ms to startup and
250 add 1.7 ms. Validation is `_meta` lookup only and never touches the database, which matters
because registration runs while Django is still populating the app registry.

### Generating components

Producing all six components for one model takes under 1 ms, scaling at roughly 0.1 ms per field per
component. Nothing is cached, so a view pays that cost per request rather than once.

The tests pin the deterministic property rather than the timings: registration and all six accessors
run with a query count of zero. Wall-clock assertions are not used, because they are flaky on shared
CI in the direction that blocks merges.

### Memory

The registry holds one configuration per model and nothing else.

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

## Contributing Guidelines

When working on the registry system:

1. **Add comprehensive tests** - both unit and integration tests for new features
2. **Update type hints** - maintain 100% mypy compliance
3. **Document performance impact** - benchmark any changes affecting registration/generation
4. **Follow naming conventions** - use consistent naming for new components/methods
5. **Validate with demo app** - ensure changes work in demo

The registry system is the foundation of FairDM's ease of use - changes here impact every user, so maintain high quality standards and thorough testing.
