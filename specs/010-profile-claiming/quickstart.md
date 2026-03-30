# Quickstart: Profile Claiming & Account Linking

**Feature:** 010-profile-claiming
**Date:** 2026-03-30

---

## For Portal Administrators

### 1. Configure Claiming Methods

By default, all claiming methods are enabled. To customize, add to your portal settings:

```python
# settings.py — Enable only specific claiming methods
FAIRDM_CLAIMING_METHODS = ["orcid", "email", "token", "admin_merge"]

# Or disable all claiming
FAIRDM_CLAIMING_METHODS = []
```

### 2. Ensure Email Verification (Required for Email Claiming)

Email-based claiming **requires** mandatory email verification. This is the default in FairDM:

```python
# Already set by default in fairdm/conf/settings/auth.py
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
```

If your portal does not enforce mandatory email verification, email-based claiming will be automatically disabled for security.

### 3. ORCID Social Login (Required for ORCID Claiming)

ORCID claiming requires ORCID social login to be configured. This is already set up in FairDM's default settings. Ensure your portal has valid ORCID OAuth credentials:

```python
SOCIALACCOUNT_PROVIDERS = {
    "orcid": {
        "BASE_DOMAIN": "orcid.org",
        "MEMBER_API": False,
    }
}
```

Register your OAuth application at <https://orcid.org/developer-tools>.

### 4. Generate Claim Links

1. Navigate to **Admin > Community > Persons**
2. Find the unclaimed Person profile
3. Click "Generate Claim Link"
4. Copy the claim URL and send it to the researcher (via email, etc.)

The link is valid for 7 days by default (override via `CLAIM_TOKEN_MAX_AGE` in seconds).

### 5. Merge Duplicate Profiles

1. Navigate to **Admin > Community > Persons**
2. Find the unclaimed Person profile
3. Review "Suggested Matches" panel for potential duplicates
4. Click "Merge" to combine profiles, or "Dismiss" for incorrect matches
5. Confirm the merge operation

### 6. View Audit Trail

All claiming events are logged. Navigate to **Admin > Community > Claiming Audit Log** to view:

- Who claimed what profile
- Which method was used
- Success/failure status
- IP addresses for security review

---

## For Portal Developers

### Token Generation

Claim tokens require no database entry — they are opaque signed strings. Generate one programmatically:

```python
from fairdm.contrib.contributors.utils.tokens import generate_claim_token
from django.urls import reverse

token_string = generate_claim_token(unclaimed_person)
claim_url = request.build_absolute_uri(reverse("contributors:claim", args=[token_string]))
# Send claim_url to the researcher
```

### Extending Claiming Behavior

To add custom logic to claiming flows, use Django signals:

```python
from fairdm.contrib.contributors.signals import person_claimed, persons_merged

@receiver(person_claimed)
def on_person_claimed(sender, person, method, **kwargs):
    """Custom logic after a profile is claimed."""
    # e.g., send welcome email, update external systems
    pass

@receiver(persons_merged)
def on_persons_merged(sender, person_keep, person_discard_pk, **kwargs):
    """Custom logic after two profiles are merged."""
    # e.g., update search index, notify collaborators
    pass
```

### Programmatic Claiming

```python
from fairdm.contrib.contributors.services.claiming import claim_via_token
from fairdm.contrib.contributors.utils.tokens import generate_claim_token, validate_claim_token

# Generate a claim token string (stateless — no DB record)
token_string = generate_claim_token(unclaimed_person)

# Validate and use a token
person = validate_claim_token(token_string)  # returns Person or None
if person:
    claimed_person = claim_via_token(token_string, authenticated_user)
```

### Programmatic Merge

```python
from fairdm.contrib.contributors.services.merge import merge_persons

# Merge person_discard into person_keep (atomic, safe)
result = merge_persons(person_keep=active_person, person_discard=unclaimed_person)
# result is person_keep with all data from person_discard transferred
```

---

## How Claiming Works (End-User Perspective)

### ORCID Claiming (Automatic)

1. Researcher clicks "Sign in with ORCID"
2. System checks if an unclaimed profile with that ORCID exists
3. If yes: profile is automatically linked — no action needed
4. If no: new profile is created normally

### Email Claiming (Semi-Automatic)

1. Portal admin sets an email on an unclaimed Person profile
2. Researcher signs up with that same email
3. Researcher verifies their email via the confirmation link
4. Profile is automatically linked after verification

### Token Claiming (Admin-Initiated)

1. Portal admin generates a claim link for an unclaimed profile
2. Admin sends the link to the researcher
3. Researcher clicks the link
4. If already logged in: profile is linked immediately
5. If not logged in: prompted to sign up or log in, then profile is linked

---

## Configuration Reference

| Setting | Default | Description |
|---------|---------|-------------|
| `CLAIM_TOKEN_MAX_AGE` | `604800` (7 days) | Token expiry in seconds |
| `CLAIM_TOKEN_SALT` | `"fairdm.contributor.claim"` | HMAC signing salt (change to invalidate all outstanding tokens) |
| `ACCOUNT_EMAIL_VERIFICATION` | `"mandatory"` | Required for email claiming |
