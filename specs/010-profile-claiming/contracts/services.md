# Service Contracts: Profile Claiming & Account Linking

**Feature:** 010-profile-claiming
**Date:** 2026-03-30

---

## Overview

This feature exposes two types of interfaces:

1. **Internal service API** — Python functions called by adapters, views, and admin code
2. **Web endpoints** — Django views for token-based claiming (user-facing)

No external REST API endpoints are defined in this feature. If the API app is enabled, registered models (ClaimToken, etc.) may be auto-generated via the registry, but claiming operations themselves are NOT exposed via REST for security reasons.

---

## 1. Claiming Service Contract

### `claim_via_orcid(person: Person, sociallogin: SocialLogin) -> Person`

**Purpose:** Activate an unclaimed Person via ORCID social login match.

**Preconditions:**

- `person.is_claimed` is `False`
- `person` has a ContributorIdentifier with type="ORCID" matching `sociallogin.account.uid`

**Postconditions:**

- `person.is_claimed = True`
- `person.is_active = True`
- `sociallogin.user` points to `person`
- Social account connected to `person`
- ClaimingAuditLog record created with method="orcid", success=True

**Errors:**

- `ValueError` if person is already claimed

---

### `claim_via_email(person: Person) -> Person`

**Purpose:** Activate an unclaimed Person after email verification confirms ownership.

**Preconditions:**

- `person.is_claimed` is `False`
- `person.email` is not None
- `ACCOUNT_EMAIL_VERIFICATION == "mandatory"`
- Email has been verified via allauth

**Postconditions:**

- `person.is_claimed = True`
- `person.is_active = True`
- ClaimingAuditLog record created with method="email", success=True

**Errors:**

- `ValueError` if email verification is not mandatory

---

### `claim_via_token(token_string: str, user: Person) -> Person`

**Purpose:** Link an unclaimed Person to an authenticated user via a one-time claim token.

**Preconditions:**

- `token_string` passes `validate_claim_token()` — HMAC valid, not expired, person still unclaimed
- `user.is_authenticated` is True

**Postconditions:**

- If `user` has no existing Person profile (fresh registration): unclaimed person activated as `user`
- If `user` already has a Person profile: merge unclaimed person into user's profile
- ClaimingAuditLog record created with method="token", success=True

**Errors:**

- `ValueError` if token is invalid, expired, or person already claimed

---

### `merge_persons(person_keep: Person, person_discard: Person) -> Person`

**Purpose:** Merge all data from person_discard into person_keep, then delete person_discard.

**Preconditions:**

- `person_keep.pk != person_discard.pk`
- Both are Person instances (same polymorphic subtype)
- Caller has admin/staff permission

**Postconditions:**

- All Contribution records reassigned (with unique_together dedup)
- All ContributorIdentifier records reassigned
- All Affiliation records reassigned (with unique_together dedup)
- All allauth EmailAddress and SocialAccount records reassigned
- All guardian UserObjectPermission records transferred
- Profile fields merged (blanks filled from discard)
- `person_discard` deleted
- Active sessions for `person_discard` invalidated
- ClaimingAuditLog record created with method="admin_merge", success=True
- Entire operation wrapped in `transaction.atomic()`

**Errors:**

- `ValueError` if person_keep == person_discard
- Rolls back fully on any exception (atomic transaction)

---

## 2. Token Utilities Contract

### `generate_claim_token(person: Person) -> str`

**Preconditions:**

- `person.is_claimed` is `False`

**Postconditions:**

- Returns an opaque HMAC-signed string (via `TimestampSigner`) encoding the Person PK
- No database record created
- Previously generated tokens for the same person remain valid until they expire or the person is claimed (implicit revocation)

---

### `validate_claim_token(token_string: str) -> Person | None`

**Preconditions:** None (accepts any string)

**Postconditions:**

- Returns the unclaimed Person if: HMAC verifies, token is within `CLAIM_TOKEN_MAX_AGE`, and person is not yet claimed
- Returns None if invalid, expired, or person already claimed

---

## 3. Web Endpoint Contract

### `GET /claim/<token>/`

**Purpose:** Landing page for claim token links.

**Behavior:**

- If token invalid/expired: Redirect to home with error message
- If user authenticated: Execute claim, redirect to profile with success message
- If user not authenticated: Store token in session, redirect to signup/login

**Security:**

- CSRF protection on form submissions
- Rate limiting: max 10 attempts per IP per hour
- No PII in URL (token is opaque signed string)
- Token validated server-side on every request (no client-side state)

### `POST /claim/<token>/confirm/`

**Purpose:** Confirmation action for authenticated users claiming a profile.

**Behavior:**

- Validates token and CSRF
- Executes `claim_via_token(token, request.user)`
- Redirects to claimed profile page

**Security:**

- Requires authentication
- CSRF token required
- Token validated again on POST (prevents TOCTOU race)

---

## 4. Admin Interface Contract

### Generate Claim Link (PersonAdmin)

**URL:** `/admin/contributors/person/<pk>/generate-claim-link/`

**Behavior:**

- Admin clicks "Generate Claim Link" on unclaimed Person's change page
- System generates a signed token string and displays the full shareable URL
- No database record created; audit log entry written when the link is consumed

**Permissions:** `is_staff` and `change_person` permission required

### Merge Persons (PersonAdmin)

**URL:** `/admin/contributors/person/<pk>/merge/`

**Behavior:**

- Admin selects two Person records to merge
- System shows preview of what will be transferred
- Admin confirms merge
- System executes `merge_persons()` and displays result

**Permissions:** `is_staff` and custom `merge_person` permission required

### Fuzzy Match Suggestions (PersonAdmin)

**Display:** Inline panel on unclaimed Person's change page

**Behavior:**

- Computed on-demand when admin opens the change page (no stored records)
- Shows candidate matches with similarity scores
- Admin can initiate token generation or merge directly from a suggestion

**Permissions:** `is_staff` and `view_person` permission required
