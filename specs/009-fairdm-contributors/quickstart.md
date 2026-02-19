# Quickstart: FairDM Contributors System

**Date**: 2026-02-18
**Feature**: 009-fairdm-contributors

This guide shows portal developers how to use the contributors system out of the box, including creating contributors, linking them to research outputs, querying contributions, and extending the transform system.

---

## 1. Basic Usage — Creating Contributors

### Create a claimed Person (active user account)

```python
from fairdm.contrib.contributors.models import Person

# Via the manager (preferred)
person = Person.objects.create_user(
    email="jane.doe@example.org",
    password="secure-password",
    first_name="Jane",
    last_name="Doe",
)

assert person.is_claimed is True
assert person.is_active is True
```

### Create an unclaimed Person (provenance-only)

```python
# For attribution when the real person hasn't registered yet
person = Person.objects.create_unclaimed(
    first_name="John",
    last_name="Smith",
)

assert person.is_claimed is False
assert person.email is None
assert person.is_active is False
```

### Create an Organization

```python
from fairdm.contrib.contributors.models import Organization

org = Organization.objects.create(
    name="Max Planck Institute for Chemistry",
    city="Mainz",
    country="DE",
)
```

### Create from external identifier

```python
# From ORCID — auto-populates name and affiliation from ORCID public API
person = Person.from_orcid("0000-0001-2345-6789")

# From ROR — auto-populates name, location, parent org from ROR API
org = Organization.from_ror("03yrm5c26")
```

---

## 2. Linking Contributors to Research Outputs

### Add a contributor to a project

```python
from fairdm.core.project.models import Project
from fairdm.contrib.contributors.models import Contribution

project = Project.objects.get(pk=1)

# Method 1: via the contributor instance
contribution = person.add_to(project, roles=["Creator", "DataCollector"])

# Method 2: via the Contribution class method
contribution = Contribution.add_to(
    contributor=person,
    obj=project,
    roles=["PrincipalInvestigator"],
    affiliation=org,  # optional: records affiliation at time of contribution
)
```

### Query contributions

```python
# All contributions for a specific entity
contribs = Contribution.objects.for_entity(project)

# All contributions by a specific person
contribs = Contribution.objects.by_contributor(person)

# Filter by role
creators = Contribution.objects.by_role("Creator")
```

---

## 3. Affiliations

### Record a person's affiliation with an organization

```python
from fairdm.contrib.contributors.models import Affiliation
from fairdm.utils.partialdate import PartialDate

# Full date precision
affiliation = Affiliation.objects.create(
    person=person,
    organization=org,
    type=1,  # MEMBER (verified)
    start_date=PartialDate(year=2022, month=1, day=15),
    is_primary=True,
)

# Year-only precision (when exact date unknown)
affiliation = Affiliation.objects.create(
    person=person,
    organization=org,
    type=0,  # PENDING (awaiting verification)
    start_date=PartialDate(year=1987),  # "some time in 1987"
)

# Query active affiliations (verified members only)
active = person.affiliations.filter(end_date__isnull=True, type__gte=1)

# End an affiliation
affiliation.end_date = PartialDate(year=2025, month=6)
affiliation.save()
```

### Affiliation verification workflow

```python
# User creates affiliation (self-declared)
affiliation = Affiliation.objects.create(
    person=new_user,
    organization=harvard,
    type=0,  # PENDING - not yet verified
    start_date=PartialDate(year=2023),
)

# Existing verified member or admin approves
if request.user.affiliations.filter(organization=harvard, type__gte=2).exists():
    # Admin or owner can verify
    affiliation.type = 1  # MEMBER
    affiliation.save()
    # Now new_user can access harvard organization resources
```

---

## 4. Organization Ownership

```python
from guardian.shortcuts import assign_perm, get_objects_for_user

# Ownership is managed via Affiliation.type
# Setting type=OWNER automatically grants manage_organization permission via lifecycle hooks
from fairdm.contrib.contributors.models import Affiliation

# Create owner affiliation (auto-grants manage_organization permission)
owner_aff = Affiliation.objects.create(
    person=person,
    organization=org,
    type=Affiliation.MembershipType.OWNER,  # Automatically grants manage_organization
)

# Check if a user can manage an organization
can_manage = person.has_perm("contributors.manage_organization", org)

# Get all organizations a user can manage
managed_orgs = get_objects_for_user(
    person, "contributors.manage_organization", klass=Organization
)

# Transfer ownership (via admin or direct Affiliation update)
# When you set a new OWNER, the old owner is automatically demoted to ADMIN
new_owner_aff = Affiliation.objects.create(
    person=another_person,
    organization=org,
    type=Affiliation.MembershipType.OWNER,  # Old owner auto-demoted via lifecycle hooks
)
```

---

## 5. Querying Contributors

### Using manager methods

```python
# All Person records (includes ghosts, claimed, unclaimed)
all_persons = Person.objects.all()

# Real people (excludes ghost/provenance-only records) - USE THIS FOR PORTAL QUERIES
real_people = Person.objects.real()

# Only claimed (active accounts)
claimed = Person.objects.claimed()

# Only unclaimed (provenance-only)
unclaimed = Person.objects.unclaimed()

# Ghost records (unclaimed, no email)
ghosts = Person.objects.ghost()

# Invited (unclaimed but has email)
invited = Person.objects.invited()

# Find co-contributors
collaborators = person.get_co_contributors(limit=10)

# Recent contributions
recent = person.get_recent_contributions(limit=5)
```

### Privacy-aware field access

```python
# Anonymous viewer — only public fields
visible = person.get_visible_fields(viewer=None)

# Authenticated viewer (staff sees everything)
visible = person.get_visible_fields(viewer=request.user)
```

---

## 6. Metadata Export

### Built-in formats

```python
# Export a single contributor
datacite_dict = person.to_datacite()
schema_org_dict = person.to_schema_org()
```

### Using the transform registry

```python
from fairdm.contrib.contributors.utils.transforms import transforms

# List available formats
formats = transforms.list()  # ["datacite", "schema.org", "csl-json", "orcid", "ror"]

# Export in a specific format
datacite = transforms.get("datacite").export(person)

# Export in all formats
all_exports = transforms.export_all(person)
```

### Creating a custom transform

```python
from fairdm.contrib.contributors.utils.transforms import BaseTransform, transforms, ImportResult

@transforms.register("my-custom-format")
class MyCustomTransform(BaseTransform):
    format_name = "my-custom-format"
    format_version = "1.0"
    content_type = "application/json"
    supports_persons = True
    supports_organizations = False

    def export(self, contributor):
        return {
            "full_name": contributor.name,
            "identifier": contributor.orcid().value if contributor.orcid() else None,
        }

    def import_data(self, data, instance=None, save=True):
        person = instance or Person()
        person.name = data["full_name"]
        if save:
            person.save()
        return ImportResult(
            instance=person,
            created=instance is None,
            unmapped_fields={k: v for k, v in data.items() if k not in ("full_name",)},
            warnings=[],
        )

    def supported_fields(self):
        return ["name", "identifiers"]
```

---

## 7. Template Tags

### In Django templates

```html
{% load contributor_tags %}

{# Filter contributions by role #}
{% for contrib in dataset.contributions.all|by_role:"Creator" %}
    <span>{{ contrib.contributor.name }}</span>
{% endfor %}

{# Check if a contribution has a specific role #}
{% if contribution|has_role:"PrincipalInvestigator" %}
    <strong>PI:</strong> {{ contribution.contributor.name }}
{% endif %}
```

---

## 8. External Sync (Background Tasks)

External sync happens automatically when identifiers are created or changed. No developer action is needed for basic sync.

### Manual sync (if needed)

```python
from fairdm.contrib.contributors.tasks import sync_contributor_identifier

# Sync a specific identifier
identifier = person.identifiers.get(type="ORCID")
sync_contributor_identifier.delay(identifier.pk)
```

### Celery Beat schedule (automatic)

The following periodic tasks are configured via Celery Beat:

| Task | Schedule | Purpose |
|------|----------|---------|
| `refresh_all_contributors` | Weekly (Sunday 03:00 UTC) | Refresh stale ORCID/ROR data |
| `detect_duplicate_contributors` | Monthly (1st, 04:00 UTC) | Find potential duplicate profiles |

---

## 9. Admin Integration

The contributors system provides admin classes out of the box:

- **PersonAdmin**: Unified view of auth account + contributor profile. Includes claim status filters, inline identifiers, inline affiliations.
- **OrganizationAdmin**: Organization profile with inline member list, sub-organization listing, ROR sync action.

No additional admin configuration is required for basic usage.

---

## 10. Common Patterns

### Check if a user contributed to an entity

```python
if person.has_contribution_to(dataset):
    # person is a contributor to this dataset
    ...
```

### Get a contributor's avatar URL

```python
from fairdm.contrib.contributors.utils.helpers import get_contributor_avatar

avatar_url = get_contributor_avatar(person, size=128)
```

### Check role in a view

```python
from fairdm.contrib.contributors.utils.helpers import current_user_has_role

if current_user_has_role(request, project, "PrincipalInvestigator"):
    # current user is PI on this project
    ...
```
