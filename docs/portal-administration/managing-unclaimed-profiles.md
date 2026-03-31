# Managing Unclaimed Profiles

**For portal administrators** responsible for linking contributor records to user accounts.

---

## Overview

When a portal is first populated — or when contributors are imported from external
sources such as publications or CVs — contributor profiles are created without an
associated user account. These profiles are **unclaimed**: they appear in the portal,
their contributions are recorded, but no person has yet signed in and taken ownership.

As an administrator you can:

- Generate a one-time **claim link** to send directly to the contributor.
- **Merge** two contributor records when the same researcher appears more than once.
- View the **audit log** to see all claiming events and diagnose problems.
- Surface **potential duplicates** using the fuzzy name-matching panel.

---

## Claim Pathways

FairDM supports three automatic pathways plus manual admin tools:

| Pathway | How it works |
|---------|-------------|
| **ORCID** | Contributor signs in via ORCID and the portal detects a matching ORCID identifier on an unclaimed profile. Claiming is automatic. |
| **Email** | Contributor registers with the same email address stored on the unclaimed profile. After email verification, the profile is automatically activated. Only works when `ACCOUNT_EMAIL_VERIFICATION = "mandatory"`. |
| **Claim token link** | Admin generates a one-time signed URL and sends it to the contributor. Clicking the link (after sign-in) activates the profile. |
| **Admin merge** | Admin directly merges two Person records from the admin site. |

---

## Generating a Claim Link

Use this when a contributor cannot claim their profile automatically (e.g. no ORCID on
record, or the stored email is out of date).

1. In the Django admin, go to **Contributors → Persons**.
2. Locate the unclaimed profile. A `—` icon in the *Claimed* column indicates an
   unclaimed profile.
3. Select the checkbox next to the person's name.
4. From the **Action** dropdown, choose **"Generate claim link for selected Person"**
   and click **Go**.
5. A page is shown with:
   - The full shareable claim URL (click the copy button).
   - Expiry information (links expire after 7 days by default).
   - The person's recent claiming history from the audit log.
6. Send the URL to the contributor by email or other secure channel.

```{warning}
**One-time use, not invalidated on re-issue.** Generating a new claim link does **not**
invalidate previously generated links for the same person. All unexpired links remain
valid until one is redeemed. Once the profile is claimed, all remaining links for that
person are automatically revoked (because the person is now marked `is_claimed=True`).
```

```{tip}
Change `CLAIM_TOKEN_MAX_AGE` in your portal settings to adjust the link expiry window.
Default is `604800` seconds (7 days).
```

---

## Merging Two Person Records

Use the merge action when the same researcher has two separate records in the portal —
for example, an imported unclaimed profile and a freshly registered account.

**What the merge transfers:**

- All dataset, sample, and measurement contributions
- External identifiers (ORCID, ROR, etc.)
- Institutional affiliations
- allauth email addresses and social accounts (ORCID, etc.)
- Guardian object-level permissions
- Profile fields (blank fields on the kept record are filled from the discarded record)

**What happens to the discarded record:**

- All active sessions are invalidated.
- The record is permanently deleted after a successful merge.

**Steps:**

1. In the Django admin, go to **Contributors → Persons**.
2. Select the **source** record to be discarded (the one that will be deleted).
3. From the **Action** dropdown, choose **"Merge selected Person into another…"** and
   click **Go**.
4. A confirmation page lists what will be transferred. Select the **target** Person (the
   one that survives) from the dropdown.
5. Review the transfer summary and click **Confirm merge**.

```{warning}
**Merges are permanent.** Although the operation is wrapped in a database transaction
(so it either completes fully or rolls back entirely), the discarded Person record is
deleted on success. There is no undo — take care to select the correct target.
```

---

## Interpreting the Audit Log

Every claiming event — successful or failed — is recorded in the **Claiming Audit Log**.
The log is immutable: records are never modified or deleted.

**To view the audit log:**

1. In the Django admin, go to **Contributors → Claiming Audit Logs**.
2. Use the **Method** and **Success** filters to narrow the results.
3. Use the date hierarchy (top of the list) to browse by date.

**Columns explained:**

| Column | Description |
|--------|-------------|
| `timestamp` | When the event occurred. |
| `method` | Pathway used: `orcid`, `email`, `token`, `admin_merge`, or `admin_manual`. |
| `source_person` | The unclaimed Person that was being claimed. |
| `target_person` | The resulting claimed Person (often the same as source for simple claims). |
| `initiated_by` | The admin who initiated the event (if admin-driven). |
| `success` | Whether the claim succeeded. |
| `failure_reason` | Populated only for failed events — explains why the claim was rejected. |

**Common failure reasons:**

- `Person is already claimed.` — The token or ORCID was valid but the profile had
  already been claimed by the time the request arrived.
- `Person is banned (is_active=False).` — An admin has deactivated this profile. Lift
  the ban before claiming is possible.
- Token expired or tampered — The claim link was used after its expiry window or the
  URL was modified.

---

## Fuzzy Name Matching

When viewing an unclaimed Person's change page in the admin, a **"Potential Duplicates"**
panel at the bottom lists other Persons whose names are similar (similarity ≥ 85%).

This panel is calculated on-demand and never triggers an automatic claim. It is a
discovery tool to help you identify pairs of records that may belong to the same person,
so you can then use the merge action if appropriate.

Click **"Generate Claim Link"** next to any suggestion to go directly to the claim link
page for that person.

---

## Banned Profiles

A profile whose `is_active` flag is set to `False` is considered **banned**. All
claiming pathways (ORCID, email, token) will reject a claim attempt for a banned profile
and log the failure with reason `"Person is banned (is_active=False)."`.

To allow claiming again, re-enable the profile:

1. Go to **Contributors → Persons → [person's change page]**.
2. Check the **Active** checkbox.
3. Save the record.

---

## Settings Reference

| Setting | Default | Description |
|---------|---------|-------------|
| `CLAIM_TOKEN_MAX_AGE` | `604800` (7 days) | Maximum age in seconds for claim token links. |
| `CLAIM_TOKEN_SALT` | `"fairdm.contributor.claim"` | HMAC salt used when signing tokens. Changing this invalidates all existing tokens. |
| `ACCOUNT_EMAIL_VERIFICATION` | `"mandatory"` | When set to `"mandatory"`, email-based claiming is active. Other values disable the email pathway entirely. |
