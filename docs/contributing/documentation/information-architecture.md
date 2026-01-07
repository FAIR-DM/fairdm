# Documentation Information Architecture

```{contents}
:depth: 3
:local:
```

## Overview

This guide defines **where** documentation lives in the FairDM project and **how** to determine the appropriate location for new documentation. The information architecture is designed to serve four distinct audiences with different needs and technical backgrounds.

```{important}
The top-level structure defined here is **immutable**. Future features MUST use these section names and locations.
```

### Quick Reference

| Audience | Section | Location | Purpose |
|----------|---------|----------|---------|
| Portal Users | User Guide | `docs/user-guide/` | How to use a FairDM-powered data portal |
| Portal Administrators | Portal Administration | `docs/portal-administration/` | How to manage and configure a portal |
| Portal Developers | Portal Development | `docs/portal-development/` | How to build and customise a portal using FairDM |
| Framework Contributors | Contributing | `docs/contributing/` | How to contribute to the FairDM framework itself |

### Special Locations

- **Constitution & Governance**: `.specify/memory/constitution.md` (immutable)
- **Feature Specifications**: `specs/###-feature-name/` (immutable)
- **Templates**: `.specify/templates/`
- **Overview Content**: `docs/overview/` (project goals, background, data model)

---

## The Four Primary Sections

### 1. User Guide (`docs/user-guide/`)

**Target Audience**: Portal Users — researchers, data contributors, and other non-technical users who interact with a FairDM-powered portal through the web interface.

**Purpose**: Explain how to accomplish common tasks in the portal: creating projects, uploading datasets, managing samples and measurements, collaborating with teams, and following FAIR metadata practices.

**Examples of Content**:

- Creating and managing user accounts
- Starting a new research project
- Uploading dataset files and metadata
- Recording sample information
- Viewing and downloading data
- Understanding permission levels
- Following metadata quality guidelines

**When to Use This Section**:

- ✅ Documenting user-facing portal features
- ✅ Explaining workflows for data contributors
- ✅ Providing guidance on FAIR metadata practices for users
- ❌ **NOT** for server installation, configuration, or customisation
- ❌ **NOT** for Python/Django development details

### 2. Portal Administration (`docs/portal-administration/`)

**Target Audience**: Portal Administrators — people responsible for configuring, managing, and maintaining a FairDM portal instance (typically with Django admin access).

**Purpose**: Document administrative tasks: user management, permissions, content moderation, configuration options, backup procedures, and monitoring.

**Examples of Content**:

- Managing user accounts and permissions
- Configuring portal settings through Django admin
- Setting up authentication providers (OAuth, SSO)
- Managing controlled vocabularies and taxonomies
- Content moderation workflows
- Backup and restore procedures
- Monitoring and logging

**When to Use This Section**:

- ✅ Documenting Django admin features
- ✅ Explaining permission models and access control
- ✅ Configuration that doesn't require code changes
- ❌ **NOT** for end-user portal features
- ❌ **NOT** for development setup or code customisation

### 3. Portal Development (`docs/portal-development/`)

**Target Audience**: Portal Developers — developers building or customising a FairDM-powered portal for their specific research community.

**Purpose**: Explain how to set up a development environment, create custom Sample and Measurement models, customise the UI, configure integrations, and deploy a portal to production.

**Examples of Content**:

- Getting started with a new portal project
- Creating custom Sample models (e.g., RockSample, WaterSample)
- Creating custom Measurement models (e.g., ChemicalAnalysis, FlowRate)
- Registering models with the FairDM registry
- Customising templates and themes
- Configuring database connections
- Deploying to production
- API usage and integration

**When to Use This Section**:

- ✅ Development environment setup
- ✅ Creating domain-specific models
- ✅ Customising portal behavior and appearance
- ✅ Production deployment guidance
- ❌ **NOT** for contributing to the FairDM framework itself
- ❌ **NOT** for end-user portal features

### 4. Contributing (`docs/contributing/`)

**Target Audience**: Framework Contributors — developers contributing to the FairDM framework codebase itself (not building portals, but improving the framework).

**Purpose**: Document how to contribute code, tests, and documentation to FairDM, including development workflows, coding standards, testing requirements, and architectural decisions.

**Examples of Content**:

- Setting up FairDM development environment
- Running the test suite
- Code style and linting requirements
- Creating feature specifications
- Writing and validating documentation
- Pull request process
- Architecture and design patterns
- Governance and decision-making

**When to Use This Section**:

- ✅ Framework development setup
- ✅ Contributing features to FairDM core
- ✅ Documentation standards (like this guide!)
- ✅ Testing strategies and requirements
- ❌ **NOT** for portal development (that's Portal Development section)
- ❌ **NOT** for portal usage (that's User Guide or Portal Administration)

---

## Decision Tree: Where Do I Document X?

Follow this decision tree to determine the correct location for your documentation:

```{mermaid}
graph TD
    Start[I need to document something] --> Q1{Who is the primary audience?}

    Q1 -->|Portal end users| UserGuide[docs/user-guide/]
    Q1 -->|Portal administrators| AdminGuide[docs/portal-administration/]
    Q1 -->|Portal developers| DevGuide[docs/portal-development/]
    Q1 -->|Framework contributors| Contributing[docs/contributing/]
    Q1 -->|Governance/principles| Constitution[.specify/memory/]
    Q1 -->|Feature specification| Specs[specs/###-feature-name/]

    UserGuide --> Q2{Type of content?}
    Q2 -->|Task walkthrough| UGTask[user-guide/[feature]/[task].md]
    Q2 -->|Feature overview| UGOverview[user-guide/[feature]/index.md]
    Q2 -->|Getting started| UGStart[user-guide/index.md OR new file]

    AdminGuide --> Q3{Type of content?}
    Q3 -->|User management| AdminUsers[portal-administration/users.md]
    Q3 -->|Configuration| AdminConfig[portal-administration/configuration.md]
    Q3 -->|Monitoring| AdminMonitor[portal-administration/monitoring.md]

    DevGuide --> Q4{Type of content?}
    Q4 -->|Custom models| DevModels[portal-development/models/]
    Q4 -->|UI customisation| DevUI[portal-development/customise/]
    Q4 -->|Deployment| DevDeploy[portal-development/deployment/]
    Q4 -->|API usage| DevAPI[portal-development/api.md]

    Contributing --> Q5{Type of content?}
    Q5 -->|Testing| ContribTest[contributing/testing/]
    Q5 -->|Documentation| ContribDocs[contributing/documentation/]
    Q5 -->|Development setup| ContribSetup[contributing/getting_started.md]
    Q5 -->|Architecture| ContribArch[contributing/architecture/]
```

### Quick Flowchart

**Question 1**: Is this about using a portal's web interface?

- **Yes** → `docs/user-guide/`

**Question 2**: Is this about managing/configuring a portal through Django admin?

- **Yes** → `docs/portal-administration/`

**Question 3**: Is this about building or customising a portal for your research domain?

- **Yes** → `docs/portal-development/`

**Question 4**: Is this about contributing to the FairDM framework code?

- **Yes** → `docs/contributing/`

**Question 5**: Is this about governance principles or feature specifications?

- **Principles** → `.specify/memory/constitution.md`
- **Specification** → `specs/###-feature-name/spec.md`

```{note}
**Feature Documentation Checklists**: When implementing a new feature, create a documentation checklist at `specs/###-feature-name/checklists/documentation.md` to track required documentation updates. See the [Feature Checklist Workflow](./feature-checklist-workflow.md) guide for details.
```

---

## File Creation Guidelines

### When to Create a New File

Create a new documentation file when:

#### a) Standalone Concept

The content represents a **standalone concept** requiring dedicated treatment.

**Example**: Creating a guide for "Data Import/Export" separate from "Dataset Management" because import/export has its own workflows, formats, and error handling.

**Rule of Thumb**: If the topic requires its own introduction, multiple subsections, and could reasonably be linked from multiple places, it deserves its own file.

#### b) Separate User Journey

The content describes a **separate user journey or workflow** from existing documentation.

**Example**: "Creating a Custom Sample Model" vs "Registering a Model with FairDM" — both are part of model development but represent different stages of the journey.

**Rule of Thumb**: If you can describe the content as "How to [accomplish specific goal]" and that goal is distinct from existing "How to" documents, create a new file.

#### c) Content Length Threshold

Adding content to an existing page would **exceed approximately 500 words** of new material.

**Example**: Adding "Bulk Upload" documentation to an existing "Dataset Creation" page — if the bulk upload section would be 600+ words with examples, it probably deserves its own file.

```{note}
This 500-word threshold is a **loose guideline**, not a strict rule. Use judgment based on content complexity and user needs.
```

### When to Update an Existing File

Update an existing file when:

- Adding a small enhancement to an existing feature (<500 words)
- Clarifying or correcting existing documentation
- Adding a single example to an existing workflow
- Updating screenshots or diagrams for an existing concept

### Subdirectory Organisation

Within each primary section, you MAY create subdirectories to organize content. Use subdirectories when:

1. **Multiple related files**: You have 3+ related files that form a logical group
   - Example: `user-guide/account_management/` for create_account.md, reset_password.md, profile_settings.md

2. **Deep hierarchical topics**: The topic has clear sub-topics with their own sub-documentation
   - Example: `contributing/testing/` for unit-tests.md, integration-tests.md, fixtures.md, coverage.md

3. **Feature families**: Related features that share common concepts
   - Example: `portal-development/models/` for sample-models.md, measurement-models.md, polymorphism.md

**Anti-patterns to avoid**:

- ❌ Single-file subdirectories (keep the file at parent level instead)
- ❌ Deeply nested subdirectories (>3 levels becomes hard to navigate)
- ❌ Subdirectories with ambiguous names (be specific: `models/` not `stuff/`)

---

## Cross-Reference Patterns

### Linking to Specifications

Use relative links to reference feature specifications:

```markdown
For implementation details, see the [Custom Model Registration Specification](../../specs/005-custom-model-registration/spec.md).
```

**Pattern**: `[descriptive text](../../specs/###-feature-name/spec.md)`

### Linking to Constitution

Use stable anchor links to reference governance principles:

```markdown
This feature implements the [FAIR-First principle](.specify/memory/constitution.md#i-fair-first-research-portals) by...
```

**Pattern**: `[principle name](.specify/memory/constitution.md#anchor-id)`

### Linking Between Documentation Sections

Use relative links between sections:

```markdown
Portal developers can refer to [Getting Started](../portal-development/getting_started.md) for environment setup.

End users should see [Creating Your First Project](../user-guide/project/create.md) for a step-by-step walkthrough.
```

### Internal Page Anchors

Use MyST anchor syntax for linking to specific sections within a page:

```markdown
See [File Creation Guidelines](#file-creation-guidelines) above for details.
```

MyST automatically generates anchors from headings. You can also create custom anchors:

```markdown
(custom-anchor-name)=
## Section Title

Link to this with: [text](#custom-anchor-name)
```

---

## Lifecycle Markers

Use standard MyST admonitions to mark feature status:

### Deprecated Features

```markdown
:::{{deprecated}} Since version 2.5
The `old_registration()` function is deprecated. Use `registry.register()` instead.

Migration guide: [Model Registration Migration](./migration-guides/registry.md)
:::
```

**When to use**: Feature is being phased out, users should migrate to alternative.

### Experimental Features

```markdown
:::{{warning}} Experimental
The custom serializer API is experimental and may change in future releases.
:::
```

**When to use**: Feature is available but API may change, not recommended for production.

### Maintenance Mode

```markdown
:::{{note}} Maintenance Mode
The legacy admin interface is in maintenance mode. Critical bugs will be fixed, but no new features will be added.
:::
```

**When to use**: Feature is stable but not actively developed, prefer newer alternatives.

---

## Examples

### Example 1: Documenting a New User Feature

**Scenario**: Adding documentation for a new "Batch Upload" feature for datasets.

**Decision Process**:

1. **Audience**: Portal users uploading data → `user-guide/`
2. **Existing content**: `user-guide/dataset/create.md` exists
3. **New content size**: Batch upload requires 3-4 sections with examples (~800 words)
4. **Decision**: Create new file `user-guide/dataset/batch_upload.md`

**Location**: `docs/user-guide/dataset/batch_upload.md`

**Cross-references**:

- Link from `user-guide/dataset/index.md`
- Reference the specification: `../../specs/042-batch-upload/spec.md`
- Link to admin configuration: `../../portal-administration/upload_limits.md`

### Example 2: Documenting a Configuration Option

**Scenario**: New Django setting for file upload size limits.

**Decision Process**:

1. **Audience**: Portal administrators configuring settings → `portal-administration/`
2. **Existing content**: `portal-administration/configuration.md` exists
3. **New content size**: One setting with 2 examples (~150 words)
4. **Decision**: Update existing file

**Location**: Add section to `docs/portal-administration/configuration.md`

**Cross-references**:

- Link to user-facing upload page: `../user-guide/dataset/upload.md`
- Reference constitution principle on data governance

### Example 3: Documenting Custom Model Creation

**Scenario**: Tutorial for creating a custom RockSample model.

**Decision Process**:

1. **Audience**: Portal developers building custom portals → `portal-development/`
2. **Existing content**: `portal-development/models/` subdirectory exists
3. **New content**: Complete tutorial with code examples (~600 words)
4. **Decision**: Create new file in models subdirectory

**Location**: `docs/portal-development/models/rock-sample-tutorial.md`

**Cross-references**:

- Link from `portal-development/models/index.md`
- Reference spec: `../../specs/015-polymorphic-models/spec.md`
- Link to API docs: `../api/sample-serializers.md`

### Example 4: Documenting a Testing Strategy

**Scenario**: Explaining database fixture usage in integration tests.

**Decision Process**:

1. **Audience**: Framework contributors writing tests → `contributing/`
2. **Existing content**: `contributing/testing/` subdirectory exists
3. **New content**: Fixture examples and patterns (~400 words)
4. **Decision**: Could update fixtures.md or create new file; since fixtures.md might not exist yet, check first

**Location**:

- If `fixtures.md` exists and is <500 words → update it
- If doesn't exist or would exceed 500 words → create `contributing/testing/fixtures.md`

**Cross-references**:

- Link from `contributing/testing/index.md`
- Reference pytest fixtures: external link to pytest docs
- Link to factory fixtures: `../testing/factories.md`

---

## FAQ

### Where do API reference docs go?

**Answer**: Depends on audience:

- **Portal developers using the API**: `docs/portal-development/api/`
- **Framework contributors building API features**: `docs/contributing/api-development.md`

Auto-generated API reference (Sphinx autodoc) typically goes in `docs/api/` at root level.

### Where do I document environment variables and configuration?

**Answer**:

- **Runtime configuration** (Django settings): `docs/portal-administration/configuration.md`
- **Development environment setup**: `docs/portal-development/getting_started.md` OR `docs/contributing/getting_started.md` depending on audience
- **Production deployment configuration**: `docs/portal-development/deployment/`

### Where do migration guides go?

**Answer**: In the section that matches the audience being impacted:

- **User-facing breaking changes**: `docs/user-guide/migration-guides/`
- **Admin configuration changes**: `docs/portal-administration/migration-guides/`
- **Developer API changes**: `docs/portal-development/migration-guides/`

### Can I create a fifth top-level section?

**Answer**: No. The four primary sections are **immutable**. If you think you need a new top-level section, consider:

1. Does it fit in `overview/` (project-wide concepts)?
2. Does it belong in `contributing/` (process and governance)?
3. Does it fit in one of the four primary sections with a subdirectory?

If truly none of these work, discuss with the project maintainers — there may be a genuine need, but the bar is high to avoid fragmentation.

### Where do troubleshooting guides go?

**Answer**: Co-located with the feature they're troubleshooting:

- User issues: `docs/user-guide/[feature]/troubleshooting.md`
- Admin issues: `docs/portal-administration/troubleshooting.md`
- Development issues: `docs/portal-development/troubleshooting.md`

---

## Validation

When you've added or updated documentation, ensure it's properly integrated:

1. **Build check**: `poetry run sphinx-build -W -b html docs docs/_build/html`
2. **Link check**: `poetry run sphinx-build -b linkcheck docs docs/_build/linkcheck`
3. **Validate internal links**: `poetry run python .github/scripts/check-internal-links.py`

---

## Related Documentation

- Feature Documentation Checklist Workflow (Coming in Phase 4) — How to track documentation updates for new features
- Documentation Standards (Coming soon) — Writing style, formatting, and quality guidelines
- [Constitution: Documentation Principles](.specify/memory/constitution.md#documentation-principles) — Governance principles for documentation

---

**Questions or suggestions about this information architecture? See [Contributing Guidelines](../getting_started.md) for how to propose improvements.**
