# Implementation Plan: Plugin System for Model Extensibility

**Branch**: `008-plugin-system` | **Date**: 2026-02-17 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/008-plugin-system/spec.md`

## Summary

Redesign the FairDM plugin system (`fairdm.contrib.plugins`) to provide a clean, declarative API for extending model detail views. The new system replaces the current `PluggableView` orchestrator pattern with a simpler architecture where each `Plugin` is a Django view mixin that owns its own URL generation (`get_urls()` classmethod), template resolution, and permission checking. A `PluginGroup` composition class enables multi-view features (e.g., CRUD interfaces) under a single tab. Categories are removed; tabs appear for any plugin with an inner `Menu` class. The registry aggregates URL patterns and tab data per model. Backward compatibility is explicitly not a requirement.

**Key design decisions** (see [research.md](research.md)):
1. Plugin as mixin paired with Django CBVs (not a standalone base view)
2. `get_urls()` classmethod on Plugin and PluginGroup (user-suggested, mirrors Django admin pattern)
3. Eliminate `PluggableView` orchestrator; registry replaces its responsibilities
4. Flat tab list via `Tab` dataclass replaces three-category `flex_menu` menus
5. Django system checks for startup validation
6. Natural error isolation (each plugin is a separate HTTP request)

## Technical Context

**Language/Version**: Python 3.13, Django 5.x  
**Primary Dependencies**: Django CBVs, django-guardian (object-level perms), django-polymorphic (model inheritance), django-extra-views (InlineFormSetView)  
**Storage**: N/A (no database tables — runtime registration system)  
**Testing**: pytest + pytest-django  
**Target Platform**: Linux/Windows server (Django WSGI/ASGI)  
**Project Type**: Django app within FairDM framework  
**Performance Goals**: ≤20 plugins per model page load under 2 seconds; tab list generation under 10ms  
**Constraints**: Server-side rendering only; no SPA/client-side rendering  
**Scale/Scope**: 4 core models + N user-defined polymorphic models, ~30-50 plugins across a typical portal

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. FAIR-First** | ✅ PASS | Plugin system enables extensible metadata views; does not weaken FAIR characteristics. Plugins can expose FAIR metadata panels. |
| **II. Domain-Driven Modeling** | ✅ PASS | Plugin system extends model views declaratively via registration, not ad-hoc runtime structures. |
| **III. Configuration Over Code** | ✅ PASS | Core design philosophy: decorator-based registration, inner `Menu` class, auto-generated URLs and templates. Developers configure, not plumb. |
| **IV. Opinionated Defaults** | ✅ PASS | Sensible defaults for URL paths, template resolution, tab ordering. Django-based stack (CBVs, guardian, templates). Bootstrap 5 tab rendering. |
| **V. Test-First Quality** | ✅ PASS | Implementation will follow Red→Green→Refactor. System checks provide startup validation. |
| **VI. Documentation Critical** | ✅ PASS | quickstart.md, contracts/, and data-model.md created as part of plan. Public API will be documented with examples. |
| **VII. Living Demo** | ✅ PASS | Demo app will be updated to demonstrate plugin registration, PluginGroups, and template customization. |

### Post-Design Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. FAIR-First** | ✅ PASS | No changes to FAIR characteristics. Plugin system is a view extension mechanism. |
| **II. Domain-Driven** | ✅ PASS | Plugin registration uses explicit `@plugins.register(Model)` decorator — declarative, discoverable. |
| **III. Configuration Over Code** | ✅ PASS | Inner `Menu` class, auto URL generation, hierarchical template resolution. Minimal boilerplate. |
| **IV. Opinionated Defaults** | ✅ PASS | Framework fallback template ensures plugins work without custom templates. Auto-derived names/paths. |
| **V. Test-First** | ✅ PASS | Contracts define testable behavior. System checks provide E001-E007, W001-W002 validation. |
| **VI. Documentation** | ✅ PASS | quickstart.md serves as developer guide. Contracts define API surface. |
| **VII. Living Demo** | ✅ PASS | Existing demo plugins will be migrated to new API in the same PR. |

**No constitution violations.** No entries needed in Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/008-plugin-system/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0: Design decisions and rationale
├── data-model.md        # Phase 1: Entity definitions and relationships
├── quickstart.md        # Phase 1: Developer getting-started guide
├── contracts/           # Phase 1: API contracts
│   ├── README.md
│   ├── registration.md
│   ├── url-generation.md
│   ├── template-resolution.md
│   ├── tab-rendering.md
│   └── permission-checking.md
├── checklists/
│   └── requirements.md  # Quality validation checklist
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
fairdm/contrib/plugins/           # Main plugin system package
├── __init__.py                   # Public API: Plugin, PluginGroup, registry, is_instance_of
├── base.py                       # Plugin mixin class
├── group.py                      # PluginGroup composition class
├── registry.py                   # PluginRegistry singleton + register() method
├── menu.py                       # Tab dataclass + Menu utilities
├── visibility.py                 # Visibility helpers: is_instance_of()
├── checks.py                     # Django system checks (E001-E007, W001-W002)
├── utils.py                      # Helpers: slugify, URL reversal
├── templatetags/
│   ├── __init__.py
│   └── plugin_tags.py            # {% get_plugin_tabs %} template tag
└── templates/
    ├── cotton/
    │   └── plugin/
    │       ├── tabs.html         # <c-plugin-tabs /> component
    │       └── base.html         # <c-plugin-base /> component (optional wrapper)
    └── plugins/
        └── base.html             # Framework fallback template for plugin views

fairdm/core/plugins.py            # Reusable base plugin classes (Overview, Edit, Delete, etc.)
fairdm/core/project/plugins.py    # Project-specific plugin registrations (migrated)
fairdm/core/dataset/plugins.py    # Dataset-specific plugin registrations (migrated)
fairdm/core/sample/plugins.py     # Sample-specific plugin registrations (migrated)
fairdm/core/measurement/plugins.py # Measurement-specific plugin registrations (migrated)
fairdm/contrib/contributors/plugins.py  # Contributor plugin registrations (migrated)
fairdm/contrib/activity_stream/plugins.py  # Activity plugin registrations (migrated)
fairdm/contrib/generic/plugins.py # Reusable plugins: Keywords, Descriptions, KeyDates (migrated)
fairdm/contrib/collections/plugins.py  # DataTable plugin (migrated)

fairdm/plugins.py                 # Re-export: from fairdm.contrib.plugins import *

tests/test_contrib/test_plugins/  # Test suite
├── __init__.py
├── test_base.py                  # Plugin mixin tests
├── test_group.py                 # PluginGroup tests
├── test_registry.py              # Registration + validation tests
├── test_urls.py                  # URL generation tests
├── test_templates.py             # Template resolution tests
├── test_tabs.py                  # Tab rendering tests
├── test_permissions.py           # Permission checking tests
├── test_checks.py                # Django system check tests
└── conftest.py                   # Fixtures: fake models, plugins, groups

fairdm_demo/plugins.py            # Demo app plugin examples (migrated/updated)
```

**Structure Decision**: Follows the existing FairDM pattern of `fairdm/contrib/{app}/` for contrib apps. Test structure mirrors source at `tests/test_contrib/test_plugins/`. Files being modified (migrations from current API) are the per-model `plugins.py` files across core and contrib packages.

### Files Removed

```text
fairdm/contrib/plugins/config.py    # PluginConfig/PluginMenuItem → replaced by inner Menu class
fairdm/contrib/plugins/views.py     # PluggableView → eliminated
fairdm/contrib/plugins/plugin.py    # FairDMPlugin → replaced by base.py Plugin
```

### Files Modified (Migration from Old API)

All existing `plugins.py` files across the codebase will be migrated from:
```python
# Old API
# OLD API - DO NOT USE
# @plugins.register(RockSample)  # Polymorphic subclass
class MyPlugin(FairDMPlugin, TemplateView):
    config = PluginConfig(title="My Plugin", category=EXPLORE, ...)
    # or
    menu_item = PluginMenuItem(name="My Plugin", category=EXPLORE, icon="eye")
```

To:
```python
# New API
@plugins.register(Sample)  # Base model only
class MyPlugin(Plugin, TemplateView):
    check = is_instance_of(RockSample)  # Visibility filter
    menu = {
        "label": "My Plugin",
        "icon": "eye",
        "order": 10,
    }
```

## Complexity Tracking

> No constitution violations. Table intentionally left empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | — | — |
