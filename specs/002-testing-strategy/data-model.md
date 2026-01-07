# Phase 1: Data Model - Testing Strategy & Fixtures

**Feature**: 004-testing-strategy-fixtures
**Date**: 2026-01-06

## Overview

This document defines the formal data models for FairDM's testing strategy. Since this feature is documentation and infrastructure (not runtime code), the "data models" are conceptual taxonomies and organizational patterns rather than Django models.

---

## Test Layer Taxonomy

### Model: TestLayer

**Purpose**: Formal classification system for categorizing tests by isolation level and testing goals.

**Attributes**:

| Attribute    | Type   | Description                                                          | Constraints                |
| ------------ | ------ | -------------------------------------------------------------------- | -------------------------- |
| name         | string | Layer identifier                                                     | One of: unit, integration, contract |
| purpose      | string | What this layer validates                                            | Required                   |
| isolation    | string | Degree of isolation from external dependencies                       | One of: high, medium, low  |
| speed        | string | Expected execution speed relative to other layers                    | One of: fast, medium, slow |
| dependencies | list   | What external systems/state this layer may interact with             | Required                   |
| path_pattern | string | File system location pattern for tests in this layer                 | Must match: `tests/{layer}/{app}/test_{module}.py` |

**Layer Definitions**:

#### Unit Layer

```yaml
name: unit
purpose: Validate behavior of a small unit (function, method, class) in isolation
isolation: high
speed: fast
dependencies: []  # No external dependencies
path_pattern: tests/unit/{app_name}/test_{module}.py
characteristics:
  - No database access
  - No file system access
  - No network calls
  - Mocks/stubs for all dependencies
  - Tests single responsibility
  - Deterministic (no randomness, no time dependencies)
```

#### Integration Layer

```yaml
name: integration
purpose: Validate behavior across multiple components and/or persisted state
isolation: medium
speed: medium
dependencies:
  - Test database (PostgreSQL)
  - Django ORM
  - File system (if testing file operations)
path_pattern: tests/integration/{app_name}/test_{module}.py
characteristics:
  - Database access via pytest.mark.django_db
  - Tests cross-component workflows
  - Tests business logic end-to-end
  - Uses factory-boy for test data
  - Transaction rollback for isolation
```

#### Contract Layer

```yaml
name: contract
purpose: Validate boundaries and interoperability contracts (API schemas, data formats)
isolation: low
speed: slow
dependencies:
  - Test database
  - API endpoints (if testing REST API)
  - External service mocks (if testing integrations)
path_pattern: tests/contract/{app_name}/test_{module}.py
characteristics:
  - Tests API request/response schemas
  - Tests data format specifications (JSON, CSV, XML)
  - Tests backward compatibility
  - Tests interoperability with external systems
  - May use pytest-playwright for UI contracts
```

### Decision Rules

**Given** a test scenario, **choose the layer** based on:

1. **Does it require database/file system/network?**
   - No → Unit
   - Yes → Continue

2. **Is it testing API boundaries or data format contracts?**
   - Yes → Contract
   - No → Continue

3. **Does it test behavior across multiple components?**
   - Yes → Integration
   - No → Unit (mock dependencies)

### Anti-Patterns

❌ **Don't**: Write unit tests that access database
❌ **Don't**: Write integration tests that duplicate unit test coverage without adding cross-component validation
❌ **Don't**: Write contract tests that validate internal implementation details

---

## Test Organization Pattern

### Model: TestDirectory

**Purpose**: File system organization structure that mirrors Django app structure for intuitive source-to-test mapping.

**Structure**:

```text
tests/
├── conftest.py                      # Root pytest configuration
├── fixtures/                        # Shared fixtures
│   ├── __init__.py
│   ├── factories.py                 # factory-boy factories
│   └── pytest_fixtures.py           # pytest fixtures
├── unit/                            # Unit tests layer
│   ├── conftest.py                  # Layer-specific configuration
│   ├── fairdm_core/                 # App-level directory
│   │   ├── conftest.py              # App-specific fixtures
│   │   ├── test_models.py           # Tests for fairdm_core/models.py
│   │   ├── test_views.py            # Tests for fairdm_core/views.py
│   │   └── test_utils.py            # Tests for fairdm_core/utils.py
│   └── fairdm_demo/
│       ├── conftest.py
│       └── test_models.py
├── integration/                     # Integration tests layer
│   ├── conftest.py
│   ├── fairdm_core/
│   │   ├── conftest.py
│   │   ├── test_project_workflow.py # Cross-component workflows
│   │   └── test_dataset_creation.py
│   └── fairdm_demo/
│       └── test_sample_workflows.py
└── contract/                        # Contract tests layer
    ├── conftest.py
    ├── api/                         # API contract tests
    │   ├── conftest.py
    │   ├── test_project_api_schema.py
    │   └── test_dataset_api_schema.py
    └── ui/                          # UI contract tests (pytest-playwright)
        ├── conftest.py
        └── test_project_detail_page.py
```

**Mapping Rules**:

| Source File                         | Unit Test Location                           | Integration Test Location                   |
| ----------------------------------- | -------------------------------------------- | ------------------------------------------- |
| `fairdm/core/models.py`             | `tests/unit/fairdm_core/test_models.py`      | `tests/integration/fairdm_core/test_*.py`   |
| `fairdm/core/views.py`              | `tests/unit/fairdm_core/test_views.py`       | `tests/integration/fairdm_core/test_*.py`   |
| `fairdm/contrib/accounts/forms.py`  | `tests/unit/contrib_accounts/test_forms.py`  | `tests/integration/contrib_accounts/test_*.py` |

**conftest.py Hierarchy**:

1. **Root `tests/conftest.py`**: Session-level fixtures (database setup, global configuration)
2. **Layer `tests/{layer}/conftest.py`**: Layer-specific fixtures and markers
3. **App `tests/{layer}/{app}/conftest.py`**: App-specific test data factories and fixtures

---

## Test Naming Convention

### Model: TestName

**Purpose**: Standardized naming pattern that encodes test intent, making tests self-documenting.

**Pattern**: `test_<behavior>__<condition>__<expected>`

**Components**:

| Component   | Description                                      | Examples                                    |
| ----------- | ------------------------------------------------ | ------------------------------------------- |
| behavior    | What behavior/operation is being validated       | `save`, `delete`, `calculate_age`, `render` |
| condition   | Key context, state, or input that matters        | `with_invalid_email`, `when_authenticated`, `for_polymorphic_model` |
| expected    | Expected outcome (success, error, side effect)   | `raises_validation_error`, `returns_queryset`, `creates_related_objects` |

**Examples**:

```python
# Unit test
def test_save__with_invalid_email__raises_validation_error():
    """When saving a User with invalid email format, ValidationError is raised."""
    pass

# Integration test
def test_project_creation__with_datasets__creates_related_objects():
    """When creating a Project with datasets, related Dataset objects are created."""
    pass

# Contract test
def test_project_api__list_endpoint__returns_valid_json_schema():
    """When requesting /api/projects/, response matches OpenAPI schema."""
    pass
```

**File Naming**: `test_{module}.py` where `{module}` matches the source module name.

**Class Naming** (optional, for grouping related tests):

```python
class TestProjectModel:
    """Group tests for Project model behavior."""

    def test_save__with_valid_data__succeeds(self):
        pass

    def test_delete__with_related_datasets__cascades(self):
        pass
```

---

## Fixture Organization Model

### Model: FixtureScope

**Purpose**: Categorize fixtures by lifecycle scope and mutability characteristics.

**Scopes**:

| Scope    | Lifecycle                  | Use Case                                         | Mutability | Example                          |
| -------- | -------------------------- | ------------------------------------------------ | ---------- | -------------------------------- |
| function | Created/destroyed per test | Default; ensures test isolation                  | Mutable    | `sample_factory()`, `rf` (RequestFactory) |
| module   | Created once per module    | Expensive setup, immutable data                  | Immutable  | Module-level reference data      |
| session  | Created once per test run  | Very expensive setup, truly immutable data       | Immutable  | Database creation, global config |

**Fixture Naming Conventions**:

- **Factories**: `{model}_factory` (e.g., `project_factory`, `user_factory`)
- **Pytest fixtures**: Descriptive names reflecting what they provide (e.g., `authenticated_user`, `sample_with_measurements`)
- **Scope suffix**: Optionally add `_session` or `_module` for non-function scopes (e.g., `db_session`, `countries_module`)

**Organization by Domain**:

```python
# tests/fixtures/factories.py
"""Core FairDM model factories."""

class UserFactory(DjangoModelFactory):
    """Factory for auth.User instances."""
    pass

class ProjectFactory(DjangoModelFactory):
    """Factory for fairdm_core.Project instances."""
    pass

# tests/fixtures/pytest_fixtures.py
"""Pytest fixtures for common test scenarios."""

@pytest.fixture
def authenticated_user(user_factory):
    """Returns authenticated User instance."""
    return user_factory()

@pytest.fixture
def project_with_datasets(project_factory, dataset_factory):
    """Returns Project with 3 related Datasets."""
    project = project_factory()
    dataset_factory.create_batch(3, project=project)
    return project
```

---

## Factory-Boy Pattern Model

### Model: FactoryDefinition

**Purpose**: Standardized factory-boy factory structure for creating test data.

**Base Template**:

```python
class {Model}Factory(DjangoModelFactory):
    """
    Factory for creating {Model} test instances.

    Usage:
        # Create with defaults
        obj = {Model}Factory()

        # Override specific fields
        obj = {Model}Factory(name="Custom Name")

        # Create batch
        objs = {Model}Factory.create_batch(10)
    """
    class Meta:
        model = "app_label.{Model}"
        django_get_or_create = ("natural_key_field",)  # Optional

    # Required fields
    name = factory.Faker("catch_phrase")

    # Foreign keys
    related_model = factory.SubFactory(RelatedModelFactory)

    # Optional fields with defaults
    description = factory.Faker("text", max_nb_chars=200)

    # Conditional fields
    @factory.lazy_attribute
    def computed_field(self):
        return f"{self.name}_computed"
```

**Polymorphic Factory Pattern**:

```python
# Base factory for polymorphic parent
class SampleFactory(DjangoModelFactory):
    class Meta:
        model = "fairdm_core.Sample"

    name = factory.Faker("catch_phrase")
    project = factory.SubFactory(ProjectFactory)

# Child factory for specific type
class RockSampleFactory(SampleFactory):
    class Meta:
        model = "fairdm_demo.RockSample"

    rock_type = factory.Iterator(["igneous", "sedimentary", "metamorphic"])
```

---

## Summary

This data model defines the conceptual structure for FairDM's testing strategy:

1. **TestLayer**: Three-layer taxonomy (unit, integration, contract) with formal definitions
2. **TestDirectory**: File system organization mirroring Django app structure
3. **TestName**: Standardized naming convention encoding behavior, condition, and expected outcome
4. **FixtureScope**: Categorization by lifecycle scope (function, module, session)
5. **FactoryDefinition**: Standardized factory-boy factory structure for test data generation

These models provide the foundation for Phase 1 contracts and quickstart documentation.
