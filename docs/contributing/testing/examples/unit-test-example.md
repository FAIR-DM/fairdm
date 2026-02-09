# Unit Test Example

This example demonstrates a complete unit test following FairDM conventions.

```{contents}
:local:
:depth: 2
```

## Overview

Unit tests validate **isolated logic** without external dependencies. This example shows:

- Proper file location and naming
- Test function naming convention
- Meaningful assertions
- No database access

## Source Code

**File**: `fairdm/core/models.py`

```python
from django.db import models
from django.utils.text import slugify

class Project(models.Model):
    """A research project containing datasets."""

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)

    def get_absolute_url(self):
        """Return the detail URL for this project."""
        return f"/projects/{self.slug}/"

    def generate_slug(self):
        """Generate a slug from the title."""
        if not self.title:
            return ""
        return slugify(self.title)

    class Meta:
        ordering = ["title"]
```

## Unit Test

**File**: `tests/unit/fairdm/core/test_models.py`

```python
"""Unit tests for fairdm.core.models."""
from fairdm.core.models import Project

# Test 1: URL generation (no database)
def test_get_absolute_url__with_valid_slug__returns_detail_url():
    """
    Test URL generation without database access.

    This validates the URL pattern is correct and doesn't
    require database persistence to test.
    """
    # Arrange: Create in-memory project (no .save())
    project = Project(pk=123, slug="test-project")

    # Act: Generate URL
    url = project.get_absolute_url()

    # Assert: Verify correct URL format
    assert url == "/projects/test-project/"


# Test 2: Slug generation from title
def test_generate_slug__with_title__returns_slugified_title():
    """
    Test slug generation from project title.

    This ensures consistent slug formatting for URLs.
    """
    # Arrange
    project = Project(title="My Test Project 2025")

    # Act
    slug = project.generate_slug()

    # Assert: Slug should be lowercase with hyphens
    assert slug == "my-test-project-2025"


# Test 3: Edge case - empty title
def test_generate_slug__with_empty_title__returns_empty_string():
    """
    Test slug generation with empty title.

    Edge case: ensures graceful handling of missing data.
    """
    # Arrange
    project = Project(title="")

    # Act
    slug = project.generate_slug()

    # Assert: Empty title should return empty slug
    assert slug == ""


# Test 4: Edge case - special characters
def test_generate_slug__with_special_characters__removes_special_chars():
    """
    Test slug generation with special characters.

    Validates that slugify properly handles non-alphanumeric characters.
    """
    # Arrange
    project = Project(title="Test @#$ Project!!")

    # Act
    slug = project.generate_slug()

    # Assert: Special characters removed
    assert slug == "test-project"
```

## Explanation

### File Location

```text
tests/unit/fairdm/core/test_models.py
└─┬─┘ └───┬───┘ └─┬─┘ └─────┬──────┘
  │       │       │          └─ Module: models.py
  │       │       └──────────── App: fairdm.core
  │       └──────────────────── Django package: fairdm
  └──────────────────────────── Test layer: unit
```

**Why this location:**

- Unit test layer (no database)
- Mirrors source structure: `fairdm/core/models.py`
- File name follows `test_<module>.py` pattern

### Test Naming Convention

Each test follows: `test_<behavior>__<condition>__<expected>`

**Example breakdown:**

```python
test_get_absolute_url__with_valid_slug__returns_detail_url
└────────┬────────┘ └─────┬──────────┘ └────────┬─────────┘
         │                │                      └─ Expected: returns detail URL
         │                └──────────────────────── Condition: with valid slug
         └───────────────────────────────────────── Behavior: get_absolute_url
```

### Test Structure (AAA Pattern)

Each test follows **Arrange-Act-Assert**:

```python
def test_something():
    # Arrange: Set up test data
    project = Project(title="Test")

    # Act: Perform the action
    result = project.generate_slug()

    # Assert: Verify the outcome
    assert result == "test"
```

### Why This is a Unit Test

✅ **Isolated**: No database calls, no external dependencies
✅ **Fast**: Runs in < 100ms
✅ **Focused**: Tests one method at a time
✅ **Deterministic**: Same input always produces same output

❌ **Not a unit test if it:**

- Uses `@pytest.mark.django_db`
- Calls `.save()` or `.create()`
- Accesses database or file system
- Makes network requests

## Running This Test

### Run all unit tests

```bash
poetry run pytest tests/unit/
```

### Run this specific file

```bash
poetry run pytest tests/unit/fairdm/core/test_models.py
```

### Run a specific test

```bash
poetry run pytest tests/unit/fairdm/core/test_models.py::test_get_absolute_url__with_valid_slug__returns_detail_url
```

### Run with verbose output

```bash
poetry run pytest tests/unit/fairdm/core/test_models.py -v
```

## Best Practices Demonstrated

### 1. No Database Access

```python
# ✅ Good: In-memory object
project = Project(pk=123, slug="test-project")

# ❌ Bad: Database access in unit test
project = Project.objects.create(slug="test-project")
```

### 2. Clear Test Names

```python
# ✅ Good: Descriptive name
def test_generate_slug__with_title__returns_slugified_title():

# ❌ Bad: Generic name
def test_slug():
```

### 3. Meaningful Docstrings

```python
# ✅ Good: Explains "why"
"""
Test slug generation from project title.

This ensures consistent slug formatting for URLs.
"""

# ❌ Bad: Repeats function name
"""Test generate_slug."""
```

### 4. One Assertion Focus

```python
# ✅ Good: Single concern
def test_generate_slug__with_title__returns_slugified_title():
    project = Project(title="Test Project")
    assert project.generate_slug() == "test-project"

# ❌ Bad: Multiple concerns
def test_project_methods():
    project = Project(title="Test")
    assert project.generate_slug() == "test"  # Testing slug
    assert project.get_absolute_url() == "/projects/test/"  # Testing URL
```

## Edge Cases Covered

This example demonstrates testing edge cases:

1. **Happy path**: Valid data → expected output
2. **Empty input**: Empty title → empty slug
3. **Special characters**: Non-alphanumeric → cleaned slug

**Why test edge cases?**
Edge cases often reveal bugs in production. Testing them in unit tests is fast and prevents regressions.

## Common Mistakes

::::{grid} 1 1 2 2
:gutter: 3

:::{grid-item-card} ❌ Database Access
Using `@pytest.mark.django_db` in unit tests makes them slow.

**Fix**: Use in-memory objects or move to integration tests.
:::

:::{grid-item-card} ❌ Multiple Assertions
Testing multiple behaviors in one test makes debugging harder.

**Fix**: One test per behavior.
:::

:::{grid-item-card} ❌ Testing Django Internals
Testing that Django's slugify works (it does).

**Fix**: Test your code's behavior, not Django's.
:::

:::{grid-item-card} ❌ Missing Edge Cases
Only testing happy path.

**Fix**: Test empty input, special characters, boundary conditions.
:::

::::

## Next Steps

```{seealso}
- Compare with [Integration Test Example](integration-test-example.md)
- Review [Test Quality Guidelines](../test-quality.md)
- Learn about [Test Organization](../test-organization.md)
```

## References

- [Test Layers: Unit Tests](../test-layers.md#unit-tests)
- [Test Quality: Meaningful Tests](../test-quality.md#meaningful-tests)
- [Test Naming Contract](../../../../specs/004-testing-strategy-fixtures/contracts/test-naming-contract.md)
