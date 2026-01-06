# Documenting Features

**For portal builders and framework contributors** who need to document new features

This guide explains how to document features in FairDM, including where documentation lives, how to use checklists, and how to trace documentation back to specifications.

---

## Quick Start

When you implement a new feature:

1. **Copy the checklist template** from `.specify/templates/feature-docs-checklist.md` to your feature directory
2. **Identify relevant sections** based on your feature type (models, UI, config, etc.)
3. **Update documentation** in the appropriate guide (developer/admin/contributor/contributing)
4. **Add cross-references** to your spec and constitution principles
5. **Validate locally** with `poetry run sphinx-build -W docs docs/_build`
6. **Complete the checklist** and mark your feature documentation as done

---

## Where Does Documentation Go?

FairDM documentation is organized by audience:

| Section | Audience | When to Use |
|---------|----------|-------------|
| **developer-guide/** | Portal builders | Configuring FairDM, extending with custom models/plugins |
| **admin-guide/** | Portal administrators | Deploying, managing permissions, backups, monitoring |
| **contributor-guide/** | Portal data contributors | Submitting data, using portal features, metadata guidelines |
| **contributing/** | Framework contributors | Developing FairDM core, testing, code style, releasing |

**See the full decision criteria**: [Documentation Standards](../contributing/documentation-standards.md#decision-criteria-where-does-my-documentation-go)

---

## Cross-Reference Patterns

### Linking to Specifications

When documenting a feature, link back to its specification to provide full context:

```markdown
This registration API was designed to support domain-driven modeling
([spec](../../specs/002-registry-api/spec.md)).
```

### Linking to Constitution

Show how features align with FairDM governance principles:

```markdown
FairDM enforces FAIR principles through automated metadata validation
([Constitution: FAIR-First](../../.specify/memory/constitution.md#i-fair-first-research-portals)).
```

### Stable Anchors

Constitution principle anchors:

- `#i-fair-first-research-portals`
- `#ii-domain-driven-declarative-modeling`
- `#iii-configuration-over-custom-plumbing`
- `#iv-opinionated-production-grade-defaults`
- `#v-quality-sustainability-and-community`

---

## Feature Documentation Checklist

Use the checklist template to ensure complete documentation coverage:

**Template**: `.specify/templates/feature-docs-checklist.md`

The checklist helps you:

- Identify which documentation sections need updates
- Track progress as you document
- Verify all required content is complete
- Link to updated documentation pages

**Example completed checklist**: See [this feature's checklist](../../specs/003-docs-infrastructure/checklists/documentation.md)

---

## Validation

Before submitting documentation:

```powershell
# Build docs and check for errors
poetry run sphinx-build -W docs docs/_build

# Validate internal links
poetry run sphinx-build -b linkcheck docs docs/_build
```

CI automatically validates:

- ✅ Documentation builds without errors or warnings
- ✅ Internal links resolve correctly (hard block)
- ⚠️ External links checked (warnings only)
- ✅ Feature checklists are complete

---

## Common Scenarios

### Adding a New Model

Update:

- **developer-guide**: Model configuration, registration API usage
- **admin-guide**: Permissions, admin interface
- **contributor-guide**: How users interact with the model

### Adding UI Components

Update:

- **developer-guide**: Component integration, customization
- **contributor-guide**: UI usage guide with screenshots
- **admin-guide**: Permissions for UI features (if applicable)

### Breaking Changes

Update:

- **developer-guide**: Migration guide with before/after examples
- **admin-guide**: Deployment considerations
- **contributing**: Note in release process/changelog

### Configuration Changes

Update:

- **developer-guide**: New settings reference with examples
- **admin-guide**: Deployment environment variables

---

## Related Documentation

- [Documentation Standards](../contributing/documentation-standards.md) - Full IA guide with decision criteria
- [Feature Documentation Checklist](../../.specify/templates/feature-docs-checklist.md) - Template to copy
- [Constitution](../../.specify/memory/constitution.md) - FairDM governance principles
- [MyST Syntax](https://myst-parser.readthedocs.io/) - Markdown extensions we use
