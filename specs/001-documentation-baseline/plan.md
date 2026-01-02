# Implementation Plan: 001-documentation-baseline

**Branch**: `001-documentation-baseline` | **Date**: 2026-01-02 | **Spec**: `specs/001-documentation-baseline/spec.md`
**Input**: Feature specification from `/specs/001-documentation-baseline/spec.md`

**Note**: This plan is maintained by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Establish a coherent, role-based documentation baseline for FairDM that aligns with the FAIR-first constitution and clearly serves four audiences: portal developers, portal administrators, data contributors, and framework contributors, while also providing a high-quality About/Overview experience for any new reader. The feature updates the Sphinx/MyST-based docs (powered by `fairdm-docs` and `pydata-sphinx-theme`) to provide opinionated Getting Started journeys, role-specific guides, a FAIR-aligned overview of goals/core features/core data model, and a dedicated Contributors explanation, with cross-linked conceptual material throughout, without over-prescribing environment or tooling details beyond the canonical `poetry run invoke docs` build entrypoint.

## Technical Context

**Language/Version**: Python 3.10+ (current dev environment Python 3.11)  
**Primary Dependencies**: Django, Sphinx (via `fairdm-docs`), MyST Markdown, `pydata-sphinx-theme`, `sphinx-design`, Bootstrap 5, Context7 for library docs  
**Storage**: N/A for this feature (documentation only; code and data models already exist in core FairDM)  
**Testing**: Sphinx docs build via `poetry run invoke docs` as the canonical documentation quality gate; manual validation per user story acceptance scenarios  
**Target Platform**: HTML documentation for web consumption (hosted alongside the FairDM project site)
**Project Type**: Single monolithic Django project with integrated Sphinx documentation  
**Performance Goals**: Documentation build completes within a few seconds on a developer machine; no heavy, blocking assets introduced; navigation remains responsive  
**Constraints**: Must not introduce tooling-specific commands into user-facing docs beyond high-level flows; FR-006 requires environment- and tooling-agnostic descriptions where possible; must not change the underlying Django stack or documentation toolchain  
**Scale/Scope**: One existing framework repository (`fairdm/`), one demo portal (`fairdm_demo/`), and a single Sphinx docs tree (`docs/`) covering four primary audiences

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **FAIR-first**: The feature strengthens FAIR compliance by clarifying metadata responsibilities, contributor workflows, and exposing core entities and APIs through documentation. No changes are made to runtime behavior.
- **Domain-driven, declarative modeling**: This work documents the existing domain model (Projects, Datasets, Samples, Measurements, Contributors, Organizations) and their extension points; it does not alter models or introduce ad-hoc structures.
- **Configuration over custom plumbing**: The plan emphasises registry- and configuration-centric explanations (e.g., how to register models) rather than encouraging ad-hoc view or routing code.
- **Opinionated, production-grade defaults**: Documentation assumes the existing Django + PostgreSQL + Sphinx + Bootstrap 5 stack; no new core technologies are introduced.
- **Quality, sustainability, and community**: The feature adds clear contributor and framework-contributor guidance, surfaces quality gates (tests, typing, linting, docs via `poetry run invoke docs`), and anchors changes in the FairDM constitution.

At this stage there are **no intentional violations** of the constitution; Complexity Tracking remains empty.

**Deferred NFRs**: NFR-003 (internationalization readiness) and NFR-004 (accessibility best practices) are structural constraints handled by the existing Sphinx/pydata-sphinx-theme stack and are not explicitly validated by tasks in this feature. Future features MAY add explicit i18n/a11y audit tasks if needed.

## Project Structure

### Documentation (this feature)

```text
specs/001-documentation-baseline/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
fairdm/                    # Core FairDM Django framework (models, views, registry, plugins)
fairdm_demo/               # Demo portal used for Getting Started and admin/contributor flows
docs/                      # Sphinx documentation (admin-guide, user-guide, developer-guide, contributing, about, more)
tests/                     # pytest test suite for core and integrations
config/                    # Django settings and URL configuration
tasks.py                   # Invoke tasks, including `poetry run invoke docs` docs build entrypoint
pyproject.toml             # Tooling configuration (pytest, mypy, Ruff, Sphinx, etc.)
```

**Structure Decision**: Use the existing monolithic Django project plus a single Sphinx docs tree. This feature operates entirely within `docs/` and `specs/001-documentation-baseline/`, reusing the existing FairDM core and demo project structure without introducing new top-level packages or services.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
