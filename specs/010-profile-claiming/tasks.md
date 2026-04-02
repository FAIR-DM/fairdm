# Tasks: Profile Claiming & Account Linking

**Input**: Design documents from `/specs/010-profile-claiming/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/services.md ✅

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1–US5)
- Exact file paths are included in every task description

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the `services/` package skeleton that all user story phases depend on.

- [ ] T001 Create `fairdm/contrib/contributors/services/` package with empty `__init__.py`; also create `fairdm/contrib/contributors/exceptions.py` with `ClaimingError(Exception)` class (used by all claiming service functions — see data-model.md § Custom Exceptions)

### System Validation — Phase 1

- [ ] T002 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` — MUST pass before proceeding to Phase 2

**Checkpoint — Setup Complete**: System checks pass and `services/` package is importable.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add `ClaimingAuditLog` model, migration, and shared utilities (`audit.py`, `tokens.py`) that every claiming pathway depends on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T003 Add `ClaimMethod` TextChoices and `ClaimingAuditLog` model to `fairdm/contrib/contributors/models.py` (immutable save() override, all fields per data-model.md)
- [ ] T004 Generate and apply migration for `ClaimingAuditLog` in `fairdm/contrib/contributors/migrations/`
- [ ] T005 [P] Create `fairdm/contrib/contributors/utils/audit.py` with `log_claiming_event(method, source, target, initiated_by, ip_address, success, failure_reason, details)` utility
- [ ] T006 [P] Create `fairdm/contrib/contributors/utils/tokens.py` with `generate_claim_token(person) -> str` and `validate_claim_token(token_string) -> Person | None` using `TimestampSigner`

### System Validation — Phase 2

- [ ] T007 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` — MUST pass before proceeding
- [ ] T008 ⚠️ CRITICAL: Run migration and model tests: `poetry run pytest tests/test_contrib/test_contributors/test_models.py -v` — ALL tests MUST pass before proceeding to any user story

**Checkpoint — Foundation Ready**: ClaimingAuditLog is migrated, both utilities are importable, and all existing model tests still pass. User story phases can now begin.

---

## Phase 3: User Story 1 — ORCID-Based Claiming (Priority: P1) 🎯 MVP

**Goal**: Fix the existing ORCID adapter bug so that signing in via ORCID automatically activates and connects an existing unclaimed Person profile instead of creating a duplicate.

**Independent Test**: Create an unclaimed Person with a ContributorIdentifier(type="ORCID"), simulate ORCID social login with that ORCID UID, assert: single Person row exists, `is_active=True`, `is_claimed=True`, social account connected, all original Contributions preserved.

- [ ] T011 [P] [US1] Write unit tests for `claim_via_orcid()` in `tests/test_contrib/test_contributors/test_claiming_services.py`: happy path; already-claimed Person raises guard; banned target Person (`is_active=False`) raises `ClaimingError` (FR-017); audit log written on success; failed claim logged with `success=False` and `failure_reason` populated (FR-015) *(TDD stubs — will initially fail with ImportError until T009 is complete)*
- [ ] T013 [P] [US1] Write unit tests for token utilities in `tests/test_contrib/test_contributors/test_tokens.py` (generate/validate round-trip, expiry rejection, tampered token rejected, already-claimed person rejected) *(TDD stubs — depends on T006 from Phase 2)*
- [ ] T009 [US1] Create `fairdm/contrib/contributors/services/claiming.py` with `claim_via_orcid(person: Person, sociallogin: SocialLogin) -> Person` — sets `is_claimed=True`, `is_active=True`, connects social account, calls `log_claiming_event()`
- [ ] T010 [US1] Fix `pre_social_login` in `fairdm/contrib/contributors/adapters.py`: replace the `is_active=False` branch's `ImmediateHttpResponse(redirect_to_signup(...))` with a call to `claim_via_orcid()` and an `ImmediateHttpResponse` completing the login
- [ ] T012 [P] [US1] Write adapter integration tests for the ORCID claiming flow in `tests/test_contrib/test_contributors/test_adapters.py` (existing unclaimed Person gets activated; new ORCID creates fresh Person)

### System Validation — Phase 3

- [ ] T014 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` — MUST pass before proceeding
- [ ] T015 ⚠️ CRITICAL: Run User Story 1 tests: `poetry run pytest tests/test_contrib/test_contributors/test_claiming_services.py tests/test_contrib/test_contributors/test_adapters.py tests/test_contrib/test_contributors/test_tokens.py -v` — ALL tests MUST pass

**Checkpoint — US1 Complete**: ORCID claiming fully functional and tested. No duplicate Person created on ORCID signup.

---

## Phase 4: User Story 2 — Email-Based Claiming (Priority: P2)

**Goal**: When a user registers with an email that matches an unclaimed Person's email and confirms the verification link, the unclaimed profile is automatically activated and connected to the new account.

**Independent Test**: Set `email="jane@example.org"` on an unclaimed Person, simulate registration + email confirmation with that address under `ACCOUNT_EMAIL_VERIFICATION="mandatory"`, assert the single Person row becomes `is_claimed=True`. Also assert the flow is entirely skipped (no claim attempted) when verification is not mandatory.

- [ ] T020 [P] [US2] Write unit tests for `claim_via_email()` in `tests/test_contrib/test_contributors/test_claiming_services.py`: happy path; mandatory-verification guard (silent no-op when `ACCOUNT_EMAIL_VERIFICATION != "mandatory"`); already-claimed Person raises guard; banned target Person (`is_active=False`) raises `ClaimingError` (FR-017); audit log written on success; failed claim logged with `success=False` and `failure_reason` populated (FR-015) *(TDD stubs — will initially fail with ImportError until T016 is complete)*
- [ ] T021 [P] [US2] Write signal handler tests in `tests/test_contrib/test_contributors/test_signals.py` (email confirmed triggers claim; no-op when verification not mandatory; no-op when no matching unclaimed Person) *(TDD stubs — will initially fail until T018/T019 are complete)*
- [ ] T016 [US2] Add `claim_via_email(person: Person) -> Person` to `fairdm/contrib/contributors/services/claiming.py` — sets `is_claimed=True`, `is_active=True`, calls `log_claiming_event()`
- [ ] T017 [US2] Update `AccountAdapter.save_user()` in `fairdm/contrib/contributors/adapters.py`: add guard that skips email-based claiming entirely when `ACCOUNT_EMAIL_VERIFICATION != "mandatory"`
- [ ] T018 [US2] Create `fairdm/contrib/contributors/signals.py` with `handle_email_confirmed` receiver on `allauth.account.signals.email_confirmed` — looks up unclaimed Person by confirmed email and calls `claim_via_email()`
- [ ] T019 [US2] Register the `email_confirmed` signal in `ready()` method of `fairdm/contrib/contributors/apps.py`

### System Validation — Phase 4

- [ ] T022 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` — MUST pass before proceeding
- [ ] T023 ⚠️ CRITICAL: Run User Story 2 tests: `poetry run pytest tests/test_contrib/test_contributors/test_claiming_services.py tests/test_contrib/test_contributors/test_signals.py -v` — ALL tests MUST pass

**Checkpoint — US2 Complete**: Email claiming fully functional. Confirming a matching email activates the unclaimed profile. Security guard prevents email claiming without mandatory verification.

---

## Phase 5: User Story 3 — Token-Based Claiming (Admin-Initiated) (Priority: P3)

**Goal**: Admin can generate a one-time signed claim link for an unclaimed Person; when clicked the link connects the Person to an authenticated (or freshly registered) user account.

**Independent Test**: Admin generates a claim token for an unclaimed Person, unauthenticated user clicks the link, registers, asserts the unclaimed profile is activated. Then attempt to reuse the same token and assert rejection.

- [ ] T030 [P] [US3] Write `ClaimProfileView` integration tests in `tests/test_contrib/test_contributors/test_views.py`: (a) authenticated same-user — GET shows claim confirmation, POST executes claim and profile is activated; (b) unauthenticated — GET redirects to login with token stored in session, claim completes after auth; (c) authenticated as different Person B (US3 Scenario 6) — GET renders merge confirmation page listing Person A's contributions/identifiers to be transferred, POST executes merge and B now has all of A's data; (d) banned target Person — GET renders error page, POST also rejected; (e) expired token — rejected with error; (f) reused token (already claimed) — rejected; (g) CSRF enforced on POST *(TDD stubs — will initially fail until T024/T025 are complete; merge path (c) additionally requires T034 from Phase 6)*
- [ ] T031 [P] [US3] Write unit tests for `claim_via_token()` in `tests/test_contrib/test_contributors/test_claiming_services.py`: valid token + authenticated user; token-already-claimed raises `ClaimingError`; expired token raises `ClaimingError`; tampered token raises `ClaimingError`; banned target Person (`is_active=False`) raises `ClaimingError` (FR-017); failed claim logged with `success=False` and `failure_reason` populated (FR-015) *(TDD stubs — will initially fail with ImportError until T024 is complete)*
- [ ] T024 [US3] Add `claim_via_token(token_string: str, user: Person) -> Person` to `fairdm/contrib/contributors/services/claiming.py` — calls `validate_claim_token()`, raises `ClaimingError` if target Person is banned (`is_active=False`, FR-017), activates the unclaimed Person for the calling user, calls `log_claiming_event()`; handles the **simple-claim path only** (user has no conflicting active Person account). The merge path (authenticated Person B claiming token for unclaimed Person A) is handled by `ClaimProfileView` routing directly to `merge_persons()` — the view is the routing layer, not this service function. *(Note: merge paths in `ClaimProfileView` POST require Phase 6 `merge_persons()` to be complete before that branch is wired up)*
- [ ] T025 [US3] Create `fairdm/contrib/contributors/views/claiming.py` with `ClaimProfileView`: `GET /claim/<token>/` ALWAYS renders a confirmation page showing the unclaimed profile details (and merge summary if user is already Person B); `POST /claim/<token>/confirm/` executes the claim or merge (requires authentication + CSRF). Four user states on GET: (a) unauthenticated → store token in session, redirect to login/register, return here after auth; (b) authenticated, no conflicting Person → show standard claim confirmation; (c) authenticated as different Person B → show merge confirmation page listing what will be transferred from Person A; (d) token targets a banned Person (`is_active=False`) → render error page immediately regardless of auth state — no confirmation page is shown. On POST: routes to `claim_via_token()` for state (b) simple-claim path, or calls `merge_persons()` directly for state (c) merge path — the view is the routing layer. No claim or merge is ever executed on GET.
- [ ] T026 [US3] Add claim URL patterns (`/claim/<token>/` and `/claim/<token>/confirm/`) to `fairdm/contrib/contributors/urls.py`
- [ ] T027 [US3] Create `fairdm/contrib/contributors/templates/contributors/claim_profile.html` — landing page showing unclaimed profile details and confirm/login button
- [ ] T028 [US3] Add "Generate Claim Link" admin action to `fairdm/contrib/contributors/admin.py` on `PersonAdmin` — calls `generate_claim_token()`, passes the shareable URL to a template context, and queries `ClaimingAuditLog` for this Person to display claim history (satisfies US3 Scenario 7: admin can see who claimed it and when)
- [ ] T029 [US3] Create `fairdm/contrib/contributors/templates/contributors/admin/claim_person.html` — renders the generated claim URL in a copyable field with expiry notice and a claim history section drawn from `ClaimingAuditLog`; includes a visible admin note: "Generating a new claim link does NOT invalidate previously generated links — all unexpired links remain valid until one is redeemed" (satisfies Q4 clarification requirement)

### System Validation — Phase 5

- [ ] T032 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` — MUST pass before proceeding
- [ ] T033 ⚠️ CRITICAL: Run User Story 3 tests: `poetry run pytest tests/test_contrib/test_contributors/test_views.py tests/test_contrib/test_contributors/test_claiming_services.py -v` — ALL tests MUST pass

**Checkpoint — US3 Complete**: Token claiming end-to-end functional. Admin can generate and share a claim link; recipient claims their profile. Token is single-use.

---

## Phase 6: User Story 4 — Post-Signup Merge (Priority: P4)

**Goal**: Admin can merge two Person records (unclaimed A + registered B), transferring all contributions, affiliations, identifiers, allauth records, and permissions from A to B inside a single atomic transaction; A is then deleted.

**Independent Test**: Create two Person records with overlapping and unique Contributions; call `merge_persons(keep=B, discard=A)`; assert B has all combined unique contributions, A is deleted, all sessions for A invalidated, all permissions transferred.

- [ ] T038 [US4] Write merge service unit tests in `tests/test_contrib/test_contributors/test_merge.py` (full merge happy path, contribution dedup on unique_together conflict, allauth records reassigned, sessions invalidated, permissions transferred, atomic rollback on error, error if keep==discard) *(TDD stubs — will initially fail with ImportError until T034 is complete)*
- [ ] T034 [US4] Create `fairdm/contrib/contributors/services/merge.py` with `merge_persons(person_keep, person_discard)` and all private helpers: `_reassign_contributions`, `_reassign_identifiers`, `_reassign_affiliations`, `_reassign_allauth_records`, `_transfer_permissions`, `_invalidate_sessions`, `_merge_profile_fields` — entire operation in `transaction.atomic()`
- [ ] T035 [US4] Add `MergePersonForm` to `fairdm/contrib/contributors/forms/person.py` — select field for target Person to merge into
- [ ] T036 [US4] Add merge admin action and merge confirmation view to `fairdm/contrib/contributors/admin.py`; action is available to any staff user with `contributors.change_person` permission (no additional permission required)
- [ ] T037 [US4] Add merge preview/confirm section to `fairdm/contrib/contributors/templates/contributors/admin/claim_person.html` (shows what will be transferred; confirm button POSTs to merge action)

### System Validation — Phase 6

- [ ] T039 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` — MUST pass before proceeding
- [ ] T040 ⚠️ CRITICAL: Run User Story 4 tests: `poetry run pytest tests/test_contrib/test_contributors/test_merge.py -v` — ALL tests MUST pass

**Checkpoint — US4 Complete**: Admin can merge any two Person records without data loss. Partial merges are impossible (transaction rollback).

---

## Phase 7: User Story 5 — Fuzzy Name Matching (Priority: P5)

**Goal**: Admin viewing an unclaimed Person profile sees on-demand suggestions of other Persons with similar names (token_sort_ratio ≥ 0.85), to help identify potential duplicates for manual review.

**Independent Test**: Create unclaimed Person "John A. Smith" and claimed Person "John Smith"; open the admin change page for the unclaimed Person; assert the suggestions panel lists "John Smith" with a similarity score ≥ 0.85. Create a clearly different Person "Alice Brown"; assert she does NOT appear in suggestions.

- [ ] T043 [US5] Write fuzzy matching unit tests in `tests/test_contrib/test_contributors/test_matching.py` (similar names surface above threshold, dissimilar names excluded, name-reordering handled, self excluded from results) *(TDD stubs — will initially fail with ImportError until T041 is complete)*
- [ ] T041 [US5] Create `fairdm/contrib/contributors/services/matching.py` with `find_duplicate_candidates(person: Person, threshold: float = 0.85) -> list[dict]` using `rapidfuzz.fuzz.token_sort_ratio` — returns list of `{person, score}` dicts sorted by score desc
- [ ] T042 [US5] Add fuzzy match inline panel to unclaimed PersonAdmin change page in `fairdm/contrib/contributors/admin.py` — calls `find_duplicate_candidates()` and passes results to the change form context; includes "Dismiss" (session-scoped) and "Claim via Token" shortcut per suggestion

### System Validation — Phase 7

- [ ] T044 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` — MUST pass before proceeding
- [ ] T045 ⚠️ CRITICAL: Run User Story 5 tests: `poetry run pytest tests/test_contrib/test_contributors/test_matching.py -v` — ALL tests MUST pass

**Checkpoint — US5 Complete**: Fuzzy name matching panel visible in admin for unclaimed Persons. Suggestions are on-demand and never auto-claim.

---

## Final Phase: Polish & Cross-Cutting Concerns

- [ ] T052 [P] Register `ClaimingAuditLog` with Django admin as a read-only `ModelAdmin` in `fairdm/contrib/contributors/admin.py` (list display: `timestamp`, `method`, `source_person`, `target_person`, `initiated_by`, `success`; no add/change/delete permissions — immutable by design)
- [ ] T046 Write `ClaimingAuditLog` model and admin registration tests in `tests/test_contrib/test_contributors/test_audit.py` (immutability enforced, manager filter methods, admin view loads); also verify demo app admin views load without errors after `ClaimingAuditLog` migration is applied (`poetry run python manage.py check` passes and demo admin changelist returns HTTP 200) — Constitution §VII compliance *(depends on T052)*
- [ ] T047 [P] Add "Claiming a Profile" guide for contributors at `docs/user-guide/claiming-a-profile.md` (ORCID, email, and token pathways explained from user perspective)
- [ ] T048 [P] Add "Managing Unclaimed Profiles" guide to `docs/portal-administration/managing-unclaimed-profiles.md` (generating claim links, running merges, interpreting audit log)
- [ ] T051 [P] Add developer-guide documentation for claiming service APIs and new settings (`CLAIM_TOKEN_MAX_AGE`, `CLAIM_TOKEN_SALT`) in `docs/portal-development/` with at least one usage example per public API and per setting (Constitution §VI compliance)

### System Validation — Final

- [ ] T049 ⚠️ CRITICAL: Run Django system checks: `poetry run python manage.py check` — MUST pass
- [ ] T050 ⚠️ CRITICAL: Run full contributor test suite: `poetry run pytest tests/test_contrib/test_contributors/ -v` — ALL tests MUST pass

**Checkpoint — Feature Complete**: All claiming pathways implemented, all tests pass, documentation updated.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — **BLOCKS all user story phases**
- **US1 (Phase 3)**: Depends on Phase 2 (T007 + T008 must pass)
- **US2 (Phase 4)**: Depends on Phase 2 + US1 (`claiming.py` created by T009)
- **US3 (Phase 5)**: Depends on Phase 2 + US1 (`claiming.py` created by T009)
- **US4 (Phase 6)**: Depends on Phase 2 — independent service module; can overlap with US2/US3
- **US5 (Phase 7)**: Depends on Phase 2 — fully independent; implement last (lowest priority)
- **Polish (Final Phase)**: Depends on all desired user stories complete

### User Story Dependencies

| Story | Depends On | Can Parallelize With |
|-------|-----------|----------------------|
| US1 (P1) | Phase 2 validation (T007+T008) | US4, US5 |
| US2 (P2) | Phase 2 + US1 (`claiming.py` created) | US4, US5 |
| US3 (P3) | Phase 2 + US1 (`claiming.py` created) | US4, US5 |
| US4 (P4) | Phase 2 validation (T007+T008) | US1, US2, US3, US5 |
| US5 (P5) | Phase 2 validation (T007+T008) | US1, US2, US3, US4 |

### Within Each User Story

- Test stubs are written **first** (they will initially fail with ImportError or assertion errors — this is expected TDD behaviour per Constitution §V)
- Service/model implementations follow to make the failing tests pass
- Views and adapters come after the service functions they call
- Admin integration comes last, after core implementation is complete
- **System validation tasks** (`⚠️ CRITICAL`) MUST complete before moving to the next phase

---

## Parallel Opportunities

### Phase 2 (Foundational)

T003 → T004 must be sequential (migration depends on model). T005 and T006 are fully parallel.

### Phase 3 (US1)

T011 + T013 written first as stubs (parallel). T009 → T010 sequential (implementation). T012 written after T009 + T010.

### Phase 4 (US2)

T020 + T021 written first as stubs (parallel). T016 → T017 sequential. T018 + T019 after T016 (parallel).

### Phase 5 (US3)

T030 + T031 written first as stubs (parallel). T024 → T025 + T026 → T027. T028 + T029 parallel to T025–T027.

### Phase 6 (US4)

T038 written first as stub. T034 → T035 + T036 (parallel) → T037.

### Phase 7 (US5)

T043 written first as stub. T041 → T042.

### Final Phase

T046, T047, T048, T051 fully parallel. T049 before T050.

---

## Implementation Strategy

**MVP Scope** (Phase 1 + Phase 2 + Phase 3 only):

- Services package created
- `ClaimingAuditLog` model migrated
- `audit.py` and `tokens.py` utilities in place
- ORCID claiming bug fixed
- All system validation checkpoints passing

This MVP is deployable and fixes the highest-impact bug (ORCID duplicate Person creation) while laying the foundation for all remaining claiming pathways.

**Incremental DWelivery**:

1. MVP: Phases 1–3 (ORCID fix — highest security value)
2. Add email claiming: Phase 4 (handles pre-enrolled contributors)
3. Add token claiming: Phase 5 (admin-initiated, most flexible)
4. Add merge recovery: Phase 6 (edge case recovery)
5. Add fuzzy matching: Phase 7 (quality-of-life tool for admins)

**Total Tasks**: 52
**Tasks per story**: US1=7 (incl. 2 validation), US2=8 (incl. 2 validation), US3=10 (incl. 2 validation), US4=7 (incl. 2 validation), US5=5 (incl. 2 validation)
**Validation checkpoints**: 10 `⚠️ CRITICAL` system validation pairs across all phases
**Parallel opportunities**: 16 tasks marked [P]
