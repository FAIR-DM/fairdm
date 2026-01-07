# Phase 0: Research - Testing Strategy & Fixtures

**Feature**: 004-testing-strategy-fixtures
**Date**: 2026-01-06
**Researcher**: AI Agent

## Research Overview

This document consolidates research findings for establishing FairDM's testing strategy, covering pytest configuration, fixture patterns, coverage philosophy, test quality metrics, and database strategies for Django projects.

---

## 1. Pytest Configuration Best Practices

### Investigation Focus

- Optimal pytest.ini vs pyproject.toml configuration for Django projects
- Test discovery patterns and performance optimization
- Pytest plugin ecosystem (pytest-django, pytest-xdist for parallel execution)

### Decision: Use pyproject.toml with pytest-django

**Rationale**:

- **Centralized configuration**: pyproject.toml is the modern Python standard (PEP 518) for tool configuration, consolidating pytest, coverage, ruff, and other tools in one file
- **pytest-django integration**: Provides Django-specific features like `--reuse-db` (reuses test database between runs for speed) and `--no-migrations` (uses existing migrations instead of recreating)
- **Strict markers**: `--strict-markers` enforces that all pytest markers (unit, integration, contract, slow) must be registered, preventing typos
- **Test discovery optimization**: Explicit `testpaths = ["tests"]` and naming patterns (`test_*.py`, `test_*` functions) limit filesystem scanning

**Configuration Example**:

```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "tests.settings"
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
testpaths = ["tests"]
markers = [
    "unit: Unit tests (fast, isolated)",
    "integration: Integration tests (database, cross-component)",
    "contract: Contract tests (API schemas, interoperability)",
    "slow: Tests that take > 1 second",
]
addopts = [
    "--strict-markers",
    "--reuse-db",
    "--no-migrations",
]
```

**Performance Optimizations**:

- **pytest-xdist**: Enables parallel test execution with `-n auto` (uses all CPU cores). Best for large test suites but adds complexity for debugging. Recommended for CI/CD, optional for local development.
- **--reuse-db**: Speeds up test runs by reusing the test database between sessions (from pytest-django)
- **--no-migrations**: Skips applying migrations in test database (assumes migrations are up-to-date)

**Alternatives Considered**:

- **pytest.ini**: Separate configuration file. Rejected because pyproject.toml provides centralized tool configuration
- **setup.cfg**: Legacy configuration format. Rejected in favor of modern pyproject.toml standard
- **Running without pytest-django**: Rejected because Django ORM integration, database fixtures, and transaction management require pytest-django

**References**:

- [pytest documentation](https://docs.pytest.org/)
- [pytest-django documentation](https://pytest-django.readthedocs.io/)
- [PEP 518 - pyproject.toml](https://peps.python.org/pep-0518/)

---

## 2. Factory-Boy Patterns for Django

### Investigation Focus

- Factory inheritance patterns for polymorphic Django models
- SubFactory and RelatedFactory patterns for complex relationships
- Fixture scope strategies (session vs module vs function)

### Decision: Use factory-boy with DjangoModelFactory base

**Rationale**:

- **Polymorphic model support**: Factory-boy supports factory inheritance matching Django model inheritance. For FairDM's polymorphic Sample and Measurement models, child factories inherit from base factories
- **Relationship handling**: SubFactory creates related objects on-demand; RelatedFactory creates reverse relationships. This mirrors Django's ForeignKey and reverse relations
- **Faker integration**: Built-in Faker support generates realistic test data (names, emails, addresses) reducing test brittleness from hardcoded values
- **Customization**: `factory.Sequence`, `factory.LazyAttribute`, and `factory.post_generation` hooks provide fine-grained control over test data generation

**Polymorphic Factory Pattern**:

```python
# Base factory for polymorphic parent
class SampleFactory(DjangoModelFactory):
    class Meta:
        model = "fairdm_core.Sample"

    name = factory.Faker("catch_phrase")
    project = factory.SubFactory(ProjectFactory)
    dataset = factory.SubFactory(DatasetFactory)

# Child factory for specific sample type
class RockSampleFactory(SampleFactory):
    class Meta:
        model = "fairdm_demo.RockSample"

    rock_type = factory.Faker("word")
    collection_date = factory.Faker("date_this_decade")
```

**SubFactory vs RelatedFactory**:

- **SubFactory**: For ForeignKey relationships. Creates the related object when the main factory is called

  ```python
  dataset = factory.SubFactory(DatasetFactory)  # Creates Dataset for Sample
  ```

- **RelatedFactory**: For reverse relationships. Creates related objects pointing back to the main object

  ```python
  class DatasetFactory(DjangoModelFactory):
      samples = factory.RelatedFactory(SampleFactory, 'dataset')  # Creates Samples for Dataset
  ```

**Fixture Scope Strategy**:

- **function scope** (default): Test isolation. Each test gets fresh objects. Use for most tests
- **module scope**: Shared across tests in one module. Use for expensive setup (e.g., loading large reference data) that doesn't mutate
- **session scope**: Shared across entire test suite. Use only for truly immutable data (e.g., lookup tables, configuration)

**Best Practice**: Prefer function scope for test isolation. Use module/session scope only when performance gains justify reduced isolation.

**Alternatives Considered**:

- **pytest fixtures only**: Rejected because fixtures require more boilerplate for complex object graphs. Factory-boy provides declarative syntax
- **Django fixtures (JSON/YAML)**: Rejected because they're brittle (break when models change) and don't support dynamic data generation
- **Manual object creation**: Rejected because it leads to test code duplication and harder maintenance

**References**:

- [factory-boy documentation](https://factoryboy.readthedocs.io/)
- [Factory-boy + Django best practices](https://factoryboy.readthedocs.io/en/stable/orms.html#django)

---

## 3. Coverage.py Configuration

### Investigation Focus

- Coverage measurement strategies that emphasize quality over quantity
- Branch coverage vs line coverage trade-offs
- Coverage reporting formats for developer feedback

### Decision: Line coverage as diagnostic tool, quality-first philosophy

**Rationale**:

- **Constitutional alignment**: Constitution v1.2.0 Principle V emphasizes test quality (meaningful, maintainable, reliable) over percentage targets
- **Diagnostic use**: Coverage identifies untested code paths, guiding where to add tests. Not a gate for merging code
- **Line coverage**: Simpler to understand and faster to compute than branch coverage. Branch coverage adds value for complex conditional logic but increases measurement overhead
- **Developer feedback**: HTML reports (`coverage html`) provide visual feedback. Terminal reports (`coverage report --show-missing`) integrate into development workflow

**Configuration Example**:

```toml
[tool.coverage.run]
source = ["fairdm"]
omit = [
    "*/tests/*",
    "*/migrations/*",
    "*/__pycache__/*",
    "*/conftest.py",
]

[tool.coverage.report]
precision = 1
show_missing = true
skip_covered = false
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if TYPE_CHECKING:",
    "raise AssertionError",
    "raise NotImplementedError",
]
```

**Quality-First Principles**:

- **Meaningful**: Tests validate actual behavior and requirements, not just "coverage"
- **Maintainable**: Tests are readable, follow conventions, use fixtures appropriately
- **Reliable**: Tests don't flake, have clear assertions, and fail for the right reasons

**When to use branch coverage**: Consider branch coverage for critical business logic with complex conditionals (e.g., permission checks, state machines). Adds overhead but catches edge cases in branching logic.

**Coverage Thresholds**: No hard minimum. Use coverage to find gaps, not as a quality gate. High coverage doesn't guarantee quality; low coverage highlights risk areas.

**Alternatives Considered**:

- **Hard 80% coverage requirement**: Rejected because it incentivizes superficial tests (hitting lines without validating behavior)
- **Branch coverage default**: Rejected because overhead isn't justified for most Django web application code
- **No coverage measurement**: Rejected because coverage provides valuable diagnostic information for identifying untested code

**References**:

- [coverage.py documentation](https://coverage.readthedocs.io/)
- [Martin Fowler - Test Coverage](https://martinfowler.com/bliki/TestCoverage.html)

---

## 4. Test Quality Metrics Beyond Coverage

### Investigation Focus

- Mutation testing tools for Python/Django
- Test maintainability metrics
- Test reliability patterns (avoiding flaky tests)

### Decision: Focus on qualitative metrics, consider mutation testing selectively

**Rationale**:

- **Mutation testing**: Tools like `mutmut` introduce bugs into code and verify tests catch them. Valuable for critical paths but expensive (slow, requires careful interpretation)
- **Maintainability**: Qualitative review (clear names, appropriate fixture use, minimal duplication, readable assertions) more practical than automated metrics
- **Reliability**: Flaky tests destroy trust. Patterns to avoid flakiness: avoid time-dependent assertions, use freezegun for time mocking, isolate database state

**Mutation Testing (mutmut)**:

- **Use case**: Validate test effectiveness for critical business logic (e.g., permission checks, financial calculations, data validation)
- **Not for**: General use across entire codebase (too slow, diminishing returns)
- **Example**:

  ```bash
  poetry add --group dev mutmut
  poetry run mutmut run --paths-to-mutate=fairdm/core/permissions.py
  ```

**Test Reliability Patterns**:

1. **Time-dependent tests**: Use `freezegun` to freeze time

   ```python
   from freezegun import freeze_time

   @freeze_time("2026-01-06 12:00:00")
   def test_timestamp_behavior():
       # Time is now frozen at 2026-01-06 12:00:00
   ```

2. **Database isolation**: pytest-django's `@pytest.mark.django_db` with transactional rollback ensures each test starts with clean state

3. **Flaky assertions**: Avoid comparing auto-generated values (UUIDs, timestamps). Use factories with deterministic values or assert on behavior, not exact values:

   ```python
   # Bad: Flaky because timestamp changes
   assert obj.created_at == datetime.now()

   # Good: Assert on behavior
   assert obj.created_at <= datetime.now()
   assert (datetime.now() - obj.created_at).seconds < 5
   ```

**Test Maintainability Checklist**:

- ✅ Test name describes behavior and condition: `test_save__with_invalid_data__raises_validation_error`
- ✅ Setup uses fixtures or factories, not duplicated code
- ✅ One logical assertion per test (multiple technical assertions OK if they validate one behavior)
- ✅ Failures produce clear, actionable error messages

**Alternatives Considered**:

- **Comprehensive mutation testing**: Rejected because runtime cost doesn't justify value for most code
- **Automated maintainability scoring**: Rejected because qualitative code review provides better signal
- **Ignoring flaky tests**: Rejected because flaky tests must be fixed or removed

**References**:

- [mutmut - mutation testing](https://mutmut.readthedocs.io/)
- [freezegun - time mocking](https://github.com/spulec/freezegun)
- [Google Testing Blog - Test Flakiness](https://testing.googleblog.com/)

---

## 5. Django Test Database Strategies

### Investigation Focus

- pytest-django database transaction strategies
- Test database creation/teardown performance optimization
- Fixture data loading strategies

### Decision: Session-level DB with per-test transaction rollback

**Rationale**:

- **Speed**: Creating database once per test session (not per test) dramatically speeds up test suite
- **Isolation**: pytest-django's transactional test database marks ensure each test starts with clean state via automatic rollback
- **Django compatibility**: Leverages Django's TestCase behavior (transaction rollback) without Django's TestCase class overhead

**Configuration**:

```python
# pytest.ini or pyproject.toml
[tool.pytest.ini_options]
addopts = ["--reuse-db", "--no-migrations"]

# conftest.py
import pytest

@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """
    Session-level database setup.
    Creates database once, loads any required reference data.
    """
    with django_db_blocker.unblock():
        # Load any required reference data here
        # e.g., Country.objects.bulk_create([...])
        pass

# Mark integration tests with database access
@pytest.mark.django_db
def test_sample_creation():
    sample = SampleFactory()
    assert Sample.objects.count() == 1
    # Automatic rollback after test
```

**pytest-django Database Markers**:

- `@pytest.mark.django_db`: Enables database access with transaction rollback
- `@pytest.mark.django_db(transaction=True)`: Enables transaction management (needed for testing transaction-aware code)
- No marker: Database access raises error

**Fixture Data Loading**:

1. **Session-level**: Load immutable reference data (countries, units, lookup tables) in `django_db_setup` fixture
2. **Per-test**: Use factory-boy to create test-specific data
3. **Avoid Django fixtures**: JSON/YAML fixtures brittle and don't support dynamic data

**Performance Optimizations**:

- `--reuse-db`: Reuses database between test runs (huge speedup for local development)
- `--no-migrations`: Uses existing migrations instead of applying them (speedup, assumes migrations are current)
- `--create-db`: Forces fresh database creation (use when migrations change)

**Alternatives Considered**:

- **In-memory SQLite**: Rejected because FairDM uses PostgreSQL-specific features; SQLite behavior differs
- **Per-test database creation**: Rejected because too slow (creating/destroying DB for each test)
- **Shared database state between tests**: Rejected because test isolation is critical for reliability

**References**:

- [pytest-django database documentation](https://pytest-django.readthedocs.io/en/latest/database.html)
- [Django TestCase documentation](https://docs.djangoproject.com/en/stable/topics/testing/tools/#testcase)

---

## Summary & Recommendations

### Key Decisions

1. **pytest + pyproject.toml**: Centralized configuration with Django-specific optimizations
2. **factory-boy**: Declarative fixture factories for complex object graphs, polymorphic model support
3. **Coverage as diagnostic tool**: No hard thresholds, focus on test quality (meaningful, maintainable, reliable)
4. **Qualitative quality metrics**: Code review for maintainability, selective mutation testing for critical paths
5. **Session-level DB with transaction rollback**: Speed + isolation for integration tests

### Implementation Priority

**Phase 1 (Foundation)**:

1. Configure pytest in pyproject.toml with markers for unit/integration/contract
2. Create base factory-boy factories for core FairDM models (Project, Dataset, Sample, Measurement)
3. Document test organization structure (`tests/{layer}/{app}/test_{module}.py`)
4. Configure coverage.py for diagnostic reporting

**Phase 2 (Quality)**:

1. Document test quality principles (meaningful, maintainable, reliable)
2. Create test examples demonstrating patterns for each layer
3. Establish fixture organization guidelines (scope, naming, documentation)
4. Create quickstart guide for contributors

**Phase 3 (Advanced)**:

1. Consider pytest-xdist for parallel test execution in CI/CD
2. Evaluate mutmut for critical business logic paths
3. Establish patterns for Cotton component testing with `django_cotton.render_component()`
4. Document pytest-playwright setup for UI testing

### Risks & Mitigations

| Risk                                  | Mitigation                                                                 |
| ------------------------------------- | -------------------------------------------------------------------------- |
| Developers chase coverage percentages | Emphasize quality in docs, code review for test meaningfulness            |
| Factory-boy complexity overwhelms     | Provide simple examples first, advanced patterns as needed                 |
| Test suite becomes slow               | Profile tests, optimize database access, consider pytest-xdist             |
| Flaky tests erode trust               | Enforce reliability patterns (freezegun, deterministic fixtures)           |
| Tests don't catch real bugs           | Use mutation testing selectively, review test assertions in code review    |

---

**Next Steps**: Proceed to Phase 1 to create data-model.md (test layer taxonomy formal definitions), quickstart.md (contributor quick reference), and contracts/ (test naming/organization contracts).
