# Testing Strategy

```{toctree}
:maxdepth: 2
:hidden:

quickstart
test-layers
test-quality
test-organization
fixtures
database-strategy
coverage
running-tests
```

FairDM follows a test-first development approach where tests are written before implementation code. This ensures code is designed for testability, encourages comprehensive coverage, and maintains high quality standards.

## Overview

This testing strategy provides contributors with:

- **5-minute quickstart**: Get writing tests immediately with practical examples
- **Clear test taxonomy**: Three distinct test layers (unit, integration, contract) with well-defined boundaries
- **Consistent organization**: Standardized directory structure and naming conventions
- **Reusable fixtures**: Factory-boy factories and pytest fixtures for efficient test setup
- **Quality focus**: Emphasis on meaningful, maintainable, and reliable tests over coverage percentages

## Quick Start

:::{admonition} New to FairDM testing?
:class: tip

Start with the [5-Minute Quickstart](quickstart.md) for a hands-on introduction. It covers:

- Choosing the right test layer
- Writing your first test
- Running tests with pytest
- Using factories for test data

[Get Started →](quickstart.md)
:::

## Quick Navigation

::::{grid} 1 1 2 2
:gutter: 3

:::{grid-item-card} {octicon}`list-unordered` Test Layers
:link: test-layers
:link-type: doc

Learn about unit, integration, and contract test layers and when to use each.
:::

:::{grid-item-card} {octicon}`checklist` Test Quality
:link: test-quality
:link-type: doc

Understand what makes tests meaningful, maintainable, and reliable.
:::

:::{grid-item-card} {octicon}`file-directory` Test Organization
:link: test-organization
:link-type: doc

Follow the standard directory structure and naming conventions.
:::

:::{grid-item-card} {octicon}`package` Fixtures & Factories
:link: fixtures
:link-type: doc

Use pytest fixtures and factory-boy factories for test data.
:::

:::{grid-item-card} {octicon}`database` Database Strategy
:link: database-strategy
:link-type: doc

Understand transaction rollback and session-level database management.
:::

:::{grid-item-card} {octicon}`graph` Coverage
:link: coverage
:link-type: doc

Use coverage.py as a diagnostic tool to identify untested code paths.
:::

:::{grid-item-card} {octicon}`play` Running Tests
:link: running-tests
:link-type: doc

Run tests locally with pytest and review coverage reports.
:::

::::

## Testing Philosophy

FairDM's testing approach is guided by these principles from the [FairDM Constitution](../../constitution.md):

:::{admonition} Principle V: Test-First Quality & Sustainability
:class: tip

**Test-first** development is **NON-NEGOTIABLE** for FairDM. All new features and bug fixes MUST follow the **Red → Green → Refactor** cycle:

1. **Red**: Write a failing test that defines desired behavior
2. **Green**: Write minimal code to make the test pass
3. **Refactor**: Improve code quality while maintaining green tests

**Test quality** is more important than coverage percentages. Tests must be:

- **Meaningful**: Test real behavior, not implementation details
- **Maintainable**: Clear intent, minimal duplication, easy to update
- **Reliable**: Deterministic, isolated, fast execution
:::

## 5-Minute Quickstart

New to FairDM testing? Follow these steps:

1. **Choose your test layer** ([decision tree](test-layers.md#decision-tree))
   - Testing isolated logic? → **Unit test**
   - Testing database interactions? → **Integration test**
   - Testing API contracts? → **Contract test**

2. **Place your test file** ([organization rules](test-organization.md))

   ```text
   tests/{layer}/{app_name}/test_{module}.py
   ```

3. **Name your test** ([naming convention](test-organization.md#test-naming))

   ```python
   def test_<behavior>__<condition>__<expected>():
       ...
   ```

4. **Use fixtures** ([fixture guide](fixtures.md))

   ```python
   from fairdm.factories import ProjectFactory

   def test_project_creation__with_valid_data__creates_project():
       project = ProjectFactory()
       assert project.title
   ```

5. **Run your tests** ([running guide](running-tests.md))

   ```bash
   poetry run pytest tests/unit/
   ```

## Next Steps

```{seealso}
- Read [Test Layers](test-layers.md) to understand the three-layer taxonomy
- Review [Test Quality](test-quality.md) for guidance on writing effective tests
- Check [Test Organization](test-organization.md) for file structure and naming
- Explore [Fixtures & Factories](fixtures.md) for reusable test data patterns
```

## Testing Standards

FairDM testing follows formal conventions to ensure consistency:

- **Test Naming**: Follow pytest conventions with descriptive names (see [Test Organization](test-organization.md))
- **Test Structure**: Organize by type (unit, integration, functional) and module
- **Fixtures**: Use factory-boy patterns documented in [Fixtures Guide](fixtures.md)

These standards are **binding** - all tests must follow these conventions to ensure discoverability, maintainability, and consistent contributor experience.
