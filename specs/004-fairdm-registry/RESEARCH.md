# Research: FairDM Registry System

**Feature**: 004-fairdm-registry
**Date**: 2026-01-08
**Phase**: 0 - Technology Research & Design Decisions

## Executive Summary

This document consolidates research findings for implementing the FairDM registry system. The registry enables declarative model registration with automatic generation of Forms, Tables, FilterSets, Serializers, and Import/Export resources.

### Key Decisions

| Area | Decision | Rationale |
|------|----------|-----------|
| Table Generation | Use `type()` with explicit column mapping | Provides full control over column types, more maintainable than metaclass magic |
| Filter Generation | Use `filterset_factory()` with custom base class | Leverages built-in django-filter factory while allowing override configuration |
| Form Generation | Use ModelForm with FormHelper(self) | django-crispy-forms: Auto-generates layouts, HTMX-compatible, server-side rendering. django-formset rejected due to web components complexity and philosophy mismatch. |
| Resource Generation | Use `modelresource_factory()` with subclass | Standard pattern, supports natural keys and validation |
| Registry Pattern | Module-level singleton with NamedTuple storage | Matches Django admin.site pattern, thread-safe via GIL |
| Registration Timing | Eager generation at AppConfig.ready() | Early error detection, zero runtime overhead |
| Registration Location | Auto-discovery via `registration.py` files | Clean separation, conventional Django pattern |
| Polymorphic Handling | Use PolymorphicQuerySet.instance_of() | Correct subclass downcasting, 1 query per type |
| Field Validation | Validate at registration using _meta.get_field() | Fail-fast principle, clear error messages |

---

## 1. django-tables2 Research

### Decision: Dynamic Table Generation using `type()`

**Rationale**: Provides full control over column types and configuration while maintaining clean, maintainable code. More explicit than metaclass magic.

**Key Findings**:

- Tables can be dynamically created using Python's `type()` function
- Column type mapping from Django fields is straightforward
- Bootstrap 5 integration via `template_name = 'django_tables2/bootstrap5.html'`
- Related fields supported via `Accessor` utility class
- Performance optimizations: `select_related()`, `prefetch_related()`, `LazyPaginator`

[Detailed code examples and implementation patterns available in original research]

**Alternative Considered**: Metaclass approach - Rejected as too complex and harder to debug.

---

## 2. django-filter Research

### Decision: Use `filterset_factory()` with Custom Base Class

**Rationale**: Leverages django-filter's built-in factory while allowing customization through inheritance and `filter_overrides`.

**Key Findings**:

- FilterSets can be created using `filterset_factory()` or `type()`
- Field type to filter type mapping is well-defined
- Relationship filters (`project__title`) work natively
- Integration with django-crispy-forms for Bootstrap 5 styling
- HTMX integration requires minimal template changes

[Detailed code examples and implementation patterns available in original research]

**Alternative Considered**: Manual filter creation - Rejected as too verbose and error-prone.

---

## 3. Form Rendering: django-crispy-forms vs django-formset

### Decision: django-crispy-forms with FormHelper(self)

**Rationale**: django-crispy-forms provides simpler, template-focused rendering that aligns better with FairDM's server-side philosophy. While django-formset offers advanced features (web components, client-side validation, nested formsets), these add complexity and JavaScript dependencies that are unnecessary for auto-generated CRUD forms in the registry system.

### Comparison Analysis

| Criterion | django-crispy-forms | django-formset | Winner |
| --------- | ------------------- | -------------- | ------ |
| **Bootstrap 5 Support** | ✅ Via crispy-bootstrap5 | ✅ Via template renderer | Tie |
| **Error Display** | ✅ Inline field errors + banner | ✅ Inline + custom attributes | Tie |
| **Dynamic Generation** | ✅ FormHelper(self) auto-layout | ✅ FormRenderer with config | Tie |
| **HTMX Integration** | ✅ Simple - no special handling | ⚠️ Web components may conflict | **crispy-forms** |
| **Client-Side Validation** | ❌ Server-side only | ✅ Built-in JS validation | formset (but not needed) |
| **Nested Forms/Formsets** | ⚠️ Requires django-formtools | ✅ Built-in FormCollection | **formset** |
| **Complexity** | ✅ Minimal - template tags only | ⚠️ Web components + Alpine.js | **crispy-forms** |
| **Maturity** | ✅ 106 snippets, High rep | ✅ 405 snippets, High rep | Tie |
| **Philosophy Alignment** | ✅ Server-rendered forms | ⚠️ Client-side web components | **crispy-forms** |
| **Learning Curve** | ✅ Simple - tags + layouts | ⚠️ Requires web component knowledge | **crispy-forms** |
| **Dependencies** | ✅ Already in FairDM | ❌ New dependency | **crispy-forms** |

### django-crispy-forms Details

**Strengths**:

- ✅ **CONFIRMED**: Default error display is field errors inline, non-field errors in banner
- FormHelper(self) auto-generates layouts from form fields
- Bootstrap 5 requires `crispy-bootstrap5` package (already in FairDM)
- Widget selection is handled by Django automatically
- Exclude auto-generated fields via `Meta.exclude`
- Simple template-based rendering: `{% crispy form %}`
- No JavaScript required - pure server-side rendering

**Error Display Behavior** (Confirmed from Documentation):

- Field-specific errors: Rendered inline below each field
- Non-field errors (form-level): Rendered in alert banner at top
- No configuration needed - this is the default behavior

**Usage Pattern**:

```python
class SampleForm(ModelForm):
    class Meta:
        model = Sample
        fields = ['title', 'description', 'date']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_method = 'post'
```

**Template**:

```django
{% load crispy_forms_tags %}
{% crispy form %}
```

### django-formset Details

**Strengths**:

- Built-in client-side validation with `formset:validated` events
- Native support for nested forms via `FormCollection`
- Web components architecture (`<django-formset>` custom element)
- Advanced widgets (file uploads, autocomplete, rich text)
- Dynamic formset management (add/remove siblings)

**Weaknesses for FairDM Registry**:

- **Web components**: Adds JavaScript complexity unnecessary for simple CRUD forms
- **Alpine.js-style attributes**: Requires learning custom `df-click` syntax
- **HTMX conflicts**: Web component event model may interfere with HTMX's model
- **Overkill**: Client-side validation and nested collections not needed for registry forms
- **Philosophy mismatch**: FairDM emphasizes server-side rendering with minimal JS

**Usage Pattern** (for reference):

```python
from formset.collection import FormCollection
from formset.renderers.bootstrap import FormRenderer

class SampleForm(ModelForm):
    default_renderer = FormRenderer(field_css_classes='mb-3')
    class Meta:
        model = Sample
        fields = ['title', 'description', 'date']

class SampleCollection(FormCollection):
    sample = SampleForm()
```

**Template**:

```django
{% load render_form from formsetify %}
<django-formset endpoint="{{ request.path }}">
    {% render_form form "bootstrap" %}
</django-formset>
```

### Decision Justification

**For FairDM Registry System**: django-crispy-forms is the better choice because:

1. **Simplicity**: Registry-generated forms are straightforward CRUD operations. Client-side validation, web components, and dynamic formset management are unnecessary complexity.

2. **Server-side philosophy**: FairDM uses HTMX for dynamic behavior, which works seamlessly with server-rendered forms. django-formset's web component model may conflict with HTMX's approach.

3. **Zero new dependencies**: django-crispy-forms + crispy-bootstrap5 are already in FairDM. django-formset would add a new dependency with features we don't need.

4. **Proven pattern**: FormHelper(self) auto-layout is simple, well-documented, and widely used in Django projects.

5. **HTMX compatibility**: Template-tag rendering integrates cleanly with HTMX's `hx-post` and partial rendering model.

**When django-formset would be better**:

- Complex multi-step forms requiring client-side state management
- Dynamic nested formsets with add/remove UI
- Rich client-side validation requirements
- Projects already using web components architecture

**For FairDM**: None of these apply to auto-generated registry forms. Keep it simple.

[Detailed code examples and implementation patterns available in original research]

**Alternatives Considered**:

- ❌ django-formset: Too complex for simple CRUD forms, web components mismatch with HTMX
- ❌ Manual layout definition: Too verbose for many models
- ✅ django-crispy-forms with FormHelper(self): Simple, proven, HTMX-compatible

---

## 4. django-import-export Research

### Decision: Use `modelresource_factory()` with Subclass Override

**Rationale**: Standard pattern that provides clean API while allowing customization through subclassing.

**Key Findings**:

- Resources can be created using `modelresource_factory()`
- Natural key support via `use_natural_foreign_keys=True`
- Row-level error validation with detailed reporting
- Export filtered querysets via `filter_export()` or direct queryset passing
- Field mapping for custom column names

[Detailed code examples and implementation patterns available in original research]

**Alternative Considered**: Manual CSV parsing - Rejected as reinventing the wheel.

---

## 5. django-polymorphic Research

### Decision: Use PolymorphicQuerySet with Automatic Downcasting

**Rationale**: django-polymorphic automatically returns correct subclass instances, eliminating manual casting logic.

**Key Findings**:

- Polymorphic querysets automatically return correct subclass instances
- Performance: 1 query per unique subclass type (not per object)
- `instance_of()` and `not_instance_of()` for type filtering
- `Model.__subclasses__()` for discovering registered subclasses
- `non_polymorphic()` optimization when only base fields needed

**Limitation**: `select_related()` cannot traverse polymorphic relationships yet (use `prefetch_related()` instead).

[Detailed code examples and implementation patterns available in original research]

**Alternative Considered**: Manual type field + Django inheritance - Rejected due to manual casting requirements.

---

## 6. Django Field Introspection Research

### Decision: Use `_meta.get_field()` with Validation Logic

**Rationale**: Django's Meta API provides reliable field introspection with clear error messages.

**Key APIs**:

- `_meta.get_fields()` - all fields including relations
- `_meta.fields` - only concrete fields
- `_meta.get_field(name)` - specific field by name
- Field attributes: `auto_created`, `auto_now`, `auto_now_add`, `remote_field`

**Field Validation Strategy**:

1. Check field existence using `_meta.get_field()`
2. Parse relationship paths (`project__title`) by traversing `remote_field.model`
3. Check type compatibility based on usage context (filterable, sortable, etc.)
4. Raise clear validation errors with suggestions for valid fields

**Auto-Generated Field Detection**:
Fields to exclude from forms:

- `AutoField` (id)
- Fields with `auto_created=True`
- Fields with `auto_now` or `auto_now_add`
- `polymorphic_ctype` (django-polymorphic internal field)

[Detailed code examples and implementation patterns available in original research]

**Alternative Considered**: Try/except on operations - Rejected due to unclear error messages.

---

## 7. Django Registry Pattern Research

### Decision: Module-Level Singleton with Auto-Discovery

**Rationale**: Matches Django's admin.site pattern, which is battle-tested and well-understood by Django developers.

**Registry Implementation**:

- Module-level singleton instance
- NamedTuple for immutable entry storage
- Dictionary for model → entry mapping
- Auto-discovery via `registration.py` files imported in `AppConfig.ready()`

**Data Structure**:

```python
RegistryEntry = namedtuple('RegistryEntry', [
    'model',
    'config',
    'table_class',
    'filterset_class',
    'form_class',
    'resource_class',
])
```

**Registration Flow**:

1. AppConfig.ready() imports `registration.py`
2. `registration.py` calls `registry.register(Model, Config)`
3. Registry validates model, generates components, stores entry
4. Views access generated components via registry getters

**Thread Safety**: Python's GIL provides basic thread safety for dictionary operations. Registration only happens during startup (single-threaded), so no explicit locking needed.

**Introspection API**:

- `is_registered(model)` - check registration status
- `get_entry(model)` - full registry entry
- `get_table(model)`, `get_filterset(model)`, etc. - component accessors
- `get_registered_samples()`, `get_registered_measurements()` - type-specific queries
- `get_all_models()` - all registered models
- Iterator support for looping over entries

[Detailed code examples and implementation patterns available in original research]

**Alternatives Considered**:

- ❌ Model decorator: Couples models to registry
- ❌ Lazy generation: Runtime overhead, delayed errors
- ❌ Metaclass magic: Implicit, harder to debug
- ✅ Explicit registration: Clean, discoverable, testable

---

## Component Generation Strategy

### Decision: Eager Generation at Registration Time

**Rationale**:

1. **Early error detection**: Configuration errors surface at startup, not runtime
2. **Zero runtime overhead**: No dynamic class creation per request
3. **Simpler debugging**: Generated classes exist in memory, can be inspected
4. **Matches Django patterns**: Admin.site generates ModelAdmin classes at registration

**Generation Timing**:

- All components generated during `registry.register()` call
- Happens at startup in `AppConfig.ready()`
- Any errors fail application startup with clear messages
- Zero performance cost during request handling

**Performance Target** (from FR-031, NFR-001):

- Component generation: <100ms per model
- Startup with 20 models: <5 seconds total
- Runtime overhead: Zero (no lazy generation)

**Alternatives Considered**:

- ❌ Lazy generation on first use: Delayed error discovery, runtime complexity
- ❌ Generate per request: Unacceptable performance penalty
- ✅ Eager at registration: Fail-fast, simple, performant

---

## Technology Stack Summary

| Technology | Version | Purpose | Status |
|------------|---------|---------|--------|
| django-tables2 | Latest | Table rendering | ✅ Chosen |
| django-filter | Latest | Filtering UI | ✅ Chosen |
| django-crispy-forms | Latest | Form styling | ✅ Chosen |
| crispy-bootstrap5 | Latest | Bootstrap 5 theme | ✅ Chosen |
| django-import-export | Latest | CSV import/export | ✅ Chosen |
| django-polymorphic | Latest | Model inheritance | ✅ Existing |
| Django ORM _meta API | Core | Field introspection | ✅ Core feature |

**No new dependencies required** - all packages are already in FairDM's dependency tree or are Django core APIs.

---

## Implementation Approach Summary

### Registration Flow

```
1. App starts → AppConfig.ready() called
2. Import registration.py → Trigger registry.register() calls
3. For each model:
   a. Validate model inheritance (Sample/Measurement)
   b. Validate field configuration (list_fields, filter_fields, etc.)
   c. Generate Table class (using type())
   d. Generate FilterSet class (using filterset_factory())
   e. Generate Form class (using ModelForm + FormHelper)
   f. Generate Resource class (using modelresource_factory())
   g. Store in registry as NamedTuple entry
4. Registry ready for views to access

Error at any step → Clear error message with context → Application fails to start
```

### View Integration Pattern

```python
# Generic list view using registry
class RegistryListView(FilterView):
    template_name = 'fairdm/registry/list.html'

    def get_filterset_class(self):
        model = self.get_model()
        return registry.get_filterset(model)

    def get_table_class(self):
        model = self.get_model()
        return registry.get_table(model)
```

---

## Open Questions Resolved

| Question | Answer | Source |
|----------|--------|--------|
| How to validate field paths like `project__title`? | Parse path, use `_meta.get_field()` on each part, follow `remote_field.model` | Django _meta API research |
| How to handle polymorphic querysets in tables? | No special handling needed - django-polymorphic auto-downcasts | django-polymorphic documentation |
| Does crispy-forms display errors by default? | YES - field errors inline, non-field errors in banner | django-crispy-forms documentation |
| Can we use natural keys for CSV import? | YES - set `use_natural_foreign_keys=True` in Resource Meta | django-import-export documentation |
| Is module-level singleton thread-safe? | YES - Python's GIL protects dict operations, registration is single-threaded | Django admin.site pattern analysis |
| Should we lazy-load generated components? | NO - eager generation provides early errors, zero runtime cost | Django admin pattern, performance requirements |
| What field types map to which filter types? | Comprehensive mapping documented in section 2 | django-filter documentation |
| How to handle related fields in tables? | Use `django_tables2.utils.Accessor` for nested attribute lookup | django-tables2 documentation |
| How to exclude auto-generated fields? | Check `auto_created`, `auto_now`, `auto_now_add`, `AutoField` type | Django field introspection research |

---

## Next Steps (Phase 1: Design)

Based on this research, Phase 1 will produce:

1. **data-model.md**: Registry data structures, RegistryEntry, Configuration class hierarchy
2. **contracts/**: API contracts for registry introspection (if API module enabled)
3. **quickstart.md**: Developer guide for registering custom Sample/Measurement models

All research findings and design decisions are final and ready for implementation planning.

---

**Research Completed**: 2026-01-08
**Status**: ✅ Ready for Phase 1 (Design & Contracts)
