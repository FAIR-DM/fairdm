# Running Tests

This guide covers how to run FairDM tests locally using pytest, including filtering, reporting, and debugging options.

## Prerequisites

Ensure you have installed FairDM's development dependencies:

```bash
poetry install --with dev
```

This installs:

- **pytest**: Test runner
- **pytest-django**: Django integration for database, fixtures, and settings
- **pytest-cov**: Coverage.py integration
- **factory-boy**: Test data factories

## Basic Test Execution

### Run All Tests

```bash
poetry run pytest
```

This executes all tests in `tests/` with default settings.

### Run Tests by Layer

```bash
# Unit tests only (no database)
poetry run pytest tests/unit/

# Integration tests only (database required)
poetry run pytest tests/integration/

# Contract tests only (API validation)
poetry run pytest tests/contract/
```

See [Test Layers](test-layers.md) for layer definitions.

### Run Tests by Module

```bash
# Single test module
poetry run pytest tests/unit/fairdm/core/test_models.py

# All tests in an app
poetry run pytest tests/integration/fairdm/core/

# Specific test function
poetry run pytest tests/unit/fairdm/core/test_models.py::test_project_creation__with_valid_data__creates_project
```

## Using Test Markers

FairDM uses pytest markers to categorize tests. See [Test Organization](test-organization.md#test-markers) for all markers.

### Run by Marker

```bash
# Unit tests only (no database access)
poetry run pytest -m unit

# Integration tests only (database required)
poetry run pytest -m integration

# Contract tests only (API validation)
poetry run pytest -m contract

# Slow tests only (>1 second)
poetry run pytest -m slow

# Skip slow tests
poetry run pytest -m "not slow"
```

### Combine Markers

```bash
# Unit tests that are not slow
poetry run pytest -m "unit and not slow"

# Integration or contract tests
poetry run pytest -m "integration or contract"
```

## Verbose Output

### Basic Verbose Mode

```bash
# Show test names as they run
poetry run pytest -v

# Show even more detail (test docstrings, fixtures)
poetry run pytest -vv
```

**Example output**:

```text
tests/unit/fairdm/core/test_models.py::test_project_creation__with_valid_data__creates_project PASSED
tests/unit/fairdm/core/test_models.py::test_project_validation__missing_title__raises_error PASSED
```

### Show Print Statements

```bash
# Show print() and logging output from passing tests
poetry run pytest -s

# Combine with verbose mode
poetry run pytest -vv -s
```

Use `-s` when debugging test failures to see intermediate values.

### Show Captured Output on Failure

By default, pytest captures `stdout` and `stderr` and only shows them for failing tests:

```bash
# Default behavior (captured output shown on failure)
poetry run pytest

# Disable capture entirely (show all output immediately)
poetry run pytest --capture=no
```

## Database Management

### Transaction Rollback (Default)

By default, pytest-django wraps each test in a transaction and rolls it back:

```bash
poetry run pytest
```

- **Fast**: No database cleanup overhead
- **Isolated**: Each test starts with clean state
- **Limitation**: Cannot test transaction commit behavior

See [Database Strategy](database-strategy.md#transaction-rollback) for details.

### Reuse Database

Speed up test runs by reusing the test database across sessions:

```bash
# Create database once, reuse on subsequent runs
poetry run pytest --reuse-db
```

**When to use**:

- **Frequent local testing**: Avoid database creation overhead
- **Stable migrations**: Database schema hasn't changed

**When to recreate**:

- After adding/modifying migrations
- After changing database settings

**Recreate database explicitly**:

```bash
# Force database recreation
poetry run pytest --create-db
```

### Parallel Testing

Run tests in parallel using `pytest-xdist` (not installed by default):

```bash
# Install pytest-xdist
poetry add --group dev pytest-xdist

# Run tests in parallel (auto-detect CPU count)
poetry run pytest -n auto

# Run with specific worker count
poetry run pytest -n 4
```

**Note**: Each worker gets its own database (`test_fairdm_gw0`, `test_fairdm_gw1`, etc.).

## Test Selection Strategies

### Run Last Failed Tests

```bash
# Re-run only tests that failed in the last run
poetry run pytest --lf

# Run failed tests first, then all others
poetry run pytest --ff
```

Useful for debugging failures without re-running the entire suite.

### Run Tests Matching Keyword

```bash
# Run tests with "project" in the name
poetry run pytest -k project

# Run tests with "validation" but not "slow"
poetry run pytest -k "validation and not slow"
```

**Example**:

```bash
# Matches: test_project_creation, test_project_validation
# Skips: test_dataset_creation
poetry run pytest -k project
```

### Stop on First Failure

```bash
# Stop immediately on first failure
poetry run pytest -x

# Stop after 3 failures
poetry run pytest --maxfail=3
```

Useful for fixing errors incrementally.

## Coverage Reporting

Run tests with coverage tracking:

```bash
# Terminal report with missing line numbers
poetry run pytest --cov=fairdm --cov-report=term-missing

# HTML report (open htmlcov/index.html)
poetry run pytest --cov=fairdm --cov-report=html

# XML report (for CI/CD)
poetry run pytest --cov=fairdm --cov-report=xml
```

See [Coverage](coverage.md) for detailed coverage guide.

### Coverage by Test Layer

```bash
# Unit test coverage
poetry run pytest tests/unit/ --cov=fairdm --cov-report=term-missing

# Integration test coverage
poetry run pytest tests/integration/ --cov=fairdm --cov-report=term-missing
```

This shows which test layers cover which code paths.

## Common Workflows

### Quick Feedback Loop

```bash
# Fast: Unit tests only, no coverage, stop on first failure
poetry run pytest tests/unit/ -x --ff
```

### Pre-Commit Checks

```bash
# Comprehensive: All tests with coverage
poetry run pytest --cov=fairdm --cov-report=term-missing
```

### Debugging Failed Test

```bash
# Verbose, show prints, stop on first failure, show locals
poetry run pytest -vv -s -x --showlocals

# Use Python debugger (pdb) on failure
poetry run pytest --pdb
```

**Using `--showlocals`**: Shows local variable values when tests fail.

**Using `--pdb`**: Drops into Python debugger on failure (type `help` for commands).

### CI/CD Simulation

```bash
# Recreate database, run all tests, generate XML coverage
poetry run pytest --create-db --cov=fairdm --cov-report=xml --cov-report=term
```

## Configuration

FairDM's pytest settings are in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "tests.settings"
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
testpaths = ["tests"]
markers = [
    "unit: Unit tests (isolated logic, no database)",
    "integration: Integration tests (database, file system)",
    "contract: Contract tests (API validation, external contracts)",
    "slow: Tests that take >1 second to run",
]
addopts = [
    "--strict-markers",
    "--tb=short",
    "--disable-warnings",
]
```

**Key settings**:

- **`DJANGO_SETTINGS_MODULE`**: Test-specific Django settings
- **`testpaths`**: Only discover tests in `tests/` directory
- **`--strict-markers`**: Prevent typos in marker names
- **`--tb=short`**: Concise traceback format

## Troubleshooting

### Tests Can't Import FairDM Modules

**Symptom**: `ModuleNotFoundError: No module named 'fairdm'`

**Cause**: FairDM not installed in Poetry environment.

**Solution**:

```bash
poetry install
```

### Database Permission Errors

**Symptom**: `django.db.utils.OperationalError: permission denied to create database`

**Cause**: Test database user lacks `CREATEDB` privilege.

**Solution**:

```bash
# Grant CREATEDB to test user (PostgreSQL)
ALTER USER fairdm_test CREATEDB;
```

Or configure `tests/settings.py` to use SQLite:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
```

### Migrations Not Applied

**Symptom**: `django.db.utils.ProgrammingError: relation "fairdm_project" does not exist`

**Cause**: Test database missing migrations.

**Solution**:

```bash
# Recreate test database with migrations
poetry run pytest --create-db
```

### Slow Test Runs

**Symptoms**:

- Tests take >10 seconds even for small suites
- Database creation happens every run

**Solutions**:

```bash
# Reuse database across test runs
poetry run pytest --reuse-db

# Run unit tests only (no database)
poetry run pytest tests/unit/

# Run in parallel
poetry add --group dev pytest-xdist
poetry run pytest -n auto
```

### Confusing Test Output

**Symptom**: Can't tell which test is running or why it failed.

**Solutions**:

```bash
# Show test names as they run
poetry run pytest -v

# Show captured output (prints, logs)
poetry run pytest -s

# Show local variables on failure
poetry run pytest --showlocals
```

## Best Practices

### ✅ DO

**Run unit tests frequently**:

```bash
# Fast feedback loop (2-5 seconds)
poetry run pytest tests/unit/ -x
```

**Use `--reuse-db` for local development**:

```bash
# Saves 2-3 seconds per run
poetry run pytest --reuse-db
```

**Run full suite before committing**:

```bash
# Comprehensive validation
poetry run pytest --cov=fairdm --cov-report=term-missing
```

**Use markers to focus on relevant tests**:

```bash
# Working on API? Test contracts only
poetry run pytest -m contract
```

### ❌ DON'T

**Don't skip database recreation after migrations**:

```bash
# Bad: Outdated schema causes cryptic errors
poetry run pytest --reuse-db  # After adding migration

# Good: Recreate database
poetry run pytest --create-db
```

**Don't run integration tests in the inner loop**:

```bash
# Bad: Slow feedback (10-30 seconds)
poetry run pytest tests/integration/ -x

# Good: Fast unit tests first (2-5 seconds)
poetry run pytest tests/unit/ -x
```

**Don't ignore test warnings**:

```bash
# Bad: Warnings hidden, bugs lurk
poetry run pytest --disable-warnings

# Good: Fix warnings incrementally
poetry run pytest  # Shows warnings
```

## Further Reading

```{seealso}
- [Test Layers](test-layers.md) - Understand unit, integration, and contract test types
- [Test Organization](test-organization.md) - Directory structure and naming conventions
- [Coverage](coverage.md) - Measure and interpret test coverage
- [Database Strategy](database-strategy.md) - Transaction management and test isolation
- [pytest Documentation](https://docs.pytest.org/) - Official pytest documentation
```

## Examples

### Example: Debug Failing Integration Test

```bash
# 1. Run only the failing test with verbose output
poetry run pytest tests/integration/fairdm/core/test_api.py::test_create_project -vv -s

# 2. Show local variables on failure
poetry run pytest tests/integration/fairdm/core/test_api.py::test_create_project --showlocals

# 3. Drop into debugger on failure
poetry run pytest tests/integration/fairdm/core/test_api.py::test_create_project --pdb
```

### Example: Pre-Commit Validation

```bash
# Run all tests with coverage, stop on first failure
poetry run pytest --cov=fairdm --cov-report=term-missing -x

# If all pass, check HTML coverage for gaps
poetry run pytest --cov=fairdm --cov-report=html
# Open htmlcov/index.html
```

### Example: Performance Testing

```bash
# Find slow tests (>1 second)
poetry run pytest --durations=10

# Mark slow tests and skip them
poetry run pytest -m "not slow"
```

### Example: Contract Validation

```bash
# Run only contract tests with verbose output
poetry run pytest -m contract -vv

# Verify API responses match OpenAPI spec
poetry run pytest tests/contract/test_api_contract.py -vv
```
