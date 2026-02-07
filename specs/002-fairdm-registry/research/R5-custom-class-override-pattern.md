# Research Finding R5: Custom Class Override Pattern

**Research Task**: Determine how custom classes should interact with parent fields and configuration
**Date**: 2026-01-12
**Spec Reference**: [spec.md](../spec.md) - Q7 clarification

## Executive Summary

**Decision**: Custom classes **completely replace** auto-generation using a **clean override pattern**. When a custom class is provided (e.g., `form_class`, `table_class`, `filterset_class`), the registry returns it directly without any field-based auto-generation or merging.

**Key Insight**: This follows Django library conventions (django-tables2, django-filter) where custom classes take full responsibility for their configuration. The parent `fields` attribute and nested config objects (FormConfig, TableConfig) are only consulted when NO custom class is provided.

---

## Research Findings

### 1. Spec Clarification Q7 Analysis

**Question**: What field configuration pattern should ModelConfiguration support?

**Answer from spec.md (Session 2026-01-12)**:
> A: Parent `fields` with optional custom class overrides - Simple configs use single `fields` list (all components inherit). Advanced users provide custom Form/Table/FilterSet classes directly. No intermediate nested config layer (FormConfig, TableConfig) needed.

**Interpretation**:

- **Simple use case**: Define `fields` once → all components auto-generate from it
- **Advanced use case**: Provide custom class directly → bypasses field-based generation entirely
- **No merge behavior**: Custom classes don't inherit from parent fields

---

### 2. Django Library Patterns

#### django-tables2 Custom Table Pattern

```python
# From fairdm_demo/tables.py
class CustomSampleTable(SampleTable):
    class Meta:
        model = CustomSample
        exclude = ["path", "depth", "status"]
        fields = [
            "id", "dataset", "name", "char_field",
            # ... full list of fields
        ]

    def render_text_field(self, value):
        return f"{value[:32]}..."
```

**Key Observations**:

1. Custom Table defines its own `Meta.fields` - does NOT inherit from config
2. Table has full control over rendering methods (`render_*` methods)
3. Inherits from base table class (`SampleTable`) for shared behavior, not for field config

#### django-filter Custom FilterSet Pattern

```python
# From fairdm_demo/filters.py
class CustomSampleFilter(SampleFilter):
    class Meta:
        model = CustomSample
        fields = [
            "name", "char_field", "text_field",
            # ... complete field list
        ]
```

**Key Observations**:

1. Custom FilterSet defines its own `Meta.fields` explicitly
2. No mechanism to merge with parent configuration
3. Inherits from base filter for shared queryset modifications, not field config

---

### 3. Current Implementation Analysis

#### Current Behavior in ModelConfiguration

From [fairdm/registry/config.py](../../../fairdm/registry/config.py):

```python
class ModelConfiguration:
    # Legacy component classes (for backwards compatibility)
    form_class = None
    table_class = None
    filterset_class = None

    def get_form_class(self) -> type[ModelForm]:
        """Get or auto-generate the ModelForm class using FormFactory."""
        if not self.form:
            self.form = FormConfig()

        factory = FormFactory(
            model=self.model,
            config=self.form,
            parent_fields=self.fields,  # ← parent fields passed but only used if no custom class
        )
        return factory.generate()
```

#### Current Behavior in Factories

From [fairdm/registry/factories.py](../../../fairdm/registry/factories.py):

```python
class FormFactory(ComponentFactory):
    def generate(self) -> type[ModelForm]:
        # If user provided a custom form class, use it
        if self.config.form_class is not None:
            if isinstance(self.config.form_class, str):
                return import_string(self.config.form_class)
            return self.config.form_class  # ← RETURN IMMEDIATELY

        # Only reaches here if NO custom class provided
        fields = self.get_fields()  # Uses parent_fields as fallback
        # ... auto-generation logic ...
```

**Pattern**:

- Check for custom class FIRST
- If found, return immediately (no merging, no field consultation)
- Only proceed to auto-generation if custom class is None

This pattern is **identical** across all factories:

- `FormFactory.generate()`
- `TableFactory.generate()`
- `FilterFactory.generate()`
- `AdminFactory.generate()`

---

### 4. fairdm_demo Examples

#### Example 1: Parent fields only (auto-generation)

```python
@register
class CustomParentSampleConfig(ModelConfiguration):
    model = CustomParentSample
    fields = [
        ("name", "status"),
        "char_field",
        ("added", "modified"),
    ]
    # No custom classes → all components auto-generated from fields
```

**Result**: Form, Table, FilterSet all auto-generated using the same field list.

#### Example 2: Custom classes with separate field lists

```python
@register
class CustomSampleConfig(ModelConfiguration):
    model = CustomSample

    # Custom classes - these IGNORE fields below
    filterset_class = CustomSampleFilter
    table_class = CustomSampleTable

    # Field configuration for auto-generated components only
    table_fields = ["name", "char_field", "boolean_field", "date_field", "added"]
    form_fields = ["name", "char_field", "text_field", "integer_field", ...]
    filterset_fields = ["char_field", "boolean_field", "date_field", "added"]
```

**Result**:

- Custom FilterSet and Table are used as-is (their own `Meta.fields` apply)
- Form is auto-generated from `form_fields`
- Resource and other components use their respective field lists

**Important Note**: The `table_fields` and `filterset_fields` are IGNORED because custom classes are provided. This is legacy configuration from before nested configs were introduced.

---

### 5. Validation Requirements

#### Inheritance Checks

Custom classes MUST inherit from expected base classes:

| Component | Expected Base Class | Example |
|-----------|---------------------|---------|
| Form | `ModelForm` or `Form` | `django.forms.ModelForm` |
| Table | `Table` | `django_tables2.Table` |
| FilterSet | `FilterSet` | `django_filters.FilterSet` |
| Resource | `ModelResource` | `import_export.resources.ModelResource` |
| ModelAdmin | `ModelAdmin` | `django.contrib.admin.ModelAdmin` |

#### Validation Logic (from tests)

From [tests/test_registry/test_model_configuration.py](../../../tests/test_registry/test_model_configuration.py):

```python
def test_custom_form_class_override(self, clean_registry, db):
    """Test providing custom form class."""
    class CustomSampleForm(forms.ModelForm):
        class Meta:
            model = Sample
            fields = ["name"]

    @fairdm.register
    class CustomFormConfig(SampleConfig):
        model = Sample
        form_class = CustomSampleForm

    config = registry._registry[Sample]["config"]
    assert config.has_custom_form()  # ← Validation check
    assert config.form_class == CustomSampleForm
```

**Current Implementation**:

- `has_custom_form()` → checks if `form.form_class is not None`
- `has_custom_filterset()` → checks if `filters.filterset_class is not None`
- `has_custom_table()` → checks if `table.table_class is not None`

**Missing**: Type checking to ensure custom classes inherit from expected bases.

---

## Three Configuration Levels

### Level 1: Parent Fields (Simplest)

```python
@register
class SimpleConfig(ModelConfiguration):
    model = MySample
    fields = ["name", "location", "collected_at"]
    # All components inherit these fields
```

**Behavior**:

- Form uses `fields` → generates ModelForm with those 3 fields
- Table uses `fields` → generates Table with those 3 columns
- FilterSet uses `fields` → generates filters for those 3 fields

### Level 2: Nested Configs (Fine-tuning)

```python
@register
class TunedConfig(ModelConfiguration):
    model = MySample
    fields = ["name", "location", "collected_at"]  # Fallback

    table = TableConfig(
        fields=["name", "collected_at"],  # Override for table only
        orderable=True
    )

    filters = FiltersConfig(
        fields=["collected_at", "status"],
        range_fields=["collected_at"]
    )
```

**Behavior**:

- Form uses parent `fields` (fallback)
- Table uses `table.fields` (overrides parent)
- FilterSet uses `filters.fields` with range filter for dates

### Level 3: Custom Classes (Full Control)

```python
@register
class CustomConfig(ModelConfiguration):
    model = MySample

    form = FormConfig(form_class=MyCustomForm)
    table = TableConfig(table_class=MyCustomTable)
    filters = FiltersConfig(filterset_class=MyCustomFilter)
```

**Behavior**:

- Form: `MyCustomForm` returned directly (NO field-based generation)
- Table: `MyCustomTable` returned directly
- FilterSet: `MyCustomFilter` returned directly
- Parent `fields` and nested config `fields` are IGNORED when custom class provided

---

## Decision: Clean Override Pattern

### Rationale

1. **Simplicity**: Clear mental model - custom class means "I'll handle it myself"
2. **Predictability**: No hidden merging logic that could surprise developers
3. **Django Conventions**: Matches how django-tables2 and django-filter work
4. **Separation of Concerns**: Configuration (fields) vs. implementation (custom classes) are separate paths
5. **Progressive Disclosure**: Simple → intermediate → advanced path is clean

### Alternatives Considered

#### Alternative 1: Merge Pattern (REJECTED)

```python
# REJECTED: Merge parent fields with custom class Meta.fields
class CustomTable(Table):
    custom_column = Column()

    class Meta:
        model = MySample
        fields = ["custom_column"]  # Only custom fields

# Registry would merge with parent fields:
# final_fields = parent_fields + custom_class.Meta.fields
```

**Why Rejected**:

- Too complex and unpredictable
- Conflicts with Django's explicit field listing
- Hard to understand what the final field list will be
- Requires custom metaclass magic

#### Alternative 2: Partial Overrides (REJECTED)

```python
# REJECTED: Allow custom class + field-based configuration
table = TableConfig(
    table_class=MyCustomTable,
    fields=["name", "location"]  # Try to override table's fields?
)
```

**Why Rejected**:

- Confusing: which takes precedence?
- Custom Table defines its own fields - can't override from outside
- Violates encapsulation

#### Alternative 3: Nested Config Required with Custom Class (REJECTED)

```python
# REJECTED: Force nested config when providing custom class
form = FormConfig(
    form_class=MyCustomForm,
    fields=["name"]  # Required even though ignored?
)
```

**Why Rejected**:

- Redundant - custom class defines its own fields
- Confusing to require unused configuration

---

## Implementation Recommendations

### 1. Validation at Registration Time

Add inheritance checks when custom classes are provided:

```python
def validate_custom_form(self, form_class):
    """Validate that custom form inherits from ModelForm."""
    if not issubclass(form_class, ModelForm):
        raise TypeError(
            f"{form_class.__name__} must inherit from django.forms.ModelForm. "
            f"Got: {form_class.__bases__}"
        )

def validate_custom_table(self, table_class):
    """Validate that custom table inherits from Table."""
    from django_tables2 import Table
    if not issubclass(table_class, Table):
        raise TypeError(
            f"{table_class.__name__} must inherit from django_tables2.Table. "
            f"Got: {table_class.__bases__}"
        )
```

### 2. Clear Error Messages

When custom class and nested fields both provided:

```python
# WARN or IGNORE extra configuration
if self.config.form_class and self.config.fields:
    warnings.warn(
        f"Custom form_class provided for {self.model.__name__}. "
        f"Ignoring FormConfig.fields={self.config.fields}. "
        f"Custom form class should define its own Meta.fields.",
        UserWarning
    )
```

### 3. Documentation Pattern

Clear examples showing the three levels:

```python
# ✅ LEVEL 1: Parent fields only
@register
class SimpleConfig(ModelConfiguration):
    model = MySample
    fields = ["name", "location"]

# ✅ LEVEL 2: Fine-tune with nested configs
@register
class TunedConfig(ModelConfiguration):
    model = MySample
    fields = ["name", "location"]  # Fallback
    table = TableConfig(fields=["name"])  # Override

# ✅ LEVEL 3: Custom class (full control)
@register
class CustomConfig(ModelConfiguration):
    model = MySample
    table = TableConfig(table_class=MyCustomTable)
    # MyCustomTable.Meta.fields defines what shows

# ❌ ANTI-PATTERN: Custom class + conflicting fields
@register
class ConfusingConfig(ModelConfiguration):
    model = MySample
    fields = ["name", "location"]  # ← IGNORED!
    table = TableConfig(
        table_class=MyCustomTable,
        fields=["name"]  # ← ALSO IGNORED!
    )
```

### 4. Backwards Compatibility

Current implementation already follows clean override pattern:

```python
# OLD API (still works)
@register
class OldStyleConfig(ModelConfiguration):
    model = MySample
    table_class = MyCustomTable  # ← Legacy attribute
    table_fields = ["name"]  # ← IGNORED when table_class provided

# NEW API (recommended)
@register
class NewStyleConfig(ModelConfiguration):
    model = MySample
    table = TableConfig(table_class=MyCustomTable)
```

No breaking changes needed - just clearer documentation and validation.

---

## Code Examples

### Example 1: Registration with Parent Fields

```python
from fairdm.registry import register
from fairdm.registry.config import ModelConfiguration

@register
class WaterSampleConfig(ModelConfiguration):
    model = WaterSample
    fields = ["name", "location", "ph_level", "temperature", "collected_at"]

# Result:
# - Form: auto-generated with all 5 fields
# - Table: auto-generated with all 5 columns
# - FilterSet: auto-generated with filters for all 5 fields
```

### Example 2: Custom Table Only

```python
from .tables import WaterSampleTable

@register
class WaterSampleConfig(ModelConfiguration):
    model = WaterSample
    fields = ["name", "location", "ph_level", "temperature"]

    # Custom table with specialized rendering
    table = TableConfig(table_class=WaterSampleTable)

# Result:
# - Form: auto-generated from parent fields
# - Table: WaterSampleTable used directly (defines own fields/columns)
# - FilterSet: auto-generated from parent fields
```

### Example 3: All Custom Components

```python
from .forms import WaterSampleForm
from .tables import WaterSampleTable
from .filters import WaterSampleFilter

@register
class WaterSampleConfig(ModelConfiguration):
    model = WaterSample

    # All custom classes - parent fields ignored
    form = FormConfig(form_class=WaterSampleForm)
    table = TableConfig(table_class=WaterSampleTable)
    filters = FiltersConfig(filterset_class=WaterSampleFilter)

# Result:
# - Form: WaterSampleForm used directly
# - Table: WaterSampleTable used directly
# - FilterSet: WaterSampleFilter used directly
```

### Example 4: Validation Error

```python
from django.db import models

# ❌ This should raise TypeError
class InvalidTable(models.Model):  # Wrong base class!
    name = models.CharField(max_length=100)

@register
class BadConfig(ModelConfiguration):
    model = WaterSample
    table = TableConfig(table_class=InvalidTable)

# Raises:
# TypeError: InvalidTable must inherit from django_tables2.Table.
# Got: (<class 'django.db.models.base.Model'>,)
```

---

## Testing Strategy

### Unit Tests

```python
def test_custom_class_ignores_parent_fields():
    """Verify custom class takes precedence over parent fields."""
    @register
    class Config(ModelConfiguration):
        model = Sample
        fields = ["name", "status", "collected_at"]
        table = TableConfig(table_class=CustomTable)

    table_class = config.get_table_class()
    assert table_class == CustomTable
    # CustomTable.Meta.fields should be used, not parent fields

def test_custom_class_validation():
    """Verify inheritance checking for custom classes."""
    class NotATable:
        pass

    with pytest.raises(TypeError, match="must inherit from.*Table"):
        @register
        class BadConfig(ModelConfiguration):
            model = Sample
            table = TableConfig(table_class=NotATable)
```

### Integration Tests

```python
def test_three_level_configuration():
    """Test all three configuration levels work correctly."""

    # Level 1: Parent fields only
    @register
    class SimpleConfig(ModelConfiguration):
        model = Sample
        fields = ["name"]

    form1 = SimpleConfig().get_form_class()
    assert "name" in form1._meta.fields

    # Level 2: Nested config override
    @register
    class TunedConfig(ModelConfiguration):
        model = Sample
        fields = ["name", "status"]
        table = TableConfig(fields=["name"])

    table2 = TunedConfig().get_table_class()
    assert len(table2._meta.fields) == 1

    # Level 3: Custom class
    @register
    class CustomConfig(ModelConfiguration):
        model = Sample
        table = TableConfig(table_class=CustomTable)

    table3 = CustomConfig().get_table_class()
    assert table3 == CustomTable
```

---

## Summary

### Key Decisions

1. ✅ **Clean Override**: Custom classes completely replace auto-generation
2. ✅ **No Merging**: Custom classes ignore parent fields and nested config fields
3. ✅ **Validation Required**: Check inheritance from expected base classes
4. ✅ **Three Clear Levels**: Parent fields → nested configs → custom classes
5. ✅ **Django Conventions**: Matches django-tables2 and django-filter patterns

### Implementation Checklist

- [ ] Add inheritance validation for custom classes
- [ ] Add warning when custom class + conflicting fields provided
- [ ] Update documentation with three-level examples
- [ ] Update fairdm_demo with clear examples of each level
- [ ] Add integration tests for custom class override pattern
- [ ] Update ModelConfiguration docstrings with anti-patterns

### Documentation Requirements

- **Quickstart**: Show Level 1 (parent fields) as default path
- **Intermediate Guide**: Show Level 2 (nested configs) for fine-tuning
- **Advanced Guide**: Show Level 3 (custom classes) with full examples
- **Migration Guide**: Explain old vs. new API, backwards compatibility
- **Anti-Patterns**: Document what NOT to do (custom class + fields)

---

## References

- [Spec Q7 Answer](../spec.md) - Parent fields with optional custom class overrides
- [Current Implementation](../../../fairdm/registry/config.py) - ModelConfiguration class
- [Factory Pattern](../../../fairdm/registry/factories.py) - Component generation logic
- [Demo Examples](../../../fairdm_demo/config.py) - Real-world registration patterns
- [Custom Table](../../../fairdm_demo/tables.py) - Example custom component
- [Custom Filter](../../../fairdm_demo/filters.py) - Example custom component
- [Tests](../../../tests/test_registry/test_model_configuration.py) - Custom class override tests
