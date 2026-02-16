# Test Organization

FairDM follows a standardized directory structure and naming convention to make test discovery intuitive and consistent.

```{contents}
:local:
:depth: 2
```

## Directory Structure

Tests are organized by **layer** and **Django app** to mirror the source code structure:

```text
tests/
├── conftest.py                 # Root-level fixtures (database setup)
├── unit/                       # Unit test layer
│   ├── conftest.py            # Unit-specific fixtures (RequestFactory)
│   ├── fairdm/                # Mirror Django app structure
│   │   ├── core/
│   │   │   ├── test_models.py
│   │   │   ├── test_views.py
│   │   │   └── test_utils.py
│   │   ├── contrib/
│   │   │   └── user/
│   │   │       └── test_models.py
│   │   └── plugins/
│   │       └── test_registry.py
│   └── fairdm_demo/
│       └── test_models.py
├── integration/                # Integration test layer
│   ├── conftest.py            # Integration-specific fixtures
│   ├── fairdm/
│   │   └── core/
│   │       ├── test_project_workflow.py
│   │       └── test_dataset_workflow.py
│   └── fairdm_demo/
│       └── test_demo_workflow.py
├── contract/                   # Contract test layer
│   ├── conftest.py            # Contract-specific fixtures (API client)
│   ├── test_api_project_schema.py
│   └── test_api_dataset_schema.py
└── fixtures/                   # Shared test data
    ├── __init__.py
    ├── factories.py           # Factory-boy factories
    └── pytest_fixtures.py     # Pytest fixtures
```

## Mapping Rules

### Rule 1: Layer-Based Organization

Tests are grouped by **test layer** (unit, integration, contract) at the top level:

- `tests/unit/` - Fast, isolated tests
- `tests/integration/` - Database-backed tests
- `tests/contract/` - API/schema validation tests

**Why**: Layer-based organization allows running specific test types independently:

```bash
poetry run pytest tests/unit/        # Fast feedback
poetry run pytest tests/integration/ # Database tests
poetry run pytest tests/contract/    # API validation
```

### Rule 2: App-Mirroring Structure

Within each layer, test directories **mirror Django app structure**:

**Source code:**

```text
fairdm/
├── core/
│   ├── models.py
│   ├── views.py
│   └── utils.py
└── contrib/
    └── user/
        └── models.py
```

**Test code:**

```text
tests/unit/fairdm/
├── core/
│   ├── test_models.py
│   ├── test_views.py
│   └── test_utils.py
└── contrib/
    └── user/
        └── test_models.py
```

**Why**: Mirroring makes it easy to find tests for specific modules.

### Rule 3: Module-to-Test File Mapping

Test files use the prefix `test_` followed by the module name:

| Source Module | Test File |
|---------------|-----------|
| `models.py` | `test_models.py` |
| `views.py` | `test_views.py` |
| `serializers.py` | `test_serializers.py` |
| `utils.py` | `test_utils.py` |

**Exception**: Contract tests may not mirror source structure if testing API endpoints:

```text
tests/contract/
├── test_api_project_schema.py      # Tests /api/projects/
└── test_api_dataset_schema.py      # Tests /api/datasets/
```

## Conftest Files

Pytest uses `conftest.py` files to provide fixtures at different scopes:

### Root conftest.py

**Location**: `tests/conftest.py`

**Purpose**: Session-level fixtures available to all tests

**Example:**

```python
"""Root conftest for all test layers."""
import pytest
from django.core.management import call_command

@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """
    Create test database once per session.

    Uses django_db_blocker to ensure database is created before tests run.
    """
    with django_db_blocker.unblock():
        call_command("migrate", "--noinput")
```

### Layer-Specific conftest.py

**Unit Layer** (`tests/unit/conftest.py`):

```python
"""Conftest for unit tests."""
import pytest
from django.test import RequestFactory

@pytest.fixture
def rf():
    """
    RequestFactory instance for creating mock HTTP requests.

    Used in unit tests to test views without full HTTP stack.
    """
    return RequestFactory()
```

**Integration Layer** (`tests/integration/conftest.py`):

```python
"""Conftest for integration tests."""
import pytest

# Integration-specific fixtures go here
# Example: fixtures for complex database scenarios
```

**Contract Layer** (`tests/contract/conftest.py`):

```python
"""Conftest for contract tests."""
import pytest
from rest_framework.test import APIClient

@pytest.fixture
def api_client():
    """
    DRF APIClient for testing API endpoints.

    Provides authentication and JSON handling.
    """
    return APIClient()
```

### App-Specific conftest.py

You can also create conftest.py files at the app level:

**Example** (`tests/unit/fairdm/core/conftest.py`):

```python
"""Fixtures specific to fairdm.core unit tests."""
import pytest
from fairdm.core.models import Project

@pytest.fixture
def sample_project_data():
    """
    Sample data for Project creation in unit tests.

    Returns dict without creating database objects.
    """
    return {
        "title": "Test Project",
        "slug": "test-project",
        "description": "A test project",
    }
```

## Test Naming Convention

### File Names

Test files MUST use the pattern: `test_<module>.py`

**Examples:**

- `test_models.py` - Tests for models.py
- `test_views.py` - Tests for views.py
- `test_serializers.py` - Tests for serializers.py

### Test Function Names

Test functions MUST use the pattern: `test_<behavior>__<condition>__<expected>`

**Pattern Breakdown:**

| Component | Description | Example |
|-----------|-------------|---------|
| `<behavior>` | What is being tested | `project_creation`, `login`, `dataset_delete` |
| `<condition>` | Key context or state | `with_valid_data`, `invalid_password`, `related_samples` |
| `<expected>` | Observable outcome | `creates_project`, `returns_error`, `cascades_deletion` |

**Examples:**

```python
# ✅ Clear and descriptive
def test_login__with_invalid_password__returns_error():
    ...

def test_project_creation__with_blank_title__raises_validation_error():
    ...

def test_dataset_delete__with_related_samples__cascades_deletion():
    ...

# ❌ Unclear intent
def test_login():
    ...

def test_project():
    ...

def test_1():
    ...
```

### Docstrings

Each test SHOULD include a docstring explaining **why** the behavior matters:

```python
def test_project_visibility__private_project_with_anonymous_user__returns_403():
    """
    Anonymous users cannot access private projects.

    This ensures projects marked private remain inaccessible
    until explicit permission is granted via django-guardian.
    """
    ...
```

## Complete Example

Here's a complete example showing proper organization:

**Source File**: `fairdm/core/models.py`

```python
class Project(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)

    def get_absolute_url(self):
        return f"/projects/{self.slug}/"
```

**Unit Test**: `tests/unit/fairdm/core/test_models.py`

```python
"""Unit tests for fairdm.core.models."""
from fairdm.core.models import Project

def test_get_absolute_url__with_valid_slug__returns_detail_url():
    """Test URL generation without database access."""
    project = Project(pk=123, slug="test-project")

    url = project.get_absolute_url()

    assert url == "/projects/test-project/"
```

**Integration Test**: `tests/integration/fairdm/core/test_project_workflow.py`

```python
"""Integration tests for project creation workflow."""
import pytest
from fairdm.factories import ProjectFactory, UserFactory

@pytest.mark.django_db
def test_project_creation__with_valid_data__creates_project_and_assigns_owner():
    """Test complete project creation workflow."""
    user = UserFactory()

    project = ProjectFactory(owner=user, title="Test Project")

    assert project.pk is not None
    assert project.owner == user
```

## Discovery Patterns

Pytest uses these patterns to discover tests (configured in `pyproject.toml`):

```toml
[tool.pytest.ini_options]
python_files = ["test_*.py"]          # Find test files
python_classes = ["Test*"]            # Find test classes
python_functions = ["test_*"]         # Find test functions
testpaths = ["tests"]                 # Search in tests/ directory
```

This means:

- ✅ `test_models.py` - Discovered
- ✅ `def test_something()` - Discovered
- ✅ `class TestProject` - Discovered
- ❌ `models_test.py` - Not discovered
- ❌ `def check_something()` - Not discovered

## Best Practices

### 1. One Test File Per Source Module

**Good:**

```text
fairdm/core/models.py → tests/unit/fairdm/core/test_models.py
fairdm/core/views.py → tests/unit/fairdm/core/test_views.py
```

**Bad:**

```text
fairdm/core/models.py → tests/unit/fairdm/core/test_all.py
fairdm/core/views.py → tests/unit/fairdm/core/test_all.py
```

### 2. Keep Related Tests Together

If testing a workflow across multiple components, keep tests together:

```text
tests/integration/fairdm/core/
├── test_project_workflow.py       # Project creation, update, delete
├── test_dataset_workflow.py       # Dataset import, export, validation
└── test_sample_measurement.py     # Sample-Measurement relationships
```

### 3. Use Markers for Test Selection

Mark tests with pytest markers for selective execution:

```python
import pytest

@pytest.mark.unit
def test_something_fast():
    ...

@pytest.mark.integration
@pytest.mark.django_db
def test_something_with_database():
    ...

@pytest.mark.slow
def test_something_slow():
    ...
```

Run specific markers:

```bash
poetry run pytest -m unit              # Only unit tests
poetry run pytest -m integration       # Only integration tests
poetry run pytest -m "not slow"        # Exclude slow tests
```

## Common Pitfalls

::::{grid} 1 1 2 2
:gutter: 3

:::{grid-item-card} ❌ Wrong File Location
Placing tests in wrong layer or not mirroring app structure.

**Fix**: Follow `tests/{layer}/{app}/test_{module}.py` pattern.
:::

:::{grid-item-card} ❌ Unclear Test Names
Using generic names like `test_1` or `test_project`.

**Fix**: Use `test_<behavior>__<condition>__<expected>` pattern.
:::

:::{grid-item-card} ❌ Missing Conftest
Duplicating fixtures across test files.

**Fix**: Create conftest.py at appropriate level with shared fixtures.
:::

:::{grid-item-card} ❌ Contract Tests in Unit/
Testing API endpoints in unit test layer.

**Fix**: Move API/schema tests to `tests/contract/`.
:::

::::

## Next Steps

```{seealso}
- Review [Test Layers](test-layers.md) for layer definitions
- Check [Test Quality](test-quality.md) for quality guidelines
- Use [Fixtures & Factories](fixtures.md) for test data
- See [Examples](examples/unit-test-example.md) for annotated examples
```

## References

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-Django Documentation](https://pytest-django.readthedocs.io/)
- [Testing Overview](index.md) - FairDM testing conventions
- [Test Layers](test-layers.md) - Understanding different test types
