# Feature Documentation Checklist

**Feature**: [Feature Name]
**Spec**: [Link to spec.md]
**Date Created**: YYYY-MM-DD
**Status**: not-started | in-progress | completed

## Purpose

This checklist ensures all required documentation is updated when shipping a feature. Complete all relevant sections before marking the feature as done.

## How to Use This Checklist

1. **Copy this template** to your feature directory: `specs/###-feature-name/checklists/documentation.md`
2. **Fill in the header** with your feature name, spec link, and date
3. **Mark relevant sections** - not all sections apply to every feature
4. **Check off items** as you complete them using `[x]`
5. **Update status** as you progress: not-started → in-progress → completed
6. **Link to updated docs** in the "Documentation Updated" column

## When This Checklist is Required

- ✅ **Required**: All features that modify user-facing behavior, add new functionality, or change configuration
- ✅ **Required**: Features that introduce new models, UI components, or APIs
- ✅ **Required**: Breaking changes or deprecations
- ⚠️ **Optional**: Internal refactoring that doesn't change external interfaces
- ⚠️ **Optional**: Bug fixes that don't introduce new concepts

## Feature Type Classification

Select the feature types that apply to your feature:

- [ ] New core model (Project, Dataset, Sample, Measurement extensions)
- [ ] New UI component (forms, tables, filters, views)
- [ ] Configuration change (settings, environment variables, deployment)
- [ ] API change (REST endpoints, serializers, filters)
- [ ] Breaking change (removes or modifies existing functionality)
- [ ] Plugin or extension system change
- [ ] CLI command or management command
- [ ] Testing or quality infrastructure
- [ ] Documentation infrastructure (meta-documentation)

---

## Documentation Sections

### Developer Guide (`docs/developer-guide/`)

**Audience**: Portal builders who are implementing FairDM for their research domain

- [ ] Model configuration documented (if feature adds/modifies models)
- [ ] Registration API usage documented (if feature uses registry)
- [ ] Configuration options documented (if feature adds settings)
- [ ] Code examples provided for common use cases
- [ ] Migration guide provided (if breaking change)
- [ ] Plugin integration documented (if feature is pluggable)

**Documentation Updated**:
- [Link to page(s)]

**Notes**:
[Any specific guidance or context]

---

### Admin Guide (`docs/admin-guide/`)

**Audience**: Portal administrators who manage deployed FairDM instances

- [ ] Admin interface changes documented (if feature modifies Django admin)
- [ ] Permissions and access control documented (if feature affects permissions)
- [ ] Deployment considerations documented (if feature affects infrastructure)
- [ ] Monitoring or maintenance tasks documented (if feature requires ops work)
- [ ] Troubleshooting guide updated (if feature has common issues)

**Documentation Updated**:
- [Link to page(s)]

**Notes**:
[Any specific guidance or context]

---

### Contributor Guide (`docs/contributor-guide/`)

**Audience**: Portal users who contribute data and use portal features

- [ ] Feature usage guide created (if feature is user-facing)
- [ ] Workflow or process documentation updated (if feature changes user workflows)
- [ ] UI screenshots or examples provided (if feature has visual components)
- [ ] Common tasks or tutorials updated (if feature affects common patterns)
- [ ] FAQ updated (if feature raises common questions)

**Documentation Updated**:
- [Link to page(s)]

**Notes**:
[Any specific guidance or context]

---

### Contributing Guide (`docs/contributing/`)

**Audience**: Framework contributors who develop FairDM itself

- [ ] Architecture documentation updated (if feature changes core architecture)
- [ ] Development workflow documentation updated (if feature changes dev process)
- [ ] Testing guidelines updated (if feature introduces new testing patterns)
- [ ] Code style or conventions updated (if feature establishes new patterns)
- [ ] Release process updated (if feature affects versioning or releases)

**Documentation Updated**:
- [Link to page(s)]

**Notes**:
[Any specific guidance or context]

---

### Governance & Specifications

- [ ] Spec cross-references added to documentation (link to `specs/###-feature-name/spec.md`)
- [ ] Constitution cross-references added (if feature aligns with specific principles)
- [ ] Feature listed in roadmap or features overview (if significant feature)

**Documentation Updated**:
- [Link to page(s)]

**Notes**:
[Any specific guidance or context]

---

### API Documentation (if applicable)

- [ ] API endpoint documented (if REST API feature)
- [ ] Request/response examples provided
- [ ] Authentication/authorization requirements documented
- [ ] Rate limiting or performance considerations documented

**Documentation Updated**:
- [Link to page(s)]

**Notes**:
[Any specific guidance or context]

---

## Examples of Completed Checklists

### Example 1: New Core Model Feature

**Feature**: Custom Sample Fields
**Feature Type**: New core model, Configuration change

**Completed Sections**:
- ✅ Developer Guide: Model configuration (how to add custom fields)
- ✅ Developer Guide: Registration API (how to register custom Sample types)
- ✅ Admin Guide: Admin interface (how custom fields appear in admin)
- ✅ Contributor Guide: Feature usage (how contributors fill in custom fields)
- ✅ Spec cross-reference added

**Skipped Sections**:
- ❌ API Documentation (no REST API changes in this feature)
- ❌ CLI commands (no new management commands)

---

### Example 2: Breaking Change Feature

**Feature**: Renamed Configuration Setting
**Feature Type**: Breaking change, Configuration change

**Completed Sections**:
- ✅ Developer Guide: Migration guide (how to update settings)
- ✅ Developer Guide: Configuration options (new setting name documented)
- ✅ Admin Guide: Deployment considerations (how to update production configs)
- ✅ Contributing Guide: Release process (noted in breaking changes section)

**Skipped Sections**:
- ❌ Contributor Guide (no user-facing changes)
- ❌ API Documentation (no API changes)

---

### Example 3: UI Component Feature

**Feature**: New Data Visualization Plugin
**Feature Type**: New UI component, Plugin system

**Completed Sections**:
- ✅ Developer Guide: Plugin integration (how to register visualization plugins)
- ✅ Admin Guide: Permissions (who can access visualizations)
- ✅ Contributor Guide: Feature usage (how to use visualizations)
- ✅ Contributor Guide: UI screenshots (visualization examples)
- ✅ API Documentation: API endpoints (data endpoints for visualizations)

**Skipped Sections**:
- ❌ Breaking changes (no breaking changes)
- ❌ CLI commands (no new commands)

---

## Validation Criteria

Before marking this checklist as complete, verify:

- [ ] At least one section has items marked `[x]`
- [ ] Each checked item has a link to the updated documentation page
- [ ] All documentation builds successfully with `poetry run sphinx-build docs docs/_build`
- [ ] All internal links are valid (verified by linkcheck)
- [ ] Spec cross-references are present in at least one documentation page
- [ ] Documentation follows the information architecture guidelines in `docs/contributing/documentation-standards.md`

---

## Completion

**Date Completed**: YYYY-MM-DD
**Completed By**: [Your Name]
**Final Status**: ✅ completed

**Notes**:
[Any final notes or context for future reference]
