# Implementation Plan: FairDM Registry System

**Branch**: `002-fairdm-registry` | **Date**: 2026-01-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-fairdm-registry/spec.md`

**Note**: This plan follows the speckit.plan workflow. Phase 0 (Research) and Phase 1 (Design) outputs will be generated as separate documents.

## Summary

The FairDM Registry System provides a central mechanism for registering Sample and Measurement models with declarative configurations that auto-generate component classes (Forms, Tables, FilterSets, Serializers, Import/Export Resources, ModelAdmin classes). The registry implements a two-step API pattern: `config = registry.get_for_model(Model)` followed by `config.get_X_class()` for component access. The core implementation already exists and is stable; this feature spec documents the system and improves the ModelConfiguration API to use a simpler pattern: parent `fields` attribute + optional custom class overrides, eliminating intermediate nested config layers.

**Technical Approach**: Lazy component generation with caching, parent field configuration with custom class overrides, validation at registration time, and backwards-compatible refactoring of existing ModelConfiguration class.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: Django 5.1+, django-tables2 2.7+, django-filter 24.3+, django-crispy-forms 2.3+, crispy-bootstrap5 2025.6+, djangorestframework 3.15+, django-import-export 4.0+, django-polymorphic 4.1+
**Storage**: PostgreSQL (primary), SQLite (development/testing)
**Testing**: pytest 7.4+, pytest-django 4.5+, pytest-playwright 0.4+ (for UI verification), factory-boy 3.3+ (test fixtures)
**Target Platform**: Linux/Windows/macOS server environments, containerized deployment (Docker)
**Project Type**: Web application (Django framework extension)
**Performance Goals**:

- Configuration validation: <10ms per model at registration time
- Component generation: <50ms per component type on first access
- Cached component access: <1ms (dictionary lookup)
- Support 20+ registered models without noticeable startup delay

**Constraints**:

- Must maintain backwards compatibility with existing registrations in fairdm_demo
- Registry core mechanics (decorator, two-step API, factories) are stable and must not change
- All component generation must use framework conventions (django-tables2, django-filter, etc.)
- Auto-generated components must use Bootstrap 5 styling consistently

**Scale/Scope**:

- Expected 5-10 Sample models and 3-5 Measurement models per typical portal
- Supports 20+ models for advanced portals
- Auto-generates 6 component types per model (Form, Table, FilterSet, Serializer, Resource, ModelAdmin)
- ModelConfiguration API refactoring affects ~10 config classes across fairdm and fairdm_demo

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: FAIR-First Research Portals

**Status**: ✅ COMPLIANT
**Assessment**: Registry enables rich metadata exposure through auto-generated serializers and APIs. Registered models provide discoverable metadata via introspection API (`registry.samples`, `registry.measurements`). Component generation supports FAIR data practices by ensuring consistent forms, validation, and import/export capabilities.

### Principle II: Domain-Driven, Declarative Modeling

**Status**: ✅ COMPLIANT
**Assessment**: Registry is the primary mechanism for declarative model configuration. ModelConfiguration uses decorator pattern (`@register`) to declare intent without procedural code. Auto-generated components derive from model definitions and field specifications, ensuring schema is source of truth.

### Principle III: Configuration Over Custom Plumbing

**Status**: ✅ COMPLIANT
**Assessment**: Registration API is the primary extension point. Developers configure behavior via `fields` attribute and optional custom class overrides rather than writing boilerplate. Sensible defaults inferred for all 6 component types when not explicitly provided.

### Principle IV: Opinionated, Production-Grade Defaults

**Status**: ✅ COMPLIANT
**Assessment**: Uses recommended Django ecosystem (django-tables2, django-filter, crispy-bootstrap5, DRF). All auto-generated components use Bootstrap 5 styling consistently. Defaults are production-ready and require minimal decisions from developers.

### Principle V: Test-First Quality & Sustainability

**Status**: ⚠️ NEEDS ATTENTION
**Assessment**: Existing implementation has limited test coverage. This feature spec MUST include:

- Unit tests for ModelConfiguration field resolution and validation
- Integration tests for component generation and caching
- Contract tests for registry API methods
- Demo app tests demonstrating registration patterns
**Action Required**: Phase 1 must include comprehensive test plan. Implementation MUST follow test-first (red-green-refactor) discipline.

### Principle VI: Documentation Critical

**Status**: ⚠️ NEEDS ATTENTION
**Assessment**: Current registry implementation lacks comprehensive documentation. This feature spec MUST include:

- API reference for registry methods and ModelConfiguration attributes
- Developer guide showing common registration patterns
- Working examples in fairdm_demo with docstrings

**Action Required**: Phase 1 must generate documentation artifacts (quickstart.md, API contracts). Implementation MUST update docs in same PR.

### Principle VII: Living Demo & Reference Implementation

**Status**: ⚠️ NEEDS ATTENTION
**Assessment**: fairdm_demo currently has registration examples but lacks comprehensive docstrings and links to documentation. This feature MUST:

- Update fairdm_demo config classes with docstrings explaining each pattern
- Add links from docstrings to relevant documentation sections
- Include test files demonstrating introspection API usage
- Ensure all registration patterns shown in docs are demonstrated in demo app
**Action Required**: Phase 1 must include demo app update plan. Implementation MUST keep demo app synchronized.

### Gates Summary

**PASS - Proceed to Phase 0**: Core design is constitutionally sound. Architecture and approach align with all 7 principles.

**Action Items for Implementation Phase** (not immediate - these are requirements for code implementation):

1. ⚠️ Test coverage must reach >90% for registry and config modules (Constitution Principle V)
2. ⚠️ Documentation must be written alongside code changes (Constitution Principle VI)
3. ⚠️ Demo app must be updated in same PR as ModelConfiguration refactoring (Constitution Principle VII)

**Re-evaluation Trigger**: After Phase 1 design is complete, re-check that test strategy, documentation plan, and demo app updates adequately address Principles V, VI, and VII.

---

## Constitution Check (Post-Phase 1 Re-evaluation)

**Date**: 2026-01-12
**Trigger**: Phase 1 complete (data-model.md, contracts/, quickstart.md generated)

### Principle V: Testing Philosophy - Post-Design Check

**Status**: ✅ ADDRESSED IN DESIGN
**Assessment**: Phase 1 deliverables include comprehensive test strategy:

- **data-model.md Section 7.5**: Complete testing checklist with 6 test categories
  - Unit tests for field resolution algorithm (all 3 tiers)
  - Unit tests for field type mapping
  - Unit tests for validation (registration + generation)
  - Integration tests for lazy generation + caching
  - Contract tests for get_X_class() methods
  - Test cache invalidation (clear_cache())

- **contracts/**: Python Protocols provide type-safe interfaces for contract testing
- **Implementation checklist** explicitly calls out testing requirements

**Conclusion**: Test strategy adequately addresses >90% coverage requirement. Implementation ready.

### Principle VI: Documentation Critical - Post-Design Check

**Status**: ✅ ADDRESSED IN DESIGN
**Assessment**: Phase 1 deliverables provide complete documentation foundation:

- **quickstart.md**: 10-section developer guide with practical examples
  - Basic registration patterns (3 levels of complexity)
  - Component-specific field configuration
  - Custom class overrides
  - Registry introspection API
  - Common patterns and best practices

- **data-model.md**: Complete API specification with docstrings
  - ModelConfiguration class definition with comprehensive docstrings
  - Field resolution algorithm (pseudocode + examples)
  - Validation rules with examples
  - Exception hierarchy with usage examples

- **contracts/**: Python Protocols with detailed docstrings and usage examples
  - registry.py: FairDMRegistry API with examples
  - config.py: ModelConfiguration interface with examples
  - factories.py: ComponentFactory protocols with examples
  - exceptions.py: Exception classes with helpful error messages

**Conclusion**: Documentation plan adequately addresses API reference and developer guide requirements. Implementation ready.

### Principle VII: Living Demo & Reference Implementation - Post-Design Check

**Status**: ✅ ADDRESSED IN DESIGN
**Assessment**: Phase 1 deliverables include demo app update strategy:

- **data-model.md Section 7.6**: Explicit documentation checklist item
  - "Update fairdm_demo configs to new API"
  - "Add docstrings linking to documentation"

- **quickstart.md Section 10**: Explicitly lists demo app update as next step
  - "Update fairdm_demo to demonstrate new patterns"

- **Implementation plan** includes demo app updates in refactoring checklist

**Conclusion**: Demo app update plan adequately addresses synchronization and documentation requirements. Implementation ready.

### Post-Phase 1 Gates Summary

**✅ PASS - Proceed to Implementation**: All constitutional concerns addressed in design phase.

**Test Strategy** (Principle V): ✅ Complete checklist in data-model.md Section 7.5
**Documentation** (Principle VI): ✅ quickstart.md, data-model.md, contracts/ provide comprehensive docs
**Demo App** (Principle VII): ✅ Update plan explicit in implementation checklist

**No blockers identified**. Implementation may proceed using Phase 1 specifications.

## Project Structure

### Documentation (this feature)

```text
specs/002-fairdm-registry/
├── plan.md              # This file
├── research.md          # Phase 0 output (ModelConfiguration patterns research)
├── data-model.md        # Phase 1 output (ModelConfiguration API specification)
├── quickstart.md        # Phase 1 output (Registration examples and usage guide)
├── contracts/           # Phase 1 output (Python protocols and type signatures)
│   ├── registry.py      # FairDMRegistry protocol
│   ├── config.py        # ModelConfiguration protocol
│   └── factories.py     # Component factory protocols
└── tasks.md             # Phase 2 output (/speckit.tasks - NOT created by this command)
```

### Source Code (repository root)

```text
fairdm/
├── registry/
│   ├── registry.py          # FairDMRegistry class [STABLE - no changes]
│   ├── config.py            # ModelConfiguration class [REFACTOR NEEDED]
│   ├── components.py        # FormConfig, TableConfig, etc. [TO BE REMOVED]
│   ├── factories.py         # FormFactory, TableFactory, etc. [UPDATE FIELD RESOLUTION]
│   └── exceptions.py        # DuplicateRegistrationError, InvalidFieldError [NEW]
├── core/
│   ├── sample/
│   │   └── models.py        # Sample base class
│   └── measurement/
│       └── models.py        # Measurement base class
└── __init__.py              # Exports registry instance

fairdm_demo/
├── models.py                # Example Sample/Measurement models
├── config.py                # Registration examples [UPDATE WITH NEW API]
├── tables.py                # Custom Table examples
├── filters.py               # Custom FilterSet examples
└── forms.py                 # Custom Form examples [IF NEEDED]

tests/
├── unit/
│   └── registry/
│       ├── test_registry.py          # Registry core functionality
│       ├── test_config.py            # ModelConfiguration validation
│       ├── test_field_resolution.py  # Field inheritance and precedence
│       └── test_factories.py         # Component generation
├── integration/
│   └── registry/
│       ├── test_registration.py      # End-to-end registration flows
│       ├── test_introspection.py     # Registry discovery API
│       └── test_components.py        # Generated component behavior
└── contract/
    └── registry/
        ├── test_registry_api.py      # Registry method contracts
        └── test_config_api.py        # ModelConfiguration interface contracts
```

**Structure Decision**: Django web application with framework-level registry module. Core implementation exists in `fairdm/registry/`, examples in `fairdm_demo/`, tests organized by layer (unit/integration/contract). This feature refactors `config.py`, removes `components.py`, updates `factories.py` field resolution, and adds new exception types.

## Phase 0: Research & Discovery

**Goal**: Resolve unknowns about ModelConfiguration API design, field resolution patterns, and component generation strategies. Breaking changes are acceptable since the system is not yet widely deployed.

### Research Tasks

| Task ID | Topic | Key Questions |
| ------- | ----- | ------------- |
| R1 | Field Configuration Patterns | How do django-tables2, django-filter, and DRF handle field lists? What are precedence rules when both parent fields and component-specific fields exist? Best practices for field inheritance? |
| R2 | Lazy vs Eager Generation | Performance trade-offs of lazy generation with caching vs eager generation at registration? Django app startup time analysis? Caching strategies (class-level vs instance-level)? |
| R3 | Validation Timing & Strategy | What should be validated at registration time vs runtime? How to provide clear error messages for field name typos? Should validation use Django's check framework? |
| R4 | Field Resolution Algorithm | How to resolve fields from parent `fields` attribute to component-specific needs? Should CharField filters use CharFilter or icontains lookup? How to handle related field lookups (double-underscore)? |
| R5 | Custom Class Override Pattern | How should custom classes interact with parent fields? Should custom classes completely replace auto-generation or merge with configuration? Backwards compatibility with existing registrations? |
| R6 | Nested Config Removal Impact | What code depends on FormConfig, TableConfig, FiltersConfig, AdminConfig dataclasses? Migration strategy for existing configs? Can removal be done with deprecation warnings? |
| R7 | Factory Pattern Best Practices | Are current factories (FormFactory, TableFactory, etc.) following Django/DRF conventions? Should factories be class-based or function-based? Type hints and protocols for factory interfaces? |
| R8 | Polymorphic Model Handling | How does django-polymorphic affect field detection? Are there special fields to exclude? Does polymorphic queryset impact component generation? |

### Research Output: research.md

Will document decisions for each research task with:

- **Decision**: What was chosen
- **Rationale**: Why it was chosen (performance, simplicity, Django conventions, etc.)
- **Alternatives Considered**: What else was evaluated
- **Implementation Notes**: Any gotchas or special considerations
- **References**: Links to Django docs, library source code, Stack Overflow discussions, etc.

### Agent Dispatch Strategy

For each research task, launch a subagent with:

- Analyze existing implementation in `fairdm/registry/`
- Review Django/DRF/django-tables2/django-filter documentation
- Search for best practices and common patterns
- Examine fairdm_demo usage patterns
- Consolidate findings with specific recommendations

**Completion Criteria**: All 8 research tasks documented, no "NEEDS CLARIFICATION" items. Breaking changes acceptable - no backwards compatibility required.

## Phase 1: Design & Contracts

**Prerequisites**: Phase 0 research complete with all decisions documented in `research.md`.

**Goal**: Create detailed design specifications for ModelConfiguration API, registry contracts, and component generation patterns. All outputs must be implementation-ready with no ambiguity.

### Deliverables

#### 1. data-model.md

**Purpose**: Complete ModelConfiguration API specification with exact attributes, methods, and behavior

**Contents**:

- ModelConfiguration class definition (attributes, types, defaults)
- Field resolution algorithm (how parent `fields` flows to components)
- Validation rules and error messages
- Custom class override patterns
- Caching strategy for lazy generation
- Backwards compatibility layer (if needed)
- Type hints and protocols

**Dependencies**: Research tasks R1 (field patterns), R2 (lazy generation), R4 (field resolution), R5 (custom overrides), R6 (nested config removal - clean removal, no deprecation needed)

#### 2. contracts/ (Python protocols and type signatures)

**Purpose**: Define programmatic contracts for registry API and configuration interfaces

**Files**:

- `registry.py`: FairDMRegistry protocol (get_for_model, samples, measurements properties)
- `config.py`: ModelConfiguration protocol (model, fields attributes, get_X_class methods)
- `factories.py`: Factory function signatures (FormFactory, TableFactory, etc.)
- `exceptions.py`: Custom exception types (DuplicateRegistrationError, InvalidFieldError)

**Format**: Python Protocol classes with comprehensive docstrings, type hints, and examples

**Dependencies**: All Phase 0 research tasks

#### 3. quickstart.md

**Purpose**: Minimal working examples for portal developers

**Sections**:

- Basic registration (model + fields only)
- Custom Form class override
- Custom Table class override
- Multiple model registration patterns
- Introspection API usage (registry.samples, get_for_model)
- Migration from old API to new API

**Format**: Code snippets with explanations, runnable in fairdm_demo context

**Dependencies**: Research tasks R5 (custom overrides), R9 (backwards compatibility)

### Phase 1 Outputs Summary

| Artifact | Purpose | Status |
| -------- | ------- | ------ |
| data-model.md | ModelConfiguration API specification | TBD - Pending Phase 0 |
| contracts/registry.py | FairDMRegistry protocol | TBD - Pending Phase 0 |
| contracts/config.py | ModelConfiguration protocol | TBD - Pending Phase 0 |
| contracts/factories.py | Component factory signatures | TBD - Pending Phase 0 |
| contracts/exceptions.py | Custom exception types | TBD - Pending Phase 0 |
| quickstart.md | Developer usage examples | TBD - Pending Phase 0 |

**Completion Criteria**: All Phase 1 artifacts generated, reviewed, and validated against:

- Specification requirements (FR-001 through FR-023)
- Constitution principles (especially V, VI, VII)
- Research decisions from Phase 0
- Backwards compatibility with existing fairdm_demo registrations

### Agent Context Update

After Phase 1 completion, run:

```powershell
.\.specify\scripts\powershell\update-agent-context.ps1 -AgentType copilot
```

This updates `.github/instructions/copilot.instructions.md` with:

- Registry API patterns (decorator, two-step access)
- ModelConfiguration design decisions
- Component generation conventions
- Field resolution algorithm summary

## Phase 2: Task Generation (NOT part of this command)

Phase 2 is handled by the `/speckit.tasks` command, which will:

- Read spec.md, research.md, and data-model.md
- Generate implementation tasks in tasks.md
- Break down work into testable units
- Sequence tasks based on dependencies

**Do NOT execute Phase 2 as part of this plan command.**

## Next Steps

1. ✅ **Gates Passed**: Constitution Check complete, proceed to Phase 0
2. 🔄 **Execute Phase 0**: Launch research agents for all 9 research tasks
3. ⏳ **Create research.md**: Consolidate findings with decisions and rationale
4. ⏳ **Execute Phase 1**: Generate data-model.md, contracts/, and quickstart.md
5. ⏳ **Update Agent Context**: Run update-agent-context.ps1
6. ⏳ **Re-check Constitution**: Verify Principles V, VI, VII addressed
7. ⏳ **Run /speckit.tasks**: Generate implementation task breakdown

**Current Status**: Plan complete, ready for Phase 0 research execution.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
