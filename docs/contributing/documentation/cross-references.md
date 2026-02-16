# Cross-Reference Patterns

Documentation traceability is critical for maintaining the connection between implemented features and their original specifications. This guide defines the standard patterns for cross-referencing specifications, constitutional principles, and related documentation.

## Why Cross-References Matter

Cross-references serve multiple purposes:

- **Traceability**: Readers can trace documented features back to their original requirements and rationale
- **Context**: Links to specifications provide deeper context for design decisions
- **Governance**: Constitution links connect features to guiding principles
- **Maintenance**: When specifications change, cross-references help identify affected documentation

```{important}
Cross-references are **mandatory** for:
- All portal-development/ documentation (must link to relevant specs)
- All contributing/ documentation (must link to constitution principles where applicable)
- Feature checklists (must link to feature specification)
```

## Specification Cross-References

### Pattern

Link to feature specifications using this exact pattern:

```markdown
[Spec: Display Name](../../specs/###-spec-name/spec.md)
```

With optional anchor for specific sections:

```markdown
[Spec: Display Name](../../specs/###-spec-name/spec.md#anchor)
```

### Components

**Display Name**: Human-readable feature name (e.g., "Documentation Strategy", "Plugin System")

**Path**: Always use relative path `../../specs/` from any file in `docs/`

**Spec ID**: Three-digit zero-padded number (e.g., `001`, `015`, `042`)

**Spec Name**: URL-safe slug matching the spec directory name (e.g., `documentation-strategy`)

**Anchor** (optional): Section heading within spec file (e.g., `#functional-requirements`, `#fr-008`)

### Examples

**Basic spec reference**:

```markdown
See [Spec: Registry System](../../specs/002-fairdm-registry/spec.md)
for complete requirements.
```

**Rendered**: See [Spec: Registry System](../../specs/002-fairdm-registry/spec.md) for complete requirements.

**Spec reference with anchor**:

```markdown
The [registration API](../../specs/002-fairdm-registry/spec.md#registration-api)
provides explicit model configuration.
```

**Rendered**: The [registration API](../../specs/002-fairdm-registry/spec.md#registration-api) provides explicit model configuration.

**Multiple spec references**:

```markdown
This feature builds on the [Registry System](../../specs/002-fairdm-registry/spec.md)
and follows patterns from the [Core Projects](../../specs/003-core-projects/spec.md).
```

### Validation Rules

```{note}
All specification links are validated during documentation builds:
- Path must resolve (spec directory and file must exist)
- Anchor must exist if specified (heading must be present in target file)
- Internal link failures cause build to fail (hard block)
```

Run validation locally:

```bash
# Check all links including spec references
poetry run sphinx-build -b linkcheck docs docs/_build/linkcheck

# Or use the dedicated script
poetry run python .github/scripts/check-internal-links.py
```

## Constitution Cross-References

### Pattern

Link to constitutional principles using this exact pattern:

```markdown
[Constitution: Principle Name](../../.specify/memory/constitution.md#anchor)
```

Or with shortened display text:

```markdown
[Principle Name](../../.specify/memory/constitution.md#anchor)
```

### Components

**Display Name**: Either "Constitution: Principle Name" or just "Principle Name"

**Path**: Always `../../.specify/memory/constitution.md` from any file in `docs/`

**Anchor**: Section identifier in kebab-case (lowercase with hyphens)

### Examples

**Basic constitution reference**:

```markdown
FairDM follows the [FAIR-First](../../.specify/memory/constitution.md#i-fair-first-research-portals)
principle, ensuring all portals promote Findable, Accessible, Interoperable, and
Reusable research data.
```

**Multiple principles**:

```markdown
All contributions must align with our [Test-First Quality](../../.specify/memory/constitution.md#v-test-first-quality-sustainability)
commitment and adhere to [Documentation Critical](../../.specify/memory/constitution.md#vi-documentation-critical)
standards.
```

**In contributing documentation**:

```markdown
The FairDM framework is built on six constitutional principles:

1. [FAIR-First Research Portals](../../.specify/memory/constitution.md#i-fair-first-research-portals)
2. [Domain-Driven, Declarative Modeling](../../.specify/memory/constitution.md#ii-domain-driven-declarative-modeling)
3. [Configuration Over Custom Plumbing](../../.specify/memory/constitution.md#iii-configuration-over-custom-plumbing)
4. [Opinionated, Production-Grade Defaults](../../.specify/memory/constitution.md#iv-opinionated-production-grade-defaults)
5. [Test-First Quality & Sustainability](../../.specify/memory/constitution.md#v-test-first-quality-sustainability)
6. [Documentation Critical](../../.specify/memory/constitution.md#vi-documentation-critical)
```

### When to Use Constitution References

Use constitution cross-references when:

- Explaining **why** FairDM makes specific design decisions
- Documenting framework contribution guidelines
- Describing architectural constraints or patterns
- Justifying opinionated defaults or conventions

```{tip}
**Portal development** docs should reference **specs** (what the feature does).
**Contributing** docs should reference **constitution** (why we build things this way).
```

## Anchor Generation Rules

Both MyST Markdown and reStructuredText automatically generate anchors from headings. Understanding these rules ensures your cross-references work correctly.

### MyST Anchor Rules

MyST (Markdown) generates anchors by:

1. Converting heading text to lowercase
2. Replacing spaces with hyphens
3. Removing special characters (except hyphens and underscores)
4. Removing leading/trailing hyphens

**Examples**:

| Heading | Anchor |
|---------|--------|
| `# Getting Started` | `#getting-started` |
| `## User Authentication` | `#user-authentication` |
| `### API: CreateSample()` | `#api-createsample` |
| `# Cross-Reference Patterns` | `#cross-reference-patterns` |

### ReStructuredText Anchor Rules

For .rst files, anchors can be:

- Auto-generated (same rules as MyST)
- Explicitly defined with `.. _anchor-name:`

**Example**:

```rst
.. _custom-anchor:

Section Title
=============
```

Link to explicit anchor: `#custom-anchor`

### Verifying Anchors

To verify an anchor exists before linking:

1. **Build the documentation locally**:

   ```bash
   poetry run sphinx-build -b html docs docs/_build/html
   ```

2. **Open the target file** in `docs/_build/html/`

3. **Inspect the heading element** - it will have an `id` attribute matching the anchor

4. **Use the anchor in your link** without the `#` in your reference:

   ```markdown
   [Section Name](path/to/file.md#anchor-name)
   ```

## Cross-Reference Checklist

When adding documentation that references other materials, verify:

### For Spec References

- [ ] Spec ID is three digits (e.g., `001`, not `1`)
- [ ] Spec directory exists in `specs/###-spec-name/`
- [ ] `spec.md` file exists in that directory
- [ ] Anchor matches an actual heading if specified
- [ ] Relative path is `../../specs/` from `docs/`
- [ ] Link text clearly indicates what is being referenced

### For Constitution References

- [ ] Path is exactly `../../.specify/memory/constitution.md`
- [ ] Anchor is in kebab-case (lowercase, hyphens only)
- [ ] Anchor matches a heading in constitution.md
- [ ] Reference explains **why** (principle), not just **what** (feature)
- [ ] Context makes it clear this is a guiding principle

### General Cross-Reference Quality

- [ ] Link text is descriptive (avoid "click here" or "see here")
- [ ] Context around link explains why reader should follow it
- [ ] Cross-references are relevant and add value
- [ ] Links are tested locally before committing
- [ ] Broken links are fixed immediately (builds will fail)

## Common Cross-Reference Scenarios

### Scenario 1: Documenting a New Portal Development Feature

**Context**: You're documenting a new API in `docs/portal-development/api/samples.md`

**Required Cross-References**:

```markdown
# Sample Creation API

The Sample API allows Portal Developers to create custom sample types
that extend the polymorphic `Sample` base model. This feature is defined
in [Spec: Sample API](../../specs/042-sample-api/spec.md).

## Creating a Custom Sample

Follow the [Domain-Driven Modeling](../../.specify/memory/constitution.md#ii-domain-driven-declarative-modeling)
principle by defining your sample's domain attributes declaratively...
```

**Why**: Spec reference traces implementation to requirements. Constitution reference explains the "why" behind the design pattern.

### Scenario 2: Contributing Guide for New Features

**Context**: You're writing `docs/contributing/development/workflow.md`

**Required Cross-References**:

```markdown
# Feature Development Workflow

All feature development follows our [Test-First Quality](../../.specify/memory/constitution.md#v-test-first-quality-sustainability)
principle:

1. Write specification in `specs/###-feature-name/spec.md`
2. Create feature checklist (see [Feature Checklist Workflow](../documentation/feature-checklist-workflow.md))
3. Write tests before implementation
4. Implement feature
5. Document feature following established documentation conventions

Each feature must have a completed checklist that links back to its specification.
```

**Why**: Constitution reference establishes the philosophical foundation. Spec reference provides implementation details.

### Scenario 3: User Guide with Portal Admin Context

**Context**: You're writing `docs/user-guide/data-submission.md`

**Required Cross-References** (usually none for user guides):

```markdown
# Submitting Data

To submit data to the portal, navigate to the Data Submission page...

[No spec or constitution references needed - user guides are consumer-focused]
```

**Why**: User guides are written for end users who don't need to know about specs or constitutional principles. Cross-references to portal administration or portal development docs are appropriate if users need elevated permissions.

### Scenario 4: Breaking Change Migration Guide

**Context**: You're documenting a breaking change in `docs/portal-development/migrations/v2-to-v3.md`

**Required Cross-References**:

```markdown
# Migrating from v2.x to v3.0

Version 3.0 removes the deprecated `old_registry` module in favor of
the new plugin-based registry system defined in
[Spec: Plugin Architecture](../../specs/005-plugin-architecture/spec.md).

## Why This Changed

The old registry violated our [Configuration Over Custom Plumbing](../../.specify/memory/constitution.md#iii-configuration-over-custom-plumbing)
principle by requiring too much boilerplate code...

## Migration Steps

1. Replace `from fairdm.old_registry import register` with new pattern
   documented in [Plugin Registration](../plugins/registration.md)...
```

**Why**: Spec reference provides new implementation details. Constitution reference justifies the breaking change. Internal doc link guides migration.

## Integration with Feature Workflow

Cross-references are mandatory in the feature checklist workflow:

### Step 1: Create Feature Checklist

Every feature checklist must include a spec reference:

```markdown
# Feature Documentation Checklist

**Feature**: Your Feature Name
**Spec**: [Your Feature](../spec.md)
**Author**: Your Name
**Date**: 2026-01-07
```

### Step 4: Add Content Requirements

The feature checklist workflow (Step 4) requires adding cross-references:

```markdown
### Content Requirements

- [x] Feature overview
- [x] Usage examples
- [x] Configuration options
- [ ] Migration guide (if applicable)
- [x] **Cross-references to spec and related docs** ← Mandatory
```

See [Feature Checklist Workflow](./feature-checklist-workflow.md#step-4-add-content-requirements) for details.

## Validation Commands

Verify all cross-references work before committing:

### Full Link Check

```bash
# Comprehensive link validation (internal + external)
poetry run sphinx-build -b linkcheck docs docs/_build/linkcheck

# Check results
cat docs/_build/linkcheck/output.txt | grep -E "(broken|redirected)"
```

### Internal Links Only

```bash
# Fast internal link check (specs and constitution)
poetry run python .github/scripts/check-internal-links.py

# Returns exit code 1 if any internal links are broken
```

### CI/CD Integration

The documentation validation workflow automatically checks all cross-references on every pull request. Internal link failures block PR merge.

See [Validation Rules](./validation-rules.md) for complete CI/CD integration details.

## Related Documentation

- [Feature Checklist Workflow](./feature-checklist-workflow.md) - When and where to add cross-references
- [Information Architecture](./information-architecture.md) - Understanding documentation structure
- [Validation Rules](./validation-rules.md) - Automated quality checks for cross-references

## Questions & Troubleshooting

**Q: My spec link shows as broken but the file exists. What's wrong?**

A: Check these common issues:

- Spec ID has wrong number of digits (must be 3: `001`, not `1` or `0001`)
- Path doesn't start with `../../specs/` from docs/
- Spec directory name doesn't match the link (check for typos)
- Missing `.md` extension on `spec.md`

**Q: Can I link to spec files other than spec.md (like plan.md or research.md)?**

A: Yes, but only for internal framework contributors. Portal development docs should **only** link to spec.md files, as other files contain implementation details.

Example:

```markdown
<!-- Good - in contributing/development/ -->
See [implementation plan](../../specs/002-fairdm-registry/plan.md)

<!-- Bad - in portal-development/ -->
See [implementation plan](../../specs/002-fairdm-registry/plan.md)
```

**Q: Do I need to add cross-references to every page?**

A: No. Cross-references are mandatory for:

- Portal development API/component documentation (must reference specs)
- Contributing guides explaining "why" (should reference constitution)
- Feature checklists (must reference parent spec)

User guides and portal administration docs rarely need cross-references.

**Q: How do I link to a specific requirement in a spec (like FR-001)?**

A: Use the heading anchor:

```markdown
[requirement FR-001](../../specs/002-fairdm-registry/spec.md#fr-001-explicit-registration)
```

The anchor is auto-generated from the heading text. Check the rendered HTML to verify the exact anchor.

**Q: Can I link directly to the constitution from user-facing docs?**

A: Generally no. Constitution references are for Portal Developers and Framework Contributors who need to understand architectural decisions. End users don't need that context.
