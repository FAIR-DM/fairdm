# Research Task R4: Field Resolution Algorithm

**Date**: 2026-01-12
**Branch**: `002-fairdm-registry`
**Related Spec**: [spec.md](./spec.md) (FR-003, FR-006)

## Executive Summary

This research defines the comprehensive field resolution algorithm that transforms a parent `fields` attribute into component-specific configurations for Tables, Filters, Forms, Serializers, and Admin interfaces. The algorithm uses intelligent type mapping based on Django field types, handles related field lookups (double-underscore paths), applies sensible default exclusions, and provides special handling for complex field types (JSONField, ImageField, polymorphic fields, translatable fields).

**Key Decision**: Use a two-stage resolution pattern: (1) Field list resolution with fallback chain, (2) Component-specific type mapping based on field introspection.

---

## 1. Current Implementation Analysis

### 1.1 Existing Field Resolution in factories.py

The current implementation in [fairdm/registry/factories.py](../../fairdm/registry/factories.py) uses a fallback chain:

```python
def get_fields(self) -> list[str]:
    """Get fields to use, with intelligent fallback chain.

    Resolution order:
    1. Component-specific fields (e.g., config.Table.fields)
    2. Global fields (config.fields)
    3. Auto-detected safe fields (inspector.get_safe_fields())
    """
    # If config specifies fields, use them
    if hasattr(self.config, "fields") and self.config.fields is not None:
        if self.config.fields == "__all__":
            return self.inspector.get_all_field_names()
        return self.config.fields

    # Otherwise, use safe fields
    return self.inspector.get_safe_fields()
```

Each factory (FormFactory, TableFactory, FilterFactory) overrides `get_fields()` to use parent_fields:

```python
# TableFactory.get_fields()
if self.config.fields is not None:
    fields = self.config.fields
# Fall back to parent fields
elif self.parent_fields:
    fields = self.parent_fields
# Use inspector's smart defaults
else:
    fields = self.inspector.get_default_list_fields()
```

### 1.2 FieldInspector Smart Detection

The [FieldInspector](../../fairdm/utils/inspection.py) provides intelligent defaults:

**Field Exclusion Logic** (lines 95-121):

```python
ALWAYS_EXCLUDE = [
    "id",
    "polymorphic_ctype",
    "polymorphic_ctype_id",
]

EXCLUDE_PATTERNS = [
    "_ptr",  # Polymorphic pointer fields
    "_ptr_id",
    "password",  # Security sensitive
]

def should_exclude_field(self, field_name: str) -> bool:
    # Check always exclude list
    if field_name in self.ALWAYS_EXCLUDE:
        return True

    # Check patterns
    if any(pattern in field_name for pattern in self.EXCLUDE_PATTERNS):
        return True

    # Check field properties
    field = self.get_field(field_name)
    if field is None:
        return True

    # Exclude auto-generated fields
    if hasattr(field, "auto_now") and field.auto_now:
        return True
    if hasattr(field, "auto_now_add") and field.auto_now_add:
        return True

    # Exclude non-editable fields (except ForeignKey which might be editable=False for admin)
    return not field.editable and not isinstance(field, self.RELATION_TYPES)
```

**Default List Fields** (lines 359-392):

```python
def get_default_list_fields(self) -> list[str]:
    """Get default fields suitable for list/table display."""
    candidates = self.get_safe_fields()
    list_fields = []

    # Prioritize common fields
    priority_fields = ["name", "title", "status", "created", "modified"]

    for field_name in priority_fields:
        if field_name in candidates:
            list_fields.append(field_name)

    # Add other safe fields up to a reasonable limit
    for field_name in candidates:
        if field_name in list_fields:
            continue

        # Skip text fields and relations for list view
        field = self.get_field(field_name)
        if isinstance(field, models.TextField):
            continue
        if isinstance(field, models.ManyToManyField):
            continue

        list_fields.append(field_name)

        # Limit to ~5 fields for list view
        if len(list_fields) >= 5:
            break

    return list_fields
```

**Default Filter Fields** (lines 397-421):

```python
def get_default_filter_fields(self) -> list[str]:
    """Get default fields suitable for filtering."""
    filter_fields = []

    # Date fields are good for filtering
    filter_fields.extend(self.get_date_fields())

    # Choice fields
    filter_fields.extend(self.get_choice_fields())

    # Boolean fields
    filter_fields.extend(self.get_boolean_fields())

    # Foreign keys (but not M2M to avoid complexity)
    for field in self._get_all_fields():
        if isinstance(field, models.ForeignKey) and not self.should_exclude_field(field.name):
            filter_fields.append(field.name)

    return list(set(filter_fields))  # Remove duplicates
```

---

## 2. Field Type Mapping

### 2.1 Django Field → Table Column

**Implementation**: django-tables2's `table_factory()` handles most mappings automatically. Special cases:

| Django Field Type | django-tables2 Column | Notes |
|-------------------|----------------------|-------|
| CharField | Column | Default text column |
| TextField | Column (truncated) | Should be excluded from default list (too long) |
| IntegerField | Column | Right-aligned by default |
| DecimalField | Column | Right-aligned, formatted |
| FloatField | Column | Right-aligned, formatted |
| BooleanField | BooleanColumn | Shows ✓/✗ icons |
| DateField | DateColumn | Formatted date |
| DateTimeField | DateTimeColumn | Formatted datetime |
| ForeignKey | Column (shows **str**) | Use accessor for nested: `project__title` |
| ManyToManyField | **EXCLUDE** | Too complex for table display |
| ImageField | ImageColumn (custom) | Thumbnail display |
| FileField | FileColumn | Download link |
| JSONField | **EXCLUDE** | Not displayable in table |
| URLField | URLColumn | Clickable link |
| EmailField | EmailColumn | mailto: link |

**Current Implementation**: [TableFactory.generate()](../../fairdm/registry/factories.py#L257-L311)

```python
# django-tables2 table_factory handles type mapping automatically
table_class = table_factory(
    self.model,
    table=self.get_base_table_class(),
    fields=fields,
)
```

### 2.2 Django Field → Filter Type

**Implementation**: [FieldInspector.suggest_filter_type()](../../fairdm/utils/inspection.py#L310-L355)

| Django Field Type | django-filter Filter | Lookup Expression | Notes |
|-------------------|---------------------|-------------------|-------|
| CharField | CharFilter | `icontains` | Case-insensitive search |
| TextField | CharFilter | `icontains` | Case-insensitive search |
| IntegerField | RangeFilter | `gte`, `lte` | Min/max inputs |
| DecimalField | RangeFilter | `gte`, `lte` | Min/max inputs |
| FloatField | RangeFilter | `gte`, `lte` | Min/max inputs |
| BooleanField | BooleanFilter | `exact` | Yes/No/Unknown dropdown |
| DateField | DateFromToRangeFilter | `gte`, `lte` | Date range picker |
| DateTimeField | DateFromToRangeFilter | `gte`, `lte` | DateTime range picker |
| ForeignKey | ModelChoiceFilter | `exact` | Dropdown of related objects |
| ManyToManyField | ModelMultipleChoiceFilter | `exact` | Multi-select of related objects |
| ChoiceField | MultipleChoiceFilter | `exact` | Multi-select from choices |
| JSONField | **EXCLUDE** | N/A | Not filterable |
| ImageField | **EXCLUDE** | N/A | Not filterable |
| FileField | **EXCLUDE** | N/A | Not filterable |

**Current Implementation**: [FilterFactory.get_filter_overrides()](../../fairdm/registry/factories.py#L368-L409)

```python
def suggest_filter_type(self, field_name: str) -> str | None:
    field = self.get_field(field_name)
    if field is None:
        return None

    # Date fields get range filters
    if isinstance(field, (models.DateField, models.DateTimeField)):
        return "DateFromToRangeFilter"

    # Boolean fields
    if isinstance(field, models.BooleanField):
        return "BooleanFilter"

    # Choice fields
    if hasattr(field, "choices") and field.choices:
        return "MultipleChoiceFilter"

    # Foreign keys
    if isinstance(field, models.ForeignKey):
        return "ModelChoiceFilter"
    if isinstance(field, models.ManyToManyField):
        return "ModelMultipleChoiceFilter"

    # Numeric fields
    if isinstance(field, (models.IntegerField, models.BigIntegerField,
                         models.FloatField, models.DecimalField)):
        return "RangeFilter"

    # Text fields
    if isinstance(field, (models.CharField, models.TextField)):
        return "CharFilter"  # Will use icontains

    return None
```

**Special Filter Configurations** (from [FiltersConfig](../../fairdm/registry/components.py#L56-L76)):

- `exact_fields`: Fields that use exact match instead of icontains
- `range_fields`: Fields that should use range filters (override default)
- `search_fields`: Fields that explicitly use icontains lookup
- `filter_overrides`: Custom filter class per field

### 2.3 Django Field → Form Widget

**Implementation**: [FieldInspector.suggest_widget()](../../fairdm/utils/inspection.py#L257-L308)

| Django Field Type | Form Widget | Notes |
|-------------------|-------------|-------|
| CharField | TextInput | Default text input |
| TextField | Textarea | Multi-line text |
| IntegerField | NumberInput | Number input with step |
| DecimalField | NumberInput | Number input with decimals |
| FloatField | NumberInput | Number input |
| BooleanField | CheckboxInput | Single checkbox |
| DateField | DateInput | Date picker (HTML5 or widget) |
| DateTimeField | SplitDateTimeWidget | Separate date and time inputs |
| TimeField | TimeInput | Time picker |
| ForeignKey | Select2Widget | Searchable dropdown (django-select2) |
| ManyToManyField | Select2MultipleWidget | Multi-select (django-select2) |
| ChoiceField (≤5 choices) | RadioSelect | Radio buttons for few options |
| ChoiceField (>5 choices) | Select | Dropdown for many options |
| ImageField | ImageWidget | File input with preview |
| FileField | FileInput | File upload |
| URLField | URLInput | URL validation |
| EmailField | EmailInput | Email validation |
| JSONField | Textarea (+ validation) | JSON editor widget |

**Current Implementation**:

```python
def suggest_widget(self, field_name: str) -> str | None:
    field = self.get_field(field_name)
    if field is None:
        return None

    # Date/time fields (check DateTime before Date)
    if isinstance(field, models.DateTimeField):
        return "SplitDateTimeWidget"
    if isinstance(field, models.TimeField):
        return "TimeInput"
    if isinstance(field, models.DateField):
        return "DateInput"

    # File fields
    if isinstance(field, models.ImageField):
        return "ImageWidget"
    if isinstance(field, models.FileField):
        return "FileInput"

    # Relationship fields
    if isinstance(field, models.ForeignKey):
        return "Select2Widget"
    if isinstance(field, models.ManyToManyField):
        return "Select2MultipleWidget"

    # Text fields
    if isinstance(field, models.TextField):
        return "Textarea"
    if isinstance(field, models.URLField):
        return "URLInput"
    if isinstance(field, models.EmailField):
        return "EmailInput"

    # Choice fields
    if hasattr(field, "choices") and field.choices:
        choice_count = len(field.choices)
        if choice_count <= 5:
            return "RadioSelect"
        return "Select"

    # Boolean
    if isinstance(field, models.BooleanField):
        return "CheckboxInput"

    return None
```

---

## 3. Related Field Handling (Double-Underscore Lookups)

### 3.1 How Double-Underscore Paths Work

Django's ORM uses `__` to traverse relationships. Example: `project__owner__name`

**Component Support**:

| Component | Support | Implementation | Example |
|-----------|---------|----------------|---------|
| **django-tables2** | ✅ Full | Accessor class handles traversal | `Column(accessor='project__title')` |
| **django-filter** | ✅ Full | `field_name` parameter | `CharFilter(field_name='project__owner__name')` |
| **ModelForm** | ❌ No | Forms only show direct fields | N/A |
| **DRF Serializer** | ⚠️ Partial | Use nested serializers instead | `ProjectSerializer()` |
| **import-export** | ✅ Full | `fields` supports __ notation | `'project__title'` |

### 3.2 Validation Strategy

**Implementation** (from [research-R3-validation-strategy.md](./research-R3-validation-strategy.md#42-relationship-path-validation)):

```python
def validate_relationship_path(model_class, field_path):
    """Validate a relationship path like 'project__owner__name'."""
    from django.core.exceptions import FieldDoesNotExist

    parts = field_path.split('__')
    current_model = model_class

    # All parts except last must be relations
    for i, part in enumerate(parts[:-1]):
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

### 3.3 Component-Specific Handling

**Tables** (django-tables2):

```python
# Automatic with Accessor
fields = ['name', 'project__title', 'project__owner__name']
table_class = table_factory(model, fields=fields)
# django-tables2 automatically creates columns with Accessor
```

**Filters** (django-filter):

```python
# Use field_name parameter
class SampleFilterSet(FilterSet):
    project_title = CharFilter(
        field_name='project__title',
        lookup_expr='icontains'
    )
```

**Filters from field list**:

```python
# For auto-generation, create filters with field_name
fields = ['name', 'project__title']
for field_name in fields:
    if '__' in field_name:
        # Get the final field type from the related model
        related_field = resolve_field_path(model, field_name)
        filter_class = suggest_filter_type(related_field)
        # Create filter with field_name parameter
```

**Forms** (ModelForm):

```python
# Forms cannot use related fields - exclude them
fields = ['name', 'project__title', 'description']
form_fields = [f for f in fields if '__' not in f]
# Only ['name', 'description'] remain
```

**Serializers** (DRF):

```python
# Use nested serializers for related objects
fields = ['name', 'project__title']
# Split into direct fields and related serializers
direct_fields = ['name']
nested = {'project': ProjectSerializer(read_only=True)}
```

**Import/Export**:

```python
# Works with __ notation directly
fields = ['name', 'project__title', 'project__owner__name']
resource_class = ModelResource
resource_class.Meta.fields = fields
# Handles lookups automatically
```

---

## 4. Default Exclusions

### 4.1 Always Exclude (All Components)

From [FieldInspector.ALWAYS_EXCLUDE](../../fairdm/utils/inspection.py#L28-L32):

```python
ALWAYS_EXCLUDE = [
    "id",                      # Primary key (auto-generated)
    "polymorphic_ctype",       # django-polymorphic internal field
    "polymorphic_ctype_id",    # django-polymorphic FK
]
```

### 4.2 Pattern-Based Exclusions

From [FieldInspector.EXCLUDE_PATTERNS](../../fairdm/utils/inspection.py#L35-L39):

```python
EXCLUDE_PATTERNS = [
    "_ptr",        # Polymorphic pointer fields (e.g., sample_ptr)
    "_ptr_id",     # Polymorphic pointer FK IDs
    "password",    # Security sensitive fields
]
```

### 4.3 Attribute-Based Exclusions

```python
# Auto-generated timestamp fields
field.auto_now = True          # modified, updated, last_modified
field.auto_now_add = True      # created, added

# Non-editable fields (except relations which may be intentionally read-only)
field.editable = False and not isinstance(field, (ForeignKey, OneToOneField, ManyToManyField))
```

### 4.4 Spec Requirements

From [FR-003](../../specs/002-fairdm-registry/spec.md#L86):

> When `fields` is not specified in the configuration, the registry MUST use a default field list that includes all user-defined model fields while excluding auto-generated fields (`id`, `created_at`, `updated_at`, `polymorphic_ctype`, and any field with `auto_now=True` or `auto_now_add=True`)

**Common Auto-Generated Field Names**:

- `id` - Primary key
- `created`, `created_at`, `added` - Creation timestamp (auto_now_add)
- `modified`, `updated`, `updated_at`, `last_modified` - Update timestamp (auto_now)
- `polymorphic_ctype`, `polymorphic_ctype_id` - Polymorphic type tracking
- `*_ptr`, `*_ptr_id` - Multi-table inheritance pointers

### 4.5 Component-Specific Exclusions

**Tables**: Exclude long text fields and M2M

```python
# Exclude TextField (too long for table display)
# Exclude ManyToManyField (too complex)
if isinstance(field, models.TextField):
    exclude_from_table = True
if isinstance(field, models.ManyToManyField):
    exclude_from_table = True
```

**Filters**: Exclude file fields and JSON

```python
# Exclude ImageField, FileField, JSONField (not filterable)
if isinstance(field, (models.ImageField, models.FileField, models.JSONField)):
    exclude_from_filters = True
```

**Forms**: Include editable fields only

```python
# Forms already respect field.editable = False
# But may need to exclude:
# - Auto-generated fields (id, timestamps)
# - Complex fields that need custom widgets (JSONField)
```

---

## 5. Special Cases

### 5.1 JSONField

**Characteristics**:

- Stores arbitrary JSON data
- Not suitable for automatic filtering or table display
- Requires custom widget for forms

**Handling**:

```python
if isinstance(field, models.JSONField):
    # Tables: EXCLUDE (can't display meaningfully)
    exclude_from_table = True

    # Filters: EXCLUDE (can't filter on arbitrary JSON)
    exclude_from_filters = True

    # Forms: Include with custom widget
    widgets[field_name] = 'JSONEditorWidget'  # Custom widget needed

    # Serializers: Include (DRF handles JSON automatically)
    include_in_serializer = True

    # Import/Export: EXCLUDE (complex structure)
    exclude_from_resource = True
```

**Example**: `options` field in [BaseModel](../../fairdm/core/abstract.py#L41-L45):

```python
options = models.JSONField(
    verbose_name=_("options"),
    null=True,
    blank=True,
)
```

### 5.2 ImageField / FileField

**Characteristics**:

- Store file paths/URLs, not displayable content
- Need special handling for upload and display

**Handling**:

```python
if isinstance(field, models.ImageField):
    # Tables: Use ImageColumn with thumbnail
    use_image_column = True  # Shows thumbnail

    # Filters: EXCLUDE (can't filter on images)
    exclude_from_filters = True

    # Forms: Use ImageWidget with preview
    widgets[field_name] = 'ImageWidget'

    # Serializers: Use ImageField (returns URL)
    use_image_field = True

    # Import/Export: EXCLUDE (binary data)
    exclude_from_resource = True

if isinstance(field, models.FileField):
    # Tables: Use FileColumn with download link
    use_file_column = True

    # Filters: EXCLUDE
    exclude_from_filters = True

    # Forms: Use FileInput
    widgets[field_name] = 'FileInput'

    # Serializers: Use FileField (returns URL)
    use_file_field = True

    # Import/Export: EXCLUDE
    exclude_from_resource = True
```

**Example**: `image` field in [BaseModel](../../fairdm/core/abstract.py#L23-L28):

```python
image = ThumbnailerImageField(
    verbose_name=_("image"),
    blank=True,
    null=True,
    upload_to=default_image_path,
)
```

### 5.3 Polymorphic Fields

**Characteristics**:

- django-polymorphic adds internal fields for type tracking
- These fields should never be exposed to users

**Handling**:

```python
# Always exclude polymorphic internal fields
ALWAYS_EXCLUDE = [
    "polymorphic_ctype",
    "polymorphic_ctype_id",
]

EXCLUDE_PATTERNS = [
    "_ptr",      # sample_ptr, measurement_ptr
    "_ptr_id",   # sample_ptr_id
]

# Example from Sample model
# Automatically has: polymorphic_ctype, polymorphic_ctype_id
# Multi-table inheritance adds: sample_ptr, sample_ptr_id
```

**Validation** (from [FR-016](../../specs/002-fairdm-registry/spec.md#L99)):
> The registry MUST handle polymorphic querysets correctly by detecting polymorphic models using `Model.__subclasses__()` and providing introspection methods that correctly categorize Sample vs Measurement subclasses

### 5.4 Translatable Fields (django-parler)

**Note**: FairDM does not currently use django-parler (no translatable fields found in codebase grep).

**If implemented in future**:

```python
# django-parler uses a separate translation table
# Example: name_en, name_de, name_fr

# Strategy 1: Use current language field only
fields = ['name']  # Uses current language (name_en or name_de)

# Strategy 2: Explicit language fields
fields = ['name_en', 'name_de', 'name_fr']  # Show all translations

# Forms: parler provides TranslatableModelForm
# Use TranslatableModelForm instead of ModelForm

# Tables: Show current language by default
# Use accessor for specific language: Accessor('translations__name')

# Filters: Filter on current language field
# django-parler handles this automatically
```

### 5.5 ManyToManyField

**Characteristics**:

- Represents multiple related objects
- Complex to display in tables
- Works in forms and filters

**Handling**:

```python
if isinstance(field, models.ManyToManyField):
    # Tables: EXCLUDE (too complex, use count column if needed)
    exclude_from_table = True
    # Alternative: Add custom column showing count
    # table_class.keywords_count = Column(accessor='keywords.count')

    # Filters: Include with ModelMultipleChoiceFilter
    use_model_multiple_choice_filter = True

    # Forms: Include with Select2MultipleWidget
    widgets[field_name] = 'Select2MultipleWidget'

    # Serializers: Use nested serializer or PrimaryKeyRelatedField
    use_nested_or_pk_field = True

    # Import/Export: Use natural keys
    use_natural_foreign_keys = True
```

**Example**: `keywords` field in [BaseModel](../../fairdm/core/abstract.py#L31-L36):

```python
keywords = models.ManyToManyField(
    "research_vocabs.Concept",
    verbose_name=_("keywords"),
    help_text=_("Controlled keywords for enhanced discoverability"),
    blank=True,
)
```

### 5.6 Choice Fields

**Characteristics**:

- Field with predefined choices
- Use different widgets based on number of choices

**Handling**:

```python
if hasattr(field, "choices") and field.choices:
    choice_count = len(field.choices)

    # Tables: Show choice display value
    # django-tables2 handles this automatically

    # Filters: Use MultipleChoiceFilter (allow multiple selections)
    use_multiple_choice_filter = True

    # Forms: Widget depends on choice count
    if choice_count <= 5:
        widgets[field_name] = 'RadioSelect'  # Radio buttons for few options
    else:
        widgets[field_name] = 'Select'  # Dropdown for many options

    # Serializers: Use ChoiceField
    use_choice_field = True
```

---

## 6. Field Resolution Algorithm

### 6.1 Algorithm Pseudocode

```python
def resolve_fields_for_component(
    model: type[models.Model],
    component_type: str,  # 'table', 'form', 'filter', 'serializer', 'resource', 'admin'
    config: ComponentConfig,
    parent_fields: list[str] | None
) -> list[str]:
    """
    Resolve field list for a specific component type.

    Returns: Final list of field names to use for component generation
    """
    inspector = FieldInspector(model)

    # STAGE 1: Get initial field list
    if config.fields is not None:
        # Component-specific fields specified
        if config.fields == "__all__":
            fields = inspector.get_all_field_names()
        else:
            fields = flatten_field_list(config.fields)
    elif parent_fields is not None:
        # Use parent config fields
        fields = flatten_field_list(parent_fields)
    else:
        # Use smart defaults based on component type
        if component_type == 'table':
            fields = inspector.get_default_list_fields()
        elif component_type == 'filter':
            fields = inspector.get_default_filter_fields()
        elif component_type == 'form':
            fields = inspector.get_safe_fields()
        elif component_type == 'serializer':
            fields = inspector.get_safe_fields()
        elif component_type == 'resource':
            fields = inspector.get_safe_fields()
        else:
            fields = inspector.get_safe_fields()

    # STAGE 2: Apply exclusions
    if config.exclude:
        fields = [f for f in fields if f not in config.exclude]

    # STAGE 3: Filter by component capabilities
    fields = filter_fields_for_component(fields, component_type, model, inspector)

    # STAGE 4: Validate field names (check existence, validate __ paths)
    validated_fields = []
    for field_name in fields:
        try:
            if '__' in field_name:
                validate_relationship_path(model, field_name)
            else:
                model._meta.get_field(field_name)
            validated_fields.append(field_name)
        except FieldDoesNotExist as e:
            # Log warning or raise error based on strict mode
            if config.strict_validation:
                raise ConfigurationError(f"Invalid field: {field_name}") from e
            else:
                logger.warning(f"Skipping invalid field: {field_name}")

    return validated_fields


def flatten_field_list(fields: list | tuple) -> list[str]:
    """Flatten nested tuples/lists from fieldsets format."""
    flattened = []
    for item in fields:
        if isinstance(item, (list, tuple)):
            flattened.extend(flatten_field_list(item))
        else:
            flattened.append(item)
    return flattened


def filter_fields_for_component(
    fields: list[str],
    component_type: str,
    model: type[models.Model],
    inspector: FieldInspector
) -> list[str]:
    """Filter fields based on component-specific constraints."""
    filtered = []

    for field_name in fields:
        # Handle related field paths
        if '__' in field_name:
            if component_type == 'form':
                # Forms don't support related fields
                continue
            elif component_type == 'serializer':
                # Serializers prefer nested serializers over __ paths
                continue
            # Tables, filters, resources support __ paths
            filtered.append(field_name)
            continue

        # Get field type
        field = inspector.get_field(field_name)
        if field is None:
            continue

        # Apply component-specific exclusions
        if component_type == 'table':
            # Exclude TextField (too long) and M2M (too complex)
            if isinstance(field, (models.TextField, models.ManyToManyField)):
                continue

        elif component_type == 'filter':
            # Exclude file fields and JSON (not filterable)
            if isinstance(field, (models.ImageField, models.FileField, models.JSONField)):
                continue

        elif component_type == 'form':
            # Forms respect field.editable
            if not field.editable:
                continue

        filtered.append(field_name)

    return filtered


def generate_field_type_mapping(
    fields: list[str],
    model: type[models.Model],
    component_type: str
) -> dict[str, Any]:
    """
    Generate type-specific configuration for each field.

    Returns: Dictionary mapping field names to component-specific configs
    """
    inspector = FieldInspector(model)
    mapping = {}

    for field_name in fields:
        if '__' in field_name:
            # Related field - get final field type
            final_field = resolve_field_path(model, field_name)
        else:
            final_field = inspector.get_field(field_name)

        if component_type == 'filter':
            mapping[field_name] = {
                'filter_class': inspector.suggest_filter_type(final_field),
                'lookup_expr': get_lookup_expr(final_field),
            }

        elif component_type == 'form':
            mapping[field_name] = {
                'widget': inspector.suggest_widget(final_field),
            }

        elif component_type == 'table':
            mapping[field_name] = {
                'column_class': get_column_class(final_field),
                'accessor': field_name if '__' not in field_name else Accessor(field_name),
            }

    return mapping
```

### 6.2 Implementation in Factories

**Current Pattern** (from [factories.py](../../fairdm/registry/factories.py)):

```python
class FilterFactory(ComponentFactory):
    def get_fields(self) -> list[str]:
        """Stage 1: Get initial field list."""
        if self.config.fields is not None:
            fields = self.config.fields
        elif self.parent_fields:
            fields = self.parent_fields
        else:
            fields = self.inspector.get_default_filter_fields()

        # Stage 2: Validate fields exist in model
        model_field_names = {f.name for f in self.model._meta.get_fields()}
        fields = [f for f in fields if f in model_field_names]

        # Stage 3: Apply exclusions
        return self.apply_exclusions(fields)

    def get_filter_overrides(self) -> dict[str, str]:
        """Stage 4: Generate type-specific filter classes."""
        overrides = {}

        # User-provided overrides take precedence
        if self.config.filter_overrides:
            overrides.update(self.config.filter_overrides)

        fields = self.get_fields()

        for field_name in fields:
            if field_name in overrides:
                continue  # User override

            # Check configuration hints
            if self.config.exact_fields and field_name in self.config.exact_fields:
                overrides[field_name] = "exact"
            elif self.config.search_fields and field_name in self.config.search_fields:
                overrides[field_name] = "CharFilter"  # icontains
            else:
                # Use smart detection
                suggested = self.inspector.suggest_filter_type(field_name)
                if suggested:
                    overrides[field_name] = suggested

        return overrides
```

---

## 7. CharField Filter Handling

### 7.1 Question: icontains vs exact?

**Decision**: Use `icontains` by default for CharField filters

**Rationale**:

1. **User Experience**: Case-insensitive partial matching is more user-friendly
2. **Search Intent**: Most text searches expect substring matching
3. **Django Convention**: QuerySet filters default to `icontains` for text search
4. **Real-World Usage**: [LiteratureFilterset](../../fairdm/utils/filters.py#L7-L12) uses icontains:

   ```python
   title = df.CharFilter(label=_("Title"), lookup_expr="icontains")
   author = df.CharFilter(field_name="item__author", lookup_expr="icontains")
   ```

**Configuration Override**:

```python
# User can override to exact match via FiltersConfig
filters = FiltersConfig(
    exact_fields=['status', 'code'],  # These use exact match
    search_fields=['name', 'description'],  # These use icontains (explicit)
)
```

### 7.2 Implementation

From [FilterFactory.get_filter_overrides()](../../fairdm/registry/factories.py#L397-L403):

```python
# Check if field is in search_fields list
if self.config.search_fields and field_name in self.config.search_fields:
    overrides[field_name] = "CharFilter"  # icontains
    continue

# Default for CharField
suggested_filter = self.inspector.suggest_filter_type(field_name)
if suggested_filter:
    overrides[field_name] = suggested_filter  # Returns "CharFilter" for CharField
```

From [FieldInspector.suggest_filter_type()](../../fairdm/utils/inspection.py#L352-L354):

```python
# Text fields
if isinstance(field, (models.CharField, models.TextField)):
    return "CharFilter"  # Will use icontains
```

**Filter Creation**:

```python
# When generating FilterSet, need to apply lookup_expr
from django_filters import CharFilter

# For CharField, create filter with icontains
filters[field_name] = CharFilter(
    field_name=field_name,
    lookup_expr='icontains',
    label=field.verbose_name,
)
```

---

## 8. Alternatives Considered

### 8.1 Simple Passthrough (Rejected)

**Approach**: Just pass `fields` directly to each factory without type mapping

**Pros**:

- Simple implementation
- No magic behavior
- Explicit configuration required

**Cons**:

- ❌ Violates Principle III (Configuration Over Custom Plumbing)
- ❌ Requires users to specify widget types, filter types manually
- ❌ No smart defaults - every field needs configuration
- ❌ Breaks for related fields (__ paths)
- ❌ User has to understand django-tables2, django-filter, crispy-forms

**Example**:

```python
# User would have to specify everything
filters = FiltersConfig(
    fields=['name', 'created', 'status'],
    filter_overrides={
        'name': CharFilter(lookup_expr='icontains'),
        'created': DateFromToRangeFilter(),
        'status': MultipleChoiceFilter(choices=STATUS_CHOICES),
    }
)
```

**Why Rejected**: This approach eliminates the primary value proposition of the registry - auto-generation with smart defaults.

### 8.2 Intelligent Type Mapping (Selected)

**Approach**: Inspect field types and generate appropriate component configuration

**Pros**:

- ✅ Follows Principle III (Configuration Over Custom Plumbing)
- ✅ Users specify intent (fields list), registry handles implementation
- ✅ Sensible defaults for 90% of cases
- ✅ Override mechanism for custom behavior
- ✅ Handles related fields automatically

**Example**:

```python
# User specifies intent
fields = ['name', 'created', 'status', 'project__owner__name']

# Registry generates appropriate components:
# - Table: Column for each field, Accessor for related
# - Filter: CharFilter(icontains) for name, DateRangeFilter for created, etc.
# - Form: TextInput for name, DateInput for created, Select for status
```

**Implementation**: Current approach in [FieldInspector](../../fairdm/utils/inspection.py) and [ComponentFactory](../../fairdm/registry/factories.py)

### 8.3 Hybrid Approach with Hints (Future Enhancement)

**Approach**: Intelligent defaults + configuration hints

**Example**:

```python
filters = FiltersConfig(
    fields=['name', 'created', 'status'],
    # Hints for customization
    search_fields=['name'],  # Use icontains
    exact_fields=['status'],  # Use exact match
    range_fields=['created'],  # Use range filter
)
```

**Status**: Partially implemented via `exact_fields`, `range_fields`, `search_fields` in [FiltersConfig](../../fairdm/registry/components.py#L56-L76)

---

## 9. Implementation Notes

### 9.1 Factory Pattern Implications

**Current Architecture**:

```
ModelConfiguration
    ├── fields (parent field list)
    ├── FormConfig (component-specific config)
    │   └── fields (optional override)
    ├── TableConfig
    │   └── fields (optional override)
    └── FiltersConfig
        └── fields (optional override)

Each factory gets:
- model class
- component config
- parent_fields (fallback)
```

**Field Resolution Chain**:

1. Component-specific fields (`config.fields`)
2. Parent fields (`parent_fields`)
3. Smart defaults (`inspector.get_default_X_fields()`)

**Implication**: Factories need access to:

- Model metadata (via `model._meta`)
- Field inspector (via `FieldInspector(model)`)
- Parent configuration (via `parent_fields` parameter)
- Component-specific config (via `config` parameter)

### 9.2 Testing Strategy

**Unit Tests** (for each component):

```python
def test_field_resolution_component_specific():
    """Test component fields override parent fields."""
    config = TableConfig(fields=['name', 'created'])
    factory = TableFactory(model, config, parent_fields=['name', 'status'])
    assert factory.get_fields() == ['name', 'created']

def test_field_resolution_parent_fallback():
    """Test falls back to parent fields."""
    config = TableConfig()  # No fields specified
    factory = TableFactory(model, config, parent_fields=['name', 'status'])
    assert factory.get_fields() == ['name', 'status']

def test_field_resolution_smart_defaults():
    """Test uses smart defaults when no fields specified."""
    config = TableConfig()
    factory = TableFactory(model, config, parent_fields=None)
    fields = factory.get_fields()
    assert 'name' in fields
    assert 'created' in fields
    assert 'modified' in fields

def test_related_field_validation():
    """Test validates relationship paths."""
    config = TableConfig(fields=['name', 'project__title'])
    factory = TableFactory(SampleModel, config)
    fields = factory.get_fields()
    assert 'project__title' in fields

def test_related_field_invalid():
    """Test raises error for invalid paths."""
    config = TableConfig(fields=['invalid__path__field'])
    factory = TableFactory(SampleModel, config)
    with pytest.raises(FieldDoesNotExist):
        factory.get_fields()
```

**Integration Tests** (component generation):

```python
def test_filterset_char_field_uses_icontains():
    """Test CharField generates CharFilter with icontains."""
    config = ModelConfiguration(
        model=Sample,
        fields=['name', 'description']
    )
    filterset = config.get_filterset_class()
    assert 'name' in filterset.base_filters
    assert filterset.base_filters['name'].lookup_expr == 'icontains'

def test_table_excludes_m2m_fields():
    """Test ManyToManyField excluded from default table."""
    config = ModelConfiguration(model=Sample)
    table = config.get_table_class()
    assert 'keywords' not in table._meta.fields

def test_form_includes_safe_fields_only():
    """Test form excludes auto-generated fields."""
    config = ModelConfiguration(model=Sample)
    form = config.get_form_class()
    assert 'id' not in form._meta.fields
    assert 'created' not in form._meta.fields
    assert 'name' in form._meta.fields
```

### 9.3 Code Examples

**Complete Field Resolution Function**:

```python
# fairdm/registry/resolution.py

from typing import Any
from django.db import models
from django.core.exceptions import FieldDoesNotExist

from fairdm.utils.inspection import FieldInspector


class FieldResolver:
    """Resolves fields from parent config to component-specific needs."""

    # Field type mapping for each component type
    FILTER_TYPE_MAP = {
        models.CharField: ('CharFilter', {'lookup_expr': 'icontains'}),
        models.TextField: ('CharFilter', {'lookup_expr': 'icontains'}),
        models.IntegerField: ('RangeFilter', {}),
        models.DecimalField: ('RangeFilter', {}),
        models.FloatField: ('RangeFilter', {}),
        models.BooleanField: ('BooleanFilter', {}),
        models.DateField: ('DateFromToRangeFilter', {}),
        models.DateTimeField: ('DateFromToRangeFilter', {}),
        models.ForeignKey: ('ModelChoiceFilter', {}),
        models.ManyToManyField: ('ModelMultipleChoiceFilter', {}),
    }

    WIDGET_MAP = {
        models.CharField: 'TextInput',
        models.TextField: 'Textarea',
        models.IntegerField: 'NumberInput',
        models.DateField: 'DateInput',
        models.DateTimeField: 'SplitDateTimeWidget',
        models.TimeField: 'TimeInput',
        models.BooleanField: 'CheckboxInput',
        models.ForeignKey: 'Select2Widget',
        models.ManyToManyField: 'Select2MultipleWidget',
        models.ImageField: 'ImageWidget',
        models.FileField: 'FileInput',
        models.URLField: 'URLInput',
        models.EmailField: 'EmailInput',
    }

    def __init__(self, model: type[models.Model]):
        self.model = model
        self.inspector = FieldInspector(model)

    def resolve_fields(
        self,
        component_type: str,
        config_fields: list[str] | str | None,
        parent_fields: list[str] | None
    ) -> list[str]:
        """Resolve field list with fallback chain."""
        # Stage 1: Get initial field list
        if config_fields is not None:
            if config_fields == "__all__":
                fields = self.inspector.get_all_field_names()
            else:
                fields = self._flatten_fields(config_fields)
        elif parent_fields:
            fields = self._flatten_fields(parent_fields)
        else:
            fields = self._get_smart_defaults(component_type)

        # Stage 2: Filter by component capabilities
        fields = self._filter_for_component(fields, component_type)

        return fields

    def _flatten_fields(self, fields: list | tuple | str) -> list[str]:
        """Flatten nested field lists from fieldsets."""
        if isinstance(fields, str):
            return [fields]

        flattened = []
        for item in fields:
            if isinstance(item, (list, tuple)):
                flattened.extend(self._flatten_fields(item))
            else:
                flattened.append(item)
        return flattened

    def _get_smart_defaults(self, component_type: str) -> list[str]:
        """Get component-specific smart defaults."""
        if component_type == 'table':
            return self.inspector.get_default_list_fields()
        elif component_type == 'filter':
            return self.inspector.get_default_filter_fields()
        else:
            return self.inspector.get_safe_fields()

    def _filter_for_component(
        self,
        fields: list[str],
        component_type: str
    ) -> list[str]:
        """Apply component-specific filtering."""
        filtered = []

        for field_name in fields:
            # Forms don't support related fields
            if component_type == 'form' and '__' in field_name:
                continue

            # Get field (or final field for related paths)
            if '__' in field_name:
                try:
                    field = self._resolve_field_path(field_name)
                except FieldDoesNotExist:
                    continue
            else:
                field = self.inspector.get_field(field_name)
                if field is None:
                    continue

            # Component-specific exclusions
            if component_type == 'table':
                if isinstance(field, (models.TextField, models.ManyToManyField)):
                    continue
            elif component_type == 'filter':
                if isinstance(field, (models.ImageField, models.FileField, models.JSONField)):
                    continue

            filtered.append(field_name)

        return filtered

    def _resolve_field_path(self, field_path: str) -> models.Field:
        """Resolve a relationship path to final field."""
        parts = field_path.split('__')
        current_model = self.model

        # Traverse relationships
        for part in parts[:-1]:
            field = current_model._meta.get_field(part)
            if not field.is_relation:
                raise FieldDoesNotExist(
                    f"'{part}' in '{field_path}' is not a relation"
                )
            current_model = field.related_model

        # Get final field
        return current_model._meta.get_field(parts[-1])

    def get_filter_config(self, field_name: str) -> tuple[str, dict[str, Any]]:
        """Get filter class and config for field."""
        field = self._get_field_for_name(field_name)

        for field_class, (filter_type, config) in self.FILTER_TYPE_MAP.items():
            if isinstance(field, field_class):
                return filter_type, config

        return 'CharFilter', {'lookup_expr': 'icontains'}

    def get_widget_name(self, field_name: str) -> str | None:
        """Get widget name for field."""
        field = self._get_field_for_name(field_name)

        # Handle choice fields specially
        if hasattr(field, 'choices') and field.choices:
            return 'RadioSelect' if len(field.choices) <= 5 else 'Select'

        for field_class, widget_name in self.WIDGET_MAP.items():
            if isinstance(field, field_class):
                return widget_name

        return None

    def _get_field_for_name(self, field_name: str) -> models.Field:
        """Get field object (handles related paths)."""
        if '__' in field_name:
            return self._resolve_field_path(field_name)
        return self.inspector.get_field(field_name)
```

---

## 10. Decision Summary

### 10.1 Field Resolution Algorithm

**Adopted Approach**:

```
1. Field List Resolution (3-level fallback):
   - Component-specific fields (config.Table.fields)
   - Parent fields (config.fields)
   - Smart defaults (inspector.get_default_X_fields())

2. Field Type Mapping:
   - Introspect Django field type
   - Map to appropriate component class (Column, Filter, Widget)
   - Apply component-specific defaults (icontains for CharField)

3. Related Field Handling:
   - Validate relationship paths (__ notation)
   - Support in Tables, Filters, Import/Export
   - Exclude from Forms, convert to nested serializers in DRF

4. Default Exclusions:
   - Always: id, polymorphic fields
   - Patterns: _ptr, password
   - Attributes: auto_now, auto_now_add, editable=False

5. Special Cases:
   - JSONField: Exclude from tables/filters
   - ImageField/FileField: Exclude from filters, special widgets
   - ManyToManyField: Exclude from tables
```

### 10.2 CharField Filter Handling

**Decision**: Use `icontains` lookup by default for CharField filters

**Rationale**:

- More user-friendly (case-insensitive partial matching)
- Aligns with search intent (users expect substring matching)
- Follows Django QuerySet conventions
- Consistent with existing codebase patterns

**Override Mechanism**:

```python
filters = FiltersConfig(
    exact_fields=['status', 'code'],  # Override to exact match
    search_fields=['name'],  # Explicit icontains (default anyway)
)
```

### 10.3 Related Field Lookups

**Decision**: Support `__` notation in components that handle it natively

**Component Support Matrix**:

| Component | Support | Implementation |
|-----------|---------|----------------|
| Tables | ✅ Full | Accessor class |
| Filters | ✅ Full | field_name parameter |
| Forms | ❌ None | Exclude related paths |
| Serializers | ⚠️ Nested | Use nested serializers |
| Import/Export | ✅ Full | Native support |

### 10.4 Default Exclusions

**Adopted List**:

```python
ALWAYS_EXCLUDE = [
    "id",                    # Auto-generated primary key
    "polymorphic_ctype",     # django-polymorphic internal
    "polymorphic_ctype_id",  # django-polymorphic FK
]

EXCLUDE_PATTERNS = [
    "_ptr",      # Multi-table inheritance pointers
    "_ptr_id",   # Pointer FK IDs
    "password",  # Security sensitive
]

EXCLUDE_BY_ATTRIBUTE = [
    # auto_now = True
    # auto_now_add = True
    # editable = False (except ForeignKey)
]
```

### 10.5 Special Field Handling

**Matrix**:

| Field Type | Table | Filter | Form | Notes |
|------------|-------|--------|------|-------|
| JSONField | ❌ Exclude | ❌ Exclude | ⚠️ Custom widget | Too complex for auto-display |
| ImageField | ✅ Thumbnail | ❌ Exclude | ✅ ImageWidget | Special column/widget |
| FileField | ✅ Link | ❌ Exclude | ✅ FileInput | Download link |
| TextField | ❌ Exclude | ✅ icontains | ✅ Textarea | Too long for table |
| ManyToManyField | ❌ Exclude | ✅ Multiple | ✅ Select2Multiple | Too complex for table |
| ForeignKey | ✅ **str** | ✅ Dropdown | ✅ Select2 | Support __ paths |

---

## 11. Next Steps

### 11.1 Implementation Tasks

1. **Refactor FieldInspector** ([inspection.py](../../fairdm/utils/inspection.py)):
   - ✅ Already has `suggest_filter_type()`
   - ✅ Already has `suggest_widget()`
   - ⚠️ Add `validate_relationship_path()` method
   - ⚠️ Add component-specific filtering methods

2. **Update FilterFactory** ([factories.py](../../fairdm/registry/factories.py)):
   - ✅ Already has `get_filter_overrides()`
   - ⚠️ Apply lookup_expr to generated filters
   - ⚠️ Support field_name parameter for related fields

3. **Update TableFactory**:
   - ✅ Already uses `table_factory()` which handles Accessor
   - ⚠️ Add explicit Accessor for related fields
   - ⚠️ Add special columns for ImageField

4. **Update FormFactory**:
   - ✅ Already has widget suggestion
   - ⚠️ Exclude related fields (__ notation)
   - ⚠️ Apply widget mapping

5. **Add Validation**:
   - ⚠️ Implement relationship path validation
   - ⚠️ Add field existence checks
   - ⚠️ Provide helpful error messages with suggestions

### 11.2 Documentation Tasks

1. **API Documentation**:
   - Document field resolution algorithm
   - Document type mapping tables
   - Document override mechanisms

2. **User Guide**:
   - Show examples of field lists
   - Explain related field notation
   - Show override patterns

3. **Migration Guide**:
   - If changing existing behavior
   - Document breaking changes
   - Provide migration examples

### 11.3 Testing Tasks

1. **Unit Tests**:
   - Field resolution chain
   - Type mapping functions
   - Related field validation
   - Default exclusions

2. **Integration Tests**:
   - Generated FilterSets have correct filters
   - Generated Tables have correct columns
   - Generated Forms have correct widgets
   - Related fields work in components

3. **Demo App**:
   - Add examples showing all field types
   - Demonstrate related field usage
   - Show override mechanisms

---

## References

### Internal Documents

- [spec.md](./spec.md) - Feature specification (FR-003, FR-006, FR-012)
- [research-R3-validation-strategy.md](./research-R3-validation-strategy.md) - Field validation
- [plan.md](./plan.md) - Implementation plan

### Source Code

- [fairdm/registry/factories.py](../../fairdm/registry/factories.py) - Component factories
- [fairdm/utils/inspection.py](../../fairdm/utils/inspection.py) - FieldInspector
- [fairdm/registry/components.py](../../fairdm/registry/components.py) - Config classes
- [fairdm_demo/config.py](../../fairdm_demo/config.py) - Real-world examples

### Django Documentation

- [Field types](https://docs.djangoproject.com/en/5.1/ref/models/fields/)
- [Field lookups](https://docs.djangoproject.com/en/5.1/ref/models/querysets/#field-lookups)
- [Related object lookups](https://docs.djangoproject.com/en/5.1/topics/db/queries/#lookups-that-span-relationships)

### Third-Party Documentation

- [django-tables2 Column reference](https://django-tables2.readthedocs.io/en/latest/pages/column-reference.html)
- [django-filter Field reference](https://django-filter.readthedocs.io/en/stable/ref/filters.html)
- [django-select2 Widgets](https://django-select2.readthedocs.io/en/latest/)

---

**Status**: ✅ Research Complete
**Next Phase**: Design (Phase 1) - Create contracts and API specification
**Implementation Target**: Phase 2 - red-green-refactor with TDD
