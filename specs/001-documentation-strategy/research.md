# Phase 0: Research & Discovery

**Feature**: FairDM Documentation Strategy
**Date**: 2026-01-07
**Status**: Complete

## Overview

This document resolves technical unknowns and establishes implementation patterns for the FairDM documentation strategy infrastructure.

---

## 1. Sphinx Linkcheck Configuration

**Research Question**: How to configure Sphinx linkcheck with ignore patterns for external links?

**Findings**:

The Sphinx `linkcheck` builder validates both internal and external links. Configuration in `docs/conf.py`:

```python
# Link checking configuration
linkcheck_ignore = [
    r'http://localhost:\d+',
    r'https://example\.com',
    r'.*\.local',
]

# Treat broken links as errors
linkcheck_allowed_redirects = {
    r'https://.*github\.com/.*': r'https://.*github\.com/.*',
}

# Retry configuration
linkcheck_retries = 2
linkcheck_timeout = 10
linkcheck_workers = 5

# Anchors to ignore (for sites that don't support HEAD requests)
linkcheck_anchors_ignore = [
    r'^!',  # Ignore anchors starting with !
]
```

**Running linkcheck**:

```bash
poetry run sphinx-build -b linkcheck docs docs/_build/linkcheck
```

**CI Integration**: Can fail build on broken internal links while warning on external links by parsing output.

**Decision**: Use linkcheck builder in CI with custom script to parse output and distinguish internal (hard fail) from external (warning only).

---

## 2. MyST Admonition Syntax

**Research Question**: Best practices for MyST admonition usage (deprecated, warning, note)?

**Findings**:

MyST supports standard Sphinx admonitions with clean syntax:

**Deprecated Features**:

```markdown
:::{deprecated} 2.0.0
This feature is deprecated and will be removed in version 3.0.0.
Use [new_feature](link/to/new_feature.md) instead.
:::
```

**Experimental Features**:

```markdown
:::{warning}
**Experimental**: This feature is in active development and may change without notice.
API stability is not guaranteed until version 2.0.0.
:::
```

**Maintenance Mode**:

```markdown
:::{note}
**Maintenance Mode**: This feature is stable but no longer receiving new functionality.
Security updates and critical bug fixes only.
:::
```

**Other Useful Admonitions**:

- `:::{attention}` - Important callouts
- `:::{tip}` - Pro tips and best practices
- `:::{seealso}` - Related documentation
- `:::{versionadded} X.Y` - New in version X.Y
- `:::{versionchanged} X.Y` - Changed in version X.Y

**Decision**: Use `deprecated`, `warning`, and `note` as specified in FR-021.

---

## 3. CI/CD Integration Patterns

**Research Question**: How to integrate Sphinx builds with GitHub Actions?

**Current State**: FairDM already uses GitHub Actions (checked `.github/workflows/` directory exists).

**Pattern**:

```yaml
name: Documentation Validation

on:
  pull_request:
    paths:
      - 'docs/**'
      - 'specs/**'
      - '*.md'
  push:
    branches:
      - main

jobs:
  validate-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Poetry
        uses: snok/install-poetry@v1

      - name: Install dependencies
        run: poetry install --with docs

      - name: Build documentation (strict)
        run: |
          poetry run sphinx-build -W --keep-going -b html docs docs/_build/html
        # -W: treat warnings as errors
        # --keep-going: report all errors, not just first

      - name: Check internal links
        run: |
          poetry run sphinx-build -b linkcheck docs docs/_build/linkcheck
          # Parse output to ensure internal links pass
          python .github/scripts/check-internal-links.py

      - name: Check external links (warning only)
        run: |
          poetry run sphinx-build -b linkcheck docs docs/_build/linkcheck
          python .github/scripts/check-external-links.py || echo "External link warnings detected"
        continue-on-error: true

      - name: Validate feature checklists
        run: |
          python tests/integration/docs/test_checklist_validation.py
```

**Decision**: Create `.github/workflows/docs-validation.yml` with strict validation for internal links/builds, warnings for external links.

---

## 4. Existing Documentation Structure Audit

**Research Question**: Map current documentation structure and identify migration needs.

**Current Structure** (audited from `docs/` directory):

```
docs/
├── conf.py                          # Sphinx configuration
├── index.md                         # Main entry point
├── overview/
│   ├── index.md                     # Overview landing
│   ├── introduction.md              # What is FairDM
│   ├── background.md                # Research context
│   ├── goals.md                     # Project goals
│   ├── features.md                  # Core features
│   ├── data-model.md                # Core data model
│   └── contributors.md              # Contributor model
├── user-guide/                      # FOR: Portal Users
│   ├── index.md                     # User guide landing
│   └── [needs content]
├── portal-administration/           # FOR: Portal Administrators
│   ├── index.md                     # Admin landing
│   └── [needs content]
├── portal-development/              # FOR: Portal Developers
│   ├── index.md                     # Developer landing
│   └── [needs content]
├── contributing/                    # FOR: Framework Contributors
│   ├── index.md                     # Contributing landing
│   └── [needs content]
├── more/                            # Miscellaneous
│   └── roadmap.md
└── technology/                      # Stack documentation
    └── [various tech docs]
```

**Conformance Assessment**:

- ✅ Top-level structure matches immutable architecture (4 sections)
- ✅ Section naming uses directory paths correctly
- ⚠️ `more/` and `technology/` don't fit immutable structure - need to relocate
- ⚠️ Most sections have only index.md - content is TBD (out of scope for this spec)
- ⚠️ No cross-references to specs or constitution found
- ⚠️ No lifecycle markers (deprecated/experimental) found

**Migration Needs**:

1. Relocate `technology/` content to `contributing/technology-stack.md`
2. Relocate `more/roadmap.md` to `overview/roadmap.md`
3. Add cross-references to constitution in overview pages
4. Add information architecture guide to `portal-development/`
5. Add documentation guides to `contributing/`

**Decision**: Conformance audit will be phased work item - document migration plan in tasks.md.

---

## 5. Feature Checklist Examples

**Research Question**: Research feature documentation checklists from similar projects.

**Examples Found**:

**Django Enhancement Proposals (DEPs)**:

- Require documentation updates in same PR as code
- Checklist includes: release notes, deprecation timeline, migration guide
- Format: Markdown checkboxes in PR template

**Sphinx Project**:

- Documentation changes tracked in CHANGES file
- Each feature requires: API docs, narrative docs, example
- No formal checklist but convention-based

**pytest**:

- PR template includes documentation checkbox
- Requires: docstring, user guide update, changelog entry
- Format: GitHub PR template with checkboxes

**Common Patterns**:

1. Metadata: Feature name, author, spec/issue reference
2. Section checklist: Which doc sections need updates (API, guide, examples)
3. Content requirements: What must be included (examples, migration, etc.)
4. Validation: Link to spec, confirm tests pass, docs build

**Decision**: Create lightweight checklist template combining best patterns - see contracts/feature-docs-checklist-example.md.

---

## 6. Cross-Reference Patterns

**Research Question**: Test cross-reference patterns in MyST (relative links, anchors).

**MyST Relative Link Syntax**:

```markdown
# Same directory
[Link text](file.md)

# Parent directory
[Link text](../other-section/file.md)

# From docs root (using absolute path from conf.py)
[Link text](/section/file.md)

# With anchor
[Link text](file.md#section-anchor)

# To spec
[Spec: Feature Name](../../specs/001-feature-name/spec.md)

# To constitution
[Constitution: Principle I](../../.specify/memory/constitution.md#i-fair-first-research-portals)
```

**Anchor Generation Rules**:

- MyST generates anchors from headers automatically
- Format: lowercase, spaces to hyphens, special chars removed
- Example: `## Test-First Quality` → `#test-first-quality`

**Testing Results**:

- ✅ Relative links work correctly
- ✅ Anchors to headers work when properly formatted
- ✅ Links to specs work with `../../specs/` pattern
- ✅ Links to constitution work with `../../.specify/memory/` pattern
- ⚠️ Sphinx linkcheck validates these links

**Decision**: Document standard patterns in information architecture guide.

---

## 7. Checklist Validation Tools

**Research Question**: Determine if existing Sphinx extensions support checklist validation.

**Findings**:

No built-in Sphinx extension for checklist validation found. Options:

1. **Custom pytest test** (Recommended):

   ```python
   def test_feature_checklist_exists(spec_dir):
       """Verify feature has completed checklist."""
       checklist_files = list(Path(spec_dir / "checklists").glob("*.md"))
       assert len(checklist_files) > 0, "No checklist found"

       for checklist in checklist_files:
           content = checklist.read_text()
           assert "## Documentation Updates" in content
           assert "[x]" in content.lower()  # At least one completed item
   ```

2. **Pre-commit hook**: Run validation before commits
3. **GitHub Action**: Run as part of PR checks

**Decision**: Implement as pytest test in `tests/integration/docs/test_documentation_validation.py` - simple, testable, integrates with existing test infrastructure.

---

## Summary

All technical unknowns resolved:

| Question | Answer | Source |
| -------- | ------ | ------ |
| Sphinx linkcheck configuration | Use `linkcheck_ignore` in conf.py, parse output for internal vs external | Sphinx docs |
| MyST admonition syntax | `:::{type}` blocks for deprecated, warning, note | MyST Parser docs |
| CI/CD integration | GitHub Actions workflow with strict build + linkcheck | Existing FairDM workflows |
| Current docs structure | 4 sections exist, need migration of `more/` and `technology/` | Direct audit |
| Checklist examples | Combine patterns from Django, pytest, Sphinx | Project documentation |
| Cross-reference patterns | Relative links with `../../specs/` and `../../.specify/` | MyST testing |
| Validation tooling | Custom pytest tests for checklist validation | pytest-django |

**Ready for Phase 1**: Design phase can now proceed with concrete patterns and validated approaches.
