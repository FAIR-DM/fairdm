# Python Code Development

```{admonition} You are here
:class: tip
**Contributing Guide** → Python Code Development

This page covers quality gates and development practices for FairDM framework contributions. If you landed here from a search, start with the [Contributing Guide overview](index.md) to understand the framework contributor role and [Before You Start](before_you_start.md) for environment setup.
```

This guide covers the quality gates and development practices for contributing Python code to FairDM. All contributions must pass these quality checks before being merged.

## Quality Gates Overview

FairDM enforces four core quality gates to maintain code quality, consistency, and documentation:

1. **Tests**: All code must have passing unit tests
2. **Type Checking**: Code must pass mypy type checking
3. **Linting**: Code must pass ruff linting checks
4. **Documentation Build**: Documentation must build without errors

```{important}
**Before submitting a pull request**, run all quality gates locally to ensure your changes will pass CI checks.
```

## 1. Running Tests

FairDM uses **pytest** for testing. Tests are located in the `tests/` directory.

### Run All Tests

```bash
poetry run pytest
```

### Run Tests for a Specific Module

```bash
poetry run pytest tests/test_core/
```

### Run a Specific Test File

```bash
poetry run pytest tests/test_core/test_models.py
```

### Run a Specific Test Function

```bash
poetry run pytest tests/test_core/test_models.py::test_project_creation
```

### Run Tests with Coverage

```bash
poetry run pytest --cov=fairdm --cov-report=html
```

This generates a coverage report in `htmlcov/index.html` showing which lines are tested.

```{tip}
**Test-Driven Development**: Write tests *before* implementing features. This helps clarify requirements and ensures your code is testable.
```

### Writing Good Tests

- **Test one thing per test**: Each test should verify a single behavior
- **Use descriptive names**: `test_project_requires_title` is better than `test_project1`
- **Arrange-Act-Assert**: Structure tests clearly (setup → execute → verify)
- **Use fixtures**: Leverage pytest fixtures for common setup (see `tests/conftest.py`)
- **Test edge cases**: Don't just test the happy path

**Example Test**:

```python
import pytest
from fairdm.core.models import Project

def test_project_requires_title():
    """Project creation should fail without a title."""
    with pytest.raises(ValueError):
        Project.objects.create(title="", description="Test project")

def test_project_str_returns_title():
    """Project string representation should return its title."""
    project = Project.objects.create(title="My Project", description="Test")
    assert str(project) == "My Project"
```

## 2. Type Checking with mypy

FairDM uses **mypy** to catch type errors before runtime.

### Run mypy

```bash
poetry run mypy fairdm
```

### Configuration

mypy is configured in `pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.10"
plugins = ["mypy_django_plugin.main"]
```

### Writing Type-Safe Code

- **Add type hints to function signatures**:

  ```python
  def create_sample(name: str, dataset_id: int) -> Sample:
      return Sample.objects.create(name=name, dataset_id=dataset_id)
  ```

- **Use `Optional` for nullable fields**:

  ```python
  from typing import Optional

  def get_project(project_id: int) -> Optional[Project]:
      try:
          return Project.objects.get(id=project_id)
      except Project.DoesNotExist:
          return None
  ```

- **Type Django querysets**:

  ```python
  from django.db.models import QuerySet

  def get_active_projects() -> QuerySet[Project]:
      return Project.objects.filter(status="active")
  ```

```{tip}
**Use django-stubs**: FairDM includes `django-stubs` for accurate Django type hints. If mypy complains about Django APIs, check the django-stubs documentation.
```

## 3. Linting with Ruff

FairDM uses **ruff** for fast Python linting and code formatting.

### Run Ruff Linter

```bash
poetry run ruff check fairdm
```

### Auto-Fix Issues

Many linting issues can be automatically fixed:

```bash
poetry run ruff check --fix fairdm
```

### Configuration

Ruff is configured in `pyproject.toml`:

```toml
[tool.ruff]
line-length = 120
select = ["E", "F", "I", "N", "W", "C90", "UP", "B", "A", "C4", "DJ", "RUF"]
ignore = ["E501", "E731", "RUF012", "TRY003", "A003", "F403", "F405", "C901"]
```

### Common Linting Rules

- **E/F**: PEP 8 style and syntax errors
- **I**: Import sorting (isort-compatible)
- **N**: PEP 8 naming conventions
- **B**: Bugbear (common Python bugs and design problems)
- **DJ**: Django-specific linting rules
- **UP**: Upgrade syntax for newer Python versions

### Import Sorting

Ruff automatically sorts imports. The expected order is:

1. Standard library imports
2. Third-party imports (Django, etc.)
3. Local application imports

**Example**:

```python
import os
from pathlib import Path

from django.db import models
from django.contrib.auth import get_user_model

from fairdm.core.models import Project
from fairdm.utils import generate_slug
```

## 4. Building Documentation

FairDM uses **Sphinx** with the **pydata-sphinx-theme** for documentation.

### Build Documentation Locally

```bash
poetry run sphinx-build -b html docs docs/_build/html
```

Open `docs/_build/html/index.html` in your browser to view the built documentation.

### Check for Documentation Errors

```bash
poetry run sphinx-build -W -b html docs docs/_build/html
```

The `-W` flag treats warnings as errors, ensuring all documentation issues are caught.

### Live Documentation Server

For live reloading while editing docs:

```bash
poetry run sphinx-autobuild docs docs/_build/html
```

Open [http://localhost:8000](http://localhost:8000) to view live documentation updates.

### Writing Good Documentation

- **Use Markdown**: FairDM docs use MyST Markdown (`.md` files)
- **Follow the style guide**: See [Documentation Style Guide](../more/documentation_style.md) for formatting conventions
- **Include code examples**: Show users *how* to use features, not just what they do
- **Cross-reference liberally**: Link to related pages and API docs
- **Use directives**: Leverage Sphinx directives like `{tip}`, `{warning}`, `{seealso}` for clarity

**Example Documentation**:

````markdown
# Registering Custom Models

To register a custom Sample model with the FairDM registry:

```python
from fairdm.registry import registry, SampleConfig
from myapp.models import RockSample

registry.register(
    RockSample,
    config=SampleConfig(
        list_fields=["name", "collection_date", "rock_type"],
        filter_fields=["rock_type", "collection_date"]
    )
)
```

```{tip}
If you don't provide a `SampleConfig`, FairDM will auto-generate sensible defaults based on your model fields.
```

```{seealso}
For advanced registry customization, see [Registry API Reference](../api/registry.md).
```
````

## Running All Quality Gates at Once

To run all quality gates in one command:

```bash
poetry run pytest && \
poetry run mypy fairdm && \
poetry run ruff check fairdm && \
poetry run sphinx-build -W -b html docs docs/_build/html
```

If all commands succeed, your code is ready for a pull request.

```{tip}
**Use pre-commit hooks**: Install pre-commit hooks to automatically run linting and type checking before each commit:

```bash
poetry run pre-commit install
```

This catches issues early and prevents CI failures.
```

## Code Style Guidelines

### General Python Style

- **Maximum line length**: 120 characters
- **Use f-strings**: Prefer `f"Hello {name}"` over `"Hello {}".format(name)` or `"Hello %s" % name`
- **Use pathlib**: Prefer `Path` over `os.path` for file operations
- **Avoid bare except**: Always catch specific exceptions

**Good**:

```python
from pathlib import Path

def read_config(config_path: Path) -> dict:
    try:
        with config_path.open() as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
```

**Bad**:

```python
import os

def read_config(config_path):
    try:
        with open(config_path) as f:
            return json.load(f)
    except:
        return {}
```

### Django-Specific Style

- **Fat models, thin views**: Business logic belongs in models, managers, or services—not views
- **Use Django ORM efficiently**: Leverage `select_related()` and `prefetch_related()` to avoid N+1 queries
- **Follow Django conventions**: Use `get_absolute_url()`, `__str__()`, `Meta` classes, etc.
- **Use lifecycle hooks**: Prefer `django-lifecycle` over signals for model state transitions

**Example**:

```python
from django.db import models
from django_lifecycle import LifecycleModel, hook, AFTER_CREATE

class Sample(LifecycleModel):
    name = models.CharField(max_length=255)
    dataset = models.ForeignKey("Dataset", on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("sample-detail", kwargs={"pk": self.pk})

    @hook(AFTER_CREATE)
    def log_creation(self):
        """Log sample creation for audit trail."""
        logger.info(f"Sample {self.name} created in dataset {self.dataset.title}")
```

## Next Steps

- **[Understand the contribution workflow](getting_started.md)**: Learn how to create issues, branches, and pull requests
- **[Review the FairDM constitution](https://github.com/FAIR-DM/fairdm/blob/main/.specify/memory/constitution.md)**: Align your contributions with FairDM's core principles

```{seealso}
**Frontend Development**: If you're working on templates or JavaScript, see [Frontend Development Guide](frontend_dev.md) for additional quality gates (djlint, ESLint, etc.).
```

