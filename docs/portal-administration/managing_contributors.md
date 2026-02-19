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

**Personal Information Tab**:
- Name fields (first_name, last_name, auto-generates display name)
- Email address (required for claimed accounts, NULL for unclaimed)
- Profile/biography
- Avatar image
- Keywords (research interests)

**Account Status Tab**:
- `is_claimed`: Boolean indicating if this person has claimed their account
- `is_active`: Standard Django active status
- `is_staff`: Django admin access
- `is_superuser`: Full system access

**Privacy Settings Tab**:
- `privacy_settings`: JSON field controlling field visibility
- Default: Email private for claimed users, all fields public for unclaimed

**Identifiers Tab**:
- ORCID (via ContributorIdentifier inline)
- Other external identifiers

**Permissions Tab**:
- Django groups and permissions
- Object-level permissions (via django-guardian)

### State Machine Overview

Person accounts follow this lifecycle:

1. **Ghost** (unclaimed, no email):
   - `is_claimed=False`, `email=None`, `is_active=False`
   - Created automatically during data import for attribution
   - Not searchable in portal member listings

2. **Invited** (unclaimed, has email):
   - `is_claimed=False`, `email` set, `is_active=False`
   - Invitation sent but not yet accepted
   - Invitation workflows in Feature 010 (not yet released)

3. **Claimed** (active account):
   - `is_claimed=True`, `is_active=True`
   - Full user account with authentication
   - Appears in portal member listings

4. **Banned** (deactivated):
   - `is_claimed=True`, `is_active=False`
   - Account disabled but data preserved

### Creating Person Records

**Creating Claimed User Accounts**:

1. Navigate to **Contributors > Persons > Add person**
2. Fill required fields:
   - Email address
   - First name
   - Last name
   - Password (or use "Set password" link after creation)
3. Check `is_active` (auto-checked for claimed accounts)
4. Save

The system automatically:
- Sets `is_claimed=True`
- Generates `name` from first_name + last_name
- Sets default privacy (email private)

**Creating Unclaimed Records** (for data attribution):

1. Navigate to **Contributors > Persons > Add person**
2. Fill name fields only (leave email NULL)
3. Leave `is_active` unchecked
4. Leave `is_claimed` unchecked
5. Save

Use for attributing data to people who haven't registered yet.

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

**ROR Synchronization**:
- Admin action: "Sync from ROR"
- Select organizations with ROR identifiers
- Triggers background sync task
- Updates organization metadata from ROR

**Ownership Transfer**:
- Admin action: "Transfer Ownership"
- Select single organization
- Redirects to organization page with instructions
- Ownership transfer via Affiliation type change

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
   - Type (PENDING, MEMBER, ADMIN, OWNER)
   - Start date (PartialDate: "2020", "2020-03", or "2020-03-15")
   - End date (optional, leave NULL for current affiliation)
   - Is primary (one per person)
5. Save

**Affiliation Type Meanings**:
- **PENDING**: Membership pending verification (no permissions)
- **MEMBER**: Regular member (read-only org access)
- **ADMIN**: Administrator (can manage memberships)
- **OWNER**: Owner (full control, automatically grants `manage_organization` permission)

**⚠️ Important**: Only ONE owner per organization. Setting a new owner automatically demotes the previous owner to ADMIN.

### Transferring Organization Ownership

To transfer ownership:

**Method 1: Via Admin Action**
1. Select organization in admin changelist
2. Choose "Transfer Ownership" action
3. Follow instructions to set new owner

**Method 2: Via Affiliation Type**
1. Edit the organization
2. Find the affiliation for the new owner
3. Change type to "OWNER"
4. Save
5. Old owner is automatically demoted to ADMIN

The `manage_organization` permission is automatically synced via lifecycle hooks.

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
   - **Approve**: Change type to MEMBER (or ADMIN if appropriate)
   - **Reject**: Delete affiliation or leave as PENDING with note

4. **Permission Sync**:
   - Lifecycle hooks automatically update object-level permissions
   - OWNER affiliations grant `manage_organization` permission

### Affiliation Admin List Filters

Use filters to find affiliations:
- **By organization**: Filter by organization name
- **By person**: Filter by person name
- **By type**: PENDING, MEMBER, ADMIN, OWNER
- **By status**: Current (end_date=NULL) vs Past (end_date set)
- **Primary only**: Show only is_primary=True

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

To sync without Celery (development only):

```python
from fairdm.contrib.contributors.utils.transforms import ORCIDTransform, RORTransform

# ORCID sync
person = Person.objects.get(email="example@example.com")
orcid_id = person.identifiers.filter(type="ORCID").first()
if orcid_id:
    # Fetch and apply ORCID data
    orcid_data = ORCIDTransform.fetch(orcid_id.value)
    internal_data = ORCIDTransform.to_internal(orcid_data)
    for key, value in internal_data.items():
        setattr(person, key, value)
    person.synced_data = orcid_data
    person.last_synced = timezone.now()
    person.save()

# ROR sync (similar pattern)
org = Organization.objects.get(pk=123)
ror_id = org.identifiers.filter(type="ROR").first()
if ror_id:
    ror_data = RORTransform.fetch(ror_id.value)
    internal_data = RORTransform.to_internal(ror_data)
    for key, value in internal_data.items():
        setattr(org, key, value)
    org.synced_data = ror_data
    org.last_synced = timezone.now()
    org.save()
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

### Bulk Privacy Settings Update

To update privacy settings for multiple unclaimed persons:

```python
from fairdm.contrib.contributors.models import Person

# Make all unclaimed persons' emails public (they're NULL anyway)
unclaimed_persons = Person.objects.unclaimed()
for person in unclaimed_persons:
    person.privacy_settings = {"email": "public"}
    person.save()
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

Ensure indexes exist on:
- `Person.email` (automatically indexed via unique=True)
- `Person.is_claimed`
- `Person.is_active`
- `Affiliation.type`
- `Affiliation.end_date`
- `Affiliation.is_primary`

Check via:
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
- By default, claimed user emails are private
- Unclaimed persons have NULL emails (safe to display)
- Use `person.get_visible_fields(viewer)` in templates

**GDPR Compliance**:
- Person records contain personal data
- Implement data export/deletion on request
- Use privacy_settings to let users control visibility

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
- Only one OWNER per organization
- OWNER has `manage_organization` permission
- Permission synced automatically via Affiliation lifecycle hooks

**Admin Access**:
- Django staff/superuser can access all records
- Non-staff users see only records they have permission for
- Use django-guardian for object-level permissions

## Related Documentation

- **Developer Guide**: [Contributors System Overview](../portal-development/contributors.md)
- **User Permissions**: [Managing Users and Permissions](managing_users_and_permissions.md)
- **Data Import**: Configure contributor attribution during data imports
