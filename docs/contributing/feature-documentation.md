# Documenting Features

**For portal builders and framework contributors** who need to document new features

This guide explains how to document features in FairDM, including where documentation lives, how to use checklists, and how to trace documentation back to specifications.

---

## Quick Start

When you implement a new feature:

1. **Identify relevant sections** based on your feature type (models, UI, config, etc.)
2. **Update documentation** in the appropriate guide (developer/admin/contributor/contributing)
3. **Add cross-references** to your spec and constitution principles
4. **Validate locally** with `poetry run sphinx-build -W docs docs/_build`
5. **Note what you updated** in your pull request description, so reviewers can confirm coverage

---

## Where Does Documentation Go?

FairDM documentation is organized by audience:

| Section | Audience | When to Use |
|---------|----------|-------------|
| **developer-guide/** | Portal builders | Configuring FairDM, extending with custom models/plugins |
| **portal-administration/** | Portal administrators | Deploying, managing permissions, backups, monitoring |
| **user-guide/** | Portal data contributors | Submitting data, using portal features, metadata guidelines |
| **contributing/** | Framework contributors | Developing FairDM core, testing, code style, releasing |

**See the full decision criteria**: [Documentation Standards](../contributing/documentation-standards.md#decision-criteria-where-does-my-documentation-go)

---

## Cross-Reference Patterns

### Linking to Specifications

When documenting a feature, link back to its specification to provide full context:

```markdown
This registration API was designed to support domain-driven modeling
([spec](../../specs/002-fairdm-registry/spec.md)).
```

### Linking to Constitution

Show how features align with FairDM governance principles:

```markdown
FairDM enforces FAIR principles through automated metadata validation
([Constitution: FAIR-First](../../CONSTITUTION.md#i-fair-first-research-portals)).
```

### Stable Anchors

Constitution principle anchors:

- `#i-fair-first-research-portals`
- `#ii-domain-driven-declarative-modeling`
- `#iii-configuration-over-custom-plumbing`
- `#iv-opinionated-production-grade-defaults`
- `#v-quality-sustainability-and-community`

---

## Validation

Before submitting documentation:

```bash
# Build docs and check for errors
poetry run sphinx-build -W docs docs/_build

# Validate internal links
poetry run sphinx-build -b linkcheck docs docs/_build
```

There's no CI job that runs these checks yet, so run them yourself before opening a pull request.

---

## Common Scenarios

### Adding a New Model

Update:

- **developer-guide**: Model configuration, registration API usage
- **portal-administration**: Permissions, admin interface
- **user-guide**: How users interact with the model

### Adding UI Components

Update:

- **developer-guide**: Component integration, customization
- **user-guide**: UI usage guide with screenshots
- **portal-administration**: Permissions for UI features (if applicable)

### Configuration Changes

Update:

- **developer-guide**: New settings reference with examples
- **portal-administration**: Deployment environment variables

---

## Related Documentation

- [Documentation Standards](../contributing/documentation-standards.md) - Full IA guide with decision criteria
- [Constitution](../../CONSTITUTION.md) - FairDM governance principles
- [MyST Syntax](https://myst-parser.readthedocs.io/) - Markdown extensions we use
