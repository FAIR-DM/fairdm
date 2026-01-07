# Phase 1: Data Model & Conceptual Entities

**Feature**: FairDM Documentation Strategy
**Date**: 2026-01-07
**Status**: Complete

## Overview

This document defines the conceptual entities that compose the FairDM documentation strategy infrastructure.

---

## Entity: Information Architecture

**Description**: The immutable top-level documentation structure that defines where content belongs.

**Purpose**: Provides stable foundation for cross-referencing and ensures all documentation has a clear, predictable location.

**Attributes**:

- **Top-level sections** (immutable):
  - `user-guide/` - For Portal Users (end users of a research portal)
  - `portal-administration/` - For Portal Administrators (managing portal settings, users, permissions)
  - `portal-development/` - For Portal Developers (building/customizing portals with FairDM)
  - `contributing/` - For Framework Contributors (contributing to FairDM framework itself)

- **Subdirectories** (extensible):
  - Can be added within any top-level section
  - Should follow logical grouping (by task, by component, etc.)
  - Must not create new top-level sections

- **Special directories**:
  - `.specify/` - Speckit metadata and templates (immutable)
  - `specs/` - Feature specifications (immutable container, extensible contents)
  - `overview/` - Cross-cutting introductory content (extensible)

**Relationships**:

- Referenced by: Feature Documentation Checklist (to determine section placement)
- Referenced by: Conformance Audit (to validate structure compliance)
- Referenced by: Cross-References (to build stable links)

**Validation Rules**:

- Top-level sections must exist and follow naming exactly
- No new top-level sections may be added without constitution amendment
- All documentation files must reside within one of the defined sections

**Examples**:

```
docs/
├── user-guide/
│   ├── getting-started/         # Extensible subdirectory
│   └── features/                # Extensible subdirectory
├── portal-administration/
│   ├── setup/                   # Extensible subdirectory
│   └── maintenance/             # Extensible subdirectory
├── portal-development/
│   ├── models/                  # Extensible subdirectory
│   ├── views/                   # Extensible subdirectory
│   └── plugins/                 # Extensible subdirectory
└── contributing/
    ├── development/             # Extensible subdirectory
    └── testing/                 # Extensible subdirectory
```

---

## Entity: Feature Documentation Checklist

**Description**: A template-driven checklist that guides Framework Contributors in documenting new features across all appropriate documentation sections.

**Purpose**: Ensures consistent documentation coverage for new features and prevents documentation gaps.

**Attributes**:

- **Metadata**:
  - Feature name (display name)
  - Spec reference (link to `../../specs/###-feature-name/spec.md`)
  - Author/responsible party
  - Completion date

- **Section Checklist**:
  - [ ] User Guide (if feature affects end users)
  - [ ] Portal Administration (if feature adds admin configuration)
  - [ ] Portal Development (if feature adds new APIs/components)
  - [ ] Contributing (if feature affects framework development workflow)

- **Content Requirements**:
  - [ ] Feature overview and purpose
  - [ ] Usage examples (code snippets where applicable)
  - [ ] Configuration options
  - [ ] Migration guide (if breaking changes)
  - [ ] Cross-references to related docs

- **Validation Checklist**:
  - [ ] Spec link resolves (via linkcheck)
  - [ ] Documentation builds without warnings
  - [ ] Internal links validated
  - [ ] Examples tested (if code samples present)

**Relationships**:

- References: Spec Cross-Reference (for spec link)
- References: Information Architecture (for section placement)
- Produces: Conformance Audit data (completed checklists)
- Used by: Framework Contributors (when implementing features)

**Validation Rules**:

- Must exist in `specs/###-feature-name/checklists/` directory
- Must include metadata section with spec reference
- Must have at least one section checkbox marked
- All links must validate via Sphinx linkcheck

**Lifecycle**:

1. Created: When feature spec is finalized (before implementation)
2. Updated: As implementation progresses and documentation is added
3. Completed: When all required checkboxes marked and validation passes
4. Archived: When feature documentation is merged to main branch

**Examples**: See `contracts/feature-docs-checklist-example.md`

---

## Entity: Spec Cross-Reference

**Description**: A standardized pattern for linking from documentation to feature specifications.

**Purpose**: Maintains traceability between documentation and the specifications that define features.

**Attributes**:

- **Spec ID**: Three-digit zero-padded number (e.g., `001`, `015`)
- **Spec name**: URL-safe slug (e.g., `documentation-strategy`)
- **Anchor**: Optional section anchor within spec (e.g., `#functional-requirements`)

**Pattern**:

```markdown
[Spec: Display Name](../../specs/###-spec-name/spec.md)
[Spec: Display Name](../../specs/###-spec-name/spec.md#anchor)
```

**Relationships**:

- Referenced by: Feature Documentation Checklist
- Referenced by: Portal Development documentation
- Referenced by: Contributing documentation
- Validated by: Validation Report (linkcheck results)

**Validation Rules**:

- Relative path must be exactly `../../specs/` from docs/
- Spec ID must be three digits
- Spec directory must exist
- `spec.md` file must exist in spec directory
- Anchor must exist in target file (if specified)

**Examples**:

```markdown
# From docs/portal-development/registry.md
See [Spec: Documentation Strategy](../../specs/001-documentation-strategy/spec.md)
for the complete specification.

# With anchor
The [information architecture requirements](../../specs/001-documentation-strategy/spec.md#fr-008)
define the immutable structure.
```

---

## Entity: Constitution Cross-Reference

**Description**: A standardized pattern for linking from documentation to constitutional principles.

**Purpose**: Connects documentation to the philosophical foundations and guiding principles of FairDM.

**Attributes**:

- **File path**: Always `../../.specify/memory/constitution.md` from docs/
- **Anchor**: Section within constitution (e.g., `#i-fair-first-research-portals`)

**Pattern**:

```markdown
[Constitution: Principle Name](../../.specify/memory/constitution.md#anchor)
```

**Relationships**:

- Referenced by: Overview documentation
- Referenced by: Contributing documentation
- Validated by: Validation Report (linkcheck results)

**Validation Rules**:

- Relative path must be exactly `../../.specify/memory/constitution.md` from docs/
- Constitution file must exist
- Anchor must exist in target file
- Anchor must follow kebab-case naming (lowercase, hyphens)

**Examples**:

```markdown
# From docs/overview/philosophy.md
FairDM follows the [FAIR-First](../../.specify/memory/constitution.md#i-fair-first-research-portals)
principle, ensuring all portals promote Findable, Accessible, Interoperable, and
Reusable research data.

# From docs/contributing/development.md
All contributions must align with our
[Test-First Quality](../../.specify/memory/constitution.md#ii-test-first-quality)
commitment.
```

---

## Entity: Lifecycle Marker

**Description**: MyST admonitions that mark documentation for features in specific lifecycle states (deprecated, experimental, maintenance).

**Purpose**: Provides clear visual indicators of feature stability and future support.

**Attributes**:

- **Type**: One of `deprecated`, `warning` (for experimental), `note` (for maintenance)
- **Version**: Version when state applies (e.g., "2.0.0")
- **Message**: Required explanation of status and next steps
- **Alternative** (for deprecated): Link to replacement feature/docs

**Patterns**:

**Deprecated**:

```markdown
:::{deprecated} 2.0.0
This feature is deprecated and will be removed in version 3.0.0.
Use [replacement_feature](link) instead.
:::
```

**Experimental**:

```markdown
:::{warning}
**Experimental**: This feature is in active development and may change without notice.
API stability is not guaranteed until version 2.0.0.
:::
```

**Maintenance**:

```markdown
:::{note}
**Maintenance Mode**: This feature is stable but no longer receiving new functionality.
Security updates and critical bug fixes only.
:::
```

**Relationships**:

- Used in: All documentation sections
- Triggered by: Constitution amendments (for deprecated features)
- Triggered by: Spec authors (for experimental features)
- Validated by: Validation Report (ensures proper MyST syntax)

**Validation Rules**:

- Must use correct MyST admonition syntax (`:::{type}` ... `:::`)
- Deprecated markers must include version and alternative
- Experimental markers must include "Experimental" keyword
- Maintenance markers must include "Maintenance Mode" keyword

---

## Entity: Validation Report

**Description**: Automated output from Sphinx build and linkcheck that indicates documentation conformance.

**Purpose**: Provides objective measure of documentation quality and completeness.

**Attributes**:

- **Build status**: Pass/Fail (warnings treated as errors)
- **Link check results**:
  - Internal links: Pass/Fail (all must pass)
  - External links: Warning only (failures logged but not blocking)
- **Completeness metrics**:
  - Features with checklists: count
  - Features with completed checklists: count
  - Missing spec cross-references: list
- **Conformance issues**:
  - Files outside immutable structure: list
  - Broken lifecycle markers: list

**Generated by**:

- Sphinx build (`sphinx-build -W -b html`)
- Sphinx linkcheck (`sphinx-build -b linkcheck`)
- Custom pytest tests (`tests/integration/docs/test_documentation_validation.py`)

**Relationships**:

- Consumes: All documentation files
- Consumes: Feature Documentation Checklists
- Consumes: Information Architecture definition
- Used by: CI/CD pipeline (GitHub Actions)
- Used by: Framework Contributors (pre-commit validation)

**Output Format**:

```
=== Documentation Validation Report ===
Build Status: PASS
Warnings: 0
Errors: 0

Link Check:
  Internal Links: 245 checked, 245 passed, 0 failed
  External Links: 42 checked, 38 passed, 4 warnings

Checklist Validation:
  Total Features: 12
  Features with Checklists: 11
  Completed Checklists: 9
  Incomplete Checklists: 2 (specs/005-api-feature, specs/008-plugin-system)

Conformance:
  Structure Violations: 0
  Lifecycle Marker Errors: 0
  Missing Spec References: 3 (portal-development/registry.md, contributing/setup.md, user-guide/advanced.md)

Result: ✅ PASS (with 4 external link warnings)
```

**Validation Rules**:

- Build must complete without warnings/errors (exit code 0)
- All internal links must resolve (hard fail)
- External link failures generate warnings only (not blocking)
- Checklists completeness is informational (not blocking)

---

## Entity: Conformance Audit

**Description**: Periodic manual review of documentation to identify drift from information architecture and standards.

**Purpose**: Catches edge cases and gradual divergence that automated tools may miss.

**Attributes**:

- **Audit date**: Date of review
- **Auditor**: Framework Contributor performing review
- **Scope**: Which documentation sections reviewed
- **Findings**:
  - Structure violations (files in wrong sections)
  - Missing cross-references (should link to spec/constitution but doesn't)
  - Inconsistent terminology usage
  - Missing lifecycle markers (known deprecated features not marked)
- **Remediation plan**: Tasks to address findings

**Relationships**:

- Reviews: Information Architecture conformance
- Reviews: Feature Documentation Checklists (completeness)
- Reviews: Cross-reference patterns (usage consistency)
- Produces: Tasks for remediation
- Triggered by: Constitution amendments (when structure changes)
- Triggered by: Periodic schedule (e.g., quarterly)

**Process**:

1. **Scope definition**: Determine which sections to audit
2. **Structure review**: Verify all files in correct sections
3. **Cross-reference review**: Check for missing spec/constitution links
4. **Lifecycle review**: Verify deprecated/experimental features marked
5. **Terminology review**: Check role term consistency
6. **Report generation**: Document findings and recommendations
7. **Issue creation**: Create tasks for remediation

**Output Format**:

```markdown
# Conformance Audit: 2026-Q1

**Date**: 2026-01-15
**Auditor**: John Doe
**Scope**: All documentation sections

## Structure Violations
- `docs/miscellaneous/old-guide.md` - Should be in `contributing/` or deleted

## Missing Cross-References
- `portal-development/registry.md` - Should reference Spec 001 (documentation strategy)
- `contributing/setup.md` - Should reference Constitution Principle II (test-first)

## Lifecycle Markers
- `user-guide/old-workflow.md` - Feature deprecated in 2.0 but not marked

## Terminology Issues
- `portal-development/` - Uses "developer" without qualification 12 times

## Recommendations
1. Move or delete `docs/miscellaneous/`
2. Add spec reference to registry documentation
3. Add constitution reference to setup guide
4. Mark old workflow as deprecated with alternative link
5. Qualify all "developer" mentions with "Portal Developer" or "Framework Contributor"
```

**Validation Rules**:

- Must be performed after constitution amendments
- Recommended quarterly for stable projects
- Findings must be tracked as issues/tasks
- Critical findings block releases

---

## Summary

This data model defines 7 conceptual entities that compose the documentation strategy infrastructure:

1. **Information Architecture**: Immutable structure defining section placement
2. **Feature Documentation Checklist**: Template guiding comprehensive feature documentation
3. **Spec Cross-Reference**: Standard pattern linking docs to specifications
4. **Constitution Cross-Reference**: Standard pattern linking docs to principles
5. **Lifecycle Marker**: Admonitions marking feature stability states
6. **Validation Report**: Automated quality metrics from builds and link checks
7. **Conformance Audit**: Periodic manual review catching edge cases

These entities interact to create a self-reinforcing documentation system that maintains quality, consistency, and traceability over time.
