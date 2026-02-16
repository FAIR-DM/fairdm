```{figure} _static/fairdm_light.svg
:align: center
:target: https://www.fairdm.org
:width: 100%
```

______________________________________________________________________

[![PyPI](https://badge.fury.io/py/fairdm.svg)](https://badge.fury.io/py/fairdm)
[![Build status](https://travis-ci.org/SSJenny90/fairdm.svg?branch=master)](https://travis-ci.org/SSJenny90/fairdm)
[![Code coverage](https://codecov.io/gh/SSJenny90/fairdm/branch/master/graph/badge.svg)](https://codecov.io/gh/SSJenny90/fairdm)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![Documentation Validation](https://github.com/FAIR-DM/fairdm/workflows/Documentation%20Validation/badge.svg)](https://github.com/FAIR-DM/fairdm/actions/workflows/docs-validation.yml)

FairDM is an open-source web framework designed to help you build modern research data portals that fully align with the FAIR data principles. It streamlines the process of creating, deploying, and maintaining research portals by using a modern, well-documented, and widely supported open-source tech stack. FairDM takes care of the complexities of web development with sensible defaults that work out of the box—so researchers and data managers can focus on their data and research, not on technical headaches.

```{tip}
**New to FairDM?** Jump straight to the [Getting Started guide](portal-development/getting_started.md) for a hands-on introduction.
```

## Documentation by Role

Choose the guide that best matches your needs:

### [Developer Guide](portal-development/index.md)

**For portal developers** who want to build and deploy a new FairDM-powered research portal. Learn how to set up your environment, define domain-specific data models, configure your portal, and deploy it to production.

**Start here if**: You're building a FairDM-based portal for your research community

### [Admin Guide](portal-administration/index.md)

**For portal administrators** who manage an existing FairDM portal. Understand your responsibilities for managing users, permissions, datasets, and ensuring FAIR-compliant metadata quality.

**Start here if**: You manage an existing FairDM portal and its users

### [User Guide](user-guide/index.md) (Portal Users)

**For portal users** who add and edit research data in FairDM portals. Learn how to contribute data, understand metadata requirements, and follow FAIR practices.

**Start here if**: You contribute data and metadata to an existing portal

### [Contributing Guide](contributing/index.md) (Framework Contributors)

**For FairDM framework contributors** who want to contribute to the core framework itself (code, documentation, examples). Set up a development environment, understand the architecture, and learn how to propose changes that align with the [FairDM constitution](https://github.com/FAIR-DM/fairdm/blob/main/.specify/memory/constitution.md).

**Start here if**: You want to improve the FairDM framework codebase

```{seealso}
For more on the distinction between portal users and framework contributors, see the [Glossary](more/glossary.md).
```

### [Overview](overview/index.md)

**For evaluators and stakeholders** seeking high-level context on FairDM's vision, FAIR-first philosophy, core architecture, design principles, and the [FairDM Constitution](../.specify/memory/constitution.md).

**Start here if**: You're evaluating FairDM or need high-level context

---

## Governance & Specifications

FairDM follows a governance model defined in the [FairDM Constitution](../.specify/memory/constitution.md), which establishes five core principles:

::::{grid} 1 2 2 3
:gutter: 3

:::{grid-item-card} {octicon}`shield-check;1.5em` FAIR by Design
:link: overview/fair-by-design
:link-type: doc

Every feature improves or maintains FAIR characteristics
+++
[Learn More →](overview/fair-by-design)
:::

:::{grid-item-card} {octicon}`package;1.5em` Domain-Driven, Declarative Modeling
:link: overview/domain-driven-modeling
:link-type: doc

Research communities define schemas declaratively
+++
[Learn More →](overview/domain-driven-modeling)
:::

:::{grid-item-card} {octicon}`gear;1.5em` Configuration Over Custom Plumbing
:link: overview/configuration-over-code
:link-type: doc

Focus on domain modeling, not web plumbing
+++
[Learn More →](overview/configuration-over-code)
:::

:::{grid-item-card} {octicon}`star;1.5em` Opinionated, Production-Grade Defaults
:link: overview/opinionated-defaults
:link-type: doc

Coherent modern stack with sensible defaults
+++
[Learn More →](overview/opinionated-defaults)
:::

:::{grid-item-card} {octicon}`people;1.5em` Quality, Sustainability, and Community
:link: overview/quality-and-sustainability
:link-type: doc

Long-lived research infrastructure with comprehensive testing
+++
[Learn More →](overview/quality-and-sustainability)
:::

::::

Feature specifications and implementation plans are maintained in the [`specs/` directory](https://github.com/FAIR-DM/fairdm/tree/main/specs).

```{toctree}
:maxdepth: 1
:hidden:

overview/index
user-guide/index
portal-development/index
portal-administration/index
contributing/index
more/glossary
more/changelog
more/support
```

## Help Improve These Docs

Found something unclear, incorrect, or missing? We welcome your feedback!

- **Report documentation issues**: [Open an issue on GitHub](https://github.com/FAIR-DM/fairdm/issues/new?labels=documentation) describing what needs improvement
- **Suggest improvements**: [Start a discussion](https://github.com/FAIR-DM/fairdm/discussions) to propose enhancements
- **Contribute directly**: See the [Contributing Guide](contributing/index.md) to submit documentation pull requests

Your feedback helps make FairDM more accessible for everyone. Thank you!

<!-- ## Indices and tables

- {ref}`genindex`
- {ref}`modindex`
- {ref}`search` -->
