# Test Coverage

Test coverage measures which parts of your code are executed during test runs. FairDM uses **coverage.py** integrated with pytest to track and report coverage.

:::{admonition} Coverage Philosophy
:class: tip

Coverage is a **diagnostic tool**, not a quality metric. High coverage doesn't guarantee good tests - it only shows which lines were executed. Use coverage to:

- **Identify untested code paths**: Find missing edge cases, error conditions, and validation logic
- **Guide test creation**: Prioritize testing critical business logic over boilerplate
- **Detect dead code**: Discover unused imports, unreachable branches, and legacy code

**Never chase coverage percentages** - focus on testing meaningful behavior first, then use coverage to find gaps.
:::

## Running Coverage

### Basic Coverage Report

Run tests with coverage tracking:

```bash
poetry run pytest --cov=fairdm --cov-report=term-missing
```

This shows:

- **Coverage percentage** per module
- **Missing line numbers** for uncovered code
- **Total coverage** across the project

### HTML Coverage Report

Generate an interactive HTML report:

```bash
poetry run pytest --cov=fairdm --cov-report=html
```

Open `htmlcov/index.html` in your browser to:

- Browse coverage by module
- See line-by-line execution counts
- Identify uncovered branches (if/else paths)

### Coverage by Test Layer

Check coverage from specific test layers:

```bash
# Unit test coverage only
poetry run pytest tests/unit/ --cov=fairdm --cov-report=term-missing

# Integration test coverage only
poetry run pytest tests/integration/ --cov=fairdm --cov-report=term-missing

# Contract test coverage only
poetry run pytest tests/contract/ --cov=fairdm --cov-report=term-missing
```

This helps identify which test layers cover which code paths.

## Interpreting Coverage Reports

### Terminal Report Example

```text
Name                                Stmts   Miss  Cover   Missing
-----------------------------------------------------------------
fairdm/__init__.py                      5      0   100%
fairdm/core/models.py                 124     18    85%   45-52, 89-93, 201-205
fairdm/core/views.py                   68     12    82%   34-38, 91-96
fairdm/registry/base.py                89      5    94%   112-115
-----------------------------------------------------------------
TOTAL                                 286     35    88%
```

**Key columns**:

- **Stmts**: Total executable statements in the file
- **Miss**: Number of statements not executed during tests
- **Cover**: Percentage of statements covered
- **Missing**: Line numbers of uncovered code

### HTML Report Features

The HTML report (generated with `--cov-report=html`) provides:

1. **File-level overview**: Coverage percentage for each module
2. **Line-by-line highlighting**:
   - **Green**: Line executed during tests
   - **Red**: Line not executed
   - **Yellow**: Partial branch coverage (e.g., only `if` tested, not `else`)
3. **Branch coverage**: Shows which if/else paths were taken
4. **Hotspot detection**: Sort by coverage percentage to find gaps

## Coverage Configuration

FairDM's coverage settings are in `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["fairdm"]
omit = [
    "*/migrations/*",
    "*/tests/*",
    "*/conftest.py",
    "*/__pycache__/*",
    "*/venv/*",
    "*/virtualenv/*",
]
branch = true

[tool.coverage.report]
precision = 2
show_missing = true
skip_covered = false
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "def __str__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
    "class .*\\bProtocol\\):",
    "@(abc\\.)?abstractmethod",
]
```

**Key settings**:

- **`source`**: Track coverage for `fairdm/` package
- **`omit`**: Exclude migrations, tests, and virtual environments
- **`branch = true`**: Enable branch coverage (if/else paths)
- **`exclude_lines`**: Ignore defensive code, debug helpers, and type hints

## Coverage Best Practices

### ✅ DO

**Use coverage to identify untested edge cases**:

```python
# Coverage reveals missing else branch
def calculate_discount(user, amount):
    if user.is_premium:
        return amount * 0.1
    # Coverage shows this line not tested ⚠️
    return 0
```

**Test critical business logic first**:

```python
# Prioritize testing data validation and calculations
def test_sample_validation__invalid_coordinates__raises_error():
    with pytest.raises(ValidationError):
        Sample(latitude=91.0)  # Out of range
```

**Use branch coverage to test all paths**:

```python
# Ensure both if and else branches are tested
@pytest.mark.parametrize("is_public,expected", [
    (True, 200),   # Tests if branch
    (False, 403),  # Tests else branch
])
def test_dataset_access__public_vs_private__correct_status(is_public, expected):
    ...
```

### ❌ DON'T

**Don't write tests just to increase coverage**:

```python
# Bad: Testing implementation details, not behavior
def test_private_method__exists():
    obj = MyClass()
    assert hasattr(obj, '_internal_helper')  # Meaningless
```

**Don't test framework code**:

```python
# Bad: Testing Django's save() method
def test_model_save__calls_super():
    project = ProjectFactory()
    project.save()  # Django already tests this
```

**Don't chase 100% coverage blindly**:

```python
# Bad: Testing defensive code that should never execute
def test_impossible_condition__never_happens():
    # This branch is unreachable by design
    ...
```

## Coverage Goals

:::{admonition} Target Coverage by Module Type
:class: note

FairDM recommends these **minimum coverage targets**:

- **Business logic** (models, services, utils): **≥ 90%**
- **Views and APIs**: **≥ 80%**
- **Django configuration** (settings, urls): **≥ 60%**
- **Template tags and filters**: **≥ 85%**

These are **guidelines**, not strict requirements. Meaningful tests are more important than hitting percentages.
:::

**What should be 100% covered?**:

- Data validation logic (model `clean()` methods)
- Permission checks and authorization logic
- Financial calculations or scientific algorithms
- API serialization/deserialization

**What doesn't need 100% coverage?**:

- Django boilerplate (model `__str__`, admin registration)
- Error messages and logging statements
- Defensive `NotImplementedError` stubs
- Type hints and protocols

## Coverage in CI/CD

FairDM's CI pipeline (GitHub Actions) runs coverage checks:

```yaml
- name: Run tests with coverage
  run: poetry run pytest --cov=fairdm --cov-report=xml --cov-report=term

- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

**Coverage enforcement**:

- **Coverage reports** are uploaded to Codecov for tracking trends
- **Failing coverage** does not block PRs (guidance, not enforcement)
- **Review coverage changes** in PR comments to catch accidental gaps

## Troubleshooting

### Coverage Shows 0% Despite Tests Passing

**Cause**: Coverage not tracking the right source directory.

**Solution**: Verify `[tool.coverage.run]` source matches your package name:

```toml
[tool.coverage.run]
source = ["fairdm"]  # Must match your package directory
```

### Coverage Includes Test Files

**Cause**: `omit` patterns not excluding `tests/`.

**Solution**: Add test exclusions:

```toml
[tool.coverage.run]
omit = ["*/tests/*", "*/conftest.py"]
```

### Missing Lines Appear Covered

**Cause**: Branch coverage not enabled (only statement coverage).

**Solution**: Enable branch coverage:

```toml
[tool.coverage.run]
branch = true
```

Run with `--cov-report=html` to see branch visualization.

### Coverage Drops After Adding Tests

**Cause**: New tests import modules that weren't previously imported, revealing untested code.

**Solution**: This is expected! Coverage helps discover gaps. Add tests for the newly revealed untested code.

## Further Reading

```{seealso}
- [Running Tests](running-tests.md) - CLI options for test execution and reporting
- [Test Quality](test-quality.md) - Writing meaningful tests that coverage can't measure
- [Fixtures & Factories](fixtures.md) - Efficient test setup reduces boilerplate coverage
- [Coverage.py Documentation](https://coverage.readthedocs.io/) - Official tool documentation
```

## Examples

### Finding Untested Error Handling

```python
# Initial implementation (missing test)
def process_sample(sample_data):
    if not sample_data.get('latitude'):
        raise ValidationError("Latitude required")  # ⚠️ Not covered
    return Sample.objects.create(**sample_data)

# Coverage reveals missing test
def test_process_sample__missing_latitude__raises_error():
    with pytest.raises(ValidationError, match="Latitude required"):
        process_sample({})  # ✅ Now covered
```

### Using Coverage to Find Dead Code

```python
# Coverage shows this import is never used
from django.core.cache import cache  # ⚠️ 0% coverage

# Remove dead import
# from django.core.cache import cache  # Deleted
```

### Testing All Branches

```python
def get_sample_access_level(user, sample):
    if sample.project.is_public:
        return "read"
    if user == sample.project.owner:
        return "write"
    # Coverage reveals missing test for this branch ⚠️
    return "none"

# Add test for third branch
def test_get_sample_access_level__private_project_non_owner__returns_none():
    user = UserFactory()
    project = ProjectFactory(is_public=False)  # Not owned by user
    sample = SampleFactory(project=project)

    assert get_sample_access_level(user, sample) == "none"  # ✅ Covered
```
