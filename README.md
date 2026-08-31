# FairDM

[![CI](https://github.com/FAIR-DM/fairdm/actions/workflows/ci.yml/badge.svg)](https://github.com/FAIR-DM/fairdm/actions/workflows/ci.yml)
[![Documentation](https://readthedocs.org/projects/fairdm/badge/?version=latest)](https://fairdm.readthedocs.io/en/latest/)
[![PyPI](https://img.shields.io/pypi/v/fairdm)](https://pypi.org/project/fairdm/)
[![codecov](https://codecov.io/gh/FAIR-DM/fairdm/branch/main/graph/badge.svg?token=0Q18CLIKZE)](https://codecov.io/gh/FAIR-DM/fairdm)
![GitHub](https://img.shields.io/github/license/FAIR-DM/fairdm)
![GitHub last commit](https://img.shields.io/github/last-commit/FAIR-DM/fairdm)

> **A Django-based framework for building FAIR research data portals with minimal code**

FairDM makes it trivial for research teams to define domain-specific sample and measurement models and run a fully functional data portal without writing views, URL routing, or frontend code.

---

## 🎯 What is FairDM?

FairDM is an opinionated **Django framework** (not a library) designed specifically for research data management. It enables researchers with basic Python skills to:

- Define custom domain models for **samples** and **measurements**
- Get a fully functional web portal **without writing views or templates**
- Ensure data follows **FAIR principles** (Findable, Accessible, Interoperable, Reusable)
- Manage research **projects**, **datasets**, and **contributors** out of the box
- Import/export data in multiple formats with zero configuration
- Control access with fine-grained **object-level permissions**

---

## Scope & philosophy

### What FairDM is

A batteries-included Django framework for building research data portals. You describe your
samples and measurements as Django models, register them, and get the portal without writing that
layer yourself: views, URLs, forms, filters, tables, admin and API.

### What FairDM is deliberately not

- **Not a library of parts.** It is opinionated and owns the application shell. If you want to
  assemble your own stack from independent components, this is the wrong starting point.
- **Not a generic CMS.** The core model (projects, datasets, samples, measurements and
  contributors) is fixed, because it is what makes portals interoperable and citable.
- **Not a single portal.** Domain-specific schemas belong in portals that build on FairDM, not
  in the framework itself.
- **Not a JavaScript application.** The server-rendered baseline is the product, not a fallback.
- **Not a formal publisher.** Publishing a dataset in FairDM makes it visible to other users of
  the portal. Sending metadata to a data publisher and receiving a DOI in return is a separate
  act, and it belongs to an addon rather than the core.
- **Not the home of every feature.** The core stays small and the framework grows through
  addons. A capability that only some portals need is an addon, not a core concern.

### When principles collide

- **Configuration over code** — declarative model registration with sensible defaults.
- **Domain-first modelling** — accurate scientific representation outranks framework convenience.
- **Progressive complexity** — registering a model works on its own. Custom forms, filters and
  views come later, and only for the portals that need them.
- **No frontend knowledge required** — a working portal must not depend on template or JS skills.
- **FAIR by design** — metadata, stable identifiers and machine access are built in, not added on.
- **A stable backbone beats a fast one** — research portals outlive their funding, so the core
  model changes slowly and deliberately.

Where the framework is headed is a separate question from what it is. That lives in
[GOALS.md](https://github.com/FAIR-DM/fairdm/blob/main/GOALS.md).

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.13+**
- **Poetry** for dependency management
- **PostgreSQL** (recommended) or SQLite for development

### Installation

```bash
# Clone the repository
git clone https://github.com/FAIR-DM/fairdm.git
cd fairdm

# Install dependencies with Poetry
poetry install

# Activate the virtual environment
poetry shell

# Run database migrations
poetry run python manage.py migrate

# Create a superuser
poetry run python manage.py createsuperuser

# Run the development server
poetry run python manage.py runserver
```

Visit `http://localhost:8000` to see your portal!

---

## 📦 Core Concepts

### Projects, Datasets, Samples & Measurements

FairDM organizes research data using a hierarchical structure:

```
Project
└── Dataset
    ├── Sample (your custom types)
    │   └── Measurement (your custom types)
    └── Sample
        └── Measurement
```

- **Project**: Top-level container for research initiatives
- **Dataset**: Collection of related samples with shared metadata
- **Sample**: Domain-specific sample types (e.g., RockSample, WaterSample)
- **Measurement**: Domain-specific measurements on samples (e.g., XRFMeasurement)

### Portal Configuration

A portal gets its entire Django configuration from one call:

```python
# config/settings.py
import fairdm

fairdm.setup(apps=["myportal"], addons=["fairdm_discussions"])
```

FairDM's settings are production-grade in every environment. Each environment is an override layered on top, named by `DJANGO_ENV` and applied only if it exists — so `config/development.py` beside your settings module tunes development, and an environment nobody ships a module for simply gets the production baseline. In production, configuration that would leave the portal unsafe stops it starting.

See [Configuration](docs/portal-development/configuration.md) for the layer order, the environment variables and `manage.py show_config`.

### Model Registration

The heart of FairDM is its **registry system**. Define your models, register them, and get automatic:

- ✅ Create/Read/Update/Delete views
- ✅ List tables with sorting and filtering
- ✅ Forms with Bootstrap 5 styling
- ✅ REST API endpoints (optional)
- ✅ Import/Export functionality
- ✅ Admin integration

#### Example: Registering a Custom Sample

```python
# myapp/models.py
from fairdm.core.models import Sample
from django.db import models

class RockSample(Sample):
    """Custom sample type for geological specimens."""

    rock_type = models.CharField(max_length=100)
    collection_date = models.DateField()
    weight_grams = models.DecimalField(max_digits=10, decimal_places=2)


# myapp/config.py
from fairdm.core.sample.config import BaseSampleConfiguration
from fairdm.registry import register
from .models import RockSample

@register
class RockSampleConfig(BaseSampleConfiguration):
    model = RockSample
    fields = ["name", "rock_type", "collection_date", "weight_grams", "location"]
```

`BaseSampleConfiguration` is the recommended base for a specimen type's registry configuration —
it declares the shared `fields` list every generated component falls back to, so you only state it
once. A configuration that relies on the registry auto-detecting a different field list per
component (table vs. form vs. filter set) should subclass the plain `ModelConfiguration` instead.

That's it! You now have:

- A working web interface for managing rock samples
- Sortable/filterable tables
- Create/update/delete forms
- Import/export to CSV/Excel
- REST API endpoints (if enabled)

---

## 🎨 Features

### ✨ Auto-Generated Components

For every registered model, FairDM automatically generates:

| Component | Library | Purpose |
|-----------|---------|---------|
| **Forms** | Django Forms + Crispy Forms | Create/edit with Bootstrap 5 styling |
| **Tables** | django-tables2 | Sortable, paginated lists |
| **Filters** | django-filter | Advanced filtering UI |
| **Serializers** | Django REST Framework | JSON API responses |
| **Resources** | django-import-export | CSV/Excel import/export |
| **Admin** | Django Admin | Optional admin interface |

### 🔐 Permissions & Access Control

- **Object-level permissions** via django-guardian
- Role-based access (viewer, editor, manager) at Project/Dataset level
- Public/private dataset visibility controls
- Add contributors to a project or dataset, including unclaimed profiles for people without accounts yet

### 📊 Data Import/Export

- **Formats**: CSV, Excel (XLSX), JSON, ODS
- **Background processing**: Large imports via Celery tasks
- **Validation**: Automatic field validation and error reporting
- **Templates**: Export sample templates for data collection

### 🔌 Plugin System

Extend FairDM with custom functionality:

- Add analysis panels to detail views
- Create custom visualizations
- Integrate third-party tools
- Build domain-specific workflows

### 🌍 Modern Frontend Stack

- **django-mvp** — Shared application shell built on Tailwind CSS and daisyUI
- **HTMX** — Dynamic interactions without writing JavaScript
- **Alpine.js** — Lightweight reactivity for complex interactions
- **Django Cotton** — Reusable component-based templates

---

## 📚 Documentation

Full documentation is available at: **<https://fairdm.github.io/fairdm/>**

### Documentation Sections

- **[User Guide](https://fairdm.github.io/fairdm/user-guide/)** — For portal users and contributors
- **[Developer Guide](https://fairdm.github.io/fairdm/portal-development/)** — Build your own research portal
- **[Admin Guide](https://fairdm.github.io/fairdm/portal-administration/)** — Portal administration and maintenance
- **[Contributing](https://fairdm.github.io/fairdm/contributing/)** — Contribute to FairDM framework development

---

## 🧪 Demo Application

Explore a working example in the `fairdm_demo/` directory:

```bash
# The demo app showcases:
# - Custom Sample and Measurement models
# - Model registration and configuration
# - Custom forms, tables, and filters
# - Plugin development examples
```

The demo app serves as **executable documentation** and demonstrates best practices for building portals with FairDM.

---

## 🛠️ Development

### Running Tests

```bash
# Run the full test suite
poetry run pytest

# Run with coverage
poetry run pytest --cov=fairdm --cov-report=html

# Run specific test file
poetry run pytest tests/test_registry.py

# Run with verbose output
poetry run pytest -v
```

### Code Quality

FairDM uses **Ruff** for linting and formatting:

```bash
# Lint the codebase
poetry run ruff check .

# Format code
poetry run ruff format .

# Check type hints with mypy
poetry run mypy fairdm
```

### Project Commands

Useful Invoke tasks (see `tasks.py`):

```bash
# Show available tasks
poetry run invoke -l

# Run database migrations
poetry run invoke migrate

# Create test data
poetry run invoke create-test-data

# Build documentation
poetry run invoke docs
```

---

## 🏗️ Technology Stack

### Core Framework

- **Django 5.1+** — Web framework
- **Python 3.13+** — Programming language
- **PostgreSQL** — Database (recommended)
- **Redis** — Caching and task queue

### Key Dependencies

- **django-polymorphic** — Polymorphic model inheritance
- **django-guardian** — Object-level permissions
- **django-tables2** — Table rendering
- **django-filter** — Filtering system
- **django-import-export** — Data import/export
- **django-htmx** — HTMX integration
- **django-cotton** — Component-based templates
- **celery** — Background task processing

See [pyproject.toml](pyproject.toml) for the complete dependency list.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

We welcome contributions! See our [Contributing Guide](CONTRIBUTING.md) for:

- **Quick setup**: Run `bash scripts/dev-setup.sh` to get started
- **Development workflow**: Install git hooks to prevent CI failures
- **Code style and conventions**: Ruff formatting (120 char lines)
- **Testing requirements**: pytest with >80% coverage goal
- **Pull request process**: Pre-push validation ensures CI passes

**Before your first push**, install git hooks to run CI checks locally:

```bash
poetry run invoke install-hooks
```

This prevents CI failures by running the same linting and formatting checks locally.

---

## 🌟 Project Status

FairDM is under active development. Current focus areas:

- ✅ Core framework and registry system
- ✅ Model registration and auto-generation
- ✅ Permissions and access control
- 🚧 Plugin system expansion
- 🚧 REST API enhancements
- 🚧 Advanced data visualization
- 📋 Cloud deployment guides
- 📋 Extended documentation

---

## 📞 Support & Community

- **Documentation**: <https://fairdm.github.io/fairdm/>
- **Issues**: <https://github.com/FAIR-DM/fairdm/issues>
- **Discussions**: <https://github.com/FAIR-DM/fairdm/discussions>
- **GitHub**: <https://github.com/FAIR-DM/fairdm>

---

## [![Repography logo](https://images.repography.com/logo.svg)](https://repography.com) / Recent activity [![Time period](https://images.repography.com/38992691/FAIR-DM/fairdm/recent-activity/wR5Qyb7vQtQMDQBP1um1HrDQXvNCa5onTbGDdtwZKCg/hzg3IEH7q7FhzX3eX5c_BGACTiJz-_dhyInw4d4n_bU_badge.svg)](https://repography.com)

[![Timeline graph](https://images.repography.com/38992691/FAIR-DM/fairdm/recent-activity/wR5Qyb7vQtQMDQBP1um1HrDQXvNCa5onTbGDdtwZKCg/hzg3IEH7q7FhzX3eX5c_BGACTiJz-_dhyInw4d4n_bU_timeline.svg)](https://github.com/FAIR-DM/fairdm/commits)
[![Issue status graph](https://images.repography.com/38992691/FAIR-DM/fairdm/recent-activity/wR5Qyb7vQtQMDQBP1um1HrDQXvNCa5onTbGDdtwZKCg/hzg3IEH7q7FhzX3eX5c_BGACTiJz-_dhyInw4d4n_bU_issues.svg)](https://github.com/FAIR-DM/fairdm/issues)
[![Pull request status graph](https://images.repography.com/38992691/FAIR-DM/fairdm/recent-activity/wR5Qyb7vQtQMDQBP1um1HrDQXvNCa5onTbGDdtwZKCg/hzg3IEH7q7FhzX3eX5c_BGACTiJz-_dhyInw4d4n_bU_prs.svg)](https://github.com/FAIR-DM/fairdm/pulls)
[![Trending topics](https://images.repography.com/38992691/FAIR-DM/fairdm/recent-activity/wR5Qyb7vQtQMDQBP1um1HrDQXvNCa5onTbGDdtwZKCg/hzg3IEH7q7FhzX3eX5c_BGACTiJz-_dhyInw4d4n_bU_words.svg)](https://github.com/FAIR-DM/fairdm/commits)
[![Top contributors](https://images.repography.com/38992691/FAIR-DM/fairdm/recent-activity/wR5Qyb7vQtQMDQBP1um1HrDQXvNCa5onTbGDdtwZKCg/hzg3IEH7q7FhzX3eX5c_BGACTiJz-_dhyInw4d4n_bU_users.svg)](https://github.com/FAIR-DM/fairdm/graphs/contributors)
[![Activity map](https://images.repography.com/38992691/FAIR-DM/fairdm/recent-activity/wR5Qyb7vQtQMDQBP1um1HrDQXvNCa5onTbGDdtwZKCg/hzg3IEH7q7FhzX3eX5c_BGACTiJz-_dhyInw4d4n_bU_map.svg)](https://github.com/FAIR-DM/fairdm/commits)

---

Made with ❤️ for the research community
