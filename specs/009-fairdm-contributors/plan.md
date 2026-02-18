# Implementation Plan: FairDM Contributors System

**Branch**: `009-fairdm-contributors` | **Date**: 2026-02-18 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/009-fairdm-contributors/spec.md`

## Summary

The contributors app is the human infrastructure layer of FairDM portals, managing people and organizations who participate in research data creation, curation, and sharing. This feature refactors and completes the existing `fairdm/contrib/contributors/` app by:

1. **Migrating** `OrganizationMember` → `Affiliation` with time-bound fields (PartialDateField for start/end dates) while preserving the security-critical `type` field for membership verification
2. **Implementing** claimed/unclaimed Person semantics (`email=NULL`, `is_active=False`, no usable password for unclaimed) — data model support only; full claiming flows deferred to Feature 010
3. **Adding** asynchronous ORCID/ROR sync via Celery tasks (no synchronous external API calls in lifecycle hooks)
4. **Implementing** `manage_organization` object-level permission via django-guardian for organization ownership
5. **Adding** privacy controls via `privacy_settings` JSONField with `get_visible_fields(viewer)` method
6. **Refactoring** the transform architecture with a `TransformRegistry` singleton for discoverable, extensible metadata transforms (DataCite, Schema.org, CSL-JSON, ORCID, ROR)
7. **Creating** `tasks.py` with three Celery tasks: identifier sync, periodic refresh, and duplicate detection
8. **Fixing** 5 identified bugs in the current models.py
9. **Completing** stub methods in managers and utility functions

**Key architectural decisions:**
- **PartialDateField** for affiliation dates allows year-only, year-month, or full date precision (prevents fabricated exact dates for historical affiliations)
- **Preserve `type` field** as security/verification mechanism: PENDING (0) → MEMBER (1) → ADMIN (2) → OWNER (3) state machine prevents unauthorized self-affiliation with organizations

The technical approach prioritizes async-first external API interaction, research-driven solutions over perpetuating incomplete patterns, and FAIR-compliant metadata export throughout.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: Django 5.x, django-polymorphic, django-lifecycle, django-guardian, django-allauth, django-countries, Celery, requests, easy-thumbnails, shortuuid, django-ordered-model, research-vocabs, django-import-export, django-autocomplete-light, django-select2
**Storage**: PostgreSQL (production), SQLite (development/testing)
**Testing**: pytest + pytest-django (test-first, Red → Green → Refactor per Constitution V)
**Target Platform**: Linux server (Docker/docker-compose), development on Windows/macOS/Linux
**Project Type**: Django app within a monolithic web framework
**Performance Goals**: Contributor lookup < 200ms for 10,000+ records (SC-007); ORCID/ROR sync < 5s per identifier (SC-002, SC-003)
**Constraints**: No synchronous external API calls in HTTP request cycle; Celery worker required for async tasks; weekly ORCID rate limit budget (~24 req/s)
**Scale/Scope**: 10,000+ contributor records per portal; ~3,500 LOC in existing app (rework, not greenfield)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. FAIR-First** | PASS | ORCID/ROR identifiers as first-class; DataCite + Schema.org exports; privacy controls respect FAIR metadata requirements |
| **II. Domain-Driven Modeling** | PASS | Models extend FairDM base classes (PolymorphicModel); vocabulary-backed roles via research-vocabs; no ad-hoc runtime structures |
| **III. Configuration Over Plumbing** | PASS | Transform registry enables declarative format registration; admin classes auto-configured; no custom views required for basic contributor management |
| **IV. Opinionated Defaults** | PASS | All dependencies are existing framework stack (Django, django-guardian, Celery, etc.); no new framework-level dependencies introduced |
| **V. Test-First Quality** | PASS | Plan requires Red-Green-Refactor; contract tests defined in contracts/; TransformTestMixin for transform testing; Django system checks between phases |
| **VI. Documentation Critical** | PASS | quickstart.md generated; API contracts documented; plan requires docs updated alongside implementation |
| **VII. Living Demo** | PASS | Demo app must be updated in same PR; demo tests required for admin views and model usage |

### Post-Design Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. FAIR-First** | PASS | Data model includes persistent identifiers (ORCID, ROR, ShortUUID); transforms support bidirectional conversion; privacy design distinguishes FAIR-required fields from optional personal data |
| **II. Domain-Driven Modeling** | PASS | Affiliation model correctly captures time-bound institutional relationships; Contribution GFK pattern consistent with framework conventions; no schema drift from backbone |
| **III. Configuration Over Plumbing** | PASS | `@transforms.register("format")` decorator pattern; lifecycle hooks over signals; admin inlines auto-derived from models |
| **IV. Opinionated Defaults** | PASS | Pydantic deferred (not a new dependency in Phase 1); all task infrastructure uses existing Celery setup; privacy defaults sensible (unclaimed=all public, claimed=email private) |
| **V. Test-First Quality** | PASS | Contracts define testable signatures; TransformTestMixin ensures round-trip fidelity; migration tests verify data integrity |
| **VI. Documentation Critical** | PASS | quickstart.md provides 10 usage scenarios; contracts/ defines full API surface; data-model.md documents all entities, fields, and indexes |
| **VII. Living Demo** | PASS | Plan requires demo app contributor demonstration updated with new Affiliation model, privacy controls, and transform usage |

## Project Structure

### Documentation (this feature)

```text
specs/009-fairdm-contributors/
├── plan.md              # This file
├── spec.md              # Feature specification (input)
├── research.md          # Phase 0: research decisions (D1-D7)
├── data-model.md        # Phase 1: entity relationship specification
├── quickstart.md        # Phase 1: developer quickstart guide
├── contracts/
│   └── api-contracts.md # Phase 1: public API contracts
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
fairdm/contrib/contributors/
├── __init__.py
├── adapters.py           # allauth adapter (minimal: bug fix only; full claiming flows → Feature 010)
├── admin.py              # PersonAdmin, OrganizationAdmin, AffiliationInline
├── apps.py               # ContributorsConfig
├── choices.py            # Enum/choice constants
├── filters.py            # PersonFilter, OrganizationFilter, ContributionFilter
├── managers.py           # UserManager, PersonalContributorsManager, ContributionManager
├── models.py             # Contributor, Person, Organization, Affiliation, Contribution, ContributorIdentifier
├── plugins.py            # Detail view plugins (17 plugins)
├── resources.py          # django-import-export PersonResource
├── tasks.py              # NEW: Celery tasks (sync, refresh, duplicate detection)
├── urls.py               # URL patterns
├── validators.py         # Field validators (ORCID, ROR format)
├── forms/
│   ├── __init__.py
│   ├── account.py        # Account-related forms
│   ├── contribution.py   # Contribution forms
│   ├── forms.py          # General forms
│   ├── organization.py   # Organization forms
│   ├── person.py         # Person forms
│   └── widgets.py        # Custom form widgets
├── migrations/
│   ├── 0001-0010          # Existing migrations
│   ├── 0011_add_partial_dates.py         # NEW: Add start_date, end_date (PartialDateField)
│   ├── 0012_rename_to_affiliation.py     # NEW: RenameModel OrganizationMember → Affiliation
│   └── 0013_update_related_names.py      # NEW: Update related_name to "affiliations"
├── static/               # Static assets (contributor avatars, icons)
├── templates/            # Django templates for contributor views
├── templatetags/
│   ├── __init__.py
│   └── contributor_tags.py  # by_role, has_role template filters
├── utils/
│   ├── __init__.py
│   ├── helpers.py        # get_contributor_avatar, current_user_has_role, update_or_create_contribution
│   └── transforms.py     # TransformRegistry, BaseTransform, DataCite/SchemaOrg/CSL/ORCID/ROR transforms
└── views/
    ├── __init__.py
    ├── generic.py        # Generic contributor views
    ├── organization.py   # Organization-specific views
    └── person.py         # Person-specific views

tests/test_contrib/test_contributors/
├── __init__.py
├── conftest.py           # Fixtures: persons, orgs, affiliations, contributions, identifiers
├── test_models.py        # Model creation, validation, is_claimed, privacy, weight
├── test_managers.py      # Manager methods: claimed(), unclaimed(), by_role(), for_entity()
├── test_admin.py         # Admin views load, inline rendering, filter behavior
├── test_transforms.py    # Round-trip fidelity, registry, import/export per format
├── test_tasks.py         # Celery task behavior (mocked external APIs)
├── test_migrations.py    # OrganizationMember -> Affiliation data integrity
├── test_permissions.py   # manage_organization grant/revoke/transfer, ownership lifecycle
├── test_privacy.py       # get_visible_fields per viewer type, GDPR pseudonymization
└── test_templatetags.py  # by_role, has_role filters

fairdm_demo/
├── models.py             # UPDATE: Use Affiliation instead of OrganizationMember
├── factories.py          # UPDATE: Add AffiliationFactory, update PersonFactory
└── tests/
    └── test_contributors.py  # NEW: Demo app contributor integration tests
```

**Structure Decision**: This feature extends an existing Django app (`fairdm/contrib/contributors/`) within the monolithic FairDM framework. The primary new file is `tasks.py` for Celery tasks. Five new migration files handle the OrganizationMember to Affiliation transition. Test files follow the constitution-mandated mirror structure under `tests/test_contrib/test_contributors/`.

## Complexity Tracking

> No constitution violations identified. All design decisions align with core principles.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *None* | — | — |
