# Test Quality

Writing tests is not enough—tests must be **meaningful**, **maintainable**, and **reliable** to provide lasting value. This guide defines what quality means for FairDM tests and how to achieve it.

```{contents}
:local:
:depth: 2
```

## Overview

Quality tests are characterized by three core properties:

::::{grid} 1 1 3 3
:gutter: 3

:::{grid-item-card} {octicon}`check-circle` Meaningful
Test **real behavior** and **observable outcomes**, not implementation details.
:::

:::{grid-item-card} {octicon}`tools` Maintainable
Easy to **understand**, **update**, and **refactor** as code evolves.
:::

:::{grid-item-card} {octicon}`sync` Reliable
**Deterministic** and **fast**—same input always produces same output.
:::

::::

## Meaningful Tests

### Test Behavior, Not Implementation

**Bad example** (tests implementation):

```python
def test_project_save__calls_clean():
    """This test breaks if we refactor how validation works."""
    project = Project(title="Test")
    with patch.object(project, 'clean') as mock_clean:
        project.save()
    mock_clean.assert_called_once()  # ❌ Tests internal call
```

**Good example** (tests behavior):

```python
@pytest.mark.django_db
def test_project_save__with_blank_title__raises_validation_error():
    """This test survives refactoring as long as validation behavior stays."""
    project = Project(title="")

    with pytest.raises(ValidationError, match="title"):
        project.full_clean()  # ✅ Tests observable outcome
```

**Why this matters**: Implementation details change frequently. Tests that verify behavior survive refactoring.

### Assert on Observable Outcomes

Focus on what users or other systems can observe:

✅ **Do assert:**

- Return values
- Raised exceptions
- Database state changes
- API response content
- UI element presence

❌ **Don't assert:**

- Private method calls
- Internal state variables
- Number of SQL queries (unless performance-critical)
- Mock call counts (unless testing side effects)

### Example: Meaningful Assertions

```python
@pytest.mark.django_db
def test_project_creation__with_valid_data__creates_project_and_assigns_owner():
    """Test observable outcomes of project creation."""
    user = UserFactory()

    project = ProjectFactory(owner=user, title="Test Project")

    # ✅ Assert on observable state
    assert project.pk is not None  # Persisted to database
    assert project.owner == user   # Relationship established
    assert project.title == "Test Project"  # Data stored correctly
    assert project.created is not None  # Timestamp set

    # ✅ Assert on database state
    assert Project.objects.filter(owner=user).count() == 1
```

## Maintainable Tests

### Clear Test Names

Use the pattern: `test_<behavior>__<condition>__<expected>`

**Examples:**

```python
# ✅ Clear intent
def test_login__with_invalid_password__returns_error():
    ...

def test_dataset_delete__with_related_samples__cascades_deletion():
    ...

# ❌ Unclear intent
def test_login():
    ...

def test_dataset_1():
    ...
```

### Minimal Duplication

**Use factories and fixtures** to reduce setup duplication:

**Bad example** (duplicated setup):

```python
def test_project_update__with_new_title__updates_database():
    user = User.objects.create(username="test", email="test@example.com")
    project = Project.objects.create(owner=user, title="Old Title")
    # ... test logic

def test_project_delete__removes_from_database():
    user = User.objects.create(username="test", email="test@example.com")
    project = Project.objects.create(owner=user, title="Test")
    # ... test logic
```

**Good example** (factory-based setup):

```python
def test_project_update__with_new_title__updates_database():
    project = ProjectFactory()  # ✅ Reusable factory
    # ... test logic

def test_project_delete__removes_from_database():
    project = ProjectFactory()  # ✅ Same factory, different test
    # ... test logic
```

### Self-Documenting Tests

Tests should explain themselves through:

1. **Descriptive names** (use the naming convention)
2. **Clear docstrings** (explain "why" not "what")
3. **Explicit assertions** (don't hide intent in helpers)

**Example:**

```python
@pytest.mark.django_db
def test_project_visibility__private_project_with_anonymous_user__returns_403():
    """
    Anonymous users cannot access private projects.

    This ensures projects marked private remain inaccessible
    until explicit permission is granted via django-guardian.
    """
    project = ProjectFactory(visibility=Project.Visibility.PRIVATE)
    client = APIClient()  # Anonymous client

    response = client.get(reverse('api:project-detail', args=[project.pk]))

    assert response.status_code == 403
```

### Easy to Update

Design tests that adapt to change:

**Brittle test** (hard-coded IDs):

```python
def test_project_list__returns_all_projects():
    response = client.get('/api/projects/')
    assert len(response.data) == 5  # ❌ Breaks if fixture changes
```

**Flexible test** (dynamic assertions):

```python
def test_project_list__returns_all_projects():
    expected_count = ProjectFactory.create_batch(5)
    response = client.get('/api/projects/')
    assert len(response.data) == len(expected_count)  # ✅ Adapts to change
```

## Reliable Tests

### Deterministic

Tests must produce the same result every time:

❌ **Avoid:**

- Random data without seeding
- Timestamps without mocking
- Network calls without mocking
- File system operations without cleanup

✅ **Use:**

- Factory-boy for consistent data
- `freezegun` for time-dependent tests
- Mocks for external dependencies
- Pytest fixtures for setup/teardown

**Example: Reliable time-dependent test**

```python
from freezegun import freeze_time

@freeze_time("2025-01-15 12:00:00")
@pytest.mark.django_db
def test_project_is_recent__within_30_days__returns_true():
    """Test with frozen time ensures deterministic results."""
    project = ProjectFactory(created=timezone.now())

    assert project.is_recent()  # ✅ Always true with frozen time
```

### Fast Execution

**Unit tests**: < 100ms per test
**Integration tests**: < 1s per test
**Contract tests**: < 5s per test

**Strategies:**

- Use `@pytest.mark.django_db` only when needed
- Avoid unnecessary database queries
- Mock slow external dependencies
- Use `--reuse-db` for faster test runs

### Isolated

Each test should be independent:

**Bad example** (shared state):

```python
# ❌ Tests depend on execution order
project = None

def test_create_project():
    global project
    project = ProjectFactory()

def test_update_project():
    project.title = "Updated"  # Fails if test_create_project doesn't run first
    project.save()
```

**Good example** (isolated tests):

```python
# ✅ Each test is self-contained
@pytest.mark.django_db
def test_create_project__with_valid_data__creates_project():
    project = ProjectFactory()
    assert project.pk is not None

@pytest.mark.django_db
def test_update_project__with_new_title__updates_database():
    project = ProjectFactory()
    project.title = "Updated"
    project.save()
    assert project.title == "Updated"
```

## Quality Checklist

Use this checklist to review your tests:

### Meaningful

- [ ] Tests verify **behavior**, not implementation
- [ ] Assertions focus on **observable outcomes**
- [ ] Test name describes **what** is being validated
- [ ] Docstring explains **why** the behavior matters

### Maintainable

- [ ] Test name follows `test_<behavior>__<condition>__<expected>` pattern
- [ ] Setup uses **factories** or **fixtures** (no duplication)
- [ ] Test is **self-documenting** (clear intent)
- [ ] Assertions are **explicit** (not hidden in helpers)

### Reliable

- [ ] Test is **deterministic** (same result every time)
- [ ] Test is **fast** (< 100ms unit, < 1s integration, < 5s contract)
- [ ] Test is **isolated** (no shared state between tests)
- [ ] External dependencies are **mocked** or **managed** with fixtures

## Anti-Patterns

### 1. Testing Django Internals

**Bad:**

```python
def test_queryset_uses_select_related():
    qs = Project.objects.get_queryset()
    assert 'owner' in qs.query.select_related  # ❌ Tests Django internals
```

**Good:**

```python
@pytest.mark.django_db
def test_project_list__includes_owner_data__without_n_plus_one():
    ProjectFactory.create_batch(10)

    with django_assert_num_queries(1):  # ✅ Tests performance behavior
        list(Project.objects.select_related('owner'))
```

### 2. Over-Mocking

**Bad:**

```python
def test_project_save():
    with patch('django.db.models.Model.save') as mock_save:
        project = Project(title="Test")
        project.save()
        mock_save.assert_called()  # ❌ Mocked so much nothing is tested
```

**Good:**

```python
@pytest.mark.django_db
def test_project_save__with_valid_data__persists_to_database():
    project = ProjectFactory()
    project.title = "Updated"
    project.save()

    assert Project.objects.get(pk=project.pk).title == "Updated"  # ✅ Real behavior
```

### 3. Brittle Assertions

**Bad:**

```python
def test_api_response__returns_project_data():
    response = client.get('/api/projects/1/')
    assert response.json() == {  # ❌ Breaks if any field changes
        'id': 1,
        'title': 'Test',
        'slug': 'test',
        'created': '2025-01-15T12:00:00Z',
        'modified': '2025-01-15T12:00:00Z',
        # ... 20 more fields
    }
```

**Good:**

```python
def test_api_response__returns_project_data():
    project = ProjectFactory(title="Test Project")
    response = client.get(f'/api/projects/{project.pk}/')

    data = response.json()
    assert data['id'] == project.pk  # ✅ Assert on essentials
    assert data['title'] == project.title
    assert 'created' in data  # ✅ Presence check for timestamps
```

## Next Steps

```{seealso}
- Review [Test Layers](test-layers.md) for layer-specific guidance
- Follow [Test Organization](test-organization.md) for structure
- Use [Fixtures & Factories](fixtures.md) for maintainable setup
- Check [Coverage](coverage.md) for measuring test effectiveness
```
