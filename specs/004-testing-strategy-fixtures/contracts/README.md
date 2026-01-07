# Testing Strategy Contracts

**Version**: 1.0
**Date**: 2026-01-06
**Feature**: 004-testing-strategy-fixtures

## Overview

This directory contains formal contracts defining the testing strategy, conventions, and patterns for the FairDM project. These contracts are binding agreements that all contributors must follow when writing tests.

## Contract Documents

### 1. [Test Naming Contract](./test-naming-contract.md)

**Purpose**: Defines mandatory naming conventions for test files and test functions.

**Key Rules**:

- Test files: `test_{module}.py`
- Test functions: `test_<behavior>__<condition>__<expected>()`
- All tests must include docstrings

**Enforced by**: pytest discovery, code review

---

### 2. [Test Organization Contract](./test-organization-contract.md)

**Purpose**: Defines directory structure and file organization for tests.

**Key Rules**:

- Three-layer structure: `tests/{layer}/{app}/test_{module}.py`
- Layers: unit, integration, contract
- Tests mirror Django app structure
- Fixtures in `tests/fixtures/`

**Enforced by**: Code review, CI/CD checks

---

### 3. [Fixture Factory Contract](./fixture-factory-contract.md)

**Purpose**: Defines structure and patterns for factory-boy test data factories.

**Key Rules**:

- All factories in `tests/fixtures/factories.py`
- Factory naming: `{Model}Factory`
- Must include comprehensive docstrings with usage examples
- Use `factory.Faker()` for realistic data
- Support polymorphic model inheritance

**Enforced by**: Code review, documentation

---

## Contract Status

| Contract                 | Version | Status | Last Updated |
| ------------------------ | ------- | ------ | ------------ |
| Test Naming              | 1.0     | Active | 2026-01-06   |
| Test Organization        | 1.0     | Active | 2026-01-06   |
| Fixture Factory          | 1.0     | Active | 2026-01-06   |

## Using These Contracts

### For Contributors

1. **Before writing tests**: Review relevant contracts
2. **During development**: Follow naming and organization rules
3. **Before submitting PR**: Verify compliance with all contracts
4. **Code review**: Reviewers will check contract compliance

### For Reviewers

1. **Check test placement**: Verify tests are in correct layer/directory
2. **Check naming**: Verify test file and function names follow pattern
3. **Check factories**: Verify factories have docstrings and use correct patterns
4. **Request changes**: If contracts violated, request updates before approval

### For Maintainers

1. **Update contracts**: When testing strategy evolves, update contract documents
2. **Version contracts**: Use semantic versioning for contract changes
3. **Communicate changes**: Announce contract updates to contributors
4. **Enforce consistently**: Apply contracts uniformly across codebase

## Contract Violations

### Handling Violations

**Minor violations** (naming inconsistencies, missing docstrings):

- Request fixes in code review
- Contributor updates before merge

**Major violations** (wrong test layer, incorrect organization):

- Block merge until fixed
- May require refactoring

**Exceptions**:

- Must be documented in test file
- Require maintainer approval
- Should be rare

### Reporting Issues

If you find:

- **Ambiguity in contracts**: Open issue to clarify
- **Outdated guidance**: Propose contract update
- **Conflicts between contracts**: Report for resolution

## References

- **Feature Spec**: [spec.md](../spec.md)
- **Implementation Plan**: [plan.md](../plan.md)
- **Quickstart Guide**: [quickstart.md](../quickstart.md)
- **Research**: [research.md](../research.md)
- **Data Model**: [data-model.md](../data-model.md)

---

**Questions?** Refer to comprehensive testing documentation in `docs/contributing/testing/` (to be created in implementation phase).
