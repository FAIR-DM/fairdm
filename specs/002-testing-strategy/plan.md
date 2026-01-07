# Implementation Plan: Testing Strategy & Fixtures

**Branch**: `004-testing-strategy-fixtures` | **Date**: 2026-01-06 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-testing-strategy-fixtures/spec.md`

## Summary

Establish a comprehensive testing strategy for FairDM that defines test layer taxonomy (unit, integration, contract), organizational structure, naming conventions, and fixture patterns. This feature serves three user personas: (1) FairDM contributors writing tests, (2) contributors using fixture factories, and (3) downstream portal developers importing FairDM factories in their own projects. This is foundational documentation and infrastructure—not a runtime behavior change—that will guide all future test development. The strategy emphasizes test quality (meaningful, maintainable, reliable) over coverage percentages, using coverage metrics as diagnostic tools to identify gaps rather than gates to merge.

**Technical Approach**: Document the testing strategy in developer documentation, create pytest configuration and directory structure following the defined taxonomy (`tests/{layer}/{app}/test_{module}.py`), establish fixture organization patterns with factory-boy factories declared in app packages (`fairdm/core/factories.py`) and re-exported via convenience module (`fairdm/factories.py`), and provide reference examples demonstrating test quality principles. Include portal developer documentation for importing and extending FairDM factories in downstream projects.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: pytest, pytest-django, factory-boy, coverage.py, pytest-playwright
**Storage**: Test database (PostgreSQL in test mode) with transaction rollback per test, session-level DB creation
**Testing**: Self-referential (this feature defines the testing strategy itself)
**Target Platform**: Developer workstations (all OS), CI/CD environments
**Project Type**: Documentation + test infrastructure configuration
**Performance Goals**: Test suite execution < 5 minutes for full run, < 30 seconds for unit tests only
**Constraints**: Must align with Constitution v1.2.0 Principle V (Test-First) and Principle VI (Documentation Critical)
**Scale/Scope**: Applies to entire FairDM framework codebase and all apps

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Constitutional Alignment

**Principle V - Test-First Quality & Sustainability (NON-NEGOTIABLE)**:

- ✅ This feature documents the test-first discipline (Red → Green → Refactor)
- ✅ Defines pytest, pytest-django, factory-boy, coverage.py, pytest-playwright as canonical tools
- ✅ Emphasizes test quality (meaningful, maintainable, reliable) over percentage targets
- ✅ Positions coverage as diagnostic tool, not a gate
- ✅ Establishes test organization taxonomy aligned with constitutional requirements

**Principle VI - Documentation Critical**:

- ✅ This feature produces documentation as its primary deliverable
- ✅ Will include usage examples for each test layer and fixture pattern
- ✅ Documents expected behavior in testable terms
- ✅ Provides migration guidance for existing tests

**Architecture & Stack Constraints**:

- ✅ Uses pytest and pytest-django (constitutional requirement)
- ✅ Defines test organization taxonomy: unit (`tests/unit/{app}/test_{module}.py`), integration, contract
- ✅ Mandates pytest fixtures and/or factory-boy for fixture factories
- ✅ Specifies transaction rollback strategy for integration tests
- ✅ Requires Cotton component tests use `django_cotton.render_component()` with `rf` fixture
- ✅ Requires UI tests use pytest-playwright

**Development Workflow & Quality Gates**:

- ✅ This feature itself follows specification-first workflow
- ✅ Addresses "Comprehensive Testing Discipline" requirement by defining what comprehensive means
- ✅ Supports "Feature Documentation & Templates" by providing testing conventions

### Violations

**None**. This feature is fully aligned with all constitutional principles and explicitly implements several constitutional requirements.

## Project Structure

### Documentation (this feature)

```text
specs/004-testing-strategy-fixtures/
├── plan.md              # This file
├── research.md          # Phase 0 output (testing tools/patterns research)
├── data-model.md        # N/A (no data models for documentation feature)
├── quickstart.md        # Phase 1 output (quick start guide for test authors)
├── checklists/
│   └── requirements.md  # Already completed
└── tasks.md             # Phase 2 output (NOT created yet)
```

### Source Code (repository root)

```text
docs/
├── contributing/
│   ├── testing/
│   │   ├── index.md              # Testing strategy overview
│   │   ├── test-layers.md        # Unit/integration/contract definitions
│   │   ├── test-organization.md  # Directory structure and naming
│   │   ├── fixtures.md           # Fixture patterns and factory-boy usage
│   │   ├── test-quality.md       # Meaningful/maintainable/reliable criteria
│   │   ├── coverage.md           # Coverage as diagnostic tool
│   │   ├── database-strategy.md  # Transaction rollback patterns
│   │   └── examples/
│   │       ├── unit-test-example.md
│   │       ├── integration-test-example.md
│   │       ├── contract-test-example.md
│   │       └── fixture-factory-example.md
│   └── index.md                  # Link to testing section
├── portal-development/
│   ├── testing-portal-projects.md  # Portal developer guide (NEW)
│   └── index.md                    # Link to portal testing guide

fairdm/
├── factories.py                  # Convenience module: imports and re-exports all factories via __all__ (NEW)
├── core/
│   ├── models.py
│   └── factories.py              # ProjectFactory, DatasetFactory declared here (NEW)
└── ...

tests/
├── conftest.py                   # Root-level pytest configuration
├── fixtures/                     # Test-specific pytest fixtures (NEW)
│   ├── __init__.py
│   └── pytest_fixtures.py        # Composed pytest fixtures using fairdm.factories imports
├── unit/                         # Unit tests (reorganized to match taxonomy)
│   ├── conftest.py
│   └── {app_name}/               # Per-app subdirectories
│       ├── conftest.py
│       └── test_{module}.py
├── integration/                  # Integration tests (reorganized)
│   ├── conftest.py
│   └── {app_name}/
│       ├── conftest.py
│       └── test_{module}.py
└── contract/                     # Contract tests (NEW)
    ├── conftest.py
    └── {app_name}/
        ├── conftest.py
        └── test_{module}.py

pyproject.toml                    # Update pytest configuration
pytest.ini or setup.cfg           # If needed for pytest settings
.coveragerc or pyproject.toml     # Coverage.py configuration
```

**Structure Decision**: Documentation-focused feature with test infrastructure reorganization. The primary deliverable is framework contributor documentation in `docs/contributing/testing/` that defines the canonical testing strategy. Supporting deliverables include pytest configuration updates, directory structure creation for the three test layers, and reference fixture examples demonstrating quality principles.

## Complexity Tracking

**No violations**. This feature is foundational infrastructure aligned with constitutional requirements.

| Violation | Severity | Justification                     |
| --------- | -------- | --------------------------------- |
| (None)    | N/A      | All constitutional principles met |

## Phase 0: Research

### Research Topics

1. **Pytest Configuration Best Practices**
   - Investigation: Optimal pytest.ini vs pyproject.toml configuration for Django projects
   - Investigation: Test discovery patterns and performance optimization
   - Investigation: Pytest plugin ecosystem (pytest-django, pytest-xdist for parallel execution)

2. **Factory-Boy Patterns for Django**
   - Investigation: Factory inheritance patterns for polymorphic Django models
   - Investigation: SubFactory and RelatedFactory patterns for complex relationships
   - Investigation: Fixture scope strategies (session vs module vs function)

3. **Coverage.py Configuration**
   - Investigation: Coverage measurement strategies that emphasize quality over quantity
   - Investigation: Branch coverage vs line coverage trade-offs
   - Investigation: Coverage reporting formats for developer feedback

4. **Test Quality Metrics Beyond Coverage**
   - Investigation: Mutation testing tools for Python/Django
   - Investigation: Test maintainability metrics
   - Investigation: Test reliability patterns (avoiding flaky tests)

5. **Django Test Database Strategies**
   - Investigation: pytest-django database transaction strategies
   - Investigation: Test database creation/teardown performance optimization
   - Investigation: Fixture data loading strategies

### Research Deliverable

`research.md` will document findings for each topic above, including:

- Chosen approach with rationale
- Alternatives considered and why rejected
- Configuration examples
- Links to authoritative documentation

## Phase 1: Design & Contracts

### Documentation Design

**Primary Deliverable**: `docs/contributing/testing/` documentation suite

Each documentation page will include:

- **Purpose**: What this aspect of testing achieves
- **When to use**: Decision criteria for test authors
- **How to implement**: Step-by-step with code examples
- **Quality criteria**: What makes a good test of this type
- **Common pitfalls**: Anti-patterns to avoid

### Configuration Design

**pytest Configuration** (`pyproject.toml`):

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
    "--reuse-db",  # pytest-django: reuse test DB
    "--no-migrations",  # pytest-django: use existing migrations
]
```

**Coverage Configuration** (pyproject.toml):

```toml
[tool.coverage.run]
source = ["fairdm"]
omit = [
    "*/tests/*",
    "*/migrations/*",
    "*/__pycache__/*",
]

[tool.coverage.report]
precision = 1
show_missing = true
skip_covered = false
```

### Fixture Design

**App-Level Factory Declaration** (`fairdm/core/factories.py`):

```python
"""
Factory-boy factories for fairdm.core models.

Factories are declared here (near models) and re-exported via fairdm/factories.py
for convenient downstream imports.
"""
import factory
from factory.django import DjangoModelFactory
from fairdm.core.models import Project, Dataset


class ProjectFactory(DjangoModelFactory):
    """Factory for creating test projects.

    All fields have defaults. Customize at runtime:
        project = ProjectFactory(title="My Project", is_public=True)
    """
    class Meta:
        model = Project

    title = factory.Sequence(lambda n: f"Project {n}")
    slug = factory.LazyAttribute(lambda obj: obj.title.lower().replace(" ", "-"))
    description = factory.Faker("text", max_nb_chars=200)
    owner = factory.SubFactory("fairdm.core.factories.UserFactory")  # Avoid circular import
    is_public = False


class DatasetFactory(DjangoModelFactory):
    """Factory for creating test datasets."""
    class Meta:
        model = Dataset

    title = factory.Sequence(lambda n: f"Dataset {n}")
    project = factory.SubFactory(ProjectFactory)
    # ... all other fields with defaults
```

**Convenience Re-Export Module** (`fairdm/factories.py`):

```python
"""
Convenience module for importing FairDM factories.

Downstream portal developers can use flat imports:
    from fairdm.factories import ProjectFactory, DatasetFactory

Factories are declared in their respective app packages and re-exported here.
"""
from fairdm.core.factories import (
    ProjectFactory,
    DatasetFactory,
    UserFactory,
)
from fairdm.other_app.factories import (
    OtherFactory,
)

__all__ = [
    "ProjectFactory",
    "DatasetFactory",
    "UserFactory",
    "OtherFactory",
]
```

**Design Rationale**:

- **App-level declaration**: Factories declared near models (`fairdm/core/factories.py`) for code locality
- **Convenience re-export**: `fairdm/factories.py` imports and re-exports via `__all__` for flat downstream imports
- **Fully-featured**: All model fields included with sensible defaults
- **Runtime overrides**: Tests customize via `ProjectFactory(field=value)`, not subclasses
- **Included in distribution**: Package includes both app-level factories and convenience re-export module
- **Comprehensive docstrings**: Each factory documents usage patterns for portal developers

### Contracts (N/A)

This feature produces documentation, not APIs, so no formal contracts are needed.

### Quickstart Guide

`quickstart.md` will provide a 5-minute tutorial:

1. Writing your first unit test
2. Using a fixture factory
3. Writing an integration test
4. Running tests and interpreting coverage reports
5. Understanding test quality vs coverage numbers

**Portal Developer Quickstart** (`docs/portal-development/testing-portal-projects.md`):

A dedicated guide for downstream portal developers:

1. Installing FairDM as a test dependency (`poetry add --group dev fairdm`)
2. Importing factories (`from fairdm.factories import ProjectFactory, DatasetFactory`)
3. Basic usage examples in portal tests
4. Customizing factories with runtime overrides
5. Extending factories for portal-specific fields
6. Best practices for maintaining portal-specific test suites

## Agent Context Update

After Phase 1 completion, run:

```powershell
.\.specify\scripts\powershell\update-agent-context.ps1 -AgentType copilot
```

This will update `.github/instructions/copilot.instructions.md` or similar agent-specific files to reference:

- New testing documentation location
- Test layer taxonomy
- Fixture factory patterns
- Test quality principles

---

**Phase 0 and Phase 1 sections above will be filled by the /speckit.plan command research and design workflow.**
