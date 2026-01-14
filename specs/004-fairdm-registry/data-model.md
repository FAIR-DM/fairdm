# Data Model: FairDM Registry System

**Feature**: 004-fairdm-registry
**Date**: 2026-01-12
**Phase**: 1 - Design Specification
**Status**: Implementation-Ready

This document provides complete API specifications for the ModelConfiguration class and related data structures based on Phase 0 research findings.

---

## 1. ModelConfiguration Class

### 1.1 Overview

`ModelConfiguration` is the central configuration class for registered Sample and Measurement models. It uses a decorator pattern (`@register`) and provides three configuration levels:

1. **Simple**: Parent `fields` attribute only (all components inherit)
2. **Intermediate**: Component-specific field overrides (`table_fields`, `form_fields`, etc.)
3. **Advanced**: Custom class overrides (`table_class`, `form_class`, etc.)

### 1.2 Class Definition

```python
from dataclasses import dataclass, field as dataclass_field
from functools import cached_property
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.db import models
    from django.forms import ModelForm
    from django_tables2 import Table
    from django_filters import FilterSet
    from rest_framework.serializers import ModelSerializer
    from import_export.resources import ModelResource
    from django.contrib.admin import ModelAdmin


@dataclass
class ModelConfiguration:
    """Configuration for auto-generating components from Sample/Measurement models.

    This class follows a three-tier configuration pattern:
    1. Parent fields (simplest): `fields = ['name', 'location']`
    2. Component-specific fields: `table_fields = ['name', 'location']`
    3. Custom classes (full control): `table_class = MyCustomTable`

    Examples:
        Basic registration with shared fields::

            @register
            class RockSampleConfig(ModelConfiguration):
                model = RockSample
                fields = ['name', 'location', 'date_collected']
                # All components auto-generate from these fields

        Component-specific field lists::

            @register
            class RockSampleConfig(ModelConfiguration):
                model = RockSample
                fields = ['name', 'location']  # Default for all
                table_fields = ['name', 'location', 'contributor']  # Table shows extra column
                form_fields = ['name', 'description', 'location']  # Form includes description

        Custom class overrides::

            @register
            class RockSampleConfig(ModelConfiguration):
                model = RockSample
                table_class = RockSampleTable  # Custom table with special columns
                form_class = RockSampleForm  # Custom form with validation logic
    """

    # Required Attributes
    model: type['models.Model']
    """Django model class (Sample or Measurement subclass). Required."""

    # Parent Field Configuration (Level 1)
    fields: list[str] = dataclass_field(default_factory=list)
    """Parent field list inherited by all components when component-specific fields not specified.

    Supports:
    - Simple field names: ['name', 'location']
    - Related field paths: ['project__title', 'contributor__name']
    - Empty list = use smart defaults (all user-defined fields, excluding auto-generated)
    """

    exclude: list[str] = dataclass_field(default_factory=list)
    """Fields to exclude from all components.

    Always excluded by default:
    - 'id', 'polymorphic_ctype', 'polymorphic_ctype_id'
    - Fields ending with '_ptr' or '_ptr_id' (multi-table inheritance)
    - Fields with auto_now=True or auto_now_add=True
    - Fields with editable=False
    """

    # Component-Specific Field Lists (Level 2)
    table_fields: list[str] | None = None
    """Fields for django-tables2 Table columns. Overrides parent `fields` for tables only."""

    form_fields: list[str] | None = None
    """Fields for Django ModelForm inputs. Overrides parent `fields` for forms only."""

    filterset_fields: list[str] | None = None
    """Fields for django-filter FilterSet filters. Overrides parent `fields` for filters only."""

    serializer_fields: list[str] | None = None
    """Fields for DRF ModelSerializer. Overrides parent `fields` for serializers only."""

    resource_fields: list[str] | None = None
    """Fields for import_export Resource. Overrides parent `fields` for import/export only."""

    admin_list_display: list[str] | None = None
    """Fields for Django Admin list_display. Overrides parent `fields` for admin list only."""

    # Custom Class Overrides (Level 3)
    form_class: type['ModelForm'] | None = None
    """Custom ModelForm class. Completely replaces auto-generation (ignores all field lists)."""

    table_class: type['Table'] | None = None
    """Custom django-tables2 Table class. Completely replaces auto-generation."""

    filterset_class: type['FilterSet'] | None = None
    """Custom django-filter FilterSet class. Completely replaces auto-generation."""

    serializer_class: type['ModelSerializer'] | None = None
    """Custom DRF ModelSerializer class. Completely replaces auto-generation."""

    resource_class: type['ModelResource'] | None = None
    """Custom import_export Resource class. Completely replaces auto-generation."""

    admin_class: type['ModelAdmin'] | None = None
    """Custom Django Admin ModelAdmin class. Completely replaces auto-generation."""

    # Metadata
    display_name: str = ""
    """Human-readable name for this model (e.g., 'Rock Sample'). Used in UI labels."""

    description: str = ""
    """Detailed description of this model type. Used in documentation and help text."""

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.model is None:
            raise ConfigurationError("ModelConfiguration.model is required")

        # Set display_name from model if not provided
        if not self.display_name:
            self.display_name = self.model._meta.verbose_name.title()

    # Component Access Methods (Public API)

    @cached_property
    def form(self) -> type['ModelForm']:
        """Get or generate ModelForm class.

        Returns custom form_class if provided, otherwise generates form from
        form_fields (or parent fields if form_fields not specified).

        Result is cached automatically via @cached_property.

        Returns:
            ModelForm subclass ready for instantiation

        Raises:
            FieldValidationError: If field names are invalid
            ConfigurationError: If custom form_class doesn't inherit from ModelForm
        """
        if self.form_class is not None:
            return self.form_class

        from fairdm.registry.factories import FormFactory
        factory = FormFactory(self.model, self)
        return factory.generate()

    @cached_property
    def table(self) -> type['Table']:
        """Get or generate django-tables2 Table class.

        Returns custom table_class if provided, otherwise generates table from
        table_fields (or parent fields if table_fields not specified).

        Result is cached automatically via @cached_property.

        Returns:
            Table subclass ready for instantiation with queryset
        """
        if self.table_class is not None:
            return self.table_class

        from fairdm.registry.factories import TableFactory
        factory = TableFactory(self.model, self)
        return factory.generate()

    @cached_property
    def filterset(self) -> type['FilterSet']:
        """Get or generate django-filter FilterSet class.

        Returns custom filterset_class if provided, otherwise generates filterset from
        filterset_fields (or parent fields if filterset_fields not specified).

        Result is cached automatically via @cached_property.

        Returns:
            FilterSet subclass ready for instantiation with queryset
        """
        if self.filterset_class is not None:
            return self.filterset_class

        from fairdm.registry.factories import FilterFactory
        factory = FilterFactory(self.model, self)
        return factory.generate()

    @cached_property
    def serializer(self) -> type['ModelSerializer']:
        """Get or generate DRF ModelSerializer class.

        Returns custom serializer_class if provided, otherwise generates serializer from
        serializer_fields (or parent fields if serializer_fields not specified).

        Result is cached automatically via @cached_property.

        Returns:
            ModelSerializer subclass for REST API endpoints
        """
        if self.serializer_class is not None:
            return self.serializer_class

        from fairdm.registry.factories import SerializerFactory
        factory = SerializerFactory(self.model, self)
        return factory.generate()

    @cached_property
    def resource(self) -> type['ModelResource']:
        """Get or generate import_export Resource class.

        Returns custom resource_class if provided, otherwise generates resource from
        resource_fields (or parent fields if resource_fields not specified).

        Result is cached automatically via @cached_property.

        Returns:
            ModelResource subclass for CSV/Excel import/export
        """
        if self.resource_class is not None:
            return self.resource_class

        from fairdm.registry.factories import ResourceFactory
        factory = ResourceFactory(self.model, self)
        return factory.generate()

    @cached_property
    def admin(self) -> type['ModelAdmin']:
        """Get or generate Django Admin ModelAdmin class.

        Returns custom admin_class if provided, otherwise generates admin configuration
        from admin_list_display (or parent fields if admin_list_display not specified).

        Result is cached automatically via @cached_property.

        Returns:
            ModelAdmin subclass for Django admin site
        """
        if self.admin_class is not None:
            return self.admin_class

        from fairdm.registry.factories import AdminFactory
        factory = AdminFactory(self.model, self)
        return factory.generate()

    def clear_cache(self):
        """Clear all cached component classes.

        Used primarily in testing to force regeneration of components.
        Should not be needed in production code.

        Uses del to remove cached_property values, causing regeneration on next access.
        """
        for attr in ('form', 'table', 'filterset', 'serializer', 'resource', 'admin'):
            try:
                delattr(self, attr)
            except AttributeError:
                pass  # Property not yet cached

    @classmethod
    def get_default_fields(cls, model: type['models.Model']) -> list[str]:
        """Generate smart default field list for a model.

        Includes all user-defined fields while excluding:
        - Technical fields (id, polymorphic_ctype, *_ptr)
        - Auto-generated timestamp fields (auto_now, auto_now_add)
        - Non-editable fields

        Args:
            model: Django model class

        Returns:
            List of field names safe for component generation
        """
        excluded = {
            'id', 'polymorphic_ctype', 'polymorphic_ctype_id'
        }

        fields = []
        for field_obj in model._meta.get_fields():
            # Skip excluded fields
            if field_obj.name in excluded:
                continue

            # Skip pointer fields (multi-table inheritance)
            if field_obj.name.endswith('_ptr') or field_obj.name.endswith('_ptr_id'):
                continue

            # Skip auto-managed timestamp fields
            if getattr(field_obj, 'auto_now', False) or getattr(field_obj, 'auto_now_add', False):
                continue

            # Skip non-editable fields
            if not getattr(field_obj, 'editable', True):
                continue

            fields.append(field_obj.name)

        return fields
```

---

## 2. Field Resolution Algorithm

### 2.1 Overview

Field resolution follows a three-tier precedence chain per component type:

1. **Custom Class** (highest) → If provided, ignore all field configuration
2. **Component-Specific Fields** (middle) → If provided, use instead of parent
3. **Parent Fields** (default) → Fallback when component-specific not specified
4. **Smart Defaults** (last resort) → If parent fields empty, generate defaults

### 2.2 Resolution Pseudocode

```python
def resolve_fields_for_component(config: ModelConfiguration, component_type: str) -> list[str]:
    """Resolve field list for a specific component type.

    Args:
        config: ModelConfiguration instance
        component_type: One of 'table', 'form', 'filterset', 'serializer', 'resource', 'admin'

    Returns:
        List of field names to use for component generation
    """
    # Tier 1: Custom class provided? Return None (class handles its own fields)
    custom_class_attr = f'{component_type}_class'
    if getattr(config, custom_class_attr, None) is not None:
        return None  # Custom class takes full responsibility

    # Tier 2: Component-specific fields provided?
    component_fields_attr = f'{component_type}_fields'
    component_fields = getattr(config, component_fields_attr, None)
    if component_fields is not None:
        return filter_fields_by_component(component_fields, component_type, config.model)

    # Tier 3: Parent fields provided?
    if config.fields:
        return filter_fields_by_component(config.fields, component_type, config.model)

    # Tier 4: Generate smart defaults
    default_fields = ModelConfiguration.get_default_fields(config.model)
    return filter_fields_by_component(default_fields, component_type, config.model)


def filter_fields_by_component(
    fields: list[str],
    component_type: str,
    model: type['models.Model']
) -> list[str]:
    """Filter field list based on component capabilities.

    Different components have different constraints:
    - Forms: Cannot include related field paths (e.g., 'project__title')
    - Tables: Can include related paths, exclude large text fields
    - Filters: Can include related paths, focus on searchable types

    Args:
        fields: Base field list to filter
        component_type: Component being generated
        model: Model class for field introspection

    Returns:
        Filtered field list appropriate for component type
    """
    if component_type == 'form':
        # Forms cannot edit related fields, exclude double-underscore paths
        return [f for f in fields if '__' not in f]

    elif component_type == 'table':
        # Tables exclude large text fields (JSONField, TextField with no max_length)
        filtered = []
        for field_name in fields:
            try:
                field_obj = model._meta.get_field(field_name.split('__')[0])
                if field_obj.__class__.__name__ in ['JSONField', 'TextField']:
                    continue  # Skip large fields
                filtered.append(field_name)
            except:
                filtered.append(field_name)  # Include if can't introspect
        return filtered

    else:
        # Other components accept all fields
        return fields
```

### 2.3 Field Type Mapping

#### 2.3.1 Filter Type Mapping

| Django Field | django-filter Type | Lookup Method |
|--------------|-------------------|---------------|
| CharField | CharFilter | `icontains` (case-insensitive) |
| TextField | CharFilter | `icontains` |
| DateField | DateFromToRangeFilter | `range` |
| DateTimeField | DateTimeFromToRangeFilter | `range` |
| IntegerField | RangeFilter | `range` |
| DecimalField | RangeFilter | `range` |
| BooleanField | BooleanFilter | `exact` |
| ForeignKey | ModelChoiceFilter | `exact` |
| ManyToManyField | ModelMultipleChoiceFilter | `in` |

#### 2.3.2 Form Widget Mapping

| Django Field | Widget | Notes |
|--------------|--------|-------|
| CharField | TextInput | Default text input |
| TextField | Textarea | Multi-line input |
| DateField | DateInput | HTML5 date picker (type='date') |
| DateTimeField | SplitDateTimeWidget | Separate date + time inputs |
| BooleanField | CheckboxInput | Checkbox |
| ForeignKey | Select2Widget | AJAX autocomplete |
| ManyToManyField | Select2MultipleWidget | Multi-select AJAX |
| ImageField | ImageWidget | File upload with preview |
| FileField | FileInput | File upload |

#### 2.3.3 Table Column Mapping

| Django Field | Column Type | Formatting |
|--------------|-------------|------------|
| CharField | Column | Plain text |
| TextField | Column | Truncated to 50 chars |
| DateField | DateColumn | Format: 'Y-m-d' |
| DateTimeField | DateTimeColumn | Format: 'Y-m-d H:i' |
| BooleanField | BooleanColumn | ✓/✗ icons |
| ForeignKey | Column (LinkColumn) | Link to related object |
| ImageField | TemplateColumn | Thumbnail preview |

---

## 3. Validation Rules

### 3.1 Registration-Time Validation

Performed during `@register` decorator execution (in `AppConfig.ready()`):

1. **Model Inheritance**: Model must inherit from Sample or Measurement

   ```python
   if not issubclass(model, (Sample, Measurement)):
       raise RegistryError(f"{model.__name__} must inherit from Sample or Measurement")
   ```

2. **Field Existence**: All fields in `fields`, `table_fields`, etc. must exist on model

   ```python
   for field_name in config.fields:
       try:
           model._meta.get_field(field_name.split('__')[0])
       except FieldDoesNotExist:
           suggestions = get_close_matches(field_name, [f.name for f in model._meta.get_fields()])
           raise FieldValidationError(
               f"Field '{field_name}' does not exist on {model.__name__}. "
               f"Did you mean '{suggestions[0]}'?" if suggestions else ""
           )
   ```

3. **Duplicate Registration**: Model can only be registered once

   ```python
   if model in registry._registry:
       original_location = registry._registry[model].__module__
       raise DuplicateRegistrationError(
           f"{model.__name__} already registered at {original_location}"
       )
   ```

4. **Custom Class Validation**: Custom classes must inherit from expected bases

   ```python
   if config.form_class and not issubclass(config.form_class, ModelForm):
       raise ConfigurationError(
           f"form_class must inherit from django.forms.ModelForm, "
           f"got {config.form_class.__name__}"
       )
   ```

### 3.2 Component Generation-Time Validation

Performed during first `get_X_class()` call (lazy generation):

1. **Type Compatibility Warnings**: Field types suitable for component

   ```python
   if isinstance(field_obj, JSONField) and component_type == 'table':
       warnings.warn(
           f"JSONField '{field_name}' excluded from {model.__name__} table "
           f"(not displayable in table columns)",
           ComponentWarning
       )
   ```

2. **Related Path Validation**: Double-underscore paths must resolve

   ```python
   if '__' in field_name:
       parts = field_name.split('__')
       current_model = model
       for part in parts:
           try:
               field_obj = current_model._meta.get_field(part)
               if field_obj.is_relation:
                   current_model = field_obj.related_model
           except FieldDoesNotExist:
               raise FieldValidationError(f"Invalid path: {field_name}")
   ```

### 3.3 Runtime Validation

Performed by Django/DRF during form submission or API requests:

- Form field validation (clean methods, validators)
- Serializer validation (DRF validators)
- Database constraints (unique, foreign key, etc.)

---

## 4. Exception Hierarchy

```python
# fairdm/registry/exceptions.py

class RegistryError(Exception):
    """Base exception for all registry errors."""
    pass


class ConfigurationError(RegistryError):
    """Invalid ModelConfiguration setup."""

    def __init__(self, message: str, model: type | None = None):
        self.model = model
        if model:
            message = f"{model.__name__}: {message}"
        super().__init__(message)


class FieldValidationError(RegistryError):
    """Invalid field name or field configuration."""

    def __init__(
        self,
        field_name: str,
        model: type,
        suggestion: str | None = None,
        valid_fields: list[str] | None = None
    ):
        self.field_name = field_name
        self.model = model
        self.suggestion = suggestion
        self.valid_fields = valid_fields

        message = f"Field '{field_name}' does not exist on {model.__name__}"

        if suggestion:
            message += f". Did you mean '{suggestion}'?"
        elif valid_fields:
            message += f". Available fields: {', '.join(valid_fields[:5])}"
            if len(valid_fields) > 5:
                message += f" (and {len(valid_fields) - 5} more)"

        super().__init__(message)


class DuplicateRegistrationError(RegistryError):
    """Model registered multiple times."""

    def __init__(self, model: type, original_location: str):
        self.model = model
        self.original_location = original_location
        message = (
            f"{model.__name__} already registered at {original_location}. "
            f"Each model can only be registered once."
        )
        super().__init__(message)


class ComponentGenerationError(RegistryError):
    """Error during component class generation."""

    def __init__(self, component_type: str, model: type, original_exception: Exception):
        self.component_type = component_type
        self.model = model
        self.original_exception = original_exception
        message = (
            f"Failed to generate {component_type} for {model.__name__}: "
            f"{original_exception.__class__.__name__}: {original_exception}"
        )
        super().__init__(message)
```

---

## 5. Caching Strategy

### 5.1 Using @cached_property

Python's `@cached_property` decorator (from `functools`) provides automatic caching:

- **Automatic**: No manual cache checking needed
- **Thread-safe**: Built-in thread safety (Python 3.8+)
- **Standard**: Uses Python's standard library pattern
- **Clean**: No boilerplate cache attributes needed

### 5.2 Component Properties

Each component is accessed via a cached property:

- `config.form` → ModelForm class
- `config.table` → Table class
- `config.filterset` → FilterSet class
- `config.serializer` → ModelSerializer class
- `config.resource` → ModelResource class
- `config.admin` → ModelAdmin class

### 5.3 How It Works

```python
@cached_property
def form(self) -> type[ModelForm]:
    """Get or generate ModelForm class."""
    # Check for custom class first
    if self.form_class is not None:
        return self.form_class

    # Generate (cached_property handles caching automatically)
    from fairdm.registry.factories import FormFactory
    factory = FormFactory(self.model, self)
    return factory.generate()
```

**First access**: Method executes, result cached
**Subsequent accesses**: Cached value returned immediately

### 5.4 Cache Invalidation

Cache can be cleared manually (primarily for testing):

```python
config.clear_cache()  # Deletes all cached properties

# Next access will regenerate
form_class = config.form  # Regenerated
```

Implementation uses `delattr()` to remove cached values:

```python
def clear_cache(self):
    for attr in ('form', 'table', 'filterset', 'serializer', 'resource', 'admin'):
        try:
            delattr(self, attr)
        except AttributeError:
            pass  # Not yet cached
```

**Thread Safety**: `@cached_property` is thread-safe. Multiple threads accessing the same property will safely generate once.

---

## 6. Type Hints & Protocols

Complete type definitions are provided in `contracts/` directory (see Phase 1 deliverable).

Key protocols:

- `ComponentFactory` - Factory interface for all component generators
- `FieldResolver` - Field list resolution and filtering
- `ModelConfigurationProtocol` - Public API for ModelConfiguration

---

## 7. Implementation Checklist

### 7.1 ModelConfiguration Refactoring

- [ ] Remove nested config attributes (form, table, filters, admin)
- [ ] Add component-specific field attributes (table_fields, form_fields, etc.)
- [ ] **Convert get_X_class() methods to @cached_property decorated properties**
  - [ ] `get_form_class()` → `@cached_property def form()`
  - [ ] `get_table_class()` → `@cached_property def table()`
  - [ ] `get_filterset_class()` → `@cached_property def filterset()`
  - [ ] `get_serializer_class()` → `@cached_property def serializer()`
  - [ ] `get_resource_class()` → `@cached_property def resource()`
  - [ ] `get_admin_class()` → `@cached_property def admin()`
- [ ] Update clear_cache() to use delattr() for cached properties
- [ ] Update **post_init** validation
- [ ] Update get_default_fields() to exclude polymorphic fields
- [ ] Add functools import for cached_property

### 7.2 Factory Updates

- [ ] Update factories to use component-specific fields from config
- [ ] Implement field resolution algorithm in each factory
- [ ] Add field type mapping logic
- [ ] Add component-specific field filtering
- [ ] Update error messages to reference new field attributes

### 7.3 Exception Classes

- [ ] Create exceptions.py with full exception hierarchy
- [ ] Implement FieldValidationError with fuzzy matching
- [ ] Implement DuplicateRegistrationError with location tracking
- [ ] Implement ComponentGenerationError with context

### 7.4 Validation

- [ ] Implement registration-time validation in registry.register()
- [ ] Add Django check framework integration
- [ ] Implement component generation-time warnings
- [ ] Add field name suggestion (difflib.get_close_matches)

### 7.5 Testing

- [ ] Unit tests for field resolution algorithm (all 3 tiers)
- [ ] Unit tests for field type mapping
- [ ] Unit tests for validation (registration + generation)
- [ ] Integration tests for lazy generation + caching
- [ ] Contract tests for get_X_class() methods
- [ ] Test cache invalidation (clear_cache())

### 7.6 Documentation

- [ ] Update fairdm_demo configs to new API
- [ ] Add docstrings linking to documentation
- [ ] Create quickstart.md with examples
- [ ] Update registry documentation with new patterns

---

## 8. Performance Expectations

Based on Phase 0 research (R2):

### 8.1 Registration Time

- Configuration validation: **<10ms per model**
- Total startup overhead (20 models): **<200ms**

### 8.2 Component Generation (First Access)

- Form generation: **30-50ms**
- Table generation: **40-60ms**
- FilterSet generation: **20-40ms**
- Serializer generation: **30-50ms**
- Resource generation: **20-30ms**
- Admin generation: **10-20ms**

### 8.3 Cached Access (Subsequent)

- All components: **<1ms** (dictionary lookup)

### 8.4 Total System Impact

- 20 models × 6 components = 120 components
- Eager generation: 1.3-2.2 seconds EVERY startup
- Lazy + caching: ~100ms startup + ~60-300ms one-time first-request cost

**Result**: Lazy generation is 10-20x faster for typical workflows.

---

## Summary

This data model specification provides:

✅ Complete ModelConfiguration class definition with type hints
✅ Three-tier field resolution algorithm (custom class > component fields > parent fields)
✅ Field type mapping for all 6 component types
✅ Validation rules (registration, generation, runtime)
✅ Exception hierarchy with helpful error messages
✅ Lazy generation + caching strategy
✅ Performance benchmarks
✅ Implementation checklist

**Status**: Implementation-ready. All Phase 0 research decisions incorporated.
