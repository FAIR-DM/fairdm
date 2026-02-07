# Research Finding R6: Nested Config Removal Impact

**Research Task**: Analyze impact of removing FormConfig, TableConfig, FiltersConfig, AdminConfig dataclasses
**Date**: 2026-01-12
**Spec Reference**: [spec.md](spec.md) - Q9 clarification

## Executive Summary

**Decision**: Remove FormConfig, TableConfig, FiltersConfig, AdminConfig nested config dataclasses from [fairdm/registry/components.py](../../fairdm/registry/components.py) and refactor ModelConfiguration to use direct custom class attributes (form_class, table_class, filterset_class, admin_class) with parent `fields` as fallback.

**Impact**: MODERATE - Affects 2 core files, 1 test file, multiple research documents. No breaking changes to fairdm_demo which uses legacy API pattern (component-specific field lists) that will continue working.

**Migration Strategy**: Deprecation warnings for 1 release cycle, then removal. New API uses parent `fields` + custom class overrides pattern. Old component-specific field lists (`table_fields`, `form_fields`, etc.) remain for backwards compatibility.

---

## 1. Code Dependencies Analysis

### 1.1 Files That Import Nested Config Classes

**Primary Usage Files**:

1. **[fairdm/registry/config.py](../../fairdm/registry/config.py)** (Line 16)

   ```python
   from fairdm.registry.components import AdminConfig, FiltersConfig, FormConfig, TableConfig
   ```

   - Imports all 4 nested config classes
   - Uses them in `ModelConfiguration.__init__()` to initialize nested config objects
   - References in 8 locations (initialization + getter methods)

2. **[fairdm/registry/factories.py](../../fairdm/registry/factories.py)** (Line 18)

   ```python
   from fairdm.registry.components import AdminConfig, FiltersConfig, FormConfig, TableConfig
   ```

   - Type hints for factory constructors (`FormFactory.__init__(config: FormConfig)`)
   - Field resolution logic checks `config.fields`, `config.exclude` attributes
   - References in 4 factory classes

3. **[tests/test_registry/test_component_factories.py](../../tests/test_registry/test_component_factories.py)** (Line 13)

   ```python
   from fairdm.config_components import FiltersConfig, FormConfig, TableConfig
   ```

   - Test fixtures instantiate config classes: `config = FormConfig(fields=['name'])`
   - Tests validate factory behavior with various config options
   - References in ~20 test methods

**No Direct Usage**:

- **fairdm_demo/config.py**: Does NOT import nested configs, uses legacy API
- **Test files**: Only `test_component_factories.py` uses them directly

### 1.2 Current Implementation in ModelConfiguration

From [fairdm/registry/config.py](../../fairdm/registry/config.py#L127-L177):

```python
class ModelConfiguration:
    # Nested component configurations
    form: FormConfig | None = None
    table: TableConfig | None = None
    filters: FiltersConfig | None = None
    admin: AdminConfig | None = None

    # Legacy component classes (for backwards compatibility)
    form_class = None
    table_class = None
    filterset_class = None

    def __init__(self, model=None):
        # Initialize nested configs if not provided
        if self.form is None:
            self.form = FormConfig()
        if self.table is None:
            self.table = TableConfig()
        if self.filters is None:
            self.filters = FiltersConfig()
        if self.admin is None:
            self.admin = AdminConfig()

        # Handle legacy form_class/table_class/filterset_class
        if self.form_class is not None and self.form.form_class is None:
            self.form.form_class = self.form_class
```

**Key Observation**: The nested configs are instantiated but NEVER explicitly configured by users in fairdm_demo. They serve as intermediate data holders between legacy attributes and factories.

### 1.3 Factory Usage Patterns

From [fairdm/registry/factories.py](../../fairdm/registry/factories.py#L87-L104):

```python
class FormFactory(ComponentFactory):
    def __init__(self, model: type[models.Model], config: FormConfig, parent_fields: list[str] | None = None):
        super().__init__(model, config)
        self.parent_fields = parent_fields

    def get_fields(self) -> list[str] | str:
        # Check if config specifies fields
        if self.config.fields is not None:
            fields = self.config.fields
        # Fall back to parent fields
        elif self.parent_fields:
            fields = self.parent_fields
        else:
            # Default to safe fields
            return self.inspector.get_safe_fields()
```

**Pattern**: Factories access `config.fields`, `config.exclude`, `config.form_class` attributes. The nested config object is just a namespace holder - it doesn't provide behavior or validation.

---

## 2. Current Usage in fairdm_demo

### 2.1 fairdm_demo/config.py Analysis

**No nested config usage found**. The demo uses:

```python
@register
class CustomSampleConfig(ModelConfiguration):
    model = CustomSample

    # Legacy component-specific field lists (NOT nested configs)
    table_fields = ["name", "char_field", "boolean_field", "date_field", "added"]
    form_fields = ["name", "char_field", "text_field", "integer_field", ...]
    filterset_fields = ["char_field", "boolean_field", "date_field", "added"]
    resource_fields = ["name", "char_field", "text_field", ...]

    # Direct custom class overrides (NOT nested configs)
    filterset_class = CustomSampleFilter
    table_class = CustomSampleTable
```

**Critical Insight**: fairdm_demo uses the OLD API pattern with component-specific field lists. This predates nested configs and will continue working after nested config removal because:

1. `table_fields` → passed to `TableFactory` as `parent_fields` parameter
2. `table_class` → checked in `ModelConfiguration.get_table_class()`
3. No code creates `TableConfig(fields=['name'])` objects

### 2.2 Backwards Compatibility Assessment

**✅ SAFE**: Removing nested configs will NOT break fairdm_demo because:

- Demo never imports `FormConfig`, `TableConfig`, etc.
- Demo never instantiates nested config objects
- Demo uses legacy attributes that bypass nested configs entirely

---

## 3. Migration Path

### 3.1 Before (Current with Nested Configs)

```python
from fairdm.registry.components import TableConfig, FormConfig

@register
class MySampleConfig(ModelConfiguration):
    model = MySample
    fields = ["name", "location"]  # Parent fields

    # Nested config with component-specific overrides
    table = TableConfig(
        fields=["name"],  # Override parent fields
        orderable=True
    )

    form = FormConfig(
        form_class=MyCustomForm  # Full custom override
    )
```

### 3.2 After (New API without Nested Configs)

```python
@register
class MySampleConfig(ModelConfiguration):
    model = MySample
    fields = ["name", "location"]  # Parent fields used by ALL components

    # Direct custom class override (no nested config)
    form_class = MyCustomForm

    # For advanced table options, provide custom Table class
    table_class = MyCustomTable  # Define orderable in class Meta
```

### 3.3 Alternative: Keep Legacy Component-Specific Fields

```python
@register
class MySampleConfig(ModelConfiguration):
    model = MySample

    # Component-specific field lists (legacy pattern, still works)
    table_fields = ["name"]
    form_fields = ["name", "location"]
    filterset_fields = ["name"]
```

---

## 4. Deprecation Strategy

### 4.1 Can Removal Be Done with Deprecation Warnings?

**YES** - Deprecation is feasible because:

1. **Detection**: Check if user sets `form`, `table`, `filters`, or `admin` attributes
2. **Warning Location**: `ModelConfiguration.__init__()` can detect and warn
3. **Migration Path**: Clear alternative (parent `fields` + custom class overrides)

### 4.2 Deprecation Implementation

```python
# fairdm/registry/config.py

class ModelConfiguration:
    # Keep attributes for deprecation period
    form: FormConfig | None = None
    table: TableConfig | None = None
    filters: FiltersConfig | None = None
    admin: AdminConfig | None = None

    def __init__(self, model=None):
        # Detect if user provided nested configs
        if any([
            self.form is not None and not isinstance(self.form, FormConfig),
            self.table is not None and not isinstance(self.table, TableConfig),
            # ... check others
        ]):
            warnings.warn(
                "Nested config attributes (form, table, filters, admin) are deprecated. "
                "Use parent 'fields' attribute for shared fields, or provide custom "
                "classes directly (form_class, table_class, etc.). "
                "See migration guide: https://fairdm.org/migration/nested-configs",
                DeprecationWarning,
                stacklevel=2
            )
```

### 4.3 Timeline

| Phase | Duration | Action |
|-------|----------|--------|
| **Phase 1: Deprecation** | 1 release (v0.8.0) | Add deprecation warnings, update docs with migration guide |
| **Phase 2: Removal** | Next release (v0.9.0) | Remove nested config classes, update factories to accept dicts |
| **Phase 3: Cleanup** | Same release | Remove deprecated attributes from ModelConfiguration |

---

## 5. Test Updates Required

### 5.1 Tests That Use Nested Configs

**[tests/test_registry/test_component_factories.py](../../tests/test_registry/test_component_factories.py)**:

- 20+ test methods instantiate `FormConfig(fields=['name'])`
- Tests validate factory behavior with config options

**Migration**:

```python
# BEFORE
config = FormConfig(fields=['name', 'collected_at'])
factory = FormFactory(SampleModel, config)

# AFTER (Option 1: Simple dict)
config = {'fields': ['name', 'collected_at']}
factory = FormFactory(SampleModel, config, parent_fields=None)

# AFTER (Option 2: Pass None, use parent_fields)
factory = FormFactory(SampleModel, config=None, parent_fields=['name', 'collected_at'])
```

### 5.2 New Tests Needed

1. **Test parent fields inheritance**:

   ```python
   def test_form_uses_parent_fields_when_no_custom_class():
       config = ModelConfiguration()
       config.model = MySample
       config.fields = ['name', 'location']
       config.form_class = None  # No custom class

       form_class = config.get_form_class()
       form = form_class()
       assert 'name' in form.fields
       assert 'location' in form.fields
   ```

2. **Test custom class override bypasses fields**:

   ```python
   def test_custom_form_class_ignores_parent_fields():
       config = ModelConfiguration()
       config.model = MySample
       config.fields = ['name']  # Should be ignored
       config.form_class = MyCustomForm  # Defines own fields

       form_class = config.get_form_class()
       assert form_class == MyCustomForm
   ```

---

## 6. Breaking Changes Assessment

### 6.1 What WILL Break Immediately

**Direct Nested Config Instantiation** (LOW IMPACT):

```python
# This will fail after removal
from fairdm.registry.components import FormConfig

config = FormConfig(fields=['name'])  # ❌ ImportError
```

**Impact**: MINIMAL - Only `test_component_factories.py` does this, no production code

### 6.2 What WILL Continue Working

**Legacy API in fairdm_demo** (HIGH USAGE):

```python
@register
class MySampleConfig(ModelConfiguration):
    table_fields = ['name']  # ✅ Still works
    form_class = MyCustomForm  # ✅ Still works
```

**New API Pattern** (TARGET PATTERN):

```python
@register
class MySampleConfig(ModelConfiguration):
    fields = ['name', 'location']  # ✅ Works (new parent fields pattern)
    table_class = MyTable  # ✅ Works (custom override)
```

---

## 7. Alternatives Considered

### 7.1 Option A: Keep Nested Configs (REJECTED)

**Pros**:

- Zero breaking changes
- Existing tests continue working
- More explicit field overrides per component

**Cons**:

- Violates spec decision Q9 (nested configs not needed)
- Extra layer of indirection for simple use cases
- Confusing for new users (parent fields vs nested config fields)
- Code maintenance burden (8 dataclasses to maintain)

**Decision**: REJECTED - Spec explicitly decided against nested configs

### 7.2 Option B: Immediate Removal (REJECTED)

**Pros**:

- Cleaner codebase immediately
- Forces migration to new API

**Cons**:

- Breaks existing tests without warning
- No migration period for external users
- Violates backwards compatibility principle

**Decision**: REJECTED - Too aggressive for existing users

### 7.3 Option C: Deprecation + Removal (SELECTED)

**Pros**:

- Clear migration path with warnings
- Gives users time to adapt
- Follows semantic versioning best practices
- Backwards compatible during deprecation period

**Cons**:

- Requires maintaining deprecated code for 1 release
- More complex implementation (detection + warnings)

**Decision**: SELECTED - Best balance of cleanliness and compatibility

---

## 8. Implementation Notes

### 8.1 File Removal Checklist

**Phase 1 (Deprecation - v0.8.0)**:

- [x] Add deprecation warnings in `ModelConfiguration.__init__()`
- [ ] Update documentation with migration guide
- [ ] Add migration examples to quickstart.md
- [ ] Update docstrings in config.py

**Phase 2 (Removal - v0.9.0)**:

- [ ] Remove nested config dataclasses from [components.py](../../fairdm/registry/components.py)
- [ ] Remove imports from [config.py](../../fairdm/registry/config.py) and [factories.py](../../fairdm/registry/factories.py)
- [ ] Update factory type hints to accept `dict | None` instead of config objects
- [ ] Remove nested config attributes from ModelConfiguration
- [ ] Update tests to use new API pattern
- [ ] Remove deprecation warnings (code is now removed)

### 8.2 Factory Signature Changes

**Before**:

```python
class FormFactory(ComponentFactory):
    def __init__(self, model: type[models.Model], config: FormConfig, parent_fields: list[str] | None = None):
        pass
```

**After**:

```python
class FormFactory(ComponentFactory):
    def __init__(self, model: type[models.Model], parent_fields: list[str] | None = None, custom_class: type | None = None):
        # config parameter removed, parent_fields becomes primary
        # custom_class optional override
        pass
```

### 8.3 Demo App Updates

**[fairdm_demo/config.py](../../fairdm_demo/config.py)** - NO CHANGES REQUIRED:

- Already uses legacy API pattern (component-specific fields)
- Already provides direct custom class overrides
- Will benefit from deprecation warnings if future updates use nested configs

---

## 9. Code Examples

### 9.1 Simple Registration (No Changes Needed)

```python
# WORKS BEFORE AND AFTER REMOVAL
@register
class RockSampleConfig(ModelConfiguration):
    model = RockSample
    fields = ['name', 'location', 'collected_at']
    # All components auto-generated from parent fields
```

### 9.2 Custom Form Migration

**Before (with nested config)**:

```python
@register
class RockSampleConfig(ModelConfiguration):
    model = RockSample
    fields = ['name', 'location']

    form = FormConfig(form_class=RockSampleForm)
```

**After (direct override)**:

```python
@register
class RockSampleConfig(ModelConfiguration):
    model = RockSample
    fields = ['name', 'location']

    form_class = RockSampleForm  # Direct attribute
```

### 9.3 Component-Specific Fields Migration

**Before (nested config with field override)**:

```python
@register
class RockSampleConfig(ModelConfiguration):
    model = RockSample
    fields = ['name', 'location', 'description']

    table = TableConfig(
        fields=['name', 'location'],  # Fewer fields than parent
        orderable=True
    )
```

**After (two options)**:

**Option 1: Custom Table Class** (RECOMMENDED):

```python
@register
class RockSampleConfig(ModelConfiguration):
    model = RockSample
    fields = ['name', 'location', 'description']

    table_class = RockSampleTable  # Define fields + orderable in Meta

# Define table class separately
class RockSampleTable(Table):
    class Meta:
        model = RockSample
        fields = ['name', 'location']
        orderable = True
```

**Option 2: Legacy Component Fields** (BACKWARDS COMPATIBLE):

```python
@register
class RockSampleConfig(ModelConfiguration):
    model = RockSample

    table_fields = ['name', 'location']  # Legacy attribute
    form_fields = ['name', 'location', 'description']  # Different fields
```

---

## 10. Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **External users depend on nested configs** | MEDIUM | HIGH | Deprecation warnings + migration guide + 1 release grace period |
| **Tests break during removal** | HIGH | LOW | Update tests during Phase 1, verify with CI |
| **Confusion about migration path** | MEDIUM | MEDIUM | Clear documentation with before/after examples |
| **Factory refactoring introduces bugs** | LOW | HIGH | Comprehensive test coverage before refactoring |
| **Backwards compatibility breaks** | LOW | HIGH | Keep legacy attributes (`table_fields`, etc.) indefinitely |

---

## 11. Decision Summary

### 11.1 Approved Changes

1. **Remove nested config dataclasses** (FormConfig, TableConfig, FiltersConfig, AdminConfig) from [components.py](../../fairdm/registry/components.py)
2. **Add deprecation warnings** in v0.8.0 for users still using nested config attributes
3. **Complete removal** in v0.9.0 after 1 release deprecation period
4. **Keep legacy API** (`table_fields`, `form_fields`, etc.) for backwards compatibility
5. **Promote new API** (parent `fields` + custom class overrides) as recommended pattern

### 11.2 Implementation Sequence

1. **Immediate**: Add deprecation warnings to `ModelConfiguration.__init__()`
2. **v0.8.0 Release**: Documentation updates + migration guide
3. **v0.9.0 Dev**: Remove nested config classes + update factories
4. **v0.9.0 Release**: Complete removal, clean API

### 11.3 Success Metrics

- ✅ Zero breaking changes to fairdm_demo during deprecation period
- ✅ All tests pass after factory refactoring
- ✅ Clear migration path documented with examples
- ✅ Deprecation warnings guide users to new API
- ✅ New API is simpler and matches spec Q9 decision

---

## References

- **Spec Decision**: [spec.md Q9](spec.md#L28) - "Not needed - Removed from spec. Simple configs use `fields` attribute, advanced users provide custom classes directly"
- **Current Implementation**: [fairdm/registry/components.py](../../fairdm/registry/components.py) - All nested config dataclasses
- **ModelConfiguration**: [fairdm/registry/config.py](../../fairdm/registry/config.py) - Uses nested configs in `__init__`
- **Factories**: [fairdm/registry/factories.py](../../fairdm/registry/factories.py) - Type hints reference config classes
- **Demo Usage**: [fairdm_demo/config.py](../../fairdm_demo/config.py) - Uses legacy API (no nested configs)
- **Research R5**: [research/R5-custom-class-override-pattern.md](research/R5-custom-class-override-pattern.md) - Custom class override patterns
