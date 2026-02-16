---
name: fairdm-testing
description: >-
  Write, review, and maintain tests for the FairDM Django project. Use when asked to create
  new tests, add test coverage for a module, review existing tests, fix failing tests, or
  refactor test code. Covers pytest conventions, factory-boy usage, fixture design, test
  structure (flat mirror of fairdm/ source tree), Django model/form/view/admin/filter testing
  patterns, registry testing with clean-state fixtures, and performance guard patterns using
  query-count assertions. Also use when discussing testing strategy, test organization, or
  when creating new fairdm modules that need accompanying tests.
---

# FairDM Testing

## Stack

- **pytest** + **pytest-django** — test runner and Django integration
- **factory-boy** — model instance generation
- **Coverage.py** — coverage reporting (configured in pyproject.toml)

Never use `unittest`, `TestCase`, or `setUp/tearDown`.

## Directory Structure

Tests mirror the `fairdm/` source tree with `test_` prefixes:

```
fairdm/core/project/models.py    → tests/test_core/test_project/test_models.py
fairdm/contrib/contributors/     → tests/test_contrib/test_contributors/
fairdm/registry/config.py        → tests/test_registry/test_config.py
fairdm/plugins.py                → tests/test_plugins.py
fairdm/db/fields.py              → tests/test_db/test_fields.py
```

See [references/structure-map.md](references/structure-map.md) for the complete mapping.

Rules:

- Test directories: `test_<dirname>/`
- Test files: `test_<module>.py`
- Every directory needs an `__init__.py`
- No layer separation (no `unit/`, `integration/`, `contract/` subdirectories)
- Unit and integration tests for a module live together in the same file

## Running Tests

```bash
poetry run pytest                          # all tests
poetry run pytest tests/test_core/         # one subtree
poetry run pytest -k "test_project"        # by name
poetry run pytest -m slow                  # only slow-marked tests
poetry run pytest --no-header -q           # quiet output
```

## Factories

Import from the canonical path:

```python
from fairdm.factories import (
    ContributorFactory, DatasetFactory, MeasurementFactory,
    OrganizationFactory, PersonFactory, ProjectFactory,
    SampleFactory, UserFactory,
)
```

### Factory Opt-In Pattern

FairDM factories follow an **opt-in pattern** for creating related metadata (descriptions, dates):

**Key Principle**: By default, factories create only required fields. No descriptions or dates are auto-created.

**Why Opt-In?**

1. **Prevents unique constraint violations** — Models have `unique_together` on `(related, type)`. Auto-creating metadata could conflict with test-specific data.
2. **Minimizes test data** — Most tests don't need metadata. Creating it by default adds unnecessary DB records and slows tests.
3. **Explicit control** — When you need metadata, you explicitly control count and types.

**Usage Patterns**:

```python
# Minimal (no metadata) - DEFAULT behavior
project = ProjectFactory()
assert project.descriptions.count() == 0
assert project.dates.count() == 0

# With metadata (opt-in via kwargs)
project = ProjectFactory(descriptions=2, dates=1)
assert project.descriptions.count() == 2
assert project.dates.count() == 1

# Custom types (validated against model VOCABULARY)
project = ProjectFactory(
    descriptions=3,
    descriptions__types=["Abstract", "Introduction", "Objectives"]
)

# All core factories support this pattern
dataset = DatasetFactory(descriptions=2, dates=1)
sample = SampleFactory(descriptions=1, dates=2)
measurement = MeasurementFactory(descriptions=2)
```

**Vocabulary Validation**:

All description/date types are validated against the model's `VOCABULARY.values`:

```python
# ✓ Valid - types exist in ProjectDescription.VOCABULARY
project = ProjectFactory(
    descriptions=2,
    descriptions__types=["Abstract", "Methods"]
)

# ✗ Raises ValueError - "InvalidType" not in VOCABULARY
project = ProjectFactory(
    descriptions=1,
    descriptions__types=["InvalidType"]
)
```

**Available VOCABULARY types**:

- `ProjectDescription.VOCABULARY.values`: Abstract, Introduction, Background, Objectives, ExpectedOutput, Conclusions, Other (+ sample/measurement-specific types)
- `ProjectDate.VOCABULARY.values`: Start, End
- `DatasetDescription.VOCABULARY.values`: Similar to Project
- `DatasetDate.VOCABULARY.values`: Check model for available types
- `SampleDescription.VOCABULARY.values`: Includes SampleCollection, SamplePreparation, etc.
- `MeasurementDescription.VOCABULARY.values`: Includes MeasurementConditions, MeasurementSetup, etc.

**Batch Creation with Metadata**:

```python
# All projects get 2 descriptions and 1 date
projects = ProjectFactory.create_batch(5, descriptions=2, dates=1)

# Custom types for all
datasets = DatasetFactory.create_batch(
    3,
    descriptions=2,
    descriptions__types=["Abstract", "Methods"]
)
```

### Factory Patterns (General)

- `SubFactory` for FK relations — never manually create parent objects when a factory exists
- `factory.Sequence(lambda n: f"value{n}")` for unique fields
- `create_batch(n)` for bulk creation
- Traits for alternate configurations

Portal-specific factories (e.g. demo app custom samples) are mapped via `FAIRDM_FACTORIES`
in test settings.

## Fixtures

### Built-in pytest-django fixtures

Use directly — no need to redeclare: `db`, `client`, `rf`, `admin_user`,
`django_user_model`, `django_assert_num_queries`.

### Project fixtures (tests/fixtures/pytest_fixtures.py)

```python
def test_something(user):           # UserFactory()
def test_something(project):        # ProjectFactory(owner=user)
def test_something(project_with_datasets):  # (project, [3 datasets])
```

### Registry fixtures (tests/test_registry/conftest.py)

```python
def test_registration(clean_registry):     # empty registry, cleaned after test
def test_dynamic_model(unique_app_label):  # "test_app_<hex>" for Meta.app_label
# cleanup_test_app_models runs autouse — removes test_app_* from Django app registry
```

Prefer a factory call over a fixture when the fixture would just wrap a single factory call.

## Test Organization

Group tests into classes by subject. One class per logical unit under test:

```python
@pytest.mark.django_db
class TestProjectModel:
    def test_creation_with_required_fields(self): ...
    def test_uuid_is_unique(self): ...
    def test_status_choices(self): ...

@pytest.mark.django_db
class TestProjectCreateForm:
    def test_valid_with_required_fields(self): ...
    def test_invalid_without_name(self): ...
```

Naming: `test_<what_is_being_tested>` — descriptive, no abbreviations.

## Test Style

- `@pytest.mark.django_db` on every class or function that touches the database
- Arrange–Act–Assert, separated by blank lines
- One logical assertion per test (unless tightly coupled)
- Deterministic and isolated — no cross-test state, no time-dependent logic
- `@pytest.mark.parametrize` for repeated logic with different inputs
- `@pytest.mark.slow` for tests that take >1 second

## Performance Tests

**Never** use wall-clock timing assertions (`assert elapsed < 0.1`).

Use query-count guards instead:

```python
def test_list_view_query_count(client, django_assert_num_queries):
    ProjectFactory.create_batch(10)
    with django_assert_num_queries(3):
        client.get("/projects/")
```

Or algorithmic complexity guards (assert O(n) not O(n²)).

## Exemplar Patterns

See [references/exemplar-patterns.md](references/exemplar-patterns.md) for complete
tested patterns covering:

- Model tests (creation, constraints, field validation, relationships)
- Form tests (valid/invalid data, field requirements, business rules)
- View tests (GET/POST, permissions, redirects, context data)
- Admin tests (registration, list display, actions)
- Filter tests (queryset filtering, filterset configuration)
- Registry tests (registration, validation, dynamic models)

## What NOT to Do

See [references/anti-patterns.md](references/anti-patterns.md) for common mistakes
and their corrections.

## Test Settings (tests/settings.py)

Key configuration (already set up — do not modify without reason):

- In-memory SQLite database
- Migrations disabled via `DisableMigrations` class
- MD5 password hasher (fast, insecure — test-only)
- DummyCache backend
- `fairdm.setup(apps=["fairdm_demo"])` loads the demo app
- `FAIRDM_FACTORIES` maps demo models to their factories

## Checklist for New Tests

1. Identify the source module → derive the test file path from the mirror structure
2. Create the test file with `__init__.py` in any new directories
3. Import from `fairdm.factories` for model instances
4. Group tests in classes by subject (`TestXxxModel`, `TestXxxForm`, etc.)
5. Mark DB-accessing tests with `@pytest.mark.django_db`
6. Run `poetry run pytest <test_file>` to verify
7. Ensure coverage does not decrease

## Historical Note

This skill file supersedes the original `specs/002-testing-strategy` spec (created January 2026, removed February 2026). The skill format provides more maintainable, agent-friendly documentation of FairDM's testing conventions.
