# Overview

FairDM is an open-source Django-based framework designed to help research teams build modern, FAIR-compliant data portals without needing to write complex web application code from scratch. Whether you're evaluating FairDM for a new project or deepening your understanding of its architecture, this section provides the essential context you need.

```{tip}
**Evaluating FairDM?** If you're a developer assessing whether FairDM fits your research community's needs, start with the [Getting Started guide](../portal-development/getting_started.md) for a hands-on walkthrough. Then return here to understand the principles that guide the framework's design.
```

## FairDM Constitution

The [FairDM Constitution](https://github.com/FAIR-DM/fairdm/blob/main/memory/constitution.md) defines the project's core principles, architecture constraints, development workflow, and governance model. It serves as the foundation for all design decisions and contributions to the framework.

Key principles include:

- **FAIR-First**: Every feature must support or at minimum not weaken FAIR characteristics
- **Domain-Driven, Declarative Modeling**: Stable core models with declarative extensions
- **Configuration Over Custom Plumbing**: Registration and configuration, not boilerplate
- **Opinionated, Production-Grade Defaults**: Modern Django stack with sensible defaults
- **Quality, Sustainability, and Community**: Tests, documentation, and clear contribution guidelines

## Where FairDM is headed

[GOALS.md](https://github.com/FAIR-DM/fairdm/blob/main/GOALS.md) lists the standing directions the
framework works toward, and how important each one is.

```{toctree}
:maxdepth: 2

introduction
background
features
data_model
contributors
tech_stack

```
