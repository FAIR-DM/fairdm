# Research Task R9: Backwards Compatibility Strategy

**Date**: 2026-01-12
**Status**: Complete
**Research Duration**: 1 hour

---

## Executive Summary

**Decision**: Implement **parallel APIs with gradual deprecation** to provide smooth migration path from old ModelConfiguration API to new simplified API.

**Key Finding**: The new API (`table_fields`, `form_fields`, `filterset_fields`, `resource_fields`) is already in use in `fairdm_demo` and fully functional. Backward compatibility properties (`list_fields`, `detail_fields`, `filter_fields`) exist in tests but need implementation in `ModelConfiguration` class itself.

**Migration Timeline**:

- **v1.0 (Current)**: Both APIs coexist, deprecation warnings enabled
- **v1.1-1.2**: Transition period (6-12 months)
- **v2.0**: Old API removed (breaking change)

---

## Current Usage Analysis

### What Patterns Exist in fairdm_demo Right Now

Examined [`fairdm_demo/config.py`](fairdm_demo/config.py) - **All 3 configurations already use the NEW API:**

```python
@register
class CustomParentSampleConfig(ModelConfiguration):
    model = CustomParentSample
    metadata = ModelMetadata(...)
    fields = [
        ("name", "status"),  # NEW API: tuple grouping syntax
        "char_field",
        ("added", "modified"),
    ]
    resource_class = SampleResource


@register
class CustomSampleConfig(ModelConfiguration):
    model = CustomSample
    metadata = ModelMetadata(...)

    # NEW API: Custom classes
    filterset_class = CustomSampleFilter
    table_class = CustomSampleTable

    # NEW API: Component-specific fields
    table_fields = ["name", "char_field", "boolean_field", "date_field", "added"]
    form_fields = ["name", "char_field", "text_field", ...]
    filterset_fields = ["char_field", "boolean_field", "date_field", "added"]
    resource_fields = ["name", "char_field", "text_field", ...]


@register
class ExampleMeasurementConfig(ModelConfiguration):
    model = ExampleMeasurement
    metadata = ModelMetadata(...)
    resource_class = MeasurementResource
    table_class = MeasurementTable
    fields = ["sample", "name", "char_field", ...]  # NEW API: general fields
```

**Current Patterns**:

1. ✅ **NEW API in use**: `table_fields`, `form_fields`, `filterset_fields`, `resource_fields`
2. ✅ **NEW API in use**: Custom classes via `table_class`, `filterset_class`, `resource_class`
3. ✅ **NEW API in use**: General `fields` attribute as fallback
4. ✅ **NEW API in use**: Tuple grouping for related fields
5. ❌ **OLD API NOT found**: No usage of `list_fields`, `detail_fields`, `filter_fields`

### Old vs New API Comparison

| Old API Pattern | New API Pattern | Migration Needed? |
|----------------|----------------|-------------------|
| `list_fields` | `table_fields` | ⚠️ Properties needed for BC |
| `detail_fields` | `form_fields` | ⚠️ Properties needed for BC |
| `filter_fields` | `filterset_fields` | ⚠️ Properties needed for BC |
| `form_class` (direct) | `form_class` (legacy support) | ✅ Already works |
| `table_class` (direct) | `table_class` (legacy support) | ✅ Already works |
| `filterset_class` (direct) | `filterset_class` (legacy support) | ✅ Already works |
| Nested config objects | Not in old API | ℹ️ New feature only |

---

## Analysis: Which Patterns Need Migration

### Already Working with New API ✅

1. **Custom Component Classes** - No migration needed

   ```python
   # This works now and will continue to work
   class MyConfig(ModelConfiguration):
       model = MySample
       form_class = CustomForm
       table_class = CustomTable
       filterset_class = CustomFilter
   ```

2. **General Fields Attribute** - No migration needed

   ```python
   # This works now and will continue to work
   class MyConfig(ModelConfiguration):
       model = MySample
       fields = ["name", "location", "collected_at"]
   ```

3. **Component-Specific Fields** - Already the recommended approach

   ```python
   # This is the NEW API and already works
   class MyConfig(ModelConfiguration):
       model = MySample
       table_fields = ["name", "location"]
       form_fields = ["name", "description", "location"]
       filterset_fields = ["location", "status"]
   ```

### Needs Backward Compatibility Layer ⚠️

**Only these three field properties need BC support:**

```python
# OLD API (needs deprecation warnings)
class OldStyleConfig(ModelConfiguration):
    model = MySample
    list_fields = ["name", "location"]      # → should map to table_fields
    detail_fields = ["name", "description"] # → should map to form_fields
    filter_fields = ["location", "status"]  # → should map to filterset_fields
```

**Implementation Status**:

- ✅ Tests exist that verify these properties work ([test_model_configuration.py:149](tests/test_registry/test_model_configuration.py#L149-L161))
- ❌ **Properties NOT implemented** in [`fairdm/registry/config.py`](fairdm/registry/config.py)
- ❌ **Getter methods referenced** in docs but missing: `get_list_fields()`, `get_detail_fields()`, `get_filter_fields()`

---

## Detection Strategy

### How to Detect Old API Usage

**Detection Logic** (to be implemented in `ModelConfiguration.__init__`):

```python
def __init__(self, model=None):
    """Initialize configuration with BC detection."""
    if model is not None:
        self.model = model

    # ... existing initialization ...

    # DETECTION: Check for old API usage
    self._check_deprecated_api_usage()

def _check_deprecated_api_usage(self):
    """Detect and warn about deprecated API usage."""
    import warnings
    import inspect

    # Get the class that defined these attributes (not inherited)
    cls = self.__class__

    # Check if old field properties are set at class level
    deprecated_attrs = {
        'list_fields': 'table_fields',
        'detail_fields': 'form_fields',
        'filter_fields': 'filterset_fields',
    }

    for old_attr, new_attr in deprecated_attrs.items():
        # Check if attribute is defined in this class (not inherited)
        if old_attr in cls.__dict__:
            # Get source location for better error messages
            source_file = inspect.getfile(cls)

            warnings.warn(
                f"{cls.__name__}.{old_attr} is deprecated. "
                f"Use {new_attr} instead. "
                f"Defined in: {source_file}",
                DeprecationWarning,
                stacklevel=3
            )
```

### Detection Triggers

Deprecation warnings shown when:

1. ✅ **Class attribute assignment**: `list_fields = [...]` at class level
2. ✅ **Property setter**: `config.list_fields = [...]` at runtime
3. ❌ **Property getter** *(no warning, silently works)*: `fields = config.list_fields`

---

## Deprecation Warning Messages

### Warning Message Template

```python
FutureWarning: {ConfigClassName}.{old_attribute} is deprecated and will be removed in FairDM 2.0.

  Replace:    {old_attribute} = {value}
  With:       {new_attribute} = {value}

  Location:   {file_path}:{line_number}

  Migration Guide: https://fairdm.readthedocs.io/migration-guides/v1-to-v2/
```

### Specific Warning Messages

#### 1. For `list_fields` → `table_fields`

```
FutureWarning: CustomSampleConfig.list_fields is deprecated and will be removed in FairDM 2.0.

  Replace:    list_fields = ["name", "created"]
  With:       table_fields = ["name", "created"]

  Location:   myapp/config.py:45

  Reason: 'table_fields' is more explicit about the component it configures.
  Migration Guide: https://fairdm.readthedocs.io/migration-guides/v1-to-v2/#field-attributes
```

#### 2. For `detail_fields` → `form_fields`

```
FutureWarning: WaterSampleConfig.detail_fields is deprecated and will be removed in FairDM 2.0.

  Replace:    detail_fields = ["name", "description", "location"]
  With:       form_fields = ["name", "description", "location"]

  Location:   waterlab/config.py:112

  Reason: 'form_fields' is more explicit about the component it configures.
  Migration Guide: https://fairdm.readthedocs.io/migration-guides/v1-to-v2/#field-attributes
```

#### 3. For `filter_fields` → `filterset_fields`

```
FutureWarning: MeasurementConfig.filter_fields is deprecated and will be removed in FairDM 2.0.

  Replace:    filter_fields = ["created", "status"]
  With:       filterset_fields = ["created", "status"]

  Location:   measurements/config.py:78

  Reason: 'filterset_fields' is more explicit about the component it configures.
  Migration Guide: https://fairdm.readthedocs.io/migration-guides/v1-to-v2/#field-attributes
```

---

## Migration Timeline

### Proposed Versions and Deprecation Schedule

#### **Phase 1: v1.0 (Current Release) - Parallel APIs**

- **Duration**: Initial release
- **Status**: Both old and new APIs work
- **Actions**:
  - ✅ New API (`table_fields`, etc.) is primary and documented
  - ⚠️ Old API (`list_fields`, etc.) works via properties **[TO IMPLEMENT]**
  - ⚠️ Deprecation warnings enabled **[TO IMPLEMENT]**
  - ⚠️ Migration guide published **[TO CREATE]**
- **Breaking Changes**: None
- **User Impact**: Zero - all existing code works

#### **Phase 2: v1.1-v1.2 (Transition Period)**

- **Duration**: 6-12 months after v1.0 release
- **Status**: Old API still works but loudly deprecated
- **Actions**:
  - ✅ New API improvements and features
  - ⚠️ Increase deprecation warning visibility
  - ⚠️ Add runtime warnings in development mode
  - ⚠️ Community outreach and migration assistance
- **Breaking Changes**: None
- **User Impact**: Warnings appear, but code still works

#### **Phase 3: v1.3-v1.5 (Final Transition)**

- **Duration**: 6 months before v2.0
- **Status**: Old API removal imminent
- **Actions**:
  - ⚠️ Change warnings from `DeprecationWarning` to `FutureWarning`
  - ⚠️ Add prominent notices in release notes
  - ⚠️ Create automated migration tool
  - ⚠️ Final community notifications
- **Breaking Changes**: None
- **User Impact**: Louder warnings, pressure to migrate

#### **Phase 4: v2.0 (Breaking Release)**

- **Duration**: After 12-18 months of deprecation
- **Status**: Old API removed
- **Actions**:
  - ❌ Remove `list_fields`, `detail_fields`, `filter_fields` properties
  - ❌ Remove getter methods for old API
  - ✅ Clean up codebase
  - ✅ Simplified documentation
- **Breaking Changes**: Old API no longer works
- **User Impact**: Code using old API will break

### Version Support Matrix

| API Feature | v1.0 | v1.1 | v1.2 | v1.3 | v1.5 | v2.0 |
|------------|------|------|------|------|------|------|
| `table_fields` (NEW) | ✅ Primary | ✅ Primary | ✅ Primary | ✅ Primary | ✅ Primary | ✅ Only |
| `form_fields` (NEW) | ✅ Primary | ✅ Primary | ✅ Primary | ✅ Primary | ✅ Primary | ✅ Only |
| `filterset_fields` (NEW) | ✅ Primary | ✅ Primary | ✅ Primary | ✅ Primary | ✅ Primary | ✅ Only |
| `list_fields` (OLD) | ⚠️ Deprecated | ⚠️ Deprecated | ⚠️ Deprecated | ⚠️ Deprecated | ⚠️ Deprecated | ❌ Removed |
| `detail_fields` (OLD) | ⚠️ Deprecated | ⚠️ Deprecated | ⚠️ Deprecated | ⚠️ Deprecated | ⚠️ Deprecated | ❌ Removed |
| `filter_fields` (OLD) | ⚠️ Deprecated | ⚠️ Deprecated | ⚠️ Deprecated | ⚠️ Deprecated | ⚠️ Deprecated | ❌ Removed |

---

## Migration Guide Outline

### Sections and Content for Developer Docs

#### **1. Overview**

- **Title**: "Migrating from FairDM 0.x to 1.x ModelConfiguration API"
- **Content**:
  - Why the API changed (clarity, explicitness, consistency)
  - Timeline for deprecation
  - Assurance that migration is straightforward

#### **2. Quick Start - Common Cases**

##### **Case 1: Simple Field Lists**

```python
# OLD API (v0.x)
class MySampleConfig(ModelConfiguration):
    model = MySample
    list_fields = ["name", "location", "created"]
    detail_fields = ["name", "description", "location", "created"]
    filter_fields = ["location", "created"]

# NEW API (v1.x)
class MySampleConfig(ModelConfiguration):
    model = MySample
    table_fields = ["name", "location", "created"]     # Renamed from list_fields
    form_fields = ["name", "description", "location", "created"]  # Renamed from detail_fields
    filterset_fields = ["location", "created"]          # Renamed from filter_fields
```

##### **Case 2: Using General Fields as Fallback**

```python
# OLD API (v0.x) - Not really an old pattern, but showing the evolution
class MySampleConfig(ModelConfiguration):
    model = MySample
    fields = ["name", "location", "created"]
    # All components use these fields

# NEW API (v1.x) - Same, but more explicit when needed
class MySampleConfig(ModelConfiguration):
    model = MySample
    fields = ["name", "location", "created"]  # ✅ Still works! Fallback for all components
    table_fields = ["name", "location"]        # Override just for tables
```

##### **Case 3: Custom Component Classes**

```python
# OLD API (v0.x)
class MySampleConfig(ModelConfiguration):
    model = MySample
    form_class = CustomForm
    table_class = CustomTable
    filterset_class = CustomFilter

# NEW API (v1.x)
class MySampleConfig(ModelConfiguration):
    model = MySample
    form_class = CustomForm          # ✅ Still works exactly the same!
    table_class = CustomTable        # ✅ Still works exactly the same!
    filterset_class = CustomFilter   # ✅ Still works exactly the same!
```

#### **3. What Changed and Why**

| Old Name | New Name | Reason for Change |
|----------|----------|------------------|
| `list_fields` | `table_fields` | More explicit - clearly indicates Django Tables2 table configuration |
| `detail_fields` | `form_fields` | More explicit - clearly indicates Django forms configuration |
| `filter_fields` | `filterset_fields` | More explicit - clearly indicates django-filter FilterSet configuration |

**Benefits of New Names**:

1. **Explicit**: Clear what component each setting affects
2. **Consistent**: Follows pattern `{component}_fields`
3. **Discoverable**: IDE autocomplete shows component-specific options
4. **Future-proof**: Easier to add new components (e.g., `api_fields`, `serializer_fields`)

#### **4. Complete Migration Checklist**

- [ ] Search codebase for `list_fields` → replace with `table_fields`
- [ ] Search codebase for `detail_fields` → replace with `form_fields`
- [ ] Search codebase for `filter_fields` → replace with `filterset_fields`
- [ ] Run tests to ensure nothing broke
- [ ] Remove any custom `get_list_fields()` method overrides
- [ ] Remove any custom `get_detail_fields()` method overrides
- [ ] Remove any custom `get_filter_fields()` method overrides
- [ ] Update documentation strings in your configs
- [ ] Run linter to catch any deprecation warnings

#### **5. Automated Migration Tool**

```bash
# Use the FairDM migration command
python manage.py fairdm_migrate_config --dry-run
# Review changes
python manage.py fairdm_migrate_config --apply
```

#### **6. FAQ**

**Q: Will my existing code break?**
A: No! Your code will work in v1.x with deprecation warnings. You have 12-18 months to migrate before v2.0.

**Q: What if I'm using both old and new attributes?**
A: New attributes take precedence. If you set `table_fields`, it will be used even if `list_fields` is also set.

**Q: Can I keep using `fields` as a general fallback?**
A: Yes! The general `fields` attribute is NOT deprecated and continues to work as a fallback when component-specific fields aren't specified.

**Q: Do I need to migrate custom classes (`form_class`, etc.)?**
A: No! Custom class attributes are unchanged and fully supported.

#### **7. Getting Help**

- **Documentation**: <https://fairdm.readthedocs.io/>
- **Migration Issues**: <https://github.com/FAIR-DM/fairdm/issues>
- **Community Forum**: <https://github.com/FAIR-DM/fairdm/discussions>

---

## Breaking vs Compatible Changes

### Backwards Compatible (Safe) ✅

These changes are **non-breaking** and can be made immediately:

1. **Adding new attributes** (`table_fields`, `form_fields`, `filterset_fields`)
   - Users can adopt at their own pace
   - Old code continues to work

2. **Adding property getters/setters** for backward compatibility
   - `list_fields` property → reads/writes `table_fields`
   - `detail_fields` property → reads/writes `form_fields`
   - `filter_fields` property → reads/writes `filterset_fields`

3. **Adding deprecation warnings**
   - Warnings don't break code
   - Help users discover they need to migrate

4. **Adding new helper methods** (`get_table_fields()`, etc.)
   - Doesn't affect existing code

5. **Extending nested config objects** (TableConfig, FormConfig, etc.)
   - Pure additions don't break anything

### Breaking Changes (v2.0 Only) ❌

These changes **MUST wait** until v2.0:

1. **Removing `list_fields` property**
   - Code using `config.list_fields` will raise `AttributeError`

2. **Removing `detail_fields` property**
   - Code using `config.detail_fields` will raise `AttributeError`

3. **Removing `filter_fields` property**
   - Code using `config.filter_fields` will raise `AttributeError`

4. **Removing `get_list_fields()` method** (if exists)
   - Code calling this method will raise `AttributeError`

5. **Removing `get_detail_fields()` method** (if exists)
   - Code calling this method will raise `AttributeError`

6. **Removing `get_filter_fields()` method** (if exists)
   - Code calling this method will raise `AttributeError`

### Change Impact Matrix

| Change Type | v1.0 | v1.x Transition | v2.0 | User Impact |
|------------|------|----------------|------|-------------|
| Add new attributes | ✅ Yes | ✅ Yes | ✅ Yes | None - pure addition |
| Add BC properties | ✅ Yes | ✅ Yes | ✅ Yes | None - pure addition |
| Add deprecation warnings | ⚠️ Yes | ⚠️ Yes | N/A | Warnings only |
| Remove old properties | ❌ No | ❌ No | ✅ Yes | **Breaking** |
| Remove old methods | ❌ No | ❌ No | ✅ Yes | **Breaking** |

---

## Alternatives Considered

### Option 1: Big Bang Migration ❌ Rejected

**Approach**: Remove old API immediately, require all portals to update at once.

**Pros**:

- Clean break, no technical debt
- Simpler codebase
- Clear direction

**Cons**:

- **Breaks all existing portals immediately**
- Forces urgent migrations across ecosystem
- High risk of community backlash
- Could delay portal updates
- Emergency support burden

**Verdict**: ❌ **Rejected** - Too disruptive for ecosystem

### Option 2: Gradual Deprecation (Parallel APIs) ✅ SELECTED

**Approach**: Support both old and new APIs with deprecation warnings, remove old API in v2.0 after 12-18 months.

**Pros**:

- **Zero disruption** to existing portals
- Clear migration path with plenty of time
- Deprecation warnings guide users
- Community can migrate at own pace
- Clean removal in v2.0

**Cons**:

- Temporary code complexity (property shims)
- Need to maintain both APIs during transition
- Documentation must cover both APIs

**Verdict**: ✅ **SELECTED** - Best balance of stability and progress

### Option 3: Keep Both APIs Forever 🤷 Considered

**Approach**: Never remove old API, support both indefinitely.

**Pros**:

- Maximum backward compatibility
- Zero migration pressure

**Cons**:

- **Technical debt accumulates forever**
- Confusing documentation (which one to use?)
- More complex codebase to maintain
- Harder to add new features
- New users confused by multiple ways

**Verdict**: 🤷 **Not Recommended** - Creates long-term maintenance burden

### Option 4: Automated Migration Tool Only ⚠️ Partial

**Approach**: Provide tool that automatically converts old API to new API in user code.

**Pros**:

- Fast migration for users
- Reduces manual work

**Cons**:

- Tool might not catch all cases
- Doesn't help with runtime compatibility
- Still need parallel APIs during migration

**Verdict**: ⚠️ **Complement to Option 2** - Good addition but not standalone solution

---

## Implementation Notes

### Testing Both APIs

**Test Strategy**:

1. **Duplicate tests** for BC period:

   ```python
   class TestBackwardCompatibility:
       def test_list_fields_maps_to_table_fields(self):
           config = ModelConfiguration(model=Sample)
           config.list_fields = ["name", "created"]
           assert config.table_fields == ["name", "created"]

       def test_detail_fields_maps_to_form_fields(self):
           config = ModelConfiguration(model=Sample)
           config.detail_fields = ["name", "description"]
           assert config.form_fields == ["name", "description"]
   ```

2. **Integration tests** verify both APIs produce same result:

   ```python
   def test_old_and_new_api_equivalent(self):
       old_config = ModelConfiguration(model=Sample)
       old_config.list_fields = ["name", "created"]

       new_config = ModelConfiguration(model=Sample)
       new_config.table_fields = ["name", "created"]

       assert old_config.get_table_class().Meta.fields == new_config.get_table_class().Meta.fields
   ```

3. **Deprecation warning tests**:

   ```python
   def test_old_api_shows_deprecation_warning(self):
       with warnings.catch_warnings(record=True) as w:
           warnings.simplefilter("always")

           class OldStyleConfig(ModelConfiguration):
               model = Sample
               list_fields = ["name"]

           assert len(w) == 1
           assert issubclass(w[0].category, DeprecationWarning)
           assert "list_fields is deprecated" in str(w[0].message)
   ```

### Validation Logic

**Priority Order** when both old and new APIs are used:

```python
def _resolve_table_fields(self):
    """Determine which table fields to use, with BC support."""
    # 1. NEW API takes precedence
    if hasattr(self, 'table_fields') and self.table_fields:
        return self.table_fields

    # 2. OLD API (with deprecation warning)
    if hasattr(self, '_list_fields_value'):  # Set via property
        return self._list_fields_value

    # 3. Fallback to general fields
    if self.fields:
        return self.fields

    # 4. Smart defaults
    return self._get_default_table_fields()
```

### Property Implementation

```python
# In ModelConfiguration class

@property
def list_fields(self) -> list[str]:
    """DEPRECATED: Use table_fields instead.

    This property provides backward compatibility for the old API.
    Will be removed in FairDM 2.0.
    """
    return self.table_fields

@list_fields.setter
def list_fields(self, value: list[str]):
    """DEPRECATED: Use table_fields instead."""
    import warnings
    warnings.warn(
        f"{self.__class__.__name__}.list_fields is deprecated. "
        "Use table_fields instead. "
        "This will be removed in FairDM 2.0.",
        DeprecationWarning,
        stacklevel=2
    )
    self.table_fields = value

@property
def detail_fields(self) -> list[str]:
    """DEPRECATED: Use form_fields instead."""
    return self.form_fields

@detail_fields.setter
def detail_fields(self, value: list[str]):
    """DEPRECATED: Use form_fields instead."""
    import warnings
    warnings.warn(
        f"{self.__class__.__name__}.detail_fields is deprecated. "
        "Use form_fields instead. "
        "This will be removed in FairDM 2.0.",
        DeprecationWarning,
        stacklevel=2
    )
    self.form_fields = value

@property
def filter_fields(self) -> list[str]:
    """DEPRECATED: Use filterset_fields instead."""
    return self.filterset_fields

@filter_fields.setter
def filter_fields(self, value: list[str]):
    """DEPRECATED: Use filterset_fields instead."""
    import warnings
    warnings.warn(
        f"{self.__class__.__name__}.filter_fields is deprecated. "
        "Use filterset_fields instead. "
        "This will be removed in FairDM 2.0.",
        DeprecationWarning,
        stacklevel=2
    )
    self.filterset_fields = value
```

### Method Implementation

**Getter methods that may exist in old code** (need to verify if these exist):

```python
def get_list_fields(self) -> list[str]:
    """DEPRECATED: Use get_table_fields() or access table_fields directly.

    Returns table fields for backward compatibility.
    Will be removed in FairDM 2.0.
    """
    import warnings
    warnings.warn(
        "get_list_fields() is deprecated. Use table_fields directly. "
        "This will be removed in FairDM 2.0.",
        DeprecationWarning,
        stacklevel=2
    )
    return self.table_fields or self.fields or self._get_default_table_fields()

def get_detail_fields(self) -> list[str]:
    """DEPRECATED: Use get_form_fields() or access form_fields directly."""
    import warnings
    warnings.warn(
        "get_detail_fields() is deprecated. Use form_fields directly. "
        "This will be removed in FairDM 2.0.",
        DeprecationWarning,
        stacklevel=2
    )
    return self.form_fields or self.fields or self._get_default_form_fields()

def get_filter_fields(self) -> list[str]:
    """DEPRECATED: Use get_filterset_fields() or access filterset_fields directly."""
    import warnings
    warnings.warn(
        "get_filter_fields() is deprecated. Use filterset_fields directly. "
        "This will be removed in FairDM 2.0.",
        DeprecationWarning,
        stacklevel=2
    )
    return self.filterset_fields or self.fields or self._get_default_filter_fields()
```

---

## Code Examples: Before/After Migration

### Example 1: Basic Configuration

#### Before (Old API)

```python
from fairdm.registry import register
from fairdm.registry.config import ModelConfiguration

@register
class WaterSampleConfig(ModelConfiguration):
    model = WaterSample

    # Old API - confusing names
    list_fields = ["name", "location", "ph_level", "collected_at"]
    detail_fields = ["name", "description", "location", "ph_level", "temperature", "collected_at"]
    filter_fields = ["location", "ph_level", "collected_at"]
```

#### After (New API)

```python
from fairdm.registry import register
from fairdm.registry.config import ModelConfiguration

@register
class WaterSampleConfig(ModelConfiguration):
    model = WaterSample

    # New API - explicit component names
    table_fields = ["name", "location", "ph_level", "collected_at"]
    form_fields = ["name", "description", "location", "ph_level", "temperature", "collected_at"]
    filterset_fields = ["location", "ph_level", "collected_at"]
```

**Benefits**: Immediately clear which component each setting affects.

### Example 2: Using General Fields Fallback

#### Before (Old API)

```python
@register
class SoilSampleConfig(ModelConfiguration):
    model = SoilSample

    # Had to duplicate fields everywhere
    list_fields = ["name", "location", "collected_at"]
    detail_fields = ["name", "location", "collected_at"]  # Same as list_fields
    filter_fields = ["location", "collected_at"]
```

#### After (New API)

```python
@register
class SoilSampleConfig(ModelConfiguration):
    model = SoilSample

    # Use general fields as default for all components
    fields = ["name", "location", "collected_at"]

    # Only override where needed
    filterset_fields = ["location", "collected_at"]  # Exclude "name" from filters
```

**Benefits**: Less repetition, DRY principle.

### Example 3: Mixed Custom and Generated Components

#### Before (Old API)

```python
from myapp.forms import CustomWaterSampleForm
from myapp.filters import CustomWaterSampleFilter

@register
class WaterSampleConfig(ModelConfiguration):
    model = WaterSample

    # Custom form
    form_class = CustomWaterSampleForm

    # But still need list_fields for auto-generated table
    list_fields = ["name", "location", "ph_level"]

    # Custom filter
    filterset_class = CustomWaterSampleFilter
```

#### After (New API)

```python
from myapp.forms import CustomWaterSampleForm
from myapp.filters import CustomWaterSampleFilter

@register
class WaterSampleConfig(ModelConfiguration):
    model = WaterSample

    # Custom components - unchanged
    form_class = CustomWaterSampleForm
    filterset_class = CustomWaterSampleFilter

    # Auto-generated components - now explicit
    table_fields = ["name", "location", "ph_level"]
```

**Benefits**: Same custom class usage, but clearer field configuration.

### Example 4: Advanced with Nested Config Objects

#### Before (Old API - didn't exist)

```python
# This pattern didn't exist in old API
# You could only use simple field lists
```

#### After (New API - NEW FEATURE)

```python
from fairdm.registry.config import ModelConfiguration, TableConfig, FiltersConfig

@register
class AdvancedWaterSampleConfig(ModelConfiguration):
    model = WaterSample

    # Simple fields as fallback
    fields = ["name", "location", "ph_level", "collected_at"]

    # Advanced table configuration
    table = TableConfig(
        fields=["name", "location", "ph_level"],
        orderable=True,
        exclude=["internal_notes"],
    )

    # Advanced filter configuration
    filters = FiltersConfig(
        fields=["location", "ph_level", "collected_at"],
        range_fields=["ph_level", "collected_at"],
        exact_fields=["location"],
    )
```

**Benefits**: New capability - fine-grained control over component behavior.

---

## Priority: Migration Guide Content

### What Portal Developers Need to Know

1. **Immediate Impact**: None - existing code continues to work
2. **Action Required**: Update field attribute names when convenient
3. **Timeline**: 12-18 months before breaking changes in v2.0
4. **Effort**: Simple find-and-replace (3 attribute renames)
5. **Benefit**: Clearer, more maintainable configuration

### Critical Information to Communicate

1. **No Panic**: Your code works now and will continue to work in v1.x
2. **Simple Change**: Just rename 3 attributes when you have time
3. **Better DX**: New names make code more readable and maintainable
4. **Community Support**: Help available if you run into issues
5. **Automated Tools**: Migration script available to help

---

## Recommendations

### Immediate Actions (Sprint 4)

1. ✅ **Implement backward compatibility properties** in ModelConfiguration
   - Add `list_fields`, `detail_fields`, `filter_fields` properties with deprecation warnings
   - Ensure tests pass

2. ✅ **Implement deprecated getter methods** if they're referenced
   - `get_list_fields()`, `get_detail_fields()`, `get_filter_fields()`
   - Add deprecation warnings

3. ✅ **Update documentation** to clearly show new API as primary
   - Mark old API patterns as deprecated
   - Add migration guide section

4. ⚠️ **No changes needed in fairdm_demo** - already uses new API!

### Near-Term Actions (v1.1 Release)

1. ⚠️ **Create automated migration tool**
   - Django management command: `fairdm_migrate_config`
   - Scans Python files and offers to update automatically

2. ⚠️ **Enhance deprecation warnings**
   - Show file/line number where deprecated API is used
   - Include direct link to migration guide

3. ⚠️ **Community outreach**
   - Blog post explaining the change
   - Forum discussions
   - Email to known portal developers

### Long-Term Actions (v1.x → v2.0)

1. ⚠️ **Monitor adoption** via deprecation warning telemetry (optional)
2. ⚠️ **Support community** during migration
3. ⚠️ **Plan v2.0 breaking release** after 12-18 months
4. ⚠️ **Remove old API** in v2.0 release

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Existing portals break unexpectedly | High | Parallel APIs with BC layer prevents immediate breakage |
| Portal developers miss deprecation warnings | Medium | Multiple warning channels: console, logs, docs, emails |
| Migration tool doesn't catch all cases | Low | Manual migration guide as backup; tool is convenience only |
| Community resists change | Low | Change is minor (3 renames); plenty of transition time |
| Documentation confusion | Medium | Clear visual distinction between old/new API in docs |

---

## Success Criteria

**Sprint 4 (Immediate)**:

- ✅ Backward compatibility properties implemented and tested
- ✅ All existing tests pass (including BC tests)
- ✅ Documentation clearly marks old API as deprecated
- ✅ Migration guide section created

**v1.1 Release**:

- ⚠️ At least 50% of known portals migrated to new API
- ⚠️ Automated migration tool available
- ⚠️ Zero bug reports related to BC layer

**v2.0 Release** (12-18 months):

- ⚠️ At least 90% of known portals migrated
- ⚠️ Clean removal of old API code
- ⚠️ Simplified documentation with only new API

---

## Conclusion

**The backward compatibility strategy is straightforward**:

1. **Implement property shims** for 3 deprecated attributes (`list_fields`, `detail_fields`, `filter_fields`)
2. **Add deprecation warnings** to guide migration
3. **Document migration path** clearly
4. **Give 12-18 months** transition period
5. **Remove old API in v2.0** after ample transition time

This approach **minimizes disruption** while **enabling ecosystem evolution**. The change is **simple** (3 attribute renames), the **timeline is generous** (12-18 months), and the **benefit is clear** (more explicit, maintainable code).

Portal developers will appreciate the **smooth transition** and **clear communication** around the change.
