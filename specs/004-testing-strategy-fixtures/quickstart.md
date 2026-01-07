# Quickstart: Writing Tests in FairDM

**Estimated time**: 5 minutes
**Audience**: Contributors writing or updating FairDM features

This guide gets you started with FairDM's testing strategy. For comprehensive documentation, see [`docs/contributing/testing/`](../../docs/contributing/testing/).

---

## 1. Choose Your Test Layer (30 seconds)

**Quick decision tree**:

```
Does your test need database/file system/network?
│
├─ NO → Write a UNIT test
│        Location: tests/unit/{app}/test_{module}.py
│        Example: Testing a pure function or class method
│
└─ YES → Does it test API/data format contracts?
         │
         ├─ YES → Write a CONTRACT test
         │         Location: tests/contract/{app}/test_{module}.py
         │         Example: Testing API response schema
         │
         └─ NO → Write an INTEGRATION test
                  Location: tests/integration/{app}/test_{module}.py
                  Example: Testing project creation workflow
```

---

## 2. Write Your First Unit Test (2 minutes)

**Unit tests** validate isolated behavior without external dependencies.

```python
# tests/unit/fairdm_core/test_utils.py
from fairdm.core.utils import slugify_name

def test_slugify_name__with_spaces__converts_to_hyphens():
    """When slugifying a name with spaces, spaces are converted to hyphens."""
    result = slugify_name("My Project Name")
    assert result == "my-project-name"

def test_slugify_name__with_special_chars__removes_them():
    """When slugifying a name with special characters, they are removed."""
    result = slugify_name("Project @#$ Name!")
    assert result == "project-name"
```

**Run it**:

```powershell
poetry run pytest tests/unit/fairdm_core/test_utils.py -v
```

**Key points**:

- ✅ Fast (no database, no network)
- ✅ Deterministic (same input always produces same output)
- ✅ Clear naming: `test_<behavior>__<condition>__<expected>`

---

## 3. Use a Fixture Factory (1 minute)

**Integration tests** need test data. Use factory-boy instead of creating objects manually.

```python
# tests/integration/fairdm_core/test_project_workflow.py
import pytest
from tests.fixtures.factories import ProjectFactory, DatasetFactory

@pytest.mark.django_db
def test_project_creation__with_datasets__creates_related_objects():
    """When creating a Project with datasets, related Dataset objects are created."""
    # Create test project with factory
    project = ProjectFactory(name="Test Project")

    # Create related datasets
    DatasetFactory.create_batch(3, project=project)

    # Validate
    assert project.datasets.count() == 3
```

**Available factories**: See [`tests/fixtures/factories.py`](../../tests/fixtures/factories.py)

**Key points**:

- ✅ No boilerplate object creation
- ✅ Consistent test data across tests
- ✅ Easy to customize: `ProjectFactory(name="Custom Name")`

---

## 4. Write an Integration Test (1 minute)

**Integration tests** validate cross-component workflows with database access.

```python
# tests/integration/fairdm_core/test_dataset_workflow.py
import pytest
from fairdm.core.models import Dataset, Sample
from tests.fixtures.factories import ProjectFactory, DatasetFactory, SampleFactory

@pytest.mark.django_db
def test_dataset_deletion__with_samples__cascades():
    """When deleting a Dataset with samples, samples are also deleted."""
    # Setup
    project = ProjectFactory()
    dataset = DatasetFactory(project=project)
    sample = SampleFactory(dataset=dataset, project=project)

    sample_id = sample.id

    # Execute
    dataset.delete()

    # Verify cascade
    assert not Sample.objects.filter(id=sample_id).exists()
```

**Key points**:

- ✅ Use `@pytest.mark.django_db` to enable database access
- ✅ Test automatically rolls back after execution (clean state)
- ✅ Focus on workflows, not individual methods

---

## 5. Run Tests and Check Coverage (1 minute)

**Run all tests**:

```powershell
poetry run pytest
```

**Run specific layer**:

```powershell
# Unit tests only (fast)
poetry run pytest tests/unit/ -v

# Integration tests only
poetry run pytest tests/integration/ -v
```

**Check coverage** (diagnostic, not a gate):

```powershell
poetry run coverage run -m pytest
poetry run coverage report --show-missing
poetry run coverage html  # Open htmlcov/index.html
```

**Key points**:

- ✅ Coverage shows untested code paths (use to find gaps)
- ✅ Test quality > coverage percentage
- ✅ Meaningful, maintainable, reliable tests are the goal

---

## Quick Reference

### Test Organization

```text
tests/
├── unit/{app}/test_{module}.py       # Fast, isolated tests
├── integration/{app}/test_{module}.py # Cross-component workflows
├── contract/{app}/test_{module}.py    # API/data format contracts
└── fixtures/factories.py              # Shared test data factories
```

### Test Naming Pattern

```python
def test_<behavior>__<condition>__<expected>():
    """Human-readable description of what this test validates."""
    pass
```

### Common pytest Markers

```python
@pytest.mark.django_db              # Enable database access (integration tests)
@pytest.mark.django_db(transaction=True)  # Enable transaction management
@pytest.mark.slow                   # Mark slow tests (>1 second)
@pytest.mark.unit                   # Explicitly mark as unit test
@pytest.mark.integration            # Explicitly mark as integration test
```

### Factory-Boy Basics

```python
from tests.fixtures.factories import ProjectFactory

# Create with defaults
project = ProjectFactory()

# Override fields
project = ProjectFactory(name="Custom Name", description="Custom Description")

# Create batch
projects = ProjectFactory.create_batch(10)

# Create with related objects
project = ProjectFactory()
DatasetFactory(project=project)  # Creates dataset linked to project
```

---

## Next Steps

- **Full documentation**: [`docs/contributing/testing/`](../../docs/contributing/testing/)
- **Test examples**: See existing tests in [`tests/`](../../tests/)
- **Fixture factories**: [`tests/fixtures/factories.py`](../../tests/fixtures/factories.py)
- **Test quality guidelines**: [`docs/contributing/testing/test-quality.md`](../../docs/contributing/testing/test-quality.md)

---

**Questions?** Check the [testing documentation](../../docs/contributing/testing/) or ask in the team chat.
