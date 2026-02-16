# Testing Portal Projects with FairDM Factories

This guide explains how to use FairDM's factory-boy factories in your own research data portal project. If you're building a portal using FairDM, you can import and reuse FairDM's test factories to simplify your test development.

:::{seealso}
**For FairDM Contributors**: If you're contributing to the FairDM framework itself, see [Testing Strategy](../contributing/testing/index.md) instead.
:::

## Why Use FairDM Factories?

When building a portal with FairDM, your custom features often depend on FairDM's core models (Projects, Datasets, Samples, Measurements). Rather than manually creating these objects in every test, you can import FairDM's factories:

**Benefits**:

- ✅ **No duplication**: Reuse FairDM's tested factory logic
- ✅ **Sensible defaults**: All required fields pre-configured
- ✅ **Easy customization**: Override specific fields for your tests
- ✅ **Consistent data**: Same patterns across portal and framework tests

## Installation

Add FairDM as a development dependency to your portal project:

```bash
# Using Poetry (recommended)
poetry add --group dev fairdm

# Using pip
pip install fairdm
```

This makes FairDM's factories available in your test suite without including them in production.

## Basic Usage

### Importing Factories

All FairDM factories are available from the convenient `fairdm.factories` module:

```python
# In your portal project's test file
from fairdm.factories import UserFactory, ProjectFactory, DatasetFactory
```

### Creating Test Data

FairDM factories follow an **opt-in pattern** for creating related metadata objects (descriptions, dates). By default, factories create only the core object without any descriptions or dates.

**Create with defaults (no metadata)**:

```python
import pytest
from fairdm.factories import ProjectFactory

@pytest.mark.django_db
def test_my_portal_feature():
    # Creates project with required fields only (no descriptions/dates)
    project = ProjectFactory()

    assert project.pk is not None
    assert project.owner is not None
    assert project.name  # Auto-generated name
    # No descriptions or dates created
    assert project.descriptions.count() == 0
    assert project.dates.count() == 0
```

**Create with metadata (opt-in)**:

```python
@pytest.mark.django_db
def test_project_with_metadata():
    # Explicitly request descriptions and dates
    project = ProjectFactory(
        descriptions=2,  # Create 2 descriptions
        dates=1          # Create 1 date
    )

    assert project.descriptions.count() == 2
    assert project.dates.count() == 1
```

**Specify custom metadata types**:

```python
@pytest.mark.django_db
def test_custom_metadata_types():
    # Control which description/date types are created
    project = ProjectFactory(
        descriptions=3,
        descriptions__types=["Abstract", "Introduction", "Objectives"],
        dates=2,
        dates__types=["Start", "End"]
    )

    # Verify specific types were created
    desc_types = project.descriptions.values_list('type', flat=True)
    assert "Abstract" in desc_types
    assert "Introduction" in desc_types
    assert "Objectives" in desc_types
```

:::{note}
**Vocabulary Validation**: Description and date types are validated against the model's `VOCABULARY` attribute. If you provide an invalid type, the factory will raise a `ValueError` listing the valid types.

```python
# This will raise ValueError
project = ProjectFactory(
    descriptions=1,
    descriptions__types=["InvalidType"]  # Not in ProjectDescription.VOCABULARY
)
```

:::

**Override specific fields**:

```python
@pytest.mark.django_db
def test_custom_project():
    project = ProjectFactory(
        name="Portal Research Project",
        visibility="private",
        # Also works with metadata
        descriptions=1,
        descriptions__types=["Abstract"]
    )

    assert project.name == "Portal Research Project"
    assert project.visibility == "private"
    assert project.descriptions.count() == 1
```

**Use existing objects**:

```python
@pytest.mark.django_db
def test_with_specific_organization():
    # Create an organization first
    org = OrganizationFactory(name="Research Institute")

    # Use that organization as project owner
    project = ProjectFactory(
        owner=org,
        name="Institute's Project",
        descriptions=1
    )

    assert project.owner == org
    assert project.owner.name == "Research Institute"
```

## Opt-In Metadata Pattern

### Why Opt-In?

FairDM factories use an **opt-in pattern** for creating related metadata objects to:

1. **Prevent Unique Constraint Violations**: Some models have `unique_together` constraints on `(related, type)`. Auto-creating descriptions could conflict with test-specific metadata you add later.

2. **Minimize Test Data**: Tests often don't need metadata. Creating it by default adds unnecessary database records and slows down tests.

3. **Explicit Control**: When you do need metadata, you explicitly control how many items and which types, making tests clearer and more maintainable.

### Pattern Details

All core factories (`ProjectFactory`, `DatasetFactory`, `SampleFactory`, `MeasurementFactory`) support these optional keyword arguments:

**For descriptions**:

- `descriptions=<int>` - Number of descriptions to create
- `descriptions__types=[...]` - List of specific types to use (must match model VOCABULARY)

**For dates**:

- `dates=<int>` - Number of dates to create
- `dates__types=[...]` - List of specific types to use (must match model VOCABULARY)

**Examples**:

```python
# No metadata (default)
project = ProjectFactory()

# 2 descriptions with auto-selected types from VOCABULARY
project = ProjectFactory(descriptions=2)

# 3 descriptions with specific types
project = ProjectFactory(
    descriptions=3,
    descriptions__types=["Abstract", "Methods", "Objectives"]
)

# Both descriptions and dates
project = ProjectFactory(
    descriptions=2,
    descriptions__types=["Abstract", "Introduction"],
    dates=2,
    dates__types=["Start", "End"]
)

# Batch creation with metadata
projects = ProjectFactory.create_batch(
    5,
    descriptions=2,
    dates=1
)
```

### Available Vocabularies

Each model has a `VOCABULARY` attribute that defines valid types:

**ProjectDescription.VOCABULARY.values**:

- Abstract, Introduction, Background, Objectives, ExpectedOutput, Conclusions, Other
- Plus sample/measurement-specific types when used on those models

**ProjectDate.VOCABULARY.values**:

- Start, End
- Dataset/Sample/Measurement may have additional date types (check model VOCABULARY)

**To check available types for any model**:

```python
from fairdm.core.project.models import ProjectDescription
print(ProjectDescription.VOCABULARY.values)
# Output: ['Abstract', 'Introduction', 'Background', ...]
```

## Runtime Overrides

FairDM factories are designed to be **fully customizable at runtime**. You never need to subclass factories.

### Common Override Patterns

**Null values**:

```python
# Override to None for testing optional fields
project = ProjectFactory(description=None)
assert project.description is None
```

**Specific values**:

```python
# Set exact values for your test scenario
user = UserFactory(
    username="admin",
    email="admin@portal.example.com",
    is_staff=True,
    is_superuser=True
)
```

**Related objects**:

```python
# Control the entire object graph
owner = UserFactory(username="owner")
project = ProjectFactory(owner=owner, title="Controlled Test")
dataset = DatasetFactory(project=project, title="Test Dataset")

assert dataset.project.owner.username == "owner"
```

**Batch creation**:

```python
# Create multiple objects at once
projects = ProjectFactory.create_batch(5)
assert len(projects) == 5

# With overrides
private_projects = ProjectFactory.create_batch(
    3,
    visibility="private"
)
assert all(p.visibility == "private" for p in private_projects)
```

## Extending Factories for Portal-Specific Fields

If your portal extends FairDM models with custom fields, create portal-specific factories:

### Example: Extended Project Model

**Your portal model** (adds custom fields to FairDM's Project):

```python
# your_portal/models.py
from fairdm.core.models import Project

class PortalProject(Project):
    \"\"\"Extended project with portal-specific fields.\"\"\"
    funding_source = models.CharField(max_length=200, blank=True)
    institution = models.CharField(max_length=200, blank=True)
    grant_number = models.CharField(max_length=50, blank=True)
```

**Your portal factory** (extends FairDM's factory):

```python
# your_portal/tests/factories.py
import factory
from fairdm.factories import ProjectFactory
from your_portal.models import PortalProject

class PortalProjectFactory(ProjectFactory):
    \"\"\"
    Factory for portal-specific project model.

    Inherits all FairDM ProjectFactory behavior and adds
    portal-specific field defaults.
    \"\"\"
    class Meta:
        model = PortalProject

    # Portal-specific fields
    funding_source = factory.Faker("company")
    institution = factory.Faker("company")
    grant_number = factory.Sequence(lambda n: f"GRANT-{n:05d}")
```

**Usage in portal tests**:

```python
@pytest.mark.django_db
def test_portal_project():
    # Use your portal factory
    project = PortalProjectFactory(
        title="Funded Research",
        funding_source="NSF",
        grant_number="NSF-12345"
    )

    assert project.funding_source == "NSF"
    assert project.grant_number == "NSF-12345"
    # FairDM fields still work
    assert project.owner is not None
```

### Pattern: Trait-Based Factories

For different test scenarios, use traits instead of subclasses:

```python
# your_portal/tests/factories.py
class PortalProjectFactory(ProjectFactory):
    class Meta:
        model = PortalProject

    funding_source = factory.Faker("company")
    institution = factory.Faker("company")

    class Params:
        # Define traits for common scenarios
        funded = factory.Trait(
            funding_source="NSF",
            grant_number=factory.Sequence(lambda n: f"NSF-{n:05d}")
        )

        unfunded = factory.Trait(
            funding_source="",
            grant_number=""
        )
```

**Usage**:

```python
# Create funded project
funded_project = PortalProjectFactory(funded=True)
assert funded_project.funding_source == "NSF"

# Create unfunded project
unfunded_project = PortalProjectFactory(unfunded=True)
assert unfunded_project.funding_source == ""
```

## Best Practices for Portal Tests

### 1. Import from fairdm.factories

Always use the convenience import path:

```python
# ✅ Good - uses convenience module
from fairdm.factories import ProjectFactory, DatasetFactory

# ❌ Avoid - internal import path
from fairdm.core.factories import ProjectFactory
```

### 2. Override at Runtime

Don't create factory subclasses for every scenario:

```python
# ✅ Good - runtime override
project = ProjectFactory(title="Specific Title", visibility="private")

# ❌ Avoid - unnecessary subclass
class PrivateProjectFactory(ProjectFactory):
    visibility = "private"
```

### 3. Use Factories for Test Setup Only

Factories are for tests, not production code:

```python
# ✅ Good - in test file
@pytest.mark.django_db
def test_my_feature():
    project = ProjectFactory()
    # test logic...

# ❌ Avoid - in production/view code
def my_view(request):
    project = ProjectFactory()  # Don't use factories in production!
```

### 4. Build vs Create

Use `build()` for unit tests (no database), `create()` for integration tests:

```python
# Unit test - no database hit
def test_project_validation():
    project = ProjectFactory.build(title="Test")
    assert project.title == "Test"
    assert project.pk is None  # Not saved

# Integration test - saves to database
@pytest.mark.django_db
def test_project_persistence():
    project = ProjectFactory.create(title="Test")
    assert project.pk is not None  # Saved
```

### 5. Compose Fixtures for Complex Scenarios

Create pytest fixtures that compose factories:

```python
# your_portal/tests/conftest.py
import pytest
from fairdm.factories import ProjectFactory, DatasetFactory, UserFactory

@pytest.fixture
def research_project():
    \"\"\"Create a project with user and datasets.\"\"\"
    user = UserFactory(username="researcher")
    project = ProjectFactory(owner=user, title="Research Project")
    datasets = DatasetFactory.create_batch(3, project=project)
    return {
        'user': user,
        'project': project,
        'datasets': datasets
    }

# Use in tests
@pytest.mark.django_db
def test_my_feature(research_project):
    project = research_project['project']
    assert project.datasets.count() == 3
```

## Complete Example: Portal Feature Test

Here's a complete example testing a portal-specific feature:

```python
# your_portal/tests/test_project_sharing.py
\"\"\"
Tests for portal-specific project sharing feature.
\"\"\"
import pytest
from fairdm.factories import UserFactory, ProjectFactory
from your_portal.models import ProjectShare

@pytest.mark.django_db
class TestProjectSharing:
    \"\"\"Test suite for project sharing feature.\"\"\"

    def test_share_project_with_user(self):
        \"\"\"Test sharing a project with another user.\"\"\"
        # Setup: Create owner and project using FairDM factories
        owner = UserFactory(username="owner")
        project = ProjectFactory(owner=owner, title="Shared Project")

        # Setup: Create collaborator
        collaborator = UserFactory(username="collaborator")

        # Action: Share project (your portal feature)
        share = ProjectShare.objects.create(
            project=project,
            user=collaborator,
            permission="view"
        )

        # Assert: Verify sharing worked
        assert share.project == project
        assert share.user == collaborator
        assert project.shares.count() == 1

    def test_multiple_shares_on_same_project(self):
        \"\"\"Test sharing a project with multiple users.\"\"\"
        # Setup using factories
        project = ProjectFactory(title="Collaborative Project")
        users = UserFactory.create_batch(3)

        # Action: Share with multiple users
        shares = [
            ProjectShare.objects.create(
                project=project,
                user=user,
                permission="edit"
            )
            for user in users
        ]

        # Assert
        assert len(shares) == 3
        assert project.shares.count() == 3

    def test_cannot_share_with_owner(self):
        \"\"\"Test that owner cannot share project with themselves.\"\"\"
        # Setup
        owner = UserFactory(username="owner")
        project = ProjectFactory(owner=owner)

        # Action & Assert: Should raise validation error
        with pytest.raises(ValidationError):
            ProjectShare.objects.create(
                project=project,
                user=owner,  # Same as owner
                permission="view"
            )
```

## Troubleshooting

### "No module named 'fairdm'"

**Problem**: Import error when running tests.

**Solution**: Install FairDM as dev dependency:

```bash
poetry add --group dev fairdm
```

### "UserFactory has no attribute 'create_user'"

**Problem**: Calling Django User manager methods on factory.

**Solution**: Use factory methods instead:

```python
# ❌ Wrong
user = UserFactory.create_user(username="test")

# ✅ Correct
user = UserFactory(username="test")
```

### Factory creates unexpected related objects

**Problem**: Factory creates unwanted SubFactory instances.

**Solution**: Override with None or provide explicit instance:

```python
# Prevent SubFactory creation
project = ProjectFactory(owner=None)  # If owner is optional

# Or provide explicit instance
owner = UserFactory()
project = ProjectFactory(owner=owner)
```

### Tests are slow due to many object creations

**Problem**: Too many database hits from factories.

**Solution**: Use `build()` where possible, or create fixtures:

```python
# Fast - no database
project = ProjectFactory.build()

# Or use module-scoped fixtures
@pytest.fixture(scope="module")
def shared_project(django_db_blocker):
    with django_db_blocker.unblock():
        return ProjectFactory()
```

## Next Steps

- **Learn more**: Read [FairDM Testing Strategy](../contributing/testing/index.md) for advanced patterns
- **Factory patterns**: See [Fixture Factory Examples](../contributing/testing/examples/fixture-factory-example.md)
- **Integration testing**: Read [Integration Test Guide](../contributing/testing/examples/integration-test-example.md)

## Getting Help

- **FairDM Documentation**: <https://docs.fairdm.org>
- **GitHub Issues**: <https://github.com/FAIR-DM/fairdm/issues>
- **Discussions**: <https://github.com/FAIR-DM/fairdm/discussions>
