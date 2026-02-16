# Integration Test Example

This example demonstrates a complete integration test following FairDM conventions.

```{contents}
:local:
:depth: 2
```

## Overview

Integration tests validate **cross-component workflows** with the **database**. This example shows:

- Database access with `@pytest.mark.django_db`
- Factory-boy usage for test data
- Testing ORM relationships
- Workflow validation

## Source Code

**File**: `fairdm/core/models.py`

```python
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Project(models.Model):
    """A research project containing datasets."""

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="projects")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]


class Dataset(models.Model):
    """A dataset within a project."""

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="datasets")
    title = models.CharField(max_length=200)

    def get_sample_count(self):
        """Return the number of samples in this dataset."""
        return self.samples.count()
```

## Integration Test

**File**: `tests/integration/fairdm/core/test_project_workflow.py`

```python
"""Integration tests for project creation and management workflows."""
import pytest
from django.contrib.auth import get_user_model
from fairdm.core.models import Project, Dataset
from fairdm.factories import UserFactory, ProjectFactory, DatasetFactory

User = get_user_model()


# Test 1: Project creation workflow
@pytest.mark.django_db
def test_project_creation__with_valid_data__creates_project_and_assigns_owner():
    """
    Test complete project creation workflow.

    Validates that creating a project:
    - Persists to database
    - Assigns owner relationship correctly
    - Sets auto-generated fields (pk, created)
    """
    # Arrange: Create user
    user = UserFactory(username="testuser", email="test@example.com")

    # Act: Create project
    project = ProjectFactory(
        owner=user,
        title="Test Project",
        slug="test-project"
    )

    # Assert: Verify persistence
    assert project.pk is not None
    assert project.owner == user
    assert project.title == "Test Project"
    assert project.created is not None

    # Assert: Verify database state
    assert Project.objects.filter(owner=user).count() == 1


# Test 2: Related objects cascade
@pytest.mark.django_db
def test_project_deletion__with_related_datasets__cascades_to_datasets():
    """
    Test cascade deletion from Project to Dataset.

    When a project is deleted, all related datasets should
    also be deleted due to CASCADE on foreign key.
    """
    # Arrange: Create project with datasets
    project = ProjectFactory()
    dataset1 = DatasetFactory(project=project, title="Dataset 1")
    dataset2 = DatasetFactory(project=project, title="Dataset 2")

    initial_dataset_count = Dataset.objects.count()
    assert initial_dataset_count == 2

    # Act: Delete project
    project.delete()

    # Assert: Datasets also deleted
    assert Dataset.objects.count() == 0
    assert not Dataset.objects.filter(pk=dataset1.pk).exists()
    assert not Dataset.objects.filter(pk=dataset2.pk).exists()


# Test 3: Reverse relationship query
@pytest.mark.django_db
def test_user_projects_query__with_multiple_projects__returns_all_projects():
    """
    Test reverse relationship from User to Projects.

    Validates that related_name="projects" works correctly
    and returns projects ordered by creation date.
    """
    # Arrange: Create user with multiple projects
    user = UserFactory()
    project1 = ProjectFactory(owner=user, title="Project A")
    project2 = ProjectFactory(owner=user, title="Project B")
    project3 = ProjectFactory(owner=user, title="Project C")

    # Create projects for different user (should not appear)
    other_user = UserFactory()
    ProjectFactory(owner=other_user)

    # Act: Query user's projects
    user_projects = user.projects.all()

    # Assert: Correct projects returned
    assert user_projects.count() == 3
    assert project1 in user_projects
    assert project2 in user_projects
    assert project3 in user_projects

    # Assert: Correct ordering (most recent first)
    assert list(user_projects) == [project3, project2, project1]


# Test 4: Method with database query
@pytest.mark.django_db
def test_get_sample_count__with_multiple_samples__returns_correct_count():
    """
    Test dataset sample counting method.

    Validates that get_sample_count() correctly queries
    the database for related samples.
    """
    # Arrange: Create dataset with samples
    dataset = DatasetFactory()
    # Assuming SampleFactory exists (simplified for example)
    from fairdm.factories import SampleFactory
    SampleFactory(dataset=dataset)
    SampleFactory(dataset=dataset)
    SampleFactory(dataset=dataset)

    # Act: Get sample count
    count = dataset.get_sample_count()

    # Assert: Correct count
    assert count == 3
```

## Explanation

### File Location

```text
tests/integration/fairdm/core/test_project_workflow.py
└────┬──────┘ └───┬───┘ └─┬─┘ └──────────┬──────────┘
     │            │       │               └─ Workflow: project operations
     │            │       └─────────────────── App: fairdm.core
     │            └─────────────────────────── Django package: fairdm
     └──────────────────────────────────────── Test layer: integration
```

**Why this location:**

- Integration test layer (uses database)
- Mirrors source app: `fairdm/core/`
- Groups related workflow tests together

### Database Marker

Every integration test MUST use `@pytest.mark.django_db`:

```python
@pytest.mark.django_db
def test_something_with_database():
    # This marker enables database access
    project = ProjectFactory()  # ✅ Works
```

Without the marker:

```python
def test_something_with_database():
    project = ProjectFactory()  # ❌ Fails: no database access
```

### Factory-Boy Usage

Integration tests use **factories** instead of **fixtures**:

```python
# ✅ Good: Factory creates objects as needed
@pytest.mark.django_db
def test_project_creation():
    user = UserFactory()
    project = ProjectFactory(owner=user)

# ❌ Bad: Fixture files create brittle dependencies
# Don't use: fixtures/test_data.json
```

**Why factories?**

- **Explicit**: Test shows exactly what data it needs
- **Flexible**: Override only the fields you care about
- **Maintainable**: Changes to models don't break all tests

### Transaction Rollback

Each integration test runs in a **transaction** that is **rolled back** after the test:

```python
@pytest.mark.django_db
def test_create_project():
    project = ProjectFactory()
    assert project.pk is not None
    # Transaction rolls back here - project deleted from database
```

**Benefits:**

- Tests are **isolated** (don't affect each other)
- Database remains **clean** between tests
- Tests can run in **any order**

## Why This is an Integration Test

✅ **Database access**: Uses `@pytest.mark.django_db`
✅ **Cross-component**: Tests Project, User, Dataset relationships
✅ **Realistic workflows**: Complete CRUD operations
✅ **Medium speed**: Runs in < 1s per test

❌ **Not an integration test if it:**

- Doesn't touch the database (use unit test)
- Tests API schema only (use contract test)
- Takes > 5 seconds (optimize or split)

## Running This Test

### Run all integration tests

```bash
poetry run pytest tests/integration/
```

### Run this specific file

```bash
poetry run pytest tests/integration/fairdm/core/test_project_workflow.py
```

### Run a specific test

```bash
poetry run pytest tests/integration/fairdm/core/test_project_workflow.py::test_project_creation__with_valid_data__creates_project_and_assigns_owner
```

### Run with database reuse (faster)

```bash
poetry run pytest tests/integration/ --reuse-db
```

## Best Practices Demonstrated

### 1. Use Factories

```python
# ✅ Good: Factory creates realistic data
user = UserFactory()
project = ProjectFactory(owner=user)

# ❌ Bad: Manual object creation
user = User.objects.create(username="test", email="test@example.com")
project = Project.objects.create(owner=user, title="Test", slug="test")
```

### 2. Test Complete Workflows

```python
# ✅ Good: Complete workflow
@pytest.mark.django_db
def test_project_deletion__with_related_datasets__cascades_to_datasets():
    project = ProjectFactory()
    DatasetFactory(project=project)
    project.delete()
    assert Dataset.objects.count() == 0

# ❌ Bad: Testing ORM internals
def test_project_has_cascade():
    # Don't test that Django's CASCADE works
    ...
```

### 3. Verify Database State

```python
# ✅ Good: Verify actual database state
@pytest.mark.django_db
def test_project_creation():
    project = ProjectFactory()
    assert Project.objects.filter(pk=project.pk).exists()

# ❌ Bad: Only check in-memory object
@pytest.mark.django_db
def test_project_creation():
    project = ProjectFactory()
    assert project.pk  # Doesn't verify persistence
```

### 4. Explicit Assertions

```python
# ✅ Good: Multiple explicit assertions
assert project.pk is not None
assert project.owner == user
assert project.created is not None

# ❌ Bad: Single assertion for complex behavior
assert project  # What are we actually testing?
```

## Common Patterns

### Testing Relationships

```python
@pytest.mark.django_db
def test_reverse_relationship():
    user = UserFactory()
    ProjectFactory(owner=user, title="Project 1")
    ProjectFactory(owner=user, title="Project 2")

    # Access reverse relationship
    assert user.projects.count() == 2
```

### Testing Cascade Deletion

```python
@pytest.mark.django_db
def test_cascade_deletion():
    parent = ParentFactory()
    child = ChildFactory(parent=parent)

    parent.delete()

    assert not Child.objects.filter(pk=child.pk).exists()
```

### Testing Ordering

```python
@pytest.mark.django_db
def test_ordering():
    obj1 = ModelFactory(created="2025-01-01")
    obj2 = ModelFactory(created="2025-01-02")
    obj3 = ModelFactory(created="2025-01-03")

    # Verify Meta.ordering
    assert list(Model.objects.all()) == [obj3, obj2, obj1]
```

## Common Mistakes

::::{grid} 1 1 2 2
:gutter: 3

:::{grid-item-card} ❌ Missing @pytest.mark.django_db
Forgetting marker causes test failure.

**Fix**: Always add `@pytest.mark.django_db` for database tests.
:::

:::{grid-item-card} ❌ Shared Test Data
Tests depend on specific fixture data.

**Fix**: Use factories to create data per test.
:::

:::{grid-item-card} ❌ Testing Implementation
Verifying Django's ORM works correctly.

**Fix**: Test your business logic, not Django internals.
:::

:::{grid-item-card} ❌ Slow Tests
Integration tests taking > 5 seconds.

**Fix**: Use `--reuse-db`, optimize queries, or split tests.
:::

::::

## Next Steps

```{seealso}
- Compare with [Unit Test Example](unit-test-example.md)
- Review [Contract Test Example](contract-test-example.md)
- Learn about [Fixtures & Factories](../fixtures.md)
- Read [Database Strategy](../database-strategy.md)
```

## References

- [Test Layers: Integration Tests](../test-layers.md#integration-tests)
- [Test Quality: Reliable Tests](../test-quality.md#reliable-tests)
- [Test Organization](../test-organization.md)
