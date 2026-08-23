# Managing Contributors

This guide covers administrator workflows for managing people, organizations, and affiliations in your research portal.

## Overview

The Contributors system provides admin interfaces for:

- **Person Admin**: Unified user account + contributor profile management
- **Organization Admin**: Organization management with inline affiliations
- **Affiliation Admin**: Verification and role management workflows
- **ORCID/ROR Sync**: Background synchronization with external scholarly databases

## Person Admin Interface

### Unified Auth + Contributor Fields

The Person admin combines Django's user management with contributor-specific fields in a single interface.

### Key Admin Sections

**Basic info**:
- Avatar image
- Name fields (first_name, last_name, auto-generates the display name)
- Email address (required for claimed accounts, NULL for unclaimed)
- Profile/biography
- Public identifier (`uuid`) and the added/modified timestamps — shown, read-only
- Last synced date

**Account**:
- Password
- `is_active`: standard Django active status
- `is_staff`: Django admin access
- `is_superuser`: full system access

**Permissions**:
- Django groups

**Inline sections**:
- Account emails (via allauth)
- Affiliations
- External identifiers (ORCID, etc.)

The changelist reports each person's derived account state (`account_state`
in `list_display`) alongside name, email and staff status, and search
covers name, email and the public identifier.

### State Machine Overview

Person accounts occupy exactly one of four states, in this precedence —
inactive overrides claimed, claimed overrides invited, invited overrides
ghost (D8):

1. **Inactive**: `is_active=False`, regardless of `is_claimed`. Account
   disabled but data preserved.

2. **Claimed**: `is_active=True`, `is_claimed=True`. Full user account with
   authentication; appears in portal member listings.

3. **Invited**: `is_active=True`, `is_claimed=False`, `email` set.
   Invitation sent but not yet accepted. Invitation workflows are Feature
   010 (not yet released).

4. **Ghost**: `is_active=True`, `is_claimed=False`, `email=None`. Created
   automatically during data import for attribution; not searchable in
   portal member listings.

### Claim-Status Filter

The **Claimed Status** filter in the Person changelist reads `is_claimed`
and `is_active` directly, not the email address — an invited person has an
email but has not claimed their account, so email presence alone cannot
tell the two apart.

- **Claimed** shows only accounts with `is_active=True` and
  `is_claimed=True` — state 2 above.
- **Unclaimed** shows everything else — inactive, invited and ghost
  accounts (states 1, 3 and 4).

### Creating Person Records

**Via the Django Admin ("Add person")**:

1. Navigate to **Contributors > Persons > Add person**
2. Fill required fields: email address, first name, last name (a password is optional —
   leaving it blank creates the account with an unusable password)
3. Save

The system automatically generates `name` from first_name + last_name. `is_claimed` is **not**
on this form and is not set by creating a record here — it stays `False`, so a person created
this way is **Invited** (has an email, not yet claimed), not **Claimed**. Actually claiming an
account happens through one of the pathways in
[Managing Unclaimed Profiles](managing-unclaimed-profiles.md#claim-pathways).

**Creating Unclaimed ("Ghost") Records** (for data attribution):

The admin's "Add person" form requires an email address, so a ghost record — no email at all —
cannot be created there. Use the manager method instead, from the Django shell or an import
script:

```python
from fairdm.contrib.contributors.models import Person

Person.objects.create_unclaimed(first_name="Jane", last_name="Doe")
# email=None, is_active=True, is_claimed=False, unusable password
```

Use for attributing data to people who haven't registered yet — this is also the path bulk data
import uses.

### Bulk ORCID Import

To import multiple people from ORCID:

1. Prepare CSV with ORCID IDs:
   ```text
   orcid_id
   0000-0002-1825-0097
   0000-0003-1234-5678
   ```

2. Use Django shell:
   ```python
   import csv
   from fairdm.contrib.contributors.models import Person
   
   with open('orcids.csv') as f:
       reader = csv.DictReader(f)
       for row in reader:
           Person.from_orcid(row['orcid_id'])
   ```

3. Background tasks will sync full ORCID data asynchronously

## Organization Admin Interface

### Organization Overview

Organizations represent institutions, companies, research groups, and other organizational entities.

### Admin Features

**Inline Memberships**:
- View and edit affiliations directly within organization admin
- Add new members inline
- Assign roles (PENDING, MEMBER, ADMIN, OWNER)

**Sub-organizations**:
- Sub-organizations (children by the self-referencing `parent` field) are
  listed in their own inline on the organization change screen, alongside
  the member inline

**Fieldsets and filters**:
- The change form groups fields into Basic info, Location and
  Synchronisation sections
- The changelist can be filtered by country
- The public identifier (`uuid`) is shown and read-only

**Affiliation Admin**:
- Affiliations also have their own top-level admin screen (list, add,
  change), independent of the person/organization inlines, with
  autocomplete on the person and organization fields
- A non-superuser's changelist there is scoped to the affiliations of
  organizations they currently manage — that is, organizations where they
  hold a current OWNER affiliation. A superuser sees every affiliation.

**ROR Synchronization**:
- Admin action: "Sync from ROR"
- Select organizations with ROR identifiers
- Triggers background sync task
- Updates organization metadata from ROR

**Ownership Transfer**:
- Admin action: "Transfer Ownership"
- Select a single organization, choose the new owner from the "New owner"
  field in the action bar, then run the action
- Performs the transfer directly — demotes the incumbent owner to ADMIN and
  promotes the chosen member to OWNER

### Creating Organizations

1. Navigate to **Contributors > Organizations > Add organization**
2. Fill required fields:
   - Name
   - City (optional)
   - Country (optional)
   - Location (lat/lon, optional)
3. Save

To link with ROR:
1. Create organization
2. Add ContributorIdentifier with type="ROR" and value="0xxxxxx00"
3. Use "Sync from ROR" admin action to populate metadata

### Managing Organization Memberships

**Adding Members**:

1. Open organization in admin
2. Scroll to "Affiliations" inline section
3. Click "Add another Affiliation"
4. Select:
   - Person
   - Type (PENDING, MEMBER, ADMIN, OWNER — see Affiliation Type Meanings,
     below, for who may set ADMIN or OWNER)
   - Start date (PartialDate: "2020", "2020-03", or "2020-03-15")
   - End date (optional, leave NULL for current affiliation)
   - Is primary (one per person)
5. Save

Setting Type to ADMIN or OWNER without `manage_organization` on this
organization is refused with a field error on save — nothing is written.

**Affiliation Type Meanings**:
- **PENDING**: Membership pending verification (no permissions)
- **MEMBER**: Regular member (read-only org access)
- **ADMIN**: Administrator (can manage memberships)
- **OWNER**: Owner — holding a *current* OWNER affiliation (no end date) on
  an organisation is what `manage_organization` on that organisation
  *means*

Setting an affiliation's type to ADMIN or OWNER requires the acting user to
already hold `manage_organization` on that organization themselves — an
account without it cannot promote anyone, including itself, to either type.
The same check applies to changing or deleting an affiliation that already
carries ADMIN or OWNER. It reaches every place a type can be written: the
standalone Affiliation admin, the affiliations inline on a person's own
change form, and the members inline on an organization's change form.

### Ownership is derived, not stored

`manage_organization` is not a permission record. `OrganizationPermissionBackend`
answers `user.has_perm("manage_organization", organization)` by checking, at
the moment of the call, whether the user holds a *current* OWNER affiliation
on that organization — one whose end date is not set. Nothing is granted,
revoked or written when an affiliation's type or end date changes — there is
no permission row to fall out of step with the affiliation, because there is
no permission row.

A stored django-guardian grant of `manage_organization` is never consulted
either, even if one exists in the database. A current OWNER affiliation and
superuser status are the only two sources of this right.

One consequence: a demotion takes effect on the very next permission check,
with no separate revocation step. Editing an affiliation's type away from
OWNER, or setting its end date, is enough on its own — either ends the
derived permission the moment it is next checked. Setting the end date is
the documented way to offboard someone: it ends the rights the type
conferred without also requiring you to change the type.

Another: the model does not enforce a single owner. Nothing stops two
affiliations on the same organisation both being current OWNER, and each of
those people independently holds `manage_organization`. Editing an
affiliation's type to OWNER by hand, on its own, does **not** demote whoever
already holds it — it adds a second owner. Use `transfer_ownership()`
(below) when the intent is to hand the role to someone else rather than add
them alongside the incumbent. Setting a type to OWNER by hand is itself
gated: the acting user must already hold `manage_organization` on that
organization — see [Managing Organization
Memberships](#managing-organization-memberships) above.

### Transferring Organization Ownership

**Via Admin Action**: Select a single organization in the admin changelist,
pick the new owner from the "New owner" field next to the action dropdown,
and choose "Transfer Ownership". The action calls
`Organization.transfer_ownership()` itself and reports the outcome — every
current owner is demoted to ADMIN and the chosen member becomes OWNER. It
requires the acting user to hold `manage_organization` on that organisation
(a current OWNER affiliation, or superuser). Holding only the ordinary
`change_organization` permission that gets an account into the admin at all
is not enough. If the model method refuses the new owner (see below), the
action reports the same message as an error instead of transferring
anything.

**Via `Organization.transfer_ownership()`**: the model method that performs
an actual transfer — demoting every *current* owner to ADMIN and promoting
the named person to OWNER in one atomic operation. The named person must
hold a *current* affiliation (no end date) of MEMBER standing or higher, and
must be an active, claimed account:

```python
from fairdm.contrib.contributors.models import Organization, Person

organization = Organization.objects.get(name="Example University")
new_owner = Person.objects.get(email="new.owner@example.edu")

organization.transfer_ownership(new_owner)
# new_owner now holds `manage_organization`; the previous owner is now ADMIN.
```

Each of the following is refused with `ValidationError`, and changes
nothing:

- `new_owner` holds no affiliation on the organisation at all.
- `new_owner`'s affiliation with the organisation has ended.
- `new_owner`'s affiliation is still PENDING verification.
- `new_owner` has not claimed their account.
- `new_owner`'s account is deactivated.

## Affiliation Verification Workflow

### Workflow Overview

1. **User Requests Affiliation** (Feature 010 - not released):
   - User submits affiliation request via portal UI
   - Creates Affiliation with type=PENDING

2. **Admin Reviews**:
   - Navigate to **Contributors > Affiliations**
   - Filter by `type=PENDING`
   - Review request

3. **Approve or Reject**:
   - **Approve**: Change type to MEMBER. Approving to ADMIN needs the
     approving user to already hold `manage_organization` on that
     organization themselves — see [Managing Organization
     Memberships](#managing-organization-memberships)
   - **Reject**: Delete affiliation or leave as PENDING with note

4. **Permission Effect**:
   - No permission row is written anywhere — `manage_organization` is derived, not stored (see
     [Ownership is derived, not stored](#ownership-is-derived-not-stored) below)
   - A current OWNER affiliation makes `user.has_perm("contributors.manage_organization", org)`
     true on the very next check, with nothing further to run

### Affiliation Admin List Filters

The Affiliation changelist filters on:
- **Type**: PENDING, MEMBER, ADMIN, OWNER
- **Primary only**: `is_primary`

The person and organization fields use autocomplete widgets rather than a
list filter.

### Bulk Affiliation Management

To verify multiple pending affiliations:

1. Filter list: `type=PENDING`
2. Select affiliations to approve
3. Choose admin action: "Approve affiliations"
4. Confirm bulk update

*(Note: Custom admin action required - not in base FairDM)*

## ORCID/ROR Sync Troubleshooting

### Background Task System

ORCID and ROR synchronization uses Celery background tasks:

- **Person.from_orcid()**: Schedules `sync_contributor_identifier` task
- **Organization.from_ror()**: Schedules `sync_contributor_identifier` task
- **Admin Actions**: "Sync from ROR" runs background sync

### Checking Sync Status

**Via Admin Interface**:

1. Open Person or Organization in admin
2. Check "Synced data" readonly field:
   - If empty: No sync data available
   - If populated: Shows raw JSON from ORCID/ROR
3. Check "Last synced" timestamp

**Via Django Shell**:

```python
from fairdm.contrib.contributors.models import Person

person = Person.objects.get(email="example@example.com")
print(person.synced_data)  # Raw ORCID data
print(person.last_synced)  # Timestamp

# Get ORCID identifier
orcid = person.identifiers.filter(type="ORCID").first()
if orcid:
    print(f"ORCID ID: {orcid.value}")
```

### Common Sync Issues

**Issue: ORCID sync fails**

Symptoms:
- `synced_data` empty after sync
- `last_synced` not updated

Troubleshooting:
1. Check Celery worker is running:
   ```bash
   celery -A config worker -l info
   ```

2. Check ORCID API credentials in settings:
   ```python
   # config/settings.py
   ORCID_CLIENT_ID = env("ORCID_CLIENT_ID")
   ORCID_SECRET = env("ORCID_SECRET")
   ```

3. Verify ORCID identifier format:
   - Correct: `0000-0002-1825-0097`
   - Incorrect: `https://orcid.org/0000-0002-1825-0097`

4. Check Celery task status:
   ```bash
   # Install flower for monitoring
   celery -A config flower
   # Visit http://localhost:5555
   ```

**Issue: ROR sync not updating organization**

Troubleshooting:
1. Verify ROR ID format:
   - Correct: `04aj4c181` (9 characters, starts with 0)
   - Also accepts: `https://ror.org/04aj4c181`

2. Check ROR identifier exists:
   ```python
   org = Organization.objects.get(pk=123)
   ror = org.identifiers.filter(type="ROR").first()
   print(ror.value)  # Should print ROR ID
   ```

3. Manually trigger sync:
   ```python
   from fairdm.contrib.contributors.tasks import sync_contributor_identifier
   
   ror_id = org.identifiers.filter(type="ROR").first()
   sync_contributor_identifier.delay(ror_id.pk)
   ```

**Issue: Celery broker not configured**

Error: `kombu.exceptions.OperationalError: [Errno 111] Connection refused`

Fix:
1. Start Redis:
   ```bash
   # Linux/Mac
   redis-server
   
   # Windows (via Docker)
   docker run -d -p 6379:6379 redis
   ```

2. Configure broker in settings:
   ```python
   # config/settings.py
   CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/0")
   ```

3. Restart Celery worker

### Manual Sync (No Celery)

To sync without Celery (development only), call the transform's own `update_or_create()` —
the same classmethod `Person.from_orcid()` and `Organization.from_ror()` schedule
asynchronously — directly and synchronously:

```python
from fairdm.contrib.contributors.utils.transforms import ORCIDTransform, RORTransform

# ORCID sync — force=True re-fetches even if last_synced is recent
person = Person.objects.get(email="example@example.com")
if person.identifiers.filter(type="ORCID").exists():
    person, _created = ORCIDTransform.update_or_create(
        person.identifiers.get(type="ORCID").value, force=True
    )

# ROR sync (same pattern)
org = Organization.objects.get(pk=123)
if org.identifiers.filter(type="ROR").exists():
    org, _created = RORTransform.update_or_create(
        org.identifiers.get(type="ROR").value, force=True
    )
```

## Data Cleanup & Maintenance

### Finding Orphaned Ghosts

Ghost persons (unclaimed, no email) created during data import but never used:

```python
from fairdm.contrib.contributors.models import Person

# Find ghosts with no contributions
ghosts_without_data = Person.objects.ghost().filter(
    contributions__isnull=True,
    affiliations__isnull=True
)

# Optionally delete
# ghosts_without_data.delete()
```

### Merging Duplicate Persons

The Person admin's **"Merge selected Person into another…"** action does this transactionally,
including identifiers, allauth accounts and guardian permissions, and is the recommended route —
see [Merging Two Person Records](managing-unclaimed-profiles.md#merging-two-person-records).
Running it requires a superuser account: the action is absent from a non-superuser's changelist,
and the confirmation page itself refuses a non-superuser with a 403 if reached directly. The
manual approach below only reassigns contributions and affiliations, and is a narrower fallback
for the pieces the admin action does not cover:

If duplicate person records exist:

1. Identify duplicates (same name, similar email/ORCID)
2. Choose canonical record
3. Reassign contributions:
   ```python
   from fairdm.contrib.contributors.models import Person, Contribution
   
   canonical = Person.objects.get(pk=primary_id)
   duplicate = Person.objects.get(pk=duplicate_id)
   
   # Move contributions
   Contribution.objects.filter(contributor=duplicate).update(contributor=canonical)
   
   # Move affiliations
   duplicate.affiliations.update(person=canonical)
   
   # Delete duplicate
   duplicate.delete()
   ```

4. Verify contributions transferred:
   ```python
   canonical.contributions.count()  # Should include old duplicate's contributions
   ```

## Performance Optimization

### Large Contributor Databases

For portals with 10,000+ contributors:

**QuerySet Optimization**:
```python
# Use select_related for foreign keys
affiliations = Affiliation.objects.select_related('person', 'organization')

# Use prefetch_related for reverse relations
people = Person.objects.prefetch_related('affiliations', 'contributions')

# Annotate counts to avoid N+1 queries
from django.db.models import Count

people_with_counts = Person.objects.real().annotate(
    contribution_count=Count('contributions'),
    affiliation_count=Count('affiliations')
)
```

**Database Indexing**:

Already indexed, no action needed:
- `Person.email` (`unique=True`, plus the case-insensitive constraint)
- `Person.is_claimed` (`db_index=True` — the account-state filters and the admin's Claimed
  Status filter both read it)
- `Affiliation.type` (`db_index=True`)
- `Affiliation.is_primary` (via the partial unique constraint, one row per person)

**Not indexed** — `Person.is_active` (inherited from Django's `AbstractUser` unchanged) and
`Affiliation.end_date`. A query filtering on either alone scans; combine with an indexed field
(`Person.objects.real().active()`, or filter `Affiliation` by `type` first) where that matters
at scale.

Check what exists via:
```bash
poetry run python manage.py sqlmigrate contributors 0001
# Look for CREATE INDEX statements
```

**Caching Contributor Lookups**:

For frequently accessed profiles:
```python
from django.core.cache import cache

def get_person_profile(person_pk):
    cache_key = f"person_profile_{person_pk}"
    profile = cache.get(cache_key)
    if profile is None:
        person = Person.objects.select_related('primary_affiliation__organization').get(pk=person_pk)
        profile = {
            "name": person.name,
            "email": person.email,
            "affiliation": person.primary_affiliation().organization.name if person.primary_affiliation() else None,
        }
        cache.set(cache_key, profile, timeout=3600)  # 1 hour
    return profile
```

## Security Considerations

### Protecting Personal Data

**Email Privacy**:
- This app enforces no field-level visibility rule of any kind — nothing reads or checks
  `Contributor.config`, and there is no `email`-is-private-by-default behaviour. A portal that
  wants email addresses (or any other field) hidden from some viewers implements and enforces
  that itself, at whichever boundary — view, serializer, template — it chooses to check.
- Unclaimed persons (ghost/invited) commonly have `email=None` for a ghost record, which is
  safe to display by construction; an invited person's email is a real address and is exposed
  exactly like a claimed person's unless the portal hides it.

**GDPR Compliance**:
- Person records contain personal data
- Implement data export/deletion on request
- `config` is a general-purpose JSON store this app assigns no meaning to — build any visibility
  policy on top of it explicitly, rather than assuming one already exists

**Sample GDPR Export**:
```python
def export_person_data(person):
    """Export all personal data for GDPR compliance."""
    return {
        "personal_info": {
            "name": person.name,
            "email": person.email,
            "profile": person.profile,
        },
        "affiliations": [
            {
                "organization": aff.organization.name,
                "role": aff.get_type_display(),
                "start": str(aff.start_date),
                "end": str(aff.end_date) if aff.end_date else None,
            }
            for aff in person.affiliations.all()
        ],
        "contributions": [
            {
                "type": contrib.content_type.model,
                "id": contrib.object_id,
                "roles": [role.label for role in contrib.roles.all()],
            }
            for contrib in person.contributions.all()
        ],
    }
```

### Permission Boundaries

**Organization Ownership**:
- A current OWNER affiliation (no end date) has `manage_organization`
  permission
- The permission is derived from the affiliation at the moment it is
  checked, not stored — see [Ownership is derived, not stored](#ownership-is-derived-not-stored)
- A stored django-guardian grant of `manage_organization` is never
  honoured, whatever the database holds for it — the affiliation and
  superuser status are the only two sources

**Affiliation Writes**:
- Setting an affiliation's type to ADMIN or OWNER, and changing or deleting
  one that already carries either type, requires `manage_organization` on
  that organization — see [Managing Organization
  Memberships](#managing-organization-memberships)

**Person Admin Actions**:
- Merging two Person records, and generating a claim link, are
  superuser-only — see [Merging Duplicate Persons](#merging-duplicate-persons)
  and [Managing Unclaimed Profiles](managing-unclaimed-profiles.md)

**Admin Access**:
- Django staff/superuser can access all records
- Non-staff users see only records they have permission for
- Use django-guardian for object-level permissions other than
  `manage_organization`, which a stored guardian grant can never confer
  (see above)

## Related Documentation

- **Developer Guide**: [Contributors System Overview](../portal-development/contributors.md)
- **User Permissions**: [Managing Users and Permissions](managing_users_and_permissions.md)
- **Data Import**: Configure contributor attribution during data imports
