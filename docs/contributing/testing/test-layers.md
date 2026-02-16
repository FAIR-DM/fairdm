# Test Layers

FairDM uses a three-layer test taxonomy to organize tests by their scope and purpose. Each layer has distinct characteristics, boundaries, and use cases.

```{contents}
:local:
:depth: 2
```

## Overview

| Layer | Purpose | Speed | Dependencies | Database |
|-------|---------|-------|--------------|----------|
| **Unit** | Test isolated logic | Fast (< 100ms) | None | No |
| **Integration** | Test component interactions | Medium (< 1s) | Database, services | Yes |
| **Contract** | Test API/data contracts | Slow (1-5s) | External systems | Maybe |

## Unit Tests

### Definition

Unit tests validate the behavior of a **single unit** (function, method, class) in **complete isolation** from external dependencies.

**Characteristics:**

- **Fast**: Run in milliseconds (target < 100ms per test)
- **Isolated**: No database, no file system, no network
- **Focused**: Test one responsibility at a time
- **Deterministic**: Same input always produces same output

### What to Test

✅ **Do test:**

- Pure functions and methods
- Business logic without side effects
- Input validation and error handling
- Utility functions and helpers
- Model methods that don't touch the database

❌ **Don't test:**

- Database queries or ORM interactions
- External API calls
- File system operations
- Multi-component workflows

### Example

```python
# tests/unit/fairdm/core/test_models.py
from fairdm.core.models import Project

def test_get_absolute_url__with_valid_project__returns_detail_url():
    """Test that get_absolute_url returns the correct detail URL."""
    project = Project(pk=123, slug="test-project")

    url = project.get_absolute_url()

    assert url == "/projects/test-project/"
```

**Why this is a unit test:**

- No database access (uses in-memory Project instance)
- Tests isolated method behavior
- Fast and deterministic

## Integration Tests

### Definition

Integration tests validate behavior **across multiple components** or with **persistent state** (database).

**Characteristics:**

- **Medium speed**: Run in sub-second range (target < 1s per test)
- **Realistic**: Use real database with transaction rollback
- **Cross-component**: Test multiple Django layers (models, views, forms)
- **Workflow-focused**: Validate end-to-end business scenarios

### What to Test

✅ **Do test:**

- Database queries and ORM relationships
- Model creation, update, delete workflows
- Form validation with database constraints
- View rendering with database data
- Signal handlers and lifecycle hooks
- Business workflows across components

❌ **Don't test:**

- External API integrations (use mocks)
- Long-running background tasks
- API contract validation (use contract tests)

### Example

```python
# tests/integration/fairdm/core/test_project_workflow.py
import pytest
from fairdm.factories import UserFactory, ProjectFactory

@pytest.mark.django_db
def test_project_creation__with_valid_data__creates_project_and_assigns_owner():
    """Test complete project creation workflow."""
    user = UserFactory()

    project = ProjectFactory(owner=user, title="Test Project")

    assert project.pk is not None
    assert project.owner == user
    assert project.title == "Test Project"
```

**Why this is an integration test:**

- Uses `@pytest.mark.django_db` to access database
- Tests creation workflow across User and Project models
- Validates ORM relationships
- Uses factory-boy for realistic data

## Contract Tests

### Definition

Contract tests validate **boundaries and interoperability** between systems. They focus on inputs, outputs, and data format compatibility.

**Characteristics:**

- **Slower**: May take 1-5 seconds per test
- **External-facing**: Test API endpoints, data exports, imports
- **Schema-focused**: Validate data structure and format
- **Compatibility**: Ensure backward compatibility and interoperability

### What to Test

✅ **Do test:**

- API endpoint response schemas (DRF serializers)
- Data import/export format validation
- External system integration contracts
- API backward compatibility
- Data migration contracts

❌ **Don't test:**

- Internal business logic (use unit tests)
- Database workflows (use integration tests)
- Performance characteristics

### Example

```python
# tests/contract/test_api_project_schema.py
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from fairdm.factories import ProjectFactory, UserFactory

@pytest.mark.django_db
def test_project_list_api__returns_valid_schema():
    """Test that project list API returns expected schema."""
    client = APIClient()
    user = UserFactory()
    client.force_authenticate(user=user)
    ProjectFactory.create_batch(2)

    response = client.get(reverse('api:project-list'))

    assert response.status_code == 200
    assert 'results' in response.data
    for project in response.data['results']:
        assert 'id' in project
        assert 'title' in project
        assert 'slug' in project
        assert 'created' in project
```

**Why this is a contract test:**

- Validates API response structure
- Ensures schema consistency
- Tests external-facing contract
- Doesn't test internal logic

## Decision Tree

Use this flowchart to choose the right test layer:

```{mermaid}
graph TD
    A[Need to write a test?] --> B{Does it touch<br/>the database?}
    B -->|No| C{Pure logic/<br/>calculation?}
    B -->|Yes| D{Testing API<br/>contract?}

    C -->|Yes| E[Unit Test]
    C -->|No| F{Mock dependencies<br/>practical?}

    F -->|Yes| E
    F -->|No| G[Integration Test]

    D -->|Yes| H[Contract Test]
    D -->|No| I{Multi-component<br/>workflow?}

    I -->|Yes| G
    I -->|No| E

    style E fill:#d4edda,stroke:#28a745
    style G fill:#fff3cd,stroke:#ffc107
    style H fill:#cce5ff,stroke:#007bff
```

## Quick Reference

### When to Use Each Layer

**Unit tests** for:

- Utility functions
- Model property calculations
- Input validation
- Error handling logic
- Business rule calculations

**Integration tests** for:

- CRUD operations
- Model relationships
- Form validation with database
- View rendering with data
- Signal/lifecycle workflows

**Contract tests** for:

- API response schemas
- Data import/export formats
- External system integration
- Backward compatibility
- Migration contracts

### Test Organization

```text
tests/
├── unit/                    # Fast, isolated tests
│   ├── fairdm/
│   │   └── core/
│   │       └── test_models.py
│   └── conftest.py
├── integration/             # Database-backed tests
│   ├── fairdm/
│   │   └── core/
│   │       └── test_project_workflow.py
│   └── conftest.py
├── contract/                # API/schema tests
│   └── test_api_project_schema.py
└── fixtures/                # Shared test data
    ├── factories.py
    └── pytest_fixtures.py
```

## Best Practices

### Unit Tests

1. **Keep them fast**: Target < 100ms per test
2. **No external dependencies**: Mock database, APIs, file system
3. **Test one thing**: Focus on single responsibility
4. **Use clear names**: Follow `test_<behavior>__<condition>__<expected>` pattern

### Integration Tests

1. **Use factories**: Factory-boy for realistic test data
2. **Transaction rollback**: Leverage `@pytest.mark.django_db` for isolation
3. **Test workflows**: Validate complete business scenarios
4. **Avoid fixtures**: Prefer factory-boy over fixture files

### Contract Tests

1. **Schema validation**: Assert on response structure
2. **Backward compatibility**: Ensure changes don't break contracts
3. **Real clients**: Use actual API clients (not mocks)
4. **Version awareness**: Test multiple API versions if applicable

## Common Pitfalls

::::{grid} 1 1 2 2
:gutter: 3

:::{grid-item-card} ❌ Slow Unit Tests
Unit tests that access database, file system, or network are misclassified.

**Fix**: Mock external dependencies or move to integration layer.
:::

:::{grid-item-card} ❌ Brittle Integration Tests
Tests that depend on specific data or state in fixtures.

**Fix**: Use factories with explicit data creation per test.
:::

:::{grid-item-card} ❌ Testing Implementation
Tests that assert on internal details rather than behavior.

**Fix**: Test observable behavior and outcomes.
:::

:::{grid-item-card} ❌ Over-mocking
Mocking so extensively that test doesn't validate real behavior.

**Fix**: Use integration tests for realistic scenarios.
:::

::::

## Next Steps

```{seealso}
- Learn about [Test Quality](test-quality.md) principles
- Follow [Test Organization](test-organization.md) conventions
- Use [Fixtures & Factories](fixtures.md) for test data creation
- Understand [Database Strategy](database-strategy.md) for integration tests
- Read [Running Tests](running-tests.md) for CLI usage
- Check [Coverage](coverage.md) to identify untested code paths
```
