# 5-Minute Testing Quickstart

Get started with FairDM testing in 5 minutes. This guide walks through writing your first test using FairDM's testing strategy.

## Prerequisites

```bash
# Install dependencies
poetry install --with dev

# Verify pytest is installed
poetry run pytest --version
```

## Step 1: Choose Your Test Layer (1 minute)

Use this decision tree to pick the right test layer:

```{mermaid}
flowchart TD
    A[What are you testing?] --> B{Uses database?}
    B -->|No| C[Unit Test]
    B -->|Yes| D{Multiple components?}
    D -->|No| E[Integration Test]
    D -->|Yes| F{External API/contract?}
    F -->|Yes| G[Contract Test]
    F -->|No| E

    C --> H[tests/unit/]
    E --> I[tests/integration/]
    G --> J[tests/contract/]
```

**Quick rules:**

- **Unit test** if testing isolated logic (no database, no file system)
- **Integration test** if testing database interactions or file operations
- **Contract test** if testing API endpoints or external service contracts

## Step 2: Place Your Test File (30 seconds)

Follow the directory structure:

```text
tests/
├── unit/                    # Unit tests (fast, isolated)
│   └── fairdm/
│       └── core/
│           └── test_models.py
├── integration/             # Integration tests (database)
│   └── fairdm/
│       └── core/
│           └── test_api.py
└── contract/                # Contract tests (API validation)
    └── test_project_api.py
```

**Naming convention:**

- File: `test_<module>.py` (e.g., `test_models.py`, `test_views.py`)
- Function: `test_<behavior>__<condition>__<expected>` (double underscores!)

## Step 3: Write Your First Test (2 minutes)

### Example: Unit Test

```python
# tests/unit/fairdm/core/test_models.py
import pytest
from fairdm.core.models import Project

@pytest.mark.unit
def test_project_title_validation__empty_title__raises_error():
    """Project with empty title raises ValidationError."""
    project = Project(title="")  # build(), don't save()

    with pytest.raises(ValidationError):
        project.full_clean()  # Validate without database
```

**Key points:**

- **Mark layer**: `@pytest.mark.unit`
- **Naming**: `test_<behavior>__<condition>__<expected>`
- **No database**: Use `.build()` or model instantiation without `.save()`

### Example: Integration Test

```python
# tests/integration/fairdm/core/test_api.py
import pytest
from fairdm.factories import ProjectFactory

@pytest.mark.django_db
@pytest.mark.integration
def test_project_creation__with_valid_data__creates_project():
    """Creating a project with valid data persists to database."""
    project = ProjectFactory(title="My Project")

    assert project.pk is not None
    assert project.title == "My Project"
```

**Key points:**

- **Mark database**: `@pytest.mark.django_db`
- **Mark layer**: `@pytest.mark.integration`
- **Use factories**: `ProjectFactory()` for test data

### Example: Contract Test

```python
# tests/contract/test_project_api.py
import pytest
from rest_framework.test import APIClient
from fairdm.factories import UserFactory, ProjectFactory

@pytest.mark.django_db
@pytest.mark.contract
def test_project_list_endpoint__authenticated_user__returns_200():
    """Project list API returns 200 for authenticated users."""
    client = APIClient()
    user = UserFactory()
    client.force_authenticate(user=user)

    response = client.get("/api/projects/")

    assert response.status_code == 200
```

**Key points:**

- **Mark database**: `@pytest.mark.django_db`
- **Mark layer**: `@pytest.mark.contract`
- **Test contract**: Verify status codes, response structure, not implementation

## Step 4: Run Your Test (1 minute)

```bash
# Run your specific test file
poetry run pytest tests/unit/fairdm/core/test_models.py -v

# Or run by layer
poetry run pytest tests/unit/ -v               # All unit tests
poetry run pytest tests/integration/ -v        # All integration tests

# Or run by marker
poetry run pytest -m unit -v                   # Unit tests only
poetry run pytest -m integration -v            # Integration tests only
```

**Expected output:**

```text
tests/unit/fairdm/core/test_models.py::test_project_title_validation__empty_title__raises_error PASSED

============================== 1 passed in 0.12s ===============================
```

## Step 5: Use Factories for Test Data (bonus)

Instead of manually creating test data, use factories:

```python
from fairdm.factories import UserFactory, ProjectFactory, DatasetFactory

# Create a user
user = UserFactory()

# Create a project owned by that user
project = ProjectFactory(owner=user, title="Custom Title")

# Create multiple datasets
datasets = DatasetFactory.create_batch(3, project=project)

# Override specific fields
dataset = DatasetFactory(
    project=project,
    title="Specific Dataset",
    is_public=False
)
```

**Available factories:**

- **UserFactory**: Creates test users with unique usernames/emails
- **ProjectFactory**: Creates projects with default owner
- **DatasetFactory**: Creates datasets linked to projects

See [Fixtures & Factories](fixtures.md) for comprehensive patterns.

## Common Patterns

### Testing Validation

```python
@pytest.mark.unit
def test_model_validation__invalid_data__raises_error():
    """Model validation catches invalid data."""
    obj = MyModel(invalid_field="bad value")

    with pytest.raises(ValidationError) as exc_info:
        obj.full_clean()

    assert "invalid_field" in str(exc_info.value)
```

### Testing Database Queries

```python
@pytest.mark.django_db
@pytest.mark.integration
def test_queryset_filter__by_status__returns_correct_objects():
    """Filtering by status returns only matching objects."""
    active_project = ProjectFactory(status="active")
    archived_project = ProjectFactory(status="archived")

    active_projects = Project.objects.filter(status="active")

    assert active_project in active_projects
    assert archived_project not in active_projects
```

### Testing API Responses

```python
@pytest.mark.django_db
@pytest.mark.contract
def test_api_endpoint__returns_expected_schema():
    """API response matches expected schema."""
    client = APIClient()
    project = ProjectFactory()

    response = client.get(f"/api/projects/{project.pk}/")

    assert response.status_code == 200
    assert "id" in response.data
    assert "title" in response.data
    assert response.data["id"] == project.pk
```

## Quick Reference

### Test Markers

```python
@pytest.mark.unit            # Unit test (no database)
@pytest.mark.integration     # Integration test (database)
@pytest.mark.contract        # Contract test (API)
@pytest.mark.slow            # Slow test (>1 second)
@pytest.mark.django_db       # Enable database access
```

### Pytest Commands

```bash
# Run all tests
poetry run pytest

# Run specific layer
poetry run pytest tests/unit/
poetry run pytest -m unit

# Verbose output
poetry run pytest -v

# Stop on first failure
poetry run pytest -x

# Reuse database (faster)
poetry run pytest --reuse-db

# With coverage
poetry run pytest --cov=fairdm --cov-report=term-missing
```

### Factory Patterns

```python
# Create in-memory (unit tests)
obj = MyFactory.build()

# Create in database (integration tests)
obj = MyFactory.create()

# Create multiple objects
objects = MyFactory.create_batch(5)

# Override fields
obj = MyFactory(custom_field="value")
```

## Troubleshooting

### "No module named 'fairdm.factories'"

**Solution**: Ensure FairDM is installed:

```bash
poetry install
```

### "django.db.utils.OperationalError: database does not exist"

**Solution**: Create test database:

```bash
poetry run pytest --create-db
```

### "Test function name does not follow convention"

**Solution**: Use double underscores:

```python
# ❌ Bad
def test_project_creation():
    ...

# ✅ Good
def test_project_creation__with_valid_data__creates_project():
    ...
```

## Next Steps

Now that you've written your first test, explore:

::::{grid} 1 1 2 2
:gutter: 3

:::{grid-item-card} {octicon}`list-unordered` Test Layers
:link: test-layers
:link-type: doc

Deep dive into unit, integration, and contract test layers.
:::

:::{grid-item-card} {octicon}`package` Fixtures & Factories
:link: fixtures
:link-type: doc

Master factory-boy patterns for efficient test data creation.
:::

:::{grid-item-card} {octicon}`database` Database Strategy
:link: database-strategy
:link-type: doc

Understand transaction rollback and test isolation.
:::

:::{grid-item-card} {octicon}`graph` Coverage
:link: coverage
:link-type: doc

Use coverage.py to identify untested code paths.
:::

::::

## Complete Example

Here's a complete working example combining all concepts:

```python
# tests/integration/fairdm/core/test_project_workflow.py
import pytest
from fairdm.factories import UserFactory, ProjectFactory, DatasetFactory

@pytest.mark.django_db
@pytest.mark.integration
class TestProjectWorkflow:
    """Test complete project creation workflow."""

    def test_create_project_with_datasets__complete_workflow__succeeds(self):
        """Creating project with datasets persists all relationships."""
        # Arrange: Create user and project
        user = UserFactory(username="researcher")
        project = ProjectFactory(
            owner=user,
            title="Geological Survey 2024",
            is_public=True
        )

        # Act: Create datasets
        datasets = DatasetFactory.create_batch(
            3,
            project=project,
            is_public=True
        )

        # Assert: Verify relationships
        assert project.pk is not None
        assert project.owner == user
        assert project.datasets.count() == 3
        assert all(ds.project == project for ds in datasets)
        assert all(ds.is_public for ds in datasets)
```

**Run this test:**

```bash
poetry run pytest tests/integration/fairdm/core/test_project_workflow.py -v
```

You're now ready to write tests for FairDM! 🎉
