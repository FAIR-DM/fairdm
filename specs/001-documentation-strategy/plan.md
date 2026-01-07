# Implementation Plan: Documentation Infrastructure

**Branch**: `003-docs-infrastructure` | **Date**: 2026-01-06 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-docs-infrastructure/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This feature establishes a comprehensive documentation infrastructure for FairDM that defines clear information architecture, provides checklists for feature documentation, enables traceability from docs to specs, implements automated validation, and brings existing documentation into compliance. The technical approach uses Sphinx with MyST parser, pydata-sphinx-theme, and sphinx-design for documentation building, with CI-integrated validation including linkcheck builder for internal/external links, custom checklist validation, and build error enforcement as hard blocks on PR merges.

## Technical Context

**Language/Version**: Python 3.11+ (Django/Sphinx tooling)
**Primary Dependencies**: Sphinx 7.x+, MyST-Parser 2.x+, pydata-sphinx-theme, sphinx-design, sphinxext.opengraph, sphinx_copybutton
**Storage**: Git repository structure (specs/, .specify/, docs/); documentation artifacts as Markdown files
**Testing**: Documentation build validation, link checking (sphinx.ext.linkcheck), custom Python validators for checklist compliance
**Target Platform**: Cross-platform (documentation builds in CI, viewed in browsers)
**Project Type**: Documentation infrastructure (single repository, multiple build targets)
**Performance Goals**: Documentation builds complete in <2 minutes; link validation scans 500+ pages in <5 minutes
**Constraints**: Must not break existing Sphinx configuration; external link checks must not cause false CI failures; validation must provide actionable error messages
**Scale/Scope**: ~200+ existing documentation pages across 4 sections; ~10-20 new features annually requiring documentation; constitution and 50+ specs to cross-reference

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Alignment with Core Principles**:

✅ **I. FAIR-First Research Portals**: Documentation infrastructure supports FAIR by making design decisions discoverable (spec traceability), ensuring documentation quality (validation), and maintaining authoritative governance references (constitution links)

✅ **II. Domain-Driven, Declarative Modeling**: Information architecture declaratively defines where documentation lives; checklist templates declaratively specify what must be documented for feature types

✅ **III. Configuration Over Custom Plumbing**: Feature documentation checklist is template-based configuration, not custom code; Sphinx extensions use declarative directives rather than imperative logic

✅ **IV. Opinionated, Production-Grade Defaults**: Chooses standard Sphinx + MyST + pydata-sphinx-theme stack; provides sensible defaults for link checking (internal=fail, external=warn)

✅ **V. Quality, Sustainability, and Community**: Automated validation enforces documentation quality; clear guidelines lower contribution barriers; constitution compliance tracking maintains governance integrity

**Development Workflow**:

✅ **Specification First**: This feature itself follows spec-first workflow (spec.md complete before plan.md)

✅ **Feature Documentation & Templates**: Creates the feature documentation checklist template that will be used by all future features

✅ **Comprehensive Testing Discipline**: Validation suite acts as "tests" for documentation (build checks, link validation, checklist compliance)

## Project Structure

### Documentation (this feature)

```text
specs/003-docs-infrastructure/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (technology decisions, best practices)
├── data-model.md        # Phase 1 output (entities: IA, checklists, validations)
├── quickstart.md        # Phase 1 output (contributor workflow for docs)
├── contracts/           # Phase 1 output (validation interfaces, checklist schema)
├── checklists/          # Quality and validation checklists for this feature
│   └── requirements.md  # Spec validation checklist (already created)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
docs/                              # Documentation source files
├── conf.py                        # Sphinx configuration (extend for validation)
├── index.md                       # Main documentation landing page
├── developer-guide/               # For portal builders
│   ├── index.md
│   ├── documentation.md           # NEW: How to document features (IA guide)
│   └── [existing guides...]
├── admin-guide/                   # For portal administrators
│   ├── index.md
│   └── [existing guides...]
├── contributor-guide/             # For portal data contributors
│   ├── index.md
│   └── [existing guides...]
├── contributing/                  # For framework contributors
│   ├── index.md
│   ├── documentation-standards.md # NEW: Documentation contribution guide
│   └── [existing guides...]
└── _static/                       # Static assets

.specify/                          # Speckit governance structure
├── memory/
│   └── constitution.md            # Governance document (referenced from docs)
├── templates/
│   ├── feature-docs-checklist.md  # NEW: Template for feature docs checklist
│   ├── spec-template.md           # Existing spec template
│   ├── plan-template.md           # Existing plan template
│   ├── tasks-template.md          # Existing tasks template
│   └── checklist-template.md      # Existing checklist template
└── scripts/
    └── powershell/
        └── validate-docs.ps1      # NEW: Documentation validation script

specs/                             # Feature specifications (reference from docs)
├── 001-documentation-baseline/
├── 002-production-config-fairdm-conf/
├── 003-docs-infrastructure/       # This feature
└── [future features]/

.github/                           # CI/CD configuration
└── workflows/
    └── docs-validation.yml        # NEW: CI workflow for doc validation

tests/                             # Test suite (if adding Python validators)
└── test_docs/
    ├── test_link_validation.py    # NEW: Test link checker logic
    ├── test_checklist_validation.py # NEW: Test checklist validator
    └── test_conformance_audit.py  # NEW: Test audit tooling
```

**Structure Decision**: Single repository structure with documentation in `docs/`, governance in `.specify/`, and specifications in `specs/`. New documentation files will be added to existing `docs/` hierarchy following the four-section architecture (developer-guide, admin-guide, contributor-guide, contributing). Validation tooling will be Python scripts in `.specify/scripts/` callable from CI. This aligns with current FairDM repository organization and follows Django project conventions.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

[No violations - feature fully aligns with constitution]

---

## Phase 0: Outline & Research

**Objective**: Resolve all NEEDS CLARIFICATION markers from Technical Context by researching technology choices, best practices, and integration patterns. Document decisions with rationale and alternatives considered.

### Research Output (research.md)

The following research areas will be documented in `research.md`:

#### R1: Sphinx Link Validation Configuration

**Question**: How to configure Sphinx linkcheck to distinguish internal vs external link handling?
**Decision**: Use `sphinx.ext.linkcheck` with `linkcheck_ignore` for external exceptions, treat internal link failures as hard errors
**Rationale**: Sphinx linkcheck builder provides built-in support for checking both internal and external links with configurable behavior per pattern
**Alternatives Considered**:

- Custom Python script for link checking → Rejected: Reinvents Sphinx functionality
- Third-party tool (e.g., linkchecker) → Rejected: Adds dependency and harder to integrate with Sphinx build
**References**: Sphinx linkcheck documentation (via Context7)

#### R2: MyST Cross-Reference Syntax

**Question**: What MyST syntax should be used for cross-referencing specs and constitution sections?
**Decision**: Use standard Markdown relative links for specs `[spec](../../specs/003-docs-infrastructure/spec.md)` and anchor links for constitution `[constitution](#section-id)`
**Rationale**: Standard Markdown links work in both Sphinx builds and GitHub/IDE preview; no special MyST roles needed
**Alternatives Considered**:

- Custom MyST role `{spec}003-docs-infrastructure` → Rejected: Adds complexity without benefit
- reStructuredText `:doc:` directive → Rejected: Not MyST-native, less readable
**References**: MyST Parser documentation, existing FairDM docs patterns

#### R3: pydata-sphinx-theme Customization

**Question**: How to extend pydata-sphinx-theme configuration without breaking existing setup?
**Decision**: Update `html_theme_options` in docs/conf.py to add secondary_sidebar_items for spec cross-references; use existing theme capabilities
**Rationale**: pydata-sphinx-theme already configured in FairDM; incremental changes preserve existing setup
**Alternatives Considered**:

- Custom theme → Rejected: Massive overhead for minor customization
- Switch to different theme → Rejected: Breaks existing documentation appearance
**References**: pydata-sphinx-theme configuration docs (via Context7), existing docs/conf.py

#### R4: CI Integration for Documentation Validation

**Question**: How to integrate documentation validation into CI without blocking legitimate use cases?
**Decision**: GitHub Actions workflow that runs `sphinx-build -W` (warnings as errors), `sphinx-build -b linkcheck`, and custom Python validator for checklists; hard fail for internal link breaks and build errors, warn for external link failures
**Rationale**: Leverages existing CI infrastructure, standard Sphinx build process, clear separation of hard vs soft failures
**Alternatives Considered**:

- Pre-commit hooks → Rejected: Doesn't enforce on CI, developers can bypass
- Manual review only → Rejected: Not scalable, doesn't enforce standards
- External service (ReadTheDocs checks) → Rejected: Ties us to specific hosting
**References**: GitHub Actions documentation, Sphinx build options

#### R5: Checklist Validation Approach

**Question**: How to validate that feature documentation checklists are complete?
**Decision**: Python script that parses checklist Markdown, verifies all items marked `[x]`, checks that required sections exist; integrated into CI validation workflow
**Rationale**: Simple Markdown parsing, no complex dependencies, easy to extend
**Alternatives Considered**:

- YAML/JSON schema → Rejected: Less human-friendly than Markdown checklist
- Manual review → Rejected: Error-prone, not automatable
**References**: Python pathlib, re module for Markdown parsing

#### R6: Documentation Conformance Audit Tooling

**Question**: What tooling to use for identifying non-conforming existing documentation?
**Decision**: Python script that scans docs/ directory, checks for: missing spec cross-references, incorrect directory placement, broken internal links, missing alt text on images; generates report with file paths and suggested fixes
**Rationale**: Custom script can check FairDM-specific conventions that generic tools can't
**Alternatives Considered**:

- Linter extension (e.g., markdownlint rules) → Rejected: Can't check spec cross-references or directory structure
- Manual audit → Rejected: Not repeatable, documentation will drift over time
**References**: Python pathlib, ast/docutils for parsing

#### R7: Information Architecture Documentation Format

**Question**: Where and how to document the information architecture itself?
**Decision**: Create `docs/contributing/documentation-standards.md` with tables showing section purpose, example pages, and decision criteria for placement
**Rationale**: Documentation about documentation belongs in contributing guide; table format makes it scannable
**Alternatives Considered**:

- Separate README in docs/ → Rejected: Less discoverable, not part of built docs
- Comments in conf.py → Rejected: Not visible to documentation contributors
**References**: Existing FairDM documentation structure

---

## Phase 1: Design & Contracts

**Objective**: Extract entities from feature spec, generate data models, define API contracts, and create quickstart guide. Update agent context with new technology decisions.

### Phase 1.1: Data Model (data-model.md)

Document the conceptual entities that underpin documentation infrastructure:

**Note**: These are conceptual documentation artifacts (files, validation reports, audit results), not Django database models. The term "entity" is used to describe discrete concepts with attributes and relationships, but these will not be persisted in the database.

#### Entity 1: Information Architecture

**Definition**: Hierarchical structure defining where documentation resides and the purpose of each section
**Attributes**:

- Section name (developer-guide, admin-guide, contributor-guide, contributing)
- Purpose statement (who the audience is, what they should find there)
- Subdirectories (optional, for organizing within sections)
- Decision criteria (rules for when content belongs in this section vs others)
**Relationships**:
- Has many Documentation Pages
- References Feature Documentation Checklist (which sections to update)
**Validation Rules**:
- Section names must match established four-section structure
- Each section must have index.md with purpose statement
- Decision criteria must be explicit and non-overlapping
**State**: Static (defined in documentation-standards.md)

#### Entity 2: Feature Documentation Checklist

**Definition**: Template listing documentation sections requiring updates for different feature types
**Attributes**:

- Feature type (new model, new UI component, configuration change, breaking change)
- Checklist items (section to update, required content, acceptance criteria)
- Status (not-started, in-progress, completed)
- Completion date
**Relationships**:
- References Information Architecture (which sections)
- Attached to Feature Spec (one checklist per spec)
- References Documentation Pages (links to updated docs)
**Validation Rules**:
- Must have at least one item marked [x] for completion
- Each item must specify target section and required content
- Status must progress from not-started → in-progress → completed
**State**: Created when feature starts, updated during implementation, finalized before merge

#### Entity 3: Spec Cross-Reference

**Definition**: Link from documentation page to specification file
**Attributes**:

- Source documentation page path
- Target spec path (specs/###-feature-name/spec.md)
- Context text (why this feature is referenced)
- Link anchor (optional, for specific section)
**Relationships**:
- Belongs to Documentation Page
- Points to Feature Specification
**Validation Rules**:
- Target spec file must exist
- Link syntax must be valid Markdown
- Context should explain relevance
**State**: Created when documentation references a feature

#### Entity 4: Constitution Cross-Reference

**Definition**: Link from documentation page to specific constitutional principle
**Attributes**:

- Source documentation page path
- Target constitution section anchor (e.g., #i-fair-first-research-portals)
- Principle name
- How feature aligns with principle
**Relationships**:
- Belongs to Documentation Page
- Points to Constitution Section
**Validation Rules**:
- Constitution anchor must exist and be stable
- Alignment explanation should be present
**State**: Created when documentation explains governance alignment

#### Entity 5: Validation Report

**Definition**: Output from documentation validation process
**Attributes**:

- Build status (success/failure)
- Internal link check results (pass/fail per link)
- External link check results (warning per link)
- Checklist completeness (missing checklists, incomplete items)
- Quality metrics (pages validated, errors found, warnings issued)
- Timestamp
**Relationships**:
- Aggregates results from all validators
- Triggers CI pass/fail
**Validation Rules**:
- Must include all validation types (build, links, checklists)
- Failure must include actionable error messages
**State**: Generated on each CI run

#### Entity 6: Conformance Audit

**Definition**: Analysis of existing documentation against standards
**Attributes**:

- Audit date
- Pages scanned count
- Non-conforming pages (list with specific issues)
- Issues by category (missing cross-refs, wrong location, formatting)
- Remediation steps (specific actions to fix)
- Priority (high/medium/low per issue)
**Relationships**:
- Analyzes Documentation Pages
- References Information Architecture (correct structure)
- Outputs Conformance Report
**Validation Rules**:
- Must scan all pages in docs/
- Each issue must have specific file path and line number
- Remediation steps must be actionable
**State**: Generated on-demand or periodically

### Phase 1.2: Contracts (contracts/)

Define interfaces and schemas for validation and automation:

#### Contract 1: Feature Documentation Checklist Schema (JSON)

```json
{
  "feature_id": "003-docs-infrastructure",
  "feature_type": "infrastructure",
  "checklist_items": [
    {
      "section": "developer-guide",
      "page": "documentation.md",
      "required_content": "Information architecture table",
      "status": "completed",
      "notes": "Added table showing all four sections"
    }
  ],
  "created_date": "2026-01-06",
  "completed_date": null
}
```

#### Contract 2: Validation Report Schema (JSON)

```json
{
  "timestamp": "2026-01-06T14:30:00Z",
  "build_status": "success|failure",
  "validations": {
    "sphinx_build": {"status": "pass|fail", "errors": []},
    "internal_links": {"status": "pass|fail", "broken_links": []},
    "external_links": {"status": "warning", "warnings": []},
    "checklists": {"status": "pass|fail", "issues": []}
  },
  "summary": {
    "total_pages": 200,
    "errors": 0,
    "warnings": 3
  }
}
```

#### Contract 3: Conformance Audit Schema (JSON)

```json
{
  "audit_date": "2026-01-06",
  "pages_scanned": 200,
  "issues": [
    {
      "file": "docs/developer-guide/old-page.md",
      "line": 45,
      "category": "missing_spec_reference",
      "severity": "medium",
      "message": "Page discusses registration API but doesn't link to spec",
      "remediation": "Add link to specs/001-feature/spec.md"
    }
  ]
}
```

### Phase 1.3: Quickstart (quickstart.md)

**Title**: Documenting a New Feature

**Audience**: Framework contributors adding features to FairDM

**Prerequisites**:

- Feature specification complete (spec.md)
- Basic familiarity with Markdown and MyST syntax

**Steps**:

1. **Locate Documentation Checklist**
   - Find `.specify/templates/feature-docs-checklist.md`
   - Copy to `specs/###-your-feature/checklists/documentation.md`

2. **Determine Documentation Sections**
   - Review information architecture in `docs/contributing/documentation-standards.md`
   - Identify which of the four sections (developer-guide, admin-guide, contributor-guide, contributing) need updates
   - Check checklist for required items per section

3. **Write Documentation**
   - Add or update pages in identified sections
   - Use MyST Markdown syntax
   - Include cross-references to spec: `[Feature Spec](../../specs/###-your-feature/spec.md)`
   - Reference constitution if applicable: `[Constitution: Principle](.specify/memory/constitution.md#principle-anchor)`

4. **Validate Locally**
   - Run `poetry run sphinx-build -W docs docs/_build/html` to check for errors
   - Run `poetry run sphinx-build -b linkcheck docs docs/_build/linkcheck` to validate links
   - Mark checklist items as `[x]` when complete

5. **Submit for Review**
   - Commit documentation changes with feature changes
   - CI will automatically validate
   - Address any validation failures before merge

**Estimated Time**: 30-60 minutes per feature depending on complexity

### Phase 1.4: Agent Context Update

Run `.specify/scripts/powershell/update-agent-context.ps1 -AgentType copilot` to update `.github/instructions/copilot.instructions.md` with:

- Documentation validation tools (Sphinx linkcheck, custom validators)
- Feature documentation checklist location
- Information architecture section references
- Cross-reference patterns for specs and constitution

---

## Phase 2: Tasks & Implementation (Reserved for /speckit.tasks)

**Note**: Task breakdown will be generated by the `/speckit.tasks` command based on this plan and the feature specification. This section is intentionally left blank.

---

## Post-Phase 1 Constitution Check

**Re-evaluation after design**:

✅ All constitutional principles remain satisfied. Design uses standard Sphinx + MyST tooling (no custom framework needed), follows declarative configuration patterns (checklist templates, IA tables), and provides automated quality enforcement (validation suite). No violations introduced during design phase.
