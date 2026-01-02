# Change log

## Documentation Baseline (2024-Q4)

**New Documentation Structure**: FairDM now provides comprehensive role-based documentation for all user types:

### For Portal Developers
- **[Getting Started Guide](../developer-guide/getting_started.md)**: Complete walkthrough from running the demo portal to defining custom models, registering them, and verifying via UI and API
- **[Before You Begin](../developer-guide/before_you_begin.md)**: Prerequisites, tools, and setup requirements
- Enhanced [Developer Guide](../developer-guide/index.md) with clear role description and navigation

### For Portal Administrators
- **[Managing Users and Permissions](../admin-guide/managing_users_and_permissions.md)**: Comprehensive guide to user management, pre-configured groups, and object-level permissions
- **[Adjusting Dataset Access](../admin-guide/adjusting_dataset_access.md)**: Step-by-step scenarios for controlling dataset access and enabling public FAIR-compliant data
- Enhanced [Admin Guide](../admin-guide/index.md) with core entities overview and responsibilities

### For Data Contributors
- **[Getting Started as a Contributor](../contributor-guide/getting_started.md)**: First contribution walkthrough covering login, dataset navigation, adding samples and measurements
- **[Understanding Core Data Structures](../contributor-guide/core_data_model.md)**: Contributor-focused explanation of Projects, Datasets, Samples, and Measurements
- **[Metadata Best Practices](../contributor-guide/metadata_practices.md)**: Practical tips for FAIR-compliant metadata, controlled vocabularies, and provenance recording
- Enhanced [Contributor Guide](../contributor-guide/index.md) with FAIR principles explanation and contributor role clarity

### For Framework Contributors
- **[Before You Start](../contributing/before_you_start.md)**: Complete development environment setup instructions (fork, clone, install, migrate, test)
- **[Python Code Development](../contributing/django_dev.md)**: Quality gates documentation covering tests, type checking, linting, and documentation builds with examples
- **[Contributing to FairDM](../contributing/getting_started.md)**: Full contribution workflow from issue creation to pull request merge, with explicit [constitution](https://github.com/FAIR-DM/fairdm/blob/main/.specify/memory/constitution.md) alignment guidance
- Enhanced [Contributing Guide](../contributing/index.md) with clear framework contributor role distinction

### Navigation & Usability Improvements
- **Contextual navigation**: "You are here" boxes on deep pages help users orient themselves after landing from search
- **Cross-references**: Extensive linking between guides and conceptual material
- **Constitution integration**: Prominent constitution link in [Overview section](../overview/index.md) with evaluator framing
- **Documentation feedback**: Clear [reporting mechanism](../index.md#help-improve-these-docs) for issues and improvements

### What This Means for You
- **New users**: Start with your role's "Getting Started" guide for a guided first experience
- **Experienced users**: Navigate directly to specific guides via the role-based structure
- **Evaluators**: Review [Getting Started](../developer-guide/getting_started.md) first, then explore the [constitution](https://github.com/FAIR-DM/fairdm/blob/main/.specify/memory/constitution.md) for principles
- **Contributors**: All contribution types now have clear, independent workflows

---

## 0.1.0 (2023-01-22)

- First release on PyPI.
