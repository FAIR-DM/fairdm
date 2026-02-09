# Fixture Factory Example

This example demonstrates complete factory-boy usage patterns for creating test data in FairDM.

```{contents}
:local:
:depth: 2
```

## Overview

This guide shows how to:

- Create factories for Django models
- Use SubFactory for relationships
- Override default values
- Build vs create (in-memory vs database)
- Use factories in tests

## Complete Factory Example

### Step 1: Define Factories

**File**: `tests/fixtures/factories.py`

```python
"""
Factory-boy factories for creating test data.

All factories follow the pattern:
1. Inherit from factory.django.DjangoModelFactory
2. Set Meta.model to the Django model
3. Define sensible defaults for all fields
4. Use factory.Sequence for unique values
5. Use factory.SubFactory for relationships
6. Include comprehensive docstrings
"""
import factory
from django.contrib.auth import get_user_model
from fairdm.core.models import Project, Dataset

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    """
    Factory for creating User instances.

    Default behavior:
    - Generates unique usernames (user0, user1, ...)
    - Generates email from username
    - Sets default first/last name

    Usage:
        # Create with defaults
        user = UserFactory()

        # Override specific fields
        user = UserFactory(username="alice", email="alice@example.com")

        # Build without saving to database (for unit tests)
        user = UserFactory.build()

        # Create multiple users
        users = UserFactory.create_batch(5)

    Examples:
        >>> user = UserFactory()
        >>> print(user.username)
        'user0'
        >>> print(user.email)
        'user0@example.com'
    """

    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = "Test"
    last_name = "User"


class ProjectFactory(factory.django.DjangoModelFactory):
    """
    Factory for creating Project instances.

    Default behavior:
    - Creates a unique owner (UserFactory)
    - Generates unique title and slug
    - Sets visibility to PUBLIC

    Usage:
        # Create with defaults (automatically creates owner)
        project = ProjectFactory()

        # Use existing user
        user = UserFactory()
        project = ProjectFactory(owner=user)

        # Override fields
        project = ProjectFactory(
            title="Custom Project",
            visibility=Project.Visibility.PRIVATE
        )

        # Build without saving
        project = ProjectFactory.build()

    Examples:
        >>> project = ProjectFactory()
        >>> print(project.title)
        'Project 0'
        >>> print(project.owner.username)
        'user0'
        >>> assert project.pk is not None
    """

    class Meta:
        model = Project

    owner = factory.SubFactory(UserFactory)
    title = factory.Sequence(lambda n: f"Project {n}")
    slug = factory.Sequence(lambda n: f"project-{n}")
    description = factory.LazyAttribute(
        lambda obj: f"Description for {obj.title}"
    )
    visibility = Project.Visibility.PUBLIC


class DatasetFactory(factory.django.DjangoModelFactory):
    """
    Factory for creating Dataset instances.

    Default behavior:
    - Creates parent Project (with owner)
    - Generates unique title

    Usage:
        # Create with defaults (creates project and owner)
        dataset = DatasetFactory()

        # Use existing project
        project = ProjectFactory()
        dataset = DatasetFactory(project=project)

        # Create multiple datasets for one project
        project = ProjectFactory()
        datasets = DatasetFactory.create_batch(3, project=project)

    Examples:
        >>> dataset = DatasetFactory()
        >>> print(dataset.title)
        'Dataset 0'
        >>> assert dataset.project is not None
        >>> assert dataset.project.owner is not None
    """

    class Meta:
        model = Dataset

    project = factory.SubFactory(ProjectFactory)
    title = factory.Sequence(lambda n: f"Dataset {n}")
```

### Step 2: Use Factories in Tests

#### Example 1: Simple Creation

```python
"""Test using factory for simple object creation."""
import pytest
from fairdm.factories import UserFactory, ProjectFactory

@pytest.mark.django_db
def test_project_creation__with_factory__creates_project():
    """Test that factory creates project with all required fields."""
    # Act: Create project using factory
    project = ProjectFactory()

    # Assert: Project created with defaults
    assert project.pk is not None
    assert project.title
    assert project.slug
    assert project.owner is not None

    # Assert: Database state
    assert Project.objects.count() == 1
```

#### Example 2: Override Defaults

```python
"""Test overriding factory defaults."""
import pytest
from fairdm.factories import ProjectFactory, UserFactory

@pytest.mark.django_db
def test_project_creation__with_custom_values__uses_custom_values():
    """Test that factory allows custom field values."""
    # Arrange: Create user explicitly
    user = UserFactory(username="alice")

    # Act: Create project with custom values
    project = ProjectFactory(
        owner=user,
        title="My Custom Project",
        slug="custom-project",
        visibility=Project.Visibility.PRIVATE
    )

    # Assert: Custom values applied
    assert project.owner == user
    assert project.title == "My Custom Project"
    assert project.slug == "custom-project"
    assert project.visibility == Project.Visibility.PRIVATE
```

#### Example 3: Relationships

```python
"""Test creating objects with relationships."""
import pytest
from fairdm.factories import ProjectFactory, DatasetFactory

@pytest.mark.django_db
def test_project_with_datasets__creates_related_objects():
    """Test creating project with multiple datasets."""
    # Arrange: Create project
    project = ProjectFactory()

    # Act: Create datasets for project
    dataset1 = DatasetFactory(project=project, title="Dataset A")
    dataset2 = DatasetFactory(project=project, title="Dataset B")
    dataset3 = DatasetFactory(project=project, title="Dataset C")

    # Assert: Relationships established
    assert project.datasets.count() == 3
    assert dataset1.project == project
    assert dataset2.project == project
    assert dataset3.project == project
```

#### Example 4: Batch Creation

```python
"""Test creating multiple objects at once."""
import pytest
from fairdm.factories import ProjectFactory, DatasetFactory

@pytest.mark.django_db
def test_batch_creation__creates_multiple_objects():
    """Test batch creation of objects."""
    # Act: Create 5 projects at once
    projects = ProjectFactory.create_batch(5)

    # Assert: Correct number created
    assert len(projects) == 5
    assert Project.objects.count() == 5

    # Assert: Each has unique values
    titles = [p.title for p in projects]
    assert len(set(titles)) == 5  # All unique


@pytest.mark.django_db
def test_batch_creation__with_relationship__shares_parent():
    """Test batch creation with shared relationship."""
    # Arrange: Create project
    project = ProjectFactory()

    # Act: Create multiple datasets for same project
    datasets = DatasetFactory.create_batch(10, project=project)

    # Assert: All datasets belong to same project
    assert len(datasets) == 10
    assert all(d.project == project for d in datasets)
    assert project.datasets.count() == 10
```

#### Example 5: Build vs Create (Unit Tests)

```python
"""Test build() for unit tests without database."""
from fairdm.factories import ProjectFactory

def test_project_slug_generation__with_build__no_database():
    """
    Test slug generation without database access.

    This is a UNIT test - no @pytest.mark.django_db needed.
    """
    # Act: Build in-memory project
    project = ProjectFactory.build(title="Test Project")

    # Assert: Object created but not saved
    assert project.pk is None  # Not in database
    assert project.title == "Test Project"
    assert project.slug  # Has slug value

    # Can test methods that don't need database
    url = project.get_absolute_url()
    assert "/projects/" in url
```

## Advanced Patterns

### Pattern 1: LazyAttribute with Logic

```python
class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project

    title = factory.Sequence(lambda n: f"Project {n}")

    # Compute description from title
    description = factory.LazyAttribute(
        lambda obj: f"This is a research project about {obj.title.lower()}"
    )

    # Compute slug from title
    slug = factory.LazyAttribute(
        lambda obj: slugify(obj.title)
    )
```

### Pattern 2: Conditional Fields

```python
class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project

    visibility = Project.Visibility.PUBLIC

    # Only set embargo_date if visibility is EMBARGO
    embargo_date = factory.Maybe(
        'is_embargoed',
        yes_declaration=factory.LazyFunction(
            lambda: timezone.now() + timedelta(days=30)
        ),
        no_declaration=None
    )

    class Params:
        is_embargoed = factory.Trait(
            visibility=Project.Visibility.EMBARGO
        )
```

Usage:

```python
public_project = ProjectFactory()  # No embargo
embargoed_project = ProjectFactory(is_embargoed=True)  # Has embargo_date
```

### Pattern 3: PostGeneration Hooks

```python
class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project

    @factory.post_generation
    def with_datasets(obj, create, extracted, **kwargs):
        """
        Create datasets after project creation.

        Usage:
            # Create project with 3 datasets
            project = ProjectFactory(with_datasets=3)

            # Create project with custom datasets
            project = ProjectFactory(with_datasets=[
                {'title': 'Dataset A'},
                {'title': 'Dataset B'},
            ])
        """
        if not create:
            return

        if extracted:
            if isinstance(extracted, int):
                DatasetFactory.create_batch(extracted, project=obj)
            elif isinstance(extracted, list):
                for dataset_data in extracted:
                    DatasetFactory(project=obj, **dataset_data)
```

## Common Patterns in Tests

### Pattern 1: Setup with Factory

```python
@pytest.mark.django_db
def test_project_update__updates_database():
    # Arrange: Create test data
    project = ProjectFactory(title="Original")

    # Act: Update
    project.title = "Updated"
    project.save()

    # Assert: Change persisted
    project.refresh_from_db()
    assert project.title == "Updated"
```

### Pattern 2: Multiple Related Objects

```python
@pytest.mark.django_db
def test_user_can_have_multiple_projects():
    # Arrange: Create user and projects
    user = UserFactory()
    projects = ProjectFactory.create_batch(3, owner=user)

    # Assert: All projects belong to user
    assert user.projects.count() == 3
    assert all(p.owner == user for p in projects)
```

### Pattern 3: Testing Queries

```python
@pytest.mark.django_db
def test_project_queryset__filters_by_owner():
    # Arrange: Create projects for different users
    user1 = UserFactory(username="alice")
    user2 = UserFactory(username="bob")

    alice_projects = ProjectFactory.create_batch(2, owner=user1)
    bob_projects = ProjectFactory.create_batch(3, owner=user2)

    # Act: Query by owner
    result = Project.objects.filter(owner=user1)

    # Assert: Only alice's projects returned
    assert result.count() == 2
    assert all(p in alice_projects for p in result)
```

## Best Practices

### 1. ✅ One Factory Per Model

```python
# Good: One factory per model
class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project
```

### 2. ✅ Sensible Defaults

```python
# Good: All fields have defaults
class ProjectFactory(factory.django.DjangoModelFactory):
    title = factory.Sequence(lambda n: f"Project {n}")
    slug = factory.Sequence(lambda n: f"project-{n}")
    owner = factory.SubFactory(UserFactory)
```

### 3. ✅ Comprehensive Docstrings

```python
# Good: Explains usage and examples
class ProjectFactory(factory.django.DjangoModelFactory):
    """
    Factory for Project instances.

    Usage:
        project = ProjectFactory()
        project = ProjectFactory(title="Custom")

    Examples:
        >>> p = ProjectFactory()
        >>> assert p.title
    """
```

### 4. ✅ Use build() in Unit Tests

```python
# Good: No database in unit tests
def test_url_generation():
    project = ProjectFactory.build()  # In-memory only
    assert project.get_absolute_url()
```

## Next Steps

```{seealso}
- Review [Fixtures & Factories Guide](../fixtures.md) for more patterns
- Check [Database Strategy](../database-strategy.md) for transaction management
- See [Fixture Factory Contract](../../../../specs/004-testing-strategy-fixtures/contracts/fixture-factory-contract.md) for standards
```

## References

- [factory-boy Documentation](https://factoryboy.readthedocs.io/)
- [factory-boy Recipes](https://factoryboy.readthedocs.io/en/stable/recipes.html)
