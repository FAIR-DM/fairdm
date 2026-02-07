# Research Task R1: Field Configuration Patterns

**Date**: 2026-01-12
**Status**: Complete
**Researcher**: GitHub Copilot

## Executive Summary

After analyzing django-tables2, django-filter, and Django REST Framework (DRF), the recommended pattern for FairDM is: **Single parent `fields` attribute with component-specific overrides and explicit custom class support**. This pattern follows established Django conventions and provides progressive disclosure from simple to advanced usage.

---

## 1. Library Pattern Analysis

### 1.1 django-tables2: Column Configuration

**Pattern**: Meta.fields + Meta.exclude + explicit column definitions

#### Key Findings

1. **Meta.fields** (tuple): Specifies which model fields to include as columns
   - `None` = all model fields
   - List of field names = only those fields

2. **Meta.exclude** (tuple): Blacklist specific fields from display

3. **Explicit column definitions**: Override auto-generated columns

   ```python
   class PersonTable(tables.Table):
       name = tables.Column()  # Explicit definition

       class Meta:
           model = Person
           fields = ("first_name", "last_name")  # Auto-generated
   ```

4. **Inheritance behavior**:
   - Columns are inherited from parent classes
   - Setting column to `None` removes inherited column
   - Meta class must be explicitly inherited: `class Meta(ParentTable.Meta)`

**Source**: django-tables2 documentation

- API Reference: Meta.fields, Meta.exclude, Meta.model
- FAQ: Inheritance patterns

### 1.2 django-filter: Filter Configuration

**Pattern**: Meta.fields + Meta.exclude + explicit filter definitions

#### Key Findings

1. **Meta.fields** (list or dict): Required for auto-generation
   - `'__all__'` = all model fields
   - List of field names = basic filters
   - Dict format = advanced filter types per field

   ```python
   fields = {
       'username': ['exact', 'contains'],
       'last_login': ['exact'],
   }
   ```

2. **Meta.exclude** (list): Blacklist fields from auto-generation

3. **Explicit filter declarations**: Override auto-generated filters

   ```python
   class UserFilter(django_filters.FilterSet):
       username = filters.CharFilter()  # Explicit override

       class Meta:
           model = User
           fields = ['username', 'last_login']
   ```

4. **Precedence rules**:
   - Explicitly declared filters are NOT overwritten by Meta.fields
   - Including declared filter in Meta.fields dict raises TypeError
   - Meta.filter_overrides applies to auto-generated filters only

5. **Migration note**: Django-filter 1.0 moved options to Meta class to prevent naming conflicts

**Source**: django-filter documentation

- FilterSet Reference: Meta.fields, Meta.exclude
- Migration Guide: 1.0 changes

### 1.3 Django REST Framework: Serializer Configuration

**Pattern**: Meta.fields + Meta.exclude + explicit field definitions

#### Key Findings

1. **Meta.fields** (list or string):
   - `'__all__'` = all model fields
   - List of field names = only those fields
   - Must be explicitly specified (no default)

2. **Meta.exclude** (list): Alternative to fields (mutually exclusive in practice)

3. **Explicit field declarations**: Add extra fields or override defaults

   ```python
   class AccountSerializer(serializers.ModelSerializer):
       url = serializers.CharField(source='get_absolute_url', read_only=True)

       class Meta:
           model = Account
           fields = ['id', 'url', 'account_name']
   ```

4. **Meta.read_only_fields** (list): Mark fields as read-only without explicit declaration

5. **Inheritance behavior**:
   - Fields inherit from parent serializers
   - Set field to `None` to remove inherited field
   - Explicitly inherit Meta: `class Meta(ParentSerializer.Meta)`

6. **Precedence**: Explicitly declared fields take precedence over Meta.fields configuration

**Source**: Django REST Framework documentation

- Serializer API Guide: ModelSerializer
- Release Notes: Field exclusion improvements

---

## 2. Current FairDM Implementation Analysis

### 2.1 Current Pattern (from config.py)

```python
class ModelConfiguration:
    # Primary field configuration - fallback for all components
    fields: list[str] = []
    exclude: list[str] = []

    # Nested component configurations
    form: FormConfig | None = None
    table: TableConfig | None = None
    filters: FiltersConfig | None = None
```

### 2.2 Component Config Pattern (from components.py)

```python
@dataclass
class TableConfig:
    fields: list[str] | None = None  # None = use parent fields
    exclude: list[str] | None = None
    table_class: type | str | None = None  # Full custom override
```

### 2.3 Factory Pattern (from factories.py)

```python
class TableFactory(ComponentFactory):
    def __init__(self, model, config: TableConfig, parent_fields: list[str] | None = None):
        self.parent_fields = parent_fields

    def get_fields(self) -> list[str]:
        # 1. Check if config specifies fields
        if self.config.fields is not None:
            fields = self.config.fields
        # 2. Fall back to parent fields
        elif self.parent_fields:
            fields = self.parent_fields
        # 3. Use inspector's smart defaults
        else:
            fields = self.inspector.get_default_list_fields()

        return self.apply_exclusions(fields)
```

### 2.4 Usage in fairdm_demo (Legacy Pattern)

```python
class CustomSampleConfig(ModelConfiguration):
    model = CustomSample

    # Legacy: Component-specific field lists
    table_fields = ["name", "char_field", "boolean_field"]
    form_fields = ["name", "char_field", "text_field", "integer_field"]
    filterset_fields = ["char_field", "boolean_field", "date_field"]

    # Custom classes
    filterset_class = CustomSampleFilter
    table_class = CustomSampleTable
```

**Analysis**: The demo uses **legacy attributes** (`table_fields`, `form_fields`) which are NOT part of the new Day 3 design. The new design uses:

- `fields` (parent-level)
- `table = TableConfig(fields=[...])` (component-level)
- `table_class` (custom class override)

---

## 3. Decision: Recommended Pattern

### Pattern: **Single Parent Fields with Component-Specific Overrides**

This three-tier approach provides progressive disclosure:

#### Tier 1: Simple (Parent Fields Only)

```python
class MySampleConfig(ModelConfiguration):
    model = MySample
    fields = ["name", "location", "collected_at"]
    # All components use same fields by default
```

#### Tier 2: Intermediate (Component-Specific Fields)

```python
class MySampleConfig(ModelConfiguration):
    model = MySample
    fields = ["name", "location", "collected_at"]  # Default

    # Fine-tune specific components
    table = TableConfig(
        fields=["name", "collected_at"],  # Fewer fields for table
        orderable=True
    )

    filters = FiltersConfig(
        fields=["collected_at", "status"],  # Different fields for filters
        range_fields=["collected_at"]
    )
```

#### Tier 3: Advanced (Custom Classes)

```python
class MySampleConfig(ModelConfiguration):
    model = MySample

    # Full custom control - auto-generation skipped
    form = FormConfig(form_class=MyCustomForm)
    table = TableConfig(table_class=MyCustomTable)
```

---

## 4. Precedence Rules

### Rule Hierarchy (Highest to Lowest Priority)

1. **Custom Class** (if provided)
   - `TableConfig(table_class=CustomTable)`
   - Completely bypasses field configuration and auto-generation
   - Component-level: `config.table.table_class`
   - Legacy support: `config.table_class`

2. **Component-Specific Fields** (if provided)
   - `TableConfig(fields=["name", "status"])`
   - Overrides parent fields for this component only
   - Component-level: `config.table.fields`

3. **Parent-Level Fields** (fallback)
   - `ModelConfiguration.fields = ["name", "location"]`
   - Used when component doesn't specify fields
   - Config-level: `config.fields`

4. **Smart Defaults** (last resort)
   - Generated by `FieldInspector` based on field types
   - Different defaults per component:
     - Tables: `["name", "created", "modified"]`
     - Forms: All editable fields
     - Filters: Date, choice, boolean, FK fields

### Exclusion Rules

Exclusions are applied **after** field selection at each level:

1. Component-specific exclusions: `TableConfig(exclude=["id"])`
2. Parent-level exclusions: `ModelConfiguration.exclude = ["internal_id"]`
3. Both are cumulative: final_fields = selected_fields - component_exclude - parent_exclude

### Explicit Declarations (Django Pattern)

Following django-filter and DRF precedent:

- Explicitly declared filters/serializer fields are NOT overwritten by Meta.fields
- In FairDM context: If user provides custom class, field configuration is ignored
- This prevents confusion between declarative and auto-generated approaches

---

## 5. Rationale

### Why This Pattern?

1. **Follows Django Conventions**
   - Meta.fields + Meta.exclude is standard across django-tables2, django-filter, and DRF
   - Developers familiar with Django will find this intuitive
   - Consistent with Django's own ModelForm pattern

2. **Progressive Disclosure**
   - Simple case: Just specify parent fields
   - Intermediate: Override specific components
   - Advanced: Provide custom classes
   - Users only learn what they need

3. **Single Source of Truth**
   - Parent `fields` serves as sensible default
   - Avoids duplication across components
   - Component overrides are explicit and intentional

4. **Backwards Compatible**
   - Legacy `table_class`/`form_class` still work
   - Can gradually migrate to new nested config pattern

5. **Clear Precedence**
   - Explicit custom classes win (Django pattern)
   - Component-specific beats parent (override pattern)
   - Smart defaults as safety net (convention over configuration)

---

## 6. Alternatives Considered

### Alternative A: Component-Specific Fields Only

```python
class Config:
    table_fields = ["name", "status"]
    form_fields = ["name", "description", "status"]
    filterset_fields = ["status", "created"]
```

**Rejected because**:

- Requires duplication when fields are mostly the same
- No fallback mechanism - must specify for every component
- Violates DRY principle
- Not how Django libraries work

### Alternative B: Single Global Fields (No Overrides)

```python
class Config:
    fields = ["name", "status", "created"]
    # All components use exactly these fields
```

**Rejected because**:

- Too rigid - different components need different fields
- Tables typically show fewer fields than forms
- Filters focus on searchable/filterable fields
- No way to customize per component

### Alternative C: Multiple Field Lists with No Hierarchy

```python
class Config:
    fields = ["name", "status"]         # For ???
    table_fields = ["name"]             # For tables
    form_fields = ["name", "status"]    # For forms
```

**Rejected because**:

- Unclear what `fields` is for if everything has specific list
- No inheritance/fallback mechanism
- Ambiguous precedence

---

## 7. Implementation Notes

### 7.1 Current Implementation Status

✅ **Already Implemented** (Day 3 design):

- Parent-level `fields` and `exclude`
- Component-specific `TableConfig(fields=...)`
- Factory precedence logic (custom class → component fields → parent fields → defaults)
- Exclusion handling at component level

❌ **Not Yet Implemented**:

- Legacy attribute deprecation warnings (`table_fields`, `form_fields`, etc.)
- Parent-level exclusion application across all components
- Documentation of precedence rules for users

### 7.2 Factory Implementation Pattern

All factories follow this pattern (from `factories.py`):

```python
def get_fields(self) -> list[str]:
    """Get fields with three-tier fallback."""
    # Tier 1: Component-specific fields
    if self.config.fields is not None:
        fields = self.config.fields
    # Tier 2: Parent fields
    elif self.parent_fields:
        fields = self.parent_fields
    # Tier 3: Smart defaults
    else:
        fields = self.inspector.get_default_X_fields()

    # Apply exclusions (component + parent)
    return self.apply_exclusions(fields)
```

This is **consistently implemented** across:

- `FormFactory`
- `TableFactory`
- `FilterFactory`
- `AdminFactory`

### 7.3 Custom Class Detection

The `has_custom_*` methods provide clean API for checking custom classes:

```python
def has_custom_table(self) -> bool:
    """Check if a custom table class is provided."""
    return self.table is not None and self.table.table_class is not None
```

Used in factories:

```python
def generate(self) -> type[Table]:
    # If custom class provided, use it
    if self.config.table_class is not None:
        return self.config.table_class

    # Otherwise, auto-generate using fields
    fields = self.get_fields()
    return table_factory(self.model, fields=fields)
```

### 7.4 Gotchas and Special Considerations

1. **Nested Field Tuples**: FairDM supports grouped field syntax

   ```python
   fields = [
       ("name", "status"),  # Grouped for form layout
       "char_field",
       ("added", "modified"),
   ]
   ```

   Factories flatten these: `["name", "status", "char_field", "added", "modified"]`

2. **Field Validation**: FilterFactory validates fields exist in model

   ```python
   model_field_names = {f.name for f in self.model._meta.get_fields()}
   fields = [f for f in fields if f in model_field_names]
   ```

   Reason: django-filter is strict about field names

3. **Special Fields Exclusion**: Some fields are automatically excluded

   ```python
   # From FieldInspector
   EXCLUDED_FIELDS = {
       "id", "polymorphic_ctype", "sample_ptr", "measurement_ptr",
       "created", "modified", "options", "image"
   }
   ```

4. **Smart Defaults Differ by Component**:
   - **Tables**: Display-oriented fields (name, dates)
   - **Forms**: All editable fields
   - **Filters**: Searchable/filterable fields (dates, choices, booleans, FKs)
   - **Admin**: All fields with intelligent grouping

5. **Backwards Compatibility**: Legacy attributes still work

   ```python
   def __init__(self, model=None):
       # Handle legacy form_class/table_class/filterset_class
       if self.form_class is not None and self.form.form_class is None:
           self.form.form_class = self.form_class
       if self.table_class is not None and self.table.table_class is None:
           self.table.table_class = self.table_class
   ```

---

## 8. Code Examples

### 8.1 Simple: Parent Fields Only

```python
from fairdm.registry import register
from fairdm.registry.config import ModelConfiguration

@register
class WaterSampleConfig(ModelConfiguration):
    model = WaterSample
    fields = ["name", "location", "ph_level", "temperature"]

    # All components auto-generated with these fields:
    # - Form: Shows all 4 fields
    # - Table: Shows all 4 fields
    # - Filters: Auto-detects filterable fields (e.g., ph_level as range)
    # - Admin: Shows all 4 fields with intelligent grouping
```

### 8.2 Intermediate: Component Overrides

```python
from fairdm.registry import register
from fairdm.registry.config import ModelConfiguration, TableConfig, FiltersConfig

@register
class WaterSampleConfig(ModelConfiguration):
    model = WaterSample
    fields = ["name", "location", "ph_level", "temperature", "collected_at"]

    # Table shows subset of fields
    table = TableConfig(
        fields=["name", "location", "collected_at"],
        orderable=True
    )

    # Filters focus on searchable fields
    filters = FiltersConfig(
        fields=["ph_level", "temperature", "collected_at"],
        range_fields=["ph_level", "temperature", "collected_at"]
    )

    # Form uses parent fields (all 5 fields)
```

### 8.3 Advanced: Custom Classes

```python
from fairdm.registry import register
from fairdm.registry.config import ModelConfiguration, TableConfig, FormConfig
from .forms import WaterSampleForm
from .tables import WaterSampleTable

@register
class WaterSampleConfig(ModelConfiguration):
    model = WaterSample

    # Custom form with special widgets
    form = FormConfig(form_class=WaterSampleForm)

    # Custom table with special rendering
    table = TableConfig(table_class=WaterSampleTable)

    # Filters still auto-generated
    # (will use smart defaults since no fields specified)
```

### 8.4 Mixed: Component Fields + Exclusions

```python
from fairdm.registry import register
from fairdm.registry.config import ModelConfiguration, TableConfig

@register
class WaterSampleConfig(ModelConfiguration):
    model = WaterSample
    fields = ["name", "location", "ph_level", "temperature", "internal_id"]
    exclude = ["internal_id"]  # Hide internal field from all components

    # Table shows even fewer fields
    table = TableConfig(
        fields=["name", "location"],
        # Could also use: exclude=["ph_level", "temperature", "internal_id"]
    )

    # Form and filters use: ["name", "location", "ph_level", "temperature"]
    # (parent fields minus parent exclusions)
```

### 8.5 Real-World: fairdm_demo Migration

**Before (Legacy)**:

```python
class CustomSampleConfig(ModelConfiguration):
    model = CustomSample

    table_fields = ["name", "char_field", "boolean_field", "date_field"]
    form_fields = ["name", "char_field", "text_field", "integer_field"]
    filterset_fields = ["char_field", "boolean_field", "date_field"]

    # Custom classes
    filterset_class = CustomSampleFilter
    table_class = CustomSampleTable
```

**After (New Pattern)**:

```python
class CustomSampleConfig(ModelConfiguration):
    model = CustomSample

    # Parent fields as sensible default
    fields = ["name", "char_field", "text_field", "boolean_field", "date_field"]

    # Component-specific overrides
    table = TableConfig(
        table_class=CustomSampleTable,  # Custom class
        # fields ignored when custom class provided
    )

    filters = FiltersConfig(
        filterset_class=CustomSampleFilter,  # Custom class
        # fields ignored when custom class provided
    )

    # Form uses parent fields (all 5)
```

---

## 9. Testing Verification

The pattern is **thoroughly tested** in the test suite:

### Test Coverage

1. **Field Precedence** (`test_component_factories.py`):

   ```python
   def test_table_with_specific_fields():
       """Component fields override parent fields."""

   def test_table_with_parent_fields():
       """Parent fields used when component doesn't specify."""

   def test_table_with_exclusions():
       """Exclusions applied correctly."""
   ```

2. **Custom Class Override** (`test_model_configuration.py`):

   ```python
   def test_custom_table_class_override():
       """Custom table class bypasses auto-generation."""
   ```

3. **Backwards Compatibility** (`test_model_configuration_integration.py`):

   ```python
   def test_legacy_table_class_attribute():
       """Old table_class attribute still works."""
   ```

4. **Integration Tests** (`test_model_configuration_integration.py`):

   ```python
   class TestNestedConfigAPI:
       def test_table_config()
       def test_filters_config()
       def test_form_config()
   ```

---

## 10. Comparison with Django Libraries

### Summary Table

| Feature | django-tables2 | django-filter | DRF | **FairDM** |
|---------|---------------|---------------|-----|------------|
| **Primary config** | Meta.fields | Meta.fields | Meta.fields | fields (parent) |
| **Exclusion** | Meta.exclude | Meta.exclude | Meta.exclude | exclude (parent + component) |
| **Custom class** | Entire Table subclass | Entire FilterSet subclass | Entire Serializer subclass | component.X_class |
| **Explicit declarations** | Column attributes | Filter attributes | Field attributes | component.X_class |
| **All fields shortcut** | `None` (default) | `'__all__'` | `'__all__'` | N/A (smart defaults) |
| **Inheritance** | Explicit Meta inheritance | Explicit Meta inheritance | Explicit Meta inheritance | Automatic |
| **Field grouping** | Via sequence | N/A | N/A | Nested tuples |
| **Progressive disclosure** | No | No | No | **Yes** ✅ |

### Key Differences in FairDM

1. **Three-tier fallback**: Component → Parent → Defaults (Django libraries only have two levels)
2. **Nested config objects**: `TableConfig`, `FormConfig` instead of everything in Meta
3. **Factory pattern**: Separation of configuration from generation
4. **Smart defaults**: Component-specific intelligent defaults when nothing specified
5. **Unified API**: Same pattern across all components (table, form, filters, admin)

---

## 11. Recommendations for Documentation

### User-Facing Documentation Should Include

1. **Quick Start** (Simple Pattern)
   - Show parent fields only
   - Explain "this is all you need for basic usage"

2. **Customization Guide** (Intermediate Pattern)
   - Show component-specific fields
   - Explain when and why to override

3. **Advanced Usage** (Custom Classes)
   - Show custom class pattern
   - Explain when to use (complex business logic)

4. **Precedence Rules** (Reference)
   - Clear hierarchy diagram
   - Examples of each level

5. **Migration Guide** (For Existing Users)
   - Show legacy → new pattern conversion
   - Mention backwards compatibility

6. **Common Patterns** (Cookbook)
   - "Show fewer fields in table than form"
   - "Use smart filter defaults"
   - "Exclude internal fields globally"

---

## 12. Conclusion

The current FairDM implementation **already follows best practices** from Django ecosystem:

✅ **Strengths**:

- Follows django-tables2, django-filter, and DRF conventions
- Clear precedence hierarchy (custom → component → parent → defaults)
- Progressive disclosure from simple to advanced
- Backwards compatible with legacy patterns
- Thoroughly tested
- Consistent across all components (form, table, filters, admin)

✅ **Unique Advantages**:

- Three-tier fallback (Django libraries only have two)
- Nested config objects (better organization)
- Factory pattern (separation of concerns)
- Smart defaults per component type

⚠️ **Minor Gaps**:

- Legacy attributes not yet deprecated (but still work)
- Documentation needs update to emphasize new pattern
- Could add warnings when mixing legacy + new patterns

**Overall Assessment**: The Day 3 redesign is architecturally sound and aligns with Django community best practices. The pattern is more sophisticated than individual Django libraries, providing a unified and progressive approach to component configuration.

---

## References

### Primary Sources

1. django-tables2 Documentation: <https://github.com/jieter/django-tables2>
   - API Reference: Table.Meta options
   - FAQ: Inheritance patterns
2. django-filter Documentation: <https://django-filter.readthedocs.io/>
   - FilterSet Reference: Meta.fields, Meta.exclude
   - Migration Guide: Version 1.0 changes
3. Django REST Framework Documentation: <https://www.django-rest-framework.org/>
   - ModelSerializer API Guide
   - Release Notes: Field configuration improvements

### FairDM Implementation

1. `fairdm/registry/config.py`: ModelConfiguration class
2. `fairdm/registry/components.py`: Component config dataclasses
3. `fairdm/registry/factories.py`: Factory implementations
4. `fairdm_demo/config.py`: Usage examples
5. `tests/test_registry/`: Comprehensive test suite

### Related Patterns

- Django ModelForm: Meta.fields and Meta.exclude
- Django Admin: ModelAdmin configuration
- SQLAlchemy: Declarative field configuration

---

**End of Research Report**
