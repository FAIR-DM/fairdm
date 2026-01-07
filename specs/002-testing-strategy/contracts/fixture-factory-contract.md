# Fixture Factory Contract

**Version**: 1.0
**Date**: 2026-01-06
**Status**: Active

## Purpose

This contract defines the structure, organization, and usage patterns for test data factories in the FairDM project. Consistent fixture factories enable:

1. **Reusable test data**: Reduce duplication across tests
2. **Maintainability**: Update test data patterns in one location
3. **Readability**: Clear factory names and parameters
4. **Flexibility**: Easy customization for specific test scenarios

## Contract Scope

- **Applies to**: All factory-boy factories in `tests/fixtures/factories.py`
- **Enforced by**: Code review, documentation
- **Violations**: Non-compliant factories may be refactored

---

## Factory Structure

### Base Template

Every factory **MUST** follow this structure:

```python
class {Model}Factory(DjangoModelFactory):
    """
    Factory for creating {Model} test instances.

    Usage:
        # Create with defaults
        obj = {Model}Factory()

        # Override specific fields
        obj = {Model}Factory(field="custom_value")

        # Create batch
        objs = {Model}Factory.create_batch(10)

    Attributes:
        field1 (type): Description of field1
        field2 (type): Description of field2
    """
    class Meta:
        model = "app_label.{Model}"
        django_get_or_create = ("natural_key_field",)  # Optional

    # Field definitions
    field1 = factory.{Strategy}(...)
    field2 = factory.{Strategy}(...)
```

### Rules

1. **MUST** inherit from `DjangoModelFactory`
2. **MUST** include comprehensive docstring with usage examples
3. **MUST** define `Meta.model` using `"app_label.ModelName"` format
4. **SHOULD** use `factory.Faker()` for realistic test data
5. **SHOULD** use `factory.Sequence()` for unique values
6. **SHOULD** use `factory.SubFactory()` for ForeignKey relationships
7. **MAY** use `factory.LazyAttribute()` for computed fields
8. **MAY** use `@factory.post_generation` for M2M relationships or complex setup

---

## Naming Conventions

### Factory Class Names

**Pattern**: `{Model}Factory`

**Rules**:

1. **MUST** match Django model name exactly with `Factory` suffix
2. **MUST** use PascalCase
3. **SHOULD** be singular (matching model name)

**Examples**:

| Django Model | Factory Class Name |
| ------------ | ------------------ |
| `Project`    | `ProjectFactory`   |
| `Dataset`    | `DatasetFactory`   |
| `RockSample` | `RockSampleFactory` |

### Factory File Location

**Location**: `tests/fixtures/factories.py`

**Rules**:

1. All factories **MUST** be defined in `tests/fixtures/factories.py`
2. If file becomes large (>500 lines), **MAY** split into domain modules:
   - `tests/fixtures/factories/core.py` (core models)
   - `tests/fixtures/factories/contrib.py` (contrib models)
   - `tests/fixtures/factories/__init__.py` (imports all)

---

## Field Strategies

### Required Fields

Use `factory.Faker()` for realistic data:

```python
class ProjectFactory(DjangoModelFactory):
    class Meta:
        model = "fairdm_core.Project"

    name = factory.Faker("catch_phrase")
    description = factory.Faker("text", max_nb_chars=200)
    created = factory.Faker("date_time_this_decade", tzinfo=timezone.utc)
```

### Unique Fields

Use `factory.Sequence()` for guaranteed uniqueness:

```python
class UserFactory(DjangoModelFactory):
    class Meta:
        model = "auth.User"

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
```

### ForeignKey Relationships

Use `factory.SubFactory()`:

```python
class DatasetFactory(DjangoModelFactory):
    class Meta:
        model = "fairdm_core.Dataset"

    project = factory.SubFactory(ProjectFactory)  # Creates related Project
    name = factory.Faker("catch_phrase")
```

**Optional relationship** (allow None):

```python
class SampleFactory(DjangoModelFactory):
    class Meta:
        model = "fairdm_core.Sample"

    dataset = factory.SubFactory(DatasetFactory)
    parent_sample = None  # Optional: can be set manually
```

### Choice Fields

Use `factory.Iterator()` or `factory.Faker()`:

```python
class RockSampleFactory(SampleFactory):
    class Meta:
        model = "fairdm_demo.RockSample"

    # Iterator cycles through choices
    rock_type = factory.Iterator(["igneous", "sedimentary", "metamorphic"])

    # Or use Faker if appropriate
    status = factory.Faker("random_element", elements=["draft", "published", "archived"])
```

### Computed Fields

Use `factory.LazyAttribute()`:

```python
class UserFactory(DjangoModelFactory):
    class Meta:
        model = "auth.User"

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    full_name = factory.LazyAttribute(lambda obj: f"{obj.first_name} {obj.last_name}")
```

### ManyToMany Relationships

Use `@factory.post_generation`:

```python
class ProjectFactory(DjangoModelFactory):
    class Meta:
        model = "fairdm_core.Project"

    name = factory.Faker("catch_phrase")

    @factory.post_generation
    def contributors(self, create, extracted, **kwargs):
        """Add contributors to project after creation."""
        if not create:
            return

        if extracted:
            # Use provided contributors
            for contributor in extracted:
                self.contributors.add(contributor)
        else:
            # Create default contributors
            self.contributors.add(UserFactory())
```

---

## Polymorphic Model Factories

FairDM uses polymorphic models (Sample, Measurement). Factories **MUST** support inheritance:

### Base Factory

```python
class SampleFactory(DjangoModelFactory):
    """Base factory for polymorphic Sample model."""
    class Meta:
        model = "fairdm_core.Sample"

    name = factory.Faker("catch_phrase")
    project = factory.SubFactory(ProjectFactory)
    dataset = factory.SubFactory(DatasetFactory)
```

### Child Factory

```python
class RockSampleFactory(SampleFactory):
    """Factory for RockSample (child of Sample)."""
    class Meta:
        model = "fairdm_demo.RockSample"

    # Inherits fields from SampleFactory
    rock_type = factory.Iterator(["igneous", "sedimentary", "metamorphic"])
    collection_date = factory.Faker("date_this_decade")
```

**Rules for polymorphic factories**:

1. Base factory **MUST** target polymorphic parent model
2. Child factories **MUST** inherit from base factory
3. Child factories **MUST** override `Meta.model`
4. Child factories **MAY** override parent fields

---

## Usage Patterns

### Basic Creation

```python
# Create with defaults
project = ProjectFactory()

# Override specific fields
project = ProjectFactory(name="Custom Project Name")

# Override nested fields
project = ProjectFactory(
    name="Custom Project",
    contributors__username="john_doe"  # SubFactory override
)
```

### Batch Creation

```python
# Create multiple instances
projects = ProjectFactory.create_batch(5)

# Create batch with overrides
projects = ProjectFactory.create_batch(5, status="published")
```

### Build Without Saving

```python
# Build instance without database save (for unit tests)
project = ProjectFactory.build()

# Build with overrides
project = ProjectFactory.build(name="Unsaved Project")
```

### Stub (No Database, Minimal Attributes)

```python
# Create stub (no DB save, only explicit attributes)
project = ProjectFactory.stub(name="Stub Project")
```

### Creating Related Objects

```python
# Create dataset with specific project
project = ProjectFactory()
dataset = DatasetFactory(project=project)

# Create dataset with auto-generated project
dataset = DatasetFactory()  # Automatically creates project via SubFactory
```

---

## pytest Fixture Integration

Factories **SHOULD** be wrapped in pytest fixtures for convenience:

```python
# tests/fixtures/pytest_fixtures.py
import pytest
from .factories import ProjectFactory, DatasetFactory

@pytest.fixture
def project():
    """Fixture providing a standard test project."""
    return ProjectFactory()

@pytest.fixture
def project_with_datasets():
    """Fixture providing a project with 3 datasets."""
    project = ProjectFactory()
    DatasetFactory.create_batch(3, project=project)
    return project

@pytest.fixture
def authenticated_user():
    """Fixture providing an authenticated user."""
    user = UserFactory()
    user.set_password("testpass123")
    user.save()
    return user
```

**Usage in tests**:

```python
@pytest.mark.django_db
def test_project_creation(project):
    """Test using project fixture."""
    assert project.id is not None
    assert project.name

@pytest.mark.django_db
def test_dataset_count(project_with_datasets):
    """Test using composed fixture."""
    assert project_with_datasets.datasets.count() == 3
```

---

## Docstring Requirements

Every factory **MUST** include docstring documenting:

1. **Purpose**: What model the factory creates
2. **Usage examples**: Basic creation, overrides, batch creation
3. **Key attributes**: Description of important fields
4. **Special behaviors**: Post-generation hooks, computed fields

### Template

```python
class {Model}Factory(DjangoModelFactory):
    """
    Factory for creating {Model} test instances.

    This factory provides [brief description of what makes this factory special,
    if any unique behavior exists].

    Usage:
        # Basic creation
        obj = {Model}Factory()

        # Override fields
        obj = {Model}Factory(field="value")

        # Create batch
        objs = {Model}Factory.create_batch(10)

        # Build without saving
        obj = {Model}Factory.build()

    Attributes:
        field1 (type): Description of field1 and default behavior
        field2 (type): Description of field2 and default behavior
        related_field (RelatedModel): Created via SubFactory, can override

    Post-generation:
        hook_name: Description of post-generation behavior

    Example:
        >>> project = ProjectFactory(name="Research Project")
        >>> assert project.name == "Research Project"
    """
    pass
```

---

## Anti-Patterns

### ❌ Don't: Hardcode values

```python
class ProjectFactory(DjangoModelFactory):
    name = "Test Project"  # BAD: Every project has same name
```

### ✅ Do: Use Faker or Sequence

```python
class ProjectFactory(DjangoModelFactory):
    name = factory.Faker("catch_phrase")  # GOOD: Unique, realistic names
```

### ❌ Don't: Create unnecessary related objects

```python
@factory.post_generation
def datasets(self, create, extracted, **kwargs):
    # BAD: Creates datasets by default, even if not needed
    DatasetFactory.create_batch(3, project=self)
```

### ✅ Do: Create related objects only when requested

```python
@factory.post_generation
def datasets(self, create, extracted, **kwargs):
    # GOOD: Only creates datasets if explicitly requested
    if extracted:
        for dataset in extracted:
            dataset.project = self
            dataset.save()
```

### ❌ Don't: Mix factory-boy and manual creation

```python
def test_example():
    project = ProjectFactory()
    dataset = Dataset.objects.create(  # BAD: Manual creation
        project=project,
        name="Test Dataset"
    )
```

### ✅ Do: Use factories consistently

```python
def test_example():
    project = ProjectFactory()
    dataset = DatasetFactory(project=project)  # GOOD: Consistent factory use
```

---

## Version History

| Version | Date       | Changes                          |
| ------- | ---------- | -------------------------------- |
| 1.0     | 2026-01-06 | Initial contract definition      |

---

**Related Contracts**:

- [Test Naming Contract](./test-naming-contract.md)
- [Test Organization Contract](./test-organization-contract.md)
