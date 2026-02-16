# Research Task R3: Validation Timing & Strategy

**Date**: 2026-01-12
**Status**: Complete
**Related**: [plan.md](./plan.md), [spec.md](./spec.md)

---

## Executive Summary

**Decision**: Validate configuration structure and field existence at **registration time** (during `AppConfig.ready()`), but defer field type compatibility and data validation to **component generation time**. Use Django's check framework for system-wide validation reporting.

**Key Findings**:
- Django's check framework provides standardized error reporting that integrates with `manage.py check`
- Field validation should happen early (registration) to catch typos before runtime
- Type compatibility needs model introspection, best done during component generation
- Error messages should follow Django's pattern: descriptive + hint + error code
- Use `difflib` for "Did you mean?" suggestions on field name typos

---

## 1. Current Implementation Analysis

### 1.1 Existing Validation in registry.py

Current validation in [fairdm/registry/registry.py](../../fairdm/registry/registry.py):

```python
def _validate_model_class(self, model_class):
    """
    Validate that the model class is a subclass of Sample or Measurement.

    Args:
        model_class: The Django model class to validate

    Raises:
        ValueError: If model is not a Sample or Measurement subclass
    """
    try:
        from fairdm.core.measurement.models import Measurement
        from fairdm.core.sample.models import Sample

        if not (issubclass(model_class, Sample) or issubclass(model_class, Measurement)):
            raise TypeError(
                f"Model {model_class.__name__} must be a subclass of "
                f"fairdm.core.sample.models.Sample or fairdm.core.measurement.models.Measurement"
            )
    except ImportError as e:
        raise ImportError(
            f"Could not import Sample or Measurement models to validate {model_class.__name__}: {e}"
        ) from e
```

**Analysis**:
- ✅ Good: Validates inheritance at registration time
- ✅ Good: Clear error message with qualified class names
- ❌ Missing: Field existence validation
- ❌ Missing: Duplicate registration check (FR-013)
- ❌ Missing: Field name suggestions
- ❌ Missing: Error codes for filtering

### 1.2 Validation in Other FairDM Components

From [fairdm/conf/checks.py](../../fairdm/conf/checks.py):

```python
def validate_services(env_profile: str, settings_dict: dict[str, Any]) -> None:
    """
    Validate that required services are configured correctly.

    Raises:
        ImproperlyConfigured: In production/staging if required services are missing
    """
    is_production_like = env_profile in ("production", "staging")
    errors = []
    warnings_list = []

    # Collect all errors first
    if not default_db:
        msg = "DATABASES['default'] is not configured. Set DATABASE_URL environment variable."
        if is_production_like:
            errors.append(msg)
        else:
            warnings_list.append(msg)

    # Report all at once
    if errors:
        error_message = "\n".join(errors)
        raise ImproperlyConfigured(f"Configuration errors:\n{error_message}")
```

**Pattern**: Collect all errors, report together with actionable messages.

---

## 2. Django Check Framework Research

### 2.1 Overview

Django provides `django.core.checks` for system-wide validation:

```python
from django.core import checks
from django.core.checks import Error, Warning, Info

@checks.register(checks.Tags.models)
def check_registry_configuration(app_configs, **kwargs):
    """Validate all registered model configurations."""
    errors = []

    for model, config in registry._registry.items():
        # Validate field existence
        for field_name in config.fields:
            try:
                model._meta.get_field(field_name)
            except FieldDoesNotExist:
                errors.append(
                    Error(
                        f"Field '{field_name}' does not exist on model {model.__name__}",
                        hint=f"Available fields: {', '.join(get_field_names(model))}",
                        obj=config,
                        id='fairdm.E001',
                    )
                )

    return errors
```

**Benefits**:
- ✅ Runs automatically with `manage.py check`, `runserver`, `migrate`
- ✅ Standardized error format across Django ecosystem
- ✅ Can be filtered by tags (e.g., `--tag fairdm`)
- ✅ Distinguishes Error (blocking) vs Warning (non-blocking)
- ✅ Supports hints for fixing issues

### 2.2 Error Message Components

Django checks use structured messages:

```python
Error(
    msg="Field 'publihsed_at' does not exist on Book model",  # What's wrong
    hint="Did you mean 'published_at'? Available fields: title, author, published_at",  # How to fix
    obj=config_instance,  # Context object
    id='fairdm.E001',  # Unique identifier for filtering/documentation
)
```

### 2.3 Integration Point

Register checks in [fairdm/apps.py](../../fairdm/apps.py):

```python
class FairDMConfig(AppConfig):
    name = "fairdm"

    def ready(self) -> None:
        # Existing autodiscovery
        autodiscover_modules("config")
        autodiscover_modules("plugins")

        # Register registry checks
        from fairdm.registry import checks as registry_checks

        return super().ready()
```

---

## 3. Validation Timing Decision

### 3.1 What to Validate When

| Validation Type | Timing | Reason | Error Level |
|----------------|--------|---------|-------------|
| **Model Inheritance** | Registration | Fast, prevents invalid registrations | Error |
| **Duplicate Registration** | Registration | Must prevent overwrites | Error |
| **Field Existence** | Registration | Catches typos early, simple check | Error |
| **Field Name Format** | Registration | Regex validation for `__` paths | Error |
| **Field Type Compatibility** | Component Generation | Needs full model introspection | Warning |
| **Field Accessibility** | Component Generation | Needs permission checks | Warning |
| **Data Validation** | Runtime | Depends on user input | Form errors |

### 3.2 Registration Time Validation

**When**: During `registry.register()` in `AppConfig.ready()`

**What**:
```python
def register(self, model_class, config=None):
    """Register with validation."""

    # 1. Validate model inheritance (existing)
    self._validate_model_class(model_class)

    # 2. Check for duplicate registration (FR-013)
    if model_class in self._registry:
        existing_config = self._registry[model_class]
        raise DuplicateRegistrationError(
            f"Model {model_class.__name__} is already registered.\n"
            f"Original registration: {existing_config.__class__.__module__}."
            f"{existing_config.__class__.__name__}\n"
            f"Duplicate attempt: {config.__class__.__module__}.{config.__class__.__name__}"
        )

    # 3. Validate field names exist (FR-012)
    self._validate_field_names(model_class, config)

    # Continue with registration...
```

### 3.3 Component Generation Time Validation

**When**: First access to `config.get_form_class()`, etc.

**What**:
```python
def get_form_class(self):
    """Get or generate form class with type validation."""
    if self._form_class_cache is not None:
        return self._form_class_cache

    # Validate field types are form-compatible
    incompatible_fields = []
    for field_name in self.form_fields or self.fields:
        field = self.model._meta.get_field(field_name)
        if not is_form_compatible(field):
            incompatible_fields.append((field_name, type(field).__name__))

    if incompatible_fields:
        warnings.warn(
            f"Fields {incompatible_fields} may not render correctly in forms",
            category=ConfigurationWarning
        )

    # Generate form
    form_class = self._generate_form()
    self._form_class_cache = form_class
    return form_class
```

---

## 4. Field Validation Strategy

### 4.1 Field Existence Validation

```python
def _validate_field_names(self, model_class, config):
    """
    Validate that all configured field names exist on the model.

    Provides helpful suggestions for typos using difflib.
    """
    from difflib import get_close_matches
    from django.core.exceptions import FieldDoesNotExist

    # Get all configured fields
    all_fields = set()
    for attr in ['fields', 'form_fields', 'table_fields', 'filterset_fields', 'resource_fields']:
        fields = getattr(config, attr, None)
        if fields:
            all_fields.update(fields)

    # Get valid field names from model
    valid_fields = {f.name for f in model_class._meta.get_fields()}

    errors = []
    for field_name in all_fields:
        # Handle relationship paths (e.g., "author__name")
        base_field = field_name.split('__')[0]

        if base_field not in valid_fields:
            # Find similar field names
            suggestions = get_close_matches(base_field, valid_fields, n=3, cutoff=0.6)

            hint = f"Available fields: {', '.join(sorted(valid_fields)[:10])}"
            if suggestions:
                hint = f"Did you mean '{suggestions[0]}'? " + hint

            errors.append(
                f"Field '{field_name}' does not exist on {model_class.__name__}. {hint}"
            )

        # Validate relationship path
        if '__' in field_name:
            try:
                self._validate_relationship_path(model_class, field_name)
            except FieldDoesNotExist as e:
                errors.append(str(e))

    if errors:
        raise ConfigurationError('\n'.join(errors))
```

### 4.2 Relationship Path Validation

```python
def _validate_relationship_path(self, model_class, field_path):
    """
    Validate a relationship path like 'author__books__title'.

    Follows the same logic as Django's ORM lookups.
    """
    from django.core.exceptions import FieldDoesNotExist

    parts = field_path.split('__')
    current_model = model_class

    for i, part in enumerate(parts[:-1]):  # All but last part must be relations
        try:
            field = current_model._meta.get_field(part)
        except FieldDoesNotExist:
            path_so_far = '__'.join(parts[:i+1])
            raise FieldDoesNotExist(
                f"Cannot resolve field path '{field_path}': "
                f"'{part}' is not a valid field on {current_model.__name__} "
                f"(at '{path_so_far}')"
            )

        # Check if it's a relation
        if not (field.is_relation or field.many_to_many):
            raise ConfigurationError(
                f"Field '{part}' in path '{field_path}' is not a relation "
                f"(it's a {type(field).__name__})"
            )

        # Move to related model
        current_model = field.related_model

    # Validate final field exists
    final_field = parts[-1]
    try:
        current_model._meta.get_field(final_field)
    except FieldDoesNotExist:
        raise FieldDoesNotExist(
            f"Cannot resolve field path '{field_path}': "
            f"'{final_field}' does not exist on {current_model.__name__}"
        )
```

---

## 5. Error Message Best Practices

### 5.1 Patterns from Django Ecosystem

**Django Core**:
```python
# Pattern: "Problem. Hint. Code."
Error(
    "Model MySample must be a subclass of Sample or Measurement",
    hint="Check that your model inherits from fairdm.core.Sample",
    id="fairdm.E001"
)
```

**Django REST Framework**:
```python
# Pattern: Descriptive validation errors with codes
ValidationError({
    'field_name': [
        ErrorDetail("Enter a valid value.", code='invalid'),
        ErrorDetail("This field is required.", code='required')
    ]
})
```

**django-tables2**:
```python
# Pattern: Runtime errors with context
TypeError(
    f"Table.Meta.fields = {value.__repr__()} (type {type(value).__name__}), "
    f"but type must be one of (list, tuple, set)"
)
```

**django-filter**:
```python
# Pattern: Helpful field lookup errors
FieldLookupError(
    f"Unsupported lookup '{lookup_expr}' for field '{model._meta}.{field_name}'."
)
```

### 5.2 FairDM Error Message Pattern

```python
class RegistryError(Exception):
    """Base class for registry errors."""

    def __init__(self, message, hint=None, obj=None):
        self.message = message
        self.hint = hint
        self.obj = obj
        super().__init__(message)

    def __str__(self):
        msg = self.message
        if self.hint:
            msg += f"\nHint: {self.hint}"
        if self.obj:
            msg += f"\nObject: {self.obj}"
        return msg


class ConfigurationError(RegistryError):
    """Raised when model configuration is invalid."""
    pass


class DuplicateRegistrationError(RegistryError):
    """Raised when a model is registered twice."""
    pass


class FieldValidationError(RegistryError):
    """Raised when field configuration is invalid."""

    def __init__(self, model, field_name, message, suggestions=None):
        self.model = model
        self.field_name = field_name
        self.suggestions = suggestions

        hint = None
        if suggestions:
            hint = f"Did you mean: {', '.join(suggestions)}?"

        super().__init__(
            f"Invalid field '{field_name}' in {model.__name__} configuration: {message}",
            hint=hint,
            obj=model
        )
```

---

## 6. Django Check Framework Integration

### 6.1 Recommended Implementation

Create [fairdm/registry/checks.py](../../fairdm/registry/checks.py):

```python
"""
Django system checks for FairDM registry.

Validates registry configuration at application startup.
"""

from django.core import checks
from django.core.checks import Error, Warning, Info
from difflib import get_close_matches

from fairdm.registry import registry


def check_registry_fields(app_configs, **kwargs):
    """
    Validate that all configured fields exist on their models.

    Error Codes:
    - fairdm.E001: Field does not exist on model
    - fairdm.E002: Invalid relationship path
    - fairdm.E003: Duplicate model registration
    """
    errors = []

    for model, config in registry._registry.items():
        # Check for field existence
        errors.extend(_check_fields_exist(model, config))

        # Check relationship paths
        errors.extend(_check_relationship_paths(model, config))

    return errors


def _check_fields_exist(model, config):
    """Check that all configured fields exist on the model."""
    errors = []

    # Collect all field references
    all_fields = set()
    for attr in ['fields', 'form_fields', 'table_fields', 'filterset_fields']:
        fields = getattr(config, attr, None)
        if fields:
            all_fields.update(fields)

    # Get valid fields
    valid_fields = {f.name for f in model._meta.get_fields()}

    for field_name in all_fields:
        base_field = field_name.split('__')[0]

        if base_field not in valid_fields:
            # Find suggestions
            suggestions = get_close_matches(base_field, valid_fields, n=3, cutoff=0.6)

            hint = f"Available fields: {', '.join(sorted(valid_fields)[:10])}"
            if suggestions:
                hint = f"Did you mean '{suggestions[0]}'? {hint}"

            errors.append(
                Error(
                    f"Field '{field_name}' does not exist on {model._meta.label}",
                    hint=hint,
                    obj=config,
                    id='fairdm.E001',
                )
            )

    return errors


def _check_relationship_paths(model, config):
    """Validate relationship paths like 'author__books__title'."""
    errors = []

    # Get all fields with __ notation
    relation_fields = set()
    for attr in ['fields', 'form_fields', 'table_fields', 'filterset_fields']:
        fields = getattr(config, attr, None)
        if fields:
            relation_fields.update(f for f in fields if '__' in f)

    for field_path in relation_fields:
        try:
            _validate_path(model, field_path)
        except Exception as e:
            errors.append(
                Error(
                    f"Invalid relationship path '{field_path}' on {model._meta.label}",
                    hint=str(e),
                    obj=config,
                    id='fairdm.E002',
                )
            )

    return errors


def _validate_path(model, field_path):
    """Validate a field path exists and is navigable."""
    from django.core.exceptions import FieldDoesNotExist

    parts = field_path.split('__')
    current_model = model

    for i, part in enumerate(parts[:-1]):
        try:
            field = current_model._meta.get_field(part)
        except FieldDoesNotExist:
            raise ValueError(f"Field '{part}' not found on {current_model._meta.label}")

        if not hasattr(field, 'related_model'):
            raise ValueError(f"Field '{part}' is not a relationship field")

        current_model = field.related_model

    # Check final field
    final = parts[-1]
    try:
        current_model._meta.get_field(final)
    except FieldDoesNotExist:
        raise ValueError(f"Field '{final}' not found on {current_model._meta.label}")


# Register the check
checks.register(check=check_registry_fields, tags=['fairdm', 'models'])
```

### 6.2 Load Checks in AppConfig

Update [fairdm/apps.py](../../fairdm/apps.py):

```python
class FairDMConfig(AppConfig):
    name = "fairdm"

    def ready(self) -> None:
        # Autodiscovery
        autodiscover_modules("config")
        autodiscover_modules("plugins")

        # Import checks to register them
        from fairdm.registry import checks as registry_checks  # noqa: F401

        # Existing patches
        from django_filters import compat
        compat.is_crispy = lambda: False

        return super().ready()
```

---

## 7. Field Name Suggestion Algorithm

### 7.1 Using difflib for Fuzzy Matching

```python
from difflib import get_close_matches

def suggest_field_names(invalid_name: str, valid_names: list[str]) -> list[str]:
    """
    Suggest valid field names similar to the invalid name.

    Uses SequenceMatcher for fuzzy matching with 60% similarity threshold.

    Args:
        invalid_name: The field name that was not found
        valid_names: List of valid field names on the model

    Returns:
        List of up to 3 suggestions, ordered by similarity

    Examples:
        >>> suggest_field_names('publihsed_at', ['title', 'author', 'published_at'])
        ['published_at']

        >>> suggest_field_names('auther', ['title', 'author', 'published_at'])
        ['author']
    """
    return get_close_matches(invalid_name, valid_names, n=3, cutoff=0.6)
```

### 7.2 Enhanced Error Messages with Suggestions

```python
def format_field_error(model, field_name, valid_fields):
    """Format a helpful field validation error message."""
    suggestions = suggest_field_names(field_name, valid_fields)

    # Build message
    msg = f"Field '{field_name}' does not exist on {model.__name__}"

    # Add suggestions if found
    if suggestions:
        if len(suggestions) == 1:
            msg += f"\n  Did you mean '{suggestions[0]}'?"
        else:
            suggestions_str = "', '".join(suggestions)
            msg += f"\n  Did you mean one of: '{suggestions_str}'?"

    # Add available fields (first 10)
    available = ', '.join(sorted(valid_fields)[:10])
    if len(valid_fields) > 10:
        available += f', ... ({len(valid_fields) - 10} more)'
    msg += f"\n  Available fields: {available}"

    return msg
```

**Example Output**:
```
Field 'publihsed_at' does not exist on Article
  Did you mean 'published_at'?
  Available fields: author, content, created_at, id, published_at, title, updated_at
```

---

## 8. Validation Categories & Strategies

### 8.1 Model Inheritance Validation

**Requirement**: FR-002
**Timing**: Registration
**Severity**: Error (blocking)

```python
def validate_model_inheritance(model_class):
    """Ensure model inherits from Sample or Measurement."""
    from fairdm.core.measurement.models import Measurement
    from fairdm.core.sample.models import Sample

    if not issubclass(model_class, (Sample, Measurement)):
        raise TypeError(
            f"Model {model_class.__name__} must inherit from "
            f"fairdm.core.Sample or fairdm.core.Measurement"
        )
```

### 8.2 Field Existence Validation

**Requirement**: FR-012
**Timing**: Registration
**Severity**: Error (blocking)

```python
def validate_field_existence(model_class, field_names):
    """Check that all field names exist on the model."""
    valid_fields = {f.name for f in model_class._meta.get_fields()}
    invalid_fields = []

    for field_name in field_names:
        base_field = field_name.split('__')[0]
        if base_field not in valid_fields:
            invalid_fields.append(field_name)

    if invalid_fields:
        raise FieldValidationError(
            model=model_class,
            field_name=', '.join(invalid_fields),
            message="Fields do not exist on model",
            suggestions=suggest_field_names(invalid_fields[0], valid_fields)
        )
```

### 8.3 Field Type Compatibility Validation

**Requirement**: FR-012
**Timing**: Component generation
**Severity**: Warning (non-blocking)

```python
import warnings

def validate_field_type_compatibility(model_class, field_names, component_type):
    """Warn about fields that may not work well with the component type."""
    incompatible = []

    for field_name in field_names:
        field = model_class._meta.get_field(field_name.split('__')[0])

        if component_type == 'table' and isinstance(field, models.FileField):
            incompatible.append((field_name, "FileField may not display properly in tables"))

        elif component_type == 'filter' and isinstance(field, models.TextField):
            incompatible.append((field_name, "TextField filtering may be slow"))

    for field_name, reason in incompatible:
        warnings.warn(
            f"{model_class.__name__}.{field_name}: {reason}",
            category=ConfigurationWarning,
            stacklevel=2
        )
```

### 8.4 Duplicate Registration Validation

**Requirement**: FR-013
**Timing**: Registration
**Severity**: Error (blocking)

```python
def validate_no_duplicate_registration(registry_dict, model_class, new_config):
    """Prevent duplicate model registration."""
    if model_class in registry_dict:
        existing = registry_dict[model_class]
        raise DuplicateRegistrationError(
            f"Model {model_class._meta.label} is already registered",
            hint=f"Original: {existing.__class__.__module__}.{existing.__class__.__name__}\n"
                 f"Duplicate: {new_config.__class__.__module__}.{new_config.__class__.__name__}"
        )
```

---

## 9. Testing Strategy

### 9.1 Registration-Time Validation Tests

```python
# tests/test_registry/test_validation.py

class RegistrationValidationTests(TestCase):
    """Test validation at registration time."""

    def test_invalid_model_inheritance(self):
        """Non-Sample/Measurement models should raise TypeError."""
        with self.assertRaises(TypeError) as cm:
            @register
            class InvalidConfig(ModelConfiguration):
                model = User  # Not Sample or Measurement

        self.assertIn("must inherit from", str(cm.exception))

    def test_invalid_field_name(self):
        """Invalid field names should raise FieldValidationError with suggestions."""
        with self.assertRaises(FieldValidationError) as cm:
            @register
            class BadFieldConfig(ModelConfiguration):
                model = Sample
                fields = ['publihsed_at']  # Typo

        error = str(cm.exception)
        self.assertIn("publihsed_at", error)
        self.assertIn("Did you mean 'published_at'", error)

    def test_invalid_relationship_path(self):
        """Invalid relationship paths should raise clear errors."""
        with self.assertRaises(FieldValidationError) as cm:
            @register
            class BadPathConfig(ModelConfiguration):
                model = Measurement
                fields = ['sample__invalid__field']

        error = str(cm.exception)
        self.assertIn("sample__invalid__field", error)
        self.assertIn("not found", error)

    def test_duplicate_registration(self):
        """Duplicate registration should raise DuplicateRegistrationError."""
        @register
        class FirstConfig(ModelConfiguration):
            model = Sample

        with self.assertRaises(DuplicateRegistrationError) as cm:
            @register
            class SecondConfig(ModelConfiguration):
                model = Sample  # Already registered

        error = str(cm.exception)
        self.assertIn("already registered", error)
        self.assertIn("FirstConfig", error)
```

### 9.2 Django Check Framework Tests

```python
# tests/test_registry/test_checks.py

from django.core.management import call_command
from django.test import TestCase

class RegistryCheckTests(TestCase):
    """Test Django system checks for registry."""

    def test_check_command_reports_field_errors(self):
        """manage.py check should report field validation errors."""
        # Register config with invalid fields
        @register
        class BadConfig(ModelConfiguration):
            model = Sample
            fields = ['nonexistent_field']

        # Run checks
        from io import StringIO
        stderr = StringIO()
        with self.assertRaises(SystemCheckError):
            call_command('check', '--tag', 'fairdm', stderr=stderr)

        output = stderr.getvalue()
        self.assertIn('fairdm.E001', output)
        self.assertIn('nonexistent_field', output)

    def test_check_suggests_similar_fields(self):
        """Checks should suggest similar field names."""
        @register
        class TypoConfig(ModelConfiguration):
            model = Sample
            fields = ['createdAt']  # Should suggest 'created_at'

        from io import StringIO
        stderr = StringIO()
        with self.assertRaises(SystemCheckError):
            call_command('check', stderr=stderr)

        output = stderr.getvalue()
        self.assertIn("Did you mean 'created_at'", output)
```

### 9.3 Component Generation Validation Tests

```python
# tests/test_registry/test_component_validation.py

class ComponentValidationTests(TestCase):
    """Test validation during component generation."""

    def test_warn_incompatible_field_types(self):
        """Should warn about field types incompatible with component."""
        @register
        class FileFieldConfig(ModelConfiguration):
            model = Sample
            table_fields = ['file']  # FileField in table

        config = registry.get_for_model(Sample)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            table_class = config.get_table_class()

            # Should warn about FileField in table
            self.assertEqual(len(w), 1)
            self.assertIn("FileField", str(w[0].message))
            self.assertIn("may not display properly", str(w[0].message))
```

---

## 10. Alternatives Considered

### 10.1 Strict vs Lenient Validation

**Option A: Strict (Recommended)**
- ✅ Catch errors early
- ✅ Prevents runtime failures
- ✅ Better developer experience
- ❌ May be too restrictive for advanced use cases

**Option B: Lenient**
- ✅ More flexible
- ✅ Allows experimentation
- ❌ Errors appear at runtime
- ❌ Harder to debug

**Decision**: **Strict validation with escape hatches** (warnings for type compatibility, errors for field existence)

### 10.2 Validation Location

**Option A: In Registration Decorator (Recommended)**
- ✅ Immediate feedback
- ✅ Fails fast
- ✅ Clear stack traces

**Option B: Lazy Validation**
- ✅ Faster startup
- ❌ Errors appear later
- ❌ Harder to trace

**Decision**: **Registration-time validation** for structure, **component-generation-time warnings** for compatibility

### 10.3 Error Reporting Mechanism

**Option A: Django Checks (Recommended)**
- ✅ Standard Django pattern
- ✅ Integrates with tooling
- ✅ Filterable by tag

**Option B: Custom Exception Handler**
- ✅ More control
- ❌ Non-standard
- ❌ Doesn't integrate with `manage.py check`

**Decision**: **Use Django checks** for system-wide validation

---

## 11. Implementation Recommendations

### 11.1 Exception Hierarchy

```python
# fairdm/registry/exceptions.py

class RegistryError(Exception):
    """Base exception for all registry errors."""
    pass

class ConfigurationError(RegistryError):
    """Raised when configuration is invalid."""
    pass

class FieldValidationError(RegistryError):
    """Raised when field configuration is invalid."""
    pass

class DuplicateRegistrationError(RegistryError):
    """Raised when a model is registered multiple times."""
    pass

class ComponentGenerationError(RegistryError):
    """Raised when component auto-generation fails."""
    pass
```

### 11.2 Error Codes

```python
# Django check error codes
REGISTRY_ERROR_CODES = {
    'fairdm.E001': 'Field does not exist on model',
    'fairdm.E002': 'Invalid relationship path',
    'fairdm.E003': 'Duplicate model registration',
    'fairdm.W001': 'Field type may be incompatible with component',
    'fairdm.W002': 'Large number of fields may impact performance',
    'fairdm.I001': 'Using auto-generated component',
}
```

### 11.3 Validation Order

1. **AppConfig.ready()** - Autodiscover configs
2. **@register decorator** - Validate immediately:
   - Model inheritance ✓
   - Duplicate registration ✓
   - Field existence ✓
   - Relationship paths ✓
3. **manage.py check** - Run Django checks:
   - Report all validation errors
   - Provide suggestions
4. **Component Generation** - First access:
   - Warn about type incompatibilities
   - Cache generated classes

---

## 12. Code Examples

### 12.1 Complete Validation Function

```python
def validate_configuration(model_class, config):
    """
    Validate a model configuration at registration time.

    Raises:
        ConfigurationError: If configuration is invalid
        FieldValidationError: If field references are invalid
        DuplicateRegistrationError: If model already registered
    """
    errors = []

    # 1. Validate model inheritance
    try:
        validate_model_inheritance(model_class)
    except TypeError as e:
        errors.append(str(e))

    # 2. Check for duplicates
    if model_class in registry._registry:
        existing = registry._registry[model_class]
        errors.append(
            f"Model {model_class._meta.label} already registered as "
            f"{existing.__class__.__name__}"
        )

    # 3. Validate all field references
    all_fields = collect_field_names(config)
    valid_fields = {f.name for f in model_class._meta.get_fields()}

    for field_name in all_fields:
        base_field = field_name.split('__')[0]

        if base_field not in valid_fields:
            suggestions = suggest_field_names(base_field, valid_fields)
            error = format_field_error(model_class, field_name, valid_fields)
            errors.append(error)

        # Validate relationship paths
        if '__' in field_name:
            try:
                validate_relationship_path(model_class, field_name)
            except Exception as e:
                errors.append(f"Invalid path '{field_name}': {e}")

    # Report all errors at once
    if errors:
        error_msg = '\n\n'.join(errors)
        raise ConfigurationError(
            f"Invalid configuration for {model_class.__name}:\n\n{error_msg}"
        )
```

### 12.2 User-Friendly Error Example

**Before (generic error)**:
```
FieldDoesNotExist: Sample has no field named 'publihsed_at'
```

**After (with suggestions)**:
```
Field 'publihsed_at' does not exist on Sample
  Did you mean 'published_at'?
  Available fields: created_at, description, id, name, project, published_at, status, updated_at

Hint: Check your ModelConfiguration.fields list in fairdm_demo/config.py
Error Code: fairdm.E001
```

---

## 13. References

### 13.1 Django Documentation
- [System Check Framework](https://docs.djangoproject.com/en/5.1/topics/checks/)
- [Check Messages API](https://docs.djangoproject.com/en/5.1/ref/checks/)
- [Field Lookups](https://docs.djangoproject.com/en/5.1/ref/models/lookups/)

### 13.2 Related Code
- [fairdm/registry/registry.py](../../fairdm/registry/registry.py)
- [fairdm/conf/checks.py](../../fairdm/conf/checks.py)
- [django-tables2 validation](https://github.com/jieter/django-tables2)
- [django-filter exceptions](https://github.com/carltongibson/django-filter/blob/main/django_filters/exceptions.py)

### 13.3 Python Standard Library
- [difflib](https://docs.python.org/3/library/difflib.html) - Fuzzy string matching
- [warnings](https://docs.python.org/3/library/warnings.html) - Warning control

---

## 14. Next Steps

### 14.1 Implementation Priority

1. **Phase 1**: Registration-time validation (Week 1)
   - Add field existence checks
   - Implement duplicate registration prevention
   - Add field name suggestions with difflib

2. **Phase 2**: Django checks integration (Week 1)
   - Create fairdm/registry/checks.py
   - Register checks in AppConfig.ready()
   - Add error codes

3. **Phase 3**: Component generation warnings (Week 2)
   - Add type compatibility checks
   - Implement performance warnings
   - Document warning categories

4. **Phase 4**: Testing & Documentation (Week 2)
   - Write comprehensive test suite
   - Document error codes
   - Create troubleshooting guide

### 14.2 Documentation Needs

- Error code reference (like Django's)
- Troubleshooting guide
- Migration guide for existing configs
- Best practices for field configuration

---

## 15. Conclusion

**Recommended Approach**:

1. ✅ **Use Django's check framework** for standardized validation reporting
2. ✅ **Validate at registration time** for field existence and structure
3. ✅ **Warn at component generation** for type compatibility issues
4. ✅ **Provide helpful suggestions** using difflib for typos
5. ✅ **Use structured exceptions** with codes, hints, and context
6. ✅ **Follow Django patterns** for consistency and familiarity

This approach provides **excellent developer experience** by:
- Catching errors early (at startup, not runtime)
- Providing actionable error messages with suggestions
- Integrating with standard Django tooling (`manage.py check`)
- Distinguishing blocking errors from non-blocking warnings
- Supporting both strict validation and flexibility where needed

The implementation will make debugging configuration issues straightforward and prevent common mistakes like field name typos from causing runtime failures.
