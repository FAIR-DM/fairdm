# Research: FairDM Contributors System

**Date**: 2026-02-18
**Feature**: 009-fairdm-contributors

## Current Implementation Inventory

### What Exists Today

The contributors app (`fairdm/contrib/contributors/`) is a substantial but uneven codebase (~3,500 lines across models, forms, views, admin, plugins, transforms, managers, and utilities). The following assessment categorizes each component by maturity.

**Mature / Well-Structured:**
- Polymorphic model hierarchy (`Contributor` → `Person` / `Organization`) — clean, well-tested pattern
- `Contribution` model with GFK linking to any core entity + `OrderedModel` for ordering + `ConceptManyToManyField` for vocabulary-backed roles
- Transform architecture (`BaseTransform` with 5 concrete implementations) — functional bidirectional conversion for DataCite, Schema.org, CSL-JSON, ORCID, ROR
- Template tags (`by_role`, `has_role`) — simple, correct
- allauth adapters — ORCID claiming flow is architecturally sound

**Functional but Needs Rework:**
- `OrganizationMember` model — uses integer `type` choices and boolean flags instead of time-bounded roles. Must migrate to `Affiliation`.
- Admin configuration — `UserAdmin` is reasonable; `OrganizationAdmin` lacks inlines for members; `ContributionInline` has a commented-out model reference
- `PersonResource` for import/export — uses `time.sleep(1.5)` for rate limiting instead of proper backoff

**Incomplete / Placeholder:**
- `ContributionManager` has 3 commented-out methods (`get_contact_persons`, `lead_contributors`, `funding_contributors`)
- `calculate_weight()` is defined but never auto-invoked
- No `tasks.py` — no Celery tasks for async sync or periodic refresh
- No `serializers.py` — REST API serialization not implemented
- No privacy controls mechanism — FR-009 is unaddressed

**Bugs Identified:**
- `Organization.from_ror()` uses `self` instead of `cls` as classmethod first parameter
- `Organization.update_identifier()` hook uses `self.identifiers.add(type=..., value=...)` — `add()` doesn't accept kwargs; should be `create()` or `get_or_create()`
- `Contribution.get_update_url()` references `self.object` which doesn't exist (should be `self.content_object`)
- `Contributor.add_to()` has redundant `get_or_create` then `get` call
- `OrganizationFilter` has `model = Contributor` — possible bug

### Dependency Map (Current)

| Package | Used For | Version Constraint |
|---------|----------|-------------------|
| `django-polymorphic` | Contributor hierarchy | Existing |
| `django-lifecycle` | Model lifecycle hooks (BEFORE_CREATE, AFTER_CREATE, AFTER_DELETE) | Existing |
| `django-countries` | CountryField on Organization | Existing |
| `django-guardian` | Object-level permissions (used framework-wide) | Existing |
| `django-allauth` | Auth, ORCID social login, email management | Existing |
| `easy-thumbnails` | Profile image thumbnails | Existing |
| `shortuuid` | UUID generation for Contributor | Existing |
| `django-model-utils` | FieldTracker for dirty checking | Existing |
| `ordered-model` | Contribution ordering (drag-and-drop) | Existing |
| `research-vocabs` | SKOS vocabulary for roles and identifiers | Existing |
| `jsonfield-toolkit` | ArrayField for links, languages | Existing |
| `django-hijack` | Admin user impersonation | Existing |
| `django-import-export` | CSV/Excel person import | Existing |
| `dal` / `django-autocomplete-light` | Autocomplete widgets | Existing |
| `django-select2` | Select2 multi-select widgets | Existing |
| `django-addanother` | Add-another popup for FK fields | Existing |
| `martor` | Markdown profile editor | Existing |
| `waffle` | Feature flag for signup access | Existing |
| `requests` | ORCID/ROR API HTTP calls | Existing |
| `celery` | Background tasks (framework dependency, not yet used in contributors) | **New usage** |

---

## Decision Records

### D1: ORCID/ROR Synchronization Architecture

**Decision:** Hybrid on-save + periodic Celery task approach.

**Details:**
- **Initial population:** `AFTER_CREATE` lifecycle hook on `ContributorIdentifier` dispatches a Celery task (`sync_contributor_identifier.delay(pk)`) using `transaction.on_commit()` to ensure DB visibility
- **Periodic refresh:** Celery beat task runs weekly (Sunday 3:00 AM UTC), queries contributors where `last_synced < 7 days ago`, processes in batches of 50 with 1s inter-batch delay
- **Never block HTTP:** No synchronous external API calls in lifecycle hooks or views
- **Error handling:** Celery `autoretry_for` with `retry_backoff=True`, `max_retries=3`. Skip 404s (invalid identifiers). Circuit breaker: halt batch if >50% fail within a window.
- **ORCID auth:** OAuth 2.0 client credentials stored in Django settings via `django-environ`. Token cached in Redis with 20-day TTL.
- **ROR auth:** Register free Client-ID. Send as `Client-Id` HTTP header.
- **Connection pooling:** Use `requests.Session()` per Celery task for TCP connection reuse.

**Rationale:** The current codebase makes synchronous API calls from lifecycle hooks (e.g., `ContributorIdentifier.fetch_ror_data()` calls `RORTransform.fetch_from_api()` directly in an `AFTER_CREATE` hook). This blocks the HTTP response and can crash saves on API failure. Deferring to Celery isolates external dependencies.

**Alternatives rejected:**
- Pure on-save (no periodic): Stale data for never-re-saved records
- Django signals instead of lifecycle hooks: Less readable, harder to reason about ordering. Lifecycle already in use project-wide.
- Daily refresh: ORCID/ROR data changes infrequently; weekly is sufficient

### D2: OrganizationMember → Affiliation Migration Strategy

**Decision:** Minimal migration preserving the `type` field for security verification. Add time-bound fields only.

**Sequence:**
1. **Migration 0011:** `AddField` — add `start_date` (PartialDateField, nullable), `end_date` (PartialDateField, nullable)
2. **Migration 0012:** `RenameModel('OrganizationMember', 'Affiliation')` — renames table, auto-updates FK/M2M references
3. **Migration 0013:** `AlterField` — update `related_name` from `"organization_memberships"` to `"affiliations"` on the person FK

**Rationale:** 
- **PartialDateField** allows year-only, year-month, or full date precision. Prevents users from fabricating exact dates for historical affiliations ("some time in 1987" → `{"year": 1987}` instead of forced "1987-01-01").
- **Preserve `type` field**: This is a **security mechanism**, not just workflow. It prevents unauthorized self-affiliation with prestigious organizations. The state machine is:
  - `PENDING (0)`: User created affiliation, awaiting verification from existing member
  - `MEMBER (1)`: Verified member, can access organization resources
  - `ADMIN (2)`: Can manage organization profile and approve pending members
  - `OWNER (3)`: Full management rights, can transfer ownership
- Without this gatekeeping, any user could add "Harvard" as affiliation and gain access to privileged organization data.
- **No data migration needed**: Existing `type` and `is_primary` values are preserved. `start_date`/`end_date` stay NULL for existing records (no creation timestamp available; fabricating would violate FAIR).

**Field semantics after migration:**
| Field | Purpose |
|-------|--------|
| `type` | Security/verification state + role hierarchy (0=pending, 1=member, 2=admin, 3=owner) |
| `is_primary` | User's primary affiliation for citation purposes (only one per person) |
| `start_date` | When affiliation began (PartialDate: year, year-month, or full date) |
| `end_date` | When affiliation ended; NULL = active membership |

**Verification workflow example:**
1. User creates affiliation with Harvard → `type=0` (PENDING)
2. User cannot access Harvard organization resources yet
3. Existing Harvard admin (type≥2) verifies → sets `type=1` (MEMBER)
4. Now user can view Harvard members, contribute to Harvard-affiliated projects
5. Harvard owner promotes to admin → sets `type=2` (ADMIN)
6. Admin can now approve pending members, edit Harvard profile
7. Owner transfers ownership → sets old owner `type=2`, new owner `type=3`

**Alternatives rejected:**
- Remove `type` field entirely: Would eliminate security verification, allowing anyone to claim affiliation with any organization
- Separate `verification_status` + `role` fields: Adds unnecessary complexity; single state machine is clearer
- Keep DateField: Forces users to fabricate exact dates or leave fields blank, violating FAIR principle of capturing available precision

**Alternatives rejected:**
- Create-new-then-migrate: Doesn't preserve FK references automatically; more risk, more migration operations
- Single monolithic migration: No intermediate rollback points; harder to debug failures
- Keeping `db_table='contributors_organizationmember'`: Creates confusion between Python name and DB name

### D3: Person/User Model — Claimed vs Unclaimed States

**Decision:** Add `is_claimed = BooleanField(default=False)` to Person model to explicitly track ownership state. Unclaimed persons have `is_active=True` (not False) to enable email-based invitation flows.

**The Problem with Email-Only Detection:**
Initially considered using `email = NULL` + `is_active = False` as the unclaimed signal. However, this breaks a critical real-world workflow: when researchers add contributors to datasets/publications, best practice is to request their email addresses so contributors can confirm their participation. This prevents reputation gaming (Person X adding Person Y without consent). If we require `email=NULL` for unclaimed, we can't support this ethical workflow. Therefore, **email presence alone cannot determine claimed status**.

**State Machine:**

| State | Description | `email` | `is_claimed` | `is_active` |
|-------|-------------|---------|--------------|-------------|
| **Ghost** | Pure attribution, no contact | NULL | False | True |
| **Invited** | Email added, awaiting signup | NOT NULL | False | True |
| **Claimed** | Owns their account | NOT NULL | True | True |
| **Banned** | Suspended after claiming | NOT NULL | True | False |

**State Transitions:**
```
Ghost (created via create_unclaimed, no email)
  ↓ [email added by dataset creator]
Invited (can receive password reset / invitation link)
  ↓ [confirms signup via allauth]
Claimed (owns account, can log in)
  ↓ [admin suspends]
Banned (locked out)
```

**Why `is_active=True` for Ghosts/Invited:**
- `is_active=False` semantically means "banned/suspended", not "hasn't signed up yet"
- Ghosts aren't banned — they're unclaimed attribution records in good standing
- Invited persons need `is_active=True` so Django auth doesn't block password reset flows
- Django auth already prevents login for users without usable passwords, so no security hole

**Implementation Details:**
- `is_claimed` field added to Person model (nullable for migration, default False going forward)
- Data migration: existing users with `email NOT NULL` → `is_claimed=True`; users created via `create_unclaimed()` → `is_claimed=False`
- Manager method: `Person.objects.real()` returns queryset excluding superusers and guardian AnonymousUser (see D8 for manager unification)
- Queryset methods: `claimed()`, `unclaimed()`, `ghost()`, `invited()`
- Validation: `clean()` prevents claimed users from removing their email (setting to NULL)
- Email normalization: Override `clean()` to fully lowercase local part (Django only lowercases domain)
- Prevent ambiguity: `unique_together` constraint on `ContributorIdentifier(type, value)` enforced (already exists via `UniqueConstraint`)

**Claiming flow:**
1. Admin creates Ghost via `create_unclaimed(first_name, last_name)` → `email=NULL`, `is_claimed=False`, `is_active=True`
2. Dataset creator adds email → Ghost transitions to Invited (same flags, email now populated)
3. Real person signs up via ORCID social login
4. `SocialAccountAdapter.pre_social_login()` matches ORCID → existing identifier
5. allauth connects social account to existing Person
6. `save_user()` sets `is_claimed=True`, populates/updates email from ORCID data
7. Person is now Claimed

**Alternatives rejected:**
- Computed `is_claimed` property: Can't query efficiently (`Person.objects.filter(is_claimed=True)` requires Python-level filtering)
- `email=NULL` requirement for unclaimed: Blocks ethical contributor confirmation workflows
- `is_active=False` for unclaimed: Semantically incorrect (not banned) and blocks invitation/password reset flows
- Separate User + Profile models: Doubles queries, introduces sync bugs, conflicts with the "Person IS the auth model" architecture

### D4: Organization Ownership via Derived Permission Backend

**Decision:** `manage_organization` permission is derived from `Affiliation.type` via a custom authentication backend that queries the database directly. No guardian permission rows are stored; `Affiliation` is the single source of truth.

**Details:**
- `OrganizationPermissionBackend` extends `guardian.backends.ObjectPermissionBackend` 
- When `user.has_perm("contributors.manage_organization", org_instance)` is called:
  - Backend queries: `Affiliation.objects.filter(person=user, organization=org, type=OWNER).exists()`
  - Returns `True` if an OWNER affiliation exists, `False` otherwise
  - Falls through to parent backend for all other permission checks
- No lifecycle hooks needed — permission is computed on-demand from current database state
- No guardian permission rows stored — eliminates synchronization bugs and cache staleness issues
- Multiple owners supported naturally (multiple OWNER affiliations = multiple users pass the check)
- Ownerless fallback: staff/superusers bypass via `ModelBackend` (first in `AUTHENTICATION_BACKENDS`)

**Architecture pattern:**
This follows the same pattern as `SamplePermissionBackend` and `MeasurementPermissionBackend` already in the codebase, which derive permissions from parent Dataset permissions. Consistency with existing project architecture.

**Backend implementation:**
```python
# fairdm/contrib/contributors/permissions.py
from guardian.backends import ObjectPermissionBackend

class OrganizationPermissionBackend(ObjectPermissionBackend):
    """Derive manage_organization permission from OWNER Affiliation."""
    
    def has_perm(self, user_obj, perm, obj=None):
        if obj is None or not isinstance(obj, Organization):
            return super().has_perm(user_obj, perm, obj)
        
        if perm == "contributors.manage_organization":
            from fairdm.contrib.contributors.models import Affiliation
            return Affiliation.objects.filter(
                person=user_obj,
                organization=obj,
                type=Affiliation.MembershipType.OWNER
            ).exists()
        
        return super().has_perm(user_obj, perm, obj)
```

**View-level enforcement:**
- Detail/edit views: `user.has_perm("contributors.manage_organization", org_instance)` — works unchanged
- List filtering: Use `Organization.objects.filter(affiliations__person=user, affiliations__type=OWNER)` instead of guardian's `get_objects_for_user()`
- Admin override: staff/superusers pass all `has_perm` checks via `ModelBackend`

**Benefits over lifecycle hook approach:**
1. **No synchronization bugs** — there's nothing to synchronize; permission = current affiliation state
2. **No cache staleness** — each check is a fresh query (or uses Django's queryset cache naturally)
3. **No guardian permission rows** — simpler database schema, no cleanup migrations needed
4. **Simpler tests** — no `ObjectPermissionChecker` workarounds or cache clearing
5. **Transaction-safe by design** — permission reflects committed affiliation changes immediately
6. **Follows project patterns** — matches existing `SamplePermissionBackend` architecture

**Granularity decision:** A single coarse permission is sufficient because:
1. The target audience (research teams) benefits from simplicity
2. The `Affiliation.role` field already provides internal role differentiation
3. Multiple granular permissions would add query complexity with minimal governance benefit

**Alternatives rejected:**
- Lifecycle hooks syncing guardian rows: Fragile under test database reuse, vulnerable to `.update()` bypasses, cache staleness issues
- Multiple permissions (`edit_organization`, `manage_members`, `transfer_ownership`): Over-engineering for the use case
- Nullable `owner` FK on Organization: Duplicates membership data; inconsistency risk
- Service layer for ownership transfer: Over-engineered; promotions/demotions are independent operations, not bundled transfers

### D5: Metadata Transform Architecture

**Decision:** Hybrid registry + strategy pattern. Keep the existing `BaseTransform` class-based architecture; add a module-level `TransformRegistry` singleton for discovery and extensibility.

**Details:**
- Registry API: `transforms.register("datacite", DataCiteTransform)` or `@transforms.register("datacite")` decorator
- Discovery: `transforms.get("datacite")`, `transforms.list()`, `transforms.export_all(contributor)`
- `import_data()` returns `ImportResult` dataclass: `{instance, created, unmapped_fields, warnings}`
- Validation: Pydantic models (one per transform) for structured inbound data validation. `validate()` returns `ValidationResult(valid, errors, warnings)`
- Transforms remain stateless by default; accept optional `config: dict` via `__init__`
- Each transform documents: `format_name`, `format_version`, `content_type`, `supports_persons`, `supports_organizations`, `supported_fields()`, fidelity notes
- ROR transform updated to v2.1 API schema (`names` array, `locations` instead of `addresses`)
- Testing: provide `TransformTestMixin` with standard `test_export_person`, `test_import_person`, `test_round_trip` methods

**Formats supported:**
| Format | Direction | Priority |
|--------|-----------|----------|
| DataCite 4.4 | Export + Import | P1 (built-in) |
| Schema.org JSON-LD | Export + Import | P1 (built-in) |
| CSL-JSON | Export + Import | P1 (built-in) |
| ORCID v3.0 | Import + Fetch | P1 (built-in) |
| ROR v2.1 | Import + Fetch | P1 (built-in) |
| CERIF | Not planned | — |
| JATS | Import-only, future | P6 (lower priority) |

**Alternatives rejected:**
- No registry (direct class usage only): Portal developers can't discover available formats; no central export-all capability
- Marshmallow instead of Pydantic: Pydantic v2 has better DX, is faster, and more widely adopted in scientific Python
- External libraries for DataCite/Schema.org: No Python library handles contributor-specific serialization; custom is correct

### D6: Privacy Controls Architecture

**Decision:** Per-field privacy via a `privacy_settings` JSONField with a `get_visible_fields(viewer)` utility method.

**Details:**
- `privacy_settings = models.JSONField(default=dict)` on `Contributor` (inherited by Person and Organization)
- Keys: `"email"`, `"phone"`, `"location"`, `"biography"`, `"links"`
- Values: `"public"` or `"private"` (two-level for simplicity)
- Always public (no toggle): `name`, ORCID, ROR, contributions, affiliations
- Always private (no toggle): password, session data, internal metadata
- Defaults: unclaimed → all public except email (which is NULL). Claimed → email private, everything else public.
- Method: `contributor.get_visible_fields(viewer: Person | None) → dict` returns field values respecting privacy. If `viewer is None` (anonymous), only public fields. If viewer is the person themselves or staff, all fields.
- GDPR: pseudonymization on account deletion (replace name with "Anonymous Contributor #N", clear personal fields, preserve contribution records)

**Alternatives rejected:**
- Single `privacy_level` enum: Too coarse for research contexts where some fields must be public for FAIR compliance
- Separate model for privacy settings: Over-engineering; a JSON field is simpler and self-contained
- Per-field BooleanField columns: Migration overhead for adding/removing privacy-controlled fields

### D7: Celery Task Infrastructure

**Decision:** Create `tasks.py` with three core tasks.

**Tasks:**
1. `sync_contributor_identifier(identifier_pk)` — Fetches ORCID/ROR data for a single identifier. Dispatched from `ContributorIdentifier.AFTER_CREATE` lifecycle hook.
2. `refresh_all_contributors()` — Periodic beat task (weekly). Queries stale contributors, dispatches `sync_contributor_identifier` for each.
3. `detect_duplicate_contributors()` — Periodic beat task (monthly). Runs duplicate detection and creates admin notifications.

**Celery configuration:**
- Use `autoretry_for=(RequestException,)`, `retry_backoff=True`, `max_retries=3`
- Rate limit: `rate_limit="10/m"` for sync tasks
- Use `transaction.on_commit()` when dispatching from lifecycle hooks
- Use `requests.Session()` within tasks for connection reuse

**Alternatives rejected:**
- Django-Q instead of Celery: Celery is already the framework's standard; adding another task queue creates confusion
- Synchronous execution (no Celery): Blocks HTTP responses; fragile to API failures

---

## Technology Evaluation

### No New Dependencies Required

All functionality can be implemented with existing project dependencies. The only consideration is:

- **Pydantic** for transform validation — this is a new dependency. However, it can be deferred to Phase 2 and manual validation used initially. The `BaseTransform.validate()` method can start with manual checks and be upgraded to Pydantic later without API changes.

### ROR API Schema Migration

The current `RORTransform` uses v1 API response fields (`aliases`, `acronyms`, `addresses`, `wikipedia_url`). ROR v2.1 changes the structure significantly:
- `names` array replaces `name`, `aliases`, `acronyms`, `labels`
- `locations` replaces `addresses`
- `links` replaces `links` + `wikipedia_url`

This must be updated as part of the transform work. The existing `synced_data` for organizations already synced from ROR v1 should not be migrated — it will be overwritten on the next periodic sync.

---

### D8: Manager Unification — Single Manager with .real() Method

**Decision:** Merge `PersonalContributorsManager` into `UserManager` using Django's `Manager.from_queryset()` pattern. Replace dual-manager approach (`objects`/`contributors`) with a single unified manager providing `Person.objects.real()` to exclude system accounts.

**The Original Dual-Manager Rationale:**
The codebase had two managers:
- `objects = UserManager()` — returns ALL users including superusers (required by Django auth machinery)
- `contributors = PersonalContributorsManager()` — excludes superusers and guardian AnonymousUser

This split was intentional: portal developers who are also portal users MUST maintain separate accounts—a superuser account for admin tasks AND a normal Person account for research activity. Portal documentation will STRONGLY recommend this separation. Excluding superusers from contributor-facing queries (`Person.contributors.all()`) prevents accidental exposure of all portal users in contributor lists, dropdowns, and attribution widgets.

Django's auth internals (`authenticate()`, session restoration, `createsuperuser` command) require `Person.objects.all()` to return ALL users including superusers, so the base manager cannot filter by default.

**Why Unification is Better:**
1. **Single source of truth**: All query methods (`claimed()`, `unclaimed()`, `ghost()`, `invited()`, `real()`) live on one manager
2. **Better autocomplete/discoverability**: Developers see all methods in one place
3. **Clearer semantics**: `objects.real()` is explicit about excluding system users, vs implicit filtering in a separate manager's `get_queryset()`
4. **Equally safe**: Both approaches require developers to consciously use the safe method (`contributors.all()` vs `objects.real()`)—neither prevents mistakes, but unified is marginally more discoverable

**Implementation:**
```python
class PersonQuerySet(models.QuerySet):
    def real(self):
        """Exclude system accounts (superusers, guardian AnonymousUser).
        Use instead of .all() in portal views and contributor listings."""
        return self.exclude(is_superuser=True).exclude(email="AnonymousUser")

    def claimed(self):
        return self.filter(is_claimed=True)

    def unclaimed(self):
        return self.filter(is_claimed=False)

    def ghost(self):
        return self.filter(is_claimed=False, email__isnull=True)

    def invited(self):
        return self.filter(is_claimed=False, email__isnull=False)

class UserManager(BaseUserManager.from_queryset(PersonQuerySet), PrefetchPolymorphicManager):
    use_in_migrations = False
    # ... existing create_user, create_superuser, create_unclaimed methods
```

On Person model: single manager `objects = UserManager()` (remove `contributors = PersonalContributorsManager()`).

**Usage:**
- Portal views/forms: `Person.objects.real()` — safe for contributor dropdowns, author lists, etc.
- Admin/auth: `Person.objects.all()` — includes superusers (required by Django internals)
- Filtering: `Person.objects.real().claimed()` — chaining works naturally

**Migration path:**
1. Update `managers.py`: create `PersonQuerySet`, merge into `UserManager`
2. Update `models.py`: remove `contributors = PersonalContributorsManager()`
3. Find-and-replace: `Person.contributors.` → `Person.objects.real().` (or just `Person.objects.` where appropriate)
4. Update tests: `test_managers.py` uses `Person.contributors.claimed()` → `Person.objects.claimed()`
5. Update spec contracts: `api-contracts.md` documents `PersonalContributorsManager`

**Alternatives rejected:**
- Keep dual managers: Less discoverable, splits related functionality
- Override `get_queryset()` in UserManager to exclude superusers: Breaks Django auth (session restore, authenticate, etc. require superusers in base queryset)
- Rename method to `contributors()` instead of `real()`: Less clear — "contributors" is a noun (the records themselves), "real" is more descriptive of the filter action

---

### D9: Profile Claiming Scope — Deferred to Feature 010

**Decision:** Remove claiming flows (ORCID, email, token, post-signup merge) from Feature 009. Defer entirely to a dedicated **Feature 010: Profile Claiming & Account Linking**. This spec (009) retains unclaimed *data model* support only — the `is_claimed` BooleanField, `claimed()`/`unclaimed()`/`ghost()`/`invited()` manager methods, and the state machine (Ghost → Invited → Claimed → Banned) — but implements no claiming *flows*.

**Rationale:**
- Claiming is significantly more complex than originally scoped: ORCID-only is insufficient, email matching carries account-takeover risk, post-signup merge requires careful FK reassignment, and all approaches interact deeply with allauth configuration
- Not all researchers have or want an ORCID (60–70 year olds approaching retirement, contributors added by name/affiliation only by unwilling dataset submitters, etc.)
- Each claiming pathway has distinct security requirements:
  - **ORCID social login:** Safest. Pre-signup interception via `pre_social_login` avoids duplicate Person creation entirely. Requires bug fix in current adapter.
  - **Email matching:** Only safe with `ACCOUNT_EMAIL_VERIFICATION = "mandatory"`. Without it, anyone who registers with a guessed email gains another person's attribution record. Must be a per-portal opt-in.
  - **Token-based:** Most robust for admin-initiated claiming. Requires separate token generation/expiry infrastructure.
  - **Fuzzy name matching:** Can only ever surface suggestions for manual admin review — never auto-claim.
  - **Post-signup merge:** Feasible with django-polymorphic (FK reassignment is safe in `transaction.atomic()`), but requires careful handling of `unique_together` conflicts on Contribution, session invalidation, and allauth social account/EmailAddress reassignment before deletion.
- Bundling all of this into 009 risks stalling the data model work, which is independently useful and can ship faster

**What this spec (009) DOES include:**
- `is_claimed` BooleanField on Person model
- `Person.objects.claimed()`, `Person.objects.unclaimed()`, `Person.objects.ghost()`, `Person.objects.invited()` queryset methods
- `Person.objects.create_unclaimed(first_name, last_name)` manager method (creates Ghost state)
- Data model fields that claiming flows will use (`email`, `is_active`, `is_claimed`, `ContributorIdentifier`)
- Unified manager approach: merge `PersonalContributorsManager` into `UserManager` with `Person.objects.real()` method to exclude system accounts (see D8)
- The existing allauth `SocialAccountAdapter` with **bug fix** for inactive user handling (the `pre_social_login` ORCID branch currently sets `is_claimed=True` and connects social account — fix this as part of 009)

**What is explicitly deferred to Feature 010:**
- Email-based claiming flow end-to-end
- Token-based claiming (admin-initiated one-time claim link)
- Fuzzy name match surfacing in admin
- Post-signup merge service (`merge_persons(person_keep, person_discard)`)
- Per-portal claiming configuration (`FAIRDM_CLAIMING_METHODS = [...]`)
- Claiming audit trail

**Alternatives rejected:**
- Implement ORCID claiming only in 009: Even ORCID-only has the adapter bug, flow testing complexity, and future compatibility concerns if 010 adds other methods alongside it. The adapter bug fix is the only ORCID-claiming change in 009.
- Implement all claiming in 009: Unacceptable scope creep; would delay data model and transform work by weeks

---

### D10: Duplicate Detection Algorithm

**Decision:** Provide a utility function `detect_duplicate_contributors()` that returns groups of potentially duplicate Person/Organization records using a multi-signal fuzzy matching approach with configurable thresholds.

**Algorithm:**

1. **Exact identifier matches** (highest confidence):
   - ORCID exact match → 100% confidence, auto-group
   - ROR exact match → 100% confidence, auto-group
   - Email exact match (case-insensitive) → 95% confidence

2. **Name-based fuzzy matching** (lower confidence):
   - Normalize names: strip titles (Dr., Prof.), lowercase, remove diacritics, collapse whitespace
   - Levenshtein distance ratio ≥ 0.85 on normalized full name → 85% confidence
   - First name exact + last name Levenshtein ≥ 0.90 → 80% confidence
   - Last name exact + first initial match → 75% confidence

3. **Affiliation context boost** (for Person records):
   - If two potential duplicates share ≥1 Organization affiliation → +10% confidence

4. **Threshold for surfacing**:
   - Return groups with ≥75% confidence as suggestions
   - Mark ≥95% (ORCID/email exact match) as "high confidence" for admin review priority

5. **Performance**:
   - For portals with >10,000 contributors, run as background Celery task
   - Use database-level similarity search (PostgreSQL `pg_trgm` extension with GIN index on normalized names) for initial candidate retrieval before Python-level Levenshtein

**Success Criterion SC-005 Qualification:**
- SC-005 originally stated "90% true positive, <5% false positive" but lacked algorithm specification
- **Revised interpretation**: The algorithm SHOULD achieve ≥90% true positive detection on test fixtures with known duplicates (same person with typos, missing middle name, etc.) while keeping false positive rate <5%
- Actual performance depends on data quality and will be measured empirically during implementation
- If empirical testing shows lower performance, threshold tuning or additional signals (e.g., affiliation dates, contribution overlap) may be added

**Implementation:**
- Location: `fairdm/contrib/contributors/utils/deduplication.py`
- Function signature: `detect_duplicate_contributors(queryset=None, confidence_threshold=0.75) -> List[DuplicateGroup]`
- Return type: `DuplicateGroup = namedtuple('DuplicateGroup', ['records', 'confidence', 'signals'])`

**Alternatives rejected:**
- Phonetic matching (Soundex, Metaphone): Over-aggressive for international names with non-English phonetics
- Auto-merge on high confidence: Too risky; all merges must be admin-confirmed
- Machine learning classifier: Overkill for initial implementation; rule-based is more transparent and debuggable

---

## Open Questions (Resolved)

All NEEDS CLARIFICATION items from the spec were resolved during the clarification session:

1. ✅ Affiliation vs OrganizationMembership → Single Affiliation model
2. ✅ Person/User coupling → Person IS AbstractUser
3. ✅ Organization ownership → django-guardian `manage_organization`
4. ✅ Sync trigger → On-save to Celery + periodic beat task
5. ✅ Ownerless fallback → Portal admins only
6. ✅ Claiming scope → Data model support only; full flows deferred to Feature 010 (D9)

---

## Supplementary Research: Contributor Claiming & Merging

**Date added:** 2026-02-18
**Purpose:** Deep-dive on the claiming/merging surface area to inform implementation decisions across Features 009 and 010.

**Scope Notes:**
- **Feature 009 (Data Model & Infrastructure):** This research informs the polymorphic structure design, FK relationships, unclaimed state semantics, and migration planning. Relevant sections: Q1 (dual-table layout, polymorphic_ctype), Q4 (is_active flag behavior).
- **Feature 010 (Claiming Flows & Merge Services):** This research informs the implementation of claiming mechanisms and merge operations. Relevant sections: Q1 (merge function), Q2 (all claiming approaches), Q3 (all edge cases), Q4 (allauth integration details).

**Cross-reference:** Feature 010's implementation will build on the data model and infrastructure established by Feature 009. See [../010-profile-claiming/spec.md](../010-profile-claiming/spec.md) for claiming-specific requirements.

---

### Q1: Django-Polymorphic FK Reassignment / Merge Feasibility

**Scope:** Foundational polymorphic structure knowledge (Feature 009) + merge implementation details (Feature 010)

**Relevant to Feature 009:**
- Understanding the dual-table layout is critical for migration planning (existing User → polymorphic Person/Organization)
- Understanding `polymorphic_ctype` behavior informs data model design decisions
- FK relationships (Contribution.contributor, ContributorIdentifier.related) inform the registry and model structure

**Relevant to Feature 010:**
- The `merge_persons()` function implementation
- Transaction safety considerations
- Cascade deletion order

#### Background: The Dual-Table Layout

`Person` stores rows across **three** database tables:

```
auth_user (via AbstractUser's parent)  ← NOT used (Person replaces this entirely)
contributors_contributor               ← PK lives here; polymorphic_ctype here too
contributors_person                    ← person_ptr_id (OneToOne → contributors_contributor)
```

Every FK in the system (`Contribution.contributor`, `ContributorIdentifier.related`) points at `contributors_contributor.id`. The `Person` object's Python-level PK is `contributor_ptr_id`, which IS the same integer as `contributors_contributor.id`.

#### Can You Safely Merge Two Person Instances?

**Short answer: yes, but it requires discipline.**

The merge operation at the DB level is:

```python
from django.db import transaction
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount

def merge_persons(person_keep: Person, person_discard: Person) -> Person:
    """
    Merge person_discard into person_keep.
    person_keep is the canonical record (typically the newly registered user).
    person_discard is the unclaimed stub.

    Must be called inside a transaction.
    """
    with transaction.atomic():
        discard_pk = person_discard.contributor_ptr_id  # == Contributor PK

        # 1. Reassign Contribution FKs (contributor → Contributor PK)
        Contribution.objects.filter(contributor_id=discard_pk).update(
            contributor_id=person_keep.contributor_ptr_id
        )

        # 2. Reassign ContributorIdentifier FKs
        ContributorIdentifier.objects.filter(related_id=discard_pk).update(
            related_id=person_keep.contributor_ptr_id
        )

        # 3. Reassign OrganizationMember (Affiliation) FKs — points at Person PK
        #    which is ALSO contributor_ptr_id
        OrganizationMember.objects.filter(person_id=discard_pk).update(
            person_id=person_keep.contributor_ptr_id
        )

        # 4. Transfer allauth EmailAddress records
        EmailAddress.objects.filter(user=person_discard).update(user=person_keep)

        # 5. Transfer allauth SocialAccount records
        SocialAccount.objects.filter(user=person_discard).update(user=person_keep)

        # 6. Transfer guardian object permissions
        #    UserObjectPermission rows reference user PKs
        from guardian.models import UserObjectPermission
        UserObjectPermission.objects.filter(user=person_discard).update(user=person_keep)

        # 7. Merge profile fields (only fill blanks — don't overwrite real data)
        if not person_keep.profile and person_discard.profile:
            person_keep.profile = person_discard.profile
        if not person_keep.image and person_discard.image:
            person_keep.image = person_discard.image
        if not person_keep.links:
            person_keep.links = person_discard.links
        person_keep.save()

        # 8. Delete the discard person — CASCADE removes:
        #    - contributors_person row (via person_ptr OneToOne)
        #    - contributors_contributor row (cascades up from person_ptr)
        #    - Any remaining allauth EmailAddress/SocialAccount (should be empty now)
        person_discard.delete()

    return person_keep
```

#### The `polymorphic_ctype` Gotcha

`polymorphic_ctype` lives on the **`Contributor`** row (not on `Person`). It stores the `ContentType` for `Person` (i.e., the CT for `contributors.person`). **You do not need to update it** when reassigning FKs because:

- You are **not changing the type** of `person_keep` — it remains a `Person` before and after.
- The FKs being reassigned point at `Contributor.pk` values. After reassignment they still point at a valid `Contributor` row whose `polymorphic_ctype` correctly says "this is a Person".

However, if you were to:
- Change the DB row's `polymorphic_ctype` — it must match the actual subclass table that has a matching `_ptr_id`. Mismatching types will cause `Contributor.objects.get(pk=X)` to return a corrupt proxy.
- **Never** set `polymorphic_ctype` manually without also having the matching subclass row.

#### Known django-polymorphic Merge Patterns

Django-polymorphic itself has **no built-in merge utility**. Community patterns are:

1. **Direct `.update()` on FKs** — what the code above does. Safe as long as you stay within `transaction.atomic()`.
2. **`reset_polymorphic_ctype()`** — from `polymorphic.utils`. Only needed when `polymorphic_ctype` is `NULL` or wrong, not in a normal merge.
3. **Cascade awareness** — deleting a `Contributor` cascades to the child table (`Person`). This is correct behaviour. Do NOT delete `Person` directly before reassigning FKs on `Contributor.pk` references, because `Contributor.delete()` fires first (due to `CASCADE`) and would attempt to null-set or cascade-delete those FKs before you've reassigned them.

**Correct deletion order:**
```python
# WRONG — deletes Contributor first, which cascade-affects FKs before reassignment
person_discard.contributor_ptr.delete()

# CORRECT — .delete() on Person deletes Person row, then Contributor row in a single
# atomic DB operation via CASCADE. But only AFTER FKs have been reassigned above.
person_discard.delete()
```

#### Pre-Signup Interception vs Post-Signup Merge

**Pre-signup interception is strongly preferred.** Here is the comparison:

| Criterion | Pre-signup intercept | Post-signup merge |
|-----------|---------------------|------------------|
| DB state during operation | Clean (no duplicate Person B exists yet) | Two live Person rows + all related FKs |
**Scope:** Claiming flow implementation details (Feature 010 only)

**Relevant to Feature 009:**
- Understanding that `Person.email` has `unique=True` and its implications for unclaimed Person creation
- The concept of `is_active=False` as the unclaimed state marker

**Relevant to Feature 010:**
- All claiming mechanism implementations (email, name-matching, token-based, admin manual)
- Security considerations for each approach
- Integration with allauth adapters

| Risk of duplicate `unique_together` violations | None | High (`Contribution.unique_together=("content_type","object_id","contributor")`) |
| allauth session/token state | Clean | Must clean up sessions, tokens, EmailAddress |
| Number of DB operations | ~3 (activate + connect social account) | ~10–15 |
| Race condition risk | Low | Medium (if two requests hit simultaneously) |
| Correct hook | `pre_social_login` | Post-`user_signed_up` signal |

The pre-signup intercept works via allauth's `pre_social_login` adapter hook (already implemented in [adapters.py](../../fairdm/contrib/contributors/adapters.py)). The current implementation is architecturally correct but **incomplete** — it raises `ImmediateHttpResponse` for inactive users instead of activating them and connecting the social account directly (see gap in the `else` branch at line ~65).

---

### Q2: Non-ORCID Claiming Approaches

#### 2a. Email-Based Claiming

**Mechanism:**
1. Admin pre-creates unclaimed `Person` with `email="known@email.com"`, `is_active=False`.
2. User registers with that identical email via allauth's normal signup.
3. **Problem:** `Person.email` has `unique=True`. If `is_active=False` person already has that email, allauth's `save_user` will try to create a new `Person` with the same email → `IntegrityError`.

**The required hook: `DefaultAccountAdapter.save_user()`**

```python
class AccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        """
        Intercept save_user for email-based claiming.
        If an inactive Person with this email already exists, activate it
        instead of creating a new one.
        """
        email = form.cleaned_data.get("email", "").lower()
        try:
            existing = Person.objects.get(email=email, is_active=False)
        except Person.DoesNotExist:
            return super().save_user(request, user, form, commit=commit)

        # Activate the existing unclaimed person
        existing.is_active = True
        existing.first_name = form.cleaned_data.get("first_name", existing.first_name)
        existing.last_name = form.cleaned_data.get("last_name", existing.last_name)
        existing.set_password(form.cleaned_data["password1"])
        if commit:
            existing.save()
        # Swap allauth's user reference to point at the existing person
        # This is critical — allauth uses request.user after save_user returns
        return existing
```

**Safety:** This is safe **only if email verification is enforced** (`ACCOUNT_EMAIL_VERIFICATION = "mandatory"`). Without it, anyone who guesses that an email is pre-enrolled can claim the account without proving ownership.

**Security consideration:** Email claiming is **not safe for auto-claim without verification**. The correct flow is:
1. Admin sets email → Person stays inactive.
2. User registers with that email → allauth sends verification email.
3. User clicks verify link → `confirm_email` callback fires → at this point (or via signal) activate the Person.

The `allauth.account.signals.email_confirmed` signal is the correct activation point:

```python
from allauth.account.signals import email_confirmed
from django.dispatch import receiver

@receiver(email_confirmed)
def activate_on_email_confirmation(sender, request, email_address, **kwargs):
    user = email_address.user
    if not user.is_active:
        user.is_active = True
        user.save(update_fields=["is_active"])
```

#### 2b. Name-Only Matching

Name matching for auto-claiming is **not reliable enough** to execute automatically. Research literature (and practical experience with author disambiguation systems like OpenAlex, ORCID auto-link) consistently finds:

- Names are not unique identifiers (same name, different person is common in academic contexts)
- Name formatting varies wildly ("J. Smith", "John Smith", "Smith, J.", "John A. Smith")
- Scores above 0.95 similarity still produce false positives at the dataset sizes portals work with

**Recommended approach: suggestion only, never auto-claim**

```python
from difflib import SequenceMatcher
from rapidfuzz import fuzz  # pip install rapidfuzz (lightweight, no new dep if already present)

def find_candidate_unclaimed_persons(name: str, threshold: float = 0.85) -> QuerySet:
    """
    Returns unclaimed Persons whose name fuzzy-matches `name` above threshold.
    For use as admin UI suggestions only — never auto-claim on this basis.
    """
    candidates = Person.objects.filter(is_active=False).values_list("pk", "name")
    matches = [
        pk for pk, candidate_name in candidates
        if fuzz.token_sort_ratio(name.lower(), candidate_name.lower()) / 100 >= threshold
    ]
    return Person.objects.filter(pk__in=matches)
```

For production-quality disambiguation at scale, the `jellyfish` or `rapidfuzz` library provides Levenshtein, Jaro-Winkler, and phonetic algorithms. **The project does not currently have fuzzy matching as a dependency** — it should be optional and wrapped in a utility function.

**Algorithmic comparison:**
| Algorithm | Best for | False positive risk |
|-----------|----------|-------------------|
| Levenshtein / edit distance | Typos in a single name | High for short names |
| Jaro-Winkler | Short strings with prefix matching | Medium |
| Token sort ratio | Reordered name parts ("Smith, John" vs "John Smith") | Low |
| Soundex / Metaphone | Phonetically similar names | High across languages |
| **Token sort + threshold 0.90** | **General contributor matching** | **Low — recommended** |

#### 2c. Manual Admin Claiming

The admin flow for manually linking an unclaimed `Person` to a registered auth account:

**Option A: Custom admin action on `PersonAdmin`**

```python
@admin.action(description="Manually claim selected persons as active users")
def mark_as_claimed(modeladmin, request, queryset):
    # Show an intermediate form asking admin to confirm and optionally select the target user
    # This is standard Django admin wizard pattern
    ...
```

**Option B: Dedicated admin view with `ModelAdmin.get_urls()`**

```python
class PersonAdmin(UserAdmin):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:pk>/claim/",
                self.admin_site.admin_view(self.claim_person_view),
                name="contributors_person_claim",
            ),
        ]
        return custom_urls + urls

    def claim_person_view(self, request, pk):
        """
        Admin view to manually claim an unclaimed Person.
        Renders a form to select an existing active user to merge into,
        or to activate the person in place.
        """
        unclaimed = get_object_or_404(Person, pk=pk, is_active=False)
        if request.method == "POST":
            form = ClaimPersonForm(request.POST)
            if form.is_valid():
                # If merge_target is provided, do full merge
                # If not, just activate in-place
                merge_target = form.cleaned_data.get("merge_target")
                if merge_target:
                    merge_persons(person_keep=merge_target, person_discard=unclaimed)
                else:
                    unclaimed.is_active = True
                    unclaimed.save()
                messages.success(request, "Person successfully claimed.")
                return redirect(reverse("admin:contributors_person_changelist"))
        else:
            form = ClaimPersonForm()
        return render(request, "admin/contributors/person/claim.html", {
            "unclaimed": unclaimed, "form": form,
        })
```

#### 2d. Token-Based Claiming (One-Time Claim Link)

This is the **most secure non-ORCID claiming mechanism** and should be the default for admin-initiated claiming:

```python
import secrets
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.urls import reverse

CLAIM_TOKEN_SALT = "fairdm.contributor.claim"
CLAIM_TOKEN_MAX_AGE = 7 * 24 * 60 * 60  # 7 days in seconds

def generate_claim_token(unclaimed_person: Person) -> str:
    """Generate a signed, time-limited claim token for the given unclaimed person."""
    signer = TimestampSigner(salt=CLAIM_TOKEN_SALT)
    return signer.sign(str(unclaimed_person.pk))

def validate_claim_token(token: str) -> Person | None:
    """Validate a claim token. Returns the unclaimed Person or None if invalid/expired."""
    signer = TimestampSigner(salt=CLAIM_TOKEN_SALT)
    try:
        pk = signer.unsign(token, max_age=CLAIM_TOKEN_MAX_AGE)
        return Person.objects.get(pk=pk, is_active=False)
    except (BadSignature, SignatureExpired, Person.DoesNotExist):
        return None
```

**View flow:**

```python
class ClaimProfileView(View):
    """
    Handles the claim link. Two scenarios:
    A) User is already authenticated → merge unclaimed into their account.
    B) User is not authenticated → redirect to allauth signup with claim token in session.
    """
    def get(self, request, token):
        unclaimed = validate_claim_token(token)
        if unclaimed is None:
            messages.error(request, "This claim link is invalid or has expired.")
            return redirect("home")

        if request.user.is_authenticated:
            merge_persons(person_keep=request.user, person_discard=unclaimed)
            messages.success(request, "Profile successfully claimed.")
            return redirect(request.user.get_absolute_url())
        else:
            # Stash token in session, redirect to signup/login
            request.session["pending_claim_token"] = token
            return redirect(reverse("account_signup"))
```

**Interaction with allauth:** The token flow bypasses allauth's normal duplicate-detection because the user may not yet have an account. After signup, a `user_signed_up` signal receiver checks for a stashed token and performs the merge:
**Scope:** Merge edge case handling (Feature 010 only)

**Relevant to Feature 009:**
- Understanding the FK relationships that must be preserved during merge (Contribution, ContributorIdentifier, OrganizationMember)
- Understanding `unique_together` constraints that affect data integrity

**Relevant to Feature 010:**
- All merge edge case implementations
- Session invalidation
- Role merging logic
- Duplicate detection and conflict resolution


```python
from allauth.account.signals import user_signed_up

@receiver(user_signed_up)
def check_pending_claim(sender, request, user, **kwargs):
    token = request.session.pop("pending_claim_token", None)
    if token:
        unclaimed = validate_claim_token(token)
        if unclaimed and unclaimed.pk != user.pk:
            merge_persons(person_keep=user, person_discard=unclaimed)
```

**Security properties of this approach:**
- Token is time-limited (7 days) via Django's `TimestampSigner` (HMAC-SHA256 with timestamp)
- Token is single-use only if the unclaimed Person is deleted/activated on first use
- Token leakage only risks account takeover if the token recipient's email is compromised (same risk as any "reset password" link)
- Does NOT require ORCID

---

### Q3: Edge Cases for Claiming

#### 3a. Post-Signup Merge: Person B Exists, Then Admin Discovers Person A

This is the hardest scenario. Person B has already registered and may have:
- `Contribution` records pointing at `B.contributor_ptr_id`
- `ContributorIdentifier` records
- allauth `EmailAddress` and `SocialAccount` rows
- `OrganizationMember` (Affiliation) rows
- Active sessions (Django session table)
- Guardian `UserObjectPermission` rows

**Decision: keep Person A as the canonical record (the "real" researcher identity), merge B into A.**

This is counter-intuitive — B is the active user — but A may already have rich contribution history and identifiers attached. The merge function handles this by making `person_keep = person_A` (the richer stub) and `person_discard = person_B` (the newer registration).

**Unique-constraint hazard:** `Contribution` has `unique_together = ("content_type", "object_id", "contributor")`. If both A and B have contributions to the same object, the `.update()` will fail with an `IntegrityError`. Handle with:

```python
# Before bulk update, identify and delete true duplicates
duplicate_contribution_ids = (
    Contribution.objects.filter(contributor_id=discard_pk)
    .filter(
        content_type__in=Contribution.objects.filter(
            contributor_id=keep_pk
        ).values("content_type"),
        object_id__in=Contribution.objects.filter(
            contributor_id=keep_pk
        ).values("object_id"),
    )
    .values_list("id", flat=True)
)
Contribution.objects.filter(id__in=duplicate_contribution_ids).delete()
# Now the bulk update is safe
Contribution.objects.filter(contributor_id=discard_pk).update(
    contributor_id=keep_pk
)
```

**Specific items to clean up when discarding Person B:**

| Item | Action |
|------|--------|
| `Contribution` rows | Reassign → person_keep, delete duplicates |
| `ContributorIdentifier` rows | Reassign, avoid type+value duplicates |
| `OrganizationMember` rows | Reassign, respect `unique_together=("person","organization")` |
| `allauth.EmailAddress` | Reassign to person_keep (keep person_keep's primary, demote B's) |
| `allauth.SocialAccount` | Reassign to person_keep |
| Django sessions | Invalidate all sessions for person_discard (prevents session fixation) |
| Guardian `UserObjectPermission` | Reassign to person_keep (avoid permission duplication) |
| `django-activity-stream` actions | Reassign actor/target to person_keep |

**Session invalidation:**

```python
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session

def invalidate_user_sessions(user: Person) -> None:
    """Invalidate all active sessions for the given user."""
    from django.contrib.auth import SESSION_KEY
    user_sessions = []
    for session in Session.objects.all():
        data = session.get_decoded()
        if str(user.pk) == str(data.get(SESSION_KEY)):
            user_sessions.append(session.pk)
    Session.objects.filter(pk__in=user_sessions).delete()
```

Note: If using Redis-backed sessions (`django-redis`), flush by user ID is not natively supported — use `django-user-sessions` package or the above DB scan approach.

#### 3b. Person B Has Already Accumulated Contributions

These are preserved: `merge_persons()` reassigns them to `person_keep` (Person A). They are not lost. Only exact duplicates (same object, same contributor) are deleted because the DB cannot hold two `Contribution` rows for the same `(content_type, object_id, contributor)` triple.

**Role merging:** If both A and B contributed to the same object but with different roles, the duplicate-handling logic should merge the roles before deleting:

**Scope:** Allauth integration for claiming flows (Feature 010 only, with foundational concepts for Feature 009)

**Relevant to Feature 009:**
- The semantics of `is_active=False` for unclaimed Person instances
- The relationship between Person and allauth's user model (Person IS the user model)
- The adapter pattern already in use in fairdm/contrib/contributors/adapters.py

**Relevant to Feature 010:**
- ORCID claiming `pre_social_login` hook implementation and bug fix
- Email-based claiming via `save_user` override
- Account takeover risk mitigation strategies
- Integration with email verification flow

```python
for contrib_b in Contribution.objects.filter(contributor_id=discard_pk):
    try:
        contrib_a = Contribution.objects.get(
            contributor_id=keep_pk,
            content_type=contrib_b.content_type,
            object_id=contrib_b.object_id,
        )
        # Merge roles from B into A (ConceptManyToManyField)
        contrib_a.roles.add(*contrib_b.roles.all())
        contrib_a.save()
        contrib_b.delete()
    except Contribution.DoesNotExist:
        contrib_b.contributor_id = keep_pk
        contrib_b.save()
```

#### 3c. Can auth User Objects Be Safely Deleted After Merging?

When `person_discard.delete()` is called (at the end of `merge_persons()`):

- The `Person` row is deleted → `contributor_ptr_id` OneToOne cascade deletes the `Contributor` row.
- **Django sessions:** NOT automatically deleted. See session invalidation above.
- **allauth `EmailAddress`:** Must be reassigned BEFORE deletion, otherwise cascade-deleted.
- **allauth `SocialAccount`:** Must be reassigned BEFORE deletion.
- **Guardian `UserObjectPermission`:** Must be reassigned BEFORE deletion (otherwise cascade-deleted).
- **`django-activity-stream` `Action` model:** Action has nullable actor GFK; cascade behaviour depends on `ActorObjectPermission` settings. Reassign before deleting.
- **Auth tokens (DRF `Token`, JWT):** DRF `Token` has `OneToOne → user` with CASCADE. If person_discard has active API tokens, they'll be deleted. This is correct behaviour (tokens for the discarded user should die).

**Result:** `person_discard.delete()` is safe **after** all FKs are reassigned. The only leakage risk is sessions (which aren't FK-linked). Always call `invalidate_user_sessions(person_discard)` before `.delete()`.

---

### Q4: Allauth + Existing Inactive User

#### 4a. ORCID-Based Claiming: Precise Flow

**Current implementation** in [adapters.py](../../fairdm/contrib/contributors/adapters.py) handles this correctly for the "active user" case, but the "inactive user" branch is incomplete. Here is the precise flow and the gap:

```
User visits /accounts/orcid/login/
    ↓
allauth redirects to ORCID OAuth
    ↓
ORCID returns access token + UID (ORCID ID string like "0000-0002-1825-0097")
    ↓
allauth calls SocialAccountAdapter.pre_social_login(request, sociallogin)
    ↓
    [Current code]
    orcid_id = sociallogin.account.uid
    existing_user = get_db_user_by_orcid(orcid_id)
    → queries ContributorIdentifier.objects.filter(value=orcid_id, type="ORCID")
    if existing_user is not None:
        if existing_user.is_active:
            → sociallogin.connect(request, existing_user)  ✅ correct
        else:
            → raise ImmediateHttpResponse(redirect_to_signup(...))  ⚠️ INCOMPLETE
```

**The gap:** When `existing_user.is_active = False` (unclaimed Person), the code redirects to signup. This sends the user through a second signup which will try to create a **new** Person row. The correct behaviour is to activate the existing person and connect the social account here.

**Fixed `pre_social_login`:**

```python
def pre_social_login(self, request, sociallogin):
    if not is_provider("orcid", sociallogin):
        return

    orcid_id = sociallogin.account.uid
    existing_user = self.get_db_user_by_orcid(orcid_id)
    if existing_user is None:
        return  # No match → normal new-user flow

    if existing_user.is_active:
        # Already claimed: just connect and log in
        sociallogin.user = existing_user
        sociallogin.connect(request, existing_user)
        return

    # Unclaimed Person found: activate and connect in pre_social_login.
    # DO NOT redirect to signup — that would create a second Person.
    existing_user.is_active = True
    existing_user.save(update_fields=["is_active"])
    sociallogin.user = existing_user
    # sociallogin.connect() creates the SocialAccount row and logs the user in
    sociallogin.connect(request, existing_user)
    # Raise ImmediateHttpResponse to complete the login immediately,
    # bypassing the normal new-user signup form.
    raise ImmediateHttpResponse(
        HttpResponseRedirect(self.get_login_redirect_url(request))
    )
```

**Then `save_user` also needs guarding:**

In the current `save_user`, the ORCID branch calls `get_db_user_by_orcid()` again. After the fix above, `existing_user.is_active` will be `True` by the time `save_user` is called (if `save_user` is even reached — raising `ImmediateHttpResponse` from `pre_social_login` skips `save_user`). Adding a guard is harmless:

```python
def save_user(self, request, sociallogin, form=None):
    if is_provider("orcid", sociallogin):
        orcid_id = sociallogin.account.uid
        if existing_user := self.get_db_user_by_orcid(orcid_id):
            # Already handled in pre_social_login (active or just-activated)
            sociallogin.user = existing_user
            return existing_user
        # New ORCID user: save normally then create identifier
        user = super().save_user(request, sociallogin, form=form)
        user.identifiers.create(value=orcid_id, type="ORCID")
        return user
    return super().save_user(request, sociallogin, form=form)
```

#### 4b. Email Matching: Inactive User + Same Email Signup

**Scenario:** Unclaimed Person has `email="alice@example.com"`, `is_active=False`. Alice registers with that exact email via standard allauth signup.

**What allauth does by default:**

allauth's signup form (`SignupForm`) calls the `AccountAdapter.save_user()`, which calls `User.objects.create_user(email=email, ...)`. The `Person` model has `email` with `unique=True`. This will raise an `IntegrityError` at the DB level because the email is already taken by the inactive Person.

However, **before** attempting DB save, allauth performs a uniqueness check in `SignupForm.clean_email()` which calls `filter_users_by_email(email)`. This function (from `allauth.account.utils`) returns any `User` with that email, including inactive ones. If it finds one, it raises `ValidationError("A user is already registered with this e-mail address.")`.

**Result: by default, allauth blocks the registration** — the user sees a form error and cannot proceed. This is actually safe (prevents duplicate accounts) but is a terrible user experience.

**To provide the claiming flow instead:**

Override `SignupForm` or the account adapter's `clean_email` behaviour:

```python
class AccountAdapter(DefaultAccountAdapter):
    def clean_email(self, email: str) -> str:
        """
        Override to allow signup with an email belonging to an inactive (unclaimed) account.
        The activation/merge is handled in save_user().
        """
        from allauth.account.utils import filter_users_by_email
        users = filter_users_by_email(email, is_active=True)  # only check ACTIVE
        if users:
            raise ValidationError(
                self.error_messages["email_taken"],
                code="email_taken",
            )
        return email
```

**⚠️ Security warning:** Only skip the check for `is_active=False` users. Never skip for active users. And this must be paired with **mandatory email verification** — otherwise an attacker can register with someone's email and claim their (potentially ORCID-enriched) contributor profile.

#### 4c. Account Takeover Risk via Email-Based Claiming

**Risk:** Without email verification, anyone who knows (or guesses) an email address that an admin has pre-enrolled can claim that contributor's entire research profile.

**Mitigations required (all must be active simultaneously):**

1. `ACCOUNT_EMAIL_VERIFICATION = "mandatory"` — allauth will not log the user in until they click the verification link sent to their address.
2. Rate-limit signup attempts (allauth supports this via `ACCOUNT_RATE_LIMITS`).
3. Activate the Person only after email confirmation (via `email_confirmed` signal as shown in Q2a above), not at signup time.
4. Log all claiming events to the activity stream for audit.
5. Notify the contributor's existing email (if any) when their profile is claimed — relevant for future MFA scenarios.

**Without `ACCOUNT_EMAIL_VERIFICATION = "mandatory"`, email-based claiming must be disabled entirely.** Consider an explicit check:

```python
from django.conf import settings

def save_user(self, request, user, form, commit=True):
    if getattr(settings, "ACCOUNT_EMAIL_VERIFICATION", "none") != "mandatory":
        # Email claiming is unsafe without mandatory verification — skip it entirely
        return super().save_user(request, user, form, commit=commit)
    # ... email claiming logic ...
```

---

### Summary: Recommended Approach for FairDM

Based on the above research, the recommended claiming strategy in priority order:

| Mechanism | Auto-claim? | Security | Recommended |
|-----------|------------|----------|-------------|
| ORCID `pre_social_login` intercept | Yes | High (ORCID = trusted identity) | ✅ Primary |
| Token-based one-time claim link | Yes (on click) | High (HMAC-signed, time-limited) | ✅ Admin tool |
| Email-based claiming (verified) | Yes (after verify) | Medium (requires email ownership) | ✅ With `MANDATORY` verify |
| Name fuzzy match | No (suggestions only) | N/A (manual review required) | ✅ Admin UI only |
| Manual admin merge | Yes (admin action) | High (admin-only) | ✅ Admin action |
| Post-signup merge | Avoid | Lower (more complex, more state) | ⚠️ Last resort only |
