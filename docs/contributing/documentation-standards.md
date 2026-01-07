# Documentation Standards

**Purpose**: Guidelines for contributing documentation to FairDM
**Audience**: Framework contributors and portal developers

This guide explains where documentation lives, how to structure it, and how to maintain quality standards.

---

## Information Architecture

FairDM documentation is organized into four primary sections, each serving a distinct audience:

| Section | Audience | Purpose | Example Pages |
|---------|----------|---------|---------------|
| **portal-development/** | Portal builders implementing FairDM | How to build and configure portals using FairDM framework | Model configuration, Registry API, Plugin development, Settings reference |
| **portal-administration/** | Portal administrators managing deployments | How to deploy, configure, and maintain FairDM instances | Deployment guide, Backup/restore, Permissions management, Monitoring |
| **user-guide/** | Portal users contributing data | How to use portal features and contribute data | Data submission workflow, Metadata guidelines, UI walkthroughs, FAQ |
| **contributing/** | Framework contributors developing FairDM | How to contribute to FairDM core development | Development setup, Testing guidelines, Code style, Release process |

---

## Decision Criteria: Where Does My Documentation Go?

Use these decision rules to determine the correct section for your documentation:

### Developer Guide (`docs/portal-development/`)

Choose this section if your documentation answers:

- "How do I configure FairDM for my domain?"
- "How do I register custom models/views/tables?"
- "What configuration options are available?"
- "How do I extend FairDM with plugins?"

**Examples**:

- Documenting a new registry option → `portal-development/registry-api.md`
- Explaining model configuration → `portal-development/models/`
- Plugin development guide → `portal-development/plugins.md`

### Admin Guide (`docs/portal-administration/`)

Choose this section if your documentation answers:

- "How do I deploy FairDM to production?"
- "How do I manage users and permissions?"
- "How do I backup and restore data?"
- "How do I monitor portal health?"

**Examples**:

- Deployment instructions → `portal-administration/deployment.md`
- Permission configuration → `portal-administration/permissions.md`
- Backup procedures → `portal-administration/backup-restore.md`

### User Guide (`docs/user-guide/`)

Choose this section if your documentation answers:

- "How do I submit data to the portal?"
- "How do I use this portal feature?"
- "What metadata fields are required?"
- "How do I search and download data?"

**Examples**:

- Data submission workflow → `user-guide/submitting-data.md`
- Using the search interface → `user-guide/searching.md`
- Metadata best practices → `user-guide/metadata.md`

### Contributing Guide (`docs/contributing/`)

Choose this section if your documentation answers:

- "How do I set up a FairDM development environment?"
- "How do I run tests?"
- "What are the code style conventions?"
- "How do I submit a pull request?"

**Examples**:

- Development setup → `contributing/development.md`
- Testing guidelines → `contributing/testing.md`
- This file → `contributing/documentation-standards.md`

---

## Special Documentation Locations

### Governance Materials (`.specify/memory/`)

The **constitution** and core governance documents reside in `.specify/memory/`:

- `.specify/memory/constitution.md` - Core principles and governance rules

**When to reference**: Link to the constitution when explaining how a feature aligns with FairDM principles (FAIR-first, domain-driven modeling, etc.)

**Cross-reference pattern**: `[Constitution: FAIR-First](.specify/memory/constitution.md#i-fair-first-research-portals)`

### Feature Specifications (`specs/`)

Feature specifications follow the **Speckit** structure in `specs/###-feature-name/`:

- `specs/###-feature-name/spec.md` - Requirements and user stories
- `specs/###-feature-name/plan.md` - Implementation plan
- `specs/###-feature-name/tasks.md` - Task breakdown
- `specs/###-feature-name/checklists/` - Quality checklists

**When to reference**: Link to specs when documenting features to provide rationale and full context

**Cross-reference pattern**: `[spec](../../specs/003-docs-infrastructure/spec.md)`

---

## When to Create a New Page vs Update Existing

### Create a New Page When

- ✅ The topic is substantial enough to stand alone (>500 words)
- ✅ The topic has a distinct audience from existing pages
- ✅ The topic will be referenced from multiple other pages
- ✅ The topic represents a new feature or major concept

**Examples**:

- New feature: Custom Sample Types → `portal-development/custom-samples.md`
- New workflow: Batch Data Import → `user-guide/batch-import.md`

### Update an Existing Page When

- ✅ Adding details to an existing topic
- ✅ Documenting a small enhancement or option
- ✅ Clarifying or expanding existing content
- ✅ The new content naturally fits within an existing structure

**Examples**:

- New configuration option → Add to existing `portal-development/configuration.md`
- UI improvement → Update existing `user-guide/searching.md`
- Bug fix clarification → Update relevant troubleshooting section

### Use Sections and Subsections

- Use heading levels to organize content within a page
- Prefer deeper sections (H3, H4) before creating new pages
- Keep page length reasonable (<2000 words per page as guideline)

---

## Cross-Reference Patterns

### Linking to Specifications

**Purpose**: Provide readers with full context and rationale for documented behavior

**Pattern**: Use relative Markdown links with context text

**Examples**:

```markdown
This registration API was designed to support domain-driven modeling
([spec](../../specs/002-registry-api/spec.md)).

For details on the validation requirements, see the
[feature specification](../../specs/003-validation-infrastructure/spec.md#validation-requirements).
```

**Guidelines**:

- Always provide context text (don't just say "see spec")
- Use relative paths from the documentation file
- Link to specific sections using `#anchor` when helpful
- Include spec version or date if referencing specific version

### Linking to Constitution

**Purpose**: Show how features align with FairDM governance principles

**Pattern**: Use anchor links to specific principle sections

**Examples**:

```markdown
FairDM enforces FAIR principles through automated metadata validation
([Constitution: FAIR-First](.specify/memory/constitution.md#i-fair-first-research-portals)).

This configuration-first approach follows the principle of
[Configuration Over Custom Plumbing](.specify/memory/constitution.md#iii-configuration-over-custom-plumbing).
```

**Guidelines**:

- Use principle names in link text for clarity
- Link to specific principle sections using anchors
- Explain how the feature aligns (don't just link without context)

### Anchor Naming Conventions

**Constitution sections** use lowercase with hyphens:

- `#i-fair-first-research-portals`
- `#ii-domain-driven-declarative-modeling`
- `#iii-configuration-over-custom-plumbing`
- `#iv-opinionated-production-grade-defaults`
- `#v-quality-sustainability-and-community`

**Spec sections** follow standard Markdown anchor rules:

- Lowercase, hyphens for spaces, remove punctuation
- Example: "User Story 1" → `#user-story-1`

---

## Feature Documentation Checklist

When implementing a new feature, use the **feature documentation checklist** to ensure complete documentation coverage.

**Template location**: `.specify/templates/feature-docs-checklist.md`

**Process**:

1. Copy template to `specs/###-feature-name/checklists/documentation.md`
2. Mark relevant sections for your feature type
3. Complete documentation for each marked section
4. Link to updated documentation pages
5. Validate checklist completion before marking feature done

**See**: [Feature Documentation Checklist Template](../../.specify/templates/feature-docs-checklist.md)

---

## Documentation Quality Standards

### Minimum Expectations

All FairDM documentation MUST meet these requirements:

- ✅ **No broken links**: All internal links must resolve (enforced by CI)
- ✅ **Valid syntax**: MyST Markdown syntax must be valid (enforced by Sphinx build)
- ✅ **Alt text on images**: All images must have descriptive alt text
- ✅ **Proper heading hierarchy**: Use H1 → H2 → H3 progression (no skipping levels)
- ✅ **Code examples validate**: All code snippets must be syntactically valid
- ✅ **Consistent formatting**: Follow MyST and FairDM conventions

### External Links

- ⚠️ External links are checked but failures are treated as **warnings**
- External link failures require **manual review** (may be temporary outages)
- Persistent external link failures should be fixed or removed

---

## Validation Process

### Local Validation

Before submitting documentation:

```powershell
# Build documentation and check for errors
poetry run sphinx-build -W docs docs/_build

# Run link validation
poetry run sphinx-build -b linkcheck docs docs/_build

# Run checklist validation
poetry run python .specify/scripts/powershell/validate-checklists.py
```

### Conformance Audit

Periodically run the conformance audit to check for documentation quality issues:

```powershell
# Text output to console
.\.specify\scripts\powershell\audit-docs.ps1

# Generate JSON report
.\.specify\scripts\powershell\audit-docs.ps1 -OutputFormat Json -OutputFile audit-report.json

# Generate HTML report
.\.specify\scripts\powershell\audit-docs.ps1 -OutputFormat Html -OutputFile audit-report.html
```

The audit checks for:

- **Missing spec cross-references**: Feature-related documentation should link to specifications
- **Misplaced files**: Content in wrong directory (e.g., admin content not in portal-administration/)
- **Missing alt text**: Images without descriptive alt text
- **Heading hierarchy violations**: Heading levels that skip (e.g., H1 → H3)

Use the audit report to prioritize documentation improvements and track conformance over time.

### CI Validation

All pull requests are validated automatically:

- ✅ **Sphinx build check**: Documentation must build without errors or warnings
- ✅ **Internal link check**: All internal links must resolve (hard block)
- ⚠️ **External link check**: External links checked, failures are warnings
- ✅ **Checklist validation**: Feature checklists must be complete

**CI Status**: ![Docs Validation](https://github.com/FAIR-DM/fairdm/workflows/docs-validation/badge.svg)

---

## Documentation Workflow

### For Framework Contributors

1. **Before starting**: Check if documentation update is needed
2. **During development**: Update relevant documentation pages
3. **Complete checklist**: Use feature documentation checklist
4. **Local validation**: Run Sphinx build and linkcheck locally
5. **Submit PR**: Documentation validation runs automatically in CI

### For Portal Developers

1. **Consult portal-development**: Find configuration and usage guidance
2. **Reference specs**: Follow links to specifications for full context
3. **Check constitution**: Understand alignment with FairDM principles
4. **Submit issues**: Report documentation gaps or errors

---

## MyST Markdown Syntax

FairDM documentation uses **MyST (Markedly Structured Text)** for enhanced Markdown features.

### Common Patterns

**Cross-references**:

```markdown
See [configuration guide](configuration.md) for details.
```

**Code blocks with syntax highlighting**:

````markdown
```python
from fairdm.registry import register
register(MyModel)
```
````

**Admonitions (notes, warnings, tips)**:

```markdown
:::{note}
This is a note.
:::

:::{warning}
This is a warning.
:::
```

**Tables**:

```markdown
| Column 1 | Column 2 |
|----------|----------|
| Value 1  | Value 2  |
```

**For more MyST syntax**: See [MyST Parser Documentation](https://myst-parser.readthedocs.io/)

---

## Troubleshooting Documentation Validation

### "Build failed with warnings"

**Cause**: Sphinx detected warnings during build (treated as errors with `-W` flag)

**Solution**:

- Check build output for specific warnings
- Common issues: broken references, invalid syntax, missing files
- Run `poetry run sphinx-build docs docs/_build` locally to see warnings

### "Internal link check failed"

**Cause**: Documentation contains broken internal links

**Solution**:

- Check linkcheck output: `docs/_build/output.txt`
- Fix or remove broken links
- Verify file paths are relative and correct

### "External link check failed"

**Cause**: External links are unreachable (may be temporary)

**Solution**:

- Verify links are still valid
- If temporary outage: wait and re-run
- If permanent: update or remove link
- External failures don't block PRs (warnings only)

### "Checklist validation failed"

**Cause**: Feature documentation checklist is incomplete

**Solution**:

- Open `specs/###-feature-name/checklists/documentation.md`
- Complete all relevant sections
- Mark items with `[x]`
- Update status to "completed"

---

## FAQ

**Q: Do I need to update documentation for every change?**
A: Not every change requires documentation. Bug fixes and internal refactoring usually don't need docs updates. New features, configuration changes, and breaking changes always require documentation.

**Q: Which section should I update for a feature that affects multiple audiences?**
A: Update all relevant sections. Use the feature documentation checklist to identify which sections need updates. A new model might need portal-development (configuration), portal-administration (permissions), and user-guide (usage).

**Q: How do I handle deprecated features?**
A: Mark the documentation section with a deprecation warning, explain the migration path to the replacement, and note the version when the feature will be removed. Use MyST admonitions:

```markdown
:::{warning}
This feature is deprecated as of FairDM 2025.1 and will be removed in 2026.0.
Use [New Feature](new-feature.md) instead.
:::
```

**Q: How do I mark experimental features?**
A: Add an experimental notice at the top of the page and note that the API may change:

```markdown
:::{note}
This is an experimental feature. The API may change in future versions without a deprecation period.
:::
```

**Q: Can I skip validation for urgent fixes?**
A: No. Documentation validation is enforced with no bypass mechanism. This ensures documentation quality and prevents broken links from reaching users.

---

## Related Documentation

- [Feature Documentation Checklist Template](../../.specify/templates/feature-docs-checklist.md)
- [FairDM Constitution](../../.specify/memory/constitution.md)
- [MyST Parser Documentation](https://myst-parser.readthedocs.io/)
- [Sphinx Documentation](https://www.sphinx-doc.org/)
- [pydata-sphinx-theme Documentation](https://pydata-sphinx-theme.readthedocs.io/)
