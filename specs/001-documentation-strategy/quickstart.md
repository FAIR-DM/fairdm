# Quick Reference: Documentation Strategy for Framework Contributors

**Audience**: Framework Contributors working on documentation infrastructure
**Last Updated**: 2026-01-07

---

## At a Glance

This spec establishes the **documentation infrastructure** for FairDM - the immutable structure, validation tooling, and lifecycle management patterns. It does NOT involve writing actual documentation content.

**What this spec provides**:

- ✅ Immutable 4-section documentation structure
- ✅ Feature documentation checklist template
- ✅ Cross-reference patterns (specs, constitution)
- ✅ Lifecycle markers (deprecated, experimental, maintenance)
- ✅ Validation tooling (Sphinx linkcheck, pytest tests, CI/CD)
- ✅ Conformance audit process

**What this spec does NOT cover**:

- ❌ Writing user guides, tutorials, or API documentation
- ❌ Creating specific feature documentation
- ❌ Content strategy or information design

---

## Where Do I Document X?

Use this decision tree to determine which section new documentation belongs in:

```
Who is the primary audience?
│
├─ End users of a research portal built with FairDM
│  └─> user-guide/
│
├─ Administrators managing portal settings, users, permissions
│  └─> portal-administration/
│
├─ Developers building/customizing portals using FairDM
│  └─> portal-development/
│
├─ Contributors developing the FairDM framework itself
│  └─> contributing/
│
└─ Cross-cutting introductory content (philosophy, architecture, etc.)
   └─> overview/
```

**Examples**:

- "How do I create a custom Sample model?" → `portal-development/models/samples.md`
- "How do I add a new plugin system?" → `contributing/architecture/plugins.md`
- "How do I submit data as an end user?" → `user-guide/data-submission.md`
- "How do I configure user permissions?" → `portal-administration/security/permissions.md`
- "What are FairDM's core principles?" → `overview/philosophy.md`

---

## Cross-Reference Syntax

### Linking to Specifications

**Pattern**: `[Spec: Display Name](../../specs/###-spec-name/spec.md)`

**Examples**:

```markdown
See [Spec: Documentation Strategy](../../specs/001-documentation-strategy/spec.md)
for complete requirements.

The [information architecture](../../specs/001-documentation-strategy/spec.md#fr-008)
is immutable.
```

**Rules**:

- Always use relative path `../../specs/` from `docs/`
- Spec ID must be 3 digits (e.g., `001`, `042`)
- Link must resolve via Sphinx linkcheck (internal link = hard fail)

### Linking to Constitution

**Pattern**: `[Constitution: Principle Name](../../.specify/memory/constitution.md#anchor)`

**Examples**:

```markdown
FairDM follows the [FAIR-First](../../.specify/memory/constitution.md#i-fair-first-research-portals)
principle.

All contributions adhere to [Test-First Quality](../../.specify/memory/constitution.md#ii-test-first-quality).
```

**Rules**:

- Always use relative path `../../.specify/memory/constitution.md` from `docs/`
- Anchors are kebab-case (lowercase, hyphens)
- Link must resolve via Sphinx linkcheck

---

## Lifecycle Markers

Use MyST admonitions to mark features in specific lifecycle states:

### Deprecated Features

```markdown
:::{deprecated} 2.0.0
This feature is deprecated and will be removed in version 3.0.0.
Use [replacement_feature](../new-approach.md) instead.
:::
```

**When to use**: Feature is no longer recommended and will be removed in future version.

### Experimental Features

```markdown
:::{warning}
**Experimental**: This feature is in active development and may change without notice.
API stability is not guaranteed until version 2.0.0.
:::
```

**When to use**: Feature is available but API may change before stabilization.

### Maintenance Mode Features

```markdown
:::{note}
**Maintenance Mode**: This feature is stable but no longer receiving new functionality.
Security updates and critical bug fixes only.
:::
```

**When to use**: Feature is stable and supported but not actively developed.

---

## Feature Documentation Workflow

When implementing a new feature, follow this workflow:

### 1. Create Feature Checklist

Copy template from `.specify/templates/feature-docs-checklist.md` to `specs/###-feature-name/checklists/feature-name.md`.

Fill in metadata:

```markdown
# Feature Documentation Checklist

**Feature**: Your Feature Name
**Spec**: [001-your-feature](../spec.md)
**Author**: Your Name
**Date**: 2026-01-07
```

### 2. Identify Required Documentation Sections

Check which sections need updates based on feature scope:

- [ ] **user-guide/** - Does this feature affect end users?
- [ ] **portal-administration/** - Does this add admin configuration?
- [ ] **portal-development/** - Does this add new APIs/components?
- [ ] **contributing/** - Does this change development workflow?

### 3. Document the Feature

For each checked section, add documentation with:

- Feature overview and purpose
- Usage examples (code snippets where applicable)
- Configuration options
- Migration guide (if breaking changes)
- Cross-references to spec and related docs

### 4. Validate Documentation

Run validation locally:

```powershell
# Build documentation (fail on warnings)
poetry run sphinx-build -W -b html docs docs/_build/html

# Check all links (internal must pass)
poetry run sphinx-build -b linkcheck docs docs/_build/linkcheck

# Validate checklists
poetry run pytest tests/integration/docs/test_documentation_validation.py
```

### 5. Update Checklist

Mark completed items in checklist:

```markdown
- [x] User guide updated with feature overview
- [x] Portal development docs include API reference
- [x] Examples tested and validated
- [x] Spec cross-reference added
- [x] Documentation builds without warnings
```

### 6. Submit PR

Include checklist in PR description and link to completed checklist file.

---

## Validation Rules

### Build Validation

**Command**: `poetry run sphinx-build -W -b html docs docs/_build/html`

**Rules**:

- All warnings treated as errors (`-W` flag)
- Build must complete with exit code 0
- Missing includes = error
- Invalid MyST syntax = error

### Link Validation

**Command**: `poetry run sphinx-build -b linkcheck docs docs/_build/linkcheck`

**Rules**:

- **Internal links** (same domain): Hard fail if broken
- **External links** (other domains): Warning only, not blocking
- Anchors validated for internal links
- Ignored patterns configured in `docs/conf.py`

### Checklist Validation

**Command**: `poetry run pytest tests/integration/docs/test_documentation_validation.py`

**Rules**:

- Checklist must exist in `specs/###-feature/checklists/`
- Must include metadata section with spec reference
- At least one section checkbox must be marked
- All links in checklist must validate

---

## File Creation Guidelines

Create a new documentation file when:

1. **Content exceeds ~500 words** (loose guideline, not strict rule)
2. **Content represents a standalone concept** that deserves its own page
3. **Content serves a separate user journey** (different task/goal)

Keep content in a single file when:

1. Content is less than 500 words AND
2. Content is tightly related to existing page topic AND
3. Splitting would create orphan pages with minimal content

**Examples**:

- ✅ New file: "Plugin Development Guide" (1500 words, standalone concept)
- ✅ New file: "Database Migration" (800 words, separate user journey)
- ❌ Single file: "Registry Quick Reference" (300 words, supplement to main registry page)

---

## Constitution Amendment Process

When the constitution is amended (e.g., adding/removing a principle):

1. **Constitution Owner** (maintainer) triggers documentation review
2. **Framework Contributors** identify affected documentation:
   - Pages that reference the amended principle
   - Pages that might conflict with new principle
   - Pages that could benefit from new principle reference
3. **Create Issues** for documentation updates
4. **Update Documentation** with:
   - New/updated constitution cross-references
   - Lifecycle markers if features deprecated by amendment
   - Conformance audit findings addressed
5. **Validate Changes** via CI/CD pipeline
6. **Update Conformance Audit** documentation

---

## CI/CD Integration

Documentation validation runs automatically on:

**Pull Requests**:

- When any file in `docs/`, `specs/`, or `*.md` changes
- Validates build, internal links, external links (warning), checklists
- Must pass before merge

**Main Branch Pushes**:

- Full validation suite
- Deploys documentation to GitHub Pages (if configured)
- Updates validation report

**Workflow Location**: `.github/workflows/docs-validation.yml`

---

## Common Tasks

### Add New Documentation Section

1. Determine which top-level section (user-guide, portal-administration, portal-development, contributing)
2. Create subdirectory if needed (e.g., `portal-development/models/`)
3. Add `index.md` for section landing page
4. Update parent `index.md` toctree to include new section
5. Validate build and links

### Mark Feature as Deprecated

1. Add `:::{deprecated} VERSION` admonition to feature documentation
2. Include removal version and alternative feature link
3. Update feature checklist with deprecation note
4. Add to conformance audit for tracking
5. Validate admonition syntax in build

### Update Spec Cross-Reference

1. Identify documentation pages referencing the spec
2. Update relative path if spec moved/renamed
3. Validate anchor exists in new spec location
4. Run linkcheck to confirm resolution
5. Update feature checklist if applicable

---

## Troubleshooting

### Build Fails with "WARNING: document isn't included in any toctree"

**Cause**: File exists but not referenced in any `index.md` toctree.

**Fix**: Add file to parent `index.md`:

```markdown
```{toctree}
:maxdepth: 2

existing-file
new-file
```

```

### Linkcheck Fails on Internal Link

**Cause**: Target file doesn't exist or anchor is incorrect.

**Fix**:
1. Verify target file exists: `ls docs/path/to/target.md`
2. Verify anchor matches header: `## My Header` → `#my-header`
3. Check relative path from source file

### Checklist Validation Fails

**Cause**: Checklist missing required sections or invalid format.

**Fix**:
1. Verify checklist in `specs/###-feature/checklists/`
2. Ensure metadata section with spec reference exists
3. Ensure at least one checkbox marked
4. Validate all links in checklist

---

## Related Resources

- Full Spec: [001-documentation-strategy/spec.md](./spec.md)
- Research: [research.md](./research.md)
- Data Model: [data-model.md](./data-model.md)
- Contracts: [contracts/](./contracts/)
- Implementation Tasks: [tasks.md](./tasks.md)

---

**Questions?** See [Spec: Documentation Strategy](./spec.md) or ask in #fairdm-dev channel.
