# Database Strategy

FairDM uses pytest-django for efficient database management in tests. Understanding transaction rollback and database lifecycle ensures fast, reliable, isolated tests.

```{contents}
:local:
:depth: 2
```

## Overview

Integration tests need database access but must remain:

- **Fast**: Minimize database overhead
- **Isolated**: Each test starts with clean state
- **Reliable**: No test-order dependencies

pytest-django achieves this through:

1. **Session-level database creation**: Database created once per test run
2. **Transaction rollback**: Each test runs in transaction, rolled back after
3. **Reusable database**: `--reuse-db` flag skips database recreation

## Database Lifecycle

### Session-Level Database Creation

The test database is created **once** at the start of the test session and **destroyed** at the end:

```python
# tests/conftest.py
import pytest
from django.core.management import call_command

@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """
    Create test database once per session.

    Uses django_db_blocker to ensure database is created
    before tests run.
    """
    with django_db_blocker.unblock():
        call_command("migrate", "--noinput")
```

**Why session scope?**

- Creating databases is slow (1-5 seconds)
- Recreating for each test is wasteful
- Session scope shares one database across all tests

### Transaction Rollback

Each test with `@pytest.mark.django_db` runs inside a **transaction**:

```python
@pytest.mark.django_db
def test_project_creation():
    project = ProjectFactory()  # INSERT
    assert project.pk is not None  # Verify
    # Transaction ROLLBACK here - project deleted
```

**After the test**:

- Transaction is rolled back
- All changes are undone
- Database returns to clean state

**Benefits**:

- **Fast**: Rollback is faster than DELETE queries
- **Isolated**: Tests don't affect each other
- **Clean**: No leftover test data

## The @pytest.mark.django_db Decorator

### Basic Usage

```python
@pytest.mark.django_db
def test_something_with_database():
    user = User.objects.create(username="test")
    assert User.objects.count() == 1
```

**Without the decorator:**

```python
def test_something():
    # ❌ PytestDjangoTestError: Database access not allowed
    user = User.objects.create(username="test")
```

### Transaction Control

```python
# Default: Wraps test in transaction (fast, isolated)
@pytest.mark.django_db
def test_normal():
    ...

# Disable transaction (for testing transaction behavior)
@pytest.mark.django_db(transaction=True)
def test_transaction_commit():
    ...
```

**When to use `transaction=True`:**

- Testing code that explicitly commits transactions
- Testing Django's `transaction.atomic()` behavior
- Testing transaction rollback handling

**Default is sufficient for 99% of tests.**

## Database Reuse with --reuse-db

### The Problem

By default, pytest-django:

1. Creates test database
2. Runs migrations
3. Runs tests
4. Destroys database

Steps 1-2 and 4 add 5-10 seconds **per test run**.

### The Solution

```bash
# First run: Creates database
poetry run pytest --reuse-db

# Subsequent runs: Reuses existing database
poetry run pytest --reuse-db
```

**Benefits**:

- Saves 5-10 seconds per test run
- Same isolation (transaction rollback still works)
- Database persists between runs

**When to recreate:**

```bash
# Force recreation (after migration changes)
poetry run pytest --create-db
```

## Fast Test Execution

### Strategy 1: Minimize Database Access

```python
# ✅ Good: Unit test without database
def test_slugify():
    result = slugify("Test Project")
    assert result == "test-project"

# ❌ Bad: Unnecessary database access
@pytest.mark.django_db
def test_slugify():
    project = ProjectFactory.build()  # Why create a project?
    result = slugify(project.title)
    assert result
```

### Strategy 2: Batch Creation

```python
# ✅ Good: Create multiple objects in one go
@pytest.mark.django_db
def test_project_list():
    projects = ProjectFactory.create_batch(10)
    assert Project.objects.count() == 10

# ❌ Bad: Multiple individual creates
@pytest.mark.django_db
def test_project_list():
    for i in range(10):
        ProjectFactory()
    assert Project.objects.count() == 10
```

### Strategy 3: Use --no-migrations

```bash
# Skip migrations (assumes migrations are current)
poetry run pytest --no-migrations
```

Configured in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
addopts = [
    "--reuse-db",
    "--no-migrations",
]
```

**Trade-off**: Faster, but won't catch migration issues.

## Database Queries and N+1 Problems

### Detecting Query Issues

Use `django-assert-num-queries` to catch performance problems:

```python
from django.test.utils import override_settings
from django.test import TestCase

@pytest.mark.django_db
def test_project_list__avoids_n_plus_one():
    """Test that listing projects doesn't cause N+1 queries."""
    ProjectFactory.create_batch(10)

    with django_assert_num_queries(1):
        # Single query with select_related
        list(Project.objects.select_related('owner'))
```

### Common N+1 Solutions

**Problem: Loading related objects in loop**

```python
# ❌ Bad: N+1 queries
projects = Project.objects.all()
for project in projects:
    print(project.owner.username)  # Query per project
```

**Solution 1: select_related (ForeignKey)**

```python
# ✅ Good: 1 query with JOIN
projects = Project.objects.select_related('owner')
for project in projects:
    print(project.owner.username)  # No additional query
```

**Solution 2: prefetch_related (ManyToMany)**

```python
# ✅ Good: 2 queries total
projects = Project.objects.prefetch_related('datasets')
for project in projects:
    print(project.datasets.count())  # No additional queries
```

## Test Data Isolation

### Isolated Tests (Default)

```python
@pytest.mark.django_db
def test_one():
    ProjectFactory()
    assert Project.objects.count() == 1

@pytest.mark.django_db
def test_two():
    ProjectFactory()
    # ✅ Previous test rolled back
    assert Project.objects.count() == 1
```

### Shared Fixtures (Explicit)

```python
@pytest.fixture(scope="module")
def shared_user(django_db_blocker):
    """
    Create user once for entire module.

    Requires django_db_blocker to manage transaction scope.
    """
    with django_db_blocker.unblock():
        return UserFactory()

@pytest.mark.django_db
def test_with_shared_user(shared_user):
    project = ProjectFactory(owner=shared_user)
    assert project.owner == shared_user
```

**Use shared fixtures sparingly** - they reduce isolation.

## Reference Data

For data that should exist across all tests (e.g., vocabularies, reference tables):

```python
# tests/conftest.py
@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Load reference data once per session."""
    with django_db_blocker.unblock():
        call_command("migrate", "--noinput")
        call_command("loaddata", "reference_vocabularies.json")
```

**Benefits:**

- Loaded once per session
- Available to all tests
- Survives transaction rollback

## Parallel Testing

For large test suites, run tests in parallel:

```bash
# Install pytest-xdist
poetry add --group dev pytest-xdist

# Run with 4 processes
poetry run pytest -n 4

# Run with auto-detect CPU count
poetry run pytest -n auto
```

**Considerations:**

- Each process gets its own database (`test_db_gw0`, `test_db_gw1`, etc.)
- Increases setup time (multiple databases)
- Speeds up test execution (parallel)
- Best for CI/CD, may be overkill for local development

## Configuration Reference

### pyproject.toml

```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "tests.settings"
addopts = [
    "--reuse-db",          # Reuse database between runs
    "--no-migrations",     # Skip migrations for speed
    "--strict-markers",    # Enforce marker registration
]
```

### Command-Line Options

```bash
# Create fresh database
poetry run pytest --create-db

# Reuse existing database
poetry run pytest --reuse-db

# Keep database after tests
poetry run pytest --reuse-db --no-migrations

# Run specific test with database
poetry run pytest tests/integration/test_project.py::test_create -v
```

## Best Practices

### 1. Default to Transaction Rollback

```python
# ✅ Good: Default transaction behavior
@pytest.mark.django_db
def test_something():
    ...

# ❌ Bad: Unnecessary transaction=True
@pytest.mark.django_db(transaction=True)
def test_something():
    ...
```

Use `transaction=True` only when testing transaction behavior.

### 2. Use --reuse-db Locally

Add to your shell alias:

```bash
alias pytest-fast="poetry run pytest --reuse-db"
```

### 3. Minimize Database Tests

```python
# ✅ Good: Unit test without database
def test_generate_slug():
    project = Project(title="Test")
    assert project.generate_slug() == "test"

# ❌ Bad: Database for simple logic
@pytest.mark.django_db
def test_generate_slug():
    project = ProjectFactory()
    assert project.generate_slug()
```

### 4. Clean Up External Resources

If tests create files, network connections, or other resources:

```python
@pytest.fixture
def temp_file(tmp_path):
    """Pytest tmp_path handles cleanup automatically."""
    file_path = tmp_path / "test.txt"
    file_path.write_text("test data")
    yield file_path
    # Automatic cleanup by pytest
```

## Troubleshooting

### Problem: Tests fail randomly

**Cause**: Tests depend on execution order or shared state

**Solution**: Ensure each test is isolated

```python
# ❌ Bad: Shared state
projects = []

@pytest.mark.django_db
def test_one():
    projects.append(ProjectFactory())

@pytest.mark.django_db
def test_two():
    assert len(projects) == 1  # Fails if test_one doesn't run first
```

### Problem: Database locked error

**Cause**: Multiple test processes accessing same database

**Solution**: Use `pytest-xdist` properly

```bash
# ✅ Good: Each worker gets own database
poetry run pytest -n auto

# ❌ Bad: Manual parallel with same DB
poetry run pytest & poetry run pytest  # Don't do this
```

### Problem: Migrations too slow

**Solution**: Use `--no-migrations` flag

```bash
poetry run pytest --reuse-db --no-migrations
```

**Warning**: Won't catch migration issues. Run full migrations in CI.

## Next Steps

```{seealso}
- Learn about [Fixtures & Factories](fixtures.md) for efficient test data creation with factory-boy
- Review [Test Layers](test-layers.md) to understand when database access is needed
- See [Running Tests](running-tests.md) for CLI options like `--reuse-db` and `--create-db`
- Check [Coverage](coverage.md) to ensure database code paths are tested
- Read [Test Quality](test-quality.md) for writing reliable integration tests
```

## References

- [pytest-django Documentation](https://pytest-django.readthedocs.io/)
- [Django Testing Tools](https://docs.djangoproject.com/en/stable/topics/testing/tools/)
- [Django Database Transactions](https://docs.djangoproject.com/en/stable/topics/db/transactions/)
