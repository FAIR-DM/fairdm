# Feature 010: Profile Claiming & Account Linking — Research

**Feature:** 010-profile-claiming  
**Date:** 2026-02-18  
**Status:** Planning

---

## Overview

This research document captures findings specific to implementing the profile claiming and account linking features described in [spec.md](./spec.md). For foundational research on polymorphic FK structure, unclaimed state semantics, and merge feasibility, see [../009-fairdm-contributors/research.md](../009-fairdm-contributors/research.md) (Supplementary Research section, Q1-Q4).

---

## Decision Records

### D1: Primary Claiming Mechanism = ORCID Pre-Signup Intercept

**Decision:** ORCID claiming via `pre_social_login` hook is the primary claiming flow.

**Rationale:**
- Highest security (ORCID is a trusted identity provider)
- Lowest complexity (no merge required — activate unclaimed Person before account creation)
- Already architecturally supported (existing adapter at fairdm/contrib/contributors/adapters.py)
- Fewest edge cases (no duplicate FK conflicts, no session invalidation)

**Implementation note:** The current adapter has a bug in the `is_active=False` branch (raises `ImmediateHttpResponse` to redirect to signup instead of activating the person in place). See [../009-fairdm-contributors/research.md Q4](../009-fairdm-contributors/research.md#q4-allauth--existing-inactive-user) for the fix.

**Alternatives considered:**
- Email-based claiming: More complex, requires mandatory email verification, higher security risk
- Token-based claiming: Good for admin-initiated claiming but doesn't support self-service
- Post-signup merge: Highest complexity, most edge cases

**Status:** Approved for Feature 010 implementation

---

### D2: Email-Based Claiming Requires Mandatory Email Verification

**Decision:** Email-based claiming (via `save_user` adapter hook) will ONLY be enabled when `ACCOUNT_EMAIL_VERIFICATION = "mandatory"`.

**Rationale:**
- Without email verification, anyone who knows (or guesses) a pre-enrolled email can claim that researcher's entire profile
- This is an unacceptable account takeover risk
- Mandatory verification ensures the claimant actually controls the email address

**Implementation:**
```python
def save_user(self, request, user, form, commit=True):
    if getattr(settings, "ACCOUNT_EMAIL_VERIFICATION", "none") != "mandatory":
        # Email claiming is unsafe — skip it
        return super().save_user(request, user, form, commit=commit)
    # ... email claiming logic ...
```

**Activation trigger:** Use `allauth.account.signals.email_confirmed` signal to activate the unclaimed Person after verification, not at signup time.

**Status:** Approved for Feature 010 implementation

---

### D3: Token-Based Claiming for Admin-Initiated Flows

**Decision:** Implement one-time claim links using Django's `TimestampSigner` with 7-day expiration.

**Rationale:**
- Most secure non-ORCID claiming mechanism
- Admin can send claim link to researcher's known email
- Time-limited, single-use, HMAC-signed (resistant to forgery)
- Works for researchers without ORCID

**Security properties:**
- Token includes Person PK signed with HMAC-SHA256
- Max age: 7 days (configurable via `CLAIM_TOKEN_MAX_AGE` setting)
- Token invalidated on first successful claim (Person is deleted or activated)
- Leakage risk equivalent to "reset password" link (acceptable standard)

**Implementation pattern:** See [../009-fairdm-contributors/research.md Q2.2d](../009-fairdm-contributors/research.md#q2-non-orcid-claiming-approaches) for `generate_claim_token()` and `validate_claim_token()` utilities.

**Status:** Approved for Feature 010 implementation

---

### D4: Name Matching for Suggestions Only, Never Auto-Claim

**Decision:** Fuzzy name matching will generate suggestions for admin review but will NEVER auto-claim profiles.

**Rationale:**
- Names are not unique identifiers (same name, different person is common in academia)
- Name formatting variance is high ("J. Smith", "John Smith", "Smith, John")
- Even 95%+ similarity scores produce false positives at portal scale
- Auto-claim based on name match = unacceptable risk of merging wrong people

**Implementation:**
- Use `rapidfuzz.fuzz.token_sort_ratio` with threshold 0.85
- Return as `DuplicateSuggestion` records for admin UI display
- Admin must manually confirm before claim/merge

**Algorithm choice:** Token sort ratio (vs Levenshtein, Jaro-Winkler, Soundex) because it handles name part reordering ("Smith, John" ↔ "John Smith") without false positives.

**Status:** Approved for Feature 010 implementation

---

### D5: Post-Signup Merge as Last Resort Only

**Decision:** Post-signup merge (Person B already registered, then discovered duplicate Person A) is supported but discouraged.

**Rationale:**
- High complexity: Session invalidation, FK reassignment, unique constraint conflict resolution
- Risk of data loss if not implemented correctly
- Pre-signup interception (ORCID, email, token) is always preferable

**When unavoidable:**
- Admin discovers duplicate after researcher has registered and accumulated contributions
- Both Person A (unclaimed) and Person B (active) have valuable data to preserve

**Implementation requirements:**
- Must run in `transaction.atomic()` to prevent partial merges
- Must handle `unique_together` conflicts (Contribution, OrganizationMember)
- Must invalidate all sessions for `person_discard`
- Must reassign allauth EmailAddress, SocialAccount, guardian UserObjectPermission
- Must delete true duplicate Contribution records before FK reassignment

**Detailed algorithm:** See [../009-fairdm-contributors/research.md Q3](../009-fairdm-contributors/research.md#q3-edge-cases-for-claiming) for full `merge_persons()` implementation.

**Status:** Approved for Feature 010 implementation (edge case handler)

---

### D6: Audit Trail for All Claiming Events

**Decision:** All claiming events (successful claims, merge operations, failed attempts) will be logged to `ClaimingAuditLog` and optionally to django-activity-stream.

**Rationale:**
- Security: Detect unauthorized claim attempts
- Compliance: Provide audit trail for data governance
- Support: Help admins debug claiming issues

**Logged events:**
- ORCID claim (pre-signup interception)
- Email claim (post-verification activation)
- Token claim (one-time link usage)
- Manual admin claim/merge
- Failed claim attempts (expired token, wrong email, etc.)

**Fields to log:**
- `claimed_person` (the unclaimed Person being claimed)
- `claiming_user` (the authenticated user claiming, if applicable)
- `claim_method` (ORCID, EMAIL, TOKEN, ADMIN_MANUAL)
- `timestamp`
- `ip_address` (for security auditing)
- `success` (boolean)
- `failure_reason` (if success=False)

**Status:** Approved for Feature 010 implementation

---

## Technical Findings Summary

### Polymorphic Merge Safety

**Finding:** Polymorphic FK reassignment is safe when both instances are the same subtype (Person → Person).

**Key insights from research:**
- `polymorphic_ctype` does NOT need updating when merging same-subtype instances
- FK reassignment via `.update(contributor_id=new_pk)` works correctly
- CASCADE deletion order matters: reassign FKs first, THEN delete the discard person
- Must use `transaction.atomic()` to prevent partial merges

**Source:** [../009-fairdm-contributors/research.md Q1](../009-fairdm-contributors/research.md#q1-django-polymorphic-fk-reassignment--merge-feasibility)

---

### Allauth Adapter Hook Ordering

**Finding:** The `pre_social_login` hook for ORCID claiming has a bug in the current implementation.

**Current behavior:**
- Active unclaimed Person → correctly handled (activates and connects)
- Inactive unclaimed Person → redirects to signup → creates duplicate Person ❌

**Root cause:** The `else` branch at adapters.py:~65 raises `ImmediateHttpResponse` to redirect, allowing allauth to continue normal signup flow.

**Correct behavior:** Activate the unclaimed Person and connect the social account IN `pre_social_login`, then raise `ImmediateHttpResponse` to complete login immediately (bypassing signup form).

**Source:** [../009-fairdm-contributors/research.md Q4.4a](../009-fairdm-contributors/research.md#q4-allauth--existing-inactive-user)

---

### Email Claiming Security Risk

**Finding:** Email-based claiming without mandatory email verification is HIGH RISK.

**Attack scenario:**
1. Admin pre-enrolls researcher as unclaimed Person with email="target@example.com"
2. Attacker registers with email="target@example.com" (if verification not required)
3. Attacker gains access to researcher's entire contribution history and identifiers

**Mitigations required (ALL must be active):**
- `ACCOUNT_EMAIL_VERIFICATION = "mandatory"`
- Rate-limit signup attempts
- Activate Person only AFTER email confirmation signal
- Log all claiming events to audit trail
- Optionally: Notify researcher at original email when profile is claimed

**Source:** [../009-fairdm-contributors/research.md Q2.2a, Q4.4c](../009-fairdm-contributors/research.md#q2-non-orcid-claiming-approaches)

---

### Unique Constraint Conflicts During Merge

**Finding:** `Contribution.unique_together = ("content_type", "object_id", "contributor")` causes `IntegrityError` if both persons have contributions to the same object.

**Resolution strategy:**
1. Before bulk FK update, identify duplicate Contribution records
2. Merge roles from duplicate B into duplicate A (if different roles)
3. Delete duplicate B
4. Then reassign remaining Contribution FKs

**Code pattern:**
```python
for contrib_b in Contribution.objects.filter(contributor_id=discard_pk):
    try:
        contrib_a = Contribution.objects.get(
            contributor_id=keep_pk,
            content_type=contrib_b.content_type,
            object_id=contrib_b.object_id,
        )
        contrib_a.roles.add(*contrib_b.roles.all())  # Merge roles
        contrib_b.delete()
    except Contribution.DoesNotExist:
        contrib_b.contributor_id = keep_pk
        contrib_b.save()
```

**Source:** [../009-fairdm-contributors/research.md Q3.3a](../009-fairdm-contributors/research.md#q3-edge-cases-for-claiming)

---

## Open Questions

*No open questions at this time. All claiming mechanisms have been researched and decision records are complete.*

---

## References

- [Feature 009 Research: Supplementary Research on Claiming & Merging](../009-fairdm-contributors/research.md#supplementary-research-contributor-claiming--merging)
- [django-allauth documentation: Adapter methods](https://docs.allauth.org/en/latest/account/advanced.html#creating-and-populating-user-instances)
- [Django cryptographic signing: TimestampSigner](https://docs.djangoproject.com/en/stable/topics/signing/)
- [django-polymorphic documentation: Queryset methods](https://django-polymorphic.readthedocs.io/en/stable/queryset_methods.html)
