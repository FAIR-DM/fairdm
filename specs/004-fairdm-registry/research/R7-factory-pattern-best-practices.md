# Research Task R7: Factory Pattern Best Practices

**Date**: 2026-01-12
**Status**: ✅ Complete
**Researcher**: GitHub Copilot

---

## Executive Summary

**Decision**: **Class-based factories** (current implementation) are the correct approach.

The current factory implementation in `fairdm/registry/factories.py` follows Django conventions and aligns with how Django itself implements similar patterns (e.g., `modelform_factory`, `table_factory`, `filterset_factory`). The class-based approach provides:

- **Encapsulation**: Related logic grouped together
- **State management**: Factory instances hold configuration and model context
- **Extensibility**: Easy to subclass and override behavior
- **Testability**: Clean dependency injection via constructor
- **Readability**: Clear, self-documenting API

**Recommended improvements**: Add type hints using `typing.Protocol` for better type safety and IDE support, but the core architecture is sound.

---

## Current Implementation Assessment

### What's Good ✅

1. **Follows Django Patterns**
   - Mirrors Django's own `modelform_factory`, `table_factory`, `filterset_factory`
   - Uses similar patterns to `ModelAdmin` registration system
   - Delegates to Django's built-in factories when appropriate

2. **Clean Architecture**
   - Base `ComponentFactory` class provides shared functionality
   - Specialized factories (`FormFactory`, `TableFactory`, `FilterFactory`, `AdminFactory`)
   - Clear separation of concerns with `FieldInspector` for introspection

3. **Good Encapsulation**

   ```python
   # Each factory encapsulates its logic
   class FormFactory(ComponentFactory):
       def __init__(self, model, config, parent_fields=None):
           super().__init__(model, config)
           self.parent_fields = parent_fields

       def get_fields(self) -> list[str] | str:
           # Smart field resolution logic

       def generate(self) -> type[ModelForm]:
           # Form generation logic
   ```

4. **Composable and Extensible**
   - Factory instances can be created and reused
   - Easy to override specific methods in subclasses
   - Configuration classes separate from factory logic

5. **Testable Design**
   - Dependencies injected via constructor
   - Methods have clear inputs/outputs
   - Can be tested without full Django setup

### What Needs Improvement 🔧

1. **Missing Type Hints on Base Class**

   ```python
   # Current
   def generate(self) -> Any:
       raise NotImplementedError("Subclasses must implement generate()")

   # Should use Protocol
   def generate(self) -> ComponentType:
       raise NotImplementedError("Subclasses must implement generate()")
   ```

2. **No Protocol for Factory Interface**
   - No explicit contract defining what a "factory" is
   - Makes it harder for type checkers and IDEs to provide guidance

3. **Some Methods Could Use Better Type Hints**

   ```python
   # Current
   def _flatten_fields(self, fields: list | tuple | None) -> list[str] | None:

   # More precise
   def _flatten_fields(self, fields: Sequence[str | Sequence[str]] | None) -> list[str] | None:
   ```

4. **Configuration Classes Could Define Protocols**
   - Config classes are dataclasses but no interface contract
   - Type checkers can't verify correct config usage

---

## Django Conventions Analysis

### How Django Admin Works

Django admin registration follows a **class-based pattern** with factories:

```python
# Simple registration
admin.site.register(Author)

# With custom ModelAdmin
class AuthorAdmin(admin.ModelAdmin):
    list_display = ['name', 'email']
    search_fields = ['name']

admin.site.register(Author, AuthorAdmin)

# Using decorator
@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    pass
```

**Key observations**:

- `ModelAdmin` is a **class**, not a function
- Configuration is done via **class attributes**
- Registration system accepts both class definitions and instances
- Django's internal code uses **factory functions** (`modelform_factory`) but wraps them in **class-based APIs**

### How DRF ViewSets Work

Django REST Framework follows a similar pattern:

```python
class AccountViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing accounts.
    """
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [IsAccountAdminOrReadOnly]
```

**Key observations**:

- `ModelViewSet` is a **class** that provides default CRUD operations
- Configuration via **class attributes** (queryset, serializer_class)
- Can override methods for custom behavior
- Uses mixins for composability

### How django-tables2 Works

django-tables2 provides both class-based and factory approaches:

```python
# Class-based (recommended for complex tables)
class PersonTable(tables.Table):
    class Meta:
        model = Person
        fields = ['first_name', 'last_name', 'birth_date']

# Factory function (for simple, dynamic tables)
PersonTable = table_factory(Person, fields=['first_name', 'last_name'])
```

**Key observations**:

- **Class-based is the primary, recommended approach**
- Factory function exists for **simple, one-off cases**
- Factory function actually **returns a class**
- Configuration uses nested `Meta` class (like Django)

### Pattern: Factory Functions Return Classes

All of Django's factory functions return **classes**, not instances:

```python
# Django's modelform_factory signature
def modelform_factory(
    model,
    form=ModelForm,
    fields=None,
    exclude=None,
    **kwargs
) -> type[ModelForm]:  # Returns a CLASS
    # ...
    return type(class_name, (form,), attrs)

# django-tables2's table_factory
def table_factory(
    model,
    table=Table,
    fields=None,
    **kwargs
) -> type[Table]:  # Returns a CLASS
    # ...
    return type(class_name, (table,), attrs)
```

**Conclusion**: Django ecosystem uses **factory functions that return classes**, then wraps them in **class-based factories** for better UX.

---

## Factory Pattern Comparison

### Class-Based Factories (Current - ✅ Recommended)

```python
class FormFactory(ComponentFactory):
    """Factory for generating ModelForm classes."""

    def __init__(self, model: type[models.Model], config: FormConfig, parent_fields: list[str] | None = None):
        super().__init__(model, config)
        self.parent_fields = parent_fields
        self.inspector = FieldInspector(model)

    def get_fields(self) -> list[str] | str:
        # Smart field resolution
        if self.config.fields is not None:
            return self.config.fields
        elif self.parent_fields:
            return self.parent_fields
        return self.inspector.get_safe_fields()

    def generate(self) -> type[ModelForm]:
        # Use Django's factory
        return modelform_factory(self.model, fields=self.get_fields())

# Usage
factory = FormFactory(MyModel, config, parent_fields)
form_class = factory.generate()
```

**Pros**:

- ✅ Encapsulates related logic (field resolution, validation, generation)
- ✅ Stateful - can maintain configuration and context
- ✅ Easy to extend via subclassing
- ✅ Testable via dependency injection
- ✅ Self-documenting with docstrings and type hints
- ✅ Matches Django's `ModelAdmin` pattern

**Cons**:

- Slightly more verbose than functions
- Requires instantiation before use

### Function-Based Factories (Alternative - ❌ Not Recommended)

```python
def create_form_class(
    model: type[models.Model],
    config: FormConfig,
    parent_fields: list[str] | None = None
) -> type[ModelForm]:
    """Generate a ModelForm class."""
    inspector = FieldInspector(model)

    # Determine fields
    if config.fields is not None:
        fields = config.fields
    elif parent_fields:
        fields = parent_fields
    else:
        fields = inspector.get_safe_fields()

    return modelform_factory(model, fields=fields)

# Usage
form_class = create_form_class(MyModel, config, parent_fields)
```

**Pros**:

- Simpler for one-off usage
- Less boilerplate
- Direct function call

**Cons**:

- ❌ No state management (must pass everything as parameters)
- ❌ Harder to extend (can't subclass a function)
- ❌ Testing requires mocking all dependencies
- ❌ Multiple related methods become multiple functions
- ❌ Doesn't match Django's class-based conventions

### Builder Pattern (Alternative - ❌ Over-Engineering)

```python
class FormBuilder:
    """Builder for ModelForm classes."""

    def __init__(self, model: type[models.Model]):
        self.model = model
        self._fields = None
        self._exclude = None
        self._widgets = {}

    def with_fields(self, fields: list[str]) -> 'FormBuilder':
        self._fields = fields
        return self

    def with_exclude(self, exclude: list[str]) -> 'FormBuilder':
        self._exclude = exclude
        return self

    def with_widget(self, field: str, widget) -> 'FormBuilder':
        self._widgets[field] = widget
        return self

    def build(self) -> type[ModelForm]:
        return modelform_factory(
            self.model,
            fields=self._fields,
            exclude=self._exclude
        )

# Usage
form_class = (FormBuilder(MyModel)
    .with_fields(['name', 'email'])
    .with_exclude(['password'])
    .build())
```

**Pros**:

- Fluent interface
- Good for complex, optional configurations

**Cons**:

- ❌ Over-engineering for this use case
- ❌ More verbose than class-based factories
- ❌ Doesn't match Django patterns
- ❌ Harder to understand for Django developers

---

## Type Hints Strategy

### Current State

The factories have basic type hints but lack:

- Generic types for configuration
- Protocols for factory interfaces
- Precise return types for methods

### Recommended: Use `typing.Protocol`

```python
from typing import Protocol, TypeVar, Generic
from django.db import models
from django.forms import ModelForm
from django_tables2 import Table
from django_filters import FilterSet

# Type variables
ModelType = TypeVar('ModelType', bound=models.Model)
ComponentType = TypeVar('ComponentType')
ConfigType = TypeVar('ConfigType')

# Protocol for factory interface
class ComponentFactoryProtocol(Protocol[ModelType, ConfigType, ComponentType]):
    """Protocol defining the factory interface."""

    model: type[ModelType]
    config: ConfigType
    inspector: FieldInspector

    def get_fields(self) -> list[str] | str:
        """Get fields to include in component."""
        ...

    def apply_exclusions(self, fields: list[str]) -> list[str]:
        """Apply exclusions to field list."""
        ...

    def generate(self) -> type[ComponentType]:
        """Generate the component class."""
        ...

# Protocol for configuration classes
class FormConfigProtocol(Protocol):
    """Protocol for form configuration."""
    fields: list[str] | str | None
    exclude: list[str] | None
    widgets: dict[str, Any] | None
    form_class: type[ModelForm] | str | None

class TableConfigProtocol(Protocol):
    """Protocol for table configuration."""
    fields: list[str] | None
    exclude: list[str] | None
    orderable: list[str] | bool
    table_class: type[Table] | str | None

# Typed base factory
class ComponentFactory(Generic[ModelType, ConfigType, ComponentType]):
    """Base factory with type parameters."""

    def __init__(self, model: type[ModelType], config: ConfigType):
        self.model = model
        self.config = config
        self.inspector = FieldInspector(model)

    def get_fields(self) -> list[str]:
        """Get fields to use."""
        if hasattr(self.config, 'fields') and self.config.fields is not None:
            if self.config.fields == "__all__":
                return self.inspector.get_all_field_names()
            return self.config.fields
        return self.inspector.get_safe_fields()

    def apply_exclusions(self, fields: list[str]) -> list[str]:
        """Apply exclusions to field list."""
        if hasattr(self.config, 'exclude') and self.config.exclude:
            return [f for f in fields if f not in self.config.exclude]
        return fields

    def generate(self) -> type[ComponentType]:
        """Generate the component class."""
        raise NotImplementedError("Subclasses must implement generate()")

# Concrete factory with full type hints
class FormFactory(ComponentFactory[models.Model, FormConfig, ModelForm]):
    """Factory for generating ModelForm classes."""

    def __init__(
        self,
        model: type[models.Model],
        config: FormConfig,
        parent_fields: list[str] | None = None
    ):
        super().__init__(model, config)
        self.parent_fields = parent_fields

    def get_fields(self) -> list[str] | str:
        """Get fields for the form."""
        # Implementation...
        return super().get_fields()

    def generate(self) -> type[ModelForm]:
        """Generate a ModelForm class."""
        if self.config.form_class is not None:
            if isinstance(self.config.form_class, str):
                from django.utils.module_loading import import_string
                return import_string(self.config.form_class)
            return self.config.form_class

        fields = self.get_fields()
        return modelform_factory(self.model, fields=fields)

# Type aliases for convenience
FormFactoryType = ComponentFactory[models.Model, FormConfig, ModelForm]
TableFactoryType = ComponentFactory[models.Model, TableConfig, Table]
FilterFactoryType = ComponentFactory[models.Model, FiltersConfig, FilterSet]
```

### Benefits of Protocols

1. **Type Safety**: IDEs and type checkers can verify correct usage
2. **Documentation**: Protocol defines the contract explicitly
3. **Flexibility**: Implementations don't need to inherit from Protocol
4. **Duck Typing**: If it walks like a factory and quacks like a factory...

### Usage with Protocols

```python
def create_component(
    factory: ComponentFactoryProtocol[models.Model, Any, ModelForm]
) -> type[ModelForm]:
    """Create a component using any factory that matches the protocol."""
    fields = factory.get_fields()
    return factory.generate()

# Works with any factory that implements the protocol
form_factory = FormFactory(MyModel, FormConfig())
form_class = create_component(form_factory)  # Type checker happy!
```

---

## Factory Signature Recommendations

### Base Factory

```python
from typing import TypeVar, Generic, Protocol
from django.db import models

ModelType = TypeVar('ModelType', bound=models.Model)
ConfigType = TypeVar('ConfigType')
ComponentType = TypeVar('ComponentType')

class ComponentFactory(Generic[ModelType, ConfigType, ComponentType]):
    """Base factory for generating Django components from configuration.

    This abstract base class provides common functionality for all component
    factories. Subclasses implement specific generation logic for Forms,
    Tables, Filters, etc.

    Type Parameters:
        ModelType: The Django model class type
        ConfigType: The configuration class type
        ComponentType: The component class type to generate

    Args:
        model: The Django model class to generate components for
        config: The component-specific configuration

    Attributes:
        model: The Django model class
        config: The component-specific configuration
        inspector: FieldInspector instance for model introspection
    """

    def __init__(self, model: type[ModelType], config: ConfigType):
        """Initialize the factory.

        Args:
            model: The Django model class to generate components for
            config: The component-specific configuration
        """
        self.model = model
        self.config = config
        self.inspector = FieldInspector(model)

    def get_fields(self) -> list[str]:
        """Get fields to use, with intelligent fallback chain.

        Resolution order:
        1. Component-specific fields (e.g., config.fields)
        2. Auto-detected safe fields (inspector.get_safe_fields())

        Returns:
            List of field names to use
        """
        if hasattr(self.config, 'fields') and self.config.fields is not None:
            if self.config.fields == "__all__":
                return self.inspector.get_all_field_names()
            return self.config.fields
        return self.inspector.get_safe_fields()

    def apply_exclusions(self, fields: list[str]) -> list[str]:
        """Apply exclusions to field list.

        Args:
            fields: Initial field list

        Returns:
            Field list with exclusions removed
        """
        if hasattr(self.config, 'exclude') and self.config.exclude:
            return [f for f in fields if f not in self.config.exclude]
        return fields

    def generate(self) -> type[ComponentType]:
        """Generate the component class.

        This method must be implemented by subclasses.

        Returns:
            The generated component class

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement generate()")
```

### Specialized Factory Example

```python
from typing import Literal
from django.forms import ModelForm

class FormFactory(ComponentFactory[models.Model, FormConfig, ModelForm]):
    """Factory for generating ModelForm classes with smart widgets.

    Generates Django ModelForm classes based on configuration settings,
    with intelligent field selection and widget generation.

    Args:
        model: The Django model class
        config: FormConfig with form-specific settings
        parent_fields: Optional fields from parent ModelConfiguration

    Example:
        >>> config = FormConfig(fields=['name', 'email'])
        >>> factory = FormFactory(MyModel, config)
        >>> form_class = factory.generate()
        >>> form = form_class()
    """

    def __init__(
        self,
        model: type[models.Model],
        config: FormConfig,
        parent_fields: list[str] | None = None
    ):
        """Initialize FormFactory.

        Args:
            model: The Django model class
            config: FormConfig with form-specific settings
            parent_fields: Fields from parent ModelConfiguration (fallback)
        """
        super().__init__(model, config)
        self.parent_fields = parent_fields

    def get_fields(self) -> list[str] | Literal["__all__"]:
        """Get fields for the form.

        Returns:
            List of field names or "__all__" string
        """
        # Check if config specifies fields
        if self.config.fields is not None:
            return self.config.fields
        # Fall back to parent fields
        elif self.parent_fields:
            return self.parent_fields
        # Default to safe fields
        return self.inspector.get_safe_fields()

    def get_widgets(self) -> dict[str, Any]:
        """Generate smart widgets for fields.

        Returns:
            Dictionary mapping field names to widget instances
        """
        widgets = dict(self.config.widgets) if self.config.widgets else {}

        fields = self.get_fields()
        if fields == "__all__":
            fields = self.inspector.get_safe_fields()

        for field_name in fields:
            if field_name not in widgets:
                suggested_widget = self.inspector.suggest_widget(field_name)
                if suggested_widget:
                    widgets[field_name] = suggested_widget

        return widgets

    def generate(self) -> type[ModelForm]:
        """Generate a ModelForm class.

        Returns:
            ModelForm subclass with smart widgets and configuration

        Raises:
            ImportError: If custom form_class string can't be imported
        """
        # If user provided a custom form class, use it
        if self.config.form_class is not None:
            if isinstance(self.config.form_class, str):
                from django.utils.module_loading import import_string
                return import_string(self.config.form_class)
            return self.config.form_class

        # Build form using Django's modelform_factory
        fields = self.get_fields()
        kwargs = {"fields": fields if fields != [] else "__all__"}

        if self.config.exclude:
            kwargs["exclude"] = self.config.exclude

        return modelform_factory(self.model, form=ModelForm, **kwargs)
```

---

## Alternatives Considered

### 1. Simple Functions (Rejected)

```python
def create_form(model, fields, exclude=None):
    return modelform_factory(model, fields=fields, exclude=exclude)
```

**Why rejected**:

- No state management
- Not extensible
- Doesn't match Django patterns
- Testing is harder

### 2. Abstract Factory Pattern (Rejected)

```python
class ComponentAbstractFactory(ABC):
    @abstractmethod
    def create_form(self) -> type[ModelForm]: ...

    @abstractmethod
    def create_table(self) -> type[Table]: ...

    @abstractmethod
    def create_filterset(self) -> type[FilterSet]: ...

class SampleComponentFactory(ComponentAbstractFactory):
    def create_form(self) -> type[ModelForm]:
        return SampleForm
```

**Why rejected**:

- Over-engineering for this use case
- Forces all components to be created together
- Less flexible than independent factories
- Not how Django ecosystem works

### 3. Registry Pattern (Already Used for Models, Not for Factories)

```python
# This is for MODEL registration, not factory registration
@register
class SoilSampleConfig(ModelConfiguration):
    model = SoilSample
    # ...
```

**Note**: Registry pattern is correctly used for model registration, but **not** needed for factory instantiation. Factories are created on-demand, not registered globally.

### 4. Factory Method Pattern (Similar to Current, but Less Explicit)

```python
class ModelConfiguration:
    def create_form_factory(self) -> FormFactory:
        return FormFactory(self.model, self.form, self.fields)
```

**Why current approach is better**:

- Direct instantiation is clearer
- No need for factory-of-factories
- Current pattern: `FormFactory(model, config).generate()`
- Would become: `config.create_form_factory().generate()`

---

## Implementation Notes

### Testability ✅

Current factories are highly testable:

```python
def test_form_factory_with_custom_fields():
    """Test FormFactory respects custom field list."""
    config = FormConfig(fields=['name', 'email'])
    factory = FormFactory(MyModel, config)

    fields = factory.get_fields()

    assert fields == ['name', 'email']

def test_form_factory_generates_valid_form():
    """Test FormFactory generates working ModelForm."""
    config = FormConfig()
    factory = FormFactory(MyModel, config)

    form_class = factory.generate()

    assert issubclass(form_class, ModelForm)
    assert form_class._meta.model == MyModel
```

**Key features**:

- No database required for most tests
- Dependencies injected via constructor
- Pure functions (get_fields, apply_exclusions) easy to test
- Can mock FieldInspector for complex scenarios

### Extensibility ✅

Factories can be easily extended:

```python
class CustomFormFactory(FormFactory):
    """Custom form factory with additional logic."""

    def get_fields(self) -> list[str]:
        """Custom field resolution logic."""
        fields = super().get_fields()
        # Add custom logic
        if 'created_at' not in fields:
            fields.append('created_at')
        return fields

    def generate(self) -> type[ModelForm]:
        """Custom form generation."""
        form_class = super().generate()
        # Add custom form attributes
        form_class.base_fields['name'].required = False
        return form_class
```

### Backwards Compatibility ✅

Current approach maintains backwards compatibility:

```python
# Old way (still works)
from django.forms import modelform_factory
form_class = modelform_factory(MyModel, fields=['name'])

# New way (more features)
factory = FormFactory(MyModel, FormConfig(fields=['name']))
form_class = factory.generate()
```

The factories **wrap** Django's built-in factories, so:

- Django updates automatically propagate
- Can still use Django's factories directly
- No vendor lock-in

### Performance Considerations

**Factories create classes, not instances** - this is important:

```python
# ✅ Good: Generate once, reuse many times
form_class = FormFactory(MyModel, config).generate()
form1 = form_class(data=data1)
form2 = form_class(data=data2)

# ❌ Bad: Generating class on every request
def my_view(request):
    form_class = FormFactory(MyModel, config).generate()  # Wasteful!
    form = form_class(request.POST)
```

**Solution**: Generate classes during app initialization:

```python
class ModelConfiguration:
    def __post_init__(self):
        # Cache generated classes
        self._form_class = None
        self._table_class = None

    def get_form_class(self) -> type[ModelForm]:
        if self._form_class is None:
            factory = FormFactory(self.model, self.form, self.fields)
            self._form_class = factory.generate()
        return self._form_class
```

This is exactly what the current implementation does! ✅

---

## Code Examples

### Ideal Factory Implementation

```python
"""
Component Factories for FairDM ModelConfiguration.

This module provides factory classes that generate Django components (Forms,
Tables, Filters, Admin) from ModelConfiguration settings using intelligent
field introspection.
"""

from typing import Any, Generic, TypeVar, Literal
from django.db import models
from django.forms import ModelForm, modelform_factory
from django_filters import FilterSet
from django_filters.filterset import filterset_factory
from django_tables2 import Table
from django_tables2.tables import table_factory

from fairdm.registry.components import (
    AdminConfig,
    FiltersConfig,
    FormConfig,
    TableConfig,
)
from fairdm.utils.inspection import FieldInspector

# Type variables for generic factory
ModelType = TypeVar('ModelType', bound=models.Model)
ConfigType = TypeVar('ConfigType')
ComponentType = TypeVar('ComponentType')


class ComponentFactory(Generic[ModelType, ConfigType, ComponentType]):
    """Base factory for generating Django components from configuration.

    This abstract base class provides common functionality for all component
    factories. Subclasses implement specific generation logic for Forms,
    Tables, Filters, etc.

    Type Parameters:
        ModelType: The Django model class type
        ConfigType: The configuration class type
        ComponentType: The component class type to generate

    Args:
        model: The Django model class to generate components for
        config: The component-specific configuration

    Attributes:
        model: The Django model class
        config: The component-specific configuration
        inspector: FieldInspector instance for model introspection

    Example:
        >>> class MyFactory(ComponentFactory[models.Model, MyConfig, MyComponent]):
        ...     def generate(self) -> type[MyComponent]:
        ...         return MyComponent
        >>>
        >>> factory = MyFactory(MyModel, MyConfig())
        >>> component_class = factory.generate()
    """

    def __init__(self, model: type[ModelType], config: ConfigType):
        """Initialize the factory.

        Args:
            model: The Django model class to generate components for
            config: The component-specific configuration
        """
        self.model = model
        self.config = config
        self.inspector = FieldInspector(model)

    def get_fields(self) -> list[str]:
        """Get fields to use, with intelligent fallback chain.

        Resolution order:
        1. Component-specific fields (e.g., config.fields)
        2. Auto-detected safe fields (inspector.get_safe_fields())

        Returns:
            List of field names to use
        """
        if hasattr(self.config, 'fields') and self.config.fields is not None:
            if self.config.fields == "__all__":
                return self.inspector.get_all_field_names()
            return self.config.fields
        return self.inspector.get_safe_fields()

    def apply_exclusions(self, fields: list[str]) -> list[str]:
        """Apply exclusions to field list.

        Args:
            fields: Initial field list

        Returns:
            Field list with exclusions removed
        """
        if hasattr(self.config, 'exclude') and self.config.exclude:
            return [f for f in fields if f not in self.config.exclude]
        return fields

    def generate(self) -> type[ComponentType]:
        """Generate the component class.

        This method must be implemented by subclasses.

        Returns:
            The generated component class

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement generate()")


class FormFactory(ComponentFactory[models.Model, FormConfig, ModelForm]):
    """Factory for generating ModelForm classes with smart widgets.

    Generates Django ModelForm classes based on configuration settings,
    with intelligent field selection, widget generation, and validation.

    Args:
        model: The Django model class
        config: FormConfig with form-specific settings
        parent_fields: Optional fields from parent ModelConfiguration

    Attributes:
        parent_fields: Fields from parent configuration (fallback)

    Example:
        >>> config = FormConfig(
        ...     fields=['name', 'email', 'description'],
        ...     widgets={'description': 'Textarea'}
        ... )
        >>> factory = FormFactory(MyModel, config)
        >>> form_class = factory.generate()
        >>> form = form_class()
    """

    def __init__(
        self,
        model: type[models.Model],
        config: FormConfig,
        parent_fields: list[str] | None = None
    ):
        """Initialize FormFactory.

        Args:
            model: The Django model class
            config: FormConfig with form-specific settings
            parent_fields: Fields from parent ModelConfiguration (fallback)
        """
        super().__init__(model, config)
        self.parent_fields = parent_fields

    def get_fields(self) -> list[str] | Literal["__all__"]:
        """Get fields for the form.

        Resolution order:
        1. Config.fields (if specified)
        2. Parent fields (if provided)
        3. Safe fields (auto-detected)

        Returns:
            List of field names or "__all__" string
        """
        if self.config.fields is not None:
            return self.config.fields
        elif self.parent_fields:
            return self.parent_fields
        return self.inspector.get_safe_fields()

    def get_widgets(self) -> dict[str, Any]:
        """Generate smart widgets for fields.

        Combines user-specified widgets with auto-detected suggestions.

        Returns:
            Dictionary mapping field names to widget instances
        """
        widgets = dict(self.config.widgets) if self.config.widgets else {}

        fields = self.get_fields()
        if fields == "__all__":
            fields = self.inspector.get_safe_fields()

        for field_name in fields:
            if field_name not in widgets:
                suggested_widget = self.inspector.suggest_widget(field_name)
                if suggested_widget:
                    widgets[field_name] = suggested_widget

        return widgets

    def generate(self) -> type[ModelForm]:
        """Generate a ModelForm class.

        Returns:
            ModelForm subclass with smart widgets and configuration

        Raises:
            ImportError: If custom form_class string path is invalid
        """
        # If user provided a custom form class, use it
        if self.config.form_class is not None:
            if isinstance(self.config.form_class, str):
                from django.utils.module_loading import import_string
                return import_string(self.config.form_class)
            return self.config.form_class

        # Prepare form factory kwargs
        fields = self.get_fields()
        kwargs: dict[str, Any] = {
            "fields": fields if fields else "__all__"
        }

        if self.config.exclude:
            kwargs["exclude"] = self.config.exclude

        # Generate form using Django's modelform_factory
        form_class = modelform_factory(
            self.model,
            form=ModelForm,
            **kwargs
        )

        return form_class


# Export factory classes
__all__ = [
    "ComponentFactory",
    "FormFactory",
    "TableFactory",
    "FilterFactory",
    "AdminFactory",
]
```

### Protocol Definition

```python
"""Factory protocols for type checking."""

from typing import Protocol, TypeVar
from django.db import models

ModelType = TypeVar('ModelType', bound=models.Model, contravariant=True)
ConfigType = TypeVar('ConfigType', contravariant=True)
ComponentType = TypeVar('ComponentType', covariant=True)


class ComponentFactoryProtocol(Protocol[ModelType, ConfigType, ComponentType]):
    """Protocol defining the factory interface.

    Any class implementing this protocol can be used as a factory
    for generating Django components.
    """

    @property
    def model(self) -> type[ModelType]:
        """The Django model class."""
        ...

    @property
    def config(self) -> ConfigType:
        """The component configuration."""
        ...

    def get_fields(self) -> list[str]:
        """Get fields to include in component."""
        ...

    def apply_exclusions(self, fields: list[str]) -> list[str]:
        """Apply exclusions to field list."""
        ...

    def generate(self) -> type[ComponentType]:
        """Generate the component class."""
        ...


def create_component(
    factory: ComponentFactoryProtocol[models.Model, Any, ComponentType]
) -> type[ComponentType]:
    """Create a component using any factory that matches the protocol.

    This function demonstrates how protocols enable duck typing
    while maintaining type safety.

    Args:
        factory: Any object implementing ComponentFactoryProtocol

    Returns:
        The generated component class

    Example:
        >>> form_factory = FormFactory(MyModel, FormConfig())
        >>> form_class = create_component(form_factory)
    """
    return factory.generate()
```

---

## Recommendations

### Immediate Actions (High Priority)

1. **Add type hints to base factory** ✅

   ```python
   class ComponentFactory(Generic[ModelType, ConfigType, ComponentType]):
   ```

2. **Define Protocol for factory interface** ✅

   ```python
   class ComponentFactoryProtocol(Protocol[ModelType, ConfigType, ComponentType]):
   ```

3. **Update docstrings with type parameter documentation** ✅

### Medium Priority

1. **Add Protocol definitions for config classes**

   ```python
   class FormConfigProtocol(Protocol):
       fields: list[str] | str | None
       exclude: list[str] | None
   ```

2. **Create type aliases for common factory types**

   ```python
   FormFactoryType = ComponentFactory[models.Model, FormConfig, ModelForm]
   ```

### Low Priority (Nice to Have)

1. **Add runtime type checking with `typing_extensions.runtime_checkable`**
2. **Create documentation examples showing type checker benefits**
3. **Add mypy configuration for strict type checking**

---

## Conclusion

**The current class-based factory implementation is correct and follows Django best practices.**

The factories in `fairdm/registry/factories.py` match how Django itself implements similar patterns:

- Django admin uses `ModelAdmin` classes
- DRF uses `ViewSet` classes
- django-tables2 uses `Table` classes

All of these use **class-based configuration** with **factory functions** under the hood - exactly what we're doing.

**Recommended improvements are additive**:

- Add type hints using `Protocol` for better IDE support
- Add more comprehensive docstrings
- Consider caching generated classes (already done)

**No architectural changes needed**. The factories are well-designed, testable, and maintainable.

---

## References

1. [Django ModelAdmin Documentation](https://docs.djangoproject.com/en/6.0/ref/contrib/admin/)
2. [Django REST Framework ViewSets](https://www.django-rest-framework.org/api-guide/viewsets/)
3. [django-tables2 Documentation](https://django-tables2.readthedocs.io/)
4. [PEP 544 – Protocols](https://peps.python.org/pep-0544/)
5. [Python typing.Generic](https://docs.python.org/3/library/typing.html#typing.Generic)
6. Django source code: `django/forms/models.py` (modelform_factory)
7. django-tables2 source code: `django_tables2/tables.py` (table_factory)
8. django-filter source code: `django_filters/filterset.py` (filterset_factory)

---

**Next Steps**: Apply type hints and Protocol definitions to existing factory implementation.
