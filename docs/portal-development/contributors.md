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

A stored ROR identifier may be the bare identifier (`04aj4c181`) or the full address
(`https://ror.org/04aj4c181`), which is how `from_ror` stores it. `Organization.clean()` accepts
both and refuses a value that is neither.

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
| `is_editable_by(user)` | `True` when the user is active and either `is_managed_by(user)` holds or the user holds the Community Manager role. It decides who may open the [editing page](#editing-a-profile). |
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

The primary affiliation is more than a label: the Contributors tab selects it to begin with
when a person is added to a record, as the organization they are credited from there. It is
offered as a starting point only. What is chosen is kept on the contribution and does not follow
the profile afterwards (see [The organization a person is credited from](#the-organization-a-person-is-credited-from)).

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

### The organization a person is credited from

`Contribution.affiliation` is the organization a person is credited from on one record, or none.
It belongs to the contribution and is not read from the person's profile: a researcher who moves
to another institute is still credited from the first on the dataset they made there. A credit
made without an organization holds none, whatever the person's primary affiliation is:

```python
contribution = person.add_to(my_project)
contribution.affiliation  # None
```

`Crediting` sets it, lists the organization on the record, and refuses to remove an organization
that people on the record are credited from (see [Changing contributors](#changing-contributors-crediting)).
Deleting an organization from the portal sets `affiliation` to none on every contribution that
named it, and leaves the people on their records.

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

### A Level Goes With Its Credit

What a person may do on a record is the level on their credit, so deleting the credit, on the
instance or in bulk through a queryset, withdraws everything the person held through being listed
on it. Nothing else is stored, and nothing needs undoing.

Crediting a person for the first time with `Contribution.add_to()`, `Contributor.add_to()` or
`add_contributor()` starts them at the view level, as adding them from the Contributors tab does.
An organization starts with no level. Crediting a person who is already credited adds the roles and
leaves their level as it is. `Contribution.starting_level(contributor)` returns the level a first
credit starts at.

A permission stored with django-guardian for a project, dataset, sample or measurement grants
nothing. See [Levels](#levels).

### Supported Content Types

Contributions use Django's GenericForeignKey to link to:
- `fairdm.core.Project`
- `fairdm.core.Dataset`
- `fairdm.core.Sample`
- `fairdm.core.Measurement`

## The Contributors tab

Projects, datasets, samples and measurements each have a **Contributors** tab beside their
overview. The tab lists a record's people and organizations and is where the people who manage the
record add, edit and remove its contributors. It is one plugin, `ContributionList` in
`fairdm.contrib.contributors.plugins.shared`, registered on `Project`, `Dataset`, `Sample` and
`Measurement`.

**A sample or measurement type your portal registers gets the tab with no configuration.** The
plugin is registered on the base `Sample` and `Measurement` classes, so every subtype inherits it,
and the record's roles, levels and addresses are read from the core model the subtype extends.

The tab's additional views share the base class `ContributionPage`, which works out the record, its
kind and whether the viewer may manage it. `ContributionAddPerson` and `ContributionAddOrganization`
add from the portal and share `ContributionAdd`. `ContributionEdit` sets a contributor's roles and
`ContributionRemove` removes one. `ContributionMove` takes a POST with `direction` set to `up` or
`down` and hands it to `Crediting.move`, then returns to the tab at the moved contributor, and a
`direction` that is neither answers 400. A page that changes anything is refused to a signed-in person who
cannot manage the record and sends a visitor to sign in. Addresses resolve with the plugin
`reverse`, the same way for every record type:

```python
from fairdm.contrib.plugins import reverse

reverse(dataset, "contribution-list")
reverse(dataset, "contribution-list-contribution-add-person")
reverse(dataset, "contribution-list-contribution-edit", pk=contribution.pk)
reverse(sample, "contribution-list-contribution-remove", pk=contribution.pk)
```

### Levels

What a person may do on a record is one of three levels, stored on their contribution as
`Contribution.level`. Each includes the ones before it, and they are integers so that "at least"
is a comparison.

| `ContributionLevel` | Value | Lets its holder |
|---|---|---|
| `VIEW` | 1 | open the record |
| `EDIT` | 2 | also change the record and the data in it |
| `MANAGE` | 3 | also change its contributors and their levels, change its visibility and delete it |

The field is empty for an organization, which holds no level, and for a person who is credited
without one. A level on a project applies to its datasets, and a level on a dataset applies to its
samples and measurements. A measurement follows its own dataset, not its sample's.
`REQUIRED_LEVEL` in `fairdm.contrib.contributors.access` maps each permission a core record type
declares to the level that carries it.

#### Which permission means which level

Every permission a core record type declares is mapped, so none is left that nothing checks.

| Level | Permissions on the record |
|---|---|
| View | `view_<model>` |
| Edit | `change_<model>`, `add_<model>`, `import_data`, `modify_metadata`, `change_<model>_metadata` |
| Manage | `delete_<model>`, `add_contributor`, `modify_contributor`, `change_<model>_settings`, `can_publish` |

`RecordAccess(record).required_level(perm)` returns the level a permission needs on the record, or
None for a permission the table does not know, which is refused. A registered type's own default
permissions, such as `demo.view_rocksample` on a rock sample, are read as the core model's. A
permission your own record type adds to its `Meta.permissions` must be added to `REQUIRED_LEVEL`
with the level that carries it, or it is refused.

#### `RecordLevelBackend`

`fairdm.contrib.contributors.permissions.RecordLevelBackend` is in `AUTHENTICATION_BACKENDS` and is
the one decision behind every `user.has_perm(perm, record)` about a project, dataset, sample or
measurement, of any registered type. It grants a permission when the user's level on the record,
or from a record above it, is at least the level the permission needs, and it refuses an inactive
user and a visitor. For any other object, or a question with no object, it returns False and the
other backends answer.

```python
user.has_perm("dataset.change_dataset", dataset)       # edit level or above
user.has_perm("demo.delete_rocksample", rock_sample)   # manage level or above
```

`PolymorphicObjectPermissionBackend` returns False for these four kinds of record, so a row that
django-guardian stores for one grants nothing. It still answers for organizations and for any
model your portal defines. The two backends that passed a dataset's rows down to its samples and
measurements are removed, together with their modules `fairdm.core.sample.permissions` and
`fairdm.core.measurement.permissions`: delete them from your own `AUTHENTICATION_BACKENDS` if it
names them.
`PortalRolePermissionBackend` is unchanged, so a portal role's rights still apply to every record
of a kind without the holder being listed.

#### `with_level`

The querysets of the four core models get `with_level(user, level)` from
`fairdm.core.managers.RecordLevelMixin`, which `ProjectQuerySet`, `DatasetQuerySet`,
`SampleQuerySet` and `MeasurementQuerySet` mix in. `with_level` keeps the records the user holds
at least that level on, on the record itself or from a record above it, in one query.
`accessible_to(user, level)` is the same and also keeps every record for someone the portal gives
the matching right for the whole model (`view` for the view level, `change` above it), as a
superuser or a Data Curator has. Choice lists and filters offer what `accessible_to` returns.

```python
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.core.dataset.models import Dataset

Dataset.all_objects.with_level(request.user, ContributionLevel.EDIT)    # datasets the user may edit
Dataset.all_objects.accessible_to(request.user, ContributionLevel.EDIT)
Sample.objects.visible_to(request.user)    # released samples, and those the user holds a level on
```

`visible_to` on the sample and measurement querysets is the released records plus
`with_level(user, VIEW)`, and keeps its rule that a user who holds `view_dataset` or
`change_dataset` for the whole portal sees everything. A person listed only on one sample sees that
sample and not the others in its dataset. Use these querysets from your own views and filters in
place of django-guardian's `get_objects_for_user`, which finds nothing for these four models.

#### Forms for existing records

On the update forms of a project, dataset, sample and measurement, the fields that decide who gets
in (a project's visibility and owner, a dataset's visibility and project, a sample's or
measurement's dataset) are offered only to someone who can manage the record, and are left out for
anyone else, so an editor's request cannot change them. `ManagerOnlyFieldsMixin` in
`fairdm.core.forms` does it: list the field names in `manager_only_fields` and call
`withhold_manager_only_fields(request)` once the form's fields exist. `ProjectForm` takes the
request as a `request` keyword. A form for a record that does not exist yet leaves nothing out.
`SampleFormMixin` and `MeasurementFormMixin` already do this for `dataset`.

### Asking what a person may do: `RecordAccess`

A page of your own asks through `RecordAccess(record)`, which takes a project, dataset, sample or
measurement of any registered type:

```python
from fairdm.contrib.contributors.access import RecordAccess
from fairdm.contrib.contributors.choices import ContributionLevel

access = RecordAccess(sample)

access.above                       # [dataset, project]: the records it takes levels from
access.level_of(request.user)      # the highest level held on the sample or above, or None
access.level_of(request.user) == ContributionLevel.MANAGE
access.can_manage(request.user)    # manage level, or change_sample for the whole portal

access.own_level(person)           # the level from being listed on this record only
level, source = access.level_from_above(person)   # and the record it comes from
access.people_above()              # (person, level, source) for everyone holding one from above
access.managers()                  # ids of people who can sign in and hold manage here or above
access.kind                        # "sample", whatever registered type the record is
access.required_level("sample.change_sample")     # the level a permission needs: EDIT
RecordAccess.is_core_record(obj)   # a project, dataset, sample or measurement, of any type
RecordAccess.is_core_model(Sample) # the model itself, not a registered subtype
```

`level_of` answers None for a visitor, an inactive user and anyone who holds no level, and reads
the record and the records above it in one query. To ask whether a person may view, edit or manage a
record, compare it with the level:

```python
level = RecordAccess(dataset).level_of(request.user)
may_edit = level is not None and level >= ContributionLevel.EDIT
```

`can_manage` is true for the manage level on the record or above it, and for anyone holding
`change_<model>` for the whole portal, which a superuser and a Data Curator do. People who can
manage only through a portal role are not counted by `managers()`, so a record's managers are
always people listed on it or above it who can sign in. `Person.can_sign_in()` is that test.

### Changing contributors: `Crediting`

`Crediting(record)` in `fairdm.contrib.contributors.services.crediting` is the one place a record's
contributors change. Each refusal is a `ValidationError` with a code, so a page can attach it to a
field and a test can assert on it:

```python
from fairdm.contrib.contributors.services.crediting import Crediting

crediting = Crediting(dataset)

contribution = crediting.add(person)             # last of its kind, at the view level, credited from none
crediting.add(organization)                      # no level
crediting.add(other_person, organization=institute)  # credited from the institute, which is listed too
crediting.offered_roles()                        # the concepts the dataset's roles group offers
crediting.update(contribution, roles=crediting.offered_roles()[:2])
crediting.update(contribution, roles=[], organization=institute)  # credited from the institute
crediting.update(contribution, roles=[], organization=None)       # credited from none
crediting.update(contribution, roles=[], level=ContributionLevel.EDIT)  # and what they may do
crediting.make_creator(user, roles=["Creator"])  # at the manage level, for whoever just made the record
crediting.credited_from()                        # organization id to the people credited from it here
crediting.move(contribution, "up")               # one place earlier among its own kind
crediting.remove(contribution)                   # and the level goes with it
```

| Method | Raises | Code |
|---|---|---|
| `add` | the contributor is already listed | `duplicate` |
| `add` | the contributor is a superuser, who cannot be credited | `superuser` |
| `update` | a role is not in the group the record's type offers | `role_not_offered` |
| `update` | the level is below what the person holds from a record above | `below_inherited` |
| `update` | the change would leave the record with nobody who counts as able to manage it | `last_manager` |
| `remove` | the contribution is an organization that people on the record are credited from | `credited_from` |
| `remove` | the contribution is the only thing that makes the record manageable | `last_manager` |
| `move` | the direction is neither `"up"` nor `"down"` | `direction` |
| `move` | the contribution is not listed on this record | `not_listed` |

`update` replaces the roles and sets the level when one is given: leave `level` out and it stays as it
is, because a contribution role carries no rights. A level is ignored for an organization. When
several refusals apply the error holds them all, in its `error_list`, and nothing is saved. `offered_roles()` returns the roles the vocabulary groups for the record's type, in the
vocabulary's order.

`make_creator(user, roles=())` lists the person who made a record at the manage level, with the
named roles, or raises an existing entry to it. The project and dataset create pages call it, and
so do the API's serializers for projects, datasets, samples and measurements, through
`fairdm.api.serializers.CreatorCreditMixin`. For a superuser it does nothing, because a superuser
cannot be credited, and the create still succeeds. Call it from your own page that makes a record
in place of granting the creator permissions.

`level_choices(record, floor=None)` in `fairdm.contrib.contributors.plugins.shared` returns the
three levels as the edit page draws them, each with its label and a hint that names the record's
kind, and marks as disabled those below `floor`, the level the person holds from above.

The organization argument of `update` has three meanings. Leaving it out, or passing `UNCHANGED`,
leaves the organization as it is. An organization sets it, and `None` sets it to none. It applies to
a person and is ignored for an organization. An organization named in `add` or `update` is listed
on the record once, as its own contribution with no level, through `list_organization(organization)`.
It stays on the record when the last person credited from it leaves or is credited from elsewhere,
and can then be removed.

The `credited_from` refusal carries the people in `params["people"]`, so a page can name them.
`credited_from()` returns the same people for every organization on the record at once.

#### Order

A record names its people in one order and its organizations in another, and `Crediting.move` is the
only thing that changes either. `crediting.move(contribution, "up")` moves a contribution one place
earlier among the contributions of its own kind, and `"down"` one place later. It swaps `order` with
the neighbour of the same kind on the same record, so the other kind is left alone, and the first
moving earlier and the last moving later change nothing and raise nothing. Contributions that share
an order value, as old data may have, are told apart by their primary key, so a move is the same
every time. Do not use `contribution.up()` or `contribution.down()` from `OrderedModel`: a
contribution has no `order_with_respect_to`, so they swap with a row on another record.

`add` places a contributor last overall, which is last among its own kind. Removing or updating a
contributor leaves the others' order as it is.

To read either list, narrow the contributions with `people()` and `organizations()` on the
`Contribution` manager and querysets. Each filters on the contributor's polymorphic type, without
loading any contributor, and orders by `order` then `pk`:

```python
from fairdm.contrib.contributors.models import Contribution

Contribution.objects.for_entity(dataset).people()
dataset.contributors.organizations()
```

`RecordOverviewPlugin.get_contributions()` is those two lists one after the other, people first, so
everything an overview or a citation names follows the order the team set. `get_credits()` follows
it and gives a person credited with no organization an `affiliation` of `None`.

#### The last manager

A record that has someone who counts as able to manage it, as `RecordAccess(record).managers()`
reckons, keeps one. `update` and `remove` refuse, with code `last_manager`, a change that would take
the record from at least one such person to none, whoever asks. A record that has none already may
lose or raise anyone. The person's own level and the level they hold from a record above are both
read, so lowering a manager who also manages through the dataset is allowed. The refusal's
`params` hold `name` and `kind`.

`would_leave_no_manager(contribution, level=None)` answers the same question without changing
anything, for a page that has to say so before the person asks: `level=None` asks about removing the
contribution, and a level asks about lowering it to that level. The edit page attaches
`last_manager` to its level field, and the remove page draws its refusal from that answer.

#### One change at a time

`add`, `update`, `remove`, `move` and `make_creator` each run in a transaction that first locks the record's
row with `select_for_update`, through the model's `all_objects` manager where it has one so that a
private record is found, before anything about its contributors is read. Two changes to one record
wait for each other and each sees what the other left, so two managers cannot remove each other at
the same moment. `locked()` is the context manager that does it, and a method you add to `Crediting`
that changes contributors uses it too. A database that cannot lock rows, such as SQLite, runs the
change in the transaction alone.

### Moving a record

`Dataset.clean`, `Sample.clean` and `Measurement.clean` refuse a change of parent, a dataset's
project or a sample's or measurement's dataset, that would leave the record with nobody who counts
as able to manage it when it had someone before the change. The error is attached to the parent field
with code `no_manager`. A new record, a record whose parent did not change and a record that had
nobody already are never refused. The check is
`RecordAccess(record).refuse_move_without_manager("project")` or `("dataset")`, which compares the
record with the one stored.

### Choosing the organization on a page

`AffiliationChoice` in `fairdm.contrib.contributors.plugins.shared` is the form behind the choice
the Contributors tab draws with `c-contribution.affiliation`. It offers the person's affiliations
with the primary one selected, another organization by name, and none. Its two fields are
`affiliation`, one of `org:<id>`, `other` or `none`, and `affiliation_name`. Choosing another
organization with no name is an error on `affiliation_name`.

```python
from fairdm.contrib.contributors.plugins.shared import AffiliationChoice

choice = AffiliationChoice(request.POST, person=person)
if choice.is_valid():
    organization = choice.organization()   # made from the name when the portal has none
    Crediting(record).add(person, organization=organization)
```

Call `organization()` inside the transaction that saves the credit, so that an organization made
for a save that is then refused is not kept. `choice()` shapes the options for the component.
Pass `credit=` the person's contribution when editing, so that its organization is selected.

### Looking people up in ORCID and ROR: `Orcid` and `Ror`

`Orcid` and `Ror` in `fairdm.contrib.contributors.services.registries` are the two registries the
add pages search. They are two plain classes with no shared base. Each has `search(term)`,
`fetch(identifier)`, `known(record)` and `profile(record)`:

```python
from fairdm.contrib.contributors.services.registries import Orcid, RegistryUnavailable, Ror

found = Orcid().search("Carberry")        # or an ORCID iD: "0000-0002-1825-0097"
found["results"][0]["name"]               # "Josiah Carberry"
found["more"]                             # True when ORCID holds more matches than were returned

record = Orcid().fetch("0000-0002-1825-0097")
person = Orcid().profile(record)          # the person holding that iD, or a new one

record = Ror().fetch("https://ror.org/04z8jg394")
organization = Ror().profile(record)      # the organization holding that ID, or a new one
```

`search` takes a name, or an identifier, which it recognises by its form and searches for by
identifier. It returns `{"results": [...], "more": bool}`: at most `RESULTS_SHOWN` (ten) records, and
whether the registry holds more. ORCID records of people with no public name and ROR records of
organizations that are not active are left out. `fetch` returns one record, or `None` when the
identifier is not in the form of the registry's own, the registry has no such record, or the record
cannot be chosen. A malformed identifier makes no request at all.

A record is a plain dictionary, with the keys the add pages read:

| Key | ORCID | ROR |
|---|---|---|
| `id` | the ORCID iD | the ROR address, `https://ror.org/...` |
| `shown_id` | the ORCID iD | the address without its scheme |
| `name` | given and family names | ROR's display name |
| `detail` | the employer and where it is, to tell namesakes apart | the kind of organization and where it is |
| `given`, `family`, `employer` | the two names and the first current employer | not present |

`known(record)` returns the contributor the portal already holds under the record's identifier, or
`None`. `profile(record)` returns that contributor, or makes one with the name and the identifier
and nothing else. A person made this way has no email address, an unusable password and no account.
A profile is never matched by name. The ROR identifier is saved as the bare ID, and a profile that
holds it as an address is found too.

Both classes raise `RegistryUnavailable` for a network error, a timeout, an answer that is not a
200 (a 404 on `fetch` is an answer: there is no such record) and an answer that is not in the form
the registry documents. The timeout, `TIMEOUT`, is five seconds. Search terms go in the request's
parameters and never into the address, and no identifier reaches an address unless it has matched
`ORCID_PATTERN` or `ROR_PATTERN` from `fairdm.contrib.contributors.models`. A test replaces
`requests.get`, as the tests of the add pages do.

`ask(address, parse, *, params=None, headers=None, missing_ok=False)` is the one function that
makes a request. Everything after `parse` is passed by keyword. Both classes call it, and the failure handling above lives in it. A caller that wants a
third registry passes the address and a function that reads the decoded answer.

Saving the identifier queues the sync that `ContributorIdentifier` queues for every identifier, so
a worker later fills in the rest of the profile.

#### The pages

`ContributionAdd`, the base of both add pages, offers the registry as its second tab: `registry_class`
is `Orcid` on `ContributionAddPerson` and `Ror` on `ContributionAddOrganization`. A search reads `rq`
and the portal search reads `q`, and `via` names the tab to open. The context's `adding` carries
`registry_results`, `registry_more` and `registry_unavailable`. A registry that cannot be reached
leaves the other two tabs working, and the page answers 200.

Choosing a record only fetches it. Adding posts the identifier, and the page fetches the record
again before it makes a profile: nothing else the form carries is read.

`NewPersonForm` and `NewOrganizationForm` in `fairdm.contrib.contributors.plugins.shared` are the
forms behind the by-hand tab. A person needs `given` and `family` and has no other field: a posted
`email` is ignored, and the person is saved with none, an unusable password and no account. The
form is not valid while `same_name` lists profiles with the person's name, until the page sends
`confirmed`. An organization needs a `name`, and may have a `city`, a `country`, as a name or
a code from the country field's list (the code `invalid_country`), and a `website`, which is kept in
the organization's `links`. It is never valid while `same_name` holds an organization of that name.
`save()` makes the contributor and does nothing else, so the page can make it, make the organization
chosen and write the credit in one transaction.

## Editing a profile

A person edits their own profile, an organization's owner and administrators edit its profile, and
a Community Manager edits the profiles nobody else can, on a page of the overview plugin at `contributor/<uuid>/update/`. The page shows one form for the
kind of contributor it is opened for and saves it, then returns to the profile.

### Who may edit

`Contributor.is_editable_by(user)` is the one place that decides. The page asks it when it opens
and again when it saves, and the overview page asks it before offering an edit action, so a right
lost while the page is open refuses the save. It is not a Django permission, because the answer
depends on the record and not only on what the user holds.

```python
person.is_editable_by(person)             # True: a person with an active account edits their own profile
person.is_editable_by(other_person)       # False
person.is_editable_by(superuser)          # False: a superuser gets nothing extra here
person.is_editable_by(anonymous_user)     # False
unclaimed.is_editable_by(manager)         # True: a Community Manager, and nobody can sign in to the profile
claimed.is_editable_by(manager)           # False: its owner has an active account
organization.is_editable_by(owner)        # True: the owner and the administrators with a current affiliation
organization.is_editable_by(member)       # False: an ordinary member
organization.is_editable_by(manager)      # True: a Community Manager, even for an organization with no owner
```

A Community Manager is a user for whom `PortalRoles.is_held_by(user, PortalRoles.COMMUNITY_MANAGER)`
is true. The Portal Administrator, Data Curator and Developer roles, and being a superuser, give no
right to edit a profile, and the rule never asks Django for a permission.

A person's profile is editable by a Community Manager only while nobody can sign in to it and keep
it themselves: the account is inactive, or the person is not claimed and has never signed in
(`last_login` is empty). `Person.can_sign_in()` is that rule: the account is active, and the person
has claimed it or has signed in. `account_state` alone cannot say it, because an account made with
`createsuperuser`, or by signing up on a portal that does not verify email addresses, is active and
in use without being marked claimed. Such a person edits their own profile and nobody else does. An
organization is editable by the people who keep its record, the ones `is_managed_by(user)`
accepts, while their account is active, and by any active Community Manager, whether or not the
organization has an owner.

The page is the `Update` class in `fairdm.contrib.contributors.plugins.update`. It declares its own
`check`, `contributor_is_editable`, because an additional view is governed by its own check and
not by its owner's. A visitor who is not signed in is sent to sign in, and a signed-in user who may
not edit gets a 403. `Contributor.get_update_url()` returns its address.

### The person form

`PersonProfileForm` in `fairdm.contrib.contributors.forms.profile` edits `image`, `first_name`,
`last_name`, `name`, `alternative_names`, `profile`, `links` and `lang`, and nothing else. Email, password, identifiers,
affiliations, portal roles and the account's state are never on it.

- `image` follows the project form: the file must be an image, `validate_image_file_size` refuses
  one over the limit and names it, and a clear box removes the photo.
- `name` is required. `first_name` and `last_name` are what citations and exported metadata use.
- `links` accepts `http` and `https` addresses only.
- `lang` is a multiple choice over the ISO 639-1 codes, named in the active language. Each code is
  stored once. `language_choices()`, in the same module, returns the `(code, name)` pairs it offers,
  sorted by name.

`alternative_names` and `links` are lists typed one entry per line, which is what `LinesField`
does.

### What both forms share

`PersonProfileForm` and `OrganizationProfileForm` extend `ProfileForm`, in the same module, so a
portal's own form can extend it too. It draws no `<form>` tag, because the editing page supplies it
and the buttons.

Each form groups its fields under headings. `sections` is a tuple of `(heading, rows)` pairs, and
a row is one field name or a tuple of names drawn side by side on a wide screen:

```python
class PersonProfileForm(ProfileForm):
    sections = (
        (None, [("first_name", "last_name"), "name", "alternative_names"]),
        (_("About you"), ["image", "profile", "lang", "links"]),
    )
```

A heading of `None` draws the rows with no heading. Each form's first group has none, because a
heading at the very top of a form reads as a stray divider.

A field the form does not carry is left out of its section, and a field no section names is drawn
after the last one. A portal's subclass sets `sections` to place a field it adds.

A stored record can fail the model's validation on a field the form does not carry, such as an
identifier that was stored malformed. `ProfileForm` reports that failure as an error on the form as
a whole, in `form.non_field_errors()`, and saves nothing. Without it Django raises a `ValueError`
for an error on a field the form lacks, and the editing page answers with a server error.

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

This form adds the person's location, which the shipped form leaves out. It is a field of
`Person`, so the model form saves it with no further code:

```python
# myportal/forms.py
from fairdm.contrib.contributors.forms.profile import PersonProfileForm as BasePersonProfileForm


class PersonProfileForm(BasePersonProfileForm):
    class Meta(BasePersonProfileForm.Meta):
        fields = [*BasePersonProfileForm.Meta.fields, "location"]
```

The page then shows the extra input after the last section and stores what is chosen. To drop a field, leave it out
of `fields` in the same way. A form without `lang`, `website` or `parent` builds and saves. Without
`website`, the `links` field shows every stored link, the first one included. A form that keeps
`website` has to keep `links` as well, because the website is stored as the first of the links.

`LinesField` accepts at most `max_entries` lines, 50 unless the field says otherwise.

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
