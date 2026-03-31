# Implementation Plan: Profile Claiming & Account Linking

**Branch**: `010-profile-claiming` | **Date**: 2026-03-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/010-profile-claiming/spec.md`

## Summary

Implement comprehensive profile claiming and account linking flows so that unclaimed Person profiles (created as attribution stubs by admin or other contributors) can be securely connected to real user accounts. Five claiming pathways are supported in priority order: ORCID-based (auto, highest security), email-based (post-verification), token-based (admin-generated one-time links), post-signup merge (admin-initiated recovery), and fuzzy name matching (suggestions only, never auto-claim). User privacy and data security are first-class concerns — every pathway requires verified identity before granting access.

## Technical Context

**Language/Version**: Python 3.11+, Django 5.x
**Primary Dependencies**: django-allauth (authentication, social login, email verification), django-guardian (object-level permissions), django-polymorphic (Contributor hierarchy), django-invitations (invitation-only signup gate — not used for claim tokens), django-lifecycle (model hooks), rapidfuzz (fuzzy name matching)
**Storage**: PostgreSQL (primary), SQLite (dev/test)
**Testing**: pytest + pytest-django, factory-boy
**Target Platform**: Linux server (Docker), development on Windows
**Project Type**: Django web framework (server-rendered templates with HTMX/Alpine.js enhancements)
**Constraints**: Zero account takeover tolerance — every claiming pathway MUST verify identity; email claiming MUST require mandatory email verification; tokens MUST be single-use and time-limited
**Scale/Scope**: Portals typically 100–10,000 contributors; fuzzy matching is implemented via `rapidfuzz` (Python-level, suitable for portals up to ~5,000 Persons). For portals exceeding ~5,000 Persons, consider PostgreSQL `pg_trgm` as a future performance optimisation — this is not in scope for the current implementation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Gate

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. FAIR-First** | ✅ PASS | Claiming connects researchers to their attribution records, improving findability and metadata accuracy. Stable identifiers (ORCID) are first-class. |
| **II. Domain-Driven Declarative Modeling** | ✅ PASS | New model (ClaimingAuditLog) extends the contributor backbone. Stateless tokens and on-demand fuzzy matching avoid unnecessary DB state. No ad-hoc runtime structures. |
| **III. Configuration Over Plumbing** | ✅ PASS | All claiming methods enabled by default — no per-method toggles needed. `CLAIM_TOKEN_MAX_AGE` allows token expiry customisation. Adapters use allauth hooks, not custom URL routing. |
| **IV. Opinionated Defaults** | ✅ PASS | All claiming methods enabled by default — no configuration needed. Email claiming self-disables if `ACCOUNT_EMAIL_VERIFICATION` is not "mandatory" (security guard). Stateless tokens need no DB table or cleanup jobs. Sensible 7-day expiry default. |
| **V. Test-First Quality** | ✅ PASS | Each user story has independent test criteria. Security edge cases (token reuse, expired tokens, unverified email) have explicit acceptance scenarios. |
| **VI. Documentation Critical** | ✅ PASS | Admin guide (claiming configuration), developer guide (extending claiming), contributor guide (how to claim a profile) required alongside implementation. |
| **VII. Living Demo** | ⚠️ NOTE | Demo app updates may be limited — claiming is contributor-infrastructure, not domain-model extension. Document admin-side configuration in demo README. |
| **Privacy & Security** | ✅ PASS | All pathways require verified identity. Email claiming disabled without mandatory verification. Tokens are stateless HMAC-signed strings — no DB table, no cleanup needed, cryptographically enforced expiry, implicit revocation on claim. Audit trail for all events. Session invalidation on merge. |

**Gate result: PASS** — no violations. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/010-profile-claiming/
├── plan.md              # This file
├── research.md          # Phase 0 output (already exists from spec phase)
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
fairdm/contrib/contributors/
├── adapters.py              # MODIFY: Fix ORCID pre_social_login bug, add email claiming hooks
├── models.py                # MODIFY: Add ClaimingAuditLog model
├── admin.py                 # MODIFY: Add claim token generation, merge UI, on-demand fuzzy match display
├── views/
│   └── claiming.py          # CREATE: ClaimProfileView for token-based claiming
├── urls.py                  # MODIFY: Add claiming URL patterns
├── forms/
│   └── person.py            # MODIFY: Add MergePersonForm
├── signals.py               # CREATE: email_confirmed handler for email claiming activation
├── services/
│   ├── __init__.py
│   ├── claiming.py          # CREATE: Core claiming service (claim_via_orcid, claim_via_email, claim_via_token)
│   ├── merge.py             # CREATE: merge_persons() with FK reassignment, dedup, session invalidation
│   └── matching.py          # CREATE: On-demand fuzzy name matching (find_duplicate_candidates)
├── utils/
│   ├── tokens.py            # CREATE: generate_claim_token(), validate_claim_token() — stateless TimestampSigner
│   └── audit.py             # CREATE: log_claiming_event() utility
├── templates/
│   └── contributors/
│       ├── claim_profile.html      # CREATE: Token claim landing page
│       └── admin/
│           └── claim_person.html   # CREATE: Admin claim/merge interface

tests/test_contrib/test_contributors/
├── test_claiming_services.py    # CREATE: Unit tests for claiming service functions
├── test_merge.py                # CREATE: Unit tests for merge_persons()
├── test_tokens.py               # CREATE: Unit tests for token generation/validation
├── test_matching.py             # CREATE: Unit tests for fuzzy name matching utility
├── test_adapters.py             # MODIFY: Add tests for ORCID bug fix, email claiming adapter hooks
├── test_views.py                # CREATE: Integration tests for ClaimProfileView
├── test_signals.py              # CREATE: Tests for email_confirmed signal handler
└── test_audit.py                # CREATE: Tests for audit trail logging
```

**Structure Decision**: All claiming code lives within `fairdm/contrib/contributors/` since claiming is contributor-domain logic. New `services/` subdirectory provides a clean separation between models (data) and operations (claiming, merging, matching). Token utilities go in `utils/` alongside existing transform utilities. Tests mirror source structure per constitution.

## Complexity Tracking

> No constitution violations identified. All design decisions align with established principles.
