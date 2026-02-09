# Fixtures & Factories

Test fixtures provide reusable test data and setup code. FairDM uses **factory-boy** for complex objects and **pytest fixtures** for composition and lifecycle management.

```{contents}
:local:
:depth: 2
```

## Overview

FairDM uses two complementary approaches for test data:

::::{grid} 1 1 2 2
:gutter: 3

:::{grid-item-card} {octicon}`package` Factory-Boy
**For creating model instances**

- Database objects with sensible defaults
- Easy field overrides
- Support for relationships and inheritance
- Located in `tests/fixtures/factories.py`
:::

:::{grid-item-card} {octicon}`tools` Pytest Fixtures
**For composition and lifecycle**

- Combine factories into scenarios
- Manage setup/teardown
- Scope control (function, module, session)
- Located in `conftest.py` files
:::

::::

## Factory-Boy Basics

### What is Factory-Boy?

Factory-boy generates test objects with sensible defaults, allowing selective field overrides.

**Without factory-boy:**

```python
# Repetitive, brittle, hard to maintain
@pytest.mark.django_db
def test_something():
    user = User.objects.create(
        username="testuser",
        email="test@example.com",
        first_name="Test",
        last_name="User"
    )
    project = Project.objects.create(
        owner=user,
        title="Test Project",
        slug="test-project",
        description="Test description"
    )
```

**With factory-boy:**

```python
# Concise, flexible, maintainable
@pytest.mark.django_db
def test_something():
    project = ProjectFactory()  # All fields have sensible defaults
```

### Creating Your First Factory

**Step 1: Define the factory in `tests/fixtures/factories.py`**

```python
import factory
from django.contrib.auth import get_user_model

User = get_user_model()

class UserFactory(factory.django.DjangoModelFactory):
    """
    Factory for creating User instances.

    Usage:
        # Create with defaults
        user = UserFactory()

        # Override specific fields
        user = UserFactory(username="custom_user")

        # Build without saving to database
        user = UserFactory.build()
    """

    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = "Test"
    last_name = "User"
```

**Step 2: Use the factory in tests**

```python
from fairdm.factories import UserFactory

@pytest.mark.django_db
def test_user_creation():
    user = UserFactory(username="alice")
    assert user.username == "alice"
    assert user.email == "alice@example.com"
```

## Factory Patterns

### Pattern 1: Sequences

Generate unique values:

```python
class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project

    title = factory.Sequence(lambda n: f"Project {n}")
    slug = factory.Sequence(lambda n: f"project-{n}")
```

Usage:

```python
p1 = ProjectFactory()  # title="Project 0", slug="project-0"
p2 = ProjectFactory()  # title="Project 1", slug="project-1"
```

### Pattern 2: LazyAttribute

Compute field from other fields:

```python
class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
```

### Pattern 3: SubFactory (ForeignKey)

Create related objects automatically:

```python
class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project

    owner = factory.SubFactory(UserFactory)
    title = "Default Project"
    slug = factory.Sequence(lambda n: f"project-{n}")
```

Usage:

```python
# Automatically creates User
project = ProjectFactory()
assert project.owner is not None

# Use existing user
user = UserFactory()
project = ProjectFactory(owner=user)
```

### Pattern 4: RelatedFactory (Reverse ForeignKey)

Create related objects on the "many" side:

```python
class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project

    owner = factory.SubFactory(UserFactory)

    # Automatically create 3 datasets
    dataset1 = factory.RelatedFactory(
        'fairdm.factories.DatasetFactory',
        factory_related_name='project'
    )
    dataset2 = factory.RelatedFactory(
        'fairdm.factories.DatasetFactory',
        factory_related_name='project'
    )
    dataset3 = factory.RelatedFactory(
        'fairdm.factories.DatasetFactory',
        factory_related_name='project'
    )
```

### Pattern 5: Traits

Create variants with different characteristics:

```python
class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project

    title = "Default Project"
    visibility = Project.Visibility.PUBLIC

    class Params:
        private = factory.Trait(
            visibility=Project.Visibility.PRIVATE
        )
        with_datasets = factory.Trait(
            dataset1=factory.RelatedFactory(DatasetFactory, 'project'),
            dataset2=factory.RelatedFactory(DatasetFactory, 'project'),
        )
```

Usage:

```python
public_project = ProjectFactory()
private_project = ProjectFactory(private=True)
project_with_data = ProjectFactory(with_datasets=True)
```

### Pattern 6: Build vs Create

Control database persistence:

```python
# Create: Saves to database
user = UserFactory()  # user.pk is set
user = UserFactory.create()  # Explicit

# Build: In-memory only (for unit tests)
user = UserFactory.build()  # user.pk is None
```

**When to use build:**

- Unit tests that don't need database
- Testing object initialization
- Faster test execution

**When to use create:**

- Integration tests
- Testing database constraints
- Testing relationships

## Polymorphic Factories

FairDM uses polymorphic models for Samples and Measurements. Factory-boy supports this:

### Base Polymorphic Factory

```python
from fairdm.core.models import Sample

class SampleFactory(factory.django.DjangoModelFactory):
    """
    Base factory for Sample model.

    Use child factories (RockSampleFactory, etc.) for specific types.
    """

    class Meta:
        model = Sample

    dataset = factory.SubFactory(DatasetFactory)
    name = factory.Sequence(lambda n: f"Sample {n}")
```

### Child Factory with Inheritance

```python
from fairdm.factories import SampleFactory

class RockSampleFactory(SampleFactory):
    """
    Factory for RockSample (inherits from Sample).

    Usage:
        rock = RockSampleFactory(rock_type="Granite")
    """

    class Meta:
        model = RockSample

    # RockSample-specific fields
    rock_type = "Igneous"
    mineral_composition = "Quartz, Feldspar"
```

Usage:

```python
@pytest.mark.django_db
def test_polymorphic_sample():
    rock = RockSampleFactory(rock_type="Granite")

    # Can query as Sample
    assert Sample.objects.count() == 1

    # Can query as RockSample
    assert RockSample.objects.count() == 1

    # Polymorphic query returns correct type
    sample = Sample.objects.first()
    assert isinstance(sample, RockSample)
```

## Pytest Fixtures

Use pytest fixtures to **compose factories** into reusable scenarios.

### Simple Fixture

```python
# tests/conftest.py
import pytest
from fairdm.factories import UserFactory

@pytest.fixture
def user():
    """Create a test user."""
    return UserFactory()
```

### Composed Fixture

```python
# tests/conftest.py
import pytest
from fairdm.factories import ProjectFactory, DatasetFactory

@pytest.fixture
def project_with_datasets():
    """
    Create a project with 3 datasets.

    Returns tuple: (project, [dataset1, dataset2, dataset3])
    """
    project = ProjectFactory()
    datasets = DatasetFactory.create_batch(3, project=project)
    return project, datasets
```

Usage:

```python
@pytest.mark.django_db
def test_something(project_with_datasets):
    project, datasets = project_with_datasets
    assert project.datasets.count() == 3
```

### Fixture Scopes

Control when fixtures are created:

```python
# Function scope (default): New instance per test
@pytest.fixture
def user():
    return UserFactory()

# Module scope: Shared across tests in one file
@pytest.fixture(scope="module")
def shared_user():
    return UserFactory()

# Session scope: Shared across entire test run
@pytest.fixture(scope="session")
def reference_data():
    # Load reference data once
    return load_reference_vocabularies()
```

## Best Practices

### 1. Factories in `tests/fixtures/factories.py`

```text
tests/fixtures/
├── __init__.py
├── factories.py           # All factory-boy factories
└── pytest_fixtures.py     # Complex pytest fixtures
```

### 2. Comprehensive Docstrings

```python
class ProjectFactory(factory.django.DjangoModelFactory):
    """
    Factory for creating Project instances.

    Default behavior:
    - Creates a unique owner (UserFactory)
    - Generates unique title and slug
    - Sets visibility to PUBLIC

    Usage:
        # Create with defaults
        project = ProjectFactory()

        # Override fields
        project = ProjectFactory(title="Custom Title")

        # Use existing user
        user = UserFactory()
        project = ProjectFactory(owner=user)

        # Build without saving
        project = ProjectFactory.build()
    """
    ...
```

### 3. Sensible Defaults

```python
# ✅ Good: Sensible defaults, easy to override
class ProjectFactory(factory.django.DjangoModelFactory):
    title = factory.Sequence(lambda n: f"Project {n}")
    visibility = Project.Visibility.PUBLIC

# ❌ Bad: No defaults, requires manual setup
class ProjectFactory(factory.django.DjangoModelFactory):
    pass  # All fields must be provided
```

### 4. Explicit Over Implicit

```python
# ✅ Good: Explicit relationships
@pytest.mark.django_db
def test_project_with_datasets():
    project = ProjectFactory()
    datasets = DatasetFactory.create_batch(3, project=project)

# ❌ Bad: Hidden RelatedFactory magic
@pytest.mark.django_db
def test_project_with_datasets():
    project = ProjectFactory(with_datasets=True)  # What datasets? How many?
```

## Common Pitfalls

::::{grid} 1 1 2 2
:gutter: 3

:::{grid-item-card} ❌ Forgetting @pytest.mark.django_db
Factories that call `.create()` need database access.

**Fix**: Add `@pytest.mark.django_db` decorator to test.
:::

:::{grid-item-card} ❌ Hard-coded Values
Using same value for unique fields causes conflicts.

**Fix**: Use `factory.Sequence` for unique values.
:::

:::{grid-item-card} ❌ Over-complicated Factories
Too many RelatedFactory or Traits makes tests confusing.

**Fix**: Keep factories simple, compose in pytest fixtures.
:::

:::{grid-item-card} ❌ Not Using build() in Unit Tests
Creating database objects in unit tests slows them down.

**Fix**: Use `.build()` for in-memory objects in unit tests.
:::

::::

## Next Steps

```{seealso}
- Review [Database Strategy](database-strategy.md) for transaction management in integration tests
- See [Fixture Factory Example](examples/fixture-factory-example.md) for complete working examples
- Check [Fixture Factory Contract](../../../specs/004-testing-strategy-fixtures/contracts/fixture-factory-contract.md) for factory standards
- Read [Test Layers](test-layers.md) to understand when to use `.build()` vs `.create()`
- Learn [Running Tests](running-tests.md) CLI options for fixture-related debugging
```

## References

- [factory-boy Documentation](https://factoryboy.readthedocs.io/)
- [pytest Fixtures Documentation](https://docs.pytest.org/en/stable/fixture.html)
- [django-polymorphic with factory-boy](https://django-polymorphic.readthedocs.io/en/stable/)
