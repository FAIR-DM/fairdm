# Contributors System

The Contributors system provides flexible person and organization management for research portals, with built-in support for ORCID and ROR integration and derived organisation ownership.

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
    # email is None, is_active=True (so a later invitation can reach them), is_claimed=False
)

# Create a person directly with a password (does NOT set is_claimed - claiming
# is a workflow of its own, see Feature 010 below)
person = Person.objects.create_user(
    email="jane@example.com",
    first_name="Jane",
    last_name="Doe",
    password="secure_password",
    # is_active=True by default; password omitted entirely sets an unusable one
)
```

### State Machine

Every `Person` is in exactly one of four states, derived from `is_active`, `is_claimed` and
`email` rather than stored (decisions.md D8). `Person.account_state` returns the value, and
each state below has a matching `Person.objects` queryset method:

1. **Ghost**: Unclaimed, no email, no credentials (`is_claimed=False`, `email=None`) —
   `Person.objects.ghost()`
2. **Invited**: Has email but not claimed (`is_claimed=False`, `email` set) —
   `Person.objects.invited()`
3. **Claimed**: Active user account (`is_claimed=True`, `is_active=True`) —
   `Person.objects.claimed()`
4. **Inactive**: Deactivated account (`is_active=False`, whatever `is_claimed` holds — this
   takes precedence over every other state) — `Person.objects.inactive()`

```python
person.account_state  # one of AccountState.GHOST/INVITED/CLAIMED/INACTIVE
```

**Note**: Invitation and claiming workflows are implemented in Feature 010 (not yet released).

### Unified Manager Approach

The `Person` model uses Django's `objects` manager instead of a separate `contributors` manager.
Every method below (FR-041) is defined once on `PersonQuerySet` and reaches `Person.objects`
through `Manager.from_queryset` (FR-040), so `Person.objects.<method>()` and
`Person.objects.all().<method>()` always agree:

```python
from fairdm.contrib.contributors.models import Person

# ✅ CORRECT: Use objects manager
real_people = Person.objects.real()     # every Person except is_superuser=True and the anonymous
                                         # placeholder (email="AnonymousUser") - superusers and the
                                         # placeholder are excluded, nothing else is
active = Person.objects.active()        # every Person with is_active=True
claimed = Person.objects.claimed()      # every Person with is_claimed=True
unclaimed = Person.objects.unclaimed()  # every Person with is_claimed=False
ghosts = Person.objects.ghost()         # is_claimed=False and email is NULL: provenance-only records
invited = Person.objects.invited()      # is_claimed=False and email is set: invited but not yet claimed

# ❌ WRONG: Old API (removed)
# Person.contributors.claimed()
```

**Portal Queries**: Use `Person.objects.real()` to keep superusers and the anonymous placeholder out
of public-facing searches. It does not exclude ghost or invited profiles - combine it with
`unclaimed()`/`ghost()`/`invited()`/`claimed()` if a query also needs to say something about claim
status:

```python
# Portal members with a claimed account, excluding superusers and the placeholder
active_members = Person.objects.real().claimed().filter(
    affiliations__organization=my_org
)
```

### Configuration Store

Every `Contributor` (both `Person` and `Organization`) carries a general-purpose `config`
JSONField. This app does not define what belongs in it or enforce anything from its
contents — including field-level visibility, which nothing in this app reads or checks:

```python
person.config = {"anything": "this app does not define"}
person.save()

person.refresh_from_db()
assert person.config == {"anything": "this app does not define"}
```

It defaults to an empty dict. A portal that wants field-level visibility rules enforces them
itself, at whatever boundary (a view, a serializer, a template) it chooses to check — this app
grants no default behaviour to build on.

### ORCID Integration

```python
from fairdm.contrib.contributors.models import Person

# Create person from ORCID
person = Person.from_orcid("0000-0002-1825-0097")
# Synchronously creates Person, then schedules async ORCID sync

# Check ORCID authentication status
if person.orcid_is_authenticated:
    orcid_identifier = person.orcid()  # Method returns the ContributorIdentifier, or None
```

### Person Properties

```python
# Name handling
person.given          # First name (property)
person.family         # Last name (property)
person.name           # Full name (auto-generated from first_name + last_name)

# Name formatting
display_name = person.get_full_name_display(name_format="family_given")
# Supports: "given_family" (default, "John Doe"), "family_given" ("Doe, John"),
# "family_initial" ("Doe, J."), "initials_family" ("J. Doe")

# Affiliations
primary_aff = person.primary_affiliation()  # Returns Affiliation or None
current_affs = person.current_affiliations()  # QuerySet of active affiliations

# Contributions
recent = person.get_recent_contributions(limit=5)
project_contribs = person.get_contributions_by_type("project")
has_contrib = person.has_contribution_to(some_project)
co_contributors = person.get_co_contributors(limit=10)

# Add person to object - role names must be members of the fairdm-roles vocabulary
# (fairdm.core.vocabularies.FairDMRoles), e.g. "Creator" or "DataCollector"
person.add_to(my_project, roles=["Creator", "DataCollector"])
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

`manage_organization` is **derived, not stored** (decisions.md D13). No django-guardian row is
granted or revoked when an affiliation's type or end date changes — `OrganizationPermissionBackend`
answers `user.has_perm("contributors.manage_organization", org)` by checking, at the moment of
the call, whether the user holds a *current* `OWNER` affiliation on that organisation — one
whose `end_date` is not set:

```python
from fairdm.contrib.contributors.models import Affiliation, Organization

# Create organization
org = Organization.objects.create(name="University of Example")

# Add owner using Affiliation type
Affiliation.objects.create(
    person=owner_person,
    organization=org,
    type=Affiliation.MembershipType.OWNER,
)

owner_person.has_perm("contributors.manage_organization", org)  # True - derived, not stored
```

Editing the affiliation's `type` away from `OWNER`, or setting its `end_date`, is enough on its
own to remove the permission on the next check - nothing else needs to run. Deactivating the
account has the same effect: a person with `is_active=False` holds nothing, whatever their
affiliation says.

```python
owner_affiliation = org.affiliations.get(person=owner_person)
owner_affiliation.end_date = "2026"
owner_affiliation.save()

owner_person.has_perm("contributors.manage_organization", org)  # False
```

A stored django-guardian grant of `manage_organization` is never consulted for this permission,
even if one exists in the database. A current `OWNER` affiliation and superuser status are the
only two sources of this right.

Nothing stops two affiliations on the same organisation both being current `OWNER`. Use
`transfer_ownership()` when the intent is to hand the role to someone else rather than add them
alongside the incumbent:

```python
# Transfer ownership: demotes every *current* owner to ADMIN, promotes new_owner to OWNER,
# in one atomic operation. new_owner must hold a current MEMBER-or-higher affiliation and be
# an active, claimed Person - see "Ownership Transfer Validation" below.
org.transfer_ownership(new_owner)
```

**Affiliation Type State Machine:**
- `PENDING`: Pending verification
- `MEMBER`: Regular member
- `ADMIN`: Administrator (can manage memberships)
- `OWNER`: Owner (full control; holding a *current* `OWNER` affiliation is what
  `manage_organization` *means* - more than one current owner per organisation is possible,
  see above)

### Ownership Transfer Validation

`Organization.transfer_ownership(new_owner)` refuses `new_owner` unless they hold a *current*
affiliation (no `end_date`) of `MEMBER` standing or higher, and are an active, claimed `Person`.
Each failure raises `ValidationError` with its own message and changes nothing:

```python
# new_owner holds no affiliation on org at all
org.transfer_ownership(stranger)
# ValidationError: "<stranger> is not a member of <org>."

# new_owner's affiliation has ended
org.transfer_ownership(former_member)
# ValidationError: "<former_member>'s affiliation with <org> has ended."

# new_owner is still PENDING verification
org.transfer_ownership(pending_affiliate)
# ValidationError: "<pending_affiliate>'s affiliation with <org> is still pending verification."

# new_owner has not claimed their account
org.transfer_ownership(unclaimed_person)
# ValidationError: "<unclaimed_person> has not claimed their account."

# new_owner's account is deactivated
org.transfer_ownership(deactivated_person)
# ValidationError: "<deactivated_person>'s account is deactivated."
```

Writing `ADMIN` or `OWNER` directly through the ORM, as in the examples above, is unrestricted.
The Django admin's affiliation forms - the standalone Affiliation admin and both inlines - gate
the same write behind `manage_organization`: setting a type to `ADMIN` or `OWNER`, or changing
or deleting an affiliation that already carries one of those types, requires the acting user to
already hold `manage_organization` on that organisation. See [Managing Organization Memberships
in Managing Contributors](../portal-administration/managing_contributors.md#managing-organization-memberships)
for the admin-facing behaviour.

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

An `Affiliation` links a `Person` to an `Organization` with a period and a membership type
(pending, member, admin or owner). A membership is **current** when it has no `end_date` -
that is the only rule; a membership with an `end_date` is past, regardless of how far in the
future that date is.

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

A person cannot be a member of the same organisation twice. Attempting to create a second
membership is refused with a readable message at validation, and by a database constraint if
validation is bypassed:

```python
duplicate = Affiliation(person=person, organization=org)
duplicate.full_clean()
# ValidationError: {'organization': ['<person> is already a member of <org>.']}
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

Only one affiliation per person can be marked `is_primary=True`. Setting a new primary demotes
the person's existing primary in the same transaction - the demotion and the save happen
together or not at all - and a partial database constraint refuses two primary rows for the
same person even for a write that bypasses `Affiliation.save()`, such as a queryset `.update()`.

```python
# Setting a new primary automatically unsets the old one
Affiliation.objects.create(
    person=person,
    organization=new_org,
    is_primary=True  # Old primary is automatically set to False
)
```

The primary affiliation is more than a label: `Contribution.set_default_affiliation` reads it
to fill in the crediting organisation whenever a person is credited without one being given
explicitly (`fairdm/contrib/contributors/models.py:1335`).

### Worked example: a person moving between two institutions

A researcher joins a university in 2018, later moves to a research institute in 2022, and the
institute affiliation becomes their primary one for citation:

```python
university = Organization.objects.get(name="Example University")
institute = Organization.objects.get(name="Example Research Institute")

# Original affiliation: full precision, now ended
university_membership = Affiliation.objects.create(
    person=researcher,
    organization=university,
    type=Affiliation.MembershipType.MEMBER,
    start_date="2018-09-01",
    end_date="2022-01-31",
)

# Current affiliation: year-month precision, no end date, marked primary
institute_membership = Affiliation.objects.create(
    person=researcher,
    organization=institute,
    type=Affiliation.MembershipType.MEMBER,
    start_date="2022-02",
    is_primary=True,
)

researcher.affiliations.current()   # [institute_membership]
researcher.affiliations.past()      # [university_membership]
researcher.affiliations.primary()   # institute_membership
```

## Contribution Model

### One Credit Per Contributor Per Object

A `Contribution` links a contributor (person or organisation) to a project, dataset,
sample or measurement through Django's `GenericForeignKey`. There is exactly one
`Contribution` row per contributor per object - a named `UniqueConstraint` refuses a
second row for the same pairing at the database level, and `Contribution.clean()`
refuses it too, with a matching message, so a form validating before save is refused the
same way a raw duplicate insert would be (FR-031).

Crediting the same contributor again under a further role does not create a second row -
the role **accumulates** on the existing credit, so a person who both collected and
analysed a dataset appears once, carrying both roles:

```python
from fairdm.contrib.contributors.models import Contribution

# Contributor.add_to() and the Contribution.add_to() classmethod are two of the three
# entry points, and both accumulate roles rather than replace them.
contribution = person.add_to(my_project, roles=["DataCollector"])
same_contribution = person.add_to(my_project, roles=["Researcher"])
assert contribution.pk == same_contribution.pk
assert {r.name for r in same_contribution.roles.all()} == {"DataCollector", "Researcher"}

# The classmethod form also accepts the crediting organisation explicitly.
Contribution.add_to(person, my_project, roles=["ProjectLeader"], affiliation=some_org)
```

The third is `add_contributor()`, which every project, dataset, sample and measurement
inherits and which the portal's own creation views use to credit the person who made the
record. It takes the roles under a different keyword and accumulates them the same way:

```python
contribution = my_dataset.add_contributor(person, with_roles=["DataCollector"])
same_contribution = my_dataset.add_contributor(person, with_roles=["Researcher"])
assert contribution.pk == same_contribution.pk
assert {r.name for r in same_contribution.roles.all()} == {"DataCollector", "Researcher"}
```

### Roles

Roles are drawn from the framework's controlled roles vocabulary (`fairdm-roles`,
`fairdm.core.vocabularies.FairDMRoles`). A role from any other vocabulary is refused
at the point it is written: `roles.add()` and `roles.set()` both raise
`ValidationError` immediately for an off-vocabulary concept, and neither writes it.
This is enforced by an `m2m_changed` receiver on `Contribution.roles.through`
(FR-032) rather than by `Contribution.clean()` - `full_clean()` never validates
many-to-many data, so nothing that writes a role needs to call it for the rule to
hold.

```python
from research_vocabs.models import Concept

role = Concept.objects.get(vocabulary__name="fairdm-roles", name="DataCollector")
contribution.roles.add(role)  # accepted

other_vocabulary_role = Concept.objects.get(vocabulary__name="not-fairdm-roles")
contribution.roles.add(other_vocabulary_role)  # raises ValidationError; not written

# Query credits by role (FR-042): every Contribution whose roles include the
# named Concept - defined once on ContributionQuerySet, reachable from both
# Contribution.objects and Contribution.objects.all() (FR-040)
data_collector_credits = Contribution.objects.by_role("DataCollector")
```

### Crediting Organisation Default

Where a person is credited and no organisation is named on the credit, their primary
membership's organisation is recorded against it automatically (FR-033):

```python
contribution = person.add_to(my_project)
contribution.affiliation  # person's primary Affiliation's organisation, if any
```

### Reporting a Contributor's Credits

```python
# What a contributor is credited on (FR-034) - each resolves through the concrete
# type a credit actually names, not the polymorphic base, which can never be
# instantiated directly for Sample and Measurement.
person.projects
person.datasets
person.samples
person.measurements

# Counts by kind, in a bounded number of queries
person.get_credit_counts()
# {'projects': 2, 'datasets': 1}

# The contributors credited alongside this one, most frequent first (FR-035)
person.get_co_contributors(limit=5)
```

### Deleting a Credit Withdraws Rights - Creating One Grants None

Deleting a person's credit on an object withdraws every object-level right that person
holds over that object, whether the credit is deleted on the instance or in bulk through
a queryset (FR-036). **Creating a credit grants nothing** - crediting someone confers no
permission by itself, so there is no corresponding grant to mirror the withdrawal. A
portal that wants a credited contributor to also gain a right over the object must grant
it separately.

Deleting the credited object itself is the one case where nothing is withdrawn: the
project or dataset row is gone before its credits are removed, so there is no object left
to hold a right over. Rights recorded against a deleted object are cleared by
django-guardian's `clean_orphan_obj_perms` management command, which is worth scheduling
on any portal that deletes records regularly.

### Supported Content Types

Contributions use Django's GenericForeignKey to link to:
- `fairdm.core.Project`
- `fairdm.core.Dataset`
- `fairdm.core.Sample`
- `fairdm.core.Measurement`

## Transform API

The transform classes in `fairdm.contrib.contributors.utils.transforms` provide bidirectional
data conversion between `Contributor` instances and external formats. Every transform is an
instance, not a namespace of classmethods - `BaseTransform.export()` and
`BaseTransform.import_data()` are the whole contract:

### BaseTransform Interface

```python
from fairdm.contrib.contributors.models import Contributor
from fairdm.contrib.contributors.utils.transforms import BaseTransform


class MyTransform(BaseTransform):
    """Custom transformer for MyFormat."""

    def export(self, contributor: Contributor) -> dict:
        """Convert a Contributor instance to external format."""
        return {
            "fullName": contributor.name,
            "emailAddress": getattr(contributor, "email", None),
            # ... map fields
        }

    def import_data(
        self, data: dict, instance: Contributor | None = None, save: bool = True
    ) -> Contributor:
        """Convert external format data into a Contributor instance."""
        contributor = instance or Contributor()
        contributor.name = data["fullName"]
        if save:
            contributor.save()
        return contributor
```

`update_or_create()` and `fetch_from_api()` are not part of `BaseTransform` itself - they exist
only on `ORCIDTransform` and `RORTransform`, the two transforms that talk to a live external API
(below).

### Built-in Transforms

#### DataCite Transform

```python
from fairdm.contrib.contributors.utils.transforms import DataCiteTransform

# Export to DataCite Contributor schema JSON
datacite_json = DataCiteTransform().export(person)

# Import from DataCite format
person = DataCiteTransform().import_data(datacite_json)
```

#### Schema.org Transform

```python
from fairdm.contrib.contributors.utils.transforms import SchemaOrgTransform

# Export to Schema.org Person/Organization JSON-LD
schema_org_json = SchemaOrgTransform().export(person)

# Import from Schema.org format
person = SchemaOrgTransform().import_data(schema_org_json)
```

#### ORCID Transform

```python
from fairdm.contrib.contributors.utils.transforms import ORCIDTransform

# Fetches the ORCID API and creates/updates a Person, returning (person, created)
person, created = ORCIDTransform.update_or_create("0000-0002-1825-0097")

# Person.from_orcid() wraps this for the common case (see "ORCID Integration" above)
```

#### ROR Transform

```python
from fairdm.contrib.contributors.utils.transforms import RORTransform

# Fetches the ROR API and creates/updates an Organization, returning (org, created)
org, created = RORTransform.update_or_create("https://ror.org/04aj4c181")

# Organization.from_ror() wraps this for the common case (see "ROR Integration" above)
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
| `Person.objects.real()` | Exclude superusers and the anonymous placeholder | **Portal queries (RECOMMENDED)** |
| `Person.objects.active()` | `is_active=True` accounts | Excluding deactivated accounts |
| `Person.objects.claimed()` | `is_claimed=True` accounts | User listings |
| `Person.objects.unclaimed()` | `is_claimed=False` accounts | Data import cleanup |
| `Person.objects.ghost()` | Unclaimed, no email | Orphaned records |
| `Person.objects.invited()` | Unclaimed, has email | Pending invitations |
| `Person.objects.inactive()` | `is_active=False` accounts | Excluding deactivated accounts, highest precedence (D8) |

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

# Get contributors by role - concepts are looked up by the vocabulary's name
# (research_vocabs.vocabularies.VocabularyBuilder subclasses aren't themselves
# passed as a `vocabulary=` value), and by the concept's own `name`, not a `label`.
from research_vocabs.models import Concept

creator_role = Concept.objects.get(vocabulary__name="fairdm-roles", name="Creator")
creators = Contribution.objects.filter(
    content_type=ContentType.objects.get_for_model(Project),
    object_id=project.pk,
    roles=creator_role
).select_related('contributor')

# Or, equivalently, using ContributionQuerySet.by_role() (FR-042):
creators = Contribution.objects.for_entity(project).by_role("Creator")
```

## Next Steps

- **Admin Guide**: See [Managing Contributors](../portal-administration/managing_contributors.md) for admin workflows
- **Registry Integration**: See [Using the Registry](using_the_registry.md) for registering custom Person/Organization fields
- **Testing**: See [Testing Portal Projects](testing-portal-projects.md) for contributor-related test patterns
