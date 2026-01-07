# Feature Specification: Testing Strategy & Fixtures

**Feature Branch**: `002-testing-strategy`
**Created**: 2026-01-06 (renamed from 004-testing-strategy-fixtures on 2026-01-07)
**Status**: Draft
**Input**: User description: "Define the testing strategy, test organization layers and feature validation. Establish test layer taxonomy (unit, integration, e2e, etc.) and their organizational structure. Define naming conventions for test files and test functions. Ensure feature specifications can reference standard test layers and fixture locations unambiguously, minimal happy-path integration tests exist covering end-to-end workflows, and testing conventions provide clear guidance on test naming, organization, and required assertions."

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.

  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Add a Test in the Right Place (Priority: P1)

As a contributor writing or updating a feature, I want a clear test-layer taxonomy and folder structure so I can quickly choose the right test type, place it correctly, and use consistent naming.

**Why this priority**: Consistent test organization is a prerequisite for reliable feature validation and reduces onboarding/maintenance costs.

**Independent Test**: A reviewer can verify this story using the documented taxonomy, file layout, and naming rules without needing any new product feature.

**Acceptance Scenarios**:

1. **Given** a new feature spec requires tests, **When** the spec references test coverage, **Then** it can cite a standard test layer and a standard fixture location unambiguously.
2. **Given** a contributor needs to add coverage for a small behavior, **When** they consult the test taxonomy, **Then** they can decide “unit vs integration vs contract” based on clear definitions and constraints.

---

### User Story 2 - Reuse Fixture Factories for Test Setup (Priority: P2)

As a contributor writing tests, I want access to reusable fixture factories that create test data so I can set up test scenarios quickly without duplicating setup code.

**Why this priority**: Shared fixture factories reduce duplication, improve test maintainability, and provide consistent test data patterns.

**Independent Test**: This can be tested by locating documented fixture factories and confirming they can be imported and used consistently across different test files.

**Acceptance Scenarios**:

1. **Given** an integration test needs test data, **When** the test imports a standard fixture factory, **Then** it can generate appropriate test objects without custom setup code.
2. **Given** multiple tests need similar data, **When** they use the same fixture factory, **Then** test data remains consistent and maintainable in one location.

---

### User Story 3 - Portal Developers Reuse FairDM Factories (Priority: P3)

As a portal developer building a research data portal with FairDM, I want to import and reuse FairDM's factories in my own test suite so I can test portal-specific features without duplicating factory setup for core FairDM models.

**Why this priority**: Portal developers need efficient testing workflows. Reusing FairDM factories accelerates portal-specific test development and ensures consistency with FairDM's data patterns.

**Independent Test**: This can be tested by creating a minimal downstream project, installing FairDM as a package, importing factories from `fairdm.factories`, and verifying they create valid model instances in the downstream environment.

**Acceptance Scenarios**:

1. **Given** a portal developer needs to test a custom feature that depends on FairDM Projects, **When** they import `from fairdm.factories import ProjectFactory` in their test, **Then** they can create Project instances with sensible defaults without reimplementing factory logic.
2. **Given** a portal developer wants to customize test data for their use case, **When** they call `ProjectFactory(title="Custom", custom_field=value)`, **Then** the factory overrides FairDM defaults while maintaining portal-specific customizations.
3. **Given** a portal developer is unfamiliar with FairDM's factory patterns, **When** they read the factory documentation, **Then** they find clear import examples, usage patterns, and field override guidance.

---

### Edge Cases

- A feature touches multiple layers; guidance must avoid double-testing the same behavior across layers without intent.
- A fixture generates incomplete or invalid test data; tests should fail with clear, actionable assertions.
- Test data includes auto-generated values (timestamps, IDs) that make equality checks flaky; fixtures must provide ways to normalize or mock these values.
- A test needs data in a specific state but no factory exists; guidance must clarify when to create new factories vs. modify existing ones.
- A portal developer extends a FairDM model with custom fields; guidance must clarify how to extend factories for portal-specific fields while inheriting FairDM factory logic.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001 (Taxonomy)**: The project MUST define three standard test layers: **unit**, **integration**, and **contract**, each with a written definition of purpose and boundaries.
- **FR-002 (Structure)**: The project MUST define a standard folder structure for each test layer so test placement is deterministic. Test organization MUST mirror Django app structure: tests/{layer}/app_name/test_module.py.
- **FR-003 (Naming)**: The project MUST define naming conventions for test files and test case names so intent is discoverable and consistent.
- **FR-004 (Fixtures - location)**: Factory-boy factories MUST be declared in their respective app packages (e.g., `fairdm/core/factories.py` for ProjectFactory) to maintain locality with models. A convenience module `fairdm/factories.py` MUST import and re-export all factories via `__all__` to enable downstream portal developers to use flat imports (`from fairdm.factories import ProjectFactory`). Pytest fixtures MAY be stored in `tests/fixtures/` for test-specific composition. Factories MUST be implemented using factory-boy DjangoModelFactory.
- **FR-005 (Fixture organization)**: The project MUST provide guidance on organizing fixtures by scope (module-level, session-level, function-level) and when to use each. Factories MUST be fully-featured, covering all possible fields with sensible defaults. Tests MUST override factory creation at runtime using factory-boy API (e.g., `ProjectFactory(title=None)`). Creating numerous factory subclasses for different scenarios is STRONGLY DISCOURAGED.
- **FR-006 (Fixture documentation)**: Each fixture factory MUST include clear docstrings documenting:
  - What test data it produces
  - What parameters it accepts for customization
  - Expected usage patterns and examples
- **FR-007 (Test tools)**: The project MUST specify which testing tools and libraries are standard: pytest (with built-in assertions), factory-boy, coverage tools (coverage.py), and pytest-django.
- **FR-008 (Spec referencability)**: Feature specifications MUST be able to reference test layers and fixture locations using stable, documented identifiers.
- **FR-009 (Assertions guidance)**: The testing conventions MUST specify minimum required assertions for each test layer (e.g., what must be asserted vs what may be omitted).
- **FR-010 (Coverage requirements)**: The project MUST define minimum test coverage expectations for new features (unit, integration, and when contract tests are needed). Coverage metrics SHOULD be used to identify untested code paths, but test quality (meaningful, maintainable, reliable) is more important than achieving specific percentage targets. New features SHOULD aim for thorough coverage of critical paths and edge cases.
- **FR-011 (Database strategy)**: Integration tests MUST use transaction rollback after each test for isolation and speed. The test database MUST be created once per test session and destroyed at the end.
- **FR-012 (Portal developer documentation)**: The project MUST provide documentation for downstream portal developers on:
  - How to install FairDM as a test dependency
  - How to import factories from `fairdm.factories`
  - How to override factory fields for portal-specific customizations
  - How to extend FairDM factories for models with portal-specific fields
  - Complete working examples of factory usage in downstream projects
- **FR-008 (Spec referencability)**: Feature specifications MUST be able to reference test layers and fixture locations using stable, documented identifiers.
- **FR-009 (Assertions guidance)**: The testing conventions MUST specify minimum required assertions for each test layer (e.g., what must be asserted vs what may be omitted).
- **FR-010 (Coverage requirements)**: The project MUST define minimum test coverage expectations for new features (unit, integration, and when contract tests are needed). Coverage metrics SHOULD be used to identify untested code paths, but test quality (meaningful, maintainable, reliable) is more important than achieving specific percentage targets. New features SHOULD aim for thorough coverage of critical paths and edge cases.
- **FR-011 (Database strategy)**: Integration tests MUST use transaction rollback after each test for isolation and speed. The test database MUST be created once per test session and destroyed at the end.

#### Standard Test Layer Definitions (for consistent use in specs)

- **Unit tests**: Validate behavior of a small unit in isolation. No reliance on external services or persisted state. Fast, deterministic, focused on one responsibility.
- **Integration tests**: Validate behavior across multiple components and/or persisted state. Focus on business workflows and cross-component interactions.
- **Contract tests**: Validate boundaries and interoperability "contracts" (e.g., API schemas, data format specifications, and compatibility expectations). Focus on inputs/outputs and compatibility, not internal implementation.

#### Standard Test Organization (paths are normative)

- Unit: `tests/unit/{app_name}/test_{module}.py`
- Integration: `tests/integration/{app_name}/test_{module}.py`
- Contract: `tests/contract/{app_name}/test_{module}.py`
- Factory-boy factories: Declared in `{app_name}/factories.py` (e.g., `fairdm/core/factories.py`), re-exported via `fairdm/factories.py` convenience module
- Pytest fixtures: `tests/fixtures/` for test-specific composition
- Conftest files: `conftest.py` at appropriate levels (root, layer-specific, app-specific)

Tests MUST mirror Django app structure to make source-to-test mapping intuitive. Factories MUST be declared near their models (app-level) and re-exported via convenience module for flat import structure (`from fairdm.factories import ProjectFactory`) to enable downstream reuse.

#### Standard Naming Conventions

- Test file names MUST use the form `test_<subject>` and live under the layer directory.
- Test case names MUST use the form `test_<behavior>__<condition>__<expected>` where:
  - `<behavior>` describes what is being validated
  - `<condition>` describes the key context/state
  - `<expected>` describes the observable outcome

#### Fixture Organization Guidelines

Fixture organization MUST follow these principles:

- **Location**: Factory-boy factories declared in app packages (`app_name/factories.py`) near their models, re-exported via `fairdm/factories.py` convenience module; pytest fixtures in `tests/fixtures/` for composition
- **Distribution**: Factories included in packaged distributions; `fairdm/factories.py` provides flat imports (`from fairdm.factories import ProjectFactory`) via `__all__` re-exports
- **Scope-based organization**: Group pytest fixtures by their scope (session, module, function)
- **Domain-based organization**: Organize factories by the domain entities they create (users, projects, datasets, etc.)
- **Fully-featured factories**: Factories MUST define all model fields with sensible defaults
- **Runtime overrides**: Tests customize factories at call-time (e.g., `ProjectFactory(title=None)`) rather than creating factory subclasses
- **Reusability**: Design fixtures to be composable - simple fixtures that can be combined for complex scenarios
- **Discovery**: Use `conftest.py` files at appropriate levels to make fixtures available where needed

Fixture factories MUST:

- Use factory-boy DjangoModelFactory
- Provide sensible defaults for all fields
- Allow selective override of specific fields
- Include docstrings with usage examples
- Be fully-featured (all fields) rather than creating multiple scenario-specific subclasses

### Key Entities *(include if feature involves data)*

- **Test Layer**: A named category (unit/integration/contract) with defined scope and required assertions.
- **Test Convention**: A set of naming, placement, and assertion rules that enable consistent contribution.
- **Fixture Factory**: A reusable factory-boy or pytest fixture that generates test data with sensible defaults.
- **Fixture Scope**: The lifecycle of a fixture (function, module, session) determining when it's created and torn down.
- **Test Tool**: A library or utility used for testing (pytest, factory-boy, coverage.py, pytest-django, etc.).
- **Test Quality**: Tests that are meaningful (verify behavior), maintainable (easy to update), and reliable (consistently correct).

### Assumptions

- The project uses pytest as the primary testing framework.
- Test contributors need both fast local feedback (unit tests) and integration test coverage for cross-component interactions.
- Fixture factories should be reusable across many feature tests and minimize duplication.
- Test organization should scale as the codebase grows.

### Dependencies

- None identified at the testing strategy level.

## Clarifications

### Session 2026-01-06

- Q: What tools/format should fixtures use? → A: pytest fixtures and/or factory-boy Factories
- Q: What minimum test coverage percentage should be required for new features? → A: Coverage is a guide, not a goal. Focus on test quality (meaningful, maintainable, reliable tests of critical paths) rather than specific percentages.
- Q: Should integration tests require database transactions to be rolled back after each test, or should they use a test database that's rebuilt for each test run? → A: Use both: rollback for individual tests, rebuild between test sessions
- Q: What assertion library should be standardized for tests beyond pytest's built-in assertions? → A: Use only pytest's built-in assertions
- Q: Should test file discovery follow a specific pattern for modules vs. packages? → A: Mirror app structure: tests/unit/app_name/test_module.py

### Session 2026-01-07

- Q: Where should factory-boy factories be stored - in tests/fixtures/ or in individual Django apps? → A: Individual Django apps, included in packaged distributions for downstream portal developers
- Q: Should factories be minimal or fully-featured? → A: Fully-featured covering all possible fields; tests override at runtime using factory-boy API (e.g. ProjectFactory(title=None))
- Q: Should we create factory subclasses for different test scenarios (e.g. ProjectFactoryWithoutTitle)? → A: Strongly discouraged; use runtime overrides instead
- Q: What should the factory import path convention be for downstream portal developers? → A: Centralized flatter structure: `from fairdm.factories import ProjectFactory` (Option B)
- Q: Should fairdm/factories.py contain all factory declarations or re-export from app packages? → A: Re-export; factories declared in app packages (e.g. fairdm/core/factories.py) for locality with models, then imported and re-exported via fairdm/factories.py `__all__` for convenience

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A contributor can identify the correct test layer and target directory for a new test in under 2 minutes using documented conventions.
- **SC-002**: Test documentation clearly specifies which testing tools to use (pytest, factory-boy) and how to organize fixtures, emphasizing test quality (meaningful, maintainable, reliable) over coverage percentages.
- **SC-003**: Fixture factories follow documented patterns with consistent docstrings and can be discovered via IDE autocomplete/search.
- **SC-004**: Feature specifications can reference test requirements using standard layer names and fixture locations.
