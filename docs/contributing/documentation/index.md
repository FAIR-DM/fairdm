# Documentation Guidelines

Welcome to the FairDM documentation guidelines for contributors. This section covers how to write, organize, and validate documentation that serves the diverse FairDM community.

## For Framework Contributors

If you're contributing to the FairDM framework codebase, these guides will help you ensure your documentation is clear, well-organized, and properly validated:

### Essential Guides

::::{grid} 1 2 2 3
:gutter: 3

:::{grid-item-card} {octicon}`book;1.5em` Information Architecture
:link: information-architecture
:link-type: doc

Learn where documentation lives and how to determine the correct location for new content
+++
[Read the IA Guide →](information-architecture)
:::

:::{grid-item-card} {octicon}`checklist;1.5em` Feature Documentation Checklist
:link: feature-checklist-workflow
:link-type: doc

Track documentation updates for new features with a structured workflow
+++
[Learn the Workflow →](feature-checklist-workflow)
:::

:::{grid-item-card} {octicon}`link;1.5em` Cross-Reference Patterns
:link: cross-references
:link-type: doc

Link documentation to specifications and constitutional principles for traceability
+++
[Learn the Patterns →](cross-references)
:::

:::{grid-item-card} {octicon}`shield-check;1.5em` Documentation Validation
:link: validation-rules
:link-type: doc

Ensure your documentation builds correctly and meets quality standards
+++
[Learn Validation Rules →](validation-rules)
:::

::::

## Quick Links

- **Where do I add documentation?** → [Information Architecture](information-architecture)
- **How do I track documentation updates?** → [Feature Checklist Workflow](feature-checklist-workflow)
- **How do I add cross-references?** → [Cross-Reference Patterns](cross-references)
- **How do I validate documentation?** → [Validation Rules](validation-rules)
- **What are the writing standards?** → Coming soon

## Overview

FairDM documentation serves four distinct audiences, each with different needs:

| Audience | Section | Purpose |
|----------|---------|---------|
| **Portal Users** | `docs/user-guide/` | How to use a FairDM-powered portal |
| **Portal Administrators** | `docs/portal-administration/` | How to manage and configure a portal |
| **Portal Developers** | `docs/portal-development/` | How to build and customise a portal |
| **Framework Contributors** | `docs/contributing/` | How to contribute to FairDM itself |

```{important}
These four sections are **immutable** — future features must use these section names and locations.
```

## Documentation Principles

FairDM documentation follows these core principles from our [Constitution](.specify/memory/constitution.md#documentation-principles):

1. **Audience-First**: Organize content by reader role, not by technical implementation
2. **Traceability**: Link documentation to specifications and governance principles
3. **Quality Gates**: Automated validation prevents broken links and incomplete documentation
4. **FAIR-Aligned**: Documentation itself follows FAIR principles (Findable, Accessible, Interoperable, Reusable)

## Contributing to Documentation

### Before You Write

1. **Identify your audience**: User, Admin, Developer, or Contributor?
2. **Check existing content**: Is there already documentation for this topic?
3. **Consult the IA guide**: Where should this documentation live?

### While You Write

1. **Follow the style guide**: Clear, concise, example-rich content
2. **Add cross-references**: Link to specs, constitution, related docs
3. **Include examples**: Show, don't just tell
4. **Consider accessibility**: Alt text for images, descriptive link text

### After You Write

1. **Run validation**: Build docs locally and check for errors
2. **Complete the checklist**: Use the feature documentation checklist
3. **Request review**: Tag documentation reviewers in your PR

## Tools and Resources

- **Sphinx**: Documentation build system ([docs](https://www.sphinx-doc.org/))
- **MyST Parser**: Markdown support for Sphinx ([docs](https://myst-parser.readthedocs.io/))
- **PyData Theme**: Our documentation theme ([docs](https://pydata-sphinx-theme.readthedocs.io/))
- **Vale Linter**: Prose linting tool (optional, for style consistency)

## Getting Help

- **Questions about where to document something?** → [File an issue](https://github.com/FAIR-DM/fairdm/issues)
- **Need help with MyST syntax?** → [MyST Syntax Reference](https://myst-parser.readthedocs.io/en/latest/syntax/syntax.html)
- **Found a documentation bug?** → [Report it](https://github.com/FAIR-DM/fairdm/issues/new)

---

## Table of Contents

```{toctree}
:maxdepth: 2

information-architecture
feature-checklist-workflow
cross-references
validation-rules
```

---

**Ready to contribute documentation? Start with the [Information Architecture Guide](information-architecture) to find the right home for your content.**
