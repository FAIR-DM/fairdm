# Contributors System

The Contributors system provides flexible person and organization management for research portals, with built-in support for ORCID and ROR integration, ownership workflows, and privacy controls.

## Overview

The contributors app (`fairdm.contrib.contributors`) provides four core models:

- **Person**: Individual contributors (AUTH_USER_MODEL for authentication)
- **Organization**: Institutional contributors with ROR integration
- **Affiliation**: Person-to-Organization relationships with role management
- **Contribution**: Links contributors to research objects (Projects, Datasets, Samples, Measurements)

## Person Model

### AUTH_USER_MODEL Integration

`Person` extends Django's `AbstractUser` and serves as the authentication model for your portal:

```python
# config/settings.py
AUTH_USER_MODEL = "contributors.Person"
```

### Account States and is_claimed

The `is_claimed` BooleanField tracks whether a person has claimed their account:

```python
from fairdm.contrib.contributors.models import Person

# Create unclaimed person (provenance-only record)
person = Person.objects.create_unclaimed(
    first_name="Jane",
    last_name="Doe",
    # email is None, is_active=False, is_claimed=False
)

# Claimed person (full user account)
person = Person.objects.create_user(
    email="jane@example.com",
    first_name="Jane",
    last_name="Doe",
    password="secure_password",
    # is_active=True, is_claimed=True automatically set
)
```

### State Machine

Person accounts follow this state machine:

1. **Ghost**: Unclaimed, no email, no credentials (`is_claimed=False`, `email=None`)
2. **Invited**: Has email but not claimed (`is_claimed=False`, `email` set)
3. **Claimed**: Active user account (`is_claimed=True`, `is_active=True`)
4. **Banned**: Deactivated account (`is_claimed=True`, `is_active=False`)

**Note**: Invitation and claiming workflows are implemented in Feature 010 (not yet released).

### Unified Manager Approach

The `Person` model uses Django's `objects` manager instead of a separate `contributors` manager:

```python
from fairdm.contrib.contributors.models import Person

# ✅ CORRECT: Use objects manager
real_people = Person.objects.real()  # Exclude ghosts (unclaimed provenance records)
claimed = Person.objects.claimed()    # Active claimed accounts
unclaimed = Person.objects.unclaimed()  # Provenance-only records
ghosts = Person.objects.ghost()       # Unclaimed with no email
invited = Person.objects.invited()    # Unclaimed with email

# ❌ WRONG: Old API (removed)
# Person.contributors.claimed()
```

**Portal Queries**: Always use `Person.objects.real()` to exclude ghost/provenance-only records from public searches:

```python
# Search for active portal members
active_members = Person.objects.real().filter(
    affiliations__organization=my_org
)
```

### Privacy Controls

The `privacy_settings` JSONField controls field visibility:

```python
person.privacy_settings = {
    "email": "private",      # Options: "public", "authenticated", "private"
    "phone": "authenticated",  # Visible to logged-in users
    "location": "public"      # Visible to everyone
}

# Get visible fields for a viewer
visible = person.get_visible_fields(viewer=request.user)
# Returns dict with only fields viewer can see
```

**Default Behavior:**
- **Unclaimed persons** (ghost/invited): All fields public (email is NULL anyway)
- **Claimed persons**: Email private by default, other fields public

### ORCID Integration

```python
from fairdm.contrib.contributors.models import Person

# Create person from ORCID
person = Person.from_orcid("0000-0002-1825-0097")
# Synchronously creates Person, then schedules async ORCID sync

# Check ORCID authentication status
if person.orcid_is_authenticated:
    orcid_id = person.orcid  # Property returns ORCID identifier
```

### Person Properties

```python
# Name handling
person.given          # First name (property)
person.family         # Last name (property)
person.name           # Full name (auto-generated from first_name + last_name)

# Name formatting
display_name = person.get_full_name_display(name_format="family_given")
# Supports: "given_family", "family_given", "family_given_comma"

# Affiliations
primary_aff = person.primary_affiliation()  # Returns Affiliation or None
current_affs = person.current_affiliations()  # QuerySet of active affiliations

# Contributions
recent = person.get_recent_contributions(limit=5)
project_contribs = person.get_contributions_by_type("project")
has_contrib = person.has_contribution_to(some_project)
co_contributors = person.get_co_contributors(limit=10)

# Add person to object
person.add_to(my_project, roles=["Author", "Data Collector"])
```

## Organization Model

### ROR Integration

```python
from fairdm.contrib.contributors.models import Organization

# Create from ROR ID
org = Organization.from_ror("https://ror.org/04aj4c181")
# Synchronously creates Organization, then schedules async ROR sync

# Check ROR identifier
ror_id = org.identifiers.filter(type="ROR").first()
```

### Organization Ownership

Organizations use the `manage_organization` permission (via django-guardian) with a role-based system:

```python
from fairdm.contrib.contributors.models import Affiliation, Organization

# Create organization
org = Organization.objects.create(name="University of Example")

# Add owner using Affiliation type
Affiliation.objects.create(
    person=owner_person,
    organization=org,
    type=Affiliation.MembershipType.OWNER  # Automatically grants manage_organization
)

# Ownership transfer (demotes current owner to ADMIN)
from fairdm.contrib.contributors.views.organization import transfer_ownership
# See admin interface for ownership transfer UI
```

**Affiliation Type State Machine:**
- `PENDING`: Pending verification
- `MEMBER`: Regular member
- `ADMIN`: Administrator (can manage memberships)
- `OWNER`: Owner (full control, only one per organization)

Lifecycle hooks automatically sync the `manage_organization` permission when affiliation type changes.

### Organization Properties

```python
# Members
memberships = org.get_memberships()  # All affiliations with person prefetched
owner = org.owner()  # Returns Person or None

# GeoJSON export (if location set)
geojson = org.as_geojson()
```

## Affiliation Model

### Time-Bound Relationships

```python
from fairdm.contrib.contributors.models import Affiliation
from fairdm.db.fields import PartialDateField

# Create affiliation with partial dates
Affiliation.objects.create(
    person=person,
    organization=org,
    start_date="2020",          # Year only
    end_date="2023-06",         # Year-month
    type=Affiliation.MembershipType.MEMBER
)

# Query by time status
current = person.affiliations.current()  # end_date=None
past = person.affiliations.past()        # end_date IS NOT NULL
primary = person.affiliations.primary()  # is_primary=True
```

### PartialDateField

The `start_date` and `end_date` fields use `PartialDateField` supporting three precision levels:

```python
# Year only
affiliation.start_date = "2020"

# Year-month
affiliation.start_date = "2020-03"

# Full date
affiliation.start_date = "2020-03-15"
```

### Primary Affiliation Constraint

Only one affiliation per person can be marked `is_primary=True`:

```python
# Setting a new primary automatically unsets the old one
Affiliation.objects.create(
    person=person,
    organization=new_org,
    is_primary=True  # Old primary is automatically set to False
)
```

## Contribution Model

### Linking Contributors to Research Objects

```python
from fairdm.contrib.contributors.models import Contribution
from research_vocabs.models import Concept
from fairdm.core.vocabularies import FairDMRoles

# Create contribution
contribution = Contribution.objects.create(
    contributor=person,
    content_object=my_project,  # GenericForeignKey supports any model
)

# Add roles from FairDMRoles vocabulary
author_role = Concept.objects.get(vocabulary=FairDMRoles, label="Author")
contribution.roles.add(author_role)

# Query contributions
project_contributions = Contribution.objects.filter(
    content_type=ContentType.objects.get_for_model(Project),
    object_id=my_project.pk
)

# Reverse query
person_projects = person.contributions.filter(
    content_type=ContentType.objects.get_for_model(Project)
)
```

### Supported Content Types

Contributions use Django's GenericForeignKey to link to:
- `fairdm.core.Project`
- `fairdm.core.Dataset`
- `fairdm.core.Sample`
- `fairdm.core.Measurement`

## TransformRegistry API

The Transform system provides bidirectional data conversion between FairDM models and external formats.

### BaseTransform Interface

```python
from fairdm.contrib.contributors.utils.transforms import BaseTransform

class MyTransform(BaseTransform):
    """Custom transformer for MyFormat."""
    
    @classmethod
    def to_internal(cls, external_data: dict) -> dict:
        """Convert external format to FairDM internal format."""
        return {
            "name": external_data["fullName"],
            "email": external_data["emailAddress"],
            # ... map fields
        }
    
    @classmethod
    def to_external(cls, person: Person) -> dict:
        """Convert Person to external format."""
        return {
            "fullName": person.name,
            "emailAddress": person.email,
            # ... map fields
        }
    
    @classmethod
    def update_or_create(cls, external_id: str, commit=True) -> Person:
        """Fetch external data and create/update Person."""
        # Fetch from external API
        data = fetch_my_api(external_id)
        internal = cls.to_internal(data)
        
        person, created = Person.objects.update_or_create(
            # ... matching logic
            defaults=internal
        )
        return person
```

### Built-in Transforms

#### DataCite Transform

```python
from fairdm.contrib.contributors.utils.transforms import DataCiteTransform

# Export to DataCite format
datacite_json = DataCiteTransform.to_external(person)
# Returns DataCite Contributor schema JSON

# Import from DataCite
internal_data = DataCiteTransform.to_internal(datacite_json)
```

#### Schema.org Transform

```python
from fairdm.contrib.contributors.utils.transforms import SchemaOrgTransform

# Export to Schema.org Person
schema_org_json = SchemaOrgTransform.to_external(person)
# Returns JSON-LD with @context

# Import from Schema.org
internal_data = SchemaOrgTransform.to_internal(schema_org_json)
```

#### ORCID Transform

```python
from fairdm.contrib.contributors.utils.transforms import ORCIDTransform

# Import from ORCID
person = ORCIDTransform.update_or_create("0000-0002-1825-0097")
# Fetches ORCID API and creates/updates Person
```

#### ROR Transform

```python
from fairdm.contrib.contributors.utils.transforms import RORTransform

# Import from ROR
org = RORTransform.update_or_create("https://ror.org/04aj4c181")
# Fetches ROR API and creates/updates Organization
```

## Important Recommendations

### Separate Superuser and Person Accounts

**⚠️ CRITICAL**: Portal developers should maintain TWO separate accounts:

1. **Superuser Account** (for development/admin):
   ```bash
   poetry run python manage.py createsuperuser
   # Email: admin@localhost
   # Used only for Django admin access
   ```

2. **Person Account** (for testing portal features):
   ```python
   # Create via portal registration or:
   person = Person.objects.create_user(
       email="developer@example.com",
       first_name="Dev",
       last_name="User",
       password="password"
   )
   ```

**Why?** The superuser account has elevated permissions that bypass normal portal workflows. Testing with a regular Person account ensures you experience the portal as real users do.

### Manager Method Summary

Use these manager methods for querying Person records:

| Method | Purpose | Use Case |
|--------|---------|----------|
| `Person.objects.all()` | All Person records | Admin/data migration |
| `Person.objects.real()` | Exclude ghosts | **Portal queries (RECOMMENDED)** |
| `Person.objects.claimed()` | Active user accounts | User listings |
| `Person.objects.unclaimed()` | Provenance records | Data import cleanup |
| `Person.objects.ghost()` | Unclaimed, no email | Orphaned records |
| `Person.objects.invited()` | Unclaimed, has email | Pending invitations |

## Migration Guide

### For Existing Portals

If migrating to Feature 009 from an older FairDM version:

1. **Update AUTH_USER_MODEL** in `config/settings.py`:
   ```python
   AUTH_USER_MODEL = "contributors.Person"
   ```

2. **Run migrations**:
   ```bash
   poetry run python manage.py migrate contributors
   ```

3. **Update manager calls**:
   - Replace `Person.contributors.*` with `Person.objects.*`
   - Use `Person.objects.real()` for portal queries

4. **Update templates**:
   - `request.user` is now a `Person` instance
   - Access user properties via `request.user.name`, `request.user.email`, etc.

### OrganizationMembership → Affiliation

If your portal used the old `OrganizationMembership` model:

```python
# Old API (removed)
# membership = OrganizationMembership.objects.create(...)

# New API
affiliation = Affiliation.objects.create(
    person=person,
    organization=org,
    type=Affiliation.MembershipType.MEMBER,
    is_primary=True
)
```

## Code Examples

### Complete Person Creation Workflow

```python
from fairdm.contrib.contributors.models import Person, Organization, Affiliation
from django.contrib.auth.hashers import make_password

# Create unclaimed person for data attribution
unclaimed_person = Person.objects.create_unclaimed(
    first_name="Jane",
    last_name="Researcher",
)

# Later, invite them (Feature 010)
unclaimed_person.email = "jane@example.com"
unclaimed_person.save()
# Send invitation email...

# When they claim account
unclaimed_person.is_claimed = True
unclaimed_person.is_active = True
unclaimed_person.set_password("their_password")
unclaimed_person.save()

# Add organization affiliation
university = Organization.objects.create(name="Example University")
Affiliation.objects.create(
    person=unclaimed_person,
    organization=university,
    type=Affiliation.MembershipType.MEMBER,
    start_date="2020",
    is_primary=True
)
```

### Querying Contributors for a Project

```python
from fairdm.core.models import Project
from fairdm.contrib.contributors.models import Contribution
from django.contrib.contenttypes.models import ContentType

project = Project.objects.get(pk=1)

# Get all contributors
contributions = Contribution.objects.filter(
    content_type=ContentType.objects.get_for_model(Project),
    object_id=project.pk
).select_related('contributor')

# Get contributors by role
from research_vocabs.models import Concept
from fairdm.core.vocabularies import FairDMRoles

author_role = Concept.objects.get(vocabulary=FairDMRoles, label="Author")
authors = Contribution.objects.filter(
    content_type=ContentType.objects.get_for_model(Project),
    object_id=project.pk,
    roles=author_role
).select_related('contributor')
```

### Privacy-Aware Person Display

```python
def show_person_profile(request, person_pk):
    person = Person.objects.get(pk=person_pk)
    
    # Get fields visible to current viewer
    visible_data = person.get_visible_fields(viewer=request.user)
    
    context = {
        "person": person,
        "visible_data": visible_data,
        "can_see_email": "email" in visible_data,
    }
    return render(request, "person_profile.html", context)
```

## Next Steps

- **Admin Guide**: See [Managing Contributors](../portal-administration/managing_contributors.md) for admin workflows
- **Registry Integration**: See [Using the Registry](using_the_registry.md) for registering custom Person/Organization fields
- **Testing**: See [Testing Portal Projects](testing-portal-projects.md) for contributor-related test patterns
