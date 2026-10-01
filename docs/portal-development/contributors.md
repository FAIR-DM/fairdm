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

**Note**: Claiming workflows (ORCID, email confirmation, and admin-generated token) are
implemented — see `fairdm.contrib.contributors.services.claiming`. Self-service signup can be
closed entirely via `FAIRDM_INVITATION_ONLY_SIGNUP`; there is no separate invitation-email
workflow.

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
primary_org = person.primary_organization  # That affiliation's Organization, or None
current_affs = person.current_affiliations()  # QuerySet of active affiliations

# Display
person.get_initials()  # "AL" for Ada Lovelace: given and family initials
person.portal_roles  # Labels of the portal roles held, e.g. ["Data Curator"]; [] when inactive

# Contributions
recent = person.get_recent_contributions(limit=5)
project_contribs = person.get_contributions_by_type("project")
has_contrib = person.has_contribution_to(some_project)
collaborators = person.get_collaborators(limit=10)

# Add person to object - role names must be members of the fairdm-roles vocabulary
# (fairdm.core.vocabularies.FairDMRoles), e.g. "Creator" or "DataCollector"
person.add_to(my_project, roles=["Creator", "DataCollector"])
```

`primary_affiliation()`, `primary_organization`, `portal_roles`, `orcid_is_authenticated` and
`get_default_identifier()` read from prefetched relations when there are any. A page listing many
people fetches them with `Person.objects.for_cards()`, which prefetches identifiers, sign-in
accounts, affiliations with their organizations, and groups, so reading those costs no query per
person:

```python
people = Person.objects.real().for_cards()
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

An organization's page reads who belongs to it and where it sits from four more methods:

| Method | What it returns |
| --- | --- |
| `get_current_memberships()` | The affiliations of its members: verified and not ended, with the person loaded. The owner comes first, then the administrators, then the other members, each group by name. |
| `has_member(user)` | `True` when the user has a current affiliation of type member or above. Pending and ended affiliations do not count, and a visitor is never a member. |
| `is_managed_by(user)` | `True` when the user has a current affiliation of type administrator or owner. A portal role does not count. |
| `is_editable_by(user)` | `True` when the user is active and `is_managed_by(user)` holds. It decides who may open the [editing page](#editing-a-profile). |
| `get_descendant_ids()` | The primary keys of every organization beneath this one, at any depth. |
| `get_hierarchy()` | `parent` (or `None`), `siblings` (the parent's sub-organizations by name, this one included, empty without a parent) and `children` (its direct sub-organizations by name). |

```python
for affiliation in org.get_current_memberships():
    print(affiliation.person, affiliation.get_type_display())

org.is_managed_by(request.user)
org.get_hierarchy()["children"]
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
person.get_collaborators(limit=5)
```

### What a profile may show

A contributor's overview page names only public work, and the methods below decide what that is.
`get_public_projects()` and `get_public_datasets()` are the one source of what a profile lists and
counts. The overview's figures and cards and the Projects and Datasets tabs all read them, so a
figure always equals the number of entries behind its link. A subclass that has more work to show
overrides both, and `Organization` does.

```python
person.get_public_projects()  # public projects the person is credited on
person.get_public_datasets()  # public datasets they are credited on, outside private projects
```

An organization's two sources add what it owns. `Organization.get_public_projects()` returns the
public projects it owns and those it is credited on, and `get_public_datasets()` returns the public
datasets it is credited on and those inside the projects it owns, whether or not it is credited on
them. Each is one queryset with nothing in it twice, and what the organization's members are
credited on under their own names is not part of either.

```python
org.get_public_projects()  # public projects it owns or is credited on
org.get_public_datasets()  # public datasets it is credited on or that sit in its projects
```

A private project hides everything beneath it, so a public dataset inside a private project is
left out. `Dataset.objects.get_visible()` holds that rule, as `Project.objects.get_visible()` does
for projects. Neither depends on who is asking: a project's member and the person themselves see
the same lists as a visitor.

`get_visible_contributions(user)` returns the person's credits on records a profile may name,
newest first. Projects and datasets are those from the two methods above. A sample or measurement
counts when `visible_to(user)` lets the user see it and its dataset's project, if it has one, is
public. Each credit carries `kind`, which is `project`, `dataset`, `sample` or `measurement`.
Projects and datasets also carry `record`. Samples and measurements are checked by id and never
loaded, because no card lists them.

```python
contributions = person.get_visible_contributions(request.user)
projects = [c.record for c in contributions if c.kind == "project"]
```

The role counts and the collaborators are worked out from those credits, so a role or a
collaborator known only through a private record never appears:

```python
person.get_role_counts(contributions)
# Counter({"Creator": 2, "Data Collector": 1})

person.get_collaborators(contributions=contributions)
# Contributors credited on the same records, most frequent first and ties by name.
# Each carries collaboration_count.
```

The rest of what a profile reads from a contributor:

| Member | What it returns |
| --- | --- |
| `get_links_display()` | One `{"url", "host"}` entry per recorded link, the host being the site it points at. |
| `get_language_names()` | The names of the recorded languages in the active language. A code Django does not know is kept as written. |
| `to_public_schema_org()` | The Schema.org description for the page head. It has no email address. A person's `affiliation` is kept only when it is the verified, current primary affiliation the page header shows. |
| `Person.get_profile_completeness()` | One flag for each of `image`, `orcid`, `profile`, `primary_affiliation` and `links`. `orcid` is true only when the person has signed in with ORCID, and `primary_affiliation` only for a verified primary affiliation that has not ended. |
| `Organization.get_record_completeness()` | One flag for each of `ror`, `image`, `type`, `location`, `profile` and `links`. `ror` needs an identifier of type ROR, and `location` needs both a city and a country. |
| `Person.get_location_display()` | The city and country of the organization the header names as primary, or `None` without a verified primary affiliation that has not ended. |
| `Person.member_since` | When the account was created, or `None` for a profile nobody has claimed. |
| `Person.get_affiliation_history()` | `current` (verified affiliations that have not ended, the primary one first and the rest by organization name) and `past` (most recently ended first). Pending affiliations are left out. |
| `Affiliation.start_display`, `Affiliation.end_display` | The date as precisely as it was recorded: a day, a month and year, or a year. An empty string when not recorded. |
| `ContributorIdentifier.resolver_url` | The address the identifier resolves to, or `None` for a type with no resolver. |

```python
history = person.get_affiliation_history()
for affiliation in history["current"]:
    print(affiliation.organization, affiliation.start_display)
```

### Profile helpers

`fairdm.contrib.contributors.profiles` holds the pure functions behind a profile page. None of them
reads the database or a request, so each takes plain values.

| Function | What it does |
| --- | --- |
| `link_host(url)` | The host of a link without a leading `www.`, or the link as written when it has no host. |
| `language_names(codes)` | One name per ISO 639-1 code, in the active language and the order given. An unknown code is kept as written. |
| `ranked_shares(counts)` | Ranks a mapping of counts, largest first, each entry as `{"label", "count", "percent"}` where the largest is 100. |
| `fill_slots(items, slots, reserve=False)` | Fits a list into a fixed number of places and returns `shown`, `more` and `total`. With `reserve`, the last place is kept for a "+n more" entry when the list overflows. |
| `checklist(items)` | Sums up a list of items that each carry a `done` flag: the `items`, how many are `done`, the `total` and whether all of them are `ready`. |
| `active_then_recent(items, modified, active=None)` | Orders items with the active ones first and each group most recently updated first. `modified` and `active` are functions of one item. |

```python
from fairdm.contrib.contributors.profiles import fill_slots, link_host, ranked_shares

link_host("https://www.github.com/someone")  # "github.com"
ranked_shares({"Creator": 4, "Editor": 2})
# [{"label": "Creator", "count": 4, "percent": 100},
#  {"label": "Editor", "count": 2, "percent": 50}]
fill_slots(list(range(12)), 10, reserve=True)
# {"shown": [0, 1, 2, 3, 4, 5, 6, 7, 8], "more": 3, "total": 12}
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

## Editing a profile

A person edits their own profile, and an organization's owner and administrators edit its profile,
on a page of the overview plugin at `contributor/<uuid>/update/`. The page shows one form for the
kind of contributor it is opened for and saves it, then returns to the profile.

### Who may edit

`Contributor.is_editable_by(user)` is the one place that decides. The page asks it when it opens
and again when it saves, and the overview page asks it before offering an edit action, so a right
lost while the page is open refuses the save. It is not a Django permission, because the answer
depends on the record and not only on what the user holds.

```python
person.is_editable_by(person)         # True: a person with an active account edits their own profile
person.is_editable_by(other_person)   # False
person.is_editable_by(superuser)      # False: a superuser gets nothing extra here
person.is_editable_by(anonymous_user) # False
organization.is_editable_by(owner)   # True: the owner and the administrators with a current affiliation
organization.is_editable_by(member)  # False: an ordinary member
```

An organization is editable by the people who keep its record, the ones `is_managed_by(user)`
accepts, while their account is active. Holding a portal role does not change the answer, and
neither does being a superuser. An organization with no owner and no administrators is editable by
nobody.

The page is the `Update` class in `fairdm.contrib.contributors.plugins.update`. It declares its own
`check`, `contributor_is_editable`, because an additional view is governed by its own check and
not by its owner's. A visitor who is not signed in is sent to sign in, and a signed-in user who may
not edit gets a 403. `Contributor.get_update_url()` returns its address.

### The person form

`PersonProfileForm` in `fairdm.contrib.contributors.forms.profile` edits `image`, `name`,
`alternative_names`, `profile`, `links` and `lang`, and nothing else. Email, password, identifiers,
affiliations, portal roles and the account's state are never on it.

- `image` follows the project form: the file must be an image, `validate_image_file_size` refuses
  one over the limit and names it, and a clear box removes the photo.
- `name` is required.
- `links` accepts `http` and `https` addresses only.
- `lang` is a multiple choice over the ISO 639-1 codes, named in the active language. Each code is
  stored once. `language_choices()`, in the same module, returns the `(code, name)` pairs it offers,
  sorted by name.

`alternative_names` and `links` are lists typed one entry per line, which is what `LinesField`
does.

### The organization form

`OrganizationProfileForm`, in the same module, edits `image` (the logo), `name`,
`alternative_names`, `type`, `parent`, `city`, `country`, `profile` (the description), `website`
and `links`, and nothing else. The ROR identifier, the members and the owner are never on it.

- `image`, `name` and `alternative_names` behave as on the person form.
- `type` and `country` are choices, and a value outside their lists is refused.
- `parent` is a search over every organization, the same picker the affiliation form uses.
- `website` and `links` are two fields over the one stored list `Organization.links`. The website
  is stored first and the other links follow it, so an address typed in both places is stored
  once. When the form opens, `website` shows the first stored link and `links` shows the rest.
  Clearing the website therefore makes the next link the website the next time the form opens.
  Every address must be an `http` or `https` address.

### The parent loop rule

An organization cannot be made part of itself or of one of its own sub-organizations at any depth.
`Organization.clean()` refuses such a parent with an error on the `parent` field, code
`parent_loop`, so the editing page and the administration interface refuse it alike.
`Organization.get_descendant_ids()` returns the primary keys it checks against:

```python
university = Organization.objects.create(name="Example University")
department = Organization.objects.create(name="Geology", parent=university)

university.get_descendant_ids() == {department.pk}  # True
university.parent = department
university.full_clean()  # raises ValidationError on "parent"
```

The method returns an empty set for an organization that is not saved yet.

### `LinesField`

`LinesField` is a `CharField` on a text area whose cleaned value is a list. It trims each line,
drops empty lines and keeps a repeated entry once, where it was first typed. A list given as the
initial value is shown one entry per line.

An optional `entry_validator` is called with each entry. The first entry it rejects is reported
with the code `invalid_entry`, and the entry is available to the message as `%(entry)s`:

```python
from django.core.validators import URLValidator

from fairdm.contrib.contributors.forms.profile import LinesField

websites = LinesField(
    required=False,
    entry_validator=URLValidator(schemes=["http", "https"]),
    error_messages={"invalid_entry": "%(entry)s is not a web address."},
)
websites.clean("https://example.org\n\nhttps://example.org\nhttps://example.net")
# ['https://example.org', 'https://example.net']
```

### Changing the fields: `FAIRDM_PROFILE_FORMS`

A portal changes what the page offers by subclassing the shipped form and naming the subclass in
`FAIRDM_PROFILE_FORMS`, which maps the kind of contributor to a dotted path. A kind the setting
leaves out, or a portal that does not set it, keeps the shipped form:

```python
# settings.py
FAIRDM_PROFILE_FORMS = {
    "person": "myportal.forms.PersonProfileForm",
    "organization": "fairdm.contrib.contributors.forms.profile.OrganizationProfileForm",
}
```

This form adds the given and family name, which the shipped form leaves out. Both are fields of
`Person`, so the model form saves them with no further code:

```python
# myportal/forms.py
from fairdm.contrib.contributors.forms.profile import PersonProfileForm as BasePersonProfileForm


class PersonProfileForm(BasePersonProfileForm):
    class Meta(BasePersonProfileForm.Meta):
        fields = [*BasePersonProfileForm.Meta.fields, "first_name", "last_name"]
```

The page then shows the two extra inputs and stores what is entered. To drop a field, leave it out
of `fields` in the same way.

```{note}
A portal that overrides `contributors/overview/person.html` keeps the disabled edit button, the
disabled biography prompt and unlinked checklist items until its template adopts the new
`can_edit` and `update_url` values the overview supplies. A portal that overrides
`contributors/overview/organization.html` keeps the disabled **Edit details** entry, the disabled
description prompt and unlinked checklist items in the same way. See
[the person page](overview-pages.md#the-person-page) and
[the organization page](overview-pages.md#the-organization-page).
```

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
