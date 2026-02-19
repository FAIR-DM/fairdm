# Feature Specification: Profile Claiming & Account Linking

**Feature Branch**: `010-profile-claiming`
**Created**: 2026-02-18
**Status**: Draft
**Prerequisites**: Feature 009 (Contributors data model with unclaimed Person support)
**Input**: User description: "Implement comprehensive profile claiming and account linking flows to allow users to claim existing unclaimed Person profiles through ORCID, email verification, admin-generated tokens, and post-signup merge. Not all researchers have ORCIDs; some are added to datasets by name/affiliation only. The system must support multiple claiming pathways with appropriate security for each."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - ORCID-Based Claiming (Priority: P1)

As a researcher with an ORCID, when I sign up via ORCID social login and an unclaimed Person profile with my ORCID already exists, the system automatically connects me to that existing profile instead of creating a duplicate, preserving all existing attribution records.

**Why this priority**: ORCID is the gold standard for researcher identification. This is the most secure claiming method (externally verified identity) and is already partially implemented in Feature 009 with a bug fix needed. Delivers immediate value to the most common case.

**Independent Test**: Create an unclaimed Person with ORCID identifier, register via ORCID social login, verify the existing profile is activated and connected (no duplicate created). Test passes when a single Person row exists with `is_active=True` and all original contributions preserved.

**Acceptance Scenarios**:

1. **Given** an unclaimed Person profile exists with ORCID "0000-0001-2345-6789", **When** a user signs up via ORCID social login with that same ORCID, **Then** the existing profile is activated (`is_active=True`, email populated from ORCID), the social account is connected, and no duplicate Person is created
2. **Given** an unclaimed Person exists with ORCID and existing Contribution records, **When** the real person claims it via ORCID login, **Then** all original Contribution records remain linked to the now-claimed profile
3. **Given** no unclaimed profile matches the ORCID, **When** a user signs up via ORCID, **Then** a new claimed Person profile is created normally
4. **Given** an unclaimed profile with ORCID exists, **When** the claiming happens, **Then** the user is redirected to their profile page with a welcome message indicating the profile was linked
5. **Given** the ORCID claiming flow completes, **When** the user logs out and back in, **Then** they can authenticate normally with full access to their claimed profile

---

### User Story 2 - Email-Based Claiming (Priority: P2)

As a portal administrator, I can pre-assign an email address to an unclaimed Person profile, and when someone registers with that email and verifies it, they are automatically connected to the existing unclaimed profile.

**Why this priority**: Handles the common case where contributors are added by name/affiliation without ORCID, but the admin knows their email. More flexible than ORCID-only but requires email verification for security.

**Independent Test**: Admin sets email on unclaimed Person, user registers with that email, verifies email via link, verify the existing profile is claimed. Test passes when the single Person row becomes claimed and the user can access their profile. Critically, test also verifies that without email verification enabled, this flow is disabled entirely (security check).

**Acceptance Scenarios**:

1. **Given** an unclaimed Person exists with `email="jane@example.org"` and portal has `ACCOUNT_EMAIL_VERIFICATION="mandatory"`, **When** a user signs up with "jane@example.org" and confirms the verification email, **Then** the existing unclaimed profile is activated and connected to the new account
2. **Given** email verification is NOT mandatory (`ACCOUNT_EMAIL_VERIFICATION="optional"` or not set), **When** admin attempts to configure email-based claiming, **Then** the system prevents this configuration and displays a security warning
3. **Given** an unclaimed Person with email exists, **When** someone registers with that email but does NOT verify it, **Then** the profile remains unclaimed and the user cannot access it
4. **Given** multiple unclaimed profiles exist but only one has the matching email, **When** registration completes, **Then** only the email-matching profile is claimed (no name matching is attempted)
5. **Given** email claiming succeeds, **When** the user views their profile, **Then** they see all pre-existing affiliations and contributions that were on the unclaimed profile

---

### User Story 3 - Token-Based Claiming (Admin-Initiated) (Priority: P3)

As a portal administrator, I can generate a one-time claim link for an unclaimed Person profile and send it to the real person, and when they click the link (authenticated or not), their account is connected to the unclaimed profile.

**Why this priority**: Most robust admin-initiated mechanism. Works regardless of whether the person has an ORCID or whether we know their email ahead of time. Admin vouches for the match, reducing false positive risk.

**Independent Test**: Admin generates claim token for unclaimed Person, sends link to researcher, researcher clicks link (either logged in or prompted to register), verify the profile is claimed. Test passes when the profile is successfully linked and the token cannot be reused.

**Acceptance Scenarios**:

1. **Given** an administrator viewing an unclaimed Person profile, **When** they click "Generate Claim Link", **Then** a unique claim token is created with 7-day expiry and a shareable URL is displayed
2. **Given** a claim link token exists, **When** an authenticated user clicks the link, **Then** their current account is connected to the unclaimed profile and they are redirected to the claimed profile page
3. **Given** a claim link token exists, **When** an unauthenticated user clicks the link, **Then** they are prompted to log in or register, and upon completion their account is connected to the unclaimed profile
4. **Given** a claim token has been used once, **When** someone tries to use the same token again, **Then** the system rejects it with "Token already used" error
5. **Given** a claim token is older than 7 days, **When** someone tries to use it, **Then** the system rejects it with "Token expired" error
6. **Given** a claim token exists for Person A but user is already Person B, **When** user clicks the token, **Then** a post-signup merge is proposed (see US4) or an error is shown if merge is not supported
7. **Given** an admin generates a claim link, **When** they view the link details, **Then** they can see who (if anyone) has claimed it and when

---

### User Story 4 - Post-Signup Merge (Recovery Mechanism) (Priority: P4)

As a portal administrator, when I discover that a newly registered Person (B) is actually the same as an existing unclaimed Person (A), I can manually merge them, transferring all contributions, affiliations, and identifiers from A to B and deleting A.

**Why this priority**: Recovery mechanism for when automated claiming fails or a match is discovered after the fact. Lower priority because it's manual intervention, not a primary flow.

**Independent Test**: Create two Person records (one unclaimed, one newly registered), admin initiates merge, verify all relations transfer to the kept Person and the discarded Person is deleted. Test passes when the kept Person has all combined contributions and the other is gone.

**Acceptance Scenarios**:

1. **Given** Person A (unclaimed) has 3 Contribution records and Person B (newly registered) has 1 Contribution, **When** admin merges A into B, **Then** B ends up with all 4 unique Contributions and A is deleted
2. **Given** both Persons have a Contribution to the same Project with the same roles, **When** merge happens, **Then** duplicate Contributions are deduplicated (merged roles, single Contribution remains)
3. **Given** Person A has a ContributorIdentifier and Person B does not, **When** merge happens, **Then** B gains the identifier from A
4. **Given** Person A has allauth EmailAddress and SocialAccount records, **When** merge happens, **Then** those records are reassigned to B before A is deleted
5. **Given** Person A has active user sessions, **When** merge completes, **Then** those sessions are invalidated to prevent stale session access
6. **Given** Person A has object-level permissions (e.g., `manage_organization`), **When** merge happens, **Then** those permissions are transferred to B
7. **Given** the merge operation fails partway through, **When** the error occurs, **Then** the transaction rolls back completely (no partial merge state)

---

### User Story 5 - Fuzzy Name Matching (Suggestions Only) (Priority: P5)

As a portal administrator reviewing an unclaimed Person profile, I see a list of suggested matches from existing claimed or unclaimed profiles based on name similarity, so I can identify potential duplicates for manual review or token-based claiming.

**Why this priority**: Discovery and quality control, but never auto-claims. Lower priority because it's a nice-to-have that improves data quality but isn't blocking for claiming flows.

**Independent Test**: Create unclaimed Person "John A. Smith" and claimed Person "John Smith", verify the admin interface shows them as potential matches with a similarity score. Test passes when suggestions appear and admin can dismiss or initiate token-based claiming from the suggestion.

**Acceptance Scenarios**:

1. **Given** an unclaimed Person named "Jane M. Doe" exists, **When** admin views the profile, **Then** the system displays similar names from other Persons with similarity scores (e.g., "Jane Doe" 95%, "J. M. Doe" 90%)
2. **Given** fuzzy matches are displayed, **When** admin reviews them, **Then** each suggestion shows the person's name, affiliation, ORCID (if any), and claim status
3. **Given** a suggested match is correct, **When** admin clicks "Claim via Token", **Then** a token-based claim link is generated and ready to send to the person
4. **Given** a suggested match is incorrect, **When** admin clicks "Dismiss", **Then** that suggestion is hidden and not shown again for this profile
5. **Given** no close matches exist, **When** admin views an unclaimed profile, **Then** no suggestions are displayed (no false positives)

---

### Edge Cases

- What happens when a user has an ORCID match but also a partial email match to different unclaimed profiles? (Priority: ORCID match)
- How does the system handle email claiming when the user's email provider has a typo in allauth (e.g., "gmial.com")? (Fail verification, no claim)
- What happens if an admin generates a claim token for an unclaimed profile, then the profile gets claimed via ORCID before the token is used? (Token becomes invalid)
- How does the system prevent an authenticated user from using someone else's claim token to gain their attribution? (Token is single-use and creates a link to a specific Person; if user already has a Person account, they can't claim another without merge permission)
- What happens when merging two Persons that both have `is_primary=True` affiliations to different organizations? (Keep both and let user choose new primary)
- How does the system handle a merge where Person A has email "old@example.org" and Person B has "new@example.org"? (Keep B's email as primary, optionally add A's as secondary EmailAddress)
- What happens if someone manually edits an unclaimed profile's data (name, affiliation) after admin generates a claim token but before it's used? (Token remains valid; the person claims the profile in its current state)
- How does claiming interact with privacy settings on unclaimed profiles? (Unclaimed profiles default to all-public; upon claiming, user can adjust privacy settings)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide ORCID-based claiming via allauth `pre_social_login` hook that detects existing unclaimed Person with matching ORCID identifier and activates it instead of creating duplicate
- **FR-002**: System MUST fix the existing bug where ORCID match redirects to signup instead of activating the unclaimed account and connecting the social login
- **FR-003**: System MUST provide email-based claiming that matches registered email to unclaimed Person with same email
- **FR-004**: Email-based claiming MUST be disabled entirely if `ACCOUNT_EMAIL_VERIFICATION` is not set to `"mandatory"` (security requirement)
- **FR-005**: System MUST provide admin interface to generate one-time claim tokens with configurable expiry (default 7 days)
- **FR-006**: Claim tokens MUST be stored securely (Django's `TimestampSigner`) and invalidated after first use
- **FR-007**: Claim tokens MUST work for both authenticated users (direct linking) and unauthenticated users (redirect to register/login then link)
- **FR-008**: System MUST provide `merge_persons(person_keep, person_discard)` service function that transfers all FK relations in `transaction.atomic()`
- **FR-009**: Merge operation MUST handle `Contribution.unique_together` conflicts by merging roles and preserving single Contribution record per (content_type, object_id, contributor)
- **FR-010**: Merge operation MUST reassign allauth `EmailAddress` and `SocialAccount` FKs before deleting discarded Person
- **FR-011**: Merge operation MUST invalidate active sessions for the discarded Person
- **FR-012**: Merge operation MUST transfer django-guardian `UserObjectPermission` records to kept Person
- **FR-013**: System MUST provide fuzzy name matching using token_sort_ratio algorithm with 90%+ threshold for suggestions (never auto-claim)
- **FR-014**: Admin MUST be able to dismiss incorrect fuzzy match suggestions permanently
- **FR-015**: Claiming via any method MUST preserve all existing Contribution, Affiliation, and ContributorIdentifier records
- **FR-016**: System MUST log all claiming events (method, timestamp, source profile, resulting profile) for audit trail
- **FR-017**: System MUST provide per-portal configuration `FAIRDM_CLAIMING_METHODS` to enable/disable specific claiming pathways
- **FR-018**: Each claiming method MUST have comprehensive test coverage including security edge cases

### Key Entities

- **ClaimToken**: One-time use token linking an unclaimed Person to a claim URL. Fields: unclaimed_person (FK), token (signed string), expires_at (DateTimeField), created_by (FK→admin), claimed_by (FK→Person, nullable), claimed_at (DateTimeField, nullable), status (pending/claimed/expired).

- **DuplicateSuggestion**: Admin-reviewable name match suggestion. Fields: unclaimed_person (FK), suggested_match (FK→Person), similarity_score (FloatField), dismissed (BooleanField), dismissed_by (FK→admin), dismissed_at (DateTimeField).

- **ClaimingAuditLog**: Immutable record of all claiming events. Fields: timestamp, method (orcid/email/token/merge), source_person (FK, nullable on delete), target_person (FK), initiated_by (FK→admin, nullable), success (BooleanField), details (JSONField).

## Dependencies & Assumptions

- **Prerequisites**: Feature 009 must be complete — Person model with `is_claimed` property, `claimed()`/`unclaimed()` manager methods, ContributorIdentifier support
- **django-allauth**: `ACCOUNT_EMAIL_VERIFICATION = "mandatory"` MUST be configured for email-based claiming to be enabled
- **Polymorphic merge**: Relies on research finding that django-polymorphic FK reassignment is safe in `transaction.atomic()` and `polymorphic_ctype` does not need updating when merging same-subtype instances
- **Security assumption**: Token-based claiming trusts the admin to correctly identify the person; onus is on admin to verify identity before generating claim link
- **Name matching**: Fuzzy matching is for suggestions only; never auto-claims regardless of score

## Success Criteria *(mandatory)*

- **SC-001**: ORCID claiming successfully connects 99%+ of unclaimed profiles with valid ORCID matches without creating duplicates
- **SC-002**: Email claiming (when enabled) successfully connects 95%+ of unclaimed profiles with verified email matches
- **SC-003**: Zero account takeover incidents via email claiming when `ACCOUNT_EMAIL_VERIFICATION="mandatory"` is enforced
- **SC-004**: Token-based claiming has 0% token reuse or expiry bypass (100% security compliance)
- **SC-005**: Post-signup merge completes without data loss in 100% of test cases (all contributions, affiliations, identifiers transferred)
- **SC-006**: Fuzzy name matching surfaces true duplicate suggestions 90%+ of the time while keeping false positive rate below 5%
- **SC-007**: All claiming events are logged to audit trail with 100% coverage
- **SC-008**: Portal admins can enable/disable specific claiming methods via settings without code changes

- **[Entity 2]**: [What it represents, relationships to other entities]

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: [Measurable metric, e.g., "Users can complete account creation in under 2 minutes"]
- **SC-002**: [Measurable metric, e.g., "System handles 1000 concurrent users without degradation"]
- **SC-003**: [User satisfaction metric, e.g., "90% of users successfully complete primary task on first attempt"]
- **SC-004**: [Business metric, e.g., "Reduce support tickets related to [X] by 50%"]
