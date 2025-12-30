---
html_theme.sidebar_secondary.remove: true
---

# Developer Guide

**For portal developers** who want to build and deploy a new FairDM-powered research portal.

## Your Role

As a portal developer, you will:

- **Build a custom research portal**: Create a FairDM-based portal tailored to your research community's needs
- **Define domain-specific models**: Extend the core Sample and Measurement models with your own fields and validation
- **Configure and customize**: Set up your portal's appearance, permissions, and behavior
- **Deploy to production**: Launch your portal in the cloud or on your own infrastructure

## Prerequisites

You should have:

- Working knowledge of Python and general web development concepts
- Basic familiarity with Django (ideally having completed the [official Django tutorials](https://docs.djangoproject.com/en/stable/intro/tutorial01/))
- Basic understanding of Docker for deployment (optional but recommended)

## Quick Start

```{important}
**New to FairDM?** Start with the [Getting Started guide](getting_started.md) for a complete walkthrough from running the demo to creating your first custom models.
```

The Getting Started guide will walk you through:

1. Running the FairDM demo portal locally
2. Creating your first custom Sample model (e.g., `RockSample`)
3. Creating your first custom Measurement model (e.g., `MineralAnalysis`)
4. Registering your models and seeing them in the UI
5. Verifying programmatic access via the API

**Time required**: ~30-60 minutes

## Contents

```{toctree}
:caption: Getting started
:maxdepth: 2

getting_started
before_you_begin
setting_up
project_directory
committing_to_github

```

```{toctree}
:caption: Defining models
:maxdepth: 2

defining_models
special_fields
controlled_vocabularies
model_configuration
using_the_registry
```

```{toctree}
:caption: Customisation
:maxdepth: 2

customise/logo
customise/theme
component_library/index
```




```{toctree}
:caption: How to
:maxdepth: 2

create_a_plugin
quality_control

```

```{toctree}
:caption: Deployment
:maxdepth: 1
:hidden:

emails
social_accounts
deployment_guide/production

```
